"""candidate_ranker.py — Phase 13: multi-dimensional ranking, NOT one number."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from discovery_infrastructure.discovery_substrate import (
    Hypothesis, TransferHypothesis, Prediction, ExperimentProposal, NoveltyStatus)
from engine.adversarial_analysis import AdversarialAnalysis
from engine.rediscovery_detection import RediscoveryReport, RediscoveryClass
from engine.novelty_firewall import NoveltyReport


@dataclass
class CandidateRanking:
    hypothesis_id: str
    mechanistic_coherence: float = 0.0
    mechanistic_coherence_why: str = ""
    cross_domain_distance: float = 0.0
    cross_domain_distance_why: str = ""
    novelty_evidence: float = 0.0
    novelty_evidence_why: str = ""
    testability: float = 0.0
    testability_why: str = ""
    falsifiability: float = 0.0
    falsifiability_why: str = ""
    prior_art_risk: float = 0.0
    prior_art_risk_why: str = ""
    expected_information_gain: float = 0.0
    expected_information_gain_why: str = ""
    potential_impact: float = 0.0
    potential_impact_why: str = ""
    experimental_feasibility: float = 0.0
    experimental_feasibility_why: str = ""

    def to_dict(self) -> Dict:
        return {"hypothesis_id": self.hypothesis_id,
                "dimensions": {
                    "mechanistic_coherence": (self.mechanistic_coherence, self.mechanistic_coherence_why),
                    "cross_domain_distance": (self.cross_domain_distance, self.cross_domain_distance_why),
                    "novelty_evidence": (self.novelty_evidence, self.novelty_evidence_why),
                    "testability": (self.testability, self.testability_why),
                    "falsifiability": (self.falsifiability, self.falsifiability_why),
                    "prior_art_risk": (self.prior_art_risk, self.prior_art_risk_why),
                    "expected_information_gain": (self.expected_information_gain, self.expected_information_gain_why),
                    "potential_impact": (self.potential_impact, self.potential_impact_why),
                    "experimental_feasibility": (self.experimental_feasibility, self.experimental_feasibility_why),
                },
                "note": "dimensions reported separately, not collapsed into a single score"}


class CandidateRanker:
    """Rank candidates on 9 separate dimensions. Deterministic. Auditable."""

    def rank(self, hypothesis: Hypothesis, transfer: TransferHypothesis,
             adversarial: Optional[AdversarialAnalysis] = None,
             rediscovery: Optional[RediscoveryReport] = None,
             novelty: Optional[NoveltyReport] = None,
             prediction: Optional[Prediction] = None,
             experiment: Optional[ExperimentProposal] = None) -> CandidateRanking:
        r = CandidateRanking(hypothesis_id=hypothesis.hypothesis_id)

        r.mechanistic_coherence = 0.5 if hypothesis.mechanism else 0.0
        r.mechanistic_coherence_why = "hypothesis has a mechanism"
        if adversarial:
            if adversarial.survives:
                r.mechanistic_coherence = min(1.0, r.mechanistic_coherence + 0.3)
                r.mechanistic_coherence_why = "survived adversarial analysis"
            else:
                r.mechanistic_coherence = max(0.0, r.mechanistic_coherence - 0.4)
                r.mechanistic_coherence_why = "did not survive adversarial analysis"

        if transfer.source_domain and transfer.target_domain:
            if transfer.source_domain.lower() != transfer.target_domain.lower():
                r.cross_domain_distance = 0.8
                r.cross_domain_distance_why = f"source '{transfer.source_domain}' != target '{transfer.target_domain}'"
            else:
                r.cross_domain_distance = 0.1
                r.cross_domain_distance_why = "same domain"

        if rediscovery:
            cls = rediscovery.classification
            if cls == RediscoveryClass.NON_TRIVIAL_TRANSFER:
                r.novelty_evidence = 0.9
                r.novelty_evidence_why = "NON_TRIVIAL_TRANSFER"
            elif cls == RediscoveryClass.STRUCTURAL_INFERENCE:
                r.novelty_evidence = 0.4
                r.novelty_evidence_why = "structural inference within source domain"
            elif cls == RediscoveryClass.UNKNOWN:
                r.novelty_evidence = 0.2
                r.novelty_evidence_why = "classification unknown"
            else:
                r.novelty_evidence = 0.0
                r.novelty_evidence_why = f"{cls.value} (rediscovery)"

        if hypothesis.falsifier and hypothesis.falsifier.strip():
            r.falsifiability = 1.0
            r.falsifiability_why = "non-empty falsifier"
        else:
            r.falsifiability = 0.0
            r.falsifiability_why = "exploratory (no falsifier)"
        if prediction and prediction.falsifier:
            r.testability = 0.8
            r.testability_why = "prediction has falsifier + observable"
        elif hypothesis.is_testable:
            r.testability = 0.5
            r.testability_why = "hypothesis marked testable"
        else:
            r.testability = 0.1
            r.testability_why = "exploratory"

        if novelty:
            status = novelty.assessment.status
            if status == NoveltyStatus.PRIOR_ART_FOUND:
                r.prior_art_risk = 1.0
                r.prior_art_risk_why = "prior art found in dev corpus"
            elif status == NoveltyStatus.PARTIAL_PRECEDENT:
                r.prior_art_risk = 0.6
                r.prior_art_risk_why = "partial precedent"
            elif status == NoveltyStatus.AMBIGUOUS:
                r.prior_art_risk = 0.4
                r.prior_art_risk_why = "ambiguous matches"
            else:
                r.prior_art_risk = 0.2
                r.prior_art_risk_why = "no matches, but NOT_EVALUATED is not proof of novelty"

        if experiment and experiment.information_gain:
            r.expected_information_gain = 0.7
            r.expected_information_gain_why = "experiment has documented information gain"
        else:
            r.expected_information_gain = 0.2
            r.expected_information_gain_why = "no experiment design yet"

        if transfer.expected_effect and len(transfer.expected_effect) > 50:
            r.potential_impact = 0.6
            r.potential_impact_why = "specific expected effect"
        else:
            r.potential_impact = 0.3
            r.potential_impact_why = "generic or missing expected effect"

        if experiment:
            cost = (experiment.estimated_cost or "").lower()
            if "low" in cost:
                r.experimental_feasibility = 0.9
                r.experimental_feasibility_why = "low cost"
            elif "medium" in cost:
                r.experimental_feasibility = 0.5
                r.experimental_feasibility_why = "medium cost"
            elif "high" in cost:
                r.experimental_feasibility = 0.2
                r.experimental_feasibility_why = "high cost"
            else:
                r.experimental_feasibility = 0.4
                r.experimental_feasibility_why = "cost not clearly specified"

        return r


__all__ = ["CandidateRanker", "CandidateRanking"]
