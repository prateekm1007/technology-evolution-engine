# COMPONENT_ENGINE

**Status:** Phase 16A Deliverable 2.
**Location:** repo root.
**Phase:** 16A.

> Break every object into components.
> — CEO directive, Phase 16A

---

## Purpose

The Component Engine decomposes an idea into its physical and
logical components. Every object — a farming robot, a desalination
plant, a battery system — can be decomposed. The decomposition is
the basis for the dependency graph, constraint analysis, and
manufacturing plan.

---

## Schema

```typescript
interface Component {
    id: string
    name: string
    description: string
    maturity: number
    dependencies: string[]
    alternatives: string[]
}
```

### Field semantics

| Field | Type | Required | Meaning |
|---|---|---|---|
| `id` | string | yes | CMP-XXX identifier. |
| `name` | string | yes | Human-readable component name. |
| `description` | string | yes | What the component does. |
| `maturity` | float [0, 1] | yes | The component's TRL normalized. 0 = concept; 1 = commercial. Equivalent to capabilityState in STATE_SPACE.md. |
| `dependencies` | string[] | yes | Other component IDs this component requires. Forms the dependency graph. |
| `alternatives` | string[] | yes | Other component IDs that could substitute for this one. |

---

## Example decomposition

### Autonomous farming robot

```
autonomous tractor
        │
        ├── sensors (CMP-001)
        ├── motors (CMP-002)
        ├── cameras (CMP-003)
        ├── GPS (CMP-004)
        ├── processors (CMP-005)
        ├── batteries (CMP-006)
        └── communications (CMP-007)
```

```json
[
  {
    "id": "CMP-001",
    "name": "sensors",
    "description": "Environmental and crop sensors (temperature, humidity, soil moisture, NDVI)",
    "maturity": 0.9,
    "dependencies": ["CMP-005"],
    "alternatives": ["CMP-001a (satellite remote sensing)"]
  },
  {
    "id": "CMP-002",
    "name": "motors",
    "description": "Electric drive motors for locomotion and implement actuation",
    "maturity": 0.9,
    "dependencies": ["CMP-006"],
    "alternatives": ["CMP-002a (hydraulic drive)"]
  },
  {
    "id": "CMP-003",
    "name": "cameras",
    "description": "Machine vision cameras for navigation and crop monitoring",
    "maturity": 0.8,
    "dependencies": ["CMP-005"],
    "alternatives": ["CMP-003a (LiDAR-only navigation)"]
  },
  {
    "id": "CMP-004",
    "name": "GPS",
    "description": "RTK-GPS for centimeter-level positioning",
    "maturity": 0.95,
    "dependencies": [],
    "alternatives": ["CMP-004a (visual odometry)"]
  },
  {
    "id": "CMP-005",
    "name": "processors",
    "description": "Edge computing processors for real-time navigation and decision-making",
    "maturity": 0.85,
    "dependencies": ["CMP-006"],
    "alternatives": ["CMP-005a (cloud computing with 5G link)"]
  },
  {
    "id": "CMP-006",
    "name": "batteries",
    "description": "Li-ion battery system with solar charging",
    "maturity": 0.9,
    "dependencies": [],
    "alternatives": ["CMP-006a (diesel-electric hybrid)"]
  },
  {
    "id": "CMP-007",
    "name": "communications",
    "description": "Cellular or LoRaWAN for fleet coordination and remote monitoring",
    "maturity": 0.9,
    "dependencies": [],
    "alternatives": ["CMP-007a (satellite link)"]
  }
]
```

---

## Decomposition rules

1. **Atomic components have no dependencies.** A component that cannot be further decomposed has `dependencies: []`.
2. **Every component must have at least one alternative.** A component with no alternatives is a single-point-of-failure. If no alternative exists, record `alternatives: ["NONE — single source of supply"]`.
3. **Maturity is normalized TRL.** `maturity = TRL / 9`. A component at TRL 9 (commercial) has maturity 1.0. A component at TRL 3 (lab) has maturity 0.33.
4. **Dependencies form a DAG.** The dependency graph (DEPENDENCY_GRAPH.md) must be acyclic. If a cycle is detected, the decomposition is invalid.

---

## What this engine does NOT do

- It does not source components from suppliers. That is the Manufacturing Engine's job.
- It does not evaluate component quality. That is the Simulation Engine's job.
- It does not estimate component cost. That is the Economic Engine's job.
- It does not generate the dependency graph. It provides the data; DEPENDENCY_GRAPH.md builds the graph.

---

## Pre-stated falsifier (EP-4)

**Claim:** Every physical/logical object can be decomposed into components using this schema.

**Falsifier:** An object that cannot be decomposed — i.e., an object where no component breakdown is possible, or where the components do not have dependencies or alternatives.

**Status:** PENDING. No objects have been decomposed (no implementation).
