# SCIENTIFIC_GATE_2_PROTOCOL.md

## Version: 1.1

## Status: CONDITIONALLY APPROVED — REVISED per independent protocol review

## Revision history
- v1.0: Initial draft (2026-08-08)
- v1.1: Revised per independent protocol review (2026-08-08). Six corrections:
  1. Statistical preregistration (α, primary comparison, multiplicity, effect size, CI)
  2. N=20 reinterpreted as pilot; Stage 2B expansion criterion added
  3. Gate-A adjudication rubric (A0–A4, only A4 passes)
  4. Gate-B: NOVEL_AS_OF_CUTOFF replaces absolute "never published"
  5. Control-equivalence table (model, version, prompt, attempts, tools, time, temperature)
  6. Matched null replaces naive random vocabulary; inter-rater reliability required

## Approval chain
```
777cb6d (frozen baseline)
   ↓
External review → PREMATURE
   ↓
Development frozen
   ↓
Gate 2 protocol v1.0 → CONDITIONALLY APPROVED
   ↓
Gate 2 protocol v1.1 → AWAITING FINAL INDEPENDENT REVIEW
   ↓
Protocol freeze → PENDING
   ↓
Prospective blind evaluation → PENDING
   ↓
Independent adjudication → PENDING
   ↓
Scientific conclusion → PENDING
```

## What this protocol is NOT

- It is NOT a repair of the existing scorer
- It is NOT a stricter version of `_bridge_matches()`
- It is NOT a new F1 benchmark
- It is NOT a modification of `GOLD_DISCOVERIES`
- It is NOT a modification of any production code

## What this protocol IS

A fundamentally different experiment that tests whether the engine can generate a scientifically meaningful relationship that is:
1. Absent from the input representations (Gate A)
2. Absent from the known literature (Gate B)
3. Judged independently to be a valid discovery (Gate C)

---

# 1. Central question

> **Can the engine generate a scientifically meaningful cross-domain relationship that is absent from the input representations, absent from the known literature, and judged independently to be a valid discovery?**

This is NOT asking whether the engine can achieve a higher F1. It is asking whether the engine can do something qualitatively different from retrieval, entity intersection, and lexical matching.

---

# 2. Discovery unit definition

A **discovery** is an auditable object with the following structure:

```
Input A (mechanism + constraints + observed behavior)
        ↓
Input B (different mechanism + constraints + observed behavior)
        ↓
Engine proposal (a stated cross-domain relationship + mechanism)
        ↓
Why it is NOT explicit in A or B (provenance argument)
        ↓
Prior-art search result (NOVEL / PREVIOUSLY_KNOWN / etc.)
        ↓
Expert adjudication (PASS / FAIL on scientific validity)
        ↓
Final classification
```

### What constitutes a proposal

A proposal must contain:
1. A stated relationship between domain A and domain B
2. A proposed mechanism explaining the connection
3. A prediction or testable consequence

A proposal is NOT:
- An extracted entity that appears in both inputs
- A synonym or paraphrase of something in the inputs
- A retrieval result
- A generated paragraph of prose without a specific claim

### Distinction from Stage −1

Stage −1 tested: "Does the system find a bridge concept in the entity intersection?"

Gate 2 tests: "Does the system generate a relationship that cannot be recovered from the inputs?"

---

# 3. Three mandatory gates

## Gate A — Novel proposal

The engine must generate a proposal that cannot be recovered from the input through:
- Exact matching
- Synonym matching
- Paraphrase
- Entity intersection
- Relation extraction
- Obvious composition of explicitly stated relationships
- Retrieval
- Benchmark leakage

### Gate A adjudication procedure

For each proposal, an independent evaluator classifies it using the following rubric:

```
A0 — Explicit: the proposal is stated verbatim in either input
A1 — Lexical/paraphrase: the proposal is recoverable via synonym, substring, or paraphrase of input text
A2 — Entity/relation extraction: the proposal is an entity or relation directly extractable from either input
A3 — Direct compositional inference: the proposal is an obvious composition of explicitly stated relationships (e.g., A causes B, B causes C → A causes C, where both links are explicit)
A4 — Non-trivial derived proposal: the proposal cannot be recovered by any of the above methods
```

Only **A4** passes Gate A.

The evaluator must document:
- The classification (A0, A1, A2, A3, or A4)
- The evidence supporting the classification (e.g., "the phrase 'thermal regulation' appears in source A line 3")
- Why the proposal is or is not recoverable from the inputs

This makes Gate A auditable: two independent evaluators should be able to review the same evidence and reach the same classification.

If the evaluator cannot find the concept or a close paraphrase in either input → A4 → Gate A PASS.

### Anti-leakage rule

Inputs should contain **mechanisms**, not the answer.

Bad input design:
```
Paper A: thermal regulation is important for...
Paper B: thermal management requires...
Expected discovery: thermal regulation
```

Good input design:
```
Domain A: mechanism + constraints + observed behavior (without naming the bridge concept)
Domain B: different mechanism + constraints + observed behavior (without naming the bridge concept)
Engine: derive a transferable mechanism
```

The evaluator should be able to ask:

> Where, exactly, did the proposed relationship come from?

If the answer is "it was already encoded in the entities extracted from the papers" → FAIL.

## Gate B — Novel knowledge

An evaluator independent of the engine must search prior literature and classify the proposal.

### Classification

```
NOVEL_AS_OF_CUTOFF — no materially equivalent relationship identified in the
                     predefined search corpus using the preregistered search
                     procedure as of the specified cutoff date
PRIOR_ART_FOUND     — a materially equivalent relationship was identified
PARTIAL_PRECEDENT   — related but not identical
AMBIGUOUS           — unclear
UNSUPPORTED         — no evidence found
```

Only `NOVEL_AS_OF_CUTOFF` can pass Gate B.

### Literature search protocol (preregistered)

The evaluator must record:
- Databases searched (e.g., Google Scholar, PubMed, arXiv, Semantic Scholar)
- Search terms used
- Date searched
- Date cutoff (the date before which prior art disqualifies novelty)
- Inclusion/exclusion rules for screening results
- Reviewer identity
- Number of results screened
- Number of full-text reviews
- Final determination

This replaces the previous "not previously published" language, which cannot be proven absolutely. "NOVEL_AS_OF_CUTOFF" is defensible because it documents the search procedure that was performed.

### Rediscovery category

If the engine independently reconstructs a relationship that already exists in literature but was absent from its supplied inputs, this is classified as **REDISCOVERY**.

Rediscovery is scientifically interesting but must NOT be called "novel discovery."

Gate 2 reports two separate quantities:
```
Independent rediscoveries
Validated novel discoveries
```

## Gate C — Scientific validity

Independent domain experts must evaluate whether the proposed relationship is:
- Coherent
- Mechanistically plausible
- Non-trivial
- Supported by the supplied evidence
- Sufficiently specific to test
- Potentially useful or explanatory

### Expert procedure

Experts receive:
- The proposal (relationship + mechanism)
- Both input sources
- The prior-art search result

Experts do NOT receive:
- Which system generated the proposal (engine vs. LLM vs. human)
- Whether the proposal is from the "gold" set
- The engine's own confidence score

### Inter-rater reliability (minimum two experts per proposal)

A minimum of **two independent experts** must evaluate each proposal. For contentious cases, **three experts** are required.

Each expert independently answers:
```
Is the relationship coherent? YES/NO
Is the mechanism plausible? YES/NO
Is it non-trivial? YES/NO
Is it supported by evidence? YES/NO
Is it testable? YES/NO
Is it potentially useful? YES/NO
Overall: PASS/FAIL
```

### Disagreement handling

If experts disagree materially (one says PASS, one says FAIL):
- A third expert is recruited
- The proposal is classified as AMBIGUOUS until adjudicated
- The adjudication procedure is: the third expert reviews the same materials and provides the deciding vote
- If all three disagree, the proposal remains AMBIGUOUS

Do NOT simply average expert opinions. Record:
```
expert_1_result
expert_2_result
expert_3_result (if applicable)
agreement (YES/NO)
adjudication (if needed)
final_result
```

For binary categorical judgments, calculate an appropriate agreement statistic (e.g., Cohen's kappa) where sample size permits.

Only unanimous PASS (or adjudicated PASS) at Gate C permits the claim **validated discovery**.

---

# 4. Prospective evaluation set

The evaluation set must be **prospectively frozen** before the engine generates its final proposals.

## What "prospective" means

1. The protocol, cases, and evaluation criteria are frozen BEFORE the engine runs
2. The engine builders must NOT see the final test cases
3. The engine builders must NOT modify the system around the test cases
4. The gold set must NOT be constructed after seeing outputs
5. Successful discoveries must NOT be added to the benchmark retroactively
6. Unsuccessful cases must NOT be removed

## Freeze procedure

1. An independent party (not the engine builders) selects input pairs
2. The input pairs are committed to a frozen file
3. The SHA of the frozen file is published
4. Only THEN does the engine run
5. The engine's outputs are committed before any evaluation
6. Evaluation begins only after outputs are frozen

## Input pair construction

Each input pair consists of:
- **Domain A source**: a scientific text describing a mechanism, constraints, and observed behavior
- **Domain B source**: a scientific text from a DIFFERENT domain describing a different mechanism

The bridge concept (if one exists) must NOT be explicitly named in either source. The sources should describe phenomena and mechanisms, not the cross-domain connection.

---

# 5. Mandatory control arms

Every test case must be run through ALL of the following. All arms must use the same input material and be scored under the same Gate A/B/C process.

## Control-equivalence table

For every arm, the following must be preregistered and held equivalent:

| Parameter | Engine | Retrieval baseline | Generic LLM | Human | Matched null |
|---|---|---|---|---|---|
| Input material | Same A + B | Same A + B | Same A + B | Same A + B | Same A + B |
| Model/system | TEE engine | BM25 + entity extraction | Prespecified LLM (model + version) | Qualified researcher | Structured recombination |
| Prompt | N/A (engine native) | N/A (algorithmic) | Preregistered zero-shot prompt | Preregistered task instructions | N/A (algorithmic) |
| Temperature | N/A | N/A | 0.0 (deterministic) | N/A | N/A |
| Max attempts | 1 | 1 | 1 | 1 (within time budget) | 1 |
| Time limit | N/A | N/A | N/A | 30 minutes per case | N/A |
| External search access | No | No | No | No | No |
| Tool access | Engine's native pipeline | Retrieval only | Text generation only | Pen and paper / word processor | Recombination only |
| Retry policy | None | None | None | None | None |
| Output format | Stated relationship + mechanism | Shared entity name | Stated relationship + mechanism | Stated relationship + mechanism | Stated relationship + mechanism |

### Control 1 — Retrieval/entity baseline
- Extract entities from A and B using the same NLP pipeline
- Find entity intersections (shared entities)
- Propose any shared entity as a "discovery"
- Score under Gate A/B/C

### Control 2 — Generic LLM
- Give both sources to a preregistered generic LLM (specific model and version documented before execution)
- Prompt: "Given these two texts from different domains, what connecting concept or mechanism do they share? Propose a specific, testable cross-domain relationship with a mechanism."
- Temperature: 0.0 (deterministic)
- One attempt per case
- Score under Gate A/B/C

### Control 3 — Human baseline
- Give both sources to qualified researchers (domain-matched where possible)
- Time budget: 30 minutes per case
- No external literature search (to match engine conditions)
- Ask: "Propose a specific, testable cross-domain relationship with a mechanism."
- Score under Gate A/B/C

### Control 4 — Matched null baseline
- For each case, take the engine's proposal structure (relationship + mechanism format)
- Replace the domain-specific content with content randomly recombined from OTHER cases' mechanisms
- Preserve proposal length, domain labels, and structural form
- This produces structurally plausible-looking but causally meaningless proposals
- Score under Gate A/B/C

**Purpose of matched null:** Answer "How often can a structurally plausible-looking but causally meaningless proposal accidentally pass the adjudication process?" This is much stronger than naive random vocabulary sampling.

## Purpose of all controls

The engine must demonstrate something beyond these controls. The critical question:

> Does the engine produce substantially more independently validated novel proposals than systems that merely retrieve, associate, or extract?

---

# 6. Auditable provenance chain

Every proposal needs a provenance chain:

```
Input A (full text)
        ↓
Input B (full text)
        ↓
Relevant mechanisms identified by the engine
        ↓
Engine reasoning/proposal (exact output)
        ↓
Proposed relationship (stated claim + mechanism)
        ↓
Why it is NOT explicit in A or B (evaluator analysis)
        ↓
Prior-art search (independent literature search)
        ↓
Expert adjudication (blinded)
        ↓
Final classification
```

The evaluator must be able to independently reconstruct this chain.

---

# 7. Outcome measurement

## NO single headline F1

The protocol explicitly does NOT use a single F1-style metric.

## Primary outcome

```
Validated Novel Discoveries
───────────────────────────
Total Prospective Cases
```

## Secondary outcomes (reported separately)

- Proposal rate (fraction of cases where the engine produces any proposal)
- Gate-A pass rate (fraction of proposals not recoverable from inputs)
- Gate-B novelty rate (fraction of Gate-A passes that are NOVEL)
- Gate-C validity rate (fraction of Gate-B passes that are expert-validated)
- Validated discovery yield (fraction of total cases producing validated novel discoveries)
- Retrieval-baseline yield
- Generic-LLM yield
- Human yield
- Random/null yield
- Independent rediscovery yield (PRIOR_ART_FOUND but absent from inputs — i.e., the engine reconstructed a known relationship that was NOT in the supplied inputs)

## Every numerator must link to an auditable case

No aggregate number may be reported without the individual case files that produce it.

---

# 8. Pre-registered failure criteria

These are defined BEFORE execution. Goalposts do not move afterward.

### Failure condition 1 — No differentiation from primary control

> If the engine's validated novel-discovery yield is not significantly greater than the generic-LLM baseline yield (one-sided Fisher's exact test, α = 0.05), the experiment does not establish specialized discovery capability beyond what a generic LLM can achieve.

### Failure condition 2 — Insufficient volume

> If fewer than 3 cases survive all three gates (A=A4, B=NOVEL_AS_OF_CUTOFF, C=PASS), the result is insufficient to establish even pilot-level discovery capability.

3 is a minimum for the pilot, not a target. Three discoveries out of twenty is nowhere near evidence of broad general capability — it is the minimum to justify a Stage 2B expansion.

### Failure condition 3 — Gate-A leakage

> If more than 50% of the engine's proposals are classified as A0, A1, A2, or A3 (i.e., recoverable from inputs), the engine is not demonstrating generation beyond extraction.

### Failure condition 4 — No expert validation

> If 0 proposals pass Gate C (expert validation), the engine is not producing scientifically meaningful relationships.

### What failure means

Failure does NOT mean the engine is incapable of discovery. It means the experiment did not establish that capability. The distinction matters.

---

# 9. Evaluator independence requirements

### Who can be an evaluator

- Did NOT build the engine
- Did NOT contribute to the benchmark
- Did NOT see the engine's outputs before evaluation
- Has NO incentive to produce a particular result

### What evaluators control

- Evaluation criteria (within this protocol)
- Negative controls
- Novelty determination
- Prior-art search
- Final classification

### What evaluators must NOT do

- Silently modify the frozen baseline
- Present a modified benchmark as the original
- Report unsupported scores
- Treat generated prose as evidence
- Accept the engine's own novelty assertion as proof

---

# 10. Statistical analysis (preregistered)

## Significance level
α = 0.05, one-sided (engine yield > control yield)

## Primary comparison
**Engine vs. generic-LLM baseline**

The generic-LLM baseline is the primary comparison because it represents the strongest non-human, non-engine system. If the engine cannot beat a generic LLM, it is not adding specialized value.

## Secondary comparisons
- Engine vs. retrieval baseline
- Engine vs. human baseline
- Engine vs. matched null

All secondary comparisons use the same α = 0.05 but are reported with confidence intervals and interpreted as exploratory.

## Multiplicity treatment
The primary comparison is the confirmatory test. Secondary comparisons are exploratory and do not require multiplicity correction, but this is stated in advance — not decided post hoc.

If the protocol is revised to use "best control" as the primary comparison, Bonferroni correction across 4 comparisons would be required (α = 0.05/4 = 0.0125). The current design avoids this by preregistering the generic-LLM as the single primary comparison.

## Statistical test
Fisher's exact test (one-sided) for the primary comparison, given the expected small sample sizes and binary outcomes.

## Effect-size reporting
- Absolute risk difference (engine yield − control yield)
- 95% confidence interval (via exact/binomial method)
- Number needed to treat (NNT = 1 / risk difference, if positive)

## Confidence interval method
Exact (Clopper-Pearson) binomial confidence intervals for individual yields. Wald interval with continuity correction for the difference.

## Sample size
N ≥ 20 prospective cases (per system: engine + 4 controls = 100 total evaluations).

### Interpretation of N=20

N=20 is a **minimum prospective pilot** intended to determine whether the engine merits a larger validation study. It is NOT, by itself, sufficient to establish general-purpose discovery capability.

### Stage 2B expansion criterion

If Gate 2A (pilot) shows promising signal (engine yield > primary control yield, with effect size > 0), the protocol expands to:

```
Gate 2B = independent replication
- New cases (not seen in Gate 2A)
- New domains (not covered in Gate 2A)
- New evaluators (not used in Gate 2A)
- N ≥ 50 for Gate 2B
```

No claim of "world-class" or general discovery capability should follow from Gate 2A alone. Gate 2B is required for such claims.

---

# 11. Stop conditions

The experiment stops and reports PREMATURE if:

- The engine cannot run on the prospective cases
- The input pairs are contaminated (bridge concept is explicit in inputs)
- The evaluation cannot be completed (experts unavailable)
- The protocol was violated (e.g., engine builders saw test cases)

The experiment reports FAIL if any pre-registered failure condition is met.

The experiment reports PASS (pilot) only if:
- At least 3 cases survive all three gates (A=A4, B=NOVEL_AS_OF_CUTOFF, C=PASS)
- Engine yield > generic-LLM yield (primary comparison, one-sided Fisher's exact, α = 0.05)
- Engine yield > matched-null yield

PASS at pilot does NOT establish general discovery capability. It only justifies Stage 2B expansion.

---

# 12. What this protocol does NOT approve

- Repairing the old scorer
- Changing GOLD_DISCOVERIES
- Creating a new discovery benchmark (implementation)
- Adding agents
- Modifying Gen5
- Adding Proposal Composer
- Optimizing discovery
- Tuning prompts against Gate 2 cases
- Claiming discovery capability
- Claiming invention capability

These can only be reconsidered AFTER this protocol is independently reviewed, frozen, and executed.

---

# 13. Immutable freeze procedure

1. This protocol document is committed
2. An independent reviewer reviews it
3. The reviewer either approves or rejects
4. If approved, the protocol SHA is recorded as frozen
5. The prospective input pairs are selected by an independent party
6. The input pairs are committed and their SHA recorded
7. Only THEN does implementation begin
8. The engine runs on the frozen inputs
9. Outputs are committed before evaluation
10. Evaluation proceeds according to this protocol
11. Results are recorded
12. No modifications to inputs, outputs, or criteria after evaluation begins

---

# 14. Distinction from the current benchmark

| Dimension | Stage −1 benchmark | Gate 2 protocol |
|---|---|---|
| What it tests | Entity intersection | Generation of novel relationship |
| Input design | Snippets containing bridge concept (paraphrased) | Mechanisms/constraints WITHOUT bridge concept |
| Proposal mechanism | `discover_shared_entities()` (entity overlap) | Engine must generate, not retrieve |
| Matching | `_bridge_matches()` (token overlap) | Gate A: independent evaluator determines if recoverable from inputs |
| FP measurement | FP=0 by construction | Every proposal evaluated; incorrect proposals count against yield |
| Novelty | Not tested | Gate B: independent literature search (NOVEL_AS_OF_CUTOFF) |
| Expert validation | Not performed | Gate C: blinded expert review (minimum 2 experts, disagreement handling) |
| Controls | None | 4 mandatory controls (retrieval, LLM, human, matched null) |
| Headline metric | F1 (single number) | Validated discovery yield (no single F1) |
| Prospective | No (gold set known to builders) | Yes (inputs frozen before engine runs) |
| Leakage control | Lexical only | Lexical + semantic + conceptual + mechanistic |

---

# 15. Deliverable

This document is the deliverable. It is a protocol specification, NOT an implementation.

The next step is independent protocol review. If approved, the protocol is frozen and implementation begins.

If rejected, the protocol is revised and re-submitted.

No implementation occurs until the protocol is independently approved and frozen.

---

## Protocol version
1.1

## Date
2026-08-08

## Author
Repository coder (not the independent reviewer)

## Status
AWAITING_INDEPENDENT_PROTOCOL_REVIEW
