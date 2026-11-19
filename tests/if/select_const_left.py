# A constant on the left of a comparison: cmpq x, $3 has an immediate
# second operand, which patch_instructions must fix (section 5.10).
x = input_int()
print((1 if 3 < x else 0) + (2 if 3 == x else 0) + (4 if 10 >= x else 0))
