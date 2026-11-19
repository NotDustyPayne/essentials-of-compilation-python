# Figure 5.12 again, other path: x = 3, so x < 1 is false and x == 2 is
# false: y + 10.
x = input_int()
y = input_int()
print(y + 2 if (x == 0 if x < 1 else x == 2) else y + 10)
