# b = not b becomes a single xorq $1, b (section 5.8).
x = input_int()
b = x < 3
b = not b
print(1 if b else 0)
b = not b
print(1 if b else 0)
