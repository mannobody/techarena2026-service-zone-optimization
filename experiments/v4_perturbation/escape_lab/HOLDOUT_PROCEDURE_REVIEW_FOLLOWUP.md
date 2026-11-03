# Read-only follow-up after analysis fixes

Static source review only, 2026-10-19; no tests/solver/analyzer/compile executed.
The runtime was not edited. CPU allocations remain released.

## Resolved by inspection

* P1 mandatory extras/process gate: finalize_holdout now requires every recorded
  primary and extension process successful, preserves primary_criteria_pass,
  computes combined input-weighted means and input bootstrap, and combines both
  budgets. Favorable extras cannot rescue a failed primary decision.
* Candidate/off source and binary are now checked against FINAL_FREEZE before
  every primary/extension stage and at analysis; variant env matches freeze.
  Makefile and generation chronology/freeze hash are checked; exact v4 source
  and binary hashes are fixed. This resolves the previously unbound solver
  identity, assuming the fixed baseline binary hash is the intended build.
* P2 zero-denominator acceptance: expected and finite-defined percentage counts
  gate primary/final acceptance. A missing bootstrap now yields false rather
  than indexing None. Nonfinite pathological data can still raise inside the
  descriptive analyzer before these gates, but cannot silently pass acceptance.

## Remaining P1: design completeness is checked only against mutable specs

verify_freeze checks each listed case against HOLDOUT_INPUTS but does not require
exact registered seconds, seeds or primary case set. finalize_holdout checks that
an extension spec exists when reasons are nonempty, but not that its cases equal
all triggered reasons or its seeds equal the registered two extras. A shortened
spec can be fully complete relative to its own manifest and still pass.

Before any runs, assert TL60 is exactly all 12 registered classes × seeds
2101/2102/2103 and seconds=60; TL280 is exactly anti/tightA/alphabig/multiskill/
cluster/huge ×2201/2202 and seconds=280. Extension cases must equal the primary
variance_extension_reasons keys, with 2104/2105 or2203/2204 respectively; no
unexpected extension when reasons are empty. Continue requiring all three variants.
The current generator creates these correct designs, so this is an enforcement
gap, not evidence that actual generated designs are wrong or runs were omitted.

## Remaining labeling/protocol details

* freeze_and_record_hash_checks_pass=True overstates the implemented check.
  analyze still checks current source/binary/input hashes, not output bytes,
  validator/runner identities or row success recomputation. Parent explicitly
  requires a separate final record audit/contract before recommendation: either
  gate that audit here, or rename this field to solver/input identity and make
  FINAL_DECISION clearly a statistical gate pending the mandatory audit. A note
  already says passing still requires final contract/record audit; retain it.
* The finalizer additionally applies quality thresholds to combined data. This
  is conservative and was introduced before holdout, but HOLDOUT_ANALYSIS_RULES.md
  should explicitly record that extra final condition before data generation,
  including input-weighted mean versus pooled pair median/worst, so it is not
  mistaken for an outcome-dependent change later.
* No actual final compiled candidate/contract is certified by this code review.
  Those remain separate and mandatory, as stated by the coordinator.

The remaining design-completeness issue was sent immediately to the coordinator.
