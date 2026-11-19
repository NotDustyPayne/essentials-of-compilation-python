# Both branches continue with the same (long) code. It must appear once in
# the CIf program, reached by goto, not copied into each branch.
x = input_int()
if x < 0:
    y = 0 - x
else:
    y = x
a = y + 1
b = a + y
c = b - a
print(a + b + c)
print(y)
