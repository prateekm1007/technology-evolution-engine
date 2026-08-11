# NULL_1_SPECIFICATION — Arm C (Random Hypothesis Generator)

**Status:** FROZEN — immutable random null specification
**Date:** 2026-08-10
**Purpose:** The random null must be independently reproducible and genuinely incapable of exploiting source-pair structure.

---

## The Null-1 Question

> **What is the false-positive rate when candidates are generated randomly, with no access to the source-pair structure?**

If random candidates survive Gate A at a rate comparable to TEE, the measurement is uninterpretable — the gate is not discriminating.

---

## Design Principle

Null-1 must be:
1. **Independently reproducible** — same seed → same output
2. **Genuinely structure-incapable** — cannot exploit source-pair relationships
3. **Schema-equivalent** — produces the same output format as TEE
4. **Budget-equivalent** — same candidate budget (3 per case)

---

## Immutable Parameters

| # | Parameter | Value | Notes |
|---|-----------|-------|-------|
| 1 | Generator type | Uniform random sampling from frozen vocabulary | No LLM, no retrieval, no mechanism extraction. |
| 2 | Vocabulary source | Fixed scientific term list (1000 terms, frozen) | Terms drawn from general scientific vocabulary. NOT from the benchmark domains. |
| 3 | Vocabulary freeze | SHA-256 of vocabulary file recorded at freeze time | No vocabulary changes after freeze. |
| 4 | Seed | `SHA256(preregistration_id || case_id || "null1_random")` | Same seed logic as existing generation_null.py. Deterministic. |
| 5 | Candidate structure | 3 candidates per case (same budget as TEE) | {hypothesis, mechanism, prediction, falsifier, label} |
| 6 | Hypothesis generation | Random selection: 1 subject term + 1 relation verb + 1 object term | "subject relation object" format. |
| 7 | Mechanism generation | Random selection of 2-3 terms from vocabulary as "mechanism components" | No causal structure. |
| 8 | Prediction generation | Random number from uniform distribution [1, 100] + random unit from frozen unit list | Quantitatively meaningless. |
| 9 | Falsifier generation | Template: "If [random term] is not [random property], then the hypothesis is false" | Structurally valid but content-free. |
| 10 | Label assignment | Random: 50% ALLOW, 50% REJECT (seeded) | No reasoning. Pure chance. |
| 11 | Output schema | Same as TEE (b2-trace-v3 JSON) | For fair comparison through the gate. |
| 12 | Failure handling | If schema validation fails → NOT_ADJUDICATED_BY_B2 | Same as all arms. |

---

## Vocabulary Specification

The vocabulary is a frozen list of 1000 general scientific terms, NOT drawn from the benchmark domains. This ensures Null-1 cannot exploit domain-specific structure.

### Vocabulary Composition
- 300 physical terms (material, energy, force, etc.)
- 300 biological terms (organism, process, structure, etc.)
- 200 chemical terms (reaction, compound, etc.)
- 200 engineering terms (system, component, etc.)

### Vocabulary Freeze
- File: `NULL_1_VOCABULARY.txt` (to be created and SHA-256 locked)
- No terms added or removed after freeze
- Vocabulary is public and inspectable

---

## Why Null-1 Cannot Exploit Source-Pair Structure

1. **No source document access** — Null-1 does not receive Source A or Source B
2. **No mechanism extraction** — Null-1 does not extract mechanisms from any document
3. **No domain vocabulary** — Null-1's vocabulary is general scientific, not benchmark-specific
4. **No retrieval** — Null-1 cannot search for connections
5. **No reasoning** — Null-1 is pure random sampling

If Null-1 produces a candidate that survives Gate A, it is because the gate is too permissive, not because Null-1 discovered anything.

---

## Interpretability Requirement

Per the auditor's hardest requirement:

> **If the false-positive rate on matched-null/shuffled controls cannot be driven below the true-positive rate, the discovery measurement is uninterpretable.**

**Null-1 survival rate must be substantially below TEE survival rate.** If not:
- The adversarial gate is too permissive
- The novelty test is too weak
- The retrieval-negative test is too weak
- The entire Gate A measurement is uninterpretable

### Threshold (Frozen)
- If Null-1 survival rate ≥ TEE survival rate → **MEASUREMENT UNINTERPRETABLE**
- If Null-1 survival rate > 0 but < TEE → gate is discriminating, but has false-positive rate
- If Null-1 survival rate = 0 → gate is perfectly discriminating (may be too strict)

---

## Adversarial Gate

Null-1 output is run through the **SAME unchanged adversarial gate** as TEE. No special treatment.

---

## Freeze Status

**FROZEN.** All 12 parameters are immutable. Vocabulary file to be created and SHA-256 locked before execution.

---

## Preflight Checklist Update

| Item | Status Before | Status After |
|------|--------------|-------------|
| 7. Random generator (Arm C / Null 1) frozen | ⬜ NOT FROZEN | ✅ PASS (pending vocabulary file creation) |
