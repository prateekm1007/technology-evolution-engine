# Novelty Formula v1 (experimental)

**Status:** experimental (NOT constitutional).
**Location:** `evidence/experiments/` (per CEO v3.5: formulas are experimental, not constitutional law).
**Constitutional reference:** `NOVELTY.md` Section 3.

This file records the CANDIDATE formula for the Novelty score.
It is a prior, not a fitted constant. It will be revised as the
formula is tested against real data from the one vertical
(electrochemical energy storage). The constitutional document
(NOVELTY.md) commits to the dimensions and invariants, not to
this specific formula.

---

## Candidate formula

```text
Novelty(combination) =
    0.40 * combinatorial_distance(N1)
  + 0.30 * exploration_score(N2)
  + 0.30 * historical_rarity(N3)
```

### Signal definitions

- N1 (combinatorial distance): for a combination C = {c1, ..., cn},
  find all existing combinations that include any subset of C. If
  no existing combination includes all of C, N1 = 1.0 (fully novel).
  If existing combinations include all of C, N1 = 0.0 (fully
  familiar). Otherwise, N1 = 1 - (max overlap / |C|). Normalized
  to [0, 1].

- N2 (exploration score): 1.0 if exploration (at least one capability
  pair has never co-occurred), 0.0 if exploitation (all pairs have
  co-occurred). Fractional for partial exploration.

- N3 (historical rarity): 1 - (count of historical occurrences /
  max count across all combinations). Normalized to [0, 1].

### N4 (exploitation cross-check)

```text
N4 = 1 - Novelty
```

N4 is NOT in the formula — it is a cross-check. If N4 ≠ 1 - Novelty,
the formula has a bug. This invariant is constitutional (recorded in
NOVELTY.md Section 3); the specific computation of N4 is experimental.

### Score range

[0, 1]. A score of 1.0 means the combination is fully novel (never
attempted, fully exploratory, historically rare). A score of 0.0
means the combination is fully familiar (frequently attempted,
exploitation, historically common).

### Weight justification (priors, not fitted)

Combinatorial distance (N1) dominates (0.40) because it is the most
direct operationalization of Fleming's "unfamiliar components."
Exploration (N2) and historical rarity (N3) are equal (0.30 each)
because they capture different aspects of novelty (structural vs
historical).

---

## What would change this formula

1. **Real data from the one vertical.** When capability combinations
   and their historical outcomes are ingested, the weights can be
   tested against the frozen-time backtest (did high-Novelty
   combinations actually have higher outcome variance?).

2. **Fleming's finding may not hold at this scale.** The one-vertical
   scope (50 patents + 50 papers) is small. If the exploitation/
   exploration distinction doesn't manifest at this scale, the
   formula may need to be simplified.

3. **N4 may enter the formula.** If N4 (exploitation) proves to be
   an independent signal rather than a pure inverse, it may be added
   to the formula with its own weight.

---

## Version history

- v1 (this file): initial candidate formula. Priors, not fitted.
  Created during Phase 6 constitutional document writing.
  Not yet tested against real data.
