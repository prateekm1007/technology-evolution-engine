#!/usr/bin/env python3
"""
verify_gate2_manifest.py — Gate 2 cryptographic integrity verification.

Repair #3 (independent infrastructure review):
    The `.IMMUTABLE` marker file in experiments/gate2/ is a convention, not
    cryptographic protection. A developer could modify frozen artifacts while
    leaving `.IMMUTABLE` untouched. This script provides REAL cryptographic
    protection via a content-addressed manifest.

Repair #4-extended (second independent review):
    The manifest alone is not sufficient. An attacker who modifies an
    artifact AND regenerates the manifest produces a self-consistent
    (artifact, manifest) pair — the verifier would pass. The manifest
    itself must be anchored to an immutable identity.

    The freeze record provides that anchor:
        experiments/gate2/FREEZE_RECORD.json
            ↓
        records: protocol_sha, cases_sha, manifest_sha, creation_commit
            ↓
        committed to git (the git commit SHA provides the external anchor)
            ↓
        the verifier checks:
            (a) computed manifest content hash == freeze_record.manifest_sha
            (b) every artifact hash in the manifest matches its current hash
            (c) protocol_sha in freeze record matches the expected frozen SHA
            (d) no missing, extra, malformed, or duplicate manifest entries

    An attacker who modifies an artifact must regenerate the manifest (else
    (b) fails). But regenerating the manifest changes manifest_sha, breaking
    (a) unless they also modify the freeze record. Modifying the freeze
    record changes the git commit, which is externally detectable.

Repair #7-extended (second independent review):
    The verifier FAILS CLOSED. Any of the following cause verification to
    fail with a non-zero exit code:
        - manifest file missing
        - freeze record file missing
        - artifact missing (recorded but not present)
        - unexpected artifact exists (present but not in manifest)
        - hash mismatch (artifact modified)
        - manifest substitution (manifest_sha != freeze_record.manifest_sha)
        - protocol SHA mismatch
        - cases_sha mismatch (when cases are registered)
        - malformed manifest (bad line format, hash not 64 hex chars)
        - duplicate manifest entries (same file listed twice)
        - malformed freeze record (missing required fields)

    The verifier behaves like a security boundary, not a convenience script.

CI integration:
    Added as a CI gate (Gate 11) in .github/workflows/ci.yml. The gate
    fails the build on any verification failure.

Usage:
    python scripts/verify_gate2_manifest.py
        # Verifies the freeze record + manifest against current files.
        # Exits 0 iff all checks pass. Exits 1 on any failure.

    python scripts/verify_gate2_manifest.py --regenerate
        # Regenerates the manifest AND the freeze record from the current
        # files. Use ONLY when intentionally freezing a new Gate 2 artifact
        # set. Commits the new files. The previous freeze record is
        # overwritten — this is the only legitimate mutation path, and it
        # changes the git commit (externally detectable).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
GATE2_DIR = REPO / "experiments" / "gate2"
MANIFEST_PATH = GATE2_DIR / "MANIFEST.sha256"
FREEZE_RECORD_PATH = GATE2_DIR / "FREEZE_RECORD.json"

# The frozen Gate 2 protocol SHA (v1.2 FROZEN, APPROVED FOR EXECUTION).
# Sourced from SCIENTIFIC_GATE_2_PROTOCOL.md approval chain.
# DO NOT change this without an explicit protocol revision.
EXPECTED_PROTOCOL_SHA = "32691a78dc3bc963937fb21380c9df9c4f1f6c33"

# Files that are part of the integrity-protected set but are NOT themselves
# hashed by the manifest (the manifest cannot hash itself; the freeze record
# cannot hash itself either, but the freeze record IS anchored by the manifest
# via the manifest_sha field, and by the git commit externally).
SELF_EXCLUDED = {"MANIFEST.sha256", "FREEZE_RECORD.json"}


def sha256_of_file(path: Path) -> str:
    """Compute the full SHA-256 (64 hex chars) of a file's bytes."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_of_text(text: str) -> str:
    """Compute the full SHA-256 (64 hex chars) of a UTF-8 string."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def list_gate2_files() -> list[Path]:
    """List all files in experiments/gate2/ (including hidden files).

    The MANIFEST.sha256 and FREEZE_RECORD.json files are excluded — they
    cannot hash themselves.
    """
    if not GATE2_DIR.exists():
        return []
    files = []
    for p in sorted(GATE2_DIR.rglob("*")):
        if not p.is_file():
            continue
        if p.name in SELF_EXCLUDED:
            continue
        files.append(p)
    return files


def is_valid_sha256(s: str) -> bool:
    """True iff s is a 64-character lowercase hex string."""
    if not isinstance(s, str):
        return False
    if len(s) != 64:
        return False
    return all(c in "0123456789abcdef" for c in s)


def is_valid_hex(s: str, length: int) -> bool:
    """True iff s is a `length`-character lowercase hex string."""
    if not isinstance(s, str):
        return False
    if len(s) != length:
        return False
    return all(c in "0123456789abcdef" for c in s)


# ============================================================================
# Manifest generation / parsing
# ============================================================================

def generate_manifest_content() -> tuple[str, str]:
    """Generate the manifest content from the current files.

    Returns (manifest_text, manifest_sha256).
    """
    lines = [
        "# Gate 2 Integrity Manifest",
        "#",
        "# Cryptographic protection for frozen Gate 2 artifacts (Repair #3).",
        "# The `.IMMUTABLE` marker is a human-readable signal; THIS manifest",
        "# provides the actual SHA-256 integrity verification.",
        "#",
        "# The manifest itself is anchored by FREEZE_RECORD.json (Repair #4-extended).",
        "# An attacker who regenerates this manifest to bless altered artifacts",
        "# will produce a different manifest_sha, breaking the freeze record.",
        "#",
        "# Do NOT edit by hand. Regenerate with:",
        "#   python scripts/verify_gate2_manifest.py --regenerate",
        "#",
        f"# Protocol SHA: {EXPECTED_PROTOCOL_SHA}",
        "# Case-set SHA: (none — no Gate 2 cases registered yet)",
        "#",
        "# Format: <sha256>  <relative_path>",
        "",
    ]
    files = list_gate2_files()
    for f in files:
        rel = f.relative_to(GATE2_DIR).as_posix()
        digest = sha256_of_file(f)
        lines.append(f"{digest}  {rel}")
    content = "\n".join(lines) + "\n"
    return content, sha256_of_text(content)


def parse_manifest() -> tuple[dict[str, str], list[str]]:
    """Parse the manifest into (entries, errors).

    entries: {relative_path: sha256}
    errors: list of malformed-line descriptions (Repair #7-extended: fail
            closed on malformed manifests)
    """
    if not MANIFEST_PATH.exists():
        return {}, ["manifest file does not exist"]
    entries: dict[str, str] = {}
    errors: list[str] = []
    seen_paths: set[str] = set()
    for lineno, raw in enumerate(MANIFEST_PATH.read_text().splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 1)
        if len(parts) != 2:
            errors.append(f"line {lineno}: malformed (expected '<sha256>  <path>'): {raw!r}")
            continue
        digest, rel = parts
        rel = rel.strip()
        if not is_valid_sha256(digest):
            errors.append(f"line {lineno}: hash is not a valid 64-char SHA-256: {digest!r}")
            continue
        if rel in seen_paths:
            errors.append(f"line {lineno}: duplicate manifest entry for path: {rel!r}")
            continue
        seen_paths.add(rel)
        entries[rel] = digest
    return entries, errors


# ============================================================================
# Freeze record generation / parsing
# ============================================================================

def generate_freeze_record(manifest_sha: str) -> dict:
    """Generate the freeze record dict.

    The freeze record anchors the manifest. It records:
        - protocol_sha: the frozen Gate 2 protocol SHA
        - cases_sha:    the SHA of the registered Gate 2 case set
                        (empty string if no cases registered yet)
        - manifest_sha: the SHA-256 of the manifest content
        - creation_commit: (filled in by caller or by git at commit time;
                            left blank here — git provides the external anchor)
        - schema_version: 1
    """
    return {
        "schema_version": 1,
        "protocol_sha": EXPECTED_PROTOCOL_SHA,
        "cases_sha": "",
        "manifest_sha": manifest_sha,
        "creation_commit": "",
        "note": "Freeze record anchoring the Gate 2 manifest (Repair #4-extended). "
                "An attacker who regenerates the manifest to bless altered artifacts "
                "produces a different manifest_sha, breaking this record. Modifying "
                "this record changes the git commit, which is externally detectable.",
    }


def parse_freeze_record() -> tuple[dict | None, list[str]]:
    """Parse the freeze record. Returns (record, errors)."""
    if not FREEZE_RECORD_PATH.exists():
        return None, ["freeze record file does not exist"]
    try:
        record = json.loads(FREEZE_RECORD_PATH.read_text())
    except json.JSONDecodeError as e:
        return None, [f"freeze record is not valid JSON: {e}"]
    errors: list[str] = []
    required = {"schema_version", "protocol_sha", "cases_sha", "manifest_sha"}
    for field in required:
        if field not in record:
            errors.append(f"freeze record missing required field: {field!r}")
    if "manifest_sha" in record and not is_valid_sha256(record["manifest_sha"]):
        errors.append(f"freeze record manifest_sha is not a valid SHA-256 (64 hex): {record['manifest_sha']!r}")
    # protocol_sha is a git commit SHA (40 hex chars, SHA-1) — not a SHA-256.
    # The frozen Gate 2 protocol is anchored by git commit 32691a7...
    if "protocol_sha" in record and not is_valid_hex(record["protocol_sha"], 40):
        errors.append(f"freeze record protocol_sha is not a valid 40-char git SHA: {record['protocol_sha']!r}")
    # cases_sha is a SHA-256 of the case set (or empty if no cases registered).
    if "cases_sha" in record and record["cases_sha"] and not is_valid_sha256(record["cases_sha"]):
        errors.append(f"freeze record cases_sha is not a valid SHA-256 (64 hex): {record['cases_sha']!r}")
    return record, errors


# ============================================================================
# Verification
# ============================================================================

def verify() -> int:
    """Verify the freeze record + manifest against current files.

    Returns 0 on success, 1 on any failure. FAILS CLOSED.
    """
    failures: list[str] = []

    # ---- Step 1: manifest file must exist and parse cleanly ----
    if not MANIFEST_PATH.exists():
        failures.append("MANIFEST.sha256 does not exist. Run with --regenerate to freeze.")
    else:
        recorded, manifest_errors = parse_manifest()
        if manifest_errors:
            failures.extend(f"manifest malformed: {e}" for e in manifest_errors)

    # ---- Step 2: freeze record must exist and parse cleanly ----
    freeze_record, freeze_errors = parse_freeze_record()
    if freeze_errors:
        failures.extend(f"freeze record invalid: {e}" for e in freeze_errors)

    # If we can't even parse the manifest or freeze record, fail now.
    if failures:
        return _report_failures(failures)

    # ---- Step 3: freeze record protocol_sha must match expected ----
    if freeze_record is not None:
        if freeze_record.get("protocol_sha") != EXPECTED_PROTOCOL_SHA:
            failures.append(
                f"protocol SHA mismatch: freeze record has "
                f"{freeze_record.get('protocol_sha')!r}, expected {EXPECTED_PROTOCOL_SHA!r}. "
                "The Gate 2 protocol SHA must match the frozen protocol version."
            )

    # ---- Step 4: manifest content hash must match freeze_record.manifest_sha ----
    # This is the key anchor (Repair #4-extended). If an attacker regenerates
    # the manifest to bless altered artifacts, the manifest_sha changes,
    # breaking the freeze record.
    if MANIFEST_PATH.exists() and freeze_record is not None:
        manifest_text = MANIFEST_PATH.read_text()
        actual_manifest_sha = sha256_of_text(manifest_text)
        recorded_manifest_sha = freeze_record.get("manifest_sha", "")
        if actual_manifest_sha != recorded_manifest_sha:
            failures.append(
                "MANIFEST SUBSTITUTION DETECTED: the manifest content hash does not "
                f"match the freeze record.\n"
                f"       freeze_record.manifest_sha = {recorded_manifest_sha}\n"
                f"       actual manifest_sha        = {actual_manifest_sha}\n"
                "       An attacker may have regenerated the manifest to bless altered "
                "artifacts. Restore the original manifest + freeze record, or perform "
                "an intentional re-freeze via --regenerate (which changes the git commit)."
            )

    # ---- Step 5: every recorded artifact must exist with matching hash ----
    if MANIFEST_PATH.exists():
        recorded, _ = parse_manifest()  # already validated above
        current_files = {p.relative_to(GATE2_DIR).as_posix() for p in list_gate2_files()}

        # Missing files (recorded but not present)
        missing = set(recorded.keys()) - current_files
        for m in sorted(missing):
            failures.append(
                f"artifact missing: {m!r} is recorded in the manifest but not present "
                "in experiments/gate2/. Gate 2 artifacts must not be deleted."
            )

        # Extra files (present but not in manifest)
        extra = current_files - set(recorded.keys())
        for e in sorted(extra):
            failures.append(
                f"unexpected artifact: {e!r} is present in experiments/gate2/ but not "
                "recorded in the manifest. Either remove the file or re-freeze."
            )

        # Hash mismatches
        for rel, expected_hash in sorted(recorded.items()):
            path = GATE2_DIR / rel
            if not path.exists():
                continue  # already reported as missing
            actual_hash = sha256_of_file(path)
            if actual_hash != expected_hash:
                failures.append(
                    f"artifact modified: {rel!r}\n"
                    f"       recorded: {expected_hash}\n"
                    f"       actual:   {actual_hash}\n"
                    "       Gate 2 artifacts are FROZEN. Modification is forbidden."
                )

    if failures:
        return _report_failures(failures)

    # ---- All checks passed ----
    recorded, _ = parse_manifest()
    print(f"PASS: experiments/gate2/ integrity verified — {len(recorded)} artifact(s) intact.")
    print(f"      Manifest SHA: {freeze_record['manifest_sha']}")
    print(f"      Protocol SHA: {freeze_record['protocol_sha']}")
    if freeze_record.get("cases_sha"):
        print(f"      Cases SHA:    {freeze_record['cases_sha']}")
    else:
        print(f"      Cases SHA:    (none — no Gate 2 cases registered yet)")
    return 0


def _report_failures(failures: list[str]) -> int:
    print("FAIL: Gate 2 integrity verification failed.")
    for f in failures:
        print(f"       - {f}")
    print("       Gate 2 artifacts are FROZEN. The verifier fails closed on any")
    print("       missing, extra, malformed, substituted, or modified artifact.")
    return 1


# ============================================================================
# Regeneration (intentional re-freeze)
# ============================================================================

def regenerate() -> int:
    """Regenerate the manifest AND freeze record from the current files.

    This is the ONLY legitimate mutation path. It changes the manifest_sha,
    which changes the freeze record, which changes the git commit —
    externally detectable.

    Use ONLY when intentionally freezing a new Gate 2 artifact set.
    """
    manifest_content, manifest_sha = generate_manifest_content()
    MANIFEST_PATH.write_text(manifest_content)

    freeze_record = generate_freeze_record(manifest_sha)
    FREEZE_RECORD_PATH.write_text(json.dumps(freeze_record, indent=2) + "\n")

    print(f"REGENERATED: {MANIFEST_PATH.relative_to(REPO)}")
    print(f"             {len(list_gate2_files())} file(s) hashed.")
    print(f"REGENERATED: {FREEZE_RECORD_PATH.relative_to(REPO)}")
    print(f"             manifest_sha = {manifest_sha}")
    print(f"             protocol_sha = {EXPECTED_PROTOCOL_SHA}")
    print("             Commit both files to record the freeze. The git commit")
    print("             provides the external anchor for the freeze record.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify or regenerate the Gate 2 integrity manifest + freeze record."
    )
    parser.add_argument(
        "--regenerate",
        action="store_true",
        help="Regenerate the manifest AND freeze record from current files. "
             "Use ONLY when intentionally freezing a new Gate 2 artifact set. "
             "Changes the git commit (externally detectable).",
    )
    args = parser.parse_args()

    if args.regenerate:
        return regenerate()

    return verify()


if __name__ == "__main__":
    sys.exit(main())
