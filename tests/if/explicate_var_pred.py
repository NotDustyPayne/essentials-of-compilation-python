# A Boolean variable as the condition. CIf needs a comparison there, so
# it becomes something like `if b == False` with the branches swapped.
x = input_int()
b = x < 3
if b:
    print(1)
else:
    print(2)
c = not b
print(10 if c else 20)
