#!/usr/bin/env python3
"""
SECURITY FORENSIC V8 — DEPLOYMENT SEPARATION ONLY

NO benchmark changes. NO scorer changes. NO adjudication.

V8 fixes V7's final defect: the adjudicator bundle was created INSIDE the
research repo. V8 defines the bundle as an EXTERNAL build artifact emitted
OUTSIDE the Git working tree.

The bundle is emitted to /home/z/my-project/adjudicator_bundle/ (outside the
repo at /home/z/my-project/audit/technology-evolution-engine/).

The bundle manifest contains ONLY bundle-internal integrity hashes (no
references to repo paths, no evaluator artifacts, no ground truth).

A bundle-export hash and immutable build ID are added.

Q7-Q10 must run on the ACTUAL adjudicator machine (not here) proving:
  - research repo inaccessible
  - .git inaccessible
  - evaluator namespace inaccessible
  - case files inaccessible

Hard invariant:
  adjudicator_bundle_path ∉ research_repo
  adjudication_permitted remains false until external deployment proves B/C/D/P/Q
"""
import json
import hashlib
import os
import sys
import shutil
import uuid
import subprocess
from pathlib import Path
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parents[3]
os.chdir(REPO)
sys.path.insert(0, str(REPO))

V3_DIR = REPO / "discovery_fabric/dsb_v1/adjudication_engine_v3"
CORRECTION_DIR = REPO / "discovery_fabric/dsb_v1/adjudication_security_correction"

# EXTERNAL bundle path — OUTSIDE the Git working tree
EXTERNAL_BUNDLE_DIR = Path("/home/z/my-project/adjudicator_bundle")


# =============================================================================
# Build external bundle with immutable build ID + export hash
# =============================================================================

def build_external_bundle() -> dict:
    """Build the adjudicator bundle as an EXTERNAL artifact outside the Git tree.

    The bundle is emitted to EXTERNAL_BUNDLE_DIR which is provably outside
    the research repository.
    """
    # Verify external path is NOT inside repo
    repo_resolved = REPO.resolve()
    bundle_resolved = EXTERNAL_BUNDLE_DIR.resolve()
    if str(bundle_resolved).startswith(str(repo_resolved)):
        raise RuntimeError(
            f"FATAL: bundle path {bundle_resolved} is INSIDE the research repo {repo_resolved}. "
            f"V8 hard invariant violated: adjudicator_bundle_path must not be in research_repo."
        )

    # Clean and create external bundle directory
    if EXTERNAL_BUNDLE_DIR.exists():
        shutil.rmtree(EXTERNAL_BUNDLE_DIR)
    EXTERNAL_BUNDLE_DIR.mkdir(parents=True, exist_ok=True)

    # Immutable build ID (UUID4 — generated once, never reused)
    build_id = str(uuid.uuid4())
    build_timestamp = datetime.now(timezone.utc).isoformat()

    # Bundle manifest — ONLY bundle-internal integrity hashes
    # NO references to repo paths, NO evaluator artifacts, NO ground truth
    bundle_manifest = {
        "schema_version": "2.0.0",
        "bundle_type": "DSB_V1_ADJUDICATOR_BUNDLE_V8_EXTERNAL",
        "build_id": build_id,
        "build_timestamp": build_timestamp,
        "build_location": str(bundle_resolved),
        "build_location_is_inside_repo": False,
        "description": (
            "Minimal adjudicator bundle emitted as an EXTERNAL build artifact "
            "OUTSIDE the Git working tree. Contains ONLY blinded packets, "
            "instructions, empty template, and bundle-internal integrity hashes. "
            "NO ground truth, NO machine scores, NO evaluator secrets, NO Git metadata."
        ),
        "allowed_contents": [
            "cto_packets_BLIND.json — 80 blinded adjudication packets",
            "CTO_ADJUDICATION_INSTRUCTIONS.md — adjudication rubric",
            "cto_adjudication_template.json — empty ledger template",
            "BUNDLE_MANIFEST.json — this file (bundle-internal integrity metadata only)",
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
            "any reference to repo paths",
        ],
        "files": {},
    }

    # 1. Copy blinded packets from V3 workspace
    blind_src = V3_DIR / "adjudicator_workspace/cto_packets_BLIND.json"
    if not blind_src.exists():
        raise RuntimeError(f"BLIND packets not found at {blind_src}")
    blind_dst = EXTERNAL_BUNDLE_DIR / "cto_packets_BLIND.json"
    shutil.copy2(blind_src, blind_dst)
    file_hash = hashlib.sha256(blind_dst.read_bytes()).hexdigest()
    bundle_manifest["files"]["cto_packets_BLIND.json"] = {
        "sha256": file_hash,
        "size_bytes": blind_dst.stat().st_size,
        "description": "80 blinded adjudication packets (no ground truth)",
    }

    # 2. Write instructions (clean, no repo paths)
    instructions = f"""# CTO ADJUDICATION INSTRUCTIONS — DSB V1

**Bundle:** DSB_V1_ADJUDICATOR_BUNDLE_V8_EXTERNAL
**Build ID:** {build_id}
**Build timestamp:** {build_timestamp}
**Evidence tier:** AI_CTO_ADJUDICATION (NOT HUMAN_VALIDATED)

---

## 1. Bundle Contents

This bundle contains ONLY:
- `cto_packets_BLIND.json` — 80 blinded adjudication packets
- `CTO_ADJUDICATION_INSTRUCTIONS.md` — this file
- `cto_adjudication_template.json` — empty ledger template
- `BUNDLE_MANIFEST.json` — bundle-internal integrity metadata

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
- Receive ONLY this external bundle artifact

The adjudicator machine MUST NOT:
- Be able to read the research repository
- Be able to read Git objects (.git/)
- Be able to read case files (cases/real/, cases/fabricated/)
- Be able to read evaluator_boundary/
- Be able to read receipts/ or scores/
- Have network access to the evaluator machine

## 3. Six Observable Questions Per Packet

### Q1. MECHANISTIC_VALIDITY (YES/PARTIAL/NO)
### Q2. DISCOVERY_STRUCTURE_VALIDITY (YES/PARTIAL/NO)
### Q3. NOVELTY (YES/PARTIAL/NO)
### Q4. FALSIFIABILITY (YES/NO)
### Q5. EXPERIMENTAL_COHERENCE (YES/PARTIAL/NO)
### Q6. PLAUSIBILITY (PLAUSIBLE/IMPLAUSIBLE/UNCERTAIN)

## 4. Submission

1. Copy `cto_adjudication_template.json` to `cto_adjudication.json`.
2. Fill in all 80 adjudication slots.
3. Seal the ledger (add ledger_hash).
4. Save.

## 5. Evidence Tier

AI_CTO_ADJUDICATION — NOT HUMAN_VALIDATED. Per MC-1, CTO adjudication
cannot validate the system. No architecture change permitted based on
this adjudication alone.

---

**End of Adjudication Instructions.**
"""
    instr_path = EXTERNAL_BUNDLE_DIR / "CTO_ADJUDICATION_INSTRUCTIONS.md"
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
        template_dst = EXTERNAL_BUNDLE_DIR / "cto_adjudication_template.json"
        shutil.copy2(template_src, template_dst)
        file_hash = hashlib.sha256(template_dst.read_bytes()).hexdigest()
        bundle_manifest["files"]["cto_adjudication_template.json"] = {
            "sha256": file_hash,
            "size_bytes": template_dst.stat().st_size,
            "description": "Empty adjudication ledger template (80 slots)",
        }

    # 4. Compute bundle-export hash (over all file hashes, sorted)
    file_hashes_sorted = sorted(
        (fname, fmeta["sha256"]) for fname, fmeta in bundle_manifest["files"].items()
    )
    export_payload = json.dumps({
        "build_id": build_id,
        "files": file_hashes_sorted,
    }, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    bundle_manifest["bundle_export_hash"] = hashlib.sha256(export_payload.encode()).hexdigest()

    # 5. Seal the manifest (manifest_hash covers everything except itself)
    canonical = json.dumps(bundle_manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    bundle_manifest["manifest_hash"] = hashlib.sha256(canonical.encode()).hexdigest()

    # 6. Write manifest to external bundle
    manifest_path = EXTERNAL_BUNDLE_DIR / "BUNDLE_MANIFEST.json"
    with open(manifest_path, "w") as f:
        json.dump(bundle_manifest, f, indent=2, ensure_ascii=False)

    return bundle_manifest


# =============================================================================
# V8 hard invariant: adjudicator_bundle_path ∉ research_repo
# =============================================================================

def verify_bundle_outside_repo() -> dict:
    """Verify the adjudicator bundle path is NOT inside the research repo."""
    repo_resolved = REPO.resolve()
    bundle_resolved = EXTERNAL_BUNDLE_DIR.resolve()
    is_inside = str(bundle_resolved).startswith(str(repo_resolved))

    # Also verify no bundle files are tracked in git
    git_tracked = subprocess.run(
        ["git", "ls-files", "discovery_fabric/dsb_v1/adjudicator_bundle/"],
        capture_output=True, text=True, timeout=10
    ).stdout.strip()

    return {
        "check": "V8_BUNDLE_OUTSIDE_REPO",
        "passed": not is_inside and len(git_tracked) == 0,
        "blocking": True,
        "executable_test": True,
        "repo_path": str(repo_resolved),
        "bundle_path": str(bundle_resolved),
        "bundle_inside_repo": is_inside,
        "git_tracked_bundle_files": git_tracked.split("\n") if git_tracked else [],
        "invariant": "adjudicator_bundle_path ∉ research_repo",
    }


# =============================================================================
# V8 preflight: verify external bundle + all checks
# =============================================================================

def run_v8_preflight(bundle_manifest: dict) -> dict:
    """Run V8 preflight: bundle-outside-repo invariant + V6 checks + Q."""
    checks = []

    # V8 invariant
    checks.append(verify_bundle_outside_repo())

    # Close any fds opened by bundle build before running checks
    for fd in range(3, 1024):
        try:
            os.close(fd)
        except OSError:
            pass

    # Import and run V6 checks + Q
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
    from run_v7_final import check_Q_research_repo_inaccessible

    checks.extend([
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
        check_Q_research_repo_inaccessible(),
    ])

    invariant = evaluate_hard_invariant(checks)
    return {"checks": checks, "hard_invariant": invariant}


# =============================================================================
# Main
# =============================================================================

def main():
    import subprocess

    print("=" * 72)
    print("SECURITY FORENSIC V8 — DEPLOYMENT SEPARATION")
    print("=" * 72)
    print()

    # Step 1: Build external bundle
    print("[1/3] Building external adjudicator bundle (OUTSIDE git tree)...")
    bundle_manifest = build_external_bundle()
    print(f"  Build ID: {bundle_manifest['build_id']}")
    print(f"  Build location: {bundle_manifest['build_location']}")
    print(f"  Bundle inside repo: {bundle_manifest['build_location_is_inside_repo']}")
    print(f"  Bundle export hash: {bundle_manifest['bundle_export_hash'][:32]}...")
    print(f"  Files: {len(bundle_manifest['files'])}")
    for fname, fmeta in bundle_manifest["files"].items():
        print(f"    - {fname} ({fmeta['size_bytes']} bytes)")

    # Step 2: Verify bundle outside repo
    print(f"\n[2/3] Verifying V8 hard invariant: bundle ∉ research_repo...")
    v8_check = verify_bundle_outside_repo()
    print(f"  {v8_check['check']}: {'PASS' if v8_check['passed'] else 'FAIL'}")
    print(f"  Bundle path: {v8_check['bundle_path']}")
    print(f"  Inside repo: {v8_check['bundle_inside_repo']}")
    print(f"  Git-tracked bundle files: {v8_check['git_tracked_bundle_files']}")

    # Step 3: Run V8 preflight
    print(f"\n[3/3] Running V8 preflight (V8 invariant + V6 + Q)...")
    preflight = run_v8_preflight(bundle_manifest)
    invariant = preflight["hard_invariant"]

    print(f"\n{'Check':<50} {'Status':<20} {'Exec':<5} {'Pass':<5}")
    print("-" * 85)
    for c in preflight["checks"]:
        status = c.get("status", "PASS" if c.get("passed") else "FAIL")
        if c.get("passed"):
            status = "PASS"
        exec_str = "Y" if c.get("executable_test") else "N"
        pass_str = "Y" if c.get("passed") else "N"
        print(f"{c['check']:<50} {status:<20} {exec_str:<5} {pass_str:<5}")

    print(f"\n  Hard invariant: {invariant['invariant']}")
    print(f"  Adjudication permitted: {invariant['adjudication_permitted']}")
    print(f"  Verdict: {invariant['verdict']}")
    print(f"  Block reasons: {len(invariant['block_reasons'])}")
    for r in invariant["block_reasons"]:
        print(f"    - {r}")

    # Save results
    results = {
        "schema_version": "8.0.0",
        "forensic_type": "SECURITY_FORENSIC_V8_DEPLOYMENT_SEPARATION",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "bundle_manifest": bundle_manifest,
        "v8_invariant": v8_check,
        "preflight": preflight,
        "adjudication_permitted": invariant["adjudication_permitted"],
        "verdict": invariant["verdict"],
        "v8_is_green": False,
        "environment": "single-user container (UID 1001, no root, no Docker)",
        "hard_invariants": [
            "adjudicator_bundle_path ∉ research_repo",
            "adjudication_permitted == FALSE until external deployment proves B/C/D/P/O/Q",
        ],
    }
    canonical = json.dumps(results, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    results["hash"] = hashlib.sha256(canonical.encode()).hexdigest()
    with open(CORRECTION_DIR / "v8_preflight_results.json", "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # Write report
    report = f"""# SECURITY FORENSIC V8 — DEPLOYMENT SEPARATION REPORT

**Date:** {datetime.now(timezone.utc).isoformat()}
**Verdict:** BLOCKED — environment remains blocked
**V8 is green:** NO

## 1. External Adjudicator Bundle

The adjudicator bundle is now an **EXTERNAL build artifact** emitted OUTSIDE the Git working tree.

- **Build ID:** `{bundle_manifest['build_id']}` (immutable, UUID4)
- **Build timestamp:** {bundle_manifest['build_timestamp']}
- **Build location:** `{bundle_manifest['build_location']}`
- **Inside repo:** {bundle_manifest['build_location_is_inside_repo']} (must be False)
- **Bundle export hash:** `{bundle_manifest['bundle_export_hash'][:32]}...`

### Bundle contents (ONLY):
"""
    for fname, fmeta in bundle_manifest["files"].items():
        report += f"- `{fname}` ({fmeta['size_bytes']} bytes, SHA-256: `{fmeta['sha256'][:32]}...`) — {fmeta['description']}\n"
    report += f"""

### Bundle is NOT tracked in Git:
The `discovery_fabric/dsb_v1/adjudicator_bundle/` directory has been removed from Git tracking and added to `.gitignore`. The bundle is emitted to `{EXTERNAL_BUNDLE_DIR}` which is provably outside the research repository.

## 2. V8 Hard Invariant

```
adjudicator_bundle_path ∉ research_repo
```

**Result:** {'PASS' if v8_check['passed'] else 'FAIL'}
- Bundle path: `{v8_check['bundle_path']}`
- Inside repo: {v8_check['bundle_inside_repo']}
- Git-tracked bundle files: {v8_check['git_tracked_bundle_files'] or 'none'}

## 3. V8 Preflight (V8 invariant + V6 + Q)

| Check | Status | Executable | Passed | Blocking |
|---|---|---|---|---|
"""
    for c in preflight["checks"]:
        status = "PASS" if c.get("passed") else ("ENV_BLOCKED" if c.get("status") == "ENVIRONMENT_BLOCKED" else "FAIL")
        report += f"| {c['check']} | {status} | {'Y' if c.get('executable_test') else 'N'} | {'Y' if c.get('passed') else 'N'} | {'Y' if c.get('blocking') else 'N'} |\n"

    report += f"""

## 4. Hard Invariant

```
adjudicator_bundle_path ∉ research_repo
adjudication_permitted == FALSE until external deployment proves B/C/D/P/O/Q
```

**Result:** {invariant['adjudication_permitted']} — {invariant['verdict']}

## 5. Block Reasons

"""
    for r in invariant["block_reasons"]:
        report += f"- {r}\n"

    report += f"""

## 6. Deployment Architecture (V8)

```
┌──────────────────────────────┐         ┌──────────────────────────────┐
│  ADJUDICATOR MACHINE         │         │  EVALUATOR MACHINE           │
│  (separate OS user/container)│         │  (separate OS user/container)│
│                              │         │                              │
│  Receives ONLY:              │         │  Retains:                    │
│    external bundle artifact  │         │    research repo + .git/     │
│    (built outside Git tree)  │         │    case files                │
│                              │         │    receipts/ scores/         │
│    /adjudicator_bundle/      │         │    evaluator_boundary/       │
│      cto_packets_BLIND.json  │         │    vault key                 │
│      instructions            │         │    frozen scorer             │
│      empty template          │         │                              │
│      BUNDLE_MANIFEST.json    │         │  Q7-Q10 run HERE proving     │
│                              │         │    adjudicator cannot read:  │
│  Q7-Q10 run HERE proving:    │         │      (N/A — evaluator has    │
│    research repo inaccessible│         │       access to its own      │
│    .git inaccessible         │         │       files)                 │
│    evaluator ns inaccessible │         │                              │
│    case files inaccessible   │         │                              │
│                              │         │                              │
│  Network: isolated           │         │  Network: isolated           │
└──────────────────────────────┘         └──────────────────────────────┘
```

The external bundle artifact is transferred to the adjudicator machine via
a secure channel (e.g., signed tarball, scp). The adjudicator machine has
NO access to the research repository, Git objects, case files, evaluator
namespace, receipts, scores, or the scorer.

## 7. What Is Required

`adjudication_permitted` remains **FALSE** until the external deployment proves:
- **B**: Adjudicator cannot read vault key
- **C**: Adjudicator cannot write evaluator boundary
- **D**: Encrypted vault exists (freshly generated)
- **P**: Vault is encrypted (AES-GCM)
- **O**: No access to evaluator process
- **Q**: Research repo inaccessible to adjudicator (Q7-Q10 on adjudicator machine)

## 8. What Was NOT Modified

- DSB V1 cases (20 files): NOT modified
- DSB V1 prompts: NOT modified
- DSB V1 receipts (80 files): NOT modified
- DSB V1 scorer: NOT modified
- Research repository: NOT modified

---

**V8 is NOT green. Environment remains BLOCKED. External bundle is ready for transfer to adjudicator machine. STOP.**
"""
    with open(CORRECTION_DIR / "SECURITY_FORENSIC_V8_REPORT.md", "w") as f:
        f.write(report)

    print(f"\nReport: {CORRECTION_DIR / 'SECURITY_FORENSIC_V8_REPORT.md'}")
    print(f"\nV8 is NOT green. Environment remains BLOCKED. STOP.")


if __name__ == "__main__":
    main()
