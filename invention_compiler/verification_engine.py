"""
Verification Engine — feeds Layer 8 (Experimental layer).

This is the loop that closes the invention compiler. Per
INVENTION_COMPILER.md, it must be promoted to a first-class module.
It currently exists as scripts/run_verification_cycle.py and
scripts/enforce_law8.py — those are the operational scripts; this
module is the in-pipeline version that proposes experiments.

Law 8 honesty: this engine's outputs are PREDICTIONS about whether
the candidate invention will pass an experiment. They are NOT
verified until the experiment is run and the outcome recorded in
the ledger.

Output contract (Layer 8):
  {
    "hypothesis": str,
    "experiments": [ {...} ],
    "measurements": [ {...} ],
    "success_criteria": [ str ],
    "failure_criteria": [ str ],
    "evidence": {...},
    "assumptions": [...],
    "falsification_criteria": str
  }
"""
from typing import Dict, Any, List


class VerificationEngine:
    """Proposes experiments and success/failure criteria for a
    candidate invention."""

    def __init__(self, graph: Dict[str, Any]):
        self.graph = graph

    def analyze(self, problem: Dict[str, Any],
                feasibility_output: Dict[str, Any],
                simulation_output: Dict[str, Any],
                constraint_layer3: Dict[str, Any]) -> Dict[str, Any]:
        # Hypothesis: the candidate invention is feasible within the
        # stated time horizon, at the composite feasibility score
        # produced by Layer 4 / Layer 5.
        composite = feasibility_output.get("composite_feasibility", 0.5)
        horizon = problem.get("time_horizon", "unknown")
        hypothesis = (
            f"The candidate invention will achieve technical feasibility "
            f">= 0.70 within {horizon}, given the prerequisite chain is "
            f"complete and no regulatory blocker materializes."
        )

        # Experiments: one per failure mode identified in Layer 3.
        failure_modes = constraint_layer3.get("failure_modes", [])
        experiments = []
        for fm in failure_modes[:5]:  # cap at 5 for readability
            experiments.append({
                "id": f"exp_{fm}",
                "purpose": f"determine whether {fm} is a real risk",
                "method": f"stress_test_against_{fm}",
                "expected_duration": "3-6 months per experiment",
            })
        # Always include one "build-it-and-see" prototype experiment.
        experiments.append({
            "id": "exp_prototype_v1",
            "purpose": "determine whether the candidate can be built at all",
            "method": "build_minimum_viable_prototype",
            "expected_duration": "6-12 months",
        })

        # Measurements: the metrics we'd track to falsify the hypothesis.
        measurements = [
            {"metric": "technical_feasibility_observed",
             "target": ">= 0.70",
             "instrument": "expert_panel_review"},
            {"metric": "cost_per_unit_observed",
             "target": "<= capex_estimate / 1000",
             "instrument": "cost_accounting"},
            {"metric": "time_to_first_prototype_observed",
             "target": f"<= {horizon}",
             "instrument": "project_tracker"},
            {"metric": "regulatory_approval_status",
             "target": "approved_or_withdrawn",
             "instrument": "regulatory_filing_tracker"},
        ]

        # Success criteria: the conditions under which the hypothesis
        # is supported.
        success_criteria = [
            "All failure-mode experiments return 'risk_acceptable'.",
            "Prototype v1 builds successfully and meets primary_output spec.",
            f"Technical feasibility observed >= 0.70 within {horizon}.",
            "Composite feasibility from simulation's p50 >= 0.60.",
        ]

        # Failure criteria: the conditions under which the hypothesis
        # is falsified (NOT the same as "the experiment failed" — that
        # is information; this is the falsification threshold).
        failure_criteria = [
            "Any failure-mode experiment returns 'risk_unacceptable' "
            "AND no mitigation is identified.",
            "Prototype v1 cannot be built within 2x the estimated time.",
            f"Technical feasibility observed < 0.40 after {horizon}.",
            "Regulatory approval is denied with no appeal path.",
        ]

        return {
            "hypothesis": hypothesis,
            "experiments": experiments,
            "measurements": measurements,
            "success_criteria": success_criteria,
            "failure_criteria": failure_criteria,
            "evidence": {
                "feasibility_composite_used": composite,
                "failure_modes_addressed": len(failure_modes),
                "simulation_p50_composite": (
                    simulation_output.get("monte_carlo", {}).get("composite", {})
                    .get("p50") if simulation_output.get("monte_carlo") else None
                ),
            },
            "assumptions": [
                "The hypothesis is a prediction. It is NOT verified until "
                "the experiments are run and outcomes recorded in the ledger.",
                "Failure-mode experiments are derived from Layer 3's failure "
                "modes. If Layer 3 is incomplete, this layer is incomplete.",
                "Success/failure thresholds (0.70, 0.40) are priors. They "
                "should be recalibrated as the verification cycle accumulates "
                "outcomes.",
            ],
            "falsification_criteria": (
                "If the candidate passes the success_criteria but the "
                "invention fails to achieve commercial adoption within "
                "the stated time horizon, the success criteria are too "
                "lenient and must be tightened. Sample size for "
                "recalibration: >= 10 verified inventions."
            ),
        }
