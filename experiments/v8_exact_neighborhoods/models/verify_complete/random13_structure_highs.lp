\ File written by HiGHS .lp file handler
min
 obj: +2 c0 -10 c1 -10 c2 +0.1 c4 -0.1 c5 
st
 r0: +1 c1 <= +1
 r1: +1 c2 <= +1
 r2: +1 c3 <= +1
 r3: -1 c0 +1 c3 <= +0
 r4: +1 c2 <= +0
 r5: +1 c1 +1 c2 <= +0
 r6: -1 c0 +1 c1 +1 c2 >= +0
 r7: +1 c1 +1 c2 -1 c6 <= +0
 r8: +2 c0 -1 c1 -1 c2 +1 c7 <= +2
 r9: +1 c2 -1 c4 <= +0
 r10: +1 c0 -1 c2 +1 c5 <= +1
 r11: -1 c4 +1 c5 <= +0
 r12: -1 c6 +1 c7 <= +0
 r13: +1 c6 -1 c7 <= +0
bounds
 c0 <= 1
 c1 <= 1
 c2 <= 1
 c3 <= 1
 c4 <= 1
 c5 <= 1
 c6 <= 2
 c7 <= 2
bin
 c0
 c1
 c2
 c3
gen
semi
end
