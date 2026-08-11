# Engineering Hypothesis H-GEN-1 — FROZEN

**Date:** 2026-08-08
**Status:** PREREGISTERED (before implementation)
**Predecessor evidence:** DXP-001 through DXP-004

---

## Hypothesis

> The dominant cause of generator failure is loss of mechanism-specific causal information during abstraction/transfer, rather than insufficient LLM reasoning capacity.

## Prediction

If the original mechanism graph is preserved alongside the abstraction and every proposed target mechanism must trace back to specific causal edges in that graph, then on a fresh blind capability-control set:

1. Correct mechanism identification should INCREASE
2. Paraphrase/semantic substitution should DECREASE
3. Quantitative-variable identification should INCREASE
4. Adversarial rejection of correct candidates should remain APPROXIMATELY UNCHANGED

## Critical condition

If the adversarial gate starts passing everything after the generator improvement, **the science is broken**. The filter must remain independent.

## Intervention

One controlled change to the hypothesis generation stage:

- The mechanism graph (from extraction) is passed ALONGSIDE the abstraction to the hypothesis generator
- The hypothesis generator prompt requires every proposed mechanism to cite specific causal edges from the mechanism graph
- The abstraction is still produced (for the transfer stage) but does not REPLACE the mechanism graph
- The adversarial gate is UNCHANGED

## What is NOT changed

- The extraction stage
- The abstraction stage (still produces a domain-neutral pattern)
- The transfer stage (still uses the abstraction)
- The adversarial gate (still uses the same prompt and criteria)
- The rediscovery detector
- The novelty firewall
- The prediction engine
- The experiment design engine
- The substrate (frozen)

## Evaluation

Test on a FRESH blind capability-control suite (not shark→pipe or any DXP-001/002/003 case):

- 5 known-positive transfers (with quantitative ground truth)
- 5 hard negatives (tempting analogy that is physically wrong)
- All controls: engine (current), engine (modified), generic LLM, retrieval, human, null

Compare:
- Correct mechanism identification rate
- Correct causal variable identification rate
- Correct direction rate
- Quantification rate
- Rediscovery rate
- Adversarial survival rate
- False-positive rate (hard negatives that survive)

**The modified engine must improve WITHOUT increasing false positives.**

## Stop conditions

- If false-positive rate increases → intervention failed (the generator is now producing more plausible but wrong candidates)
- If adversarial survival increases but correct mechanism rate does not → the filter was weakened implicitly
- If no improvement on any metric → H-GEN-1 is refuted; the problem is not mechanism preservation
