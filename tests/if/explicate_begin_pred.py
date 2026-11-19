# The branches of the inner if are comparisons with a non-atomic operand,
# so after RCO they are Begin expressions in predicate position.
c = input_int()
x = input_int()
if (x == input_int() if c == 1 else x == input_int() + 1):
    print(1)
else:
    print(2)
print(input_int())
