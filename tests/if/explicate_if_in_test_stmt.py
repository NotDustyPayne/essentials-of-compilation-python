# An if statement whose condition is itself an if expression.
a = input_int()
b = input_int()
c = input_int()
if (a < b if c == 0 else a > b):
    print(1)
else:
    print(2)
