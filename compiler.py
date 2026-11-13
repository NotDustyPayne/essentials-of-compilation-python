import ast
from ast import *
from utils import *
# x86_ast's `arg` (an x86 operand) and `Global` deliberately replace ast.arg and
# ast.Global from `from ast import *`. For function parameters, write ast.arg.
from x86_ast import *  # type: ignore[assignment]
import os

# Use the built-in list/tuple/dict/set for type hints. Importing
# typing.List / typing.Tuple here would hide ast.List / ast.Tuple, which
# you'll pattern-match on in later chapters (`case Tuple(...)`).

# A temporary variable and the expression it's bound to (from RCO).
Binding = tuple[Name, expr]
Temporaries = list[Binding]


class Compiler:

    ############################################################################
    # Remove Complex Operands
    ############################################################################

    def rco_exp(self, e: expr, need_atomic : bool) -> tuple[expr, Temporaries]:
        """
        Pattern match on the expression types, if its atomic do :-> return as is
        if its non atomic do :-> atomicize the expression, and if it needs bindings create that
        """
        match e:
            case Constant(n):
                return (Constant(n), [])
            
            case Name(var):
                return (Name(var), [])
            
            case Call(Name('input_int'),[]):
                if need_atomic:
                    new_binding_name = Name(generate_name("tmp"))
                    new_temp = new_binding_name, Call(Name('input_int'),[])
                    return new_binding_name, [new_temp]
                
                else:
                    return Call(Name('input_int'),[]) , []
            
            case UnaryOp(USub(), exp):
                atm, temps = self.rco_exp(exp, True)
                if need_atomic:
                    new_binding_name = Name(generate_name("tmp"))
                    new_temp = new_binding_name, UnaryOp(USub(), atm)
                    return new_binding_name , temps + [new_temp]
                else:
                    return UnaryOp(USub(), atm) , temps

            case BinOp(left_exp, Add(), right_exp):
                left_atm, left_temps = self.rco_exp(left_exp, True)
                right_atm, right_temps = self.rco_exp(right_exp, True)
                if need_atomic:
                    new_binding_name = Name(generate_name("tmp"))
                    new_temp = new_binding_name , BinOp(left_atm, Add(), right_atm)
                    return new_binding_name, left_temps + right_temps + [new_temp]
                else:
                    return BinOp(left_atm, Add(), right_atm) , left_temps + right_temps

            case BinOp(left_exp, Sub(), right_exp):
                left_atm, left_temps = self.rco_exp(left_exp, True)
                right_atm, right_temps = self.rco_exp(right_exp, True)
                if need_atomic:
                    new_binding_name = Name(generate_name("tmp"))
                    new_temp = new_binding_name , BinOp(left_atm, Sub(), right_atm)
                    return new_binding_name, left_temps + right_temps + [new_temp]
                else:
                    return BinOp(left_atm, Sub(), right_atm) , left_temps + right_temps
            case _:
                raise Exception("invalid program in rco_exp")


    def generate_binding_statements(self, s: Temporaries) ->list[stmt]:
        return [Assign([name], value) for (name,value) in s]


    def rco_stmt(self, s: stmt) -> list[stmt]:
        """
        Identify when a statement needs to have simplified atomic expressions
        """
        match s:
            case Expr(Call(Name('print'), [exp])):
                updated_exp, temp_bindings = self.rco_exp(e=exp, need_atomic=True)
                return self.generate_binding_statements(temp_bindings) + [Expr(Call(Name('print'), [updated_exp]))]
            case Expr(exp):
                updated_exp, temp_bindings = self.rco_exp(e=exp, need_atomic=False)
                return self.generate_binding_statements(temp_bindings) + [Expr(updated_exp)]

            case Assign([Name(var)], exp):
                updated_exp, temp_bindings = self.rco_exp(e=exp, need_atomic=False)
                return self.generate_binding_statements(temp_bindings) + [Assign([Name(var)], updated_exp)]
            case _:
                raise Exception("invalid program in rco_stmt")


    def remove_complex_operands(self, p: Module) -> Module:

        updated_statements: list[stmt] = []
        for statment in p.body:
            updated_statements.extend(self.rco_stmt(statment))

        return Module(body=updated_statements, type_ignores=p.type_ignores)            

    ############################################################################
    # Select Instructions
    ############################################################################

    # The expression e passed to select_arg should furthermore be an atom.
    # (But there is no type for atoms, so the type of e is given as expr.)
    def select_arg(self, e: expr) -> arg:
        """
        translate individual expressions to x86 counterparts
        this will just be the atms, that map from atm-> arg
        """
        match e:
            case Constant(int):
                return Immediate(int)
            case Name(var):
                return Variable(var)
            case _:
                raise Exception("unexpected non-atomic in select_arg")


    def select_stmt(self, s: stmt) -> list[instr]:
        """
        take some statement and return it as a list of instructions
        instr class is all the X86 defined things we have
        """
        match s:
            case Expr(Call(Name('print'), [atm])):
                return [
                    Instr('movq', [self.select_arg(atm), Reg('rdi')]),
                    Callq('print_int', 1)
                ]
            case Expr(exp):
                # MOST of this is NOT observable!! we don't needa. lot of these cases!
                # for example, " a + b ; print (a) " who cares about the result of a + b here
                match exp:
                    case Call(Name('input_int'), []):
                        return [
                            Callq('read_int', 0),
                        ]
                    case UnaryOp(USub(), atm):
                        return [Instr('negq', [self.select_arg(atm)])]
                    case BinOp(left_atm, Add(), right_atm):
                        return [
                            Instr('movq', [self.select_arg(left_atm), Reg('rax')]),
                            Instr('addq', [self.select_arg(right_atm), Reg('rax')]),
                        ]
                    case BinOp(left_atm, Sub(), right_atm):
                        return [
                            Instr('movq', [self.select_arg(left_atm), Reg('rax')]),
                            Instr('subq', [self.select_arg(right_atm), Reg('rax')]),
                        ]
                    case _:
                        raise Exception("error in pattern match of Expr in select_stmt ")
            case Assign([var], exp):
                match exp:
                    case Call(Name('input_int'), []):
                        return [
                            Callq('read_int', 0),
                            Instr('movq', [Reg('rax'), self.select_arg(var)])
                        ]
                    case UnaryOp(USub(), atm):
                        return [
                            Instr('movq', [self.select_arg(atm), Reg('rax')]),
                            Instr('negq', [Reg('rax')]),
                            Instr('movq', [Reg('rax'), self.select_arg(var)])
                            ]
                    case BinOp(left_atm, Add(), right_atm):
                        return [
                            Instr('movq', [self.select_arg(left_atm), Reg('rax')]),
                            Instr('addq', [self.select_arg(right_atm), Reg('rax')]),
                            Instr('movq', [Reg('rax'), self.select_arg(var)])
                        ]
                    case BinOp(left_atm, Sub(), right_atm):
                        return [
                            Instr('movq', [self.select_arg(left_atm), Reg('rax')]),
                            Instr('subq', [self.select_arg(right_atm), Reg('rax')]),
                            Instr('movq', [Reg('rax'), self.select_arg(var)])
                        ]
                    # needs to handle atms as well
                    case Name(inner_var):
                        return [Instr('movq', [self.select_arg(Name(inner_var)), self.select_arg(var)])]
                    case Constant(inner_int):
                        return [Instr('movq', [self.select_arg(Constant(inner_int)), self.select_arg(var)])]

                    case _:
                        raise Exception("error in pattern match of Assign in select_stmt")
            case _:
                raise Exception("error in select_stmt, pattern unrecognized")

    def select_instructions(self, p: Module) -> X86Program:
        """
        we need to do some translation here, something about labels
        """
        instructions : list[instr] = []
        for statement in p.body:
            instructions.extend(self.select_stmt(statement))
        x86_program = X86Program(body=instructions)
        return x86_program

    ############################################################################
    # Assign Homes
    ############################################################################

    def assign_homes_arg(self, a: arg, home: dict[Variable, arg]) -> arg:
        match a:
            case Variable(var):
                if Variable(var) in home:
                    return home[a]
                else:
                    offset = -8 * (len(home.keys()) + 1)
                    home[a] = Deref('rbp', offset)
                    return home[a]
            case _:
                return a


    def assign_homes_instr(self, i: instr,
                           home: dict[Variable, arg]) -> instr:
        match i:
            case Instr(instr, args):
                homed_args = [self.assign_homes_arg(a, home) for a in args]
                return Instr(instr, homed_args)
            case Callq(func, num_args):
                return Callq(func, num_args)
            case _:
                raise Exception("unrecognized pattern in assign_homes_instr")


    def assign_homes(self, p: X86Program) -> X86Program:
        program_instructions_with_assign_homes : list[instr] = []
        homes_dict : dict[Variable, arg] = {}
        assert isinstance(p.body, list)

        for instruction in p.body:
            program_instructions_with_assign_homes.append(self.assign_homes_instr(instruction, homes_dict))

        stack_space = align((len(homes_dict.keys())) * 8 , 16)

        return X86Program(body = program_instructions_with_assign_homes, stack_space=stack_space)

    ############################################################################
    # Patch Instructions
    ############################################################################

    def patch_instr(self, i: instr) -> list[instr]:
        # YOUR CODE HERE
        raise NotImplementedError

    def patch_instructions(self, p: X86Program) -> X86Program:
        # YOUR CODE HERE
        raise NotImplementedError

    ############################################################################
    # Prelude & Conclusion
    ############################################################################

    def prelude_and_conclusion(self, p: X86Program) -> X86Program:
        # YOUR CODE HERE
        raise NotImplementedError

