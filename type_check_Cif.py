from ast import *
from utils import CProgram, Goto, trace, Bottom, IntType, BoolType, Begin, Type
from type_check_Lvar import TypeEnv
import copy

class TypeCheckCif:

  # Bottom is the "don't know yet" type: a variable gets it when it is used
  # in a block that is checked before the block that assigns it. It is
  # compatible with every type, and type_check repeats until nothing changes.
  def check_type_equal(self, t1: Type, t2: Type, e: object) -> None:
    if t1 == Bottom() or t2 == Bottom():
      pass
    elif t1 != t2:
      raise Exception('error: ' + repr(t1) + ' != ' + repr(t2) \
                      + ' in ' + repr(e))

  def combine_types(self, t1: Type, t2: Type) -> Type:
    match (t1, t2):
      case (Bottom(), _):
        return t2
      case (_, Bottom()):
        return t1
      case _:
        return t1

  def type_check_atm(self, e: expr, env: TypeEnv) -> Type:
    match e:
      case Name(id):
        t = env.get(id, Bottom())
        env[id] = t    # make sure this gets into the environment for later definedness checking
        return t
      case Constant(value) if isinstance(value, bool):
        return BoolType()
      case Constant(value) if isinstance(value, int):
        return IntType()
      case _:
        raise Exception('error in type_check_atm, unexpected ' + repr(e))

  def type_check_exp(self, e: expr, env: TypeEnv) -> Type:
    match e:
      case Name(id):
        return self.type_check_atm(e, env)
      case Constant(value):
        return self.type_check_atm(e, env)
      case BinOp(left, op, right) if isinstance(op, Add) or isinstance(op, Sub):
        l = self.type_check_atm(left, env)
        self.check_type_equal(l, IntType(), e)
        r = self.type_check_atm(right, env)
        self.check_type_equal(r, IntType(), e)
        return IntType()
      case UnaryOp(USub(), v):
        t = self.type_check_atm(v, env)
        self.check_type_equal(t, IntType(), e)
        return IntType()
      case UnaryOp(Not(), v):
        t = self.type_check_exp(v, env)
        self.check_type_equal(t, BoolType(), e)
        return BoolType()
      case Compare(left, [cmp], [right]) if isinstance(cmp, Eq) \
                                         or isinstance(cmp, NotEq):
        l = self.type_check_atm(left, env)
        r = self.type_check_atm(right, env)
        self.check_type_equal(l, r, e)
        return BoolType()
      case Compare(left, [cmp], [right]):
        l = self.type_check_atm(left, env)
        self.check_type_equal(l, IntType(), left)
        r = self.type_check_atm(right, env)
        self.check_type_equal(r, IntType(), right)
        return BoolType()
      case Call(Name('input_int'), []):
        return IntType()
      case Begin(ss, e):
        self.type_check_stmts(ss, env)
        return self.type_check_exp(e, env)
      case _:
        raise Exception('error in type_check_exp, unexpected ' + repr(e))

  def type_check_stmts(self, ss: list[stmt], env: TypeEnv) -> None:
      for s in ss:
          self.type_check_stmt(s, env)

  def type_check_stmt(self, s: stmt, env: TypeEnv) -> None:
    match s:
      case Assign([Name(id)], value):
        t = self.type_check_exp(value, env)
        lhs_ty = env.get(id, Bottom())
        self.check_type_equal(lhs_ty, t, s)
        env[id] = self.combine_types(t, lhs_ty)
      case Expr(Call(Name('print'), [arg])):
        t = self.type_check_exp(arg, env)
        self.check_type_equal(t, IntType(), s)
      case Expr(value):
        self.type_check_exp(value, env)
      case _:
        raise Exception('error in type_check_stmt, unexpected ' + repr(s))

  def type_check_tail(self, s: stmt, env: TypeEnv) -> None:
    match s:
      case If(Compare(left, [cmp], [right]), [Goto(_)], [Goto(_)]):
        left_t = self.type_check_atm(left, env)
        right_t = self.type_check_atm(right, env)
        self.check_type_equal(left_t, right_t, s) # not quite strict enough
      case Goto(label):
        pass
      case Return(value) if value is not None:
        value_t = self.type_check_exp(value, env)
      case _:
        raise Exception('error in type_check_tail, unexpected' + repr(s))

  # Checks every block repeatedly until the environment stops changing (a
  # "fixed point"): a variable's type is only known once the block that
  # assigns it has been checked, and blocks can be in any order.
  def type_check(self, p: CProgram) -> None:
    match p:
      case CProgram(body):
          env: TypeEnv = {}
          while True:
              old_env = copy.deepcopy(env)
              for (l, ss) in body.items():
                  self.type_check_stmts(ss[:-1], env)
              # Note: this line is outside the loop, so only the *last*
              # block's tail gets checked. (Upstream has it this way too.)
              self.type_check_tail(ss[-1], env)
              if env == old_env:
                  break
          # because of explicate_control there can be undefined vars -Jeremy
          # undefs = [x for x,t in env.items() if t == Bottom()]
          # if undefs:
          #     raise Exception('error: undefined type for ' + str(undefs))
          p.var_types = env
      case _:
        raise Exception('error in type_check, unexpected ' + repr(p))
