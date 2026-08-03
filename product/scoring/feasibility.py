"""
Feasibility scoring — Priority 4 of the North-Star directive.

Every candidate invention should eventually produce something like:

    {
      "technical_feasibility": 0.82,
      "economic_feasibility": 0.71,
      "regulatory_feasibility": 0.65,
      "manufacturing_feasibility": 0.79,
      "adoption_probability": 0.58,
      "estimated_time_horizon": "5-10 years"
    }

This module implements that score. The score is computed from
graph-structural signals (prerequisites met, constraints binding,
cemetery analogues, lineage depth) — NOT from a black-box model.
Every input that affects the score is exposed in the `evidence` block
of the output, so the score is auditable.

Law 8 honesty: feasibility scores are PREDICTIONS about future
feasibility. They are not "verified" until the verification cycle
has recorded at least one pass and one fail for the relevant
prediction class.

Honesty Loop (Law 27/28/29): the `confidence` field is forbidden as
a numerical certainty on claims without experimental validation. The
FeasibilityScore dataclass now carries:
  - `epistemic_status`: the typed status block (Law 29e) — this is
    the sanctioned output.
  - `legacy_confidence_deprecated`: the old numerical confidence,
    retained for one release cycle for backward compat with existing
    consumers. Marked DEPRECATED. Will be removed in the next cycle.

Per Law 7 (Historical Permanence): the dataclass field rename is a
breaking change, but the migration is documented here and in the
HONESTY_LOOP.md gate. Existing consumers must read `epistemic_status`
instead of `confidence`.
"""

from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, asdict, field
import json

from product.scoring.epistemic_status import ANALYZER_EPISTEMIC_STATUS


# Time-horizon buckets, matching the directive's "5-10 years" example.
# A score below 0.4 -> horizon >= "10+ years"; a score above 0.85 -> "0-2 years".
def _horizon_from_score(s: float) -> str:
    if s >= 0.85: return "0-2 years"
    if s >= 0.70: return "2-5 years"
    if s >= 0.55: return "5-10 years"
    if s >= 0.40: return "10-15 years"
    return "15+ years"


@dataclass
class FeasibilityScore:
    """The exact schema demanded by the directive.

    Honesty Loop (Law 27/28/29): the `confidence` field is forbidden
    as a numerical certainty. It is retained as
    `legacy_confidence_deprecated` for one release cycle. The
    sanctioned output is `epistemic_status` (typed block per Law 29e).
    """
    technical_feasibility: float
    economic_feasibility: float
    regulatory_feasibility: float
    manufacturing_feasibility: float
    adoption_probability: float
    estimated_time_horizon: str
    composite_feasibility: float
    # Honesty Loop (Law 27): the legacy `confidence` field is renamed
    # to `legacy_confidence_deprecated`. The typed `epistemic_status`
    # block is the sanctioned output.
    legacy_confidence_deprecated: float
    epistemic_status: Dict[str, Any]
    evidence: Dict[str, Any]
    assumptions: List[str]
    falsification_criteria: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class FeasibilityScorer:
    """Scores candidate inventions across the five feasibility dimensions.

    The scorer takes:
      - a target node id (the invention being scored)
      - the civilization graph
      - optionally, a list of operator types applied (eliminate,
        substitute, etc.) — these adjust the score based on which
        transformation the candidate represents.

    The scorer does NOT consult the ledger or any external state. It
    is purely a function of (target_id, graph, operators). This makes
    it deterministic and replayable.
    """

    # Constraint-type weights. Constraints are the second-class citizen
    # of the graph — every node can carry a `constraints` list. Each
    # constraint type contributes differently to each feasibility
    # dimension. The mapping below is the prior; it can be calibrated
    # by the verification cycle.
    CONSTRAINT_WEIGHTS = {
        "energy":         {"technical": -0.05, "economic": -0.05, "regulatory":  0.00, "manufacturing": -0.03, "adoption":  0.00},
        "material":       {"technical": -0.03, "economic": -0.02, "regulatory":  0.00, "manufacturing": -0.05, "adoption":  0.00},
        "cost":           {"technical":  0.00, "economic": -0.10, "regulatory":  0.00, "manufacturing": -0.02, "adoption": -0.05},
        "regulation":     {"technical":  0.00, "economic": -0.02, "regulatory": -0.15, "manufacturing":  0.00, "adoption": -0.05},
        "manufacturing":  {"technical": -0.02, "economic": -0.03, "regulatory":  0.00, "manufacturing": -0.15, "adoption": -0.02},
        "supply_chain":   {"technical":  0.00, "economic": -0.05, "regulatory":  0.00, "manufacturing": -0.05, "adoption":  0.00},
        "time":           {"technical": -0.02, "economic": -0.03, "regulatory":  0.00, "manufacturing": -0.02, "adoption": -0.02},
        "information":    {"technical": -0.02, "economic":  0.00, "regulatory":  0.00, "manufacturing":  0.00, "adoption":  0.00},
        "safety":         {"technical": -0.03, "economic":  0.00, "regulatory": -0.05, "manufacturing":  0.00, "adoption": -0.03},
        "maintenance":    {"technical": -0.02, "economic": -0.03, "regulatory":  0.00, "manufacturing":  0.00, "adoption": -0.05},
    }

    def __init__(self, graph: Dict[str, Any]):
        self.nodes = graph.get("nodes", [])
        self.edges = graph.get("edges", [])
        self.by_id: Dict[str, Dict[str, Any]] = {n["id"]: n for n in self.nodes}
        # Prereq adjacency.
        self.out: Dict[str, List[Any]] = {}
        self.inc: Dict[str, List[Any]] = {}
        for e in self.edges:
            src = e.get("source")
            tgt = e.get("target")
            rel = e.get("relationship") or e.get("rel", "depends_on")
            if src is None or tgt is None:
                continue
            self.out.setdefault(src, []).append((tgt, rel))
            self.inc.setdefault(tgt, []).append((src, rel))

    def score(self, target_id: str,
              operators: Optional[List[str]] = None) -> FeasibilityScore:
        """Compute the feasibility score for a target invention.

        Args:
            target_id: the node id of the invention being scored.
            operators: optional list of transformation operators
                applied (from Law 4's set: eliminate, substitute,
                miniaturize, distribute, modularize,
                software_substitution, change_energy_domain,
                change_information_domain).
        """
        operators = operators or []
        if target_id not in self.by_id:
            return self._empty_score(target_id, reason="node not in graph")

        node = self.by_id[target_id]

        # 1. Prerequisite completeness: how many of the target's
        # documented prerequisites actually exist in the graph?
        prereqs = [
            tgt for tgt, rel in self.out.get(target_id, [])
            if rel in ("requires", "depends_on")
        ]
        prereqs_met = sum(1 for p in prereqs if p in self.by_id)
        prereq_completeness = (
            prereqs_met / len(prereqs) if prereqs else 0.7  # no prereqs = neutral
        )

        # 2. Constraints binding: count constraint types on the node.
        # C2 FIX: constraints is now a dict (Phase 2 migration).
        # _as_list on a dict returns [dict] — a one-element list
        # containing the dict itself. The keyword matching then
        # accidentally works because str(dict) contains all keys.
        # Fix: extract constraint names from the dict's keys with
        # value > 0, or fall back to the list format.
        raw_constraints = node.get("constraints", [])
        if isinstance(raw_constraints, dict):
            constraints = [k for k, v in raw_constraints.items() if v and v > 0]
        else:
            constraints = _as_list(raw_constraints)
        constraint_adjustments = {
            "technical": 0.0, "economic": 0.0,
            "regulatory": 0.0, "manufacturing": 0.0, "adoption": 0.0,
        }
        for c in constraints:
            # constraint names are free-text; map by keyword
            cl = str(c).lower()
            for key, weights in self.CONSTRAINT_WEIGHTS.items():
                if key in cl:
                    for dim, w in weights.items():
                        constraint_adjustments[dim] += w
                    break

        # 3. Cemetery analogues: has this invention's lineage failed
        # before? Each documented failure in the lineage drags
        # adoption_probability down (but not technical feasibility —
        # the tech was viable, the timing was wrong).
        cemetery_analogues = self._find_cemetery_analogues(target_id)
        cemetery_penalty_adoption = -0.05 * len(cemetery_analogues)

        # 4. Lineage depth: deeper lineage = more mature = higher
        # technical feasibility (more prerequisites proven).
        lineage_depth = self._lineage_depth(target_id, max_depth=5)
        lineage_bonus_technical = min(0.15, lineage_depth * 0.03)

        # 5. Domain mix: cross-domain candidates get a small bonus
        # because the directive's thesis is that cross-domain
        # combinations are where invention happens.
        domain_mix_bonus = 0.0
        if prereqs:
            prereq_domains = {
                self.by_id.get(p, {}).get("domain")
                for p in prereqs if p in self.by_id
            }
            node_domain = node.get("domain")
            if node_domain and any(d and d != node_domain for d in prereq_domains):
                domain_mix_bonus = 0.05

        # 6. Operator effects: each operator shifts specific dimensions.
        operator_effects = self._operator_effects(operators)

        # Compute each dimension.
        technical = self._clamp(0.65 + prereq_completeness * 0.20
                                + lineage_bonus_technical
                                + constraint_adjustments["technical"]
                                + operator_effects["technical"])
        economic = self._clamp(0.55 + prereq_completeness * 0.15
                                + constraint_adjustments["economic"]
                                + operator_effects["economic"])
        regulatory = self._clamp(0.60 + constraint_adjustments["regulatory"]
                                  + operator_effects["regulatory"])
        manufacturing = self._clamp(0.60 + prereq_completeness * 0.10
                                    + constraint_adjustments["manufacturing"]
                                    + operator_effects["manufacturing"])
        adoption = self._clamp(0.50 + prereq_completeness * 0.15
                                + constraint_adjustments["adoption"]
                                + cemetery_penalty_adoption
                                + domain_mix_bonus
                                + operator_effects["adoption"])

        composite = (
            0.30 * technical
            + 0.20 * economic
            + 0.15 * regulatory
            + 0.20 * manufacturing
            + 0.15 * adoption
        )

        horizon = _horizon_from_score(composite)

        # Confidence: starts at 0.3 (uncalibrated prior), rises with
        # the number of structural signals we were able to gather.
        # Real calibration happens via the verification cycle.
        confidence = self._clamp(0.30
                                  + 0.05 * (1 if prereqs else 0)
                                  + 0.05 * (1 if constraints else 0)
                                  + 0.05 * (1 if cemetery_analogues else 0)
                                  + 0.05 * (1 if lineage_depth > 0 else 0)
                                  + 0.05 * (1 if operators else 0))

        evidence = {
            "prerequisite_completeness": round(prereq_completeness, 4),
            "prerequisites_total": len(prereqs),
            "prerequisites_met": prereqs_met,
            "constraints": list(constraints),
            "constraint_adjustments": {k: round(v, 4) for k, v in constraint_adjustments.items()},
            "cemetery_analogues": cemetery_analogues,
            "lineage_depth": lineage_depth,
            "domain_mix_bonus": domain_mix_bonus,
            "operators_applied": operators,
            "operator_effects": {k: round(v, 4) for k, v in operator_effects.items()},
        }

        assumptions = [
            "Prerequisite completeness is a proxy for technical maturity.",
            "Constraint types map linearly to feasibility penalties; the mapping is a prior, not a calibration.",
            "Cemetery analogues reduce adoption probability but not technical feasibility.",
            "Time horizon is bucketed from the composite score and is approximate.",
            "Confidence is structural (how many signals we gathered), not statistical (how often past predictions of this class were correct).",
        ]

        falsification = (
            "If, after N verification cycles, candidates scored >=0.75 on "
            "composite feasibility fail to achieve adoption within the "
            "predicted time horizon more than 50% of the time, the "
            "constraint-weight prior is wrong and must be recalibrated. "
            "N >= 20 cycles is the minimum sample size for recalibration."
        )

        return FeasibilityScore(
            technical_feasibility=round(technical, 4),
            economic_feasibility=round(economic, 4),
            regulatory_feasibility=round(regulatory, 4),
            manufacturing_feasibility=round(manufacturing, 4),
            adoption_probability=round(adoption, 4),
            estimated_time_horizon=horizon,
            composite_feasibility=round(composite, 4),
            # Honesty Loop (Law 27): legacy `confidence` is retained
            # as `legacy_confidence_deprecated` (one release cycle).
            legacy_confidence_deprecated=round(confidence, 4),
            # The sanctioned output is the typed epistemic_status block.
            epistemic_status=dict(ANALYZER_EPISTEMIC_STATUS),
            evidence=evidence,
            assumptions=assumptions,
            falsification_criteria=falsification,
        )

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _find_cemetery_analogues(self, target_id: str) -> List[str]:
        """Walk the lineage of `target_id` and return ids of any
        cemetery_entry nodes in the lineage."""
        visited: Set[str] = set()
        frontier = [target_id]
        found = []
        for _ in range(5):
            next_frontier = []
            for nid in frontier:
                if nid in visited:
                    continue
                visited.add(nid)
                n = self.by_id.get(nid, {})
                if n.get("type") == "cemetery_entry":
                    found.append(nid)
                # Walk both directions.
                for tgt, _rel in self.out.get(nid, []):
                    if tgt not in visited:
                        next_frontier.append(tgt)
                for src, _rel in self.inc.get(nid, []):
                    if src not in visited:
                        next_frontier.append(src)
            frontier = next_frontier
            if not frontier:
                break
        return found

    def _lineage_depth(self, target_id: str, max_depth: int = 5) -> int:
        """Max depth of the prerequisite chain rooted at `target_id`."""
        visited: Set[str] = {target_id}
        frontier = [target_id]
        depth = 0
        for _ in range(max_depth):
            next_frontier = []
            for nid in frontier:
                for tgt, rel in self.out.get(nid, []):
                    if rel in ("requires", "depends_on") and tgt not in visited:
                        visited.add(tgt)
                        next_frontier.append(tgt)
            if not next_frontier:
                break
            depth += 1
            frontier = next_frontier
        return depth

    def _operator_effects(self, operators: List[str]) -> Dict[str, float]:
        """Per-operator dimension adjustments."""
        effects = {k: 0.0 for k in ("technical", "economic", "regulatory",
                                    "manufacturing", "adoption")}
        for op in operators:
            if op == "eliminate":
                effects["technical"] += 0.05
                effects["economic"] += 0.05
            elif op == "substitute":
                effects["technical"] += 0.03
                effects["manufacturing"] += 0.03
            elif op == "miniaturize":
                effects["technical"] += 0.05
                effects["adoption"] += 0.05
                effects["manufacturing"] -= 0.03
            elif op == "distribute":
                effects["technical"] += 0.02
                effects["adoption"] += 0.05
            elif op == "modularize":
                effects["manufacturing"] += 0.05
                effects["adoption"] += 0.03
            elif op == "software_substitution":
                effects["technical"] += 0.05
                effects["economic"] += 0.05
                effects["manufacturing"] += 0.05
            elif op == "change_energy_domain":
                effects["technical"] -= 0.02
                effects["economic"] += 0.03
            elif op == "change_information_domain":
                effects["technical"] += 0.03
                effects["adoption"] += 0.03
        return effects

    def _clamp(self, x: float, lo: float = 0.0, hi: float = 1.0) -> float:
        return max(lo, min(hi, x))

    def _empty_score(self, target_id: str, reason: str = "") -> FeasibilityScore:
        return FeasibilityScore(
            technical_feasibility=0.0,
            economic_feasibility=0.0,
            regulatory_feasibility=0.0,
            manufacturing_feasibility=0.0,
            adoption_probability=0.0,
            estimated_time_horizon="unknown",
            composite_feasibility=0.0,
            # Honesty Loop (Law 27): legacy `confidence` is retained
            # as `legacy_confidence_deprecated` (one release cycle).
            legacy_confidence_deprecated=0.0,
            epistemic_status=dict(ANALYZER_EPISTEMIC_STATUS),
            evidence={"target_id": target_id, "reason": reason},
            assumptions=[],
            falsification_criteria="N/A — score not computed.",
        )


def _as_list(x) -> list:
    if x is None:
        return []
    if isinstance(x, list):
        return x
    return [x]
