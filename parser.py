import math
import re

from dataclasses import dataclass

from .source.ast       import BinaryOp, Constant, FunctionCall, UnaryOp, VariableRead
from .source.transform import Transform

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
               ('COLON',      r':'),
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

@dataclass
class Matcher:
    prefix: str
    expression: object

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens

    def parse_arguments(self):
        self.tokens.expect('LEFT')

        args = []
        while self.tokens.peek()[0] != 'RIGHT':
            args.append(self.parse_expression())

            if self.tokens.peek()[0] != 'COMMA':
                break

            self.tokens.pop()

        self.tokens.expect('RIGHT')

        return args

    def parse_primative(self):
        match self.tokens.pop():
            case ('NUMBER', value):
                return Constant(float(value))

            case ('LEFT', _):
                expression = self.parse_expression()
                self.tokens.expect('RIGHT')
                return expression

            case ('ID', value):
                match self.tokens.peek():
                    case ('LEFT', _): return FunctionCall(value, self.parse_arguments())
                    case _:           return VariableRead(value)

            case (token, value):
                raise RuntimeError(f'Unexpected token "{value}" of type {token}')

    def parse_factor(self):
        match self.tokens.peek():
            case ('OP', '+'): self.tokens.pop(); return UnaryOp('+', self.parse_primative())
            case ('OP', '-'): self.tokens.pop(); return UnaryOp('-', self.parse_primative())
            case _:            return self.parse_primative()

    def parse_term(self):
        factor = self.parse_factor()

        while True:
            match self.tokens.peek():
                case ('OP', '*'): self.tokens.pop(); factor = BinaryOp(factor, '*', self.parse_factor())
                case ('OP', '/'): self.tokens.pop(); factor = BinaryOp(factor, '/', self.parse_factor())
                case ('OP', '@'): self.tokens.pop(); factor = BinaryOp(factor, '@', self.parse_factor())
                case _: return factor

    def parse_expression(self):
        term = self.parse_term()

        while True:
            match self.tokens.peek():
                case ('OP', '+'): self.tokens.pop(); term = BinaryOp(term, '+', self.parse_term())
                case ('OP', '-'): self.tokens.pop(); term = BinaryOp(term, '-', self.parse_term())
                case _: return term

    def parse_script(self):
        matchers = []

        if (self.tokens.pop() == ('ID', "script") and
            self.tokens.pop() == ('LEFT', "(") and
            self.tokens.pop() == ('ID', "polaris") and
            self.tokens.pop() == ('RIGHT', ")")):

            while self.tokens:
                prefix = self.tokens.expect('ID')
                self.tokens.expect('COLON')
                expression = self.parse_expression()

                matchers.append(Matcher(prefix, expression))

        return matchers
