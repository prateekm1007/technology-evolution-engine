#!/usr/bin/env python3
"""
Test: F-066 enforcement — mechanism label must be locked at T1.

Per F-066 (cycle 91): "Mechanism label reframing changes non-triviality
verdict. Must be locked at T1."

Per P70: "A principle written down after finding a bug does not retroactively
protect code written to fix a different ticket in the same file, even minutes
later. Principles need grep-able CI checks, not just paragraphs."

This test file mechanically enforces F-066 by checking that:
  1. Every non-triviality report in predictions.jsonl uses the same
     shared_mechanism label as the original blind_test_hypothesis or
     blind_test_result entry for that experiment_id.
  2. If the labels differ, the test fails — flagging post-hoc reframing.

The check is conservative: it only flags CHANGES to the mechanism label
between the original entry and any subsequent non-triviality report.
Adding more detail to the label (e.g., adding a parenthetical) is allowed
if the core label is unchanged; wholesale replacement is not.

Per P27: read the assertion, not the test name.
Per P28: test with 3+ inputs (exact match, added detail, wholesale change).
"""
import json
import pathlib
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PREDICTIONS = ROOT / "data" / "ledger" / "predictions.jsonl"


def load_predictions_by_experiment() -> dict:
    """Load all predictions.jsonl entries, grouped by experiment_id."""
    if not PREDICTIONS.exists():
        return {}
    entries_by_exp = {}
    with PREDICTIONS.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            exp_id = entry.get("experiment_id") or entry.get("test_id")
            if exp_id:
                entries_by_exp.setdefault(exp_id, []).append(entry)
    return entries_by_exp


def get_original_mechanism(entries: list) -> str:
    """Find the original mechanism label from the first entry that has one."""
    for entry in entries:
        # blind_test_hypothesis_v2 has "candidate_bridge"
        if entry.get("type") == "blind_test_hypothesis_v2":
            return entry.get("candidate_bridge", "").lower()
        # blind_test_result has "cross_details" but not the mechanism directly
        # The first entry with the mechanism is the hypothesis
    return ""


def get_nontriviality_mechanisms(entries: list) -> list:
    """Find all non-triviality check entries and their mechanism labels."""
    results = []
    for entry in entries:
        if entry.get("type") in ("nontriviality_check",):
            results.append({
                "timestamp": entry.get("timestamp", ""),
                "mechanism": entry.get("shared_mechanism", "").lower(),
                "verdict": entry.get("overall_verdict", ""),
            })
    return results


def mechanisms_consistent(original: str, reported: str) -> bool:
    """Check if a reported mechanism is consistent with the original.

    Conservative: the reported mechanism must CONTAIN the original's core
    term, or the original must contain the reported's core term. Wholesale
    replacement (neither contains the other) is a violation.

    Examples:
      - original="surface_wettability_control", reported="surface_wettability_control (contact angle)"
        -> CONSISTENT (reported contains original)
      - original="surface_wettability_control", reported="hierarchical_micro_nano_roughness_wettability"
        -> INCONSISTENT (neither contains the other — wholesale replacement)
      - original="selective_permeability", reported="selective permeability via pore size control"
        -> CONSISTENT (reported contains original)
    """
    if not original or not reported:
        return True  # can't check if either is missing

    orig = original.lower().replace(" ", "_")
    rep = reported.lower().replace(" ", "_")

    # Extract core terms (first 2 words, or the full thing if short)
    orig_core = "_".join(orig.split("_")[:3])
    rep_core = "_".join(rep.split("_")[:3])

    # Check if one contains the other's core
    if orig_core in rep or rep_core in orig:
        return True
    if orig in rep or rep in orig:
        return True

    return False


class TestF066MechanismLabelLocking:
    """Mechanically enforce F-066: mechanism labels locked at T1."""

    def test_predictions_file_exists(self):
        """The predictions.jsonl file must exist."""
        assert PREDICTIONS.exists(), "data/ledger/predictions.jsonl does not exist"

    def test_mechanisms_consistent_function_exact_match(self):
        """Per P28: exact case — identical labels are consistent."""
        assert mechanisms_consistent("selective_permeability", "selective_permeability") is True

    def test_mechanisms_consistent_function_added_detail(self):
        """Per P28: variation — adding detail (parenthetical) is consistent."""
        assert mechanisms_consistent(
            "surface_wettability_control",
            "surface_wettability_control (contact angle + pore structure)"
        ) is True

    def test_mechanisms_consistent_function_wholesale_replacement(self):
        """Per P28: edge case — wholesale replacement is a violation."""
        assert mechanisms_consistent(
            "surface_wettability_control",
            "hierarchical_micro_nano_roughness_wettability"
        ) is False

    def test_mechanisms_consistent_function_space_vs_underscore(self):
        """Per P28: edge case — spaces and underscores are equivalent."""
        assert mechanisms_consistent(
            "selective permeability",
            "selective_permeability via pore size control"
        ) is True

    def test_no_nontriviality_report_reframes_mechanism_label(self):
        """F-066 enforcement: no non-triviality report may use a different
        mechanism label than the original pre-registration.

        This test scans all experiments in predictions.jsonl and checks that
        every non-triviality_check entry uses a mechanism label consistent
        with the original blind_test_hypothesis entry for that experiment.
        """
        entries_by_exp = load_predictions_by_experiment()
        violations = []

        for exp_id, entries in entries_by_exp.items():
            original = get_original_mechanism(entries)
            if not original:
                continue  # no hypothesis entry to compare against

            nt_reports = get_nontriviality_mechanisms(entries)
            for report in nt_reports:
                if not mechanisms_consistent(original, report["mechanism"]):
                    violations.append({
                        "experiment_id": exp_id,
                        "original_mechanism": original,
                        "reported_mechanism": report["mechanism"],
                        "timestamp": report["timestamp"],
                        "verdict": report["verdict"],
                    })

        assert not violations, (
            f"F-066 VIOLATION: {len(violations)} non-triviality report(s) use a "
            f"different mechanism label than the original pre-registration. "
            f"This is post-hoc label reframing to flip verdicts (same pattern "
            f"as F-063). Violations: {json.dumps(violations, indent=2)}"
        )

    def test_exp_blind_023_label_history_is_honest(self):
        """EXP-BLIND-023 specifically: the cycle-90 reframing should be
        flagged, and the cycle-91 revert should be recorded.

        This test verifies that the F-066 violation for EXP-BLIND-023 is
        documented in the ledger (as a reclassification entry), not hidden.
        """
        entries_by_exp = load_predictions_by_experiment()
        entries = entries_by_exp.get("EXP-BLIND-023", [])

        # There should be a reclassification entry documenting the F-066 fix
        reclassifications = [e for e in entries if e.get("type") == "blind_test_reclassification"]
        assert len(reclassifications) >= 1, (
            "EXP-BLIND-023 should have at least 1 reclassification entry "
            "documenting the F-066 label-reframing fix."
        )

        # The reclassification should mention F-066 or label reframing
        reclass_text = json.dumps(reclassifications).lower()
        assert "f-066" in reclass_text or "refram" in reclass_text or "label" in reclass_text, (
            "EXP-BLIND-023 reclassification should document the F-066 "
            "label-reframing issue."
        )
