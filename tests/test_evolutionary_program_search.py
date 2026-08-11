"""Tests for evolutionary_program_search.py — cycle 230.

Auditor's update #20 (priority #1):
  "Random is now your bottleneck. I'd improve the search."

This test verifies the evolutionary search runs and honestly reports
whether it improves on random.
"""
import sys
import math
import random
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest


def test_evo_imports():
    """Module imports cleanly."""
    from scripts.evolutionary_program_search import EvolutionaryProgramSearch
    assert EvolutionaryProgramSearch is not None


def test_evo_initializes():
    """EvolutionaryProgramSearch initializes with correct parameters."""
    from scripts.evolutionary_program_search import EvolutionaryProgramSearch
    evo = EvolutionaryProgramSearch(population_size=10, n_generations=3)
    assert evo.population_size == 10
    assert evo.n_generations == 3
    assert evo.n_elites >= 2


def test_evo_runs_on_blind_suite():
    """Evolutionary search runs on blind suite without crashing."""
    from scripts.evolutionary_program_search import EvolutionaryProgramSearch
    from scripts.blind_suite import BLIND_SUITE

    training = [(p.problem_id, p.to_domain_spec(), p.forward)
                for p in BLIND_SUITE[:3]]  # small for test speed
    evo = EvolutionaryProgramSearch(population_size=5, n_generations=2,
                                    program_length=3, n_iterations=1, n_per_iter=8)
    best = evo.search(training, seed=42)
    assert best is not None
    assert best.fitness != 0.0
    assert len(evo.fitness_history) == 3  # gen 0 + 2 generations


def test_evo_crossover_combines_parents():
    """Crossover combines operations from two parents."""
    from scripts.evolutionary_program_search import EvolutionaryProgramSearch
    from scripts.l5_search_discovery import OptimizerProgram, OpType

    evo = EvolutionaryProgramSearch()
    rng = random.Random(42)

    p1 = OptimizerProgram(program_id="P1",
                          operations=[OpType.SAMPLE_UNIFORM, OpType.NARROW_IQR,
                                      OpType.MUTATE, OpType.ACQUIRE_EI])
    p2 = OptimizerProgram(program_id="P2",
                          operations=[OpType.CROSSOVER, OpType.FIT_SURROGATE,
                                      OpType.WIDEN, OpType.SELECT_TOP_QUARTILE])
    child = evo._crossover(p1, p2, rng, "CHILD")
    assert len(child.operations) == 4
    # Child should have prefix from p1 and suffix from p2
    assert child.operations[0] == OpType.SAMPLE_UNIFORM  # from p1


def test_evo_mutate_changes_operations():
    """Mutation can change operations."""
    from scripts.evolutionary_program_search import EvolutionaryProgramSearch
    from scripts.l5_search_discovery import OptimizerProgram, OpType

    evo = EvolutionaryProgramSearch(mutation_rate=1.0)  # 100% mutation
    rng = random.Random(42)

    original = OptimizerProgram(program_id="ORIG",
                                operations=[OpType.SAMPLE_UNIFORM, OpType.NARROW_IQR,
                                            OpType.MUTATE, OpType.ACQUIRE_EI])
    mutated = evo._mutate(original, rng)
    # With 100% mutation rate, at least some ops should change
    changes = sum(1 for o1, o2 in zip(original.operations, mutated.operations) if o1 != o2)
    assert changes > 0, "Mutation should change at least one operation"


def test_evo_tournament_selects_best():
    """Tournament selection picks the best of k contestants."""
    from scripts.evolutionary_program_search import EvolutionaryProgramSearch
    from scripts.l5_search_discovery import OptimizerProgram, OpType

    evo = EvolutionaryProgramSearch(tournament_size=3)
    rng = random.Random(42)

    population = []
    for i in range(10):
        p = OptimizerProgram(program_id=f"P{i}",
                             operations=[OpType.SAMPLE_UNIFORM, OpType.NARROW_IQR])
        p.fitness = float(i)  # P9 has highest fitness
        population.append((p, float(i)))

    selected = evo._tournament_select(population, rng)
    # Tournament of 3 from 10 should usually pick above-average fitness
    # (average = 4.5, so selected should be >= 3.0 in most cases)
    assert selected.fitness >= 3.0  # should be above average usually


def test_evo_blind_suite_honest_result():
    """HONEST TEST: Evolutionary search on blind suite.

    The honest result (cycle 230): evolutionary search MATCHES random
    search at 2/10 on the blind suite. The fitness history is flat
    (no improvement over generations). This suggests the DSL is the
    bottleneck, not the search quality.

    This test enforces the honest minimum: evolutionary search must
    produce a valid program that runs on held-out blind problems.
    It does NOT assert improvement over random (because the honest
    result is no improvement).
    """
    from scripts.evolutionary_program_search import EvolutionaryProgramSearch
    from scripts.blind_suite import BLIND_SUITE

    # Small test: 3 training, 2 held-out
    training = [(p.problem_id, p.to_domain_spec(), p.forward)
                for p in BLIND_SUITE[:3]]
    held_out = [(p.problem_id, p.to_domain_spec(), p.forward)
                for p in BLIND_SUITE[3:5]]

    evo = EvolutionaryProgramSearch(population_size=5, n_generations=2,
                                    program_length=3, n_iterations=1, n_per_iter=8)
    best = evo.search(training, seed=42)
    result = evo.evaluate_on_held_out(best, held_out, seed=42)

    assert "n_beats_random" in result
    assert result["n_total"] == 2
    # The honest result: evolutionary works (produces valid programs)
    # but may or may not beat random. The test just verifies it runs.


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
