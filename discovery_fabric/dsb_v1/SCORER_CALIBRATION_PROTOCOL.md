# SCORER-CALIBRATION PROTOCOL

**Date:** 2026-08-12
**Status:** PROTOCOL DEFINED. Calibration set NOT YET BUILT.

---

## 1. Purpose

The DSB V1 deterministic scorer is **FROZEN**. It must NOT be tuned on the 80 DSB V1 cases — doing so would be data snooping.

If human adjudication of the 80 DSB V1 cases reveals systematic false positives (e.g., the scorer gives high DISCOVERY_STRUCTURE_RECOVERY scores to cases that humans judge as NOT_RECOVERED), a **separate scorer-calibration set** must be created. The scorer may be tuned ONLY on this separate set, then re-evaluated on the DSB V1 80 cases (one-shot, no further tuning).

---

## 2. Frozen Scorer Policy

The DSB V1 scorer (`discovery_fabric/dsb_v1/scorer.py`) is FROZEN at commit `a0a316f6`. The freeze manifest (`FREEZE_MANIFEST.json`) records its SHA-256 hash.

**Prohibited:**
- Modifying `scorer.py` based on observations from the 80 DSB V1 cases
- Adjusting the 0.50 threshold based on DSB V1 results
- Changing the sub-score weights (0.5 / 0.25 / 0.25) based on DSB V1 results
- Adding new relation-type patterns based on DSB V1 failures
- Re-running the scorer after "fixes" and reporting the new numbers as DSB V1 results

**Permitted:**
- Building a NEW scorer (e.g., `scorer_v2.py`) that is calibrated on a separate set
- Reporting both the FROZEN v1 scorer results AND the v2 scorer results, clearly labeled
- Using the DSB V1 80 cases ONLY as a held-out evaluation set for v2

---

## 3. Calibration Set Specification

If human adjudication reveals systematic false positives, build a calibration set with these properties:

### 3.1 Size
- Minimum 40 cases (20 real + 20 fabricated), structured identically to DSB V1 cases
- Drawn from DIFFERENT historical discoveries than the 10 in DSB V1 (no overlap)
- Same case schema (exposed_facts, withheld_facts, breakthrough_relationship, etc.)

### 3.2 Case selection
- Real cases: 20 historical discoveries NOT in DSB V1 (e.g., HeLa cells, GFP, RNA interference, induced pluripotent stem cells [if not already used], CAR-T, etc.)
- Fabricated cases: 20 matched counterfactuals, each structurally matched to a real case but with a "breakthrough" that did NOT happen

### 3.3 Human adjudication
- The 40 calibration cases undergo the SAME human adjudication process as DSB V1 (2-3 independent experts, blind to case_type, Q1/Q2/Q3)
- Inter-rater agreement must be measured on the calibration set independently

### 3.4 Tuning protocol
1. Build the calibration set
2. Human-adjudicate the calibration set
3. Tune scorer_v2 on the calibration set (adjust thresholds, weights, patterns)
4. Evaluate scorer_v2 ONE-SHOT on the DSB V1 80 cases (frozen human results)
5. Report: scorer_v1 (frozen) vs scorer_v2 (calibrated) on DSB V1
6. If scorer_v2 materially outperforms scorer_v1 on DSB V1 held-out, adopt v2 as the new frozen scorer for future benchmarks

### 3.5 What tuning is allowed
- Adjusting the 0.50 threshold
- Adjusting the 0.30 novelty threshold
- Adjusting the 0.5 / 0.25 / 0.25 sub-score weights
- Adding new relation-type patterns (only if generic, not DSB-V1-specific)
- Adjusting the term-overlap computation (e.g., switching from overlap coefficient to Jaccard)

### 3.6 What tuning is NOT allowed
- Adding case-specific rules (e.g., "if case_id == DSB-R-001, score = 1.0")
- Removing specific terms from the stopwords list to boost specific cases
- Hand-tuning per-case verdicts

---

## 4. Decision Tree

```
Human adjudication of DSB V1 80 cases complete
       │
       ▼
Compute confusion matrices (human vs scorer_v1)
       │
       ▼
┌──────────────────────────────────────────────────┐
│ Is the scorer_v1 FALSE POSITIVE rate on          │
│ fabricated cases > 30%?                          │
└──────────────────────────────────────────────────┘
       │
   YES │   NO
       │       │
       ▼       ▼
Build calibration set        scorer_v1 is valid
(§3 above)                   against humans.
       │                     DSB V1 is CLOSED.
       ▼                     (No v2 needed.)
Tune scorer_v2 on
calibration set
       │
       ▼
Evaluate scorer_v2 one-shot
on DSB V1 80 cases
       │
       ▼
┌──────────────────────────────────────────────────┐
│ Does scorer_v2 materially outperform scorer_v1   │
│ on DSB V1 held-out (lower FP, higher F1)?        │
└──────────────────────────────────────────────────┘
       │
   YES │   NO
       │       │
       ▼       ▼
Adopt scorer_v2 as        scorer_v1 stands.
new frozen scorer.        DSB V1 is CLOSED
DSB V1 is CLOSED          with the caveat that
with v2 results.          the scorer has known
                          false positives.
```

---

## 5. Timing

The calibration set is NOT built yet. It is ONLY built if human adjudication of DSB V1 reveals systematic false positives. Building it pre-emptively would waste effort if the scorer turns out to be valid.

---

## 6. Quarantine (Continued)

Until DSB V1 is scientifically closed (human adjudication complete + scorer validity established + fabricated-vs-real inversion explained):

- ❌ No temporal reasoning module
- ❌ No negative knowledge module
- ❌ No patent integration
- ❌ No architecture redesign
- ❌ No new discovery modes

The calibration set, if needed, is the ONLY permitted forward work.

---

**End of Scorer-Calibration Protocol.**
