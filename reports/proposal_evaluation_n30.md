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

## Gate C verdict: **PASS** (verdict_tier: **WEAK_STATISTICAL_PASS**)

**Cycle 257 tightening**: This gate's PASS criterion was too weak.
Distinguishability from FP=1.0 is NECESSARY but NOT SUFFICIENT.
Useful proposal performance requires per-proposal honest F1 mean
≥ 0.3. Observed: 0.1500.

WEAK_STATISTICAL_PASS: N=40 meets ≥30, honest F1 mean
(0.1500) is distinguishable from FP floor at p<0.05,
BUT the mean is below the useful-performance threshold
(≥0.3).

This means the matcher produces non-zero signal, but the signal
is weak. Per-proposal F1 of 0.1500 means most proposals do not
match the gold bridge. The matcher is statistically not pure
noise, but it is not producing useful proposals at scale.

To earn SCIENCE_PASS, the matcher's per-proposal honest F1
must reach ≥ 0.3.
