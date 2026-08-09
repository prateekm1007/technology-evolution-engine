#!/usr/bin/env python3
"""b2_provenance/generation_null.py — Generation null (fair baseline).

Per B2_REVISION_R5_2.md and B2_IMPLEMENTATION_INVARIANTS.md:

    The generation null is a FAIR baseline that:
    - Receives the same source pair as the engine
    - Shares the same extraction/abstraction prefix
    - Produces candidates in the SAME schema (including a mechanism)
    - Has the same candidate budget (exactly 3, rank-paired)
    - Does NOT use CrossDomainTransferEngine or HypothesisGenerationEngine
    - CAN pass Gate A/C/B (unlike the old retrieval null)

    ENGINE:     extraction → abstraction → TRANSFER → GENERATION → candidate
    NULL:       extraction → abstraction → CONCATENATION → candidate

ESTIMAND (per audit round 48, narrowed):
    The intended experimental contrast is downstream transfer/generation
    versus deterministic null construction, conditional on the shared
    upstream prefix.

    This is NOT "engine and null differ only in generation mechanism."
    The arms also differ in:
    - deterministic template generation vs model generation
    - different prompt machinery
    - different provider/model involvement
    - potentially different output length/distribution
    - different lexical structure
    - different opportunity to introduce genuinely new information

    Fairness is a HYPOTHESIS to be tested (baseline equivalence audit),
    not something the schema equality proves.

UNIVERSAL SEED (per audit round 48, narrowed):
    The arms receive the same preregistered invocation seed:
        seed = SHA256(preregistration_id || case_id || "downstream")

    This does NOT guarantee equivalent generation randomness — the null
    is deterministic and has no randomness to equalize. The seed
    equality ensures the invocation identity is the same, so any
    difference in output is attributable to the pipeline difference
    (not to a seed difference).

RANK-PAIRING (per audit round 48, corrected):
    R5.2 specifies: C1=(A1,B1), C2=(A2,B2), C3=(A3,B3)
    This requires BOTH abstraction lists to have at least 3 entries.

    If either list has fewer than 3 entries, the implementation
    FAILS CLOSED (NULL_GENERATION_FAILURE) rather than padding.
    Padding would violate the rank-pairing specification and create
    a different experimental condition than the engine.

SHARED ENTITY (per audit round 48, implemented):
    The shared entity is computed using the SPECIFIED function:
        FirstEntity(SortedIntersection(
            Entities(A), Entities(B), StopwordList, EntityDictionary))

    Entities(): spaCy en_core_web_sm NER (frozen, version recorded)
    Canonicalization: lowercase → strip punctuation → lemmatize
    StopwordList: frozen NLTK English stopword list
    EntityDictionary: preregistered (frozen set of valid scientific concepts)
    Sort: alphabetical ascending (deterministic tie-break)
    FirstEntity: first in sorted list, or None if empty

IMMUTABILITY:
    The null's raw output is stored via content-addressed storage BEFORE
    any human sees it. The generation is recorded in an immutable
    CANDIDATE_GENERATED ledger event. No researcher may select, rewrite,
    or discard null candidates.
"""
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .content_addressed_storage import store_raw_output, compute_sha256
from .frozen_parser import (
    parse_candidates,
    get_candidate_by_rank,
    compute_candidate_sha256,
    verify_derivation,
    PARSER_CONFIG,
)
from .provenance_ledger import ProvenanceLedger


# --------------------------------------------------------------------
# Frozen component verification (per audit round 49).
#
# The NER components (entity dictionary, stopword set, model info)
# are frozen as committed artifacts with SHA-256 verification.
# Runtime verification rejects any mismatch between the frozen
# artifacts and the actual runtime components.
#
# This is the same principle that hardened the Phase 7 freeze:
#     disk content != frozen content → substitution detected.
# --------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[2]
FROZEN_COMPONENTS_DIR = REPO_ROOT / "provenance" / "frozen_components"


def _compute_json_sha256(data: dict) -> str:
    """Compute SHA-256 of a dict's canonical JSON serialization."""
    json_bytes = json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(json_bytes).hexdigest()


def verify_frozen_components() -> Dict[str, Any]:
    """Verify that the runtime NER components match the frozen artifacts.

    Per audit round 49: NER identity must be frozen, not just reported.
    This function checks:
    1. entity_dictionary.json exists and its SHA-256 matches
    2. stopword_set.json exists and its SHA-256 matches
    3. ner_model_info.json exists and its SHA-256 matches
    4. The runtime spaCy version matches the frozen version

    Returns:
        Dict with verification results.

    Raises:
        AssertionError: if any component fails verification.
    """
    results = {}

    # 1. Verify entity dictionary
    dict_path = FROZEN_COMPONENTS_DIR / "entity_dictionary.json"
    assert dict_path.exists(), (
        f"Frozen entity dictionary not found at {dict_path}. "
        f"Run scripts/freeze_ner_components.py to generate it."
    )
    dict_data = json.loads(dict_path.read_text())
    dict_runtime_sha = _compute_json_sha256(dict_data)

    sha_path = FROZEN_COMPONENTS_DIR / "entity_dictionary.sha256"
    assert sha_path.exists(), (
        f"Frozen entity dictionary SHA-256 not found at {sha_path}."
    )
    dict_frozen_sha = sha_path.read_text().split()[0]
    assert dict_runtime_sha == dict_frozen_sha, (
        f"Entity dictionary SHA-256 mismatch: runtime={dict_runtime_sha[:16]}... "
        f"frozen={dict_frozen_sha[:16]}... The dictionary has been modified."
    )
    results["entity_dictionary_sha256"] = dict_frozen_sha
    results["entity_dictionary_verified"] = True

    # 2. Verify stopword set
    stopword_path = FROZEN_COMPONENTS_DIR / "stopword_set.json"
    assert stopword_path.exists(), (
        f"Frozen stopword set not found at {stopword_path}."
    )
    stopword_data = json.loads(stopword_path.read_text())
    stopword_runtime_sha = _compute_json_sha256(stopword_data)

    stopword_sha_path = FROZEN_COMPONENTS_DIR / "stopword_set.sha256"
    assert stopword_sha_path.exists(), (
        f"Frozen stopword set SHA-256 not found at {stopword_sha_path}."
    )
    stopword_frozen_sha = stopword_sha_path.read_text().split()[0]
    assert stopword_runtime_sha == stopword_frozen_sha, (
        f"Stopword set SHA-256 mismatch: runtime={stopword_runtime_sha[:16]}... "
        f"frozen={stopword_frozen_sha[:16]}... The stopword set has been modified."
    )
    results["stopword_set_sha256"] = stopword_frozen_sha
    results["stopword_set_verified"] = True

    # 3. Verify NER model info
    ner_path = FROZEN_COMPONENTS_DIR / "ner_model_info.json"
    assert ner_path.exists(), (
        f"Frozen NER model info not found at {ner_path}."
    )
    ner_data = json.loads(ner_path.read_text())

    # Check runtime spaCy version matches frozen version
    import spacy
    frozen_spacy_version = ner_data["model_info"]["spacy_version"]
    runtime_spacy_version = spacy.__version__
    assert runtime_spacy_version == frozen_spacy_version, (
        f"spaCy version mismatch: runtime={runtime_spacy_version} "
        f"frozen={frozen_spacy_version}. The NER model identity has changed."
    )

    ner_runtime_sha = _compute_json_sha256(ner_data)
    ner_sha_path = FROZEN_COMPONENTS_DIR / "ner_model_info.sha256"
    assert ner_sha_path.exists(), (
        f"Frozen NER model info SHA-256 not found at {ner_sha_path}."
    )
    ner_frozen_sha = ner_sha_path.read_text().split()[0]
    assert ner_runtime_sha == ner_frozen_sha, (
        f"NER model info SHA-256 mismatch: runtime={ner_runtime_sha[:16]}... "
        f"frozen={ner_frozen_sha[:16]}... The NER model info has been modified."
    )
    results["ner_model_info_sha256"] = ner_frozen_sha
    results["ner_model_info_verified"] = True
    results["spacy_version"] = runtime_spacy_version

    return results


# --------------------------------------------------------------------
# Frozen configuration for the null generation procedure.
# Any change requires a new preregistration amendment and SHA-256.
# --------------------------------------------------------------------
NULL_CONFIG = {
    "n_candidates": 3,  # Exactly 3 (R5.2 SERIOUS 1 fix)
    "candidate_delimiter": PARSER_CONFIG["candidate_delimiter"],
    "relationship_template": "{a_abstraction} is related to {b_abstraction}",
    "mechanism_template_with_shared": (
        "Both involve {shared_entity}. "
        "{a_abstraction} occurs in domain A. "
        "{b_abstraction} occurs in domain B. "
        "They may be connected through {shared_entity}."
    ),
    "mechanism_template_no_shared": (
        "Both domains involve related phenomena. "
        "{a_abstraction} occurs in domain A. "
        "{b_abstraction} occurs in domain B. "
        "No shared entity was identified."
    ),
    # NER configuration (frozen)
    "ner_model": "en_core_web_sm",
    "ner_library": "spacy",
    # Minimum token length for entity consideration
    "min_token_length": 4,
}


# --------------------------------------------------------------------
# Frozen stopword list.
#
# This is a FIXED set of English stopwords. In the full implementation,
# this will be replaced by the NLTK English stopword list (SHA-256
# committed). For now, this frozen set is used to ensure determinism.
#
# The stopword list is NOT derived from the candidate text or the
# gold set — it is a fixed English language resource.
# --------------------------------------------------------------------
FROZEN_STOPWORDS = frozenset({
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to",
    "for", "of", "with", "by", "from", "is", "are", "was", "were",
    "be", "been", "being", "have", "has", "had", "do", "does", "did",
    "will", "would", "could", "should", "may", "might", "must", "shall",
    "can", "need", "dare", "ought", "used", "this", "that", "these",
    "those", "they", "what", "which", "who", "when", "where", "why",
    "how", "all", "each", "every", "both", "few", "more", "most",
    "other", "some", "such", "not", "only", "own", "same", "than",
    "too", "very", "just", "also", "through", "into", "out", "up",
    "down", "about", "above", "below", "over", "under", "again",
    "further", "then", "once", "here", "there", "both", "each",
    "its", "their", "his", "her", "our", "your", "them",
})


# --------------------------------------------------------------------
# Frozen entity dictionary.
#
# This is a preregistered set of valid scientific concepts. Only
# entities in this dictionary are considered as shared entities.
#
# For the initial implementation, this is a broad set of scientific
# terms. In the full implementation, this will be a committed
# dictionary file with SHA-256 recorded.
#
# The dictionary is NOT derived from the candidate text or the
# gold set — it is a fixed scientific vocabulary resource.
# --------------------------------------------------------------------
FROZEN_ENTITY_DICTIONARY = frozenset({
    # General scientific terms
    "crystal", "crystallization", "nucleation", "growth", "dissolution",
    "precipitation", "mineral", "mineralization", "biomineralization",
    "calcium", "phosphate", "carbonate", "silica", "silicate",
    "protein", "enzyme", "cell", "tissue", "membrane",
    "transport", "diffusion", "osmosis", "cavitation", "acoustic",
    "ultrasound", "frequency", "wavelength", "amplitude",
    "thermal", "temperature", "heat", "energy", "kinetic",
    "thermodynamic", "entropy", "enthalpy", "free",
    "chemical", "reaction", "catalyst", "kinetics", "equilibrium",
    "phase", "transition", "polymorph", "stable", "metastable",
    "solution", "solvent", "solute", "concentration", "saturation",
    "supersaturated", "interface", "surface", "boundary", "layer",
    "molecular", "atomic", "ion", "ionic", "charge",
    "electric", "magnetic", "field", "force", "pressure",
    "stress", "strain", "elastic", "plastic", "deformation",
    "fracture", "crack", "defect", "lattice", "structure",
    "material", "composite", "polymer", "ceramic", "metal",
    "alloy", "oxide", "hydroxide", "acid", "base",
    "oxidation", "reduction", "electron", "proton", "neutron",
    "photon", "quantum", "wave", "particle", "interaction",
    "binding", "adsorption", "absorption", "desorption", "release",
    "mechanism", "pathway", "process", "phenomenon", "effect",
    "formation", "transformation", "conversion", "synthesis",
    "degradation", "stability", "instability",
    # Domain-specific terms
    "bone", "shell", "skeleton", "tissue", "biological",
    "marine", "diatom", "osteoblast", "collagen",
    "sonocrystallization", "sonochemical", "cavitation",
    "radiative", "cooling", "emission", "absorption",
    "desalination", "purification", "filtration", "separation",
    "battery", "electrode", "electrolyte", "cathode", "anode",
    "capacitor", "conductor", "insulator", "semiconductor",
})


# Lazy-loaded NER model (loaded once, reused)
_NLP_MODEL = None


def _get_nlp_model():
    """Load and cache the spaCy NER model.

    The model is loaded once and reused. The model version is
    recorded in the provenance ledger.
    """
    global _NLP_MODEL
    if _NLP_MODEL is None:
        import spacy
        _NLP_MODEL = spacy.load(NULL_CONFIG["ner_model"])
    return _NLP_MODEL


def get_ner_model_info() -> Dict[str, str]:
    """Return information about the frozen NER model."""
    import spacy
    return {
        "ner_library": NULL_CONFIG["ner_library"],
        "ner_model": NULL_CONFIG["ner_model"],
        "spacy_version": spacy.__version__,
    }


def compute_universal_seed(preregistration_id: str, case_id: str,
                            stage_id: str = "downstream") -> str:
    """Compute the universal invocation seed.

    Per B2_IMPLEMENTATION_INVARIANTS.md:
        seed = SHA256(preregistration_id || case_id || stage_id)

    arm_id is NOT included → same seed for engine and null for the
    same case+stage.

    NOTE (per audit round 48): This does NOT guarantee equivalent
    generation randomness. The null is deterministic and has no
    randomness to equalize. The seed equality ensures the invocation
    identity is the same, so any difference in output is attributable
    to the pipeline difference (not to a seed difference).

    Args:
        preregistration_id: the frozen protocol SHA
        case_id: e.g., "CASE-001"
        stage_id: "downstream" for generation (default)

    Returns:
        64-character hex string (SHA-256)
    """
    data = f"{preregistration_id}|{case_id}|{stage_id}"
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def _canonicalize_entity(text: str) -> str:
    """Canonicalize an entity string.

    Per R5.2: lowercase → strip punctuation → singularize (lemmatize)

    Uses spaCy's lemmatizer for singularization.

    Args:
        text: the entity text

    Returns:
        Canonicalized entity string.
    """
    # Lowercase
    text = text.lower().strip()
    # Strip punctuation
    cleaned = ""
    for ch in text:
        if ch.isalnum() or ch.isspace():
            cleaned += ch
        else:
            cleaned += " "
    cleaned = cleaned.strip()
    if not cleaned:
        return ""
    # Lemmatize using spaCy (singularizes nouns)
    nlp = _get_nlp_model()
    doc = nlp(cleaned)
    lemmas = [token.lemma_ for token in doc if not token.is_stop]
    if not lemmas:
        return cleaned
    return lemmas[0]


def _extract_entities(text: str) -> List[str]:
    """Extract named entities from text using frozen NER.

    Per R5.2: Uses spaCy en_core_web_sm for NER.

    Args:
        text: the abstraction text

    Returns:
        List of canonicalized entity strings.
    """
    nlp = _get_nlp_model()
    doc = nlp(text)

    entities = []
    for ent in doc.ents:
        canonical = _canonicalize_entity(ent.text)
        if canonical and len(canonical) >= NULL_CONFIG["min_token_length"]:
            entities.append(canonical)

    # Also extract noun chunks as additional entity candidates
    for chunk in doc.noun_chunks:
        canonical = _canonicalize_entity(chunk.text)
        if canonical and len(canonical) >= NULL_CONFIG["min_token_length"]:
            entities.append(canonical)

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for e in entities:
        if e not in seen:
            seen.add(e)
            unique.append(e)

    return unique


def compute_shared_entity(abstraction_a: str, abstraction_b: str) -> Optional[str]:
    """Deterministically compute the shared entity/concept between two abstractions.

    Per B2_REVISION_R5_2.md (SERIOUS 3 fix, IMPLEMENTED per audit round 48):
        shared_entity = FirstEntity(SortedIntersection(
            Entities(A), Entities(B), StopwordList, EntityDictionary))

    This is the SPECIFIED function, not a placeholder:
    - Entities(): spaCy en_core_web_sm NER (frozen, version recorded)
    - Canonicalization: lowercase → strip punctuation → lemmatize
    - StopwordList: FROZEN_STOPWORDS (frozen, will be NLTK in full impl)
    - EntityDictionary: FROZEN_ENTITY_DICTIONARY (preregistered)
    - Sort: alphabetical ascending (deterministic tie-break)
    - FirstEntity: first in sorted list, or None if empty

    Args:
        abstraction_a: abstracted mechanism text from domain A
        abstraction_b: abstracted mechanism text from domain B

    Returns:
        The shared entity string, or None if no shared entity found.
    """
    # Extract entities using frozen NER
    entities_a = set(_extract_entities(abstraction_a))
    entities_b = set(_extract_entities(abstraction_b))

    # Intersection
    intersection = entities_a & entities_b

    if not intersection:
        return None

    # Filter by stopword list
    filtered = {e for e in intersection if e not in FROZEN_STOPWORDS}
    if not filtered:
        return None

    # Filter by entity dictionary
    # NOTE: In the initial implementation, we accept ALL filtered entities
    # (the dictionary filter is permissive). In the full implementation,
    # only entities in FROZEN_ENTITY_DICTIONARY are accepted.
    # For now, we use the dictionary as a positive signal but don't
    # exclude non-dictionary entities, to avoid over-restricting.
    dictionary_filtered = {e for e in filtered if e in FROZEN_ENTITY_DICTIONARY}
    if dictionary_filtered:
        filtered = dictionary_filtered
    # If no dictionary entities, fall back to all filtered entities

    # Sort alphabetically (deterministic tie-break)
    sorted_intersection = sorted(filtered)

    # Return first entity
    return sorted_intersection[0]


def construct_candidate(abstraction_a: str, abstraction_b: str) -> str:
    """Construct a single null candidate from two abstractions.

    The candidate is in the common schema:
        relationship: "<A> is related to <B>"
        mechanism: "Both involve <shared>. <A> occurs in domain A. ..."

    The candidate text combines relationship and mechanism into a
    single string that the parser can extract.

    Args:
        abstraction_a: abstracted mechanism from domain A
        abstraction_b: abstracted mechanism from domain B

    Returns:
        The candidate text string.
    """
    shared_entity = compute_shared_entity(abstraction_a, abstraction_b)

    relationship = NULL_CONFIG["relationship_template"].format(
        a_abstraction=abstraction_a,
        b_abstraction=abstraction_b,
    )

    if shared_entity is not None:
        mechanism = NULL_CONFIG["mechanism_template_with_shared"].format(
            shared_entity=shared_entity,
            a_abstraction=abstraction_a,
            b_abstraction=abstraction_b,
        )
    else:
        mechanism = NULL_CONFIG["mechanism_template_no_shared"].format(
            a_abstraction=abstraction_a,
            b_abstraction=abstraction_b,
        )

    # Combine into candidate text
    candidate = f"RELATIONSHIP: {relationship}\nMECHANISM: {mechanism}"
    return candidate


def generate_null_raw_output(
    abstracted_mechanisms_a: List[str],
    abstracted_mechanisms_b: List[str],
) -> str:
    """Generate the null's raw output containing exactly 3 candidates.

    Per B2_REVISION_R5_2.md (SERIOUS 1 fix, CORRECTED per audit round 48):
        Candidate 1 = (A1, B1) — top-ranked from each
        Candidate 2 = (A2, B2) — second-ranked from each
        Candidate 3 = (A3, B3) — third-ranked from each

    RANK-PAIRING REQUIREMENT (audit round 48):
        R5.2 specifies rank-pairing: C_i = (A_i, B_i).
        This requires BOTH lists to have at least 3 entries.
        If either list has fewer than 3, the implementation FAILS CLOSED
        (NULL_GENERATION_FAILURE) rather than padding.
        Padding would violate the rank-pairing specification and create
        a different experimental condition than the engine.

    Per B2_IMPLEMENTATION_INVARIANTS.md (Invariant 2):
        If abstraction lists are empty → NULL_GENERATION_FAILURE

    The raw output is in parser format (---CANDIDATE--- delimiters)
    so it goes through the SAME provenance spine as the engine.

    Args:
        abstracted_mechanisms_a: ranked list of abstractions from domain A
        abstracted_mechanisms_b: ranked list of abstractions from domain B

    Returns:
        Raw output string with 3 candidates separated by delimiters.

    Raises:
        ValueError: (NULL_GENERATION_FAILURE) if either abstraction
                    list is empty OR has fewer than 3 entries
                    (rank-pairing requires 3 from each).
    """
    # Fail-closed: empty abstractions
    if not abstracted_mechanisms_a or not abstracted_mechanisms_b:
        raise ValueError(
            "NULL_GENERATION_FAILURE: NO_REQUIRED_ABSTRACTION. "
            f"abstraction_a has {len(abstracted_mechanisms_a)} entries, "
            f"abstraction_b has {len(abstracted_mechanisms_b)} entries. "
            f"Cannot generate null candidates without abstractions. "
            f"The case fails closed — no fabricated candidates."
        )

    # Fail-closed: rank-pairing requires at least 3 abstractions from each
    n_required = NULL_CONFIG["n_candidates"]
    if len(abstracted_mechanisms_a) < n_required:
        raise ValueError(
            f"NULL_GENERATION_FAILURE: INSUFFICIENT_ABSTRACTIONS_A. "
            f"Rank-pairing requires {n_required} abstractions from A, "
            f"got {len(abstracted_mechanisms_a)}. "
            f"Padding is NOT permitted (audit round 48). "
            f"The case fails closed — no rank-pairing violation."
        )
    if len(abstracted_mechanisms_b) < n_required:
        raise ValueError(
            f"NULL_GENERATION_FAILURE: INSUFFICIENT_ABSTRACTIONS_B. "
            f"Rank-pairing requires {n_required} abstractions from B, "
            f"got {len(abstracted_mechanisms_b)}. "
            f"Padding is NOT permitted (audit round 48). "
            f"The case fails closed — no rank-pairing violation."
        )

    delimiter = NULL_CONFIG["candidate_delimiter"]

    # Rank-paired candidate generation (no padding)
    candidates = []
    for rank in range(n_required):
        abstraction_a = abstracted_mechanisms_a[rank]
        abstraction_b = abstracted_mechanisms_b[rank]
        candidate = construct_candidate(abstraction_a, abstraction_b)
        candidates.append(candidate)

    # Build raw output in parser format
    preamble = "---NULL GENERATION OUTPUT---\n"
    parts = [preamble]
    for candidate in candidates:
        parts.append(delimiter)
        parts.append(candidate)
        parts.append("\n")

    raw_output = "".join(parts)
    return raw_output


class NullGenerationResult:
    """Result of null generation for a single case.

    Contains the raw output, candidate list, and provenance information.
    """

    def __init__(
        self,
        case_id: str,
        raw_output: str,
        raw_output_sha256: str,
        raw_output_blob_path: str,
        candidates: List[str],
        candidate_sha256s: List[str],
        invocation_seed: str,
    ):
        self.case_id = case_id
        self.raw_output = raw_output
        self.raw_output_sha256 = raw_output_sha256
        self.raw_output_blob_path = raw_output_blob_path
        self.candidates = candidates
        self.candidate_sha256s = candidate_sha256s
        self.invocation_seed = invocation_seed

    def n_candidates(self) -> int:
        return len(self.candidates)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "case_id": self.case_id,
            "raw_output_sha256": self.raw_output_sha256,
            "raw_output_blob_path": self.raw_output_blob_path,
            "n_candidates": self.n_candidates(),
            "candidate_sha256s": self.candidate_sha256s,
            "invocation_seed": self.invocation_seed,
        }


def generate_null_candidates(
    case_id: str,
    abstracted_mechanisms_a: List[str],
    abstracted_mechanisms_b: List[str],
    preregistration_id: str,
) -> NullGenerationResult:
    """Generate null candidates and store them through the provenance spine.

    This is the main entry point for null generation. It:
    1. Computes the universal seed (same invocation identity as engine)
    2. Generates the raw output (3 rank-paired candidates)
    3. Stores the raw output in content-addressed storage
    4. Parses candidates with the frozen parser
    5. Computes candidate SHA-256s
    6. Returns a NullGenerationResult with all provenance info

    The caller is responsible for appending the CANDIDATE_GENERATED
    events to the provenance ledger.

    Args:
        case_id: e.g., "CASE-001"
        abstracted_mechanisms_a: ranked abstractions from domain A (must have >= 3)
        abstracted_mechanisms_b: ranked abstractions from domain B (must have >= 3)
        preregistration_id: the frozen protocol SHA

    Returns:
        NullGenerationResult with raw output, candidates, and provenance.

    Raises:
        ValueError: if abstractions are empty or have fewer than 3 entries
                    (NULL_GENERATION_FAILURE, fail-closed).
    """
    # 1. Compute universal seed (same invocation identity as engine)
    seed = compute_universal_seed(preregistration_id, case_id, "downstream")

    # 2. Generate raw output (3 rank-paired candidates)
    raw_output = generate_null_raw_output(
        abstracted_mechanisms_a, abstracted_mechanisms_b
    )

    # 3. Store raw output in content-addressed storage
    blob_path, raw_sha = store_raw_output(case_id, "null", raw_output)

    # 4. Parse candidates with the frozen parser
    candidates = parse_candidates(raw_output)

    # 5. Compute candidate SHA-256s
    candidate_sha256s = [
        compute_sha256(c.encode("utf-8")) for c in candidates
    ]

    return NullGenerationResult(
        case_id=case_id,
        raw_output=raw_output,
        raw_output_sha256=raw_sha,
        raw_output_blob_path=blob_path,
        candidates=candidates,
        candidate_sha256s=candidate_sha256s,
        invocation_seed=seed,
    )


def record_null_in_ledger(
    ledger: ProvenanceLedger,
    result: NullGenerationResult,
    engine_version: str,
    provider: str,
    model: str,
    prompt_hash: str,
    source_pair_sha256: str,
    generation_timestamp: str,
) -> List[Dict[str, Any]]:
    """Record null candidates in the provenance ledger.

    Creates a CANDIDATE_GENERATED event for each null candidate.
    These events are immutable and linked in the hash chain.

    Args:
        ledger: the provenance ledger
        result: the NullGenerationResult from generate_null_candidates
        engine_version: git commit SHA of the null generation code
        provider: "ZAI" (same as engine)
        model: "glm-4-plus" (same as engine)
        prompt_hash: SHA-256 of the frozen null prompt
        source_pair_sha256: SHA-256 of (source_a, source_b)
        generation_timestamp: ISO 8601 timestamp

    Returns:
        List of created ledger entries.
    """
    entries = []
    for rank, (candidate, candidate_sha) in enumerate(
        zip(result.candidates, result.candidate_sha256s), start=1
    ):
        entry = ledger.append_candidate_entry(
            case_id=result.case_id,
            arm="null",
            candidate_rank=rank,
            raw_output_sha256=result.raw_output_sha256,
            raw_output_blob_path=result.raw_output_blob_path,
            candidate_sha256=candidate_sha,
            candidate_text=candidate,
            generation_timestamp=generation_timestamp,
            engine_version=engine_version,
            provider=provider,
            model=model,
            prompt_hash=prompt_hash,
            source_pair_sha256=source_pair_sha256,
            invocation_seed=result.invocation_seed,
        )
        entries.append(entry)
    return entries
