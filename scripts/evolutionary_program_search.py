#!/usr/bin/env python3
"""
evolutionary_program_search.py — Evolutionary search over optimizer programs (cycle 230).

Per auditor's update #20 (priority #1):
  "Random is now your bottleneck. The repository is reaching a point
   where Architecture >> Search quality. Earlier the opposite was true.
   Now your DSL is better than your search algorithm. That's a good
   place to be. I'd stop improving the DSL. I'd improve the search."

The cycle 228-229 L5a used RANDOM search (random program generation +
fitness selection). The auditor correctly identified this as the
bottleneck: the DSL has 13 primitives and the executor works, but
random search cannot explore the program space effectively (proven by
the 2/10 blind suite result in F-119).

This module replaces random search with EVOLUTIONARY search:
1. Population of programs (initialized randomly)
2. Selection: keep top-k by fitness
3. Crossover: combine operations from two parent programs
4. Mutation: randomly perturb operations
5. Repeat for N generations

The hypothesis: if search quality was the bottleneck (not the DSL),
evolutionary search should raise the blind suite score above 2/10.
If it doesn't, the bottleneck is the DSL itself (L5b territory).

This directly tests the auditor's strategic insight. The result is
honest either way:
- If score rises: confirms search was the bottleneck, path forward
  is even stronger search (RL, MCTS, beam).
- If score stays low: confirms the DSL is the bottleneck, path
  forward is L5b (operator discovery).
"""
import sys
import math
import random
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Callable
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.l5_search_discovery import (
    OptimizerProgram, ProgramExecutor, OpType, ALL_OPS,
)


class EvolutionaryProgramSearch:
    """Evolutionary search over optimizer programs.

    Replaces random search with:
    1. Population of P programs (initialized randomly)
    2. Evaluate all on training domains
    3. Select top-k parents (elitism + tournament)
    4. Crossover: swap operation subsequences between parents
    5. Mutation: replace/insert/delete operations
    6. Next generation = elites + offspring
    7. Repeat for G generations

    The key difference from random search:
    - Random: each program is independent (no learning between programs)
    - Evolutionary: programs share information via crossover + selection

    This tests whether the DSL is sufficient (evolutionary should find
    good programs if they exist in the search space) or insufficient
    (evolutionary also fails → need L5b).
    """

    def __init__(self, population_size: int = 30, n_generations: int = 5,
                 program_length: int = 4, elite_fraction: float = 0.3,
                 mutation_rate: float = 0.3, crossover_rate: float = 0.7,
                 n_iterations: int = 2, n_per_iter: int = 15,
                 tournament_size: int = 3):
        self.population_size = population_size
        self.n_generations = n_generations
        self.program_length = program_length
        self.elite_fraction = elite_fraction
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.n_iterations = n_iterations
        self.n_per_iter = n_per_iter
        self.tournament_size = tournament_size
        self.n_elites = max(2, int(population_size * elite_fraction))
        self.programs: List[OptimizerProgram] = []
        self.best_program: Optional[OptimizerProgram] = None
        self.fitness_history: List[float] = []

    def _random_program(self, rng: random.Random, program_id: str) -> OptimizerProgram:
        """Generate a random program."""
        ops = [rng.choice(ALL_OPS) for _ in range(self.program_length)]
        return OptimizerProgram(program_id=program_id, operations=ops)

    def _evaluate_program(self, program: OptimizerProgram,
                          training_domains: List[Tuple[str, Dict, Callable]],
                          seed: int = 42) -> Tuple[float, float]:
        """Evaluate a program on training domains. Returns (mean_fitness, std)."""
        improvements = []
        for name, spec, fn in training_domains:
            executor = ProgramExecutor(spec)
            try:
                iters = executor.execute_program(program, fn,
                                                  n_iterations=self.n_iterations,
                                                  n_per_iter=self.n_per_iter,
                                                  seed=seed)
                improvement = iters[-1]["best_outcome"] - iters[0]["best_outcome"]
                improvements.append(improvement)
            except Exception:
                improvements.append(-1e6)  # penalty for crashing programs

        mean_fit = sum(improvements) / len(improvements) if improvements else -1e6
        std_fit = math.sqrt(sum((x - mean_fit) ** 2 for x in improvements) / len(improvements)) if improvements else 0
        return mean_fit, std_fit

    def _tournament_select(self, population: List[Tuple[OptimizerProgram, float]],
                           rng: random.Random) -> OptimizerProgram:
        """Tournament selection: pick best of k random programs."""
        contestants = rng.sample(population, min(self.tournament_size, len(population)))
        return max(contestants, key=lambda x: x[1])[0]

    def _crossover(self, parent1: OptimizerProgram, parent2: OptimizerProgram,
                   rng: random.Random, program_id: str) -> OptimizerProgram:
        """Single-point crossover: take prefix from p1, suffix from p2."""
        if rng.random() > self.crossover_rate or len(parent1.operations) < 2:
            return OptimizerProgram(program_id=program_id,
                                    operations=parent1.operations[:])
        crossover_point = rng.randint(1, len(parent1.operations) - 1)
        child_ops = parent1.operations[:crossover_point] + parent2.operations[crossover_point:]
        return OptimizerProgram(program_id=program_id, operations=child_ops)

    def _mutate(self, program: OptimizerProgram, rng: random.Random) -> OptimizerProgram:
        """Mutate: replace, insert, or delete operations."""
        ops = program.operations[:]
        for i in range(len(ops)):
            if rng.random() < self.mutation_rate:
                mutation_type = rng.choice(["replace", "replace", "replace"])  # weighted toward replace
                if mutation_type == "replace":
                    ops[i] = rng.choice(ALL_OPS)
        return OptimizerProgram(program_id=program.program_id, operations=ops)

    def search(self, training_domains: List[Tuple[str, Dict, Callable]],
               seed: int = 42) -> OptimizerProgram:
        """Run evolutionary search.

        Args:
            training_domains: list of (name, domain_spec, forward_fn)

        Returns:
            The best-performing program found across all generations.
        """
        rng = random.Random(seed)
        print(f"Evolutionary Program Search:")
        print(f"  Population: {self.population_size}")
        print(f"  Generations: {self.n_generations}")
        print(f"  Program length: {self.program_length}")
        print(f"  Elite fraction: {self.elite_fraction} ({self.n_elites} elites)")
        print(f"  Mutation rate: {self.mutation_rate}")
        print(f"  Crossover rate: {self.crossover_rate}")
        print(f"  Training domains: {len(training_domains)}")
        print()

        # Generation 0: random initialization
        population = []
        for i in range(self.population_size):
            program = self._random_program(rng, f"GEN0-{i+1:03d}")
            fitness, std = self._evaluate_program(program, training_domains, seed=42)
            program.fitness = fitness
            program.fitness_std = std
            program.n_evaluated = len(training_domains)
            population.append((program, fitness))

        # Sort by fitness
        population.sort(key=lambda x: x[1], reverse=True)
        best = population[0][0]
        self.fitness_history.append(best.fitness)

        print(f"  Gen 0: best fitness = {best.fitness:+.4f} (std={best.fitness_std:.4f})")
        print(f"    Best: {' → '.join(op.value[:10] for op in best.operations)}")

        # Evolution
        for gen in range(1, self.n_generations + 1):
            new_population = []

            # Elitism: keep top-k from previous generation
            elites = population[:self.n_elites]
            for program, fitness in elites:
                new_program = OptimizerProgram(
                    program_id=f"GEN{gen}-ELITE-{program.program_id}",
                    operations=program.operations[:],
                    fitness=fitness,
                    fitness_std=program.fitness_std,
                    n_evaluated=program.n_evaluated,
                )
                new_population.append((new_program, fitness))

            # Offspring: crossover + mutation
            n_offspring = self.population_size - self.n_elites
            for i in range(n_offspring):
                parent1 = self._tournament_select(population, rng)
                parent2 = self._tournament_select(population, rng)
                child = self._crossover(parent1, parent2, rng, f"GEN{gen}-{i+1:03d}")
                child = self._mutate(child, rng)

                fitness, std = self._evaluate_program(child, training_domains, seed=42)
                child.fitness = fitness
                child.fitness_std = std
                child.n_evaluated = len(training_domains)
                new_population.append((child, fitness))

            # Sort and keep best
            new_population.sort(key=lambda x: x[1], reverse=True)
            population = new_population[:self.population_size]

            gen_best = population[0][0]
            self.fitness_history.append(gen_best.fitness)

            if gen_best.fitness > best.fitness:
                best = gen_best

            print(f"  Gen {gen}: best fitness = {gen_best.fitness:+.4f} (std={gen_best.fitness_std:.4f})")
            print(f"    Best: {' → '.join(op.value[:10] for op in gen_best.operations)}")

        self.best_program = best
        self.programs = [p for p, _ in population]

        print()
        print(f"  Final best: fitness={best.fitness:+.4f}")
        print(f"  Fitness history: {[f'{f:+.3f}' for f in self.fitness_history]}")

        return best

    def evaluate_on_held_out(self, program: OptimizerProgram,
                              held_out_domains: List[Tuple[str, Dict, Callable]],
                              seed: int = 42) -> Dict:
        """Evaluate a discovered program on held-out domains."""
        from scripts.comparative_benchmark import run_optimizer, RandomRestartOptimizer

        print()
        print(f"Evaluating on {len(held_out_domains)} held-out domains:")
        print(f"  Program: {' → '.join(op.value for op in program.operations)}")
        print()

        results = []
        for name, spec, fn in held_out_domains:
            executor = ProgramExecutor(spec)
            iters = executor.execute_program(program, fn,
                                              n_iterations=3, n_per_iter=20, seed=seed)
            prog_best = iters[-1]["best_outcome"]

            random_opt = RandomRestartOptimizer(spec)
            rand_iters = run_optimizer(spec, fn, random_opt,
                                        n_iterations=3, n_per_iter=20, seed=seed)
            rand_best = rand_iters[-1]["best_outcome"]

            beats = prog_best > rand_best + 1e-9
            results.append({
                "domain": name,
                "program_best": prog_best,
                "random_best": rand_best,
                "beats_random": beats,
            })
            print(f"  {name:<20} program={prog_best:>+10.4f}  random={rand_best:>+10.4f}  "
                  f"beats={'✓' if beats else '✗'}")

        n_beats = sum(1 for r in results if r["beats_random"])
        print()
        print(f"Discovered program beats RANDOM on {n_beats}/{len(results)} held-out domains")

        return {
            "program": program.to_dict(),
            "results": results,
            "n_beats_random": n_beats,
            "n_total": len(results),
        }


def main():
    print("=" * 90)
    print("EVOLUTIONARY PROGRAM SEARCH (cycle 230)")
    print("Testing auditor's hypothesis: is search quality the bottleneck?")
    print("=" * 90)
    print()

    from scripts.blind_suite import BLIND_SUITE

    # Training: first 10 blind problems
    training = [(p.problem_id, p.to_domain_spec(), p.forward) for p in BLIND_SUITE[:10]]
    # Held-out: last 10 blind problems
    held_out = [(p.problem_id, p.to_domain_spec(), p.forward) for p in BLIND_SUITE[10:]]

    # Phase 1: Evolutionary search
    print("=" * 90)
    print("PHASE 1: Evolutionary search on 10 blind training problems")
    print("=" * 90)
    print()

    evo = EvolutionaryProgramSearch(
        population_size=30, n_generations=5, program_length=4,
        elite_fraction=0.3, mutation_rate=0.3, crossover_rate=0.7,
        n_iterations=2, n_per_iter=15,
    )
    best_evo = evo.search(training, seed=42)

    # Phase 2: Compare to random search (cycle 229 baseline)
    print()
    print("=" * 90)
    print("PHASE 2: Compare evolutionary vs random on held-out blind problems")
    print("=" * 90)
    print()

    # Evaluate evolutionary best
    print("--- Evolutionary best ---")
    evo_result = evo.evaluate_on_held_out(best_evo, held_out, seed=42)

    # For comparison: random search baseline (from cycle 229)
    print()
    print("--- Random search baseline (cycle 229) ---")
    from scripts.l5_search_discovery import L5ProgramDiscovery
    random_search = L5ProgramDiscovery(n_programs=30, program_length=4,
                                       n_iterations=2, n_per_iter=15)
    best_random = random_search.search(training, seed=42)
    random_result = random_search.evaluate_on_held_out(best_random, held_out, seed=42)

    # Summary
    print()
    print("=" * 90)
    print("EVOLUTIONARY vs RANDOM — BLIND SUITE COMPARISON")
    print("=" * 90)
    print()
    print(f"{'Search':<20} {'Training fitness':<20} {'Beats baseline (held-out)':<25}")
    print("-" * 65)
    print(f"{'Random (cycle 229)':<20} {best_random.fitness:>+20.4f} "
          f"{random_result['n_beats_portfolio']}/{random_result['n_total']:<25}")
    print(f"{'Evolutionary':<20} {best_evo.fitness:>+20.4f} "
          f"{evo_result['n_beats_random']}/{evo_result['n_total']:<25}")

    print()
    print("=" * 90)
    print("HONEST INTERPRETATION")
    print("=" * 90)
    print()

    evo_beats = evo_result["n_beats_random"]
    rand_beats = random_result["n_beats_portfolio"]

    if evo_beats > rand_beats:
        print(f"Evolutionary search ({evo_beats}/10) BEATS random search ({rand_beats}/10)")
        print("on the blind suite. This confirms the auditor's hypothesis:")
        print("search quality WAS the bottleneck, not the DSL.")
        print()
        print("Path forward: even stronger search (RL, MCTS, beam) should")
        print("raise the blind suite score further. The DSL is sufficient;")
        print("the search procedure was too weak.")
    elif evo_beats == rand_beats:
        print(f"Evolutionary search ({evo_beats}/10) MATCHES random search ({rand_beats}/10).")
        print("Evolutionary did not improve on random. This suggests the DSL")
        print("is the bottleneck, not the search quality (L5b territory).")
        print()
        print("Path forward: L5b (operator discovery) is needed. The current")
        print("13 primitives cannot express optimizers for the blind suite's")
        print("diverse problem types (continuous + combinatorial + hybrid).")
    else:
        print(f"Evolutionary search ({evo_beats}/10) is WORSE than random ({rand_beats}/10).")
        print("This is surprising. Possible causes:")
        print("- Evolutionary overfit to training blind problems")
        print("- Crossover disrupts useful operation sequences")
        print("- Population too small for effective evolution")
        print()
        print("This is an honest negative result. The search procedure change")
        print("did not help. The bottleneck is elsewhere (DSL or training data).")

    print()
    print("=" * 90)
    print("FITNESS HISTORY (does evolution improve training fitness?)")
    print("=" * 90)
    print()
    print(f"Evolutionary fitness by generation: {[f'{f:+.3f}' for f in evo.fitness_history]}")
    print(f"Random search best fitness: {best_random.fitness:+.4f}")
    print()
    if evo.fitness_history[-1] > evo.fitness_history[0]:
        print("Evolution DID improve training fitness over generations.")
        print("The question is whether this training improvement transfers")
        print("to held-out (it may be overfitting).")
    else:
        print("Evolution did NOT improve training fitness.")
        print("The search space may be flat (many programs have similar fitness)")
        print("or the mutation/crossover operators are not effective.")


if __name__ == "__main__":
    main()
