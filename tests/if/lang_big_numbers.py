# Comparisons with values that don't fit in 32 bits.
x = input_int()
y = x + x
print((1 if y > 4000000000 else 0) + (2 if x < y else 0) + (4 if y == 6000000000 else 0))
