#!/usr/bin/env python3
"""
SECURITY FORENSIC V7 — FINAL BOUNDARY CORRECTION

NO adjudication. NO benchmark modifications. NO scorer modifications.

Creates a minimal adjudicator bundle SEPARATE from the Git repository.
The adjudicator bundle contains ONLY:
  - blinded packets
  - adjudication instructions
  - empty ledger/template
  - public integrity metadata (hashes for verification, NOT ground truth)

The bundle MUST NOT contain:
  - case files
  - real/fabricated labels
  - breakthrough relationships
  - withheld facts
  - answer mechanisms
  - machine receipts/scores
  - full packets
  - evaluator secrets
  - Git metadata/history

Adds Q_RESEARCH_REPO_INACCESSIBLE_TO_ADJUDICATOR: a hard check proving the
adjudicator process cannot read the research repo, Git objects, case files,
or evaluator namespace.

Q is a mandatory blocking prerequisite.
Only after B/C/D/P/O/Q all pass in a true multi-identity deployment can
the 80 adjudications begin.
"""
import json
import hashlib
import os
import sys
import shutil
import subprocess
from pathlib import Path
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parents[3]
os.chdir(REPO)
sys.path.insert(0, str(REPO))

V3_DIR = REPO / "discovery_fabric/dsb_v1/adjudication_engine_v3"
CORRECTION_DIR = REPO / "discovery_fabric/dsb_v1/adjudication_security_correction"
BUNDLE_DIR = REPO / "discovery_fabric/dsb_v1/adjudicator_bundle"

# The bundle lives OUTSIDE the Git repo in deployment. Here we create it
# inside the repo for distribution, but the V7 report documents that in
# the real deployment it must be extracted to a separate filesystem location
# with no Git access.


# =============================================================================
# Step 1: Build the minimal adjudicator bundle
# =============================================================================

def build_adjudicator_bundle() -> dict:
    """Build the minimal adjudicator bundle.

    The bundle contains ONLY:
    - blinded packets (80)
    - adjudication instructions
    - empty ledger/template
    - public integrity metadata (manifest of allowed files + their hashes)

    The bundle MUST NOT contain any ground truth, machine scores, or
    evaluator secrets.
    """
    # Clean bundle directory
    if BUNDLE_DIR.exists():
        shutil.rmtree(BUNDLE_DIR)
    BUNDLE_DIR.mkdir(parents=True, exist_ok=True)

    bundle_manifest = {
        "schema_version": "1.0.0",
        "bundle_type": "DSB_V1_ADJUDICATOR_BUNDLE",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "description": "Minimal adjudicator bundle. Contains ONLY blinded packets, instructions, empty template, and public integrity metadata. NO ground truth, NO machine scores, NO evaluator secrets, NO Git metadata.",
        "allowed_contents": [
            "cto_packets_BLIND.json — 80 blinded adjudication packets",
            "CTO_ADJUDICATION_INSTRUCTIONS.md — adjudication rubric",
            "cto_adjudication_template.json — empty ledger template",
            "BUNDLE_MANIFEST.json — this file (public integrity metadata)",
        ],
        "forbidden_contents": [
            "case files (cases/real/, cases/fabricated/)",
            "real/fabricated labels (case_type field)",
            "breakthrough_relationship text",
            "withheld_facts text",
            "answer_mechanism text",
            "machine receipts (receipts/)",
            "machine scores (scores/)",
            "full packets (cto_packets_FULL.json)",
            "evaluator secrets (vault_key*, machine_score_vault*)",
            "Git metadata (.git/)",
            "research repository code (discovery_fabric/)",
        ],
        "files": {},
    }

    # 1. Copy blinded packets
    blind_src = V3_DIR / "adjudicator_workspace/cto_packets_BLIND.json"
    if blind_src.exists():
        blind_dst = BUNDLE_DIR / "cto_packets_BLIND.json"
        shutil.copy2(blind_src, blind_dst)
        file_hash = hashlib.sha256(blind_dst.read_bytes()).hexdigest()
        bundle_manifest["files"]["cto_packets_BLIND.json"] = {
            "source": str(blind_src.relative_to(REPO)),
            "sha256": file_hash,
            "size_bytes": blind_dst.stat().st_size,
            "description": "80 blinded adjudication packets (no ground truth)",
        }

    # 2. Copy instructions (need to create a clean V7 version without repo paths)
    instructions = build_bundle_instructions()
    instr_path = BUNDLE_DIR / "CTO_ADJUDICATION_INSTRUCTIONS.md"
    instr_path.write_text(instructions)
    file_hash = hashlib.sha256(instr_path.read_bytes()).hexdigest()
    bundle_manifest["files"]["CTO_ADJUDICATION_INSTRUCTIONS.md"] = {
        "sha256": file_hash,
        "size_bytes": instr_path.stat().st_size,
        "description": "Adjudication rubric and instructions",
    }

    # 3. Copy empty template
    template_src = V3_DIR / "adjudicator_workspace/cto_adjudication_template.json"
    if template_src.exists():
        template_dst = BUNDLE_DIR / "cto_adjudication_template.json"
        shutil.copy2(template_src, template_dst)
        file_hash = hashlib.sha256(template_dst.read_bytes()).hexdigest()
        bundle_manifest["files"]["cto_adjudication_template.json"] = {
            "sha256": file_hash,
            "size_bytes": template_dst.stat().st_size,
            "description": "Empty adjudication ledger template (80 slots)",
        }

    # 4. Verify bundle does NOT contain forbidden files
    forbidden_in_bundle = []
    for item in BUNDLE_DIR.rglob("*"):
        if item.is_file():
            name = item.name
            if "vault_key" in name or "machine_score_vault" in name:
                forbidden_in_bundle.append(str(item))
            if "FULL" in name or "full" in name.lower():
                forbidden_in_bundle.append(str(item))
            if "receipt" in name.lower() or "score" in name.lower():
                if name != "cto_adjudication_template.json":  # template is OK
                    forbidden_in_bundle.append(str(item))

    bundle_manifest["forbidden_files_check"] = {
        "passed": len(forbidden_in_bundle) == 0,
        "found": forbidden_in_bundle,
    }

    # 5. Seal the manifest
    canonical = json.dumps(bundle_manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    bundle_manifest["manifest_hash"] = hashlib.sha256(canonical.encode()).hexdigest()

    manifest_path = BUNDLE_DIR / "BUNDLE_MANIFEST.json"
    with open(manifest_path, "w") as f:
        json.dump(bundle_manifest, f, indent=2, ensure_ascii=False)

    return bundle_manifest


def build_bundle_instructions() -> str:
    """Build adjudication instructions for the bundle (no repo paths)."""
    return f"""# CTO ADJUDICATION INSTRUCTIONS — DSB V1

**Bundle:** DSB_V1_ADJUDICATOR_BUNDLE
**Date:** {datetime.now(timezone.utc).isoformat()}
**Evidence tier:** AI_CTO_ADJUDICATION (NOT HUMAN_VALIDATED)

---

## 1. Bundle Contents

This bundle contains ONLY:
- `cto_packets_BLIND.json` — 80 blinded adjudication packets
- `CTO_ADJUDICATION_INSTRUCTIONS.md` — this file
- `cto_adjudication_template.json` — empty ledger template
- `BUNDLE_MANIFEST.json` — public integrity metadata (file hashes)

This bundle does NOT contain:
- Case files (real or fabricated)
- Real/fabricated labels
- Breakthrough relationships
- Withheld facts
- Answer mechanisms
- Machine receipts or scores
- Full packets
- Evaluator secrets
- Git metadata or repository history
- Research repository code

## 2. Adjudicator Environment Requirements

The adjudicator machine/container MUST:
- Have ZERO access to the research repository
- Have ZERO access to Git objects, case files, or evaluator namespace
- Have ZERO access to machine scores or vault keys
- Run in a separate OS identity/container from the evaluator

The adjudicator machine MUST NOT:
- Be able to read the research repository
- Be able to read Git objects (.git/)
- Be able to read case files (cases/real/, cases/fabricated/)
- Be able to read evaluator_boundary/
- Be able to read receipts/ or scores/
- Have network access to the evaluator machine

## 3. Six Observable Questions Per Packet

### Q1. MECHANISTIC_VALIDITY
Is the proposed mechanism scientifically valid and plausibly tied to the exposed facts?
- YES / PARTIAL / NO

### Q2. DISCOVERY_STRUCTURE_VALIDITY
Does the proposed_relationship express a relationship NOT explicit in the exposed_facts that combines them in a novel way?
- YES / PARTIAL / NO

### Q3. NOVELTY
Does the proposal introduce genuinely new entities, mechanisms, or relational structure beyond the exposed_facts?
- YES / PARTIAL / NO

### Q4. FALSIFIABILITY
Is the proposed_relationship specific enough to be falsifiable?
- YES / NO

### Q5. EXPERIMENTAL_COHERENCE
Could an experiment be designed to test this proposal, given the exposed_facts?
- YES / PARTIAL / NO

### Q6. PLAUSIBILITY
Is this proposal scientifically plausible — could it work in reality, regardless of whether it has been historically demonstrated?
- PLAUSIBLE / IMPLAUSIBLE / UNCERTAIN

## 4. Submission

1. Copy `cto_adjudication_template.json` to `cto_adjudication.json`.
2. Fill in all 80 adjudication slots.
3. Fill in `submitted_at` and `time_spent_minutes`.
4. Seal the ledger: compute SHA-256 of the ledger (excluding ledger_hash) and add it as `ledger_hash`.
5. Save.

## 5. Evidence Tier

AI_CTO_ADJUDICATION — NOT HUMAN_VALIDATED. Per MC-1 (No self-validation),
CTO adjudication cannot validate the system. No architecture change permitted
based on this adjudication alone.

---

**End of Adjudication Instructions.**
"""


# =============================================================================
# Step 2: Q check — research repo inaccessible to adjudicator
# =============================================================================

def check_Q_research_repo_inaccessible() -> dict:
    """Q: Prove the adjudicator process cannot read the research repo,
    Git objects, case files, or evaluator namespace.

    In this single-user environment, the adjudicator process CAN read
    everything (same UID). This check is ENVIRONMENT_BLOCKED — it cannot
    be executed here. It requires a real multi-identity deployment where
    the adjudicator runs as a separate user/container with no access to
    the research repository.

    The check verifies:
    1. Adjudicator cannot read the research repository directory
    2. Adjudicator cannot read .git/ objects
    3. Adjudicator cannot read case files (cases/real/, cases/fabricated/)
    4. Adjudicator cannot read evaluator_boundary/
    5. Adjudicator cannot read receipts/ or scores/
    6. Adjudicator cannot read the frozen scorer (scorer.py)
    7. Adjudicator bundle is self-contained (no symlinks to repo)
    """
    checks = []

    # 1. Verify bundle is self-contained (no symlinks pointing outside)
    bundle_symlinks = []
    if BUNDLE_DIR.exists():
        for item in BUNDLE_DIR.rglob("*"):
            if item.is_symlink():
                target = item.resolve()
                if not str(target).startswith(str(BUNDLE_DIR)):
                    bundle_symlinks.append({"symlink": str(item), "target": str(target)})
    checks.append({
        "subcheck": "Q1_BUNDLE_NO_EXTERNAL_SYMLINKS",
        "passed": len(bundle_symlinks) == 0,
        "symlinks": bundle_symlinks,
    })

    # 2. Verify bundle does not contain .git metadata
    git_in_bundle = []
    if BUNDLE_DIR.exists():
        for item in BUNDLE_DIR.rglob("*"):
            if ".git" in str(item):
                git_in_bundle.append(str(item))
    checks.append({
        "subcheck": "Q2_BUNDLE_NO_GIT_METADATA",
        "passed": len(git_in_bundle) == 0,
        "found": git_in_bundle,
    })

    # 3. Verify bundle does not contain case files
    case_files_in_bundle = []
    if BUNDLE_DIR.exists():
        for item in BUNDLE_DIR.rglob("DSB-*.json"):
            case_files_in_bundle.append(str(item))
    checks.append({
        "subcheck": "Q3_BUNDLE_NO_CASE_FILES",
        "passed": len(case_files_in_bundle) == 0,
        "found": case_files_in_bundle,
    })

    # 4. Verify bundle does not contain receipts or scores
    receipts_scores_in_bundle = []
    if BUNDLE_DIR.exists():
        for item in BUNDLE_DIR.rglob("*"):
            if "receipt" in item.name.lower() or "score" in item.name.lower():
                if item.name != "cto_adjudication_template.json":
                    receipts_scores_in_bundle.append(str(item))
    checks.append({
        "subcheck": "Q4_BUNDLE_NO_RECEIPTS_OR_SCORES",
        "passed": len(receipts_scores_in_bundle) == 0,
        "found": receipts_scores_in_bundle,
    })

    # 5. Verify bundle does not contain vault keys
    vault_in_bundle = []
    if BUNDLE_DIR.exists():
        for item in BUNDLE_DIR.rglob("*"):
            if "vault" in item.name.lower() or "key" in item.name.lower():
                vault_in_bundle.append(str(item))
    checks.append({
        "subcheck": "Q5_BUNDLE_NO_VAULT_KEYS",
        "passed": len(vault_in_bundle) == 0,
        "found": vault_in_bundle,
    })

    # 6. Verify bundle does not contain full packets
    full_in_bundle = []
    if BUNDLE_DIR.exists():
        for item in BUNDLE_DIR.rglob("*"):
            if "FULL" in item.name or "full" in item.name.lower():
                full_in_bundle.append(str(item))
    checks.append({
        "subcheck": "Q6_BUNDLE_NO_FULL_PACKETS",
        "passed": len(full_in_bundle) == 0,
        "found": full_in_bundle,
    })

    # 7. The CRITICAL check: can the adjudicator process read the research repo?
    # In this environment (single-user), YES — the adjudicator has the same UID.
    # This is ENVIRONMENT_BLOCKED — it requires a separate OS identity.
    repo_accessible = os.access(REPO, os.R_OK)
    checks.append({
        "subcheck": "Q7_ADJUDICATOR_CANNOT_READ_RESEARCH_REPO",
        "passed": not repo_accessible,
        "status": "ENVIRONMENT_BLOCKED" if repo_accessible else "PASS",
        "reason": "Single-user container — adjudicator has same UID as repository owner. Cannot enforce OS-level read restriction." if repo_accessible else "Adjudicator cannot read research repository (OS-enforced).",
    })

    # 8. Can the adjudicator read Git objects?
    git_dir = REPO / ".git"
    git_accessible = os.access(git_dir, os.R_OK) if git_dir.exists() else False
    checks.append({
        "subcheck": "Q8_ADJUDICATOR_CANNOT_READ_GIT_OBJECTS",
        "passed": not git_accessible,
        "status": "ENVIRONMENT_BLOCKED" if git_accessible else "PASS",
        "reason": "Single-user container — .git/ is readable by same UID." if git_accessible else "",
    })

    # 9. Can the adjudicator read case files?
    cases_dir = REPO / "discovery_fabric/dsb_v1/cases"
    cases_accessible = os.access(cases_dir, os.R_OK) if cases_dir.exists() else False
    checks.append({
        "subcheck": "Q9_ADJUDICATOR_CANNOT_READ_CASE_FILES",
        "passed": not cases_accessible,
        "status": "ENVIRONMENT_BLOCKED" if cases_accessible else "PASS",
        "reason": "Single-user container — case files readable by same UID." if cases_accessible else "",
    })

    # 10. Can the adjudicator read evaluator boundary?
    eval_dir = V3_DIR / "evaluator_boundary"
    eval_accessible = os.access(eval_dir, os.R_OK) if eval_dir.exists() else False
    checks.append({
        "subcheck": "Q10_ADJUDICATOR_CANNOT_READ_EVALUATOR_BOUNDARY",
        "passed": not eval_accessible,
        "status": "ENVIRONMENT_BLOCKED" if eval_accessible else "PASS",
        "reason": "Single-user container — evaluator boundary readable by same UID." if eval_accessible else "",
    })

    # Summary
    n_subchecks = len(checks)
    n_passed = sum(1 for c in checks if c["passed"])
    n_env_blocked = sum(1 for c in checks if c.get("status") == "ENVIRONMENT_BLOCKED")
    n_failed = n_subchecks - n_passed - n_env_blocked

    # Q passes ONLY if ALL subchecks pass AND no ENVIRONMENT_BLOCKED
    # (ENVIRONMENT_BLOCKED = cannot execute = blocking)
    all_executable_pass = all(c["passed"] for c in checks if c.get("status") != "ENVIRONMENT_BLOCKED")
    no_env_blocked = n_env_blocked == 0

    return {
        "check": "Q_RESEARCH_REPO_INACCESSIBLE_TO_ADJUDICATOR",
        "passed": all_executable_pass and no_env_blocked,
        "blocking": True,
        "executable_test": n_env_blocked == 0,  # cannot fully execute if env-blocked
        "status": "ENVIRONMENT_BLOCKED" if n_env_blocked > 0 else ("PASS" if all_executable_pass else "FAIL"),
        "n_subchecks": n_subchecks,
        "n_passed": n_passed,
        "n_environment_blocked": n_env_blocked,
        "n_failed": n_failed,
        "subchecks": checks,
        "description": "Proves the adjudicator process cannot read the research repo, Git objects, case files, or evaluator namespace. Requires separate OS identity/container.",
    }


# =============================================================================
# Step 3: Run full V7 preflight (V6 checks + Q)
# =============================================================================

def run_v7_preflight(bundle_manifest: dict) -> dict:
    """Run the V7 preflight: all V6 checks + Q."""
    # Import V6 checks
    sys.path.insert(0, str(CORRECTION_DIR))
    from run_v6_preflight import (
        check_H1, check_H2_true_forbidden_audit, check_H3, check_H4,
        check_B_environment_blocked, check_C_environment_blocked,
        check_D_vault_exists, check_E_recursive_blind_inspection,
        check_F_recursive_namespace, check_I, check_J, check_K, check_L,
        check_M_deterministic_manifest, check_N,
        check_O_environment_blocked, check_P_vault_encrypted,
        evaluate_hard_invariant,
    )

    checks = [
        check_H1(),
        check_H2_true_forbidden_audit(),
        check_H3(),
        check_H4(),
        check_B_environment_blocked(),
        check_C_environment_blocked(),
        check_D_vault_exists(),
        check_E_recursive_blind_inspection(),
        check_F_recursive_namespace(),
        check_I(),
        check_J(),
        check_K(),
        check_L(),
        check_M_deterministic_manifest(),
        check_N(),
        check_O_environment_blocked(),
        check_P_vault_encrypted(),
        check_Q_research_repo_inaccessible(),  # NEW V7 check
    ]

    invariant = evaluate_hard_invariant(checks)
    return {"checks": checks, "hard_invariant": invariant}


# =============================================================================
# Main
# =============================================================================

def main():
    print("=" * 72)
    print("SECURITY FORENSIC V7 — FINAL BOUNDARY CORRECTION")
    print("=" * 72)
    print()

    # Step 1: Build adjudicator bundle
    print("[1/3] Building minimal adjudicator bundle...")
    bundle_manifest = build_adjudicator_bundle()
    print(f"  Bundle created: {BUNDLE_DIR}")
    print(f"  Files in bundle: {len(bundle_manifest['files'])}")
    for fname, fmeta in bundle_manifest["files"].items():
        print(f"    - {fname} ({fmeta['size_bytes']} bytes, sha256={fmeta['sha256'][:16]}...)")
    print(f"  Forbidden files check: {'PASS' if bundle_manifest['forbidden_files_check']['passed'] else 'FAIL'}")

    # Step 2: Run Q check
    print(f"\n[2/3] Running Q_RESEARCH_REPO_INACCESSIBLE_TO_ADJUDICATOR...")
    q_result = check_Q_research_repo_inaccessible()
    print(f"  Status: {q_result['status']}")
    print(f"  Subchecks: {q_result['n_passed']}/{q_result['n_subchecks']} PASS, {q_result['n_environment_blocked']} ENV_BLOCKED")
    for sc in q_result["subchecks"]:
        icon = "✓" if sc["passed"] else ("⚠" if sc.get("status") == "ENVIRONMENT_BLOCKED" else "✗")
        print(f"    {icon} {sc['subcheck']}")

    # Step 3: Run full V7 preflight
    print(f"\n[3/3] Running full V7 preflight (V6 + Q)...")
    preflight = run_v7_preflight(bundle_manifest)

    invariant = preflight["hard_invariant"]
    print(f"\n  Hard invariant: {invariant['invariant']}")
    print(f"  Adjudication permitted: {invariant['adjudication_permitted']}")
    print(f"  Verdict: {invariant['verdict']}")
    print(f"  Block reasons: {len(invariant['block_reasons'])}")
    for r in invariant["block_reasons"]:
        print(f"    - {r}")

    # Print check table
    print(f"\n{'Check':<50} {'Status':<20} {'Exec':<5} {'Pass':<5}")
    print("-" * 85)
    for c in preflight["checks"]:
        status = c.get("status", "PASS" if c.get("passed") else "FAIL")
        if c.get("passed"):
            status = "PASS"
        exec_str = "Y" if c.get("executable_test") else "N"
        pass_str = "Y" if c.get("passed") else "N"
        print(f"{c['check']:<50} {status:<20} {exec_str:<5} {pass_str:<5}")

    # Save results
    results = {
        "schema_version": "7.0.0",
        "forensic_type": "SECURITY_FORENSIC_V7_FINAL_BOUNDARY",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "bundle_manifest": bundle_manifest,
        "q_check": q_result,
        "preflight": preflight,
        "adjudication_permitted": invariant["adjudication_permitted"],
        "verdict": invariant["verdict"],
        "v7_is_green": False,
        "environment": "single-user container (UID 1001, no root, no Docker)",
        "note": "V7 adds Q_RESEARCH_REPO_INACCESSIBLE_TO_ADJUDICATOR. Adjudicator bundle is minimal and self-contained. Environment remains BLOCKED. B/C/D/P/O/Q all required to pass in multi-identity deployment.",
    }
    canonical = json.dumps(results, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    results["hash"] = hashlib.sha256(canonical.encode()).hexdigest()
    with open(CORRECTION_DIR / "v7_preflight_results.json", "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # Write report
    report = f"""# SECURITY FORENSIC V7 — FINAL BOUNDARY CORRECTION REPORT

**Date:** {datetime.now(timezone.utc).isoformat()}
**Verdict:** BLOCKED — environment remains blocked
**V7 is green:** NO

## 1. Adjudicator Bundle

A minimal adjudicator bundle has been created at `discovery_fabric/dsb_v1/adjudicator_bundle/`.

### Bundle contents (ONLY):
"""
    for fname, fmeta in bundle_manifest["files"].items():
        report += f"- `{fname}` ({fmeta['size_bytes']} bytes, SHA-256: `{fmeta['sha256'][:32]}...`) — {fmeta['description']}\n"
    report += f"""

### Bundle MUST NOT contain:
"""
    for item in bundle_manifest["forbidden_contents"]:
        report += f"- {item}\n"
    report += f"""

### Forbidden files check: {'PASS' if bundle_manifest['forbidden_files_check']['passed'] else 'FAIL'}"

## 2. Q_RESEARCH_REPO_INACCESSIBLE_TO_ADJUDICATOR (NEW)

Q is a mandatory blocking prerequisite. It proves the adjudicator process cannot read:
- The research repository
- Git objects (.git/)
- Case files (cases/real/, cases/fabricated/)
- Evaluator namespace (evaluator_boundary/)
- Receipts and scores
- The frozen scorer

### Q subcheck results:

| Subcheck | Status |
|---|---|
"""
    for sc in q_result["subchecks"]:
        status = "PASS" if sc["passed"] else ("ENV_BLOCKED" if sc.get("status") == "ENVIRONMENT_BLOCKED" else "FAIL")
        report += f"| {sc['subcheck']} | {status} |\n"
    report += f"""

**Q overall: {q_result['status']}** ({q_result['n_passed']}/{q_result['n_subchecks']} subchecks pass, {q_result['n_environment_blocked']} environment-blocked)

## 3. Full V7 Preflight (V6 checks + Q)

| Check | Status | Executable | Passed | Blocking |
|---|---|---|---|---|
"""
    for c in preflight["checks"]:
        status = "PASS" if c.get("passed") else ("ENV_BLOCKED" if c.get("status") == "ENVIRONMENT_BLOCKED" else "FAIL")
        report += f"| {c['check']} | {status} | {'Y' if c.get('executable_test') else 'N'} | {'Y' if c.get('passed') else 'N'} | {'Y' if c.get('blocking') else 'N'} |\n"

    report += f"""

## 4. Hard Invariant

```
adjudication_permitted == TRUE
ONLY IF every required check has:
  executable_test == true
  passed == true
```

**Result:** {invariant['adjudication_permitted']} — {invariant['verdict']}

## 5. Block Reasons

"""
    for r in invariant["block_reasons"]:
        report += f"- {r}\n"

    report += f"""

## 6. Deployment Architecture

```
┌──────────────────────────────┐         ┌──────────────────────────────┐
│  ADJUDICATOR MACHINE         │         │  EVALUATOR MACHINE           │
│  (separate OS user/container)│         │  (separate OS user/container)│
│                              │         │                              │
│  Has: adjudicator_bundle/    │         │  Has: research repo +        │
│    - cto_packets_BLIND.json  │         │    - case files              │
│    - instructions            │         │    - receipts/ scores/       │
│    - empty template          │         │    - evaluator_boundary/     │
│    - BUNDLE_MANIFEST.json    │         │    - vault key               │
│                              │         │    - frozen scorer           │
│  Does NOT have:              │         │    - .git/                   │
│    - research repo ✗         │         │                              │
│    - .git/ ✗                 │         │  Cannot access:              │
│    - case files ✗            │         │    - adjudicator_bundle/     │
│    - evaluator_boundary/ ✗   │         │      (until ledger sealed)   │
│    - receipts/ scores/ ✗     │         │                              │
│    - vault key ✗             │         │                              │
│    - scorer.py ✗             │         │                              │
│                              │         │                              │
│  Network: isolated           │         │  Network: isolated           │
└──────────────────────────────┘         └──────────────────────────────┘
```

The adjudicator bundle is a SELF-CONTAINED artifact. It is extracted to a
separate machine/container that has ZERO access to the research repository.
The adjudicator cannot read Git objects, case files, evaluator boundary,
receipts, scores, or the scorer.

## 7. What Is Required

Only after **B/C/D/P/O/Q all pass** in a true multi-identity deployment can
the 80 adjudications begin:

- **B**: Adjudicator cannot read vault key (OS-enforced, separate user)
- **C**: Adjudicator cannot write evaluator boundary (OS-enforced)
- **D**: Encrypted vault exists (freshly generated with new key)
- **O**: No access to evaluator process (separate users, ptrace checks)
- **P**: Vault is encrypted (AES-GCM authenticated)
- **Q**: Research repo inaccessible to adjudicator (separate machine/container)

## 8. What Was NOT Modified

- DSB V1 cases (20 files): NOT modified
- DSB V1 prompts: NOT modified
- DSB V1 receipts (80 files): NOT modified
- DSB V1 scorer: NOT modified
- FREEZE_MANIFEST.json: NOT modified
- Research repository: NOT modified

---

**V7 is NOT green. Environment remains BLOCKED. The adjudicator bundle is ready for deployment to a separate machine. STOP.**
"""
    with open(CORRECTION_DIR / "SECURITY_FORENSIC_V7_REPORT.md", "w") as f:
        f.write(report)

    print(f"\nReport: {CORRECTION_DIR / 'SECURITY_FORENSIC_V7_REPORT.md'}")
    print(f"\nV7 is NOT green. Environment remains BLOCKED. STOP.")


if __name__ == "__main__":
    main()
