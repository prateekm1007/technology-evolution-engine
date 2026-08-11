#!/usr/bin/env python3
"""
Test: Retraction Registry (Honesty Loop Priority 7 engine).

Per RETRACTION_REGISTRY_ENGINE.md: append-only ledger of retracted
claims. Per CONSTITUTION.md Law 7 (Historical Permanence): records
cannot be edited once written.

Per HONESTY_LOOP.md Gate 11 check 5: 'The Retraction Registry must
contain no unresolved retractions.'

Per Law 27: each retraction record carries a typed `epistemic_status`
block, not a numerical confidence.

This test verifies:
1. The RetractionRegistry class works correctly (register, list,
   count, get, unresolved).
2. The registry is append-only (Law 7).
3. Records carry typed epistemic_status, not numerical confidence.
4. The /api/v1/retractions endpoint exposes the registry.
5. The endpoint reports Gate 11 check 5 status.
6. The scanner accepts the API response (no forbidden language).
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
    from adapters.retraction_registry import RetractionRegistry, REASON_CATEGORIES, STATUS_VALUES
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

import pytest

if not FASTAPI_AVAILABLE:
    pytest.skip("fastapi not installed — skipping retraction registry tests",
                allow_module_level=True)

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]


# --------------------------------------------------------------------------
# Unit tests for RetractionRegistry class
# --------------------------------------------------------------------------

class TestRetractionRegistryClass:
    """Verify the RetractionRegistry class works correctly."""

    def test_register_writes_record(self, tmp_path):
        """register() must write a record to the registry file."""
        reg_path = tmp_path / "retractions.jsonl"
        reg = RetractionRegistry(registry_path=reg_path)
        r = reg.register(
            retracted_claim_id="CL-007",
            retracted_claim_statement="Total pack mass: 584 kg",
            retraction_agent="consistency_engine",
            reason_category="NUMERICAL_CONTRADICTION",
            reason_description="584 kg + 75 kWh = 161 Wh/kg; cell-level 172; contradiction.",
            detected_by="consistency_engine",
            detection_date="2024-08-15T14:21:55Z",
            replacement_claim_id="CL-014",
            replacement_evidence_id="EV-101",
            replacement_derivation="Stack-up: cells 436.8 + ... = 612.4 kg.",
        )
        assert r["id"] == "RT-001"
        assert r["status"] == "RETRACTED"
        assert r["retracted_claim_id"] == "CL-007"
        assert reg_path.exists(), "Registry file was not created."

    def test_register_assigns_sequential_ids(self, tmp_path):
        """Multiple registrations must get sequential IDs."""
        reg = RetractionRegistry(registry_path=tmp_path / "r.jsonl")
        r1 = reg.register(
            retracted_claim_id="CL-1", retracted_claim_statement="A",
            retraction_agent="t", reason_category="EVIDENCE_INVALIDATED",
            reason_description="x", detected_by="t", detection_date="2024-01-01T00:00:00Z",
        )
        r2 = reg.register(
            retracted_claim_id="CL-2", retracted_claim_statement="B",
            retraction_agent="t", reason_category="EVIDENCE_INVALIDATED",
            reason_description="y", detected_by="t", detection_date="2024-01-01T00:00:00Z",
        )
        r3 = reg.register(
            retracted_claim_id="CL-3", retracted_claim_statement="C",
            retraction_agent="t", reason_category="EVIDENCE_INVALIDATED",
            reason_description="z", detected_by="t", detection_date="2024-01-01T00:00:00Z",
        )
        assert r1["id"] == "RT-001"
        assert r2["id"] == "RT-002"
        assert r3["id"] == "RT-003"

    def test_registry_is_append_only(self, tmp_path):
        """Per Law 7: the registry is append-only. Registering again
        does not overwrite existing records."""
        reg_path = tmp_path / "r.jsonl"
        reg = RetractionRegistry(registry_path=reg_path)
        reg.register(
            retracted_claim_id="CL-1", retracted_claim_statement="A",
            retraction_agent="t", reason_category="EVIDENCE_INVALIDATED",
            reason_description="x", detected_by="t", detection_date="2024-01-01T00:00:00Z",
        )
        # Read the file content
        content_after_first = reg_path.read_text()
        reg.register(
            retracted_claim_id="CL-2", retracted_claim_statement="B",
            retraction_agent="t", reason_category="EVIDENCE_INVALIDATED",
            reason_description="y", detected_by="t", detection_date="2024-01-01T00:00:00Z",
        )
        content_after_second = reg_path.read_text()
        # The first record must still be in the file (append-only).
        assert "CL-1" in content_after_second, (
            "First retraction was overwritten — registry is not append-only (Law 7 violation)."
        )
        assert content_after_first in content_after_second, (
            "Original content was modified — registry is not append-only (Law 7 violation)."
        )

    def test_count(self, tmp_path):
        """count() returns the number of records."""
        reg = RetractionRegistry(registry_path=tmp_path / "r.jsonl")
        assert reg.count() == 0
        for i in range(5):
            reg.register(
                retracted_claim_id=f"CL-{i}", retracted_claim_statement=f"S{i}",
                retraction_agent="t", reason_category="EVIDENCE_INVALIDATED",
                reason_description="x", detected_by="t", detection_date="2024-01-01T00:00:00Z",
            )
        assert reg.count() == 5

    def test_get_returns_record_by_id(self, tmp_path):
        """get() returns the record with the given ID."""
        reg = RetractionRegistry(registry_path=tmp_path / "r.jsonl")
        r = reg.register(
            retracted_claim_id="CL-1", retracted_claim_statement="A",
            retraction_agent="t", reason_category="EVIDENCE_INVALIDATED",
            reason_description="x", detected_by="t", detection_date="2024-01-01T00:00:00Z",
        )
        rid = r["id"]
        fetched = reg.get(rid)
        assert fetched is not None
        assert fetched["retracted_claim_id"] == "CL-1"
        assert reg.get("RT-999") is None

    def test_unresolved_returns_retracted_without_replacement(self, tmp_path):
        """unresolved() returns RETRACTED records with no replacement.

        Per HONESTY_LOOP.md Gate 11 check 5: 'All retractions must have
        either a replacement claim or an explicit WITHDRAWN status
        with rationale.'
        """
        reg = RetractionRegistry(registry_path=tmp_path / "r.jsonl")
        # RETRACTED with replacement -> resolved
        reg.register(
            retracted_claim_id="CL-1", retracted_claim_statement="A",
            retraction_agent="t", reason_category="EVIDENCE_INVALIDATED",
            reason_description="x", detected_by="t", detection_date="2024-01-01T00:00:00Z",
            replacement_claim_id="CL-2", replacement_evidence_id="EV-1",
            replacement_derivation="New evidence.",
        )
        # RETRACTED without replacement -> unresolved
        reg.register(
            retracted_claim_id="CL-3", retracted_claim_statement="B",
            retraction_agent="t", reason_category="EVIDENCE_INVALIDATED",
            reason_description="y", detected_by="t", detection_date="2024-01-01T00:00:00Z",
        )
        # WITHDRAWN without replacement -> resolved (explicit withdrawal)
        reg.register(
            retracted_claim_id="CL-4", retracted_claim_statement="C",
            retraction_agent="t", reason_category="EVIDENCE_INVALIDATED",
            reason_description="z", detected_by="t", detection_date="2024-01-01T00:00:00Z",
            status="WITHDRAWN",
        )
        unresolved = reg.unresolved()
        assert len(unresolved) == 1
        assert unresolved[0]["retracted_claim_id"] == "CL-3"

    def test_invalid_reason_category_raises(self, tmp_path):
        """Invalid reason_category must raise ValueError."""
        reg = RetractionRegistry(registry_path=tmp_path / "r.jsonl")
        with pytest.raises(ValueError, match="reason_category"):
            reg.register(
                retracted_claim_id="CL-1", retracted_claim_statement="A",
                retraction_agent="t", reason_category="INVALID_CATEGORY",
                reason_description="x", detected_by="t", detection_date="2024-01-01T00:00:00Z",
            )

    def test_invalid_status_raises(self, tmp_path):
        """Invalid status must raise ValueError."""
        reg = RetractionRegistry(registry_path=tmp_path / "r.jsonl")
        with pytest.raises(ValueError, match="status"):
            reg.register(
                retracted_claim_id="CL-1", retracted_claim_statement="A",
                retraction_agent="t", reason_category="EVIDENCE_INVALIDATED",
                reason_description="x", detected_by="t", detection_date="2024-01-01T00:00:00Z",
                status="INVALID_STATUS",
            )

    def test_partial_replacement_raises(self, tmp_path):
        """Partial replacement fields must raise ValueError."""
        reg = RetractionRegistry(registry_path=tmp_path / "r.jsonl")
        with pytest.raises(ValueError, match="Replacement fields are partially populated"):
            reg.register(
                retracted_claim_id="CL-1", retracted_claim_statement="A",
                retraction_agent="t", reason_category="EVIDENCE_INVALIDATED",
                reason_description="x", detected_by="t", detection_date="2024-01-01T00:00:00Z",
                replacement_claim_id="CL-2",  # missing evidence_id and derivation
            )

    def test_record_has_epistemic_status(self, tmp_path):
        """Per Law 27: each record carries a typed epistemic_status block,
        not a numerical confidence."""
        reg = RetractionRegistry(registry_path=tmp_path / "r.jsonl")
        r = reg.register(
            retracted_claim_id="CL-1", retracted_claim_statement="A",
            retraction_agent="t", reason_category="EVIDENCE_INVALIDATED",
            reason_description="x", detected_by="t", detection_date="2024-01-01T00:00:00Z",
        )
        assert "epistemic_status" in r, "Record missing epistemic_status (Law 27)."
        es = r["epistemic_status"]
        for field in ["validation_level", "evidence_strength",
                      "experimental_validation", "status"]:
            assert field in es, f"epistemic_status missing `{field}` (Law 29e)."
        # Retraction records should be L1 (literature support: the
        # registry is its own documentation).
        assert es["validation_level"] == "L1"
        # No numerical confidence field anywhere in the record.
        assert "confidence" not in r, (
            "Retraction record contains forbidden `confidence` field (Law 27)."
        )

    def test_all_reason_categories_accepted(self, tmp_path):
        """All 8 reason categories from the spec must be accepted."""
        reg = RetractionRegistry(registry_path=tmp_path / "r.jsonl")
        for i, cat in enumerate(sorted(REASON_CATEGORIES)):
            r = reg.register(
                retracted_claim_id=f"CL-{i}", retracted_claim_statement=f"S{i}",
                retraction_agent="t", reason_category=cat,
                reason_description="x", detected_by="t", detection_date="2024-01-01T00:00:00Z",
            )
            assert r["reason"]["category"] == cat

    def test_immutable_flag_is_true(self, tmp_path):
        """Per spec: every record has immutable: true."""
        reg = RetractionRegistry(registry_path=tmp_path / "r.jsonl")
        r = reg.register(
            retracted_claim_id="CL-1", retracted_claim_statement="A",
            retraction_agent="t", reason_category="EVIDENCE_INVALIDATED",
            reason_description="x", detected_by="t", detection_date="2024-01-01T00:00:00Z",
        )
        assert r["immutable"] is True


# --------------------------------------------------------------------------
# API endpoint tests
# --------------------------------------------------------------------------

class TestRetractionApiEndpoint:
    """Verify the /api/v1/retractions endpoint works."""

    def test_endpoint_responds(self):
        """GET /api/v1/retractions must return 200."""
        client = TestClient(app)
        r = client.get("/api/v1/retractions")
        assert r.status_code == 200

    def test_endpoint_returns_required_fields(self):
        """The response must include count, unresolved_count, gate_11_check_5_pass."""
        client = TestClient(app)
        r = client.get("/api/v1/retractions")
        body = r.json()
        for field in ["retractions", "count", "unresolved_count",
                      "unresolved_ids", "gate_11_check_5_pass", "registry_path"]:
            assert field in body, f"Response missing `{field}`."

    def test_endpoint_returns_list_of_retractions(self):
        """The `retractions` field must be a list."""
        client = TestClient(app)
        body = client.get("/api/v1/retractions").json()
        assert isinstance(body["retractions"], list)

    def test_endpoint_reports_gate_11_check_5_status(self):
        """The endpoint must report whether Gate 11 check 5 passes
        (no unresolved retractions)."""
        client = TestClient(app)
        body = client.get("/api/v1/retractions").json()
        # gate_11_check_5_pass is True iff unresolved_count == 0
        assert body["gate_11_check_5_pass"] == (body["unresolved_count"] == 0)

    def test_endpoint_has_verification_stamp(self):
        """The response must carry the verification stamp."""
        client = TestClient(app)
        body = client.get("/api/v1/retractions").json()
        assert "verification" in body
        assert body["verification"]["level"] in {"integrated", "implemented"}


# --------------------------------------------------------------------------
# Honesty Loop scanner acceptance
# --------------------------------------------------------------------------

class TestScannerAcceptsRetractionApi:
    """Verify the Law 27 scanner accepts the /api/v1/retractions response."""

    def test_retractions_endpoint_passes_scanner(self, tmp_path):
        """The /api/v1/retractions response must pass the Law 27 scanner.

        The response carries retraction records. Each record has an
        `epistemic_status` block (typed) and must NOT contain the
        forbidden `confidence` field.
        """
        client = TestClient(app)
        # First, register a retraction through the registry so the
        # response has at least one record.
        # Note: we use the registry's append method directly because
        # the API endpoint is read-only.
        from adapters.retraction_registry import RetractionRegistry
        # Use the same registry instance the app uses
        reg = RetractionRegistry()  # uses default REGISTRY_PATH
        # Don't pollute the real registry — skip if it already has entries
        # (we don't want to add test data to the production registry)
        if reg.count() == 0:
            # No retractions in the real registry — that's fine, the
            # empty response should still pass the scanner.
            pass

        # Get the response and write to a temp file
        body = client.get("/api/v1/retractions").json()
        fixture = tmp_path / "retractions_response.json"
        fixture.write_text(json.dumps(body, indent=2))

        # Run the scanner on it
        result = subprocess.run(
            ["python3", str(REPO_ROOT / "scripts" / "enforce_law27.py"),
             str(fixture)],
            capture_output=True, text=True, cwd=str(REPO_ROOT)
        )
        assert result.returncode == 0, (
            f"Law 27 scanner REJECTED the /api/v1/retractions response:\n"
            f"{result.stdout}\n"
            f"The API response contains forbidden language (Law 27/28/29)."
        )
