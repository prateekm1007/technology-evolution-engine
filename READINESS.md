# READINESS — Phase 6 Score A Definition

**Status:** constitutional document (Score A definition).
**Location:** repo root (peer of CAPABILITY_ONTOLOGY.md, CONVERGENCE.md).
**Phase:** 6 (architectural investigation; implementation NOT yet authorized).
**Question:** Can it exist?

> Score A — Readiness: Can this exist?
> Inputs: TRL level, manufacturing maturity, infrastructure maturity,
> scientific maturity, cost curves.
> — CEO directive, Phase 6, Section 9

This document defines the Readiness score for the capability-centric
architecture. It follows the 5-section structure established by
CONVERGENCE.md: Definition, Signals, Formula, Failure modes, Validation
plan. The formula is a prior informed by the prior art (Hidalgo &
Hausmann, Fleming); it is NOT a fitted constant. Calibration requires
real data from the one vertical (electrochemical energy storage),
which is not yet ingested.

**This document does NOT authorize implementation.** It defines what
Readiness means. Building the scoring code (Phase 7) requires
separate explicit CEO authorization.

---

## 1. Definition

**Readiness** measures whether a capability (or a combination of
capabilities) is mature enough to exist — i.e., whether the
scientific, manufacturing, infrastructure, and economic preconditions
for it are in place.

**The defining property:** Readiness is a per-capability measurement,
NOT a pairwise measurement. It asks "is this capability ready?"
not "are these two capabilities converging?" This distinguishes it
from the Phase 5 convergence score, which was pairwise.

**Relationship to the other scores:**
- Readiness (Score A): can it exist? (per-capability)
- Novelty (Score B): has this combination been tried? (pairwise/combinatorial)
- Feasibility (Score C): would reality allow it? (threshold gates)

A combination can be high-Readiness (each capability is mature) but
low-Feasibility (regulatory or economic gates block it). A combination
can be high-Novelty (never tried) but low-Readiness (one capability
is not yet mature). The three scores are independent.

**Honest framing:** Readiness is the score most grounded in external
standards (TRL, manufacturing maturity curves). It is the least
speculative of the three. But it still requires calibration against
real data — the formula below is a prior, not a fitted constant.

---

## 2. Signals

Five candidate signals, grounded in the prior art and the CEO's
directive.

### Signal R1 — Technology Readiness Level (TRL)

**What it measures:** the NASA/DoD TRL scale (1-9), where 1 is basic
principles observed, 9 is actual system proven in operational
environment.

**Unit:** integer 1-9.

**Why necessary:** TRL is the globally-accepted standard for
technology maturity. It is the most defensible signal because it
is externally validated and widely used.

**Live data:** not yet ingested. The Phase 5 graph has no TRL field.
Phase 7 ingestion would need to attach TRL to each capability (from
patent claims, paper abstracts, or product specs).

### Signal R2 — Manufacturing maturity

**What it measures:** whether the capability can be manufactured at
scale. Sub-signals: pilot-line status, yield rate, cost-per-unit
trajectory.

**Unit:** categorical (lab / pilot / production / mass) + cost curve
slope.

**Why necessary:** a capability can be scientifically mature (high
TRL) but manufacturing-immature (can't be made at scale). This is
the gap between "works in the lab" and "works in the factory."

**Live data:** not yet ingested. Would require product specs,
manufacturing patents, or industry reports.

### Signal R3 — Infrastructure maturity

**What it measures:** whether the supporting infrastructure exists
(e.g., for EV batteries: charging stations, grid capacity, recycling
facilities).

**Unit:** categorical (none / partial / sufficient / mature).

**Why necessary:** a capability can be ready in isolation but blocked
by missing infrastructure. The CEO's directive includes INFRASTRUCTURE
as a node type (Section 4) for this reason.

**Live data:** not yet ingested.

### Signal R4 — Scientific maturity

**What it measures:** the depth of scientific understanding behind
the capability. Sub-signals: number of peer-reviewed papers, citation
count, presence of review articles, existence of consensus models.

**Unit:** continuous (papers count + citation density).

**Why necessary:** a capability can be patented (high R1) but
scientifically underexplored (low R4), which means the patent might
be premature — the underlying science isn't settled enough to
predict whether the capability will actually work.

**Live data:** partially available — the Phase 5 graph has 10 arXiv
papers that could contribute to scientific maturity signals. But
they're in the wrong ontology (component-centric, not capability-
centric).

### Signal R5 — Cost curve

**What it measures:** the trajectory of cost-per-unit over time.
Wright's Law / experience curve: cost decreases by a fixed percentage
for each doubling of cumulative production.

**Unit:** slope (cost reduction per doubling) + current cost-per-unit.

**Why necessary:** a capability can be ready (high R1-R4) but
economically non-viable (cost too high). Weitzman's recombinant
growth theory (prior art) grounds this: the limit is not idea
generation but economic viability.

**Live data:** not yet ingested. Would require industry cost data
or production-volume data.

---

## 3. Formula (experimental — NOT constitutional)

**Per CEO v3.5 correction:** constitutional documents encode
invariants, not fitted equations. The dimensions (R1-R5) are
invariant — they are the signals Readiness must measure. The
mathematics (weights, normalization, combination rule) are
experimental — they are candidate scoring functions that must be
tested against real data before being elevated.

The candidate formula, weights, thresholds, and combination rules
are recorded in:

```
evidence/experiments/readiness_formula_v1.md
```

That file is in the **experimental layer**, not the constitutional
layer. It will be revised as the formula is tested against the one
vertical's real data. The constitutional layer (this document) does
not commit to a specific formula.

**What IS invariant (constitutional):**
- Readiness is per-capability (not pairwise).
- The 5 signals (R1-R5) are the required dimensions.
- A combination's Readiness is limited by its least-ready capability
  (the weakest-link principle is an invariant, but the specific
  function — min(), weighted-min, etc. — is experimental).

**What is NOT invariant (experimental):**
- The weights of each signal.
- The normalization scheme.
- The specific combination function (min vs. weighted-min vs. other).
- The thresholds for "ready" vs. "not ready."

---

## 4. Failure modes

### Failure Mode R1 — TRL inflation

**Description:** a capability's TRL is overestimated because the
patent or paper claims more maturity than the evidence supports.

**Impact:** Readiness score is inflated; the system flags capabilities
as ready when they aren't.

**Mitigation:** TRL must be derived from evidence (patent claims,
paper abstracts, product specs), not asserted. Each TRL assignment
must cite the evidence. An assertion without evidence is a hypothesis.

### Failure Mode R2 — Stale readiness

**Description:** a capability's Readiness was high at time T but has
since been superseded or deprecated. Without temporal state, the
system still flags it as ready.

**Impact:** the system recommends capabilities that are no longer
viable.

**Mitigation:** TemporalState (CAPABILITY_ONTOLOGY.md Section 10).
Every Readiness score carries validFrom/validTo. A capability with
validTo < now is not ready (it's been superseded).

### Failure Mode R3 — Infrastructure dependency blindness

**Description:** a capability is ready in isolation but blocked by
missing infrastructure. The Readiness score is high because R1-R4
are high, but R3 (infrastructure) is undercounted.

**Impact:** the system flags combinations that can't actually deploy.

**Mitigation:** R3 (infrastructure maturity) must be weighted
appropriately for the capability type. A capability that requires
novel infrastructure (e.g., hydrogen fueling stations) should weight
R3 higher than a capability that uses existing infrastructure.

### Failure Mode R4 — Cost curve non-stationarity

**Description:** Wright's Law assumes cost decreases with cumulative
production. But cost curves can be non-stationary (e.g., raw material
shortages can reverse the curve).

**Impact:** the system predicts cost viability based on a trend that
no longer holds.

**Mitigation:** R5 (cost curve) must be re-evaluated at each
snapshot. The frozen-time backtest (Section 5) will reveal whether
the cost curve assumption held historically.

---

## 5. Validation plan

### Validation pair 1: lithium-ion battery (1995 vs 2010)

**Prediction:** Readiness(lithium-ion) should be low in 1995 (TRL 6,
pilot manufacturing, partial infrastructure) and high in 2010
(TRL 9, mass production, sufficient infrastructure).

**Falsification:** if the Readiness score doesn't increase
significantly between 1995 and 2010, the formula is wrong (either
the weights are off or the signals are not capturing the right
maturity dimensions).

**Resolution:** requires historical TRL data, historical manufacturing
data, and historical infrastructure data for lithium-ion. This is
the frozen-time backtest applied to Readiness.

### Validation pair 2: solid-state battery (2020 vs 2026)

**Prediction:** Readiness(solid-state) should be moderate in 2020
(TRL 5-6, lab-to-pilot) and higher in 2026 (TRL 7-8, pilot-to-
production, if recent claims hold).

**Falsification:** if the Readiness score doesn't increase, either
the technology hasn't progressed (and the system correctly flags it
as not-yet-ready) or the formula is missing a signal.

**Resolution:** requires current TRL data, manufacturing pilot status,
and cost trajectory for solid-state batteries.

### Pre-validation prerequisite

The one vertical (electrochemical energy storage) must be ingested
with TRL, manufacturing, infrastructure, scientific, and cost data
before this validation can run. That ingestion is Phase 7 work,
which is NOT yet authorized.

**What this document does NOT do:** it does not authorize the
ingestion. It defines what Readiness means, so that when ingestion
is authorized, the data collected will match the formula's signals.

---

## Implementation status

| Item | Status |
|---|---|
| Definition | COMPLETE (this document) |
| Signals (5) | COMPLETE (R1-R5) |
| Formula | COMPLETE (prior; not fitted) |
| Failure modes (4) | COMPLETE |
| Validation plan | COMPLETE (requires Phase 7 ingestion to execute) |
| Phase 7 implementation | NOT AUTHORIZED |

No code written. No data ingested. This is a definition document,
grounded in the prior art, awaiting Phase 7 authorization to be
tested against real data from the one vertical.
