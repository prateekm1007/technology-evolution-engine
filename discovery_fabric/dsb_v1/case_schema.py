"""
DSB V1 — Case Schema
=====================

Each case is a JSON file with this schema:

{
  "case_id": "DSB-R-001",                    # DSB-R-### for real, DSB-F-### for fabricated
  "case_type": "real" | "fabricated",
  "domain": "materials" | "biology" | "ml" | ...,
  "name_internal": "lithium_ion_battery",    # internal name (NEVER shown to generator)
  "cutoff_date": "1990-12-31T23:59:59Z",     # pre-discovery cutoff

  "exposed_facts": [
    "fact 1 the generator sees",
    "fact 2 the generator sees",
    ...
  ],

  "withheld_facts": [
    "fact 1 the generator must NOT see (the other side of the relationship)",
    "fact 2 the generator must NOT see (the explicit combination statement)",
    ...
  ],

  "breakthrough_relationship": "The actual discovery: combining X with Y yields Z.",

  "answer_hash": "SHA-256 of canonical breakthrough_relationship text",

  "forbidden_terms": [                       # terms that must NEVER appear in the payload
    "lithium-ion", "LiCoO2", "graphite anode", ...
  ],

  "future_terminology": [                    # terms that emerged post-discovery
    "Li-ion", "LiCoO2-graphite", ...
  ],

  "answer_mechanism": "The mechanism behind the breakthrough (one paragraph).",

  "constraint_release": "What constraint was released by the breakthrough?",

  "historical_source": "Sony commercialization 1991; Goodenough/Whittingham/Yoshino (Nobel 2019)",

  "fabricated": false                        # false for real, true for fabricated
}

CRITICAL DESIGN PRINCIPLE:
  The exposed_facts give the generator ONE SIDE of the eventual relationship
  + general context. The withheld_facts contain the OTHER SIDE + the explicit
  combination statement. The generator must independently infer the combination
  to score positively on discovery_structure_recovery.

  The payload_builder extracts ONLY exposed_facts and constructs a neutral
  prompt. It NEVER includes:
    - case_id
    - name_internal
    - breakthrough_relationship
    - withheld_facts
    - forbidden_terms
    - answer_mechanism
    - constraint_release
    - historical_source
"""
import json
import hashlib
from pathlib import Path
from typing import Any

CASE_SCHEMA_VERSION = "1.0.0"


def compute_answer_hash(breakthrough_relationship: str) -> str:
    """Compute the canonical answer hash for a case."""
    canonical = breakthrough_relationship.strip().lower()
    return hashlib.sha256(canonical.encode()).hexdigest()


def validate_case(case: dict) -> tuple[bool, list[str]]:
    """Validate that a case file conforms to the schema."""
    failures = []
    required_fields = [
        "case_id", "case_type", "domain", "name_internal", "cutoff_date",
        "exposed_facts", "withheld_facts", "breakthrough_relationship",
        "answer_hash", "forbidden_terms", "future_terminology",
        "answer_mechanism", "constraint_release", "historical_source", "fabricated",
    ]
    for f in required_fields:
        if f not in case:
            failures.append(f"missing field: {f}")

    # Validate answer_hash matches breakthrough_relationship
    if "breakthrough_relationship" in case and "answer_hash" in case:
        expected = compute_answer_hash(case["breakthrough_relationship"])
        if case["answer_hash"] != expected:
            failures.append(f"answer_hash mismatch: expected {expected[:16]}, got {case['answer_hash'][:16]}")

    # Validate case_type matches fabricated flag
    if case.get("case_type") == "real" and case.get("fabricated") is True:
        failures.append("case_type=real but fabricated=True")
    if case.get("case_type") == "fabricated" and case.get("fabricated") is False:
        failures.append("case_type=fabricated but fabricated=False")

    # Validate case_id prefix
    cid = case.get("case_id", "")
    if case.get("case_type") == "real" and not cid.startswith("DSB-R-"):
        failures.append(f"real case_id should start with DSB-R-, got {cid}")
    if case.get("case_type") == "fabricated" and not cid.startswith("DSB-F-"):
        failures.append(f"fabricated case_id should start with DSB-F-, got {cid}")

    # Validate exposed_facts and withheld_facts are non-empty
    if not case.get("exposed_facts"):
        failures.append("exposed_facts is empty")
    if not case.get("withheld_facts"):
        failures.append("withheld_facts is empty")

    # Validate no overlap between exposed and withheld
    exposed_set = {f.strip().lower() for f in case.get("exposed_facts", [])}
    withheld_set = {f.strip().lower() for f in case.get("withheld_facts", [])}
    overlap = exposed_set & withheld_set
    if overlap:
        failures.append(f"exposed_facts and withheld_facts overlap: {overlap}")

    return (len(failures) == 0, failures)


def load_case(path: Path) -> dict:
    """Load a case file."""
    with open(path) as f:
        return json.load(f)


def load_all_cases(cases_dir: Path) -> list[dict]:
    """Load all case files from a directory."""
    cases = []
    for p in sorted(cases_dir.glob("DSB-*.json")):
        cases.append(load_case(p))
    return cases
