# if statements nested in both branches of an if statement.
a = input_int()
b = input_int()
if a < b:
    if a == 0:
        print(1)
    else:
        print(2)
    print(3)
else:
    if b == 0:
        print(4)
    else:
        if a == b:
            print(5)
        else:
            print(6)
    print(7)
print(8)
