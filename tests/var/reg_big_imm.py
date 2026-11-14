# Big constants with many live variables: patch_instructions uses %r11 for
# the constant, so no variable may live in %r11.
a = 1
b = 2
c = 3
d = 4
e = 5
f = 6
g = 7
h = 8
i = 9
j = 10
k = 11
l = 12
x = a + 5000000000
print(x - 5000000000 + b + c + d + e + f + g + h + i + j + k + l)
