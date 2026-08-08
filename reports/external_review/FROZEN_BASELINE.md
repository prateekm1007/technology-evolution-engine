# Frozen Baseline Card

## Measurement matrix (frozen at 777cb6d)

| Measurement | Value | Interpretation |
|---|---|---|
| Current production F1 | 0.5714 | Historical result under flawed scorer |
| Proposal-locus F1 | 0.4615 | No ambient fallback |
| Strict normalized F1 | 0.0000 | Exact canonical matching |
| Proposal + strict + FP F1 | 0.0000 | Conservative measurement |
| Shuffled-gold null rate | 0.1374 | Chance matching under null |
| Proposal precision | 0.2727 | 6 / 22 actual proposals |

## Additional frozen metrics

```
Ambient fallback TPs = 2 / 8 = 25%
```

## Critical statement

None of these numbers is the corrected discovery score.

Each number answers a different measurement question:

- **0.5714** — What does the production scorer report? (Inflated by fallback + FP=0 + loose matching)
- **0.4615** — What happens if you require the bridge to be in shared entities? (Still FP=0)
- **0.0000** — What happens if you require exact canonical match? (No matches at all)
- **0.1374** — What hit rate does random gold assignment produce? (Chance floor)
- **0.2727** — What precision do actual proposals achieve? (6 correct, 16 incorrect)

The correct scientific posture is:

**Current benchmark → invalid for independent discovery → frozen baseline → repair methodology → independently rerun.**
