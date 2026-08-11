# DEPENDENCY_GRAPH

**Status:** Phase 16A Deliverable 5.
**Location:** repo root.
**Phase:** 16A.

> Construct causal relationships.
> — CEO directive, Phase 16A

---

## Purpose

The Dependency Graph builds causal relationships between components.
It is a directed acyclic graph (DAG) where nodes are components and
edges are dependencies. The graph determines the execution order:
which components must exist before others can be built.

---

## Schema

```typescript
interface Dependency {
    id: string
    fromComponent: string    // CMP-XXX
    toComponent: string      // CMP-XXX
    dependencyType: "REQUIRES" | "ENABLES" | "CONSTRAINS"
    strength: number         // [0, 1]
}
```

### Field semantics

| Field | Type | Required | Meaning |
|---|---|---|---|
| `id` | string | yes | DEP-XXX identifier. |
| `fromComponent` | string | yes | The source component. |
| `toComponent` | string | yes | The target component. |
| `dependencyType` | enum | yes | REQUIRES: from needs to exist before to can be built. ENABLES: from makes to possible. CONSTRAINS: from limits to. |
| `strength` | float [0, 1] | yes | How strong the dependency is. 1 = absolute (cannot build without); 0 = weak (nice to have). |

---

## Example

```
battery density
        │
        ▼
electric motors
        │
        ▼
autonomous mobility
        │
        ▼
agricultural robotics
```

```json
[
  {
    "id": "DEP-001",
    "fromComponent": "CMP-BATTERY-DENSITY",
    "toComponent": "CMP-ELECTRIC-MOTORS",
    "dependencyType": "REQUIRES",
    "strength": 0.9
  },
  {
    "id": "DEP-002",
    "fromComponent": "CMP-ELECTRIC-MOTORS",
    "toComponent": "CMP-AUTONOMOUS-MOBILITY",
    "dependencyType": "ENABLES",
    "strength": 0.8
  },
  {
    "id": "DEP-003",
    "fromComponent": "CMP-AUTONOMOUS-MOBILITY",
    "toComponent": "CMP-AGRICULTURAL-ROBOTICS",
    "dependencyType": "ENABLES",
    "strength": 0.7
  }
]
```

---

## Graph construction protocol

1. **Collect components** from COMPONENT_ENGINE.md.
2. **Identify dependencies** by asking: "Can this component be built without that component?"
3. **Classify dependency type:**
   - REQUIRES: from must exist before to can be built (hard dependency).
   - ENABLES: from makes to possible but to could exist in a weaker form without from (soft dependency).
   - CONSTRAINS: from limits to's performance or capability (constraint dependency).
4. **Assess strength:** 1 = absolute blocker; 0.5 = significant but not blocking; 0 = weak.
5. **Check for cycles.** The graph must be a DAG. If a cycle is detected, the decomposition is invalid and must be revised.

---

## Critical path analysis

The dependency graph enables critical path analysis:

1. **Find the longest path** from any leaf component (no dependencies) to the root (the idea).
2. **The longest path is the critical path** — the minimum time to build the idea.
3. **Components on the critical path** are bottlenecks. Delaying them delays the entire project.
4. **Components NOT on the critical path** have slack. They can be delayed without affecting the timeline (up to their slack).

---

## Example: Autonomous farming robot critical path

```
GPS (maturity 0.95)
    │
    ├── REQUIRES → processors (maturity 0.85)
    │                   │
    │                   ├── REQUIRES → batteries (maturity 0.9)
    │                   │
    │                   └── REQUIRES → sensors (maturity 0.9)
    │
    └── ENABLES → autonomous navigation (maturity 0.7)
                        │
                        └── ENABLES → agricultural robotics (maturity 0.6)
```

Critical path: GPS → processors → autonomous navigation → agricultural robotics.
Length: 4 edges. If each edge takes 1 year, minimum time = 4 years.

Bottlenecks (on critical path):
- autonomous navigation (maturity 0.7 — lowest maturity on path)
- agricultural robotics (maturity 0.6 — the idea itself)

Non-critical:
- batteries (maturity 0.9 — high maturity, has slack)
- sensors (maturity 0.9 — high maturity, has slack)

---

## What this graph does NOT do

- It does not estimate time per edge. Time estimation is the Execution Engine's job.
- It does not include alternatives. The alternatives are in COMPONENT_ENGINE.md; the graph uses the primary component.
- It does not handle temporal dynamics (dependencies that change over time). The graph is static.
- It does not modify the frozen formula. The formula's adjacency term is a simplified dependency graph (graph distance), not a full causal DAG.

---

## Pre-stated falsifier (EP-4)

**Claim:** Every causal relationship between components can be expressed as a Dependency in this schema.

**Falsifier:** A causal relationship that cannot be classified as REQUIRES, ENABLES, or CONSTRAINS — i.e., a relationship that is a different type of dependency (e.g., "PREFERS" or "COMPETES_WITH").

**Status:** PENDING. No dependency graphs have been constructed (no implementation).
