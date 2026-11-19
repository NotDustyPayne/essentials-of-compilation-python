# Each branch of the if expression reads input. Only the chosen branch may
# read (section 5.6, Begin). Hoisting both reads out of the if would read
# 10 and 20 here, print 19, and then the last read would find no input.
x = input_int()
y = (input_int() + 1) if x == 0 else (input_int() - 1)
print(y)
print(input_int())
