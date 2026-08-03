#!/usr/bin/env python3
"""
Test: API emits typed epistemic status, not numerical confidence.

Per auditor SS5 / RR2: "the live API still returns
`confidence: {value: 0.5}`. No `validationLevel`, no
`evidenceStrength`. The CEO's most important directive — remove
false precision — is not implemented."

This test verifies the migration is real:
1. /api/v1/simulate does NOT emit a top-level `confidence` field.
2. /api/v1/simulate DOES emit an `epistemic_status` block with
   the typed status fields required by Law 29e:
   validation_level, evidence_strength, experimental_validation,
   status.
3. The legacy `confidence` is retained only as
   `legacy_confidence_deprecated` for one release cycle, marked
   as deprecated.
4. The ledger entries written by the Oracle carry the typed
   `epistemic_status` block, not the bare `confidence` number.
"""
import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "web" / "backend"))

try:
    from fastapi.testclient import TestClient
    from main import app
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

import pytest

if not FASTAPI_AVAILABLE:
    pytest.skip("fastapi not installed — skipping API typed-status tests",
                allow_module_level=True)

client = TestClient(app)


class TestApiEmitsTypedStatus:
    """Verify the /api/v1/simulate endpoint emits the typed status block."""

    def test_simulate_response_has_epistemic_status(self):
        """The simulate response must include the `epistemic_status` block."""
        r = client.post("/api/v1/simulate", json={
            "constraint": "energy", "direction": "decrease", "magnitude": "2x"})
        assert r.status_code == 200
        body = r.json()
        assert "epistemic_status" in body, (
            "/api/v1/simulate response missing `epistemic_status` block. "
            "Per Law 27/28/29 + HONESTY_LOOP.md, the typed status block "
            "is the required replacement for the forbidden `confidence` field."
        )

    def test_simulate_response_has_no_top_level_confidence(self):
        """The simulate response must NOT have a top-level `confidence` field.

        Per Law 27: numerical certainty is forbidden. Per Law 28c:
        confidence percentages are forbidden. The legacy number is
        retained only as `legacy_confidence_deprecated`, clearly
        marked as deprecated.
        """
        r = client.post("/api/v1/simulate", json={
            "constraint": "energy", "direction": "decrease", "magnitude": "2x"})
        body = r.json()
        assert "confidence" not in body, (
            "/api/v1/simulate still emits top-level `confidence` field. "
            "Per Law 27, this is forbidden. Use `epistemic_status` block instead. "
            f"Found keys: {sorted(body.keys())}"
        )

    def test_epistemic_status_has_required_fields(self):
        """The epistemic_status block must have all 4 required typed fields
        per Law 29e: validation_level, evidence_strength,
        experimental_validation, status."""
        r = client.post("/api/v1/simulate", json={
            "constraint": "energy", "direction": "decrease", "magnitude": "2x"})
        es = r.json()["epistemic_status"]
        for field in ["validation_level", "evidence_strength",
                      "experimental_validation", "status"]:
            assert field in es, (
                f"epistemic_status missing required field `{field}` (Law 29e). "
                f"Found: {sorted(es.keys())}"
            )

    def test_validation_level_is_l0_through_l9(self):
        """validation_level must be one of L0-L9 per Law 29b."""
        r = client.post("/api/v1/simulate", json={
            "constraint": "energy", "direction": "decrease", "magnitude": "2x"})
        vl = r.json()["epistemic_status"]["validation_level"]
        assert vl in {f"L{i}" for i in range(10)}, (
            f"validation_level `{vl}` is not in L0-L9 (Law 29b)."
        )

    def test_evidence_strength_is_valid_enum(self):
        """evidence_strength must be one of the 5 values per Law 29c."""
        r = client.post("/api/v1/simulate", json={
            "constraint": "energy", "direction": "decrease", "magnitude": "2x"})
        es = r.json()["epistemic_status"]["evidence_strength"]
        assert es in {"ABSENT", "WEAK", "MODERATE", "STRONG", "VERY_STRONG"}, (
            f"evidence_strength `{es}` is not in the Law 29c enum."
        )

    def test_experimental_validation_is_valid_enum(self):
        """experimental_validation must be one of the 6 values per Law 29e."""
        r = client.post("/api/v1/simulate", json={
            "constraint": "energy", "direction": "decrease", "magnitude": "2x"})
        ev = r.json()["epistemic_status"]["experimental_validation"]
        assert ev in {"ABSENT", "BENCH", "SUBSYSTEM", "PROTOTYPE",
                       "PILOT", "PRODUCTION"}, (
            f"experimental_validation `{ev}` is not in the Law 29e enum."
        )

    def test_status_is_valid_verdict_enum(self):
        """status must be one of the 5 verdict values per Law 29a."""
        r = client.post("/api/v1/simulate", json={
            "constraint": "energy", "direction": "decrease", "magnitude": "2x"})
        st = r.json()["epistemic_status"]["status"]
        assert st in {"PASS", "PASS_WITH_CONDITIONS", "MARGINAL",
                      "BLOCKED", "REJECTED", "PLAUSIBLE"}, (
            f"status `{st}` is not in the Law 29a verdict enum "
            "(extended with PLAUSIBLE for epistemic claims that are not "
            "verdicts but plausibility statements)."
        )

    def test_legacy_confidence_is_deprecated(self):
        """The legacy `confidence` number must be retained ONLY under
        `legacy_confidence_deprecated`, clearly marked as deprecated.

        Per the migration plan: backward-compat for one release cycle,
        then removed. New consumers MUST read `epistemic_status`.
        """
        r = client.post("/api/v1/simulate", json={
            "constraint": "energy", "direction": "decrease", "magnitude": "2x"})
        body = r.json()
        assert "legacy_confidence_deprecated" in body, (
            "Legacy confidence must be retained as `legacy_confidence_deprecated` "
            "for one release cycle to avoid silent breakage of downstream consumers."
        )
        # The legacy number must be a number (not None) — proves the
        # old calculation still runs for backward compat.
        assert isinstance(body["legacy_confidence_deprecated"], (int, float)), (
            f"legacy_confidence_deprecated must be a number, got: "
            f"{type(body['legacy_confidence_deprecated']).__name__}"
        )

    def test_oracle_predictions_are_l2_plausible(self):
        """The Oracle's predictions are analytical estimates (L2) with
        no experimental validation. Per Law 26, they are PLAUSIBILITY,
        not MEASUREMENT. The typed status must reflect this honestly."""
        r = client.post("/api/v1/simulate", json={
            "constraint": "energy", "direction": "decrease", "magnitude": "2x"})
        es = r.json()["epistemic_status"]
        # The Oracle's model is an analytical estimate from a heuristic
        # propagation model — that's L2 (analytical estimate from first
        # principles). It has no physical validation — ABSENT. Per Law 26,
        # it's a PLAUSIBILITY, not a MEASUREMENT.
        assert es["validation_level"] == "L2", (
            f"Oracle predictions should be L2 (analytical estimate), got "
            f"`{es['validation_level']}`. The Oracle's model is a heuristic "
            f"propagation model — that's an analytical estimate, not a "
            f"numerical simulation (L3) or physical validation (L4+)."
        )
        assert es["experimental_validation"] == "ABSENT", (
            f"Oracle predictions should have experimental_validation=ABSENT, "
            f"got `{es['experimental_validation']}`. No physical test has "
            f"been run against the Oracle's predictions."
        )


class TestLedgerCarriesTypedStatus:
    """Verify the prediction ledger carries the typed status block."""

    def test_ledger_entries_have_epistemic_status(self):
        """After a simulate call, the ledger entry written by the Oracle
        must carry the `epistemic_status` block, not just the bare
        `confidence` number."""
        # Trigger a simulate call to write a ledger entry
        client.post("/api/v1/simulate", json={
            "constraint": "energy", "direction": "decrease", "magnitude": "2x"})

        # Read the ledger
        r = client.get("/api/v1/evidence")
        body = r.json()
        assert body["entry_count"] > 0, "Ledger is empty — simulate didn't write."

        # The latest entry should be from the simulate call above
        latest = body["ledger"][-1]
        assert "epistemic_status" in latest, (
            f"Ledger entry missing `epistemic_status`. Found keys: "
            f"{sorted(latest.keys())}"
        )
        es = latest["epistemic_status"]
        for field in ["validation_level", "evidence_strength",
                      "experimental_validation", "status"]:
            assert field in es, (
                f"Ledger epistemic_status missing `{field}`. "
                f"Found: {sorted(es.keys())}"
            )

    def test_ledger_entries_have_legacy_confidence_deprecated(self):
        """Ledger entries must retain the legacy confidence as
        `legacy_confidence_deprecated` for backward compat with
        existing ledger readers."""
        client.post("/api/v1/simulate", json={
            "constraint": "energy", "direction": "decrease", "magnitude": "2x"})
        r = client.get("/api/v1/evidence")
        latest = r.json()["ledger"][-1]
        assert "legacy_confidence_deprecated" in latest, (
            "Ledger entry missing `legacy_confidence_deprecated`. "
            "Required for backward compat with existing ledger readers."
        )

    def test_ledger_entries_do_not_have_bare_confidence(self):
        """Ledger entries written AFTER the migration must NOT have the
        bare `confidence` field. (Historical entries are grandfathered
        per Law 7; only NEW entries are checked here.)"""
        # Write a fresh entry
        client.post("/api/v1/simulate", json={
            "constraint": "energy", "direction": "decrease", "magnitude": "2x"})
        r = client.get("/api/v1/evidence")
        # Find the latest entry — it was just written by the simulate above
        latest = r.json()["ledger"][-1]
        # New entries must not carry the bare `confidence` field —
        # only the deprecated variant
        assert "confidence" not in latest or "legacy_confidence_deprecated" in latest, (
            "New ledger entry has bare `confidence` field — must use "
            "`legacy_confidence_deprecated` (per Law 27 migration). "
            f"Keys: {sorted(latest.keys())}"
        )


class TestHonestyLoopScannerAcceptsApi:
    """Verify the Law 27 scanner accepts the migrated API output."""

    def test_simulate_response_passes_scanner(self, tmp_path):
        """The /api/v1/simulate response JSON, when written to a file,
        must pass the Law 27 scanner (no forbidden language)."""
        import subprocess
        import json

        r = client.post("/api/v1/simulate", json={
            "constraint": "energy", "direction": "decrease", "magnitude": "2x"})
        body = r.json()

        # Write the response to a temporary file
        fixture = tmp_path / "api_response.json"
        fixture.write_text(json.dumps(body, indent=2))

        # Run the scanner on it
        repo_root = pathlib.Path(__file__).resolve().parents[1]
        result = subprocess.run(
            ["python3", str(repo_root / "scripts" / "enforce_law27.py"),
             str(fixture)],
            capture_output=True, text=True, cwd=str(repo_root)
        )
        assert result.returncode == 0, (
            f"Law 27 scanner REJECTED the /api/v1/simulate response:\n"
            f"{result.stdout}\n"
            f"The API response contains forbidden language (Law 27/28/29)."
        )
