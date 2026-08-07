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
| M-008 | FP floor (synonym) | 0.9352 | 0.0658 | 0.0703 | 0.7879 | 1.0000 | 0.2121 | 0.6000 | -0.1599 | ACCEPTABLE |
| M-013 | Aggregate F1 (honest) | 0.8333 | 0.0000 | 0.0000 | 0.8333 | 0.8333 | 0.0000 | 1.0000 | +0.0000 | STABLE |
| M-201 | L5a held-out beats (/10) | 0.8300 | 0.1100 | 0.1325 | 0.7000 | 1.0000 | 0.3000 | 0.3000 | +0.0158 | ACCEPTABLE |
| M-203 | L5b+Synthesis held-out beats (/10) | 0.8400 | 0.0800 | 0.0952 | 0.7000 | 1.0000 | 0.3000 | 0.5000 | -0.1741 | ACCEPTABLE |

## Verdict counts

- STABLE: 2/5
- ACCEPTABLE: 3/5
- UNSTABLE: 0/5
- DETERMINISTIC (std=0): 2/5

## Gate M4 verdict: **PASS**

All metrics are STABLE or ACCEPTABLE (CV < 0.15).
Nondeterministic metrics have been tested and their run-to-run
variance is within acceptable bounds.

## Key findings

- **M-005** (Discovery F1 (DR-91, shared, syn)): DETERMINISTIC — produces the same value (0.8571) on every run. Run-to-run variance is zero.
- **M-008** (FP floor (synonym)): ACCEPTABLE — CV=0.0703, stability=0.6000. Some run-to-run variance but within 15% threshold.
- **M-013** (Aggregate F1 (honest)): DETERMINISTIC — produces the same value (0.8333) on every run. Run-to-run variance is zero.
- **M-201** (L5a held-out beats (/10)): ACCEPTABLE — CV=0.1325, stability=0.3000. Some run-to-run variance but within 15% threshold.
- **M-203** (L5b+Synthesis held-out beats (/10)): ACCEPTABLE — CV=0.0952, stability=0.5000. Some run-to-run variance but within 15% threshold.
