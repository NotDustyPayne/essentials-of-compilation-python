# Several call-live variables, used in different branches, so the
# callee-saved registers they get must be saved in main and restored in
# the conclusion block.
a = input_int()
b = input_int()
c = input_int()
if a < b:
    d = input_int()
    print(a + b + c + d)
else:
    print(a - b - c)
print(a + c)
