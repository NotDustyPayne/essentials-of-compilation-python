# y = x makes x and y move-related, so that move adds no interference edge.
# But x is written again while y is still live, so they do interfere.
x = input_int()
y = x
x = x + 1
print(y - x)
