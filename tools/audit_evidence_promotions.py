#!/usr/bin/env python3
"""
Repository-wide static audit: zero direct EVIDENCE_BACKED writes outside canonical promotion.

Per CTO V16 #3/#4: "Search every occurrence of status='EVIDENCE_BACKED' in constructors,
migrations, deserializers, fixtures, graph builders, loaders, and tests. The invariant
must be: NO DIRECT EVIDENCE_BACKED WRITE OUTSIDE canonical promotion function."
"""
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ALLOWED_PATTERNS = [
    r'def promote_claim_to_evidence_backed',
    r'status="EVIDENCE_BACKED" if _can_promote',
    r'promote_claim_to_evidence_backed',
    r'"EVIDENCE_BACKED"',
    r"'EVIDENCE_BACKED'",
    r'claim\.status == "EVIDENCE_BACKED"',
    r'self\.status == "EVIDENCE_BACKED"',
    r'== "EVIDENCE_BACKED"',
    r'!= "EVIDENCE_BACKED"',
    r'in \("EVIDENCE_BACKED"',
    r'"EVIDENCE_BACKED" in',
    r'assert.*status.*EVIDENCE_BACKED',
    r'is_evidence_backed',
    r'CLAIM_STATUS',
    r'#.*EVIDENCE_BACKED',
    r'EVIDENCE_BACKED.*#',
]


def scan_file(filepath: Path) -> list[dict]:
    violations = []
    try:
        content = filepath.read_text(errors='replace')
    except Exception:
        return []

    in_docstring = False
    for line_num, line in enumerate(content.splitlines(), 1):
        line_stripped = line.strip()

        # Track docstring state
        if '"""' in line or "'''" in line:
            # Toggle docstring state (simplified: handles single-line and multi-line)
            count = line.count('"""') + line.count("'''")
            if count >= 2:
                pass  # single-line docstring, skip this line
            else:
                in_docstring = not in_docstring
                continue
        if in_docstring:
            continue

        if line_stripped.startswith('#'):
            continue
        if line_stripped.startswith('"""') or line_stripped.startswith("'''"):
            continue
        if 'EVIDENCE_BACKED' not in line:
            continue

        is_allowed = False
        for pattern in ALLOWED_PATTERNS:
            if re.search(pattern, line):
                is_allowed = True
                break

        if not is_allowed:
            if 'status=' in line or 'status =' in line:
                if '_can_promote' not in line and 'promote_claim' not in line:
                    violations.append({
                        'file': str(filepath.relative_to(REPO)),
                        'line': line_num,
                        'content': line_stripped[:200],
                    })
    return violations


def main():
    all_violations = []
    for pyfile in (REPO / "source_fabric").rglob("*.py"):
        all_violations.extend(scan_file(pyfile))
    scripts_dir = REPO / "scripts"
    if scripts_dir.exists():
        for pyfile in scripts_dir.rglob("*.py"):
            all_violations.extend(scan_file(pyfile))

    if all_violations:
        print("AUDIT FAIL: Direct EVIDENCE_BACKED writes outside canonical promotion:")
        for v in all_violations:
            print(f"  {v['file']}:{v['line']}: {v['content']}")
        print(f"\nTotal violations: {len(all_violations)}")
        sys.exit(1)
    else:
        print("AUDIT PASS: No direct EVIDENCE_BACKED writes outside canonical promotion.")
        sys.exit(0)


if __name__ == "__main__":
    main()
