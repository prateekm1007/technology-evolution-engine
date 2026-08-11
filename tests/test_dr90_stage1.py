"""Tests for dr90_stage1_representation_library.py — DR-90 Stage 1.

Tests that the representation library:
- Has the correct structure (each entry has required fields)
- Contains real historical examples
- Reveals transformation patterns
- Is saved/loaded correctly as JSON
"""
import sys
import json
import tempfile
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest


def test_library_imports():
    """Module imports cleanly."""
    from scripts.dr90_stage1_representation_library import (
        REPRESENTATION_LIBRARY, save_library, load_library, analyze_library,
    )
    assert len(REPRESENTATION_LIBRARY) > 0


def test_library_has_required_fields():
    """Each entry has all required fields."""
    from scripts.dr90_stage1_representation_library import REPRESENTATION_LIBRARY
    required = ["id", "primitive", "field", "why_it_mattered",
                "what_representation_changed", "what_previous_representation_failed",
                "what_new_search_became_possible"]
    for entry in REPRESENTATION_LIBRARY:
        for field in required:
            assert field in entry, f"Entry {entry.get('id', '?')} missing field: {field}"
            assert entry[field], f"Entry {entry.get('id', '?')} has empty field: {field}"


def test_library_has_at_least_25_entries():
    """Library has at least 25 entries (initial target)."""
    from scripts.dr90_stage1_representation_library import REPRESENTATION_LIBRARY
    assert len(REPRESENTATION_LIBRARY) >= 25, \
        f"Library has {len(REPRESENTATION_LIBRARY)} entries. Expected ≥25."


def test_library_covers_multiple_fields():
    """Library covers multiple fields (not just one domain)."""
    from scripts.dr90_stage1_representation_library import REPRESENTATION_LIBRARY
    from collections import Counter
    fields = Counter(e["field"] for e in REPRESENTATION_LIBRARY)
    assert len(fields) >= 5, \
        f"Library covers only {len(fields)} fields. Expected ≥5 for diversity."


def test_library_has_id_pattern():
    """All entries have REP-### ID format."""
    from scripts.dr90_stage1_representation_library import REPRESENTATION_LIBRARY
    for entry in REPRESENTATION_LIBRARY:
        assert entry["id"].startswith("REP-"), \
            f"Entry ID {entry['id']} doesn't follow REP-### pattern"


def test_save_and_load():
    """Library saves and loads correctly as JSON."""
    from scripts.dr90_stage1_representation_library import (
        REPRESENTATION_LIBRARY, save_library, load_library,
    )
    tmpdir = tempfile.mkdtemp()
    path = os.path.join(tmpdir, "test_library.json")
    save_library(path)
    loaded = load_library(path)
    assert len(loaded) == len(REPRESENTATION_LIBRARY)
    assert loaded[0]["id"] == REPRESENTATION_LIBRARY[0]["id"]


def test_all_entries_have_from_to_pattern():
    """Every representation change follows a 'from X to Y' pattern."""
    from scripts.dr90_stage1_representation_library import REPRESENTATION_LIBRARY
    for entry in REPRESENTATION_LIBRARY:
        text = entry["what_representation_changed"].lower()
        assert "from" in text, \
            f"Entry {entry['id']} 'what_representation_changed' doesn't contain 'from'"
        assert "to" in text, \
            f"Entry {entry['id']} 'what_representation_changed' doesn't contain 'to'"


def test_all_entries_describe_what_failed():
    """Every entry describes what previous representation failed."""
    from scripts.dr90_stage1_representation_library import REPRESENTATION_LIBRARY
    for entry in REPRESENTATION_LIBRARY:
        text = entry["what_previous_representation_failed"].lower()
        assert len(text) > 20, \
            f"Entry {entry['id']} 'what_previous_representation_failed' too short"
        # Must describe a limitation of the previous representation
        failure_words = ["could not", "couldn't", "failed", "impossible", "intractable",
                        "cannot", "can't", "no ", "unable", "exponential", "error-prone",
                        "ad hoc", "tedious", "limited", "didn't", "did not",
                        "imperative", "sequential", "manual", "require", "were ",
                        "too many", "couldn", "hard to", "uninformative", "assumed",
                        "is uninformative"]
        has_failure = any(w in text for w in failure_words)
        assert has_failure, \
            f"Entry {entry['id']} doesn't describe a failure in 'what_previous_representation_failed'"


def test_all_entries_describe_new_search():
    """Every entry describes what new search became possible."""
    from scripts.dr90_stage1_representation_library import REPRESENTATION_LIBRARY
    for entry in REPRESENTATION_LIBRARY:
        text = entry["what_new_search_became_possible"]
        assert len(text) > 20, \
            f"Entry {entry['id']} 'what_new_search_became_possible' too short"


def test_analyze_runs():
    """analyze_library runs without crashing."""
    from scripts.dr90_stage1_representation_library import (
        REPRESENTATION_LIBRARY, analyze_library,
    )
    # Should not crash
    analyze_library(REPRESENTATION_LIBRARY)


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
