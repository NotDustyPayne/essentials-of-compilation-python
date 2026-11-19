# Comparisons of negative numbers.
x = input_int()
print((1 if x < -3 else 0) + (2 if -5 < x else 0) + (4 if x <= -5 else 0)
      + (8 if -(x) > 4 else 0))
