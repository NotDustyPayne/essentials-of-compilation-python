# Figure 5.12, third path: x = 2, so x < 1 is false and x == 2 is true.
x = input_int()
y = input_int()
print(y + 2 if (x == 0 if x < 1 else x == 2) else y + 10)
