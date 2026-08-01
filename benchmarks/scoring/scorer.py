"""
Evidence Benchmark Scoring Engine

Scores pipeline outputs across 7 weighted dimensions.
All scoring is deterministic and reproducible.

Dimensions and weights:
    feasibility           20%
    novelty               15%
    usefulness            20%
    clarity               10%
    historical_accuracy   10%
    prerequisite_accuracy 15%
    blueprint_quality     10%
"""

import json
from dataclasses import dataclass, field, asdict
from typing import Dict, List

WEIGHTS = {
    "feasibility": 0.20,
    "novelty": 0.15,
    "usefulness": 0.20,
    "clarity": 0.10,
    "historical_accuracy": 0.10,
    "prerequisite_accuracy": 0.15,
    "blueprint_quality": 0.10,
}

assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9, "Weights must sum to 1.0"


@dataclass
class DimensionScore:
    dimension: str
    weight: float
    raw_score: float
    weighted_score: float
    evidence: str
    signals: List[str] = field(default_factory=list)


@dataclass
class BenchmarkScore:
    benchmark_id: str
    pipeline: str
    dimensions: Dict[str, DimensionScore] = field(default_factory=dict)
    composite_score: float = 0.0
    grade: str = ""
    warnings: List[str] = field(default_factory=list)

    def compute_composite(self):
        self.composite_score = sum(d.weighted_score for d in self.dimensions.values())
        if self.composite_score >= 0.9: self.grade = "A"
        elif self.composite_score >= 0.75: self.grade = "B"
        elif self.composite_score >= 0.6: self.grade = "C"
        elif self.composite_score >= 0.4: self.grade = "D"
        else: self.grade = "F"

    def to_dict(self):
        return {
            "benchmark_id": self.benchmark_id,
            "pipeline": self.pipeline,
            "dimensions": {k: asdict(v) for k, v in self.dimensions.items()},
            "composite_score": round(self.composite_score, 4),
            "grade": self.grade,
            "warnings": self.warnings,
        }


class EvidenceScorer:
    """Deterministic scorer. No randomness. No external calls. Same input = same output."""

    def score_business(self, input_data: dict, output_data: dict) -> BenchmarkScore:
        bs = BenchmarkScore(benchmark_id=input_data.get("id", "unknown"), pipeline="business")
        w = WEIGHTS
        scores = {
            "feasibility": self._score_feasibility(input_data, output_data),
            "novelty": self._score_novelty(input_data, output_data),
            "usefulness": self._score_usefulness(input_data, output_data),
            "clarity": self._score_clarity(output_data),
            "historical_accuracy": self._score_historical_accuracy(input_data, output_data),
            "prerequisite_accuracy": self._score_prerequisite_accuracy(input_data, output_data),
            "blueprint_quality": self._score_blueprint_quality(output_data),
        }
        for dim, raw in scores.items():
            bs.dimensions[dim] = DimensionScore(dimension=dim, weight=w[dim], raw_score=raw,
                weighted_score=raw * w[dim], evidence=f"Scored {dim} at {raw:.3f} via rule-based evaluation.")
        bs.compute_composite()
        return bs

    def score_consumer(self, input_data: dict, output_data: dict) -> BenchmarkScore:
        bs = BenchmarkScore(benchmark_id=input_data.get("id", "unknown"), pipeline="consumer")
        cw = {"feasibility":0.25,"novelty":0.05,"usefulness":0.25,"clarity":0.15,
              "historical_accuracy":0.05,"prerequisite_accuracy":0.10,"blueprint_quality":0.15}
        scores = {
            "feasibility": self._score_feasibility(input_data, output_data),
            "novelty": self._score_novelty(input_data, output_data),
            "usefulness": self._score_usefulness(input_data, output_data),
            "clarity": self._score_clarity(output_data),
            "historical_accuracy": self._score_historical_accuracy(input_data, output_data),
            "prerequisite_accuracy": self._score_prerequisite_accuracy(input_data, output_data),
            "blueprint_quality": self._score_blueprint_quality(output_data),
        }
        for dim, raw in scores.items():
            bs.dimensions[dim] = DimensionScore(dimension=dim, weight=cw[dim], raw_score=raw,
                weighted_score=raw * cw[dim], evidence=f"Scored {dim} at {raw:.3f} (consumer weights).")
        bs.compute_composite()
        return bs

    def _score_feasibility(self, inp, out):
        score = 0.5
        expected = set(inp.get("expected_constraints", []))
        output_c = set()
        for s in ["report","blueprint","analysis"]:
            if s in out and isinstance(out[s], dict):
                output_c.update(out[s].get("constraints_addressed", []))
        if expected:
            score += (len(expected & output_c) / len(expected)) * 0.3
        ef = set(inp.get("expected_failure_modes", []))
        af = set()
        if "report" in out and isinstance(out["report"], dict):
            af = set(out["report"].get("failure_modes_addressed", []))
        if ef:
            score -= (len(ef - af) / len(ef)) * 0.2
        return max(0.0, min(1.0, score))

    def _score_novelty(self, inp, out):
        score = 0.4
        perms = out.get("permutations", [])
        if isinstance(perms, list):
            n = len(perms)
            if n >= 10: score += 0.3
            elif n >= 5: score += 0.2
            elif n >= 1: score += 0.1
        domains = set()
        for p in (perms if isinstance(perms, list) else []):
            if isinstance(p, dict):
                domains.add(p.get("domain",""))
                for a in p.get("adjacent_domains",[]): domains.add(a)
        if len(domains) >= 3: score += 0.2
        elif len(domains) >= 2: score += 0.1
        return max(0.0, min(1.0, score))

    def _score_usefulness(self, inp, out):
        score = 0.4
        bp = out.get("blueprint", {})
        if isinstance(bp, dict):
            for k in ["build_concept","prototype_plan","bom","cost_estimate"]:
                if bp.get(k): score += 0.1
        rpt = out.get("report", {})
        if isinstance(rpt, dict):
            for k in ["recommendations","next_steps"]:
                if rpt.get(k): score += 0.1
        return max(0.0, min(1.0, score))

    def _score_clarity(self, out):
        score = 0.3
        req = ["report","blueprint","permutations","metadata"]
        present = sum(1 for s in req if s in out and out[s])
        score += (present / len(req)) * 0.4
        meta = out.get("metadata", {})
        if isinstance(meta, dict):
            for k in ["assumptions","confidence","warnings"]:
                if meta.get(k): score += 0.1
        return max(0.0, min(1.0, score))

    def _score_historical_accuracy(self, inp, out):
        score = 0.4
        rpt = out.get("report", {})
        if isinstance(rpt, dict):
            if rpt.get("cemetery_references"): score += 0.2
            if rpt.get("historical_analogues"): score += 0.2
        ef = set(inp.get("expected_failure_modes", []))
        mentioned = set()
        if isinstance(rpt, dict):
            for s in ["risk_register","failure_modes_addressed","warnings"]:
                items = rpt.get(s, [])
                if isinstance(items, list):
                    for item in items:
                        if isinstance(item, str): mentioned.add(item.lower())
                        elif isinstance(item, dict): mentioned.add(str(item.get("mode","")).lower())
        if ef:
            hits = sum(1 for f in ef if any(f.lower() in m for m in mentioned))
            score += (hits / len(ef)) * 0.2
        return max(0.0, min(1.0, score))

    def _score_prerequisite_accuracy(self, inp, out):
        score = 0.4
        expected = set(p.lower() for p in inp.get("expected_prerequisites", []))
        identified = set()
        for sk in ["report","blueprint","analysis"]:
            sec = out.get(sk, {})
            if isinstance(sec, dict):
                for k in ["prerequisites","missing_prerequisites","gaps"]:
                    items = sec.get(k, [])
                    if isinstance(items, list):
                        for item in items:
                            if isinstance(item, str): identified.add(item.lower())
                            elif isinstance(item, dict): identified.add(str(item.get("name","")).lower())
        if expected:
            hits = sum(1 for e in expected if any(e in i or i in e for i in identified))
            score += (hits / len(expected)) * 0.4
            if identified:
                fp = sum(1 for i in identified if not any(e in i or i in e for e in expected))
                score -= (fp / len(identified)) * 0.2
        return max(0.0, min(1.0, score))

    def _score_blueprint_quality(self, out):
        score = 0.3
        bp = out.get("blueprint", {})
        if not isinstance(bp, dict): return score
        signals = ["build_concept","subsystem_architecture","bom","prototype_plan",
                   "risk_register","cost_estimate","timeline","next_experiments"]
        present = sum(1 for s in signals if bp.get(s))
        score += (present / len(signals)) * 0.5
        if isinstance(bp.get("bom"), list) and len(bp["bom"]) > 0: score += 0.1
        if isinstance(bp.get("prototype_plan"), list) and len(bp["prototype_plan"]) > 0: score += 0.1
        return max(0.0, min(1.0, score))
