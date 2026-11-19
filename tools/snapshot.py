"""Behavior snapshot for the support code.

Prints a deterministic report covering: importing every module, running the
interpreter and type checker for each test directory's language on tests/
(Lvar for tests/var, Lif for tests/if and tests/if_type_errors),
pretty-printing each test AST, running the Cif interpreter and type checker
on the book's figure 5.12 program, and running the x86 interpreter on a
small hand-written program. Diff the
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

from ast import Assign, BinOp, Add, Call, Compare, Constant, Eq, Expr, If, Lt, Name, Return
from interp_Lvar import InterpLvar
from type_check_Lvar import TypeCheckLvar
from interp_Lif import InterpLif
from type_check_Lif import TypeCheckLif
from interp_Cif import InterpCif
from type_check_Cif import TypeCheckCif
from utils import CProgram, Goto
from interp_x86.eval_x86 import interp_x86
from x86_ast import X86Program, Instr, Immediate, Reg, Callq

LANGS = {"var": (InterpLvar, TypeCheckLvar), "if": (InterpLif, TypeCheckLif),
         "if_type_errors": (InterpLif, TypeCheckLif)}

for d in sorted(os.listdir("tests")):
    Interp, TypeCheck = LANGS[d]
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
            TypeCheck().type_check(tree)
            print("type_check: ok")
        except Exception as ex:
            print("type_check: FAILED", ex)
        if not os.path.exists(root + ".in"):
            continue  # type-error tests are never run
        out = io.StringIO()
        old_stdin = sys.stdin
        try:
            with open(root + ".in") as stdin, contextlib.redirect_stdout(out):
                sys.stdin = stdin
                Interp().interp(tree)
        except Exception:
            print("interp: FAILED\n" + traceback.format_exc())
        finally:
            sys.stdin = old_stdin
        golden = open(root + ".golden").read() if os.path.exists(root + ".golden") else None
        print("interp output:", repr(out.getvalue()),
              "matches golden" if golden is not None and out.getvalue().strip() == golden.strip()
              else "golden: " + repr(golden))

section("Cif: figure 5.12")
def name(x: str) -> Name:
    return Name(x)
read = Call(Name("input_int"), [])
cprog = CProgram({
    "start": [Assign([name("x")], read), Assign([name("y")], read),
              If(Compare(name("x"), [Lt()], [Constant(1)]), [Goto("block_6")], [Goto("block_7")])],
    "block_6": [If(Compare(name("x"), [Eq()], [Constant(0)]), [Goto("block_4")], [Goto("block_5")])],
    "block_7": [If(Compare(name("x"), [Eq()], [Constant(2)]), [Goto("block_4")], [Goto("block_5")])],
    "block_4": [Assign([name("tmp")], BinOp(name("y"), Add(), Constant(2))), Goto("block_3")],
    "block_5": [Assign([name("tmp")], BinOp(name("y"), Add(), Constant(10))), Goto("block_3")],
    "block_3": [Expr(Call(Name("print"), [name("tmp")])), Return(Constant(0))],
})
print(str(cprog))
TypeCheckCif().type_check(cprog)
print("var_types:", sorted((k, repr(t)) for k, t in cprog.var_types.items()))
for inputs in ("0\n5\n", "3\n5\n", "2\n5\n"):
    out = io.StringIO()
    old_stdin = sys.stdin
    try:
        sys.stdin = io.StringIO(inputs)
        with contextlib.redirect_stdout(out):
            InterpCif().interp(cprog)
    finally:
        sys.stdin = old_stdin
    print("inputs", repr(inputs), "output:", repr(out.getvalue()))

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
