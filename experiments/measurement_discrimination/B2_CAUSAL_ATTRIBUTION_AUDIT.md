# B2 Causal Attribution Audit

**Date:** 2026-08-09
**Auditor:** External (CEO directive, round 41)
**Subject:** B2 — Open Discovery protocol design
**Scope:** Candidate generation → independent adjudication → novelty → component attribution
**Statistical engine:** OUT OF SCOPE (closed at commit `39f5d37`, audit round 40)

---

## Executive Summary

The statistical substrate is now exact end-to-end (formal root isolation, exact algebraic evaluation, fail-closed comparison). **The statistical machinery is no longer the bottleneck.**

The bottleneck has moved to the **experimental design**. This audit identifies **9 design defects** in the B2 protocol that must be corrected before freeze. Several are serious enough that a positive B2 result could be **scientifically misleading** if the defects are not addressed.

The core problem is stated precisely by the auditor:

> If B2 produces a positive candidate, can we prove that the candidate came from the discovery capability being tested, rather than from leakage, retrieval, provider priors, evaluator discretion, candidate multiplicity, or an unfair baseline?

The current design does NOT establish this proof. This audit specifies what is required.

---

## Audit Framework

Each attack is classified as:

| Classification | Meaning |
|---|---|
| **FATAL** | The defect invalidates the experiment's central claim. Must be fixed before freeze. |
| **SERIOUS** | The defect creates a plausible alternative explanation for a positive result. Must be fixed before freeze. |
| **MODERATE** | The defect weakens interpretability but does not invalidate the primary endpoint. Should be fixed before freeze; must be fixed before Stage 2B. |
| **ALREADY HANDLED** | The current design addresses this concern adequately. No change required. |

---

## Attack 1: Candidate Capture — Researcher Degrees of Freedom

### Auditor's concern

> The engine must be unable to generate candidate #4 and then have the coordinator select the "best three." It should be: engine output → immutable candidate capture → first 3 eligible outputs → all 3 adjudicated. Not: engine generates 17 → researcher selects 3 → adjudication.

### Current design (B1_B2_DETAILED_DESIGN.md §1.3, §2.3)

The design specifies the pipeline (MechanismExtraction → MechanismAbstraction → CrossDomainTransfer → HypothesisGeneration → candidate) and states "up to three candidates per case." However, the design does **NOT** specify:

1. How many candidates the engine actually generates internally
2. Whether the engine generates exactly 3 or generates more and selects 3
3. Whether the "first 3" are captured immutably or selected post-hoc
4. Whether researchers see all candidates before selection

### Defect classification: **FATAL**

This is a hidden researcher degree of freedom. If the engine generates 17 candidates and a researcher selects the "best 3," the experiment has an uncontrolled selection bias. The case-level success rate becomes a function of both engine capability AND researcher judgment.

### Required fix

The protocol must specify:

```
CANDIDATE CAPTURE RULE:
    1. The engine is invoked ONCE per case.
    2. The engine's output stream is captured immutably (write-only log).
    3. The FIRST 3 eligible candidates (passing basic format validation) are
       captured for adjudication.
    4. NO selection, NO filtering, NO "best 3" curation.
    5. If the engine produces < 3 candidates, all are adjudicated.
    6. If the engine produces > 3 candidates, candidates 4+ are DISCARDED
       (recorded but NOT adjudicated).
    7. The researcher CANNOT see candidate content before capture.
```

The capture log must be SHA-256 hashed and committed before adjudication begins.

---

## Attack 2: Component Attribution — Which Component Produced the Novel Information?

### Auditor's concern

> A positive B2 result does not yet establish that the discovery capability resides in the transfer/generation mechanism. It could arise because extraction already contains the answer, abstraction collapses the domain distinction, transfer merely joins two already-compatible abstractions, hypothesis generation paraphrases an obvious combination, the LLM provider supplies the conceptual leap, or some combination of these.

### Current design (B1_B2_DETAILED_DESIGN.md §1.3)

The design specifies the pipeline:
```
Source A → MechanismExtractionEngine → MechanismAbstractionEngine
Source B → MechanismExtractionEngine → MechanismAbstractionEngine
    ↓
CrossDomainTransferEngine.generate()
    ↓
HypothesisGenerationEngine.generate()
    ↓
Candidate
```

The design does **NOT** specify:
1. Which component is the "discovery" component being tested
2. How to attribute a positive result to a specific component
3. Whether intermediate artifacts (extracted mechanisms, abstractions) are logged for attribution analysis
4. Whether the LLM provider (ZAI/GLM) is part of the tested system or a confound

### Defect classification: **FATAL**

This is the deepest conceptual issue. A positive B2 result currently attributes the discovery to "the engine" as a monolithic black box. But the engine is a CHAIN of components, and the novel information could enter at any stage — including from the LLM provider's training data.

### Required fix

The protocol must specify component attribution as a **preregistered requirement**, not a Stage 2B aspiration:

```
COMPONENT ATTRIBUTION PROTOCOL:
    1. Every intermediate artifact is logged:
       - extracted_mechanisms_a (from MechanismExtractionEngine on Source A)
       - extracted_mechanisms_b (from MechanismExtractionEngine on Source B)
       - abstracted_mechanisms_a (from MechanismAbstractionEngine on A)
       - abstracted_mechanisms_b (from MechanismAbstractionEngine on B)
       - transfer_result (from CrossDomainTransferEngine)
       - final_candidate (from HypothesisGenerationEngine)

    2. For each B2-positive candidate, a COMPONENT ATTRIBUTION AUDIT is
       performed:
       - Does the candidate mechanism appear in extracted_mechanisms_a
         or extracted_mechanisms_b? (extraction already contained it)
       - Does the candidate mechanism appear in abstracted_mechanisms_a
         or abstracted_mechanisms_b? (abstraction already contained it)
       - Is the candidate a trivial join of abstractions from A and B?
         (transfer merely joined compatible pieces)
       - Does the candidate require a conceptual leap not present in any
         intermediate? (genuine generation)

    3. The primary endpoint is DOWNGRADED based on attribution:
       - If the candidate appears in extraction → NOT_DISCOVERY
         (extraction found it, not generation)
       - If the candidate appears in abstraction → NOT_DISCOVERY
         (abstraction found it, not generation)
       - If the candidate is a trivial join → COMPOSITIONAL_NOT_DISCOVERY
       - If the candidate requires a leap → DISCOVERY_SIGNAL

    4. Provider attribution:
       - The LLM provider (ZAI/GLM) is explicitly acknowledged as part
         of the tested system.
       - A positive result establishes:
         "the engine+provider pipeline produced a candidate..."
       NOT:
         "the engine's transfer/generation component produced a candidate..."
       - Component-level attribution requires ablating the provider
         (Stage 2B: replace ZAI with a different provider, test whether
         the capability survives).
```

---

## Attack 3: Gate A Operationalization — Frozen Examples Required

### Auditor's concern

> The same human evaluator is being asked to determine whether the proposal is "obvious" from the inputs and whether it constitutes a meaningful synthesis. You need operational examples frozen before execution. Not just definitions.

### Current design (B1_B2_DETAILED_DESIGN.md §1.6)

The design defines the A0–A4 rubric:
- A0 — Explicit: stated verbatim in either input
- A1 — Lexical/paraphrase: recoverable via synonym, substring, paraphrase
- A2 — Entity/relation extraction: directly extractable entity or relation
- A3 — Direct compositional inference: obvious composition of explicit relationships
- A4 — Non-trivial derived proposal: cannot be recovered by any above method

However, the design provides **NO frozen examples** for each level. The rubric is defined verbally but not operationalized with concrete cases.

### Defect classification: **SERIOUS**

Without frozen examples, two evaluators can honestly disagree about what "obvious composition" means. This is the next level of the adjudicator disagreement problem recognized in R1/R2.

### Required fix

The protocol must include a **frozen examples calibration set** (committed before execution, SHA-256 recorded):

```
GATE A CALIBRATION EXAMPLES (frozen before execution):

A0 (explicit):
  Source A: "Calcium phosphate forms crystalline deposits in bone tissue."
  Candidate: "Calcium phosphate forms crystalline deposits in bone tissue."
  → The candidate literally states what Source A says.

A1 (lexical/paraphrase):
  Source A: "Calcium phosphate forms crystalline deposits in bone tissue."
  Candidate: "Apatite minerals precipitate in skeletal structures."
  → Candidate is a paraphrase of Source A.

A2 (entity/relation extraction):
  Source A: "Calcium phosphate forms crystalline deposits in bone tissue."
  Source B: "Marine shells use calcium carbonate for structural support."
  Candidate: "Calcium phosphate and calcium carbonate are both structural minerals."
  → Candidate is a direct extraction of entities and their relation.

A3 (compositional):
  Source A: "Calcium phosphate forms crystalline deposits in bone tissue."
  Source B: "Marine shells use calcium carbonate for structural support."
  Candidate: "Biomineralization processes in both bone and shells use calcium-based minerals for structural purposes."
  → Candidate is an obvious composition of the two sources.

A4 (non-trivial derived):
  Source A: "Ultrasound causes cavitation in liquids."
  Source B: "Crystal nucleation is sensitive to acoustic perturbations."
  Candidate: "Ultrasonic cavitation can control polymorph selection in crystallization by preferentially nucleating metastable forms."
  → Neither source contains this mechanism. The candidate requires a
     synthesis that is not an obvious composition.
```

Evaluators must be calibrated on these examples before seeing study cases. Calibration results are recorded. Evaluators who cannot reproduce the A0–A4 classification on calibration examples are disqualified.

---

## Attack 4: Novelty — Lexical Paraphrase Can Manufacture False Novelty

### Auditor's concern

> Candidate wording can manufacture novelty. The mechanism isn't novel. The lexical representation is novel. Novelty must operate at two levels: lexical retrieval + semantic/mechanistic precedent search.

### Current design (B1_B2_DESIGN_REVISION_R4.md §3)

The design specifies:
- Query generation: Mechanical, extract top 5 keywords from candidate text (TF-IDF, fixed stopword list)
- Databases: Google Scholar, PubMed, arXiv, Semantic Scholar
- Max results per database: 20
- Full-text review: Top 5 after deduplication
- Search iterations: 1 per candidate (no iterative refinement)

The design does **NOT** address:
1. That candidate wording can manufacture novelty by using synonyms the search doesn't retrieve
2. That TF-IDF keyword extraction is sensitive to lexical representation
3. That a semantic/mechanistic precedent search is needed in addition to lexical retrieval

### Defect classification: **SERIOUS**

This is potentially fatal if left loose. The auditor's example is precise:

```
Actual prior art: "membrane-mediated stochastic transport"
Engine candidate: "probabilistic boundary-selective molecular transfer"
TF-IDF search → fails to retrieve prior art → NOVEL
```

The mechanism isn't novel. The **lexical representation** is novel.

### Required fix

The protocol must specify a **two-level novelty search**:

```
LEVEL 1 — LEXICAL RETRIEVAL (current design, unchanged):
    - TF-IDF keyword extraction from candidate text
    - Search 4 databases, top 20 per database, top 5 full-text review
    - Result: PRIOR_ART_FOUND or NO_LEXICAL_MATCH

LEVEL 2 — SEMANTIC/MECHANISTIC PRECEDENT SEARCH (new):
    - An independent evaluator (different from the Gate A/C evaluator)
      examines the candidate's MECHANISM (not its wording)
    - The evaluator generates 3 ALTERNATIVE FORMULATIONS of the same
      mechanism (paraphrases that a prior author might have used)
    - Each alternative formulation is searched using the same Level 1
      protocol
    - If ANY alternative formulation retrieves prior art that describes
      the same mechanism: PRIOR_ART_FOUND
    - Only if ALL alternative formulations fail to retrieve matching
      prior art: NO_PRECEDENT_FOUND_UNDER_PREREGISTERED_SEARCH

CLASSIFICATION:
    - Level 1 finds prior art → PRIOR_ART_FOUND
    - Level 1 fails but Level 2 finds prior art → PRIOR_ART_FOUND
      (lexical paraphrase manufactured false novelty)
    - Both levels fail → NO_PRECEDENT_FOUND_UNDER_PREREGISTERED_SEARCH
      (NOT "NOVEL" — the search may simply be insufficient)
```

The endpoint must remain `NO_PRECEDENT_FOUND_UNDER_PREREGISTERED_SEARCH`, NOT `NOVEL`, until Stage 2B performs a stronger independent novelty audit.

---

## Attack 5: Search Sensitivity — "No Precedent Found" ≠ "No Precedent Exists"

### Auditor's concern

> The design says no precedent found, but that does not imply no precedent exists. Therefore the endpoint should not be simply NOVEL. It should remain NO_PRECEDENT_FOUND_UNDER_PREREGISTERED_SEARCH until Stage 2B performs a stronger independent novelty audit.

### Current design (B1_B2_DETAILED_DESIGN.md §2.4, §2.5)

The current design uses:
- Gate B outcome: `NOVEL_AS_OF_CUTOFF / PRIOR_ART_FOUND / PARTIAL_PRECEDENT / AMBIGUOUS`
- Primary endpoint: `Gate B = NOVEL_AS_OF_CUTOFF`

The term `NOVEL_AS_OF_CUTOFF` implies the candidate IS novel, which is stronger than what the search establishes.

### Defect classification: **MODERATE**

This is primarily a terminology issue, but it has epistemic consequences. The search is reproducible but not exhaustive — "no precedent found" is not the same as "no precedent exists."

### Required fix

```
TERMINOLOGY CORRECTION:
    OLD: NOVEL_AS_OF_CUTOFF
    NEW: NO_PRECEDENT_FOUND_UNDER_PREREGISTERED_SEARCH

The primary endpoint becomes:
    Gate B = NO_PRECEDENT_FOUND_UNDER_PREREGISTERED_SEARCH

The protocol must explicitly state:
    "A NO_PRECEDENT_FOUND result does NOT establish that the candidate
     is novel. It establishes only that the preregistered search
     procedure did not find prior art. A stronger independent novelty
     audit is required before any novelty claim (Stage 2B)."
```

---

## Attack 6: Multiple-Candidate / Multiple-Arm Multiplicity

### Auditor's concern

> You have potentially: Engine, Generic LLM, Retrieval, Human, Null — and up to three candidates per case. There are many opportunities to find an apparently impressive result. The primary endpoint must be absolutely singular. And the statistical analysis must use one immutable case-level vector.

### Current design (B1_B2_DESIGN_REVISION_R4.md §4)

The design specifies:
- α/multiple-testing hierarchy with B1 → B2 sequential gatekeeping
- No multiplicity correction needed (sequential, not simultaneous)
- Both classified as exploratory

However, the design does **NOT** specify:
1. That case-level success is a single binary outcome (not candidate-level)
2. That the primary endpoint is exactly one combination (not multiple)
3. That candidate-level successes are NOT pseudo-replication

### Defect classification: **SERIOUS**

Without a singular case-level primary endpoint, candidate count becomes pseudo-replication. If each case has 3 candidates and 5 arms, that's 15 observations per case — but the case is the unit of independence.

### Required fix

```
PRIMARY ENDPOINT (singular, case-level):

    CASE_SUCCESS_i = 1 iff
        at least one candidate from case i is:
            AND Generated
            AND Cross-domain
            AND Gate A = A4
            AND Gate C = PASS
            AND Gate B = NO_PRECEDENT_FOUND_UNDER_PREREGISTERED_SEARCH

    CASE_SUCCESS_i = 0 otherwise

STATISTICAL UNIT:
    The case (i = 1..N) is the ONLY unit of analysis.
    Candidate-level outcomes are NOT counted as independent observations.
    Case-level success is a single binary value per case per arm.

MULTIPLICITY CONTROL:
    - The primary comparison is Engine CASE_SUCCESS vs. Null CASE_SUCCESS.
    - All other comparisons (Engine vs. LLM, Engine vs. Retrieval,
      Engine vs. Human) are SECONDARY and EXPLORATORY.
    - No primary inferential claim is made from secondary comparisons.
    - The primary endpoint is the ONLY endpoint that can trigger
      NORTH_STAR_SIGNAL_DETECTED.
```

---

## Attack 7: Baseline Fairness — Can Retrieval Succeed Under the Same Adjudication?

### Auditor's concern

> If retrieval produces "entity A ↔ entity B" while the engine produces "mechanistic hypothesis," then the baseline is structurally disadvantaged before adjudication. A comparison can be statistically immaculate and still be scientifically unfair. The baseline audit needs to establish: same source material, same candidate budget, same adjudication, same candidate representation, same opportunity to succeed, while differing ONLY in the proposed discovery mechanism.

### Current design (B1_B2_DETAILED_DESIGN.md §1.8)

The design specifies control equivalence:
- Same input (A+B sources) for all arms
- Same temperature (0.0) for LLM arms
- Same attempts (1) for all arms
- Same time limit for human arm (30 min)
- No external search for any arm

However, the design does **NOT** specify:
1. That the retrieval arm produces candidates in the same FORMAT as the engine
2. That the retrieval arm has the same candidate budget (3 candidates)
3. That the adjudication rubric is equally applicable to retrieval candidates
4. That the retrieval arm is not structurally disadvantaged by producing entity-pairs instead of mechanisms

### Defect classification: **SERIOUS**

This is the central baseline-equivalence question. If the retrieval arm produces entity pairs while the engine produces mechanism hypotheses, the comparison is scientifically unfair regardless of statistical validity.

### Required fix

```
BASELINE EQUIVALENCE PROTOCOL:

    1. CANDIDATE FORMAT EQUIVALENCE:
       All arms must produce candidates in the SAME format:
           (domain_a_concept, domain_b_concept, proposed_mechanism)
       The retrieval arm must produce a MECHANISM (not just an entity pair).
       If retrieval cannot produce a mechanism, it produces:
           (entity_a, entity_b, "retrieved co-occurrence — no mechanism proposed")
       This is recorded as a retrieval-format candidate.

    2. CANDIDATE BUDGET EQUIVALENCE:
       All arms get exactly 3 candidates per case (same as engine).
       The retrieval arm's 3 candidates are the top 3 entity pairs by
       co-occurrence frequency, each wrapped in the candidate format.

    3. ADJUDICATION EQUIVALENCE:
       Adjudicators see the SAME rubric for all candidates.
       Adjudicators do NOT know which arm produced which candidate.
       A retrieval candidate that says "no mechanism proposed" will
       naturally fail Gate C (no mechanism to validate) — this is
       a FAIR failure, not a structural disadvantage.

    4. OPPORTUNITY EQUIVALENCE:
       All arms have the same:
           - source material
           - candidate budget (3)
           - adjudication pipeline
           - novelty search protocol
           - blinding
       They differ ONLY in the discovery mechanism (engine pipeline
       vs. retrieval vs. LLM vs. human).

    5. STRUCTURAL FAIRNESS AUDIT:
       Before execution, an independent party verifies that all arms
       CAN produce candidates that pass Gate A and Gate C. If an arm
       is structurally incapable of passing (e.g., retrieval cannot
       produce a mechanism), that arm is classified as:
           STRUCTURALLY_DISADVANTAGED — reported descriptively, not
           used for primary inferential comparison.
```

---

## Attack 8: Human Arm — Descriptive, Not Inferential

### Auditor's concern

> The R4 document acknowledges the human arm has a 30-minute limit while other arms have computational resources. That's okay if the human arm is explicitly exploratory. It is NOT okay if it becomes evidence that "engine > human" because the resource budgets aren't equivalent. I would prohibit any primary inferential comparison involving the human arm.

### Current design (B1_B2_DETAILED_DESIGN.md §1.8, §2.7)

The design specifies:
- Human arm: 30-minute limit, same source texts
- Secondary comparisons (exploratory): Engine vs. generic LLM, Engine vs. retrieval, Engine vs. human

The design does **NOT** explicitly prohibit inferential comparison with the human arm.

### Defect classification: **MODERATE**

The human arm is useful as a descriptive reference, but inferential comparison with unequal resource budgets is scientifically invalid.

### Required fix

```
HUMAN ARM CLASSIFICATION:

    The human arm is:
        DESCRIPTIVE HUMAN REFERENCE

    It is NOT a hypothesis-testing comparator.

    PROHIBITED:
        - Any primary inferential comparison involving the human arm
        - Any claim of the form "engine outperforms human"
        - Any statistical test comparing engine yield to human yield

    PERMITTED:
        - Descriptive reporting of human arm yield
        - Qualitative comparison ("the engine produced N candidates
          in time T; the human produced M candidates in 30 minutes")
        - Discussion of resource-budget inequivalence as a limitation

    The human arm's purpose is to provide a qualitative sense of
    what a human expert can produce under constrained conditions,
    NOT to serve as a statistical baseline.
```

---

## Attack 9: Discovery Capability vs. Single Positive Result

### Auditor's concern

> Suppose 20 cases, 3 candidates/case, one candidate passes all gates. That's an interesting result. But it doesn't necessarily establish that the engine has a general discovery capability. It establishes that under this source-selection regime, this pipeline produced at least one candidate satisfying the preregistered adjudication criteria. The outcome downgrade from NORTH_STAR_ACHIEVED to DISCOVERY_PIPELINE_SIGNAL_DETECTED was correct.

### Current design (B1_B2_DETAILED_DESIGN.md §2.9)

The design already specifies:
```
NORTH_STAR_SIGNAL_DETECTED (pilot — requires Stage 2B replication)
    - Does NOT establish general discovery capability
    - Justifies Stage 2B expansion
    - Stage 2B is a NEW experiment with new cases, new domains, new evaluators
    - Stage 2B must independently confirm before any discovery claim
```

### Defect classification: **ALREADY HANDLED**

The current design correctly downgrades the outcome from `NORTH_STAR_ACHIEVED` to `NORTH_STAR_SIGNAL_DETECTED` and explicitly states it does not establish general discovery capability.

### Required enhancement

While the classification is correct, the protocol should add an explicit **generalization limitation**:

```
GENERALIZATION LIMITATION (explicit):

    A NORTH_STAR_SIGNAL_DETECTED result establishes:
        "Under this source-selection regime, this pipeline
         produced at least one candidate satisfying the
         preregistered adjudication criteria."

    It does NOT establish:
        - The engine has a general discovery capability
        - The engine would succeed on other domain pairs
        - The engine would succeed with different source materials
        - The result is not attributable to a single unusually
          favorable domain pair

    ANTI-OUTLIER RULE:
        If the NORTH_STAR_SIGNAL_DETECTED result is driven by a
        SINGLE case (1/N), the protocol must report:
            SINGLE_CASE_SIGNAL — requires Stage 2B with new cases
            from the SAME domain pair to rule out domain-pair
            idiosyncrasy.
        Only if ≥2 cases produce passing candidates can the result
        be classified as:
            MULTI_CASE_SIGNAL — still requires Stage 2B, but with
            stronger evidence of generality.
```

---

## The 15-Question Causal Attribution Audit

| # | Question | Answer against committed design |
|---|---|---|
| 1 | **Can researchers select the best 3 after seeing all outputs?** | **UNKNOWN** — the design says "up to 3 candidates per case" but does NOT specify whether the engine generates exactly 3 or generates more and researchers select. **DEFECT (Attack 1).** |
| 2 | **Is case-level success mathematically fixed before execution?** | **PARTIAL** — the case-level success definition exists but candidate multiplicity is not constrained to a single binary per case. **DEFECT (Attack 6).** |
| 3 | **Which component actually produced the novel information?** | **NOT ESTABLISHED** — the design treats the engine as a monolithic black box. No component attribution protocol. **DEFECT (Attack 2).** |
| 4 | **Could extraction/abstraction already contain the answer?** | **NOT CHECKED** — intermediate artifacts are not logged for attribution analysis. **DEFECT (Attack 2).** |
| 5 | **Are A0–A4 operationalized with frozen examples?** | **NO** — the rubric is defined verbally but no frozen calibration examples are provided. **DEFECT (Attack 3).** |
| 6 | **Can evaluators distinguish coherence from plausibility?** | **PARTIAL** — the design says adjudicators "can reject the premise" but does not provide operational criteria for distinguishing a coherent mechanism from a plausible-sounding one. **MODERATE.** |
| 7 | **Can lexical paraphrase create false novelty?** | **YES** — the novelty search is purely lexical (TF-IDF). No semantic/mechanistic precedent search. **DEFECT (Attack 4).** |
| 8 | **What establishes "no precedent found"?** | **ONLY the preregistered search** — 4 databases, 20 results each, 5 full-text reviews. No stronger audit. The endpoint should be NO_PRECEDENT_FOUND, not NOVEL. **DEFECT (Attack 5).** |
| 9 | **Can retrieval succeed under exactly the same adjudication?** | **UNKNOWN** — the design specifies same input and same budget, but does NOT specify same candidate format or same opportunity to produce a mechanism. **DEFECT (Attack 7).** |
| 10 | **Is the human arm descriptive rather than inferential?** | **NOT EXPLICITLY** — the human arm is listed as a "secondary comparison (exploratory)" but inferential comparison is not explicitly prohibited. **DEFECT (Attack 8).** |
| 11 | **Is every primary observation one case?** | **NOT GUARANTEED** — candidate-level outcomes could be counted as independent observations if the protocol is not tightened. **DEFECT (Attack 6).** |
| 12 | **Is there exactly one B2 primary endpoint?** | **PARTIAL** — the primary endpoint is defined, but the design does not explicitly state it is the ONLY endpoint that can trigger NORTH_STAR_SIGNAL_DETECTED. **DEFECT (Attack 6).** |
| 13 | **Is ZAI/GLM itself part of the tested system?** | **NOT ACKNOWLEDGED** — the design specifies ZAI as the provider but does not acknowledge it as part of the tested system. A positive result could be attributable to the provider's training data, not the engine's transfer/generation capability. **DEFECT (Attack 2).** |
| 14 | **Can the experiment distinguish engine capability from provider capability?** | **NO** — no provider ablation is specified. The protocol cannot distinguish "the engine's transfer mechanism produced the novel information" from "the LLM provider's training data contained the answer." **DEFECT (Attack 2).** |
| 15 | **What prevents one unusually favorable domain pair from driving the result?** | **NOTHING** — the design does not specify an anti-outlier rule. A single positive case out of 20 would trigger NORTH_STAR_SIGNAL_DETECTED. **DEFECT (Attack 9).** |

---

## Summary of Defects

| Attack | Defect | Classification |
|---|---|---|
| 1 | Candidate capture allows researcher selection | **FATAL** |
| 2 | No component attribution protocol | **FATAL** |
| 3 | Gate A rubric not operationalized with frozen examples | **SERIOUS** |
| 4 | Novelty search is purely lexical (paraphrase can manufacture novelty) | **SERIOUS** |
| 5 | Endpoint says "NOVEL" instead of "NO_PRECEDENT_FOUND" | **MODERATE** |
| 6 | Case-level singularity not guaranteed (pseudo-replication risk) | **SERIOUS** |
| 7 | Baseline equivalence not fully specified | **SERIOUS** |
| 8 | Human arm inferential comparison not prohibited | **MODERATE** |
| 9 | No anti-outlier rule (single case can drive result) | **MODERATE** (classification already correct, enhancement needed) |

**FATAL defects: 2** (must fix before any freeze consideration)
**SERIOUS defects: 4** (must fix before freeze)
**MODERATE defects: 3** (should fix before freeze; must fix before Stage 2B)

---

## Required Design Changes Before Freeze

The B2 protocol must be revised to address all 9 attacks. The revision (R5 or B2_REVISION_R5) must specify:

1. **Candidate Capture Rule** (Attack 1): immutable capture of first 3 eligible outputs, no researcher selection
2. **Component Attribution Protocol** (Attack 2): log all intermediate artifacts, perform attribution audit on positive candidates, acknowledge provider as part of tested system
3. **Gate A Calibration Examples** (Attack 3): frozen examples for A0–A4, evaluator calibration before study
4. **Two-Level Novelty Search** (Attack 4): lexical retrieval + semantic/mechanistic precedent search
5. **Endpoint Terminology** (Attack 5): NO_PRECEDENT_FOUND_UNDER_PREREGISTERED_SEARCH (not NOVEL)
6. **Singular Case-Level Primary Endpoint** (Attack 6): one binary per case per arm, no candidate-level pseudo-replication
7. **Baseline Equivalence Protocol** (Attack 7): same candidate format, same budget, structural fairness audit
8. **Human Arm Classification** (Attack 8): DESCRIPTIVE_HUMAN_REFERENCE, no inferential comparison
9. **Anti-Outlier Rule** (Attack 9): SINGLE_CASE_SIGNAL vs MULTI_CASE_SIGNAL classification

---

## What This Audit Does NOT Do

- Does NOT revise the B2 protocol (that is a separate revision document)
- Does NOT touch the statistical engine (closed at commit `39f5d37`)
- Does NOT authorize execution
- Does NOT freeze anything

This audit IDENTIFIES defects. The revision FIXES them. Only after the revision is reviewed and frozen may Phase 8 execution be reconsidered.

---

## Status

```
Statistical engine:               CLOSED (commit 39f5d37, audit round 40)
B2 protocol design:               9 DEFECTS FOUND (2 FATAL, 4 SERIOUS, 3 MODERATE)
B2 freeze:                        BLOCKED
B1/B2 execution:                  BLOCKED
Phase 8 execution:                BLOCKED
North Star:                       NOT ACHIEVED

Next step: Write B2_REVISION_R5 addressing all 9 defects.
           Then: adversarial review of R5.
           Then: freeze consideration.
           Then: execution authorization (separate).
```

---

## The Central Insight

> **The statistical substrate can now be exact while the experiment itself can still be scientifically invalid.**

The p-value can be computed with formal root isolation and exact algebraic evaluation, and the result can still be scientifically meaningless if:

- The candidate was selected by a researcher (not captured immutably)
- The novel information came from the LLM provider (not the engine)
- The novelty search missed prior art due to lexical paraphrase
- The baseline was structurally disadvantaged
- The result was driven by a single favorable domain pair

**Statistical exactness is necessary but not sufficient.** The experiment must also be **causally attributable** — a positive result must be traceable to the discovery capability being tested, not to leakage, retrieval, provider priors, evaluator discretion, candidate multiplicity, or an unfair baseline.

This is the attack that matters for the North Star.
