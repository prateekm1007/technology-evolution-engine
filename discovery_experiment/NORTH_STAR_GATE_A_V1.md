# NORTH_STAR_GATE_A_V1 — The Measurement Boundary

**Status:** FROZEN — pre-execution measurement specification
**Date:** 2026-08-10
**CTO Verdict:** "The next thing to freeze is not DXP-005. It is the North Star measurement boundary."

---

## What This Document Is

This is NOT a DXP-005 amendment. This is the **measurement boundary** that governs how any discovery experiment (DXP-005, DXP-005b, or successors) will be evaluated. DXP-005 execution remains on HOLD until this boundary is frozen and all six arms are independently specified.

---

## The North Star

> **Candidate not recoverable from the supplied inputs → independently non-retrievable → survives adversarial scrutiny → produces a novel falsifiable prediction → experiment agrees.**

Gate A tests steps 1-3. Gate B tests steps 4-5. **Neither gate alone establishes the North Star.**

---

## Gate A — Discovery Discrimination

### The Question

> **Can the entire TEE system outperform a strong model given the same raw external evidence, despite TEE's additional machinery?**

This is a **product-level test**, not an ablation. TEE's full pipeline (extraction, mechanism graphs, ontology, adversarial analysis, candidate generation, retrieval, novelty firewall) is compared against controls receiving the same two source documents.

### Six Frozen Arms

| Arm | Description | Infrastructure |
|-----|-------------|----------------|
| **1. TEE** | Full engine pipeline | `engine/` (all stages) |
| **2. TEE mechanism-null** | Full pipeline with null mechanism graph (same structure, irrelevant edges) | `engine/b2_provenance/generation_null.py` |
| **3. Random/null generator** | Deterministic template generation from shared extraction/abstraction prefix | `generation_null.py::generate_null_candidates()` |
| **4. Retrieval-only** | Lexical + embedding retrieval with adversarial query formulation (see §Retrieval Spec) | NEW — must be independently frozen |
| **5. Frontier LLM** | Generic LLM with same raw documents, no mechanism pipeline | NEW — must be independently frozen (see §C2 Spec) |
| **6. Expert** | Human expert with information-budget protocol | NEW — must be independently frozen (see §Expert Spec) |

### Arms 4, 5, 6 Require Independent Freeze

Arms 1-3 have existing infrastructure. Arms 4, 5, 6 are **NOT yet frozen** and must be independently specified before execution. Each requires its own immutable protocol artifact (see below).

---

## Survival Funnel (Gate A)

```
Candidates generated
        ↓
Novelty-negative (not recoverable from inputs)
        ↓
Retrieval-negative (not found by adversarial retrieval)
        ↓
Adversarial survivors (pass unchanged gate)
        ↓
Falsifiable predictions produced
        ↓
Prediction locked (timestamp + hash)
        ↓
Gate A survivor
```

**Gate A stops here.** No candidate is called "discovery." No victory is declared.

The **prediction lock** is the boundary between Gate A and Gate B. Gate A measures generation/discrimination. Gate B measures confirmation.

---

## Gate B — Discovery Validation

Gate B runs ONLY on Gate A survivors.

```
Gate A survivor
      ↓
Independent experiment (designed by confirmation party)
      ↓
Confirmation (prediction tested)
      ↓
Replication (result must replicate)
      ↓
Tier progression: HYPOTHESIZED → PREDICTED → EXPERIMENTALLY_SUPPORTED → REPLICATED → ESTABLISHED
```

**Only ESTABLISHED candidates count toward the North Star.**

### Final Metric

> **Tier-0 → Tier-3 conversion rate of TEE versus the strongest control.**

---

## Information Boundaries (Per CTO Critique #3)

| Party | Knows source pair? | Knows answer? | Knows benchmark structure? |
|-------|-------------------|---------------|---------------------------|
| TEE | Yes (receives docs) | No | No |
| Frontier LLM | Yes (receives docs) | No | No |
| Retrieval | Yes (indexes docs) | No | No |
| Expert | Yes (receives docs) | No | No |
| Evaluator | Yes | Ideally no | Yes |
| Confirmation party | Eventually | Yes, only after prediction lock | No |
| Benchmark constructor | Yes | Yes | Yes — but CANNOT subsequently adjudicate |

**Critical:** The people constructing the benchmark cannot subsequently adjudicate it. Custodian separation is enforced.

---

## Custodian Separation (Per CTO Critique #4)

```
Problem constructor (creates cases + ground truth)
        ↓
Sealed benchmark (SHA-256 locked, no downstream access to answers)
        ↓
Independent evaluator (runs Gate A, no answer access)
        ↓
Confirmation party (Gate B only, answer access only after prediction lock)
```

### Generator Must NEVER See (Before Prediction Lock)
- Gold labels
- Expected mechanism
- Expected direction
- Falsifier
- Answer-derived synonyms
- Benchmark-specific terminology

This addresses the historical leakage event documented in the audit history (synonym table derived from answer-key material).

---

## C2 Specification (Frontier LLM — Per CTO Critiques #1, #5)

### Status: NOT YET FROZEN

C2 must be independently frozen with the following immutable parameters:

| Parameter | Value | Status |
|-----------|-------|--------|
| Model identifier | TBD (must be a frontier-class LLM) | NOT FROZEN |
| Provider | TBD | NOT FROZEN |
| System prompt | TBD (must be frozen verbatim) | NOT FROZEN |
| User prompt | TBD (must be frozen verbatim) | NOT FROZEN |
| Temperature | TBD | NOT FROZEN |
| Sampling parameters | TBD (top_p, top_k, etc.) | NOT FROZEN |
| Context window | TBD | NOT FROZEN |
| Maximum output tokens | TBD | NOT FROZEN |
| Retry policy | TBD | NOT FROZEN |
| Tool availability | NONE (no tools, no function calling) | PRELIMINARY |
| Retrieval availability | NONE (no web search, no RAG) | PRELIMINARY |
| Knowledge cutoff treatment | TBD (frozen cutoff date, no live access) | NOT FROZEN |
| Input serialization | TBD (exact JSON/text format) | NOT FROZEN |

### C2 Question (Product-Level Test)

> **Can the entire TEE system outperform a strong model given the same raw external evidence, despite TEE's additional machinery?**

C2 receives ONLY:
- Source document A
- Source document B
- The candidate prompt (same prompt TEE's final stage uses)

C2 does NOT receive:
- Mechanism graphs
- Ontology
- Adversarial analysis
- Retrieval results
- Novelty firewall output
- Historical patterns

This is intentionally a **product-level test**, not a controlled ablation. The question is whether TEE's machinery adds end-to-end value, not whether each component contributes.

---

## Retrieval Specification (Per CTO Critique #6)

### Status: NOT YET FROZEN

The retrieval baseline must be **genuinely adversarial**. "Retrieval baseline" cannot mean BM25 over the same corpus.

### Required Retrieval Components

| Component | Description | Status |
|-----------|-------------|--------|
| Lexical retrieval | BM25 or TF-IDF with frozen config | NOT FROZEN |
| Embedding retrieval | Dense vector retrieval with frozen model | NOT FROZEN |
| Cross-source query formulation | Queries designed to find cross-domain connections | NOT FROZEN |
| Entity-expanded queries | Query expansion using entity recognition | NOT FROZEN |
| Relation-oriented queries | Queries targeting relational structure | NOT FROZEN |
| Broad external literature search | Where permitted, search external corpus | NOT FROZEN |
| Fixed retrieval budget | Maximum queries / documents per case | NOT FROZEN |
| Frozen ranking configuration | No tuning after seeing results | NOT FROZEN |

### Retrieval Success Criterion

A candidate is "retrieval-negative" only if NONE of the retrieval components can produce it (or a sufficiently similar variant) within the fixed budget.

---

## Expert Specification (Per CTO Critique #7)

### Status: NOT YET FROZEN

| Parameter | Value | Status |
|-----------|-------|--------|
| Expert qualifications | TBD (domain expertise requirements) | NOT FROZEN |
| Number of experts | TBD (minimum 3 for inter-rater reliability) | NOT FROZEN |
| Time limit | TBD (per case) | NOT FROZEN |
| Internet access | PROHIBITED | PRELIMINARY |
| External literature access | PROHIBITED | PRELIMINARY |
| Calculator/code access | TBD | NOT FROZEN |
| Collaboration | TBD (likely prohibited) | NOT FROZEN |
| Scoring rubric | TBD (must be frozen) | NOT FROZEN |
| Blinding | Blind to which system produced which output | PRELIMINARY |
| Compensation/incentives | TBD | NOT FROZEN |

---

## Matched Null Controls (Per CTO Critique #10)

The auditor's hardest requirement:

> **If the false-positive rate on matched-null/shuffled controls cannot be driven below the true-positive rate, the discovery measurement is uninterpretable.**

### Four Null Conditions

| Null | Description | Infrastructure |
|------|-------------|----------------|
| **Null 1 — Random hypothesis** | Randomly generated hypothesis from generic vocabulary | NEW |
| **Null 2 — Shuffled mechanism graph** | Real mechanism graph with edges/nodes shuffled | `create_null_mechanism_graph()` (exists, must verify) |
| **Null 3 — Retrieval-only** | Arm 4 (retrieval baseline) | See Retrieval Spec |
| **Null 4 — Frontier LLM** | Arm 5 (frontier LLM baseline) | See C2 Spec |

### Survival Funnel Comparison

The **entire survival funnel** is measured for each arm, not merely final accuracy:

```
                    TEE    Null1   Null2   Null3   Null4   Expert
Candidates gen     ?       ?       ?       ?       ?       ?
Novelty-neg        ?       ?       ?       ?       ?       ?
Retrieval-neg      ?       ?       ?       ?       ?       ?
Adversarial surv   ?       ?       ?       ?       ?       ?
Falsifiable pred   ?       ?       ?       ?       ?       ?
Gate A survivors   ?       ?       ?       ?       ?       ?
```

**Interpretability requirement:** If Null 1-4 survival rates are not below TEE's survival rate, the measurement is uninterpretable.

---

## DXP-005 Classification (Per CTO Critique #2)

### DXP-005 is a PILOT, not the definitive North Star trial.

| Property | DXP-005 | North Star Trial |
|----------|---------|------------------|
| Case count | 10 (5P + 5N) | N≥30 |
| Domain coverage | Limited | Multiple unrelated domains |
| Selection | Internally constructed | Unpredictable selection |
| Risk | Case-selection effects, ontology familiarity, source-pair bias | Minimized |
| Statistical power | Low | Adequate |

**DXP-005 = "Discovery-generation mechanism pilot / Gate-A evidence"**

The definitive North Star trial requires a separately constructed, custodian-sealed benchmark of N≥30 problems across multiple unrelated domains with unpredictable selection.

---

## Gate A / Gate B Boundary (Per CTO Critique #8)

### Gate A (Generation/Discrimination)

```
Inputs → candidate → novelty → control comparison → Tier-0 decision
```

Gate A measures: Can TEE generate non-recoverable candidates that survive adversarial scrutiny?

### LOCK (Boundary)

```
candidate + prediction + timestamp + hash
```

The prediction lock is the **boundary**, not part of Gate A or Gate B. It is the handoff.

### Gate B (Confirmation)

```
falsifiable prediction → independent experiment → confirmation → replication
```

Gate B measures: Does the prediction survive independent testing?

---

## Architecture Preservation (Per CTO Critique #9)

### Do NOT weaken the existing architecture.

The repository has invested heavily in:
- Fail-closed behavior
- Provenance (cryptographic manifests, immutable ledger)
- Falsifiers required for testable hypotheses
- Adversarial gate as a real gate (not rubber stamp)
- Epistemic state enforcement (HYPOTHESIZED → ESTABLISHED requires evidence)

**The adversarial gate must remain a real gate.** An earlier real-LLM run generated hypotheses that all failed adversarial analysis, and the repaired engine correctly prevented them from advancing. That is exactly the behavior we want.

### What Must NOT Change
- The adversarial gate (`engine/adversarial_analysis.py`) — UNCHANGED
- The epistemic state enforcer (`engine/epistemic_state_enforcer.py`) — UNCHANGED
- The provenance/ledger system — UNCHANGED
- The falsifier requirement — UNCHANGED
- The fail-closed behavior — UNCHANGED

---

## Execution Authorization

### DXP-005: HOLD

DXP-005 execution remains on HOLD. The 30-run A/B/C ablation is NOT authorized until:
1. This measurement boundary (NORTH_STAR_GATE_A_V1) is frozen
2. C2 (frontier LLM) is independently frozen
3. Retrieval baseline is independently frozen
4. Expert protocol is independently frozen
5. Null 1 (random hypothesis) is implemented and frozen
6. Custodian separation is enforced

### What IS Authorized
- Freezing this document (the measurement boundary)
- Independently freezing C2, retrieval, expert, and null specifications
- Preparing the 6-arm infrastructure

### What is NOT Authorized
- Executing DXP-005's 30-run A/B/C ablation
- Declaring any victory from DXP-005 results
- Calling DXP-005 results "discovery"
- Weakening the adversarial gate
- Modifying the frozen detector or engine architecture

---

## Status Summary

| Component | Status |
|-----------|--------|
| Gate A / Gate B separation | FROZEN |
| Survival funnel definition | FROZEN |
| Information boundaries | FROZEN |
| Custodian separation | FROZEN |
| DXP-005 classification (pilot) | FROZEN |
| Architecture preservation | FROZEN |
| 6-arm structure | FROZEN |
| Arm 1 (TEE) | EXISTS (engine/) |
| Arm 2 (TEE mechanism-null) | EXISTS (generation_null.py) |
| Arm 3 (Random/null generator) | EXISTS (generate_null_candidates) |
| Arm 4 (Retrieval) | NOT FROZEN — requires independent spec |
| Arm 5 (Frontier LLM) | NOT FROZEN — requires independent spec |
| Arm 6 (Expert) | NOT FROZEN — requires independent spec |
| Null 1 (random hypothesis) | NOT IMPLEMENTED |
| Definitive North Star benchmark (N≥30) | NOT CONSTRUCTED |

**Next artifacts to freeze:**
1. C2_SPECIFICATION.md (frontier LLM)
2. RETRIEVAL_SPECIFICATION.md (adversarial retrieval)
3. EXPERT_SPECIFICATION.md (expert protocol)
4. NULL_1_SPECIFICATION.md (random hypothesis generator)

Only after all four are frozen can Gate A execution proceed.

**Ad astra.**
