"""Progress scoreboard for chapters 2, 4 and 5.

Runs every test program (tests/var, or tests/if for chapter 5) through the
compiler's passes, in order, and checks two things after each pass:

  shape   the output is in the pass's target language (tools/shapes.py)
  output  running the output gives the same result as the original program
          (book diagram 1.8): pass outputs are run on an interpreter, and the
          final program is assembled with gcc and run for real

Each test stops at its first failing pass, so every failure shown is the
earliest one for that test. Unimplemented passes (NotImplementedError) show
as "not started".

Chapter 4 (register allocation, compiler_register_allocator.py) adds:
  - the book's worked examples for uncover_live, build_interference,
    color_graph and allocate_registers, checked against the book's answers
  - allocation checks after assign_homes (tools/regalloc_checks.py)
  - stricter shape checks for patch_instructions and prelude_and_conclusion
  - "register poisoning": after every callq, the interpreter overwrites the
    caller-saved registers with junk, as a real call may

Chapter 5 (Booleans and conditionals, compiler_conditionals.py) runs the
tests in tests/if through the passes of figure 5.15, with the book's type
checkers on the L_If and C_If outputs (like run-tests.py), the chapter 4
allocation checks, a check that explicate_control doesn't duplicate code,
book examples for liveness and interference across blocks, and the
programs in tests/if_type_errors, which the type checker must reject.

    .venv/bin/python tools/progress.py              # chapter 2 scoreboard
    .venv/bin/python tools/progress.py --chapter 4  # chapter 4 scoreboard
    .venv/bin/python tools/progress.py --chapter 5  # chapter 5 scoreboard
    .venv/bin/python tools/progress.py -v           # every failure
    .venv/bin/python tools/progress.py -k input     # only tests with "input" in the name
"""
from __future__ import annotations

import argparse
import contextlib
import importlib
import io
import os
import subprocess
import sys
import traceback
from ast import Module, parse
from dataclasses import dataclass
from typing import Any, Callable, Literal, Sequence

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

from interp_Cif import InterpCif  # noqa: E402
from interp_Lif import InterpLif  # noqa: E402
from interp_Lvar import InterpLvar  # noqa: E402
from interp_x86.eval_x86 import interp_x86  # noqa: E402
from type_check_Cif import TypeCheckCif  # noqa: E402
from type_check_Lif import TypeCheckLif  # noqa: E402
from type_check_Lvar import TypeCheckLvar  # noqa: E402
from tools import regalloc_checks  # noqa: E402
from tools.regalloc_checks import ExampleResult  # noqa: E402
from tools.shapes import (CHECKERS, CHECKERS_CH4, CHECKERS_CH5, check_Lif,  # noqa: E402
                          check_Lvar, check_no_duplication)

TEST_DIR = os.path.join(ROOT, 'tests', 'var')
BUILD_DIR = os.path.join(ROOT, 'build')

Status = Literal['ok', 'shape', 'output', 'crash', 'todo', 'blocked']

Interp = Callable[[Any], None]


def type_check_Lvar(p: Any) -> None:
    TypeCheckLvar().type_check(p)


def type_check_Lif(p: Any) -> None:
    TypeCheckLif().type_check(p)


def type_check_Cif(p: Any) -> None:
    TypeCheckCif().type_check(p)


def interp_Lvar(p: Any) -> None:
    InterpLvar().interp(p)


def interp_Lif(p: Any) -> None:
    InterpLif().interp(p)


def interp_Cif(p: Any) -> None:
    InterpCif().interp(p)


def interp_x86_poisoned(p: Any) -> None:
    interp_x86(regalloc_checks.poison_calls(p))


@dataclass
class Chapter:
    number: int
    module: str                                         # where the Compiler class lives
    section: dict[str, str]                             # pass -> book section, in pipeline order
    checkers: dict[str, Callable[[object], list[str]]]  # pass -> shape checker
    regalloc: bool                                      # chapter 4 extras
    tests: str = 'var'                                  # directory under tests/
    language: str = 'L_Var'
    source_check: Callable[[Module], list[str]] = check_Lvar
    type_check: Callable[[Any], None] = type_check_Lvar
    interps: dict[str, Interp] | None = None            # pass -> interpreter for its output
    type_checks: dict[str, Callable[[Any], None]] | None = None  # pass -> type checker for its output

    @property
    def passes(self) -> list[str]:
        return list(self.section)

    def interp_for(self, p: str) -> Interp:
        if self.interps and p in self.interps:
            return self.interps[p]
        if p == 'remove_complex_operands':
            return interp_Lvar
        if self.regalloc:
            return interp_x86_poisoned
        return interp_x86


CHAPTERS = {
    2: Chapter(2, 'compiler', {
        'remove_complex_operands': '2.4',
        'select_instructions': '2.5',
        'assign_homes': '2.6',
        'patch_instructions': '2.7',
        'prelude_and_conclusion': '2.8',
    }, CHECKERS, regalloc=False),
    4: Chapter(4, 'compiler_register_allocator', {
        'remove_complex_operands': '2.4',
        'select_instructions': '2.5',
        'assign_homes': '4.4',
        'patch_instructions': '4.5',
        'prelude_and_conclusion': '4.6',
    }, CHECKERS_CH4, regalloc=True),
    5: Chapter(5, 'compiler_conditionals', {
        'shrink': '5.5',
        'remove_complex_operands': '5.6',
        'explicate_control': '5.7',
        'select_instructions': '5.8',
        'assign_homes': '5.9',
        'patch_instructions': '5.10',
        'prelude_and_conclusion': '5.11',
    }, CHECKERS_CH5, regalloc=True, tests='if', language='L_If',
        source_check=check_Lif, type_check=type_check_Lif,
        interps={'shrink': interp_Lif, 'remove_complex_operands': interp_Lif,
                 'explicate_control': interp_Cif},
        type_checks={'shrink': type_check_Lif, 'remove_complex_operands': type_check_Lif,
                     'explicate_control': type_check_Cif}),
}


@dataclass
class PassResult:
    status: Status
    detail: str = ''


@dataclass
class TestResult:
    name: str
    error: str  # problem with the test itself (empty if the test is fine)
    passes: dict[str, PassResult]


def read_text(path: str) -> str:
    with open(path) as f:
        return f.read()


def run_interp(interp: Callable[[Any], object], program: Any, input_path: str) -> str:
    """Run an interpreter with stdin from input_path; return what it prints."""
    out = io.StringIO()
    old_stdin = sys.stdin
    try:
        with open(input_path) as stdin, contextlib.redirect_stdout(out):
            sys.stdin = stdin
            interp(program)
    finally:
        sys.stdin = old_stdin
    return out.getvalue()


def runtime_object() -> str:
    """Compile runtime.c to build/runtime.o if needed (x86-64, as the book says)."""
    os.makedirs(BUILD_DIR, exist_ok=True)
    obj = os.path.join(BUILD_DIR, 'runtime.o')
    src = os.path.join(ROOT, 'runtime.c')
    if not os.path.exists(obj) or os.path.getmtime(obj) < os.path.getmtime(src):
        subprocess.run(['gcc', '-c', '-g', '-std=c99', *arch_flags(), src, '-o', obj],
                       check=True, capture_output=True)
    return obj


def arch_flags() -> list[str]:
    # On Apple Silicon, build x86-64 binaries; macOS runs them through Rosetta.
    return ['-arch', 'x86_64'] if sys.platform == 'darwin' else []


def run_executable(program: object, name: str, input_path: str) -> str:
    """Assemble and link the final program, run it, and return its output."""
    os.makedirs(BUILD_DIR, exist_ok=True)
    asm = os.path.join(BUILD_DIR, name + '.s')
    exe = os.path.join(BUILD_DIR, name)
    with open(asm, 'w') as f:
        f.write(str(program))
    link = subprocess.run(['gcc', *arch_flags(), runtime_object(), asm, '-o', exe],
                          capture_output=True, text=True)
    if link.returncode != 0:
        raise RuntimeError('assembler/linker rejected the program:\n' + link.stderr.strip())
    with open(input_path) as stdin:
        run = subprocess.run([exe], stdin=stdin, capture_output=True, text=True, timeout=10)
    if run.returncode < 0:
        raise RuntimeError(f'program crashed (signal {-run.returncode})')
    return run.stdout


def same_output(actual: str, golden: str) -> bool:
    # Like `diff -b`, which run-tests.py uses: ignore trailing whitespace.
    return actual.strip() == golden.strip()


def run_test(path: str, ch: Chapter, make_compiler: Callable[[], Any]) -> TestResult:
    name = os.path.splitext(os.path.basename(path))[0]
    root = os.path.splitext(path)[0]
    passes = {p: PassResult('blocked') for p in ch.passes}

    # Check the test itself first.
    if not os.path.exists(root + '.in'):
        return TestResult(name, f'missing {name}.in (create it, even if empty)', passes)
    if not os.path.exists(root + '.golden'):
        return TestResult(name, f'missing {name}.golden (run tools/make_golden.py)', passes)
    try:
        program: Any = parse(read_text(path))
    except SyntaxError as ex:
        return TestResult(name, f'syntax error: {ex}', passes)
    problems = ch.source_check(program)
    if problems:
        return TestResult(name, f'not an {ch.language} program: ' + problems[0], passes)
    try:
        ch.type_check(program)
    except Exception as ex:
        return TestResult(name, f'type error: {ex}', passes)
    golden = read_text(root + '.golden')

    c = make_compiler()
    for p in ch.passes:
        before = program
        try:
            program = getattr(c, p)(program)
        except NotImplementedError:
            passes[p] = PassResult('todo')
            break
        except Exception:
            passes[p] = PassResult('crash', traceback.format_exc(limit=-3).strip())
            break

        problems = ch.checkers[p](program)
        if not problems and ch.regalloc and p == 'assign_homes':
            problems = regalloc_checks.check_allocation(c, before, program)
        if not problems and p == 'explicate_control':
            problems = check_no_duplication(before, program)
        if not problems and ch.type_checks and p in ch.type_checks:
            try:
                ch.type_checks[p](program)
            except Exception as ex:
                problems = [f'the output does not type check: {ex}']
        if problems:
            passes[p] = PassResult('shape', '\n'.join(problems[:5]))
            break

        try:
            if p == 'prelude_and_conclusion':
                actual = run_executable(program, name, root + '.in')
            else:
                actual = run_interp(ch.interp_for(p), program, root + '.in')
        except Exception as ex:
            passes[p] = PassResult('crash', f'running the output failed: {ex}')
            break
        if not same_output(actual, golden):
            passes[p] = PassResult('output', f'expected {golden.strip()!r}, got {actual.strip()!r}')
            break
        passes[p] = PassResult('ok')
    return TestResult(name, '', passes)


LABEL: dict[Status, str] = {
    'shape': 'wrong shape', 'output': 'wrong output', 'crash': 'crashed',
}


def status_word(statuses: Sequence[str], ok: int, failing: int) -> str:
    if statuses and all(s == 'todo' for s in statuses):
        return 'not started'
    if statuses and all(s == 'blocked' for s in statuses):
        return 'waiting on earlier passes'
    if ok == len(statuses):
        return 'done ✓'
    if failing:
        return f'{failing} failing ✗'
    return 'in progress'


def report_examples(examples: dict[str, list[ExampleResult]], sections: dict[str, str],
                    title: str, verbose: bool) -> int:
    """The book-example table. Returns the number of failures."""
    print(f'\nBook examples ({title})\n')
    print(f'  {"step":<26}{"book":<7}{"passing":<10}status')
    print(f'  {"-" * 26}{"-" * 7}{"-" * 10}{"-" * 20}')
    failures = 0
    for step, results in examples.items():
        statuses = [r.status for r in results]
        ok = statuses.count('ok')
        failing = sum(s in ('wrong', 'crash') for s in statuses)
        failures += failing
        print(f'  {step:<26}§{sections[step]:<6}'
              f'{f"{ok}/{len(results)}":<10}{status_word(statuses, ok, failing)}')
    for step, results in examples.items():
        broken = [r for r in results if r.status in ('wrong', 'crash')]
        if not broken:
            continue
        print(f'\n{step}: {len(broken)} failing')
        for r in broken if verbose else broken[:2]:
            print(f'  ✗ {r.example} ({"crashed" if r.status == "crash" else "wrong answer"})')
            for line in r.detail.splitlines():
                print('      ' + line)
        if not verbose and len(broken) > 2:
            print(f'  ... and {len(broken) - 2} more (use -v to see all)')
    return failures


def report(results: list[TestResult], ch: Chapter, verbose: bool) -> int:
    good = [r for r in results if not r.error]
    bad = [r for r in results if r.error]
    print(f'\nChapter {ch.number} progress: {len(good)} tests in tests/{ch.tests}\n')
    print(f'  {"pass":<26}{"book":<7}{"passing":<10}status')
    print(f'  {"-" * 26}{"-" * 7}{"-" * 10}{"-" * 20}')
    failures = 0
    for p in ch.passes:
        statuses = [r.passes[p].status for r in good]
        ok = statuses.count('ok')
        failing = sum(s in ('shape', 'output', 'crash') for s in statuses)
        failures += failing
        status = status_word(statuses, ok, failing)
        print(f'  {p:<26}§{ch.section[p]:<6}{f"{ok}/{len(good)}":<10}{status}')

    all_done = good and all(r.passes['prelude_and_conclusion'].status == 'ok' for r in good)
    if all_done:
        print(f'\n  All tests compile to x86 and print the right output. Chapter {ch.number} done!')

    if bad:
        print('\nProblems with the tests themselves:')
        for r in bad:
            print(f'  {r.name}: {r.error}')

    shown = 0
    for p in ch.passes:
        broken = [r for r in good if r.passes[p].status in ('shape', 'output', 'crash')]
        if not broken:
            continue
        print(f'\n{p}: {len(broken)} failing')
        for r in broken if verbose else broken[:3]:
            res = r.passes[p]
            print(f'  ✗ {r.name} ({LABEL[res.status]})')
            for line in res.detail.splitlines():
                print('      ' + line)
            shown += 1
        if not verbose and len(broken) > 3:
            print(f'  ... and {len(broken) - 3} more (use -v to see all)')
    print()
    return 1 if failures or bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('-v', '--verbose', action='store_true', help='show every failure')
    ap.add_argument('-k', metavar='TEXT', default='', help='only tests whose name contains TEXT')
    ap.add_argument('-c', '--chapter', type=int, choices=sorted(CHAPTERS), default=2,
                    help='which chapter\'s compiler to check (default 2)')
    ap.add_argument('--module', help='module with the Compiler class (default: compiler '
                    'for chapter 2, compiler_register_allocator for 4, compiler_conditionals for 5)')
    args = ap.parse_args()
    sys.setrecursionlimit(10000)
    ch = CHAPTERS[args.chapter]
    module = importlib.import_module(args.module or ch.module)
    make_compiler: Callable[[], Any] = module.Compiler
    test_dir = os.path.join(ROOT, 'tests', ch.tests)
    tests = sorted(os.path.join(test_dir, f) for f in os.listdir(test_dir)
                   if f.endswith('.py') and args.k in f)
    example_failures = 0
    if ch.number == 4:
        example_failures = report_examples(regalloc_checks.run_examples(make_compiler()),
                                           regalloc_checks.EXAMPLE_SECTION,
                                           'worked examples from sections 4.2-4.4', args.verbose)
    elif ch.number == 5:
        example_failures = report_examples(regalloc_checks.run_examples_ch5(make_compiler()),
                                           regalloc_checks.EXAMPLE_SECTION_CH5,
                                           'figures 5.12 and 5.14, and two more, as x86 blocks',
                                           args.verbose)
        example_failures += report_type_errors(ch)
    status = report([run_test(t, ch, make_compiler) for t in tests], ch, args.verbose)
    return 1 if status or example_failures else 0


def report_type_errors(ch: Chapter) -> int:
    """Exercise 5.1: programs in tests/<dir>_type_errors must be rejected by
    the type checker. Returns the number that were wrongly accepted."""
    d = os.path.join(ROOT, 'tests', ch.tests + '_type_errors')
    if not os.path.isdir(d):
        return 0
    accepted = []
    files = sorted(f for f in os.listdir(d) if f.endswith('.py'))
    for f in files:
        try:
            ch.type_check(parse(read_text(os.path.join(d, f))))
            accepted.append(f[:-3])
        except Exception:
            pass
    print(f'\nType checker (exercise 5.1): rejects {len(files) - len(accepted)}/{len(files)} '
          f'ill-typed programs in tests/{ch.tests}_type_errors')
    for name in accepted:
        print(f'  ✗ {name} was accepted, but it has a type error')
    return len(accepted)


if __name__ == '__main__':
    sys.exit(main())
