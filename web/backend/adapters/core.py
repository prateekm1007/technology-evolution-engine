"""Bridge to the frozen core. READ-ONLY (Rule 8)."""
import importlib, json, pathlib


class CoreUnavailable(Exception):
    pass


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
            return self.consumer.ConsumerPipeline().solve(payload)
        return self.business.BusinessPipeline().analyze(payload)

    def read_evidence(self):
        ledger = self.root / "data" / "ledger" / "predictions.jsonl"
        return {"ledger": [json.loads(l) for l in ledger.read_text().splitlines() if l.strip()]
                          if ledger.exists() else []}
