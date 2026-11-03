# Search architecture laboratory — completed development study

This is a local investigation against **exact frozen server v4**, not merged main.
Baseline source SHA256:5b3914fa9791cb879f3232fb2876a915de83b848ad4b353b0dbf25b574998c25.
Baseline binary is shared/v4; every experiment manifest records its actual hash and all candidate/input hashes.
No commits, staging, push, deletion or submission are part of this work.

## Implemented hypotheses

`IDEAS.md` preregisters the generator family, seeds, tests and hypotheses. All experimental sources derive from frozen_v4.cpp. `build_source.py` and `build_source2.py` reproduce them. All switches in lab/lab2 default off:

- LAB_BATCH: defer hull/coverage reconstruction across removal phases and journal rollback; batch office closure. Exact predicates unchanged.
- LAB_ALNS: operator credit per second with half baseline probability; ported independently from merged implementation.
- LAB_ARCHIVE: maintain best feasible trajectory per constructor candidate origin between ordinary full-length chunks; no particle cloning and no shorter chunks.
- LAB_WIDE: separate constructor-start counter from elite continuation rounds, include ranks beyond six without shortening0.12TL chunks.
- LAB_MEMO: bounded per-thread successful worker certificates keyed by complete demand/activity string; failures not cached.
- LAB_NICHES: verified elite archive up to12 states with at most2 states per office mask; occasional uniform niche sampling instead of exclusively geometrically biased top-score choice.
- LAB_XOVER: transplant1–3 neighboring verified elite zones, clear incompatible sites/anchors, then add through exact Engine checks. Disabled under GEO_EXACT=0.

The phase2 combinations distinguish batch alone, batch+ALNS, batch+ALNS+niche+crossover, and that combination plus persistent trajectories. These components are not automatically recommended together. XOVER and niche policy still require separate ablation if their combination remains promising.

## Correctness and independent kernel measurements

`CORRECTNESS.md` gives the deferred-state and certificate arguments. `src/test_batch.cpp` passed24000 differential transactions and96000 full state checks. It compares the same operations with batching disabled/enabled, including all input-point coverage and rollback. It uses duplicates, collinearity,A=0 and multiple worker profiles.

Fixed-work tests use the same O3 binary, a fixed mature checkpoint,1000 identical remove32+undo transactions, and three alternating off/on repetitions on the same locked CPU14/15 pair. Final state is recomputed independently. Median kernel times:

| Workload | Original kernel | Batched kernel | Speedup |
|---|---:|---:|---:|
| anti721000 |0.653096s|0.181421s|3.60×|
| multiskill721300 |1.493647s|0.369380s|4.04×|

The second checkpoint was produced by the ALNS candidate; the benchmark compares kernels at the identical state and is not a comparison of solution quality. On this fixed successful multiskill demand,10000 repeated worker checks took median0.115580s uncached versus0.006460s cached (17.89×). This is a deliberately cache-friendly workload; it is not total solver speedup or an estimate of realistic hit rate.

A separate memo oracle uses one instance per process, varying assignment/demand states within that instance and checking every positive certificate independently. All80 processes /360000 certificate checks passed. Production also handles one instance per process. Logs:logs/memo_oracle.json and memo_oracle.summary.log.

A separate direct-close signature regression was identified during review: frozen Sol::close_office omits sig_open(o), so directclose/reopen diverge from fresh load_state's signature. The compiled regression reports0/0 matches without fix and1/1 after the single sig_open(o) correction. The coordinator applied the correction separately in modular solver/sol.h; all lab and frozen quality binaries remain unchanged. No practical invalid solution is claimed solely from this invariant violation.

## Experimental design and limitations

Development inputs use generator721000+100j for anti,alphabig,tightA,multiskill,grid,cluster,large,huge; tightA explicitly forcesA=0. Sizes are150,600,150,400,100,1500,3500,10000 sites respectively. INPUTS.json records all parameters and hashes. Holdout751000+ belongs to the coordinator and is not accessed by this lab.

Initial screen60:8 cases×2 seeds×6 variants=96 runs, TL60/NT2/O3. **Exploratory only:** individual tasks were randomized across CPU pairs before hardware audit found8/9 and10/11 are SMT siblings, whereas12/13 and14/15 are separate cores. This is a hardware confound; its percentages cannot establish a causal quality/speed improvement.

Phase2_block60:8 cases×one fresh solver seed1103×5 variants=40 runs. Every case/seed block stays on the same CPU pair, variant order randomized. CONTROL280:anti/large×seeds1201/1202×exactv4/lab2allflagsOFF/lab2batchON/lab2wideON=16 runs. The all-off control exposes code-layout and no-op overhead effects independently from enabled research mechanisms. These runs follow the screening automatically, without tuning on holdout.

Every run records return code, timeout, wall time, peak RSS, actual thread count and official validator result. Valid checkpoint plus nonzero return/TLE is failure. Wall quality guard isTL+3; subprocess kill atTL+10 is emergency protection, not the accepted runtime. Locks exclude other lab jobs/compilers from the same pair. Initial runners left Python validation threads with broad affinity; later runner revisions pin validation too. Their exact prior versions are retained as run_v1.py/run_blocked_v1.py. Full-machine frequency/power variation remains unisolated.

Small numerical gains need replication; the mean is not the judge's hidden-test score. Algorithmic accelerations can change basin selection under a time limit and therefore can worsen objective on a particular run despite exact equivalent state transitions. Huge atTL60 is especially sensitive to initialization budget.

## Basin observations (preliminary)

BASINS.json records final office masks, counts, task loads, required skill sets, objective decomposition, constructor-rank matches and LNS iteration counts. On anti721000, v4seed1101 reached54.0119 with7 offices, seed1102 reached64.3287 with8 offices; the final winning masks were absent from printed initial candidate ranks. Forseed1101 no initial candidate even contains the final active mask; forseed1102 the all10-office candidate is a superset, so contraction of that candidate is also possible. Without an origin trace, the latter cannot prove discovery of a previously inaccessible basin. This illustrates substantial stochastic basin variation.

On multiskill, typical initial-rank0 mask{0,2,4,6,7} yields9489.189. An exploratory wide-start run found mask{0,1,4,6,7}, already present at rank1, and9641.115. Thus access to a skipped strong start can matter even before rank>=6. This is a mechanism witness, not replicated quality superiority.

On anti v4seed1101, LNS incumbent51.7899 became52.9981 in finish and54.0119 in boundary tail (~0.322s). This motivated the coordinator's separate tail-budget investigation; this lab does not attribute it to a new search component.

## Reproduction and integration

Run specs with a new unique `name` to preserve immutable histories:

```
.venv/bin/python experiments/v4_deep_parallel/search/build_source.py
.venv/bin/python experiments/v4_deep_parallel/search/build_source2.py
.venv/bin/python experiments/v4_deep_parallel/search/run_blocked.py experiments/v4_deep_parallel/search/PHASE2_BLOCK60.json
.venv/bin/python experiments/v4_deep_parallel/search/metrics.py screen60 phase2_block60 control280
.venv/bin/python experiments/v4_deep_parallel/search/basins.py screen60 phase2_block60 control280
```

`batch.patch` and `src/batch_only.cpp` are a minimal integration component over frozen v4, with no experimental archive/memo/ALNS code or repeated environment checks. The quality series uses lab/lab2, not this stripped derivative; integrating it requires its own exact-v4 comparison. It composes with the geometry lab's resplit proposal changes: the only change inside resplit is begin/end around the removal loop. Other components are independently controlled and should be adopted only if final ablations and coordinator holdout support them.

Final distributions and decisions appear below. Machine-readable evidence: METRICS.json, CONTROL_COMPARISONS.json, EVIDENCE_AUDIT.json and per-run manifests.

## Completed blocked TL60 comparison

All40/40 runs returned successfully, validated, and met the runtime limit. Each row represents eight paired instances, one solver seed each, identical hardware within each pair. This is development screening, not the independent final holdout.

| Variant | Mean Δ% | Median Δ% | Worst Δ% | Best Δ% | SD Δ% | W/T/L |
|---|---:|---:|---:|---:|---:|---|
|batch|0.37467|0.03966|-0.26626|1.92588|0.70785|5/2/1|
|adaptive|-1.70421|0.00000|-7.79396|1.15588|2.83674|3/2/3|
|niche_cross|-0.82028|0.00023|-8.41731|1.15588|2.89575|4/3/1|
|persistent_cross|-2.60861|-0.03400|-20.08228|0.14997|6.60971|3/1/4|

Batch is the strongest development candidate from this lab. Large has−0.266% in this single-seed block, so it still does not satisfy a literal no-instance-regression gate. Adaptive operator selection and stronger archive/crossover combinations are not recommended from this series: anti loses7.79%,8.42%,20.08% respectively. The apparent positive niche_cross mean over the first five completed blocks reversed after anti; this is why partial means were not used for promotion. CROSS_ABLATION60.json remains a prepared but unexecuted follow-up, because the combined method failed the full screen.


Synthetic all-flags test completed28/28 successfully (TL5,NT2,O3), including empty inputs, missing workers/skills,maxSize0,A0, hugealpha, coincident/collinear points, multiskill and10k sites. The synthetic run is a safety check, not a quality ranking. Raw resource/validator records are in logs/synthetic_all5.

## Exact finite-zone recombination diagnostic

The two anti incumbents service78 and79 sites, yet only5 site→office assignments are common. There are39 shared sites assigned to different offices,34 sites used only by the first solution and35 only by the second. Their summed hull areas are0.518711 and0.633464; their hulls cover23 and24 unassigned sites. These are raw geometric measurements, not a bound on achievable objective or a claim that polygon intersections themselves are invalid.

`zone_pool_oracle.py` collects their15 complete zones and exhaustively enumerates feasible selections. A selection must have disjoint coverage on **all** input points (including free sites and closed office anchors), obey the global count range, task-load penalty and single-skill worker availability. Of56 inter-incumbent zone pairs,27 conflict geometrically. The oracle visits2720 search nodes and635 feasible packings; the conditional optimum is64.328740079648, exactly the stronger incumbent with all its8 zones. The official validator independently confirms the emitted solution.

Thus simply selecting intact zones from these two elites cannot improve the stronger basin. This is a finite-pool result, not a global optimum. It supports investigating coordinated reshaping/resizing when crossing basins; adding more elite slots or naive zone crossover alone does not resolve these conflicts. Raw details:ANTI_GEOMETRY.json andZONE_POOL.json.

CONTROL280 was extended before launch to include LAB_WIDE-only (source unchanged), after the exploratory screen revealed a concrete rank1-access witness. The original12-run spec is retained asCONTROL280_ORIGINAL.json; the final16-run spec includes the same-binary all-off control. No280 orholdout outcomes were observed before this extension.

## Completed exploratory TL60 screen (hardware-confounded)

All96/96 runs passed validation/return/runtime checks. Each candidate has16 case-seed pairs. These values are retained for completeness, **not causal quality evidence**: variants of a pair were not guaranteed the same CPU type.

| Variant | Mean Δ% | Median Δ% | Worst Δ% | Best Δ% | SD Δ% | W/T/L |
|---|---:|---:|---:|---:|---:|---|
|batch|-0.80724|0.01951|-14.48650|7.73404|4.30664|10/0/6|
|alns|-0.09216|0.00000|-14.41395|12.54408|5.06029|6/5/5|
|archive|-1.22297|0.00000|-20.51345|5.57162|5.43486|6/4/6|
|wide|1.11498|0.00877|-4.22053|16.22599|4.11523|8/3/5|
|memo|-1.28903|0.00628|-25.74392|3.20273|6.38943|8/4/4|

## Counter-only versus full-wide diagnostic

`counter.cpp` adds LAB_COUNTER independently from LAB_WIDE. LAB_COUNTER changes only the real-constructor-start counter and retains top6; LAB_WIDE also expands the rank list. Both preserve the original nominal chunk length. The same-binary TL30 pilot has6/6 valid runs and is a mechanism experiment, not an exact-v4 quality comparison.

| Seed | Instrumented trace-off | Counter-only top6 | Full-wide |
|---|---:|---:|---:|
|1301|9489.189006|9483.217463|9495.138581|
|1302|9641.008173|9489.189006|9496.087834|

Forseed1302, trace-off tid0 actually constructs ranks[3,4,5,2], skipping0 and1; the shadow real-start counter on the same observed elite schedule would select[0,1,2,3]. The independent tid1 constructs[0,1,2,3,4,5,0,1] under old/counter-only, but full-wide selects[0,1,2,3,4,5,6,7]. The two mechanisms are therefore distinct. Actual/shadow sequences are preserved inCOUNTER_TRACES.json.

Better nominal rank coverage did not imply higher objective in this pilot. In particular, the old schedule still had an independent tid1 covering rank1. Also, a constructor-only counter ignores effort already spent in the same office mask through elite continuations; counting only explicit starts may duplicate explored basins. That is a plausible policy-level explanation, not a demonstrated causal attribution of the observed score loss. No scheduler change is recommended from these short diagnostics alone.

## Scope ledger and interpretation of rejected hypotheses

| Hypothesis | Actual evidence | Disposition |
|---|---|---|
| Deferred exact geometry | Differential state oracle, fixed-work speedup, blocked TL60 and TL280 controls | Minimal candidate for coordinator integration |
| Adaptive move allocation | Independent exploratory variant; blocked batch+ALNS ablation | Reject current policy: quality loss, especially anti |
| Persistent trajectories | Independent exploratory variant; blocked archive on top of population combination | Reject current policy: strongest anti loss |
| Constructor coverage | Exploratory wide variant, same-binary counter/top6/full-wide trace, TL280 controls | Mechanism demonstrated; quality decision must use complete controls |
| Successful worker certificates | 360000 checks, favorable fixed-demand kernel, exploratory solver test | Correct under stated scope; realistic hit rate and wall-quality benefit unproven, keep off |
| Niche archive and zone crossover | Blocked combined test and exact finite-zone packing oracle | Reject current combination; separate niche/crossover ablation prepared but not executed |
| Long-run basin diagnosis | TL280 controls, short-run final geometry and rank traces | Observational evidence; no causal plateau claim from LNS message counts |
| Reheat from retained basin | Preregistered contingent follow-up only | Not implemented/tested after archive failed; no result claimed |

There is no evidence here that combining all the implemented mechanisms creates a stronger algorithm. Stronger exploration can spend the budget in worse basins, and a fixed office mask does not uniquely identify a geometric basin. The finite-zone oracle shows one concrete reason simple recombination fails: many high-value intact zones conflict. A future population method should carry compatible partial boundaries or optimize overlapping donor zones jointly, rather than infer usefulness from elite-count diversity alone. That is a research direction, not a tested improvement.

The signature regression is a correctness invariant repair and should be kept separate from claims of objective improvement. The batch kernel proof is exact-state equivalence, but wall-time search trajectories are intentionally not asserted equivalent. Memo certificates are independently verified for feasibility, not proved to improve search quality. No benchmark here measures the contest hidden-test distribution or establishes a server score gain.


## Completed blocked TL280 controls

All16/16 runs passed return-code, runtime, actualNT2 and official feasibility checks. Two classes × two solver seeds provide four blocks; this is a targeted development diagnostic, not a broad holdout or statistically precise estimate. All variants of each block ran on the same CPU pair. The same lab2 binary was used for off/batch/wide.

| Case | Seed | Exact v4 | Lab off | Batch | Wide | CPU pair |
|---|---:|---:|---:|---:|---:|---|
|anti|1201|48.114162|48.114162|48.114162|55.503448|[10, 11]|
|anti|1202|48.114162|56.021746|60.045162|65.956012|[8, 9]|
|large|1201|123205.246420|123485.716400|123498.793918|122741.108781|[14, 15]|
|large|1202|123419.780724|122829.898541|123749.117858|123338.980336|[12, 13]|

| Comparison | Mean Δ% | Median Δ% | Worst Δ% | Best Δ% | SD Δ% | W/T/L |
|---|---:|---:|---:|---:|---:|---|
|lab_off_vs_v4|4.04619|0.11382|-0.47795|16.43504|7.15724|2/1/1|
|batch_vs_v4|6.32559|0.25255|0.00000|24.79727|10.66513|3/1/0|
|wide_vs_v4|12.99949|7.64618|-0.37672|37.08232|15.29020|2/0/2|
|batch_vs_lab_off|1.98521|0.37948|0.00000|7.18188|3.01560|3/1/0|
|wide_vs_lab_off|8.22554|7.88614|-0.60299|17.73288|8.36981|3/0/1|

An all-off difference combines code layout, no-op bookkeeping/branches and stochastic wall-time scheduling. It does not identify which of these causes a particular objective shift. Comparisons with all-off isolate the enabled component more closely, but each remains a small stochastic sample. Percentage deltas divide by max(1, abs(control objective)); standard deviations are descriptive population SD over the listed blocks.

## Final integration recommendation and evidence limits

Keep the minimal deferred-geometry component as the only search-lab performance candidate for independent combined holdout. Its strongest evidence is the exact-state differential test and the fixed-work3.60–4.04× removal/rollback kernel speedup. This is not a guarantee of whole-solver speedup or per-instance objective improvement. The stripped batch_only source was not itself a quality-series binary; the coordinator must compare the exact integrated artifact against exact frozen v4. Keep the direct-close signature correction separate as an invariant repair.

Do not enable the current ALNS, persistent archive, niche/crossover or memo implementations in the final combination from this evidence. Wide scheduling remains a research candidate only: counter coverage and full-rank coverage are distinct, the counter-only pilot did not improve quality, and the long controls cover only two classes. No scheduler policy has passed an independent broad holdout in this lab. No parameter was selected using coordinator holdout751000+.

Across the five solver series, 186/186 runs have successful stored return/runtime/validator status (0 failures). The evidence audit confirms current binary/input hashes match manifests, row completeness and blocked pair consistency where applicable. Of186 runs,184 logged actualNT2; the synthetic empty-input and no-office cases exited before creating workers and have no thread-count log (NT2 was requested). These two trivial safety cases are not parallel-search quality evidence. It does not retroactively repair the initial screen's hardware confound. Correctness oracles and finite-zone enumeration are additional evidence, not extra full-solver quality runs.

Reproduce statistics with metrics.py, basins.py, control_analysis.py and verify_evidence.py. Compile sources using compile_locked.py SOURCE.cpp BINARY (O3, C++17, locked CPU14/15); do not run after releasing CPUs without coordinating ownership. Test sources include the immutable lab.cpp. Logs and all rejected candidates remain preserved. No commits, staging, push or submission were made.
