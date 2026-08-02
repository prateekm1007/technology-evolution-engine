# COMPRESSION_TEST — Phase 12F

**Status:** constitutional document (compression test).
**Location:** repo root.
**Phase:** 12F.

> A scientific theory compresses information.
> If the theory becomes more complicated every time reality disagrees
> with it, then the theory is failing.
> — CEO directive, Phase 12F

## The constitutional rule

```text
Never permit: failure → complexity → success
Permit only:  failure → understanding → simplicity
```

## The measure

```text
explanatory_power
──────────────────
architectural_complexity
```

Where:
- **explanatory power** = number of correct predictions / total predictions
  (precision across all backtest points)
- **architectural complexity** = number of node types + edge types +
  capabilities + constraints + formula factors + scoring parameters

## Current state

### Explanatory power

| Domain | Precision | TP | FP |
|---|---|---|---|
| Li-ion (14-point) | 3.57% | 5 | 135 |
| Photovoltaics | 3.33% | 2 | 58 |
| NULL_MODEL | 0.71% | 1 | 139 |

Combined explanatory power: (5+2) / (5+2+135+58) = 7/200 = 3.5%

### Architectural complexity

| Component | Count |
|---|---|
| Node types | 3 (CAPABILITY, CONSTRAINT, PRODUCT) |
| Edge types | 4 (EMBODIED_IN, REQUIRES, CONSTRAINS, REGULATED_BY) |
| Capabilities (Li-ion) | 10 |
| Capabilities (PV) | 10 |
| Constraints | 5 |
| Formula factors | 3 (velocity, adjacency, cost_bonus) |
| Formula constants | 2 (normalization 2.0, weight 0.3) |
| Governance documents | 30+ |
| Epistemic layer items | 11 principles + 5 assumptions |

Total architectural complexity: ~80 distinct components.

### Compression ratio

```text
3.5% explanatory power / 80 components = 0.044% per component
```

This is LOW. The model has many components but explains few outcomes.
The theory is not compressing efficiently.

## The test

The compression test asks: **can the model achieve the same or better
explanatory power with FEWER components?**

If the ablation study (Phase 12B) shows that velocity-only achieves
similar precision to the full Formula B, then:
- Explanatory power stays the same (~3.5%)
- Architectural complexity drops (remove adjacency, feasibility, cost_bonus)
- Compression ratio IMPROVES

If adding more components (more capabilities, more constraints, more
formula factors) does NOT improve explanatory power, then:
- Explanatory power stays the same
- Architectural complexity increases
- Compression ratio WORSENS
- The theory is failing (adding complexity without adding explanation)

## The rule in practice

When a prediction fails, the response must be:

```text
failure → understand WHY → simplify the model → re-test
```

NOT:

```text
failure → add a new factor → add a new constraint → re-test until it passes
```

The second path is overfitting. The first path is science.

## Historical tracking

| Phase | Components | Precision | Compression | Trend |
|---|---|---|---|---|
| Phase 5 (co-occurrence) | ~50 | 0% | 0.000 | — |
| Phase 9 (Formula A) | ~60 | 0% | 0.000 | worse (more complexity, same power) |
| Phase 10 (Formula B) | ~70 | 6% (5pt) | 0.086 | better (power emerged) |
| Phase 11 (expanded) | ~80 | 3.5% | 0.044 | worse (complexity grew faster than power) |

The trend is concerning: complexity is growing faster than power.
The Phase 11 expansion added components (registries, protocols,
assumptions) but precision dropped (from 6% to 3.5%).

The model needs to SIMPLIFY, not add more. The ablation study
(Phase 12B) is the tool for this: remove components and see if
precision holds. If it does, the removed components were complexity
without value.
