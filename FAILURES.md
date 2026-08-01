# FAILURES

Every entry here was reproduced live, not inferred from reading code. Status
is current as of commit `01db12f`. New entries append; existing entries are
never edited except to change `status` and add a `resolved_in` commit —
per CONSTITUTION.md Law 7, historical permanence.

---

### F-001 — PatentParser silently returns empty output on realistic input
**Found:** forensic audit, this session.
**Repro:** POST loosely-formatted patent prose (no numbered claims, no
`comprising`/`coupled to` trigger phrases) to `/api/v1/business/analyze`.
**Observed:** `200 OK`, `confidence: 0.0`, zero components/candidates/blueprints.
No error surfaced.
**Root cause:** `product/ingestion/patent_parser.py` extraction is a fixed
set of regex trigger phrases. Text that doesn't happen to contain them
extracts nothing.
**Severity:** P1 — a business user uploading a real patent in non-claims
prose gets a confident-looking empty report with no indication anything
went wrong.
**Status:** OPEN.

### F-002 — Two disconnected FastAPI apps, no canonical surface
**Found:** forensic audit, this session.
**Observed:** `web/backend/main.py` (frontend + verification contract) and
`product/api/app.py` (business/consumer routes, no frontend, no
verification contract) both exist, both work, neither calls the other.
**Root cause:** parallel development, never reconciled.
**Severity:** P0 — ambiguous which is "the product."
**Status:** OPEN — decision needed, not a code fix.

### F-003 — Web schema fields didn't map to pipeline input keys
**Found:** while implementing the previous session's proposed fix to F-006.
**Repro:** `POST /api/v1/analyze` with `{"text": "..."}` after wiring
`CoreAdapter` — response came back with empty `problem_summary`,
`detected_domains: ["general"]`, despite the pipeline call succeeding.
**Root cause:** `TextNormalizer.run()` / `PatentParser.run()` read
`raw_text`/`problem_statement`; `AnalyzeRequest` sends `text`/`title`.
FastAPI silently drops unrecognized fields, so nothing errored — the
pipeline just received an empty string.
**Severity:** P1 — same class as MaestroAgent's `owner`/`commitment_owner`
mismatch: a cross-boundary dict-key contract nobody wrote down.
**Status:** RESOLVED in `01db12f` — explicit key mapping added in
`analyze()`, with a regression test (`test_analyze_actually_consumes_input_text`).

### F-004 — Consumer scoring collapses to near-duplicate results across distinct inputs
**Found:** forensic audit, this session.
**Repro:** POST two unrelated problem statements ("reduce household water
consumption" vs "grow food indoors with minimal energy") to
`/api/v1/consumer/solve`.
**Observed:** both return the same duplication pattern — top result
repeated 3x differing only by `operator_applied`, near-identical
feasibility/novelty scores.
**Root cause:** `product/permutation/engine.py::_score()` computes
`feasibility`/`novelty`/`pcs` from operator type and element count alone —
no signal from the actual extracted content. Short consumer prompts (2-3
elements) collapse to a handful of scoring buckets regardless of topic.
**Severity:** P1 — undermines perceived product value; second query a user
runs looks suspiciously like the first.
**Status:** OPEN.

### F-005 — Prediction ledger is corrupted at the byte level
**Found:** while diagnosing F-006's `/api/v1/evidence` 500.
**Repro:** `open('data/ledger/predictions.jsonl').read().splitlines()`.
**Observed:** 704 one-character "lines" from a 1403-byte file — a literal
`\n` inserted after every character.
**Root cause:** unknown — not yet traced to the writer. Not something a
`.jsonl.strip()` fix addresses; the file itself needs regenerating.
**Severity:** P0 for the "verified" label specifically — this file is the
only mechanism for recording prediction outcomes. See
`evidence/reports/verification_report.json`: nothing in this repo can
honestly claim "verified" under the amended rule until this is fixed.
**Status:** RESOLVED — ledger regenerated from a known writer
(`scripts/run_evidence_tests.py::log_to_ledger` +
`scripts/run_verification_cycle.py::reconcile`). 10 entries, all
parseable, all carry a `writer` field. F-014 regression tests now
pass. See F-AUD-004 in `AUDIT.md` for the audit that caught the
stale OPEN status.

### F-006 — `/api/v1/evidence` 500s on the corrupted ledger
**Found:** forensic audit, this session.
**Repro:** `GET /api/v1/evidence` with the corrupted ledger in place.
**Observed:** `JSONDecodeError` unhandled, `500 Internal Server Error`.
**Root cause:** no error handling around `json.loads()` per line.
**Severity:** P1.
**Status:** RESOLVED in `01db12f` — malformed lines now collected and
returned in `malformed_lines` instead of crashing. F-005 (the underlying
data corruption) remains open.

### F-007 — `web/frontend/` did not exist; documented run path crashed on import
**Found:** forensic audit, this session.
**Repro:** `pip install -r web/requirements.txt && ./web/run.sh` per
`web/README.md`.
**Observed:** `RuntimeError: Directory '.../web/frontend' does not exist`,
crash before uvicorn started listening.
**Root cause:** `app.mount("/static", StaticFiles(directory=FRONTEND))`
pointed at a directory never committed.
**Severity:** P0 — no consumer or business surface existed at all.
**Status:** RESOLVED in `7af85d9`.

### F-008 — `POST /api/v1/analyze` returned hardcoded output regardless of input
**Found:** forensic audit, immediately after F-007's fix landed.
**Repro:** two different request bodies, byte-identical responses.
**Root cause:** endpoint returned `SPECIMEN["analysis"]` unconditionally;
`adapters/core.py` existed but was never imported.
**Severity:** P0 — the one action a real user takes did nothing with what
they typed.
**Status:** RESOLVED in `01db12f`, contingent on F-003 also being fixed
(the first wiring attempt alone was insufficient — see F-009).

### F-009 — `CoreAdapter.run_pipeline()` called methods that don't exist
**Found:** while verifying the fix for F-008, before pushing.
**Repro:** call `CoreAdapter(...).run_pipeline(...)`.
**Observed:** `AttributeError` — `ConsumerPipeline`/`BusinessPipeline` only
expose `.run()`; the adapter called `.solve()`/`.analyze()`.
**Root cause:** adapter written against an assumed interface, never run
against the real classes before being proposed as a fix.
**Severity:** would have shipped as "wired" while silently falling back to
the F-008 stub on every real call — worse than F-008 because it looks
fixed under a `verified` label.
**Status:** RESOLVED in `01db12f`, caught by running the fix before
pushing it, not by reading it.

### F-010 — `layout_cache.compute_layout()` called `mkdir()` on a file path
**Found:** forensic audit, this session (dead code, never executed in
production, so no live repro — traced by reading).
**Root cause:** `cache = dir / "layout_<key>.json"` then `cache.mkdir(...)`
— creates a directory with a `.json`-suffixed name, then
`cache.write_text()` raises `IsADirectoryError`.
**Severity:** P2 — file is unwired into any route, so currently inert.
**Status:** RESOLVED in `01db12f`. Still unwired — see F-002.

---

### F-011 — `scripts/verify_stack.py` stamps `oracle: "verified"` without any ledger backing
**Found:** F-005 follow-up forensic audit (this session).
**Repro:** `python scripts/verify_stack.py` (with `data/civilization_graph.json`
present, which is the default).
**Observed:** report prints `"oracle": "verified"` because `gm.source == "core"`.
The condition for the "verified" stamp is "the civilization graph file
parses" — which is presence-of-data, not verification. There is no successful
prediction, no failed prediction, and no replayable evidence in the ledger
behind this label. This is exactly the Law 8 violation F-005 warned about.
**Root cause:** `scripts/verify_stack.py:15` uses `gm.source == "core"` as a
proxy for "verified", but `source == "core"` only means "the static graph
file loaded successfully". That is an integration check, not a verification.
**Severity:** P1 — the script's output is consumed by humans as a verification
report, and the script lies.
**Status:** OPEN — label should be downgraded to "integrated" until a real
prediction → observe → reconcile loop exists and is logged to a working
ledger. The Law 8 enforcement script (`scripts/enforce_law8.py`) now flags
this automatically.

### F-012 — `INTERFACES.md` documents `"verified"` as a possible `level` value, but no endpoint actually produces it honestly
**Found:** F-005 follow-up forensic audit (this session).
**Observed:** `INTERFACES.md:44` declares the response contract
`{"level": "verified" | "implemented", ...}`, listing "verified" as if it
were a value the system could honestly produce. In reality, the only code
path that ever assigned "verified" (`/api/v1/analyze` in `web/backend/main.py`)
was downgraded to "integrated" in commit `01db12f` for exactly this reason
(see F-001 follow-up in `tests/test_endpoints.py`). The contract is now
aspirational: it advertises a label the system cannot honestly produce.
**Root cause:** documentation drift. The interface spec was written when
"verified" was still being claimed; it was not updated when the claim was
retracted.
**Severity:** P2 — does not affect runtime behavior, but misleads anyone
reading the spec to plan an integration.
**Status:** OPEN — the contract should either drop "verified" from the
allowed-values list, or be reworded as "verified (not currently achievable
under Law 8; see evidence/reports/verification_report.json)".

### F-013 — `web/backend/adapters/core.py::evidence()` reads the ledger without total-corruption detection
**Found:** F-005 follow-up forensic audit (this session).
**Repro:** with the corrupted ledger in place, call
`CoreAdapter(repo_root=...).run_pipeline(...)` (or any path that touches
`web/backend/adapters/core.py:28-30`).
**Observed:** `JSONDecodeError` unhandled — `core.py` does
`[json.loads(l) for l in ledger.read_text().splitlines() if l.strip()]`
with no try/except, no total-corruption heuristic. The same crash that
F-006 fixed in `web/backend/main.py::evidence()` is still live in
`core.py`. The fix landed in only one of the two readers.
**Root cause:** parallel development. Two readers, one fix.
**Severity:** P1 — any caller of `CoreAdapter` that hits the ledger path
gets a 500 (or worse, a CLI crash). The route `/api/v1/analyze` does fall
through to this code on the success path.
**Status:** RESOLVED — `core.py::read_evidence()` now delegates to the
shared `_read_ledger_safely()` helper (introduced in F-AUD-002).
`main.py::evidence()` was refactored to use the same helper, so the
two readers can no longer drift. See F-AUD-002 in `AUDIT.md`.

### F-014 — F-005 regression tests confirmed failing on the corrupted state
**Found:** F-005 follow-up forensic audit (this session).
**Repro:** `pytest tests/test_ledger_integrity.py -v` with the corrupted
ledger at `data/ledger/predictions.jsonl` in place.
**Observed:**
- `test_every_committed_jsonl_line_parses` FAILS — 703 non-empty lines, 0 parse as JSON.
- `test_no_one_char_per_line_pattern` FAILS — 609 non-empty lines, max length 1.
- `test_ledger_schema_matches_writer` PASSES (vacuously) — the file does not parse, so the schema check is skipped and regression #1 is the single loud failure.
**Root cause:** this is the F-005 corruption itself, observed through the
regression tests added by this audit. The tests are working as designed:
they catch the corruption at commit time, on every commit, going forward.
**Severity:** informational — the tests are red because the underlying bug
is real, not because the tests are wrong.
**Status:** RESOLVED — the corrupted ledger was regenerated from a
known writer (see F-005 resolution above). The three regression tests
now pass: every line parses, no one-char-per-line pattern, and every
entry's schema matches a known writer. See F-AUD-004 in `AUDIT.md`.

### F-015 — `scripts/calibrate.py` reads the ledger without total-corruption detection
**Found:** F-005 follow-up forensic audit (this session).
**Repro:** `python scripts/calibrate.py` with the corrupted ledger in place.
**Observed:** `JSONDecodeError` — `calibrate.py:8` does
`[json.loads(l) for l in lp.read_text().splitlines() if l.strip()]`
with no error handling. Same crash class as F-013.
**Root cause:** same as F-013 — parallel ledger readers, none share
the corruption-aware read logic from `main.py::evidence()`.
**Severity:** P2 — `calibrate.py` is a manual CLI tool, not a runtime path.
But it's the script the user runs to actually recalibrate, so it should
fail loudly, not with a traceback.
**Status:** RESOLVED — `calibrate.py` now delegates to the shared
`_read_ledger_safely()` helper via its `read_ledger()` wrapper. See
F-AUD-003 in `AUDIT.md`.

---

### F-AUD-001 — DependencyModule._classify_edge_causally() called with source == target (walrus-operator bug)
**Found:** forensic audit (`AUDIT.md`).
**Repro:** `pytest tests/test_audit_findings.py::test_F_AUD_001_causal_classification_uses_target_not_source -v`.
**Observed:** the `causal_classifications` count in `dependency_module.analyze()` returned `{"necessary": 0, "sufficient": 0, "contributing": 0, "unknown": 0}` for a test graph where ground truth is `necessary=2, contributing=2`. The per-prereq `causal_classification` field was missing from every prereq in the output.
**Root cause:** `dependency_module.py:160` used the walrus operator `target_id if (target_id := p.get("id")) else target_node_id`. Since prereqs always have ids, the walrus assigned `p["id"]` to `target_id` (always truthy), so `target` was always set to `p["id"]` — the same value as `source`. `_classify_edge_causally` then counted edges pointing INTO the prereq, not into the target. The entire causal-classification feature was structurally broken since commit `02d7658` (CTO review #2).
**Severity:** P1 — the CTO-mandated "depth over breadth" upgrade (causal edges, counterfactual analysis) was shipping a wrong answer with no test catching it. The existing test `test_dependency_module_exposes_causal_edges` only checked that the `causal_classifications` key existed, not that its values were correct — exactly the "test asserts the contract but not the correctness" failure mode the anti-entropy rules warn about.
**Status:** RESOLVED — walrus operator removed; `target_node_id` passed directly. Regression test added (`tests/test_audit_findings.py::test_F_AUD_001_*`).

### F-AUD-002 — `CoreAdapter.read_evidence()` crashes on corrupted ledger (F-013 still live)
**Found:** forensic audit (`AUDIT.md`). Closes F-013.
**Repro:** `pytest tests/test_audit_findings.py::test_F_AUD_002_core_adapter_read_evidence_handles_corrupted_ledger -v`.
**Observed:** `JSONDecodeError` on a one-char-per-line ledger — the same crash F-006 fixed in `main.py::evidence()`, still live in `core.py` because the fix landed in only one of two readers.
**Root cause:** parallel development (the F-013/F-015 class). Two ledger readers, one fix.
**Severity:** P1 — `/api/v1/analyze` falls through to `CoreAdapter` on the success path; a corrupted ledger would 500 the main user action.
**Status:** RESOLVED — both readers now share `_read_ledger_safely()` in `adapters/core.py`. `main.py::evidence()` refactored to call the same helper. The two readers can no longer drift.

### F-AUD-003 — `scripts/calibrate.py` crashes on corrupted ledger (F-015 still live)
**Found:** forensic audit (`AUDIT.md`). Closes F-015.
**Repro:** `pytest tests/test_audit_findings.py::test_F_AUD_003_calibrate_handles_corrupted_ledger -v`.
**Observed:** `JSONDecodeError` — same unguarded list comprehension as F-013.
**Root cause:** same as F-013 — three parallel ledger readers, none shared the corruption-aware logic.
**Severity:** P2 — `calibrate.py` is a manual CLI tool, but it's the script the user runs to recalibrate.
**Status:** RESOLVED — `calibrate.py` now exposes `read_ledger()` which delegates to the shared helper.

### F-AUD-004 — FAILURES.md marked F-005 and F-014 as OPEN after they were remediated (Law 7 violation)
**Found:** forensic audit (`AUDIT.md`).
**Repro:** `pytest tests/test_audit_findings.py::test_F_AUD_004_failures_md_marks_remediated_entries_resolved -v`.
**Observed:** F-005 marked OPEN but the ledger was regenerated (10 parseable entries, all carry `writer`). F-014 marked OPEN but its three regression tests pass.
**Root cause:** FAILURES.md is the canonical record of system state per Law 7 (historical permanence). When the ledger was remediated, the status lines for F-005 and F-014 were not updated. This is exactly the "documentation drift" entropy the anti-entropy rules exist to prevent — a future reader consulting FAILURES.md would conclude the system is more broken than it is.
**Severity:** P2 — does not affect runtime, but undermines trust in the failure taxonomy. If FAILURES.md lies about OPEN vs RESOLVED, the CTO review process can't rely on it.
**Status:** RESOLVED — F-005, F-013, F-014, F-015 status lines updated to RESOLVED with remediating references.

### F-AUD-005 — `verification_engine` is named "engine" but does not satisfy ANTI_ENTROPY.md's three-condition bar
**Found:** forensic audit (`AUDIT.md`).
**Observed:** `invention_compiler/verification_engine.py` is the ONLY file allowed to be named `*_engine.py` (enforced by `test_only_verification_engine_is_called_engine`). The ANTI_ENTROPY.md rule requires three conditions: (1) explicit model encoded in code, (2) empirical validation recorded in the ledger, (3) reproducible results. The file satisfies (3) but not (1) or (2): it produces f-string templates of experiments and success/failure criteria. It does not encode a verification model — it proposes one. The "empirical validation" condition is met by the *ledger entries* (9 verification records from `scripts/run_verification_cycle.py`), not by the `verification_engine.py` module itself.
**Root cause:** the naming-rule test checks file globs (`*_engine.py`), not whether the file meets the bar. This is exactly the "lies compound" failure mode ANTI_ENTROPY.md warns about: a future engineer reads `verification_engine` and assumes a verification model is encoded. It isn't.
**Severity:** P2 — does not affect runtime, but the naming overclaim is the same class of bug as F-011 (`scripts/verify_stack.py` stamping "verified" without evidence). The fix is either (a) rename to `verification_module.py` and update the naming test to allowlist zero engine files, or (b) actually encode a verification model (e.g., a Bayesian update of the prior given ledger outcomes) and record pass+fail evidence against it.
**Status:** OPEN — documented in `AUDIT.md`. Recommended action: option (a) for now (rename), option (b) when bandwidth allows. The naming-rule test should be tightened to check the file's *content* meets the bar, not just the filename.

### F-AUD-006 — physics/chemistry/mathematics modules claim "upgraded from keyword matching to encoding actual [scientific principles]" but the upgrade is documentation, not encoding
**Found:** forensic audit (`AUDIT.md`).
**Observed:** per CTO review #2 (commit `02d7658`), `physics_module`, `chemistry_module`, and `mathematics_module` were supposed to be upgraded from keyword matching to "encoding actual physical laws / reaction pathways / mathematical structures". The modules now contain large dictionaries of structured objects (equations, units, variables), but the equations are *strings*, not code. `physics_module.check_consistency()` is a 6-line hardcoded dict lookup of canonical equations — not dimensional analysis. `analyze()` still picks applicable laws via keyword maps (`DOMAIN_TO_LAWS`, `CONSTRAINT_TO_LAWS`). The modules document scientific principles; they do not encode them.
**Root cause:** the CTO directive in ANTI_ENTROPY.md is explicit: "A module that calls itself 'laws, equations, constraints, units, conservation principles' but actually does keyword matching is lying — and per the 'use the word engine honestly' rule, lies compound. Encode the actual principle or admit you haven't." The module docstrings do admit this in their "Law 8 honesty" sections ("the kinetics models are not solved against real data; they identify WHICH model would apply"), but the top-level claim "upgraded from keyword matching to encoding actual physical laws" overstates what landed.
**Severity:** P1 — the CTO review approved this state as "a genuine increase in maturity rather than an increase in complexity" based on the docstrings. If the docstrings overclaim, the review was misinformed. This is the same class of overclaim as F-AUD-005 and F-011.
**Status:** OPEN — documented in `AUDIT.md`. Recommended action: either (a) downgrade the top-level docstring claim to "documented scientific principles, not encoded solvers" (honest, low-effort), or (b) actually encode one solver per module (e.g., a real Arrhenius rate calculator in `chemistry_module`, a real dimensional-analysis checker in `physics_module`) and record pass+fail benchmark evidence against it. Option (b) is the CTO-mandated "depth over breadth" directive.

### F-AUD-007 — `graph_retriever._cem()` used bare `open().read()` (resource leak)
**Found:** forensic audit (`AUDIT.md`).
**Repro:** `pytest tests/test_audit_findings.py::test_F_AUD_007_graph_retriever_cemetery_scan_uses_context_manager -v`.
**Observed:** `product/retrieval/graph_retriever.py::_cem()` did `content = open(path).read().lower()` without a `with` statement. If `read()` raised (binary file, permissions error), the file descriptor leaked.
**Root cause:** Python resource-management anti-pattern. Not a security issue (the path is constructed from `os.listdir` of project-controlled directories, so no path traversal), but a correctness issue under error conditions.
**Severity:** P3 — minor; only manifests when `_cem()` encounters an unreadable file, which is rare in practice.
**Status:** RESOLVED — converted to `with open(...) as f:`. No behavior change on the happy path.

### F-AUD-008 — `product/api/routes.py` leaks raw exception strings into HTTP 500 responses
**Found:** forensic audit (`AUDIT.md`).
**Observed:** all three route handlers (`/api/v1/business/analyze`, `/api/v1/consumer/solve`, `/api/v1/analyze`) do `except Exception as e: raise HTTPException(status_code=500, detail=str(e))`. The raw exception string is returned to the client in the `detail` field.
**Root cause:** catch-all exception handling with no sanitization. Python tracebacks and exception messages can leak internal paths, file structure, and sometimes user input reflected back.
**Severity:** P2 — information disclosure. In a public-facing deployment, this would be a CVE-class issue (CWE-209: Generation of Error Message Containing Sensitive Information). For this repo's current "private, all rights reserved" license, it's a defensive-coding gap.
**Status:** OPEN — documented in `AUDIT.md`. Recommended action: log the full exception server-side; return a generic "internal error" message with a correlation id to the client. Out of scope for this audit PR (changes user-visible API contract).

### F-AUD-009 — `requirements.txt` uses `>=` soft floors with no lockfile (anti-entropy rule violation)
**Found:** forensic audit (`AUDIT.md`).
**Observed:** both `requirements.txt` (root) and `web/requirements.txt` use `>=` version specifiers. No `requirements.lock`, no `pip-compile` output, no hash-pinned deps.
**Root cause:** ANTI_ENTROPY.md rule "Lock dependencies" explicitly calls this out: "`requirements.txt` uses `>=` for soft floors. This is intentional for the dev environment but MUST be paired with a frozen `requirements.lock` file (or `pyproject.toml` with hash-pinned deps) for any production-bound deploy." The lock file does not exist.
**Severity:** P2 — reproducibility risk. A `pip install -r requirements.txt` today and one in 6 months may resolve to different versions, breaking Law 8 replayability ("re-running the model with the same inputs produces the same outputs, byte-exact").
**Status:** OPEN — documented in `AUDIT.md`. Recommended action: generate `requirements.lock` via `pip freeze` from a clean venv, commit it, and add a CI check that `requirements.txt` and `requirements.lock` are consistent.

### F-AUD-010 — `web/backend/main.py` mounts `StaticFiles` at import time (F-007 regression risk)
**Found:** forensic audit (`AUDIT.md`).
**Observed:** `app.mount("/static", StaticFiles(directory=FRONTEND), name="static")` runs at module import. If `FRONTEND` does not exist, the entire app fails to import — every endpoint 500s, not just `/static`. This is the exact failure mode F-007 fixed for the `index()` route (which now uses `FileResponse` and would 404 rather than crash).
**Root cause:** the F-007 fix was incomplete. `FileResponse` is lazy; `StaticFiles` mount is eager.
**Severity:** P2 — if the frontend directory is ever missing in a deploy (e.g., a backend-only container), the whole API dies at startup.
**Status:** OPEN — documented in `AUDIT.md`. Recommended action: wrap the mount in a `try/except` or check `FRONTEND.exists()` before mounting, and emit a health warning. Out of scope for this audit PR (changes startup behavior).

### F-AUD-011 — `product/orchestration/pipeline.py` writes logs with no schema validation (F-005 class of bug)
**Found:** forensic audit (`AUDIT.md`).
**Observed:** `_log()` appends to `logs/pipeline_runs.jsonl` with `json.dumps(entry)`. The entry has no `writer` field (Law 8 replayability violation), no schema validation, no integrity check. If a future code change adds a field, old entries silently lack it. If the writer ever produces malformed JSON (e.g., a non-serializable object), the log file becomes unparseable — the F-005 failure mode in miniature.
**Root cause:** the F-005 postmortem (`evidence/corruption/POSTMORTEM_F005.md`) documents the root cause as "a writer that was never committed produced a `predictions.jsonl` written one-character-per-line." `pipeline.py::_log()` is a new writer with the same shape: append-only, no schema, no writer field, no integrity check.
**Severity:** P2 — does not affect runtime, but is the seed of the next F-005-class bug.
**Status:** OPEN — documented in `AUDIT.md`. Recommended action: (1) add a `writer` field to every log entry, (2) add a schema test in `tests/test_ledger_integrity.py` that asserts every line in `logs/pipeline_runs.jsonl` parses and carries the required fields, (3) wrap `json.dumps` in a try/except that refuses to write unparseable entries.

### F-AUD-012 — `orchestrator._chain_summary()` hardcoded `verification_status="integrated"`
**Found:** forensic audit (`AUDIT.md`).
**Repro:** `pytest tests/test_audit_findings.py::test_F_AUD_012_chain_summary_derives_verification_status -v`.
**Observed:** `_chain_summary()` returned `"verification_status": "integrated"` as a string literal, regardless of what Layer 8 (the verification engine) actually concluded. The chain summary is the system's final answer to "is this candidate verified?" — hardcoding the answer is the same class of overclaim that Law 8 forbids.
**Root cause:** the line had a comment `# NEVER "verified" until Law 8 cycle` — acknowledging the rule but bypassing it by hardcoding the second-best label. The verification engine's actual output was ignored.
**Severity:** P2 — does not crash, but lies about system state. If Layer 8 ever emits a different status (e.g., "failed" after a verification cycle records a fail), the chain summary would still say "integrated".
**Status:** RESOLVED — `verification_status` is now derived from `layers[8].get("verification_status")` if Layer 8 emits one; otherwise it falls back to `"integrated"` with an explicit `verification_status_source` field noting that it's a default, not a derived value.
