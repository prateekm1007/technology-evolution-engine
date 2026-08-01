# F-005 Postmortem: predictions.jsonl Corruption

**Incident ID:** F-005
**Status:** Root cause identified. Fix NOT applied (this is archaeology, not engineering — the fix is a separate, subsequent step).
**Date of postmortem:** 2026-08-01
**Investigator:** external audit (this conversation)
**Artifact preserved at:** `evidence/corruption/predictions_corrupted.jsonl`
**Artifact SHA256:** `df65acbd6b81606e3bb68540b038955673f2ef67d408c13f277f4dd0d6629909`

---

## Symptoms

The file `data/ledger/predictions.jsonl` is 1,403 bytes long and contains 704 lines. Every non-empty line is exactly one character long. The file does not parse as JSONL. The `/api/v1/evidence` endpoint, prior to the F-002 fix, returned 74 spurious "valid" entries from this file because single digits and single-character JSON literals (`0`, `1`, `2`... `[`, `]`, `{`, `}`) parse as valid JSON when read line-by-line.

### Forensic measurements (preserved in `metadata.json`)

| Metric | Value |
|---|---|
| Byte count | 1,403 |
| Char count (UTF-8) | 1,403 |
| Line count | 704 |
| Non-empty line count | 609 |
| Empty line count | 4 |
| Max line length | 1 |
| Min line length | 0 |
| Unique line lengths | `[0, 1]` |
| SHA256 | `df65acbd6b81606e3bb68540b038955673f2ef67d408c13f277f4dd0d6629909` |

### Internal structure of the corrupted file

| Region | Lines | Content |
|---|---|---|
| Record 1 | 0–205 | 206 chars of valid JSON (pred_001), one char per line |
| Empty lines | 206–207 | 2 empty lines |
| Record 2 | 208–458 | 251 chars of valid JSON (pred_002), one char per line |
| Empty lines | 459–460 | 2 empty lines |
| Record 3 | 461–703 | 243 chars of valid JSON (pred_003), one char per line, no trailing newline |

When newlines are stripped, the salvage is **3 valid JSON objects concatenated with no separator**:

```
{"id":"pred_001",...}{"id":"pred_002",...}{"id":"pred_003",...}
```

Each individual record is valid JSON. The corruption is in the *serialization-to-filesystem* step, not in the data itself.

---

## Impact

1. **The verification layer cannot function.** Law 8 requires "verified" labels to be backed by failure logging. The only mechanism for recording prediction outcomes is this ledger. With the ledger unreadable, no "verified" stamp in the system can be honestly claimed.

2. **The `/api/v1/evidence` endpoint silently lied.** Before the F-002 fix, it returned 74 spurious "valid" entries parsed from single-character lines. This is worse than a 500 error — it gave consumers the impression that evidence existed when it did not.

3. **The schema in the corrupted file does not match any writer currently in the repo.** The corrupted records use keys `{id, date, claim, confidence, falsification, status}`. The two current writers (`scripts/run_evidence_tests.py:log_to_ledger` and `web/backend/adapters/graph_model.py:GraphModel.append_ledger`) write completely different schemas (`{type, timestamp, total_benchmarks, ...}` and caller-supplied dicts respectively). This means **the corrupted file was not produced by any code currently in the repository.**

4. **The corruption was frozen into the initial commit.** `git log --all --oneline -- data/ledger/predictions.jsonl` shows the file was created in commit `090d3cf` (the initial commit) and has never been modified since. The SHA256 of the file at `090d3cf` matches the current SHA256 exactly. The corruption predates version control.

---

## Root cause

### Technical root cause

Character-by-character iteration over a JSON-serialized string, with a newline written after each character. The reproduction pattern is:

```python
buf = []
for i, entry in enumerate(predictions):
    if i > 0:
        buf.append("\n\n")                # 2 empty lines between records
    for ch in json.dumps(entry):          # iterates a STRING char-by-char
        buf.append(ch + "\n")             # newline after EVERY character
text = "".join(buf)[:-1]                  # drop the trailing newline
```

The original writer treated `json.dumps(entry)` — which returns a `str` — as if it were an iterable of records. In Python, strings ARE iterable, and iterating them yields one character at a time. Each character thus became a "record" and got its own newline. The writer did know that records needed separation (the `"\n\n"` between records is present), but did not realize their inner `for ch in ...` loop was already destroying the record structure.

### Process root cause

**The writer script was never committed to version control.** The corrupted file was committed in the initial commit (`090d3cf`) already corrupted. The script that produced it was either:

- A local dev script that was deleted before the initial commit
- A notebook cell that was never saved to a `.py` file
- A REPL session whose commands were never recorded

Either way, the corruption was **born outside version control** and **imported into the repo as fact**. The initial commit's role was to freeze the corruption, not to create it. We cannot recover the exact original writer — it is genuinely lost.

---

## Contributing factors

1. **No pre-commit hook validates JSONL files for structural sanity.** A 5-line pre-commit hook that ran `python -c "import json,sys; [json.loads(l) for l in open(sys.argv[1]) if l.strip()]"` on every `.jsonl` file would have rejected this file at commit time.

2. **No CI test ever read the ledger back.** If any test had done `for line in open('data/ledger/predictions.jsonl'): json.loads(line)`, the 703-malformed-lines result would have failed loudly on the very first test run. The existing test suite (`tests/test_endpoints.py`) only tests that `/api/v1/evidence` does not 500 — it does not assert that the returned entries are non-spurious.

3. **The schema mismatch was not flagged.** The corrupted file uses `{id, date, claim, confidence, falsification, status}`. The two current writers use completely different schemas. No test asserts the ledger's schema, so the mismatch went unnoticed.

4. **The initial commit bundled 46 files including data, with no review gate.** The commit message "Initial commit: TEE v0.1 - full architecture, ontology, engine, candidates, data" treats data files as a monolithic block. Nothing asked "is this data actually readable?"

5. **The `/api/v1/evidence` endpoint's failure mode was silent degradation, not loud failure.** Before the F-002 fix, it returned 74 spurious "valid" entries instead of erroring. Silent degradation is more dangerous than a 500 because consumers don't know to investigate.

---

## Detection method

**External audit.** The corruption was discovered by an external review of the repo (this conversation), not by the system itself. Specifically:

1. The user (Prateek) noted in the handoff document that the ledger was corrupted.
2. The investigator (this assistant) ran `wc -l data/ledger/predictions.jsonl` and observed 703 lines in a 1403-byte file — a statistically impossible line-to-byte ratio that immediately signaled one-char-per-line corruption.
3. The investigator then hit `/api/v1/evidence` and observed 74 spurious "valid" entries, confirming the silent-degradation failure mode.

**The system itself had no way to discover this.** The capability matrix the user laid out is accurate:

| Capability | Present? |
|---|---|
| Logging | Yes |
| Reporting | Yes |
| External auditing | Yes |
| Failure taxonomy | Yes |
| Self-auditing | No |
| Continuous verification | No |
| Autonomous rollback | No |

This incident is concrete evidence that "self-auditing: No" is not a hypothetical gap — it is a present, active failure mode. The system would still be silently degrading if not for the external audit.

---

## Reproduction evidence

The reproduction is preserved at `evidence/corruption/reproduction_byte_exact.jsonl`. Its SHA256 matches the corrupted artifact's SHA256 exactly:

```
reproduction: df65acbd6b81606e3bb68540b038955673f2ef67d408c13f277f4dd0d6629909
artifact:     df65acbd6b81606e3bb68540b038955673f2ef67d408c13f277f4dd0d6629909
```

The reproduction script is at `/home/z/my-project/scripts/f005_repro.py` and `/home/z/my-project/scripts/f005_repro_refined.py` and `/home/z/my-project/scripts/f005_repro_final.py` (the iterative narrowing of hypotheses). The final byte-exact reproduction is the snippet in the "Technical root cause" section above.

The input data for the reproduction was reconstructed from the salvage (the 3 prediction records are fully readable once newlines are stripped). The exact bytes were recovered.

---

## Corrective action (NOT YET APPLIED — for the next step)

The corrective action is NOT part of this postmortem. This postmortem is archaeology. The fix is engineering, and engineering is a separate step that comes after the postmortem is accepted.

When the fix is applied, it should:

1. **Delete the corrupted file.** It cannot be salvaged as a ledger — the records are valid but the schema doesn't match any current writer, and there is no provenance for where these 3 predictions came from. Keeping it would be importing unprovenanced claims into the verification layer.

2. **Regenerate the ledger from scratch** using `scripts/run_evidence_tests.py` (the only writer with a defined schema). The first run will produce 1 entry with the benchmark-summary schema. That is the honest starting state: 1 entry, not 3 unprovenanced predictions.

3. **Find and fix the writer** — but since the writer is lost, the practical action is to **add a pre-commit hook** that rejects any `.jsonl` file where `max(len(line) for line in lines) < 5 and len(lines) > 100`. This catches the one-char-per-line corruption pattern generically, without depending on finding the original writer.

4. **Add a regression test** that reads every committed `.jsonl` file in `data/` and asserts every non-empty line parses as JSON. This test would have failed on the initial commit and on every commit since.

---

## Preventive action (NOT YET APPLIED — for the next step)

1. **Pre-commit hook** for `.jsonl` files: parse every non-empty line as JSON; reject the commit if any line fails.
2. **CI test** that reads every committed ledger file and asserts the schema matches the writer that produced it.
3. **Schema stamping**: every ledger entry should include a `schema_version` field so future drift is detectable.
4. **Provenance stamping**: every ledger entry should include a `writer` field naming the script/module that produced it, so unprovenanced data is impossible to commit silently.
5. **Add the "self-auditing" capability** the user identified as missing. Concretely: a scheduled job that reads every ledger file, validates structure, and raises an alert (not just logs) on corruption. Until this exists, the system will continue to depend on external audits to catch this class of failure.

---

## Regression tests (NOT YET APPLIED — for the next step)

1. `tests/test_ledger_integrity.py::test_every_committed_jsonl_line_parses` — iterate every `.jsonl` file under `data/`, assert every non-empty line is valid JSON.
2. `tests/test_ledger_integrity.py::test_ledger_schema_matches_writer` — assert that every entry in `data/ledger/predictions.jsonl` has the keys that `log_to_ledger()` writes.
3. `tests/test_ledger_integrity.py::test_no_one_char_per_line_pattern` — assert that no `.jsonl` file in `data/` has the structural signature of this corruption (line_count > 500 AND max_line_length < 5).

These tests should be added BEFORE the corrupted file is deleted, so the regression test can be verified to fail on the corrupted state and pass on the regenerated state.

---

## What this incident proves about the system

This incident is the cleanest possible demonstration of the gap between "the code exists and runs" and "the system is verified." Every commit since `090d3cf` has included a corrupted ledger. Every test suite has passed. Every endpoint has returned 200. The system has been silently degrading for its entire committed history, and only an external audit caught it.

The user's framing is exactly right:

> "The system discovered the error" would be inaccurate. "An external audit discovered the error" is accurate. Those are radically different maturity levels.

This postmortem is the artifact that preserves that distinction. When the fix is applied, it must come with the self-auditing capability that would have caught this corruption without external help. Anything less is treating the symptom, not the disease.

---

## Provenance of this postmortem

- **Investigator:** external audit (Claude / Super Z, in conversation with Prateek)
- **Procedure followed:** the 6-step forensic procedure specified by the user (preserve → search → graph → reproduce → classify → postmortem)
- **Scripts written:** `/home/z/my-project/scripts/f005_preserve.py`, `f005_repro.py`, `f005_repro_refined.py`, `f005_repro_final.py`
- **Evidence preserved:** `evidence/corruption/predictions_corrupted.jsonl` (byte-identical copy), `evidence/corruption/sha256.txt`, `evidence/corruption/metadata.json`, `evidence/corruption/reproduction_byte_exact.jsonl` (byte-identical reproduction)
- **Code modified:** NONE. This is archaeology. The fix is a separate step.
