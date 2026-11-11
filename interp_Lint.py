from ast import *
from typing import Any
from utils import input_int, add64, sub64, neg64

# What a program can compute at run time. In Lint that's only int, but the
# interpreters for later languages subclass InterpLint and add booleans,
# tuples, functions, and so on, so the class-based version uses Any.
InterpValue = Any

# Maps each variable name to its current value.
Env = dict[str, InterpValue]

def interp_exp(e: expr) -> int:
    match e:
        case BinOp(left, Add(), right):
            l = interp_exp(left); r = interp_exp(right)
            return add64(l, r)
        case BinOp(left, Sub(), right):
            l = interp_exp(left); r = interp_exp(right)
            return sub64(l, r)
        case UnaryOp(USub(), v):
            return neg64(interp_exp(v))
        case Constant(value):
            assert isinstance(value, int)
            return value
        case Call(Name('input_int'), []):
            return input_int()
        case _:
            raise Exception('error in interp_exp, unexpected ' + repr(e))

def interp_stmt(s: stmt) -> None:
    match s:
        case Expr(Call(Name('print'), [arg])):
            print(interp_exp(arg))
        case Expr(value):
            interp_exp(value)
        case _:
            raise Exception('error in interp_stmt, unexpected ' + repr(s))

def interp(p: Module) -> None:
    match p:
        case Module(body):
            for s in body:
                interp_stmt(s)
        case _:
            raise Exception('error in interp, unexpected ' + repr(p))

# This version is for InterpLvar to inherit from 
class InterpLint:
  def interp_exp(self, e: expr, env: Env) -> InterpValue:
    match e:
      case BinOp(left, Add(), right):
        l = self.interp_exp(left, env); r = self.interp_exp(right, env)
        return add64(l, r)
      case BinOp(left, Sub(), right):
        l = self.interp_exp(left, env); r = self.interp_exp(right, env)
        return sub64(l, r)
      case UnaryOp(USub(), v):
        return neg64(self.interp_exp(v, env))
      case Constant(value):
        return value
      case Call(Name('input_int'), []):
        return input_int()
      case _:
        raise Exception('error in interp_exp, unexpected ' + repr(e))

  # The cont parameter is a list of statements that are the
  # continuaton of the current statement s.
  # We use this continuation-passing approach because
  # it enables the handling of Goto in interp_Cif.py.
  def interp_stmt(self, s: stmt, env: Env, cont: list[stmt]) -> InterpValue:
    match s:
      case Expr(Call(Name('print'), [arg])):
        val = self.interp_exp(arg, env)
        print(val, end='')
        return self.interp_stmts(cont, env)
      case Expr(value):
        self.interp_exp(value, env)
        return self.interp_stmts(cont, env)
      case _:
        raise Exception('error in interp_stmt, unexpected ' + repr(s))
    
  def interp_stmts(self, ss: list[stmt], env: Env) -> InterpValue:
    match ss:
      case []:
        return 0
      case [s, *rest]:
        return self.interp_stmt(s, env, rest)
      case _:
        raise Exception('interp_stmts: unexpected ' + repr(ss))

  def interp(self, p: Module) -> None:
    match p:
      case Module(body):
        self.interp_stmts(body, {})
      case _:
        raise Exception('error in interp, unexpected ' + repr(p))
    
if __name__ == "__main__":
  eight = Constant(8)
  neg_eight = UnaryOp(USub(), eight)
  read = Call(Name('input_int'), [])
  ast1_1 = BinOp(read, Add(), neg_eight)
  pr = Expr(Call(Name('print'), [ast1_1]))
  p = Module([pr])
  interp(p)
