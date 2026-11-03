\ SCIP STATISTICS
\   Problem name     : model
\   Variables        : 8 (4 binary, 0 integer, 0 implicit integer, 4 continuous)
\   Constraints      : 17
Minimize
 Obj: +2 x1 -6 x2 -1 x3 -4 x4 +0.1 x5 -0.1 x6
Subject to
 c1: +1 x2 <= +1
 c2: +1 x3 <= +1
 c3: +1 x4 <= +1
 c4: +1 x2 <= +0
 c5: +1 x2 <= +0
 c6: +1 x3 <= +0
 c7: +1 x3 <= +0
 c8: +1 x4 <= +0
 c9: +1 x2 +1 x3 +1 x4 -2 x1 <= +0
 c10: +1 x2 +1 x3 +1 x4 -1 x1 >= +0
 c11: +1 x2 +1 x3 +1 x4 -1 x7 <= +0
 c12: -1 x2 -1 x3 -1 x4 +1 x8 +3 x1 <= +3
 c13: +2 x2 +3 x3 +1 x4 -1 x5 <= +0
 c14: -2 x2 -3 x3 -1 x4 +1 x6 +6 x1 <= +6
 c15: +1 x6 -1 x5 <= +0
 c16: +1 x8 -1 x7 <= +0
 c17: +1 x7 -1 x8 <= +3
Bounds
 0 <= x1 <= 1
 0 <= x2 <= 1
 0 <= x3 <= 1
 0 <= x4 <= 1
 0 <= x5 <= 6
 0 <= x6 <= 6
 0 <= x7 <= 3
 0 <= x8 <= 3
Binaries
 x1 x2 x3 x4
End
