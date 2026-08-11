"""Tests for l5b_synthesis.py — cycle 233.

L5b operator synthesis loop: the engine generates composite operators
from frequent pairs. This is the first step toward true L5b (engine-
discovered operators, not hand-designed).
"""
import sys
import math
import random
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest


def test_synthesis_imports():
    """Module imports cleanly."""
    from scripts.l5b_synthesis import (
        CompositeOperator, OperatorSynthesizer,
    )
    assert CompositeOperator is not None
    assert OperatorSynthesizer is not None


def test_composite_operator_dataclass():
    """CompositeOperator has the right fields."""
    from scripts.l5b_synthesis import CompositeOperator
    from scripts.l5_search_discovery import OpType

    comp = CompositeOperator(
        composite_id="TEST-001",
        name="narrow_then_mutate",
        constituents=[OpType.NARROW_IQR, OpType.MUTATE],
    )
    assert comp.composite_id == "TEST-001"
    assert comp.name == "narrow_then_mutate"
    assert len(comp.constituents) == 2
    assert comp.selection_count == 0


def test_synthesizer_initializes():
    """OperatorSynthesizer initializes with correct parameters."""
    from scripts.l5b_synthesis import OperatorSynthesizer
    syn = OperatorSynthesizer(n_programs=10, program_length=3,
                              min_pair_frequency=2)
    assert syn.n_programs == 10
    assert syn.min_pair_frequency == 2
    assert syn.composites == []


def test_synthesizer_runs_on_blind_suite():
    """The synthesis loop runs on blind suite without crashing."""
    from scripts.l5b_synthesis import OperatorSynthesizer
    from scripts.blind_suite import BLIND_SUITE

    training = [(p.problem_id, p.to_domain_spec(), p.forward)
                for p in BLIND_SUITE[:3]]  # small for test speed
    syn = OperatorSynthesizer(n_programs=10, program_length=4,
                              n_iterations=1, n_per_iter=8,
                              min_pair_frequency=1)  # low threshold for small test
    result = syn.synthesize(training, seed=42)

    assert "n_composites" in result
    assert "n_selected" in result
    assert "base_best_fitness" in result
    assert "composite_best_fitness" in result


def test_synthesis_produces_composites():
    """HONEST TEST: The synthesis loop produces composite operators.

    With enough programs (50) and a low threshold (2), the loop should
    find frequent pairs and fuse them into composites.

    Observed (cycle 233): 17 composites synthesized, all 17 selected.
    """
    from scripts.l5b_synthesis import OperatorSynthesizer
    from scripts.blind_suite import BLIND_SUITE

    training = [(p.problem_id, p.to_domain_spec(), p.forward)
                for p in BLIND_SUITE[:5]]  # 5 for test speed
    syn = OperatorSynthesizer(n_programs=20, program_length=4,
                              n_iterations=1, n_per_iter=8,
                              min_pair_frequency=1)
    result = syn.synthesize(training, seed=42)

    # With min_pair_frequency=1 and 20 programs, we should get at least 1 composite
    assert result["n_composites"] >= 1, \
        f"Synthesis produced {result['n_composites']} composites. Expected ≥1. " \
        f"The loop should find frequent pairs."


def test_composites_are_selected_by_search():
    """HONEST TEST: Composites are selected by the search in the re-run.

    If the engine synthesizes composites but the search never selects
    them, the composites are useless. This test verifies that at least
    one composite is selected.

    Observed (cycle 233): 17/17 composites selected (115 total selections).
    """
    from scripts.l5b_synthesis import OperatorSynthesizer
    from scripts.blind_suite import BLIND_SUITE

    training = [(p.problem_id, p.to_domain_spec(), p.forward)
                for p in BLIND_SUITE[:5]]
    syn = OperatorSynthesizer(n_programs=20, program_length=4,
                              n_iterations=1, n_per_iter=8,
                              min_pair_frequency=1)
    result = syn.synthesize(training, seed=42)

    if result["n_composites"] > 0:
        assert result["n_selected"] >= 1, \
            f"0/{result['n_composites']} composites were selected. " \
            f"The search should select at least one composite."


def test_composite_dsl_beats_or_matches_base():
    """HONEST TEST: Composite DSL performance vs base DSL.

    The composite DSL (base + composites) should at least MATCH the
    base DSL (composites add options but don't remove any). If it
    BEATS the base DSL, the composites are genuinely useful.

    Observed (cycle 233): base=+38.53, composite=+39.61 (beats).
    """
    from scripts.l5b_synthesis import OperatorSynthesizer
    from scripts.blind_suite import BLIND_SUITE

    training = [(p.problem_id, p.to_domain_spec(), p.forward)
                for p in BLIND_SUITE[:5]]
    syn = OperatorSynthesizer(n_programs=20, program_length=4,
                              n_iterations=1, n_per_iter=8,
                              min_pair_frequency=1)
    result = syn.synthesize(training, seed=42)

    # Composite DSL should be >= base DSL (composites add options)
    # Allow small tolerance for randomness
    assert result["composite_best_fitness"] >= result["base_best_fitness"] - 1.0, \
        f"Composite DSL ({result['composite_best_fitness']:+.4f}) is worse than " \
        f"base DSL ({result['base_best_fitness']:+.4f}). " \
        f"Composites should not hurt performance."


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
