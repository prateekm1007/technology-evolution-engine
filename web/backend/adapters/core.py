"""Bridge to the frozen core. READ-ONLY (Rule 8)."""
import importlib, json, pathlib


class CoreUnavailable(Exception):
    pass


def _read_ledger_safely(ledger_path):
    """Read a JSONL ledger with total-corruption detection.

    F-AUD-002 / F-013 fix: previously this module did
    ``[json.loads(l) for l in ledger.read_text().splitlines() if l.strip()]``
    with no error handling. The same crash that F-006 fixed in
    ``web/backend/main.py::evidence()`` was still live here because the
    fix landed in only one of the two readers (parallel development,
    the F-013/F-015 class of bug documented in FAILURES.md).

    This helper consolidates the corruption-aware read logic so both
    readers (this module and main.py::evidence) share it. Per
    ANTI_ENTROPY.md rule "Decouple modules", this is a function
    rather than a class — it has no state and one job.

    Returns a dict with: ``ledger`` (list of parsed entries),
    ``malformed_lines`` (list of ``{line, error, preview}`` dicts),
    and ``entry_count`` (int). A totally-corrupted file (the F-005
    signature: many short lines) yields ``entry_count=0`` and a single
    ``malformed_lines`` entry describing the corruption.
    """
    entries, malformed = [], []
    if not ledger_path.exists():
        return {"ledger": entries, "malformed_lines": malformed,
                "entry_count": 0}
    raw_text = ledger_path.read_text(encoding="utf-8")
    lines = raw_text.splitlines()
    non_empty = [ln for ln in lines if ln.strip()]
    # Total-corruption heuristic: >500 non-empty lines AND every
    # non-empty line is <5 chars => the file was almost certainly
    # written one-char-per-line (F-005 failure mode).
    if len(non_empty) > 500 and all(len(ln) < 5 for ln in non_empty):
        salvage = raw_text.replace("\n", "").replace("\r", "")
        malformed.append({
            "line": 1,
            "error": ("Total file corruption detected: file appears to be "
                      "written one character per line. Salvaged raw text "
                      "below. See evidence/corruption/POSTMORTEM_F005.md."),
            "preview": salvage[:200],
            "salvaged_length": len(salvage),
        })
        return {"ledger": entries, "malformed_lines": malformed,
                "entry_count": 0}
    for i, line in enumerate(lines, start=1):
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError as e:
            malformed.append({"line": i, "error": str(e),
                              "preview": line[:120]})
    return {"ledger": entries, "malformed_lines": malformed,
            "entry_count": len(entries)}


class CoreAdapter:
    def __init__(self, repo_root):
        self.root = pathlib.Path(repo_root)
        graph_path = self.root / "data" / "civilization_graph.json"
        if not graph_path.exists():
            raise CoreUnavailable(f"graph not found: {graph_path}")
        try:
            self.business = importlib.import_module("product.business.pipeline")
            self.consumer = importlib.import_module("product.consumer.pipeline")
        except ModuleNotFoundError as e:
            raise CoreUnavailable(f"product layer not importable: {e}")
        self.graph = json.loads(graph_path.read_text())

    def run_pipeline(self, mode, input_type, payload):
        if mode == "consumer":
            return self.consumer.ConsumerPipeline().run(payload)
        return self.business.BusinessPipeline().run(payload)

    def read_evidence(self):
        """Read the prediction ledger, tolerating corruption.

        F-AUD-002 / F-013 fix: this method previously crashed with
        ``JSONDecodeError`` on the F-005 corrupted ledger. It now
        shares the corruption-aware read logic with
        ``main.py::evidence()`` via the ``_read_ledger_safely``
        helper.
        """
        ledger_path = self.root / "data" / "ledger" / "predictions.jsonl"
        return _read_ledger_safely(ledger_path)
