# Variables updated in place while the other is still live.
# a = 3, b = 5, a = -2. Output: -2 then 5, printed as "-25".
a = 1
b = 2
a = b + a
b = a + b
a = a - b
print(a)
print(b)
