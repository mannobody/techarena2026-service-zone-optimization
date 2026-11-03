\ File written by HiGHS .lp file handler
min
 obj: +5 c0 -4 c1 +1 c2 -7 c3 +100 c6 -100 c7 
st
 r0: +1 c1 <= +1
 r1: +1 c2 <= +1
 r2: +1 c3 <= +1
 r3: +1 c4 <= +1
 r4: +1 c5 <= +1
 r5: -1 c0 +1 c4 <= +0
 r6: -1 c0 +1 c5 <= +0
 r7: +1 c1 -1 c4 -1 c5 <= +0
 r8: +1 c2 -1 c4 <= +0
 r9: +1 c3 -1 c4 -1 c5 <= +0
 r10: -1 c0 +1 c1 +1 c2 +1 c3 <= +0
 r11: -1 c0 +1 c1 +1 c2 +1 c3 >= +0
 r12: +1 c1 +1 c2 +1 c3 -1 c8 <= +0
 r13: +3 c0 -1 c1 -1 c2 -1 c3 +1 c9 <= +3
 r14: +1 c1 +1 c2 +1 c3 -1 c6 <= +0
 r15: +3 c0 -1 c1 -1 c2 -1 c3 +1 c7 <= +3
 r16: -1 c6 +1 c7 <= +0
 r17: -1 c8 +1 c9 <= +0
 r18: +1 c8 -1 c9 <= +0
bounds
 c0 <= 1
 c1 <= 1
 c2 <= 1
 c3 <= 1
 c4 <= 1
 c5 <= 1
 c6 <= 3
 c7 <= 3
 c8 <= 3
 c9 <= 3
bin
 c0
 c1
 c2
 c3
 c4
 c5
gen
semi
end
