# Feasibility Formula v1 (experimental)

**Status:** experimental (NOT constitutional).
**Location:** `evidence/experiments/` (per CEO v3.5: formulas are experimental, not constitutional law).
**Constitutional reference:** `FEASIBILITY.md` Section 3.

This file records the CANDIDATE formula for the Feasibility score.
The boolean-AND structure IS constitutional (recorded in FEASIBILITY.md
Section 3 as an invariant). The specific thresholds and gate
definitions recorded here are experimental — they must be calibrated
against real data.

---

## Candidate formula

```text
Feasibility(combination) =
    F1_regulatory AND
    F2_economic AND
    F3_manufacturing AND
    F4_infrastructure AND
    F5_physical
```

### Score

Boolean: FEASIBLE / INFEASIBLE. There is no continuous score. A
combination either passes all gates or it doesn't.

### Gate definitions (candidate thresholds)

#### F1 — Regulatory

**Pass condition:** the combination does not violate any REGULATION
node in the graph.

**Candidate thresholds (to be calibrated):**
- UN38_3 (battery shipping safety): pass if all cells in the
  combination meet UN38_3 testing requirements.
- IEC 62133 (battery safety): pass if the combination's design
  meets IEC 62133 standards.
- Additional regulations to be identified during Phase 7C ingestion.

#### F2 — Economic

**Pass condition:** the combination's cost-per-unit is below the
market threshold.

**Candidate thresholds (to be calibrated):**
- EV battery: cost-per-kWh < $100/kWh (2026 threshold; will change
  over time — requires TemporalState).
- Grid storage: cost-per-kWh-cycle < $0.05.
- Consumer electronics: cost-per-unit < $50.
- These are priors; real thresholds come from industry data.

#### F3 — Manufacturing

**Pass condition:** the manufacturing capacity exists to produce the
combination at the required scale.

**Candidate thresholds (to be calibrated):**
- Lab: < 100 units/year. Pass for research; fail for commercial.
- Pilot: 100-10,000 units/year. Pass for early commercial; fail
  for mass market.
- Production: 10,000-1,000,000 units/year. Pass for most
  commercial applications.
- Mass: > 1,000,000 units/year. Pass for all applications.

#### F4 — Infrastructure

**Pass condition:** the required INFRASTRUCTURE nodes exist with
sufficient maturity.

**Candidate thresholds (to be calibrated):**
- EV charging: > 1 charging station per 100 EVs in the target market.
- Grid storage: grid connection capacity > peak demand.
- Recycling: recycling facility within 500km of deployment.
- These are priors; real thresholds come from infrastructure data.

#### F5 — Physical

**Pass condition:** the combination does not violate any physical
CONSTRAINT node.

**Candidate thresholds (to be calibrated):**
- Energy density: < theoretical maximum for the chemistry (e.g.,
  < 400 Wh/kg for lithium-ion).
- Operating temperature: within the safe range for the materials.
- Cycle life: > minimum cycles for the application.
- These are priors; real limits come from materials science data.

---

## Partial Feasibility (informational, not scored)

For diagnostic purposes, the system can report which gates failed:

```
combination X is INFEASIBLE because:
  F1 (regulatory): FAIL — does not meet UN38_3
  F3 (manufacturing): FAIL — only lab-scale production exists
  F2 (economic): PASS
  F4 (infrastructure): PASS
  F5 (physical): PASS
```

This is informational — it helps the user understand WHY the
combination is infeasible, but it does not change the score. The
score remains INFEASIBLE (boolean).

---

## What would change this formula

1. **Real threshold data.** The candidate thresholds above are
   priors. When real data from the one vertical is ingested, the
   thresholds will be calibrated.

2. **Gate interactions.** The current formula assumes gates are
   independent. If gate interactions are discovered (e.g., failing
   F1 regulatory adds compliance costs that push F2 economic over
   threshold), the reporting mechanism (not the boolean structure)
   will be updated to reflect interactions.

3. **New gates.** If a new constraint type is discovered that
   doesn't fit F1-F5, a new gate may need to be added (requiring
   a constitutional amendment to FEASIBILITY.md Section 2 — but
   only if the existing 5 gates are demonstrably insufficient).

---

## Version history

- v1 (this file): initial candidate formula + candidate thresholds.
  Boolean-AND structure is constitutional; thresholds are priors.
  Created during Phase 6 constitutional document writing.
  Not yet tested against real data.
