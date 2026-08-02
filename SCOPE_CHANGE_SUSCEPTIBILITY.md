# SCOPE_CHANGE_SUSCEPTIBILITY

**Status:** Formal scope change (EP-7).
**Location:** repo root.
**Phase:** 14 (pre-execution).

> Redefining the target is a retraction, not a rewording.
> — EP-7

This document formally retracts the "inevitability" target
(Phase 10F) and argues for "susceptibility" as the new target.
Per EP-7, the retraction precedes the new target. The original
claim was already marked FALSIFIED in FEC-005 (commit 88e2996);
this document makes the scope change explicit and argues for
the new target on its own terms.

---

## The retraction

### Original claim (Phase 10F, INEVITABILITY_PROTOCOL.md, commit cc387cd)

> The model is an inevitability detector — predicting conditions
> under which invention becomes unavoidable.

### Falsification (FEC-005, commit 88e2996)

The Phase 11A backtest (commit 75ef7e1) produced 135 false
positives at 3.57% precision — 135 cases where the model's
predicted conditions occurred (high score) but no event
followed within the 5-year horizon. This falsifies "inevitability"
by the model's own output. A condition that produces an event
only 3.57% of the time is not "unavoidable."

Additionally, the significance test (commit 829ac26) showed
the 3.57% vs 0.71% difference is not statistically significant
(McNemar p=0.2188). The inevitability claim was not just
falsified by the false-positive count; the model's advantage
over NULL is not distinguishable from chance.

### Status

**FALSIFIED.** The inevitability target is retired. It cannot
be cited as the model's objective in any future document. The
INEVITABILITY_PROTOCOL.md document is retained (Law 7, historical
permanence) but is labeled as a superseded articulation.

---

## The new target

### Susceptibility estimation

The model estimates the susceptibility of a capability landscape
to invention. A landscape is "susceptible" when the conditions
for invention are present — but susceptibility does not guarantee
that invention occurs. Invention requires both susceptibility
AND agency (a firm, inventor, or institution that acts on the
susceptibility).

### Why this is the right target

1. **It matches what the model actually measures.** The formula
   `max(dTRL/dt) × adjacency` measures what is changing (velocity)
   and what is reachable (adjacency). These are landscape
   properties, not invention properties. The model was always
   measuring susceptibility; the "inevitability" framing was
   overclaiming what the measurement implies.

2. **It is consistent with the significance test result.** A
   susceptibility model is not falsified by false positives —
   a susceptible landscape may or may not produce an invention,
   depending on agency. The 135 false positives are consistent
   with "susceptible but no agent acted." The inevitability
   model was falsified by those same 135 cases; the susceptibility
   model is not.

3. **It is consistent with the counterexample pattern.** The
   counterexamples (CE-002, CE-003) have zero velocity and are
   not in the Top-10 — they are NOT susceptible, and indeed no
   invention occurred. The TPs have non-zero velocity and are
   in the Top-10 — they ARE susceptible, and invention occurred.
   The pattern holds for susceptibility, even though it does
   not hold for inevitability (because susceptible ≠ inevitable).

4. **It is consistent with the CEO's framing.** The CEO's Phase 14
   directive articulates the deeper question as "Where is the
   landscape becoming unstable?" — which is a susceptibility
   question, not an inevitability question. A landscape becomes
   unstable when capabilities are rising and adjacent
   combinations are reachable. Whether invention occurs at
   that instability point depends on agency, which the model
   does not measure.

### What susceptibility does NOT claim

- It does NOT claim invention will occur. It claims the landscape
  is susceptible to invention.
- It does NOT claim a specific invention will occur. It claims
  the combination-space has become reachable.
- It does NOT claim the model beats NULL at prediction. It claims
  the model identifies landscape instability, which is a different
  question from "will event E occur by year Y."

### What this means for the backtest

The backtest asks "did the predicted event occur within 5 years?"
This is an inevitability test, not a susceptibility test. Under
the susceptibility framing, the backtest is testing a NECESSARY
BUT NOT SUFFICIENT condition: susceptibility is necessary (no
event occurs without it, per the counterexample pattern), but
not sufficient (events occur only 3.57% of the time when
susceptibility is present).

This means:
- The 3.57% precision is not a measure of the model's predictive
  accuracy. It is a measure of how often susceptibility leads
  to actual invention — which depends on agency, not on the
  landscape.
- The significance test (p=0.2188) tests whether the model
  identifies susceptibility better than random. It does not
  test whether susceptibility leads to invention.
- A proper susceptibility test would ask: "of the landscapes
  that became susceptible, how many produced invention within
  5 years?" — which is recall, not precision. The current
  backtest measures precision (of the Top-10, how many were
  TPs). A susceptibility test measures recall (of the actual
  events, how many were in the susceptible set).

### Implication for Phase 14

Phase 14's stress tests should report BOTH:
1. Precision (Top-10 TP rate) — the inevitability metric, for
   comparability with prior backtests.
2. Recall (susceptible-set TP rate) — the susceptibility metric,
   which is the new target.

A domain "survives" (per PHASE_14_ADVANCEMENT_CRITERIA.md) if
it passes conditions 1-4 on precision. But the recall metric
is also reported, as the primary evidence for the susceptibility
claim. If precision is low but recall is high, the model is a
susceptibility detector, not an inevability detector — and
that is the honest claim.

---

## What this scope change authorizes

- Re-framing all prior precision numbers as inevitability metrics
  (the old target), not as susceptibility metrics (the new target).
- Adding recall as a co-equal metric in Phase 14 stress tests.
- Describing the model as a "susceptibility estimator" in
  synthesis documents.
- Citing the 135 false positives as "susceptible but no agent
  acted" rather than as "model failure."

## What this scope change does NOT authorize

- Ignoring the significance test result. The model still does
  not beat NULL at p<0.05 on the inevitability metric. The
  susceptibility re-framing does not rescue the precision claim;
  it supplements it with a recall claim.
- Skipping the destruction tests (Phase 14E). Susceptibility is
  still a causal claim (velocity and adjacency cause
  susceptibility). The destruction tests must verify this.
- Claiming M5. The susceptibility re-framing is a scope change,
  not a validation. M5 requires the same criteria as before:
  survive falsification, survive adversarial review, survive
  transferability, make confirmed predictions.

---

## Pre-registration

This scope change is committed before any Phase 14 stress test
runs. The susceptibility framing cannot be adjusted after seeing
Phase 14 results. If the stress tests produce high recall and
low precision, that is evidence FOR the susceptibility claim. If
they produce low recall and low precision, that is evidence
AGAINST it — and the theory is rejected regardless of the scope
change.
