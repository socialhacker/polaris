from dataclasses import dataclass
from typing      import Any, Dict, List, Optional

@dataclass
class Statement:
    pass

@dataclass
class SymbolTable:
    scope: Optional[Any] # This should be Optional(SymbolTable)
    table: Dict[str, Statement]

@dataclass
class Function(Statement):
    func: object

@dataclass
class Variable(Statement):
    value: Any

@dataclass
class Expression(Statement):
    pass

@dataclass
class UnaryOp(Expression):
    op:  str
    rhs: object

@dataclass
class BinaryOp(Expression):
    lhs: object
    op:  str
    rhs: object

@dataclass
class FunctionCall(Expression):
    name: str
    args: List[Expression]

@dataclass
class VariableRead(Expression):
    name: str

@dataclass
class Constant(Expression):
    value: Any

def evaluate(symbols : SymbolTable, tree):
    match tree:
        case UnaryOp(      '+', rhs):  return +evaluate(symbols, rhs)
        case UnaryOp      ('-', rhs):  return -evaluate(symbols, rhs)
        case BinaryOp(lhs, '+', rhs):  return evaluate(symbols, lhs) + evaluate(symbols, rhs)
        case BinaryOp(lhs, '-', rhs):  return evaluate(symbols, lhs) - evaluate(symbols, rhs)
        case BinaryOp(lhs, '*', rhs):  return evaluate(symbols, lhs) * evaluate(symbols, rhs)
        case BinaryOp(lhs, '@', rhs):  return evaluate(symbols, lhs) @ evaluate(symbols, rhs)
        case BinaryOp(lhs, '/', rhs):  return evaluate(symbols, lhs) / evaluate(symbols, rhs)
        case FunctionCall(name, args): return symbols[name].func(symbols, *args)
        case VariableRead(name):       return symbols[name].value
        case Constant(value):          return value
        case _:                        raise RuntimeError(f'Unhandled AST node type {tree}')
