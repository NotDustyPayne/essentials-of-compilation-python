"""Shape checkers: does a pass's output belong to its target language?

run-tests.py only checks that each pass preserves the program's output. That
is necessary but not enough: a pass that returns its input unchanged also
preserves the output. These checkers test the other half, that each pass
produced the language the book says it should (figure 2.10):

    L_Var --rco--> L_Var^mon --select--> x86_Var --assign homes--> x86_Var
          (no variables) --patch--> x86_Int --prelude--> x86_Int (main)

Chapter 4 tightens the last two checks, and chapter 5 (figure 5.15) has its
own set, at the end of this file.

Each checker returns a list of human-readable problems. An empty list means
the program has the right shape.
"""
from __future__ import annotations

import ast
from ast import (Add, Assign, BinOp, Call, Constant, Expr, Module, Name,
                 Sub, UnaryOp, USub, expr, stmt)
from typing import Callable

from ast import Return

from utils import Begin, CProgram, Goto
from x86_ast import (ByteReg, Callq, Deref, Immediate, Instr, Jump, JumpIf, Reg,
                     Variable, X86Program, arg, instr)

REGISTERS = {'rsp', 'rbp', 'rax', 'rbx', 'rcx', 'rdx', 'rsi', 'rdi',
             'r8', 'r9', 'r10', 'r11', 'r12', 'r13', 'r14', 'r15'}

# Instruction name -> number of arguments (x86_Int, figure 2.9).
INSTR_ARITY = {'addq': 2, 'subq': 2, 'movq': 2, 'negq': 1,
               'pushq': 1, 'popq': 1, 'retq': 0}

INT32_MIN, INT32_MAX = -(1 << 31), (1 << 31) - 1


def _src(node: ast.AST) -> str:
    """Show a node as Python-like source in error messages."""
    try:
        return ast.unparse(node)
    except Exception:
        return repr(node)


# ---------------------------------------------------------------------------
# L_Var (figure 2.2): checks that a test program stays inside the language
# ---------------------------------------------------------------------------

def _is_input_int(e: expr) -> bool:
    match e:
        case Call(Name('input_int'), []):
            return True
    return False


def _lvar_exp(e: expr, problems: list[str]) -> None:
    match e:
        case Constant(value) if isinstance(value, int) and not isinstance(value, bool):
            pass
        case Name(_):
            pass
        case _ if _is_input_int(e):
            pass
        case UnaryOp(USub(), v):
            _lvar_exp(v, problems)
        case BinOp(left, Add() | Sub(), right):
            _lvar_exp(left, problems)
            _lvar_exp(right, problems)
        case _:
            problems.append(f'not an L_Var expression: {_src(e)}')


def check_Lvar(p: Module) -> list[str]:
    """Figure 2.2. Used to validate the test programs themselves."""
    problems: list[str] = []
    for s in p.body:
        match s:
            case Expr(Call(Name('print'), [e])):
                _lvar_exp(e, problems)
            case Expr(e):
                _lvar_exp(e, problems)
            case Assign([Name(_)], e):
                _lvar_exp(e, problems)
            case _:
                problems.append(f'not an L_Var statement: {_src(s)}')
    return problems


# ---------------------------------------------------------------------------
# L_Var^mon (figure 2.11): output of remove_complex_operands
# ---------------------------------------------------------------------------

def _is_atomic(e: expr) -> bool:
    match e:
        case Constant(value) if isinstance(value, int):
            return True
        case Name(_):
            return True
    return False


def _mon_exp(e: expr, where: str, problems: list[str]) -> None:
    """exp ::= atm | input_int() | -atm | atm + atm | atm - atm"""
    match e:
        case _ if _is_atomic(e) or _is_input_int(e):
            pass
        case UnaryOp(USub(), v):
            if not _is_atomic(v):
                problems.append(f'operand of - is not atomic: `{_src(v)}` in `{where}`')
        case BinOp(left, Add() | Sub(), right):
            for side in (left, right):
                if not _is_atomic(side):
                    problems.append(f'operand of {"+" if isinstance(e.op, Add) else "-"} '
                                    f'is not atomic: `{_src(side)}` in `{where}`')
        case _:
            problems.append(f'not an L_Var^mon expression: `{_src(e)}` in `{where}`')


def check_Lvar_mon(p: object) -> list[str]:
    """Figure 2.11: every operand of an operation must be atomic
    (a constant or a variable)."""
    if not isinstance(p, Module):
        return [f'expected a Module, got {type(p).__name__}']
    problems: list[str] = []
    for s in p.body:
        where = _src(s)
        match s:
            case Expr(Call(Name('print'), [e])):
                if not _is_atomic(e):
                    problems.append(f'argument of print is not atomic: `{_src(e)}`')
            case Expr(e):
                _mon_exp(e, where, problems)
            case Assign([Name(_)], e):
                _mon_exp(e, where, problems)
            case _:
                problems.append(f'not an L_Var^mon statement: `{where}`')
    return problems


# ---------------------------------------------------------------------------
# x86 (figure 2.9 and sections 2.5-2.8)
# ---------------------------------------------------------------------------

def _main_body(p: object, problems: list[str]) -> list[instr]:
    if not isinstance(p, X86Program):
        problems.append(f'expected an X86Program, got {type(p).__name__}')
        return []
    if isinstance(p.body, dict):
        if 'main' not in p.body:
            problems.append('X86Program body is a dict without a "main" block')
            return []
        return p.body['main']
    return p.body


def _check_arg(a: arg, i: instr, allow_vars: bool, problems: list[str]) -> None:
    match a:
        case Immediate(value):
            if not isinstance(value, int):
                problems.append(f'immediate is not an int: {i}')
        case Reg(name):
            if name not in REGISTERS:
                problems.append(f'unknown register %{name}: {i}')
        case Deref(reg, offset):
            if reg not in REGISTERS or not isinstance(offset, int):
                problems.append(f'bad memory operand: {i}')
        case Variable(_):
            if not allow_vars:
                problems.append(f'variable left in the program: `{str(i).strip()}`')
        case _:
            problems.append(f'unexpected argument {a!r} in: {i}')


def _check_instrs(body: list[instr], allow_vars: bool, problems: list[str]) -> None:
    for i in body:
        match i:
            case Instr(name, args):
                if name not in INSTR_ARITY:
                    problems.append(f'unknown instruction "{name}": {str(i).strip()}')
                elif len(args) != INSTR_ARITY[name]:
                    problems.append(f'{name} takes {INSTR_ARITY[name]} argument(s): {str(i).strip()}')
                for a in args:
                    _check_arg(a, i, allow_vars, problems)
            case Callq(func, num_args):
                if not isinstance(func, str) or not isinstance(num_args, int):
                    problems.append(f'bad callq: {i!r}')
            case Jump(_):
                pass
            case _:
                problems.append(f'not an x86 instruction: {i!r}')


def check_x86_var(p: object) -> list[str]:
    """Output of select_instructions: x86 instructions, variables allowed,
    no restriction on memory operands yet (x86_Var, section 2.5)."""
    problems: list[str] = []
    body = _main_body(p, problems)
    _check_instrs(body, allow_vars=True, problems=problems)
    if not problems and not body:
        problems.append('program has no instructions')
    return problems


def check_x86_homes(p: object) -> list[str]:
    """Output of assign_homes: x86_Var with every variable replaced by a
    register or stack location (section 2.6)."""
    problems: list[str] = []
    body = _main_body(p, problems)
    _check_instrs(body, allow_vars=False, problems=problems)
    return problems


def _fits_int32(a: arg) -> bool:
    return not isinstance(a, Immediate) or INT32_MIN <= a.value <= INT32_MAX


def _check_x86_int_rules(body: list[instr], problems: list[str]) -> None:
    """Section 2.7: at most one memory operand per instruction, and
    immediates must fit what real x86 accepts."""
    for i in body:
        if not isinstance(i, Instr):
            continue
        memory = [a for a in i.args if isinstance(a, Deref)]
        if len(memory) > 1:
            problems.append(f'two memory operands: `{str(i).strip()}`')
        # The book says "larger than 2^16" to be safe. The real rule: only
        # `movq $imm, %register` accepts a full 64-bit immediate; every
        # other instruction takes a 32-bit immediate.
        big = [a for a in i.args if not _fits_int32(a)]
        if big and not (i.instr == 'movq' and isinstance(i.args[1], Reg)):
            problems.append(f'immediate too big for this instruction: `{str(i).strip()}`')


def check_x86_int(p: object) -> list[str]:
    """Output of patch_instructions: valid x86_Int (figure 2.9, section 2.7)."""
    problems: list[str] = []
    body = _main_body(p, problems)
    _check_instrs(body, allow_vars=False, problems=problems)
    _check_x86_int_rules(body, problems)
    return problems


def check_x86_final(p: object) -> list[str]:
    """Output of prelude_and_conclusion (section 2.8, figure 2.7): valid
    x86_Int with a 16-byte-aligned frame that ends in retq."""
    problems = check_x86_int(p)
    body = _main_body(p, [])
    if body:
        last = body[-1]
        if not (isinstance(last, Instr) and last.instr == 'retq'):
            problems.append(f'main should end with retq, ends with `{str(last).strip()}`')
        for i in body:
            match i:
                case Instr('subq', [Immediate(n), Reg('rsp')]) if n % 16 != 0:
                    problems.append(f'frame size {n} is not a multiple of 16: `{str(i).strip()}`')
    return problems


# Pass name -> checker for that pass's output.
CHECKERS: dict[str, Callable[[object], list[str]]] = {
    'remove_complex_operands': check_Lvar_mon,
    'select_instructions': check_x86_var,
    'assign_homes': check_x86_homes,
    'patch_instructions': check_x86_int,
    'prelude_and_conclusion': check_x86_final,
}


# ---------------------------------------------------------------------------
# Chapter 4: register allocation (sections 4.5 and 4.6)
# ---------------------------------------------------------------------------

CALLEE_SAVED_REGS = ['rbx', 'r12', 'r13', 'r14', 'r15']  # plus rsp and rbp


def check_x86_int_ch4(p: object) -> list[str]:
    """Output of patch_instructions in chapter 4: valid x86_Int, and the
    trivial moves (same source and destination) are deleted (section 4.5)."""
    problems = check_x86_int(p)
    for i in _main_body(p, []):
        match i:
            case Instr('movq', [a, b]) if a == b:
                problems.append(f'trivial move left in (delete it, section 4.5): `{str(i).strip()}`')
    return problems


def _is(i: instr, name: str, *args: arg) -> bool:
    return isinstance(i, Instr) and i.instr == name and tuple(i.args) == args


def _reg_operand(i: instr, name: str) -> str | None:
    """`pushq %rbx` -> 'rbx' (for name='pushq'); None if i isn't that."""
    match i:
        case Instr(n, [Reg(reg)]) if n == name:
            return reg
    return None


def check_x86_final_ch4(p: object) -> list[str]:
    """Output of prelude_and_conclusion in chapter 4 (section 4.6, figure 4.9):

        pushq %rbp; movq %rsp, %rbp; pushq <callee-saved>...; subq $A, %rsp
        ... body ...
        addq $A, %rsp; popq <callee-saved, reversed>...; popq %rbp; retq

    with %rsp 16-byte aligned in the body, every callee-saved register the
    body uses saved and restored, and every stack slot inside the frame,
    below the saved registers."""
    problems = check_x86_int(p)
    body = _main_body(p, [])
    if not body:
        return problems or ['program has no instructions']
    return problems + _check_frame(body)


def _check_frame(body: list[instr]) -> list[str]:
    """The prelude/conclusion checks of check_x86_final_ch4, on a list of
    instructions that starts with the prelude and ends with the conclusion."""
    problems: list[str] = []
    # Prelude
    if not (_is(body[0], 'pushq', Reg('rbp')) and len(body) > 1
            and _is(body[1], 'movq', Reg('rsp'), Reg('rbp'))):
        return problems + ['main should start with `pushq %rbp` then `movq %rsp, %rbp`']
    k = 2
    pushed: list[str] = []
    while k < len(body) and (reg := _reg_operand(body[k], 'pushq')) is not None:
        pushed.append(reg)
        k += 1
    sub = 0
    match body[k] if k < len(body) else None:
        case Instr('subq', [Immediate(n), Reg('rsp')]):
            sub = n
            k += 1

    # Conclusion
    j = len(body)
    if not _is(body[j - 1], 'retq'):
        return problems + [f'main should end with retq, ends with `{str(body[-1]).strip()}`']
    j -= 1
    if not (j > k and _is(body[j - 1], 'popq', Reg('rbp'))):
        return problems + ['the conclusion should end with `popq %rbp` then `retq`']
    j -= 1
    popped: list[str] = []
    while j > k and (reg := _reg_operand(body[j - 1], 'popq')) is not None:
        popped.insert(0, reg)
        j -= 1
    add = 0
    match body[j - 1] if j > k else None:
        case Instr('addq', [Immediate(n), Reg('rsp')]):
            add = n
            j -= 1
    middle = body[k:j]

    for reg in pushed:
        if reg not in CALLEE_SAVED_REGS:
            problems.append(f'the prelude pushes %{reg}, which is not callee-saved')
    if popped != pushed[::-1]:
        want = ', '.join('%' + x for x in pushed[::-1])
        got = ', '.join('%' + x for x in popped)
        problems.append(f'the conclusion should pop the saved registers in the reverse of the '
                        f'order they were pushed: expected popq {want or "(none)"}; got popq {got or "(none)"}')
    if sub != add:
        problems.append(f'the prelude subtracts {sub} from %rsp but the conclusion adds back {add}')
    c = len(pushed)
    if (8 * c + sub) % 16 != 0:
        problems.append(f'%rsp is not 16-byte aligned for calls: the prelude pushes {c} register(s) '
                        f'({8 * c} bytes) and subtracts {sub}; those must add up to a multiple of 16 '
                        f'(the book: A = align(8S + 8C) - 8C)')

    used = set()
    for i in middle:
        if isinstance(i, Instr):
            for a in i.args:
                if isinstance(a, Reg) and a.id in CALLEE_SAVED_REGS:
                    used.add(a.id)
                if isinstance(a, Deref) and a.reg == 'rbp':
                    if -a.offset <= 8 * c:
                        problems.append(f'{a} overlaps the saved callee-saved registers '
                                        f'(-8(%rbp)..{-8 * c}(%rbp)): `{str(i).strip()}`')
                    elif -a.offset > 8 * c + sub:
                        problems.append(f'{a} is outside the frame (the prelude reserves {sub} bytes '
                                        f'below the {c} saved register(s)): `{str(i).strip()}`')
    for reg in sorted(used - set(pushed)):
        problems.append(f'the program uses callee-saved %{reg} but the prelude does not save it')
    return problems


CHECKERS_CH4: dict[str, Callable[[object], list[str]]] = {
    'remove_complex_operands': check_Lvar_mon,
    'select_instructions': check_x86_var,
    'assign_homes': check_x86_homes,
    'patch_instructions': check_x86_int_ch4,
    'prelude_and_conclusion': check_x86_final_ch4,
}


# ---------------------------------------------------------------------------
# Chapter 5: Booleans and conditionals
#
#   L_If --shrink--> L_If (no and/or) --rco--> L_If^mon --explicate--> C_If
#        --select--> x86_If^Var --assign homes--> x86_If --patch--> x86_If
#        --prelude--> x86_If with main and conclusion blocks     (figure 5.15)
# ---------------------------------------------------------------------------

CMP_OPS = (ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE)
CONDITION_CODES = {'e', 'ne', 'l', 'le', 'g', 'ge'}
BYTE_REGISTERS = {'ah', 'al', 'bh', 'bl', 'ch', 'cl', 'dh', 'dl'}

# Instruction name -> number of arguments (x86_If, figure 5.10).
INSTR_ARITY_IF = {**INSTR_ARITY, 'xorq': 2, 'cmpq': 2, 'movzbq': 2,
                  **{'set' + cc: 1 for cc in CONDITION_CODES}}


def _is_bool_const(e: expr) -> bool:
    return isinstance(e, Constant) and isinstance(e.value, bool)


def _is_int_const(e: expr) -> bool:
    return isinstance(e, Constant) and isinstance(e.value, int) and not isinstance(e.value, bool)


def _is_cmp(e: expr) -> bool:
    """Compare(e, [cmp], [e]) with exactly one comparison (no `a < b < c`)."""
    return (isinstance(e, ast.Compare) and len(e.ops) == 1 and len(e.comparators) == 1
            and isinstance(e.ops[0], CMP_OPS))


def _lif_exp(e: expr, allow_boolop: bool, problems: list[str]) -> None:
    """exp in figure 5.2 (allow_boolop=False: after shrink, no and/or)."""
    match e:
        case _ if _is_int_const(e) or _is_bool_const(e) or _is_input_int(e):
            pass
        case Name(_):
            pass
        case UnaryOp(USub() | ast.Not(), v):
            _lif_exp(v, allow_boolop, problems)
        case BinOp(left, Add() | Sub(), right):
            _lif_exp(left, allow_boolop, problems)
            _lif_exp(right, allow_boolop, problems)
        case ast.BoolOp(ast.And() | ast.Or(), values) if len(values) == 2:
            if not allow_boolop:
                problems.append(f'`and`/`or` left in the program (shrink should turn them into '
                                f'if expressions, section 5.5): `{_src(e)}`')
            for x in values:
                _lif_exp(x, allow_boolop, problems)
        case ast.Compare(left, _, [right]) if _is_cmp(e):
            _lif_exp(left, allow_boolop, problems)
            _lif_exp(right, allow_boolop, problems)
        case ast.IfExp(test, body, orelse):
            for x in (test, body, orelse):
                _lif_exp(x, allow_boolop, problems)
        case _:
            problems.append(f'not an L_If expression: {_src(e)}')


def _lif_stmts(ss: list[stmt], allow_boolop: bool, problems: list[str]) -> None:
    for s in ss:
        match s:
            case Expr(Call(Name('print'), [e])):
                _lif_exp(e, allow_boolop, problems)
            case Expr(e):
                _lif_exp(e, allow_boolop, problems)
            case Assign([Name(_)], e):
                _lif_exp(e, allow_boolop, problems)
            case ast.If(test, body, orelse):
                _lif_exp(test, allow_boolop, problems)
                if not body or not orelse:
                    problems.append(f'an L_If `if` needs both branches (stmt+): `{_src(s)}`')
                _lif_stmts(body, allow_boolop, problems)
                _lif_stmts(orelse, allow_boolop, problems)
            case _:
                problems.append(f'not an L_If statement: {_src(s)}')


def check_Lif(p: Module) -> list[str]:
    """Figure 5.2. Used to validate the chapter 5 test programs."""
    problems: list[str] = []
    _lif_stmts(p.body, True, problems)
    return problems


def check_Lif_shrunk(p: object) -> list[str]:
    """Output of shrink (section 5.5): L_If without `and` and `or`."""
    if not isinstance(p, Module):
        return [f'expected a Module, got {type(p).__name__}']
    problems: list[str] = []
    _lif_stmts(p.body, False, problems)
    return problems


def _is_atomic_if(e: expr) -> bool:
    """atm ::= Constant(int) | Name(var) | Constant(bool)"""
    return isinstance(e, Name) or isinstance(e, Constant) and isinstance(e.value, int)


def _is_generated(e: expr) -> bool:
    # utils.generate_name makes names like tmp.3; source variables can't contain a dot.
    return isinstance(e, Name) and '.' in e.id


def _mon_if_exp(e: expr, problems: list[str]) -> None:
    """exp in figure 5.11. The text of section 5.6 adds that the operands of
    `not` and of comparisons must be atomic."""
    where = _src(e)
    match e:
        case _ if _is_atomic_if(e) or _is_input_int(e):
            pass
        case UnaryOp(USub() | ast.Not() as op, v):
            if not _is_atomic_if(v):
                name = '-' if isinstance(op, USub) else 'not'
                problems.append(f'operand of {name} is not atomic: `{_src(v)}` in `{where}`')
        case BinOp(left, Add() | Sub(), right):
            for side in (left, right):
                if not _is_atomic_if(side):
                    problems.append(f'operand of {"+" if isinstance(e.op, Add) else "-"} '
                                    f'is not atomic: `{_src(side)}` in `{where}`')
        case ast.Compare(left, _, [right]) if _is_cmp(e):
            for side in (left, right):
                if not _is_atomic_if(side):
                    problems.append(f'operand of a comparison is not atomic: `{_src(side)}` in `{where}`')
        case ast.IfExp(test, body, orelse):
            _mon_if_test(test, e, problems)
            for x in (test, body, orelse):
                _mon_if_exp(x, problems)
        case _ if isinstance(e, Begin):
            _mon_if_stmts(e.body, problems)
            _mon_if_exp(e.result, problems)
        case ast.BoolOp():
            problems.append(f'`and`/`or` should be gone after shrink: `{where}`')
        case _:
            problems.append(f'not an L_If^mon expression: `{where}`')


def _mon_if_test(test: expr, node: ast.AST, problems: list[str]) -> None:
    # Look through Begins: Begin([tmp.0 = x < y], tmp.0) hides the same problem.
    while isinstance(test, Begin):
        test = test.result
    if _is_generated(test):
        problems.append(f'the condition of an if was replaced by the temporary `{_src(test)}` '
                        f'(section 5.6 says not to; explicate_control needs the comparison '
                        f'itself to jump on it directly): `{_src(node).splitlines()[0]}`')


def _mon_if_stmts(ss: list[stmt], problems: list[str]) -> None:
    for s in ss:
        match s:
            case Expr(Call(Name('print'), [e])):
                if not _is_atomic_if(e):
                    problems.append(f'argument of print is not atomic: `{_src(e)}`')
            case Expr(e):
                _mon_if_exp(e, problems)
            case Assign([Name(_)], e):
                _mon_if_exp(e, problems)
            case ast.If(test, body, orelse):
                _mon_if_test(test, s, problems)
                _mon_if_exp(test, problems)
                _mon_if_stmts(body, problems)
                _mon_if_stmts(orelse, problems)
            case _:
                problems.append(f'not an L_If^mon statement: `{_src(s)}`')


def check_Lif_mon(p: object) -> list[str]:
    """Output of remove_complex_operands (figure 5.11, section 5.6)."""
    if not isinstance(p, Module):
        return [f'expected a Module, got {type(p).__name__}']
    problems: list[str] = []
    _mon_if_stmts(p.body, problems)
    return problems


def _label_problem(label: object, what: str) -> str | None:
    if not isinstance(label, str):
        return f'{what} {label!r} is not a string'
    if label.startswith('_'):
        return (f'{what} `{label}` starts with "_". Don\'t call label_name() in your passes: on '
                f'macOS it adds a "_", and X86Program printing adds another one, so the '
                f'interpreters can\'t find `start`. Use plain names; printing adds the "_".')
    return None


def _cif_exp(e: expr, where: str, problems: list[str]) -> None:
    """exp in figure 5.8, plus `not atm` (section 5.8 translates it)."""
    match e:
        case _ if _is_atomic_if(e) or _is_input_int(e):
            pass
        case UnaryOp(USub() | ast.Not(), v) if _is_atomic_if(v):
            pass
        case BinOp(left, Add() | Sub(), right) if _is_atomic_if(left) and _is_atomic_if(right):
            pass
        case ast.Compare(left, _, [right]) if _is_cmp(e) and _is_atomic_if(left) and _is_atomic_if(right):
            pass
        case _:
            problems.append(f'not a C_If expression: `{_src(e)}` in `{where}`')


def check_Cif(p: object) -> list[str]:
    """Output of explicate_control (figure 5.8): a CProgram mapping labels
    to blocks; each block is statements followed by one tail."""
    if not isinstance(p, CProgram):
        return [f'expected a CProgram, got {type(p).__name__}']
    if not isinstance(p.body, dict):
        return [f'CProgram body should be a dict (label -> statements), got {type(p.body).__name__}']
    problems: list[str] = []
    labels = set(p.body)
    for label in labels:
        if (msg := _label_problem(label, 'block label')) is not None:
            problems.append(msg)
    if 'start' not in labels:
        problems.append(f'there is no "start" block (labels: {", ".join(sorted(map(str, labels)))})')

    def goto_ok(g: stmt) -> bool:
        if not isinstance(g, Goto):
            return False
        if g.label not in labels:
            problems.append(f'goto {g.label}, but there is no block with that label')
        return True

    for label, ss in p.body.items():
        if not ss:
            problems.append(f'block {label} is empty (it needs at least a tail: return, goto, or if)')
            continue
        *stmts, tail = ss
        for s in stmts:
            where = _src(s)
            match s:
                case Expr(Call(Name('print'), [e])):
                    if not _is_atomic_if(e):
                        problems.append(f'argument of print is not atomic: `{where}`')
                case Expr(e):
                    _cif_exp(e, where, problems)
                case Assign([Name(_)], e):
                    _cif_exp(e, where, problems)
                case Return() | Goto() | ast.If():
                    problems.append(f'block {label}: `{where.splitlines()[0]}` is a tail, so it must be '
                                    'the last statement of its block')
                case _:
                    problems.append(f'not a C_If statement: `{where}`')
        match tail:
            case Return(value) if value is not None:
                _cif_exp(value, _src(tail), problems)
            case Goto():
                goto_ok(tail)
            case ast.If(test, [thn], [els]) if _is_cmp(test):
                assert isinstance(test, ast.Compare)
                if not (_is_atomic_if(test.left) and _is_atomic_if(test.comparators[0])):
                    problems.append(f'operands of the comparison must be atomic: `{_src(test)}`')
                if not (goto_ok(thn) and goto_ok(els)):
                    problems.append(f'block {label}: both branches of an if must be a single goto')
            case ast.If(test, _, _):
                problems.append(f'block {label}: the condition of an if must be a comparison, and '
                                f'each branch a single goto: `if {_src(test)}: ...`')
            case _:
                problems.append(f'block {label} must end with return, goto, or if; it ends with '
                                f'`{_src(tail)}`')
    return problems


def _count_effects(nodes: list[ast.AST]) -> tuple[int, int]:
    """Number of print(...) and input_int() calls."""
    prints = inputs = 0
    for n in nodes:
        for x in ast.walk(n):
            if isinstance(x, Call) and isinstance(x.func, Name):
                prints += x.func.id == 'print'
                inputs += x.func.id == 'input_int'
    return prints, inputs


def _begin_aware_nodes(p: Module) -> list[ast.AST]:
    """ast.walk doesn't know Begin's fields; flatten Begins into statements."""
    out: list[ast.AST] = []

    def visit(n: ast.AST) -> None:
        if isinstance(n, Begin):
            for s in n.body:
                visit(s)
            visit(n.result)
            return
        out.append(n)
        for child in ast.iter_child_nodes(n):
            visit(child)
    for s in p.body:
        visit(s)
    return [n for n in out if isinstance(n, Call)]


def check_no_duplication(before: object, after: object) -> list[str]:
    """explicate_control must never copy code (section 5.7): a continuation
    used by two branches goes in its own block, reached by goto. So the
    C_If program can't have more print or input_int calls than its input."""
    if not isinstance(before, Module) or not isinstance(after, CProgram):
        return []
    p0, i0 = _count_effects(_begin_aware_nodes(before))
    blocks: list[ast.AST] = [s for ss in after.body.values() for s in ss]
    p1, i1 = _count_effects(blocks)
    problems = []
    if p1 > p0:
        problems.append(f'the program has {p0} print call(s) but the C_If output has {p1}: '
                        'code was duplicated. Use create_block so both branches goto one copy (section 5.7)')
    if i1 > i0:
        problems.append(f'the program has {i0} input_int call(s) but the C_If output has {i1}: '
                        'code was duplicated. Use create_block so both branches goto one copy (section 5.7)')
    return problems


def _blocks(p: object, problems: list[str]) -> dict[str, list[instr]]:
    if not isinstance(p, X86Program):
        problems.append(f'expected an X86Program, got {type(p).__name__}')
        return {}
    if not isinstance(p.body, dict):
        problems.append('in chapter 5 the X86Program body is a dict of blocks (label -> instructions), '
                        'not a list (figure 5.10)')
        return {}
    return p.body


def _check_arg_if(a: arg, i: instr, allow_vars: bool, problems: list[str]) -> None:
    if isinstance(a, ByteReg):
        if a.id not in BYTE_REGISTERS:
            problems.append(f'unknown byte register %{a.id}: `{str(i).strip()}`')
    else:
        _check_arg(a, i, allow_vars, problems)


def _check_blocks(blocks: dict[str, list[instr]], allow_vars: bool, final: bool,
                  problems: list[str]) -> None:
    labels = set(blocks)
    for label in labels:
        if (msg := _label_problem(label, 'block label')) is not None:
            problems.append(msg)

    def target_ok(label: str, i: instr) -> None:
        if (msg := _label_problem(label, 'jump target')) is not None:
            problems.append(msg)
        elif label not in labels and not (label == 'conclusion' and not final):
            problems.append(f'`{str(i).strip()}` jumps to a block that does not exist')

    for label, body in blocks.items():
        if not body:
            problems.append(f'block {label} is empty')
            continue
        for i in body:
            match i:
                case Instr(name, args):
                    if name not in INSTR_ARITY_IF:
                        problems.append(f'unknown instruction "{name}": `{str(i).strip()}`')
                    elif len(args) != INSTR_ARITY_IF[name]:
                        problems.append(f'{name} takes {INSTR_ARITY_IF[name]} argument(s): `{str(i).strip()}`')
                    for a in args:
                        _check_arg_if(a, i, allow_vars, problems)
                    if name.startswith('set') and not (args and isinstance(args[0], ByteReg)):
                        problems.append(f'set{name[3:]} writes one byte, so its argument must be a '
                                        f'byte register like %al (ByteReg): `{str(i).strip()}`')
                    if name == 'movzbq' and not (args and isinstance(args[0], ByteReg)):
                        problems.append(f'movzbq moves from a byte register like %al (ByteReg): `{str(i).strip()}`')
                case Callq(func, num_args):
                    if not isinstance(func, str) or not isinstance(num_args, int):
                        problems.append(f'bad callq: {i!r}')
                case Jump(target):
                    target_ok(target, i)
                case JumpIf(cc, target):
                    if cc not in CONDITION_CODES:
                        problems.append(f'unknown condition code "{cc}" in `{str(i).strip()}`')
                    target_ok(target, i)
                case _:
                    problems.append(f'not an x86 instruction: {i!r}')
        last = body[-1]
        if not (isinstance(last, Jump) or _is(last, 'retq')):
            problems.append(f'block {label} must end with a jmp (blocks can be laid out in any '
                            f'order, so nothing can fall through); it ends with `{str(last).strip()}`')


def check_x86_if_var(p: object) -> list[str]:
    """Output of select_instructions (figure 5.10, section 5.8)."""
    problems: list[str] = []
    blocks = _blocks(p, problems)
    if problems:
        return problems
    if 'start' not in blocks:
        problems.append('there is no "start" block')
    _check_blocks(blocks, allow_vars=True, final=False, problems=problems)
    return problems


def check_x86_if_homes(p: object) -> list[str]:
    """Output of assign_homes: no variables left."""
    problems: list[str] = []
    blocks = _blocks(p, problems)
    if not problems:
        _check_blocks(blocks, allow_vars=False, final=False, problems=problems)
    return problems


def check_x86_if(p: object) -> list[str]:
    """Output of patch_instructions (sections 2.7, 4.5, 5.10)."""
    problems = check_x86_if_homes(p)
    blocks = _blocks(p, [])
    for body in blocks.values():
        _check_x86_int_rules(body, problems)
        for i in body:
            match i:
                case Instr('movq', [a, b]) if a == b:
                    problems.append(f'trivial move left in (delete it, section 4.5): `{str(i).strip()}`')
                case Instr('cmpq', [_, Immediate()]):
                    problems.append(f'the second argument of cmpq must not be an immediate '
                                    f'(section 5.10): `{str(i).strip()}`')
                case Instr('movzbq', [_, b]) if not isinstance(b, Reg) or isinstance(b, ByteReg):
                    problems.append(f'the second argument of movzbq must be a (64-bit) register '
                                    f'(section 5.10): `{str(i).strip()}`')
    return problems


def check_x86_if_final(p: object) -> list[str]:
    """Output of prelude_and_conclusion (section 5.11): a `main` block with
    the prelude ending in `jmp start`, and a `conclusion` block, with the
    same frame rules as chapter 4."""
    problems = check_x86_if(p)
    blocks = _blocks(p, [])
    if not blocks:
        return problems
    main, conclusion = blocks.get('main'), blocks.get('conclusion')
    if main is None:
        problems.append('there is no "main" block (the prelude goes there)')
    if conclusion is None:
        problems.append('there is no "conclusion" block (section 5.11)')
    if main is None or conclusion is None:
        return problems
    if not (main and _is_jump(main[-1], 'start')):
        problems.append('the main block should end with `jmp start`')
        return problems
    rest = [i for label, b in blocks.items() if label not in ('main', 'conclusion') for i in b]
    return problems + _check_frame(main[:-1] + rest + conclusion)


def _is_jump(i: instr, label: str) -> bool:
    return isinstance(i, Jump) and i.label == label


CHECKERS_CH5: dict[str, Callable[[object], list[str]]] = {
    'shrink': check_Lif_shrunk,
    'remove_complex_operands': check_Lif_mon,
    'explicate_control': check_Cif,
    'select_instructions': check_x86_if_var,
    'assign_homes': check_x86_if_homes,
    'patch_instructions': check_x86_if,
    'prelude_and_conclusion': check_x86_if_final,
}
