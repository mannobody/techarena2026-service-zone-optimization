\ SCIP STATISTICS
\   Problem name     : model
\   Variables        : 8 (4 binary, 0 integer, 0 implicit integer, 4 continuous)
\   Constraints      : 14
Minimize
 Obj: +2 x1 -10 x2 -10 x3 +0.1 x5 -0.1 x6
Subject to
 c1: +1 x2 <= +1
 c2: +1 x3 <= +1
 c3: +1 x4 <= +1
 c4: +1 x4 -1 x1 <= +0
 c5: +1 x3 <= +0
 c6: +1 x2 +1 x3 <= +0
 c7: +1 x2 +1 x3 -1 x1 >= +0
 c8: +1 x2 +1 x3 -1 x7 <= +0
 c9: -1 x2 -1 x3 +1 x8 +2 x1 <= +2
 c10: +1 x3 -1 x5 <= +0
 c11: -1 x3 +1 x6 +1 x1 <= +1
 c12: +1 x6 -1 x5 <= +0
 c13: +1 x8 -1 x7 <= +0
 c14: +1 x7 -1 x8 <= +0
Bounds
 0 <= x1 <= 1
 0 <= x2 <= 1
 0 <= x3 <= 1
 0 <= x4 <= 1
 0 <= x5 <= 1
 0 <= x6 <= 1
 0 <= x7 <= 2
 0 <= x8 <= 2
Binaries
 x1 x2 x3 x4
End
