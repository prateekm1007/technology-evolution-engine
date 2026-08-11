# Stage M4: Repeatability (Program A)

Cycle: 263

Per ROADMAP_V2.md Stage M4: run identical benchmark N times with
different seeds, measure variance/drift/stability.
Per AP-1: run it, don't reason about it.

## Difference from M3 (Bootstrap)

- **M3 (Bootstrap)**: resamples the SAME data with replacement to
  quantify SAMPLING uncertainty. Question: 'if we had a different
  sample of 20 gold bridges, how much would F1 vary?'
- **M4 (Repeatability)**: runs the SAME benchmark with DIFFERENT seeds
  to quantify RUN-TO-RUN variance. Question: 'if we run the exact same
  benchmark 10 times, do we get the same answer?'

These are different questions. A metric can have a tight bootstrap CI
(M3) but high run-to-run variance (M4) if the computation is
nondeterministic (e.g., random candidate generation).

## Method

- **Seeds**: [42, 7, 99, 123, 256, 1000, 2000, 3000, 4000, 5000]
- **N runs per metric**: 10
- **Acceptance**: CV < 0.05 = STABLE, CV < 0.15 = ACCEPTABLE,
  CV >= 0.15 = UNSTABLE
- **Stability rate**: fraction of runs within ±5% of mean
- **Drift**: Pearson correlation between seed order and value

## Results

| Metric | Name | Mean | Std | CV | Min | Max | Range | Stability | Drift | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| M-005 | Discovery F1 (DR-91, shared, syn) | 0.8571 | 0.0000 | 0.0000 | 0.8571 | 0.8571 | 0.0000 | 1.0000 | +0.0000 | STABLE |
| M-008 | FP floor (synonym) | 0.9595 | 0.0405 | 0.0422 | 0.8571 | 1.0000 | 0.1429 | 0.9000 | -0.1624 | STABLE |
| M-013 | Aggregate F1 (honest) | 0.8333 | 0.0000 | 0.0000 | 0.8333 | 0.8333 | 0.0000 | 1.0000 | +0.0000 | STABLE |
| M-201 | L5a held-out beats (/10) | 0.8300 | 0.1100 | 0.1325 | 0.7000 | 1.0000 | 0.3000 | 0.3000 | +0.0158 | ACCEPTABLE |
| M-203 | L5b+Synthesis held-out beats (/10) | 0.8400 | 0.0800 | 0.0952 | 0.7000 | 1.0000 | 0.3000 | 0.5000 | -0.1741 | ACCEPTABLE |
| M-304 | Inter-rater agreement rate (E1) | 0.1833 | 0.1167 | 0.6364 | 0.0000 | 0.3333 | 0.3333 | 0.0000 | -0.0249 | UNSTABLE |
| M-305 | Self-validation bias (E1) | 2.4917 | 0.0312 | 0.0125 | 2.4583 | 2.5417 | 0.0833 | 1.0000 | +0.5118 | STABLE |
| M-306 | Expected Calibration Error / ECE (E1) | 0.8983 | 0.0062 | 0.0069 | 0.8917 | 0.9083 | 0.0167 | 1.0000 | +0.5118 | STABLE |

## Verdict counts

- STABLE: 5/8
- ACCEPTABLE: 2/8
- UNSTABLE: 1/8
- DETERMINISTIC (std=0): 2/8

## Gate M4 verdict: **FAIL**

1 metric(s) are UNSTABLE (CV >= 0.15).
These metrics produce significantly different values across
runs with different seeds. This means any single-run report
of these metrics is unreliable.

## Key findings

- **M-005** (Discovery F1 (DR-91, shared, syn)): DETERMINISTIC — produces the same value (0.8571) on every run. Run-to-run variance is zero.
- **M-008** (FP floor (synonym)): STABLE — CV=0.0422. Run-to-run variance is below 5%.
- **M-013** (Aggregate F1 (honest)): DETERMINISTIC — produces the same value (0.8333) on every run. Run-to-run variance is zero.
- **M-201** (L5a held-out beats (/10)): ACCEPTABLE — CV=0.1325, stability=0.3000. Some run-to-run variance but within 15% threshold.
- **M-203** (L5b+Synthesis held-out beats (/10)): ACCEPTABLE — CV=0.0952, stability=0.5000. Some run-to-run variance but within 15% threshold.
- **M-304** (Inter-rater agreement rate (E1)): UNSTABLE — CV=0.6364, range [0.0000, 0.3333]. Values across seeds: [0.1667, 0.1667, 0.0, 0.3333, 0.3333, 0.1667, 0.1667, 0.3333, 0.0, 0.1667]. This metric is unreliable on any single run.
- **M-305** (Self-validation bias (E1)): STABLE — CV=0.0125. Run-to-run variance is below 5%.
- **M-306** (Expected Calibration Error / ECE (E1)): STABLE — CV=0.0069. Run-to-run variance is below 5%.
