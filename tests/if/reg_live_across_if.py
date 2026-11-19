# Values defined before the if and used after it.
a = input_int()
b = input_int()
if a < b:
    c = a + 1
else:
    c = b + 1
print(a + b + c)
