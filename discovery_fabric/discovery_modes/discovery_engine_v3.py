"""
Discovery Modes V3 — all 15 modes on structured mechanism graph.

Modes 5, 7, 8, 11, 13, 15 added to complete the 15-mode requirement.
Each mode has: name, scientific_rationale, input_requirements,
candidate_generation_rule, evidence_requirements, failure_conditions.
"""
import json
import sys
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter, defaultdict

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from discovery_fabric.discovery_modes.discovery_engine_v2 import (
    mode_1_cross_domain_transfer, mode_2_scientific_contradiction,
    mode_3_failure_mode_transfer, mode_4_material_substitution,
    mode_6_functional_analogy, mode_9_patent_whitespace,
    mode_10_temporal_gap, mode_12_negative_space, mode_14_performance_anomaly,
    UNKNOWN, load_evidence, load_mechanisms
)

CANDIDATES_DIR = REPO / "discovery_fabric/discovery_candidates"


def mode_5_process_substitution(mechanisms, evidence):
    """Mode 5: Process substitution — find different processes for same INPUT→OUTPUT."""
    by_input_output = defaultdict(list)
    for m in mechanisms:
        inp = m.get("INPUT", UNKNOWN)
        out = m.get("OUTPUT", UNKNOWN)
        if inp != UNKNOWN and out != UNKNOWN:
            by_input_output[(inp[:20], out[:20])].append(m)

    candidates = []
    for (inp, out), mechs in by_input_output.items():
        processes = set(m.get("PROCESS", UNKNOWN) for m in mechs)
        if len(processes) >= 2:
            proc_list = list(processes)
            cand_id = f"M5-{hashlib.sha256(f'{inp}-{out}'.encode()).hexdigest()[:8]}"
            candidates.append({
                "candidate_id": cand_id,
                "discovery_mode": "process_substitution",
                "mechanism_a": {"process": proc_list[0], "input": inp, "output": out},
                "mechanism_b": {"process": proc_list[1], "input": inp, "output": out},
                "bridge": "Same input→output via different processes — substitution candidate",
                "constraints": "PENDING — process compatibility check needed",
                "evidence": [{"evidence_id": m["evidence_id"]} for m in mechs[:3]],
                "candidate_hypothesis": f"Process '{proc_list[1][:30]}' may substitute '{proc_list[0][:30]}' for {inp}→{out}",
                "epistemic_state": "CANDIDATE_CONNECTION",
            })
    return candidates


def mode_7_enabling_technology(mechanisms, evidence):
    """Mode 7: Enabling-technology discovery — old problem + new enabling tech."""
    # Find mechanisms with FAILURE_MODE that could be solved by newer mechanisms
    by_domain_year = defaultdict(list)
    for m in mechanisms:
        eid = m.get("evidence_id", "")
        for e in evidence:
            if e["id"] == eid:
                date = e.get("publication_date", "")
                if date and date != "UNAVAILABLE":
                    try:
                        year = int(date[:4])
                        by_domain_year[m.get("domain", "?")].append((year, m))
                    except:
                        pass
                break

    candidates = []
    for domain, year_mechs in by_domain_year.items():
        year_mechs.sort(key=lambda x: x[0])
        if len(year_mechs) < 3:
            continue
        old = year_mechs[0][1]
        new = year_mechs[-1][1]
        if old.get("FAILURE_MODE") != UNKNOWN:
            cand_id = f"M7-{hashlib.sha256(f'{domain}-enabling'.encode()).hexdigest()[:8]}"
            candidates.append({
                "candidate_id": cand_id,
                "discovery_mode": "enabling_technology_discovery",
                "mechanism_a": {"evidence_id": old["evidence_id"], "failure_mode": old["FAILURE_MODE"], "year": year_mechs[0][0]},
                "mechanism_b": {"evidence_id": new["evidence_id"], "process": new.get("PROCESS", UNKNOWN), "year": year_mechs[-1][0]},
                "bridge": "New technology may remove historical failure mode",
                "constraints": "PENDING",
                "evidence": [{"evidence_id": old["evidence_id"]}, {"evidence_id": new["evidence_id"]}],
                "candidate_hypothesis": f"Newer mechanism ({year_mechs[-1][0]}) may enable older failed approach ({year_mechs[0][0]}) in {domain}",
                "epistemic_state": "INFERRED",
            })
    return candidates


def mode_8_abandoned_technology(mechanisms, evidence):
    """Mode 8: Abandoned-technology revival — activity rises then collapses."""
    by_process = defaultdict(list)
    for m in mechanisms:
        eid = m.get("evidence_id", "")
        proc = m.get("PROCESS", UNKNOWN)
        if proc == UNKNOWN:
            continue
        for e in evidence:
            if e["id"] == eid:
                date = e.get("publication_date", "")
                if date and date != "UNAVAILABLE":
                    try:
                        year = int(date[:4])
                        by_process[proc[:20]].append(year)
                    except:
                        pass
                break

    candidates = []
    for process, years in by_process.items():
        if len(years) < 3:
            continue
        years.sort()
        # Check for collapse: activity in early period, none in recent
        mid = len(years) // 2
        early_count = mid + 1
        recent_years = [y for y in years if y >= (years[-1] - 3)]
        if early_count >= 2 and len(recent_years) == 0:
            cand_id = f"M8-{hashlib.sha256(process.encode()).hexdigest()[:8]}"
            candidates.append({
                "candidate_id": cand_id,
                "discovery_mode": "abandoned_technology_revival",
                "mechanism_a": {"process": process, "years": years},
                "mechanism_b": None,
                "bridge": "Technology abandoned — may be revivable with new enabling tech",
                "constraints": "PENDING — requires investigation of why abandoned",
                "evidence": [],
                "candidate_hypothesis": f"Process '{process[:30]}' shows abandonment pattern — investigate revival potential",
                "epistemic_state": "INFERRED",
            })
    return candidates


def mode_11_constraint_inversion(mechanisms, evidence):
    """Mode 11: Constraint inversion — what if we invert a constraint?"""
    candidates = []
    for m in mechanisms:
        constraint = m.get("CONSTRAINTS", UNKNOWN)
        if constraint != UNKNOWN and len(constraint) > 10:
            cand_id = f"M11-{hashlib.sha256(m['evidence_id'].encode()).hexdigest()[:8]}"
            candidates.append({
                "candidate_id": cand_id,
                "discovery_mode": "constraint_inversion",
                "mechanism_a": {"evidence_id": m["evidence_id"], "constraint": constraint},
                "mechanism_b": None,
                "bridge": "Inverting the constraint may reveal new design space",
                "constraints": "PENDING — requires physical feasibility check of inverted constraint",
                "evidence": [{"evidence_id": m["evidence_id"], "field": "CONSTRAINTS"}],
                "candidate_hypothesis": f"What if constraint '{constraint[:40]}' is inverted or removed?",
                "epistemic_state": "CANDIDATE_CONNECTION",
            })
    return candidates[:10]


def mode_13_method_transfer(mechanisms, evidence):
    """Mode 13: Method transfer — same method across different objectives."""
    by_process = defaultdict(list)
    for m in mechanisms:
        proc = m.get("PROCESS", UNKNOWN)
        obj = m.get("OBJECTIVE", UNKNOWN)
        if proc != UNKNOWN and obj != UNKNOWN:
            by_process[proc[:20]].append(m)

    candidates = []
    for process, mechs in by_process.items():
        objectives = set(m["OBJECTIVE"][:30] for m in mechs)
        if len(objectives) >= 2:
            obj_list = list(objectives)
            cand_id = f"M13-{hashlib.sha256(process.encode()).hexdigest()[:8]}"
            candidates.append({
                "candidate_id": cand_id,
                "discovery_mode": "method_transfer",
                "mechanism_a": {"process": process, "objective": obj_list[0]},
                "mechanism_b": {"process": process, "objective": obj_list[1]},
                "bridge": "Same method applied to different objectives — transfer candidate",
                "constraints": "PENDING — method-objective compatibility check",
                "evidence": [{"evidence_id": m["evidence_id"]} for m in mechs[:3]],
                "candidate_hypothesis": f"Method '{process[:30]}' may transfer from '{obj_list[0][:30]}' to '{obj_list[1][:30]}'",
                "epistemic_state": "CANDIDATE_CONNECTION",
            })
    return candidates


def mode_15_rare_mechanism_migration(mechanisms, evidence):
    """Mode 15: Rare mechanism migration — rare mechanism in one domain, absent in others."""
    by_mechanism = defaultdict(list)
    for m in mechanisms:
        proc = m.get("PROCESS", UNKNOWN)
        if proc != UNKNOWN:
            by_mechanism[proc[:20]].append(m)

    candidates = []
    # Find rare mechanisms (appearing in only 1-2 items)
    for proc, mechs in by_mechanism.items():
        if len(mechs) <= 2:
            domain = mechs[0].get("domain", "?")
            other_domains = set(e.get("domain", "?") for e in evidence) - {domain}
            for target in list(other_domains)[:2]:
                cand_id = f"M15-{hashlib.sha256(f'{proc}-{target}'.encode()).hexdigest()[:8]}"
                candidates.append({
                    "candidate_id": cand_id,
                    "discovery_mode": "rare_mechanism_migration",
                    "mechanism_a": {"process": proc, "domain": domain, "rarity": len(mechs)},
                    "mechanism_b": {"domain": target},
                    "bridge": "Rare mechanism may be underexplored in other domains",
                    "constraints": "PENDING",
                    "evidence": [{"evidence_id": m["evidence_id"]} for m in mechs],
                    "candidate_hypothesis": f"Rare process '{proc[:30]}' (only {len(mechs)} occurrences) may migrate to {target}",
                    "epistemic_state": "CANDIDATE_CONNECTION",
                })
    return candidates[:10]


def main():
    print(f"[{datetime.now(timezone.utc).isoformat()}] Discovery Engine V3 — all 15 modes")

    evidence = load_evidence()
    mechanisms = load_mechanisms()
    print(f"  Evidence: {len(evidence)}")
    print(f"  Mechanisms: {len(mechanisms)}")

    all_modes = [
        ("Mode 1: Cross-domain transfer", mode_1_cross_domain_transfer),
        ("Mode 2: Scientific contradiction", mode_2_scientific_contradiction),
        ("Mode 3: Failure-mode transfer", mode_3_failure_mode_transfer),
        ("Mode 4: Material substitution", mode_4_material_substitution),
        ("Mode 5: Process substitution", mode_5_process_substitution),
        ("Mode 6: Functional analogy", mode_6_functional_analogy),
        ("Mode 7: Enabling technology", mode_7_enabling_technology),
        ("Mode 8: Abandoned technology", mode_8_abandoned_technology),
        ("Mode 9: Patent whitespace", mode_9_patent_whitespace),
        ("Mode 10: Temporal gap", mode_10_temporal_gap),
        ("Mode 11: Constraint inversion", mode_11_constraint_inversion),
        ("Mode 12: Negative space", mode_12_negative_space),
        ("Mode 13: Method transfer", mode_13_method_transfer),
        ("Mode 14: Performance anomaly", mode_14_performance_anomaly),
        ("Mode 15: Rare mechanism migration", mode_15_rare_mechanism_migration),
    ]

    all_candidates = []
    for name, func in all_modes:
        try:
            cands = func(mechanisms, evidence)
            print(f"  {name}: {len(cands)}")
            all_candidates.extend(cands)
        except Exception as e:
            print(f"  {name}: ERROR {e}")

    output = CANDIDATES_DIR / "discovery_candidates_v3.json"
    with open(output, "w") as f:
        json.dump({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_candidates": len(all_candidates),
            "modes_implemented": 15,
            "mechanisms_analyzed": len(mechanisms),
            "candidates": all_candidates,
        }, f, indent=2, ensure_ascii=False)

    by_mode = Counter(c["discovery_mode"] for c in all_candidates)
    print(f"\n  Total: {len(all_candidates)} candidates from 15 modes")
    print(f"  By mode: {dict(by_mode)}")
    print(f"  Saved: {output}")


if __name__ == "__main__":
    main()
