import hashlib
class BlueprintComposer:
    def run(self, d):
        cs=d.get('candidates',[]); mode=d.get('mode','business'); mx=d.get('max_blueprints',5)
        viable=sorted([c for c in cs if c.get('composite_score',0)>0.3],key=lambda c:c.get('composite_score',0),reverse=True)[:mx]
        return {'blueprints':[self._bp(c,mode) for c in viable],'total_viable':len(viable),'mode':mode}
    def _bp(self,c,mode):
        el=c.get('elements',[]); op=c.get('operator_applied','none'); cid=c.get('candidate_id','?')
        bpid='BP-'+hashlib.sha256(cid.encode()).hexdigest()[:10].upper()
        opn=op.replace('_',' ').title() if op!='none' else 'Combination'
        title=opn+': '+' + '.join(str(e)[:30] for e in el[:3])
        bp={'blueprint_id':bpid,'candidate_id':cid,'title':title,'summary':self._sum(el,op,c),'build_concept':self._concept(el,op),'subsystem_architecture':self._subs(el),'bom':self._bom(el,mode),'prototype_plan':self._plan(el,mode),'risks':self._risks(c),'patent_differentiation':self._diff(el,op) if mode=='business' else [],'next_experiments':self._exps(el,c),'cost_estimate_usd':len(el)*500.0*(10.0 if mode=='business' else 1.0),'timeline_estimate_days':(30+len(el)*10)*(3 if mode=='business' else 1),'skill_required':self._skill(el,op),'assumptions':c.get('assumptions',[]),'confidence':c.get('composite_score',0.0),'mode':mode}
        if mode=='consumer': bp['subsystem_architecture']=bp['subsystem_architecture'][:3]; bp['bom']=bp['bom'][:5]; bp['prototype_plan']=bp['prototype_plan'][:3]
        return bp
    def _sum(self,el,op,c):
        s='A '+str(len(el))+'-element combination'
        if op!='none': s+=' with '+op.replace('_',' ')+' applied'
        s+='. PCS='+str(round(c.get('pcs',0),2))+', CIS='+str(round(c.get('cis',0),2))+'.'
        if c.get('cemetery_risk',0)>0: s+=' Overlaps with known historical failures.'
        return s
    def _concept(self,el,op):
        ps=['Subsystem '+str(i+1)+': Integrate '+str(e) for i,e in enumerate(el)]
        om={'eliminate':'Remove non-essential subsystems.','substitute':'Replace constrained materials.','miniaturize':'Scale down dimensions.','distribute':'Distribute across nodes.','modularize':'Decompose into modules.','software_substitution':'Replace hardware with software.','change_energy_domain':'Shift energy domain.','change_information_domain':'Shift information domain.'}
        if op in om: ps.append(om[op])
        return chr(10).join(ps)
    def _subs(self,el): return [{'name':'Subsystem-'+str(i+1),'core_element':str(e),'function':'Provides '+str(e)+' capability','interfaces':['Connects to Subsystem-'+str(j+1) for j in range(len(el)) if j!=i]} for i,e in enumerate(el)]
    def _bom(self,el,mode):
        bom=[{'item':str(e),'category':'core_component','quantity':1,'notes':'Verify availability'} for e in el]
        if mode=='business': bom+=[{'item':'Integration hardware','category':'infrastructure','quantity':1,'notes':'Architecture-dependent'},{'item':'Testing equipment','category':'validation','quantity':1,'notes':'Domain-specific'}]
        return bom
    def _plan(self,el,mode):
        p=[{'phase':1,'name':'Proof of Concept','duration_days':14,'goal':'Validate core interactions'},{'phase':2,'name':'Breadboard','duration_days':21,'goal':'Low-fidelity integration'},{'phase':3,'name':'Functional Prototype','duration_days':30,'goal':'Working prototype'}]
        if mode=='business': p+=[{'phase':4,'name':'DFM','duration_days':45,'goal':'Optimize for production'},{'phase':5,'name':'Pilot','duration_days':60,'goal':'Small batch'}]
        return p
    def _risks(self,c):
        r=[]
        if c.get('cemetery_risk',0)>0: r.append({'risk':'Historical failure overlap','severity':'high','mitigation':'Review cemetery entries'})
        if c.get('pcs',1)<0.5: r.append({'risk':'Missing prerequisites','severity':'high','mitigation':'Develop prerequisites first'})
        if c.get('feasibility',1)<0.4: r.append({'risk':'Low feasibility','severity':'medium','mitigation':'Try alternative operators'})
        r.append({'risk':'Integration complexity','severity':'medium','mitigation':'Modular interfaces'})
        return r
    def _diff(self,el,op):
        d=[]
        if op!='none': d.append({'claim':'Novel '+op.replace('_',' ')+' application','strength':'medium'})
        if len(el)>=3: d.append({'claim':'Novel '+str(len(el))+'-element combination','strength':'medium'})
        d.append({'claim':'Specific integration architecture','strength':'high'})
        return d
    def _exps(self,el,c):
        e=[{'experiment':'Element compatibility test','hypothesis':'Core elements interface without degradation','priority':1},{'experiment':'Operator effect validation','hypothesis':'Operator improves target metric','priority':2}]
        if c.get('cemetery_risk',0)>0: e.insert(0,{'experiment':'Historical failure replication','hypothesis':'Failure mode mitigated','priority':0})
        return e
    def _skill(self,el,op):
        cx=len(el)+(2 if op in ('change_energy_domain','change_information_domain') else 0)
        if cx<=2:return 'beginner'
        if cx<=4:return 'intermediate'
        if cx<=6:return 'advanced'
        return 'expert'
