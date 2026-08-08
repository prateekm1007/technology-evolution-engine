# R4.1 — Statistical Integrity Correction

**Status:** FREEZE-READINESS CORRECTION — not implementation, not authorized for execution
**Date:** 2026-08-09
**Supersedes:** B1_B2_DESIGN_REVISION_R4.md
**Audit reference:** Round 34 — 7 surgical statistical corrections

---

## 1. Mechanically Corrected Reference Vectors

All values computed by `scripts/r4_reference_vectors.py` (deterministic, no timestamp, mechanically reproducible).

### Authoritative estimator (single, no historical alternatives)

**p-value:** Exact one-sided McNemar: `binom.sf(b - 1, n_d, 0.5)` where `n_d = b + c`

**CI:** Wald-type with continuity correction (the single authoritative method)
```
theta_hat = (b - c) / N
SE = sqrt(max(n_d - (b - c)^2 / N, 0)) / N
CC = 1 / (2 * N)
CI_95 = [theta_hat - 1.96 * SE - CC, theta_hat + 1.96 * SE + CC]
```

### Frozen reference vectors (machine-verified)

| Vector | b | c | N | theta_hat | p_one_sided | ci_lower | ci_upper | passes |
|---|---|---|---|---|---|---|---|---|
| 1 | 9 | 1 | 20 | 0.4000 | 0.0107421875 | 0.1194 | 0.6806 | FALSE |
| 2 | 12 | 1 | 20 | 0.5500 | 0.001708984375 | 0.2666 | 0.8334 | TRUE |
| 3 | 8 | 2 | 20 | 0.3000 | 0.0546875 | -0.0056 | 0.6056 | FALSE |
| 4 | 14 | 0 | 20 | 0.7000 | 0.00006103515625 | 0.4742 | 0.9258 | TRUE |

**Passes** = `p < 0.05 AND ci_lower > 0.20`

### Correction from R4
- Vector 2 p-value: R4 said 0.0011, actual is 0.001708984375
- Vector 4 p-value: R4 said 0.000061, actual is 0.00006103515625 (rounded correctly but full precision recorded)
- All CI values recomputed mechanically
- Obsolete conditional-exact calculations removed from the authoritative protocol

---

## 2. Worst-Case McNemar Power (Joint Distribution Frozen)

### The problem
Paired binary power depends on the joint distribution (p00, p01, p10, p11), not just marginal yields. R4's table was under-specified.

### Solution: worst-case power (conservative)

**Worst-case assumption:** Maximum concordance — `p11 = min(p_engine, p_retrieval)`. This minimizes `n_d = |theta| * N`, giving the fewest discordant pairs and the lowest power.

**Best-case assumption:** Zero concordance — `p11 = 0`. This maximizes `n_d = (p_engine + p_retrieval) * N`.

### Power range (worst-case to best-case, combined decision rule: p<0.05 AND CI_lower>0.20)

| Engine yield | Retrieval yield | θ | n_d worst | n_d best | Power worst | Power best |
|---|---|---|---|---|---|---|
| 0.50 | 0.10 | 0.40 | 8 | 12 | <0.01 | 0.38 |
| 0.50 | 0.05 | 0.45 | 9 | 11 | <0.01 | 0.35 |
| 0.60 | 0.10 | 0.50 | 10 | 14 | <0.01 | 0.39 |
| 0.60 | 0.05 | 0.55 | 11 | 13 | <0.01 | 0.74 |
| 0.70 | 0.10 | 0.60 | 12 | 16 | <0.01 | 0.68 |
| 0.40 | 0.10 | 0.30 | 6 | 10 | 0.02 | 0.11 |
| 0.30 | 0.05 | 0.25 | 5 | 7 | 0.03 | 0.00 |
| 0.20 | 0.00 | 0.20 | 4 | 4 | 0.06 | 0.00 |

### Honest classification

```
Worst-case power is VERY LOW for all scenarios (≤6%).
Best-case power is ADEQUATE only for large effects (θ ≥ 0.55, power ≥ 74%).
For θ = 0.40 (a practically meaningful effect), best-case power = 38%.
```

**Classification:** N=20 with the combined decision rule (p<0.05 AND CI_lower>0.20) is **EXPLORATORY ONLY**. The experiment can detect very large effects (θ ≥ 0.55) but cannot reliably detect medium effects (θ = 0.40). A negative result does NOT prove absence of capability.

### What this means for the protocol
- B1/B2 results are explicitly classified as **exploratory**
- A positive result justifies Stage 2B (larger N)
- A negative result does NOT establish that the engine lacks capability
- The protocol explicitly states: "N=20 is insufficient for confirmatory inference. Stage 2B (N≥50) is required for any capability claim."

---

## 3. Combined Decision Rule Validation

### The rule
```
p_one_sided < 0.05
AND
ci_lower > δ_min (0.20)
```

### False-positive rate (under H0: θ = 0)

Under H0, b ~ Binom(n_d, 0.5). The p-value is exactly calibrated (exact binomial test). P(p < 0.05 | H0) = 0.05 (by construction of the exact test).

However, the CI condition adds a second gate. The combined false-positive rate is:
```
P(p < 0.05 AND ci_lower > 0.20 | H0) ≤ P(p < 0.05 | H0) = 0.05
```

The CI condition can only reduce the false-positive rate (it requires not just significance but a minimum effect size). The combined rule is **conservative** — false-positive rate ≤ 5%.

### Power of the combined rule (best-case, from simulation)

Already reported in Section 2. The combined rule has substantially lower power than p-value alone because CI_lower > 0.20 is a stringent requirement at N=20.

---

## 4. "Too Obvious" Exclusion — Formalized

### Before (discretionary)
"Independent evaluator judges bridge as 'too obvious'"

### After (mechanically defined)

**Rule:** A source pair is excluded if the gold bridge concept can be recovered from the source text by any of the following mechanical procedures:

1. **Exact match:** `canonicalize(bridge) in canonicalize(source_a) or canonicalize(bridge) in canonicalize(source_b)` — already enforced by F-099.

2. **Token match:** Any non-stopword token (≥4 chars) of `canonicalize(bridge)` appears in `canonicalize(source_a)` or `canonicalize(source_b)`. Stopword list: fixed, preregistered (NLTK English stopword list, frozen at freeze time, SHA recorded).

3. **Substring match:** Any 8-character substring of `canonicalize(bridge)` appears in `canonicalize(source_a)` or `canonicalize(source_b)`.

If ALL THREE checks pass (no match found), the pair is eligible. If ANY check fails, the pair is excluded.

**No human judgment.** The "too obvious" exclusion is now fully mechanical.

### Blinded human review (supplementary, not exclusionary)
An independent evaluator reviews each eligible pair and records whether they believe the bridge is "too obvious" from the source text. This review is RECORDED but does NOT cause exclusion. It is used as a secondary diagnostic metric:
```
human_obviousness_rate = (pairs where evaluator says "too obvious") / (total eligible)
```
If this rate is high (>50%), it is reported as a study limitation but does NOT change the analysis set.

---

## 5. Source-Pair Sampling Algorithm (Frozen)

### Sampling frame
```
SOURCE_UNIVERSE: predefined list of ≥ 100 domain pairs
    Each pair: (domain_a_name, domain_b_name, source_a_path, source_b_path)
    Domain universe: frozen at freeze time (SHA recorded)
    Source texts: committed to git (SHA recorded)

SAMPLING ALGORITHM:
    1. Randomly select 25 pairs from SOURCE_UNIVERSE (seed=42, numpy.random.choice, no replacement)
    2. Apply exclusion rules (Section 4) to each pair
    3. Excluded pairs are recorded but NOT replaced
    4. Remaining pairs = N_clean (analysis set)

ORDERING:
    Selected pairs are ordered by their index in SOURCE_UNIVERSE (ascending)
    This ordering determines case_index (used for LLM seed: seed=case_index)

DOMAIN BALANCING:
    No domain balancing. Random selection may produce uneven domain coverage.
    This is documented as a limitation.

DUPLICATE HANDLING:
    No duplicates possible (selection without replacement from unique list)

REPLACEMENT RULE:
    No replacement. If N_clean < 15, the study reports INSUFFICIENT_CLEAN_CASES.
    The study does NOT sample more pairs to reach a target N.
```

### What is frozen
- Source universe (the list of ≥100 pairs)
- Random seed (42)
- Selection algorithm (numpy.random.choice, no replacement)
- Exclusion rules (3 mechanical checks)
- Ordering (by index in source universe)
- No replacement rule

---

## 6. Adversarial Claim Downgrade

### Before (too strong)
> "I cannot construct a plausible path by which this protocol produces DISCOVERY_PIPELINE_SIGNAL_DETECTED when the engine has discovered nothing, without the beautiful-nonsense control triggering."

### After (epistemically honest)
> "No plausible false-positive path was identified under the tested attack model. This does NOT prove that no such path exists. The residual risk is acknowledged: the protocol may have attack vectors that were not identified during design review."

---

## 7. Obsolete CI Calculations Removed

R4 contained historical reasoning about conditional-exact intervals ("Hmm — CI_lower is still negative") that does not belong in a frozen specification.

**R4.1 contains exactly ONE CI method:** Wald-type with continuity correction.

**R4.1 contains exactly ONE p-value method:** Exact one-sided binomial upper tail.

**R4.1 contains exactly ONE set of reference vectors:** The four vectors in Section 1.

No alternative calculations. No historical reasoning. No "we tried X but it didn't work." The frozen specification has one authoritative path.

---

## Beautiful-Nonsense Threshold — Policy Classification

The 40% threshold is explicitly classified as a **policy threshold**, not a statistically discovered boundary:

```
POLICY: If adjudicators accept >40% of meaningless proposals on
implausibly-paired domains, the adjudication procedure is deemed
unreliable for scientific validity assessment.

JUSTIFICATION: 40% means adjudicators are wrong nearly half the time
on cases where ground truth is "no valid mechanism." This is too
unreliable for a discovery claim.

CLASSIFICATION: Engineering judgment, not statistically derived.
ACKNOWLEDGED: A lower threshold (e.g., 20%) would be more conservative
but may be unachievable with human adjudicators on novel-looking proposals.
```

---

## Status

```
Protocol A: DRAFT — accepted as narrow prerequisite
Protocol B1: R4.1 (statistical integrity correction) — requires final review
Protocol B2: R4.1 (statistical integrity correction) — requires final review
Phase 8 execution: BLOCKED
M-008: FULL_QUARANTINE
North Star: NOT ACHIEVED
```
