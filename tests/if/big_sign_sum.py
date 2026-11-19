# Sum of signs of five inputs: -1, 0, or +1 each.
a = input_int()
b = input_int()
c = input_int()
d = input_int()
e = input_int()
s = (-1 if a < 0 else (0 if a == 0 else 1)) + (-1 if b < 0 else (0 if b == 0 else 1)) \
    + (-1 if c < 0 else (0 if c == 0 else 1)) + (-1 if d < 0 else (0 if d == 0 else 1)) \
    + (-1 if e < 0 else (0 if e == 0 else 1))
print(s)
