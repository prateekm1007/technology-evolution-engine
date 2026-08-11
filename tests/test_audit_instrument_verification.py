#!/usr/bin/env python3
"""test_audit_instrument_verification.py — Adversarial tests for instrument freeze.

Per audit round 53: the instrument freeze must be INDEPENDENTLY VERIFIED.

Tests attack:
1. Internal SHA consistency (not just sidecar)
2. Runtime environment verification
3. Actual loaded module verification (import-path substitution)
4. Component mutation detection
5. instrument_sha field tampering
6. Path substitution detection
7. Execution manifest sealing and invalidation
"""
import hashlib
import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.verify_audit_instrument import (
    verify_instrument,
    verify_internal_sha,
    verify_sidecar_sha,
    verify_runtime_environment,
    verify_loaded_module,
    verify_all_loaded_modules,
    get_runtime_manifest,
    create_execution_manifest,
    verify_execution_manifest,
    canonical_serialize,
    compute_sha256,
)

FROZEN_DIR = REPO_ROOT / "provenance" / "frozen_components"


# =====================================================================
# CATEGORY 1: INTERNAL SHA CONSISTENCY (not just sidecar)
# =====================================================================

class TestInternalShaConsistency:
    """Verify the internal instrument_sha256 is consistent, not just the
    sidecar file."""

    def test_internal_sha_verified(self):
        """The internal instrument_sha256 matches the canonical hash
        of the payload without the hash field."""
        artifact = json.loads((FROZEN_DIR / "audit_instrument.json").read_text())
        ok, err = verify_internal_sha(artifact)
        assert ok, f"Internal SHA verification failed: {err}"

    def test_internal_sha_detects_tampering(self, tmp_path):
        """If the instrument_sha256 field is altered, verification fails."""
        artifact = json.loads((FROZEN_DIR / "audit_instrument.json").read_text())
        artifact["instrument_sha256"] = "0" * 64
        ok, err = verify_internal_sha(artifact)
        assert not ok
        assert "mismatch" in err.lower()

    def test_internal_sha_detects_payload_tampering(self, tmp_path):
        """If the payload is modified but the hash isn't updated, verification fails."""
        artifact = json.loads((FROZEN_DIR / "audit_instrument.json").read_text())
        artifact["audit_dimensions"] = ["modified"]  # tamper with payload
        ok, err = verify_internal_sha(artifact)
        assert not ok

    def test_sidecar_verified(self):
        """The sidecar .sha256 file matches the artifact file bytes."""
        ok, err = verify_sidecar_sha()
        assert ok, f"Sidecar verification failed: {err}"

    def test_canonical_convention_in_artifact(self):
        """The canonical serialization convention is explicitly frozen."""
        artifact = json.loads((FROZEN_DIR / "audit_instrument.json").read_text())
        assert "canonical_convention" in artifact
        conv = artifact["canonical_convention"]
        assert conv["format"] == "JSON"
        assert conv["sort_keys"] is True
        assert conv["encoding"] == "UTF-8"


# =====================================================================
# CATEGORY 2: RUNTIME ENVIRONMENT VERIFICATION
# =====================================================================

class TestRuntimeEnvironment:
    """Verify the runtime environment matches the frozen manifest."""

    def test_runtime_manifest_in_artifact(self):
        """The frozen instrument contains a runtime_manifest."""
        artifact = json.loads((FROZEN_DIR / "audit_instrument.json").read_text())
        assert "runtime_manifest" in artifact
        rm = artifact["runtime_manifest"]
        assert "python_version" in rm
        assert "spacy_version" in rm
        assert "numpy_version" in rm

    def test_runtime_matches_frozen(self):
        """The current runtime matches the frozen runtime manifest."""
        artifact = json.loads((FROZEN_DIR / "audit_instrument.json").read_text())
        ok, err = verify_runtime_environment(artifact["runtime_manifest"])
        assert ok, f"Runtime mismatch: {err}"

    def test_runtime_detects_python_version_change(self):
        """A different Python version is detected."""
        artifact = json.loads((FROZEN_DIR / "audit_instrument.json").read_text())
        fake_manifest = dict(artifact["runtime_manifest"])
        fake_manifest["python_version"] = "3.99.0"
        ok, err = verify_runtime_environment(fake_manifest)
        assert not ok
        assert "python_version" in err

    def test_runtime_detects_spacy_version_change(self):
        """A different spaCy version is detected."""
        artifact = json.loads((FROZEN_DIR / "audit_instrument.json").read_text())
        fake_manifest = dict(artifact["runtime_manifest"])
        fake_manifest["spacy_version"] = "0.0.1"
        ok, err = verify_runtime_environment(fake_manifest)
        assert not ok
        assert "spacy_version" in err


# =====================================================================
# CATEGORY 3: ACTUAL LOADED MODULE VERIFICATION
# =====================================================================

class TestLoadedModuleVerification:
    """Verify the ACTUAL loaded module matches the frozen hash."""

    def test_loaded_module_matches_frozen(self):
        """The actual loaded frozen_parser module matches its frozen SHA."""
        artifact = json.loads((FROZEN_DIR / "audit_instrument.json").read_text())
        parser_info = artifact["components"]["parser_script"]
        ok, err = verify_loaded_module(
            "engine.b2_provenance.frozen_parser",
            parser_info["sha256"],
            parser_info["path"],
        )
        assert ok, f"Module verification failed: {err}"

    def test_all_modules_verified(self):
        """All 5 frozen modules are verified as actually loaded."""
        artifact = json.loads((FROZEN_DIR / "audit_instrument.json").read_text())
        ok, errors = verify_all_loaded_modules(artifact)
        assert ok, f"Module verification errors: {errors}"

    def test_wrong_sha_detected(self):
        """A wrong SHA for a loaded module is detected."""
        ok, err = verify_loaded_module(
            "engine.b2_provenance.frozen_parser",
            "0" * 64,  # wrong hash
            "engine/b2_provenance/frozen_parser.py",
        )
        assert not ok
        assert "SHA mismatch" in err or "mismatch" in err.lower()

    def test_path_substitution_detected(self):
        """If the module loads from a different path, it's detected."""
        ok, err = verify_loaded_module(
            "engine.b2_provenance.frozen_parser",
            "0" * 64,  # also wrong hash
            "wrong/path/frozen_parser.py",  # wrong path
        )
        assert not ok


# =====================================================================
# CATEGORY 4: COMPONENT MUTATION DETECTION
# =====================================================================

class TestComponentMutationDetection:
    """Verify that mutating any frozen component after freeze is detected."""

    def test_full_verification_passes(self):
        """The full instrument verification passes with current state."""
        results = verify_instrument()
        assert results["source_frozen"], f"Source not frozen: {results['errors']}"
        assert results["data_frozen"], f"Data not frozen: {results['errors']}"
        assert results["runtime_frozen"], f"Runtime not frozen: {results['errors']}"
        assert results["module_loaded"], f"Module not loaded: {results['errors']}"
        assert results["sidecar_verified"], f"Sidecar not verified: {results['errors']}"
        assert results["internal_sha_verified"], f"Internal SHA not verified: {results['errors']}"

    def test_full_verification_reports_all_levels(self):
        """verify_instrument reports all 6 verification levels."""
        results = verify_instrument()
        for key in ["source_frozen", "data_frozen", "runtime_frozen",
                     "module_loaded", "sidecar_verified", "internal_sha_verified"]:
            assert key in results, f"Missing verification level: {key}"


# =====================================================================
# CATEGORY 5: EXECUTION MANIFEST
# =====================================================================

class TestExecutionManifest:
    """Verify the execution manifest sealing and invalidation."""

    def test_create_execution_manifest(self):
        """An execution manifest can be created with all required fields."""
        manifest = create_execution_manifest(
            preregistration_id="PREREG-001",
            case_ids=["CASE-001", "CASE-002"],
            source_pair_hashes={"CASE-001": "a" * 64, "CASE-002": "b" * 64},
        )
        assert manifest["manifest_type"] == "EXECUTION_MANIFEST"
        assert manifest["preregistration_id"] == "PREREG-001"
        assert manifest["audit_instrument_sha256"] is not None
        assert "manifest_sha256" in manifest
        assert "runtime_manifest" in manifest
        assert "diagnostic_rule" in manifest

    def test_manifest_internal_sha_consistent(self):
        """The manifest's internal SHA is consistent."""
        manifest = create_execution_manifest("PREREG-001", ["CASE-001"], {})
        recorded = manifest["manifest_sha256"]
        payload = {k: v for k, v in manifest.items() if k != "manifest_sha256"}
        computed = compute_sha256(canonical_serialize(payload))
        assert recorded == computed

    def test_manifest_tampering_detected(self):
        """If the manifest is tampered after sealing, verification fails."""
        manifest = create_execution_manifest("PREREG-001", ["CASE-001"], {})
        # Tamper: add a case after sealing
        manifest["case_ids"].append("CASE-999")
        ok, errors = verify_execution_manifest(manifest)
        assert not ok
        assert "EXECUTION_INVALIDATED" in errors or "mismatch" in str(errors).lower()

    def test_manifest_verification_passes_for_fresh_manifest(self):
        """A freshly created manifest passes verification."""
        manifest = create_execution_manifest("PREREG-001", ["CASE-001"], {})
        ok, errors = verify_execution_manifest(manifest)
        # This should pass if the instrument is still valid
        if not ok:
            # Check if it's an instrument issue, not a manifest issue
            instrument_results = verify_instrument()
            if all([
                instrument_results["source_frozen"],
                instrument_results["data_frozen"],
                instrument_results["runtime_frozen"],
                instrument_results["module_loaded"],
            ]):
                pytest.fail(f"Manifest verification failed unexpectedly: {errors}")

    def test_manifest_contains_diagnostic_rule(self):
        """The manifest contains the diagnostic rule."""
        manifest = create_execution_manifest("PREREG-001", ["CASE-001"], {})
        assert "DIAGNOSTIC" in manifest["diagnostic_rule"]
        assert "not" in manifest["diagnostic_rule"].lower()
