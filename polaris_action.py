#
# Copyright (c) 2022, Anton Staaf.  All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
#

import math
import pcbnew
import re
import sys

class Transform:
    def __init__(self, x, y, theta):
        self.x = x
        self.y = y
        self.theta = theta

    @classmethod
    def from_translation(cls, x, y):
        return cls(x, y, 0)

    @classmethod
    def from_rotation(cls, theta):
        return cls(0, 0, theta)

    def __repr__(self):
        return f'Transform({self.x}x{self.y},{self.theta})'

    def __mul__(self, transform):
        s = math.sin(self.theta)
        c = math.cos(self.theta)

        return Transform(self.x     + c * transform.x - s * transform.y,
                         self.y     + s * transform.x + c * transform.y,
                         self.theta + transform.theta)

#
# Polaris syntax:
#
# TRANSFORMS  = TRANSFORM*
# TRANSFORM   = FOOTPRINT | ROTATION | TRANSLATION
# FOOTPRINT   = 'ref' '(' REFERENCE ')'
# ROTATION    = ('deg'|'grad'|'rad'|'turn') '(' EXPRESSION ')'
# TRANSLATION = ('inch'|'mil'|'mm') '(' EXPRESSION ',' EXPRESSION ')'
# REFERENCE   = [A-Za-z]+[A-Za-z0-9_]*
# EXPRESSION  = TERM (('+'|'-') TERM)*
# TERM        = FACTOR (('*'|'/') FACTOR)*
# FACTOR      = ('+'|'-')? (NUMBER | '(' EXPRESSION ')')
# NUMBER      = DIGITS+ ("." DIGITS)? EXPONENT?
# EXPONENT    = ('e'|'E') ('+'|'-')? DIGITS
# DIGITS      = [0-9] [0-9_]*
#

def tokenize(source):
    tokens = [ ('NUMBER',     r'\d[\d_]*(\.\d[\d_]*)?([eE][+\-]?\d[\d_]*)?'),
               ('ID',         r'[A-Za-z]+\w*'),
               ('OP',         r'[+\-*/]'),
               ('LEFT',       r'\('),
               ('RIGHT',      r'\)'),
               ('COMMA',      r','),
               ('WHITESPACE', r'\s+'),
               ('ERROR',      r'.') ]

    regex = '|'.join('(?P<%s>%s)' % token for token in tokens)

    for m in re.finditer(regex, source):
        match m.lastgroup:
            case 'NUMBER':     yield 'NUMBER', float(m.group())
            case 'WHITESPACE': pass
            case _:            yield m.lastgroup, m.group()

class Tokens:
    def __init__(self, tokens):
        self.tokens  = tokens
        self.current = None
        self.pop()

    def __bool__(self):
        return self.current != None

    def peek(self):
        return self.current

    def pop(self):
        current = self.current

        try:
            self.current = next(self.tokens)
        except StopIteration:
            self.current = None

        return current

    def expect(self, token_name):
        name, value = self.pop()

        if name != token_name:
            raise RuntimeError(f'Expected {token_name}, found "{value}" which is {name}')

        return value

def parse_factor(tokens):
    match tokens.pop():
        case ('NUMBER', value): return value
        case (group,    value): raise RuntimeError(f'Unexpected token "{value}" of type {group}')

def parse_term(tokens):
    factor = parse_factor(tokens)

    while True:
        match tokens.peek():
            case ('OP', '*'): tokens.pop(); factor = factor * parse_factor(tokens)
            case ('OP', '/'): tokens.pop(); factor = factor / parse_factor(tokens)
            case _: return factor

def parse_expression(tokens):
    term = parse_term(tokens)

    while True:
        match tokens.peek():
            case ('OP', '+'): tokens.pop(); term = term + parse_term(tokens)
            case ('OP', '-'): tokens.pop(); term = term - parse_term(tokens)
            case _: return term

def parse_reference(tokens):
    tokens.expect('LEFT')
    tokens.expect('RIGHT')
    return Transform(0, 0, 0)

def parse_rotation(tokens, scale):
    tokens.expect('LEFT')
    angle = parse_expression(tokens) * scale
    tokens.expect('RIGHT')

    return Transform.from_rotation(angle)

def parse_translation(tokens, scale):
    tokens.expect('LEFT')
    x = parse_expression(tokens) * scale
    tokens.expect('COMMA')
    y = parse_expression(tokens) * scale
    tokens.expect('RIGHT')

    return Transform.from_translation(x, y)

def parse_transform(tokens):
    match tokens.pop():
        case ('ID', value):
            match value:
                case 'ref':  return parse_reference(tokens)
                case 'deg':  return parse_rotation(tokens, math.pi / 180)
                case 'grad': return parse_rotation(tokens, math.pi / 200)
                case 'rad':  return parse_rotation(tokens, 1)
                case 'turn': return parse_rotation(tokens, math.pi * 2)
                case 'inch': return parse_translation(tokens, 25.4)
                case 'mil':  return parse_translation(tokens, 0.0254)
                case 'mm':   return parse_translation(tokens, 1)
                case _:      raise RuntimeError(f'Unexpected transformation "{value}"')
        case (group, value): raise RuntimeError(f'Unexpected token "{value}" of type {group}')

def compute_transform(source):
    tokens    = Tokens(tokenize(source))
    transform = Transform(0, 0, 0)

    while tokens:
        transform = transform * parse_transform(tokens)

    return transform

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

        for footprint in board.GetFootprints():
            if footprint.HasProperty('Polaris'):
                t = compute_transform(footprint.GetProperty('Polaris'))

                set_footprint_transform(footprint, t);
