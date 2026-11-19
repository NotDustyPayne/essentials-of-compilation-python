# True and False become 1 and 0.
t = True
f = False
print((1 if t else 0) + (2 if f else 0) + (4 if t == f else 0) + (8 if t != f else 0))
