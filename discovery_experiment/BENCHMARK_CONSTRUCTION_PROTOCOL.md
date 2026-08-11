# BENCHMARK_CONSTRUCTION_PROTOCOL — Definitive North Star Benchmark

**Status:** FROZEN — immutable benchmark construction protocol
**Date:** 2026-08-10
**Purpose:** The benchmark is the most important unresolved risk. It must be custodian-controlled, externally seeded, sealed, and inaccessible to the generator/evaluator before execution.

---

## The Benchmark Question

> **Are the problems representative of the discovery problem, or are they cases TEE is particularly good at?**

If the latter, any positive result is a measurement artifact.

---

## Hard Requirements (Per Power Analysis)

| Requirement | Value | Rationale |
|-------------|-------|-----------|
| Minimum N (problems) | 100 | Required for 10pp superiority margin at α=0.0167 (Bonferroni). See power analysis in NORTH_STAR_GATE_A_EXECUTION_GATE.md. |
| If 10pp infeasible | 80 (with 15pp margin) | Relaxed margin; achieves 0.80 power if TEE ≥ 30% and control ≤ 15%. |
| Minimum domains | 4 unrelated scientific domains | Prevents domain-specific optimization. |
| Selection | Externally seeded (unpredictable to team) | Prevents case-selection bias. |
| Sealing | SHA-256 locked before execution | Prevents post-hoc case modification. |
| Custodian | Independent from team | Prevents answer leakage. |

---

## Custodian Separation

```
Problem Constructor (creates cases + ground truth)
        ↓
Sealed Benchmark (SHA-256 locked)
        ↓
Independent Evaluator (runs Gate A, no answer access)
        ↓
Confirmation Party (Gate B only, answer access after prediction lock)
```

### Roles

| Role | Who | Access | Cannot do |
|------|-----|--------|-----------|
| Problem Constructor | Custodian + domain experts | Creates cases, ground truth | Cannot adjudicate, cannot run TEE |
| Sealed Benchmark | Custodian | Holds SHA-256 lock | Cannot modify after seal |
| Independent Evaluator | Execution team | Runs all 6 arms, blind | Cannot access answers |
| Confirmation Party | Independent lab/expert | Gate B only | Cannot access answers before prediction lock |
| TEE Team | Coders | Runs TEE arm | Cannot see benchmark cases before seal, cannot access answers |

### Generator Must NEVER See (Before Prediction Lock)
- Gold labels
- Expected mechanism
- Expected direction
- Falsifier
- Answer-derived synonyms
- Benchmark-specific terminology

---

## Case Construction Protocol

### Step 1: Domain Selection (Custodian)
- Select ≥4 unrelated scientific domains (e.g., fluid mechanics, enzymology, optics, materials science)
- Domains must be sufficiently different that expertise in one does not transfer to another
- Domain list is frozen and sealed

### Step 2: Problem Seeding (External)
- For each domain, an external seeder (not the team) provides 25+ problem seeds
- Seeds are brief descriptions of source-target pairs, not detailed cases
- Seeds are unpredictable to the team (team cannot anticipate which seeds will be selected)

### Step 3: Case Construction (Custodian + Domain Experts)
- For each selected seed, the custodian constructs:
  - Source document A (mechanism description)
  - Source document B (target problem description)
  - Ground truth (mechanism, causal variable, direction, magnitude, falsifier)
  - Expected label (ALLOW for positive, REJECT for negative)
- 50% positive cases, 50% hard-negative cases
- Hard-negatives must have plausible but wrong mechanism transfers

### Step 4: Information Boundary Verification (Custodian)
- Verify no answer-derived information leaks into source documents
- Verify no benchmark-specific terminology appears in source documents
- Verify ground truth is stored separately and sealed

### Step 5: Sealing (Custodian)

The custodian seal must contain, at minimum:

| # | Seal Component | Description |
|---|----------------|-------------|
| 1 | Immutable benchmark hash | SHA-256 of the complete sealed benchmark file |
| 2 | Case count and domain distribution | N (≥100), number of domains (≥4), cases per domain |
| 3 | Source-pair hashes | SHA-256 of each (source_a, source_b) pair, listed by case ID |
| 4 | Answer-key hash | SHA-256 of the ground-truth file (stored separately from blind fixture) |
| 5 | Timestamp | ISO 8601 timestamp of sealing |
| 6 | Construction/randomization seed | The seed used for case selection (for reproducibility) |
| 7 | Attestation: no TEE team access | Custodian attests that no TEE team member saw the benchmark before sealing |
| 8 | Attestation: answer key inaccessible | Custodian attests that the answer key is inaccessible to every generator/evaluator |
| 9 | Independent verification | An independent party (not the custodian, not the TEE team) verifies the sealed package integrity |

### Step 6: Custodian Independence Verification
- Custodian signs attestation that:
  - Cases were constructed without TEE team input
  - Seeds were externally provided
  - Ground truth is sealed and inaccessible to the team
  - No answer-derived information was shared with the team
- Independent verifier confirms:
  - Seal hash matches the sealed file
  - Blind fixture (source_a, source_b only) contains no ground-truth fields
  - Answer-key file is stored in a separate, access-controlled location

---

## Case Format

Each case in the sealed benchmark:

```json
{
  "id": "NS-{domain}-{number}",
  "domain": "fluid_mechanics",
  "source_a": "Source document A text...",
  "source_b": "Source document B text...",
  "candidate_prompt": "How might the mechanism in Source A apply to the problem in Source B?",
  "ground_truth": {
    "type": "positive" or "negative",
    "mechanism": "expected mechanism",
    "causal_variable": "expected variable",
    "direction": "expected direction",
    "magnitude": "expected magnitude",
    "falsifier": "expected falsifier"
  }
}
```

**The team receives ONLY:** `id`, `source_a`, `source_b`, `candidate_prompt`
**The custodian retains:** `ground_truth` (sealed)

---

## What the Benchmark Tests

| If benchmark result | Interpretation |
|--------------------|---------------|
| TEE beats controls on positive cases | TEE can recover correct mechanisms on unseen problems |
| TEE rejects negative cases | TEE can identify false transfers |
| TEE passes positive but fails negative | TEE is too permissive (false positives) |
| TEE rejects negative but fails positive | TEE is too strict (false negatives) |
| TEE fails both | TEE is not a discovery instrument |

---

## Freeze Status

**FROZEN.** Protocol is immutable. The benchmark itself is NOT YET CONSTRUCTED — construction requires custodian action.

---

## Critical Rules (Per CTO Direction)

### Rule 1: Do Not Optimize for Difficulty

The benchmark must be **representative**, not designed to make TEE look good or bad.

- The construction protocol determines the sampling process **BEFORE** the source material is selected
- The custodian must not select cases based on perceived difficulty for TEE
- The custodian must not filter cases based on whether TEE is "likely to succeed" or "likely to fail"
- Cases are selected by the externally seeded randomization process, not by judgment of suitability

**If the custodian suspects the benchmark is biased (too easy or too hard), the response is to reconstruct with a different seed — NOT to cherry-pick cases.**

### Rule 2: Post-Seal Freeze-All

Once the benchmark is sealed, **everything is frozen again.** No changes to any specification based on observed results.

| What is frozen after benchmark sealing | Status |
|---------------------------------------|--------|
| C2 (Frontier LLM) specification | FROZEN — no changing because the frontier model looks too strong |
| Retrieval specification | FROZEN — no changing because retrieval performs unexpectedly well |
| 10pp superiority margin | FROZEN — no relaxing because the gap is smaller than hoped |
| Novelty definition | FROZEN — no redefining "novel" to include more candidates |
| Adversarial gate | FROZEN — no relaxing because the gate kills too many candidates |
| Statistical test | FROZEN — no switching to a more favorable test |
| Expert protocol | FROZEN — no changing expert qualifications or time budget |

> **Otherwise you have simply moved the tuning problem from the model into the evaluation.**

### Rule 3: No TEE Team Benchmark Construction

The TEE team must NOT construct the benchmark. This includes:
- Selecting source pairs
- Writing source documents
- Defining ground truth
- Reviewing cases before sealing
- Providing input on case difficulty or suitability

The TEE team's role begins ONLY when the sealed blind fixture is delivered for execution.

---

## Final Gate Sequence

```text
22/25
  ↓
Independent custodian identified
  ↓
N≥100 benchmark constructed (representative, not difficulty-optimized)
  ↓
Benchmark + answer key sealed (9-component seal)
  ↓
Blind fixture extracted (source_a, source_b, candidate_prompt only)
  ↓
Hash independently verified
  ↓
Answer key access tested (confirmed inaccessible to generators/evaluators)
  ↓
25/25
  ↓
Post-seal freeze-all enforced
  ↓
EXECUTION AUTHORIZED
```

---

## Preflight Checklist Update

| Item | Status Before | Status After |
|------|--------------|-------------|
| 9. Benchmark construction protocol frozen | ⬜ NOT FROZEN | ✅ PASS |
| 10. Benchmark sealed | ⬜ NOT CONSTRUCTED | ⬜ PENDING (requires custodian action) |
| 11. Benchmark custodian independent | ⬜ NOT ESTABLISHED | ⬜ PENDING (requires custodian identification) |
| 12. Answer key inaccessible to execution | ⬜ NOT VERIFIED | ⬜ PENDING (verified at seal time) |
