# negq reads and writes its operand in place, while other variables are live.
x = input_int()
y = - x
z = - y
print(y - z + x)
