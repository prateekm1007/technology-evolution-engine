# Assumptions — Type C Epistemic Statements

**Status:** epistemic layer (assumptions: what are we taking for granted?).
**Location:** `evidence/epistemic/assumptions/`

An assumption is a statement the system depends on but cannot
prove from evidence alone. It is NOT an observation (it wasn't
read from a document) and NOT a principle (it is not a named
physical law). It is a modeling choice that a reviewer made,
recorded so that future workers can challenge it.

## Schema

```typescript
interface Assumption {
    statement: string;    // the assumption being made
    rationale: string;    // why this assumption seems reasonable
    reviewer: string;     // who made the assumption
}
```

## What goes here

- "Capability maturity can be approximated from CPC evidence."
- "CPC codes accurately reflect what a patent is about."
- "The 10 capabilities in the catalog are sufficient for the electrochemical energy storage vertical."
- "Structural invariants (physical necessities) are stable across time."
- "UN38.3 and IEC 62133 are the most important regulations for this vertical."

## What does NOT go here

- Observations ("patent contains CPC code H01M 10/0562") → observations/
- Principles ("charge conservation requires ion transport") → principles/

## Current assumptions

### A-001: CPC codes approximate capability

**Statement:** A patent's CPC code accurately reflects the capabilities
the patent describes.

**Rationale:** CPC codes are assigned by USPTO patent examiners who
read the full patent. The classification system is decades-refined
and globally consistent. However, a CPC code tells you what a
patent is CLASSIFIED as, not necessarily what it ENABLES. This
assumption is necessary for the EMBODIED_IN edge but should be
tested in the frozen-time backtest.

**Reviewer:** coder_agent_001 / 2026-08-02

### A-002: 10 capabilities are sufficient

**Statement:** The 10 capabilities in CAPABILITY_CATALOG.md (reduced
from 20) are sufficient to model the electrochemical energy storage
vertical.

**Rationale:** The 10 were selected to cover the core value chain
(storage → transport → electrodes → thermal → management → manufacturing).
However, some capabilities from the original 20 were dropped (e.g.,
HIGH_POWER_DISCHARGE, CONVERSION_REACTION, SOLID_ELECTROLYTE_SINTERING,
RECYCLING, GRID_INTERCONNECTION). If the frozen-time backtest reveals
that important predictions can't be made without these, the assumption
is wrong.

**Reviewer:** coder_agent_001 / 2026-08-02

### A-003: Structural invariants are stable across time

**Statement:** The structural REQUIRES edges (e.g., electrochemical
storage requires ion transport) hold across the entire temporal
scope (1990-2026).

**Rationale:** These are physical necessities — charge conservation
hasn't changed in 30 years. However, some "requirements" may be
technology-specific (e.g., "Li-ion requires intercalation" is
true for Li-ion but not for flow batteries). The assumption is
that the structural edges are sufficiently general.

**Reviewer:** coder_agent_001 / 2026-08-02

### A-004: The 5 selected patents are representative

**Statement:** The 5 patents selected (US20240194939A1, US12489120B2,
US20240021793A1, WO2012068732A1, WO2015119843A1) are representative
of the electrochemical energy storage domain.

**Rationale:** They span diverse H01M subclasses (solid-state, flow
battery, Li-ion + fast charging, battery pack, electrode coating).
However, 5 patents is a very small sample. The frozen-time backtest
will reveal whether this sample is sufficient for meaningful
predictions.

**Reviewer:** coder_agent_001 / 2026-08-02

### A-005: The 5 constraints are the most important

**Statement:** The 5 constraints (theoretical energy density limit,
thermal runaway threshold, cost per kWh threshold, UN38.3 shipping
safety, IEC 62133 safety standard) are the most important constraints
for this vertical.

**Rationale:** They cover physical (2), economic (1), and regulatory
(2) constraints. However, manufacturing constraints (e.g., solid
electrolyte densification, dry electrode yield) were dropped in the
scope reduction. If these are load-bearing for predictions, the
assumption is wrong.

**Reviewer:** coder_agent_001 / 2026-08-02
