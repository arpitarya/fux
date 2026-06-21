// Fux graph — Solar Terminal viewer. Vanilla canvas, offline, dependency-free.
// Code desaturates to graphite dust; knowledge nodes ignite incandescent amber;
// the precious `governs` edges stream across as glowing threads.
const cv = document.getElementById("cv"), ctx = cv.getContext("2d");
const tip = document.getElementById("tip"), $ = id => document.getElementById(id);
const esc = s => String(s).replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
let DPR = Math.max(1, Math.min(2, window.devicePixelRatio || 1));

const nodes = DATA.nodes.map(n => ({ ...n, x: Math.random()*900-450, y: Math.random()*900-450, vx:0, vy:0 }));
const byId = Object.fromEntries(nodes.map(n => [n.id, n]));
const edges = DATA.edges.filter(e => byId[e.source] && byId[e.target]);
const deg = {}; edges.forEach(e => { deg[e.source]=(deg[e.source]||0)+1; deg[e.target]=(deg[e.target]||0)+1; });
const maxDeg = Math.max(1, ...Object.values(deg));
const maxC = Math.max(1e-9, ...nodes.map(n => n.centrality||0));
const adj = {}; nodes.forEach(n => adj[n.id] = []);
edges.forEach(e => { adj[e.source].push([e.target,e,1]); adj[e.target].push([e.source,e,-1]); });

const KNOWLEDGE = new Set(["rule","formula","glossary","invariant","adr","edge-case",
  "convention","regulatory","runbook","narrative","memory","spec","task"]);
const isKnow = n => KNOWLEDGE.has(n.type);
const knowHue = t => (t==="invariant"||t==="regulatory"||t==="contradicts") ? 12
  : (t==="adr"||t==="formula"||t==="glossary"||t==="spec") ? 44 : 32;

// Per-community rollup + inter-community weights (semantic-zoom macro view).
const comm = {};
for (const n of nodes){ const c = comm[n.community] || (comm[n.community]={size:0,top:n,members:[],know:0});
  c.size++; c.members.push(n.id); if(isKnow(n)) c.know++; if((n.centrality||0) > (c.top.centrality||0)) c.top = n; }
const godThresh = [...nodes].sort((a,b)=>(b.centrality||0)-(a.centrality||0))
  [Math.max(0, Math.floor(nodes.length*0.015)-1)]?.centrality ?? maxC;
const isGod = n => (n.centrality||0) >= godThresh;

// Governance: which knowledge nodes link to which code nodes, and how.
// `governedCode` is the set of code-node ids that any knowledge node touches —
// the warm side of the Coverage lens (everything else is ungoverned, cold-grey).
const govTargets = {};
const governedCode = new Set();
let governsCount = 0;
for (const e of edges){ const a=byId[e.source], b=byId[e.target];
  if(e.type==="governs") governsCount++;
  let kn=null, other=null;
  if(isKnow(a) && !isKnow(b)){ kn=a; other=b; }
  else if(isKnow(b) && !isKnow(a)){ kn=b; other=a; }
  else continue;
  if(e.type==="governs" || e.type==="related" || e.type==="references" || e.type==="implements"){
    (govTargets[kn.id]=govTargets[kn.id]||[]).push({id:other.id, type:e.type});
    governedCode.add(other.id); } }
const isGoverned = id => governedCode.has(id);

let view = { x: 0, y: 0, k: 1 }, hidden = new Set(), hiddenE = new Set();
let vTarget = null;           // when set, the camera eases toward it (smooth zoom/fly)
const VIEW_EASE = 0.2;        // per-frame approach fraction toward vTarget
let selected = null, hover = null, query = "", lens = "know";
let running = true, showLabels = true, focusSet = null;
let pathMode = false, pathA = null, pathSet = null, pathEdge = new Set(), pathMD = null;
let linkDist = 70, charge = 900;
// Simulated-annealing cooling: forces scale with `alpha`, which decays every
// physics tick. Once it bottoms out the layout has settled and the sim stops, so
// the graph holds still. Interactions that change the layout call reheat().
let alpha = 1;
const ALPHA_MIN = 0.004, ALPHA_DECAY = 0.98, ALPHA_REHEAT = 0.55;
function reheat(a){ alpha = Math.max(alpha, a==null ? ALPHA_REHEAT : a); running = true; }
const REP = nodes.length > 1200 ? 0.020 : 0.032;
const REP_RANGE = 420, GRAVITY = 0.0014, COMM_PULL = 0.028;
// Community palette: the Tableau-10 categorical set (as used by Graphify) — cool,
// distinct and cohesive on near-black. Three shade tiers extend the 10 colours so
// neighbouring communities still separate across 100+ clusters. Knowledge nodes
// stay incandescent amber regardless, so they still read as the special layer.
const TABLEAU = ["#4E79A7","#F28E2B","#E15759","#76B7B2","#59A14F",
                 "#EDC948","#B07AA1","#FF9DA7","#9C755F","#BAB0AC"];
function shade(hex, pct){ const n=parseInt(hex.slice(1),16); const f=pct<0?0:255, p=Math.abs(pct)/100;
  const r=Math.round((f-(n>>16))*p)+(n>>16), g=Math.round((f-((n>>8)&255))*p)+((n>>8)&255), b=Math.round((f-(n&255))*p)+(n&255);
  return `rgb(${r},${g},${b})`; }
function ccolor(c){ c=c||0; const base=TABLEAU[c % TABLEAU.length], tier=Math.floor(c/TABLEAU.length)%3;
  return tier===0 ? base : shade(base, tier===1 ? -22 : 20); }
const heat = d => { const t = (deg[d]||0)/maxDeg; return `hsl(${28+t*16},${40+t*55}%,${42+t*22}%)`; };
function codeFill(n){ if(lens==="community") return ccolor(n.community); if(lens==="heat") return heat(n.id);
  if(lens==="coverage") return isGoverned(n.id)            // warm = governed, cold-grey = not
    ? "hsl(33 90% " + (52 + (n.centrality||0)*22) + "%)"
    : "hsl(214 6% " + (30 + (n.centrality||0)*16) + "%)";
  return "hsl(214 10% " + (44 + (n.centrality||0)*30) + "%)"; }

// ---- pre-rendered glow sprites (built ONCE; drawImage'd in the hot path) -----
// The amber knowledge-node glow used to allocate a fresh radialGradient per node
// per frame (GC churn + a slow fill). Instead bake one sprite per knowledge hue at
// a fixed radius and scale it on draw. Same radial amber falloff, no per-frame alloc.
const GLOW_R = 64;                     // sprite half-extent in px (high enough to scale up cleanly)
const _glowSprite = {};                // hue → offscreen canvas
function glowSprite(hue){ let c = _glowSprite[hue]; if(c) return c;
  c = document.createElement("canvas"); c.width = c.height = GLOW_R*2;
  const g = c.getContext("2d"); const grd = g.createRadialGradient(GLOW_R,GLOW_R,0,GLOW_R,GLOW_R,GLOW_R);
  grd.addColorStop(0,"hsla("+hue+",100%,70%,0.5)"); grd.addColorStop(1,"hsla("+hue+",100%,60%,0)");
  g.fillStyle = grd; g.beginPath(); g.arc(GLOW_R,GLOW_R,GLOW_R,0,6.2832); g.fill();
  _glowSprite[hue] = c; return c; }

// ---- static code-substrate cache (offscreen) -----------------------------
// The faint contains/references/calls layer is the heaviest set of strokes but is
// static once the layout settles. We render it to an offscreen canvas once and blit
// it every frame; it's re-rendered only when the layout, camera, or filters change
// (tracked via _substrateDirty + a camera snapshot). invalidateVis() also dirties it.
let _subCv = null, _subCtx = null, _substrateDirty = true, _subView = {x:NaN,y:NaN,k:NaN};

// ---- header counts + per-type meters + edge legend (all from real data) ----
const fmt = n => n.toLocaleString("en-US");
const typeCounts = {}; nodes.forEach(n => typeCounts[n.type]=(typeCounts[n.type]||0)+1);
const edgeCounts = {}; edges.forEach(e => edgeCounts[e.type]=(edgeCounts[e.type]||0)+1);
const nComm = Object.keys(comm).length;
$("stats").textContent = `${fmt(nodes.length)} nodes · ${fmt(edges.length)} edges · ${nComm} communities`;
$("st-nodes").textContent = fmt(nodes.length);
$("st-edges").textContent = fmt(edges.length);
$("st-gov").textContent = governsCount;
$("mp-comm").textContent = nComm;
$("lens-comm").textContent = nComm;
$("ov-cnt").textContent = fmt(nodes.length) + " nodes";
$("led-frac").textContent = governsCount + " of " + fmt(edges.length);
// Coverage lens subtitle: how much of the code layer any rule actually touches.
const codeTotal = nodes.reduce((a,n)=> a + (isKnow(n)?0:1), 0);
$("lens-cov").textContent = fmt(governedCode.size) + " of " + fmt(codeTotal);

const tOrder = Object.keys(typeCounts).sort((a,b)=>{
  const ka=KNOWLEDGE.has(a), kb=KNOWLEDGE.has(b);
  if(ka!==kb) return ka?1:-1;            // code types first, knowledge last
  return typeCounts[b]-typeCounts[a]; });
const maxType = Math.max(...Object.values(typeCounts));
$("filters").innerHTML = tOrder.map(t => { const know = KNOWLEDGE.has(t);
  const c = know ? "hsl("+knowHue(t)+" 100% 66%)" : color(t);
  const glow = know ? `;box-shadow:0 0 8px ${c}` : "";
  return `<div class="meter${know?" know":""}"><input type="checkbox" data-t="${t}" checked hidden>`+
    `<span class="sw" style="background:${c}${glow}"></span>`+
    `<span class="nm">${t}${know?' <span class="pill-mini">knowledge</span>':''}</span>`+
    `<span class="bar"><i style="width:${Math.max(4,typeCounts[t]/maxType*100)}%;background:${c}"></i></span>`+
    `<span class="ct">${fmt(typeCounts[t])}</span></div>`; }).join("");
document.querySelectorAll("#filters .meter").forEach(row => { const cb=row.querySelector("input");
  row.onclick = () => { cb.checked=!cb.checked; cb.checked ? hidden.delete(cb.dataset.t) : hidden.add(cb.dataset.t);
    row.classList.toggle("off",!cb.checked); invalidateVis(); }; });   // hide/show never re-lays-out

const EDGE_LABEL = {governs:"governs",calls:"calls",references:"references",contains:"contains",
  related:"related",supersedes:"supersedes",implements:"implements","depends-on":"depends-on",contradicts:"contradicts"};
const eOrder = Object.keys(edgeCounts).sort((a,b)=>{
  const pa=a==="governs"?0:1, pb=b==="governs"?0:1; if(pa!==pb) return pa-pb; return edgeCounts[b]-edgeCounts[a]; });
$("efilters").innerHTML = eOrder.map(t => { const amber = (t==="governs");
  const styl = t==="references" ? "border-top:1px dashed "+edgeColor(t)
    : t==="contains" ? "border-top:1px solid "+edgeColor(t)
    : "border-top:"+(amber?"2px":"1.5px")+" solid "+edgeColor(t)+(amber?";box-shadow:0 0 6px "+edgeColor(t):"");
  return `<div class="lg-row" data-e="${t}"><span class="ln" style="${styl}"></span>`+
    `<b class="${amber?"amb":""}">${EDGE_LABEL[t]||t}</b><span class="ct">${fmt(edgeCounts[t])}</span></div>`; }).join("");
document.querySelectorAll("#efilters .lg-row").forEach(row => { const t=row.dataset.e;
  row.onclick = () => { hiddenE.has(t) ? hiddenE.delete(t) : hiddenE.add(t); row.classList.toggle("off",hiddenE.has(t)); invalidateVis(); }; });

$("ntoggle").onclick = $("ntoggle2").onclick = () => { const rows=[...document.querySelectorAll("#filters .meter")];
  const any=rows.some(r=>r.querySelector("input").checked);
  rows.forEach(r=>{ const cb=r.querySelector("input"); cb.checked=!any;
    !any ? hidden.delete(cb.dataset.t) : hidden.add(cb.dataset.t); r.classList.toggle("off",any); }); invalidateVis(); };

// ---- lens grid (Knowledge / Communities / Heat / Path) ----
function setLens(name){ if(name==="path"){ togglePath(); return; }
  lens = name;
  document.querySelectorAll("#lensgrid .lens").forEach(c => c.classList.toggle("on", c.dataset.lens===name)); }
document.querySelectorAll("#lensgrid .lens").forEach(c => c.onclick = () => setLens(c.dataset.lens));

// ---- search → clickable hit list ----
$("q").oninput = e => { query = e.target.value.toLowerCase(); updateHits(); };
const match = n => query && (n.label.toLowerCase().includes(query) || n.id.toLowerCase().includes(query));
function updateHits(){ if(!query){ $("qhits").innerHTML=""; return; }
  const m = nodes.filter(match);
  $("qhits").innerHTML = m.slice(0,14).map(n => { const c = isKnow(n) ? "hsl("+knowHue(n.type)+" 100% 66%)" : codeFill(n);
    return `<div class="hit" data-jump="${esc(n.id)}" title="${esc(n.id)}"><span class="sw" style="background:${c}"></span>`+
      `<span class="hl">${esc(n.label)}</span><span class="ct">${n.type}</span></div>`; }).join("")
    + (m.length>14 ? `<div class="ct" style="padding:5px 7px">+${m.length-14} more</div>` : "");
  $("qhits").querySelectorAll("[data-jump]").forEach(el => el.onclick = () => jumpTo(el.dataset.jump)); }
function jumpTo(id){ const n=byId[id]; if(!n) return; selected=id; clearPath(); showDetail(n);
  const k=Math.max(view.k,1); flyTo(-n.x*k, -n.y*k, k); }

// ---- copy / governance footer buttons ----
$("bcopy").onclick = () => { if(pathSet && pathMD) copy(pathMD(), "path copied");
  else if(selected) copy(nodeMarkdown(byId[selected]), "node copied"); };
$("bexport").onclick = () => copy(graphMarkdown(), "visible subgraph copied");
$("bgov").onclick = () => copy(governedMarkdown(), "governed subgraph copied");
$("bopen").onclick = () => toggleLens();
$("ledhead").onclick = () => $("led").classList.toggle("collapsed");
function applyRightState(){ const collapsed = $("right").classList.contains("collapsed");
  $("railtab").textContent = collapsed ? "‹" : "›";
  $("floatmm").style.display = collapsed ? "block" : "none"; }
$("railtab").onclick = () => { $("right").classList.toggle("collapsed"); applyRightState(); setTimeout(resize, 200); };
applyRightState();   // honour the default-collapsed markup on load
// Micro / Macro both show the real nodes — they just change zoom. Micro zooms in
// (centred on the selection if any); Macro fits the whole graph as an overview.
$("bmicro").onclick = () => { focusSet=null; invalidateVis(); const z=Math.max(view.k,1.3); const p=selected&&byId[selected];
  if(p) flyTo(-p.x*z, -p.y*z, z); else zoomToCenter(z); };
// Macro = the auto-framed overview; re-enable auto-fit so it stays framed on resize.
$("bmacro").onclick = () => { focusSet=null; invalidateVis(); userMoved=false; query=""; $("q").value=""; updateHits(); clearPath(); fitAnimated(); };

// ---- layout & geometry --------------------------------------------------
let W=0, H=0;
function resize(){ const st=cv.parentElement; W=st.clientWidth; H=st.clientHeight;
  cv.width=Math.max(1,W*DPR); cv.height=Math.max(1,H*DPR); ctx.setTransform(DPR,0,0,DPR,0,0); }
// The stage's real size often isn't known at first script run (fonts/flex still
// settling, or the tab is backgrounded), so the initial fit framed to the wrong
// size and stayed cut off until a manual resize. Re-frame (resize + fit) on first
// paint, tab-visibility and resize — but only until the user pans/zooms.
let userMoved = false;
function reframe(){ resize(); if(!userMoved) fit(); }
resize(); window.addEventListener("resize", reframe);   // initial fit happens at the end
if(window.ResizeObserver) new ResizeObserver(reframe).observe(cv.parentElement);
window.addEventListener("load", reframe);
document.addEventListener("visibilitychange", () => { if(!document.hidden) reframe(); });
window.addEventListener("pageshow", reframe);
requestAnimationFrame(reframe);
const inFocus = n => !focusSet || focusSet.has(n.id);
const visible = n => !hidden.has(n.type) && inFocus(n);
const eVisible = e => !hiddenE.has(e.type) && visible(byId[e.source]) && visible(byId[e.target]);
const ekey = e => e.source+" "+e.target;
const PHYS_STRIDE = nodes.length > 600 ? 2 : 1;
let _f = 0;
// Cached visible-node list — `visible(n)` only changes when a type filter or the
// focus set toggles, so we rebuild lazily on invalidateVis() instead of every
// step()/draw(). Anything that mutates `hidden`/`focusSet` must call invalidateVis().
let _visList = null, _visEdges = null;
function invalidateVis(){ _visList = null; _visEdges = null; _substrateDirty = true; }
function visList(){ if(!_visList) _visList = nodes.filter(visible); return _visList; }
function visEdges(){ if(!_visEdges) _visEdges = edges.filter(eVisible); return _visEdges; }

function communityCentroids(){ const cc = {};
  for (const n of visList()){
    const c = cc[n.community] || (cc[n.community]={x:0,y:0,n:0}); c.x+=n.x; c.y+=n.y; c.n++; }
  for (const k in cc){ cc[k].x/=cc[k].n; cc[k].y/=cc[k].n; } return cc; }

// ---- Barnes–Hut quadtree : O(n log n) repulsion (replaces the O(n²) pair loop).
// A far cell is approximated as a single charge at its centre-of-mass when
// size/distance < THETA. The original force law and REP_RANGE cutoff are preserved
// exactly, so the settled layout is indistinguishable from the O(n²) one.
// Layout in flat parallel arrays (reused across frames, grown as needed) keyed by
// quadtree-node index: each node is a leaf holding one body, or an internal node
// with up to four children (c0..c3 = -1 when absent). reg* = the node's region.
const BH_THETA = 0.8, BH_THETA2 = BH_THETA*BH_THETA, REP_RANGE2 = REP_RANGE*REP_RANGE;
let _bh = { mass:null, comX:null, comY:null, size:null, bx:null, by:null,
            c0:null, c1:null, c2:null, c3:null, regX:null, regY:null, regH:null, cap:0 };
function _bhGrow(cap){ if(_bh.cap>=cap) return; const n=Math.max(cap, _bh.cap*2, 256), F=Float64Array, I=Int32Array;
  _bh.mass=new F(n); _bh.comX=new F(n); _bh.comY=new F(n); _bh.size=new F(n);
  _bh.bx=new F(n); _bh.by=new F(n); _bh.regX=new F(n); _bh.regY=new F(n); _bh.regH=new F(n);
  _bh.c0=new I(n); _bh.c1=new I(n); _bh.c2=new I(n); _bh.c3=new I(n); _bh.cap=n; }
function buildBH(vis){
  let minX=1e18,minY=1e18,maxX=-1e18,maxY=-1e18;
  for(const a of vis){ if(a.x<minX)minX=a.x; if(a.x>maxX)maxX=a.x; if(a.y<minY)minY=a.y; if(a.y>maxY)maxY=a.y; }
  if(!isFinite(minX)) return false;
  _bhGrow(vis.length*2 + 16);
  const b=_bh;
  let nextFree = 0;                                   // bump allocator over the arrays
  const alloc = (rx,ry,rh) => { const i=nextFree++; b.mass[i]=0; b.bx[i]=NaN;
    b.c0[i]=b.c1[i]=b.c2[i]=b.c3[i]=-1; b.size[i]=rh*2; b.regX[i]=rx; b.regY[i]=ry; b.regH[i]=rh; return i; };
  const childAt = (i,q) => q===0?b.c0[i] : q===1?b.c1[i] : q===2?b.c2[i] : b.c3[i];
  const setChild = (i,q,v) => { if(q===0)b.c0[i]=v; else if(q===1)b.c1[i]=v; else if(q===2)b.c2[i]=v; else b.c3[i]=v; };
  const cx=(minX+maxX)/2, cy=(minY+maxY)/2, half=Math.max(maxX-minX, maxY-minY, 1)/2 + 1;
  const root = alloc(cx, cy, half);
  const descend = (i,q) => { let ci=childAt(i,q); if(ci<0){ const nh=b.regH[i]/2;
      ci=alloc(b.regX[i]+(q&1?nh:-nh), b.regY[i]+(q&2?nh:-nh), nh); setChild(i,q,ci); } return ci; };
  for(const a of vis){ let i=root, px=a.x, py=a.y;
    for(let depth=0; depth<64; depth++){
      if(b.mass[i]===0){ b.bx[i]=px; b.by[i]=py; b.mass[i]=1; break; }   // empty leaf → place here
      if(b.bx[i]===b.bx[i]){                                            // occupied leaf → split, push old body down
        const ox=b.bx[i], oy=b.by[i]; b.bx[i]=NaN;
        const oq=(ox>=b.regX[i]?1:0)+(oy>=b.regY[i]?2:0); const oc=descend(i,oq);
        b.bx[oc]=ox; b.by[oc]=oy; b.mass[oc]=1; }
      b.mass[i]++;                                                      // internal node accrues count; descend
      i = descend(i, (px>=b.regX[i]?1:0)+(py>=b.regY[i]?2:0)); } }
  _bhCom(root); _bh.root = root; return true;
}
// Post-order roll-up of mass-weighted centre-of-mass for every internal node.
function _bhCom(i){ const b=_bh;
  if(b.bx[i]===b.bx[i]){ b.comX[i]=b.bx[i]; b.comY[i]=b.by[i]; return; }   // leaf body
  let sx=0, sy=0;
  for(const ci of [b.c0[i],b.c1[i],b.c2[i],b.c3[i]]){ if(ci<0) continue;
    _bhCom(ci); sx+=b.comX[ci]*b.mass[ci]; sy+=b.comY[ci]*b.mass[ci]; }
  if(b.mass[i]>0){ b.comX[i]=sx/b.mass[i]; b.comY[i]=sy/b.mass[i]; } }
// Repulsion on body a: descend the tree, approximating far cells as a single charge.
// Same force law + REP_RANGE cutoff as the O(n²) loop, scaled by the cell's body count.
const _bhStack = new Int32Array(4096);
function bhForce(a){ const b=_bh; let fx=0, fy=0, sp=0; _bhStack[sp++]=b.root;
  while(sp){ const i=_bhStack[--sp]; const m=b.mass[i]; if(m===0) continue;
    let dx=a.x-b.comX[i], dy=a.y-b.comY[i]; let d2=dx*dx+dy*dy;
    const leaf=(b.c0[i]<0 && b.c1[i]<0 && b.c2[i]<0 && b.c3[i]<0);
    if(leaf || b.size[i]*b.size[i] < BH_THETA2*d2){     // single body, or far enough to approximate
      if(d2===0) continue;                              // self / coincident — no force (matches d||1 no-op)
      if(d2 < REP_RANGE2){ if(d2<1) d2=1;               // identical force law, ×mass for an aggregated cell
        const f=charge*REP/d2*alpha*m; fx+=dx*f; fy+=dy*f; }
    } else { if(b.c0[i]>=0)_bhStack[sp++]=b.c0[i]; if(b.c1[i]>=0)_bhStack[sp++]=b.c1[i];
             if(b.c2[i]>=0)_bhStack[sp++]=b.c2[i]; if(b.c3[i]>=0)_bhStack[sp++]=b.c3[i]; } }
  a.vx+=fx; a.vy+=fy; }

function step(){
  const vis = visList();
  const cc = communityCentroids();
  if(buildBH(vis)) for(const a of vis) bhForce(a);
  for (const e of edges){ if(!eVisible(e)) continue; const a=byId[e.source], b=byId[e.target];
    let dx=b.x-a.x, dy=b.y-a.y, d=Math.hypot(dx,dy)||1, f=(d-linkDist)*0.01*alpha;
    a.vx+=dx/d*f; a.vy+=dy/d*f; b.vx-=dx/d*f; b.vy-=dy/d*f; }
  for (const n of vis){ const c=cc[n.community];
    if(c){ n.vx+=(c.x-n.x)*COMM_PULL*alpha; n.vy+=(c.y-n.y)*COMM_PULL*alpha; }
    n.vx*=.85; n.vy*=.85; n.x+=n.vx*0.5; n.y+=n.vy*0.5;
    n.vx-=n.x*GRAVITY*alpha; n.vy-=n.y*GRAVITY*alpha; }
  alpha *= ALPHA_DECAY; if(alpha < ALPHA_MIN){ alpha = 0; running = false; if(!userMoved && !vTarget) fit(); }
}
const TC = (wx,wy) => ({ x: wx*view.k+W/2+view.x, y: wy*view.k+H/2+view.y });
const T = n => TC(n.x, n.y);
// Viewport culling: the on-screen rect (in screen px) recomputed once per frame.
// `PAD` keeps a node whose centre is just off-screen but whose glow still reaches
// in. onNode() rejects a single point; segVisible() does a cheap separating-axis
// reject — a segment with both endpoints off the same side can't cross the rect.
let _vp = { x0:0, y0:0, x1:0, y1:0 };
function updateViewport(){ const PAD = 40 * Math.min(2.4, Math.max(0.7, view.k));
  _vp.x0 = -PAD; _vp.y0 = -PAD; _vp.x1 = W + PAD; _vp.y1 = H + PAD; }
const onPt = p => p.x>=_vp.x0 && p.x<=_vp.x1 && p.y>=_vp.y0 && p.y<=_vp.y1;
const segVisible = (p,q) => !((p.x<_vp.x0&&q.x<_vp.x0) || (p.x>_vp.x1&&q.x>_vp.x1) ||
                             (p.y<_vp.y0&&q.y<_vp.y0) || (p.y>_vp.y1&&q.y>_vp.y1));

// ---- macro LOD : one blob per community below MACRO_K ---------------------
// Zoomed far out, drawing every node is both slow and illegible. Instead roll the
// visible nodes up per community (centroid + spread + counts, computed live from
// current positions) and draw one blob per community — sized by member count,
// coloured by community, amber-tinged if it holds knowledge. Individual nodes
// return on zoom-in. The `comm` rollup (size/top/know) is reused for labels.
const MACRO_K = 0.4;
const isMacro = () => view.k < MACRO_K;
// Drift pulse + constitutional crown (governance overlay). `_pulse` advances every
// frame so the drift ring breathes even after the layout settles; `_pulseLive` is
// re-armed each frame a drifted node is drawn, so draw() keeps animating only while
// a pulse is on screen (no busy-loop on a clean graph).
let _pulse = 0, _pulseLive = false;
function drawCrown(cx, cy, s, a){ ctx.save(); ctx.globalAlpha=0.95*a;
  ctx.fillStyle="hsl(44 100% 64%)"; ctx.strokeStyle="rgba(40,24,2,0.6)"; ctx.lineWidth=0.6;
  ctx.beginPath(); ctx.moveTo(cx-s, cy); ctx.lineTo(cx-s, cy-s*0.85);
  ctx.lineTo(cx-s*0.5, cy-s*0.35); ctx.lineTo(cx, cy-s*1.05);
  ctx.lineTo(cx+s*0.5, cy-s*0.35); ctx.lineTo(cx+s, cy-s*0.85);
  ctx.lineTo(cx+s, cy); ctx.closePath(); ctx.fill(); ctx.stroke(); ctx.restore(); }
// Per-community geometry over the visible set: centroid, member points (for the
// hull), member/knowledge counts. Rebuilt each macro frame — O(visible nodes).
function macroRollup(){ const m = {};
  for (const n of visList()){ const c = m[n.community] ||
      (m[n.community]={cx:0,cy:0,n:0,know:0,pts:[],comm:n.community});
    c.cx+=n.x; c.cy+=n.y; c.n++; if(isKnow(n)) c.know++; c.pts.push(n); }
  for (const k in m){ const c=m[k]; c.cx/=c.n; c.cy/=c.n;
    let s=0; for(const p of c.pts){ const dx=p.x-c.cx, dy=p.y-c.cy; const d2=dx*dx+dy*dy; if(d2>s)s=d2; }
    c.spread = Math.sqrt(s); }                  // world-space radius enclosing members
  return m; }
// Convex hull (Andrew's monotone chain) of a community's member points — drawn as a
// faint filled region so a cluster reads as a territory, Gephi-style.
function convexHull(pts){ if(pts.length<3) return pts.map(p=>[p.x,p.y]);
  const P = pts.map(p=>[p.x,p.y]).sort((a,b)=> a[0]-b[0] || a[1]-b[1]);
  const cross=(o,a,b)=>(a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0]);
  const lo=[]; for(const p of P){ while(lo.length>=2 && cross(lo[lo.length-2],lo[lo.length-1],p)<=0) lo.pop(); lo.push(p); }
  const hi=[]; for(let i=P.length-1;i>=0;i--){ const p=P[i];
    while(hi.length>=2 && cross(hi[hi.length-2],hi[hi.length-1],p)<=0) hi.pop(); hi.push(p); }
  lo.pop(); hi.pop(); return lo.concat(hi); }
function drawMacro(){ const m = macroRollup();
  const groups = Object.values(m).sort((a,b)=>b.n-a.n);   // big communities behind
  // Pass A: faint convex-hull territories behind everything.
  for(const c of groups){ if(c.n<3) continue; const hull=convexHull(c.pts);
    let any=false; for(const h of hull){ const sp=TC(h[0],h[1]); if(onPt(sp)){ any=true; break; } }
    if(!any) continue;
    ctx.beginPath(); for(let i=0;i<hull.length;i++){ const sp=TC(hull[i][0],hull[i][1]);
      i?ctx.lineTo(sp.x,sp.y):ctx.moveTo(sp.x,sp.y); } ctx.closePath();
    ctx.fillStyle=ccolor(c.comm); ctx.globalAlpha=0.07; ctx.fill();
    ctx.globalAlpha=0.22; ctx.lineWidth=1; ctx.strokeStyle=ccolor(c.comm); ctx.stroke(); }
  ctx.globalAlpha=1;
  // Pass B: one solid blob per community at its centroid, sized by member count.
  for(const c of groups){ const p=TC(c.cx,c.cy);
    const r = Math.max(6, Math.sqrt(c.n)*3.2) ;          // area ∝ member count
    if(p.x<-r||p.x>W+r||p.y<-r||p.y>H+r) continue;
    const base=ccolor(c.comm);
    ctx.globalAlpha=0.85; ctx.fillStyle=base; ctx.beginPath(); ctx.arc(p.x,p.y,r,0,6.2832); ctx.fill();
    ctx.globalAlpha=0.5; ctx.lineWidth=1.4; ctx.strokeStyle="rgba(255,255,255,0.18)";
    ctx.beginPath(); ctx.arc(p.x,p.y,r,0,6.2832); ctx.stroke();
    if(c.know){ ctx.globalAlpha=0.9; ctx.fillStyle="hsl(36 100% 66%)";   // knowledge presence: amber core
      ctx.beginPath(); ctx.arc(p.x,p.y,Math.max(2.5,r*0.28),0,6.2832); ctx.fill();
      ctx.globalAlpha=0.5; ctx.drawImage(glowSprite(32), p.x-r, p.y-r, r*2, r*2); } }
  ctx.globalAlpha=1;
  // Pass C: label only the largest communities (top-centrality member as the name)
  // — labelling all 100+ clusters is soup; the big territories carry the meaning.
  // Drawn back-to-front by size and skipped if the label box overlaps an earlier one.
  ctx.font="600 11px ui-sans-serif,system-ui"; ctx.textAlign="center";
  const minLabelN = Math.max(3, groups.length>40 ? (groups[Math.min(groups.length-1,24)]?.n||3) : 2);
  const placed=[];
  for(const c of groups){ if(c.n<minLabelN) continue; const co=comm[c.comm]; if(!co) continue;
    const p=TC(c.cx,c.cy); const r=Math.max(6, Math.sqrt(c.n)*3.2); if(p.x<0||p.x>W||p.y<0||p.y>H) continue;
    const txt=co.top.label, tw=ctx.measureText(txt).width;
    const bx=p.x-tw/2-5, by=p.y+r+3, bw=tw+10, bh=16;
    if(placed.some(o => bx<o.x+o.w && bx+bw>o.x && by<o.y+o.h && by+bh>o.y)) continue;  // de-overlap
    placed.push({x:bx,y:by,w:bw,h:bh});
    ctx.fillStyle="rgba(20,19,16,0.78)"; ctx.fillRect(bx, by, bw, bh);
    ctx.fillStyle=c.know?"#ffd27f":"#cdd3da"; ctx.fillText(txt, p.x, p.y+r+15); }
  ctx.textAlign="start"; }
// In the Knowledge lens code is tiny "dust"; in Communities/Heat it's rendered as
// bigger, solid, graphify-style nodes so the colours actually read.
const baseR = n => isKnow(n) ? (3 + (n.centrality||0)*3.4 + Math.min((deg[n.id]||0)*0.12,2.4))
  : (lens === "know" ? (1.6 + (n.centrality||0)*5 + Math.min((deg[n.id]||0),30)*0.05)
                     : (2.6 + (n.centrality||0)*6 + Math.min((deg[n.id]||0),40)*0.07));
const radius = n => baseR(n) * Math.min(2.4, Math.max(0.7, view.k));
const neighbors = id => new Set(adj[id].map(([t])=>t));

function fitView(){ const vis = visList(); if(!vis.length) return null;
  const xs=vis.map(n=>n.x).sort((a,b)=>a-b), ys=vis.map(n=>n.y).sort((a,b)=>a-b);
  const lo=i=>i[Math.floor(i.length*0.02)], hi=i=>i[Math.floor(i.length*0.98)];
  const minX=lo(xs),maxX=hi(xs),minY=lo(ys),maxY=hi(ys);
  const w=maxX-minX||1, h=maxY-minY||1;
  const k = Math.max(0.2, Math.min(2.5, 0.85*Math.min(W/w, H/h)));
  return { k, x:-(minX+maxX)/2*k, y:-(minY+maxY)/2*k }; }
// fit() snaps (used by the settling physics loop); fitAnimated() glides (user-driven).
function fit(){ const t=fitView(); if(t){ view.k=t.k; view.x=t.x; view.y=t.y; vTarget=null; } }
function fitAnimated(){ const t=fitView(); if(t) vTarget={...t}; }
function setFocus(id){ focusSet = new Set([id, ...neighbors(id)]); invalidateVis(); reheat(0.45); }
function clearFocus(){ focusSet = null; invalidateVis(); reheat(0.3); }
function toggleLens(){ const knowOn = focusSet && focusSet._lens;
  if(knowOn){ focusSet=null; }
  else { const s=new Set(); s._lens=true; for(const n of nodes) if(isKnow(n)){ s.add(n.id);
      neighbors(n.id).forEach(x=>s.add(x)); } focusSet=s; fit(); toast("knowledge nodes + the code they touch"); }
  invalidateVis(); reheat(0.4); }

// ---- shortest path (BFS) ----
function togglePath(){ pathMode=!pathMode; pathA=null;
  document.querySelector('[data-lens="path"]').classList.toggle("on",pathMode);
  if(pathMode){ clearPath(); toast("click the source node"); } }
function shortestPath(a,b){ if(a===b) return [a]; const prev={[a]:null}, q=[a];
  while(q.length){ const u=q.shift();
    for(const [v] of adj[u]){ if(!(v in prev)){ prev[v]=u;
      if(v===b){ const p=[b]; let x=b; while(prev[x]!=null){ x=prev[x]; p.unshift(x); } return p; }
      q.push(v); } } } return null; }
function setPath(p){ if(!p){ toast("no path between those nodes"); clearPath(); return; }
  pathSet=new Set(p); pathEdge=new Set(); selected=null;
  for(let i=0;i<p.length-1;i++){ pathEdge.add(p[i]+" "+p[i+1]); pathEdge.add(p[i+1]+" "+p[i]); }
  $("detail").innerHTML = `<div class="ins-type"><span class="sw"></span><span class="lab">Path · ${p.length} nodes</span></div>` +
    p.map((id,i)=>`<span class="nb${i?"":" gov"}" data-go="${esc(id)}"><span class="sym">${i?"↳":"▸"}</span>${esc(byId[id].label)}</span>`).join("");
  $("agentrow").style.display="flex"; wireGo();
  pathMD = () => `# Path (${p.length} nodes)\n` + p.map(id=>`- ${byId[id].label} (${byId[id].type})`).join("\n");
  _substrateDirty=true; }   // path edges are skipped from the substrate — re-render it
function clearPath(){ pathSet=null; pathEdge=new Set(); pathA=null; pathMD=null; _substrateDirty=true; }

// ---- render : the Solar pipeline ----------------------------------------
function draw(){
  _f++; _pulse++; _pulseLive=false;
  easeView();
  if(running && _f % PHYS_STRIDE === 0) step();
  // The layout grows as it settles, so keep re-framing to fit (driven by the draw
  // loop, not events) until the user takes control — this is the real fix for the
  // "graph is cut off until I switch tabs" glitch. Suppressed while a camera tween
  // is in flight, so the auto-fit and the glide never fight.
  if(running && !userMoved && !vTarget && _f % 16 === 0) fit();
  ctx.clearRect(0,0,W,H);
  updateViewport();
  const anchor = selected || hover, near = anchor ? neighbors(anchor) : null;
  const dimCode = lens==="know";
  const macro = isMacro();        // far-out overview: communities as blobs, not nodes

  // 1. faint code substrate — blitted from an offscreen cache when idle, else live
  substratePass();
  if(!macro && anchor){ ctx.setLineDash([]); ctx.lineWidth=1.2;
    for(const [tid,e] of adj[anchor]){ if(!eVisible(e)) continue;
      if(e.type==="governs"||e.type==="related"||e.type==="supersedes") continue;
      const a=byId[e.source], b=byId[e.target], p=T(a), q=T(b); if(!segVisible(p,q)) continue;
      ctx.strokeStyle="rgba("+(e.type==="calls"?"140,160,178":"120,124,130")+",0.55)";
      ctx.beginPath(); ctx.moveTo(p.x,p.y); ctx.lineTo(q.x,q.y); ctx.stroke(); } }

  // 2. code dust  (skipped at macro — communities are drawn as blobs instead)
  if(!macro) for (const n of nodes){ if(!visible(n) || isKnow(n)) continue; const p=T(n); if(!onPt(p)) continue; const r=radius(n);
    let a = dimCode ? (0.32+(n.centrality||0)*0.5) : 0.95;
    if(anchor && near && !near.has(n.id) && n.id!==anchor) a*=0.22;
    if(query && !match(n)) a*=0.2; if(pathSet && !pathSet.has(n.id)) a*=0.18;
    ctx.globalAlpha=a; ctx.fillStyle=codeFill(n);
    ctx.beginPath(); ctx.arc(p.x,p.y,r,0,6.2832); ctx.fill();
    if(isGod(n) && a>0.5){ ctx.globalAlpha=a*0.28; ctx.strokeStyle=codeFill(n); ctx.lineWidth=1;
      ctx.beginPath(); ctx.arc(p.x,p.y,r+3.5,0,6.2832); ctx.stroke(); }
    if(n.id===selected){ ctx.globalAlpha=1; ctx.strokeStyle="#fff"; ctx.lineWidth=1.6;
      ctx.beginPath(); ctx.arc(p.x,p.y,r+2,0,6.2832); ctx.stroke(); } }
  ctx.globalAlpha=1;

  // 3. governs threads — glowing amber curves (the precious knowledge↔code links).
  // Two static passes (wide soft underlay + bright thread) replace the per-frame
  // shadowBlur + per-edge linearGradient — same amber bloom, none of the cost.
  // Pass A: build all the curve paths once, stroke the soft glow underlay.
  ctx.lineCap="round";
  ctx.beginPath();
  for (const e of edges){ if(e.type!=="governs" || !eVisible(e)) continue;
    const a=byId[e.source], b=byId[e.target], p=T(a), q=T(b); if(!segVisible(p,q)) continue;
    const mx=(p.x+q.x)/2, my=(p.y+q.y)/2-Math.abs(q.x-p.x)*0.10;
    ctx.moveTo(p.x,p.y); ctx.quadraticCurveTo(mx,my,q.x,q.y); }
  ctx.strokeStyle="rgba(255,143,0,0.10)"; ctx.lineWidth=4.5; ctx.stroke();   // bloom
  ctx.strokeStyle="rgba(255,160,72,0.62)"; ctx.lineWidth=1.6; ctx.stroke();  // bright thread
  ctx.lineCap="butt";

  // Macro LOD: communities as blobs + hulls + labels; skip the per-node passes.
  if(macro){ drawMacro();
    if(_f%4===0) drawMini(); updatePill(); requestAnimationFrame(draw); return; }

  // 4. knowledge-internal edges
  ctx.strokeStyle="rgba(255,164,79,0.18)"; ctx.lineWidth=1;
  for (const e of edges){ if((e.type!=="related"&&e.type!=="supersedes") || !eVisible(e)) continue;
    const a=byId[e.source], b=byId[e.target], p=T(a), q=T(b); if(!segVisible(p,q)) continue;
    ctx.beginPath(); ctx.moveTo(p.x,p.y); ctx.lineTo(q.x,q.y); ctx.stroke(); }

  // 5. highlighted path
  if(pathSet){ ctx.save(); ctx.shadowColor="rgba(255,143,0,0.8)"; ctx.shadowBlur=6;
    ctx.strokeStyle="#ffd27f"; ctx.lineWidth=2.4;
    for(const e of edges){ if(!pathEdge.has(ekey(e))) continue; const a=byId[e.source], b=byId[e.target], p=T(a), q=T(b);
      if(!segVisible(p,q)) continue;
      ctx.beginPath(); ctx.moveTo(p.x,p.y); ctx.lineTo(q.x,q.y); ctx.stroke(); } ctx.restore(); }

  // 6. knowledge nodes — incandescent
  for (const n of nodes){ if(!visible(n) || !isKnow(n)) continue; const p=T(n), r=radius(n);
    const gl=r*4.5; if(p.x<-gl||p.x>W+gl||p.y<-gl||p.y>H+gl) continue;   // cull (glow-aware)
    let a=1; if(anchor && near && !near.has(n.id) && n.id!==anchor) a*=0.3;
    if(query && !match(n)) a*=0.3; if(pathSet && !pathSet.has(n.id)) a*=0.25;
    const hue=knowHue(n.type);
    ctx.globalAlpha=a; ctx.drawImage(glowSprite(hue), p.x-gl, p.y-gl, gl*2, gl*2);
    ctx.fillStyle="hsl("+hue+" 100% 72%)"; ctx.beginPath(); ctx.arc(p.x,p.y,r,0,6.2832); ctx.fill();
    ctx.strokeStyle="rgba(255,225,180,"+(0.9*a)+")"; ctx.lineWidth=1; ctx.beginPath(); ctx.arc(p.x,p.y,r,0,6.2832); ctx.stroke();
    ctx.globalAlpha=1;
    // Drift pulse — a rule whose seal drifted (governed code changed structure since
    // affirmed). The flag is deterministic, stamped at build time from `seal`/`check`.
    if(n.drift){ _pulseLive=true; const ph=0.5+0.5*Math.sin(_pulse*0.10);
      ctx.strokeStyle="rgba(255,70,54,"+(0.85*a)+")"; ctx.lineWidth=1.6;
      ctx.beginPath(); ctx.arc(p.x,p.y,r+3,0,6.2832); ctx.stroke();
      ctx.strokeStyle="rgba(255,70,54,"+(0.5*a*ph)+")"; ctx.lineWidth=2;
      ctx.beginPath(); ctx.arc(p.x,p.y,r+6+ph*7,0,6.2832); ctx.stroke(); }
    // Constitutional crown — the highest tier, ratified. A small 3-point amber crown.
    if(n.tier==="constitutional") drawCrown(p.x, p.y-r-4, Math.max(4, r*0.9), a);
    if(n.id===selected){ ctx.strokeStyle="rgba(255,164,79,0.9)"; ctx.lineWidth=1.4;
      ctx.beginPath(); ctx.arc(p.x,p.y,r+8,0,6.2832); ctx.stroke();
      ctx.strokeStyle="rgba(255,164,79,0.3)"; ctx.beginPath(); ctx.arc(p.x,p.y,r+13,0,6.2832); ctx.stroke(); } }

  // 7. labels — only the hovered (or selected) node; the field stays label-free
  // otherwise, so nothing clutters it until you hover.
  if(showLabels) { ctx.font="600 11px ui-sans-serif,system-ui";
    for (const id of [selected, hover]){ const n = id && byId[id]; if(!n || !visible(n)) continue;
      const p=T(n), r=radius(n), txt=n.label, tw=ctx.measureText(txt).width;
      ctx.fillStyle = id===selected ? "rgba(20,19,16,0.95)" : "rgba(20,19,16,0.8)";
      ctx.fillRect(p.x+r+3, p.y-8, tw+10, 17);
      ctx.fillStyle = isKnow(n) ? "#ffd27f" : (id===selected ? "#ffa44f" : "#ece7df");
      ctx.fillText(txt, p.x+r+8, p.y+4); } }
  if(_f%4===0) drawMini();
  updatePill();
  requestAnimationFrame(draw);
}
function drawSubstrate(g, type, rgb, alpha, dash){
  g.setLineDash(dash?[3,3]:[]); g.lineWidth=1; g.strokeStyle="rgba("+rgb+","+alpha+")";
  for(const e of edges){ if(e.type!==type || !eVisible(e)) continue;
    if(pathSet && pathEdge.has(ekey(e))) continue;
    const a=byId[e.source], b=byId[e.target], p=T(a), q=T(b); if(!segVisible(p,q)) continue;
    g.beginPath(); g.moveTo(p.x,p.y); g.lineTo(q.x,q.y); g.stroke(); }
  g.setLineDash([]); }
function paintSubstrate(g){
  drawSubstrate(g, "contains", "44,42,38", 0.06, false);
  drawSubstrate(g, "references", "74,79,85", 0.06, true);
  drawSubstrate(g, "calls", "111,126,140", 0.11, false); }
// Blit the static substrate when idle (settled + still camera); otherwise paint
// live. Returns true when it served from the offscreen cache (so draw() can skip
// the live passes). The cache is full-canvas (already in screen space), so the
// blit is a 1:1 drawImage with no transform.
function substratePass(){
  const still = !running && !vTarget;
  if(!still){ _substrateDirty = true; paintSubstrate(ctx); return; }
  if(_subView.x!==view.x || _subView.y!==view.y || _subView.k!==view.k) _substrateDirty = true;
  if(_substrateDirty || !_subCv){
    if(!_subCv){ _subCv = document.createElement("canvas"); }
    if(_subCv.width!==cv.width || _subCv.height!==cv.height){ _subCv.width=cv.width; _subCv.height=cv.height; }
    _subCtx = _subCv.getContext("2d"); _subCtx.setTransform(DPR,0,0,DPR,0,0);
    _subCtx.clearRect(0,0,W,H); paintSubstrate(_subCtx);
    _subView.x=view.x; _subView.y=view.y; _subView.k=view.k; _substrateDirty=false; }
  ctx.drawImage(_subCv, 0, 0, W, H); }

// ---- minimap (rail overview, or floating one when the rail is collapsed) --
let _mmBounds=null;
function drawMiniInto(mm, frame){ if(!mm) return; const MW=mm.clientWidth, MH=mm.clientHeight;
  if(!MW || !MH) return; const mx=mm.getContext("2d");
  mm.width=MW*DPR; mm.height=MH*DPR; mx.setTransform(DPR,0,0,DPR,0,0);
  mx.fillStyle="#000"; mx.fillRect(0,0,MW,MH);
  let minX=1e9,maxX=-1e9,minY=1e9,maxY=-1e9;
  for(const n of nodes){ if(n.x<minX)minX=n.x; if(n.x>maxX)maxX=n.x; if(n.y<minY)minY=n.y; if(n.y>maxY)maxY=n.y; }
  const bw=(maxX-minX)||1, bh=(maxY-minY)||1, s=Math.min((MW-12)/bw,(MH-12)/bh);
  const ox=MW/2-(minX+maxX)/2*s, oy=MH/2-(minY+maxY)/2*s;
  _mmBounds={s,ox,oy};
  for(const n of nodes){ if(isKnow(n)||!visible(n)) continue;
    mx.fillStyle="rgba(120,130,142,"+(0.16+(n.centrality||0)*0.4)+")";
    mx.fillRect(n.x*s+ox, n.y*s+oy, 1, 1); }
  mx.save(); mx.shadowColor="rgba(255,143,0,0.9)"; mx.shadowBlur=4;
  for(const n of nodes){ if(!isKnow(n)||!visible(n)) continue; mx.fillStyle="#ffb56a";
    mx.fillRect(n.x*s+ox-1, n.y*s+oy-1, 2.4, 2.4); } mx.restore();
  const wx0=(0-W/2-view.x)/view.k, wx1=(W-W/2-view.x)/view.k;
  const wy0=(0-H/2-view.y)/view.k, wy1=(H-H/2-view.y)/view.k;
  const rx=wx0*s+ox, ry=wy0*s+oy, rw=(wx1-wx0)*s, rh=(wy1-wy0)*s;
  const cx=Math.max(0,rx), cy=Math.max(0,ry);
  frame.style.left=cx+"px"; frame.style.top=cy+"px";
  frame.style.width=Math.max(6,Math.min(MW,rx+rw)-cx)+"px"; frame.style.height=Math.max(6,Math.min(MH,ry+rh)-cy)+"px"; }
function drawMini(){ if($("right").classList.contains("collapsed")) drawMiniInto($("fmm"), $("fmmview"));
  else drawMiniInto($("mm"), $("mmview")); }
function bindMM(mm){ if(!mm) return;
  const panTo = ev => { if(!_mmBounds) return; const r=mm.getBoundingClientRect();
    const wx=((ev.clientX-r.left)-_mmBounds.ox)/_mmBounds.s, wy=((ev.clientY-r.top)-_mmBounds.oy)/_mmBounds.s;
    view.x=-wx*view.k; view.y=-wy*view.k; };
  mm.onmousedown = e => { vTarget=null; panTo(e); const mv=ev=>panTo(ev);
    const up=()=>{ window.removeEventListener("mousemove",mv); window.removeEventListener("mouseup",up); };
    window.addEventListener("mousemove",mv); window.addEventListener("mouseup",up); }; }
bindMM($("mm")); bindMM($("fmm"));

// ---- zoom well + mode pill ----------------------------------------------
const K_MIN=0.15, K_MAX=5, LK=Math.log(K_MIN), LKR=Math.log(K_MAX)-LK;
const clampK = k => Math.max(K_MIN, Math.min(K_MAX, k));
// Smooth camera. Every interactive zoom/recenter sets `vTarget`; easeView() (run
// once per frame in draw) glides the live `view` toward it, so nothing snaps.
// Direct manipulation — panning, node-drag, the zoom slider — cancels the tween so
// it stays 1:1 with the cursor; the physics auto-fit is suppressed while one runs.
function easeView(){ if(!vTarget) return;
  view.k += (vTarget.k-view.k)*VIEW_EASE;
  view.x += (vTarget.x-view.x)*VIEW_EASE;
  view.y += (vTarget.y-view.y)*VIEW_EASE;
  if(Math.abs(vTarget.k-view.k)<1e-3 && Math.hypot(vTarget.x-view.x, vTarget.y-view.y)<0.4){
    view.k=vTarget.k; view.x=vTarget.x; view.y=vTarget.y; vTarget=null; } }
// Zoom keeping the world point under (ex,ey) pinned — compounded in target space so
// rapid wheel ticks anchor consistently while the previous glide is still in flight.
function zoomBy(ex, ey, factor){ userMoved=true; const b=vTarget||view; const k=clampK(b.k*factor);
  const wx=(ex-W/2-b.x)/b.k, wy=(ey-H/2-b.y)/b.k;
  vTarget={ k, x: ex-W/2-wx*k, y: ey-H/2-wy*k }; }
function zoomToCenter(k){ userMoved=true; const b=vTarget||view; k=clampK(k);
  const wx=-b.x/b.k, wy=-b.y/b.k; vTarget={ k, x:-wx*k, y:-wy*k }; }
function flyTo(x, y, k){ userMoved=true; vTarget={ k:clampK(k), x, y }; }
function updatePill(){ const macro = view.k < 0.55;   // zoomed-out overview = macro
  $("bmacro").classList.toggle("on",macro); $("bmicro").classList.toggle("on",!macro);
  $("zthumb").style.left=((Math.log(clampK(view.k))-LK)/LKR*100)+"%";
  $("zlabel").textContent = macro ? "macro" : (view.k>1.4 ? "detail" : "micro"); }
// Zoom slider: drag (not just click) the thumb. Writes the camera directly so the
// thumb tracks the cursor 1:1, recentred on the viewport so the graph scales in place.
const kFromTrack = clientX => { const r=$("ztrack").getBoundingClientRect();
  return Math.exp(LK + Math.max(0,Math.min(1,(clientX-r.left)/r.width))*LKR); };
function zoomCenterNow(k){ userMoved=true; vTarget=null; k=clampK(k);
  const wx=-view.x/view.k, wy=-view.y/view.k; view.k=k; view.x=-wx*k; view.y=-wy*k; }
$("ztrack").onmousedown = e => { e.preventDefault(); zoomCenterNow(kFromTrack(e.clientX));
  const mv=ev=>zoomCenterNow(kFromTrack(ev.clientX));
  const up=()=>{ window.removeEventListener("mousemove",mv); window.removeEventListener("mouseup",up); };
  window.addEventListener("mousemove",mv); window.addEventListener("mouseup",up); };

// ---- governance ledger --------------------------------------------------
(function buildLedger(){
  const rows = Object.keys(govTargets).map(id => { const tg=govTargets[id];
    return { id, gov: tg.filter(t=>t.type==="governs").length, targets: tg }; })
    .sort((a,b)=> b.gov-a.gov || b.targets.length-a.targets.length);
  const body = $("ledbody");
  if(!rows.length){ body.innerHTML = `<div class="led-empty">No knowledge→code links in this graph yet — `+
    `the rule layer isn't wired to code. (That absence is the finding.)</div>`; return; }
  body.innerHTML = rows.map(r => { const n=byId[r.id], inv=(n.type==="invariant"||n.type==="regulatory");
    const sub = [n.type, n.layer, n.domain].filter(Boolean).join(" · ");
    const tgts = r.targets.map(t => { const m=byId[t.id];
      return `<div class="tgt" data-go="${esc(t.id)}"><span class="mk"></span><span class="fn">${esc(m.label)}</span>`+
        `<span class="fl">${esc(m.file?m.file+(m.line?":"+m.line:""):t.type)}</span></div>`; }).join("");
    return `<div class="lrow${inv?" inv":""}" data-rule="${esc(r.id)}"><div class="rtop"><span class="di"></span>`+
      `<span class="nm">${esc(n.label)}<small>${esc(sub)}</small></span><span class="gc">${r.gov||r.targets.length}</span></div>`+
      `<div class="targets">${tgts}</div></div>`; }).join("");
  body.querySelectorAll(".lrow").forEach(row => { row.onclick = e => {
    if(e.target.closest(".tgt")) return;
    body.querySelectorAll(".lrow").forEach(x=>x.classList.remove("open")); row.classList.add("open");
    const n=byId[row.dataset.rule]; selected=n.id; clearPath(); showDetail(n);
    const k=Math.max(view.k,1.1); flyTo(-n.x*k, -n.y*k, k); }; });
  body.querySelectorAll(".tgt").forEach(t => { t.onclick = () => { const n=byId[t.dataset.go];
    if(!n) return; selected=n.id; clearPath(); showDetail(n);
    const k=Math.max(view.k,1.1); flyTo(-n.x*k, -n.y*k, k); }; });
})();

// ---- interaction --------------------------------------------------------
function hit(mx,my){ let best=null,bd=1e9; for(const n of nodes){ if(!visible(n)) continue; const p=T(n);
  const d=Math.hypot(mx-p.x,my-p.y); if(d < radius(n)+4 && d<bd){ bd=d; best=n; } } return best; }
let drag=null, pan=false, last=null, downAt=null;
cv.onmousedown = e => { vTarget=null; last={x:e.offsetX,y:e.offsetY}; downAt={x:e.offsetX,y:e.offsetY};
  const n=hit(e.offsetX,e.offsetY);
  if(pathMode){ if(n){ if(!pathA){ pathA=n.id; selected=n.id; showDetail(n); toast("now click the target node"); }
      else { setPath(shortestPath(pathA,n.id)); pathA=null; togglePath(); } } return; }
  if(n){ drag=n; selected=n.id; clearPath(); showDetail(n); } else { pan=true; selected=null; clearPath(); clearDetail(); } };
cv.onmousemove = e => {
  const n=hit(e.offsetX,e.offsetY); hover = n?n.id:null;
  if(n && !drag){ tip.style.display="block"; tip.style.left=(e.clientX+14)+"px"; tip.style.top=(e.clientY+14)+"px";
    tip.innerHTML = `<b>${esc(n.label)}</b> · ${n.type}`+(n.file?`<br>${esc(n.file)}${n.line?":"+n.line:""}`:"")+
      `<br>${deg[n.id]||0} edges`; }
  else if(!drag) tip.style.display="none";
  // only treat it as a drag past a small threshold, so a plain click never nudges
  // a node (and thus never disturbs the settled layout).
  if(drag){ if(downAt && Math.hypot(e.offsetX-downAt.x, e.offsetY-downAt.y) > 4){
      drag.x+=(e.offsetX-last.x)/view.k; drag.y+=(e.offsetY-last.y)/view.k; drag.vx=drag.vy=0; reheat(0.5); } }
  else if(pan){ view.x+=e.offsetX-last.x; view.y+=e.offsetY-last.y; userMoved=true; }
  last={x:e.offsetX,y:e.offsetY}; };
window.addEventListener("mouseup", () => { drag=null; pan=false; });
cv.ondblclick = e => { const n=hit(e.offsetX,e.offsetY); if(n){ selected=n.id; setFocus(n.id); showDetail(n); } };
// Wheel/trackpad zoom: scale by the *magnitude* of the delta (normalised across
// pixel/line/page deltaModes) so one mouse notch and a trackpad swipe both feel
// natural, then glide there. macOS pinch arrives as ctrl+wheel with coarser deltas.
cv.onwheel = e => { e.preventDefault();
  let d = e.deltaY; if(e.deltaMode===1) d*=16; else if(e.deltaMode===2) d*=(H||500);
  const factor = Math.max(0.4, Math.min(2.5, Math.exp(-d * (e.ctrlKey ? 0.010 : 0.0018))));
  zoomBy(e.offsetX, e.offsetY, factor); };
window.addEventListener("keydown", e => { if(e.target.tagName==="INPUT"){ if(e.key==="Escape")e.target.blur(); return; }
  const k=e.key.toLowerCase();
  if(k==="/"){ e.preventDefault(); $("q").focus(); }
  else if(k==="f"){ userMoved=false; fitAnimated(); } else if(k==="r"){ flyTo(0,0,1); }
  else if(k==="+"||k==="="){ zoomToCenter((vTarget?vTarget.k:view.k)*1.3); }
  else if(k==="-"||k==="_"){ zoomToCenter((vTarget?vTarget.k:view.k)/1.3); }
  else if(k===" "){ e.preventDefault(); running ? (running=false) : reheat(0.3); }
  else if(k==="e"){ if(selected) setFocus(selected); }
  else if(k==="l"){ showLabels=!showLabels; }
  else if(k==="c") $("bmacro").click();
  else if(k==="p") togglePath();
  else if(k==="escape"){ clearFocus(); clearPath(); pathMode=false;
    document.querySelector('[data-lens="path"]').classList.remove("on"); selected=null; clearDetail(); } });

// ---- inspector ----------------------------------------------------------
function wireGo(){ $("detail").querySelectorAll("[data-go]").forEach(el => el.onclick = () => {
  selected = el.dataset.go; clearPath(); showDetail(byId[selected]); }); }
function showDetail(n){ $("agentrow").style.display="flex";
  const groups={}; for(const [tid,e,dir] of adj[n.id]){ (groups[e.type]=groups[e.type]||[]).push({id:tid,dir,sym:dir>0?"→":"←"}); }
  const hue = isKnow(n) ? knowHue(n.type) : null;
  const swStyle = hue!=null ? `background:hsl(${hue} 100% 66%);box-shadow:0 0 10px hsl(${hue} 100% 66%)` : `background:${codeFill(n)};box-shadow:none`;
  let s = `<div class="ins-type"><span class="sw" style="${swStyle}"></span>`+
    `<span class="lab" style="${hue!=null?"":"color:var(--muted)"}">${n.type}${isKnow(n)?" · knowledge layer":""}</span></div>`+
    `<div class="ins-title">${esc(n.label)}</div>`+
    `<div class="ins-sub">community ${n.community} · degree ${deg[n.id]||0} · centrality ${(n.centrality||0).toFixed(3)}`+
      (n.file?` · ${fileLink(n)}`:"")+`</div>`;
  const pills=[]; if(n.layer)pills.push(["layer: "+n.layer,1]); if(n.domain)pills.push(["domain: "+n.domain,0]);
  if(n.status)pills.push(["status: "+n.status,0]); if(isGod(n))pills.push(["⭐ hub",1]);
  if(n.tier==="constitutional")pills.push(["♚ constitutional",1]);
  if(pills.length) s += `<div class="pills">`+pills.map(([p,a])=>`<span class="pill${a?" amb":""}">${esc(p)}</span>`).join("")+`</div>`;
  if(n.drift) s += `<div class="pills"><span class="pill drift">⚠ drifted — governed code changed since sealed; <code>fux seal ${esc(n.label)}</code></span></div>`;
  if(!isKnow(n)){ const know = adj[n.id].filter(([tid])=>isKnow(byId[tid]));
    s += `<div class="lab ins-section">⚖ governed by</div>`;
    s += know.length ? know.map(([tid,e])=>`<span class="nb gov" data-go="${esc(tid)}"><span class="sym">⚖</span>${esc(byId[tid].label)} · ${e.type}</span>`).join("")
      : `<div class="ins-sub" style="font-style:italic">no rules linked to this node</div>`; }
  for(const t of Object.keys(groups).sort()){ s += `<div class="lab ins-section">${t}</div>`+
    groups[t].slice(0,30).map(x=>`<span class="nb" data-go="${esc(x.id)}"><span class="sym">${x.sym}</span>${esc(byId[x.id].label)}</span>`).join(""); }
  $("detail").innerHTML = s; wireGo(); }
function clearDetail(){ $("agentrow").style.display="none";
  $("detail").innerHTML = `<div class="ins-sub" style="margin:0">Click a node. Double-click to focus its neighbourhood.</div>`; }
// file:line → an <editor>://file/<abs>:<line>:<col> deep link (opens VSCode/Cursor on
// the exact line). Falls back to plain text when the build embedded no project ROOT.
function fileLink(n){
  const label = esc(n.file) + (n.line ? ":"+n.line : "");
  if(!ROOT) return label;
  const href = encodeURI(EDITOR + "://file" + ROOT + "/" + n.file + ":" + (n.line||1) + ":1");
  return `<a href="${href}" title="open in ${esc(EDITOR)} at line ${n.line||1}"`+
    ` style="color:#ffb877;text-decoration:none">${label}<span style="opacity:.6"> ↗</span></a>`; }

// ---- markdown export ----------------------------------------------------
function nodeMarkdown(n){ let s=`### ${n.label} (${n.type})\n`;
  if(n.file)s+=`- file: ${n.file}${n.line?":"+n.line:""}\n`;
  for(const f of ["domain","layer","status","community"]) if(n[f]!=null) s+=`- ${f}: ${n[f]}\n`;
  s+=`- degree: ${deg[n.id]||0}\n\n**Connections**\n`;
  for(const [tid,e,dir] of adj[n.id]) s+=`- ${e.type} ${dir>0?"→":"←"} ${byId[tid].label} (${byId[tid].type})\n`;
  return s; }
function graphMarkdown(){ const vis=nodes.filter(visible);
  let s=`# Fux graph (visible subset)\n${vis.length} nodes, `+edges.filter(eVisible).length+` edges\n\n## Nodes by type\n`;
  const byT={}; vis.forEach(n=>(byT[n.type]=byT[n.type]||[]).push(n.label));
  for(const t of Object.keys(byT).sort()) s+=`- **${t}** (${byT[t].length}): ${byT[t].slice(0,30).join(", ")}\n`;
  s+=`\n## Edges\n`; edges.filter(eVisible).slice(0,200).forEach(e=> s+=`- ${byId[e.source].label} —${e.type}→ ${byId[e.target].label}\n`);
  return s; }
function governedMarkdown(){ let s=`# Governed subgraph — ${governsCount} governs links\n\n`;
  const rules=Object.keys(govTargets); if(!rules.length) return s+"_No knowledge→code links in this graph._\n";
  for(const id of rules){ const n=byId[id]; s+=`## ${n.label} (${n.type}${n.layer?" · "+n.layer:""})\n`;
    for(const t of govTargets[id]){ const m=byId[t.id]; s+=`- ${t.type} → ${m.label}${m.file?" ("+m.file+(m.line?":"+m.line:"")+")":""}\n`; } s+="\n"; }
  return s; }
function copy(text,msg){ navigator.clipboard?.writeText(text).then(()=>toast(msg),()=>toast("copy blocked")); }
function toast(m){ const t=$("toast"); $("toastmsg").innerHTML="<b>"+esc(m)+"</b>"; t.style.display="flex";
  clearTimeout(t._h); t._h=setTimeout(()=>t.style.display="none",1800); }

setLens("community"); fit(); draw();
