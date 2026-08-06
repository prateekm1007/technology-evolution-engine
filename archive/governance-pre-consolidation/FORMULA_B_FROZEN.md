# FORMULA_B_FROZEN — Phase 11

**Status:** frozen. No modifications permitted.
**Location:** repo root (constitutional guardrail).
**Phase:** 11 (per CEO Rule 1).

> Do not modify Formula B. Freeze it.
> — CEO directive, Phase 11, Rule 1

> The temptation will be to adjust constants. That is forbidden.
> — CEO directive, Phase 11, Rule 2

## Formula B (frozen)

```text
score = velocity × adjacency + cost_bonus × 0.3 × adjacency
```

Where:
- velocity = max(dTRL/dt for c in combo) / 2.0, capped at 1.0
- adjacency = 1.0 / (1.0 + min_symmetric_difference_to_existing)
- cost_bonus = min(cost_velocity, 0.5)
- cost_velocity = (cost_before - cost_now) / (cost_before × window)

## Why it's frozen

Formula B achieved 6% Top-10 precision — the first non-zero result
in the project's history. It beat NULL_MODEL (0%), Formula A (0%),
and INEVITABILITY (4%).

The CEO's directive is to expand the EVIDENCE (more time points,
more events, a second domain), not to adjust the FORMULA. If the
formula is modified every time a new data point arrives, we are
fitting — not testing.

## What may change

- The DATA fed to the formula (more time points, more historical events)
- The DOMAIN tested (photovoltaics generalization test)
- The EVALUATION methodology (expanded timeline, bottleneck analysis)

## What may NOT change

- The formula itself (velocity × adjacency + cost_bonus × 0.3 × adjacency)
- The constant 0.3 (cost_bonus weight)
- The constant 2.0 (velocity normalization)
- The min() and max() aggregation functions
- The symmetric_difference distance metric

## Enforcement

Any commit that modifies the Formula B scoring function in
`scripts/run_inevitability_backtest.py` (or any other script) violates
this freeze. The formula is a frozen artifact. New data tests the
frozen formula; the formula does not adapt to new data.
