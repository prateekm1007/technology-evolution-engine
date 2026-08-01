
/* TEE Graph Explorer — canvas force-directed graph with LOD. */
const TYPE_COLOR = {domain:'#5fe0cd',principle:'#ffb454',process:'#a8d08d',component:'#7fb3ff',
  system:'#ff8f6b',industry:'#c0c8d8',cemetery:'#ff6f61'};
const EDGE_COLOR = {structural:'rgba(95,224,205,.35)',functional:'rgba(255,180,84,.35)',historical:'rgba(255,111,97,.4)'};

class GraphExplorer {
  constructor(canvas, data, onSelect){
    this.cv=canvas;this.ctx=canvas.getContext('2d');this.data=data;this.onSelect=onSelect;
    this.t={x:0,y:0,k:1};this.alpha=1;this.hover=null;this.selected=null;this.lineage=new Set();
    this.show={types:new Set(Object.keys(TYPE_COLOR)),edges:new Set(Object.keys(EDGE_COLOR)),cemetery:true};
    this.epoch=data.epochs?data.epochs[1]:2030;this.search='';
    this._seed();this._bind();this._loop();
  }
  _seed(){
    const W=this.cv.width=this.cv.offsetWidth*devicePixelRatio;
    const H=this.cv.height=this.cv.offsetHeight*devicePixelRatio;
    this.W=W;this.H=H;
    const domains=[...new Set(this.data.nodes.map(n=>n.domain))];
    this.centers={};
    domains.forEach((d,i)=>{const a=(i/domains.length)*Math.PI*2;
      this.centers[d]={x:W/2+Math.cos(a)*Math.min(W,H)*0.32,y:H/2+Math.sin(a)*Math.min(W,H)*0.32};});
    const rng=mulberry(7);
    this.data.nodes.forEach(n=>{const c=this.centers[n.domain]||{x:W/2,y:H/2};
      n.x=c.x+(rng()-.5)*120;n.y=c.y+(rng()-.5)*120;n.vx=0;n.vy=0;
      n.r=n.type==='domain'?9:n.is_cemetery?7:5;});
    this.byId={};this.data.nodes.forEach(n=>this.byId[n.id]=n);
    this.adj={};
    this.data.edges.forEach(e=>{(this.adj[e.source]||=[]).push(e.target);(this.adj[e.target]||=[]).push(e.source);});
  }
  _bind(){
    const cv=this.cv;
    cv.addEventListener('wheel',e=>{e.preventDefault();
      const f=e.deltaY<0?1.12:1/1.12;const r=cv.getBoundingClientRect();
      const mx=(e.clientX-r.left)*devicePixelRatio,my=(e.clientY-r.top)*devicePixelRatio;
      this.t.x=mx-(mx-this.t.x)*f;this.t.y=my-(my-this.t.y)*f;this.t.k*=f;},{passive:false});
    let drag=null;
    cv.addEventListener('pointerdown',e=>{const p=this._toWorld(e);const n=this._pick(p);
      drag=n?{node:n}:{pan:true,x:e.clientX,y:e.clientY};if(n)n.fixed=true;});
    cv.addEventListener('pointermove',e=>{const p=this._toWorld(e);
      if(drag&&drag.node){drag.node.x=p.x;drag.node.y=p.y;drag.node.vx=drag.node.vy=0;this.alpha=Math.max(this.alpha,.3);}
      else if(drag&&drag.pan){this.t.x+=(e.clientX-drag.x)*devicePixelRatio;this.t.y+=(e.clientY-drag.y)*devicePixelRatio;drag.x=e.clientX;drag.y=e.clientY;}
      else{this.hover=this._pick(p);cv.style.cursor=this.hover?'pointer':'grab';}});
    cv.addEventListener('pointerup',()=>{if(drag&&drag.node){drag.node.fixed=false;this._select(drag.node);}drag=null;});
  }
  _toWorld(e){const r=this.cv.getBoundingClientRect();
    return{x:((e.clientX-r.left)*devicePixelRatio-this.t.x)/this.t.k,
           y:((e.clientY-r.top)*devicePixelRatio-this.t.y)/this.t.k};}
  _pick(p){for(let i=this.data.nodes.length-1;i>=0;i--){const n=this.data.nodes[i];
    if(!this._visible(n))continue;const dx=n.x-p.x,dy=n.y-p.y;if(dx*dx+dy*dy<(n.r+4)*(n.r+4))return n;}return null;}
  _visible(n){return this.show.types.has(n.type)&&n.epoch<=this.epoch&&(this.show.cemetery||!n.is_cemetery);}
  _isLod(n){if(this.t.k>=0.6)return true;
    return n.type==='domain'||n.is_cemetery||(this.selected&&(n.id===this.selected.id||(this.adj[this.selected.id]||[]).includes(n.id)));}
  _select(n){this.selected=n;this.lineage=new Set([n.id]);
    this._ancestors(n.id).forEach(id=>this.lineage.add(id));this.onSelect&&this.onSelect(n,this);}
  _ancestors(id,depth=4){const seen=new Set();let frontier=[id];
    for(let d=0;d<depth;d++){const nxt=[];for(const cur of frontier){
      for(const e of this.data.edges){if(e.target===cur&&!seen.has(e.source)){seen.add(e.source);nxt.push(e.source);}}}frontier=nxt;}
    return[...seen];}
  _tick(){
    if(this.alpha<0.005)return;const N=this.data.nodes;
    for(let i=0;i<N.length;i++){const a=N[i];
      for(let j=i+1;j<N.length;j++){const b=N[j];
        let dx=a.x-b.x,dy=a.y-b.y,d2=dx*dx+dy*dy;if(d2<1)d2=1;if(d2>90000)continue;
        const f=900/d2,d=Math.sqrt(d2);dx/=d;dy/=d;
        a.vx+=dx*f;a.vy+=dy*f;b.vx-=dx*f;b.vy-=dy*f;}}
    for(const e of this.data.edges){const a=this.byId[e.source],b=this.byId[e.target];
      if(!a||!b)continue;let dx=b.x-a.x,dy=b.y-a.y,d=Math.sqrt(dx*dx+dy*dy)||1;
      const f=(d-70)*0.004;dx/=d;dy/=d;a.vx+=dx*f;a.vy+=dy*f;b.vx-=dx*f;b.vy-=dy*f;}
    for(const n of N){const c=this.centers[n.domain];
      if(c){n.vx+=(c.x-n.x)*0.003;n.vy+=(c.y-n.y)*0.003;}
      if(!n.fixed){n.x+=n.vx*this.alpha;n.y+=n.vy*this.alpha;}n.vx*=0.85;n.vy*=0.85;}
    this.alpha*=0.995;
  }
  _draw(){
    const c=this.ctx;c.setTransform(1,0,0,1,0,0);c.clearRect(0,0,this.W,this.H);
    c.setTransform(this.t.k,0,0,this.t.k,this.t.x,this.t.y);
    const focus=this.hover||this.selected;
    for(const e of this.data.edges){if(!this.show.edges.has(e.class))continue;
      const a=this.byId[e.source],b=this.byId[e.target];
      if(!a||!b||!this._visible(a)||!this._visible(b)||!this._isLod(a)||!this._isLod(b))continue;
      let col=EDGE_COLOR[e.class];
      if(focus&&a.id!==focus.id&&b.id!==focus.id&&!this.lineage.has(a.id)&&!this.lineage.has(b.id))col='rgba(120,140,140,.05)';
      if(this.lineage.has(a.id)&&this.lineage.has(b.id))col='rgba(255,180,84,.8)';
      c.strokeStyle=col;c.lineWidth=1/this.t.k;
      if(e.class==='historical')c.setLineDash([4/this.t.k,4/this.t.k]);else c.setLineDash([]);
      c.beginPath();c.moveTo(a.x,a.y);c.lineTo(b.x,b.y);c.stroke();}
    c.setLineDash([]);
    for(const n of this.data.nodes){if(!this._visible(n)||!this._isLod(n))continue;
      const dim=focus&&n.id!==focus.id&&!(this.adj[focus.id]||[]).includes(n.id)&&!this.lineage.has(n.id);
      const matched=this.search&&n.label.toLowerCase().includes(this.search);
      c.globalAlpha=dim?0.12:1;c.beginPath();c.arc(n.x,n.y,n.r,0,Math.PI*2);
      if(n.is_cemetery){c.strokeStyle=TYPE_COLOR.cemetery;c.lineWidth=1.5/this.t.k;c.stroke();
        c.beginPath();c.moveTo(n.x-n.r,n.y-n.r);c.lineTo(n.x+n.r,n.y+n.r);
        c.moveTo(n.x+n.r,n.y-n.r);c.lineTo(n.x-n.r,n.y+n.r);c.stroke();}
      else{c.fillStyle=TYPE_COLOR[n.type];c.fill();}
      if(matched){c.strokeStyle='#ffb454';c.lineWidth=2/this.t.k;c.beginPath();c.arc(n.x,n.y,n.r+4,0,Math.PI*2);c.stroke();}
      if(n===this.hover||this.lineage.has(n.id)){c.strokeStyle='#f2efe6';c.lineWidth=1.5/this.t.k;
        c.beginPath();c.arc(n.x,n.y,n.r+2.5,0,Math.PI*2);c.stroke();}
      c.globalAlpha=1;}
  }
  _loop(){this._tick();this._draw();requestAnimationFrame(()=>this._loop());}
  toggleType(t){this.show.types.has(t)?this.show.types.delete(t):this.show.types.add(t);}
  toggleEdge(cl){this.show.edges.has(cl)?this.show.edges.delete(cl):this.show.edges.add(cl);}
  toggleCemetery(){this.show.cemetery=!this.show.cemetery;}
  setEpoch(y){this.epoch=y;}
  setSearch(s){this.search=(s||'').toLowerCase();}
  reheat(){this.alpha=1;}
}
function mulberry(seed){return function(){seed|=0;seed=seed+0x6D2B79F5|0;
  let t=Math.imul(seed^seed>>>15,1|seed);t=t+Math.imul(t^t>>>7,61|t)^t;
  return((t^t>>>14)>>>0)/4294967296;};}
