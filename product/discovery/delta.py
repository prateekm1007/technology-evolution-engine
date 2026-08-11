"""
Discovery Delta (DD) Metric

DD = discovered_value_with_system - discovered_value_without_system

If DD approaches zero, the system is merely a search engine.
If DD becomes large, the system is genuinely generative.

This metric measures whether the system produces outputs that
a user would probably not have discovered without it.
"""

import json
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional


class DiscoveryDelta:
    """
    Measures the generative value of the system.
    
    DD is computed across five dimensions:
    - adjacency_novelty: did the system find connections the user wouldn't have?
    - prerequisite_insight: did the system identify gaps the user missed?
    - cemetery_value: did the system surface relevant failures?
    - permutation_quality: were the combinations non-obvious?
    - blueprint_actionability: can the user actually build from the output?
    """

    DIMENSIONS = {
        "adjacency_novelty": 0.25,
        "prerequisite_insight": 0.20,
        "cemetery_value": 0.15,
        "permutation_quality": 0.25,
        "blueprint_actionability": 0.15,
    }

    def __init__(self):
        self.history = []

    def score(
        self,
        pipeline_output: Dict[str, Any],
        user_input: Dict[str, Any],
        baseline: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Compute Discovery Delta for a single pipeline run.
        
        Args:
            pipeline_output: Full output from BusinessPipeline or ConsumerPipeline
            user_input: The original user input
            baseline: Optional baseline representing what a simple search would return
            
        Returns:
            DD score with per-dimension breakdown
        """
        scores = {}

        # 1. Adjacency Novelty
        # How many adjacencies were found that are non-trivial?
        adjacencies = pipeline_output.get("adjacency_map", [])
        if isinstance(adjacencies, list):
            n_adj = len(adjacencies)
        elif isinstance(adjacencies, dict):
            n_adj = sum(len(v) if isinstance(v, list) else 1 for v in adjacencies.values())
        else:
            n_adj = 0

        # Non-trivial threshold: more than 3 adjacencies suggests generative value
        scores["adjacency_novelty"] = min(1.0, n_adj / 10.0) if n_adj > 0 else 0.0

        # 2. Prerequisite Insight
        # Did the system identify prerequisites the user likely didn't know about?
        candidates = pipeline_output.get("candidates", [])
        total_prereqs = 0
        missing_prereqs = 0
        for c in candidates if isinstance(candidates, list) else []:
            prereqs = c.get("prerequisites", [])
            if isinstance(prereqs, list):
                total_prereqs += len(prereqs)
                missing_prereqs += sum(1 for p in prereqs if isinstance(p, dict) and not p.get("met", True))

        if total_prereqs > 0:
            scores["prerequisite_insight"] = min(1.0, missing_prereqs / max(total_prereqs, 1) + 0.3)
        else:
            scores["prerequisite_insight"] = 0.2  # baseline if no prereqs found

        # 3. Cemetery Value
        # Did the system surface relevant historical failures?
        warnings = pipeline_output.get("warnings", [])
        cemetery_refs = pipeline_output.get("cemetery_matches", [])
        risk_flags = pipeline_output.get("risk_register", [])

        cemetery_signal = len(cemetery_refs) + len([w for w in warnings if "cemetery" in str(w).lower()])
        scores["cemetery_value"] = min(1.0, cemetery_signal / 5.0) if cemetery_signal > 0 else 0.1

        # 4. Permutation Quality
        # Were the combinations non-obvious and diverse?
        permutations = pipeline_output.get("permutations", [])
        n_perms = len(permutations) if isinstance(permutations, list) else 0

        # Diversity: how many unique domains are represented?
        domains_seen = set()
        for p in permutations if isinstance(permutations, list) else []:
            if isinstance(p, dict):
                domains_seen.add(p.get("domain", "unknown"))

        diversity_bonus = min(0.3, len(domains_seen) * 0.1)
        scores["permutation_quality"] = min(1.0, (n_perms / 15.0) + diversity_bonus) if n_perms > 0 else 0.0

        # 5. Blueprint Actionability
        # Can the user actually build from the output?
        blueprints = pipeline_output.get("blueprints", [])
        n_blueprints = len(blueprints) if isinstance(blueprints, list) else 0

        has_bom = any(
            isinstance(b, dict) and b.get("bom")
            for b in blueprints if isinstance(blueprints, list)
        )
        has_prototype_plan = any(
            isinstance(b, dict) and b.get("prototype_plan")
            for b in blueprints if isinstance(blueprints, list)
        )

        actionability = 0.0
        if n_blueprints > 0:
            actionability += 0.4
        if has_bom:
            actionability += 0.3
        if has_prototype_plan:
            actionability += 0.3
        scores["blueprint_actionability"] = min(1.0, actionability)

        # Weighted composite
        dd = sum(
            scores[dim] * weight
            for dim, weight in self.DIMENSIONS.items()
        )

        # Baseline comparison
        baseline_dd = 0.0
        if baseline:
            baseline_dd = baseline.get("dd", 0.0)

        delta = dd - baseline_dd

        result = {
            "dd": round(dd, 4),
            "delta_vs_baseline": round(delta, 4),
            "dimensions": {k: round(v, 4) for k, v in scores.items()},
            "interpretation": self._interpret(dd),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        self.history.append(result)
        return result

    def _interpret(self, dd: float) -> str:
        if dd >= 0.7:
            return "HIGH: System is genuinely generative. User would likely not discover this without it."
        elif dd >= 0.4:
            return "MODERATE: System adds meaningful value beyond search."
        elif dd >= 0.2:
            return "LOW: System is close to a search engine. Limited generative value."
        else:
            return "NEGLIGIBLE: System adds little beyond what a search engine provides."

    def summary(self) -> Dict[str, Any]:
        """Aggregate DD across all scored runs."""
        if not self.history:
            return {"total_runs": 0, "mean_dd": 0.0, "interpretation": "No data"}

        dds = [h["dd"] for h in self.history]
        return {
            "total_runs": len(dds),
            "mean_dd": round(sum(dds) / len(dds), 4),
            "min_dd": round(min(dds), 4),
            "max_dd": round(max(dds), 4),
            "high_count": sum(1 for d in dds if d >= 0.7),
            "moderate_count": sum(1 for d in dds if 0.4 <= d < 0.7),
            "low_count": sum(1 for d in dds if 0.2 <= d < 0.4),
            "negligible_count": sum(1 for d in dds if d < 0.2),
            "interpretation": self._interpret(sum(dds) / len(dds)),
        }

    def export(self, path: str):
        """Export DD history to JSON."""
        with open(path, "w") as f:
            json.dump({
                "metric": "discovery_delta",
                "history": self.history,
                "summary": self.summary(),
            }, f, indent=2)
