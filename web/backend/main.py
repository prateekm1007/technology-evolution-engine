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
    return stamp(gm.to_explorer(), "integrated" if gm.source == "core" else "implemented")


@app.get("/api/v1/evidence")
def evidence():
    """Append-only ledger read. Skips malformed lines instead of 500ing."""
    ledger_path = gm.root / "data" / "ledger" / "predictions.jsonl"
    entries, malformed = [], []
    if ledger_path.exists():
        for i, line in enumerate(ledger_path.read_text().splitlines(), start=1):
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
    """
    try:
        from adapters.core import CoreAdapter, CoreUnavailable
        core = CoreAdapter(repo_root=ROOT.parents[1])
        # NOTE: the product-layer pipelines read 'raw_text' / 'problem_statement' /
        # 'patent_id' — not 'text' / 'title'. Map explicitly so content isn't
        # silently dropped at this boundary (see PatentParser._comps,
        # TextNormalizer.run for the keys each pipeline actually reads).
        payload = {
            "raw_text": req.text or "",
            "problem_statement": req.text or "",
            "patent_id": None,
            "title": req.title,
        }
        result = core.run_pipeline(
            mode=req.mode,
            input_type=req.input_type,
            payload=payload,
        )
        return stamp(result, "verified")
    except Exception as e:
        out = dict(SPECIMEN["analysis"])
        out["fallback_reason"] = f"{type(e).__name__}: {e}"
        return stamp(out, "implemented")


app.mount("/static", StaticFiles(directory=FRONTEND), name="static")


@app.get("/")
def index():
    return FileResponse(FRONTEND / "index.html")
