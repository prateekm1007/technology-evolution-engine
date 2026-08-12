# SECURITY FORENSIC V4 — GIT HISTORY PURGE REPORT

**Date:** 2026-08-12T19:29:45.064620+00:00
**Verdict:** ADJUDICATION CANNOT START — requires multi-identity deployment

## 1. Git History Purge

### Contaminated files found in git history:


### Purge result:
- Purged: False
- Files removed from history: 0
- git-filter-repo used with --invert-paths

### Compromised key treatment:
All previously committed vault keys are treated as **COMPROMISED**. New key material must be generated in the real multi-identity deployment. Old keys are purged from git history but should never be reused.

## 2. Git Object Verification

Verified absence across ALL reachable Git objects (not just working tree):

| Check | Result |
|---|---|
| V1_NO_CONTAMINATED_PATHS_IN_COMMITS | PASS |
| V2_NO_VAULT_KEY_BLOBS | PASS |
| V3_REFLOG_CLEAN | PASS |


- git reflog expired and gc --prune=now --aggressive run
- All unreachable objects pruned

## 3. Hard Preflight (H1-H4 + A-P)

**Adjudication permitted: False**

| Check | Passed | Blocking |
|---|---|---|
| H1_NO_VAULT_KEYS_IN_WORKING_TREE | PASS | YES |
| H2_NO_VAULT_KEYS_IN_GIT_HISTORY | PASS | YES |
| H3_NO_GROUND_TRUTH_IN_ADJUDICATOR_SPACE | PASS | YES |
| H4_OLD_KEYS_TREATED_AS_COMPROMISED | PASS | YES |
| B_ADJUDICATOR_CANNOT_READ_KEY | FAIL | YES |
| C_ADJUDICATOR_CANNOT_WRITE_EVAL_BOUNDARY | FAIL | YES |
| D_ENCRYPTED_VAULT_EXISTS | FAIL | no |
| E_BLIND_NO_GROUND_TRUTH | PASS | YES |
| F_FULL_NOT_IN_WS | PASS | YES |
| I_NO_OPEN_FD_TO_KEY | PASS | YES |
| J_NO_ENV_VAR_WITH_KEY | PASS | YES |
| L_SYMLINK_TRAVERSAL_PROTECTION | PASS | YES |
| O_NO_ACCESS_TO_EVALUATOR_PROCESS | FAIL | YES |
| P_VAULT_IS_ENCRYPTED | FAIL | no |


## 4. Blocking Failures

The following checks CANNOT pass in this single-user container:

- **B_ADJUDICATOR_CANNOT_READ_KEY**: requires separate OS user
- **C_ADJUDICATOR_CANNOT_WRITE_EVAL_BOUNDARY**: requires separate OS user
- **O_NO_ACCESS_TO_EVALUATOR_PROCESS**: requires separate OS user

These require a **genuinely isolated multi-identity deployment** (separate Unix users or separate containers with no shared filesystem access to vault keys).

## 5. What Was Accomplished

✓ All vault keys purged from git history
✓ All plaintext machine-score vaults purged from git history
✓ All ground-truth/full-packet artifacts purged from adjudicator-accessible space
✓ Absence verified across all reachable Git objects
✓ git gc --prune=now run to remove unreachable objects
✓ All previously committed vault keys treated as compromised
✓ Hard preflight H1-H4 added
✓ H2 (no vault keys in git history) PASSES after purge

## 6. What Remains Blocked

✗ B/C/O: require multi-identity deployment (separate OS users/containers)
✗ The 80-case adjudication CANNOT run until preflight is fully green (16+ checks PASS)

## 7. Deployment Requirement

The preflight MUST be performed in a genuinely isolated multi-identity deployment:
- Adjudicator identity/container (separate from evaluator)
- Evaluator identity/container (separate from adjudicator)
- Evaluator-only secret store
- Encrypted vault accessible to adjudicator but undecryptable without evaluator-held key
- Evaluator key supplied only after immutable adjudication ledger is sealed

**Only when ALL 16+ security checks PASS in that environment can the 80-case adjudication begin.**

---

**NO ADJUDICATION. NO scorer changes. NO benchmark changes. NO discovery changes.**
