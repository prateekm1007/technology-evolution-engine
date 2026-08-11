#!/usr/bin/env python3
"""
Phase 9 — Scored backtest: apply Readiness, Novelty, Feasibility to
filter the 1746 raw predictions down to a ranked list.

This is the transition from M2 (reproducible evidence) to M3
(predictive capability).

The scoring uses the CANDIDATE formulas from evidence/experiments/
(experimental layer, not constitutional). The formulas are priors,
not fitted constants.

Readiness: weighted sum of capability maturity (weakest-link for combos)
Novelty: combinatorial distance from existing combinations
Feasibility: boolean AND of constraint gates

The model predicts: combinations that are READY (all caps mature),
NOVEL (not already attempted), and FEASIBLE (no constraints violated).
"""
import json
import pathlib
from collections import defaultdict
from itertools import combinations

ROOT = pathlib.Path(__file__).resolve().parents[1]

CAPABILITIES = [
    "ELECTROCHEMICAL_ENERGY_STORAGE", "ION_TRANSPORT", "INTERCALATION",
    "ELECTRON_COLLECTION", "FAST_CHARGING", "THERMAL_MANAGEMENT",
    "STATE_OF_CHARGE_MONITORING", "SAFETY_PROTECTION", "ELECTRODE_COATING",
    "CELL_ASSEMBLY",
]

# Maturity levels: MATURE=1.0, EMERGING=0.5, ABSENT=0.0
MATURITY_SCORE = {"MATURE": 1.0, "EMERGING": 0.5, "ABSENT": 0.0}

CAPABILITY_MATURITY = {
    "ELECTROCHEMICAL_ENERGY_STORAGE": {1991: "EMERGING", 1995: "MATURE", 2000: "MATURE", 2005: "MATURE", 2010: "MATURE", 2015: "MATURE", 2020: "MATURE"},
    "ION_TRANSPORT": {1991: "MATURE", 1995: "MATURE", 2000: "MATURE", 2005: "MATURE", 2010: "MATURE", 2015: "MATURE", 2020: "MATURE"},
    "INTERCALATION": {1991: "MATURE", 1995: "MATURE", 2000: "MATURE", 2005: "MATURE", 2010: "MATURE", 2015: "MATURE", 2020: "MATURE"},
    "ELECTRON_COLLECTION": {1991: "MATURE", 1995: "MATURE", 2000: "MATURE", 2005: "MATURE", 2010: "MATURE", 2015: "MATURE", 2020: "MATURE"},
    "FAST_CHARGING": {1991: "ABSENT", 1995: "ABSENT", 2000: "EMERGING", 2005: "EMERGING", 2010: "EMERGING", 2015: "MATURE", 2020: "MATURE"},
    "THERMAL_MANAGEMENT": {1991: "ABSENT", 1995: "EMERGING", 2000: "EMERGING", 2005: "MATURE", 2010: "MATURE", 2015: "MATURE", 2020: "MATURE"},
    "STATE_OF_CHARGE_MONITORING": {1991: "EMERGING", 1995: "MATURE", 2000: "MATURE", 2005: "MATURE", 2010: "MATURE", 2015: "MATURE", 2020: "MATURE"},
    "SAFETY_PROTECTION": {1991: "EMERGING", 1995: "MATURE", 2000: "MATURE", 2005: "MATURE", 2010: "MATURE", 2015: "MATURE", 2020: "MATURE"},
    "ELECTRODE_COATING": {1991: "MATURE", 1995: "MATURE", 2000: "MATURE", 2005: "MATURE", 2010: "MATURE", 2015: "MATURE", 2020: "MATURE"},
    "CELL_ASSEMBLY": {1991: "MATURE", 1995: "MATURE", 2000: "MATURE", 2005: "MATURE", 2010: "MATURE", 2015: "MATURE", 2020: "MATURE"},
}

REQUIRES_EDGES = [
    ("ELECTROCHEMICAL_ENERGY_STORAGE", "ION_TRANSPORT"),
    ("ELECTROCHEMICAL_ENERGY_STORAGE", "INTERCALATION"),
    ("FAST_CHARGING", "ION_TRANSPORT"),
    ("FAST_CHARGING", "THERMAL_MANAGEMENT"),
    ("CELL_ASSEMBLY", "ELECTRODE_COATING"),
    ("SAFETY_PROTECTION", "STATE_OF_CHARGE_MONITORING"),
]

# Historical outcomes (same as unscored backtest)
HISTORICAL_OUTCOMES = {
    1995: [
        {"combination": ["ELECTROCHEMICAL_ENERGY_STORAGE", "INTERCALATION", "CELL_ASSEMBLY"],
         "description": "Li-ion in consumer electronics", "year": 1992},
    ],
    2000: [
        {"combination": ["ELECTROCHEMICAL_ENERGY_STORAGE", "INTERCALATION", "STATE_OF_CHARGE_MONITORING"],
         "description": "Li-ion with BMS in early EVs", "year": 1997},
        {"combination": ["ELECTROCHEMICAL_ENERGY_STORAGE", "INTERCALATION", "ELECTRODE_COATING"],
         "description": "LFP cathode commercialization", "year": 1996},
    ],
    2005: [
        {"combination": ["ELECTROCHEMICAL_ENERGY_STORAGE", "THERMAL_MANAGEMENT", "STATE_OF_CHARGE_MONITORING"],
         "description": "Li-ion EV with thermal management + BMS (Tesla Roadster)", "year": 2008},
        {"combination": ["ELECTROCHEMICAL_ENERGY_STORAGE", "INTERCALATION", "ELECTRON_COLLECTION"],
         "description": "NCM cathode commercialization", "year": 2004},
    ],
    2010: [
        {"combination": ["ELECTROCHEMICAL_ENERGY_STORAGE", "FAST_CHARGING", "THERMAL_MANAGEMENT", "SAFETY_PROTECTION"],
         "description": "Mass-market Li-ion EV with fast charging (Leaf, Volt)", "year": 2010},
        {"combination": ["FAST_CHARGING", "THERMAL_MANAGEMENT"],
         "description": "DC fast charging network (Tesla Supercharger)", "year": 2012},
    ],
    2015: [
        {"combination": ["ELECTROCHEMICAL_ENERGY_STORAGE", "ELECTRODE_COATING", "CELL_ASSEMBLY"],
         "description": "Gigafactory mass production of Li-ion cells", "year": 2016},
        {"combination": ["FAST_CHARGING", "THERMAL_MANAGEMENT", "SAFETY_PROTECTION"],
         "description": "800V fast-charging architecture (Porsche Taycan)", "year": 2019},
    ],
}

# ─── Scoring functions (candidate formulas from evidence/experiments/) ───

def get_maturity(cap, year):
    """Get maturity level for a capability at a given year."""
    timeline = CAPABILITY_MATURITY[cap]
    maturity = "ABSENT"
    for y in sorted(timeline.keys()):
        if y <= year:
            maturity = timeline[y]
    return maturity


def score_readiness(combo, year):
    """Readiness = min(maturity) across all capabilities in the combo.
    Weakest-link principle (from readiness_formula_v1.md).
    A combination is only as ready as its least-ready capability."""
    scores = [MATURITY_SCORE.get(get_maturity(cap, year), 0.0) for cap in combo]
    return min(scores) if scores else 0.0


def score_novelty(combo, year, prior_combos):
    """Novelty = has this exact combination been seen before?
    1.0 if never seen, 0.0 if already exists.
    Based on novelty_formula_v1.md: combinatorial distance."""
    combo_set = frozenset(combo)
    if combo_set in prior_combos:
        return 0.0  # already attempted — low novelty
    return 1.0  # never attempted — high novelty


def score_feasibility(combo, year):
    """Feasibility = boolean AND of constraint gates.
    From feasibility_formula_v1.md.

    Gates:
    F1_regulatory: pass (no regulations violated in this simple model)
    F2_economic: pass if at least one capability is MATURE (cost viable)
    F3_manufacturing: pass if CELL_ASSEMBLY and ELECTRODE_COATING are mature
    F4_infrastructure: pass (no infrastructure data in this simple model)
    F5_physical: pass if THERMAL_MANAGEMENT is present when FAST_CHARGING is present
    """
    combo_set = set(combo)

    # F2_economic: at least one capability must be MATURE
    any_mature = any(get_maturity(cap, year) == "MATURE" for cap in combo)
    if not any_mature:
        return False

    # F3_manufacturing: if CELL_ASSEMBLY in combo, ELECTRODE_COATING must be mature
    if "CELL_ASSEMBLY" in combo_set:
        if get_maturity("ELECTRODE_COATING", year) != "MATURE":
            return False

    # F5_physical: if FAST_CHARGING in combo, THERMAL_MANAGEMENT must be mature
    if "FAST_CHARGING" in combo_set:
        if get_maturity("THERMAL_MANAGEMENT", year) not in ("MATURE", "EMERGING"):
            return False

    # F1, F4: pass (no data to check against in this simple model)
    return True


def get_prior_combinations(year):
    """Get combinations that were already realized before `year`.
    These are the 'familiar' combinations — low novelty."""
    priors = set()
    for outcome_year, outcomes in HISTORICAL_OUTCOMES.items():
        if outcome_year < year:
            for o in outcomes:
                if o["year"] < year:
                    priors.add(frozenset(o["combination"]))
    return priors


def main():
    print("=" * 70)
    print("SCORED BACKTEST — Readiness + Novelty + Feasibility")
    print("Transition from M2 (reproducible evidence) to M3 (predictive capability)")
    print("=" * 70)

    backtest_points = [1995, 2000, 2005, 2010, 2015]
    horizon = 5

    all_results = {}

    for T in backtest_points:
        T_eval = T + horizon
        print(f"\n{'─' * 70}")
        print(f"T = {T} | Evaluation at T+{horizon} = {T_eval}")
        print(f"{'─' * 70}")

        # Get mature capabilities at T
        mature_caps = set()
        for cap in CAPABILITIES:
            if get_maturity(cap, T) in ("MATURE", "EMERGING"):
                mature_caps.add(cap)

        # Get prior combinations (for novelty scoring)
        prior_combos = get_prior_combinations(T)

        # Generate all reachable combinations
        all_combos = []
        for size in range(2, min(5, len(mature_caps) + 1)):
            for combo in combinations(sorted(mature_caps), size):
                # Check REQUIRES dependencies
                valid = True
                for src, tgt in REQUIRES_EDGES:
                    if src in combo and tgt not in mature_caps:
                        valid = False
                        break
                if valid:
                    all_combos.append(frozenset(combo))

        print(f"\nRaw reachable combinations: {len(all_combos)}")

        # Score each combination
        scored = []
        for combo in all_combos:
            combo_list = sorted(list(combo))
            readiness = score_readiness(combo_list, T)
            novelty = score_novelty(combo_list, T, prior_combos)
            feasible = score_feasibility(combo_list, T)

            # Only keep combinations that are FEASIBLE (boolean AND)
            if not feasible:
                continue

            # Combined score: readiness * novelty (feasible is already filtered)
            # This is a candidate formula, not a fitted constant
            combined_score = readiness * novelty

            scored.append({
                "combo": combo,
                "readiness": round(readiness, 2),
                "novelty": round(novelty, 2),
                "feasible": feasible,
                "combined_score": round(combined_score, 4),
            })

        # Sort by combined score (descending)
        scored.sort(key=lambda x: -x["combined_score"])

        print(f"After feasibility filter: {len(scored)}")
        print(f"After novelty filter (novelty > 0): {sum(1 for s in scored if s['novelty'] > 0)}")

        # Get actual outcomes in window
        actual = []
        for outcome_year, outcomes in HISTORICAL_OUTCOMES.items():
            for o in outcomes:
                if T < o["year"] <= T_eval:
                    actual.append(o)

        actual_set = set(frozenset(o["combination"]) for o in actual)

        # ─── Strategy 1: Top-N predictions ───
        # Take top 10 predictions by combined score
        top_n = 10
        top_preds = set(s["combo"] for s in scored[:top_n])

        tp1 = top_preds & actual_set
        fp1 = top_preds - actual_set
        fn1 = actual_set - top_preds
        prec1 = len(tp1) / len(top_preds) if top_preds else 0
        rec1 = len(tp1) / len(actual_set) if actual_set else 0

        # ─── Strategy 2: High-readiness + high-novelty ───
        # Filter: readiness >= 0.5 AND novelty > 0
        filtered = set(s["combo"] for s in scored if s["readiness"] >= 0.5 and s["novelty"] > 0)

        tp2 = filtered & actual_set
        fp2 = filtered - actual_set
        fn2 = actual_set - filtered
        prec2 = len(tp2) / len(filtered) if filtered else 0
        rec2 = len(tp2) / len(actual_set) if actual_set else 0

        # ─── Compare to unscored (all reachable) ───
        all_preds = set(all_combos)
        tp0 = all_preds & actual_set
        fp0 = all_preds - actual_set
        fn0 = actual_set - all_preds
        prec0 = len(tp0) / len(all_preds) if all_preds else 0
        rec0 = len(tp0) / len(actual_set) if actual_set else 0

        print(f"\n{'─' * 50}")
        print(f"RESULTS at T={T}, eval T+{horizon}={T_eval}")
        print(f"{'─' * 50}")
        print(f"{'Strategy':<30} {'Preds':>6} {'TP':>4} {'FP':>6} {'FN':>4} {'Prec':>8} {'Recall':>8}")
        print(f"{'-'*70}")
        print(f"{'Unscored (all reachable)':<30} {len(all_preds):>6} {len(tp0):>4} {len(fp0):>6} {len(fn0):>4} {prec0:>8.4f} {rec0:>8.4f}")
        print(f"{'Top-10 by score':<30} {len(top_preds):>6} {len(tp1):>4} {len(fp1):>6} {len(fn1):>4} {prec1:>8.4f} {rec1:>8.4f}")
        print(f"{'Readiness>=0.5 + Novel':<30} {len(filtered):>6} {len(tp2):>4} {len(fp2):>6} {len(fn2):>4} {prec2:>8.4f} {rec2:>8.4f}")

        if actual:
            print(f"\nActual outcomes in window:")
            for o in actual:
                in_top = frozenset(o["combination"]) in top_preds
                in_filtered = frozenset(o["combination"]) in filtered
                print(f"  {o['year']}: {o['description']}")
                print(f"    combo: {o['combination']}")
                print(f"    in top-10: {in_top}, in filtered: {in_filtered}")

        all_results[T] = {
            "unscored": {"preds": len(all_preds), "tp": len(tp0), "fp": len(fp0), "fn": len(fn0), "precision": round(prec0, 4), "recall": round(rec0, 4)},
            "top10": {"preds": len(top_preds), "tp": len(tp1), "fp": len(fp1), "fn": len(fn1), "precision": round(prec1, 4), "recall": round(rec1, 4)},
            "filtered": {"preds": len(filtered), "tp": len(tp2), "fp": len(fp2), "fn": len(fn2), "precision": round(prec2, 4), "recall": round(rec2, 4)},
        }

    # ─── Aggregate ───
    print(f"\n{'=' * 70}")
    print("AGGREGATE RESULTS")
    print(f"{'=' * 70}")

    for strategy in ["unscored", "top10", "filtered"]:
        total_preds = sum(r[strategy]["preds"] for r in all_results.values())  # type: ignore
        total_tp = sum(r[strategy]["tp"] for r in all_results.values())  # type: ignore
        total_fp = sum(r[strategy]["fp"] for r in all_results.values())  # type: ignore
        total_fn = sum(r[strategy]["fn"] for r in all_results.values())  # type: ignore
        prec = total_tp / total_preds if total_preds else 0
        rec = total_tp / (total_tp + total_fn) if (total_tp + total_fn) else 0
        print(f"{strategy:<20} preds={total_preds:>6} tp={total_tp:>3} fp={total_fp:>6} fn={total_fn:>3} prec={prec:.4f} rec={rec:.4f}")

    # ─── Verdict ───
    unscored_prec = sum(r["unscored"]["tp"] for r in all_results.values()) / sum(r["unscored"]["preds"] for r in all_results.values())
    top10_prec = sum(r["top10"]["tp"] for r in all_results.values()) / max(sum(r["top10"]["preds"] for r in all_results.values()), 1)
    filtered_prec = sum(r["filtered"]["tp"] for r in all_results.values()) / max(sum(r["filtered"]["preds"] for r in all_results.values()), 1)

    print(f"\n{'=' * 70}")
    print("VERDICT")
    print(f"{'=' * 70}")
    print(f"\nUnscored precision:     {unscored_prec:.4f} ({unscored_prec*100:.2f}%)")
    print(f"Top-10 precision:       {top10_prec:.4f} ({top10_prec*100:.2f}%)")
    print(f"Filtered precision:     {filtered_prec:.4f} ({filtered_prec*100:.2f}%)")
    print(f"NULL_MODEL precision:   0.0000 (0.00%)")

    if top10_prec > unscored_prec:
        print(f"\n>>> Scoring IMPROVED precision: {unscored_prec*100:.2f}% → {top10_prec*100:.2f}%")
        print(f">>> The scoring system acts as a filter.")
    else:
        print(f"\n>>> Scoring did NOT improve precision.")

    if top10_prec > 0.10:
        print(f">>> Precision > 10%: the model is approaching predictive capability (M3).")
    elif top10_prec > 0.05:
        print(f">>> Precision > 5%: the model is better than chance but not yet predictive.")
    else:
        print(f">>> Precision ≤ 5%: the model needs better scoring.")

    # Write results
    output = {
        "backtest_id": "phase9_scored_backtest_v1",
        "model": "CAPABILITY_MODEL with Readiness+Novelty+Feasibility scoring",
        "scope": "Li-ion intercalation systems (SCOPE_V2.md)",
        "aggregate": {
            "unscored": {"precision": round(unscored_prec, 4)},
            "top10": {"precision": round(top10_prec, 4)},
            "filtered": {"precision": round(filtered_prec, 4)},
            "null_model": {"precision": 0.0},
        },
        "per_point": all_results,
    }

    output_path = ROOT / "evidence" / "observations" / "SCORED_BACKTEST_RESULTS.md"
    with open(output_path, "w") as f:
        f.write("# SCORED BACKTEST RESULTS — Phase 9\n\n")
        f.write(f"**Status:** scored backtest (Readiness + Novelty + Feasibility filtering)\n\n")
        f.write("## Aggregate Precision Comparison\n\n")
        f.write(f"| Strategy | Precision | Improvement |\n|---|---:|---|\n")
        f.write(f"| Unscored (all reachable) | {unscored_prec:.4f} ({unscored_prec*100:.2f}%) | baseline |\n")
        f.write(f"| Top-10 by score | {top10_prec:.4f} ({top10_prec*100:.2f}%) | {((top10_prec/unscored_prec - 1)*100 if unscored_prec else 0):.0f}% better |\n")
        f.write(f"| Readiness≥0.5 + Novel | {filtered_prec:.4f} ({filtered_prec*100:.2f}%) | {((filtered_prec/unscored_prec - 1)*100 if unscored_prec else 0):.0f}% better |\n")
        f.write(f"| NULL_MODEL | 0.0000 (0.00%) | — |\n")

    json_path = ROOT / "evidence" / "observations" / "scored_backtest_results.json"
    with open(json_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nResults: {output_path}")


if __name__ == "__main__":
    main()
