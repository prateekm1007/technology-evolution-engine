# RETRIEVAL_SPECIFICATION — Arm D (Retrieval Baseline)

**Status:** FROZEN — immutable retrieval control specification
**Date:** 2026-08-10
**Purpose:** The retrieval baseline must be genuinely adversarial. It cannot be a deliberately crippled opponent.

---

## The Retrieval Question

> **Can a strong retrieval system, given the same two source documents and a competitive query budget, produce the same candidates that TEE produces?**

If yes → TEE is not generating anything non-retrievable.
If no → TEE's candidates are genuinely non-retrievable (necessary but not sufficient for discovery).

---

## Same Searchable Universe

The retrieval baseline searches the **same universe** that TEE is implicitly competing against. This includes:

1. **The two source documents** (lexical + embedding search)
2. **A frozen external corpus** (scientific literature, if permitted by the benchmark)
3. **No deliberately crippled index** — the retrieval system gets a real, competitive setup

---

## Immutable Parameters

| # | Parameter | Value | Notes |
|---|-----------|-------|-------|
| 1 | Corpus | Source A + Source B + frozen external corpus (if benchmark permits) | Same documents TEE receives, plus any external corpus the benchmark specifies. |
| 2 | Lexical retrieval algorithm | BM25 with default parameters (k1=1.5, b=0.75) | Standard, well-tuned BM25. |
| 3 | Embedding model | `sentence-transformers/all-MiniLM-L6-v2` | Frozen. No model swaps. |
| 4 | Embedding index | FAISS IndexFlatIP (inner product) | Exact search, no approximate NN. |
| 5 | Query generation method | Three query types per case (see below) | Adversarial query formulation. |
| 6 | Number of queries per case | 9 (3 types × 3 variants) | Competitive budget. |
| 7 | Top-k per query | 10 | Retrieved passages per query. |
| 8 | Reranking | Cross-encoder reranking (`cross-encoder/ms-marco-MiniLM-L-6-v2`) | Competitive reranking. |
| 9 | External search allowance | If benchmark permits: search external corpus. If not: source documents only. | Determined by benchmark protocol. |
| 10 | Time budget | 60 seconds per case | Generous. Not a bottleneck. |
| 11 | Output budget | Top 3 candidates per case (same as TEE) | Same candidate budget as TEE. |
| 12 | Output schema | Same as TEE (b2-trace-v3) | For fair comparison. |
| 13 | Failure handling | If no candidates retrieved → NOT_ADJUDICATED_BY_B2 | Counted as failure. |
| 14 | Ranking configuration | Frozen at freeze time. No tuning after seeing results. | No post-hoc tuning. |

---

## Query Generation (Adversarial)

Three query types, three variants each = 9 queries per case:

### Type 1: Source-A mechanism queries
- `Q1a`: "What is the mechanism in Source A?"
- `Q1b`: "What causal process does Source A describe?"
- `Q1c`: "What is the key physical mechanism in Source A?"

### Type 2: Source-B problem queries
- `Q2a`: "What problem does Source B describe?"
- `Q2b`: "What challenge is addressed in Source B?"
- `Q2c`: "What is the target domain in Source B?"

### Type 3: Cross-source connection queries
- `Q3a`: "How might the mechanism in Source A apply to Source B?"
- `Q3b`: "What connection exists between Source A and Source B?"
- `Q3c`: "Can the mechanism from Source A solve the problem in Source B?"

### Entity-Expanded Variants
For each query, an entity-expanded variant is also generated using spaCy NER (`en_core_web_sm`, frozen) to extract entities from both sources and add them to the query.

---

## Retrieval-Negative Definition (Frozen)

A candidate is **retrieval-negative** if and only if:

1. None of the 9 queries (plus entity-expanded variants) retrieve a passage that, when processed by the same LLM used for C2, produces the same candidate
2. The cross-encoder reranker does not rank any retrieved passage above threshold 0.5 for relevance to the candidate
3. No passage in the top-k results across all queries contains the candidate's core mechanism

**"Retrieval-negative" means the candidate was not found by any retrieval path.** It does NOT mean the candidate is novel (that's the novelty test). It means retrieval could not produce it.

---

## What Retrieval Tests

| If retrieval result | Interpretation |
|--------------------|---------------|
| Retrieval ≈ TEE | TEE is not generating anything non-retrievable. |
| Retrieval < TEE | TEE produces candidates retrieval cannot find. Necessary for discovery. |
| Retrieval > TEE | TEE is WORSE than retrieval. Architecture is harmful. |

---

## Adversarial Gate

Retrieval's output is run through the **SAME unchanged adversarial gate** as TEE. No special treatment.

---

## Freeze Status

**FROZEN.** All 14 parameters are immutable.

---

## Preflight Checklist Update

| Item | Status Before | Status After |
|------|--------------|-------------|
| 5. Retrieval (Arm D) frozen | ⬜ NOT FROZEN | ✅ PASS |
| 14. Retrieval-negative definition frozen | ⬜ NOT FROZEN | ✅ PASS |
