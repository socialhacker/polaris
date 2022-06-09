import math
import re

from .transform import Transform

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
        yield m.lastgroup, m.group()

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

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens

def parse_factor(tokens):
    match tokens.pop():
        case ('NUMBER', value): return float(value)
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
