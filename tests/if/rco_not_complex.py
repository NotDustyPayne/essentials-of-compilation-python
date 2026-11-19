# not applied to a non-atomic expression, stored in a variable.
x = input_int()
y = input_int()
b = not (x < y)
c = not (x + 1 == y)
print((1 if b else 0) + (2 if c else 0))
