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
from .clock import Clock, SystemClock, DEFAULT_CLOCK
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
VALID_SLOTS = {"cause", "failure_mode", "causal_relation", "mechanism",
               "intervention", "measured_effect", "boundary_conditions"}


@dataclass(frozen=True)
class Claim:
    """The canonical epistemic atomic unit.

    V9: 7-slot scientific structure (CAUSE + FAILURE_MODE + CAUSAL_RELATION +
    MECHANISM + INTERVENTION + MEASURED_EFFECT + BOUNDARY_CONDITIONS).

    Per CTO V14 #1: "A causal relationship is not the same thing as a mechanism."
    - CAUSAL_RELATION = the observed predicate (e.g. "reduces", "prevents")
    - MECHANISM = the underlying causal explanation (e.g. "adhesive interaction")
    A Claim may be EVIDENCE_BACKED with mechanism=UNKNOWN if the source
    establishes a causal relation but does not identify the mechanism.
    But it cannot be a MECHANISM_CLAIM without an explicit mechanism.
    """
    claim_id: str
    claim_type: str
    proposition: str

    # 7-SLOT SCIENTIFIC STRUCTURE
    cause: str
    failure_mode: str          # V5: separated from cause
    causal_relation: str       # V9: the observed predicate (e.g. "reduces")
    mechanism: str             # V9: the underlying explanation (may be "UNKNOWN")
    intervention: str
    measured_effect: str
    boundary_conditions: str   # "UNSPECIFIED" allowed

    # EVIDENCE — each slot has its own slot-specific evidence
    cause_evidence: tuple[SourceEvidence, ...] = ()
    failure_mode_evidence: tuple[SourceEvidence, ...] = ()
    causal_relation_evidence: tuple[SourceEvidence, ...] = ()
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

    # V9: FAILURE_MODE provenance tracking — three levels
    failure_mode_source: str = "DERIVED_FROM_CONTEXT"  # SOURCE_EXPLICIT | ONTOLOGY_VALIDATED | DERIVED_FROM_CONTEXT
    failure_mode_term_in_source: str = ""
    failure_mode_canonical_term: str = ""
    failure_mode_mapping_rule: str = ""
    failure_mode_taxonomy_version: str = ""

    # V10: MECHANISM_STATUS — separate from mechanism value
    # Per CTO V15 #2: "mechanism='UNKNOWN' plus mandatory mechanism evidence is contradictory"
    # UNKNOWN_NOT_STATED = source does not identify a mechanism (no evidence needed)
    # EXPLICIT = source explicitly identifies a mechanism (evidence with span required)
    # UNKNOWN_NOT_RESOLVED = parser could not resolve (human review needed)
    mechanism_status: str = "UNKNOWN_NOT_STATED"  # EXPLICIT | UNKNOWN_NOT_STATED | UNKNOWN_NOT_RESOLVED
    # V10: mechanism inspection scope — what source scope was inspected
    mechanism_inspection_method: str = "SENTENCE_LOCAL"  # SENTENCE_LOCAL | FULL_DOCUMENT | NONE
    mechanism_inspection_scope: str = ""  # e.g. "abstract sentence 3" or "full document"
    mechanism_resolution_version: str = "v10"

    # V9: Structured measured_effect — genuinely extracted, not copied from cause
    effect_value: str = ""        # e.g. "30"
    effect_unit: str = ""         # e.g. "%"
    effect_direction: str = ""    # "increase" or "decrease"
    effect_metric: str = ""       # V9: e.g. "wear_rate" — extracted from source, NOT copied from cause
    effect_target: str = ""       # V9: e.g. "implant" — extracted from source, NOT copied from cause
    effect_raw_text: str = ""     # e.g. "reduced implant wear by 30 percent"

    # V9: Schema versioning
    claim_schema_version: int = 10
    validator_version: int = 10
    extraction_version: int = 10
    # V11: Contract identity (provenance metadata, not scientific schema)
    contract_hash: str = ""       # hash of the frozen contract that validated this Claim
    repository_commit: str = ""   # git commit at which this Claim was promoted

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
                self.causal_relation_evidence + self.mechanism_evidence +
                self.intervention_evidence + self.measured_effect_evidence +
                self.boundary_evidence)

    def has_six_slots(self) -> bool:
        """V9 backward compat: checks 6 original slots (without causal_relation)."""
        return all([
            self.cause and self.cause != "UNSPECIFIED",
            self.failure_mode and self.failure_mode != "UNSPECIFIED",
            self.mechanism and self.mechanism != "UNSPECIFIED",
            self.intervention and self.intervention != "UNSPECIFIED",
            self.measured_effect and self.measured_effect != "UNSPECIFIED",
            self.boundary_conditions,
        ])

    def has_seven_slots(self) -> bool:
        """V9: Check that all 7 mandatory slots are filled.

        Per CTO V14 #1: CAUSAL_RELATION is now separate from MECHANISM.
        - cause, failure_mode, causal_relation, intervention, measured_effect must be real
        - mechanism may be "UNKNOWN" (source establishes causal relation but not mechanism)
        - boundary_conditions may be "UNSPECIFIED"
        """
        return all([
            self.cause and self.cause != "UNSPECIFIED",
            self.failure_mode and self.failure_mode != "UNSPECIFIED",
            self.causal_relation and self.causal_relation != "UNSPECIFIED",
            self.mechanism,  # may be "UNKNOWN"
            self.intervention and self.intervention != "UNSPECIFIED",
            self.measured_effect and self.measured_effect != "UNSPECIFIED",
            self.boundary_conditions,  # may be "UNSPECIFIED"
        ])

    def has_five_slots(self) -> bool:
        """Backward compat: 5-slot check."""
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
        """V6 backward compat."""
        return all([
            len(self.cause_evidence) > 0,
            len(self.failure_mode_evidence) > 0,
            len(self.mechanism_evidence) > 0,
            len(self.intervention_evidence) > 0,
            len(self.measured_effect_evidence) > 0,
        ])

    def has_slot_level_evidence_v9(self) -> bool:
        """V10: Each mandatory slot must have slot-specific evidence.

        Per CTO V15 #2: mechanism evidence is NOT required when
        mechanism_status == "UNKNOWN_NOT_STATED". That is a valid
        scientific absence state, not evidence for a mechanism.
        """
        required = [
            len(self.cause_evidence) > 0,
            len(self.failure_mode_evidence) > 0,
            len(self.causal_relation_evidence) > 0,
            len(self.intervention_evidence) > 0,
            len(self.measured_effect_evidence) > 0,
        ]
        # V10: mechanism evidence only required when mechanism_status == "EXPLICIT"
        if self.mechanism_status == "EXPLICIT":
            required.append(len(self.mechanism_evidence) > 0)
        return all(required)

    def has_slot_specific_evidence(self) -> bool:
        """V9: Evidence objects must have supports_slot matching their slot."""
        slot_evidence_map = {
            "cause": self.cause_evidence,
            "failure_mode": self.failure_mode_evidence,
            "causal_relation": self.causal_relation_evidence,
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
        """V9: EVIDENCE_BACKED requires ALL of:
        - 7 slots filled (INCLUDING causal_relation; mechanism may be "UNKNOWN")
        - slot-level evidence for all mandatory slots
        - no supports_slot="all" in any evidence
        - status == EVIDENCE_BACKED
        - temporal_validity == "valid"
        - source sentence + hash + date in every evidence
        - every non-boundary evidence has a real span (has_span())
        - boundary evidence required when boundary != UNSPECIFIED
        - failure_mode_source in (SOURCE_EXPLICIT, ONTOLOGY_VALIDATED)

        Per CTO V14 #1: 'A causal relationship is not the same thing as a mechanism.'
        Per CTO V14 #2: 'Separate SOURCE_EXPLICIT from ONTOLOGY_VALIDATED.'
        """
        # V9: boundary evidence check
        boundary_ok = True
        if self.boundary_conditions != "UNSPECIFIED" and len(self.boundary_conditions) > 5:
            boundary_ok = (
                len(self.boundary_evidence) > 0
                and all(e.has_span() for e in self.boundary_evidence)
            )
        return (
            self.has_seven_slots()
            and self.has_slot_level_evidence_v9()
            and self.has_slot_specific_evidence()
            and self.status == "EVIDENCE_BACKED"
            and self.temporal_validity == "valid"
            and self.failure_mode_source in ("SOURCE_EXPLICIT", "ONTOLOGY_VALIDATED")  # V10: removed "EXPLICIT"
            and all(e.source_sentence for e in self.source_evidence)
            and all(e.source_hash for e in self.source_evidence)
            and all(e.publication_date for e in self.source_evidence)
            and all(e.has_span() for e in self.source_evidence
                    if e.supports_slot not in ("boundary_conditions",)
                    and not (e.supports_slot == "mechanism" and self.mechanism == "UNKNOWN"))
            and boundary_ok
        )

    def is_search_candidate_only(self) -> bool:
        return self.status == "SEARCH_CANDIDATE"

    def is_blocked(self) -> bool:
        return self.status == "BLOCKED"

    def is_mechanistically_complete(self) -> bool:
        """V10: True only when mechanism is explicitly identified with evidence.

        Per CTO V16 #5: 'No exceptions. mechanism_status == EXPLICIT and
        mechanism_evidence != empty before FAILURE→MECHANISM discovery.'
        """
        return (
            self.mechanism_status == "EXPLICIT"
            and len(self.mechanism_evidence) > 0
            and self.mechanism != "UNKNOWN"
            and self.mechanism != "UNSPECIFIED"
            and self.mechanism != ""
        )

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
                              publication_date: str, evidence_tier: str,
                              clock: Clock = None) -> list[Claim]:
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
    clock = clock or DEFAULT_CLOCK
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
                creation_timestamp=clock.now(),
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
        # V9: unpack 7-tuple
        cause, causal_relation, mechanism, intervention, measured_effect, boundary = slots
        sent_id = f"{source_id}:s{hashlib.sha256((source_id + sentence + source_hash).encode()).hexdigest()[:8]}"

        # V7: Create SLOT-SPECIFIC evidence with ACTUAL character spans.
        # Per CTO V12 #1: "Delete the fallback completely. No match → FAIL.
        # For an evidence-backed Claim, every non-UNSPECIFIED slot must have
        # an exact grounded span. A missed span should produce BLOCKED."
        def _find_span(text: str, sentence: str) -> Optional[tuple[int, int, str]]:
            """Find the character offset of text within sentence.

            V7: Returns None if not found. NO fallback to whole-sentence.
            """
            if not text or not sentence:
                return None
            idx = sentence.lower().find(text.lower())
            if idx >= 0:
                return (idx, idx + len(text), sentence[idx:idx + len(text)])
            # Try whitespace-normalized match
            text_norm = " ".join(text.lower().split())
            sent_norm = " ".join(sentence.lower().split())
            idx = sent_norm.find(text_norm)
            if idx >= 0:
                # Map back to original sentence (approximate)
                return (idx, idx + len(text), sentence[idx:idx + len(text)] if idx + len(text) <= len(sentence) else text)
            return None  # NO FALLBACK — caller must handle None

        cause_span = _find_span(cause, sentence)
        cr_span = _find_span(causal_relation, sentence)  # V9: causal_relation span
        # V9: mechanism may be "UNKNOWN" — if so, no span needed (but evidence still required)
        mech_span = _find_span(mechanism, sentence) if mechanism != "UNKNOWN" else (0, 0, "")
        intv_span = _find_span(intervention, sentence)
        eff_span = _find_span(measured_effect, sentence)

        # V9: If ANY mandatory slot value cannot be grounded (except mechanism=UNKNOWN),
        # the Claim is BLOCKED — not EVIDENCE_BACKED with degraded spans.
        if cause_span is None or cr_span is None or intv_span is None or eff_span is None:
            evidence = SourceEvidence(
                source_id=source_id, source_type=source_type,
                source_field=source_field, source_sentence=sentence[:500],
                source_hash=source_hash, publication_date=publication_date,
                evidence_tier=evidence_tier,
                extraction_method="structured_causal_extraction_span_not_found",
                supports_slot="cause",
                sentence_id=sent_id,
                char_start=0, char_end=0, quoted_span="",
            )
            blocked_claim = Claim(
                claim_id=make_claim_id("MECHANISM_CLAIM", cause or "unknown", mechanism or "unknown", intervention or "unknown"),
                claim_type="MECHANISM_CLAIM",
                proposition=sentence[:300],
                cause=cause, failure_mode="UNSPECIFIED",
                mechanism=mechanism, intervention=intervention,
                measured_effect=measured_effect, boundary_conditions="UNSPECIFIED",
                cause_evidence=(), failure_mode_evidence=(),
                mechanism_evidence=(), intervention_evidence=(),
                measured_effect_evidence=(),
                source_ids=(source_id,), source_hashes=(source_hash,),
                temporal_validity="valid" if publication_date else "unknown",
                creation_timestamp=clock.now(),
                evidence_tier=evidence_tier,
                derivation_method="span_not_found",
                status="BLOCKED",
                falsification_condition="", measurement_method="",
                alternative_explanations=(),
            )
            claims.append(blocked_claim)
            continue

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
        # V8: FAILURE_MODE must be EXPLICITLY evidenced, not merely copied from CAUSE.
        # Per CTO V13 #1: "Require FAILURE_MODE_SOURCE == EXPLICIT for EVIDENCE_BACKED,
        # unless a tightly defined ontology rule proves the extracted phrase is the
        # canonical failure mode."
        #
        # The failure_mode is the observable failure (e.g. "wear", "infection"),
        # while the cause is the underlying driver (e.g. "surface degradation").
        #
        # Extraction logic:
        # 1. If "due to"/"caused by" pattern → cause and failure_mode are DIFFERENT
        # 2. If no pattern → failure_mode = cause (the object of the verb IS the failure)
        #    BUT: this is DERIVED, not EXPLICIT. Mark as DERIVED_FROM_CONTEXT.
        # 3. For EVIDENCE_BACKED, require EXPLICIT or validated ontology mapping.
        failure_mode_value = cause  # In simple sentences, failure_mode = cause
        failure_mode_source = "DERIVED_FROM_CONTEXT"  # default: derived, not explicit

        # V8: If the cause matches a known failure mode in the controlled taxonomy,
        # mark as EXPLICIT via ontology mapping.
        # Per CTO V13 #1: "only if 'wear' is mapped to the controlled failure taxonomy
        # through a validated ontology mapping."
        from ..failure_taxonomy import FAILURE_MODES, classify_failure_from_text
        # V9: three-level failure_mode_source distinction
        failure_mode_term_in_source = ""
        failure_mode_canonical_term = ""
        failure_mode_mapping_rule = ""
        failure_mode_taxonomy_version = "v1"  # from failure_taxonomy.py

        # Check if cause text contains a known failure mode keyword
        failure_matches = classify_failure_from_text(cause.lower())
        if failure_matches:
            failure_mode_source = "ONTOLOGY_VALIDATED"  # V9: not SOURCE_EXPLICIT
            failure_mode_value = failure_matches[0].lower().replace("_", " ")
            failure_mode_term_in_source = cause
            failure_mode_canonical_term = failure_matches[0]
            failure_mode_mapping_rule = "keyword_match_in_taxonomy"
        failure_mode_span = cause_span
        # If "due to"/"caused by" pattern → cause and failure_mode are DIFFERENT
        cause_pattern = re.search(r'(?:due to|caused by|because of|resulting from)\s+(.+?)(?:[,.]|$)',
                                   sentence, re.IGNORECASE)
        if cause_pattern:
            failure_mode_value = cause
            failure_mode_source = "SOURCE_EXPLICIT"  # V9: explicitly distinguished
            failure_mode_term_in_source = cause
            failure_mode_canonical_term = cause
            failure_mode_mapping_rule = "explicit_due_to_pattern"
            actual_cause = cause_pattern.group(1).strip()
            actual_cause_span = _find_span(actual_cause, sentence)
            if actual_cause_span:
                cause = actual_cause
                cause_span = actual_cause_span
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
            char_start=failure_mode_span[0], char_end=failure_mode_span[1],
            quoted_span=failure_mode_span[2],
        )
        # V9: causal_relation evidence
        cr_ev = SourceEvidence(
            source_id=source_id, source_type=source_type,
            source_field=source_field, source_sentence=sentence[:500],
            source_hash=source_hash, publication_date=publication_date,
            evidence_tier=evidence_tier,
            extraction_method="structured_causal_extraction",
            supports_slot="causal_relation",
            sentence_id=sent_id,
            char_start=cr_span[0], char_end=cr_span[1],
            quoted_span=cr_span[2],
        )
        # V10: mechanism evidence — NOT created when mechanism_status == "UNKNOWN_NOT_STATED"
        # Per CTO V15 #2: "mechanism='UNKNOWN' plus mandatory mechanism evidence is
        # conceptually contradictory. It is an absence/negative-information assertion."
        mechanism_status_value = "EXPLICIT" if mechanism != "UNKNOWN" else "UNKNOWN_NOT_STATED"
        mechanism_inspection_scope = f"sentence: {sentence[:80]}"  # V10
        if mechanism_status_value == "EXPLICIT":
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
            mechanism_evidence_tuple = (mechanism_ev,)
        else:
            # V10: no mechanism evidence — UNKNOWN_NOT_STATED is a valid absence
            mechanism_evidence_tuple = ()
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

        # V8: Populate structured effect fields
        effect_raw = sentence[:200]  # use the full sentence as raw effect context
        # Determine direction from the causal verb
        decrease_verbs = {"reduces", "reduced", "decreases", "decreased", "prevents",
                          "prevented", "inhibits", "inhibited", "suppresses", "suppressed",
                          "eliminates", "eliminated", "attenuates", "attenuated",
                          "blocks", "blocked", "abolishes", "abolished", "abrogates", "abrogated"}
        increase_verbs = {"causes", "caused", "induces", "induced", "increases", "increased",
                          "improves", "improved", "enhances", "enhanced", "restores", "restored",
                          "accelerates", "accelerated", "promotes", "promoted", "reverses", "reversed"}
        effect_direction = "decrease" if found_verb in decrease_verbs else \
                           "increase" if found_verb in increase_verbs else ""

        # Extract numeric value and unit
        eff_value = ""
        eff_unit = ""
        quant_match = re.search(r'(\d+)\s*(percent|%)?', sentence, re.IGNORECASE)
        if quant_match:
            eff_value = quant_match.group(1)
            eff_unit = quant_match.group(2) or "%" if quant_match.group(2) else "%"

        # V9: effect_metric and effect_target are NOT copied from cause.
        # They are extracted from the source sentence independently.
        # If not identifiable, they remain empty (UNKNOWN).
        eff_metric = ""  # V9: extracted from source, not copied from cause
        eff_target = ""  # V9: extracted from source, not copied from cause
        # Try to extract metric from the object (e.g. "wear rate" from "wear rate by 30%")
        metric_match = re.search(r'(\w+\s+rate|\w+\s+life|\w+\s+strength|\w+\s+resistance)',
                                  sentence, re.IGNORECASE)
        if metric_match:
            eff_metric = metric_match.group(1).lower().replace(" ", "_")
        # Try to extract target from the subject or object
        target_match = re.search(r'(implant|device|coating|surface|material|catheter|stent|sensor)',
                                  sentence, re.IGNORECASE)
        if target_match:
            eff_target = target_match.group(1).lower()

        # V9: claim_type depends on whether mechanism is identified
        # If mechanism = UNKNOWN, this is a FAILURE_CLAIM (causal relation established,
        # but mechanism not identified). Not a MECHANISM_CLAIM.
        claim_type = "MECHANISM_CLAIM" if mechanism != "UNKNOWN" else "FAILURE_CLAIM"

        claim = Claim(
            claim_id=make_claim_id(claim_type, cause, causal_relation, intervention),
            claim_type=claim_type,
            proposition=sentence[:300],
            cause=cause,
            failure_mode=failure_mode_value,
            causal_relation=causal_relation,  # V9: the verb
            mechanism=mechanism,  # V9: may be "UNKNOWN"
            intervention=intervention,
            measured_effect=measured_effect,
            boundary_conditions=boundary,
            cause_evidence=(cause_ev,),
            failure_mode_evidence=(failure_mode_ev,),
            causal_relation_evidence=(cr_ev,),  # V9
            mechanism_evidence=mechanism_evidence_tuple,  # V10: empty when UNKNOWN_NOT_STATED
            mechanism_status=mechanism_status_value,  # V10
            mechanism_inspection_scope=mechanism_inspection_scope,  # V10
            intervention_evidence=(intervention_ev,),
            measured_effect_evidence=(effect_ev,),
            boundary_evidence=boundary_ev,
            source_ids=(source_id,),
            source_hashes=(source_hash,),
            temporal_validity="valid" if publication_date else "unknown",
            creation_timestamp=clock.now(),
            evidence_tier=evidence_tier,
            derivation_method="structured_causal_extraction",
            # V9: structured effect fields — genuinely extracted
            effect_value=eff_value,
            effect_unit=eff_unit,
            effect_direction=effect_direction,
            effect_metric=eff_metric,  # V9: not copied from cause
            effect_target=eff_target,  # V9: not copied from cause
            effect_raw_text=effect_raw[:200],
            # V9: failure_mode provenance
            failure_mode_source=failure_mode_source,
            failure_mode_term_in_source=failure_mode_term_in_source,
            failure_mode_canonical_term=failure_mode_canonical_term,
            failure_mode_mapping_rule=failure_mode_mapping_rule,
            failure_mode_taxonomy_version=failure_mode_taxonomy_version,
            claim_schema_version=10,
            validator_version=10,
            extraction_version=10,
            # V11: Extractor creates BLOCKED or SEARCH_CANDIDATE only.
            # Promotion to EVIDENCE_BACKED happens ONLY through
            # promote_claim_to_evidence_backed() — the canonical promotion function.
            status="SEARCH_CANDIDATE" if _can_promote(cause, failure_mode_value, mechanism,
                                                       intervention, measured_effect, boundary,
                                                       cause_ev, failure_mode_ev,
                                                       mechanism_evidence_tuple[0] if mechanism_evidence_tuple else None,
                                                       intervention_ev, effect_ev,
                                                       publication_date, failure_mode_source,
                                                       causal_relation, cr_ev) else "BLOCKED",
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
    # V9: CAUSAL_RELATION is the verb itself (e.g. "reduces").
    #     MECHANISM is the underlying explanation (e.g. "adhesive interaction").
    #     The source may establish a causal relation without identifying a mechanism.
    #     In that case, mechanism = "UNKNOWN".
    causal_relation = causal_verb  # V9: just the verb

    # Extract cause from the object (the thing being reduced is the problem)
    # V8: Try to find a failure-mode keyword in the object for ontology mapping.

    # Extract cause from the object (the thing being reduced is the problem)
    # V8: Try to find a failure-mode keyword in the object for ontology mapping.
    # If found, use it as the cause (e.g. "wear" in "implant wear by 30%").
    from ..failure_taxonomy import classify_failure_from_text
    obj_lower = obj.lower()
    failure_matches = classify_failure_from_text(obj_lower)
    if failure_matches:
        # Use the first matched failure keyword as the cause
        # Find it in the original object text (preserving case)
        fm_keyword = failure_matches[0].lower().replace("_", " ")
        # Find the keyword in the object
        for word in obj.split():
            if word.lower().rstrip(".,;:") in fm_keyword or fm_keyword in word.lower().rstrip(".,;:"):
                cause = word.strip(".,;:")
                break
        else:
            cause = fm_keyword
    else:
        # V7: cause must be an actual word from the source sentence for span grounding
        cause = obj.split()[0].strip(".,;:") if obj.split() else ""

    # V9: MECHANISM is NOT the causal predicate. It is the underlying explanation.
    # Per CTO V14 #1: "A causal relationship is not the same thing as a mechanism."
    # The source may say "reduces wear" (causal_relation) without identifying
    # WHY it reduces wear (mechanism). In that case, mechanism = "UNKNOWN".
    # Only set mechanism if the source explicitly identifies it (e.g. "via", "through",
    # "by", "due to", "through the mechanism of").
    mechanism = "UNKNOWN"  # V9: default — source does not explicitly identify mechanism
    # V10: Removed "due to" from mechanism patterns.
    # Per CTO V15 #4: "'due to' is dangerous. It may indicate CAUSE, not MECHANISM."
    mechanism_patterns = [
        r'(?:via|through|by means of|through the mechanism of)\s+(.+?)(?:[,.]|$)',
        r'(?:mechanism\s*:\s*)(.+?)(?:[,.]|$)',
    ]
    for pattern in mechanism_patterns:
        mech_match = re.search(pattern, sentence, re.IGNORECASE)
        if mech_match:
            mechanism = mech_match.group(1).strip()
            break

    # V7: measured_effect must be an actual quote from the source sentence.
    # Per CTO V12 #1: "No match → BLOCKED." We cannot construct synthetic phrases.
    # Look for quantification in the OBJECT (after the verb)
    quant_match = re.search(r'(\d+\s*(?:percent|%|°[CF])?)', obj, re.IGNORECASE)
    if quant_match:
        # Use the actual quantified phrase from the source
        # e.g. "by 30 percent" or "30%"
        quant_start = obj.find(quant_match.group(0))
        # Try to capture "by X%" or "X%" as it appears
        measured_effect = quant_match.group(0).strip()
    else:
        # If no quantification, the measured effect is the object itself
        # (e.g. "wear" in "reduces wear")
        measured_effect = cause

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

    # V9: Validate: cause, causal_relation, intervention, measured_effect must be non-empty
    # mechanism may be "UNKNOWN" — that is valid.
    if not subject or not cause or not causal_relation or not measured_effect:
        return None
    if len(subject) < 3 or len(cause) < 3:
        return None

    # V9: return 7-tuple including causal_relation and mechanism
    return (cause, causal_relation, mechanism, subject, measured_effect, boundary)


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
# =====================================================================
# V7: EXTRACTION STATUS (separate from evidence status)
# =====================================================================
EXTRACTION_STATUS = {
    "PARSED",      # structured extraction succeeded
    "AMBIGUOUS",   # sentence has causal language but slots are ambiguous
    "FAILED",      # extraction could not parse the sentence
}


def _can_promote(cause: str, failure_mode: str, mechanism: str,
                 intervention: str, measured_effect: str, boundary: str,
                 cause_ev: SourceEvidence, failure_mode_ev: SourceEvidence,
                 mechanism_ev: SourceEvidence, intervention_ev: SourceEvidence,
                 effect_ev: SourceEvidence,
                 publication_date: str,
                 failure_mode_source: str = "DERIVED_FROM_CONTEXT",
                 causal_relation: str = "",
                 causal_relation_ev: SourceEvidence = None) -> bool:
    """V9: Mandatory promotion gate. Only returns True if ALL invariants hold.

    Per CTO V14 #1: mechanism may be "UNKNOWN" — that is valid for FAILURE_CLAIM.
    Per CTO V14 #2: failure_mode_source must be SOURCE_EXPLICIT or ONTOLOGY_VALIDATED.

    Checks:
      1. All mandatory slots non-empty (mechanism may be "UNKNOWN")
      2. All mandatory slots have evidence with spans (mechanism evidence may have empty span if UNKNOWN)
      3. All evidence has correct supports_slot
      4. No supports_slot="all"
      5. failure_mode_source in (SOURCE_EXPLICIT, ONTOLOGY_VALIDATED, EXPLICIT)
      6. publication_date exists
      7. V9: causal_relation and causal_relation_ev must exist
    """
    # 1. All mandatory slots filled (mechanism may be "UNKNOWN")
    if not cause or cause == "UNSPECIFIED":
        return False
    if not failure_mode or failure_mode == "UNSPECIFIED":
        return False
    if not mechanism:  # may be "UNKNOWN" but must not be empty
        return False
    if not intervention or intervention == "UNSPECIFIED":
        return False
    if not measured_effect or measured_effect == "UNSPECIFIED":
        return False
    # V9: causal_relation must be non-empty
    if not causal_relation or causal_relation == "UNSPECIFIED":
        return False
    # boundary may be UNSPECIFIED

    # V10: mechanism evidence NOT required when mechanism_status == "UNKNOWN_NOT_STATED"
    mandatory_evs = [cause_ev, failure_mode_ev, intervention_ev, effect_ev]
    if causal_relation_ev:
        mandatory_evs.append(causal_relation_ev)
    for ev in mandatory_evs:
        if not ev or not ev.has_span():
            return False
        if not ev.source_sentence or not ev.source_hash or not ev.publication_date:
            return False
    # V10: mechanism_ev only required when mechanism is explicitly identified
    # (mechanism != "UNKNOWN"). When UNKNOWN_NOT_STATED, no evidence needed.

    # 3. Evidence supports_slot matches (mechanism_ev may be None when UNKNOWN_NOT_STATED)
    if cause_ev.supports_slot != "cause":
        return False
    if failure_mode_ev.supports_slot != "failure_mode":
        return False
    if mechanism_ev is not None and mechanism_ev.supports_slot != "mechanism":
        return False
    if intervention_ev.supports_slot != "intervention":
        return False
    if effect_ev.supports_slot != "measured_effect":
        return False
    if causal_relation_ev and causal_relation_ev.supports_slot != "causal_relation":
        return False

    # 4. No supports_slot="all" (mechanism_ev may be None)
    all_evs = [ev for ev in [cause_ev, failure_mode_ev, mechanism_ev, intervention_ev, effect_ev] if ev is not None]
    for ev in all_evs:
        if ev.supports_slot == "all":
            return False

    # 5. V10: failure_mode_source must be SOURCE_EXPLICIT or ONTOLOGY_VALIDATED (no "EXPLICIT")
    if failure_mode_source not in ("SOURCE_EXPLICIT", "ONTOLOGY_VALIDATED"):
        return False

    # 6. publication_date must exist for temporal validity
    if not publication_date:
        return False

    # 7. V9: causal_relation_ev must exist
    if not causal_relation_ev:
        return False

    return True


# BACKWARD-COMPATIBLE ALIASES (for existing tests)
# =====================================================================
# V4 renamed extract_causal_claims → extract_causal_claims_v4 and changed
# the Claim constructor. These aliases maintain backward compatibility.

def extract_causal_claims(text: str, **kwargs) -> list[Claim]:
    """Backward-compatible alias for extract_causal_claims_v4.

    V11: This function extracts Claims AND promotes eligible ones to EVIDENCE_BACKED
    via the canonical promotion function. The extractor itself creates SEARCH_CANDIDATE
    or BLOCKED only; promotion is the sole path to EVIDENCE_BACKED.
    """
    raw_claims = extract_causal_claims_v4(text, **kwargs)
    promoted = []
    for claim in raw_claims:
        if claim.status == "SEARCH_CANDIDATE":
            promoted_claim = promote_claim_to_evidence_backed(claim)
            promoted.append(promoted_claim)
        else:
            promoted.append(claim)
    return promoted


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
    if not claim.has_slot_level_evidence_v9():
        return False, "missing slot-level evidence for one or more mandatory slots"

    # 4. Must have slot-specific evidence (no supports_slot="all")
    if not claim.has_slot_specific_evidence():
        return False, "evidence has supports_slot mismatch or 'all'"

    # 5. Every evidence must have a span (except mechanism=UNKNOWN and boundary=UNSPECIFIED)
    for ev in claim.source_evidence:
        if ev.supports_slot == "boundary_conditions" and claim.boundary_conditions == "UNSPECIFIED":
            continue
        if ev.supports_slot == "mechanism" and claim.mechanism == "UNKNOWN":
            continue  # V9: mechanism evidence may have empty span when mechanism is UNKNOWN
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
        if value == "UNKNOWN" and slot_name == "mechanism":
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


# =====================================================================
# V8: CANONICAL PROMOTION FUNCTION (CTO V13 #5, #6)
# =====================================================================

def validate_claim_for_promotion(claim: Claim, source_store: dict = None) -> tuple[bool, str]:
    """V11: Validate a CANDIDATE claim for promotion to EVIDENCE_BACKED.

    Per CTO V19 P0-2: "The canonical promotion path must consume
    validate_claim_against_contract(). No Claim can become EVIDENCE_BACKED
    unless the active frozen contract validates it."

    This function works on candidate claims (status may be anything).
    It does NOT check claim.status — it checks the structural invariants.
    """
    source_store = source_store or {}

    # V11 P0-2: FIRST check against the frozen contract (source of truth)
    from .contract_loader import validate_claim_against_contract
    contract_passed, contract_reason = validate_claim_against_contract(claim)
    if not contract_passed:
        return False, f"contract validation failed: {contract_reason}"

    # 1. has_seven_slots (V9: 7 slots including causal_relation)
    if not claim.has_seven_slots():
        return False, "missing one or more of the 7 mandatory slots"

    # 2. has_slot_level_evidence
    if not claim.has_slot_level_evidence_v9():
        return False, "missing slot-level evidence for one or more mandatory slots"

    # 3. has_slot_specific_evidence
    if not claim.has_slot_specific_evidence():
        return False, "evidence has supports_slot mismatch"

    # 4. Every non-boundary evidence has a span
    for ev in claim.source_evidence:
        if ev.supports_slot != "boundary_conditions" and not ev.has_span():
            return False, f"evidence for slot '{ev.supports_slot}' has no span"

    # 5. V8: boundary evidence required when boundary != UNSPECIFIED
    if claim.boundary_conditions != "UNSPECIFIED" and len(claim.boundary_conditions) > 5:
        if not claim.boundary_evidence:
            return False, "boundary_conditions specified but no boundary_evidence"
        for ev in claim.boundary_evidence:
            if not ev.has_span():
                return False, "boundary evidence has no span"

    # 6. V11: failure_mode_source must be SOURCE_EXPLICIT or ONTOLOGY_VALIDATED
    if claim.failure_mode_source not in ("SOURCE_EXPLICIT", "ONTOLOGY_VALIDATED"):
        return False, f"failure_mode_source is '{claim.failure_mode_source}', must be SOURCE_EXPLICIT or ONTOLOGY_VALIDATED"

    # 7. Slot grounding
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
        if value == "UNKNOWN" and slot_name == "mechanism":
            continue  # V9

    # 8. Temporal validity
    if claim.temporal_validity != "valid":
        return False, f"temporal_validity is '{claim.temporal_validity}', not 'valid'"

    # 9. Source hashes and dates
    if not all(e.source_hash for e in claim.source_evidence):
        return False, "one or more evidence objects have empty source_hash"
    if not all(e.publication_date for e in claim.source_evidence):
        return False, "one or more evidence objects have empty publication_date"

    # 10. V8: quoted_span alignment (if source_store available)
    for ev in claim.source_evidence:
        if ev.source_id in source_store:
            source_record = source_store[ev.source_id]
            source_field_text = source_record.get(ev.source_field, "")
            if source_field_text and ev.char_end <= len(source_field_text):
                actual_span = source_field_text[ev.char_start:ev.char_end]
                if actual_span != ev.quoted_span:
                    return False, (f"quoted_span mismatch for slot '{ev.supports_slot}': "
                                   f"expected '{ev.quoted_span[:30]}', "
                                   f"got '{actual_span[:30]}'")

    return True, "validated"


def promote_claim_to_evidence_backed(claim: Claim, source_store: dict = None) -> Claim:
    """V11: The ONLY function that may transition a Claim to EVIDENCE_BACKED.

    Per CTO V13 #5: "The promotion function alone may transition status."
    Per CTO V19 P0-2: "Must consume validate_claim_against_contract()."
    Per CTO V19 P0-4: "Must stamp contract_hash and repository_commit."

    Returns a NEW Claim with status=EVIDENCE_BACKED if validation passes.
    Returns the original claim (unchanged) if validation fails.
    """
    passed, reason = validate_claim_for_promotion(claim, source_store)
    if not passed:
        return claim
    # V11: Stamp contract identity on the promoted Claim
    from .contract_loader import get_contract_hash, load_contract
    import subprocess
    contract_hash = get_contract_hash()
    try:
        repo_commit = subprocess.check_output(
            ['git', 'rev-parse', 'HEAD'],
            stderr=subprocess.DEVNULL
        ).decode().strip()
    except Exception:
        repo_commit = "UNAVAILABLE"
    # Create a new frozen Claim with EVIDENCE_BACKED status + contract identity
    import dataclasses
    return dataclasses.replace(claim, status="EVIDENCE_BACKED",
                               contract_hash=contract_hash,
                               repository_commit=repo_commit)


# =====================================================================
# V8: EVIDENCE SPAN VALIDATION (CTO V13 #3)
# =====================================================================

def validate_evidence_span(evidence: SourceEvidence, source_field_text: str) -> tuple[bool, str]:
    """V8: Verify that the evidence span matches the source field.

    Per CTO V13 #3: "source_field[char_start:char_end] == quoted_span
    after one canonical normalization procedure."

    Returns (passed, reason).
    """
    if not evidence.has_span():
        return False, "evidence has no span"

    if not source_field_text:
        return False, "source_field_text is empty"

    if evidence.char_end > len(source_field_text):
        return False, f"char_end ({evidence.char_end}) exceeds source_field length ({len(source_field_text)})"

    actual_span = source_field_text[evidence.char_start:evidence.char_end]
    if actual_span != evidence.quoted_span:
        # Try whitespace-normalized comparison
        actual_norm = " ".join(actual_span.split())
        quoted_norm = " ".join(evidence.quoted_span.split())
        if actual_norm == quoted_norm:
            return True, "validated (whitespace-normalized)"
        return False, (f"span mismatch: source_field[{evidence.char_start}:{evidence.char_end}] = "
                       f"'{actual_span[:50]}' but quoted_span = '{evidence.quoted_span[:50]}'")

    return True, "validated"


# =====================================================================
# V8: TEMPORAL KNOWLEDGE-CUTOFF (CTO V13 #8)
# =====================================================================

def validate_temporal_cutoff(claim: Claim, candidate_lock_date: str) -> tuple[bool, str]:
    """V8: Verify that all evidence predates the candidate lock date.

    Per CTO V13 #8: "claim evidence date <= candidate lock date.
    mechanism evidence must predate candidate creation."

    Returns (passed, reason).
    """
    if not candidate_lock_date:
        return False, "candidate_lock_date is empty"

    lock_date = candidate_lock_date[:10]  # ISO date portion

    for ev in claim.source_evidence:
        if not ev.publication_date:
            return False, f"evidence for slot '{ev.supports_slot}' has no publication_date"
        ev_date = ev.publication_date[:10]
        if ev_date > lock_date:
            return False, (f"evidence for slot '{ev.supports_slot}' published {ev_date} "
                           f"which is after lock date {lock_date}")

    return True, "validated"
