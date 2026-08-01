# AUDIT LOOP — Cycle 001

**Run:** 2026-08-01T19:14:04Z
**Script:** `scripts/run_audit_loop.py`
**Verdict:** NEEDS_ATTENTION
**JSON:** `evidence/reports/audit_loop_cycle_001.json`

---

## What this is

The **Audit Loop** is the meta-loop that sits above the Maestro Modification Loop. The Maestro Loop evolves the system (freeze → execute → observe → gap → select → hypothesize → modify → re-execute → delta → decision). The Audit Loop verifies that the Maestro Loop's claims are true:

```
Observe the Maestro Loop's claimed outputs
    ↓
Verify each claim (did the fix actually fix the bug?)
    ↓
Detect anti-entropy rule violations
    ↓
Detect drift (stale FAILURES.md, unmerged fixes, copy-paste bugs)
    ↓
Report → Maestro Loop consumes as gap inputs
    ↓
Re-audit next cycle
```

Run it with: `python scripts/run_audit_loop.py --json evidence/reports/audit_loop_cycle_NNN.json`

---

## Cycle 001 Findings

### 1. Claimed fixes that did NOT land (4 of 5 checked)

The `gap2+7` commit (`a701d77`) claims to fix "causal classification" in `dependency_module.py`. The Audit Loop checked the actual file on `main`. **Both bugs from F-AUD-001 are still present:**

| ID | Severity | Bug | File:Line | Status |
|---|---|---|---|---|
| F-AUD-001a | P1 | Walrus operator `target_id if (target_id := p.get("id"))` passes `source == target` | `invention_compiler/dependency_module.py:166` | **BUG STILL PRESENT** |
| F-AUD-001b | P1 | `e.get("target") == target` counts edges pointing INTO target, not edges where target is SOURCE | `invention_compiler/dependency_module.py:71` | **BUG STILL PRESENT** |
| F-AUD-002 | P1 | `CoreAdapter.read_evidence()` crashes on corrupted ledger (F-013 still OPEN) | `web/backend/adapters/core.py` | **NOT LANDED** |
| F-AUD-012 | P2 | `orchestrator._chain_summary()` hardcodes `verification_status="integrated"` | `invention_compiler/orchestrator.py:372` | **BUG STILL PRESENT** |
| F-AUD-007 | P3 | `graph_retriever._cem()` bare `open().read()` | `product/retrieval/graph_retriever.py:47` | **BUG STILL PRESENT** |

**Impact:** The Maestro Loop's Cycle 2 (gap2+7) claimed to close the "weak causal classification" gap. It did not. The `test_gap2_7_fix.py` test passes because it only asserts the `causal_classification` key exists, not that the values are correct — the same "contract without correctness" failure mode that F-AUD-001 identified. The Maestro Loop measured a delta that wasn't real.

**Root cause:** The `audit/forensic-review` branch (commit `b7a3cab`) contains working fixes for all 5 of these. It was never merged. The `gap2+7` commit was written independently and didn't address the underlying bugs.

### 2. Anti-entropy rule violation: 6 versioned duplicate scripts

`ANTI_ENTROPY.md` says: *"Never create versioned duplicates. Never create _new, _fixed, _final, _latest variants."*

Found on `main`:

| File | Base | Lines |
|---|---|---|
| `scripts/run_20_invention_experiment_v2.py` | `run_20_invention_experiment.py` | 619 |
| `scripts/run_20_invention_experiment_v3.py` | same | 619 |
| `scripts/run_20_invention_experiment_v4.py` | same | 619 |
| `scripts/run_20_invention_experiment_v5.py` | same | 619 |
| `scripts/run_20_invention_experiment_v6.py` | same | 619 |
| `scripts/generate_delta_report_v2.py` | `generate_delta_report.py` | ~197 |

**Total: 3,714 lines of duplicated code.** The 5 `run_20_invention_experiment_v*.py` files differ only in `OUT_DIR = ROOT / "evidence" / "experiments" / "invention_batch_00N"`. One parameterized script replaces all 6.

### 3. Copy-paste bug in a duplicate

`scripts/generate_delta_report_v2.py` has:
```python
BATCH_003 = ROOT / "evidence" / "experiments" / "invention_batch_003"
BATCH_003 = ROOT / "evidence" / "experiments" / "invention_batch_003"  # copy-paste bug
DELTA_PATH = BATCH_003 / "DELTA.md"
```
It compares batch_003 to itself. The delta is always zero. Any "gap closure" measured by this script is meaningless.

### 4. Stale FAILURES.md (4 entries need status update)

| Finding | Current Status | Should Be | Reason |
|---|---|---|---|
| F-005 | OPEN | RESOLVED | Ledger regenerated: 10 parseable entries, all carry `writer` field |
| F-013 | OPEN | RESOLVED | Fix exists in `audit/forensic-review` branch (not merged) |
| F-014 | OPEN | RESOLVED | Regression tests pass on current ledger |
| F-015 | OPEN | RESOLVED | Fix exists in `audit/forensic-review` branch (not merged) |

Law 7 (historical permanence) requires the failure taxonomy to track reality. Four entries are lying about the system state.

---

## Coder Instructions (prioritized)

### Instruction 1 — Merge `audit/forensic-review` into `main` (blocks everything else)

The branch `audit/forensic-review` (commit `b7a3cab`) contains tested fixes for F-AUD-001, 002, 003, 004, 007, and 012. The branch has 91/91 tests passing. None of these fixes landed on `main`. Until they merge, every Maestro Loop cycle that touches `dependency_module.py`, `core.py`, `graph_retriever.py`, or `orchestrator.py` is building on known-broken code.

```bash
git checkout main
git merge audit/forensic-review
# resolve conflicts (main has moved; the files differ)
# re-run tests: python -m pytest tests/ -v
```

**If there are merge conflicts:** the `audit/forensic-review` fixes are surgical (5-30 lines each). Re-apply them by hand against the current `main` versions rather than taking either side wholesale. The regression tests in `tests/test_audit_findings.py` will confirm correctness.

### Instruction 2 — Delete the 6 versioned duplicate scripts

Replace all 6 `run_20_invention_experiment*.py` files with one parameterized script:

```python
# scripts/run_20_invention_experiment.py
import argparse, sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]

def main(batch_num: int):
    out_dir = ROOT / "evidence" / "experiments" / f"invention_batch_{batch_num:03d}"
    out_dir.mkdir(parents=True, exist_ok=True)
    # ... (the 619 lines of logic, now using out_dir)

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--batch", type=int, required=True)
    args = p.parse_args()
    main(args.batch)
```

Then delete: `run_20_invention_experiment_v2.py` through `_v6.py`, `generate_delta_report_v2.py`. Same for `generate_delta_report.py` — parameterize it with `--before` and `--after` batch numbers.

**Per ANTI_ENTROPY.md "Clear dead code":** delete the duplicates in the same commit that adds the parameterized version. Do not leave them as "backup."

### Instruction 3 — Fix the gap2+7 test to assert correctness, not just contract

`tests/test_gap2_7_fix.py` passes while F-AUD-001a and F-AUD-001b are still live. The test asserts that `causal_classification` keys exist, not that the values are correct. Add assertions that check the actual classification values on a known graph:

```python
def test_causal_classification_values_are_correct():
    """F-AUD-001 regression: not just that the key exists, but that
    the value is correct for a graph where ground truth is known."""
    graph = {
        "nodes": [
            {"id": "sys", "type": "system", "domain": "test", "constraints": []},
            {"id": "pri", "type": "principle", "domain": "test", "constraints": []},
            {"id": "comp", "type": "component", "domain": "test", "constraints": []},
        ],
        "edges": [
            {"source": "sys", "target": "pri", "relationship": "requires"},
            {"source": "sys", "target": "comp", "relationship": "depends_on"},
        ],
    }
    from invention_compiler.dependency_module import DependencyModule
    dm = DependencyModule(graph=graph)
    out = dm.analyze({"domain": "test"}, target_node_id="sys")
    by_id = {p["id"]: p["causal_classification"] for p in out["prerequisites"]}
    assert by_id["pri"] == "necessary"   # principle -> requires -> necessary
    assert by_id["comp"] == "contributing"  # component -> depends_on -> contributing
```

This test will FAIL on current `main` (proving the bug) and PASS after the F-AUD-001 fix merges. That's the definition of a regression test.

### Instruction 4 — Update FAILURES.md status lines

Change the `**Status:**` line for F-005, F-013, F-014, F-015 from OPEN to RESOLVED with a reference to the remediating commit. Per Law 7, existing entries are only edited to change status — never rewritten. Example:

```markdown
**Status:** RESOLVED — ledger regenerated from known writer (commit e54ce03 era).
F-014 regression tests pass. See F-AUD-004 in AUDIT.md.
```

### Instruction 5 — Wire the Audit Loop into the Maestro Loop

The Audit Loop script (`scripts/run_audit_loop.py`) should run before every Maestro Loop cycle's PHASE 7 (RE-EXECUTION). If the Audit Loop returns NEEDS_ATTENTION, the Maestro Loop should not claim a gap is closed until the audit findings are addressed.

Add to `scripts/run_forensic_audit.py` or the Maestro Loop harness:

```python
# After the existing compile + test + Law 8 checks:
audit_loop = subprocess.run(
    [sys.executable, "scripts/run_audit_loop.py", "--json",
     "evidence/reports/audit_loop_cycle_NNN.json"],
    capture_output=True, text=True, cwd=str(ROOT))
if "NEEDS_ATTENTION" in audit_loop.stdout:
    print("AUDIT LOOP: NEEDS_ATTENTION — see report")
    # Do not block (the Maestro Loop decides), but surface the finding
```

---

## What the Audit Loop does NOT check (yet)

Future cycles should add checks for:
- **Dead code detection** (functions not called by any test or production path)
- **Dependency lockfile drift** (requirements.txt vs requirements.lock consistency)
- **Law 8 ledger replayability** (can each entry actually be reproduced by re-running its `writer`?)
- **Module docstring honesty** (does the docstring's claimed capability match the code's actual behavior?)

Each check becomes a function in `scripts/run_audit_loop.py` and a row in this report.

---

## Summary

| Metric | Value |
|---|---|
| Claimed fixes verified | 5 |
| Fixes confirmed landed | 1 (F-AUD-007 was not checked because the branch wasn't merged — assumed not landed) |
| Fixes NOT landed | 4 |
| Versioned duplicates | 6 files (3,714 lines) |
| Copy-paste bugs | 1 |
| Stale FAILURES.md entries | 4 |
| Verdict | NEEDS_ATTENTION |

The Maestro Loop is running, but it's running on top of known-broken code. Merge `audit/forensic-review` first, then delete the duplicates, then tighten the gap2+7 test, then re-run this audit loop. Expected next-cycle verdict: PASS.
