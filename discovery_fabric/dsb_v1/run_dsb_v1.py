"""
DSB V1 — Orchestrator
======================

Runs the full DSB V1 pipeline:
  1. Build cases (real + fabricated)
  2. Build payloads + run leakage audit
  3. Generate receipts (4 arms × 20 cases = 80)
  4. Score receipts (deterministic)
  5. Build human adjudication packets
  6. Run recomputation check
  7. Produce exit-gate report

The exit gate requires ALL of:
  (E1) Leakage audit: PASS (all 80 payloads leak-nothing)
  (E2) Raw payload hashes: ALL 80 verified
  (E3) Scorer validation: reproducible (byte-identical modulo timestamps)
  (E4) Controls: 4 arms × 20 cases, all 80 generated, all hash-sealed
  (E5) Human adjudication: packets built (adjudication itself is PENDING)
  (E6) Reproducible recomputation: all 5 checks PASS

If ALL 6 exit-gate components pass, DSB V1 is COMPLETE.
Only then do we decide what the next architecture should be.
"""
import json
import hashlib
import sys
from pathlib import Path
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from discovery_fabric.dsb_v1.leakage_audit import audit_all_payloads
from discovery_fabric.dsb_v1.payload_builder import build_payload, verify_payload
from discovery_fabric.dsb_v1.scorer import score_all
from discovery_fabric.dsb_v1.human_adjudication_packet import build_all_packets
from discovery_fabric.dsb_v1.recomputation_check import (
    check_leakage_audit_passes,
    check_leakage_audit_reproducibility,
    check_scorer_reproducibility,
    check_adjudication_packet_reproducibility,
    check_receipt_integrity,
)
from discovery_fabric.dsb_v1.case_schema import load_case


def exit_gate_E1_leakage_audit() -> dict:
    """E1. Leakage audit passes on all 80 payloads."""
    result = audit_all_payloads()
    return {
        "gate": "E1_LEAKAGE_AUDIT",
        "passed": result["overall_pass"],
        "n_payloads": result["n_payloads"],
        "n_pass": result["n_pass"],
        "n_fail": result["n_fail"],
    }


def exit_gate_E2_payload_hashes() -> dict:
    """E2. All 80 payload hashes verified."""
    REPO = Path(__file__).resolve().parents[2]
    real_dir = REPO / "discovery_fabric/dsb_v1/cases/real"
    fab_dir = REPO / "discovery_fabric/dsb_v1/cases/fabricated"
    arms = ["LLM_only", "mechanism_only", "combination", "full_system"]
    n_total = 0
    n_ok = 0
    for d in [real_dir, fab_dir]:
        for case_path in sorted(d.glob("DSB-*.json")):
            case = load_case(case_path)
            for arm in arms:
                payload = build_payload(case, arm)
                n_total += 1
                if verify_payload(payload):
                    n_ok += 1
    return {
        "gate": "E2_PAYLOAD_HASHES",
        "passed": n_ok == n_total,
        "n_total": n_total,
        "n_ok": n_ok,
    }


def exit_gate_E3_scorer_validation() -> dict:
    """E3. Scorer is reproducible."""
    check = check_scorer_reproducibility()
    return {
        "gate": "E3_SCORER_VALIDATION",
        "passed": check["passed"],
        "n_scores": check["n_scores"],
    }


def exit_gate_E4_controls() -> dict:
    """E4. All 4 arms × 20 cases generated and hash-sealed."""
    receipt_check = check_receipt_integrity()
    return {
        "gate": "E4_CONTROLS",
        "passed": receipt_check["passed"],
        "n_total": receipt_check["n_total"],
        "n_ok": receipt_check["n_ok"],
        "arms": ["LLM_only", "mechanism_only", "combination", "full_system"],
        "n_cases": 20,
        "expected_total": 80,
    }


def exit_gate_E5_human_adjudication() -> dict:
    """E5. Human adjudication.

    RELABELED (per directive 2026-08-12): E5 is PENDING_HUMAN_ADJUDICATION,
    not PASS. Packets are built, but the actual human adjudication by 2-3
    independent expert adjudicators has NOT been performed.

    E5 passes ONLY when ALL of the following are true:
      (a) 2-3 independent expert adjudicators have scored all 80 blind packets
      (b) Inter-rater agreement is measured (Cohen's kappa for 2 raters,
          Fleiss' kappa for 3+ raters)
      (c) Human vs deterministic-scorer confusion matrices are computed
          separately for real and fabricated cases
      (d) Adjudicator-blind review of the 12 machine "recoveries" is complete
      (e) Adjudicator-blind review of all cases where fabricated > real is complete
      (f) The fabricated-vs-real inversion is explained

    Until ALL of (a)-(f) are complete, E5 is PENDING and DSB V1 is NOT closed.
    """
    result = build_all_packets()
    packets_built = result["n_packets"] == 80
    return {
        "gate": "E5_HUMAN_ADJUDICATION",
        "status": "PENDING_HUMAN_ADJUDICATION",  # was incorrectly "PASS" before
        "passed": False,  # PENDING — not PASS until human adjudication is complete
        "packets_built": packets_built,
        "n_packets": result["n_packets"],
        "adjudication_performed": False,
        "required_for_close": [
            "2-3 independent expert adjudicators score all 80 blind packets",
            "Inter-rater agreement measured (Cohen/Fleiss kappa)",
            "Human vs deterministic-scorer confusion matrices (real + fabricated separate)",
            "Adjudicator-blind review of 12 machine 'recoveries'",
            "Adjudicator-blind review of all fabricated > real cases",
            "Fabricated-vs-real inversion explained",
        ],
        "note": (
            "Packets are built and ready at adjudication/adjudication_packets_BLIND.json. "
            "Human adjudication is PENDING — must be performed by 2-3 INDEPENDENT expert "
            "adjudicators (NOT the experimenter, NOT an LLM proxy). "
            "See ADJUDICATOR_INSTRUCTIONS.md for rubric and submission format."
        ),
    }


def exit_gate_E6_reproducible_recomputation() -> dict:
    """E6. All 5 recomputation checks pass."""
    checks = [
        check_leakage_audit_passes(),
        check_leakage_audit_reproducibility(),
        check_scorer_reproducibility(),
        check_adjudication_packet_reproducibility(),
        check_receipt_integrity(),
    ]
    n_pass = sum(1 for c in checks if c["passed"])
    return {
        "gate": "E6_REPRODUCIBLE_RECOMPUTATION",
        "passed": n_pass == len(checks),
        "n_checks": len(checks),
        "n_pass": n_pass,
        "checks": [c["check"] for c in checks],
    }


def run_full_pipeline() -> dict:
    """Run the full DSB V1 pipeline and produce the exit-gate report."""
    print("=" * 72)
    print("DSB V1 — ORCHESTRATOR (FULL PIPELINE)")
    print("=" * 72)
    print()

    gates = [
        exit_gate_E1_leakage_audit(),
        exit_gate_E2_payload_hashes(),
        exit_gate_E3_scorer_validation(),
        exit_gate_E4_controls(),
        exit_gate_E5_human_adjudication(),
        exit_gate_E6_reproducible_recomputation(),
    ]

    print("EXIT GATE STATUS:")
    print(f"{'GATE':<35} {'STATUS':<10} DETAILS")
    print("-" * 80)
    for g in gates:
        if g.get("status") == "PENDING_HUMAN_ADJUDICATION":
            status_str = "PENDING"
        elif g["passed"]:
            status_str = "PASS"
        else:
            status_str = "FAIL"
        details = ", ".join(f"{k}={v}" for k, v in g.items()
                            if k not in ("gate", "passed", "status", "required_for_close", "note"))
        print(f"{g['gate']:<35} {status_str:<10} {details[:55]}")

    n_pass = sum(1 for g in gates if g["passed"])
    n_fail = sum(1 for g in gates if not g["passed"])
    n_pending = sum(1 for g in gates if g.get("status") == "PENDING_HUMAN_ADJUDICATION")
    # DSB V1 is NOT closed if ANY gate is failed OR pending
    overall_pass = n_fail == 0 and n_pending == 0

    print()
    if n_pending > 0:
        print(f"EXIT GATE: NOT CLOSED ({n_pending} gate(s) PENDING human adjudication)")
    else:
        print(f"EXIT GATE: {'PASS' if overall_pass else 'FAIL'}")
    print(f"  {n_pass} passed, {n_fail} failed, {n_pending} pending")
    print(f"  DSB V1 SCIENTIFICALLY CLOSED: {'YES' if overall_pass else 'NO'}")

    # Get scorer summary
    scorer_result = score_all()
    scores = scorer_result["scores"]
    from collections import defaultdict
    summary = defaultdict(lambda: {"n": 0, "mech_reconstructed": 0, "disc_recovered": 0,
                                    "mech_score_sum": 0.0, "disc_score_sum": 0.0})
    for s in scores:
        arm = s["arm"]
        ctype = s["case_type"]
        key = (arm, ctype)
        summary[key]["n"] += 1
        if s["mechanism_reconstruction"]["verdict"] == "RECONSTRUCTED":
            summary[key]["mech_reconstructed"] += 1
        if s["discovery_structure_recovery"]["verdict"] == "RECOVERED":
            summary[key]["disc_recovered"] += 1
        summary[key]["mech_score_sum"] += s["mechanism_reconstruction"]["score"]
        summary[key]["disc_score_sum"] += s["discovery_structure_recovery"]["score"]

    print()
    print("SCORER RESULTS (deterministic):")
    print(f"{'Arm':<16} {'Type':<12} {'N':>3} {'MechR':>6} {'DiscR':>6} {'MechAvg':>8} {'DiscAvg':>8}")
    print("-" * 70)
    for (arm, ctype), s in sorted(summary.items()):
        mech_avg = s["mech_score_sum"] / max(s["n"], 1)
        disc_avg = s["disc_score_sum"] / max(s["n"], 1)
        print(f"{arm:<16} {ctype:<12} {s['n']:>3} {s['mech_reconstructed']:>6} {s['disc_recovered']:>6} {mech_avg:>8.3f} {disc_avg:>8.3f}")

    report = {
        "schema_version": "1.0.0",
        "report_type": "DSB_V1_EXIT_GATE",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "exit_gates": gates,
        "overall_pass": overall_pass,
        "n_gates_passed": n_pass,
        "n_gates_total": len(gates),
        "scorer_summary": {
            f"{arm}|{ctype}": dict(s) for (arm, ctype), s in sorted(summary.items())
        },
        "scorer_scores": scores,
    }

    # Seal
    canonical = json.dumps(report, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    report["report_hash"] = hashlib.sha256(canonical.encode()).hexdigest()

    return report


def main():
    report = run_full_pipeline()
    out_path = REPO / "discovery_fabric/dsb_v1/audit/exit_gate_report.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\nExit gate report: {out_path}")
    print(f"Report hash: {report['report_hash'][:32]}...")


if __name__ == "__main__":
    main()
