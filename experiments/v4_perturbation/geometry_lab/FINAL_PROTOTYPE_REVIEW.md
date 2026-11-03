# Read-only review of final plateau/boundary prototype

Reviewed file: `experiments/v4_perturbation/integration/src/boundary_dev.cpp`.
SHA256: `44ae896a9eeb1cf618fa0e2d91136a676d0f91568c14d8bdef964a199f2977e8`.
Scope: static inspection only. No compilation, CPU test, benchmark or validation was run for this review; no source outside geometry_lab was modified. Line references below are for this hash.

## Verdict

No blocking journal, rollback or publication-validity error was found in the new mode5/mode6 path. It is suitable for the planned *experimental* equal-budget ablation, subject to the deadline limitations below. This review neither establishes quality superiority nor certifies a hard wall-time bound. A negative outcome is a valid research result and does not justify a submission package.

## State transactions and valid incumbent

- The perturb-only V1 definitions precede EscapeControl (2508–2607), so they do not require a recursive or forward-declared lns call. The relevant mode2 transaction preserves completed office counts, loads and activity and checks native geometry plus worker feasibility. It uses a private Engine journal; rejection restores its entry state.
- `restore` (2657) reloads the controller's retained assignments/offices and clears the outer Engine journal and bans. In the new path (2672–2686), both the perturbation and boundary operation are followed by outer journal clearing, Guide value recomputation and a complete assignment hash recomputation. The caller invalidates the cached worker signature when tick reports a state change (2802). Thus the private transactions do not leave unlogged changes in the next native proposal's outer rollback journal.
- BoundarySearch uses its own journal. Its `finish` (2446–2459) restores its input before trying an improved assignment, and reverts if worker reconstruction/full verify fails. A deadline ending its DFS therefore does not leave the shared Sol at an incomplete search node.
- A retained positive kick is observed and offered before boundary recovery (2678–2679), and boundary improvements are observed/offered again (2684–2685). This preserves a positive intermediate state that later native recovery could lose. `offer` remains the verified global publication gate; inferior private working states cannot replace its output incumbent.
- Modes5/6 use ordinary native acceptance, not mode2 late acceptance or mode3 tabu acceptance (2714–2723). `finish` restores the controller's best before existing DP/polish (2726–2727;2945–2949). Initial controller state feasibility is the same inherited precondition as the native LNS entry, rather than a new constructor validation.
- Mode0 short-circuits tick/observe/finish and retains the native acceptance/RNG condition. Code layout, constructor/branch overhead and wall-clock trajectories can still differ from the exact baseline; the explicit all-off comparison is necessary.

## Deadline findings

1. **The post-tick guard is conditional on a changed state (2802).** `tick` calls `observe` before deciding whether to return false (2660). `observe` can run worker search and full input-point verification (2640–2645). If those cross tloop but tick then returns false, `now` remains the earlier timestamp and the native loop can start another operation. To make this guard cover observer cost, elapsed time would need to be refreshed/rechecked after every enabled tick, independently of its changed-state result. This is a soft-deadline risk, not a demonstrated invalid output or measured timeout from this read-only review.
2. The geometry deadline is checked around proposal generation, but sorting, hull reconstruction and worker checks within an attempted transaction are not interruptible at every instruction. The native boundary call is limited to q24 and receives `min(episode_end, now+0.04)` (2683), but its neighborhood setup, constructor, worker checks and final full verification can exceed that local interval. Therefore `.04s` is a search cutoff, not a proved maximum elapsed call cost.
3. At an expired episode, `record_episode` can still perform worker reconstruction and restore rebuilds. The 30% episode budget is checked on already recorded time before launching a new episode (2665); one additional episode and its overrun can carry the realized total above30%. Reports should describe this as an admission rule rather than a strict runtime partition.
4. The new post-change tloop recheck is useful: when a kick/repair actually runs, its measured cost is now charged before the next normal move. No extra full-solver time is explicitly reserved or added. Existing main finishing order remains `finish_solution` then `boundary_finish` after worker joins.

The planned run manifests should retain actual wall time, success/timeout, and local episode/repair overshoot. A valid incumbent surviving a timeout does not make the timed-out run successful.

## Attribution and counters

- Mode5 copies the native RNG for geometry, while mode6 omits geometry; both then use the native RNG for one bounded boundary call on the controller's best/restored state. A failed kick still receives the same kind of bounded repair. This is a useful targeted control: differences include the geometry state change, its cost, and later search consequences, rather than an entirely different RNG draw count caused solely by proposal sampling.
- A geometry call can consume enough episode time to shorten or skip its boundary repair. That is part of the perturbation's real cost and must remain in the comparison. Full-run trajectories can diverge before later plateau episodes; full objective differences are not per-kick causal gain estimates.
- A mode5 win over plain v4 does not by itself establish perturbation value. Compare mode5 with mode6 and mode6 with retain/all-off; otherwise a benefit from simply running boundary repair earlier would be misattributed to support perturbation.
- `raw_success` and `retained` are now distinct (2674–2676;2686), resolving the earlier metric ambiguity. In mode6 both are initialized true without a geometry proposal, so they are not geometry acceptance observations for that control; attempts/accepted remain zero.
- `recovery_seconds` in EscapeControl measures kick construction/check cost here. `repair_seconds` includes the boundary call plus subsequent recomputation/observe/offer before printing. Neither is the first-passage time back to the pre-kick objective. `escape_seconds` includes the wider native episode.
- `changed_assignment`, `changed_office` and related episode counters compare the final working state with the snapshot taken **before** restoring the controller's best (2667 vs2670). They include that restoration and subsequent native moves, not only the geometry transaction. `GeometryStats.moved` describes the direct kick separately.

## Recommendation

Proceed with the requested exact/off/retain/mode5/mode6 experiments as research, preserving negative results and freezing the selected source before independent data. Use source-specific runtime evidence before any hard-deadline or promotion claim. No source edit or packaging action was performed by this review.
