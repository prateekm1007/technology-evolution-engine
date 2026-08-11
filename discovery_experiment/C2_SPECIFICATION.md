# C2_SPECIFICATION — Arm E (Frontier LLM)

**Status:** FROZEN — immutable control specification
**Date:** 2026-08-10
**Purpose:** The frontier LLM is the strongest general-model control. It must be adversarially strong, not a straw man.

---

## The C2 Question

> **Can the entire TEE system outperform a strong model given the same raw external evidence, despite TEE's additional machinery?**

This is a **product-level test**. C2 receives ONLY the two source documents and the candidate prompt. TEE receives the same documents plus its entire architecture. The question is whether TEE's machinery adds end-to-end value.

---

## Immutable Parameters

| # | Parameter | Value | Notes |
|---|-----------|-------|-------|
| 1 | Model identifier | `z-ai/glm-4.7-flash` | Frontier-class GLM model available via OpenRouter. NOT glm-4-plus (that is TEE's frozen instrument). C2 is a DIFFERENT model — this is intentional. |
| 2 | Provider | OpenRouter (`https://openrouter.ai/api/v1`) | Same provider used in three-arm experiment. |
| 3 | Model version | `glm-4.7-flash` (OpenRouter model ID) | Frozen at this exact identifier. No silent version changes. |
| 4 | System prompt | See below (verbatim) | Frozen verbatim. No modifications after freeze. |
| 5 | User prompt | See below (verbatim) | Frozen verbatim. No modifications after freeze. |
| 6 | Temperature | `0.7` | Same as TEE's hypothesis generation. Fair comparison. |
| 7 | Top-p | `1.0` (default) | No nucleus sampling restriction. |
| 8 | Max tokens | `8192` | Sufficient for detailed hypothesis output. |
| 9 | Reasoning configuration | `reasoning: { enabled: false, exclude: true }` | GLM-4.7-flash is a reasoning model; reasoning disabled to match TEE's `thinking: { type: 'disabled' }`. |
| 10 | Tool access | `NONE` | No function calling, no tools, no code execution. |
| 11 | Retrieval access | `NONE` | No RAG, no web search, no browsing. |
| 12 | External browsing | `PROHIBITED` | Model cannot access the internet. |
| 13 | Context window | `202,752` tokens (model max) | Sufficient for any problem. |
| 14 | Retry policy | `3 retries on failure; fall back to NOT_ADJUDICATED` | Same as TEE's frozen detector. |
| 15 | Number of samples | `5` (N=5 majority vote) | Same as TEE. Fair comparison. |
| 16 | Voting procedure | Majority vote (same as TEE) | Ties counted as failures. |
| 17 | Output schema | `b2-trace-v3` (same as TEE) | C2 must produce the same schema as TEE for fair comparison. |
| 18 | Failure handling | `NOT_ADJUDICATED_BY_B2` fallback | Same as TEE. Failures counted as failures. |
| 19 | Input serialization | See below (exact format) | Frozen verbatim. |

---

## System Prompt (Frozen Verbatim)

```
You are an expert scientific reasoning system. Your task is to analyze two source documents and generate a hypothesis about how a mechanism from Source A could apply to a problem described in Source B.

You must:
1. Identify the key mechanism in Source A
2. Identify the key problem in Source B
3. Generate a hypothesis connecting them
4. Provide a quantitative prediction
5. Provide a falsifier (an experimental test that could disprove the hypothesis)
6. Classify the hypothesis as ALLOW (genuine cross-source synthesis) or REJECT (source-local paraphrase or no real connection)

Output ONLY a JSON object with this schema:
{
  "hypothesis": "string describing the proposed mechanism transfer",
  "mechanism": "the specific causal mechanism from Source A",
  "prediction": "quantitative prediction with units",
  "falsifier": "experimental test that could disprove this",
  "label": "ALLOW" or "REJECT",
  "reasoning": "brief explanation"
}
```

## User Prompt (Frozen Verbatim)

```
CASE ID: {case_id}

SOURCE A:
{source_a}

SOURCE B:
{source_b}

CANDIDATE PROBLEM: How might the mechanism in Source A apply to the problem in Source B?

Generate a hypothesis. Output ONLY the JSON object.
```

## Input Serialization (Frozen)

```json
{
  "model": "z-ai/glm-4.7-flash",
  "messages": [
    {"role": "system", "content": "<system prompt above>"},
    {"role": "user", "content": "<user prompt above with case_id, source_a, source_b substituted>"}
  ],
  "max_tokens": 8192,
  "temperature": 0.7,
  "top_p": 1.0,
  "reasoning": {"enabled": false, "exclude": true}
}
```

---

## Information Equivalence

C2 receives EXACTLY the same information as TEE's final hypothesis-generation stage:
- Source document A (verbatim)
- Source document B (verbatim)
- The candidate problem prompt

C2 does NOT receive:
- Mechanism graphs
- Ontology
- Adversarial analysis
- Retrieval results
- Novelty firewall output
- Historical patterns
- Any TEE-internal processing

**This is intentionally a product-level test.** The question is whether TEE's entire pipeline adds value over a strong model given the same raw inputs.

---

## Adversarial Gate

C2's output is run through the **SAME unchanged adversarial gate** as TEE (`engine/adversarial_analysis.py`). No special treatment. No relaxed criteria.

---

## What C2 Tests

| If C2 result | Interpretation |
|-------------|---------------|
| C2 ≈ TEE | TEE's architecture adds no value over raw LLM. Devastating. |
| C2 < TEE | TEE's architecture adds value. Degree of improvement matters. |
| C2 > TEE | TEE's architecture is WORSE than raw LLM. Architecture is harmful. |

---

## What C2 Does NOT Test

- Whether TEE's individual components contribute (that's an ablation, not Gate A)
- Whether TEE is a "discovery machine" (that's Gate B)
- Whether the mechanism is correct (that's ground-truth comparison)

---

## Freeze Status

**FROZEN.** All 19 parameters are immutable. No changes after this freeze. Any modification requires a new specification (C2_V2) and re-freeze.

---

## Preflight Checklist Update

| Item | Status Before | Status After |
|------|--------------|-------------|
| 4. Frontier LLM (Arm E) frozen | ⬜ NOT FROZEN | ✅ PASS |
