#!/usr/bin/env python3
"""
autonomous_inventor.py — DR-81: Wire ALL stages together into a single loop.

The autonomous invention loop:

  specification → discovery → capabilities → artifact generation →
  search → simulation → failure engine → novelty → prototype →
  measurement → learning → repeat

This module wires together all the existing stages and the new DR-69
through DR-80 modules into a single executable loop. Each iteration of
the loop:

  1. Compiles the spec (Stage I).
  2. Builds the capability graph (Stage 0.5).
  3. Reasons about capabilities (DR-69).
  4. Generates candidates (Stage II / DR-72 operator library).
  5. Searches the design space (DR-73).
  6. Predicts behavior (Stage IV).
  7. Runs the failure engine (DR-75).
  8. Checks novelty (Stage V).
  9. Compiles prototypes (Stage VI).
 10. Measures (Stage VII).
 11. Analyzes residuals (DR-78).
 12. Revises beliefs (DR-80).
 13. Records to design memory (DR-79).
 14. Repeats.

Usage:
    from scripts.autonomous_inventor import AutonomousInventor
    ai = AutonomousInventor(seed=42, n_cycles=3)
    result = ai.run(objective="improve thermoelectric efficiency of "
                              "bismuth telluride",
                    relations=[("bismuth telluride", "generates", "voltage")])
    # result.cycles[i].best_config is the top config from cycle i
    # result.cycles[i+1] is built on the lessons of cycle i
"""
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.specification import SpecificationEngine, Specification
from scripts.capability_graph import CapabilityGraph
from scripts.capability_reasoner import CapabilityReasoner
from scripts.capability_constraints import CapabilityConstraints
from scripts.artifact_generator import ArtifactGenerator, Configuration
from scripts.operator_library import OPERATOR_LIBRARY, generate_with_library
from scripts.search_engine import SearchEngine, SearchResult
from scripts.forward_model import ForwardModel
from scripts.novelty_engine import NoveltyEngine
from scripts.prototype_compiler import PrototypeCompiler
from scripts.measurement_engine import MeasurementEngine, MeasurementInstrument
from scripts.failure_engine import FailureEngine, FailureEngineResult
from scripts.experiment_runner import ExperimentRunner, ExperimentResult
from scripts.design_memory import DesignMemory
from scripts.operator_ranking import OperatorRanking
from scripts.belief_revision import BeliefRevision


@dataclass
class InventorCycle:
    """One cycle of the autonomous invention loop."""
    cycle: int
    spec: Optional[Specification] = None
    capabilities_inferred: List[str] = field(default_factory=list)
    search_result: Optional[SearchResult] = None
    best_config: Optional[Configuration] = None
    best_score: float = 0.0
    failure_engine_result: Optional[FailureEngineResult] = None
    is_novel: bool = False
    experiment_result: Optional[ExperimentResult] = None
    lessons_recorded: int = 0
    revised_top_operators: List[str] = field(default_factory=list)
    timestamp: str = ""
    trace: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class InventorResult:
    """The output of AutonomousInventor.run()."""
    cycles: List[InventorCycle] = field(default_factory=list)
    n_cycles: int = 0
    final_best_config: Optional[Configuration] = None
    final_best_score: float = 0.0
    final_beliefs: Dict[str, float] = field(default_factory=dict)
    final_operator_ranking: List[str] = field(default_factory=list)
    n_total_lessons: int = 0
    closed_loops: int = 0
    timestamp: str = ""
    provenance: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "n_cycles": self.n_cycles,
            "final_best_score": self.final_best_score,
            "final_beliefs": self.final_beliefs,
            "final_operator_ranking": self.final_operator_ranking,
            "n_total_lessons": self.n_total_lessons,
            "closed_loops": self.closed_loops,
            "cycle_summaries": [
                {"cycle": c.cycle,
                 "best_score": c.best_score,
                 "is_novel": c.is_novel,
                 "lessons_recorded": c.lessons_recorded,
                 "n_trace_entries": len(c.trace)}
                for c in self.cycles
            ],
            "timestamp": self.timestamp,
            "provenance": self.provenance,
        }


class AutonomousInventor:
    """DR-81: the full autonomous invention loop."""

    def __init__(self, seed: int = 42, n_cycles: int = 3,
                 beam_width: int = 4, n_iterations: int = 2,
                 n_candidates: int = 4,
                 forward_model: Optional[ForwardModel] = None,
                 compiler: Optional[PrototypeCompiler] = None,
                 instrument: Optional[MeasurementInstrument] = None,
                 design_memory: Optional[DesignMemory] = None):
        self.seed = seed
        self.n_cycles = n_cycles
        self.beam_width = beam_width
        self.n_iterations = n_iterations
        self.n_candidates = n_candidates
        # Engines
        self.forward_model = forward_model or ForwardModel()
        self.compiler = compiler or PrototypeCompiler(forward_model=self.forward_model)
        self.instrument = instrument or MeasurementInstrument()
        self.design_memory = design_memory or DesignMemory()
        self.failure_engine = FailureEngine()
        self.capability_reasoner = CapabilityReasoner()
        self.capability_constraints = CapabilityConstraints()
        self.novelty_engine = NoveltyEngine()
        self.operator_ranking = OperatorRanking()
        self.belief_revision = BeliefRevision()

    # ----- public API ---------------------------------------------------
    def run(self, objective: str,
            relations: List[Tuple[str, str, str]],
            input_text: Optional[str] = None,
            gold_text: Optional[str] = None,
            ) -> InventorResult:
        """Run the full invention loop.

        Args:
            objective: the natural-language objective
            relations: list of (subject, verb, object) for the capability graph
            input_text: optional input text for the failure engine's gold checker
            gold_text: optional gold-standard text for contamination check

        Returns:
            InventorResult with per-cycle summaries
        """
        cycles: List[InventorCycle] = []
        # Build the spec once (the objective doesn't change)
        spec = SpecificationEngine().compile(objective)
        # Build the capability graph once
        cg = CapabilityGraph()
        cg.from_relations(relations)

        best_overall_config = None
        best_overall_score = 0.0
        n_total_lessons = 0
        closed_loops = 0

        for c_idx in range(self.n_cycles):
            cycle = self._run_one_cycle(
                cycle_idx=c_idx, spec=spec, cg=cg,
                input_text=input_text, gold_text=gold_text)
            cycles.append(cycle)
            # Track overall best
            if cycle.best_config and cycle.best_score > best_overall_score:
                best_overall_config = cycle.best_config
                best_overall_score = cycle.best_score
            n_total_lessons += cycle.lessons_recorded
            if cycle.experiment_result and cycle.experiment_result.closed:
                closed_loops += 1

        return InventorResult(
            cycles=cycles,
            n_cycles=len(cycles),
            final_best_config=best_overall_config,
            final_best_score=best_overall_score,
            final_beliefs=dict(self.belief_revision.beliefs),
            final_operator_ranking=self.operator_ranking.top_k(k=5),
            n_total_lessons=n_total_lessons,
            closed_loops=closed_loops,
            timestamp=datetime.now(timezone.utc).isoformat(),
            provenance={
                "engine": "AutonomousInventor",
                "stage": "DR-81",
                "n_cycles": self.n_cycles,
                "beam_width": self.beam_width,
                "n_iterations": self.n_iterations,
                "n_candidates": self.n_candidates,
                "stages_wired": [
                    "specification", "capability_graph", "capability_reasoner",
                    "operator_library", "search_engine", "forward_model",
                    "failure_engine", "novelty_engine", "prototype_compiler",
                    "measurement_engine", "experiment_runner",
                    "design_memory", "operator_ranking", "belief_revision",
                ],
            },
        )

    # ----- internals ----------------------------------------------------
    def _run_one_cycle(self, cycle_idx: int, spec: Specification,
                       cg: CapabilityGraph,
                       input_text: Optional[str],
                       gold_text: Optional[str]) -> InventorCycle:
        trace: List[Dict[str, Any]] = []
        cycle = InventorCycle(
            cycle=cycle_idx, spec=spec, timestamp=datetime.now(timezone.utc).isoformat())

        # 1. Reason about capabilities
        caps_inferred: List[str] = []
        for entity_edges in cg.capabilities_by_entity.values():
            cap_names = [e.capability for e in entity_edges]
            reasoning = self.capability_reasoner.infer(cap_names)
            caps_inferred.extend(reasoning.closure)
        caps_inferred = sorted(set(caps_inferred))
        cycle.capabilities_inferred = caps_inferred
        trace.append({"step": "capability_reasoning",
                      "n_inferred": len(caps_inferred)})

        # 2. Search the design space
        search_engine = SearchEngine(
            seed=self.seed + cycle_idx,
            beam_width=self.beam_width,
            n_iterations=self.n_iterations,
            n_seed_configs=self.n_candidates,
            forward_model=self.forward_model,
        )
        search_result = search_engine.search(spec, cg)
        cycle.search_result = search_result
        cycle.best_config = search_result.best_config
        cycle.best_score = search_result.best_score
        trace.append({"step": "search",
                      "best_score": cycle.best_score,
                      "n_expansions": search_result.n_expansions_total})

        # 3. Failure engine check on the best config
        if cycle.best_config is not None:
            pred = self.forward_model.predict(cycle.best_config)
            meas = self.instrument.measure(cycle.best_config)
            # Use a small set of varied configs for the forward-model check
            sample_configs = [cycle.best_config]
            if search_result.final_beam:
                sample_configs = list(search_result.final_beam)[:4]
            fr = self.failure_engine.run(
                prediction=pred, measurement=meas,
                input_text=input_text, gold_text=gold_text,
                forward_model=self.forward_model,
                sample_configs=sample_configs, metric="ZT")
            cycle.failure_engine_result = fr
            trace.append({"step": "failure_engine",
                          "status": fr.status,
                          "n_failed": fr.n_failed})

            # 4. Novelty check
            novelty_report = self.novelty_engine.check(cycle.best_config)
            cycle.is_novel = novelty_report.is_novel
            self.novelty_engine.register(cycle.best_config)
            trace.append({"step": "novelty_check",
                          "is_novel": cycle.is_novel})

            # 5. Experiment runner (predict → build → measure → residual → repair)
            exp_runner = ExperimentRunner(
                seed=self.seed + cycle_idx,
                forward_model=self.forward_model,
                compiler=self.compiler,
                instrument=self.instrument,
            )
            exp_result = exp_runner.run(spec, cg,
                                        n_iterations=1,
                                        n_candidates=self.n_candidates)
            cycle.experiment_result = exp_result
            trace.append({"step": "experiment_runner",
                          "closed": exp_result.closed,
                          "n_measured": exp_result.n_total_measured})

            # 6. Update beliefs & ranking based on outcomes
            if exp_result.iterations:
                it = exp_result.iterations[0]
                # Record outcomes: for each config, did its prediction match
                # its measurement within tolerance?
                for r in it.residuals:
                    # The operator that produced this config is the LAST
                    # operator in its design_operator_chain (excluding "init")
                    ops = [op for op in cycle.best_config.design_operator_chain
                           if op != "init"]
                    for op in ops:
                        passed = not r.significant  # passed if not significant
                        self.belief_revision.observe(op, passed=passed)
                        self.operator_ranking.record_outcome(op, passed=passed)
                # Record lessons to design memory
                if it.residual_analysis:
                    for rec in it.residual_analysis.recommendations:
                        self.design_memory.record_failure(
                            config_id=cycle.best_config.config_id,
                            reason="residual bias",
                            lesson=rec)
                        cycle.lessons_recorded += 1
                # Record the iteration to design memory
                self.design_memory.record_iteration(
                    iteration=cycle_idx,
                    config_ids=[c.config_id for c in it.generated_configs],
                    priors_before=it.correction_priors_before,
                    priors_after=it.correction_priors_after,
                    n_measured=it.n_measured)

            # Record a motif if the best score is high
            if cycle.best_score > 0.5:
                self.design_memory.record_motif(
                    motif_id=f"MOTIF-C{cycle_idx}",
                    components=[c.material for c in cycle.best_config.components],
                    structure=cycle.best_config.structure,
                    score=cycle.best_score,
                    config_id=cycle.best_config.config_id)

        # 7. Get revised operator recommendations
        cycle.revised_top_operators = self.belief_revision.recommended_operators(top_k=5)
        trace.append({"step": "belief_revision",
                      "top_operators": cycle.revised_top_operators[:3]})

        cycle.trace = trace
        return cycle


def main():
    print("=" * 60)
    print("AUTONOMOUS INVENTOR (DR-81)")
    print("=" * 60)
    print()

    ai = AutonomousInventor(seed=42, n_cycles=2, beam_width=3,
                            n_iterations=1, n_candidates=3)
    result = ai.run(
        objective="improve thermoelectric efficiency of bismuth telluride",
        relations=[
            ("bismuth telluride", "generates", "voltage"),
            ("bismuth telluride", "conducts", "electricity"),
            ("lead telluride", "generates", "voltage"),
            ("bismuth telluride", "transfers", "heat"),
        ],
        input_text="improve thermoelectric efficiency of bismuth telluride",
        gold_text="The reference contains Seebeck, conductivity, and "
                  "thermal data for various lead alloys.",
    )

    print(f"Cycles: {result.n_cycles}")
    print(f"Final best score: {result.final_best_score:.4f}")
    print(f"Closed loops: {result.closed_loops}")
    print(f"Total lessons recorded: {result.n_total_lessons}")
    print(f"Final top-5 operators: {result.final_operator_ranking}")
    print()
    for c in result.cycles:
        print(f"--- Cycle {c.cycle} ---")
        print(f"  Inferred capabilities: {len(c.capabilities_inferred)}")
        print(f"  Best score: {c.best_score:.4f}")
        print(f"  Failure engine: {c.failure_engine_result.status if c.failure_engine_result else 'N/A'}")
        print(f"  Novel: {c.is_novel}")
        print(f"  Lessons recorded: {c.lessons_recorded}")
        print(f"  Top operators: {c.revised_top_operators[:3]}")
        print()


if __name__ == "__main__":
    main()
