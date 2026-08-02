# Principles — Type B Epistemic Statements

**Status:** epistemic layer (principles: what do we believe is true?).
**Location:** `evidence/epistemic/principles/`

A principle is a named physical, chemical, or economic law that
justifies a structural edge. It is NOT an observation (it wasn't
read from a document) and NOT an assumption (it is grounded in
established science). It is a domain-model assertion that a
reviewer invokes to explain WHY one capability requires or
constrains another.

## Schema

```typescript
interface Principle {
    name: string;            // short name (e.g., "charge conservation")
    description: string;     // what the principle states
    references: string[];   // where the principle is established
                             // (textbook, standard, seminal paper)
}
```

## What goes here

- "Charge conservation requires ion transport between electrodes."
- "Joule heating (I²R) generates heat proportional to current squared."
- "Thermodynamic energy density ceiling limits maximum stored energy."

## What does NOT go here

- Observations ("patent contains CPC code H01M 10/0562") → observations/
- Assumptions ("CPC codes approximate capability maturity") → assumptions/

## The 11 principles currently invoked in the trusted graph

| Principle | Description | Edges using it |
|---|---|---|
| charge conservation | Electrochemical storage requires ions to move between electrodes to balance electron flow in the external circuit. | EDGE-025 |
| lattice insertion chemistry (Li-ion specifically) | Li-ion storage requires intercalation — ions insert into and remove from electrode lattices. Specific to intercalation-based chemistries. | EDGE-026 |
| transport kinetics | Fast charging requires ions to move rapidly. C-rate is limited by ion transport kinetics. | EDGE-027 |
| Joule heating (I²R losses) | High current generates heat via internal resistance. Without thermal management, temperature exceeds safe limits at high C-rates. | EDGE-028 |
| manufacturing process dependency | Cell assembly requires coated electrodes. The coating process produces the functional electrode. | EDGE-029 |
| feedback control | Safety protection requires knowing state of charge. Without monitoring, the system cannot determine when to intervene. | EDGE-030 |
| thermodynamic energy density ceiling | Theoretical energy density of electrochemical chemistries limits maximum stored energy. | EDGE-031 |
| exothermic decomposition threshold | If cell temperature exceeds ~150°C, thermal runaway occurs. | EDGE-032 |
| market price elasticity | Cost per kWh must be below market threshold for economic viability. | EDGE-033 |
| transport safety regulation (UN Model Regulations) | UN38.3 requires batteries to pass safety tests before transport. | EDGE-034 |
| product safety standard (IEC 62133) | IEC 62133 specifies safety requirements for secondary cells. | EDGE-035 |

## References (to be populated)

Each principle should cite where it is established (textbook chapter,
standard section, seminal paper). This is pending — the current
principles are grounded in domain knowledge but not yet cited to
specific references. This is recorded honestly per principle #8
(no data, say no data).
