import re, hashlib
class TextNormalizer:
    DOMS={'energy':['solar','battery','wind','grid','power','energy'],'water':['water','purification','desalination','filtration'],'computing':['computer','software','algorithm','ai','ml'],'materials':['material','polymer','ceramic','composite'],'biotech':['gene','protein','cell','medical'],'manufacturing':['manufactur','fabricat','3d print'],'transport':['vehicle','transport','drone'],'agriculture':['crop','farm','soil','food'],'communications':['wireless','network','signal','iot'],'construction':['building','construction','infrastructure']}
    CONS={'budget':['budget','cost','cheap','affordable'],'time':['fast','quick','deadline','urgent'],'size':['small','compact','portable'],'environment':['outdoor','indoor','harsh'],'safety':['safe','non-toxic']}
    def run(self,d):
        t=d.get('raw_text','') or d.get('problem_statement','')
        return {'normalized_id':'NORM-'+hashlib.sha256(t.encode()).hexdigest()[:12].upper(),'original_text':t,'detected_domains':self._doms(t),'detected_constraints':self._cons(t),'problem_type':self._ptype(t),'entities':self._ents(t),'action_verbs':self._acts(t),'negations':self._negs(t),'complexity_score':self._cx(t),'word_count':len(t.split())}
    def _doms(self,t):
        tl=t.lower()
        d=[dom for dom,ks in self.DOMS.items() if any(k in tl for k in ks)]
        return d if d else ['general']
    def _cons(self,t):
        tl=t.lower()
        return {c:'mentioned' for c,ks in self.CONS.items() if any(k in tl for k in ks)}
    def _ptype(self,t):
        tl=t.lower()
        if any(x in tl for x in ['improve','better','optimize']):return 'improvement'
        if any(x in tl for x in ['create','build','make','design']):return 'creation'
        if any(x in tl for x in ['replace','substitute']):return 'substitution'
        if any(x in tl for x in ['reduce','eliminate','remove']):return 'elimination'
        if any(x in tl for x in ['combine','integrate','merge']):return 'combination'
        return 'exploration'
    def _ents(self,t):
        es=re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b',t)
        return [e for e in es if e not in {'The','This','That','What','How','Why','When','Where'}][:20]
    def _acts(self,t):
        return [m[0]+' '+m[1] for m in re.findall(r'\b(want|need|wish|hope|plan|seek|require)\b\s+(\w+)',t,re.I)]
    def _negs(self,t):
        return [m[0]+' '+m[1] for m in re.findall(r'\b(no|not|without|never|avoid)\b\s+(\w+(?:\s+\w+)?)',t,re.I)]
    def _cx(self,t):
        s=0.0
        wc=len(t.split())
        if wc>20:s+=0.2
        if wc>50:s+=0.2
        if len(self._doms(t))>1:s+=0.3
        s+=min(len(self._cons(t))*0.1,0.3)
        return min(s,1.0)
