# B2 Revision R5.1 — Null Architecture & Provenance Invariants

**Status:** DESIGN REVISION — not implementation, not authorized for execution
**Date:** 2026-08-09
**Supersedes:** B2_REVISION_R5.md (R5)
**Audit reference:** R5 adversarial review (round 43) — 2 FATAL, 2 SERIOUS defects
**Statistical engine:** FROZEN at commit `39f5d37` — unchanged by this revision

---

## Purpose

R5 established the causal-chain architecture and provenance ledger concept. R5.1 fixes the 4 blocking defects identified in the R5 adversarial review:

1. **FATAL:** The retrieval null is structurally incapable of succeeding (cannot produce a mechanism, so `P(null CASE_SUCCESS) = 0` by construction, making `engine > null` nearly tautological)
2. **FATAL:** The provenance hash chain does not prove candidate derivation (`candidate_sha256 ≠ raw_output_sha256` — they are different objects)
3. **SERIOUS:** Calibration reverted to Cohen's κ (should be Fleiss' κ for multiple raters); calibration failure allows silent rubric revision (researcher degree of freedom)
4. **SERIOUS:** Novelty Channel B is not actually frozen (an LLM-generated paraphrase procedure is not deterministic just because a synonym dictionary is frozen)

R5.1 also addresses:
- Raw-output immutability (content-addressed storage, not just hash-recorded)
- Acceptance state granularity (SPECIFIED → IMPLEMENTED → ADVERSARIAL_TESTED → FREEZE_VERIFIED)

R5.1 is **narrowly surgical**. It does NOT reopen the parts R5 got right (candidate capture, provider attribution, case-level endpoint, human arm, novelty terminology). It does NOT touch the statistical engine.

---

## FATAL 1 Fix: Genuine Generation Null

### The problem (R5 adversarial review)

R5 defined the retrieval null with:
```
mechanism = "NO_MECHANISM_PROPOSED"
```

This means `P(null CASE_SUCCESS) = 0` by construction (Gate C requires a mechanism to validate). The engine-vs-null comparison becomes nearly tautological: the engine CAN generate mechanisms, the null CANNOT, so `engine > null` is almost guaranteed.

This is not a valid discovery baseline. The experiment cannot answer "does the discovery pipeline add value over a credible alternative?" if the alternative is deliberately incapable of producing the thing being measured.

### R5.1 resolution: Generation null

R5.1 replaces the retrieval null with a **generation null** — a preregistered alternative-generation process that:
- Receives the same source pair
- Has the same candidate budget (3 candidates)
- Produces candidates in the same schema (including a mechanism)
- Does NOT use the engine's mechanism-transfer machinery (CrossDomainTransferEngine + HypothesisGenerationEngine)

```
ENGINE ARM:
    source A + source B
        ↓
    MechanismExtractionEngine → MechanismAbstractionEngine
        ↓
    CrossDomainTransferEngine.generate()    ← TESTED COMPONENT
        ↓
    HypothesisGenerationEngine.generate()   ← TESTED COMPONENT
        ↓
    candidate (relationship + mechanism)

GENERATION NULL ARM:
    source A + source B
        ↓
    MechanismExtractionEngine → MechanismAbstractionEngine
        (SAME extraction/abstraction as engine — shared prefix)
        ↓
    NullGenerationProcedure()               ← FROZEN ALTERNATIVE
        (does NOT use CrossDomainTransferEngine or HypothesisGenerationEngine)
        ↓
    candidate (relationship + mechanism)
```

### Null generation procedure (frozen, preregistered)

The null generation procedure must:
1. Receive the SAME extracted mechanisms and abstractions as the engine
2. Produce a candidate WITHOUT using the tested transfer/generation machinery
3. Be mechanically reproducible (frozen prompt, model, temperature, seed)

```
NULL GENERATION PROCEDURE (frozen):

    Input:
        - extracted_mechanisms_a (from MechanismExtractionEngine on Source A)
        - extracted_mechanisms_b (from MechanismExtractionEngine on Source B)
        - abstracted_mechanisms_a (from MechanismAbstractionEngine on A)
        - abstracted_mechanisms_b (from MechanismAbstractionEngine on B)

    Procedure:
        1. Select the top-ranked abstraction from A (by extraction confidence)
        2. Select the top-ranked abstraction from B (by extraction confidence)
        3. Construct a candidate by CONCATENATION:
             relationship = "<A_abstraction> is related to <B_abstraction>"
             mechanism = "Both involve <shared_entity_or_concept>. " +
                         "<A_abstraction> occurs in domain A. " +
                         "<B_abstraction> occurs in domain B. " +
                         "They may be connected through <shared_entity_or_concept>."
        4. This is a COMPOSITIONAL null — it joins abstractions without
           transfer or hypothesis generation.

    Provider:
        - Same provider as engine (ZAI/GLM glm-4-plus)
        - Same temperature (0.0)
        - Same seed (case_index)
        - Frozen prompt (SHA-256 committed)

    Output:
        - Up to 3 candidates per case (same budget as engine)
        - Same candidate schema as engine
        - Candidates CAN pass Gate A (if the composition is non-trivial)
        - Candidates CAN pass Gate C (if the mechanism is coherent)
        - Candidates CAN pass Gate B (if no precedent is found)
```

### Why this is a fair baseline

```
ENGINE:     extraction → abstraction → TRANSFER → GENERATION → candidate
NULL:       extraction → abstraction → CONCATENATION → candidate

Both arms:
    - Receive the same source material
    - Share the same extraction/abstraction prefix
    - Have the same candidate budget (3)
    - Produce candidates in the same schema
    - Are adjudicated by the same blinded pipeline
    - Undergo the same novelty search

They differ ONLY in the generation mechanism:
    - Engine uses CrossDomainTransferEngine + HypothesisGenerationEngine
    - Null uses frozen concatenation (no transfer, no generation)

If engine yield > null yield, the difference is attributable to the
transfer/generation machinery (at the system level — provider
dependence is still acknowledged).
```

### Retrieval arm — demoted to descriptive

The retrieval arm (entity intersection) remains in the protocol but is explicitly classified:

```
RETRIEVAL ARM:
    DESCRIPTIVE_REFERENCE_ONLY

    - Produces entity pairs, not mechanisms
    - Cannot pass Gate C (no mechanism)
    - Structurally disadvantaged by design
    - Reported descriptively, NOT used for primary inferential comparison
    - No statistical test involving the retrieval arm
```

The primary comparison is **engine vs. generation null** (both can produce mechanisms).

---

## FATAL 2 Fix: Parser-Derived Provenance Invariant

### The problem (R5 adversarial review)

R5 said `candidate_sha256` must match `raw_output_sha256`. But these are different objects — the hash of the raw LLM output cannot equal the hash of the parsed candidate text unless the candidate IS the entire raw output byte-for-byte.

An auditor can verify "this candidate hash exists" but cannot mechanically verify "this candidate was deterministically derived from this exact raw output."

### R5.1 resolution: Parser-derived derivation record

```
DERIVATION RECORD (per candidate):

    raw_output_sha256:       <SHA-256 of the engine's raw output>
    raw_output_blob_path:    <content-addressed storage path>
    parser_sha256:           <SHA-256 of the frozen parser source code>
    parser_config_sha256:    <SHA-256 of the parser configuration>
    candidate_rank:          <1, 2, or 3>
    candidate_sha256:        <SHA-256 of the parsed candidate text>

DERIVATION INVARIANT:

    SHA256(
        FrozenParser(
            raw_output,
            parser_version,
            parser_config
        ).candidate(rank)
    )
    ==
    candidate_sha256

    This is mechanically verifiable: an auditor can retrieve the raw
    output blob, retrieve the parser source, retrieve the parser config,
    run the parser, extract the candidate at the given rank, and verify
    the hash matches.
```

### Parser freeze

```
PARSER FREEZE:
    - The parser source code is committed to git (SHA-256 recorded)
    - The parser configuration is committed to git (SHA-256 recorded)
    - The parser is deterministic (no RNG, no LLM, no network calls)
    - The parser version is recorded in every provenance entry
    - Parser changes require a new preregistration amendment
```

### Verification test

```
DERIVATION VERIFICATION TEST (automated):

    For every candidate in the provenance ledger:
    1. Retrieve raw_output_blob by path
    2. Verify raw_output_sha256 matches blob content
    3. Retrieve parser source by parser_sha256
    4. Retrieve parser config by parser_config_sha256
    5. Run: candidate = parser(raw_output, config).candidate(rank)
    6. Verify SHA256(candidate) == candidate_sha256
    7. If mismatch → PROVENANCE_VIOLATION (fatal)

    This test is run before the primary statistical analysis.
    If any candidate fails derivation verification, the experiment
    is INCONCLUSIVE_PROVENANCE_VIOLATION.
```

---

## SERIOUS 3 Fix: Fleiss' κ + Calibration Failure Protocol

### The problem (R5 adversarial review)

R5 reverted to Cohen's κ, which is a two-rater statistic. If R5 uses multiple raters (min 2, +3rd on disagreement), Fleiss' κ is required. Also, R5 allowed silent rubric revision on calibration failure, which is a researcher degree of freedom.

### R5.1 resolution: Fleiss' κ

```
INTER-RATER RELIABILITY:
    Statistic: Fleiss' κ (not Cohen's κ)
    Reason: The design uses multiple raters (min 2, +3rd on disagreement).
            Cohen's κ is a two-rater statistic. Fleiss' κ handles
            multiple raters.

    Calculation:
    - Fleiss' κ calculated on calibration cases
    - If κ < 0.40: CALIBRATION_FAILURE (see below)
    - If κ ≥ 0.40: adjudication procedure is ready
    - κ is reported in the study results

    Pairwise Cohen's κ may be reported as supplementary information,
    but Fleiss' κ is the primary calibration statistic.
```

### Calibration failure protocol (no silent revision)

```
CALIBRATION FAILURE PROTOCOL:

    IF Fleiss' κ < 0.40 on calibration cases:
        ↓
    PROTOCOL_NOT_READY
        ↓
    The experiment CANNOT proceed with the current rubric.
        ↓
    Required sequence:
        1. New preregistration amendment (documenting what changed)
        2. New SHA-256 for the amended protocol
        3. New calibration set (or revised calibration set with new SHA)
        4. Fresh adjudicator calibration (new calibration session)
        5. New Fleiss' κ calculation
        6. Only if κ ≥ 0.40: freeze consideration resumes
        ↓
    NO SILENT REVISION:
        - The rubric cannot be edited and then executed without
          a new preregistration amendment and SHA.
        - The calibration set cannot be selected because it makes
          adjudicators agree.
        - All calibration attempts are recorded (including failures).
```

---

## SERIOUS 4 Fix: Fully Frozen Channel B

### The problem (R5 adversarial review)

R5 said Channel B uses "an independent evaluator generating three alternative formulations." A frozen synonym dictionary does NOT make an LLM-generated paraphrase procedure deterministic. The evaluator can choose formulations that are broad, narrow, favorable, or unfavorable.

### R5.1 resolution: Fully frozen Channel B

```
CHANNEL B — MECHANISM-NORMALIZED SEARCH (fully frozen):

    GENERATION PROCEDURE:
        - Evaluator/Model: ZAI/GLM glm-4-plus (same as engine, but
          independently invoked — no shared session)
        - Model version: frozen, recorded
        - Prompt: frozen (SHA-256 committed), specifying:
            * "Generate exactly 3 alternative formulations of the
               following mechanism. Each formulation should use
               different vocabulary that a prior author might have
               used to describe the same mechanism."
            * Input: the candidate's mechanism text (NOT the source
              texts, NOT the arm identity)
            * Output format: exactly 3 numbered formulations
        - Temperature: 0.0 (deterministic)
        - Seed: frozen (derived from candidate_id hash)
        - Max output: frozen (e.g., 500 tokens)
        - Number of formulations: exactly 3 (no more, no less)

    FORMULATION PARSING:
        - Frozen parser (SHA-256 committed) extracts the 3 formulations
        - Rejection rules (frozen):
            * If fewer than 3 formulations are parsed → RETRY (up to 2 retries)
            * If a formulation is identical to the candidate text → RETRY
            * If a formulation is empty or malformed → RETRY
            * After 2 failed retries → CHANNEL_B_FAILURE (recorded,
              candidate classified as AMBIGUOUS for novelty)
        - No evaluator may manually edit formulations
        - No evaluator may retry beyond the frozen limit
        - No evaluator may select which formulations to use

    SEARCH:
        - Each of the 3 formulations is searched using Channel A protocol
          (same 4 databases, same top-20/top-5 rule)
        - If ANY formulation retrieves prior art describing the same
          mechanism → PRIOR_ART_FOUND
        - Only if ALL 3 formulations fail to retrieve matching prior
          art → NO_PRECEDENT_FOUND_UNDER_PREREGISTERED_SEARCH

    BLINDING:
        - The Channel B evaluator does NOT know:
            * which arm generated the candidate
            * whether the candidate is from a true or null case
            * the source texts
            * the Gate A or Gate C classification
        - The evaluator sees ONLY the mechanism text.

    REPRODUCIBILITY:
        - The entire Channel B procedure is mechanically reproducible:
            same model + same prompt + same temperature + same seed
            → same 3 formulations → same search results
        - The procedure is NOT dependent on human judgment (except
          for the final "does this prior art describe the same
          mechanism?" determination, which is performed by a blinded
          adjudicator using the Gate C rubric).
```

---

## Fix: Raw-Output Immutability — Content-Addressed Storage

### The problem (R5 adversarial review)

R5 said raw output SHA-256 is "computed and recorded" and raw output is "retained indefinitely." But a hash is not the artifact. An operator could replace the raw output while preserving the hash in the ledger if the verification process doesn't have an independent copy.

### R5.1 resolution: Content-addressed storage

```
RAW-OUTPUT IMmutABILITY:

    1. The raw output is written to content-addressed storage:
         path = provenance/raw_outputs/{raw_output_sha256}.txt
       The filename IS the SHA-256. If the content changes, the path
       changes. The path is recorded in the provenance ledger.

    2. The raw output blob is committed to git BEFORE adjudication:
         git add provenance/raw_outputs/{raw_output_sha256}.txt
         git commit -m "PROVENANCE: raw output for {case_id} {arm}"
       The git commit SHA is recorded in the ledger.

    3. After adjudication, the finalized ledger is committed to git:
         git add provenance/ledger.json
         git commit -m "PROVENANCE: ledger finalized after adjudication"

    4. Verification:
       - The auditor retrieves the blob from git at the recorded commit
       - The auditor computes SHA-256 of the blob
       - The auditor verifies it matches raw_output_sha256 in the ledger
       - The auditor verifies the blob path matches the hash
       - Any discrepancy → PROVENANCE_VIOLATION (fatal)

    This applies the same principle that hardened the Phase 7 freeze:
       disk content != git HEAD content → manifest substitution detected.
    Here:
       ledger hash != blob content → raw output tampering detected.
```

---

## Fix: Acceptance State Granularity

### The problem (R5 adversarial review)

R5's acceptance table said all 22 requirements are "SPECIFIED." But "specified" can be mistaken for "established." The auditor needs to distinguish between specification, implementation, adversarial testing, and freeze verification.

### R5.1 resolution: Four-level acceptance states

```
ACCEPTANCE STATE LEVELS:

    SPECIFIED:
        The requirement is documented in the design.
        The design explains what must be true.

    IMPLEMENTED:
        The requirement is implemented in code or procedure.
        The implementation exists and is committed.

    ADVERSARIAL_TESTED:
        The implementation has been tested by an adversarial process.
        Tests exist that attempt to break the invariant.

    FREEZE_VERIFIED:
        The requirement is verified at freeze time.
        The freeze-time verification is recorded and SHA-256 committed.
```

### Updated acceptance gate

| # | Requirement | R5 state | R5.1 state |
|---|---|---|---|
| 1 | Candidate capture (immutable) | SPECIFIED | SPECIFIED |
| 2 | Candidate selection (mechanical) | SPECIFIED | SPECIFIED |
| 3 | Maximum candidates (K ≤ 3) | SPECIFIED | SPECIFIED |
| 4 | Raw output hash-committed | SPECIFIED | SPECIFIED |
| 5 | Candidate rewriting forbidden | SPECIFIED | SPECIFIED |
| 6 | Pipeline attribution (system-level) | SPECIFIED | SPECIFIED |
| 7 | Provider attribution (separated) | SPECIFIED | SPECIFIED |
| 8 | Gate-A examples (frozen) | SPECIFIED | SPECIFIED |
| 9 | Gate-A calibration (Fleiss' κ) | SPECIFIED (Cohen's κ) | SPECIFIED (Fleiss' κ) |
| 10 | Gate-C adjudication (blinded) | SPECIFIED | SPECIFIED |
| 11 | Primary endpoint (case-level binary) | SPECIFIED | SPECIFIED |
| 12 | Candidate multiplicity (secondary) | SPECIFIED | SPECIFIED |
| 13 | Novelty wording (NO_PRECEDENT_FOUND) | SPECIFIED | SPECIFIED |
| 14 | Novelty search (two-channel) | SPECIFIED | SPECIFIED (Channel B fully frozen) |
| 15 | Search protocol (frozen) | SPECIFIED | SPECIFIED |
| 16 | Generation null (fair baseline) | NOT SPECIFIED | SPECIFIED |
| 17 | Retrieval baseline (descriptive) | SPECIFIED | SPECIFIED (demoted) |
| 18 | Human arm (descriptive) | SPECIFIED | SPECIFIED |
| 19 | Outliers (no exclusions) | SPECIFIED | SPECIFIED |
| 20 | Sensitivity analysis (predeclared) | SPECIFIED | SPECIFIED |
| 21 | Provenance (parser-derived invariant) | SPECIFIED (wrong invariant) | SPECIFIED (correct invariant) |
| 22 | Raw-output storage (content-addressed) | SPECIFIED (hash only) | SPECIFIED (content-addressed) |
| 23 | Domain concentration (reported) | SPECIFIED | SPECIFIED |
| 24 | Provider dependence (limited claim) | SPECIFIED | SPECIFIED |
| 25 | Calibration failure (PROTOCOL_NOT_READY) | NOT SPECIFIED | SPECIFIED |

**All 25 requirements are SPECIFIED.** None are IMPLEMENTED, ADVERSARIAL_TESTED, or FREEZE_VERIFIED yet.

Freeze-readiness requires:
- All requirements reach SPECIFIED ✓ (this document)
- Requirements 1-5, 16, 21-22 reach IMPLEMENTED (provenance ledger, parser, content-addressed storage, generation null implementation)
- Requirements 1-5, 21-22 reach ADVERSARIAL_TESTED (tests that attempt to break invariants)
- All requirements reach FREEZE_VERIFIED (freeze-time verification recorded)

---

## Updated Decision Partition

```
IF baseline_equivalence_audit == FAILED:
    INCONCLUSIVE_UNFAIR_BASELINE

ELSE IF N_clean < 15:
    INSUFFICIENT_CLEAN_CASES

ELSE IF null_validity == FAILED:
    INCONCLUSIVE_INVALID_NULL

ELSE IF provenance_derivation_verification == FAILED:
    INCONCLUSIVE_PROVENANCE_VIOLATION

ELSE IF calibration_Fleiss_kappa < 0.40:
    INCONCLUSIVE_CALIBRATION_FAILURE

ELSE IF engine_yield == 0:
    DISCOVERY_SIGNAL_NOT_DETECTED

ELSE IF engine_yield > 0 AND engine_yield > generation_null_yield
        (exact McNemar, α=0.05, CI_lower > 0.20):
    DISCOVERY_PIPELINE_SIGNAL_DETECTED (pilot — requires Stage 2B replication)

ELSE:
    DISCOVERY_SIGNAL_NOT_DETECTED
```

### Key change

The primary comparison is now **engine vs. generation null** (not engine vs. retrieval null). Both arms can produce mechanisms. The comparison is scientifically fair.

### New failure states

- **INCONCLUSIVE_PROVENANCE_VIOLATION:** Parser-derived derivation verification failed. Result cannot be trusted.
- **INCONCLUSIVE_CALIBRATION_FAILURE:** Fleiss' κ < 0.40. Adjudication procedure not ready. Requires new preregistration amendment.

---

## What R5.1 Does NOT Change

- **Statistical engine:** UNCHANGED (frozen at `39f5d37`)
- **Candidate capture:** R5's design is correct (first-3-eligible, immutable)
- **System/provider attribution:** R5's boundary is correct
- **Case-level endpoint:** R5's CASE_SUCCESS_i is correct
- **Human arm:** R5's descriptive-only classification is correct
- **Novelty terminology:** R5's NO_PRECEDENT_FOUND is correct
- **No anti-outlier rule:** R5's sensitivity-analysis approach is correct

R5.1 is narrowly surgical. It fixes the 4 blocking defects and the 2 implementation gaps. It does not reopen the parts R5 got right.

---

## What R5.1 Does NOT Authorize

- Implementing any protocol
- Executing any protocol
- Modifying the frozen statistical engine
- Making any discovery or capability claim
- Skipping the adversarial review of R5.1
- Skipping the baseline equivalence audit
- Freezing B2

---

## Status

```
Statistical engine:               FROZEN (commit 39f5d37)
B2 protocol design (R5.1):        SPECIFIED — requires adversarial review
B2 freeze:                        BLOCKED (pending R5.1 review)
B1/B2 execution:                  BLOCKED
Phase 8 execution:                BLOCKED
North Star:                       NOT ACHIEVED

Acceptance states:
    SPECIFIED:           25/25 requirements
    IMPLEMENTED:         0/25 requirements
    ADVERSARIAL_TESTED:  0/25 requirements
    FREEZE_VERIFIED:     0/25 requirements

Next steps:
  1. Adversarial review of R5.1
  2. If review passes: implement provenance ledger, parser, content-addressed storage, generation null
  3. Adversarial testing of implemented invariants
  4. Baseline equivalence audit (before execution)
  5. Freeze consideration (after all requirements reach FREEZE_VERIFIED)
  6. Execution authorization (separate, after freeze)
```

---

## The Accurate Statement

R5 said: "the causal chain is now established."

R5.1 corrects this to:

> **R5.1 specifies a candidate causal chain with a fair generation null and a parser-derived provenance invariant. The design is now internally consistent. Implementation, adversarial testing, and freeze verification remain.**

The null architecture is no longer tautological. The provenance invariant is now mechanically verifiable. But the design is not yet the experiment.
