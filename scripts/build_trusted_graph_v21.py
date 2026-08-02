#!/usr/bin/env python3
"""
Phase 7C.2 — Trusted capability graph v2.1.

Four CEO corrections applied:
1. Evidence edges separated from structural edges (different schemas).
2. Numeric confidence replaced with ordinal labels (EXPLICIT/IMPLIED/STRUCTURAL/SPECULATIVE).
3. Structural edges carry a 'principle' field citing the physical principle.
4. Epistemic layer created: evidence/epistemic/{causality,justifications,assumptions}/

5 patents. 10 capabilities. 5 constraints. 4 edge types.
Every edge has an EdgeJustification with ordinal confidence + principle.

One-off builder. NOT a module. NOT imported by anything.
"""
import json
import pathlib
from datetime import datetime, timezone

ROOT = pathlib.Path("/home/z/my-project/audit/repo")
OUTPUT = ROOT / "data" / "capability_graph.json"

PATENTS = [
    {"id": "US20240194939A1", "title": "All-solid-state battery",
     "cpc_codes": ["H01M 10/0562", "H01M 10/0525", "H01M 4/00", "H01M 50/00"]},
    {"id": "US12489120B2", "title": "Redox flow battery",
     "cpc_codes": ["H01M 4/86", "H01M 2300/00", "H01M 10/00"]},
    {"id": "US20240021793A1", "title": "Lithium ion battery and powered vehicle",
     "cpc_codes": ["H01M 10/0525", "H01M 10/44", "H01M 50/00"]},
    {"id": "WO2012068732A1", "title": "Battery pack assembly",
     "cpc_codes": ["H01M 50/00", "H01M 10/42", "H01M 10/48"]},
    {"id": "WO2015119843A1", "title": "High performance lithium battery electrodes by self-assembly processing",
     "cpc_codes": ["H01M 4/00", "H01M 10/0525"]},
]

CAPABILITIES = [
    "ELECTROCHEMICAL_ENERGY_STORAGE", "ION_TRANSPORT", "INTERCALATION",
    "ELECTRON_COLLECTION", "FAST_CHARGING", "THERMAL_MANAGEMENT",
    "STATE_OF_CHARGE_MONITORING", "SAFETY_PROTECTION", "ELECTRODE_COATING",
    "CELL_ASSEMBLY",
]

CONSTRAINTS = [
    "THEORETICAL_ENERGY_DENSITY_LIMIT", "THERMAL_RUNAWAY_THRESHOLD",
    "COST_PER_KWH_THRESHOLD", "UN38_3_SHIPPING_SAFETY",
    "IEC_62133_SAFETY_STANDARD",
]

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

# Structural REQUIRES edges — now with PRINCIPLE field (Correction 3)
STRUCTURAL_REQUIRES = [
    {"source": "ELECTROCHEMICAL_ENERGY_STORAGE", "target": "ION_TRANSPORT",
     "principle": "charge conservation",
     "justification": "Electrochemical storage requires ions to move between electrodes to balance the electron flow in the external circuit. Without ion transport, charge accumulation prevents further reaction."},
    {"source": "ELECTROCHEMICAL_ENERGY_STORAGE", "target": "INTERCALATION",
     "principle": "lattice insertion chemistry (Li-ion specifically)",
     "justification": "Li-ion electrochemical storage (the dominant chemistry in this corpus) requires intercalation — ions insert into and remove from electrode lattices. NOTE: specific to intercalation-based chemistries, not universal."},
    {"source": "FAST_CHARGING", "target": "ION_TRANSPORT",
     "principle": "transport kinetics",
     "justification": "Fast charging requires ions to move rapidly between electrodes. The C-rate is limited by ion transport kinetics in the electrolyte and across interfaces."},
    {"source": "FAST_CHARGING", "target": "THERMAL_MANAGEMENT",
     "principle": "Joule heating (I²R losses)",
     "justification": "Fast charging drives high current, generating heat via internal resistance (Joule heating). Without thermal management, cell temperature exceeds safe limits at high C-rates."},
    {"source": "CELL_ASSEMBLY", "target": "ELECTRODE_COATING",
     "principle": "manufacturing process dependency",
     "justification": "Cell assembly requires coated electrodes. The electrode coating process produces the functional electrode that is then assembled into a cell. This is a manufacturing necessity."},
    {"source": "SAFETY_PROTECTION", "target": "STATE_OF_CHARGE_MONITORING",
     "principle": "feedback control",
     "justification": "Safety protection systems (e.g., overcharge cutoff) require knowing the cell's state of charge. Without monitoring, the safety system cannot determine when to intervene."},
]

CONSTRAINT_EDGES = [
    {"constraint": "THEORETICAL_ENERGY_DENSITY_LIMIT", "capability": "ELECTROCHEMICAL_ENERGY_STORAGE",
     "principle": "thermodynamic energy density ceiling of electrochemical chemistry",
     "justification": "The theoretical energy density of electrochemical chemistries (e.g., ~400 Wh/kg for Li-ion) limits the maximum energy a cell can store. This is a thermodynamic limit, not an engineering limit."},
    {"constraint": "THERMAL_RUNAWAY_THRESHOLD", "capability": "ELECTROCHEMICAL_ENERGY_STORAGE",
     "principle": "exothermic decomposition threshold",
     "justification": "If cell temperature exceeds ~150°C, thermal runaway occurs — an uncontrollable exothermic decomposition reaction. This constrains the operating envelope."},
    {"constraint": "COST_PER_KWH_THRESHOLD", "capability": "ELECTROCHEMICAL_ENERGY_STORAGE",
     "principle": "market price elasticity",
     "justification": "The cost per kWh must be below the market threshold (~$100/kWh for EVs) for the storage to be economically viable. This constrains which chemistries and processes are deployable."},
    {"constraint": "UN38_3_SHIPPING_SAFETY", "capability": "ELECTROCHEMICAL_ENERGY_STORAGE",
     "principle": "transport safety regulation (UN Model Regulations)",
     "justification": "UN38.3 requires batteries to pass specific safety tests before transport. Batteries that fail cannot be shipped commercially. This regulation constrains deployment."},
    {"constraint": "IEC_62133_SAFETY_STANDARD", "capability": "SAFETY_PROTECTION",
     "principle": "product safety standard (IEC 62133)",
     "justification": "IEC 62133 specifies safety requirements for secondary cells. Safety protection systems must comply with this standard for consumer products."},
]

REGULATED_BY_EDGES = [
    {"capability": "ELECTROCHEMICAL_ENERGY_STORAGE", "regulation": "UN38_3_SHIPPING_SAFETY",
     "principle": "UN Model Regulations on the Transport of Dangerous Goods",
     "justification": "UN38.3 is a UN standard that explicitly regulates the transport of lithium batteries. The regulation is explicit and externally validated."},
    {"capability": "SAFETY_PROTECTION", "regulation": "IEC_62133_SAFETY_STANDARD",
     "principle": "IEC 62133 international safety standard",
     "justification": "IEC 62133 is an international standard that explicitly governs safety requirements for secondary cells containing alkaline or other non-acid electrolytes."},
]


def main():
    print("=" * 70)
    print("PHASE 7C.2 — TRUSTED CAPABILITY GRAPH (v2.1)")
    print("4 CEO corrections applied:")
    print("  1. Evidence edges ≠ structural edges (separate schemas)")
    print("  2. Ordinal confidence labels (not numeric)")
    print("  3. Structural edges carry 'principle' field")
    print("  4. Epistemic layer: evidence/epistemic/")
    print("=" * 70)

    graph = {
        "metadata": {
            "name": "Capability Graph (CAPABILITY_MODEL) — Trusted v2.1",
            "version": "2.1",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "model": "CAPABILITY_MODEL",
            "vertical": "electrochemical energy storage",
            "phase": "7C.2",
            "scope": {
                "patents": 5,
                "capabilities": 10,
                "constraints": 5,
                "edge_types_authorized": ["EMBODIED_IN", "REQUIRES", "CONSTRAINS", "REGULATED_BY"],
                "edge_types_suspended": ["ENABLES", "SUBSTITUTES_FOR"],
            },
            "confidence_scale": "ordinal (EXPLICIT / IMPLIED / STRUCTURAL / SPECULATIVE)",
            "corrections_applied": [
                "1. EvidenceEdge vs StructuralEdge separation",
                "2. Ordinal confidence labels (not numeric)",
                "3. Structural edges carry 'principle' field",
                "4. Epistemic layer created",
            ],
        },
        "nodes": [],
        "evidence_edges": [],      # Correction 1: separated from structural
        "structural_edges": [],    # Correction 1: separated from evidence
        "edge_justifications": [],
    }

    edge_counter = 0

    def next_edge_id():
        nonlocal edge_counter
        edge_counter += 1
        return f"EDGE-{edge_counter:03d}"

    # ─── Add nodes ───
    for cap in CAPABILITIES:
        graph["nodes"].append({
            "id": f"CAP_{cap}", "type": "CAPABILITY", "label": cap,
            "domain": "electrochemical_storage", "validFrom": "1990-01-01",
            "validTo": None, "confidence": "EXPLICIT",
        })
    for con in CONSTRAINTS:
        graph["nodes"].append({
            "id": f"CON_{con}", "type": "CONSTRAINT", "label": con,
            "domain": "electrochemical_storage", "validFrom": "1990-01-01",
            "validTo": None, "confidence": "EXPLICIT",
        })
    for pat in PATENTS:
        graph["nodes"].append({
            "id": f"PAT_{pat['id']}", "type": "PRODUCT", "label": pat["title"][:80],
            "domain": "electrochemical_storage", "validFrom": "2026-08-02",
            "validTo": None, "confidence": "EXPLICIT",
            "cpcCodes": pat["cpc_codes"],
        })
    print(f"\nNodes: {len(graph['nodes'])} (10 CAP + 5 CON + 5 PAT)")

    # ─── EVIDENCE EDGES: EMBODIED_IN (patent → capability) ───
    # These are observations — the patent's CPC code evidences the capability.
    print("\n--- Evidence edges (EMBODIED_IN) ---")
    for pat in PATENTS:
        caps_for_patent = set()
        for cpc in pat["cpc_codes"]:
            if cpc in CPC_TO_CAPS:
                caps_for_patent.update(CPC_TO_CAPS[cpc])
        for cap in sorted(caps_for_patent):
            if cap in CAPABILITIES:
                edge_id = next_edge_id()
                source = f"PAT_{pat['id']}"
                target = f"CAP_{cap}"
                cpc_used = next((c for c in pat["cpc_codes"] if cap in CPC_TO_CAPS.get(c, [])), "unknown")

                # EvidenceEdge schema (Correction 1)
                graph["evidence_edges"].append({
                    "id": edge_id,
                    "source": source,
                    "target": target,
                    "type": "EMBODIED_IN",
                    "evidence": [f"CPC:{cpc_used}", f"patent:{pat['id']}"],
                    "confidence": "EXPLICIT",  # Correction 2: ordinal label
                })
                # Justification (full schema)
                graph["edge_justifications"].append({
                    "edgeId": edge_id,
                    "sourcePatent": pat["id"],
                    "cpcCode": cpc_used,
                    "sourceNode": source,
                    "targetNode": target,
                    "relationship": "EMBODIED_IN",
                    "justification": f"Patent {pat['id']} has CPC code {cpc_used}, which maps to {cap} per CPC_MAPPING.md. CPC codes are assigned by USPTO patent examiners and are externally validated.",
                    "reviewer": "coder_agent_001 / 2026-08-02",
                    "confidence": "EXPLICIT",
                    "edge_category": "evidence",  # Correction 1: category tag
                })
                print(f"  {edge_id}: {pat['id']} → EMBODIED_IN → {cap} [EXPLICIT, CPC:{cpc_used}]")

    # ─── STRUCTURAL EDGES: REQUIRES (capability → capability) ───
    # These are domain model assertions, not observations.
    print("\n--- Structural edges (REQUIRES) ---")
    for req in STRUCTURAL_REQUIRES:
        edge_id = next_edge_id()
        source = f"CAP_{req['source']}"
        target = f"CAP_{req['target']}"

        # StructuralEdge schema (Correction 1 + 3)
        graph["structural_edges"].append({
            "id": edge_id,
            "source": source,
            "target": target,
            "type": "REQUIRES",
            "principle": req["principle"],  # Correction 3: principle field
            "reviewer": "coder_agent_001 / 2026-08-02",
            "confidence": "STRUCTURAL",  # Correction 2: ordinal label
        })
        graph["edge_justifications"].append({
            "edgeId": edge_id,
            "sourcePatent": "structural_invariant",
            "cpcCode": "N/A (structural)",
            "sourceNode": source,
            "targetNode": target,
            "relationship": "REQUIRES",
            "principle": req["principle"],  # Correction 3
            "justification": req["justification"],
            "reviewer": "coder_agent_001 / 2026-08-02",
            "confidence": "STRUCTURAL",
            "edge_category": "structural",  # Correction 1
        })
        print(f"  {edge_id}: {req['source']} → REQUIRES → {req['target']} [STRUCTURAL, principle: {req['principle']}]")

    # ─── STRUCTURAL EDGES: CONSTRAINS (constraint → capability) ───
    print("\n--- Structural edges (CONSTRAINS) ---")
    for ce in CONSTRAINT_EDGES:
        edge_id = next_edge_id()
        source = f"CON_{ce['constraint']}"
        target = f"CAP_{ce['capability']}"

        graph["structural_edges"].append({
            "id": edge_id,
            "source": source,
            "target": target,
            "type": "CONSTRAINS",
            "principle": ce["principle"],
            "reviewer": "coder_agent_001 / 2026-08-02",
            "confidence": "STRUCTURAL",
        })
        graph["edge_justifications"].append({
            "edgeId": edge_id,
            "sourcePatent": "structural_constraint",
            "cpcCode": "N/A (structural)",
            "sourceNode": source,
            "targetNode": target,
            "relationship": "CONSTRAINS",
            "principle": ce["principle"],
            "justification": ce["justification"],
            "reviewer": "coder_agent_001 / 2026-08-02",
            "confidence": "STRUCTURAL",
            "edge_category": "structural",
        })
        print(f"  {edge_id}: {ce['constraint']} → CONSTRAINS → {ce['capability']} [STRUCTURAL, principle: {ce['principle']}]")

    # ─── EVIDENCE EDGES: REGULATED_BY (capability → regulation) ───
    # These are evidence edges because regulations are externally validated documents.
    print("\n--- Evidence edges (REGULATED_BY) ---")
    for rb in REGULATED_BY_EDGES:
        edge_id = next_edge_id()
        source = f"CAP_{rb['capability']}"
        target = f"CON_{rb['regulation']}"

        graph["evidence_edges"].append({
            "id": edge_id,
            "source": source,
            "target": target,
            "type": "REGULATED_BY",
            "evidence": [f"regulation:{rb['regulation']}"],
            "confidence": "EXPLICIT",
        })
        graph["edge_justifications"].append({
            "edgeId": edge_id,
            "sourcePatent": "regulation",
            "cpcCode": "N/A (regulation)",
            "sourceNode": source,
            "targetNode": target,
            "relationship": "REGULATED_BY",
            "principle": rb["principle"],
            "justification": rb["justification"],
            "reviewer": "coder_agent_001 / 2026-08-02",
            "confidence": "EXPLICIT",
            "edge_category": "evidence",
        })
        print(f"  {edge_id}: {rb['capability']} → REGULATED_BY → {rb['regulation']} [EXPLICIT, principle: {rb['principle']}]")

    # ─── Verify ───
    total_edges = len(graph["evidence_edges"]) + len(graph["structural_edges"])
    total_just = len(graph["edge_justifications"])

    print(f"\n{'=' * 70}")
    print("VERIFICATION")
    print(f"{'=' * 70}")
    print(f"Nodes: {len(graph['nodes'])}")
    print(f"Evidence edges: {len(graph['evidence_edges'])} (observations — CPC-coded, regulation-backed)")
    print(f"Structural edges: {len(graph['structural_edges'])} (domain model — principle-cited)")
    print(f"Total edges: {total_edges}")
    print(f"Justifications: {total_just}")
    print(f"Every edge justified: {'YES' if total_edges == total_just else 'NO'}")
    assert total_edges == total_just, "MISMATCH: edges ≠ justifications"

    # Check: no suspended types
    for e in graph["evidence_edges"] + graph["structural_edges"]:
        assert e["type"] not in ("ENABLES", "SUBSTITUTES_FOR"), f"SUSPENDED TYPE: {e['type']}"
    print(f"Suspended types used: 0")

    # Check: all structural edges have 'principle' field (Correction 3)
    for e in graph["structural_edges"]:
        assert "principle" in e and e["principle"], f"MISSING PRINCIPLE: {e['id']}"
    print(f"All structural edges have 'principle': YES")

    # Check: all confidence is ordinal (Correction 2)
    valid_labels = {"EXPLICIT", "IMPLIED", "STRUCTURAL", "SPECULATIVE"}
    for ej in graph["edge_justifications"]:
        assert ej["confidence"] in valid_labels, f"INVALID CONFIDENCE: {ej['confidence']}"
    print(f"All confidence is ordinal: YES")

    # Check: evidence edges have 'evidence' field, structural edges have 'principle' field (Correction 1)
    for e in graph["evidence_edges"]:
        assert "evidence" in e, f"MISSING EVIDENCE FIELD: {e['id']}"
    for e in graph["structural_edges"]:
        assert "principle" in e, f"MISSING PRINCIPLE FIELD: {e['id']}"
    print(f"Evidence ≠ structural separation: YES")

    print(f"\nTRUSTED GRAPH v2.1:")
    print(f"  Evidence edges: {len(graph['evidence_edges'])}")
    print(f"    EMBODIED_IN: {sum(1 for e in graph['evidence_edges'] if e['type'] == 'EMBODIED_IN')}")
    print(f"    REGULATED_BY: {sum(1 for e in graph['evidence_edges'] if e['type'] == 'REGULATED_BY')}")
    print(f"  Structural edges: {len(graph['structural_edges'])}")
    print(f"    REQUIRES: {sum(1 for e in graph['structural_edges'] if e['type'] == 'REQUIRES')}")
    print(f"    CONSTRAINS: {sum(1 for e in graph['structural_edges'] if e['type'] == 'CONSTRAINS')}")

    with open(OUTPUT, "w") as f:
        json.dump(graph, f, indent=2)
        f.write("\n")
    print(f"\n  Written to: {OUTPUT}")


if __name__ == "__main__":
    main()
