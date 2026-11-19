# The result of and/or stored in variables, not just used as a condition.
x = input_int()
y = input_int()
both = x > 0 and y > 0
either = x > 0 or y > 0
print((1 if both else 0) + (2 if either else 0))
