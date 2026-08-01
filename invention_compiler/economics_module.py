"""
Economics Module — feeds Layer 1 (economics) AND Layer 7 (Economic layer).

Layer 1: identifies economic structure (cost curves, market shape,
adoption dynamics) from the graph's industry nodes.

Layer 7: produces capex/opex estimates, market size, adoption model.
"""
from typing import Dict, Any, List


class EconomicsModule:
    """Produces economic estimates for a candidate invention."""

    # Industry-node counts -> market-size multiplier (a coarse prior).
    # 0 industries in domain -> tiny market; >=5 -> large.
    MARKET_SIZE_BUCKETS = [
        (0, 1.0),    # niche; ~$1M
        (1, 5.0),    # small; ~$5M
        (2, 20.0),   # medium; ~$20M
        (5, 100.0),  # large; ~$100M
        (10, 1000.0),# huge; ~$1B
    ]

    def __init__(self, graph: Dict[str, Any]):
        self.graph = graph
        self.nodes = graph.get("nodes", [])
        self.edges = graph.get("edges", [])

    def _industries_in_domain(self, domain: str) -> List[Dict[str, Any]]:
        return [
            n for n in self.nodes
            if n.get("type") == "industry" and (
                n.get("domain") == domain or domain is None
            )
        ]

    def analyze_layer1(self, problem: Dict[str, Any]) -> Dict[str, Any]:
        """Layer 1: economic structure of the problem's domain."""
        domain = problem.get("domain")
        industries = self._industries_in_domain(domain)
        # Adoption model prior: short time-horizon tech (consumer) follows
        # Bass diffusion; long-horizon (industrial) follows S-curve.
        horizon = problem.get("time_horizon", "")
        if "0-2" in horizon or "2-5" in horizon:
            adoption = "bass_diffusion"
        else:
            adoption = "s_curve"
        return {
            "market_structure": {
                "industries_in_domain": len(industries),
                "adoption_model_prior": adoption,
            },
            "evidence": {
                "domain": domain,
                "industry_nodes_found": len(industries),
            },
            "assumptions": [
                "Market structure is approximated by counting industry nodes "
                "in the graph. This is a proxy, not a market study.",
                "Adoption model is inferred from the time horizon, not from "
                "actual customer-segment data.",
            ],
            "falsification_criteria": (
                "If a market study for the problem's domain reports a "
                "market size or adoption curve inconsistent with this "
                "engine's output, the priors are wrong."
            ),
        }

    def analyze_layer7(self, problem: Dict[str, Any],
                       feasibility_output: Dict[str, Any]) -> Dict[str, Any]:
        """Layer 7: capex/opex/market/adoption estimates.

        Inputs:
          - problem (Layer 0)
          - feasibility_output (Layer 4's evidence, used to scale capex)
        """
        domain = problem.get("domain")
        industries = self._industries_in_domain(domain)

        # Market size: bucket by industry count.
        n = len(industries)
        market_size_usd_m = 1.0
        for threshold, mult in self.MARKET_SIZE_BUCKETS:
            if n >= threshold:
                market_size_usd_m = mult

        # Capex scales with composite feasibility — high feasibility
        # means lower capex (proven tech stack).
        composite = feasibility_output.get("composite_feasibility", 0.5)
        # Capex range: $1M (composite=1.0) to $50M (composite=0.0).
        capex_usd_m = round(50.0 * (1.0 - composite), 2)
        # Opex is typically 10-30% of capex annually; use 20%.
        opex_usd_m_per_y = round(capex_usd_m * 0.20, 2)

        # Cost curve: assume Wright's Law — every doubling of cumulative
        # production drops unit cost by 15% (a learning rate of 0.85).
        learning_rate = 0.85

        return {
            "capex": {
                "value_usd_m": capex_usd_m,
                "model": "linear_in_(1-composite_feasibility)",
            },
            "opex": {
                "value_usd_m_per_y": opex_usd_m_per_y,
                "model": "20%_of_capex",
            },
            "cost_curve": {
                "model": "wright_law",
                "learning_rate": learning_rate,
                "form": "unit_cost(q) = c0 * q^log2(0.85)",
            },
            "market_size": {
                "value_usd_m": market_size_usd_m,
                "bucket_source": "industry_node_count",
            },
            "adoption_model": "bass_diffusion" if "0-2" in problem.get("time_horizon", "")
                              else "s_curve",
            "evidence": {
                "industry_count": n,
                "feasibility_composite_used": composite,
                "market_size_bucket_source": "industry_node_count",
                "capex_model": "linear_in_(1-composite_feasibility)",
                "opex_model": "20%_of_capex",
            },
            "assumptions": [
                "Capex is a linear function of (1 - composite feasibility). "
                "This is a coarse prior; real capex depends on tooling, "
                "regulatory pathway, and supply chain.",
                "Opex is assumed to be 20% of capex annually. Real ratios "
                "vary by industry from 5% (capital-intensive) to 50% "
                "(service-intensive).",
                "Market size is bucketed by industry-node count in the "
                "graph. This is a proxy for actual market research.",
                "Cost curve assumes Wright's Law with a 15% learning rate. "
                "Real learning rates range from 10% to 30% by industry.",
            ],
            "falsification_criteria": (
                "If a real capex/opex/market study for a comparable "
                "invention disagrees with these estimates by more than "
                "2x, the priors must be recalibrated. Sample size for "
                "recalibration: >= 10 comparable inventions."
            ),
        }
