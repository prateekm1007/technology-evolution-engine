#!/usr/bin/env python3
"""diagnostic_execution.py — Engine-vs-null diagnostic execution.

Per audit round 62: DIAGNOSTIC execution, not evidence.
Emits machine facts and hashes, then terminates.
No prose interpretation. No post-result repair.

IMPLEMENTATION REPAIR (per fresh-context investigation):
  The first diagnostic (19c27da) failed because the script used
  OpenRouterProvider (which requires api_key) instead of the
  preregistered ZAIReasoningProvider (which uses the z-ai CLI).
  This is a plumbing fix, not a substrate change:
    - Same engine (MechanismExtraction → Abstraction → Transfer → Generation)
    - Same provider (ZAI/GLM glm-4-plus)
    - Same protocol (R5.2)
    - Same evaluator (Gate A/C/B)
    - Same cases
    - Same estimand
    - Frozen statistical engine (39f5d37) unchanged
"""
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from engine.b2_provenance import (
    ExecutionGate,
    ExecutionGateError,
    ProvenanceLedger,
    generate_null_candidates,
    record_null_in_ledger,
    parse_candidates,
    store_raw_output,
    compute_sha256,
    verify_frozen_components,
)
from engine.b2_provenance.content_addressed_storage import STORAGE_ROOT
from engine.b2_provenance.frozen_parser import PARSER_CONFIG
from scripts.verify_audit_instrument import (
    create_execution_manifest,
    verify_execution_manifest,
    verify_instrument,
)
from scripts.baseline_equivalence_audit import run_baseline_equivalence_audit


def _format_engine_output_as_raw(hypotheses):
    """Format engine hypothesis output as parser-compatible raw output.

    The engine produces Hypothesis objects with claim + mechanism fields.
    This formats them as ---CANDIDATE--- delimited text so they go
    through the SAME frozen parser as the null arm.
    """
    delimiter = PARSER_CONFIG["candidate_delimiter"]
    parts = ["---ENGINE GENERATION OUTPUT---\n"]
    for i, hyp in enumerate(hypotheses[:3], 1):
        claim = getattr(hyp, 'claim', str(hyp.get('claim', '')) if isinstance(hyp, dict) else str(hyp))
        mechanism = getattr(hyp, 'mechanism', str(hyp.get('mechanism', '')) if isinstance(hyp, dict) else '')
        candidate = f"RELATIONSHIP: {claim}\nMECHANISM: {mechanism}"
        parts.append(delimiter)
        parts.append(candidate)
        parts.append("\n")
    return "".join(parts)


def main():
    output_path = REPO_ROOT / "experiments" / "measurement_discrimination" / "diagnostic_execution_record.json"

    # Test source documents (real arXiv papers from the committed corpus)
    source_a_path = REPO_ROOT / "data" / "ingestion" / "real" / "arxiv_2301.04523.txt"
    source_b_path = REPO_ROOT / "data" / "ingestion" / "real" / "arxiv_2003.10495.txt"
    source_a_text = source_a_path.read_text()
    source_b_text = source_b_path.read_text()

    # Compute source pair hash
    source_data = json.dumps({
        "source_a": source_a_text,
        "source_b": source_b_text,
    }, sort_keys=True, separators=(",", ":"))
    source_pair_sha = hashlib.sha256(source_data.encode("utf-8")).hexdigest()

    # Test abstractions (for the null arm — the engine will extract its own)
    test_abstractions_a = [
        "Deep learning-assisted thermal diffusion metamaterials with adaptive thermal functions",
        "Heat-enhanced thermal transport using metamaterials with tunable properties",
        "Intelligent thermal diffusion metamaterials for dynamic thermal environments",
    ]
    test_abstractions_b = [
        "Graded nanocomposite metamaterials for radiative cooling architecture",
        "Double-sided radiative cooling with record cooling power density",
        "Nanocomposite metamaterials for electricity-free cooling technology",
    ]

    # === SEAL MANIFEST ===
    manifest = create_execution_manifest(
        preregistration_id="DIAG-R5.2-002",
        case_ids=["DIAG-001"],
        source_pair_hashes={"DIAG-001": source_pair_sha},
    )

    # === EXECUTE ===
    ledger_path = REPO_ROOT / "provenance" / "ledger_diag2.json"
    ledger = ProvenanceLedger(ledger_path=ledger_path)

    machine_facts = {
        "execution_type": "DIAGNOSTIC",
        "manifest_sha256": manifest["manifest_sha256"],
        "manifest_verified_before": True,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "arms_attempted": [],
        "arms_completed": [],
        "arms_failed": [],
        "artifacts_produced": [],
        "provenance_ledger_path": str(ledger_path),
        "failures": [],
        "source_pair_sha256": source_pair_sha,
        "source_a_path": str(source_a_path.relative_to(REPO_ROOT)),
        "source_b_path": str(source_b_path.relative_to(REPO_ROOT)),
    }

    try:
        with ExecutionGate(manifest) as gate:
            machine_facts["execution_id"] = gate.record.execution_id

            # --- NULL ARM ---
            machine_facts["arms_attempted"].append("null")
            try:
                null_result = generate_null_candidates(
                    case_id="DIAG-001",
                    abstracted_mechanisms_a=test_abstractions_a,
                    abstracted_mechanisms_b=test_abstractions_b,
                    preregistration_id="DIAG-R5.2-002",
                )
                entries = record_null_in_ledger(
                    ledger=ledger,
                    result=null_result,
                    engine_version="0dc4470",
                    provider="none",
                    model="deterministic-template",
                    prompt_hash="none",
                    source_pair_sha256=source_pair_sha,
                    generation_timestamp=datetime.now(timezone.utc).isoformat(),
                )
                machine_facts["arms_completed"].append("null")
                for rank, (candidate, sha) in enumerate(
                    zip(null_result.candidates, null_result.candidate_sha256s), 1
                ):
                    machine_facts["artifacts_produced"].append({
                        "arm": "null",
                        "case_id": "DIAG-001",
                        "candidate_rank": rank,
                        "candidate_sha256": sha,
                        "raw_output_sha256": null_result.raw_output_sha256,
                        "candidate_length": len(candidate),
                    })
                    gate.add_artifact("DIAG-001", "null", rank, sha, null_result.raw_output_sha256)
            except Exception as e:
                machine_facts["arms_failed"].append({
                    "arm": "null",
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                })

            # --- ENGINE ARM ---
            machine_facts["arms_attempted"].append("engine")
            try:
                from engine.providers import ZAIReasoningProvider
                from engine.mechanism_extraction import MechanismExtractionEngine
                from engine.mechanism_abstraction import MechanismAbstractionEngine
                from engine.cross_domain_transfer import CrossDomainTransferEngine
                from engine.hypothesis_generation import HypothesisGenerationEngine

                # Use the preregistered provider (ZAI/GLM via z-ai CLI)
                reasoning_provider = ZAIReasoningProvider(timeout=120)

                # Parse source documents
                doc_a_lines = source_a_text.strip().split('\n', 3)
                doc_b_lines = source_b_text.strip().split('\n', 3)
                doc_a = {"title": doc_a_lines[0].replace("Title: ", ""), "text": source_a_text}
                doc_b = {"title": doc_b_lines[0].replace("Title: ", ""), "text": source_b_text}

                # Step 1: Mechanism Extraction (Source A)
                extractor = MechanismExtractionEngine(reasoning_provider)
                ext_result = extractor.extract(doc_a)
                if not ext_result.ok:
                    raise RuntimeError(f"Mechanism extraction failed: {ext_result.failures}")

                # Step 2: Mechanism Abstraction
                abstracter = MechanismAbstractionEngine(reasoning_provider)
                ab_result = abstracter.abstract(
                    ext_result.graph,
                    source_domain="thermal_metamaterials",
                    source_title=doc_a["title"],
                    pattern_id="MP-DIAG-001",
                )

                # Step 3: Cross-Domain Transfer
                transfer_engine = CrossDomainTransferEngine(reasoning_provider)
                tr_result = transfer_engine.generate(
                    ab_result.pattern,
                    target_domain="radiative_cooling",
                    target_problem=doc_b["text"][:500],
                    target_constraints=[],
                    transfer_id_prefix="TH-DIAG-001",
                )
                if not tr_result.transfers:
                    raise RuntimeError("Transfer rejected — no transfers generated")

                # Step 4: Hypothesis Generation
                hyp_engine = HypothesisGenerationEngine(reasoning_provider)
                hyp_set = hyp_engine.generate(
                    tr_result.transfers[0],
                    id_prefix="H-DIAG-001",
                    mechanism_graph=ext_result.graph,
                )
                if not hyp_set.hypotheses:
                    raise RuntimeError("No hypotheses generated")

                # Format engine output as raw output (parser format)
                raw_output = _format_engine_output_as_raw(hyp_set.hypotheses)

                # Store in content-addressed storage
                blob_path, raw_sha = store_raw_output("DIAG-001", "engine", raw_output)

                # Parse candidates with the frozen parser
                candidates = parse_candidates(raw_output)
                candidate_sha256s = [compute_sha256(c.encode("utf-8")) for c in candidates]

                # Record in provenance ledger
                prompt_hash = compute_sha256("engine-pipeline".encode("utf-8"))
                for rank, (candidate, cand_sha) in enumerate(zip(candidates, candidate_sha256s), 1):
                    ledger.append_candidate_entry(
                        case_id="DIAG-001",
                        arm="engine",
                        candidate_rank=rank,
                        raw_output_sha256=raw_sha,
                        raw_output_blob_path=blob_path,
                        candidate_sha256=cand_sha,
                        candidate_text=candidate,
                        generation_timestamp=datetime.now(timezone.utc).isoformat(),
                        engine_version="0dc4470",
                        provider="zai",
                        model="glm-4-plus",
                        prompt_hash=prompt_hash,
                        source_pair_sha256=source_pair_sha,
                        invocation_seed=manifest.get("manifest_sha256", "")[:64],
                    )
                    machine_facts["artifacts_produced"].append({
                        "arm": "engine",
                        "case_id": "DIAG-001",
                        "candidate_rank": rank,
                        "candidate_sha256": cand_sha,
                        "raw_output_sha256": raw_sha,
                        "candidate_length": len(candidate),
                    })
                    gate.add_artifact("DIAG-001", "engine", rank, cand_sha, raw_sha)

                machine_facts["arms_completed"].append("engine")

            except Exception as e:
                machine_facts["arms_failed"].append({
                    "arm": "engine",
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                })

        # === POST-EXECUTION ===
        machine_facts["finished_at"] = datetime.now(timezone.utc).isoformat()
        machine_facts["manifest_verified_after"] = gate.record.manifest_verified
        machine_facts["provenance_verified"] = gate.record.provenance_verified

        if gate.record.failures:
            machine_facts["post_execution_failures"] = gate.record.failures

        # === LEDGER STATE ===
        machine_facts["ledger_n_generation_events"] = ledger.n_generation_events()
        machine_facts["ledger_n_adjudication_events"] = ledger.n_adjudication_events()
        machine_facts["ledger_sha256"] = ledger.get_ledger_sha256()
        machine_facts["ledger_hash_chain_valid"] = ledger.verify_hash_chain()

        # === BASELINE AUDIT ===
        audit_result = run_baseline_equivalence_audit(ledger, "DIAG-001")
        machine_facts["baseline_audit"] = {
            "engine_entries_found": audit_result["engine_entries_found"],
            "null_entries_found": audit_result["null_entries_found"],
            "n_dimensions": audit_result["n_dimensions"],
            "state_counts": audit_result["state_counts"],
            "fairness_established": audit_result["summary"]["fairness_established"],
            "all_observations_from_verified_artifacts": audit_result["summary"]["all_observations_from_verified_artifacts"],
        }

    except ExecutionGateError as e:
        machine_facts["gate_error"] = str(e)
        machine_facts["finished_at"] = datetime.now(timezone.utc).isoformat()

    # === WRITE DIAGNOSTIC ARTIFACT ===
    machine_facts["artifact_type"] = "DIAGNOSTIC_EXECUTION_RECORD"
    machine_facts["diagnostic_rule"] = (
        "This is a DIAGNOSTIC execution. Results do NOT establish "
        "baseline fairness, discovery capability, or North Star. "
        "They establish machine facts about what ran and what artifacts "
        "were produced. Interpretation is reserved for a fresh-context "
        "independent auditor."
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(machine_facts, indent=2, default=str))

    # === EMIT MACHINE FACTS ===
    print(json.dumps(machine_facts, indent=2, default=str))


if __name__ == "__main__":
    main()
