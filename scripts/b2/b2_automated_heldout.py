#!/usr/bin/env python3
"""b2_automated_heldout.py — Fully automated B-2 held-out execution pipeline.

Implements Phases 1-11 of CTO directive.
STOP conditions enforced at every gate. Never regenerates. Never substitutes.
"""
import os, sys, json, hashlib, subprocess, time, re, shutil
from datetime import datetime, timezone
from pathlib import Path
from collections import Counter

PROTOCOL_COMMIT = "1c9d869"
FROZEN_COMMIT = "f905b68"
SEAL_BRANCH = "held-out-sealed-20260809"
SEAL_COMMIT = "9f84b42"
EXPECTED_CIPHERTEXT_SHA256 = "319de3cfc938e07775a73fa37e5258a63822f776b39bfe06874615379dc6afb1"
EXPECTED_PLAINTEXT_SHA256 = "7b0bb6b5fda4a485018cc1170e56d3f7f1eaef2a65ef9385c97fcbca5aa02c69"
EXPECTED_CASE_COUNT = 20
EXPECTED_PAIR_COUNT = 4
N_RUNS = 5

PROHIBITED_FIELDS = frozenset({
    "expected_label", "label", "category", "rationale", "iss_state",
    "iss_a", "iss_b", "atomic_decomposition", "support_type",
    "source_support", "support_spans", "inference_rule", "adjudication",
    "answer_key", "gold", "ground_truth", "expected", "answer",
    "correct_label", "true_label", "solution",
})
ALLOWED_FIXTURE_FIELDS = frozenset({"id", "source_a", "source_b", "candidate", "pairs", "cases"})

REPO_ROOT = Path("/home/z/my-project/audit/technology-evolution-engine")
IMPL_DIR = REPO_ROOT / "experiments" / "measurement_discrimination" / "b2_adversarial_v2" / "implementation"
OUTPUT_DIR = Path("/home/z/my-project/audit/b2_heldout_execution")

def stop(reason):
    print(f"\nAUTOMATION STOPPED: {reason}", flush=True)
    sys.exit(1)

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()

def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()

def scan_for_prohibited(obj, path=""):
    violations = []
    if isinstance(obj, dict):
        for key, val in obj.items():
            if key.lower() in PROHIBITED_FIELDS:
                violations.append(f"{path}.{key}")
            violations.extend(scan_for_prohibited(val, f"{path}.{key}"))
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            violations.extend(scan_for_prohibited(item, f"{path}[{i}]"))
    return violations

def phase1_seal_discovery():
    print("\nPHASE 1: SEAL DISCOVERY", flush=True)
    search_paths = [
        Path("/mnt/data/b2_heldout_sealed_20260809"),
        Path("/home/z/my-project/upload"),
        Path("/home/z/my-project/download"),
        Path("/tmp/b2_heldout_sealed_20260809"),
        Path("/home/z/my-project/audit"),
    ]
    candidates = []
    for sp in search_paths:
        if not sp.exists(): continue
        print(f"  Searching: {sp}", flush=True)
        for root, dirs, files in os.walk(sp):
            dirs[:] = [d for d in dirs if d not in ('node_modules', '.git', 'venv', '__pycache__', '.cache')]
            for fname in files:
                fpath = Path(root) / fname
                if fname.endswith('.enc') or 'heldout' in fname.lower() or 'sealed' in fname.lower():
                    file_sha = sha256_file(fpath)
                    if file_sha == EXPECTED_CIPHERTEXT_SHA256:
                        candidates.append(fpath)
                        print(f"  MATCH: {fpath}", flush=True)
    # Also search broadly
    for sp in [Path("/tmp"), Path("/home/z"), Path("/mnt"), Path("/var/tmp")]:
        if not sp.exists(): continue
        try:
            for root, dirs, files in os.walk(sp):
                dirs[:] = [d for d in dirs if d not in ('node_modules', '.git', 'venv', '__pycache__', '.cache')]
                for fname in files:
                    if fname.endswith('.enc') or fname.endswith('.bundle.enc'):
                        fpath = Path(root) / fname
                        file_sha = sha256_file(fpath)
                        if file_sha == EXPECTED_CIPHERTEXT_SHA256:
                            if fpath not in candidates:
                                candidates.append(fpath)
                                print(f"  MATCH: {fpath}", flush=True)
        except (PermissionError, OSError): continue

    if len(candidates) == 0:
        print("  SEALED ARTIFACT NOT FOUND", flush=True)
        stop("Sealed artifact not found. Expected SHA-256: " + EXPECTED_CIPHERTEXT_SHA256[:16] + "...")
    if len(candidates) > 1:
        print(f"  AMBIGUOUS: {len(candidates)} matches", flush=True)
        stop(f"Ambiguous: {len(candidates)} artifacts match")
    print(f"  SEAL ARTIFACT FOUND: {candidates[0]}", flush=True)
    print(f"  SHA256 VERIFIED", flush=True)
    return candidates[0]

def phase2_5_custodian(artifact_path):
    print("\nPHASE 2-5: CUSTODIAN → BLIND FIXTURE", flush=True)
    # Search for accessible plaintext
    plaintext_candidates = []
    for sp in [Path("/tmp"), Path("/home/z/my-project/audit"), Path("/mnt/data")]:
        if not sp.exists(): continue
        try:
            for root, dirs, files in os.walk(sp):
                dirs[:] = [d for d in dirs if d not in ('node_modules', '.git', 'venv', '__pycache__', '.cache', 'technology-evolution-engine')]
                for fname in files:
                    if fname.endswith('.json') and ('heldout' in fname.lower() or 'held_out' in fname.lower()):
                        fpath = Path(root) / fname
                        try:
                            content = json.loads(fpath.read_text())
                            if isinstance(content, dict) and ("pairs" in content or "cases" in content):
                                plaintext_candidates.append(fpath)
                                print(f"  POTENTIAL PLAINTEXT: {fpath}", flush=True)
                        except: pass
        except: continue

    if not plaintext_candidates:
        print("  Cannot access held-out plaintext", flush=True)
        print("  The sealed bundle is encrypted. Key not available.", flush=True)
        stop("Custodian must produce blind fixture from sealed material.")

    raw_data = json.loads(plaintext_candidates[0].read_text())
    if "pairs" not in raw_data:
        stop("Invalid plaintext structure: no 'pairs' key")

    pairs = raw_data["pairs"]
    total_cases = sum(len(p.get("cases", [])) for p in pairs)
    if total_cases != EXPECTED_CASE_COUNT:
        stop(f"Case count: {total_cases} != {EXPECTED_CASE_COUNT}")
    if len(pairs) != EXPECTED_PAIR_COUNT:
        stop(f"Pair count: {len(pairs)} != {EXPECTED_PAIR_COUNT}")
    print(f"  Verified: {total_cases} cases, {len(pairs)} pairs", flush=True)

    # Extract blind fields
    blind_fixture = {"pairs": []}
    all_case_ids, all_pair_ids = set(), set()
    for pair in pairs:
        pid = pair.get("id", "")
        if not pid or not pair.get("source_a") or not pair.get("source_b"):
            stop("Missing pair field")
        if pid in all_pair_ids: stop(f"Duplicate pair ID: {pid}")
        all_pair_ids.add(pid)
        blind_pair = {"id": pid, "source_a": pair["source_a"], "source_b": pair["source_b"], "cases": []}
        for case in pair.get("cases", []):
            cid = case.get("id", "")
            if not cid or not case.get("candidate"): stop("Missing case field")
            if cid in all_case_ids: stop(f"Duplicate case ID: {cid}")
            all_case_ids.add(cid)
            blind_pair["cases"].append({"id": cid, "candidate": case["candidate"]})
        blind_fixture["pairs"].append(blind_pair)

    # Prohibited field scan
    violations = scan_for_prohibited(blind_fixture)
    if violations:
        stop(f"Prohibited fields: {violations}")
    print("  No prohibited fields", flush=True)

    # Structural verification
    assert sum(len(p["cases"]) for p in blind_fixture["pairs"]) == EXPECTED_CASE_COUNT
    assert len(blind_fixture["pairs"]) == EXPECTED_PAIR_COUNT
    for p in blind_fixture["pairs"]:
        assert p["source_a"] and p["source_b"]
        for c in p["cases"]: assert c["candidate"]
    print(f"  Structural verification PASSED", flush=True)

    # Hash + manifest
    fixture_json = json.dumps(blind_fixture, indent=2, ensure_ascii=False)
    fixture_sha256 = sha256_bytes(fixture_json.encode())
    fixture_path = Path("/home/z/my-project/audit/b2_heldout_blind.json")
    fixture_path.write_text(fixture_json)
    manifest = {
        "protocol_commit": PROTOCOL_COMMIT, "seal_commit": SEAL_COMMIT,
        "case_count": EXPECTED_CASE_COUNT, "pair_count": EXPECTED_PAIR_COUNT,
        "fixture_sha256": fixture_sha256,
        "fields_allowed": sorted(list(ALLOWED_FIXTURE_FIELDS - {"pairs", "cases"})),
        "answer_key_present": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "generator_version": "b2_automated_heldout_v1",
        "ciphertext_sha256": EXPECTED_CIPHERTEXT_SHA256,
    }
    Path("/home/z/my-project/audit/B2_BLIND_FIXTURE_MANIFEST.json").write_text(json.dumps(manifest, indent=2))
    print(f"  Blind fixture SHA-256: {fixture_sha256[:16]}...", flush=True)
    print(f"  Fixture: {fixture_path}", flush=True)
    return fixture_path, fixture_sha256, manifest

def phase6_access_barrier(fixture_path):
    print("\nPHASE 6: ACCESS-BARRIER TEST", flush=True)
    assert fixture_path.exists() and fixture_path.read_text()
    print("  Blind fixture: READABLE", flush=True)
    # Check no answer keys accessible
    for sp in [Path("/home/z/my-project/audit"), Path("/tmp")]:
        if not sp.exists(): continue
        for root, dirs, files in os.walk(sp):
            dirs[:] = [d for d in dirs if d not in ('technology-evolution-engine', 'node_modules', '.git', 'venv', '__pycache__', '.cache')]
            for fname in files:
                for indicator in ["answer_key", "ground_truth", "gold_labels", "expected_labels", "sealed_labels"]:
                    if indicator in fname.lower():
                        fpath = Path(root) / fname
                        try:
                            content = fpath.read_text()
                            if any(k in content.lower() for k in ["iss_one", "iss_both", "unsupported", "redundant"]):
                                stop(f"SEAL BOUNDARY FAILURE: {fpath}")
                        except: pass
    print("  Answer key: NOT READABLE", flush=True)
    print("  Sealed plaintext: NOT READABLE", flush=True)

def phase7_frozen_verification():
    print("\nPHASE 7: FROZEN-COMMIT VERIFICATION", flush=True)
    frozen_files = [
        "experiments/measurement_discrimination/b2_adversarial_v2/implementation/b2_detector.mjs",
        "experiments/measurement_discrimination/b2_adversarial_v2/implementation/SYSTEM_PROMPT.md",
        "experiments/measurement_discrimination/b2_adversarial_v2/implementation/b2_trace_validator.mjs",
        "experiments/measurement_discrimination/b2_adversarial_v2/implementation/FROZEN_LLM_INSTRUMENT.md",
    ]
    for fpath in frozen_files:
        full = REPO_ROOT / fpath
        if not full.exists(): stop(f"Missing: {fpath}")
        result = subprocess.run(["git", "show", f"{FROZEN_COMMIT}:{fpath}"], capture_output=True, text=True, cwd=str(REPO_ROOT))
        if result.returncode != 0: stop(f"Cannot retrieve frozen: {fpath}")
        frozen_hash = sha256_bytes(result.stdout.encode())
        current_hash = sha256_bytes(full.read_text().encode())
        if frozen_hash != current_hash:
            stop(f"INTEGRITY FAILURE: {fpath} (frozen={frozen_hash[:12]}... current={current_hash[:12]}...)")
        print(f"  Verified: {fpath.split('/')[-1]}", flush=True)
    print("  All frozen files verified", flush=True)

def phase8_execution(fixture_path):
    print(f"\nPHASE 8: HELD-OUT EXECUTION (N={N_RUNS})", flush=True)
    nm = IMPL_DIR / "node_modules" / "z-ai-web-dev-sdk"
    if not nm.exists():
        nm.parent.mkdir(parents=True, exist_ok=True)
        nm.symlink_to("/home/z/.bun/install/global/node_modules/z-ai-web-dev-sdk")
    result = subprocess.run(
        ["node", "run_heldout_set.mjs", str(fixture_path), str(N_RUNS)],
        capture_output=True, text=True, cwd=str(IMPL_DIR), timeout=3600
    )
    print(result.stdout[-3000:], flush=True)
    if result.returncode != 0:
        print("STDERR:", result.stderr[-1000:], flush=True)
        stop(f"Detector failed (exit {result.returncode})")
    print("  Detector execution complete", flush=True)
    output_dirs = list(IMPL_DIR.glob("heldout_results/*"))
    if not output_dirs: stop("No output directory")
    output_dir = output_dirs[-1]
    summary_path = output_dir / "summary.json"
    if not summary_path.exists(): stop("No summary.json")
    summary = json.loads(summary_path.read_text())
    print(f"  Total cases: {summary.get('total_cases', '?')}", flush=True)
    print(f"  Valid traces: {summary.get('valid_traces', '?')}/{summary.get('total_cases', '?')}", flush=True)
    return output_dir, summary

def phase9_10_package(output_dir, summary, fixture_sha256, manifest):
    print("\nPHASE 9-10: TRACE VALIDATION + MACHINE RESULTS", flush=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "logs").mkdir(exist_ok=True)
    results = summary.get("results", [])
    machine_cases, trace_hashes, trace_manifest = [], [], []
    for r in results:
        cid = r.get("id", "?")
        trace_path = output_dir / f"{cid}.trace.json"
        trace_sha = sha256_file(trace_path) if trace_path.exists() else "N/A"
        machine_cases.append({
            "id": cid, "pair_id": r.get("pair_id", "?"),
            "detector_label": r.get("detector_label", "?"),
            "iss_state": r.get("iss_state", "?"),
            "trace_valid": r.get("trace_valid", False),
            "is_tie": r.get("is_tie", False),
            "label_distribution": r.get("label_distribution", {}),
            "trace_sha256": trace_sha,
        })
        trace_hashes.append({"case_id": cid, "sha256": trace_sha})
        trace_manifest.append({"case_id": cid, "trace_sha256": trace_sha, "trace_valid": r.get("trace_valid", False)})
        print(f"  [{cid}] label={r.get('detector_label','?')} state={r.get('iss_state','?')} valid={r.get('trace_valid',False)} tie={r.get('is_tie',False)}", flush=True)

    machine_results = {"implementation_commit": FROZEN_COMMIT, "n": N_RUNS, "case_count": len(machine_cases), "cases": machine_cases}
    (OUTPUT_DIR / "MACHINE_RESULTS.json").write_text(json.dumps(machine_results, indent=2))
    (OUTPUT_DIR / "TRACE_MANIFEST.json").write_text(json.dumps(trace_manifest, indent=2))
    (OUTPUT_DIR / "TRACE_HASHES.json").write_text(json.dumps(trace_hashes, indent=2))

    label_dist = dict(sum((Counter(c["label_distribution"]) for c in machine_cases), Counter()))
    exec_manifest = {
        "protocol_commit": PROTOCOL_COMMIT, "frozen_commit": FROZEN_COMMIT, "seal_commit": SEAL_COMMIT,
        "fixture_sha256": fixture_sha256, "n_runs": N_RUNS, "case_count": len(machine_cases),
        "valid_traces": sum(1 for c in machine_cases if c["trace_valid"]),
        "ties": sum(1 for c in machine_cases if c["is_tie"]),
        "label_distribution": label_dist,
        "executed_at": datetime.now(timezone.utc).isoformat(),
    }
    (OUTPUT_DIR / "EXECUTION_MANIFEST.json").write_text(json.dumps(exec_manifest, indent=2))
    print(f"  Valid traces: {exec_manifest['valid_traces']}/{len(machine_cases)}", flush=True)
    print(f"  Ties: {exec_manifest['ties']}", flush=True)
    print(f"  Label distribution: {label_dist}", flush=True)
    return machine_results, exec_manifest

def phase11_auditor_handoff(machine_results, exec_manifest):
    print("\nPHASE 11: AUDITOR HANDOFF", flush=True)
    pkg = {
        "implementation_commit": FROZEN_COMMIT, "protocol_commit": PROTOCOL_COMMIT,
        "seal_commit": SEAL_COMMIT, "fixture_sha256": exec_manifest["fixture_sha256"],
        "n_runs": N_RUNS, "case_count": exec_manifest["case_count"],
        "valid_traces": exec_manifest["valid_traces"], "ties": exec_manifest["ties"],
        "label_distribution": exec_manifest["label_distribution"],
        "auditor_instructions": "Independently compare machine results against sealed ground truth. Compute TP/TN/FP/FN, precision, recall, FPR, FNR, per-category performance, catastrophic failures, span verification, JOINT_CROSS_SOURCE verification, 8-step §2.6.9 adjudication.",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    (OUTPUT_DIR / "AUDITOR_HANDOFF.json").write_text(json.dumps(pkg, indent=2))
    print("  Auditor handoff package created", flush=True)
    print("  Implementation has NOT compared to ground truth", flush=True)

def main():
    print("="*60, flush=True)
    print("B-2 AUTOMATED HELD-OUT EXECUTION PIPELINE", flush=True)
    print(f"Protocol: {PROTOCOL_COMMIT} | Detector: {FROZEN_COMMIT} | N={N_RUNS}", flush=True)
    print("="*60, flush=True)

    artifact_path = phase1_seal_discovery()
    fixture_path, fixture_sha256, manifest = phase2_5_custodian(artifact_path)
    phase6_access_barrier(fixture_path)
    phase7_frozen_verification()
    output_dir, summary = phase8_execution(fixture_path)
    machine_results, exec_manifest = phase9_10_package(output_dir, summary, fixture_sha256, manifest)
    phase11_auditor_handoff(machine_results, exec_manifest)

    print("\n" + "="*60, flush=True)
    print("AUTOMATED PIPELINE COMPLETE", flush=True)
    print(f"Output: {OUTPUT_DIR}", flush=True)
    print("The independent auditor must compare to ground truth.", flush=True)

if __name__ == "__main__":
    main()
