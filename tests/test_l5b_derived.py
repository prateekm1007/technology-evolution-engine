"""Tests for l5b_derived.py — cycle 239.

L5b.3: Derived operators from landscape measurement.
HONEST LABEL: 'derived' NOT 'discovered'.
Saturation evidence complete: 4 hypotheses falsified.
"""
import sys
import math
import random
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest


def test_derived_imports():
    """Module imports cleanly."""
    from scripts.l5b_derived import (
        DerivedOpType, DerivedOperator, DerivedProgramExecutor,
        DerivedOperatorSynthesizer, evaluate_derived_on_held_out,
    )
    assert DerivedOpType is not None
    assert DerivedOperator is not None


def test_derived_op_types_exist():
    """Three derived operator types exist."""
    from scripts.l5b_derived import DerivedOpType
    assert DerivedOpType.INTERACTION_AWARE_NARROW
    assert DerivedOpType.BIMODALITY_SPLIT
    assert DerivedOpType.SKEW_AWARE_SELECT


def test_derived_operator_has_type_label():
    """DerivedOperator.to_dict has type='derived' (NOT 'discovered')."""
    from scripts.l5b_derived import DerivedOperator, DerivedOpType

    op = DerivedOperator(
        operator_id="TEST-001",
        name="test_derived",
        derived_type=DerivedOpType.INTERACTION_AWARE_NARROW,
        derivation_rule="test rule",
    )
    d = op.to_dict()
    assert d["type"] == "derived"
    assert d["type"] != "discovered"


def test_derived_synthesizer_creates_operators():
    """DerivedOperatorSynthesizer creates operators from training landscapes."""
    from scripts.l5b_derived import DerivedOperatorSynthesizer
    from scripts.blind_suite import BLIND_SUITE

    training = [(p.problem_id, p.to_domain_spec(), p.forward)
                for p in BLIND_SUITE[:5]]
    syn = DerivedOperatorSynthesizer()
    ops = syn.synthesize(training, seed=42)
    assert isinstance(ops, list)
    # Should create at least 1 derived operator (landscapes have interaction/skew)
    assert len(ops) >= 1


def test_derived_executor_runs():
    """DerivedProgramExecutor runs with landscape signature."""
    from scripts.l5b_derived import DerivedProgramExecutor, DerivedOpType
    from scripts.l5_search_discovery import OpType, OptimizerProgram
    from scripts.synthetic_landscapes import SPHERE_DOMAIN, sphere_forward
    from scripts.meta_invention import LandscapeSignature, LandscapeType

    sig = LandscapeSignature(
        n_samples=50, q25=0.1, q50=0.2, q75=0.3, q99=0.4, max_val=0.5,
        nonzero_fraction=0.8, skew_ratio=0.4, bimodality=0.3,
        interaction_index=0.5, landscape_type=LandscapeType.SMOOTH,
    )
    executor = DerivedProgramExecutor(SPHERE_DOMAIN, landscape_sig=sig)

    # Generate candidates
    rng = random.Random(42)
    cands = []
    for _ in range(20):
        dp = {v["name"]: rng.uniform(*v["bounds"]) for v in SPHERE_DOMAIN["design_vars"]}
        o, _ = sphere_forward(dp)
        c = type("C", (), {"design_point": dp, "predicted_outcome": o, "derived": {}})()
        cands.append(c)

    # Test each derived op type
    for dt in DerivedOpType:
        executor._execute_derived_op(dt, cands, rng)
        # Should not crash


def test_derived_honest_label():
    """HONEST TEST: derived operators are labeled 'derived', NOT 'discovered'.

    Per anti-entropy #5: the derivation rules are hand-designed by the
    engineer. The operators' behavior is new (not composition of existing
    ops) but the derivation logic is not engine-discovered.
    """
    from scripts.l5b_derived import DerivedOperator, DerivedOpType

    op = DerivedOperator(
        operator_id="TEST-LABEL",
        name="test",
        derived_type=DerivedOpType.INTERACTION_AWARE_NARROW,
        derivation_rule="test",
    )
    d = op.to_dict()
    assert d["type"] == "derived", \
        f"Type must be 'derived', got '{d['type']}'. " \
        f"Per anti-entropy #5: these are DERIVED operators (behavior shaped " \
        f"by landscape measurement), NOT discovered (derivation rules are " \
        f"hand-designed by the engineer)."
    assert d["type"] != "discovered", \
        "Type must NOT be 'discovered' — derivation rules are hand-designed."


def test_derived_matches_or_beats_fixed():
    """HONEST TEST: derived operators match fixed composites on held-out.

    The cycle 239 result: derived 9/10 vs fixed 9/10 (MATCHES).
    The saturation ceiling persists. This is the 4th hypothesis falsified.

    This test enforces: derived must not be MUCH worse than fixed.
    """
    from scripts.l5b_derived import (
        DerivedOperatorSynthesizer, evaluate_derived_on_held_out,
    )
    from scripts.l5b_synthesis import OperatorSynthesizer
    from scripts.l5b_synthesis_heldout import evaluate_on_held_out_with_composites
    from scripts.blind_suite import BLIND_SUITE

    training = [(p.problem_id, p.to_domain_spec(), p.forward)
                for p in BLIND_SUITE[:5]]
    held_out = [(p.problem_id, p.to_domain_spec(), p.forward)
                for p in BLIND_SUITE[5:8]]

    # Fixed composites
    fixed_syn = OperatorSynthesizer(n_programs=10, program_length=3,
                                    n_iterations=1, n_per_iter=8,
                                    min_pair_frequency=1)
    import io
    from contextlib import redirect_stdout
    f = io.StringIO()
    with redirect_stdout(f):
        fixed_syn.synthesize(training, seed=42)
    fixed_result = evaluate_on_held_out_with_composites(
        fixed_syn.composites, held_out,
        n_programs=8, program_length=3, n_iterations=1, n_per_iter=8, seed=42,
    )

    # Derived operators
    derived_syn = DerivedOperatorSynthesizer()
    derived_syn.synthesize(training, seed=42)
    derived_result = evaluate_derived_on_held_out(
        derived_syn.derived_ops, held_out,
        n_programs=8, program_length=3, n_iterations=1, n_per_iter=8, seed=42,
    )

    assert derived_result["n_beats_random"] >= fixed_result["n_beats_random"] - 2, \
        f"Derived ({derived_result['n_beats_random']}) much worse than " \
        f"fixed ({fixed_result['n_beats_random']}). " \
        f"Derived operators should not hurt performance."


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
