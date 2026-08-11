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

from .analogy_module import AnalogyModule
from .physics_knowledge_module import PhysicsKnowledgeModule
from .chemistry_knowledge_module import ChemistryKnowledgeModule
from .biology_knowledge_module import BiologyKnowledgeModule
from .mathematics_knowledge_module import MathematicsKnowledgeModule
from .economics_knowledge_module import EconomicsKnowledgeModule
from .constraint_module import ConstraintModule
from .architecture_module import ArchitectureModule
from .simulation_module import SimulationModule
from .dependency_module import DependencyModule
from .resurrection_module import ResurrectionModule
from .verification_engine import VerificationEngine
from .prototype_module import PrototypeModule
from .blueprint_module import BlueprintModule


class InventionCompiler:
    """Runs the 11-layer invention compilation pipeline.

    Construction:
        graph: the civilization graph dict (JSON-loaded). Decoupled
               per ANTI_ENTROPY.md rule 'Decouple modules'.
    """

    def __init__(self, graph: Dict[str, Any]):
        self.graph = graph
        # Instantiate every module once. Decoupled per anti-entropy rule.
        # Per the CTO review, only verification_engine is a true "engine";
        # the rest are modules doing keyword matching until they earn
        # the "engine" name by satisfying: explicit model + empirical
        # validation + reproducible results.
        self.analogy = AnalogyModule(graph)
        self.physics = PhysicsKnowledgeModule(graph)
        self.chemistry = ChemistryKnowledgeModule(graph)
        self.biology = BiologyKnowledgeModule(graph)
        self.mathematics = MathematicsKnowledgeModule(graph)
        self.economics = EconomicsKnowledgeModule(graph)
        self.constraint = ConstraintModule(graph)
        self.architecture = ArchitectureModule(graph)
        self.simulation = SimulationModule(graph)
        self.dependency = DependencyModule(graph)
        self.resurrection = ResurrectionModule(graph)
        self.verification = VerificationEngine(graph)
        self.prototype = PrototypeModule(graph)
        self.blueprint = BlueprintModule(graph)

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
        output: the chain of reasoning required to build the invention.

        Per CTO review #4, the summary must carry a claim/confidence/
        evidence triple (a Hypothesis), not a bare composite scalar.
        The composite_feasibility_baseline becomes the `confidence`
        of an explicit `claim` about the invention's feasibility.
        """
        # Compute the composite feasibility from Layer 5's evidence.
        composite = layers[5].get("evidence", {}).get(
            "baseline_composite")
        # Build the evidence list for the headline hypothesis.
        # It draws from multiple layers — each layer's output contributes
        # named evidence to the headline claim.
        evidence = []
        # Layer 1 physics laws
        evidence.extend(layers[1].get("physics", {}).get("applicable_laws", []))
        # Layer 1 chemistry pathways
        evidence.extend(layers[1].get("chemistry", {}).get(
            "applicable_pathways", []))
        # Layer 3 governing equations
        for eq in layers[3].get("governing_equations", []):
            if isinstance(eq, dict) and "name" in eq:
                evidence.append(eq["name"])
        # Layer 2 prerequisite count (as a named piece of evidence)
        prereq_count = layers[2].get("evidence", {}).get("prerequisite_count", 0)
        if prereq_count > 0:
            evidence.append(f"prerequisite_chain_depth_{layers[2].get('evidence', {}).get('chain_depth', 0)}")
        # Layer 7 capex (as a named piece of evidence)
        capex = layers[7].get("capex", {}).get("value_usd_m")
        if capex is not None:
            evidence.append(f"capex_${capex}M")

        # GAP 4 FIX: Build the counterevidence list for the headline
        # hypothesis. Before this fix, counterevidence was always empty
        # — the system was an optimism engine. Now we pull counterevidence
        # from multiple layers that identify risks, failure modes, and
        # stress scenarios.
        counterevidence = []
        # Layer 3: failure modes (e.g., cost_overrun, regulatory_rejection)
        for fm in layers[3].get("failure_modes", []):
            counterevidence.append(f"failure_mode: {fm}")
        # Layer 5: stress testing (worst-case composites below 0.4)
        for s in (layers[5].get("stress_testing") or [])[:3]:
            comp = s.get("composite")
            if comp is not None and comp < 0.40:
                counterevidence.append(
                    f"stress_scenario: composite={comp:.4f} (below 0.40)")
        # Layer 10: technical risks (failure modes + stress composites)
        for tr in layers[10].get("technical_risks", []):
            if tr not in layers[3].get("failure_modes", []):
                counterevidence.append(f"technical_risk: {tr}")
        # Layer 10: commercial risks
        for cr in layers[10].get("commercial_risks", []):
            if cr != "no_structural_commercial_risks_identified":
                counterevidence.append(f"commercial_risk: {cr}")

        # Build the headline Hypothesis. Per the CTO review #4 rule,
        # every assertion carries claim/confidence/evidence.
        target = layers[0].get("problem", "the candidate invention")
        domain = layers[0].get("domain", "unknown")
        if composite is not None:
            claim = (
                f"The invention '{target}' is feasible in the {domain} domain "
                f"within the stated time horizon."
            )
            confidence = round(float(composite), 4)
        else:
            claim = (
                f"The invention '{target}' has indeterminate feasibility — "
                f"the compiler did not produce a composite score."
            )
            confidence = 0.0

        # Use the Hypothesis class for the structured representation.
        try:
            from hypothesis.hypothesis import Hypothesis
            headline_hypothesis = Hypothesis(
                claim=claim,
                confidence=confidence,
                evidence=evidence,
                counterevidence=counterevidence,
                writer="invention_compiler.orchestrator.InventionCompiler._chain_summary",
            )
            hypothesis_block = headline_hypothesis.to_dict()
        except Exception:
            # If the hypothesis package is unavailable for any reason,
            # fall back to a dict. This should not happen in normal
            # operation, but we don't want a hypothesis-package bug
            # to break the entire compiler.
            hypothesis_block = {
                "claim": claim,
                "confidence": confidence,
                "evidence": evidence,
                "counterevidence": counterevidence,
                "status": "pending",
                "writer": "invention_compiler.orchestrator.InventionCompiler._chain_summary",
            }

        return {
            "target_invention": layers[0].get("problem"),
            "domain": layers[0].get("domain"),
            "time_horizon": layers[0].get("time_horizon"),
            "prerequisite_chain_depth": layers[2].get("evidence", {}).get(
                "chain_depth", 0),
            "governing_equations_count": len(layers[3].get(
                "governing_equations", [])),
            "subsystem_count": len(layers[4].get("subsystems", [])),
            "composite_feasibility_baseline": composite,
            "capex_usd_m": capex,
            "market_size_usd_m": layers[7].get("market_size", {}).get("value_usd_m"),
            "total_prototype_timeline_years": layers[9].get("timeline", {}).get(
                "total_years"),
            "technical_risk_count": len(layers[10].get("technical_risks", [])),
            "commercial_risk_count": len(layers[10].get("commercial_risks", [])),
            "verification_status": "integrated",  # NEVER "verified" until Law 8 cycle
            # CTO review #4: the headline hypothesis. Every chain_summary
            # carries this — no bare composite scalar without an
            # explicit claim and evidence.
            "hypothesis": hypothesis_block,
        }
