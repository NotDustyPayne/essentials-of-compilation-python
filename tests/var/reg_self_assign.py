# `x = x` becomes `movq x, x`: a trivial move that patch_instructions
# should delete once x has a home (section 4.5).
x = 5
x = x
y = x
print(y)
