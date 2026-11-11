# var = atm - var: subtraction is not commutative, so the
# addq shortcut from section 2.5 must not be used here.
x = 3
x = 10 - x
print(x)
