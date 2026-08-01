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
    ledger = gm.root / "data" / "ledger" / "predictions.jsonl"
    data = {"ledger": [json.loads(l) for l in ledger.read_text().splitlines() if l.strip()]
                       if ledger.exists() else []}
    return stamp(data, "integrated" if gm.source == "core" else "implemented")


@app.get("/api/v1/benchmarks")
def benchmarks():
    return stamp(SPECIMEN["benchmarks"], "implemented")


@app.post("/api/v1/analyze")
def analyze(req: AnalyzeRequest):
    return stamp(SPECIMEN["analysis"], "implemented")


app.mount("/static", StaticFiles(directory=FRONTEND), name="static")


@app.get("/")
def index():
    return FileResponse(FRONTEND / "index.html")
