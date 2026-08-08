# Detailed B1/B2 Preregistration Design

**Status:** DESIGN DOCUMENT — not implementation, not authorized for execution
**Date:** 2026-08-09
**Prior documents:** PROTOCOL_B_REDESIGN_MEMORANDUM.md, PROTOCOL_B_ADVERSARIAL_AUDIT.md, PROTOCOL_VALIDITY_AUDIT.md

---

## Hard Separation: Engineering Readiness ≠ Scientific Authorization

```
B1 design complete        ≠ B1 authorized
B1 result positive        ≠ B2 authorized
B2 generated candidate    ≠ discovery
B2 candidate passes Gate A ≠ scientifically valid
B2 candidate passes Gate C ≠ novel
Novel + valid candidate   ≠ general discovery capability
```

---

# PART 1: B1 — Controlled Rediscovery

## 1.1 Central Question

> **Can the system reconstruct a known cross-domain relationship from source material without being given the relationship itself?**

## 1.2 Source-Pair Construction

### What the engine receives
For each gold discovery:
- **Domain A source:** `source_snippet_a` — scientific text describing a mechanism from domain A
- **Domain B source:** `source_snippet_b` — scientific text from domain B

### What is hidden from the engine
- `bridge` — the gold bridge concept
- `published_relation` — the known relationship
- `expected_in_graph` — whether the bridge should appear in the graph
- `verification` — the verification status
- `id` — the gold discovery identifier
- Any metadata about the expected answer

### Anti-leakage controls (layered, NOT gold-derived)

1. **Exact string check:** The bridge word must NOT appear verbatim in either source snippet. (Already enforced by F-099 hard gate.)

2. **Normalized string check:** Canonicalized bridge must not appear as a substring of canonicalized source text.

3. **Token/subsequence overlap check:** No token of the bridge (≥4 chars) should appear in the source snippets unless the token is a common English word. This check uses a FIXED stopword list (not gold-derived).

4. **Independent lexical check:** An evaluator independently inspects each source pair and judges whether the bridge concept is "obviously implied" by the source text. This is done BEFORE the engine runs, by an evaluator who does NOT know the engine's output.

5. **Human blind leakage adjudication:** For borderline cases (where the independent lexical check is uncertain), a second evaluator reviews. If both evaluators agree the bridge is "too obvious" in the source, the case is flagged as LEAKAGE_RISK and excluded BEFORE execution. Exclusion happens before the engine runs, not after.

### Leakage exclusion is preregistered
Cases excluded for leakage risk are recorded with:
- Case ID
- Reason for exclusion
- Evaluator identities
- Date of exclusion

Excluded cases are NOT replaced. If N drops below a minimum, the experiment reports INSUFFICIENT_CLEAN_CASES.

## 1.3 Candidate-Generation Pipeline

### What pipeline is used
The engine's full discovery pipeline:
```
Source A → MechanismExtractionEngine → MechanismAbstractionEngine
Source B → MechanismExtractionEngine → MechanismAbstractionEngine
    ↓
CrossDomainTransferEngine.generate()
    ↓
HypothesisGenerationEngine.generate()
    ↓
Candidate mechanism (relationship + proposed mechanism)
```

### What the pipeline must NOT receive
- The gold bridge
- Any gold metadata
- Results from previous cases
- Cached outputs from gold-set processing

### Provider specification
- Provider: ZAI (glm-4-plus via z-ai CLI) — the preregistered provider
- If ZAI is unavailable: B1 is BLOCKED (no provider substitution)
- P46 served-instrument verification required (model AND provider in response)

## 1.4 Case-Level Isolation

Each case is processed as a completely independent episode:

| Requirement | Specification |
|---|---|
| Provider session | New session per case (no conversation context) |
| Cache | Cleared between cases |
| Temporary files | Deleted between cases |
| Retrieval state | No cross-case retrieval |
| Checkpoints | Not shared between cases |
| Intermediate artifacts | Not visible to subsequent cases |
| Random seed | Fixed per case (seed = case_index, preregistered) |
| Model version | Same for all cases (recorded) |
| Prompt version | Same for all cases (frozen, recorded) |
| System prompt | Same for all cases (frozen, recorded) |
| Temperature | 0.0 (deterministic) for all LLM calls |
| Tool state | No tools carried between cases |

## 1.5 What Constitutes a Recoverable Relationship

### Predeclared rubric (NOT string matching)

A candidate "recovers" the gold relationship if ALL of the following are true:

1. **Generation:** The system generated a candidate (did not produce empty output)
2. **Gate A PASS:** The candidate is NOT recoverable from either input alone via extraction, entity intersection, paraphrase, or obvious composition (classified A4 by independent evaluator)
3. **Semantic match:** An independent evaluator determines that the candidate captures the SAME cross-domain mechanism as the gold bridge — NOT by string matching, but by semantic/mechanistic assessment

### Semantic match rubric (predeclared)

The evaluator assesses:
- Does the candidate propose the same causal mechanism as the gold bridge?
- Does the candidate connect the same domains?
- Is the candidate's proposed relationship functionally equivalent to the gold relationship?

Options:
- EXACT_MATCH — candidate captures the identical mechanism
- FUNCTIONAL_EQUIVALENT — candidate captures a different formulation of the same mechanism
- PARTIAL_MATCH — candidate captures part of the mechanism but misses key elements
- NO_MATCH — candidate does not capture the gold mechanism

EXACT_MATCH and FUNCTIONAL_EQUIVALENT count as "recovered."
PARTIAL_MATCH and NO_MATCH count as "not recovered."

### Treatment of partial discoveries
PARTIAL_MATCH is recorded separately. It is NOT counted as a true positive, but it is reported as a secondary endpoint.

### Treatment of valid-but-differently-worded discoveries
FUNCTIONAL_EQUIVALENT explicitly covers this. The evaluator is instructed that differently-worded formulations of the same mechanism count as recovery.

## 1.6 Gate A/B/C Adjudication Procedure

### Gate A — Non-triviality (adjudicator-blinded)

**Question:** Is the candidate recoverable from the inputs through extraction, entity intersection, paraphrase, or obvious composition?

**Adjudicator sees:**
- The candidate (proposed relationship + mechanism)
- Both source texts
- The Gate A rubric (A0–A4)

**Adjudicator does NOT see:**
- The gold bridge
- Which system generated the candidate
- Whether this is a true or null case
- The system's confidence score

**Classification:**
- A0 — Explicit: stated verbatim in either input
- A1 — Lexical/paraphrase: recoverable via synonym, substring, paraphrase
- A2 — Entity/relation extraction: directly extractable entity or relation
- A3 — Direct compositional inference: obvious composition of explicit relationships
- A4 — Non-trivial derived proposal: cannot be recovered by any above method

Only A4 passes Gate A.

### Gate B — Prior-art / Novelty (for B1, reported but not required)

**Question:** Has this relationship been previously published?

For B1, the gold relationships ARE previously published (they are known discoveries). So Gate B will return PRIOR_ART_FOUND for all B1 true cases. This is expected and documented.

Gate B is REPORTED for B1 but is NOT a pass/fail criterion. B1 tests recovery, not novelty.

### Gate C — Scientific validity

**Question:** Is the proposed mechanism scientifically coherent, plausible, non-trivial, supported by the evidence, and testable?

**Adjudicator sees:**
- The candidate (proposed relationship + mechanism)
- Both source texts
- The prior-art search result

**Adjudicator does NOT see:**
- The gold bridge
- Which system generated the candidate
- Whether this is a true or null case
- The system's confidence score
- Whether the candidate was generated by AI

**Adjudicator CAN reject the premise:** "This isn't even a meaningful mechanism" is a valid Gate C FAIL. The adjudicator is explicitly instructed that rubber-stamping is prohibited.

**Minimum: 2 independent adjudicators per candidate.**
- If they agree: record the agreement
- If they disagree: third adjudicator recruited
- If all three disagree: AMBIGUOUS (recorded, not counted as PASS)

**Inter-rater reliability:** Cohen's kappa calculated where sample size permits.

## 1.7 Primary and Secondary Endpoints

### Primary endpoint
```
Recovery rate = (candidates that pass Gate A AND semantic-match as EXACT or FUNCTIONAL_EQUIVALENT) / (total cases)
```

### Secondary endpoints (reported separately)
- Gate A pass rate (fraction of candidates classified A4)
- Gate C pass rate (fraction of candidates rated scientifically valid)
- Partial match rate (fraction classified PARTIAL_MATCH)
- Generation rate (fraction of cases where the system produced any candidate)
- Null false-positive rate (fraction of null cases producing a candidate that passes Gate A)

### Why B1's primary endpoint does NOT require Gate B
B1 tests controlled rediscovery. The gold relationships are known. Gate B will return PRIOR_ART_FOUND. Requiring Gate B PASS for B1 would make the experiment impossible by design.

## 1.8 Null/Control Construction

### Matched null
For each gold case, create a null by:
1. Using the SAME source texts (domain A + domain B)
2. But asking the engine to generate a mechanism for a DIFFERENT domain pair (borrowed from another case)
3. Or: using source texts from an unrelated domain pair where NO known bridge exists

### Control arms (mandatory per Amendment 10)
- **Control A — Machine:** the engine itself (B1 test arm)
- **Control B — Generic LLM:** zero-shot LLM with same source texts
- **Control C — Retrieval only:** entity intersection only (no mechanism generation)
- **Control D — Human:** qualified researcher, same source texts, 30 minutes
- **Control E — Matched null:** structurally plausible but causally meaningless proposals

### Control equivalence (preregistered)
| Parameter | Engine | Generic LLM | Retrieval | Human | Matched null |
|---|---|---|---|---|---|
| Input | Same A+B | Same A+B | Same A+B | Same A+B | Same A+B |
| System | Engine pipeline | Prespecified LLM | Entity extraction | Researcher | Recombination |
| Prompt | N/A | Preregistered | N/A | Preregistered | N/A |
| Temperature | 0.0 | 0.0 | N/A | N/A | N/A |
| Attempts | 1 | 1 | 1 | 1 | 1 |
| Time limit | N/A | N/A | N/A | 30 min | N/A |
| External search | No | No | No | No | No |
| Retry | No | No | No | No | No |

## 1.9 Sample Size and Power

### N = 20 true cases + 20 null cases = 40 total per arm

### Power rationale (honest)
With N=20 and a recovery rate threshold:
- If true recovery rate = 0.50, P(≥ 8/20 recover) = 0.25 — INADEQUATE
- If true recovery rate = 0.70, P(≥ 8/20 recover) = 0.77 — MARGINAL
- If true recovery rate = 0.80, P(≥ 8/20 recover) = 0.97 — ADEQUATE

**Classification:** N=20 is exploratory. A positive result justifies expansion (Stage 2B). A negative result does NOT prove inability — it means the experiment was insufficient to establish the capability.

### Minimum for pilot
≥ 3 recoveries (Gate A PASS + semantic match) out of 20 to justify Stage 2B expansion.

## 1.10 Decision Partition (Exhaustive)

```
IF leakage_check == FAILED:
    INCONCLUSIVE_LEAKAGE

ELSE IF N_clean < 10:
    INSUFFICIENT_CLEAN_CASES

ELSE IF null_validity == FAILED:
    INCONCLUSIVE_INVALID_NULL

ELSE IF recovery_rate ≥ 0.40 AND null_FP_rate ≤ 0.20:
    REDISCOVERY_CAPABILITY_ESTABLISHED (pilot)

ELSE:
    REDISCOVERY_NOT_ESTABLISHED
```

Every outcome maps to exactly one state. No ambiguity.

### What each state means
- **INCONCLUSIVE_LEAKAGE:** Source materials contained too much information about the gold answer. Redesign needed.
- **INSUFFICIENT_CLEAN_CASES:** Too many cases excluded for leakage. Need better source materials.
- **INCONCLUSIVE_INVALID_NULL:** Null construction failed quality audit.
- **REDISCOVERY_CAPABILITY_ESTABLISHED:** The engine can recover known mechanisms. B2 may be designed.
- **REDISCOVERY_NOT_ESTABLISHED:** The engine cannot recover known mechanisms. B2 is premature.

### REDISCOVERY_NOT_ESTABLISHED handling
- Result preserved
- No rescue, no threshold change, no case removal
- B2 is NOT authorized
- The measurement pipeline needs investigation, not the experiment

## 1.11 Stopping Rule
Run to completion. No early stopping.

---

# PART 2: B2 — Open Discovery

## 2.1 Central Question

> **Does the engine produce a scientifically valid, non-trivial cross-domain mechanism that survives blind adjudication and prior-art examination?**

## 2.2 Source-Pair Construction

### What the engine receives
- Domain A source: scientific text describing a mechanism from domain A
- Domain B source: scientific text from a different domain

### What is NOT assumed
- No gold bridge
- No predefined "correct answer"
- No assumption that a valid cross-domain mechanism exists for this pair

### Source-pair selection
- Pairs selected by an independent party (not the engine builders)
- Pairs committed and SHA-recorded before engine runs
- Pairs from domains where cross-domain connections are plausible but not obvious
- Pairs are NOT derived from the existing gold set

## 2.3 Candidate-Generation Pipeline
Same as B1 (Section 1.3). Same isolation requirements (Section 1.4).

## 2.4 Adjudication (Blind, Independent)

### What each candidate is evaluated on (SEPARATE endpoints)

| # | Dimension | Question | Procedure |
|---|---|---|---|
| 1 | Generated | Did the system produce a candidate? | Binary (yes/no) |
| 2 | Cross-domain | Does it genuinely connect the two designated domains? | Evaluator judgment |
| 3 | Non-trivial (Gate A) | Does it require synthesis beyond direct extraction? | A0–A4 rubric |
| 4 | Scientific validity (Gate C) | Is the mechanism coherent, plausible, testable? | Expert adjudication |
| 5 | Prior-art result (Gate B) | Has it been published before? | Literature search |
| 6 | Novelty (Gate B) | Is it genuinely new as of cutoff date? | NOVEL_AS_OF_CUTOFF / PRIOR_ART_FOUND |

### Each dimension is measured and reported SEPARATELY

A candidate can be:
- Generated + cross-domain + A4 + C=PASS + B=PRIOR_ART_FOUND → valid rediscovery
- Generated + cross-domain + A4 + C=PASS + B=NOVEL → **North Star candidate**
- Generated + cross-domain + A4 + C=FAIL + B=NOVEL → novel but invalid
- Generated + cross-domain + A0 + C=PASS + B=NOVEL → trivial (extractable from inputs)

### Blinding requirements

**Adjudicators do NOT see:**
- Which system generated the candidate (engine vs LLM vs human vs null)
- Whether a gold answer exists
- The system's confidence score
- Whether the candidate was AI-generated

**Adjudicators DO see:**
- The candidate (proposed relationship + mechanism)
- Both source texts
- The adjudication rubric

**Adjudicators CAN:**
- Reject the premise ("this isn't even a meaningful mechanism")
- Request clarification from the experiment coordinator (not the engine builders)
- Flag candidates for third-adjudicator review

### Adjudicator calibration
- Calibrated on NON-STUDY cases before seeing study cases
- Calibration cases are from different domains
- Calibration results recorded but NOT used to adjust study results
- Inter-rater reliability (Cohen's kappa) calculated on calibration cases

### Prior-art search protocol (preregistered)
- Databases: Google Scholar, PubMed, arXiv, Semantic Scholar
- Search terms: derived from the candidate mechanism (NOT from the gold set — there is no gold set in B2)
- Date cutoff: preregistered before execution
- Screening: top 20 results per database
- Full-text review: top 5 results
- Adjudicator identity: recorded
- Final determination: NOVEL_AS_OF_CUTOFF / PRIOR_ART_FOUND / PARTIAL_PRECEDENT / AMBIGUOUS

## 2.5 Primary Outcome

```
North Star yield = (cases producing ≥1 candidate that is
    Generated AND
    Cross-domain AND
    Gate A = A4 AND
    Gate C = PASS AND
    Gate B = NOVEL_AS_OF_CUTOFF
) / (total eligible cases)
```

## 2.6 Secondary Outcomes (reported separately)
- Generation rate (fraction producing any candidate)
- Gate A pass rate
- Gate C pass rate
- Gate B novelty rate
- Rediscovery rate (valid + prior art found)
- Engine yield vs. generic-LLM yield
- Engine yield vs. retrieval yield
- Engine yield vs. matched-null yield
- Engine yield vs. human yield

## 2.7 Statistical Framework

### Primary comparison
Engine North Star yield vs. matched-null yield.

### Test
Fisher's exact test (one-sided), α = 0.05.

### Secondary comparisons (exploratory)
- Engine vs. generic LLM
- Engine vs. retrieval
- Engine vs. human

### Confidence intervals
- Individual yields: exact Clopper-Pearson 95% CI
- Difference in yields: Newcombe hybrid Wilson 95% CI

## 2.8 Sample Size
N ≥ 20 prospective cases (per system: engine + 4 controls = 100 total evaluations).

### Interpretation
N=20 is a minimum prospective pilot. A positive result justifies Stage 2B expansion (N ≥ 50, new cases, new domains, new evaluators). A negative result does NOT prove inability — it means the pilot was insufficient.

## 2.9 Decision Partition (Exhaustive)

```
IF null_validity == FAILED:
    INCONCLUSIVE_INVALID_NULL

ELSE IF north_star_yield == 0:
    NORTH_STAR_NOT_ACHIEVED

ELSE IF north_star_yield > 0 AND engine_yield > null_yield (Fisher, α=0.05):
    NORTH_STAR_SIGNAL_DETECTED (pilot — requires Stage 2B replication)

ELSE:
    NORTH_STAR_NOT_ACHIEVED
```

### NORTH_STAR_NOT_ACHIEVED handling
- Result preserved
- No rescue
- No threshold change
- No case removal
- The result is the result

### NORTH_STAR_SIGNAL_DETECTED handling
- Does NOT establish general discovery capability
- Justifies Stage 2B expansion
- Stage 2B is a NEW experiment with new cases, new domains, new evaluators
- Stage 2B must independently confirm before any discovery claim

## 2.10 Stopping Rule
Run to completion. No early stopping.

---

# PART 3: Adjudicator Anti-Bias Measures

## 3.1 Blinding
- Adjudicators do not know which arm generated each candidate
- Candidates are presented in randomized order
- No arm labels, confidence scores, or system identifiers visible

## 3.2 Independence
- Minimum 2 adjudicators per candidate
- Adjudicators work independently (no discussion before scoring)
- Disagreement → third adjudicator
- All three disagree → AMBIGUOUS (recorded, not counted as PASS)

## 3.3 Calibration
- Calibration performed on non-study cases
- Calibration cases from different domains
- Calibration results recorded but NOT used to adjust study results
- Inter-rater reliability (Cohen's kappa) calculated on calibration cases
- If kappa < 0.40: adjudication procedure needs revision before study execution

## 3.4 Premise rejection
- Adjudicators are explicitly instructed: "You may reject the premise of a proposed mechanism. 'This isn't even a meaningful mechanism' is a valid Gate C FAIL."
- Rubber-stamping is prohibited
- Adjudicators must document WHY a mechanism passes or fails

## 3.5 What adjudicators see and don't see

| Information | Visible to adjudicator? |
|---|---|
| Candidate (relationship + mechanism) | YES |
| Source text A | YES |
| Source text B | YES |
| Gate A rubric | YES |
| Gate C rubric | YES |
| Prior-art search result (for Gate C) | YES |
| Gold bridge (B1 only) | NO |
| Which system generated the candidate | NO |
| Whether candidate is from true or null case | NO |
| System confidence score | NO |
| Whether candidate was AI-generated | NO |
| Other adjudicators' scores | NO (until after their own scoring) |

---

# PART 4: What This Design Does NOT Authorize

- Implementing any protocol
- Executing any protocol
- Modifying the frozen matcher, gold set, Gate 2 protocol, M-008, DXP-005, or production pipeline
- Constructing gold-derived leakage dictionaries
- Selecting adjudicators
- Selecting source pairs
- Making any discovery or capability claim

---

# Status

```
Protocol A: DRAFT — accepted as narrow prerequisite
Protocol B1: DESIGN COMPLETE — requires adversarial review before freezing
Protocol B2: DESIGN COMPLETE — requires adversarial review before freezing
Phase 8 execution: BLOCKED
M-008: FULL_QUARANTINE
North Star: NOT ACHIEVED
```
