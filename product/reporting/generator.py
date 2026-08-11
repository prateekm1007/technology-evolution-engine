import hashlib, datetime
from product.scoring.epistemic_status import migrate_confidence_to_typed

class ReportGenerator:
    def run(self, d):
        mode=d.get('mode','business')
        if mode=='business': return self._biz(d)
        return self._con(d)
    def _biz(self,d):
        parsed=d.get('parsed',{}); ret=d.get('retrieval',{}); perm=d.get('permutation',{}); bp=d.get('blueprint',{})
        rid='RPT-BIZ-'+hashlib.sha256(datetime.datetime.now().isoformat().encode()).hexdigest()[:10].upper()
        cs=perm.get('candidates',[]); top=[c for c in cs if c.get('composite_score',0)>0.4][:10]
        risks=[]
        for c in top:
            if c.get('cemetery_risk',0)>0: risks.append({'candidate':c.get('candidate_id'),'risk':'Historical failure overlap','severity':'high'})
            if c.get('pcs',1)<0.5: risks.append({'candidate':c.get('candidate_id'),'risk':'Prerequisite gaps','severity':'high'})
        prio=[{'rank':i+1,'candidate_id':c.get('candidate_id'),'score':c.get('composite_score',0),'operator':c.get('operator_applied','none')} for i,c in enumerate(top[:5])]
        asmp=set()
        for c in cs:
            for a in c.get('assumptions',[]): asmp.add(a)
        n=max(len(cs),1); ap=sum(c.get('pcs',0) for c in cs)/n; ac=sum(c.get('cis',0) for c in cs)/n; af=sum(c.get('feasibility',0) for c in cs)/n
        # Honesty Loop (Law 27/28/29): the legacy `confidence` number
        # is computed and retained as `legacy_confidence_deprecated`
        # for one release cycle. The typed `epistemic_status` block is
        # the sanctioned output. The bare `confidence` key is forbidden
        # per Law 27 — the scanner would reject the API response.
        legacy_conf = round(af*0.5+ap*0.3+ac*0.2, 3)
        typed = migrate_confidence_to_typed(legacy_conf)
        return {'report_id':rid,'report_type':'business','generated_at':datetime.datetime.now().isoformat(),'input_summary':{'patent_id':parsed.get('patent_id'),'title':parsed.get('title'),'components_count':len(parsed.get('components',[])),'materials_count':len(parsed.get('materials',[])),'claims_count':len(parsed.get('claims',[]))},'adjacency_map':ret.get('adjacency_map',{}),'permutation_summary':{'total_generated':perm.get('total_generated',0),'total_scored':perm.get('total_scored',0),'total_survived':perm.get('total_survived',0)},'top_candidates':top,'prerequisite_gaps':ret.get('prerequisite_gaps',[]),'cemetery_analogues':ret.get('cemetery_matches',[]),'risk_register':risks,'blueprints':bp.get('blueprints',[]),'prototype_priority':prio,'assumptions':list(asmp),'epistemic_status':typed['epistemic_status'],'legacy_confidence_deprecated':typed['legacy_confidence_deprecated'],'metrics':{'avg_pcs':round(ap,3),'avg_cis':round(ac,3),'avg_feasibility':round(af,3),'total_blueprints':len(bp.get('blueprints',[]))}}
    def _con(self,d):
        parsed=d.get('parsed',{}); ret=d.get('retrieval',{}); perm=d.get('permutation',{}); bp=d.get('blueprint',{})
        rid='RPT-CON-'+hashlib.sha256(datetime.datetime.now().isoformat().encode()).hexdigest()[:10].upper()
        cs=perm.get('candidates',[]); top=[c for c in cs if c.get('composite_score',0)>0.3][:5]
        sols=[{'name':' + '.join(str(e)[:25] for e in c.get('elements',[])[:3]),'feasibility':c.get('feasibility',0),'novelty':c.get('novelty',0),'operator':c.get('operator_applied','none')} for c in top]
        paths=[{'title':b.get('title',''),'steps':[p.get('goal','') for p in b.get('prototype_plan',[])],'estimated_days':b.get('timeline_estimate_days',0),'skill':b.get('skill_required','intermediate')} for b in bp.get('blueprints',[])[:3]]
        costs=[{'blueprint':b.get('title',''),'estimated_cost_usd':b.get('cost_estimate_usd',0),'tier':'low' if b.get('cost_estimate_usd',0)<2000 else 'medium' if b.get('cost_estimate_usd',0)<10000 else 'high'} for b in bp.get('blueprints',[])[:3]]
        res=[{'source':cm.get('file',''),'relevance':cm.get('matched_term',''),'suggestion':'Review historical failure for lessons'} for cm in ret.get('cemetery_matches',[])[:3]]
        ns='Start with the highest-feasibility solution and build a proof of concept.'
        if top: ns='Start by validating: '+str(top[0].get('elements',['unknown'])[0])+'. Build a minimal PoC in 2 weeks.'
        asmp=set()
        for c in cs:
            for a in c.get('assumptions',[]): asmp.add(a)
        conf=sum(c.get('feasibility',0) for c in top)/max(len(top),1)
        # Honesty Loop (Law 27/28/29): same migration as business report.
        typed = migrate_confidence_to_typed(round(conf, 3))
        return {'report_id':rid,'report_type':'consumer','generated_at':datetime.datetime.now().isoformat(),'problem_summary':parsed.get('original_text','')[:200],'detected_domains':parsed.get('detected_domains',[]),'solutions':sols,'build_paths':paths,'cost_tiers':costs,'resurrection_suggestions':res,'nearby_alternatives':[],'next_step':ns,'assumptions':list(asmp),'epistemic_status':typed['epistemic_status'],'legacy_confidence_deprecated':typed['legacy_confidence_deprecated']}
