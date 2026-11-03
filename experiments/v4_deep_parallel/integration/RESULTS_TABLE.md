# Frozen hybrid versus exact server v4

All percentages are descriptive paired objective changes. These are not hidden-test scores.
Each pair uses identical CPU affinity, NT=2, and the same total time budget.

| Series | Successful runs | Pairs | Mean Δ% | Median Δ% | Worst Δ% | Best Δ% | SD Δ% | W/T/L |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| holdout60 | 72/72 | 36 | +0.133173 | +0.000000 | -1.579876 | +4.422545 | +1.032970 | 14/12/10 |
| holdout280 | 12/12 | 6 | -0.176472 | +0.068371 | -2.000740 | +0.798845 | +1.029588 | 3/0/3 |
| development280 | 24/24 | 12 | +0.889617 | +0.029748 | -0.960960 | +4.910095 | +1.938187 | 6/4/2 |
| open60 | 20/20 | 10 | -0.087969 | +0.000000 | -4.519009 | +3.639317 | +1.931858 | 1/8/1 |

## Runtime and process status

| Series | Variant | Max wall (s) | Median wall (s) | Peak RSS (MiB) | RE / timeout / invalid / wrong NT / wall / error log |
|---|---|---:|---:|---:|---|
| holdout60 | v4 | 60.423 | 59.809 | 25.62 | 0/0/0/0/0/0 |
| holdout60 | hybrid | 60.015 | 59.817 | 25.65 | 0/0/0/0/0/0 |
| holdout280 | v4 | 279.582 | 279.532 | 28.00 | 0/0/0/0/0/0 |
| holdout280 | hybrid | 279.545 | 279.498 | 28.02 | 0/0/0/0/0/0 |
| development280 | v4 | 279.548 | 279.501 | 28.00 | 0/0/0/0/0/0 |
| development280 | hybrid | 279.543 | 279.494 | 27.66 | 0/0/0/0/0/0 |
| open60 | v4 | 59.860 | 59.811 | 26.02 | 0/0/0/0/0/0 |
| open60 | hybrid | 59.874 | 59.824 | 27.26 | 0/0/0/0/0/0 |

## holdout60: per-instance results

| Class | Seeds | Baseline median | Candidate median | Ratio of medians Δ% | Mean paired Δ% | Worst paired Δ% |
|---|---:|---:|---:|---:|---:|---:|
| alphabig | 3 | 14606287.812399 | 14536658.907962 | -0.476705 | -0.437265 | -0.748362 |
| alphazero | 3 | 31310.193577 | 31320.093502 | +0.031619 | -0.418925 | -1.579876 |
| anti | 3 | 62584.668420 | 62590.865848 | +0.009902 | +0.779090 | +0.009902 |
| cluster | 3 | 410182.103117 | 416735.916207 | +1.597781 | +2.134297 | +0.426963 |
| deficit | 3 | 36.034422 | 36.034422 | +0.000000 | +0.000000 | +0.000000 |
| grid | 3 | 115325.522081 | 115325.522081 | +0.000000 | +0.000000 | +0.000000 |
| huge | 3 | 5374.195998 | 5374.472272 | +0.005141 | +0.054946 | +0.000000 |
| large | 3 | 702.227300 | 699.469372 | -0.392740 | -0.301295 | -0.580963 |
| medium | 3 | 593442.819843 | 593442.819843 | +0.000000 | +0.077320 | +0.000000 |
| multiskill | 3 | 57.379399 | 56.712918 | -1.161532 | -0.961681 | -1.496720 |
| small | 3 | 60108.025301 | 60108.025301 | +0.000000 | +0.000000 | +0.000000 |
| tightA | 3 | 17124.707356 | 17279.288485 | +0.902679 | +0.671587 | -0.104046 |

Percent mean uses 36/36 nonzero-reference pairs.

## holdout280: per-instance results

| Class | Seeds | Baseline median | Candidate median | Ratio of medians Δ% | Mean paired Δ% | Worst paired Δ% |
|---|---:|---:|---:|---:|---:|---:|
| alphabig | 1 | 14891978.520511 | 15010942.359398 | +0.798845 | +0.798845 | +0.798845 |
| anti | 1 | 80539.441810 | 80662.108553 | +0.152306 | +0.152306 | +0.152306 |
| huge | 1 | 5238.933134 | 5205.501207 | -0.638144 | -0.638144 | -0.638144 |
| large | 1 | 753.010873 | 757.863771 | +0.644466 | +0.644466 | +0.644466 |
| multiskill | 1 | 57.870762 | 56.712918 | -2.000740 | -2.000740 | -2.000740 |
| tightA | 1 | 17953.785409 | 17950.991054 | -0.015564 | -0.015564 | -0.015564 |

Percent mean uses 6/6 nonzero-reference pairs.

## development280: per-instance results

| Class | Seeds | Baseline median | Candidate median | Ratio of medians Δ% | Mean paired Δ% | Worst paired Δ% |
|---|---:|---:|---:|---:|---:|---:|
| alphabig | 2 | 4971789.004555 | 4984814.671664 | +0.261992 | +0.261944 | -0.138926 |
| anti | 2 | 245574.494407 | 257618.587967 | +4.904456 | +4.904457 | +4.898818 |
| huge | 2 | 7802.410957 | 7807.080901 | +0.059853 | +0.093301 | -0.960960 |
| large | 2 | 3256515.380005 | 3259054.968276 | +0.077985 | +0.078001 | +0.059496 |
| multiskill | 2 | 68512.710124 | 68512.710124 | +0.000000 | +0.000000 | +0.000000 |
| tightA | 2 | 23.075703 | 23.075703 | +0.000000 | +0.000000 | +0.000000 |

Percent mean uses 12/12 nonzero-reference pairs.

## open60: per-instance results

| Class | Seeds | Baseline median | Candidate median | Ratio of medians Δ% | Mean paired Δ% | Worst paired Δ% |
|---|---:|---:|---:|---:|---:|---:|
| inst0 | 2 | 5164995.266685 | 5164995.266685 | +0.000000 | +0.000000 | +0.000000 |
| inst1 | 2 | 32.229957 | 32.229957 | +0.000000 | +0.000000 | +0.000000 |
| inst2 | 2 | 5.626352 | 5.626352 | +0.000000 | +0.000000 | +0.000000 |
| inst3 | 2 | 136605.743050 | 136605.743050 | +0.000000 | +0.000000 | +0.000000 |
| inst4 | 2 | 18559.214551 | 18464.003793 | -0.513011 | -0.439846 | -4.519009 |

Percent mean uses 10/10 nonzero-reference pairs.

## Interpretation limits

The primary holdout contains 12 fresh generated instances with three solver seeds each,
not 36 independent instances. The TL280 confirmation reuses six of those fresh instances
with a new solver seed. Development TL280 uses six earlier development instances and
two new solver seeds. Open examples are compatibility checks, not tuning inputs.
Source and binary were frozen before holdout generation and were not changed afterward.
CPU type is controlled within pairs; full-machine frequency/power effects remain.

## Supplemental inst4 variance check (six seeds)

The four additional seeds completed8/8 successfully, giving12/12 successful
processes across six seeds on this one known open instance. Mean paired change
+0.712537%, paired median+0.544035%, ratio of objective
medians+0.178612%, SD3.188839%,
W/T/L4/0/2. Range-4.519009% to+4.409634%.
This confirms substantial variability, not a robust regression fix. The extra
seeds were registered after the first two outcomes; they are a supplemental
variance diagnostic, not another independent holdout. Source/defaults remain
unchanged. The original128 main-series rows and these8 follow-up rows are
reported separately. Raw pairs: `INST4_POOLED6.json`.

The pooled inst4 spread includes different CPU pairs and timing conditions as
well as solver seeds; it is not a pure estimate of seed variance. Hardware is
matched within each A/B pair.
