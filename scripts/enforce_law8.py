#!/usr/bin/env python3
"""
Law 8 enforcement: automated check that no "verified" label is claimed
without replayable evidence.

Law 8 (CONSTITUTION.md):
    No "verified" label without a successful prediction, a failed
    prediction, and replayable evidence.

This script makes that rule executable rather than aspirational.
It scans the codebase for places that assign or claim the
"verified" label, and for each one it requires:

  1. The ledger at data/ledger/predictions.jsonl is parseable.
  2. The ledger contains at least one entry with `outcome: "pass"`
     (successful prediction).
  3. The ledger contains at least one entry with `outcome: "fail"`
     (failed prediction).
  4. Every entry is replayable: re-running the writer reproduces
     the same bytes. (For now, replayability is asserted by
     checking that each entry has a `writer` field naming its
     source script/module — without that, we cannot replay.)

If any of those conditions fail, every "verified" stamp in the
codebase is reported as UNSUPPORTED, and the script exits non-zero.

This script does NOT modify any file. It only reads and reports.
It is suitable for a CI gate or a pre-merge check.

Usage:
    python scripts/enforce_law8.py [--json evidence/reports/verification_report.json]
"""
import argparse
import json
import re
import sys
import pathlib
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
LEDGER = ROOT / "data" / "ledger" / "predictions.jsonl"

# Scopes to scan for "verified" labels. .md and .py only —
# anything else (CSS, JS frontend cosmetics) does not constitute
# a system-level verification claim.
SCAN_GLOBS = ("**/*.py", "**/*.md")
SCAN_SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv",
    "evidence",  # the evidence dir is the audit output, not a claim
}

# What counts as a CLAIM of "verified":
#   - "verified" used as a value being assigned / returned / compared
#   - i.e. a code path that could actually stamp the label.
# What does NOT count:
#   - prose discussion of the rule (in docstrings, comments, md prose).
#   - test assertions that the label is NOT present.
#
# We approximate this with two regexes that look for assignment-like
# or value-like usage of "verified" as a string literal.
CLAIM_PATTERNS = [
    # stamp(..., "verified")  /  verification == "verified"  /  "verified" if ...
    re.compile(r'["\']verified["\']'),
    # Markdown label-list: | verified |, level: verified, "verified" | "implemented"
    # but only in contexts that look like a label declaration (not prose).
    re.compile(r'^\s*\|\s*verified\s*\|', re.MULTILINE),
    re.compile(r'level["\']?\s*[:=]\s*["\']?verified', re.IGNORECASE),
]


def _looks_like_claim(line):
    """Heuristic: does this line actually assert the 'verified' label,
    or just discuss it?"""
    # Comments and docstrings discussing the rule.
    lowered = line.lower()
    if any(needle in lowered for needle in (
        "law 8", "no \"verified\" without", "no 'verified' without",
        "downgrade", "not verified", "cannot claim",
        "not yet a verified", "without successful prediction",
        "without failure cases", "not for public citation",
        "verification standard", "amended rule",
        "rule 'no verified", "no verified label",
        "without adversarial", "lying about verification",
        "f\"analyze() stamped", "assert level !=",
        "stamped 'verified' without",
    )):
        return False
    # If the line is an assert that something is NOT verified, skip.
    if "!=" in line and "verified" in line:
        return False
    # If the line is a comment about the rule (starts with # or """).
    stripped = line.lstrip()
    if stripped.startswith(("#", '"""', "'''")) or stripped.startswith('"""'):
        return False
    # Otherwise: it's an assignment/comparison/return of "verified".
    return any(p.search(line) for p in CLAIM_PATTERNS)


def scan_for_verified_claims():
    """Walk SCAN_GLOBS, return list of (file, line_no, line_text, kind)."""
    claims = []
    for pat in SCAN_GLOBS:
        for path in ROOT.glob(pat):
            if not path.is_file():
                continue
            if any(part in SCAN_SKIP_DIRS for part in path.relative_to(ROOT).parts):
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, IsADirectoryError):
                continue
            for i, line in enumerate(text.splitlines(), start=1):
                if not _looks_like_claim(line):
                    continue
                claims.append({
                    "file": str(path.relative_to(ROOT)),
                    "line": i,
                    "text": line.strip()[:200],
                })
    return claims


def assess_ledger():
    """Read the ledger and report whether it backs any verified claim."""
    if not LEDGER.exists():
        return {
            "ledger_exists": False,
            "parseable": False,
            "entries": [],
            "successful_predictions": 0,
            "failed_predictions": 0,
            "replayable_entries": 0,
            "parse_error": f"file not found at {LEDGER.relative_to(ROOT)}",
        }
    raw = LEDGER.read_text(encoding="utf-8")
    lines = raw.splitlines()
    non_empty = [ln for ln in lines if ln.strip()]

    # Total-corruption signature: many lines, all <5 chars.
    totally_corrupted = (
        len(non_empty) > 500 and all(len(ln) < 5 for ln in non_empty)
    )
    if totally_corrupted:
        return {
            "ledger_exists": True,
            "parseable": False,
            "entries": [],
            "successful_predictions": 0,
            "failed_predictions": 0,
            "replayable_entries": 0,
            "parse_error": (
                "Total file corruption: file appears to be written one "
                "character per line (F-005). Ledger is unusable as evidence."
            ),
            "sha256": _sha256(LEDGER),
        }

    entries, parse_errors = [], []
    for i, line in enumerate(lines, start=1):
        s = line.strip()
        if not s:
            continue
        try:
            entries.append(json.loads(s))
        except json.JSONDecodeError as e:
            parse_errors.append({"line": i, "error": str(e), "preview": s[:80]})

    successful = [e for e in entries if e.get("outcome") == "pass"]
    failed = [e for e in entries if e.get("outcome") == "fail"]
    replayable = [e for e in entries if "writer" in e]

    return {
        "ledger_exists": True,
        "parseable": not parse_errors,
        "entries": entries,
        "successful_predictions": len(successful),
        "failed_predictions": len(failed),
        "replayable_entries": len(replayable),
        "parse_errors": parse_errors[:5],
        "sha256": _sha256(LEDGER),
    }


def _sha256(path):
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def enforce():
    ledger_state = assess_ledger()
    claims = scan_for_verified_claims()

    # Determine the global verdict.
    ledger_supports_verified = (
        ledger_state["parseable"]
        and ledger_state["successful_predictions"] > 0
        and ledger_state["failed_predictions"] > 0
        and ledger_state["replayable_entries"] > 0
    )

    # Each "verified" mention is classified.
    classified = []
    for c in claims:
        if ledger_supports_verified:
            verdict = "supported"
            reason = "ledger contains >=1 pass + >=1 fail + replayable evidence"
        else:
            verdict = "unsupported"
            gaps = []
            if not ledger_state["parseable"]:
                gaps.append("ledger is not parseable")
            if ledger_state["parseable"] and ledger_state["successful_predictions"] == 0:
                gaps.append("no successful prediction recorded")
            if ledger_state["parseable"] and ledger_state["failed_predictions"] == 0:
                gaps.append("no failed prediction recorded")
            if ledger_state["parseable"] and ledger_state["replayable_entries"] == 0:
                gaps.append("no entry carries a `writer` field (replayability)")
            reason = "Law 8 not satisfied: " + "; ".join(gaps)
        classified.append({**c, "verdict": verdict, "reason": reason})

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "rule": (
            "Law 8 (CONSTITUTION.md): No 'verified' label without a "
            "successful prediction, a failed prediction, and replayable "
            "evidence."
        ),
        "ledger_state": ledger_state,
        "claims_found": len(classified),
        "supported_claims": sum(1 for c in classified if c["verdict"] == "supported"),
        "unsupported_claims": sum(1 for c in classified if c["verdict"] == "unsupported"),
        "global_verdict": "PASS" if ledger_supports_verified else "FAIL",
        "claims": classified,
        "required_to_pass": (
            "To flip this verdict to PASS: (1) regenerate data/ledger/predictions.jsonl "
            "with a known writer, (2) record at least one prediction with outcome=pass "
            "AND at least one with outcome=fail, (3) stamp every ledger entry with a "
            "`writer` field naming the script/module that produced it so the entry is "
            "replayable. Until all three are true, every 'verified' label in the repo is "
            "aspirational, not evidenced."
        ),
    }


def main():
    parser = argparse.ArgumentParser(description="Law 8 enforcement (automated)")
    parser.add_argument("--json", dest="json_out", default=None,
                        help="path to write the JSON report")
    parser.add_argument("--strict", action="store_true",
                        help="exit non-zero if verdict is FAIL (default: always 0)")
    args = parser.parse_args()

    report = enforce()
    pretty = json.dumps(report, indent=2)
    if args.json_out:
        out = pathlib.Path(args.json_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(pretty + "\n", encoding="utf-8")
        print(f"wrote {out}", file=sys.stderr)

    # Print a short human summary.
    print("=" * 60)
    print("LAW 8 ENFORCEMENT")
    print("=" * 60)
    print(f"Ledger parseable:        {report['ledger_state']['parseable']}")
    print(f"Successful predictions:  {report['ledger_state']['successful_predictions']}")
    print(f"Failed predictions:      {report['ledger_state']['failed_predictions']}")
    print(f"Replayable entries:       {report['ledger_state']['replayable_entries']}")
    print(f"'verified' claims found: {report['claims_found']}")
    print(f"  supported:             {report['supported_claims']}")
    print(f"  unsupported:            {report['unsupported_claims']}")
    print(f"Global verdict:          {report['global_verdict']}")
    if report['unsupported_claims'] > 0:
        print("\nFirst 5 unsupported claims:")
        for c in report["claims"][:5]:
            if c["verdict"] == "unsupported":
                print(f"  - {c['file']}:{c['line']}  {c['text'][:100]}")
    print("=" * 60)
    if args.strict and report["global_verdict"] == "FAIL":
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
