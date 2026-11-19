# Comparisons of two constants: cmpq $3, $2 is not valid x86; the second
# operand must be moved into a register first.
print((1 if 2 < 3 else 0) + (2 if 3 == 3 else 0) + (4 if 5 <= 4 else 0))
