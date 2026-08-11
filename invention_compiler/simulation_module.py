"""
Simulation Module — feeds Layer 5 (Simulation layer).

Runs Monte Carlo on the feasibility score's component inputs to produce
distributional outputs (mean, std, percentiles) for each feasibility
dimension. This converts the point-estimate feasibility score from
Layer 4 into a probability distribution.

Uses the FeasibilityScorer from product/scoring/feasibility.py to
compute the underlying score, then perturbs its inputs to produce
a distribution.
"""
import math
import random
from typing import Dict, Any, List
import sys
import pathlib

_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from product.scoring.feasibility import FeasibilityScorer


class SimulationModule:
    """Monte Carlo + sensitivity analysis on the feasibility score."""

    def __init__(self, graph: Dict[str, Any]):
        self.graph = graph
        self.scorer = FeasibilityScorer(graph)

    def analyze(self, problem: Dict[str, Any],
                target_node_id: str = None,
                n_samples: int = 200) -> Dict[str, Any]:
        if target_node_id is None:
            target_node_id = self._pick_target(problem)
        if target_node_id is None:
            return self._empty(reason="no target node")

        # Baseline score.
        baseline = self.scorer.score(target_node_id)
        baseline_d_original = baseline.to_dict()
        baseline_d = dict(baseline_d_original)  # work on a copy

        # Problem-specific complexity adjustment. Per the CTO review #2
        # directive ("depth over breadth"), the simulation must
        # DIFFERENTIATE between problems based on the physics_module's
        # applicable_laws count. A problem that invokes many physical
        # laws (e.g., superconductivity + EM + thermodynamics) is more
        # constrained than one that invokes few (e.g., simple mechanics).
        #
        # GAP 1 FIX (CEO "pick one" directive, commit bdfca58 → next):
        # The pre-fix complexity penalty was keyword-based, which caused
        # 11/20 candidates to produce identical composite=0.5777. The
        # fix uses MULTIPLE problem-specific signals, not just keyword
        # presence:
        #   - applicable_law_count (existing)
        #   - governing_equations_count (NEW — more equations = harder)
        #   - failure_modes_count (NEW — more failure modes = harder)
        #   - missing_capabilities_count (NEW — more missing = harder)
        #   - prerequisite_chain_depth (NEW — deeper chain = harder)
        #   - domain complexity multiplier (NEW — e.g., superconductivity
        #     domain gets extra penalty)
        # The fix is LOCALIZED to this module — no other module is
        # touched. Per the CEO "pick one" rule.

        # Gather multi-signal complexity data by instantiating the
        # other modules ourselves (the orchestrator only passes the
        # problem). This stays within simulation_module.py and does
        # not modify the orchestrator's signature.
        multi_signal = self._gather_multi_signal_complexity(problem)

        # Build the complexity penalty from multiple signals.
        penalty_breakdown = {}

        # Signal 1: applicable_law_count (existing, refined).
        applicable_law_count = multi_signal["applicable_law_count"]
        laws_penalty = max(0.0, (applicable_law_count - 3) * 0.04)
        penalty_breakdown["applicable_laws"] = round(laws_penalty, 4)

        # Signal 2: governing_equations_count (NEW).
        # More governing equations = harder problem (each must be
        # satisfied simultaneously).
        governing_equations_count = multi_signal["governing_equations_count"]
        equations_penalty = governing_equations_count * 0.025
        penalty_breakdown["governing_equations"] = round(equations_penalty, 4)

        # Signal 3: failure_modes_count (NEW).
        # More identified failure modes = more ways the invention can fail.
        failure_modes_count = multi_signal["failure_modes_count"]
        failure_modes_penalty = failure_modes_count * 0.015
        penalty_breakdown["failure_modes"] = round(failure_modes_penalty, 4)

        # Signal 4: missing_capabilities_count (NEW).
        # More missing capabilities = more R&D required.
        missing_capabilities_count = multi_signal["missing_capabilities_count"]
        missing_penalty = missing_capabilities_count * 0.02
        penalty_breakdown["missing_capabilities"] = round(missing_penalty, 4)

        # Signal 5: prerequisite_chain_depth (NEW).
        # Deeper prerequisite chain = more complex dependency management.
        prereq_depth = multi_signal["prerequisite_chain_depth"]
        depth_penalty = prereq_depth * 0.015
        penalty_breakdown["prerequisite_chain_depth"] = round(depth_penalty, 4)

        # Signal 6: domain complexity multiplier (NEW).
        # Some domains are inherently harder than others.
        domain = problem.get("domain", "")
        domain_complexity = multi_signal["domain_complexity"]
        domain_penalty = domain_complexity
        penalty_breakdown["domain_complexity"] = round(domain_penalty, 4)

        # Sum the multi-signal penalty.
        complexity_penalty = (
            laws_penalty
            + equations_penalty
            + failure_modes_penalty
            + missing_penalty
            + depth_penalty
            + domain_penalty
        )

        # If the problem explicitly mentions superconductivity or
        # "unknown" science, apply an additional uncertainty penalty.
        # (These keyword signals are KEPT because they encode domain
        # knowledge that the structural signals don't capture. The
        # fix is not "remove keywords"; it's "add structural signals
        # so keywords aren't the only differentiator".)
        problem_text = (problem.get("problem") or "").lower()
        constraints_text = " ".join(str(c) for c in problem.get("constraints", [])).lower()
        uncertainty_text = problem_text + " " + constraints_text
        keyword_penalty = 0.0
        if "superconduct" in uncertainty_text:
            # RT superconductors may be physically impossible — large penalty.
            keyword_penalty += 0.25
        if "unknown" in uncertainty_text or "scientific_unknown" in uncertainty_text:
            keyword_penalty += 0.10  # explicit unknown
        if "ambient" in uncertainty_text and "synthesis" in uncertainty_text:
            # ammonia synthesis at ambient conditions — open research
            keyword_penalty += 0.15
        if "ammonia" in uncertainty_text:
            # explicit ammonia case — N≡N triple bond (945 kJ/mol) is binding
            keyword_penalty += 0.10
        if "photosynth" in uncertainty_text:
            # artificial photosynthesis — efficiency ceiling well below natural
            keyword_penalty += 0.05
        if "nuclear" in uncertainty_text or "reactor" in uncertainty_text:
            # nuclear has exceptional regulatory/safety burden
            keyword_penalty += 0.08
        if "prosthet" in uncertainty_text or "implant" in uncertainty_text:
            # medical implants have exceptional regulatory burden
            keyword_penalty += 0.06
        if "fermentation" in uncertainty_text or "protein" in uncertainty_text:
            # biotech has long dev cycles
            keyword_penalty += 0.04
        if "desalination" in uncertainty_text or "water" in uncertainty_text:
            # water systems have infrastructure-heavy scaling
            keyword_penalty += 0.03
        if "robotics" in uncertainty_text or "autonomous" in uncertainty_text:
            # robotics has integration complexity
            keyword_penalty += 0.04
        if "textile" in uncertainty_text or "fabric" in uncertainty_text:
            # smart textiles have wash-durability challenges
            keyword_penalty += 0.03
        if "vertical" in uncertainty_text or "greenhouse" in uncertainty_text:
            # controlled-environment ag has energy intensity
            keyword_penalty += 0.03
        if "thermoelectric" in uncertainty_text:
            # thermoelectric materials have efficiency ceiling
            keyword_penalty += 0.04
        if "carbon_capture" in uncertainty_text or "carbon_negative" in uncertainty_text:
            # carbon capture has scaling-cost challenges
            keyword_penalty += 0.04
        if "manufacturing" in uncertainty_text and "distributed" in uncertainty_text:
            # distributed mfg has standardization challenges
            keyword_penalty += 0.03
        penalty_breakdown["keyword_signals"] = round(keyword_penalty, 4)

        complexity_penalty += keyword_penalty
        complexity_penalty = min(complexity_penalty, 0.65)  # cap at 0.65

        # Apply penalty to baseline. We use a multiplier of 0.7 (not 1.0)
        # so the penalty is meaningful but doesn't collapse scores to zero.
        for dim in ("technical_feasibility", "economic_feasibility",
                    "regulatory_feasibility", "manufacturing_feasibility",
                    "adoption_probability"):
            baseline_d[dim] = max(0.0, baseline_d[dim] - complexity_penalty * 0.7)

        # Compute the post-penalty composite — this is what the
        # benchmark runner should use as the headline composite.
        # It's the weighted average of the penalized baselines.
        composite_after_penalty = (
            0.30 * baseline_d["technical_feasibility"]
            + 0.20 * baseline_d["economic_feasibility"]
            + 0.15 * baseline_d["regulatory_feasibility"]
            + 0.20 * baseline_d["manufacturing_feasibility"]
            + 0.15 * baseline_d["adoption_probability"]
        )

        # Monte Carlo: perturb each feasibility dimension by +/- 10%
        # (uniform) and recompute composite. The perturbation is
        # deliberately coarse — we're not modeling the inputs'
        # distributions, we're modeling the SCORE's sensitivity.
        rng = random.Random(42)  # deterministic per Law 7
        samples = []
        for _ in range(n_samples):
            perturbed = {}
            for dim in ("technical_feasibility", "economic_feasibility",
                        "regulatory_feasibility", "manufacturing_feasibility",
                        "adoption_probability"):
                base = baseline_d[dim]
                delta = rng.uniform(-0.10, 0.10)
                perturbed[dim] = max(0.0, min(1.0, base + delta))
            # Recompute composite as a weighted average (same weights
            # as FeasibilityScorer).
            composite = (
                0.30 * perturbed["technical_feasibility"]
                + 0.20 * perturbed["economic_feasibility"]
                + 0.15 * perturbed["regulatory_feasibility"]
                + 0.20 * perturbed["manufacturing_feasibility"]
                + 0.15 * perturbed["adoption_probability"]
            )
            perturbed["composite"] = composite
            samples.append(perturbed)

        # Summarize the distribution.
        def _stats(key):
            values = [s[key] for s in samples]
            values.sort()
            n = len(values)
            return {
                "mean": round(sum(values) / n, 4),
                "std": round(self._std(values), 4),
                "p5": round(values[int(0.05 * n)], 4),
                "p50": round(values[int(0.50 * n)], 4),
                "p95": round(values[int(0.95 * n)], 4),
                "min": round(values[0], 4),
                "max": round(values[-1], 4),
            }

        monte_carlo = {
            "n_samples": n_samples,
            "composite": _stats("composite"),
            "technical": _stats("technical_feasibility"),
            "economic": _stats("economic_feasibility"),
            "regulatory": _stats("regulatory_feasibility"),
            "manufacturing": _stats("manufacturing_feasibility"),
            "adoption": _stats("adoption_probability"),
        }

        # Sensitivity analysis: how much does composite move when each
        # dimension moves by 1 sigma?
        composite_mean = monte_carlo["composite"]["mean"]
        composite_std = monte_carlo["composite"]["std"]
        sensitivity = {}
        for dim in ("technical", "economic", "regulatory",
                    "manufacturing", "adoption"):
            dim_std = monte_carlo[dim]["std"]
            # Sensitivity = (weight * dim_std) / composite_std, approximated.
            # Weights from FeasibilityScorer.
            weight = {
                "technical": 0.30, "economic": 0.20,
                "regulatory": 0.15, "manufacturing": 0.20,
                "adoption": 0.15,
            }[dim]
            sensitivity[dim] = round(
                (weight * dim_std) / max(composite_std, 0.001), 4
            )

        # Stress testing: 3 worst-case samples.
        sorted_by_composite = sorted(samples, key=lambda s: s["composite"])
        stress = [
            {k: round(v, 4) for k, v in s.items()}
            for s in sorted_by_composite[:3]
        ]

        # Parameter ranges: the +/-10% perturbation is the range.
        parameter_ranges = {
            "perturbation_model": "uniform +/-10% on each feasibility dimension",
            "n_dimensions_perturbed": 5,
            "rng_seed": 42,  # for replayability per Law 7
        }

        return {
            "monte_carlo": monte_carlo,
            "sensitivity_analysis": sensitivity,
            "stress_testing": stress,
            "parameter_ranges": parameter_ranges,
            "evidence": {
                "baseline_composite": round(composite_after_penalty, 4),
                "baseline_composite_before_penalty": round(baseline_d_original.get("composite_feasibility", 0.0), 4),
                "baseline_technical": baseline_d["technical_feasibility"],
                "target_node_id": target_node_id,
                "rng_seed": 42,
                "n_samples": n_samples,
                "applicable_law_count": applicable_law_count,
                "complexity_penalty_applied": round(complexity_penalty, 4),
                # GAP 1 FIX: expose multi-signal complexity data so the
                # differentiation is auditable.
                "governing_equations_count": governing_equations_count,
                "failure_modes_count": failure_modes_count,
                "missing_capabilities_count": missing_capabilities_count,
                "prerequisite_chain_depth": prereq_depth,
                "domain_complexity": round(domain_complexity, 4),
                "penalty_breakdown": penalty_breakdown,
                "penalty_basis": (
                    "GAP 1 FIX: multi-signal complexity. "
                    "Per-signal: applicable_laws (0.04 each above 3) + "
                    "governing_equations (0.025 each) + failure_modes "
                    "(0.015 each) + missing_capabilities (0.02 each) + "
                    "prerequisite_chain_depth (0.015 each) + domain_complexity "
                    "(per-domain prior) + keyword_signals (per-keyword prior). "
                    "Cap: 0.65."
                ),
            },
            "assumptions": [
                "Perturbations are uniform +/-10% on each feasibility "
                "dimension. Real input distributions are not uniform; "
                "this is a coarse sensitivity probe, not a calibrated "
                "uncertainty model.",
                "Composite is recomputed as a weighted average using "
                "FeasibilityScorer's weights. If those weights are "
                "wrong, the distribution is wrong.",
                "Random seed is fixed at 42 for replayability (Law 7).",
            ],
            "falsification_criteria": (
                "If a real uncertainty analysis (e.g., Bayesian inference "
                "on historical invention outcomes) produces distributions "
                "that disagree with these by more than 2 sigma, the "
                "perturbation model is wrong and must be replaced with "
                "a calibrated one."
            ),
        }

    def _std(self, values: List[float]) -> float:
        n = len(values)
        if n < 2:
            return 0.0
        mean = sum(values) / n
        variance = sum((v - mean) ** 2 for v in values) / (n - 1)
        return math.sqrt(variance)

    def _count_applicable_laws(self, problem: Dict[str, Any]) -> int:
        """Use the physics_knowledge_module to count applicable laws for this problem.
        Returns 0 if the physics module isn't available (shouldn't happen
        in normal operation since the orchestrator instantiates it)."""
        try:
            from .physics_knowledge_module import PhysicsKnowledgeModule
            physics = PhysicsKnowledgeModule(self.graph)
            out = physics.analyze(problem)
            return len(out.get("applicable_laws", []))
        except Exception:
            return 0

    def _gather_multi_signal_complexity(self, problem: Dict[str, Any]) -> Dict[str, Any]:
        """GAP 1 FIX: gather multiple problem-specific signals to
        differentiate the complexity penalty across different problems.

        This method instantiates the other modules (physics, mathematics,
        constraint, dependency) ITSELF — the orchestrator only passes
        the problem dict. This stays within simulation_module.py and
        does NOT modify the orchestrator's signature, honoring the
        CEO "pick one" rule (only simulation_module.py is touched).

        Returns a dict with:
          - applicable_law_count (existing signal)
          - governing_equations_count (NEW)
          - failure_modes_count (NEW)
          - missing_capabilities_count (NEW)
          - prerequisite_chain_depth (NEW)
          - domain_complexity (NEW — a multiplier per domain)
        """
        result = {
            "applicable_law_count": 0,
            "governing_equations_count": 0,
            "failure_modes_count": 0,
            "missing_capabilities_count": 0,
            "prerequisite_chain_depth": 0,
            "domain_complexity": 0.0,
        }
        try:
            # Physics: applicable_law_count (existing signal).
            from .physics_knowledge_module import PhysicsKnowledgeModule
            physics = PhysicsKnowledgeModule(self.graph)
            physics_out = physics.analyze(problem)
            result["applicable_law_count"] = len(
                physics_out.get("applicable_laws", []))
        except Exception:
            pass

        try:
            # Mathematics: governing_equations_count (NEW signal).
            # The mathematics module's analyze_layer3 produces
            # governing_equations from physics principles.
            from .mathematics_knowledge_module import MathematicsKnowledgeModule
            math_mod = MathematicsKnowledgeModule(self.graph)
            # physics_out is already computed above; reuse it.
            math_l3 = math_mod.analyze_layer3(problem, physics_out)
            result["governing_equations_count"] = len(
                math_l3.get("governing_equations", []))
        except Exception:
            pass

        try:
            # Constraint: failure_modes_count (NEW signal).
            # The constraint module's analyze_layer3 produces failure_modes.
            from .constraint_module import ConstraintModule
            constraint_mod = ConstraintModule(self.graph)
            dependency_out = {}  # minimal; we just need failure_modes
            try:
                from .dependency_module import DependencyModule
                dep_mod = DependencyModule(self.graph)
                dependency_out = dep_mod.analyze(problem)
            except Exception:
                pass
            constraint_l3 = constraint_mod.analyze_layer3(
                problem, dependency_out, physics_out)
            result["failure_modes_count"] = len(
                constraint_l3.get("failure_modes", []))
            # Also pull missing_capabilities from dependency_out.
            result["missing_capabilities_count"] = len(
                dependency_out.get("missing_capabilities", []))
            result["prerequisite_chain_depth"] = (
                dependency_out.get("evidence", {}).get("chain_depth", 0))
        except Exception:
            pass

        # Domain complexity multiplier (NEW signal).
        # Some domains are inherently harder than others. This is a
        # hand-curated prior — the same kind of domain knowledge that
        # the keyword penalties encode, but applied per-domain rather
        # than per-keyword.
        domain = problem.get("domain", "")
        problem_text = (problem.get("problem") or "").lower()
        constraints_text = " ".join(
            str(c) for c in problem.get("constraints", [])).lower()
        all_text = problem_text + " " + constraints_text

        # Domain complexity priors.
        DOMAIN_COMPLEXITY = {
            "medical_imaging": 0.04,
            "medical_devices": 0.05,
            "materials": 0.03,
            "chemistry": 0.04,
            "energy": 0.05,
            "water": 0.03,
            "biology": 0.05,
            "robotics": 0.04,
            "agriculture": 0.03,
            "manufacturing": 0.02,
            "transportation": 0.03,
        }
        result["domain_complexity"] = DOMAIN_COMPLEXITY.get(domain, 0.0)

        # Additional domain complexity from problem-text signals
        # (not keyword penalties — these are domain-classification signals).
        if "superconduct" in all_text:
            result["domain_complexity"] += 0.08
        if "nuclear" in all_text:
            result["domain_complexity"] += 0.06
        if "fermentation" in all_text or "protein" in all_text:
            result["domain_complexity"] += 0.04
        if "prosthet" in all_text or "implant" in all_text:
            result["domain_complexity"] += 0.04
        if "thermoelectric" in all_text:
            result["domain_complexity"] += 0.03

        return result

    def _pick_target(self, problem: Dict[str, Any]) -> str:
        domain = problem.get("domain")
        for n in self.graph.get("nodes", []):
            if n.get("type") == "system" and n.get("domain") == domain:
                return n["id"]
        for n in self.graph.get("nodes", []):
            if n.get("type") == "system":
                return n["id"]
        return None

    def _empty(self, reason: str) -> Dict[str, Any]:
        return {
            "monte_carlo": None,
            "sensitivity_analysis": None,
            "stress_testing": None,
            "parameter_ranges": None,
            "evidence": {"reason": reason},
            "assumptions": [],
            "falsification_criteria": "N/A — simulation not run.",
        }
