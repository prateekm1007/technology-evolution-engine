#!/usr/bin/env python3
"""run_dxp005.py — run the DXP-005 ablation experiment.

3 conditions × 10 cases = 30 runs.
Uses checkpoint/resume. Each run is independently recoverable.
"""
import sys, json, time, hashlib
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "discovery_experiment/CASES"))

from engine.checkpoint import CheckpointedDiscoveryLoop, RUNS_DIR
from engine.providers import ZAIReasoningProvider, MockLiteratureProvider, ProviderCallManifest
from engine.hypothesis_generation import HypothesisGenerationEngine
from engine.mechanism_extraction import MechanismExtractionEngine
from engine.mechanism_abstraction import MechanismAbstractionEngine, MechanismPattern
from engine.cross_domain_transfer import CrossDomainTransferEngine
from discovery_infrastructure.discovery_substrate import (
    TransferHypothesis, EpistemicState, MechanismGraph, MechanismNode, MechanismEdge,
    MechanismNodeType, MechanismEdgeType, Hypothesis,
)

# Load ground truth
gt = json.loads((REPO / "discovery_experiment/CASES/DXP-005/DXP-005_GROUND_TRUTH.json").read_text())
CASES = gt["cases"]

# Condition A: baseline (no mechanism graph)
# Condition B: H-GEN-1 (with mechanism graph)
# Condition C: mechanism-null (with irrelevant mechanism graph)

CONDITIONS = ["A-baseline", "B-hgen1", "C-null"]
OUTPUT_DIR = REPO / "discovery_experiment/ENGINE_OUTPUT/DXP-005"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# --- Helper: load input documents for a case ---
def get_case_documents(case_id):
    inputs_dir = REPO / "discovery_experiment/INPUTS"
    case = CASES[case_id]
    
    if case_id == "P1":
        doc_a = (inputs_dir / "DXP-004_DOCUMENT_A_SHARK_SKIN.txt").read_text()
        doc_b = (inputs_dir / "DXP-004_DOCUMENT_B_PIPE_DRAG.txt").read_text()
    elif case_id == "P2":
        doc_a = (inputs_dir / "DXP-003_DOCUMENT_A_BAT_ECHOLOCATION.txt").read_text()
        doc_b = (inputs_dir / "DXP-003_DOCUMENT_B_RADAR.txt").read_text()
    else:
        a_matches = list(inputs_dir.glob(f"DXP-005-{case_id}-A-*.txt"))
        b_matches = list(inputs_dir.glob(f"DXP-005-{case_id}-B-*.txt"))
        doc_a = a_matches[0].read_text() if a_matches else ""
        doc_b = b_matches[0].read_text() if b_matches else ""
    
    return {"title": case["source_doc"], "text": doc_a}, doc_b, case

# --- Helper: create a null mechanism graph (same structure, irrelevant edges) ---
def create_null_mechanism_graph(real_graph):
    """Create a mechanism graph with the same number of nodes/edges but
    with irrelevant causal content (generic labels)."""
    null_graph = MechanismGraph()
    for i, (nid, node) in enumerate(real_graph.nodes.items()):
        null_graph.add_node(MechanismNode(
            node_id=f"null_node_{i}",
            node_type=node.node_type,
            label=f"generic_{node.node_type.value}_{i}",
            description="A generic structural element with no specific causal function.",
            provenance=["null_source"],
        ))
    for i, edge in enumerate(real_graph.edges):
        # Use the same edge types but with generic, irrelevant descriptions
        source_idx = list(real_graph.nodes.keys()).index(edge.source_id)
        target_idx = list(real_graph.nodes.keys()).index(edge.target_id)
        null_graph.add_edge(MechanismEdge(
            edge_id=f"null_edge_{i}",
            source_id=f"null_node_{source_idx}",
            target_id=f"null_node_{target_idx}",
            edge_type=edge.edge_type,
            confidence=0.5,
            evidence=["generic structural relationship"],
        ))
    return null_graph

# --- Run a single case under a single condition ---
def run_case(case_id, condition, reasoning_provider):
    """Run one case under one condition. Uses the engine pipeline up to
    hypothesis generation, then stops (no adversarial/prediction/etc.
    — those are the same across conditions since only the generator changes)."""
    case = CASES[case_id]
    doc_a, doc_b_text, case_data = get_case_documents(case_id)
    
    output_dir = OUTPUT_DIR / f"{case_id}-{condition}"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"  [{case_id}-{condition}] Extracting...")
    
    # Stage 1: Extraction (same for all conditions)
    extractor = MechanismExtractionEngine(reasoning_provider)
    ext_result = extractor.extract(doc_a)
    ext_output = {"ok": ext_result.ok, "graph": ext_result.graph.to_dict(),
                  "n_nodes": len(ext_result.graph.nodes), "n_edges": len(ext_result.graph.edges)}
    (output_dir / "01_extraction.json").write_text(json.dumps(ext_output, indent=2, default=str))
    
    if not ext_result.ok:
        print(f"  [{case_id}-{condition}] Extraction failed — skipping")
        return {"case_id": case_id, "condition": condition, "status": "EXTRACTION_FAILED"}
    
    # Stage 2: Abstraction (same for all conditions)
    print(f"  [{case_id}-{condition}] Abstracting...")
    abstracter = MechanismAbstractionEngine(reasoning_provider)
    ab_result = abstracter.abstract(ext_result.graph,
        source_domain=case["source_domain"],
        source_title=doc_a.get("title", ""),
        pattern_id=f"MP-{case_id}")
    (output_dir / "02_abstraction.json").write_text(json.dumps(
        {"pattern": ab_result.pattern.to_dict()}, indent=2, default=str))
    
    # Stage 3: Transfer (same for all conditions)
    print(f"  [{case_id}-{condition}] Transferring...")
    transfer_engine = CrossDomainTransferEngine(reasoning_provider)
    tr_result = transfer_engine.generate(ab_result.pattern,
        target_domain=case["target_domain"],
        target_problem=doc_b_text[:500],
        target_constraints=[],
        transfer_id_prefix=f"TH-{case_id}")
    (output_dir / "03_transfer.json").write_text(json.dumps(
        {"transfers": [t.to_dict() for t in tr_result.transfers],
         "rejected": tr_result.rejected}, indent=2, default=str))
    
    if not tr_result.transfers:
        print(f"  [{case_id}-{condition}] Transfer rejected — skipping")
        return {"case_id": case_id, "condition": condition, "status": "TRANSFER_REJECTED"}
    
    transfer = tr_result.transfers[0]
    
    # Stage 4: Hypothesis generation (DIFFERS by condition)
    print(f"  [{case_id}-{condition}] Generating hypotheses...")
    hyp_engine = HypothesisGenerationEngine(reasoning_provider)
    
    if condition == "A-baseline":
        # Baseline: no mechanism graph
        result = hyp_engine.generate(transfer, id_prefix=f"H-{case_id}")
    elif condition == "B-hgen1":
        # H-GEN-1: real mechanism graph
        result = hyp_engine.generate(transfer, id_prefix=f"H-{case_id}",
            mechanism_graph=ext_result.graph)
    elif condition == "C-null":
        # Mechanism-null: irrelevant mechanism graph
        null_graph = create_null_mechanism_graph(ext_result.graph)
        result = hyp_engine.generate(transfer, id_prefix=f"H-{case_id}",
            mechanism_graph=null_graph)
    
    hyp_output = {
        "hypotheses": [h.to_dict() for h in result.hypotheses],
        "distinguishing_predictions": result.distinguishing_predictions,
        "failures": result.failures,
        "n_hypotheses": len(result.hypotheses),
        "n_testable": sum(1 for h in result.hypotheses if h.is_testable),
    }
    (output_dir / "04_hypotheses.json").write_text(json.dumps(hyp_output, indent=2, default=str))
    
    print(f"  [{case_id}-{condition}] Done: {len(result.hypotheses)} hypotheses ({hyp_output['n_testable']} testable)")
    
    return {
        "case_id": case_id,
        "condition": condition,
        "status": "COMPLETED",
        "n_hypotheses": len(result.hypotheses),
        "n_testable": hyp_output["n_testable"],
        "hypotheses": [{"id": h.hypothesis_id, "claim": h.claim[:200],
                        "mechanism": h.mechanism[:200],
                        "falsifier": h.falsifier[:200] if h.falsifier else "",
                        "is_testable": h.is_testable}
                       for h in result.hypotheses],
    }

# --- Main: run all 30 experiments ---
def main():
    reasoning = ZAIReasoningProvider(timeout=120)
    
    all_results = []
    case_ids = sorted(CASES.keys())
    
    for case_id in case_ids:
        for condition in CONDITIONS:
            run_id = f"{case_id}-{condition}"
            result_file = OUTPUT_DIR / f"{run_id}-result.json"
            
            if result_file.exists():
                print(f"[{run_id}] Already completed — skipping")
                result = json.loads(result_file.read_text())
            else:
                print(f"[{run_id}] Running...")
                try:
                    result = run_case(case_id, condition, reasoning)
                except Exception as e:
                    result = {"case_id": case_id, "condition": condition,
                              "status": f"ERROR: {type(e).__name__}: {e}"}
                result_file.write_text(json.dumps(result, indent=2, default=str))
            
            all_results.append(result)
    
    # Summary
    summary_file = OUTPUT_DIR / "DXP-005-summary.json"
    summary_file.write_text(json.dumps(all_results, indent=2, default=str))
    print(f"\nSummary saved to {summary_file}")
    print(f"Total runs: {len(all_results)}")
    for r in all_results:
        print(f"  {r['case_id']}-{r['condition']}: {r['status']}")

if __name__ == "__main__":
    main()
