# b is used only in the "then" branch, which is the target of the
# conditional jump. Liveness must union the jump target's live-before set
# (section 5.9.1); otherwise b looks dead after it is read and c can be
# given the same register.
a = input_int()
b = input_int()
c = a + 10
if c < 5:
    print(b)
else:
    print(c)
