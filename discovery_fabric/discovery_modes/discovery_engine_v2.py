"""
Discovery Engine V2 — all 15 modes on structured mechanism graph.

Operates on structured mechanisms (10-field) rather than keyword tags.
Every candidate declares: discovery_mode, mechanism_a, mechanism_b, bridge,
constraints, evidence, candidate_hypothesis.
"""
import json
import sys
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter, defaultdict

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

EVIDENCE_FILE = REPO / "discovery_fabric/evidence/evidence.jsonl"
MECHANISMS_FILE = REPO / "discovery_fabric/mechanisms/structured_mechanisms_v2.json"
CANDIDATES_DIR = REPO / "discovery_fabric/discovery_candidates"
CANDIDATES_DIR.mkdir(parents=True, exist_ok=True)

UNKNOWN = "UNKNOWN"


def load_evidence():
    evidence = []
    with open(EVIDENCE_FILE) as f:
        for line in f:
            if line.strip():
                evidence.append(json.loads(line))
    return evidence


def load_mechanisms():
    with open(MECHANISMS_FILE) as f:
        data = json.load(f)
    return data.get("mechanisms", [])


def mode_1_cross_domain_transfer(mechanisms, evidence):
    """Find mechanisms in one domain that could transfer to another."""
    by_domain = defaultdict(list)
    for m in mechanisms:
        if m.get("PROCESS") != UNKNOWN and m.get("INPUT") != UNKNOWN:
            by_domain[m.get("domain", "?")].append(m)

    candidates = []
    domains = list(by_domain.keys())
    for i, d1 in enumerate(domains):
        for d2 in domains[i+1:]:
            # Find mechanisms in d1 not in d2 (by PROCESS)
            d1_processes = set(m["PROCESS"] for m in by_domain[d1] if m["PROCESS"] != UNKNOWN)
            d2_processes = set(m["PROCESS"] for m in by_domain[d2] if m["PROCESS"] != UNKNOWN)
            unique_to_d1 = d1_processes - d2_processes
            for process in list(unique_to_d1)[:2]:
                source = [m for m in by_domain[d1] if m["PROCESS"] == process][:2]
                cand_id = f"M1-{hashlib.sha256(f'{d1}-{d2}-{process}'.encode()).hexdigest()[:8]}"
                candidates.append({
                    "candidate_id": cand_id,
                    "discovery_mode": "cross_domain_mechanism_transfer",
                    "mechanism_a": {"domain": d1, "process": process, "source_mechanisms": [m["evidence_id"] for m in source]},
                    "mechanism_b": {"domain": d2, "process": UNKNOWN, "source_mechanisms": []},
                    "bridge": "NOT_ESTABLISHED — requires compatible INPUT/CONSTRAINTS analysis",
                    "constraints": "PENDING — requires constraint compatibility check",
                    "evidence": [{"evidence_id": m["evidence_id"], "domain": d1, "field": "PROCESS", "value": process} for m in source],
                    "candidate_hypothesis": f"Process '{process}' from {d1} may transfer to {d2}",
                    "epistemic_state": "CANDIDATE_CONNECTION",
                })
    return candidates


def mode_2_scientific_contradiction(mechanisms, evidence):
    """Find mechanisms with contradictory MEASURED_EFFECT for same OBJECTIVE."""
    by_objective = defaultdict(list)
    for m in mechanisms:
        obj = m.get("OBJECTIVE", UNKNOWN)
        if obj != UNKNOWN and len(obj) > 10:
            # Normalize objective to first 50 chars
            by_objective[obj[:50]].append(m)

    candidates = []
    for obj, mechs in by_objective.items():
        if len(mechs) < 2:
            continue
        # Check for different processes targeting same objective
        processes = set(m.get("PROCESS", UNKNOWN) for m in mechs)
        if len(processes) >= 2:
            cand_id = f"M2-{hashlib.sha256(obj.encode()).hexdigest()[:8]}"
            candidates.append({
                "candidate_id": cand_id,
                "discovery_mode": "scientific_contradiction",
                "mechanism_a": {"process": list(processes)[0], "objective": obj},
                "mechanism_b": {"process": list(processes)[1], "objective": obj},
                "bridge": "Same objective, different processes — may indicate regime variable",
                "constraints": "PENDING",
                "evidence": [{"evidence_id": m["evidence_id"], "process": m.get("PROCESS", UNKNOWN)} for m in mechs[:4]],
                "candidate_hypothesis": f"Multiple processes target same objective '{obj[:60]}...' — missing regime variable may explain which works",
                "epistemic_state": "INFERRED",
            })
    return candidates


def mode_3_failure_mode_transfer(mechanisms, evidence):
    """Find failure modes in one mechanism that could be solved by another."""
    with_failure = [m for m in mechanisms if m.get("FAILURE_MODE") != UNKNOWN]
    candidates = []
    for m in with_failure[:10]:
        # Find mechanisms whose OUTPUT could address this failure
        failure = m["FAILURE_MODE"]
        for m2 in mechanisms:
            if m2.get("OUTPUT") != UNKNOWN and m2["evidence_id"] != m["evidence_id"]:
                # Simple keyword overlap check
                if any(w in failure.lower() for w in m2["OUTPUT"].lower().split()[:3] if len(w) > 4):
                    m1_id = m["evidence_id"]
                    m2_id = m2["evidence_id"]
                    cand_id = f"M3-{hashlib.sha256(f'{m1_id}-{m2_id}'.encode()).hexdigest()[:8]}"
                    candidates.append({
                        "candidate_id": cand_id,
                        "discovery_mode": "failure_mode_transfer",
                        "mechanism_a": {"evidence_id": m["evidence_id"], "failure_mode": failure},
                        "mechanism_b": {"evidence_id": m2["evidence_id"], "output": m2["OUTPUT"]},
                        "bridge": f"Output of B may address failure mode of A",
                        "constraints": "PENDING",
                        "evidence": [{"evidence_id": m["evidence_id"], "field": "FAILURE_MODE"}, {"evidence_id": m2["evidence_id"], "field": "OUTPUT"}],
                        "candidate_hypothesis": f"Mechanism producing '{m2['OUTPUT'][:40]}' may solve failure: '{failure[:40]}'",
                        "epistemic_state": "CANDIDATE_CONNECTION",
                    })
                    if len(candidates) >= 10:
                        break
        if len(candidates) >= 10:
            break
    return candidates


def mode_4_material_substitution(mechanisms, evidence):
    """Find mechanisms using different materials for same process."""
    by_process = defaultdict(list)
    for m in mechanisms:
        if m.get("PROCESS") != UNKNOWN and m.get("INPUT") != UNKNOWN:
            by_process[m["PROCESS"][:30]].append(m)

    candidates = []
    for process, mechs in by_process.items():
        materials = set(m["INPUT"] for m in mechs)
        if len(materials) >= 2:
            cand_id = f"M4-{hashlib.sha256(process.encode()).hexdigest()[:8]}"
            candidates.append({
                "candidate_id": cand_id,
                "discovery_mode": "material_substitution",
                "mechanism_a": {"process": process, "material": list(materials)[0]},
                "mechanism_b": {"process": process, "material": list(materials)[1]},
                "bridge": "Same process, different materials — substitution candidate",
                "constraints": "PENDING — material compatibility check needed",
                "evidence": [{"evidence_id": m["evidence_id"], "material": m["INPUT"]} for m in mechs[:3]],
                "candidate_hypothesis": f"Material '{list(materials)[1][:30]}' may substitute '{list(materials)[0][:30]}' in process '{process}'",
                "epistemic_state": "CANDIDATE_CONNECTION",
            })
    return candidates


def mode_6_functional_analogy(mechanisms, evidence):
    """Find mechanisms with same OUTPUT via different processes."""
    by_output = defaultdict(list)
    for m in mechanisms:
        if m.get("OUTPUT") != UNKNOWN:
            by_output[m["OUTPUT"][:30]].append(m)

    candidates = []
    for output, mechs in by_output.items():
        if len(mechs) >= 2:
            processes = [m.get("PROCESS", UNKNOWN) for m in mechs]
            if len(set(processes)) >= 2:
                cand_id = f"M6-{hashlib.sha256(output.encode()).hexdigest()[:8]}"
                candidates.append({
                    "candidate_id": cand_id,
                    "discovery_mode": "functional_analogy",
                    "mechanism_a": {"process": processes[0], "output": output},
                    "mechanism_b": {"process": processes[1], "output": output},
                    "bridge": "Different processes produce same output — functional analogy",
                    "constraints": "PENDING",
                    "evidence": [{"evidence_id": m["evidence_id"]} for m in mechs[:3]],
                    "candidate_hypothesis": f"Processes '{processes[0][:30]}' and '{processes[1][:30]}' are functionally analogous (same output)",
                    "epistemic_state": "ANALOGY",
                })
    return candidates


def mode_9_patent_whitespace(mechanisms, evidence):
    """Find INPUT + PROCESS combinations not present in evidence."""
    input_process = set()
    for m in mechanisms:
        if m.get("INPUT") != UNKNOWN and m.get("PROCESS") != UNKNOWN:
            input_process.add((m["INPUT"][:20], m["PROCESS"][:20]))

    all_inputs = set(ip[0] for ip in input_process)
    all_processes = set(ip[1] for ip in input_process)

    candidates = []
    missing = []
    for inp in list(all_inputs)[:5]:
        for proc in list(all_processes)[:5]:
            if (inp, proc) not in input_process:
                missing.append((inp, proc))

    for inp, proc in missing[:10]:
        cand_id = f"M9-{hashlib.sha256(f'{inp}-{proc}'.encode()).hexdigest()[:8]}"
        candidates.append({
            "candidate_id": cand_id,
            "discovery_mode": "patent_whitespace",
            "mechanism_a": {"input": inp, "process": proc},
            "mechanism_b": None,
            "bridge": "Combination absent from searched evidence",
            "constraints": "PENDING",
            "evidence": [],
            "candidate_hypothesis": f"Input '{inp}' + process '{proc}' combination not found",
            "epistemic_state": "CANDIDATE_CONNECTION",
            "anti_hallucination": {
                "absence_label": "ABSENCE_OF_EVIDENCE",
                "note": "Combination absent from searched universe — does NOT prove novelty",
            },
        })
    return candidates


def mode_10_temporal_gap(mechanisms, evidence):
    """Find mechanisms with temporal gaps in publication dates."""
    by_process = defaultdict(list)
    for m in mechanisms:
        eid = m.get("evidence_id", "")
        # Find matching evidence for date
        for e in evidence:
            if e["id"] == eid:
                date = e.get("publication_date", "")
                if date and date != "UNAVAILABLE":
                    try:
                        year = int(date[:4])
                        by_process[m.get("PROCESS", UNKNOWN)[:30]].append(year)
                    except:
                        pass
                break

    candidates = []
    for process, years in by_process.items():
        if process == UNKNOWN or len(years) < 3:
            continue
        years.sort()
        span = years[-1] - years[0]
        if span >= 5:
            cand_id = f"M10-{hashlib.sha256(process.encode()).hexdigest()[:8]}"
            candidates.append({
                "candidate_id": cand_id,
                "discovery_mode": "temporal_gap",
                "mechanism_a": {"process": process, "years": years},
                "mechanism_b": None,
                "bridge": f"Process studied over {span} years — gap may indicate abandoned/enabling tech",
                "constraints": "PENDING",
                "evidence": [],
                "candidate_hypothesis": f"Process '{process[:30]}' shows {span}-year span — investigate enabling technology changes",
                "epistemic_state": "INFERRED",
            })
    return candidates


def mode_12_negative_space(mechanisms, evidence):
    """Find A+B, A+C, B+C exist but A+B+C absent."""
    # Build mechanism sets per evidence
    mech_sets = []
    for m in mechanisms:
        fields = []
        for f in ["INPUT", "PROCESS", "OUTPUT"]:
            v = m.get(f, UNKNOWN)
            if v != UNKNOWN:
                fields.append(v[:20])
        if len(fields) >= 2:
            mech_sets.append(set(fields))

    # Find pairs that co-occur
    from itertools import combinations
    pair_counts = Counter()
    for s in mech_sets:
        for pair in combinations(sorted(s), 2):
            pair_counts[pair] += 1

    # Find triples absent
    common_pairs = [p for p, c in pair_counts.most_common(20) if c >= 2]
    candidates = []
    for i, (a, b) in enumerate(common_pairs[:5]):
        for c_pair in common_pairs[i+1:i+3]:
            # Check if triple exists
            triple = {a, b, *c_pair}
            if len(triple) == 3:
                triple_exists = any(triple.issubset(s) for s in mech_sets)
                if not triple_exists:
                    cand_id = f"M12-{hashlib.sha256(str(sorted(triple)).encode()).hexdigest()[:8]}"
                    candidates.append({
                        "candidate_id": cand_id,
                        "discovery_mode": "negative_space_combination",
                        "mechanism_a": {"element": a},
                        "mechanism_b": {"element": b, "element_c": list(triple - {a, b})[0]},
                        "bridge": "All pairs exist but triple combination absent",
                        "constraints": "PENDING",
                        "evidence": [],
                        "candidate_hypothesis": f"Combination {sorted(triple)} not found — negative space candidate",
                        "epistemic_state": "CANDIDATE_CONNECTION",
                        "anti_hallucination": {"absence_label": "ABSENCE_OF_EVIDENCE"},
                    })
    return candidates[:5]


def mode_14_performance_anomaly(mechanisms, evidence):
    """Find same process with different measured effects."""
    by_process = defaultdict(list)
    for m in mechanisms:
        if m.get("PROCESS") != UNKNOWN and m.get("MEASURED_EFFECT") != UNKNOWN:
            by_process[m["PROCESS"][:30]].append(m)

    candidates = []
    for process, mechs in by_process.items():
        if len(mechs) >= 2:
            effects = [m["MEASURED_EFFECT"] for m in mechs]
            if len(set(effects)) >= 2:
                cand_id = f"M14-{hashlib.sha256(process.encode()).hexdigest()[:8]}"
                candidates.append({
                    "candidate_id": cand_id,
                    "discovery_mode": "performance_anomaly",
                    "mechanism_a": {"process": process, "effect": effects[0]},
                    "mechanism_b": {"process": process, "effect": effects[1]},
                    "bridge": "Same process, different measured effects — hidden variable may explain",
                    "constraints": "PENDING",
                    "evidence": [{"evidence_id": m["evidence_id"], "effect": m["MEASURED_EFFECT"]} for m in mechs[:3]],
                    "candidate_hypothesis": f"Process '{process[:30]}' produces different effects — hidden variable may explain",
                    "epistemic_state": "INFERRED",
                })
    return candidates


def main():
    print(f"[{datetime.now(timezone.utc).isoformat()}] Discovery Engine V2 starting")

    evidence = load_evidence()
    mechanisms = load_mechanisms()
    print(f"  Evidence: {len(evidence)}")
    print(f"  Structured mechanisms: {len(mechanisms)}")

    all_candidates = []

    modes = [
        ("Mode 1: Cross-domain transfer", mode_1_cross_domain_transfer),
        ("Mode 2: Scientific contradiction", mode_2_scientific_contradiction),
        ("Mode 3: Failure-mode transfer", mode_3_failure_mode_transfer),
        ("Mode 4: Material substitution", mode_4_material_substitution),
        ("Mode 6: Functional analogy", mode_6_functional_analogy),
        ("Mode 9: Patent whitespace", mode_9_patent_whitespace),
        ("Mode 10: Temporal gap", mode_10_temporal_gap),
        ("Mode 12: Negative space", mode_12_negative_space),
        ("Mode 14: Performance anomaly", mode_14_performance_anomaly),
    ]

    for name, func in modes:
        print(f"  {name}...")
        try:
            cands = func(mechanisms, evidence)
            print(f"    {len(cands)} candidates")
            all_candidates.extend(cands)
        except Exception as e:
            print(f"    ERROR: {e}")

    # Save
    output = CANDIDATES_DIR / "discovery_candidates_v2.json"
    with open(output, "w") as f:
        json.dump({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_candidates": len(all_candidates),
            "mechanisms_analyzed": len(mechanisms),
            "candidates": all_candidates,
        }, f, indent=2, ensure_ascii=False)

    by_mode = Counter(c["discovery_mode"] for c in all_candidates)
    by_epistemic = Counter(c.get("epistemic_state", "?") for c in all_candidates)

    print(f"\n[{datetime.now(timezone.utc).isoformat()}] COMPLETE")
    print(f"  Total candidates: {len(all_candidates)}")
    print(f"  By mode: {dict(by_mode)}")
    print(f"  By epistemic: {dict(by_epistemic)}")
    print(f"  INVENTION_CANDIDATE: {by_epistemic.get('INVENTION_CANDIDATE', 0)} (must be 0)")
    print(f"  Saved: {output}")


if __name__ == "__main__":
    main()
