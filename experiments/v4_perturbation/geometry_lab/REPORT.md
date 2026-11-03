# Small structural perturbations: exact frozen server v4

This laboratory is research only. The exact baseline source is SHA256 `5b3914fa9791cb879f3232fb2876a915de83b848ad4b353b0dbf25b574998c25`; the ordinary solver and previous experiments are untouched. All builds, tests, benchmark processes and official validation in this lab use CPU12/13, NT2 for quality runs. No holdout was consumed, and nothing was staged, committed, pushed or deleted.

## Operators and what is actually guaranteed

`src/geometry_perturb.h` is immutable V1. `geometry_finish.h` is its optional integration hook, called after `finish_solution` and before `boundary_finish`, defaults OFF (`GEOMETRY_PERTURB=0`). Modes1/2/3 request packets/support/cycle; `GEOMETRY_SECONDS` defaults0.8s, capped by the original solver's remaining tail deadline.

The completed perturbation preserves the exact count and task load of every office and the set of offices. It removes all changed sites first, then adds through frozen-v4's exact Engine and verifies workers; failure rolls back. Thus a perturbation's immediate objective change contains only real site profit, with zero office-cost and imbalance change. The native LNS recovery can change count/load and, despite passing `lock_offices=true`, can open an office: frozen v4 checks that flag on closure but not on its opening branch. This pre-existing behavior was not silently changed.

V1 uses1↔1/2↔2 equal-load packets, an equal-load replacement of a hull-support site by a free site that changes the hull and releases at least one input point, and a directed equal-load3-site cycle. Small losses are allowed only in the working state, with a separately retained best and native global verified publication. Each recovery is bounded to0.35s, although inherited native helpers use soft deadlines and may overrun the episode. Returning an inferior recovery endpoint never replaces the valid output incumbent.

V1 pair/triple office selection is uniform, while its site pools rank destination-minus-source road profit. This is not guaranteed geometric adjacency. The screen found zero accepted packet/cycle perturbations, so their negative result alone says little about useful equal-load chains. V2 (`geometry_perturb_v2.h`) therefore chooses among the3 nearest hulls, combines geometric boundary and road-profit site pools, ranks compatible packets/cycles before testing and requires support replacements to release an input point other than the exchanged sites. It also adopts a better globally published incumbent after recovery. These several changes make V2 an exploratory prototype, not a single-factor ablation.

This differs materially from previously rejected peeling/random removal/whole-triple rebuilding: no completed perturbation violates count/load, no whole zone is destroyed, losses are small, and the cycle changes only3 sites. It still cannot directly solve office-set basin barriers.

## Correctness and deadlines

Both V1 and V2 passed30000 atomic transactions on100 small instances, with duplicates/collinearity, alpha0/100 and multi-skilled/scarce workers:7018 accepted and22982 rejected per run. After every transaction all membership, count/load, skill demand, coverage lists/matrix, hulls, signature and objective are compared with an independent reconstruction; frozen independent `verify` checks workers and all input-point hull overlap. Rejection restores assignments and office activity. Test builds useO1 and `_GLIBCXX_ASSERTIONS`; quality builds useO3.

The first test harness compilation referenced merged-only `Inst::build_grid`; this compile error was fixed before tests ran, and its diagnostic is retained. V1's driver accidentally emitted no newline after its per-thread diagnostic, while V2 fixes that formatting; parsing uses the delimited `geometry ... first_improvement=...` record and does not depend on a newline. No benchmark binary/source was overwritten while its runs were active.

The shared offline reader independently verifies and publishes the input worker certificate before the search. Tiny-budget checks below assess retention of that valid output even if initialization consumes the requested budget. These offline files/checkpoints are never part of the submitted solver.

## Metrics and limitations

`SCREEN60_SUMMARY.json`, `SCREEN280_V2_SUMMARY.json` and later summaries retain individual official objective, return code, actualNT, wall, RSS, input/source/binary hashes, final assignment/worker/hull/office changes, reward/distance/cost/imbalance decomposition and raw per-thread counters. Every solver variant within a(case,seed) block uses the same pinned CPU pair in randomized order.

Per-thread `improved`, `unrecovered`, `returned_same` and recovery duration are **endpoint observations**. Native LNS may publish a superior intermediate solution and then return a worse endpoint. The final official objective uses the globally retained best encountered solution; endpoint failure counters must not be interpreted as proof that no intermediate improvement occurred. Summed thread seconds are not process wall. V2's loss-rejection counter additionally counts proposal-ranking discards and is not directly comparable with the V1 transaction rejection denominator.

An important screen limitation was found and preserved: a single call to native LNS may finish after about70% of its nominal4s budget, after early polish termination, whereas repeated support episodes often consume almost all4s. Thus the original nominal-equal-budget screen is not an equal-used-time comparison. Subsequent `filled_lns*` controls repeat native LNS until the common deadline. Separate `exact_repeat*` runs compare an exact frozen-source repeated-LNS driver with the all-off compiled candidate and support on the same two informative cases. `causal3_mature_v1` instead compares boundary alone, supportV1 then boundary, and monotone-only support then boundary within one common3s budget.

## Initial nominal-budget screen (not sufficient for promotion)

80/80 successful,8 development classes ×2 solver seeds ×5 variants, same checkpoint from exact v4 atTL60. V1 support versus single-LNS: mean+0.021690%, median0, min−0.003466%, max+0.180009%, W/T/L3/12/1. The two alphabig gains were+0.180009/+0.169090%, changing2/4 assignments and1 hull with unchanged reward, costs and imbalance; the gain was entirely lower road distance. On huge, one support run gained0.001400% over its checkpoint, while the other lost to the control's0.003466% improvement. Packet/cycle had no accepted perturbations across their16 runs each.

Support accepted208/4582 tested transactions. Across208 endpoint recoveries,6 ended better,42 returned to identical assignments and160 remained below their entry objective. These outcomes are endpoint-only as explained above. They show that low-cost proposal construction does not imply cheap or reliable recovery; they are not independent success probabilities across instances.


## Final paired evidence (completed)

All percentages below use paired `(candidate−control)/max(1,abs(control))`. The unit is a(case,seed) pair, not a hidden-test score. All raw results are retained.

| Series | Variant | Successful runs, all variants | Mean Δ% | Median Δ% | Worst Δ% | W/T/L |
|---|---|---:|---:|---:|---:|---:|
| screen60 | packet | 80/80 | -0.000217 | +0.000000 | -0.003466 | 0/15/1 |
| screen60 | support | 80/80 | +0.021690 | +0.000000 | -0.003466 | 3/12/1 |
| screen60 | cycle | 80/80 | -0.000217 | +0.000000 | -0.003466 | 0/15/1 |
| screen60 | polish | 80/80 | -0.000217 | +0.000000 | -0.003466 | 0/15/1 |
| screen280_v2 | packet | 72/72 | +0.000000 | +0.000000 | +0.000000 | 0/12/0 |
| screen280_v2 | support | 72/72 | +0.000011 | +0.000000 | +0.000000 | 1/11/0 |
| screen280_v2 | cycle | 72/72 | +0.000000 | +0.000000 | +0.000000 | 0/12/0 |
| screen280_v2 | polish | 72/72 | +0.000000 | +0.000000 | +0.000000 | 0/12/0 |
| screen280_v2 | support_v1 | 72/72 | +0.000000 | +0.000000 | +0.000000 | 0/12/0 |
| causal3_mature_v1 | support | 36/36 | -0.003172 | +0.000000 | -0.015464 | 0/8/4 |
| causal3_mature_v1 | monotone_support | 36/36 | -0.003418 | +0.000000 | -0.026253 | 0/8/4 |
| filled_lns60 | support | 32/32 | +0.028650 | +0.000000 | -0.003466 | 3/12/1 |
| filled_lns280 | support | 24/24 | +0.000000 | +0.000000 | +0.000000 | 0/12/0 |
| exact_repeat60 | support | 12/12 | +0.078350 | +0.068429 | -0.003466 | 2/1/1 |
| exact_repeat60 | alloff_repeat | 12/12 | +0.000000 | +0.000000 | +0.000000 | 0/4/0 |
| exact_repeat280 | support | 12/12 | +0.000000 | +0.000000 | +0.000000 | 0/4/0 |
| exact_repeat280 | alloff_repeat | 12/12 | +0.000000 | +0.000000 | +0.000000 | 0/4/0 |
| synced3_alpha60 | support | 6/6 | -0.038256 | -0.038256 | -0.049877 | 0/0/2 |
| synced3_alpha60 | monotone_support | 6/6 | -0.274461 | -0.274461 | -0.346865 | 0/0/2 |
| synced3_alpha280 | support | 6/6 | +0.000000 | +0.000000 | +0.000000 | 0/2/0 |
| synced3_alpha280 | monotone_support | 6/6 | +0.000000 | +0.000000 | +0.000000 | 0/2/0 |

The original single-call screen controls can stop early. `filled_lns` and `exact_repeat` exhaust the native-LNS control budget; the support strategy may still stop early when it cannot build a perturbation. Thus support never gains an advantage from unused control time in these repeats. The `exact_repeat` all-off variant uses the same compiled source as support.


## Stage mechanism with synchronized phases

The first causal series lets each thread start boundary recovery independently, so phases can overlap slightly when native LNS exceeds its local deadline. It also carries the RNG consumed by geometry into boundary search, unlike the production wrapper's fresh boundary RNG. Its negative percentages therefore characterize that driver, not precisely the production ordering. The separate synchronized diagnostic waits for both geometry threads, saves and independently validates the global incumbent, then restarts both boundary RNG streams identically to the boundary-only control. It uses only alphabig, at both saved checkpoint ages; these are diagnostic development data, not a holdout.

| Checkpoint | Seed | Variant | Geometry gain | Boundary gain | Changed assignments after geometry |
|---|---:|---|---:|---:|---:|
| 60 | 2102 | monotone_support | 35763.999461 | 37306.176686 | 4 |
| 60 | 2102 | support | 25833.833717 | 103710.162376 | 2 |
| 60 | 2102 | boundary | 0.000000 | 139028.273029 | 0 |
| 60 | 2101 | monotone_support | 53483.052324 | 47539.622835 | 4 |
| 60 | 2101 | support | 0.000000 | 134381.026488 | 0 |
| 60 | 2101 | boundary | 0.000000 | 139445.842838 | 0 |
| 280 | 2102 | monotone_support | 0.000000 | 1920.855901 | 0 |
| 280 | 2102 | support | 0.000000 | 1920.855901 | 0 |
| 280 | 2102 | boundary | 0.000000 | 1920.855901 | 0 |
| 280 | 2101 | monotone_support | 0.000000 | 5960.695357 | 0 |
| 280 | 2101 | support | 0.000000 | 5960.695357 | 0 |
| 280 | 2101 | boundary | 0.000000 | 5960.695357 | 0 |

Stage snapshots passed official validation: 12/12. Full reward/distance/cost/imbalance decomposition is in `SYNCED_STAGE_ANALYSIS.json`.

On the earlier checkpoint with seed2101, support leaves the global incumbent exactly unchanged before boundary search. The same-state, same-RNG boundary gain then falls from139445.84 to134381.03 because less time remains. With seed2102, the support stage gains25833.83 by changing2 assignments, yet its combined gain129544.00 remains below boundary-only139028.27; the altered state and reduced time are not separately identified in that case. Monotone support also loses, so the failure is not explained merely by permitting temporary deterioration. On the mature checkpoint, the synchronized stage changes nothing and boundary search reaches the same1920.86/5960.70 improvements within either remaining budget. The earlier unsynchronized mature losses are therefore not robust evidence of production-tail regression; the robust conclusion is lack of incremental mature gain and demonstrated opportunity cost on the earlier checkpoint.


Tiny-budget incumbent checks: deadline_short 6/6 valid and successful (max wall0.322711s), deadline_mid 6/6 valid and successful (max wall0.485431s). These test certificate/output retention when initialization or a local move reaches the deadline; initialization itself cannot be made zero-cost.


## Decision and remaining hypothesis

No structural tail is recommended as a default from this lab. Support can improve some earlier incumbents under a repeated native-LNS control, but has no broad mature-checkpoint improvement and loses time to an effective existing boundary operator. V2 makes packet/cycle proposals feasible (38/37 accepted on the mature screen), yet their75 recovery endpoints all remain below entry and no final improvement occurs. This does not prove larger budgets or different placement cannot work. In particular, an explicitly separate plateau-time support experiment can test placement earlier in the main search; it must not be described as acceptance of the rejected final-tail combination.

The60s and280s checkpoints use different solver seeds1901/1902, so differences between them are not a causal estimate of extra optimization time. `PLATEAU.json` instead reports within-run saved objectives and assignment changes at known snapshot times. No output ZIP, commit, push or submission was produced by this lab. The optional code and all negative evidence remain available to the parent investigation.
