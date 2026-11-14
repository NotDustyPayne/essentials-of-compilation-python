# Section 4.2 / figure 4.3: the first value written to b is never read, so
# a and b are never live at the same time.
a = 5
b = 30
c = a
b = 10
c = c + b
print(c)
