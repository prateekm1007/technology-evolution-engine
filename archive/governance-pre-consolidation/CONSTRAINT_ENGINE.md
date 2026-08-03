# CONSTRAINT_ENGINE

**Status:** Phase 16A Deliverable 3.
**Location:** repo root.
**Phase:** 16A.

> Find every obstacle.
> — CEO directive, Phase 16A

---

## Purpose

The Constraint Engine identifies every obstacle that blocks an idea
from becoming reality. Constraints are the inverse of enablers —
they are what prevents reachability. Per REACHABILITY_CONSTITUTION.md
Rule 4 (boundaries are assets), constraints are not failures; they
are observations about the shape of the possibility space.

---

## Constraint classes

```text
physics
economics
manufacturing
regulation
infrastructure
coordination
capital
talent
time
```

These 9 classes extend the original 5 (physics, economics,
manufacturing, regulation, infrastructure) from CONSTITUTION.md Law 2
by adding 4 new classes (coordination, capital, talent, time)
identified through the Phase 14 stress tests and Phase 15
classification work.

---

## Schema

```typescript
interface Constraint {
    id: string
    type: string
    severity: number
    probability: number
    mitigation: string[]
}
```

### Field semantics

| Field | Type | Required | Meaning |
|---|---|---|---|
| `id` | string | yes | CON-XXX identifier. |
| `type` | string | yes | One of the 9 constraint classes. |
| `severity` | float [0, 1] | yes | How much this constraint blocks the idea. 0 = negligible; 1 = absolute blocker. |
| `probability` | float [0, 1] | yes | The probability that this constraint will be active during the execution window. 0 = will not be active; 1 = certain to be active. |
| `mitigation` | string[] | yes | Actions that could reduce severity or probability. Empty array = no known mitigation. |

---

## Constraint class definitions

### physics
Constraints imposed by physical laws: thermal limits, energy density
ceilings, wavelength of light, material strength, quantum effects.
These are the hardest constraints — they cannot be engineered around.

### economics
Constraints imposed by cost: unit cost above market willingness-to-pay,
capital requirements beyond available funding, negative unit economics.

### manufacturing
Constraints imposed by production capability: yield below threshold,
throughput insufficient, process not mature, supply chain absent.

### regulation
Constraints imposed by regulatory bodies: certification required,
testing incomplete, approval pending, jurisdiction restrictions.

### infrastructure
Constraints imposed by deployment environment: no charging stations,
no cell towers, no clean water, no power grid.

### coordination
Constraints imposed by multi-actor synchronization: standards not
agreed, industry consortium not formed, patent landscape fragmented.

### capital
Constraints imposed by funding availability: insufficient venture
capital, no government subsidies, capital cost too high.

### talent
Constraints imposed by human capital: insufficient engineers, no
domain experts, skills gap in the workforce.

### time
Constraints imposed by temporal deadlines: market window closing,
competitive pressure, regulatory deadline, patent expiry.

---

## Example constraints

### Autonomous farming robot

```json
[
  {
    "id": "CON-001",
    "type": "physics",
    "severity": 0.3,
    "probability": 0.8,
    "mitigation": ["Use shaded solar panels", "Add supplementary battery charging"]
  },
  {
    "id": "CON-002",
    "type": "economics",
    "severity": 0.7,
    "probability": 0.6,
    "mitigation": ["Target large farms first ( economies of scale)", "Lease model instead of purchase"]
  },
  {
    "id": "CON-003",
    "type": "regulation",
    "severity": 0.5,
    "probability": 0.4,
    "mitigation": ["Start in jurisdictions with permissive autonomous vehicle laws", "Engage regulators early"]
  },
  {
    "id": "CON-004",
    "type": "infrastructure",
    "severity": 0.4,
    "probability": 0.5,
    "mitigation": ["Use satellite communication as fallback", "Pre-map farm terrain"]
  },
  {
    "id": "CON-005",
    "type": "talent",
    "severity": 0.6,
    "probability": 0.7,
    "mitigation": ["Partner with agricultural engineering programs", "Retrain existing farm equipment technicians"]
  },
  {
    "id": "CON-006",
    "type": "time",
    "severity": 0.5,
    "probability": 0.5,
    "mitigation": ["Phase deployment: start with monitoring-only robots, add autonomy later"]
  }
]
```

---

## Constraint analysis protocol

1. **Identify constraints per class.** For each of the 9 classes, check if a constraint is active.
2. **Assess severity.** How much does this constraint block the idea? (0-1)
3. **Assess probability.** How likely is this constraint to be active during execution? (0-1)
4. **Identify mitigations.** What actions could reduce severity or probability?
5. **Compute overall constraint load.** `load = sum(severity × probability for all constraints) / number_of_constraints`. A load > 0.5 indicates the idea is heavily constrained.

---

## What this engine does NOT do

- It does not remove constraints. It identifies them.
- It does not prioritize constraints. All constraints are cataloged equally.
- It does not guarantee completeness. New constraints may emerge during execution.
- It does not modify the frozen formula. The formula's `limitations` field is a constraint statement for the formula itself, not for the ideas being evaluated.

---

## Pre-stated falsifier (EP-4)

**Claim:** The 9 constraint classes cover all obstacles that block an idea from becoming reality.

**Falsifier:** An obstacle that does not fit any of the 9 classes — i.e., a blocker that is not physical, economic, manufacturing, regulatory, infrastructural, coordination, capital, talent, or temporal.

**Status:** PENDING. No ideas have been constraint-analyzed (no implementation).
