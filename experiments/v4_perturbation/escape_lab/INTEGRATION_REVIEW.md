# Independent read-only integration review

Reviewer: escape lab. Scope: `integration/src/combined_dev.cpp`,
`shared/run_blocks.py`, `shared/analyze.py`, `PROTOCOL.md`. The review does not
modify parent runtime, tools, protocol or evidence. This preliminary review
precedes the final candidate freeze and independent holdout; it is not a final
performance audit. The reviewer authored the escape component, so the review of
that component is not independent authorship. Geometry lab separately reviewed
its journal/hash/rollback/all-off hooks without finding a correctness blocker.

## Runtime and publication

No P0/P1 correctness defect found in the inspected composition. Escape-local
snapshots and final geometric transactions cannot directly replace the global
answer: publication still passes original `offer`, worker assignment and full
native `verify`, under the global-best mutex. The support transaction removes
all selected sites before rebuilding target hulls and rolls back failed skill,
geometry or objective conditions. Counts and task loads are explicitly checked
before mutation and again for feasibility after mutation. Its intermediate
count imbalance is never published. The original serialized incumbent remains
available when a recovery or worker search reaches its deadline.

All new production mechanisms default OFF. ESCAPE_MODE0 reproduces the original
SA short-circuit/RNG expression and does no controller mutation. GEOMETRY_PERTURB0
returns before starting its tail. Both flags off therefore preserve algorithmic
intent; binary layout, tiny constructor overhead and time/thread scheduling can
still alter timed trajectories. The separately benchmarked all-off binary is
necessary. Mode4 is explicitly **best retention**, not pure telemetry: restoring
local best before DP/polish can change the subsequent trajectory.

Escape tabu uses a disjoint token space for site/office assignments and open
flags. Journal additions/removals XOR the same token, as do openings/closures.
The native invariant that the journal is empty before the next proposal is
preserved by accept-clear/reject-undo; DP and controller restoration resynchronize
the hash. Tick restoration invalidates cached worker feasibility through wsig.
Hash collisions can conservatively reject a state; they do not authorize invalid
publication. There is no persistent archive, restart file or external dependency.

## Deadline and attribution limitations

The original wall-time deadline remains in force and the geometry tail is bounded
by both remaining outer time and its requested allocation. Neither mechanism
gets the benchmark's3-second accounting tolerance as algorithmic time. However,
native `verify`, worker matching, state reconstruction and individual native moves
are not preemptible. Episode duration and the nominal30% escape share are soft
checks at safe points, not hard real-time guarantees. Measure actual wall-time
and retain overruns. A valid last checkpoint after timeout/nonzero exit does not
turn that process into a success.

A single native LNS call can finish before its supplied deadline after early
polish termination. Consequently the original four-second single-chunk screen
compares equal allowed budgets, not guaranteed equal consumed budgets. The lab
retains it and adds a separately frozen repeated-continuation driver running
native LNS again while time remains. This is the appropriate stronger competitor
for checkpoint claims about useful use of the entire remaining budget.

Escape plus geometric support is not automatically a sum of independent effects:
with ESCAPE_MODE enabled, the geometry tail's calls to LNS also use that controller.
Any combined runtime configuration requires its own ablation and full-run checks.
Per-thread gains/episode counters cannot be summed into the final process gain.
The quality log's recovery_seconds is refill cost; separate diagnostic sources
measure first return and censor unrecovered episodes.

## Pairing and missing/failed results

The runner randomizes variants within each(instance,seed) block; all variants of
a block run sequentially on the identical two-core affinity. NT2/SEED overrides
are applied after variant environment. Input, checkpoint and binary hashes are
checked immediately before each run. Cross-process CPU lock files coordinate
runner jobs using the same logical CPUs; they do not exclude unrelated programs,
compilers launched outside the runner, SMT siblings or shared thermal/power effects.
The recorded topology and parent allocation prevent the intended SMT overlap.

The runner stores return status, emergency timeout, official validation,
actual-thread log, wall time, resource data and immutable output paths. Success
requires all declared predicates, including wall≤TL+3. The analyzer asserts exact
expected key products, no duplicates, matching pair affinity and COMPLETE counts.
No missing result is silently omitted. It preserves all failed rows separately.

The analyzer deliberately also describes valid output files from failed
processes under `distribution_valid_outputs_including_failed_processes`; its W/T/L
and per-case statistics use that same population. These numbers must not be
presented as successful quality evidence when failed_pairs>0. Promotion must
first require every expected process to succeed, as the protocol specifies.
With zero failures the distinction disappears. Zero baseline objectives are
excluded from percent statistics but remain in raw pairs/result classifications.

Preliminary audit gaps in analyze.py: its current hash_audit verifies top-level
binary/source/input files, but not checkpoint, output-versus-row, spec, runner or
validator hashes; it also does not independently recompute every success flag or
cross-run CPU-interval overlap. The runner records enough evidence to check these
at final audit. A combined self-contained source avoids include-hash ambiguity;
small offline driver sources additionally need the separately recorded transitive
include hashes. These are final-audit requirements, not evidence of a changed file.

## Protocol arithmetic and statistical interpretation

The original preregistration says six TL280 inputs×two seeds×three variants, which
is36 processes /12 paired case-seed blocks, but calls it18 trials. Parent was
notified to preserve the preregistration and append a dated arithmetic correction.
The six long-run inputs overlap the twelve primary held-out inputs; they are not
six additional independent inputs. The bootstrap resamples input-level means,
which correctly avoids counting solver seeds as independent generated problems.
The strict validity/mean/median/worst-pair/bootstrap/all-off promotion gate must
be checked on complete frozen-candidate data. Development wins and supplemental
variance seeds cannot replace negative primary holdout observations.

Final frozen-source and complete-evidence audit remains pending.

## Short gen10 runtime failure investigation

Parent's combined development smoke has one valid/rc0 process that exceeds the
TL3 accounting wall bound: about6.029s. It remains a failure. Its trace records
an escape-controller interval of5.210250s with only3 native LNS iterations,
zero episodes/kicks, two split attempts (one accepted), one ruin attempt and
one DP call. This rules out a new destructive escape episode as the direct work
performed, but does not rule out verification/restoration overhead outside an
episode or timing changes from the new controller.

A concrete inherited unbounded path exists in frozen-v4 `move_resplit`: every
angular sweep and refinement runs without a time check; then the loop removing
all selected sites repeatedly rebuilds hull/coverage without checking the hard
cap. Only the later insertion loop checks it every128 insertions. `resize_dp`
also checks at office/window boundaries, not inside its knapsack inner loops.
These paths can overshoot a short deadline. The aggregate trace alone cannot
uniquely attribute the5.21 seconds among resplit, DP and added verification.
A matched native/all-off run and, if necessary, a separately instrumented timing
build are needed. No frozen source was patched on the basis of this finding.


## Final boundary prototype deadline addendum

Geometry lab identified a remaining soft-deadline path in the frozen boundary
prototype: caller refreshes elapsed time only when tick returns true, whereas
tick(false) may still verify an incumbent in observe and cross tloop. Parent
will apply unconditional refresh/check as a separately frozen change. Recorded
60-run source is unchanged. This is a runtime-budget issue, not an invalid
certificate or worse-incumbent publication finding. Final local compile and
all tests finished; CPU14,15 and18,19 explicitly released to parent.
