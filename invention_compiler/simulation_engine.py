"""
Simulation Engine — feeds Layer 5 (Simulation layer).

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


class SimulationEngine:
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
        baseline_d = baseline.to_dict()

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
                "baseline_composite": baseline_d["composite_feasibility"],
                "baseline_technical": baseline_d["technical_feasibility"],
                "target_node_id": target_node_id,
                "rng_seed": 42,
                "n_samples": n_samples,
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
