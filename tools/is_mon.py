"""Is this program in L_Var^mon (book figure 2.11), the output form of RCO?

    .venv/bin/python tools/is_mon.py 'print(42 + -10)'
    .venv/bin/python tools/is_mon.py 'tmp_1 = -10
    print(42 + tmp_1)'

Useful for checking your understanding: write what you think RCO should
produce, and see whether it's valid L_Var^mon.
"""
from __future__ import annotations

import os
import sys
from ast import parse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.shapes import check_Lvar_mon  # noqa: E402


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    problems = check_Lvar_mon(parse(sys.argv[1]))
    if not problems:
        print('✓ valid L_Var^mon: every operand is atomic')
        return 0
    for p in problems:
        print('✗ ' + p)
    return 1


if __name__ == '__main__':
    sys.exit(main())
