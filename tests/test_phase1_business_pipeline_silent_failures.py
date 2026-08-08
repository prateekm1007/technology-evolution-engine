"""Tests for Phase 1 (Amendment directive): BusinessPipeline silent-failure elimination.

These tests verify that the pipeline raises loudly on every silent-failure
pattern identified in the Phase 1 audit, rather than producing zero-valued
reports that look like valid negative results.
"""
import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from product.business.pipeline import BusinessPipeline
from product.retrieval.graph_retriever import GraphRetriever


# ===== Phase 1: empty raw_text rejected =====

def test_empty_raw_text_raises():
    """Empty raw_text must raise, not silently produce a zero-valued report."""
    bp = BusinessPipeline()
    with pytest.raises(ValueError, match="non-empty string 'raw_text'"):
        bp.run({'raw_text': ''})


def test_whitespace_only_raw_text_raises():
    """Whitespace-only raw_text must raise for the same reason."""
    bp = BusinessPipeline()
    with pytest.raises(ValueError, match="non-empty string 'raw_text'"):
        bp.run({'raw_text': '   \n\t  '})


def test_non_string_raw_text_raises():
    """Non-string raw_text (e.g. None, int) must raise."""
    bp = BusinessPipeline()
    with pytest.raises(ValueError, match="non-empty string 'raw_text'"):
        bp.run({'raw_text': None})
    with pytest.raises(ValueError, match="non-empty string 'raw_text'"):
        bp.run({'raw_text': 12345})


# ===== Phase 1: parser empty extraction rejected =====

def test_parser_empty_extraction_raises():
    """If the parser extracts nothing (no components/materials/claims, <10 words),
    the pipeline must raise rather than produce a zero-valued report."""
    bp = BusinessPipeline()
    # A very short input that the parser will extract nothing from
    with pytest.raises(ValueError, match="Parser returned empty extraction"):
        bp.run({'raw_text': 'short'})


# ===== Phase 1: retriever graph load error surfaced =====

def test_retriever_graph_missing_records_error():
    """If the graph file is missing, retriever.load_error must be set
    (not silently swallowed)."""
    r = GraphRetriever(graph_path='/nonexistent/path/graph.json')
    err = r.load_error
    assert err is not None, "Missing graph file should set load_error"
    assert 'not found' in err.lower() or 'no such file' in err.lower()


def test_retriever_graph_corrupt_records_error():
    """If the graph file is corrupt JSON, retriever.load_error must be set."""
    import tempfile, os
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('{"nodes": {, "invalid json"}')
        path = f.name
    try:
        r = GraphRetriever(graph_path=path)
        err = r.load_error
        assert err is not None, "Corrupt JSON should set load_error"
        assert 'corrupt' in err.lower() or 'json' in err.lower()
    finally:
        os.unlink(path)


def test_retriever_result_includes_graph_load_error_field():
    """The retriever.run() result includes 'graph_load_error' field so
    callers can detect silent graph failures."""
    r = GraphRetriever(graph_path='/nonexistent/path/graph.json')
    result = r.run({'components': ['sensor'], 'materials': [], 'methods': []})
    assert 'graph_load_error' in result
    assert result['graph_load_error'] is not None


# ===== Phase 1: stage output contract checks =====

def test_stage_output_non_dict_raises():
    """If a stage returns a non-dict, the pipeline must raise TypeError."""
    bp = BusinessPipeline()
    # Monkey-patch parser.run to return None (simulating internal crash)
    bp.parser.run = lambda d: None
    with pytest.raises(TypeError, match="Stage 'parser' returned NoneType"):
        bp.run({'raw_text': 'graphene supercapacitor with high energy density'})


def test_stage_output_missing_required_key_raises():
    """If a stage returns a dict missing required keys, the pipeline
    must raise KeyError."""
    bp = BusinessPipeline()
    # Monkey-patch parser.run to return an incomplete dict
    bp.parser.run = lambda d: {'patent_id': 'X'}  # missing word_count, components
    with pytest.raises(KeyError, match="missing required keys"):
        bp.run({'raw_text': 'graphene supercapacitor with high energy density'})


# ===== Phase 1: permuter silent failure rejected =====

def test_permuter_zero_candidates_raises():
    """If the permuter generates 0 candidates despite non-empty parser
    output, the pipeline must raise (silent permuter failure)."""
    bp = BusinessPipeline()
    # Monkey-patch permuter.run to return 0 candidates
    bp.permuter.run = lambda d: {
        'total_generated': 0, 'total_scored': 0, 'candidates': [],
        'adjacency_map': {}, 'cemetery_matches': [], 'prerequisite_gaps': [],
    }
    with pytest.raises(RuntimeError, match="Permuter generated 0 candidates"):
        bp.run({'raw_text': 'graphene supercapacitor with high energy density'})


# ===== Phase 1: empty graph rejected at pipeline level =====

def test_pipeline_rejects_empty_graph():
    """If the graph has 0 nodes (load failure or genuinely empty),
    the pipeline must raise rather than produce a zero-valued report."""
    bp = BusinessPipeline(graph_path='/nonexistent/path/graph.json')
    with pytest.raises(RuntimeError, match="Retriever searched 0 graph nodes"):
        bp.run({'raw_text': 'graphene supercapacitor with high energy density'})


# ===== Phase 1: regression — valid input still works =====

def test_valid_input_still_produces_report():
    """A valid input must still produce a non-empty report. This is the
    regression test ensuring Phase 1 didn't break the happy path."""
    bp = BusinessPipeline()
    result = bp.run({'raw_text': 'graphene supercapacitor with high energy density'})
    assert 'report_id' in result
    assert result['report_type'] == 'business'
    assert 'epistemic_status' in result


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
