#!/usr/bin/env python3
"""run_dxp005_step.py — Run a single step of DXP-005.

Each invocation does ONE small unit of work:
  - generate upstream for one case (extraction/abstraction/transfer/null graph)
  - generate hypotheses for one case × one condition
  - run adversarial on one case × one condition × one hypothesis

Saves progress after each step. Designed to fit within the bash tool's
time budget per invocation.
"""
import sys, os, json, time, hashlib
from pathlib import Path
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "discovery_experiment/CASES"))

from engine.openrouter_provider import OpenRouterProvider
from engine.mechanism_extraction import MechanismExtractionEngine
from engine.mechanism_abstraction import MechanismAbstractionEngine
from engine.cross_domain_transfer import CrossDomainTransferEngine
from engine.hypothesis_generation import HypothesisGenerationEngine
from engine.adversarial_analysis import AdversarialAnalysisEngine
from discovery_infrastructure.discovery_substrate import (
    TransferHypothesis, EpistemicState, MechanismGraph, MechanismNode,
    MechanismEdge, MechanismNodeType, MechanismEdgeType, Hypothesis,
)

GT = json.loads((REPO / "discovery_experiment/CASES/DXP-005/DXP-005_GROUND_TRUTH.json").read_text())
CASES = GT["cases"]
CONDITIONS = ["A-baseline", "B-hgen1", "C-null"]
OUTPUT_DIR = REPO / "discovery_experiment/ENGINE_OUTPUT/DXP-005"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def make_provider():
    API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
    if not API_KEY:
        raise SystemExit("OPENROUTER_API_KEY not set")
    return OpenRouterProvider(
        api_key=API_KEY,
        model="nvidia/nemotron-3-ultra-550b-a55b:free",
        default_max_tokens=4096,
        timeout=60,
        max_retries=3,
        retry_backoff=3.0,
    )


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str))


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


def create_null_mechanism_graph(real_graph):
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


def step_upstream(case_id, provider):
    """Freeze upstream for a case (extract+abstract+transfer+nullgraph)."""
    case_dir = OUTPUT_DIR / case_id
    upstream_dir = case_dir / "upstream"
    upstream_hash_file = upstream_dir / "HASHES.json"

    if upstream_hash_file.exists():
        print(f"  [{case_id}] Upstream already frozen — skip")
        return True

    print(f"  [{case_id}] Freezing upstream...")
    case = CASES[case_id]
    doc_a, doc_b_text, case_data = get_case_documents(case_id)

    # Extraction
    print(f"  [{case_id}] Extracting...")
    extractor = MechanismExtractionEngine(provider)
    ext_result = extractor.extract(doc_a)
    ext_data = {
        "ok": ext_result.ok, "graph": ext_result.graph.to_dict(),
        "n_nodes": len(ext_result.graph.nodes), "n_edges": len(ext_result.graph.edges),
        "n_failures": len(ext_result.failures),
        "failures": [f.__dict__ for f in ext_result.failures],
    }
    save_json(upstream_dir / "01_extraction.json", ext_data)
    if not ext_result.ok:
        print(f"  [{case_id}] Extraction failed")
        return False

    # Abstraction
    print(f"  [{case_id}] Abstracting...")
    abstracter = MechanismAbstractionEngine(provider)
    ab_result = abstracter.abstract(ext_result.graph,
        source_domain=case["source_domain"],
        source_title=doc_a.get("title", ""),
        pattern_id=f"MP-{case_id}")
    ab_data = {"pattern": ab_result.pattern.to_dict()}
    save_json(upstream_dir / "02_abstraction.json", ab_data)

    # Transfer
    print(f"  [{case_id}] Transferring...")
    transfer_engine = CrossDomainTransferEngine(provider)
    tr_result = transfer_engine.generate(ab_result.pattern,
        target_domain=case["target_domain"],
        target_problem=doc_b_text[:500],
        target_constraints=[],
        transfer_id_prefix=f"TH-{case_id}")
    tr_data = {"transfers": [t.to_dict() for t in tr_result.transfers],
               "rejected": tr_result.rejected}
    save_json(upstream_dir / "03_transfer.json", tr_data)

    if not tr_result.transfers:
        print(f"  [{case_id}] Transfer rejected")
        # Still save hashes so we know upstream is frozen
        upstream = {
            "extraction_sha256": hashlib.sha256(json.dumps(ext_data, sort_keys=True).encode()).hexdigest(),
            "abstraction_sha256": hashlib.sha256(json.dumps(ab_data, sort_keys=True).encode()).hexdigest(),
            "transfer_sha256": hashlib.sha256(json.dumps(tr_data, sort_keys=True).encode()).hexdigest(),
            "null_graph_sha256": "TRANSFER_REJECTED_NO_NULL_GRAPH",
            "frozen_at": datetime.now(timezone.utc).isoformat(),
            "transfer_rejected": True,
        }
        save_json(upstream_hash_file, upstream)
        return "TRANSFER_REJECTED"

    # Null graph
    null_graph = create_null_mechanism_graph(ext_result.graph)
    null_data = {"graph": null_graph.to_dict()}
    save_json(upstream_dir / "04_null_graph.json", null_data)

    upstream = {
        "extraction_sha256": hashlib.sha256(json.dumps(ext_data, sort_keys=True).encode()).hexdigest(),
        "abstraction_sha256": hashlib.sha256(json.dumps(ab_data, sort_keys=True).encode()).hexdigest(),
        "transfer_sha256": hashlib.sha256(json.dumps(tr_data, sort_keys=True).encode()).hexdigest(),
        "null_graph_sha256": hashlib.sha256(json.dumps(null_data, sort_keys=True).encode()).hexdigest(),
        "frozen_at": datetime.now(timezone.utc).isoformat(),
    }
    save_json(upstream_hash_file, upstream)
    print(f"  [{case_id}] Upstream frozen")
    return True


def step_hypotheses(case_id, condition, provider):
    """Generate hypotheses for one case × one condition."""
    case_dir = OUTPUT_DIR / case_id
    cond_dir = case_dir / condition
    hyp_file = cond_dir / "04_hypotheses.json"
    result_file = cond_dir / "result.json"

    if result_file.exists():
        print(f"  [{case_id}-{condition}] Already complete — skip")
        return "ALREADY_COMPLETE"

    if hyp_file.exists():
        print(f"  [{case_id}-{condition}] Hypotheses already generated — skip")
        return "ALREADY_GENERATED"

    # Load upstream
    upstream_dir = case_dir / "upstream"
    ext_data = json.loads((upstream_dir / "01_extraction.json").read_text())
    null_data = json.loads((upstream_dir / "04_null_graph.json").read_text())
    tr_data = json.loads((upstream_dir / "03_transfer.json").read_text())
    if not tr_data.get("transfers"):
        print(f"  [{case_id}-{condition}] Transfer was rejected — no hypotheses")
        return "TRANSFER_REJECTED"

    # Reconstruct real graph
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

    # Reconstruct transfer
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

    # Generate
    print(f"  [{case_id}-{condition}] Generating hypotheses...")
    hyp_engine = HypothesisGenerationEngine(provider)
    if condition == "A-baseline":
        result = hyp_engine.generate(transfer, id_prefix=f"H-{case_id}")
    elif condition == "B-hgen1":
        result = hyp_engine.generate(transfer, id_prefix=f"H-{case_id}",
            mechanism_graph=real_graph)
    elif condition == "C-null":
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
    save_json(hyp_file, hyp_output)
    print(f"  [{case_id}-{condition}] Generated {hyp_output['n_hypotheses']} hypotheses")
    return "GENERATED"


def step_adversarial(case_id, condition, provider):
    """Run adversarial on all hypotheses for one case × one condition.
    Saves progress after each call so partial progress is preserved.
    """
    case_dir = OUTPUT_DIR / case_id
    cond_dir = case_dir / condition
    hyp_file = cond_dir / "04_hypotheses.json"
    adv_file = cond_dir / "05_adversarial.json"
    result_file = cond_dir / "result.json"

    if result_file.exists():
        print(f"  [{case_id}-{condition}] Already complete — skip")
        return "ALREADY_COMPLETE"

    if not hyp_file.exists():
        print(f"  [{case_id}-{condition}] No hypotheses file — run step_hypotheses first")
        return "NO_HYPOTHESES"

    cached = json.loads(hyp_file.read_text())
    if not cached.get("hypotheses"):
        # 0 hypotheses — write empty result
        adv_results = []
        save_json(adv_file, {"results": adv_results})
        cond_result = {
            "condition": condition,
            "n_hypotheses": 0,
            "n_testable": 0,
            "n_survived": 0,
            "n_killed": 0,
            "hypotheses": [],
            "adversarial": adv_results,
        }
        save_json(result_file, cond_result)
        print(f"  [{case_id}-{condition}] 0 hypotheses — empty result written")
        return "EMPTY"

    # Load existing adversarial progress if any
    existing_results = {}
    if adv_file.exists():
        existing = json.loads(adv_file.read_text())
        for r in existing.get("results", []):
            existing_results[r.get("hypothesis_id")] = r

    # Reconstruct Hypothesis objects
    hyps = []
    for h in cached.get("hypotheses", []):
        try:
            hyps.append(Hypothesis(
                hypothesis_id=h.get("hypothesis_id", h.get("id", "")),
                claim=h.get("claim", ""),
                mechanism=h.get("mechanism", ""),
                evidence=h.get("evidence", []),
                assumptions=h.get("assumptions", []),
                predictions=h.get("predictions", []),
                expected_failure_modes=h.get("expected_failure_modes", []),
                novelty_rationale=h.get("novelty_rationale", ""),
                testability=h.get("testability", ""),
                falsifier=h.get("falsifier", ""),
                epistemic_state=EpistemicState(h.get("epistemic_state", "HYPOTHESIZED")),
                parent_hypothesis_ids=h.get("parent_hypothesis_ids", []),
                is_testable=h.get("is_testable", bool(h.get("falsifier", "").strip())),
            ))
        except Exception as e:
            print(f"  WARN: skip hyp {h.get('hypothesis_id','?')}: {e}")

    adv_engine = AdversarialAnalysisEngine(provider)
    adv_results = []
    n_done = 0

    for h in hyps:
        if h.hypothesis_id in existing_results:
            adv_results.append(existing_results[h.hypothesis_id])
            n_done += 1
            continue
        if not h.is_testable:
            r = {"hypothesis_id": h.hypothesis_id, "skipped": "not testable"}
            adv_results.append(r)
            existing_results[h.hypothesis_id] = r
            save_json(adv_file, {"results": adv_results})
            continue

        print(f"  [{case_id}-{condition}] Adversarial on {h.hypothesis_id}...")
        try:
            adv = adv_engine.analyze(h)
            adv_output = {
                "hypothesis_id": h.hypothesis_id,
                "outcome": None,
                "survives": adv.survives,
                "failure_modes": [fm.__dict__ for fm in adv.failure_modes],
                "n_high": sum(1 for fm in adv.failure_modes if fm.severity == "HIGH"),
                "n_medium": sum(1 for fm in adv.failure_modes if fm.severity == "MEDIUM"),
                "failures": adv.failures,
            }
            adv_results.append(adv_output)
            existing_results[h.hypothesis_id] = adv_output
            save_json(adv_file, {"results": adv_results})
            n_done += 1
            print(f"    survives={adv.survives} n_high={adv_output['n_high']}")
        except Exception as e:
            r = {"hypothesis_id": h.hypothesis_id, "error": f"{type(e).__name__}: {e}"}
            adv_results.append(r)
            existing_results[h.hypothesis_id] = r
            save_json(adv_file, {"results": adv_results})
            print(f"    ERROR: {e}")

    # Write final result
    cond_result = {
        "condition": condition,
        "n_hypotheses": len(hyps),
        "n_testable": sum(1 for h in hyps if h.is_testable),
        "n_survived": sum(1 for a in adv_results if a.get("survives")),
        "n_killed": sum(1 for a in adv_results if not a.get("survives") and not a.get("skipped") and not a.get("error")),
        "hypotheses": [{"id": h.hypothesis_id, "claim": (h.claim or "")[:300],
                        "mechanism": (h.mechanism or "")[:300],
                        "falsifier": (h.falsifier or "")[:300] if h.falsifier else "",
                        "is_testable": h.is_testable}
                       for h in hyps],
        "adversarial": adv_results,
    }
    save_json(result_file, cond_result)
    print(f"  [{case_id}-{condition}] Done: {cond_result['n_hypotheses']} hyps, "
          f"{cond_result['n_survived']} survived, {cond_result['n_killed']} killed")
    return "COMPLETED"


def main():
    # ===== MACHINE-ENFORCED PROTOCOL LOCK (audit finding A) =====
    # DXP-005 is PAUSED. The runner cannot proceed unless PROGRAM_STATE.json
    # explicitly says status=AUTHORIZED.
    from engine.protocol_lock import assert_experiment_authorized
    assert_experiment_authorized("DXP-005")

    if len(sys.argv) < 3:
        print("Usage: python3 scripts/run_dxp005_step.py <step> <case_id> [condition]")
        print("  step: upstream | hypotheses | adversarial")
        print(f"  case_id: {sorted(CASES.keys())}")
        print(f"  condition (for hypotheses/adversarial): {CONDITIONS}")
        return

    step = sys.argv[1]
    case_id = sys.argv[2]
    condition = sys.argv[3] if len(sys.argv) > 3 else None

    if case_id not in CASES:
        print(f"ERROR: case '{case_id}' not in CASES")
        return

    provider = make_provider()
    print(f"Provider: {provider.provider_name} / {provider.model_name}")
    print(f"Step: {step}  Case: {case_id}  Condition: {condition}")
    print(f"Started: {time.strftime('%H:%M:%S')}")

    t0 = time.time()
    if step == "upstream":
        result = step_upstream(case_id, provider)
    elif step == "hypotheses":
        if condition not in CONDITIONS:
            print(f"ERROR: condition must be one of {CONDITIONS}")
            return
        result = step_hypotheses(case_id, condition, provider)
    elif step == "adversarial":
        if condition not in CONDITIONS:
            print(f"ERROR: condition must be one of {CONDITIONS}")
            return
        result = step_adversarial(case_id, condition, provider)
    else:
        print(f"ERROR: unknown step '{step}'")
        return

    t1 = time.time()
    print(f"Elapsed: {t1-t0:.1f}s  Result: {result}")


if __name__ == "__main__":
    main()
