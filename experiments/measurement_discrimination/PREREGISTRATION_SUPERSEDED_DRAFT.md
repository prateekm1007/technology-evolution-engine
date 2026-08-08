# Phase 8 Preregistration: Matcher Discrimination Study

**Status:** PREPARED (not yet authorized for execution)
**Date:** 2026-08-09
**Author:** Repository coder
**Reviewer:** External audit (pending)

---

## Central Question

> **Can the frozen discovery matcher discriminate between true cross-domain relationships and matched null controls at a rate significantly above chance?**

This is NOT asking whether the matcher achieves a good F1. It is asking whether the matcher's discrimination ability is statistically distinguishable from a matched null baseline.

---

## 1. Frozen Matcher Identity (Amendment 1)

### Matcher specification

The frozen matcher is `_bridge_matches()` defined in `benchmarks/discovery_capability_benchmark.py` at commit `9189880` (the freeze point). The matcher combines:

1. **Exact match**: canonicalized string equality
2. **Token overlap**: substring + shared token (≥4 chars)
3. **Synonym lookup**: `BRIDGE_SYNONYMS` map (currently empty since cycle 270)

### Matcher commit
```
commit: 9189880fde1496ceba9f0c4f242ab65cb7303711
file: benchmarks/discovery_capability_benchmark.py
function: _bridge_matches (line 71)
sha256: 9ba196603e90f5fb83e5bf1f10cf7c7523357b725b107c72afcede0642adc547
```

### Matcher configuration
- `BRIDGE_SYNONYMS = {}` (empty, frozen since cycle 270)
- `canonicalize()` function (frozen)
- No fuzzy matching in the frozen matcher (fuzzy match threshold 0.85 exists in bootstrap_statistics.py and dr91_audit.py but NOT in the production `_bridge_matches()`)

### Read-only enforcement (Amendment 1)
The matcher is READ-ONLY during the discrimination study. The discrimination harness:
- IMPORTS the frozen matcher
- CALLS it through its existing public interface
- RECORDS the exact matcher commit, configuration, and thresholds
- DOES NOT edit, modify, or calibrate the matcher

### Required provenance
```json
{
  "matcher_commit": "9189880fde1496ceba9f0c4f242ab65cb7303711",
  "matcher_file": "benchmarks/discovery_capability_benchmark.py",
  "matcher_function": "_bridge_matches",
  "matcher_source_sha256": "9ba196603e90f5fb83e5bf1f10cf7c7523357b725b107c72afcede0642adc547",
  "matcher_configuration": {
    "bridge_synonyms": "{}",
    "canonicalization": "canonicalize() in discovery_capability_benchmark.py",
    "fuzzy_threshold": "N/A (not in production matcher)"
  },
  "harness_commit": "to_be_set_at_freeze",
  "dataset_sha256": "to_be_set_at_freeze"
}
```

---

## 2. Frozen Vocabulary / Entity Pool (Amendment 2)

### L3 — Single-hop synonym

**Vocabulary source:** `BRIDGE_SYNONYMS = {}` (empty, frozen at commit `9189880`)

```json
{
  "level": "L3",
  "vocabulary_source": "benchmarks/discovery_capability_benchmark.py:68",
  "vocabulary_version": "cycle-270-empty",
  "vocabulary_sha256": "44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a",
  "created_before_gold_access": true,
  "gold_derived": false
}
```

### L4 — Domain-semantic matching

**Model:** No semantic embedding model is used in the frozen production matcher. The matcher uses only exact/token/synonym matching. L4 is NOT applicable to the current frozen matcher.

```json
{
  "level": "L4",
  "model": "N/A",
  "model_version": "N/A",
  "similarity_metric": "N/A",
  "threshold": "N/A",
  "internet_access": false,
  "gold_data_access": false,
  "gold_derived_vocabulary": false,
  "training_corpus_independence": "N/A (no embedding model used)",
  "residual_leakage_risk": "N/A (no embedding model used)"
}
```

---

## 3. Frozen Gold Set

### Gold set specification

The gold set is `GOLD_DISCOVERIES` defined in `benchmarks/discovery_capability_benchmark.py` at commit `9189880`. It contains 20 cross-domain published bridges (DISC-GOLD-001 through DISC-GOLD-020).

```json
{
  "gold_set_source": "benchmarks/discovery_capability_benchmark.py:105-328",
  "gold_set_commit": "9189880fde1496ceba9f0c4f242ab65cb7303711",
  "gold_set_sha256": "1ed102361bdccd8fa0beed77e44b8600a2a36746904d0d249c686931bd761191",
  "gold_set_count": 20,
  "frozen": true
}
```

---

## 4. Control / Null Construction (Amendments 8, 9, 10)

### True cases
The 20 `GOLD_DISCOVERIES` entries. Each has:
- `literature_a`: source text from domain A
- `literature_b`: source text from domain B
- `bridge`: the published cross-domain bridge concept
- `published_relation`: the known relationship

### Shuffled null (matched null)
For each gold discovery, create a shuffled version by:
1. Taking the bridge concept from a DIFFERENT gold entry
2. Pairing it with the original source texts
3. The shuffled bridge should NOT match the original bridge
4. The shuffled pair preserves document length, domain distribution, token count, and structural complexity

**Control generation algorithm:**
```
for each gold[i]:
    shuffled_bridge = gold[(i + offset) % 20].bridge
    where offset = 10 (fixed, preregistered)
    if shuffled_bridge == gold[i].bridge:
        shuffled_bridge = gold[(i + 7) % 20].bridge  # fallback offset
    create null_case[i] with gold[i].source_a, gold[i].source_b, shuffled_bridge
```

**Control seed:** 42 (preregistered)
**Control dataset SHA-256:** to be computed after generation and recorded

### Control quality audit (Amendment 9)
The shuffled control must preserve:
- document length (±10%)
- token count (±10%)
- domain distribution (same domains)
- node count (same entity pool)
- graph size (same structural complexity)

If any null case violates these matching properties, label the experiment:
```
INCONCLUSIVE — INVALID NULL
```

---

## 5. Candidate Generation Procedure

### True candidate set
For each gold discovery, the candidate is the gold bridge concept itself. The matcher is asked: "does the matcher identify this bridge as a match for the source texts?"

### Null candidate set
For each shuffled null, the candidate is the shuffled bridge concept. The matcher is asked: "does the matcher identify this shuffled bridge as a match for the source texts?"

### Scoring procedure
The frozen `_bridge_matches(expected_bridge, candidate)` function is called for each (source, candidate) pair. The function returns True (match) or False (no match).

The scoring is INDEPENDENT of the matcher — the harness calls the matcher and records the output. The harness does NOT implement its own matching logic.

---

## 6. Primary Discrimination Metric (Amendment 4)

### Definition
```
Δ = TPR_true − FPR_shuffled
```

where:
- `TPR_true` = true-positive rate = (matched true bridges) / (total true bridges)
- `FPR_shuffled` = false-positive rate = (matched shuffled bridges) / (total shuffled bridges)

### Preregistered threshold
```
Δ_min = 0.20
```

The threshold 0.20 was chosen BEFORE any results were visible. It represents a minimum practically meaningful discrimination: the matcher must identify true bridges at least 20 percentage points more often than shuffled bridges.

### Primary success condition
```
Δ ≥ 0.20
AND
the lower bound of the pre-specified 95% confidence interval for Δ is > 0
```

---

## 7. Secondary Criteria

### Precision separation
```
Precision_true − Precision_shuffled ≥ P_min
```
where `P_min = 0.15` (preregistered)

### False-positive ceiling
```
FPR_shuffled ≤ FPR_max
```
where `FPR_max = 0.30` (preregistered)

---

## 8. Statistical Procedure (Amendment 5)

### Confidence interval method
```
95% percentile bootstrap CI
10,000 resamples
resampling at case level (not observation level)
fixed preregistered seed: 42
```

### Random seed policy
- Candidate generation seed: 42
- Control generation seed: 42
- Bootstrap seed: 42
- All seeds preregistered before execution

### Unit of resampling
Case level (each of the 20 gold cases is a unit). Resampling with replacement at the case level preserves within-case dependence structure.

### Treatment of repeated observations
Each case produces exactly one observation (match/no-match). No repeated observations per case.

### Handling of ties
Ties (same TPR and FPR) produce Δ = 0. The lower bound of the CI will be ≤ 0, failing the success condition.

### Missing-value policy
No missing values expected (the matcher always returns True or False). If the matcher crashes on a case, the case is recorded as "no match" (conservative).

---

## 9. Sample Size

```
N = 20 true cases + 20 shuffled controls = 40 total observations
```

This is the existing `GOLD_DISCOVERIES` set. No new cases are generated.

---

## 10. Multiple-Comparison Policy

Only ONE primary comparison is tested: `Δ ≥ 0.20`. No multiplicity correction is needed.

Secondary criteria (precision separation, FP ceiling) are exploratory and reported with CIs but not used for the primary decision.

---

## 11. Stopping Rule

The experiment runs to completion (all 40 observations). There is no early stopping.

---

## 12. Decision Rule (Amendment 15, 16)

### DISCRIMINATIVE
```
Δ ≥ 0.20
AND
lower bound of 95% CI for Δ > 0
AND
FPR_shuffled ≤ 0.30
```

### NOT_DISCRIMINATIVE
```
Δ < 0.20
OR
lower bound of 95% CI for Δ ≤ 0
```

### Terminal handling for NOT_DISCRIMINATIVE
- The result is recorded as `NOT_DISCRIMINATIVE`
- No semantic synonyms are added
- No thresholds are changed
- No hard cases are removed
- The null is not altered
- The metric is not reinterpreted
- The experiment is not rerun until favorable
- The result is NOT called "promising"
- Discovery claims remain BLOCKED (Amendment 16)

---

## 13. DXP-005 Resumption Conditions

DXP-005 may resume ONLY if ALL of the following are true:

1. The discrimination study produces `DISCRIMINATIVE`
2. ZAI provider is available (HTTP 429 resolved)
3. The frozen protocol (`66b3212`) is still valid
4. The ground truth (`db2df3ec...`) is still valid
5. No protocol parameters are changed
6. P46 served-instrument verification is satisfied (the ZAI CLI response includes both `model` and `provider` fields)

If the discrimination study produces `NOT_DISCRIMINATIVE`:
- DXP-005 is permanently abandoned (Amendment 15)
- The partial state is preserved as a historical record
- No discovery claims may be made on the basis of DXP-005 results

---

## 14. Adversarial Attack Matrix

Before execution, the following attacks on the protocol design must be addressed:

### A. Vocabulary leakage
**Risk:** The matcher's vocabulary (BRIDGE_SYNONYMS) could contain gold-derived synonyms.
**Mitigation:** BRIDGE_SYNONYMS is empty (frozen since cycle 270). No gold-derived vocabulary exists. Verified by `tests/test_no_gold_derived_synonyms.py`.

### B. Control contamination
**Risk:** Shuffled controls could accidentally differ from true candidates in ways that bias the result.
**Mitigation:** The shuffled null uses a fixed offset (10) with a fallback (7). The control quality audit (Section 4) verifies that nulls preserve document length, token count, domain distribution, and structural complexity.

### C. Candidate generation encoding the answer
**Risk:** The candidate generation procedure could encode information about whether a case is true or null.
**Mitigation:** The candidate is simply the bridge string (true or shuffled). The matcher receives only the string — no metadata about whether it's a true or null case.

### D. Ordering leaking condition identity
**Risk:** The order of cases could leak whether a case is true or null.
**Mitigation:** Cases are processed in a fixed order (gold[0], null[0], gold[1], null[1], ...). The matcher does not see the order — it receives one (source, candidate) pair at a time.

### E. Scorer seeing unavailable information
**Risk:** The scorer could have access to information the matcher doesn't.
**Mitigation:** The scorer IS the matcher. The harness calls `_bridge_matches()` and records the output. No separate scoring layer exists.

### F. Repeated entities creating dependence
**Risk:** If the same entity appears in multiple gold cases, observations could be dependent.
**Mitigation:** Resampling is at the case level (not observation level). The bootstrap CI accounts for within-case dependence. Cross-case dependence is a known limitation, documented in the results.

### G. Null distribution contamination
**Risk:** The shuffled null could accidentally create a true bridge (the shuffled bridge could actually be a valid cross-domain connection for the source texts).
**Mitigation:** The shuffled bridge comes from a different gold entry's domain pair. The probability of accidental validity is low. If a shuffled bridge is found to be a valid connection, the case is flagged and excluded from analysis (with the exclusion recorded).

### H. Provider/model identity leaking
**Risk:** The matcher's behavior could depend on which LLM/provider was used to generate the entities.
**Mitigation:** The frozen matcher (`_bridge_matches`) is a pure string-matching function. It does NOT call any LLM. No provider identity can leak into the matcher's output.

### I. RNG state creating condition-dependent artifacts
**Risk:** The RNG used for shuffling could create systematic patterns.
**Mitigation:** The RNG seed is preregistered (42). The shuffle algorithm is deterministic and documented. The same seed produces the same null set every time.

### J. Statistical decision rule manufacturing significance
**Risk:** The threshold (Δ ≥ 0.20) or CI method could be chosen post-hoc to produce significance.
**Mitigation:** The threshold and CI method are PREREGISTERED in this document BEFORE any results are visible. The threshold is not derived from the data.

### K. Direct invocation bypassing the scientific gate
**Risk:** Someone could call the matcher directly without going through the discrimination harness.
**Mitigation:** The discrimination harness IS the direct invocation. The harness calls the frozen matcher through its public interface. The epistemic gate (Phase 6) blocks any scientific consumer that doesn't pass through the eligibility check.

### L. Future operator changing frozen inputs
**Risk:** A future operator could modify GOLD_DISCOVERIES or BRIDGE_SYNONYMS without detection.
**Mitigation:** The F1 freeze gate (Phase 7) maintains SHA-256 hashes of all frozen artifacts and verifies them at runtime. Any modification is detected and blocked.

---

## 15. Lock File (Amendment 6)

The following files must be committed BEFORE the gold set is opened for execution:

```
experiments/measurement_discrimination/
    PREREGISTRATION.md          (this file)
    protocol.json               (machine-readable protocol)
    protocol.sha256             (SHA-256 of protocol.json)
    matcher_manifest.json       (frozen matcher identity)
    vocabulary_manifest.json    (frozen vocabulary provenance)
    dataset_manifest.json       (frozen gold set identity)
    controls_manifest.json      (frozen control construction)
```

The execution script must refuse to run if any of these files are absent.

---

## 16. What This Preregistration Does NOT Authorize

- Executing the discrimination study (requires separate audit authorization)
- Executing DXP-005 (requires DISCRIMINATIVE verdict + ZAI availability + P46)
- Modifying the frozen matcher
- Modifying the gold set
- Modifying BRIDGE_SYNONYMS
- Repairing M-008
- Making any discovery claim
- Making any capability claim

---

## Status

```
PREPARED — awaiting audit authorization to freeze and execute
```
