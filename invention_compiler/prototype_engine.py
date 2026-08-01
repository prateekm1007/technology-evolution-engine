"""
Prototype Engine — feeds Layer 9 (Prototype layer).

Proposes three prototype stages (v1, v2, v3) and a timeline. Each
prototype has a purpose, a target capability, and an estimated duration.

v1: prove the core mechanism works (physics validation).
v2: prove the architecture holds together (engineering integration).
v3: prove the manufacturing pathway is viable (production-readiness).
"""
from typing import Dict, Any, List


class PrototypeEngine:
    """Proposes a three-stage prototype plan."""

    def __init__(self, graph: Dict[str, Any]):
        self.graph = graph

    def analyze(self, problem: Dict[str, Any],
                feasibility_output: Dict[str, Any],
                dependency_output: Dict[str, Any]) -> Dict[str, Any]:
        horizon = problem.get("time_horizon", "5-10 years")

        # v1: physics validation. Goal: prove the governing equations hold.
        v1 = {
            "name": "prototype_v1_physics_validation",
            "goal": "prove the core mechanism works at lab scale",
            "scope": "single subsystem, no integration, no manufacturability",
            "success_threshold": "core mechanism reproduces predicted output "
                                 "within 30%",
            "estimated_duration_months": 6,
            "estimated_cost_usd_m": round(
                feasibility_output.get("composite_feasibility", 0.5) * 0.5, 2),
        }

        # v2: engineering integration. Goal: prove the architecture holds.
        prereq_count = len(dependency_output.get("prerequisites", []))
        v2 = {
            "name": "prototype_v2_engineering_integration",
            "goal": "prove the subsystems integrate into a working system",
            "scope": "all subsystems, no manufacturing pathway, no "
                     "regulatory submission",
            "success_threshold": "integrated prototype meets primary_output "
                                 "spec at 50% of target performance",
            "estimated_duration_months": 12 + prereq_count,
            "estimated_cost_usd_m": round(
                feasibility_output.get("composite_feasibility", 0.5) * 2.0, 2),
        }

        # v3: production-readiness. Goal: prove manufacturability + cost.
        v3 = {
            "name": "prototype_v3_production_readiness",
            "goal": "prove the manufacturing pathway and cost model hold",
            "scope": "production-intent prototype, pilot manufacturing run, "
                     "regulatory pre-submission",
            "success_threshold": "unit cost within 2x of cost_curve target; "
                                 "regulatory pre-submission accepted",
            "estimated_duration_months": 18 + prereq_count * 2,
            "estimated_cost_usd_m": round(
                feasibility_output.get("composite_feasibility", 0.5) * 8.0, 2),
        }

        # Timeline: sum of the three phases, expressed in the problem's
        # time horizon if it matches.
        total_months = (v1["estimated_duration_months"]
                        + v2["estimated_duration_months"]
                        + v3["estimated_duration_months"])
        years = total_months / 12
        timeline = {
            "total_months": total_months,
            "total_years": round(years, 1),
            "fits_within_horizon": self._fits(horizon, years),
            "phases": [
                {"phase": "v1", "start_month": 0,
                 "end_month": v1["estimated_duration_months"]},
                {"phase": "v2", "start_month": v1["estimated_duration_months"],
                 "end_month": v1["estimated_duration_months"]
                              + v2["estimated_duration_months"]},
                {"phase": "v3",
                 "start_month": v1["estimated_duration_months"]
                                 + v2["estimated_duration_months"],
                 "end_month": total_months},
            ],
        }

        return {
            "prototype_v1": v1,
            "prototype_v2": v2,
            "prototype_v3": v3,
            "timeline": timeline,
            "evidence": {
                "feasibility_composite_used": feasibility_output.get(
                    "composite_feasibility", 0.5),
                "prerequisite_count": prereq_count,
                "horizon": horizon,
            },
            "assumptions": [
                "Prototype stages follow the canonical physics -> "
                "engineering -> manufacturing progression. Real projects "
                "sometimes collapse v1+v2 or skip v3 entirely depending "
                "on funding.",
                "Estimated durations scale with prerequisite count — more "
                "prerequisites means more integration risk, so v2 and v3 "
                "take longer. This is a coarse linear prior.",
                "Cost estimates scale with composite feasibility — higher "
                "feasibility means lower cost (proven tech stack). This "
                "is the same prior as the economics engine's capex model.",
            ],
            "falsification_criteria": (
                "If a real prototype program for the candidate takes more "
                "than 2x the estimated duration, the duration prior is "
                "wrong and must be recalibrated. Sample size: >= 5 "
                "comparable prototype programs."
            ),
        }

    def _fits(self, horizon: str, years: float) -> bool:
        """Check if the timeline fits within the stated horizon."""
        if "0-2" in horizon:
            return years <= 2
        if "2-5" in horizon:
            return years <= 5
        if "5-10" in horizon:
            return years <= 10
        if "10-15" in horizon:
            return years <= 15
        return True  # unknown horizon -> assume yes
