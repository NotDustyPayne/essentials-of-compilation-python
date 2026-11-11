# An expression statement with nested input calls: both inputs
# must still be read, even though the result is discarded.
input_int() + (input_int() - 1)
print(input_int())
