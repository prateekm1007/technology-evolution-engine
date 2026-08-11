# ADJACENCY_PROTOCOL — Phase 10B

**Status:** constitutional document (replace novelty with adjacency).
**Location:** repo root.
**Phase:** 10B.

> The adjacent possible matters more than the unimaginable possible.
> — CEO directive, Phase 10B

## The rejection

The previous formula used:
```text
novelty = 1 - max_jaccard_similarity(combo, existing_combos)
```

This measures how UNUSUAL a combination is. It fails because most
unusual combinations are worthless (Failure C: "Most untried
combinations are worthless"). And Fleming showed that successful
inventions often arise from RECOMBINATIONS of FAMILIAR components —
not from maximally distant ones.

The novelty formula rewarded distance from existing, but real
inventions are often CLOSE to existing — one step away, not ten.

## The replacement

Replace:
```text
novelty = how unusual is this? (1 - similarity)
```

With:
```text
adjacency = how far away is this? (graph distance)
```

The question changes from "how unique?" to "how reachable?"

## Candidate measures

| Measure | What it captures | Formula (candidate) |
|---|---|---|
| Graph distance | Shortest path between capabilities in the dependency graph | min_path_length(c_i, c_j) for all pairs in combo |
| Combinatorial distance | How many NEW edges would need to be created? | count of missing REQUIRES edges between combo members |
| Dependency distance | How deep is the dependency chain? | longest REQUIRES path from any combo member to a root capability |
| Cost distance | How far is the cost from the economic threshold? | cost_threshold(T) - actual_cost(T) |
| Institutional distance | How many regulatory gates stand between here and deployment? | count of REGULATED_BY edges not yet satisfied |

## The Kauffman connection

Kauffman's "adjacent possible" is the set of things reachable in
one combinatorial step from the current state. The model should
identify combinations that are in the adjacent possible — one step
away — not combinations that are maximally distant.

A combination in the adjacent possible:
- Shares most capabilities with existing combinations
- Has ONE capability that just became reachable (TRL crossed threshold)
- Is connected to existing combinations via REQUIRES edges

A combination outside the adjacent possible:
- Requires capabilities that don't exist yet
- Has no path from existing combinations
- Is "imaginable but not reachable"

## Adjacency-based scoring (candidate formula)

```text
adjacency_score(combo, T) =
    1 / (1 + graph_distance(combo, nearest_existing_combination))
```

High adjacency (low distance) = high score. Combinations one step
from existing ones score higher than combinations ten steps away.

This INVERTS the novelty formula: instead of rewarding distance,
we reward PROXIMITY to the adjacent possible.
