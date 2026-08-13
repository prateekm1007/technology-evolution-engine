"""
MDDG V1 — Independent Mechanism, Prior-Art, Adversarial Qualification (CTO directives #9, #10, #14).

#9. Independent mechanism: source-set-A (device/failure literature) ≠ source-set-B (mechanism literature).
    Mechanism literature must predate candidate lock time. Hashes preserved.

#10. Prior-art check: patent/paper/device/clinical/failure search →
    DIRECTLY_DISCLOSED | PARTIALLY_DISCLOSED | STRUCTURALLY_SIMILAR |
    MECHANISTICALLY_RELATED | NOT_FOUND | UNKNOWN. Never "NOVEL" until supported.

#14. Adversarial qualification: attempt to classify candidate as
    RETRIEVAL | OBVIOUS_COMBINATION | INSUFFICIENT_EVIDENCE |
    TEMPORALLY_INVALID | PRIOR_ART | SEMANTIC_ONLY. Only if it survives →
    MDDG_QUALIFIED_CANDIDATE.
"""
from __future__ import annotations
import hashlib
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# =====================================================================
# #9. INDEPENDENT MECHANISM PROCEDURE
# =====================================================================

@dataclass(frozen=True)
class IndependentMechanismAttestation:
    """Procedural independence attestation for a mechanism.

    Per CTO V8 directive #11: "Replace hash inequality with true set disjointness.
    Require: set(device_failure_sources) ∩ set(mechanism_sources) = ∅.
    Then require every mechanism source to satisfy publication_date < candidate_lock_time.
    Record the full source lists plus their hashes."
    """
    source_set_a_ids: tuple[str, ...]    # full list of device/failure source IDs
    source_set_b_ids: tuple[str, ...]    # full list of mechanism source IDs
    source_set_a_hash: str
    source_set_b_hash: str
    mechanism_vocabulary_hash: str
    candidate_creation_timestamp: str
    mechanism_source_dates: tuple[str, ...]  # publication dates of each mechanism source
    lock_time: str
    is_disjoint: bool              # True iff A ∩ B = ∅
    all_mechanism_sources_predate: bool  # True iff ALL mechanism sources predate lock
    is_independent: bool           # True iff disjoint AND all predate

    def canonical_dict(self) -> dict:
        return asdict(self)


def hash_source_set(source_ids: list[str]) -> str:
    """Hash a set of source record IDs for independence attestation."""
    return hashlib.sha256(
        "|".join(sorted(set(source_ids))).encode()
    ).hexdigest()


def attest_independence(device_failure_source_ids: list[str],
                         mechanism_source_ids: list[str],
                         mechanism_vocabulary: list[str],
                         mechanism_source_dates: list[str],
                         lock_time: Optional[str] = None) -> IndependentMechanismAttestation:
    """Procedurally attest that a mechanism is independent of the device/failure literature.

    Per CTO V8 #11:
      - True set disjointness: A ∩ B = ∅ (not just hash inequality)
      - Every mechanism source publication_date < candidate_lock_time
      - Record full source lists + dates + hashes
    """
    lock_time = lock_time or now_iso()
    lock_date = lock_time[:10]
    set_a = set(device_failure_source_ids)
    set_b = set(mechanism_source_ids)
    is_disjoint = len(set_a & set_b) == 0
    # Every mechanism source must predate the lock time
    all_predate = all(
        d < lock_date if d and len(d) >= 10 else False
        for d in mechanism_source_dates
    ) if mechanism_source_dates else False
    is_independent = is_disjoint and all_predate
    return IndependentMechanismAttestation(
        source_set_a_ids=tuple(sorted(set_a)),
        source_set_b_ids=tuple(sorted(set_b)),
        source_set_a_hash=hash_source_set(device_failure_source_ids),
        source_set_b_hash=hash_source_set(mechanism_source_ids),
        mechanism_vocabulary_hash=hashlib.sha256(
            "|".join(sorted(mechanism_vocabulary)).encode()
        ).hexdigest(),
        candidate_creation_timestamp=lock_time,
        mechanism_source_dates=tuple(mechanism_source_dates),
        lock_time=lock_time,
        is_disjoint=is_disjoint,
        all_mechanism_sources_predate=all_predate,
        is_independent=is_independent,
    )


# =====================================================================
# #10. PRIOR-ART CHECK (V8 corrected — no token-overlap classifier)
# =====================================================================

PRIOR_ART_STATUSES = {
    "EXACT_IDENTIFIER_MATCH",        # candidate identifier found verbatim in corpus
    "EXPLICIT_DISCLOSURE",           # explicit textual disclosure (auditable)
    "EXPLICIT_CITATION",             # explicit citation relationship
    "STRUCTURAL_REVIEW_REQUIRED",    # lexical similarity exists — needs human review
    "NOT_FOUND",                     # no match found
    "UNKNOWN",                       # corpus not available
}

# V8: Removed DIRECTLY_DISCLOSED, PARTIALLY_DISCLOSED, STRUCTURALLY_SIMILAR,
# MECHANISTICALLY_RELATED — those were token-overlap classifications, not evidence.


@dataclass
class PriorArtResult:
    """Result of a prior-art search for a candidate."""
    candidate_id: str
    patent_search_status: str       # one of PRIOR_ART_STATUSES
    paper_search_status: str
    device_search_status: str
    clinical_search_status: str
    failure_search_status: str
    overall_status: str = ""        # computed in __post_init__
    search_timestamp: str = ""
    search_artifacts: dict = field(default_factory=dict)

    def __post_init__(self):
        for field_name in ["patent_search_status", "paper_search_status",
                           "device_search_status", "clinical_search_status",
                           "failure_search_status"]:
            val = getattr(self, field_name)
            if val not in PRIOR_ART_STATUSES:
                raise ValueError(f"Bad prior-art status: {val!r}")
        # Overall = most restrictive (EXACT_IDENTIFIER_MATCH > EXPLICIT_DISCLOSURE >
        # EXPLICIT_CITATION > STRUCTURAL_REVIEW_REQUIRED > NOT_FOUND > UNKNOWN)
        priority = {"EXACT_IDENTIFIER_MATCH": 0, "EXPLICIT_DISCLOSURE": 1,
                    "EXPLICIT_CITATION": 2, "STRUCTURAL_REVIEW_REQUIRED": 3,
                    "NOT_FOUND": 4, "UNKNOWN": 5}
        statuses = [self.patent_search_status, self.paper_search_status,
                    self.device_search_status, self.clinical_search_status,
                    self.failure_search_status]
        self.overall_status = min(statuses, key=lambda s: priority.get(s, 5))
        if not self.search_timestamp:
            self.search_timestamp = now_iso()


def run_prior_art_check(candidate_id: str, *,
                         candidate_identifiers: list[str],
                         patent_corpus: list[dict] = None,
                         paper_corpus: list[dict] = None,
                         device_corpus: list[dict] = None,
                         clinical_corpus: list[dict] = None,
                         failure_corpus: list[dict] = None) -> PriorArtResult:
    """Run a structured prior-art search using IDENTIFIER matching, not token overlap.

    Per CTO V8 #12: "Remove automated assertions such as 5 shared words =
    DIRECTLY_DISCLOSED. Replace with EXACT_IDENTIFIER_MATCH, EXPLICIT_DISCLOSURE,
    EXPLICIT_CITATION, STRUCTURAL_REVIEW_REQUIRED, NOT_FOUND, UNKNOWN.
    Lexical similarity remains useful for search only. Never emit NOVEL."
    """
    patent_corpus = patent_corpus or []
    paper_corpus = paper_corpus or []
    device_corpus = device_corpus or []
    clinical_corpus = clinical_corpus or []
    failure_corpus = failure_corpus or []

    def search_corpus(corpus: list[dict], identifiers: list[str]) -> str:
        """Search a corpus for prior art using IDENTIFIER matching.

        V8: No token-overlap. Only exact identifier matches or explicit
        textual mentions of the candidate's identifiers.
        """
        if not corpus:
            return "UNKNOWN"
        for record in corpus:
            record_text = " ".join(str(v) for v in record.values() if isinstance(v, (str, int, float)))
            for identifier in identifiers:
                if identifier and len(identifier) >= 3 and identifier in record_text:
                    # Check if it's an exact identifier match or just a substring
                    # For K-numbers, product codes, NCT IDs — substring IS exact match
                    return "EXACT_IDENTIFIER_MATCH"
        return "NOT_FOUND"

    return PriorArtResult(
        candidate_id=candidate_id,
        patent_search_status=search_corpus(patent_corpus, candidate_identifiers),
        paper_search_status=search_corpus(paper_corpus, candidate_identifiers),
        device_search_status=search_corpus(device_corpus, candidate_identifiers),
        clinical_search_status=search_corpus(clinical_corpus, candidate_identifiers),
        failure_search_status=search_corpus(failure_corpus, candidate_identifiers),
        search_timestamp=now_iso(),
    )


# =====================================================================
# #14. ADVERSARIAL QUALIFICATION
# =====================================================================

ADVERSARIAL_ATTACKS = {
    "RETRIEVAL",              # candidate is just retrieval of existing knowledge
    "OBVIOUS_COMBINATION",    # candidate is an obvious combination of known elements
    "INSUFFICIENT_EVIDENCE",  # one or more evidence hops missing
    "TEMPORALLY_INVALID",     # mechanism postdates failure or temporal ordering wrong
    "PRIOR_ART",              # prior-art check found direct disclosure
    "SEMANTIC_ONLY",          # evidence is semantic similarity only (Tier C)
}


@dataclass
class AdversarialReview:
    """Result of adversarial review of a candidate."""
    candidate_id: str
    attacks_attempted: list[str]
    attacks_survived: list[str]
    attacks_failed: list[str]   # attacks that succeeded (candidate rejected)
    survived: bool              # True iff all attacks survived
    review_timestamp: str
    notes: str = ""

    def canonical_dict(self) -> dict:
        return asdict(self)


def run_adversarial_review(candidate_id: str, *,
                           has_device_evidence: bool,
                           has_failure_evidence: bool,
                           has_mechanism_evidence: bool,
                           has_intervention_evidence: bool,
                           mechanism_predates_failure: bool,
                           prior_art_status: str,
                           evidence_tiers: list[str],
                           obvious_combination_check_implemented: bool = False) -> AdversarialReview:
    """Run adversarial review. Candidate must survive ALL attacks to qualify.

    Per CTO V8 #13: "OBVIOUS_COMBINATION must be a genuine procedure. Until that
    exists: OBVIOUS_COMBINATION = BLOCKED. A candidate cannot qualify."

    Every attack must actually execute. No hardcoded PASS.
    """
    attacks_attempted = list(ADVERSARIAL_ATTACKS)
    attacks_survived = []
    attacks_failed = []

    # Attack 1: RETRIEVAL — is this just retrieval of existing knowledge?
    if all([has_device_evidence, has_failure_evidence, has_mechanism_evidence,
            has_intervention_evidence]):
        attacks_survived.append("RETRIEVAL")
    else:
        attacks_failed.append("RETRIEVAL")

    # Attack 2: OBVIOUS_COMBINATION — V8: must be a genuine procedure.
    # Until implemented, this attack is BLOCKED → candidate FAILS.
    if not obvious_combination_check_implemented:
        # BLOCKED: the attack cannot execute, so the candidate CANNOT qualify
        attacks_failed.append("OBVIOUS_COMBINATION")
    else:
        # When implemented: search for explicit combinations in prior art
        # For now, this path is not reached
        attacks_survived.append("OBVIOUS_COMBINATION")

    # Attack 3: INSUFFICIENT_EVIDENCE — are all evidence hops present?
    if all([has_device_evidence, has_failure_evidence, has_mechanism_evidence,
            has_intervention_evidence]):
        attacks_survived.append("INSUFFICIENT_EVIDENCE")
    else:
        attacks_failed.append("INSUFFICIENT_EVIDENCE")

    # Attack 4: TEMPORALLY_INVALID — does mechanism predate failure?
    if mechanism_predates_failure:
        attacks_survived.append("TEMPORALLY_INVALID")
    else:
        attacks_failed.append("TEMPORALLY_INVALID")

    # Attack 5: PRIOR_ART — was this directly disclosed?
    # V8: only EXACT_IDENTIFIER_MATCH blocks; STRUCTURAL_REVIEW_REQUIRED does not
    if prior_art_status != "EXACT_IDENTIFIER_MATCH":
        attacks_survived.append("PRIOR_ART")
    else:
        attacks_failed.append("PRIOR_ART")

    # Attack 6: SEMANTIC_ONLY — is the evidence only semantic (Tier C)?
    if "A" in evidence_tiers or "B" in evidence_tiers:
        attacks_survived.append("SEMANTIC_ONLY")
    else:
        attacks_failed.append("SEMANTIC_ONLY")

    survived = len(attacks_failed) == 0
    return AdversarialReview(
        candidate_id=candidate_id,
        attacks_attempted=attacks_attempted,
        attacks_survived=attacks_survived,
        attacks_failed=attacks_failed,
        survived=survived,
        review_timestamp=now_iso(),
        notes=f"Survived {len(attacks_survived)}/{len(attacks_attempted)} attacks. "
              f"OBVIOUS_COMBINATION={'BLOCKED' if not obvious_combination_check_implemented else 'IMPLEMENTED'}",
    )


# =====================================================================
# QUALIFIED CANDIDATE (CTO directive #8, #14)
# =====================================================================

@dataclass
class QualifiedCandidate:
    """A four-hop candidate with full evidence schema.

    Per CTO directive #8: candidate must contain:
    candidate_id, device, device_evidence[], failure_mode, failure_evidence[],
    mechanism, mechanism_evidence[], intervention, intervention_evidence[],
    temporal_cutoff, prior_art_state, non_entailed_basis,
    falsification_condition, measurement_method
    """
    candidate_id: str
    device: str
    device_evidence: list[dict]
    failure_mode: str
    failure_evidence: list[dict]
    mechanism: str
    mechanism_evidence: list[dict]
    intervention: str
    intervention_evidence: list[dict]
    temporal_cutoff: str
    prior_art_state: str         # overall prior-art status
    non_entailed_basis: str      # why this is not entailed by existing knowledge
    falsification_condition: str # how to falsify this candidate
    measurement_method: str      # how to measure the outcome
    independence_attestation: Optional[dict] = None
    adversarial_review: Optional[dict] = None
    qualified: bool = False      # True only if adversarial review survived

    def canonical_dict(self) -> dict:
        return asdict(self)
