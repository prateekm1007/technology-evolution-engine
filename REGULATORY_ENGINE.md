# REGULATORY_ENGINE

**Status:** Phase 16A Deliverable 7.
**Location:** repo root.
**Phase:** 16A.

---

## Purpose

The Regulatory Engine identifies the regulatory pathway for an
idea: which jurisdictions, which authorities, which requirements,
which risks. It feeds the Constraint Engine (regulatory constraints)
and the Execution Engine (regulatory milestones in the timeline).

---

## Schema

```typescript
interface Regulation {
    jurisdiction: string
    authority: string
    requirement: string
    risk: number
}
```

### Field semantics

| Field | Type | Required | Meaning |
|---|---|---|---|
| `jurisdiction` | string | yes | The regulatory jurisdiction (e.g., "US-FDA", "EU-EMA", "US-FAA", "US-FCC", "global-IEC"). |
| `authority` | string | yes | The specific regulatory authority (e.g., "FDA-CDER", "FAA-AVR", "FCC-WTB"). |
| `requirement` | string | yes | The specific requirement (e.g., "Phase III clinical trial", "Type Certificate", "Spectrum auction participation"). |
| `risk` | float [0, 1] | yes | The probability that this regulatory pathway will block or delay the idea. 0 = no risk; 1 = certain blocker. |

---

## Example

### Autonomous farming robot

```json
[
  {
    "jurisdiction": "US-States",
    "authority": "State-DOT",
    "requirement": "Autonomous vehicle operation permit (varies by state)",
    "risk": 0.6
  },
  {
    "jurisdiction": "US-Federal",
    "authority": "EPA",
    "requirement": "Pesticide application certification (if robot applies pesticides)",
    "risk": 0.4
  },
  {
    "jurisdiction": "EU",
    "authority": "EU-Commission",
    "requirement": "CE marking + Machinery Directive 2006/42/EC compliance",
    "risk": 0.5
  },
  {
    "jurisdiction": "India",
    "authority": "MoTA",
    "requirement": "No specific autonomous vehicle regulation for agricultural use (permissive)",
    "risk": 0.1
  }
]
```

---

## Regulatory pathway analysis

1. **Identify applicable jurisdictions.** Where will the idea be deployed? (US, EU, India, China, global?)
2. **Identify authorities.** Which regulatory bodies have jurisdiction? (FDA, FAA, FCC, EPA, EMA, IEC, etc.)
3. **Identify requirements.** What must be done to comply? (Testing, certification, documentation, fees.)
4. **Assess risk.** How likely is this pathway to block or delay? Based on: (a) historical approval rates, (b) regulatory complexity, (c) jurisdictional precedent.
5. **Flag high-risk regulations.** Regulations with `risk > 0.7` are critical-path items for the Execution Engine.

---

## Relationship to constraint engine

The Regulatory Engine feeds the Constraint Engine:

- Each Regulation with `risk > 0.5` becomes a REGULATION constraint.
- Severity = `risk` value.
- Probability = `risk` value (probability the regulation blocks execution).
- Mitigation = ["Engage regulator early", "Hire regulatory consultant", "Pilot in permissive jurisdiction first"].

---

## Relationship to frozen formula

The frozen formula does not use regulatory_state. The Phase 12
ablation did not include regulatory data. The Regulatory Engine is
a new component that addresses one of the boundary patterns
(Pattern 2: coordination/regulatory) identified in Phase 14R.

---

## What this engine does NOT do

- It does not provide legal advice. It identifies pathways; legal counsel validates.
- It does not guarantee approval. Risk is an estimate, not a promise.
- It does not handle regulatory changes over time. Regulations are current-state only.
- It does not modify the frozen formula.

---

## Pre-stated falsifier (EP-4)

**Claim:** The 4-field Regulation schema captures all regulatory information needed to evaluate an idea's pathway.

**Falsifier:** A regulatory pathway that cannot be expressed in this schema — e.g., a pathway that requires modeling the regulatory body's internal decision process, or that involves multi-jurisdictional harmonization.

**Status:** PENDING. No regulatory analyses have been conducted (no implementation).
