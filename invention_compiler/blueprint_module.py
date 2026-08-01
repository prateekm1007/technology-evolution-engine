"""
Blueprint Module — feeds Layer 10 (Final blueprint).

Composes the final blueprint from all 10 preceding layers. The blueprint
is the system's deliverable: a complete chain of reasoning that an
engineer could use to start building the invention.

Per INVENTION_COMPILER.md, the system may NEVER output "this is a good
idea." It must output the chain of reasoning. This engine enforces
that rule: its output is the chain itself, not a verdict.
"""
from typing import Dict, Any, List


class BlueprintModule:
    """Composes the final Layer 10 blueprint."""

    def __init__(self, graph: Dict[str, Any]):
        self.graph = graph

    def analyze(self, problem: Dict[str, Any],
                all_layers: Dict[int, Dict[str, Any]]) -> Dict[str, Any]:
        # The blueprint itself is a structured summary of the 10
        # preceding layers. It is NOT a verdict — it is the chain.
        blueprint = {
            "problem": all_layers[0].get("problem"),
            "domain": all_layers[0].get("domain"),
            "target_invention": problem.get("problem"),
            "prerequisite_chain_depth": all_layers[2].get("evidence", {}).get(
                "chain_depth", 0),
            "governing_equations": all_layers[3].get("governing_equations", []),
            "subsystems": all_layers[4].get("subsystems", []),
            "composite_feasibility": all_layers[7].get("capex", {}).get("value_usd_m"),
            "prototype_stages": [
                all_layers[9].get("prototype_v1", {}).get("name"),
                all_layers[9].get("prototype_v2", {}).get("name"),
                all_layers[9].get("prototype_v3", {}).get("name"),
            ],
            "total_prototype_timeline_years": all_layers[9].get(
                "timeline", {}).get("total_years"),
        }

        # Patent landscape: derived from analogy_engine's output in Layer 0.
        # We use the analogy candidates as a proxy for "what existing
        # patents might cover this space."
        patent_landscape = []
        for analogy in (all_layers[0].get("analogies", []) or [])[:5]:
            patent_landscape.append({
                "related_node": analogy.get("node_a", {}).get("label"),
                "structural_overlap": analogy.get("structural_overlap_score"),
                "note": "Structural overlap is a proxy for patent "
                         "overlap, not a substitute for a real patent search.",
            })

        # Technical risks: from constraint_engine's failure modes.
        technical_risks = all_layers[3].get("failure_modes", [])
        # Plus risks from simulation_engine's stress tests.
        stress = all_layers[5].get("stress_testing", []) or []
        for s in stress[:2]:
            technical_risks.append(
                f"stress_scenario_composite={s.get('composite')}"
            )

        # Commercial risks: from economics_engine's market size + capex.
        market_size = all_layers[7].get("market_size", {}).get("value_usd_m", 0)
        capex = all_layers[7].get("capex", {}).get("value_usd_m", 0)
        commercial_risks = []
        if market_size < 5:
            commercial_risks.append("market_size_too_small_to_justify_capex")
        if capex > market_size * 0.5:
            commercial_risks.append("capex_exceeds_half_of_market_size")
        # Adoption model risk: s_curve adoptions take longer.
        if all_layers[7].get("adoption_model") == "s_curve":
            commercial_risks.append("s_curve_adoption_extends_payback_period")
        if not commercial_risks:
            commercial_risks = ["no_structural_commercial_risks_identified"]

        # Recommended actions: ordered by dependency.
        recommended_actions = [
            "Verify the prerequisite chain is complete (Layer 2).",
            "Run the proposed experiments in Layer 8; record outcomes "
            "in the ledger per Law 8.",
            "Build prototype v1 (physics validation) per Layer 9.",
            "If v1 succeeds, commit to prototype v2 budget per Layer 7's "
            "capex estimate.",
            "Engage regulatory counsel before v3 (Layer 4's regulatory "
            "constraints + Layer 8's regulatory measurement).",
        ]

        return {
            "blueprint": blueprint,
            "patent_landscape": patent_landscape,
            "technical_risks": technical_risks,
            "commercial_risks": commercial_risks,
            "recommended_actions": recommended_actions,
            "evidence": {
                "layers_composed": 11,
                "patent_analogies_count": len(patent_landscape),
                "technical_risk_count": len(technical_risks),
                "commercial_risk_count": len(commercial_risks),
            },
            "assumptions": [
                "The blueprint is a STRUCTURED SUMMARY of the 10 preceding "
                "layers, not a separate analysis. If the layers are wrong, "
                "the blueprint is wrong.",
                "Patent landscape is proxied by structural-overlap analogies "
                "from Layer 0. Real patent landscape analysis requires a "
                "patent database.",
                "Recommended actions are generic. Real action plans require "
                "domain-specific sequencing.",
            ],
            "falsification_criteria": (
                "If an engineer cannot start building the invention from "
                "this blueprint, the blueprint is incomplete. The "
                "blueprint must be revised to fill the gap. This engine "
                "does NOT verify the blueprint is buildable — that is the "
                "verification_engine's job (Layer 8 + the verification "
                "cycle in scripts/run_verification_cycle.py)."
            ),
        }
