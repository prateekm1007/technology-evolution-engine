import re, hashlib
class PatentParser:
    CLAIM_PAT = re.compile(r'\d+\.\s+(.*?)(?=\d+\.\s+|$)', re.DOTALL)
    HEADERS = ['FIELD OF THE INVENTION','BACKGROUND','SUMMARY OF THE INVENTION','DETAILED DESCRIPTION','CLAIMS','ABSTRACT']
    # Component keywords for extraction when "comprising" doesn't capture them.
    COMPONENT_KEYWORDS = ['pump','sensor','coating','membrane','exchanger','substrate',
                          'valve','motor','circuit','electrode','battery','panel',
                          'filter','chamber','nozzle','actuator','controller']
    def parse(self, d):
        """Phase 3 ingestion interface. Accepts a dict with 'text' and
        optional 'provenance', returns structured extraction with
        components, materials, constraints, and provenance attached."""
        t = d.get('text', d.get('raw_text', ''))
        pid = d.get('id', d.get('patent_id')) or 'PAT-'+hashlib.sha256(t.encode()).hexdigest()[:12].upper()
        # Run the existing extraction logic.
        base = self.run({'raw_text': t, 'patent_id': pid})
        # Add components from keyword scan (supplements "comprising" extraction).
        existing_comps = set(str(c).lower() for c in base.get('components', []))
        extra_comps = []
        for kw in self.COMPONENT_KEYWORDS:
            if kw in t.lower() and kw not in existing_comps:
                extra_comps.append(kw)
                existing_comps.add(kw)
        base['components'] = list(base.get('components', [])) + extra_comps
        # Attach provenance if provided.
        if 'provenance' in d:
            base['provenance'] = d['provenance']
        else:
            base['provenance'] = {
                'source': pid, 'source_type': 'patent',
                'title': d.get('title', base.get('title', '')),
                'extracted_by': 'product.ingestion.patent_parser',
                'confidence': base.get('parse_confidence', 0.0),
            }
        return base
    def run(self, d):
        t = d.get('raw_text','')
        pid = d.get('patent_id') or 'PAT-'+hashlib.sha256(t.encode()).hexdigest()[:12].upper()
        return {'patent_id':pid,'title':self._title(t),'claims':self._claims(t),'components':self._comps(t),'materials':self._mats(t),'methods':self._methods(t),'problem_statement':self._problem(t),'constraints':self._constraints(t),'dependencies':self._deps(t),'sections':self._sections(t),'classification_codes':list(set(re.findall(r'[A-H]\d{2}[A-Z]\s*\d{1,4}(?:/\d+)?',t))),'word_count':len(t.split()),'parse_confidence':self._conf(t)}
    def _title(self,t):
        for l in t.strip().split('\n')[:5]:
            l=l.strip()
            if len(l)>10 and not l.isupper(): return l
        return 'Untitled'
    def _claims(self,t):
        s=self._sec(t,'CLAIMS') or t
        return [m.strip() for m in self.CLAIM_PAT.findall(s) if len(m.strip())>20]
    def _comps(self,t):
        c=[]
        for k in ['comprising','including','consisting of','disposed on','coupled to','configured to']:
            c.extend([m.strip() for m in re.findall(k+r'\s+(.*?)(?:\.|,|;)',t,re.I) if len(m.strip())>5])
        return list(set(c))[:50]
    def _mats(self,t):
        ms=['polymer','ceramic','metal','alloy','composite','silicon','graphene','carbon','titanium','aluminum','steel','copper','glass','membrane','substrate','semiconductor']
        return [m for m in ms if m in t.lower()]
    def _methods(self,t):
        r=[]
        for k in ['method comprising','steps of','process of','fabricating','manufacturing','depositing','etching','sintering']:
            r.extend([m.strip() for m in re.findall(k+r'\s+(.*?)(?:\.|;)',t,re.I) if len(m.strip())>5])
        return list(set(r))[:30]
    def _problem(self,t):
        bg=self._sec(t,'BACKGROUND')
        if bg:
            for s in re.split(r'[.!?]',bg):
                s=s.strip()
                if any(x in s.lower() for x in ['problem','need','limitation','challenge']) and len(s)>30: return s
        return ''
    def _constraints(self,t):
        cm={'energy':['power','energy','watt','voltage'],'temperature':['temperature','thermal','heat','cooling'],'size':['dimension','size','volume','weight'],'cost':['cost','price','expense'],'safety':['safety','toxic','hazard'],'manufacturing':['manufactur','fabricat','production']}
        tl=t.lower()
        return {c:'present' for c,ks in cm.items() if any(k in tl for k in ks)}
    def _deps(self,t):
        d=[]
        for p in [r'requires?\s+(.*?)(?:\.|,)',r'depends?\s+(?:on|upon)\s+(.*?)(?:\.|,)']:
            d.extend([m.strip() for m in re.findall(p,t,re.I) if len(m.strip())>5])
        return list(set(d))[:20]
    def _sections(self,t):
        return {h.lower().replace(' ','_'):self._sec(t,h) for h in self.HEADERS if self._sec(t,h)}
    def _sec(self,t,h):
        m=re.search(h+r'[\s:]*\n(.*?)(?=[A-Z][A-Z\s]{5,}|$)',t,re.DOTALL|re.I)
        return m.group(1).strip() if m else ''
    def _conf(self,t):
        s=0.0
        if len(t)>500:s+=0.2
        if len(t)>2000:s+=0.2
        if 'claim' in t.lower():s+=0.2
        if any(h in t.upper() for h in self.HEADERS):s+=0.2
        if re.search(r'[A-H]\d{2}',t):s+=0.2
        return min(s,1.0)
