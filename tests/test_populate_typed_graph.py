"""Tests for populate_typed_graph.py — Representation 7→9."""
import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.populate_typed_graph import (
    categorize_predicate,
    PREDICATE_CATEGORIES,
    populate_typed_edges,
)


def test_categorize_predicate_causal():
    """Causal predicates are categorized correctly."""
    assert categorize_predicate("causes") == "causal"
    assert categorize_predicate("produces") == "causal"
    assert categorize_predicate("generates") == "causal"
    assert categorize_predicate("triggers") == "causal"


def test_categorize_predicate_enabling():
    """Enabling predicates are categorized correctly."""
    assert categorize_predicate("enables") == "enabling"
    assert categorize_predicate("facilitates") == "enabling"
    assert categorize_predicate("allows") == "enabling"


def test_categorize_predicate_modulating():
    """Modulating predicates are categorized correctly."""
    assert categorize_predicate("increases") == "modulating"
    assert categorize_predicate("decreases") == "modulating"
    assert categorize_predicate("reduces") == "modulating"
    assert categorize_predicate("inhibits") == "modulating"


def test_categorize_predicate_determining():
    """Determining predicates are categorized correctly."""
    assert categorize_predicate("determines") == "determining"
    assert categorize_predicate("governs") == "determining"
    assert categorize_predicate("controls") == "determining"


def test_categorize_predicate_characterizing():
    """Characterizing predicates are categorized correctly."""
    assert categorize_predicate("exhibits") == "characterizing"
    assert categorize_predicate("shows") == "characterizing"
    assert categorize_predicate("displays") == "characterizing"


def test_categorize_predicate_unknown():
    """Unknown predicates return 'unknown'."""
    assert categorize_predicate("purple") == "unknown"
    assert categorize_predicate("hello") == "unknown"


def test_categorize_predicate_case_insensitive():
    """Categorization is case-insensitive."""
    assert categorize_predicate("CAUSES") == "causal"
    assert categorize_predicate("Enables") == "enabling"
    assert categorize_predicate("INCREASES") == "modulating"


def test_predicate_categories_covers_5_gentner_groups():
    """All 5 Gentner predicate groups are represented."""
    categories_seen = set(PREDICATE_CATEGORIES.values())
    expected = {"causal", "enabling", "modulating", "determining", "characterizing"}
    assert expected.issubset(categories_seen), \
        f"Missing categories: {expected - categories_seen}"


def test_populate_typed_edges_dry_run():
    """populate_typed_edges runs in dry-run mode without modifying the graph."""
    # Use a temporary graph file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({"nodes": [], "edges": []}, f)
        tmp_path = f.name

    try:
        with patch('scripts.populate_typed_graph.GRAPH_PATH', Path(tmp_path)):
            stats = populate_typed_edges(dry_run=True)
            # Should return a stats dict
            assert isinstance(stats, dict)
            assert "nodes_added" in stats
            assert "edges_added" in stats
            assert "edges_by_category" in stats

            # The original graph file should NOT be modified in dry-run
            with open(tmp_path) as f:
                content = json.load(f)
            assert content == {"nodes": [], "edges": []}, \
                "Dry-run should not modify the graph"
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def test_populate_typed_edges_returns_category_distribution():
    """The returned stats include edges_by_category distribution."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({"nodes": [], "edges": []}, f)
        tmp_path = f.name

    try:
        with patch('scripts.populate_typed_graph.GRAPH_PATH', Path(tmp_path)):
            stats = populate_typed_edges(dry_run=True)
            assert isinstance(stats["edges_by_category"], dict)
    finally:
        Path(tmp_path).unlink(missing_ok=True)


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
