#!/usr/bin/env python3
"""
Phase 9 — Frozen-time backtest for the CAPABILITY_MODEL.

Advances the model from M1 (structured observations) to M2
(reproducible evidence).

Method: define the capability state at each backtest point T,
predict which combinations were reachable, check what actually
happened by T+n.

The backtest uses HISTORICAL KNOWLEDGE of Li-ion development,
not patent data. The 5 patents in the corpus are recent (2012-2024).
The backtest tests the MODEL's structure (capabilities + constraints +
edges), not the DATA (which patents we have).

This is a knowledge-based backtest — appropriate for a 5-patent
corpus testing whether the model's STRUCTURE makes correct predictions.

Also implements the NULL_MODEL (random selection) for comparison.

One-off script. NOT a module. NOT imported by anything.
"""
import json
import pathlib
import random
from collections import defaultdict

ROOT = pathlib.Path("/home/z/my-project/audit/repo")

# ─── The 10 capabilities ───
CAPABILITIES = [
    "ELECTROCHEMICAL_ENERGY_STORAGE",
    "ION_TRANSPORT",
    "INTERCALATION",
    "ELECTRON_COLLECTION",
    "FAST_CHARGING",
    "THERMAL_MANAGEMENT",
    "STATE_OF_CHARGE_MONITORING",
    "SAFETY_PROTECTION",
    "ELECTRODE_COATING",
    "CELL_ASSEMBLY",
]

# ─── Capability maturity by year (historical knowledge of Li-ion) ───
# Maturity: MATURE (commercially available), EMERGING (lab/pilot), ABSENT (not yet)
# Source: general knowledge of Li-ion history (Sony 1991, LFP 1996, NCM 2001, etc.)

CAPABILITY_MATURITY = {
    # capability: {year: maturity_level}
    "ELECTROCHEMICAL_ENERGY_STORAGE": {
        1991: "EMERGING",  # Sony commercialized first Li-ion
        1995: "MATURE",    # Li-ion commercially available
        2000: "MATURE",
        2005: "MATURE",
        2010: "MATURE",
        2015: "MATURE",
        2020: "MATURE",
    },
    "ION_TRANSPORT": {
        1991: "MATURE",  # Liquid electrolytes existed from day 1
        1995: "MATURE",
        2000: "MATURE",
        2005: "MATURE",
        2010: "MATURE",
        2015: "MATURE",
        2020: "MATURE",
    },
    "INTERCALATION": {
        1991: "MATURE",  # Graphite intercalation is the basis of Li-ion
        1995: "MATURE",
        2000: "MATURE",
        2005: "MATURE",
        2010: "MATURE",
        2015: "MATURE",
        2020: "MATURE",
    },
    "ELECTRON_COLLECTION": {
        1991: "MATURE",  # Current collectors (Al, Cu) existed from day 1
        1995: "MATURE",
        2000: "MATURE",
        2005: "MATURE",
        2010: "MATURE",
        2015: "MATURE",
        2020: "MATURE",
    },
    "FAST_CHARGING": {
        1991: "ABSENT",   # Not a concern in early Li-ion
        1995: "ABSENT",
        2000: "EMERGING", # Some fast-charge protocols emerging
        2005: "EMERGING", # Power tools, early EVs
        2010: "EMERGING", # EV fast charging becoming important
        2015: "MATURE",   # DC fast charging (CHAdeMO, Supercharger)
        2020: "MATURE",   # 800V architectures (Porsche Taycan)
    },
    "THERMAL_MANAGEMENT": {
        1991: "ABSENT",   # Early cells were small, no thermal mgmt needed
        1995: "EMERGING", # Larger packs needed some cooling
        2000: "EMERGING",
        2005: "MATURE",   # EV battery packs required active cooling
        2010: "MATURE",
        2015: "MATURE",
        2020: "MATURE",
    },
    "STATE_OF_CHARGE_MONITORING": {
        1991: "EMERGING", # Coulomb counting existed but primitive
        1995: "MATURE",   # BMS became standard
        2000: "MATURE",
        2005: "MATURE",
        2010: "MATURE",
        2015: "MATURE",
        2020: "MATURE",
    },
    "SAFETY_PROTECTION": {
        1991: "EMERGING", # Fuses, PTC existed
        1995: "MATURE",   # CID, vents standard
        2000: "MATURE",
        2005: "MATURE",
        2010: "MATURE",
        2015: "MATURE",
        2020: "MATURE",
    },
    "ELECTRODE_COATING": {
        1991: "MATURE",   # Slot-die coating existed from day 1
        1995: "MATURE",
        2000: "MATURE",
        2005: "MATURE",
        2010: "MATURE",
        2015: "MATURE",
        2020: "MATURE",
    },
    "CELL_ASSEMBLY": {
        1991: "MATURE",   # Winding, stacking existed from day 1
        1995: "MATURE",
        2000: "MATURE",
        2005: "MATURE",
        2010: "MATURE",
        2015: "MATURE",
        2020: "MATURE",
    },
}

# ─── Constraint thresholds by year ───
CONSTRAINT_THRESHOLDS = {
    "COST_PER_KWH_THRESHOLD": {
        1995: 3000,  # ~$3000/kWh
        2000: 1000,  # ~$1000/kWh
        2005: 500,   # ~$500/kWh
        2010: 300,   # ~$300/kWh
        2015: 200,   # ~$200/kWh
        2020: 150,   # ~$150/kWh
    },
}

# ─── Historical outcomes (what actually happened by T+n) ───
# Key Li-ion milestones, with the capabilities they combined
HISTORICAL_OUTCOMES = {
    1995: [
        # Sony Li-ion commercial (1991), early EVs (GM EV1 used lead-acid, not Li-ion)
        # Li-ion in consumer electronics (camcorders, laptops)
        {"combination": ["ELECTROCHEMICAL_ENERGY_STORAGE", "INTERCALATION", "CELL_ASSEMBLY"],
         "description": "Li-ion in consumer electronics", "year": 1992},
    ],
    2000: [
        # LFP cathode (1996, Goodenough), early Li-ion EVs (Altra, Nissan)
        {"combination": ["ELECTROCHEMICAL_ENERGY_STORAGE", "INTERCALATION", "STATE_OF_CHARGE_MONITORING"],
         "description": "Li-ion with BMS in early EVs", "year": 1997},
        # LFP commercialization
        {"combination": ["ELECTROCHEMICAL_ENERGY_STORAGE", "INTERCALATION", "ELECTRODE_COATING"],
         "description": "LFP cathode commercialization", "year": 1996},
    ],
    2005: [
        # Tesla Roadster development (2004-2008), using Li-ion for EVs
        {"combination": ["ELECTROCHEMICAL_ENERGY_STORAGE", "THERMAL_MANAGEMENT", "STATE_OF_CHARGE_MONITORING"],
         "description": "Li-ion EV with thermal management + BMS (Tesla Roadster)", "year": 2008},
        # NCM cathode (2001, Argonne)
        {"combination": ["ELECTROCHEMICAL_ENERGY_STORAGE", "INTERCALATION", "ELECTRON_COLLECTION"],
         "description": "NCM cathode commercialization", "year": 2004},
    ],
    2010: [
        # Nissan Leaf (2010), Chevy Volt (2010) — mass-market Li-ion EVs
        {"combination": ["ELECTROCHEMICAL_ENERGY_STORAGE", "FAST_CHARGING", "THERMAL_MANAGEMENT", "SAFETY_PROTECTION"],
         "description": "Mass-market Li-ion EV with fast charging (Leaf, Volt)", "year": 2010},
        # Tesla Supercharger (2012)
        {"combination": ["FAST_CHARGING", "THERMAL_MANAGEMENT"],
         "description": "DC fast charging network (Tesla Supercharger)", "year": 2012},
    ],
    2015: [
        # 2170 cell (Tesla/Panasonic Gigafactory, 2014-2017)
        {"combination": ["ELECTROCHEMICAL_ENERGY_STORAGE", "ELECTRODE_COATING", "CELL_ASSEMBLY"],
         "description": "Gigafactory mass production of Li-ion cells", "year": 2016},
        # Porsche 800V fast charging architecture (2019)
        {"combination": ["FAST_CHARGING", "THERMAL_MANAGEMENT", "SAFETY_PROTECTION"],
         "description": "800V fast-charging architecture (Porsche Taycan)", "year": 2019},
    ],
}

# ─── The structural REQUIRES edges (from the trusted graph) ───
REQUIRES_EDGES = [
    ("ELECTROCHEMICAL_ENERGY_STORAGE", "ION_TRANSPORT"),
    ("ELECTROCHEMICAL_ENERGY_STORAGE", "INTERCALATION"),
    ("FAST_CHARGING", "ION_TRANSPORT"),
    ("FAST_CHARGING", "THERMAL_MANAGEMENT"),
    ("CELL_ASSEMBLY", "ELECTRODE_COATING"),
    ("SAFETY_PROTECTION", "STATE_OF_CHARGE_MONITORING"),
]


def get_mature_capabilities(year):
    """Return capabilities that are MATURE or EMERGING at year T."""
    mature = set()
    for cap, timeline in CAPABILITY_MATURITY.items():
        # Find the maturity at or before the given year
        years = sorted(timeline.keys())
        maturity = "ABSENT"
        for y in years:
            if y <= year:
                maturity = timeline[y]
        if maturity in ("MATURE", "EMERGING"):
            mature.add(cap)
    return mature


def get_reachable_combinations(mature_caps, max_size=4):
    """Generate all combinations of mature capabilities up to max_size.
    A combination is 'reachable' if all its REQUIRES dependencies are met."""
    from itertools import combinations

    reachable = []
    for size in range(2, min(max_size + 1, len(mature_caps) + 1)):
        for combo in combinations(sorted(mature_caps), size):
            # Check if all REQUIRES dependencies are satisfied
            valid = True
            for src, tgt in REQUIRES_EDGES:
                if src in combo and tgt not in mature_caps:
                    valid = False
                    break
            if valid:
                reachable.append(frozenset(combo))
    return reachable


def get_null_model_predictions(mature_caps, max_size=4, seed=42):
    """NULL_MODEL: randomly select combinations from mature capabilities."""
    from itertools import combinations
    random.seed(seed)

    all_combos = []
    for size in range(2, min(max_size + 1, len(mature_caps) + 1)):
        for combo in combinations(sorted(mature_caps), size):
            all_combos.append(frozenset(combo))

    # Random selection: pick same number as the capability model
    n_select = min(len(all_combos), 20)
    return set(random.sample(all_combos, n_select)) if all_combos else set()


def evaluate_predictions(predictions, actual_outcomes):
    """Compute precision, recall, false positives, false negatives."""
    pred_set = set(predictions)
    actual_set = set()

    for outcome in actual_outcomes:
        actual_set.add(frozenset(outcome["combination"]))

    true_positives = pred_set & actual_set
    false_positives = pred_set - actual_set
    false_negatives = actual_set - pred_set

    precision = len(true_positives) / len(pred_set) if pred_set else 0
    recall = len(true_positives) / len(actual_set) if actual_set else 0

    return {
        "true_positives": len(true_positives),
        "false_positives": len(false_positives),
        "false_negatives": len(false_negatives),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "tp_combos": [sorted(list(c)) for c in true_positives],
        "fp_combos": [sorted(list(c)) for c in false_positives][:5],  # first 5 for display
        "fn_combos": [sorted(list(c)) for c in false_negatives],
    }


def main():
    print("=" * 70)
    print("FROZEN-TIME BACKTEST — CAPABILITY_MODEL vs NULL_MODEL")
    print("Advancing from M1 (structured observations) to M2 (reproducible evidence)")
    print("=" * 70)

    backtest_points = [1995, 2000, 2005, 2010, 2015]
    horizon = 5  # T+5 years

    results = {}

    for T in backtest_points:
        T_eval = T + horizon
        print(f"\n{'─' * 70}")
        print(f"T = {T} | Evaluation at T+{horizon} = {T_eval}")
        print(f"{'─' * 70}")

        # Step 1: What capabilities are mature at T?
        mature = get_mature_capabilities(T)
        print(f"\nMature/emerging capabilities at T={T}:")
        for cap in sorted(mature):
            timeline = CAPABILITY_MATURITY[cap]
            maturity = "ABSENT"
            for y in sorted(timeline.keys()):
                if y <= T:
                    maturity = timeline[y]
            print(f"  {cap}: {maturity}")

        # Step 2: What combinations are reachable at T? (CAPABILITY_MODEL)
        reachable = get_reachable_combinations(mature)
        print(f"\nCAPABILITY_MODEL: {len(reachable)} reachable combinations at T={T}")

        # Step 3: NULL_MODEL — random selection
        null_preds = get_null_model_predictions(mature, seed=T)
        print(f"NULL_MODEL: {len(null_preds)} random predictions at T={T}")

        # Step 4: What actually happened by T+horizon?
        actual = []
        for outcome_year, outcomes in HISTORICAL_OUTCOMES.items():
            if T < outcome_year <= T_eval:
                actual.extend(outcomes)
        # Also check if any outcome happened AT or before T (already realized)
        # We only count outcomes that happened BETWEEN T and T+horizon
        actual_in_window = [o for o in actual if T < o["year"] <= T_eval]

        print(f"\nActual outcomes between T={T} and T+{horizon}={T_eval}:")
        if actual_in_window:
            for o in actual_in_window:
                print(f"  {o['year']}: {o['description']} — {o['combination']}")
        else:
            print("  (none recorded)")

        # Step 5: Evaluate CAPABILITY_MODEL
        cap_preds = set(reachable)
        actual_combos = [frozenset(o["combination"]) for o in actual_in_window]
        actual_set = set(actual_combos)

        cap_tp = cap_preds & actual_set
        cap_fp = cap_preds - actual_set
        cap_fn = actual_set - cap_preds

        cap_precision = len(cap_tp) / len(cap_preds) if cap_preds else 0
        cap_recall = len(cap_tp) / len(actual_set) if actual_set else 0

        # Step 6: Evaluate NULL_MODEL
        null_tp = null_preds & actual_set
        null_fp = null_preds - actual_set
        null_fn = actual_set - null_preds

        null_precision = len(null_tp) / len(null_preds) if null_preds else 0
        null_recall = len(null_tp) / len(actual_set) if actual_set else 0

        # Step 7: Compare
        print(f"\n{'─' * 40}")
        print(f"RESULTS at T={T}, eval T+{horizon}={T_eval}")
        print(f"{'─' * 40}")
        print(f"{'Metric':<20} {'CAPABILITY_MODEL':>20} {'NULL_MODEL':>20}")
        print(f"{'-'*60}")
        print(f"{'Predictions':<20} {len(cap_preds):>20} {len(null_preds):>20}")
        print(f"{'Actual outcomes':<20} {len(actual_set):>20} {len(actual_set):>20}")
        print(f"{'True positives':<20} {len(cap_tp):>20} {len(null_tp):>20}")
        print(f"{'False positives':<20} {len(cap_fp):>20} {len(null_fp):>20}")
        print(f"{'False negatives':<20} {len(cap_fn):>20} {len(null_fn):>20}")
        print(f"{'Precision':<20} {cap_precision:>20.4f} {null_precision:>20.4f}")
        print(f"{'Recall':<20} {cap_recall:>20.4f} {null_recall:>20.4f}")

        if actual_set:
            beats_null_precision = cap_precision > null_precision
            print(f"\nCAPABILITY_MODEL beats NULL on precision: {beats_null_precision}")
        else:
            print(f"\nNo actual outcomes in window — inconclusive for this T.")

        results[T] = {
            "T": T,
            "T_eval": T_eval,
            "capability_model": {
                "predictions": len(cap_preds),
                "true_positives": len(cap_tp),
                "false_positives": len(cap_fp),
                "false_negatives": len(cap_fn),
                "precision": round(cap_precision, 4),
                "recall": round(cap_recall, 4),
                "tp_details": [sorted(list(c)) for c in cap_tp],
                "fp_sample": [sorted(list(c)) for c in list(cap_fp)[:3]],
                "fn_details": [sorted(list(c)) for c in cap_fn],
            },
            "null_model": {
                "predictions": len(null_preds),
                "true_positives": len(null_tp),
                "false_positives": len(null_fp),
                "false_negatives": len(null_fn),
                "precision": round(null_precision, 4),
                "recall": round(null_recall, 4),
            },
            "actual_outcomes": [{"year": o["year"], "description": o["description"],
                                   "combination": o["combination"]} for o in actual_in_window],
        }

    # ─── Aggregate results ───
    print(f"\n{'=' * 70}")
    print("AGGREGATE RESULTS (all backtest points)")
    print(f"{'=' * 70}")

    total_cap_tp = sum(r["capability_model"]["true_positives"] for r in results.values())
    total_cap_fp = sum(r["capability_model"]["false_positives"] for r in results.values())
    total_cap_fn = sum(r["capability_model"]["false_negatives"] for r in results.values())
    total_null_tp = sum(r["null_model"]["true_positives"] for r in results.values())
    total_null_fp = sum(r["null_model"]["false_positives"] for r in results.values())
    total_null_fn = sum(r["null_model"]["false_negatives"] for r in results.values())

    cap_total_preds = total_cap_tp + total_cap_fp
    null_total_preds = total_null_tp + total_null_fp
    total_actual = total_cap_tp + total_cap_fn  # same as null_tp + null_fn

    cap_precision = total_cap_tp / cap_total_preds if cap_total_preds else 0
    cap_recall = total_cap_tp / total_actual if total_actual else 0
    null_precision = total_null_tp / null_total_preds if null_total_preds else 0
    null_recall = total_null_tp / total_actual if total_actual else 0

    print(f"\n{'Metric':<25} {'CAPABILITY_MODEL':>20} {'NULL_MODEL':>20}")
    print(f"{'-'*65}")
    print(f"{'Total predictions':<25} {cap_total_preds:>20} {null_total_preds:>20}")
    print(f"{'Total actual outcomes':<25} {total_actual:>20} {total_actual:>20}")
    print(f"{'Total true positives':<25} {total_cap_tp:>20} {total_null_tp:>20}")
    print(f"{'Total false positives':<25} {total_cap_fp:>20} {total_null_fp:>20}")
    print(f"{'Total false negatives':<25} {total_cap_fn:>20} {total_null_fn:>20}")
    print(f"{'AGGREGATE PRECISION':<25} {cap_precision:>20.4f} {null_precision:>20.4f}")
    print(f"{'AGGREGATE RECALL':<25} {cap_recall:>20.4f} {null_recall:>20.4f}")

    print(f"\n{'=' * 70}")
    print("VERDICT")
    print(f"{'=' * 70}")
    beats_null = cap_precision > null_precision
    beats_null_recall = cap_recall > null_recall

    print(f"\nCAPABILITY_MODEL precision > NULL_MODEL precision: {beats_null}")
    print(f"CAPABILITY_MODEL recall > NULL_MODEL recall: {beats_null_recall}")

    if beats_null:
        print("\n>>> The CAPABILITY_MODEL outperforms the NULL_MODEL on precision.")
        print(">>> IC-001 (cannot outperform null model) is NOT met.")
        print(">>> The model advances to M2 (reproducible evidence).")
    else:
        print("\n>>> The CAPABILITY_MODEL does NOT outperform the NULL_MODEL.")
        print(">>> IC-001 (cannot outperform null model) IS MET.")
        print(">>> The theory FAILS at IC-001.")

    # ─── Write results ───
    output = {
        "backtest_id": "phase9_frozen_time_v1",
        "model": "CAPABILITY_MODEL vs NULL_MODEL",
        "scope": "Li-ion intercalation systems (per SCOPE_V2.md)",
        "backtest_points": backtest_points,
        "horizon_years": horizon,
        "aggregate": {
            "capability_model": {
                "total_predictions": cap_total_preds,
                "true_positives": total_cap_tp,
                "false_positives": total_cap_fp,
                "false_negatives": total_cap_fn,
                "precision": round(cap_precision, 4),
                "recall": round(cap_recall, 4),
            },
            "null_model": {
                "total_predictions": null_total_preds,
                "true_positives": total_null_tp,
                "false_positives": total_null_fp,
                "false_negatives": total_null_fn,
                "precision": round(null_precision, 4),
                "recall": round(null_recall, 4),
            },
        },
        "verdict": "CAPABILITY_MODEL beats NULL_MODEL" if beats_null else "CAPABILITY_MODEL does NOT beat NULL_MODEL — IC-001 MET",
        "ic_001_status": "NOT MET" if beats_null else "MET — THEORY FAILS",
        "maturity": "M2" if beats_null else "M1 (blocked at IC-001)",
        "per_point_results": results,
    }

    output_path = ROOT / "evidence" / "observations" / "BACKTEST_RESULTS.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        f.write("# BACKTEST RESULTS — Phase 9 Frozen-Time Backtest\n\n")
        f.write(f"**Status:** {'M2 (reproducible evidence)' if beats_null else 'IC-001 MET — theory fails'}\n")
        f.write(f"**Scope:** Li-ion intercalation systems (per SCOPE_V2.md)\n\n")
        f.write("## Aggregate Results\n\n")
        f.write(f"| Metric | CAPABILITY_MODEL | NULL_MODEL |\n|---|---:|---:|\n")
        f.write(f"| Total predictions | {cap_total_preds} | {null_total_preds} |\n")
        f.write(f"| Total actual outcomes | {total_actual} | {total_actual} |\n")
        f.write(f"| True positives | {total_cap_tp} | {total_null_tp} |\n")
        f.write(f"| False positives | {total_cap_fp} | {total_null_fp} |\n")
        f.write(f"| False negatives | {total_cap_fn} | {total_null_fn} |\n")
        f.write(f"| **Precision** | **{cap_precision:.4f}** | **{null_precision:.4f}** |\n")
        f.write(f"| **Recall** | **{cap_recall:.4f}** | **{null_recall:.4f}** |\n\n")
        f.write(f"## Verdict\n\n")
        f.write(f"CAPABILITY_MODEL beats NULL_MODEL on precision: **{beats_null}**\n\n")
        f.write(f"IC-001 status: **{'NOT MET' if beats_null else 'MET — THEORY FAILS'}**\n\n")
        f.write(f"Maturity: **{'M2' if beats_null else 'M1 (blocked)'}**\n")

    print(f"\nResults written to: {output_path}")

    # Also write JSON
    json_path = ROOT / "evidence" / "observations" / "backtest_results.json"
    with open(json_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"JSON results: {json_path}")


if __name__ == "__main__":
    main()
