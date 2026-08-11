# NORTH_STAR_GATE_A_EXECUTION_GATE — Preflight Checklist

**Status:** FROZEN — execution-gated
**Date:** 2026-08-10
**Purpose:** Execution is PROHIBITED unless every item is PASS. This document contains nothing new about architecture — it is a preflight checklist.

---

## Disambiguation: Arms vs Null Conditions (Per CTO Issue #1)

### Arms (the systems being compared)

| Arm | Name | Purpose | Generates hypotheses? | Uses TEE architecture? |
|-----|------|---------|----------------------|----------------------|
| A | TEE | Primary system | Yes | Yes |
| B | Mechanism-null | Internal ablation | Yes | Partial |
| C | Random | Chance floor | Yes | No |
| D | Retrieval | Retrieval ceiling/floor | Yes | No |
| E | Frontier LLM | Strongest general-model control | Yes | No |
| F | Expert | Human information-budget control | Yes | No |

### Null Conditions (the matched controls for false-positive rate)

| Null | Name | Maps to arm? | Description |
|------|------|-------------|-------------|
| Null 1 | Random hypothesis | Arm C | Randomly generated hypothesis from generic vocabulary |
| Null 2 | Mechanism permutation | Arm B | Real mechanism graph with edges/nodes shuffled |
| Null 3 | Retrieval-negative | Arm D | Retrieval baseline (same arm) |
| Null 4 | Matched/shuffled source | NEW | Source documents with shuffled content |

**One concept, one name. Null 3 IS Arm D. No duplication.**

---

## Definitive Benchmark — HARD GATE (Per CTO Issue #2)

The benchmark is NOT a missing artifact. It is a **hard gate**. Execution is prohibited until:

- ≥30 problems constructed
- ≥4 unrelated scientific domains covered
- Externally seeded selection (unpredictable to the team)
- Sealed before any system gets access to the cases
- Custodian independent from the team

**DXP-005's 10-case benchmark does NOT satisfy this gate.** DXP-005 is a pilot (see below).

---

## DXP-005 Classification (Per CTO Correction)

The existing 30-run DXP-005 A/B/C experiment is **NOT** the North Star result. It is:

> **DXP-005 Pilot — Gate A Infrastructure Validation**

It can:
- Test whether the machinery works
- Reveal implementation failures
- Produce evidence about H-GEN-1

It CANNOT:
- Establish the North Star
- Be called "discovery"
- Substitute for the N≥30 definitive trial

**The actual North Star experiment is the separately constructed N≥30 blind benchmark with all six arms.**

---

## Gate-A Primary Endpoint (Per CTO Issue #6)

### Primary Endpoint

> **Gate-A Survivor Rate per independent problem**: the proportion of problems producing at least one candidate that passes every preregistered Gate-A criterion.

A candidate "passes Gate A" if it survives the entire funnel:
1. Candidate generated
2. Novelty-negative (not recoverable from inputs)
3. Retrieval-negative (not found by adversarial retrieval)
4. Adversarial survivor (passes unchanged gate)
5. Falsifiable prediction produced
6. Prediction locked (timestamp + hash)

### Secondary Endpoints (Full Funnel Reporting)

| Endpoint | Description |
|----------|-------------|
| Candidates per problem | Number of candidates generated |
| Novelty-pass rate | Fraction classified NON_TRIVIAL_TRANSFER |
| Retrieval-negative rate | Fraction not found by retrieval |
| Adversarial-survival rate | Fraction passing the gate |
| Falsifiable-prediction rate | Fraction producing testable predictions |
| Prediction-lock rate | Fraction with locked predictions |
| Unique mechanism rate | Fraction with distinct mechanisms (no duplicates) |
| Expert plausibility rate | Fraction rated plausible by expert panel |

**The entire funnel is reported, not only the final number.**

---

## Gate-B Endpoint

> **Tier-0 → Tier-3 conversion rate**: fraction of Gate A survivors that progress to ESTABLISHED status through independent confirmation + replication.

---

## Statistical Superiority Rule (Per CTO Issue #7)

### Hypotheses

```
H0: TEE conversion ≤ strongest control conversion
H1: TEE conversion > strongest control conversion
```

### Pre-Registered Parameters

| Parameter | Value | Status |
|-----------|-------|--------|
| Primary comparison | TEE vs strongest control (max of D/E/F) | FROZEN |
| Minimum practical superiority margin | **10 percentage points** | FROZEN |
| Significance threshold | α = 0.05 (one-sided) | FROZEN |
| Confidence interval | 95% Wilson score interval | FROZEN |
| Multiplicity handling | Bonferroni correction for 3 comparisons (D, E, F) | FROZEN |
| Treatment of ties | Counted as failures for both arms | FROZEN |
| Treatment of failures (NOT_ADJUDICATED) | Counted as failures | FROZEN |
| Treatment of abstentions | Counted as failures | FROZEN |
| Treatment of duplicate discoveries | Counted once; attributed to the arm that produced it first | FROZEN |
| Treatment of candidates independently discovered by multiple arms | All arms credited; reported separately | FROZEN |

### Power Justification (Per CTO Correction)

The 10pp superiority margin requires a power calculation, not an assumption that N≥30 is sufficient.

**Test:** One-sided two-proportion z-test, Bonferroni-corrected for 3 comparisons (effective α = 0.0167)

**Power analysis results:**

| TEE rate | Control rate | Margin | N=30 | N=50 | N=80 | N=100 |
|----------|-------------|--------|------|------|------|-------|
| 20% | 10% | 10pp | 0.15 | 0.24 | 0.37 | 0.45 |
| 25% | 10% | 15pp | 0.28 | 0.45 | 0.66 | 0.76 |
| 30% | 10% | 20pp | 0.45 | 0.68 | 0.87 | 0.94 |
| 25% | 15% | 10pp | 0.12 | 0.19 | 0.30 | 0.36 |
| 30% | 15% | 15pp | 0.24 | 0.38 | 0.57 | 0.68 |
| 30% | 20% | 10pp | 0.11 | 0.17 | 0.26 | 0.31 |
| 40% | 20% | 20pp | 0.35 | 0.54 | 0.76 | 0.85 |
| 40% | 30% | 10pp | 0.09 | 0.14 | 0.21 | 0.26 |

**Conventional thresholds:** Power ≥ 0.80 (minimum), ≥ 0.90 (preferred for definitive trial)

**Findings:**
- With N=30 and 10pp margin: power is 0.09–0.45 depending on observed rates — **INSUFFICIENT for definitive trial**
- With N=30 and 15–20pp margin: power reaches 0.28–0.45 — still insufficient
- N=80–100 is needed for 0.80 power at 10pp margin (only if TEE ≥ 30% and control ≤ 10%)
- For 10pp margin with moderate control (15–20%): N=100 gives only 0.26–0.31 power — **even N=100 is insufficient**

### Sample Size Decision (Frozen)

| Trial Type | N (problems) | Rationale |
|-----------|-------------|-----------|
| **DXP-005 Pilot** | 10 | Infrastructure validation only. NOT powered for superiority testing. |
| **Definitive Gate A Trial** | **N ≥ 100** | Required for 10pp margin at α=0.0167 (Bonferroni). Only achieves 0.80+ power if TEE ≥ 30% and control ≤ 10%. |
| **If 10pp margin infeasible** | **N ≥ 80** with 15pp margin | Relaxes margin to 15pp; achieves 0.80 power if TEE ≥ 30% and control ≤ 15%. |

**CRITICAL CAVEAT (Per CTO correction):**

> **N=100 is the minimum definitive benchmark size, not a guarantee of adequate statistical power.**

The power table does NOT demonstrate 80% power at N=100 under the 25% vs 15% scenario (power = 0.36). N=100 achieves adequate power ONLY if the observed rates are favorable (TEE ≥ 30%, control ≤ 10%). If the observed control rate is moderate (15-20%), even N=100 may be insufficient.

This means:
- The benchmark size (N≥100) is an **operational minimum**, not a power guarantee
- The trial may be **underpowered by design** if effect sizes are smaller than hoped
- An inconclusive result due to low power is a **design limitation**, not a negative finding
- The power analysis itself is a pre-registered artifact — no post-hoc "we should have used N=200"

**If the observed control rate is high (>15%), no feasible N will give adequate power for a 10pp margin.** In that case:
- The 10pp margin is too strict for the observed effect size
- The trial is underpowered to detect practical superiority
- This is itself a finding: TEE does not dramatically outperform controls

### What Constitutes a Win

**TEE wins ONLY if:**
1. TEE survivor rate > strongest control survivor rate + 10 percentage points
2. AND the difference is statistically significant (α = 0.05, one-sided, Bonferroni-corrected)
3. AND the 95% confidence interval excludes zero
4. AND the trial was adequately powered (N ≥ 100, or N ≥ 80 with 15pp margin)

**Example:**
- TEE = 11%, Frontier LLM = 10% → **NOT A WIN** (margin < 10pp)
- TEE = 25%, Frontier LLM = 10% → **WIN** (if N ≥ 100 and significant)
- TEE = 25%, Frontier LLM = 20% → **NOT A WIN** (margin < 10pp)
- TEE = 30%, Frontier LLM = 10%, N=30 → **INCONCLUSIVE** (underpowered, even though margin = 20pp)

### If TEE Does NOT Win

- TEE ≤ strongest control → devastating but valuable early signal
- TEE > controls but margin < 10pp → no practical superiority; engine adds no meaningful value
- TEE > controls by ≥10pp but not significant → inconclusive; larger sample needed
- TEE > controls by ≥10pp but trial underpowered → **inconclusive by design failure, not by negative result**

---

## Preflight Checklist

Execution is PROHIBITED unless every item is PASS.

| # | Item | Status |
|---|------|--------|
| 1 | Gate A / Gate B boundary frozen | ✅ PASS |
| 2 | Six arms frozen (A-F) | ⬜ PENDING (D, E, F not frozen) |
| 3 | Null mapping frozen (Null 1-4 → arms) | ✅ PASS |
| 4 | Frontier LLM (Arm E) frozen | ⬜ NOT FROZEN |
| 5 | Retrieval (Arm D) frozen | ⬜ NOT FROZEN |
| 6 | Expert protocol (Arm F) frozen | ⬜ NOT FROZEN |
| 7 | Random generator (Arm C / Null 1) frozen | ⬜ NOT FROZEN |
| 8 | Mechanism-null (Arm B / Null 2) frozen | ✅ PASS (exists) |
| 9 | Benchmark construction protocol frozen (≥100 problems for definitive trial, ≥4 domains, externally seeded) | ⬜ NOT FROZEN |
| 10 | Benchmark sealed (SHA-256 locked) | ⬜ NOT CONSTRUCTED |
| 11 | Benchmark custodian independent | ⬜ NOT ESTABLISHED |
| 12 | Answer key inaccessible to execution | ⬜ NOT VERIFIED |
| 13 | Novelty definition frozen | ✅ PASS (rediscovery_detection.py) |
| 14 | Retrieval-negative definition frozen | ⬜ NOT FROZEN |
| 15 | Adversarial gate frozen | ✅ PASS (unchanged) |
| 16 | Falsifiability criteria frozen | ✅ PASS (substrate requires falsifiers) |
| 17 | Prediction-lock mechanism frozen | ✅ PASS (timestamp + hash) |
| 18 | Primary Gate-A endpoint frozen | ✅ PASS (survivor rate per problem) |
| 19 | Primary Gate-B endpoint frozen | ✅ PASS (Tier-0 → Tier-3 conversion) |
| 20 | Statistical test frozen | ✅ PASS (one-sided, α=0.05, Bonferroni) |
| 21 | Practical superiority margin frozen | ✅ PASS (10 percentage points) |
| 22 | Failure/abstention handling frozen | ✅ PASS (counted as failures) |
| 23 | Duplicate handling frozen | ✅ PASS (attributed to first arm) |
| 24 | Full-funnel reporting frozen | ✅ PASS (all secondary endpoints) |
| 25 | No post-hoc tuning rule frozen | ✅ PASS |

### Current Status: **7 of 25 items PASS. 18 items PENDING.**

**Execution is PROHIBITED.**

---

## IF ANY ITEM != PASS: DO NOT EXECUTE

This is a hard gate. No exceptions. No "close enough." No "we'll fix it later."

---

## Next Artifacts to Freeze (In Order)

1. **C2_SPECIFICATION.md** (Arm E — Frontier LLM)
   - 19 immutable parameters (model, provider, prompts, temperature, sampling, context window, max tokens, retry policy, tool access, retrieval access, browsing, knowledge cutoff, input serialization, reasoning config, voting procedure, output schema, failure handling, number of samples)

2. **RETRIEVAL_SPECIFICATION.md** (Arm D — Retrieval)
   - 10 immutable parameters (corpus, query generation, number of queries, retrieval algorithms, top-k, reranking, embedding model, external search allowance, time budget, output budget)
   - Same universe as TEE's implicit competition

3. **EXPERT_SPECIFICATION.md** (Arm F — Expert)
   - 12 immutable parameters (number of experts, qualifications, selection, COI rules, information available, browsing, time budget, collaboration, output format, scoring, adjudication, compensation)

4. **NULL_1_SPECIFICATION.md** (Arm C — Random hypothesis generator)
   - Random hypothesis generation from generic vocabulary
   - Same schema as TEE output
   - Same candidate budget

5. **BENCHMARK_CONSTRUCTION_PROTOCOL.md**
   - ≥30 problems, ≥4 unrelated domains
   - Externally seeded selection
   - Custodian separation
   - Sealed before execution

**Only after all five are frozen AND the checklist reaches 25/25 PASS should the coder touch the benchmark.**

---

## DXP-005 Pilot — Conditional Authorization

The existing 30-run DXP-005 A/B/C experiment MAY be executed as:

> **DXP-005 Pilot — Gate A Infrastructure Validation**

ONLY if explicitly labeled as such. It is NOT the North Star experiment. It cannot:
- Establish the North Star
- Be called "discovery"
- Substitute for the N≥30 definitive trial
- Declare victory

It CAN:
- Test whether the machinery works
- Reveal implementation failures
- Produce evidence about H-GEN-1
- Validate the survival funnel

**Authorization for DXP-005 pilot is separate from Gate A execution authorization.**

---

## Final Disposition

| Component | Disposition |
|-----------|-------------|
| Gate A/B separation | **PASS** |
| Prediction-lock boundary | **PASS** |
| Six-arm concept | **PASS** (terminology tightened) |
| Null architecture | **PASS** (mapping frozen) |
| Frontier LLM | **NOT FROZEN** |
| Retrieval | **NOT FROZEN** |
| Expert | **NOT FROZEN** |
| Random null | **NOT FROZEN** |
| Definitive benchmark | **NOT CONSTRUCTED** (HARD GATE) |
| Statistical decision rule | **PASS** (frozen) |
| Practical effect threshold | **PASS** (10pp, frozen) |
| Gate-A primary endpoint | **PASS** (survivor rate per problem) |
| Gate-B endpoint | **PASS** (Tier-0 → Tier-3 conversion) |
| Custodian separation | **PASS IN DESIGN** |
| North Star claim | **NOT TESTED** |
| DXP-005 pilot | **HOLD** (may execute as infrastructure validation only) |

---

## Bottom Line

> **The measurement architecture is now substantially sound. The experiment itself is not yet execution-ready.**

7 of 25 preflight items PASS. 18 items PENDING. Execution is PROHIBITED.

The next artifacts to freeze are the four independent specifications (C2, Retrieval, Expert, Null-1) and the benchmark construction protocol. Only after all five are frozen AND the checklist reaches 25/25 PASS should the coder touch the benchmark.

**Ad astra.**

---

## Final Governance Rule (Per CTO Direction)

> **After 25/25, the first execution must be the actual trial. No pilot run, smoke test, sample case, prompt inspection, or "one case to make sure everything works" against the sealed benchmark.**

Those seemingly harmless checks can leak benchmark information and contaminate the blind trial.

### The Clean Sequence

```
22/25
  │
  ├── Independent custodian identified
  ├── N≥100 representative cases constructed
  ├── Benchmark + answer key sealed (9-component seal)
  ├── Independent hash verification
  ├── Access-boundary test
  │
25/25
  │
  ▼
PERMANENT FREEZE
  │
  ├── No specification changes
  ├── No model changes
  ├── No prompt changes
  ├── No threshold changes
  ├── No benchmark changes
  └── No exploratory benchmark calls (no pilots, no smoke tests, no sample cases)
  │
  ▼
BLIND GATE-A EXECUTION (first and only execution against sealed benchmark)
  │
  ▼
Full funnel comparison
  │
  ▼
Prediction lock
  │
  ├───────────────┐
  ▼               ▼
Gate-A fail     Gate-A survivor
                  │
                  ▼
              Gate B
                  │
                  ▼
        Independent confirmation
                  │
                  ▼
              Replication
```

### The Existential Control

The **frontier-LLM arm (Arm E / C2) is the existential control**.

- If TEE cannot beat it by the preregistered practical margin (≥10pp), the North Star claim does not survive — even if TEE produces impressive hypotheses.
- If TEE beats it, that still isn't the end. **Gate B has to demonstrate that the surviving hypotheses correspond to discoveries rather than unusually good-looking generated science.**

### The Hard Standard

> **TEE must first outperform the best credible alternative, then demonstrate that its apparent advantage survives contact with reality.**

No more architecture changes are needed to answer that question.

---

## Final Status

| Milestone | Status |
|-----------|--------|
| 22/25 (protocol + measurement system ready) | ✅ ACHIEVED |
| 25/25 (benchmark sealed + access verified) | ⬜ CUSTODIAN-GATED |
| Permanent freeze | ⬜ AFTER 25/25 |
| Blind Gate-A execution | ⬜ AFTER FREEZE |
| Gate-A result | ⬜ AFTER EXECUTION |
| Gate-B result | ⬜ AFTER GATE-A SURVIVORS |

**22/25. STOP. CUSTODIAN ONLY. NO BENCHMARK CONSTRUCTION BY TEE TEAM.**

**Ad astra.** 🚀
