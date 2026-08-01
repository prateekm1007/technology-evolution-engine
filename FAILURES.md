# FAILURES

Every entry here was reproduced live, not inferred from reading code. Status
is current as of commit `01db12f`. New entries append; existing entries are
never edited except to change `status` and add a `resolved_in` commit —
per CONSTITUTION.md Law 7, historical permanence.

**ID assignment rule (per external auditor F-018 finding):** ID assignment
MUST check the existing file for the next free number before writing, not
assume. The F-016/F-017/F-018 renumbering was required because two work
streams numbered independently and collided on F-011/F-012/F-013. This
is a process fix, not an architectural one — it directly prevents
recurrence of the same Law 7 violation.

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
**Status:** OPEN — `core.py` should reuse the same total-corruption-aware
read logic that `main.py::evidence()` uses, or the two readers should be
consolidated.

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
**Status:** OPEN — these tests will flip green when (and only when) the
corrupted ledger is regenerated from a known writer (per the corrective
action in `evidence/corruption/POSTMORTEM_F005.md`). Until then, they
remain red on every commit — which is correct: the system has a known
unfixed bug, and the test suite should say so loudly.

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
**Status:** OPEN.

---

### F-016 — Systemic character-per-line corruption in historian/*.json and mode4_constraint_leverage.json
**Found:** external audit (mission-alignment review).
**Repro:** `json.load(open('data/historian/0001_APRM_historian.json'))` → JSONDecodeError. `wc -l` shows 656 lines in a 1273-byte file; `max_line_length=1`. Same corruption signature as F-005.
**Observed:** All 4 files exhibit the identical character-per-line pattern:
  - `data/historian/0001_APRM_historian.json` (656 lines, 1273 bytes, max_line_len=1)
  - `data/historian/0002_DAM_historian.json` (705 lines, 1371 bytes, max_line_len=1)
  - `data/historian/0003_ACWPS_historian.json` (671 lines, 1303 bytes, max_line_len=1)
  - `data/ledger/mode4_constraint_leverage.json` (713 lines, 1369 bytes, max_line_len=1)
**Root cause:** Same lost writer as F-005. The corruption was born outside version control, frozen into the initial commit `090d3cf`, and never noticed because no test ever read these files back. `engine/historian.py` is a 17-line stub that returns empty dicts — it does not write these files. No current code in the repository writes any of these 4 files.
**Severity:** P0 — the Historian layer is supposed to be the system's evidentiary memory (Law 6/7). All of it was unreadable. This undermines prediction→observation→reconciliation, historical permanence, reproducibility, and auditability simultaneously.
**Status:** RESOLVED — all 4 files salvaged by stripping newlines and re-serializing as clean JSON. 10 regression tests added at `tests/test_f011_regression.py` to prevent recurrence. The fix follows the same pattern as the F-005 remediation: preserve the corrupted bytes in git history (they're at commit `090d3cf`), repair the live files, add tests that read them back.

### F-017 — External auditor mission-alignment scorecard (informational)
**Found:** external audit (mission-alignment review).
**Observed:** The auditor assessed the system against its own mission statement and scored most dimensions 0-2 out of 10. Key findings:
  - Data breadth: 1/10 (graph is hand-seeded taxonomy, not built from patents/literature/regulation)
  - Constraint surface (Law 2): 0/10 (0 of 577 nodes have non-empty constraints)
  - Convergence detection: 0/10 (no code computes this)
  - Feasible vs. premature: 2/10 (scoring is static formula, not real signal)
  - Resurrection: 1/10 (cemetery is mostly empty, engine is 18-line stub)
  - Prediction→verification loop: 0/10 (zero completed cycles — ledger was corrupted)
  - Software correctness: 6/10 (the code that exists compiles and passes tests)
**Root cause:** the mission statement describes capabilities the system does not yet have. Named components exist as stubs that match the mission's vocabulary without the substance the words imply.
**Severity:** informational — this is not a bug, it's a gap between mission and reality. The scorecard is recorded for calibration.
**Status:** OPEN — recorded for future planning. No code change needed; the finding is about capability gaps, not data corruption.

---

### F-018 — External auditor's updated scorecard + 5-phase roadmap (verified independently)
**Found:** external audit (post-F-011 verification).
**Verified independently:** all three key claims checked against the live repo:
  - 0/577 graph nodes have non-empty constraints: **CONFIRMED** (Law 2 unimplemented on the actual graph)
  - Convergence detection doesn't exist: **CONFIRMED** (all "converge" mentions are docstrings saying "does not yet do that")
  - invention_compiler is a parallel vertical slice: **CONFIRMED** (reads graph, never writes back; constraints computed for test problem not propagated)

**Updated scorecard:**

| Dimension | Last | Now | Why |
|---|---|---|---|
| Software correctness | 6 | 7 | 236 tests, real regression coverage for F-005/F-011 class |
| Historical permanence (Law 7) | 1 | 4 | Both F-005 and F-011 fixed with regression tests |
| Prediction→verification loop (Law 8) | 0 | 1 | Ledger readable now, but zero completed cycles |
| Data breadth | 1 | 1 | Unchanged — no real patent/literature ingestion |
| Constraint surface (Law 2) | 0 | 0 | Unchanged on the artifact that matters — the seed graph |
| Convergence detection | 0 | 0 | Unchanged, now self-documented as not-yet-done |
| Feasible vs. premature | 2 | 2 | Scoring still templated/non-discriminative |
| Multi-audience surface | 1 | 1 | Unchanged |
| Continuously evolving map | 1 | 1 | Unchanged — still one seed batch |
| Track record | 1 | 1 | Unchanged — 3 candidates, 0 approved |

**The separation problem:** two parallel systems exist:
  - System A: graph, historian, ledger, agents (the original architecture)
  - System B: invention_compiler, benchmarks, loops, hypotheses (the new vertical slice)
  Knowledge accumulates in System B without propagating back to System A.

**CTO's 5-phase roadmap (canonical forward plan):**

Phase 1 — Close the loop: complete one prediction → observe one outcome → reconcile → record permanently.
Phase 2 — Unify representations: constraints computed by invention_compiler must propagate back to the graph, historian, ledger.
Phase 3 — Ingest external evidence: patents, literature, regulations, economics, manufacturing.
Phase 4 — Define convergence mathematically: only after the definition exists should implementation begin.
Phase 5 — Audience specialization: researchers, corporations, investors, governments.

**Severity:** informational — this is a roadmap, not a bug. But the separation problem and the empty constraint surface are the two most important architectural findings in the entire audit history.

**Status:** OPEN — recorded as the canonical forward plan. The Maestro Loop will execute these phases one at a time.
