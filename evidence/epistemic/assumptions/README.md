# Assumptions — Type C Epistemic Statements

**Status:** epistemic layer (assumptions: what are we taking for granted?).
**Location:** `evidence/epistemic/assumptions/`
**Phase:** 7C.3 (per CEO Rule 1: every assumption must be falsifiable).

> Every assumption must be falsifiable.
> — CEO Rule 1

An assumption is a statement the system depends on but cannot
prove from evidence alone. It is NOT an observation and NOT a
principle. It is a modeling choice that a reviewer made, recorded
so that future workers can challenge it.

## Schema

```typescript
interface Assumption {
    id: string;                  // e.g., "A-001"
    statement: string;           // the assumption
    rationale: string;           // why it seems reasonable
    falsificationCriterion: string;  // what would prove it wrong
    status: "ACTIVE" | "FALSIFIED" | "RETIRED";
    reviewer: string;            // who made the assumption
}
```

---

## A-001: CPC codes approximate capability

**Statement:** A patent's CPC code accurately reflects the capabilities
the patent describes.

**Rationale:** CPC codes are assigned by USPTO patent examiners who
read the full patent. The classification system is decades-refined
and globally consistent. However, a CPC code tells you what a
patent is CLASSIFIED as, not necessarily what it ENABLES.

**Falsification criterion:** Discover a patent whose CPC code maps
to a capability, but whose claims do not actually describe that
capability (i.e., the classification is wrong or misleading).

**Status:** ACTIVE

**Reviewer:** coder_agent_001 / 2026-08-02

---

## A-002: 10 capabilities are sufficient

**Statement:** The 10 capabilities in CAPABILITY_CATALOG.md (reduced
from 20) are sufficient to model the electrochemical energy storage
vertical.

**Rationale:** The 10 were selected to cover the core value chain
(storage → transport → electrodes → thermal → management → manufacturing).
However, some capabilities from the original 20 were dropped (e.g.,
HIGH_POWER_DISCHARGE, CONVERSION_REACTION, SOLID_ELECTROLYTE_SINTERING,
RECYCLING, GRID_INTERCONNECTION).

**Falsification criterion:** The frozen-time backtest (Phase 7D)
produces predictions that are impossible to make without one of the
dropped capabilities — i.e., a missing capability blocks a
prediction that should have been possible.

**Status:** ACTIVE

**Reviewer:** coder_agent_001 / 2026-08-02

---

## A-003: Structural invariants are stable across time

**Statement:** The structural REQUIRES edges (e.g., electrochemical
storage requires ion transport) hold across the entire temporal
scope (1990-2026).

**Rationale:** These are physical necessities — charge conservation
hasn't changed in 30 years. However, some "requirements" may be
technology-specific (e.g., "Li-ion requires intercalation" is
true for Li-ion but not for flow batteries).

**Falsification criterion:** Discover a historical period in which
the invariant does not hold — e.g., a time before Li-ion existed
where the REQUIRES INTERCALATION edge would have been false
(because the dominant chemistry was lead-acid, which doesn't use
intercalation).

**Status:** ACTIVE

**Reviewer:** coder_agent_001 / 2026-08-02

---

## A-004: The 5 selected patents are representative

**Statement:** The 5 patents selected (US20240194939A1, US12489120B2,
US20240021793A1, WO2012068732A1, WO2015119843A1) are representative
of the electrochemical energy storage domain.

**Rationale:** They span diverse H01M subclasses (solid-state, flow
battery, Li-ion + fast charging, battery pack, electrode coating).
However, 5 patents is a very small sample.

**Falsification criterion:** The frozen-time backtest reveals that
predictions made from these 5 patents systematically miss a class
of inventions that a different sample would have caught — i.e.,
the sample is biased toward a subset of the domain.

**Status:** ACTIVE

**Reviewer:** coder_agent_001 / 2026-08-02

---

## A-005: The 5 constraints are the most important

**Statement:** The 5 constraints (theoretical energy density limit,
thermal runaway threshold, cost per kWh threshold, UN38.3 shipping
safety, IEC 62133 safety standard) are the most important constraints
for this vertical.

**Rationale:** They cover physical (2), economic (1), and regulatory
(2) constraints. However, manufacturing constraints were dropped in
the scope reduction.

**Falsification criterion:** The frozen-time backtest reveals that
a dropped constraint (e.g., solid electrolyte densification, dry
electrode yield) was load-bearing for a prediction that failed —
i.e., the missing constraint explains a false positive or false
negative.

**Status:** ACTIVE

**Reviewer:** coder_agent_001 / 2026-08-02
