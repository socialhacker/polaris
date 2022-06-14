"""Polaris: A KiCad action plugin to position components on the PCB

Polaris defines a language of translations and rotations that can be
applied to parts on a PCB.
"""

import math
import pcbnew
import re
import sys
import wx

from .transform import Transform
from .parser    import Tokens
from .parser    import Parser
from .parser    import tokenize

def ignore_whitespace(tokens):
    return filter(lambda item : item[0] != "WHITESPACE", tokens)

def compute_transform(source):
    tokens = Tokens(ignore_whitespace(tokenize(source)))

    return Parser(tokens).parse_expression()

def get_footprint_transform(footprint):
    x, y = footprint.GetPosition()

    return Transform(pcbnew.Iu2Millimeter(x),
                     pcbnew.Iu2Millimeter(y),
                     -math.radians(footprint.GetOrientationDegrees()))

def set_footprint_transform(footprint, transform):
    footprint.SetPosition(pcbnew.wxPoint(pcbnew.Millimeter2iu(transform.x),
                                         pcbnew.Millimeter2iu(transform.y)))
    footprint.SetOrientationDegrees(-math.degrees(transform.theta))

class PolarisAction(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "Polaris"
        self.category = "Modify PCB"
        self.description = "Compute part placement and orientation from transformations stored in a property"
        self.show_toolbar_button = True

    def Run(self):
        board = pcbnew.GetBoard()
        transforms = {}

        for drawing in board.GetDrawings():
            if isinstance (drawing, pcbnew.PCB_TEXT):
                print(f'PCB_TEXT: {drawing.GetText()}', file=sys.stderr)

        for footprint in board.GetFootprints():
            if footprint.HasProperty('Polaris'):
                source    = footprint.GetProperty('Polaris')
                transform = compute_transform(source)
                path      = footprint.GetPath().AsString()
                _, origin = transforms.get(path, (footprint,
                                                  Transform(0, 0, 0)))

                transforms[path] = (footprint, transform @ origin)

        for uuid, (footprint, transform) in transforms.items():
            set_footprint_transform(footprint, transform)
