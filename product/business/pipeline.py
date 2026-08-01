from product.ingestion.patent_parser import PatentParser
from product.retrieval.graph_retriever import GraphRetriever
from product.permutation.engine import PermutationEngine
from product.blueprint.composer import BlueprintComposer
from product.reporting.generator import ReportGenerator
class BusinessPipeline:
    def __init__(self, graph_path=None):
        self.parser=PatentParser(); self.retriever=GraphRetriever(graph_path=graph_path); self.permuter=PermutationEngine(max_permutations=50); self.blueprinter=BlueprintComposer(); self.reporter=ReportGenerator()
    def run(self, d):
        parsed=self.parser.run(d); retrieval=self.retriever.run(parsed)
        permutation=self.permuter.run({'parsed':parsed,'retrieval':retrieval})
        blueprint=self.blueprinter.run({'candidates':permutation.get('candidates',[]),'mode':'business','max_blueprints':5})
        return self.reporter.run({'mode':'business','parsed':parsed,'retrieval':retrieval,'permutation':permutation,'blueprint':blueprint})
