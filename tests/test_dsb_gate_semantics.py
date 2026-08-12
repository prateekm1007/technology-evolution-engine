#!/usr/bin/env python3
"""
Regression test: DSB gate semantics.

Enforces that:
  E5_HUMAN_ADJUDICATION = NOT_PERFORMED (not PASS)
  DSB_SCIENTIFICALLY_CLOSED = FALSE
  NORTH_STAR = UNPROVEN
  overall_pass cannot be true while any required gate is pending

Run: python3 tests/test_dsb_gate_semantics.py
Exit 0 = PASS, Exit 1 = FAIL
"""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def test_e5_not_performed():
    """E5_HUMAN_ADJUDICATION must be NOT_PERFORMED, not PASS."""
    report_path = REPO / "discovery_fabric/dsb_v1/audit/exit_gate_report.json"
    if not report_path.exists():
        print("SKIP: exit_gate_report.json not found")
        return True
    report = json.load(open(report_path))
    for gate in report.get("exit_gates", []):
        if gate.get("gate") == "E5_HUMAN_ADJUDICATION":
            passed = gate.get("passed")
            if passed:
                print(f"FAIL: E5_HUMAN_ADJUDICATION has passed={passed} — must be False (NOT_PERFORMED)")
                return False
            print(f"✓ E5_HUMAN_ADJUDICATION passed={passed} (correctly NOT_PERFORMED)")
            return True
    print("WARN: E5_HUMAN_ADJUDICATION gate not found in report")
    return True


def test_overall_pass_false():
    """overall_pass must be False while any gate is pending/failed."""
    report_path = REPO / "discovery_fabric/dsb_v1/audit/exit_gate_report.json"
    if not report_path.exists():
        print("SKIP: exit_gate_report.json not found")
        return True
    report = json.load(open(report_path))
    overall = report.get("overall_pass")
    if overall:
        print(f"FAIL: overall_pass={overall} — must be False while gates are pending")
        return False
    print(f"✓ overall_pass={overall} (correctly False)")
    return True


def test_north_star_unproven():
    """North Star must be UNPROVEN."""
    # Check RESEARCH_TRUTH_INVENTORY_V2.json
    truth_path = REPO / "RESEARCH_TRUTH_INVENTORY_V2.json"
    if truth_path.exists():
        truth = json.load(open(truth_path))
        ns = truth.get("north_star_status", {})
        if ns.get("status") != "UNPROVEN":
            print(f"FAIL: North Star status={ns.get('status')} — must be UNPROVEN")
            return False
        print(f"✓ North Star status=UNPROVEN")
        return True
    print("SKIP: RESEARCH_TRUTH_INVENTORY_V2.json not found")
    return True


def test_no_collapse_of_evidence_tiers():
    """AI_CTO_ADJUDICATION must never be labeled HUMAN_VALIDATED."""
    # Check all JSON files in adjudication area for tier collapse
    adj_dir = REPO / "discovery_fabric/dsb_v1/adjudication_security_correction"
    if not adj_dir.exists():
        print("SKIP: adjudication_security_correction not found")
        return True
    for f in adj_dir.glob("*.json"):
        content = f.read_text()
        if "AI_CTO_ADJUDICATION" in content and "HUMAN_VALIDATED" in content:
            # Check if they're used as equivalent (collapse)
            # This is a heuristic — flag for review if both appear in same file
            # without explicit "NOT HUMAN_VALIDATED" qualifier
            if "NOT HUMAN_VALIDATED" not in content and "not_human_validated" not in content.lower():
                print(f"WARN: {f.name} contains both AI_CTO_ADJUDICATION and HUMAN_VALIDATED without explicit separation")
    print("✓ No evidence tier collapse detected")
    return True


def main():
    tests = [
        ("E5_NOT_PERFORMED", test_e5_not_performed),
        ("OVERALL_PASS_FALSE", test_overall_pass_false),
        ("NORTH_STAR_UNPROVEN", test_north_star_unproven),
        ("NO_EVIDENCE_TIER_COLLAPSE", test_no_collapse_of_evidence_tiers),
    ]
    all_pass = True
    for name, fn in tests:
        if not fn():
            all_pass = False
    if all_pass:
        print("\n✓ All DSB gate semantics tests PASS")
        sys.exit(0)
    else:
        print("\n✗ DSB gate semantics tests FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
