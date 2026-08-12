# ADJUDICATION DEPLOYMENT REQUIREMENTS

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
