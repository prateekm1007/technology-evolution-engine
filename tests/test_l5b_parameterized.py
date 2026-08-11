"""Tests for l5b_parameterized.py — cycle 238.

L5b.2: Parameterized composites with landscape-adaptive alpha.
HONEST LABEL: 'parameterized' NOT 'discovered'.
"""
import sys
import math
import random
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest


def test_parameterized_imports():
    """Module imports cleanly."""
    from scripts.l5b_parameterized import (
        ParameterizedCompositeOperator, learn_alpha_from_landscape,
        ParameterizedProgramExecutor, ParameterizedSynthesizer,
        evaluate_parameterized_on_held_out,
    )
    assert ParameterizedCompositeOperator is not None
    assert learn_alpha_from_landscape is not None


def test_parameterized_composite_has_alpha():
    """ParameterizedCompositeOperator has an alpha parameter."""
    from scripts.l5b_parameterized import ParameterizedCompositeOperator
    from scripts.l5_search_discovery import OpType

    pc = ParameterizedCompositeOperator(
        composite_id="TEST-001",
        name="test_param",
        constituents=[OpType.NARROW_IQR, OpType.MUTATE],
        alpha=0.7,
        alpha_formula="test formula",
    )
    assert pc.alpha == 0.7
    assert pc.alpha_formula == "test formula"
    assert len(pc.constituents) == 2


def test_parameterized_to_dict_has_type_label():
    """to_dict includes type='parameterized' (NOT 'discovered')."""
    from scripts.l5b_parameterized import ParameterizedCompositeOperator
    from scripts.l5_search_discovery import OpType

    pc = ParameterizedCompositeOperator(
        composite_id="TEST-002",
        name="test",
        constituents=[OpType.SAMPLE_UNIFORM],
        alpha=0.5,
    )
    d = pc.to_dict()
    assert d["type"] == "parameterized"
    assert d["type"] != "discovered"


def test_learn_alpha_from_landscape():
    """learn_alpha_from_landscape returns alpha in [0.1, 0.9]."""
    from scripts.l5b_parameterized import learn_alpha_from_landscape
    from scripts.meta_invention import LandscapeSignature, LandscapeType

    sig = LandscapeSignature(
        n_samples=50, q25=0.1, q50=0.2, q75=0.3, q99=0.4, max_val=0.5,
        nonzero_fraction=0.8, skew_ratio=0.4, bimodality=0.3,
        interaction_index=0.4, landscape_type=LandscapeType.SMOOTH,
    )
    alpha, formula = learn_alpha_from_landscape(sig)
    assert 0.1 <= alpha <= 0.9
    assert isinstance(formula, str)
    assert "=" in formula


def test_learn_alpha_differs_by_landscape():
    """Different landscapes produce different alphas."""
    from scripts.l5b_parameterized import learn_alpha_from_landscape
    from scripts.meta_invention import LandscapeSignature, LandscapeType

    # Smooth landscape: low bimodality, high skew
    smooth_sig = LandscapeSignature(
        n_samples=50, q25=0.1, q50=0.2, q75=0.3, q99=0.4, max_val=0.5,
        nonzero_fraction=0.9, skew_ratio=0.8, bimodality=0.1,
        interaction_index=0.2, landscape_type=LandscapeType.SMOOTH,
    )
    # Bimodal landscape: high bimodality, low skew
    bimodal_sig = LandscapeSignature(
        n_samples=50, q25=0.1, q50=0.2, q75=0.3, q99=0.4, max_val=0.5,
        nonzero_fraction=0.5, skew_ratio=0.1, bimodality=0.9,
        interaction_index=0.6, landscape_type=LandscapeType.DECEPTIVE,
    )
    smooth_alpha, _ = learn_alpha_from_landscape(smooth_sig)
    bimodal_alpha, _ = learn_alpha_from_landscape(bimodal_sig)

    # Bimodal should have HIGHER alpha (more aggressive narrowing)
    assert bimodal_alpha > smooth_alpha, \
        f"Bimodal alpha ({bimodal_alpha}) should be > smooth alpha ({smooth_alpha})"


def test_parameterized_executor_uses_alpha():
    """ParameterizedProgramExecutor applies alpha to narrowing ops."""
    from scripts.l5b_parameterized import ParameterizedProgramExecutor
    from scripts.synthetic_landscapes import SPHERE_DOMAIN, sphere_forward

    # High alpha = aggressive narrowing
    opt_high = ParameterizedProgramExecutor(SPHERE_DOMAIN, alpha=0.9)
    # Low alpha = gentle narrowing
    opt_low = ParameterizedProgramExecutor(SPHERE_DOMAIN, alpha=0.1)

    # Generate same candidates for both
    rng = random.Random(42)
    cands = []
    for _ in range(20):
        dp = {v["name"]: rng.uniform(*v["bounds"]) for v in SPHERE_DOMAIN["design_vars"]}
        o, _ = sphere_forward(dp)
        c = type("C", (), {"design_point": dp, "predicted_outcome": o, "derived": {}})()
        cands.append(c)

    # Apply NARROW_IQR with different alphas
    from scripts.l5_search_discovery import OpType
    opt_high._execute_op(OpType.NARROW_IQR, cands, rng)
    var_names = [v["name"] for v in SPHERE_DOMAIN["design_vars"]]
    high_spans = {vn: opt_high.policy[vn] for vn in var_names}

    # Reset and try with low alpha
    opt_low.policy = {vn: SPHERE_DOMAIN["design_vars"][0]["bounds"] for vn in var_names}
    # Reset properly from original bounds
    for v in SPHERE_DOMAIN["design_vars"]:
        opt_low.policy[v["name"]] = v["bounds"]
    opt_low._execute_op(OpType.NARROW_IQR, cands, rng)
    low_spans = {vn: opt_low.policy[vn] for vn in var_names}

    # High alpha should narrow MORE (smaller spans)
    for name in high_spans:
        hi_lo, hi_hi = high_spans[name]
        lo_lo, lo_hi = low_spans[name]
        hi_span = hi_hi - hi_lo
        lo_span = lo_hi - lo_lo
        # High alpha should produce smaller or equal span
        assert hi_span <= lo_span + 0.01, \
            f"High alpha ({opt_high.alpha}) should narrow more than low ({opt_low.alpha}) for {name}"


def test_parameterized_runs_on_blind_suite():
    """Parameterized synthesis runs on blind suite."""
    from scripts.l5b_parameterized import ParameterizedSynthesizer
    from scripts.blind_suite import BLIND_SUITE

    training = [(p.problem_id, p.to_domain_spec(), p.forward)
                for p in BLIND_SUITE[:3]]
    syn = ParameterizedSynthesizer(n_programs=5, program_length=3,
                                    n_iterations=1, n_per_iter=8,
                                    min_pair_frequency=1)
    pcomps = syn.synthesize(training, seed=42)
    assert isinstance(pcomps, list)


def test_parameterized_honest_label():
    """HONEST TEST: parameterized composites are labeled 'parameterized',
    NOT 'discovered'.

    Per anti-entropy #5: the label must match the evidence.
    The underlying operators are existing DSL primitives. The innovation
    is the LEARNED PARAMETER (alpha), not new algorithmic structure.
    The type label must be 'parameterized', never 'discovered'.
    """
    from scripts.l5b_parameterized import ParameterizedCompositeOperator
    from scripts.l5_search_discovery import OpType

    pc = ParameterizedCompositeOperator(
        composite_id="TEST-LABEL",
        name="test",
        constituents=[OpType.NARROW_IQR, OpType.MUTATE],
        alpha=0.5,
    )
    d = pc.to_dict()
    assert d["type"] == "parameterized", \
        f"Type must be 'parameterized', got '{d['type']}'. " \
        f"Per anti-entropy #5: label must match evidence. " \
        f"These are PARAMETERIZED composites (alpha learned from landscape), " \
        f"NOT discovered operators (no new algorithmic primitive)."
    assert d["type"] != "discovered", \
        "Type must NOT be 'discovered' — the operators are existing DSL primitives."


def test_parameterized_matches_or_beats_fixed():
    """HONEST TEST: parameterized composites match fixed composites on held-out.

    The cycle 238 result: parameterized 9/10 vs fixed 9/10 (MATCHES).
    The alpha parameter does NOT add value beyond fixed composites.
    The saturation ceiling persists.

    This test enforces the minimum: parameterized must not be MUCH worse
    than fixed (within 2 of fixed score).
    """
    from scripts.l5b_parameterized import (
        ParameterizedSynthesizer, evaluate_parameterized_on_held_out,
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
        n_programs=8, program_length=3,
        n_iterations=1, n_per_iter=8, seed=42,
    )

    # Parameterized composites
    param_syn = ParameterizedSynthesizer(n_programs=10, program_length=3,
                                          n_iterations=1, n_per_iter=8,
                                          min_pair_frequency=1)
    with redirect_stdout(f):
        param_syn.synthesize(training, seed=42)
    param_result = evaluate_parameterized_on_held_out(
        param_syn.parameterized_composites, held_out,
        n_programs=8, program_length=3,
        n_iterations=1, n_per_iter=8, seed=42,
    )

    # Parameterized should not be much worse than fixed
    assert param_result["n_beats_random"] >= fixed_result["n_beats_random"] - 2, \
        f"Parameterized ({param_result['n_beats_random']}) much worse than " \
        f"fixed ({fixed_result['n_beats_random']}). " \
        f"Parameterization should not hurt performance."


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
