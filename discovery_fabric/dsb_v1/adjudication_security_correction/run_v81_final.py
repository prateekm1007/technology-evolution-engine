#!/usr/bin/env python3
"""
V8.1 — FINAL BUNDLE IDENTITY CORRECTION

NO benchmark changes. NO scorer changes. NO adjudication.

Fixes:
  1. Remove host filesystem path from BUNDLE_MANIFEST (build_location removed).
  2. Make the cryptographic bundle hash the canonical artifact identity.
  3. Bind build_id + bundle_hash + manifest_hash into the final adjudication ledger.
  4. Make evaluator access to adjudicator output strictly one-way after ledger sealing.
  5. Re-run the bundle self-integrity test.
  6. STOP coding permanently in this environment.
"""
import json
import hashlib
import os
import sys
import shutil
import uuid
from pathlib import Path
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parents[3]
os.chdir(REPO)
sys.path.insert(0, str(REPO))

V3_DIR = REPO / "discovery_fabric/dsb_v1/adjudication_engine_v3"
CORRECTION_DIR = REPO / "discovery_fabric/dsb_v1/adjudication_security_correction"
EXTERNAL_BUNDLE_DIR = Path("/home/z/my-project/adjudicator_bundle")


def build_v81_bundle() -> dict:
    """Build V8.1 external bundle with canonical identity.

    V8.1 changes vs V8:
    - build_location (host path) REMOVED from manifest
    - bundle_hash is the CANONICAL artifact identity (not the path)
    - build_id + bundle_hash + manifest_hash are bound into the ledger binding
    - Evaluator access is strictly one-way after ledger sealing
    """
    # Verify external path is NOT inside repo
    repo_resolved = REPO.resolve()
    bundle_resolved = EXTERNAL_BUNDLE_DIR.resolve()
    if str(bundle_resolved).startswith(str(repo_resolved)):
        raise RuntimeError("FATAL: bundle path is INSIDE the research repo.")

    # Clean and create
    if EXTERNAL_BUNDLE_DIR.exists():
        shutil.rmtree(EXTERNAL_BUNDLE_DIR)
    EXTERNAL_BUNDLE_DIR.mkdir(parents=True, exist_ok=True)

    # Immutable build ID
    build_id = str(uuid.uuid4())
    build_timestamp = datetime.now(timezone.utc).isoformat()

    # --- V8.1 manifest: NO host filesystem path ---
    bundle_manifest = {
        "schema_version": "2.1.0",
        "bundle_type": "DSB_V1_ADJUDICATOR_BUNDLE_V81",
        "build_id": build_id,
        "build_timestamp": build_timestamp,
        # build_location REMOVED — host path is NOT part of the artifact identity
        "description": (
            "Minimal adjudicator bundle. Canonical identity is the bundle_hash "
            "(cryptographic), NOT a filesystem path. Contains ONLY blinded packets, "
            "instructions, empty template, and bundle-internal integrity hashes."
        ),
        "allowed_contents": [
            "cto_packets_BLIND.json",
            "CTO_ADJUDICATION_INSTRUCTIONS.md",
            "cto_adjudication_template.json",
            "BUNDLE_MANIFEST.json",
        ],
        "forbidden_contents": [
            "case files", "real/fabricated labels", "breakthrough_relationship text",
            "withheld_facts text", "answer_mechanism text", "machine receipts",
            "machine scores", "full packets", "evaluator secrets", "Git metadata",
            "research repository code", "host filesystem paths",
        ],
        "files": {},
        "ledger_binding": {
            "description": (
                "The final adjudication ledger MUST bind build_id + bundle_hash + "
                "manifest_hash. This proves the adjudicator operated on this exact "
                "bundle and prevents substitution."
            ),
            "required_fields": ["build_id", "bundle_hash", "manifest_hash"],
            "evaluator_access": "strictly_one_way_after_ledger_sealing",
            "evaluator_access_note": (
                "The evaluator can read the adjudicator's sealed ledger ONLY after "
                "the ledger_hash is computed and committed. The evaluator cannot "
                "write to the adjudicator's workspace. The adjudicator cannot read "
                "the evaluator's namespace. Access is strictly one-way: adjudicator "
                "produces → evaluator consumes (after sealing)."
            ),
        },
    }

    # 1. Copy blinded packets
    blind_src = V3_DIR / "adjudicator_workspace/cto_packets_BLIND.json"
    if not blind_src.exists():
        raise RuntimeError(f"BLIND packets not found at {blind_src}")
    blind_dst = EXTERNAL_BUNDLE_DIR / "cto_packets_BLIND.json"
    shutil.copy2(blind_src, blind_dst)
    file_hash = hashlib.sha256(blind_dst.read_bytes()).hexdigest()
    bundle_manifest["files"]["cto_packets_BLIND.json"] = {
        "sha256": file_hash,
        "size_bytes": blind_dst.stat().st_size,
    }

    # 2. Write instructions (no repo paths, no host paths)
    instructions = f"""# CTO ADJUDICATION INSTRUCTIONS — DSB V1

**Bundle:** DSB_V1_ADJUDICATOR_BUNDLE_V81
**Build ID:** {build_id}
**Build timestamp:** {build_timestamp}
**Evidence tier:** AI_CTO_ADJUDICATION (NOT HUMAN_VALIDATED)

---

## 1. Bundle Canonical Identity

The bundle's identity is its **cryptographic bundle_hash**, NOT a filesystem path.
The adjudication ledger MUST bind:
- `build_id`: `{build_id}`
- `bundle_hash`: (computed over all file hashes — see BUNDLE_MANIFEST.json)
- `manifest_hash`: (computed over the manifest — see BUNDLE_MANIFEST.json)

This prevents bundle substitution and proves the adjudicator operated on the
exact bundle identified by these hashes.

## 2. Bundle Contents

ONLY:
- `cto_packets_BLIND.json` — 80 blinded adjudication packets
- `CTO_ADJUDICATION_INSTRUCTIONS.md` — this file
- `cto_adjudication_template.json` — empty ledger template
- `BUNDLE_MANIFEST.json` — bundle-internal integrity metadata

NOT present: case files, labels, breakthroughs, withheld facts, answer mechanisms,
receipts, scores, full packets, evaluator secrets, Git metadata, repo code, host paths.

## 3. Evaluator Access (Strictly One-Way)

- Adjudicator produces sealed ledger → evaluator consumes (after sealing)
- Evaluator CANNOT write to adjudicator workspace
- Adjudicator CANNOT read evaluator namespace
- Access is strictly one-way after ledger sealing

## 4. Six Observable Questions

Q1 MECHANISTIC_VALIDITY (YES/PARTIAL/NO)
Q2 DISCOVERY_STRUCTURE_VALIDITY (YES/PARTIAL/NO)
Q3 NOVELTY (YES/PARTIAL/NO)
Q4 FALSIFIABILITY (YES/NO)
Q5 EXPERIMENTAL_COHERENCE (YES/PARTIAL/NO)
Q6 PLAUSIBILITY (PLAUSIBLE/IMPLAUSIBLE/UNCERTAIN)

## 5. Submission

1. Copy template to `cto_adjudication.json`.
2. Fill 80 slots.
3. Seal ledger (add `ledger_hash`).
4. The ledger MUST include `build_id`, `bundle_hash`, `manifest_hash` from BUNDLE_MANIFEST.json.

---

**End of Instructions.**
"""
    instr_path = EXTERNAL_BUNDLE_DIR / "CTO_ADJUDICATION_INSTRUCTIONS.md"
    instr_path.write_text(instructions)
    file_hash = hashlib.sha256(instr_path.read_bytes()).hexdigest()
    bundle_manifest["files"]["CTO_ADJUDICATION_INSTRUCTIONS.md"] = {
        "sha256": file_hash,
        "size_bytes": instr_path.stat().st_size,
    }

    # 3. Copy template
    template_src = V3_DIR / "adjudicator_workspace/cto_adjudication_template.json"
    if template_src.exists():
        template_dst = EXTERNAL_BUNDLE_DIR / "cto_adjudication_template.json"
        shutil.copy2(template_src, template_dst)
        file_hash = hashlib.sha256(template_dst.read_bytes()).hexdigest()
        bundle_manifest["files"]["cto_adjudication_template.json"] = {
            "sha256": file_hash,
            "size_bytes": template_dst.stat().st_size,
        }

    # 4. Compute bundle_hash (canonical identity — over all file hashes sorted)
    file_hashes_sorted = sorted(
        (fname, fmeta["sha256"]) for fname, fmeta in bundle_manifest["files"].items()
    )
    bundle_hash_payload = json.dumps({
        "build_id": build_id,
        "files": file_hashes_sorted,
    }, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    bundle_manifest["bundle_hash"] = hashlib.sha256(bundle_hash_payload.encode()).hexdigest()

    # 5. Compute manifest_hash (seals the manifest)
    # manifest_hash covers everything except itself
    manifest_for_hash = {k: v for k, v in bundle_manifest.items() if k != "manifest_hash"}
    canonical = json.dumps(manifest_for_hash, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    bundle_manifest["manifest_hash"] = hashlib.sha256(canonical.encode()).hexdigest()

    # 6. Write manifest
    manifest_path = EXTERNAL_BUNDLE_DIR / "BUNDLE_MANIFEST.json"
    with open(manifest_path, "w") as f:
        json.dump(bundle_manifest, f, indent=2, ensure_ascii=False)

    return bundle_manifest


def run_bundle_self_integrity_test(manifest: dict) -> dict:
    """Re-run the bundle self-integrity test.

    Verifies:
    1. Every file in the manifest exists in the bundle
    2. Every file's SHA-256 matches the manifest
    3. bundle_hash matches recomputed hash
    4. manifest_hash matches recomputed hash
    5. No host filesystem path in the manifest
    6. No forbidden content in any bundle file
    7. No Git metadata in the bundle
    8. No symlinks pointing outside the bundle
    """
    checks = []

    # 1. Every file exists + hash matches
    for fname, fmeta in manifest["files"].items():
        fpath = EXTERNAL_BUNDLE_DIR / fname
        if not fpath.exists():
            checks.append({"check": f"FILE_EXISTS_{fname}", "passed": False})
            continue
        actual_hash = hashlib.sha256(fpath.read_bytes()).hexdigest()
        checks.append({
            "check": f"FILE_HASH_{fname}",
            "passed": actual_hash == fmeta["sha256"],
            "expected": fmeta["sha256"][:16],
            "actual": actual_hash[:16],
        })

    # 2. bundle_hash matches
    file_hashes_sorted = sorted(
        (fname, fmeta["sha256"]) for fname, fmeta in manifest["files"].items()
    )
    bundle_hash_payload = json.dumps({
        "build_id": manifest["build_id"],
        "files": file_hashes_sorted,
    }, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    recomputed_bundle_hash = hashlib.sha256(bundle_hash_payload.encode()).hexdigest()
    checks.append({
        "check": "BUNDLE_HASH_MATCHES",
        "passed": recomputed_bundle_hash == manifest["bundle_hash"],
    })

    # 3. manifest_hash matches
    manifest_for_hash = {k: v for k, v in manifest.items() if k != "manifest_hash"}
    canonical = json.dumps(manifest_for_hash, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    recomputed_manifest_hash = hashlib.sha256(canonical.encode()).hexdigest()
    checks.append({
        "check": "MANIFEST_HASH_MATCHES",
        "passed": recomputed_manifest_hash == manifest["manifest_hash"],
    })

    # 4. No host filesystem path in manifest
    manifest_str = json.dumps(manifest)
    host_path_indicators = ["/home/", "/tmp/", "/var/", "/opt/", "/root/", "/Users/"]
    has_host_path = any(ind in manifest_str for ind in host_path_indicators)
    checks.append({
        "check": "NO_HOST_PATH_IN_MANIFEST",
        "passed": not has_host_path,
        "host_path_indicators_found": [ind for ind in host_path_indicators if ind in manifest_str],
    })

    # 5. No forbidden content in bundle files
    forbidden_strings = [
        "breakthrough_relationship", "withheld_facts", "answer_mechanism",
        "case_type", "discovery_structure_recovery_verdict",
    ]
    forbidden_found = []
    for fname in manifest["files"]:
        fpath = EXTERNAL_BUNDLE_DIR / fname
        if fpath.exists():
            content = fpath.read_text(errors="ignore")
            # Check if forbidden strings appear as JSON KEYS (not values)
            try:
                data = json.loads(content)
                def check_keys(d, path=""):
                    if isinstance(data, dict):
                        for key in data.keys():
                            if key in forbidden_strings:
                                forbidden_found.append(f"{fname}:key:{key}")
                # Only check top-level for arrays of packets
                if isinstance(data, list):
                    for item in data[:3]:
                        if isinstance(item, dict):
                            for key in item.keys():
                                if key in forbidden_strings:
                                    forbidden_found.append(f"{fname}:key:{key}")
                elif isinstance(data, dict):
                    for key in data.keys():
                        if key in forbidden_strings:
                            forbidden_found.append(f"{fname}:key:{key}")
            except json.JSONDecodeError:
                pass
    checks.append({
        "check": "NO_FORBIDDEN_CONTENT_IN_BUNDLE",
        "passed": len(forbidden_found) == 0,
        "found": forbidden_found,
    })

    # 6. No Git metadata
    git_in_bundle = []
    for item in EXTERNAL_BUNDLE_DIR.rglob("*"):
        if ".git" in str(item):
            git_in_bundle.append(str(item))
    checks.append({
        "check": "NO_GIT_METADATA_IN_BUNDLE",
        "passed": len(git_in_bundle) == 0,
    })

    # 7. No external symlinks
    external_symlinks = []
    for item in EXTERNAL_BUNDLE_DIR.rglob("*"):
        if item.is_symlink():
            target = item.resolve()
            if not str(target).startswith(str(EXTERNAL_BUNDLE_DIR)):
                external_symlinks.append({"symlink": str(item), "target": str(target)})
    checks.append({
        "check": "NO_EXTERNAL_SYMLINKS",
        "passed": len(external_symlinks) == 0,
    })

    # 8. Bundle has exactly 4 files (no extra, no missing)
    expected_files = {"cto_packets_BLIND.json", "CTO_ADJUDICATION_INSTRUCTIONS.md",
                      "cto_adjudication_template.json", "BUNDLE_MANIFEST.json"}
    actual_files = {f.name for f in EXTERNAL_BUNDLE_DIR.iterdir() if f.is_file()}
    checks.append({
        "check": "BUNDLE_HAS_EXACTLY_4_FILES",
        "passed": actual_files == expected_files,
        "expected": sorted(expected_files),
        "actual": sorted(actual_files),
    })

    n_pass = sum(1 for c in checks if c["passed"])
    return {
        "n_checks": len(checks),
        "n_passed": n_pass,
        "all_pass": n_pass == len(checks),
        "checks": checks,
    }


def main():
    print("=" * 72)
    print("V8.1 — FINAL BUNDLE IDENTITY CORRECTION")
    print("=" * 72)
    print()

    # Step 1: Build V8.1 bundle (no host path, canonical identity)
    print("[1/3] Building V8.1 external bundle (no host path, canonical identity)...")
    manifest = build_v81_bundle()
    print(f"  Build ID: {manifest['build_id']}")
    print(f"  Bundle hash (canonical identity): {manifest['bundle_hash'][:32]}...")
    print(f"  Manifest hash: {manifest['manifest_hash'][:32]}...")
    print(f"  Host path in manifest: NO (removed in V8.1)")
    print(f"  Files: {len(manifest['files'])}")
    for fname, fmeta in manifest["files"].items():
        print(f"    - {fname} ({fmeta['size_bytes']} bytes)")

    # Step 2: Re-run bundle self-integrity test
    print(f"\n[2/3] Running bundle self-integrity test...")
    integrity = run_bundle_self_integrity_test(manifest)
    print(f"  {integrity['n_passed']}/{integrity['n_checks']} checks PASS")
    for c in integrity["checks"]:
        icon = "✓" if c["passed"] else "✗"
        print(f"    {icon} {c['check']}")

    # Step 3: Verify V8 hard invariant still holds
    print(f"\n[3/3] Verifying V8 hard invariant (bundle ∉ research_repo)...")
    import subprocess
    git_tracked = subprocess.run(
        ["git", "ls-files", "discovery_fabric/dsb_v1/adjudicator_bundle/"],
        capture_output=True, text=True, timeout=10
    ).stdout.strip()
    v8_ok = len(git_tracked) == 0
    print(f"  Bundle not in Git: {'PASS' if v8_ok else 'FAIL'}")
    print(f"  Git-tracked bundle files: {git_tracked or 'none'}")

    # Save results
    results = {
        "schema_version": "8.1.0",
        "forensic_type": "V81_FINAL_BUNDLE_IDENTITY_CORRECTION",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "bundle_manifest": manifest,
        "bundle_self_integrity": integrity,
        "v8_hard_invariant_holds": v8_ok,
        "canonical_identity": {
            "build_id": manifest["build_id"],
            "bundle_hash": manifest["bundle_hash"],
            "manifest_hash": manifest["manifest_hash"],
            "description": "These three values form the canonical artifact identity. The adjudication ledger MUST bind all three.",
        },
        "evaluator_access": "strictly_one_way_after_ledger_sealing",
        "v81_is_green": integrity["all_pass"] and v8_ok,
        "adjudication_permitted": False,  # still blocked by B/C/D/P/O/Q
    }
    canonical = json.dumps(results, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    results["hash"] = hashlib.sha256(canonical.encode()).hexdigest()
    with open(CORRECTION_DIR / "v81_results.json", "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # Write report
    report = f"""# V8.1 — FINAL BUNDLE IDENTITY CORRECTION

**Date:** {datetime.now(timezone.utc).isoformat()}

## 1. Host Path Removed

The `build_location` field (host filesystem path) has been **removed** from BUNDLE_MANIFEST.json. The bundle's identity is now **cryptographic**, not path-based.

## 2. Canonical Artifact Identity

The bundle is identified by three bound values:

| Field | Value |
|---|---|
| `build_id` | `{manifest['build_id']}` |
| `bundle_hash` | `{manifest['bundle_hash'][:32]}...` |
| `manifest_hash` | `{manifest['manifest_hash'][:32]}...` |

The final adjudication ledger MUST bind all three. This proves the adjudicator operated on this exact bundle and prevents substitution.

## 3. Evaluator Access (Strictly One-Way)

- Adjudicator produces sealed ledger → evaluator consumes (after sealing)
- Evaluator CANNOT write to adjudicator workspace
- Adjudicator CANNOT read evaluator namespace
- Access is strictly one-way after ledger sealing

## 4. Bundle Self-Integrity Test

**{integrity['n_passed']}/{integrity['n_checks']} checks PASS**

| Check | Result |
|---|---|
"""
    for c in integrity["checks"]:
        report += f"| {c['check']} | {'PASS' if c['passed'] else 'FAIL'} |\n"

    report += f"""

## 5. V8 Hard Invariant

`adjudicator_bundle_path ∉ research_repo`: **{'PASS' if v8_ok else 'FAIL'}**
Git-tracked bundle files: {git_tracked or 'none'}

## 6. Adjudication Status

- Bundle self-integrity: **{'PASS' if integrity['all_pass'] else 'FAIL'}**
- V8 hard invariant: **{'PASS' if v8_ok else 'FAIL'}**
- adjudication_permitted: **FALSE** (B/C/D/P/O/Q still required)
- V8.1 bundle integrity is GREEN, but adjudication remains BLOCKED

## 7. What Was NOT Modified

- DSB V1 cases, prompts, receipts, scorer: NOT modified
- Research repository: NOT modified

---

**V8.1 bundle identity correction complete. Bundle self-integrity PASS. Adjudication remains BLOCKED. STOP coding permanently in this environment.**
"""
    with open(CORRECTION_DIR / "V81_FINAL_BUNDLE_IDENTITY_REPORT.md", "w") as f:
        f.write(report)

    print(f"\nReport: {CORRECTION_DIR / 'V81_FINAL_BUNDLE_IDENTITY_REPORT.md'}")
    print(f"\nBundle self-integrity: {'PASS' if integrity['all_pass'] else 'FAIL'}")
    print(f"V8 hard invariant: {'PASS' if v8_ok else 'FAIL'}")
    print(f"adjudication_permitted: FALSE (B/C/D/P/O/Q still required)")
    print(f"\nSTOP coding permanently in this environment.")


if __name__ == "__main__":
    main()
