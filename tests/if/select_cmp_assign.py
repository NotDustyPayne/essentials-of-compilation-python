# Comparisons stored in variables: cmpq, set<cc> %al, movzbq %al, var.
x = input_int()
y = input_int()
lt = x < y
eq = x == y
ge = x >= y
print((1 if lt else 0) + (2 if eq else 0) + (4 if ge else 0))
