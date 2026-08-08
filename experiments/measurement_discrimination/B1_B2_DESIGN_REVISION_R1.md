# B1/B2 Design Revision R1

**Status:** DESIGN REVISION — not implementation, not authorized for execution
**Date:** 2026-08-09
**Supersedes:** B1_B2_DETAILED_DESIGN.md (which had 12 defects per audit round 30)
**Governing rule:** Every endpoint must be computable from information that the endpoint's adjudicator is actually allowed to observe.

---

## Audit Findings Addressed

| # | Finding | Severity | Fix |
|---|---|---|---|
| 1 | B1 semantic-match adjudicator cannot see gold | FATAL | Two-stage adjudication: blind quality evaluation, then separate gold comparison |
| 2 | B1 null construction not properly matched | FATAL | Same input pair, same task, structurally matched permutation that breaks the designated correspondence |
| 3 | B2 source-pair selection bias | HIGH | Mechanical sampling frame, blind eligibility screening, preregistered random selection |
| 4 | Gate C contaminated by prior-art result | HIGH | Gate C runs BEFORE Gate B; prior-art does not influence validity adjudication |
| 5 | Study adjudication aggregation undefined | HIGH | Deterministic aggregation rule: majority of 2; if disagreement, 3rd adjudicator; majority of 3 wins; 3-way split = AMBIGUOUS |
| 6 | Calibration failure triggers discretionary redesign | HIGH | Kappa < 0.40 → PROTOCOL_NOT_READY → no execution → revision requires new preregistration |
| 7 | B2 paired-vs-independent statistical structure unresolved | HIGH | McNemar's test for paired binary data (engine vs null on same case) |
| 8 | Candidate multiplicity / per-case budget unspecified | HIGH | Max 3 candidates per case (preregistered); success is binary at case level |
| 9 | Human-control resource equivalence unclear | MEDIUM | Renamed to "Input Equivalence" with explicit resource asymmetry documentation |
| 10 | Prior-art reproducibility under-specified | MEDIUM | Full search protocol: date, query, database, result snapshot hash, inclusion/exclusion, language, preprint/patent handling |
| 11 | Independent selector operational definition missing | MEDIUM | Selector protocol frozen: who, what they can see, rejection criteria, iteration limit |
| 12 | Negative scientific proposals control missing | MEDIUM (upgraded) | Added "beautiful nonsense" control: inputs specifically capable of generating plausible-sounding but scientifically meaningless relationships |

---

# PART 1: B1 — Controlled Rediscovery (Revised)

## 1.1 Central Question

> **Can the system reconstruct a known cross-domain relationship from source material without being given the relationship itself?**

## 1.2 Two-Stage Adjudication (Fix for Finding #1 — FATAL)

### Stage B1-A: Blind Quality Evaluation

**Adjudicator sees:**
- Source text A
- Source text B
- Candidate (proposed relationship + mechanism)

**Adjudicator does NOT see:**
- Gold bridge
- Which system generated the candidate
- Whether this is a true or null case
- System confidence score
- Whether candidate was AI-generated
- Prior-art search results

**Adjudicator scores:**
- Gate A: A0/A1/A2/A3/A4 (non-triviality)
- Gate C: PASS/FAIL (scientific validity)
- Cross-domain: YES/NO (does it genuinely connect the two domains?)

**Premise rejection:** Adjudicator may say "this isn't even a meaningful mechanism" → Gate C FAIL.

### Stage B1-B: Blinded Gold Comparison (separate evaluator)

**Evaluator sees:**
- Candidate (proposed relationship + mechanism)
- Gold bridge + gold published_relation

**Evaluator does NOT see:**
- Source texts (they already passed to Stage A)
- System identity
- Case condition (true/null)
- Stage A adjudicator's judgment
- Gate A or Gate C result

**Evaluator classifies:**
- EXACT_MATCH — candidate captures the identical mechanism
- FUNCTIONAL_EQUIVALENT — different formulation, same mechanism
- PARTIAL_MATCH — captures part but misses key elements
- NO_MATCH — does not capture the gold mechanism
- AMBIGUOUS — cannot determine

EXACT_MATCH and FUNCTIONAL_EQUIVALENT count as "recovered."
PARTIAL_MATCH, NO_MATCH, and AMBIGUOUS count as "not recovered."

### Governing rule verification

The semantic-match endpoint (B1-B) is computable from information the B1-B evaluator observes: candidate + gold. The B1-B evaluator does not need source texts, system identity, or Gate A/C results to make this determination.

The Gate A/C endpoints (B1-A) are computable from information the B1-A adjudicator observes: source texts + candidate. The B1-A adjudicator does not need the gold bridge to assess non-triviality or scientific validity.

## 1.3 Primary Endpoint (Revised per Finding #7)

```
B1 primary endpoint =
    (cases where candidate passes Gate A = A4
     AND semantic-match = EXACT or FUNCTIONAL_EQUIVALENT
     AND Gate C = PASS)
    / total clean cases
```

This is "RECOVERED_VALID_MECHANISM" — the engine rediscovered a known mechanism AND the proposed mechanism is scientifically valid.

### Secondary endpoints (reported separately)
- A4 rate (Gate A pass rate)
- Semantic recovery rate (EXACT + FUNCTIONAL_EQUIVALENT, regardless of Gate A/C)
- Gate C pass rate
- A4 + semantic (recovery regardless of validity)
- A4 + semantic + C (primary)
- Generation rate (fraction producing any candidate)
- Partial match rate

## 1.4 Null Construction (Fix for Finding #2 — FATAL)

### The problem with the original null
The original proposed using source texts from a different domain pair. This changes the task (different input, different difficulty) and is not a matched null.

### Revised null: same-input structural permutation

For each true case, the null uses the SAME source texts (domain A + domain B) but breaks the cross-domain correspondence:

1. Take the engine's generated candidate for the true case
2. Replace the domain-specific mechanism with a mechanism randomly recombined from OTHER cases' candidates
3. Preserve: proposal length, structural form, domain labels, output format
4. The recombined candidate is structurally plausible-looking but causally meaningless for THIS domain pair

### Null validity audit (pre-execution)

Before the engine runs, verify that each null:
- Has the same input complexity as the true case (same source texts)
- Has the same task (same generation instruction)
- Has the same output opportunity (same pipeline configuration)
- Contains no answer leakage (the recombined mechanism does not accidentally match the gold bridge)
- Has a known interpretation: if a null candidate passes Gate A + semantic-match + Gate C, this means the adjudication process accepted a causally meaningless proposal

### If null validity fails
```
NULL_VALIDITY = FAILED
EXPERIMENT = INCONCLUSIVE_INVALID_NULL
NO CASE EXCLUSION
NO REPAIR
```

### "Beautiful nonsense" control (Finding #12)

In addition to the matched null, include a control where the system is exposed to inputs specifically designed to generate plausible-sounding but scientifically meaningless relationships:
- Source pairs from domains with NO plausible cross-domain connection (e.g., quantum chromodynamics + medieval poetry)
- The system may still generate candidates — the question is whether adjudicators reject them at Gate C
- This tests whether Gate C is a rubber stamp or a real filter

## 1.5 Decision Partition (Exhaustive — Revised)

```
IF leakage_check == FAILED:
    INCONCLUSIVE_LEAKAGE

ELSE IF N_clean < 10:
    INSUFFICIENT_CLEAN_CASES

ELSE IF null_validity == FAILED:
    INCONCLUSIVE_INVALID_NULL

ELSE IF beautiful_nonsense_control == FAILED:
    INCONCLUSIVE_ADJUDICATION_RUBBER_STAMP
    (adjudicators accepted meaningless proposals → Gate C is not a filter)

ELSE IF recovery_rate ≥ 0.40 AND null_FP_rate ≤ 0.20:
    REDISCOVERY_CAPABILITY_ESTABLISHED (pilot)

ELSE:
    REDISCOVERY_NOT_ESTABLISHED
```

---

# PART 2: B2 — Open Discovery (Revised)

## 2.1 Source-Pair Selection (Fix for Finding #3 — HIGH)

### Mechanical sampling frame

```
Eligible domain universe (predefined list of ≥ 100 domain pairs)
        ↓
Mechanically generated candidate pairs (random selection from the universe)
        ↓
Blind eligibility screening (evaluator who has NOT seen engine outputs)
        ↓
Preregistered random selection (seed=42)
        ↓
Freeze (SHA recorded before engine runs)
```

### Selection rules
- The selector does NOT know which pairs the engine performs well on
- The selector does NOT see previous engine outputs
- The selector does NOT discuss candidates with engine builders
- The selector CAN reject pairs only if they fail explicit eligibility criteria (preregistered)
- Maximum 2 rejections per pair (to prevent iterative selection toward "fertile" pairs)
- Final pairs frozen before engine runs

### Eligibility criteria (preregistered)
- Both sources are scientific texts (papers, technical reports)
- Sources are from genuinely different domains
- Sources describe mechanisms (not just data)
- Sources are available in full text
- Sources are in English
- Sources are not from the existing gold set

### What "plausible but not obvious" means operationally
The selector does NOT assess whether a cross-domain connection is "plausible." The selector only verifies the eligibility criteria above. Whether a connection exists is for the engine to discover and the adjudicators to evaluate.

## 2.2 Adjudication Ordering (Fix for Finding #4 — HIGH)

### Correct ordering

```
CANDIDATE
    │
    ├──► Gate A (non-triviality)
    │        adjudicator sees: source A, source B, candidate
    │        adjudicator does NOT see: prior-art, gold, system identity
    │
    ├──► Cross-domain validity
    │        adjudicator sees: source A, source B, candidate
    │        does the candidate genuinely connect the two domains?
    │
    ├──► Gate C (scientific validity)
    │        adjudicator sees: source A, source B, candidate
    │        adjudicator does NOT see: prior-art result, gold, system identity
    │        adjudicator CAN reject premise ("not a meaningful mechanism")
    │
    │    FREEZE Gate A and Gate C RESULTS
    │
    └──► Gate B (prior art / novelty)
             separate evaluator
             sees: candidate only (not source texts, not Gate A/C results)
             conducts: independent literature search
```

### Why this ordering matters
Gate C (scientific validity) is evaluated WITHOUT knowledge of prior art. This prevents:
- "No prior art found" → adjudicator becomes more receptive (inflates validity)
- "Closely related mechanism found" → adjudicator becomes more skeptical (deflates validity)

Gate B is a separate evaluation channel. Scientific validity is frozen before novelty is assessed.

## 2.3 Adjudication Aggregation (Fix for Finding #5 — HIGH)

### Deterministic aggregation rule (preregistered)

For each gate (A, C, cross-domain):

```
2 adjudicators score independently

IF both agree (PASS/PASS or FAIL/FAIL):
    result = agreed value

IF they disagree (PASS/FAIL or FAIL/PASS):
    recruit 3rd adjudicator
    result = majority of 3

IF all 3 disagree (PASS/FAIL/PARTIAL or similar 3-way split):
    result = AMBIGUOUS
    (recorded, NOT counted as PASS)
```

### For Gate A (A0–A4 scale):
```
2 adjudicators classify independently

IF both agree (same classification):
    result = agreed classification

IF they differ by 1 level (e.g., A3 vs A4):
    recruit 3rd adjudicator
    result = majority classification

IF they differ by ≥ 2 levels OR all 3 disagree:
    result = AMBIGUOUS (recorded, NOT counted as A4)
```

### Inter-rater reliability
- **Calibration kappa:** calculated on non-study calibration cases BEFORE study execution
- **Study kappa:** calculated on study cases (reported, not used to adjust results)
- **Statistic:** Cohen's kappa for 2-rater, Fleiss' kappa for 3-rater
- **Missing ratings:** if an adjudicator cannot score (recusal, unavailability), the candidate is re-rated by a replacement adjudicator. The replacement is recorded.
- **Minimum N for kappa:** if < 10 rated cases, report percentage agreement instead and note "insufficient N for kappa"
- **Confidence interval:** bootstrap 95% CI for kappa (10000 resamples, seed=42)

## 2.4 Calibration Failure (Fix for Finding #6 — HIGH)

```
IF calibration_kappa < 0.40:
    PROTOCOL_NOT_READY
    → no study execution
    → no recalibration using study cases
    → protocol revision requires new preregistration
    → the rubric, training, or adjudicator pool must be revised
      and re-preregistered before another attempt
```

No iterative rubric adjustment. No "keep changing until they agree."

## 2.5 Candidate Multiplicity (Fix for Finding #8 — HIGH)

### Per-case budget
```
max_candidates_per_case = 3
```

The engine pipeline may generate multiple hypotheses. The first 3 candidates (by pipeline order) are retained. Additional candidates are recorded but NOT adjudicated.

### Success is binary at case level
```
case_success = (at least 1 of the ≤3 candidates passes all required gates)
```

A case with 3 valid candidates counts the same as a case with 1 valid candidate.

### Candidate multiplicity is a secondary metric
```
average_candidates_per_case = total_candidates / total_cases
```

This is reported but does not affect the primary outcome.

## 2.6 Statistical Framework (Fix for Finding #7 — HIGH)

### The pairing issue
If the null is matched within the same case (same source pair, same task, different candidate), the observations are PAIRED:
```
Case 1: engine=1, null=0
Case 2: engine=0, null=0
Case 3: engine=1, null=1
...
```

### Revised statistical test

**If null is case-matched (paired):**
- McNemar's test (exact binomial version for small N)
- Primary: P(engine success rate > null success rate | paired observations)
- α = 0.05, one-sided

**If null is independent (different source pairs):**
- Fisher's exact test, one-sided
- α = 0.05

### Preregistered choice
The null IS case-matched (same source pair, recombined candidate). Therefore:
- **Primary test: McNemar's exact test (one-sided)**
- Secondary: Fisher's exact test (exploratory, treats arms as independent)
- Confidence interval: exact binomial 95% CI for the difference in paired proportions

## 2.7 Input Equivalence (Fix for Finding #9 — MEDIUM)

### Renamed from "Control equivalence" to "Input equivalence"

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
| Max candidates | 3 | 3 | 3 | 3 | 3 |

### Resource asymmetry (documented, not "equivalent")
- Engine: effectively unlimited computation time within the pipeline
- Human: 30 minutes
- LLM: single API call
- Retrieval: algorithmic, near-instant

These are NOT equivalent resource conditions. The comparison is between systems with different capabilities and constraints. The document explicitly states this and does not claim the arms are "equivalent" beyond input material.

## 2.8 Prior-Art Search Protocol (Fix for Finding #10 — MEDIUM)

### Full specification
- **Databases:** Google Scholar, PubMed, arXiv, Semantic Scholar
- **Search date/time:** recorded per search (date + UTC time)
- **Exact query:** derived from candidate mechanism keywords (recorded verbatim)
- **Result snapshot:** top 20 results per database, URLs recorded, page saved (HTML snapshot hash recorded)
- **Inclusion/exclusion rules:**
  - Include: peer-reviewed papers, preprints, patents
  - Exclude: blog posts, news articles, Wikipedia
  - Language: English only
  - Publication cutoff: preregistered date
- **Duplicate handling:** deduplicate by title + first author
- **Preprint handling:** included if posted before cutoff
- **Patent handling:** included if filed before cutoff
- **Full-text review:** top 5 results after deduplication
- **Final determination:** NOVEL_AS_OF_CUTOFF / PRIOR_ART_FOUND / PARTIAL_PRECEDENT / AMBIGUOUS
- **Adjudicator independence:** the person conducting the novelty search is NOT the same person who conducted Gate A or Gate C adjudication for that candidate

## 2.9 Independent Selector Protocol (Fix for Finding #11 — MEDIUM)

### Operational definition
- **Who:** a person who has NOT seen engine outputs, has NOT contributed to engine development, and has NOT seen the gold set (for B2, there is no gold set)
- **What they can see:** the eligible domain universe, the eligibility criteria
- **What they cannot see:** engine outputs, gold set (B1), previous engine performance on any pair
- **Can they reject pairs?** Yes, but only if the pair fails explicit eligibility criteria (preregistered). Maximum 2 rejections per pair.
- **Can they iterate?** They can generate candidate pairs mechanically (random selection), screen for eligibility, and reject ineligible pairs. They CANNOT iterate toward "fertile" pairs.
- **Can they discuss with engine builders?** No. Communication about pair selection is prohibited.
- **Final pairs:** frozen (SHA recorded) before engine runs

---

# PART 3: Revised Decision Partitions

## B1 Decision Partition (Exhaustive)

```
IF leakage_check == FAILED:
    INCONCLUSIVE_LEAKAGE

ELSE IF N_clean < 10:
    INSUFFICIENT_CLEAN_CASES

ELSE IF null_validity == FAILED:
    INCONCLUSIVE_INVALID_NULL

ELSE IF beautiful_nonsense_control == FAILED:
    INCONCLUSIVE_ADJUDICATION_RUBBER_STAMP

ELSE IF calibration_kappa < 0.40:
    PROTOCOL_NOT_READY

ELSE IF recovery_rate ≥ 0.40 AND null_FP_rate ≤ 0.20:
    REDISCOVERY_CAPABILITY_ESTABLISHED (pilot)

ELSE:
    REDISCOVERY_NOT_ESTABLISHED
```

## B2 Decision Partition (Exhaustive)

```
IF null_validity == FAILED:
    INCONCLUSIVE_INVALID_NULL

ELSE IF beautiful_nonsense_control == FAILED:
    INCONCLUSIVE_ADJUDICATION_RUBBER_STAMP

ELSE IF calibration_kappa < 0.40:
    PROTOCOL_NOT_READY

ELSE IF north_star_yield == 0:
    NORTH_STAR_NOT_ACHIEVED

ELSE IF north_star_yield > 0 AND McNemar_p < 0.05 (one-sided, engine > null):
    NORTH_STAR_SIGNAL_DETECTED (pilot — requires Stage 2B replication)

ELSE:
    NORTH_STAR_NOT_ACHIEVED
```

---

# PART 4: Governing Rule Verification

> Every endpoint must be computable from information that the endpoint's adjudicator is actually allowed to observe.

| Endpoint | Adjudicator | Observes | Computable? |
|---|---|---|---|
| Gate A (A0–A4) | Blind adjudicator | source A, source B, candidate | YES — non-triviality is assessable from inputs + candidate |
| Gate C (PASS/FAIL) | Blind adjudicator | source A, source B, candidate | YES — scientific validity is assessable from mechanism + evidence |
| Cross-domain | Blind adjudicator | source A, source B, candidate | YES — does the candidate connect the two domains? |
| Semantic match (B1 only) | Separate evaluator | candidate, gold bridge | YES — does the candidate capture the same mechanism as the gold? |
| Gate B (novelty) | Separate evaluator | candidate only | YES — has this been published? (literature search) |
| Generation | System | source A, source B | YES — did the pipeline produce output? |
| Null FP | Blind adjudicator | source A, source B, null candidate | YES — does the null candidate pass Gate A + semantic + Gate C? |

All endpoints are computable from observed information. No endpoint requires the adjudicator to evaluate information they cannot see.

---

# PART 5: What This Revision Does NOT Authorize

- Implementing any protocol
- Executing any protocol
- Modifying frozen artifacts
- Selecting adjudicators or source pairs
- Making any discovery or capability claim

---

# Status

```
Protocol A: DRAFT — accepted as narrow prerequisite
Protocol B1: DESIGN REVISION R1 — requires adversarial review before freezing
Protocol B2: DESIGN REVISION R1 — requires adversarial review before freezing
Phase 8 execution: BLOCKED
M-008: FULL_QUARANTINE
North Star: NOT ACHIEVED
```
