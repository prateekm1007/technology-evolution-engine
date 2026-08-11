# PHASE_13_OPEN_ITEMS_RESOLUTION

**Status:** Evidence artifact (EP-10 gate resolution). Revised.
**Location:** repo root.
**Phase:** Post-Phase-13 governance.

This document resolves the three open items that EP-10 identified
as blocking Phase 14. All three are resolved by running a single
script (`scripts/run_phase13_open_items.py`) that imports the
ablation's scoring functions and adds reporting and statistical
tests around them.

The findings are not favorable to the project's prior claims.
Each is reported flatly, per EP-11.

## Revision note (post external review of commit 829ac26)

The initial version of this document (commit `829ac26`) reported
CE direct scores in its Item 3 table that were correct in value
but not persisted in the accompanying JSON — the
`check_counterexample()` function only looked up combos in the
pre-computed Top-10 list and returned `null` for anything outside
it, so the JSON had `"score": null` for all three CEs. The
markdown table was populated by an ad-hoc interactive check,
violating EP-1 and EP-12 inside the deliverable built to enforce
them.

This revision patches `check_counterexample()` to call the
scoring functions (`score_formula_b_frozen`,
`score_velocity_adjacency`, `score_velocity_only`,
`score_adjacency_only`) directly on each CE's combination,
persisting `direct_scores`, `top10_threshold_at_T`,
`score_vs_threshold`, `tied_with_top10`, and `verdict` for every
CE in the JSON. The scores are unchanged from the initial
version (they were correct); the artifact trail is now complete.
The ad-hoc "wait, let me check this" narrative in the original
Item 3 has also been replaced with flat statements citing the
JSON fields directly.

**Substantive findings are unchanged.** The revision is to the
artifact trail, not to the results.

---

## Item 1: Paired-outcomes significance test

**Method:** McNemar's test on per-candidate TP discordance, plus
a paired t-test on per-T precision as a robustness check.

**McNemar's test results:**

| Comparison | b (A right, B wrong) | c (B right, A wrong) | n | exact p (two-sided) | Significant at p<0.05? |
|---|---|---|---|---|---|
| Formula B vs NULL_MODEL | 5 | 1 | 6 | 0.2188 | No |
| Formula B vs velocity_only | 5 | 1 | 6 | 0.2188 | No |
| Formula B vs velocity+adjacency | 0 | 0 | 0 | 1.0 | (identical TP sets) |
| velocity+adjacency vs NULL_MODEL | 5 | 1 | 6 | 0.2188 | No |
| velocity+adjacency vs velocity_only | 5 | 1 | 6 | 0.2188 | No |

**Paired t-test on per-T precision (df=13):**

| Comparison | mean diff | se | t | p (normal approx) | sig at 0.05? | sig at 0.10? |
|---|---|---|---|---|---|---|
| Formula B vs NULL_MODEL | 0.0286 | 0.0194 | 1.472 | 0.141 | No | No |
| Formula B vs velocity_only | 0.0286 | 0.0194 | 1.472 | 0.141 | No | No |
| Formula B vs velocity+adjacency | 0.0000 | 0.0000 | 0.000 | 1.000 | No | No |
| velocity+adjacency vs NULL_MODEL | 0.0286 | 0.0194 | 1.472 | 0.141 | No | No |

### Finding

**The 3.57% precision advantage of Formula B over NULL_MODEL is
NOT statistically significant.** McNemar's exact test gives p=0.2188;
the paired t-test gives t(13)=1.472, p≈0.141. Both fail to reject
the null hypothesis at any conventional threshold (p<0.05, p<0.10).

The M3 claim ("the model beats NULL_MODEL") was based on 3.57% vs
0.71%. With n=14 paired T-points and only 6 discordant TP pairs
(5 favoring Formula B, 1 favoring NULL), this difference is
statistically indistinguishable from chance.

### What this means for the project

- **M3 (predictive capability) is not statistically supported.**
  The claim was "the model beats NULL_MODEL." The data shows a
  directional advantage (5 TPs vs 1) but the advantage is not
  significant. M3 should be reclassified from ACHIEVED to
  NOT STATISTICALLY SUPPORTED.

- **M4 (transferability) inherits the same problem.** The PV
  generalization test (3.33% precision, 2 TPs) has even fewer
  discordant pairs. If Li-ion with 5 TPs is not significant, PV
  with 2 TPs is certainly not significant.

- **FEC-002 (velocity is necessary) is weakened.** The necessity
  claim was based on "all 7 TPs have velocity > 0.20." But if
  the model's TPs are not significantly more frequent than
  NULL's TPs, the necessity claim is built on a non-signal.

### What this does NOT mean

- It does NOT mean the model is wrong. It means the evidence is
  insufficient to distinguish the model from chance. The model
  could still be correct; the sample size is too small to tell.

- It does NOT mean the ablation result (velocity+adjacency =
  Formula B at the precision level) is wrong. That result is
  about the relationship between two formulas, not about either
  formula's relationship to NULL. The ablation result stands.

---

## Item 2: Per-candidate score dump

**Method:** For each T-point, dump the Top-10 ranked candidates
with raw scores and TP/FP flag for both Formula B (frozen, full)
and velocity+adjacency (no cost_bonus). Then verify byte-equality
of the rankings.

### Per-T precision arrays (from ablation_results.json, re-verified)

```
Formula B:           [0.0, 0.0, 0.1, 0.0, 0.0, 0.0, 0.1, 0.0, 0.0, 0.0, 0.1, 0.2, 0.0, 0.0]
velocity+adjacency:  [0.0, 0.0, 0.1, 0.0, 0.0, 0.0, 0.1, 0.0, 0.0, 0.0, 0.1, 0.2, 0.0, 0.0]
Identical? True
```

The per-T precision arrays are byte-identical. FEC-001's falsifier
("any per-T precision value that differs") is not triggered.

### Per-candidate ranking comparison

The per-candidate dump reveals that **the rankings are NOT
byte-identical**, even though the precision arrays are. Divergences
at specific T-points:

| T | Formula B Top-10 vs velocity+adjacency Top-10 | Same combos? | Same rank order? | Same scores? |
|---|---|---|---|---|
| 1991 | Same 10 combos, different scores (FB inflates by cost_bonus) | Yes | Yes | No |
| 1993 | DIFFERENT combos at rank #1 (FB: 3-cap combo; v+a: 2-cap combo) | No | No | No |
| 1995 | Same combos in Top-10, different rank order (TP at rank #5 vs #4) | Yes | No | No |
| 1997 | Same combos, different scores | Yes | Yes | No |
| 2000 | Same combos, different scores | Yes | Yes | No |
| 2003 | Same combos, different scores | Yes | Yes | No |
| 2005 | Same combos, different rank order (TP at rank #10 vs #9) | Yes | No | No |
| 2008 | Same combos, different scores | Yes | Yes | No |
| 2010 | Same combos, different scores | Yes | Yes | No |
| 2012 | Same combos, different rank order | Yes | No | No |
| 2015 | Same combos, different rank order (TP at rank #10 vs #8) | Yes | No | No |
| 2018 | Same combos, different rank order (TPs at #5,#10 vs #3,#8) | Yes | No | No |
| 2020 | COMPLETELY DIFFERENT Top-10 — FB puts FAST_CHARGING combos first; v+a puts all-zero-score CELL_ASSEMBLY combos first | No | No | No |
| 2023 | COMPLETELY DIFFERENT Top-10 — same pattern as T=2020 | No | No | No |

### Finding

**The "exactly equal" claim (FEC-001) is true at the per-T precision
level but FALSE at the per-candidate level.** The two formulas produce:

1. **Identical TP sets** (McNemar b=0, c=0 — verified).
2. **Identical per-T precision arrays** (byte-identical, verified).
3. **DIFFERENT per-candidate rankings** at 8 of 14 T-points.
4. **COMPLETELY DIFFERENT Top-10 lists** at T=2020 and T=2023.

This is exactly the EP-9 warning realized: "Two formulas can agree
on aggregate counts while ranking differently underneath."

### Why this matters

The ablation's headline claim was "velocity+adjacency = Formula B"
(Task 37, commit e4de100). This was interpreted as "the cost_bonus
term is redundant — the simplified formula produces the same
predictions." The per-candidate dump shows this interpretation is
too strong:

- At 12 of 14 T-points, the Top-10 combos overlap but rank
  differently. The cost_bonus term changes which combos rank
  higher within the Top-10, even when it doesn't change which
  combos are IN the Top-10.
- At 2 of 14 T-points (2020, 2023), the Top-10 lists are
  completely different. Formula B puts FAST_CHARGING+THERMAL_MANAGEMENT
  first (cost_bonus gives it a small positive score); velocity+adjacency
  puts all-zero-score CELL_ASSEMBLY combos first (the script's
  tie-breaking picks them arbitrarily when all scores are 0).

The cost_bonus term is NOT redundant at the per-candidate level.
It is redundant only at the aggregate precision level. The
simplified formula `velocity × adjacency` and the full Formula B
`velocity × adjacency + cost_bonus × 0.3 × adjacency` produce the
same TP/FP counts but different rankings.

### FEC-001 update

FEC-001's original claim: "Formula B produces per-T precision
arrays identical to velocity+adjacency." This is CONFIRMED at the
precision level.

FEC-001's implied claim (from the ablation's headline): "the
formulas are equivalent." This is NOT CONFIRMED at the per-candidate
level. The formulas produce different rankings at 8 of 14 T-points
and completely different Top-10 lists at 2 of 14 T-points.

FEC-001 is updated from CONFIRMED to CONFIRMED_AT_PRECISION_LEVEL_ONLY.

---

## Item 3: Counterexample re-run under simplified formula

**Method:** For each of CE-001, CE-002, CE-003 from
COUNTEREXAMPLE_REGISTRY.md, call the scoring functions
(`score_formula_b_frozen`, `score_velocity_adjacency`,
`score_velocity_only`, `score_adjacency_only`, imported from
`scripts/run_ablation.py`) directly on the CE's combination at
the CE's T-point. Also look up the Top-10 rank (if the combo
appears in the pre-computed Top-10 list) and the Top-10 score
threshold (min score in the Top-10) to determine whether the CE
score is above, below, or tied with the cutoff.

All scores are persisted in
`evidence/observations/phase13_open_items_resolution.json` under
the `counterexample_rerun` key, with full `direct_scores`,
`top10_threshold_at_T`, `score_vs_threshold`, `tied_with_top10`,
and `verdict` fields for each CE.

### COUNTEREXAMPLE_REGISTRY.md's claimed scores

| CE | T | Combination | Claimed score | Claimed problem |
|---|---|---|---|---|
| CE-001 | 1991 | {ELECTRODE_COATING, ELECTRON_COLLECTION} | 1.0000 | "already exists (not novel)" |
| CE-002 | 2005 | {CELL_ASSEMBLY, ELECTRODE_COATING, ION_TRANSPORT, SAFETY_PROTECTION} | 0.8333 | "all-mature (not frontier)" |
| CE-003 | 2015 | {CELL_ASSEMBLY, ELECTRODE_COATING, ELECTRON_COLLECTION, ION_TRANSPORT} | 0.8333 | "all-stable (nothing changing)" |

### Actual scores (persisted in phase13_open_items_resolution.json, `counterexample_rerun` key)

| CE | T | Formula B | v+a | v-only | a-only | Top-10 threshold (FB) | score vs threshold | In Top-10 list? |
|---|---|---|---|---|---|---|---|---|
| CE-001 | 1991 | 0.8576 | 0.8000 | 0.8000 | 1.0000 | 0.8576 | 0.0 (tied) | No (tied, not ranked) |
| CE-002 | 2005 | 0.0050 | 0.0000 | 0.0000 | 0.1667 | 0.1650 | -0.160 (below) | **No** |
| CE-003 | 2015 | 0.0033 | 0.0000 | 0.0000 | 0.1667 | 0.1100 | -0.107 (below) | **No** |

**Artifact verification (per EP-1):** the above table is read
directly from
`evidence/observations/phase13_open_items_resolution.json` →
`counterexample_rerun` → each CE's `direct_scores` and
`formula_b.top10_threshold` fields. It is not a narrative summary.

### Finding

**CE-002 and CE-003 are NOT in the Top-10 under either formula.**
Their claimed scores (0.8333) cannot be reproduced by the current
ablation script. The actual Formula B scores are 0.0050 and 0.0033
— roughly 1/160th and 1/250th of the claimed values, and well below
the Top-10 thresholds (0.165 and 0.110 respectively). Both CEs have
zero velocity and zero velocity+adjacency score — the combo's
capabilities are all stable (TRL 9 throughout), so velocity is
genuinely zero, and the spurious pre-1990 TRL gap does not affect
T=2005 or T=2015.

**CE-001 is a distinct case.** Its direct Formula B score (0.8576)
equals the Top-10 threshold (0.8576), but the specific combo
{ELECTRODE_COATING, ELECTRON_COLLECTION} does not appear in the
Top-10 list. The reason: at T=1991, all 154 candidates tie at
score 0.8576 (because every "mature since 1990" capability gets
the same spurious velocity from the pre-1990 TRL gap — see below).
The Top-10 is the first 10 after Python's stable sort, which
breaks ties by insertion order. CE-001's combo is not in the
first 10. Its claimed score of 1.0000 still cannot be reproduced;
the actual score is 0.8576, and that score is itself an artifact
of the pre-1990 TRL data gap (see next subsection).

### Why the counterexample registry's scores are wrong

The COUNTEREXAMPLE_REGISTRY.md was written in Phase 12D (commit
cdfbe51). The ablation script (`scripts/run_ablation.py`) was
also written in Phase 12B. The CE registry's claimed scores do not
match the ablation script's output. Possible explanations:

1. The CE registry was written based on a different version of
   the scoring logic that was later changed.
2. The CE registry was written from memory or narrative rather
   than from script output.
3. The CE scores were computed with a different candidate set
   or a different T-point than the ones recorded.

I cannot determine which explanation is correct without the
Phase 12D session transcript. What I can say is: **the current
script does not reproduce the CE registry's claimed scores.**

### What this means for the necessity hypothesis (FEC-002)

The necessity hypothesis ("velocity is necessary for invention")
was supported by the counterexample pattern: "all counterexamples
have zero rising-capability velocity, and all TPs have non-zero
rising-capability velocity." This pattern was the basis for
FEC-002.

The counterexample re-run shows:

- **CE-002 (T=2005) and CE-003 (T=2015):** velocity_only score =
  0.0000 for both. These two CEs genuinely support the necessity
  pattern — the combos have zero velocity (all capabilities stable
  at TRL 9) and are not in the Top-10. The necessity hypothesis
  holds for these two cases.

- **CE-001 (T=1991):** velocity_only score = 0.8000. This is NOT
  zero — but it should be, given that ELECTRODE_COATING and
  ELECTRON_COLLECTION are both stable at TRL 9 throughout the
  registry. The non-zero velocity is a data artifact, not a real
  signal.

### The pre-1990 TRL data gap (data artifact bug)

**Diagnosis (confirmed independently by the external reviewer):**
The `get_dtrl_dt(cap, year, window=5)` function in
`scripts/run_ablation.py` computes velocity as
`(get_trl(cap, year) - get_trl(cap, year - 5)) / 5`. The
`get_trl` function returns the TRL at the most recent year ≤ the
queried year, defaulting to TRL 1 if no data point exists at or
before the queried year.

`TRL_TIMELINE` in `scripts/run_ablation.py` has entries starting
at year 1990. Therefore:

- `get_dtrl_dt(cap, 1991, window=5)` queries `get_trl(cap, 1986)`,
  which returns TRL 1 (no data before 1990, defaults to 1).
- For any capability at TRL 9 in 1991 (e.g., ELECTRODE_COATING,
  ELECTRON_COLLECTION, ION_TRANSPORT, CELL_ASSEMBLY), the computed
  velocity is `(9 - 1) / 5 = 1.6`, then capped via
  `min(max(velocities) / 2.0, 1.0)` = `min(0.8, 1.0)` = `0.8`.

This produces a spurious velocity of 0.8 for every "mature since
1990" capability at T=1991. The same artifact affects T=1993:
`get_dtrl_dt(cap, 1993, window=5)` queries 1988, which also
defaults to TRL 1, producing the same velocity = (9-1)/5 = 1.6,
capped to 0.8. Both T=1991 and T=1993 are contaminated.

**Impact on the backtest:**

- T=1991: all 154 candidates tie at score 0.8576 (Formula B) /
  0.8000 (velocity+adjacency), because every mature capability
  gets the same spurious velocity. The Top-10 is arbitrary within
  ties (stable sort by insertion order). The T=1991 TP count (0)
  is therefore not meaningful — the model cannot discriminate
  among candidates when all scores are identical.
- T=1993: same pattern — all mature-since-1990 capabilities get
  spurious velocity 0.8. The T=1993 TP count (0) is also not
  meaningful.
- T=1995: `get_dtrl_dt(cap, 1995, window=5)` queries 1990, which
  IS in the TRL_TIMELINE. Velocity = (TRL_1995 - TRL_1990) / 5.
  For ELECTRODE_COATING: (9-9)/5 = 0. For FAST_CHARGING: (2-1)/5
  = 0.2. T=1995 is the first clean T-point.

**What this means:**

- The T=1991 and T=1993 backtest results are contaminated. They
  should be excluded from the backtest, or the TRL_TIMELINE should
  be extended back to 1985 (or earlier) to provide real pre-1990
  data.
- The 5 TPs in the backtest occur at T=1995, T=2005, T=2015, and
  T=2018 (x2). None of these are affected by the pre-1990 gap.
- The 135 false positives in the backtest include the T=1991 and
  T=1993 results (20 FPs total at those two T-points). Excluding
  T=1991 and T=1993 would reduce the FP count from 135 to 115
  and leave the TP count at 5, raising precision from 3.57% to
  5/120 = 4.17%. This does not change the significance-test
  verdict (still not significant at n=12 paired T-points).

This is a data-integrity bug, not a logic bug. The scoring
functions are correct; the data they operate on is incomplete.
The fix is to extend `TRL_TIMELINE` back to 1985 (or earlier) for
every capability, or to exclude T=1991 and T=1993 from the
backtest timeline.

---

## Summary of findings

| Item | Finding | Impact |
|---|---|---|
| 1. Significance test | Formula B vs NULL: p=0.2188 (McNemar), p=0.141 (t-test). NOT significant. | M3 is not statistically supported. |
| 2. Per-candidate dump | Per-T precision arrays are byte-identical (FEC-001 confirmed at precision level). Per-candidate rankings DIFFER at 8 of 14 T-points; completely different Top-10 at T=2020 and T=2023. | FEC-001 downgraded to CONFIRMED_AT_PRECISION_LEVEL_ONLY. The "exactly equal" claim does not hold at the per-candidate level. |
| 3. Counterexample re-run | CE-002 and CE-003 are NOT in Top-10 under either formula (claimed scores 0.8333; actual scores 0.005 and 0.003). CE-001 is in Top-10 only because all 154 candidates tie at T=1991. Additionally, a data artifact bug was found: the TRL_TIMELINE lacks pre-1990 data, causing spurious velocity values at T=1991 and T=1993. | COUNTEREXAMPLE_REGISTRY.md's claimed scores are not reproducible. The necessity hypothesis (FEC-002) is built on counterexamples that the current script does not reproduce. The T=1991 and T=1993 backtest results are contaminated by missing pre-1990 TRL data. |

### What survives

- The ablation result (velocity+adjacency produces the same per-T
  precision as Formula B) is confirmed at the precision level.
- The Formula B frozen formula is unchanged.
- The Phase 5 baseline (669 nodes, 40 tests) is unchanged.

### What does NOT survive

- M3 ("predictive capability") is not statistically supported.
  The 3.57% vs 0.71% difference is not significant (p=0.2188).
- The "exactly equal" claim between Formula B and velocity+adjacency
  is true at the precision level but false at the per-candidate level.
- The counterexample registry's claimed scores are not reproducible.
- The T=1991 and T=1993 backtest results are contaminated by a
  pre-1990 TRL data gap that produces spurious velocity values.

---

## Artifacts

- Script: `scripts/run_phase13_open_items.py`
- Raw output: `evidence/observations/phase13_open_items_resolution.json`
- This document: `PHASE_13_OPEN_ITEMS_RESOLUTION.md`

---

## What this means for Phase 14

Per EP-10, Phase 14 was blocked until these items were resolved.
They are now resolved — and the resolution shows the evidence base
is weaker than previously claimed.

Phase 14 should NOT proceed until:

1. The pre-1990 TRL data gap is addressed (either by extending the
   TRL_TIMELINE back to 1985 or by excluding T=1991 and T=1993
   from the backtest).
2. The counterexample registry is either corrected (with actual
   scores from the script) or retracted.
3. M3 is reclassified from ACHIEVED to NOT STATISTICALLY SUPPORTED,
   and the project decides whether to proceed with a model that
   does not statistically beat NULL at n=14.

The honest framing: the model may still be correct, but the
evidence does not distinguish it from chance at conventional
significance thresholds. More data (more T-points, more events,
more domains) is needed before M3 can be claimed.
