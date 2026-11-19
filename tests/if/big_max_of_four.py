a = input_int()
b = input_int()
c = input_int()
d = input_int()
m1 = a if a > b else b
m2 = c if c > d else d
print(m1 if m1 > m2 else m2)
