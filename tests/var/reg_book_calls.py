# Figure 4.2: x is live during the second call to input_int, so it must not
# be in a caller-saved register (the book puts it in %rbx).
x = input_int()
y = input_int()
print((x + y) + 42)
