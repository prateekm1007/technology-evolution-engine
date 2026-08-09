#!/usr/bin/env python3
"""test_audit_instrument_freeze.py — Tests for audit instrument freeze.

Per audit round 52: the audit instrument must be frozen before the first
real engine-vs-null run. This creates a clean separation between the
thing being measured and the instrument doing the measurement.

Tests:
1. Frozen instrument artifact exists
2. SHA-256 matches
3. All required components are recorded
4. All 13 dimensions are frozen
5. All 5 states are frozen
6. NER component hashes are included
7. Diagnostic rule is documented
8. Runtime verification rejects mismatched instrument
"""
import hashlib
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

FROZEN_DIR = REPO_ROOT / "provenance" / "frozen_components"


class TestAuditInstrumentFreeze:
    """Verify the audit instrument is properly frozen."""

    def test_frozen_artifact_exists(self):
        """The frozen audit instrument artifact exists."""
        assert (FROZEN_DIR / "audit_instrument.json").exists()
        assert (FROZEN_DIR / "audit_instrument.sha256").exists()

    def test_sha256_matches(self):
        """The SHA-256 in the .sha256 file matches the artifact content."""
        artifact = json.loads((FROZEN_DIR / "audit_instrument.json").read_text())
        # Strip the hash field before computing
        artifact_without_hash = {k: v for k, v in artifact.items() if k != "instrument_sha256"}
        artifact_str = json.dumps(artifact_without_hash, sort_keys=True, separators=(",", ":"))
        computed_sha = hashlib.sha256(artifact_str.encode("utf-8")).hexdigest()

        frozen_sha = (FROZEN_DIR / "audit_instrument.sha256").read_text().split()[0]
        assert computed_sha == frozen_sha, (
            f"Audit instrument SHA mismatch: computed={computed_sha[:16]}... "
            f"frozen={frozen_sha[:16]}..."
        )

    def test_instrument_sha256_in_artifact(self):
        """The instrument_sha256 field is present in the artifact."""
        artifact = json.loads((FROZEN_DIR / "audit_instrument.json").read_text())
        assert "instrument_sha256" in artifact
        assert len(artifact["instrument_sha256"]) == 64

    def test_all_components_recorded(self):
        """All 5 instrument components have SHA-256 hashes."""
        artifact = json.loads((FROZEN_DIR / "audit_instrument.json").read_text())
        components = artifact["components"]
        expected = [
            "audit_script", "parser_script", "generation_null_script",
            "provenance_ledger_script", "content_addressed_storage_script",
        ]
        for name in expected:
            assert name in components, f"Missing component: {name}"
            assert "sha256" in components[name], f"Missing sha256 for {name}"
            assert len(components[name]["sha256"]) == 64

    def test_all_13_dimensions_frozen(self):
        """All 13 audit dimensions are frozen in the instrument."""
        artifact = json.loads((FROZEN_DIR / "audit_instrument.json").read_text())
        dims = artifact["audit_dimensions"]
        assert len(dims) == 13
        expected = {
            "source_pair", "upstream_extraction", "abstraction",
            "candidate_count", "candidate_schema", "candidate_length",
            "mechanism_presence", "information_available", "llm_access",
            "prompt_complexity", "entity_specificity", "human_intervention",
            "invocation_seed",
        }
        assert set(dims) == expected

    def test_all_5_states_frozen(self):
        """All 5 audit states are frozen in the instrument."""
        artifact = json.loads((FROZEN_DIR / "audit_instrument.json").read_text())
        states = artifact["audit_states"]
        assert len(states) == 5
        expected = {
            "CONTRACT_EQUAL", "OBSERVED_EQUAL", "OBSERVED_DIFFERENT",
            "NOT_OBSERVABLE", "NOT_RUN",
        }
        assert set(states) == expected

    def test_ner_component_hashes_included(self):
        """NER component SHA-256 hashes are included in the instrument."""
        artifact = json.loads((FROZEN_DIR / "audit_instrument.json").read_text())
        ner = artifact["ner_components"]
        assert ner["entity_dictionary_sha256"] is not None
        assert ner["stopword_set_sha256"] is not None
        assert ner["ner_model_info_sha256"] is not None

    def test_diagnostic_rule_documented(self):
        """The diagnostic rule is documented in the instrument."""
        artifact = json.loads((FROZEN_DIR / "audit_instrument.json").read_text())
        rule = artifact["diagnostic_rule"]
        assert "DIAGNOSTIC" in rule
        assert "not evidence" in rule.lower() or "NOT establish" in rule
        assert "fairness" in rule.lower()

    def test_output_schema_frozen(self):
        """The audit output schema is frozen."""
        artifact = json.loads((FROZEN_DIR / "audit_instrument.json").read_text())
        schema = artifact["audit_output_schema"]
        assert schema["audit_type"] == "BASELINE_EQUIVALENCE_AUDIT"
        assert "measurements" in schema
        assert "summary" in schema
        assert "fairness_established" in schema["summary"]

    def test_ledger_schema_frozen(self):
        """The ledger schema is frozen."""
        artifact = json.loads((FROZEN_DIR / "audit_instrument.json").read_text())
        schema = artifact["ledger_schema"]
        assert schema["ledger_type"] == "B2_PROVENANCE_LEDGER"
        assert "CANDIDATE_GENERATED" in schema["event_types"]
        assert "ADJUDICATION_RECORDED" in schema["event_types"]
        assert "immutability" in schema

    def test_component_hashes_match_actual_files(self):
        """The frozen component SHA-256 hashes match the actual source files."""
        artifact = json.loads((FROZEN_DIR / "audit_instrument.json").read_text())
        components = artifact["components"]

        for name, info in components.items():
            path = REPO_ROOT / info["path"]
            assert path.exists(), f"Component file not found: {path}"
            actual_sha = hashlib.sha256(path.read_bytes()).hexdigest()
            assert actual_sha == info["sha256"], (
                f"Component '{name}' SHA mismatch: "
                f"actual={actual_sha[:16]}... frozen={info['sha256'][:16]}..."
            )
