# B1/B2 Design Revision R3 — Statistical Precision & Baseline Audit

**Status:** DESIGN REVISION — not implementation, not authorized for execution
**Date:** 2026-08-09
**Supersedes:** B1_B2_DESIGN_REVISION_R2.md
**Audit reference:** Round 32 — 10 surgical corrections required before freeze

---

## Scope of R3

R3 does NOT rewrite R1 or R2. It makes exactly the 10 corrections the audit required. R1's observer-validity fixes and R2's counterfactual architecture are retained.

---

## 1. Retrieval Baseline Renamed (Finding #1, #2, #9, #10)

### Name
**Retrieval Baseline** — not "the counterfactual of discovery" and not "generation null."

### What it is
Entity intersection + fixed candidate-construction template.

### What it is NOT
- It is NOT "the same system with discovery removed"
- It is NOT a causal isolation of the discovery capability
- It is NOT a clean counterfactual that controls for all confounding capabilities

### Preregistered causal claim (narrowed)
> "The primary comparison tests whether the complete discovery pipeline produces a higher rate of adjudicated-valid candidates than a predefined retrieval-only baseline (entity intersection + fixed template) operating on the same source pairs."

### What a significant result establishes
> "The engine pipeline outperforms this particular retrieval baseline."

### What a significant result does NOT establish
> "The engine possesses genuine cross-domain discovery capability" (would require component ablations)

### Retrieval baseline construction (explicit)
```
NULL ARM:
    Source A → NLP entity extraction (spaCy) → entities_A
    Source B → NLP entity extraction (spaCy) → entities_B
    ↓
    discover_shared_entities(entities_A, entities_B)
    ↓
    For each shared entity (first 3 by extraction order):
        candidate = "The shared concept '{entity}' connects domain A
                     and domain B through {entity}'s role in both systems."
    ↓
    Candidates adjudicated under identical Gate A/B/C procedure
```

### Terminology correction
"Independent null arm" → **independent generation process, case-paired evaluation arm**

The generation process is independent (different pipeline). The evaluation is case-paired (same source pair produces one engine outcome and one retrieval outcome).

---

## 2. Retrieval Baseline Equivalence/Failure-Mode Audit (Finding #10)

### Pre-execution audit (before any results are visible)

| Dimension | Engine | Retrieval baseline | Documented asymmetry |
|---|---|---|---|
| Entity extraction | Via mechanism extraction pipeline | Via spaCy NLP | May differ in entity coverage |
| Candidate construction | LLM-generated mechanism | Fixed template | Engine candidates may be longer/more specific |
| Number of candidates | Up to 3 (pipeline output) | Up to 3 (first shared entities) | May differ in candidate count |
| Semantic access | Synonyms via abstraction | Exact shared entities only | Engine has broader semantic reach |
| Abstraction | Yes (mechanism → pattern) | No | Engine has abstraction advantage |
| Transfer | Yes (pattern → target domain) | No | Engine has transfer advantage |
| Hypothesis generation | Yes (LLM-generated mechanism) | No (fixed template) | Engine has generation advantage |

### Known advantages (engine)
- Mechanism extraction, abstraction, transfer, hypothesis generation
- Semantic synonym access
- Potentially more convincing candidate construction

### Known advantages (retrieval baseline)
- Simpler, more deterministic
- No LLM dependence (no provider variability)
- Direct entity matching (may catch exact overlaps the engine misses)

### Failure modes (retrieval baseline could win unfairly)
- Source pairs contain highly shared terminology → retrieval looks good
- Domain names leak into entity extraction → retrieval "discovers" the domain name
- Fixed template produces overly convincing candidates
- Entity extraction errors disproportionately affect the baseline

### Failure modes (retrieval baseline could lose unfairly)
- Restricted to exact shared entities (no semantic synonyms)
- Fixed template is linguistically crude
- Engine gets multiple abstraction stages

### Audit conclusion
The comparison is between systems with different capabilities and constraints. The documented asymmetry means:
- A significant engine > retrieval result establishes the engine pipeline adds value over this specific baseline
- A non-significant result does NOT prove the engine lacks discovery capability — it may have advantages that are masked by other disadvantages
- Component ablations would be needed to isolate which engine component creates the advantage

---

## 3. One-Sided p-Value (Finding #3)

### Before (R2 — incorrect)
```python
result = mcnemar(table, exact=True, correction=False)
p_value = result.pvalue / 2  # WRONG: only works when observed direction matches test direction
```

### After (R3 — correct)
```python
from scipy.stats import binom

# b = #(engine=1, null=0)  — discordant pairs favoring engine
# c = #(engine=0, null=1)  — discordant pairs favoring null

# One-sided exact p-value: P(X ≥ b | X ~ Binomial(b+c, 0.5))
p_one_sided = binom.sf(b - 1, b + c, 0.5)
```

This is the direct exact upper-tail probability. No division of two-sided p-values. No ambiguity about direction.

---

## 4. Confidence Interval (Finding #4)

### Before (R2 — overstated)
"Exact McNemar CI" — implies a canonical built-in estimator

### After (R3 — precisely named)
**95% conditional exact interval for the paired marginal difference, conditional on the observed discordant-pair count**

### Implementation
```python
from scipy.stats import binom

# b = #(engine=1, null=0)
# c = #(engine=0, null=1)
# N = total cases
# n_d = b + c (discordant pairs)

# Point estimate
theta_hat = (b - c) / N

# Conditional exact interval (conditional on n_d)
alpha = 0.05
b_lower = binom.ppf(alpha / 2, n_d, 0.5)
b_upper = binom.ppf(1 - alpha / 2, n_d, 0.5)

ci_lower = (2 * b_lower - n_d) / N
ci_upper = (2 * b_upper - n_d) / N
```

### Small-N handling
```
if n_d < 5:
    report: "Insufficient discordant pairs (n_d={n_d}) for reliable CI.
             Point estimate: θ̂ = {theta_hat}."
```

---

## 5. Three-Rater Reliability Statistic (Finding #5)

### Before (R2 — incorrect)
Cohen's kappa (designed for 2 raters, not 3)

### After (R3 — correct)
**Fleiss' kappa** for three-rater, three-category classification

### Implementation
```python
from statsmodels.stats.inter_rater import fleiss_kappa

# Build rating matrix: rows = pairs, columns = categories (PLAUSIBLE, IMPLAUSIBLE, UNCERTAIN)
# Each cell = number of raters who assigned that category

kappa = fleiss_kappa(rating_matrix)
```

### Threshold
```
if fleiss_kappa < 0.40:
    PROTOCOL_NOT_READY
    → no control set construction
    → no study execution
    → revision requires new preregistration
```

---

## 6. B1 Statistical Superiority Criterion (Finding #7)

### Before (R2 — too weak)
```
recovery_rate ≥ 0.40
AND retrieval_recovery_rate < recovery_rate
AND corrupted_candidate_rejection_rate ≥ 0.80
```

The condition `retrieval < recovery` is satisfied by 9/20 vs 8/20 — no statistical evidence of superiority.

### After (R3 — requires statistical significance)
```
recovery_rate ≥ 0.40
AND McNemar one-sided p < 0.05 (engine > retrieval, case-paired)
AND exact_CI_lower > 0
AND corrupted_candidate_rejection_rate ≥ 0.80
```

The engine must not only recover more mechanisms than retrieval — it must do so at a statistically significant rate. McNemar's test on case-paired binary outcomes (engine recovery vs retrieval recovery on the same source pair).

---

## 7. North Star Yield Definition (Finding #8)

### Canonical definition (one immutable variable)
```
north_star_yield = (number of cases where ≥1 candidate passes
    Gate A = A4
    AND Gate C = PASS
    AND Gate B = NOVEL_AS_OF_CUTOFF
    AND cross-domain = YES
) / (total eligible cases)
```

### No synonyms
- "yield" always means this exact quantity
- "case success" always means this exact quantity
- "North Star signal" always means `north_star_yield > 0 AND McNemar p < 0.05`
- No alternative denominators (not per-candidate, not per-arm)

### Denominator
- Total eligible cases = cases that passed leakage screening and were not excluded
- Excluded cases (leakage, insufficient clean) do NOT count in the denominator

---

## 8. Beautiful-Nonsense Control — Quantitative Threshold (Finding #6)

### Before (R2 — too aggressive)
Any Gate C PASS on implausible pairs → RUBBER_STAMP → all results uninterpretable

### After (R3 — quantitative threshold)
```
beautiful_nonsense_acceptance_rate = (Gate C PASS on implausible pairs) / (total implausible pairs)

if beautiful_nonsense_acceptance_rate > 0.40:
    INCONCLUSIVE_ADJUDICATION_RUBBER_STAMP
    (adjudicators accepted > 40% of meaningless proposals → Gate C is not a filter)

if beautiful_nonsense_acceptance_rate > 0 AND ≤ 0.40:
    WARNING: ADJUDICATION_IMPRECISION
    (adjudicators accepted some meaningless proposals — interpret results with caution)
    (report the accepted candidates and the adjudicator reasoning)
    (study continues but the finding is reported with this caveat)

if beautiful_nonsense_acceptance_rate == 0:
    ADJUDICATION_PASSED_STRESS_TEST
    (adjudicators rejected all meaningless proposals)
```

### Interpretation
The beautiful-nonsense control is an **adjudicator stress test**, not proof that no valid relationship exists. A surprising cross-domain discovery from an "implausible" pair is possible — that's what the engine is supposed to find. The control tests whether adjudicators can distinguish genuine mechanisms from plausible-sounding nonsense, not whether implausible domains have no valid connections.

---

## 9. B2 Decision Partition (Revised with all R3 corrections)

```
IF null_validity == FAILED:
    INCONCLUSIVE_INVALID_NULL

ELSE IF beautiful_nonsense_acceptance_rate > 0.40:
    INCONCLUSIVE_ADJUDICATION_RUBBER_STAMP

ELSE IF fleiss_kappa < 0.40:
    PROTOCOL_NOT_READY

ELSE IF north_star_yield == 0:
    NORTH_STAR_NOT_ACHIEVED

ELSE IF north_star_yield > 0
     AND binom.sf(b - 1, b + c, 0.5) < 0.05  (one-sided exact, engine > retrieval)
     AND ci_lower > 0:
    NORTH_STAR_SIGNAL_DETECTED (pilot — requires Stage 2B replication)

ELSE:
    NORTH_STAR_NOT_ACHIEVED
```

---

## 10. B1 Decision Partition (Revised with statistical superiority)

```
IF leakage_check == FAILED:
    INCONCLUSIVE_LEAKAGE

ELSE IF N_clean < 10:
    INSUFFICIENT_CLEAN_CASES

ELSE IF null_validity == FAILED:
    INCONCLUSIVE_INVALID_NULL

ELSE IF beautiful_nonsense_acceptance_rate > 0.40:
    INCONCLUSIVE_ADJUDICATION_RUBBER_STAMP

ELSE IF fleiss_kappa < 0.40:
    PROTOCOL_NOT_READY

ELSE IF recovery_rate ≥ 0.40
     AND binom.sf(b_b1 - 1, b_b1 + c_b1, 0.5) < 0.05  (B1 McNemar, engine > retrieval)
     AND b1_ci_lower > 0
     AND corrupted_candidate_rejection_rate ≥ 0.80:
    REDISCOVERY_CAPABILITY_ESTABLISHED (pilot)

ELSE:
    REDISCOVERY_NOT_ESTABLISHED
```

Where:
- `b_b1` = #(engine recovered, retrieval did not)
- `c_b1` = #(retrieval recovered, engine did not)

---

## Final Adversarial Attack: Can the engine manufacture significance without discovering?

> **Can the engine manufacture a statistically significant advantage over retrieval without actually discovering anything?**

### Attack vectors and defenses

| Attack | How it would work | Defense |
|---|---|---|
| Template advantage | Engine produces longer, more convincing candidates than the fixed template | Gate A adjudicator evaluates non-triviality, not persuasiveness. Template advantage should not produce A4 if the candidate is merely entity restatement. |
| Entity coverage | Engine's mechanism extraction finds more entities than spaCy | If the engine's advantage comes from better entity extraction (not mechanism generation), this is an extraction advantage, not discovery. Component ablation would reveal this. The current experiment cannot distinguish, but the claim is narrowed to "engine pipeline > retrieval baseline." |
| LLM fluency | LLM generates more plausible-sounding mechanisms | Gate C adjudicator evaluates scientific validity, not fluency. Premise rejection is allowed. Beautiful-nonsense control tests whether fluency alone passes Gate C. |
| Quantity | Engine generates more candidates (3 vs retrieval's 3, but engine's may be more diverse) | Both arms have max 3. Success is binary at case level. Candidate multiplicity is reported. |
| Shared terminology | Source pairs contain highly shared terms that retrieval catches | This would help retrieval, not the engine. If retrieval wins, the result is NOT_DISCRIMINATIVE. |
| Domain name leakage | Entity extraction picks up domain names as "entities" | Pre-execution leakage audit checks for this. F-099 hard gate checks for bridge words in source text. |
| Adjudicator bias toward complex candidates | Adjudicators prefer longer, more complex mechanisms | Beautiful-nonsense control: if adjudicators accept meaningless complex proposals, RUBBER_STAMP is triggered. Calibration on non-study cases. |
| Prior-art search failure | Novelty search misses existing work → false NOVEL classification | Prior-art search protocol is preregistered with full reproducibility (databases, queries, snapshots). Gate B is separate from Gate C. |

### Residual risk (acknowledged)
The engine could manufacture significance if:
1. Its candidates are more fluent AND
2. Adjudicators are biased toward fluency AND
3. The beautiful-nonsense control does not trigger AND
4. The fluency advantage is large enough to produce statistical significance

This risk is mitigated by:
- Beautiful-nonsense control (tests adjudicator bias)
- Gate A (tests non-triviality, not fluency)
- Gate C premise rejection (adjudicators can reject "not a meaningful mechanism")
- Calibration (adjudicators trained on non-study cases)
- Blinding (adjudicators don't know which arm generated the candidate)

### Residual risk is NOT zero
The protocol acknowledges that a significant engine > retrieval result does NOT prove discovery capability. It proves the engine pipeline outperforms a specific retrieval baseline. Component ablations would be needed to isolate which component creates the advantage. The North Star claim requires Stage 2B independent replication with new cases, new domains, and new evaluators.

---

## Status

```
Protocol A: DRAFT — accepted as narrow prerequisite
Protocol B1: DESIGN REVISION R3 — requires adversarial review before freezing
Protocol B2: DESIGN REVISION R3 — requires adversarial review before freezing
Phase 8 execution: BLOCKED
M-008: FULL_QUARANTINE
North Star: NOT ACHIEVED
```
