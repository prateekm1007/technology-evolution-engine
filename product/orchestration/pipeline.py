import datetime, json, os
from product.business.pipeline import BusinessPipeline
from product.consumer.pipeline import ConsumerPipeline
LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'logs')
class Orchestrator:
    def __init__(self, graph_path=None):
        self.business=BusinessPipeline(graph_path=graph_path); self.consumer=ConsumerPipeline(graph_path=graph_path)
    def run(self, d):
        mode=d.get('mode') or self._detect(d); started=datetime.datetime.now()
        result=self.business.run(d) if mode=='business' else self.consumer.run(d)
        elapsed=(datetime.datetime.now()-started).total_seconds(); self._log(mode,d,result,elapsed)
        result['pipeline_mode']=mode; result['processing_time_seconds']=round(elapsed,3)
        return result
    def _detect(self, d):
        if d.get('patent_id') or d.get('claims'): return 'business'
        raw=d.get('raw_text','')
        if any(s in raw.lower() for s in ['comprising','wherein','embodiment','claim','prior art']): return 'business'
        if d.get('problem_statement') or d.get('budget_usd') or d.get('skill_level'): return 'consumer'
        return 'consumer'
    def _log(self, mode, inp, result, elapsed):
        if not os.path.exists(LOGS_DIR): os.makedirs(LOGS_DIR)
        entry={'timestamp':datetime.datetime.now().isoformat(),'mode':mode,'input_keys':list(inp.keys()),'processing_time_seconds':round(elapsed,3),'report_id':result.get('report_id','?'),'confidence':result.get('confidence',0)}
        with open(os.path.join(LOGS_DIR,'pipeline_runs.jsonl'),'a') as f: f.write(json.dumps(entry)+chr(10))
