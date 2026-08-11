# DXP-005 — Gate Separation Addendum

**Date:** 2026-08-10
**Status:** ADDENDUM to DXP-005_FROZEN_DISCOVERY_PROTOCOL.md
**Purpose:** Explicitly separate evaluation into two gates per CTO direction. No rewrite of the existing protocol — this addendum locks the gate structure.

---

## The Rule (LOCKED)

> **DXP-005 can establish evidence for or against the discovery-generation mechanism. It cannot by itself establish that TEE is a genuine discovery machine.**

DXP-005 results alone **CANNOT** declare the North Star achieved. The North Star requires Gate B (independent confirmation), which is a separate, downstream operation.

**No victory declaration from DXP-005 results alone.**

---

## Why This Distinction Matters

The North Star is not merely "can TEE generate candidates?" It is whether TEE generates candidates that **beat serious controls and ultimately survive independent confirmation.**

If DXP-005's generator beats its null, that is an **internal benchmark victory** — not a discovery. The external auditor gave us the harder standard:

> **TEE must beat the strongest relevant control, especially a frontier LLM receiving the same raw information, and eventually demonstrate independently confirmed predictions.**

---

## Gate A — Discovery Discrimination

**What it tests:** Does TEE generate candidates that beat serious controls on blind inputs?

### Participants (identical blind inputs)
- **TEE** (full engine: extraction → abstraction → transfer → hypothesis generation → adversarial gate)
- **Null generator** (mechanism-null condition C — same structure, irrelevant edges)
- **Retrieval baseline** (TF-IDF/embedding-based, no mechanism pipeline — C3 from DXP-001)
- **Frontier-LLM baseline** (generic LLM with same raw documents, no mechanism extraction/abstraction pipeline — C2 from DXP-001)
- **Expert baseline** (human expert with only the two documents, no ground truth — C4 from DXP-004)

### Conditions
- Identical blind inputs for all participants
- Predictions locked before confirmation
- Novelty/retrieval/citation-graph tests applied
- **Complete failure accounting** (every candidate tracked: generated, survived, killed, why)

### Gate A Success (per case)
A candidate "passes Gate A" if:
1. TEE produces it (condition B)
2. The null generator (C) does NOT produce it
3. The retrieval baseline (C3) does NOT produce it
4. The frontier-LLM baseline (C2) does NOT produce it (or produces a weaker version)
5. It survives the unchanged adversarial gate
6. It is classified as NON_TRIVIAL_TRANSFER (not recoverable from inputs)

### Gate A Failure Modes
- TEE loses to frontier-LLM baseline → devastating but valuable early signal
- TEE beats null but loses to frontier-LLM → engine adds no value over raw LLM
- TEE beats all controls but candidate is PARAPHRASED_IN_INPUT → not novel
- TEE beats all controls, candidate is novel, but adversarial gate kills it → filter is the bottleneck
- TEE beats all controls, candidate survives, but is physically invalid → generator quality deficit

---

## Gate B — Discovery Validation

**What it tests:** Do Gate-A-surviving candidates survive independent confirmation?

### Gate B only runs on candidates that passed Gate A.

### Steps
1. **Specific falsifiable prediction** — the candidate must produce a quantitative, testable prediction
2. **Timestamped prediction lock** — prediction frozen before any confirmation attempt
3. **Independent confirmation** — the prediction is tested by an independent process (not the engine itself)
4. **Pre-registered experimental protocol** — where applicable, a physical/computational experiment is designed and executed
5. **Replication** — the result must replicate (not a single-shot fluke)
6. **Tier 0 → Tier 3 conversion rate** — track how many candidates progress through the epistemic tiers

### Gate B Success
A candidate "passes Gate B" if:
- Its prediction is confirmed by independent verification
- The result replicates
- The candidate progresses to ESTABLISHED status (not merely HYPOTHESIZED)

### Gate B Failure Modes
- Prediction is falsified by experiment → candidate killed (science working correctly)
- Prediction is confirmed but doesn't replicate → single-shot fluke
- No falsifiable prediction can be generated → candidate is not testable
- Prediction is too vague to test → candidate is not scientific

---

## The Relationship Between Gates

```
Gate A (Discrimination)          Gate B (Validation)
    │                                 │
    ├─ TEE vs null                    ├─ Falsifiable prediction
    ├─ TEE vs retrieval               ├─ Timestamped lock
    ├─ TEE vs frontier-LLM            ├─ Independent confirmation
    ├─ TEE vs expert                  ├─ Pre-registered experiment
    ├─ Adversarial survival           ├─ Replication
    ├─ Novelty test                   ├─ Tier 0 → Tier 3 conversion
    └─ Complete failure accounting    └─ ESTABLISHED status
         │                                 │
         ▼                                 ▼
    "TEE generates non-recoverable    "TEE's prediction is
     candidates that survive          independently confirmed"
     adversarial scrutiny"
         │                                 │
         ▼                                 ▼
    EVIDENCE FOR/AGAINST              GENUINE DISCOVERY
    DISCOVERY MECHANISM              (North Star)
```

---

## What DXP-005 Execution Produces

DXP-005 execution produces **Gate A evidence only**. Specifically:

1. **Generator vs. null comparison** (condition B vs. C) — does mechanism-graph preservation help?
2. **Generator vs. baseline** (condition B vs. A) — does the full pipeline add value?
3. **Adversarial gate behavior** — does the unchanged filter kill correct mechanisms?
4. **Novelty classification** — are candidates NON_TRIVIAL_TRANSFER?
5. **Quantitative predictions** — does the engine produce testable predictions?

**What DXP-005 does NOT produce:**
- Independent confirmation (Gate B)
- Replication
- ESTABLISHED status
- North Star achievement

---

## Victory Declaration Rules (LOCKED)

### DXP-005 results CAN support:
- "H-GEN-1 is supported/not supported as a discovery-generation mechanism"
- "The generator beats/loses to the null on known-positive recovery"
- "The adversarial gate kills/passes correct mechanisms at rate X"
- "The engine produces NON_TRIVIAL_TRANSFER candidates at rate Y"

### DXP-005 results CANNOT support:
- "TEE is a genuine discovery machine"
- "The North Star is achieved"
- "TEE discovers novel phenomena"
- "TEE beats frontier-LLM controls" (unless Gate A includes the frontier-LLM baseline, which DXP-005's current protocol does not — see note below)

### Important Note on Frontier-LLM Baseline

The current DXP-005 protocol tests conditions A/B/C (baseline, H-GEN-1, mechanism-null) but does NOT include a frontier-LLM baseline receiving the same raw documents. The frontier-LLM baseline (C2) was defined in DXP-001 but is not part of DXP-005's 3-condition design.

**For a complete Gate A evaluation, the frontier-LLM baseline should be added as a separate comparison arm.** This can be done without rewriting DXP-005 — it runs as an additional control alongside the existing A/B/C conditions, receiving the same 10 cases.

If the frontier-LLM baseline is NOT added, DXP-005 can only establish:
- Generator vs. null (internal comparison)
- NOT generator vs. frontier-LLM (external comparison)

The external comparison is the one that matters for the North Star.

---

## Authorization

**DXP-005 execution is authorized** with the following constraints:
1. The existing frozen protocol (3 conditions × 10 cases) runs as-is
2. No victory declaration from results alone
3. Gate A / Gate B separation is explicit in all reporting
4. The frontier-LLM baseline gap is documented (whether or not it is added)
5. All results are framed as "evidence for/against the discovery-generation mechanism," NOT "TEE is a discovery machine"

**Ad astra.**
