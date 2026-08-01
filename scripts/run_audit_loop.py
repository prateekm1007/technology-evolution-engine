#!/usr/bin/env python3
"""
The Audit Loop — a meta-loop that audits the Maestro Loop.

The Maestro Modification Loop (ANTI_ENTROPY.md, v1.0) is the epistemic
loop the team uses to evolve the system:

    Freeze → Execute → Observe → Gap Analysis → Select → Hypothesis →
    Modify → Re-execute → Delta → Decision

The Audit Loop is the meta-loop that sits above it:

    Observe the Maestro Loop's claimed outputs
        ↓
    Verify each claim (did the fix actually fix the bug?)
        ↓
    Detect anti-entropy rule violations (versioned duplicates, dead code, ...)
        ↓
    Detect drift (stale FAILURES.md, unmerged fixes, hardcoded labels)
        ↓
    Report findings as F-AUD-XXX entries
        ↓
    (Maestro Loop consumes the findings as gap inputs)
        ↓
    Re-audit next cycle

Usage:
    python scripts/run_audit_loop.py [--json evidence/reports/audit_loop.json]

Exit code:
    0 — always (the script reports, never blocks; the Maestro Loop decides)
"""
import argparse
import json
import re
import subprocess
import sys
import pathlib
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]


def now_iso():
    return datetime.now(timezone.utc).isoformat()


# ----------------------------------------------------------------------
# Check 1: Verify that claimed fixes actually fixed their target bugs.
# Each check looks for a specific code pattern that should NOT exist
# if the fix landed. If the pattern is still present, the fix is
# "claimed but not landed" — the most dangerous class of drift.
# ----------------------------------------------------------------------

CLAIMED_FIXES = [
    {
        "id": "F-AUD-001a",
        "claim": "dependency_module walrus-operator bug fixed",
        "claim_source": "audit/forensic-review branch (b7a3cab) + gap2+7 commit (a701d77) claims to fix causal classification",
        "file": "invention_compiler/dependency_module.py",
        "pattern": r"target_id\s+if\s*\(target_id\s*:=\s*p\.get\(\"id\"\)\)",
        "should_exist": False,
        "severity": "P1",
        "instruction": "Remove the walrus operator. Pass target_node_id directly as the target argument.",
    },
    {
        "id": "F-AUD-001b",
        "claim": "dependency_module direction bug fixed (edges where target is SOURCE, not TARGET)",
        "claim_source": "audit/forensic-review branch (b7a3cab)",
        "file": "invention_compiler/dependency_module.py",
        "pattern": r'e\.get\("target"\)\s*==\s*target\s*$',
        "should_exist": False,
        "severity": "P1",
        "instruction": "Change e.get('target') == target to e.get('source') == target. A node's prerequisites are edges where the node is the SOURCE (per LineageMapper convention: A --requires--> B means A requires B).",
    },
    {
        "id": "F-AUD-002",
        "claim": "CoreAdapter.read_evidence() shares _read_ledger_safely() helper",
        "claim_source": "audit/forensic-review branch (b7a3cab); F-013 tracked as OPEN on main",
        "file": "web/backend/adapters/core.py",
        "pattern": r"_read_ledger_safely",
        "should_exist": True,
        "severity": "P1",
        "instruction": "Add _read_ledger_safely() helper to core.py and have read_evidence() delegate to it. main.py::evidence() should also delegate. Closes F-013.",
    },
    {
        "id": "F-AUD-007",
        "claim": "graph_retriever._cem() uses context manager (no bare open().read())",
        "claim_source": "audit/forensic-review branch (b7a3cab)",
        "file": "product/retrieval/graph_retriever.py",
        "pattern": r"open\([^)]*\)\.read\(\)",
        "should_exist": False,
        "severity": "P3",
        "instruction": "Convert bare open(...).read() to 'with open(...) as f: content = f.read()'.",
    },
    {
        "id": "F-AUD-012",
        "claim": "orchestrator._chain_summary() derives verification_status (not hardcoded)",
        "claim_source": "audit/forensic-review branch (b7a3cab)",
        "file": "invention_compiler/orchestrator.py",
        "pattern": r'"verification_status":\s*"integrated"',
        "should_exist": False,
        "severity": "P2",
        "instruction": "Derive verification_status from layers[8].get('verification_status') instead of hardcoding 'integrated'.",
    },
]


def check_claimed_fixes():
    """For each claimed fix, check if the pattern exists in the file."""
    results = []
    for fix in CLAIMED_FIXES:
        path = ROOT / fix["file"]
        if not path.exists():
            results.append({**fix, "status": "file_missing", "landed": False})
            continue
        text = path.read_text(encoding="utf-8")
        pattern_found = bool(re.search(fix["pattern"], text, re.MULTILINE))
        if fix["should_exist"]:
            landed = pattern_found
            status = "landed" if landed else "not_landed"
        else:
            landed = not pattern_found
            status = "landed" if landed else "bug_still_present"
        results.append({
            "id": fix["id"],
            "claim": fix["claim"],
            "claim_source": fix["claim_source"],
            "file": fix["file"],
            "pattern": fix["pattern"],
            "should_exist": fix["should_exist"],
            "pattern_found": pattern_found,
            "landed": landed,
            "status": status,
            "severity": fix["severity"],
            "instruction": fix["instruction"],
        })
    return results


# ----------------------------------------------------------------------
# Check 2: Anti-entropy rule violations — versioned duplicates.
# ANTI_ENTROPY.md: "Never create versioned duplicates. Never create
# _new, _fixed, _final, _latest variants."
# ----------------------------------------------------------------------

def find_versioned_duplicates():
    """Find files matching _v2, _v3, _v4, _v5, _v6, _new, _fixed, _final, _latest."""
    patterns = [
        r"_v\d+\.py$",
        r"_new\.py$",
        r"_fixed\.py$",
        r"_final\.py$",
        r"_latest\.py$",
    ]
    violations = []
    for p in ROOT.rglob("*.py"):
        if ".git" in p.parts or "__pycache__" in p.parts or "venv" in p.parts:
            continue
        rel = p.relative_to(ROOT)
        for pat in patterns:
            if re.search(pat, p.name):
                # Find the "base" file (without the suffix).
                base_name = re.sub(r"_(v\d+|new|fixed|final|latest)\.py$", ".py", p.name)
                base_path = p.parent / base_name
                violations.append({
                    "file": str(rel),
                    "pattern_matched": pat,
                    "base_file_exists": base_path.exists(),
                    "base_file": str(base_path.relative_to(ROOT)) if base_path.exists() else None,
                })
                break
    return violations


# ----------------------------------------------------------------------
# Check 3: Stale FAILURES.md — entries marked OPEN that should be RESOLVED.
# ----------------------------------------------------------------------

def check_failures_md_sync():
    """Check if F-013, F-014, F-015 are still marked OPEN on main
    (they were resolved in the audit/forensic-review branch)."""
    path = ROOT / "FAILURES.md"
    if not path.exists():
        return {"error": "FAILURES.md not found"}
    text = path.read_text(encoding="utf-8")
    stale = []
    for fid in ("F-005", "F-013", "F-014", "F-015"):
        # Extract the block for this finding.
        m = re.search(rf"### {fid}\b.*?(?=\n### |\Z)", text, re.DOTALL)
        if not m:
            stale.append({"finding": fid, "issue": "block not found"})
            continue
        block = m.group(0)
        # Check the Status line.
        status_match = re.search(r"\*\*Status:\*\*\s*(.+?)(?:\n|$)", block)
        if not status_match:
            stale.append({"finding": fid, "issue": "no Status line"})
            continue
        status_text = status_match.group(1).strip()
        if fid in ("F-005", "F-014") and "RESOLVED" not in status_text:
            stale.append({
                "finding": fid,
                "current_status": status_text,
                "expected_status": "RESOLVED",
                "reason": "ledger was regenerated (10 parseable entries); F-014 regression tests pass",
            })
        elif fid in ("F-013", "F-015") and "RESOLVED" not in status_text:
            stale.append({
                "finding": fid,
                "current_status": status_text,
                "expected_status": "RESOLVED",
                "reason": "fix exists in audit/forensic-review branch (shared _read_ledger_safely helper); not merged to main",
            })
    return stale


# ----------------------------------------------------------------------
# Check 4: Copy-paste bugs in versioned duplicates.
# ----------------------------------------------------------------------

def check_delta_report_v2_bug():
    """generate_delta_report_v2.py compares batch_003 to batch_003
    (copy-paste bug — should compare different batches)."""
    path = ROOT / "scripts" / "generate_delta_report_v2.py"
    if not path.exists():
        return {"error": "file not found"}
    text = path.read_text(encoding="utf-8")
    # Look for BATCH_003 = ... assigned twice (the copy-paste bug).
    batch_assignments = re.findall(r"BATCH_\w+\s*=\s*ROOT\s*/\s*\"evidence\"\s*/\s*\"experiments\"\s*/\s*\"(invention_batch_\w+)\"", text)
    if len(batch_assignments) >= 2 and batch_assignments[0] == batch_assignments[1]:
        return {
            "bug": "copy-paste: compares the same batch to itself",
            "batches": batch_assignments,
            "file": "scripts/generate_delta_report_v2.py",
            "severity": "P2",
            "instruction": "Fix the second BATCH_003 assignment to point at a different batch, OR delete this duplicate script and parameterize generate_delta_report.py.",
        }
    return {"ok": True}


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------

def run_audit_loop():
    print("=" * 60)
    print("AUDIT LOOP — Cycle 001")
    print(f"Timestamp: {now_iso()}")
    print("=" * 60)

    claimed = check_claimed_fixes()
    duplicates = find_versioned_duplicates()
    stale = check_failures_md_sync()
    delta_bug = check_delta_report_v2_bug()

    # Summarize.
    not_landed = [c for c in claimed if not c["landed"]]
    print(f"\n[1] Claimed fixes verification:")
    print(f"    {len(claimed) - len(not_landed)}/{len(claimed)} fixes confirmed landed")
    for c in not_landed:
        status_label = "BUG STILL PRESENT" if c["status"] == "bug_still_present" else "NOT LANDED"
        print(f"    [{status_label}] {c['id']} ({c['severity']}): {c['claim']}")
        print(f"      file: {c['file']}")
        print(f"      instruction: {c['instruction']}")

    print(f"\n[2] Versioned duplicates (ANTI_ENTROPY violation):")
    print(f"    {len(duplicates)} files found")
    for d in duplicates:
        print(f"    {d['file']} (base: {d.get('base_file', 'none')})")

    print(f"\n[3] Stale FAILURES.md entries:")
    print(f"    {len(stale)} entries need status update")
    for s in stale:
        print(f"    {s['finding']}: {s.get('current_status', '?')} → should be {s.get('expected_status', '?')}")

    print(f"\n[4] Copy-paste bugs in duplicates:")
    if delta_bug.get("ok"):
        print("    (none found)")
    else:
        print(f"    {delta_bug.get('file')}: {delta_bug.get('bug')}")
        print(f"      severity: {delta_bug.get('severity')}")

    verdict = "PASS" if not not_landed and not duplicates and not stale and delta_bug.get("ok") else "NEEDS_ATTENTION"
    print(f"\n{'=' * 60}")
    print(f"AUDIT LOOP VERDICT: {verdict}")
    print(f"{'=' * 60}")

    return {
        "generated_at": now_iso(),
        "cycle": 1,
        "verdict": verdict,
        "claimed_fixes": claimed,
        "versioned_duplicates": duplicates,
        "stale_failures": stale,
        "copy_paste_bugs": delta_bug,
        "summary": {
            "fixes_not_landed": len(not_landed),
            "versioned_duplicates": len(duplicates),
            "stale_failures": len(stale),
            "copy_paste_bugs": 0 if delta_bug.get("ok") else 1,
        },
    }


def main():
    parser = argparse.ArgumentParser(description="The Audit Loop (meta-loop over the Maestro Loop)")
    parser.add_argument("--json", dest="json_out", default=None,
                        help="path to write the JSON report")
    args = parser.parse_args()
    report = run_audit_loop()
    if args.json_out:
        out = pathlib.Path(args.json_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2, default=str) + "\n",
                       encoding="utf-8")
        print(f"\nwrote {out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
