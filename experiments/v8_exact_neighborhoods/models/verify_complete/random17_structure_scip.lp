\ SCIP STATISTICS
\   Problem name     : model
\   Variables        : 12 (8 binary, 0 integer, 0 implicit integer, 4 continuous)
\   Constraints      : 24
Minimize
 Obj: +3 x1 +3 x2 +1 x3 -8 x4 -7 x5
Subject to
 c1: +1 x3 +1 x4 <= +1
 c2: +1 x5 +1 x6 <= +1
 c3: +1 x7 +1 x8 <= +1
 c4: +1 x7 -1 x1 <= +0
 c5: +1 x8 -1 x2 <= +0
 c6: +1 x3 <= +0
 c7: +1 x5 -1 x7 <= +0
 c8: +1 x4 <= +0
 c9: +1 x6 -1 x8 <= +0
 c10: +1 x3 +1 x5 -2 x1 <= +0
 c11: +1 x3 +1 x5 -1 x1 >= +0
 c12: +1 x3 +1 x5 -1 x11 <= +0
 c13: -1 x3 -1 x5 +1 x12 +2 x1 <= +2
 c14: +1 x3 +3 x5 -1 x9 <= +0
 c15: -1 x3 -3 x5 +1 x10 +4 x1 <= +4
 c16: +1 x4 +1 x6 -2 x2 <= +0
 c17: +1 x4 +1 x6 -1 x2 >= +0
 c18: +1 x4 +1 x6 -1 x11 <= +0
 c19: -1 x4 -1 x6 +1 x12 +2 x2 <= +2
 c20: +1 x4 +3 x6 -1 x9 <= +0
 c21: -1 x4 -3 x6 +1 x10 +4 x2 <= +4
 c22: +1 x10 -1 x9 <= +0
 c23: +1 x12 -1 x11 <= +0
 c24: +1 x11 -1 x12 <= +0
Bounds
 0 <= x1 <= 1
 0 <= x2 <= 1
 0 <= x3 <= 1
 0 <= x4 <= 1
 0 <= x5 <= 1
 0 <= x6 <= 1
 0 <= x7 <= 1
 0 <= x8 <= 1
 0 <= x9 <= 4
 0 <= x10 <= 4
 0 <= x11 <= 2
 0 <= x12 <= 2
Binaries
 x1 x2 x3 x4 x5 x6 x7 x8
End
