# REQUIREMENT_RECONCILIATION_ENGINE

**Status:** Honesty Loop Priority 6 engine (specification).
**Location:** repo root.
**Phase:** Honesty Loop v1.0 / P6.
**Governance:** Per BLUEPRINT_CONSTITUTION.md Law 27 (no numerical certainty), Law 28 (forbidden language), Law 29 (typed status enums). See HONESTY_LOOP.md.
**Triggered by:** Consolidated review finding — "You cannot
simultaneously state CTP architecture and module replacement
without reconciliation."

> A requirement that contradicts another requirement is not
> a requirement — it is a contradiction. The blueprint's job
> is to detect contradictions before the manufacturer finds
> them on the assembly line.
> — Consolidated review, post-BP-2

---

## Purpose

The Requirement Reconciliation Engine classifies every
requirement in a Blueprint as MANDATORY, DESIRABLE,
ASPIRATIONAL, or EXPERIMENTAL, then detects contradictions
between requirements of equal or higher priority. A blueprint
with unresolved contradictions is rejected at Gate 11
(Loop Closure).

This is Priority 6 because the EV battery blueprint shipped
with a contradiction (CTP + module-replacement) that the
existing consistency engine (which checks numerical
contradictions) did not catch — because the contradiction
was between two textual requirements, not two numbers.

---

## Requirement classification

```text
MANDATORY
    A requirement that, if unmet, makes the design fail in
    its primary purpose. Cannot be traded away.
    Example: "Pack voltage: 307 V nominal (96S × 3.2V)."

DESIRABLE
    A requirement that improves the design but is not strictly
    necessary. May be traded with justification.
    Example: "Pack mass < 600 kg (target)."

ASPIRATIONAL
    A stated goal that the design aims for but is not committed
    to. Failure to meet is acceptable; effort is noted.
    Example: "Cycle life > 6000 cycles (stretch)."

EXPERIMENTAL
    A requirement being tested for inclusion in a future revision.
    Not binding on the current design.
    Example: "V2G bidirectional capability (experimental)."
```

---

## Schema

```typescript
interface RequirementRecord {
    id: string                                // R-XXX
    statement: string                        // the requirement
    classification: "MANDATORY" | "DESIRABLE" | "ASPIRATIONAL" | "EXPERIMENTAL"
    source: string                            // who/what stated this requirement
    rationale: string                         // why it exists
    evidenceId: string                        // EV-XXX (P1) — supports the classification
    conflictsWith?: ConflictRecord[]          // detected contradictions with other requirements
    reconciliation?: ReconciliationRecord     // how the conflict was resolved (if resolved)
    status: "PASS" | "PASS_WITH_CONDITIONS" | "MARGINAL" | "BLOCKED" | "REJECTED"
}

interface ConflictRecord {
    requirementId: string                     // the conflicting R-XXX
    conflictType: "DIRECT" | "PARTIAL" | "TENSION"
    description: string                       // what the contradiction is
    detectionMethod: "MANUAL" | "RULE_BASED" | "SEMANTIC"
}

interface ReconciliationRecord {
    method: "TRADING" | "REQUIREMENT_DEMOTION" | "REQUIREMENT_RETRACTION" | "DESIGN_CHANGE"
    description: string                       // how the conflict was resolved
    evidenceId: string                        // supports the reconciliation
    retractionId?: string                      // if a requirement was retracted (P7)
    date: string                              // ISO 8601
    agent: string                             // who/what reconciled
}
```

---

## Conflict detection rules

1. **Two MANDATORY requirements cannot directly conflict.**
   If R-001 (MANDATORY: "Cell-to-Pack, welded busbar") and
   R-002 (MANDATORY: "Module-level field replacement, 30 min
   R&R") both exist, the engine detects a DIRECT conflict
   and marks both `STATUS: REJECTED`.

2. **A MANDATORY requirement overrides a DESIRABLE one.**
   If R-001 (MANDATORY) and R-003 (DESIRABLE) conflict,
   the engine marks R-003 as overridden. The conflict is
   recorded but does not block.

3. **Two DESIRABLE requirements may be in tension.**
   The conflict is recorded as `conflictType: TENSION` and
   the engine marks both `STATUS: PASS_WITH_CONDITIONS`
   with a condition that the tension be acknowledged in
   the design rationale.

4. **ASPIRATIONAL and EXPERIMENTAL requirements do not block.**
   They may conflict with anything; the conflict is recorded
   but the requirements pass.

5. **Reconciliation must be honest.** A reconciliation record
   must specify the method (TRADING / REQUIREMENT_DEMOTION /
   REQUIREMENT_RETRACTION / DESIGN_CHANGE). Silently editing
   a requirement is forbidden — the change must be recorded
   as a retraction (P7) if it changes the meaning, or a
   design change if it modifies the design.

---

## Canonical example: CTP vs module-replacement

```
R-001 (MANDATORY):
    "Cell-to-Pack (CTP) architecture: cells welded directly
     to pack busbar, no module housing."
    source: CEO directive
    rationale: "Eliminate module housing mass to achieve 160 Wh/kg."

R-008 (MANDATORY):
    "Module-level field replacement: any module replaceable
     in 30 minutes by a field technician."
    source: customer requirement
    rationale: "Field serviceability; no factory return for cell failure."

CONFLICT DETECTED:
    conflictType: DIRECT
    description: "CTP architecture (R-001) eliminates module
                 housings; module replacement (R-008) requires
                 module housings. Both cannot be true."

RECONCILIATION REQUIRED:
    Options:
      (a) TRADING — demote R-008 to ASPIRATIONAL; ship CTP,
          accept that field service requires factory return.
      (b) REQUIREMENT_DEMOTION — demote R-001 to DESIRABLE;
          ship modular pack, accept 5-10% mass penalty.
      (c) DESIGN_CHANGE — design a hybrid (CTP modules that
          are individually field-replaceable); requires
          new interface design (P3).
      (d) REQUIREMENT_RETRACTION — retract one requirement
          entirely; register retraction in P7.

    Without one of (a)-(d), the blueprint is REJECTED.
```

This is exactly the contradiction the auditor caught. The
existing consistency engine (which checks numerical
contradictions like mass vs energy density) did not catch
it because the conflict is semantic, not numerical. The
Requirement Reconciliation Engine catches it.

---

## What this engine does NOT do

- It does not write requirements. Requirements are upstream
  (Gate 1 Comprehension of AEP).
- It does not prioritize requirements. Prioritization is
  a human judgment; the engine records the result.
- It does not enforce reconciliations. Enforcement is at
  Gate 11 (Loop Closure) — the blueprint cannot ship with
  unresolved MANDATORY conflicts.

---

## Pre-stated falsifier (EP-4)

**Claim:** Every pair of MANDATORY requirements in a Blueprint
can be reconciled or detected as conflicting.

**Falsifier:** A pair of MANDATORY requirements that the engine
fails to flag as conflicting, but that a human reviewer
identifies as contradictory. The engine's detection rules
(MANDATORY-MANDATORY direct conflict, semantic similarity)
must catch every such case, or the engine is incomplete.

**Status:** PENDING. Engine specified; implementation awaits
AEP Gate 1 for the engine itself.
