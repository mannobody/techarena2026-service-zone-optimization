# Final statistical/procedural read-only review

Reviewed before holdout generation, 2026-10-19. No solver, validator, analyzer,
benchmark or compilation was executed by this review. Only source/document reads
and writing this report/its hash manifest in escape_lab. CPU allocations remain
released. This review does not read independent holdout inputs or outcomes.

## Blocking findings for automatic acceptance

### P1 — Required extra runs do not enter a final acceptance gate

`integration/evaluate_holdout.py:45` writes accepted_at_this_budget from primary
runs before variance extension. `integration/holdout_pipeline.py:34–40` only runs
and analyzes extras, then marks the pipeline complete. There is no final reducer
requiring both primary decisions, all required extras completed, and success of
every extra process. A variance solver failure can leave the primary accepted flag
true: run_blocks finishes normally with success=false rows, and analyze also
returns normally. HOLDOUT_ANALYSIS_RULES.md explicitly requires all runs of all
three variants to succeed. This is a concrete acceptance gap, not an objection to
keeping primary statistics unchanged.

Required action: retain immutable primary decisions, label them primary only,
and add a final decision requiring both primary budget gates plus complete and
successful required extra series. Show extra statistics separately and construct
the promised combined summary by averaging all seeds within each input then
weighting inputs equally; bootstrap input means, never the enlarged pool of pairs.
Do not let favorable extras rescue a failed primary gate. Preserve all individual
pairs and the worst extra/combined pair for the adverse-outcome explanation.
The present written rule does not explicitly say every quality threshold is
retested on the extra series, so do not silently invent that requirement after
seeing its outcomes; the missing all-process-success gate is unambiguous.

### P1 — Acceptance is not bound to the original freeze identity

`shared/analyze.py:44–46` computes hash booleans but evaluation never gates on
them. It covers binary/source/input only, not the original freeze/spec/env,
recorded output or validator. `holdout_pipeline.py` has no freeze identity check.
The runner snapshots the currently available binaries and verifies those hashes
before each process; this guards within-series mutation, but not mutation between
FINAL_FREEZE and runner startup, nor between budgets. generate_holdout verifies
source/binary against freeze once, which is useful but does not close this later
gap. shared/audit.py strengthens record integrity but also compares to each run's
manifest rather than linking candidate/off manifests to FINAL_FREEZE.

Required action: before each primary/extension run, and in final acceptance,
verify candidate/off source+binary hashes and env against FINAL_FREEZE; verify
that HOLDOUT_INPUTS.freeze_sha256 equals the freeze file hash, generated input
hashes match manifest, v4 is the exact frozen baseline, and spec matches the
registered budgets/seeds/classes/three variants. Fail acceptance on any identity
or record audit error, including output/validator/runner/spec mismatches. Persist
analysis/rules/script identities so later reanalysis is distinguishable.
This is a missing enforcement path; no actual freeze mutation was observed.
FINAL_FREEZE/HOLDOUT specs had not yet appeared in the inspected listing, so
this review cannot certify a future artifact's bytes or run chronology.

## Nonblocking robustness/completeness findings

* `analyze.py:57–65` excludes a pair from percentage statistics when the comparator
  objective has magnitude <=1e-9. Validity/process success alone does not ensure a
  full percentage denominator. An input with all undefined ratios makes its gate
  fail, but one undefined seed can silently shrink a primary input's denominator.
  Add explicit expected/defined/undefined pair counts and reject acceptance if a
  required relative metric is undefined, or preregister a zero-objective policy.
  Do not manufacture a percentage gain from zero. Check finite values too.
* `evaluate_holdout.py:35` indexes a bootstrap that can be None if every ratio is
  undefined/invalid. This fails closed with an exception, but loses a completed
  failure decision. Emit rejected/incomplete decisions with reasons instead.
* The summary checks complete key products against the manifest, not against the
  registered external spec. This is sufficient for a trusted unchanged manifest;
  the freeze/spec gate above is needed to prevent a smaller altered design from
  being accepted with all its recorded runs successful.
* Decomposition is recomputed from solution files while the reported quality
  delta uses stored official validator values. Their formulas match, but no
  explicit numerical agreement assertion exists. Add a scale-aware equality
  check and bind solution bytes to each row's saved output hash in final audit.
* `prepare_final.py:26–33` records g++ --version although Makefile permits CXX
  override. Current intended g++ build is sensible, but record the effective
  compiler/flags from the actual build environment/log if reproducibility needs
  to survive a CXX/MAKEFLAGS override. This is not evidence of a wrong compiler.

## Checks that passed by inspection

* Objective is reward minus input distance-matrix distance minus opening costs
  minus balanceCoefficient times max/min task-load spread over opened offices.
  Task load is sum of task-list lengths, not site count. Empty output has zero
  imbalance. This matches task/validate_solution.py:138–147. Cost includes every
  opened office, including an empty office if present.
* Component deltas have raw candidate-minus-base signs, so objective delta equals
  reward delta minus distance delta minus office-cost delta minus penalty delta.
  These are not all positive-is-better contributions. Assignment add/remove/
  reassign and worker differences are correct for validated unique indices.
* Hulls include the office point. Common-office hull counts/area are explicitly
  labeled common-only; opened/closed offices are reported separately. Geometric
  equal-area differences can be zero for distinct line/point hulls, so the
  equals-based changed count is useful and should not be replaced by area alone.
* Paired case/seed keys are complete and unique; affinity must match within pair.
  Failed valid outputs remain visible, clearly labeled, while all-process success
  blocks primary acceptance. Invalid outputs remain rows, not successful gains.
* Relative effect uses abs(baseline), preserving the intended gain sign for a
  negative objective. W/T/L uses a scale-aware 1e-9 tolerance; means and gate
  medians use raw deltas without that tolerance, a conservative minor difference.
* Primary balanced design gives all inputs equal weight in pooled pair mean.
  Bootstrap resamples per-input means with replacement (10,000 draws, fixed RNG),
  not individual correlated solver seeds. Its percentile interval is a descriptive
  input-level interval for this fixed suite, not a hidden-test guarantee.
* Variance rule is sample SD >0.5 percentage points or range >1, evaluated for all
  three declared contrasts. All three variants receive exactly the preregistered
  extra seeds. Strict > thresholds agree with the written rule. No adaptive
  parameter selection is implemented in these scripts.
* Primary criteria implement mean >=0.1%, median >=0, every input median >=0,
  worst >=-1%, input-bootstrap lower bound >=0, and mean vs off >=0. The missing
  cross-budget/extras final reducer is the specific remaining issue.
* prepare_final makes only the declared default-mode substitution and unconditional
  post-tick elapsed/deadline check, with unique-needle assertions. It preserves
  the development source and refuses existing final freeze/candidate directory.
  Default mode is selected explicitly from 5/6. Off overrides that same binary
  with ESCAPE_MODE=0. The resulting holdout binary legitimately differs from
  development and must be evaluated with both exact and off controls.
* Generation refuses an existing holdout input directory and checks source/binary
  freeze before generating. Snapshot observations are not used as independent
  cases. The protocol addendum correctly fixes TL280 to 36 processes/12 blocks;
  TL60 is 108 processes/36 blocks before extras. TL280 reuses six of twelve inputs.

No runtime modifications are requested by this review. The two P1 findings were
sent immediately to the coordinator before this report was saved. Recommendations
concern analysis/provenance gates and can be completed before viewing holdout.
