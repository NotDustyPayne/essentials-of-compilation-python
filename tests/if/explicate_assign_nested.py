# Nested if expressions on the right of an assignment.
a = input_int()
b = input_int()
c = input_int()
z = (1 if a < b else 2) if c == 0 else (3 if a == c else 4)
print(z)
