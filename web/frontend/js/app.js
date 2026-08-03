
/* TEE front-end — SPA over the /api/v1 surface. Consumer mode translates
   every metric into plain language; every result shows its verification stamp. */
const $=s=>document.querySelector(s);
const API='/api/v1';
const state={mode:'business',data:{},health:null};
const LEX={
  business:{opportunity:'Opportunity score',dd:'Discovery delta',conf:'Confidence',
    why:'Why this exists',prereq:'Prerequisites',risks:'Risks',proto:'Prototype plan',rejected:'Why alternatives were rejected'},
  consumer:{opportunity:'How strong is this?',dd:'How new is this idea?',conf:'How sure are we?',
    why:'Why this makes sense',prereq:"What's missing",risks:'What could go wrong',proto:'What to build first',rejected:'Ideas we set aside'}};
const t=k=>LEX[state.mode][k];
async function api(path,opts){try{const r=await fetch(API+path,opts);return await r.json();}catch(e){return null;}}
async function boot(){
  state.health=await api('/health');
  const dot=$('#core-dot'),lbl=$('#core-label');
  if(state.health&&state.health.core_bound){dot.className='dot live';lbl.textContent='core: live';}
  else{dot.className='dot spec';lbl.textContent='core: specimen';}
  $('#mode-consumer').onclick=()=>setMode('consumer');
  $('#mode-business').onclick=()=>setMode('business');
  window.addEventListener('hashchange',route);route();
}
function setMode(m){state.mode=m;
  $('#mode-consumer').classList.toggle('is-on',m==='consumer');
  $('#mode-business').classList.toggle('is-on',m==='business');route();}
const VIEWS={'':workbench,graph:graph,blueprint:blueprint,evidence:evidence,simulate:simulate,benchmarks:benchmarks};
function route(){const r=location.hash.replace('#/','');
  document.querySelectorAll('.rail-nav a').forEach(a=>a.classList.toggle('is-active',a.dataset.route===r));
  (VIEWS[r]||workbench)();requestAnimationFrame(observeReveals);}
const stampHtml=v=>(v&&v.is_fact)?'<span class="stamp verified">Verified</span>':'<span class="stamp hypothesis">Hypothesis — preview</span>';
function countUp(el,target,dec=0,ms=900){const t0=performance.now();
  (function tick(now){const p=Math.min((now-t0)/ms,1),e=1-Math.pow(1-p,3);
    el.textContent=(target*e).toFixed(dec);if(p<1)requestAnimationFrame(tick);})(t0);}
function observeReveals(){const io=new IntersectionObserver(es=>es.forEach(e=>e.isIntersecting&&e.target.classList.add('in')),{threshold:.12});
  document.querySelectorAll('.reveal').forEach(el=>io.observe(el));}
const readout=(k,v,cls='')=>'<div class="readout"><span class="k">'+k+'</span><span class="leader"></span><span class="v '+cls+'">'+v+'</span></div>';

function workbench(){
  $('#view').innerHTML=
    '<p class="eyebrow">Workbench · '+state.mode+' mode</p>'+
    '<h1 class="disp">What could this<br/>become?</h1>'+
    '<p class="lede">Feed the engine a patent, a paper, an idea, or an objective. It returns opportunities, risks, what\'s missing, and what to build first — with every claim stamped by its verification status.</p>'+
    '<div class="bench">'+
    '<section class="panel reveal"><h2 class="disp">Input</h2>'+
    '<div class="field"><label>Input type</label><select id="in-type"><option value="patent">Patent</option><option value="paper">Research paper</option><option value="idea">Idea</option><option value="objective">Objective</option></select></div>'+
    '<div class="field"><label>Title</label><input id="in-title" value="Cyclonic separation system for dust and debris collection"/></div>'+
    '<div class="field"><label>Abstract / description / objective</label><textarea id="in-text">A cyclonic separation system that maintains suction by spinning particulate into a collection vessel, reducing filter clogging.</textarea></div>'+
    '<button class="btn" id="run">Run analysis &#9656;</button></section>'+
    '<section class="panel reveal" id="bench-out"><h2 class="disp">Analysis</h2><p class="lede">Results appear here. Every number carries a verification stamp.</p></section></div>';
  $('#run').onclick=runAnalysis;
}
async function runAnalysis(){
  const btn=$('#run');btn.disabled=true;btn.textContent='Traversing graph…';
  const res=await api('/analyze',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({mode:state.mode,input_type:$('#in-type').value,title:$('#in-title').value,text:$('#in-text').value})});
  btn.disabled=false;btn.textContent='Run analysis ▸';
  if(!res){$('#bench-out').innerHTML='<h2 class="disp">Analysis</h2><p class="lede">Backend unreachable. Start it with ./run.sh.</p>';return;}
  state.data.analysis=res;renderBenchOut(res);
}
function renderBenchOut(r){
  const s=r.scores,p=r.parsing;
  $('#bench-out').innerHTML=
    '<div style="display:flex;justify-content:space-between;align-items:flex-start"><h2 class="disp">Analysis</h2>'+stampHtml(r.verification)+'</div>'+
    '<div style="display:flex;gap:34px;align-items:center;margin:18px 0 6px">'+
    '<div class="gauge" style="--p:'+s.opportunity_score+'"><span id="g1">0</span></div><div>'+
    readout(t('opportunity'),'<b style="color:var(--amber)">'+s.opportunity_score+'</b> / 100')+
    readout(t('dd'),s.discovery_delta.toFixed(2),'hi')+readout(t('conf'),s.confidence,'ok')+'</div></div>'+
    readout('Claims parsed',p.claims)+readout('Components parsed',p.components)+
    readout('Constraints detected',p.constraints)+readout('Domains identified',p.domains)+
    '<div class="rule"><span class="lbl">Lineage</span></div><div class="lineage">'+
    r.lineage.map((n,i)=>'<div class="lin-node"><span class="idx">'+String(i+1).padStart(2,'0')+'</span><span class="tag">'+n+'</span></div>'+
      (i<r.lineage.length-1?'<div class="lin-edge"></div>':'')).join('')+'</div>'+
    '<button class="btn" onclick="location.hash=\'#/blueprint\'">Open blueprint &#9656;</button>';
  countUp($('#g1'),s.opportunity_score);requestAnimationFrame(observeReveals);
}
function blueprint(){
  const r=state.data.analysis;
  if(!r){$('#view').innerHTML='<p class="eyebrow">Blueprint</p><h1 class="disp">No analysis yet</h1><p class="lede">Run an analysis in the Workbench first.</p><button class="btn" onclick="location.hash=\'#/\'">Go to Workbench &#9656;</button>';return;}
  const s=r.scores;
  $('#view').innerHTML=
    '<div style="display:flex;justify-content:space-between;align-items:flex-start"><div><p class="eyebrow">Blueprint · '+r.input.title+'</p><h1 class="disp">Build dossier</h1></div>'+stampHtml(r.verification)+'</div>'+
    '<section class="panel reveal" style="margin-top:26px"><div style="display:flex;gap:48px;flex-wrap:wrap;align-items:center">'+
    '<div class="gauge" style="--p:'+s.opportunity_score+'"><span id="g2">0</span></div><div style="flex:1;min-width:260px">'+
    readout(t('opportunity'),'<b style="color:var(--amber)">'+s.opportunity_score+'</b> / 100')+
    readout(t('dd'),s.discovery_delta.toFixed(2),'hi')+readout(t('conf'),s.confidence,'ok')+'</div></div></section>'+
    '<div class="rule"><span class="lbl">'+t('why')+'</span></div><section class="panel reveal"><p style="line-height:1.7">'+r.why_exists+'</p></section>'+
    '<div class="rule"><span class="lbl">'+t('prereq')+'</span></div><section class="panel reveal"><table class="spec"><tbody>'+
    r.prerequisites.map(p=>'<tr><td style="color:var(--cyan)">&#9671;</td><td>'+p+'</td><td><span class="stamp gated">must become true</span></td></tr>').join('')+'</tbody></table></section>'+
    '<div class="rule"><span class="lbl">'+t('risks')+'</span></div><section class="panel reveal"><table class="spec"><thead><tr><th>Risk</th><th>Severity</th></tr></thead><tbody>'+
    r.risks.map(x=>'<tr><td>'+x.risk+'</td><td style="color:var(--amber)">'+x.severity+'</td></tr>').join('')+'</tbody></table></section>'+
    '<div class="rule"><span class="lbl">'+t('rejected')+'</span></div><section class="panel reveal">'+
    r.rejected.map(x=>'<p style="margin-bottom:8px"><span class="stamp rejected">rejected</span><b style="margin-left:10px">'+x.item+'</b></p><p class="mono" style="font-size:12px;color:var(--muted)">'+x.reasons.join(' · ')+'</p>').join('')+'</section>'+
    '<div class="rule"><span class="lbl">'+t('proto')+'</span></div><section class="panel reveal">'+
    readout('Timeline',r.prototype_plan.timeline_weeks+' weeks')+readout('Cost',r.prototype_plan.cost)+
    '<div class="lineage" style="margin-top:14px">'+r.prototype_plan.steps.map((s,i)=>'<div class="lin-node"><span class="idx">'+String(i+1).padStart(2,'0')+'</span><span class="tag">'+s+'</span></div>'+(i<r.prototype_plan.steps.length-1?'<div class="lin-edge"></div>':'')).join('')+'</div></section>';
  countUp($('#g2'),s.opportunity_score);requestAnimationFrame(observeReveals);
}
async function evidence(){
  const r=await api('/evidence')||{};
  const e=r.ledger?r:{ledger:[]};
  $('#view').innerHTML=
    '<div style="display:flex;justify-content:space-between;align-items:flex-start"><div><p class="eyebrow">Evidence · the moat</p><h1 class="disp">Institutional memory</h1>'+
    '<p class="lede">Predictions, analogues, failures, constraint movements, and resurrections — the accumulated record that cannot be replicated.</p></div>'+stampHtml(r.verification)+'</div>'+
    '<div class="rule"><span class="lbl">Prediction ledger</span></div><section class="panel reveal"><table class="spec">'+
    '<thead><tr><th>Type</th><th>Detail</th><th>Validation</th><th>Status</th></tr></thead><tbody>'+
    (e.ledger.map(function(x){
      var es = x.epistemic_status || {};
      var vl = es.validation_level || '—';
      var st = es.status || (x.outcome || 'pending');
      return '<tr><td>'+(x.type||'prediction')+'</td><td style="color:var(--muted)">'+(x.constraint?('constraint '+x.constraint+' &#916;'+x.delta):(x.prediction||''))+'</td><td>'+vl+'</td><td>'+st+'</td></tr>';
    }).join('')||'<tr><td colspan="4">empty</td></tr>')+
    '</tbody></table></section>';
  requestAnimationFrame(observeReveals);
}
async function graph(){
  const g=await api('/graph')||{nodes:[],edges:[]};
  $('#view').innerHTML=
    '<div style="display:flex;justify-content:space-between;align-items:flex-start"><div><p class="eyebrow">Graph explorer · '+(g.source||'specimen')+' substrate</p>'+
    '<h1 class="disp">The evolving substrate</h1><p class="lede">Drag to pan, scroll to zoom, drag nodes to rearrange. Click a node to trace its lineage. Scrub time to replay emergence.</p></div>'+stampHtml(g.verification)+'</div>'+
    '<div class="explorer-wrap reveal"><aside class="exp-controls panel">'+
    '<div class="field"><label>Search</label><input id="gx-search" placeholder="find a node…"/></div>'+
    '<div class="field"><label>Node types</label><div id="gx-types"></div></div>'+
    '<div class="field"><label>Relationship class</label><div id="gx-edges"></div></div>'+
    '<div class="field"><label><input type="checkbox" id="gx-cem" checked style="width:auto"/> Cemetery overlay</label></div>'+
    '<div class="field"><label>Temporal replay — <span id="gx-year" class="mono">2030</span></label>'+
    '<input type="range" id="gx-epoch" min="1850" max="2030" value="2030" step="5"/></div>'+
    '<div id="gx-legend" class="mono"></div></aside>'+
    '<div class="exp-stage"><canvas id="gx-canvas"></canvas><div id="gx-tip" class="gx-tip mono"></div></div>'+
    '<aside class="exp-detail panel" id="gx-detail"><h2 class="disp">Lineage</h2><p class="lede">Select a node.</p></aside></div>';
  const ex=new GraphExplorer($('#gx-canvas'),g,(n,ex)=>renderDetail(n,ex));
  $('#gx-types').innerHTML=Object.keys(TYPE_COLOR).map(t=>'<label style="display:block"><input type="checkbox" checked data-type="'+t+'" style="width:auto"/> <span style="color:'+TYPE_COLOR[t]+'">&#9679;</span> '+t+'</label>').join('');
  $('#gx-types').querySelectorAll('input').forEach(cb=>cb.onchange=()=>ex.toggleType(cb.dataset.type));
  $('#gx-edges').innerHTML=Object.keys(EDGE_COLOR).map(cl=>'<label style="display:block"><input type="checkbox" checked data-edge="'+cl+'" style="width:auto"/> '+cl+'</label>').join('');
  $('#gx-edges').querySelectorAll('input').forEach(cb=>cb.onchange=()=>ex.toggleEdge(cb.dataset.edge));
  $('#gx-cem').onchange=()=>ex.toggleCemetery();
  $('#gx-epoch').oninput=e=>{ex.setEpoch(+e.target.value);$('#gx-year').textContent=e.target.value;};
  $('#gx-search').oninput=e=>ex.setSearch(e.target.value);
  $('#gx-legend').innerHTML=Object.entries(TYPE_COLOR).map(([t,c])=>'<span style="color:'+c+'">&#9679;</span> '+t+'&nbsp;&nbsp;').join('');
  $('#gx-canvas').addEventListener('pointermove',e=>{const n=ex.hover;const tip=$('#gx-tip');
    if(n){tip.style.opacity=1;tip.style.left=(e.offsetX+16)+'px';tip.style.top=(e.offsetY+16)+'px';
      tip.innerHTML='<b>'+n.label+'</b><br/>'+n.type+' · '+n.epoch+(n.is_cemetery?'<br/>&#9888; '+(n.lesson||''):'');}
    else tip.style.opacity=0;});
  requestAnimationFrame(observeReveals);
}
function renderDetail(n,ex){
  const anc=ex._ancestors(n.id).map(id=>ex.byId[id]).filter(Boolean);
  $('#gx-detail').innerHTML=
    '<div style="display:flex;justify-content:space-between;align-items:flex-start"><h2 class="disp">'+n.label+'</h2>'+
    (n.is_cemetery?'<span class="stamp rejected">cemetery</span>':'<span class="stamp gated">'+n.type+'</span>')+'</div>'+
    readout('Domain',n.domain)+readout('Emerged',n.epoch)+
    (n.is_cemetery&&n.lesson?readout('Lesson',n.lesson,'risk'):'')+
    (n.constraints&&n.constraints.length?readout('Binding constraints',n.constraints.join(', '),'hi'):'')+
    '<div class="rule"><span class="lbl">Ancestor lineage</span></div><div class="lineage">'+
    (anc.length?anc.map((a,i)=>'<div class="lin-node"><span class="idx">'+String(i+1).padStart(2,'0')+'</span><span class="tag" style="border-color:'+TYPE_COLOR[a.type]+'">'+a.label+'</span></div>').join(''):'<p class="lede">no ancestors within 4 hops</p>')+'</div>';
}
async function simulate(){
  $('#view').innerHTML=
    '<p class="eyebrow">The Oracle · causal cascade</p>'+
    '<h1 class="disp">If <span id="orc-c-wrap" style="color:var(--amber)">cost</span> moves, what becomes possible?</h1>'+
    '<p class="lede">A constraint movement propagates through prerequisites, cost, lineage, and competition until the system settles into a new equilibrium. Drag the lever — the cascade recomputes.</p>'+
    '<section class="panel reveal" style="margin-top:26px"><div style="display:flex;gap:34px;flex-wrap:wrap;align-items:center">'+
    '<div class="field" style="flex:1;min-width:200px"><label>Constraint</label><select id="orc-c"><option>cost</option><option>energy</option><option>material</option><option>regulation</option><option>manufacturing</option></select></div>'+
    '<div class="field" style="flex:1;min-width:200px"><label>Direction</label><select id="orc-d"><option value="decrease">loosen (unlock)</option><option value="increase">tighten</option></select></div>'+
    '<div class="field" style="flex:2;min-width:260px"><label>Magnitude — <span id="orc-mag" class="mono" style="color:var(--amber)">2x</span></label>'+
    '<input type="range" id="orc-m" min="0" max="2" step="1" value="1" style="width:100%"/></div></div></section>'+
    '<div id="orc-cascade" style="margin-top:34px"><p class="lede">Move the lever to run the cascade.</p></div>';
  const MAGS=['10%','2x','10x'];
  const run=async()=>{const m=MAGS[+$('#orc-m').value];$('#orc-mag').textContent=m;$('#orc-c-wrap').textContent=$('#orc-c').value;
    const r=await api('/simulate',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({constraint:$('#orc-c').value,direction:$('#orc-d').value,magnitude:m})});
    if(r)renderCascade(r);};
  ['orc-c','orc-d'].forEach(id=>$('#'+id).onchange=run);
  $('#orc-m').oninput=run;run();
}
const STAGE_META=[['binding','01 · Binding','which nodes are held by this constraint'],
  ['prerequisites','02 · Prerequisites','what completion eases as a result'],
  ['cost','03 · Cost','how economics propagate up containment'],
  ['lineage','04 · Lineage','which lineages accelerate or stall'],
  ['competition','05 · Competition','who gains, loses, cooperates'],
  ['equilibrium','06 · Equilibrium','the new stable configuration']];
function renderCascade(r){
  const s=r.stages,eq=s.equilibrium;
  const stage=(key,body)=>{const m=STAGE_META.find(x=>x[0]===key);
    return '<section class="panel reveal stage-card" data-stage="'+key+'"><div class="stage-head"><span class="stage-title">'+m[1]+'</span><span class="stage-sub mono">'+m[2]+'</span></div>'+body+'</section>';};
  const traj=eq.trajectory||[];const W=260,H=60;
  const pts=traj.map((t,i)=>((i/Math.max(traj.length-1,1))*W)+','+(H-(t.viable_count/60)*H)).join(' ');
  $('#orc-cascade').innerHTML=
    '<div style="display:flex;justify-content:space-between;align-items:center"><div class="readout" style="flex:1"><span class="k">Net possibility-space</span><span class="leader"></span>'+
    '<span class="v '+(eq.net_possibility_space>=0?'ok':'risk')+'">'+(eq.net_possibility_space>=0?'+':'')+eq.net_possibility_space+' · '+eq.state+'</span></div>'+stampHtml(r.verification)+'</div>'+
    stage('binding','<table class="spec"><thead><tr><th>Node</th><th>Type</th><th>Binding</th><th>Response</th></tr></thead><tbody>'+
      s.binding.nodes.slice(0,8).map(b=>'<tr><td>'+b.label+'</td><td>'+b.type+'</td><td>'+b.binding_share+'</td><td class="'+(b.response>=0?'ok':'risk')+'">'+(b.response>=0?'+':'')+b.response+'</td></tr>').join('')+'</tbody></table>')+
    stage('prerequisites','<table class="spec"><tbody>'+
      (s.prerequisites.movements.slice(0,6).map(p=>'<tr><td>'+p.prerequisite+'</td><td style="color:var(--cyan)">unblocks</td><td>'+p.unblocks+'</td><td class="hi">'+(p.pcs_delta>=0?'+':'')+p.pcs_delta+' PCS</td></tr>').join('')||'<tr><td>none within one hop</td></tr>')+'</tbody></table>')+
    stage('cost','<table class="spec"><tbody>'+
      (s.cost.propagated.slice(0,6).map(c=>'<tr><td>'+c.system+'</td><td style="color:var(--muted)">via '+c.via+'</td><td class="'+(c.cost_delta<=0?'ok':'risk')+'">'+c.cost_delta+' cost</td></tr>').join('')||'<tr><td>no cost propagation</td></tr>')+'</tbody></table>')+
    stage('lineage','<div style="display:flex;gap:12px;flex-wrap:wrap">'+
      s.lineage.lineages.map(l=>'<span class="stamp '+(l.state==='accelerating'?'verified':l.state==='stalling'?'rejected':'gated')+'">'+l.lineage+' '+(l.velocity>=0?'&#8593;':'&#8595;')+' '+l.velocity+'</span>').join('')+'</div>')+
    stage('competition','<table class="spec"><tbody>'+
      s.competition.rivals.slice(0,6).map(rv=>'<tr><td style="color:'+(rv.direction==='displaced'?'var(--coral)':'var(--sage)')+'">'+(rv.direction==='displaced'?'&#9660;':'&#9650;')+' '+rv.rival+'</td><td style="color:var(--muted)">'+rv.kind+' · via '+rv.via_purpose+'</td></tr>').join('')+
      s.competition.cooperators.slice(0,4).map(c=>'<tr><td style="color:var(--cyan)">&#9670; '+c.node+'</td><td style="color:var(--muted)">cooperates via '+c.via+'</td></tr>').join('')+'</tbody></table>')+
    stage('equilibrium','<div style="display:flex;gap:36px;flex-wrap:wrap;align-items:center;margin-bottom:16px"><div>'+
      '<svg width="'+W+'" height="'+H+'" style="background:rgba(255,255,255,.03)"><polyline points="'+pts+'" fill="none" stroke="var(--cyan)" stroke-width="2"/></svg>'+
      '<div class="mono" style="font-size:10px;color:var(--dim);letter-spacing:.14em">VIABLE COUNT · '+eq.iterations+' iterations · '+(eq.converged?'converged':'capped')+'</div></div>'+
      '<div style="flex:1;min-width:240px">'+
      readout('Validation level', (r.epistemic_status ? r.epistemic_status.validation_level : '—')+' <span class="stamp gated" style="margin-left:8px">'+(r.epistemic_status ? r.epistemic_status.status : 'unknown')+'</span>','hi')+
      readout('Evidence strength', r.epistemic_status ? r.epistemic_status.evidence_strength : '—')+
      readout('Experimental validation', r.epistemic_status ? r.epistemic_status.experimental_validation : '—')+
      readout('Net possibility-space',eq.net_possibility_space,eq.net_possibility_space>=0?'ok':'risk')+'</div></div>'+
      (eq.resurrections.length?'<div class="rule"><span class="lbl">Resurrections</span></div>'+eq.resurrections.map(x=>'<p><span class="stamp rejected">&#10013; '+x.label+'</span><span class="mono" style="font-size:12px;color:var(--sage);margin-left:10px">viability '+x.new_viability+(x.lesson?' — '+x.lesson:'')+'</span></p>').join(''):'')+
      (eq.crossings.length?'<div class="rule"><span class="lbl">Viability crossings</span></div>'+eq.crossings.map(x=>'<p><span class="stamp '+(x.direction==='viable'?'verified':'rejected')+'">'+x.direction+'</span><span class="mono" style="font-size:12px;margin-left:10px">'+x.label+' &#8594; '+x.new_viability+'</span></p>').join(''):'')+
      '<div class="rule"><span class="lbl">Falsification (can be wrong on record)</span></div>'+
      r.falsification.map(f=>'<p class="mono" style="font-size:11px;color:var(--dim)">· '+f+'</p>').join('')+
      '<div class="rule"><span class="lbl">Assumptions (Law 6)</span></div>'+
      r.assumptions.map(a=>'<p class="mono" style="font-size:11px;color:var(--dim)">· '+a+'</p>').join(''));
  document.querySelectorAll('.stage-card').forEach((el,i)=>setTimeout(()=>el.classList.add('in'),90*i));
  requestAnimationFrame(observeReveals);
}
const DIMS=[['feasibility',.20],['novelty',.15],['usefulness',.20],['clarity',.10],
  ['historical_accuracy',.10],['prerequisite_accuracy',.15],['blueprint_quality',.10]];
async function benchmarks(){
  const b=await api('/benchmarks')||{};
  const base={feasibility:.62,novelty:.55,usefulness:.60,clarity:.68,historical_accuracy:.50,prerequisite_accuracy:.58,blueprint_quality:.64};
  $('#view').innerHTML=
    '<div style="display:flex;justify-content:space-between;align-items:flex-start"><div><p class="eyebrow">Calibration bench · an instrument, not a dashboard</p>'+
    '<h1 class="disp">What happens if we<br/>improve <span id="cb-bind" style="color:var(--amber)">—</span>?</h1>'+
    '<p class="lede">Drag any dimension. The composite recomputes live and the binding dimension is identified. This is how the institution decides where to invest next.</p></div>'+stampHtml(b.verification)+'</div>'+
    '<div class="bench"><section class="panel reveal"><h2 class="disp">Levers</h2><div id="cb-levers"></div></section>'+
    '<section class="panel reveal"><h2 class="disp">Response</h2>'+
    '<div style="display:flex;gap:36px;align-items:center;margin:16px 0"><div class="gauge" id="cb-gauge" style="--p:0"><span id="cb-score">0</span></div>'+
    '<div style="flex:1">'+readout('Composite','<span id="cb-comp">—</span>','hi')+
    readout('&#916; from baseline','<span id="cb-delta">—</span>')+
    readout('Binding dimension','<span id="cb-binding">—</span>','risk')+'</div></div><div id="cb-bars"></div></section></div>';
  const cur=Object.assign({},base);
  const baseline=DIMS.reduce((s,d)=>s+base[d[0]]*d[1],0);
  $('#cb-levers').innerHTML=DIMS.map(d=>'<div class="field"><label>'+d[0].replace(/_/g,' ')+' · weight '+(d[1]*100).toFixed(0)+'%</label>'+
    '<input type="range" data-dim="'+d[0]+'" min="0" max="100" value="'+Math.round(base[d[0]]*100)+'" style="width:100%"/></div>').join('');
  function composite(v){return DIMS.reduce((s,d)=>s+v[d[0]]*d[1],0);}
  function render(){
    const c=composite(cur);
    const bind=DIMS.map(d=>[d[0],cur[d[0]]*d[1]]).sort((a,b)=>a[1]-b[1])[0][0];
    $('#cb-score').textContent=Math.round(c*100);
    $('#cb-gauge').style.setProperty('--p',Math.round(c*100));
    $('#cb-comp').textContent=c.toFixed(3);
    const d=c-baseline;
    $('#cb-delta').textContent=(d>=0?'+':'')+d.toFixed(3);
    $('#cb-delta').style.color=d>=0?'var(--sage)':'var(--coral)';
    $('#cb-binding').textContent=bind.replace(/_/g,' ');
    $('#cb-bind').textContent=bind.replace(/_/g,' ');
    $('#cb-bars').innerHTML=DIMS.map(d=>'<div class="readout"><span class="k">'+d[0].replace(/_/g,' ')+'</span><span class="leader"></span>'+
      '<span style="flex:0 0 140px;height:6px;background:rgba(255,255,255,.06);position:relative">'+
      '<span style="position:absolute;inset:0;width:'+(cur[d[0]]*100)+'%;background:'+(d[0]===bind?'var(--coral)':'var(--cyan)')+';transition:width .3s"></span></span></div>').join('');
  }
  document.querySelectorAll('#cb-levers input').forEach(inp=>inp.oninput=()=>{cur[inp.dataset.dim]=inp.value/100;render();});
  render();requestAnimationFrame(observeReveals);
}
boot();
