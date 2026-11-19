# An if expression with constant branches, used as a condition.
x = input_int()
if (True if x < 2 else False):
    print(1)
else:
    print(2)
if (False if x < 2 else True):
    print(3)
else:
    print(4)
