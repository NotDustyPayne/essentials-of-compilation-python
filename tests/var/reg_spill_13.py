# 13 variables live at the same time: more than the 11 registers, so at
# least two must be spilled to the stack. Powers of two, so any mix-up shows.
a = 1
b = 2
c = 4
d = 8
e = 16
f = 32
g = 64
h = 128
i = 256
j = 512
k = 1024
l = 2048
m = 4096
print(a + b + c + d + e + f + g + h + i + j + k + l + m)
