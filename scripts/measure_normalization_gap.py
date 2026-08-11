#!/usr/bin/env python3
"""
Phase 5.D — Normalization gap measurement (NOT a parser change).

Per the CEO's directive (post-Phase 5.C audit):
  'Do not solve these problems yet. Measure them.'

This script computes three things:
  1. NORMALIZATION_GAP.md content — every failed bridge between
     semantically-related component labels across the real-source
     corpus, with the reason each bridge failed.
  2. bridgeable_shared_components metric — exact / potential /
     unmatched label counts, measuring how much signal is being
     lost to normalization gaps.
  3. Saturation analysis — across all 4 snapshots, the table of
     (snapshot, nodes, shared_components, score) and the derivative
     d(shared_components)/d(total_components).

This is a MEASUREMENT script. It does NOT modify the parser, does NOT
add keywords, does NOT implement stemming or synonym maps or
embeddings. Per the CEO's most important instruction:
  'Do not interpret this as permission to build semantic matching.
   The evidence currently supports only this statement:
   > Exact-label matching is the limiting factor.
   It does not support the statement:
   > Semantic matching is the correct solution.'

One-off script. NOT a module. NOT imported by anything.
"""
import json
import pathlib
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
GRAPH_PATH = ROOT / "data" / "civilization_graph.json"
SOURCES_DIR = ROOT / "data" / "ingestion" / "real"
SNAPSHOTS_DIR = ROOT / "data" / "snapshots"


def load_graph():
    with open(GRAPH_PATH) as f:
        return json.load(f)


def load_snapshots():
    snaps = {}
    for p in sorted(SNAPSHOTS_DIR.glob("snapshot_*.json")):
        with open(p) as f:
            snaps[p.stem] = json.load(f)
    return snaps


def real_component_labels(graph):
    """Return list of (label, node_id, source) for ALL component-typed
    nodes in the graph — both real-source (real_*) and Phase 3 synthetic
    (ingested_*). The convergence formula's Signal C uses all of them,
    so the normalization gap analysis must too."""
    labels = []
    for n in graph["nodes"]:
        if n.get("type") != "component":
            continue
        # Include both real_ (Phase 5) and ingested_ (Phase 3 synthetic)
        # nodes — the formula doesn't distinguish.
        prov = n.get("provenance", {})
        source = prov.get("patent_number") or prov.get("doi") or prov.get("source", "?")
        is_real = prov.get("is_real_source", False) or n["id"].startswith("real_")
        labels.append({
            "label": n.get("label", ""),
            "label_key": n.get("label", "").lower().strip(),
            "node_id": n["id"],
            "source": source,
            "domain": prov.get("domain", "?"),
            "is_real_source": is_real,
        })
    return labels


def scan_source_text_for_terms():
    """Scan all real-source text files for component-vocabulary terms
    that appear in the text but were NOT extracted by the (frozen)
    parser. This is the 'extraction gap' — terms present in source
    text but missing from the graph."""
    # The parser's current (frozen) keyword list (Phase 5.C state).
    PAPER_KEYWORDS = {'pump', 'sensor', 'coating', 'membrane', 'exchanger',
                       'substrate', 'valve', 'motor', 'circuit', 'electrode',
                       'battery', 'panel', 'filter', 'chamber', 'nozzle',
                       'actuator', 'controller', 'anode', 'cathode',
                       'electrolyte', 'sorbent', 'metamaterial', 'adsorbent',
                       'charger', 'metal-organic framework'}
    PATENT_KEYWORDS = {'pump', 'sensor', 'coating', 'membrane', 'exchanger',
                       'substrate', 'valve', 'motor', 'circuit', 'electrode',
                       'battery', 'panel', 'filter', 'chamber', 'nozzle',
                       'actuator', 'controller'}

    # Candidate terms that appear in source text but are NOT in the
    # frozen keyword list (i.e., would be extraction gaps).
    # These are the auditor's examples + variants found by scanning.
    candidate_unextracted = [
        ('batteries', 'plural of battery (substring miss: battery not in batteries)'),
        ('batter', 'stem — would catch battery/batteries/battery-powered'),
        ('cells', 'plural of cell — battery context'),
        ('electrodes', 'plural of electrode'),
        ('anodes', 'plural of anode'),
        ('cathodes', 'plural of cathode'),
        ('electrolytes', 'plural of electrolyte'),
        ('membranes', 'plural of membrane'),
        ('sorbents', 'plural of sorbent'),
        ('adsorbents', 'plural of adsorbent'),
        ('metamaterials', 'plural of metamaterial'),
        ('MOF', 'abbreviation of metal-organic framework'),
        ('MOFs', 'plural abbreviation of metal-organic framework'),
        ('mof', 'lowercase abbreviation'),
        ('desiccant', 'synonym-ish of sorbent (AWH context)'),
        ('sieve', 'related to membrane/filter'),
        ('photonic', 'related to metamaterial (radiative cooling)'),
        ('emitter', 'related to coating (radiative cooling)'),
        ('absorber', 'related to coating (radiative cooling)'),
    ]

    text_files = sorted(SOURCES_DIR.glob("*.txt"))
    extraction_gaps = []
    for fp in text_files:
        text = fp.read_text().lower()
        for term, reason in candidate_unextracted:
            # Word-boundary match to avoid false positives
            if re.search(r'\b' + re.escape(term.lower()) + r'\b', text):
                # Check if this term is already extracted (i.e., is a keyword)
                already_extracted = term in PAPER_KEYWORDS or term in PATENT_KEYWORDS
                if not already_extracted:
                    extraction_gaps.append({
                        "source_file": fp.name,
                        "term": term,
                        "reason": reason,
                    })
    return extraction_gaps


def find_failed_bridges(graph):
    """Identify pairs of labels in the graph that COULD share a node
    under some normalization rule but currently don't. Categorize by
    the normalization gap type."""
    labels = real_component_labels(graph)
    # Group by label_key to find existing shared nodes
    by_key = defaultdict(list)
    for l in labels:
        by_key[l["label_key"]].append(l)

    failed_bridges = []

    # 1. Pluralization gaps: check if "X" and "Xs" both appear as labels
    label_keys = set(by_key.keys())
    for key in sorted(label_keys):
        plural = key + "s"
        if plural in label_keys:
            failed_bridges.append({
                "type": "pluralization",
                "source_a": key,
                "source_b": plural,
                "nodes_a": [l["node_id"] for l in by_key[key]],
                "nodes_b": [l["node_id"] for l in by_key[plural]],
                "why": f"'{key}' and '{plural}' are singular/plural of the same concept but treated as different labels",
            })

    # 2. Abbreviation gaps: metal-organic framework <-> MOF
    # (MOF is not in graph because we excluded it for false-positive risk,
    # but it appears in source text. Document this as a known gap.)
    if "metal-organic framework" in label_keys:
        failed_bridges.append({
            "type": "abbreviation",
            "source_a": "metal-organic framework",
            "source_b": "MOF / MOFs",
            "nodes_a": [l["node_id"] for l in by_key["metal-organic framework"]],
            "nodes_b": "(not in graph — 'mof' excluded from keyword list for false-positive risk; appears in arxiv_2311.00341, arxiv_2407.00470, arxiv_2501.04825 source text)",
            "why": "'MOF' is the standard abbreviation of 'metal-organic framework'. Keyword 'mof' was excluded because it would substring-match 'monolithic' and other words.",
        })

    # 3. Synonymy / terminology drift: sorbent <-> adsorbent
    # These are different words for overlapping concepts.
    if "sorbent" in label_keys and "adsorbent" in label_keys:
        failed_bridges.append({
            "type": "terminology_drift",
            "source_a": "sorbent",
            "source_b": "adsorbent",
            "nodes_a": [l["node_id"] for l in by_key["sorbent"]],
            "nodes_b": [l["node_id"] for l in by_key["adsorbent"]],
            "why": "'sorbent' and 'adsorbent' are near-synonyms in the AWH/DAC literature. Both refer to materials that capture gases. Treated as different labels because the parser uses exact matching.",
        })

    # 4. Subtype / hypernym: electrode <-> anode/cathode
    # anode and cathode are TYPES of electrodes.
    if "electrode" in label_keys and ("anode" in label_keys or "cathode" in label_keys):
        failed_bridges.append({
            "type": "hypernym_subtype",
            "source_a": "electrode",
            "source_b": "anode / cathode",
            "nodes_a": [l["node_id"] for l in by_key["electrode"]],
            "nodes_b": [l["node_id"] for l in by_key.get("anode", [])] + [l["node_id"] for l in by_key.get("cathode", [])],
            "why": "'anode' and 'cathode' are subtypes of 'electrode'. The battery patent (US20240194939A1) uses 'electrode'; the battery arXiv paper (2307.03620) uses 'anode'/'cathode'. Treated as different labels.",
        })

    # 5. Compound vs simple: battery <-> "an all-solid-state battery laminate..."
    # The patent extracted a long compound label, the arXiv paper extracted "battery"/"anode".
    long_battery_labels = [k for k in label_keys if "battery" in k and len(k) > 20]
    if "battery" in label_keys and long_battery_labels:
        failed_bridges.append({
            "type": "compound_vs_simple",
            "source_a": "battery",
            "source_b": long_battery_labels[0][:50] + "..." if len(long_battery_labels[0]) > 50 else long_battery_labels[0],
            "nodes_a": [l["node_id"] for l in by_key["battery"]],
            "nodes_b": [l["node_id"] for l in by_key[long_battery_labels[0]]],
            "why": "The patent's claims-format extraction produced a long compound label containing 'battery'; the arXiv paper's keyword extraction produced the simple 'battery'. Both refer to the same component class but don't share a node.",
        })

    return failed_bridges, by_key


def compute_bridgeable_metric(graph):
    """Compute exact / potential / unmatched label counts."""
    labels = real_component_labels(graph)
    by_key = defaultdict(list)
    for l in labels:
        by_key[l["label_key"]].append(l)

    # Exact matches: labels shared by 2+ sources
    exact_matches = []
    for key, occs in by_key.items():
        sources = set(l["source"] for l in occs)
        if len(sources) >= 2:
            exact_matches.append({
                "label": key,
                "count": len(occs),
                "sources": sorted(sources),
            })

    # Potential matches: pairs of labels that COULD share under
    # some normalization rule (plural, abbreviation, synonym).
    # We re-use the failed_bridges analysis to count these.
    failed, _ = find_failed_bridges(graph)
    potential_pairs = []
    for fb in failed:
        if "nodes_b" in fb and isinstance(fb["nodes_b"], list) and fb["nodes_b"]:
            # Both sides are in the graph
            potential_pairs.append({
                "label_a": fb["source_a"],
                "label_b": fb["source_b"],
                "type": fb["type"],
                "in_graph_both": True,
            })
        else:
            # One side is missing from graph (extraction gap)
            potential_pairs.append({
                "label_a": fb["source_a"],
                "label_b": fb["source_b"],
                "type": fb["type"],
                "in_graph_both": False,
            })

    # Unmatched labels: labels with no exact match AND no potential match
    matched_labels = set()
    for em in exact_matches:
        matched_labels.add(em["label"])
    for pp in potential_pairs:
        if pp["in_graph_both"]:
            matched_labels.add(pp["label_a"])
            matched_labels.add(pp["label_b"])

    unmatched = []
    for key, occs in by_key.items():
        if key not in matched_labels:
            unmatched.append({
                "label": key,
                "count": len(occs),
                "sources": sorted(set(l["source"] for l in occs)),
            })

    return {
        "total_distinct_labels": len(by_key),
        "exact_matches": exact_matches,
        "exact_matches_count": len(exact_matches),
        "potential_matches": potential_pairs,
        "potential_matches_count": len(potential_pairs),
        "unmatched_labels": unmatched,
        "unmatched_count": len(unmatched),
    }


def saturation_analysis(snapshots):
    """Compute the saturation table and derivative across snapshots."""
    rows = []
    prev_shared = None
    prev_total = None
    for snap_id in sorted(snapshots.keys()):
        snap = snapshots[snap_id]
        # Use the convergence breakdown for battery×EV
        ev = snap["metrics"]["convergence_scores"]["battery_ev"]
        shared = ev["breakdown"].get("shared_components_count", 0)
        total_a = ev["breakdown"].get("component_subtree_a_size", 0)
        total_b = ev["breakdown"].get("component_subtree_b_size", 0)
        total = total_a + total_b - shared  # union
        score = ev["score"]
        d_shared = (shared - prev_shared) if prev_shared is not None else None
        d_total = (total - prev_total) if prev_total is not None else None
        derivative = (d_shared / d_total) if (d_shared is not None and d_total and d_total != 0) else None
        rows.append({
            "snapshot": snap_id,
            "graph_version": snap["graph_version"],
            "nodes": snap["nodes"],
            "edges": snap["edges"],
            "shared_components_battery_ev": shared,
            "total_components_battery_ev": total,
            "score_battery_ev": score,
            "d_shared": d_shared,
            "d_total": d_total,
            "d_shared_over_d_total": round(derivative, 4) if derivative is not None else None,
        })
        prev_shared = shared
        prev_total = total
    return rows


def main():
    print("=" * 70)
    print("PHASE 5.D — NORMALIZATION GAP MEASUREMENT")
    print("(NOT a parser change, NOT semantic matching)")
    print("=" * 70)

    graph = load_graph()
    snapshots = load_snapshots()

    print(f"\nGraph: {len(graph['nodes'])} nodes, {len(graph['edges'])} edges, v{graph['metadata']['version']}")
    print(f"Snapshots loaded: {sorted(snapshots.keys())}")

    # --- Task 2: Failed bridges ---
    print(f"\n--- Task 2: Failed bridges ---")
    failed_bridges, by_key = find_failed_bridges(graph)
    print(f"Distinct real-component labels in graph: {len(by_key)}")
    print(f"Failed bridges identified: {len(failed_bridges)}")
    for fb in failed_bridges:
        print(f"  [{fb['type']}] {fb['source_a']!r} <-> {fb['source_b']!r}")

    # --- Task 3: Bridgeable metric ---
    print(f"\n--- Task 3: bridgeable_shared_components metric ---")
    metric = compute_bridgeable_metric(graph)
    print(f"Total distinct labels:        {metric['total_distinct_labels']}")
    print(f"Exact matches (shared nodes): {metric['exact_matches_count']}")
    print(f"Potential matches (gaps):     {metric['potential_matches_count']}")
    print(f"Unmatched labels:             {metric['unmatched_count']}")
    print(f"\nExact matches:")
    for em in metric["exact_matches"]:
        print(f"  - {em['label']!r}: {em['count']} occurrences from {em['sources']}")
    print(f"\nPotential matches (normalization gaps):")
    for pp in metric["potential_matches"]:
        marker = "[in-graph both]" if pp["in_graph_both"] else "[one side missing]"
        print(f"  - {pp['label_a']!r} <-> {pp['label_b']!r} ({pp['type']}) {marker}")
    print(f"\nUnmatched labels (no bridge, no potential):")
    for u in metric["unmatched_labels"]:
        print(f"  - {u['label']!r}: {u['count']} occurrence(s) from {u['sources']}")

    # --- Task 4: Saturation analysis ---
    print(f"\n--- Task 4: Saturation analysis ---")
    sat = saturation_analysis(snapshots)
    print(f"\n{'Snapshot':<12} {'Graph v':<8} {'Nodes':>6} {'Edges':>6} {'Shared':>7} {'Total':>7} {'Score':>8} {'dShared':>8} {'dTotal':>8} {'dSh/dTot':>9}")
    print("-" * 90)
    for row in sat:
        d_sh = f"{row['d_shared']:+d}" if row['d_shared'] is not None else "—"
        d_tot = f"{row['d_total']:+d}" if row['d_total'] is not None else "—"
        deriv = f"{row['d_shared_over_d_total']:+.4f}" if row['d_shared_over_d_total'] is not None else "—"
        print(f"{row['snapshot']:<12} {row['graph_version']:<8} {row['nodes']:>6} {row['edges']:>6} {row['shared_components_battery_ev']:>7} {row['total_components_battery_ev']:>7} {row['score_battery_ev']:>8.4f} {d_sh:>8} {d_tot:>8} {deriv:>9}")


if __name__ == "__main__":
    main()
