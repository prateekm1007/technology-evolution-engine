#!/usr/bin/env python3
"""zai_response_schema_diagnostic.py — Capture the actual z-ai CLI response schema.

NON-SCIENTIFIC DIAGNOSTIC (audit finding round 5 prerequisite):
    The Round 5 audit accepted that the z-ai CLI response includes 'model'
    but not 'provider', but noted: "the audit evidence shown here does not
    independently demonstrate an actual captured production CLI response."

    This script captures the actual CLI response and records:
    - raw response (JSON)
    - SHA-256 of the raw response
    - timestamp
    - CLI version (z-ai --version)
    - fields present
    - fields absent (from the standard OpenAI-compatible schema)

    This establishes exactly what the installed CLI emits WITHOUT touching
    DXP-005 or any scientific experiment. It is a provider diagnostic only.

Usage:
    python3 scripts/zai_response_schema_diagnostic.py
    Output: reports/diagnostics/zai_response_schema.json
"""
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUTPUT = REPO / "reports" / "diagnostics" / "zai_response_schema.json"

# The standard OpenAI-compatible response schema fields we check for
EXPECTED_FIELDS = [
    "id", "object", "created", "model", "choices", "usage",
    "provider",  # OpenRouter adds this; z-ai CLI may not
    "system_fingerprint", "service_tier",
]


def get_cli_version():
    """Get the z-ai CLI version."""
    try:
        result = subprocess.run(
            ["z-ai", "--version"], capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return f"exit {result.returncode}: {result.stderr.strip()[:200]}"
    except Exception as e:
        return f"ERROR: {type(e).__name__}: {e}"


def capture_response():
    """Capture an actual z-ai CLI response."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        args = ["z-ai", "chat", "--prompt", "Reply with exactly: OK", "-o", tmp_path]
        proc = subprocess.run(args, capture_output=True, text=True, timeout=30)

        if proc.returncode != 0:
            return None, f"CLI exit {proc.returncode}: {proc.stderr[:500]}"

        with open(tmp_path) as f:
            raw_text = f.read()

        try:
            data = json.loads(raw_text)
        except json.JSONDecodeError as e:
            return raw_text, f"JSON decode error: {e}"

        return data, None
    except subprocess.TimeoutExpired:
        return None, "timeout after 30s"
    except Exception as e:
        return None, f"ERROR: {type(e).__name__}: {e}"
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def main():
    print("ZAI Response Schema Diagnostic")
    print("=" * 60)
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print()

    # Get CLI version
    cli_version = get_cli_version()
    print(f"CLI version: {cli_version}")

    # Capture response
    print("Capturing response from z-ai CLI...")
    response, error = capture_response()

    if error:
        print(f"ERROR: Could not capture response: {error}")
        diagnostic = {
            "diagnostic_type": "ZAI_RESPONSE_SCHEMA_DIAGNOSTIC",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "cli_version": cli_version,
            "capture_error": error,
            "raw_response": None,
            "raw_response_sha256": None,
            "fields_present": [],
            "fields_absent": EXPECTED_FIELDS,
            "model_field_present": False,
            "provider_field_present": False,
            "scientific_experiment_executed": False,
            "note": "Could not capture CLI response. This may be due to API rate limiting or CLI unavailability.",
        }
    else:
        raw_text = json.dumps(response, sort_keys=True) if isinstance(response, dict) else str(response)
        raw_sha = hashlib.sha256(raw_text.encode()).hexdigest()

        fields_present = [f for f in EXPECTED_FIELDS if f in response] if isinstance(response, dict) else []
        fields_absent = [f for f in EXPECTED_FIELDS if f not in response] if isinstance(response, dict) else EXPECTED_FIELDS

        print(f"Response captured. SHA-256: {raw_sha[:16]}...")
        print(f"Fields present: {fields_present}")
        print(f"Fields absent: {fields_absent}")
        print(f"model field present: {'model' in (response or {})}")
        print(f"provider field present: {'provider' in (response or {})}")

        if isinstance(response, dict) and "model" in response:
            print(f"model value: {response['model']}")
        if isinstance(response, dict) and "provider" in response:
            print(f"provider value: {response['provider']}")

        diagnostic = {
            "diagnostic_type": "ZAI_RESPONSE_SCHEMA_DIAGNOSTIC",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "cli_version": cli_version,
            "capture_error": None,
            "raw_response": response,
            "raw_response_sha256": raw_sha,
            "fields_present": fields_present,
            "fields_absent": fields_absent,
            "model_field_present": "model" in (response or {}),
            "provider_field_present": "provider" in (response or {}),
            "model_value": response.get("model") if isinstance(response, dict) else None,
            "provider_value": response.get("provider") if isinstance(response, dict) else None,
            "scientific_experiment_executed": False,
            "note": "Non-scientific diagnostic. Captures actual CLI response schema for P46 verification purposes. Does NOT execute DXP-005 or any scientific experiment.",
        }

    # Write output
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(diagnostic, indent=2, default=str))
    print(f"\nDiagnostic written to {OUTPUT}")
    print(f"\nScientific experiment executed: {diagnostic['scientific_experiment_executed']}")


if __name__ == "__main__":
    main()
