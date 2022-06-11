from dataclasses import dataclass
from typing      import Any, List

@dataclass
class UnaryOp:
    op:  str
    rhs: object

@dataclass
class BinaryOp:
    lhs: object
    op:  str
    rhs: object

@dataclass
class Function:
    func: object
    args: List[object]

@dataclass
class Variable:
    name: str

@dataclass
class Constant:
    value: Any

def evaluate(symbols, tree):
    match tree:
        case UnaryOp(      '+', rhs): return +evaluate(symbols, rhs)
        case UnaryOp      ('-', rhs): return -evaluate(symbols, rhs)
        case BinaryOp(lhs, '+', rhs): return evaluate(symbols, lhs) + evaluate(symbols, rhs)
        case BinaryOp(lhs, '-', rhs): return evaluate(symbols, lhs) - evaluate(symbols, rhs)
        case BinaryOp(lhs, '*', rhs): return evaluate(symbols, lhs) * evaluate(symbols, rhs)
        case BinaryOp(lhs, '/', rhs): return evaluate(symbols, lhs) / evaluate(symbols, rhs)
        case Function(func, args):    return func(symbols, *args)
        case Variable(name):          return symbols[name]
        case Constant(value):         return value
        case _:                       raise RuntimeError(f'Unhandled AST node type {tree}')
