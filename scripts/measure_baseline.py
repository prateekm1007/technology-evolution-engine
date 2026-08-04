#!/usr/bin/env python3
"""
measure_baseline.py — DR-24: Measure before building.

Per External Auditor cycle 53 roadmap (Phase 0):
  "Run causal_density() against the real data/civilization_graph.json
   and persist the result (verified/asserted/associative/contradicted
   counts) in the ledger, refreshed on every discovery-loop run."

  "Baseline every category with a number, not a vibe: current bridge
   count from SwansonBridgeSearch, current contradiction count from
   Altshuller, current chain count from Gentner — all on the full
   graph, not test fixtures."

  Exit criterion: a benchmarks/reports/baseline_YYYYMMDD.json with a
  real number for every row in the scoring table. No roadmap item
  below is allowed to claim progress without a before/after diff
  against this file.

This script produces that baseline file. It runs all metrics against
the real corpus (not test fixtures) and writes a JSON file with every
number. Future cycles diff against this file to prove progress.

Per ANTI_ENTROPY.md "Don't reward agreement with priors": the numbers
here are what they are. If causal_density is 0.0, that's the truth.
A category can't hit 9 by hiding a bad ratio; it hits 9 by having
the ratio be good AND measured.
"""
import sys
import pathlib
import json
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from invention_compiler.edge_extractor import EdgeExtractor
from invention_compiler.discovery_graph import (
    SwansonBridgeSearch, GentnerStructureMapping, AltshullerContradictionSearch,
)


def measure_baseline() -> dict:
    """Run all metrics against the real corpus. Return a baseline dict.

    This is the Phase 0 exit criterion: a real number for every row.
    """
    extractor = EdgeExtractor()
    papers = extractor.extract_from_corpus(
        str(ROOT / "data" / "ingestion" / "papers"), use_discovery_graph=False
    )
    patents = extractor.extract_from_corpus(
        str(ROOT / "data" / "ingestion" / "patents"), use_discovery_graph=False
    )
    rc_dir = ROOT / "data" / "ingestion" / "radiative_cooling"
    rc = extractor.extract_from_corpus(str(rc_dir), use_discovery_graph=False) if rc_dir.exists() else type(papers)()

    combined = type(papers)()
    for src in (papers, patents, rc):
        for nid, node in src.nodes.items():
            if nid not in combined.nodes:
                combined.add_node(node)
            else:
                existing = combined.nodes[nid]
                existing.what_does_this_change = list(
                    set(existing.what_does_this_change + node.what_does_this_change)
                )
                existing.evidence = list(set(existing.evidence + node.evidence))
        for edge in src.edges:
            exists = any(
                e.source == edge.source and e.target == edge.target
                and e.mechanism == edge.mechanism for e in combined.edges
            )
            if not exists:
                combined.add_edge(edge)

    dg = combined.to_discovery_graph()

    # Causal density + tier counts (DR-24 core)
    tier_counts = combined.tier_counts()
    causal_density = combined.causal_density()

    # Swanson bridges
    bridges = SwansonBridgeSearch.search(dg)

    # Gentner analogies
    analogies = GentnerStructureMapping.find_analogous_chains(dg, min_chain_length=2)

    # Altshuller contradictions
    contradictions = AltshullerContradictionSearch.find_contradictions(dg)

    # BACON: run on real Stefan-Boltzmann data
    bacon_r2 = None
    try:
        from invention_compiler.bacon_engine import discover_law, stefan_boltzmann_dataset
        sb = stefan_boltzmann_dataset(n_points=15)
        law = discover_law(sb["T_surface_K"], sb["Q_W"])
        bacon_r2 = law.r2 if law else None
    except Exception:
        pass

    # Cross-validation generalization
    cv_gap = None
    try:
        from invention_compiler.bacon_engine import cross_validate_law, pcm_latent_heat_dataset
        pcm = pcm_latent_heat_dataset(n_points=10)
        cv = cross_validate_law(pcm["Q_daily_W"], pcm["m_pcm_kg"])
        cv_gap = cv.generalization_gap if cv else None
    except Exception:
        pass

    # Node type distribution
    from collections import Counter
    node_types = dict(Counter(n.node_type for n in dg.nodes.values()))

    baseline = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "graph": {
            "total_nodes": len(dg.nodes),
            "total_edges": len(combined.edges),
            "node_types": node_types,
            "tier_counts": tier_counts,
            "causal_density": causal_density,
        },
        "swanson": {
            "total_bridges": len(bridges),
            "score_min": min((b.get("score", 0) for b in bridges), default=0),
            "score_max": max((b.get("score", 0) for b in bridges), default=0),
            "score_is_constant": len(set(b.get("score", 0) for b in bridges)) <= 1,
        },
        "gentner": {
            "total_analogies": len(analogies),
            "systematicity_min": min((a.get("systematicity", 0) for a in analogies), default=0),
            "systematicity_max": max((a.get("systematicity", 0) for a in analogies), default=0),
            "systematicity_is_constant": len(set(a.get("systematicity", 0) for a in analogies)) <= 1,
        },
        "altshuller": {
            "total_contradictions": len(contradictions),
        },
        "bacon": {
            "stefan_boltzmann_r2": bacon_r2,
            "pcm_cv_gap": cv_gap,
        },
        "corpus": {
            "papers": len(list((ROOT / "data" / "ingestion" / "papers").glob("*.txt"))),
            "patents": len(list((ROOT / "data" / "ingestion" / "patents").glob("*.txt"))),
            "radiative_cooling": len(list((ROOT / "data" / "ingestion" / "radiative_cooling").glob("*.txt"))),
        },
    }
    return baseline


def main():
    baseline = measure_baseline()

    # Write baseline file
    reports_dir = ROOT / "benchmarks" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    baseline_path = reports_dir / f"baseline_{today}.json"
    baseline_path.write_text(json.dumps(baseline, indent=2, default=str), encoding="utf-8")

    print(f"Baseline written: {baseline_path.relative_to(ROOT)}")
    print()
    print("=" * 60)
    print("PHASE 0 BASELINE — DR-24")
    print("=" * 60)
    print(f"Graph: {baseline['graph']['total_nodes']} nodes, {baseline['graph']['total_edges']} edges")
    print(f"Tier counts: {baseline['graph']['tier_counts']}")
    print(f"Causal density: {baseline['graph']['causal_density']:.4f}")
    print(f"  (verified / total = {baseline['graph']['tier_counts'].get('verified', 0)} / {baseline['graph']['total_edges']})")
    print()
    print(f"Swanson bridges: {baseline['swanson']['total_bridges']}")
    print(f"  score is constant: {baseline['swanson']['score_is_constant']} ( Auditor Phase 1 bug)")
    print(f"  score range: [{baseline['swanson']['score_min']}, {baseline['swanson']['score_max']}]")
    print()
    print(f"Gentner analogies: {baseline['gentner']['total_analogies']}")
    print(f"  systematicity is constant: {baseline['gentner']['systematicity_is_constant']} (Auditor Phase 1 bug)")
    print(f"  systematicity range: [{baseline['gentner']['systematicity_min']}, {baseline['gentner']['systematicity_max']}]")
    print()
    print(f"Altshuller contradictions: {baseline['altshuller']['total_contradictions']}")
    print()
    print(f"BACON Stefan-Boltzmann R²: {baseline['bacon']['stefan_boltzmann_r2']}")
    print(f"BACON PCM CV gap: {baseline['bacon']['pcm_cv_gap']}")
    print()
    print(f"Corpus: {baseline['corpus']['papers']} papers, {baseline['corpus']['patents']} patents, {baseline['corpus']['radiative_cooling']} RC papers")
    print("=" * 60)

    # Also persist tier_counts + causal_density to the ledger (DR-24)
    ledger_path = ROOT / "data" / "ledger" / "predictions.jsonl"
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_entry = {
        "type": "baseline_measurement",
        "timestamp": baseline["timestamp"],
        "writer": "scripts.measure_baseline",
        "tier_counts": baseline["graph"]["tier_counts"],
        "causal_density": baseline["graph"]["causal_density"],
        "total_edges": baseline["graph"]["total_edges"],
        "total_nodes": baseline["graph"]["total_nodes"],
    }
    with ledger_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(ledger_entry, default=str) + "\n")
    print(f"Ledger entry appended: {ledger_path.relative_to(ROOT)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
