# SCIENTIFIC_GATE_2_PROTOCOL.md

## Status: DRAFT — AWAITING INDEPENDENT PROTOCOL REVIEW

## Approval chain
```
777cb6d (frozen baseline)
   ↓
External review → PREMATURE
   ↓
Development frozen
   ↓
Gate 2 protocol design → APPROVED (this document)
   ↓
Independent protocol review → PENDING
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

For each proposal, an independent evaluator asks:

> Could a competent evaluator reconstruct the proposed bridge merely by looking at entities, relations, phrases, synonyms, or paraphrases already present in A and B?

If YES → Gate A FAIL.

The evaluator must document exactly where in the input the concept appears (or a close paraphrase thereof).

If the evaluator cannot find the concept or a close paraphrase in either input → Gate A PASS.

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
NOVEL — not previously published
PREVIOUSLY_KNOWN — published before the benchmark
PARTIAL_PRECEDENT — related but not identical
AMBIGUOUS — unclear
UNSUPPORTED — no evidence found
```

Only `NOVEL` can pass Gate B.

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

Experts answer:
```
Is the relationship coherent? YES/NO
Is the mechanism plausible? YES/NO
Is it non-trivial? YES/NO
Is it supported by evidence? YES/NO
Is it testable? YES/NO
Is it potentially useful? YES/NO
Overall: PASS/FAIL
```

Only PASS at Gate C permits the claim **validated discovery**.

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

Every test case must be run through ALL of the following:

### Control 1 — Retrieval/entity baseline
- Extract entities from A and B
- Find entity intersections
- Propose any shared entity as a "discovery"
- Score under Gate A/B/C

### Control 2 — Generic LLM
- Give both sources to a generic LLM (GPT-4, Claude, etc.)
- Prompt: "Given these two texts from different domains, what connecting concept or mechanism do they share? Propose a specific, testable cross-domain relationship."
- Score under Gate A/B/C

### Control 3 — Human baseline
- Give both sources to qualified researchers
- Ask them to propose a cross-domain connection
- Score under Gate A/B/C

### Control 4 — Random/null baseline
- Randomly select terms from a scientific vocabulary
- Propose random cross-domain connections
- Score under Gate A/B/C
- This establishes the chance rate of apparently interesting proposals

## Purpose

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
- Independent rediscovery yield (PREVIOUSLY_KNOWN but absent from inputs)

## Every numerator must link to an auditable case

No aggregate number may be reported without the individual case files that produce it.

---

# 8. Pre-registered failure criteria

These are defined BEFORE execution. Goalposts do not move afterward.

### Failure condition 1 — No differentiation from baselines

> If the engine's validated novel-discovery yield is not distinguishable from the retrieval/generic-LLM/null baselines, the experiment does not establish specialized discovery capability.

### Failure condition 2 — Insufficient volume

> If fewer than 3 cases survive all three gates (A=PASS, B=NOVEL, C=PASS), the result is insufficient to establish general discovery capability.

3 is a minimum, not a target. The protocol does not claim that 3 discoveries prove general capability — only that fewer than 3 is insufficient.

### Failure condition 3 — Gate-A leakage

> If more than 50% of the engine's proposals fail Gate A (i.e., are recoverable from inputs), the engine is not demonstrating generation beyond extraction.

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

# 10. Statistical analysis

### Comparison

The primary comparison is:

```
Engine yield vs. best control yield
```

Where yield = validated novel discoveries / total cases.

### Statistical test

Fisher's exact test or binomial test, depending on sample size.

The protocol does NOT prescribe a specific p-value threshold. Instead, it requires:
- The effect size (difference in yield)
- The confidence interval
- The sample size
- A pre-registered interpretation

### Minimum sample size

N ≥ 20 prospective cases (per system: engine + 4 controls = 100 total evaluations).

---

# 11. Stop conditions

The experiment stops and reports PREMATURE if:

- The engine cannot run on the prospective cases
- The input pairs are contaminated (bridge concept is explicit in inputs)
- The evaluation cannot be completed (experts unavailable)
- The protocol was violated (e.g., engine builders saw test cases)

The experiment reports FAIL if any pre-registered failure condition is met.

The experiment reports PASS only if:
- At least 3 cases survive all three gates
- Engine yield > best control yield
- The effect is not explainable by chance alone

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
| Novelty | Not tested | Gate B: independent literature search |
| Expert validation | Not performed | Gate C: blinded expert review |
| Controls | None | 4 mandatory controls (retrieval, LLM, human, random) |
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
1.0

## Date
2026-08-08

## Author
Repository coder (not the independent reviewer)

## Status
AWAITING_INDEPENDENT_PROTOCOL_REVIEW
