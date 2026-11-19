# x is 0, so `and` must evaluate its right side (which reads 5).
x = input_int()
if x == 0 and input_int() == 5:
    print(1)
else:
    print(2)
print(input_int())
