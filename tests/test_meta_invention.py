"""Tests for meta_invention.py — landscape classification + optimizer selection.

Cycle 218 — auditor's update #8:
  'Instead of learning "grain size → good", the engine should learn
   "this landscape → high interaction → Bayesian search" or
   "landscape → needle → importance sampling." Those transfer.'
"""
import sys
import math
import random
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest


# ============================================================================
# L1 — Landscape classification tests
# ============================================================================

def test_landscape_classifier_distinguishes_smooth_from_needle():
    """Smooth vs needle landscapes get different classifications."""
    from scripts.meta_invention import LandscapeClassifier, LandscapeType

    # Build a smooth landscape: outcomes uniformly distributed 0.5-1.0
    class C: pass
    smooth_cands = []
    for i in range(100):
        c = C()
        c.design_point = {"x": i * 0.01}
        c.predicted_outcome = 0.5 + 0.5 * (i / 100)
        smooth_cands.append(c)

    # Build a needle landscape: 95% produce 0, 5% produce 1.0
    needle_cands = []
    for i in range(100):
        c = C()
        c.design_point = {"x": i * 0.01}
        c.predicted_outcome = 1.0 if i >= 95 else 0.001
        needle_cands.append(c)

    design_vars = [{"name": "x", "bounds": (0.0, 1.0)}]
    clf = LandscapeClassifier()
    smooth_sig = clf.classify(smooth_cands, design_vars)
    needle_sig = clf.classify(needle_cands, design_vars)

    # Smooth landscape should have high nonzero_fraction
    assert smooth_sig.nonzero_fraction > 0.9
    # Needle landscape should have low nonzero_fraction
    assert needle_sig.nonzero_fraction < 0.4


def test_landscape_signature_is_domain_invariant():
    """Landscape signatures describe shape, not physics."""
    from scripts.meta_invention import LandscapeClassifier

    class C: pass
    # Two landscapes with the SAME statistical shape but different domains
    te_cands = []
    bat_cands = []
    for i in range(50):
        c1 = C()
        c1.design_point = {"x": i * 0.01}
        c1.predicted_outcome = 0.001 if i < 40 else 1.0  # needle
        te_cands.append(c1)

        c2 = C()
        c2.design_point = {"y": i * 0.01}
        c2.predicted_outcome = 0.001 if i < 40 else 1.0  # needle
        bat_cands.append(c2)

    clf = LandscapeClassifier()
    design_vars = [{"name": "x", "bounds": (0.0, 1.0)}]
    sig1 = clf.classify(te_cands, design_vars)
    sig2 = clf.classify(bat_cands, [{"name": "y", "bounds": (0.0, 1.0)}])

    # Same landscape shape → same landscape type
    assert sig1.landscape_type == sig2.landscape_type
    assert abs(sig1.nonzero_fraction - sig2.nonzero_fraction) < 0.01


# ============================================================================
# L2 — Optimizer selection tests
# ============================================================================

def test_optimizer_selector_default_mapping():
    """Selector has a default (landscape_type → optimizer) mapping."""
    from scripts.meta_invention import OptimizerSelector, LandscapeType
    from scripts.meta_invention import GreedyHillClimber, ImportanceSampler, BayesianOptimizer, EvolutionarySearch

    sel = OptimizerSelector()
    assert sel.mapping[LandscapeType.SMOOTH] == GreedyHillClimber
    assert sel.mapping[LandscapeType.NEEDLE] == ImportanceSampler
    assert sel.mapping[LandscapeType.DECEPTIVE] == BayesianOptimizer
    assert sel.mapping[LandscapeType.MULTIMODAL] == EvolutionarySearch


def test_optimizer_selector_records_performance():
    """Selector records improvements for meta-learning."""
    from scripts.meta_invention import OptimizerSelector, LandscapeType

    sel = OptimizerSelector()
    sel.record(LandscapeType.NEEDLE, "importance_sampler", +1.5)
    sel.record(LandscapeType.NEEDLE, "importance_sampler", +2.0)
    sel.record(LandscapeType.NEEDLE, "greedy_hill_climber", -0.5)

    key = ("needle", "importance_sampler")
    assert key in sel.performance_log
    assert len(sel.performance_log[key]) == 2


def test_meta_learning_updates_mapping():
    """Meta-learning picks the best-performing optimizer per landscape."""
    from scripts.meta_invention import OptimizerSelector, LandscapeType
    from scripts.meta_invention import ImportanceSampler, GreedyHillClimber

    sel = OptimizerSelector()
    # Override the default to a bad choice
    sel.mapping[LandscapeType.NEEDLE] = GreedyHillClimber
    # Record: importance_sampler wins, greedy loses
    sel.record(LandscapeType.NEEDLE, "importance_sampler", +1.5)
    sel.record(LandscapeType.NEEDLE, "importance_sampler", +2.0)
    sel.record(LandscapeType.NEEDLE, "greedy_hill_climber", -0.5)

    updates = sel.meta_learn()
    assert len(updates) >= 1
    assert sel.mapping[LandscapeType.NEEDLE] == ImportanceSampler


# ============================================================================
# L3 — Operator learning tests
# ============================================================================

def test_operator_logger_records_per_landscape():
    """Operator logger records (operator, landscape) pairs across domains."""
    from scripts.meta_invention import OperatorLogger, LandscapeType, LandscapeSignature
    from scripts.meta_invention import ImportanceSampler, BayesianOptimizer

    logger = OperatorLogger()
    # Fake optimizer objects
    class Opt:
        def __init__(self, name): self.name = name
    class FakeLand:
        def __init__(self, lt): self.landscape_type = LandscapeType(lt)

    logger.log(Opt("importance_sampler"), FakeLand("needle"), "battery", +1.5, 50)
    logger.log(Opt("bayesian_optimizer"), FakeLand("deceptive"), "pv", +2.0, 50)

    summary = logger.summary()
    assert "importance_sampler_needle" in summary
    assert "bayesian_optimizer_deceptive" in summary


# ============================================================================
# L4 — End-to-end meta-invention tests
# ============================================================================

def test_meta_invention_runs_on_all_four_domains():
    """Meta-invention loop runs end-to-end on all 4 domains."""
    from scripts.meta_invention import run_meta_invention
    from scripts.cross_domain_transfer import (
        THERMOELECTRIC_DOMAIN, BATTERY_DOMAIN, CATALYST_DOMAIN, PV_DOMAIN,
        thermoelectric_forward, battery_forward, catalyst_forward, pv_forward,
    )

    cases = [
        (THERMOELECTRIC_DOMAIN, thermoelectric_forward),
        (BATTERY_DOMAIN, battery_forward),
        (CATALYST_DOMAIN, catalyst_forward),
        (PV_DOMAIN, pv_forward),
    ]
    for spec, fn in cases:
        iters, landscape, opt_name = run_meta_invention(
            spec, fn, n_iterations=2, n_per_iter=20, seed=42,
        )
        assert len(iters) == 3  # iter 0 + 2 iterations
        assert landscape.landscape_type.value in [
            "smooth", "multimodal", "needle", "deceptive",
            "constraint_dominated", "unknown"
        ]
        assert opt_name in [
            "greedy_hill_climber", "importance_sampler",
            "bayesian_optimizer", "evolutionary_search",
        ]


def test_bayesian_optimizer_fits_surrogate():
    """BayesianOptimizer fits a quadratic surrogate to candidates."""
    from scripts.meta_invention import BayesianOptimizer
    from scripts.cross_domain_transfer import PV_DOMAIN

    class C: pass
    opt = BayesianOptimizer(PV_DOMAIN)
    # Generate 30 fake candidates
    rng = random.Random(42)
    cands = []
    for _ in range(30):
        c = C()
        c.design_point = {v["name"]: rng.uniform(*v["bounds"]) for v in PV_DOMAIN["design_vars"]}
        # Outcome with strong interaction: bandgap × defects
        Eg = c.design_point["bandgap_eV"]
        Nd = c.design_point["defect_density_cm2"]
        c.predicted_outcome = (1.5 - abs(Eg - 1.2)) * (1 - math.log10(Nd) / 16) * 20
        cands.append(c)

    opt._fit_surrogate(cands)
    assert opt.surrogate_coeffs  # must have fit something
    assert "weights" in opt.surrogate_coeffs
    # Surrogate should predict close to actual for training points
    pred = opt._predict_surrogate(cands[0].design_point)
    assert abs(pred - cands[0].predicted_outcome) < 5.0  # rough fit


def test_importance_sampler_builds_kernel_around_winners():
    """ImportanceSampler builds kernel centers around top candidates."""
    from scripts.meta_invention import ImportanceSampler
    from scripts.cross_domain_transfer import BATTERY_DOMAIN

    class C: pass
    opt = ImportanceSampler(BATTERY_DOMAIN)
    rng = random.Random(42)
    cands = []
    for i in range(50):
        c = C()
        c.design_point = {v["name"]: rng.uniform(*v["bounds"]) for v in BATTERY_DOMAIN["design_vars"]}
        # Top 5 are the "needles"
        c.predicted_outcome = 10.0 if i >= 45 else 0.001
        cands.append(c)

    opt.step(cands, rng)
    assert len(opt.kernel_centers) > 0
    # Kernel centers should be the top candidates (high outcome)
    for kc in opt.kernel_centers:
        # Find the original candidate with this design point
        for c in cands:
            if c.design_point == kc:
                assert c.predicted_outcome == 10.0  # must be a winner
                break


def test_evolutionary_search_generates_offspring():
    """EvolutionarySearch generates offspring via crossover + mutation."""
    from scripts.meta_invention import EvolutionarySearch
    from scripts.cross_domain_transfer import THERMOELECTRIC_DOMAIN

    class C: pass
    opt = EvolutionarySearch(THERMOELECTRIC_DOMAIN, population_size=10)
    rng = random.Random(42)
    cands = []
    for _ in range(50):
        c = C()
        c.design_point = {v["name"]: rng.uniform(*v["bounds"]) for v in THERMOELECTRIC_DOMAIN["design_vars"]}
        c.predicted_outcome = rng.uniform(0, 1)
        cands.append(c)

    opt.step(cands, rng)
    # Policy should be narrowed (not original bounds)
    for vname, (lo, hi) in opt.policy.items():
        orig_lo, orig_hi = opt.original_bounds[vname]
        # Width should be less than original (crossover narrowed it)
        # Allow equal in case all parents had the same value
        assert (hi - lo) <= (orig_hi - orig_lo) + 1e-9


# ============================================================================
# Causal chain tests
# ============================================================================

def test_causal_chain_renders_to_prose():
    """CausalChain renders to human-readable prose."""
    from scripts.meta_invention import CAUSAL_CHAINS

    chain = CAUSAL_CHAINS["pisarenko"]
    prose = chain.to_prose()
    assert "carrier_concentration" in prose
    assert "Pisarenko" in prose
    assert "seebeck_coefficient" in prose
    assert "ZT" in prose


def test_causal_chain_to_dict_includes_formula():
    """CausalChain.to_dict includes formula at each step."""
    from scripts.meta_invention import CAUSAL_CHAINS

    chain = CAUSAL_CHAINS["grain_boundary"]
    d = chain.to_dict()
    assert "steps" in d
    for step in d["steps"]:
        assert "variable" in step
        assert "mechanism" in step
        assert "formula" in step


def test_causal_chain_is_executable():
    """Each step references a named mechanism + formula (auditor's requirement)."""
    from scripts.meta_invention import CAUSAL_CHAINS

    for chain_id, chain in CAUSAL_CHAINS.items():
        assert len(chain.steps) >= 2, f"{chain_id} must have >= 2 steps"
        for step in chain.steps:
            assert step.variable, f"{chain_id}: step variable empty"
            assert step.change, f"{chain_id}: step change empty"
            assert step.mechanism, f"{chain_id}: step mechanism empty"
            assert step.formula, f"{chain_id}: step formula empty"
        # Final step must touch the outcome variable
        assert chain.final_variable == chain.steps[-1].variable


# ============================================================================
# Multi-seed robustness tests
# ============================================================================

def test_meta_invention_robust_across_seeds():
    """FAST smoke test: meta-invention improves on >=3/4 domains across 2 seeds.

    This is the smoke test — quick to run, asserts the minimum bar.
    The full 5-seed × 4-domain 4/4 enforcement is in
    test_meta_invention_full_5seed_4of4 (marked slow).
    """
    from scripts.meta_invention import run_meta_invention
    from scripts.cross_domain_transfer import (
        THERMOELECTRIC_DOMAIN, BATTERY_DOMAIN, CATALYST_DOMAIN, PV_DOMAIN,
        thermoelectric_forward, battery_forward, catalyst_forward, pv_forward,
    )

    cases = [
        ("TE", THERMOELECTRIC_DOMAIN, thermoelectric_forward),
        ("Battery", BATTERY_DOMAIN, battery_forward),
        ("Catalyst", CATALYST_DOMAIN, catalyst_forward),
        ("PV", PV_DOMAIN, pv_forward),
    ]

    # Run with 2 seeds (fast smoke test)
    for seed in [42, 7]:
        n_improved = 0
        for name, spec, fn in cases:
            iters, _, _ = run_meta_invention(
                spec, fn, n_iterations=3, n_per_iter=30, seed=seed,
            )
            delta = iters[-1]["best_outcome"] - iters[0]["best_outcome"]
            if delta > 0:
                n_improved += 1
        assert n_improved >= 3, f"Seed {seed}: only {n_improved}/4 domains improved"


@pytest.mark.slow
def test_meta_invention_full_5seed_4of4():
    """FULL validation: 5 seeds × 4 domains, asserting 4/4 per seed.

    This is the test that backs the claim '20/20 wins across 5 seeds ×
    4 domains'. Anything less than 4/4 per seed fails.

    Marked slow because it runs 5 × 4 = 20 meta-invention loops.
    Skip during normal development with: pytest -m "not slow"
    """
    from scripts.meta_invention import run_meta_invention
    from scripts.cross_domain_transfer import (
        THERMOELECTRIC_DOMAIN, BATTERY_DOMAIN, CATALYST_DOMAIN, PV_DOMAIN,
        thermoelectric_forward, battery_forward, catalyst_forward, pv_forward,
    )

    cases = [
        ("TE", THERMOELECTRIC_DOMAIN, thermoelectric_forward),
        ("Battery", BATTERY_DOMAIN, battery_forward),
        ("Catalyst", CATALYST_DOMAIN, catalyst_forward),
        ("PV", PV_DOMAIN, pv_forward),
    ]

    seeds = [42, 7, 99, 123, 256]
    total_wins = 0
    total_runs = 0
    per_seed_results = {}

    for seed in seeds:
        n_improved = 0
        per_domain_deltas = {}
        for name, spec, fn in cases:
            iters, _, _ = run_meta_invention(
                spec, fn, n_iterations=5, n_per_iter=50, seed=seed,
            )
            delta = iters[-1]["best_outcome"] - iters[0]["best_outcome"]
            per_domain_deltas[name] = delta
            if delta > 0:
                n_improved += 1
                total_wins += 1
            total_runs += 1
        per_seed_results[seed] = (n_improved, per_domain_deltas)
        # Each seed must achieve 4/4
        assert n_improved == 4, \
            f"Seed {seed}: only {n_improved}/4 domains improved. Deltas: {per_domain_deltas}"

    # Final sanity: 20/20 total wins
    assert total_wins == total_runs, \
        f"Expected {total_runs}/{total_runs} wins, got {total_wins}/{total_runs}. " \
        f"Per-seed: {per_seed_results}"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
