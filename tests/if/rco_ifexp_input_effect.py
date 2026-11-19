# An if expression as a statement by itself, with input in one branch.
# Its value is thrown away, but the read still has to happen.
x = input_int()
input_int() if x == 0 else 0
print(input_int())
