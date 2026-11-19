# The same, but b is used only in the else branch (reached by jmp).
a = input_int()
b = input_int()
c = a + 10
if c < 5:
    print(c)
else:
    print(b)
