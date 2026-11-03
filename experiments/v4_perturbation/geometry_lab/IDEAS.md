# Geometry perturbation lab: preregistered small structural changes

Comparator: exact frozen server v4 SHA256 `5b3914fa9791cb879f3232fb2876a915de83b848ad4b353b0dbf25b574998c25`. All writes remain here. CPU12/13 are separate physical cores; compilation, native tests, Python coordinators and official validation inherit that affinity. NT=2. No holdout is accessed.

Previous negative findings are treated as constraints: full hull-layer peeling, independent random removals and whole triple rebuilding destroy cardinality/load and consume repair time. This experiment instead preserves the exact count and task load of every office during each completed perturbation. It allows only a small objective loss in the private working state, never in the separately retained best solution.

Modes:

1. Boundary packets: 1↔1 and 2↔2 exchanges with equal total task count; pools contain24 sites per direction ranked by destination-minus-source real profit. Both affected hulls need not change, but at least one must. This is geometric small-step exploration; it deliberately cannot jump office-set basins.
2. Support replacement: replace one actual hull-support site by a free site of exactly the same task count, selected among32 highest real profit alternatives. At least one input point must cease being covered by the modified zone. No unbalanced removal is accepted.
3. Directed three-office cycle: one boundary-pool site from each office, all equal task count; each enters the next office. This is a3-site transaction, not the previous whole-three-zone power rebuild. At least one hull must change.

Each proposal uses the exact frozen Engine with remove-all/add-all rollback, plus worker feasibility. Nonpositive proposal gains are allowed down to min(0.2% incumbent absolute objective,0.5 average absolute per-site profit), using1 as the numerical floor. This is a heuristic scale, not a theorem. Every completed proposal preserves the office set, cardinalities and loads, so cost and imbalance terms are exactly unchanged; its immediate objective change is real profit only.

Recovery is bounded native LNS with offices locked, up to0.35s per episode. Before each episode the current best is copied; recovered inferior states are discarded. If no perturbation is found in256 bounded attempts or0.08s, remaining time is given to ordinary native LNS. Main comparisons use same input/checkpoint,2 threads, same seed and4s total process budget including initialization, proposal, feasibility, copying, recovery and final serialization. Main control is native LNS continuation; ordinary polish is a secondary plateau diagnostic.

The4s run is not a full60 or280 solver comparison and cannot itself justify a new default. Positive results must survive a separately fixed optional final hook under full budget. Any failures, timeouts and negative effects remain recorded.

Correctness: independently rebuild all fields and verify30000 random transactions on100 small instances with duplicates/collinear points, worker scarcity, multiskill and alpha0/100. Check that failure rolls back and success preserves exact counts/load/offices. Test assertions are enabled atO1; speed/quality binary usesO3.
