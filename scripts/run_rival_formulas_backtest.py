#!/usr/bin/env python3
"""
Phase 10 — Rival formulas backtest.

Tests Formulas B, C, D against the frozen-time backtest and compares
to NULL_MODEL and the rejected Formula A.

Formula A (REJECTED): readiness × novelty × feasibility
Formula B: velocity × adjacency × feasibility
Formula C: constraint_removal_rate × capability_growth_rate
Formula D: bottleneck_resolution_score
NULL_MODEL: random selection

Key changes from previous formulas:
- Formula B: uses MAX(dTRL/dt) instead of MIN(TRL); uses 1/(1+distance) instead of 1-jaccard
- Formula C: multiplies two VELOCITY signals (constraint weakening × capability rising)
- Formula D: scores based on distance to bottleneck resolution (1/time_to_resolution)

One-off script. NOT a module. NOT imported by anything.
"""
import json
import pathlib
import random
from collections import defaultdict
from itertools import combinations

ROOT = pathlib.Path("/home/z/my-project/audit/repo")

CAPABILITIES = [
    "ELECTROCHEMICAL_ENERGY_STORAGE", "ION_TRANSPORT", "INTERCALATION",
    "ELECTRON_COLLECTION", "FAST_CHARGING", "THERMAL_MANAGEMENT",
    "STATE_OF_CHARGE_MONITORING", "SAFETY_PROTECTION", "ELECTRODE_COATING",
    "CELL_ASSEMBLY",
]

# TRL timeline (calibrated, same as previous backtest)
TRL_TIMELINE = {
    "ELECTROCHEMICAL_ENERGY_STORAGE": {1991: 9, 1995: 9, 2000: 9, 2005: 9, 2010: 9, 2015: 9, 2020: 9},
    "ION_TRANSPORT": {1991: 9, 1995: 9, 2000: 9, 2005: 9, 2010: 9, 2015: 9, 2020: 9},
    "INTERCALATION": {1991: 9, 1995: 9, 2000: 9, 2005: 9, 2010: 9, 2015: 9, 2020: 9},
    "ELECTRON_COLLECTION": {1991: 9, 1995: 9, 2000: 9, 2005: 9, 2010: 9, 2015: 9, 2020: 9},
    "FAST_CHARGING": {1991: 1, 1995: 2, 2000: 4, 2005: 5, 2010: 7, 2015: 9, 2020: 9},
    "THERMAL_MANAGEMENT": {1991: 2, 1995: 5, 2000: 6, 2005: 9, 2010: 9, 2015: 9, 2020: 9},
    "STATE_OF_CHARGE_MONITORING": {1991: 5, 1995: 9, 2000: 9, 2005: 9, 2010: 9, 2015: 9, 2020: 9},
    "SAFETY_PROTECTION": {1991: 7, 1995: 9, 2000: 9, 2005: 9, 2010: 9, 2015: 9, 2020: 9},
    "ELECTRODE_COATING": {1991: 9, 1995: 9, 2000: 9, 2005: 9, 2010: 9, 2015: 9, 2020: 9},
    "CELL_ASSEMBLY": {1991: 9, 1995: 9, 2000: 9, 2005: 9, 2010: 9, 2015: 9, 2020: 9},
}

# Cost per kWh timeline (for constraint weakening)
COST_TIMELINE = {1995: 3000, 2000: 1000, 2005: 500, 2010: 300, 2015: 200, 2020: 150}
COST_THRESHOLD = 100  # $100/kWh — the "holy grail" for mass EV adoption

REQUIRES_EDGES = [
    ("ELECTROCHEMICAL_ENERGY_STORAGE", "ION_TRANSPORT"),
    ("ELECTROCHEMICAL_ENERGY_STORAGE", "INTERCALATION"),
    ("FAST_CHARGING", "ION_TRANSPORT"),
    ("FAST_CHARGING", "THERMAL_MANAGEMENT"),
    ("CELL_ASSEMBLY", "ELECTRODE_COATING"),
    ("SAFETY_PROTECTION", "STATE_OF_CHARGE_MONITORING"),
]

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


def get_trl(cap, year):
    timeline = TRL_TIMELINE[cap]
    trl = 1
    for y in sorted(timeline.keys()):
        if y <= year:
            trl = timeline[y]
    return trl


def get_trl_trajectory(cap, year):
    """Get the TRL at year and the TRL 5 years before.
    Returns (trl_now, trl_5yr_ago) for computing velocity."""
    trl_now = get_trl(cap, year)
    trl_before = get_trl(cap, year - 5)
    return trl_now, trl_before


def get_dtrl_dt(cap, year):
    """Rate of TRL change: (TRL(t) - TRL(t-5)) / 5."""
    trl_now, trl_before = get_trl_trajectory(cap, year)
    return (trl_now - trl_before) / 5.0


def get_cost(year):
    """Get cost per kWh at year."""
    cost = 3000
    for y in sorted(COST_TIMELINE.keys()):
        if y <= year:
            cost = COST_TIMELINE[y]
    return cost


def get_cost_velocity(year):
    """How fast is cost decreasing? (negative = decreasing = good).
    Returns |dCost/dt| (positive = cost is falling)."""
    cost_now = get_cost(year)
    cost_before = get_cost(year - 5)
    if cost_before == 0:
        return 0
    return (cost_before - cost_now) / cost_before  # fractional decrease


def get_mature_caps(year, min_trl=5):
    return {cap for cap in CAPABILITIES if get_trl(cap, year) >= min_trl}


def get_prior_combinations(year):
    priors = set()
    for outcome_year, outcomes in HISTORICAL_OUTCOMES.items():
        for o in outcomes:
            if o["year"] < year:
                priors.add(frozenset(o["combination"]))
    return priors


def check_feasibility(combo, year):
    """Boolean feasibility gates."""
    combo_set = set(combo)
    any_trl7 = any(get_trl(cap, year) >= 7 for cap in combo)
    if not any_trl7:
        return False
    if "FAST_CHARGING" in combo_set:
        if get_trl("THERMAL_MANAGEMENT", year) < 5:
            return False
    return True


def get_reachable_combos(mature_caps, year):
    combos = []
    for size in range(2, min(5, len(mature_caps) + 1)):
        for combo in combinations(sorted(mature_caps), size):
            valid = True
            for src, tgt in REQUIRES_EDGES:
                if src in combo and get_trl(tgt, year) < 5:
                    valid = False
                    break
            if valid:
                combos.append(frozenset(combo))
    return combos


def get_actual_outcomes(T, horizon=5):
    """Get actual outcomes in window T < year <= T+horizon."""
    actual = []
    for outcome_year, outcomes in HISTORICAL_OUTCOMES.items():
        for o in outcomes:
            if T < o["year"] <= T + horizon:
                actual.append(frozenset(o["combination"]))
    return set(actual)


# ─── FORMULA A (REJECTED) ───
def score_formula_a(combo, year, prior_combos):
    """Old formula: readiness × novelty × feasibility.
    readiness = min(TRL) / 9
    novelty = 1 - max_jaccard
    """
    trls = [get_trl(cap, year) for cap in combo]
    readiness = min(trls) / 9.0

    combo_set = set(combo)
    max_sim = 0.0
    for prior in prior_combos:
        prior_set = set(prior)
        inter = len(combo_set & prior_set)
        union = len(combo_set | prior_set)
        if union > 0:
            sim = inter / union
            max_sim = max(max_sim, sim)
    novelty = 1.0 - max_sim

    return readiness * novelty


# ─── FORMULA B (velocity × adjacency × feasibility) ───
def score_formula_b(combo, year, prior_combos):
    """Formula B: velocity × adjacency × feasibility.
    velocity = max(dTRL/dt) — the FASTEST-RISING capability
    adjacency = 1/(1+graph_distance) — proximity to existing
    """
    # Velocity: max TRL change rate across combo members
    velocities = [get_dtrl_dt(cap, year) for cap in combo]
    max_velocity = max(velocities) if velocities else 0
    # Normalize: TRL change rate of 2/yr (= 10 in 5yr) is very fast
    velocity_score = min(max_velocity / 2.0, 1.0)  # cap at 1.0

    # Adjacency: proximity to nearest existing combination
    combo_set = set(combo)
    min_distance = float('inf')
    for prior in prior_combos:
        prior_set = set(prior)
        # Distance = number of capabilities that differ
        sym_diff = len(combo_set.symmetric_difference(prior_set))
        min_distance = min(min_distance, sym_diff)

    if min_distance == float('inf'):
        adjacency = 1.0  # no priors — everything is novel
    else:
        adjacency = 1.0 / (1.0 + min_distance)

    # Add cost velocity bonus
    cost_vel = get_cost_velocity(year)
    cost_bonus = min(cost_vel, 0.5)  # cap cost contribution

    return velocity_score * adjacency + cost_bonus * 0.3 * adjacency


# ─── FORMULA C (constraint_removal × capability_growth) ───
def score_formula_c(combo, year, prior_combos):
    """Formula C: constraint_removal_rate × capability_growth_rate.
    Measures the PRODUCT of two velocities:
    1. How fast are capabilities growing? (avg dTRL/dt)
    2. How fast are constraints weakening? (cost decrease + regulatory change)
    """
    # Capability growth: average TRL velocity across combo
    velocities = [get_dtrl_dt(cap, year) for cap in combo]
    avg_velocity = sum(velocities) / len(velocities) if velocities else 0
    cap_growth = min(avg_velocity / 1.0, 1.0)  # normalize: 1 TRL/yr is fast

    # Constraint removal: cost decrease + regulatory change
    cost_decrease = get_cost_velocity(year)
    # Regulatory: UN38.3 came 2003, IEC 62133 came 2012
    reg_change = 0
    if year >= 2000 and year < 2005:  # UN38.3 approaching
        reg_change = 0.3
    if year >= 2008 and year < 2013:  # IEC 62133 approaching
        reg_change += 0.3

    constraint_removal = min(cost_decrease + reg_change, 1.0)

    return cap_growth * constraint_removal


# ─── FORMULA D (bottleneck_resolution_score) ───
def score_formula_d(combo, year, prior_combos):
    """Formula D: 1 / time_to_resolution(bottleneck).
    Identifies the single blocking constraint and estimates how soon it'll be removed.

    Key insight: inventions happen when the ONE thing blocking them is about to give.
    """
    combo_set = set(combo)

    # Identify potential bottlenecks
    bottlenecks = []

    # Bottleneck 1: a capability with low TRL (emerging)
    min_trl_cap = min(combo, key=lambda c: get_trl(c, year))
    min_trl = get_trl(min_trl_cap, year)
    if min_trl < 9:
        # How fast is this capability's TRL rising?
        vel = get_dtrl_dt(min_trl_cap, year)
        if vel > 0:
            # Time to TRL 9: (9 - current_TRL) / velocity
            time_to_mature = (9 - min_trl) / vel
            bottlenecks.append(time_to_mature)
        else:
            bottlenecks.append(99)  # not improving — very far away
    else:
        bottlenecks.append(0)  # already mature

    # Bottleneck 2: cost above threshold
    cost = get_cost(year)
    cost_vel = get_cost_velocity(year)
    if cost > COST_THRESHOLD:
        if cost_vel > 0:
            # Time to reach threshold
            time_to_cost = -1  # can't easily compute without log-linear model
            # Approximate: if cost is X and decreasing at rate r,
            # time to reach threshold T = ln(X/T) / ln(1/(1-r))
            import math
            if cost_vel > 0 and cost > COST_THRESHOLD:
                ratio = COST_THRESHOLD / cost
                if cost_vel < 1:
                    time_to_cost = math.log(ratio) / math.log(1 - cost_vel) if (1 - cost_vel) > 0 else 99
                else:
                    time_to_cost = 1
            bottlenecks.append(max(time_to_cost, 0))
        else:
            bottlenecks.append(99)
    else:
        bottlenecks.append(0)  # cost already viable

    # The bottleneck is the MAXIMUM time to resolution (the hardest to fix)
    max_bottleneck = max(bottlenecks)

    if max_bottleneck <= 0:
        return 1.0  # no bottleneck — already feasible
    elif max_bottleneck >= 99:
        return 0.01  # essentially impossible
    else:
        return 1.0 / (1.0 + max_bottleneck)


def run_backtest():
    print("=" * 70)
    print("RIVAL FORMULAS BACKTEST — B vs C vs D vs NULL")
    print("=" * 70)

    backtest_points = [1995, 2000, 2005, 2010, 2015]
    horizon = 5

    formulas = {
        "A (rejected)": score_formula_a,
        "B (velocity×adjacency)": score_formula_b,
        "C (constraint×growth)": score_formula_c,
        "D (bottleneck)": score_formula_d,
    }

    all_results = {}

    for T in backtest_points:
        T_eval = T + horizon
        print(f"\n{'─' * 70}")
        print(f"T = {T} | Eval at T+{horizon} = {T_eval}")
        print(f"{'─' * 70}")

        mature_caps = get_mature_caps(T, min_trl=5)
        prior_combos = get_prior_combinations(T)
        all_combos = get_reachable_combos(mature_caps, T)
        actual_set = get_actual_outcomes(T, horizon)

        print(f"  Capabilities (TRL≥5): {len(mature_caps)}")
        print(f"  Reachable combinations: {len(all_combos)}")
        print(f"  Actual outcomes: {len(actual_set)}")

        for formula_name, score_fn in formulas.items():
            # Score all feasible combinations
            scored = []
            for combo in all_combos:
                combo_list = sorted(list(combo))
                if not check_feasibility(combo_list, T):
                    continue
                score = score_fn(combo_list, T, prior_combos)
                scored.append((combo, score))

            scored.sort(key=lambda x: -x[1])

            # Top-10
            top10 = set(c for c, s in scored[:10])
            tp = top10 & actual_set
            fp = top10 - actual_set
            fn = actual_set - top10
            prec = len(tp) / len(top10) if top10 else 0
            rec = len(tp) / len(actual_set) if actual_set else 0

            # Top-5
            top5 = set(c for c, s in scored[:5])
            tp5 = top5 & actual_set
            prec5 = len(tp5) / len(top5) if top5 else 0
            rec5 = len(tp5) / len(actual_set) if actual_set else 0

            # All feasible (unscored baseline)
            all_feasible = set(c for c, s in scored)
            tp_all = all_feasible & actual_set
            prec_all = len(tp_all) / len(all_feasible) if all_feasible else 0

            print(f"\n  {formula_name}:")
            print(f"    Top-5:  prec={prec5:.4f} rec={rec5:.4f} tp={len(tp5)} fp={len(top5)-len(tp5)} fn={len(fn)}")
            print(f"    Top-10: prec={prec:.4f} rec={rec:.4f} tp={len(tp)} fp={len(top10)-len(tp)} fn={len(fn)}")
            print(f"    All:    prec={prec_all:.4f} rec={'1.0000' if len(tp_all)==len(actual_set) else '0.0000'}")

            # Show top-5 for inspection
            if actual_set:
                for i, (c, s) in enumerate(scored[:5]):
                    is_actual = "✓ ACTUAL" if c in actual_set else ""
                    print(f"      {i+1}. score={s:.4f} {sorted(list(c))} {is_actual}")
                # Find rank of actuals
                for actual_combo in actual_set:
                    rank = next((i+1 for i, (c, s) in enumerate(scored) if c == actual_combo), None)
                    score_val = next((s for c, s in scored if c == actual_combo), None)
                    if rank:
                        print(f"      ACTUAL rank={rank}/{len(scored)} score={score_val:.4f} {sorted(list(actual_combo))}")

            key = f"T{T}_{formula_name.split(' ')[0]}"
            all_results[key] = {
                "formula": formula_name,
                "T": T,
                "top5_precision": round(prec5, 4),
                "top10_precision": round(prec, 4),
                "all_precision": round(prec_all, 4),
                "top5_recall": round(rec5, 4),
                "top10_recall": round(rec, 4),
                "tp_top10": len(tp),
                "fp_top10": len(top10) - len(tp),
                "fn_top10": len(fn),
            }

    # NULL_MODEL
    print(f"\n{'─' * 70}")
    print("NULL_MODEL (random selection)")
    print(f"{'─' * 70}")
    random.seed(42)
    null_tp_total = 0
    null_pred_total = 0
    null_actual_total = 0
    for T in backtest_points:
        mature_caps = get_mature_caps(T, min_trl=5)
        all_combos = get_reachable_combos(mature_caps, T)
        actual_set = get_actual_outcomes(T, horizon)
        null_preds = set(random.sample(all_combos, min(10, len(all_combos))))
        tp = null_preds & actual_set
        null_tp_total += len(tp)
        null_pred_total += len(null_preds)
        null_actual_total += len(actual_set)
    null_prec = null_tp_total / null_pred_total if null_pred_total else 0
    print(f"  Top-10 aggregate: prec={null_prec:.4f} tp={null_tp_total} fp={null_pred_total - null_tp_total}")

    # ─── Aggregate comparison ───
    print(f"\n{'=' * 70}")
    print("AGGREGATE COMPARISON (Top-10 precision across all backtest points)")
    print(f"{'=' * 70}")
    print(f"\n{'Formula':<30} {'Avg Top-10 Prec':>15} {'Total TP':>10} {'Total FP':>10}")
    print(f"{'-'*65}")

    for formula_short in ["A", "B", "C", "D"]:
        formula_keys = [k for k in all_results if k.startswith(f"T") and f"_{formula_short}_" in k]
        if not formula_keys:
            continue
        precisions = [all_results[k]["top10_precision"] for k in formula_keys]
        tps = [all_results[k]["tp_top10"] for k in formula_keys]
        fps = [all_results[k]["fp_top10"] for k in formula_keys]
        avg_prec = sum(precisions) / len(precisions) if precisions else 0
        total_tp = sum(tps)
        total_fp = sum(fps)
        formula_name = all_results[formula_keys[0]]["formula"]
        print(f"{formula_name:<30} {avg_prec:>15.4f} {total_tp:>10} {total_fp:>10}")

    print(f"{'NULL_MODEL':<30} {null_prec:>15.4f} {null_tp_total:>10} {null_pred_total - null_tp_total:>10}")

    # ─── Verdict ───
    print(f"\n{'=' * 70}")
    print("VERDICT")
    print(f"{'=' * 70}")

    best_formula = None
    best_prec = -1
    for formula_short in ["B", "C", "D"]:
        formula_keys = [k for k in all_results if f"_{formula_short}_" in k]
        if not formula_keys:
            continue
        precisions = [all_results[k]["top10_precision"] for k in formula_keys]
        avg_prec = sum(precisions) / len(precisions)
        if avg_prec > best_prec:
            best_prec = avg_prec
            best_formula = formula_short

    print(f"\nBest formula: {best_formula} (precision {best_prec:.4f})")
    print(f"NULL_MODEL precision: {null_prec:.4f}")
    print(f"Formula A (rejected) precision: 0.0000")

    if best_prec > null_prec and best_prec > 0:
        print(f"\n>>> Formula {best_formula} BEATS NULL_MODEL and Formula A.")
        print(f">>> Formula {best_formula} becomes the LEADING CANDIDATE.")
        print(f">>> Still experimental — not constitutional.")
    else:
        print(f"\n>>> No formula beats NULL_MODEL.")
        print(f">>> The objective function is still wrong.")
        print(f">>> Per INEVITABILITY_PROTOCOL.md: the model may need to shift from")
        print(f">>> 'predicting what might happen' to 'predicting what is inevitable.'")

    # Write results
    output_path = ROOT / "evidence" / "observations" / "RIVAL_FORMULAS_BACKTEST_RESULTS.md"
    with open(output_path, "w") as f:
        f.write("# RIVAL FORMULAS BACKTEST RESULTS — Phase 10\n\n")
        f.write("## Aggregate Top-10 Precision\n\n")
        f.write(f"| Formula | Avg Precision | Total TP | Total FP |\n|---|---:|---:|---:|\n")
        for formula_short in ["A", "B", "C", "D"]:
            formula_keys = [k for k in all_results if f"_{formula_short}_" in k]
            if not formula_keys:
                continue
            precisions = [all_results[k]["top10_precision"] for k in formula_keys]
            tps = [all_results[k]["tp_top10"] for k in formula_keys]
            fps = [all_results[k]["fp_top10"] for k in formula_keys]
            avg_prec = sum(precisions) / len(precisions) if precisions else 0
            formula_name = all_results[formula_keys[0]]["formula"]
            f.write(f"| {formula_name} | {avg_prec:.4f} | {sum(tps)} | {sum(fps)} |\n")
        f.write(f"| NULL_MODEL | {null_prec:.4f} | {null_tp_total} | {null_pred_total - null_tp_total} |\n\n")
        f.write(f"## Verdict\n\n")
        f.write(f"Best formula: {best_formula} (precision {best_prec:.4f})\n")
        f.write(f"Beats NULL: {'YES' if best_prec > null_prec and best_prec > 0 else 'NO'}\n")
        f.write(f"Beats Formula A: {'YES' if best_prec > 0 else 'NO'}\n")

    json_path = ROOT / "evidence" / "observations" / "rival_formulas_backtest_results.json"
    with open(json_path, "w") as f:
        json.dump({"all_results": all_results, "null_precision": null_prec,
                   "best_formula": best_formula, "best_precision": best_prec}, f, indent=2)

    print(f"\nResults: {output_path}")


if __name__ == "__main__":
    run_backtest()
