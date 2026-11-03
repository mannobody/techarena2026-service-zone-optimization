# Geometry lab: preregistration

Baseline: exact frozen server v4, SHA256 5b3914fa9791cb879f3232fb2876a915de83b848ad4b353b0dbf25b574998c25. Research starts 2026-10-19. No shared solver edits. NT2/O3 full runs, NT1 checkpoint operators; CPU0..7 exclusively. Every full comparison uses identical time, independent fresh generation seeds and several solver seeds. A valid checkpoint after nonzero rc/TLE is failure.

Development inputs seeds 711000 + 100*j for classes anti, cluster, tightA, alphabig, multiskill, large. Holdout seeds 721000 + 100*j are reserved until candidate freeze. Solver seeds 711,712; long diagnostic seed713. Initial mature checkpoints TL280 seed711. Conditional operator comparisons do not imply equal-budget full solver superiority.

Hypotheses, fixed before inspecting generated solutions:
1. Profitable inaccessible sites identify a few blocking hull support vertices; targeted ejection can beat random spatial ruin. Remove all assigned sites on the offending side of a separator through the target, recreate jointly, accept only verified true improvement.
2. Pairwise separators miss coordinated three-zone moves. Rebuild three neighboring territories through randomized power diagrams, keep other zones fixed, use original Engine and DP to restore constraints.
3. Existing resplit only admits free sites whose cheapest open road office belongs to the pair. This exclusion is particularly wrong under road/geometry anticorrelation. Admit all free sites with positive pair gain and test neighboring-pair scheduling.
4. Existing resplit optimizes capacities but does not optimize equal counts during its sweep. At A=0 it usually never proposes feasible boundaries. Add count-window-aware TopSum capacities per pair; preserve actual counts initially to isolate geometry.
5. Convex support peeling must free multiple layers, not one site. Remove one or two complete hull layers of two/three neighboring zones and jointly recreate, compared with the same number of random removed sites.
6. Long mature solutions may remain trapped in office topology. Restricted SCIP/HiGHS repair over whole neighboring zones (not safe envelopes) can reveal profitable moves and geometric obstructions beyond pairwise resplit.
7. An insertion can cause connected blocking-zone chains. Score expanded-hull overlaps on all input points; analyze how many blocking zones and support sites are required before implementing wider chains.
8. Long TL600+ runs diagnose whether v4 gains more from pure time than new geometry neighborhoods; compare final hulls, active offices, assignments and load/count bottlenecks.

No new method is promoted on a small noisy average with material class regressions. Failed hypotheses, build/process mistakes, selection limitations and time overhead remain recorded.
