\ SCIP STATISTICS
\   Problem name     : model
\   Variables        : 10 (6 binary, 0 integer, 0 implicit integer, 4 continuous)
\   Constraints      : 21
Minimize
 Obj: +6 x1 -6 x2 -5 x3 -7 x4 +1 x6 +100 x7 -100 x8
Subject to
 c1: +1 x2 <= +1
 c2: +1 x3 <= +1
 c3: +1 x4 <= +1
 c4: +1 x5 <= +1
 c5: +1 x6 <= +1
 c6: +1 x2 <= +0
 c7: +1 x3 <= +0
 c8: +1 x4 <= +0
 c9: +1 x4 <= +0
 c10: +1 x5 <= +0
 c11: +1 x5 <= +0
 c12: +1 x6 <= +0
 c13: +1 x2 +1 x3 +1 x4 +1 x5 +1 x6 -5 x1 <= +0
 c14: +1 x2 +1 x3 +1 x4 +1 x5 +1 x6 -1 x1 >= +0
 c15: +1 x2 +1 x3 +1 x4 +1 x5 +1 x6 -1 x9 <= +0
 c16: -1 x2 -1 x3 -1 x4 -1 x5 -1 x6 +1 x10 +5 x1 <= +5
 c17: +2 x2 +1 x3 +3 x4 +2 x5 +1 x6 -1 x7 <= +0
 c18: -2 x2 -1 x3 -3 x4 -2 x5 -1 x6 +1 x8 +9 x1 <= +9
 c19: +1 x8 -1 x7 <= +0
 c20: +1 x10 -1 x9 <= +0
 c21: +1 x9 -1 x10 <= +0
Bounds
 0 <= x1 <= 1
 0 <= x2 <= 1
 0 <= x3 <= 1
 0 <= x4 <= 1
 0 <= x5 <= 1
 0 <= x6 <= 1
 0 <= x7 <= 9
 0 <= x8 <= 9
 0 <= x9 <= 5
 0 <= x10 <= 5
Binaries
 x1 x2 x3 x4 x5 x6
End
