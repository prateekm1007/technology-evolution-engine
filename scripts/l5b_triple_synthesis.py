#!/usr/bin/env python3
"""
l5b_triple_synthesis.py — L5b triple composites (cycle 236).

Per auditor's directive (post-235):
  "Option 1 (closest to current code): Extend synthesis to TRIPLES —
   CompositeOperator of 3 operators, or composite-of-composite.
   Source already notes 'future: triples' (l5b_synthesis.py:89).
   Build it; test if triple-composite improves over pair on held-out;
   if not, document the negative (honest)."

THE SCIENTIFIC QUESTION:
Does deeper composition (triples) help over pairs?

- If YES: triples beat pairs on held-out → deeper composition is
  valuable, and the synthesis loop should be extended to arbitrary
  depth.
- If NO: triples don't help → pair-level composition is sufficient,
  and deeper composition is either unnecessary or requires a different
  approach (e.g., parameterized, not just longer sequences).

HONEST EXPECTATION:
Triples may or may not help. The cycle 235 result (8.6/10 with pairs)
is already strong. Triples add expressive power but also add search
space complexity — the program space grows, making it harder for
random search to find good programs. The net effect is unknown.

APPROACH:
1. Run pair synthesis (cycle 235 baseline) → get pair composites
2. Analyze TRIPLES of operators that co-occur in high-fitness programs
   (using the same pair-frequency method, but for 3-grams)
3. Fuse frequent triples into TripleCompositeOperators
4. Evaluate triple-enhanced DSL on held-out blind suite
5. Compare: pairs-only (8.6/10) vs triples ( ?/10)

The key design choice: triples are FUSED 3-ops, not composite-of-
composite. A TripleCompositeOperator runs 3 ops in sequence when
referenced. This is the simplest extension — no recursion needed.
"""
import sys
import math
import random
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Callable, Any
from pathlib import Path
from collections import defaultdict, Counter

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.l5_search_discovery import (
    OpType, OptimizerProgram, ProgramExecutor, ALL_OPS,
)
from scripts.l5b_operator_discovery import (
    CombinatorialOpType, ExtendedProgramExecutor, EXTENDED_OPS,
)
from scripts.l5b_synthesis import CompositeOperator, OperatorSynthesizer
from scripts.l5b_synthesis_heldout import evaluate_on_held_out_with_composites
from scripts.blind_suite import BLIND_SUITE


# ============================================================================
# TRIPLE COMPOSITE OPERATOR
# ============================================================================

@dataclass
class TripleCompositeOperator:
    """A composite operator created by FUSING THREE existing operators.

    Extends CompositeOperator (pairs) to triples. When a program
    references this composite, the executor runs all three constituents
    in sequence.

    Example:
      TripleCompositeOperator("narrow_mutate_acquire",
          [NARROW_IQR, MUTATE, ACQUIRE_EI])
      → runs NARROW_IQR → MUTATE → ACQUIRE_EI

    This is the simplest extension of pair synthesis to triples.
    No recursion — just 3-ops-in-a-row as a named subroutine.
    """
    composite_id: str          # e.g., "TRIPLE-001"
    name: str                  # human-readable name
    constituents: List[Any]    # list of 3 OpType or CombinatorialOpType
    selection_count: int = 0
    fitness_when_selected: float = 0.0

    def to_composite_operator(self) -> CompositeOperator:
        """Convert to a CompositeOperator for compatibility with existing
        evaluate_on_held_out_with_composites."""
        return CompositeOperator(
            composite_id=self.composite_id,
            name=self.name,
            constituents=self.constituents,
            selection_count=self.selection_count,
            fitness_when_selected=self.fitness_when_selected,
        )


# ============================================================================
# TRIPLE SYNTHESIZER
# ============================================================================

class TripleSynthesizer:
    """Synthesizes triple composites from frequent 3-grams.

    Same approach as OperatorSynthesizer but for 3-operator sequences
    instead of 2-operator pairs.
    """

    def __init__(self, n_programs: int = 50, program_length: int = 5,
                 n_iterations: int = 2, n_per_iter: int = 15,
                 min_triple_frequency: int = 2):
        self.n_programs = n_programs
        self.program_length = program_length
        self.n_iterations = n_iterations
        self.n_per_iter = n_per_iter
        self.min_triple_frequency = min_triple_frequency
        self.triples: List[TripleCompositeOperator] = []
        self.triple_frequency: Dict[Tuple, int] = defaultdict(int)
        self.triple_fitness: Dict[Tuple, List[float]] = defaultdict(list)

    def _run_program_discovery(self, ops: List, training_domains: List,
                                seed: int = 42) -> List[Tuple[OptimizerProgram, float]]:
        """Run random program discovery."""
        rng = random.Random(seed)
        results = []
        for i in range(self.n_programs):
            ops_seq = [rng.choice(ops) for _ in range(self.program_length)]
            program = OptimizerProgram(program_id=f"TRI-{i+1:03d}", operations=ops_seq)

            improvements = []
            for name, spec, fn in training_domains:
                executor = ExtendedProgramExecutor(spec)
                try:
                    iters = executor.execute_program(program, fn,
                                                      n_iterations=self.n_iterations,
                                                      n_per_iter=self.n_per_iter,
                                                      seed=42)
                    imp = iters[-1]["best_outcome"] - iters[0]["best_outcome"]
                    improvements.append(imp)
                except Exception:
                    improvements.append(-1e6)

            program.fitness = sum(improvements) / len(improvements) if improvements else -1e6
            results.append((program, program.fitness))
        return results

    def _analyze_triples(self, results: List[Tuple[OptimizerProgram, float]]):
        """Find operator triples that co-occur in high-fitness programs."""
        self.triple_frequency.clear()
        self.triple_fitness.clear()

        sorted_results = sorted(results, key=lambda x: x[1], reverse=True)
        top_half = sorted_results[:max(5, len(sorted_results) // 2)]

        for program, fitness in top_half:
            ops = program.operations
            for i in range(len(ops) - 2):
                triple = (ops[i], ops[i + 1], ops[i + 2])
                self.triple_frequency[triple] += 1
                self.triple_fitness[triple].append(fitness)

    def _synthesize_triples(self) -> List[TripleCompositeOperator]:
        """Fuse frequent triples into TripleCompositeOperators."""
        new_triples = []
        for triple, count in self.triple_frequency.items():
            if count >= self.min_triple_frequency:
                avg_fitness = sum(self.triple_fitness[triple]) / len(self.triple_fitness[triple])
                op1, op2, op3 = triple
                name = f"{op1.value}_then_{op2.value}_then_{op3.value}"
                # Shorten name if too long
                if len(name) > 60:
                    name = name[:57] + "..."
                triple_comp = TripleCompositeOperator(
                    composite_id=f"TRIPLE-{len(self.triples) + len(new_triples) + 1:03d}",
                    name=name,
                    constituents=[op1, op2, op3],
                    fitness_when_selected=avg_fitness,
                )
                new_triples.append(triple_comp)
        return new_triples

    def synthesize(self, training_domains: List[Tuple[str, Dict, Callable]],
                   seed: int = 42) -> List[TripleCompositeOperator]:
        """Run triple synthesis loop."""
        import io
        from contextlib import redirect_stdout
        f = io.StringIO()
        with redirect_stdout(f):
            # Phase 1: Run program discovery
            base_results = self._run_program_discovery(EXTENDED_OPS, training_domains, seed)

            # Phase 2: Analyze triples
            self._analyze_triples(base_results)

            # Phase 3: Synthesize triples
            new_triples = self._synthesize_triples()
            self.triples.extend(new_triples)

        return new_triples


# ============================================================================
# HELD-OUT EVALUATION WITH TRIPLES
# ============================================================================

def evaluate_triples_on_held_out(triples: List[TripleCompositeOperator],
                                  held_out_domains: List[Tuple[str, Dict, Callable]],
                                  n_programs: int = 20,
                                  program_length: int = 4,
                                  n_iterations: int = 2,
                                  n_per_iter: int = 12,
                                  seed: int = 42) -> Dict:
    """Evaluate triple-enhanced DSL on held-out problems.

    The triple DSL = 18 base ops + N triple composites.
    Each triple composite expands to 3 ops at execution time.
    """
    # Convert triples to CompositeOperator for compatibility
    composites = [t.to_composite_operator() for t in triples]

    return evaluate_on_held_out_with_composites(
        composites, held_out_domains,
        n_programs=n_programs,
        program_length=program_length,
        n_iterations=n_iterations,
        n_per_iter=n_per_iter,
        seed=seed,
    )


# ============================================================================
# MULTI-SEED TRIPLE EVALUATION
# ============================================================================

def run_multiseed_triple_heldout(training, held_out, seeds=[42, 7, 99, 123, 256],
                                   n_programs=20, program_length=4,
                                   n_iterations=2, n_per_iter=12,
                                   synth_n_programs=30, synth_program_length=5,
                                   min_triple_frequency=2):
    """Run triple synthesis + held-out across multiple seeds."""
    results = []

    for seed in seeds:
        # Synthesize triples
        syn = TripleSynthesizer(
            n_programs=synth_n_programs,
            program_length=synth_program_length,
            n_iterations=n_iterations,
            n_per_iter=n_per_iter,
            min_triple_frequency=min_triple_frequency,
        )
        triples = syn.synthesize(training, seed=seed)

        if not triples:
            results.append({
                "seed": seed,
                "n_triples": 0,
                "n_beats": 0,
                "n_total": len(held_out),
            })
            continue

        # Reset selection counts
        for t in triples:
            t.selection_count = 0

        # Evaluate on held-out
        held_out_result = evaluate_triples_on_held_out(
            triples, held_out,
            n_programs=n_programs,
            program_length=program_length,
            n_iterations=n_iterations,
            n_per_iter=n_per_iter,
            seed=seed,
        )

        n_beats = held_out_result["n_beats_random"]

        results.append({
            "seed": seed,
            "n_triples": len(triples),
            "n_beats": n_beats,
            "n_total": held_out_result["n_total"],
        })

    return results


def main():
    print("=" * 90)
    print("L5b TRIPLE SYNTHESIS (cycle 236)")
    print("Does deeper composition (triples) help over pairs?")
    print("=" * 90)
    print()

    training = [(p.problem_id, p.to_domain_spec(), p.forward) for p in BLIND_SUITE[:10]]
    held_out = [(p.problem_id, p.to_domain_spec(), p.forward) for p in BLIND_SUITE[10:]]

    # Phase 1: Synthesize triples (single seed first for inspection)
    print("=" * 90)
    print("PHASE 1: Synthesize triples on training (seed=42)")
    print("=" * 90)
    print()

    syn = TripleSynthesizer(
        n_programs=50, program_length=5,
        n_iterations=2, n_per_iter=15,
        min_triple_frequency=1,  # lower threshold — triples are rarer than pairs
    )
    triples = syn.synthesize(training, seed=42)

    print(f"Triples synthesized: {len(triples)}")
    for t in triples[:10]:
        ops_str = " → ".join(op.value[:12] for op in t.constituents)
        print(f"  {t.composite_id}: {ops_str} (avg_fit={t.fitness_when_selected:+.4f})")
    if len(triples) > 10:
        print(f"  ... and {len(triples) - 10} more")
    print()

    if not triples:
        print("No triples synthesized (threshold too high).")
        print("This is an honest result — triple frequency was too low.")
        return

    # Phase 2: Evaluate triples on held-out (single seed)
    print("=" * 90)
    print("PHASE 2: Evaluate triple DSL on held-out (seed=42)")
    print("=" * 90)
    print()

    # Reset counts
    for t in triples:
        t.selection_count = 0

    held_out_result = evaluate_triples_on_held_out(
        triples, held_out,
        n_programs=20, program_length=4,
        n_iterations=2, n_per_iter=12, seed=42,
    )

    print(f"Triple DSL beats RANDOM on {held_out_result['n_beats_random']}/{held_out_result['n_total']} held-out")
    print()

    # Phase 3: Multi-seed comparison (pairs vs triples)
    print("=" * 90)
    print("PHASE 3: Multi-seed comparison — pairs (cycle 235) vs triples (cycle 236)")
    print("=" * 90)
    print()

    # Run pair synthesis multi-seed (for fair comparison)
    from scripts.l5b_synthesis_multiseed import run_multiseed_synthesis_heldout
    pair_results = run_multiseed_synthesis_heldout(
        training, held_out, seeds=[42, 7, 99, 123, 256],
        n_programs=20, program_length=4,
        n_iterations=2, n_per_iter=12,
        synth_n_programs=30, synth_program_length=5,
        min_pair_frequency=2,
    )

    # Run triple synthesis multi-seed
    triple_results = run_multiseed_triple_heldout(
        training, held_out, seeds=[42, 7, 99, 123, 256],
        n_programs=20, program_length=4,
        n_iterations=2, n_per_iter=12,
        synth_n_programs=30, synth_program_length=5,
        min_triple_frequency=1,  # lowered — triples are rarer
    )

    # Summary
    print()
    print("=" * 90)
    print("PAIRS vs TRIPLES — MULTI-SEED HELD-OUT COMPARISON")
    print("=" * 90)
    print()
    print(f"{'Seed':<8} {'Pairs beats':<15} {'Triples beats':<15} {'Triples n':<12}")
    print("-" * 55)
    for p, t in zip(pair_results, triple_results):
        p_beats = p["n_beats"]
        t_beats = t["n_beats"]
        t_n = t["n_triples"]
        print(f"{p['seed']:<8} {p_beats}/{p['n_total']:<15} {t_beats}/{t['n_total']:<15} {t_n:<12}")

    pair_beats = [r["n_beats"] for r in pair_results]
    triple_beats = [r["n_beats"] for r in triple_results]
    pair_mean = sum(pair_beats) / len(pair_beats) if pair_beats else 0
    triple_mean = sum(triple_beats) / len(triple_beats) if triple_beats else 0

    if len(pair_beats) > 1:
        pair_std = math.sqrt(sum((b - pair_mean) ** 2 for b in pair_beats) / len(pair_beats))
    else:
        pair_std = 0
    if len(triple_beats) > 1:
        triple_std = math.sqrt(sum((b - triple_mean) ** 2 for b in triple_beats) / len(triple_beats))
    else:
        triple_std = 0

    print()
    print(f"Pairs mean:   {pair_mean:.1f}/10 (std={pair_std:.2f})")
    print(f"Triples mean: {triple_mean:.1f}/10 (std={triple_std:.2f})")
    print()

    print("=" * 90)
    print("HONEST INTERPRETATION")
    print("=" * 90)
    print()

    if triple_mean > pair_mean + 0.5:
        print(f"TRIPLES BEAT PAIRS: {triple_mean:.1f} vs {pair_mean:.1f}")
        print("Deeper composition helps! Triples outperform pairs on held-out.")
        print("The synthesis loop should be extended to arbitrary depth.")
    elif triple_mean >= pair_mean - 0.5:
        print(f"TRIPLES MATCH PAIRS: {triple_mean:.1f} vs {pair_mean:.1f}")
        print("Deeper composition does NOT help. Triples perform the same as pairs.")
        print()
        print("Honest assessment: pair-level synthesis is sufficient. The extra")
        print("expressive power of triples is offset by the larger search space.")
        print("The bottleneck is NOT composition depth — it's elsewhere (operator")
        print("quality, search procedure, or DSL expressiveness).")
    else:
        print(f"TRIPLES WORSE THAN PAIRS: {triple_mean:.1f} vs {pair_mean:.1f}")
        print("Deeper composition HURTS. Triples perform worse than pairs.")
        print()
        print("Honest negative result: the larger search space from triples makes")
        print("it harder for random search to find good programs. Pair-level is")
        print("the optimal composition depth for this DSL and search budget.")

    print()
    print("Triples synthesized per seed:", [r["n_triples"] for r in triple_results])


if __name__ == "__main__":
    main()
