import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from product.ingestion.patent_parser import PatentParser
from product.ingestion.text_normalizer import TextNormalizer
from product.permutation.engine import PermutationEngine
from product.blueprint.composer import BlueprintComposer
from product.business.pipeline import BusinessPipeline
from product.consumer.pipeline import ConsumerPipeline
from product.orchestration.pipeline import Orchestrator
SAMPLE='Adaptive Passive Refrigeration Mesh\n\nFIELD OF THE INVENTION\nThe present invention relates to passive cooling systems.\n\nBACKGROUND\nCurrent refrigeration systems require significant energy input.\nThere is a need for passive cooling solutions that operate without\ncompressors or refrigerants. The problem of energy consumption in\ncooling systems remains a significant challenge.\n\nSUMMARY OF THE INVENTION\nThe invention comprises a mesh structure with selective emitters\nand phase-change materials configured to radiate heat to outer space.\n\nDETAILED DESCRIPTION\nThe mesh comprises a polymer substrate with embedded ceramic particles.\nThe substrate is configured to emit infrared radiation in the 8-13 micron\natmospheric transparency window. A phase-change material layer is disposed\non the substrate for thermal buffering.\n\nCLAIMS\n1. A passive refrigeration device comprising a mesh substrate with\nselective infrared emitters configured to radiate through the\natmospheric transparency window.\n2. The device of claim 1 wherein the mesh substrate comprises a polymer\nwith embedded ceramic particles.\n3. The device of claim 1 further comprising a phase-change material\nlayer disposed on the substrate.\n'
def test_patent_parser():
    r=PatentParser().run({'raw_text':SAMPLE}); assert r['patent_id'].startswith('PAT-'); assert 'claims' in r and 'components' in r and 'materials' in r; assert r['word_count']>50; print('  PASS: test_patent_parser')
def test_text_normalizer():
    r=TextNormalizer().run({'raw_text':'I want a cheap way to purify water at home without electricity.'}); assert 'normalized_id' in r and 'water' in r['detected_domains']; print('  PASS: test_text_normalizer')
def test_permutation_engine():
    r=PermutationEngine(max_permutations=20).run({'parsed':{'components':['mesh','emitter','pcm'],'materials':['polymer','ceramic'],'methods':['radiative cooling']},'retrieval':{'adjacency_map':{'mesh':[{'target':'solar panel','relationship':'complementary','weight':0.8}]},'cemetery_matches':[{'file':'prc.yaml','matched_term':'ceramic'}],'prerequisite_gaps':[{'node':'APRM','prerequisite':'selective emitters','node_status':'GATED'}]}}); assert r['total_generated']>0 and len(r['candidates'])>0; assert all('composite_score' in c and 'assumptions' in c for c in r['candidates']); print('  PASS: test_permutation_engine')
def test_blueprint_composer():
    r=BlueprintComposer().run({'candidates':[{'candidate_id':'T1','elements':['mesh','emitter'],'operator_applied':'modularize','composite_score':0.65,'pcs':0.7,'cis':0.6,'feasibility':0.7,'novelty':0.5,'rps':0.3,'cemetery_risk':1,'assumptions':['test']}],'mode':'business','max_blueprints':3}); assert r['total_viable']==1 and len(r['blueprints'])==1; bp=r['blueprints'][0]; assert all(k in bp for k in ['blueprint_id','title','bom','prototype_plan','risks','assumptions']); print('  PASS: test_blueprint_composer')
def test_business_pipeline():
    r=BusinessPipeline().run({'raw_text':SAMPLE}); assert r['report_type']=='business'; assert all(k in r for k in ['report_id','adjacency_map','top_candidates','blueprints','risk_register','assumptions','confidence','metrics']); print('  PASS: test_business_pipeline')
def test_consumer_pipeline():
    r=ConsumerPipeline().run({'problem_statement':'I need a way to cool my house without AC.','budget_usd':500,'skill_level':'beginner'}); assert r['report_type']=='consumer'; assert all(k in r for k in ['report_id','solutions','build_paths','cost_tiers','next_step','assumptions']); print('  PASS: test_consumer_pipeline')
def test_orchestrator():
    o=Orchestrator(); biz=o.run({'raw_text':SAMPLE}); assert biz['pipeline_mode']=='business'; con=o.run({'problem_statement':'I want clean water'}); assert con['pipeline_mode']=='consumer'; assert 'processing_time_seconds' in biz; print('  PASS: test_orchestrator')
def run_all():
    print('Running product layer tests...'); test_patent_parser(); test_text_normalizer(); test_permutation_engine(); test_blueprint_composer(); test_business_pipeline(); test_consumer_pipeline(); test_orchestrator(); print('All product tests passed.')
if __name__=='__main__': run_all()
