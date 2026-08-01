"""
Resurrection Engine — feeds Layer 2 (Dependency graph).

For each prerequisite in the dependency chain, checks if there's a
historical failure (cemetery_entry node, or evidence/failures/*.json
record) that resembles it. The directive's resurrection analysis
asks: "which inventions failed only because they arrived too early?"
— and the cemetery is the evidence base for that question.

Output contract (Layer 2 fragment, `resurrection_opportunities`):
  [
    {
      "cemetery_id": str,
      "name": str,
      "resurrection_conditions": [...],
      "applicable": bool,
      "reason": str,
      "evidence_ref": str
    }, ...
  ]
"""
from typing import Dict, Any, List
import json
import pathlib

_ROOT = pathlib.Path(__file__).resolve().parents[1]
FAILURES_DIR = _ROOT / "evidence" / "failures"


class ResurrectionEngine:
    """Surfaces resurrection opportunities from the failure record."""

    def __init__(self, graph: Dict[str, Any]):
        self.graph = graph
        self.nodes = graph.get("nodes", [])
        self.failures = self._load_failures()

    def _load_failures(self) -> List[Dict[str, Any]]:
        records = []
        if not FAILURES_DIR.exists():
            return records
        for fp in sorted(FAILURES_DIR.glob("*.json")):
            try:
                records.append(json.loads(fp.read_text()))
            except json.JSONDecodeError:
                continue
        return records

    def analyze(self, problem: Dict[str, Any],
                dependency_output: Dict[str, Any]) -> Dict[str, Any]:
        """For each failure record, check whether the problem's
        prerequisites overlap with the failure's resurrection conditions."""
        prereqs = dependency_output.get("prerequisites", [])
        prereq_labels = [
            (p.get("label") or "").lower() for p in prereqs
        ]
        prereq_constraints = []
        for p in prereqs:
            for c in (p.get("constraints") or []):
                prereq_constraints.append(str(c).lower())

        opportunities = []
        for f in self.failures:
            resurrection_conds = f.get("resurrection_conditions", [])
            # Apply if any resurrection condition keyword-matches any
            # prerequisite label or constraint.
            applicable = False
            reason_parts = []
            for cond in resurrection_conds:
                cl = cond.lower()
                if any(kw in cl for kw in prereq_labels + prereq_constraints
                       if kw):
                    applicable = True
                    reason_parts.append(f"matches prerequisite: {cond}")
                    break
            opportunities.append({
                "cemetery_id": f.get("id"),
                "name": f.get("name"),
                "resurrection_conditions": resurrection_conds,
                "applicable": applicable,
                "reason": "; ".join(reason_parts) if reason_parts else
                          "no prerequisite overlap",
                "evidence_ref": f"evidence/failures/{f.get('name','').lower().replace(' ','_')}.json",
            })

        applicable_count = sum(1 for o in opportunities if o["applicable"])
        return {
            "resurrection_opportunities": opportunities,
            "evidence": {
                "failure_records_examined": len(self.failures),
                "applicable_resurrections": applicable_count,
                "prerequisites_examined": len(prereqs),
            },
            "assumptions": [
                "Resurrection applicability is approximated by keyword "
                "overlap between failure records' resurrection_conditions "
                "and the problem's prerequisites. This is a coarse filter.",
                "The failure record's `resurrection_conditions` field is "
                "treated as ground truth. In practice, those conditions "
                "are themselves predictions that should be verified.",
            ],
            "falsification_criteria": (
                "If a real resurrection opportunity exists for the problem "
                "but is not in this engine's output, either the failure "
                "record's resurrection_conditions are incomplete, or the "
                "keyword-overlap heuristic missed a match."
            ),
        }
