# V7 packaging read-only review

Reviewed 2026-10-19T09:41:29.702077+00:00. Script SHA256 `a36bda588ca7eccaf0ff9b25b980546c8357fc03dcc6ef8dac0bfe0cbceb66d1`.
No command in package_v7.py was executed. No compilation, solver, validator or
CPU test was started; concurrent TL280 work is untouched. This is a static
review, not a claim that the archive has already been built or validated.

## Verdict

No blocking issue found in the proposed packaging flow. It meets the requested
scope: a new v7 submission artifact without changing the frozen algorithm,
overwriting previous releases, uploading, or performing Git operations.
Packaging is explicitly separated from recommending replacement of v4.

## Checked behavior

* Requires completed holdout pipeline, completed decision-with-audit and report
  before creating the package. Current frozen source and binary hashes must match
  FINAL_FREEZE. The upstream decision combines statistical gates, contract and
  record audit; a failed gate yields experimental/not-recommended labeling.
* `experiments/server_v7` is created with exist_ok=False. Earlier v4/v6 artifacts
  and the original frozen Makefile/source are only read. The new Makefile adapts
  server targets, without modifying C++ source: make build compiles main.cpp via
  g++ -O3 -std=c++17 -pthread; make run executes NT=2 ./solution.
* ZIP is created exclusively, contains exactly main.cpp and Makefile at root,
  has a successful CRC test required, and each extracted file must equal package
  bytes. Build takes place in the fresh extraction directory. Rebuilt executable
  must be byte-identical to the independently tested frozen binary before it is
  described as verified. This is stronger than a source-only reproducibility
  assertion; any toolchain/link/build-environment difference causes a hard stop.
* The frozen source uses instance.json and solution.json with no arguments;
  default TL is280 and frozen mode is5, matching the hardcoded README description.
  The diagnostic threads line is unconditional, so DBG-unset smoke can verify NT2.
* Smoke runs make run from the extracted package with a sanitized environment,
  TL1, two-core affinity, process-group timeout, official validation and explicit
  rc0/no-timeout/wall<=4/actualNT2 checks. Its one-site fixture is a valid existing
  contract input. This checks the adapter and no-argument server entry point;
  it does not claim full-length DBG0 quality equivalence. README explicitly says
  quality comparisons used DBG1 and DBG0 stability is not established.
* Provenance records archive/source/Makefile/rebuilt-binary hashes, freeze identity,
  whole final decision, contract summary and actual make-run smoke evidence.
  Negative criteria produce conspicuous experimental wording and no replacement
  recommendation. No network, upload, stage, commit or push commands are present.

## Nonblocking operational notes

1. The ZIP is written before build/smoke verification and before README/provenance.
   If the script aborts, that ZIP and partial directory remain for diagnosis;
   they must not be handed out as verified. Announce/link the finished artifact
   only after successful script completion and complete PROVENANCE.json. A rerun
   intentionally refuses the existing directory, so inspect failures instead of
   deleting or silently overwriting them.
2. Run this packaging only when the coordinator releases CPU14,15 after TL280.
   The packaging subprocesses themselves do not acquire shared benchmark locks.
   This review has not used those CPUs and does not authorize contention.
3. README's policy description is correct for current FINAL_FREEZE.default_mode=5.
   It is intentionally specific to this frozen v7 and should not be reused for a
   hypothetical different default without updating artifact metadata.
4. Compilation/official validation must use the intended environment (repository
   venv for Python validator dependencies). A missing dependency, compile failure,
   binary mismatch or smoke failure must remain a packaging failure, not be
   bypassed to obtain the ZIP. The script currently fails closed on these paths.

All recommendations are packaging/provenance handling, not runtime changes.
Final ZIP hashes and observed build/smoke outcomes belong in the coordinator's
completion report once the script actually succeeds.
