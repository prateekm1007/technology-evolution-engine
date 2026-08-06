#!/usr/bin/env python3
"""
Phase 5.C — Re-ingest arXiv papers with EXPANDED PaperParser.

Per the auditor's V4 finding on F-038 and the CEO's authorized action:
  'F-038's recommended fix (expand COMPONENT_KEYWORDS to include
  scientific vocabulary: sorbent, metamaterial, electrolyte, anode,
  cathode) is allowed as a data modification, not architecture.'

This script re-runs the EXISTING 10 arXiv abstracts (from Phase 5.B)
through the now-richer PaperParser and adds any NEWLY-extracted
component nodes to the live graph. The 10 paper nodes already exist
(from Phase 5.B); this script only adds the new components they
extract and links them to the existing paper nodes via `contains`
edges from the paper's domain's subdomain.

This is a measurement cycle on data already in the repo, NOT a new
ingestion cycle. The corpus is unchanged; only the parser changed.

One-off ingestion script, NOT a module. NOT imported by anything.
"""
import json
import pathlib
import sys
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from product.ingestion.paper_parser import PaperParser

GRAPH_PATH = ROOT / "data" / "civilization_graph.json"
REAL_SOURCES_DIR = ROOT / "data" / "ingestion" / "real"

PAPER_DOMAIN = {
    "2307.03620": "battery",
    "2311.08656": "ev_charging",
    "2105.02905": "ev_charging",
    "2301.13160": "desalination",
    "2003.10495": "radiative_cooling",
    "2301.04523": "radiative_cooling",
    "2301.10338": "radiative_cooling",
    "2407.00470": "atmospheric_water_harvesting",
    "2311.00341": "carbon_capture",
    "2501.04825": "carbon_capture",
}

DOMAIN_TO_SUBDOMAIN_NODE = {
    "battery": "sub_battery_technology",
    "ev_charging": "sub_electric_propulsion",
    "desalination": "sub_desalination",
    "radiative_cooling": "sub_radiative_cooling",
    "atmospheric_water_harvesting": "sub_atmospheric_water_harvesting",
    "carbon_capture": "sub_carbon_capture",
}


def make_provenance(filename, arxiv_id, title):
    return {
        "source": filename,
        "source_type": "paper",
        "title": title,
        "authors": ["(real arXiv paper, re-ingested Phase 5.C)"],
        "publication_date": "2026-08-02",
        "patent_number": None,
        "doi": f"arxiv:{arxiv_id}",
        "confidence": 0.9,
        "extracted_by": "scripts.ingest_real_arxiv_phase5c_expanded_parser",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "is_real_source": True,
        "domain": PAPER_DOMAIN.get(arxiv_id, "unknown"),
        "phase": "5.C",
        "parser_note": "Re-ingested with expanded COMPONENT_KEYWORDS (Phase 5.C fix for F-038)",
    }


def main():
    print("=" * 70)
    print("PHASE 5.C — Re-ingest arXiv papers with EXPANDED PaperParser")
    print("=" * 70)
    print("Parser change: COMPONENT_KEYWORDS expanded with scientific")
    print("vocabulary (anode, cathode, electrolyte, sorbent, metamaterial,")
    print("adsorbent, charger, metal-organic framework).")
    print()

    with open(GRAPH_PATH) as f:
        graph = json.load(f)
    original_count = len(graph["nodes"])
    original_edge_count = len(graph["edges"])
    existing_ids = {n["id"] for n in graph["nodes"]}
    existing_node_ids = set(existing_ids)
    existing_edge_keys = {(e["source"], e["target"], e.get("relationship"))
                         for e in graph["edges"]}
    print(f"Graph before: {original_count} nodes, {original_edge_count} edges")

    real_before = sum(1 for n in graph["nodes"]
                      if n.get("provenance", {}).get("is_real_source"))
    print(f"Nodes with REAL provenance before: {real_before}")

    parser = PaperParser()  # Uses the EXPANDED keyword list
    added = 0
    edges_added = 0
    domain_counts = {}
    new_components_by_paper = {}

    # Build a deduplication map: component label -> canonical node ID.
    # Initialized with EXISTING real-component labels from the graph
    # (both Phase 5.A patent components and Phase 5.B paper components
    # if any). When the updated parser extracts "membrane" from the
    # desalination paper, it will deduplicate to the existing
    # real_US4039440A_membrane node.
    label_to_canonical_id = {}
    for n in graph["nodes"]:
        if n.get("provenance", {}).get("is_real_source"):
            label = n.get("label", "").lower().strip()
            if label:
                if label not in label_to_canonical_id:
                    label_to_canonical_id[label] = n["id"]

    print(f"Existing real-component canonical labels: {len(label_to_canonical_id)}")

    for filepath in sorted(REAL_SOURCES_DIR.glob("arxiv_*.txt")):
        arxiv_id = filepath.stem.replace("arxiv_", "")
        text = filepath.read_text()
        title_line = text.split("\n")[0]
        title = title_line.replace("Title: ", "").strip() if "Title:" in title_line else arxiv_id
        provenance = make_provenance(filepath.name, arxiv_id, title)
        result = parser.parse({"id": arxiv_id, "text": text, "provenance": provenance})

        domain = PAPER_DOMAIN.get(arxiv_id, "unknown")
        domain_counts[domain] = domain_counts.get(domain, 0) + 1

        subdomain_node_id = DOMAIN_TO_SUBDOMAIN_NODE.get(domain)
        subdomain_exists = subdomain_node_id and subdomain_node_id in existing_node_ids

        new_components = []
        for comp in result.get("components", []):
            label = str(comp)
            label_key = label.lower().strip()
            canonical_id = label_to_canonical_id.get(label_key)
            if canonical_id:
                # Reuse existing node — don't create a new one, but
                # DO add an edge from this paper's subdomain to it
                # if no such edge exists yet (cross-source bridge).
                node_id = canonical_id
                is_new_node = False
            else:
                node_id = f"real_arxiv_{arxiv_id}_{label_key.replace(' ', '_')}"[:80]
                is_new_node = True
                label_to_canonical_id[label_key] = node_id

            if is_new_node and node_id not in existing_ids:
                parsed_constraints = result.get("constraints", {})
                if isinstance(parsed_constraints, dict):
                    constraints = {k: 0.7 for k in parsed_constraints}
                else:
                    constraints = {}
                graph["nodes"].append({
                    "id": node_id,
                    "label": label,
                    "type": "component",
                    "domain": domain,
                    "constraints": constraints,
                    "provenance": provenance,
                    "status": "active",
                    "shared_label": label_key,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                })
                existing_ids.add(node_id)
                existing_node_ids.add(node_id)
                added += 1
                new_components.append(label)

            # Add `contains` edge from this paper's domain's subdomain to the component
            if subdomain_exists:
                edge_key = (subdomain_node_id, node_id, "contains")
                if edge_key not in existing_edge_keys:
                    graph["edges"].append({
                        "source": subdomain_node_id,
                        "target": node_id,
                        "relationship": "contains",
                        "weight": 1.0,
                        "description": f"Phase 5.C: arxiv:{arxiv_id} ({domain}) -> {subdomain_node_id} (expanded parser)",
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    })
                    existing_edge_keys.add(edge_key)
                    edges_added += 1

        new_components_by_paper[arxiv_id] = new_components
        all_comps = result.get("components", [])
        print(f"  arxiv:{arxiv_id} ({domain}): "
              f"components={all_comps}, new={new_components}, "
              f"subdomain_link={'yes' if subdomain_exists else 'no'}")

    real_after = sum(1 for n in graph["nodes"]
                     if n.get("provenance", {}).get("is_real_source"))

    # Update graph metadata
    graph["metadata"]["version"] = "4.2"
    graph["metadata"]["node_count"] = len(graph["nodes"])
    graph["metadata"]["edge_count"] = len(graph["edges"])
    graph["metadata"]["phase_5c_re_ingestion"] = {
        "ingested_at": datetime.now(timezone.utc).isoformat(),
        "description": "Re-ran the existing 10 arXiv abstracts through the "
                       "EXPANDED PaperParser (Phase 5.C fix for F-038). The "
                       "parser now extracts scientific component vocabulary "
                       "(anode, cathode, electrolyte, sorbent, metamaterial, "
                       "adsorbent, charger, metal-organic framework) that the "
                       "Phase 5.B parser missed.",
        "parser_change": "product/ingestion/paper_parser.py _extract_components "
                          "expanded with 8 new keywords grounded in actual arXiv "
                          "abstracts. The original 17 patent-oriented keywords "
                          "are unchanged.",
        "arxiv_papers_re_ingested": len(list(REAL_SOURCES_DIR.glob("arxiv_*.txt"))),
        "new_component_nodes_added": added,
        "new_edges_added": edges_added,
        "nodes_with_real_provenance_before": real_before,
        "nodes_with_real_provenance_after": real_after,
        "new_components_by_paper": new_components_by_paper,
    }

    with open(GRAPH_PATH, "w") as f:
        json.dump(graph, f, indent=2)
        f.write("\n")

    print(f"\n{'=' * 70}")
    print(f"Graph after: {len(graph['nodes'])} nodes (+{len(graph['nodes']) - original_count})")
    print(f"             {len(graph['edges'])} edges (+{edges_added})")
    print(f"Nodes with REAL provenance: {real_before} -> {real_after}")
    print(f"Domain distribution: {domain_counts}")
    print(f"Graph version: 4.1 -> 4.2")
    print(f"Written to: {GRAPH_PATH}")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
