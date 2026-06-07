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
const govTargets = {};
let governsCount = 0;
for (const e of edges){ const a=byId[e.source], b=byId[e.target];
  if(e.type==="governs") governsCount++;
  let kn=null, other=null;
  if(isKnow(a) && !isKnow(b)){ kn=a; other=b; }
  else if(isKnow(b) && !isKnow(a)){ kn=b; other=a; }
  else continue;
  if(e.type==="governs" || e.type==="related" || e.type==="references" || e.type==="implements")
    (govTargets[kn.id]=govTargets[kn.id]||[]).push({id:other.id, type:e.type}); }

let view = { x: 0, y: 0, k: 1 }, hidden = new Set(), hiddenE = new Set();
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
  return "hsl(214 10% " + (44 + (n.centrality||0)*30) + "%)"; }

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
    row.classList.toggle("off",!cb.checked); }; });   // hide/show never re-lays-out

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
  row.onclick = () => { hiddenE.has(t) ? hiddenE.delete(t) : hiddenE.add(t); row.classList.toggle("off",hiddenE.has(t)); }; });

$("ntoggle").onclick = $("ntoggle2").onclick = () => { const rows=[...document.querySelectorAll("#filters .meter")];
  const any=rows.some(r=>r.querySelector("input").checked);
  rows.forEach(r=>{ const cb=r.querySelector("input"); cb.checked=!any;
    !any ? hidden.delete(cb.dataset.t) : hidden.add(cb.dataset.t); r.classList.toggle("off",any); }); };

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
  if(view.k<1) view.k=1; view.x=-n.x*view.k; view.y=-n.y*view.k; }

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
$("bmicro").onclick = () => { focusSet=null; userMoved=true; const z=Math.max(view.k,1.3); const p=selected&&byId[selected];
  view.k=z; if(p){ view.x=-p.x*z; view.y=-p.y*z; } };
// Macro = the auto-framed overview; re-enable auto-fit so it stays framed on resize.
$("bmacro").onclick = () => { focusSet=null; userMoved=false; query=""; $("q").value=""; updateHits(); clearPath(); fit(); };

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

function communityCentroids(){ const cc = {};
  for (const n of nodes){ if(!visible(n)) continue;
    const c = cc[n.community] || (cc[n.community]={x:0,y:0,n:0}); c.x+=n.x; c.y+=n.y; c.n++; }
  for (const k in cc){ cc[k].x/=cc[k].n; cc[k].y/=cc[k].n; } return cc; }

function step(){
  const vis = nodes.filter(visible);
  const cc = communityCentroids();
  for (let i=0; i<vis.length; i++){
    const a=vis[i];
    for (let j=i+1; j<vis.length; j++){
      const b=vis[j];
      let dx=a.x-b.x, dy=a.y-b.y, d=Math.hypot(dx,dy)||1;
      if(d<REP_RANGE){ const f=charge*REP/(d*d)*alpha;
        a.vx+=dx*f; a.vy+=dy*f; b.vx-=dx*f; b.vy-=dy*f; } } }
  for (const e of edges){ if(!eVisible(e)) continue; const a=byId[e.source], b=byId[e.target];
    let dx=b.x-a.x, dy=b.y-a.y, d=Math.hypot(dx,dy)||1, f=(d-linkDist)*0.01*alpha;
    a.vx+=dx/d*f; a.vy+=dy/d*f; b.vx-=dx/d*f; b.vy-=dy/d*f; }
  for (const n of vis){ const c=cc[n.community];
    if(c){ n.vx+=(c.x-n.x)*COMM_PULL*alpha; n.vy+=(c.y-n.y)*COMM_PULL*alpha; }
    n.vx*=.85; n.vy*=.85; n.x+=n.vx*0.5; n.y+=n.vy*0.5;
    n.vx-=n.x*GRAVITY*alpha; n.vy-=n.y*GRAVITY*alpha; }
  alpha *= ALPHA_DECAY; if(alpha < ALPHA_MIN){ alpha = 0; running = false; if(!userMoved) fit(); }
}
const TC = (wx,wy) => ({ x: wx*view.k+W/2+view.x, y: wy*view.k+H/2+view.y });
const T = n => TC(n.x, n.y);
// In the Knowledge lens code is tiny "dust"; in Communities/Heat it's rendered as
// bigger, solid, graphify-style nodes so the colours actually read.
const baseR = n => isKnow(n) ? (3 + (n.centrality||0)*3.4 + Math.min((deg[n.id]||0)*0.12,2.4))
  : (lens === "know" ? (1.6 + (n.centrality||0)*5 + Math.min((deg[n.id]||0),30)*0.05)
                     : (2.6 + (n.centrality||0)*6 + Math.min((deg[n.id]||0),40)*0.07));
const radius = n => baseR(n) * Math.min(2.4, Math.max(0.7, view.k));
const neighbors = id => new Set(adj[id].map(([t])=>t));

function fit(){ const vis = nodes.filter(visible); if(!vis.length) return;
  const xs=vis.map(n=>n.x).sort((a,b)=>a-b), ys=vis.map(n=>n.y).sort((a,b)=>a-b);
  const lo=i=>i[Math.floor(i.length*0.02)], hi=i=>i[Math.floor(i.length*0.98)];
  const minX=lo(xs),maxX=hi(xs),minY=lo(ys),maxY=hi(ys);
  const w=maxX-minX||1, h=maxY-minY||1;
  view.k = Math.max(0.2, Math.min(2.5, 0.85*Math.min(W/w, H/h)));
  view.x = -(minX+maxX)/2*view.k; view.y = -(minY+maxY)/2*view.k; }
function setFocus(id){ focusSet = new Set([id, ...neighbors(id)]); reheat(0.45); }
function clearFocus(){ focusSet = null; reheat(0.3); }
function toggleLens(){ const knowOn = focusSet && focusSet._lens;
  if(knowOn){ focusSet=null; }
  else { const s=new Set(); s._lens=true; for(const n of nodes) if(isKnow(n)){ s.add(n.id);
      neighbors(n.id).forEach(x=>s.add(x)); } focusSet=s; fit(); toast("knowledge nodes + the code they touch"); }
  reheat(0.4); }

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
  pathMD = () => `# Path (${p.length} nodes)\n` + p.map(id=>`- ${byId[id].label} (${byId[id].type})`).join("\n"); }
function clearPath(){ pathSet=null; pathEdge=new Set(); pathA=null; pathMD=null; }

// ---- render : the Solar pipeline ----------------------------------------
function draw(){
  _f++;
  if(running && _f % PHYS_STRIDE === 0) step();
  // The layout grows as it settles, so keep re-framing to fit (driven by the draw
  // loop, not events) until the user takes control — this is the real fix for the
  // "graph is cut off until I switch tabs" glitch.
  if(running && !userMoved && _f % 16 === 0) fit();
  ctx.clearRect(0,0,W,H);
  const anchor = selected || hover, near = anchor ? neighbors(anchor) : null;
  const dimCode = lens==="know";

  // 1. faint code substrate — grouped passes so we don't thrash canvas state
  drawSubstrate("contains", "44,42,38", 0.06, false);
  drawSubstrate("references", "74,79,85", 0.06, true);
  drawSubstrate("calls", "111,126,140", 0.11, false);
  if(anchor){ ctx.setLineDash([]); ctx.lineWidth=1.2;
    for(const [tid,e] of adj[anchor]){ if(!eVisible(e)) continue;
      if(e.type==="governs"||e.type==="related"||e.type==="supersedes") continue;
      const a=byId[e.source], b=byId[e.target], p=T(a), q=T(b);
      ctx.strokeStyle="rgba("+(e.type==="calls"?"140,160,178":"120,124,130")+",0.55)";
      ctx.beginPath(); ctx.moveTo(p.x,p.y); ctx.lineTo(q.x,q.y); ctx.stroke(); } }

  // 2. code dust
  for (const n of nodes){ if(!visible(n) || isKnow(n)) continue; const p=T(n), r=radius(n);
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

  // 3. governs threads — glowing amber curves (the precious knowledge↔code links)
  ctx.save(); ctx.shadowColor="rgba(255,143,0,0.9)"; ctx.shadowBlur=8;
  for (const e of edges){ if(e.type!=="governs" || !eVisible(e)) continue;
    const a=byId[e.source], b=byId[e.target], p=T(a), q=T(b);
    const g=ctx.createLinearGradient(p.x,p.y,q.x,q.y);
    g.addColorStop(0,"rgba(255,164,79,0.85)"); g.addColorStop(1,"rgba(255,143,0,0.30)");
    ctx.strokeStyle=g; ctx.lineWidth=1.6;
    const mx=(p.x+q.x)/2, my=(p.y+q.y)/2-Math.abs(q.x-p.x)*0.10;
    ctx.beginPath(); ctx.moveTo(p.x,p.y); ctx.quadraticCurveTo(mx,my,q.x,q.y); ctx.stroke(); }
  ctx.restore();

  // 4. knowledge-internal edges
  ctx.strokeStyle="rgba(255,164,79,0.18)"; ctx.lineWidth=1;
  for (const e of edges){ if((e.type!=="related"&&e.type!=="supersedes") || !eVisible(e)) continue;
    const a=byId[e.source], b=byId[e.target], p=T(a), q=T(b);
    ctx.beginPath(); ctx.moveTo(p.x,p.y); ctx.lineTo(q.x,q.y); ctx.stroke(); }

  // 5. highlighted path
  if(pathSet){ ctx.save(); ctx.shadowColor="rgba(255,143,0,0.8)"; ctx.shadowBlur=6;
    ctx.strokeStyle="#ffd27f"; ctx.lineWidth=2.4;
    for(const e of edges){ if(!pathEdge.has(ekey(e))) continue; const a=byId[e.source], b=byId[e.target], p=T(a), q=T(b);
      ctx.beginPath(); ctx.moveTo(p.x,p.y); ctx.lineTo(q.x,q.y); ctx.stroke(); } ctx.restore(); }

  // 6. knowledge nodes — incandescent
  for (const n of nodes){ if(!visible(n) || !isKnow(n)) continue; const p=T(n), r=radius(n);
    let a=1; if(anchor && near && !near.has(n.id) && n.id!==anchor) a*=0.3;
    if(query && !match(n)) a*=0.3; if(pathSet && !pathSet.has(n.id)) a*=0.25;
    const hue=knowHue(n.type);
    const g=ctx.createRadialGradient(p.x,p.y,0,p.x,p.y,r*4.5);
    g.addColorStop(0,"hsla("+hue+",100%,70%,"+(0.5*a)+")"); g.addColorStop(1,"hsla("+hue+",100%,60%,0)");
    ctx.fillStyle=g; ctx.beginPath(); ctx.arc(p.x,p.y,r*4.5,0,6.2832); ctx.fill();
    ctx.globalAlpha=a; ctx.fillStyle="hsl("+hue+" 100% 72%)"; ctx.beginPath(); ctx.arc(p.x,p.y,r,0,6.2832); ctx.fill();
    ctx.strokeStyle="rgba(255,225,180,"+(0.9*a)+")"; ctx.lineWidth=1; ctx.beginPath(); ctx.arc(p.x,p.y,r,0,6.2832); ctx.stroke();
    ctx.globalAlpha=1;
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
function drawSubstrate(type, rgb, alpha, dash){
  ctx.setLineDash(dash?[3,3]:[]); ctx.lineWidth=1; ctx.strokeStyle="rgba("+rgb+","+alpha+")";
  for(const e of edges){ if(e.type!==type || !eVisible(e)) continue;
    if(pathSet && pathEdge.has(ekey(e))) continue;
    const a=byId[e.source], b=byId[e.target], p=T(a), q=T(b);
    ctx.beginPath(); ctx.moveTo(p.x,p.y); ctx.lineTo(q.x,q.y); ctx.stroke(); }
  ctx.setLineDash([]); }

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
  mm.onmousedown = e => { panTo(e); const mv=ev=>panTo(ev);
    const up=()=>{ window.removeEventListener("mousemove",mv); window.removeEventListener("mouseup",up); };
    window.addEventListener("mousemove",mv); window.addEventListener("mouseup",up); }; }
bindMM($("mm")); bindMM($("fmm"));

// ---- zoom well + mode pill ----------------------------------------------
const K_MIN=0.15, K_MAX=5, LK=Math.log(K_MIN), LKR=Math.log(K_MAX)-LK;
function updatePill(){ const macro = view.k < 0.55;   // zoomed-out overview = macro
  $("bmacro").classList.toggle("on",macro); $("bmicro").classList.toggle("on",!macro);
  $("zthumb").style.left=((Math.log(Math.max(K_MIN,Math.min(K_MAX,view.k)))-LK)/LKR*100)+"%";
  $("zlabel").textContent = macro ? "macro" : (view.k>1.4 ? "detail" : "micro"); }
$("ztrack").onclick = e => { userMoved=true; const r=$("ztrack").getBoundingClientRect();
  view.k = Math.exp(LK + Math.max(0,Math.min(1,(e.clientX-r.left)/r.width))*LKR); };

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
    if(view.k<1) view.k=1.1; view.x=-n.x*view.k; view.y=-n.y*view.k; }; });
  body.querySelectorAll(".tgt").forEach(t => { t.onclick = () => { const n=byId[t.dataset.go];
    if(!n) return; selected=n.id; clearPath(); showDetail(n); if(view.k<1) view.k=1.1;
    view.x=-n.x*view.k; view.y=-n.y*view.k; }; });
})();

// ---- interaction --------------------------------------------------------
function hit(mx,my){ let best=null,bd=1e9; for(const n of nodes){ if(!visible(n)) continue; const p=T(n);
  const d=Math.hypot(mx-p.x,my-p.y); if(d < radius(n)+4 && d<bd){ bd=d; best=n; } } return best; }
let drag=null, pan=false, last=null, downAt=null;
cv.onmousedown = e => { last={x:e.offsetX,y:e.offsetY}; downAt={x:e.offsetX,y:e.offsetY};
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
cv.onwheel = e => { e.preventDefault(); userMoved=true; const f=e.deltaY<0?1.1:0.9;
  const mx=e.offsetX-W/2-view.x, my=e.offsetY-H/2-view.y;
  view.k=Math.max(K_MIN,Math.min(K_MAX,view.k*f)); view.x-=mx*(f-1); view.y-=my*(f-1); };
window.addEventListener("keydown", e => { if(e.target.tagName==="INPUT"){ if(e.key==="Escape")e.target.blur(); return; }
  const k=e.key.toLowerCase();
  if(k==="/"){ e.preventDefault(); $("q").focus(); }
  else if(k==="f"){ userMoved=false; fit(); } else if(k==="r"){ userMoved=true; view={x:0,y:0,k:1}; }
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
      (n.file?` · ${esc(n.file)}${n.line?":"+n.line:""}`:"")+`</div>`;
  const pills=[]; if(n.layer)pills.push(["layer: "+n.layer,1]); if(n.domain)pills.push(["domain: "+n.domain,0]);
  if(n.status)pills.push(["status: "+n.status,0]); if(isGod(n))pills.push(["⭐ hub",1]);
  if(pills.length) s += `<div class="pills">`+pills.map(([p,a])=>`<span class="pill${a?" amb":""}">${esc(p)}</span>`).join("")+`</div>`;
  if(!isKnow(n)){ const know = adj[n.id].filter(([tid])=>isKnow(byId[tid]));
    s += `<div class="lab ins-section">⚖ governed by</div>`;
    s += know.length ? know.map(([tid,e])=>`<span class="nb gov" data-go="${esc(tid)}"><span class="sym">⚖</span>${esc(byId[tid].label)} · ${e.type}</span>`).join("")
      : `<div class="ins-sub" style="font-style:italic">no rules linked to this node</div>`; }
  for(const t of Object.keys(groups).sort()){ s += `<div class="lab ins-section">${t}</div>`+
    groups[t].slice(0,30).map(x=>`<span class="nb" data-go="${esc(x.id)}"><span class="sym">${x.sym}</span>${esc(byId[x.id].label)}</span>`).join(""); }
  $("detail").innerHTML = s; wireGo(); }
function clearDetail(){ $("agentrow").style.display="none";
  $("detail").innerHTML = `<div class="ins-sub" style="margin:0">Click a node. Double-click to focus its neighbourhood.</div>`; }

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
