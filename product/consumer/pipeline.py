from product.ingestion.text_normalizer import TextNormalizer
from product.retrieval.graph_retriever import GraphRetriever
from product.permutation.engine import PermutationEngine
from product.blueprint.composer import BlueprintComposer
from product.reporting.generator import ReportGenerator
class ConsumerPipeline:
    def __init__(self, graph_path=None):
        self.normalizer=TextNormalizer(); self.retriever=GraphRetriever(graph_path=graph_path); self.permuter=PermutationEngine(max_permutations=30); self.blueprinter=BlueprintComposer(); self.reporter=ReportGenerator()
    def run(self, d):
        parsed=self.normalizer.run(d)
        ri={'components':parsed.get('entities',[]),'materials':[],'methods':parsed.get('action_verbs',[]),'detected_domains':parsed.get('detected_domains',[])}
        retrieval=self.retriever.run(ri)
        permutation=self.permuter.run({'parsed':{'components':parsed.get('entities',[]),'materials':[],'methods':parsed.get('action_verbs',[])},'retrieval':retrieval})
        blueprint=self.blueprinter.run({'candidates':permutation.get('candidates',[]),'mode':'consumer','max_blueprints':3})
        return self.reporter.run({'mode':'consumer','parsed':parsed,'retrieval':retrieval,'permutation':permutation,'blueprint':blueprint})
