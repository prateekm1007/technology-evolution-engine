# Stage M8: Measurement Constitution (Program A)

Cycle: 266

Per ROADMAP_V2.md Stage M8: 'Rules every future metric must satisfy.'

## The 8 Constitutional Rules

| Rule | Name | Statement |
|---|---|---|
| MC-1 | No self-validation | A metric may not be validated by the same system that produced it. Every metric ... |
| MC-2 | Independent rescoring | Every metric must have an independent implementation that reproduces the score w... |
| MC-3 | Confidence calibration | Every metric that produces a confidence score must report ECE or Brier score. Co... |
| MC-4 | Evidence tiers | Every metric must declare an evidence tier (A-I per CONSTITUTION evidence hierar... |
| MC-5 | Adversarial testing | Every metric must be tested against adversarial inputs: FP floor (random candida... |
| MC-6 | Historical permanence | No metric may be silently altered. Historical scores must be reproducible. Code ... |
| MC-7 | No naked numbers | No score may be reported as a bare scalar. Every score must be a ScoredValue wit... |
| MC-8 | Bootstrap uncertainty | Every metric must report a bootstrap 95% CI with N and B. Point estimates withou... |

## Compliance summary

- Total checks: 304
- Compliant: 304
- Non-compliant: 0
- All metrics pass: True

### Per-rule compliance

| Rule | Name | Compliant | Total |
|---|---|---|---|
| MC-1 | No self-validation | 38 | 38 |
| MC-2 | Independent rescoring | 38 | 38 |
| MC-3 | Confidence calibration | 38 | 38 |
| MC-4 | Evidence tiers | 38 | 38 |
| MC-5 | Adversarial testing | 38 | 38 |
| MC-6 | Historical permanence | 38 | 38 |
| MC-7 | No naked numbers | 38 | 38 |
| MC-8 | Bootstrap uncertainty | 38 | 38 |

## Gate M8 verdict: **PASS**

Constitution document exists, CI test exists, all checks compliant.
Every metric satisfies all 8 constitutional rules.

## Relationship to Gate 1

With M8 PASS, Gate 1 has 8/11 criteria addressed:
- M1 (Specification): PASS
- M2 (Provenance): PASS
- M3 (Bootstrap + CIs): PASS
- M4 (Repeatability): PASS
- M6 (Sensitivity): PARTIAL
- M7 (Failure Envelope): PASS
- M8 (Measurement Constitution): PASS
- Remaining: M5 (reproducibility), Evaluator reliability (M4/E1),
  Calibration documented (M2/E1)
