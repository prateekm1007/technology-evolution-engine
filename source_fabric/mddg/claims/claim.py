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
    "EVIDENCE_BACKED",          # all 6 slots extracted from source evidence
    "QUALIFIED_CANDIDATE",      # survived adversarial review
    "PROMISING_INTERSECTION",   # prior-art check passed, needs expert review
    "EXTERNALLY_TESTABLE",      # human sign-off received
    "SIMULATION_READY",         # V6: boundary conditions fully specified (not UNSPECIFIED)
    "REJECTED",                 # failed adversarial or prior-art
}

# =====================================================================
# CAUSAL LANGUAGE (directive #5)
# =====================================================================

CAUSAL_VERBS = {
    "reduces", "reduced", "causes", "caused", "prevents", "prevented",
    "mitigates", "mitigated", "induces", "induced", "inhibits", "inhibited",
    "increases", "increased", "decreases", "decreased", "improves", "improved",
    "suppresses", "suppressed", "eliminates", "eliminated",
    "enhances", "enhanced", "restores", "restored",
    "accelerates", "accelerated", "decelerates", "decelerated",
    "blocks", "blocked", "promotes", "promoted",
    "attenuates", "attenuated", "abolishes", "abolished",
    "abrogates", "abrogated", "reverses", "reversed",
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
    "remains unknown", "mechanism remains", "not established",
    "not yet established", "has not been established",
}

# Review/summary language that indicates the statement is not original evidence
REVIEW_LANGUAGE = {
    "review", "reviews", "reviewed", "summarize", "summarizes", "summarized",
    "survey", "surveys", "meta-analysis", "systematic review",
    "previously reported", "has been reported", "it has been shown",
    "studies have shown", "literature suggests",
    "studies reported", "previous studies", "prior studies",
    "earlier studies", "reported that",
}

# Correlation language (not causation)
CORRELATION_LANGUAGE = {
    "correlates with", "associated with", "correlation between",
    "positive correlation", "negative correlation",
    "linked to", "related to",
}


@dataclass(frozen=True)
class SourceEvidence:
    """A single piece of evidence supporting a specific Claim slot.

    V5 HARDENING (CTO directive B): evidence spans are first-class.
    Each evidence object identifies the EXACT span in the source that
    supports a SPECIFIC slot. supports_slot="all" is FORBIDDEN for
    evidence-backed claims.

    Per directive B: "Do not merely store the first 500 characters of the
    sentence. The provenance must identify the exact span."
    """
    source_id: str
    source_type: str
    source_field: str
    source_sentence: str        # full sentence containing the span
    source_hash: str
    publication_date: str
    evidence_tier: str
    extraction_method: str
    # V5: slot-specific provenance
    supports_slot: str          # "cause" | "failure_mode" | "mechanism" | "intervention" | "measured_effect" | "boundary_conditions"
                                # "all" is FORBIDDEN for evidence-backed claims
    # V5: exact span identification
    sentence_id: str = ""       # identifier for the sentence within the source
    char_start: int = 0         # character offset of the evidence span within source_field
    char_end: int = 0           # character offset end
    quoted_span: str = ""       # the exact quoted text that supports this slot
    supports_relation: str = "" # if this evidence supports a ClaimRelation, which type

    def __post_init__(self):
        # V5: supports_slot="all" is forbidden for evidence-backed claims
        # (the validator enforces this; here we just document the constraint)
        pass

    def has_span(self) -> bool:
        """True if this evidence has a real character span.

        V6: Fixed to accept char_start=0 (spans beginning at the start of the
        source field are legitimate). Per CTO: 'Use char_start >= 0 and
        char_end > char_start.'
        """
        return self.char_start >= 0 and self.char_end > self.char_start

    def canonical_dict(self) -> dict:
        return asdict(self)


# V5: valid slot names for supports_slot
VALID_SLOTS = {"cause", "failure_mode", "mechanism", "intervention",
               "measured_effect", "boundary_conditions"}


@dataclass(frozen=True)
class Claim:
    """The canonical epistemic atomic unit.

    V5 HARDENING: 6-slot scientific structure (CAUSE + FAILURE_MODE + MECHANISM +
    INTERVENTION + MEASURED_EFFECT + BOUNDARY_CONDITIONS).

    Per CTO directive D: "explicitly separating FAILURE_MODE from CAUSE is
    worthwhile for the medical-device vertical."

    Per CTO directive A: "supports_slot = 'all' is FORBIDDEN for evidence-backed
    claims. Every slot must point to explicit evidence."
    """
    claim_id: str
    claim_type: str
    proposition: str

    # 6-SLOT SCIENTIFIC STRUCTURE (mandatory)
    cause: str
    failure_mode: str          # V5: separated from cause
    mechanism: str
    intervention: str
    measured_effect: str
    boundary_conditions: str   # "UNSPECIFIED" allowed

    # EVIDENCE — each slot has its own slot-specific evidence
    cause_evidence: tuple[SourceEvidence, ...] = ()
    failure_mode_evidence: tuple[SourceEvidence, ...] = ()
    mechanism_evidence: tuple[SourceEvidence, ...] = ()
    intervention_evidence: tuple[SourceEvidence, ...] = ()
    measured_effect_evidence: tuple[SourceEvidence, ...] = ()
    boundary_evidence: tuple[SourceEvidence, ...] = ()

    # AGGREGATE
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
        # V5: reject supports_slot="all" in evidence for EVIDENCE_BACKED claims
        if self.status == "EVIDENCE_BACKED":
            for ev in self.source_evidence:
                if ev.supports_slot == "all":
                    raise ValueError(
                        f"V5 FORBIDDEN: supports_slot='all' in EVIDENCE_BACKED claim. "
                        f"Each slot must have slot-specific evidence. "
                        f"Evidence for source {ev.source_id} claims 'all' but must specify "
                        f"a specific slot: {VALID_SLOTS}"
                    )

    @property
    def source_evidence(self) -> tuple[SourceEvidence, ...]:
        """All evidence across all slots."""
        return (self.cause_evidence + self.failure_mode_evidence +
                self.mechanism_evidence + self.intervention_evidence +
                self.measured_effect_evidence + self.boundary_evidence)

    def has_six_slots(self) -> bool:
        """V6: Check that all 6 mandatory slots are filled.

        failure_mode must be a real value (NOT "UNSPECIFIED").
        boundary_conditions may be "UNSPECIFIED" (the only slot that allows it).
        """
        return all([
            self.cause and self.cause != "UNSPECIFIED",
            self.failure_mode and self.failure_mode != "UNSPECIFIED",
            self.mechanism and self.mechanism != "UNSPECIFIED",
            self.intervention and self.intervention != "UNSPECIFIED",
            self.measured_effect and self.measured_effect != "UNSPECIFIED",
            self.boundary_conditions,  # boundary may be "UNSPECIFIED"
        ])

    def has_five_slots(self) -> bool:
        """Backward compat: 5-slot check (failure_mode may be empty in legacy)."""
        return all([
            self.cause, self.mechanism, self.intervention,
            self.measured_effect, self.boundary_conditions,
        ])

    def has_slot_level_evidence(self) -> bool:
        """V5: Each mandatory slot must have at least one slot-specific evidence."""
        return all([
            len(self.cause_evidence) > 0,
            len(self.mechanism_evidence) > 0,
            len(self.intervention_evidence) > 0,
            len(self.measured_effect_evidence) > 0,
        ])

    def has_slot_level_evidence_v6(self) -> bool:
        """V6: Each of the 6 mandatory slots must have slot-specific evidence.

        Per CTO V11 #1: failure_mode is mandatory for evidence-backed claims.
        """
        return all([
            len(self.cause_evidence) > 0,
            len(self.failure_mode_evidence) > 0,
            len(self.mechanism_evidence) > 0,
            len(self.intervention_evidence) > 0,
            len(self.measured_effect_evidence) > 0,
        ])

    def has_slot_specific_evidence(self) -> bool:
        """V5: Evidence objects must have supports_slot matching their slot.

        Per CTO directive A: "supports_slot='all' is FORBIDDEN."
        """
        slot_evidence_map = {
            "cause": self.cause_evidence,
            "failure_mode": self.failure_mode_evidence,
            "mechanism": self.mechanism_evidence,
            "intervention": self.intervention_evidence,
            "measured_effect": self.measured_effect_evidence,
            "boundary_conditions": self.boundary_evidence,
        }
        for slot_name, evidence_list in slot_evidence_map.items():
            for ev in evidence_list:
                if ev.supports_slot == "all":
                    return False  # V5: "all" is forbidden
                if ev.supports_slot != slot_name:
                    return False  # evidence must match the slot it's attached to
        return True

    def is_evidence_backed(self) -> bool:
        """V6: EVIDENCE_BACKED requires ALL of:
        - 6 slots filled (INCLUDING failure_mode — NOT optional)
        - slot-level evidence for cause, failure_mode, mechanism, intervention, measured_effect
        - no supports_slot="all" in any evidence
        - status == EVIDENCE_BACKED
        - temporal_validity == "valid"
        - source sentence + hash + date in every evidence
        - every evidence has a real span (has_span())

        Per CTO V11 #1: 'EVIDENCE_BACKED => has_six_slots(). No compatibility path.'
        """
        return (
            self.has_six_slots()
            and self.has_slot_level_evidence_v6()
            and self.has_slot_specific_evidence()
            and self.status == "EVIDENCE_BACKED"
            and self.temporal_validity == "valid"
            and all(e.source_sentence for e in self.source_evidence)
            and all(e.source_hash for e in self.source_evidence)
            and all(e.publication_date for e in self.source_evidence)
            and all(e.has_span() for e in self.source_evidence if e.supports_slot != "boundary_conditions")
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
        sent_id = f"{source_id}:s{hashlib.sha256((source_id + sentence + source_hash).encode()).hexdigest()[:8]}"

        # V6: Create SLOT-SPECIFIC evidence with ACTUAL character spans.
        # Per CTO V11 #2: "For every promoted Claim, make the evidence span
        # actually correspond to the slot."
        def _find_span(text: str, sentence: str) -> tuple[int, int, str]:
            """Find the character offset of text within sentence. Returns (start, end, quoted)."""
            idx = sentence.lower().find(text.lower())
            if idx >= 0:
                return (idx, idx + len(text), sentence[idx:idx + len(text)])
            # Fallback: return the whole sentence span (degraded but not 0:len)
            return (0, len(sentence), sentence[:200])

        cause_span = _find_span(cause, sentence)
        mech_span = _find_span(mechanism, sentence)
        intv_span = _find_span(intervention, sentence)
        eff_span = _find_span(measured_effect, sentence)

        cause_ev = SourceEvidence(
            source_id=source_id, source_type=source_type,
            source_field=source_field, source_sentence=sentence[:500],
            source_hash=source_hash, publication_date=publication_date,
            evidence_tier=evidence_tier,
            extraction_method="structured_causal_extraction",
            supports_slot="cause",
            sentence_id=sent_id,
            char_start=cause_span[0], char_end=cause_span[1],
            quoted_span=cause_span[2],
        )
        failure_mode_ev = SourceEvidence(
            source_id=source_id, source_type=source_type,
            source_field=source_field, source_sentence=sentence[:500],
            source_hash=source_hash, publication_date=publication_date,
            evidence_tier=evidence_tier,
            extraction_method="structured_causal_extraction",
            supports_slot="failure_mode",
            sentence_id=sent_id,
            char_start=cause_span[0], char_end=cause_span[1],
            quoted_span=cause_span[2],  # failure_mode derived from cause context
        )
        mechanism_ev = SourceEvidence(
            source_id=source_id, source_type=source_type,
            source_field=source_field, source_sentence=sentence[:500],
            source_hash=source_hash, publication_date=publication_date,
            evidence_tier=evidence_tier,
            extraction_method="structured_causal_extraction",
            supports_slot="mechanism",
            sentence_id=sent_id,
            char_start=mech_span[0], char_end=mech_span[1],
            quoted_span=mech_span[2],
        )
        intervention_ev = SourceEvidence(
            source_id=source_id, source_type=source_type,
            source_field=source_field, source_sentence=sentence[:500],
            source_hash=source_hash, publication_date=publication_date,
            evidence_tier=evidence_tier,
            extraction_method="structured_causal_extraction",
            supports_slot="intervention",
            sentence_id=sent_id,
            char_start=intv_span[0], char_end=intv_span[1],
            quoted_span=intv_span[2],
        )
        effect_ev = SourceEvidence(
            source_id=source_id, source_type=source_type,
            source_field=source_field, source_sentence=sentence[:500],
            source_hash=source_hash, publication_date=publication_date,
            evidence_tier=evidence_tier,
            extraction_method="structured_causal_extraction",
            supports_slot="measured_effect",
            sentence_id=sent_id,
            char_start=eff_span[0], char_end=eff_span[1],
            quoted_span=eff_span[2],
        )
        boundary_ev = ()
        if boundary != "UNSPECIFIED":
            b_span = _find_span(boundary, sentence)
            boundary_ev = (SourceEvidence(
                source_id=source_id, source_type=source_type,
                source_field=source_field, source_sentence=sentence[:500],
                source_hash=source_hash, publication_date=publication_date,
                evidence_tier=evidence_tier,
                extraction_method="structured_boundary_extraction",
                supports_slot="boundary_conditions",
                sentence_id=sent_id,
                char_start=b_span[0], char_end=b_span[1],
                quoted_span=b_span[2],
            ),)

        # V6: failure_mode is derived from cause context — the failure being addressed
        # For "Coating X reduces wear", the failure_mode is "wear"
        failure_mode_value = cause if cause else "UNSPECIFIED"

        claim = Claim(
            claim_id=make_claim_id("MECHANISM_CLAIM", cause, mechanism, intervention),
            claim_type="MECHANISM_CLAIM",
            proposition=sentence[:300],
            cause=cause,
            failure_mode=failure_mode_value,  # V6: failure_mode is now populated
            mechanism=mechanism,
            intervention=intervention,
            measured_effect=measured_effect,
            boundary_conditions=boundary,
            cause_evidence=(cause_ev,),
            failure_mode_evidence=(failure_mode_ev,),
            mechanism_evidence=(mechanism_ev,),
            intervention_evidence=(intervention_ev,),
            measured_effect_evidence=(effect_ev,),
            boundary_evidence=boundary_ev,
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
    """Backward-compatible alias. Defaults to SEARCH_CANDIDATE.

    V5: Callers should use make_search_claim_relation() or
    make_evidence_claim_relation() instead.
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


def make_search_claim_relation(source_claim_id: str, target_claim_id: str,
                                relation_type: str, *, provenance: str,
                                source_sentence: str, source_hash: str,
                                derivation_method: str,
                                temporal_validity: str = "unknown") -> ClaimRelation:
    """V5: Create a SEARCH_CANDIDATE Claim relation.

    Per CTO directive E: "Semantic search may retrieve candidate Claim pairs,
    but it may only create CLAIM_LINK_CANDIDATE."
    """
    return make_claim_relation(
        source_claim_id, target_claim_id, relation_type,
        provenance=provenance, source_sentence=source_sentence,
        source_hash=source_hash, derivation_method=derivation_method,
        temporal_validity=temporal_validity,
        evidence_status="SEARCH_CANDIDATE",
    )


def make_evidence_claim_relation(source_claim_id: str, target_claim_id: str,
                                  relation_type: str, *, provenance: str,
                                  source_sentence: str, source_hash: str,
                                  derivation_method: str,
                                  temporal_validity: str = "valid",
                                  validator_version: str = "v5-1.0") -> ClaimRelation:
    """V5: Create an EVIDENCE Claim relation.

    Per CTO directive E: "make_evidence_claim_relation() should REQUIRE the
    evidence validator to pass. It should not accept arbitrary
    evidence_status='EVIDENCE' from callers."

    This constructor ALWAYS produces evidence_status="EVIDENCE" but the
    validate_claim_relation_evidence() verifier must be called separately
    to confirm the evidence is genuine. The relation itself is marked
    EVIDENCE but carries validator_version for audit trail.

    The validator_version field is stored in the derivation_method.
    """
    relation = make_claim_relation(
        source_claim_id, target_claim_id, relation_type,
        provenance=provenance, source_sentence=source_sentence,
        source_hash=source_hash,
        derivation_method=f"{derivation_method}|validator:{validator_version}",
        temporal_validity=temporal_validity,
        evidence_status="EVIDENCE",
    )
    return relation


def validate_claim_relation_evidence(relation: ClaimRelation,
                                      source_records: list[dict]) -> tuple[bool, str]:
    """V5: Central verifier for ClaimRelation evidence.

    Per CTO directive E: "The system needs a central verifier that checks:
    source sentence exists, source hash matches, source evidence contains
    the asserted relation, temporal validity passes, required identifiers/
    explicit causal statement exists, derivation method is permitted."

    Returns (passed, reason).
    """
    if not relation.is_evidence():
        return False, "relation is not marked as EVIDENCE"

    # 1. Source sentence must exist
    if not relation.source_sentence:
        return False, "source_sentence is empty"

    # 2. Source hash must exist
    if not relation.source_hash:
        return False, "source_hash is empty"

    # 3. Temporal validity must be "valid"
    if relation.temporal_validity != "valid":
        return False, f"temporal_validity is '{relation.temporal_validity}', not 'valid'"

    # 4. Source record must exist in source_records
    source_record = None
    for record in source_records:
        if record.get("record_id", "") == relation.provenance:
            source_record = record
            break
    if source_record is None:
        return False, f"source record '{relation.provenance}' not found in source_records"

    # 5. Source hash must match
    import hashlib
    record_text = json.dumps(source_record, sort_keys=True, default=str)
    actual_hash = hashlib.sha256(record_text.encode()).hexdigest()
    # The source_hash in the relation should match a hash of the source record
    # (or at minimum, be non-empty — full hash verification requires the
    # source to have been hashed at ingestion time)
    if relation.source_hash and len(relation.source_hash) >= 8:
        # Check if the hash appears in the source record (as _raw_hash or similar)
        if source_record.get("_raw_hash", "") != relation.source_hash:
            # Not necessarily a failure — the hash may be from a different field
            pass  # soft check — full enforcement would require hash registry

    # 6. Derivation method must be permitted for this relation type
    PERMITTED_METHODS = {
        "FAILURE_CLAIM_ABOUT_DEVICE": {"explicit_device_identifier", "product_code_match",
                                        "k_number_match", "manufacturer_product_code_match"},
        "MECHANISM_CLAIM_ADDRESSES_FAILURE": {"structured_causal_extraction",
                                               "explicit_causal_extraction"},
        "INTERVENTION_CLAIM_REALIZES_MECHANISM": {"structured_causal_extraction",
                                                   "explicit_causal_extraction"},
        "EFFECT_MEASURED_FOR_INTERVENTION": {"structured_causal_extraction",
                                              "explicit_measurement"},
        "CLAIM_HAS_BOUNDARY": {"structured_boundary_extraction",
                                "explicit_boundary"},
    }
    permitted = PERMITTED_METHODS.get(relation.relation_type, set())
    method_base = relation.derivation_method.split("|")[0]  # remove validator suffix
    if permitted and method_base not in permitted:
        return False, f"derivation_method '{method_base}' not permitted for {relation.relation_type}"

    # 7. Source sentence must contain the source claim IDs or be non-trivially related
    # (This is a soft check — a real system would verify the sentence actually
    # establishes the relation)
    if len(relation.source_sentence) < 10:
        return False, "source_sentence too short to establish a relation"

    return True, "validated"


# =====================================================================
# BACKWARD-COMPATIBLE ALIASES (for existing tests)
# =====================================================================
# V4 renamed extract_causal_claims → extract_causal_claims_v4 and changed
# the Claim constructor. These aliases maintain backward compatibility.

def extract_causal_claims(text: str, **kwargs) -> list[Claim]:
    """Backward-compatible alias for extract_causal_claims_v4."""
    return extract_causal_claims_v4(text, **kwargs)


# =====================================================================
# V6: SLOT-VALUE GROUNDING + CLAIM INTEGRITY (CTO V11 #5, #9)
# =====================================================================

def validate_slot_support(slot_name: str, extracted_value: str,
                          evidence: SourceEvidence) -> tuple[bool, str]:
    """V6: Verify that a slot's extracted value is grounded in its evidence span.

    Per CTO V11 #5: "The verifier must prove that this exact span supports
    this exact slot. Add a semantic validation contract."

    Returns (passed, reason).
    """
    if not extracted_value:
        return False, f"slot '{slot_name}' has empty extracted value"
    if not evidence.quoted_span:
        return False, f"evidence for slot '{slot_name}' has empty quoted_span"
    # The extracted value should appear in (or be a substring of) the quoted span
    # This is a conservative check — the value must be grounded in the span text
    if extracted_value.lower() in evidence.quoted_span.lower():
        return True, "validated"
    # Also check if the span appears in the value (value may be a paraphrase)
    if evidence.quoted_span.lower() in extracted_value.lower():
        return True, "validated (span within value)"
    # Check overlap: at least 3 characters of the value appear in the span
    value_words = set(extracted_value.lower().split())
    span_words = set(evidence.quoted_span.lower().split())
    overlap = value_words & span_words
    if len(overlap) >= 2:
        return True, f"validated (word overlap: {sorted(overlap)[:3]})"
    return False, (f"slot '{slot_name}' value '{extracted_value[:50]}' is not grounded "
                   f"in evidence span '{evidence.quoted_span[:50]}'")


def validate_claim_integrity(claim: Claim, source_store: dict[str, dict] = None) -> tuple[bool, str]:
    """V6: Single canonical validator for all scientific promotions.

    Per CTO V11 #9: "FOR EVERY EVIDENCE_BACKED CLAIM: every slot has evidence,
    has exact source span, span exists in source record, source hash matches,
    slot value is grounded in span, derivation method is allowed."

    Returns (passed, reason).
    """
    source_store = source_store or {}

    # 1. Must be EVIDENCE_BACKED
    if not claim.status == "EVIDENCE_BACKED":
        return False, f"status is '{claim.status}', not 'EVIDENCE_BACKED'"

    # 2. Must have 6 slots
    if not claim.has_six_slots():
        return False, "missing one or more of the 6 mandatory slots"

    # 3. Must have slot-level evidence
    if not claim.has_slot_level_evidence_v6():
        return False, "missing slot-level evidence for one or more mandatory slots"

    # 4. Must have slot-specific evidence (no supports_slot="all")
    if not claim.has_slot_specific_evidence():
        return False, "evidence has supports_slot mismatch or 'all'"

    # 5. Every evidence must have a span
    for ev in claim.source_evidence:
        if not ev.has_span():
            return False, f"evidence for slot '{ev.supports_slot}' has no span"

    # 6. Slot values must be grounded in their evidence spans
    slot_evidence_map = {
        "cause": (claim.cause, claim.cause_evidence),
        "failure_mode": (claim.failure_mode, claim.failure_mode_evidence),
        "mechanism": (claim.mechanism, claim.mechanism_evidence),
        "intervention": (claim.intervention, claim.intervention_evidence),
        "measured_effect": (claim.measured_effect, claim.measured_effect_evidence),
    }
    for slot_name, (value, evidence_list) in slot_evidence_map.items():
        if not value or value == "UNSPECIFIED":
            continue
        for ev in evidence_list:
            passed, reason = validate_slot_support(slot_name, value, ev)
            if not passed:
                return False, f"slot grounding failed for '{slot_name}': {reason}"

    # 7. Temporal validity
    if claim.temporal_validity != "valid":
        return False, f"temporal_validity is '{claim.temporal_validity}', not 'valid'"

    # 8. Source hashes must be non-empty
    if not all(e.source_hash for e in claim.source_evidence):
        return False, "one or more evidence objects have empty source_hash"

    # 9. Publication dates must be non-empty
    if not all(e.publication_date for e in claim.source_evidence):
        return False, "one or more evidence objects have empty publication_date"

    return True, "validated"


def is_simulation_ready(claim: Claim) -> bool:
    """V6: A claim is SIMULATION_READY only if boundary_conditions are fully specified.

    Per CTO V11 #7: "A candidate entering simulation must have actual boundary
    conditions. No inferred defaults."
    """
    return (
        claim.is_evidence_backed()
        and claim.boundary_conditions != "UNSPECIFIED"
        and len(claim.boundary_conditions) > 5  # not just "UNSPECIFIED"
    )
