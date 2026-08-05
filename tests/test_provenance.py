#!/usr/bin/env python3
"""
test_provenance.py — DR-43 tests.

Per DR-43 test requirements:
  - provenance is attached to every extracted item
  - publication_date < prediction_lock_time
  - retrieval timestamps are recorded
  - provenance hashes change when the source changes
"""
import sys
import pathlib
import pytest
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.provenance import ProvenanceManager, ProvenanceRecord


class TestProvenanceCreation:
    """Test provenance record creation."""

    def test_create_provenance_returns_record(self):
        """Exact case: create_provenance returns ProvenanceRecord."""
        pm = ProvenanceManager()
        prov = pm.create_provenance(
            source_id="arxiv_001",
            source_section="methods",
            char_start=100,
            char_end=200,
            source_text="The nanofiber membrane was fabricated.",
        )
        assert isinstance(prov, ProvenanceRecord)
        assert prov.source_id == "arxiv_001"
        assert prov.source_section == "methods"
        assert prov.char_start == 100
        assert prov.char_end == 200
        assert prov.retrieval_timestamp != ""
        assert prov.provenance_hash != ""
        assert "nanofiber" in prov.source_text_snippet

    def test_provenance_has_retrieval_timestamp(self):
        """DR-43: retrieval timestamp is recorded."""
        pm = ProvenanceManager()
        prov = pm.create_provenance("id", "methods", 0, 10, "text")
        assert prov.retrieval_timestamp != ""
        # Should be ISO format
        datetime.fromisoformat(prov.retrieval_timestamp.replace("Z", "+00:00"))

    def test_provenance_has_hash(self):
        """DR-43: provenance hash is computed."""
        pm = ProvenanceManager()
        prov = pm.create_provenance("id", "methods", 0, 10, "test text")
        assert len(prov.provenance_hash) >= 32  # SHA-256


class TestTemporalInvariants:
    """Test temporal invariant validation (EPISTEMIC_ENGINE.md §2.2)."""

    def test_publication_before_lock_time_passes(self):
        """publication_date < prediction_lock_time → valid."""
        pm = ProvenanceManager()
        errors = pm.validate_temporal_invariant(
            "2020-01-01T00:00:00+00:00",
            "2026-08-06T00:00:00+00:00"
        )
        assert len(errors) == 0

    def test_publication_after_lock_time_fails(self):
        """publication_date >= prediction_lock_time → violation."""
        pm = ProvenanceManager()
        errors = pm.validate_temporal_invariant(
            "2027-01-01T00:00:00+00:00",
            "2026-08-06T00:00:00+00:00"
        )
        assert len(errors) > 0
        assert "F-064" in errors[0]

    def test_missing_publication_date_fails(self):
        """Missing publication_date → error."""
        pm = ProvenanceManager()
        errors = pm.validate_temporal_invariant("", "2026-08-06T00:00:00+00:00")
        assert len(errors) > 0

    def test_retrieval_before_verification_passes(self):
        """retrieval_timestamp <= verification_timestamp → valid."""
        pm = ProvenanceManager()
        errors = pm.validate_retrieval_before_verification(
            "2026-08-05T00:00:00+00:00",
            "2026-08-06T00:00:00+00:00"
        )
        assert len(errors) == 0

    def test_retrieval_after_verification_fails(self):
        """retrieval_timestamp > verification_timestamp → error."""
        pm = ProvenanceManager()
        errors = pm.validate_retrieval_before_verification(
            "2026-08-07T00:00:00+00:00",
            "2026-08-06T00:00:00+00:00"
        )
        assert len(errors) > 0


class TestProvenanceValidation:
    """Test provenance presence validation."""

    def test_all_items_have_provenance(self):
        """All items with provenance → no errors."""
        pm = ProvenanceManager()
        items = [
            {"source_id": "a", "source_section": "methods",
             "char_start": 0, "char_end": 10, "retrieval_timestamp": "2026-01-01"},
            {"source_id": "b", "source_section": "results",
             "char_start": 0, "char_end": 20, "retrieval_timestamp": "2026-01-02"},
        ]
        errors = pm.validate_provenance_present(items)
        # Debug: if errors, print them
        if errors:
            print(f"Errors: {errors}")
        assert len(errors) == 0

    def test_missing_provenance_detected(self):
        """Missing provenance fields → errors."""
        pm = ProvenanceManager()
        items = [
            {"source_id": "a", "source_section": ""},  # missing fields
        ]
        errors = pm.validate_provenance_present(items)
        assert len(errors) > 0


class TestProvenanceHash:
    """Test provenance hash behavior."""

    def test_hash_deterministic(self):
        """Same text → same hash."""
        pm = ProvenanceManager()
        h1 = pm.compute_provenance_hash("test text")
        h2 = pm.compute_provenance_hash("test text")
        assert h1 == h2

    def test_hash_changes_with_content(self):
        """Different text → different hash."""
        pm = ProvenanceManager()
        assert pm.hash_changes_with_content("text A", "text B")
        assert not pm.hash_changes_with_content("same", "same")


class TestModuleContract:
    """Test module importability."""

    def test_module_importable(self):
        from scripts.provenance import ProvenanceManager, ProvenanceRecord
        assert hasattr(ProvenanceManager, "create_provenance")
        assert hasattr(ProvenanceManager, "validate_temporal_invariant")
        assert hasattr(ProvenanceManager, "validate_provenance_present")
        assert hasattr(ProvenanceManager, "compute_provenance_hash")
