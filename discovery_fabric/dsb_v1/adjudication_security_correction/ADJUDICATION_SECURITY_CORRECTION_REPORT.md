# ADJUDICATION SECURITY CORRECTION REPORT

**Date:** 2026-08-12T19:18:38.850172+00:00
**Verdict:** ADJUDICATION CANNOT START IN THIS ENVIRONMENT

## 1. Vault Key Removal

All vault keys removed from repository:
- `adjudication_engine_v2/evaluator_boundary/vault_key.json` — REMOVED
- `adjudication_engine_v3/evaluator_boundary/vault_key.bin` — REMOVED
- `adjudication_engine_v3/evaluator_boundary/vault_key_META.json` — REMOVED
- `adjudication_engine_v1/vault/machine_score_vault.json` — REMOVED (plaintext)

## 2. False OS-Isolation Claims Fixed



## 3. Hard Preflight Results (16 checks)

**Adjudication permitted: False**

| Check | Passed | Blocking |
|---|---|---|
| A_NO_VAULT_KEYS_IN_REPO | PASS | YES |
| B_ADJUDICATOR_CANNOT_READ_KEY | FAIL | YES |
| C_ADJUDICATOR_CANNOT_WRITE_EVAL_BOUNDARY | FAIL | YES |
| D_ENCRYPTED_VAULT_EXISTS | PASS | YES |
| E_BLIND_NO_GROUND_TRUTH | PASS | YES |
| F_FULL_NOT_IN_WS | PASS | YES |
| G_NO_HIDDEN_COPIES | PASS | YES |
| H_GIT_NO_VAULT_KEYS | FAIL | YES |
| I_NO_OPEN_FD_TO_KEY | PASS | YES |
| J_NO_ENV_VAR_WITH_KEY | PASS | YES |
| K_NO_INHERITED_FDS | PASS | YES |
| L_SYMLINK_TRAVERSAL_PROTECTION | PASS | YES |
| M_NO_TEMP_KEY_FILES | PASS | YES |
| N_NO_BACKUP_FILES | PASS | YES |
| O_NO_ACCESS_TO_EVALUATOR_PROCESS | FAIL | YES |
| P_VAULT_IS_ENCRYPTED | PASS | YES |


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
