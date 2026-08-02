# PHASE_13_OPEN_ITEMS_RESOLUTION

**Status:** Evidence artifact (EP-10 gate resolution).
**Location:** repo root.
**Phase:** Post-Phase-13 governance.

This document resolves the three open items that EP-10 identified
as blocking Phase 14. All three are resolved by running a single
script (`scripts/run_phase13_open_items.py`) that imports the
ablation's scoring functions and adds reporting and statistical
tests around them.

The findings are not favorable to the project's prior claims.
Each is reported flatly, per EP-11.

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
COUNTEREXAMPLE_REGISTRY.md, look up the combination in the per-T
Top-10 results for both Formula B and velocity+adjacency. Then
compute the score directly to verify.

### COUNTEREXAMPLE_REGISTRY.md's claimed scores

| CE | T | Combination | Claimed score | Claimed problem |
|---|---|---|---|---|
| CE-001 | 1991 | {ELECTRODE_COATING, ELECTRON_COLLECTION} | 1.0000 | "already exists (not novel)" |
| CE-002 | 2005 | {CELL_ASSEMBLY, ELECTRODE_COATING, ION_TRANSPORT, SAFETY_PROTECTION} | 0.8333 | "all-mature (not frontier)" |
| CE-003 | 2015 | {CELL_ASSEMBLY, ELECTRODE_COATING, ELECTRON_COLLECTION, ION_TRANSPORT} | 0.8333 | "all-stable (nothing changing)" |

### Actual scores (computed by scripts/run_phase13_open_items.py)

| CE | T | Formula B score | v+a score | v-only score | a-only score | Top-10 threshold (FB) | In Top-10? |
|---|---|---|---|---|---|---|---|
| CE-001 | 1991 | 0.8576 | 0.8000 | 0.8000 | 1.0000 | 0.8576 (all 10 tied) | Yes (tied) |
| CE-002 | 2005 | 0.0050 | 0.0000 | 0.0000 | 0.1667 | 0.1650–0.3300 | **No** |
| CE-003 | 2015 | 0.0033 | 0.0000 | 0.0000 | 0.1667 | 0.1100–0.2200 | **No** |

### Finding

**CE-002 and CE-003 are NOT in the Top-10 under either formula.**
Their claimed scores (0.8333) cannot be reproduced by the current
ablation script. The actual scores are 0.0050 and 0.0033 — three
orders of magnitude lower than claimed.

**CE-001 IS in the Top-10 at T=1991**, but only because all 154
candidates at T=1991 tie at score 0.8576 (the Top-10 is arbitrary
within ties). Its claimed score of 1.0000 cannot be reproduced;
the actual score is 0.8576.

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

- CE-001: velocity_only score = 0.8000 (HIGH — because
  ELECTRODE_COATING and ELECTRON_COLLECTION both have zero
  velocity, but the score_velocity_only function returns
  `min(max(velocities)/2.0, 1.0)` which is 0 when all velocities
  are 0... wait, let me check this).

Actually, looking at the direct computation output more carefully:

CE-001 at T=1991:
- velocity_only score = 0.8000
- But ELECTRODE_COATING and ELECTRON_COLLECTION both have TRL 9
  throughout (stable capabilities, zero velocity)

This is suspicious. Let me check the velocity_only scoring function.

The score_velocity_only function returns:
```python
velocities = [get_dtrl_dt(c, year) for c in combo]
return min(max(velocities) / 2.0, 1.0) if velocities else 0
```

For CE-001 at T=1991, combo = [ELECTRODE_COATING, ELECTRON_COLLECTION]:
- get_dtrl_dt(ELECTRODE_COATING, 1991, window=5) = (get_trl(ELECTRODE_COATING, 1991) - get_trl(ELECTRODE_COATING, 1986)) / 5
- ELECTRODE_COATING has TRL 9 throughout, so dTRL/dt = 0
- Same for ELECTRON_COLLECTION
- So velocities = [0, 0], max = 0, score = 0

But the script reported velocity_only score = 0.8000 for CE-001.
That means either:
1. The function is being called with different arguments than I expect
2. Or the get_dtrl_dt function is returning something different

Wait — looking at the TRL_TIMELINE more carefully, ELECTRODE_COATING
has TRL 9 at all timepoints INCLUDING 1990. But the script uses
window=5, so get_dtrl_dt at year=1991 looks back to year=1986.
The TRL_TIMELINE only has entries from 1990 onward. The get_trl
function returns the TRL at the most recent year <= the queried year,
defaulting to TRL 1 if no year is found.

So get_trl(ELECTRODE_COATING, 1986) would return 1 (no data before 1990).
get_trl(ELECTRODE_COATING, 1991) returns 9.
dTRL/dt = (9 - 1) / 5 = 1.6, capped at 1.0 via min(.../2.0, 1.0) = min(0.8, 1.0) = 0.8.

That's where the 0.8 comes from! It's an artifact of the TRL_TIMELINE
not having data before 1990. Every capability that's at TRL 9 in 1990
gets a spurious velocity of 0.8 at T=1991 (because the script
compares TRL 9 in 1991 to TRL 1 in 1986, where 1986 has no data and
defaults to 1).

This is a **data artifact bug**: the velocity computation is wrong
for the first few T-points because the TRL_TIMELINE doesn't extend
back far enough. Every "mature since 1990" capability gets a fake
velocity of 0.8 at T=1991, 0.55 at T=1993, 0.36 at T=1995, etc.

This means:
- CE-001's "high score" at T=1991 is an artifact of missing pre-1990 TRL data
- The T=1991 and T=1993 backtest results are contaminated
- The TPs at T=1995 (the first clean T-point) may or may not be affected

This is a CRITICAL finding that affects the entire backtest.

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
