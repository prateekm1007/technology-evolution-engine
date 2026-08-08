# Protocol A — Lexical Matcher Discrimination

**Status:** DRAFT (not yet authorized)
**Date:** 2026-08-09
**Supersedes:** PREREGISTRATION_SUPERSEDED_DRAFT.md (which was invalid for relationship discrimination)
**Claim limit:** LEXICAL_MATCHER_DISCRIMINATION only

---

## Central Question

> **Can the frozen lexical matcher `_bridge_matches()` distinguish gold bridge strings from bridge strings borrowed from other cases?**

This is NOT a discovery experiment. It is a lexical separability benchmark. It tests whether the matcher's exact/token/synonym matching can tell the difference between the correct bridge and a wrong bridge from a different domain pair.

---

## What This Protocol Does NOT Claim

- It does NOT claim discovery capability
- It does NOT claim cross-domain relationship discrimination
- It does NOT claim the engine can identify bridges from source documents
- It does NOT use M-008 (FP floor) as a decision metric

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

A low FPR_shuffled means the matcher can lexically separate gold bridges from non-gold bridges. This is necessary but NOT sufficient for discovery discrimination.

### Threshold
```
FPR_shuffled ≤ 0.20
```

If FPR_shuffled > 0.20, the matcher cannot even lexically separate bridges, and Protocol B (discovery discrimination) is premature.

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

N=20 null cases. With FPR_shuffled threshold of 0.20:

- If true FPR = 0.10 (10% accidental match rate), the probability of observing ≤ 4/20 matches (FPR ≤ 0.20) is ~0.96 (binomial). Power is adequate.
- If true FPR = 0.25 (25% accidental match rate), the probability of observing ≤ 4/20 matches is ~0.42. Power is inadequate for distinguishing 0.20 from 0.25.

**Classification:** N=20 is sufficient for detecting gross lexical overlap (FPR > 0.40) but exploratory for fine discrimination near the 0.20 threshold.

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
