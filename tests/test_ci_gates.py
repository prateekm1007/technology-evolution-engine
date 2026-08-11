"""
Test the CI gates (cycle 61).

Per CEO directive: "The CI gates that would mechanically enforce the
new principles do not exist yet. See that they do."

Per P70: "Principles need grep-able CI checks, not just paragraphs."

This test verifies each CI gate function exists and returns the expected
(passed, details) tuple structure.
"""
import sys
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


class TestCIGatesExist:
    """Verify all CI gate functions exist and are callable."""

    def test_ci_gates_module_imports(self):
        """scripts/ci_gates.py must be importable."""
        import scripts.ci_gates
        assert hasattr(scripts.ci_gates, "GATES")

    def test_all_7_gates_exist(self):
        """All CI gates must be defined (8 as of cycle 68: +PDF gate)."""
        from scripts.ci_gates import GATES
        expected_gates = {"P27", "P77", "P1", "FA2", "GOV", "P70", "TAX", "PDF"}
        assert set(GATES.keys()) == expected_gates, (
            f"expected {expected_gates}, got {set(GATES.keys())}"
        )

    def test_each_gate_is_callable(self):
        """Each gate must be a callable function."""
        from scripts.ci_gates import GATES
        for name, fn in GATES.items():
            assert callable(fn), f"gate {name} is not callable"


class TestCIGatesReturnCorrectStructure:
    """Each gate must return (passed: bool, details: str)."""

    def test_p27_gate_returns_tuple(self):
        from scripts.ci_gates import gate_p27_no_assert_true
        result = gate_p27_no_assert_true()
        assert isinstance(result, tuple), "P27 gate must return a tuple"
        assert len(result) == 2, "P27 gate must return (passed, details)"
        assert isinstance(result[0], bool), "P27 gate first element must be bool"
        assert isinstance(result[1], str), "P27 gate second element must be str"

    def test_p70_gate_returns_tuple(self):
        from scripts.ci_gates import gate_p70_principles_grepable
        result = gate_p70_principles_grepable()
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], bool)
        assert isinstance(result[1], str)

    def test_gov_gate_returns_tuple(self):
        from scripts.ci_gates import gate_gov_read_receipt
        result = gate_gov_read_receipt()
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], bool)
        assert isinstance(result[1], str)


class TestCIGatesPass:
    """Verify the gates pass on the current repository state."""

    def test_p70_principles_are_grepable(self):
        """P70: required principles must be in ANTI_ENTROPY.md (cycle 64: reduced set)."""
        from scripts.ci_gates import gate_p70_principles_grepable
        passed, details = gate_p70_principles_grepable()
        assert passed, f"P70 gate failed: {details}"

    def test_p27_no_assert_true_theater(self):
        """P27: no tests that assert True (theater)."""
        from scripts.ci_gates import gate_p27_no_assert_true
        passed, details = gate_p27_no_assert_true()
        assert passed, f"P27 gate failed: {details}"

    def test_tax_consistency_holds(self):
        """TAX: no tier=VERIFIED with mechanism_status=ASSERTED."""
        from scripts.ci_gates import gate_tax_consistency
        passed, details = gate_tax_consistency()
        assert passed, f"TAX gate failed: {details}"


class TestCIGatesRunner:
    """Verify the main runner works."""

    def test_run_all_gates_returns_exit_code(self):
        """run_all_gates must return 0 (all pass) or 1 (some fail)."""
        from scripts.ci_gates import run_all_gates
        exit_code = run_all_gates()
        assert exit_code in (0, 1), f"exit code must be 0 or 1, got {exit_code}"

    def test_list_gates_works(self):
        """--list flag must show all gates."""
        from scripts.ci_gates import GATES
        assert len(GATES) == 8
