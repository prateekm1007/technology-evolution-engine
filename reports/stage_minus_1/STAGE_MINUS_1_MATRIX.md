# Stage −1 Metric Matrix

| Measurement | TP | FP | FN | Precision | Recall | F1 | Interpretation |
|---|---|---|---|---|---|---|---|
| Current production scorer | 8 | 0 | 12 | 1.0000 | 0.4000 | 0.5714 | Baseline (with fallback, FP=0 by construction) |
| Proposal-locus only | 6 | 0 | 14 | 1.0000 | 0.3000 | 0.4615 | Independent proposal test (no fallback) |
| Strict normalized matcher | 0 | 0 | 20 | 1.0000 | 0.0000 | 0.0000 | No fuzzy credit (exact canonical only) |
| Proposal + strict matcher | 0 | 16 | 20 | 0.0000 | 0.0000 | 0.0000 | Most conservative (proposal-only + strict + FP counted) |
| Shuffled gold (N=1000) | 2.75 | — | — | — | 0.1374 | — | Empirical null hit rate (chance matching under shuffled-gold null) |

## Additional metrics
- Ambient fallback hits = 2
- Total current hits = 8
- Fallback fraction = 2/8 = 0.2500
- Strict proposal precision = 0.2727 (from Part 4C)
- Shuffled-gold P(>=current) = 0.0020
