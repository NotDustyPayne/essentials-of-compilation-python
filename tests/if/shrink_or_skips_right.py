# x is 1, so `or` is already true and must not read the 99.
x = input_int()
if x == 1 or input_int() == 5:
    print(1)
else:
    print(2)
print(input_int())
