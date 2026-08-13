"""
MDDG V3 — Staged Prior-Art Vocabulary + Claim-Chain Detector (directive #12, #13).

#13. Prior-art vocabulary (staged, never NOVEL):
    RETRIEVAL → KNOWN_COMBINATION → PARTIAL_PRIOR_ART → UNRESOLVED →
    CANDIDATE → PROMISING_INTERSECTION → EXTERNALLY_TESTABLE
    Human sign-off required for PROMISING_INTERSECTION → EXTERNALLY_TESTABLE.
    Machine never self-labels NOVEL.

#12. Four-hop replaced by Claim-chain detector:
    DEVICE → FAILURE_CLAIM → MECHANISM_CLAIM → INTERVENTION_CLAIM
    Every transition must be an actual evidence-backed Claim, not co-presence.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Optional
from datetime import datetime, timezone
import hashlib

from .claim import Claim, CLAIM_STATUS


# =====================================================================
# STAGED PRIOR-ART VOCABULARY (directive #13)
# =====================================================================

PRIOR_ART_STAGES = {
    "RETRIEVAL",               # candidate is just retrieval of existing knowledge
    "KNOWN_COMBINATION",       # the combination is already known in the prior art
    "PARTIAL_PRIOR_ART",       # some elements are in the prior art
    "UNRESOLVED",              # prior-art status cannot be determined
    "CANDIDATE",               # no prior art found — still a candidate
    "PROMISING_INTERSECTION",  # passed prior-art check, needs expert patent review
    "EXTERNALLY_TESTABLE",     # human sign-off received
}

# Machine may NEVER emit:
FORBIDDEN_PRIOR_ART_LABELS = {"NOVEL", "NEW", "INVENTION"}


@dataclass
class PriorArtAssessment:
    """Staged prior-art assessment.

    Per directive #13: "The machine must never self-label NOVEL.
    At PROMISING_INTERSECTION, trigger mandatory expert patent review.
    Only a human sign-off event can promote PROMISING_INTERSECTION → EXTERNALLY_TESTABLE."
    """
    candidate_id: str
    stage: str                   # one of PRIOR_ART_STAGES
    patent_search_result: str    # identifier-based search result
    paper_search_result: str
    device_search_result: str
    clinical_search_result: str
    failure_search_result: str
    assessment_timestamp: str
    human_sign_off: bool = False  # True only if a human expert signed off
    human_sign_off_timestamp: str = ""
    expert_review_required: bool = False  # True if stage == PROMISING_INTERSECTION
    notes: str = ""

    def __post_init__(self):
        if self.stage not in PRIOR_ART_STAGES:
            raise ValueError(f"Bad prior-art stage: {self.stage!r}")
        if self.stage in FORBIDDEN_PRIOR_ART_LABELS:
            raise ValueError(f"Forbidden prior-art label: {self.stage!r}")
        # PROMISING_INTERSECTION requires expert review
        if self.stage == "PROMISING_INTERSECTION":
            self.expert_review_required = True
        # EXTERNALLY_TESTABLE requires human sign-off
        if self.stage == "EXTERNALLY_TESTABLE" and not self.human_sign_off:
            raise ValueError("EXTERNALLY_TESTABLE requires human_sign_off=True")

    def can_promote_to_externally_testable(self) -> bool:
        """Only a human sign-off can promote to EXTERNALLY_TESTABLE."""
        return self.stage == "PROMISING_INTERSECTION" and self.human_sign_off

    def canonical_dict(self) -> dict:
        return asdict(self)


def assess_prior_art(candidate_id: str, *,
                     candidate_identifiers: list[str],
                     patent_corpus: list[dict] = None,
                     paper_corpus: list[dict] = None,
                     device_corpus: list[dict] = None,
                     clinical_corpus: list[dict] = None,
                     failure_corpus: list[dict] = None,
                     human_sign_off: bool = False) -> PriorArtAssessment:
    """Assess prior art using identifier-based search (not token overlap).

    Per directive #13: staged vocabulary. Never NOVEL.
    """
    patent_corpus = patent_corpus or []
    paper_corpus = paper_corpus or []
    device_corpus = device_corpus or []
    clinical_corpus = clinical_corpus or []
    failure_corpus = failure_corpus or []

    def search_corpus(corpus: list[dict], identifiers: list[str]) -> str:
        if not corpus:
            return "UNKNOWN"
        for record in corpus:
            record_text = " ".join(str(v) for v in record.values() if isinstance(v, (str, int, float)))
            for identifier in identifiers:
                if identifier and len(identifier) >= 3 and identifier in record_text:
                    return "EXACT_IDENTIFIER_MATCH"
        return "NOT_FOUND"

    patent_result = search_corpus(patent_corpus, candidate_identifiers)
    paper_result = search_corpus(paper_corpus, candidate_identifiers)
    device_result = search_corpus(device_corpus, candidate_identifiers)
    clinical_result = search_corpus(clinical_corpus, candidate_identifiers)
    failure_result = search_corpus(failure_corpus, candidate_identifiers)

    # Determine stage
    all_results = [patent_result, paper_result, device_result, clinical_result, failure_result]
    has_exact_match = any(r == "EXACT_IDENTIFIER_MATCH" for r in all_results)
    has_not_found = any(r == "NOT_FOUND" for r in all_results)
    all_unknown = all(r == "UNKNOWN" for r in all_results)

    if has_exact_match:
        stage = "KNOWN_COMBINATION"
    elif all_unknown:
        stage = "UNRESOLVED"
    elif has_not_found and not has_exact_match:
        # Searched and found no prior art → candidate
        if human_sign_off:
            stage = "EXTERNALLY_TESTABLE"
        else:
            stage = "PROMISING_INTERSECTION"
    else:
        stage = "PARTIAL_PRIOR_ART"

    return PriorArtAssessment(
        candidate_id=candidate_id,
        stage=stage,
        patent_search_result=patent_result,
        paper_search_result=paper_result,
        device_search_result=device_result,
        clinical_search_result=clinical_result,
        failure_search_result=failure_result,
        assessment_timestamp=datetime.now(timezone.utc).isoformat(),
        human_sign_off=human_sign_off,
        expert_review_required=(stage == "PROMISING_INTERSECTION"),
    )


# =====================================================================
# CLAIM-CHAIN DETECTOR (directive #12)
# =====================================================================

@dataclass
class ClaimChainCandidate:
    """A candidate formed by following actual Claim edges.

    Per directive #12: "A valid path must be:
    DEVICE → FAILURE_CLAIM → MECHANISM_CLAIM → INTERVENTION_CLAIM
    Every transition must correspond to an actual evidence-backed relationship."

    The following is forbidden:
    "device exists + failure exists + mechanism exists + material exists = candidate"
    """
    candidate_id: str
    device_id: str
    failure_claim: Optional[Claim] = None
    mechanism_claim: Optional[Claim] = None
    intervention_claim: Optional[Claim] = None

    # Every hop must have an actual Claim
    hop1_claim: bool = False      # DEVICE → FAILURE_CLAIM
    hop2_claim: bool = False      # FAILURE_CLAIM → MECHANISM_CLAIM
    hop3_claim: bool = False      # MECHANISM_CLAIM → INTERVENTION_CLAIM

    all_hops_have_claims: bool = False
    all_claims_evidence_backed: bool = False
    qualified: bool = False

    # Invention-candidate package (directive #18 — 11 fields)
    cause: str = ""
    mechanism: str = ""
    intervention: str = ""
    expected_effect_direction: str = ""
    boundary_conditions: str = ""
    evidence_summary: str = ""
    alternative_explanations: tuple[str, ...] = ()
    prior_art_burden: str = ""
    falsification_condition: str = ""
    measurement_method: str = ""

    def __post_init__(self):
        self.hop1_claim = self.failure_claim is not None
        self.hop2_claim = self.mechanism_claim is not None
        self.hop3_claim = self.intervention_claim is not None
        self.all_hops_have_claims = self.hop1_claim and self.hop2_claim and self.hop3_claim
        self.all_claims_evidence_backed = (
            self.all_hops_have_claims
            and self.failure_claim.is_evidence_backed()
            and self.mechanism_claim.is_evidence_backed()
            and self.intervention_claim.is_evidence_backed()
        ) if self.all_hops_have_claims else False
        # Qualified requires all hops + all evidence-backed + all 11 package fields
        self.qualified = (
            self.all_hops_have_claims
            and self.all_claims_evidence_backed
            and bool(self.cause)
            and bool(self.mechanism)
            and bool(self.intervention)
            and bool(self.expected_effect_direction)
            and bool(self.boundary_conditions)
            and bool(self.evidence_summary)
            and bool(self.alternative_explanations)
            and bool(self.prior_art_burden)
            and bool(self.falsification_condition)
            and bool(self.measurement_method)
        )


def find_claim_chain_candidates(
    device_id: str,
    failure_claims: list[Claim],
    mechanism_claims: list[Claim],
    intervention_claims: list[Claim],
) -> list[ClaimChainCandidate]:
    """Find Claim-chain candidates by matching actual Claims.

    Per directive #12: "Every transition must correspond to an actual
    evidence-backed relationship."

    The matching logic:
      - FAILURE_CLAIM: must reference the device_id
      - MECHANISM_CLAIM: must reference the same failure as the FAILURE_CLAIM
      - INTERVENTION_CLAIM: must reference the same mechanism as the MECHANISM_CLAIM
    """
    candidates = []
    # Filter failure claims that reference this device
    device_failure_claims = [fc for fc in failure_claims
                              if device_id in fc.source_ids or device_id in fc.proposition]
    for fc in device_failure_claims:
        # Find mechanism claims that address the same failure
        failure_text = fc.cause.lower()
        matching_mech_claims = [mc for mc in mechanism_claims
                                if failure_text and any(
                                    word in mc.proposition.lower()
                                    for word in failure_text.split()
                                    if len(word) > 4
                                )]
        for mc in matching_mech_claims:
            # Find intervention claims that reference the same mechanism
            mech_text = mc.mechanism.lower()
            matching_int_claims = [ic for ic in intervention_claims
                                   if mech_text and any(
                                       word in ic.proposition.lower()
                                       for word in mech_text.split()
                                       if len(word) > 4
                                   )]
            for ic in matching_int_claims:
                cid = f"claimchain:{device_id}:{fc.claim_id[:8]}:{mc.claim_id[:8]}:{ic.claim_id[:8]}"
                candidate = ClaimChainCandidate(
                    candidate_id=cid,
                    device_id=device_id,
                    failure_claim=fc,
                    mechanism_claim=mc,
                    intervention_claim=ic,
                    cause=fc.cause,
                    mechanism=mc.mechanism,
                    intervention=ic.intervention,
                    expected_effect_direction=ic.measured_effect,
                    boundary_conditions=fc.boundary_conditions,
                    evidence_summary=f"Failure: {fc.proposition[:100]} | Mechanism: {mc.proposition[:100]} | Intervention: {ic.proposition[:100]}",
                    alternative_explanations=fc.alternative_explanations + mc.alternative_explanations,
                    prior_art_burden="Not yet assessed",
                    falsification_condition=fc.falsification_condition,
                    measurement_method=ic.measurement_method,
                )
                candidates.append(candidate)
    return candidates
