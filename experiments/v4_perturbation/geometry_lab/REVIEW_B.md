# Read-only integration review of B's support plateau kick

Reviewed `escape_lab/src/escape_geometry_kick.h` and the include ordering in `geometry_kick_v4.cpp`. No files outside geometry_lab were changed.

The perturb-only source is the exact prefix of frozen V1 before geometry_search; hashes are in SPLIT_V1.json. It needs Engine and Sol but does not require a prior lns definition. The outer Engine journal is cleared before the call. The perturbation has its own journal, commits an internally feasible count/load-preserving state on success, and restores the entry state on failure. Therefore subsequent outer journal clear, Guide value and full assignment hash recomputation, and caller worker-signature invalidation are necessary; they are present. Positive accepted kicks are observed and offered immediately, avoiding loss of that positive intermediate state during native recovery. No blocking correctness issue was found by this static review; this is not a substitute for B's runtime oracle.

Metric caveats communicated and confirmed: GEOKICK success is the raw geometry_perturb return; the outer controller can subsequently reject by its own loss cap. The controller's failed_kicks records such rejection. Its recovery_seconds counter includes kick construction cost, not the full subsequent native recovery episode or first-return time. These counters cannot be equated with geometry_lab's endpoint recovery durations.

The copied kick RNG leaves the native RNG stream unchanged; B preserves the earlier consumed-RNG variant as history. Different placement and acceptance are a new hypothesis, not promotion of the rejected final tail.
