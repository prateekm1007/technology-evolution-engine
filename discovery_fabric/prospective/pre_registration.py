"""
PROSPECTIVE EXPERIMENT — Pre-Registration Module
=================================================

Stage 1 of the prospective pipeline:
    PRE_REGISTER → FREEZE_MODEL → FREEZE_EVIDENCE → GENERATE_PREDICTION
                 → WAIT → EXTERNAL_OBSERVATION → DETERMINISTIC_SCORE

This module produces the pre-registration manifest. The manifest is the
immutable, hash-sealed record of EVERYTHING that is fixed before any
prediction is generated:

    - Problem set (selected independently of outcomes)
    - Model snapshot identifier (frozen weights or version pin)
    - Retrieval corpus hash (frozen)
    - Prompt templates for all 4 arms (LLM-only, mechanism-only, full, random)
    - Analysis plan (alpha, MDE, sample size, INDETERMINATE handling)
    - Observation window (start, end)
    - Outcome source specification (independent of engine)
    - Trusted timestamp (UTC, from system clock; verifiable)

CRITICAL INVARIANTS (enforced by audit_verifier.py):
    (I1) The manifest is hash-sealed IMMEDIATELY after creation. Any
         modification after sealing is detectable.
    (I2) The manifest timestamp MUST be a real UTC timestamp from the system
         clock at sealing time. It MUST NOT be backdated. The audit verifier
         will reject any manifest whose timestamp is more than 60 seconds
         older than the file's filesystem mtime.
    (I3) The problem set MUST NOT contain any outcome information. Each
         problem is a description + a frozen corpus query, nothing more.
    (I4) All 4 arms are registered in the SAME manifest with the SAME
         timestamp. They cannot be registered separately.
    (I5) The analysis plan is fixed at registration. It cannot be modified
         after outcomes are observed.

DO NOT RUN THIS MODULE unless you are committing to the full prospective
experiment. Running it creates a real pre-registration record.

This module is currently in DRAFT mode — calling main() will produce a
sample manifest in the manifests/ directory but will NOT commit it to the
append-only log. To commit for real, set COMMIT_TO_LOG=True (not yet done).
"""
from __future__ import annotations

import json
import hashlib
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Any

REPO = Path("/home/z/my-project/audit/technology-evolution-engine")
PROSPECTIVE_DIR = REPO / "discovery_fabric/prospective"
MANIFESTS_DIR = PROSPECTIVE_DIR / "manifests"
LOG_FILE = PROSPECTIVE_DIR / "manifests" / "append_only_log.jsonl"

MANIFESTS_DIR.mkdir(parents=True, exist_ok=True)

# =============================================================================
# Pre-registration schema
# =============================================================================

PRE_REG_SCHEMA_VERSION = "1.0.0"

def build_manifest(
    problem_set: list[dict],
    model_snapshot: dict,
    retrieval_corpus: dict,
    prompt_templates: dict,
    analysis_plan: dict,
    observation_window: dict,
    outcome_source_spec: dict,
) -> dict:
    """Build a pre-registration manifest (unsealed).

    Args:
        problem_set: list of problems. Each problem is:
            {
              "problem_id": str,
              "description": str,           # NO outcome info
              "corpus_query": str,           # query to run against frozen corpus
              "domain": str,
              "expected_outcome_type": "NUMERIC" | "BINARY",
              "measurement_unit": str,       # e.g., "cycles", "efficiency %"
            }
        model_snapshot:
            {
              "model_name": str,             # e.g., "glm-4-plus"
              "model_version": str,          # version pin, e.g., "2024-09-15"
              "weights_hash": str | None,   # SHA-256 of weights file (if local)
              "endpoint_url": str | None,   # if hosted
              "api_version": str | None,    # if hosted
            }
        retrieval_corpus:
            {
              "corpus_name": str,
              "corpus_version": str,
              "corpus_hash": str,           # SHA-256 of corpus manifest
              "document_count": int,
              "date_filter_upper_bound": str,  # ISO date — excludes docs after this
              "date_filter_verified": bool,
            }
        prompt_templates: dict mapping arm_name -> prompt template string.
            MUST contain exactly 4 keys: "B_llm_only", "C_mechanism",
            "F_full", "D_random".
        analysis_plan:
            {
              "primary_endpoint": str,       # "DPS_1_rate"
              "comparison": str,             # "treatment_vs_random"
              "alpha": float,                # e.g., 0.05
              "mde": float,                  # minimum detectable effect, e.g., 0.15
              "sample_size_per_arm": int,    # e.g., 50
              "indeterminate_handling": str, # "excluded" | "counted_as_failure"
              "calibration_threshold": float,  # e.g., 0.50
              "ic_threshold": float,         # e.g., 0.67 (>= 4/6 encoded = RECONSTRUCTION)
            }
        observation_window:
            {
              "window_start": str,           # ISO datetime — when observation begins
              "window_end": str,             # ISO datetime — when observation closes
              "min_observations_per_problem": int,  # e.g., 1
            }
        outcome_source_spec:
            {
              "source_type": str,            # "peer_reviewed" | "public_database" | ...
              "source_name": str,            # e.g., "Nature", "arXiv", "ClinicalTrials.gov"
              "source_url": str,
              "independence_verification": str,  # how independence is verified
            }

    Returns:
        Unsealed manifest dict (no manifest_hash yet).
    """
    # Validate prompt templates
    required_arms = {"B_llm_only", "C_mechanism", "F_full", "D_random"}
    if set(prompt_templates.keys()) != required_arms:
        raise ValueError(f"prompt_templates must have exactly {required_arms}, got {set(prompt_templates.keys())}")

    # Validate analysis plan
    required_plan_keys = {"primary_endpoint", "comparison", "alpha", "mde",
                          "sample_size_per_arm", "indeterminate_handling",
                          "calibration_threshold", "ic_threshold"}
    if not required_plan_keys.issubset(analysis_plan.keys()):
        raise ValueError(f"analysis_plan missing keys: {required_plan_keys - set(analysis_plan.keys())}")

    # Validate problem set (no outcome info allowed)
    for p in problem_set:
        for forbidden_key in ["outcome", "answer", "result", "observed_value", "historical_result"]:
            if forbidden_key in p:
                raise ValueError(f"problem {p.get('problem_id')} contains forbidden key '{forbidden_key}' (outcome leakage)")

    manifest = {
        "schema_version": PRE_REG_SCHEMA_VERSION,
        "manifest_type": "PRE_REGISTRATION",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "problem_set": problem_set,
        "model_snapshot": model_snapshot,
        "retrieval_corpus": retrieval_corpus,
        "prompt_templates": prompt_templates,
        "analysis_plan": analysis_plan,
        "observation_window": observation_window,
        "outcome_source_spec": outcome_source_spec,
        "arms": sorted(required_arms),
    }
    return manifest


def seal_manifest(manifest: dict) -> dict:
    """Seal a manifest by computing its SHA-256 hash.

    After sealing, the manifest is immutable. Any modification will be
    detectable by re-computing the hash.
    """
    canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    manifest["manifest_hash"] = hashlib.sha256(canonical.encode()).hexdigest()
    return manifest


def verify_manifest(manifest: dict) -> bool:
    """Verify that a manifest's hash matches its contents."""
    stored = manifest.get("manifest_hash")
    if not stored:
        return False
    m = {k: v for k, v in manifest.items() if k != "manifest_hash"}
    canonical = json.dumps(m, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    computed = hashlib.sha256(canonical.encode()).hexdigest()
    return computed == stored


def append_to_log(manifest: dict) -> Path:
    """Append a sealed manifest to the append-only log.

    The log is a JSONL file. Each line is one manifest. Once written,
    lines cannot be modified without detection (audit_verifier checks
    line count + per-line hash + cumulative hash).
    """
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "log_entry_type": "PRE_REGISTRATION",
        "manifest_hash": manifest["manifest_hash"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "manifest": manifest,
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return LOG_FILE


def save_manifest(manifest: dict, name: str = "pre_registration.json") -> Path:
    """Save a sealed manifest to the manifests directory."""
    path = MANIFESTS_DIR / name
    with open(path, "w") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    return path


# =============================================================================
# Sample / template manifest (for infrastructure verification only)
# =============================================================================

SAMPLE_PROBLEM_SET = [
    {
        "problem_id": "PROS-001",
        "description": "Identify a materials combination that achieves > 1500 Wh/kg specific energy in a rechargeable battery, falsified if no combination achieves > 1000 Wh/kg within 24 months.",
        "corpus_query": "battery materials specific energy cathode anode electrolyte",
        "domain": "materials_science",
        "expected_outcome_type": "NUMERIC",
        "measurement_unit": "Wh/kg",
    },
    {
        "problem_id": "PROS-002",
        "description": "Identify a small-molecule compound that achieves > 10x selective killing of KRAS-G12C mutant cancer cells vs wild-type, falsified if selectivity < 3x in vitro.",
        "corpus_query": "KRAS G12C inhibitor selective cancer",
        "domain": "oncology",
        "expected_outcome_type": "NUMERIC",
        "measurement_unit": "selectivity_ratio",
    },
]

SAMPLE_MODEL_SNAPSHOT = {
    "model_name": "glm-4-plus",
    "model_version": "TO_BE_PINNED",
    "weights_hash": None,
    "endpoint_url": "https://api.z.ai/v1/chat/completions",
    "api_version": "TO_BE_PINNED",
    "note": "Hosted model — version pin MUST be set before sealing. Local model preferred for true freezing.",
}

SAMPLE_RETRIEVAL_CORPUS = {
    "corpus_name": "TO_BE_SPECIFIED",
    "corpus_version": "TO_BE_SPECIFIED",
    "corpus_hash": "TO_BE_COMPUTED",
    "document_count": 0,
    "date_filter_upper_bound": "TO_BE_SET",  # MUST be <= manifest timestamp
    "date_filter_verified": False,
    "note": "Corpus MUST be frozen and hash-sealed before this manifest is sealed.",
}

SAMPLE_PROMPT_TEMPLATES = {
    "B_llm_only": (
        "PROBLEM: {description}\n\n"
        "Retrieve relevant evidence from the frozen corpus using query: {corpus_query}\n\n"
        "Based ONLY on the retrieved evidence, propose ONE falsifiable quantitative prediction. "
        "Output JSON with: hypothesis, prediction, predicted_value, tolerance_lower, "
        "tolerance_upper, expected_direction, measurement_method, falsification_condition."
    ),
    "C_mechanism": (
        "PROBLEM: {description}\n\n"
        "Retrieve relevant evidence using query: {corpus_query}\n\n"
        "Identify the CORE MECHANISM in the retrieved evidence. Propose ONE falsifiable "
        "quantitative prediction based on THAT MECHANISM. Output JSON with: hypothesis, "
        "prediction, predicted_value, tolerance_lower, tolerance_upper, expected_direction, "
        "measurement_method, falsification_condition."
    ),
    "F_full": (
        "PROBLEM: {description}\n\n"
        "Retrieve relevant evidence using query: {corpus_query}\n\n"
        "Identify (a) invariant principles, (b) operational constraints, (c) mechanism "
        "interactions. Propose ONE falsifiable quantitative prediction with point estimate "
        "and tight tolerance. Output JSON with: hypothesis, prediction, predicted_value, "
        "tolerance_lower, tolerance_upper, expected_direction, measurement_method, "
        "falsification_condition."
    ),
    "D_random": (
        "PROBLEM: {description}\n\n"
        "Retrieve relevant evidence using query: {corpus_query}\n\n"
        "Propose ANY plausible scientific prediction that follows from the retrieved evidence. "
        "The prediction should be specific and falsifiable. Output JSON with: hypothesis, "
        "prediction, predicted_value, tolerance_lower, tolerance_upper, expected_direction, "
        "measurement_method, falsification_condition."
    ),
}

SAMPLE_ANALYSIS_PLAN = {
    "primary_endpoint": "DPS_1_rate",
    "comparison": "treatment_vs_random",
    "alpha": 0.05,
    "mde": 0.15,
    "sample_size_per_arm": 50,
    "indeterminate_handling": "excluded",
    "calibration_threshold": 0.50,
    "ic_threshold": 0.67,
    "statistical_test": "two_proportion_z_test",
    "multiple_testing_correction": "bonferroni",
    "num_comparisons": 3,  # B vs D, C vs D, F vs D
}

SAMPLE_OBSERVATION_WINDOW = {
    "window_start": "TO_BE_SET",  # e.g., 12 months after registration
    "window_end": "TO_BE_SET",    # e.g., 24 months after registration
    "min_observations_per_problem": 1,
}

SAMPLE_OUTCOME_SOURCE_SPEC = {
    "source_type": "peer_reviewed",
    "source_name": "TO_BE_SPECIFIED",
    "source_url": "TO_BE_SPECIFIED",
    "independence_verification": (
        "Outcome must be published in a peer-reviewed venue that the engine "
        "cannot influence. The publication date must be within the observation "
        "window. The outcome value must be extracted by an independent curator "
        "who is not the experimenter."
    ),
}


def build_sample_manifest() -> dict:
    """Build a SAMPLE manifest for infrastructure verification.

    This does NOT commit to the append-only log. It only demonstrates that
    the manifest builder works.
    """
    manifest = build_manifest(
        problem_set=SAMPLE_PROBLEM_SET,
        model_snapshot=SAMPLE_MODEL_SNAPSHOT,
        retrieval_corpus=SAMPLE_RETRIEVAL_CORPUS,
        prompt_templates=SAMPLE_PROMPT_TEMPLATES,
        analysis_plan=SAMPLE_ANALYSIS_PLAN,
        observation_window=SAMPLE_OBSERVATION_WINDOW,
        outcome_source_spec=SAMPLE_OUTCOME_SOURCE_SPEC,
    )
    return seal_manifest(manifest)


# =============================================================================
# Main — infrastructure verification only (does NOT commit)
# =============================================================================

def main():
    """Verify the infrastructure by building and verifying a sample manifest.

    DOES NOT COMMIT TO THE LOG. The sample manifest is saved to
    manifests/_sample_pre_registration.json for inspection only.
    """
    print("=" * 72)
    print("PROSPECTIVE EXPERIMENT — PRE-REGISTRATION INFRASTRUCTURE CHECK")
    print("=" * 72)
    print()
    print("This module is in DRAFT mode. It builds a SAMPLE manifest to verify")
    print("the infrastructure works. It does NOT commit to the append-only log.")
    print()
    print("To commit a real pre-registration:")
    print("  1. Replace all TO_BE_* fields with real values")
    print("  2. Set COMMIT_TO_LOG=True in the call to main()")
    print("  3. Run this module")
    print()

    manifest = build_sample_manifest()

    # Verify
    ok = verify_manifest(manifest)
    print(f"Manifest built. Schema version: {manifest['schema_version']}")
    print(f"Arms registered: {manifest['arms']}")
    print(f"Problem set size: {len(manifest['problem_set'])}")
    print(f"Manifest hash: {manifest['manifest_hash'][:32]}...")
    print(f"Hash verification: {'PASS' if ok else 'FAIL'}")

    # Save sample
    path = save_manifest(manifest, name="_sample_pre_registration.json")
    print(f"\nSample manifest saved: {path}")
    print(f"\nDO NOT run a real pre-registration until the audit_verifier passes")
    print(f"and an independent auditor has reviewed the manifest.")


if __name__ == "__main__":
    main()
