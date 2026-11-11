"""Behavior snapshot for the support code.

Prints a deterministic report covering: importing every module, running the
Lvar interpreter and type checker on tests/, pretty-printing each test AST,
and running the x86 interpreter on a small hand-written program. Diff the
output before and after a refactor to confirm nothing changed at runtime.

    .venv/bin/python tools/snapshot.py > /tmp/before.txt
"""
import contextlib
import importlib
import io
import os
import sys
import traceback
from ast import parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
sys.setrecursionlimit(10000)


def section(title: str) -> None:
    print(f"\n=== {title}")


def modules() -> list[str]:
    names = [f[:-3] for f in os.listdir(ROOT)
             if f.endswith(".py") and f not in ("run-tests.py", "simple-test.py")]
    names += ["interp_x86." + f[:-3] for f in os.listdir("interp_x86")
              if f.endswith(".py") and f != "x86exp.py"]
    return sorted(names)


section("imports")
for m in modules():
    try:
        importlib.import_module(m)
        print(m, "ok")
    except Exception as ex:
        print(m, "FAILED", type(ex).__name__, ex)

from interp_Lvar import InterpLvar
from type_check_Lvar import TypeCheckLvar
from interp_x86.eval_x86 import interp_x86
from x86_ast import X86Program, Instr, Immediate, Reg, Callq

for d in sorted(os.listdir("tests")):
    for f in sorted(os.listdir(os.path.join("tests", d))):
        if not f.endswith(".py"):
            continue
        path = os.path.join("tests", d, f)
        root = path[:-3]
        section(path)
        with open(path) as src:
            tree = parse(src.read())
        print("str:", str(tree))
        print("repr:", repr(tree))
        try:
            TypeCheckLvar().type_check(tree)
            print("type_check: ok")
        except Exception as ex:
            print("type_check: FAILED", ex)
        out = io.StringIO()
        old_stdin = sys.stdin
        try:
            with open(root + ".in") as stdin, contextlib.redirect_stdout(out):
                sys.stdin = stdin
                InterpLvar().interp(tree)
        except Exception:
            print("interp: FAILED\n" + traceback.format_exc())
        finally:
            sys.stdin = old_stdin
        golden = open(root + ".golden").read() if os.path.exists(root + ".golden") else None
        print("interp output:", repr(out.getvalue()),
              "matches golden" if golden is not None and out.getvalue().strip() == golden.strip()
              else "golden: " + repr(golden))

section("x86 interpreter")
prog = X86Program([
    Instr("movq", [Immediate(40), Reg("rax")]),
    Instr("addq", [Immediate(2), Reg("rax")]),
    Instr("movq", [Reg("rax"), Reg("rdi")]),
    Callq("print_int", 1),
    Instr("movq", [Immediate(0), Reg("rax")]),
])
print(str(prog))
out = io.StringIO()
with contextlib.redirect_stdout(out):
    interp_x86(prog)
print("output:", repr(out.getvalue()))
