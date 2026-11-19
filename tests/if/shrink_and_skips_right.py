# x is not 0, so `and` must not evaluate input_int() on its right.
# If it does, the second read takes the 99 and the last read finds no input.
x = input_int()
if x == 0 and input_int() == 5:
    print(1)
else:
    print(2)
print(input_int())
