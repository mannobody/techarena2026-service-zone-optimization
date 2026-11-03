# Geometry lab — exact frozen server v4

Completed research pass; no commits, push, submission or deletion. All writes are inside this lab. The comparator is `../shared/v4`, built from frozen server source SHA256 `5b3914fa9791cb879f3232fb2876a915de83b848ad4b353b0dbf25b574998c25`. The previous study compared merged v4, so its numbers are not substituted here.

## Hypotheses and implementation

`IDEAS.md` preregisters eight distinct structural directions and fresh generation seeds711000+. Source patch `candidate.patch` modifies only resplit of frozen v4; existing global feasibility/geometry/worker checks remain. Every new feature defaults off.

`GEO_SPLIT` bitmask:
- 1: cap each changed zone by min(nonempty unchanged zone count)+A. This is a necessary bound.
- 2: allow profitable free sites regardless of their cheapest road office, except points already covered by an unchanged third hull. Selection is heuristic: positive real profit is required for these free sites, so negative-cost support sites remain outside this expanded pool.
- 4: additionally cap each zone by the attainable count of its counterpart+A. The other attainable count includes its actual capacity and the bound from unchanged offices.
- 5 combines the cardinality bounds;7 combines them with the wider pool.

The old sweep takes each side's best maxSize positive-effective-profit sites and then rejects count imbalance. It misses cuts that become feasible after dropping the worst surplus sites. New caps change proposal construction, not the final balance check. When alpha=0, skills/partition are fixed, all candidate gains are positive, and both offices remain nonempty, the maximal feasible count pair is optimal for this restricted cardinality subproblem. This does not prove full resplit optimality: directions, skill split, free pool and interactions with other hulls are limited.

An independent exhaustive count oracle (`count_oracle.py`) tested1,484 feasible random outside-count cases. A naive dynamic cap ignoring the other office's capacity missed76; corrected caps missed0. The pre-oracle source is retained. This is a mathematical count oracle, not a full geometry/worker oracle.

Offline structural operators (`src/structural.h`, never packaged) compare successive hull-layer peeling with equal-cardinality random removal, three-neighbor power-cell rebuilding, and target-driven half-plane ejection of sites covering blocking input points. All geometry uses all input points and the exact native Engine. These prototypes are bounded and heuristic; they make no completeness claim.

## Mature checkpoint findings

Fresh exact-v4 checkpoints ran280s, NT2, O3, seed711 on six classes. Initial operator comparisons used identical3s NT1 post budgets and seeds711/712; those timings are separate from full solver comparisons.

For anti, ordinary polish found0 while the broader free pool found994.887962 on both seeds (+0.38915%). The improvement changes66 site assignments across a geometric boundary; it is not a one-site tweak. Among100 highest-profit free insertions, all were blocked by geometry:46 by one zone,54 by two zones,11 included another office anchor.

For tightA, ordinary polish found0.70950, count bounds3.22459, free pool6.92869, both9.44378, all identical across two operator seeds. The top100 profitable insertions were94% geometrically unblocked; count/capacity/skills dominate this checkpoint. Both bounds improve a count-generating mechanism that was demonstrably incomplete, but full-budget evidence is still required.

For alphabig, the initial operators found no improvement. Four open zones all have228 tasks, making unbalanced changes expensive. Peeling, random ruin, and target ejection found0 in the initial three cases; triple rebuilding found0.85955 on tightA. These negative results are retained.

## Methodology and process records

The initial280s checkpoint runs used CPU pairs(0,1),(2,3),(4,5), which spread SMT siblings between slots. They are causal input snapshots, not paired throughput measurements. Full60 comparisons use whole(case,seed) blocks on identical CPU pairs(0,5),(1,2),(3,4), randomized variant order. Source, binary, input hashes, rc, actualNT, wall, RSS, timeout and official validator are saved. Failure/TLE with a valid checkpoint is still failure.

The first frozen-source build of structural operators incorrectly assumed merged-v4's deferred-removal API. Compilation failed before any benchmark; it was adapted to the actual frozen API. A first MIP diagnostic CLI also had an argument-unpacking error; stderr is retained. Neither is a submission runtime failure.

Older benchmark coordinators did not pin their Python validation thread; this can create brief cross-core validation work even when solver subprocess affinity is fixed. Updated post/MIP runners pin validation too. The full60 coordinator was already launched with the earlier shared runner; the limitation will be reported, and fresh holdout uses the corrected runner.

## Geometry-cut MILP: broad neighborhoods versus a known witness

Twenty-four fresh20s runs (six classes, whole nearest pair or triple plus nearby free sites, bothHiGHS/SCIP) all returned valid output within the23s wall allowance. None improved the incumbent. Some restricted models were proved optimal; several returned an optimal relaxation followed by geometry cuts and then exhausted time. A status string `optimal` alone is NOT a geometry-feasible optimality certificate; only `conditional_optimal=true` is.

A more informative experiment selected exactly the66 assignments changed by native resplit on anti and enabled every office alternative, removing the earlier top3/nearest filter. All unchanged assignments are identical in both endpoints, and every native assignment is represented. With a600s budget and original-v4 warm start, SCIP andHiGHS independently terminated after62.54/65.28s at the same conditional optimum256665.7084296862, gain1009.7249571538. Both needed21 solve/cut iterations and233 cuts, largest support4. Model:354 variables,566 rows before cuts.

Native resplit's gain994.8879619609 therefore captured98.53% of that selected-neighborhood gain in0.13s. This is a useful counterexample to assuming a longer generic MILP repair automatically beats a specialized boundary search. It is not a global optimality statement. At the same time, it confirms that the earlier20s MILP failure was not evidence of no useful geometry move.

The remaining14.836995 gain replaces one assigned3-task site with one free1-task site in the same office: real profit decreases16.907038 while imbalance penalty decreases31.744033. Counts stay140/125/129. This suggests composing geometric proposals with joint count/load selection. A20s diagnostic warm-started from the native endpoint only preserved it; neither backend proved optimality within that shorter budget.

Artifacts: `logs/long_mip/*.manifest.json`, `*.run.json`, `*.json`; every source/input/incumbent hash is recorded. Full geometry on all input sites and office points is enforced through cuts, without fixed safe envelopes. SCIP/HiGHS remain offline and are never packaged.

## Isolated final-stage implementation

`src/geometry_tail.h` duplicates the new proposal code under independent symbols `geom_resplit`, `geom_polish`, `geom_finish`. Original frozen-v4 search stays byte-for-byte unchanged when this header is inserted and the optional call is disabled. `GEOM_TAIL=7` requests count+pool,15 also negative support atA=0; default0. `GEOM_SECONDS` defaults1s and cannot exceed remaining wall budget. Extra absolute-deadline checks apply to each directional sweep and every128 cut positions. Parent integration owns placement relative to existing final boundary search, which can otherwise lose valuable time.

## Count reduction proof and negative support witness

Let `u_a=min(capacity_a, available_a, min_other+A)` and similarly`u_b`, omitting the last term when there are no unchanged nonempty offices. Set`a*=min(u_a,u_b+A)` and`b*=min(u_b,u_a+A)`. Every feasible pair count is componentwise at most this pair. If this pair meets the lower bound`max_other−A` and nonemptiness, it is feasible and dominates every other count pair. With only positive gains, the prefix objective increases with count, so this pair is optimal for the fixed separator/skills subproblem. The existing full range check enforces all lower/pairwise conditions. With nonzero alpha, TopSum's effective gains are a heuristic and this profit optimality claim does not apply.

For A=0 with at least one unchanged nonempty office, its countc forces both modified offices to exactlyc. Filtering out nonpositive gains is then wrong: low-profit support may enable a larger positive gain in the other zone. The optional padding bit8 keeps all eligible effective gains in TopSum for precisely this case. It still relies on the exact final objective and existing validity acceptance.

A new8-site,3-office,task-free,alpha0,A0 witness was independently exhaustively enumerated:65,536 assignments,375 valid, optimum135. Frozen-v4 polish improves60→130 by closing an office; padding improves60→135 while retaining that office with value5, including a negative-profit supporting site. Official validation confirms both. The instance, output, full enumeration code and hashes are in`inputs/padding_witness*`, `verify_padding.py`, `logs/padding_oracle.json`. This is a constructive mechanism proof. Padding added no extra gain on the six mature random checkpoints, so its practical value remains unproved.

The isolated final-stage header compiled successfully both standalone and in the parent's batch+geometry integration. Twenty-four1s checkpoint tests (two seeds, six classes, flags7/15) were all successful; they reproduced the earlier useful gains. The tighter absolute-deadline checks did not erase those gains. This does not settle competition with the existing boundary tail in a full equal-budget run.

## Reproduction

Run from repository root using its`.venv/bin/python` unless a MIP command explicitly uses`/tmp/szo-research-venv/bin/python`:

```
.venv/bin/python experiments/v4_deep_parallel/geometry/setup.py
.venv/bin/python experiments/v4_deep_parallel/geometry/build_candidates.py
g++ -O3 -std=c++17 -pthread experiments/v4_deep_parallel/geometry/src/candidate.cpp -o /tmp/geometry_candidate
.venv/bin/python experiments/v4_deep_parallel/shared/run_blocks.py experiments/v4_deep_parallel/geometry/FULL60_DEV.json
.venv/bin/python experiments/v4_deep_parallel/geometry/verify_padding.py
```

The run specification points to immutable recorded binaries; rebuilding another binary requires a new spec/destination and manifest. Existing output directories are intentionally not overwritten. `setup.py` documents the deterministic input generator and seeds; its generated inputs/hashes already exist, so regeneration is unnecessary for analysis. Use only the dedicated CPU slot allocation when reproducing concurrent runs.

For the long exact model, the corresponding command is`/tmp/szo-research-venv/bin/python experiments/v4_deep_parallel/geometry/long_mip.py highs 600 v4` (or`scip`). This includes full geometry cuts and all office alternatives on the66-site known witness. It is an offline research command reading a checkpoint, never submission code.

The header is integrated by including it after existing solver helpers and calling`geom_finish(I,limit)` only after worker threads join. Placement and budget compete with boundary search and require equal-TL validation. No library beyond the original C++17 standard/native dependencies is introduced.

## Equal-budget full60 outcome: reject global replacement

All48 runs completed successfully (six new classes×two solver seeds×v4/count/pool/both). Same CPU pair and randomized variant order were held for each complete(case,seed) block. Every output passed the official validator, rc/time checks and actualNT2 check.

| Global resplit variant | Mean paired delta | Median | Worst pair | W/T/L |
|---|---:|---:|---:|---|
| count(bit5) | −0.95292% | 0% | −7.37361% |3/4/5|
| pool(bit2) | −1.55750% | +0.00289% | −11.19118% |6/1/5|
| both(bit7) | −0.70396% | +0.00016% | −7.37361% |6/2/4|

Mean paired deltas by class:

|Class|count|pool|both|
|---|---:|---:|---:|
|anti|−0.01934%|+1.49324%|+1.49232%|
|tightA|−5.42964%|−9.28854%|−4.57520%|
|multiskill|+0.08130%|−1.29509%|−1.09570%|
|cluster|−0.37639%|−0.28996%|−0.04857%|
|large|0%|+0.00881%|+0.00338%|
|alphabig|+0.02655%|+0.02655%|0%|

The tightA regressions change the selected office set. For seed711, v4 ends with seven offices{0,1,2,3,4,5,6}, all counts16; all modified variants end with six offices missing0. For seed712, office sets also diverge, and the pool variant again has only six. This observes a different search trajectory; it does not establish whether timing, altered proposals, ranking or elite sharing is the sole cause. Warm-start diagnostics were nearly identical in seed711 (same3867 attempts,223 evaluated,3 decoded, objective5188.302506), so the difference appears after warm start. No case-specific branch was introduced to hide the failure.

The global candidate therefore fails the no-regression gate and is NOT recommended as a default. Its frozen source and all negative runs are retained. Reserved holdout generation seeds721000+ were not consumed to rescue a rejected global variant. Parent integration has separate untouched holdout seeds and tests the isolated tail with other components.

Exact frozen comparison files and full absolute objective/wall statistics are in`FULL60_DEV_SUMMARY.json` and`logs/full60_dev/MANIFEST.json`. Source of the originally used unpinned-validator runner is preserved under`src/run_blocks_unpinned.py`; its hash matches the run manifest exactly. Later diagnostic runs use the corrected pinned-validator shared runner.

## Real600s trajectory and final recommendation

An exact frozen-v4 diagnostic ran with TL600, NT2, seed713, same anti input, CPU6/7. It exited normally after598.864s and passed official validation. Snapshots at60,120,280,450s all had objective255426.087462765 and exactly the same assignments, offices{0,2,3}, counts140/125/129 and loads222/197/197. Debug output shows the main search still had that same incumbent at594.403s. The final native boundary search used4.399s and improved304.769504 to255730.856966455, changing10 assignments.

Starting from this full600s endpoint, ordinary polish with a1s budget found0; the isolated geometric operator found another939.2866453426 in0.118s, yielding256670.1436117976. Both operator seeds and flags7/15 agree. All six final checkpoint tests passed. This demonstrates a persistent proposal barrier, not merely lack of running time, on this particular instance. It remains a single development case, not a universal complexity/performance claim. Within-run snapshots are not an equal-budget280-versus600 algorithm comparison because phase budgets and final polishing differ with TL.

`ANYTIME600.json` contains validated snapshots and assignment-change counts; `logs/v4_anti600` retains full timings and traces. The1s experiments are under`logs/mature600_tail`.

**Recommended integration:** retain original search trajectory, add the independent monotone geometric tail under a flag, and test its ordering/budget together with the parent's joint count/load DP and search_lab's batch hull maintenance. In a combined build, the new `geom_resplit` remove loop can use the same deferred batch API as original resplit; standalone frozen-v4 lacks that API, so the delivered header intentionally does not call it. Validate the composed transaction/deadline behavior again.

**Do not integrate as defaults:** global GEO_SPLIT replacement (fails full60 regression gate), the tested standalone peeling/random/triple/ejection prototypes (no material broad gain), or an external MIP dependency. SCIP/HiGHS are useful research oracles here, not yet cost-effective submission operators. Negative padding has an exact witness but no incremental gain in the random mature tests, so keep it separately switchable.

Completed evidence in this lab:55 full native runs (6×280s,48×60s,1×600s),186 successful checkpoint operator runs,2 explicit native padding-witness runs,24 short structural MIP runs and4 known-witness MIP runs,1,484 independent count-oracle cases,65,536 exhaustively enumerated padding-witness assignments. This counts experiments, not independent test instances. No failures are hidden: early compile/CLI mistakes and the76 naive-cap oracle misses remain saved.

Reserved721000+ holdout seeds were not generated in this lab; search_lab independently used that range, so it must not later be described as globally unseen. Parent-owned final holdout751000+ remains the separate integration check. No overall improvement claim is made before that evaluation.
