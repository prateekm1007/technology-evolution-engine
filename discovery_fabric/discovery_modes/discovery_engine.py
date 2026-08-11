"""
Discovery Fabric — Discovery Engine.

Implements discovery operators that find cross-domain connections,
contradictions, gaps, and anomalies in the knowledge graph.

Every candidate carries:
- evidence trace (patent_id → abstract → extracted fact)
- epistemic state (OBSERVED → INFERRED → CANDIDATE_CONNECTION → ...)
- prior-art firewall status
- adversarial review checklist
"""
import json
import sys
import hashlib
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

EVIDENCE_FILE = REPO / "discovery_fabric/evidence/evidence.jsonl"
GRAPH_FILE = REPO / "discovery_fabric/knowledge_graph/knowledge_graph.json"
CANDIDATES_DIR = REPO / "discovery_fabric/discovery_candidates"
CANDIDATES_DIR.mkdir(parents=True, exist_ok=True)


def load_evidence():
    evidence = []
    with open(EVIDENCE_FILE) as f:
        for line in f:
            if line.strip():
                evidence.append(json.loads(line))
    return evidence


def load_graph():
    with open(GRAPH_FILE) as f:
        return json.load(f)


def get_text(item):
    """Get combined text from an evidence item."""
    text = ""
    if item.get("title") and item["title"] != "UNAVAILABLE":
        text += item["title"] + " "
    if item.get("abstract") and item["abstract"] != "UNAVAILABLE":
        text += item["abstract"]
    return text.lower()


def mode_1_cross_domain_transfer(evidence, graph):
    """Find mechanisms mature in one domain but absent in another."""
    # Build mechanism → domain matrix
    mech_by_domain = defaultdict(lambda: defaultdict(list))
    for e in evidence:
        text = get_text(e)
        domain = e.get("domain", "unknown")
        for edge in graph["edges"]:
            if edge["type"] == "USES_MECHANISM" and edge["source"] == e["id"]:
                mech = edge["target"]
                mech_by_domain[mech][domain].append(e["id"])

    candidates = []
    mechanisms = list(mech_by_domain.keys())
    domains = sorted(set(e.get("domain", "?") for e in evidence))

    for mech in mechanisms:
        present_domains = set(mech_by_domain[mech].keys())
        absent_domains = set(domains) - present_domains
        if not absent_domains or len(present_domains) < 2:
            continue

        # Find source papers (domain with most occurrences)
        source_domain = max(present_domains, key=lambda d: len(mech_by_domain[mech][d]))
        source_papers = mech_by_domain[mech][source_domain][:5]

        for target_domain in list(absent_domains)[:3]:
            cand_id = f"CDM1-{hashlib.sha256(f'{mech}-{source_domain}-{target_domain}'.encode()).hexdigest()[:8]}"
            candidates.append({
                "candidate_id": cand_id,
                "discovery_type": "CROSS_DOMAIN_TRANSFER",
                "mode": 1,
                "mechanism": mech,
                "source_domain": source_domain,
                "target_domain": target_domain,
                "source_evidence": source_papers,
                "epistemic_state": "CANDIDATE_CONNECTION",
                "cross_domain_bridge": "NOT_YET_ESTABLISHED — requires mechanistic bridge analysis",
                "hypothesis": f"Mechanism '{mech}' from {source_domain} may transfer to {target_domain}",
                "prediction": "PENDING — requires mechanistic bridge",
                "falsifier": "PENDING",
                "confidence": {
                    "evidence_strength": min(len(source_papers) * 15, 80),
                    "cross_domain_transferability": 50,
                    "prior_art_distance": 0,
                    "uncertainty": 90,
                },
                "novelty_status": "UNVERIFIED",
                "prior_art_firewall": "PENDING",
                "adversarial_review": "PENDING",
                "anti_hallucination": {
                    "absence_label": "ABSENCE_OF_EVIDENCE",
                    "absence_note": f"Mechanism not found in {target_domain} evidence — may be due to search coverage, not true absence",
                    "search_universe": f"{len(evidence)} evidence objects from {len(domains)} domains",
                },
            })

    return candidates


def mode_3_functional_analogy(evidence, graph):
    """Find materials used in different domains — potential functional analogy."""
    material_by_domain = defaultdict(lambda: defaultdict(list))
    for e in evidence:
        domain = e.get("domain", "unknown")
        for edge in graph["edges"]:
            if edge["type"] == "USES_MATERIAL" and edge["source"] == e["id"]:
                mat = edge["target"]
                material_by_domain[mat][domain].append(e["id"])

    candidates = []
    for mat, domains in material_by_domain.items():
        if len(domains) >= 3:
            domain_list = list(domains.keys())
            source_papers = []
            for d in domain_list[:3]:
                source_papers.extend(domains[d][:2])

            cand_id = f"CDM3-{hashlib.sha256(f'{mat}-analogy'.encode()).hexdigest()[:8]}"
            candidates.append({
                "candidate_id": cand_id,
                "discovery_type": "FUNCTIONAL_ANALOGY",
                "mode": 3,
                "material": mat,
                "domains_present": domain_list,
                "source_evidence": source_papers[:8],
                "epistemic_state": "ANALOGY",
                "hypothesis": f"Material '{mat}' appears across {len(domain_list)} domains — functional analogy may exist",
                "confidence": {
                    "evidence_strength": min(len(source_papers) * 10, 70),
                    "uncertainty": 85,
                },
                "novelty_status": "UNVERIFIED",
                "prior_art_firewall": "PENDING",
                "adversarial_review": "PENDING",
                "anti_hallucination": {
                    "note": "Presence across domains does not prove transferability — requires mechanistic bridge",
                },
            })

    return candidates


def mode_10_patent_whitespace(evidence, graph):
    """Find negative space — mechanisms + materials combinations that don't appear together."""
    # Build mechanism → materials co-occurrence
    mech_materials = defaultdict(set)
    for e in evidence:
        text = get_text(e)
        eid = e["id"]
        mechs = set()
        mats = set()
        for edge in graph["edges"]:
            if edge["source"] == eid:
                if edge["type"] == "USES_MECHANISM":
                    mechs.add(edge["target"])
                elif edge["type"] == "USES_MATERIAL":
                    mats.add(edge["target"])
        for m in mechs:
            mech_materials[m].update(mats)

    # Find mechanisms that don't use certain materials
    all_materials = set()
    for mats in mech_materials.values():
        all_materials.update(mats)

    candidates = []
    for mech, used_materials in mech_materials.items():
        unused = all_materials - used_materials
        # Only flag if the mechanism uses at least 3 materials (mature) and misses notable ones
        if len(used_materials) >= 3 and len(unused) > 0:
            # Pick top 2 unused materials that are well-represented overall
            material_freq = Counter()
            for mats in mech_materials.values():
                material_freq.update(mats)
            notable_unused = [m for m, _ in material_freq.most_common(20) if m in unused][:2]

            for mat in notable_unused:
                cand_id = f"CDM10-{hashlib.sha256(f'{mech}-{mat}-gap'.encode()).hexdigest()[:8]}"
                candidates.append({
                    "candidate_id": cand_id,
                    "discovery_type": "PATENT_WHITESPACE",
                    "mode": 10,
                    "mechanism": mech,
                    "material_not_combined": mat,
                    "epistemic_state": "CANDIDATE_CONNECTION",
                    "hypothesis": f"Mechanism '{mech}' has not been combined with material '{mat}' in the searched evidence",
                    "confidence": {
                        "evidence_strength": 20,
                        "prior_art_distance": 50,
                        "uncertainty": 95,
                    },
                    "novelty_status": "UNVERIFIED_ABSENCE",
                    "prior_art_firewall": "PENDING",
                    "adversarial_review": "PENDING",
                    "anti_hallucination": {
                        "absence_label": "ABSENCE_OF_EVIDENCE",
                        "absence_note": f"Combination not found in {len(evidence)} evidence objects — does NOT prove novelty",
                        "search_universe": f"{len(evidence)} evidence objects, {len(graph['edges'])} graph edges",
                        "limitations": ["Keyword-based extraction may miss synonymous descriptions", "Coverage limited to 4 sources"],
                    },
                })

    return candidates[:20]  # limit


def mode_14_temporal_gap(evidence, graph):
    """Find technologies with temporal gaps — old idea + recent resurgence."""
    # Group by mechanism, find date ranges
    mech_dates = defaultdict(list)
    for e in evidence:
        date_str = e.get("publication_date", "")
        if date_str and date_str != "UNAVAILABLE":
            try:
                year = int(date_str[:4])
                for edge in graph["edges"]:
                    if edge["type"] == "USES_MECHANISM" and edge["source"] == e["id"]:
                        mech_dates[edge["target"]].append(year)
            except (ValueError, TypeError):
                pass

    candidates = []
    for mech, years in mech_dates.items():
        if len(years) < 5:
            continue
        years.sort()
        earliest = years[0]
        latest = years[-1]
        span = latest - earliest
        if span >= 10:  # at least 10 year span
            # Check for gap
            gaps = []
            for i in range(1, len(years)):
                gap = years[i] - years[i-1]
                if gap >= 5:
                    gaps.append((years[i-1], years[i], gap))
            if gaps:
                biggest_gap = max(gaps, key=lambda x: x[2])
                cand_id = f"CDM14-{hashlib.sha256(f'{mech}-temporal'.encode()).hexdigest()[:8]}"
                candidates.append({
                    "candidate_id": cand_id,
                    "discovery_type": "TEMPORAL_GAP",
                    "mode": 14,
                    "mechanism": mech,
                    "earliest_year": earliest,
                    "latest_year": latest,
                    "biggest_gap": {"from": biggest_gap[0], "to": biggest_gap[1], "years": biggest_gap[2]},
                    "total_papers": len(years),
                    "epistemic_state": "INFERRED",
                    "hypothesis": f"Mechanism '{mech}' shows a {biggest_gap[2]}-year gap ({biggest_gap[0]}–{biggest_gap[1]}) — enabling technology may have changed",
                    "confidence": {
                        "evidence_strength": min(len(years) * 5, 60),
                        "uncertainty": 80,
                    },
                    "novelty_status": "UNVERIFIED",
                    "prior_art_firewall": "PENDING",
                    "adversarial_review": "PENDING",
                })

    return candidates


def run_prior_art_firewall(candidates, evidence):
    """Run prior-art firewall on each candidate."""
    for cand in candidates:
        mech = cand.get("mechanism", "")
        if not mech:
            cand["prior_art_firewall"] = "SKIPPED"
            continue

        # Count how many evidence items mention this mechanism
        matches = 0
        for e in evidence:
            text = get_text(e)
            if mech.replace("_", " ") in text:
                matches += 1

        if matches > 20:
            cand["prior_art_firewall"] = "ADJACENT_PRIOR_ART"
            cand["prior_art_match_count"] = matches
        elif matches > 0:
            cand["prior_art_firewall"] = "ADJACENT_PRIOR_ART"
            cand["prior_art_match_count"] = matches
        else:
            cand["prior_art_firewall"] = "UNVERIFIED_ABSENCE"
            cand["prior_art_match_count"] = 0

    return candidates


def run_adversarial_review(candidates):
    """Run adversarial review checklist on each candidate."""
    for cand in candidates:
        cand["adversarial_review"] = {
            "is_mechanism_transferable": "UNASSESSED",
            "is_analogy_superficial": "UNASSESSED",
            "is_effect_already_known": "UNASSESSED",
            "hidden_prior_art": "UNASSESSED",
            "physical_constraint_prevents_transfer": "UNASSESSED",
            "is_effect_correlation_not_causation": "UNASSESSED",
            "alternative_explanation": "UNASSESSED",
            "can_be_falsified": "UNASSESSED",
            "killing_experiment": "PENDING",
        }
        # Honest assessment
        cand["adversarial_review"]["is_analogy_superficial"] = "LIKELY — keyword-based extraction does not establish mechanistic bridge"
        cand["adversarial_review"]["hidden_prior_art"] = "UNASSESSED — requires full-text patent search"
        cand["adversarial_review"]["can_be_falsified"] = "PENDING — requires falsifiable prediction first"
    return candidates


def main():
    print(f"[{datetime.now(timezone.utc).isoformat()}] Discovery engine starting")

    evidence = load_evidence()
    graph = load_graph()
    print(f"  Evidence: {len(evidence)} items")
    print(f"  Graph edges: {len(graph['edges'])}")

    all_candidates = []

    # Mode 1: Cross-domain transfer
    print("  Mode 1: Cross-domain transfer...")
    c1 = mode_1_cross_domain_transfer(evidence, graph)
    print(f"    {len(c1)} candidates")
    all_candidates.extend(c1)

    # Mode 3: Functional analogy
    print("  Mode 3: Functional analogy...")
    c3 = mode_3_functional_analogy(evidence, graph)
    print(f"    {len(c3)} candidates")
    all_candidates.extend(c3)

    # Mode 10: Patent whitespace
    print("  Mode 10: Patent whitespace...")
    c10 = mode_10_patent_whitespace(evidence, graph)
    print(f"    {len(c10)} candidates")
    all_candidates.extend(c10)

    # Mode 14: Temporal gap
    print("  Mode 14: Temporal gap...")
    c14 = mode_14_temporal_gap(evidence, graph)
    print(f"    {len(c14)} candidates")
    all_candidates.extend(c14)

    # Prior-art firewall
    print("  Running prior-art firewall...")
    all_candidates = run_prior_art_firewall(all_candidates, evidence)

    # Adversarial review
    print("  Running adversarial review...")
    all_candidates = run_adversarial_review(all_candidates)

    # Save
    output = CANDIDATES_DIR / "discovery_candidates.json"
    with open(output, "w") as f:
        json.dump({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_candidates": len(all_candidates),
            "candidates": all_candidates,
        }, f, indent=2, ensure_ascii=False)

    # Summary
    by_type = Counter(c["discovery_type"] for c in all_candidates)
    by_firewall = Counter(c.get("prior_art_firewall", "?") for c in all_candidates)
    by_epistemic = Counter(c.get("epistemic_state", "?") for c in all_candidates)

    print(f"\n[{datetime.now(timezone.utc).isoformat()}] DISCOVERY COMPLETE")
    print(f"  Total candidates: {len(all_candidates)}")
    print(f"  By type: {dict(by_type)}")
    print(f"  By firewall: {dict(by_firewall)}")
    print(f"  By epistemic state: {dict(by_epistemic)}")
    print(f"  Saved: {output}")

    # NO candidate labeled INVENTION_CANDIDATE (per protocol)
    invention_count = sum(1 for c in all_candidates if c.get("epistemic_state") == "INVENTION_CANDIDATE")
    print(f"  INVENTION_CANDIDATE count: {invention_count} (must be 0 at this stage)")

    return all_candidates


if __name__ == "__main__":
    main()
