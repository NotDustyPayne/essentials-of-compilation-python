"""Chapter 4: Register Allocation.

The chapter 2 compiler with register allocation added. It inherits
remove_complex_operands and select_instructions from compiler.Compiler
unchanged, and replaces the passes that chapter 4 changes.

Check progress with:

    .venv/bin/python tools/progress.py --chapter 4
"""
import compiler
from utils import align
from priority_queue import PriorityQueue
from graph import UndirectedAdjList
from x86_ast import *  # X86Program, Instr, Reg, Variable, location, ...

# Instructions work as dict keys: two Instr objects are equal only if they
# are the same object, so even two identical `movq x, y` lines get separate
# entries.
LiveAfter = dict[instr, set[location]]

ARG_REGS = ['rdi', 'rsi', 'rdx', 'rcx', 'r8', 'r9']
CALLER_SAVED_REGS = ['rax', 'rcx', 'rdx', 'rsi', 'rdi', 'r8', 'r9', 'r10', 'r11']
# Register name -> color (book p. 55). Colors 0-10 are the registers given to
# variables; 11 and up are stack slots. Negative colors are reserved registers
# that variables never get, but they still show up as neighbors in the
# interference graph (a callq writes rax and r11).
REG_COLOR: dict[str, int] = {
    'rcx': 0, 'rdx': 1, 'rsi': 2, 'rdi': 3, 'r8': 4, 'r9': 5, 'r10': 6,
    'rbx': 7, 'r12': 8, 'r13': 9, 'r14': 10, # callee-saved registers that can be assigned
    'rax': -1, 'rsp': -2, 'rbp': -3, 'r11': -4, 'r15': -5,
}
# Color -> register name, the reverse of REG_COLOR.
COLOR_DICT: dict[int, str] = {color: reg for reg, color in REG_COLOR.items()}

class Compiler(compiler.Compiler):

    ############################################################################
    # Liveness Analysis (section 4.2)
    ############################################################################

    def uncover_live(self, p: X86Program) -> LiveAfter:
        """Map each instruction to its live-after set (exercise 4.2)."""

        assert isinstance(p.body, list)
        live_after : LiveAfter = {}
        live_before_set : set[location] = set() # represents the previous L_before(K+1) , carries over in the iterations

        last_item_flag : bool = True

        for instruction in reversed(p.body):
            if last_item_flag:
                live_after[instruction] = set()
                last_item_flag = False
            else:
                live_after[instruction] = live_before_set

            live_before_set = (live_after[instruction].difference(self.write_locations(instruction))).union(self.read_locations(instruction))

        return live_after

    def write_locations(self, instruction: instr) -> set[location]:
        match instruction:
            case Callq(_, _):
                return {Reg(r) for r in CALLER_SAVED_REGS}
            case Instr('addq' | 'subq' | 'movq', [_, dest]):
                return {dest} if isinstance(dest, location) else set()
            case Instr('negq', [dest]):
                return {dest} if isinstance(dest, location) else set()
            case _:
                raise Exception("unrecognized write pattern")

    def read_locations(self, instruction: instr) -> set[location]:
        match instruction:
            case Callq(_, num_args):
                return {Reg(r) for r in ARG_REGS[:num_args]}
            case Instr('movq', [src, _]):
                return {src} if isinstance(src, location) else set()

            case Instr('addq' | 'subq' | 'negq', args):
                return {a for a in args if isinstance(a, location)}
            case _:
                raise Exception("unrecognized read location pattern")





    ############################################################################
    # Build the Interference Graph (section 4.3)
    ############################################################################

    def build_interference(self, p: X86Program,
                           live_after: LiveAfter) -> UndirectedAdjList[location]:
        """Exercise 4.3."""
        assert isinstance(p.body, list)
        interference_graph = UndirectedAdjList[location]()

        # add vertices, any location in the Instructions
        for instruction in p.body:
            locations = self.write_locations(instruction).union(self.read_locations(instruction))
            for loc in locations:
                interference_graph.add_vertex(loc)

        # add edges
        for instruction in p.body:
            live_set = live_after[instruction]
            write_locs = self.write_locations(instruction)

            match instruction:
                case Instr('movq', [src, location() as dest]):
                    for loc in live_set:
                        if loc != src and loc != dest:
                            interference_graph.add_edge(dest, loc)
                case _:
                    for d in write_locs:
                        for v in live_set:
                            if v != d:
                                interference_graph.add_edge(d,v)

        return interference_graph

    ############################################################################
    # Allocate Registers (section 4.4)
    ############################################################################

    def color_graph(self, graph: UndirectedAdjList[location],
                    variables: set[Variable]) -> dict[location, int]:
        """Give each variable a color 0, 1, 2, ... (figure 4.8). Use
        priority_queue.PriorityQueue to pick the most saturated variable."""

        """
        follow DSATUR v
        """
        sat: dict[location, set[int]] = {}
        color: dict[location, int] = {}
        pq : PriorityQueue[Variable] = PriorityQueue(lambda a, b: len(sat[a.key]) < len(sat[b.key]))

        # build sat initial set. add all the variable nodes, then add their initial saturation levels.

        # initialization. Gives us sat with the existing registers, and also fills the PQ
        for node in graph.vertices():
            if isinstance(node, Variable):
                sat[node] = set()

                for neighbor in graph.adjacent(node):
                    if isinstance(neighbor, Reg):
                        sat[node].add(REG_COLOR[neighbor.id])
                pq.push(node)

        # now do the algorithm from the text book, pop off a saturated node, color it, update the other neighbors and fix the pq as we go
        while pq.empty() is False:
            saturated_node = pq.pop()
            color[saturated_node] = self.find_lowest_color(saturated_node, sat)

            # update saturation of all nodes
            for neighbor in graph.adjacent(saturated_node):
                if isinstance(neighbor, Variable) and neighbor not in color:
                    sat[neighbor].add(color[saturated_node])
                    pq.increase_key(neighbor)


        return color


    def find_lowest_color(self, node: location, sat: dict[location, set[int]]) -> int:

        color_int : int = 0
        while color_int in sat[node]:
            color_int = color_int + 1
        return color_int

    def allocate_registers(self, p: X86Program,
                           graph: UndirectedAdjList[location]) -> X86Program:
        """Replace each variable with a register or stack location
        (exercise 4.4). Also set `used_callee` on the result (section 4.6)."""
        assert isinstance(p.body, list)
        graph_colors = self.color_graph(graph, set())

        # we need to loop through and replace any variables in the instructions with their color representations
        # we need to calculate when these things become stack locations
        #
        allocated_instructions : list[instr] = []

        used_callee: set[Reg] = {Reg(COLOR_DICT[c]) for c in graph_colors.values() if 7 <= c <= 10}
        reserved_offset = len(used_callee)
        spill_colors = {color for color in graph_colors.values() if color > 10}
        spill_slots = len(spill_colors)

        for instruction in p.body:
            # match on the Instruction
            match instruction:
                case Instr(name, args):
                    allocated_args : list[arg] = []
                    for a in args:
                        if isinstance(a, Variable):
                            if graph_colors[a] <= 10:
                                # adding a color dict item
                                allocated_args.append(Reg(COLOR_DICT[graph_colors[a]]))
                            else:
                                # this means that we don't have a register for it, so it has to go on the stack somehow
                                allocated_args.append(Deref('rbp', -8 * (reserved_offset + (graph_colors[a] - 10))))
                        else:
                            allocated_args.append(a)
                    allocated_instructions.append(Instr(name, allocated_args))
                case _:
                    allocated_instructions.append(instruction)

        allocated_stack_space: int = align(8 * (reserved_offset + spill_slots), 16) - (8 * reserved_offset)


        allocated_program = X86Program(body = allocated_instructions, stack_space = allocated_stack_space, used_callee=used_callee)
        return allocated_program





    ############################################################################
    # Assign Homes (section 4.4: now uses the three functions above)
    ############################################################################

    def assign_homes(self, p: X86Program) -> X86Program:
        live_after_set = self.uncover_live(p)
        g = self.build_interference(p, live_after_set)
        return self.allocate_registers(p, g)


    def patch_instr(self, i: instr) -> list[instr]:
        match i:
            case Instr('movq', [src,dest]) if src == dest:
                return []
            case _:
                return super().patch_instr(i)


    ############################################################################
    # Prelude & Conclusion (section 4.6)
    ############################################################################

    def prelude_and_conclusion(self, p: X86Program) -> X86Program:
        raise NotImplementedError
