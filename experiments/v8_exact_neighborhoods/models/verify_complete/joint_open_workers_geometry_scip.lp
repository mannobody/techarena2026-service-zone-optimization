\ SCIP STATISTICS
\   Problem name     : model
\   Variables        : 14 (10 binary, 0 integer, 0 implicit integer, 4 continuous)
\   Constraints      : 29
Minimize
 Obj: +3 x1 +3 x2 -10 x3 -10 x4 -1 x5 -1 x6
Subject to
 c1: +1 x3 <= +1
 c2: +1 x4 <= +1
 c3: +1 x5 <= +1
 c4: +1 x6 <= +1
 c5: +1 x7 +1 x9 <= +1
 c6: +1 x8 +1 x10 <= +1
 c7: +1 x7 -1 x1 <= +0
 c8: +1 x8 -1 x1 <= +0
 c9: +1 x9 -1 x2 <= +0
 c10: +1 x10 -1 x2 <= +0
 c11: +1 x3 -1 x7 <= +0
 c12: +1 x4 -1 x7 <= +0
 c13: +1 x5 -1 x7 -1 x8 <= +0
 c14: +1 x6 -1 x7 -1 x8 <= +0
 c15: +1 x3 +1 x4 +1 x5 +1 x6 -10 x1 <= +0
 c16: +1 x3 +1 x4 +1 x5 +1 x6 -1 x1 >= +0
 c17: +1 x3 +1 x4 +1 x5 +1 x6 -1 x13 <= +0
 c18: -1 x3 -1 x4 -1 x5 -1 x6 +1 x14 +4 x1 <= +4
 c19: +1 x3 +1 x4 +1 x5 +1 x6 -1 x11 <= +0
 c20: -1 x3 -1 x4 -1 x5 -1 x6 +1 x12 +4 x1 <= +4
 c21: -10 x2 <= +0
 c22: -1 x2 >= +0
 c23: -1 x13 <= +0
 c24: +1 x14 +4 x2 <= +4
 c25: -1 x11 <= +0
 c26: +1 x12 +4 x2 <= +4
 c27: +1 x12 -1 x11 <= +0
 c28: +1 x14 -1 x13 <= +0
 c29: +1 x13 -1 x14 <= +0
Bounds
 1 <= x1 <= 1
 0 <= x2 <= 0
 0 <= x3 <= 1
 0 <= x4 <= 1
 0 <= x5 <= 1
 0 <= x6 <= 1
 0 <= x7 <= 1
 0 <= x8 <= 1
 0 <= x9 <= 1
 0 <= x10 <= 1
 0 <= x11 <= 4
 0 <= x12 <= 4
 0 <= x13 <= 4
 0 <= x14 <= 4
Binaries
 x1 x2 x3 x4 x5 x6 x7 x8 x9 x10
End
