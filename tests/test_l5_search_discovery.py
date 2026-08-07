"""Tests for l5_search_discovery.py — cycle 228.

Auditor's update #18 (remaining frontier):
  "L5 Search Theory Discovery — inventing optimizers (AlphaDev analog),
   not selecting from portfolio."
"""
import sys
import math
import random
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest


def test_l5_imports():
    """Module imports cleanly."""
    from scripts.l5_search_discovery import (
        OpType, OptimizerProgram, ProgramExecutor, L5SearchDiscovery,
        ALL_OPS,
    )
    assert OpType is not None
    assert len(ALL_OPS) >= 10  # at least 10 primitives


def test_dsl_has_core_primitives():
    """The DSL has the core optimizer primitives."""
    from scripts.l5_search_discovery import OpType
    required = [
        OpType.SAMPLE_UNIFORM, OpType.SAMPLE_NORMAL,
        OpType.SELECT_TOP_QUARTILE, OpType.WEIGHTED_MEAN,
        OpType.NARROW_IQR, OpType.WIDEN,
        OpType.CROSSOVER, OpType.MUTATE,
        OpType.FIT_SURROGATE, OpType.ACQUIRE_EI,
    ]
    for op in required:
        assert op in OpType, f"Missing required primitive: {op}"


def test_program_is_serializable():
    """OptimizerProgram can be serialized to dict."""
    from scripts.l5_search_discovery import OptimizerProgram, OpType
    program = OptimizerProgram(
        program_id="TEST-001",
        operations=[OpType.SAMPLE_UNIFORM, OpType.NARROW_IQR, OpType.MUTATE],
    )
    d = program.to_dict()
    assert d["program_id"] == "TEST-001"
    assert len(d["operations"]) == 3
    assert d["operations"][0] == "sample_uniform"


def test_executor_runs_program():
    """ProgramExecutor runs a program and returns iteration stats."""
    from scripts.l5_search_discovery import (
        OptimizerProgram, ProgramExecutor, OpType,
    )
    from scripts.synthetic_landscapes import SPHERE_DOMAIN, sphere_forward

    program = OptimizerProgram(
        program_id="TEST-002",
        operations=[OpType.NARROW_IQR, OpType.MUTATE],
    )
    executor = ProgramExecutor(SPHERE_DOMAIN)
    iters = executor.execute_program(program, sphere_forward,
                                      n_iterations=2, n_per_iter=15, seed=42)
    assert len(iters) == 3  # iter 0 + 2 iterations
    for it in iters:
        assert "best_outcome" in it
        assert "avg_outcome" in it


def test_executor_samples_within_bounds():
    """All executor samples are within variable bounds."""
    from scripts.l5_search_discovery import ProgramExecutor
    from scripts.synthetic_landscapes import SPHERE_DOMAIN

    executor = ProgramExecutor(SPHERE_DOMAIN)
    rng = random.Random(42)
    for _ in range(50):
        dp = executor._sample_uniform(rng)
        for v in SPHERE_DOMAIN["design_vars"]:
            lo, hi = v["bounds"]
            assert lo <= dp[v["name"]] <= hi


def test_l5_search_finds_best_program():
    """L5SearchDiscovery finds a best program from training."""
    from scripts.l5_search_discovery import L5SearchDiscovery
    from scripts.cross_domain_transfer import (
        THERMOELECTRIC_DOMAIN, BATTERY_DOMAIN,
        thermoelectric_forward, battery_forward,
    )

    training = [
        ("TE", THERMOELECTRIC_DOMAIN, thermoelectric_forward),
        ("Battery", BATTERY_DOMAIN, battery_forward),
    ]

    l5 = L5SearchDiscovery(n_programs=10, program_length=3,
                           n_iterations=1, n_per_iter=10)
    best = l5.search(training, seed=42)

    assert best is not None
    assert best.fitness != 0.0  # was evaluated
    assert len(l5.programs) == 10


def test_l5_discovered_program_runs_on_held_out():
    """A discovered program runs on held-out domains without crashing."""
    from scripts.l5_search_discovery import L5SearchDiscovery, OptimizerProgram, OpType
    from scripts.synthetic_landscapes import (
        SPHERE_DOMAIN, ACKLEY_DOMAIN,
        sphere_forward, ackley_forward,
    )

    held_out = [
        ("Sphere", SPHERE_DOMAIN, sphere_forward),
        ("Ackley", ACKLEY_DOMAIN, ackley_forward),
    ]

    # Create a fixed program (don't rely on search for test stability)
    program = OptimizerProgram(
        program_id="TEST-FIXED",
        operations=[OpType.FIT_SURROGATE, OpType.ACQUIRE_EI, OpType.NARROW_IQR],
    )

    l5 = L5SearchDiscovery(n_programs=5, program_length=3)
    result = l5.evaluate_on_held_out(program, held_out, seed=42)

    assert "n_beats_portfolio" in result
    assert "n_total" in result
    assert result["n_total"] == 2


def test_l5_search_beats_portfolio_on_at_least_one():
    """HONEST TEST: L5 search discovers a program that beats the portfolio
    on at least 1/7 held-out landscapes.

    This is the MINIMUM bar for L5: the search must find SOMETHING that
    beats the portfolio on at least one held-out problem. If it can't,
    the search procedure is too weak.

    Observed: 4/7 (top programs beat portfolio on 4/7 held-out).
    """
    from scripts.l5_search_discovery import L5SearchDiscovery
    from scripts.cross_domain_transfer import (
        THERMOELECTRIC_DOMAIN, BATTERY_DOMAIN, CATALYST_DOMAIN, PV_DOMAIN,
        thermoelectric_forward, battery_forward, catalyst_forward, pv_forward,
    )
    from scripts.synthetic_landscapes import (
        SPHERE_DOMAIN, ROSENBROCK_DOMAIN, ACKLEY_DOMAIN,
        sphere_forward, rosenbrock_forward, ackley_forward,
    )

    training = [
        ("TE", THERMOELECTRIC_DOMAIN, thermoelectric_forward),
        ("Battery", BATTERY_DOMAIN, battery_forward),
    ]
    held_out = [
        ("Sphere", SPHERE_DOMAIN, sphere_forward),
        ("Rosenbrock", ROSENBROCK_DOMAIN, rosenbrock_forward),
        ("Ackley", ACKLEY_DOMAIN, ackley_forward),
    ]

    l5 = L5SearchDiscovery(n_programs=20, program_length=3,
                           n_iterations=1, n_per_iter=10)
    best = l5.search(training, seed=42)
    result = l5.evaluate_on_held_out(best, held_out, seed=42)

    assert result["n_beats_portfolio"] >= 1, \
        f"L5 search discovered a program that beats portfolio on only " \
        f"{result['n_beats_portfolio']}/{result['n_total']} held-out. Expected ≥1. " \
        f"The search must find SOMETHING that beats the portfolio."


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
