"""
TEE Web Backend — production API over the frozen core.
Rule 8 compliant: reads engine/ and data/, never modifies them.
Every response carries a verification field.
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List
import time, pathlib, json

from adapters.graph_model import GraphModel
from adapters.oracle_deep import DeepOracle
from adapters.specimen import SPECIMEN

ROOT = pathlib.Path(__file__).resolve().parent
FRONTEND = ROOT.parent / "frontend"

app = FastAPI(title="Technology Evolution Engine", version="1.0.0")

gm = GraphModel(repo_root=ROOT.parents[1])
oracle = DeepOracle(gm)
BACKEND_STATUS = "integrated" if gm.source == "core" else "implemented"


class AnalyzeRequest(BaseModel):
    mode: str = "business"
    input_type: str = "patent"
    title: Optional[str] = None
    text: Optional[str] = None
    # Some callers send a structured problem statement instead of free-form
    # 'text'. Accept both at the schema boundary so neither is silently
    # dropped (F-001: previously a caller sending only problem_statement had
    # their input discarded).
    problem_statement: Optional[str] = None


class SimRequest(BaseModel):
    constraint: str
    direction: str = "decrease"
    magnitude: str = "2x"


def stamp(payload, verification):
    payload["verification"] = {
        "level": verification, "is_fact": verification == "verified",
        "note": ("Produced by a live run against the repository."
                 if verification == "verified"
                 else "Preview/hypothesis — not yet a verified pipeline run.")}
    return payload


@app.get("/api/v1/health")
def health():
    return {"status": "ok", "core_bound": gm.source == "core",
            "backend_status": BACKEND_STATUS, "graph_nodes": len(gm.nodes)}


@app.post("/api/v1/simulate")
def simulate(req: SimRequest):
    result = oracle.simulate(req.constraint, req.direction, req.magnitude)
    return stamp(result, "integrated" if gm.source == "core" else "implemented")


@app.get("/api/v1/graph")
def graph():
    """F-003: wire layout_cache into the graph endpoint so the deterministic
    clustered layout is actually used (and the cached path is exercised in
    tests, not just importable). Falls back to the explorer payload without
    layout if the cache layer raises for any reason — graph must not 500."""
    out = gm.to_explorer()
    try:
        from adapters.layout_cache import compute_layout
        layout = compute_layout(gm, ROOT / ".cache" / "layouts")
        # Merge positions in without dropping anything the explorer already
        # produced; consumers that want positions read 'layout.positions'.
        out["layout"] = {"positions": layout["positions"], "key": layout["key"]}
    except Exception as e:
        out["layout"] = {"error": f"{type(e).__name__}: {e}"}
    return stamp(out, "integrated" if gm.source == "core" else "implemented")


@app.get("/api/v1/evidence")
def evidence():
    """Append-only ledger read. Skips malformed lines instead of 500ing.

    F-002: Detect total file corruption (e.g. one character per line from
    a botched writer). Without this branch, the per-line parser happily
    'parses' single digits as JSON numbers and returns spurious entries —
    silently lying about the ledger state. Total-corruption is detected
    by the heuristic 'many lines, all very short', then we salvage the
    raw text by stripping newlines and report it as a single malformed
    entry for investigation.
    """
    ledger_path = gm.root / "data" / "ledger" / "predictions.jsonl"
    entries, malformed = [], []
    if ledger_path.exists():
        raw_text = ledger_path.read_text(encoding="utf-8")
        lines = raw_text.splitlines()
        # Heuristic: >500 non-empty lines AND every non-empty line is <5 chars
        # => the file was almost certainly written one-char-per-line.
        non_empty = [ln for ln in lines if ln.strip()]
        if len(non_empty) > 500 and all(len(ln) < 5 for ln in non_empty):
            salvage = raw_text.replace("\n", "").replace("\r", "")
            malformed.append({
                "line": 1,
                "error": "Total file corruption detected: file appears to be written one character per line. Salvaged raw text below.",
                "preview": salvage[:200],
                "salvaged_length": len(salvage),
            })
        else:
            for i, line in enumerate(lines, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError as e:
                    malformed.append({"line": i, "error": str(e), "preview": line[:120]})
    data = {"ledger": entries, "malformed_lines": malformed, "entry_count": len(entries)}
    return stamp(data, "integrated" if gm.source == "core" else "implemented")


@app.get("/api/v1/benchmarks")
def benchmarks():
    return stamp(SPECIMEN["benchmarks"], "implemented")


@app.post("/api/v1/analyze")
def analyze(req: AnalyzeRequest):
    """
    Real wiring. Falls back to SPECIMEN with an explicit stamp
    if the product-layer pipelines are not importable or raise.

    Verification level is 'integrated', NOT 'verified' — per Law 8 and
    the handoff rule "No 'verified' label without failure cases", we
    cannot stamp 'verified' until adversarial tests, replay capability,
    and failure logging are in place. Lying about verification is worse
    than admitting it's only integrated.
    """
    try:
        from adapters.core import CoreAdapter, CoreUnavailable
        core = CoreAdapter(repo_root=ROOT.parents[1])
        # Prefer an explicit problem_statement if the caller supplied one;
        # otherwise use free-form text. Both raw_text and problem_statement
        # are populated so whichever key the downstream pipeline reads
        # (PatentParser._problem reads BACKGROUND sections, TextNormalizer
        # reads raw_text first then problem_statement) the content reaches
        # the engine.
        content = req.problem_statement or req.text or ""
        payload = {
            "raw_text": content,
            "problem_statement": content,
            "patent_id": None,
            "title": req.title,
        }
        result = core.run_pipeline(
            mode=req.mode,
            input_type=req.input_type,
            payload=payload,
        )
        return stamp(result, "integrated")
    except Exception as e:
        out = dict(SPECIMEN["analysis"])
        out["fallback_reason"] = f"{type(e).__name__}: {e}"
        return stamp(out, "implemented")


app.mount("/static", StaticFiles(directory=FRONTEND), name="static")


@app.get("/")
def index():
    return FileResponse(FRONTEND / "index.html")
