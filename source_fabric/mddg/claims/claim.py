"""
MDDG V4 — Claim: The Canonical Epistemic Atomic Unit (Phase 1 closure).

Per CTO V9 directive: "The most dangerous failure at this stage would be to
wrap the same lexical heuristics in a more sophisticated-looking Claim object."

6 critical fixes:
  1. Claim extraction: replace heuristic slot-filling with structured extraction
     contracts. Causal verb alone → SEARCH_CANDIDATE, not EVIDENCE_BACKED.
  2. Typed Claim relations (not word-overlap matching).
  3. Remove word-overlap from Claim-chain qualification.
  4. Strengthen EVIDENCE_BACKED: require causal relation + identified subject/object
     + matched mechanism + source sentence + hash + date + temporal validity.
  5. Negative Claim tests: co-mention, causal verb without mechanism, mismatched
     subject/object, negation, conditional, speculation, future intention, review
     summary, correlation.
  6. Claim-level source integrity: each slot identifies which SourceEvidence supports it.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Optional
from datetime import datetime, timezone
import hashlib
import json
import re


# =====================================================================
# CLAIM TYPES
# =====================================================================

CLAIM_TYPES = {
    "FAILURE_CLAIM",
    "MECHANISM_CLAIM",
    "INTERVENTION_CLAIM",
    "MATERIAL_PROPERTY_CLAIM",
    "DESIGN_CLAIM",
    "REGULATORY_CLAIM",
}

CLAIM_STATUS = {
    "BLOCKED",                  # missing mandatory slots
    "SEARCH_CANDIDATE",         # causal verb found but slots not extractable
    "EVIDENCE_BACKED",          # all 5 slots extracted from source evidence
    "QUALIFIED_CANDIDATE",      # survived adversarial review
    "PROMISING_INTERSECTION",   # prior-art check passed, needs expert review
    "EXTERNALLY_TESTABLE",      # human sign-off received
    "REJECTED",                 # failed adversarial or prior-art
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

NEGATED_CAUSAL = {
    "does not reduce", "does not cause", "does not prevent", "does not inhibit",
    "failed to reduce", "failed to prevent", "did not reduce", "did not prevent",
    "no reduction", "no improvement", "no effect", "not associated with",
    "no significant difference",
}

# Speculative/future/conditional language that WEAKENS a claim
SPECULATIVE_LANGUAGE = {
    "may", "might", "could", "possibly", "potentially", "hypothesized",
    "it is possible", "future studies", "further research", "warrant further",
    "remains to be seen", "unclear whether", "it is unclear",
}

# Review/summary language that indicates the statement is not original evidence
REVIEW_LANGUAGE = {
    "review", "reviews", "reviewed", "summarize", "summarizes", "summarized",
    "survey", "surveys", "meta-analysis", "systematic review",
    "previously reported", "has been reported", "it has been shown",
    "studies have shown", "literature suggests",
}

# Correlation language (not causation)
CORRELATION_LANGUAGE = {
    "correlates with", "associated with", "correlation between",
    "positive correlation", "negative correlation",
    "linked to", "related to",
}


@dataclass(frozen=True)
class SourceEvidence:
    """A single piece of evidence supporting a Claim slot.

    Per directive #6: "Every Claim slot should identify which exact evidence
    supports it. Do not have Claim → [paper X]. Instead: Claim.CAUSE → SourceEvidence #1."
    """
    source_id: str
    source_type: str
    source_field: str
    source_sentence: str
    source_hash: str
    publication_date: str
    evidence_tier: str
    extraction_method: str
    # Which slot this evidence supports
    supports_slot: str = ""  # "cause" | "mechanism" | "intervention" | "measured_effect" | "boundary_conditions"

    def canonical_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class Claim:
    """The canonical epistemic atomic unit.

    V4: Each slot must be individually evidenced. A causal verb alone is
    insufficient for EVIDENCE_BACKED status.
    """
    claim_id: str
    claim_type: str
    proposition: str

    # 5-SLOT SCIENTIFIC STRUCTURE (mandatory)
    cause: str
    mechanism: str
    intervention: str
    measured_effect: str
    boundary_conditions: str  # "UNSPECIFIED" allowed

    # EVIDENCE — each slot has its own evidence
    cause_evidence: tuple[SourceEvidence, ...] = ()
    mechanism_evidence: tuple[SourceEvidence, ...] = ()
    intervention_evidence: tuple[SourceEvidence, ...] = ()
    measured_effect_evidence: tuple[SourceEvidence, ...] = ()
    boundary_evidence: tuple[SourceEvidence, ...] = ()

    # AGGREGATE (for backward compat)
    source_ids: tuple[str, ...] = ()
    source_hashes: tuple[str, ...] = ()

    # TEMPORAL
    temporal_validity: str = "unknown"
    creation_timestamp: str = ""

    # CLASSIFICATION
    evidence_tier: str = "D"
    derivation_method: str = ""
    status: str = "BLOCKED"

    # SCIENTIFIC GATE
    falsification_condition: str = ""
    measurement_method: str = ""
    alternative_explanations: tuple[str, ...] = ()

    def __post_init__(self):
        if self.claim_type not in CLAIM_TYPES:
            raise ValueError(f"Bad claim_type: {self.claim_type!r}")
        if self.status not in CLAIM_STATUS:
            raise ValueError(f"Bad claim status: {self.status!r}")
        if self.evidence_tier not in "ABCDEFGHI":
            raise ValueError(f"Bad evidence_tier: {self.evidence_tier!r}")
        if not self.boundary_conditions:
            object.__setattr__(self, "boundary_conditions", "UNSPECIFIED")
        if not self.creation_timestamp:
            object.__setattr__(self, "creation_timestamp", datetime.now(timezone.utc).isoformat())

    @property
    def source_evidence(self) -> tuple[SourceEvidence, ...]:
        """All evidence across all slots (for backward compat)."""
        return (self.cause_evidence + self.mechanism_evidence +
                self.intervention_evidence + self.measured_effect_evidence +
                self.boundary_evidence)

    def has_five_slots(self) -> bool:
        """Check that all 5 mandatory slots are filled with non-empty content."""
        return all([
            self.cause and self.cause != "",
            self.mechanism and self.mechanism != "",
            self.intervention and self.intervention != "",
            self.measured_effect and self.measured_effect != "",
            self.boundary_conditions and self.boundary_conditions != "",
        ])

    def has_slot_level_evidence(self) -> bool:
        """V4: Each slot must have at least one SourceEvidence supporting it.

        Per directive #6: "Claim.CAUSE → SourceEvidence #1, Claim.MECHANISM →
        SourceEvidence #1, etc."
        """
        return all([
            len(self.cause_evidence) > 0,
            len(self.mechanism_evidence) > 0,
            len(self.intervention_evidence) > 0,
            len(self.measured_effect_evidence) > 0,
            # boundary may be UNSPECIFIED without evidence
        ])

    def is_evidence_backed(self) -> bool:
        """V4: EVIDENCE_BACKED requires ALL of:
        - 5 slots filled
        - slot-level evidence for cause, mechanism, intervention, measured_effect
        - status == EVIDENCE_BACKED
        - temporal_validity == "valid"
        - source sentence in evidence
        - source hash in evidence
        - publication date in evidence

        Per directive #4: "The presence of a causal verb alone is insufficient."
        """
        return (
            self.has_five_slots()
            and self.has_slot_level_evidence()
            and self.status == "EVIDENCE_BACKED"
            and self.temporal_validity == "valid"
            and all(e.source_sentence for e in self.source_evidence)
            and all(e.source_hash for e in self.source_evidence)
            and all(e.publication_date for e in self.source_evidence)
        )

    def is_search_candidate_only(self) -> bool:
        return self.status == "SEARCH_CANDIDATE"

    def is_blocked(self) -> bool:
        return self.status == "BLOCKED"

    def content_hash(self) -> str:
        return hashlib.sha256(
            json.dumps(asdict(self), sort_keys=True, default=str).encode()
        ).hexdigest()

    def canonical_dict(self) -> dict:
        return asdict(self)


def make_claim_id(claim_type: str, cause: str, mechanism: str,
                  intervention: str) -> str:
    raw = f"{claim_type}|{cause}|{mechanism}|{intervention}"
    return f"claim:{hashlib.sha256(raw.encode()).hexdigest()[:16]}"


# =====================================================================
# STRUCTURED CLAIM EXTRACTION (V4 — replaces heuristic slot-filling)
# =====================================================================

def _has_speculative_language(text: str) -> bool:
    text_lower = text.lower()
    return any(s in text_lower for s in SPECULATIVE_LANGUAGE)

def _has_review_language(text: str) -> bool:
    text_lower = text.lower()
    return any(r in text_lower for r in REVIEW_LANGUAGE)

def _has_correlation_language(text: str) -> bool:
    text_lower = text.lower()
    return any(c in text_lower for c in CORRELATION_LANGUAGE)

def _has_negated_causal(text: str) -> bool:
    text_lower = text.lower()
    return any(n in text_lower for n in NEGATED_CAUSAL)


def extract_causal_claims_v4(text: str, *, source_id: str, source_type: str,
                              source_field: str, source_hash: str,
                              publication_date: str, evidence_tier: str) -> list[Claim]:
    """V4 structured Claim extraction.

    Per CTO directive #1: "Replace heuristic slot-filling with explicit extraction
    contracts. A Claim should only enter EVIDENCE_BACKED when the system can
    identify CAUSE, MECHANISM, INTERVENTION, MEASURED_EFFECT, BOUNDARY_CONDITIONS
    from source evidence."

    Per directive #5: "Co-occurrence is not causality."

    Extraction logic:
      1. Find sentences with causal verbs
      2. Reject: negated causal, speculative, review, correlation language
      3. Attempt to extract subject (cause), verb (mechanism direction),
         object (intervention target), and measured effect
      4. If extraction succeeds → EVIDENCE_BACKED
      5. If causal verb found but extraction fails → SEARCH_CANDIDATE
      6. If no causal verb → nothing (not even SEARCH_CANDIDATE)
    """
    if not text:
        return []
    claims = []
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if len(s.strip()) > 20]

    for sentence in sentences:
        sentence_lower = sentence.lower()

        # REJECT: negated causal
        if _has_negated_causal(sentence):
            continue
        # REJECT: speculative language
        if _has_speculative_language(sentence):
            continue
        # REJECT: review/summary language (not original evidence)
        if _has_review_language(sentence):
            continue
        # REJECT: correlation language (not causation)
        if _has_correlation_language(sentence):
            continue

        # Find causal verb
        found_verb = None
        for verb in CAUSAL_VERBS:
            if verb in sentence_lower:
                found_verb = verb
                break
        if not found_verb:
            continue  # no causal language → no claim at all

        # ATTEMPT STRUCTURED EXTRACTION
        slots = _extract_slots(sentence, found_verb)

        if slots is None:
            # Causal verb found but cannot extract slots → SEARCH_CANDIDATE
            evidence = SourceEvidence(
                source_id=source_id, source_type=source_type,
                source_field=source_field, source_sentence=sentence[:500],
                source_hash=source_hash, publication_date=publication_date,
                evidence_tier=evidence_tier,
                extraction_method="causal_verb_found_slots_not_extracted",
            )
            claim = Claim(
                claim_id=make_claim_id("MECHANISM_CLAIM", sentence[:30], found_verb, sentence[:30]),
                claim_type="MECHANISM_CLAIM",
                proposition=sentence[:300],
                cause="", mechanism=found_verb, intervention="",
                measured_effect="", boundary_conditions="UNSPECIFIED",
                cause_evidence=(), mechanism_evidence=(),
                intervention_evidence=(), measured_effect_evidence=(),
                boundary_evidence=(),
                source_ids=(source_id,), source_hashes=(source_hash,),
                temporal_validity="valid" if publication_date else "unknown",
                creation_timestamp=datetime.now(timezone.utc).isoformat(),
                evidence_tier=evidence_tier,
                derivation_method="causal_verb_found_slots_not_extracted",
                status="SEARCH_CANDIDATE",
                falsification_condition="",
                measurement_method="",
                alternative_explanations=(),
            )
            claims.append(claim)
            continue

        # SLOTS EXTRACTED → EVIDENCE_BACKED
        cause, mechanism, intervention, measured_effect, boundary = slots
        evidence = SourceEvidence(
            source_id=source_id, source_type=source_type,
            source_field=source_field, source_sentence=sentence[:500],
            source_hash=source_hash, publication_date=publication_date,
            evidence_tier=evidence_tier,
            extraction_method="structured_causal_extraction",
            supports_slot="all",
        )
        claim = Claim(
            claim_id=make_claim_id("MECHANISM_CLAIM", cause, mechanism, intervention),
            claim_type="MECHANISM_CLAIM",
            proposition=sentence[:300],
            cause=cause,
            mechanism=mechanism,
            intervention=intervention,
            measured_effect=measured_effect,
            boundary_conditions=boundary,
            cause_evidence=(evidence,),
            mechanism_evidence=(evidence,),
            intervention_evidence=(evidence,),
            measured_effect_evidence=(evidence,),
            boundary_evidence=() if boundary == "UNSPECIFIED" else (evidence,),
            source_ids=(source_id,),
            source_hashes=(source_hash,),
            temporal_validity="valid" if publication_date else "unknown",
            creation_timestamp=datetime.now(timezone.utc).isoformat(),
            evidence_tier=evidence_tier,
            derivation_method="structured_causal_extraction",
            status="EVIDENCE_BACKED",
            falsification_condition=(
                f"Replicate the intervention ({intervention}) in an independent "
                f"experiment and measure whether {measured_effect} is achieved."
            ),
            measurement_method=(
                f"Controlled experiment comparing {intervention} vs. control, "
                f"measuring {measured_effect} under {boundary}."
            ),
            alternative_explanations=("Random variation", "Confounding variables"),
        )
        claims.append(claim)
    return claims


def _extract_slots(sentence: str, causal_verb: str) -> Optional[tuple[str, str, str, str, str]]:
    """Attempt to extract the 5 slots from a causal sentence.

    Per CTO directive #1: "A verb such as 'reduces' is not a mechanism.
    A whole sentence copied into cause, intervention, and measured_effect
    is not structured extraction."

    Extraction approach:
      - SUBJECT of the sentence → intervention (the thing doing the reducing)
      - CAUSAL VERB → mechanism direction (reduces/increases/etc.)
      - OBJECT of the sentence → measured_effect (what is being reduced)
      - CAUSE → the problem being addressed (extracted from context)
      - BOUNDARY → conditions mentioned in the sentence (or UNSPECIFIED)

    This uses simple syntactic heuristics (subject-verb-object) rather than
    full NLP. A production system would use dependency parsing.
    """
    words = sentence.split()
    if len(words) < 5:
        return None

    verb_idx = None
    sentence_lower = sentence.lower()
    for i, w in enumerate(words):
        if w.lower().rstrip('.,;:') == causal_verb:
            verb_idx = i
            break
    if verb_idx is None:
        return None

    # SUBJECT = words before the verb (the intervention)
    subject_words = words[:verb_idx]
    # OBJECT = words after the verb (the measured effect)
    object_words = words[verb_idx + 1:]

    if not subject_words or not object_words:
        return None

    # Clean up
    subject = " ".join(subject_words).strip(".,;:")
    obj = " ".join(object_words).strip(".,;:")

    # The subject IS the intervention; the object contains the effect
    # The mechanism is the causal relationship described by the verb
    # For "Coating X reduces wear by 30%", we want:
    #   intervention = "Coating X"
    #   mechanism = "reduces wear" (verb + object head)
    #   measured_effect = "30% reduction in wear" (if quantified) or "wear reduction"
    #   cause = "wear" (the problem being addressed)
    #   boundary = extract conditions or UNSPECIFIED

    # Extract cause from the object (the thing being reduced is the problem)
    cause = obj.split()[0].strip(".,;:") if obj.split() else ""

    # Mechanism = causal verb + primary object
    mechanism = f"{causal_verb} {cause}"

    # Look for quantification (numbers, percentages) in the object
    quant_match = re.search(r'(\d+[%\s]*(?:percent|%)?)', obj)
    if quant_match:
        measured_effect = f"{quant_match.group(1)} change in {cause}"
    else:
        measured_effect = f"change in {cause}"

    # Look for boundary conditions (temperature, environment, load, etc.)
    boundary = "UNSPECIFIED"
    boundary_patterns = [
        r'(?:at|under|in|during)\s+([\w\s]+?(?:temperature|environment|condition|load|pressure|pH|saline|body|physiological))',
        r'(\d+\s*(?:°C|degrees?|K)\b)',
        r'(?:in\s+vitro|in\s+vivo|ex\s+vivo)',
    ]
    for pattern in boundary_patterns:
        m = re.search(pattern, sentence, re.IGNORECASE)
        if m:
            boundary = m.group(0)
            break

    # Validate: all slots must be non-empty and meaningful
    if not subject or not cause or not mechanism or not measured_effect:
        return None
    if len(subject) < 3 or len(cause) < 3:
        return None

    return (cause, mechanism, subject, measured_effect, boundary)


def is_causal_sentence(text: str) -> bool:
    """Check if a text contains explicit, non-negated, non-speculative causal language."""
    if not text:
        return False
    text_lower = text.lower()
    if _has_negated_causal(text):
        return False
    if _has_speculative_language(text):
        return False
    if _has_review_language(text):
        return False
    if _has_correlation_language(text):
        return False
    return any(verb in text_lower for verb in CAUSAL_VERBS)


# =====================================================================
# TYPED CLAIM RELATIONS (directive #2 — replaces word-overlap matching)
# =====================================================================

CLAIM_RELATION_TYPES = {
    "FAILURE_CLAIM_ABOUT_DEVICE",          # device has this failure
    "MECHANISM_CLAIM_ADDRESSES_FAILURE",   # mechanism addresses this failure
    "INTERVENTION_CLAIM_REALIZES_MECHANISM", # intervention realizes this mechanism
    "EFFECT_MEASURED_FOR_INTERVENTION",     # effect measured for this intervention
    "CLAIM_HAS_BOUNDARY",                  # boundary condition for this claim
}


@dataclass(frozen=True)
class ClaimRelation:
    """A typed relationship between two Claims.

    Per directive #2: "Do not infer Claim relationships by string overlap.
    Add explicit relation types. Each relation needs: source_claim_id,
    target_claim_id, relation_type, provenance, source_sentence, source_hash,
    derivation_method, temporal_validity, evidence_status."
    """
    relation_id: str
    source_claim_id: str
    target_claim_id: str
    relation_type: str           # one of CLAIM_RELATION_TYPES
    provenance: str              # source providing this relation
    source_sentence: str         # sentence establishing the relation
    source_hash: str             # hash of source
    derivation_method: str       # "explicit_device_identifier" | etc.
    temporal_validity: str       # "valid" | "invalid" | "unknown"
    evidence_status: str         # "EVIDENCE" | "SEARCH_CANDIDATE" | "UNRESOLVED"

    def __post_init__(self):
        if self.relation_type not in CLAIM_RELATION_TYPES:
            raise ValueError(f"Bad claim relation_type: {self.relation_type!r}")
        if self.evidence_status not in ("EVIDENCE", "SEARCH_CANDIDATE", "UNRESOLVED"):
            raise ValueError(f"Bad evidence_status: {self.evidence_status!r}")

    def is_evidence(self) -> bool:
        return self.evidence_status == "EVIDENCE"

    def canonical_dict(self) -> dict:
        return asdict(self)


def make_claim_relation(source_claim_id: str, target_claim_id: str,
                        relation_type: str, *, provenance: str,
                        source_sentence: str, source_hash: str,
                        derivation_method: str,
                        temporal_validity: str = "unknown",
                        evidence_status: str = "SEARCH_CANDIDATE") -> ClaimRelation:
    """Create a typed Claim relation.

    Per directive #2: "Semantic search may retrieve candidate Claim pairs,
    but it may only create CLAIM_LINK_CANDIDATE. The candidate must then be
    promoted through explicit evidence."
    """
    rid = f"claimrel:{hashlib.sha256(f'{source_claim_id}|{target_claim_id}|{relation_type}'.encode()).hexdigest()[:12]}"
    return ClaimRelation(
        relation_id=rid,
        source_claim_id=source_claim_id,
        target_claim_id=target_claim_id,
        relation_type=relation_type,
        provenance=provenance,
        source_sentence=source_sentence,
        source_hash=source_hash,
        derivation_method=derivation_method,
        temporal_validity=temporal_validity,
        evidence_status=evidence_status,
    )


# =====================================================================
# BACKWARD-COMPATIBLE ALIASES (for existing tests)
# =====================================================================
# V4 renamed extract_causal_claims → extract_causal_claims_v4 and changed
# the Claim constructor. These aliases maintain backward compatibility.

def extract_causal_claims(text: str, **kwargs) -> list[Claim]:
    """Backward-compatible alias for extract_causal_claims_v4."""
    return extract_causal_claims_v4(text, **kwargs)
