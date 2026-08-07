#!/usr/bin/env python3
"""
vertical_slice_thermal.py — DR-82: Run the full invention loop for one domain.

Domain: thermal materials / thermoelectrics.

Objective: improve thermoelectric performance.
Constraints: cost, stability, operating temperature.
Pipeline: full end-to-end — specification → discovery → capabilities →
artifact generation → search → simulation → failure engine → novelty →
prototype → measurement → learning.

This is a vertical slice: ONE domain, ONE objective, the full pipeline.
It's the integration test that proves all the DR-69 through DR-81
modules work together for a real-world domain.

Usage:
    from scripts.vertical_slice_thermal import VerticalSliceThermal
    vst = VerticalSliceThermal(seed=42)
    result = vst.run()
    # result.report contains the full end-to-end outcome
"""
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.autonomous_inventor import AutonomousInventor, InventorResult
from scripts.specification import SpecificationEngine, Specification
from scripts.capability_graph import CapabilityGraph
from scripts.capability_reasoner import CapabilityReasoner
from scripts.capability_constraints import CapabilityConstraints
from scripts.acceptance_criteria import AcceptanceCriteriaCompiler, AcceptanceCriteria
from scripts.goal_parser import GoalParser
from scripts.design_memory import DesignMemory


@dataclass
class VerticalSliceReport:
    """The end-to-end report for the thermal vertical slice."""
    domain: str = "thermal"
    objective: str = ""
    goals_parsed: List[Dict[str, Any]] = field(default_factory=list)
    spec: Optional[Dict[str, Any]] = None
    acceptance_criteria: List[Dict[str, Any]] = field(default_factory=list)
    capabilities_inferred: List[str] = field(default_factory=list)
    physics_constraints: List[Dict[str, Any]] = field(default_factory=list)
    inventor_result: Optional[Dict[str, Any]] = None
    best_config_id: Optional[str] = None
    best_score: float = 0.0
    best_predicted_ZT: Optional[float] = None
    best_measured_ZT: Optional[float] = None
    best_residual: Optional[float] = None
    n_cycles: int = 0
    n_total_lessons: int = 0
    closed_loops: int = 0
    acceptance_passed: bool = False
    timestamp: str = ""
    trace: List[Dict[str, Any]] = field(default_factory=list)
    provenance: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "domain": self.domain,
            "objective": self.objective,
            "goals_parsed": self.goals_parsed,
            "spec": self.spec,
            "acceptance_criteria": self.acceptance_criteria,
            "capabilities_inferred": self.capabilities_inferred,
            "physics_constraints": self.physics_constraints,
            "inventor_result": self.inventor_result,
            "best_config_id": self.best_config_id,
            "best_score": self.best_score,
            "best_predicted_ZT": self.best_predicted_ZT,
            "best_measured_ZT": self.best_measured_ZT,
            "best_residual": self.best_residual,
            "n_cycles": self.n_cycles,
            "n_total_lessons": self.n_total_lessons,
            "closed_loops": self.closed_loops,
            "acceptance_passed": self.acceptance_passed,
            "timestamp": self.timestamp,
            "trace": self.trace,
            "provenance": self.provenance,
        }


class VerticalSliceThermal:
    """DR-82: the thermal vertical slice — full end-to-end pipeline."""

    OBJECTIVE = ("improve thermoelectric efficiency of bismuth telluride "
                 "for room-temperature power generation")
    DOMAIN = "thermal"

    # The relations / discoveries that seed the capability graph.
    RELATIONS = [
        ("bismuth telluride", "generates", "voltage"),
        ("bismuth telluride", "conducts", "electricity"),
        ("bismuth telluride", "transfers", "heat"),
        ("bismuth telluride", "resists", "thermal shock"),
        ("lead telluride", "generates", "voltage"),
        ("lead telluride", "conducts", "electricity"),
        ("graphene", "conducts", "electricity"),
        ("graphene", "transfers", "heat"),
        ("silicon", "generates", "voltage"),
    ]

    def __init__(self, seed: int = 42, n_cycles: int = 2,
                 design_memory: Optional[DesignMemory] = None):
        self.seed = seed
        self.n_cycles = n_cycles
        self.design_memory = design_memory or DesignMemory()
        self.goal_parser = GoalParser()
        self.spec_engine = SpecificationEngine()
        self.cap_reasoner = CapabilityReasoner()
        self.cap_constraints = CapabilityConstraints()
        self.acceptance_compiler = AcceptanceCriteriaCompiler()
        self.inventor = AutonomousInventor(
            seed=seed, n_cycles=n_cycles,
            beam_width=4, n_iterations=2, n_candidates=4,
            design_memory=self.design_memory,
        )

    # ----- public API ---------------------------------------------------
    def run(self) -> VerticalSliceReport:
        """Run the full thermal vertical slice end-to-end."""
        trace: List[Dict[str, Any]] = []
        report = VerticalSliceReport(
            domain=self.DOMAIN,
            objective=self.OBJECTIVE,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        # 1. Parse goals
        goals = self.goal_parser.parse_many([
            "increase ZT by 50%",
            "reduce cost by 20%",
            "improve stability to 1000 cycles",
        ])
        report.goals_parsed = [g.to_dict() for g in goals.goals]
        trace.append({"step": "goal_parsing", "n_goals": len(goals.goals)})

        # 2. Compile spec
        spec = self.spec_engine.compile(self.OBJECTIVE)
        report.spec = {
            "objective": spec.objective,
            "domain": spec.domain,
            "target_material": spec.target_material,
            "capability_targets": spec.capability_targets,
            "hard_constraints": spec.hard_constraints,
            "acceptance_criteria": spec.acceptance_criteria,
        }
        trace.append({"step": "spec_compilation",
                      "domain": spec.domain,
                      "n_hard_constraints": len(spec.hard_constraints)})

        # 3. Compile acceptance criteria
        ac = self.acceptance_compiler.compile_from_specification(spec)
        report.acceptance_criteria = [c.to_dict() for c in ac]
        trace.append({"step": "acceptance_criteria",
                      "n_criteria": len(ac)})

        # 4. Build capability graph + reason
        cg = CapabilityGraph()
        cg.from_relations(self.RELATIONS)
        # Infer closure capabilities across all entities
        all_caps = set()
        for entity, edges in cg.capabilities_by_entity.items():
            cap_names = [e.capability for e in edges]
            reasoning = self.cap_reasoner.infer(cap_names)
            all_caps.update(reasoning.closure)
        report.capabilities_inferred = sorted(all_caps)
        trace.append({"step": "capability_reasoning",
                      "n_inferred": len(all_caps)})

        # 5. Derive physics constraints
        cap_list = list(all_caps)
        constraint_result = self.cap_constraints.derive(cap_list)
        report.physics_constraints = [
            {"capability": c.capability, "parameter": c.parameter,
             "operator": c.operator, "threshold": c.threshold,
             "units": c.units, "rationale": c.rationale}
            for c in constraint_result.constraints
        ]
        trace.append({"step": "constraint_derivation",
                      "n_constraints": len(report.physics_constraints)})

        # 6. Run the full autonomous invention loop
        inventor_result = self.inventor.run(
            objective=self.OBJECTIVE,
            relations=self.RELATIONS,
            input_text=self.OBJECTIVE,
            gold_text=("The reference dataset contains Seebeck coefficient, "
                       "electrical conductivity, and thermal conductivity "
                       "for various lead and bismuth alloys."),
        )
        report.inventor_result = inventor_result.to_dict()
        report.n_cycles = inventor_result.n_cycles
        report.n_total_lessons = inventor_result.n_total_lessons
        report.closed_loops = inventor_result.closed_loops
        report.best_config_id = (
            inventor_result.final_best_config.config_id
            if inventor_result.final_best_config else None)
        report.best_score = inventor_result.final_best_score
        trace.append({"step": "autonomous_inventor",
                      "best_score": report.best_score,
                      "closed_loops": report.closed_loops})

        # 7. Predict + measure the best config to extract ZT values
        if inventor_result.final_best_config is not None:
            from scripts.forward_model import ForwardModel
            from scripts.independent_measurement import IndependentMeasurement
            from scripts.physical_plausibility import PhysicalPlausibilityChecker
            fm = ForwardModel()
            inst = IndependentMeasurement()  # INDEPENDENT code path (Track A2)
            best = inventor_result.final_best_config
            pred = fm.predict(best)
            meas = inst.measure(best)  # independent measurement
            pred_ZT = pred.predicted_properties.get("ZT")
            meas_ZT = meas.measured_zt  # from independent code path

            # F-100: Physical plausibility veto — if ZT > 5, reject
            plaus_checker = PhysicalPlausibilityChecker()
            plaus_result = plaus_checker.check_prediction(pred.predicted_properties)
            if plaus_result.vetoed:
                report.plausibility_violations = plaus_result.to_dict()
                # ZT is physically impossible — report honestly
                report.best_predicted_ZT = pred_ZT
                report.best_measured_ZT = meas_ZT
                report.acceptance_passed = False
                report.plausibility_note = (
                    f"VETOED: predicted ZT={pred_ZT:.2f} exceeds physical maximum (5.0). "
                    f"The candidate games the ZT formula by maximizing S and σ simultaneously, "
                    f"which is physically impossible (Pisarenko relation). The search needs "
                    f"material-realistic priors, not unbounded amplification."
                )
                trace.append({"step": "plausibility_veto",
                              "ZT": pred_ZT,
                              "vetoed": True})
                report.trace = trace
                return report

            report.best_predicted_ZT = pred_ZT
            report.best_measured_ZT = meas_ZT
            if pred_ZT is not None and meas_ZT is not None:
                report.best_residual = pred_ZT - meas_ZT
            # Evaluate acceptance criteria against the measured values
            candidate_metrics = {
                "ZT": meas_ZT or 0.0,
                "seebeck_coefficient":
                    best.components[0].parameters.get("seebeck_coefficient", 0.0)
                    * 1e6,  # convert V/K to µV/K
                "temperature_range":
                    best.parameters.get("T_hot_K", 400.0),
                "stability": 200.0,  # placeholder
            }
            ac_result = ac.evaluate(candidate_metrics)
            report.acceptance_passed = ac_result.passed
            trace.append({"step": "acceptance_evaluation",
                          "passed": ac_result.passed,
                          "n_passed": ac_result.n_passed,
                          "n_failed": ac_result.n_failed})

        # 8. Final trace
        report.trace = trace
        report.provenance = {
            "engine": "VerticalSliceThermal",
            "stage": "DR-82",
            "domain": self.DOMAIN,
            "n_cycles": self.n_cycles,
            "n_relations": len(self.RELATIONS),
            "pipeline_stages": [
                "goal_parsing", "spec_compilation", "acceptance_criteria",
                "capability_reasoning", "constraint_derivation",
                "autonomous_inventor", "acceptance_evaluation",
            ],
        }
        return report


def main():
    print("=" * 60)
    print("VERTICAL SLICE: THERMAL (DR-82)")
    print("=" * 60)
    print()

    vst = VerticalSliceThermal(seed=42, n_cycles=2)
    report = vst.run()

    print(f"Domain: {report.domain}")
    print(f"Objective: {report.objective}")
    print()
    print(f"Goals parsed: {len(report.goals_parsed)}")
    for g in report.goals_parsed:
        print(f"  - {g['raw_text']} → {g['metric']} "
              f"target={g['target']}")
    print()
    print(f"Spec: domain={report.spec['domain']} "
          f"target_material={report.spec['target_material']}")
    print(f"Acceptance criteria: {len(report.acceptance_criteria)}")
    for ac in report.acceptance_criteria:
        print(f"  - {ac['metric']} {ac['operator']} {ac['threshold']}")
    print()
    print(f"Inferred capabilities: {len(report.capabilities_inferred)}")
    print(f"  {report.capabilities_inferred[:5]} ...")
    print()
    print(f"Physics constraints: {len(report.physics_constraints)}")
    print()
    print(f"Inventor result:")
    print(f"  cycles: {report.n_cycles}")
    print(f"  best config: {report.best_config_id}")
    print(f"  best score: {report.best_score:.4f}")
    print(f"  closed loops: {report.closed_loops}")
    print(f"  total lessons: {report.n_total_lessons}")
    print()
    print(f"Best config predictions:")
    print(f"  predicted ZT: {report.best_predicted_ZT}")
    print(f"  measured ZT: {report.best_measured_ZT}")
    print(f"  residual: {report.best_residual}")
    print()
    print(f"Acceptance criteria passed: {report.acceptance_passed}")
    print()
    print("Trace:")
    for entry in report.trace:
        print(f"  [{entry['step']}] {entry}")


if __name__ == "__main__":
    main()
