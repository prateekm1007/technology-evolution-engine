#!/usr/bin/env python3
"""
Phase 7C.1 — Build the TRUSTED capability graph (v2.0).

5 patents. 10 capabilities. 5 constraints. 4 edge types.
Every edge has an EdgeJustification (edgeId, sourcePatent, cpcCode,
sourceNode, targetNode, relationship, justification, reviewer, confidence).

NO ENABLES. NO SUBSTITUTES_FOR. Only:
  EMBODIED_IN, REQUIRES, CONSTRAINS, REGULATED_BY.

Per CEO Phase 7C.1:
> The objective is now: 'Can we trust the graph?'

One-off builder. NOT a module. NOT imported by anything.
"""
import json
import pathlib
from datetime import datetime, timezone

ROOT = pathlib.Path("/home/z/my-project/audit/repo")
OUTPUT = ROOT / "data" / "capability_graph.json"
JUSTIFICATIONS_OUTPUT = ROOT / "evidence" / "observations" / "EDGE_JUSTIFICATION_TABLE.md"

# ─── The 5 patents (selected from 15 fetched, diverse H01M subclasses) ───
PATENTS = [
    {
        "id": "US20240194939A1",
        "title": "All-solid-state battery",
        "cpc_codes": ["H01M 10/0562", "H01M 10/0525", "H01M 4/00", "H01M 50/00"],
    },
    {
        "id": "US12489120B2",
        "title": "Redox flow battery",
        "cpc_codes": ["H01M 4/86", "H01M 2300/00", "H01M 10/00"],
    },
    {
        "id": "US20240021793A1",
        "title": "Lithium ion battery and powered vehicle",
        "cpc_codes": ["H01M 10/0525", "H01M 10/44", "H01M 50/00"],
    },
    {
        "id": "WO2012068732A1",
        "title": "Battery pack assembly",
        "cpc_codes": ["H01M 50/00", "H01M 10/42", "H01M 10/48"],
    },
    {
        "id": "WO2015119843A1",
        "title": "High performance lithium battery electrodes by self-assembly processing",
        "cpc_codes": ["H01M 4/00", "H01M 10/0525"],
    },
]

# ─── The 10 capabilities (reduced from 20 per CEO 7C.1) ───
CAPABILITIES = [
    "ELECTROCHEMICAL_ENERGY_STORAGE",
    "ION_TRANSPORT",
    "INTERCALATION",
    "ELECTRON_COLLECTION",
    "FAST_CHARGING",
    "THERMAL_MANAGEMENT",
    "STATE_OF_CHARGE_MONITORING",
    "SAFETY_PROTECTION",
    "ELECTRODE_COATING",
    "CELL_ASSEMBLY",
]

# ─── The 5 constraints (reduced from 10 per CEO 7C.1) ───
CONSTRAINTS = [
    "THEORETICAL_ENERGY_DENSITY_LIMIT",
    "THERMAL_RUNAWAY_THRESHOLD",
    "COST_PER_KWH_THRESHOLD",
    "UN38_3_SHIPPING_SAFETY",
    "IEC_62133_SAFETY_STANDARD",
]

# ─── CPC → Capability mapping (reduced) ───
CPC_TO_CAPS = {
    "H01M 4/00":   ["INTERCALATION", "ELECTRON_COLLECTION", "ELECTRODE_COATING"],
    "H01M 4/86":   ["ELECTRON_COLLECTION"],
    "H01M 10/00":  ["ELECTROCHEMICAL_ENERGY_STORAGE"],
    "H01M 10/42":  ["ELECTROCHEMICAL_ENERGY_STORAGE"],
    "H01M 10/44":  ["FAST_CHARGING"],
    "H01M 10/48":  ["STATE_OF_CHARGE_MONITORING", "SAFETY_PROTECTION"],
    "H01M 10/0525": ["ELECTROCHEMICAL_ENERGY_STORAGE", "ION_TRANSPORT"],
    "H01M 10/0562": ["ION_TRANSPORT"],
    "H01M 50/00":  ["CELL_ASSEMBLY", "THERMAL_MANAGEMENT"],
    "H01M 2300/00": ["ELECTROCHEMICAL_ENERGY_STORAGE"],
}

# ─── Structural REQUIRES edges (only physical necessities, confidence 0.5) ───
# Per CAUSALITY_POLICY.md: only admissible when the relationship is a
# physical necessity (not merely common practice).
STRUCTURAL_REQUIRES = [
    {
        "source": "ELECTROCHEMICAL_ENERGY_STORAGE",
        "target": "ION_TRANSPORT",
        "justification": "Electrochemical storage requires ions to move between electrodes; without ion transport, the electrochemical reaction cannot occur. This is a physical necessity, not a convention.",
    },
    {
        "source": "ELECTROCHEMICAL_ENERGY_STORAGE",
        "target": "INTERCALATION",
        "justification": "Li-ion electrochemical storage (the dominant chemistry in this corpus) requires intercalation — ions must insert into and remove from electrode lattices. NOTE: this is specific to intercalation-based chemistries, not universal (conversion reactions exist). Confidence reduced to 0.5 accordingly.",
    },
    {
        "source": "FAST_CHARGING",
        "target": "ION_TRANSPORT",
        "justification": "Fast charging requires ions to move rapidly between electrodes; the C-rate is limited by ion transport kinetics. This is a physical necessity of the charge process.",
    },
    {
        "source": "FAST_CHARGING",
        "target": "THERMAL_MANAGEMENT",
        "justification": "Fast charging generates heat due to internal resistance (Joule heating). Without thermal management, the cell temperature rises beyond safe limits. This is a physical necessity at high C-rates, though not at low C-rates.",
    },
    {
        "source": "CELL_ASSEMBLY",
        "target": "ELECTRODE_COATING",
        "justification": "Cell assembly requires coated electrodes; the electrode coating process produces the functional electrode that is then assembled into a cell. This is a manufacturing necessity, not a convention.",
    },
    {
        "source": "SAFETY_PROTECTION",
        "target": "STATE_OF_CHARGE_MONITORING",
        "justification": "Safety protection systems (e.g., overcharge cutoff) require knowing the cell's state of charge; without monitoring, the safety system cannot determine when to intervene. This is a functional necessity.",
    },
]

# ─── CONSTRAINS edges (constraint → capability, confidence 0.5) ───
CONSTRAINT_EDGES = [
    {"constraint": "THEORETICAL_ENERGY_DENSITY_LIMIT", "capability": "ELECTROCHEMICAL_ENERGY_STORAGE",
     "justification": "The theoretical energy density of electrochemical chemistries (e.g., ~400 Wh/kg for Li-ion) limits the maximum energy a cell can store. This is a physics limit, not an engineering limit."},
    {"constraint": "THERMAL_RUNAWAY_THRESHOLD", "capability": "ELECTROCHEMICAL_ENERGY_STORAGE",
     "justification": "If cell temperature exceeds ~150°C, thermal runaway occurs — an uncontrollable exothermic reaction. This constrains the operating envelope of electrochemical storage."},
    {"constraint": "COST_PER_KWH_THRESHOLD", "capability": "ELECTROCHEMICAL_ENERGY_STORAGE",
     "justification": "The cost per kWh must be below the market threshold (~$100/kWh for EVs) for the storage to be economically viable. This constrains which chemistries and manufacturing processes are deployable."},
    {"constraint": "UN38_3_SHIPPING_SAFETY", "capability": "ELECTROCHEMICAL_ENERGY_STORAGE",
     "justification": "UN38.3 requires batteries to pass specific safety tests before transport. Batteries that fail cannot be shipped commercially. This regulation constrains the deployment of electrochemical storage."},
    {"constraint": "IEC_62133_SAFETY_STANDARD", "capability": "SAFETY_PROTECTION",
     "justification": "IEC 62133 specifies safety requirements for secondary cells. Safety protection systems must comply with this standard for consumer products. This regulation governs safety protection capabilities."},
]

# ─── REGULATED_BY edges (capability → regulation, confidence 1.0) ───
# Note: these are the same as CONSTRAINS but from the capability's perspective
# — the capability is REGULATED_BY the regulation. We model them as REGULATED_BY
# (not CONSTRAINS) because the regulation explicitly governs the capability.
REGULATED_BY_EDGES = [
    {"capability": "ELECTROCHEMICAL_ENERGY_STORAGE", "regulation": "UN38_3_SHIPPING_SAFETY",
     "justification": "UN38.3 is a UN standard that explicitly regulates the transport of lithium batteries. Patent US20240021793A1 and US20240194939A1 both fall under this regulation. The regulation is explicit and externally validated."},
    {"capability": "SAFETY_PROTECTION", "regulation": "IEC_62133_SAFETY_STANDARD",
     "justification": "IEC 62133 is an international standard that explicitly governs safety requirements for secondary cells containing alkaline or other non-acid electrolytes. Safety protection systems must comply."},
]


def main():
    print("=" * 70)
    print("PHASE 7C.1 — TRUSTED CAPABILITY GRAPH (v2.0)")
    print("5 patents | 10 capabilities | 5 constraints | 4 edge types")
    print("Every edge has an EdgeJustification")
    print("=" * 70)

    graph = {
        "metadata": {
            "name": "Capability Graph (CAPABILITY_MODEL) — Trusted v2.0",
            "version": "2.0",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "model": "CAPABILITY_MODEL",
            "vertical": "electrochemical energy storage",
            "phase": "7C.1",
            "scope": {
                "patents": 5,
                "capabilities": 10,
                "constraints": 5,
                "edge_types_authorized": ["EMBODIED_IN", "REQUIRES", "CONSTRAINS", "REGULATED_BY"],
                "edge_types_suspended": ["ENABLES", "SUBSTITUTES_FOR"],
            },
            "ontology_freeze": "RESPECTED (reduced caps per CEO 7C.1)",
            "trust_framework": "CAUSALITY_POLICY.md",
        },
        "nodes": [],
        "edges": [],
        "edge_justifications": [],
    }

    edge_counter = 0
    evidence_counter = 0

    def make_edge_id():
        nonlocal edge_counter
        edge_counter += 1
        return f"EDGE-{edge_counter:03d}"

    def add_justification(edge_id, source_patent, cpc_code, source_node, target_node,
                          relationship, justification, reviewer, confidence):
        graph["edge_justifications"].append({
            "edgeId": edge_id,
            "sourcePatent": source_patent,
            "cpcCode": cpc_code,
            "sourceNode": source_node,
            "targetNode": target_node,
            "relationship": relationship,
            "justification": justification,
            "reviewer": reviewer,
            "confidence": confidence,
        })

    # ─── Add 10 capability nodes ───
    print("\n--- Adding 10 capability nodes ---")
    for cap in CAPABILITIES:
        graph["nodes"].append({
            "id": f"CAP_{cap}",
            "type": "CAPABILITY",
            "label": cap,
            "domain": "electrochemical_storage",
            "validFrom": "1990-01-01",
            "validTo": None,
            "confidence": 1.0,
        })
    print(f"  Added {len(CAPABILITIES)} capability nodes")

    # ─── Add 5 constraint nodes ───
    print("\n--- Adding 5 constraint nodes ---")
    for con in CONSTRAINTS:
        graph["nodes"].append({
            "id": f"CON_{con}",
            "type": "CONSTRAINT",
            "label": con,
            "domain": "electrochemical_storage",
            "validFrom": "1990-01-01",
            "validTo": None,
            "confidence": 1.0,
        })
    print(f"  Added {len(CONSTRAINTS)} constraint nodes")

    # ─── Add 5 patent (PRODUCT) nodes ───
    print("\n--- Adding 5 patent nodes ---")
    for pat in PATENTS:
        graph["nodes"].append({
            "id": f"PAT_{pat['id']}",
            "type": "PRODUCT",
            "label": pat["title"][:80],
            "domain": "electrochemical_storage",
            "validFrom": "2026-08-02",
            "validTo": None,
            "confidence": 1.0,
            "cpcCodes": pat["cpc_codes"],
        })
    print(f"  Added {len(PATENTS)} patent nodes")

    # ─── Add EMBODIED_IN edges (patent → capability, confidence 1.0) ───
    print("\n--- Adding EMBODIED_IN edges (patent → capability) ---")
    for pat in PATENTS:
        caps_for_patent = set()
        for cpc in pat["cpc_codes"]:
            if cpc in CPC_TO_CAPS:
                caps_for_patent.update(CPC_TO_CAPS[cpc])

        for cap in sorted(caps_for_patent):
            if cap in CAPABILITIES:  # only include capabilities in the reduced catalog
                edge_id = make_edge_id()
                source = f"PAT_{pat['id']}"
                target = f"CAP_{cap}"
                # Find which CPC code maps to this capability
                cpc_used = next((c for c in pat["cpc_codes"] if cap in CPC_TO_CAPS.get(c, [])), "unknown")

                graph["edges"].append({
                    "id": edge_id,
                    "source": source,
                    "type": "EMBODIED_IN",
                    "target": target,
                    "confidence": 1.0,
                })
                add_justification(
                    edge_id,
                    pat["id"],
                    cpc_used,
                    source,
                    target,
                    "EMBODIED_IN",
                    f"Patent {pat['id']} has CPC code {cpc_used}, which maps to {cap} per CPC_MAPPING.md. CPC codes are assigned by USPTO patent examiners and are externally validated.",
                    "coder_agent_001 / 2026-08-02",
                    1.0,
                )
                print(f"  {edge_id}: {pat['id']} → EMBODIED_IN → {cap} (CPC: {cpc_used}, conf: 1.0)")

    # ─── Add REQUIRES edges (structural, confidence 0.5) ───
    print("\n--- Adding REQUIRES edges (structural invariants) ---")
    for req in STRUCTURAL_REQUIRES:
        edge_id = make_edge_id()
        source = f"CAP_{req['source']}"
        target = f"CAP_{req['target']}"

        graph["edges"].append({
            "id": edge_id,
            "source": source,
            "type": "REQUIRES",
            "target": target,
            "confidence": 0.5,
        })
        add_justification(
            edge_id,
            "structural_invariant",
            "N/A (structural)",
            source,
            target,
            "REQUIRES",
            req["justification"],
            "coder_agent_001 / 2026-08-02",
            0.5,
        )
        print(f"  {edge_id}: {req['source']} → REQUIRES → {req['target']} (conf: 0.5)")

    # ─── Add CONSTRAINS edges (constraint → capability, confidence 0.5) ───
    print("\n--- Adding CONSTRAINS edges ---")
    for ce in CONSTRAINT_EDGES:
        edge_id = make_edge_id()
        source = f"CON_{ce['constraint']}"
        target = f"CAP_{ce['capability']}"

        graph["edges"].append({
            "id": edge_id,
            "source": source,
            "type": "CONSTRAINS",
            "target": target,
            "confidence": 0.5,
        })
        add_justification(
            edge_id,
            "structural_constraint",
            "N/A (structural)",
            source,
            target,
            "CONSTRAINS",
            ce["justification"],
            "coder_agent_001 / 2026-08-02",
            0.5,
        )
        print(f"  {edge_id}: {ce['constraint']} → CONSTRAINS → {ce['capability']} (conf: 0.5)")

    # ─── Add REGULATED_BY edges (capability → regulation, confidence 1.0) ───
    print("\n--- Adding REGULATED_BY edges ---")
    for rb in REGULATED_BY_EDGES:
        edge_id = make_edge_id()
        source = f"CAP_{rb['capability']}"
        target = f"CON_{rb['regulation']}"

        graph["edges"].append({
            "id": edge_id,
            "source": source,
            "type": "REGULATED_BY",
            "target": target,
            "confidence": 1.0,
        })
        add_justification(
            edge_id,
            "regulation",
            "N/A (regulation)",
            source,
            target,
            "REGULATED_BY",
            rb["justification"],
            "coder_agent_001 / 2026-08-02",
            1.0,
        )
        print(f"  {edge_id}: {rb['capability']} → REGULATED_BY → {rb['regulation']} (conf: 1.0)")

    # ─── Verify ───
    print(f"\n{'=' * 70}")
    print("VERIFICATION")
    print(f"{'=' * 70}")

    # Check: every edge has a justification
    edges_with_just = set(ej["edgeId"] for ej in graph["edge_justifications"])
    edges_without = [e for e in graph["edges"] if e["id"] not in edges_with_just]
    print(f"Edges without justification: {len(edges_without)}")
    assert len(edges_without) == 0, "VIOLATION: edges without justification!"

    # Check: no suspended edge types
    suspended = [e for e in graph["edges"] if e["type"] in ("ENABLES", "SUBSTITUTES_FOR")]
    print(f"Suspended edge types used: {len(suspended)}")
    assert len(suspended) == 0, "VIOLATION: suspended edge types used!"

    # Check: ontology freeze
    from collections import Counter
    node_types = Counter(n["type"] for n in graph["nodes"])
    edge_types = Counter(e["type"] for e in graph["edges"])
    caps = node_types.get("CAPABILITY", 0)
    cons = node_types.get("CONSTRAINT", 0)
    print(f"Node types: {len(node_types)} (cap: 10)")
    print(f"Edge types: {len(edge_types)} (cap: 4)")
    print(f"Capabilities: {caps} (cap: 10)")
    print(f"Constraints: {cons} (cap: 5)")
    assert len(edge_types) <= 4, "ONTOLOGY_FREEZE VIOLATION"
    assert caps <= 10, "ONTOLOGY_FREEZE VIOLATION"
    assert cons <= 5, "ONTOLOGY_FREEZE VIOLATION"
    print("ALL CAPS RESPECTED ✓")

    # Summary
    print(f"\n{'=' * 70}")
    print(f"TRUSTED CAPABILITY GRAPH (v2.0)")
    print(f"{'=' * 70}")
    print(f"  Nodes: {len(graph['nodes'])}")
    print(f"    Capabilities: {caps}")
    print(f"    Constraints: {cons}")
    print(f"    Patents (PRODUCT): {node_types.get('PRODUCT', 0)}")
    print(f"  Edges: {len(graph['edges'])}")
    for et, count in sorted(edge_types.items(), key=lambda x: -x[1]):
        print(f"    {et}: {count}")
    print(f"  Edge justifications: {len(graph['edge_justifications'])}")
    print(f"  Every edge justified: {'YES' if len(edges_without) == 0 else 'NO'}")
    print(f"  Suspended types used: NONE")
    print(f"  Ontology freeze: RESPECTED")

    # Write graph
    with open(OUTPUT, "w") as f:
        json.dump(graph, f, indent=2)
        f.write("\n")
    print(f"\n  Written to: {OUTPUT}")

    # Write human-readable justification table
    just_lines = [
        "# EDGE_JUSTIFICATION_TABLE — Phase 7C.1 Trusted Graph (v2.0)",
        "",
        "**Status:** every edge justified per CEO Phase 7C.1 Decision 4.",
        "**Graph:** capability_graph.json v2.0 (5 patents, 10 capabilities, 5 constraints, 4 edge types).",
        "",
        f"Total edges: {len(graph['edges'])}",
        f"Total justifications: {len(graph['edge_justifications'])}",
        "",
        "| Edge ID | Source | → | Target | Type | CPC Code | Confidence | Justification | Reviewer |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for ej in graph["edge_justifications"]:
        just_text = ej["justification"][:120].replace("|", "\\|")
        just_lines.append(
            f"| {ej['edgeId']} | {ej['sourceNode']} | → | {ej['targetNode']} | "
            f"{ej['relationship']} | {ej['cpcCode']} | {ej['confidence']} | "
            f"{just_text} | {ej['reviewer']} |"
        )
    just_lines.append("")
    just_lines.append("Every edge has an EdgeJustification. No ENABLES. No SUBSTITUTES_FOR.")
    just_lines.append("The question is: can we trust each edge?")

    with open(JUSTIFICATIONS_OUTPUT, "w") as f:
        f.write("\n".join(just_lines))
    print(f"  Justification table: {JUSTIFICATIONS_OUTPUT}")


if __name__ == "__main__":
    main()
