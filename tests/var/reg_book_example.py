# The chapter's running example (figure 4.1). x and z can share a register,
# and so can several others (figure 4.6).
v = 1
w = 42
x = v + 7
y = x
z = x + w
print(z + (- y))
