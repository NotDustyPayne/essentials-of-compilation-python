# A chain of decisions, each feeding the next.
x = input_int()
y = input_int()
z = 0
if x < y:
    z = z + 1
else:
    z = z - 1
if z == 1 and y > 5:
    z = z + 10
else:
    z = z + 20
w = (z + 100) if (z > 15 or not (x == 2)) else (z - 100)
if w > 50:
    if w < 120:
        print(w)
    else:
        print(w - 1000)
else:
    print(0 - w)
