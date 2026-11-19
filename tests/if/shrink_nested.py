# and/or nested inside each other and inside not.
a = input_int()
b = input_int()
c = input_int()
if (a < b and b < c) or not (a == c):
    print(1)
else:
    print(2)
print(1 if not (a < b or b < c) and a == c else 0)
