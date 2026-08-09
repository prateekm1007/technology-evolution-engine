# B2 Revision R5.2 — Null Candidate Budget, Estimand, and Seed Symmetry

**Status:** DESIGN REVISION (tiny) — not implementation, not authorized for execution
**Date:** 2026-08-09
**Supersedes:** B2_REVISION_R5_1.md (R5.1)
**Audit reference:** R5.1 adversarial review (round 44) — 3 SERIOUS, 2 IMPORTANT
**Statistical engine:** FROZEN at commit `39f5d37` — unchanged

---

## Purpose

R5.2 is a **tiny surgical revision**. It fixes exactly 5 items from the R5.1 adversarial review. It does NOT redesign the protocol. It does NOT reopen anything R5.1 got right. After R5.2, the next phase is **implementation**, not another conceptual revision.

---

## SERIOUS 1 Fix: Exactly 3 Null Candidates with Deterministic Rank Generation

### The problem

R5.1 said the null produces "up to 3 candidates per case" but its actual procedure only defined how to generate Candidate 1 (top-ranked abstraction from A + top-ranked abstraction from B + concatenation). Candidates 2 and 3 were undefined. This gives the engine 3 opportunities and the null 1 opportunity per case — a residual multiplicity advantage.

### R5.2 resolution

The null must generate **exactly 3 candidates** using a deterministic rank-based rule:

```
NULL CANDIDATE GENERATION (exactly 3, deterministic):

    Input (shared with engine):
        - abstracted_mechanisms_a: ranked list [A1, A2, A3, ...] by extraction confidence
        - abstracted_mechanisms_b: ranked list [B1, B2, B3, ...] by extraction confidence

    Candidate generation (rank-paired):
        Candidate 1: pair (A1, B1) — top-ranked from each
        Candidate 2: pair (A2, B2) — second-ranked from each
        Candidate 3: pair (A3, B3) — third-ranked from each

    If an arm produces fewer than 3 abstractions:
        - If A has < 3 abstractions: use A1 for all 3 candidates, paired with B1, B2, B3
        - If B has < 3 abstractions: use B1 for all 3 candidates, paired with A1, A2, A3
        - If both have < 3: use the available abstractions, cycling if needed
        - The padding rule is deterministic and preregistered

    Candidate construction (same as R5.1, applied to each pair):
        relationship = "<A_i_abstraction> is related to <B_i_abstraction>"
        mechanism = "Both involve <shared_entity_or_concept>. " +
                    "<A_i_abstraction> occurs in domain A. " +
                    "<B_i_abstraction> occurs in domain B. " +
                    "They may be connected through <shared_entity_or_concept>."

    Output: exactly 3 candidates, no "up to", no human selection, no padding with empty candidates.
```

### Budget equivalence

```
K_ENGINE = 3 (first 3 eligible from engine raw output)
K_NULL   = 3 (rank-paired from abstraction lists)

Both arms produce exactly 3 candidates per case.
Both arms have exactly 3 opportunities to produce a passing candidate.
No multiplicity advantage.
```

---

## SERIOUS 2 Fix: Estimand Statement — Engine-Downstream-Pipeline, Not Transfer Attribution

### The problem

R5.1's language came dangerously close to calling the comparison a transfer/generation attribution. The engine branch contains BOTH CrossDomainTransferEngine AND HypothesisGenerationEngine. The null contains NEITHER. A positive result establishes that the **engine downstream pipeline** (transfer + generation) outperforms the null procedure — it does NOT establish that the transfer mechanism itself caused the improvement.

### R5.2 resolution: Explicit estimand statement

```
B2 ESTIMAND (primary causal claim):

    The frozen engine downstream pipeline
    (CrossDomainTransferEngine + HypothesisGenerationEngine)
    produces more qualifying discovery cases than
    the preregistered generation-null procedure,
    conditional on the shared upstream pipeline
    (extraction + abstraction).

    This is a SYSTEM-LEVEL DOWNSTREAM comparison.
    It is NOT a component-level attribution.

WHAT B2 DOES NOT ESTABLISH:

    - CrossDomainTransferEngine caused the improvement
    - HypothesisGenerationEngine caused the improvement
    - The transfer mechanism itself adds value
    - Any individual component is necessary or sufficient

    Component-level attribution requires Stage 2B+ ablation:
    - Replace CrossDomainTransferEngine with a trivial join → test degradation
    - Replace HypothesisGenerationEngine with a template fill → test degradation
    - These are SEPARATE preregistered experiments, not B2.
```

### Causal graph (explicit)

```
SOURCE PAIR
     │
     ▼
EXTRACTION (shared)
     │
     ▼
ABSTRACTION (shared)
     │
     ├──────────────────────┐
     ▼                      ▼
  ENGINE                  NULL
  Transfer + Gen          Concatenation
     │                      │
     ▼                      ▼
 CANDIDATES (3)          CANDIDATES (3)
     │                      │
     └──────────┬───────────┘
                ▼
        BLINDED GATES
                │
                ▼
        CASE_SUCCESS_i ∈ {0,1}

The experiment estimates:
    Effect(ENGINE_DOWNSTREAM_PIPELINE vs NULL_GENERATION_PROCEDURE)
    conditional on the shared upstream pipeline.

It does NOT estimate:
    Effect(CrossDomainTransferEngine)
    Effect(HypothesisGenerationEngine)
```

---

## SERIOUS 3 Fix: Fully Formalize `<shared_entity_or_concept>`

### The problem

R5.1's null procedure used `<shared_entity_or_concept>` without specifying where it comes from. This is a major hidden degree of freedom — if the null can choose a shared concept intelligently, it becomes a stronger baseline; if it uses crude lexical intersection, it becomes weaker. Either is defensible, but it must be fixed before seeing B2 results.

### R5.2 resolution: Deterministic entity intersection

```
SHARED_ENTITY_OR_CONCEPT (deterministic, frozen):

    Definition:
        shared_entity_or_concept =
            FirstEntity(
                SortedIntersection(
                    Entities(A_i_abstraction),
                    Entities(B_i_abstraction),
                    FrozenStopwordList,
                    FrozenEntityDictionary
                )
            )

    Where:
        Entities(abstraction):
            Deterministic extraction of named entities from the abstraction
            text using a FROZEN NER model (spaCy en_core_web_sm, version
            recorded, SHA-256 committed).

        SortedIntersection(entities_a, entities_b, stopword_list, entity_dict):
            1. Compute the set intersection of entities_a and entities_b
               (after canonicalization: lowercase, strip punctuation,
               singularize using a frozen lemmatizer).
            2. Remove any entity in the FrozenStopwordList.
            3. Remove any entity not in the FrozenEntityDictionary
               (a preregistered dictionary of valid scientific concepts,
               SHA-256 committed).
            4. Sort the remaining entities alphabetically (deterministic).
            5. Return the sorted list.

        FirstEntity(sorted_list):
            Return the first entity in the sorted list.
            If the list is empty, return NULL.

    When shared_entity_or_concept = NULL:
        mechanism = "Both domains involve related phenomena. " +
                    "<A_i_abstraction> occurs in domain A. " +
                    "<B_i_abstraction> occurs in domain B. " +
                    "No shared entity was identified."
        (This is a valid candidate — it can still pass Gate A if the
         abstractions themselves are non-trivial, and can pass/fail
         Gate C based on coherence.)

    FROZEN COMPONENTS:
        - NER model: spaCy en_core_web_sm (version recorded, SHA-256)
        - Stopword list: NLTK English (frozen at freeze time, SHA-256)
        - Entity dictionary: preregistered, SHA-256 committed
        - Lemmatizer: spaCy built-in (version recorded)
        - Canonicalization rule: lowercase → strip punctuation → singularize
        - Sorting rule: alphabetical (ascending)

    No LLM, no human judgment, no adaptive selection.
    The shared entity is deterministically computed from the abstractions.
```

### Tie-breaking

```
TIE-BREAKING RULE:
    If multiple entities have the same canonical form, they are deduplicated
    before sorting. If the sorted list is empty, shared_entity_or_concept = NULL.
    There is no tie-breaking by frequency, confidence, or any other criterion
    — alphabetical sorting is the sole tie-breaker.
```

---

## IMPORTANT 4 Fix: Fixed Three-Rater Calibration for Fleiss' κ

### The problem

R5.1's design uses 2 raters normally, with a 3rd rater on disagreement. This creates a variable number of ratings per item. Fleiss' κ assumes a fixed number of ratings per subject. Computing Fleiss' κ on a variable-rater structure is statistically ambiguous.

### R5.2 resolution: Fixed three-rater calibration

```
CALIBRATION DESIGN (fixed three raters):

    Every calibration item is rated by exactly 3 independent raters:
        R1, R2, R3 (all see every calibration item)

    No disagreement-triggered 3rd rater during calibration.
    All three raters rate all items unconditionally.

    Fleiss' κ is computed on the complete 3-rater × N-item matrix.
    This gives a fixed, unambiguous reliability statistic.

    κ ≥ 0.40 → calibration passes
    κ < 0.40 → PROTOCOL_NOT_READY (per R5.1's failure protocol)

STUDY ADJUDICATION (can still use 2+1 design):

    For study cases (not calibration), the design MAY use:
        R1 + R2 → agreement = final
        R1 + R2 → disagreement = R3 recruited, majority rules

    This is acceptable for study adjudication because the reliability
    of the rubric was already established on the fixed-3-rater
    calibration set.

    But the CALIBRATION statistic (Fleiss' κ) uses the fixed-3 design.
```

---

## IMPORTANT 5 Fix: Freeze Identical Seed Construction Across Arms

### The problem

R5.1 used different seed rules for different arms: `seed = case_index` for the null, `seed = candidate_id hash` for Channel B. If both arms use the same provider/model, different seed rules can become a hidden experimental difference. Even at temperature 0, some providers use the seed internally.

### R5.2 resolution: Universal invocation seed

```
UNIVERSAL INVOCATION SEED (same construction for all arms):

    invocation_seed =
        SHA256(
            preregistration_id
            || case_id
            || stage_id
        )

    Where:
        preregistration_id: the frozen protocol SHA (same for all arms)
        case_id: the case identifier (e.g., "CASE-001")
        stage_id: the pipeline stage (e.g., "extraction", "abstraction",
                  "transfer", "generation", "null_generation",
                  "channel_b_formulation")

    NOTE: arm_id is NOT included in the seed.
    This means:
        - Engine and null receive the SAME seed for the same case+stage.
        - The seed is deterministic from (preregistration, case, stage).
        - No arm has a seed advantage.

    For stages that are shared (extraction, abstraction):
        Both arms use the same seed → same extracted/abstracted mechanisms.
        (This is already guaranteed by the shared-prefix design, but the
         seed rule makes it explicit.)

    For stages that differ (engine: transfer+generation; null: concatenation):
        Both arms use seed = SHA256(preregistration_id || case_id || "downstream")
        The provider receives the same seed for the same case, regardless of arm.

    For Channel B (novelty search):
        seed = SHA256(preregistration_id || case_id || candidate_id || "channel_b")
        This is the same across arms because candidate_id is arm-specific but
        the seed construction rule is identical.

RATIONALE:
    Same seed across arms for the same case+stage ensures that any difference
    in output is attributable to the pipeline difference (engine vs null),
    not to a seed difference. This is the strictest paired counterfactual.
```

---

## Summary of R5.2 Changes

| # | Fix | What changed |
|---|---|---|
| 1 | Exactly 3 null candidates | Rank-paired generation: (A1,B1), (A2,B2), (A3,B3). No "up to 3." Deterministic padding rule. |
| 2 | Estimand statement | Explicit: "engine downstream pipeline vs generation-null, conditional on shared upstream." NOT transfer attribution. |
| 3 | Formalize shared_entity_or_concept | Deterministic: NER intersection → stopword filter → dictionary filter → alphabetical sort → first entity. NULL if empty. |
| 4 | Fixed 3-rater calibration | All 3 raters rate all calibration items. Fleiss' κ on fixed matrix. Study adjudication can still use 2+1. |
| 5 | Universal seed | SHA256(preregistration_id \|\| case_id \|\| stage_id). arm_id NOT included. Same seed for same case+stage across arms. |

---

## What R5.2 Does NOT Change

- **Statistical engine:** UNCHANGED (frozen at `39f5d37`)
- **Candidate capture:** R5/R5.1 correct
- **Parser-derived provenance invariant:** R5.1 correct
- **Content-addressed storage:** R5.1 correct
- **Calibration failure protocol:** R5.1 correct (PROTOCOL_NOT_READY → new amendment)
- **Channel B freezing:** R5.1 correct (now uses universal seed)
- **Novelty terminology:** R5 correct (NO_PRECEDENT_FOUND)
- **Human arm:** R5 correct (descriptive only)
- **No anti-outlier rule:** R5 correct (sensitivity analysis, reported not decision-altering)
- **System/provider attribution boundary:** R5 correct (system-level claim only)

---

## Updated Acceptance Gate

| # | Requirement | R5.1 state | R5.2 state |
|---|---|---|---|
| 1 | Candidate capture (immutable) | SPECIFIED | SPECIFIED |
| 2 | Candidate selection (mechanical) | SPECIFIED | SPECIFIED |
| 3 | Maximum candidates (K = 3, both arms) | SPECIFIED (K≤3) | SPECIFIED (K=3 exact, rank-paired) |
| 4 | Raw output hash-committed | SPECIFIED | SPECIFIED |
| 5 | Candidate rewriting forbidden | SPECIFIED | SPECIFIED |
| 6 | Pipeline attribution (system-level downstream) | SPECIFIED | SPECIFIED (estimand explicit) |
| 7 | Provider attribution (separated) | SPECIFIED | SPECIFIED |
| 8 | Gate-A examples (frozen) | SPECIFIED | SPECIFIED |
| 9 | Gate-A calibration (Fleiss' κ, fixed 3 raters) | SPECIFIED | SPECIFIED (fixed 3-rater calibration) |
| 10 | Gate-C adjudication (blinded) | SPECIFIED | SPECIFIED |
| 11 | Primary endpoint (case-level binary) | SPECIFIED | SPECIFIED |
| 12 | Candidate multiplicity (secondary) | SPECIFIED | SPECIFIED |
| 13 | Novelty wording (NO_PRECEDENT_FOUND) | SPECIFIED | SPECIFIED |
| 14 | Novelty search (two-channel, fully frozen) | SPECIFIED | SPECIFIED |
| 15 | Search protocol (frozen) | SPECIFIED | SPECIFIED |
| 16 | Generation null (fair baseline, 3 candidates) | SPECIFIED | SPECIFIED (3 candidates, deterministic) |
| 17 | Null shared_entity_or_concept (formalized) | NOT SPECIFIED | SPECIFIED (deterministic intersection) |
| 18 | Retrieval baseline (descriptive) | SPECIFIED | SPECIFIED |
| 19 | Human arm (descriptive) | SPECIFIED | SPECIFIED |
| 20 | Outliers (no exclusions) | SPECIFIED | SPECIFIED |
| 21 | Sensitivity analysis (predeclared) | SPECIFIED | SPECIFIED |
| 22 | Provenance (parser-derived invariant) | SPECIFIED | SPECIFIED |
| 23 | Raw-output storage (content-addressed) | SPECIFIED | SPECIFIED |
| 24 | Domain concentration (reported) | SPECIFIED | SPECIFIED |
| 25 | Provider dependence (limited claim) | SPECIFIED | SPECIFIED |
| 26 | Calibration failure (PROTOCOL_NOT_READY) | SPECIFIED | SPECIFIED |
| 27 | Universal seed (same across arms) | NOT SPECIFIED | SPECIFIED |
| 28 | Estimand statement (downstream pipeline, not transfer) | NOT SPECIFIED | SPECIFIED |

**All 28 requirements are SPECIFIED.** None are IMPLEMENTED, ADVERSARIAL_TESTED, or FREEZE_VERIFIED.

---

## Status

```
Statistical engine:               FROZEN (commit 39f5d37)
B2 protocol design (R5.2):        SPECIFIED — all 28 requirements specified
B2 freeze:                        BLOCKED (pending adversarial review of R5.2)
B1/B2 execution:                  BLOCKED
Phase 8 execution:                BLOCKED
North Star:                       NOT ACHIEVED

Acceptance states:
    SPECIFIED:           28/28 requirements
    IMPLEMENTED:         0/28 requirements
    ADVERSARIAL_TESTED:  0/28 requirements
    FREEZE_VERIFIED:     0/28 requirements

Next phase: IMPLEMENTATION
    - Build provenance ledger
    - Build mechanical parser (with SHA-256 committed source/config)
    - Build content-addressed raw-output storage
    - Build generation null (rank-paired, deterministic shared entity)
    - Build derivation verification test
    - Build Channel B formulation generator (frozen prompt, universal seed)
    - Build Fleiss' κ calibration tool (fixed 3-rater)
    - Adversarial tests for each invariant
    - Baseline equivalence audit
    - Freeze verification
    - Execution authorization (separate)
```

---

## The Stopping Line (Unchanged)

R5.2 does not manufacture a stronger scientific claim. Even if B2 produces a statistically significant positive result with verified provenance:

```
DISCOVERY_PIPELINE_SIGNAL_DETECTED
```

NOT:

```
THE ENGINE HAS ACHIEVED THE NORTH STAR
```

The North Star requires Stage 2B replication + component attribution + stronger novelty investigation. R5.2 closes the remaining specification defects. The next phase is implementation.

---

## What R5.2 Does NOT Authorize

- Implementing any protocol
- Executing any protocol
- Modifying the frozen statistical engine
- Making any discovery or capability claim
- Skipping the adversarial review of R5.2
- Another conceptual redesign (R5.2 is the last design revision before implementation)
