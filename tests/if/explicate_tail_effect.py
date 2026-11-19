# Section 5.7's `42 if x == 0 else 777`, as a statement by itself:
# explicate_effect can drop both branches, since constants have no effects.
x = input_int()
42 if x == 0 else 777
print(x)
