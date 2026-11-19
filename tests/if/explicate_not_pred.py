# not in the condition: explicate_pred swaps the branches.
x = input_int()
if not (x < 5):
    print(1)
else:
    print(2)
if not not (x < 5):
    print(3)
else:
    print(4)
