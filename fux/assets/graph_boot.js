// Force-directed canvas viewer — vanilla, offline, no deps.
const cv = document.getElementById("cv"), ctx = cv.getContext("2d");
const tip = document.getElementById("tip");
const nodes = DATA.nodes.map(n => ({ ...n, x: Math.random()*800-400, y: Math.random()*800-400, vx:0, vy:0 }));
const byId = Object.fromEntries(nodes.map(n => [n.id, n]));
const edges = DATA.edges.filter(e => byId[e.source] && byId[e.target]);
const deg = {}; edges.forEach(e => { deg[e.source]=(deg[e.source]||0)+1; deg[e.target]=(deg[e.target]||0)+1; });
let view = { x: 0, y: 0, k: 1 }, hidden = new Set(), selected = null, query = "";

document.getElementById("stats").textContent =
  `${nodes.length} nodes · ${edges.length} edges · ${DATA.meta.code_files} code files · ${DATA.meta.rules} rules`;
const types = [...new Set(nodes.map(n => n.type))].sort();
document.getElementById("filters").innerHTML = types.map(t =>
  `<label><span class="sw" style="background:${color(t)}"></span>
   <input type="checkbox" data-t="${t}" checked> ${t}</label>`).join("");
document.querySelectorAll("[data-t]").forEach(cb => cb.onchange = () => {
  cb.checked ? hidden.delete(cb.dataset.t) : hidden.add(cb.dataset.t); });
document.getElementById("q").oninput = e => query = e.target.value.toLowerCase();

function resize(){ cv.width = innerWidth-260; cv.height = innerHeight; } resize(); onresize = resize;
function visible(n){ return !hidden.has(n.type); }

function step(){
  for (const a of nodes){ if(!visible(a)) continue;
    for (const b of nodes){ if(a===b||!visible(b)) continue;
      let dx=a.x-b.x, dy=a.y-b.y, d=Math.hypot(dx,dy)||1;
      if(d<260){ const f=900/(d*d); a.vx+=dx/d*f; a.vy+=dy/d*f; } } }
  for (const e of edges){ const a=byId[e.source], b=byId[e.target];
    if(!visible(a)||!visible(b)) continue;
    let dx=b.x-a.x, dy=b.y-a.y, d=Math.hypot(dx,dy)||1, f=(d-70)*0.01;
    a.vx+=dx/d*f; a.vy+=dy/d*f; b.vx-=dx/d*f; b.vy-=dy/d*f; }
  for (const n of nodes){ n.vx*=.85; n.vy*=.85; n.x+=n.vx*0.5; n.y+=n.vy*0.5;
    n.vx-=n.x*0.0008; n.vy-=n.y*0.0008; }
}
function T(n){ return { x: n.x*view.k+cv.width/2+view.x, y: n.y*view.k+cv.height/2+view.y }; }
const neighbors = id => new Set(edges.filter(e=>e.source===id||e.target===id)
  .flatMap(e=>[e.source,e.target]));

function draw(){
  step(); ctx.clearRect(0,0,cv.width,cv.height);
  const near = selected ? neighbors(selected) : null;
  ctx.lineWidth = 1;
  for (const e of edges){ const a=byId[e.source], b=byId[e.target];
    if(!visible(a)||!visible(b)) continue;
    const on = !selected || (e.source===selected||e.target===selected);
    ctx.strokeStyle = on ? "#3a4150" : "#20262e"; ctx.beginPath();
    const p=T(a), q=T(b); ctx.moveTo(p.x,p.y); ctx.lineTo(q.x,q.y); ctx.stroke(); }
  for (const n of nodes){ if(!visible(n)) continue; const p=T(n);
    const r=Math.min(4+(deg[n.id]||0)*0.8,14)*view.k;
    const dim = (selected && near && !near.has(n.id) && n.id!==selected) ||
                (query && !n.label.toLowerCase().includes(query) && !n.id.toLowerCase().includes(query));
    ctx.globalAlpha = dim ? 0.2 : 1; ctx.fillStyle = color(n.type);
    ctx.beginPath(); ctx.arc(p.x,p.y,r,0,7); ctx.fill();
    if(n.id===selected){ ctx.strokeStyle="#fff"; ctx.lineWidth=2; ctx.stroke(); }
    if(view.k>1.1 || n.id===selected){ ctx.globalAlpha=dim?0.2:0.9; ctx.fillStyle="#c9d1d9";
      ctx.font="10px sans-serif"; ctx.fillText(n.label, p.x+r+2, p.y+3); } }
  ctx.globalAlpha=1; requestAnimationFrame(draw);
}
function hit(mx,my){ for(const n of nodes){ if(!visible(n)) continue; const p=T(n);
  if(Math.hypot(mx-p.x,my-p.y) < Math.min(4+(deg[n.id]||0)*0.8,14)*view.k+3) return n; } }
let drag=null, pan=false, last=null;
cv.onmousedown = e => { const n=hit(e.offsetX,e.offsetY); if(n){ drag=n; selected=n.id; showDetail(n); }
  else { pan=true; selected=null; document.getElementById("detail").innerHTML="Click a node to inspect."; }
  last={x:e.offsetX,y:e.offsetY}; };
cv.onmousemove = e => { const n=hit(e.offsetX,e.offsetY);
  if(n && !drag){ tip.style.display="block"; tip.style.left=(e.clientX+10)+"px";
    tip.style.top=(e.clientY+10)+"px"; tip.textContent=`${n.label} · ${n.type}`; }
  else if(!drag) tip.style.display="none";
  if(drag){ drag.x+=(e.offsetX-last.x)/view.k; drag.y+=(e.offsetY-last.y)/view.k; drag.vx=drag.vy=0; }
  else if(pan){ view.x+=e.offsetX-last.x; view.y+=e.offsetY-last.y; }
  last={x:e.offsetX,y:e.offsetY}; };
onmouseup = () => { drag=null; pan=false; };
cv.onwheel = e => { e.preventDefault(); view.k = Math.max(0.2, Math.min(4, view.k*(e.deltaY<0?1.1:0.9))); };
function showDetail(n){ const nb=[...neighbors(n.id)].filter(i=>i!==n.id);
  document.getElementById("detail").innerHTML =
    `<b>${n.label}</b><br><span class="muted">${n.type}${n.file?" · "+n.file:""}`+
    `${n.line?":"+n.line:""}</span><br><br>${nb.length} neighbor(s):<br>`+
    nb.slice(0,30).map(i=>`· ${byId[i].label}`).join("<br>"); }
draw();
