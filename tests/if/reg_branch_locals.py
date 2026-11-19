# Each branch has its own short-lived variables, which can share registers
# with the other branch's.
x = input_int()
if x < 0:
    p = x + 1
    q = p + 2
    r = q + 3
    print(r)
else:
    s = x - 1
    t = s - 2
    u = t - 3
    print(u)
