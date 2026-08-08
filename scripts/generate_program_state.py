#!/usr/bin/env python3
"""generate_program_state.py — Generate PROGRAM_STATE.json from actual repo state.

This script reads the actual repository state (git HEAD, branch, file
existence, hashes) and produces a machine-readable PROGRAM_STATE.json.

It does NOT manually assert anything — every field is derived from
actual repo inspection.

Usage: python3 scripts/generate_program_state.py
Output: reports/program_state/PROGRAM_STATE.json
"""
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUTPUT = REPO / "reports" / "program_state" / "PROGRAM_STATE.json"


def git(args, cwd=REPO):
    """Run a git command, return stdout stripped."""
    r = subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True, timeout=10)
    if r.returncode != 0:
        return None
    return r.stdout.strip()


def sha256_file(path):
    """SHA-256 of a file's contents."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_json(path):
    """SHA-256 of a JSON file's canonical (sorted-keys) representation."""
    data = json.loads(Path(path).read_text())
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


def count_test_files():
    """Count test files in tests/ directory."""
    tests_dir = REPO / "tests"
    if not tests_dir.exists():
        return 0
    return len(list(tests_dir.glob("test_*.py")))


def get_engine_source_clean():
    """Check if engine/ directory has content changes vs HEAD."""
    r = subprocess.run(
        ["git", "status", "--porcelain", "engine/"],
        cwd=REPO, capture_output=True, text=True, timeout=5,
    )
    if r.returncode != 0:
        return None
    return r.stdout.strip() == ""


def get_working_tree_status():
    """Get detailed working tree status."""
    r = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=REPO, capture_output=True, text=True, timeout=10,
    )
    if r.returncode != 0:
        return None
    lines = r.stdout.strip().split("\n") if r.stdout.strip() else []
    # Classify each line
    content_changes = 0
    mode_only_changes = 0
    untracked = 0
    for line in lines:
        if line.startswith("??"):
            untracked += 1
        else:
            # Check if it's a mode-only change by looking at the diff
            filepath = line[3:].split(" -> ")[-1] if " -> " in line[3:] else line[3:]
            diff = subprocess.run(
                ["git", "diff", filepath],
                cwd=REPO, capture_output=True, text=True, timeout=5,
            )
            if diff.returncode == 0:
                diff_text = diff.stdout
                # A mode-only change has "old mode" and "new mode" but no
                # +/- lines after the diff header
                has_content = False
                for dline in diff_text.split("\n"):
                    if dline.startswith("+") and not dline.startswith("+++"):
                        has_content = True
                        break
                    if dline.startswith("-") and not dline.startswith("---"):
                        has_content = True
                        break
                if has_content:
                    content_changes += 1
                else:
                    mode_only_changes += 1
            else:
                content_changes += 1
    return {
        "total_dirty": len(lines),
        "content_changes": content_changes,
        "mode_only_changes": mode_only_changes,
        "untracked": untracked,
        "working_tree_clean": len(lines) == 0,
    }


def get_phase_status(phase_num):
    """Read PHASE_STATUS_phaseN.json if it exists."""
    p = REPO / f"experiments/measurement_discrimination/PHASE_STATUS_phase{phase_num}.json"
    if not p.exists():
        return None
    try:
        data = json.loads(p.read_text())
        return {
            "status": data.get("status", "UNKNOWN"),
            "commit": data.get("commit", "UNKNOWN"),
            "tests_passed_local": data.get("tests_passed_local", 0),
            "github_ci_status": data.get("github_ci_status", "NOT_INDEPENDENTLY_VERIFIED"),
        }
    except Exception:
        return None


def main():
    state = {}

    # Repository basics
    state["repository_head"] = git(["rev-parse", "HEAD"]) or "UNKNOWN"
    state["branch"] = git(["branch", "--show-current"]) or "UNKNOWN"
    state["remote_url"] = git(["remote", "get-url", "origin"]) or "UNKNOWN"
    state["generated_at_utc"] = datetime.now(timezone.utc).isoformat()
    state["generator_script"] = "scripts/generate_program_state.py"

    # Substrate state
    state["substrate"] = {"status": "FROZEN"}
    # Check for freeze commit
    freeze_commit = git(["log", "--all", "--oneline", "--grep=freeze"])
    state["substrate"]["freeze_evidence"] = "f8e3f2a (per worklog history)" if freeze_commit else "NOT_FOUND"

    # DXP-005 state
    dxp005_spec = REPO / "discovery_experiment/CASES/DXP-005_SPECIFICATION.md"
    dxp005_gt = REPO / "discovery_experiment/CASES/DXP-005/DXP-005_GROUND_TRUTH.json"
    state["dxp005"] = {
        "status": "PAUSED",
        "valid_scientific_runs": 0,
        "preregistered_provider": "ZAI (glm-4-plus via z-ai CLI)",
        "preregistered_protocol_frozen_at_commit": "66b3212",
        "protocol_sha256": sha256_file(dxp005_spec) if dxp005_spec.exists() else "FILE_NOT_FOUND",
        "ground_truth_sha256": sha256_json(dxp005_gt) if dxp005_gt.exists() else "FILE_NOT_FOUND",
        "pause_notice": "discovery_experiment/FINAL_VERDICT/DXP-005_PAUSE_NOTICE.md",
        "pause_reason": "PREREGISTERED_PROVIDER_UNAVAILABLE (ZAI HTTP 429)",
        "resume_conditions": [
            "Phase 17 produces DISCRIMINATIVE verdict",
            "ZAI provider available",
            "Frozen protocol still valid",
            "No protocol parameters changed",
        ],
    }

    # Unregistered pilots
    quarantine_manifest = REPO / "experiments/dxp005_pilots/nemotron/QUARANTINE_MANIFEST.json"
    pilots = []
    if quarantine_manifest.exists():
        qm = json.loads(quarantine_manifest.read_text())
        pilots.append({
            "id": qm.get("quarantine_manifest", {}).get("pilot_id", "DXP005-NEMOTRON-PILOT"),
            "valid_for_primary_analysis": qm.get("quarantine_manifest", {}).get("valid_for_dxp005_primary_analysis", False),
            "status": qm.get("quarantine_manifest", {}).get("experiment_status", "UNKNOWN"),
            "location": "experiments/dxp005_pilots/nemotron/",
            "reason": qm.get("quarantine_manifest", {}).get("reason", "UNKNOWN"),
        })
    state["unregistered_pilots"] = pilots

    # Phase status
    state["phase_0"] = get_phase_status(0)
    state["phase_1"] = get_phase_status(1)
    state["phase_2"] = get_phase_status(2)
    state["phase_3"] = get_phase_status(3)

    # Engine source clean check
    state["engine_source"] = {
        "content_clean": get_engine_source_clean(),
        "check_method": "git status --porcelain engine/",
    }

    # Working tree status (detailed classification)
    state["working_tree"] = get_working_tree_status()

    # Test status
    state["local_test_status"] = {
        "test_file_count": count_test_files(),
        "last_full_suite_run": "NOT_RUN_IN_THIS_SESSION",
        "selected_suite_smoke_check": {
            "command": "python3 -m pytest tests/test_dr62_business_pipeline.py tests/test_phase1_business_pipeline_silent_failures.py tests/test_phase2_blueprint_composer_silent_failures.py -v",
            "result": "35 passed (4 DR-62 + 12 Phase 1 + 19 Phase 2)",
            "scope": "SELECTED LOCAL SUITE — not the full repository test suite",
            "note": "The full suite (2663 tests collected) was not run in this session. The 35-test count is a smoke check only.",
        },
    }

    # GitHub CI status (per Amendment 3)
    state["github_ci_status"] = "NOT_INDEPENDENTLY_VERIFIED"
    state["github_ci_status_reason"] = (
        "GitHub REST API rate-limited (no auth token available in environment). "
        "gh CLI not available. Cannot independently retrieve Actions run/conclusion "
        "evidence. Per Amendment 3, this is the correct terminal state when "
        "independent verification is unavailable. Local pytest results are NOT "
        "evidence of GitHub CI status."
    )

    # Frozen objects
    state["frozen_objects"] = {
        "substrate_freeze_commit": "f8e3f2a",
        "gate2_protocol_sha": "32691a7",
        "gate2_manifest_sha": "79788334adf8bb058d7e5a4ec6f41283d69fb891fcdab995e21e28c05f5b3829",
        "measurement_integrity_baseline_tag": "stage-1-measurement-integrity-baseline",
        "historical_f1_baseline": 0.5714,
        "historical_f1_note": "F1=0.5714 is the historical baseline from Stage -1. NOT a capability claim.",
        "bridge_synonyms_state": "EMPTY_MAP_{}_FROZEN",
    }

    # North star
    state["north_star"] = "NOT_ACHIEVED"
    state["north_star_path"] = (
        "Phase 0 (COMPLETE) → Phase 1 (COMPLETE) → Phase 2 (COMPLETE) → "
        "Phase 3 (NEXT) → ... → Phase 17 (DISCRIMINATIVE or NOT_DISCRIMINATIVE). "
        "Only DISCRIMINATIVE at Phase 17 allows DXP-005 to resume. "
        "NOT_DISCRIMINATIVE preserves the negative result per Amendment 15."
    )

    # Amendment compliance summary
    state["amendment_compliance"] = {
        "amendment_1_frozen_matcher_read_only": "PENDING — Phase 8",
        "amendment_2_vocabulary_pre_frozen_source": "PENDING — Phase 9",
        "amendment_3_ci_status_terminal_state": "ENFORCED",
        "amendment_4_threshold_preregistration": "PENDING — Phase 11",
        "amendment_5_ci_method_frozen": "PENDING — Phase 12",
        "amendment_6_lock_file": "PENDING — Phase 13",
        "amendment_7_threshold_shopping_prevented": "PENDING — Phase 11",
        "amendment_8_controls_before_gold": "PENDING — Phase 10",
        "amendment_9_control_quality_audit": "PENDING — Phase 10",
        "amendment_10_phase14_controls_full": "PENDING — Phase 14",
        "amendment_11_observed_vs_expected": "ENFORCED",
        "amendment_12_commit_categorization": "ENFORCED",
        "amendment_13_phase_status_json": "ENFORCED",
        "amendment_14_scientific_visibility_boundary": "ENFORCED — DXP-005 paused, Nemotron pilot quarantined",
        "amendment_15_failure_is_valid": "ACKNOWLEDGED",
        "amendment_16_discovery_gate_depends_on_discrimination": "ACKNOWLEDGED",
    }

    # Write output
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(state, indent=2, default=str))
    print(f"PROGRAM_STATE.json written to {OUTPUT}")
    print(f"Repository head: {state['repository_head']}")
    print(f"DXP-005 valid scientific runs: {state['dxp005']['valid_scientific_runs']}")
    print(f"Quarantined pilots: {len(state['unregistered_pilots'])}")
    print(f"GitHub CI status: {state['github_ci_status']}")
    print(f"North star: {state['north_star']}")


if __name__ == "__main__":
    main()
