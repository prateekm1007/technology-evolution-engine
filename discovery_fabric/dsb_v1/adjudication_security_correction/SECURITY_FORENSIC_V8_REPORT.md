# SECURITY FORENSIC V8 — DEPLOYMENT SEPARATION REPORT

**Date:** 2026-08-12T20:16:52.605323+00:00
**Verdict:** BLOCKED — environment remains blocked
**V8 is green:** NO

## 1. External Adjudicator Bundle

The adjudicator bundle is now an **EXTERNAL build artifact** emitted OUTSIDE the Git working tree.

- **Build ID:** `a2cf8c14-670e-43eb-975f-f13926fbcd8c` (immutable, UUID4)
- **Build timestamp:** 2026-08-12T20:16:27.837171+00:00
- **Build location:** `/home/z/my-project/adjudicator_bundle`
- **Inside repo:** False (must be False)
- **Bundle export hash:** `be1277641495d0c246340bfb80a71c4c...`

### Bundle contents (ONLY):
- `cto_packets_BLIND.json` (127780 bytes, SHA-256: `0eb79566718b5a68c3ac994686861ebf...`) — 80 blinded adjudication packets (no ground truth)
- `CTO_ADJUDICATION_INSTRUCTIONS.md` (2216 bytes, SHA-256: `6182819ceb5edc8d83ebfc6388420b4a...`) — Adjudication rubric and instructions
- `cto_adjudication_template.json` (33643 bytes, SHA-256: `813fedc6129a3db68676357bfe5a6c4e...`) — Empty adjudication ledger template (80 slots)


### Bundle is NOT tracked in Git:
The `discovery_fabric/dsb_v1/adjudicator_bundle/` directory has been removed from Git tracking and added to `.gitignore`. The bundle is emitted to `/home/z/my-project/adjudicator_bundle` which is provably outside the research repository.

## 2. V8 Hard Invariant

```
adjudicator_bundle_path ∉ research_repo
```

**Result:** PASS
- Bundle path: `/home/z/my-project/adjudicator_bundle`
- Inside repo: False
- Git-tracked bundle files: none

## 3. V8 Preflight (V8 invariant + V6 + Q)

| Check | Status | Executable | Passed | Blocking |
|---|---|---|---|---|
| V8_BUNDLE_OUTSIDE_REPO | PASS | Y | Y | Y |
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
adjudicator_bundle_path ∉ research_repo
adjudication_permitted == FALSE until external deployment proves B/C/D/P/O/Q
```

**Result:** False — BLOCKED

## 5. Block Reasons

- B_ADJUDICATOR_CANNOT_READ_KEY: ENVIRONMENT_BLOCKED
- C_ADJUDICATOR_CANNOT_WRITE_EVAL_BOUNDARY: ENVIRONMENT_BLOCKED
- D_ENCRYPTED_VAULT_EXISTS: FAILED
- O_NO_ACCESS_TO_EVALUATOR_PROCESS: ENVIRONMENT_BLOCKED
- P_VAULT_IS_ENCRYPTED: FAILED
- Q_RESEARCH_REPO_INACCESSIBLE_TO_ADJUDICATOR: ENVIRONMENT_BLOCKED


## 6. Deployment Architecture (V8)

```
┌──────────────────────────────┐         ┌──────────────────────────────┐
│  ADJUDICATOR MACHINE         │         │  EVALUATOR MACHINE           │
│  (separate OS user/container)│         │  (separate OS user/container)│
│                              │         │                              │
│  Receives ONLY:              │         │  Retains:                    │
│    external bundle artifact  │         │    research repo + .git/     │
│    (built outside Git tree)  │         │    case files                │
│                              │         │    receipts/ scores/         │
│    /adjudicator_bundle/      │         │    evaluator_boundary/       │
│      cto_packets_BLIND.json  │         │    vault key                 │
│      instructions            │         │    frozen scorer             │
│      empty template          │         │                              │
│      BUNDLE_MANIFEST.json    │         │  Q7-Q10 run HERE proving     │
│                              │         │    adjudicator cannot read:  │
│  Q7-Q10 run HERE proving:    │         │      (N/A — evaluator has    │
│    research repo inaccessible│         │       access to its own      │
│    .git inaccessible         │         │       files)                 │
│    evaluator ns inaccessible │         │                              │
│    case files inaccessible   │         │                              │
│                              │         │                              │
│  Network: isolated           │         │  Network: isolated           │
└──────────────────────────────┘         └──────────────────────────────┘
```

The external bundle artifact is transferred to the adjudicator machine via
a secure channel (e.g., signed tarball, scp). The adjudicator machine has
NO access to the research repository, Git objects, case files, evaluator
namespace, receipts, scores, or the scorer.

## 7. What Is Required

`adjudication_permitted` remains **FALSE** until the external deployment proves:
- **B**: Adjudicator cannot read vault key
- **C**: Adjudicator cannot write evaluator boundary
- **D**: Encrypted vault exists (freshly generated)
- **P**: Vault is encrypted (AES-GCM)
- **O**: No access to evaluator process
- **Q**: Research repo inaccessible to adjudicator (Q7-Q10 on adjudicator machine)

## 8. What Was NOT Modified

- DSB V1 cases (20 files): NOT modified
- DSB V1 prompts: NOT modified
- DSB V1 receipts (80 files): NOT modified
- DSB V1 scorer: NOT modified
- Research repository: NOT modified

---

**V8 is NOT green. Environment remains BLOCKED. External bundle is ready for transfer to adjudicator machine. STOP.**
