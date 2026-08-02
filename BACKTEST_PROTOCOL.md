# BACKTEST_PROTOCOL — Phase 8A

**Status:** constitutional document (backtest methodology).
**Location:** repo root.
**Phase:** 8A.

This document defines the mechanics of the frozen-time backtest. It
extends HISTORICAL_VALIDATION_PROTOCOL.md (Phase 7D) with the
validation contract from VALIDATION_CONSTITUTION.md.

---

## 1. The backtest procedure

```text
Step 1: Freeze the graph at year T.
        Only nodes/edges with validFrom <= T are visible.

Step 2: Generate predictions.
        For each reachable combination of capabilities at T,
        compute Readiness, Novelty, and Feasibility.
        Rank the combinations.

Step 3: Record predictions.
        Every prediction is recorded BEFORE the outcome is known.
        No retrospective filtering.

Step 4: Wait until T+n (n = 5 to 10 years).

Step 5: Evaluate outcomes.
        For each predicted combination:
          - Did it actually appear? (true positive or false positive)
          - Did combinations the model DIDN'T predict appear?
            (false negative)

Step 6: Record failures.
        Every false positive and false negative is recorded in
        evidence/failures/ per Phase 8B.

Step 7: Explain failures.
        For each failure, identify which assumption or principle
        was violated. Per Phase 8C (counterfactual protocol).

Step 8: Adversarial review.
        Every prediction (success and failure) is reviewed by
        4 roles per Phase 8D.
```

---

## 2. Backtest points

```text
T = 1995, 2000, 2005, 2010, 2015, 2020
n = 5 to 10 years after T
```

At each T, the system's knowledge is restricted to data available
at T. Predictions are ranked possibilities. Validation is outcomes
at T+n.

---

## 3. Required metrics

```text
precision    = true_positives / (true_positives + false_positives)
recall       = true_positives / (true_positives + false_negatives)
false_positives  = flagged but didn't happen
false_negatives  = happened but weren't flagged
specificity  = true_negatives / (true_negatives + false_positives)
calibration  = predicted probability vs observed frequency
```

### Minimum thresholds for provisional validation

| Metric | Minimum |
|---|---|
| Precision | > CO_OCCURRENCE_MODEL precision |
| False positives | < CO_OCCURRENCE_MODEL false positives |
| Recall | > 0 (at least one true positive) |
| Calibration | predicted ≈ observed within 20% |

If the minimum thresholds are not met, the model is NOT provisionally
validated. The validation contract (VALIDATION_CONSTITUTION.md) is
not satisfied.

---

## 4. Forbidden methodology

```text
inventor hindsight
post hoc reasoning
manual cherry-picking
transistor stories
retrospective explanations
```

Per HISTORICAL_VALIDATION_PROTOCOL.md (Phase 7D), these are
forbidden. The backtest must use ONLY data available at T, make
predictions BEFORE outcomes are known, and report ALL predictions
(not just successful ones).

---

## 5. What distinguishes this from Phase 7D

Phase 7D defined the methodology. Phase 8A binds it to the validation
contract. The difference:

- Phase 7D: "here's how to run the backtest."
- Phase 8A: "here's what the backtest results mean for the model's
  validity, and here are the conditions under which the model is
  validated or invalidated."

The backtest is the instrument. The validation constitution is the
standard against which the instrument's results are judged.
