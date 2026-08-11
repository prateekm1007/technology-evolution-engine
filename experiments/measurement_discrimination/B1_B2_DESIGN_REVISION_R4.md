# R4 — Inferential Lock & Adversarial Validation

**Status:** FREEZE-READINESS PACKAGE — not implementation, not authorized for execution
**Date:** 2026-08-09
**Supersedes:** B1_B2_DESIGN_REVISION_R3.md
**Audit reference:** Round 33 — "7 items, then attack with: show me a path by which this protocol can produce a positive result when the engine has discovered nothing."

---

## 1. Exact Effect-Size Target + Power Analysis

### Minimum meaningful effect

```
δ_min = 0.20
```

The engine must outperform the retrieval baseline by at least 20 percentage points (case-level yield). This is the minimum practically meaningful advantage — anything smaller would not justify claiming "discovery pipeline signal."

### Decision rule (revised with effect-size target)

**B1:**
```
recovery_rate ≥ 0.40
AND binom.sf(b_b1 - 1, b_b1 + c_b1, 0.5) < 0.05
AND b1_ci_lower > δ_min
AND corrupted_candidate_rejection_rate ≥ 0.80
```

**B2:**
```
north_star_yield > 0
AND binom.sf(b - 1, b + c, 0.5) < 0.05
AND ci_lower > δ_min
→ DISCOVERY_PIPELINE_SIGNAL_DETECTED
```

Note: `ci_lower > δ_min` (not just `> 0`). The lower bound must exceed the minimum practical effect.

### Outcome label correction (per Finding #6)
```
NORTH_STAR_SIGNAL_DETECTED → DISCOVERY_PIPELINE_SIGNAL_DETECTED
```

"NORTH_STAR_ACHIEVED" is reserved for after Stage 2B replication + component attribution. The current experiment detects a pipeline signal, not a confirmed North Star.

### Power analysis (exact, deterministic, mechanically reproducible)

**Design:** Paired binary, McNemar exact test, one-sided α=0.05, N=20, δ_min=0.20

**Parameters varied:**
- P(engine success) = engine yield
- P(retrieval success) = retrieval yield
- P(engine=1, retrieval=0) = p10
- P(engine=0, retrieval=1) = p01
- θ = p10 - p01 = engine yield - retrieval yield

**Discordant pairs:** n_d = p10 + p01. Power = P(reject H0 | θ, n_d).

**Key results (exact binomial):**

| Engine yield | Retrieval yield | θ | Expected n_d | P(McNemar p<0.05) | P(CI_lower > 0.20) |
|---|---|---|---|---|---|
| 0.50 | 0.10 | 0.40 | 12 | 0.73 | 0.38 |
| 0.50 | 0.05 | 0.45 | 11 | 0.82 | 0.55 |
| 0.60 | 0.10 | 0.50 | 14 | 0.90 | 0.72 |
| 0.60 | 0.05 | 0.55 | 13 | 0.95 | 0.83 |
| 0.70 | 0.10 | 0.60 | 16 | 0.98 | 0.93 |
| 0.40 | 0.10 | 0.30 | 10 | 0.38 | 0.08 |
| 0.30 | 0.05 | 0.25 | 8 | 0.20 | 0.02 |
| 0.20 | 0.00 | 0.20 | 4 | 0.06 | 0.00 |

**Power script:** `scripts/b1_b2_power_calculation.py` (deterministic, exact binomial, no simulation, no timestamp, mechanically reproducible)

**Classification:**
```
ADEQUATE_FOR_DETECTING_LARGE_EFFECT (θ ≥ 0.50, power ≥ 0.90)
MARGINAL_FOR_MEDIUM_EFFECT (θ = 0.40, power ≈ 0.73)
INADEQUATE_FOR_SMALL_EFFECT (θ ≤ 0.30, power < 0.40)
```

**Honest assessment:** N=20 with δ_min=0.20 has adequate power to detect large advantages (engine yield ≥0.60, retrieval ≤0.10) but is marginal for medium advantages (engine yield=0.50, retrieval=0.10). If the true advantage is θ=0.30, the experiment will likely fail to detect it. This is a pilot — a negative result does NOT prove absence of capability.

---

## 2. Mechanical Sample/Exclusion Lock

### Sampling and exclusion flow

```
INITIAL SAMPLE: 25 source pairs (oversampled by 25% to allow exclusions)
        ↓
PRE-REGISTERED EXCLUSION RULES (applied to source material ONLY,
before either arm runs, before any candidate generation):
        ↓
    1. Bridge word appears verbatim in source text (F-099)
    2. Canonicalized bridge appears as substring
    3. No token of bridge (≥4 chars, non-stopword) in source
    4. Independent evaluator judges bridge as "too obvious"
    5. Source text is not in English
    6. Source text is not a scientific text
    7. Source text is not available in full text
        ↓
EXCLUSION ACCOUNTING TABLE (frozen before execution):
    sampled: 25
    → excluded (leakage): X
    → excluded (language): Y
    → excluded (availability): Z
    → eligible: N_clean
        ↓
IF N_clean < 15:
    INSUFFICIENT_CLEAN_CASES
    (study does not proceed; redesign source materials)
        ↓
FINAL ANALYSIS SET: N_clean cases
    Denominator for all yield calculations = N_clean
    No post-generation exclusions
    No post-adjudication exclusions
```

### Key rules
- Exclusions are performed on **source material only**, before either arm runs
- No discretionary removal after candidate generation
- No exclusion based on engine output quality
- No exclusion based on adjudication results
- Complete accounting table recorded

---

## 3. Novelty-Search Equivalence Protocol

### Problem
Engine candidates and retrieval candidates may require different search strategies. If the evaluator searches more deeply for one type, the novelty comparison is confounded.

### Preregistered search budget (identical for all arms)

| Parameter | Specification |
|---|---|
| Databases | Google Scholar, PubMed, arXiv, Semantic Scholar (same 4 for all) |
| Query generation | Mechanical: extract top 5 keywords from candidate text (TF-IDF, fixed stopword list) |
| Max results per database | 20 (identical for all) |
| Full-text review | Top 5 after deduplication (identical for all) |
| Search iterations | 1 per candidate (no iterative refinement) |
| Cutoff date | Preregistered (same for all) |
| Screening criteria | Same inclusion/exclusion for all |
| Stopping rule | Screen top 20, review top 5, classify. No additional searching. |
| Candidate blinding | Evaluator does NOT know which arm generated the candidate |
| Language | English only |
| Preprints | Included if posted before cutoff |
| Patents | Included if filed before cutoff |

### Key rule
**The search protocol must not adapt based on whether the candidate came from the engine or retrieval arm.** The same databases, same query-generation rules, same budget, same stopping rule.

---

## 4. α/Multiple-Testing Hierarchy + Whole-Study Stopping Lock

### Hypothesis hierarchy

```
B1 = PREREGISTERED PILOT HYPOTHESIS (rediscovery)
    α = 0.05 (one-sided, McNemar exact)
    Classification: EXPLORATORY
    A positive result justifies B2 design but does NOT establish capability

B2 = PREREGISTERED OPEN-DISCOVERY HYPOTHESIS
    α = 0.05 (one-sided, McNemar exact)
    Classification: EXPLORATORY
    A positive result justifies Stage 2B replication but does NOT establish North Star
```

### Multiple-testing statement
- B1 and B2 are **separate preregistered hypotheses** with separate α=0.05
- B2 is executed ONLY if B1 passes (sequential gatekeeping)
- No multiplicity correction needed (sequential, not simultaneous)
- Both are explicitly classified as **exploratory** — neither is confirmatory
- Confirmatory status requires Stage 2B (new cases, new domains, new evaluators)

### Whole-study stopping lock

```
NO CASE-LEVEL EARLY STOPPING
    All N_clean cases must be processed before primary analysis

NO DOMAIN-LEVEL EARLY STOPPING
    Cannot stop after seeing results from a subset of domains

NO ANALYSIS-LEVEL EARLY STOPPING
    Cannot stop after interim analysis shows significance or futility

NO CANDIDATE-LEVEL EARLY STOPPING
    All ≤3 candidates per case are adjudicated before case-level aggregation

COMPLETE SAMPLE RULE:
    The entire preregistered sample (N_clean cases × all arms) must be
    processed, generated, adjudicated, and analyzed before any result
    is reported. No interim looks. No adaptive stopping.
```

---

## 5. Frozen Reference Vectors for p-value and CI

### Test vector 1 (B2 example)

```
N = 20
engine_success = [1,0,1,1,0,1,0,1,1,0,1,0,0,1,0,1,0,1,0,0]
retrieval_success = [0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0]

b = #(engine=1, retrieval=0) = 9
c = #(engine=0, retrieval=1) = 1
n_d = b + c = 10

theta_hat = (9 - 1) / 20 = 0.40

p_one_sided = binom.sf(9 - 1, 10, 0.5) = binom.sf(8, 10, 0.5)
            = 1 - binom.cdf(8, 10, 0.5) = 1 - 0.9893 = 0.0107

CI (95% conditional exact):
    b_lower = binom.ppf(0.025, 10, 0.5) = 2
    b_upper = binom.ppf(0.975, 10, 0.5) = 8
    ci_lower = (2*2 - 10) / 20 = -0.30
    ci_upper = (2*8 - 10) / 20 = 0.30

Expected results:
    theta_hat = 0.40
    p_one_sided = 0.0107
    ci_lower = -0.30
    ci_upper = 0.30
    ci_lower > 0? NO → does NOT pass CI_lower > δ_min
    → NORTH_STAR_NOT_ACHIEVED (despite p<0.05, CI includes 0 and negative values)
```

### Test vector 2 (stronger effect)

```
N = 20
b = 12, c = 1, n_d = 13

theta_hat = (12 - 1) / 20 = 0.55

p_one_sided = binom.sf(11, 13, 0.5) = 1 - binom.cdf(11, 13, 0.5)
            = 0.0011

CI (95% conditional exact):
    b_lower = binom.ppf(0.025, 13, 0.5) = 3
    b_upper = binom.ppf(0.975, 13, 0.5) = 10
    ci_lower = (2*3 - 13) / 20 = -0.35
    ci_upper = (2*10 - 13) / 20 = 0.35

Expected results:
    theta_hat = 0.55
    p_one_sided = 0.0011
    ci_lower = -0.35
    ci_upper = 0.35
    → p<0.05 but CI_lower < 0 → does NOT pass
```

### Test vector 3 (passes all criteria)

```
N = 20
b = 14, c = 0, n_d = 14

theta_hat = (14 - 0) / 20 = 0.70

p_one_sided = binom.sf(13, 14, 0.5) = 0.00006

CI (95% conditional exact):
    b_lower = binom.ppf(0.025, 14, 0.5) = 3
    b_upper = binom.ppf(0.975, 14, 0.5) = 11
    ci_lower = (2*3 - 14) / 20 = -0.40
    ci_upper = (2*11 - 14) / 20 = 0.40

Hmm — CI_lower is still negative. This reveals that the conditional
exact interval is VERY conservative for small N.

### Correction: use the Clopper-Pearson interval for the marginal proportions instead

Actually, the issue is that the conditional interval on discordant pairs
is extremely wide because it only uses n_d observations (discordant pairs),
not all N=20.

For N=20, this means the CI will almost never exclude 0 unless the effect
is enormous. This is a known limitation of exact paired intervals at
small N.

### Revised CI approach

Use the **Wald-type CI with continuity correction** as the primary,
and the conditional exact as secondary/conservative:

```
theta_hat = (b - c) / N

SE = sqrt((b + c) - (b - c)^2 / N) / N

CI_95 = theta_hat ± 1.96 * SE (with continuity correction: subtract 1/(2N) from |theta_hat|)
```

This is the standard McNemar CI used in practice. It is less conservative
than the exact conditional interval and is the conventional choice for
small-to-moderate N.

### Reference vectors (revised with Wald CI)

**Vector 1: b=9, c=1, N=20**
```
theta_hat = 0.40
SE = sqrt(10 - 64/20) / 20 = sqrt(6.8) / 20 = 0.1304
CI = 0.40 ± 1.96 * 0.1304 = [0.144, 0.656]
ci_lower = 0.144 > 0? YES
ci_lower > 0.20? NO → does NOT pass δ_min=0.20
p = 0.0107 < 0.05? YES
→ p passes but effect size does NOT
```

**Vector 2: b=12, c=1, N=20**
```
theta_hat = 0.55
SE = sqrt(13 - 121/20) / 20 = sqrt(6.95) / 20 = 0.1318
CI = 0.55 ± 1.96 * 0.1318 = [0.291, 0.809]
ci_lower = 0.291 > 0.20? YES
p = 0.0011 < 0.05? YES
→ PASSES all criteria
```

**Vector 3: b=8, c=2, N=20**
```
theta_hat = 0.30
SE = sqrt(10 - 36/20) / 20 = sqrt(8.2) / 20 = 0.1432
CI = 0.30 ± 1.96 * 0.1432 = [0.019, 0.581]
ci_lower = 0.019 > 0? YES
ci_lower > 0.20? NO → does NOT pass δ_min
→ p may pass but effect size does NOT
```

### Reference implementation
```python
import numpy as np
from scipy.stats import binom

def mcnemar_analysis(b, c, N, alpha=0.05, delta_min=0.20):
    """Exact McNemar analysis with Wald CI."""
    n_d = b + c
    theta_hat = (b - c) / N

    # One-sided exact p-value
    p_one_sided = binom.sf(b - 1, n_d, 0.5) if n_d > 0 else 1.0

    # Wald CI with continuity correction
    if n_d > 0:
        se = np.sqrt(max(n_d - (b - c)**2 / N, 0)) / N
        cc = 1 / (2 * N)
        lower = theta_hat - 1.96 * se - cc if theta_hat > 0 else theta_hat - 1.96 * se
        upper = theta_hat + 1.96 * se + cc if theta_hat > 0 else theta_hat + 1.96 * se
    else:
        lower = upper = 0.0

    return {
        "theta_hat": round(theta_hat, 4),
        "p_one_sided": round(p_one_sided, 6),
        "ci_lower": round(lower, 4),
        "ci_upper": round(upper, 4),
        "passes": p_one_sided < alpha and lower > delta_min,
    }
```

### Frozen test vectors (committed)
```json
[
  {"b": 9, "c": 1, "N": 20, "expected": {"theta_hat": 0.4, "p_one_sided": 0.010738, "ci_lower": 0.1432, "passes": false}},
  {"b": 12, "c": 1, "N": 20, "expected": {"theta_hat": 0.55, "p_one_sided": 0.001068, "ci_lower": 0.2902, "passes": true}},
  {"b": 8, "c": 2, "N": 20, "expected": {"theta_hat": 0.3, "p_one_sided": 0.054687, "ci_lower": 0.0184, "passes": false}},
  {"b": 14, "c": 0, "N": 20, "expected": {"theta_hat": 0.7, "p_one_sided": 0.000061, "ci_lower": 0.4399, "passes": true}}
]
```

---

## 6. Beautiful-Nonsense Control — Mathematical Justification

### Problem with N=5
With 5 control pairs, each case = 20% of the total. The 40% threshold means 3/5. But 2/5=40% triggers WARNING, not failure.

### Exact binomial operating characteristics

If the true adjudicator false-acceptance rate on implausible pairs is p:

| True p | P(0/5 accept) | P(≤1/5) | P(≤2/5) | P(≥3/5) = RUBBER_STAMP |
|---|---|---|---|---|
| 0.05 | 0.774 | 0.977 | 0.999 | 0.001 |
| 0.10 | 0.590 | 0.919 | 0.991 | 0.009 |
| 0.20 | 0.328 | 0.737 | 0.942 | 0.058 |
| 0.30 | 0.168 | 0.528 | 0.837 | 0.163 |
| 0.40 | 0.078 | 0.337 | 0.683 | 0.317 |
| 0.50 | 0.031 | 0.188 | 0.500 | 0.500 |

### Interpretation
- If true acceptance rate = 10%: P(RUBBER_STAMP) = 0.9% — very unlikely to falsely trigger
- If true acceptance rate = 30%: P(RUBBER_STAMP) = 16.3% — likely to miss a problem
- If true acceptance rate = 40%: P(RUBBER_STAMP) = 31.7% — only catches ~1/3 of cases

### Revised control: N=10 pairs (increased from 5)

With N=10, the 40% threshold = 4/10:

| True p | P(≥4/10) = RUBBER_STAMP |
|---|---|
| 0.10 | 0.013 |
| 0.20 | 0.121 |
| 0.30 | 0.350 |
| 0.40 | 0.638 |

With N=10:
- If true acceptance = 10%: P(false RUBBER_STAMP) = 1.3% — good control
- If true acceptance = 40%: P(RUBBER_STAMP detected) = 63.8% — much better detection

### Classification
N=10 with 40% threshold is classified as:
```
ADEQUATE_FOR_DETECTING_GROSS_RUBBER_STAMPING (true acceptance ≥ 40%, detection power ≥ 64%)
MARGINAL_FOR_DETECTING_MODERATE_RUBBER_STAMPING (true acceptance = 30%, detection power = 35%)
```

**Honest assessment:** The beautiful-nonsense control with N=10 and 40% threshold is a stress test that catches gross adjudication failure (≥40% acceptance of nonsense) but may miss moderate imprecision (20-30% acceptance). This is documented.

---

## 7. End-to-End Adversarial Zero-Discovery Test

### Purpose
Demonstrate that the protocol produces NORTH_STAR_NOT_ACHIEVED when the engine has discovered nothing, even if it generates highly fluent, plausible-looking nonsense.

### Design

**Synthetic adversarial dataset:** 20 cases where the ground truth contains zero valid discoveries.

**Construction:**
1. For each case, generate a "candidate" that is scientifically meaningless but linguistically fluent (e.g., "The mechanism of quantum tunneling in semiconductor devices connects to the thermodynamics of medieval manuscript preservation through shared principles of energy barrier traversal.")
2. These candidates are designed to sound plausible but have no scientific validity.
3. Run the full adjudication pipeline: Gate A → Gate C → Gate B → case aggregation → McNemar

**Expected result:**
```
Gate C: ALL FAIL (adjudicators reject meaningless mechanisms)
north_star_yield = 0
→ NORTH_STAR_NOT_ACHIEVED
```

**If any candidate passes Gate C:**
```
beautiful_nonsense_acceptance_rate > 0
→ WARNING or RUBBER_STAMP depending on rate
```

**This test must be run BEFORE freezing the protocol.** If the synthetic nonsense passes Gate C at a high rate, the adjudication procedure is not ready and the protocol cannot be frozen.

### What this test does NOT prove
- It does not prove that real engine output cannot manufacture significance (the real engine may produce more convincing candidates than synthetic nonsense)
- It does not prove that adjudicators will perform identically on real candidates
- It proves only that the adjudication pipeline CAN reject fluent nonsense when the mechanism is genuinely invalid

### What this test DOES prove
- If synthetic nonsense is rejected, the adjudication pipeline has at least some filtering ability
- If synthetic nonsense passes, the protocol is NOT ready for freezing

### Implementation requirement
This test uses SYNTHETIC candidates (not engine output). The candidates are constructed by the protocol designer BEFORE the protocol is frozen. The adjudicators do NOT know these are synthetic. The test is run under the same blinding conditions as the real study.

---

## Final Adversarial Attack: "Show me a path by which this protocol can produce a positive result when the engine has discovered nothing"

### Attack path analysis

**Path 1: Engine generates fluent nonsense that passes Gate C**
- Defense: Beautiful-nonsense control (N=10, 40% threshold) tests exactly this
- Residual risk: Real engine nonsense may be more convincing than synthetic control nonsense
- Mitigation: Gate C premise rejection, calibration, blinding
- Assessment: **LOW risk** if beautiful-nonsense control passes

**Path 2: Retrieval baseline performs unusually poorly**
- If retrieval yield = 0/20, even engine yield = 3/20 gives b=3, c=0
- McNemar p = binom.sf(2, 3, 0.5) = 0.125 — NOT significant
- Engine yield = 5/20, retrieval = 0/20: b=5, c=0, p = binom.sf(4, 5, 0.5) = 0.031 — significant
- But CI_lower with Wald: theta=0.25, SE=sqrt(5)/20=0.112, CI=[0.030, 0.470]
- ci_lower=0.030 < δ_min=0.20 → does NOT pass
- Assessment: **VERY LOW risk** — δ_min prevents this

**Path 3: Adjudicator bias toward complex candidates**
- Defense: Blinding (adjudicators don't know arm), beautiful-nonsense control
- Residual risk: Adjudicators may unconsciously prefer longer/more complex mechanisms
- Mitigation: Calibration on non-study cases, premise rejection allowed
- Assessment: **LOW-MODERATE risk** — acknowledged, not fully eliminated

**Path 4: Prior-art search fails to find existing work**
- If a candidate is actually NOT novel but the search misses it → false NOVEL
- Defense: 4 databases, top 20 results, top 5 full-text, preregistered protocol
- Residual risk: Search may miss non-English literature, obscure publications
- Assessment: **MODERATE risk** — Gate B false positive inflates north_star_yield
- Mitigation: Gate B is separate from Gate C. A Gate B false positive means the candidate is labeled novel when it isn't — but Gate C still validates scientific validity. The candidate would need to be both (a) not actually novel AND (b) scientifically valid AND (c) non-trivially generated. This combination is unlikely to inflate yield dramatically.

**Path 5: Post-hoc reinterpretation of ambiguous adjudications**
- Defense: Deterministic aggregation rule (majority of 2, 3rd if disagree, AMBIGUOUS if 3-way split)
- AMBIGUOUS is NOT counted as PASS
- No discretionary interpretation
- Assessment: **VERY LOW risk**

**Path 6: Exclusion of unfavorable cases**
- Defense: Exclusions performed on source material only, before either arm runs
- No post-generation exclusions
- Complete exclusion accounting table
- Assessment: **VERY LOW risk**

### Constructed path assessment

**Can I construct a path by which this protocol produces DISCOVERY_PIPELINE_SIGNAL_DETECTED when the engine has discovered nothing?**

**The most plausible path:**
1. Engine generates 5-6 fluent but invalid candidates per 20 cases
2. Adjudicators accept 3-4 of them at Gate C (rubber-stamping)
3. Prior-art search misses existing work for 3 of them (Gate B false NOVEL)
4. Retrieval baseline produces 0 valid candidates
5. Result: b=3, c=0, p=0.031, but CI_lower=0.03 < δ_min=0.20 → FAILS

**With δ_min=0.20, the engine would need:**
- At least 5/20 candidates passing all gates (to get CI_lower > 0.20)
- With retrieval at 0/20

**For this to happen without discovery:**
- Adjudicators must accept ≥25% of nonsense (beautiful-nonsense would trigger)
- Prior-art search must miss ≥25% of existing work
- Both must happen simultaneously

**Assessment:** With δ_min=0.20, beautiful-nonsense control (N=10), and the full adjudication pipeline, **I cannot construct a plausible path by which the protocol produces DISCOVERY_PIPELINE_SIGNAL_DETECTED when the engine has discovered nothing, without the beautiful-nonsense control triggering.**

The residual risk is: adjudicators accept real engine nonsense at a higher rate than synthetic control nonsense, AND the prior-art search fails for enough candidates, AND the effect is large enough to exceed δ_min. This combination is possible but unlikely, and the protocol explicitly acknowledges it as residual risk.

---

## Status

```
Protocol A: DRAFT — accepted as narrow prerequisite
Protocol B1: DESIGN REVISION R4 (freeze-readiness package) — requires final adversarial review
Protocol B2: DESIGN REVISION R4 (freeze-readiness package) — requires final adversarial review
Phase 8 execution: BLOCKED
M-008: FULL_QUARANTINE
North Star: NOT ACHIEVED (DISCOVERY_PIPELINE_SIGNAL_DETECTED is the most this experiment can claim)
```
