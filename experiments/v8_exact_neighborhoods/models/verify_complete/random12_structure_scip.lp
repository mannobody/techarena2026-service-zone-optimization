\ SCIP STATISTICS
\   Problem name     : model
\   Variables        : 12 (8 binary, 0 integer, 0 implicit integer, 4 continuous)
\   Constraints      : 20
Minimize
 Obj: +3 x1 +3 x2 -2 x3 -5 x4 -9 x5 -6 x6 -2 x7 +1 x8 +0.1 x9 -0.1 x10
Subject to
 c1: +1 x3 +1 x4 <= +1
 c2: +1 x5 +1 x6 <= +1
 c3: +1 x7 +1 x8 <= +1
 c4: +1 x5 <= +0
 c5: +1 x6 <= +0
 c6: +1 x3 +1 x5 +1 x7 -2 x1 <= +0
 c7: +1 x3 +1 x5 +1 x7 -1 x1 >= +0
 c8: +1 x3 +1 x5 +1 x7 -1 x11 <= +0
 c9: -1 x3 -1 x5 -1 x7 +1 x12 +3 x1 <= +3
 c10: +3 x5 -1 x9 <= +0
 c11: -3 x5 +1 x10 +3 x1 <= +3
 c12: +1 x4 +1 x6 +1 x8 -2 x2 <= +0
 c13: +1 x4 +1 x6 +1 x8 -1 x2 >= +0
 c14: +1 x4 +1 x6 +1 x8 -1 x11 <= +0
 c15: -1 x4 -1 x6 -1 x8 +1 x12 +3 x2 <= +3
 c16: +3 x6 -1 x9 <= +0
 c17: -3 x6 +1 x10 +3 x2 <= +3
 c18: +1 x10 -1 x9 <= +0
 c19: +1 x12 -1 x11 <= +0
 c20: +1 x11 -1 x12 <= +0
Bounds
 0 <= x1 <= 1
 0 <= x2 <= 1
 0 <= x3 <= 1
 0 <= x4 <= 1
 0 <= x5 <= 1
 0 <= x6 <= 1
 0 <= x7 <= 1
 0 <= x8 <= 1
 0 <= x9 <= 3
 0 <= x10 <= 3
 0 <= x11 <= 3
 0 <= x12 <= 3
Binaries
 x1 x2 x3 x4 x5 x6 x7 x8
End
