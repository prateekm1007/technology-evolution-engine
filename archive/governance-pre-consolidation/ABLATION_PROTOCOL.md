# ABLATION_PROTOCOL — Phase 12B

**Status:** constitutional document (ablation study).
**Location:** repo root.
**Phase:** 12B.

> Remove one variable at a time.
> — CEO directive, Phase 12B

## The ablation tests

| Formula | What it tests |
|---|---|
| velocity only | Is velocity sufficient alone? |
| adjacency only | Is adjacency sufficient alone? |
| feasibility only | Is feasibility sufficient alone? |
| velocity + adjacency | Is feasibility redundant? |
| velocity + feasibility | Is adjacency redundant? |
| adjacency + feasibility | Is velocity redundant? |
| **Formula B (full)** | **Baseline (frozen)** |
| NULL_MODEL | Random baseline |

## Interpretation

- If a single variable matches Formula B's precision: the other
  variables are redundant.
- If removing a variable causes precision to DROP: that variable
  contributes independent signal.
- If removing a variable causes precision to STAY THE SAME: that
  variable is redundant.
- If removing a variable causes precision to INCREASE: that variable
  is adding noise.

## The key comparison

The most important comparison is:

```text
velocity only  vs  Formula B (full)
```

If velocity-only achieves similar precision to Formula B, then adjacency
and feasibility are redundant — velocity is doing all the work. This
would simplify the theory dramatically.

If velocity-only is WORSE than Formula B, then adjacency and feasibility
contribute independent signal — the full formula is necessary.
