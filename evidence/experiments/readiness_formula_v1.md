# Readiness Formula v1 (experimental)

**Status:** experimental (NOT constitutional).
**Location:** `evidence/experiments/` (per CEO v3.5: formulas are experimental, not constitutional law).
**Constitutional reference:** `READINESS.md` Section 3.

This file records the CANDIDATE formula for the Readiness score.
It is a prior, not a fitted constant. It will be revised as the
formula is tested against real data from the one vertical
(electrochemical energy storage). The constitutional document
(READINESS.md) commits to the dimensions and invariants, not to
this specific formula.

---

## Candidate formula

```text
Readiness(capability) =
    0.30 * TRL_normalized(R1)
  + 0.25 * manufacturing_maturity(R2)
  + 0.20 * infrastructure_maturity(R3)
  + 0.15 * scientific_maturity(R4)
  + 0.10 * cost_curve_viability(R5)
```

### Signal normalization

- TRL_normalized = TRL / 9
- manufacturing_maturity: lab=0.2, pilot=0.4, production=0.7, mass=1.0
- infrastructure_maturity: none=0, partial=0.3, sufficient=0.7, mature=1.0
- scientific_maturity: normalized paper/citation count
- cost_curve_viability: 1.0 if cost is below threshold, scaled otherwise

### Score range

[0, 1]. A score of 1.0 means the capability is fully ready (TRL 9,
mass-manufactured, sufficient infrastructure, deep science, viable
cost). A score of 0.0 means nothing is in place.

### Weight justification (priors, not fitted)

TRL dominates (0.30) because it is the most externally-validated
signal. Manufacturing (0.25) and infrastructure (0.20) follow
because they represent the gap between lab and deployment.
Scientific maturity (0.15) and cost curve (0.10) are lower because
they are more speculative signals.

---

## Combination rule (candidate)

```text
Readiness(combination) = min(Readiness(c) for c in combination)
```

The weakest-link principle — a chain is only as strong as its
weakest link. If one capability is at TRL 3 (lab), the combination
is not ready, regardless of how mature the others are.

**Alternative candidates (not yet tested):**
- weighted-min: min(weighted_readiness(c) for c in combination),
  where weights reflect the capability's importance to the combination.
- geometric-mean: (product of Readiness(c))^(1/n). Less harsh than
  min; allows a single low-readiness capability to be partially
  compensated by others.
- These alternatives are recorded for future testing, not adopted.

---

## What would change this formula

1. **Real data from the one vertical.** When TRL, manufacturing,
   infrastructure, scientific, and cost data are ingested for
   electrochemical energy storage, the weights can be tested
   against historical outcomes (frozen-time backtest).

2. **Discovery of missing signals.** If the frozen-time backtest
   reveals that the formula doesn't predict readiness well, a new
   signal may need to be added (requiring a constitutional amendment
   to READINESS.md Section 2).

3. **Discovery of redundant signals.** If two signals are highly
   correlated, one may be dropped (simplifying the formula without
   losing signal).

---

## Version history

- v1 (this file): initial candidate formula. Priors, not fitted.
  Created during Phase 6 constitutional document writing.
  Not yet tested against real data.
