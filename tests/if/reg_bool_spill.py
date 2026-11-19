# Booleans computed while many values are live, so some of the Boolean
# variables end up on the stack: movzbq into memory needs patching.
a = input_int()
b = input_int()
c = input_int()
d = input_int()
e = input_int()
f = input_int()
g = input_int()
h = input_int()
i = input_int()
j = input_int()
k = input_int()
l = input_int()
p = a < b
q = c < d
r = e == f
s = g > h
t = i != j
u = k >= l
print((1 if p else 0) + (2 if q else 0) + (4 if r else 0) + (8 if s else 0)
      + (16 if t else 0) + (32 if u else 0) + a + b + c + d + e + f + g + h + i + j + k + l)
