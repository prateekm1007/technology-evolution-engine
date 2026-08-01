# F-005 Follow-up Audit: Epistemic Instrument Run Against Itself

**Audit ID:** F-005-followup
**Date:** 2026-08-01
**Investigator:** external audit (this conversation)
**Starting point:** `evidence/corruption/POSTMORTEM_F005.md`
**Procedure:** the 8-step procedure specified by the repository owner.
**Commit at audit time:** `c6ece5e71470c8b8cd2460d1d2cb908f9526a2fe`

---

## Required Output Format

### STATUS

**The system does not currently deserve the "verified" label it assigns itself.**
Law 8 enforcement verdict: **FAIL**. Every "verified" mention in the
codebase is unsupported by replayable evidence, because the only
mechanism for recording prediction outcomes (`data/ledger/predictions.jsonl`)
is byte-level corrupted (F-005). 12 of 14 unit tests pass; 2 fail by
design — they are the F-005 regression tests, and they fail because the
corruption is real. 7 of 7 integration tests pass; 0 of 0 "verified"
labels have replayable backing.

The epistemic instrument, when run against itself, returns the verdict
that the F-005 postmortem predicted: the system cannot honestly
distinguish a real verification from an aspirational one. The
instrument works. The system under test does not.

### EVIDENCE

Six deliverable artifacts, all generated live by `scripts/run_forensic_audit.py`
in this session. Nothing here is hand-written.

| Artifact | Path | Result |
|---|---|---|
| Compile report | `evidence/reports/compile_report.json` | 70/70 files compile clean (was 67 — 3 new audit files added) |
| Unit test report | `evidence/reports/unit_test_report.json` | 12 passed, 2 failed (the 2 F-005 regression tests, by design) |
| Integration report | `evidence/reports/integration_report.json` | 7/7 passed (was 4 — 3 endpoint honesty tests added) |
| Benchmark report | `evidence/reports/benchmark_report.json` | Harness ran live; appended 1 well-formed entry; ledger restored to corrupted state to honor audit constraint #2 |
| Verification report | `evidence/reports/verification_report.json` | Verdict: FAIL. 0 supported "verified" claims. 14 unsupported mentions. |
| Ledger integrity report | `evidence/reports/ledger_integrity_report.json` | Corruption signature: confirmed. Writer: lost. Reproduction: byte-exact. Schema: matches no current writer. |
| FAILURES.md | `FAILURES.md` | Appended F-011 through F-015. Existing entries untouched (Law 7). |

**Key forensic measurements (re-verified live this session):**

| Metric | Value |
|---|---|
| Ledger SHA256 (live) | `df65acbd6b81606e3bb68540b038955673f2ef67d408c13f277f4dd0d6629909` |
| Ledger SHA256 (preserved copy) | `df65acbd6b81606e3bb68540b038955673f2ef67d408c13f277f4dd0d6629909` |
| Ledger SHA256 (byte-exact reproduction) | `df65acbd6b81606e3bb68540b038955673f2ef67d408c13f277f4dd0d6629909` |
| Ledger SHA256 at initial commit `090d3cf` | `df65acbd6b81606e3bb68540b038955673f2ef67d408c13f277f4dd0d6629909` |
| Byte count | 1,403 |
| Line count (splitlines) | 704 |
| Non-empty line count | 609 |
| Max line length | 1 |
| Unique line lengths | `[0, 1]` |
| Salvaged records (newline-stripped) | 3 valid JSON objects |
| Salvaged schema | `{id, date, claim, confidence, falsification, status}` |
| Matches `GraphModel.append_ledger` schema? | No |
| Matches `log_to_ledger` schema? | No |

**Ledger write graph (exhaustive):**

| Writer | Schema | Triggered by | Writes to |
|---|---|---|---|
| `web/backend/adapters/graph_model.py::GraphModel.append_ledger` (line 115–121) | `{type:"oracle_prediction", constraint, delta, net_possibility_space, confidence, confidence_status, outcome:"pending", assumptions, timestamp}` | `DeepOracle.simulate()` via `POST /api/v1/simulate` | `data/ledger/predictions.jsonl` (append) |
| `scripts/run_evidence_tests.py::log_to_ledger` (line 205–217) | `{type:"benchmark_run", timestamp, total_benchmarks, overall_composite_mean, grade_distribution, assumptions, falsification_criteria}` | manual: `python scripts/run_evidence_tests.py --all` | `data/ledger/predictions.jsonl` (append) |
| **LOST** (the writer that produced the corrupted file) | `{id, date, claim, confidence, falsification, status}` | unknown — never committed | `data/ledger/predictions.jsonl` (initial commit `090d3cf`) |

The corrupted file's schema matches **neither** of the two current
writers. The writer is genuinely lost — born outside version control,
frozen into the initial commit already corrupted, and never since
reproduced by any code in the repo.

### FAILURES

**Reproduced this session:**
- F-005 (byte-level ledger corruption) — re-verified by SHA256 match
  between the live file, the preserved copy, and the byte-exact
  reproduction. All three are identical.
- F-006 (the `/api/v1/evidence` 500 on the corrupted ledger) — confirmed
  resolved; `test_evidence_does_not_500` and
  `test_evidence_detects_total_corruption` both pass.
- F-014 (the new regression tests) — confirmed to fail on the
  corrupted state, by design. This IS the F-005 failure observed
  through the test lens.

**Newly discovered this session (F-011 through F-015):**
- **F-011** — `scripts/verify_stack.py:15` stamps `"oracle": "verified"`
  whenever the static graph file loads. That is presence-of-data, not
  verification. No prediction/observation/reconciliation cycle backs
  this label. Severity P1.
- **F-012** — `INTERFACES.md:44` documents `"verified" | "implemented"`
  as the response contract, but no endpoint honestly produces
  `"verified"`. The contract advertises a label the system cannot
  honestly produce. Severity P2.
- **F-013** — `web/backend/adapters/core.py:28-30` reads the ledger
  with the same naive `json.loads(l) for l in ...` pattern that
  F-006 fixed in `main.py`. The fix landed in only one of the two
  readers. Severity P1.
- **F-014** — F-005 regression tests confirmed failing on the
  corrupted state (informational — the tests are doing their job).
- **F-015** — `scripts/calibrate.py:8` has the same naive reader
  pattern as F-013. Severity P2.

**Reproduction evidence preserved:**
- The corrupted file is untouched: SHA256 matches its state at the
  initial commit `090d3cf`.
- The byte-exact reproduction at
  `evidence/corruption/reproduction_byte_exact.jsonl` still matches
  the live file by SHA256.
- The benchmark harness was run live; it appended 1 entry to the
  ledger. That append was captured in
  `evidence/reports/benchmark_report.json`, and the ledger was then
  restored to its corrupted state to honor audit constraint #2
  ("Do not overwrite the corrupted ledger"). The restoration was
  verified by SHA256: ledger SHA before run = ledger SHA after restore.

### ROOT CAUSES

**Technical root cause of F-005** (from the postmortem, re-verified
this session by reproduction): character-by-character iteration over
a JSON-serialized string, with a newline written after each character.
The original writer treated `json.dumps(entry)` — a `str` — as if it
were an iterable of records. In Python, strings ARE iterable, and
iterating yields one character at a time.

**Process root cause of F-005**: the writer script was never committed
to version control. The corruption was born outside version control
and imported into the repo as fact in the initial commit.

**Root cause of the unsupported "verified" labels (F-011, F-012)**:
Law 8 was added to CONSTITUTION.md and the rule was enforced by
hand-analysis (the existing `verification_report.json`), but no
automated enforcement existed. Without automated enforcement, the
rule erodes: developers add "verified" stamps for any condition that
*feels* like verification ("the graph loaded!", "the pipeline
returned!") without checking whether the formal criteria (successful
prediction + failed prediction + replayable evidence) are met.

**Root cause of the duplicated reader bug (F-013, F-015)**: the
ledger is read in three places (`main.py`, `core.py`, `calibrate.py`)
and the total-corruption-aware read logic was implemented in only
one of them. There is no shared `read_ledger()` utility; each reader
re-implements the read inline. This is parallel development with no
reconciliation.

**Root cause of the schema mismatch (writer lost)**: there is no
schema-stamping requirement on ledger entries. Neither current writer
includes a `schema_version` or `writer` field in its entries. Without
those, drift between writers and the ledger is structurally
undetectable — which is exactly how the corrupted file's third schema
went unnoticed for the entire committed history.

### OPEN QUESTIONS

1. **What evidence supports every remaining "verified" label?**
   **Answer: NONE.** The Law 8 enforcement script
   (`scripts/enforce_law8.py`, this audit) found 0 supported
   "verified" claims. The verdict is FAIL because the ledger is
   not parseable, contains 0 successful predictions, contains
   0 failed predictions, and contains 0 entries with a `writer`
   field (so even if it parsed, none of the entries would be
   replayable). Every "verified" label in the system is
   aspirational, not evidenced.

2. **Which claims are true?**
   The following claims in the repo are TRUE:
   - The codebase compiles (70/70 files).
   - The unit tests pass for everything except the new F-005
     regression tests (12/14 passing; the 2 failures are
     catching real bugs).
   - The integration tests pass (7/7).
   - The `/api/v1/analyze` endpoint does not stamp "verified"
     (it stamps "integrated" — the F-001 follow-up fix in
     `01db12f` is intact).
   - The `/api/v1/evidence` endpoint does not 500 on the
     corrupted ledger (the F-006 fix in `01db12f` is intact).
   - The corruption predates version control (verified by
     comparing the live SHA256 against the SHA256 at the initial
     commit `090d3cf`).
   - The corruption is reproducible byte-exactly (the reproduction
     at `evidence/corruption/reproduction_byte_exact.jsonl` matches
     the live file by SHA256).

3. **Which claims are unsupported?**
   The following claims are UNSUPPORTED by replayable evidence:
   - `scripts/verify_stack.py:15` — claims `oracle: "verified"`.
     Unsupported: no prediction/observation/reconciliation cycle
     exists for Oracle output.
   - `INTERFACES.md:44` — claims `"verified"` is a possible
     `level` value in the response contract. Unsupported: no
     endpoint honestly produces it.
   - The implicit claim, made by every commit since `090d3cf`,
     that the ledger is a usable record of predictions.
     Unsupported: the file is byte-level corrupted.

4. **Which claims must be downgraded?**
   - `scripts/verify_stack.py:15` "oracle: verified" → "integrated"
     (or "implemented", depending on whether `gm.source == "core"`).
     The condition correctly detects graph loading, but graph loading
     is not verification.
   - `INTERFACES.md:44` `"level": "verified" | "implemented"` →
     `"level": "integrated" | "implemented"`, with a note that
     "verified" is reserved for when Law 8 criteria are met
     (currently: never).

5. **Which failures were reproduced?**
   - F-005 (ledger byte corruption) — reproduced by SHA256 match
     between live, preserved, and reproduction copies.
   - F-006 silently-deegrading `/api/v1/evidence` on corrupted
     ledger — confirmed RESOLVED (the total-corruption heuristic
     fires correctly; `entry_count: 0` is returned).
   - The class of "verified-without-evidence" failure — reproduced
     by the new F-011 finding (verify_stack.py still stamps it).
   - The new regression tests caught F-005 at the unit-test layer
     (F-014 documents this).

6. **Which failures remain unexplained?**
   - The exact identity of the LOST WRITER that produced the
     corrupted file. The postmortem narrowed the reproduction to
     a 5-line Python snippet and proved it produces byte-exact
     output. But the actual script/notebook/REPL that ran that
     snippet is gone — never committed, deleted before the
     initial commit. We have the pattern; we do not have the
     artifact.
   - Why the corrupted file's 3 salvaged records use a schema
     (`{id, date, claim, confidence, falsification, status}`) that
     matches no current writer. This is consistent with "the writer
     was lost", but it also raises the possibility that the writer
     was deliberately removed and the data was meant to be
     regenerated — and never was. We cannot distinguish those
     two histories from the available evidence.

### NEXT ACTIONS

Ordered by dependency, not by severity.

1. **Regenerate `data/ledger/predictions.jsonl` from a known writer.**
   Run `python scripts/run_evidence_tests.py --all`. This will
   append a `benchmark_run` entry to the corrupted file. The
   corrupted bytes will still be at the head of the file — the
   file is append-only and cannot be cleanly regenerated without
   deleting it. The decision to delete is the user's, not the
   audit's, per audit constraint #2 ("Do not overwrite the
   corrupted ledger"). When the user is ready: back up the
   corrupted file (already done at
   `evidence/corruption/predictions_corrupted.jsonl`), delete the
   live file, re-run the harness, and the F-005 regression tests
   will flip green.

2. **Stamp every ledger entry with a `writer` field.**
   Both current writers (`GraphModel.append_ledger` and
   `log_to_ledger`) should add `"writer": "module::function"` to
   every entry. Without this, replayability is unverifiable and
   the Law 8 enforcement script's `replayable_entries` count
   stays at 0.

3. **Implement at least one predict → observe → reconcile cycle.**
   Pick one prediction (e.g., the Oracle's `net_possibility_space`
   output for a known constraint move). Wait for an outcome
   (could be a simulated outcome for a deterministic test, but
   must be recorded as `outcome: "pass"` or `outcome: "fail"`).
   Record at least one pass and at least one fail. This is the
   single step that, once done, flips the Law 8 verdict from
   FAIL to PASS.

4. **Downgrade `scripts/verify_stack.py:15` from "verified" to "integrated".**
   One-line change. The `gm.source == "core"` condition correctly
   detects graph loading; it does not verify anything. Stop
   calling it "verified".

5. **Update `INTERFACES.md:44`** to either drop "verified" from
   the allowed-values list or annotate it as "not currently
   achievable under Law 8".

6. **Consolidate the three ledger readers** (`main.py::evidence`,
   `core.py`, `calibrate.py`) into a single shared utility with
   the total-corruption-aware read logic from `main.py`. This
   closes F-013 and F-015 in one move.

7. **Add a pre-commit hook** that rejects any `.jsonl` file
   whose `line_count > 500 AND max_line_length < 5`. This is the
   generic catch for the F-005 corruption pattern, independent
   of any specific writer.

8. **Wire `scripts/enforce_law8.py` into CI.** Run it on every
   PR. Fail the build if verdict is FAIL. The script is already
   idempotent and side-effect-free.

---

## Provenance of this audit

- **Investigator:** external audit (Claude / Super Z, in conversation with Prateek)
- **Procedure followed:** the 8-step procedure specified by the user
  (preserve → search → graph → reproduce → classify → postmortem →
  regress → enforce → re-run → answer).
- **Scripts written:**
  - `/home/z/my-project/scripts/run_forensic_audit.py` (master harness)
  - `scripts/run_forensic_audit.py` (copy in repo)
  - `scripts/enforce_law8.py` (Law 8 automated enforcement)
  - `tests/test_ledger_integrity.py` (F-005 regression tests)
- **Evidence preserved:** the corrupted ledger at
  `data/ledger/predictions.jsonl` is byte-identical to its state at
  the initial commit `090d3cf` (verified by SHA256 before and after
  the audit). The benchmark harness's append was reversed; the
  restoration was verified by SHA256.
- **Code modified:** `tests/test_ledger_integrity.py` (new),
  `scripts/enforce_law8.py` (new), `scripts/run_forensic_audit.py`
  (new), `FAILURES.md` (appended F-011 through F-015; existing
  entries untouched), `evidence/reports/*.json` (regenerated by
  the harness, not hand-edited), `evidence/corruption/AUDIT_F005_FOLLOWUP.md`
  (this file, new).
- **Code NOT modified:** the corrupted ledger, the existing engine/
  and product/ code, the existing tests, the CONSTITUTION.md, the
  GOVERNANCE.md. No feature additions. No architectural changes.
