"""
Cross-evidence-type motifs (Issue #5).

These extend the 10 paper×patent motifs from cross_corpus/motifs/ to include
the new evidence layers: technical reports, standards, datasets, code,
clinical trials, products, and failure records.

Motif set (per CEO directive):
  C01: paper + patent + standard         — standard constrains what the patent can claim
  C02: paper + patent + dataset          — dataset enables independent verification of the patent claim
  C03: paper + patent + technical_report — report contains engineering detail neither paper nor patent has
  C04: paper + patent + code             — code reveals what was actually implemented vs claimed
  C05: paper + patent + failure          — failure record contradicts the patent's implicit success claim
  C06: paper + paper + patent + dataset  — two papers disagree; dataset can adjudicate; patent bets on one
  C07: paper + patent + material + process — specific (material, process) combo is unclaimed
  C08: paper + patent + clinical_trial   — clinical trial tests the patent's medical device/drug claim
  C09: paper + patent + product          — product exists but no paper validates it; or paper validates but no product
  C10: paper + patent + experiment       — experimental database can falsify the patent's claim

Each motif produces a Candidate with:
  - falsifiable prediction (machine-checkable)
  - knowledge_distance score (search prioritization only)
  - typed provenance edges (no RELATED_TO)
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable
from .provenance import ProvenanceEdge


@dataclass
class CrossEvidenceCandidate:
    candidate_id: str
    motif: str
    evidence_layers: tuple[str, ...]    # e.g., ("paper", "patent", "standard")
    node_ids: tuple[str, ...]           # node ids from each layer
    edges: tuple[ProvenanceEdge, ...]   # typed provenance edges
    candidate_claim_text: str
    predicted_outcome: str
    prediction_window_days: int
    knowledge_distance: dict            # from knowledge_distance.py
    generated_at: str

    def canonical_dict(self) -> dict:
        return {
            "candidate_id": self.candidate_id,
            "motif": self.motif,
            "evidence_layers": list(self.evidence_layers),
            "node_ids": list(self.node_ids),
            "edges": [e.canonical_dict() for e in self.edges],
            "candidate_claim_text": self.candidate_claim_text,
            "predicted_outcome": self.predicted_outcome,
            "prediction_window_days": self.prediction_window_days,
            "knowledge_distance": self.knowledge_distance,
            "generated_at": self.generated_at,
        }


def motif_c01_paper_patent_standard(paper_id: str, patent_id: str, standard_id: str,
                                     *, paper_date: str, patent_date: str,
                                     standard_date: str, domain: str,
                                     distance: dict) -> CrossEvidenceCandidate:
    """Standard constrains what the patent can claim. If the paper later
    reports a result that violates the standard, the patent is at risk."""
    edges = (
        ProvenanceEdge(paper_id, patent_id, "cites", "D", "src:openalex",
                       citation_role="A", harvested_at="", notes="paper cites patent as background"),
        ProvenanceEdge(patent_id, standard_id, "cites_standard", "B", "src:iso_catalog",
                       harvested_at="", notes="patent claims compliance with standard"),
        ProvenanceEdge(paper_id, standard_id, "cites_standard", "B", "src:iso_catalog",
                       harvested_at="", notes="paper references standard as constraint"),
    )
    return CrossEvidenceCandidate(
        candidate_id=f"c01:{paper_id}:{patent_id}:{standard_id}",
        motif="c01_paper_patent_standard",
        evidence_layers=("paper", "patent", "standard"),
        node_ids=(paper_id, patent_id, standard_id),
        edges=edges,
        candidate_claim_text=(
            f"The result reported in {paper_id} will be found to violate the constraint "
            f"set by {standard_id}, invalidating the compliance claim of {patent_id}."
        ),
        predicted_outcome=f"{paper_id}|violates|{standard_id}|{patent_id}|False",
        prediction_window_days=1095,
        knowledge_distance=distance,
        generated_at="",
    )


def motif_c02_paper_patent_dataset(paper_id: str, patent_id: str, dataset_id: str,
                                    *, paper_date: str, patent_date: str,
                                    domain: str, distance: dict) -> CrossEvidenceCandidate:
    """Dataset can independently verify or refute the paper's claim that
    underlies the patent."""
    edges = (
        ProvenanceEdge(paper_id, dataset_id, "uses_dataset", "A", "src:zenodo",
                       harvested_at="", notes="paper uses dataset"),
        ProvenanceEdge(patent_id, paper_id, "derived_from", "C", "src:epo_ops",
                       harvested_at="", notes="patent derives from paper"),
    )
    return CrossEvidenceCandidate(
        candidate_id=f"c02:{paper_id}:{patent_id}:{dataset_id}",
        motif="c02_paper_patent_dataset",
        evidence_layers=("paper", "patent", "dataset"),
        node_ids=(paper_id, patent_id, dataset_id),
        edges=edges,
        candidate_claim_text=(
            f"Reanalysis of dataset {dataset_id} will either confirm or refute the central "
            f"claim of {paper_id} that {patent_id} relies on."
        ),
        predicted_outcome=f"{dataset_id}|adjudicates|{paper_id}|{patent_id}|False",
        prediction_window_days=730,
        knowledge_distance=distance,
        generated_at="",
    )


def motif_c03_paper_patent_tech_report(paper_id: str, patent_id: str, report_id: str,
                                        *, paper_date: str, patent_date: str,
                                        report_date: str, domain: str, distance: dict) -> CrossEvidenceCandidate:
    """Technical report contains engineering detail (failure modes, test
    conditions, design tradeoffs) that neither the paper nor patent discloses."""
    edges = (
        ProvenanceEdge(report_id, paper_id, "extends", "D", "src:nasa_ntrs",
                       harvested_at="", notes="report extends paper"),
        ProvenanceEdge(patent_id, report_id, "cites", "C", "src:epo_ops",
                       citation_role="A", harvested_at="", notes="patent cites report as background"),
    )
    return CrossEvidenceCandidate(
        candidate_id=f"c03:{paper_id}:{patent_id}:{report_id}",
        motif="c03_paper_patent_tech_report",
        evidence_layers=("paper", "patent", "technical_report"),
        node_ids=(paper_id, patent_id, report_id),
        edges=edges,
        candidate_claim_text=(
            f"The engineering detail in {report_id} will be cited in a future "
            f"improvement patent on {patent_id}."
        ),
        predicted_outcome=f"{report_id}|cited_in_future_patent|{patent_id}||False",
        prediction_window_days=1095,
        knowledge_distance=distance,
        generated_at="",
    )


def motif_c04_paper_patent_code(paper_id: str, patent_id: str, code_id: str,
                                 *, paper_date: str, patent_date: str,
                                 code_date: str, domain: str, distance: dict) -> CrossEvidenceCandidate:
    """Code reveals what was actually implemented vs what the paper claimed
    and the patent protected. Discrepancies are candidates for follow-on
    patents or retractions."""
    edges = (
        ProvenanceEdge(code_id, paper_id, "implements", "D", "src:github",
                       harvested_at="", notes="code implements paper's algorithm"),
        ProvenanceEdge(patent_id, paper_id, "derived_from", "C", "src:epo_ops",
                       harvested_at="", notes="patent derives from paper"),
    )
    return CrossEvidenceCandidate(
        candidate_id=f"c04:{paper_id}:{patent_id}:{code_id}",
        motif="c04_paper_patent_code",
        evidence_layers=("paper", "patent", "code"),
        node_ids=(paper_id, patent_id, code_id),
        edges=edges,
        candidate_claim_text=(
            f"The implementation in {code_id} differs materially from the algorithm "
            f"described in {paper_id} on which {patent_id} relies. A follow-on patent "
            f"or correction will appear."
        ),
        predicted_outcome=f"{code_id}|diverges_from|{paper_id}|{patent_id}|False",
        prediction_window_days=730,
        knowledge_distance=distance,
        generated_at="",
    )


def motif_c05_paper_patent_failure(paper_id: str, patent_id: str, failure_id: str,
                                    *, paper_date: str, patent_date: str,
                                    failure_date: str, domain: str, distance: dict) -> CrossEvidenceCandidate:
    """Failure record (recall, retraction, accident report) contradicts the
    patent's implicit success claim. The patent may be at risk of being
    practiced unsuccessfully."""
    edges = (
        ProvenanceEdge(failure_id, patent_id, "cites_failure", "B", "src:fda_recalls",
                       harvested_at="", notes="failure record implicates patent"),
        ProvenanceEdge(paper_id, failure_id, "cites_failure", "D", "src:openalex",
                       harvested_at="", notes="paper references failure as motivation"),
    )
    return CrossEvidenceCandidate(
        candidate_id=f"c05:{paper_id}:{patent_id}:{failure_id}",
        motif="c05_paper_patent_failure",
        evidence_layers=("paper", "patent", "failure_record"),
        node_ids=(paper_id, patent_id, failure_id),
        edges=edges,
        candidate_claim_text=(
            f"The failure record {failure_id} will be formally cited against the "
            f"validity of {patent_id} in a future post-grant review."
        ),
        predicted_outcome=f"{failure_id}|cited_against|{patent_id}|{paper_id}|False",
        prediction_window_days=1825,
        knowledge_distance=distance,
        generated_at="",
    )


def motif_c06_two_papers_patent_dataset(p1_id: str, p2_id: str, patent_id: str, dataset_id: str,
                                         *, distance: dict) -> CrossEvidenceCandidate:
    """Two papers disagree; dataset can adjudicate; patent bets on one."""
    edges = (
        ProvenanceEdge(p1_id, p2_id, "refutes", "D", "src:openalex",
                       harvested_at="", notes="paper1 refutes paper2"),
        ProvenanceEdge(p1_id, dataset_id, "uses_dataset", "A", "src:zenodo",
                       harvested_at="", notes="paper1 uses dataset"),
        ProvenanceEdge(p2_id, dataset_id, "uses_dataset", "A", "src:zenodo",
                       harvested_at="", notes="paper2 uses dataset"),
        ProvenanceEdge(patent_id, p1_id, "derived_from", "C", "src:epo_ops",
                       harvested_at="", notes="patent derives from paper1"),
    )
    return CrossEvidenceCandidate(
        candidate_id=f"c06:{p1_id}:{p2_id}:{patent_id}:{dataset_id}",
        motif="c06_two_papers_patent_dataset",
        evidence_layers=("paper", "paper", "patent", "dataset"),
        node_ids=(p1_id, p2_id, patent_id, dataset_id),
        edges=edges,
        candidate_claim_text=(
            f"Reanalysis of {dataset_id} will confirm one of {p1_id} or {p2_id}, "
            f"determining whether {patent_id} is valid."
        ),
        predicted_outcome=f"{dataset_id}|adjudicates|{p1_id}+{p2_id}|{patent_id}|False",
        prediction_window_days=730,
        knowledge_distance=distance,
        generated_at="",
    )


def motif_c07_paper_patent_material_process(paper_id: str, patent_id: str,
                                             material: str, process: str,
                                             *, distance: dict) -> CrossEvidenceCandidate:
    """Specific (material, process) combination is unclaimed in the patent
    corpus but enabled by the paper's science."""
    edges = (
        ProvenanceEdge(paper_id, f"material:{material}", "uses_material", "A", "src:openalex",
                       harvested_at="", notes="paper uses material"),
        ProvenanceEdge(paper_id, f"process:{process}", "uses_process", "A", "src:openalex",
                       harvested_at="", notes="paper uses process"),
        ProvenanceEdge(patent_id, paper_id, "derived_from", "C", "src:epo_ops",
                       harvested_at="", notes="patent derives from paper"),
    )
    return CrossEvidenceCandidate(
        candidate_id=f"c07:{paper_id}:{patent_id}:{material}:{process}",
        motif="c07_paper_patent_material_process",
        evidence_layers=("paper", "patent"),
        node_ids=(paper_id, patent_id, f"material:{material}", f"process:{process}"),
        edges=edges,
        candidate_claim_text=(
            f"The combination ({material}, {process}) will appear in a future patent "
            f"with priority_date after {patent_id}'s priority."
        ),
        predicted_outcome=f"{material}|{process}|future_patent|{patent_id}|False",
        prediction_window_days=1095,
        knowledge_distance=distance,
        generated_at="",
    )


def motif_c08_paper_patent_clinical_trial(paper_id: str, patent_id: str, trial_id: str,
                                           *, distance: dict) -> CrossEvidenceCandidate:
    """Clinical trial tests the patent's medical device/drug claim."""
    edges = (
        ProvenanceEdge(trial_id, patent_id, "validates", "B", "src:ct_gov",
                       harvested_at="", notes="trial validates patent claim"),
        ProvenanceEdge(paper_id, trial_id, "derived_from", "D", "src:openalex",
                       harvested_at="", notes="paper reports trial result"),
    )
    return CrossEvidenceCandidate(
        candidate_id=f"c08:{paper_id}:{patent_id}:{trial_id}",
        motif="c08_paper_patent_clinical_trial",
        evidence_layers=("paper", "patent", "clinical_trial"),
        node_ids=(paper_id, patent_id, trial_id),
        edges=edges,
        candidate_claim_text=(
            f"Clinical trial {trial_id} will report a result that either supports or "
            f"undermines the claim of {patent_id}."
        ),
        predicted_outcome=f"{trial_id}|adjudicates|{patent_id}|{paper_id}|False",
        prediction_window_days=1825,
        knowledge_distance=distance,
        generated_at="",
    )


def motif_c09_paper_patent_product(paper_id: str, patent_id: str, product_id: str,
                                    *, distance: dict) -> CrossEvidenceCandidate:
    """Product exists in the market but no paper validates it; or paper
    validates but no product exists. The discrepancy is a candidate."""
    edges = (
        ProvenanceEdge(product_id, patent_id, "product_of", "B", "src:fda_devices",
                       harvested_at="", notes="product is product_of patent"),
        ProvenanceEdge(paper_id, product_id, "validates", "D", "src:openalex",
                       harvested_at="", notes="paper validates product"),
    )
    return CrossEvidenceCandidate(
        candidate_id=f"c09:{paper_id}:{patent_id}:{product_id}",
        motif="c09_paper_patent_product",
        evidence_layers=("paper", "patent", "product"),
        node_ids=(paper_id, patent_id, product_id),
        edges=edges,
        candidate_claim_text=(
            f"A post-market surveillance study on product {product_id} will either "
            f"confirm or refute the validation in {paper_id}."
        ),
        predicted_outcome=f"{product_id}|post_market_study|{paper_id}|{patent_id}|False",
        prediction_window_days=1825,
        knowledge_distance=distance,
        generated_at="",
    )


def motif_c10_paper_patent_experiment(paper_id: str, patent_id: str, experiment_id: str,
                                       *, distance: dict) -> CrossEvidenceCandidate:
    """Experimental database can falsify the patent's claim."""
    edges = (
        ProvenanceEdge(experiment_id, paper_id, "validates", "A", "src:materials_project",
                       harvested_at="", notes="experimental DB validates paper"),
        ProvenanceEdge(patent_id, paper_id, "derived_from", "C", "src:epo_ops",
                       harvested_at="", notes="patent derives from paper"),
    )
    return CrossEvidenceCandidate(
        candidate_id=f"c10:{paper_id}:{patent_id}:{experiment_id}",
        motif="c10_paper_patent_experiment",
        evidence_layers=("paper", "patent", "experiment"),
        node_ids=(paper_id, patent_id, experiment_id),
        edges=edges,
        candidate_claim_text=(
            f"Independent measurement from {experiment_id} will either confirm or "
            f"falsify the property claim underlying {patent_id}."
        ),
        predicted_outcome=f"{experiment_id}|adjudicates|{patent_id}|{paper_id}|False",
        prediction_window_days=1095,
        knowledge_distance=distance,
        generated_at="",
    )


ALL_CROSS_EVIDENCE_MOTIFS = [
    "c01_paper_patent_standard",
    "c02_paper_patent_dataset",
    "c03_paper_patent_tech_report",
    "c04_paper_patent_code",
    "c05_paper_patent_failure",
    "c06_two_papers_patent_dataset",
    "c07_paper_patent_material_process",
    "c08_paper_patent_clinical_trial",
    "c09_paper_patent_product",
    "c10_paper_patent_experiment",
]
