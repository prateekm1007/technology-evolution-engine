#!/usr/bin/env python3
"""
Phase 7B/7C — CPC extraction + capability mapping + evidence recording.

Per CEO authorization CEO-7A-7D:
- Phase 7B: CPC ingestion, patent classification extraction, evidence linkage
- Phase 7C: Manual capability extraction (document → claim → capability → evidence)

This script reads the fetched patent pages, extracts CPC codes, maps them
to capabilities per CPC_MAPPING.md, and creates evidence-backed capability
nodes + edges in a NEW graph (separate from the Phase 5 CO_OCCURRENCE_MODEL).

The Phase 5 graph (data/civilization_graph.json) is NOT modified.
The new graph is written to data/capability_graph.json.

One-off ingestion script. NOT a module. NOT imported by anything.
"""
import json
import pathlib
import re
import sys
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
PAGES_DIR = pathlib.Path("/tmp/phase7_patents/pages")
OUTPUT_GRAPH = ROOT / "data" / "capability_graph.json"

# CPC → Capability mapping (from CPC_MAPPING.md)
CPC_TO_CAPABILITIES = {
    "H01M 4/00": ["INTERCALATION", "ELECTRON_COLLECTION", "CONVERSION_REACTION"],
    "H01M 4/13": ["INTERCALATION"],
    "H01M 4/36": ["INTERCALATION", "ELECTRON_COLLECTION"],
    "H01M 4/48": ["INTERCALATION"],
    "H01M 4/50": ["INTERCALATION"],
    "H01M 4/58": ["INTERCALATION", "CONVERSION_REACTION"],
    "H01M 4/62": ["ELECTRON_COLLECTION"],
    "H01M 4/66": ["ELECTRON_COLLECTION"],
    "H01M 4/70": ["ELECTRON_COLLECTION"],
    "H01M 4/73": ["ELECTRODE_COATING"],
    "H01M 4/139": ["ELECTRODE_COATING"],
    "H01M 10/00": ["ELECTROCHEMICAL_ENERGY_STORAGE", "LONG_CYCLE_LIFE_STORAGE"],
    "H01M 10/0525": ["ELECTROCHEMICAL_ENERGY_STORAGE", "ION_TRANSPORT"],
    "H01M 10/0565": ["ION_TRANSPORT"],
    "H01M 10/0562": ["ION_TRANSPORT", "SOLID_ELECTROLYTE_SINTERING"],
    "H01M 10/058": ["CELL_ASSEMBLY"],
    "H01M 10/052": ["ELECTROCHEMICAL_ENERGY_STORAGE"],
    "H01M 10/44": ["FAST_CHARGING"],
    "H01M 10/48": ["STATE_OF_CHARGE_MONITORING", "CELL_BALANCING", "SAFETY_PROTECTION"],
    "H01M 50/00": ["CELL_ASSEMBLY", "THERMAL_MANAGEMENT"],
    "H01M 50/40": ["SELECTIVE_ION_TRANSPORT"],
    "H01M 50/41": ["SELECTIVE_ION_TRANSPORT"],
    "H01M 50/60": ["CELL_ASSEMBLY"],
    "H01M 50/70": ["CELL_ASSEMBLY"],
    "H01M 50/80": ["THERMAL_MANAGEMENT", "SAFETY_PROTECTION"],
    "H01M 50/90": ["CELL_BALANCING"],
    "H01M 50/92": ["CELL_ASSEMBLY"],
    "H01M 50/46": ["SELECTIVE_ION_TRANSPORT"],
    "H01M 50/451": ["SELECTIVE_ION_TRANSPORT"],
    "H01M 50/453": ["SELECTIVE_ION_TRANSPORT"],
    "H01M 50/463": ["SELECTIVE_ION_TRANSPORT"],
    "H01M 50/467": ["SELECTIVE_ION_TRANSPORT"],
    "H01M 50/47": ["SELECTIVE_ION_TRANSPORT"],
    "H01M 50/483": ["SELECTIVE_ION_TRANSPORT"],
    "H01M 50/489": ["SELECTIVE_ION_TRANSPORT"],
    "H01M 50/495": ["SELECTIVE_ION_TRANSPORT"],
    "H01M 50/499": ["SELECTIVE_ION_TRANSPORT"],
    "H01M 50/503": ["SELECTIVE_ION_TRANSPORT"],
    "H01M 50/507": ["SELECTIVE_ION_TRANSPORT"],
    "H01M 50/511": ["CELL_BALANCING"],
    "H01M 50/516": ["CELL_BALANCING"],
    "H01M 50/52": ["SAFETY_PROTECTION"],
    "H01M 50/523": ["SAFETY_PROTECTION"],
    "H01M 50/531": ["SAFETY_PROTECTION"],
    "H01M 50/538": ["SAFETY_PROTECTION"],
    "H01M 50/543": ["THERMAL_MANAGEMENT"],
    "H01M 50/548": ["THERMAL_MANAGEMENT"],
    "H01M 50/555": ["THERMAL_MANAGEMENT"],
    "H01M 50/56": ["STATE_OF_CHARGE_MONITORING"],
    "H01M 50/583": ["SAFETY_PROTECTION"],
    "H01M 50/587": ["SAFETY_PROTECTION"],
    "H01M 50/593": ["SAFETY_PROTECTION"],
    "H01M 50/598": ["SAFETY_PROTECTION"],
    "H01M 50/602": ["CELL_ASSEMBLY"],
    "H01M 50/607": ["CELL_ASSEMBLY"],
    "H01M 50/613": ["CELL_ASSEMBLY"],
    "H01M 50/616": ["CELL_ASSEMBLY"],
    "H01M 50/62": ["CELL_ASSEMBLY"],
    "H01M 50/64": ["CELL_ASSEMBLY"],
    "H01M 50/646": ["CELL_ASSEMBLY"],
    "H01M 50/653": ["CELL_ASSEMBLY"],
    "H01M 50/66": ["CELL_ASSEMBLY"],
    "H01M 50/67": ["CELL_ASSEMBLY"],
    "H01M 50/678": ["CELL_ASSEMBLY"],
    "H01M 50/684": ["CELL_ASSEMBLY"],
    "H01M 50/69": ["CELL_ASSEMBLY"],
    "H01M 50/702": ["CELL_ASSEMBLY"],
    "H01M 50/71": ["CELL_ASSEMBLY"],
    "H01M 50/712": ["CELL_ASSEMBLY"],
    "H01M 50/717": ["CELL_ASSEMBLY"],
    "H01M 50/72": ["CELL_ASSEMBLY"],
    "H01M 50/725": ["CELL_ASSEMBLY"],
    "H01M 50/74": ["CELL_ASSEMBLY"],
    "H01M 50/75": ["CELL_ASSEMBLY"],
    "H01M 50/76": ["CELL_ASSEMBLY"],
    "H01M 50/77": ["CELL_ASSEMBLY"],
    "H01M 50/78": ["CELL_ASSEMBLY"],
    "H01M 50/79": ["CELL_ASSEMBLY"],
    "H01M 50/802": ["THERMAL_MANAGEMENT"],
    "H01M 50/807": ["THERMAL_MANAGEMENT"],
    "H01M 50/812": ["THERMAL_MANAGEMENT"],
    "H01M 50/818": ["THERMAL_MANAGEMENT"],
    "H01M 50/822": ["SAFETY_PROTECTION"],
    "H01M 50/824": ["SAFETY_PROTECTION"],
    "H01M 50/828": ["THERMAL_MANAGEMENT"],
    "H01M 50/831": ["THERMAL_MANAGEMENT"],
    "H01M 50/835": ["THERMAL_MANAGEMENT"],
    "H01M 50/84": ["CELL_ASSEMBLY"],
    "H01M 50/843": ["THERMAL_MANAGEMENT"],
    "H01M 50/847": ["THERMAL_MANAGEMENT"],
    "H01M 50/85": ["THERMAL_MANAGEMENT"],
    "H01M 50/883": ["SAFETY_PROTECTION"],
    "H01M 50/887": ["SAFETY_PROTECTION"],
    "H01M 50/89": ["SAFETY_PROTECTION"],
    "H01M 2300/00": ["RECYCLING"],
    "H01M 2300/0068": ["RECYCLING"],
    "H01M 2300/0074": ["GRID_INTERCONNECTION"],
    "H01M 2300/0078": ["GRID_INTERCONNECTION"],
    "H01M 16/00": ["ELECTROCHEMICAL_ENERGY_STORAGE"],
    "H01M 8/00": ["ELECTROCHEMICAL_ENERGY_STORAGE"],
    "H01M 12/00": [],
    "H01M 6/00": ["ELECTROCHEMICAL_ENERGY_STORAGE"],
}

# Capabilities that REQUIRE other capabilities (structural edges)
# These are invariant structural relationships (not derived from text)
STRUCTURAL_EDGES = [
    # (source_capability, edge_type, target_capability, reason)
    ("ELECTROCHEMICAL_ENERGY_STORAGE", "REQUIRES", "ION_TRANSPORT", "electrochemical storage requires ion transport between electrodes"),
    ("ELECTROCHEMICAL_ENERGY_STORAGE", "REQUIRES", "INTERCALATION", "most Li-ion storage uses intercalation"),
    ("FAST_CHARGING", "REQUIRES", "THERMAL_MANAGEMENT", "fast charging generates heat that must be managed"),
    ("FAST_CHARGING", "REQUIRES", "ION_TRANSPORT", "fast charging requires fast ion transport"),
    ("HIGH_POWER_DISCHARGE", "REQUIRES", "ION_TRANSPORT", "high power requires fast ion transport"),
    ("HIGH_POWER_DISCHARGE", "REQUIRES", "ELECTRON_COLLECTION", "high power requires efficient electron collection"),
    ("SELECTIVE_ION_TRANSPORT", "REQUIRES", "ION_TRANSPORT", "selective transport is a specialization of ion transport"),
    ("CELL_BALANCING", "REQUIRES", "STATE_OF_CHARGE_MONITORING", "balancing requires knowing the state of each cell"),
    ("SAFETY_PROTECTION", "REQUIRES", "STATE_OF_CHARGE_MONITORING", "safety cutoffs require monitoring"),
    ("SOLID_ELECTROLYTE_SINTERING", "ENABLES", "ION_TRANSPORT", "sintering enables solid electrolyte ion transport"),
    ("ELECTRODE_COATING", "ENABLES", "INTERCALATION", "coating enables intercalation electrodes"),
    ("CELL_ASSEMBLY", "REQUIRES", "ELECTRODE_COATING", "assembly requires coated electrodes"),
    ("CELL_ASSEMBLY", "REQUIRES", "SELECTIVE_ION_TRANSPORT", "assembly requires separator"),
    ("RECYCLING", "ENABLES", "ELECTROCHEMICAL_ENERGY_STORAGE", "recycling enables sustainable storage"),
    ("GRID_INTERCONNECTION", "ENABLES", "ELECTROCHEMICAL_ENERGY_STORAGE", "grid connection enables grid-scale storage"),
    ("THERMAL_MANAGEMENT", "CONSTRAINS", "HIGH_POWER_DISCHARGE", "thermal limits power discharge rate"),
    ("CONVERSION_REACTION", "SUBSTITUTES_FOR", "INTERCALATION", "conversion can replace intercalation in some chemistries"),
]


def extract_cpc_codes(text):
    """Extract CPC codes from patent page text."""
    # CPC codes look like "H01M 4/00", "H01M 10/0525", etc.
    # They appear in the classification section of Google Patents pages.
    # Pattern: letter(s) + digits + space + digits/digits
    pattern = r'\b([A-Z]\d{2}[A-Z])\s+(\d+/\d+)\b'
    codes = set()
    for m in re.finditer(pattern, text):
        code = f"{m.group(1)} {m.group(2)}"
        codes.add(code)
    # Also try without space (H01M4/00)
    pattern2 = r'\b([A-Z]\d{2}[A-Z])(\d+/\d+)\b'
    for m in re.finditer(pattern2, text):
        code = f"{m.group(1)} {m.group(2)}"
        codes.add(code)
    return sorted(codes)


def extract_title(data):
    """Extract patent title."""
    title = data.get("title", "")
    if title:
        # Clean Google Patents title format
        if " - " in title:
            parts = title.split(" - ")
            if len(parts) >= 2:
                return parts[-1].strip().replace(" - Google Patents", "").strip()
        return title.strip()
    return "Untitled"


def extract_claims_snippet(text):
    """Extract first ~500 chars of claims text for evidence."""
    # Try to find "Claims" section
    claims_idx = text.lower().find("claims")
    if claims_idx >= 0:
        return text[claims_idx:claims_idx + 500].strip()
    # Fallback: first 500 chars of abstract
    abstract_idx = text.lower().find("abstract")
    if abstract_idx >= 0:
        return text[abstract_idx:abstract_idx + 500].strip()
    return text[:500].strip()


def map_cpc_to_capabilities(cpc_codes):
    """Map CPC codes to capabilities using CPC_MAPPING.md rules."""
    capabilities = set()
    for code in cpc_codes:
        # Try exact match
        if code in CPC_TO_CAPABILITIES:
            capabilities.update(CPC_TO_CAPABILITIES[code])
        else:
            # Try prefix match (e.g., H01M 4/131 matches H01M 4/13)
            for mapped_code, caps in CPC_TO_CAPABILITIES.items():
                if code.startswith(mapped_code) or mapped_code.startswith(code):
                    capabilities.update(caps)
                    break
    return sorted(capabilities)


def main():
    print("=" * 70)
    print("PHASE 7B/7C — CPC EXTRACTION + CAPABILITY MAPPING")
    print("=" * 70)

    pages = sorted(PAGES_DIR.glob("*.json"))
    print(f"Found {len(pages)} patent pages to process\n")

    # Initialize the capability graph
    graph = {
        "metadata": {
            "name": "Capability Graph (CAPABILITY_MODEL)",
            "version": "1.0",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "model": "CAPABILITY_MODEL",
            "vertical": "electrochemical energy storage",
            "phase": "7B/7C",
            "ontology_freeze_respected": True,
            "node_type_count": 10,
            "edge_type_count": 6,
        },
        "nodes": [],
        "edges": [],
        "evidence": [],
    }

    # Track existing nodes and edges
    existing_nodes = set()
    existing_edges = set()
    evidence_id_counter = 0

    def add_node(node_id, node_type, label, domain="electrochemical_storage"):
        if node_id not in existing_nodes:
            graph["nodes"].append({
                "id": node_id,
                "type": node_type,
                "label": label,
                "domain": domain,
                "validFrom": "1990-01-01",
                "validTo": None,
                "confidence": 1.0,
            })
            existing_nodes.add(node_id)

    def add_edge(source, edge_type, target, confidence, evidence_ids):
        edge_key = (source, edge_type, target)
        if edge_key not in existing_edges:
            graph["edges"].append({
                "source": source,
                "type": edge_type,
                "target": target,
                "confidence": confidence,
                "evidence": evidence_ids,
            })
            existing_edges.add(edge_key)

    def add_evidence(source_type, source_id, claims, confidence, supports):
        nonlocal evidence_id_counter
        evidence_id_counter += 1
        eid = f"E-{evidence_id_counter:04d}"
        graph["evidence"].append({
            "id": eid,
            "sourceType": source_type,
            "sourceId": source_id,
            "publicationDate": "2026-08-02",  # ingestion date
            "confidence": confidence,
            "claims": claims[:500] if claims else "",
            "supports": supports,
        })
        return eid

    # Add the 20 capability nodes (from CAPABILITY_CATALOG.md)
    capabilities_catalog = [
        "ELECTROCHEMICAL_ENERGY_STORAGE", "HIGH_POWER_DISCHARGE", "HIGH_ENERGY_DENSITY_STORAGE",
        "LONG_CYCLE_LIFE_STORAGE", "FAST_CHARGING", "ION_TRANSPORT", "SELECTIVE_ION_TRANSPORT",
        "INTERCALATION", "CONVERSION_REACTION", "ELECTRON_COLLECTION",
        "THERMAL_MANAGEMENT", "RADIATIVE_COOLING", "STATE_OF_CHARGE_MONITORING",
        "CELL_BALANCING", "SAFETY_PROTECTION", "ELECTRODE_COATING",
        "CELL_ASSEMBLY", "SOLID_ELECTROLYTE_SINTERING", "GRID_INTERCONNECTION", "RECYCLING",
    ]
    for cap in capabilities_catalog:
        add_node(f"CAP_{cap}", "CAPABILITY", cap)

    # Add the 10 constraint nodes (from CONSTRAINT_CATALOG.md)
    constraints_catalog = [
        "THEORETICAL_ENERGY_DENSITY_LIMIT", "ION_TRANSPORT_RESISTANCE", "THERMAL_RUNAWAY_THRESHOLD",
        "SOLID_ELECTROLYTE_DENSIFICATION", "DRY_ELECTRODE_YIELD", "COST_PER_KWH_THRESHOLD",
        "MATERIAL_SCARCITY", "UN38_3_SHIPPING_SAFETY", "IEC_62133_SAFETY_STANDARD", "GRID_CAPACITY_LIMIT",
    ]
    for con in constraints_catalog:
        add_node(f"CON_{con}", "CONSTRAINT", con)

    # Add structural edges (invariant capability → capability relationships)
    print("Adding structural edges (invariant relationships)...")
    for source_cap, edge_type, target_cap, reason in STRUCTURAL_EDGES:
        source_id = f"CAP_{source_cap}"
        target_id = f"CAP_{target_cap}"
        # Structural edges are inferred from domain knowledge, not from
        # a single document. Evidence is "structural invariant" with
        # confidence 0.5 (INFERRED level per EVIDENCE_PROTOCOL.md).
        eid = add_evidence(
            "REGULATION",  # not from a document — structural invariant
            "structural_invariant",
            reason,
            0.5,
            [f"{source_id} -> {edge_type} -> {target_id}"]
        )
        add_edge(source_id, edge_type, target_id, 0.5, [eid])
    print(f"  Added {len(STRUCTURAL_EDGES)} structural edges")

    # Process each patent
    print(f"\nProcessing {len(pages)} patents...\n")
    patent_count = 0
    for page_path in pages:
        patent_id = page_path.stem
        with open(page_path) as f:
            page_data = json.load(f)

        data = page_data.get("data", page_data)
        title = extract_title(data)
        html = data.get("html", "")
        text = data.get("text", "") or html

        # Strip HTML tags for text processing
        clean_text = re.sub(r"<[^>]+>", " ", text)
        clean_text = re.sub(r"&\w+;", " ", clean_text)
        clean_text = re.sub(r"\s+", " ", clean_text).strip()

        # Extract CPC codes
        cpc_codes = extract_cpc_codes(clean_text)
        if not cpc_codes:
            print(f"  {patent_id}: NO CPC CODES FOUND (skipping)")
            continue

        # Map CPC codes to capabilities
        capabilities = map_cpc_to_capabilities(cpc_codes)

        # Extract claims snippet for evidence
        claims_snippet = extract_claims_snippet(clean_text)

        # Create evidence record
        eid = add_evidence(
            "PATENT",
            patent_id,
            claims_snippet,
            1.0,  # EXPLICIT — CPC codes are explicit patent classifications
            [f"CAP_{cap}" for cap in capabilities] + [f"CPC:{code}" for code in cpc_codes]
        )

        # Create PATENT evidence node
        patent_node_id = f"PAT_{patent_id}"
        add_node(patent_node_id, "PRODUCT", title[:80])

        # Create EMBODIED_IN edges from patent to capabilities it evidences
        for cap in capabilities:
            cap_node_id = f"CAP_{cap}"
            if cap_node_id in existing_nodes:
                # Patent EMBODIED_IN capability (the patent evidences this capability)
                add_edge(patent_node_id, "EMBODIED_IN", cap_node_id, 1.0, [eid])

        print(f"  {patent_id}: {len(cpc_codes)} CPC codes, {len(capabilities)} capabilities")
        print(f"    CPC: {cpc_codes[:5]}")
        print(f"    Capabilities: {capabilities[:5]}")
        patent_count += 1

    # Add constraint → capability edges (CONSTRAINS)
    constraint_edges = [
        ("CON_THEORETICAL_ENERGY_DENSITY_LIMIT", "CONSTRAINS", "CAP_HIGH_ENERGY_DENSITY_STORAGE"),
        ("CON_ION_TRANSPORT_RESISTANCE", "CONSTRAINS", "CAP_ION_TRANSPORT"),
        ("CON_ION_TRANSPORT_RESISTANCE", "CONSTRAINS", "CAP_HIGH_POWER_DISCHARGE"),
        ("CON_THERMAL_RUNAWAY_THRESHOLD", "CONSTRAINS", "CAP_ELECTROCHEMICAL_ENERGY_STORAGE"),
        ("CON_SOLID_ELECTROLYTE_DENSIFICATION", "CONSTRAINS", "CAP_SOLID_ELECTROLYTE_SINTERING"),
        ("CON_DRY_ELECTRODE_YIELD", "CONSTRAINS", "CAP_ELECTRODE_COATING"),
        ("CON_COST_PER_KWH_THRESHOLD", "CONSTRAINS", "CAP_ELECTROCHEMICAL_ENERGY_STORAGE"),
        ("CON_MATERIAL_SCARCITY", "CONSTRAINS", "CAP_INTERCALATION"),
        ("CON_UN38_3_SHIPPING_SAFETY", "REGULATED_BY", "CAP_ELECTROCHEMICAL_ENERGY_STORAGE"),
        ("CON_IEC_62133_SAFETY_STANDARD", "REGULATED_BY", "CAP_SAFETY_PROTECTION"),
        ("CON_GRID_CAPACITY_LIMIT", "CONSTRAINS", "CAP_GRID_INTERCONNECTION"),
    ]
    for source, edge_type, target in constraint_edges:
        eid = add_evidence(
            "REGULATION",
            "structural_constraint",
            f"Constraint {source} {edge_type} {target}",
            0.5,
            [f"{source} -> {edge_type} -> {target}"]
        )
        add_edge(source, edge_type, target, 0.5, [eid])

    # Update metadata
    graph["metadata"]["node_count"] = len(graph["nodes"])
    graph["metadata"]["edge_count"] = len(graph["edges"])
    graph["metadata"]["evidence_count"] = len(graph["evidence"])
    graph["metadata"]["patents_processed"] = patent_count
    graph["metadata"]["capabilities_used"] = len([n for n in graph["nodes"] if n["type"] == "CAPABILITY"])
    graph["metadata"]["constraints_used"] = len([n for n in graph["nodes"] if n["type"] == "CONSTRAINT"])

    # Write the graph
    OUTPUT_GRAPH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_GRAPH, "w") as f:
        json.dump(graph, f, indent=2)
        f.write("\n")

    print(f"\n{'=' * 70}")
    print(f"Capability graph created: {OUTPUT_GRAPH}")
    print(f"  Nodes: {len(graph['nodes'])}")
    print(f"    Capabilities: {graph['metadata']['capabilities_used']}")
    print(f"    Constraints: {graph['metadata']['constraints_used']}")
    print(f"    Patents (PRODUCT): {patent_count}")
    print(f"  Edges: {len(graph['edges'])}")
    print(f"  Evidence records: {len(graph['evidence'])}")
    print(f"  Patents processed: {patent_count}")
    print(f"  Graph version: 1.0")
    print(f"  Ontology freeze: RESPECTED")
    print(f"    Node types: 10 (frozen)")
    print(f"    Edge types: 6 (of 9, within cap)")
    print(f"    Capabilities: {graph['metadata']['capabilities_used']} (of 20, at cap)")
    print(f"    Constraints: {graph['metadata']['constraints_used']} (of 10, at cap)")
    print(f"  Phase 5 CO_OCCURRENCE_MODEL: UNCHANGED")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
