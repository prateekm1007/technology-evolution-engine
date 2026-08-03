# MASS_STACKUP_ENGINE

**Status:** Honesty Loop Priority 2 engine (specification).
**Location:** repo root.
**Phase:** Honesty Loop v1.0 / P2.
**Governance:** Per BLUEPRINT_CONSTITUTION.md Law 27 (no numerical certainty without experimental validation), Law 28a (no "complete blueprint"), Law 29 (required typed status enums). See HONESTY_LOOP.md.
**Triggered by:** Consolidated review finding — "The figure of
584 kg is unsupported."

> A mass total without a stack-up is a guess with units.
> The auditor wants to see every component that contributes
> mass, with its mass, and a margin. Only then may the total
> be computed.
> — Consolidated review, post-BP-2

---

## Purpose

The Mass Stack-up Engine produces a per-component mass table
that must sum to the claimed total mass of an assembly. It
forbids bare mass totals ("584 kg") and requires the stack-up
as the only permitted form.

This is Priority 2 because mass is the most common place where
Blueprints manufacture unsupported numbers. A mass claim
propagates to energy density, to vehicle weight, to motor
sizing, to cost — every downstream calculation inherits the
lie. The stack-up is the only defense.

---

## Schema

```typescript
interface MassStackUp {
    assemblyId: string                  // the assembly this stack-up describes
    totalMassKg: number                 // the claimed total — MUST equal sum(rows) + margin
    rows: MassRow[]
    margin: MassMargin
    status: "PASS" | "PASS_WITH_CONDITIONS" | "MARGINAL" | "BLOCKED" | "REJECTED"
    evidenceLineageIds: string[]        // EV-XXX IDs (P1) — every row mass must trace to evidence
    retractionId?: string               // if this stack-up retracts a prior bare mass claim (P7)
}

interface MassRow {
    componentId: string                 // CMP-XXX from COMPONENT_ENGINE
    componentName: string
    massKg: number                       // the mass of this component
    count: number                        // how many of this component (default 1)
    subtotalKg: number                   // massKg * count — computed, not entered
    evidenceId: string                   // EV-XXX from Evidence Lineage (P1)
    measurementMethod: "WEIGHED" | "SPEC_SHEET" | "CAD_VOLUME_DENSITY" | "ESTIMATED_FROM_ANALOG" | "UNKNOWN"
    measurementDate?: string            // ISO 8601 — when this mass was measured/specified
    notes?: string
}

interface MassMargin {
    kg: number                           // the margin added to cover uncounted mass
    percentage: number                   // margin / total, computed
    rationale: string                    // why this margin, not larger or smaller
    evidenceId?: string                  // EV-XXX supporting the margin choice
}
```

### Required row categories

Every mass stack-up must include AT LEAST the following categories
of rows. A stack-up that omits any category is `STATUS: BLOCKED`.

| # | Category | Why required |
|---|---|---|
| 1 | cells | The active material — usually the largest mass |
| 2 | coolant | Liquid coolant mass is routinely forgotten |
| 3 | busbars | Conductors are dense and numerous |
| 4 | housing | The enclosure, often the second-largest mass |
| 5 | insulation | Thermal + electrical, often underestimated |
| 6 | harnesses | Wiring adds up across a pack |
| 7 | fasteners | Bolts, brackets, clips — individually trivial, collectively significant |
| 8 | mounts | Structural attachment to the vehicle |
| 9 | margin | Explicit allowance for uncounted mass |

A stack-up that lists only "cells + housing + margin" is forbidden.
Every category must appear. If a category is genuinely zero (e.g.,
an air-cooled pack has no coolant), the row must be present with
`massKg: 0` and a `notes` field explaining why.

---

## Stack-up rules

1. **`totalMassKg` must equal `sum(rows.subtotalKg) + margin.kg`.**
   The engine recomputes this and rejects the stack-up if the
   arithmetic does not match. A tolerance of 0.001 kg is permitted
   for floating-point rounding only.

2. **Every row must have an evidence ID.** A row mass with no
   upstream evidence (P1 Evidence Lineage) is a guess. The row
   must be marked `STATUS: BLOCKED` until evidence is supplied.

3. **`measurementMethod` must be declared.** "584 kg" with no
   measurement method is forbidden. The method determines the
   validation level (P5): WEIGHED → L4+, SPEC_SHEET → L1,
   CAD_VOLUME_DENSITY → L2, ESTIMATED_FROM_ANALOG → L1,
   UNKNOWN → L0.

4. **Margin must be justified.** A 15% margin "because that's
   what we always do" is forbidden. The rationale must reference
   the specific categories of uncounted mass the margin covers.

5. **Retraction is required if the stack-up contradicts a
   prior bare mass claim.** If the Blueprint previously stated
   "total mass: 584 kg" and the stack-up reveals the total is
   612 kg, the prior claim is retracted via P7 (Retraction
   Registry) — not silently edited.

---

## Example stack-up

```
assemblyId: PACK-001
totalMassKg: 612.4

rows:
  - cells         18.2 kg × 24 = 436.8 kg   (EV-101, WEIGHED, 2024-03-15)
  - coolant        1.1 kg ×  6 =   6.6 kg   (EV-102, SPEC_SHEET)
  - busbars        0.4 kg × 96 =  38.4 kg   (EV-103, WEIGHED)
  - housing       72.0 kg ×  1 =  72.0 kg   (EV-104, CAD_VOLUME_DENSITY)
  - insulation     8.5 kg ×  1 =   8.5 kg   (EV-105, SPEC_SHEET)
  - harnesses      6.2 kg ×  1 =   6.2 kg   (EV-106, WEIGHED)
  - fasteners      14.0 kg ×  1 =  14.0 kg   (EV-107, ESTIMATED_FROM_ANALOG)
  - mounts         18.0 kg ×  1 =  18.0 kg   (EV-108, CAD_VOLUME_DENSITY)
  - margin         12.9 kg ×  1 =  12.9 kg   (rationale: fasteners+clips undercount)

subtotal: 612.4 - 12.9 = 599.5 kg
margin:   12.9 kg (2.15%)
total:    612.4 kg ✓

status: PASS_WITH_CONDITIONS
  (condition: fasteners mass is ESTIMATED_FROM_ANALOG — re-weigh at prototype)
```

Without this stack-up, the prior "584 kg" claim is a bare number
with no arithmetic, no evidence, and no margin. The auditor is
correct to reject it.

---

## What this engine does NOT do

- It does not weigh components. Physical measurement is upstream.
- It does not compute energy density. Energy density is a derived
  quantity that USES the stack-up output, computed downstream.
- It does not optimize mass. Optimization is Era 2 (BP-2).

---

## Pre-stated falsifier (EP-4)

**Claim:** Every mass claim in a Blueprint can be replaced by a
stack-up that sums to the claimed total.

**Falsifier:** A mass claim where the stack-up cannot be
constructed — i.e., the components are not enumerated, the
per-component mass is unknown, and no margin can be honestly
justified. Such claims must be `STATUS: BLOCKED`, not
`STATUS: PLAUSIBLE`.

**Status:** PENDING. Engine specified; implementation awaits
AEP Gate 1 for the engine itself.
