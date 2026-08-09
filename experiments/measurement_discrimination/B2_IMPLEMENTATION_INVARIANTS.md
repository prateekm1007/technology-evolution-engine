# B2 Implementation Invariants — R5.2 Freeze-Verification Corrections

**Status:** IMPLEMENTATION SPECIFICATION — not a design revision, not R5.3
**Date:** 2026-08-09
**Parent design:** B2_REVISION_R5_2.md (R5.2, accepted)
**Audit reference:** R5.2 adversarial review (round 45) — 1 freeze-blocking consistency defect + 1 edge case
**Statistical engine:** FROZEN at commit `39f5d37` — unchanged

---

## Purpose

This document specifies two implementation invariants that correct freeze-blocking issues in R5.2's seed specification and padding rule. These are **NOT design revisions** — they are implementation-level corrections that resolve internal contradictions in R5.2 without reopening the experimental design.

Per the auditor (round 45): "Do not write R5.3. The correct state is: R5.2 design SUBSTANTIVELY ACCEPTED. One freeze-blocking consistency defect: seed specification internally contradictory. Resolution: implementation/freeze invariant, not conceptual redesign."

---

## Invariant 1: Universal Seed Construction (Consistency Correction)

### The contradiction in R5.2

R5.2 defined two different seed rules:

**Rule A (universal):**
```
seed = SHA256(preregistration_id || case_id || stage_id)
```
where `stage_id` can be `"transfer"`, `"generation"`, `"null_generation"`, etc.

**Rule B (downstream):**
```
seed = SHA256(preregistration_id || case_id || "downstream")
```
for both engine and null.

These are contradictory: if Rule A is applied literally, engine uses `stage_id="transfer"` and null uses `stage_id="null_generation"`, producing **different seeds**. Rule B fixes this by using the same `stage_id="downstream"` for both arms, but then the `stage_id` is no longer the arm-specific value from Rule A.

### The Channel B problem

R5.2 also said Channel B uses:
```
seed = SHA256(preregistration_id || case_id || candidate_id || "channel_b")
```

But `candidate_id` is arm-specific (e.g., `CASE-001-ENGINE-CAND-001` vs `CASE-001-NULL-CAND-001`). Therefore the seeds differ across arms even though the "construction rule is identical."

**Identical construction rule ≠ identical seed.**

### Implementation invariant (correcting the contradiction)

```
UNIVERSAL SEED INVARIANT (implementation-level):

    For paired engine/null downstream generation:
        seed = SHA256(preregistration_id || case_id || "downstream")
        - Used for BOTH engine and null
        - arm_id is NOT part of the seed
        - stage_id = "downstream" (arm-independent)
        - This ensures: seed(engine, case) == seed(null, case)

    For Channel B (novelty search):
        seed = SHA256(preregistration_id || case_id || candidate_rank || "channel_b")
        - candidate_rank ∈ {1, 2, 3} (arm-independent)
        - candidate_id is NOT used (it is arm-specific)
        - This ensures: seed(engine, case, rank) == seed(null, case, rank)

    For shared stages (extraction, abstraction):
        seed = SHA256(preregistration_id || case_id || "extraction")
        seed = SHA256(preregistration_id || case_id || "abstraction")
        - Same for both arms (shared prefix by design)

    MECHANICAL ASSERTION (before execution):
        For every case i and rank r:
            seed(engine, i, r) == seed(null, i, r)
        This is verified by a test that computes both seeds and asserts equality.
        If the assertion fails, the experiment is BLOCKED.
```

### What this invariant establishes

The paired counterfactual is clean: any difference in output between engine and null for the same case is attributable to the **pipeline difference** (Transfer+Gen vs Concatenation), NOT to a seed difference. This is the strictest paired comparison.

---

## Invariant 2: Empty-Abstraction Fail-Closed (Edge Case)

### The edge case in R5.2's padding rule

R5.2's null candidate generation says:
```
If A has < 3 abstractions: use A1 for all 3 candidates, paired with B1, B2, B3
```

But this assumes A1 exists. What happens when:
```
A = []  (no abstractions extracted)
B = [B1, B2, B3]
```
or:
```
A = []
B = []
```

R5.2 does not explicitly define this case. The implementation must not fabricate behavior after seeing data.

### Implementation invariant (fail-closed)

```
EMPTY-ABSTRACTION FAIL-CLOSED INVARIANT:

    IF abstraction_list_a is empty OR abstraction_list_b is empty:
        ↓
    NULL_GENERATION_FAILURE
        ↓
    The case CANNOT silently receive a fabricated candidate.
        ↓
    The case is recorded as:
        case_status = NULL_GENERATION_FAILURE
        n_candidates = 0
        case_success = 0 (for the null arm)
        failure_reason = "NO_REQUIRED_ABSTRACTION"
        ↓
    The case is reported in the study results as a null-arm generation failure.
        ↓
    The engine arm is NOT affected (it uses its own extraction/abstraction,
    which may succeed even if the null's shared prefix failed — but since
    the prefix is SHARED, if extraction fails for the null, it also fails
    for the engine, and the case is:
        case_status = EXTRACTION_FAILURE
        n_candidates = 0 (both arms)
        case_success = 0 (both arms)
        failure_reason = "EXTRACTION_PRODUCED_NO_ABSTRACTIONS"
        ↓
    The case is included in N_clean (it was eligible) but contributes
    0 to both engine_yield and null_yield. This is a fair outcome —
    both arms failed equally.

    NO FABRICATION:
        - The implementation must NOT generate placeholder candidates
        - The implementation must NOT retry with different parameters
        - The implementation must NOT substitute alternative source material
        - The failure is recorded and the case moves on
```

### What this invariant establishes

No researcher can "rescue" a case by fabricating candidates when extraction fails. The experiment fails closed — if the pipeline cannot produce abstractions, the case contributes 0 to both arms equally. This is the only fair outcome.

---

## Implementation Acceptance

These two invariants are added to the acceptance gate as implementation-level requirements:

| # | Requirement | State |
|---|---|---|
| 29 | Universal seed (seed(engine,case,rank) == seed(null,case,rank)) | SPECIFIED (this document) |
| 30 | Empty-abstraction fail-closed (NULL_GENERATION_FAILURE, no fabrication) | SPECIFIED (this document) |

Both must reach IMPLEMENTED → ADVERSARIAL_TESTED → FREEZE_VERIFIED before freeze.

---

## What This Document Is NOT

- NOT a design revision (no R5.3)
- NOT a reopening of the experimental design
- NOT a conceptual change
- NOT a modification to the statistical engine

This document resolves two implementation-level contradictions in R5.2's specification. R5.2's substantive experimental architecture is accepted. The next phase is implementation.
