# var = -var and var = -other. Printed separately: a broken `x = -x`
# would still make x + y come out 0, so a sum would hide the bug.
x = 5
x = -x
y = -x
print(x)
print(y)
