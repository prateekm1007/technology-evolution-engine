# H-GEN-1 Evaluation — DXP-004 Re-run with Mechanism Preservation

**Date:** 2026-08-08
**Hypothesis:** H-GEN-1 — loss of mechanism-specific causal information during abstraction is the dominant cause of generator failure
**Test:** Re-run DXP-004 (shark skin → pipe drag) with mechanism-preserving generator

---

## Key Finding: H-GEN-1 PARTIALLY SUPPORTED

### What improved

**H-GEN-1 produced the CORRECT MECHANISM in H-001.**

Original engine (DXP-004):
- H-001: "boundary layer transition modification" ❌ WRONG
- H-002: "micro-streams reducing viscous dissipation" ❌ WRONG
- H-003: "biofilm inhibition" ❌ WRONG
- H-004: "elastic deformation" ❌ WRONG

H-GEN-1 engine:
- **H-001: "lifts near-wall turbulent structures away from the pipe wall" ✅ CORRECT**
- H-002: "generates controlled streamwise vortices that thin the viscous sublayer" ⚠️ PARTIALLY CORRECT (mentions vortices but wrong mechanism)
- H-003: "surface flexibility absorbs pressure fluctuations" ❌ WRONG (same as original)
- H-004: "anisotropic riblet structure creates directional flow control" ⚠️ PARTIALLY CORRECT (mentions riblets but wrong mechanism)

**Correct mechanism identification: 0/4 → 1/4 (25% improvement)**
**Mentions riblets/vortices: 0/4 → 3/4 (75% improvement)**

### What also improved

**Quantitative predictions appeared:**
- H-001: "6-9% drag reduction" ✅ IN CORRECT RANGE (ground truth: 5-10%)
- H-002: "4-7% drag reduction" ✅ IN CORRECT RANGE
- H-003: "3-6% drag reduction" ⚠️ LOW END OF RANGE
- H-004: "5-8% drag reduction" ✅ IN CORRECT RANGE

Original engine: 0/4 had quantitative predictions
H-GEN-1 engine: 4/4 have quantitative predictions

**Quantification rate: 0% → 100%**

### What did NOT improve

**Adversarial survival: still 0/4**

All 4 H-GEN-1 hypotheses were still killed by the adversarial gate. However, the objections are now a MIX of valid and questionable:

H-001 (CORRECT mechanism):
- [HIGH] "riblet dimensions are unsubstantiated" — VALID (the engine didn't specify exact dimensions)
- [HIGH] "lifts vortices contradicts literature" — **QUESTIONABLE** (the literature SUPPORTS vortex lifting; the adversarial critic may be wrong here)
- [HIGH] "external vs internal flow" — VALID concern but not fatal (riblets work in both)
- [HIGH] "practical implementation challenges" — VALID but not fatal

**This is the critical finding:** The adversarial gate killed H-001 (the CORRECT mechanism) with an objection that is itself QUESTIONABLE. The claim "lifts vortices contradicts established literature" is REFUTED by the known ground truth — the literature CONFIRMS that riblets lift vortices.

This suggests the adversarial gate has a false-positive problem: it can kill correct candidates with incorrect objections. However, this is based on ONE case — more data is needed.

### Rediscovery rate

Original: 4/4 PARAPHRASED_IN_INPUT (100% rediscovery)
H-GEN-1: 4/4 PARAPHRASED_IN_INPUT (100% rediscovery)

No improvement — the rediscovery detector still classifies all candidates as paraphrases. This may be because the detector is also LLM-based and the shark→pipe transfer is conceptually adjacent.

---

## H-GEN-1 Scorecard

| Metric | Original | H-GEN-1 | Ground truth | Prediction |
|---|---|---|---|---|
| Correct mechanism | 0/4 (0%) | 1/4 (25%) | Riblet vortex lifting | Should INCREASE ✅ |
| Mentions riblets/vortices | 0/4 (0%) | 3/4 (75%) | N/A | Should INCREASE ✅ |
| Quantitative prediction | 0/4 (0%) | 4/4 (100%) | 5-10% | Should INCREASE ✅ |
| Correct magnitude range | 0/4 (0%) | 3/4 (75%) | 5-10% | Should INCREASE ✅ |
| Rediscovery rate | 4/4 (100%) | 4/4 (100%) | N/A | Should DECREASE ❌ (no change) |
| Adversarial survival | 0/4 (0%) | 0/4 (0%) | N/A | Should be ~unchanged ✅ (unchanged) |
| False-positive rate | N/A | N/A | N/A | Should not increase ✅ (no increase) |

### H-GEN-1 prediction evaluation

| Prediction | Result |
|---|---|
| Correct mechanism identification should INCREASE | ✅ CONFIRMED (0→25%) |
| Paraphrase/semantic substitution should DECREASE | ❌ NOT CONFIRMED (100% → 100%) |
| Quantitative-variable identification should INCREASE | ✅ CONFIRMED (0% → 100%) |
| Adversarial rejection should remain ~unchanged | ✅ CONFIRMED (0% → 0%) |

**H-GEN-1: PARTIALLY SUPPORTED.** The mechanism-preserving intervention improved mechanism identification and quantification, but did not reduce rediscovery classification. The adversarial gate remains unchanged (0% survival).

---

## Critical observation: the adversarial gate killed the CORRECT mechanism

H-001 proposed the correct mechanism ("lifts near-wall turbulent structures away from the pipe wall") with the correct magnitude ("6-9% drag reduction"). The adversarial gate killed it with:

> [HIGH] CONTRADICTS_KNOWN: "The claim that riblets lift streamwise vortices away from the surface directly contradicts established literature"

**This objection is FACTUALLY WRONG.** The established literature (Bechert et al. 1997, Garcia-Mayoral & Jimenez 2011) CONFIRMS that riblets reduce drag by lifting streamwise vortices. The adversarial gate's LLM does not know this and incorrectly asserts the opposite.

This is a **false-positive kill** — the adversarial gate killed a correct candidate with an incorrect objection. This is the first evidence that the adversarial gate has a false-positive problem, not just a false-negative problem.

However: this is ONE case. It does not establish that the gate is systematically over-aggressive. It may be that the LLM used for adversarial analysis has a knowledge gap about riblet physics.

---

## Honest assessment

**H-GEN-1 is a real improvement.** The mechanism-preserving intervention:
- Produced the correct mechanism (1/4 vs 0/4)
- Produced quantitative predictions (4/4 vs 0/4)
- Produced correct magnitude ranges (3/4 vs 0/4)
- Did not increase false positives (0/4 survived, same as original)
- Did not weaken the adversarial gate (still 0/4 survived)

**But it did not produce a surviving candidate.** The adversarial gate killed all 4, including the correct one. The correct candidate (H-001) was killed with a factually wrong objection about riblet physics.

**The bottleneck has shifted.** Before H-GEN-1: the generator couldn't produce the right mechanism. After H-GEN-1: the generator CAN produce the right mechanism, but the adversarial gate kills it with incorrect objections.

This suggests the next intervention should target the adversarial gate's knowledge accuracy, not its aggressiveness. The gate should not raise CONTRADICTS_KNOWN objections that are themselves contradicted by the known literature.

But: this is ONE data point. More experiments are needed to determine whether this is a systematic problem or a one-off knowledge gap.

---

## Recommendation

1. **H-GEN-1 is a genuine improvement.** The mechanism-preserving intervention should be retained.

2. **The adversarial gate may have a false-positive problem.** H-001 (correct mechanism) was killed with a factually wrong objection. This needs more data — run the fresh blind capability-control suite (5 positives + 5 negatives) to determine whether false-positive kills are systematic.

3. **Do NOT weaken the adversarial gate.** The correct response to a false-positive kill is to improve the gate's knowledge, not to lower its standards.

4. **Run the fresh blind suite next.** The reviewer's recommended design (5 known-positive + 5 hard-negative, all controls) will determine whether H-GEN-1's improvement generalizes and whether the adversarial gate's false-positive is systematic.
