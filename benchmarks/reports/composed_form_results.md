# Composed Transcendental Form Results (cycle 79)

**Date:** 2026-08-05
**Status:** Phase III progress (40% → 45%)

## Composed form: sqrt(x+offset) → single form

BACON.3-style composition: transform x → sqrt(x+offset), then fit single forms on the transformed variable.

### Stull wet-bulb (RH → T_wb at T=25°C, 25 points)

| Form | R² | Notes |
|---|---|---|
| sqrt (single, cycle 74) | 0.9980 | Best single form |
| sqrt(RH+0) → atan | 0.9980 | No offset |
| sqrt(RH+5) → atan | 0.9995 | Better |
| sqrt(RH+8) → power | **0.9997** | **Best composed** |
| atan(0.001*sqrt(RH+8.31)) | 0.9996 | Double composition |

The true Stull formula uses sqrt(RH + 8.313659) inside atan. The composed form with offset=8 comes very close.

### Boundary (Constitution Rule 5)

- Single forms: R²=0.998 (sqrt is best)
- Composed forms: R²=0.9997 (sqrt(RH+8) → power)
- True Stull formula: R²=1.000 (multi-term atan+sqrt)
- Improvement: +0.0016 from composition
- The true formula has MULTIPLE atan terms — not a single composition
- BACON.3 composition helps but cannot discover the full multi-term formula
