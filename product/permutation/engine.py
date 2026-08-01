import hashlib, itertools
OPS = ['eliminate','substitute','miniaturize','distribute','modularize','software_substitution','change_energy_domain','change_information_domain']
class PermutationEngine:
    def __init__(self, max_permutations=50, max_operators=3):
        self.mx = max_permutations; self.mo = max_operators
    def run(self, d):
        parsed=d.get('parsed',{}); ret=d.get('retrieval',{})
        elems=parsed.get('components',[])+parsed.get('materials',[])+parsed.get('methods',[])
        adj=ret.get('adjacency_map',{}); cem=ret.get('cemetery_matches',[]); prereqs=ret.get('prerequisite_gaps',[])
        adjacent=[]
        for ts in adj.values():
            for t in ts:
                tg=t.get('target','')
                if tg and tg not in adjacent: adjacent.append(tg)
        raw=self._gen(elems,adjacent); oped=self._op(raw); scored=self._score(oped,prereqs,cem)
        scored.sort(key=lambda c:c.get('composite_score',0),reverse=True); scored=scored[:self.mx]
        survived=[c for c in scored if c.get('feasibility',0)>0.3]
        return {'total_generated':len(raw),'total_operated':len(oped),'total_scored':len(scored),'total_survived':len(survived),'candidates':scored,'adjacency_map':adj,'cemetery_matches':cem,'prerequisite_gaps':prereqs}
    def _gen(self,pri,sec):
        cs=[]; ae=pri+sec
        if not ae: return cs
        for combo in itertools.combinations(ae,2):
            cid='PERM-'+hashlib.sha256(str(combo).encode()).hexdigest()[:10].upper()
            cs.append({'candidate_id':cid,'elements':list(combo),'combination_type':'pairwise','source_primary':[e for e in combo if e in pri],'source_secondary':[e for e in combo if e in sec]})
        if len(ae)>=3:
            for combo in itertools.combinations(ae,3):
                cid='PERM-'+hashlib.sha256(str(combo).encode()).hexdigest()[:10].upper()
                cs.append({'candidate_id':cid,'elements':list(combo),'combination_type':'triple','source_primary':[e for e in combo if e in pri],'source_secondary':[e for e in combo if e in sec]})
                if len(cs)>=self.mx*2: break
        return cs
    def _op(self,cs):
        out=[]
        for c in cs:
            for op in OPS[:self.mo]:
                v=dict(c); v['operator_applied']=op; v['candidate_id']=c['candidate_id']+'-'+op[:4].upper(); out.append(v)
            b=dict(c); b['operator_applied']='none'; out.append(b)
        return out
    def _score(self,cs,prereqs,cem):
        pt=set(p.get('prerequisite','').lower() for p in prereqs); ct=set(c.get('matched_term','').lower() for c in cem)
        for c in cs:
            el=c.get('elements',[]); op=c.get('operator_applied','none'); es=' '.join(str(e) for e in el).lower()
            ph=sum(1 for p in pt if p in es); pcs=max(0.1,1.0-(len(pt)-ph)*0.15) if pt else 0.7
            np=len(c.get('source_primary',[])); ns=len(c.get('source_secondary',[])); cis=min(1.0,(np+ns)*0.2+(0.2 if op!='none' else 0))
            fe=0.5
            if op in ('eliminate','substitute','modularize'): fe+=0.15
            if op in ('change_energy_domain','change_information_domain'): fe-=0.1
            if len(el)>4: fe-=0.1
            fe=max(0.1,min(1.0,fe)); nov=min(1.0,cis*0.6+(0.3 if op!='none' else 0.1))
            cr=sum(1 for e in el if str(e).lower() in ct); rps=0.5 if cr>0 else 0.3
            comp=pcs*0.25+cis*0.25+fe*0.25+nov*0.15+rps*0.10
            c.update({'pcs':round(pcs,3),'cis':round(cis,3),'feasibility':round(fe,3),'novelty':round(nov,3),'rps':round(rps,3),'cemetery_risk':cr,'composite_score':round(comp,3),'assumptions':['Scoring is heuristic pending calibration','Operator effects estimated not measured','Cemetery matching keyword-based not semantic']})
        return cs
