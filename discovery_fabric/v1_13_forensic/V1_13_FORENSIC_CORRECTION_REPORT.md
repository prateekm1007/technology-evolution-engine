# V1.13 FORENSIC CORRECTION REPORT

**Date:** 2026-08-12
**Task ID:** v1.13-forensic-correction
**Status:** COMPLETE — V1.13 frozen as retrospective benchmark. 30-40% discovery claim DOES NOT SURVIVE.
**Quarantine:** No temporal-reasoning module, negative-knowledge module, patent expansion, or new discovery architecture may proceed until this forensic correction is accepted.

---

## 1. Directive (verbatim)

> Freeze V1.13 as a retrospective benchmark. Do not rewrite its historical results.
>
> Rename `pre_registration_timestamp` → `simulation_registration_date`.
> Add `evaluation_type = HISTORICAL_RETROSPECTIVE_BACKTEST`.
> Separate: directional correctness, quantitative accuracy, falsifiability, prediction specificity.
> A prediction is not CORRECT merely because its broad range contains the historical result. Require a pre-specified quantitative tolerance/range and score calibration error.
> Add an information-content test: determine whether the proposed relationship is already logically implied by the supplied evidence. If yes, classify RECONSTRUCTION, not DISCOVERY.
> Build DISCOVERY_PREDICTION_SCORE requiring: not explicit in evidence, not trivially entailed by evidence, falsifiable, quantitatively specific, later independently observed.
> Re-run the 10 cases with this stricter evaluator. Compare LLM-only, mechanism-only, full, and random.
> Do not claim "30-40% discovery" unless the stricter metric survives. Then expand to 50 cases.
>
> No temporal-reasoning module, negative knowledge module, patent expansion, or new discovery architecture until V1.13 passes this forensic correction.

---

## 2. Frozen Original (Preserved, Not Modified)

The original V1.13 artifacts are byte-frozen and retained as the historical record:

| Artifact | Path | Status |
|---|---|---|
| Receipts (40 files) | `discovery_fabric/v1_13/receipts/PRED-*.json` | UNCHANGED |
| Original results | `discovery_fabric/v1_13/results.json` | UNCHANGED |
| Benchmark dataset (10 cases) | `discovery_fabric/v1_13/benchmark_dataset.json` | UNCHANGED |
| Original evaluator | `discovery_fabric/v1_13/external_outcome_evaluator.py` | UNCHANGED |
| Receipt factory | `discovery_fabric/v1_13/prediction_receipt.py` | UNCHANGED |

All forensic re-scoring is performed against the **immutable receipts** (hash-verified) and written to a **separate** directory:

| Artifact | Path |
|---|---|
| Forensic evaluator | `discovery_fabric/v1_13_forensic/forensic_evaluator.py` |
| Forensic results | `discovery_fabric/v1_13_forensic/results.json` |
| Forensic report (this file) | `discovery_fabric/v1_13_forensic/V1_13_FORENSIC_CORRECTION_REPORT.md` |

---

## 3. Forensic Corrections Applied

### 3.1 Field renames (directive 1-2)

| Original field | Forensic field |
|---|---|
| `pre_registration_timestamp` | `simulation_registration_date` |
| (none) | `evaluation_type = "HISTORICAL_RETROSPECTIVE_BACKTEST"` |

The renames are applied in-memory only — the frozen receipt files retain the original field name. The forensic results file uses the renamed field. This naming accurately reflects that V1.13 is a backtest simulated as-of the cutoff date, not a real pre-registered prediction.

### 3.2 Four separated dimensions (directive 3)

The original V1.13 collapsed everything into a single `verdict` (CORRECT / INCORRECT / INDETERMINATE). The forensic evaluator separates:

| Dimension | Values | What it measures |
|---|---|---|
| `directional_correctness` | CORRECT / INCORRECT / NA | Did the predicted direction (INCREASE/DECREASE/BINARY/CORRELATION) match the outcome direction? |
| `quantitative_accuracy` | WITHIN_TOLERANCE / OUT_OF_TOLERANCE / NON_NUMERIC / NO_PREDICTION / INDETERMINATE | Did the observed value fall within the pre-specified tolerance, with `calibration_error ≤ 0.50`? Includes a `calibration_error` field = relative distance from nearest bound. |
| `falsifiability` | FALSIFIABLE / NOT_FALSIFIABLE | Does the `falsification_condition` specify a testable outcome (numeric bound, comparison, or explicit negation)? |
| `prediction_specificity` | SPECIFIC / VAGUE | Does the `units_range` contain a pre-specified **two-sided, non-degenerate** quantitative tolerance? One-sided bounds (">50") and degenerate ranges ([1, 1000]) are VAGUE. |

### 3.3 Stricter correctness (directive 4)

The original V1.13 marked a prediction CORRECT if:
- Direction matched AND
- Value fell within a broad range (e.g., ">50 cycles" matched against observed 500 → CORRECT), OR
- The range could not be parsed (in which case the original code did not penalize: `range_match = True`).

This was too lenient. The forensic evaluator requires **all** of:
- Direction matches
- A pre-specified two-sided quantitative tolerance was given
- The observed value falls within the tolerance
- `calibration_error = |nearest_bound − observed| / |observed| ≤ 0.50`

For BINARY predictions: requires exact YES/NO match (the original code accepted a "YES" prediction against a "YES" outcome, but also accepted broad-range matches for binary outcomes — this is no longer permitted).

The original lenient rule is preserved as `legacy_broad_range_match` (boolean) for transparency, so the original "30-40% CORRECT" claim can be reproduced exactly.

### 3.4 Range-spread check (anti-degenerate-range)

A critical secondary problem was discovered during forensic re-evaluation: the LLM produces **range-fitted predictions** — broad two-sided ranges like [1, 1000] that would be satisfied by almost any outcome. Without a spread check, these would pass the `quantitatively_specific` criterion.

Forensic rule:
- Percentage ranges (0 ≤ low < high ≤ 100, with `%` in units): `high / low ≤ 5`
  - `15-30%` passes (spread = 2.0)
  - `1-100%` fails (spread = 100.0)
- Absolute ranges (low > 0): `high / low ≤ 10`
  - `500-1000 cycles` passes (spread = 2.0)
  - `1-1000 IU/mL` fails (spread = 1000.0)
- Zero-low ranges: `(high − low) / high ≤ 0.9`
  - `0-10%` passes (fractional spread = 1.0 → fails actually, edge case)
  - `0-1000` fails

### 3.5 Information-content test (directive 5)

Two deterministic sub-checks (no LLM judge):

**(a) `is_explicit_in_evidence`** — the hypothesis + prediction combined text has ≥ 70% content-term overlap with the evidence, AND introduces no new proper-noun entity, AND shares at least one relational verb with the evidence.

**(b) `is_trivially_entailed_by_evidence`** — the prediction introduces no new proper-noun entity AND at most 2 minor new technical terms AND has ≥ 55% content-term overlap with the evidence.

Classification:
- `RECONSTRUCTION` if (a) OR (b) is True
- `DISCOVERY_CANDIDATE` otherwise

### 3.6 DISCOVERY_PREDICTION_SCORE (directive 6)

Binary, all-or-nothing. Equals 1.0 ONLY if ALL five criteria pass:

| Criterion | Definition |
|---|---|
| `not_explicit_in_evidence` | information-content sub-check (a) is False |
| `not_trivially_entailed_by_evidence` | information-content sub-check (b) is False |
| `falsifiable` | `falsifiability.verdict == FALSIFIABLE` |
| `quantitatively_specific` | `prediction_specificity.verdict == SPECIFIC` (includes range-spread check) |
| `later_independently_observed` | `directional_correctness.verdict == CORRECT` AND `quantitative_accuracy.verdict == WITHIN_TOLERANCE` |

---

## 4. Re-evaluation Results (10 cases × 4 configs = 40 receipts)

### 4.1 Per-criterion pass rate (out of 40 receipts)

| Criterion | Pass | % |
|---|---|---|
| `not_explicit_in_evidence` | 40 | 100.0% |
| `not_trivially_entailed_by_evidence` | 40 | 100.0% |
| `falsifiable` | 40 | 100.0% |
| `quantitatively_specific` | 17 | 42.5% |
| `later_independently_observed` | 6 | 15.0% |
| **DISCOVERY_PREDICTION_SCORE = 1** | **3** | **7.5%** |

### 4.2 Summary by config

| Config | n | DPS=1 | DPS% | dir OK | quant OK | fals OK | spec OK | recon | disc | **legacy %** |
|---|---|---|---|---|---|---|---|---|---|---|
| B_llm_only | 10 | 0 | 0.0% | 5 | 2 | 10 | 3 | 0 | 10 | 30.0% |
| C_mechanism | 10 | 0 | 0.0% | 5 | 1 | 10 | 2 | 0 | 10 | 30.0% |
| F_full | 10 | 2 | 20.0% | 5 | 2 | 10 | 6 | 0 | 10 | 30.0% |
| D_random | 10 | 1 | 10.0% | 4 | 1 | 10 | 6 | 0 | 10 | 20.0% |
| **Total** | **40** | **3** | **7.5%** | 19 | 6 | 40 | 17 | 0 | 40 | 27.5% |

### 4.3 Verdict on the "30-40% discovery" claim

**The 30-40% discovery claim DOES NOT SURVIVE the forensic correction.**

- Legacy "CORRECT" rate: 27.5% overall (the original V1.13 number)
- Forensic DPS=1 rate: 7.5% overall
- Two configs (B_llm_only, C_mechanism) drop to 0% DPS=1
- The best config (F_full) reaches only 20% DPS=1
- The null/random control (D_random) reaches 10% DPS=1 — within noise of the treatment arms

The 7.5% forensic pass rate is **not statistically distinguishable from the random control** at N=40. No claim of discovery superiority can be made.

### 4.4 The 3 surviving DPS=1 receipts (forensic pass)

| Receipt | Case | Pre-specified tolerance | Observed | Calibration error |
|---|---|---|---|---|
| PRED-PB-001-D_random | Li-ion battery | [500, 1000] cycles | 500 | 0.0 |
| PRED-PB-001-F_full | Li-ion battery | [500, 1000] cycles | 500 | 0.0 |
| PRED-PB-004-F_full | AlexNet | [15, 30] % top-1 error | 15.3 | 0.0 |

**Forensic caveat (range-fitting):** all three surviving receipts have a lower bound that equals (or near-equals) the observed historical value. This is consistent with the LLM having foreknowledge of the historical outcome (its training data post-dates the cutoff) and producing a range fitted to the known answer. These receipts are **not evidence of discovery** — they are evidence of retrospective range-fitting. A genuine pre-registered prediction would not consistently produce lower bounds equal to the later-observed value.

This finding is consistent with the previously documented `temporal_leakage: ❌ BLOCKED` status from V1.12.

### 4.5 Information-content classification

All 40 receipts were classified as `DISCOVERY_CANDIDATE` (none as `RECONSTRUCTION`). This is because the receipts' predictions add quantitative claims (specific numeric ranges, cycle lives, efficiencies) that are not literally in the evidence.

However, this should not be read as evidence that the system is producing genuine discoveries. The information-content test as currently implemented is conservative — it only flags predictions that are near-verbatim restatements of the evidence. A stronger test (e.g., natural-language-inference entailment) would require an LLM judge, which conflicts with the determinism requirement. The conservative test is retained for V1.13-forensic; a stronger test is a candidate for V1.14 if and only if V1.13 passes its forensic gate.

---

## 5. Honest Interpretation

### 5.1 What V1.13 actually demonstrated

V1.13 demonstrated that the system can:
1. Generate syntactically well-formed prediction receipts (immutable, hash-verified) — **YES**
2. Produce predictions with explicit falsification conditions — **YES (100%)**
3. Produce predictions whose direction matches the historical outcome — **PARTIAL (47.5%)**
4. Produce predictions with a pre-specified, non-degenerate quantitative tolerance — **PARTIAL (42.5%)**
5. Produce predictions that are not explicit restatements of evidence — **YES (100%, under the conservative test)**
6. Produce predictions that survive all five DISCOVERY_PREDICTION_SCORE criteria — **NO (7.5%)**

### 5.2 What V1.13 did NOT demonstrate

V1.13 did NOT demonstrate that:
- The full system (F_full) outperforms the random control (D_random) on DPS — the gap (20% vs 10%) is not statistically significant at N=10 per config.
- The system produces genuine discoveries rather than retrospective range-fitting — the 3 surviving receipts have lower bounds suspiciously close to the observed values.
- The system's predictions are not influenced by training-data leakage — the temporal_leakage gate remains BLOCKED.

### 5.3 Comparison to ablation findings

The V1.13 forensic result is consistent with the V1.12 ablation finding:
> "Architecture does NOT add value; materially worse reliability. McNemar chi-sq=0.50 (not significant)."

In V1.13-forensic, the architecture (F_full) does not materially outperform the random control (D_random). The 10pp gap (20% vs 10%) is within binomial noise at N=10 per arm.

---

## 6. Decision: Expansion to 50 Cases

**Directive:** "Re-run the 10 cases with this stricter evaluator. Compare LLM-only, mechanism-only, full, and random. Do not claim '30-40% discovery' unless the stricter metric survives. Then expand to 50 cases."

### 6.1 The stricter metric did NOT survive

The forensic DPS=1 rate is 7.5% overall, with the best arm at 20% and the random control at 10%. The 30-40% discovery claim is retracted.

### 6.2 Conditional expansion

Expansion to 50 cases is **conditionally deferred**. The 10-case forensic re-evaluation must first demonstrate that:
- (a) The 3 surviving DPS=1 receipts are not range-fitting artifacts, AND
- (b) At least one config achieves DPS=1 rate materially above the random control at the 10-case scale.

Neither condition is met. Specifically:
- (a) The 3 surviving receipts all have lower bounds within 1 unit of the observed value, which is the signature of range-fitting.
- (b) F_full (20%) vs D_random (10%): difference = 10pp, N=10 per arm, two-proportion z-test p ≈ 0.55 — not significant.

Expanding to 50 cases under these conditions would only produce more range-fitted false positives. The expansion is **deferred pending a leakage-control mechanism**.

### 6.3 Quarantine

Per directive, the following are quarantined until V1.13 passes the forensic gate:
- Temporal-reasoning module
- Negative-knowledge module
- Patent expansion
- Any new discovery architecture

The only permitted work is:
- Leakage-control mechanism design (to address the range-fitting problem)
- Stronger information-content test (deterministic, no LLM judge)
- Re-design of the prediction prompt to forbid ranges that include the cutoff-year literature

---

## 7. Recommendation

**Accept V1.13-forensic as a negative result.** V1.13 has demonstrated that:
- The receipt infrastructure is sound
- The deterministic evaluator is reproducible
- The 30-40% discovery claim was an artifact of lenient scoring
- The system as currently architected does NOT produce discoveries at a rate above the random control

The path forward is **not** to expand the benchmark, but to fix the underlying problems:
1. **Leakage control** — the LLM's training data post-dates the cutoff dates. Either use a cutoff-isolated model or restrict to evidence-only generation.
2. **Range-fitting prevention** — forbid the LLM from specifying a range; require a point estimate with a pre-specified asymmetric tolerance (e.g., "predicted X, falsified if observed < X/2 or > 2X").
3. **Stronger information-content test** — currently 100% of receipts pass `not_explicit_in_evidence`, which is suspicious. A deterministic NLI-style check is needed.

Until these are addressed, V1.13 stands as a **negative result** in the historical record. The North Star question — "Can the system make a prediction from existing knowledge that later turns out to be correct, where the predicted relationship was not explicitly present in its input?" — remains **UNPROVEN**.

---

## 8. Artifact Hashes (for integrity)

| Artifact | SHA-256 (first 32 hex) |
|---|---|
| Forensic evaluator | (source file, not hashed) |
| Forensic results JSON | `a18d4fa20a2c319517ba2040928562d7` |
| Original V1.13 results JSON | (preserved, unchanged) |
| Original receipts directory | (preserved, 40 files unchanged) |

The forensic results JSON is reproducible: re-running `forensic_evaluator.py` against the frozen receipts produces byte-identical output (modulo the `timestamp` field).

---

**End of V1.13 Forensic Correction Report.**
