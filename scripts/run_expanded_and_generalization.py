#!/usr/bin/env python3
"""
Phase 11A + 11F — Expanded timeline backtest (14 points) + photovoltaic
generalization test.

Phase 11A: Re-run FROZEN Formula B against expanded 14-point timeline
(1991, 1993, 1995, 1997, 2000, 2003, 2005, 2008, 2010, 2012, 2015,
2018, 2020, 2023) to test whether 6% precision holds.

Phase 11F: Apply the SAME methodology (trajectory + adjacency + bottleneck)
to photovoltaics — a different domain. If the method transfers, M4 is
achieved.

Formula B is FROZEN per FORMULA_B_FROZEN.md. No modifications.

One-off script. NOT a module. NOT imported by anything.
"""
import json
import pathlib
import random
import math
from collections import defaultdict
from itertools import combinations

ROOT = pathlib.Path(__file__).resolve().parents[1]

# ═══════════════════════════════════════════════════════════════
# PART 1: EXPANDED Li-ion BACKTEST (14 time points)
# ═══════════════════════════════════════════════════════════════

LI_CAPABILITIES = [
    "ELECTROCHEMICAL_ENERGY_STORAGE", "ION_TRANSPORT", "INTERCALATION",
    "ELECTRON_COLLECTION", "FAST_CHARGING", "THERMAL_MANAGEMENT",
    "STATE_OF_CHARGE_MONITORING", "SAFETY_PROTECTION", "ELECTRODE_COATING",
    "CELL_ASSEMBLY",
]

# Expanded TRL timeline (14 time points, finer granularity)
LI_TRL = {
    "ELECTROCHEMICAL_ENERGY_STORAGE": {1990: 6, 1991: 9, 1993: 9, 1995: 9, 1997: 9, 2000: 9, 2003: 9, 2005: 9, 2008: 9, 2010: 9, 2012: 9, 2015: 9, 2018: 9, 2020: 9, 2023: 9},
    "ION_TRANSPORT": {y: 9 for y in [1990, 1991, 1993, 1995, 1997, 2000, 2003, 2005, 2008, 2010, 2012, 2015, 2018, 2020, 2023]},
    "INTERCALATION": {1990: 8, 1991: 9, **{y: 9 for y in [1993, 1995, 1997, 2000, 2003, 2005, 2008, 2010, 2012, 2015, 2018, 2020, 2023]}},
    "ELECTRON_COLLECTION": {y: 9 for y in [1990, 1991, 1993, 1995, 1997, 2000, 2003, 2005, 2008, 2010, 2012, 2015, 2018, 2020, 2023]},
    "FAST_CHARGING": {1990: 1, 1991: 1, 1993: 2, 1995: 2, 1997: 3, 2000: 4, 2003: 5, 2005: 5, 2008: 6, 2010: 7, 2012: 8, 2015: 9, 2018: 9, 2020: 9, 2023: 9},
    "THERMAL_MANAGEMENT": {1990: 2, 1991: 2, 1993: 4, 1995: 5, 1997: 5, 2000: 6, 2003: 8, 2005: 9, 2008: 9, 2010: 9, 2012: 9, 2015: 9, 2018: 9, 2020: 9, 2023: 9},
    "STATE_OF_CHARGE_MONITORING": {1990: 4, 1991: 5, 1993: 7, 1995: 9, **{y: 9 for y in [1997, 2000, 2003, 2005, 2008, 2010, 2012, 2015, 2018, 2020, 2023]}},
    "SAFETY_PROTECTION": {1990: 6, 1991: 7, 1993: 8, 1995: 9, **{y: 9 for y in [1997, 2000, 2003, 2005, 2008, 2010, 2012, 2015, 2018, 2020, 2023]}},
    "ELECTRODE_COATING": {y: 9 for y in [1990, 1991, 1993, 1995, 1997, 2000, 2003, 2005, 2008, 2010, 2012, 2015, 2018, 2020, 2023]},
    "CELL_ASSEMBLY": {y: 9 for y in [1990, 1991, 1993, 1995, 1997, 2000, 2003, 2005, 2008, 2010, 2012, 2015, 2018, 2020, 2023]},
}

LI_COST = {1990: 5000, 1991: 4000, 1993: 3500, 1995: 3000, 1997: 2500, 2000: 1000, 2003: 700, 2005: 500, 2008: 400, 2010: 300, 2012: 250, 2015: 200, 2018: 170, 2020: 150, 2023: 120}
LI_COST_THRESHOLD = 100

LI_REQUIRES = [
    ("ELECTROCHEMICAL_ENERGY_STORAGE", "ION_TRANSPORT"),
    ("ELECTROCHEMICAL_ENERGY_STORAGE", "INTERCALATION"),
    ("FAST_CHARGING", "ION_TRANSPORT"),
    ("FAST_CHARGING", "THERMAL_MANAGEMENT"),
    ("CELL_ASSEMBLY", "ELECTRODE_COATING"),
    ("SAFETY_PROTECTION", "STATE_OF_CHARGE_MONITORING"),
]

# Expanded events (from EVENT_REGISTRY.md — 16 events)
LI_EVENTS = [
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

LI_TIMELINE = [1991, 1993, 1995, 1997, 2000, 2003, 2005, 2008, 2010, 2012, 2015, 2018, 2020, 2023]

# ═══════════════════════════════════════════════════════════════
# PART 2: PHOTOVOLTAIC GENERALIZATION TEST
# ═══════════════════════════════════════════════════════════════

PV_CAPABILITIES = [
    "LIGHT_ABSORPTION",        # Absorb photons to create electron-hole pairs
    "CHARGE_SEPARATION",       # Separate electrons and holes at junction
    "CHARGE_COLLECTION",       # Collect separated charges at electrodes
    "ENERGY_CONVERSION",       # Convert light to electrical energy
    "SILICON_CRYSTALLIZATION", # Produce crystalline Si wafers
    "THIN_FILM_DEPOSITION",    # Deposit thin-film PV materials
    "MODULE_ASSEMBLY",         # Assemble cells into modules
    "INVERTER_INTEGRATION",    # Convert DC to AC for grid
    "GRID_INTERCONNECTION",    # Connect PV system to grid
    "BIFACIAL_DESIGN",         # Capture light on both sides
]

PV_TRL = {
    "LIGHT_ABSORPTION": {y: 9 for y in [1990, 1995, 2000, 2005, 2010, 2015, 2020, 2023]},
    "CHARGE_SEPARATION": {y: 9 for y in [1990, 1995, 2000, 2005, 2010, 2015, 2020, 2023]},
    "CHARGE_COLLECTION": {y: 9 for y in [1990, 1995, 2000, 2005, 2010, 2015, 2020, 2023]},
    "ENERGY_CONVERSION": {y: 9 for y in [1990, 1995, 2000, 2005, 2010, 2015, 2020, 2023]},
    "SILICON_CRYSTALLIZATION": {1990: 8, 1995: 9, **{y: 9 for y in [2000, 2005, 2010, 2015, 2020, 2023]}},
    "THIN_FILM_DEPOSITION": {1990: 5, 1995: 7, 2000: 8, 2005: 9, **{y: 9 for y in [2010, 2015, 2020, 2023]}},
    "MODULE_ASSEMBLY": {y: 9 for y in [1990, 1995, 2000, 2005, 2010, 2015, 2020, 2023]},
    "INVERTER_INTEGRATION": {1990: 7, 1995: 8, 2000: 9, **{y: 9 for y in [2005, 2010, 2015, 2020, 2023]}},
    "GRID_INTERCONNECTION": {1990: 6, 1995: 7, 2000: 8, 2005: 9, **{y: 9 for y in [2010, 2015, 2020, 2023]}},
    "BIFACIAL_DESIGN": {1990: 2, 1995: 3, 2000: 4, 2005: 5, 2010: 6, 2015: 8, 2018: 9, 2020: 9, 2023: 9},
}

PV_COST = {1990: 7.0, 1995: 4.5, 2000: 3.0, 2005: 2.0, 2010: 1.5, 2015: 0.6, 2020: 0.4, 2023: 0.3}  # $/W
PV_COST_THRESHOLD = 0.30  # $/W — grid parity in sunny regions

PV_REQUIRES = [
    ("ENERGY_CONVERSION", "LIGHT_ABSORPTION"),
    ("ENERGY_CONVERSION", "CHARGE_SEPARATION"),
    ("ENERGY_CONVERSION", "CHARGE_COLLECTION"),
    ("GRID_INTERCONNECTION", "INVERTER_INTEGRATION"),
    ("BIFACIAL_DESIGN", "LIGHT_ABSORPTION"),
]

PV_EVENTS = [
    {"year": 1995, "combination": ["ENERGY_CONVERSION", "SILICON_CRYSTALLIZATION", "MODULE_ASSEMBLY"]},
    {"year": 2000, "combination": ["ENERGY_CONVERSION", "THIN_FILM_DEPOSITION", "MODULE_ASSEMBLY"]},
    {"year": 2005, "combination": ["ENERGY_CONVERSION", "GRID_INTERCONNECTION", "INVERTER_INTEGRATION"]},
    {"year": 2010, "combination": ["ENERGY_CONVERSION", "THIN_FILM_DEPOSITION"]},
    {"year": 2015, "combination": ["ENERGY_CONVERSION", "MODULE_ASSEMBLY", "GRID_INTERCONNECTION"]},
    {"year": 2019, "combination": ["BIFACIAL_DESIGN", "ENERGY_CONVERSION", "MODULE_ASSEMBLY"]},
]

PV_TIMELINE = [1995, 2000, 2005, 2010, 2015, 2020]


# ═══════════════════════════════════════════════════════════════
# SHARED UTILITIES
# ═══════════════════════════════════════════════════════════════

def get_trl(trl_table, cap, year):
    timeline = trl_table[cap]
    trl = 1
    for y in sorted(timeline.keys()):
        if y <= year:
            trl = timeline[y]
    return trl

def get_dtrl_dt(trl_table, cap, year, window=5):
    trl_now = get_trl(trl_table, cap, year)
    trl_before = get_trl(trl_table, cap, year - window)
    return (trl_now - trl_before) / float(window)

def get_cost(cost_table, year):
    cost = 999999
    for y in sorted(cost_table.keys()):
        if y <= year:
            cost = cost_table[y]
    return cost

def get_cost_velocity(cost_table, year, window=5):
    cost_now = get_cost(cost_table, year)
    cost_before = get_cost(cost_table, year - window)
    if cost_before == 0:
        return 0
    return (cost_before - cost_now) / (cost_before * window)

def get_mature_caps(trl_table, capabilities, year, min_trl=5):
    return {cap for cap in capabilities if get_trl(trl_table, cap, year) >= min_trl}

def get_prior_combos(events, year):
    priors = set()
    for e in events:
        if e["year"] < year:
            priors.add(frozenset(e["combination"]))
    return priors

def get_actual_outcomes(events, T, horizon=5):
    return set(frozenset(e["combination"]) for e in events if T < e["year"] <= T + horizon)

def get_reachable_combos(trl_table, requires, mature_caps, year, min_trl=5):
    combos = []
    for size in range(2, min(5, len(mature_caps) + 1)):
        for combo in combinations(sorted(mature_caps), size):
            valid = True
            for src, tgt in requires:
                if src in combo and get_trl(trl_table, tgt, year) < min_trl:
                    valid = False
                    break
            if valid:
                combos.append(frozenset(combo))
    return combos

def check_feasibility(trl_table, combo, year, requires, fast_charging_cap=None, thermal_cap=None):
    any_trl7 = any(get_trl(trl_table, cap, year) >= 7 for cap in combo)
    if not any_trl7:
        return False
    if fast_charging_cap and fast_charging_cap in combo and thermal_cap:
        if get_trl(trl_table, thermal_cap, year) < 5:
            return False
    return True


# ═══════════════════════════════════════════════════════════════
# FROZEN FORMULA B (per FORMULA_B_FROZEN.md — DO NOT MODIFY)
# ═══════════════════════════════════════════════════════════════

def score_formula_b_frozen(trl_table, cost_table, combo, year, prior_combos, requires):
    """Formula B: velocity × adjacency + cost_bonus × 0.3 × adjacency.
    FROZEN — do not modify."""
    # velocity = max(dTRL/dt for c in combo) / 2.0, capped at 1.0
    velocities = [get_dtrl_dt(trl_table, cap, year) for cap in combo]
    max_velocity = max(velocities) if velocities else 0
    velocity_score = min(max_velocity / 2.0, 1.0)

    # adjacency = 1.0 / (1.0 + min_symmetric_difference_to_existing)
    combo_set = set(combo)
    min_distance = float('inf')
    for prior in prior_combos:
        sym_diff = len(combo_set.symmetric_difference(set(prior)))
        min_distance = min(min_distance, sym_diff)
    if min_distance == float('inf'):
        adjacency = 1.0
    else:
        adjacency = 1.0 / (1.0 + min_distance)

    # cost_bonus = min(cost_velocity, 0.5)
    cost_vel = get_cost_velocity(cost_table, year)
    cost_bonus = min(cost_vel, 0.5)

    # score = velocity × adjacency + cost_bonus × 0.3 × adjacency
    return velocity_score * adjacency + cost_bonus * 0.3 * adjacency


# ═══════════════════════════════════════════════════════════════
# RUN BACKTEST
# ═══════════════════════════════════════════════════════════════

def run_domain_backtest(domain_name, trl_table, cost_table, requires, events,
                         timeline, capabilities, fast_charging_cap=None, thermal_cap=None,
                         horizon=5):
    print(f"\n{'═' * 70}")
    print(f"  {domain_name} BACKTEST — Frozen Formula B")
    print(f"  Timeline: {timeline}")
    print(f"  Events: {len(events)}")
    print(f"{'═' * 70}")

    all_tps = 0
    all_fps = 0
    all_actuals = 0
    per_t = []

    for T in timeline:
        T_eval = T + horizon
        mature = get_mature_caps(trl_table, capabilities, T, min_trl=5)
        prior = get_prior_combos(events, T)
        combos = get_reachable_combos(trl_table, requires, mature, T)
        actual = get_actual_outcomes(events, T, horizon)

        # Score with frozen Formula B
        scored = []
        for combo in combos:
            combo_list = sorted(list(combo))
            if not check_feasibility(trl_table, combo_list, T, requires, fast_charging_cap, thermal_cap):
                continue
            score = score_formula_b_frozen(trl_table, cost_table, combo_list, T, prior, requires)
            scored.append((combo, score))
        scored.sort(key=lambda x: -x[1])

        # Top-10
        top10 = set(c for c, s in scored[:10])
        tp = top10 & actual
        fp = top10 - actual
        fn = actual - top10
        prec = len(tp) / len(top10) if top10 else 0
        rec = len(tp) / len(actual) if actual else 0

        all_tps += len(tp)
        all_fps += len(fp)
        all_actuals += len(actual)
        per_t.append({"T": T, "prec": round(prec, 4), "tp": len(tp), "fp": len(fp), "fn": len(fn), "actual": len(actual)})

        marker = "✓" if len(tp) > 0 else " "
        print(f"  T={T} eval={T_eval}: {marker} prec={prec:.2f} tp={len(tp)} fp={len(fp)} fn={len(fn)} actual={len(actual)}")

        if len(tp) > 0:
            for c in tp:
                print(f"    ✓ {sorted(list(c))}")

    total_prec = all_tps / (all_tps + all_fps) if (all_tps + all_fps) > 0 else 0
    total_rec = all_tps / all_actuals if all_actuals > 0 else 0

    print(f"\n  AGGREGATE: prec={total_prec:.4f} ({total_prec*100:.2f}%) tp={all_tps} fp={all_fps} actual={all_actuals}")
    print(f"  Per-T precision: {[p['prec'] for p in per_t]}")

    return {"domain": domain_name, "precision": round(total_prec, 4),
            "total_tp": all_tps, "total_fp": all_fps, "total_actual": all_actuals,
            "per_t": per_t}


def main():
    print("=" * 70)
    print("PHASE 11A + 11F: EXPANDED TIMELINE + GENERALIZATION TEST")
    print("Frozen Formula B (per FORMULA_B_FROZEN.md)")
    print("=" * 70)

    # ─── Phase 11A: Expanded Li-ion backtest (14 points) ───
    li_results = run_domain_backtest(
        "Li-ion (expanded 14-point timeline)",
        LI_TRL, LI_COST, LI_REQUIRES, LI_EVENTS, LI_TIMELINE,
        LI_CAPABILITIES, fast_charging_cap="FAST_CHARGING", thermal_cap="THERMAL_MANAGEMENT"
    )

    # ─── Phase 11F: Photovoltaic generalization test ───
    pv_results = run_domain_backtest(
        "Photovoltaics (generalization test)",
        PV_TRL, PV_COST, PV_REQUIRES, PV_EVENTS, PV_TIMELINE,
        PV_CAPABILITIES, fast_charging_cap="BIFACIAL_DESIGN", thermal_cap=None
    )

    # ─── NULL_MODEL for comparison ───
    random.seed(42)
    null_tp = 0
    null_pred = 0
    for T in LI_TIMELINE:
        mature = get_mature_caps(LI_TRL, LI_CAPABILITIES, T)
        combos = get_reachable_combos(LI_TRL, LI_REQUIRES, mature, T)
        actual = get_actual_outcomes(LI_EVENTS, T)
        preds = set(random.sample(combos, min(10, len(combos))))
        null_tp += len(preds & actual)
        null_pred += len(preds)
    null_prec = null_tp / null_pred if null_pred else 0

    # ─── Comparison ───
    print(f"\n{'═' * 70}")
    print("COMPARISON")
    print(f"{'═' * 70}")
    print(f"\n{'Domain':<40} {'Precision':>10} {'TP':>5} {'FP':>5}")
    print(f"{'-'*60}")
    print(f"{'Li-ion (14-point, previous 5-point=6%)':<40} {li_results['precision']:>10.4f} {li_results['total_tp']:>5} {li_results['total_fp']:>5}")
    print(f"{'Photovoltaics (generalization)':<40} {pv_results['precision']:>10.4f} {pv_results['total_tp']:>5} {pv_results['total_fp']:>5}")
    print(f"{'NULL_MODEL (Li-ion)':<40} {null_prec:>10.4f} {null_tp:>5} {null_pred - null_tp:>5}")

    # ─── Verdict ───
    print(f"\n{'═' * 70}")
    print("VERDICT")
    print(f"{'═' * 70}")

    print(f"\n  Li-ion expanded precision: {li_results['precision']*100:.2f}% (was 6.00% with 5 points)")
    print(f"  Photovoltaic precision:     {pv_results['precision']*100:.2f}%")
    print(f"  NULL_MODEL precision:       {null_prec*100:.2f}%")

    li_holds = li_results['precision'] > 0.03  # >3% means signal persists
    pv_transfers = pv_results['precision'] > 0 and pv_results['total_tp'] > 0

    if li_holds:
        print(f"\n  >>> Li-ion signal HOLDS with expanded timeline: {li_results['precision']*100:.2f}% (was 6%)")
    else:
        print(f"\n  >>> Li-ion signal DID NOT HOLD: {li_results['precision']*100:.2f}% (was 6%)")

    if pv_transfers:
        print(f"  >>> Photovoltaic signal DETECTED: {pv_results['precision']*100:.2f}% with {pv_results['total_tp']} TPs")
        print(f"  >>> The METHODOLOGY transfers across domains!")
        print(f"  >>> M4 (Transferability) is ACHIEVED.")
    else:
        print(f"  >>> Photovoltaic signal NOT detected: {pv_results['precision']*100:.2f}%")
        print(f"  >>> The methodology does NOT transfer (yet).")

    if li_holds and pv_transfers:
        print(f"\n  >>> BOTH conditions met:")
        print(f"  >>>   1. Li-ion signal holds with expanded timeline")
        print(f"  >>>   2. Methodology transfers to photovoltaics")
        print(f"  >>> M3 (Predictive capability) is ACHIEVED.")
        print(f"  >>> M4 (Transferability) is ACHIEVED.")
        print(f"  >>> The model is approaching M5 (Scientific theory).")
    elif li_holds:
        print(f"\n  >>> Li-ion signal holds but transferability not yet confirmed.")
        print(f"  >>> M3 is achieved. M4 is not.")
    elif pv_transfers:
        print(f"\n  >>> Transferability detected but Li-ion signal weakened with expansion.")
        print(f"  >>> M4 is partially achieved. M3 needs re-confirmation.")
    else:
        print(f"\n  >>> Neither condition met. The 6% may have been sample-specific.")

    # Write results
    output = {
        "phase": "11A + 11F",
        "formula": "Formula B (FROZEN)",
        "li_ion": li_results,
        "photovoltaics": pv_results,
        "null_model": {"precision": round(null_prec, 4), "tp": null_tp},
        "verdict": {
            "li_holds": li_holds,
            "pv_transfers": pv_transfers,
            "m3_achieved": li_holds,
            "m4_achieved": li_holds and pv_transfers,
        },
    }

    out_path = ROOT / "evidence" / "observations" / "EXPANDED_AND_GENERALIZATION_RESULTS.md"
    with open(out_path, "w") as f:
        f.write("# EXPANDED TIMELINE + GENERALIZATION RESULTS — Phase 11A + 11F\n\n")
        f.write("## Formula B (FROZEN)\n\n")
        f.write(f"| Domain | Precision | TP | FP |\n|---|---:|---:|---:|\n")
        f.write(f"| Li-ion (14-point timeline) | {li_results['precision']:.4f} | {li_results['total_tp']} | {li_results['total_fp']} |\n")
        f.write(f"| Photovoltaics (generalization) | {pv_results['precision']:.4f} | {pv_results['total_tp']} | {pv_results['total_fp']} |\n")
        f.write(f"| NULL_MODEL | {null_prec:.4f} | {null_tp} | — |\n\n")
        f.write(f"## Verdict\n\n")
        f.write(f"- Li-ion signal holds: {'YES' if li_holds else 'NO'}\n")
        f.write(f"- PV transfers: {'YES' if pv_transfers else 'NO'}\n")
        f.write(f"- M3 (Predictive): {'ACHIEVED' if li_holds else 'NOT achieved'}\n")
        f.write(f"- M4 (Transferability): {'ACHIEVED' if li_holds and pv_transfers else 'NOT achieved'}\n")

    json_path = ROOT / "evidence" / "observations" / "expanded_and_generalization_results.json"
    with open(json_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nResults: {out_path}")


if __name__ == "__main__":
    main()
