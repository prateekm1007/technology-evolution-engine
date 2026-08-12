# SECURITY FORENSIC V7 — FINAL BOUNDARY CORRECTION REPORT

**Date:** 2026-08-12T20:07:40.010848+00:00
**Verdict:** BLOCKED — environment remains blocked
**V7 is green:** NO

## 1. Adjudicator Bundle

A minimal adjudicator bundle has been created at `discovery_fabric/dsb_v1/adjudicator_bundle/`.

### Bundle contents (ONLY):
- `cto_packets_BLIND.json` (127780 bytes, SHA-256: `0eb79566718b5a68c3ac994686861ebf...`) — 80 blinded adjudication packets (no ground truth)
- `CTO_ADJUDICATION_INSTRUCTIONS.md` (2869 bytes, SHA-256: `261d648d6f7006b79dc7920912a0a7cf...`) — Adjudication rubric and instructions
- `cto_adjudication_template.json` (33643 bytes, SHA-256: `813fedc6129a3db68676357bfe5a6c4e...`) — Empty adjudication ledger template (80 slots)


### Bundle MUST NOT contain:
- case files (cases/real/, cases/fabricated/)
- real/fabricated labels (case_type field)
- breakthrough_relationship text
- withheld_facts text
- answer_mechanism text
- machine receipts (receipts/)
- machine scores (scores/)
- full packets (cto_packets_FULL.json)
- evaluator secrets (vault_key*, machine_score_vault*)
- Git metadata (.git/)
- research repository code (discovery_fabric/)


### Forbidden files check: PASS"

## 2. Q_RESEARCH_REPO_INACCESSIBLE_TO_ADJUDICATOR (NEW)

Q is a mandatory blocking prerequisite. It proves the adjudicator process cannot read:
- The research repository
- Git objects (.git/)
- Case files (cases/real/, cases/fabricated/)
- Evaluator namespace (evaluator_boundary/)
- Receipts and scores
- The frozen scorer

### Q subcheck results:

| Subcheck | Status |
|---|---|
| Q1_BUNDLE_NO_EXTERNAL_SYMLINKS | PASS |
| Q2_BUNDLE_NO_GIT_METADATA | PASS |
| Q3_BUNDLE_NO_CASE_FILES | PASS |
| Q4_BUNDLE_NO_RECEIPTS_OR_SCORES | PASS |
| Q5_BUNDLE_NO_VAULT_KEYS | PASS |
| Q6_BUNDLE_NO_FULL_PACKETS | PASS |
| Q7_ADJUDICATOR_CANNOT_READ_RESEARCH_REPO | ENV_BLOCKED |
| Q8_ADJUDICATOR_CANNOT_READ_GIT_OBJECTS | ENV_BLOCKED |
| Q9_ADJUDICATOR_CANNOT_READ_CASE_FILES | ENV_BLOCKED |
| Q10_ADJUDICATOR_CANNOT_READ_EVALUATOR_BOUNDARY | PASS |


**Q overall: ENVIRONMENT_BLOCKED** (7/10 subchecks pass, 3 environment-blocked)

## 3. Full V7 Preflight (V6 checks + Q)

| Check | Status | Executable | Passed | Blocking |
|---|---|---|---|---|
| H1_NO_VAULT_KEYS_IN_WORKING_TREE | PASS | Y | Y | Y |
| H2_TRUE_FORBIDDEN_ARTIFACT_AUDIT | PASS | Y | Y | Y |
| F_RECURSIVE_NAMESPACE_INSPECTION | PASS | Y | Y | Y |
| H4_OLD_KEYS_TREATED_AS_COMPROMISED | PASS | Y | Y | Y |
| B_ADJUDICATOR_CANNOT_READ_KEY | ENV_BLOCKED | N | N | Y |
| C_ADJUDICATOR_CANNOT_WRITE_EVAL_BOUNDARY | ENV_BLOCKED | N | N | Y |
| D_ENCRYPTED_VAULT_EXISTS | FAIL | Y | N | Y |
| E_RECURSIVE_BLIND_INSPECTION | PASS | Y | Y | Y |
| F_RECURSIVE_NAMESPACE_INSPECTION | PASS | Y | Y | Y |
| I_NO_OPEN_FD_TO_KEY | PASS | Y | Y | Y |
| J_NO_ENV_VAR_WITH_KEY | PASS | Y | Y | Y |
| K_NO_INHERITED_FDS | PASS | Y | Y | Y |
| L_SYMLINK_TRAVERSAL_PROTECTION | PASS | Y | Y | Y |
| M_DETERMINISTIC_FORBIDDEN_MANIFEST | PASS | Y | Y | Y |
| N_NO_BACKUP_FILES | PASS | Y | Y | Y |
| O_NO_ACCESS_TO_EVALUATOR_PROCESS | ENV_BLOCKED | N | N | Y |
| P_VAULT_IS_ENCRYPTED | FAIL | Y | N | Y |
| Q_RESEARCH_REPO_INACCESSIBLE_TO_ADJUDICATOR | ENV_BLOCKED | N | N | Y |


## 4. Hard Invariant

```
adjudication_permitted == TRUE
ONLY IF every required check has:
  executable_test == true
  passed == true
```

**Result:** False — BLOCKED

## 5. Block Reasons

- B_ADJUDICATOR_CANNOT_READ_KEY: ENVIRONMENT_BLOCKED
- C_ADJUDICATOR_CANNOT_WRITE_EVAL_BOUNDARY: ENVIRONMENT_BLOCKED
- D_ENCRYPTED_VAULT_EXISTS: FAILED
- O_NO_ACCESS_TO_EVALUATOR_PROCESS: ENVIRONMENT_BLOCKED
- P_VAULT_IS_ENCRYPTED: FAILED
- Q_RESEARCH_REPO_INACCESSIBLE_TO_ADJUDICATOR: ENVIRONMENT_BLOCKED


## 6. Deployment Architecture

```
┌──────────────────────────────┐         ┌──────────────────────────────┐
│  ADJUDICATOR MACHINE         │         │  EVALUATOR MACHINE           │
│  (separate OS user/container)│         │  (separate OS user/container)│
│                              │         │                              │
│  Has: adjudicator_bundle/    │         │  Has: research repo +        │
│    - cto_packets_BLIND.json  │         │    - case files              │
│    - instructions            │         │    - receipts/ scores/       │
│    - empty template          │         │    - evaluator_boundary/     │
│    - BUNDLE_MANIFEST.json    │         │    - vault key               │
│                              │         │    - frozen scorer           │
│  Does NOT have:              │         │    - .git/                   │
│    - research repo ✗         │         │                              │
│    - .git/ ✗                 │         │  Cannot access:              │
│    - case files ✗            │         │    - adjudicator_bundle/     │
│    - evaluator_boundary/ ✗   │         │      (until ledger sealed)   │
│    - receipts/ scores/ ✗     │         │                              │
│    - vault key ✗             │         │                              │
│    - scorer.py ✗             │         │                              │
│                              │         │                              │
│  Network: isolated           │         │  Network: isolated           │
└──────────────────────────────┘         └──────────────────────────────┘
```

The adjudicator bundle is a SELF-CONTAINED artifact. It is extracted to a
separate machine/container that has ZERO access to the research repository.
The adjudicator cannot read Git objects, case files, evaluator boundary,
receipts, scores, or the scorer.

## 7. What Is Required

Only after **B/C/D/P/O/Q all pass** in a true multi-identity deployment can
the 80 adjudications begin:

- **B**: Adjudicator cannot read vault key (OS-enforced, separate user)
- **C**: Adjudicator cannot write evaluator boundary (OS-enforced)
- **D**: Encrypted vault exists (freshly generated with new key)
- **O**: No access to evaluator process (separate users, ptrace checks)
- **P**: Vault is encrypted (AES-GCM authenticated)
- **Q**: Research repo inaccessible to adjudicator (separate machine/container)

## 8. What Was NOT Modified

- DSB V1 cases (20 files): NOT modified
- DSB V1 prompts: NOT modified
- DSB V1 receipts (80 files): NOT modified
- DSB V1 scorer: NOT modified
- FREEZE_MANIFEST.json: NOT modified
- Research repository: NOT modified

---

**V7 is NOT green. Environment remains BLOCKED. The adjudicator bundle is ready for deployment to a separate machine. STOP.**
