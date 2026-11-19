# Comparisons whose operands are not atomic.
x = input_int()
y = input_int()
print(1 if (x + 1) < (y - -2) else 0)
print(1 if -(x) == y - 7 else 0)
