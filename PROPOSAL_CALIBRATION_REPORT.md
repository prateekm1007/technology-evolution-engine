# Proposal Calibration Report

## DR-94: Proposal Composer Gen0 Calibration Study

**Date:** cycle 250
**Proposal Composer:** Generation 0 (FROZEN — never modify)
**Internal evaluator:** DR-93 heuristic (Tier 0 — self-evaluation)
**External evaluator:** DR-93.5 LLM judge (Tier 1 — independent but not ground truth)

## Evidence Tiers

| Tier | Evaluator | Status |
|---|---|---|
| 0 | Internal heuristic (DR-93) | ✓ Completed |
| 1 | External LLM (DR-93.5) | ✓ Completed |
| 2 | Domain expert | Future |
| 3 | Experimental validation | Future |

## Calibration Metrics

| Metric | Value |
|---|---|
| N proposals | 6 |
| Mean internal score | 4.5/5 |
| Mean external score | 2.0/5 |
| Mean Calibration Error | 2.5 |
| Bias (internal - external) | +2.50 |
| Variance | 0.02 |
| Correlation | 0.0 |
| Agreement rate (|resid|≤1) | 0.0% |
| Overestimate rate | 100.0% |
| Underestimate rate | 0.0% |

## Finding: Self-Validation Bias Detected

The internal evaluator OVERESTIMATES proposal quality by 2.50 points.
This is a measurable calibration problem. The internal heuristic
rates proposals 4.5/5 on average; the external LLM
rates them 2.0/5. The gap (+2.50) is the
self-validation bias.

## Per-Proposal Calibration

| Entity | Internal Q | External Q | Residual | Ext Plausible | Ext Novelty | Ext Recommendation |
|---|---|---|---|---|---|---|
| heat | 4.25 | 2 | 2.25 | Yes | Incremental | Revise |
| thermal_differential | 4.5 | 2 | 2.5 | No | Incremental | Reject |
| surface_chemical_modification | 4.75 | 2 | 2.75 | No | Incremental | Reject |
| energy_gap | 4.5 | 2 | 2.5 | No | Incremental | Revise |
| phase_change_enthalpy | 4.5 | 2 | 2.5 | No | Known | Reject |
| light_quantum_energy | 4.5 | 2 | 2.5 | No | Incremental | Reject |

## Honest Wording (per CTO)

- ~~'0/6 potentially novel'~~ → 'The external evaluator did not identify
  evidence supporting novelty claims.'
- ~~'Scientific validity 6/6'~~ → 'Scientific plausibility 1/6 (external LLM).
  Internal heuristic overestimates by bias of +2.50.'

## Proposal Composer Gen0 — FROZEN

Generation 0 is permanently frozen. It serves as the baseline
for comparing future generations. Never modify Gen0 results.
Future: Gen1 (mechanism-driven) will be evaluated against the
same calibration corpus and compared to Gen0.
