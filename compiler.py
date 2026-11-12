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
        # YOUR CODE HERE
        raise NotImplementedError

    def select_stmt(self, s: stmt) -> list[instr]:
        # YOUR CODE HERE
        raise NotImplementedError

    def select_instructions(self, p: Module) -> X86Program:
        # YOUR CODE HERE
        raise NotImplementedError

    ############################################################################
    # Assign Homes
    ############################################################################

    def assign_homes_arg(self, a: arg, home: dict[Variable, arg]) -> arg:
        # YOUR CODE HERE
        raise NotImplementedError

    def assign_homes_instr(self, i: instr,
                           home: dict[Variable, arg]) -> instr:
        # YOUR CODE HERE
        raise NotImplementedError

    def assign_homes(self, p: X86Program) -> X86Program:
        # YOUR CODE HERE
        raise NotImplementedError

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

