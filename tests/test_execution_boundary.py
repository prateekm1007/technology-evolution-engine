#!/usr/bin/env python3
"""test_execution_boundary.py — Pre-execution boundary adversarial test.

Per audit round 54: test the ENTIRE pre-execution boundary, not just
individual components. Deliberately:

1. Create a valid execution manifest
2. Mutate one frozen component → verify execution refuses
3. Restore → verify execution proceeds
4. Mutate case-set hash → verify refusal
5. Mutate runtime manifest → verify refusal
6. Restore everything → verify execution proceeds

This establishes:
    The system cannot accidentally run an execution whose declared
    experimental substrate differs from the substrate actually being executed.

CRITICAL RULE (per audit round 54):
    The first run produces artifacts and stops. The coding agent has NO
    authority to declare the result good, bad, significant, fair, or
    successful. It should produce artifacts and stop.
"""
import hashlib
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.verify_audit_instrument import (
    create_execution_manifest,
    verify_execution_manifest,
    verify_instrument,
    get_runtime_manifest,
    canonical_serialize,
    compute_sha256,
)


class TestExecutionBoundary:
    """Test the entire pre-execution boundary.

    The system cannot accidentally run an execution whose declared
    experimental substrate differs from the substrate actually being executed.
    """

    def _create_valid_manifest(self):
        """Create a valid execution manifest."""
        return create_execution_manifest(
            preregistration_id="PREREG-TEST-001",
            case_ids=["CASE-001", "CASE-002", "CASE-003"],
            source_pair_hashes={
                "CASE-001": "a" * 64,
                "CASE-002": "b" * 64,
                "CASE-003": "c" * 64,
            },
        )

    def test_01_valid_manifest_passes_verification(self):
        """Step 1: A valid execution manifest passes verification."""
        manifest = self._create_valid_manifest()
        ok, errors = verify_execution_manifest(manifest)
        assert ok, f"Valid manifest failed verification: {errors}"

    def test_02_mutate_instrument_sha_fails(self):
        """Step 2: Mutating the instrument SHA → EXECUTION_INVALIDATED."""
        manifest = self._create_valid_manifest()
        # Mutate: change the instrument SHA to a fake value
        manifest["audit_instrument_sha256"] = "0" * 64
        ok, errors = verify_execution_manifest(manifest)
        assert not ok
        assert "EXECUTION_INVALIDATED" in errors

    def test_03_mutate_case_set_fails(self):
        """Step 3: Mutating the case set → EXECUTION_INVALIDATED."""
        manifest = self._create_valid_manifest()
        # Mutate: add a case after sealing
        manifest["case_ids"].append("CASE-EVIL")
        ok, errors = verify_execution_manifest(manifest)
        assert not ok
        assert "EXECUTION_INVALIDATED" in errors

    def test_04_mutate_source_pair_hash_fails(self):
        """Step 4: Mutating a source pair hash → EXECUTION_INVALIDATED."""
        manifest = self._create_valid_manifest()
        # Mutate: change a source pair hash
        manifest["source_pair_hashes"]["CASE-001"] = "x" * 64
        ok, errors = verify_execution_manifest(manifest)
        assert not ok
        assert "EXECUTION_INVALIDATED" in errors

    def test_05_mutate_preregistration_id_fails(self):
        """Step 5: Mutating the preregistration ID → EXECUTION_INVALIDATED."""
        manifest = self._create_valid_manifest()
        # Mutate: change the preregistration ID
        manifest["preregistration_id"] = "FAKE-PREREG"
        ok, errors = verify_execution_manifest(manifest)
        assert not ok
        assert "EXECUTION_INVALIDATED" in errors

    def test_06_mutate_seed_derivation_rule_fails(self):
        """Step 6: Mutating the seed derivation rule → EXECUTION_INVALIDATED."""
        manifest = self._create_valid_manifest()
        # Mutate: change the seed rule
        manifest["seed_derivation_rule"] = "SHA256(case_id || 'downstream')"
        ok, errors = verify_execution_manifest(manifest)
        assert not ok
        assert "EXECUTION_INVALIDATED" in errors

    def test_07_mutate_runtime_manifest_fails(self):
        """Step 7: Mutating the runtime manifest → EXECUTION_INVALIDATED."""
        manifest = self._create_valid_manifest()
        # Mutate: change the Python version in the runtime manifest
        manifest["runtime_manifest"]["python_version"] = "3.99.0"
        ok, errors = verify_execution_manifest(manifest)
        assert not ok
        assert "EXECUTION_INVALIDATED" in errors

    def test_08_mutate_diagnostic_rule_fails(self):
        """Step 8: Mutating the diagnostic rule → EXECUTION_INVALIDATED.
        The diagnostic rule is part of the sealed manifest."""
        manifest = self._create_valid_manifest()
        # Mutate: change the diagnostic rule
        manifest["diagnostic_rule"] = "This execution IS evidence."
        ok, errors = verify_execution_manifest(manifest)
        assert not ok
        assert "EXECUTION_INVALIDATED" in errors

    def test_09_restore_everything_passes(self):
        """Step 9: After restoring everything, execution proceeds."""
        # Create a fresh valid manifest (simulating restoration)
        manifest = self._create_valid_manifest()
        ok, errors = verify_execution_manifest(manifest)
        assert ok, f"Restored manifest failed: {errors}"

    def test_10_manifest_sha_field_removal_fails(self):
        """Removing the manifest_sha256 field → EXECUTION_INVALIDATED."""
        manifest = self._create_valid_manifest()
        del manifest["manifest_sha256"]
        ok, errors = verify_execution_manifest(manifest)
        assert not ok
        assert "EXECUTION_INVALIDATED" in errors or "manifest_sha256" in str(errors)

    def test_11_manifest_tampering_detected_after_seal(self):
        """The manifest is sealed (hash computed) and any post-seal
        modification is detected. This is the central invariant:

        'The system cannot accidentally run an execution whose declared
         experimental substrate differs from the substrate actually
         being executed.'
        """
        manifest = self._create_valid_manifest()

        # Record the sealed hash
        sealed_hash = manifest["manifest_sha256"]

        # Attempt to modify ANY field after sealing
        modifications = [
            ("preregistration_id", "HACKED"),
            ("case_ids", ["HACKED"]),
            ("source_pair_hashes", {"HACKED": "0" * 64}),
            ("seed_derivation_rule", "HACKED"),
            ("diagnostic_rule", "HACKED"),
        ]

        for field, value in modifications:
            tampered = dict(manifest)
            tampered[field] = value
            # Keep the original sealed hash (don't update it)
            tampered["manifest_sha256"] = sealed_hash

            ok, errors = verify_execution_manifest(tampered)
            assert not ok, (
                f"Tampering with '{field}' was NOT detected! "
                f"The execution boundary is compromised."
            )
            assert "EXECUTION_INVALIDATED" in errors or "mismatch" in str(errors).lower()

    def test_12_execution_refuses_when_instrument_changed(self, tmp_path, monkeypatch):
        """If a frozen component changes after the manifest is sealed,
        execution is invalidated. This simulates: source file modified
        after manifest creation."""
        # This test patches verify_instrument to simulate a changed component
        manifest = self._create_valid_manifest()

        # Patch verify_instrument to return failure (simulating changed source)
        with patch("scripts.verify_audit_instrument.verify_instrument") as mock_verify:
            mock_verify.return_value = {
                "source_frozen": False,  # Source changed!
                "data_frozen": True,
                "runtime_frozen": True,
                "module_loaded": True,
                "sidecar_verified": True,
                "internal_sha_verified": True,
                "errors": ["SOURCE: audit_script: SHA mismatch"],
            }

            ok, errors = verify_execution_manifest(manifest)
            assert not ok
            assert "EXECUTION_INVALIDATED" in errors
            assert "Audit instrument verification FAILED" in errors

    def test_13_diagnostic_rule_preserved_in_manifest(self):
        """The diagnostic rule is preserved in the manifest and cannot
        be removed without invalidation."""
        manifest = self._create_valid_manifest()
        assert "diagnostic_rule" in manifest
        assert "DIAGNOSTIC" in manifest["diagnostic_rule"]
        assert "not" in manifest["diagnostic_rule"].lower()

    def test_14_no_authority_to_declare_result(self):
        """Document (as a test) that the first run produces artifacts
        and stops. The coding agent has NO authority to declare the
        result good, bad, significant, fair, or successful.

        This test exists to enforce the rule that the diagnostic run
        is not an optimization loop."""
        manifest = self._create_valid_manifest()
        rule = manifest["diagnostic_rule"]

        # The diagnostic rule must explicitly say the result is NOT evidence
        assert "not" in rule.lower() or "NOT" in rule, (
            "The diagnostic rule must state the result is NOT evidence."
        )

        # The manifest must not contain any field suggesting the result
        # will be interpreted as success/failure
        for key in manifest:
            assert "success" not in key.lower(), (
                f"Manifest contains '{key}' — the first run cannot declare success."
            )
            assert "failure" not in key.lower(), (
                f"Manifest contains '{key}' — the first run cannot declare failure."
            )
            assert "fair" not in key.lower(), (
                f"Manifest contains '{key}' — the first run cannot declare fairness."
            )
