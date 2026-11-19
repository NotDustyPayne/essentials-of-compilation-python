# The truth tables of and/or. Each line of the table is one bit.
t = input_int() == 1
f = input_int() == 1
print((1 if t and t else 0) + (2 if t and f else 0) + (4 if f and t else 0)
      + (8 if f and f else 0) + (16 if t or t else 0) + (32 if t or f else 0)
      + (64 if f or t else 0) + (128 if f or f else 0))
