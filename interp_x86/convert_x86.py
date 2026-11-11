# Convert from the x86 AST classes defined in utils.py into the parse
# tree format used by the interpreter.

from ast import Constant, Name

from lark import Tree
from utils import GlobalValue, label_name
from x86_ast import *

from typing import Any


def convert_int(value: int) -> Tree:
    return Tree("int_a", [value])    
    # if value >= 0:
    #     return Tree("int_a", [value])
    # else:
    #     return Tree("neg_a", [Tree("int_a", [-value])])

def convert_arg(arg: Any) -> Tree:
    match arg:
        case Reg(id):
            return Tree('reg_a', [id])
        case Variable(id):
            return Tree('var_a', [id])
        case Immediate(value):
            return convert_int(value)
        case Deref(reg, offset):
            return Tree('mem_a', [convert_int(offset), reg])
        case ByteReg(id):
            return Tree('reg_a', [id])
        case GlobalValue(id):
            return Tree('global_val_a', [id, 'rip'])
        case _:
            raise Exception('convert_arg: unhandled ' + repr(arg))

def convert_instr(i: instr) -> Tree:
    match i:
        case Instr(name, args):
            return Tree(name, [convert_arg(arg) for arg in args])
        case Callq(func, args):
            return Tree('callq', [func])
        case Jump(label):
            return Tree('jmp', [label])
        case JumpIf(cc, label):
            return Tree('j' + cc, [label])
        case _:
            raise Exception('error in convert_instr, unhandled ' + repr(i))

def convert_program(p: X86Program) -> Tree:
    if isinstance(p.body, list):
        main_instrs = [convert_instr(instr) for instr in p.body]
        main_block = Tree('block', ['main'] + main_instrs)
        return Tree('prog', [main_block])
    elif isinstance(p.body, dict):
        blocks: list[Tree] = []
        for (l, ss) in p.body.items():
            blocks.append(Tree('block',
                               [l] + [convert_instr(instr) for instr in ss]))
        return Tree('prog', blocks)
    else:
        raise Exception('convert_program: unexpected body ' + repr(p.body))
