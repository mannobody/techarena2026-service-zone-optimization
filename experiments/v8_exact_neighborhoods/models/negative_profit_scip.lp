\ SCIP STATISTICS
\   Problem name     : model
\   Variables        : 10 (6 binary, 0 integer, 0 implicit integer, 4 continuous)
\   Constraints      : 23
Minimize
 Obj: +1 x1 +1 x2 +1000 x3 +5 x4 +10 x7 -10 x8
Subject to
 c1: +1 x3 +1 x4 <= +1
 c2: +1 x5 +1 x6 <= +2
 c3: +1 x5 -1 x1 <= +0
 c4: +1 x6 -1 x2 <= +0
 c5: +1 x5 >= +1
 c6: +1 x3 -1 x5 <= +0
 c7: +1 x6 >= +1
 c8: +1 x4 -1 x6 <= +0
 c9: +1 x3 -10 x1 <= -1
 c10: +1 x3 -1 x1 >= -1
 c11: +1 x3 -1 x9 <= -1
 c12: -1 x3 +1 x10 +3 x1 <= +4
 c13: +9 x3 -1 x7 <= -10
 c14: -9 x3 +1 x8 +20 x1 <= +30
 c15: +1 x4 -10 x2 <= -1
 c16: +1 x4 -1 x2 >= -1
 c17: +1 x4 -1 x9 <= -1
 c18: -1 x4 +1 x10 +3 x2 <= +4
 c19: +9 x4 -1 x7 <= -1
 c20: -9 x4 +1 x8 +20 x2 <= +21
 c21: +1 x8 -1 x7 <= +0
 c22: +1 x10 -1 x9 <= +0
 c23: +1 x9 -1 x10 <= +1
Bounds
 1 <= x1 <= 1
 1 <= x2 <= 1
 0 <= x3 <= 1
 0 <= x4 <= 1
 0 <= x5 <= 1
 0 <= x6 <= 1
 0 <= x7 <= 20
 0 <= x8 <= 20
 0 <= x9 <= 3
 0 <= x10 <= 3
Binaries
 x1 x2 x3 x4 x5 x6
End
