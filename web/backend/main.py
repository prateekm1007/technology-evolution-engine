"""TEE Web Backend — production API over the frozen core."""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import pathlib

from adapters.graph_model import GraphModel
from adapters.oracle_deep import DeepOracle

ROOT = pathlib.Path(__file__).resolve().parent
FRONTEND = ROOT.parent / "frontend"
app = FastAPI(title="Technology Evolution Engine", version="1.0.0")

gm = GraphModel(repo_root=ROOT.parents[1])
oracle = DeepOracle(gm)

class SimRequest(BaseModel):
    constraint: str
    direction: str = "decrease"
    magnitude: str = "2x"

def stamp(payload, verification):
    payload["verification"] = {
        "level": verification, "is_fact": verification == "verified",
        "note": "Produced by a live run against the repository." if verification == "verified" else "Preview/hypothesis"}
    return payload

@app.get("/api/v1/health")
def health():
    return {"status": "ok", "core_bound": gm.source == "core", "graph_nodes": len(gm.nodes)}

@app.post("/api/v1/simulate")
def simulate(req: SimRequest):
    result = oracle.simulate(req.constraint, req.direction, req.magnitude)
    return stamp(result, "integrated" if gm.source == "core" else "implemented")

@app.get("/api/v1/graph")
def graph():
    return stamp(gm.to_explorer(), "integrated" if gm.source == "core" else "implemented")

app.mount("/static", StaticFiles(directory=FRONTEND), name="static")

@app.get("/")
def index():
    return FileResponse(FRONTEND / "index.html")
