# Booleans stored in variables, compared with == and !=.
x = input_int()
y = input_int()
b = x < 3
c = y < 3
print((1 if b == c else 0) + (2 if b != c else 0) + (4 if b == True else 0)
      + (8 if c == False else 0) + (16 if b else 0) + (32 if c else 0))
