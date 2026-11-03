# Escape lab preregistration

Exact baseline SHA256 5b3914fa9791cb879f3232fb2876a915de83b848ad4b353b0dbf25b574998c25.
Only this directory is written. All builds, native runs and official validation
use CPU14/15 and NT2. No independent holdout is examined here.

The new header preserves the original LNS operators, cooling and phase budget.
A plateau means no new fully verified thread-local objective record for
min(2 seconds, max(.08 seconds, .16 loop duration)); it is not a proof of local
optimality. An escape episode lasts at most min(.8 seconds, max(.06 seconds,
.10 loop duration)). Episodes consume at most approximately30% of loop duration
(the last admitted episode can cross that cap; it cannot exceed the loop end).

* Mode0: all off, original acceptance including identical RNG short circuit.
* Mode1: plateau-only symmetric-count removal of one random site per nonempty
  office (never emptying an office), bounded alternate-site refill excluding
  removed sites, then native level_fill/recreate with an explicit .35-episode
  deadline; reject infeasible or excessive loss, then original LNS recovery.
* Mode2: plateau-only late/threshold acceptance with64-slot objective history and
  a bounded loss. No destructive proposal is added.
* Mode3: adaptive symmetric-count removal1–4 sites per office;12-state short tabu
  on full assignment/open mask via incremental journal hashing; aspiration for
  an objective record. A4× temperature applies only during the bounded episode.
* Mode4: best-retention-only control, essential to separate memory overhead and
  restoration from escape semantics.

Loss envelope=min(.75% of max(1,abs(incumbent)),2× native profit scale).
True objective, feasible worker matching and full native verify gate local
records; global publication remains the original offer. Internal trajectories
may decrease; checkpoint output cannot be below its verified input. Snapshot
storage is O(N+O); no persistent archive, workers/population cloning or ALNS
credit changes. Full runtime candidate defaults off.

This addresses previous negative ILS/VNS/TS/GWW/archive experiments by avoiding
replacement of every original LNS chunk, unbounded reconstruction and permanent
cross-chunk basin retention. It does not assume that these changes will improve
quality. Full TL60/TL280 comparisons remain necessary and may reject all modes.

Planned initial screen: exact same fresh v4 TL60 checkpoints;6 representative
classes, two solver seeds,6 seconds per process; original v4 continuation,
all-off, best-only and modes1/2/3. Within each(case,seed) block, randomize variants
and pin all to CPU14/15. Retain every failure and official validator result.
Metrics: paired gain; plateau fraction; successful escape episodes; exact return
to retained maximum; recovery seconds; assignment/open/hull/worker changes;
profit/cost/imbalance decomposition. Tick counts and episode changes describe
this controller and must not be advertised as an unbiased native baseline trace.
