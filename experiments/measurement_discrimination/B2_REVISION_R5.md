# B2 Revision R5 — Causal Attribution & Experimental Integrity

**Status:** DESIGN REVISION — not implementation, not authorized for execution
**Date:** 2026-08-09
**Supersedes:** B1_B2_DESIGN_REVISION_R4_1.md (for B2 only; B1 statistical elements retained)
**Audit references:** B2_CAUSAL_ATTRIBUTION_AUDIT.md (round 41), external audit round 42
**Statistical engine:** FROZEN at commit `39f5d37` — unchanged by this revision

---

## Purpose

R5 does NOT patch the 9 defects from the Causal Attribution Audit one-for-one. R5 establishes a **causal chain** from source material → engine-generated information → candidate → independent adjudication → result, with an immutable **provenance ledger** as the central artifact.

The goal is not to manufacture a stronger scientific claim. The goal is to ensure that if B2 produces a positive result, an independent auditor can reconstruct exactly what information existed at every stage and prove that the final candidate was not selected or altered after the fact.

---

## Central Epistemic Boundary

R5 establishes two explicitly separated claims:

```
SYSTEM-LEVEL CLAIM (tested by B2):
    The complete frozen pipeline (engine + provider + prompts + sources)
    produces discovery candidates satisfying the adjudication criteria.

COMPONENT-LEVEL CLAIM (NOT tested by B2):
    A particular component (extraction, abstraction, transfer, generation)
    contributes causally to discovery.
```

B2 tests ONLY the system-level claim. Component attribution is deferred to a preregistered ablation/replication study (Stage 2B+). R5 does NOT quietly turn B2 into an attribution experiment.

Even if B2 produces a statistically significant positive result, the conclusion remains:

```
DISCOVERY_PIPELINE_SIGNAL_DETECTED
```

NOT:

```
THE ENGINE HAS ACHIEVED THE NORTH STAR
```

The latter requires independent Stage 2B replication and component-attribution work already reserved by the protocol.

---

## The Causal Chain

```
SOURCE PAIR (SHA-256 committed)
    ↓
FROZEN ENGINE INVOCATION (provider, model, prompt, temperature, seed — all frozen)
    ↓
RAW OUTPUT (SHA-256 captured before any human sees it)
    ↓
MECHANICAL PARSER (frozen, deterministic)
    ↓
CANDIDATES 1..K (K ≤ 3, first-3-eligible rule)
    ↓
IMMUTABLE PROVENANCE LEDGER (per-candidate, hash-committed)
    ↓
ADJUDICATION (Gate A, Gate C, Gate B — all blinded)
    ↓
CASE-LEVEL BINARY OUTCOME (one per case per arm)
    ↓
PRIMARY STATISTICAL ANALYSIS (frozen statistical engine, commit 39f5d37)
    ↓
SENSITIVITY ANALYSIS (leave-one-case-out, per-domain — does NOT alter primary decision)
    ↓
RESULT CLASSIFICATION
```

No human may select, rewrite, discard, or regenerate candidates at any point in this chain.

---

## 1. Immutable Candidate Capture

### Rule

```
CANDIDATE CAPTURE PROTOCOL:
    1. The engine is invoked ONCE per case per arm.
    2. The engine's raw output stream is captured to an immutable
       write-only log BEFORE any human sees the output.
    3. The raw output SHA-256 is computed and recorded.
    4. A frozen mechanical parser extracts candidates from the raw output.
    5. The FIRST 3 eligible candidates (passing basic format validation)
       are captured for adjudication.
    6. If the engine produces < 3 candidates, all are adjudicated.
    7. If the engine produces > 3 candidates, candidates 4+ are DISCARDED
       (recorded in the provenance ledger but NOT adjudicated).
    8. NO researcher may:
       - select the "best" candidates
       - rewrite candidates
       - discard weak candidates
       - regenerate after seeing results
       - choose which three enter adjudication
    9. The raw output is retained indefinitely for audit.
```

### Engine output limit

Preferably, the engine itself is hard-limited to producing exactly 3 candidates per invocation. If the engine cannot be hard-limited, the first-3-eligible mechanical rule applies. The rule is determined by the parser, not by a human.

### What this establishes

An independent auditor can answer: **"Did the engine actually generate this candidate?"** by checking the raw output SHA-256 against the provenance ledger.

---

## 2. Generation Attribution vs. Provider Attribution

### The problem

The pipeline is effectively:

```
Maestro discovery machinery
    +
ZAI / GLM (provider)
    +
training corpus (provider's, not ours)
    +
prompts (ours)
    +
source material (ours)
    ↓
candidate
```

A positive B2 result establishes that **the complete frozen pipeline** produced the candidate. It does NOT establish that the internal discovery architecture (transfer/generation) caused the discovery — the novel information could have come from the provider's training data.

### R5 resolution

R5 explicitly defines the claim boundary:

```
SYSTEM-LEVEL CLAIM (what B2 tests):
    "The preregistered system configuration — engine pipeline + ZAI/GLM
     provider + frozen prompts + frozen source material — generated
     candidates satisfying the adjudication criteria."

    This claim is tested by B2.

COMPONENT-LEVEL CLAIM (what B2 does NOT test):
    "The engine's transfer/generation component causally contributed
     to the discovery."

    This claim is NOT tested by B2. It requires:
    - Provider ablation (replace ZAI with a different provider, test
      whether the capability survives)
    - Component ablation (replace transfer with a trivial join, test
      whether the capability degrades)
    - Both are Stage 2B+ experiments with separate preregistration.
```

### Provider dependence acknowledgment

The protocol explicitly states:

```
PROVIDER DEPENDENCE:
    B2 uses ZAI/GLM (glm-4-plus) as the LLM provider. The provider
    is part of the tested system. A positive result is attributable
    to the system configuration, not to the engine architecture alone.

    The claim is limited to:
        "the engine+provider pipeline produced..."

    NOT:
        "the engine's transfer mechanism produced..."

    Component-level attribution requires ablation (Stage 2B+).
```

### What R5 does NOT do

R5 does NOT add component ablation to B2. That would introduce another enormous design surface and turn B2 into an attribution experiment. R5 preserves B2 as a system-level test.

---

## 3. Frozen Gate-A Calibration Exemplars

### The problem

The A0–A4 taxonomy is defined verbally but not operationalized. Two evaluators can honestly disagree about "obvious composition."

### R5 resolution

R5 includes a **frozen calibration set** with concrete examples for each level. These examples are:

- Created before study execution
- From domains OUTSIDE the study sample
- Frozen (SHA-256 committed)
- Available to every adjudicator before seeing study cases
- Never modified after seeing B2 results

### Frozen exemplars

```
GATE A CALIBRATION EXEMPLARS (frozen, SHA-256: [to be computed at freeze])

=== A0 — Explicit ===
Source A: "Calcium phosphate forms crystalline deposits in bone tissue
          through a process mediated by osteoblast cells."
Source B: "Marine diatoms precipitate silica-based cell walls using
          enzymatic silicatein proteins."
Candidate: "Calcium phosphate forms crystalline deposits in bone tissue
            through a process mediated by osteoblast cells."
Classification: A0 — The candidate literally restates Source A.

=== A1 — Lexical/Paraphrase ===
Source A: "Calcium phosphate forms crystalline deposits in bone tissue
          through a process mediated by osteoblast cells."
Source B: "Marine diatoms precipitate silica-based cell walls using
          enzymatic silicatein proteins."
Candidate: "Apatite minerals accumulate in skeletal structures via
            osteoblast-mediated mineralization."
Classification: A1 — The candidate is a paraphrase of Source A.

=== A2 — Entity/Relation Extraction ===
Source A: "Calcium phosphate forms crystalline deposits in bone tissue
          through a process mediated by osteoblast cells."
Source B: "Marine diatoms precipitate silica-based cell walls using
          enzymatic silicatein proteins."
Candidate: "Both bone tissue and marine diatoms use biologically
            mediated mineral precipitation."
Classification: A2 — Direct extraction of entities (bone, diatoms,
                mineral precipitation) and their shared relation.

=== A3 — Obvious Composition ===
Source A: "Ultrasound waves cause acoustic cavitation in liquids,
          creating localized high-pressure zones."
Source B: "Crystal nucleation rate is sensitive to local pressure
          variations in supersaturated solutions."
Candidate: "Ultrasound-induced cavitation can accelerate crystal
            nucleation by creating localized high-pressure zones in
            supersaturated solutions."
Classification: A3 — The candidate is an obvious composition of
                Source A (cavitation creates high pressure) and
                Source B (pressure affects nucleation). Both pieces
                are explicit; the join is obvious.

=== A4 — Non-Trivial Synthesis ===
Source A: "Ultrasound waves cause acoustic cavitation in liquids,
          creating localized high-pressure zones that persist for
          microseconds."
Source B: "Polymorph selection in crystallization depends on the
          thermodynamic pathway, with metastable forms nucleating
          first under certain kinetic conditions."
Candidate: "Ultrasonic cavitation can control polymorph selection by
            preferentially nucleating metastable crystal forms through
            transient high-pressure shockwaves that alter the kinetic
            pathway."
Classification: A4 — Neither source contains this mechanism. The
                candidate synthesizes: (1) cavitation creates
                transient pressure (Source A), (2) polymorph selection
                depends on kinetic pathway (Source B), (3) transient
                pressure could alter the kinetic pathway to favor
                metastable forms (synthesis). Step 3 is not obvious
                from either source alone.
```

### Calibration selection rule

```
CALIBRATION SELECTION RULE:
    Calibration cases are selected from domains OUTSIDE the study sample.
    They are selected to illustrate the CLASSIFICATION BOUNDARIES
    (what makes A3 different from A4), not to make adjudicators agree.

    Calibration cases CANNOT be selected because they make adjudicators
    agree. If adjudicators disagree on calibration, that is recorded
    and the adjudication rubric is revised BEFORE study execution.

    Calibration results are recorded but NOT used to adjust study
    results. Inter-rater reliability (Cohen's kappa) is calculated
    on calibration cases. If kappa < 0.40, adjudication procedure
    needs revision before study execution.
```

---

## 4. Novelty Terminology — NO_PRECEDENT_FOUND, Not NOVEL

### Rule

```
TERMINOLOGY:
    OLD: NOVEL_AS_OF_CUTOFF
    NEW: NO_PRECEDENT_FOUND_UNDER_PREREGISTERED_SEARCH

The protocol explicitly states:
    "A NO_PRECEDENT_FOUND result does NOT establish that the candidate
     is novel. It establishes only that the preregistered search
     procedure did not find prior art. A stronger independent novelty
     audit is required before any novelty claim."

RESERVED FOR STAGE 2B+:
    NOVELTY_ESTABLISHED — requires independent novelty investigation
    beyond the preregistered search. Not achieved by B2.
```

### Endpoint change

```
B2 PRIMARY ENDPOINT (updated):
    CASE_SUCCESS_i = 1 iff
        candidate generated
        AND cross-domain
        AND Gate A = A4
        AND Gate C = PASS
        AND Gate B = NO_PRECEDENT_FOUND_UNDER_PREREGISTERED_SEARCH
```

---

## 5. Two-Channel Novelty Search

### The problem

Pure lexical (TF-IDF) search cannot detect prior art described with different vocabulary. Candidate wording can manufacture false novelty.

### R5 resolution

R5 uses **two predetermined search channels**:

```
CHANNEL A — LEXICAL (existing design, unchanged):
    - TF-IDF keyword extraction from candidate text
    - Top 5 keywords
    - Search 4 databases: Google Scholar, PubMed, arXiv, Semantic Scholar
    - Top 20 results per database, top 5 full-text review
    - Result: PRIOR_ART_FOUND or NO_LEXICAL_MATCH

CHANNEL B — MECHANISM-NORMALIZED (new):
    - An independent evaluator (different from Gate A/C evaluator)
      examines the candidate's MECHANISM (not its wording)
    - The evaluator generates 3 ALTERNATIVE FORMULATIONS of the same
      mechanism (paraphrases a prior author might have used)
    - Each alternative formulation is searched using Channel A protocol
    - Result: PRIOR_ART_FOUND or NO_MECHANISM_MATCH
```

### Critical constraint

```
MECHANISM-NORMALIZATION INDEPENDENCE:
    The mechanism-normalization dictionary and alternative-formulation
    generation must be FROZEN INDEPENDENTLY of the candidate and
    generated WITHOUT seeing whether the candidate is from the engine
    or baseline.

    The evaluator who generates alternative formulations:
    - Does NOT know which arm generated the candidate
    - Does NOT see the candidate's source text (only the mechanism)
    - Uses a FROZEN synonym/functional-terminology dictionary
      (committed before execution, SHA-256 recorded)

    Otherwise the novelty evaluator can unconsciously create a search
    strategy that favors one arm.
```

### Classification

```
    Channel A finds prior art → PRIOR_ART_FOUND
    Channel A fails but Channel B finds prior art → PRIOR_ART_FOUND
        (lexical paraphrase manufactured false novelty)
    Both channels fail → NO_PRECEDENT_FOUND_UNDER_PREREGISTERED_SEARCH
```

---

## 6. Case-Level Primary Endpoint — Singular Binary

### Rule

```
PRIMARY ENDPOINT (singular, case-level):

    CASE_SUCCESS_i ∈ {0, 1}

    CASE_SUCCESS_i = 1 iff
        at least one candidate from case i (arm = engine) is:
            AND Generated
            AND Cross-domain
            AND Gate A = A4
            AND Gate C = PASS
            AND Gate B = NO_PRECEDENT_FOUND_UNDER_PREREGISTERED_SEARCH

    CASE_SUCCESS_i = 0 otherwise

B2 PRIMARY OUTCOME:
    engine_yield = Σ CASE_SUCCESS_i / N_clean

STATISTICAL UNIT:
    The case (i = 1..N_clean) is the ONLY unit of analysis.
    Candidate-level outcomes are NOT counted as independent observations.
    Case-level success is a single binary value per case per arm.

MULTIPLICITY CONTROL:
    - The primary comparison is Engine yield vs. Null yield.
    - All other comparisons are SECONDARY and EXPLORATORY.
    - No primary inferential claim is made from secondary comparisons.
    - The primary endpoint is the ONLY endpoint that can trigger
      DISCOVERY_PIPELINE_SIGNAL_DETECTED.

PSEUDO-REPLICATION PROHIBITION:
    Three successful candidates in one case do NOT equal three
    observations. They equal one CASE_SUCCESS = 1.
```

---

## 7. No Anti-Outlier Rule — Sensitivity Analysis Instead

### The problem

The previous audit (round 41) suggested an "anti-outlier rule" (SINGLE_CASE_SIGNAL vs MULTI_CASE_SIGNAL). The round 42 auditor correctly challenged this: a single successful case SHOULD be allowed to drive the result if the preregistered primary endpoint says it does. Inventing an outlier exclusion creates another researcher degree of freedom.

### R5 resolution

R5 does NOT add an anti-outlier rule. Instead:

```
REPORTING RULE:
    The primary case-level result is reported as-is.
    No outlier exclusion. No threshold based on case count.

    In addition, the following are reported (do NOT alter the primary decision):
    1. LEAVE-ONE-CASE-OUT SENSITIVITY ANALYSIS:
       - Recompute engine_yield and null_yield with each case removed in turn.
       - Report the range of yields and the range of p-values.
       - If the result is driven by a single case, this will be visible.

    2. PER-DOMAIN DISTRIBUTION:
       - Report which domain pairs produced successful candidates.
       - Report domain concentration (e.g., "3 of 5 successes came from
         acoustics-crystallization pairs").

    3. CASE-LEVEL SUCCESS TABLE:
       - For each case, report: case_id, domain_pair, n_candidates,
         best_candidate_outcome (A4? C=PASS? B=?), case_success (0/1).

    The sensitivity analysis MUST NOT alter the primary decision.
    If the primary endpoint says DISCOVERY_PIPELINE_SIGNAL_DETECTED,
    that is the result — even if the sensitivity analysis shows the
    result is fragile.

    The sensitivity analysis is REPORTED, not USED for the decision.
    This preserves epistemic honesty without introducing researcher
    degrees of freedom.
```

---

## 8. Baseline Equivalence Audit — Before Execution

### The problem

The retrieval baseline produces entity pairs while the engine produces mechanism hypotheses. The comparison can be statistically immaculate and scientifically unfair.

### R5 resolution

R5 requires a **baseline equivalence audit** before freeze. The audit must establish that the retrieval baseline can produce an object eligible for the same Gate A, Gate C, and novelty adjudication.

### Common candidate schema

```
COMMON CANDIDATE SCHEMA (all arms must produce this):
    {
        "relationship": "<proposed cross-domain relationship>",
        "mechanism": "<proposed mechanism, or 'NO_MECHANISM_PROPOSED'>",
        "source_A_reference": "<citation to Source A>",
        "source_B_reference": "<citation to Source B>"
    }
```

### Retrieval arm adaptation

```
RETRIEVAL ARM CANDIDATE FORMAT:
    The retrieval arm must populate the common schema:
        relationship: "<entity_a> co-occurs with <entity_b>"
        mechanism: "NO_MECHANISM_PROPOSED"
        source_A_reference: <citation>
        source_B_reference: <citation>

    This is a fair candidate. It will naturally fail Gate C (no mechanism
    to validate), but this is a FAIR failure — the retrieval arm
    genuinely cannot produce a mechanism, and that is the point of
    the comparison.

    The retrieval arm is NOT given a mechanism-generation capability.
    That would make it equivalent to the engine, defeating the purpose
    of the baseline.
```

### Baseline equivalence audit (before freeze)

```
BASELINE EQUIVALENCE AUDIT:
    An independent party verifies BEFORE execution:
    1. All arms produce candidates in the common schema.
    2. All arms have the same candidate budget (3 per case).
    3. All arms have the same adjudication pipeline.
    4. All arms have the same novelty search protocol.
    5. All arms are blinded identically.
    6. The retrieval arm is structurally capable of producing a
       candidate that COULD pass Gate A (if it proposed a non-trivial
       relationship) and Gate C (if it proposed a valid mechanism).
       If the retrieval arm is structurally incapable of passing
       Gate C (because it produces NO_MECHANISM_PROPOSED), this is
       classified as:
           STRUCTURALLY_DISADVANTAGED — reported descriptively.
       The primary comparison (engine vs. null) is NOT affected.
       The engine-vs-retrieval comparison is downgraded to
       descriptive only.

    This audit is recorded and SHA-256 committed before execution.
```

---

## 9. Human Arm — Descriptive Only

### Rule

```
HUMAN ARM CLASSIFICATION:
    DESCRIPTIVE_HUMAN_REFERENCE

    Explicitly:
    - No hypothesis test.
    - No superiority claim.
    - No inferential comparison.
    - No contribution to primary endpoint.

    The 30-minute human budget makes it unsuitable as an inferentially
    equivalent comparator. The human arm provides a qualitative sense
    of what a human expert can produce under constrained conditions,
    NOT a statistical baseline.

PROHIBITED:
    - Any claim of the form "engine outperforms human"
    - Any statistical test comparing engine yield to human yield
    - Any p-value or CI involving the human arm

PERMITTED:
    - Descriptive reporting: "the human arm produced N candidates
      in 30 minutes across M cases; K passed Gate A"
    - Qualitative comparison: "the engine produced candidates in
      time T; the human produced candidates in 30 minutes"
    - Discussion of resource-budget inequivalence as a limitation
```

---

## 10. Provenance Ledger (New Mandatory Artifact)

### Purpose

For every candidate, an immutable provenance record is maintained. This answers the question that matters most:

> **Can an independent auditor reconstruct exactly what information existed at every stage and prove that the final candidate was not selected or altered after the fact?**

### Schema

```json
{
  "case_id": "CASE-001",
  "arm": "engine",
  "candidate_id": "CASE-001-ENGINE-CAND-001",
  "raw_output_sha256": "<SHA-256 of the engine's raw output>",
  "raw_output_path": "provenance/CASE-001-engine-raw.txt",
  "generation_timestamp": "<ISO 8601 timestamp>",
  "engine_version": "<git commit SHA>",
  "provider": "ZAI",
  "model": "glm-4-plus",
  "prompt_hash": "<SHA-256 of the frozen prompt>",
  "source_pair_sha256": "<SHA-256 of (source_a, source_b)>",
  "candidate_rank": 1,
  "candidate_text": "<the candidate's relationship + mechanism>",
  "candidate_sha256": "<SHA-256 of candidate_text>",
  "parser_version": "<git commit SHA of the mechanical parser>",
  "adjudication_input_sha256": "<SHA-256 of what the adjudicator saw>",
  "gate_a_classification": "A4",
  "gate_a_adjudicator_ids": ["ADJ-001", "ADJ-002"],
  "gate_a_agreement": true,
  "gate_c_classification": "PASS",
  "gate_c_adjudicator_ids": ["ADJ-003", "ADJ-004"],
  "gate_c_agreement": true,
  "prior_art_search_id": "SEARCH-CASE-001-CAND-001",
  "prior_art_channel_a_result": "NO_LEXICAL_MATCH",
  "prior_art_channel_b_result": "NO_MECHANISM_MATCH",
  "prior_art_final": "NO_PRECEDENT_FOUND_UNDER_PREREGISTERED_SEARCH",
  "case_success": true,
  "case_success_timestamp": "<ISO 8601 timestamp>"
}
```

### Immutability

```
PROVENANCE LEDGER IMMUTABILITY:
    1. The ledger is append-only.
    2. Each entry is hash-chained to the previous entry.
    3. The ledger SHA-256 is committed to git before adjudication begins.
    4. After adjudication, the ledger is finalized and re-committed.
    5. Any discrepancy between the pre-adjudication and post-adjudication
       ledger (other than adding adjudication results) is a FATAL
       integrity violation.

    The timestamp is provenance metadata — unlike the power artifact,
    it is not claimed as part of a deterministic mathematical output.
    It records WHEN the candidate was generated, for audit purposes.
```

### What this establishes

An independent auditor can:
1. Check `raw_output_sha256` matches the retained raw output
2. Check `candidate_sha256` matches the candidate text
3. Check `adjudication_input_sha256` matches what the adjudicator saw
4. Verify the hash chain is unbroken
5. Confirm no candidate was altered after generation
6. Confirm no candidate was selected post-hoc
7. Confirm the adjudication was performed on the exact candidate that was generated

---

## R5 Acceptance Gate

R5 is NOT freeze-ready until ALL of the following are mechanically true:

| # | Requirement | Required state | Status |
|---|---|---|---|
| 1 | Candidate capture | Immutable (raw output SHA-256 before human sees) | SPECIFIED |
| 2 | Candidate selection | Mechanical (first-3-eligible rule, no researcher selection) | SPECIFIED |
| 3 | Maximum candidates | Frozen (K ≤ 3) | SPECIFIED |
| 4 | Raw generation output | Hash-committed (SHA-256 in provenance ledger) | SPECIFIED |
| 5 | Candidate rewriting | Forbidden (candidate_sha256 must match raw output) | SPECIFIED |
| 6 | Pipeline attribution | System-level claim only | SPECIFIED |
| 7 | Provider attribution | Explicitly separated (provider is part of tested system) | SPECIFIED |
| 8 | Gate-A examples | Frozen (5 exemplars, A0–A4, SHA-256 committed) | SPECIFIED |
| 9 | Gate-A calibration | Pre-study (kappa < 0.40 → revise before execution) | SPECIFIED |
| 10 | Gate-C adjudication | Independent/blinded (min 2 adjudicators, disagreement → 3rd) | SPECIFIED |
| 11 | Primary endpoint | One case-level binary (CASE_SUCCESS_i ∈ {0,1}) | SPECIFIED |
| 12 | Candidate multiplicity | Secondary only (candidate-level outcomes not primary) | SPECIFIED |
| 13 | Novelty wording | NO_PRECEDENT_FOUND_UNDER_PREREGISTERED_SEARCH | SPECIFIED |
| 14 | Novelty search | Lexical + mechanism-normalized (two channels) | SPECIFIED |
| 15 | Search protocol | Frozen before execution (dictionary SHA-256 committed) | SPECIFIED |
| 16 | Retrieval baseline | Same candidate schema (common schema, structural fairness audit) | SPECIFIED |
| 17 | Human arm | Descriptive only (no inferential comparison) | SPECIFIED |
| 18 | Outliers | No exclusions (sensitivity analysis only, does NOT alter decision) | SPECIFIED |
| 19 | Sensitivity analysis | Predeclared (leave-one-case-out, per-domain, case-level table) | SPECIFIED |
| 20 | Provenance | Immutable per-candidate ledger (hash-chained, append-only) | SPECIFIED |
| 21 | Domain concentration | Reported (per-domain distribution in results) | SPECIFIED |
| 22 | Provider dependence | Explicitly limited claim (system-level, not component-level) | SPECIFIED |

**All 22 requirements are SPECIFIED in this document.** Freeze-readiness requires:
1. Adversarial review of this R5 document
2. Computation and commitment of all SHA-256 values (Gate-A exemplars, search dictionary, source pairs)
3. Implementation of the provenance ledger schema
4. Baseline equivalence audit (before execution, not before freeze)

---

## Decision Partition (Updated)

```
IF baseline_equivalence_audit == FAILED:
    INCONCLUSIVE_UNFAIR_BASELINE

ELSE IF N_clean < 15:
    INSUFFICIENT_CLEAN_CASES

ELSE IF null_validity == FAILED:
    INCONCLUSIVE_INVALID_NULL

ELSE IF provenance_ledger_integrity == FAILED:
    INCONCLUSIVE_PROVENANCE_VIOLATION

ELSE IF engine_yield == 0:
    DISCOVERY_SIGNAL_NOT_DETECTED

ELSE IF engine_yield > 0 AND engine_yield > null_yield (exact McNemar, α=0.05, CI_lower > 0.20):
    DISCOVERY_PIPELINE_SIGNAL_DETECTED (pilot — requires Stage 2B replication)

ELSE:
    DISCOVERY_SIGNAL_NOT_DETECTED
```

### What each state means

- **INCONCLUSIVE_UNFAIR_BASELINE:** Baseline equivalence audit failed. Redesign needed.
- **INSUFFICIENT_CLEAN_CASES:** Too many cases excluded. Need better source materials.
- **INCONCLUSIVE_INVALID_NULL:** Null construction failed quality audit.
- **INCONCLUSIVE_PROVENANCE_VIOLATION:** Provenance ledger integrity check failed. Result cannot be trusted.
- **DISCOVERY_SIGNAL_NOT_DETECTED:** The engine did not produce a passing candidate, or the engine yield did not exceed null yield.
- **DISCOVERY_PIPELINE_SIGNAL_DETECTED:** The engine produced ≥1 passing candidate AND engine yield > null yield. Does NOT establish general discovery capability. Requires Stage 2B replication.

### DISCOVERY_PIPELINE_SIGNAL_DETECTED handling

```
- Does NOT establish general discovery capability
- Does NOT establish component-level attribution
- Does NOT establish novelty (only NO_PRECEDENT_FOUND)
- Justifies Stage 2B expansion (new cases, new domains, new evaluators)
- Stage 2B must independently confirm before any discovery claim
- Stage 2B+ (component ablation) required for component attribution
```

---

## Statistical Engine — Unchanged

The statistical engine remains FROZEN at commit `39f5d37`. R5 does NOT modify:
- `scripts/r4_1_power_analysis.py`
- `scripts/r4_reference_vectors.py`
- `experiments/measurement_discrimination/r4_1_power_analysis.json`
- The exact McNemar test (binom.sf)
- The Wald+CC CI
- The combined decision rule (p < 0.05 AND CI_lower > 0.20)
- The formal root isolation via Sturm sequences
- The exact algebraic extremum evaluation
- The fail-closed comparison

R5 uses the frozen statistical engine for the primary analysis. No statistical changes.

---

## What R5 Does NOT Authorize

- Implementing any protocol
- Executing any protocol
- Modifying the frozen statistical engine
- Modifying the frozen matcher, gold set, Gate 2 protocol, M-008, DXP-005
- Making any discovery or capability claim
- Skipping the adversarial review of R5
- Skipping the baseline equivalence audit

---

## Status

```
Statistical engine:               FROZEN (commit 39f5d37)
B2 protocol design (R5):          SPECIFIED — requires adversarial review
B2 freeze:                        BLOCKED (pending R5 review)
B1/B2 execution:                  BLOCKED
Phase 8 execution:                BLOCKED
North Star:                       NOT ACHIEVED

Next steps:
  1. Adversarial review of R5
  2. Computation and commitment of SHA-256 values (exemplars, dictionary, sources)
  3. Implementation of provenance ledger schema
  4. Baseline equivalence audit (before execution)
  5. Freeze consideration (after review passes)
  6. Execution authorization (separate, after freeze)
```

---

## The Stopping Line

R5 closes causal-attribution and experimental-integrity defects. R5 does NOT manufacture a stronger scientific claim.

Even if B2 produces:

```
25 cases
3 candidates/case
↓
1+ valid + non-trivial + no-precedent-found candidate
↓
statistically significant engine > null (exact McNemar, α=0.05)
↓
provenance ledger integrity verified
↓
sensitivity analysis reported
```

The conclusion is:

```
DISCOVERY_PIPELINE_SIGNAL_DETECTED
```

NOT:

```
THE ENGINE HAS ACHIEVED THE NORTH STAR
```

The North Star requires:
- Independent Stage 2B replication (new cases, new domains, new evaluators)
- Component attribution (provider ablation, component ablation)
- Stronger novelty investigation (NOVELTY_ESTABLISHED, not just NO_PRECEDENT_FOUND)

That is the right stopping line.
