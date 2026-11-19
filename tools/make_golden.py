"""Create expected-output (.golden) files for test programs.

For each test program that has no .golden file, run the definitional
interpreter (the referee from book section 2.1.2) on it with its .in file as
input, and save what it prints. A missing .in file is created empty (for
programs that don't call input_int).

    tests/var  L_Var programs, run with interp_Lvar (chapters 2 and 4)
    tests/if   L_If programs, run with interp_Lif (chapter 5)

    .venv/bin/python tools/make_golden.py            # only missing .golden files
    .venv/bin/python tools/make_golden.py --force    # regenerate all of them
"""
from __future__ import annotations

import argparse
import os
import sys
from ast import Module, parse
from typing import Callable

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from interp_Lif import InterpLif  # noqa: E402
from interp_Lvar import InterpLvar  # noqa: E402
from tools.progress import read_text, run_interp  # noqa: E402
from tools.shapes import check_Lif, check_Lvar  # noqa: E402
from type_check_Lif import TypeCheckLif  # noqa: E402
from type_check_Lvar import TypeCheckLvar  # noqa: E402


class Language:
    def __init__(self, name: str, check: Callable[[Module], list[str]],
                 type_check: Callable[[Module], object],
                 interp: Callable[[Module], object]) -> None:
        self.name = name
        self.check = check
        self.type_check = type_check
        self.interp = interp


LANGUAGES = {
    'var': Language('L_Var', check_Lvar, lambda p: TypeCheckLvar().type_check(p),
                    lambda p: InterpLvar().interp(p)),
    'if': Language('L_If', check_Lif, lambda p: TypeCheckLif().type_check(p),
                   lambda p: InterpLif().interp(p)),
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--force', action='store_true', help='regenerate existing .golden files')
    args = ap.parse_args()
    sys.setrecursionlimit(10000)
    status = 0
    for d, lang in LANGUAGES.items():
        test_dir = os.path.join(ROOT, 'tests', d)
        for f in sorted(os.listdir(test_dir)):
            if not f.endswith('.py'):
                continue
            root = os.path.join(test_dir, f[:-3])
            if os.path.exists(root + '.golden') and not args.force:
                continue
            if not os.path.exists(root + '.in'):
                open(root + '.in', 'w').close()
            program = parse(read_text(root + '.py'))
            problems = lang.check(program)
            if problems:
                print(f'skipped {d}/{f}: not an {lang.name} program: {problems[0]}')
                status = 1
                continue
            lang.type_check(program)
            output = run_interp(lang.interp, program, root + '.in')
            with open(root + '.golden', 'w') as g:
                g.write(output + '\n')
            print(f'{d}/{f[:-3]}.golden: {output!r}')
    return status


if __name__ == '__main__':
    sys.exit(main())
