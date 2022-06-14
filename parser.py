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
# TERM        = FACTOR (('@'|'*'|'/') FACTOR)*
# FACTOR      = ('+'|'-')? (NUMBER | '(' EXPRESSION ')')
# NUMBER      = DIGITS+ ("." DIGITS)? EXPONENT?
# EXPONENT    = ('e'|'E') ('+'|'-')? DIGITS
# DIGITS      = [0-9] [0-9_]*
#

def tokenize(source):
    tokens = [ ('NUMBER',     r'\d[\d_]*(\.\d[\d_]*)?([eE][+\-]?\d[\d_]*)?'),
               ('ID',         r'[A-Za-z]+\w*'),
               ('OP',         r'[+\-*/@]'),
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

    def parse_reference(self):
        self.tokens.expect('LEFT')
        self.tokens.expect('RIGHT')

        return Transform(0, 0, 0)

    def parse_rotation(self, scale):
        self.tokens.expect('LEFT')
        angle = self.parse_expression() * scale
        self.tokens.expect('RIGHT')

        return Transform.from_rotation(angle)

    def parse_translation(self, scale):
        self.tokens.expect('LEFT')
        x = self.parse_expression() * scale
        self.tokens.expect('COMMA')
        y = self.parse_expression() * scale
        self.tokens.expect('RIGHT')

        return Transform.from_translation(x, y)

    def parse_primative(self):
        match self.tokens.pop():
            case ('NUMBER', value):
                return float(value)

            case ('LEFT', _):
                expression = self.parse_expression()
                self.tokens.expect('RIGHT')
                return expression

            case ('ID', value):
                match value:
                    case 'ref':  return self.parse_reference()
                    case 'deg':  return self.parse_rotation(math.pi / 180)
                    case 'grad': return self.parse_rotation(math.pi / 200)
                    case 'rad':  return self.parse_rotation(1)
                    case 'turn': return self.parse_rotation(math.pi * 2)
                    case 'inch': return self.parse_translation(25.4)
                    case 'mil':  return self.parse_translation(0.0254)
                    case 'mm':   return self.parse_translation(1)
                    case _:      raise RuntimeError(f'Unexpected transformation "{value}"')                

            case (token, value):
                raise RuntimeError(f'Unexpected token "{value}" of type {token}')

    def parse_factor(self):
        match self.tokens.peek():
            case ('+', value): self.tokens.pop(); return +self.parse_primative()
            case ('-', value): self.tokens.pop(); return -self.parse_primative()
            case _:            return self.parse_primative()

    def parse_term(self):
        factor = self.parse_factor()

        while True:
            match self.tokens.peek():
                case ('OP', '*'): self.tokens.pop(); factor = factor * self.parse_factor()
                case ('OP', '/'): self.tokens.pop(); factor = factor / self.parse_factor()
                case ('OP', '@'): self.tokens.pop(); factor = factor @ self.parse_factor()
                case _: return factor

    def parse_expression(self):
        term = self.parse_term()

        while True:
            match self.tokens.peek():
                case ('OP', '+'): self.tokens.pop(); term = term + self.parse_term()
                case ('OP', '-'): self.tokens.pop(); term = term - self.parse_term()
                case _: return term
