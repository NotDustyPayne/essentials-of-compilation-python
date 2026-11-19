import os
import sys

sys.path.append('../python-student-support-code')
sys.path.append('../python-student-support-code/interp_x86')

import compiler
import interp_Lvar
import type_check_Lvar
from utils import run_tests, run_one_test, enable_tracing, InterpDict, TypeCheckDict
from interp_x86.eval_x86 import interp_x86

enable_tracing()

# Which chapter's compiler to test: 2, 4 (register allocation), or 5
# (conditionals). tools/progress.py --chapter N gives a more detailed report.
CHAPTER = 2

C: compiler.Compiler  # each chapter's Compiler subclasses the one before
typecheck_dict: TypeCheckDict
interp_dict: InterpDict

if CHAPTER == 5:
    import compiler_conditionals
    import interp_Lif
    import interp_Cif
    import type_check_Lif
    import type_check_Cif
    C = compiler_conditionals.Compiler()
    lang = 'if'
    typecheck_Lif = type_check_Lif.TypeCheckLif().type_check
    typecheck_Cif = type_check_Cif.TypeCheckCif().type_check
    typecheck_dict = {
        'source': typecheck_Lif,
        'shrink': typecheck_Lif,
        'remove_complex_operands': typecheck_Lif,
        'explicate_control': typecheck_Cif,
    }
    interpLif = interp_Lif.InterpLif().interp
    interpCif = interp_Cif.InterpCif().interp
    interp_dict = {
        'shrink': interpLif,
        'remove_complex_operands': interpLif,
        'explicate_control': interpCif,
        'select_instructions': interp_x86,
        'assign_homes': interp_x86,
        'patch_instructions': interp_x86,
    }
else:
    if CHAPTER == 4:
        import compiler_register_allocator
        C = compiler_register_allocator.Compiler()
    else:
        C = compiler.Compiler()
    lang = 'var'
    typecheck_Lvar = type_check_Lvar.TypeCheckLvar().type_check
    typecheck_dict = {
        'source': typecheck_Lvar,
        'remove_complex_operands': typecheck_Lvar,
    }
    interpLvar = interp_Lvar.InterpLvar().interp
    interp_dict = {
        'remove_complex_operands': interpLvar,
        'select_instructions': interp_x86,
        'assign_homes': interp_x86,
        'patch_instructions': interp_x86,
    }

if True:
    run_tests(lang, C, lang,
              typecheck_dict,
              interp_dict)
else:
    run_one_test(os.getcwd() + '/tests/' + lang + '/zero.py',
                 lang,
                 C,
                 lang,
                 typecheck_dict,
                 interp_dict)
