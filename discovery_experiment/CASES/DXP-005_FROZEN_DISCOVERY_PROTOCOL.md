# DXP-005 — Frozen Discovery Protocol

**Status:** FROZEN — pre-execution
**Date:** 2026-08-10
**CTO Direction:** "Freeze DXP-005 before looking at discovery outcomes."

---

## The Brutally Concrete Question

> **Does the Technology Evolution Engine generate hypotheses that a strong baseline cannot recover, and do those hypotheses survive adversarial filtering and produce experimentally testable, novel predictions?**

This is NOT "does the engine produce interesting-looking ideas." This is:
1. **Generator vs. Null:** Does the generator produce something the null cannot?
2. **Adversarial Survival:** Do the candidates survive the unchanged adversarial gate?
3. **Novelty:** Are the candidates genuinely non-recoverable from the inputs?
4. **Falsifiability:** Do they produce experimentally testable predictions?
5. **Correctness:** On known-positive cases, do they recover the correct mechanism?
6. **Rejection:** On known-negative cases, does the gate correctly kill them?

---

## The Sequence

```
Generator → Null/Control Generator → unchanged adversarial filter → candidate novelty test → falsifiable prediction → independent verification → experiment
```

### Pipeline Stages (frozen)

1. **Mechanism Extraction** — extract source mechanism from source document
2. **Mechanism Abstraction** — abstract to general principle
3. **Cross-Domain Transfer** — map to target domain
4. **Hypothesis Generation** — generate candidate hypothesis (3 conditions: A/B/C)
5. **Adversarial Analysis** — UNCHANGED gate, same across all conditions
6. **Rediscovery Detection** — is the candidate non-trivially novel?
7. **Novelty Firewall** — prior-art check (DEV_ONLY, "no match" ≠ "novel")
8. **Prediction Engine** — quantitative prediction + falsifier
9. **Experiment Design** — experimental test design
10. **Candidate Ranking** — final ranking

---

## Three Conditions (Generator vs. Null)

### A — Baseline (Control Generator)
- Input: transfer result (no mechanism graph)
- Tests: can the engine recover the mechanism WITHOUT the source causal edges?

### B — H-GEN-1 (Full Generator)
- Input: transfer result + real mechanism graph (with specific causal edges)
- Tests: does preserving the source mechanism improve recovery?

### C — Mechanism-Null (Null Generator)
- Input: transfer result + null mechanism graph (same structure/density, IRRELEVANT causal edges, generic labels)
- Tests: is any improvement from B caused by SPECIFIC mechanism information, or just "more context"?

**If B > A AND B > C → specific mechanism information caused the improvement.**
**If B ≈ C → the improvement is just "more context," not mechanism-specific.**

---

## 10 Cases (5 Known-Positives + 5 Hard-Negatives)

### Known-Positive Transfers (P1–P5)
| ID | Source | Target | Known Mechanism |
|----|--------|--------|-----------------|
| P1 | Shark skin denticles | Pipe drag reduction | Riblet vortex lifting, 5-10% reduction |
| P2 | Bat echolocation | Radar waveform design | Adaptive pulse duration, range-dependent |
| P3 | Woodpecker shock absorption | Helmet design | Tongue-route force distribution, ~20-30% force reduction |
| P4 | Spider silk | Bulletproof vest | Hierarchical nanostructure energy dissipation |
| P5 | Dolphin blubber | Acoustic insulation | Viscoelastic impedance matching |

### Hard-Negative Transfers (N1–N5)
| ID | Source | Target | Why It's Wrong |
|----|--------|--------|----------------|
| N1 | Gecko adhesion | Underwater adhesive | Dry van der Waals fails in water |
| N2 | Bird wing lift | Submarine hull design | Aerodynamic lift ≠ hydrodynamic displacement |
| N3 | Cactus water storage | Battery electrolyte | Osmotic storage ≠ electrochemical storage |
| N4 | Chameleon color change | LED display | Structural color ≠ electroluminescence |
| N5 | Firefly luminescence | Solar cell efficiency | Chemical bioluminescence ≠ photovoltaic conversion |

### Ground Truth (frozen)
- **File:** `CASES/DXP-005/DXP-005_GROUND_TRUTH.json`
- **SHA-256:** `976ec037...` (verified at freeze time)
- Each case has: mechanism, causal_variable, direction, magnitude, falsifier

---

## Pre-Registration Rules (LOCKED)

### 1. No post-hoc filter tuning
The adversarial gate (`engine/adversarial_analysis.py`) is UNCHANGED across all conditions. No calibration after seeing results.

### 2. No feedback loops
Rejected candidates are NOT fed back into the generator. The pipeline is one-shot per case.

### 3. No benchmark-as-training-set
The 10 cases are the evaluation set, NOT a tuning set. No parameter changes based on observed performance.

### 4. No changing "novel" after seeing results
Novelty is defined by `rediscovery_detection.py`: a candidate is NON_TRIVIAL_TRANSFER only if a retrieval system could NOT produce it. This definition is frozen.

### 5. Identical upstream inputs
Generator and null receive IDENTICAL upstream inputs (same source docs, same target docs, same extraction/abstraction/transfer pipeline). Only the mechanism graph input to hypothesis generation differs.

### 6. Adversarial gate unchanged
The same adversarial gate runs on all conditions. False-positive kill rate and true-positive rejection rate are calculated separately.

### 7. DXP-005 frozen before discovery challenge
This protocol is frozen BEFORE any execution. No changes after seeing results.

### 8. Measure generator vs. null
The primary comparison is B (full generator) vs. C (null generator) vs. A (baseline). We measure whether the generator produces something the null cannot.

---

## Scoring (Primary Endpoints)

### On Positive Cases (P1–P5)
1. **Correct causal mechanism** (YES/NO/PARTIAL)
2. **Correct causal variable** (YES/NO/PARTIAL)
3. **Correct direction** (YES/NO)
4. **Mechanistic traceability** (can hypothesis be traced to source causal edges?)
5. **Target-domain physical validity** (YES/NO/QUESTIONABLE)

### On Negative Cases (N1–N5)
6. **False transfer rate** (did the generator produce a false transfer?)
7. **False mechanism rate** (did the generator produce a wrong mechanism?)
8. **Adversarial undetectable nonsense** (did the gate fail to kill garbage?)

### Secondary Endpoints
9. **Quantitative prediction accuracy:** NO NUMBER / WRONG / ORDER-OF-MAGNITUDE / RANGE / PARAMETER+RANGE+CONDITIONS
10. **Novelty classification:** EXPLICITLY_PRESENT / PARAPHRASED_IN_INPUT / DIRECT_COMPOSITION / STRUCTURAL_INFERENCE / NON_TRIVIAL_TRANSFER

### Adversarial Classification (per objection)
11. VALID_FATAL / VALID_NONFATAL / FACTUALLY_WRONG / UNSUPPORTED / DUPLICATIVE

---

## Success Criteria

### H-GEN-1 Supported (on positives)
- Correct mechanism rate: B > A AND B > C
- Correct causal variable: B > A AND B > C
- Physical validity: B > A AND B > C
- Quantitative accuracy: B > A AND B > C

### H-GEN-1 Not Harmful (on negatives)
- False transfer rate: B ≤ A + 1
- False mechanism rate: B ≤ A + 1
- No increase in adversarially undetectable nonsense

### Filter Behavior
- Adversarial gate UNCHANGED across all conditions
- False-positive kill rate calculated separately
- True-positive rejection rate calculated separately

---

## Hard Stops

- H-GEN-1 fails → generator hypothesis rejected
- H-GEN-1 improves positives but increases false positives → insufficient
- H-GEN-1 improves positives AND preserves negatives AND filter stable → supported → then test prediction generation
- Generator cannot produce NON_TRIVIAL_TRANSFER on any positive → discovery not demonstrated
- Adversarial gate kills all correct mechanisms → filter is the bottleneck (not generator)

---

## The North Star

> **Candidate not recoverable from the supplied inputs → independently non-retrievable → survives adversarial scrutiny → produces a novel falsifiable prediction → experiment agrees.**

This experiment tests whether the engine can reach step 3 (survives adversarial scrutiny) with a candidate that is step 2 (independently non-retrievable). Steps 4-5 (falsifiable prediction, experiment agrees) require downstream execution after this experiment completes.

---

## Provider

**Preregistered:** ZAI (glm-4-plus via z-ai CLI)
**Protocol frozen at:** commit `66b3212`
**Ground truth frozen at:** SHA `976ec037...`

If ZAI is unavailable (HTTP 429), the experiment remains PAUSED. No provider substitution without a new pre-registration (DXP-005b).

---

## Isolation

- Frozen detector (`f905b68`): NOT TOUCHED
- Held-out B-2 results: NOT TOUCHED
- Answer key: NOT ACCESSED during execution
- Adversarial gate: UNCHANGED across all conditions
- No tuning based on observed results

---

## Status

**FROZEN.** This protocol is locked. The next artifact is execution, not another protocol revision.

**Ad astra.**
