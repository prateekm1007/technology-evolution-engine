from product.ingestion.patent_parser import PatentParser
from product.retrieval.graph_retriever import GraphRetriever
from product.permutation.engine import PermutationEngine
from product.blueprint.composer import BlueprintComposer
from product.reporting.generator import ReportGenerator

class BusinessPipeline:
    def __init__(self, graph_path=None):
        self.parser=PatentParser(); self.retriever=GraphRetriever(graph_path=graph_path); self.permuter=PermutationEngine(max_permutations=50); self.blueprinter=BlueprintComposer(); self.reporter=ReportGenerator()

    def run(self, d):
        # Per DR-62 (cycle 198): input validation — raise loudly on unexpected schema.
        # The old code silently returned empty results when given {'text': ...} instead
        # of {'raw_text': ...}, producing a zero-valued report that looked like a valid
        # negative result instead of a broken call.
        if not isinstance(d, dict):
            raise ValueError(f"BusinessPipeline.run() expects a dict, got {type(d).__name__}")
        if 'raw_text' not in d:
            raise ValueError(
                f"BusinessPipeline.run() requires 'raw_text' key. "
                f"Got keys: {list(d.keys())}. "
                f"This is DR-62: the old code silently returned empty results "
                f"on malformed input — now it raises loudly."
            )
        parsed=self.parser.run(d); retrieval=self.retriever.run(parsed)
        permutation=self.permuter.run({'parsed':parsed,'retrieval':retrieval})
        blueprint=self.blueprinter.run({'candidates':permutation.get('candidates',[]),'mode':'business','max_blueprints':5})
        return self.reporter.run({'mode':'business','parsed':parsed,'retrieval':retrieval,'permutation':permutation,'blueprint':blueprint})
