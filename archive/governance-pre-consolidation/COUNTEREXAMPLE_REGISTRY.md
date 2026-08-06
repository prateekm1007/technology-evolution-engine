# COUNTEREXAMPLE_REGISTRY — Phase 12D

**Status:** evidence layer (counterexamples: predicted success that never occurred).
**Location:** repo root.
**Phase:** 12D.

> Why did the model predict success?
> Why did success never occur?
> — CEO directive, Phase 12D

## Schema

```typescript
interface Counterexample {
    caseId: string;
    timePoint: number;
    predictedCombination: string[];
    formulaScore: number;
    whyPredicted: string;
    whyItFailed: string;
    hiddenVariable: string;
    lesson: string;
}
```

## Counterexamples from the expanded Li-ion backtest

These are Top-10 predictions that scored HIGH but never materialized.

### CE-001: {ELECTRODE_COATING, ELECTRON_COLLECTION}

| Field | Value |
|---|---|
| T | 1991 |
| Score | 1.0000 |
| Why predicted | Both capabilities at TRL 9, high velocity (from 1990→1991 jump), high adjacency (close to existing) |
| Why it failed | This is not an "invention" — it's a manufacturing detail. Combining two mature, stable capabilities doesn't produce a new product. The model conflates "reachable" with "inventable." |
| Hidden variable | These two capabilities were already combined in every Li-ion cell since 1991. The model is predicting something that already existed. |
| Lesson | Adjacency = 0 (already exists) should produce score = 0, not score = high. The model needs a "novelty floor" — combinations that are already realized should score zero. |

### CE-002: {CELL_ASSEMBLY, ELECTRODE_COATING, ION_TRANSPORT, SAFETY_PROTECTION}

| Field | Value |
|---|---|
| T | 2005 |
| Score | 0.8333 |
| Why predicted | All mature, close to existing combinations, cost declining |
| Why it failed | This is a combination of infrastructure capabilities, not a product. Nobody "invents" {assembly + coating + transport + safety} — they're all present in every battery. The model is predicting the BASELINE, not the FRONTIER. |
| Hidden variable | The model rewards "all-mature" combinations, but those are the LEAST likely to produce new inventions. Invention happens at the EDGE of maturity, not at the center. |
| Lesson | The model needs a "frontier signal" — at least one capability should be EMERGING (TRL < 9) for the combination to be invention-relevant. |

### CE-003: {CELL_ASSEMBLY, ELECTRODE_COATING, ELECTRON_COLLECTION, ION_TRANSPORT}

| Field | Value |
|---|---|
| T | 2015 |
| Score | 0.8333 |
| Why predicted | All TRL 9, stable but cost declining, high adjacency |
| Why it failed | These are manufacturing fundamentals. They've been combined since 1991. No new invention. |
| Hidden variable | Same as CE-002: the model rewards the center, not the frontier. |
| Lesson | A combination where ALL capabilities are TRL 9 AND stable (velocity = 0) should score LOW, not high. Velocity = 0 means nothing is changing — no invention pressure. |

## Summary of counterexamples

| Case | Score | Problem | Hidden variable |
|---|---|---|---|
| CE-001 | 1.00 | Already exists (not novel) | No novelty floor |
| CE-002 | 0.83 | All-mature (not frontier) | No frontier requirement |
| CE-003 | 0.83 | All-stable (nothing changing) | Velocity = 0 but score is high |

## The pattern

All three counterexamples involve combinations of **all-mature, all-stable
capabilities**. The model scores them HIGH because:
- Velocity is normalized (max velocity in the combo), and even stable
  capabilities get velocity from the cost_bonus term.
- Adjacency is HIGH because these combinations are close to existing ones
  (they ARE existing ones).
- Feasibility is TRUE because all capabilities are mature.

The model's weakness: it doesn't distinguish "already exists" from
"about to emerge." Both score high. The fix (per FORMULA_B_FROZEN.md:
no modifications) would require a new formula — not a modification of B.

## What this reveals

The counterexamples reveal that Formula B's false positives cluster
around a specific pattern: **all-mature, all-stable combinations that
already exist.** The model is not predicting inventions — it's predicting
the status quo.

The true positives (actual inventions) all involve at least one
capability with non-zero velocity — a rising capability. The false
positives mostly involve all-stable capabilities. This confirms that
VELOCITY is the key discriminative signal, but the current formula
doesn't penalize zero-velocity combinations strongly enough.
