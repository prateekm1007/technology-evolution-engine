#!/usr/bin/env python3
"""freeze_audit_instrument.py — Freeze the baseline equivalence audit instrument.

Per audit round 52: before the first real engine-vs-null run, freeze the
audit protocol itself. This creates a clean separation between the thing
being measured (engine vs null) and the instrument doing the measurement
(the audit).

Frozen artifacts:
    - baseline_equivalence_audit.py source SHA-256
    - ALL_DIMENSIONS list
    - 5-state classification definitions
    - provenance verification code
    - audit output schema
    - ledger schema expected by the audit
    - frozen NER artifacts (already established)
    - parser identity/configuration (already established)

The first real engine/null execution then becomes a proper experimental
artifact with a frozen measurement instrument.

CRITICAL RULE (per audit round 52):
    The first real run is DIAGNOSTIC, not evidence for the North Star.
    Even if it produces 13/13 OBSERVED_EQUAL, that does NOT establish
    baseline fairness. And if it produces 8 EQUAL / 5 DIFFERENT, that
    does NOT establish baseline unfairness. It establishes the empirical
    structure of the two arms. The external/preregistered adjudication
    protocol determines whether differences are acceptable relative to
    the estimand.
"""
import hashlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "provenance" / "frozen_components"

# The audit script whose identity we're freezing
AUDIT_SCRIPT_PATH = REPO_ROOT / "scripts" / "baseline_equivalence_audit.py"

# The parser whose identity is part of the audit instrument
PARSER_SCRIPT_PATH = REPO_ROOT / "engine" / "b2_provenance" / "frozen_parser.py"

# The generation null whose identity is part of the audit instrument
NULL_SCRIPT_PATH = REPO_ROOT / "engine" / "b2_provenance" / "generation_null.py"

# The provenance ledger whose identity is part of the audit instrument
LEDGER_SCRIPT_PATH = REPO_ROOT / "engine" / "b2_provenance" / "provenance_ledger.py"

# The content-addressed storage whose identity is part of the audit instrument
STORAGE_SCRIPT_PATH = REPO_ROOT / "engine" / "b2_provenance" / "content_addressed_storage.py"


def compute_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compute_file_sha256(path: Path) -> str:
    return compute_sha256(path.read_bytes())


def get_audit_dimensions():
    """The frozen 13-dimension set."""
    return [
        "source_pair",
        "upstream_extraction",
        "abstraction",
        "candidate_count",
        "candidate_schema",
        "candidate_length",
        "mechanism_presence",
        "information_available",
        "llm_access",
        "prompt_complexity",
        "entity_specificity",
        "human_intervention",
        "invocation_seed",
    ]


def get_audit_states():
    """The frozen 5-state classification."""
    return [
        "CONTRACT_EQUAL",
        "OBSERVED_EQUAL",
        "OBSERVED_DIFFERENT",
        "NOT_OBSERVABLE",
        "NOT_RUN",
    ]


def get_audit_output_schema():
    """The frozen audit output schema."""
    return {
        "audit_type": "BASELINE_EQUIVALENCE_AUDIT",
        "case_id": "string",
        "engine_entries_found": "int",
        "null_entries_found": "int",
        "engine_provenance_valid": "bool",
        "null_provenance_valid": "bool",
        "engine_verification_errors": "list[string]",
        "null_verification_errors": "list[string]",
        "n_dimensions": "int (always 13)",
        "dimensions_audited": "list[string] (always ALL_DIMENSIONS)",
        "state_counts": "dict[state -> count]",
        "measurements": "list[EquivalenceMeasurement]",
        "summary": {
            "engine_executed": "bool",
            "null_executed": "bool",
            "all_provenance_verified": "bool",
            "all_observations_from_verified_artifacts": "bool",
            "fairness_established": "bool (always False)",
            "notes": "string",
        },
    }


def get_ledger_schema():
    """The frozen ledger schema expected by the audit."""
    return {
        "ledger_type": "B2_PROVENANCE_LEDGER",
        "event_types": ["CANDIDATE_GENERATED", "ADJUDICATION_RECORDED"],
        "generation_entry_fields": [
            "event_type", "candidate_id", "case_id", "arm",
            "candidate_rank", "raw_output_sha256", "raw_output_blob_path",
            "parser_sha256", "parser_config_sha256", "candidate_sha256",
            "candidate_text", "generation_timestamp", "engine_version",
            "provider", "model", "prompt_hash", "source_pair_sha256",
            "invocation_seed", "prev_entry_hash", "entry_hash",
        ],
        "adjudication_entry_fields": [
            "event_type", "candidate_id", "adjudication_input_sha256",
            "gate_a_classification", "gate_a_adjudicator_ids", "gate_a_agreement",
            "gate_c_classification", "gate_c_adjudicator_ids", "gate_c_agreement",
            "prior_art_search_id", "prior_art_channel_a_result",
            "prior_art_channel_b_result", "prior_art_final",
            "case_success", "adjudication_timestamp",
            "prev_entry_hash", "entry_hash",
        ],
        "chain_rule": "each entry's prev_entry_hash == previous entry's entry_hash",
        "immutability": "entries are never modified after creation",
    }


def main():
    print("Freezing audit instrument for provenance verification...")
    print(f"Output directory: {OUTPUT_DIR}")
    print()

    # Compute SHA-256 of all instrument components
    instrument = {
        "artifact_type": "FROZEN_AUDIT_INSTRUMENT",
        "description": (
            "Frozen baseline equivalence audit instrument. "
            "Creates a clean separation between the thing being measured "
            "(engine vs null) and the instrument doing the measurement (the audit). "
            "The first real engine/null execution becomes a proper experimental "
            "artifact with a frozen measurement instrument."
        ),
        "diagnostic_rule": (
            "CRITICAL: The first real run is DIAGNOSTIC, not evidence for the "
            "North Star. Even if it produces 13/13 OBSERVED_EQUAL, that does "
            "NOT establish baseline fairness. And if it produces 8 EQUAL / 5 "
            "DIFFERENT, that does NOT establish baseline unfairness. It "
            "establishes the empirical structure of the two arms. The external/"
            "preregistered adjudication protocol determines whether differences "
            "are acceptable relative to the estimand."
        ),
        "components": {
            "audit_script": {
                "path": str(AUDIT_SCRIPT_PATH.relative_to(REPO_ROOT)),
                "sha256": compute_file_sha256(AUDIT_SCRIPT_PATH),
            },
            "parser_script": {
                "path": str(PARSER_SCRIPT_PATH.relative_to(REPO_ROOT)),
                "sha256": compute_file_sha256(PARSER_SCRIPT_PATH),
            },
            "generation_null_script": {
                "path": str(NULL_SCRIPT_PATH.relative_to(REPO_ROOT)),
                "sha256": compute_file_sha256(NULL_SCRIPT_PATH),
            },
            "provenance_ledger_script": {
                "path": str(LEDGER_SCRIPT_PATH.relative_to(REPO_ROOT)),
                "sha256": compute_file_sha256(LEDGER_SCRIPT_PATH),
            },
            "content_addressed_storage_script": {
                "path": str(STORAGE_SCRIPT_PATH.relative_to(REPO_ROOT)),
                "sha256": compute_file_sha256(STORAGE_SCRIPT_PATH),
            },
        },
        "audit_dimensions": get_audit_dimensions(),
        "audit_states": get_audit_states(),
        "audit_output_schema": get_audit_output_schema(),
        "ledger_schema": get_ledger_schema(),
        "ner_components": {
            "entity_dictionary_sha256": None,  # filled from frozen artifacts
            "stopword_set_sha256": None,
            "ner_model_info_sha256": None,
        },
        "canonical_convention": {
            "format": "JSON",
            "sort_keys": True,
            "separators": [",", ":"],
            "encoding": "UTF-8",
            "no_trailing_newline": True,
            "description": (
                "Canonical serialization for hash computation. "
                "The instrument_sha256 field is computed from the instrument "
                "payload WITHOUT the instrument_sha256 field itself."
            ),
        },
    }

    # Read existing frozen NER component hashes
    ner_dict_sha_path = OUTPUT_DIR / "entity_dictionary.sha256"
    ner_stop_sha_path = OUTPUT_DIR / "stopword_set.sha256"
    ner_model_sha_path = OUTPUT_DIR / "ner_model_info.sha256"

    if ner_dict_sha_path.exists():
        instrument["ner_components"]["entity_dictionary_sha256"] = ner_dict_sha_path.read_text().split()[0]
    if ner_stop_sha_path.exists():
        instrument["ner_components"]["stopword_set_sha256"] = ner_stop_sha_path.read_text().split()[0]
    if ner_model_sha_path.exists():
        instrument["ner_components"]["ner_model_info_sha256"] = ner_model_sha_path.read_text().split()[0]

    # Capture runtime manifest (per audit round 53: frozen source ≠ frozen behavior)
    runtime_manifest = {
        "python_version": sys.version.split()[0],
        "python_executable": sys.executable,
        "platform": sys.platform,
    }
    try:
        import spacy
        runtime_manifest["spacy_version"] = spacy.__version__
        runtime_manifest["spacy_model"] = "en_core_web_sm"
    except Exception:
        runtime_manifest["spacy_version"] = None
        runtime_manifest["spacy_model"] = None
    try:
        import numpy
        runtime_manifest["numpy_version"] = numpy.__version__
    except Exception:
        runtime_manifest["numpy_version"] = None
    try:
        import sympy
        runtime_manifest["sympy_version"] = sympy.__version__
    except Exception:
        runtime_manifest["sympy_version"] = None
    try:
        import scipy
        runtime_manifest["scipy_version"] = scipy.__version__
    except Exception:
        runtime_manifest["scipy_version"] = None

    instrument["runtime_manifest"] = runtime_manifest

    # Compute overall instrument hash (from the instrument WITHOUT the hash field)
    instrument_without_hash = {k: v for k, v in instrument.items() if k != "instrument_sha256"}
    instrument_str = json.dumps(instrument_without_hash, sort_keys=True, separators=(",", ":"))
    instrument_sha = compute_sha256(instrument_str.encode("utf-8"))
    instrument["instrument_sha256"] = instrument_sha

    # Write the frozen instrument
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / "audit_instrument.json"
    output_path.write_text(json.dumps(instrument, indent=2))

    sha_path = OUTPUT_DIR / "audit_instrument.sha256"
    sha_path.write_text(f"{instrument_sha}  audit_instrument.json\n")

    # Verify reproducibility (re-read, strip hash, recompute)
    reloaded = json.loads(output_path.read_text())
    reloaded_without_hash = {k: v for k, v in reloaded.items() if k != "instrument_sha256"}
    reloaded_str = json.dumps(reloaded_without_hash, sort_keys=True, separators=(",", ":"))
    reloaded_sha = compute_sha256(reloaded_str.encode("utf-8"))
    assert reloaded_sha == instrument_sha, "REPRODUCIBILITY FAILED"

    print(f"Audit instrument frozen:")
    print(f"  audit_script:              {instrument['components']['audit_script']['sha256'][:16]}...")
    print(f"  parser_script:             {instrument['components']['parser_script']['sha256'][:16]}...")
    print(f"  generation_null_script:    {instrument['components']['generation_null_script']['sha256'][:16]}...")
    print(f"  provenance_ledger_script:  {instrument['components']['provenance_ledger_script']['sha256'][:16]}...")
    print(f"  storage_script:            {instrument['components']['content_addressed_storage_script']['sha256'][:16]}...")
    print(f"  entity_dictionary_sha256:  {instrument['ner_components']['entity_dictionary_sha256'][:16] if instrument['ner_components']['entity_dictionary_sha256'] else 'None'}...")
    print(f"  stopword_set_sha256:       {instrument['ner_components']['stopword_set_sha256'][:16] if instrument['ner_components']['stopword_set_sha256'] else 'None'}...")
    print(f"  ner_model_info_sha256:     {instrument['ner_components']['ner_model_info_sha256'][:16] if instrument['ner_components']['ner_model_info_sha256'] else 'None'}...")
    print()
    print(f"  INSTRUMENT_SHA256:         {instrument_sha[:16]}...")
    print()
    print("The audit instrument is now frozen. Any change to any component")
    print("will produce a different instrument hash, making the change detectable.")
    print()
    print("CRITICAL RULE:")
    print("  The first real engine/null run is DIAGNOSTIC, not evidence.")
    print("  It establishes the empirical structure of the two arms.")
    print("  Fairness is determined by external adjudication, not by the audit.")


if __name__ == "__main__":
    main()
