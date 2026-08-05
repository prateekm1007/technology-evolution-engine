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
    #
    # DR-31 (EPISTEMIC_ENGINE.md): register all entry types, including
    # the new Claim/Reaudit/Benchmark/ExclusionEvent types AND the
    # existing debt (blind_test_*, mechanism_verification, etc. that
    # were unregistered since cycle 55).
    known_writers = {
        # --- Original 3 types ---
        "oracle_prediction": {
            "required": {"type", "timestamp"},
            "writer": "web/backend/adapters/graph_model.py::GraphModel.append_ledger",
        },
        "benchmark_run": {
            "required": {"type", "timestamp", "total_benchmarks",
                         "overall_composite_mean", "grade_distribution", "writer"},
            "writer": "scripts/run_evidence_tests.py::log_to_ledger",
        },
        "verification": {
            "required": {"type", "timestamp", "prediction_id", "outcome",
                         "writer"},
            "requires_evidence": True,
            "writer": "scripts/run_verification_cycle.py::reconcile",
        },
        # --- DR-31: existing debt (unregistered since cycle 55+) ---
        "baseline_measurement": {
            "required": {"type", "timestamp", "writer"},
            "writer": "scripts/measure_baseline.py",
        },
        "mechanism_verification": {
            "required": {"type", "timestamp", "writer"},
            "writer": "scripts/verify_mechanisms.py",
        },
        "blind_test_hypothesis": {
            "required": {"type", "timestamp"},
            "writer": "scripts.blind_test_runner / manual",
        },
        "blind_test_hypothesis_v2": {
            "required": {"type", "timestamp", "writer"},
            "writer": "scripts.blind_discovery_test_v2",
        },
        "blind_test_result": {
            "required": {"type", "timestamp", "outcome"},
            "writer": "scripts.blind_test_runner / cycle scripts",
        },
        "blind_test_verification": {
            "required": {"type", "timestamp", "outcome"},
            "writer": "scripts.blind_test_runner / cycle scripts",
        },
        "blind_test_reclassification": {
            "required": {"type", "timestamp", "experiment_id"},
            "writer": "scripts.fix_cycle83_discovery01_misclassification / manual",
        },
        "nontriviality_check": {
            "required": {"type", "timestamp", "experiment_id", "overall_verdict"},
            "writer": "scripts.nontriviality_check",
        },
        "external_investigation": {
            "required": {"type", "timestamp", "experiment_id", "overall_verdict"},
            "writer": "scripts.external_investigation",
        },
        "f065_fullpdf_reinvestigation": {
            "required": {"type", "timestamp", "experiment_id"},
            "writer": "scripts.reinvestigate_exp_blind_*_fullpdf",
        },
        "f065_verification_verdict": {
            "required": {"type", "timestamp", "experiment_id", "f065_status"},
            "writer": "scripts.run_external_investigation_cycle85",
        },
        "f065_verification_note": {
            "required": {"type", "timestamp", "experiment_id", "verdict"},
            "writer": "manual / cycle scripts",
        },
        "f065_reinvestigation": {
            "required": {"type", "timestamp", "experiment_id", "a_side_overall_verdict"},
            "writer": "scripts.reinvestigate_exp_blind_003_arxiv",
        },
        "f063_reverification": {
            "required": {"type", "timestamp", "experiment_id", "finding"},
            "writer": "manual / cycle scripts",
        },
        "f063_manual_verification": {
            "required": {"type", "timestamp", "experiment_id", "verdict"},
            "writer": "manual / cycle scripts",
        },
        "intervention_proposal": {
            "required": {"type", "timestamp", "experiment_id", "intervention",
                         "pearl_do_operator", "class"},
            "writer": "scripts.intervention_proposal",
        },
        # --- DR-31: new EPISTEMIC_ENGINE.md types ---
        "claim": {
            "required": {"type", "claim_id", "proposition", "claim_type",
                         "original_verdict", "confidence", "lock_time", "timestamp"},
            "writer": "scripts.reaudit_loop.py::register_claim",
        },
        "reaudit": {
            "required": {"type", "claim_id", "auditor", "timestamp", "verdict",
                         "confidence", "vocabulary_hash"},
            "writer": "scripts.reaudit_loop.py::run_reaudit",
        },
        "exclusion_event": {
            "required": {"type", "benchmark_id", "timestamp", "actor",
                         "reason_code", "source_reference"},
            "writer": "scripts.reaudit_loop.py::exclude_benchmark",
        },
        "adversary_performance": {
            "required": {"type", "timestamp", "claims_reviewed", "claims_killed",
                         "claims_missed_then_caught_later"},
            "writer": "scripts.reaudit_loop.py::log_adversary_performance",
        },
        "nine_tenths_scorecard": {
            "required": {"type", "timestamp", "scorecard", "highest_leverage"},
            "writer": "scripts.nine_tenths_loop",
        },
        "calibration_metrics": {
            "required": {"type", "timestamp", "ece", "brier_score"},
            "writer": "scripts.cycle122_calibration",
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
            continue
        # Per auditor: verification entries must carry EITHER evidence_ref
        # OR an inline evidence list. Don't allow both to be absent.
        if known_writers[etype].get("requires_evidence"):
            has_ref = "evidence_ref" in entry and entry["evidence_ref"]
            has_inline = "evidence" in entry and entry["evidence"]
            if not has_ref and not has_inline:
                unprovenanced.append({
                    "line": i,
                    "type": etype,
                    "missing_required_keys": ["evidence_ref OR evidence"],
                    "reason": "verification entry must carry evidence_ref "
                              "OR an inline evidence list — neither is present",
                    "writer": known_writers[etype]["writer"],
                })
    assert not unprovenanced, (
        "F-005 regression: ledger entries exist whose schema matches no current "
        "writer. This is the 'unprovenanced data' failure mode — entries that "
        "were produced by a writer that has since been deleted. "
        f"Unprovenanced entries: {unprovenanced[:5]}"
    )
