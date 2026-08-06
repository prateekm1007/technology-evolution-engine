"""Tests for DR-62: BusinessPipeline input validation (cycle 198)."""
import sys
import pytest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from product.business.pipeline import BusinessPipeline


def test_correct_key_produces_blueprints():
    """BusinessPipeline.run({'raw_text': ...}) produces non-empty blueprints."""
    bp = BusinessPipeline()
    result = bp.run({'raw_text': 'graphene supercapacitor with high energy density'})
    assert 'blueprints' in result
    assert len(result['blueprints']) > 0, "Correct key should produce blueprints"


def test_wrong_key_raises_valueerror():
    """BusinessPipeline.run({'text': ...}) raises ValueError, not silent empty result.

    Per DR-62: the old code silently returned empty results when given {'text': ...}
    instead of {'raw_text': ...}. Now it raises loudly.
    """
    bp = BusinessPipeline()
    with pytest.raises(ValueError, match="raw_text"):
        bp.run({'text': 'graphene supercapacitor'})


def test_non_dict_input_raises_valueerror():
    """Non-dict input raises ValueError."""
    bp = BusinessPipeline()
    with pytest.raises(ValueError, match="dict"):
        bp.run("not a dict")


def test_empty_dict_raises_valueerror():
    """Empty dict raises ValueError."""
    bp = BusinessPipeline()
    with pytest.raises(ValueError, match="raw_text"):
        bp.run({})


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
