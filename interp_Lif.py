from ast import *
from typing import Callable
from interp_Lvar import InterpLvar
from interp_Lint import InterpValue, Env
from utils import *

# A comparison operator as a Python function: interp_cmp(Lt()) is `<`.
CmpFn = Callable[[InterpValue, InterpValue], bool]

class InterpLif(InterpLvar):

  def interp_cmp(self, cmp: cmpop) -> CmpFn:
    match cmp:
      case Lt():
        return lambda x, y: x < y
      case LtE():
        return lambda x, y: x <= y
      case Gt():
        return lambda x, y: x > y
      case GtE():
        return lambda x, y: x >= y
      case Eq():
        return lambda x, y: x == y
      case NotEq():
        return lambda x, y: x != y
      case _:
        raise Exception('interp_cmp: unexpected ' + repr(cmp))

  def interp_exp(self, e: expr, env: Env) -> InterpValue:
    match e:
      case IfExp(test, body, orelse):
        match self.interp_exp(test, env):
          case True:
            return self.interp_exp(body, env)
          case False:
            return self.interp_exp(orelse, env)
      case UnaryOp(Not(), v):
        return not self.interp_exp(v, env)
      case BoolOp(And(), values):
        left = values[0]; right = values[1]
        match self.interp_exp(left, env):
          case True:
            return self.interp_exp(right, env)
          case False:
            return False
      case BoolOp(Or(), values):
        left = values[0]; right = values[1]
        match self.interp_exp(left, env):
          case True:
            return True
          case False:
            return self.interp_exp(right, env)
      case Compare(left, [cmp], [right]):
        l = self.interp_exp(left, env)
        r = self.interp_exp(right, env)
        return self.interp_cmp(cmp)(l, r)
      # Begin (utils.py) is not in L_If itself: remove_complex_operands
      # creates it (section 5.6), so this interpreter can run that pass's output.
      case Begin(ss, e):
        self.interp_stmts(ss, env)
        return self.interp_exp(e, env)
      case _:
        return super().interp_exp(e, env)

  def interp_stmt(self, s: stmt, env: Env, cont: list[stmt]) -> InterpValue:
    match s:
      case If(test, body, orelse):
        match self.interp_exp(test, env):
          case True:
            return self.interp_stmts(body + cont, env)
          case False:
            return self.interp_stmts(orelse + cont, env)
      case _:
        return super().interp_stmt(s, env, cont)

