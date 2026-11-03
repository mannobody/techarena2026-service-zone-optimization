# Independent integration evidence audit

Scope: read-only review of the frozen integration experiment and its stored evidence. No solver benchmarks, runtime/source/log changes, commits or CPU reservations are performed by this audit. Only this audit document is written. Initial inspection: 2026-10-19 07:39:15 UTC. Final results are still pending at this inspection.

## Freeze and provenance

Verified current frozen source SHA256 `c7ae1602c35d8d41d7791bbc8a296b3396675d6e858767c7cb69b0a9dd039366` and binary SHA256 `e0e2aed21d02c91b5b8ddcbc1da2da25d7768c9864f77361d40113e9fb89390c` against FINAL_FREEZE.json and HOLDOUT_PREREGISTRATION.json. Their source/binary identities agree. The baseline remains exact server v4, binary SHA256 `5cc54b6ad0f02a3d6d471d0e2f9129c229b4925aaa2b2c01ce26bd5305a4963c`.

HOLDOUT_GENERATOR_PROVENANCE.json matches the current hashes of tools/gen.py, generate_holdout.py, FINAL_FREEZE.json and HOLDOUT_PREREGISTRATION.json. All12 HOLDOUT_INPUTS.json records match current input bytes and preregistered generator seeds751000+100j in class order. Registration timestamp is07:26:47 UTC; generation provenance timestamp is07:37:44 UTC, after the search CPU release at07:37:43 UTC. generate_holdout.py verifies frozen source and binary hashes before generating and refuses to overwrite its input directory. These are local reproducibility records, not independently timestamped attestations.

The generation script uses the twelve preregistered generator families. The three primary solver seeds are repeated optimization trials on each of12 fresh instances: they are **not36 independent test instances**. TL280 confirmation uses six of the same fresh instances with a fourth solver seed; it is a longer-budget confirmation subset, not another independent generator holdout. Open instances are known development/public data and must remain separately labelled.

## Runner and aggregation review

The runner verifies each input and binary hash immediately before each run, forces NT2/SEED after variant environment overrides, pins solver and Python validator threads, and runs all variants of each(case,seed) block sequentially on the same two logical CPUs. It randomizes block and variant order deterministically. Return code, emergency timeout, actual logged NT, official validator result, error log and wall<=TL+3 are all part of success. A valid checkpoint after nonzero return or timeout is not successful. The TL+10 kill is emergency containment, not the accepted runtime. The accepted TL+3 allowance should remain explicit in final statements about timing.

Shared runner locks are **per destination**, not global CPU locks. They do not prevent simultaneous series on overlapping CPUs. run_final_holdouts.py currently sequences root hybrid280 before confirmation280 and waits for the search release before primary60. OPEN60 uses confirmation CPUs and therefore must also wait for their release. Completed timestamps/affinities should be checked for overlap before claiming exclusivity. Full-machine power/frequency interference is still possible despite logical CPU separation.

summarize.py computes descriptive metrics from successful matched pairs only; it does not itself enforce expected count, uniqueness or COMPLETE counts. COMPLETE existence alone does not mean all runs succeeded. Missing/failed pairs must be explicitly reported, never silently removed from a headline quality claim. This audit therefore independently checks counts, keys, affinities and success fields. Percentage deltas exclude baseline objectives near zero; those pairs remain in W/T/L and raw delta data. Keep `nonzero_reference_pairs` visible if any such cases occur. SD uses sample SD, unlike the search-lab report's descriptive population SD. The per-class ratio of medians and mean paired percentage are different summaries; do not present them as interchangeable.

The freeze's promotion phrase “material regressions” has no numeric threshold. This is not a preregistered quantitative pass/fail test. Report per-instance distributions and worst losses, and describe any promotion judgment as a judgment. A positive overall mean cannot establish a no-regression guarantee or predict the contest server score.

## Initial independent checks

At07:39:15 UTC:

| Series | Recorded / expected runs | Complete pairs | Stored successful | Status |
|---|---:|---:|---:|---|
|hybrid_280|19/24|7|19|Running|
|holdout_primary60|4/72|0|4|Running|
|holdout_confirmation280|0/12|0|0|Not started|
|open60|0/20|0|0|Not started|

For both existing series, every recorded key is unique and belongs to the specification; all complete pairs use identical affinity. Independently reconstructed success conditions pass for every recorded row. Current runner, binary and input hashes match their manifests. No final aggregate inference is made from these partial rows.

### Follow-up methodology review,07:40 UTC

Reviewed run_open_compatibility.py: it explicitly waits for confirmation280 COMPLETE before launching OPEN60 on overlapping root CPUs. The coordinator separately reserves package/tail checks to20/21 after that pair's development block; these are outside the primary holdout CPUs. Shared locks alone still should not be described as cross-series exclusion.

Reviewed the newly prepared finalize_results.py: it now asserts exact run counts, unique keys and equality with the full case×seed×variant product before summarizing. This closes the missing/duplicate-pair risk at finalization. It exposes successful/runs and process-status counts, and labels the12-instance primary holdout and reused confirmation subset correctly. Suggested explicit same-affinity assertions and wall-exceeded/error-log counters as additional guards; success already includes both conditions. These are aggregation/reporting suggestions and do not require a runtime change or a new experiment.

The development order-selection series independently has COMPLETE expected36/completed36/success36; its last solver ended07:22:07 UTC, before registration07:26:47. The currently running development280 and primary60 spec hashes also match their manifests, and both manifest baseline hashes equal the exact server-v4 hash above. This supports the recorded selection chronology; no holdout outcomes were needed to select the frozen order.

## Completed development TL280 audit,07:44 UTC

Verified all24 expected unique rows and12 exact pairs, COMPLETE24/24/24, per-run JSON identity, actualNT2, rc0, no timeout/error log, valid outputs and wall<=283 seconds. Every pair has identical CPU affinity. There are no failed or missing pairs and no zero-reference objectives. Independently recomputed descriptive figures:

```json
{
  "pairs": 12,
  "mean": 0.8896170227881198,
  "median": 0.02974823261601884,
  "min": -0.9609603261525486,
  "max": 4.91009485203447,
  "sample_sd": 1.9381867797719818,
  "wtl": [
    6,
    4,
    2
  ],
  "max_wall": 279.54791561399907,
  "worst": [
    [
      "huge",
      1402,
      -0.9609603261525486
    ],
    [
      "alphabig",
      1403,
      -0.13892554842375718
    ],
    [
      "multiskill",
      1402,
      0.0
    ]
  ]
}
```

This is development evidence on six previously studied instances with two new solver seeds; it must not be described as independent holdout performance.

### Reporting/provenance additions verified,07:49 UTC

The finalizer now asserts identical affinity for every expected pair and separately counts wall_exceeded and error_log, in addition to return/timeout/validation/NT failures. These initial review suggestions are resolved. BUILD_PROVENANCE.json supplies the exact O3/C++17/pthread command, compiler16.2.1 and source/binary identities in a separate record explicitly labelled as recorded after compilation. Its freeze hash matches the original frozen record; no source, binary or original freeze manifest was changed for this addition. The baseline build record uses the same compiler and O3/C++17. Package compilation equivalence is separately documented by the coordinator; this audit does not relaunch compilation.

## Completed holdout TL280 audit,07:52 UTC

All12 expected unique rows/six exact pairs and COMPLETE12/12/12 agree. Current spec/runner/binary/input hashes match the manifest; both binary identities are the frozen intended ones. Per-run JSON agrees with the aggregate. All independent process/runtime/validation/NT checks pass, and every pair uses identical affinity. No failed/missing/zero-reference pairs. Independently recomputed:

```json
{
  "pairs": 6,
  "mean": -0.17647169845382868,
  "median": 0.06837113484918017,
  "min": -2.0007396111170963,
  "max": 0.7988450878029923,
  "sample_sd": 1.0295884744261363,
  "wtl": [
    3,
    0,
    3
  ],
  "by_case": {
    "tightA": -0.015564153427678567,
    "anti": 0.1523064231260389,
    "large": 0.6444658560227445,
    "multiskill": -2.0007396111170963,
    "alphabig": 0.7988450878029923,
    "huge": -0.638143793129973
  },
  "max_wall": 279.5823596419996
}
```

These are six fresh generator instances already included in the primary60 holdout, with one different solver seed at280 seconds. They are not six additional independent holdout inputs.

### Validation environment supplement

At07:55 UTC the official validator file task/validate_solution.py has SHA256 `6dd5948ebe72977976acf1b8dcaf7c819274c79addfb82328c0ec9a012ed56e0`; the repository venv reports Python3.14.7, Pydantic2.14.1 and Shapely2.2.0. This is a current-environment provenance supplement; the original runner manifests do not independently freeze the Python package environment. This audit inspects stored official validation results and their invocation path; it does not rerun a second independent geometric validator or repeat solver benchmarks.

## Final complete audit,07:57 UTC

All four series are complete:128/128 rows and64/64 pairs. Exact expected key products, uniqueness, per-run JSON equality, COMPLETE counts, current source/binary/input/spec/runner provenance, logged actualNT2 and every success predicate were independently checked. All checks pass. No failed/missing pairs were removed from the summaries. No baseline objective is near zero. No two recorded solver-process intervals overlap on any shared logical CPU, either within or across these four series. This interval check concerns these recorded solver processes; it is not a proof that no unrelated system activity occurred.

The original freeze and all hashes recorded at holdout generation still match their current bytes. The two final series independently recompute as follows; the prior two are included for a complete comparison:

```json
{
  "hybrid_280": {
    "runs": 24,
    "pairs": 12,
    "nonzero_reference_pairs": 12,
    "mean": 0.8896170227881198,
    "median": 0.02974823261601884,
    "min": -0.9609603261525486,
    "max": 4.91009485203447,
    "sample_sd": 1.9381867797719818,
    "wtl": [
      6,
      4,
      2
    ],
    "max_wall": 279.54791561399907,
    "cases": {
      "multiskill": {
        "pairs": 2,
        "paired_mean_pct": 0.0,
        "worst_pct": 0.0,
        "median_objective_ratio_pct": 0.0
      },
      "anti": {
        "pairs": 2,
        "paired_mean_pct": 4.9044565206716815,
        "worst_pct": 4.898818189308894,
        "median_objective_ratio_pct": 4.904456217626584
      },
      "large": {
        "pairs": 2,
        "paired_mean_pct": 0.07800091260074951,
        "worst_pct": 0.05949646523203768,
        "median_objective_ratio_pct": 0.07798483882707777
      },
      "tightA": {
        "pairs": 2,
        "paired_mean_pct": 0.0,
        "worst_pct": 0.0,
        "median_objective_ratio_pct": 0.0
      },
      "alphabig": {
        "pairs": 2,
        "paired_mean_pct": 0.2619438537623488,
        "worst_pct": -0.13892554842375718,
        "median_objective_ratio_pct": 0.2619915506707848
      },
      "huge": {
        "pairs": 2,
        "paired_mean_pct": 0.09330084969393881,
        "worst_pct": -0.9609603261525486,
        "median_objective_ratio_pct": 0.059852574530377796
      }
    }
  },
  "holdout_primary60": {
    "runs": 72,
    "pairs": 36,
    "nonzero_reference_pairs": 36,
    "mean": 0.133172914893411,
    "median": 0.0,
    "min": -1.5798764314424136,
    "max": 4.4225454834922,
    "sample_sd": 1.0329702139768602,
    "wtl": [
      14,
      12,
      10
    ],
    "max_wall": 60.42261075500028,
    "cases": {
      "medium": {
        "pairs": 3,
        "paired_mean_pct": 0.07732046397152141,
        "worst_pct": 0.0,
        "median_objective_ratio_pct": 0.0
      },
      "small": {
        "pairs": 3,
        "paired_mean_pct": 0.0,
        "worst_pct": 0.0,
        "median_objective_ratio_pct": 0.0
      },
      "deficit": {
        "pairs": 3,
        "paired_mean_pct": 0.0,
        "worst_pct": 0.0,
        "median_objective_ratio_pct": 0.0
      },
      "alphabig": {
        "pairs": 3,
        "paired_mean_pct": -0.43726495622566297,
        "worst_pct": -0.7483616193664626,
        "median_objective_ratio_pct": -0.47670500082599554
      },
      "anti": {
        "pairs": 3,
        "paired_mean_pct": 0.7790904690603722,
        "worst_pct": 0.009902469969554874,
        "median_objective_ratio_pct": 0.009902469969554874
      },
      "multiskill": {
        "pairs": 3,
        "paired_mean_pct": -0.9616805692615985,
        "worst_pct": -1.4967198869562883,
        "median_objective_ratio_pct": -1.161532460292658
      },
      "large": {
        "pairs": 3,
        "paired_mean_pct": -0.301294969830613,
        "worst_pct": -0.5809627184478506,
        "median_objective_ratio_pct": -0.3927400783715023
      },
      "cluster": {
        "pairs": 3,
        "paired_mean_pct": 2.1342971581832066,
        "worst_pct": 0.42696254028587394,
        "median_objective_ratio_pct": 1.597781336669966
      },
      "alphazero": {
        "pairs": 3,
        "paired_mean_pct": -0.4189254182659507,
        "worst_pct": -1.5798764314424136,
        "median_objective_ratio_pct": 0.031618855584869085
      },
      "huge": {
        "pairs": 3,
        "paired_mean_pct": 0.05494598327739901,
        "worst_pct": 0.0,
        "median_objective_ratio_pct": 0.005140762460666378
      },
      "tightA": {
        "pairs": 3,
        "paired_mean_pct": 0.671586817812258,
        "worst_pct": -0.10404560634004088,
        "median_objective_ratio_pct": 0.9026789569051737
      },
      "grid": {
        "pairs": 3,
        "paired_mean_pct": 0.0,
        "worst_pct": 0.0,
        "median_objective_ratio_pct": 0.0
      }
    }
  },
  "holdout_confirmation280": {
    "runs": 12,
    "pairs": 6,
    "nonzero_reference_pairs": 6,
    "mean": -0.17647169845382868,
    "median": 0.06837113484918017,
    "min": -2.0007396111170963,
    "max": 0.7988450878029923,
    "sample_sd": 1.0295884744261363,
    "wtl": [
      3,
      0,
      3
    ],
    "max_wall": 279.5823596419996,
    "cases": {
      "tightA": {
        "pairs": 1,
        "paired_mean_pct": -0.015564153427678567,
        "worst_pct": -0.015564153427678567,
        "median_objective_ratio_pct": -0.015564153427678567
      },
      "anti": {
        "pairs": 1,
        "paired_mean_pct": 0.1523064231260389,
        "worst_pct": 0.1523064231260389,
        "median_objective_ratio_pct": 0.1523064231260389
      },
      "large": {
        "pairs": 1,
        "paired_mean_pct": 0.6444658560227445,
        "worst_pct": 0.6444658560227445,
        "median_objective_ratio_pct": 0.6444658560227445
      },
      "multiskill": {
        "pairs": 1,
        "paired_mean_pct": -2.0007396111170963,
        "worst_pct": -2.0007396111170963,
        "median_objective_ratio_pct": -2.0007396111170963
      },
      "alphabig": {
        "pairs": 1,
        "paired_mean_pct": 0.7988450878029923,
        "worst_pct": 0.7988450878029923,
        "median_objective_ratio_pct": 0.7988450878029923
      },
      "huge": {
        "pairs": 1,
        "paired_mean_pct": -0.638143793129973,
        "worst_pct": -0.638143793129973,
        "median_objective_ratio_pct": -0.638143793129973
      }
    }
  },
  "open60": {
    "runs": 20,
    "pairs": 10,
    "nonzero_reference_pairs": 10,
    "mean": -0.08796921458835483,
    "median": 0.0,
    "min": -4.519008853532915,
    "max": 3.6393167076493667,
    "sample_sd": 1.9318580949073578,
    "wtl": [
      1,
      8,
      1
    ],
    "max_wall": 59.874195070000496,
    "cases": {
      "inst1": {
        "pairs": 2,
        "paired_mean_pct": 0.0,
        "worst_pct": 0.0,
        "median_objective_ratio_pct": 0.0
      },
      "inst4": {
        "pairs": 2,
        "paired_mean_pct": -0.43984607294177414,
        "worst_pct": -4.519008853532915,
        "median_objective_ratio_pct": -0.5130107121554108
      },
      "inst2": {
        "pairs": 2,
        "paired_mean_pct": 0.0,
        "worst_pct": 0.0,
        "median_objective_ratio_pct": 0.0
      },
      "inst3": {
        "pairs": 2,
        "paired_mean_pct": 0.0,
        "worst_pct": 0.0,
        "median_objective_ratio_pct": 0.0
      },
      "inst0": {
        "pairs": 2,
        "paired_mean_pct": 0.0,
        "worst_pct": 0.0,
        "median_objective_ratio_pct": 0.0
      }
    }
  }
}
```

## Audit verdict

The completed comparison is internally consistent and reproducible from the recorded artifacts. The initial aggregation concerns were resolved by explicit finalizer guards; no completeness, identity, affinity or process-status defect remains in these128 records. None of the data-quality checks supports discarding the negative outcomes.

The full hybrid has **not demonstrated robust superiority over exact v4**. Primary60 gains only+0.13317% on average, with median0 and10 losing pairs; TL280 confirmation has negative mean−0.17647%, including a−2.00074% multiskill loss. Open60 also retains a−4.51901% pair. These are compatible with useful monotone checkpoint operators and a faster exact kernel, because the integrated wall-time trajectory can enter a different basin or spend its budget differently. The data do not establish which component caused each loss. Do not promote the whole combination as a reliable v4 replacement or describe positive development averages as the held-out result.

A defensible final claim is: substantial research produced validated local mechanisms and explained several limitations, but the frozen full solver did not establish broad non-regression. Preserve the exact v4 comparator and the frozen candidate/negative results. Any later runtime change needs a new freeze and fresh independent inputs; the present holdout must then be treated as development evidence.

Final cross-check: integration/FINAL_RESULTS.json matches this independent recomputation for all four aggregate distributions, W/T/L, pair/success counts, affinities and per-class mean/min/ratio-of-medians figures to1e-12 tolerance. No statistical transcription discrepancy was found.

## Separate inst4 variance follow-up audit,08:00 UTC

The additional8/8 runs are complete and valid with four exact pairs, unchanged frozen source/binary intent, matching spec/runner/input/binary hashes, actualNT2, rc0 and accepted wall times. Every per-run row equals its aggregate row. All four new seeds1604–1607 started after the07:57:16 follow-up registration. This diagnostic was selected **after** seeing the original inst4 outcomes; it was preregistered before its new measurements, not part of the original holdout plan.

Pooling the original two and four new seeds gives six distinct paired seeds on **one known instance**:

```json
{
  "paired_seed_count": 6,
  "paired_mean_pct": 0.7125373574687807,
  "paired_median_pct": 0.544035446049429,
  "ratio_of_medians_pct": 0.17861231030746738,
  "sample_sd_pct": 3.188838591173732,
  "min_pct": -4.519008853532915,
  "max_pct": 4.40963428109411,
  "wtl": [
    4,
    0,
    2
  ],
  "per_seed_pct": {
    "1602": 3.6393167076493667,
    "1603": -4.519008853532915,
    "1604": 0.7302070826661211,
    "1605": 4.40963428109411,
    "1606": 0.35786380943273693,
    "1607": -0.342788882496736
  }
}
```

The pooled mean is positive, but the range and SD remain substantial. The different seeds were run on different CPU pairs; within-pair comparisons are controlled, but the pooled spread mixes solver-seed and execution/hardware variation. It is not a pure estimate of seed variance. This characterizes observed performance variation on inst4; it does not remove either original observation, convert the example into independent holdout data, or overturn the mixed twelve-instance primary and negative-mean TL280 confirmation. The original128 runs and additional8 remain separate accounting categories.

INST4_POOLED6.json agrees with the independent pooled recomputation above for every paired percentage and all reported distribution metrics. Audit complete; no runtime or experiment logs were changed.
