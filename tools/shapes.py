"""Shape checkers: does a pass's output belong to its target language?

run-tests.py only checks that each pass preserves the program's output. That
is necessary but not enough: a pass that returns its input unchanged also
preserves the output. These checkers test the other half, that each pass
produced the language the book says it should (figure 2.10):

    L_Var --rco--> L_Var^mon --select--> x86_Var --assign homes--> x86_Var
          (no variables) --patch--> x86_Int --prelude--> x86_Int (main)

Each checker returns a list of human-readable problems. An empty list means
the program has the right shape.
"""
from __future__ import annotations

import ast
from ast import (Add, Assign, BinOp, Call, Constant, Expr, Module, Name,
                 Sub, UnaryOp, USub, expr, stmt)
from typing import Callable

from x86_ast import (Callq, Deref, Immediate, Instr, Jump, Reg, Variable,
                     X86Program, arg, instr)

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
