# Section 5.12.1: if True discards the else branch, which contains an if
# expression of its own.
x = input_int()
if True:
    print(0)
else:
    x = 1 if False else 2
    print(x)
print(x)
