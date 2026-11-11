"""Chapter 2 progress scoreboard.

Runs every test program in tests/var through the compiler's passes, in order,
and checks two things after each pass:

  shape   the output is in the pass's target language (tools/shapes.py)
  output  running the output gives the same result as the original program
          (book diagram 1.8): pass outputs are run on an interpreter, and the
          final program is assembled with gcc and run for real

Each test stops at its first failing pass, so every failure shown is the
earliest one for that test. Unimplemented passes (NotImplementedError) show
as "not started".

    .venv/bin/python tools/progress.py            # scoreboard + first failures
    .venv/bin/python tools/progress.py -v         # every failure
    .venv/bin/python tools/progress.py -k input   # only tests with "input" in the name
"""
from __future__ import annotations

import argparse
import contextlib
import io
import os
import subprocess
import sys
import traceback
from ast import Module, parse
from dataclasses import dataclass
from typing import Any, Callable, Literal

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

import compiler  # noqa: E402
from interp_Lvar import InterpLvar  # noqa: E402
from interp_x86.eval_x86 import interp_x86  # noqa: E402
from type_check_Lvar import TypeCheckLvar  # noqa: E402
from tools.shapes import CHECKERS, check_Lvar  # noqa: E402

TEST_DIR = os.path.join(ROOT, 'tests', 'var')
BUILD_DIR = os.path.join(ROOT, 'build')

Status = Literal['ok', 'shape', 'output', 'crash', 'todo', 'blocked']

PASSES: list[str] = [
    'remove_complex_operands',
    'select_instructions',
    'assign_homes',
    'patch_instructions',
    'prelude_and_conclusion',
]
SECTION = {
    'remove_complex_operands': '2.4',
    'select_instructions': '2.5',
    'assign_homes': '2.6',
    'patch_instructions': '2.7',
    'prelude_and_conclusion': '2.8',
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


def run_test(path: str) -> TestResult:
    name = os.path.splitext(os.path.basename(path))[0]
    root = os.path.splitext(path)[0]
    passes = {p: PassResult('blocked') for p in PASSES}

    # Check the test itself first.
    if not os.path.exists(root + '.in'):
        return TestResult(name, f'missing {name}.in (create it, even if empty)', passes)
    if not os.path.exists(root + '.golden'):
        return TestResult(name, f'missing {name}.golden (run tools/make_golden.py)', passes)
    try:
        program: Any = parse(read_text(path))
    except SyntaxError as ex:
        return TestResult(name, f'syntax error: {ex}', passes)
    problems = check_Lvar(program)
    if problems:
        return TestResult(name, 'not an L_Var program: ' + problems[0], passes)
    try:
        TypeCheckLvar().type_check(program)
    except Exception as ex:
        return TestResult(name, f'type error: {ex}', passes)
    golden = read_text(root + '.golden')

    c = compiler.Compiler()
    for p in PASSES:
        try:
            program = getattr(c, p)(program)
        except NotImplementedError:
            passes[p] = PassResult('todo')
            break
        except Exception:
            passes[p] = PassResult('crash', traceback.format_exc(limit=-3).strip())
            break

        problems = CHECKERS[p](program)
        if problems:
            passes[p] = PassResult('shape', '\n'.join(problems[:5]))
            break

        try:
            if p == 'prelude_and_conclusion':
                actual = run_executable(program, name, root + '.in')
            elif p == 'remove_complex_operands':
                actual = run_interp(InterpLvar().interp, program, root + '.in')
            else:
                actual = run_interp(interp_x86, program, root + '.in')
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


def report(results: list[TestResult], verbose: bool) -> int:
    good = [r for r in results if not r.error]
    bad = [r for r in results if r.error]
    print(f'\nChapter 2 progress: {len(good)} tests in tests/var\n')
    print(f'  {"pass":<26}{"book":<7}{"passing":<10}status')
    print(f'  {"-" * 26}{"-" * 7}{"-" * 10}{"-" * 20}')
    failures = 0
    for p in PASSES:
        statuses = [r.passes[p].status for r in good]
        ok = statuses.count('ok')
        failing = sum(s in ('shape', 'output', 'crash') for s in statuses)
        failures += failing
        if statuses and all(s == 'todo' for s in statuses):
            status = 'not started'
        elif statuses and all(s == 'blocked' for s in statuses):
            status = 'waiting on earlier passes'
        elif ok == len(good):
            status = 'done ✓'
        elif failing:
            status = f'{failing} failing ✗'
        else:
            status = 'in progress'
        print(f'  {p:<26}§{SECTION[p]:<6}{f"{ok}/{len(good)}":<10}{status}')

    all_done = good and all(r.passes['prelude_and_conclusion'].status == 'ok' for r in good)
    if all_done:
        print('\n  All tests compile to x86 and print the right output. Chapter 2 done!')

    if bad:
        print('\nProblems with the tests themselves:')
        for r in bad:
            print(f'  {r.name}: {r.error}')

    shown = 0
    for p in PASSES:
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
    args = ap.parse_args()
    sys.setrecursionlimit(10000)
    tests = sorted(os.path.join(TEST_DIR, f) for f in os.listdir(TEST_DIR)
                   if f.endswith('.py') and args.k in f)
    return report([run_test(t) for t in tests], args.verbose)


if __name__ == '__main__':
    sys.exit(main())
