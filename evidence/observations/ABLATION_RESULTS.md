# ABLATION RESULTS — Phase 12B

## Comparison

| Formula | Precision | TP | FP | vs Formula B |
|---|---:|---:|---:|---|
| 1. velocity only | 0.0071 | 1 | 139 | -0.0286 |
| 2. adjacency only | 0.0000 | 0 | 140 | -0.0357 |
| 3. feasibility only | 0.0000 | 0 | 140 | -0.0357 |
| 4. velocity + adjacency | 0.0357 | 5 | 135 | ≈ same |
| 5. velocity + feasibility | 0.0071 | 1 | 139 | -0.0286 |
| 6. adjacency + feasibility | 0.0000 | 0 | 140 | -0.0357 |
| 7. Formula B (frozen) | 0.0357 | 5 | 135 | baseline |
| NULL_MODEL | 0.0071 | 1 | 139 | — |

## Verdict

VELOCITY-ONLY IS WORSE. Adjacency and/or cost_bonus contribute independent signal.
