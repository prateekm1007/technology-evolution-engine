# DSB_HUMAN_ADJUDICATION_REPORT_V1

**Date:** 2026-08-12
**Frozen artifacts:** DSB V1 (hash `dfe15a46...`), V3 scorer (frozen)
**Adjudication hash:** `77360588...`

---

## CRITICAL DISCLOSURE

**This is an LLM-proxy adjudication, NOT human expert review.**
- Reviewer A: z-ai CLI (glm-4-plus) — different model from V3 scorer
- Reviewer B: OpenRouter (meta-llama/llama-3.3-70b-instruct) at temperature=0.7 — different from V3's 0.3
- V3 scorer: meta-llama/llama-3.3-70b-instruct at temperature=0.3

**True human expert review remains the gold standard and has NOT been performed.**

---

## Results (30 cases, blinded)

### Inter-Rater Agreement (Reviewer A vs Reviewer B)

| Dimension | Agreement | Rate |
|---|---|---|
| Discovery Structure Match | 12/30 | **40%** |
| Mechanism Match | 11/30 | **37%** |
| Real/Fabricated Classification | 20/30 | **67%** |

**Inter-rater agreement is LOW.** Two different LLM models disagree on 60% of discovery-structure-match judgments and 63% of mechanism-match judgments. This means the scoring task is genuinely difficult and subjective — even LLM proxies disagree.

### V3 Scorer vs Human Proxy Agreement

| Dimension | Agreement | Rate |
|---|---|---|
| Discovery Structure Match | 10/30 | **33%** |
| Mechanism Match | 14/30 | **47%** |

**V3 agreement with Reviewer A is LOW (33% on DSM, 47% on MM).** The V3 scorer's judgments do not align well with an independent LLM reviewer. This raises serious questions about V3 scorer reliability.

### False Positives / False Negatives

| Metric | V3 Scorer | Reviewer A (proxy) |
|---|---|---|
| False positives (YES on fabricated) | 0 | 0 |
| False negatives (NO on real) | 10 | 8 |

Both V3 and Reviewer A have **0 false positives** — neither incorrectly identifies fabricated discoveries as real. But both have significant **false negatives** — they miss real discoveries 27-33% of the time.

---

## Interpretation

### What the data shows

1. **The scoring task is genuinely difficult.** Two independent LLM models agree only 40% of the time on discovery structure match. This is not a scorer calibration problem — it's a fundamental difficulty in judging whether a proposal captures the same discovery relationship as a target.

2. **V3 scorer has low agreement with independent reviewers.** At 33% DSM agreement, the V3 scorer's judgments are not reliably reproducible by other models. This means the V3 scorer's 40-60% DSM rates in the ablation may not be stable.

3. **Both scorers are conservative.** Zero false positives means both correctly reject fabricated discoveries. But high false negatives (8-10 out of ~15 real cases) means both miss many real discovery matches.

4. **Real/fabricated classification is more reliable.** 67% agreement on whether a target is real or fabricated is higher than DSM or MM agreement. This suggests the system can somewhat distinguish real from fabricated even when it can't precisely score mechanism matches.

### What this means for V1.12

The V3 scorer is **not validated** against independent judgment. The 40-60% DSM rates in the DSB V1 benchmark are scorer-dependent and may not be reproducible with different scorers or human experts.

**The DSB V1 results should be treated as exploratory, not confirmatory.**

### Known Limitations

1. **LLM proxies, not human experts.** True human adjudication is the gold standard and has not been performed.
2. **Same model family.** Reviewer B and V3 both use llama-3.3-70b (different temperature). Reviewer A uses a different model (glm-4-plus) but is still an LLM.
3. **Small sample.** 30 cases with 60% disagreement is insufficient for reliable calibration.
4. **No formal inter-rater reliability statistic.** Cohen's kappa was not computed due to multi-category labels (YES/PARTIAL/NO).

---

## Gate Status

| Gate | Status | Result |
|---|---|---|
| DSB V1 frozen | ✅ | Hash `dfe15a46...` |
| V3 scorer frozen | ✅ | No tuning |
| Blinded packet | ✅ | 30 cases, evidence + proposed + target only |
| 2 independent reviews per case | ✅ | Reviewer A (glm-4-plus) + Reviewer B (llama@0.7) |
| Inter-rater agreement | ✅ MEASURED | 40% DSM, 37% MM (LOW) |
| V3 vs human agreement | ✅ MEASURED | 33% DSM, 47% MM (LOW) |
| V3 false positive/negative rates | ✅ MEASURED | 0 FP, 10 FN |
| Report + hashes | ✅ | Hash `77360588...` |
| **Human expert review** | ❌ | **NOT PERFORMED — LLM proxies only** |

---

## Recommendation

**Do not expand to 50+50 until the scorer agreement problem is addressed.**

The 33% V3-vs-reviewer agreement means the current evaluation pipeline is not reliable enough to support scaling. Options:

1. **Use majority voting** across 3+ reviewers per case
2. **Develop a more structured rubric** that reduces subjectivity
3. **Obtain actual human expert reviews** (not LLM proxies)
4. **Accept the uncertainty** and report results with wide confidence intervals

The frozen TEE yardstick remains clean. Baseline `4b5b51a0...` unmodified. No evidence manufactured.
