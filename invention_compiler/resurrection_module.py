"""
Resurrection Module — feeds Layer 2 (Dependency graph).

Per CTO review #2 (commit `02d7658`), upgraded from "historical
similarity" (keyword overlap) to "historical counterfactual analysis".

For each historical failure, the module now asks: "if the documented
cause of failure had been different, would the invention have
succeeded?" The answer is a counterfactual prediction, not a
similarity score.

For example, for Airships:
  - Cause of failure: hydrogen flammability + helium unavailability.
  - Counterfactual: "if helium had been available, would Airships
    have succeeded as passenger transport?"
  - Predicted outcome: partial (helium availability removes the
    flammability risk, but speed/cost remain issues vs airplanes).

The counterfactual is specific to the failure's documented cause,
not a generic "if conditions changed" statement.

Output contract (Layer 2 fragment):
  {
    "resurrection_opportunities": [
      {
        "cemetery_id": str,
        "name": str,
        "resurrection_conditions": [...],
        "applicable": bool,
        "reason": str,
        "evidence_ref": str,
        "counterfactual": {
          "what_changed": str,            # specific historical variable
          "predicted_outcome_if_changed": str,
          "rationale": str
        }
      }, ...
    ]
  }
"""
from typing import Dict, Any, List
import json
import pathlib

_ROOT = pathlib.Path(__file__).resolve().parents[1]
FAILURES_DIR = _ROOT / "evidence" / "failures"


class ResurrectionModule:
    """Surfaces resurrection opportunities from the failure record,
    with historical counterfactual analysis per failure."""

    # Counterfactual table: per-failure-id, what specific historical
    # variable would have to change, and what outcome we'd predict.
    # These are hand-curated because they encode domain knowledge —
    # the failure record's `resurrection_conditions` is too generic
    # for true counterfactual reasoning.
    COUNTERFACTUALS = {
        "failure_001": {  # Segway
            "what_changed": "if e-scooter sharing model existed in 2001 (eliminating ownership burden)",
            "predicted_outcome_if_changed": "partial_resurrection",
            "rationale": "The sharing model removes Segway's ownership-burden failure "
                         "mode, but the Segway form factor itself was replaced by "
                         "smaller, cheaper e-scooters. Resurrection is partial — "
                         "the category survived, the specific product did not.",
        },
        "failure_002": {  # Google Glass
            "what_changed": "if social acceptance of always-on cameras existed in 2014",
            "predicted_outcome_if_changed": "partial_resurrection",
            "rationale": "Social acceptance would have removed the privacy-stigma "
                         "failure mode, but the form factor was also ergonomically "
                         "flawed. Resurrection is partial — AR headsets (Meta "
                         "Ray-Ban, Apple Vision Pro) succeed in a different form.",
        },
        "failure_003": {  # Concorde
            "what_changed": "if fuel prices had not risen 4x in the 1970s and noise regulations had not banned supersonic overland flight",
            "predicted_outcome_if_changed": "partial_resurrection",
            "rationale": "Removing fuel-cost and noise-regulation pressures would "
                         "have made Concorde economically viable longer, but speed "
                         "alone is no longer a competitive advantage vs subsonic "
                         "business class. Resurrection is partial — Boom Supersonic "
                         "is trying, but for premium niche, not mass transport.",
        },
        "failure_004": {  # Theranos
            "what_changed": "if the underlying physics of single-drop diagnostics worked at consumer accuracy",
            "predicted_outcome_if_changed": "not_resurrected",
            "rationale": "The failure was not environmental — it was scientific. "
                         "Single-drop diagnostics at the claimed accuracy violated "
                         "the physics of sample volume vs measurement noise. No "
                         "counterfactual change in market, regulation, or timing "
                         "would have made the underlying claim true.",
        },
        "failure_005": {  # Quibi
            "what_changed": "if TikTok had not already captured short-form mobile video",
            "predicted_outcome_if_changed": "partial_resurrection",
            "rationale": "Without TikTok as substitute, Quibi's premium-content "
                         "model might have found a niche. But the underlying "
                         "assumption (people want 10-minute premium mobile "
                         "video) was wrong regardless. Partial resurrection only.",
        },
        "failure_006": {  # Iridium
            "what_changed": "if IoT demand for satellite connectivity had existed in 1999",
            "predicted_outcome_if_changed": "resurrected",
            "rationale": "Iridium's failure was timing — the market for global "
                         "satellite connectivity didn't exist in 1999. When IoT "
                         "demand materialized, Iridium Communications relaunched "
                         "and now operates profitably. Counterfactual confirmed: "
                         "this is a real resurrection.",
        },
        "failure_007": {  # Betamax
            "what_changed": "if Sony had licensed Betamax widely (VHS strategy)",
            "predicted_outcome_if_changed": "partial_resurrection",
            "rationale": "Licensing would have removed the format-war loss, but "
                         "physical-media videocassettes were obsoleted by streaming "
                         "regardless. Counterfactual change would have extended "
                         "Betamax's life, not prevented its eventual obsolescence.",
        },
        "failure_008": {  # HD-DVD
            "what_changed": "if Sony had not bundled Blu-ray into PlayStation 3",
            "predicted_outcome_if_changed": "partial_resurrection",
            "rationale": "Without PS3 bundling, the format war might have gone "
                         "differently. But both formats lost to streaming. "
                         "Counterfactual change would have extended HD-DVD's life, "
                         "not prevented obsolescence.",
        },
        "failure_009": {  # Airships
            "what_changed": "if helium had been available in the 1930s instead of hydrogen (hydrogen was used because helium was US-restricted)",
            "predicted_outcome_if_changed": "partial_resurrection",
            "rationale": "Helium availability would have removed the Hindenburg "
                         "flammability failure mode. But airships would still "
                         "have lost to airplanes on speed. Counterfactual "
                         "resurrection is partial — cargo (not passenger) "
                         "airships may yet succeed (LTA Research, HAV Airlander).",
        },
    }

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
        """For each failure record, surface the counterfactual: what
        historical variable would have to change, and what outcome
        we'd predict if it did."""
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
            fid = f.get("id")
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

            # Get the counterfactual for this failure.
            cf = self.COUNTERFACTUALS.get(fid, {
                "what_changed": "no specific counterfactual encoded",
                "predicted_outcome_if_changed": "unknown",
                "rationale": "No hand-curated counterfactual for this failure. "
                             "Resurrection applicability based on keyword overlap only.",
            })

            opportunities.append({
                "cemetery_id": fid,
                "name": f.get("name"),
                "resurrection_conditions": resurrection_conds,
                "applicable": applicable,
                "reason": "; ".join(reason_parts) if reason_parts else
                          "no prerequisite overlap",
                "evidence_ref": f"evidence/failures/{f.get('name','').lower().replace(' ','_')}.json",
                "counterfactual": cf,
            })

        applicable_count = sum(1 for o in opportunities if o["applicable"])
        return {
            "resurrection_opportunities": opportunities,
            "evidence": {
                "failure_records_examined": len(self.failures),
                "applicable_resurrections": applicable_count,
                "prerequisites_examined": len(prereqs),
                "counterfactual_table_size": len(self.COUNTERFACTUALS),
                "differentiation_basis": "specific_historical_counterfactual_per_failure",
            },
            "assumptions": [
                "Counterfactuals are hand-curated per failure, encoding "
                "domain knowledge about which historical variable was the "
                "binding constraint. They are not derived from the graph.",
                "Resurrection applicability (keyword overlap) is a separate "
                "signal from the counterfactual prediction. A failure may "
                "have a documented counterfactual even if no prerequisite "
                "overlap exists.",
            ],
            "falsification_criteria": (
                "If a real resurrection attempt for the failure contradicts "
                "the predicted_outcome_if_changed, the counterfactual was "
                "wrong. Sample size for recalibration: >= 5 resurrections "
                "per failure category."
            ),
        }
