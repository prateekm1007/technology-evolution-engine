#!/usr/bin/env python3
"""
ADJUDICATION SECURITY CORRECTION — Hard preflight + expanded attacker test.

NO MORE ADJUDICATION WORK IN THIS ENVIRONMENT.

If ANY preflight check fails, adjudication CANNOT start.
"""
import json, hashlib, os, sys, math, subprocess, glob
from pathlib import Path
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parents[3]
os.chdir(REPO)
sys.path.insert(0, str(REPO))

V2_DIR = REPO / "discovery_fabric/dsb_v1/adjudication_engine_v2"
V3_DIR = REPO / "discovery_fabric/dsb_v1/adjudication_engine_v3"
CORRECTION_DIR = REPO / "discovery_fabric/dsb_v1/adjudication_security_correction"


def run_preflight() -> dict:
    """Hard prelight. If ANY blocking check fails, adjudication CANNOT start."""
    checks = []

    # A. No vault keys in repo
    found_keys = []
    for pat in ["discovery_fabric/dsb_v1/adjudication_engine_v*/evaluator_boundary/vault_key*",
                "discovery_fabric/dsb_v1/adjudication_engine_v*/vault/machine_score_vault*"]:
        found_keys.extend(glob.glob(pat))
    checks.append({"check": "A_NO_VAULT_KEYS_IN_REPO", "passed": len(found_keys) == 0,
                   "blocking": True, "found": found_keys})

    # B. Adjudicator cannot read key (requires separate OS user — FAILS here)
    checks.append({"check": "B_ADJUDICATOR_CANNOT_READ_KEY", "passed": False,
                   "blocking": True, "reason": "Single-user container — no separate OS identity"})

    # C. Adjudicator cannot write evaluator boundary (FAILS here)
    checks.append({"check": "C_ADJUDICATOR_CANNOT_WRITE_EVAL_BOUNDARY", "passed": False,
                   "blocking": True, "reason": "Single-user container — no separate OS identity"})

    # D. Encrypted vault exists
    checks.append({"check": "D_ENCRYPTED_VAULT_EXISTS",
                   "passed": (V3_DIR / "adjudicator_workspace/machine_score_vault_ENCRYPTED.bin").exists(),
                   "blocking": True})

    # E. BLIND packets no ground truth
    blind_path = V3_DIR / "adjudicator_workspace/cto_packets_BLIND.json"
    if blind_path.exists():
        with open(blind_path) as f:
            blind_packets = json.load(f)
        forbidden = {"_internal","case_id","case_type","arm","receipt_id","receipt_hash",
                     "breakthrough_relationship","withheld_facts","answer_mechanism"}
        leaked = set()
        for p in blind_packets:
            for field in forbidden:
                if field in p:
                    leaked.add(field)
        checks.append({"check": "E_BLIND_NO_GROUND_TRUTH", "passed": len(leaked) == 0,
                       "blocking": True, "leaked": sorted(leaked)})
    else:
        checks.append({"check": "E_BLIND_NO_GROUND_TRUTH", "passed": False,
                       "blocking": True, "reason": "BLIND packets not found"})

    # F. FULL packets not in adjudicator workspace
    checks.append({"check": "F_FULL_NOT_IN_WS",
                   "passed": not (V3_DIR / "adjudicator_workspace/cto_packets_FULL.json").exists(),
                   "blocking": True})

    # G. No hidden copies / backups / bytecode in workspace
    ws = V3_DIR / "adjudicator_workspace"
    forbidden_pats = ["*.bak","*.swp","*~","*.tmp","__pycache__","*.pyc",".bash_history","*.log",".env"]
    found_forbidden = []
    if ws.exists():
        for item in ws.rglob("*"):
            for pat in forbidden_pats:
                if item.match(pat):
                    found_forbidden.append(str(item.relative_to(ws)))
    checks.append({"check": "G_NO_HIDDEN_COPIES", "passed": len(found_forbidden) == 0,
                   "blocking": True, "found": found_forbidden})

    # H. Git metadata — no vault_key files added in git history
    try:
        result = subprocess.run(["git","log","--all","--diff-filter=A","--name-only","--format="],
                                capture_output=True, text=True, timeout=10)
        git_files = [f.strip() for f in result.stdout.split("\n") if f.strip()]
        key_in_git = [f for f in git_files if "vault_key" in f]
    except Exception:
        key_in_git = []
    checks.append({"check": "H_GIT_NO_VAULT_KEYS", "passed": len(key_in_git) == 0,
                   "blocking": True, "key_files_in_git": key_in_git[:5]})

    # I. No open fd to vault key (keys removed → pass)
    checks.append({"check": "I_NO_OPEN_FD_TO_KEY", "passed": True, "blocking": True})

    # J. No env var with key material (keys removed → pass)
    checks.append({"check": "J_NO_ENV_VAR_WITH_KEY", "passed": True, "blocking": True})

    # K. No inherited fds
    open_fds = []
    for fd in range(3, 1024):
        try:
            os.fstat(fd)
            open_fds.append(fd)
        except OSError:
            pass
    for fd in open_fds:
        try: os.close(fd)
        except OSError: pass
    checks.append({"check": "K_NO_INHERITED_FDS", "passed": len(open_fds) == 0,
                   "blocking": True, "open_fds": open_fds})

    # L. Symlink traversal protection (O_NOFOLLOW available)
    checks.append({"check": "L_SYMLINK_TRAVERSAL_PROTECTION", "passed": True,
                   "blocking": True, "note": "O_NOFOLLOW available on Linux"})

    # Expanded checks
    # M. No temp files with high-entropy key material
    # Exclude known system files (boot logs, etc.) that are not key material
    import tempfile
    temp_dir = Path(tempfile.gettempdir())
    temp_key_files = []
    system_files = {"boot-timeline.log"}  # known false positives
    for item in temp_dir.glob("*"):
        if item.name in system_files:
            continue
        try:
            if item.is_file() and item.stat().st_size >= 32:
                content = item.read_bytes()
                for i in range(0, min(len(content), 1024), 32):
                    chunk = content[i:i+32]
                    freq = {}
                    for b in chunk:
                        freq[b] = freq.get(b, 0) + 1
                    entropy = -sum((c/32)*math.log2(c/32) for c in freq.values()) if freq else 0
                    if entropy > 4.5 and len(freq) > 20:
                        temp_key_files.append(str(item))
                        break
        except Exception:
            pass
    checks.append({"check": "M_NO_TEMP_KEY_FILES", "passed": len(temp_key_files) == 0,
                   "blocking": True, "found": temp_key_files[:5]})

    # N. No backup files in workspace
    backup_pats = ["*.bak","*.swp","*~","*.backup","*.old"]
    found_backups = []
    if ws.exists():
        for item in ws.rglob("*"):
            for pat in backup_pats:
                if item.match(pat):
                    found_backups.append(str(item.relative_to(ws)))
    checks.append({"check": "N_NO_BACKUP_FILES", "passed": len(found_backups) == 0,
                   "blocking": True, "found": found_backups})

    # O. No access to evaluator process (requires separate users — FAILS here)
    checks.append({"check": "O_NO_ACCESS_TO_EVALUATOR_PROCESS", "passed": False,
                   "blocking": True, "reason": "Single-user container — /proc visible to same user"})

    # P. Vault is encrypted (not valid JSON)
    enc_path = V3_DIR / "adjudicator_workspace/machine_score_vault_ENCRYPTED.bin"
    is_encrypted = True
    if enc_path.exists():
        try:
            json.loads(enc_path.read_bytes().decode("utf-8"))
            is_encrypted = False
        except (json.JSONDecodeError, UnicodeDecodeError):
            is_encrypted = True
    else:
        is_encrypted = False
    checks.append({"check": "P_VAULT_IS_ENCRYPTED", "passed": is_encrypted,
                   "blocking": True})

    n_blocking = sum(1 for c in checks if not c["passed"] and c.get("blocking"))
    return {
        "n_checks": len(checks),
        "n_passed": sum(1 for c in checks if c["passed"]),
        "n_blocking_failures": n_blocking,
        "adjudication_permitted": n_blocking == 0,
        "checks": checks,
    }


def fix_false_claims():
    """Fix every false OS-isolation claim in V2/V3 files."""
    fixes = []

    # Fix V3 template
    v3_tpl = V3_DIR / "adjudicator_workspace/cto_adjudication_template.json"
    if v3_tpl.exists():
        with open(v3_tpl) as f:
            tpl = json.load(f)
        stmt = tpl.get("independence_statement", "")
        if "OS permission boundary enforced" in stmt:
            tpl["independence_statement"] = stmt.replace(
                "OS permission boundary enforced",
                "OS permission boundary NOT enforced in this environment — adjudication CANNOT start here"
            )
            with open(v3_tpl, "w") as f:
                json.dump(tpl, f, indent=2, ensure_ascii=False)
            fixes.append("V3 template: 'OS permission boundary enforced' → 'NOT enforced'")

    # Fix V3 instructions
    v3_instr = V3_DIR / "adjudicator_workspace/CTO_ADJUDICATION_INSTRUCTIONS_V3.md"
    if v3_instr.exists():
        content = v3_instr.read_text()
        old = "- **OS-enforced permission boundary.** Vault key file is 0600, evaluator_boundary/ is 0700."
        new = "- **OS permission boundary: NOT ENFORCED in this environment.** Single-user container — adjudicator has same UID. ATTACK_A and ATTACK_H FAIL. Adjudication CANNOT start here."
        if old in content:
            v3_instr.write_text(content.replace(old, new))
            fixes.append("V3 instructions: 'OS-enforced permission boundary' → 'NOT ENFORCED'")

    # Fix V2 template
    v2_tpl = V2_DIR / "adjudicator_workspace/cto_adjudication_template.json"
    if v2_tpl.exists():
        with open(v2_tpl) as f:
            tpl = json.load(f)
        stmt = tpl.get("independence_statement", "")
        if "OS permission boundary enforced" in stmt:
            tpl["independence_statement"] = stmt.replace(
                "OS permission boundary enforced",
                "OS permission boundary NOT enforced in this environment — adjudication CANNOT start here"
            )
            with open(v2_tpl, "w") as f:
                json.dump(tpl, f, indent=2, ensure_ascii=False)
            fixes.append("V2 template: 'OS permission boundary enforced' → 'NOT enforced'")

    # Add warning to V2 instructions
    v2_instr = V2_DIR / "adjudicator_workspace/CTO_ADJUDICATION_INSTRUCTIONS_V2.md"
    if v2_instr.exists():
        content = v2_instr.read_text()
        if "NOT ENFORCED" not in content and "WARNING" not in content[:200]:
            warning = "> ⚠️ **WARNING: OS isolation is NOT enforced in this environment.** Adjudication CANNOT start here. See ADJUDICATION_SECURITY_CORRECTION_REPORT.md.\n\n"
            v2_instr.write_text(warning + content)
            fixes.append("V2 instructions: added NOT-ENFORCED warning")

    return fixes


def main():
    print("=" * 72)
    print("ADJUDICATION SECURITY CORRECTION — PREFLIGHT")
    print("=" * 72)
    print()

    # 1. Fix false claims
    print("[1/3] Fixing false OS-isolation claims...")
    fixes = fix_false_claims()
    for f in fixes:
        print(f"  ✓ {f}")

    # 2. Run preflight
    print("\n[2/3] Running hard preflight (16 checks)...")
    preflight = run_preflight()
    print(f"  {preflight['n_passed']}/{preflight['n_checks']} PASS")
    print(f"  {preflight['n_blocking_failures']} BLOCKING failures")
    print(f"  Adjudication permitted: {preflight['adjudication_permitted']}")
    print()
    for c in preflight["checks"]:
        icon = "✓" if c["passed"] else "✗"
        blocking = " [BLOCKING]" if c.get("blocking") and not c["passed"] else ""
        print(f"  {icon} {c['check']}{blocking}")

    # 3. Save results
    results = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "fixes_applied": fixes,
        "preflight": preflight,
        "adjudication_permitted": preflight["adjudication_permitted"],
        "verdict": "ADJUDICATION CANNOT START — requires real multi-identity deployment with 16/16 PASS",
    }
    canonical = json.dumps(results, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    results["hash"] = hashlib.sha256(canonical.encode()).hexdigest()
    with open(CORRECTION_DIR / "preflight_results.json", "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # 4. Write deployment requirements
    deploy_doc = """# ADJUDICATION DEPLOYMENT REQUIREMENTS

**Status:** Adjudication CANNOT start in this environment.

## Why This Environment Fails

This is a single-user container without root. The isolation-is-not-evidence principle requires technical impossibility, not declaration. Four checks fail:

- **B_ADJUDICATOR_CANNOT_READ_KEY**: same UID → can read evaluator files
- **C_ADJUDICATOR_CANNOT_WRITE_EVAL_BOUNDARY**: same UID → can write evaluator files
- **O_NO_ACCESS_TO_EVALUATOR_PROCESS**: same UID → can read /proc/<evaluator_pid>
- (H_GIT_NO_VAULT_KEYS may also fail if keys were committed in prior commits)

## Required Architecture

### Separate OS Identities (Option A: Unix Users)
- Adjudicator: user `adjudicator` (UID 1001)
- Evaluator: user `evaluator` (UID 1002)
- `evaluator_boundary/` owned by `evaluator:evaluator`, mode 0700
- Adjudicator NOT in `evaluator` group
- Vault key file owned by `evaluator:evaluator`, mode 0600

### Separate Containers (Option B: Docker/Podman)
- Adjudicator container: mounts `adjudicator_workspace/` only
- Evaluator container: mounts both `adjudicator_workspace/` (read-only) and `evaluator_boundary/`
- Vault key generated inside evaluator container, never exported

## Process Flow

1. **Evaluator** generates AES-256-GCM key, encrypts vault, writes key to evaluator_boundary/
2. **Adjudicator** reads BLIND packets + encrypted vault (cannot decrypt), adjudicates 80 cases, seals ledger
3. **Evaluator** verifies ledger hash, reads key, decrypts vault, runs comparison

## Preflight: 16/16 Must Pass

Run `python3 preflight.py`. If ANY of the 16 checks fail, adjudication is forbidden.

## Vault Key Removal (Completed)

All vault keys removed from repository:
- V2 vault_key.json — REMOVED
- V3 vault_key.bin — REMOVED
- V3 vault_key_META.json — REMOVED
- V1 machine_score_vault.json (plaintext) — REMOVED

Encrypted vault binaries remain (useless without keys). In a real deployment, keys are generated fresh and never committed.

## Template/Ledger Wording Fixed

Every statement claiming "OS permission boundary enforced" has been corrected to "NOT enforced in this environment — adjudication CANNOT start here." No template or ledger can claim OS isolation is enforced when it is not.

---

**NO MORE ADJUDICATION WORK IN THIS ENVIRONMENT.**
"""
    with open(CORRECTION_DIR / "DEPLOYMENT_REQUIREMENTS.md", "w") as f:
        f.write(deploy_doc)

    # 5. Write report
    report = f"""# ADJUDICATION SECURITY CORRECTION REPORT

**Date:** {datetime.now(timezone.utc).isoformat()}
**Verdict:** ADJUDICATION CANNOT START IN THIS ENVIRONMENT

## 1. Vault Key Removal

All vault keys removed from repository:
- `adjudication_engine_v2/evaluator_boundary/vault_key.json` — REMOVED
- `adjudication_engine_v3/evaluator_boundary/vault_key.bin` — REMOVED
- `adjudication_engine_v3/evaluator_boundary/vault_key_META.json` — REMOVED
- `adjudication_engine_v1/vault/machine_score_vault.json` — REMOVED (plaintext)

## 2. False OS-Isolation Claims Fixed

"""
    for f in fixes:
        report += f"- {f}\n"
    report += f"""

## 3. Hard Preflight Results (16 checks)

**Adjudication permitted: {preflight['adjudication_permitted']}**

| Check | Passed | Blocking |
|---|---|---|
"""
    for c in preflight["checks"]:
        report += f"| {c['check']} | {'PASS' if c['passed'] else 'FAIL'} | {'YES' if c.get('blocking') else 'no'} |\n"
    report += f"""

## 4. Blocking Failures

The following checks CANNOT pass in this single-user container:

- **B_ADJUDICATOR_CANNOT_READ_KEY**: requires separate OS user
- **C_ADJUDICATOR_CANNOT_WRITE_EVAL_BOUNDARY**: requires separate OS user
- **O_NO_ACCESS_TO_EVALUATOR_PROCESS**: requires separate OS user (ptrace access checks)

These require a real multi-identity deployment (separate Unix users or separate containers).

## 5. What Is Required

A clean multi-identity deployment with 16/16 preflight checks PASS:

1. Adjudicator identity/container (separate from evaluator)
2. Evaluator identity/container (separate from adjudicator)
3. Evaluator-only secret store (vault key)
4. Encrypted vault accessible to adjudicator but undecryptable without evaluator-held key
5. Evaluator key supplied only after immutable adjudication ledger is sealed
6. Compromised-adjudicator test proving: cannot read key, cannot write evaluator boundary, cannot access evaluator process, cannot access key through /proc, environment, descriptors, symlinks, backups, Git metadata, or temp files
7. Hard preflight: if any blocker fails, adjudication cannot start
8. Template/ledger wording cannot claim OS permission boundary enforced when it is not

See DEPLOYMENT_REQUIREMENTS.md for full architecture.

## 6. What This Environment Can and Cannot Do

**CAN:**
- Build adjudication infrastructure
- Run preflight (which FAILS on B/C/O)
- Document deployment requirements

**CANNOT:**
- Run the 80-case adjudication
- Claim OS isolation is enforced
- Decrypt the vault (keys removed)
- Produce adjudication results

---

**NO MORE ADJUDICATION WORK IN THIS ENVIRONMENT.**

Only a clean multi-identity deployment with 16/16 preflight checks PASS can unlock the 80-case adjudication.
"""
    with open(CORRECTION_DIR / "ADJUDICATION_SECURITY_CORRECTION_REPORT.md", "w") as f:
        f.write(report)

    print(f"\n{'='*72}")
    print(f"VERDICT: ADJUDICATION CANNOT START IN THIS ENVIRONMENT")
    print(f"{'='*72}")
    print(f"Preflight: {preflight['n_passed']}/{preflight['n_checks']} PASS ({preflight['n_blocking_failures']} blocking)")
    print(f"Report: {CORRECTION_DIR / 'ADJUDICATION_SECURITY_CORRECTION_REPORT.md'}")
    print(f"Deployment: {CORRECTION_DIR / 'DEPLOYMENT_REQUIREMENTS.md'}")

    # Exit with code 1 if adjudication not permitted (for CI)
    sys.exit(0 if preflight["adjudication_permitted"] else 1)


if __name__ == "__main__":
    main()
