# Variables that are assigned but never read are never live. They still
# need a home, and the input_int call must still happen.
u = 7
v = input_int()
w = u + 1
print(input_int())
