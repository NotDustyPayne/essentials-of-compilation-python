# 13 values read with input_int. Each one is live during the later calls to
# read_int, so all of them are call-live: only the 4 callee-saved registers
# (rbx, r12, r13, r14) are safe, and the rest must be spilled.
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
print(a - b + c - d + e - f + g - h + i - j + k - l + m)
