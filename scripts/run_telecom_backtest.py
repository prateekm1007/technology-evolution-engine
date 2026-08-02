#!/usr/bin/env python3
"""
Phase 14 — Telecom backtest.

Uses the FROZEN formula:
    score = max(dTRL/dt) × adjacency
where:
    velocity = max(dTRL/dt for c in combo) / 2.0, capped at 1.0
    adjacency = 1.0 / (1.0 + min_symmetric_difference_to_existing)

NO modifications to the formula. Per Rule 1.

Mirrors scripts/run_semiconductor_backtest.py structure but with
telecom-specific data.
"""
import json
import pathlib
import sys
import math
import random
from itertools import combinations
from math import comb, erf

ROOT = pathlib.Path(__file__).resolve().parents[1]
EVIDENCE_DIR = ROOT / "evidence" / "observations"
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TELECOM DOMAIN DATA (per committed registries)
# ═══════════════════════════════════════════════════════════════════════════════

CAPABILITIES = [
    # Rising
    "WIRELESS_PROTOCOL",
    "SPECTRUM_UTILIZATION",
    "PACKET_SWITCHING",
    "SMART_DEVICE_INTEGRATION",
    "NETWORK_VIRTUALIZATION",
    # Stable
    "RADIO_TRANSMISSION",
    "ANTENNA_HARDWARE",
    "INFRASTRUCTURE_DEPLOYMENT",
]

# TRL at each T-point (per TELECOM_TRAJECTORY_REGISTRY.md)
# T-points: 1980, 1985, 1990, 1995, 2000, 2005, 2010, 2015, 2020, 2025
# Note: include 1975 for velocity computation at T=1980 (window=5)
TRL_TIMELINE = {
    "WIRELESS_PROTOCOL": {
        1975: 3, 1980: 5, 1985: 9, 1990: 9, 1995: 9, 2000: 9,
        2005: 9, 2010: 9, 2015: 9, 2020: 9, 2025: 9,
    },
    "SPECTRUM_UTILIZATION": {
        1975: 9, 1980: 9, 1985: 9, 1990: 9, 1995: 9, 2000: 9,
        2005: 9, 2010: 9, 2015: 5, 2020: 9, 2025: 9,
    },
    "PACKET_SWITCHING": {
        1975: 9, 1980: 9, 1985: 5, 1990: 7, 1995: 9, 2000: 9,
        2005: 9, 2010: 9, 2015: 9, 2020: 9, 2025: 9,
    },
    "SMART_DEVICE_INTEGRATION": {
        1975: 9, 1980: 9, 1985: 9, 1990: 9, 1995: 9, 2000: 9,
        2005: 5, 2010: 9, 2015: 5, 2020: 9, 2025: 9,
    },
    "NETWORK_VIRTUALIZATION": {
        1975: 1, 1980: 1, 1985: 1, 1990: 1, 1995: 1, 2000: 3,
        2005: 4, 2010: 5, 2015: 6, 2020: 8, 2025: 9,
    },
    # Stable throughout
    "RADIO_TRANSMISSION": {y: 9 for y in
        [1975, 1980, 1985, 1990, 1995, 2000, 2005, 2010, 2015, 2020, 2025]},
    "ANTENNA_HARDWARE": {y: 9 for y in
        [1975, 1980, 1985, 1990, 1995, 2000, 2005, 2010, 2015, 2020, 2025]},
    "INFRASTRUCTURE_DEPLOYMENT": {y: 9 for y in
        [1975, 1980, 1985, 1990, 1995, 2000, 2005, 2010, 2015, 2020, 2025]},
}

# Events (per TELECOM_EVENT_REGISTRY.md)
EVENTS = [
    # Group A (scaling, no rising capability)
    {"year": 1995, "combination": ["WIRELESS_PROTOCOL", "RADIO_TRANSMISSION"], "event": "IS-95 CDMA", "group": "A"},
    {"year": 2003, "combination": ["WIRELESS_PROTOCOL", "PACKET_SWITCHING"], "event": "CDMA2000 EV-DO", "group": "A"},
    {"year": 2010, "combination": ["SMART_DEVICE_INTEGRATION", "WIRELESS_PROTOCOL"], "event": "Samsung Galaxy S", "group": "A"},
    {"year": 2014, "combination": ["WIRELESS_PROTOCOL", "PACKET_SWITCHING"], "event": "LTE Advanced", "group": "A"},
    {"year": 2017, "combination": ["WIRELESS_PROTOCOL", "SPECTRUM_UTILIZATION"], "event": "Gigabit LTE", "group": "A"},
    {"year": 2022, "combination": ["WIRELESS_PROTOCOL", "NETWORK_VIRTUALIZATION"], "event": "5G Standalone", "group": "A"},
    {"year": 2023, "combination": ["WIRELESS_PROTOCOL", "SPECTRUM_UTILIZATION"], "event": "5G Advanced", "group": "A"},
    # Group B (capability-driven, rising capability present)
    {"year": 1983, "combination": ["WIRELESS_PROTOCOL", "RADIO_TRANSMISSION", "INFRASTRUCTURE_DEPLOYMENT"], "event": "AMPS 1G", "group": "B"},
    {"year": 1991, "combination": ["WIRELESS_PROTOCOL", "RADIO_TRANSMISSION"], "event": "GSM 2G", "group": "B"},
    {"year": 2001, "combination": ["WIRELESS_PROTOCOL", "PACKET_SWITCHING"], "event": "WCDMA 3G", "group": "B"},
    {"year": 2007, "combination": ["SMART_DEVICE_INTEGRATION", "WIRELESS_PROTOCOL"], "event": "iPhone", "group": "B"},
    {"year": 2009, "combination": ["WIRELESS_PROTOCOL", "PACKET_SWITCHING", "SMART_DEVICE_INTEGRATION"], "event": "LTE 4G", "group": "B"},
    {"year": 2016, "combination": ["SMART_DEVICE_INTEGRATION", "WIRELESS_PROTOCOL"], "event": "NB-IoT", "group": "B"},
    {"year": 2019, "combination": ["WIRELESS_PROTOCOL", "SPECTRUM_UTILIZATION", "NETWORK_VIRTUALIZATION"], "event": "5G NR sub-6", "group": "B"},
    {"year": 2020, "combination": ["SPECTRUM_UTILIZATION", "WIRELESS_PROTOCOL"], "event": "5G mmWave", "group": "B"},
]

TIMELINE = [1980, 1985, 1990, 1995, 2000, 2005, 2010, 2015, 2020, 2025]
HORIZON = 5

# REQUIRES edges
# - WIRELESS_PROTOCOL requires RADIO_TRANSMISSION (need RF to transmit)
# - SMART_DEVICE_INTEGRATION requires WIRELESS_PROTOCOL (devices need protocols)
# - NETWORK_VIRTUALIZATION requires PACKET_SWITCHING (need packet core to virtualize)
REQUIRES_EDGES = [
    ("WIRELESS_PROTOCOL", "RADIO_TRANSMISSION"),
    ("SMART_DEVICE_INTEGRATION", "WIRELESS_PROTOCOL"),
    ("NETWORK_VIRTUALIZATION", "PACKET_SWITCHING"),
]

# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS (mirrors semiconductor script)
# ═══════════════════════════════════════════════════════════════════════════════

def get_trl(cap, year):
    t = TRL_TIMELINE[cap]
    trl = 1
    for y in sorted(t.keys()):
        if y <= year:
            trl = t[y]
    return trl

def get_dtrl_dt(cap, year, window=5):
    return (get_trl(cap, year) - get_trl(cap, year - window)) / float(window)

def get_mature(year, min_trl=5):
    return {c for c in CAPABILITIES if get_trl(c, year) >= min_trl}

def get_priors(year):
    return set(frozenset(e["combination"]) for e in EVENTS if e["year"] < year)

def get_actuals(T, horizon=HORIZON):
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
    return True

# ═══════════════════════════════════════════════════════════════════════════════
# FROZEN FORMULA: score = max(dTRL/dt) × adjacency
# Per Rule 1. NO modifications.
# ═══════════════════════════════════════════════════════════════════════════════

def score_frozen(combo, year, priors):
    combo_set = set(combo)

    # Velocity
    velocities = [get_dtrl_dt(c, year) for c in combo]
    v = min(max(velocities) / 2.0, 1.0) if velocities else 0
    # Note: if max(velocities) is negative (non-monotonic TRL drop),
    # v becomes negative, then min(negative/2, 1.0) = negative.
    # The frozen formula does NOT clamp negative to 0 — it produces
    # negative scores, which sort below 0. This is the formula's
    # actual behavior on non-monotonic data.

    # Adjacency
    min_dist = float('inf')
    for p in priors:
        d = len(combo_set.symmetric_difference(set(p)))
        min_dist = min(min_dist, d)
    if min_dist == float('inf'):
        a = 1.0
    elif min_dist == 0:
        a = 0.1
    else:
        a = 1.0 / (1.0 + min_dist)

    return v * a

# ═══════════════════════════════════════════════════════════════════════════════
# BACKTEST
# ═════════════════════════════════════════════════════════════════════════════════

def run_backtest(score_fn, label, seed=None):
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
            "candidates_count": len(scored),
            "actual_count": len(actual),
            "actual_events": [sorted(list(c)) for c in actual],
            "ranked_top10": [(sorted(list(c)), round(s, 6)) for c, s in scored[:10]],
            "top10_set": top10,
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "tp_count": len(tp),
            "fp_count": len(fp),
            "fn_count": len(fn),
            "precision": len(tp) / 10.0,
            "recall": len(tp) / len(actual) if actual else 0.0,
        })
    return results

def run_null_model(seed=42):
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

# ═══════════════════════════════════════════════════════════════════════════════
# STATISTICAL TESTS
# ═════════════════════════════════════════════════════════════════════════════════

def mcnemars_test(model_a, model_b, label_a, label_b):
    a_tps = set()
    b_tps = set()
    for ra, rb in zip(model_a, model_b):
        a_tps |= {(ra["T"], frozenset(c)) for c in ra["tp"]}
        b_tps |= {(rb["T"], frozenset(c)) for c in rb["tp"]}

    b_disc = len(a_tps - b_tps)
    c_disc = len(b_tps - a_tps)
    n = b_disc + c_disc

    if n == 0:
        return {"test": "mcnemar", "label_a": label_a, "label_b": label_b,
                "b_discordant": 0, "c_discordant": 0, "n_discordant": 0,
                "exact_p_two_sided": 1.0,
                "interpretation": "no discordant pairs (identical TP sets)"}

    k = min(b_disc, c_disc)
    tail = sum(comb(n, i) for i in range(k + 1)) / (2 ** n)
    p_exact = min(2 * tail, 1.0)
    return {"test": "mcnemar", "label_a": label_a, "label_b": label_b,
            "b_discordant": b_disc, "c_discordant": c_disc,
            "n_discordant": n, "exact_p_two_sided": round(p_exact, 6),
            "interpretation": (
                f"Of {n} discordant TP pairs, {b_disc} favored {label_a} "
                f"and {c_disc} favored {label_b}. Exact two-sided p = {p_exact:.4f}. "
                + ("REJECT H0." if p_exact < 0.05 else
                   "FAIL TO REJECT H0 (no significant difference)."))}

def paired_t_test(model_a, model_b, label_a, label_b):
    diffs = [ra["precision"] - rb["precision"] for ra, rb in zip(model_a, model_b)]
    n = len(diffs)
    mean_diff = sum(diffs) / n
    var = sum((d - mean_diff) ** 2 for d in diffs) / (n - 1) if n > 1 else 0
    se = math.sqrt(var / n) if n > 0 else 0
    t_stat = mean_diff / se if se > 0 else (float('inf') if mean_diff > 0 else (float('-inf') if mean_diff < 0 else 0))
    df = n - 1
    z = abs(t_stat)
    p_normal = 2 * (1 - 0.5 * (1 + erf(z / math.sqrt(2))))
    return {"test": "paired_t", "label_a": label_a, "label_b": label_b,
            "n_pairs": n, "mean_diff": round(mean_diff, 6),
            "se": round(se, 6), "t_statistic": round(t_stat, 4),
            "df": df, "p_normal_approx": round(p_normal, 6),
            "per_T_diffs": [round(d, 4) for d in diffs]}

# ═══════════════════════════════════════════════════════════════════════════════
# DESTRUCTION TEST D4: invention without velocity
# ═════════════════════════════════════════════════════════════════════════════════

def check_d4_invention_without_velocity():
    results = []
    for e in EVENTS:
        year = e["year"]
        combo = e["combination"]
        T_pred = year - 1

        velocities = [(c, get_dtrl_dt(c, T_pred)) for c in combo]
        max_v = max(v for _, v in velocities) if velocities else 0
        rising_caps = [c for c, v in velocities if v > 0.20]

        results.append({
            "year": year,
            "event": e["event"],
            "combination": combo,
            "group": e["group"],
            "T_check": T_pred,
            "velocities_at_T": [(c, round(v, 4)) for c, v in velocities],
            "max_velocity": round(max_v, 4),
            "rising_capabilities": rising_caps,
            "d4_triggered": len(rising_caps) == 0,
        })
    return results

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 72)
    print("PHASE 14 — TELECOM BACKTEST")
    print("Frozen formula: score = max(dTRL/dt) × adjacency")
    print("No modifications. Per Rule 1.")
    print("=" * 72)

    print("\n[1/3] Running frozen formula backtest...")
    fb_results = run_backtest(score_frozen, "frozen_formula")
    total_tp = sum(r["tp_count"] for r in fb_results)
    total_fp = sum(r["fp_count"] for r in fb_results)
    total_actual = sum(r["actual_count"] for r in fb_results)
    total_prec = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
    total_recall = total_tp / total_actual if total_actual > 0 else 0
    print(f"      TPs: {total_tp}, FPs: {total_fp}, Actuals: {total_actual}")
    print(f"      Precision: {total_prec:.4f} ({total_prec*100:.2f}%)")
    print(f"      Recall:    {total_recall:.4f} ({total_recall*100:.2f}%)")

    print("\n[2/3] Running NULL_MODEL (seed=42)...")
    null_results = run_null_model(seed=42)
    null_tp = sum(r["tp_count"] for r in null_results)
    null_fp = sum(r["fp_count"] for r in null_results)
    null_prec = null_tp / (null_tp + null_fp) if (null_tp + null_fp) > 0 else 0
    null_recall = null_tp / sum(r["actual_count"] for r in null_results) if sum(r["actual_count"] for r in null_results) > 0 else 0
    print(f"      NULL TPs: {null_tp}, FPs: {null_fp}")
    print(f"      NULL Precision: {null_prec:.4f} ({null_prec*100:.2f}%)")
    print(f"      NULL Recall:    {null_recall:.4f} ({null_recall*100:.2f}%)")

    print("\n[3/3] Running significance tests...")
    mc = mcnemars_test(fb_results, null_results, "frozen_formula", "NULL_MODEL")
    print(f"  McNemar: b={mc['b_discordant']}, c={mc['c_discordant']}, n={mc['n_discordant']}, p={mc['exact_p_two_sided']}")
    print(f"  → {mc['interpretation']}")

    tt = paired_t_test(fb_results, null_results, "frozen_formula", "NULL_MODEL")
    print(f"  Paired t: t({tt['df']})={tt['t_statistic']}, p_normal={tt['p_normal_approx']}")
    print(f"  Per-T diffs: {tt['per_T_diffs']}")

    # Per-T breakdown
    print("\n" + "=" * 72)
    print("PER-T BREAKDOWN")
    print("=" * 72)
    print(f"  {'T':<6} {'cands':<7} {'actuals':<9} {'FB TP':<7} {'FB prec':<9} {'FB recall':<10} {'NULL TP':<8} {'NULL prec':<10}")
    for fb, nul in zip(fb_results, null_results):
        print(f"  {fb['T']:<6} {fb['candidates_count']:<7} {fb['actual_count']:<9} "
              f"{fb['tp_count']:<7} {fb['precision']:<9.4f} {fb['recall']:<10.4f} "
              f"{nul['tp_count']:<8} {nul['precision']:<10.4f}")

    # Per-candidate Top-10 dump
    print("\n" + "=" * 72)
    print("PER-CANDIDATE TOP-10 (frozen formula)")
    print("=" * 72)
    for r in fb_results:
        print(f"\n  T={r['T']}  (candidates: {r['candidates_count']}, actuals: {r['actual_count']})")
        actual_set = set(frozenset(x) for x in r["actual_events"])
        for combo_list, score in r["ranked_top10"]:
            combo_fs = frozenset(combo_list)
            outcome = "TP" if combo_fs in actual_set else "FP"
            combo_str = "+".join(combo_list)
            print(f"    score={score:.6f}  [{outcome}]  {combo_str}")

    # Destruction test D4
    print("\n" + "=" * 72)
    print("DESTRUCTION TEST D4: Invention without velocity")
    print("=" * 72)
    print("  For each event: does the combination have any capability with")
    print("  velocity > 0.20 at year-1?")
    print()
    d4_results = check_d4_invention_without_velocity()
    d4_triggered = [r for r in d4_results if r["d4_triggered"]]
    for r in d4_results:
        marker = "D4 TRIGGERED" if r["d4_triggered"] else "OK"
        print(f"  {r['year']} [{r['group']}] {r['event']:<25} max_v={r['max_velocity']:.4f}  {marker}")
        if r["rising_capabilities"]:
            print(f"         rising: {r['rising_capabilities']}")
        else:
            print(f"         rising: NONE — all velocities ≤ 0.20")

    print(f"\n  D4 TRIGGERED: {len(d4_triggered)}/{len(d4_results)} events have NO rising capability")
    if d4_triggered:
        print(f"  → Strict necessity (FEC-002) is FALSIFIED for telecom.")
        print(f"  → Events without rising capability:")
        for r in d4_triggered:
            print(f"      {r['year']} {r['event']}")
    else:
        print(f"  → Strict necessity (FEC-002) SURVIVES for telecom.")

    # Threshold sensitivity
    print("\n" + "=" * 72)
    print("D4 THRESHOLD SENSITIVITY")
    print("=" * 72)
    thresholds = [0.20, 0.15, 0.10, 0.05, 0.01, 0.00]
    for thresh in thresholds:
        triggered = sum(1 for r in d4_results if r["max_velocity"] <= thresh)
        group_a = sum(1 for r in d4_results if r["group"] == "A" and r["max_velocity"] <= thresh)
        group_b = sum(1 for r in d4_results if r["group"] == "B" and r["max_velocity"] <= thresh)
        print(f"  threshold > {thresh:.2f}: D4 triggered on {triggered}/15 (A: {group_a}/7, B: {group_b}/8)")

    # Save JSON output
    output = {
        "phase": "14A telecom backtest",
        "formula": "score = max(dTRL/dt) × adjacency (FROZEN, no modifications)",
        "timeline": TIMELINE,
        "horizon": HORIZON,
        "capabilities": CAPABILITIES,
        "events": [{"year": e["year"], "combination": e["combination"],
                     "event": e["event"], "group": e["group"]} for e in EVENTS],
        "frozen_formula": {
            "total_tp": total_tp,
            "total_fp": total_fp,
            "total_actual": total_actual,
            "precision": round(total_prec, 6),
            "recall": round(total_recall, 6),
            "per_T": [{"T": r["T"], "candidates": r["candidates_count"],
                        "actuals": r["actual_count"], "tp": r["tp_count"],
                        "fp": r["fp_count"], "precision": r["precision"],
                        "recall": r["recall"],
                        "ranked_top10": r["ranked_top10"],
                        "actual_events": r["actual_events"]} for r in fb_results],
        },
        "null_model": {
            "total_tp": null_tp,
            "total_fp": null_fp,
            "precision": round(null_prec, 6),
            "recall": round(null_recall, 6),
            "per_T": [{"T": r["T"], "tp": r["tp_count"], "fp": r["fp_count"],
                        "precision": r["precision"], "recall": r["recall"]} for r in null_results],
        },
        "significance_tests": {
            "mcnemar": mc,
            "paired_t": tt,
        },
        "destruction_test_d4": {
            "description": "Invention without velocity",
            "events_checked": len(d4_results),
            "d4_triggered_count": len(d4_triggered),
            "d4_triggered": d4_triggered,
            "all_events": d4_results,
            "verdict": "FALSIFIED" if d4_triggered else "SURVIVES",
        },
    }

    output_path = EVIDENCE_DIR / "phase14_telecom_backtest.json"
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n{'=' * 72}")
    print(f"OUTPUT: {output_path}")
    print(f"{'=' * 72}")

    # Advancement criteria check
    print(f"\n{'=' * 72}")
    print("ADVANCEMENT CRITERIA CHECK (per PHASE_14_ADVANCEMENT_CRITERIA.md)")
    print(f"{'=' * 72}")
    c1 = total_tp >= 1
    c2 = total_prec > null_prec
    c3 = mc["exact_p_two_sided"] < 0.10
    c4 = not d4_triggered

    print(f"  Condition 1 (≥1 TP):             {'PASS' if c1 else 'FAIL'} ({total_tp} TPs)")
    print(f"  Condition 2 (prec > NULL):        {'PASS' if c2 else 'FAIL'} ({total_prec:.4f} vs {null_prec:.4f})")
    print(f"  Condition 3 (McNemar p < 0.10):  {'PASS' if c3 else 'FAIL'} (p={mc['exact_p_two_sided']})")
    print(f"  Condition 4 (no D4 falsification): {'PASS' if c4 else 'FAIL'} ({len(d4_triggered)} events without velocity)")
    print()
    all_pass = c1 and c2 and c3 and c4
    print(f"  Domain SURVIVES: {'YES' if all_pass else 'NO'}")
    if not all_pass:
        failed = []
        if not c1: failed.append("condition 1 (≥1 TP)")
        if not c2: failed.append("condition 2 (precision > NULL)")
        if not c3: failed.append("condition 3 (significance)")
        if not c4: failed.append("condition 4 (no D4 falsification)")
        print(f"  Failed: {', '.join(failed)}")


if __name__ == "__main__":
    main()
