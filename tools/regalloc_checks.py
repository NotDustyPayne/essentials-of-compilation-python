"""Chapter 4 (register allocation) checks for tools/progress.py.

Three kinds of check:

1. Book examples. uncover_live, build_interference, color_graph and
   allocate_registers are run on small x86_Var programs from the chapter,
   and compared against the book's own answers (figures 4.3-4.6) or checked
   for the properties a correct answer must have.

2. Allocation checks on every test program, comparing the output of
   select_instructions (before) with the output of assign_homes (after):
   every variable gets one home, no reserved register is handed out, two
   variables that interfere don't share a home, call-live variables avoid
   caller-saved registers, and spilled variables sit below the saved
   callee-saved registers.

3. Register poisoning. x86 interpreters don't model function calls
   overwriting registers, so a variable wrongly kept in a caller-saved
   register across `callq print_int` would still give the right answer.
   `poison_calls` inserts, after every callq, instructions that overwrite
   each caller-saved register with garbage (except %rax after read_int,
   which holds the result), the way a real call is allowed to.

None of this computes liveness or interference itself: the expected answers
are the book's, written out by hand.
"""
from __future__ import annotations

import dataclasses
import traceback
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any

from graph import UndirectedAdjList
from x86_ast import (Callq, Deref, Immediate, Instr, Reg, Variable, X86Program,
                     arg, instr, location)

# Section 4.1 and the color numbering suggested in section 4.4.
CALLER_SAVED = ['rax', 'rcx', 'rdx', 'rsi', 'rdi', 'r8', 'r9', 'r10', 'r11']
CALLEE_SAVED = ['rsp', 'rbp', 'rbx', 'r12', 'r13', 'r14', 'r15']
ARG_REGISTERS = ['rdi', 'rsi', 'rdx', 'rcx', 'r8', 'r9']
ALLOCATABLE = ['rcx', 'rdx', 'rsi', 'rdi', 'r8', 'r9', 'r10',
               'rbx', 'r12', 'r13', 'r14']
RESERVED_WHY = {
    'rax': 'patch_instructions uses it as a scratch register, and calls return in it',
    'r11': 'patch_instructions uses it as a scratch register for big immediates',
    'rsp': 'it is the stack pointer',
    'rbp': 'it is the frame pointer',
    'r15': 'the book reserves it (it becomes the root-stack pointer in chapter 6)',
}

LiveAfter = dict[instr, set[location]]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def name_of(loc: object) -> str:
    """Variable('x') -> 'x', Reg('rdi') -> '%rdi'."""
    match loc:
        case Variable(x):
            return x
        case Reg(r):
            return '%' + r
    return repr(loc)


def body_of(p: X86Program) -> list[instr]:
    if isinstance(p.body, dict):
        return p.body.get('main', [])
    return p.body


def fmt_set(names: Iterable[str]) -> str:
    return '{' + ', '.join(sorted(names)) + '}'


def _edge_key(u: object, v: object) -> frozenset[str]:
    return frozenset([name_of(u), name_of(v)])


def variable_edges(g: Any) -> set[frozenset[str]]:
    """Edges of an interference graph that involve at least one variable
    (register-register edges don't matter for allocation)."""
    out: set[frozenset[str]] = set()
    for e in g.edges():
        if isinstance(e.source, Variable) or isinstance(e.target, Variable):
            if e.source != e.target:
                out.add(_edge_key(e.source, e.target))
    return out


def fmt_edge(e: frozenset[str]) -> str:
    return ' -- '.join(sorted(e))


def call_safely(f: Callable[[], Any]) -> tuple[Any, str | None]:
    """Run f(); return (result, None), or (None, 'todo'/traceback)."""
    try:
        return f(), None
    except NotImplementedError:
        return None, 'todo'
    except Exception:
        return None, traceback.format_exc(limit=-3).strip()


# ---------------------------------------------------------------------------
# Register poisoning
# ---------------------------------------------------------------------------

def poison_calls(p: X86Program) -> X86Program:
    """A copy of p where every callq is followed by writes of junk values to
    the caller-saved registers it may overwrite."""
    def poisoned(body: list[instr]) -> list[instr]:
        out: list[instr] = []
        for i in body:
            out.append(i)
            if isinstance(i, Callq):
                for k, r in enumerate(CALLER_SAVED):
                    if r == 'rax' and i.func == 'read_int':
                        continue
                    out.append(Instr('movq', [Immediate(0x5EED0000 + 1111 * k), Reg(r)]))
        return out
    if isinstance(p.body, dict):
        return dataclasses.replace(p, body={k: poisoned(b) for k, b in p.body.items()})
    return dataclasses.replace(p, body=poisoned(p.body))


# ---------------------------------------------------------------------------
# Allocation checks (assign_homes output vs. select_instructions output)
# ---------------------------------------------------------------------------

def variable_homes(before: X86Program, after: X86Program,
                   problems: list[str]) -> dict[str, arg]:
    """Line up the instructions before and after assign_homes and read off
    where each variable went. Section 4.4 assumes each variable gets exactly
    one location for the whole program."""
    b, a = body_of(before), body_of(after)
    if len(b) != len(a):
        problems.append(f'assign_homes changed the number of instructions ({len(b)} -> {len(a)}); '
                        'it should only replace variables (deleting moves is patch_instructions\' job)')
        return {}
    homes: dict[str, arg] = {}
    for ib, ia in zip(b, a):
        if not (isinstance(ib, Instr) and isinstance(ia, Instr)):
            continue
        if ib.instr != ia.instr or len(ib.args) != len(ia.args):
            problems.append(f'instruction changed: `{str(ib).strip()}` became `{str(ia).strip()}`')
            continue
        for x, y in zip(ib.args, ia.args):
            if isinstance(x, Variable):
                if x.id in homes and homes[x.id] != y:
                    problems.append(f'variable {x.id} is in two places: {homes[x.id]} and {y}')
                homes.setdefault(x.id, y)
    return homes


def check_homes(homes: dict[str, arg], used_callee: object,
                edges: set[frozenset[str]] | None,
                call_live: dict[str, str]) -> list[str]:
    """Properties every register allocation must have.

    edges: the interference edges to respect (None to skip).
    call_live: variable -> name of a call it is live across."""
    problems: list[str] = []
    callee_used: set[str] = set()
    for x, h in sorted(homes.items()):
        match h:
            case Reg(r) if r in RESERVED_WHY:
                problems.append(f'variable {x} was given %{r}, which is reserved: {RESERVED_WHY[r]}')
            case Reg(r) if r in ALLOCATABLE:
                if r in CALLEE_SAVED:
                    callee_used.add(r)
                if x in call_live and r in CALLER_SAVED:
                    problems.append(f'{x} is live across `callq {call_live[x]}` but was put in '
                                    f'caller-saved %{r}, which the call may overwrite (section 4.1)')
            case Deref('rbp', off) if off < 0 and off % 8 == 0:
                pass
            case _:
                problems.append(f'variable {x} was given {h}; homes should be registers or '
                                'stack slots like -8(%rbp)')

    # Spilled variables go below the saved callee-saved registers (section 4.6).
    c = len(callee_used)
    for x, h in sorted(homes.items()):
        if isinstance(h, Deref) and h.reg == 'rbp' and -h.offset <= 8 * c:
            problems.append(f'{x} was spilled to {h}, but with {c} callee-saved register(s) in use '
                            f'the prelude saves them at -8(%rbp)..{-8 * c}(%rbp); spilled variables '
                            f'must start at {-8 * (c + 1)}(%rbp) (section 4.6)')

    if homes and not any(isinstance(h, Reg) for h in homes.values()):
        problems.append('no variable was put in a register (is assign_homes still the chapter 2 version?)')

    if used_callee is None:
        problems.append('X86Program.used_callee is not set; allocate_registers should record the '
                        'callee-saved registers it used (section 4.6)')
    else:
        given = None
        if isinstance(used_callee, (set, frozenset, list, tuple)):
            given = {x.id if isinstance(x, Reg) else str(x).lstrip('%') for x in used_callee}
        if given is None:
            problems.append(f'used_callee should be a set of registers, got {used_callee!r}')
        elif given != callee_used:
            problems.append(f'used_callee is {fmt_set(given)} but the callee-saved registers given '
                            f'to variables are {fmt_set(callee_used)}')

    if edges is not None:
        for e in sorted(edges, key=fmt_edge):
            u, v = sorted(e)
            hu = homes.get(u) if not u.startswith('%') else Reg(u[1:])
            hv = homes.get(v) if not v.startswith('%') else Reg(v[1:])
            if hu is not None and hu == hv:
                problems.append(f'{u} and {v} interfere but were both given {hu}')
    return problems


def check_allocation(c: Any, before: X86Program, after: object) -> list[str]:
    """Allocation checks for one test program, using the student's own
    uncover_live and build_interference to know what interferes."""
    if not isinstance(after, X86Program):
        return []  # the plain shape check reports this
    problems: list[str] = []
    homes = variable_homes(before, after, problems)
    if problems:
        return problems

    edges: set[frozenset[str]] | None = None
    call_live: dict[str, str] = {}
    live, err = call_safely(lambda: c.uncover_live(before))
    if err is None and isinstance(live, dict):
        for i in body_of(before):
            if isinstance(i, Callq):
                for loc in live.get(i, set()):
                    if isinstance(loc, Variable):
                        call_live.setdefault(loc.id, i.func)
        g, err = call_safely(lambda: c.build_interference(before, live))
        if err is None and g is not None:
            edges = variable_edges(g)
    return check_homes(homes, after.used_callee, edges, call_live)


# ---------------------------------------------------------------------------
# Book examples
# ---------------------------------------------------------------------------

def v(x: str) -> Variable:
    return Variable(x)


def r(x: str) -> Reg:
    return Reg(x)


def movq(a: arg, b: arg) -> Instr:
    return Instr('movq', [a, b])


def addq(a: arg, b: arg) -> Instr:
    return Instr('addq', [a, b])


def subq(a: arg, b: arg) -> Instr:
    return Instr('subq', [a, b])


def negq(a: arg) -> Instr:
    return Instr('negq', [a])


def imm(n: int) -> Immediate:
    return Immediate(n)


@dataclass
class Example:
    name: str
    where: str                     # where it comes from in the book
    body: list[instr]
    live_after: list[set[str]]     # expected L_after, one set per instruction
    edges: set[frozenset[str]]     # expected edges that involve a variable

    def program(self) -> X86Program:
        return X86Program(list(self.body))

    def live_dict(self) -> LiveAfter:
        """The expected live-after sets as uncover_live would return them."""
        def loc(n: str) -> location:
            return Reg(n[1:]) if n.startswith('%') else Variable(n)
        return {i: {loc(n) for n in s} for i, s in zip(self.body, self.live_after)}

    def graph(self) -> UndirectedAdjList[location]:
        g: UndirectedAdjList[location] = UndirectedAdjList()
        for i in self.body:
            if isinstance(i, Instr):
                for a in i.args:
                    if isinstance(a, Variable):
                        g.add_vertex(a)
        def loc(n: str) -> location:
            return Reg(n[1:]) if n.startswith('%') else Variable(n)
        for e in self.edges:
            n1, n2 = sorted(e)
            g.add_edge(loc(n1), loc(n2))
        return g


def E(*pairs: str) -> set[frozenset[str]]:
    return {frozenset(p.split('-')) for p in pairs}


def S(*names: str) -> set[str]:
    return set(names)


CALLER_SAVED_NAMES = ['%' + x for x in CALLER_SAVED]

EXAMPLES: list[Example] = [
    Example(
        'two writes to b', 'section 4.2, figure 4.3',
        [movq(imm(5), v('a')), movq(imm(30), v('b')), movq(v('a'), v('c')),
         movq(imm(10), v('b')), addq(v('b'), v('c'))],
        [S('a'), S('a'), S('c'), S('b', 'c'), S()],
        # Rule 1 (section 4.3): the write to b on line 2 happens while a is live.
        E('a-b', 'b-c'),
    ),
    Example(
        'running example', 'figures 4.1, 4.4, 4.5, 4.6',
        [movq(imm(1), v('v')), movq(imm(42), v('w')), movq(v('v'), v('x')),
         addq(imm(7), v('x')), movq(v('x'), v('y')), movq(v('x'), v('z')),
         addq(v('w'), v('z')), movq(v('y'), v('tmp_0')), negq(v('tmp_0')),
         movq(v('z'), v('tmp_1')), addq(v('tmp_0'), v('tmp_1')),
         movq(v('tmp_1'), r('rdi')), Callq('print_int', 1)],
        [S('v'), S('w', 'v'), S('w', 'x'), S('w', 'x'), S('w', 'x', 'y'),
         S('w', 'y', 'z'), S('y', 'z'), S('tmp_0', 'z'), S('tmp_0', 'z'),
         S('tmp_0', 'tmp_1'), S('tmp_1'), S('%rdi'), S()],
        E('v-w', 'w-x', 'w-y', 'w-z', 'y-z', 'tmp_0-z', 'tmp_0-tmp_1'),
    ),
    Example(
        'calls to read_int', 'figure 4.2 (x is call-live)',
        [Callq('read_int', 0), movq(r('rax'), v('x')), Callq('read_int', 0),
         movq(r('rax'), v('y')), movq(v('x'), v('tmp_0')), addq(v('y'), v('tmp_0')),
         movq(v('tmp_0'), v('tmp_1')), addq(imm(42), v('tmp_1')),
         movq(v('tmp_1'), r('rdi')), Callq('print_int', 1)],
        [S('%rax'), S('x'), S('x', '%rax'), S('x', 'y'), S('y', 'tmp_0'),
         S('tmp_0'), S('tmp_1'), S('tmp_1'), S('%rdi'), S()],
        E('x-y', 'y-tmp_0', *[f'x-{reg}' for reg in CALLER_SAVED_NAMES]),
    ),
    Example(
        'subq and negq', 'formula 4.3: subq and negq read and write their target',
        [movq(imm(10), v('a')), movq(imm(3), v('b')), subq(v('b'), v('a')),
         negq(v('a')), movq(v('a'), r('rdi')), Callq('print_int', 1)],
        [S('a'), S('a', 'b'), S('a'), S('a'), S('%rdi'), S()],
        E('a-b'),
    ),
]


@dataclass
class ExampleResult:
    example: str
    status: str   # 'ok', 'wrong', 'crash', 'todo'
    detail: str = ''


def _result(name: str, err: str | None, problems: list[str]) -> ExampleResult:
    if err == 'todo':
        return ExampleResult(name, 'todo')
    if err is not None:
        return ExampleResult(name, 'crash', err)
    if problems:
        return ExampleResult(name, 'wrong', '\n'.join(problems[:6]))
    return ExampleResult(name, 'ok')


def check_uncover_live(c: Any, ex: Example) -> ExampleResult:
    p = ex.program()
    live, err = call_safely(lambda: c.uncover_live(p))
    problems: list[str] = []
    if err is None:
        if not isinstance(live, dict):
            problems.append(f'uncover_live should return a dict (instruction -> live-after set), '
                            f'got {type(live).__name__}')
        else:
            for k, (i, want) in enumerate(zip(body_of(p), ex.live_after), 1):
                if i not in live:
                    problems.append(f'line {k} `{str(i).strip()}`: no live-after set')
                    continue
                got = {name_of(loc) for loc in live[i]}
                if got != want:
                    problems.append(f'line {k} `{str(i).strip()}`: live-after should be '
                                    f'{fmt_set(want)}, got {fmt_set(got)}')
    return _result(ex.name, err, problems)


def check_build_interference(c: Any, ex: Example) -> ExampleResult:
    # Feed the book's live-after sets, so a liveness bug doesn't show up here.
    p = ex.program()
    live = ex.live_dict()
    g, err = call_safely(lambda: c.build_interference(p, live))
    problems: list[str] = []
    if err is None:
        if not hasattr(g, 'edges'):
            problems.append(f'build_interference should return an UndirectedAdjList, got {type(g).__name__}')
        else:
            got = variable_edges(g)
            for e in sorted(ex.edges - got, key=fmt_edge):
                problems.append(f'missing edge {fmt_edge(e)}')
            for e in sorted(got - ex.edges, key=fmt_edge):
                problems.append(f'extra edge {fmt_edge(e)}')
    return _result(ex.name, err, problems)


def check_color_graph(c: Any, ex: Example) -> ExampleResult:
    g = ex.graph()
    variables = {x for x in g.vertices() if isinstance(x, Variable)}
    colors, err = call_safely(lambda: c.color_graph(g, variables))
    problems: list[str] = []
    if err is None:
        if not isinstance(colors, dict):
            problems.append(f'color_graph should return a dict (variable -> color), got {type(colors).__name__}')
        else:
            for x in sorted(variables, key=name_of):
                col = colors.get(x)
                if not isinstance(col, int) or col < 0:
                    problems.append(f'{x} should get a color 0, 1, 2, ...; got {col!r}')
            for e in sorted(ex.edges, key=fmt_edge):
                a, b = sorted(e)
                if a.startswith('%') or b.startswith('%'):
                    continue
                if colors.get(Variable(a)) == colors.get(Variable(b)) is not None:
                    problems.append(f'{a} and {b} interfere but both got color {colors.get(Variable(a))}')
    return _result(ex.name, err, problems)


def spill_example() -> tuple[X86Program, UndirectedAdjList[location]]:
    """13 variables that all interfere: more than the 11 registers."""
    n = 13
    xs = [Variable(f'x{k}') for k in range(n)]
    body: list[instr] = [movq(imm(k), xs[k]) for k in range(n)]
    body += [addq(xs[k], xs[0]) for k in range(1, n)]
    body += [movq(xs[0], r('rdi')), Callq('print_int', 1)]
    g: UndirectedAdjList[location] = UndirectedAdjList()
    for a in xs:
        g.add_vertex(a)
    for i in range(n):
        for j in range(i + 1, n):
            g.add_edge(xs[i], xs[j])
    return X86Program(body), g


def check_allocate_registers(c: Any, name: str, p: X86Program,
                             g: UndirectedAdjList[location], need_spill: bool) -> ExampleResult:
    before = X86Program(list(body_of(p)))
    after, err = call_safely(lambda: c.allocate_registers(p, g))
    problems: list[str] = []
    if err is None:
        if not isinstance(after, X86Program):
            problems.append(f'allocate_registers should return an X86Program, got {type(after).__name__}')
        else:
            homes = variable_homes(before, after, problems)
            left = [str(i).strip() for i in body_of(after) if isinstance(i, Instr)
                    and any(isinstance(a, Variable) for a in i.args)]
            if left:
                problems.append(f'variables left in the program: `{left[0]}`')
            # A call-live variable has edges to the caller-saved registers,
            # so checking the edges also keeps it out of those registers.
            problems += check_homes(homes, after.used_callee, variable_edges(g), {})
            if need_spill and not any(isinstance(h, Deref) for h in homes.values()):
                problems.append('13 variables that all interfere need at least two stack slots')
    return _result(name, err, problems)


def run_examples(c: Any) -> dict[str, list[ExampleResult]]:
    """Book-example results for each analysis step, in pipeline order."""
    out: dict[str, list[ExampleResult]] = {
        'uncover_live': [check_uncover_live(c, ex) for ex in EXAMPLES],
        'build_interference': [check_build_interference(c, ex) for ex in EXAMPLES],
        'color_graph': [check_color_graph(c, ex) for ex in EXAMPLES[1:3]],
    }
    alloc = []
    for ex in EXAMPLES[1:3]:
        alloc.append(check_allocate_registers(c, ex.name, ex.program(), ex.graph(), False))
    p, g = spill_example()
    alloc.append(check_allocate_registers(c, '13 interfering variables', p, g, True))
    out['allocate_registers'] = alloc
    return out


EXAMPLE_SECTION = {
    'uncover_live': '4.2',
    'build_interference': '4.3',
    'color_graph': '4.4',
    'allocate_registers': '4.4',
}
