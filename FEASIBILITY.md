# FEASIBILITY — Phase 6 Score C Definition

**Status:** constitutional document (Score C definition).
**Location:** repo root (peer of CAPABILITY_ONTOLOGY.md, CONVERGENCE.md, READINESS.md, NOVELTY.md).
**Phase:** 6 (architectural investigation; implementation NOT yet authorized).
**Question:** Would reality allow it?

> Score C — Feasibility: Can this survive contact with reality?
> Inputs: regulations, economics, manufacturing, infrastructure,
> physical constraints.
> — CEO directive, Phase 6, Section 9

This document defines the Feasibility score for the capability-centric
architecture. It follows the 5-section structure established by
CONVERGENCE.md. The formula is a prior informed by the prior art
(Weitzman, Hidalgo & Hausmann); it is NOT a fitted constant.

**This document does NOT authorize implementation.** It defines what
Feasibility means.

---

## 1. Definition

**Feasibility** measures whether a combination of capabilities can
survive contact with reality — i.e., whether regulatory, economic,
manufacturing, infrastructure, and physical constraints allow it.

**The defining property:** Feasibility is a **threshold gate**
measurement, not a continuous score. Each constraint is boolean
(pass/fail) or threshold-based (above/below a limit). The overall
Feasibility is the AND of all gates — if any gate fails, the
combination is not feasible.

**This is the critical distinction from Readiness and Novelty.**
Per the external review:

> Feasibility gates are boolean/threshold conditions, not similarity
> scores. Blending them into a continuous convergence number is why
> "premature" inventions and "impossible" inventions currently look
> the same to the system.

A combination that fails a regulatory gate is not "70% feasible" —
it is infeasible. Period. The Feasibility score preserves this
distinction by being gate-based, not blended.

**Relationship to the other scores:**
- Readiness (Score A): can it exist? (per-capability, continuous)
- Novelty (Score B): has this combination been tried? (combinatorial, continuous)
- Feasibility (Score C): would reality allow it? (threshold gates, boolean)

A combination can be high-Readiness AND high-Novelty but low-Feasibility
(e.g., a novel combination of mature capabilities that violates a
regulation). The three scores are independent.

---

## 2. Signals

Five threshold gates, grounded in the CEO's directive and the prior art.

### Gate F1 — Regulatory

**What it measures:** whether the combination complies with all
applicable regulations.

**Unit:** boolean (pass / fail). Pass if the combination does not
violate any REGULATION node in the graph. Fail if it does.

**Why necessary:** a combination can be ready and novel but illegal
(e.g., a battery chemistry that violates shipping regulations). The
regulatory gate is hard — there is no "partially compliant."

**Live data:** not yet ingested. The REGULATION node type
(CAPABILITY_ONTOLOGY.md Section 4) must be populated with actual
regulations (e.g., UN38_3 for battery shipping, IEC 62133 for
battery safety).

### Gate F2 — Economic

**What it measures:** whether the combination's cost-per-unit is
below the market threshold.

**Unit:** threshold (pass if cost < threshold, fail otherwise).

**Why necessary:** a combination can be ready and novel but
economically non-viable (costs too much to produce). Weitzman's
recombinant growth theory (prior art) grounds this: the limit is
not idea generation but economic viability.

**Live data:** not yet ingested. Requires cost data (from product
specs, industry reports, or cost models).

### Gate F3 — Manufacturing

**What it measures:** whether the combination can be manufactured
at the required scale.

**Unit:** threshold (pass if manufacturing capacity exists, fail
otherwise).

**Why necessary:** a combination can be ready in the lab but not
manufacturable at scale. This is the gap between "works" and "can
be made."

**Live data:** not yet ingested. Requires manufacturing process data.

### Gate F4 — Infrastructure

**What it measures:** whether the supporting infrastructure exists.

**Unit:** boolean (pass / fail). Pass if the required INFRASTRUCTURE
nodes exist with sufficient maturity.

**Why necessary:** a combination can be ready and manufacturable but
blocked by missing infrastructure (e.g., EV batteries require
charging stations, grid capacity, recycling facilities).

**Live data:** not yet ingested. The INFRASTRUCTURE node type must
be populated.

### Gate F5 — Physical

**What it measures:** whether the combination violates any physical
laws or material limits.

**Unit:** boolean (pass / fail). Pass if no physical CONSTRAINT
node is violated.

**Why necessary:** a combination can be ready, novel, and economically
viable but physically impossible (e.g., a battery with energy density
exceeding the theoretical limit of its chemistry).

**Live data:** not yet ingested. The CONSTRAINT node type must be
populated with physical limits (e.g., theoretical energy density
ceilings).

---

## 3. Formula (experimental — NOT constitutional)

**Per CEO v3.5 correction:** constitutional documents encode
invariants, not fitted equations. The dimensions (F1-F5) are
invariant — they are the gates Feasibility must check. The specific
thresholds and gate-interaction rules are experimental.

The candidate formula, thresholds, and gate definitions are recorded
in:

```
evidence/experiments/feasibility_formula_v1.md
```

**What IS invariant (constitutional):**
- Feasibility is a boolean gate-based measurement (NOT continuous).
- The 5 gates (F1-F5) are the required dimensions.
- A combination is FEASIBLE only if ALL gates pass (AND logic).
- A combination that fails ANY gate is INFEASIBLE — there is no
  "partially feasible." This is the critical invariant that
  distinguishes Feasibility from Readiness and Novelty.

**What is NOT invariant (experimental):**
- The specific thresholds for each gate (e.g., what cost-per-unit
  counts as "economically viable").
- Whether gates interact (e.g., does failing F1 regulatory change
  the F2 economic threshold?).
- How gate failures are reported (which diagnostic information
  accompanies the INFEASIBLE verdict).
- The specific regulations, cost thresholds, manufacturing capacity
  values, infrastructure requirements, and physical limits
  populating each gate.

**The boolean-AND structure IS invariant.** Per the external review,
blending threshold gates into a continuous number is what made the
CO_OCCURRENCE_MODEL conflate "premature" and "impossible." The
boolean structure prevents this. The specific thresholds within each
gate are experimental — they must be calibrated against real data.

---

## 4. Failure modes

### Failure Mode F1 — Gate omission

**Description:** a constraint exists in reality but is not in the
graph (no REGULATION, CONSTRAINT, or INFRASTRUCTURE node for it).
The combination passes all recorded gates but fails an unrecorded
one.

**Impact:** the system flags an infeasible combination as feasible.

**Mitigation:** the Feasibility score is only as good as the
constraint graph. The one-vertical scope (10 constraints max,
Section 12) means only the 10 most important constraints are
modeled. This is a known limitation — the system should report
"feasible given the modeled constraints," not "feasible."

### Failure Mode F2 — Gate staleness

**Description:** a regulation was valid at time T but has since
changed. Without temporal state, the system uses the stale
regulation.

**Impact:** the system flags combinations as feasible/infeasible
based on outdated regulations.

**Mitigation:** TemporalState. Every gate must carry validFrom/
validTo. A regulation that changed in 2020 must be queried as-of
the investigation date.

### Failure Mode F3 — Threshold miscalibration

**Description:** the economic threshold (F2) is set too high or
too low, causing the gate to pass/fail incorrectly.

**Impact:** feasible combinations are flagged as infeasible (threshold
too low) or infeasible ones are flagged as feasible (threshold too
high).

**Mitigation:** thresholds must be derived from real market data,
not asserted. Each threshold must cite evidence (industry reports,
product specs). The frozen-time backtest will reveal whether the
thresholds held historically.

### Failure Mode F4 — Gate interaction blindness

**Description:** gates are assumed independent, but they interact.
E.g., a regulatory gate failing might cause the economic gate to
fail (compliance costs raise the cost-per-unit). The AND formula
treats them as independent.

**Impact:** the system might flag a combination as feasible because
each gate passes individually, but the interaction makes it
infeasible.

**Mitigation:** this is a known limitation of the gate-based model.
The system should report gate interactions when they're known (e.g.,
"regulatory compliance adds $X to cost, which may push F2 over
threshold"). But the Feasibility score remains boolean — the
interaction is informational, not scored.

---

## 5. Validation plan

### Validation pair 1: a feasible combination (lithium-ion EV battery, 2020)

**Prediction:** {lithium-ion, EV_charging_infrastructure} should
pass all gates: F1 (UN38_3 compliant), F2 (cost below threshold),
F3 (mass-manufactured), F4 (charging infrastructure exists), F5
(within physical limits). Feasibility = FEASIBLE.

**Falsification:** if the combination fails any gate, either the
gate is miscalibrated or the constraint data is wrong.

**Resolution:** requires the constraint graph populated with
regulations, cost thresholds, manufacturing capacity, infrastructure
status, and physical limits for the electrochemical energy storage
vertical.

### Validation pair 2: an infeasible combination (solid-state battery with energy density exceeding theoretical limit)

**Prediction:** {solid-state, energy_density_>1000_Wh/kg} should
fail F5 (physical) because the theoretical limit of solid-state
chemistry is below 1000 Wh/kg. Feasibility = INFEASIBLE.

**Falsification:** if the combination passes F5, the physical
constraint data is wrong.

**Resolution:** requires the CONSTRAINT node for theoretical energy
density limits.

### Pre-validation prerequisite

The one vertical must be ingested with REGULATION, CONSTRAINT, and
INFRASTRUCTURE nodes before this validation can run. That ingestion
is Phase 7 work, which is NOT yet authorized.

---

## Implementation status

| Item | Status |
|---|---|
| Definition | COMPLETE (this document) |
| Signals (5 gates) | COMPLETE (F1-F5) |
| Formula | COMPLETE (boolean AND; not continuous) |
| Failure modes (4) | COMPLETE |
| Validation plan | COMPLETE (requires Phase 7 ingestion to execute) |
| Phase 7 implementation | NOT AUTHORIZED |

No code written. No data ingested. This is a definition document,
grounded in Weitzman (economic viability) and the external review
(boolean gates, not blended scores), awaiting Phase 7 authorization
to be tested against real data from the one vertical.
