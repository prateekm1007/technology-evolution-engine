# RETRACTION_REGISTRY_ENGINE

**Status:** Honesty Loop Priority 7 engine (specification).
**Location:** repo root.
**Phase:** Honesty Loop v1.0 / P7.
**Triggered by:** Consolidated review finding — "Most systems
quietly edit their mistakes. Your system says: claim →
contradiction → retraction → replacement. That is
extraordinarily valuable."

> A system that edits its mistakes silently is a system
> that cannot be trusted. A system that names its mistakes,
> dates them, and replaces them, is a system that learns.
> The Retraction Registry is how the system names them.
> — Consolidated review, post-BP-2

---

## Purpose

The Retraction Registry Engine maintains an append-only ledger
of every claim that has been retracted. A retracted claim is
not deleted — it is marked RETRACTED, with a reason, a date,
a replacement (if any), and a retraction ID. The registry
is the system's memory of its own errors.

This is Priority 7 because the EV battery blueprint demonstrated
the value of retractions: 2 FATAL consistency violations were
caught and corrected, and the corrections were documented.
The Retraction Engine formalizes this practice so it is
mandatory, not best-effort.

---

## Schema

```typescript
interface RetractionRecord {
    id: string                                // RT-XXX, immutable
    retractedClaimId: string                  // CL-XXX — the claim being retracted
    retractedClaimStatement: string            // verbatim copy of the retracted claim
    retractedClaimEvidenceId?: string         // EV-XXX that supported the claim (now invalid)
    retractionDate: string                    // ISO 8601
    retractionAgent: string                    // who/what retracted (human name, script, LLM)
    reason: {
        category: "NUMERICAL_CONTRADICTION" | "SEMANTIC_CONTRADICTION" |
                  "EVIDENCE_INVALIDATED" | "MEASUREMENT_SUPERSEDED" |
                  "ASSUMPTION_FALSIFIED" | "KILL_TEST_FAILED" |
                  "DESIGN_CHANGE" | "EXTERNAL_AUDIT"
        description: string                   // the specific reason
        detectedBy: string                     // which engine or agent detected it
        detectionDate: string                 // when the contradiction was detected
    }
    replacement?: {
        claimId: string                       // CL-XXX — the replacement claim
        evidenceId: string                     // EV-XXX supporting the replacement
        derivation: string                    // how the replacement was derived
    }
    status: "RETRACTED" | "SUPERSEDED" | "WITHDRAWN"
    relatedRetractionIds?: string[]            // if multiple claims were retracted together
    immutable: true                           // the record cannot be edited once written
}
```

---

## Retraction rules

1. **The registry is append-only.** A retraction record,
   once written, cannot be edited, deleted, or amended.
   If the retraction itself was in error, a new retraction
   record is added that retracts the retraction — and both
   records remain in the registry.

2. **Every retracted claim is marked in place.** The
   retracted claim is not removed from its source document.
   It is marked `[RETRACTED: RT-XXX, see Retraction Registry]`
   in place, with a link to the registry entry.

3. **Every retraction has a reason.** The reason must specify
   the category, a description, who detected it, and when.
   Vague reasons ("incorrect") are forbidden.

4. **Every retraction has a replacement OR an explicit
   withdrawal.** A retraction without a replacement leaves
   a hole in the blueprint. If no replacement is available,
   the retraction record must include `status: WITHDRAWN`
   and the blueprint must mark the affected section as
   `STATUS: BLOCKED`.

5. **Retractions propagate downstream.** If a claim is
   retracted, all claims that depend on it (per the
   Evidence Lineage DAG, P1) are flagged for review.
   Downstream claims that cannot be re-derived from
   remaining evidence are also retracted.

6. **Retractions are recorded even for fixes.** A bug fix
   that changes a numerical output is a retraction: the old
   output is retracted, the new output is the replacement.
   This is the only way to maintain an honest history.

---

## The retraction lifecycle

```
    Original claim (CL-001)
        │
        │  ← contradiction detected (by consistency engine,
        │     kill-test, audit, or reality feedback)
        ▼
    Retraction registered (RT-001)
        │
        ├── retractedClaimId: CL-001
        ├── reason: NUMERICAL_CONTRADICTION
        ├── detectedBy: consistency_engine
        ├── detectionDate: 2024-08-15T10:30:00Z
        │
        ▼
    Replacement derived
        │
        ├── new evidence (EV-XXX) or new calculation
        ├── new claim (CL-002)
        │
        ▼
    Replacement recorded in RT-001
        │
        ├── replacement.claimId: CL-002
        ├── replacement.evidenceId: EV-XXX
        ├── replacement.derivation: "stack-up computed from
        │   per-component masses; see MASS_STACKUP_ENGINE"
        │
        ▼
    Source document updated
        │
        ├── CL-001 marked "[RETRACTED: RT-001]"
        ├── CL-002 added with full typed wrapper (Law 29e)
        │
        ▼
    Downstream claims reviewed
        │
        ├── claims that depended on CL-001
        ├── re-derived from CL-002 if possible
        ├── retracted (RT-002, RT-003...) if not
```

---

## Example retraction

```
RT-001:

  retractedClaimId: CL-007
  retractedClaimStatement: "Total pack mass: 584 kg"
  retractedClaimEvidenceId: EV-007 (rank H — general web source)

  retractionDate: 2024-08-15T14:22:00Z
  retractionAgent: "consistency_engine (auto)"

  reason:
    category: NUMERICAL_CONTRADICTION
    description: "Mass 584 kg + energy 75 kWh + volume 0.47 m³
                  → energy density 161 Wh/kg, 160 Wh/L. But cell-level
                  energy density is 172 Wh/kg. Pack overhead 0.93
                  → pack density 160 Wh/kg. 584 kg × 161 Wh/kg =
                  94 kWh ≠ 75 kWh. Mass is inconsistent with energy
                  and density."
    detectedBy: consistency_engine
    detectionDate: 2024-08-15T14:21:55Z

  replacement:
    claimId: CL-014
    evidenceId: EV-101 (rank A — measured per-component masses)
    derivation: "Mass stack-up: cells 436.8 + coolant 6.6 + busbars 38.4
                 + housing 72.0 + insulation 8.5 + harnesses 6.2
                 + fasteners 14.0 + mounts 18.0 + margin 12.9 = 612.4 kg.
                 See MASS_STACKUP_ENGINE.md, IF-001."

  status: RETRACTED
  relatedRetractionIds: [RT-002 (energy density claim), RT-003 (vehicle weight claim)]
  immutable: true
```

---

## What this engine does NOT do

- It does not detect contradictions. Detection is upstream
  (consistency engine, kill-test engine, adversarial gate).
- It does not write replacements. Replacement derivation is
  upstream (the engines that produce the new claim).
- It does not edit source documents. Editing is done by the
  producing agent; the registry records WHAT was retracted
  and WHY, not the edit itself.

---

## Pre-stated falsifier (EP-4)

**Claim:** Every retraction in the system is recorded in the
Retraction Registry, with a reason, a date, and a replacement
or explicit withdrawal.

**Falsifier:** A claim in a Blueprint that has been silently
edited (i.e., the document changed but no retraction record
exists). Such edits are forbidden; they are entropy (per
ANTI_ENTROPY.md principle 4 — "A capability isn't shipped
until it writes to the system of record").

**Status:** PENDING. Engine specified; implementation awaits
AEP Gate 1 for the engine itself.
