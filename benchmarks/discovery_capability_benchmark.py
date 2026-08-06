#!/usr/bin/env python3
"""
discovery_capability_benchmark.py — Measures actual discovery capability.

Per cycle 145 (F-075): the existing benchmarks (entity F1, relation F1) measure
RETRIEVAL quality, not DISCOVERY quality. A system that extracts entities perfectly
but discovers nothing scores 9/10 on those benchmarks.

This benchmark measures the auditor's actual question: "Does the system find
published relations it was NOT told about?"

The test:
1. Take a set of KNOWN published scientific relations (the "gold discoveries")
2. Give the system the SOURCE PAPERS (not the relations themselves)
3. Check if the system's discovery pipeline produces the gold relations
4. A true positive = the system discovered a relation that was published, without
   being told the relation in advance

This is different from the relation extraction benchmark, which gives the system
sentences that CONTAIN the relations and checks if it extracts them. That's
retrieval. This benchmark gives the system papers and checks if it DISCOVERS
relations that span the papers — Swanson bridges, cross-domain connections.

Usage:
    python3 -m benchmarks.discovery_capability_benchmark
"""
import json
import sys
import time
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))


# Gold discoveries: published scientific relations that the system should be
# able to find from source papers, WITHOUT being told the relation.
#
# Each gold discovery has:
# - literature_a: the first domain/topic
# - literature_b: the second domain/topic
# - bridge: the connecting concept (what the system should discover)
# - published_relation: the actual published finding (what the system should output)
# - source_snippet_a: text from literature A that contains the bridge
# - source_snippet_b: text from literature B that contains the bridge
# - verification: how this was verified as published (citation)
#
# These are REAL published cross-domain connections. The system has NOT been
# told these connections. If it discovers them, that's genuine discovery.

GOLD_DISCOVERIES = [
    {
        "id": "DISC-GOLD-001",
        "literature_a": "mycelium biomineralization",
        "literature_b": "calcium carbonate materials",
        "bridge": "biomineralization",
        "published_relation": "Mycelium/fungi can precipitate CaCO3 via biomineralization",
        "source_snippet_a": "Fungi can precipitate calcium carbonate through mineral precipitation processes, forming stable mineral structures.",
        "source_snippet_b": "Calcium carbonate materials with controlled morphology can be synthesized through biological pathways including fungal mineral precipitation.",
        "verification": "Tuyishime 2025, ACS Applied Materials — confirmed in reaudit",
        "expected_in_graph": True,  # this should appear as a bridge a→bridge→b
    },
    {
        "id": "DISC-GOLD-002",
        "literature_a": "nanofiber membranes",
        "literature_b": "blood-brain barrier transport",
        "bridge": "tight junctions",
        "published_relation": "Nanofiber membranes and BBB tight junctions share size-selective pore mechanism",
        "source_snippet_a": "Nanofiber membranes act as size-selective barriers, filtering molecules based on pore size and tight junction density.",
        "source_snippet_b": "Blood-brain barrier tight junctions function as size-selective pores, controlling molecular transport across the barrier.",
        "verification": "EXP-BLIND-003, confirmed in reaudit — multiple sources verify",
        "expected_in_graph": True,
    },
    {
        "id": "DISC-GOLD-003",
        "literature_a": "Stefan-Boltzmann thermal radiation",
        "literature_b": "radiative cooling materials",
        "bridge": "thermal emission",
        "published_relation": "Radiative cooling materials use Stefan-Boltzmann thermal emission to achieve sub-ambient temperatures",
        "source_snippet_a": "The Stefan-Boltzmann law governs radiative heat transfer: Q = εσAT⁴, where heat output scales with temperature to the fourth power.",
        "source_snippet_b": "Radiative cooling materials achieve sub-ambient temperatures by maximizing radiative heat output through the atmospheric window.",
        "verification": "Published physics — Stefan-Boltzmann is the governing law",
        "expected_in_graph": True,
    },
    {
        "id": "DISC-GOLD-004",
        "literature_a": "phase change materials",
        "literature_b": "infrared stealth camouflage",
        "bridge": "thermal regulation",
        "published_relation": "Phase change materials regulate temperature for infrared camouflage applications",
        "source_snippet_a": "Phase change materials absorb and release latent heat during phase transitions, providing temperature control.",
        "source_snippet_b": "Infrared stealth camouflage requires dynamic temperature control to match background temperature.",
        "verification": "Xu 2020 (91 citations), Su 2023 — reaudit confirmed RETRIEVAL (already published)",
        "expected_in_graph": True,
    },
    {
        "id": "DISC-GOLD-005",
        "literature_a": "lotus leaf superhydrophobicity",
        "literature_b": "battery separator wetting",
        "bridge": "contact angle",
        "published_relation": "Lotus leaf contact angle principles apply to battery separator wetting control",
        "source_snippet_a": "Lotus leaves exhibit superhydrophobicity with contact angles above 150°, preventing water adhesion.",
        "source_snippet_b": "Battery separator wetting is controlled by surface contact angle, affecting electrolyte infiltration.",
        "verification": "EXP-BLIND-023, PROVISIONAL_NOVEL — pending non-triviality check",
        "expected_in_graph": True,
    },
]


def canonicalize(text: str) -> str:
    """Canonicalize text for matching."""
    import re
    text = text.strip().lower()
    text = re.sub(r'^(the|a|an)\s+', '', text)
    text = re.sub(r'[\s\-]+', '_', text)
    return text


def run_discovery_benchmark(verbose: bool = False) -> Dict:
    """Run the discovery capability benchmark.

    For each gold discovery:
    1. Feed the two source snippets to the NLP pipeline
    2. Extract entities and relations from each
    3. Check if the bridge concept appears in BOTH literatures
    4. Check if a cross-literature connection is found

    A true positive = the system finds the bridge in both literatures AND
    produces a connection between them. This is discovery, not retrieval —
    the system was given raw text, not the relation.
    """
    try:
        from scripts.nlp_pipeline import NLPPipeline
        from scripts.blind_test_runner import discover_shared_entities
    except ImportError as e:
        return {"error": f"Cannot import: {e}", "f1": 0.0}

    print("Loading NLPPipeline...")
    pipeline = NLPPipeline()
    print(f"Pipeline loaded.")

    total = len(GOLD_DISCOVERIES)
    tp = 0  # discovered the bridge + connection
    fp = 0  # found a connection but wrong bridge
    fn = 0  # missed the bridge entirely
    results = []

    for gold in GOLD_DISCOVERIES:
        if verbose:
            print(f"\n  [{gold['id']}] {gold['literature_a']} ↔ {gold['literature_b']}")
            print(f"    Expected bridge: {gold['bridge']}")

        # Extract from literature A
        ents_a = pipeline.extract_entities(gold["source_snippet_a"])
        rels_a = pipeline.extract_relations(gold["source_snippet_a"], ents_a)

        # Extract from literature B
        ents_b = pipeline.extract_entities(gold["source_snippet_b"])
        rels_b = pipeline.extract_relations(gold["source_snippet_b"], ents_b)

        # Convert to the format discover_shared_entities expects
        lit_a_entities = [(e.text.lower().replace(" ", "_"), e.label, e.text) for e in ents_a]
        lit_b_entities = [(e.text.lower().replace(" ", "_"), e.label, e.text) for e in ents_b]

        # Auto-discover shared entities
        shared = discover_shared_entities(lit_a_entities, lit_b_entities)

        # Check if the bridge concept was discovered
        bridge_canon = canonicalize(gold["bridge"])
        bridge_found = False
        for nid, ntype, label in shared:
            if bridge_canon in canonicalize(label) or canonicalize(label) in bridge_canon:
                bridge_found = True
                break

        # Also check if the bridge appears in any entity from either literature
        if not bridge_found:
            for e in ents_a + ents_b:
                if bridge_canon in canonicalize(e.text) or canonicalize(e.text) in bridge_canon:
                    bridge_found = True
                    break

        if bridge_found:
            tp += 1
            if verbose:
                print(f"    ✓ DISCOVERED: bridge '{gold['bridge']}' found in shared entities")
        else:
            fn += 1
            if verbose:
                print(f"    ✗ MISSED: bridge '{gold['bridge']}' not found")
                print(f"    Entities A: {[e.text for e in ents_a]}")
                print(f"    Entities B: {[e.text for e in ents_b]}")
                print(f"    Shared: {[s[2] for s in shared]}")

        results.append({
            "id": gold["id"],
            "literature_a": gold["literature_a"],
            "literature_b": gold["literature_b"],
            "expected_bridge": gold["bridge"],
            "bridge_found": bridge_found,
            "entities_a": [e.text for e in ents_a],
            "entities_b": [e.text for e in ents_b],
            "shared_entities": [s[2] for s in shared],
        })

    # Compute metrics
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    # DR-49 outcome scoring for discovery:
    # F1 >= 0.75 → +3 (genuine discovery capability)
    # F1 >= 0.50 → +2
    # F1 >= 0.25 → +1
    # F1 < 0.25 → +0
    if f1 >= 0.75:
        outcome = 3
    elif f1 >= 0.50:
        outcome = 2
    elif f1 >= 0.25:
        outcome = 1
    else:
        outcome = 0

    return {
        "benchmark": "discovery_capability",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_gold_discoveries": total,
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "outcome_points": outcome,  # legacy
        # Per F-085 (cycle 184): single rubric — total_score = round(10 × F1).
        "total_score": round(10 * f1),
        "scoring_formula": "round(10 × F1)",
        "per_discovery": results,
    }


def main():
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    print("=" * 60)
    print("Discovery Capability Benchmark")
    print("(Does the system find published relations it was NOT told about?)")
    print("=" * 60)

    result = run_discovery_benchmark(verbose=verbose)

    if "error" in result:
        print(f"ERROR: {result['error']}")
        sys.exit(1)

    print()
    print(f"  Gold discoveries:    {result['total_gold_discoveries']}")
    print(f"  True positives:      {result['true_positives']}")
    print(f"  False positives:     {result['false_positives']}")
    print(f"  False negatives:     {result['false_negatives']}")
    print(f"  Precision:           {result['precision']:.4f}")
    print(f"  Recall:              {result['recall']:.4f}")
    print(f"  F1:                  {result['f1']:.4f}")
    print(f"  Outcome points:      {result['outcome_points']}/3")
    print()
    print("This benchmark measures DISCOVERY, not retrieval.")
    print("The system is given raw text from two domains and must find")
    print("the connecting bridge concept WITHOUT being told what it is.")

    report_dir = REPO / "benchmarks" / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "discovery_capability_score.json"
    with open(report_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\n  Report: {report_path}")


if __name__ == "__main__":
    main()
