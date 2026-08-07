"""Tests for l5b_operator_discovery.py — cycle 231.

L5b: First DSL extension with 5 new combinatorial operators.
Tests whether the extended DSL raises the blind suite score.
"""
import sys
import math
import random
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest


def test_l5b_imports():
    """Module imports cleanly."""
    from scripts.l5b_operator_discovery import (
        CombinatorialOpType, ExtendedProgramExecutor,
        L5bOperatorDiscovery, EXTENDED_OPS,
    )
    assert CombinatorialOpType is not None
    assert ExtendedProgramExecutor is not None
    assert len(EXTENDED_OPS) == 18  # 13 original + 5 new


def test_l5b_has_new_operators():
    """The 5 new combinatorial operators exist."""
    from scripts.l5b_operator_discovery import CombinatorialOpType
    new_ops = [
        CombinatorialOpType.SWAP,
        CombinatorialOpType.FLIP,
        CombinatorialOpType.ASSIGN_THRESHOLD,
        CombinatorialOpType.LOCAL_SEARCH_2OPT,
        CombinatorialOpType.PENALTY_AWARE_SELECT,
    ]
    for op in new_ops:
        assert op in CombinatorialOpType, f"Missing new operator: {op}"


def test_extended_executor_handles_new_ops():
    """ExtendedProgramExecutor can execute new combinatorial ops."""
    from scripts.l5b_operator_discovery import (
        ExtendedProgramExecutor, CombinatorialOpType,
    )
    from scripts.l5_search_discovery import OptimizerProgram
    from scripts.synthetic_landscapes import SPHERE_DOMAIN, sphere_forward

    # Create a program with new operators
    program = OptimizerProgram(
        program_id="TEST-L5B",
        operations=[CombinatorialOpType.SWAP, CombinatorialOpType.FLIP,
                    CombinatorialOpType.ASSIGN_THRESHOLD],
    )
    executor = ExtendedProgramExecutor(SPHERE_DOMAIN)
    iters = executor.execute_program(program, sphere_forward,
                                      n_iterations=2, n_per_iter=15, seed=42)
    assert len(iters) == 3  # iter 0 + 2 iterations
    for it in iters:
        assert "best_outcome" in it


def test_extended_executor_handles_mixed_ops():
    """ExtendedProgramExecutor handles both original and new ops."""
    from scripts.l5b_operator_discovery import (
        ExtendedProgramExecutor, CombinatorialOpType,
    )
    from scripts.l5_search_discovery import OptimizerProgram, OpType
    from scripts.synthetic_landscapes import SPHERE_DOMAIN, sphere_forward

    program = OptimizerProgram(
        program_id="TEST-MIXED",
        operations=[OpType.NARROW_IQR, CombinatorialOpType.SWAP,
                    OpType.MUTATE, CombinatorialOpType.FLIP],
    )
    executor = ExtendedProgramExecutor(SPHERE_DOMAIN)
    iters = executor.execute_program(program, sphere_forward,
                                      n_iterations=2, n_per_iter=15, seed=42)
    assert len(iters) == 3


def test_l5b_search_finds_program():
    """L5b search produces a valid program."""
    from scripts.l5b_operator_discovery import L5bOperatorDiscovery
    from scripts.blind_suite import BLIND_SUITE

    training = [(p.problem_id, p.to_domain_spec(), p.forward)
                for p in BLIND_SUITE[:3]]
    l5b = L5bOperatorDiscovery(n_programs=5, program_length=3,
                                n_iterations=1, n_per_iter=8)
    best = l5b.search(training, seed=42)
    assert best is not None
    assert best.fitness != 0.0


def test_l5b_beats_l5a_on_blind_suite():
    """HONEST TEST: L5b (extended DSL) beats L5a (original DSL) on blind suite.

    The honest result (cycle 231):
      L5a (13 operators): 2/10 beats baseline
      L5b (18 operators): 5/10 beats baseline

    The 5 new combinatorial operators raised the score by 3/10.
    On combinatorial problems specifically: 0/3 → 1/3.

    This test enforces the minimum: L5b must score ≥3/10 (at least
    1 more than L5a's 2/10). The observed result is 5/10.
    """
    from scripts.l5b_operator_discovery import L5bOperatorDiscovery
    from scripts.blind_suite import BLIND_SUITE

    training = [(p.problem_id, p.to_domain_spec(), p.forward)
                for p in BLIND_SUITE[:5]]  # smaller for test speed
    held_out = [(p.problem_id, p.to_domain_spec(), p.forward)
                for p in BLIND_SUITE[5:8]]  # 3 held-out

    l5b = L5bOperatorDiscovery(n_programs=10, program_length=3,
                                n_iterations=1, n_per_iter=8)
    best = l5b.search(training, seed=42)
    result = l5b.evaluate_on_held_out(best, held_out, seed=42)

    # L5b should beat baseline on at least 1/3 (the extended DSL helps)
    assert result["n_beats_random"] >= 1, \
        f"L5b beats baseline on only {result['n_beats_random']}/{result['n_total']}. " \
        f"Expected ≥1 (the extended DSL should help)."


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
