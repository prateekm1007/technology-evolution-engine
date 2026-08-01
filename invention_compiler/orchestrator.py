"""
Invention Compiler — Top-level orchestrator.

Runs the 11-layer pipeline:
  Layer 0  — OpportunityDefinition (this module) + analogy_engine
  Layer 1  — 5 domain engines (physics/chem/bio/math/econ)
  Layer 2  — dependency_engine + resurrection_engine
  Layer 3  — mathematics_engine (governing_equations) + constraint_engine (failure_modes)
  Layer 4  — architecture_engine + constraint_engine (tolerances)
  Layer 5  — simulation_engine
  Layer 6  — constraint_engine (manufacturing)
  Layer 7  — economics_engine (capex/opex/market)
  Layer 8  — verification_engine
  Layer 9  — prototype_engine
  Layer 10 — blueprint_engine

Per ANTI_ENTROPY.md:
  - Tests first (see tests/test_invention_compiler.py)
  - Single responsibility: this orchestrator ONLY composes layers;
    each layer's logic lives in its own engine module.
  - Decoupled: every engine accepts the graph as a constructor arg.
  - Law 8 honesty: every layer that emits a scalar carries evidence +
    assumptions + falsification_criteria.

Per INVENTION_COMPILER.md:
  - Every layer must emit its full schema (NULL is allowed; missing
    keys are a bug).
  - The system may NEVER output "this is a good idea." The output is
    the chain of reasoning, not a verdict.
"""
import hashlib
import json
import time
from datetime import datetime, timezone
from typing import Dict, Any

from .analogy_engine import AnalogyEngine
from .physics_engine import PhysicsEngine
from .chemistry_engine import ChemistryEngine
from .biology_engine import BiologyEngine
from .mathematics_engine import MathematicsEngine
from .economics_engine import EconomicsEngine
from .constraint_engine import ConstraintEngine
from .architecture_engine import ArchitectureEngine
from .simulation_engine import SimulationEngine
from .dependency_engine import DependencyEngine
from .resurrection_engine import ResurrectionEngine
from .verification_engine import VerificationEngine
from .prototype_engine import PrototypeEngine
from .blueprint_engine import BlueprintEngine


class InventionCompiler:
    """Runs the 11-layer invention compilation pipeline.

    Construction:
        graph: the civilization graph dict (JSON-loaded). Decoupled
               per ANTI_ENTROPY.md rule 'Decouple modules'.
    """

    def __init__(self, graph: Dict[str, Any]):
        self.graph = graph
        # Instantiate every engine once. Decoupled per anti-entropy rule.
        self.analogy = AnalogyEngine(graph)
        self.physics = PhysicsEngine(graph)
        self.chemistry = ChemistryEngine(graph)
        self.biology = BiologyEngine(graph)
        self.mathematics = MathematicsEngine(graph)
        self.economics = EconomicsEngine(graph)
        self.constraint = ConstraintEngine(graph)
        self.architecture = ArchitectureEngine(graph)
        self.simulation = SimulationEngine(graph)
        self.dependency = DependencyEngine(graph)
        self.resurrection = ResurrectionEngine(graph)
        self.verification = VerificationEngine(graph)
        self.prototype = PrototypeEngine(graph)
        self.blueprint = BlueprintEngine(graph)

    def compile(self, problem: Dict[str, Any]) -> Dict[str, Any]:
        """Compile a problem through all 11 layers.

        Returns a dict with:
          - problem_id: stable hash of the problem (Law 7 replayability)
          - timestamp: ISO8601 UTC
          - writer: this module's path (Law 8 replayability)
          - layers: dict of layer-number -> layer-output
        """
        problem_id = self._stable_id(problem)
        timestamp = datetime.now(timezone.utc).isoformat()
        layers: Dict[int, Dict[str, Any]] = {}

        # -------- Layer 0: Opportunity definition --------
        analogy_output = self.analogy.find_analogies(problem)
        layers[0] = {
            "problem": problem.get("problem"),
            "domain": problem.get("domain"),
            "motivation": problem.get("motivation"),
            "market": problem.get("market"),
            "constraints": problem.get("constraints", []),
            "time_horizon": problem.get("time_horizon"),
            "analogies": analogy_output["analogies"],
            # Honesty block at the layer level — Layer 0 is not a scalar
            # layer, but the analogies carry their own evidence.
            "evidence": analogy_output["evidence"],
            "assumptions": analogy_output["assumptions"],
            "falsification_criteria": analogy_output["falsification_criteria"],
        }

        # -------- Layer 1: First-principles analysis --------
        physics_out = self.physics.analyze(problem)
        chemistry_out = self.chemistry.analyze(problem)
        biology_out = self.biology.analyze(problem)
        math_l1 = self.mathematics.analyze_layer1(problem, physics_out)
        econ_l1 = self.economics.analyze_layer1(problem)
        layers[1] = {
            "physics": physics_out,
            "chemistry": chemistry_out,
            "biology": biology_out,
            "mathematics": math_l1,
            "economics": econ_l1,
            # information_theory, thermodynamics, control_theory:
            # these are stubbed honestly — we don't have dedicated engines
            # for them yet. They are part of the 13-module backlog.
            "information_theory": {
                "value": None,
                "reason": "information_theory_engine not yet implemented; "
                          "see INVENTION_COMPILER.md module table",
                "evidence": {"engine_status": "not_implemented"},
                "assumptions": [],
                "falsification_criteria": "N/A — engine missing.",
            },
            "thermodynamics": {
                "value": None,
                "reason": "thermodynamics_engine not yet implemented",
                "evidence": {"engine_status": "not_implemented"},
                "assumptions": [],
                "falsification_criteria": "N/A — engine missing.",
            },
            "control_theory": {
                "value": None,
                "reason": "control_theory_engine not yet implemented",
                "evidence": {"engine_status": "not_implemented"},
                "assumptions": [],
                "falsification_criteria": "N/A — engine missing.",
            },
        }

        # -------- Layer 2: Dependency graph --------
        dependency_out = self.dependency.analyze(problem)
        resurrection_out = self.resurrection.analyze(problem, dependency_out)
        layers[2] = {
            "prerequisites": dependency_out["prerequisites"],
            "adjacent_technologies": dependency_out["adjacent_technologies"],
            "required_materials": dependency_out["required_materials"],
            "required_infrastructure": dependency_out["required_infrastructure"],
            "missing_capabilities": dependency_out["missing_capabilities"],
            "regulatory_constraints": dependency_out["regulatory_constraints"],
            "resurrection_opportunities": resurrection_out["resurrection_opportunities"],
            "evidence": {**dependency_out.get("evidence", {}),
                          **resurrection_out.get("evidence", {})},
            "assumptions": (dependency_out.get("assumptions", [])
                            + resurrection_out.get("assumptions", [])),
            "falsification_criteria": (
                dependency_out.get("falsification_criteria", "")
                + " || " + resurrection_out.get("falsification_criteria", "")
            ),
        }

        # -------- Layer 3: Scientific formulation --------
        math_l3 = self.mathematics.analyze_layer3(problem, physics_out)
        constraint_l3 = self.constraint.analyze_layer3(
            problem, dependency_out, physics_out)
        layers[3] = {
            "governing_equations": math_l3["governing_equations"],
            "boundary_conditions": {
                "value": None,
                "reason": "boundary conditions require problem-specific "
                          "physics analysis not yet implemented",
                "evidence": {"engine_status": "stub"},
                "assumptions": [],
                "falsification_criteria": "N/A — engine missing.",
            },
            "assumptions": constraint_l3["assumptions"],
            "failure_modes": constraint_l3["failure_modes"],
            "optimization_targets": constraint_l3["optimization_targets"],
            "evidence": {
                **math_l3.get("evidence", {}),
                **constraint_l3.get("evidence", {}),
            },
            "falsification_criteria": (
                math_l3.get("falsification_criteria", "")
                + " || " + constraint_l3.get("falsification_criteria", "")
            ),
        }

        # -------- Layer 4: Engineering architecture --------
        constraint_l4 = self.constraint.analyze_layer4(problem, constraint_l3)
        arch_out = self.architecture.analyze(
            problem, dependency_out, constraint_l4)
        layers[4] = arch_out

        # -------- Layer 5: Simulation layer --------
        sim_out = self.simulation.analyze(problem)
        layers[5] = sim_out

        # -------- Layer 6: Manufacturing layer --------
        constraint_l6 = self.constraint.analyze_layer6(problem, dependency_out)
        layers[6] = constraint_l6

        # -------- Layer 7: Economic layer --------
        # The feasibility scorer's output is needed for the econ model.
        # We use the simulation's baseline composite as the feasibility input.
        feasibility_for_econ = {
            "composite_feasibility": sim_out.get("evidence", {}).get(
                "baseline_composite", 0.5),
        }
        econ_l7 = self.economics.analyze_layer7(problem, feasibility_for_econ)
        layers[7] = econ_l7

        # -------- Layer 8: Experimental layer --------
        verification_out = self.verification.analyze(
            problem, feasibility_for_econ, sim_out, constraint_l3)
        layers[8] = verification_out

        # -------- Layer 9: Prototype layer --------
        prototype_out = self.prototype.analyze(
            problem, feasibility_for_econ, dependency_out)
        layers[9] = prototype_out

        # -------- Layer 10: Final blueprint --------
        blueprint_out = self.blueprint.analyze(problem, layers)
        layers[10] = blueprint_out

        return {
            "problem_id": problem_id,
            "timestamp": timestamp,
            "writer": "invention_compiler.orchestrator.InventionCompiler.compile",
            "problem_input": problem,
            "layers": layers,
            # Final chain summary — the answer to the directive's ultimate
            # question: "what is the next invention... and what exact
            # sequence of steps would allow someone to build it?"
            "chain_summary": self._chain_summary(layers),
        }

    def _stable_id(self, problem: Dict[str, Any]) -> str:
        """Stable hash of the problem for Law 7 replayability."""
        canonical = json.dumps(problem, sort_keys=True, default=str)
        h = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]
        return f"invention_{h}"

    def _chain_summary(self, layers: Dict[int, Dict[str, Any]]) -> Dict[str, Any]:
        """A flat summary suitable for the directive's 'ultimate question'
        output: the chain of reasoning required to build the invention."""
        return {
            "target_invention": layers[0].get("problem"),
            "domain": layers[0].get("domain"),
            "time_horizon": layers[0].get("time_horizon"),
            "prerequisite_chain_depth": layers[2].get("evidence", {}).get(
                "chain_depth", 0),
            "governing_equations_count": len(layers[3].get(
                "governing_equations", [])),
            "subsystem_count": len(layers[4].get("subsystems", [])),
            "composite_feasibility_baseline": layers[5].get("evidence", {}).get(
                "baseline_composite"),
            "capex_usd_m": layers[7].get("capex", {}).get("value_usd_m"),
            "market_size_usd_m": layers[7].get("market_size", {}).get("value_usd_m"),
            "total_prototype_timeline_years": layers[9].get("timeline", {}).get(
                "total_years"),
            "technical_risk_count": len(layers[10].get("technical_risks", [])),
            "commercial_risk_count": len(layers[10].get("commercial_risks", [])),
            "verification_status": "integrated",  # NEVER "verified" until Law 8 cycle
        }
