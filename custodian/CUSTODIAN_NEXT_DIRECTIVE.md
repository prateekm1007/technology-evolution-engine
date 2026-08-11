# CUSTODIAN / CTO NEXT DIRECTIVE

## Status

Custodian software baseline: **ACCEPTED WITH DEPLOYMENT GATE**

Baseline commit: `f992e12`

The custodian package is not a benchmark. No real corpus has been ingested, no real benchmark has been constructed, and no benchmark has been sealed.

## Directive

Proceed to the next task: **CUSTODIAN_CORPUS_INTAKE_V1**.

This task must not modify TEE, DXP-005, NORTH_STAR_GATE_A_V1, Gate A/B definitions, frozen arm specifications, statistical rules, or any existing scientific protocol.

Do not construct a real benchmark. Do not synthesize a substitute corpus. Do not run TEE against any real or synthetic benchmark as an evaluation.

## Objective

Build an intake boundary through which an independent custodian can introduce a real external corpus while preserving provenance, contamination detection, custody state, and separation from TEE.

## Required capabilities

1. Immutable source registration.
2. SHA-256 content identity for every source and source version.
3. Acquisition provenance and timestamp recording.
4. Source-version tracking.
5. Exact duplicate detection.
6. Near-duplicate detection with explicit `FLAGGED` state; never silent rejection.
7. Canonical-domain classification using the hardened taxonomy.
8. TEE prior-exposure detection across repository artifacts, indexed corpus material, prior fixtures, generated outputs, caches, and available retrieval stores.
9. Benchmark/answer-key contamination detection.
10. Custodian-only quarantine state.
11. Machine-readable intake manifest.
12. Human-readable intake audit report.
13. Append-only audit trail.
14. Explicit source states: `ELIGIBLE`, `FLAGGED`, `REJECTED`, `UNDETERMINABLE`.
15. Recursive leak detection for answer-key-like material and TEE-derived content.
16. A deployment-isolation verification harness proving that the TEE execution identity cannot read, enumerate, mount, or obtain the custodian answer-key store.
17. Tests proving TEE output cannot influence or mutate intake/custody state.

## Independence rule

The intake system must distinguish:

- `UNSEEN`
- `POSSIBLY_SEEN`
- `KNOWN_SEEN`
- `UNDETERMINABLE`

Prior exposure is a custody signal. It must not be silently converted into eligibility or rejection. Final eligibility is a custodian decision recorded in the audit trail.

## Scientific classes to preserve

The intake metadata should support later classification into:

- genuine cross-domain opportunity
- hard null / plausible non-connection
- retrieval-obvious connection
- frontier-LLM-recoverable connection
- expert-obvious connection
- obscure potential connection
- mechanistically incompatible pair

These classifications are intake metadata only. They must not be used to optimize the benchmark after sealing.

## Deployment gate

Code-level permission checks are insufficient. Before a real benchmark is sealed, the actual execution environment must demonstrate:

1. TEE can read the blind fixture.
2. TEE cannot read the answer-key path.
3. TEE cannot enumerate the answer-key directory.
4. TEE cannot access the answer key through an alternate mount.
5. Answer-key material is absent from TEE environment variables.
6. Answer-key material is absent from logs, caches, temporary files, artifacts, backups, and process arguments.
7. Custodian identity can access the answer key.
8. TEE cannot escalate to the custodian identity.

The deployment test must record the execution identity, mount topology, relevant permissions, and test results. It must not copy answer-key contents into the TEE environment merely to test access.

## Required test standard

Add regression/adversarial tests for every capability above. Synthetic fixtures are permitted only for testing the custody machinery and must remain explicitly marked `NOT_FOR_EVALUATION`.

At completion, report:

- total test count and result;
- attack coverage;
- what the software proves;
- what remains deployment-enforced;
- exact external-custodian inputs required for real corpus intake.

## Stop condition

When CUSTODIAN_CORPUS_INTAKE_V1 is complete and audited:

**STOP.**

Do not ingest a real corpus until an independent source is actually supplied and the custodian explicitly authorizes intake.

Do not declare the North Star benchmark ready.

The next real-world dependency remains independent scientific material.
