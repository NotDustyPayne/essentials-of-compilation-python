# Section 5.7, figure 5.12: an if expression nested in the condition of
# another. With x = 0: x < 1, then x == 0, so y + 2.
x = input_int()
y = input_int()
print(y + 2 if (x == 0 if x < 1 else x == 2) else y + 10)
