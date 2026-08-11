# Protocol B Adversarial Audit — Candidate-Generation → Recognition Chain

**Date:** 2026-08-09
**Auditor:** Repository coder (self-audit per CEO directive)
**Status:** DEFECTS FOUND — Protocol B design requires correction before execution

---

## CEO's Five Questions

### 1. What generates the candidate?

**Current implementation:** `run_discovery_benchmark()` generates candidates as follows:

1. Feed `source_snippet_a` and `source_snippet_b` to `NLPPipeline.extract_entities()`
2. Feed the same snippets to `NLPPipeline.extract_relations()`
3. Call `discover_shared_entities(lit_a_entities, lit_b_entities)` — finds entities appearing in BOTH literatures
4. The shared entities ARE the candidates
5. Each candidate is checked against `gold.bridge` using `_bridge_matches()`

**Assessment:** The candidate IS system-generated. The system receives source text, extracts entities, and finds shared entities. The gold bridge is NOT supplied as input — the system must discover it from the text.

**However:** The "discovery" is entity intersection, not mechanism generation. The system finds entities that appear in both texts — it does not generate a novel mechanism. This is closer to retrieval than discovery.

**Defect B-1:** The candidate generation is entity intersection, not mechanism generation. The SCIENTIFIC_GATE_2_PROTOCOL.md (v1.2) explicitly states this is NOT discovery: "A proposal is NOT: An extracted entity that appears in both inputs." Protocol B must test mechanism generation, not entity intersection.

### 2. Can candidate generation leak the answer?

**Risk assessment of leakage vectors:**

| Vector | Risk | Status |
|---|---|---|
| Bridge word in source snippets | HIGH | F-099 hard gate checks this — benchmark exits non-zero if bridge appears in input |
| Gold-set structure in filenames | LOW | Filenames use gold IDs (DISC-GOLD-001) but the system doesn't see filenames |
| Cached NLP outputs | MEDIUM | If NLP pipeline caches entity extractions from previous runs, it could leak |
| Prompt context | N/A | The NLP pipeline uses spaCy, not an LLM — no prompt to leak through |
| Fixture names | LOW | Gold entries have `id` field but it's not passed to the NLP pipeline |
| Search indices | LOW | No search index is used in the discovery benchmark |
| Metadata | LOW | Gold entries have `published_relation` and `verification` fields not passed to the pipeline |

**Defect B-2:** The F-099 circularity check only checks for the EXACT bridge string in the source snippets. It does NOT check for:
- Paraphrases of the bridge concept
- Synonyms of the bridge
- Substrings of the bridge that could guide entity extraction
- Concepts that are lexically close but not identical

A source snippet could contain "mineral precipitation" (a paraphrase of "biomineralization") without triggering F-099, and the NLP pipeline could extract "mineral_precipitation" as an entity, which `_bridge_matches()` might match against "biomineralization" via token overlap.

### 3. Does the scorer see enough information to judge correctness?

**Current scorer:** `_bridge_matches(expected_bridge, candidate)` — receives only two strings.

**Assessment:** This is the SAME defect as Protocol A. The scorer receives only two strings and does string matching. It does NOT see:
- The source documents
- The proposed mechanism
- The relationship claim
- Whether the candidate was derived from domain A or B

**Defect B-3:** If Protocol B uses `_bridge_matches()` as the scorer, it recreates the Protocol A defect. The scorer cannot judge whether a candidate represents a genuine cross-domain relationship — it can only check string similarity.

**Required correction:** Protocol B must use a DIFFERENT scoring procedure that evaluates the candidate as a relationship/mechanism, not just a string. The SCIENTIFIC_GATE_2_PROTOCOL.md already defines this: Gate A (is the proposal recoverable from inputs?), Gate B (is it novel?), Gate C (is it scientifically valid?).

### 4. What is the true unit of independence?

**Current design:** 20 gold discoveries, each producing one observation (bridge_found: True/False).

**Assessment of independence:**
- Each gold discovery uses different source snippets from different domain pairs
- The NLP pipeline is stateless (spaCy processes each text independently)
- `discover_shared_entities()` operates on each pair independently
- No cross-case dependence in the candidate generation

**However:** If Protocol B uses LLM-based generation (e.g., the discovery engine's mechanism extraction → abstraction → transfer → hypothesis generation pipeline), the LLM's internal state could create dependence:
- The LLM might "remember" patterns from previous cases
- If the LLM is called with the same temperature/seed, outputs could be correlated
- If the same provider session is used, rate-limiting could affect output quality differently across cases

**Defect B-4:** If Protocol B uses the LLM-based discovery pipeline (not just NLP entity extraction), the independence assumption needs explicit verification. The unit of resampling must be the case, not the observation, and the LLM must not carry state between cases.

### 5. What constitutes a true positive?

**Current definition:** `_bridge_matches(gold.bridge, candidate)` returns True — the candidate string matches the gold bridge string via exact/substring/token/synonym matching.

**Assessment:** This is almost certainly too narrow for genuine discovery.

**Problems:**
1. **Exact string matching is too narrow:** The system might discover "calcium carbonate precipitation" when the gold bridge is "biomineralization" — a correct discovery that fails string matching.
2. **Semantic equivalence cannot be introduced post-hoc:** If the system discovers a correct but differently-worded relationship, we cannot retroactively decide it counts.
3. **The gold bridge might be wrong:** The gold set contains published bridges, but the system might discover a DIFFERENT valid cross-domain connection that the gold entry doesn't capture.

**Defect B-5:** True positive definition requires a predeclared adjudication protocol. The SCIENTIFIC_GATE_2_PROTOCOL.md already defines this (Gate A/B/C), but Protocol B hasn't specified which adjudication level it uses.

**Required:** Protocol B must predeclare:
- Is a true positive exact string match? (too narrow)
- Is it semantic equivalence? (requires predeclared adjudication)
- Is it expert-validated scientific validity? (Gate C)
- Is it novelty? (Gate B)

---

## Summary of Defects Found

| ID | Defect | Severity |
|---|---|---|
| B-1 | Candidate generation is entity intersection, not mechanism generation | FATAL — Protocol B would test retrieval, not discovery |
| B-2 | F-099 circularity check only catches exact bridge strings, not paraphrases | HIGH — leakage risk |
| B-3 | Scorer sees only two strings (same as Protocol A defect) | FATAL — recreates the original protocol-validity failure |
| B-4 | Independence assumption unverified for LLM-based pipeline | MEDIUM — needs explicit verification |
| B-5 | True positive definition not predeclared | FATAL — cannot interpret results without it |

---

## Required Corrections Before Protocol B Can Be Authorized

### Correction for B-1: Use the full discovery pipeline
Protocol B must use the engine's mechanism extraction → abstraction → transfer → hypothesis generation pipeline, not just NLP entity extraction. The candidate must be a generated mechanism/relationship, not an extracted entity.

### Correction for B-2: Strengthen anti-leakage
The circularity check must be extended to detect:
- Paraphrases of the bridge concept in source snippets
- Synonym overlap
- Substring matches that could guide extraction

### Correction for B-3: Use Gate A/B/C adjudication
Protocol B must use the SCIENTIFIC_GATE_2_PROTOCOL.md's three-gate adjudication, not `_bridge_matches()`. The scorer must evaluate whether the candidate is:
- Gate A: Not recoverable from inputs
- Gate B: Novel (not in prior literature)
- Gate C: Scientifically valid (expert adjudication)

### Correction for B-4: Verify independence
If using LLM-based generation, each case must be processed in an independent LLM session. No state sharing between cases. Document the provider, model, temperature, and seed.

### Correction for B-5: Predeclare true positive definition
Protocol B must predeclare what counts as a true positive BEFORE seeing results. Options:
- A4 classification (Gate A: non-trivial derived proposal)
- A4 + NOVEL_AS_OF_CUTOFF (Gate A + Gate B)
- A4 + NOVEL + expert PASS (Gate A + Gate B + Gate C)

The preregistration must specify which level is the primary endpoint.

---

## Relationship to Existing Infrastructure

### SCIENTIFIC_GATE_2_PROTOCOL.md (v1.2 FROZEN)

Gate 2 already defines the correct experiment type. Protocol B should be designed as a **measurement-discrimination prerequisite** to Gate 2, using the same adjudication framework but with a simpler statistical design.

### DXP-001 through DXP-005

The DXP experiments already tested the discovery engine's pipeline (extraction → abstraction → transfer → hypothesis generation → adversarial filtering). Protocol B should leverage this infrastructure but with the discrimination-study statistical framework.

### Protocol A

Protocol A (lexical selectivity gate) remains a necessary but insufficient precondition. Even if Protocol A passes, Protocol B must use a different scoring procedure (Gate A/B/C, not `_bridge_matches()`).

---

## Status

```
Protocol B: DRAFT — 5 defects found, requires redesign
Phase 8 execution: BLOCKED
M-008: FULL_QUARANTINE
North Star: NOT ACHIEVED
```

The most important finding is B-1: the current discovery benchmark (`run_discovery_benchmark()`) tests entity intersection, not mechanism generation. The SCIENTIFIC_GATE_2_PROTOCOL.md explicitly states that entity intersection is NOT discovery. Protocol B must test the full pipeline.

The second most important finding is B-3: using `_bridge_matches()` as the scorer recreates the exact defect that invalidated the original Protocol A. Protocol B must use Gate A/B/C adjudication.
