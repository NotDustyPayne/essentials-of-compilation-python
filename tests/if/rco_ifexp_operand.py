# An if expression as the operand of + must become a temporary.
x = input_int()
y = input_int()
print(5 + (x if x < y else y))
print((x if x > y else y) - (1 if x == y else 2))
