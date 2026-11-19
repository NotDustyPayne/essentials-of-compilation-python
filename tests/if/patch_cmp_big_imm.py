# cmpq takes at most a 32-bit immediate.
x = input_int()
print((1 if x < 9999999999 else 0) + (2 if 9999999999 == x else 0))
