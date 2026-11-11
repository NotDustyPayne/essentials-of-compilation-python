import os
import sys
from sys import platform
import ast
from ast import *
from dataclasses import dataclass
import typing
from typing import Any, Callable, Iterable, Mapping

# `from ast import *` also defines ast.TypeVar, so use the qualified name.
A = typing.TypeVar('A')
B = typing.TypeVar('B')

# move these to the compilers, use a method with overrides -Jeremy
builtin_functions = \
    {'input_int', 'print',
     'arity',
     'len',
     'array_len', 'array_load', 'array_store',
     'any_load', 'any_load_unsafe', 'any_store', 'any_store_unsafe',
     'any_len', 'make_any',
     'exit',
     'is_tuple_proxy', 'project_tuple', 'proxy_tuple_load', 'proxy_tuple_len',
     'is_array_proxy', 'project_array', 'proxy_array_load', 'proxy_array_len',
     'proxy_array_store',
     }

tag_is_array_right_shift = 62
tag_is_proxy_right_shift = 63

################################################################################
# repr for classes in the ast module
################################################################################

indent_amount = 2


def indent_stmt() -> str:
    return " " * indent_amount


def indent() -> None:
    global indent_amount
    indent_amount += 2


def dedent() -> None:
    global indent_amount
    indent_amount -= 2


def str_stmts(stmts: Iterable[object]) -> str:
    """Render statements with one separator, even for legacy trailing-newline printers."""
    return '\n'.join(str(s).rstrip('\n') for s in stmts)


def str_Module(self: ast.Module) -> str:
    body = '\n'.join([str(s) for s in self.body])
    return body


setattr(Module, '__str__', str_Module)


def repr_Module(self: ast.Module) -> str:
    return 'Module(' + repr(self.body) + ')'


setattr(Module, '__repr__', repr_Module)


def str_Expr(self: ast.Expr) -> str:
    return indent_stmt() + str(self.value)


setattr(Expr, '__str__', str_Expr)


def repr_Expr(self: ast.Expr) -> str:
    return indent_stmt() + 'Expr(' + repr(self.value) + ')'


setattr(Expr, '__repr__', repr_Expr)


def str_Pass(self: ast.Pass) -> str:
    return indent_stmt() + 'pass'


setattr(Pass, '__str__', str_Pass)


def repr_Pass(self: ast.Pass) -> str:
    return indent_stmt() + 'Pass()'


setattr(Pass, '__repr__', repr_Pass)


def str_Assign(self: ast.Assign) -> str:
    return indent_stmt() + str(self.targets[0]) + ' = ' + str(self.value)


setattr(Assign, '__str__', str_Assign)


def repr_Assign(self: ast.Assign) -> str:
    return indent_stmt() + 'Assign(' + repr(self.targets) + ', ' + repr(self.value) + ')'


setattr(Assign, '__repr__', repr_Assign)


def str_AnnAssign(self: ast.AnnAssign) -> str:
    return indent_stmt() + str(self.target) + ' : ' + str(self.annotation) + ' = ' + str(self.value)


setattr(AnnAssign, '__str__', str_AnnAssign)


def repr_AnnAssign(self: ast.AnnAssign) -> str:
    return indent_stmt() + 'AnnAssign(' + repr(self.target) + ', ' \
           + repr(self.annotation) + ', ' + repr(self.value) + repr(self.simple) + ')'


setattr(AnnAssign, '__repr__', repr_AnnAssign)


def str_Return(self: ast.Return) -> str:
    return indent_stmt() + 'return ' + str(self.value)


setattr(Return, '__str__', str_Return)


def repr_Return(self: ast.Return) -> str:
    return indent_stmt() + 'Return(' + repr(self.value) + ')'


setattr(Return, '__repr__', repr_Return)


def str_Name(self: ast.Name) -> str:
    if hasattr(self, 'has_type'):
        return self.id + ':' + str(self.has_type)
    else:
        return self.id


setattr(Name, '__str__', str_Name)


def repr_Name(self: ast.Name) -> str:
    return 'Name(' + repr(self.id) + ')'


setattr(Name, '__repr__', repr_Name)


def str_Constant(self: ast.Constant) -> str:
    return str(self.value)


setattr(Constant, '__str__', str_Constant)


def repr_Constant(self: ast.Constant) -> str:
    return 'Constant(' + repr(self.value) + ')'


setattr(Constant, '__repr__', repr_Constant)


def str_Add(self: ast.Add) -> str:
    return '+'


setattr(Add, '__str__', str_Add)


def repr_Add(self: ast.Add) -> str:
    return 'Add()'


setattr(Add, '__repr__', repr_Add)


def str_Sub(self: ast.Sub) -> str:
    return '-'


setattr(Sub, '__str__', str_Sub)


def repr_Sub(self: ast.Sub) -> str:
    return 'Sub()'


setattr(Sub, '__repr__', repr_Sub)


def str_Mult(self: ast.Mult) -> str:
    return '*'


setattr(Mult, '__str__', str_Mult)


def repr_Mult(self: ast.Mult) -> str:
    return 'Mult()'


setattr(Mult, '__repr__', repr_Mult)


def str_And(self: ast.And) -> str:
    return 'and'


setattr(And, '__str__', str_And)


def repr_And(self: ast.And) -> str:
    return 'And()'


setattr(And, '__repr__', repr_And)


def str_Or(self: ast.Or) -> str:
    return 'or'


setattr(Or, '__str__', str_Or)


def repr_Or(self: ast.Or) -> str:
    return 'Or()'


setattr(Or, '__repr__', repr_Or)


def str_BinOp(self: ast.BinOp) -> str:
    return '(' + str(self.left) + ' ' + str(self.op) + ' ' + str(self.right) + ')'


setattr(BinOp, '__str__', str_BinOp)


def repr_BinOp(self: ast.BinOp) -> str:
    return 'BinOp(' + repr(self.left) + ', ' + repr(self.op) + ', ' + repr(self.right) + ')'


setattr(BinOp, '__repr__', repr_BinOp)


def str_BoolOp(self: ast.BoolOp) -> str:
    return '(' + str(self.values[0]) + ' ' + str(self.op) + ' ' + str(self.values[1]) + ')'


setattr(BoolOp, '__str__', str_BoolOp)


def repr_BoolOp(self: ast.BoolOp) -> str:
    return repr(self.values[0]) + ' ' + repr(self.op) + ' ' + repr(self.values[1])


setattr(BoolOp, '__repr__', repr_BoolOp)


def str_USub(self: ast.USub) -> str:
    return '-'


setattr(USub, '__str__', str_USub)


def repr_USub(self: ast.USub) -> str:
    return 'USub()'


setattr(USub, '__repr__', repr_USub)


def str_Not(self: ast.Not) -> str:
    return 'not'


setattr(Not, '__str__', str_Not)


def repr_Not(self: ast.Not) -> str:
    return 'Not()'


setattr(Not, '__repr__', repr_Not)


def str_UnaryOp(self: ast.UnaryOp) -> str:
    return str(self.op) + '(' + str(self.operand) + ')'


setattr(UnaryOp, '__str__', str_UnaryOp)


def repr_UnaryOp(self: ast.UnaryOp) -> str:
    return 'UnaryOp(' + repr(self.op) + ', ' + repr(self.operand) + ')'


setattr(UnaryOp, '__repr__', repr_UnaryOp)


def str_Call(self: ast.Call) -> str:
    return str(self.func) \
           + '(' + ', '.join([str(arg) for arg in self.args]) + ')'


setattr(Call, '__str__', str_Call)


def repr_Call(self: ast.Call) -> str:
    return 'Call(' + repr(self.func) + ', ' + repr(self.args) + ')'


setattr(Call, '__repr__', repr_Call)


def str_If(self: ast.If) -> str:
    header = indent_stmt() + 'if ' + str(self.test) + ':\n'
    indent()
    thn = str_stmts(self.body)
    els = str_stmts(self.orelse)
    dedent()
    return header + thn + '\n' + indent_stmt() + 'else:\n' + els


setattr(If, '__str__', str_If)


def repr_If(self: ast.If) -> str:
    return 'If(' + repr(self.test) + ', ' + repr(self.body) + ', ' + repr(self.orelse) + ')'


setattr(If, '__repr__', repr_If)


def str_IfExp(self: ast.IfExp) -> str:
    return '(' + str(self.body) + ' if ' + str(self.test) + \
           ' else ' + str(self.orelse) + ')'


setattr(IfExp, '__str__', str_IfExp)


def repr_IfExp(self: ast.IfExp) -> str:
    return 'IfExp(' + repr(self.test) + ', ' + repr(self.body) + \
        ', ' + repr(self.orelse) + ')'


setattr(IfExp, '__repr__', repr_IfExp)


def str_While(self: ast.While) -> str:
    header = indent_stmt() + 'while ' + str(self.test) + ':\n'
    indent()
    body = str_stmts(self.body)
    dedent()
    return header + body


setattr(While, '__str__', str_While)


def repr_While(self: ast.While) -> str:
    return 'While(' + repr(self.test) + ', ' + repr(self.body) + ', ' + repr(self.orelse) + ')'


setattr(While, '__repr__', repr_While)


def str_Compare(self: ast.Compare) -> str:
    return str(self.left) + ' ' + str(self.ops[0]) + ' ' + str(self.comparators[0])


setattr(Compare, '__str__', str_Compare)


def repr_Compare(self: ast.Compare) -> str:
    return 'Compare(' + repr(self.left) + ', ' + repr(self.ops) + ', ' \
           + repr(self.comparators) + ')'


setattr(Compare, '__repr__', repr_Compare)


def str_Eq(self: ast.Eq) -> str:
    return '=='


setattr(Eq, '__str__', str_Eq)


def repr_Eq(self: ast.Eq) -> str:
    return 'Eq()'


setattr(Eq, '__repr__', repr_Eq)


def str_NotEq(self: ast.NotEq) -> str:
    return '!='


setattr(NotEq, '__str__', str_NotEq)


def repr_NotEq(self: ast.NotEq) -> str:
    return 'NotEq()'


setattr(NotEq, '__repr__', repr_NotEq)


def str_Lt(self: ast.Lt) -> str:
    return '<'


setattr(Lt, '__str__', str_Lt)


def repr_Lt(self: ast.Lt) -> str:
    return 'Lt()'


setattr(Lt, '__repr__', repr_Lt)


def str_LtE(self: ast.LtE) -> str:
    return '<='


setattr(LtE, '__str__', str_LtE)


def repr_LtE(self: ast.LtE) -> str:
    return 'LtE()'


setattr(LtE, '__repr__', repr_LtE)


def str_Gt(self: ast.Gt) -> str:
    return '>'


setattr(Gt, '__str__', str_Gt)


def repr_Gt(self: ast.Gt) -> str:
    return 'Gt()'


setattr(Gt, '__repr__', repr_Gt)


def str_GtE(self: ast.GtE) -> str:
    return '>='


setattr(GtE, '__str__', str_GtE)


def repr_GtE(self: ast.GtE) -> str:
    return 'GtE()'


setattr(GtE, '__repr__', repr_GtE)


def str_Is(self: ast.Is) -> str:
    return 'is'


setattr(Is, '__str__', str_Is)


def repr_Is(self: ast.Is) -> str:
    return 'Is()'


setattr(Is, '__repr__', repr_Is)


def str_Tuple(self: ast.Tuple) -> str:
    return '(' + ', '.join([str(e) for e in self.elts]) + ',)'


setattr(Tuple, '__str__', str_Tuple)


def repr_Tuple(self: ast.Tuple) -> str:
    return 'Tuple(' + repr(self.elts) + ')'


setattr(Tuple, '__repr__', repr_Tuple)


def str_List(self: ast.List) -> str:
    return '[' + ', '.join([str(e) for e in self.elts]) + ']'


setattr(ast.List, '__str__', str_List)


def repr_List(self: ast.List) -> str:
    return 'List(' + repr(self.elts) + ')'


setattr(ast.List, '__repr__', repr_List)


def str_Subscript(self: ast.Subscript) -> str:
    return str(self.value) + '[' + str(self.slice) + ']'


setattr(Subscript, '__str__', str_Subscript)


def repr_Subscript(self: ast.Subscript) -> str:
    return 'Subscript(' + repr(self.value) + ', ' + repr(self.slice) \
           + ', ' + repr(self.ctx) + ')'


setattr(Subscript, '__repr__', repr_Subscript)


def str_FunctionDef(self: ast.FunctionDef) -> str:
    if isinstance(self.args, ast.arguments):
        params = ', '.join([a.arg + ' : ' + str(a.annotation) for a in self.args.args])
    else:
        params = ', '.join([x + ' : ' + str(t) for (x, t) in self.args])
    indent()
    if isinstance(self.body, list):
        body = str_stmts(self.body)
    elif isinstance(self.body, dict):
        body = ''
        for (l, ss) in self.body.items():
            body += l + ':\n'
            indent()
            body += '\n'.join([str(s) for s in ss])
            body += '\n'
            dedent()
    else:
        body = ''
    dedent()
    return indent_stmt() + 'def ' + self.name + '(' + params + ')' + \
           ' -> ' + str(self.returns) + ':\n' + body + '\n'


def repr_FunctionDef(self: ast.FunctionDef) -> str:
    return 'FunctionDef(' + self.name + ',' + repr(self.args) + ',' + \
           repr(self.body) + ')'


setattr(FunctionDef, '__str__', str_FunctionDef)
setattr(FunctionDef, '__repr__', repr_FunctionDef)


def str_Lambda(self: ast.Lambda) -> str:
    if isinstance(self.args, ast.arguments):
        params = ', '.join([a.arg for a in self.args.args])
    else:
        params = ', '.join([x for x in self.args])
    body = str(self.body)
    return '(lambda ' + params + ': ' + body + ')'


def repr_Lambda(self: ast.Lambda) -> str:
    return 'Lambda(' + repr(self.args) + ',' + repr(self.body) + ')'


setattr(Lambda, '__str__', str_Lambda)
setattr(Lambda, '__repr__', repr_Lambda)


def str_ImportFrom(self: ast.ImportFrom) -> str:
    return indent_stmt() + 'from' + ' X ' + 'import' + ' Y\n'

def repr_ImportFrom(self: ast.ImportFrom) -> str:
    return 'ImportFrom()'

setattr(ImportFrom, '__str__', str_ImportFrom)
setattr(ImportFrom, '__repr__', repr_ImportFrom)


################################################################################
# __eq__ and __hash__ for classes in the ast module
################################################################################

def eq_Name(self: ast.Name, other: object) -> bool:
    if isinstance(other, Name):
        return self.id == other.id
    else:
        return False


setattr(Name, '__eq__', eq_Name)


def hash_Name(self: ast.Name) -> int:
    return hash(self.id)


setattr(Name, '__hash__', hash_Name)

################################################################################
# Generating unique names
################################################################################

name_id = 0


def generate_name(name: str) -> str:
    global name_id
    ls = name.split('.')
    new_id = name_id
    name_id += 1
    return ls[0] + '.' + str(new_id)


################################################################################
# AST classes
################################################################################

class Type:
    pass

def make_assigns(bs: Iterable[tuple[expr, expr]]) -> list[stmt]:
    return [Assign([x], rhs) for (x, rhs) in bs]


def make_begin(bs: list[tuple[expr, expr]], e: expr) -> expr:
    if len(bs) > 0:
        return Begin([Assign([x], rhs) for (x, rhs) in bs], e)
    else:
        return e


@dataclass
class Cast(expr):
    body: expr
    source: Type
    target: Type
    __match_args__ = ("body", "source", "target")

    def __str__(self) -> str:
        return '(' + str(self.body) + ' : ' + str(self.source) + ' => ' + str(self.target) + ')'


# A lambda expression whose parameters are annotated with types.
@dataclass
class AnnLambda(expr):
    params: list[tuple[str, Type]]
    returns: Type
    body: expr
    __match_args__ = ("params", "returns", "body")

    def __str__(self) -> str:
        return 'lambda [' + \
               ', '.join([x + ':' + str(t) for (x, t) in self.params]) + '] -> ' \
               + str(self.returns) + ': ' + str(self.body)


# Instantiate a generic function
@dataclass
class Inst(expr):
    generic: expr
    type_args: dict[str, Type]
    __match_args__ = ("generic", "type_args")

    def __str__(self) -> str:
        return str(self.generic) + str(self.type_args)

# An uninitialized value of a given type.
# Needed for boxing local variables.
@dataclass
class Uninitialized(expr):
    ty: Type
    __match_args__ = ("ty",)

    def __str__(self) -> str:
        return 'uninit[' + str(self.ty) + ']'


@dataclass
class CProgram:
    __match_args__ = ("body",)
    body: dict[str, list[stmt]]

    def __str__(self) -> str:
        result = []
        for (l, ss) in self.body.items():
            block = l + ':\n'
            indent()
            block += '\n'.join([str(s) for s in ss])
            dedent()
            result.append(block)
        return '\n\n'.join(result)


@dataclass
class CProgramDefs:
    defs: list[stmt]
    __match_args__ = ("defs",)

    def __str__(self) -> str:
        return '\n'.join([str(d) for d in self.defs]) + '\n'


@dataclass
class Goto(stmt):
    label: str
    __match_args__ = ("label",)

    def __str__(self) -> str:
        return indent_stmt() + 'goto ' + self.label


@dataclass
class Allocate(expr):
    length: int
    ty: Type
    __match_args__ = ("length", "ty")

    def __str__(self) -> str:
        return 'allocate(' + str(self.length) + ',' + str(self.ty) + ')'


@dataclass
class AllocateArray(expr):
    length: int
    ty: Type
    __match_args__ = ("length", "ty")

    def __str__(self) -> str:
        return 'allocate_array(' + str(self.length) + ',' + str(self.ty) + ')'


@dataclass
class AllocateClosure(expr):
    length: int
    ty: Type
    arity: int
    __match_args__ = ("length", "ty", "arity")

    def __str__(self) -> str:
        return 'alloc_clos(' + str(self.length) + ',' + str(self.ty) \
               + ',' + str(self.arity) + ')'

@dataclass
class UncheckedCast(expr):
    exp: expr
    ty: Type
    __match_args__ = ("exp","ty")

@dataclass
class Collect(stmt):
    size: int
    __match_args__ = ("size",)

    def __str__(self) -> str:
        return indent_stmt() + 'collect(' + str(self.size) + ')\n'


@dataclass
class Begin(expr):
    __match_args__ = ("body", "result")
    body: list[stmt]
    result: expr

    def __str__(self) -> str:
        indent()
        stmts = '\n'.join([str(s) for s in self.body])
        stmts += '\n' if self.body else ''
        end = indent_stmt() + 'produce ' + str(self.result) + '\n'
        dedent()
        return '{\n' + stmts + end + indent_stmt() + '}'


@dataclass
class GlobalValue(expr):
    name: str
    __match_args__ = ("name",)

    def __str__(self) -> str:
        return str(self.name)


@dataclass(eq=True)
class IntType(Type):
    def __str__(self) -> str:
        return 'int'


@dataclass(eq=True)
class BoolType(Type):
    def __str__(self) -> str:
        return 'bool'


@dataclass(eq=True)
class VoidType(Type):
    def __str__(self) -> str:
        return 'void'


@dataclass(eq=True)
class Bottom(Type):
    def __str__(self) -> str:
        return 'bottom'


@dataclass(eq=True)
class TupleType(Type):
    types: list[Type]
    __match_args__ = ("types",)

    def __str__(self) -> str:
        return 'tuple[' + ','.join([str(p) for p in self.types]) + ']'


@dataclass(eq=True)
class ListType(Type):
    elt_type: Type
    __match_args__ = ("elt_type",)

    def __str__(self) -> str:
        return 'list[' + str(self.elt_type) + ']'


# Deliberately shadows ast.FunctionType (from `from ast import *`).
@dataclass(eq=True)
class FunctionType(Type):  # type: ignore[no-redef]
    param_types: list[Type]
    ret_type: Type
    __match_args__ = ("param_types", "ret_type")

    def __str__(self) -> str:
        return 'Callable[[' + ','.join([str(p) for p in self.param_types]) + ']' \
               + ', ' + str(self.ret_type) + ']'

@dataclass(eq=True)
class GenericVar(Type):
    id: str
    __match_args__ = ("id",)
    def __str__(self) -> str:
        return str(self.id)

@dataclass(eq=True)
class AllType(Type):
    params: list[str]
    typ: Type
    __match_args__ = ("params", "typ")

    def __str__(self) -> str:
        return '∀ ' + ','.join([str(p) for p in self.params]) + '(' \
            + str(self.typ) + ')'

@dataclass(eq=True)
class FunRef(expr):
    name: str
    arity: int
    __match_args__ = ("name", "arity")

    def __str__(self) -> str:
        return '{' + self.name + '}'


@dataclass
class TailCall(stmt):
    func: expr
    args: list[expr]
    __match_args__ = ("func", "args")

    def __str__(self) -> str:
        return indent_stmt() + 'tail ' + str(self.func) + '(' + ', '.join([str(e) for e in self.args]) + ')\n'


# like a Tuple, but also stores the function's arity
@dataclass
class Closure(expr):
    arity: int
    args: list[expr]
    __match_args__ = ("arity", "args")

    def __str__(self) -> str:
        if hasattr(self, 'has_type'):
            typ = ':' + str(self.has_type)
        else:
            typ = ''
        return 'closure{' + repr(self.arity) + '}(' + ', '.join([str(e) for e in self.args]) + ')' + typ


@dataclass
class Inject(expr):
    value: expr
    typ: Type
    __match_args__ = ("value", "typ")

    def __str__(self) -> str:
        return 'inject(' + str(self.value) + ', ' + str(self.typ) + ')'


@dataclass
class Project(expr):
    value: expr
    typ: Type
    __match_args__ = ("value", "typ")

    def __str__(self) -> str:
        return 'project(' + str(self.value) + ', ' + str(self.typ) + ')'


@dataclass
class TagOf(expr):
    value: expr
    __match_args__ = ("value",)

    def __str__(self) -> str:
        return 'tagof(' + str(self.value) + ')'


@dataclass
class ValueOf(expr):
    value: expr
    typ: Type
    __match_args__ = ("value", "typ")

    def __str__(self) -> str:
        return 'valueof(' + str(self.value) + ', ' + str(self.typ) + ')'


@dataclass(eq=True)
class AnyType(Type):
    def __str__(self) -> str:
        return 'Any'


@dataclass(eq=True)
class ProxyOrTupleType(Type):
    elt_types: list[Type]

    def __str__(self) -> str:
        return 'POrTuple[' + ','.join([str(t) for t in self.elt_types]) + ']'


@dataclass(eq=True)
class ProxyOrListType(Type):
    elt_type: Type

    def __str__(self) -> str:
        return 'POrList[' + str(self.elt_type) + ']'


@dataclass(eq=True)
class TupleProxy(expr):
    value: expr
    reads: list[expr]
    source: Type
    target: Type

    def __str__(self) -> str:
        return 'tuple_proxy(' + str(self.value) + ', ' + str(self.source) \
               + ', ' + str(self.target) + ')'


@dataclass(eq=True)
class RawTuple(expr):
    elts: list[expr]

    def __str__(self) -> str:
        return '[[' + ','.join([str(e) for e in self.elts]) + ']]'


@dataclass(eq=True)
class ListProxy(expr):
    value: expr
    read: expr
    write: expr
    source: Type
    target: Type

    def __str__(self) -> str:
        return 'array_proxy(' + str(self.value) + ', ' + str(self.source) \
               + ', ' + str(self.target) + ')'


@dataclass(eq=True)
class InjectTuple(expr):
    value: expr

    def __str__(self) -> str:
        return 'inject_tuple[' + str(self.value) + ']'


@dataclass(eq=True)
class InjectTupleProxy(expr):
    value: expr
    typ: Type

    def __str__(self) -> str:
        return 'inject_tuple_proxy[' + str(self.value) + ' from ' + str(self.typ) + ']'


@dataclass(eq=True)
class InjectList(expr):
    value: expr

    def __str__(self) -> str:
        return 'inject_array[' + str(self.value) + ']'


@dataclass(eq=True)
class InjectListProxy(expr):
    value: expr
    typ: Type

    def __str__(self) -> str:
        return 'inject_array_proxy[' + str(self.value) + ' from ' + str(self.typ) + ']'


# Base class of runtime values
class Value:
    pass


# smuggle a runtime value back into the AST
@dataclass(eq=True)
class ValueExp(expr):
    value: Value


@dataclass(eq=True)
class ProxiedTuple(Value):
    tup: Value
    reads: list[Value]

    def __str__(self) -> str:
        return 'proxy[' + str(self.tup) + ']'


@dataclass(eq=True)
class ProxiedList(Value):
    tup: Value
    read: Value
    write: Value

    def __str__(self) -> str:
        return 'proxy[' + str(self.tup) + ']'

################################################################################

class TrappedError(Exception):
    pass


################################################################################
# Auxiliary Functions
################################################################################

# signed 64-bit arithmetic

min_int64 = -(1<<63)

max_int64 = (1<<63)-1

mask_64 = (1<<64)-1

offset_64 = 1<<63

def to_unsigned(x: int) -> int:
    return x & mask_64

def to_signed(x: int) -> int:
    return ((x + offset_64) & mask_64) - offset_64

def add64(x: int, y: int) -> int:
    return to_signed(x+y)

def sub64(x: int, y: int) -> int:
    return to_signed(x-y)

def mul64(x: int, y: int) -> int:
    return to_signed(x*y)

def neg64(x: int) -> int:
    return to_signed(-x)

def xor64(x: int, y: int) -> int:
    return to_signed(x^y)

def is_int64(x: object) -> bool:
    return isinstance(x,int) and (x >= min_int64 and x <= max_int64)

def input_int() -> int:
    # entering illegal characters may cause exception,
    # but we won't worry about that
    x = int(input())
    # clamp to 64 bit signed number, emulating behavior of C's scanf
    x = min(max_int64,max(min_int64,x))
    return x

def unzip(ls: Iterable[tuple[A, B]]) -> tuple[list[A], list[B]]:
    xs: list[A] = []
    ys: list[B] = []
    for (x, y) in ls:
        xs += [x]
        ys += [y]
    return (xs, ys)


def align(n: int, alignment: int) -> int:
    if 0 == n % alignment:
        return n
    else:
        return n + (alignment - n % alignment)


def bool2int(b: object) -> int:
    if b:
        return 1
    else:
        return 0


def label_name(n: str) -> str:
    if platform == "darwin":
        return '_' + n
    else:
        return n


tracing = False


def enable_tracing() -> None:
    global tracing
    tracing = True


def trace(msg: object) -> None:
    if tracing:
        print(msg, file=sys.stderr)


def is_python_extension(filename: str) -> bool:
    s = os.path.splitext(filename)
    if len(s) > 1:
        return s[1] == ".py"
    else:
        return False


# Pass name -> type checker / interpreter for that pass's output.
# Each pass produces a different kind of program, so the argument is Any.
TypeCheckDict = Mapping[str, Callable[[Any], object]]
InterpDict = Mapping[str, Callable[[Any], object]]


# Given the `ast` output of a pass and a test program (root) name,
# runs the interpreter on the program and compares the output to the
# expected "golden" output.
def test_pass(passname: str, interp_dict: InterpDict, program_root: str, ast: Any,
              compiler_name: str) -> int:
    if passname in interp_dict.keys():
        input_file = program_root + '.in'
        output_file = program_root + '.out'
        stdin = sys.stdin
        stdout = sys.stdout
        sys.stdin = open(input_file, 'r')
        sys.stdout = open(output_file, 'w')
        interp_dict[passname](ast)
        if sys.stdout.tell() > 0:
            print() # terminate nonempty interpreter output for diff
        sys.stdin = stdin
        sys.stdout = stdout
        result = os.system('diff' + ' -b ' + output_file \
                           + ' ' + program_root + '.golden')
        if result == 0:
            trace('compiler ' + compiler_name + ' success on pass ' + passname \
                  + ' on test\n' + program_root + '\n')
            return 1
        else:
            print('compiler ' + compiler_name + ' failed pass ' + passname \
                  + ' on test:\n' + program_root + '\n')
            return 0
    else:
        trace('compiler ' + compiler_name + ' skip test on pass ' + passname \
              + ' on test\n' + program_root + '\n')
        return 0  # ??


def compile_and_test(compiler: Any, compiler_name: str,
                     type_check_dict: TypeCheckDict, interp_dict: InterpDict,
                     program_filename: str) -> tuple[int, int, int]:
    total_passes = 0
    successful_passes = 0
    successful_test = 0
    from interp_x86.eval_x86 import interp_x86

    program_root = os.path.splitext(program_filename)[0]
    # `program` changes type from pass to pass (Module, CProgram, X86Program, ...),
    # so the driver treats it dynamically.
    program: Any
    with open(program_filename) as source:
        program = parse(source.read())

    trace('\n# source program: ' + os.path.basename(program_root) + '\n')
    trace(program)
    trace('')
    trace(repr(program))
    trace('')

    if 'source' in type_check_dict.keys():
        trace('\n# type checking source program\n')
        type_check_dict['source'](program)


    passname = 'partial_eval'
    if hasattr(compiler, passname):
        trace('\n# ' + passname + '\n')
        program = compiler.partial_eval(program)
        trace(program)
        trace('')
        if passname in type_check_dict.keys():
            type_check_dict[passname](program)
        total_passes += 1
        successful_passes += \
            test_pass(passname, interp_dict, program_root, program,
                      compiler_name)

    passname = 'shrink'
    if hasattr(compiler, passname):
        trace('\n# ' + passname + '\n')
        program = compiler.shrink(program)
        trace(program)
        trace('')
        if passname in type_check_dict.keys():
            type_check_dict[passname](program)
        total_passes += 1
        successful_passes += \
            test_pass(passname, interp_dict, program_root, program,
                      compiler_name)

    passname = 'uniquify'
    if hasattr(compiler, passname):
        trace('\n# ' + passname + '\n')
        program = compiler.uniquify(program)
        trace(program)
        if passname in type_check_dict.keys():
            type_check_dict[passname](program)
        total_passes += 1
        successful_passes += \
            test_pass(passname, interp_dict, program_root, program,
                      compiler_name)

    passname = 'reveal_functions'
    if hasattr(compiler, passname):
        trace('\n# ' + passname + '\n')
        program = compiler.reveal_functions(program)
        trace(program)
        if passname in type_check_dict.keys():
            type_check_dict[passname](program)
        total_passes += 1
        successful_passes += \
            test_pass(passname, interp_dict, program_root, program,
                      compiler_name)

    passname = 'resolve'
    if hasattr(compiler, passname):
        trace('\n# ' + passname + '\n')
        program = compiler.resolve(program)
        trace(program)
        trace('')
        if passname in type_check_dict.keys():
            type_check_dict[passname](program)
        total_passes += 1
        successful_passes += \
            test_pass(passname, interp_dict, program_root, program,
                      compiler_name)

    passname = 'check_bounds'
    if hasattr(compiler, passname):
        trace('\n# ' + passname + '\n')
        program = compiler.check_bounds(program)
        trace(program)
        trace('')
        if passname in type_check_dict.keys():
            type_check_dict[passname](program)
        total_passes += 1
        successful_passes += \
            test_pass(passname, interp_dict, program_root, program,
                      compiler_name)

    passname = 'erase_types'
    if hasattr(compiler, passname):
        trace('\n# ' + passname + '\n')
        program = compiler.erase_types(program)
        trace(program)
        trace('')
        if passname in type_check_dict.keys():
            type_check_dict[passname](program)
        total_passes += 1
        successful_passes += \
            test_pass(passname, interp_dict, program_root, program,
                      compiler_name)

    passname = 'cast_insert'
    if hasattr(compiler, passname):
        trace('\n# ' + passname + '\n')
        program = compiler.cast_insert(program)
        trace(program)
        if passname in type_check_dict.keys():
            type_check_dict[passname](program)
        total_passes += 1
        successful_passes += \
            test_pass(passname, interp_dict, program_root, program,
                      compiler_name)

    passname = 'lower_casts'
    if hasattr(compiler, passname):
        trace('\n# ' + passname + '\n')
        program = compiler.lower_casts(program)
        trace(program)
        if passname in type_check_dict.keys():
            type_check_dict[passname](program)
        total_passes += 1
        successful_passes += \
            test_pass(passname, interp_dict, program_root, program,
                      compiler_name)

    passname = 'differentiate_proxies'
    if hasattr(compiler, passname):
        trace('\n# ' + passname + '\n')
        program = compiler.differentiate_proxies(program)
        trace(program)
        if passname in type_check_dict.keys():
            type_check_dict[passname](program)
        total_passes += 1
        successful_passes += \
            test_pass(passname, interp_dict, program_root, program,
                      compiler_name)

    passname = 'reveal_casts'
    if hasattr(compiler, passname):
        trace('\n# ' + passname + '\n')
        program = compiler.reveal_casts(program)
        trace(program)
        if passname in type_check_dict.keys():
            type_check_dict[passname](program)
        total_passes += 1
        successful_passes += \
            test_pass(passname, interp_dict, program_root, program,
                      compiler_name)

    passname = 'convert_assignments'
    if hasattr(compiler, passname):
        trace('\n# ' + passname + '\n')
        program = compiler.convert_assignments(program)
        trace(program)
        if passname in type_check_dict.keys():
            type_check_dict[passname](program)
        total_passes += 1
        successful_passes += \
            test_pass(passname, interp_dict, program_root, program,
                      compiler_name)

    passname = 'convert_to_closures'
    if hasattr(compiler, passname):
        trace('\n# ' + passname + '\n')
        program = compiler.convert_to_closures(program)
        trace(program)
        if passname in type_check_dict.keys():
            type_check_dict[passname](program)
        total_passes += 1
        successful_passes += \
            test_pass(passname, interp_dict, program_root, program,
                      compiler_name)

    passname = 'limit_functions'
    if hasattr(compiler, passname):
        trace('\n# ' + passname + '\n')
        program = compiler.limit_functions(program)
        trace(program)
        if passname in type_check_dict.keys():
            trace('type checking after ' + passname + '\n')
            type_check_dict[passname](program)
            trace('type checking passed')
        total_passes += 1
        successful_passes += \
            test_pass(passname, interp_dict, program_root, program,
                      compiler_name)

    passname = 'expose_allocation'
    if hasattr(compiler, passname):
        trace('\n# ' + passname + '\n')
        program = compiler.expose_allocation(program)
        trace(program)
        if passname in type_check_dict.keys():
            trace('type checking after ' + passname + '\n')
            type_check_dict[passname](program)
            trace('type checking passed')
        total_passes += 1
        successful_passes += \
            test_pass(passname, interp_dict, program_root, program,
                      compiler_name)

    passname = 'remove_complex_operands'
    if hasattr(compiler, passname):
        trace('\n# ' + passname + '\n')
        program = compiler.remove_complex_operands(program)
        trace(program)
        trace(repr(program))
        if passname in type_check_dict.keys():
            trace('type checking after ' + passname + '\n')
            type_check_dict[passname](program)
            trace('type checking passed')
        total_passes += 1
        successful_passes += \
            test_pass(passname, interp_dict, program_root, program,
                      compiler_name)

    passname = 'explicate_control'
    if hasattr(compiler, passname):
        trace('\n# ' + passname + '\n')
        program = compiler.explicate_control(program)
        trace(program)
        trace(repr(program))
        if passname in type_check_dict.keys():
            trace('type checking after ' + passname + '\n')
            type_check_dict[passname](program)
            trace('type checking passed')
        else:
            trace('skipped type checking')
        total_passes += 1
        successful_passes += \
            test_pass(passname, interp_dict, program_root, program,
                      compiler_name)

    passname = 'select_instructions'
    if hasattr(compiler, passname):
        trace('\n# ' + passname + '\n')
        program = compiler.select_instructions(program)
        trace(program)
        total_passes += 1
        successful_passes += \
            test_pass(passname, interp_dict, program_root, program,
                      compiler_name)

    passname = 'assign_homes'
    if hasattr(compiler, passname):
        trace('\n# ' + passname + '\n')
        program = compiler.assign_homes(program)
        trace(program)
        total_passes += 1
        successful_passes += \
            test_pass(passname, interp_dict, program_root, program,
                      compiler_name)

    passname = 'patch_instructions'
    if hasattr(compiler, passname):
        trace('\n# ' + passname + '\n')
        program = compiler.patch_instructions(program)
        trace(program)
        total_passes += 1
        successful_passes += \
            test_pass(passname, interp_dict, program_root, program,
                      compiler_name)

    passname = 'prelude_and_conclusion'
    if hasattr(compiler, passname):
        trace('\n# ' + passname + '\n')
        program = compiler.prelude_and_conclusion(program)
        trace(program)
        trace("")

        x86_filename = program_root + ".s"
        with open(x86_filename, "w") as dest:
            dest.write(str(program))

        total_passes += 1

        # Run the final x86 program
        emulate_x86 = False
        if emulate_x86:
            stdin = sys.stdin
            stdout = sys.stdout
            sys.stdin = open(program_root + '.in', 'r')
            sys.stdout = open(program_root + '.out', 'w')
            interp_x86(program)
            sys.stdin = stdin
            sys.stdout = stdout
        else:
            if platform == 'darwin':
                os.system('gcc -arch x86_64 runtime.o ' + x86_filename)
            else:
                os.system('gcc runtime.o ' + x86_filename + ' -z noexecstack')
            input_file = program_root + '.in'
            output_file = program_root + '.out'
            os.system('./a.out < ' + input_file + ' > ' + output_file)

        result = os.system('diff' + ' -b ' + program_root + '.out ' \
                           + program_root + '.golden')
        if result == 0:
            successful_passes += 1
            successful_test = 1
            print('compiler ' + compiler_name + ' passed test ' + os.path.basename(program_root))
        else:
            print('compiler ' + compiler_name + ', executable failed' \
                  + ' on test ' + os.path.basename(program_root))
    return (successful_passes, total_passes, successful_test)


def trace_ast_and_concrete(ast: object) -> None:
    trace("concrete syntax:")
    trace(ast)
    trace("")
    trace("AST:")
    trace(repr(ast))


# This function compiles the program without any testing
def compile(compiler: Any, compiler_name: str, type_check_L: Callable[[Any], object],
            type_check_C: Callable[[Any], object] | None,
            program_filename: str) -> None:
    program_root = os.path.splitext(program_filename)[0]
    program: Any
    with open(program_filename) as source:
        program = parse(source.read())

    trace('\n# type check\n')
    type_check_L(program)
    trace_ast_and_concrete(program)

    if hasattr(compiler, 'partial_eval'):
        trace('\n# partial_eval\n')
        program = compiler.partial_eval(program)
        trace_ast_and_concrete(program)

    if hasattr(compiler, 'shrink'):
        trace('\n# shrink\n')
        program = compiler.shrink(program)
        trace_ast_and_concrete(program)

    if hasattr(compiler, 'uniquify'):
        trace('\n# uniquify\n')
        program = compiler.uniquify(program)
        trace_ast_and_concrete(program)

    if hasattr(compiler, 'reveal_functions'):
        trace('\n# reveal functions\n')
        type_check_L(program)
        program = compiler.reveal_functions(program)
        trace_ast_and_concrete(program)

    if hasattr(compiler, 'resolve'):
        trace('\n# resolve\n')
        type_check_L(program)
        program = compiler.resolve(program)
        trace_ast_and_concrete(program)

    if hasattr(compiler, 'convert_assignments'):
        trace('\n# assignment conversion\n')
        type_check_L(program)
        program = compiler.convert_assignments(program)
        trace_ast_and_concrete(program)

    if hasattr(compiler, 'convert_to_closures'):
        trace('\n# closure conversion\n')
        type_check_L(program)
        program = compiler.convert_to_closures(program)
        trace_ast_and_concrete(program)

    if hasattr(compiler, 'limit_functions'):
        trace('\n# limit functions\n')
        type_check_L(program)
        program = compiler.limit_functions(program)
        trace_ast_and_concrete(program)

    if hasattr(compiler, 'expose_allocation'):
        trace('\n# expose allocation\n')
        type_check_L(program)
        program = compiler.expose_allocation(program)
        trace_ast_and_concrete(program)

    trace('\n# remove complex\n')
    program = compiler.remove_complex_operands(program)
    trace_ast_and_concrete(program)

    if hasattr(compiler, 'explicate_control'):
        trace('\n# explicate control\n')
        program = compiler.explicate_control(program)
        trace_ast_and_concrete(program)

    if type_check_C:
        type_check_C(program)

    trace('\n# select instructions\n')
    pseudo_x86 = compiler.select_instructions(program)
    trace_ast_and_concrete(pseudo_x86)

    trace('\n# assign homes\n')
    almost_x86 = compiler.assign_homes(pseudo_x86)
    trace_ast_and_concrete(almost_x86)

    trace('\n# patch instructions\n')
    x86 = compiler.patch_instructions(almost_x86)
    trace_ast_and_concrete(x86)

    trace('\n# prelude and conclusion\n')
    x86 = compiler.prelude_and_conclusion(x86)
    trace_ast_and_concrete(x86)

    # Output x86 program to the .s file
    x86_filename = program_root + ".s"
    with open(x86_filename, "w") as dest:
        dest.write(str(x86))

# Given a test file name, the name of a language, a compiler, a type
# checker and interpreter for the language, and an interpeter for the
# C intermediate language, run all the passes in the compiler,
# checking that the resulting programs produce output that matches the
# golden file.
def run_one_test(test: str, lang: str, compiler: Any, compiler_name: str,
                 type_check_dict: TypeCheckDict,
                 interp_dict: InterpDict) -> tuple[int, int, int]:
#    test_root = os.path.splitext(test)[0]
#    test_name = os.path.basename(test_root)
    return compile_and_test(compiler, compiler_name, type_check_dict,
                            interp_dict, test)


# Given the name of a language, a compiler, the compiler's name, a
# type checker and interpreter for the language, and an interpreter
# for the C intermediate language, test the compiler on all the tests
# in the directory of for the given language, i.e., all the
# python files in ./tests/<language>.
def run_tests(lang: str, compiler: Any, compiler_name: str,
              type_check_dict: TypeCheckDict, interp_dict: InterpDict) -> int:
    # Collect all the test programs for this language.
    homedir = os.getcwd()
    directory = homedir + '/tests/' + lang + '/'
    if not os.path.isdir(directory):
        raise Exception('missing directory for test programs: ' \
                        + directory)
    tests: list[str] = []
    for (dirpath, dirnames, filenames) in os.walk(directory):
        tests = [dirpath + t for t in filter(is_python_extension, filenames)]
        break
    # Compile and run each test program, comparing output to the golden file.
    successful_passes = 0
    total_passes = 0
    successful_tests = 0
    total_tests = 0
    for test in tests:
        (succ_passes, tot_passes, succ_test) = \
            run_one_test(test, lang, compiler, compiler_name,
                         type_check_dict, interp_dict)
        successful_passes += succ_passes
        total_passes += tot_passes
        successful_tests += succ_test
        total_tests += 1

    # Report the pass/fails
    print('tests: ' + repr(successful_tests) + '/' + repr(total_tests) \
          + ' for compiler ' + compiler_name + ' on language ' + lang)
    print('passes: ' + repr(successful_passes) + '/' + repr(total_passes) \
          + ' for compiler ' + compiler_name + ' on language ' + lang)

    failed_tests = total_tests - successful_tests
    return failed_tests
