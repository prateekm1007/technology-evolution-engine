# IMPOSSIBILITY_CRITERIA — Phase 9D

**Status:** constitutional document (when the theory fails).
**Location:** repo root.
**Phase:** 9D.

> You have defined success. Now define failure.
> — CEO directive, Phase 9D

This document defines the conditions under which the CAPABILITY_MODEL
theory is considered FAILED — not just "needs improvement," but
fundamentally wrong. If any criterion is met, the theory is impossible
within its current form.

---

## The impossibility criteria

### IC-001: Cannot outperform the null model

```text
If the CAPABILITY_MODEL cannot outperform the NULL_MODEL (random selection)
on precision, the theory fails.
```

**Why:** If the model can't beat random, it's not adding signal. The
CPC-to-capability mapping and structural edges are noise, not signal.
The theory's core claim (capabilities + constraints → reachable
possibilities) is false.

### IC-002: Cannot transfer between domains

```text
If the CAPABILITY_MODEL cannot transfer between domains (electrochemical
→ photovoltaics), the theory fails.
```

**Why:** If the method only works in one domain, it's overfit to
that domain. The architectural pivot from CO_OCCURRENCE to CAPABILITY
hasn't captured a general principle — it's captured a domain-specific
pattern.

### IC-003: Cannot explain its own outputs

```text
If the CAPABILITY_MODEL cannot explain its own outputs (trace every
prediction to observations, principles, and assumptions), the theory
fails.
```

**Why:** A model that predicts but can't explain is a black box.
The entire architecture was built on the principle that provenance
(trust) is the asset. If the provenance chain breaks, the model is
no better than embedding similarity.

### IC-004: Ontology complexity grows faster than explanatory power

```text
If the ontology (node types, edge types, capabilities, constraints)
grows faster than the model's explanatory power (precision, recall,
calibration), the theory fails.
```

**Why:** This is the "ontology explosion → collapse" failure mode.
If adding more capabilities, constraints, or edge types doesn't
improve predictions, the model is accumulating complexity without
value. The ONTOLOGY_FREEZE.md caps exist to prevent this; if the
caps are exceeded without explanatory gain, the freeze was wrong
and the theory can't be saved by more structure.

### IC-005: Cannot reproduce results

```text
If the same input produces different output across runs, the theory
fails.
```

**Why:** Reproducibility is Law 8 (verification standard). If the
model is non-deterministic (e.g., because of embedding randomness,
LLM non-determinism, or temporal data drift), its predictions are
not verifiable. The model is not a scientific instrument — it's
a random number generator with good marketing.

### IC-006: Assumptions proven wrong without model revision

```text
If an assumption is falsified (per its falsification criterion) but
the model is not updated, the theory fails.
```

**Why:** The stress tests (Phase 9A) already falsified 4 of 5
assumptions. If the model continues operating with falsified
assumptions, it's ignoring evidence. A model that ignores its own
falsification is dogma, not science.

### IC-007: False positive rate exceeds CO_OCCURRENCE_MODEL

```text
If the CAPABILITY_MODEL's false positive rate exceeds the
CO_OCCURRENCE_MODEL's false positive rate, the theory fails.
```

**Why:** The architectural pivot was justified by the claim that
the CAPABILITY_MODEL would produce fewer false positives (typed,
evidence-backed edges vs. co-occurrence). If it doesn't, the pivot
hasn't paid off.

---

## What happens when a criterion is met

If any IC-xxx is met:

1. The theory is declared FAILED.
2. H0 (the CO_OCCURRENCE_MODEL is sufficient) is reinstated.
3. The failure is recorded in CEMETERY.md (Phase 9E).
4. The model's scope is narrowed to what it CAN do (if anything).
5. The CEO decides whether to revise the theory or abandon it.

---

## Current status

| Criterion | Status |
|---|---|
| IC-001 (beat null model) | NOT YET TESTED (backtest not run) |
| IC-002 (transfer domains) | NOT YET TESTED (second vertical not authorized) |
| IC-003 (explain outputs) | SURVIVED (provenance chain is complete for 37 edges) |
| IC-004 (complexity vs. power) | SURVIVED (ontology frozen; no growth) |
| IC-005 (reproduce results) | SURVIVED (deterministic; no embeddings/LLMs) |
| IC-006 (falsified assumptions unupdated) | AT RISK (4/5 assumptions failed stress tests; model not yet updated) |
| IC-007 (FP rate) | NOT YET TESTED (backtest not run) |

**The most immediate risk is IC-006:** 4 of 5 assumptions were
falsified in Phase 9A, but the model has not yet been updated. If
the model continues operating with falsified assumptions, IC-006
is met and the theory fails. The model MUST be updated (assumptions
retired, edges corrected, scope narrowed) before any backtest.
