# Measurement Specification

## Status: PRELIMINARY — under DR-91 reconstruction

## Principle

Every score in this repository must carry:
1. **Uncertainty** (bootstrap CI or equivalent)
2. **Provenance** (who measured, when, using what evaluator, calibration version)
3. **Evidence tier** (Tier 0: internal, Tier 1: external LLM, Tier 2: domain expert, Tier 3: experimental)
4. **Calibration status** (calibrated / uncalibrated / biased)

## Forbidden

A single-number F1 without uncertainty is **BANNED**.

```
F1 = 0.91  ← FORBIDDEN
F1 = 0.91 ± 0.05 (95% CI, N=200, Tier 1, calibrated)  ← REQUIRED
```

## Evidence Tiers

| Tier | Evaluator | Trust Level |
|------|-----------|-------------|
| 0 | Internal heuristic | LOW — known bias (+2.50, F-139) |
| 1 | External LLM | MEDIUM — independent but noisy (judges disagree 83%) |
| 2 | Domain expert | HIGH — not yet available |
| 3 | Experimental validation | HIGHEST — not yet available |

## Current State (cycle 252)

- **Discovery F1 = 0.9189** (HISTORICAL — was circular, current F1=0.5714 after cycle 270): INVALID (measured entity recognition, not discovery)
- **Proposal F1**: UNKNOWN (pipeline produces proposals but benchmark not rerun)
- **Evaluator reliability**: EXPLORATORY (N=6, insufficient for conclusions)
- **Confidence calibration**: POOR (ECE=0.433, Brier=0.340)
- **Self-validation bias**: +2.50 (internal overestimates, F-139)

## Required Before FINAL_VERDICT

1. N≥30 proposals evaluated
2. Bootstrap CIs on all scores
3. At least 2 independent LLM judges
4. At least 1 domain expert (Tier 2)
5. Adversarial FP < 5%
6. Confidence calibration ECE < 0.2
7. Evaluator agreement > 70%
