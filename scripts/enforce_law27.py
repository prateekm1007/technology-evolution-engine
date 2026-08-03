#!/usr/bin/env python3
"""
enforce_law27.py — Honesty Loop forbidden-language scanner.

Per Law 27 (BLUEPRINT_CONSTITUTION.md): "The Blueprint shall not
assign numerical certainty to claims that lack repeated
experimental validation."

Per Law 28: certain phrases are forbidden in Blueprint outputs.
Per Law 29: typed status enums are required.

This scanner reads Markdown / JSON / TypeScript / Python files
in the repository and detects forbidden language patterns.

Modes:
    default              Scan user-facing Blueprint artifacts
                         (.md, .json in download/, evidence/,
                          examples/, milestones/). Exit 1 on
                          any violation. Used by CI Gate 4.
    --full               Scan the entire repo (.md, .json, .ts,
                         .tsx, .py) including source code.
                         Informational; exits 0 unless --strict.
    --strict             Exit 1 on any violation, in any mode.
    PATH                 Scan a specific file or directory.

Usage:
    python scripts/enforce_law27.py            # CI gate (Blueprint artifacts only)
    python scripts/enforce_law27.py --full     # honest audit of entire repo
    python scripts/enforce_law27.py --full --strict  # zero-tolerance audit
    python scripts/enforce_law27.py PATH       # scan a specific file/dir

Exit codes:
    0 = no violations detected (or informational mode without --strict)
    1 = violations detected (in default or --strict mode)

Note on historical code: pre-Law-27 source files
(loops/, invention_compiler/, product/, evidence/experiments/,
milestones/) use `confidence=0.55` as a Python parameter name
in Hypothesis objects. These are internal API contracts, not
user-facing claims. They are grandfathered in default mode and
slated for migration to typed status objects in a future AEP
work item. --full mode reports them honestly without blocking.
"""

import argparse
import json
import pathlib
import re
import sys
from dataclasses import dataclass
from typing import Iterable

ROOT = pathlib.Path(__file__).resolve().parents[1]

# --------------------------------------------------------------------------
# Allowlist — paths where forbidden language is permitted (it is being
# quoted to define what is forbidden, not used as a claim).
# --------------------------------------------------------------------------
ALLOWLIST_PATHS = [
    # Documents that define the forbidden language
    "HONESTY_LOOP.md",
    "BLUEPRINT_CONSTITUTION.md",
    "EVIDENCE_LINEAGE_ENGINE.md",
    "MASS_STACKUP_ENGINE.md",
    "INTERFACE_CONTROL_ENGINE.md",
    "PROCUREMENT_ENGINE.md",
    "VALIDATION_LEVEL_ENGINE.md",
    "REQUIREMENT_RECONCILIATION_ENGINE.md",
    "RETRACTION_REGISTRY_ENGINE.md",
    "TEST_REGISTRY_ENGINE.md",
    "ECONOMIC_REALITY_ENGINE.md",
    "THERMAL_ENVELOPE_ENGINE.md",
    "ENGINEERING_PRINCIPLES.md",
    "CODER_DIRECTIONS.md",
    "AEP_PROTOCOL.md",
    "CONSTITUTION.md",
    "ANTI_ENTROPY.md",
    "HANDOFF.md",
    # Failure records quote the patterns they report on
    "FAILURES.md",
    "FAILURE_LIBRARY.md",
    # The scanner's own tests must contain the patterns to verify detection
    "tests/test_honesty_loop.py",

    # ----------------------------------------------------------------
    # Historical records (pre-Law-27)
    # ----------------------------------------------------------------
    # Per CONSTITUTION.md Law 7 (Historical Permanence): "No benchmark,
    # prediction, assumption, failure, or outcome may be silently
    # altered." The following files are HISTORICAL RECORDS produced
    # before Law 27 was enacted. They quote the forbidden patterns
    # because that is what the system produced at the time.
    # Editing them to remove the patterns would violate Law 7.
    #
    # These are grandfathered. The scanner continues to enforce Law 27
    # on all NEW artifacts. The next AEP work item (Gate 1
    # Comprehension) for the Honesty Loop will decide whether to
    # re-publish these records under the new typed status vocabulary
    # (which would create BP1_RECORD_v2.md, not edit BP1_RECORD.md).
    "BP0_RECORD.md",
    "BP1_RECORD.md",
    "INTERFACES.md",
    "EXAMPLE_BLUEPRINT_001.md",  # produced before Law 27; grandfathered
    "milestones/milestone_001/README.md",
    "milestones/milestone_001/spec.json",
    "milestones/milestone_002/spec.json",
    "milestones/milestone_002/README.md",
    # Historical audit/benchmark reports (pre-Law-27). These contain
    # "confidence" fields in their JSON schema. Migrating them to
    # typed status objects is a separate AEP work item.
    "evidence/reports/",
]

# Directories considered "user-facing Blueprint artifacts" — scanned
# in default mode. These are the paths where new forbidden language
# would constitute a real Law 27 violation in a shipped artifact.
BLUEPRINT_ARTIFACT_DIRS = [
    "download",
    "evidence",
    "examples",
    "milestones",
    "agent",
    "belief",
    "hypothesis",
    "layer_status",
    "logs",
    "workstreams",
]

# File extensions to scan in default mode (Markdown + JSON artifacts)
DEFAULT_SCAN_EXTENSIONS = {".md", ".json"}

# Additional extensions in --full mode (source code)
FULL_SCAN_EXTENSIONS = {".md", ".json", ".ts", ".tsx", ".py"}

# --------------------------------------------------------------------------
# Forbidden patterns. Each has:
#   - id: short identifier
#   - regex: compiled pattern
#   - law: which law it violates
#   - replacement: the required replacement (informational)
# --------------------------------------------------------------------------

@dataclass
class ForbiddenPattern:
    id: str
    description: str
    regex: re.Pattern
    law: str
    replacement: str


PATTERNS: list[ForbiddenPattern] = [
    ForbiddenPattern(
        id="A1",
        description="'complete engineering blueprint' / 'complete blueprint' phrasing",
        regex=re.compile(r"\bcomplete\s+(?:engineering\s+)?blueprint\b", re.IGNORECASE),
        law="Law 28a",
        replacement="engineering concept package | decision package | evaluation package | prototype package | production package",
    ),
    ForbiddenPattern(
        id="B1",
        description="numerical confidence percentage (e.g. 'confidence: 58%', JSON '\"confidence\": \"58%\"', or Python 'confidence=0.58')",
        regex=re.compile(
            r"\bconfidence\"?\s*[:=]\s*\"?\s*\d+(?:\.\d+)?\s*%\"?", re.IGNORECASE
        ),
        law="Law 27 / Law 28c",
        replacement="validation_level: L{n} (Law 29b)",
    ),
    ForbiddenPattern(
        id="B2",
        description="numerical confidence decimal (e.g. 'confidence: 0.58', JSON '\"confidence\": 0.58', or Python 'confidence=0.58')",
        regex=re.compile(
            r"\bconfidence\"?\s*[:=]\s*\"?\s*0\.\d+\s*\"?", re.IGNORECASE
        ),
        law="Law 27 / Law 28c",
        replacement="validation_level: L{n} (Law 29b)",
    ),
    ForbiddenPattern(
        id="B3",
        description="'overall confidence' as a number",
        regex=re.compile(
            r"\boverall\s+confidence\"?\s*[:=]\s*\"?\s*\d+(?:\.\d+)?\s*%?\"?", re.IGNORECASE
        ),
        law="Law 27 / Law 28c",
        replacement="validation_level + status + evidence_strength + experimental_validation (Law 29e)",
    ),
    ForbiddenPattern(
        id="C1",
        description="PASS with percentage (e.g. '85.7% PASS')",
        regex=re.compile(
            r"\d+(?:\.\d+)?\s*%\s*PASS\b", re.IGNORECASE
        ),
        law="Law 28b",
        replacement="STATUS: PASS | PASS_WITH_CONDITIONS | MARGINAL | BLOCKED | REJECTED (Law 29a)",
    ),
    ForbiddenPattern(
        id="C2",
        description="FAIL with percentage (e.g. '28% FAIL')",
        regex=re.compile(
            r"\d+(?:\.\d+)?\s*%\s*FAIL\b", re.IGNORECASE
        ),
        law="Law 28b",
        replacement="STATUS: PASS | PASS_WITH_CONDITIONS | MARGINAL | BLOCKED | REJECTED (Law 29a)",
    ),
    ForbiddenPattern(
        id="C3",
        description="'score: X%' or 'score = X%' verdict",
        regex=re.compile(
            r"\bscore\"?\s*[:=]\s*\"?\s*\d+(?:\.\d+)?\s*%\"?", re.IGNORECASE
        ),
        law="Law 28b",
        replacement="STATUS: PASS | PASS_WITH_CONDITIONS | MARGINAL | BLOCKED | REJECTED (Law 29a)",
    ),
    ForbiddenPattern(
        id="C4",
        description="'readiness: X%' as a verdict",
        regex=re.compile(
            r"\breadiness\"?\s*[:=]\s*\"?\s*\d+(?:\.\d+)?\s*%\"?", re.IGNORECASE
        ),
        law="Law 28b",
        replacement="STATUS: PASS | PASS_WITH_CONDITIONS | MARGINAL | BLOCKED | REJECTED (Law 29a)",
    ),
    ForbiddenPattern(
        id="C5",
        description="'X% pass' or 'X% fail' inside JSON string values (case-insensitive)",
        regex=re.compile(
            r"\d+(?:\.\d+)?\s*%\s*(?:pass|fail)\b", re.IGNORECASE
        ),
        law="Law 28b",
        replacement="STATUS: PASS | PASS_WITH_CONDITIONS | MARGINAL | BLOCKED | REJECTED (Law 29a)",
    ),
    ForbiddenPattern(
        id="E1",
        description="uncalibrated probability percentage",
        regex=re.compile(
            r"\bprobability\"?\s*[:=]\s*\"?\s*\d+(?:\.\d+)?\s*%\"?", re.IGNORECASE
        ),
        law="Law 27",
        replacement="validation_level: L{n} + experimental_validation: ABSENT (Law 29e)",
    ),
    ForbiddenPattern(
        id="E2",
        description="uncalibrated certainty percentage",
        regex=re.compile(
            r"\bcertainty\"?\s*[:=]\s*\"?\s*\d+(?:\.\d+)?\s*%\"?", re.IGNORECASE
        ),
        law="Law 27",
        replacement="validation_level: L{n} + status: PLAUSIBLE (Law 29)",
    ),
    ForbiddenPattern(
        id="E3",
        description="uncalibrated reliability percentage",
        regex=re.compile(
            r"\breliability\"?\s*[:=]\s*\"?\s*\d+(?:\.\d+)?\s*%\"?", re.IGNORECASE
        ),
        law="Law 27",
        replacement="validation_level: L{n} + experimental_validation: <level> (Law 29)",
    ),
]


# --------------------------------------------------------------------------
# Violation record
# --------------------------------------------------------------------------

@dataclass
class Violation:
    pattern_id: str
    file: str
    line_number: int
    line: str
    description: str
    law: str
    replacement: str

    def format(self) -> str:
        return (
            f"  [{self.pattern_id}] {self.file}:{self.line_number}\n"
            f"      {self.description}\n"
            f"      law:      {self.law}\n"
            f"      matched:  {self.line.strip()!r}\n"
            f"      replace:  {self.replacement}\n"
        )


# --------------------------------------------------------------------------
# Allowlist check
# --------------------------------------------------------------------------

def is_allowlisted(path: pathlib.Path) -> bool:
    """Check whether a path is allowlisted (exempt from scanning)."""
    try:
        rel = str(path.relative_to(ROOT))
    except ValueError:
        rel = str(path)
    rel = rel.replace("\\", "/")

    for allowed in ALLOWLIST_PATHS:
        if rel == allowed or rel.startswith(allowed):
            return True

    return False


def is_blueprint_artifact(path: pathlib.Path) -> bool:
    """Check whether a path is in a Blueprint-artifact directory.

    These are the directories whose contents are user-facing
    Blueprint outputs — the artifacts to which Law 27/28/29 apply
    directly. Source code (loops/, invention_compiler/, product/)
    is NOT a Blueprint artifact; it is internal code that will be
    migrated separately.
    """
    try:
        rel = str(path.relative_to(ROOT))
    except ValueError:
        rel = str(path)
    rel = rel.replace("\\", "/")

    for d in BLUEPRINT_ARTIFACT_DIRS:
        if rel.startswith(d + "/") or rel == d:
            return True

    # Root-level .md files (e.g., EXAMPLE_BLUEPRINT_001.md) are
    # also Blueprint artifacts.
    if path.suffix == ".md" and "/" not in rel:
        return True

    return False


# --------------------------------------------------------------------------
# File scanner
# --------------------------------------------------------------------------

def scan_file(path: pathlib.Path) -> list[Violation]:
    """Scan a single file for forbidden patterns.

    Lines inside markdown fenced code blocks (``` or ~~~) or blockquotes
    (lines starting with >) are exempt — they are quotes of forbidden
    language, not uses of it.
    """
    violations: list[Violation] = []

    if not path.exists() or not path.is_file():
        return violations

    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return violations

    try:
        rel = str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        rel = str(path)

    in_fenced_block = False
    fence_marker = ""

    for line_num, line in enumerate(text.splitlines(), start=1):
        stripped = line.lstrip()

        # Track fenced code blocks
        if stripped.startswith("```") or stripped.startswith("~~~"):
            if not in_fenced_block:
                in_fenced_block = True
                fence_marker = stripped[:3]
                continue
            elif stripped.startswith(fence_marker):
                in_fenced_block = False
                fence_marker = ""
                continue

        if in_fenced_block:
            continue

        # Exempt markdown blockquote lines (lines starting with >)
        if stripped.startswith(">"):
            continue

        # Exempt lines that are explicitly labeled "Bad:" — these
        # are example patterns showing what NOT to do.
        if stripped.startswith("Bad:"):
            continue
        if "Bad:" in line and any(p.regex.search(line) for p in PATTERNS):
            # Allow "Bad:" lines even if the prefix is mid-line
            continue

        for pattern in PATTERNS:
            if pattern.regex.search(line):
                violations.append(
                    Violation(
                        pattern_id=pattern.id,
                        file=rel,
                        line_number=line_num,
                        line=line,
                        description=pattern.description,
                        law=pattern.law,
                        replacement=pattern.replacement,
                    )
                )

    return violations


# --------------------------------------------------------------------------
# Recursive directory scan
# --------------------------------------------------------------------------

def iter_scan_targets(
    root: pathlib.Path,
    full_mode: bool = False,
    blueprint_only: bool = True,
) -> Iterable[pathlib.Path]:
    """Yield all files under root that should be scanned."""
    skip_dirs = {".git", "node_modules", "__pycache__", ".pytest_cache", "venv", ".venv"}

    extensions = FULL_SCAN_EXTENSIONS if full_mode else DEFAULT_SCAN_EXTENSIONS

    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix not in extensions:
            continue
        if any(part in skip_dirs for part in path.parts):
            continue
        if is_allowlisted(path):
            continue
        if blueprint_only and not full_mode:
            if not is_blueprint_artifact(path):
                continue
        yield path


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Honesty Loop forbidden-language scanner (Law 27, 28, 29)."
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=None,
        help="Specific file or directory to scan. Default: entire repo.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 on any violation (default in CI; flag retained for compatibility).",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Scan the entire repo (.md, .json, .ts, .tsx, .py), including source code. "
             "Informational unless --strict is also passed.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output violations as JSON (for programmatic consumers).",
    )
    args = parser.parse_args()

    if args.path:
        target = pathlib.Path(args.path)
        if not target.is_absolute():
            target = ROOT / target
        if target.is_file():
            files = [target]
        else:
            files = list(iter_scan_targets(
                target, full_mode=args.full, blueprint_only=False
            ))
    else:
        files = list(iter_scan_targets(
            ROOT, full_mode=args.full, blueprint_only=not args.full
        ))

    all_violations: list[Violation] = []
    for f in files:
        all_violations.extend(scan_file(f))

    if args.json:
        print(json.dumps(
            [
                {
                    "pattern_id": v.pattern_id,
                    "file": v.file,
                    "line": v.line_number,
                    "matched": v.line.strip(),
                    "law": v.law,
                    "description": v.description,
                    "replacement": v.replacement,
                }
                for v in all_violations
            ],
            indent=2,
        ))
    else:
        mode_label = "FULL (entire repo)" if args.full else "DEFAULT (Blueprint artifacts only)"
        print("=" * 70)
        print("HONESTY LOOP — Law 27/28/29 forbidden-language scanner")
        print(f"Mode: {mode_label}")
        print("=" * 70)
        print(f"Scanned {len(files)} files. {len(all_violations)} violation(s) found.")
        print()
        if all_violations:
            # Show at most 20 violations to keep output readable
            for v in all_violations[:20]:
                print(v.format())
            if len(all_violations) > 20:
                print(f"  ... and {len(all_violations) - 20} more violations not shown.")
                print(f"  Run with --json to see all violations.")
            print("-" * 70)
            print(f"STATUS: REJECTED — {len(all_violations)} violation(s) of Law 27/28/29.")
            print("Per HONESTY_LOOP.md: artifact cannot close until violations are resolved.")
            print("See BLUEPRINT_CONSTITUTION.md Law 27, 28, 29 for required replacements.")
        else:
            print("STATUS: PASS — no forbidden language detected.")

    # Exit code:
    # - default mode (--full not set): exit 1 on any violation (CI gate behavior)
    # - --full mode without --strict: informational, exit 0
    # - --full mode with --strict: exit 1 on any violation
    if args.full and not args.strict:
        return 0
    return 1 if all_violations else 0


if __name__ == "__main__":
    sys.exit(main())

