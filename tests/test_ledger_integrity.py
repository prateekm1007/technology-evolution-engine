"""
Ledger integrity regression tests.

These tests exist to catch the exact failure mode documented in
F-005 (see evidence/corruption/POSTMORTEM_F005.md): a writer script
that was never committed produced a `predictions.jsonl` written
one-character-per-line. Every test in this suite passed while the
ledger was corrupted, because no test ever read the ledger back.

These three tests would have failed on the initial commit `090d3cf`
and on every commit since. They are added BEFORE the corrupted file
is touched, so the failure can be observed live, then the fix can be
verified to flip them green.

Law 7 (historical permanence): the corrupted artifact at
data/ledger/predictions.jsonl is preserved exactly. These tests
assert against the current state of the repo, whatever that state
is. They do NOT mutate the ledger.
"""
import json
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
LEDGER_PATH = DATA_DIR / "ledger" / "predictions.jsonl"


def _all_jsonl_files():
    """Every .jsonl file committed anywhere under data/."""
    if not DATA_DIR.exists():
        return []
    return sorted(DATA_DIR.rglob("*.jsonl"))


def test_every_committed_jsonl_line_parses():
    """F-005 regression #1.

    Every non-empty line in every committed .jsonl file under data/
    must parse as a single JSON value. A file written one-character-
    per-line fails this trivially: each "line" is a single character
    like `{` or `"` or `,`, none of which is a valid JSON document.

    On the corrupted state, data/ledger/predictions.jsonl has 703
    lines and not one of them parses as JSON. On a regenerated
    state, every line should parse.
    """
    files = _all_jsonl_files()
    assert files, "expected at least one .jsonl file under data/"
    failures = []
    for f in files:
        with open(f, "r", encoding="utf-8") as fh:
            for i, line in enumerate(fh, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    json.loads(stripped)
                except json.JSONDecodeError as e:
                    failures.append({
                        "file": str(f.relative_to(ROOT)),
                        "line": i,
                        "error": str(e),
                        "preview": stripped[:80],
                    })
    assert not failures, (
        "F-005 regression: .jsonl files under data/ contain lines that do not "
        "parse as JSON. This is the exact failure mode of the corrupted ledger. "
        f"First 5 failures: {failures[:5]}"
    )


def test_no_one_char_per_line_pattern():
    """F-005 regression #2.

    Heuristic for the exact corruption signature: a file with
    `line_count > 500` AND `max_line_length < 5` is almost certainly
    a writer that iterated a string character-by-character and
    wrote a newline after each character. The legitimate
    one-line-per-record JSONL format cannot hit this signature:
    any non-trivial JSON object is longer than 5 characters.

    On the corrupted state, predictions.jsonl hits this with
    line_count=703 and max_line_length=1.
    """
    files = _all_jsonl_files()
    flagged = []
    for f in files:
        with open(f, "r", encoding="utf-8") as fh:
            lines = fh.read().splitlines()
        non_empty = [ln for ln in lines if ln.strip()]
        if len(non_empty) > 500 and all(len(ln) < 5 for ln in non_empty):
            flagged.append({
                "file": str(f.relative_to(ROOT)),
                "line_count": len(lines),
                "non_empty_count": len(non_empty),
                "max_line_length": max((len(ln) for ln in non_empty), default=0),
            })
    assert not flagged, (
        "F-005 regression: one-character-per-line corruption signature "
        f"detected in: {flagged}"
    )


def test_ledger_schema_matches_writer():
    """F-005 regression #3.

    Every entry in data/ledger/predictions.jsonl, if it parses, must
    have a schema that matches one of the two writers that currently
    produce the file:

      - GraphModel.append_ledger() in web/backend/adapters/graph_model.py
        schema: {type:"oracle_prediction", constraint, delta, ...,
                 timestamp, outcome}
      - log_to_ledger() in scripts/run_evidence_tests.py
        schema: {type:"benchmark_run", timestamp, total_benchmarks, ...}

    The corrupted file's records use a THIRD schema
    ({id, date, claim, confidence, falsification, status}) that
    matches no current writer — proving the writer was lost.

    This test asserts that no entry in the ledger uses a schema
    that doesn't match a known writer. On the corrupted state,
    the file doesn't parse (regression #1 catches that); but
    even after a hypothetical byte-fix that makes the lines
    parse, the schema check would still flag the records as
    unprovenanced.

    Test is skipped if the ledger doesn't currently parse (so
    that regression #1 is the single loud failure on the corrupted
    state, not three overlapping failures).
    """
    if not LEDGER_PATH.exists():
        return  # nothing to test

    # Try to parse the current ledger. If it doesn't parse at all,
    # regression #1 already fires loud and clear.
    parsed = []
    for line in LEDGER_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            parsed.append(json.loads(line))
        except json.JSONDecodeError:
            return  # leave the loud failure to regression #1

    # Once we get here, the file parses line-by-line. Now check
    # that every parsed entry matches one of the known writers.
    known_writers = {
        "oracle_prediction": {
            "required": {"type", "constraint", "delta", "timestamp", "outcome",
                         "writer"},
            "writer": "web/backend/adapters/graph_model.py::GraphModel.append_ledger "
                      "(called by web/backend/adapters/oracle_deep.py::_log_to_ledger)",
        },
        "benchmark_run": {
            "required": {"type", "timestamp", "total_benchmarks",
                         "overall_composite_mean", "grade_distribution", "writer"},
            "writer": "scripts/run_evidence_tests.py::log_to_ledger",
        },
        "verification": {
            "required": {"type", "timestamp", "prediction_id", "outcome",
                         "writer"},
            "writer": "scripts/run_verification_cycle.py::reconcile OR phase1.close_the_loop",
        },
    }
    unprovenanced = []
    for i, entry in enumerate(parsed, start=1):
        etype = entry.get("type", "<missing type>")
        if etype not in known_writers:
            unprovenanced.append({
                "line": i,
                "type": etype,
                "keys": sorted(entry.keys()),
                "reason": f"no known writer produces type={etype!r}",
            })
            continue
        required = known_writers[etype]["required"]
        missing = required - set(entry.keys())
        if missing:
            unprovenanced.append({
                "line": i,
                "type": etype,
                "missing_required_keys": sorted(missing),
                "writer": known_writers[etype]["writer"],
            })
    assert not unprovenanced, (
        "F-005 regression: ledger entries exist whose schema matches no current "
        "writer. This is the 'unprovenanced data' failure mode — entries that "
        "were produced by a writer that has since been deleted. "
        f"Unprovenanced entries: {unprovenanced[:5]}"
    )
