# 14 values live across an if: some must be spilled, and the comparisons
# on spilled values need patching (two memory operands).
a = input_int()
b = input_int()
c = input_int()
d = input_int()
e = input_int()
f = input_int()
g = input_int()
h = input_int()
i = input_int()
j = input_int()
k = input_int()
l = input_int()
m = input_int()
n = input_int()
if a < n:
    print(a + b + c + d + e + f + g + h + i + j + k + l + m + n)
else:
    print(a - b - c - d - e - f - g - h - i - j - k - l - m - n)
print(1 if m == l else 0)
