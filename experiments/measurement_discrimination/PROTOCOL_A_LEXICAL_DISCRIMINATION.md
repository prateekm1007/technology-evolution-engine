# Protocol A — Lexical Matcher Selectivity Gate

**Status:** DRAFT (not yet authorized)
**Date:** 2026-08-09
**Supersedes:** PREREGISTRATION_SUPERSEDED_DRAFT.md (which was invalid for relationship discrimination)
**Claim limit:** LEXICAL_SELECTIVITY only (NOT discovery, NOT relationship discrimination)

---

## Experimental Validity Assessment (audit round 26)

### Can Protocol A produce an informative measurement given TPR_true = 1.0 by construction?

**Yes, but only as a gatekeeping test — not as a discrimination measurement.**

Because TPR_true = 1.0 by construction, the headline metric Δ = TPR - FPR reduces to (1.0 - FPR). The experiment effectively measures FPR_shuffled alone. This is still informative:

- **If FPR_shuffled is high (near 1.0):** The matcher matches everything — it has no lexical selectivity. Protocol B (where the system generates candidates) would be uninterpretable because the scorer cannot distinguish correct from incorrect candidates. Protocol B is premature.
- **If FPR_shuffled is low (near 0.0):** The matcher has lexical selectivity — it does not match arbitrary strings. This is a necessary precondition for Protocol B: the scoring function can distinguish correct from incorrect candidates at the lexical level.

**What Protocol A does NOT establish:**
- It does NOT prove the matcher discriminates true cross-domain relationships (the matcher never sees relationships — only two strings)
- It does NOT prove the discovery engine can identify bridges from source documents
- It does NOT validate the discovery pipeline
- Perfect lexical selectivity (FPR=0.0) does NOT imply discovery capability

### Why Protocol A is still worth running

Protocol A is a **necessary precondition** for Protocol B, not a substitute for it:

```
Protocol A (lexical selectivity gate)
    ↓
FPR_shuffled ≤ 0.20 → scorer has lexical selectivity → Protocol B may proceed
FPR_shuffled > 0.20 → scorer is too permissive → Protocol B is premature
```

Without Protocol A, Protocol B's results would be uninterpretable: if the scorer matches everything, we cannot tell whether the system's output is correct or incorrect.

### Metric reduction (honest)

Because TPR_true = 1.0 by construction:
```
Δ = TPR_true - FPR_shuffled = 1.0 - FPR_shuffled
```

The experiment reduces to measuring FPR_shuffled. The preregistration should NOT present Δ as a two-sided discrimination metric. The primary measured variable is FPR_shuffled.

---

## Central Question

> **Does the frozen lexical matcher `_bridge_matches()` have sufficient lexical selectivity to serve as a scoring function for Protocol B?**

This is a gatekeeping test. It determines whether the scoring infrastructure is ready for discovery discrimination testing (Protocol B), not whether discovery discrimination exists.

---

## What This Protocol Does NOT Claim

- It does NOT claim discovery capability
- It does NOT claim cross-domain relationship discrimination
- It does NOT claim the engine can identify bridges from source documents
- It does NOT use M-008 (FP floor) as a decision metric
- It does NOT validate the discovery pipeline
- TPR_true = 1.0 by construction — this is documented, not hidden

---

## Experimental Design

### True cases (N=20)
For each gold discovery:
```
expected_bridge = gold.bridge
candidate = gold.bridge
result = _bridge_matches(expected_bridge, candidate)
```

**Note:** TPR_true is 1.0 by construction (the candidate IS the expected bridge). This is documented, not hidden.

### Null cases (N=20)
For each gold discovery:
```
expected_bridge = gold.bridge
candidate = gold[(i + offset) % 20].bridge  (shuffled)
result = _bridge_matches(expected_bridge, candidate)
```

The null tests whether a bridge from a different domain pair accidentally matches the expected bridge via substring or token overlap.

### What is measured
- FPR_shuffled = fraction of null cases where the shuffled bridge accidentally matches
- TPR_true = 1.0 (by construction — documented, not a discovery claim)

### Primary metric
```
FPR_shuffled
```

**Note:** Because TPR_true = 1.0 by construction, Δ = TPR - FPR reduces to (1 - FPR). The primary measured variable is FPR_shuffled. The experiment does NOT present Δ as a two-sided discrimination metric.

A low FPR_shuffled means the matcher can lexically separate gold bridges from non-gold bridges. This is necessary but NOT sufficient for discovery discrimination.

### Threshold
```
FPR_shuffled ≤ 0.20
```

If FPR_shuffled > 0.20, the matcher cannot lexically separate bridges, and Protocol B (discovery discrimination) is premature.

---

## Decision Rule (Exhaustive Partition)

```text
IF null_validity == FAILED:
    INCONCLUSIVE_INVALID_NULL

ELSE IF FPR_shuffled ≤ 0.20:
    LEXICALLY_SEPARABLE

ELSE:
    NOT_LEXICALLY_SEPARABLE
```

Every possible outcome maps to exactly one state.

---

## Null Validity (Preregistered, Before Results)

Before running the matcher, verify that for each null case:
1. The shuffled bridge is different from the true bridge (string inequality after canonicalization)
2. The shuffled bridge comes from a different gold entry (index ≠ i)

If ANY null case fails these checks:
```text
NULL_VALIDITY = FAILED
EXPERIMENT = INCONCLUSIVE_INVALID_NULL
NO CASE EXCLUSION
NO REPAIR
NO REPLACEMENT
```

---

## Power Justification

**Mechanically reproducible calculation:** See `protocol_a_power.json` (generated by `scripts/protocol_a_power_calculation.py`). The calculation uses exact binomial CDF — no simulation, no RNG, no timestamp. Running the script twice from identical source produces identical JSON bytes and identical SHA-256 values (verified).

### Hashing convention
- `calculation_content_sha256` — SHA-256 of the calculation payload (all fields except the hashes themselves), using canonical JSON: `sort_keys=True, separators=(",", ":")`
- `artifact_sha256` — SHA-256 of the final artifact (including content_sha but not itself), using the same canonical serialization

### Key results (exact binomial, N=20, threshold ≤ 4/20)

| True FPR | P(LEXICALLY_SEPARABLE) | Interpretation |
|---|---|---|
| 0.00 | 1.0000 | Perfect matcher — always classified as separable |
| 0.05 | 0.9974 | Excellent matcher — 99.7% probability |
| 0.10 | 0.9568 | Good matcher — 95.7% probability (≥80%) |
| 0.15 | 0.8298 | Adequate matcher — 83.0% probability (≥80%) |
| 0.20 | 0.6296 | Threshold — 63.0% probability (marginal) |
| 0.25 | 0.4148 | Marginal — 41.5% probability (inadequate) |
| 0.50 | 0.0059 | Random — 0.6% (excellent Type I control) |

### Type I error (P(false LEXICALLY_SEPARABLE) under H0)

| H0: FPR | P(false LEXICALLY_SEPARABLE) |
|---|---|
| 0.30 | 0.2375 |
| 0.40 | 0.0510 |
| 0.50 | 0.0059 |

### Classification

```
ADEQUATE_FOR_DETECTING_FPR_0.10
```

If the true null-case FPR is 0.10, the probability that the preregistered rule observes ≤4/20 false matches and therefore classifies the matcher as LEXICALLY_SEPARABLE is 0.9568. The experiment can confidently distinguish a good lexical matcher from random (Type I error = 0.0059 under H0: FPR=0.50).

However, if the true FPR is exactly 0.20 (the threshold), the probability of classification as LEXICALLY_SEPARABLE is only 0.6296. This means the experiment is **adequate for detecting good matchers** (FPR ≤ 0.15) but **marginal for distinguishing the threshold itself** (FPR = 0.20).

**Honest classification:** N=20 is adequate for detecting gross lexical overlap (FPR > 0.40) and good matchers (FPR ≤ 0.15), but exploratory for fine discrimination near the 0.20 threshold.

---

## STRUCTURAL_MATCHING vs INFORMATION_VISIBLE_TO_SCORER

### STRUCTURAL_MATCHING_OF_CASES
- Document length: matched (same source documents)
- Domain distribution: matched (same domain pairs)
- Token count: matched (same source texts)

### INFORMATION_VISIBLE_TO_SCORER
The scorer (`_bridge_matches`) sees ONLY:
- `expected_bridge` (string)
- `candidate` (string)

It does NOT see:
- Source documents
- Domain labels
- Entity pools
- Graph structure
- Document length
- Token count

The structural matching properties are irrelevant to the scorer's decision. They are documented for completeness but do not affect the measured variable.

---

## What This Protocol Authorizes If PASSED

If the result is `LEXICALLY_SEPARABLE`:
- The matcher can distinguish gold bridges from non-gold bridges at the lexical level
- Protocol B (discovery discrimination) may be designed and preregistered
- NO discovery claim is made
- NO capability claim is made

If the result is `NOT_LEXICALLY_SEPARABLE`:
- The matcher cannot even lexically separate bridges
- Protocol B is premature
- The measurement substrate needs fundamental repair before any discovery experiment

---

## Lock File

```
experiments/measurement_discrimination/
    PROTOCOL_A_LEXICAL_DISCRIMINATION.md   (this file)
    protocol_a.json                         (machine-readable)
    protocol_a.sha256                       (SHA-256)
```

---

## Status

```
DRAFT — awaiting audit authorization
```
