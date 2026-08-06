#!/usr/bin/env python3
"""
Phase 5 — Ingest REAL patent sources into the live graph.

Per the CEO's Phase 5 directive Step 1 (corpus) and Step 2 (domains):
  - Ingest real USPTO patents (not synthetic) into the actual
    civilization_graph.json.
  - Domains: batteries, electric vehicles, desalination, radiative
    cooling, atmospheric water harvesting, carbon capture.

This is a ONE-OFF ingestion script, NOT a module. It is NOT imported
by anything. It uses the existing PatentParser from product/ingestion/.

This is the snapshot_1 → snapshot_2 transition. The graph at the start
of this script's run is snapshot_1; the graph at the end is snapshot_2.
"""
import json
import pathlib
import sys
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from product.ingestion.patent_parser import PatentParser

GRAPH_PATH = ROOT / "data" / "civilization_graph.json"
REAL_SOURCES_DIR = ROOT / "data" / "ingestion" / "real"

# Domain mapping based on the patent's source domain (from the search)
PATENT_DOMAIN = {
    "US20240194939A1": "battery",
    "US7768229B2": "ev_charging",
    "WO2017210800A1": "desalination",
    "US4039440A": "desalination",
    "WO2017151514A1": "radiative_cooling",
    "US20160363396A1": "radiative_cooling",
    "US10683644B2": "atmospheric_water_harvesting",
    "US11536010B2": "atmospheric_water_harvesting",
    "AU2022232918A1": "carbon_capture",
}

# Map domains to the existing subdomain node IDs in the graph.
# These are the nodes that the convergence formula measures against.
DOMAIN_TO_SUBDOMAIN_NODE = {
    "battery": "sub_battery_technology",
    "ev_charging": "sub_electric_propulsion",
    "desalination": "sub_desalination",
    "radiative_cooling": "sub_radiative_cooling",  # may not exist; skip if absent
    "atmospheric_water_harvesting": "sub_atmospheric_water_harvesting",  # may not exist
    "carbon_capture": "sub_carbon_capture",  # may not exist
}


def make_provenance(filename, patent_id, title):
    return {
        "source": filename,
        "source_type": "patent",
        "title": title,
        "authors": ["(real USPTO patent)"],
        "publication_date": "2026-08-02",
        "patent_number": patent_id,
        "doi": None,
        "confidence": 0.9,  # Higher confidence for real sources
        "extracted_by": "scripts.ingest_real_patents_phase5",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "is_real_source": True,  # Distinguishes from synthetic
        "domain": PATENT_DOMAIN.get(patent_id, "unknown"),
    }


def main():
    print("=" * 70)
    print("PHASE 5 — Ingest REAL patent sources into the live graph")
    print("=" * 70)

    with open(GRAPH_PATH) as f:
        graph = json.load(f)
    original_count = len(graph["nodes"])
    existing_ids = {n["id"] for n in graph["nodes"]}
    print(f"Graph before: {original_count} nodes")

    # Count nodes with REAL provenance before
    real_before = sum(1 for n in graph["nodes"]
                      if n.get("provenance", {}).get("is_real_source"))
    print(f"Nodes with REAL provenance before: {real_before}")

    parser = PatentParser()
    added = 0
    edges_added = 0
    domain_counts = {}

    # First, identify which subdomain nodes exist in the graph
    existing_node_ids = {n["id"] for n in graph["nodes"]}
    existing_edge_keys = {(e["source"], e["target"], e.get("relationship"))
                         for e in graph["edges"]}

    # Deduplication map: component label -> canonical node ID.
    # When two patents from DIFFERENT domains both mention "battery",
    # they should share a single component node, so the convergence
    # formula's Signal C (component reuse) can detect the overlap.
    # This is the structural change that creates cross-domain bridges.
    label_to_canonical_id = {}

    for filepath in sorted(REAL_SOURCES_DIR.glob("*.txt")):
        patent_id = filepath.stem
        text = filepath.read_text()
        title_line = text.split("\n")[0]
        title = title_line.replace("TITLE: ", "").strip() if "TITLE:" in title_line else patent_id
        provenance = make_provenance(filepath.name, patent_id, title)
        result = parser.parse({"id": patent_id, "text": text, "provenance": provenance})

        domain = PATENT_DOMAIN.get(patent_id, "unknown")
        domain_counts[domain] = domain_counts.get(domain, 0) + 1

        # Look up the subdomain node to connect to (if it exists)
        subdomain_node_id = DOMAIN_TO_SUBDOMAIN_NODE.get(domain)
        subdomain_exists = subdomain_node_id and subdomain_node_id in existing_node_ids

        # Add components as new nodes + edges from subdomain -> component.
        # DEDUPLICATE by label: if a component with this label already exists
        # (from a prior patent), reuse the existing node ID and add a new edge
        # from this domain's subdomain. This creates cross-domain bridges
        # through shared components.
        for comp in result.get("components", []):
            label = str(comp)
            label_key = label.lower().strip()
            node_id = f"real_{patent_id}_{label_key.replace(' ', '_')}"[:80]

            # Check if we've already created a canonical node for this label
            canonical_id = label_to_canonical_id.get(label_key)
            if canonical_id:
                # Reuse the existing node — don't create a new one
                node_id = canonical_id
                is_new_node = False
            else:
                # First occurrence of this label — create the canonical node
                is_new_node = True
                label_to_canonical_id[label_key] = node_id

            if is_new_node and node_id not in existing_ids:
                parsed_constraints = result.get("constraints", {})
                if isinstance(parsed_constraints, dict):
                    constraints = {k: 0.8 for k in parsed_constraints}
                else:
                    constraints = {str(c): 0.8 for c in parsed_constraints}
                for mat in result.get("materials", []):
                    if "material" not in constraints:
                        constraints["material"] = 0.7
                # Mark this component with the SHARED label so the convergence
                # formula can detect that two subdomains share it (Signal C).
                graph["nodes"].append({
                    "id": node_id,
                    "label": label,
                    "type": "component",
                    "domain": domain,  # the FIRST domain to introduce it
                    "constraints": constraints,
                    "provenance": provenance,
                    "status": "active",
                    "shared_label": label_key,  # markers for delta analysis
                    "created_at": datetime.now(timezone.utc).isoformat(),
                })
                existing_ids.add(node_id)
                existing_node_ids.add(node_id)
                added += 1

            # Add a `contains` edge from THIS patent's domain's subdomain node
            # to the component (whether new or reused). If the subdomain
            # node exists, this creates or strengthens the structural link.
            if subdomain_exists:
                edge_key = (subdomain_node_id, node_id, "contains")
                if edge_key not in existing_edge_keys:
                    graph["edges"].append({
                        "source": subdomain_node_id,
                        "target": node_id,
                        "relationship": "contains",
                        "weight": 1.0,
                        "description": f"Phase 5 ingestion: {patent_id} ({domain}) linked to {subdomain_node_id}",
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    })
                    existing_edge_keys.add(edge_key)
                    edges_added += 1

        print(f"  {patent_id} ({domain}): components={len(result.get('components', []))}, "
              f"materials={len(result.get('materials', []))}, "
              f"constraints={len(result.get('constraints', {}))}, "
              f"subdomain_link={'yes' if subdomain_exists else 'no (subdomain missing)'}")

    # Count real-provenance nodes after
    real_after = sum(1 for n in graph["nodes"]
                     if n.get("provenance", {}).get("is_real_source"))

    # Update graph metadata
    graph["metadata"]["version"] = "4.0"
    graph["metadata"]["node_count"] = len(graph["nodes"])
    graph["metadata"]["edge_count"] = len(graph["edges"])
    graph["metadata"]["phase_5_ingestion"] = {
        "ingested_at": datetime.now(timezone.utc).isoformat(),
        "patents_ingested": len(list(REAL_SOURCES_DIR.glob("*.txt"))),
        "nodes_added": added,
        "edges_added": edges_added,
        "nodes_with_real_provenance_before": real_before,
        "nodes_with_real_provenance_after": real_after,
        "domain_distribution": domain_counts,
        "source": "REAL USPTO patents fetched via web-search + web-reader",
        "distinguishes_from_phase_3": "Phase 3 used synthetic abstracts (F-034). Phase 5 uses real USPTO patent text.",
        "structural_change": "Added `contains` edges from each domain's subdomain node to the newly-ingested component nodes. This is what enables Signal C (component reuse) to be non-zero on snapshot_2.",
    }

    with open(GRAPH_PATH, "w") as f:
        json.dump(graph, f, indent=2)
        f.write("\n")

    print(f"\n{'=' * 70}")
    print(f"Graph after: {len(graph['nodes'])} nodes (+{len(graph['nodes']) - original_count})")
    print(f"             {len(graph['edges'])} edges (+{edges_added})")
    print(f"Nodes with REAL provenance: {real_before} -> {real_after}")
    print(f"Domain distribution: {domain_counts}")
    print(f"Graph version: 3.1 -> 4.0")
    print(f"Written to: {GRAPH_PATH}")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
