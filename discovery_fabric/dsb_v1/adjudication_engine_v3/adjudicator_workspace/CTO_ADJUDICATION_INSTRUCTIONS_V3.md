# CTO ADJUDICATION INSTRUCTIONS V3 — DSB V1

**Engine:** ADJUDICATION_ENGINE_V3 (security hardening of V2)
**Date:** 2026-08-12T19:07:52.796483+00:00
**Vault sealed at:** 2026-08-12T19:07:52.781635+00:00
**Encryption:** AES-256-GCM (authenticated)
**Evidence tier:** AI_CTO_ADJUDICATION (NOT HUMAN_VALIDATED)
**Attacker tests:** 10/12 PASS

---

## 1. What Changed in V3 (vs V2)

V2 declared isolation but did not enforce it. V3 enforces it per the
**isolation-is-not-evidence principle** (ANTI_ENTROPY.md, 2026-08-12):

> A declaration that something is isolated is not evidence that it is
> isolated. The system needs to make cheating technically impossible,
> not merely forbidden.

### V2 → V3 changes:
- **Custom crypto fallback REMOVED.** V3 requires AES-GCM (authenticated encryption). Missing `cryptography` library = hard failure.
- **AES-GCM with authentication tag.** Tampered ciphertext is rejected with InvalidTag.
- **OS permission boundary: NOT ENFORCED in this environment.** Single-user container — adjudicator has same UID. ATTACK_A and ATTACK_H FAIL. Adjudication CANNOT start here.
- **Comprehensive attacker test.** 12 attack vectors tested.
- **Workspace hygiene scan.** Adjudicator workspace verified free of hidden copies, backups, bytecode, temp plaintext, shell history, logs, env secrets.

## 2. Attacker Test Results

10/12 checks PASS.

- ✗ **ATTACK_A_READ_VAULT_KEY_DIRECTLY**: KEY READABLE — OS permission boundary NOT enforced (single-user container, no root)
- ✓ **ATTACK_B_DECRYPT_WITHOUT_KEY**: InvalidTag — AES-GCM authentication rejected wrong key
- ✓ **ATTACK_C_DECRYPT_TAMPERED_CIPHERTEXT**: InvalidTag — AES-GCM detected tampering
- ✓ **ATTACK_D_SYMLINK_TRAVERSAL**: ELOOP — O_NOFOLLOW rejected symlink (defensive open path enforced)
- ✓ **ATTACK_E_PROC_VISIBILITY**: No open fd points to vault key
- ✓ **ATTACK_F_ENV_VAR_LEAKAGE**: No environment variable contains the vault key
- ✓ **ATTACK_G_INHERITED_FDS**: Closed 1 inherited fds; 0 remain
- ✗ **ATTACK_H_WRITABLE_EVALUATOR_BOUNDARY**: ADJUDICATOR CAN WRITE — OS permission boundary NOT enforced (single-user container, no root)
- ✓ **ATTACK_I_NO_HIDDEN_COPIES**: Workspace clean
- ✓ **ATTACK_J_BLIND_PACKETS_NO_GROUND_TRUTH**: No ground-truth fields in BLIND packets
- ✓ **ATTACK_K_FULL_PACKETS_NOT_IN_ADJUDICATOR_WS**: FULL packets NOT in adjudicator workspace
- ✓ **ATTACK_L_VAULT_IS_ENCRYPTED**: Vault is encrypted (32312 bytes, not valid JSON)


## 3. Single-User Environment Limitations

This environment is a single-user container. The following checks document
limitations that would be enforced in a real multi-user deployment:



**Real deployment:** Run adjudicator and evaluator as separate Unix users
OR separate containers. The adjudicator user must not have read permission
on evaluator_boundary/vault_key.bin. The AES-GCM encryption is the primary
control in this single-user env; OS permissions are the primary control in
a real deployment.

## 4. Six Observable Questions Per Packet

(Same as V2 — no change to adjudication criteria)

- Q1 MECHANISTIC_VALIDITY (YES/PARTIAL/NO)
- Q2 DISCOVERY_STRUCTURE_VALIDITY (YES/PARTIAL/NO)
- Q3 NOVELTY (YES/PARTIAL/NO)
- Q4 FALSIFIABILITY (YES/NO)
- Q5 EXPERIMENTAL_COHERENCE (YES/PARTIAL/NO)
- Q6 PLAUSIBILITY (PLAUSIBLE/IMPLAUSIBLE/UNCERTAIN) — NOT ground-truth REAL/FABRICATED

## 5. Submission + Sealing

1. Copy `cto_adjudication_template.json` to `cto_adjudication.json`.
2. Fill in all 80 adjudication slots.
3. Fill in `submitted_at` and `time_spent_minutes`.
4. **Seal the ledger:** compute SHA-256 of the ledger (excluding ledger_hash) and add it as `ledger_hash`.
5. Save.

## 6. After Submission

Run:
```bash
python3 discovery_fabric/dsb_v1/adjudication_engine_v3/run_v3_comparison.py
```

## 7. Evidence Tier

AI_CTO_ADJUDICATION — NOT HUMAN_VALIDATED. No architecture change permitted
based on this adjudication alone.

---

**End of V3 CTO Adjudication Instructions.**
