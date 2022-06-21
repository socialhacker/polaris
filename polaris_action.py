"""Polaris: A KiCad action plugin to position components on the PCB

Polaris defines a language of translations and rotations that can be
applied to parts on a PCB.
"""

import math
import pcbnew
import re
import sys
import wx

from .source.ast import evaluate, Function, SymbolTable, Variable
from .source.transform import Transform
from .parser import Tokens
from .parser import Parser
from .parser import tokenize

def rotation(symbols, angle, scale):
    return Transform.from_rotation(evaluate(symbols, angle) * scale)

def translation(symbols, x, y, scale):
    return Transform.from_translation(evaluate(symbols, x) * scale,
                                      evaluate(symbols, y) * scale)

symbols = SymbolTable(None, {
    'deg':  Function(lambda s, a: rotation(s, a, math.pi / 180)),
    'grad': Function(lambda s, a: rotation(s, a, math.pi / 200)),
    'rad':  Function(lambda s, a: rotation(s, a, 1)),
    'turn': Function(lambda s, a: rotation(s, a, math.pi * 2)),
    'inch': Function(lambda s, x, y: translation(s, x, y, 25.4)),
    'mil':  Function(lambda s, x, y: translation(s, x, y, 0.0254)),
    'mm':   Function(lambda s, x, y: translation(s, x, y, 1))
})

def ignore_whitespace(tokens):
    return filter(lambda item : item[0] != "WHITESPACE", tokens)

def read_transform(source):
    tokens = Tokens(ignore_whitespace(tokenize(source)))

    return evaluate(symbols, Parser(tokens).parse_expression())

def read_script(source):
    tokens = Tokens(ignore_whitespace(tokenize(source)))

    return Parser(tokens).parse_script()

def get_footprint_transform(footprint):
    x, y = footprint.GetPosition()

    return Transform(pcbnew.Iu2Millimeter(x),
                     pcbnew.Iu2Millimeter(y),
                     -math.radians(footprint.GetOrientationDegrees()))

def set_footprint_transform(footprint, transform):
    footprint.SetPosition(pcbnew.wxPoint(pcbnew.Millimeter2iu(transform.x),
                                         pcbnew.Millimeter2iu(transform.y)))
    footprint.SetOrientationDegrees(-math.degrees(transform.theta))

def add_transform(transforms, footprint, transform):
    path = footprint.GetPath().AsString()

    if path in transforms:
        (_, origin) = transforms[path]
        transforms[path] = (footprint, transform @ origin)
    else:
        transforms[path] = (footprint, transform)

def show_dialog(title, message):
    dialog = wx.MessageDialog(None, message, title, wx.OK)
    dialog.ShowModal()
    dialog.Destroy()

def find_duplicates(matchers):
    unique     = set()
    duplicates = []

    for matcher in matchers:
        if matcher.prefix in unique:
            duplicates.append(matcher.prefix)
        else:
            unique.add(matcher.prefix)

    return duplicates

class PolarisAction(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "Polaris"
        self.category = "Modify PCB"
        self.description = "Compute part placement and orientation from transformations stored in a property"
        self.show_toolbar_button = True

    def Run(self):
        board      = pcbnew.GetBoard()
        transforms = {}
        matchers   = []

        #
        # Parse all of the polaris scripts found in TEXT drawings.  These will
        # contain footprint reference patterns to match and associated
        # expressions to evaluate.
        #
        for drawing in board.GetDrawings():
            if isinstance (drawing, pcbnew.PCB_TEXT):
                matchers.extend(read_script(drawing.GetText()))

        #
        # Check for duplicate reference prefix matchers.  We can't handle
        # duplicates because we don't know what order to apply the transforms
        # in.
        #
        duplicates = find_duplicates(matchers)

        if (duplicates):
            show_dialog("Error",
                        f'Duplicate reference matchers found: {duplicates}')
            return

        #
        # Sort the matchers by prefix length.  This ensures that the more
        # general prefix matches and applies before the more specific prefix
        # matches.
        #
        matchers.sort(key=lambda m : len(m.prefix))

        #
        # For every footprint on the board check to see if one of the script
        # patterns matches, and if the footprint has a Polaris property.  The
        # transforms that are found are composed with scripts happening first,
        # and then individual footprint Polaris property transforms happending.
        #
        for footprint in board.GetFootprints():
            reference = footprint.GetReference()
            index     = int(re.search(r"(\d*)$", reference).group())
            local     = SymbolTable(symbols, {'index': Variable(index)})

            for matcher in matchers:
                if reference.startswith(matcher.prefix):
                    add_transform(transforms,
                                  footprint,
                                  evaluate(local, matcher.expression))

            if footprint.HasProperty('Polaris'):
                source = footprint.GetProperty('Polaris')
                add_transform(transforms, footprint, read_transform(source))

        #
        # Finally, apply all of the transforms that we found.
        #
        for uuid, (footprint, transform) in transforms.items():
            set_footprint_transform(footprint, transform)
