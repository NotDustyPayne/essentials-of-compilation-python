# 14 Booleans live at the same time, more than there are registers, so some
# are spilled to the stack. `movzbq %al, -16(%rbp)` is not valid x86: the
# second argument of movzbq must be a register (section 5.10).
a = input_int()
p0 = a < 1
p1 = a < 2
p2 = a < 3
p3 = a < 4
p4 = a < 5
p5 = a < 6
p6 = a < 7
p7 = a < 8
p8 = a < 9
p9 = a < 10
p10 = a < 11
p11 = a < 12
p12 = a < 13
p13 = a < 14
print((1 if p0 else 0) + (1 if p1 else 0) + (1 if p2 else 0) + (1 if p3 else 0)
      + (1 if p4 else 0) + (1 if p5 else 0) + (1 if p6 else 0) + (1 if p7 else 0)
      + (1 if p8 else 0) + (1 if p9 else 0) + (1 if p10 else 0) + (1 if p11 else 0)
      + (1 if p12 else 0) + (1 if p13 else 0))
