# a is live across the read_int inside the branch, so it needs a
# callee-saved register (or the stack), and main must save that register.
a = input_int()
if a < 100:
    b = input_int()
    print(a + b)
else:
    print(a)
print(a)
