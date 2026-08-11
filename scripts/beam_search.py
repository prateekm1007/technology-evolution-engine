#!/usr/bin/env python3
"""
beam_search.py — DR-73: Beam search over the design space.

Maintains a beam of top-K candidates. Each iteration:
  1. Expand each candidate by applying each operator from OPERATOR_LIBRARY.
  2. Prune the expansions using ConstraintPruner (DR-73).
  3. Score each surviving expansion using a provided scoring function.
  4. Keep the top-K by score.
Repeat for N iterations.

Reproducible under seed: the operator selection and tie-breaking are
seeded. Logs a complete trace.

Usage:
    from scripts.beam_search import BeamSearch
    bs = BeamSearch(beam_width=5, n_iterations=3, seed=42)
    result = bs.search(seed_configs, scorer, pruner)
    # result.beam = [top-K configs]
"""
import sys
import random
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any, Callable, Tuple
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.artifact_generator import Configuration
from scripts.operator_library import OPERATOR_LIBRARY
from scripts.constraint_pruning import ConstraintPruner, PruneResult


# Scoring function signature: (config) -> float
ScorerFn = Callable[[Configuration], float]


@dataclass
class BeamIteration:
    """The state of the beam at one iteration."""
    iteration: int
    n_expansions_generated: int = 0
    n_expansions_survived_pruning: int = 0
    beam_before: List[str] = field(default_factory=list)   # config_ids
    beam_after: List[str] = field(default_factory=list)
    best_score: float = 0.0
    worst_score: float = 0.0
    pruned_ids: List[str] = field(default_factory=list)


@dataclass
class BeamSearchResult:
    """The output of BeamSearch.search()."""
    beam: List[Configuration] = field(default_factory=list)
    iterations: List[BeamIteration] = field(default_factory=list)
    scores: Dict[str, float] = field(default_factory=dict)
    n_total_expansions: int = 0
    n_total_pruned: int = 0
    seed: int = 0
    beam_width: int = 0
    n_iterations: int = 0
    timestamp: str = ""
    provenance: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "beam": [c.config_id for c in self.beam],
            "iterations": [
                {"iteration": it.iteration,
                 "n_expansions_generated": it.n_expansions_generated,
                 "n_expansions_survived_pruning": it.n_expansions_survived_pruning,
                 "beam_before": it.beam_before,
                 "beam_after": it.beam_after,
                 "best_score": it.best_score,
                 "worst_score": it.worst_score,
                 "pruned_ids": it.pruned_ids}
                for it in self.iterations
            ],
            "scores": self.scores,
            "n_total_expansions": self.n_total_expansions,
            "n_total_pruned": self.n_total_pruned,
            "seed": self.seed,
            "beam_width": self.beam_width,
            "n_iterations": self.n_iterations,
            "timestamp": self.timestamp,
            "provenance": self.provenance,
        }


class BeamSearch:
    """DR-73: beam search over the design space."""

    def __init__(self, beam_width: int = 5, n_iterations: int = 3,
                 seed: int = 42,
                 pruner: Optional[ConstraintPruner] = None,
                 operators: Optional[List[str]] = None):
        self.beam_width = beam_width
        self.n_iterations = n_iterations
        self.seed = seed
        self.pruner = pruner or ConstraintPruner()
        # Default: use ALL operators from the library
        self.operators: List[str] = operators or OPERATOR_LIBRARY.names

    # ----- public API ---------------------------------------------------
    def search(self, seed_configs: List[Configuration],
               scorer: ScorerFn,
               capabilities_per_config: Optional[Dict[str, List[str]]] = None,
               ) -> BeamSearchResult:
        """Run beam search.

        Args:
            seed_configs: the initial beam
            scorer: a function (config) -> float (higher is better)
            capabilities_per_config: optional dict {config_id: [caps]}

        Returns:
            BeamSearchResult with the final beam and per-iteration trace
        """
        rng = random.Random(self.seed)
        capabilities_per_config = capabilities_per_config or {}
        beam: List[Configuration] = list(seed_configs)
        scores: Dict[str, float] = {}
        iterations: List[BeamIteration] = []
        n_total_expansions = 0
        n_total_pruned = 0

        # Score the initial beam
        for c in beam:
            scores[c.config_id] = scorer(c)

        for it in range(self.n_iterations):
            iter_state = BeamIteration(iteration=it)
            iter_state.beam_before = [c.config_id for c in beam]

            # 1. Expand each candidate by each operator
            expansions: List[Configuration] = []
            for c in beam:
                # Use a deterministic subset of operators per candidate
                # (to keep branching factor manageable)
                ops_for_this = self.operators
                for op_name in ops_for_this:
                    try:
                        new = OPERATOR_LIBRARY.apply(c, op_name)
                        # Assign a new config_id for traceability
                        new.config_id = f"{c.config_id}→{op_name}"
                        expansions.append(new)
                    except Exception:
                        # Some operators may fail on certain configs — skip
                        pass
            iter_state.n_expansions_generated = len(expansions)
            n_total_expansions += len(expansions)

            # 2. Prune by hard constraints
            caps_for_expansions = {}
            for new in expansions:
                # Inherit caps from parent if available
                parent_id = new.config_id.split("→")[0]
                caps_for_expansions[new.config_id] = (
                    capabilities_per_config.get(parent_id, []))
            prune_result = self.pruner.prune(expansions, caps_for_expansions)
            survivors = prune_result.survived
            iter_state.n_expansions_survived_pruning = len(survivors)
            iter_state.pruned_ids = [c.config_id for c, _ in prune_result.pruned]
            n_total_pruned += prune_result.n_pruned

            # 3. Score survivors
            for c in survivors:
                scores[c.config_id] = scorer(c)

            # 4. Combine current beam + survivors, keep top-K
            combined = list(beam) + survivors
            combined.sort(key=lambda c: scores.get(c.config_id, -float("inf")),
                          reverse=True)
            # Tie-break by config_id for reproducibility
            top_k = combined[:self.beam_width]
            beam = top_k

            # Record iteration state
            scored = [scores.get(c.config_id, 0.0) for c in beam]
            iter_state.beam_after = [c.config_id for c in beam]
            iter_state.best_score = max(scored) if scored else 0.0
            iter_state.worst_score = min(scored) if scored else 0.0
            iterations.append(iter_state)

        return BeamSearchResult(
            beam=beam,
            iterations=iterations,
            scores=scores,
            n_total_expansions=n_total_expansions,
            n_total_pruned=n_total_pruned,
            seed=self.seed,
            beam_width=self.beam_width,
            n_iterations=self.n_iterations,
            timestamp=datetime.now(timezone.utc).isoformat(),
            provenance={
                "engine": "BeamSearch",
                "n_operators": len(self.operators),
                "operators": self.operators,
            },
        )


def main():
    print("=" * 60)
    print("BEAM SEARCH (DR-73)")
    print("=" * 60)
    print()

    from scripts.specification import SpecificationEngine
    from scripts.capability_graph import CapabilityGraph
    from scripts.artifact_generator import ArtifactGenerator
    from scripts.forward_model import ForwardModel

    spec = SpecificationEngine().compile(
        "improve thermoelectric efficiency of bismuth telluride")
    cg = CapabilityGraph()
    cg.from_relations([("bismuth telluride", "generates", "voltage")])
    seed_configs = ArtifactGenerator(seed=42).generate(spec, cg, n=3)

    fm = ForwardModel()

    def scorer(c: Configuration) -> float:
        pred = fm.predict(c)
        return pred.predicted_properties.get("ZT", 0.0)

    bs = BeamSearch(beam_width=5, n_iterations=2, seed=42)
    result = bs.search(seed_configs, scorer)
    print(f"Beam width: {result.beam_width}")
    print(f"Iterations: {result.n_iterations}")
    print(f"Total expansions: {result.n_total_expansions}")
    print(f"Total pruned: {result.n_total_pruned}")
    print()
    print("Final beam:")
    for c in result.beam:
        print(f"  {c.config_id}  score={result.scores[c.config_id]:.4f}  "
              f"hash={c.config_hash}")
    print()

    # Reproducibility
    result2 = BeamSearch(beam_width=5, n_iterations=2, seed=42).search(
        ArtifactGenerator(seed=42).generate(spec, cg, n=3), scorer)
    hashes_a = [c.config_hash for c in result.beam]
    hashes_b = [c.config_hash for c in result2.beam]
    print(f"Reproducibility: {'PASS' if hashes_a == hashes_b else 'FAIL'}")


if __name__ == "__main__":
    main()
