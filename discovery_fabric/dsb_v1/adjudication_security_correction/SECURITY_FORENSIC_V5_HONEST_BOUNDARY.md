# SECURITY FORENSIC V5 — HONEST BOUNDARY REPORT

**Date:** 2026-08-12
**Directive:** Provision the real two-identity/container deployment and run a fresh preflight. No more code in the current environment.
**Status:** CANNOT COMPLETE IN THIS ENVIRONMENT. Honest boundary stated below.

---

## 1. What Was Verified (GitHub Refs)

After the V4 git history purge, all GitHub refs were verified clean:

| Ref | SHA | Contaminated files? |
|---|---|---|
| `refs/heads/main` | `9512208e` | NONE (clean) |
| `refs/heads/audit/forensic-review` | `aacd9e44` | NONE (clean) |
| `refs/heads/external-review-preparation` | `b585e60a` | NONE (clean) |
| `refs/heads/held-out-sealed-20260809` | `9f84b425` | NONE (clean) |
| `refs/heads/independent-scientific-corpus-construction-75b04` | `742cf207` | NONE (clean) |
| `refs/tags/proposal-composer-gen0` | `49ad21ba` | NONE (clean) |
| `refs/tags/stage-1-measurement-integrity-baseline` | `4e239e60` | NONE (clean) |
| `refs/pull/1/head` | `742cf207` | NONE (clean) |
| `refs/pull/1/merge` | `7260de6d` | NONE (clean) |

**Result:** No contaminated files (vault keys, plaintext vaults, full-packet artifacts) exist in ANY reachable ref on GitHub. The history rewrite is complete and verified.

---

## 2. What CANNOT Be Done In This Environment

Per the Honest-Boundary Rule (CONSTITUTION.md): "State the boundary precisely. Diagnose as far as you CAN go. Report the exact remaining step."

### This environment:
- **UID:** 1001 (user `z`), single user
- **Root access:** NO (`useradd` fails with Permission denied)
- **Docker/podman:** NOT AVAILABLE
- **sudo:** NOT AVAILABLE

### What I CANNOT do:
1. **Provision a real two-identity deployment.** Creating separate Unix users requires root. Creating separate containers requires Docker/podman. Neither is available.
2. **Generate new vault key material in an isolated environment.** This environment is the contaminated one (per V4). New keys must be generated in a clean, isolated environment — not here.
3. **Run the preflight from a clean deployment clone.** I AM the contaminated environment. A clean clone must be made on a separate host with separate identities.
4. **Make D/P (encrypted vault exists / is encrypted) pass.** The old encrypted vault was purged (old key compromised). A new vault with new key must be generated in the real deployment.
5. **Make B/C/O pass.** These require separate OS identities (adjudicator user vs evaluator user) which cannot be created without root.

### What I CANNOT claim:
- I cannot claim the preflight is green.
- I cannot claim the deployment is provisioned.
- I cannot claim new key material was generated.
- I cannot claim the 80-case adjudication can begin.

---

## 3. The Exact Remaining Step

The remaining step is **NOT a code change**. It is an **infrastructure provisioning step** that must be performed on a real multi-user host or container orchestration platform:

### Step 1: Provision the infrastructure
On a real host with root access (or a container orchestration platform):

```bash
# Option A: Separate Unix users
sudo useradd -u 1001 -m adjudicator
sudo useradd -u 1002 -m evaluator

# Create directories with correct ownership
sudo mkdir -p /opt/tee/adjudicator_workspace
sudo mkdir -p /opt/tee/evaluator_boundary
sudo chown adjudicator:adjudicator /opt/tee/adjudicator_workspace
sudo chown evaluator:evaluator /opt/tee/evaluator_boundary
sudo chmod 0700 /opt/tee/adjudicator_workspace
sudo chmod 0700 /opt/tee/evaluator_boundary
```

```bash
# Option B: Separate containers (Docker Compose)
# adjudicator container: mounts adjudicator_workspace/ only
# evaluator container: mounts both directories
# Vault key generated inside evaluator container, never exported
```

### Step 2: Clone the clean repository
```bash
# As the adjudicator user:
su - adjudicator
git clone https://github.com/prateekm1007/technology-evolution-engine.git
```

### Step 3: Generate new vault key material (as evaluator)
```bash
su - evaluator
cd /opt/tee
python3 -c "
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
key = AESGCM.generate_key(bit_length=256)
with open('/opt/tee/evaluator_boundary/vault_key.bin', 'wb') as f:
    f.write(key)
"
chmod 0600 /opt/tee/evaluator_boundary/vault_key.bin
```

### Step 4: Generate encrypted vault (as evaluator)
```bash
su - evaluator
cd /opt/tee/technology-evolution-engine
python3 discovery_fabric/dsb_v1/adjudication_engine_v3/build_v3.py
# This generates the encrypted vault in adjudicator_workspace/
# and the key in evaluator_boundary/
```

### Step 5: Run the preflight (as adjudicator)
```bash
su - adjudicator
cd /opt/tee/technology-evolution-engine
python3 discovery_fabric/dsb_v1/adjudication_security_correction/run_correction.py
```

### Step 6: Verify all 16+ checks PASS
The preflight must show:
- ✓ A_NO_VAULT_KEYS_IN_REPO
- ✓ B_ADJUDICATOR_CANNOT_READ_KEY (EACCES — separate user)
- ✓ C_ADJUDICATOR_CANNOT_WRITE_EVAL_BOUNDARY (EACCES — separate user)
- ✓ D_ENCRYPTED_VAULT_EXISTS (new vault generated)
- ✓ E_BLIND_NO_GROUND_TRUTH
- ✓ F_FULL_NOT_IN_WS
- ✓ G_NO_HIDDEN_COPIES
- ✓ H_GIT_NO_VAULT_KEYS (already verified)
- ✓ I_NO_OPEN_FD_TO_KEY
- ✓ J_NO_ENV_VAR_WITH_KEY
- ✓ K_NO_INHERITED_FDS
- ✓ L_SYMLINK_TRAVERSAL_PROTECTION
- ✓ M_NO_TEMP_KEY_FILES
- ✓ N_NO_BACKUP_FILES
- ✓ O_NO_ACCESS_TO_EVALUATOR_PROCESS (separate user — ptrace checks)
- ✓ P_VAULT_IS_ENCRYPTED (new vault)

### Step 7: Only then — begin the 80-case adjudication

---

## 4. What Was NOT Modified

Per directive: "Do not regenerate or modify the DSB cases, prompts, receipts, or frozen scorer."

- ✓ DSB V1 cases (20 files): NOT modified
- ✓ DSB V1 prompts (payload_builder.py): NOT modified
- ✓ DSB V1 receipts (80 files): NOT modified
- ✓ DSB V1 scorer (scorer.py): NOT modified
- ✓ FREEZE_MANIFEST.json: NOT modified (111 artifacts unchanged)

---

## 5. Summary

| Item | Status |
|---|---|
| Git history purged (V4) | ✓ COMPLETE |
| GitHub refs verified clean | ✓ COMPLETE (all branches, tags, PR refs) |
| H1-H4 preflight | ✓ PASS (in this environment) |
| B/C/O preflight | ✗ BLOCKING (requires multi-identity deployment) |
| D/P preflight | ✗ BLOCKING (vault purged — must regenerate with new key) |
| Real two-identity deployment provisioned | ✗ CANNOT DO in this environment |
| New vault key material generated | ✗ CANNOT DO in this environment (contaminated) |
| 80-case adjudication | ✗ BLOCKED until preflight fully green |

**Honest boundary:** I have verified everything that can be verified from this single-user container. The remaining steps require a real multi-user host or container orchestration platform with root access. This environment cannot provision that infrastructure.

**No more code in this environment.** The next action is infrastructure provisioning, which must happen on a different host.

---

**End of Security Forensic V5 — Honest Boundary Report.**
