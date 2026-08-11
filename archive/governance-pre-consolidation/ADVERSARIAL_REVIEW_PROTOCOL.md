# ADVERSARIAL_REVIEW_PROTOCOL — Phase 8D

**Status:** constitutional document (adversarial review).
**Location:** repo root.
**Phase:** 8D.

> Every prediction must survive an attack.
> — CEO directive, Phase 8D

This document defines the four reviewer roles that every prediction
must pass before it is considered validated. A prediction that
survives only one perspective is not trusted. It must survive four.

---

## The four roles

### Reviewer A — Builder

**Perspective:** "Does this prediction follow from the model's
structure? Are the edges, principles, and assumptions correctly
applied?"

**What the Builder checks:**
- Is the provenance chain complete? (observation → principle →
  assumption → evidence → edge → prediction)
- Are the correct edge types used? (no suspended types)
- Is the confidence level appropriate for the evidence type?
- Are the principles in scope for this prediction?

**What the Builder does NOT check:** whether the prediction is
correct — only whether it was DERIVED correctly from the model.

### Reviewer B — Skeptic

**Perspective:** "What's wrong with this prediction? What evidence
contradicts it? What assumptions are most likely wrong?"

**What the Skeptic checks:**
- Which assumptions (A-001 through A-005) does this prediction
  depend on? Can any be challenged?
- Are there false positives the model would also produce?
- Is the confidence calibration correct? (High confidence on
  uncertain predictions.)
- What would a pattern matcher say? (If the CO_OCCURRENCE_MODEL
  would make the same prediction, the CAPABILITY_MODEL adds no
  value.)

**What the Skeptic does NOT check:** whether the model is
structurally correct — only whether THIS prediction is trustworthy.

### Reviewer C — Historian

**Perspective:** "Has this combination been attempted before? What
happened? Does the historical record support or contradict the
prediction?"

**What the Historian checks:**
- Is there a historical precedent for this combination?
- Did it succeed or fail historically?
- If it failed, why? Does the model account for the failure mode?
- If it succeeded, was it for the reasons the model predicts?

**What the Historian does NOT check:** the model's internal
consistency — only its correspondence to historical reality.

### Reviewer D — Domain expert

**Perspective:** "Is this physically/economically/regulatorily
plausible? Would a practitioner in this field consider this
prediction reasonable?"

**What the Domain expert checks:**
- Does the prediction violate any known physical law not in the
  model's principles?
- Are the constraints correctly applied? (Is the cost threshold
  right? Is the regulation still in force?)
- Are there domain-specific factors the model missed? (Supply
  chain, geopolitical, infrastructure.)
- Would a battery engineer, an economist, or a regulator agree
  with this prediction?

**What the Domain expert does NOT check:** the model's architecture
— only the domain-level plausibility.

---

## The review process

```text
Prediction is made.
     ↓
Reviewer A (Builder) checks derivation.
     ↓
Reviewer B (Skeptic) challenges assumptions.
     ↓
Reviewer C (Historian) checks historical precedent.
     ↓
Reviewer D (Domain expert) checks plausibility.
     ↓
ALL FOUR must approve for the prediction to be VALIDATED.
If ANY reviewer rejects, the prediction is FLAGGED.
```

A prediction that passes all 4 reviews is provisionally validated
(subject to outcome verification at T+n). A prediction that fails
any review is flagged for revision.

---

## What this document does NOT do

- It does NOT define who the reviewers are (they can be the same
  person wearing different hats, or different people).
- It does NOT define the backtest mechanics (that's BACKTEST_PROTOCOL.md).
- It defines the REVIEW STANDARD: no prediction is trusted unless
  it survives attack from 4 perspectives.
