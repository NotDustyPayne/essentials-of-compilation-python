# 20 short-lived variables, each dead right after the next is computed.
# They can all share one or two registers.
s0 = 1
s1 = s0 + 1
s2 = s1 + 2
s3 = s2 + 3
s4 = s3 + 4
s5 = s4 + 5
s6 = s5 + 6
s7 = s6 + 7
s8 = s7 + 8
s9 = s8 + 9
s10 = s9 + 10
s11 = s10 + 11
s12 = s11 + 12
s13 = s12 + 13
s14 = s13 + 14
s15 = s14 + 15
s16 = s15 + 16
s17 = s16 + 17
s18 = s17 + 18
s19 = s18 + 19
print(s19)
