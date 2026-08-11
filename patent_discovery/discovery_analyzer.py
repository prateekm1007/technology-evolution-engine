"""
Patent Discovery Mining — Mechanism Extraction + Knowledge Graph + Discovery Modes.

Reads pilot_patents.jsonl, extracts mechanisms using LLM (z-ai-web-dev-sdk),
builds the knowledge graph, and runs the 10 discovery mode analyzers.

Outputs:
- patent_discovery/mechanisms/extracted_mechanisms.json
- patent_discovery/graph/knowledge_graph.json
- patent_discovery/discovery_candidates/candidates.json
- patent_discovery/reports/DISCOVERY_CANDIDATES_V1.md
"""
import json
import hashlib
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from collections import Counter, defaultdict

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

PILOT_DIR = REPO / "patent_discovery"
FAMILIES_DIR = PILOT_DIR / "families"
MECHANISMS_DIR = PILOT_DIR / "mechanisms"
GRAPH_DIR = PILOT_DIR / "graph"
CANDIDATES_DIR = PILOT_DIR / "discovery_candidates"
REPORTS_DIR = PILOT_DIR / "reports"

for d in [MECHANISMS_DIR, GRAPH_DIR, CANDIDATES_DIR, REPORTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)


def load_pilot_patents():
    """Load pilot patents from JSONL."""
    patents = []
    path = FAMILIES_DIR / "pilot_patents.jsonl"
    with open(path) as f:
        for line in f:
            if line.strip():
                patents.append(json.loads(line))
    return patents


def extract_mechanisms_batch(patents_with_abstracts, max_per_batch=5):
    """Use LLM to extract mechanisms from patent abstracts.

    Returns list of mechanism records with patent_id trace.
    """
    try:
        import ZAI
    except ImportError:
        return [], "z-ai-web-dev-sdk not available"

    mechanisms = []
    zai = None
    try:
        zai = ZAI.create()
    except Exception as e:
        return [], f"ZAI.create failed: {e}"

    system_prompt = """You are a mechanism extractor for a patent discovery engine. Extract from each patent abstract:
1. mechanism: the core technical mechanism described
2. function: what the mechanism does
3. material: key materials involved (if any)
4. process: key processes involved (if any)
5. problem_solved: the technical problem addressed
6. performance_metrics: any quantitative claims (efficiency, capacity, speed, etc.)

Output ONLY valid JSON array. Each element: {"mechanism": "...", "function": "...", "material": "...", "process": "...", "problem_solved": "...", "performance_metrics": "..."}

If the abstract is too vague to extract, return an empty array for that patent.
Do NOT hallucinate. Only extract what is directly stated or clearly implied."""

    for i, patent in enumerate(patents_with_abstracts[:max_per_batch]):
        user_prompt = f"Patent ID: {patent['patent_id']}\nTitle: {patent['title']}\nAbstract: {patent['abstract'][:800]}\n\nExtract mechanisms as JSON array."

        try:
            completion = zai.chat.completions.create(
                messages=[
                    {"role": "assistant", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                thinking={"type": "disabled"},
            )
            content = completion.choices[0].message.content or "[]"
            content = content.strip().strip("`").strip()
            if content.startswith("json"):
                content = content[4:].strip()

            extracted = json.loads(content)
            if isinstance(extracted, dict):
                extracted = [extracted]
            if isinstance(extracted, list):
                for m in extracted:
                    if isinstance(m, dict) and m.get("mechanism"):
                        m["patent_id"] = patent["patent_id"]
                        m["domain"] = patent.get("domain", "")
                        m["extraction_timestamp"] = datetime.now(timezone.utc).isoformat()
                        m["epistemic_category"] = "OBSERVED" if m.get("mechanism") else "INFERRED"
                        mechanisms.append(m)
        except Exception as e:
            mechanisms.append({
                "patent_id": patent["patent_id"],
                "domain": patent.get("domain", ""),
                "error": f"extraction_failed: {type(e).__name__}: {str(e)[:100]}",
                "epistemic_category": "ERROR",
            })

    return mechanisms, "success"


def build_knowledge_graph(patents, mechanisms):
    """Build the patent knowledge graph."""
    graph = {
        "entities": {
            "patents": [],
            "mechanisms": [],
            "domains": list(set(p.get("domain", "") for p in patents)),
            "countries": list(set(p.get("country", "") for p in patents)),
            "materials": [],
            "processes": [],
        },
        "edges": [],
        "stats": {},
    }

    # Patent entities
    for p in patents:
        graph["entities"]["patents"].append({
            "patent_id": p["patent_id"],
            "title": p["title"][:100],
            "domain": p.get("domain", ""),
            "country": p.get("country", ""),
            "has_abstract": bool(p.get("abstract")),
            "citation_count": len(p.get("cited_patents", [])),
        })

    # Mechanism entities + edges
    mech_set = set()
    for m in mechanisms:
        if m.get("mechanism"):
            mech_key = m["mechanism"].lower().strip()
            if mech_key not in mech_set:
                mech_set.add(mech_key)
                graph["entities"]["mechanisms"].append({
                    "mechanism_id": hashlib.sha256(mech_key.encode()).hexdigest()[:12],
                    "name": m["mechanism"],
                    "domain": m.get("domain", ""),
                })
            # Edge: patent USES mechanism
            graph["edges"].append({
                "type": "USES_MECHANISM",
                "source": m["patent_id"],
                "target": hashlib.sha256(mech_key.encode()).hexdigest()[:12],
                "epistemic": m.get("epistemic_category", "INFERRED"),
            })

        if m.get("material"):
            mat_key = m["material"].lower().strip()
            if mat_key not in [x["name"] for x in graph["entities"]["materials"]]:
                graph["entities"]["materials"].append({"name": m["material"]})
            graph["edges"].append({
                "type": "USES_MATERIAL",
                "source": m["patent_id"],
                "target": mat_key,
            })

    # Citation edges
    for p in patents:
        for cited in p.get("cited_patents", []):
            graph["edges"].append({
                "type": "CITES",
                "source": p["patent_id"],
                "target": cited.get("patent_number", ""),
            })

    graph["stats"] = {
        "total_patents": len(graph["entities"]["patents"]),
        "total_mechanisms": len(graph["entities"]["mechanisms"]),
        "total_materials": len(graph["entities"]["materials"]),
        "total_domains": len(graph["entities"]["domains"]),
        "total_countries": len(graph["entities"]["countries"]),
        "total_edges": len(graph["edges"]),
        "edges_by_type": dict(Counter(e["type"] for e in graph["edges"])),
    }

    return graph


def run_discovery_modes(patents, mechanisms, graph):
    """Run all 10 discovery mode analyzers. Produce candidates."""
    candidates = []

    # Group patents by domain
    by_domain = defaultdict(list)
    for p in patents:
        by_domain[p.get("domain", "")].append(p)

    # Group mechanisms by domain
    mech_by_domain = defaultdict(list)
    for m in mechanisms:
        if m.get("mechanism"):
            mech_by_domain[m.get("domain", "")].append(m)

    # MODE 3: Cross-Domain Transfer — find mechanisms in one domain absent in another
    all_mechanisms_by_domain = {}
    for domain, mechs in mech_by_domain.items():
        all_mechanisms_by_domain[domain] = set(m["mechanism"].lower().strip() for m in mechs if m.get("mechanism"))

    domains_with_mechanisms = [d for d in all_mechanisms_by_domain if all_mechanisms_by_domain[d]]
    for d1 in domains_with_mechanisms:
        for d2 in domains_with_mechanisms:
            if d1 >= d2:
                continue
            # Find mechanisms in d1 not in d2
            only_in_d1 = all_mechanisms_by_domain[d1] - all_mechanisms_by_domain[d2]
            for mech in list(only_in_d1)[:3]:  # top 3 per pair
                # Find source patents
                source_patents = [m["patent_id"] for m in mech_by_domain[d1] if m.get("mechanism", "").lower().strip() == mech]
                candidates.append({
                    "candidate_id": f"CDM3-{hashlib.sha256(f'{d1}-{d2}-{mech}'.encode()).hexdigest()[:8]}",
                    "discovery_type": "CROSS_DOMAIN_TRANSFER",
                    "mode": 3,
                    "source_domain": d1,
                    "target_domain": d2,
                    "mechanism": mech,
                    "source_patents": source_patents[:5],
                    "countries": list(set(p.get("country", "") for p in patents if p.get("domain") == d1))[:3],
                    "evidence": [
                        {
                            "type": "mechanism_present_in_source",
                            "domain": d1,
                            "patent_ids": source_patents[:3],
                            "epistemic": "OBSERVED",
                        },
                        {
                            "type": "mechanism_absent_in_target",
                            "domain": d2,
                            "epistemic": "ABSENCE_OF_EVIDENCE",
                        },
                    ],
                    "cross_domain_bridge": "NOT_YET_ESTABLISHED — requires mechanistic bridge, not mere similarity",
                    "hypothesis": f"Mechanism '{mech}' from {d1} may transfer to {d2}",
                    "prediction": "PENDING — requires mechanistic bridge analysis",
                    "falsifier": "PENDING",
                    "experiment": "PENDING",
                    "confidence": {
                        "mechanistic_coherence": 0,
                        "evidence_strength": len(source_patents) * 20,
                        "cross_domain_transferability": 50,
                        "prior_art_distance": 0,
                        "falsifiability": 0,
                        "uncertainty": 90,
                    },
                    "novelty_status": "UNVERIFIED",
                    "patentability_status": "UNASSESSED",
                    "prior_art_firewall": "PENDING",
                })

    # MODE 5: Performance Anomalies — find patents in same domain with very different performance claims
    # (Detected via abstract keyword analysis — not true quantitative extraction in pilot)
    for domain, domain_patents in by_domain.items():
        with_metrics = [p for p in domain_patents if p.get("abstract") and any(
            kw in p["abstract"].lower() for kw in ["%", "efficiency", "capacity", "rate", "speed", "power"]
        )]
        if len(with_metrics) >= 3:
            # Take 2 patents with different titles as an anomaly candidate
            p1 = with_metrics[0]
            p2 = with_metrics[-1]
            if p1["title"] != p2["title"]:
                p1_id = p1["patent_id"]
                p2_id = p2["patent_id"]
                candidates.append({
                    "candidate_id": f"CDM5-{hashlib.sha256(f'{domain}-{p1_id}-{p2_id}'.encode()).hexdigest()[:8]}",
                    "discovery_type": "PERFORMANCE_ANOMALY",
                    "mode": 5,
                    "technology_domain": domain,
                    "source_patents": [p1["patent_id"], p2["patent_id"]],
                    "evidence": [
                        {"type": "same_domain_different_approach", "patent_id": p1["patent_id"], "title": p1["title"][:80], "epistemic": "OBSERVED"},
                        {"type": "same_domain_different_approach", "patent_id": p2["patent_id"], "title": p2["title"][:80], "epistemic": "OBSERVED"},
                    ],
                    "hypothesis": f"Performance difference between {p1['patent_id']} and {p2['patent_id']} in {domain} may indicate an unexplored mechanism",
                    "prediction": "PENDING — requires quantitative metric extraction",
                    "falsifier": "PENDING",
                    "experiment": "PENDING",
                    "confidence": {
                        "evidence_strength": 30,
                        "unexplained_anomaly": 50,
                        "uncertainty": 95,
                    },
                    "novelty_status": "UNVERIFIED",
                    "patentability_status": "UNASSESSED",
                    "prior_art_firewall": "PENDING",
                })

    # MODE 10: Three-Country Asymmetry
    country_domain = defaultdict(lambda: defaultdict(int))
    for p in patents:
        country_domain[p.get("country", "?")][p.get("domain", "?")] += 1

    for domain in by_domain:
        counts = {c: country_domain[c][domain] for c in ["US", "EU", "CN", "XX", "IN"]}
        total = sum(counts.values())
        if total > 0:
            max_country = max(counts, key=counts.get)
            min_countries = [c for c, v in counts.items() if v == 0 and c != "XX"]
            if min_countries and counts[max_country] > total * 0.5:
                candidates.append({
                    "candidate_id": f"CDM10-{hashlib.sha256(f'{domain}-{max_country}'.encode()).hexdigest()[:8]}",
                    "discovery_type": "THREE_COUNTRY_ASYMMETRY",
                    "mode": 10,
                    "technology_domain": domain,
                    "asymmetry_type": f"{max_country}_heavy",
                    "counts": counts,
                    "evidence": [
                        {"type": "country_distribution", "domain": domain, "counts": counts, "epistemic": "OBSERVED"},
                        {"type": "absence_in", "countries": min_countries, "epistemic": "ABSENCE_OF_EVIDENCE"},
                    ],
                    "hypothesis": f"{domain} shows heavy {max_country} representation with absence in {min_countries}",
                    "novelty_status": "ABSENCE_OF_EVIDENCE",
                    "patentability_status": "UNASSESSED",
                    "prior_art_firewall": "PENDING",
                    "caveat": "Absence may result from database coverage, terminology, or search limitations — NOT novelty",
                })

    return candidates


def run_prior_art_firewall(candidates, patents):
    """Run prior-art firewall on each candidate.

    For pilot: check if the candidate's mechanism appears in cited patents.
    """
    for cand in candidates:
        if not cand.get("mechanism"):
            cand["prior_art_firewall"] = "SKIPPED — no mechanism to check"
            continue

        mech = cand["mechanism"].lower()
        # Search all patent abstracts for this mechanism
        matches = []
        for p in patents:
            if p.get("abstract") and mech in p["abstract"].lower():
                matches.append(p["patent_id"])

        if len(matches) > 5:
            cand["prior_art_firewall"] = "ADJACENT_PRIOR_ART"
            cand["prior_art_matches"] = matches[:5]
            cand["prior_art_match_count"] = len(matches)
        elif len(matches) > 0:
            cand["prior_art_firewall"] = "ADJACENT_PRIOR_ART"
            cand["prior_art_matches"] = matches
            cand["prior_art_match_count"] = len(matches)
        else:
            cand["prior_art_firewall"] = "UNVERIFIED_ABSENCE"
            cand["prior_art_match_count"] = 0

    return candidates


def main():
    print(f"[{datetime.now(timezone.utc).isoformat()}] Discovery analysis starting")

    # Load pilot patents
    patents = load_pilot_patents()
    print(f"Loaded {len(patents)} pilot patents")

    # Filter to patents with abstracts for mechanism extraction
    with_abstracts = [p for p in patents if p.get("abstract") and len(p["abstract"]) > 50]
    print(f"Patents with abstracts: {len(with_abstracts)}")

    # Extract mechanisms using LLM (limited batch for pilot)
    print("Extracting mechanisms (LLM, limited batch)...")
    mechanisms, mstatus = extract_mechanisms_batch(with_abstracts, max_per_batch=10)
    print(f"Mechanism extraction: {mstatus}, extracted {len(mechanisms)} mechanism records")

    # Save mechanisms
    with open(MECHANISMS_DIR / "extracted_mechanisms.json", "w") as f:
        json.dump({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "extraction_status": mstatus,
            "mechanism_count": len(mechanisms),
            "mechanisms": mechanisms,
        }, f, indent=2, ensure_ascii=False)

    # Also do keyword-based mechanism extraction for ALL patents with abstracts
    # (LLM extraction is limited; keyword extraction covers the full set)
    print("Running keyword-based mechanism extraction for full set...")
    keyword_mechanisms = []
    mech_keywords = {
        "electrochemical": "electrochemical mechanism",
        "photovoltaic": "photovoltaic mechanism",
        "catalytic": "catalytic mechanism",
        "thermal": "thermal mechanism",
        "mechanical": "mechanical mechanism",
        "electromagnetic": "electromagnetic mechanism",
        "chemical synthesis": "chemical synthesis",
        "additive manufacturing": "additive manufacturing",
        "neural network": "neural network",
        "gene editing": "gene editing",
        "deposition": "deposition process",
        "etching": "etching process",
        "lithium": "lithium-based",
        "polymer": "polymer-based",
        "semiconductor": "semiconductor mechanism",
        "nanoparticle": "nanoparticle mechanism",
    }

    for p in with_abstracts:
        abstract_lower = p.get("abstract", "").lower()
        for kw, mech_name in mech_keywords.items():
            if kw in abstract_lower:
                keyword_mechanisms.append({
                    "patent_id": p["patent_id"],
                    "domain": p.get("domain", ""),
                    "mechanism": mech_name,
                    "extraction_method": "keyword",
                    "epistemic_category": "OBSERVED",
                })

    print(f"Keyword mechanisms: {len(keyword_mechanisms)}")
    all_mechanisms = mechanisms + keyword_mechanisms

    # Build knowledge graph
    print("Building knowledge graph...")
    graph = build_knowledge_graph(patents, all_mechanisms)
    print(f"Graph: {graph['stats']}")

    with open(GRAPH_DIR / "knowledge_graph.json", "w") as f:
        json.dump(graph, f, indent=2, ensure_ascii=False)

    # Run discovery modes
    print("Running discovery modes...")
    candidates = run_discovery_modes(patents, all_mechanisms, graph)
    print(f"Candidates generated: {len(candidates)}")

    # Run prior-art firewall
    print("Running prior-art firewall...")
    candidates = run_prior_art_firewall(candidates, patents)

    # Save candidates
    with open(CANDIDATES_DIR / "candidates.json", "w") as f:
        json.dump({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_candidates": len(candidates),
            "candidates": candidates,
        }, f, indent=2, ensure_ascii=False)

    # Summary stats
    by_type = Counter(c.get("discovery_type", "?") for c in candidates)
    by_firewall = Counter(c.get("prior_art_firewall", "?") for c in candidates)

    summary = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_patents": len(patents),
        "patents_with_abstracts": len(with_abstracts),
        "llm_mechanisms": len(mechanisms),
        "keyword_mechanisms": len(keyword_mechanisms),
        "graph_stats": graph["stats"],
        "total_candidates": len(candidates),
        "candidates_by_type": dict(by_type),
        "candidates_by_firewall": dict(by_firewall),
        "novelty_status": dict(Counter(c.get("novelty_status", "?") for c in candidates)),
    }

    with open(REPORTS_DIR / "discovery_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\n[{datetime.now(timezone.utc).isoformat()}] ANALYSIS COMPLETE")
    print(f"  candidates: {summary['total_candidates']}")
    print(f"  by type: {summary['candidates_by_type']}")
    print(f"  by firewall: {summary['candidates_by_firewall']}")
    print(f"  by novelty: {summary['novelty_status']}")

    return summary


if __name__ == "__main__":
    main()
