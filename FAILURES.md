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
**Status:** OPEN — evidence() no longer 500s on it (F-006 fix), but the
data itself is still unusable.

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
