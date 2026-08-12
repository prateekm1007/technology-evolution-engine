"""
ADJUDICATION_ENGINE_V1 — Comparison Engine
============================================

Runs AFTER the CTO submits adjudications. Verifies temporal ordering,
computes confusion matrix / precision / recall / FP rate / agreement /
disagreements, generates forensic case files, produces final report.

VERIFICATIONS BEFORE RUNNING:
  1. CTO ledger exists (ledger/cto_adjudication.json)
  2. CTO ledger has 80 entries
  3. CTO submitted_at timestamp is AFTER vault sealed_at timestamp
  4. Vault hash matches (vault not tampered with)

OUTPUTS:
  - analysis/comparison_results.json (machine-readable)
  - analysis/confusion_matrices.json
  - disagreements/forensic_case_*.json (one per disagreement)
  - DSB_V1_CTO_ADJUDICATION_REPORT.md

EVIDENCE TIER: AI_CTO_ADJUDICATION (NOT HUMAN_VALIDATED)
NO architecture change permitted based on this adjudication alone.
"""
import json
import hashlib
import sys
import os
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter, defaultdict

REPO = Path(__file__).resolve().parents[3]
os.chdir(REPO)
sys.path.insert(0, str(REPO))

ENGINE_DIR = REPO / "discovery_fabric" / "dsb_v1" / "adjudication_engine_v1"
LEDGER_DIR = ENGINE_DIR / "ledger"
VAULT_DIR = ENGINE_DIR / "vault"
ANALYSIS_DIR = ENGINE_DIR / "analysis"
DISAGREEMENT_DIR = ENGINE_DIR / "disagreements"


# =============================================================================
# Verification
# =============================================================================

def verify_prerequisites() -> tuple[bool, list[str]]:
    """Verify all prerequisites before running comparison."""
    failures = []

    # 1. CTO ledger exists
    ledger_path = LEDGER_DIR / "cto_adjudication.json"
    if not ledger_path.exists():
        failures.append("CTO ledger not found at ledger/cto_adjudication.json. CTO must adjudicate first.")
        return (False, failures)

    with open(ledger_path) as f:
        ledger = json.load(f)

    # 2. 80 entries
    adjudications = ledger.get("adjudications", [])
    if len(adjudications) != 80:
        failures.append(f"CTO ledger has {len(adjudications)} entries, expected 80.")

    # 3. submitted_at is AFTER vault sealed_at
    vault_path = VAULT_DIR / "machine_score_vault.json"
    if not vault_path.exists():
        failures.append("Machine score vault not found.")
        return (False, failures)

    with open(vault_path) as f:
        vault = json.load(f)

    submitted_at = ledger.get("submitted_at", "")
    sealed_at = vault.get("sealed_at", "")
    try:
        sub_dt = datetime.fromisoformat(submitted_at.replace("Z", "+00:00"))
        seal_dt = datetime.fromisoformat(sealed_at.replace("Z", "+00:00"))
        if sub_dt <= seal_dt:
            failures.append(
                f"TEMPORAL VIOLATION: CTO submitted_at ({sub_dt}) is NOT after "
                f"vault sealed_at ({seal_dt}). CTO may have read the vault before adjudicating."
            )
    except (ValueError, TypeError) as e:
        failures.append(f"Cannot parse timestamps: {e}")

    # 4. Vault hash matches
    stored_vault_hash = vault.get("vault_hash")
    vault_copy = {k: v for k, v in vault.items() if k != "vault_hash"}
    canonical = json.dumps(vault_copy, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    computed_vault_hash = hashlib.sha256(canonical.encode()).hexdigest()
    if stored_vault_hash != computed_vault_hash:
        failures.append("VAULT TAMPERED: vault_hash mismatch. Vault was modified after sealing.")

    return (len(failures) == 0, failures)


# =============================================================================
# Comparison logic
# =============================================================================

def load_data() -> tuple[dict, dict, list]:
    """Load CTO ledger, machine vault, and full packets."""
    with open(LEDGER_DIR / "cto_adjudication.json") as f:
        ledger = json.load(f)
    with open(VAULT_DIR / "machine_score_vault.json") as f:
        vault = json.load(f)
    with open(ENGINE_DIR / "cto_packets_FULL.json") as f:
        packets_data = json.load(f)
    return ledger, vault, packets_data["packets"]


def compute_confusion_matrix(cto_positives: list[bool], machine_positives: list[bool]) -> dict:
    """Compute TP/FP/TN/FN + precision/recall/F1/accuracy/FP_rate."""
    tp = sum(1 for c, m in zip(cto_positives, machine_positives) if c and m)
    fp = sum(1 for c, m in zip(cto_positives, machine_positives) if not c and m)
    tn = sum(1 for c, m in zip(cto_positives, machine_positives) if not c and not m)
    fn = sum(1 for c, m in zip(cto_positives, machine_positives) if c and not m)
    precision = tp / max(tp + fp, 1)
    recall = tp / max(tp + fn, 1)
    f1 = 2 * precision * recall / max(precision + recall, 1e-9)
    accuracy = (tp + tn) / max(tp + fp + tn + fn, 1)
    fp_rate = fp / max(fp + tn, 1)
    return {
        "tp": tp, "fp": fp, "tn": tn, "fn": fn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "accuracy": round(accuracy, 4),
        "false_positive_rate": round(fp_rate, 4),
    }


def run_comparison() -> dict:
    """Run the full comparison."""
    ok, failures = verify_prerequisites()
    if not ok:
        return {"status": "FROZEN", "prerequisite_failures": failures}

    ledger, vault, packets = load_data()

    # Map packet_id -> CTO adjudication
    cto_by_packet = {a["packet_id"]: a for a in ledger["adjudications"]}

    # Map receipt_id -> machine score
    machine_by_receipt = {s["receipt_id"]: s for s in vault["scores"]}

    # Map packet_id -> receipt_id (from full packets)
    packet_to_receipt = {p["packet_id"]: p["_internal"]["receipt_id"] for p in packets}
    packet_to_internal = {p["packet_id"]: p["_internal"] for p in packets}

    # Build comparison rows
    rows = []
    for packet_id, cto_adj in cto_by_packet.items():
        receipt_id = packet_to_receipt.get(packet_id)
        if not receipt_id:
            continue
        machine = machine_by_receipt.get(receipt_id)
        if not machine:
            continue
        internal = packet_to_internal[packet_id]

        # CTO Q7 (OVERALL_DISCOVERY) vs machine discovery_structure_recovery_verdict
        cto_discovery = cto_adj.get("Q7_OVERALL_DISCOVERY", "").upper() == "YES"
        machine_discovery = machine["discovery_structure_recovery_verdict"] == "RECOVERED"

        # CTO Q6 (REAL_VS_FABRICATED) vs actual case_type
        cto_real_fab = cto_adj.get("Q6_REAL_VS_FABRICATED", "").upper()
        actual_case_type = internal["case_type"].upper()  # "REAL" or "FABRICATED"

        # CTO Q1 (MECHANISTIC_VALIDITY) vs machine mechanism_reconstruction_verdict
        cto_mech = cto_adj.get("Q1_MECHANISTIC_VALIDITY", "").upper()
        cto_mech_positive = cto_mech in ("YES", "PARTIAL")
        machine_mech_positive = machine["mechanism_reconstruction_verdict"] == "RECONSTRUCTED"

        rows.append({
            "packet_id": packet_id,
            "receipt_id": receipt_id,
            "case_id": internal["case_id"],
            "case_type": internal["case_type"],
            "arm": internal["arm"],
            "cto_q1_mechanistic_validity": cto_mech,
            "cto_q2_discovery_structure": cto_adj.get("Q2_DISCOVERY_STRUCTURE_VALIDITY", ""),
            "cto_q3_novelty": cto_adj.get("Q3_NOVELTY", ""),
            "cto_q4_falsifiability": cto_adj.get("Q4_FALSIFIABILITY", ""),
            "cto_q5_experimental_coherence": cto_adj.get("Q5_EXPERIMENTAL_COHERENCE", ""),
            "cto_q6_real_vs_fabricated": cto_real_fab,
            "cto_q6_actual_case_type": actual_case_type,
            "cto_q6_correct": cto_real_fab == actual_case_type,
            "cto_q7_overall_discovery": cto_adj.get("Q7_OVERALL_DISCOVERY", ""),
            "cto_discovery_positive": cto_discovery,
            "machine_mechanism_verdict": machine["mechanism_reconstruction_verdict"],
            "machine_mechanism_positive": machine_mech_positive,
            "machine_discovery_verdict": machine["discovery_structure_recovery_verdict"],
            "machine_discovery_positive": machine_discovery,
            "machine_discovery_score": machine["discovery_structure_recovery_score"],
            "agreement_discovery": cto_discovery == machine_discovery,
            "agreement_mechanism": cto_mech_positive == machine_mech_positive,
        })

    # Confusion matrices
    # Discovery: CTO Q7 vs machine discovery_structure_recovery
    # Separate by case_type (real vs fabricated)
    discovery_matrices = {}
    for case_type in ["real", "fabricated", "all"]:
        subset = [r for r in rows if case_type == "all" or r["case_type"] == case_type]
        cto_pos = [r["cto_discovery_positive"] for r in subset]
        machine_pos = [r["machine_discovery_positive"] for r in subset]
        discovery_matrices[case_type] = compute_confusion_matrix(cto_pos, machine_pos)

    # Real-vs-fabricated accuracy
    rvs_correct = sum(1 for r in rows if r["cto_q6_correct"])
    rvs_accuracy = rvs_correct / max(len(rows), 1)

    # Agreement
    discovery_agreement = sum(1 for r in rows if r["agreement_discovery"]) / max(len(rows), 1)
    mechanism_agreement = sum(1 for r in rows if r["agreement_mechanism"]) / max(len(rows), 1)

    # Disagreements
    disagreements = [r for r in rows if not r["agreement_discovery"]]

    return {
        "status": "COMPUTED",
        "n_rows": len(rows),
        "evidence_tier": "AI_CTO_ADJUDICATION",
        "tier_note": "NOT HUMAN_VALIDATED. CTO is not independent (per MC-1).",
        "vault_sealed_at": vault["sealed_at"],
        "cto_submitted_at": ledger.get("submitted_at"),
        "discovery_confusion_matrices": discovery_matrices,
        "real_vs_fabricated_accuracy": round(rvs_accuracy, 4),
        "real_vs_fabricated_correct": rvs_correct,
        "discovery_agreement": round(discovery_agreement, 4),
        "mechanism_agreement": round(mechanism_agreement, 4),
        "n_disagreements": len(disagreements),
        "disagreements": disagreements,
        "all_rows": rows,
    }


# =============================================================================
# Disagreement forensic files
# =============================================================================

def generate_disagreement_forensic_files(comparison: dict):
    """Generate one forensic case file per disagreement."""
    from discovery_fabric.dsb_v1.case_schema import load_case

    DISAGREEMENT_DIR.mkdir(parents=True, exist_ok=True)

    # Load cases for evidence
    cases = {}
    for d in [REPO / "discovery_fabric/dsb_v1/cases/real",
              REPO / "discovery_fabric/dsb_v1/cases/fabricated"]:
        for cp in sorted(d.glob("DSB-*.json")):
            case = load_case(cp)
            cases[case["case_id"]] = case

    # Load receipts
    receipts = {}
    receipts_dir = REPO / "discovery_fabric/dsb_v1/receipts"
    for rp in sorted(receipts_dir.glob("RECEIPT-*.json")):
        with open(rp) as f:
            r = json.load(f)
        receipts[r["receipt_id"]] = r

    n_generated = 0
    for disagreement in comparison.get("disagreements", []):
        case = cases.get(disagreement["case_id"], {})
        receipt = receipts.get(disagreement["receipt_id"], {})

        forensic = {
            "schema_version": "1.0.0",
            "forensic_type": "DSB_V1_CTO_MACHINE_DISAGREEMENT",
            "packet_id": disagreement["packet_id"],
            "receipt_id": disagreement["receipt_id"],
            "case_id": disagreement["case_id"],
            "case_type": disagreement["case_type"],
            "arm": disagreement["arm"],
            "evidence": {
                "exposed_facts": case.get("exposed_facts", []),
                "proposed_relationship": receipt.get("proposed_relationship", ""),
                "proposed_mechanism": receipt.get("mechanism", ""),
                "proposed_constraint_released": receipt.get("constraint_released", ""),
            },
            "machine_decision": {
                "mechanism_reconstruction_verdict": disagreement["machine_mechanism_verdict"],
                "discovery_structure_recovery_verdict": disagreement["machine_discovery_verdict"],
                "discovery_structure_recovery_score": disagreement["machine_discovery_score"],
            },
            "cto_decision": {
                "Q1_mechanistic_validity": disagreement["cto_q1_mechanistic_validity"],
                "Q2_discovery_structure": disagreement["cto_q2_discovery_structure"],
                "Q3_novelty": disagreement["cto_q3_novelty"],
                "Q4_falsifiability": disagreement["cto_q4_falsifiability"],
                "Q5_experimental_coherence": disagreement["cto_q5_experimental_coherence"],
                "Q6_real_vs_fabricated": disagreement["cto_q6_real_vs_fabricated"],
                "Q7_overall_discovery": disagreement["cto_q7_overall_discovery"],
            },
            "disagreement_reason": (
                f"CTO Q7_overall_discovery = {disagreement['cto_q7_overall_discovery']} "
                f"(positive={disagreement['cto_discovery_positive']}), "
                f"but machine discovery_structure_recovery_verdict = "
                f"{disagreement['machine_discovery_verdict']} "
                f"(positive={disagreement['machine_discovery_positive']}). "
                f"Agreement = {disagreement['agreement_discovery']}."
            ),
            "evidence_tier": "AI_CTO_ADJUDICATION",
            "tier_note": "NOT HUMAN_VALIDATED.",
        }
        canonical = json.dumps(forensic, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        forensic["forensic_hash"] = hashlib.sha256(canonical.encode()).hexdigest()

        out_path = DISAGREEMENT_DIR / f"forensic_case_{disagreement['packet_id']}.json"
        with open(out_path, "w") as f:
            json.dump(forensic, f, indent=2, ensure_ascii=False)
        n_generated += 1

    return n_generated


# =============================================================================
# Report generation
# =============================================================================

def produce_report(comparison: dict):
    """Produce DSB_V1_CTO_ADJUDICATION_REPORT.md."""
    report = []
    report.append("# DSB V1 — CTO ADJUDICATION REPORT")
    report.append("")
    report.append(f"**Date:** {datetime.now(timezone.utc).isoformat()}")
    report.append(f"**Engine:** ADJUDICATION_ENGINE_V1")
    report.append(f"**Evidence tier:** AI_CTO_ADJUDICATION")
    report.append(f"**Tier note:** NOT HUMAN_VALIDATED. CTO is not independent (per MC-1). This adjudication decides whether the benchmark/scorer survives; it does NOT manufacture human-validation status.")
    report.append(f"**Vault sealed at:** {comparison.get('vault_sealed_at', 'N/A')}")
    report.append(f"**CTO submitted at:** {comparison.get('cto_submitted_at', 'N/A')}")
    report.append("")

    if comparison["status"] != "COMPUTED":
        report.append("## Status: FROZEN")
        report.append("")
        report.append("Comparison cannot run. Prerequisites not met:")
        for f in comparison.get("prerequisite_failures", []):
            report.append(f"- {f}")
        report.append("")
        report.append("**No architecture change permitted.**")
        with open(ENGINE_DIR / "DSB_V1_CTO_ADJUDICATION_REPORT.md", "w") as f:
            f.write("\n".join(report))
        return

    report.append("## 1. Verification")
    report.append("")
    report.append(f"- CTO ledger entries: **{comparison['n_rows']}/80**")
    report.append(f"- Temporal ordering verified: CTO submitted AFTER vault sealed ✓")
    report.append(f"- Vault hash verified: vault not tampered ✓")
    report.append("")

    report.append("## 2. Confusion Matrices (CTO Q7 vs Machine Discovery-Structure Recovery)")
    report.append("")
    report.append("CTO Q7_OVERALL_DISCOVERY (YES=positive) vs Machine discovery_structure_recovery_verdict (RECOVERED=positive).")
    report.append("")
    for case_type in ["real", "fabricated", "all"]:
        m = comparison["discovery_confusion_matrices"][case_type]
        report.append(f"### {case_type.upper()} cases")
        report.append("")
        report.append(f"| TP | FP | TN | FN | Precision | Recall | F1 | Accuracy | FP Rate |")
        report.append(f"|---|---|---|---|---|---|---|---|---|")
        report.append(f"| {m['tp']} | {m['fp']} | {m['tn']} | {m['fn']} | {m['precision']} | {m['recall']} | {m['f1']} | {m['accuracy']} | {m['false_positive_rate']} |")
        report.append("")

    report.append("## 3. Real-vs-Fabricated Accuracy")
    report.append("")
    report.append(f"CTO Q6_REAL_VS_FABRICATED correctness: **{comparison['real_vs_fabricated_correct']}/{comparison['n_rows']} ({comparison['real_vs_fabricated_accuracy']*100:.1f}%)**")
    report.append("")
    report.append("This measures whether the CTO can distinguish real discoveries from plausible counterfactuals based on scientific plausibility alone.")
    report.append("")

    report.append("## 4. Agreement")
    report.append("")
    report.append(f"- Discovery agreement (CTO Q7 vs machine): **{comparison['discovery_agreement']*100:.1f}%**")
    report.append(f"- Mechanism agreement (CTO Q1 vs machine): **{comparison['mechanism_agreement']*100:.1f}%**")
    report.append("")

    report.append("## 5. Disagreements")
    report.append("")
    report.append(f"Total disagreements: **{comparison['n_disagreements']}**")
    report.append("")
    if comparison['n_disagreements'] > 0:
        report.append("Per-disagreement forensic case files generated in `disagreements/`.")
        report.append("")
        report.append("| Packet ID | Case Type | Arm | CTO Q7 | Machine | CTO Q6 | Score |")
        report.append("|---|---|---|---|---|---|---|")
        for d in comparison['disagreements']:
            report.append(f"| {d['packet_id']} | {d['case_type']} | {d['arm']} | {d['cto_q7_overall_discovery']} | {d['machine_discovery_verdict']} | {d['cto_q6_real_vs_fabricated']} | {d['machine_discovery_score']} |")
    report.append("")

    # Scorer survival decision
    fp_rate_fab = comparison["discovery_confusion_matrices"]["fabricated"]["false_positive_rate"]
    report.append("## 6. Scorer Survival Decision")
    report.append("")
    report.append(f"False-positive rate on FABRICATED cases: **{fp_rate_fab*100:.1f}%**")
    report.append("")
    if fp_rate_fab > 0.30:
        report.append("**SCORER DOES NOT SURVIVE.** False-positive rate on fabricated cases exceeds 30%. Triggers scorer-calibration protocol (separate 40-case set, NOT these 80).")
    elif comparison["discovery_agreement"] < 0.60:
        report.append("**SCORER DOES NOT SURVIVE.** Overall agreement below 60%. Scorer does not align with CTO judgment. Triggers scorer-calibration protocol.")
    else:
        report.append("**SCORER SURVIVES.** False-positive rate on fabricated cases ≤ 30% and agreement ≥ 60%. Benchmark continues with current scorer.")
    report.append("")
    report.append("**Either way: NOT human-validated. No architecture change permitted based on this adjudication alone.**")
    report.append("")

    report.append("## 7. What This Adjudication Does NOT Establish")
    report.append("")
    report.append("- ❌ Does NOT establish human validation (CTO is not independent)")
    report.append("- ❌ Does NOT justify architecture changes")
    report.append("- ❌ Does NOT override the DSB V1 PENDING_HUMAN_ADJUDICATION status")
    report.append("- ❌ Does NOT manufacture a discovery rate")
    report.append("")
    report.append("## 8. What This Adjudication DOES Establish")
    report.append("")
    report.append("- ✅ Whether the machine scorer agrees with informed CTO judgment")
    report.append("- ✅ Whether systematic false positives exist (fabricated cases scored as recoveries)")
    report.append("- ✅ Whether the CTO can distinguish real from fabricated (Q6 accuracy)")
    report.append("- ✅ Per-disagreement forensic evidence for review")
    report.append("")

    report.append("---")
    report.append("")
    report.append("**End of DSB V1 CTO Adjudication Report.**")
    report.append("")
    report.append("**Evidence tier: AI_CTO_ADJUDICATION (NOT HUMAN_VALIDATED).**")
    report.append("**No architecture change permitted based on this adjudication alone.**")

    with open(ENGINE_DIR / "DSB_V1_CTO_ADJUDICATION_REPORT.md", "w") as f:
        f.write("\n".join(report))


# =============================================================================
# Main
# =============================================================================

def main():
    print("=" * 72)
    print("ADJUDICATION_ENGINE_V1 — COMPARISON")
    print("=" * 72)
    print()

    comparison = run_comparison()

    if comparison["status"] != "COMPUTED":
        print("Status: FROZEN — prerequisites not met")
        for f in comparison.get("prerequisite_failures", []):
            print(f"  - {f}")
        produce_report(comparison)
        return

    print(f"Status: COMPUTED")
    print(f"Rows compared: {comparison['n_rows']}")
    print()
    print("Confusion matrices (CTO Q7 vs Machine Discovery):")
    for ct in ["real", "fabricated", "all"]:
        m = comparison["discovery_confusion_matrices"][ct]
        print(f"  {ct:12s}: TP={m['tp']} FP={m['fp']} TN={m['tn']} FN={m['fn']} | "
              f"P={m['precision']} R={m['recall']} F1={m['f1']} FPr={m['false_positive_rate']}")
    print()
    print(f"Real-vs-fabricated accuracy: {comparison['real_vs_fabricated_accuracy']*100:.1f}%")
    print(f"Discovery agreement: {comparison['discovery_agreement']*100:.1f}%")
    print(f"Mechanism agreement: {comparison['mechanism_agreement']*100:.1f}%")
    print(f"Disagreements: {comparison['n_disagreements']}")

    # Generate forensic files
    n_forensic = generate_disagreement_forensic_files(comparison)
    print(f"\nForensic case files generated: {n_forensic}")

    # Save comparison results
    with open(ANALYSIS_DIR / "comparison_results.json", "w") as f:
        json.dump(comparison, f, indent=2, ensure_ascii=False)

    # Produce report
    produce_report(comparison)
    print(f"\nReport: {ENGINE_DIR / 'DSB_V1_CTO_ADJUDICATION_REPORT.md'}")


if __name__ == "__main__":
    main()
