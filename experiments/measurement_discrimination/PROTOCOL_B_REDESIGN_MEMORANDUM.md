# Protocol B Redesign Memorandum

**Date:** 2026-08-09
**Author:** Repository coder
**Status:** EXPERIMENTAL DESIGN — not code, not execution

---

## Purpose

Per CEO directive (audit round 28): separate five conceptual dimensions before any implementation.

1. Controlled rediscovery vs genuine discovery
2. Candidate generation vs candidate recognition
3. Mechanism validity vs historical novelty
4. Lexical scoring vs scientific adjudication
5. Gold-set evaluation vs open-ended evaluation

---

## 1. Controlled Rediscovery (B1) vs Genuine Discovery (B2)

### The distinction

**B1 — Controlled Rediscovery:** The engine receives source material from two domains where a known cross-domain relationship exists. The engine must recover (rediscover) that relationship without being told what it is. The gold answer exists but is hidden from the generator.

**B2 — Open Discovery:** The engine receives source material from two domains. No predefined "correct answer" is assumed. The engine generates candidate mechanisms. Independent adjudication determines whether any candidate is scientifically valid, non-trivial, and novel.

### Why they require different designs

| Dimension | B1 (Rediscovery) | B2 (Open Discovery) |
|---|---|---|
| Gold answer | Exists (hidden from generator) | Does not exist |
| Scoring | Candidate compared to known answer | Candidate evaluated on its own scientific merits |
| True positive | Candidate matches/recovers known relationship | Candidate survives blind adjudication |
| False positive | Candidate does NOT match known relationship | N/A — no "wrong" answer, only "invalid" candidates |
| Statistical framework | TPR/FPR against gold labels | Yield rate (fraction of cases producing valid candidates) |
| What it measures | Can the engine recover known mechanisms? | Can the engine generate valid novel mechanisms? |
| Bias | Structurally biased toward rediscovery, not invention | No gold-match bias |
| North Star relevance | Necessary precondition | The actual North Star test |

### B1 is experimentally tractable; B2 is harder

B1 has a clear binary outcome per case: did the engine recover the known bridge/mechanism? This allows TPR/FPR analysis with matched nulls.

B2 has no binary outcome per case. The engine might produce 0, 1, or multiple candidates. Each candidate must be independently adjudicated. The statistical framework is yield-based (what fraction of source pairs produce at least one adjudicated-valid candidate?), not TPR/FPR.

### Both are needed

B1 tests whether the engine's pipeline can recover known cross-domain mechanisms. If B1 fails, the pipeline is broken and B2 is premature.

B2 tests whether the engine can generate genuinely novel, valid mechanisms. This is the North Star.

```
Protocol A (lexical selectivity gate)
    ↓ PASS
Protocol B1 (controlled rediscovery)
    ↓ PASS (engine can recover known mechanisms)
Protocol B2 (open discovery)
    ↓ This is the North Star experiment
```

---

## 2. Candidate Generation vs Candidate Recognition

### The distinction

**Candidate generation:** The process by which the engine produces a proposed cross-domain mechanism from source material. This is the engine's job.

**Candidate recognition:** The process by which a generated candidate is evaluated for correctness, validity, or novelty. This is the adjudicator's job.

### Why they must be separated

If the same system both generates and evaluates candidates, the evaluation is not independent. The engine could generate a plausible-sounding but incorrect mechanism and then "recognize" it as correct.

### Required architecture

```
SOURCE MATERIAL (domain A + domain B)
        ↓
CANDIDATE GENERATION (engine pipeline)
        ↓
CANDIDATE (proposed mechanism)
        ↓
    ┌────┴────┐
    ↓         ↓
B1: Gold     B2: Blind
comparison   adjudication
(hidden)     (no gold)
```

For B1: the candidate is compared to the hidden gold answer using a predeclared matching procedure. The matching procedure must NOT be `_bridge_matches()` (string matching). It must be a Gate-A-style adjudication: "Is this candidate recoverable from the inputs, or does it require cross-domain synthesis?"

For B2: the candidate is evaluated by independent adjudicators who do NOT know which system generated it, whether a gold answer exists, or what the expected outcome is.

### What candidate generation must NOT do

- Receive the gold bridge as input (B1)
- Receive any metadata about the expected answer (B1)
- Receive information from previous cases (independence)
- Use cached results from gold-set processing
- Use vocabulary derived from the gold set

---

## 3. Mechanism Validity vs Historical Novelty

### The distinction

**Mechanism validity (Gate C):** Is the proposed mechanism scientifically coherent, plausible, non-trivial, supported by evidence, and testable? This is a scientific quality question.

**Historical novelty (Gate B):** Has this relationship been previously published? This is a literature-search question.

### Why they must remain separate endpoints

A candidate can be:

| Gate A (non-trivial) | Gate B (novel) | Gate C (valid) | Classification |
|---|---|---|---|
| PASS | PASS | PASS | Validated novel discovery (North Star) |
| PASS | FAIL | PASS | Validated rediscovery (scientifically valid, previously known) |
| PASS | PASS | FAIL | Novel but invalid (sounds new but is wrong) |
| PASS | FAIL | FAIL | Previously known and invalid |
| FAIL | — | — | Trivial / recoverable from inputs |

### The North Star requires A + B + C, but each should be measured separately

The primary endpoint for B1 should be **Gate A + Gate C** (non-trivial + valid). Historical novelty (Gate B) is not expected in B1 because B1 uses known relationships — they are rediscoveries by definition.

The primary endpoint for B2 should be **Gate A + Gate B + Gate C** (non-trivial + novel + valid). This is the North Star.

But all three gates should be measured and reported separately for every candidate, in both B1 and B2.

---

## 4. Lexical Scoring vs Scientific Adjudication

### The distinction

**Lexical scoring:** `_bridge_matches(expected_bridge, candidate)` — string matching between two strings. Fast, deterministic, but cannot evaluate scientific meaning.

**Scientific adjudication:** Gate A/B/C evaluation — independent assessment of non-triviality, novelty, and scientific validity. Slow, requires human experts, but measures the actual scientific property.

### Why `_bridge_matches()` is insufficient for Protocol B

The Protocol B adversarial audit (defect B-3) established that `_bridge_matches()` receives only two strings and cannot judge whether a candidate represents a genuine cross-domain relationship. Using it as the scorer recreates the Protocol A defect.

### What Protocol B should use instead

For B1 (controlled rediscovery):
- Gate A adjudication: "Is the candidate recoverable from the inputs, or does it require cross-domain synthesis?"
- Gate C adjudication: "Is the proposed mechanism scientifically valid?"
- The candidate is NOT compared to the gold bridge by string matching
- Instead, an evaluator determines whether the candidate captures the SAME mechanism as the gold bridge (semantic match, predeclared rubric)

For B2 (open discovery):
- Gate A adjudication: non-triviality
- Gate B adjudication: prior-art search
- Gate C adjudication: scientific validity
- No gold comparison at all

### What `_bridge_matches()` CAN still be used for

Protocol A (lexical selectivity gate) — its original purpose. It tests whether the matcher has lexical selectivity. It does NOT test discovery.

---

## 5. Gold-Set Evaluation vs Open-Ended Evaluation

### The distinction

**Gold-set evaluation (B1):** The engine is tested on cases where a known answer exists. The engine's output is compared to the known answer. This measures rediscovery capability.

**Open-ended evaluation (B2):** The engine is tested on cases where no known answer is assumed. The engine's output is evaluated on its own merits. This measures discovery capability.

### Why B1 alone is insufficient for the North Star

A gold-set benchmark is structurally biased toward rediscovery. If the engine produces a scientifically valid, novel mechanism that is NOT in the gold set, a gold-match benchmark calls it wrong. This penalizes genuine invention.

B1 is necessary as a precondition (can the engine recover known mechanisms?), but B2 is the actual North Star experiment (can the engine generate valid novel mechanisms?).

### B2's statistical framework

B2 has no gold labels, so TPR/FPR doesn't apply. The framework is:

```
Yield = (number of cases producing ≥1 adjudicated-valid candidate) / (total cases)
```

With controls:
- **Retrieval baseline yield:** same source pairs, retrieval-only system (entity intersection)
- **Generic LLM yield:** same source pairs, zero-shot LLM
- **Matched null yield:** structurally plausible but causally meaningless proposals

The engine must produce a yield significantly above the matched null and the retrieval baseline.

---

## Conceptual Architecture (Frozen)

```
                    PROTOCOL A
              Lexical Selectivity Gate
                       │
                       ▼
             Is the scorer sufficiently
                 selective?
                       │
                       ▼
              ┌─────────────────────┐
              │      PROTOCOL B1    │
              │ Controlled          │
              │ Rediscovery         │
              │                     │
              │ Source A + Source B │
              │       ↓             │
              │ Engine pipeline     │
              │       ↓             │
              │ Candidate mechanism │
              │       ↓             │
              │ Gate A (non-trivial)│
              │ Gate C (valid)      │
              │       ↓             │
              │ Semantic match to   │
              │ hidden gold answer  │
              └─────────┬───────────┘
                        │
                 Can the engine
                 recover known
                  mechanisms?
                        │
                        ▼
              ┌─────────────────────┐
              │      PROTOCOL B2    │
              │ Open Discovery      │
              │                     │
              │ Source A + Source B │
              │       ↓             │
              │ Engine pipeline     │
              │       ↓             │
              │ Candidate mechanism │
              │       ↓             │
              │ BLIND ADJUDICATION  │
              │ (no gold answer)    │
              │       ↓             │
              │ Gate A (non-trivial)│
              │ Gate B (novel)      │
              │ Gate C (valid)      │
              └─────────┬───────────┘
                        │
                        ▼
             NORTH STAR:
             Can the engine
             generate valid
             novel mechanisms?
```

---

## What This Memorandum Does NOT Authorize

- Implementing any protocol
- Executing any protocol
- Modifying the frozen matcher, gold set, Gate 2 protocol, M-008, DXP-005, or production pipeline
- Constructing a paraphrase/synonym leakage dictionary from the gold set
- Selecting an A/B/C "true-positive" definition (the memorandum separates the gates but does not select a primary endpoint — that requires further design)

---

## Required Next Steps (Design, Not Code)

1. **B1 design:** Specify the exact engine pipeline configuration, source-pair selection, semantic-match rubric, and statistical framework
2. **B2 design:** Specify the open-ended source-pair selection, adjudication procedure, control arms, and yield-based statistical framework
3. **Anti-leakage design:** Specify a leakage detection procedure that does NOT derive vocabulary from the gold set
4. **Independence design:** Specify the case-level isolation requirements for LLM-based generation
5. **Adjudication design:** Specify the Gate A/B/C rubric, evaluator qualifications, blinding procedure, and inter-rater reliability requirements

---

## Status

```
Protocol A: DRAFT — accepted as narrow prerequisite
Protocol B1: CONCEPTUAL — requires detailed design
Protocol B2: CONCEPTUAL — requires detailed design
Phase 8 execution: BLOCKED
M-008: FULL_QUARANTINE
North Star: NOT ACHIEVED
```
