#!/usr/bin/env python3
"""
Test: Test Registry (Honesty Loop Priority 8 engine).

Per TEST_REGISTRY_ENGINE.md: append-only ledger of every test run
against a Blueprint claim. Per Law 28d: three test types cannot be
conflated (ANALYTICAL_ESTIMATE, NUMERICAL_SIMULATION,
PHYSICAL_VALIDATION). Per Law 4: FAIL is a valid result, not hidden.
Per EP-6: pass_criteria must be pre-stated. Per Law 27: each record
carries a typed epistemic_status block.

This test verifies:
1. The TestRegistry class works correctly (register, list, count,
   get, by_claim, by_type, failed, not_run, summary).
2. The registry is append-only (Law 7).
3. Test type / validation level consistency is enforced.
4. Records carry typed epistemic_status, not numerical confidence.
5. FAIL results are not hidden (Law 4).
6. The /api/v1/tests endpoint exposes the registry.
7. The scanner accepts the API response (no forbidden language).
"""
import sys
import pathlib
import tempfile
import json
import subprocess

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "web" / "backend"))

try:
    from fastapi.testclient import TestClient
    from main import app
    from adapters.test_registry import (
        TestRegistry, TEST_TYPES, RESULT_STATUS_VALUES,
        VALIDATION_LEVEL_TARGETS,
    )
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

import pytest

if not FASTAPI_AVAILABLE:
    pytest.skip("fastapi not installed — skipping test registry tests",
                allow_module_level=True)

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]


# --------------------------------------------------------------------------
# Unit tests for TestRegistry class
# --------------------------------------------------------------------------

class TestTestRegistryClass:
    """Verify the TestRegistry class works correctly."""

    def test_register_writes_record(self, tmp_path):
        """register() must write a record to the registry file."""
        reg_path = tmp_path / "tests.jsonl"
        reg = TestRegistry(registry_path=reg_path)
        t = reg.register(
            test_name="Pack energy density analytical estimate",
            test_type="ANALYTICAL_ESTIMATE",
            claim_id="CL-014",
            validation_level_target="L2",
            expected_value="160 Wh/kg",
            pass_criteria="Within +/- 5 Wh/kg of cell_density * overhead",
            evidence_id="EV-001",
            analytical_model="cell_density * pack_overhead = 172 * 0.93",
        )
        assert t["id"] == "TR-001"
        assert t["test_type"] == "ANALYTICAL_ESTIMATE"
        assert t["result"]["status"] == "NOT_RUN"
        assert reg_path.exists(), "Registry file was not created."

    def test_register_assigns_sequential_ids(self, tmp_path):
        """Multiple registrations must get sequential IDs."""
        reg = TestRegistry(registry_path=tmp_path / "t.jsonl")
        for i in range(3):
            t = reg.register(
                test_name=f"Test {i}",
                test_type="ANALYTICAL_ESTIMATE",
                claim_id=f"CL-{i}",
                validation_level_target="L2",
                expected_value="X",
                pass_criteria="X",
                evidence_id=f"EV-{i}",
            )
        assert t["id"] == "TR-003"

    def test_registry_is_append_only(self, tmp_path):
        """Per Law 7: the registry is append-only."""
        reg_path = tmp_path / "t.jsonl"
        reg = TestRegistry(registry_path=reg_path)
        reg.register(
            test_name="T1", test_type="ANALYTICAL_ESTIMATE",
            claim_id="CL-1", validation_level_target="L2",
            expected_value="X", pass_criteria="X", evidence_id="EV-1",
        )
        content_after_first = reg_path.read_text()
        reg.register(
            test_name="T2", test_type="ANALYTICAL_ESTIMATE",
            claim_id="CL-2", validation_level_target="L2",
            expected_value="Y", pass_criteria="Y", evidence_id="EV-2",
        )
        content_after_second = reg_path.read_text()
        assert "T1" in content_after_second
        assert content_after_first in content_after_second, (
            "Original content was modified — registry is not append-only (Law 7 violation)."
        )

    def test_count(self, tmp_path):
        """count() returns the number of records."""
        reg = TestRegistry(registry_path=tmp_path / "t.jsonl")
        assert reg.count() == 0
        for i in range(5):
            reg.register(
                test_name=f"T{i}", test_type="ANALYTICAL_ESTIMATE",
                claim_id=f"CL-{i}", validation_level_target="L2",
                expected_value="X", pass_criteria="X", evidence_id=f"EV-{i}",
            )
        assert reg.count() == 5

    def test_get_returns_record_by_id(self, tmp_path):
        """get() returns the record with the given ID."""
        reg = TestRegistry(registry_path=tmp_path / "t.jsonl")
        t = reg.register(
            test_name="T1", test_type="ANALYTICAL_ESTIMATE",
            claim_id="CL-1", validation_level_target="L2",
            expected_value="X", pass_criteria="X", evidence_id="EV-1",
        )
        fetched = reg.get(t["id"])
        assert fetched is not None
        assert fetched["test_name"] == "T1"
        assert reg.get("TR-999") is None

    def test_by_claim(self, tmp_path):
        """by_claim() returns all tests for a given claim."""
        reg = TestRegistry(registry_path=tmp_path / "t.jsonl")
        reg.register(
            test_name="T1", test_type="ANALYTICAL_ESTIMATE",
            claim_id="CL-1", validation_level_target="L2",
            expected_value="X", pass_criteria="X", evidence_id="EV-1",
        )
        reg.register(
            test_name="T2", test_type="NUMERICAL_SIMULATION",
            claim_id="CL-1", validation_level_target="L3",
            expected_value="Y", pass_criteria="Y", evidence_id="EV-2",
            numerical_solver="FEA (ANSYS)",
            numerical_model_file="model.fea",
        )
        reg.register(
            test_name="T3", test_type="ANALYTICAL_ESTIMATE",
            claim_id="CL-2", validation_level_target="L2",
            expected_value="Z", pass_criteria="Z", evidence_id="EV-3",
        )
        assert len(reg.by_claim("CL-1")) == 2
        assert len(reg.by_claim("CL-2")) == 1
        assert len(reg.by_claim("CL-999")) == 0

    def test_by_type(self, tmp_path):
        """by_type() returns all tests of a given type."""
        reg = TestRegistry(registry_path=tmp_path / "t.jsonl")
        reg.register(
            test_name="T1", test_type="ANALYTICAL_ESTIMATE",
            claim_id="CL-1", validation_level_target="L2",
            expected_value="X", pass_criteria="X", evidence_id="EV-1",
        )
        reg.register(
            test_name="T2", test_type="NUMERICAL_SIMULATION",
            claim_id="CL-2", validation_level_target="L3",
            expected_value="Y", pass_criteria="Y", evidence_id="EV-2",
            numerical_solver="FEA",
            numerical_model_file="m.fea",
        )
        assert len(reg.by_type("ANALYTICAL_ESTIMATE")) == 1
        assert len(reg.by_type("NUMERICAL_SIMULATION")) == 1
        assert len(reg.by_type("PHYSICAL_VALIDATION")) == 0

    def test_failed_returns_fail_results(self, tmp_path):
        """failed() returns all tests with result.status == FAIL.

        Per Law 4: failure is an asset. FAIL is not hidden.
        """
        reg = TestRegistry(registry_path=tmp_path / "t.jsonl")
        # A PASS test
        reg.register(
            test_name="T1", test_type="ANALYTICAL_ESTIMATE",
            claim_id="CL-1", validation_level_target="L2",
            expected_value="X", pass_criteria="X", evidence_id="EV-1",
            result_status="PASS", measured_value="X (measured)",
        )
        # A FAIL test
        reg.register(
            test_name="T2", test_type="PHYSICAL_VALIDATION",
            claim_id="CL-2", validation_level_target="L4",
            expected_value=">=80% in 18 min",
            pass_criteria=">=80% in 18 min AND temp < 55C",
            evidence_id="EV-2",
            physical_test_stand="bench rig B-001",
            physical_sample_size=3,
            result_status="FAIL",
            measured_value="78% in 18 min, temp peaked at 62C",
        )
        failed = reg.failed()
        assert len(failed) == 1
        assert failed[0]["test_name"] == "T2"

    def test_not_run_returns_planned_tests(self, tmp_path):
        """not_run() returns tests with result.status == NOT_RUN."""
        reg = TestRegistry(registry_path=tmp_path / "t.jsonl")
        reg.register(
            test_name="T1", test_type="ANALYTICAL_ESTIMATE",
            claim_id="CL-1", validation_level_target="L2",
            expected_value="X", pass_criteria="X", evidence_id="EV-1",
            # result_status defaults to NOT_RUN
        )
        reg.register(
            test_name="T2", test_type="ANALYTICAL_ESTIMATE",
            claim_id="CL-2", validation_level_target="L2",
            expected_value="Y", pass_criteria="Y", evidence_id="EV-2",
            result_status="PASS", measured_value="Y (measured)",
        )
        not_run = reg.not_run()
        assert len(not_run) == 1
        assert not_run[0]["test_name"] == "T1"

    def test_invalid_test_type_raises(self, tmp_path):
        """Invalid test_type must raise ValueError."""
        reg = TestRegistry(registry_path=tmp_path / "t.jsonl")
        with pytest.raises(ValueError, match="test_type"):
            reg.register(
                test_name="T1", test_type="INVALID_TYPE",
                claim_id="CL-1", validation_level_target="L2",
                expected_value="X", pass_criteria="X", evidence_id="EV-1",
            )

    def test_invalid_result_status_raises(self, tmp_path):
        """Invalid result_status must raise ValueError."""
        reg = TestRegistry(registry_path=tmp_path / "t.jsonl")
        with pytest.raises(ValueError, match="result_status"):
            reg.register(
                test_name="T1", test_type="ANALYTICAL_ESTIMATE",
                claim_id="CL-1", validation_level_target="L2",
                expected_value="X", pass_criteria="X", evidence_id="EV-1",
                result_status="INVALID_STATUS",
            )

    def test_analytical_estimate_must_be_l2(self, tmp_path):
        """ANALYTICAL_ESTIMATE must have validation_level_target=L2."""
        reg = TestRegistry(registry_path=tmp_path / "t.jsonl")
        with pytest.raises(ValueError, match="ANALYTICAL_ESTIMATE requires"):
            reg.register(
                test_name="T1", test_type="ANALYTICAL_ESTIMATE",
                claim_id="CL-1", validation_level_target="L3",
                expected_value="X", pass_criteria="X", evidence_id="EV-1",
            )

    def test_numerical_simulation_must_be_l3(self, tmp_path):
        """NUMERICAL_SIMULATION must have validation_level_target=L3."""
        reg = TestRegistry(registry_path=tmp_path / "t.jsonl")
        with pytest.raises(ValueError, match="NUMERICAL_SIMULATION requires"):
            reg.register(
                test_name="T1", test_type="NUMERICAL_SIMULATION",
                claim_id="CL-1", validation_level_target="L2",
                expected_value="X", pass_criteria="X", evidence_id="EV-1",
                numerical_solver="FEA",
                numerical_model_file="m.fea",
            )

    def test_physical_validation_must_be_l4_through_l9(self, tmp_path):
        """PHYSICAL_VALIDATION must have validation_level_target L4-L9."""
        reg = TestRegistry(registry_path=tmp_path / "t.jsonl")
        with pytest.raises(ValueError, match="PHYSICAL_VALIDATION requires"):
            reg.register(
                test_name="T1", test_type="PHYSICAL_VALIDATION",
                claim_id="CL-1", validation_level_target="L2",
                expected_value="X", pass_criteria="X", evidence_id="EV-1",
                physical_test_stand="bench",
                physical_sample_size=1,
            )

    def test_physical_validation_requires_test_stand_and_sample_size(self, tmp_path):
        """PHYSICAL_VALIDATION requires physical_test_stand and sample_size."""
        reg = TestRegistry(registry_path=tmp_path / "t.jsonl")
        with pytest.raises(ValueError, match="PHYSICAL_VALIDATION requires"):
            reg.register(
                test_name="T1", test_type="PHYSICAL_VALIDATION",
                claim_id="CL-1", validation_level_target="L4",
                expected_value="X", pass_criteria="X", evidence_id="EV-1",
                # missing physical_test_stand and physical_sample_size
            )

    def test_numerical_simulation_requires_solver_and_model_file(self, tmp_path):
        """NUMERICAL_SIMULATION requires numerical_solver and model_file."""
        reg = TestRegistry(registry_path=tmp_path / "t.jsonl")
        with pytest.raises(ValueError, match="NUMERICAL_SIMULATION requires"):
            reg.register(
                test_name="T1", test_type="NUMERICAL_SIMULATION",
                claim_id="CL-1", validation_level_target="L3",
                expected_value="X", pass_criteria="X", evidence_id="EV-1",
                # missing numerical_solver and numerical_model_file
            )

    def test_record_has_epistemic_status(self, tmp_path):
        """Per Law 27: each record carries a typed epistemic_status block."""
        reg = TestRegistry(registry_path=tmp_path / "t.jsonl")
        t = reg.register(
            test_name="T1", test_type="ANALYTICAL_ESTIMATE",
            claim_id="CL-1", validation_level_target="L2",
            expected_value="X", pass_criteria="X", evidence_id="EV-1",
        )
        assert "epistemic_status" in t, "Record missing epistemic_status (Law 27)."
        es = t["epistemic_status"]
        for field in ["validation_level", "evidence_strength",
                      "experimental_validation", "status"]:
            assert field in es, f"epistemic_status missing `{field}` (Law 29e)."
        # No numerical confidence field anywhere in the record.
        assert "confidence" not in t, (
            "Test record contains forbidden `confidence` field (Law 27)."
        )

    def test_epistemic_status_varies_by_test_type(self, tmp_path):
        """The epistemic_status block must reflect the test type honestly:
        ANALYTICAL_ESTIMATE -> L2, WEAK, ABSENT
        NUMERICAL_SIMULATION -> L3, MODERATE, ABSENT
        PHYSICAL_VALIDATION (L4) -> L4, STRONG, BENCH
        """
        reg = TestRegistry(registry_path=tmp_path / "t.jsonl")
        # Analytical
        t1 = reg.register(
            test_name="T1", test_type="ANALYTICAL_ESTIMATE",
            claim_id="CL-1", validation_level_target="L2",
            expected_value="X", pass_criteria="X", evidence_id="EV-1",
        )
        assert t1["epistemic_status"]["validation_level"] == "L2"
        assert t1["epistemic_status"]["evidence_strength"] == "WEAK"
        assert t1["epistemic_status"]["experimental_validation"] == "ABSENT"
        # Numerical
        t2 = reg.register(
            test_name="T2", test_type="NUMERICAL_SIMULATION",
            claim_id="CL-2", validation_level_target="L3",
            expected_value="Y", pass_criteria="Y", evidence_id="EV-2",
            numerical_solver="FEA",
            numerical_model_file="m.fea",
        )
        assert t2["epistemic_status"]["validation_level"] == "L3"
        assert t2["epistemic_status"]["evidence_strength"] == "MODERATE"
        assert t2["epistemic_status"]["experimental_validation"] == "ABSENT"
        # Physical (L4)
        t3 = reg.register(
            test_name="T3", test_type="PHYSICAL_VALIDATION",
            claim_id="CL-3", validation_level_target="L4",
            expected_value="Z", pass_criteria="Z", evidence_id="EV-3",
            physical_test_stand="bench",
            physical_sample_size=1,
        )
        assert t3["epistemic_status"]["validation_level"] == "L4"
        assert t3["epistemic_status"]["evidence_strength"] == "STRONG"
        assert t3["epistemic_status"]["experimental_validation"] == "BENCH"
        # Physical (L7+ — pilot deployment)
        t4 = reg.register(
            test_name="T4", test_type="PHYSICAL_VALIDATION",
            claim_id="CL-4", validation_level_target="L7",
            expected_value="W", pass_criteria="W", evidence_id="EV-4",
            physical_test_stand="pilot fleet",
            physical_sample_size=10,
        )
        assert t4["epistemic_status"]["evidence_strength"] == "VERY_STRONG"
        assert t4["epistemic_status"]["experimental_validation"] == "PILOT"

    def test_fail_result_sets_record_status_rejected(self, tmp_path):
        """A FAIL result must set the record's overall status to REJECTED."""
        reg = TestRegistry(registry_path=tmp_path / "t.jsonl")
        t = reg.register(
            test_name="T1", test_type="PHYSICAL_VALIDATION",
            claim_id="CL-1", validation_level_target="L4",
            expected_value=">=80%", pass_criteria=">=80%",
            evidence_id="EV-1",
            physical_test_stand="bench",
            physical_sample_size=1,
            result_status="FAIL",
            measured_value="78%",
        )
        assert t["result"]["status"] == "FAIL"
        assert t["status"] == "REJECTED"

    def test_not_run_sets_record_status_blocked(self, tmp_path):
        """A NOT_RUN result must set the record's overall status to BLOCKED
        (planned but not yet executed)."""
        reg = TestRegistry(registry_path=tmp_path / "t.jsonl")
        t = reg.register(
            test_name="T1", test_type="ANALYTICAL_ESTIMATE",
            claim_id="CL-1", validation_level_target="L2",
            expected_value="X", pass_criteria="X", evidence_id="EV-1",
            # result_status defaults to NOT_RUN
        )
        assert t["result"]["status"] == "NOT_RUN"
        assert t["status"] == "BLOCKED"

    def test_immutable_flag_is_true(self, tmp_path):
        """Per spec: every record has immutable: true."""
        reg = TestRegistry(registry_path=tmp_path / "t.jsonl")
        t = reg.register(
            test_name="T1", test_type="ANALYTICAL_ESTIMATE",
            claim_id="CL-1", validation_level_target="L2",
            expected_value="X", pass_criteria="X", evidence_id="EV-1",
        )
        assert t["immutable"] is True

    def test_pass_criteria_is_pre_stated(self, tmp_path):
        """Per EP-6: pass_criteria must be supplied at registration
        (before the test runs), not alongside the results."""
        reg = TestRegistry(registry_path=tmp_path / "t.jsonl")
        t = reg.register(
            test_name="T1", test_type="ANALYTICAL_ESTIMATE",
            claim_id="CL-1", validation_level_target="L2",
            expected_value="160 Wh/kg",
            pass_criteria="Within +/- 5 Wh/kg of cell_density * overhead",
            evidence_id="EV-1",
        )
        assert t["result"]["pass_criteria"] == "Within +/- 5 Wh/kg of cell_density * overhead"
        # Even NOT_RUN tests have pass_criteria pre-stated
        assert t["result"]["status"] == "NOT_RUN"
        assert t["result"]["pass_criteria"]  # non-empty


# --------------------------------------------------------------------------
# API endpoint tests
# --------------------------------------------------------------------------

class TestTestApiEndpoint:
    """Verify the /api/v1/tests endpoint works."""

    def test_endpoint_responds(self):
        """GET /api/v1/tests must return 200."""
        client = TestClient(app)
        r = client.get("/api/v1/tests")
        assert r.status_code == 200

    def test_endpoint_returns_required_fields(self):
        """The response must include count, summary, failed_count, etc."""
        client = TestClient(app)
        r = client.get("/api/v1/tests")
        body = r.json()
        for field in ["tests", "count", "failed_count", "not_run_count",
                      "by_type", "by_result", "summary", "registry_path"]:
            assert field in body, f"Response missing `{field}`."

    def test_endpoint_returns_list_of_tests(self):
        """The `tests` field must be a list."""
        client = TestClient(app)
        body = client.get("/api/v1/tests").json()
        assert isinstance(body["tests"], list)

    def test_endpoint_summary_is_consistent(self):
        """The summary fields must be consistent with the tests list."""
        client = TestClient(app)
        body = client.get("/api/v1/tests").json()
        assert body["count"] == len(body["tests"])
        assert body["count"] == body["summary"]["total"]
        assert body["failed_count"] == body["summary"]["failed_count"]

    def test_endpoint_has_verification_stamp(self):
        """The response must carry the verification stamp."""
        client = TestClient(app)
        body = client.get("/api/v1/tests").json()
        assert "verification" in body
        assert body["verification"]["level"] in {"integrated", "implemented"}


# --------------------------------------------------------------------------
# Honesty Loop scanner acceptance
# --------------------------------------------------------------------------

class TestScannerAcceptsTestApi:
    """Verify the Law 27 scanner accepts the /api/v1/tests response."""

    def test_tests_endpoint_passes_scanner(self, tmp_path):
        """The /api/v1/tests response must pass the Law 27 scanner."""
        client = TestClient(app)
        body = client.get("/api/v1/tests").json()
        fixture = tmp_path / "tests_response.json"
        fixture.write_text(json.dumps(body, indent=2))

        result = subprocess.run(
            ["python3", str(REPO_ROOT / "scripts" / "enforce_law27.py"),
             str(fixture)],
            capture_output=True, text=True, cwd=str(REPO_ROOT)
        )
        assert result.returncode == 0, (
            f"Law 27 scanner REJECTED the /api/v1/tests response:\n"
            f"{result.stdout}\n"
            f"The API response contains forbidden language (Law 27/28/29)."
        )
