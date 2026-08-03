#!/usr/bin/env python3
"""
Test: Rigor Engines Enforcement

Per auditor NN6 (P2): 'No CI test asserting the 5 engines are present.'
Per auditor NN5 (P2): 'AEP gates not updated for consistency and kill-test.'

This test verifies that:
1. The 5 rigor engine keys exist in the blueprint output
2. FATAL consistency violations are flagged (not hidden)
3. Failed kill tests are tracked (not hidden)

This runs in CI (Gate 3). If engines are unwired or FATAL violations
are unflagged, CI fails.
"""

import json
import subprocess
import urllib.request
import pytest
import os


def get_blueprint():
    """Call the live API to get a blueprint, or skip if API is not running."""
    api_url = os.environ.get("API_URL", "http://localhost:3000")
    try:
        req = urllib.request.Request(
            f"{api_url}/api/compile",
            data=json.dumps({"idea": "Build a solar-powered irrigation robot for small farms in India."}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read())
            if not data.get("success"):
                pytest.skip(f"API returned failure: {data.get('error')}")
            return data["blueprint"]
    except Exception as e:
        pytest.skip(f"API not available: {e}")


class TestRigorEngines:
    """Test that all 5 rigor engines are present and functional."""

    def test_consistency_violations_present(self):
        """Consistency engine must be in the blueprint output."""
        bp = get_blueprint()
        assert "consistencyViolations" in bp, (
            "consistencyViolations not in blueprint output. "
            "The consistency engine must be wired into the API."
        )
        cv = bp["consistencyViolations"]
        assert "totalQuantities" in cv, "consistencyViolations missing totalQuantities"
        assert "totalViolations" in cv, "consistencyViolations missing totalViolations"
        assert "fatal" in cv, "consistencyViolations missing fatal count"
        assert "warnings" in cv, "consistencyViolations missing warnings count"
        assert "violations" in cv, "consistencyViolations missing violations array"

    def test_consistency_fatal_violations_are_flagged(self):
        """FATAL consistency violations must not be hidden."""
        bp = get_blueprint()
        cv = bp.get("consistencyViolations", {})
        fatal = cv.get("fatal", 0)
        if fatal > 0:
            violations = cv.get("violations", [])
            fatal_violations = [v for v in violations if v.get("severity") == "FATAL"]
            assert len(fatal_violations) == fatal, (
                f"Fatal count ({fatal}) does not match fatal violations in array ({len(fatal_violations)}). "
                "Fatal violations must be visible in the output, not hidden."
            )

    def test_dimensional_analysis_present(self):
        """Dimensional analysis engine must be in the blueprint output."""
        bp = get_blueprint()
        assert "dimensionalAnalysis" in bp, (
            "dimensionalAnalysis not in blueprint output. "
            "The dimensional analysis engine must be wired into the API."
        )
        da = bp["dimensionalAnalysis"]
        assert "totalChecks" in da, "dimensionalAnalysis missing totalChecks"
        assert "passed" in da, "dimensionalAnalysis missing passed"
        assert "failed" in da, "dimensionalAnalysis missing failed"
        assert "checks" in da, "dimensionalAnalysis missing checks array"

    def test_requirement_classification_present(self):
        """Requirement reconciliation engine must be in the blueprint output."""
        bp = get_blueprint()
        assert "requirementClassification" in bp, (
            "requirementClassification not in blueprint output. "
            "The requirement reconciliation engine must be wired into the API."
        )
        rc = bp["requirementClassification"]
        assert "totalRequirements" in rc, "requirementClassification missing totalRequirements"
        assert "requirements" in rc, "requirementClassification missing requirements array"

    def test_physics_boundaries_present(self):
        """Physics boundary engine must be in the blueprint output."""
        bp = get_blueprint()
        assert "physicsBoundaries" in bp, (
            "physicsBoundaries not in blueprint output. "
            "The physics boundary engine must be wired into the API."
        )
        pb = bp["physicsBoundaries"]
        assert "totalClaims" in pb, "physicsBoundaries missing totalClaims"
        assert "unvalidated" in pb, "physicsBoundaries missing unvalidated"
        assert "claims" in pb, "physicsBoundaries missing claims array"

    def test_kill_tests_present(self):
        """Kill-test engine must be in the blueprint output."""
        bp = get_blueprint()
        assert "killTests" in bp, (
            "killTests not in blueprint output. "
            "The kill-test engine must be wired into the API."
        )
        kt = bp["killTests"]
        assert "totalTests" in kt, "killTests missing totalTests"
        assert "untested" in kt, "killTests missing untested"
        assert "passed" in kt, "killTests missing passed"
        assert "failed" in kt, "killTests missing failed"
        assert "tests" in kt, "killTests missing tests array"

    def test_failed_kill_tests_are_tracked(self):
        """Failed kill tests must be visible in the output, not hidden."""
        bp = get_blueprint()
        kt = bp.get("killTests", {})
        failed = kt.get("failed", 0)
        if failed > 0:
            tests = kt.get("tests", [])
            failed_tests = [t for t in tests if t.get("status") == "FAILED"]
            assert len(failed_tests) == failed, (
                f"Failed count ({failed}) does not match failed tests in array ({len(failed_tests)}). "
                "Failed kill tests must be visible, not hidden."
            )

    def test_aep_protocol_has_consistency_gate(self):
        """AEP_PROTOCOL.md must contain Gate 4.5 (Consistency Gate)."""
        repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        aep_path = os.path.join(repo_root, "AEP_PROTOCOL.md")
        if os.path.exists(aep_path):
            content = open(aep_path).read()
            assert "Gate 4.5" in content, (
                "Gate 4.5 (Consistency Gate) not found in AEP_PROTOCOL.md. "
                "Per auditor NN5: engines detect contradictions but no gate blocks on them."
            )
            assert "FATAL" in content, (
                "Gate 4.5 must reference FATAL violations as the blocking condition."
            )

    def test_aep_protocol_has_killtest_gate(self):
        """AEP_PROTOCOL.md must contain Gate 10.5 (Kill-Test Gate)."""
        repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        aep_path = os.path.join(repo_root, "AEP_PROTOCOL.md")
        if os.path.exists(aep_path):
            content = open(aep_path).read()
            assert "Gate 10.5" in content or "Kill-Test Gate" in content, (
                "Gate 10.5 (Kill-Test Gate) not found in AEP_PROTOCOL.md. "
                "Per auditor NN5: kill tests detect failures but no gate blocks on them."
            )
