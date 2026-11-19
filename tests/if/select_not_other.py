# c = not b needs movq then xorq.
x = input_int()
b = x < 3
c = not b
print((1 if b else 0) + (2 if c else 0))
