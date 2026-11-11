"""Create expected-output (.golden) files for test programs.

For each tests/var/*.py that has no .golden file, run the definitional
interpreter (interp_Lvar, the referee from book section 2.1.2) on it with its
.in file as input, and save what it prints. A missing .in file is created
empty (for programs that don't call input_int).

    .venv/bin/python tools/make_golden.py            # only missing .golden files
    .venv/bin/python tools/make_golden.py --force    # regenerate all of them
"""
from __future__ import annotations

import argparse
import os
import sys
from ast import parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from interp_Lvar import InterpLvar  # noqa: E402
from tools.progress import TEST_DIR, read_text, run_interp  # noqa: E402
from tools.shapes import check_Lvar  # noqa: E402
from type_check_Lvar import TypeCheckLvar  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--force', action='store_true', help='regenerate existing .golden files')
    args = ap.parse_args()
    status = 0
    for f in sorted(os.listdir(TEST_DIR)):
        if not f.endswith('.py'):
            continue
        root = os.path.join(TEST_DIR, f[:-3])
        if os.path.exists(root + '.golden') and not args.force:
            continue
        if not os.path.exists(root + '.in'):
            open(root + '.in', 'w').close()
        program = parse(read_text(root + '.py'))
        problems = check_Lvar(program)
        if problems:
            print(f'skipped {f}: not an L_Var program: {problems[0]}')
            status = 1
            continue
        TypeCheckLvar().type_check(program)
        output = run_interp(InterpLvar().interp, program, root + '.in')
        with open(root + '.golden', 'w') as g:
            g.write(output + '\n')
        print(f'{f[:-3]}.golden: {output!r}')
    return status


if __name__ == '__main__':
    sys.exit(main())
