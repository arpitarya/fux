// Fux graph — vanilla canvas force viewer. Offline, dependency-free.
const cv = document.getElementById("cv"), ctx = cv.getContext("2d");
const tip = document.getElementById("tip"), $ = id => document.getElementById(id);
const SIDE = 290;

const nodes = DATA.nodes.map(n => ({ ...n, x: Math.random()*900-450, y: Math.random()*900-450, vx:0, vy:0 }));
const byId = Object.fromEntries(nodes.map(n => [n.id, n]));
const edges = DATA.edges.filter(e => byId[e.source] && byId[e.target]);
const deg = {}; edges.forEach(e => { deg[e.source]=(deg[e.source]||0)+1; deg[e.target]=(deg[e.target]||0)+1; });
const maxDeg = Math.max(1, ...Object.values(deg));
const adj = {}; nodes.forEach(n => adj[n.id] = []);
edges.forEach(e => { adj[e.source].push([e.target,e,1]); adj[e.target].push([e.source,e,-1]); });

let view = { x: 0, y: 0, k: 1 }, hidden = new Set(), hiddenE = new Set();
let selected = null, hover = null, query = "", colorMode = "type";
let running = true, showLabels = true, focusSet = null;
let linkDist = 70, charge = 900;

// ---- colour modes -------------------------------------------------------
const ccolor = c => "hsl(" + (((c||0)*67)%360) + ",62%,55%)";
const heat = d => { const t = (deg[d]||0)/maxDeg; return `hsl(${(1-t)*210},80%,${35+t*25}%)`; };
function nodeColor(n){
  if (colorMode === "community") return ccolor(n.community);
  if (colorMode === "layer") return LAYER_COLORS[n.layer] || color(n.type);
  if (colorMode === "degree") return heat(n.id);
  return color(n.type);
}

// ---- sidebar: stats, filters, controls ----------------------------------
$("stats").textContent =
  `${nodes.length} nodes · ${edges.length} edges · ${DATA.meta.code_files} files · `+
  `${DATA.meta.rules} rules · ${DATA.meta.communities} communities`;

const typeCounts = {}; nodes.forEach(n => typeCounts[n.type]=(typeCounts[n.type]||0)+1);
const types = Object.keys(typeCounts).sort();
$("filters").innerHTML = types.map(t =>
  `<label><span class="sw" style="background:${color(t)}"></span>
   <input type="checkbox" data-t="${t}" checked> ${t}<span class="ct">${typeCounts[t]}</span></label>`).join("");
document.querySelectorAll("[data-t]").forEach(cb => cb.onchange = () => {
  cb.checked ? hidden.delete(cb.dataset.t) : hidden.add(cb.dataset.t); });

const edgeCounts = {}; edges.forEach(e => edgeCounts[e.type]=(edgeCounts[e.type]||0)+1);
const etypes = Object.keys(edgeCounts).sort();
$("efilters").innerHTML = etypes.map(t =>
  `<label><span class="ln" style="border-color:${edgeColor(t)}"></span>
   <input type="checkbox" data-e="${t}" checked> ${t}<span class="ct">${edgeCounts[t]}</span></label>`).join("");
document.querySelectorAll("[data-e]").forEach(cb => cb.onchange = () => {
  cb.checked ? hiddenE.delete(cb.dataset.e) : hiddenE.add(cb.dataset.e); });

$("ntoggle").onclick = () => toggleAll("[data-t]", hidden, t=>t.dataset.t);
$("etoggle").onclick = () => toggleAll("[data-e]", hiddenE, t=>t.dataset.e);
function toggleAll(sel, set, key){ const boxes=[...document.querySelectorAll(sel)];
  const any=boxes.some(b=>b.checked); boxes.forEach(b=>{ b.checked=!any;
    !any ? set.delete(key(b)) : set.add(key(b)); }); }

$("cmode").onchange = e => colorMode = e.target.value;
$("q").oninput = e => { query = e.target.value.toLowerCase(); updateHits(); };
$("slink").oninput = e => linkDist = +e.target.value;
$("scharge").oninput = e => charge = +e.target.value;
$("bpause").onclick = () => { running=!running; $("bpause").textContent = running?"Pause":"Resume";
  $("bpause").classList.toggle("on",!running); if(running) draw(); };
$("blabels").onclick = () => { showLabels=!showLabels; $("blabels").classList.toggle("on",showLabels); };
$("bfit").onclick = fit; $("breset").onclick = () => { view={x:0,y:0,k:1}; };
$("bfocus").onclick = () => { if(selected) setFocus(selected); };
$("bclear").onclick = clearFocus;
$("bcopy").onclick = () => selected && copy(nodeMarkdown(byId[selected]), "node copied");
$("bexport").onclick = () => copy(graphMarkdown(), "visible graph copied");

function updateHits(){ if(!query){ $("qhits").textContent=""; return; }
  const m = nodes.filter(n => match(n)).length; $("qhits").textContent = `${m} match`; }
const match = n => query && (n.label.toLowerCase().includes(query) || n.id.toLowerCase().includes(query));

// ---- layout & geometry --------------------------------------------------
function resize(){ cv.width = innerWidth-SIDE; cv.height = innerHeight; } resize(); onresize = resize;
const inFocus = n => !focusSet || focusSet.has(n.id);
const visible = n => !hidden.has(n.type) && inFocus(n);
const eVisible = e => !hiddenE.has(e.type) && visible(byId[e.source]) && visible(byId[e.target]);

// Physics runs every PHYS_STRIDE render frames so rendering stays at ≥30 fps
// even when the simulation is expensive (large graphs).
const PHYS_STRIDE = nodes.length > 600 ? 2 : 1;
let _drawFrame = 0;

function step(){
  const vis = nodes.filter(visible);
  // Process each pair once (i<j) and apply equal-and-opposite forces to both
  // nodes — halves the O(n²) work vs the naive double-loop.
  for (let i=0; i<vis.length; i++){
    const a=vis[i];
    for (let j=i+1; j<vis.length; j++){
      const b=vis[j];
      let dx=a.x-b.x, dy=a.y-b.y, d=Math.hypot(dx,dy)||1;
      if(d<280){ const f=charge/(d*d*d);
        a.vx+=dx*f; a.vy+=dy*f; b.vx-=dx*f; b.vy-=dy*f; } } }
  for (const e of edges){ if(!eVisible(e)) continue; const a=byId[e.source], b=byId[e.target];
    let dx=b.x-a.x, dy=b.y-a.y, d=Math.hypot(dx,dy)||1, f=(d-linkDist)*0.01;
    a.vx+=dx/d*f; a.vy+=dy/d*f; b.vx-=dx/d*f; b.vy-=dy/d*f; }
  for (const n of vis){ n.vx*=.85; n.vy*=.85; n.x+=n.vx*0.5; n.y+=n.vy*0.5;
    n.vx-=n.x*0.0007; n.vy-=n.y*0.0007; }
}
const T = n => ({ x: n.x*view.k+cv.width/2+view.x, y: n.y*view.k+cv.height/2+view.y });
const radius = n => Math.min(4+(deg[n.id]||0)*0.8, 16)*view.k;
const neighbors = id => new Set(adj[id].map(([t])=>t));

function fit(){ const vis = nodes.filter(visible); if(!vis.length) return;
  const xs=vis.map(n=>n.x), ys=vis.map(n=>n.y);
  const minX=Math.min(...xs),maxX=Math.max(...xs),minY=Math.min(...ys),maxY=Math.max(...ys);
  const w=maxX-minX||1, h=maxY-minY||1;
  view.k = Math.max(0.2, Math.min(2.5, 0.85*Math.min(cv.width/w, cv.height/h)));
  view.x = -(minX+maxX)/2*view.k; view.y = -(minY+maxY)/2*view.k; }

function setFocus(id){ focusSet = new Set([id, ...neighbors(id)]); }
function clearFocus(){ focusSet = null; }

// ---- render -------------------------------------------------------------
function draw(){
  _drawFrame++;
  if(running && _drawFrame % PHYS_STRIDE === 0) step();
  ctx.clearRect(0,0,cv.width,cv.height);
  const near = selected ? neighbors(selected) : (hover ? neighbors(hover) : null);
  const anchor = selected || hover;
  for (const e of edges){ if(!eVisible(e)) continue; const a=byId[e.source], b=byId[e.target];
    const on = !anchor || e.source===anchor || e.target===anchor;
    ctx.globalAlpha = on ? 0.9 : 0.12; ctx.strokeStyle = edgeColor(e.type);
    ctx.lineWidth = on ? 1.4 : 0.8;
    const p=T(a), q=T(b); ctx.beginPath(); ctx.moveTo(p.x,p.y); ctx.lineTo(q.x,q.y); ctx.stroke();
    if(on && view.k>0.7) arrow(p,q,radius(b)); }
  ctx.globalAlpha=1;
  for (const n of nodes){ if(!visible(n)) continue; const p=T(n), r=radius(n);
    const dim = (anchor && near && !near.has(n.id) && n.id!==anchor) || (query && !match(n));
    ctx.globalAlpha = dim ? 0.18 : 1; ctx.fillStyle = nodeColor(n);
    ctx.beginPath(); ctx.arc(p.x,p.y,r,0,7); ctx.fill();
    if(n.id===selected){ ctx.strokeStyle="#fff"; ctx.lineWidth=2; ctx.stroke(); }
    else if(query && match(n)){ ctx.strokeStyle="#ffd33d"; ctx.lineWidth=2; ctx.stroke(); }
    if(showLabels && (view.k>1.1 || n.id===anchor || (near&&near.has(n.id)) || (query&&match(n)))){
      ctx.globalAlpha = dim?0.2:0.95; ctx.fillStyle="#c9d1d9"; ctx.font="10px ui-sans-serif";
      ctx.fillText(n.label, p.x+r+3, p.y+3); } }
  ctx.globalAlpha=1; requestAnimationFrame(draw);
}
function arrow(p,q,rad){ const a=Math.atan2(q.y-p.y,q.x-p.x), ex=q.x-Math.cos(a)*rad, ey=q.y-Math.sin(a)*rad;
  ctx.beginPath(); ctx.moveTo(ex,ey);
  ctx.lineTo(ex-Math.cos(a-0.4)*6, ey-Math.sin(a-0.4)*6);
  ctx.lineTo(ex-Math.cos(a+0.4)*6, ey-Math.sin(a+0.4)*6); ctx.closePath();
  ctx.fillStyle=ctx.strokeStyle; ctx.fill(); }

// ---- interaction --------------------------------------------------------
function hit(mx,my){ for(const n of nodes){ if(!visible(n)) continue; const p=T(n);
  if(Math.hypot(mx-p.x,my-p.y) < radius(n)+3) return n; } }
let drag=null, pan=false, last=null;
cv.onmousedown = e => { const n=hit(e.offsetX,e.offsetY);
  if(n){ drag=n; selected=n.id; showDetail(n); } else { pan=true; selected=null; clearDetail(); }
  last={x:e.offsetX,y:e.offsetY}; };
cv.onmousemove = e => { const n=hit(e.offsetX,e.offsetY); hover = n?n.id:null;
  if(n && !drag){ tip.style.display="block"; tip.style.left=(e.clientX+12)+"px"; tip.style.top=(e.clientY+12)+"px";
    tip.innerHTML = `<b>${esc(n.label)}</b> · ${n.type}`+(n.file?`<br>${esc(n.file)}${n.line?":"+n.line:""}`:"")+
      `<br>${deg[n.id]||0} edges`; }
  else if(!drag) tip.style.display="none";
  if(drag){ drag.x+=(e.offsetX-last.x)/view.k; drag.y+=(e.offsetY-last.y)/view.k; drag.vx=drag.vy=0; }
  else if(pan){ view.x+=e.offsetX-last.x; view.y+=e.offsetY-last.y; }
  last={x:e.offsetX,y:e.offsetY}; };
onmouseup = () => { drag=null; pan=false; };
cv.ondblclick = e => { const n=hit(e.offsetX,e.offsetY); if(n){ selected=n.id; setFocus(n.id); showDetail(n); } };
cv.onwheel = e => { e.preventDefault(); const f=e.deltaY<0?1.1:0.9;
  const mx=e.offsetX-cv.width/2-view.x, my=e.offsetY-cv.height/2-view.y;
  view.k=Math.max(0.15,Math.min(5,view.k*f)); view.x-=mx*(f-1); view.y-=my*(f-1); };

onkeydown = e => { if(e.target.tagName==="INPUT"||e.target.tagName==="SELECT"){ if(e.key==="Escape")e.target.blur(); return; }
  const k=e.key.toLowerCase();
  if(k==="/"){ e.preventDefault(); $("q").focus(); }
  else if(k==="f") fit(); else if(k==="r") view={x:0,y:0,k:1};
  else if(k===" "){ e.preventDefault(); $("bpause").click(); }
  else if(k==="e"){ if(selected) setFocus(selected); }
  else if(k==="l") $("blabels").click();
  else if(k==="escape"){ clearFocus(); selected=null; clearDetail(); } };

// ---- detail panel + agent export ---------------------------------------
function showDetail(n){ $("agentrow").style.display="flex";
  const groups={}; for(const [tid,e,dir] of adj[n.id]){ (groups[e.type]=groups[e.type]||[])
    .push({id:tid,dir,sym:dir>0?"→":"←"}); }
  let meta = `<b>${esc(n.label)}</b><br><span class="muted">${n.type}`+
    (n.file?` · ${esc(n.file)}${n.line?":"+n.line:""}`:"")+`</span><br>`;
  const pills=[]; if(n.domain)pills.push(n.domain); if(n.layer)pills.push(n.layer);
  if(n.status)pills.push(n.status); if(n.community!=null)pills.push("community "+n.community);
  pills.push((deg[n.id]||0)+" edges");
  meta += pills.map(p=>`<span class="pill">${esc(p)}</span>`).join("")+"<br>";
  for(const t of Object.keys(groups).sort()){ meta += `<br><span class="muted">${t}</span><br>`+
    groups[t].slice(0,40).map(x=>`<span class="nb" data-go="${esc(x.id)}">${x.sym} ${esc(byId[x.id].label)}</span>`).join("<br>"); }
  $("detail").innerHTML = meta;
  $("detail").querySelectorAll("[data-go]").forEach(el => el.onclick = () => {
    selected = el.dataset.go; showDetail(byId[selected]);
    const p=byId[selected]; view.x=-p.x*view.k; view.y=-p.y*view.k; }); }
function clearDetail(){ $("agentrow").style.display="none";
  $("detail").innerHTML="Click a node. Double-click to focus its neighbourhood."; }

function nodeMarkdown(n){ let s=`### ${n.label} (${n.type})\n`;
  if(n.file)s+=`- file: ${n.file}${n.line?":"+n.line:""}\n`;
  for(const f of ["domain","layer","status","community"]) if(n[f]!=null) s+=`- ${f}: ${n[f]}\n`;
  s+=`- degree: ${deg[n.id]||0}\n\n**Connections**\n`;
  for(const [tid,e,dir] of adj[n.id]) s+=`- ${e.type} ${dir>0?"→":"←"} ${byId[tid].label} (${byId[tid].type})\n`;
  return s; }
function graphMarkdown(){ const vis=nodes.filter(visible);
  let s=`# Fux graph (visible subset)\n${vis.length} nodes, `+
    edges.filter(eVisible).length+` edges\n\n## Nodes by type\n`;
  const byT={}; vis.forEach(n=>(byT[n.type]=byT[n.type]||[]).push(n.label));
  for(const t of Object.keys(byT).sort()) s+=`- **${t}** (${byT[t].length}): ${byT[t].slice(0,30).join(", ")}\n`;
  s+=`\n## Edges\n`; edges.filter(eVisible).slice(0,200).forEach(e=>
    s+=`- ${byId[e.source].label} —${e.type}→ ${byId[e.target].label}\n`);
  return s; }
function copy(text,msg){ navigator.clipboard?.writeText(text).then(()=>toast(msg),()=>toast("copy blocked")); }
function toast(m){ const t=$("toast"); t.textContent=m; t.style.display="block";
  clearTimeout(t._h); t._h=setTimeout(()=>t.style.display="none",1500); }
const esc = s => String(s).replace(/[&<>]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;"}[c]));

fit(); draw();
