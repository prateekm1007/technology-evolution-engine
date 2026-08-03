# RIVAL_MODEL_PROTOCOL — Phase 9C

**Status:** scientific instrument (competing models).
**Location:** repo root.
**Phase:** 9C.

> You currently possess only one explanatory model. That is dangerous.
> Create competing models.
> — CEO directive, Phase 9C

## The four models

### Model A — CO_OCCURRENCE_MODEL

**Claim:** Inventions are predicted by shared vocabulary between components.

**Method:** Extract component labels from patents via keyword matching.
Compute co-occurrence (shared labels). Rank by convergence score.

**Strengths:** Simple, deterministic, no domain knowledge required.

**Weaknesses:** Co-occurrence ≠ enablement. Saturated at
d(shared)/d(total) = 0.00. Cannot distinguish "premature" from
"impossible."

**Status:** BASELINE (Phase 5 architecture, preserved at v4.2).

---

### Model B — CAPABILITY_MODEL

**Claim:** Inventions are predicted by reachable combinations of typed capabilities under constraints.

**Method:** Map CPC codes to capabilities. Create evidence-backed
edges (EMBODIED_IN, REQUIRES, CONSTRAINS, REGULATED_BY). Compute
Readiness, Novelty, Feasibility. Rank reachable combinations.

**Strengths:** Typed, evidence-backed, separates observation from
model, falsifiable assumptions, scoped principles.

**Weaknesses:** Small corpus (5 patents). 4/5 assumptions failed
stress tests. Scope is narrower than claimed (Li-ion, not all
electrochemical storage).

**Status:** UNDER INVESTIGATION (Phase 7-9 architecture).

---

### Model C — NULL_MODEL

**Claim:** Random selection performs just as well as either model.

**Method:** Randomly select N combinations from the set of all
possible capability combinations. Rank randomly. Compare precision
and recall to Models A and B.

**Strengths:** The ultimate baseline. If Models A or B can't beat
random, they add no value.

**Weaknesses:** Doesn't explain anything. But that's the point —
if the CAPABILITY_MODEL can't beat random, it's not adding signal.

**The null model asks:**
> Would random selection perform just as well?

**Status:** NOT YET IMPLEMENTED. Must be run before any model claims
validity. If Model B doesn't beat Model C, Model B is invalid.

---

### Model D — EXPERT_MODEL

**Claim:** A domain specialist performs better than the machine.

**Method:** Give a battery engineer the same 5 patents. Ask them
to predict which capability combinations will become reachable
in T+5 to T+10 years. Compare their predictions to the machine's
predictions and to actual outcomes.

**Strengths:** Human domain knowledge is deep, contextual, and
intuitive. An expert may catch factors the model misses (supply
chain, geopolitics, company strategy).

**Weaknesses:** Not reproducible (different experts give different
answers). Not scalable. Subject to hindsight bias.

**The expert model asks:**
> Would a domain specialist perform better than the machine?

**Status:** NOT YET IMPLEMENTED. Requires a human domain expert.
The comparison is: if Model B (CAPABILITY_MODEL) doesn't beat
Model D (EXPERT), the machine isn't adding value over a human.

---

## The comparison framework

| Criterion | Model A (CO_OCCURRENCE) | Model B (CAPABILITY) | Model C (NULL) | Model D (EXPERT) |
|---|---|---|---|---|
| Precision | Measured (Phase 5 baseline) | Not yet measured | 1/N (random) | Not yet measured |
| Recall | Measured | Not yet measured | 1/N (random) | Not yet measured |
| Reproducibility | High (deterministic) | High (deterministic) | High (seeded) | Low (human) |
| Interpretability | Low (co-occurrence ≠ causality) | High (evidence-backed) | N/A | High (human explains) |
| Scalability | High | Medium | High | Low |
| Explanatory power | Low | Medium-High | None | High |

## The rivalry rule

A model is only VALIDATED if it beats ALL competing models on the
CEO's success criteria (precision, false positives, interpretability,
reproducibility, explanatory power).

If Model B beats Model A but not Model C (random), Model B is
not validated — it's doing worse than chance.

If Model B beats Model C but not Model D (expert), Model B is
not validated — a human is better.

Model B must beat A, C, AND D to be validated. Until then, it
is PROVISIONAL.

---

## What this document does NOT do

- It does NOT implement any model (all are defined, not built).
- It does NOT run the comparison (the backtest is not yet executed).
- It defines the RIVALRY: which models compete, what criteria they
  compete on, and what it means to win.
