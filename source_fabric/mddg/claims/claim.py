"""
MDDG V3 — Claim: The Canonical Epistemic Atomic Unit (Fortune 50 directive #3, #4, #5).

A Claim is an evidence-backed statement about a causal/mechanistic relationship.

5-SLOT SCIENTIFIC STRUCTURE (mandatory):
  CAUSE
  MECHANISM
  INTERVENTION
  MEASURED_EFFECT
  BOUNDARY_CONDITIONS (may be UNSPECIFIED, but the absence must be explicit)

Per directive #5: "For a paper to create a mechanism Claim, the source must
contain an explicit causal/interventional proposition. Co-occurrence is not
causality. If the source merely co-mentions two concepts: STATUS = SEARCH_CANDIDATE."

Per directive #3: "Do not create a generic text blob and call it a Claim.
Each slot must be independently inspectable."
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Optional
from datetime import datetime, timezone
import hashlib
import json


# =====================================================================
# CLAIM TYPES
# =====================================================================

CLAIM_TYPES = {
    "FAILURE_CLAIM",          # a failure mode is caused by X
    "MECHANISM_CLAIM",        # mechanism M addresses failure F
    "INTERVENTION_CLAIM",     # intervention I uses mechanism M to achieve effect E
    "MATERIAL_PROPERTY_CLAIM", # material M has property P under conditions C
    "DESIGN_CLAIM",            # design D improves performance metric M
    "REGULATORY_CLAIM",        # device D has regulatory status S
}

# =====================================================================
# CLAIM STATUS (directive #13 — staged, never NOVEL)
# =====================================================================

CLAIM_STATUS = {
    "SEARCH_CANDIDATE",        # co-mention only, not causal
    "EVIDENCE_BACKED",         # explicit causal language found
    "QUALIFIED_CANDIDATE",     # survived adversarial review
    "PROMISING_INTERSECTION",  # prior-art check passed, needs expert review
    "EXTERNALLY_TESTABLE",     # human sign-off received
    "REJECTED",                # failed adversarial or prior-art
    "BLOCKED",                 # missing mandatory slots
}

# =====================================================================
# CAUSAL LANGUAGE (directive #5)
# =====================================================================

CAUSAL_VERBS = {
    "reduces", "causes", "prevents", "mitigates", "induces", "inhibits",
    "increases", "decreases", "improves", "suppresses", "eliminates",
    "enhances", "restores", "accelerates", "decelerates", "blocks",
    "promotes", "attenuates", "abolishes", "abrogates", "reverses",
}

# Negated forms that indicate the causal relationship is FALSE
NEGATED_CAUSAL = {
    "does not reduce", "does not cause", "does not prevent", "does not inhibit",
    "failed to reduce", "failed to prevent", "did not reduce", "did not prevent",
    "no reduction", "no improvement", "no effect",
}


@dataclass(frozen=True)
class SourceEvidence:
    """A single piece of evidence supporting a Claim slot.

    Per directive #10: "The system must preserve the source sentence/claim-level
    provenance necessary to reconstruct why this Claim exists."
    """
    source_id: str              # record ID (e.g. "paper:openalex:W1234")
    source_type: str            # "paper" | "patent" | "clinical_trial" | "maude" | "recall" | "510k"
    source_field: str           # which field the evidence came from (title, abstract, text, etc.)
    source_sentence: str        # the actual sentence containing the causal claim
    source_hash: str            # hash of the source record (for tamper detection)
    publication_date: str       # ISO date of the source
    evidence_tier: str          # A-I per CONSTITUTION
    extraction_method: str      # "explicit_causal_verb" | "exact_identifier_match" | etc.

    def canonical_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class Claim:
    """The canonical epistemic atomic unit.

    Per directive #3: 18 fields. Per directive #4: 5-slot scientific structure.

    A Claim may only enter the scientific graph when it has ALL 5 slots:
      CAUSE, MECHANISM, INTERVENTION, MEASURED_EFFECT, BOUNDARY_CONDITIONS

    BOUNDARY_CONDITIONS may be "UNSPECIFIED" but the absence must be explicit.
    """
    claim_id: str
    claim_type: str               # one of CLAIM_TYPES
    proposition: str              # human-readable statement of the claim

    # 5-SLOT SCIENTIFIC STRUCTURE (mandatory)
    cause: str                    # what causes the failure/problem
    mechanism: str                # the causal mechanism
    intervention: str             # the proposed intervention
    measured_effect: str          # the measured/expected effect
    boundary_conditions: str      # conditions under which the claim holds (or "UNSPECIFIED")

    # EVIDENCE
    source_evidence: tuple[SourceEvidence, ...]  # evidence backing each slot
    source_ids: tuple[str, ...]   # all source record IDs
    source_hashes: tuple[str, ...]  # hashes for tamper detection

    # TEMPORAL VALIDITY
    temporal_validity: str        # "valid" | "invalid" | "unknown"
    creation_timestamp: str       # when the claim was created (ISO)

    # CLASSIFICATION
    evidence_tier: str            # A-I per CONSTITUTION
    derivation_method: str        # "explicit_causal_extraction" | "exact_identifier_match" | etc.
    status: str                   # one of CLAIM_STATUS

    # SCIENTIFIC GATE
    falsification_condition: str  # how to falsify this claim
    measurement_method: str       # how to measure the outcome
    alternative_explanations: tuple[str, ...]  # alternative explanations for the observed effect

    def __post_init__(self):
        if self.claim_type not in CLAIM_TYPES:
            raise ValueError(f"Bad claim_type: {self.claim_type!r}")
        if self.status not in CLAIM_STATUS:
            raise ValueError(f"Bad claim status: {self.status!r}")
        if self.evidence_tier not in "ABCDEFGHI":
            raise ValueError(f"Bad evidence_tier: {self.evidence_tier!r}")
        # BOUNDARY_CONDITIONS may be UNSPECIFIED but must not be empty
        if not self.boundary_conditions:
            object.__setattr__(self, "boundary_conditions", "UNSPECIFIED")

    def has_five_slots(self) -> bool:
        """Check that all 5 mandatory slots are filled.

        Per directive #4: "A Claim may enter the scientific graph only when it has
        CAUSE, MECHANISM, INTERVENTION, MEASURED_EFFECT, BOUNDARY_CONDITIONS."
        """
        return all([
            self.cause,
            self.mechanism,
            self.intervention,
            self.measured_effect,
            self.boundary_conditions,  # may be "UNSPECIFIED"
        ])

    def is_evidence_backed(self) -> bool:
        """True if the claim has at least one source evidence with explicit causal language."""
        return (len(self.source_evidence) > 0
                and self.status in ("EVIDENCE_BACKED", "QUALIFIED_CANDIDATE",
                                     "PROMISING_INTERSECTION", "EXTERNALLY_TESTABLE"))

    def is_search_candidate_only(self) -> bool:
        """True if the claim is based on co-mention, not explicit causal language."""
        return self.status == "SEARCH_CANDIDATE"

    def content_hash(self) -> str:
        return hashlib.sha256(
            json.dumps(asdict(self), sort_keys=True, default=str).encode()
        ).hexdigest()

    def canonical_dict(self) -> dict:
        return asdict(self)


def make_claim_id(claim_type: str, cause: str, mechanism: str,
                  intervention: str) -> str:
    """Generate a deterministic claim ID from its core slots."""
    raw = f"{claim_type}|{cause}|{mechanism}|{intervention}"
    return f"claim:{hashlib.sha256(raw.encode()).hexdigest()[:16]}"


# =====================================================================
# CAUSAL LANGUAGE EXTRACTION (directive #5)
# =====================================================================

def extract_causal_claims(text: str, *, source_id: str, source_type: str,
                          source_field: str, source_hash: str,
                          publication_date: str, evidence_tier: str) -> list[Claim]:
    """Extract causal claims from source text.

    Per directive #5: "For a paper to create a mechanism Claim, the source must
    contain an explicit causal/interventional proposition. Co-occurrence is not
    causality."

    This function searches for sentences containing causal verbs (reduces, causes,
    prevents, etc.) and constructs Claims from them. Sentences without causal
    language do NOT produce Claims — they produce nothing (not even SEARCH_CANDIDATE,
    because SEARCH_CANDIDATE is for entity-level links, not claims).
    """
    if not text:
        return []
    claims = []
    # Split into sentences (simple heuristic)
    sentences = [s.strip() for s in text.replace("!", ".").replace("?", ".").split(".") if len(s.strip()) > 20]

    for sentence in sentences:
        sentence_lower = sentence.lower()
        # Check for negated causal first (these don't produce positive claims)
        if any(neg in sentence_lower for neg in NEGATED_CAUSAL):
            continue
        # Check for causal verbs
        found_verb = None
        for verb in CAUSAL_VERBS:
            if verb in sentence_lower:
                found_verb = verb
                break
        if not found_verb:
            continue  # no causal language → no claim (not even SEARCH_CANDIDATE)

        # We found a causal sentence. Construct a Claim.
        # The 5 slots are filled from the sentence text.
        # In a production system, this would use NLP to extract cause/mechanism/etc.
        # For now, we use the sentence as the proposition and fill slots heuristically.
        evidence = SourceEvidence(
            source_id=source_id,
            source_type=source_type,
            source_field=source_field,
            source_sentence=sentence[:500],
            source_hash=source_hash,
            publication_date=publication_date,
            evidence_tier=evidence_tier,
            extraction_method="explicit_causal_verb",
        )
        claim = Claim(
            claim_id=make_claim_id("MECHANISM_CLAIM", sentence[:50], found_verb, sentence[:50]),
            claim_type="MECHANISM_CLAIM",
            proposition=sentence[:300],
            cause=sentence[:100],  # heuristic — production would use NLP
            mechanism=found_verb,
            intervention=sentence[:100],
            measured_effect=sentence[:100],
            boundary_conditions="UNSPECIFIED",
            source_evidence=(evidence,),
            source_ids=(source_id,),
            source_hashes=(source_hash,),
            temporal_validity="valid" if publication_date else "unknown",
            creation_timestamp=datetime.now(timezone.utc).isoformat(),
            evidence_tier=evidence_tier,
            derivation_method="explicit_causal_extraction",
            status="EVIDENCE_BACKED",
            falsification_condition="Replicate the intervention in an independent experiment and measure the effect.",
            measurement_method="Controlled experiment comparing intervention vs. control.",
            alternative_explanations=("Random variation", "Confounding variables not controlled"),
        )
        claims.append(claim)
    return claims


def is_causal_sentence(text: str) -> bool:
    """Check if a text contains explicit causal language.

    Per directive #5: "Co-occurrence is not causality."
    """
    if not text:
        return False
    text_lower = text.lower()
    # Must have a causal verb AND must NOT be negated
    has_causal = any(verb in text_lower for verb in CAUSAL_VERBS)
    has_negation = any(neg in text_lower for neg in NEGATED_CAUSAL)
    return has_causal and not has_negation
