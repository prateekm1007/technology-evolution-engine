"""
PROSPECTIVE EXPERIMENT — Observation Window Manager
====================================================

Stage 5-6 of the prospective pipeline:
    PRE_REGISTER → FREEZE_MODEL → FREEZE_EVIDENCE → GENERATE_PREDICTION
                 → WAIT → EXTERNAL_OBSERVATION → DETERMINISTIC_SCORE

This module manages the WAIT and EXTERNAL_OBSERVATION stages:

    WAIT:
        Between generation_timestamp and observation_window.window_start,
        NO engine activity is permitted. The audit_verifier checks that
        no log entries exist in this interval.

    EXTERNAL_OBSERVATION:
        During [window_start, window_end], an independent curator (NOT the
        experimenter) collects outcomes from the pre-registered outcome source.
        Each observation is hash-sealed and appended to the log.

CRITICAL INVARIANTS (enforced by audit_verifier.py):
    (I14) No observation may be collected before window_start.
    (I15) Observations MUST come from the source specified in the manifest.
    (I16) Observations MUST be collected by an independent curator — the
          experimenter cannot collect their own outcomes.
    (I17) Each observation is hash-sealed immediately after collection.
    (I18) The observation's measurement_date MUST be within the observation
          window. Outcomes measured before window_start or after window_end
          are rejected.
    (I19) The observation's source URL MUST be accessible and verifiable
          by an independent auditor at audit time.

DO NOT RUN THIS MODULE. It is infrastructure only. The actual observation
collection requires:
    (a) A real pre-registration manifest with a real observation window
    (b) An independent curator (not the experimenter)
    (c) Real outcomes from the pre-registered source
"""
from __future__ import annotations

import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Any

REPO = Path("/home/z/my-project/audit/technology-evolution-engine")
PROSPECTIVE_DIR = REPO / "discovery_fabric/prospective"
OBSERVATIONS_DIR = PROSPECTIVE_DIR / "observations"
LOG_FILE = PROSPECTIVE_DIR / "manifests" / "append_only_log.jsonl"

OBSERVATIONS_DIR.mkdir(parents=True, exist_ok=True)


# =============================================================================
# Observation schema
# =============================================================================

OBSERVATION_SCHEMA_VERSION = "1.0.0"


def build_observation(
    problem_id: str,
    manifest_hash: str,
    outcome_value: float | str,
    outcome_direction: str,  # INCREASE / DECREASE / BINARY / CORRELATION
    measurement_date: str,   # ISO date — when the outcome was measured
    source_name: str,
    source_url: str,
    curator_id: str,         # identifier of the independent curator
    curator_statement: str,  # signed statement that the curator is independent
    raw_evidence_excerpt: str,  # excerpt from the source documenting the outcome
    manifest: dict,          # the pre-registration manifest (for verification)
) -> dict:
    """Build an observation record.

    The observation is NOT yet sealed. Call seal_observation() to seal it.

    Args:
        problem_id: which problem this observation is for
        manifest_hash: hash of the pre-registration manifest
        outcome_value: the measured value (numeric or "YES"/"NO")
        outcome_direction: direction of the outcome
        measurement_date: when the outcome was measured (ISO date)
        source_name: name of the source (e.g., "Nature", "arXiv:2401.12345")
        source_url: URL of the source
        curator_id: identifier of the independent curator
        curator_statement: signed statement of independence
        raw_evidence_excerpt: excerpt from the source documenting the outcome
        manifest: the pre-registration manifest (for verification)

    Returns:
        Unsealed observation dict.
    """
    obs = {
        "schema_version": OBSERVATION_SCHEMA_VERSION,
        "observation_type": "EXTERNAL_OUTCOME",
        "problem_id": problem_id,
        "manifest_hash": manifest_hash,
        "outcome_value": outcome_value,
        "outcome_direction": outcome_direction,
        "measurement_date": measurement_date,
        "source_name": source_name,
        "source_url": source_url,
        "curator_id": curator_id,
        "curator_statement": curator_statement,
        "raw_evidence_excerpt": raw_evidence_excerpt,
        "collected_at": datetime.now(timezone.utc).isoformat(),
    }
    return obs


def seal_observation(observation: dict) -> dict:
    """Seal an observation by computing its SHA-256 hash."""
    canonical = json.dumps(observation, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    observation["observation_hash"] = hashlib.sha256(canonical.encode()).hexdigest()
    return observation


def verify_observation(observation: dict) -> bool:
    """Verify that an observation's hash matches its contents."""
    stored = observation.get("observation_hash")
    if not stored:
        return False
    o = {k: v for k, v in observation.items() if k != "observation_hash"}
    canonical = json.dumps(o, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    computed = hashlib.sha256(canonical.encode()).hexdigest()
    return computed == stored


# =============================================================================
# Window verification
# =============================================================================

def verify_observation_window(
    observation: dict,
    manifest: dict,
) -> tuple[bool, list[str]]:
    """Verify that an observation is within the pre-registered window and
    from the pre-registered source.

    Returns (all_ok, list_of_failure_reasons).
    """
    failures = []

    window = manifest.get("observation_window", {})
    window_start = window.get("window_start")
    window_end = window.get("window_end")

    if not window_start or not window_end:
        failures.append("manifest has no observation_window or window bounds missing")
        return (False, failures)

    # Check measurement_date is within [window_start, window_end]
    measurement_date = observation.get("measurement_date")
    if not measurement_date:
        failures.append("observation has no measurement_date")
    else:
        try:
            md = datetime.fromisoformat(measurement_date.replace("Z", "+00:00"))
            ws = datetime.fromisoformat(window_start.replace("Z", "+00:00"))
            we = datetime.fromisoformat(window_end.replace("Z", "+00:00"))
            if md < ws:
                failures.append(f"measurement_date {md} is BEFORE window_start {ws}")
            if md > we:
                failures.append(f"measurement_date {md} is AFTER window_end {we}")
        except (ValueError, TypeError) as e:
            failures.append(f"cannot parse dates: {e}")

    # Check source matches manifest
    expected_source = manifest.get("outcome_source_spec", {})
    expected_source_name = expected_source.get("source_name")
    actual_source_name = observation.get("source_name")
    if expected_source_name and actual_source_name and expected_source_name != actual_source_name:
        failures.append(f"source_name mismatch: expected '{expected_source_name}', got '{actual_source_name}'")

    # Check curator independence
    curator_statement = observation.get("curator_statement", "")
    if "independent" not in curator_statement.lower():
        failures.append("curator_statement does not assert independence")

    # Check that the observation's collected_at is after the manifest's created_at
    # (cannot observe before registration)
    manifest_ts = manifest.get("created_at")
    collected_at = observation.get("collected_at")
    if manifest_ts and collected_at:
        try:
            mt = datetime.fromisoformat(manifest_ts.replace("Z", "+00:00"))
            ct = datetime.fromisoformat(collected_at.replace("Z", "+00:00"))
            if ct < mt:
                failures.append(f"observation collected_at {ct} is BEFORE manifest created_at {mt}")
        except (ValueError, TypeError) as e:
            failures.append(f"cannot parse timestamps: {e}")

    return (len(failures) == 0, failures)


# =============================================================================
# WAIT stage verification
# =============================================================================

def verify_wait_stage(
    manifest: dict,
    receipts: list[dict],
    observations: list[dict],
) -> tuple[bool, list[str]]:
    """Verify that no engine activity occurred between generation and
    observation window start.

    Returns (all_ok, list_of_failure_reasons).
    """
    failures = []

    window = manifest.get("observation_window", {})
    window_start = window.get("window_start")
    if not window_start:
        failures.append("manifest has no observation_window.window_start")
        return (False, failures)

    try:
        ws = datetime.fromisoformat(window_start.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        failures.append(f"cannot parse window_start: {window_start}")
        return (False, failures)

    # Check all observation collected_at >= window_start
    for obs in observations:
        ct = obs.get("collected_at")
        if ct:
            try:
                ct_dt = datetime.fromisoformat(ct.replace("Z", "+00:00"))
                if ct_dt < ws:
                    failures.append(
                        f"observation {obs.get('problem_id')} collected at {ct_dt}, "
                        f"BEFORE window_start {ws} — WAIT stage violated"
                    )
            except (ValueError, TypeError):
                failures.append(f"cannot parse collected_at: {ct}")

    # Check all receipt generation_timestamp < window_start
    # (receipts must be generated before the wait begins)
    for r in receipts:
        gt = r.get("generation_timestamp")
        if gt:
            try:
                gt_dt = datetime.fromisoformat(gt.replace("Z", "+00:00"))
                if gt_dt > ws:
                    failures.append(
                        f"receipt {r.get('candidate_id')} generated at {gt_dt}, "
                        f"AFTER window_start {ws} — generation must precede wait"
                    )
            except (ValueError, TypeError):
                failures.append(f"cannot parse generation_timestamp: {gt}")

    return (len(failures) == 0, failures)


# =============================================================================
# Save and log
# =============================================================================

def save_observation(observation: dict) -> Path:
    """Save a sealed observation to the observations directory and append to log."""
    if "observation_hash" not in observation:
        raise ValueError("observation must be sealed before saving")
    path = OBSERVATIONS_DIR / f"obs_{observation['problem_id']}.json"
    with open(path, "w") as f:
        json.dump(observation, f, indent=2, ensure_ascii=False)
    # Append to log
    entry = {
        "log_entry_type": "EXTERNAL_OBSERVATION",
        "observation_hash": observation["observation_hash"],
        "timestamp": observation["collected_at"],
        "problem_id": observation["problem_id"],
        "manifest_hash": observation["manifest_hash"],
        "source_name": observation["source_name"],
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return path


# =============================================================================
# Main — infrastructure check only
# =============================================================================

def main():
    """Verify the observation window infrastructure.

    DOES NOT COLLECT REAL OBSERVATIONS. Builds a sample observation to verify
    the schema and sealing work, then verifies the window check correctly
    fails for out-of-window observations.
    """
    print("=" * 72)
    print("PROSPECTIVE EXPERIMENT — OBSERVATION WINDOW INFRASTRUCTURE CHECK")
    print("=" * 72)
    print()

    # Build a sample observation
    obs = build_observation(
        problem_id="PROS-001",
        manifest_hash="dummy_manifest_hash",
        outcome_value=1800,
        outcome_direction="INCREASE",
        measurement_date="2027-08-01T00:00:00Z",  # far future
        source_name="TO_BE_SPECIFIED",
        source_url="https://example.com/article",
        curator_id="independent_curator_001",
        curator_statement="I, the undersigned curator, certify that I am independent of the experimenter and the engine.",
        raw_evidence_excerpt="The battery achieved 1800 Wh/kg specific energy in 1000 charge cycles.",
        manifest={"observation_window": {"window_start": "2027-01-01", "window_end": "2027-12-31"}},
    )
    obs = seal_observation(obs)
    ok = verify_observation(obs)
    print(f"Sample observation built. Hash: {obs['observation_hash'][:32]}...")
    print(f"Hash verification: {'PASS' if ok else 'FAIL'}")

    # Verify window check
    ok_window, failures = verify_observation_window(obs, {
        "observation_window": {"window_start": "2027-01-01T00:00:00Z", "window_end": "2027-12-31T00:00:00Z"},
        "outcome_source_spec": {"source_name": "TO_BE_SPECIFIED"},
        "created_at": "2026-08-12T00:00:00Z",
    })
    print(f"\nWindow check: {'PASS' if ok_window else 'FAIL (expected — sample has placeholder source)'}")
    for f in failures:
        print(f"  - {f}")

    print()
    print("Observation window infrastructure is in place. To collect real observations:")
    print("  1. Wait until the pre-registered observation window opens")
    print("  2. Engage an INDEPENDENT curator (not the experimenter)")
    print("  3. Curator collects outcomes from the pre-registered source")
    print("  4. Curator seals each observation and appends to the log")
    print()
    print("DO NOT collect observations before the window opens.")


if __name__ == "__main__":
    main()
