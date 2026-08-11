#!/usr/bin/env python3
"""
search_engine.py — DR-73: The main search orchestrator.

Wires together:
  - ArtifactGenerator / operator_library (config generation)
  - ConstraintPruner (DR-73)
  - BeamSearch (DR-73)
  - ForwardModel (Stage IV) for scoring
  - A reproducible search trace log

The orchestrator is reproducible under a seed and logs every step of the
search to a trace log (list of dicts).

Usage:
    from scripts.search_engine import SearchEngine
    engine = SearchEngine(seed=42, beam_width=5, n_iterations=3)
    result = engine.search(spec, capability_graph)
    # result.best_config is the top-scoring config
"""
import sys
import random
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any, Callable
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.artifact_generator import ArtifactGenerator, Configuration
from scripts.forward_model import ForwardModel
from scripts.operator_library import OPERATOR_LIBRARY
from scripts.constraint_pruning import ConstraintPruner
from scripts.beam_search import BeamSearch, BeamSearchResult


@dataclass
class SearchTraceEntry:
    """One entry in the search trace log."""
    step: str           # 'init', 'prune', 'expand', 'score', 'select'
    iteration: int
    message: str
    config_ids: List[str] = field(default_factory=list)
    timestamp: str = ""


@dataclass
class SearchResult:
    """The output of SearchEngine.search()."""
    best_config: Optional[Configuration] = None
    best_score: float = 0.0
    final_beam: List[Configuration] = field(default_factory=list)
    n_seed_configs: int = 0
    n_expansions_total: int = 0
    n_pruned_total: int = 0
    seed: int = 0
    beam_width: int = 0
    n_iterations: int = 0
    trace: List[Dict[str, Any]] = field(default_factory=list)
    beam_search_result: Optional[BeamSearchResult] = None
    timestamp: str = ""
    provenance: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "best_config_id": self.best_config.config_id if self.best_config else None,
            "best_score": self.best_score,
            "final_beam": [c.config_id for c in self.final_beam],
            "n_seed_configs": self.n_seed_configs,
            "n_expansions_total": self.n_expansions_total,
            "n_pruned_total": self.n_pruned_total,
            "seed": self.seed,
            "beam_width": self.beam_width,
            "n_iterations": self.n_iterations,
            "trace": self.trace,
            "timestamp": self.timestamp,
            "provenance": self.provenance,
        }


class SearchEngine:
    """DR-73: the main search orchestrator using beam search."""

    def __init__(self,
                 seed: int = 42,
                 beam_width: int = 5,
                 n_iterations: int = 3,
                 n_seed_configs: int = 5,
                 forward_model: Optional[ForwardModel] = None,
                 pruner: Optional[ConstraintPruner] = None,
                 scorer: Optional[Callable[[Configuration], float]] = None,
                 operators: Optional[List[str]] = None):
        self.seed = seed
        self.beam_width = beam_width
        self.n_iterations = n_iterations
        self.n_seed_configs = n_seed_configs
        self.forward_model = forward_model or ForwardModel()
        self.pruner = pruner or ConstraintPruner()
        self.operators = operators or OPERATOR_LIBRARY.names
        # Default scorer: predicted ZT for thermoelectric domain,
        # predicted power for thermal, predicted capacitance for supercap.
        self.scorer = scorer or self._default_scorer
        self._trace: List[Dict[str, Any]] = []

    # ----- public API ---------------------------------------------------
    def search(self, spec, capability_graph,
               capabilities_per_config: Optional[Dict[str, List[str]]] = None
               ) -> SearchResult:
        """Run the full search.

        Args:
            spec: a Specification
            capability_graph: a CapabilityGraph
            capabilities_per_config: optional dict of capabilities per config_id

        Returns:
            SearchResult with best_config, final_beam, and full trace
        """
        self._trace = []
        self._log("init", 0, f"seed={self.seed} beam={self.beam_width} "
                  f"iters={self.n_iterations}")

        # 1. Generate seed configs
        gen = ArtifactGenerator(seed=self.seed)
        seed_configs = gen.generate(spec, capability_graph, n=self.n_seed_configs)
        self._log("seed", 0,
                  f"generated {len(seed_configs)} seed configs",
                  config_ids=[c.config_id for c in seed_configs])

        # 2. Prune seeds by hard constraints
        prune_result = self.pruner.prune(seed_configs, capabilities_per_config)
        self._log("prune", 0,
                  f"pruned {prune_result.n_pruned} of {prune_result.n_input} seeds",
                  config_ids=[c.config_id for c in prune_result.survived])
        if not prune_result.survived:
            self._log("abort", 0, "no seeds survived pruning")
            return SearchResult(
                best_config=None, best_score=0.0,
                final_beam=[], n_seed_configs=len(seed_configs),
                n_expansions_total=0, n_pruned_total=prune_result.n_pruned,
                seed=self.seed, beam_width=self.beam_width,
                n_iterations=0, trace=list(self._trace),
                timestamp=datetime.now(timezone.utc).isoformat(),
                provenance={"engine": "SearchEngine", "aborted": True})

        # 3. Beam search
        beam_search = BeamSearch(
            beam_width=self.beam_width,
            n_iterations=self.n_iterations,
            seed=self.seed,
            pruner=self.pruner,
            operators=self.operators,
        )
        bs_result = beam_search.search(
            prune_result.survived, self.scorer,
            capabilities_per_config=capabilities_per_config)
        for it in bs_result.iterations:
            self._log("iteration", it.iteration,
                      f"expanded={it.n_expansions_generated} "
                      f"survived={it.n_expansions_survived_pruning} "
                      f"best_score={it.best_score:.4f}",
                      config_ids=it.beam_after)

        # 4. Pick best
        if bs_result.beam:
            best = bs_result.beam[0]
            best_score = bs_result.scores.get(best.config_id, 0.0)
        else:
            best = None
            best_score = 0.0
        self._log("done", self.n_iterations,
                  f"best_score={best_score:.4f} "
                  f"best={best.config_id if best else None}")

        return SearchResult(
            best_config=best,
            best_score=best_score,
            final_beam=bs_result.beam,
            n_seed_configs=len(seed_configs),
            n_expansions_total=bs_result.n_total_expansions,
            n_pruned_total=bs_result.n_total_pruned + prune_result.n_pruned,
            seed=self.seed,
            beam_width=self.beam_width,
            n_iterations=self.n_iterations,
            trace=list(self._trace),
            beam_search_result=bs_result,
            timestamp=datetime.now(timezone.utc).isoformat(),
            provenance={
                "engine": "SearchEngine",
                "scorer": self.scorer.__name__ if hasattr(self.scorer, '__name__')
                          else "default",
                "n_operators": len(self.operators),
            },
        )

    def get_trace(self) -> List[Dict[str, Any]]:
        """Return the trace log from the last search."""
        return list(self._trace)

    # ----- internals ----------------------------------------------------
    def _default_scorer(self, c: Configuration) -> float:
        pred = self.forward_model.predict(c)
        # Pick the most relevant metric for the domain
        props = pred.predicted_properties
        if "ZT" in props:
            return float(props["ZT"])
        if "Q_rad_W" in props:
            return float(props["Q_rad_W"])
        if "capacitance_F" in props:
            return float(props["capacitance_F"])
        if "power_W" in props:
            return float(props["power_W"])
        # Fallback: sum all numeric properties
        return float(sum(v for v in props.values() if isinstance(v, (int, float))))

    def _log(self, step: str, iteration: int, message: str,
             config_ids: Optional[List[str]] = None) -> None:
        self._trace.append({
            "step": step,
            "iteration": iteration,
            "message": message,
            "config_ids": list(config_ids) if config_ids else [],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })


def main():
    print("=" * 60)
    print("SEARCH ENGINE (DR-73)")
    print("=" * 60)
    print()

    from scripts.specification import SpecificationEngine
    from scripts.capability_graph import CapabilityGraph

    spec = SpecificationEngine().compile(
        "improve thermoelectric efficiency of bismuth telluride")
    cg = CapabilityGraph()
    cg.from_relations([
        ("bismuth telluride", "generates", "voltage"),
        ("bismuth telluride", "conducts", "electricity"),
        ("lead telluride", "generates", "voltage"),
    ])

    engine = SearchEngine(seed=42, beam_width=5, n_iterations=2,
                          n_seed_configs=5)
    result = engine.search(spec, cg)

    print(f"Seed configs: {result.n_seed_configs}")
    print(f"Total expansions: {result.n_expansions_total}")
    print(f"Total pruned: {result.n_pruned_total}")
    print(f"Best score: {result.best_score:.4f}")
    if result.best_config:
        print(f"Best config: {result.best_config.config_id}  "
              f"hash={result.best_config.config_hash}")
        print(f"  chain: {' -> '.join(result.best_config.design_operator_chain)}")
    print()
    print("Trace (last 5 entries):")
    for entry in result.trace[-5:]:
        print(f"  [{entry['step']}/{entry['iteration']}] {entry['message']}")
    print()

    # Reproducibility
    result2 = SearchEngine(seed=42, beam_width=5, n_iterations=2,
                           n_seed_configs=5).search(spec, cg)
    h1 = result.best_config.config_hash if result.best_config else None
    h2 = result2.best_config.config_hash if result2.best_config else None
    print(f"Reproducibility: {'PASS' if h1 == h2 else 'FAIL'}  "
          f"({h1} vs {h2})")


if __name__ == "__main__":
    main()
