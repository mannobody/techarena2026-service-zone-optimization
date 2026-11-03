# Plateau escape: exact-v4 native LNS extension

Status: development experiments; no promotion, commit, merge, package or submission.
Exact baseline is SHA256
`5b3914fa9791cb879f3232fb2876a915de83b848ad4b353b0dbf25b574998c25`.
Only `experiments/v4_perturbation/escape_lab/` is written by this lab. All solver,
compiler, property-test and official-validation processes use CPU14/15 and NT2.

## Mechanism and relation to previous negative results

The previous full ILS replacement lost1.3523% on development, despite favorable
short postchecks; persistent archive/ALNS combinations also failed. This design
therefore retains all original LNS operators, cooling, scheduler and finalization.
`src/integration.patch` adds one controller, a periodic tick, five acceptance
hooks, DP-state synchronization and a local-best restoration before final polish.
`src/escape.h` is the complete optional component; `ESCAPE_MODE=0` by default.
The frozen quality source/binaries and every included source hash are recorded in
`FREEZE_SCREEN.json`. No runtime parameters are selected from a held-out input.

Three hypotheses are implemented separately:

1. A measured local-record plateau triggers small count-compatible removal,
   alternate-site refill excluding destroyed sites, then original LNS recovery.
   Refill considers negative count-support sites and native level-fill at A≤2.
   This prevents two prior failure modes: immediate replacement by the same
   destroyed sites and A=0 blocking every single-site addition.
2. Plateau-only late/threshold acceptance uses a64-slot true-objective history,
   retains the native guide-improving acceptance path inside the same loss cap,
   and adds no destructive proposal.
3. Plateau-only short tabu uses12 assignment/open-mask hashes with aspiration,
   adaptive removal strength1–4 and a4× reheating factor inside a bounded episode.
   It replaces neither the original move sampler nor the portfolio.

Mode4 is an essential best-retention-only control. It separates local-best memory,
verification and restoration from the perturbation itself. Mode0 takes exactly
original SA decisions and consumes the same RNG values for the same proposals;
wall-time/code-layout effects can still differ from the separately compiled v4.

Plateau is operationally defined as no fully verified thread-local objective
record for min(2s,max(.08s,.16×loop duration)); this is not a proof of local
optimality. Episodes nominally last min(.8s,max(.06s,.10×loop duration)). New
admissions stop after accumulated episode time exceeds30% of the loop duration.
An in-progress native move can overrun the nominal episode boundary, so30% is
not a strict measured CPU/wall cap. The outer original phase deadline remains.
Loss envelope=min(.75%×max(1,abs(entry incumbent)),2×native profit scale).

The current trajectory may worsen. A separate local best passes worker matching
and full native verify, and global output still uses original monotone offer.
The offline driver preserves the checkpoint's original worker certificate; an
exhausted reconstruction budget cannot replace it with an invalid/worse output.
This monotonicity relative to one's own initial checkpoint is not a claim of
non-regression relative to another timed solver trajectory.

## Design and accounting

`SCREEN60.json`: six fresh development inputs, exact-v4 TL60 checkpoints,
two continuation seeds, original v4 / all-off / retain-only / kick / late / tabu,
four seconds each, randomized within every paired block on CPU14/15. Budget
includes load/initialization and final output. `MATURE280.json` repeats on six
exact-v4 TL280 checkpoints with two fresh continuation seeds; cluster replaces
large because the shared mature set contains cluster. This is checkpoint-stage
evidence, not full TL60 or TL280 solver quality.

Every process must return0, pass the official validator, log actualNT2, avoid
error/timeout markers and finish within requested seconds+3. The emergency kill
is seconds+10. No failed or missing row is silently treated as a valid comparison.
The summarizer asserts exact key products and matching CPU affinity. Raw stderr,
resource reports, per-run JSON, input/checkpoint/binary/source hashes and COMPLETE
counts remain in each log directory. Percentages are relative to matched v4
continuation; the initial checkpoint is also retained for absolute gains.

`ESCAPE` records are per-thread local-controller observations. Summing their
objective gains does not give the published process gain, because two threads
can discover the same improvement. Plateau fraction is sampled at native time
checks (every64 iterations for small inputs, every iteration for large inputs),
so it is neither a uniform-time fraction nor directly comparable across classes.
Assignment, office, hull and worker counters compare episode endpoints; they do
not count all intermediate transitions. `same_max` means the endpoint equals
that thread's retained best assignment/open mask when the episode did not improve.

The quality log field `recovery_seconds` measures synchronous refill/repair
cost, not first passage back to the old objective. Separate diagnostic-only
sources (`escape_diagnostic.h`, `escape_diagnostic_v4.cpp`) measure the first
fully verified accepted state reaching the pre-episode best objective, retain
right-censored episode durations and distinguish changed/failed kicks.
They do not modify the frozen quality candidate. Diagnostic instrumentation
adds checks and therefore has its own source/binary manifest and run series.

## Safety checks and preserved failures

The initial build failed because a hull diagnostic snapshot used integer IDs
instead of native Pt coordinates. `logs/compile_initial_failure.json` records
this compile-only failure. It was corrected before any benchmark. The first
compiled refill prototype was then statically found to be ineffective at A=0;
its header and binaries remain as `*_initial`, and no quality results use them.

`property.cpp` performs10,000 all-off SA/RNG comparisons and2,000 journal-hash /
rollback checks per checkpoint. TightA and multiskill passed24,000 checks total,
with native final validity. The extended property check additionally tests office
close/open journal hashes and compares size, load, skill demands, skill counts,
coverage, inclusion bits and native signature against full reconstruction.
Its distinct source/logs preserve the original test evidence.

Results and final interpretation will be appended only after complete series.

## Completed single-chunk comparisons

Both screens complete72/72 successful processes, each with12 paired comparisons
per variant. All-off and retention-only tie original continuation in every pair.

| Candidate | TL60 checkpoint mean Δ% | W/T/L | TL280 checkpoint mean Δ% | W/T/L |
|---|---:|---|---:|---|
| Bounded kick |0|0/12/0|0|0/12/0|
| Late/threshold |0|0/12/0|0|0/12/0|
| Adaptive tabu |+0.000310315|1/11/0|0|0/12/0|

The sole difference is huge/2101: tabu552401.983455 versus native552381.413956,
+20.569499 objective /+0.003723786%. Median is zero for every variant. This is a
very weak isolated effect, not evidence for enabling an escape default. The
mature screen does not reproduce it. Parent selects tabu only as an exploratory
full-solver ablation, with retention-only as a separate control; no automatic
composition with the geometry component is justified by these figures.

The TL60 per-thread diagnostic records show why counting attempts alone would
mislead: bounded kick has68 episodes,49 rejected kicks, zero improving episodes;
late/threshold has66 episodes and zero improving episodes; tabu has63 episodes,
56 rejected kicks and one improving episode. Recorded exact returns to retained
maximum are54/62/47 respectively. Endpoint assignment changes are90/6/53 and hull
changes33/3/22; worker-certificate changes are zero in all three. Thus altered
territories were observed, but productive departures were rare. Rejected kicks
combine feasibility and the bounded-loss envelope; the separate diagnostics
classify those reasons. Thread-local sampled plateau fractions are about83–84%;
they use iteration checks rather than uniform time sampling.

A subsequent methodology check found native single-LNS continuation can return
around its tloop boundary if polish terminates early. The single-chunk comparison
therefore does not establish superiority over native v4 making full use of the
four-second allowance. A separately frozen repeated-continuation comparison is
required and retained as `REPEAT280.json` / `FREEZE_REPEAT.json`; it repeats LNS
until the common deadline for native, all-off, retain-only and tabu. The original
single-chunk data remain unchanged and are not relabelled as that stronger test.

The coordinator's independent solution-level decomposition
(`integration/ESCAPE_CHECKPOINT60_REVIEW.json`) attributes the sole+20.569499 gain
entirely to lower travel distance. Reward, office cost and imbalance penalty
are unchanged. Eleven assignments differ: five newly selected sites, five
removed sites and one reassignment. Two hulls change; office set and worker
certificate do not. This is evidence of a tiny territorial alternative, not a
worker reassignment or a different office-selection basin.

## First-return diagnostics: useful perturbations did not recover in time

The separate diagnostic series completes36/36 successful processes on the same
six TL60 checkpoints, two fresh continuation seeds and three active modes.
`DIAGNOSTIC_SUMMARY.json` confirms the four frozen production source/binary hashes
are unchanged. Its first-return metric requires a fully verified observed state
at least as good as the pre-episode local best. It is sampled at accepted states,
DP completions and normal controller ticks; it is not a continuous-time crossing.

| Mode | Episodes | Rejected kicks (feasibility / loss) | Effective changed kicks | Recovered effective kicks | Censored duration |
|---|---:|---:|---:|---:|---|
| Bounded kick |62|50 (16 /34)|8|0/8|0.298–0.429s; median0.325s|
| Adaptive tabu |65|61 (22 /39)|3|0/3|0.324–0.342s; median0.339s|

An effective changed kick is accepted, changes assignment/open state, and is not
a rejected proposal restored immediately. Including such rejected/no-change
proposals would produce misleadingly fast apparent recovery medians1–2ms.
All eleven effective changed kicks are right-censored before returning to the
old best within their episode allowance. This does not prove that a longer
recovery could never succeed. It does show that cheap refill alone is not the
cost or success metric that matters for this bounded policy.

Late/threshold has no explicit kick:60/66 episodes observe a first return,
median0.0551s, while six are censored at0.283–0.352s. Returning to the same score
is not an improvement. No candidate/default is tuned using these diagnostic
outcomes. The high proposal rejection rates and failure of changed states to
recover explain why episode counts by themselves do not support promotion.

Causal limitation of the sole positive result: the original huge/2101 tabu trace
shows five kick attempts across the two threads and **all five rejected**;
there are zero tabu rejections. The two accepted native moves in the improving
thread discover the gain. Consequently it cannot be attributed to a successful
new ruin or an observed tabu exclusion. The combined effects of changed RNG
consumption, bounded reheating, timing and retained-state policy are not isolated
by that pair. The trace supports only the measured policy outcome.

## Repeated-continuation control completed

The stronger mature-checkpoint comparison completes48/48 successful processes:
six exact-v4 TL280 checkpoints ×two new continuation seeds ×native v4, all-off,
retention-only and adaptive tabu. Every variant ties native in all12 paired
objectives: mean/median/min/maxΔ%=0 and W/T/L0/12/0. The wrapper repeatedly calls
LNS while at least5ms remain before the common end; its code, transitive sources,
binaries and specification are frozen separately in `FREEZE_REPEAT.json`.
This confirms no observed mature-checkpoint quality benefit for the tested tabu
policy even against the stronger native time-use control. The earlier isolated
TL60 gain remains preserved, with its causal limitations, and is not promoted.

## New targeted geometry-kick hypothesis (separate prototype)

At the coordinator's request, a new mode5 replaces only the frequently rejected
random-refill kick with geometry lab's frozen V1 support-site perturbation.
The old quality source/binaries/parameters remain unchanged. The exact prefix
`geometry_perturb_only_v1.h` has SHA256
`b1877a90fdad4ebc5fed6bd21f53784889c369e4c69bc7223543646623d504b2`.
It is placed before LNS without the geometry lab's separate search wrapper/tail.

The proposal uses a local **copy** of native RNG state and never writes it back;
rejected geometry proposals therefore do not consume native move RNG draws.
The mode uses original SA acceptance for normal moves, original native recovery,
verified local-best retention and immediate original-offer publication of a
positive kick. It includes no late acceptance, tabu rejection, adaptive random
refill or support tail. The inner geometry transaction has its own Engine, so
outer journal, guide score, assignment hash and worker-feasibility cache are
explicitly reset after it returns. Defaults remain off.

A preliminary compilation started just before the RNG-isolation clarification;
its unbenchmarked binary/header are preserved. The preparation script forces a
fresh compilation of final clarified inputs **before** freeze and any benchmark.
No result comes from that transitional build. `GEOMETRY_KICK_DESIGN.json` records
the chronology; `FREEZE_GEOMETRY_KICK.json` identifies the tested source/binary.
The preregistered test uses the same final TL60 checkpoints as geometry lab's
positive screen, six classes, two new continuation seeds, repeated native v4 /
all-off /mode5 and four seconds per process. It does not mix t10/t30 snapshots.

The geometry-kick V1 screen completes36/36 successful processes. Native/off tie
in all12 pairs. Mode5 has mean+0.000633547%, median0, W/T/L2/10/0; its best pair
is+0.005600921%. Gains occur on alphabig/2701 (+1057.256) and huge/2701 (+11.056).
These tiny effects do not establish a practical improvement or justify a default.

Static inspection and the alpha trace reveal a specific integration limitation:
successful support-site kicks can reach the episode boundary with zero accepted
native moves, after which the controller restores its best **before** final
polish. The standalone geometry policy instead invokes local recovery on the
perturbed state before rollback. This motivated one final, separately frozen
repair-attribution prototype, rather than unrestricted parameter exploration.

A native-polish repair was initially prepared/compiled but superseded by the
coordinator before any freeze or benchmark because native resplit inside polish
has weak deadline checks. The source/binary remain unbenchmarked; the dispatcher
intentionally exits75 and `POLISH_SUPERSEDED.json` records zero quality runs.
This is not a solver crash or an omitted comparison result.

The final prototype uses a single native boundary move with q24 and deadline
min(episode_end,now+.04), then observes/offers the repaired state before rollback.
Mode5 includes the frozen geometry kick; mode6 performs the **same plateau,
retention and boundary policy without a kick**. Rejected kicks restore best and
still receive the same boundary repair, so the control accounts for that work.
Native move RNG is unchanged by geometry proposals. In this frozen prototype,
elapsed time is refreshed after a tick that reports a state change; a later
review identified the false-return path limitation documented below.
No native polish, late acceptance, tabu or separate tail is added. This is the
final extra prototype of the round; negative results end selection.

`GEOMETRY_BOUNDARY_DESIGN.json` and `FREEZE_GEOMETRY_BOUNDARY.json` record it.
The matched screen has six same-stage inputs, seeds2701/2702 and five variants
(native/off/retain/mode5/mode6). At the coordinator's explicit resource update,
blocks use both CPU14/15 and CPU18/19, with identical affinity within every block
and NT2. All earlier laboratory measurements remain on CPU14/15. Geometry lab
reviewed journal/guide/hash synchronization and immediate monotone publication;
no correctness-blocking finding was reported. In V1, GEOKICK success was the raw
geometry transaction return, potentially distinct from outer loss-envelope
retention; V2 logs both raw_success and retained explicitly. Construction time,
boundary repair time and full episode time are separate quantities.


## Final completed comparison and selection

All 60/60 final prototype processes passed the runner success gate and official
validator. This is six final-TL60 checkpoints × two continuation seeds × five
variants, four seconds including initialization/output, NT2. Repeated native LNS
uses the remaining allowance. Every matched block used the same assigned CPU
pair. The following means are arithmetic means of per-pair relative objectives:

| Variant | Mean gain vs exact v4 | Median | W/T/L |
|---|---:|---:|---:|
| All-off | 0% | 0% | 0/12/0 |
| Retention-only (mode4) | 0% | 0% | 0/12/0 |
| Geometry kick + boundary (mode5) | +0.012648901% | 0% | 4/8/0 |
| Boundary without kick (mode6) | +0.014699265% | 0% | 3/9/0 |

Mode5 versus mode6 is 2/9/1, arithmetic mean −0.002049590%. The only different
pairs are alphabig/2701 (−5756.807064 objective, −0.030487966%), alphabig/2702
(+801.857250, +0.004247919%) and huge/2702 (+9.086203, +0.001644972%).
Thus the perturbation does not improve the mean over its repair-only control.
The experiment supports testing earlier bounded boundary repair, not attributing
that gain to geometric escape. No escape policy is promoted to a default from
these data, and no further prototype or tuning is planned in this round.
The coordinator owns full TL60 and independent TL60/TL280 tests; this checkpoint
screen alone is not evidence of improved end-to-end or holdout performance.

`GEOMETRY_BOUNDARY60_SUMMARY.json` contains all paired records and telemetry;
`GEOMETRY_BOUNDARY60_ANALYSIS.json` adds the shared analyzer's decomposition and
resampling summaries. `FINAL_LAB_AUDIT.json` covers all six laboratory runs:
324/324 successful processes, no missing comparisons, preserved frozen source
hashes. Maximum final-screen wall time is 4.248363 s, inside the declared TL+3 s
runner tolerance; deadlines are soft, not a claim of strict 4 s completion.

A final independent review found that `tick(false)` can still run `observe`,
whose full verification may cross tloop while the caller retains cached `now`.
The frozen source refreshes `now` only after `tick(true)`. This does not invalidate
solution certificates or monotone publication, but weakens the no-new-move-after-
deadline claim. The coordinator will make a separately documented unconditional
refresh/check for the final freeze; no source used by the recorded screen was
changed. Native boundary/resplit/worker checks also have soft internal deadlines.

Ready full solver: `bin/geometry_boundary_full`, source
`src/geometry_boundary_v4.cpp`, local includes `src/escape_geometry_boundary.h`
and `src/geometry_perturb_only_v1.h`. Compilation completed successfully with
-O3 -std=c++17 -pthread on CPU14,15. `BUILD_GEOMETRY_BOUNDARY_FULL.json` fixes all
source/include/binary hashes and the exact command. Default ESCAPE_MODE remains
0; mode6 is the stronger repair-only candidate and mode5 its perturbation
comparator. This full executable is compiled, while its full-length validation
belongs to the coordinator; the checkpoint executable is the tested artifact.
CPU14,15 and CPU18,19 were explicitly released to the coordinator after the final
compile. No later laboratory compile or benchmark is scheduled.
