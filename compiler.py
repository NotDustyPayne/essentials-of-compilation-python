import ast
from ast import *
from utils import *
# x86_ast's `arg` (an x86 operand) and `Global` deliberately replace ast.arg and
# ast.Global from `from ast import *`. For function parameters, write ast.arg.
from x86_ast import *  # type: ignore[assignment]
import os

# Use the built-in list/tuple/dict/set for type hints. Importing
# typing.List / typing.Tuple here would hide ast.List / ast.Tuple, which
# you'll pattern-match on in later chapters (`case Tuple(...)`).

# A temporary variable and the expression it's bound to (from RCO).
Binding = tuple[Name, expr]
Temporaries = list[Binding]


class Compiler:

    ############################################################################
    # Remove Complex Operands
    ############################################################################

    def rco_exp(self, e: expr, need_atomic : bool) -> tuple[expr, Temporaries]:
        # YOUR CODE HERE
        raise NotImplementedError

    def rco_stmt(self, s: stmt) -> list[stmt]:
        # YOUR CODE HERE
        raise NotImplementedError

    def remove_complex_operands(self, p: Module) -> Module:
        # YOUR CODE HERE
        raise NotImplementedError

    ############################################################################
    # Select Instructions
    ############################################################################

    # The expression e passed to select_arg should furthermore be an atom.
    # (But there is no type for atoms, so the type of e is given as expr.)
    def select_arg(self, e: expr) -> arg:
        # YOUR CODE HERE
        raise NotImplementedError

    def select_stmt(self, s: stmt) -> list[instr]:
        # YOUR CODE HERE
        raise NotImplementedError

    def select_instructions(self, p: Module) -> X86Program:
        # YOUR CODE HERE
        raise NotImplementedError

    ############################################################################
    # Assign Homes
    ############################################################################

    def assign_homes_arg(self, a: arg, home: dict[Variable, arg]) -> arg:
        # YOUR CODE HERE
        raise NotImplementedError

    def assign_homes_instr(self, i: instr,
                           home: dict[Variable, arg]) -> instr:
        # YOUR CODE HERE
        raise NotImplementedError

    def assign_homes(self, p: X86Program) -> X86Program:
        # YOUR CODE HERE
        raise NotImplementedError

    ############################################################################
    # Patch Instructions
    ############################################################################

    def patch_instr(self, i: instr) -> list[instr]:
        # YOUR CODE HERE
        raise NotImplementedError

    def patch_instructions(self, p: X86Program) -> X86Program:
        # YOUR CODE HERE
        raise NotImplementedError

    ############################################################################
    # Prelude & Conclusion
    ############################################################################

    def prelude_and_conclusion(self, p: X86Program) -> X86Program:
        # YOUR CODE HERE
        raise NotImplementedError

