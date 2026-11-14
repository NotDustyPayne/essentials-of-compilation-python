"""Chapter 4: Register Allocation.

The chapter 2 compiler with register allocation added. It inherits
remove_complex_operands and select_instructions from compiler.Compiler
unchanged, and replaces the passes that chapter 4 changes.

Check progress with:

    .venv/bin/python tools/progress.py --chapter 4
"""
import compiler
from graph import UndirectedAdjList
from x86_ast import *  # X86Program, Instr, Reg, Variable, location, ...

# Instructions work as dict keys: two Instr objects are equal only if they
# are the same object, so even two identical `movq x, y` lines get separate
# entries.
LiveAfter = dict[instr, set[location]]


class Compiler(compiler.Compiler):

    ############################################################################
    # Liveness Analysis (section 4.2)
    ############################################################################

    def uncover_live(self, p: X86Program) -> LiveAfter:
        """Map each instruction to its live-after set (exercise 4.2)."""
        raise NotImplementedError

    ############################################################################
    # Build the Interference Graph (section 4.3)
    ############################################################################

    def build_interference(self, p: X86Program,
                           live_after: LiveAfter) -> UndirectedAdjList[location]:
        """Exercise 4.3."""
        raise NotImplementedError

    ############################################################################
    # Allocate Registers (section 4.4)
    ############################################################################

    def color_graph(self, graph: UndirectedAdjList[location],
                    variables: set[Variable]) -> dict[location, int]:
        """Give each variable a color 0, 1, 2, ... (figure 4.8). Use
        priority_queue.PriorityQueue to pick the most saturated variable."""
        raise NotImplementedError

    def allocate_registers(self, p: X86Program,
                           graph: UndirectedAdjList[location]) -> X86Program:
        """Replace each variable with a register or stack location
        (exercise 4.4). Also set `used_callee` on the result (section 4.6)."""
        raise NotImplementedError

    ############################################################################
    # Assign Homes (section 4.4: now uses the three functions above)
    ############################################################################

    def assign_homes(self, p: X86Program) -> X86Program:
        raise NotImplementedError

    ############################################################################
    # Patch Instructions (section 4.5)
    ############################################################################

    def patch_instructions(self, p: X86Program) -> X86Program:
        raise NotImplementedError

    ############################################################################
    # Prelude & Conclusion (section 4.6)
    ############################################################################

    def prelude_and_conclusion(self, p: X86Program) -> X86Program:
        raise NotImplementedError
