from ast import *
from interp_Lif import InterpLif
from interp_Lint import InterpValue, Env
from utils import *

class InterpCif(InterpLif):
  # The program being run: label -> that block's statements (set by interp).
  blocks: dict[str, list[stmt]]

  # A C_If program is a CProgram, not a Module, so this overrides interp with
  # a different parameter type. mypy flags that ([override]): code holding an
  # InterpLif could pass a Module here. That's fine in practice, since each
  # interpreter is only ever given its own language.
  def interp(self, p: CProgram) -> None:  # type: ignore[override]
    match p:
      case CProgram(blocks):
        env: Env = {}
        self.blocks = blocks
        self.interp_stmts(blocks['start'], env)

  # In C_If the last statement of a block is its tail (return, goto, or if),
  # which decides where to go next; the others are ordinary statements.
  def interp_stmts(self, ss: list[stmt], env: Env) -> InterpValue:
    match ss:
      case [t]:
        return self.interp_tail(t, env)
      case [s, *ss]:
        self.interp_stmt(s, env, [])
        return self.interp_stmts(ss, env)

  def interp_tail(self, s: stmt, env: Env) -> InterpValue:
    match s:
      case Return(value):
        assert value is not None
        return self.interp_exp(value, env)
      case Goto(label):
        return self.interp_stmts(self.blocks[label], env)
      case If(test, [Goto(thn)], [Goto(els)]):
        match self.interp_exp(test, env):
          case True:
            return self.interp_stmts(self.blocks[thn], env)
          case False:
            return self.interp_stmts(self.blocks[els], env)
      case _:
        raise Exception('interp_tail: unexpected ' + repr(s))
