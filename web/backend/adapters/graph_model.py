"""
Graph model for the explorer + Oracle. Typed, epoched nodes and classed edges.
READ-ONLY against the frozen core (Rule 8).
"""
import json, pathlib, random

NODE_TYPES = ["domain", "principle", "process", "component", "system", "industry", "cemetery"]
EDGE_CLASSES = ["structural", "functional", "historical"]

HISTORICAL_RELS = {
    "inspired_by",
    "resurrected_from",
    "failed_because",
    "preceded_by",
}


def _edge_class(rel):
    return "historical" if rel in HISTORICAL_RELS else "structural"


EPOCHS = {"domain": 1900, "principle": 1880, "process": 1920,
          "component": 1950, "system": 1970, "industry": 1980}


class GraphModel:
    def __init__(self, repo_root):
        self.root = pathlib.Path(repo_root)
        self.source = "specimen"
        path = self.root / "data" / "civilization_graph.json"
        if path.exists():
            try:
                raw = json.loads(path.read_text())
                self.nodes, self.edges = self._from_core(raw)
                self.source = "core"
            except Exception:
                self.nodes, self.edges = self._specimen()
        else:
            self.nodes, self.edges = self._specimen()
        self._index()

    def _index(self):
        self.by_id = {n["id"]: n for n in self.nodes}
        self.out, self.inc = {}, {}
        for e in self.edges:
            self.out.setdefault(e["source"], []).append(e)
            self.inc.setdefault(e["target"], []).append(e)

    def _from_core(self, raw):
        nodes, edges = [], []
        for n in raw.get("nodes", []):
            ntype = n.get("type", "component")
            if ntype not in NODE_TYPES:
                ntype = "cemetery" if (n.get("is_cemetery") or ntype == "failure") else "component"
            nodes.append({
                "id": n["id"], "label": n.get("label", n["id"]), "type": ntype,
                "epoch": n.get("epoch", EPOCHS.get(ntype, 1950)),
                "domain": n.get("domain", "general"),
                "constraints": n.get("constraints", []),
                "cost_drivers": n.get("cost_drivers", []),
                "is_cemetery": ntype == "cemetery",
                "lesson": n.get("lesson"),
                "failed_because": n.get("failed_because"),
            })
        for e in raw.get("edges", []):
            rel = e.get("rel", "depends_on")
            cls = e.get("class") or _edge_class(rel)
            if cls not in EDGE_CLASSES:
                cls = _edge_class(rel)
            edges.append({"source": e["source"], "target": e["target"],
                          "class": cls, "rel": rel,
                          "weight": float(e.get("weight", 1.0))})
        return nodes, edges

    def _specimen(self):
        rng = random.Random(42)
        domains = ["fluid dynamics", "thermodynamics", "materials", "electronics",
                   "sensing", "computation", "manufacturing", "energy", "water", "transport"]
        nodes, edges = [], []
        for d in domains:
            nodes.append({"id": f"dom_{d}", "label": d, "type": "domain", "epoch": 1890,
                          "domain": d, "constraints": [], "cost_drivers": [], "is_cemetery": False})
        for p in ["centrifugal force", "bernoulli principle", "heat transfer",
                  "electromagnetism", "feedback control", "particle transport"]:
            nodes.append({"id": f"pri_{p}", "label": p, "type": "principle", "epoch": 1870,
                          "domain": rng.choice(domains), "constraints": [], "cost_drivers": [],
                          "is_cemetery": False})
        for d in domains:
            for kind, prefix, epoch in [("process", "proc", 1920), ("component", "comp", 1955),
                                        ("system", "sys", 1975), ("industry", "ind", 1985)]:
                for i in range(3):
                    nid = f"{prefix}_{d}_{i}"
                    cons = rng.sample(["cost", "energy", "material", "regulation", "manufacturing"],
                                      rng.randint(1, 3))
                    nodes.append({"id": nid, "label": f"{d} {kind} {i+1}", "type": kind,
                                  "epoch": epoch + rng.randint(0, 20), "domain": d,
                                  "constraints": cons, "cost_drivers": cons, "is_cemetery": False})
                    edges.append({"source": f"dom_{d}", "target": nid,
                                  "class": "structural", "rel": "contains", "weight": 1.0})
        for name, lesson, cb in [("early EVs", "battery density too low", "energy"),
                                 ("airships", "lift-gas economics", "cost"),
                                 ("Iridium", "infra prerequisite arrived late", "regulation")]:
            nodes.append({"id": f"cem_{name}", "label": name, "type": "cemetery", "epoch": 1990,
                          "domain": rng.choice(domains), "constraints": [cb], "cost_drivers": [],
                          "is_cemetery": True, "lesson": lesson, "failed_because": cb})
        return nodes, edges

    def binding_nodes(self, constraint):
        return [n for n in self.nodes if constraint in n.get("constraints", [])]

    def neighbors(self, nid):
        ids = {e["target"] for e in self.out.get(nid, [])} | {e["source"] for e in self.inc.get(nid, [])}
        return [self.by_id[i] for i in ids if i in self.by_id]

    def append_ledger(self, entry):
        import datetime
        ledger = self.root / "data" / "ledger" / "predictions.jsonl"
        ledger.parent.mkdir(parents=True, exist_ok=True)
        entry["timestamp"] = datetime.datetime.utcnow().isoformat() + "Z"
        with ledger.open("a") as f:
            f.write(json.dumps(entry) + "\n")

    def to_explorer(self):
        return {"nodes": self.nodes, "edges": self.edges,
                "node_count": len(self.nodes), "edge_count": len(self.edges),
                "source": self.source, "epochs": [1850, 2030]}
