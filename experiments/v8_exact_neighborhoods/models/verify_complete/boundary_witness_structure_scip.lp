\ SCIP STATISTICS
\   Problem name     : model
\   Variables        : 14 (10 binary, 0 integer, 0 implicit integer, 4 continuous)
\   Constraints      : 27
Minimize
 Obj: +1 x1 +1 x2 -10 x3 +20 x4 +20 x5 -10 x6 +20 x7 +20 x8
Subject to
 c1: +1 x3 +1 x4 <= +1
 c2: +1 x5 +1 x6 <= +1
 c3: +1 x7 +1 x8 <= +1
 c4: +1 x9 +1 x10 <= +2
 c5: +1 x9 -1 x1 <= +0
 c6: +1 x10 -1 x2 <= +0
 c7: +1 x3 -1 x9 <= +0
 c8: +1 x5 -1 x9 <= +0
 c9: +1 x7 -1 x9 <= +0
 c10: +1 x4 -1 x10 <= +0
 c11: +1 x6 -1 x10 <= +0
 c12: +1 x8 -1 x10 <= +0
 c13: +1 x3 +1 x5 +1 x7 -10 x1 <= +0
 c14: +1 x3 +1 x5 +1 x7 -1 x1 >= +0
 c15: +1 x3 +1 x5 +1 x7 -1 x13 <= +0
 c16: -1 x3 -1 x5 -1 x7 +1 x14 +3 x1 <= +3
 c17: +1 x3 +1 x5 +1 x7 -1 x11 <= +0
 c18: -1 x3 -1 x5 -1 x7 +1 x12 +3 x1 <= +3
 c19: +1 x4 +1 x6 +1 x8 -10 x2 <= +0
 c20: +1 x4 +1 x6 +1 x8 -1 x2 >= +0
 c21: +1 x4 +1 x6 +1 x8 -1 x13 <= +0
 c22: -1 x4 -1 x6 -1 x8 +1 x14 +3 x2 <= +3
 c23: +1 x4 +1 x6 +1 x8 -1 x11 <= +0
 c24: -1 x4 -1 x6 -1 x8 +1 x12 +3 x2 <= +3
 c25: +1 x12 -1 x11 <= +0
 c26: +1 x14 -1 x13 <= +0
 c27: +1 x13 -1 x14 <= +10
Bounds
 0 <= x1 <= 1
 0 <= x2 <= 1
 0 <= x3 <= 1
 0 <= x4 <= 1
 0 <= x5 <= 1
 0 <= x6 <= 1
 0 <= x7 <= 1
 0 <= x8 <= 1
 0 <= x9 <= 1
 0 <= x10 <= 1
 0 <= x11 <= 3
 0 <= x12 <= 3
 0 <= x13 <= 3
 0 <= x14 <= 3
Binaries
 x1 x2 x3 x4 x5 x6 x7 x8 x9 x10
End
