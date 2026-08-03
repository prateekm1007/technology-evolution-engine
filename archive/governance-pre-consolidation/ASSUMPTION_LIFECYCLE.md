# ASSUMPTION_LIFECYCLE — Phase 9 Post-Stress-Test

**Status:** constitutional document (assumption lifecycle states).
**Location:** repo root.
**Phase:** 9 (per CEO Instruction 2).

Assumptions are not permanent. They have a lifecycle — from proposal
through active use, questioning, falsification, replacement, and
retirement. This document defines the lifecycle states and tracks
where each assumption currently sits.

---

## Lifecycle states

```text
PROPOSED → ACTIVE → QUESTIONED → FALSIFIED → REPLACED or RETIRED
```

| State | Meaning |
|---|---|
| PROPOSED | An assumption has been suggested but not yet adopted. Under review. |
| ACTIVE | The assumption is in use. The model depends on it. It has not been challenged. |
| QUESTIONED | A stress test or observation has raised doubt. The assumption is under scrutiny but still in use. |
| FALSIFIED | The assumption's falsification criterion has been met. The assumption is wrong. The model must be updated. |
| REPLACED | A falsified assumption has been replaced by a new, narrower assumption. |
| RETIRED | A falsified assumption has been removed entirely. The model no longer depends on it. |

---

## Current assumption states

| Assumption | Original state | Current state | Action needed |
|---|---|---|---|
| A-001 (CPC ≈ capability) | ACTIVE | QUESTIONED | CPC is coarse, not precise. Narrow the claim: "CPC codes approximate the DOMAIN of a patent, not the specific CAPABILITY." |
| A-002 (10 capabilities sufficient) | ACTIVE | FALSIFIED | 5 innovations can't be expressed. Either expand the catalog (CEO auth) or narrow the vertical to "Li-ion intercalation" (SCOPE_V2.md). |
| A-003 (invariants stable across time) | ACTIVE | FALSIFIED | REQUIRES INTERCALATION is false pre-1991. Narrow EDGE-026 to Li-ion-specific or add temporal scope. |
| A-004 (5 patents representative) | ACTIVE | FALSIFIED | Sample is Li-ion-biased. Qualify all backtest results as "valid for Li-ion-adjacent technologies only." |
| A-005 (5 constraints most important) | ACTIVE | FALSIFIED | Manufacturing constraints missing. Either reinstate (CEO auth) or qualify: "model does not predict manufacturing-related failures." |

---

## The lifecycle rule

An assumption in FALSIFIED state MUST be acted on within the next
cycle. If it is not — if the model continues to depend on a falsified
assumption — then IMPOSSIBILITY_CRITERIA IC-006 is met and the
theory fails.

The actions available are:
1. **REPLACE** — replace the falsified assumption with a narrower one.
   (E.g., A-002 "10 capabilities sufficient for electrochemical
   storage" → A-002a "10 capabilities sufficient for Li-ion
   intercalation systems.")
2. **RETIRE** — remove the assumption entirely if it's not load-bearing.
3. **UPDATE** — modify the assumption to match reality (e.g., add
   temporal scope to A-003).

---

## Proposed replacements

### A-002 → A-002a (REPLACED)

**Original:** 10 capabilities are sufficient for the electrochemical
energy storage vertical.
**Replacement:** 10 capabilities are sufficient for Li-ion intercalation
systems. The model does not cover flow batteries, lead-acid, Na-ion,
Li-S, Li-air, or supercapacitors.

### A-003 → A-003a (REPLACED)

**Original:** Structural invariants are stable across time (1990-2026).
**Replacement:** Structural invariants specific to Li-ion chemistry
are stable across the period in which Li-ion is commercially relevant
(1991-2026). Pre-Li-ion invariants (lead-acid, NiCd) are out of scope.

### A-004 → A-004a (UPDATED)

**Original:** 5 patents are representative of electrochemical energy
storage.
**Updated:** 5 patents are representative of Li-ion intercalation
systems. They are NOT representative of the broader electrochemical
storage domain. Backtest results are qualified accordingly.

### A-005 → A-005a (UPDATED)

**Original:** 5 constraints are the most important for this vertical.
**Updated:** 5 constraints capture physics and regulatory limits for
Li-ion intercalation systems. Manufacturing constraints are NOT
covered. The model cannot predict manufacturing-related failures
(e.g., Samsung Note 7).

### A-001 (QUESTIONED, not yet replaced)

**Status:** CPC codes approximate the DOMAIN of a patent, not the
specific CAPABILITY. The mapping from CPC to capability is coarse.
This is acceptable for EMBODIED_IN edges (which record "this patent
is about this domain") but should not be over-interpreted as "this
patent enables this specific capability."

**Proposed action:** narrow the claim rather than falsify it. A-001
is INCONCLUSIVE, not FAILED. The assumption survives at a coarser
level of granularity.
