"""Chapter 5: Booleans and Conditionals.

The chapter 4 compiler (compiler_register_allocator.Compiler) extended to
L_If. The passes, in order (figure 5.15):

    shrink                   L_If -> L_If without and/or            (5.5)
    remove_complex_operands  L_If -> L_If^mon                       (5.6)
    explicate_control        L_If^mon -> C_If (new)                 (5.7)
    select_instructions      C_If -> x86_If^Var                     (5.8)
    assign_homes             uncover_live, build_interference, allocate_registers
                             on all blocks                          (5.9)
    patch_instructions       x86_If (cmpq, movzbq restrictions)     (5.10)
    prelude_and_conclusion   adds `main` and `conclusion` blocks    (5.11)

Inherited unchanged: remove_complex_operands (extend rco_exp/rco_stmt for
the new expressions, calling super() for the old ones), color_graph, and
assign_homes, which already calls the three register allocation steps.

From here on, programs are made of blocks: CProgram.body and X86Program.body
are dicts, label -> statements/instructions.

macOS gotcha: the book's code calls label_name('start') and
label_name(generate_name('block')). Don't, in your passes: on macOS
label_name adds a "_", and X86Program/Jump printing adds it again when
writing the assembly, so the interpreters can't find a block called
"start". Plain labels ('start', 'block.3', 'conclusion') are right; the
printing takes care of the "_".

Check progress with:

    .venv/bin/python tools/progress.py --chapter 5
"""
from ast import *
from utils import *  # Begin, CProgram, Goto, generate_name, ...
# x86_ast's `arg` (an x86 operand) and `Global` deliberately replace ast.arg
# and ast.Global. In type hints, write X86Arg (see compiler.py for why).
from x86_ast import *  # type: ignore[assignment]
from x86_ast import arg as X86Arg
from graph import DirectedAdjList, UndirectedAdjList, topological_sort, transpose
import compiler_register_allocator
from compiler_register_allocator import LiveAfter

# C_If blocks: label -> statements, the last of which is the tail
# (return, goto, or if with a goto in each branch).
Blocks = dict[str, list[stmt]]


class Compiler(compiler_register_allocator.Compiler):

    ############################################################################
    # Shrink (section 5.5)
    ############################################################################

    def shrink(self, p: Module) -> Module:
        """Replace `and` and `or` with if expressions (exercise 5.2)."""
        raise NotImplementedError

    ############################################################################
    # Remove Complex Operands (section 5.6): inherited. Add the new cases
    # (Constant(bool), not, comparisons, IfExp, If, Begin) to rco_exp and
    # rco_stmt (exercise 5.3).
    ############################################################################

    ############################################################################
    # Explicate Control (section 5.7, figure 5.13)
    ############################################################################

    def create_block(self, stmts: list[stmt], basic_blocks: Blocks) -> list[stmt]:
        """Given in the book (p. 79), minus label_name (see the macOS note
        at the top): put stmts in a new block and return a goto to it,
        unless stmts is already just a goto."""
        match stmts:
            case [Goto(l)]:
                return stmts
            case _:
                label = generate_name('block')
                basic_blocks[label] = stmts
                return [Goto(label)]

    def explicate_effect(self, e: expr, cont: list[stmt],
                         basic_blocks: Blocks) -> list[stmt]:
        """Code for e as a statement: only its side effects matter."""
        raise NotImplementedError

    def explicate_assign(self, rhs: expr, lhs: expr, cont: list[stmt],
                         basic_blocks: Blocks) -> list[stmt]:
        """Code for `lhs = rhs` (lhs is always a Name)."""
        raise NotImplementedError

    def explicate_pred(self, cnd: expr, thn: list[stmt], els: list[stmt],
                       basic_blocks: Blocks) -> list[stmt]:
        """Code that runs thn if cnd is true, else els."""
        raise NotImplementedError

    def explicate_stmt(self, s: stmt, cont: list[stmt],
                       basic_blocks: Blocks) -> list[stmt]:
        raise NotImplementedError

    def explicate_control(self, p: Module) -> CProgram:
        """Exercise 5.4."""
        raise NotImplementedError

    ############################################################################
    # Select Instructions (section 5.8)
    ############################################################################

    # The parameter is now a CProgram instead of a Module, which mypy reports
    # as an incompatible override; that's expected here, hence the ignore.
    def select_instructions(self, p: CProgram) -> X86Program:  # type: ignore[override]
        """Exercise 5.5. Returns an X86Program whose body is a dict of
        blocks with the same labels as p."""
        raise NotImplementedError

    ############################################################################
    # Register allocation (section 5.9)
    ############################################################################

    def uncover_live(self, p: X86Program) -> LiveAfter:
        """Live-after sets for the instructions of every block, processing
        the blocks in reverse topological order of the control-flow graph
        (exercise 5.6; graph.py has topological_sort and transpose)."""
        raise NotImplementedError

    def build_interference(self, p: X86Program,
                           live_after: LiveAfter) -> UndirectedAdjList[location]:
        """Exercise 5.7."""
        raise NotImplementedError

    def allocate_registers(self, p: X86Program,
                           graph: UndirectedAdjList[location]) -> X86Program:
        """As in chapter 4 (color_graph doesn't change), for every block."""
        raise NotImplementedError

    ############################################################################
    # Patch Instructions (section 5.10)
    ############################################################################

    def patch_instructions(self, p: X86Program) -> X86Program:
        """Exercise 5.8."""
        raise NotImplementedError

    ############################################################################
    # Prelude & Conclusion (section 5.11)
    ############################################################################

    def prelude_and_conclusion(self, p: X86Program) -> X86Program:
        """Add a `main` block (the prelude, ending in `jmp start`) and a
        `conclusion` block."""
        raise NotImplementedError
