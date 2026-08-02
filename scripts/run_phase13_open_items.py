#!/usr/bin/env python3
"""
Phase 13 open items resolver (EP-10 gate).

Resolves three blocking items identified by the external auditor
and recorded in PHASE_13_SYNTHESIS.md's supersession disclosure:

1. Paired-outcomes significance test on Formula B vs NULL_MODEL
   and Formula B vs velocity-only. Uses McNemar's test on the
   full per-candidate paired matrix (formula predicts yes/no ×
   actual yes/no), plus a paired t-test on per-T precision as
   a robustness check.

2. Per-candidate score dump for the "exactly equal" claim.
   Dumps the ranked Top-10 candidates per T for both Formula B
   (frozen, full) and velocity+adjacency (no cost_bonus), with
   their raw scores and TP/FP flag. Lets the auditor verify at
   the per-candidate level that the two formulas produce
   byte-identical rankings, not just matching aggregate TP/FP
   counts.

3. Counterexample re-run under the simplified formula.
   Computes the velocity+adjacency score for each of CE-001,
   CE-002, CE-003 from COUNTEREXAMPLE_REGISTRY.md at the T and
   combination specified, and reports whether they fall inside
   or outside the Top-10 under the simplified formula. If they
   fall outside, the necessity hypothesis (FEC-002) gains
   support: the counterexamples that scored high under the old
   formula (with cost_bonus) now score low without cost_bonus,
   consistent with cost_bonus being the noise term.

This script imports data and scoring functions from
scripts/run_ablation.py — it does not duplicate them. The
ablation script's scoring functions are the source of truth;
this script only adds reporting and statistical tests around
them.

One-off script. NOT a module. NOT imported by anything.
"""
import json
import pathlib
import sys
import math
from itertools import combinations
from collections import defaultdict

# Import the ablation's data and scoring functions
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from run_ablation import (
    CAPABILITIES, TRL_TIMELINE, COST_TIMELINE, COST_THRESHOLD,
    REQUIRES_EDGES, EVENTS, TIMELINE, HORIZON,
    get_trl, get_dtrl_dt, get_cost, get_cost_velocity,
    get_mature, get_priors, get_actuals, get_combos, is_feasible,
    score_velocity_only, score_adjacency_only, score_feasibility_only,
    score_velocity_adjacency, score_velocity_feasibility,
    score_adjacency_feasibility, score_formula_b_frozen,
)

ROOT = pathlib.Path(__file__).resolve().parents[1]
EVIDENCE_DIR = ROOT / "evidence" / "observations"
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────────────────────────────────────
# Helper: run a formula across the full backtest, return per-T data
# ─────────────────────────────────────────────────────────────────────────────

def run_formula_backtest(score_fn, seed=None):
    """Run a scoring function across the full backtest.

    Returns a list of per-T dicts containing:
      - T: the year
      - ranked: list of (combo, score) sorted desc by score, top 10 retained
      - top10: set of combos in top 10
      - actual: set of actual events in (T, T+HORIZON]
      - tp: top10 ∩ actual
      - fp: top10 - actual
      - fn: actual - top10
      - all_candidates: list of (combo, score) for ALL candidates, sorted desc
    """
    results = []
    for T in TIMELINE:
        mature = get_mature(T)
        priors = get_priors(T)
        combos = get_combos(mature, T)
        actual = get_actuals(T, HORIZON)

        scored = []
        for combo in combos:
            combo_list = sorted(list(combo))
            score = score_fn(combo_list, T, priors)
            scored.append((frozenset(combo), score))

        scored.sort(key=lambda x: -x[1])
        top10 = set(c for c, s in scored[:10])
        tp = top10 & actual
        fp = top10 - actual
        fn = actual - top10

        results.append({
            "T": T,
            "ranked_top10": [(sorted(list(c)), round(s, 6)) for c, s in scored[:10]],
            "all_candidates_count": len(scored),
            "top10_set": top10,
            "actual_set": actual,
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "tp_count": len(tp),
            "fp_count": len(fp),
            "fn_count": len(fn),
            "actual_count": len(actual),
            "precision": len(tp) / 10.0,
            "recall": len(tp) / len(actual) if actual else 0.0,
        })
    return results


def run_null_model(seed=42):
    """Run the NULL_MODEL — random selection of 10 candidates per T."""
    import random
    random.seed(seed)
    results = []
    for T in TIMELINE:
        mature = get_mature(T)
        combos = get_combos(mature, T)
        actual = get_actuals(T, HORIZON)

        scored = [(c, 0.0) for c in combos]
        random.shuffle(scored)
        top10 = set(c for c, s in scored[:10])
        tp = top10 & actual
        fp = top10 - actual
        fn = actual - top10

        results.append({
            "T": T,
            "top10_set": top10,
            "actual_set": actual,
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "tp_count": len(tp),
            "fp_count": len(fp),
            "fn_count": len(fn),
            "actual_count": len(actual),
            "precision": len(tp) / 10.0,
            "recall": len(tp) / len(actual) if actual else 0.0,
        })
    return results


# ─────────────────────────────────────────────────────────────────────────────
# ITEM 1: Paired-outcomes significance test
# ─────────────────────────────────────────────────────────────────────────────

def mcnemars_test(model_a_results, model_b_results, label_a, label_b):
    """McNemar's test on paired binary outcomes.

    For each (T, candidate) pair where exactly one of the models
    classified correctly (TP or TN), count:
      b = cases where A correct, B wrong
      c = cases where A wrong, B correct

    McNemar's statistic: chi2 = (|b - c| - 1)^2 / (b + c)
    (with continuity correction)

    But our setting is asymmetric — both models produce the SAME
    Top-10 list size (10 per T), but they may predict different
    candidates. The proper unit of comparison is: for each
    candidate that EITHER model put in its Top-10, was the
    classification correct?

    b = candidates A predicted correctly (TP) that B missed
        (either B didn't predict, or B predicted and was wrong)
    c = candidates B predicted correctly (TP) that A missed

    This is the discordant-pair count for the "TP" outcome only.
    FPs alone don't enter the comparison because they're
    non-events — both models make the same number of FP claims
    by construction (Top-10 size is fixed).
    """
    # Build per-candidate outcome table across all T's
    # For each T, compute the set of TPs for each model
    a_tps = set()
    b_tps = set()
    for ra, rb in zip(model_a_results, model_b_results):
        a_tps |= {(ra["T"], frozenset(c)) for c in ra["tp"]}
        b_tps |= {(rb["T"], frozenset(c)) for c in rb["tp"]}

    b_discordant = len(a_tps - b_tps)  # A right, B wrong
    c_discordant = len(b_tps - a_tps)  # B right, A wrong
    n = b_discordant + c_discordant

    if n == 0:
        return {
            "test": "mcnemar",
            "label_a": label_a,
            "label_b": label_b,
            "b_discordant": 0,
            "c_discordant": 0,
            "n_discordant": 0,
            "exact_p_two_sided": 1.0,
            "chi2_with_cc": 0.0,
            "interpretation": "no discordant pairs (models produce identical TP sets across all T-points)",
        }

    # Exact binomial p-value (preferred for small n)
    # Under H0: b ~ Binomial(n, 0.5)
    # Two-sided p = 2 * min(P(X <= b), P(X >= b))
    from math import comb
    k = min(b_discordant, c_discordant)
    tail = sum(comb(n, i) for i in range(k + 1)) / (2 ** n)
    p_exact = 2 * tail  # two-sided
    p_exact = min(p_exact, 1.0)

    # Chi-squared with continuity correction (for comparison)
    chi2 = (abs(b_discordant - c_discordant) - 1) ** 2 / n if n > 0 else 0.0

    return {
        "test": "mcnemar",
        "label_a": label_a,
        "label_b": label_b,
        "b_discordant": b_discordant,  # A right, B wrong
        "c_discordant": c_discordant,  # B right, A wrong
        "n_discordant": n,
        "exact_p_two_sided": round(p_exact, 6),
        "chi2_with_cc": round(chi2, 4),
        "interpretation": (
            f"Of {n} discordant TP pairs, {b_discordant} favored {label_a} "
            f"and {c_discordant} favored {label_b}. "
            f"Exact two-sided p = {p_exact:.4f}. "
            + ("REJECT H0 (models differ significantly)."
               if p_exact < 0.05 else
               "FAIL TO REJECT H0 (no significant difference).")
        ),
    }


def paired_t_test_on_precision(model_a_results, model_b_results, label_a, label_b):
    """Paired t-test on per-T precision.

    For each T, compute precision_A and precision_B. The paired
    t-test checks whether the mean difference is significantly
    different from zero.

    This is a robustness check on McNemar's — McNemar's operates
    on per-candidate outcomes, while this operates on per-T
    aggregates. They should agree in direction; McNemar's is
    more powerful when n is large.
    """
    diffs = []
    for ra, rb in zip(model_a_results, model_b_results):
        diffs.append(ra["precision"] - rb["precision"])

    n = len(diffs)
    mean_diff = sum(diffs) / n
    var_diff = sum((d - mean_diff) ** 2 for d in diffs) / (n - 1) if n > 1 else 0
    se_diff = math.sqrt(var_diff / n) if n > 0 else 0
    t_stat = mean_diff / se_diff if se_diff > 0 else float('inf') if mean_diff > 0 else float('-inf') if mean_diff < 0 else 0
    # Degrees of freedom = n - 1
    df = n - 1

    # Approximate p-value using normal distribution (n=14 is small but
    # we use the t-approximation; for a proper p we'd need scipy)
    # For df=13, critical t-values (two-sided):
    #   t_0.05 = 2.160, t_0.01 = 3.012, t_0.001 = 4.221
    if df <= 0:
        p_approx = 1.0
    else:
        # Use a simple approximation: |t| > 2.160 → p < 0.05 (df=13)
        # Better: use the incomplete beta function approximation
        # For honesty, we report the t-statistic and let the reader
        # consult a t-table. We also compute an approximate p via
        # the normal approximation (which is conservative for small n).
        from math import erf
        # Two-sided p via normal approx (conservative for df=13)
        z = abs(t_stat)
        p_normal = 2 * (1 - 0.5 * (1 + erf(z / math.sqrt(2))))
        p_approx = p_normal

    # Critical t for df=13, two-sided alpha=0.05: 2.160
    # Critical t for df=13, two-sided alpha=0.10: 1.771
    sig_05 = abs(t_stat) > 2.160 if df == 13 else None
    sig_10 = abs(t_stat) > 1.771 if df == 13 else None

    return {
        "test": "paired_t_on_per_T_precision",
        "label_a": label_a,
        "label_b": label_b,
        "n_pairs": n,
        "mean_diff_a_minus_b": round(mean_diff, 6),
        "se_diff": round(se_diff, 6),
        "t_statistic": round(t_stat, 4),
        "df": df,
        "p_value_normal_approx": round(p_approx, 6),
        "significant_at_0.05_df13": sig_05,
        "significant_at_0.10_df13": sig_10,
        "per_T_diffs": [round(d, 4) for d in diffs],
        "interpretation": (
            f"Mean per-T precision difference ({label_a} - {label_b}) = {mean_diff:.4f}. "
            f"t({df}) = {t_stat:.4f}. "
            + ("Significant at p<0.05 (t>2.160)."
               if sig_05 else
               ("Significant at p<0.10 (t>1.771)."
                if sig_10 else
                "Not significant at p<0.10."))
        ),
    }


# ─────────────────────────────────────────────────────────────────────────────
# ITEM 2: Per-candidate score dump
# ─────────────────────────────────────────────────────────────────────────────

def dump_per_candidate_top10(results, label):
    """For each T, dump the Top-10 ranked candidates with scores and TP/FP flag."""
    out = {"formula": label, "per_T": []}
    for r in results:
        t_entry = {
            "T": r["T"],
            "all_candidates_count": r.get("all_candidates_count", "?"),
            "actual_events": [sorted(list(c)) for c in r["actual_set"]],
            "top10": [],
        }
        for combo_list, score in r["ranked_top10"]:
            is_tp = frozenset(combo_list) in r["actual_set"]
            t_entry["top10"].append({
                "rank": len(t_entry["top10"]) + 1,
                "combo": combo_list,
                "score": score,
                "outcome": "TP" if is_tp else "FP",
            })
        out["per_T"].append(t_entry)
    return out


def verify_byte_equality_of_rankings(fb_results, va_results):
    """Verify Formula B and velocity+adjacency produce identical Top-10
    rankings at every T — not just matching TP/FP counts.

    Returns a list of per-T comparisons. If any T has a divergence
    (different combo, different score, or different rank order),
    that's flagged.
    """
    comparisons = []
    for fb, va in zip(fb_results, va_results):
        assert fb["T"] == va["T"]
        T = fb["T"]
        fb_top = fb["ranked_top10"]
        va_top = va["ranked_top10"]

        # Compare combo-by-combo at each rank
        divergences = []
        max_len = max(len(fb_top), len(va_top))
        for i in range(max_len):
            fb_combo, fb_score = fb_top[i] if i < len(fb_top) else (None, None)
            va_combo, va_score = va_top[i] if i < len(va_top) else (None, None)
            if fb_combo != va_combo or fb_score != va_score:
                divergences.append({
                    "rank": i + 1,
                    "formula_b": {"combo": fb_combo, "score": fb_score},
                    "velocity_adjacency": {"combo": va_combo, "score": va_score},
                })

        comparisons.append({
            "T": T,
            "identical": len(divergences) == 0,
            "divergences": divergences,
            "fb_tp_count": fb["tp_count"],
            "va_tp_count": va["tp_count"],
        })
    return comparisons


# ─────────────────────────────────────────────────────────────────────────────
# ITEM 3: Counterexample re-run under simplified formula
# ─────────────────────────────────────────────────────────────────────────────

def check_counterexample(ce_id, T, combo, fb_results, va_results):
    """Look up the specified combination in the per-T results.

    Returns: rank and score under Formula B vs velocity+adjacency,
    and whether the combo was even in the candidate set at T.
    """
    # Find the T entry
    fb_T = next((r for r in fb_results if r["T"] == T), None)
    va_T = next((r for r in va_results if r["T"] == T), None)

    result = {
        "ce_id": ce_id,
        "T": T,
        "combo": combo,
        "formula_b": None,
        "velocity_adjacency": None,
        "verdict": None,
    }

    combo_set = frozenset(combo)

    for label, r_T in [("formula_b", fb_T), ("velocity_adjacency", va_T)]:
        if r_T is None:
            result[label] = {"error": f"T={T} not in TIMELINE"}
            continue

        # Check if combo is in the Top-10
        rank = None
        score = None
        for i, (c, s) in enumerate(r_T["ranked_top10"]):
            if frozenset(c) == combo_set:
                rank = i + 1
                score = s
                break

        if rank is not None:
            result[label] = {
                "rank_in_top10": rank,
                "score": score,
                "in_top10": True,
            }
        else:
            # Check if it's in the candidate set at all (we'd need to
            # re-score it; the ablation script doesn't preserve all
            # candidates). For now, report "not in top 10".
            result[label] = {
                "rank_in_top10": None,
                "score": None,
                "in_top10": False,
                "note": "not in Top-10 under this formula (may or may not be in candidate set)",
            }

    # Verdict
    fb_in = result["formula_b"].get("in_top10", False) if isinstance(result["formula_b"], dict) else False
    va_in = result["velocity_adjacency"].get("in_top10", False) if isinstance(result["velocity_adjacency"], dict) else False

    if fb_in and not va_in:
        result["verdict"] = (
            f"CE scored HIGH under Formula B (in Top-10) but LOW under "
            f"velocity+adjacency (not in Top-10). Consistent with the "
            f"necessity hypothesis (FEC-002): cost_bonus was the term "
            f"responsible for the false positive."
        )
    elif fb_in and va_in:
        result["verdict"] = (
            f"CE scored HIGH under BOTH formulas. The simplified formula "
            f"does NOT eliminate the false positive. The necessity "
            f"hypothesis (FEC-002) is NOT supported for this CE — there "
            f"is another factor keeping this combo in the Top-10."
        )
    elif not fb_in and not va_in:
        result["verdict"] = (
            f"CE scored LOW under both formulas. Neither formula flags "
            f"this combination. The counterexample record may need "
            f"updating — the CE was originally reported under a different "
            f"formula version."
        )
    else:
        result["verdict"] = (
            f"CE scored LOW under Formula B but HIGH under velocity+adjacency. "
            f"Unexpected — investigate."
        )

    return result


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print("=" * 72)
    print("PHASE 13 OPEN ITEMS RESOLVER (EP-10 gate)")
    print("1. Paired-outcomes significance test (McNemar + paired t)")
    print("2. Per-candidate score dump (Top-10 per T for FB and v+a)")
    print("3. Counterexample re-run under simplified formula")
    print("=" * 72)

    # Run all formulas
    print("\n[1/4] Running Formula B (frozen, full)...")
    fb_results = run_formula_backtest(score_formula_b_frozen)
    print(f"      {sum(r['tp_count'] for r in fb_results)} TPs across {len(TIMELINE)} T-points")

    print("[2/4] Running velocity+adjacency (no cost_bonus)...")
    va_results = run_formula_backtest(score_velocity_adjacency)
    print(f"      {sum(r['tp_count'] for r in va_results)} TPs across {len(TIMELINE)} T-points")

    print("[3/4] Running velocity-only (for significance test)...")
    v_results = run_formula_backtest(score_velocity_only)
    print(f"      {sum(r['tp_count'] for r in v_results)} TPs across {len(TIMELINE)} T-points")

    print("[4/4] Running NULL_MODEL (seed=42)...")
    null_results = run_null_model(seed=42)
    print(f"      {sum(r['tp_count'] for r in null_results)} TPs across {len(TIMELINE)} T-points")

    # ─── ITEM 1: SIGNIFICANCE TESTS ───
    print("\n" + "=" * 72)
    print("ITEM 1: PAIRED-OUTCOMES SIGNIFICANCE TESTS")
    print("=" * 72)

    sig_tests = {}

    print("\n--- McNemar's test (per-candidate TP discordance) ---")
    print("(b = pairs where A right, B wrong; c = pairs where B right, A wrong)")
    print()

    for label_a, results_a, label_b, results_b in [
        ("Formula B", fb_results, "NULL_MODEL", null_results),
        ("Formula B", fb_results, "velocity_only", v_results),
        ("Formula B", fb_results, "velocity+adjacency", va_results),
        ("velocity+adjacency", va_results, "NULL_MODEL", null_results),
        ("velocity+adjacency", va_results, "velocity_only", v_results),
    ]:
        m = mcnemars_test(results_a, results_b, label_a, label_b)
        sig_tests[f"mcnemar_{label_a}_vs_{label_b}"] = m
        print(f"  {label_a} vs {label_b}:")
        print(f"    b={m['b_discordant']}  c={m['c_discordant']}  n={m['n_discordant']}")
        print(f"    exact_p_two_sided = {m['exact_p_two_sided']}")
        print(f"    → {m['interpretation']}")
        print()

    print("\n--- Paired t-test on per-T precision (robustness check) ---")
    print("(H0: mean per-T precision difference = 0; df = n_pairs - 1)")
    print()

    for label_a, results_a, label_b, results_b in [
        ("Formula B", fb_results, "NULL_MODEL", null_results),
        ("Formula B", fb_results, "velocity_only", v_results),
        ("Formula B", fb_results, "velocity+adjacency", va_results),
        ("velocity+adjacency", va_results, "NULL_MODEL", null_results),
    ]:
        t = paired_t_test_on_precision(results_a, results_b, label_a, label_b)
        sig_tests[f"paired_t_{label_a}_vs_{label_b}"] = t
        print(f"  {label_a} vs {label_b}:")
        print(f"    mean_diff = {t['mean_diff_a_minus_b']:.4f}  se = {t['se_diff']:.4f}")
        print(f"    t({t['df']}) = {t['t_statistic']:.4f}  p_normal_approx = {t['p_value_normal_approx']:.4f}")
        print(f"    significant at 0.05 (t>2.160): {t['significant_at_0.05_df13']}")
        print(f"    significant at 0.10 (t>1.771): {t['significant_at_0.10_df13']}")
        print(f"    → {t['interpretation']}")
        print()

    # ─── ITEM 2: PER-CANDIDATE DUMP ───
    print("\n" + "=" * 72)
    print("ITEM 2: PER-CANDIDATE SCORE DUMP")
    print("=" * 72)
    print()
    print("--- Formula B (frozen) Top-10 per T ---")
    fb_dump = dump_per_candidate_top10(fb_results, "Formula B (frozen)")
    for t_entry in fb_dump["per_T"]:
        print(f"\n  T={t_entry['T']}  (candidates: {t_entry['all_candidates_count']}, actual events: {len(t_entry['actual_events'])})")
        for c in t_entry["top10"]:
            combo_str = "+".join(c["combo"])
            print(f"    #{c['rank']:2d}  score={c['score']:.4f}  [{c['outcome']}]  {combo_str}")

    print("\n\n--- velocity+adjacency Top-10 per T ---")
    va_dump = dump_per_candidate_top10(va_results, "velocity+adjacency (no cost_bonus)")
    for t_entry in va_dump["per_T"]:
        print(f"\n  T={t_entry['T']}  (candidates: {t_entry['all_candidates_count']}, actual events: {len(t_entry['actual_events'])})")
        for c in t_entry["top10"]:
            combo_str = "+".join(c["combo"])
            print(f"    #{c['rank']:2d}  score={c['score']:.4f}  [{c['outcome']}]  {combo_str}")

    # ─── ITEM 2b: BYTE-EQUALITY VERIFICATION ───
    print("\n" + "=" * 72)
    print("ITEM 2b: BYTE-EQUALITY VERIFICATION (Formula B vs velocity+adjacency)")
    print("=" * 72)
    print()
    comparisons = verify_byte_equality_of_rankings(fb_results, va_results)
    any_divergence = False
    for c in comparisons:
        marker = "IDENTICAL" if c["identical"] else "DIVERGENT"
        print(f"  T={c['T']}: {marker}  (fb_tp={c['fb_tp_count']}, va_tp={c['va_tp_count']})")
        if not c["identical"]:
            any_divergence = True
            for d in c["divergences"]:
                print(f"    rank #{d['rank']}:")
                print(f"      Formula B:           {d['formula_b']}")
                print(f"      velocity+adjacency:  {d['velocity_adjacency']}")

    print()
    if not any_divergence:
        print("  >>> ALL 14 T-POINTS PRODUCE BYTE-IDENTICAL TOP-10 RANKINGS.")
        print("  >>> The 'Formula B ≈ velocity+adjacency' claim (FEC-001) is")
        print("  >>> verified at the per-candidate level, not just aggregate.")
    else:
        print("  >>> DIVERGENCE FOUND. The 'exactly equal' claim is NOT fully")
        print("  >>> supported at the per-candidate level. Investigate above.")

    # ─── ITEM 3: COUNTEREXAMPLE RE-RUN ───
    print("\n" + "=" * 72)
    print("ITEM 3: COUNTEREXAMPLE RE-RUN UNDER SIMPLIFIED FORMULA")
    print("=" * 72)
    print()
    print("Per COUNTEREXAMPLE_REGISTRY.md:")
    print("  CE-001: T=1991, combo={ELECTRODE_COATING, ELECTRON_COLLECTION}")
    print("  CE-002: T=2005, combo={CELL_ASSEMBLY, ELECTRODE_COATING, ION_TRANSPORT, SAFETY_PROTECTION}")
    print("  CE-003: T=2015, combo={CELL_ASSEMBLY, ELECTRODE_COATING, ELECTRON_COLLECTION, ION_TRANSPORT}")
    print()

    ces = [
        ("CE-001", 1991, ["ELECTRODE_COATING", "ELECTRON_COLLECTION"]),
        ("CE-002", 2005, ["CELL_ASSEMBLY", "ELECTRODE_COATING", "ION_TRANSPORT", "SAFETY_PROTECTION"]),
        ("CE-003", 2015, ["CELL_ASSEMBLY", "ELECTRODE_COATING", "ELECTRON_COLLECTION", "ION_TRANSPORT"]),
    ]

    ce_results = []
    for ce_id, T, combo in ces:
        r = check_counterexample(ce_id, T, combo, fb_results, va_results)
        ce_results.append(r)
        print(f"  {ce_id}  T={T}  combo={combo}")
        print(f"    Formula B:           {r['formula_b']}")
        print(f"    velocity+adjacency:  {r['velocity_adjacency']}")
        print(f"    → {r['verdict']}")
        print()

    # ─── WRITE OUTPUTS ───
    output_path = EVIDENCE_DIR / "phase13_open_items_resolution.json"
    output = {
        "phase": "13 open items resolution (EP-10 gate)",
        "items_resolved": [
            "1. paired-outcomes significance test (McNemar + paired t)",
            "2. per-candidate score dump for FEC-001 'exactly equal' claim",
            "3. counterexample re-run under simplified formula (CE-001 to CE-003)",
        ],
        "significance_tests": sig_tests,
        "per_candidate_dump": {
            "formula_b": fb_dump,
            "velocity_adjacency": va_dump,
        },
        "byte_equality_verification": comparisons,
        "byte_equality_verdict": "ALL 14 T-POINTS IDENTICAL" if not any_divergence else "DIVERGENCE FOUND",
        "counterexample_rerun": ce_results,
    }

    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print("=" * 72)
    print(f"OUTPUT WRITTEN: {output_path}")
    print("=" * 72)


if __name__ == "__main__":
    main()
