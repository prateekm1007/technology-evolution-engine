#!/usr/bin/env python3
"""run_dxp005.py — DXP-005 ablation experiment (FIXED protocol).

Architecture (per CEO directive):
  1. Freeze upstream (extraction/abstraction/transfer) ONCE per case
  2. Share identical upstream artifacts across all 3 conditions
  3. Only the hypothesis generation stage differs (A/B/C)
  4. Run the UNCHANGED adversarial gate on every hypothesis
  5. Record API failures as operational interruptions, not scientific results

Conditions:
  A — baseline: transfer only → hypothesis generation
  B — H-GEN-1: transfer + real mechanism graph → hypothesis generation
  C — mechanism-null: transfer + null mechanism graph → hypothesis generation

The adversarial gate is the SAME for all conditions. No calibration.
"""
import sys, json, time, hashlib, os
from pathlib import Path
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "discovery_experiment/CASES"))

from engine.providers import ZAIReasoningProvider, ProviderCallManifest
from engine.mechanism_extraction import MechanismExtractionEngine
from engine.mechanism_abstraction import MechanismAbstractionEngine
from engine.cross_domain_transfer import CrossDomainTransferEngine
from engine.hypothesis_generation import HypothesisGenerationEngine
from engine.adversarial_analysis import AdversarialAnalysisEngine
from discovery_infrastructure.discovery_substrate import (
    TransferHypothesis, EpistemicState, MechanismGraph, MechanismNode,
    MechanismEdge, MechanismNodeType, MechanismEdgeType, Hypothesis,
)

# Load ground truth
gt = json.loads((REPO / "discovery_experiment/CASES/DXP-005/DXP-005_GROUND_TRUTH.json").read_text())
CASES = gt["cases"]
CONDITIONS = ["A-baseline", "B-hgen1", "C-null"]
OUTPUT_DIR = REPO / "discovery_experiment/ENGINE_OUTPUT/DXP-005"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def get_case_documents(case_id):
    """Load input documents for a case."""
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


def create_null_mechanism_graph(real_graph):
    """Create a mechanism graph with the same number of nodes/edges but
    with irrelevant causal content (generic labels/descriptions).

    This is the C condition: same structural density, no specific mechanism.
    """
    null_graph = MechanismGraph()
    for i, (nid, node) in enumerate(real_graph.nodes.items()):
        null_graph.add_node(MechanismNode(
            node_id=f"null_node_{i}",
            node_type=node.node_type,
            label=f"generic_{node.node_type.value}_{i}",
            description="A generic structural element with no specific causal function.",
            provenance=["null_source"],
        ))
    node_ids = list(real_graph.nodes.keys())
    for i, edge in enumerate(real_graph.edges):
        source_idx = node_ids.index(edge.source_id)
        target_idx = node_ids.index(edge.target_id)
        null_graph.add_edge(MechanismEdge(
            edge_id=f"null_edge_{i}",
            source_id=f"null_node_{source_idx}",
            target_id=f"null_node_{target_idx}",
            edge_type=edge.edge_type,
            confidence=0.5,
            evidence=["generic structural relationship"],
        ))
    return null_graph


def save_json(path, data):
    """Save JSON with timestamp."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str))


def run_case(case_id, reasoning_provider):
    """Run one case through the FIXED protocol.

    Architecture:
      1. Extract ONCE → save mechanism graph → hash
      2. Abstract ONCE → save → hash
      3. Transfer ONCE → save → hash
      4. Generate null graph ONCE from the real graph → save → hash
      5. For each condition (A/B/C): hypothesis generation only (using shared upstream)
      6. For each condition: adversarial analysis (SAME gate) on every hypothesis
    """
    case = CASES[case_id]
    doc_a, doc_b_text, case_data = get_case_documents(case_id)
    case_dir = OUTPUT_DIR / case_id

    # ===== STEP 1: Freeze upstream (extraction → abstraction → transfer) =====
    upstream_dir = case_dir / "upstream"
    upstream_hash_file = upstream_dir / "HASHES.json"

    if upstream_hash_file.exists():
        print(f"  [{case_id}] Upstream already frozen — loading")
        upstream = json.loads(upstream_hash_file.read_text())
        ext_data = json.loads((upstream_dir / "01_extraction.json").read_text())
        ab_data = json.loads((upstream_dir / "02_abstraction.json").read_text())
        tr_data = json.loads((upstream_dir / "03_transfer.json").read_text())
        null_data = json.loads((upstream_dir / "04_null_graph.json").read_text())
    else:
        print(f"  [{case_id}] Freezing upstream...")

        # 1a. Extraction (ONCE)
        print(f"  [{case_id}] Extracting...")
        extractor = MechanismExtractionEngine(reasoning_provider)
        ext_result = extractor.extract(doc_a)
        ext_data = {
            "ok": ext_result.ok, "graph": ext_result.graph.to_dict(),
            "n_nodes": len(ext_result.graph.nodes), "n_edges": len(ext_result.graph.edges),
            "n_failures": len(ext_result.failures),
            "failures": [f.__dict__ for f in ext_result.failures],
        }
        save_json(upstream_dir / "01_extraction.json", ext_data)

        if not ext_result.ok:
            print(f"  [{case_id}] Extraction failed — cannot proceed")
            return {"case_id": case_id, "status": "EXTRACTION_FAILED"}

        # 1b. Abstraction (ONCE)
        print(f"  [{case_id}] Abstracting...")
        abstracter = MechanismAbstractionEngine(reasoning_provider)
        ab_result = abstracter.abstract(ext_result.graph,
            source_domain=case["source_domain"],
            source_title=doc_a.get("title", ""),
            pattern_id=f"MP-{case_id}")
        ab_data = {"pattern": ab_result.pattern.to_dict()}
        save_json(upstream_dir / "02_abstraction.json", ab_data)

        # 1c. Transfer (ONCE)
        print(f"  [{case_id}] Transferring...")
        transfer_engine = CrossDomainTransferEngine(reasoning_provider)
        tr_result = transfer_engine.generate(ab_result.pattern,
            target_domain=case["target_domain"],
            target_problem=doc_b_text[:500],
            target_constraints=[],
            transfer_id_prefix=f"TH-{case_id}")
        tr_data = {"transfers": [t.to_dict() for t in tr_result.transfers],
                   "rejected": tr_result.rejected}
        save_json(upstream_dir / "03_transfer.json", tr_data)

        if not tr_result.transfers:
            print(f"  [{case_id}] Transfer rejected — cannot proceed")
            return {"case_id": case_id, "status": "TRANSFER_REJECTED"}

        # 1d. Null graph (ONCE, from the SAME real graph)
        null_graph = create_null_mechanism_graph(ext_result.graph)
        null_data = {"graph": null_graph.to_dict()}
        save_json(upstream_dir / "04_null_graph.json", null_data)

        # Hash everything
        upstream = {
            "extraction_sha256": hashlib.sha256(json.dumps(ext_data, sort_keys=True).encode()).hexdigest(),
            "abstraction_sha256": hashlib.sha256(json.dumps(ab_data, sort_keys=True).encode()).hexdigest(),
            "transfer_sha256": hashlib.sha256(json.dumps(tr_data, sort_keys=True).encode()).hexdigest(),
            "null_graph_sha256": hashlib.sha256(json.dumps(null_data, sort_keys=True).encode()).hexdigest(),
            "frozen_at": datetime.now(timezone.utc).isoformat(),
        }
        save_json(upstream_hash_file, upstream)
        print(f"  [{case_id}] Upstream frozen and hashed")

    # Reconstruct objects from frozen data
    # Mechanism graph (real)
    real_graph = MechanismGraph()
    for n in ext_data["graph"]["nodes"].values():
        real_graph.add_node(MechanismNode(
            node_id=n["node_id"], node_type=MechanismNodeType(n["node_type"]),
            label=n["label"], description=n.get("description", ""),
            provenance=n.get("provenance", [])))
    for e in ext_data["graph"]["edges"]:
        real_graph.add_edge(MechanismEdge(
            edge_id=e["edge_id"], source_id=e["source_id"], target_id=e["target_id"],
            edge_type=MechanismEdgeType(e["edge_type"]),
            confidence=e.get("confidence", 0.5), evidence=e.get("evidence", [])))

    # Transfer hypothesis (shared)
    t = tr_data["transfers"][0]
    transfer = TransferHypothesis(
        transfer_id=t["transfer_id"], source_domain=t.get("source_domain", ""),
        source_mechanism=t.get("source_mechanism", ""),
        source_conditions=t.get("source_conditions", []),
        target_domain=t.get("target_domain", ""),
        target_problem=t.get("target_problem", ""),
        transferred_principle=t.get("transferred_principle", ""),
        required_translation=t.get("required_translation", ""),
        expected_effect=t.get("expected_effect", ""),
        boundary_conditions=t.get("boundary_conditions", []),
        failure_conditions=t.get("failure_conditions", []),
        testable_prediction=t.get("testable_prediction", ""),
        epistemic_state=EpistemicState(t.get("epistemic_state", "HYPOTHESIZED")))

    # ===== STEP 2: Run 3 generator conditions =====
    hyp_engine = HypothesisGenerationEngine(reasoning_provider)
    adversarial_engine = AdversarialAnalysisEngine(reasoning_provider)

    case_results = {"case_id": case_id, "upstream_hashes": upstream, "conditions": {}}

    for condition in CONDITIONS:
        cond_dir = case_dir / condition
        result_file = cond_dir / "result.json"

        if result_file.exists():
            print(f"  [{case_id}-{condition}] Already completed — loading")
            case_results["conditions"][condition] = json.loads(result_file.read_text())
            continue

        print(f"  [{case_id}-{condition}] Generating hypotheses...")

        # ONLY THIS DIFFERS between conditions
        if condition == "A-baseline":
            result = hyp_engine.generate(transfer, id_prefix=f"H-{case_id}")
        elif condition == "B-hgen1":
            result = hyp_engine.generate(transfer, id_prefix=f"H-{case_id}",
                mechanism_graph=real_graph)
        elif condition == "C-null":
            # Reconstruct null graph from frozen data
            null_graph_obj = MechanismGraph()
            for n in null_data["graph"]["nodes"].values():
                null_graph_obj.add_node(MechanismNode(
                    node_id=n["node_id"], node_type=MechanismNodeType(n["node_type"]),
                    label=n["label"], description=n.get("description", ""),
                    provenance=n.get("provenance", [])))
            for e in null_data["graph"]["edges"]:
                null_graph_obj.add_edge(MechanismEdge(
                    edge_id=e["edge_id"], source_id=e["source_id"], target_id=e["target_id"],
                    edge_type=MechanismEdgeType(e["edge_type"]),
                    confidence=e.get("confidence", 0.5), evidence=e.get("evidence", [])))
            result = hyp_engine.generate(transfer, id_prefix=f"H-{case_id}",
                mechanism_graph=null_graph_obj)

        hyp_output = {
            "hypotheses": [h.to_dict() for h in result.hypotheses],
            "distinguishing_predictions": result.distinguishing_predictions,
            "n_hypotheses": len(result.hypotheses),
            "n_testable": sum(1 for h in result.hypotheses if h.is_testable),
        }
        save_json(cond_dir / "04_hypotheses.json", hyp_output)

        # ===== STEP 3: Run UNCHANGED adversarial gate on every hypothesis =====
        print(f"  [{case_id}-{condition}] Running adversarial gate...")
        adv_results = []
        for h in result.hypotheses:
            if not h.is_testable:
                adv_results.append({"hypothesis_id": h.hypothesis_id, "skipped": "not testable"})
                continue
            adv = adversarial_engine.analyze(h)
            adv_output = {
                "hypothesis_id": h.hypothesis_id,
                "outcome": adv.result.outcome if hasattr(adv, 'result') else None,
                "survives": adv.survives,
                "failure_modes": [fm.__dict__ for fm in adv.failure_modes],
                "n_high": sum(1 for fm in adv.failure_modes if fm.severity == "HIGH"),
                "n_medium": sum(1 for fm in adv.failure_modes if fm.severity == "MEDIUM"),
            }
            adv_results.append(adv_output)

        save_json(cond_dir / "05_adversarial.json", {"results": adv_results})

        cond_result = {
            "condition": condition,
            "n_hypotheses": len(result.hypotheses),
            "n_testable": hyp_output["n_testable"],
            "n_survived": sum(1 for a in adv_results if a.get("survives")),
            "n_killed": sum(1 for a in adv_results if not a.get("survives") and not a.get("skipped")),
            "hypotheses": [{"id": h.hypothesis_id, "claim": h.claim[:300],
                            "mechanism": h.mechanism[:300],
                            "falsifier": h.falsifier[:300] if h.falsifier else "",
                            "is_testable": h.is_testable}
                           for h in result.hypotheses],
            "adversarial": adv_results,
        }
        save_json(result_file, cond_result)
        case_results["conditions"][condition] = cond_result
        print(f"  [{case_id}-{condition}] Done: {cond_result['n_hypotheses']} hyps, {cond_result['n_survived']} survived, {cond_result['n_killed']} killed")

    return case_results


def main():
    reasoning = ZAIReasoningProvider(timeout=120)
    all_results = []
    case_ids = sorted(CASES.keys())

    for case_id in case_ids:
        print(f"\n[{case_id}] === STARTING ===")
        try:
            result = run_case(case_id, reasoning)
        except Exception as e:
            import traceback
            result = {"case_id": case_id, "status": f"ERROR: {type(e).__name__}: {e}",
                      "traceback": traceback.format_exc()}
            print(f"[{case_id}] ERROR: {e}")

        case_result_file = OUTPUT_DIR / f"{case_id}-result.json"
        save_json(case_result_file, result)
        all_results.append(result)

    # Summary
    summary_file = OUTPUT_DIR / "DXP-005-summary.json"
    save_json(summary_file, all_results)
    print(f"\nSummary saved to {summary_file}")
    print(f"Total cases: {len(all_results)}")
    for r in all_results:
        status = r.get("status", "COMPLETED")
        if status == "COMPLETED" or "conditions" in r:
            for cond, cr in r.get("conditions", {}).items():
                print(f"  {r['case_id']}-{cond}: {cr.get('n_hypotheses',0)} hyps, {cr.get('n_survived',0)} survived")
        else:
            print(f"  {r['case_id']}: {status}")


if __name__ == "__main__":
    main()
