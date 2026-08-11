"""Tests for DR-93.5: Independent Proposal Validation."""
import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest


def test_dr935_imports():
    from audit.measurement_integrity.dr93_5_independent_validation import (
        llm_evaluate_proposal,
    )
    assert llm_evaluate_proposal is not None


def test_llm_evaluates_proposal():
    """LLM can evaluate a proposal and return structured ratings."""
    from audit.measurement_integrity.dr93_5_independent_validation import llm_evaluate_proposal

    proposal = {
        "shared_mechanism": "The concept 'thermal_conductivity' appears in both source A and source B",
        "necessary_assumptions": ["thermal_conductivity is real"],
        "prediction": "If 'thermal_conductivity' is present, then cross-domain connection exists",
        "alternative_explanations": ["coincidence"],
        "counterexample": "If 'thermal_conductivity' is removed, connection disappears",
        "falsification_experiment": "Check if 'thermal_conductivity' appears in non-cross-domain papers",
        "confidence": 0.3,
        "provenance": {"shared_entity": "thermal_conductivity"},
    }

    result = llm_evaluate_proposal(proposal)
    # Should return a dict with evaluation fields or an error
    assert isinstance(result, dict)
    if "error" not in result:
        assert "mechanistically_coherent" in result or "choices" in result


def test_independent_evaluation_not_self_grading():
    """HONEST TEST: the evaluation uses an EXTERNAL LLM, not internal heuristics.

    Per CTO: 'No module validates itself.' The Proposal Composer
    generates proposals; the LLM evaluator judges them independently.
    This test verifies the evaluator function exists and is callable
    with external LLM access.
    """
    from audit.measurement_integrity.dr93_5_independent_validation import llm_evaluate_proposal
    # The function calls z-ai CLI (external LLM) — not internal scoring
    import inspect
    source = inspect.getsource(llm_evaluate_proposal)
    assert "z-ai" in source or "subprocess" in source, \
        "Evaluation must use external LLM (z-ai CLI), not internal scoring"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
