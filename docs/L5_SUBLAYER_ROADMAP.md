# L5 Sublayer Roadmap — Computational Search Theory (cycle 229)

## Honest Status (per auditor update #19)

The auditor correctly distinguished:
- **"optimizer invention"** (AlphaDev sense: discovers NEW algorithms)
- **"program synthesis"** (current L5a: recombines FIXED primitives)

The cycle 228 module was described as "inventing optimizers." That was
overselling. The DSL already contains `FIT_SURROGATE` and `ACQUIRE_EI` —
those are Bayesian-optimization concepts. The search discovers useful
**compositions** of known operators, not new operators.

The honest claim: **"discovered effective optimizer programs over a
fixed operator language."**

## The L5 Sublayers

### L5a — Program Discovery (WORKING, maturity 7.8/10)

Search over programs composed from a FIXED DSL of known operators.

- **What it does**: random search over sequences of 13 primitives
  (sample, select, narrow, widen, crossover, mutate, fit_surrogate,
  acquire_ei, etc.)
- **What it proved**: discovered programs beat GreedyHillClimber on 4/7
  held-out synthetic landscapes
- **What it did NOT prove**: it did not invent new operators or new
  algorithmic concepts. The discovered programs converged on
  `fit_surrogate → acquire_ei` — a known pattern (poor man's Bayesian
  optimization), rediscovered from scratch.
- **The real contribution**: the ARCHITECTURAL INVERSION
  ```
  OLD: engineer → writes optimizer → optimizer searches designs
  NEW: search → creates optimizer → optimizer searches designs
  ```
  That recursion is the important part. Changing the search procedure
  (random → evolution → MCTS → RL → beam → CEM) does NOT require
  rewriting the architecture.

### L5b — Operator Discovery (NOT STARTED, maturity ~2/10)

Search for NEW reusable operators (primitives that don't exist in the
current DSL).

Examples of operators a human expert might design:
- `LOCAL_CURVATURE_ESTIMATE` — estimate local second-derivative
- `ENTROPY_GUIDED_MUTATION` — mutation direction chosen by entropy
- `CONSTRAINT_PRESSURE` — push away from constraint boundaries
- `LANDSCAPE_EMBEDDING` — project landscape to a feature vector

The L5b search would discover operators like these by:
1. Defining a meta-DSL for operator construction (input → transform → output)
2. Searching over operator definitions
3. Adding useful discovered operators to the L5a DSL

This is closer to AlphaDev's actual contribution (discovering new
sorting network primitives, not just recombining compare-swap).

### L5c — Language Discovery (CONCEPTUAL, maturity ~1/10)

Search over the DSL itself — invent new operator CATEGORIES.

Today the DSL has: sampling ops, selection ops, narrowing ops,
surrogate ops. These categories are human-defined.

L5c would ask: what NEW categories of operations exist that humans
haven't thought of? This requires:
- A meta-language for defining operator types
- A search over type signatures
- An evaluation of whether a new category adds expressive power

This is the deepest sublayer — it questions the assumptions of the
DSL itself.

### L5d — Theory Discovery (CONCEPTUAL, maturity ~1/10)

Explain WHY discovered operators work — derive the theoretical
properties of discovered programs.

Today: we know a program works (it beats the portfolio) but not WHY.
L5d would:
- Analyze a discovered program's convergence properties
- Derive its landscape-type preferences theoretically
- Connect it to known optimization theory (e.g., "this program is
  equivalent to CMA-ES with diagonal covariance under these conditions")

This is the "understanding" layer — it turns empirical discoveries
into theoretical contributions.

## The Blind Benchmark (the key missing test)

Per auditor: "Take 20 completely unrelated optimization problems
(Ackley, Rosenbrock, TSP, SAT, Job Shop, Portfolio Optimization,
Bayesian hyperparameter tuning, Circuit placement, Protein toy
folding, Symbolic regression, etc.). Hide their names. Only expose
`sample()` and `evaluate()` to the engine."

If L5a consistently discovers optimizer programs that outperform a
reasonable baseline across that blind suite, *without domain labels*,
that's a much stronger demonstration than success on technology
domains alone. It would show the search machinery is learning
optimization strategies rather than exploiting characteristics of a
familiar application area.

**Status**: NOT YET BUILT. This is the next priority for L5a.

## Pareto Optimizer Discovery (future enhancement)

Per auditor: "if one optimizer beats another by 0.5% but is 10×
simpler, that's arguably the more important discovery."

Instead of maximizing score alone, optimize:
```
(score, complexity, runtime, robustness, transferability)
```

Now optimizer discovery becomes multi-objective. The Pareto frontier
of (score vs complexity) reveals which discovered programs are
genuinely efficient vs which are overfit.

**Status**: NOT YET BUILT. This is a refinement for L5a once the
blind benchmark is in place.

## Maturity Summary

| Sublayer | Maturity | Status |
|----------|---------:|--------|
| L5a — Program Discovery | 7.8/10 | WORKING (random search, fixed DSL) |
| L5b — Operator Discovery | 2/10 | NOT STARTED (conceptual) |
| L5c — Language Discovery | 1/10 | CONCEPTUAL ONLY |
| L5d — Theory Discovery | 1/10 | CONCEPTUAL ONLY |

**Honest overall claim**: "L5a has been successfully bootstrapped.
The first sublayer — program discovery over a fixed DSL — is working.
The remaining research challenge is to make the language of
optimization itself evolvable (L5b/c), and to demonstrate that
discovered programs generalize across a broad, blind benchmark suite."
