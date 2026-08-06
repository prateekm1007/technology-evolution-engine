#!/usr/bin/env python3
"""
Phase 12B — Ablation study.

Run 7 ablation tests on the expanded Li-ion timeline (14 points).
Formula B is FROZEN — we test VARIANTS that remove components,
not modifications to Formula B itself.

Tests:
1. velocity only
2. adjacency only
3. feasibility only (boolean: feasible=1, infeasible=0)
4. velocity + adjacency (no cost_bonus)
5. velocity + feasibility (no adjacency)
6. adjacency + feasibility (no velocity)
7. Formula B (full, frozen) — baseline

Plus NULL_MODEL for comparison.

One-off script. NOT a module. NOT imported by anything.
"""
import json
import pathlib
import random
import math
from collections import defaultdict
from itertools import combinations

ROOT = pathlib.Path(__file__).resolve().parents[1]

CAPABILITIES = [
    "ELECTROCHEMICAL_ENERGY_STORAGE", "ION_TRANSPORT", "INTERCALATION",
    "ELECTRON_COLLECTION", "FAST_CHARGING", "THERMAL_MANAGEMENT",
    "STATE_OF_CHARGE_MONITORING", "SAFETY_PROTECTION", "ELECTRODE_COATING",
    "CELL_ASSEMBLY",
]

TRL_TIMELINE = {
    "ELECTROCHEMICAL_ENERGY_STORAGE": {1990: 6, 1991: 9, **{y: 9 for y in [1993, 1995, 1997, 2000, 2003, 2005, 2008, 2010, 2012, 2015, 2018, 2020, 2023]}},
    "ION_TRANSPORT": {y: 9 for y in [1990, 1991, 1993, 1995, 1997, 2000, 2003, 2005, 2008, 2010, 2012, 2015, 2018, 2020, 2023]},
    "INTERCALATION": {1990: 8, 1991: 9, **{y: 9 for y in [1993, 1995, 1997, 2000, 2003, 2005, 2008, 2010, 2012, 2015, 2018, 2020, 2023]}},
    "ELECTRON_COLLECTION": {y: 9 for y in [1990, 1991, 1993, 1995, 1997, 2000, 2003, 2005, 2008, 2010, 2012, 2015, 2018, 2020, 2023]},
    "FAST_CHARGING": {1990: 1, 1991: 1, 1993: 2, 1995: 2, 1997: 3, 2000: 4, 2003: 5, 2005: 5, 2008: 6, 2010: 7, 2012: 8, 2015: 9, 2018: 9, 2020: 9, 2023: 9},
    "THERMAL_MANAGEMENT": {1990: 2, 1991: 2, 1993: 4, 1995: 5, 1997: 5, 2000: 6, 2003: 8, 2005: 9, **{y: 9 for y in [2008, 2010, 2012, 2015, 2018, 2020, 2023]}},
    "STATE_OF_CHARGE_MONITORING": {1990: 4, 1991: 5, 1993: 7, 1995: 9, **{y: 9 for y in [1997, 2000, 2003, 2005, 2008, 2010, 2012, 2015, 2018, 2020, 2023]}},
    "SAFETY_PROTECTION": {1990: 6, 1991: 7, 1993: 8, 1995: 9, **{y: 9 for y in [1997, 2000, 2003, 2005, 2008, 2010, 2012, 2015, 2018, 2020, 2023]}},
    "ELECTRODE_COATING": {y: 9 for y in [1990, 1991, 1993, 1995, 1997, 2000, 2003, 2005, 2008, 2010, 2012, 2015, 2018, 2020, 2023]},
    "CELL_ASSEMBLY": {y: 9 for y in [1990, 1991, 1993, 1995, 1997, 2000, 2003, 2005, 2008, 2010, 2012, 2015, 2018, 2020, 2023]},
}

COST_TIMELINE = {1990: 5000, 1991: 4000, 1993: 3500, 1995: 3000, 1997: 2500, 2000: 1000, 2003: 700, 2005: 500, 2008: 400, 2010: 300, 2012: 250, 2015: 200, 2018: 170, 2020: 150, 2023: 120}
COST_THRESHOLD = 100

REQUIRES_EDGES = [
    ("ELECTROCHEMICAL_ENERGY_STORAGE", "ION_TRANSPORT"),
    ("ELECTROCHEMICAL_ENERGY_STORAGE", "INTERCALATION"),
    ("FAST_CHARGING", "ION_TRANSPORT"),
    ("FAST_CHARGING", "THERMAL_MANAGEMENT"),
    ("CELL_ASSEMBLY", "ELECTRODE_COATING"),
    ("SAFETY_PROTECTION", "STATE_OF_CHARGE_MONITORING"),
]

EVENTS = [
    {"year": 1992, "combination": ["ELECTROCHEMICAL_ENERGY_STORAGE", "INTERCALATION", "CELL_ASSEMBLY"]},
    {"year": 1996, "combination": ["ELECTROCHEMICAL_ENERGY_STORAGE", "INTERCALATION", "ELECTRODE_COATING"]},
    {"year": 1997, "combination": ["ELECTROCHEMICAL_ENERGY_STORAGE", "INTERCALATION", "STATE_OF_CHARGE_MONITORING"]},
    {"year": 2001, "combination": ["ELECTROCHEMICAL_ENERGY_STORAGE", "INTERCALATION", "ELECTRON_COLLECTION"]},
    {"year": 2003, "combination": ["ELECTROCHEMICAL_ENERGY_STORAGE", "THERMAL_MANAGEMENT", "SAFETY_PROTECTION"]},
    {"year": 2004, "combination": ["ELECTROCHEMICAL_ENERGY_STORAGE", "INTERCALATION", "ELECTRON_COLLECTION"]},
    {"year": 2008, "combination": ["ELECTROCHEMICAL_ENERGY_STORAGE", "THERMAL_MANAGEMENT", "STATE_OF_CHARGE_MONITORING"]},
    {"year": 2010, "combination": ["ELECTROCHEMICAL_ENERGY_STORAGE", "FAST_CHARGING", "THERMAL_MANAGEMENT", "SAFETY_PROTECTION"]},
    {"year": 2012, "combination": ["FAST_CHARGING", "THERMAL_MANAGEMENT"]},
    {"year": 2016, "combination": ["ELECTROCHEMICAL_ENERGY_STORAGE", "ELECTRODE_COATING", "CELL_ASSEMBLY"]},
    {"year": 2017, "combination": ["ELECTROCHEMICAL_ENERGY_STORAGE", "INTERCALATION", "ELECTRON_COLLECTION"]},
    {"year": 2019, "combination": ["FAST_CHARGING", "THERMAL_MANAGEMENT", "SAFETY_PROTECTION"]},
    {"year": 2020, "combination": ["ELECTROCHEMICAL_ENERGY_STORAGE", "ELECTRODE_COATING", "CELL_ASSEMBLY"]},
    {"year": 2023, "combination": ["ELECTROCHEMICAL_ENERGY_STORAGE", "FAST_CHARGING", "THERMAL_MANAGEMENT"]},
]

TIMELINE = [1991, 1993, 1995, 1997, 2000, 2003, 2005, 2008, 2010, 2012, 2015, 2018, 2020, 2023]
HORIZON = 5


def get_trl(cap, year):
    t = TRL_TIMELINE[cap]
    trl = 1
    for y in sorted(t.keys()):
        if y <= year:
            trl = t[y]
    return trl

def get_dtrl_dt(cap, year, window=5):
    return (get_trl(cap, year) - get_trl(cap, year - window)) / float(window)

def get_cost(year):
    cost = 99999
    for y in sorted(COST_TIMELINE.keys()):
        if y <= year:
            cost = COST_TIMELINE[y]
    return cost

def get_cost_velocity(year, window=5):
    c_now = get_cost(year)
    c_before = get_cost(year - window)
    if c_before == 0:
        return 0
    return (c_before - c_now) / (c_before * window)

def get_mature(year, min_trl=5):
    return {c for c in CAPABILITIES if get_trl(c, year) >= min_trl}

def get_priors(year):
    return set(frozenset(e["combination"]) for e in EVENTS if e["year"] < year)

def get_actuals(T, horizon=5):
    return set(frozenset(e["combination"]) for e in EVENTS if T < e["year"] <= T + horizon)

def get_combos(mature, year):
    combos = []
    for size in range(2, min(5, len(mature) + 1)):
        for combo in combinations(sorted(mature), size):
            valid = True
            for src, tgt in REQUIRES_EDGES:
                if src in combo and get_trl(tgt, year) < 5:
                    valid = False
                    break
            if valid:
                combos.append(frozenset(combo))
    return combos

def is_feasible(combo, year):
    if not any(get_trl(c, year) >= 7 for c in combo):
        return False
    if "FAST_CHARGING" in combo and get_trl("THERMAL_MANAGEMENT", year) < 5:
        return False
    return True


# ═══ ABLATION SCORING FUNCTIONS ═══

def score_velocity_only(combo, year, priors):
    """Just velocity — no adjacency, no cost, no feasibility filter."""
    velocities = [get_dtrl_dt(c, year) for c in combo]
    return min(max(velocities) / 2.0, 1.0) if velocities else 0

def score_adjacency_only(combo, year, priors):
    """Just adjacency — no velocity, no cost."""
    combo_set = set(combo)
    min_dist = float('inf')
    for p in priors:
        d = len(combo_set.symmetric_difference(set(p)))
        min_dist = min(min_dist, d)
    if min_dist == float('inf'):
        return 1.0
    if min_dist == 0:
        return 0.1  # already exists — low score
    return 1.0 / (1.0 + min_dist)

def score_feasibility_only(combo, year, priors):
    """Just feasibility — boolean: feasible=1, infeasible=0."""
    return 1.0 if is_feasible(combo, year) else 0.0

def score_velocity_adjacency(combo, year, priors):
    """velocity × adjacency — no cost_bonus."""
    v = min(max(get_dtrl_dt(c, year) for c in combo) / 2.0, 1.0) if combo else 0
    combo_set = set(combo)
    min_dist = float('inf')
    for p in priors:
        d = len(combo_set.symmetric_difference(set(p)))
        min_dist = min(min_dist, d)
    a = 1.0 if min_dist == float('inf') else (0.1 if min_dist == 0 else 1.0 / (1.0 + min_dist))
    return v * a

def score_velocity_feasibility(combo, year, priors):
    """velocity × feasibility — no adjacency."""
    if not is_feasible(combo, year):
        return 0
    v = min(max(get_dtrl_dt(c, year) for c in combo) / 2.0, 1.0) if combo else 0
    return v

def score_adjacency_feasibility(combo, year, priors):
    """adjacency × feasibility — no velocity."""
    if not is_feasible(combo, year):
        return 0
    combo_set = set(combo)
    min_dist = float('inf')
    for p in priors:
        d = len(combo_set.symmetric_difference(set(p)))
        min_dist = min(min_dist, d)
    a = 1.0 if min_dist == float('inf') else (0.1 if min_dist == 0 else 1.0 / (1.0 + min_dist))
    return a

def score_formula_b_frozen(combo, year, priors):
    """Formula B (FROZEN): velocity × adjacency + cost_bonus × 0.3 × adjacency."""
    v = min(max(get_dtrl_dt(c, year) for c in combo) / 2.0, 1.0) if combo else 0
    combo_set = set(combo)
    min_dist = float('inf')
    for p in priors:
        d = len(combo_set.symmetric_difference(set(p)))
        min_dist = min(min_dist, d)
    a = 1.0 if min_dist == float('inf') else 1.0 / (1.0 + min_dist)
    cv = get_cost_velocity(year)
    cb = min(cv, 0.5)
    return v * a + cb * 0.3 * a


def run_ablation():
    print("=" * 70)
    print("ABLATION STUDY — Phase 12B")
    print("7 tests: remove one variable at a time")
    print("=" * 70)

    formulas = {
        "1. velocity only": (score_velocity_only, False),        # no feasibility filter
        "2. adjacency only": (score_adjacency_only, False),
        "3. feasibility only": (score_feasibility_only, False),
        "4. velocity + adjacency": (score_velocity_adjacency, False),
        "5. velocity + feasibility": (score_velocity_feasibility, True),  # has feasibility
        "6. adjacency + feasibility": (score_adjacency_feasibility, True),
        "7. Formula B (frozen)": (score_formula_b_frozen, False),  # B doesn't filter; it scores
    }

    results = {}

    for name, (score_fn, has_feas_filter) in formulas.items():
        total_tp = 0
        total_fp = 0
        total_actual = 0
        per_t_precs = []

        for T in TIMELINE:
            mature = get_mature(T)
            priors = get_priors(T)
            combos = get_combos(mature, T)
            actual = get_actuals(T, HORIZON)

            scored = []
            for combo in combos:
                combo_list = sorted(list(combo))
                # For formulas that include feasibility in the score,
                # we still score all combos (feasible ones get 0).
                # For formulas without feasibility, we DON'T filter.
                score = score_fn(combo_list, T, priors)
                scored.append((combo, score))

            scored.sort(key=lambda x: -x[1])
            top10 = set(c for c, s in scored[:10])
            tp = top10 & actual
            fp = top10 - actual

            total_tp += len(tp)
            total_fp += len(fp)
            total_actual += len(actual)
            prec = len(tp) / len(top10) if top10 else 0
            per_t_precs.append(round(prec, 4))

        total_prec = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
        total_rec = total_tp / total_actual if total_actual > 0 else 0

        results[name] = {
            "precision": round(total_prec, 4),
            "recall": round(total_rec, 4),
            "tp": total_tp,
            "fp": total_fp,
            "per_t": per_t_precs,
        }

        print(f"\n  {name}:")
        print(f"    precision={total_prec:.4f} ({total_prec*100:.2f}%) tp={total_tp} fp={total_fp} rec={total_rec:.4f}")
        print(f"    per-T: {per_t_precs}")

    # NULL_MODEL
    random.seed(42)
    null_tp = 0
    null_pred = 0
    null_actual = 0
    for T in TIMELINE:
        mature = get_mature(T)
        combos = get_combos(mature, T)
        actual = get_actuals(T, HORIZON)
        preds = set(random.sample(combos, min(10, len(combos))))
        null_tp += len(preds & actual)
        null_pred += len(preds)
        null_actual += len(actual)
    null_prec = null_tp / null_pred if null_pred else 0
    print(f"\n  NULL_MODEL: precision={null_prec:.4f} tp={null_tp} fp={null_pred - null_tp}")

    # ─── Comparison ───
    print(f"\n{'=' * 70}")
    print("ABLATION COMPARISON")
    print(f"{'=' * 70}")
    print(f"\n{'Formula':<30} {'Precision':>10} {'TP':>5} {'FP':>5} {'vs Formula B':>12}")
    print(f"{'-'*62}")

    fb_prec = results["7. Formula B (frozen)"]["precision"]
    for name in sorted(results.keys()):
        r = results[name]
        delta = r["precision"] - fb_prec
        marker = ""
        if name != "7. Formula B (frozen)":
            if abs(delta) < 0.005:
                marker = "≈ SAME"
            elif delta > 0:
                marker = f"+{delta:.4f} ↑"
            else:
                marker = f"{delta:.4f} ↓"
        print(f"  {name:<28} {r['precision']:>10.4f} {r['tp']:>5} {r['fp']:>5} {marker:>12}")

    print(f"  {'NULL_MODEL':<28} {null_prec:>10.4f} {null_tp:>5} {null_pred - null_tp:>5}")

    # ─── Verdict ───
    print(f"\n{'=' * 70}")
    print("VERDICT")
    print(f"{'=' * 70}")

    v_only = results["1. velocity only"]["precision"]
    a_only = results["2. adjacency only"]["precision"]
    f_only = results["3. feasibility only"]["precision"]
    va = results["4. velocity + adjacency"]["precision"]
    vf = results["5. velocity + feasibility"]["precision"]
    af = results["6. adjacency + feasibility"]["precision"]

    print(f"\n  Formula B (frozen): {fb_prec:.4f}")
    print(f"  velocity only:      {v_only:.4f}  ({'REDUNDANT' if abs(v_only - fb_prec) < 0.005 else 'CONTRIBUTES' if v_only < fb_prec else 'BETTER'})")
    print(f"  adjacency only:     {a_only:.4f}  ({'REDUNDANT' if abs(a_only - fb_prec) < 0.005 else 'CONTRIBUTES' if a_only < fb_prec else 'BETTER'})")
    print(f"  feasibility only:   {f_only:.4f}  ({'REDUNDANT' if abs(f_only - fb_prec) < 0.005 else 'CONTRIBUTES' if f_only < fb_prec else 'BETTER'})")

    # Key comparison: velocity-only vs full Formula B
    if abs(v_only - fb_prec) < 0.005:
        print(f"\n  >>> VELOCITY-ONLY MATCHES FORMULA B.")
        print(f"  >>> The theory simplifies from 3 factors to 1: VELOCITY.")
        print(f"  >>> Adjacency and cost_bonus are redundant.")
    elif v_only > fb_prec:
        print(f"\n  >>> VELOCITY-ONLY BEATS FORMULA B ({v_only:.4f} > {fb_prec:.4f}).")
        print(f"  >>> Adjacency and cost_bonus are adding NOISE.")
    else:
        print(f"\n  >>> VELOCITY-ONLY IS WORSE THAN FORMULA B ({v_only:.4f} < {fb_prec:.4f}).")
        print(f"  >>> Adjacency and/or cost_bonus contribute INDEPENDENT SIGNAL.")
        print(f"  >>> The full formula is NECESSARY.")

    # Write results
    output_path = ROOT / "evidence" / "observations" / "ABLATION_RESULTS.md"
    with open(output_path, "w") as f:
        f.write("# ABLATION RESULTS — Phase 12B\n\n")
        f.write("## Comparison\n\n")
        f.write(f"| Formula | Precision | TP | FP | vs Formula B |\n|---|---:|---:|---:|---|\n")
        for name in sorted(results.keys()):
            r = results[name]
            delta = r["precision"] - fb_prec
            if name == "7. Formula B (frozen)":
                marker = "baseline"
            elif abs(delta) < 0.005:
                marker = "≈ same"
            elif delta > 0:
                marker = f"+{delta:.4f}"
            else:
                marker = f"{delta:.4f}"
            f.write(f"| {name} | {r['precision']:.4f} | {r['tp']} | {r['fp']} | {marker} |\n")
        f.write(f"| NULL_MODEL | {null_prec:.4f} | {null_tp} | {null_pred - null_tp} | — |\n\n")
        f.write(f"## Verdict\n\n")
        if abs(v_only - fb_prec) < 0.005:
            f.write("VELOCITY-ONLY MATCHES FORMULA B. Adjacency and cost_bonus are redundant.\n")
        elif v_only > fb_prec:
            f.write("VELOCITY-ONLY BEATS FORMULA B. Adjacency and cost_bonus add noise.\n")
        else:
            f.write("VELOCITY-ONLY IS WORSE. Adjacency and/or cost_bonus contribute independent signal.\n")

    json_path = ROOT / "evidence" / "observations" / "ablation_results.json"
    with open(json_path, "w") as f:
        json.dump({"results": results, "null_model": {"precision": null_prec, "tp": null_tp}}, f, indent=2)

    print(f"\nResults: {output_path}")


if __name__ == "__main__":
    run_ablation()
