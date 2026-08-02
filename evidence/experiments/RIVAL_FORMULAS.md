# RIVAL_FORMULAS — Phase 10E

**Status:** experimental document (competing scoring formulas).
**Location:** `evidence/experiments/` (NOT constitutional — per CEO rule: no formula is constitutional).
**Phase:** 10E.

> The current model has only one formula. That is dangerous.
> Construct competing hypotheses.
> — CEO directive, Phase 10E

> No formula is allowed to become constitutional.
> — CEO rule, Phase 10E

## The five rival formulas

### Formula A (REJECTED — the old formula)

```text
score = readiness × novelty × feasibility
```

**Status:** REJECTED. Failed both uncalibrated and calibrated backtests.
Root cause: min(readiness) penalizes emerging capabilities; 1-jaccard(novelty)
rewards distance from existing. The formula's assumptions are inverted.

### Formula B (candidate — trajectory + adjacency)

```text
score = velocity × adjacency × feasibility
```

Where:
- velocity = max(dTRL/dt for c in combo) — the FASTEST-RISING capability
  (not the weakest). Innovation happens when something is about to break through.
- adjacency = 1 / (1 + graph_distance) — proximity to the adjacent possible.
  Close to existing = reachable. Far from existing = imagination.
- feasibility = boolean AND of constraint gates (unchanged from Phase 9).

**Hypothesis:** inventions emerge where capabilities are RISING FAST and
are CLOSE to existing combinations.

**Why this might work:** replaces the two wrong assumptions (min penalizes
emerging; 1-jaccard rewards distance) with their inversions (max rewards
rising; adjacency rewards proximity).

### Formula C (candidate — constraint removal + capability growth)

```text
score = constraint_removal_rate × capability_growth_rate
```

Where:
- constraint_removal_rate = how fast is the blocking constraint weakening?
  (d(constraint_strength)/dt < 0)
- capability_growth_rate = how fast are the capabilities improving?
  (d(TRL)/dt > 0)

**Hypothesis:** inventions emerge when constraints are being REMOVED
and capabilities are GROWING simultaneously. The intersection of these
two trends creates inevitability.

**Why this might work:** doesn't ask "is this ready?" — asks "are things
moving in the right direction?" Static readiness doesn't predict; velocity does.

### Formula D (candidate — bottleneck resolution)

```text
score = 1 / time_to_resolution(bottleneck(combo, T))
```

Where:
- bottleneck(combo, T) = the single constraint that, if removed, would
  make the combination feasible.
- time_to_resolution = estimated time until the bottleneck is removed
  (based on trajectory of the constraint).

**Hypothesis:** the most invention-relevant combinations are those whose
SINGLE blocking constraint is about to be removed.

**Why this might work:** inventions happen when bottlenecks are removed.
A combination with 10 satisfied constraints and 1 blocking constraint
is more invention-relevant than one with 0 blocking constraints (already
exists) or 10 blocking constraints (too far away).

### Formula E (candidate — expert judgment)

```text
score = human_expert_assessment(combo, T)
```

Where:
- A domain expert (battery engineer, materials scientist) ranks the
  combinations manually.

**Hypothesis:** human domain knowledge captures factors the model misses
(supply chain, geopolitics, company strategy, market timing).

**Why this matters:** if Formula E outperforms B, C, and D, the machine
models are missing something fundamental. If B, C, or D outperform E,
the machine has captured something the expert's intuition misses.

## Testing protocol

Each formula will be tested against the same frozen-time backtest:
1. Generate predictions at T using the formula.
2. Evaluate at T+n.
3. Compute precision, recall, false positives, false negatives.
4. Compare to NULL_MODEL and to the other formulas.

The formula that achieves the highest precision (while maintaining
recall > 0) becomes the LEADING CANDIDATE. It does NOT become
constitutional — it remains experimental, subject to further testing
and potential replacement.

## The rule

No formula becomes constitutional. Formulas are experiments. They
live in `evidence/experiments/`. They are tested, revised, or
rejected based on evidence — not promoted to governance.
