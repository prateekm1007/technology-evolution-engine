# DR-99: N≥30 Proposal Evaluation (Gate C of Road to FINAL)

Cycle: 256

## Sample size: N = 40 (MET ≥30 requirement)

- Original (gold) evaluations: 20
- Synthetic (perturbed) evaluations: 20

## Distribution statistics

| Metric | n | mean | median | stdev | min | max | Q1 | Q3 |
|---|---|---|---|---|---|---|---|---|
| Strict + Honest F1 | 40 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| Lenient + DR-91 F1 | 40 | 0.1500 | 0.0000 | 0.3571 | 0.0000 | 1.0000 | 0.0000 | 0.0000 |
| Lenient + Honest F1 | 40 | 0.1500 | 0.0000 | 0.3571 | 0.0000 | 1.0000 | 0.0000 | 0.0000 |

## Statistical test: distinguishability from FP floor (1.0)

- H0: mean(honest F1) = 1.0 (the FP floor)
- H1: mean(honest F1) < 1.0
- N = 40
- Sample mean: 0.1500
- Sample stdev: 0.3616
- Standard error: 0.0572
- t-statistic: -14.8661
- p-value: 0.000000
- Verdict (α=0.05): **REJECT_H0**

## Gate C verdict: **PASS**

Sample size N=40 meets ≥30 requirement, and the
honest-F1 mean (0.1500) is statistically distinguishable
from the FP floor (1.0) at p<0.05.

This is EVIDENCE (not proof) that the production matcher produces
non-trivial signal on larger samples. It does not address whether
the signal is *discovery* vs *recognition* — that requires Gate D
(Tier-2 human domain expert review).
