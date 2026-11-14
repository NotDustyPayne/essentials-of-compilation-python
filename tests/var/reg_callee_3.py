# 3 variables live across a call to print_int. They need callee-saved
# registers (or the stack), so the prelude saves 3 callee-saved registers.
# Checks the frame stays 16-byte aligned.
c0 = 1
c1 = 10
c2 = 100
print(-1)
print(c0 + c1 + c2)
