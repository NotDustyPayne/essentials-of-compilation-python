# x is live during the first call to print_int, so it must survive the call.
x = 7
print(x)
print(- x)
