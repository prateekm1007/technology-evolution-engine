# VALIDATION_LEVEL_ENGINE

**Status:** Honesty Loop Priority 5 engine (specification).
**Location:** repo root.
**Phase:** Honesty Loop v1.0 / P5.
**Triggered by:** Consolidated review finding — "This system
needs explicit maturity levels. L0 hypothesis → L9 production
deployment."

> A claim without a maturity level is a claim without a
> history. "58% confidence" tells you nothing about whether
> the claim has been measured, simulated, or merely asserted.
> L0-L9 tells you exactly which.
> — Consolidated review, post-BP-2

---

## Purpose

The Validation Level Engine assigns every claim in a Blueprint
to one of 10 maturity levels (L0-L9). The level declares what
kind of evidence supports the claim — from "we asserted it"
(L0) to "we measured it at production scale" (L9). This
replaces confidence percentages (Law 27) with a typed, ordered,
monotone scale that cannot be inflated.

This is Priority 5 because it is the direct mechanical
replacement for the forbidden numerical confidence. Every
claim that previously carried "confidence: 0.58" now carries
"validation_level: L2" — and the level has a precise meaning
that the number never did.

---

## The 10 levels

```text
L0  HYPOTHESIS
    No evidence beyond the claim itself.
    Example: "Self-healing electrolyte additives could extend cycle life."
    Permitted in: CONCEPT packages only.

L1  LITERATURE_SUPPORT
    Published sources exist, but no first-party analysis or experiment.
    Example: "LFP cycle life: 4000 cycles (Yang et al. 2022, EV-001)."
    Permitted in: CONCEPT, DECISION packages.

L2  ANALYTICAL_ESTIMATE
    Derived from first principles; no numerical model, no physical test.
    Example: "Pack energy density 160 Wh/kg = cell (172) × overhead (0.93)."
    Permitted in: CONCEPT, DECISION, EVALUATION packages.

L3  NUMERICAL_MODEL
    Governing equations solved numerically (FEA, CFD, circuit sim).
    Example: "Thermal CFD: 4.8°C cell-to-coolant ΔT at 2C discharge."
    Permitted in: EVALUATION, PROTOTYPE packages.

L4  BENCH_VALIDATION
    Physical test on a sub-scale unit (single cell, single module).
    Example: "Single-cell 2C cycle test: 3500 cycles to 80% DoD."
    Permitted in: EVALUATION, PROTOTYPE, PRODUCTION packages.

L5  SUBSYSTEM_VALIDATION
    Physical test on a full subsystem (full module, full pack).
    Example: "Module-level 1C cycle test: 3200 cycles to 80% DoD."
    Permitted in: PROTOTYPE, PRODUCTION packages.

L6  PROTOTYPE
    Full prototype tested in lab.
    Example: "Pack-level 1C cycle test: 3000 cycles to 80% DoD on Prototype-1."
    Permitted in: PROTOTYPE, PRODUCTION packages.

L7  PILOT_DEPLOYMENT
    Tested in real environment, small fleet.
    Example: "10 packs deployed in pilot fleet, 6-month data, 2 failures."
    Permitted in: PRODUCTION packages.

L8  PRODUCTION_CANDIDATE
    Pre-production units built and tested; design frozen for production.
    Example: "500 production-intent packs built, DVP completed."
    Permitted in: PRODUCTION packages.

L9  PRODUCTION_DEPLOYMENT
    At production scale, measured against reality.
    Example: "50,000 packs deployed, field data: 0.04% warranty rate / 12 months."
    Permitted in: PRODUCTION packages.
```

---

## Schema

```typescript
interface ValidationAssignment {
    claimId: string                          // CL-XXX — the claim being assigned
    validationLevel: "L0" | "L1" | "L2" | "L3" | "L4" | "L5" | "L6" | "L7" | "L8" | "L9"
    supportingEvidence: {
        evidenceId: string                   // EV-XXX from Evidence Lineage (P1)
        testRegistryId?: string              // TR-XXX from Test Registry (P8), if L3+
    }[]
    promotionPath: string[]                  // the L0→L1→...→L9 path the claim has walked
    nextPromotionRequirement?: string        // what evidence is needed to advance one level
    lastPromotedAt?: string                  // ISO 8601
    retractionId?: string                    // if the claim was demoted (P7)
    status: "PASS" | "PASS_WITH_CONDITIONS" | "MARGINAL" | "BLOCKED" | "REJECTED"
}
```

---

## Promotion rules

1. **Promotion is monotone in evidence.** A claim advances
   from Ln to L(n+1) only when the next-level evidence
   threshold is met. Demotion (via retraction) is permitted
   when evidence is found to be flawed.

2. **Each promotion requires specific evidence.**
   - L0 → L1: cite at least one rank-D+ source (academic literature).
   - L1 → L2: provide the derivation chain (first-principles calculation).
   - L2 → L3: provide the numerical model file and its output.
   - L3 → L4: provide the bench test report (TR-XXX in Test Registry, P8).
   - L4 → L5: provide the subsystem test report.
   - L5 → L6: provide the full-prototype test report.
   - L6 → L7: provide the pilot deployment data (small fleet, real env).
   - L7 → L8: provide the production-intent build report + DVP results.
   - L8 → L9: provide the field deployment data (production scale, >1 year).

3. **A claim's validation level cannot exceed its evidence's
   rank-derived ceiling.** Rank-I (LLM inference) evidence
   supports at most L0. Rank-A (physics/experiment) evidence
   supports up to L9.

4. **Package maturity gates the maximum permitted validation
   level.** A CONCEPT package (Law 29d) may contain claims up
   to L2 only. A PRODUCTION package may contain claims at
   any level, but PRODUCTION-critical claims (e.g., safety)
   must be at least L7.

5. **Demotion is a retraction.** If a claim at L4 is found
   to have a flawed bench test, it is demoted to L1 (or L0)
   and a retraction is registered (P7). The original L4
   status is not silently edited.

---

## Example assignment

```
claimId: CL-014
statement: "Pack energy density: 160 Wh/kg"

validationLevel: L2

supportingEvidence:
  - evidenceId: EV-001  (cell energy density: 172 Wh/kg, rank A, measured)
  - evidenceId: EV-002  (overhead factor 0.93, rank D, derived from first principles)

promotionPath: ["L0", "L1", "L2"]
nextPromotionRequirement: "Build a pack, measure energy density on Prototype-1 (target: L6)."
lastPromotedAt: 2024-08-01T10:00:00Z

status: PASS
```

Without this engine, the claim "160 Wh/kg" carried
"confidence: 0.85" — a number that told the reader nothing.
With this engine, the claim carries L2 — the reader knows
the claim is an analytical estimate, not a measurement.

---

## What this engine does NOT do

- It does not assign levels automatically. Assignment is a
  judgment, made by the producing agent, against the rules
  above. The engine verifies the assignment is consistent
  with the evidence; it does not replace the judgment.
- It does not promote claims without evidence. Promotion
  requires the next-level evidence to be present in the
  Evidence Lineage (P1) and, for L3+, a Test Registry entry
  (P8).
- It does not compute a "confidence." Per Law 27, numerical
  certainty is forbidden. The level IS the certainty.

---

## Pre-stated falsifier (EP-4)

**Claim:** Every claim in a Blueprint can be assigned a
validation level from L0 to L9, and the assignment is
verifiable against the supporting evidence.

**Falsifier:** A claim whose assigned level exceeds what
the supporting evidence permits — e.g., an L4 assignment
with no bench test report in the Test Registry. Such
assignments are marked `STATUS: REJECTED` and the claim
is demoted to the highest level the evidence supports.

**Status:** PENDING. Engine specified; implementation
awaits AEP Gate 1 for the engine itself.
