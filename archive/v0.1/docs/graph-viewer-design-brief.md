# Fux Graph Viewer — Design Brief

> A handoff document for a redesign. It describes what the Fux graph viewer is,
> the data it shows, everything it can currently do, how it looks today, where it
> falls short, and the hard constraints any new design must respect. No code
> knowledge is assumed.

---

## 1. What it is

The Fux graph viewer is a **single, self-contained HTML file** (`graph.html`) that
renders an interactive, force-directed **knowledge graph of a software codebase
merged with its documentation/rules**. It is generated offline by the `fux` tool
and opened directly in a browser (`file://`) — no server, no internet, no build.

It answers questions like:
- *How is this codebase structured?* (modules, hubs, clusters)
- *What calls/references what?* (code dependencies)
- *Which rules/specs/memories govern which code?* (the knowledge↔code link)
- *What's the shortest path between two things?*

Two audiences use it: a **human developer** exploring/reviewing the codebase, and
an **AI coding agent** that needs to extract a subgraph as text. Both matter.

---

## 2. The data it visualizes

A real example graph (one mid-size project): **1,513 nodes · 7,048 edges · 162
communities**. Designs must look good at this scale (1k–5k nodes), not just 50.

**Nodes** — each has:
| Attribute | Meaning | Notes |
|---|---|---|
| `type` | one of ~16 kinds | dominated by `function` (≈60%) and `code-file` |
| `community` | cluster id (0–161) | **one community held 842 nodes (56%)** — very uneven |
| `centrality` | structural importance 0–1 | drives node size; top ~1.5% are "hub/god" nodes |
| `label` | short display name | e.g. `run_migrations_offline` |
| `file`, `line` | source location | code nodes only |
| `layer`, `domain`, `status` | knowledge metadata | rules/specs/memories only |

Node types: `code-file`, `function`, `class` (code) · `rule`, `formula`,
`glossary`, `invariant`, `adr`, `edge-case`, `convention`, `regulatory`,
`runbook`, `narrative`, `memory`, `spec`, `task` (knowledge).

**Edges** — directed, typed. Real counts from the example:
`references` 4,025 · `calls` 1,856 · `contains` 1,150 · `related` 12 · `governs` 5.
Other possible types: `depends-on`, `supersedes`, `contradicts`, `implements`.

> ⚠️ **Critical data shape:** the graph is ~99% code-to-code edges. Only **17 of
> 7,048 edges** connect the knowledge layer to code. The knowledge nodes are a
> tiny, weakly-attached island. A good design must make a sparse, important
> minority (rules) findable inside an overwhelming majority (code).

---

## 3. Current visual design (what it looks like today)

**Layout:** fixed **left sidebar (290px)** + full-bleed **canvas** filling the rest.
A floating keyboard-hint bar sits top-right; a hover tooltip and a bottom toast
appear transiently.

**Theme:** GitHub-dark-dimmed. Tokens:
```
--bg     #0e1116   (canvas + page background)
--panel  #161b22   (sidebar)
--line   #30363d   (borders)
--fg     #e6edf3   (text)
--muted  #8b949e   (secondary text)
--accent #58a6ff   (interactive / focus blue)
```
Font: `13px ui-sans-serif, system-ui` (system font; **no web fonts** allowed).

**Sidebar sections, top to bottom:**
1. Title + logo, one-line stats (`1513 nodes · 7048 edges · …`)
2. Search box → **clickable result list** (swatch + label + type)
3. "Colour by" dropdown: node type / community / rule layer / degree-heat
4. Button row: Fit · Reset · Pause · Labels
5. Button row: Focus sel. · Unfocus
6. Button row: Clusters · Rules (lens) · Path
7. Two sliders: link distance, charge (repulsion strength)
8. Node-type filter checkboxes (with per-type colour swatch + count)
9. Edge-type filter checkboxes (with per-type colour line + count)
10. "Inspect" detail panel (selected node's metadata + grouped neighbours)
11. Copy-node / Copy-visible-graph buttons (markdown export)

**Canvas rendering:**
- Nodes = filled circles. Radius = blend of centrality + degree (3–20px). Top
  centrality nodes get a faint same-colour halo ring.
- Node colour driven by the "Colour by" mode. Node-type palette (the busy part):
  `function #3fb950` (green), `code-file #7d8590` (grey), `class #a371f7`
  (purple), `rule #58a6ff` (blue), `invariant #f85149` (red), `memory #f0883e`
  (orange), `narrative #bc8cff` (lilac)… ~16 colours total.
- Edges = thin straight lines, colour by edge type. Drawn **whisper-faint at
  rest** (structural `contains` at ~0.05 alpha) and brightened only around the
  hovered/selected node. Directed arrowheads appear when zoomed in.
- Labels: shown only when zoomed in, or for hubs / search hits / selection.
- Community names float over each cluster's centroid when zoomed out.

**Semantic-zoom (macro view):** when zoomed out past a threshold, the 1,513 nodes
collapse into **162 community "super-nodes"** arranged organically, each sized by
membership and labelled by its most-central member, with faint aggregated links.
Click a super-node to drill into that community. Zoom in to expand back to nodes.

---

## 4. Everything it can do (capability inventory)

**Navigate**
- Pan (drag canvas), zoom (wheel/trackpad/pinch — delta-proportional and eased so
  it glides rather than stepping), drag the zoom-well slider to scrub zoom live,
  Fit-to-view, Reset view. All button/search/ledger recentres animate (camera
  tween); direct manipulation — pan, node-drag, slider — stays 1:1.
- Drag individual nodes to reposition; physics re-settles around them.
- Pause/resume the force simulation.
- Semantic zoom: macro community map ⇄ micro node view by zoom level.

**Focus & filter**
- Toggle visibility per node type and per edge type (with live counts).
- "Focus selection": isolate a node + its neighbours; "Unfocus" to restore.
- Double-click a node to focus its neighbourhood.

**Colour / encode**
- Colour by: node type · community · rule layer (project/global) · degree (heat).
- Node size encodes structural importance (centrality); hubs get a halo.

**Search**
- Type to filter; matches listed as a **clickable dropdown**; click → select +
  centre that node. Matches also highlight on the canvas.

**Inspect**
- Click a node → detail panel: label, type, file:line, domain/layer/status pills,
  community, degree, hub flag, and neighbours grouped by edge type (each clickable
  to hop). For code nodes, a "⚖ governed by" section lists linked rules first (or
  says none are linked).
- Hover → tooltip with label, type, file, edge count.

**Specialised lenses**
- **Rules lens:** isolate the knowledge layer + only the code it touches — makes
  the sparse rule↔code linkage visible at a glance.
- **Path mode:** click node A then node B → shortest path highlighted on canvas
  and listed in the panel.

**Export (for AI agents / docs)**
- Copy a node + its neighbourhood as markdown.
- Copy the entire visible subgraph as markdown.
- Copy the highlighted path as markdown.

**Keyboard:** `/` search · `+`/`-` zoom · `f` fit · `r` reset · `space` pause ·
`e` focus · `c` clusters · `p` path · `Esc` clear · `l` labels.

---

## 5. Where it falls short (design goals)

These are the honest problems a better design should address:

1. **One node type drowns the rest.** ~60% of nodes are green `function`s, so
   colour-by-type reads as a green blob. The visually important minority (rules,
   invariants, ADRs) gets lost.
2. **Communities are uneven.** Colour-by-community is dominated by one giant
   cluster (842/1513). Hard to perceive structure. (Partly a data problem, but the
   design should degrade gracefully when one cluster dominates.)
3. **Dense centre / readability.** Even with tuning, the hub region is crowded;
   distinguishing individual nodes and following edges is hard at full zoom-out.
4. **Sidebar is cramped.** 11 stacked sections in 290px; controls, filters, and
   the inspect panel compete for space. Information hierarchy is flat.
5. **Edges carry little meaning visually.** 5+ edge types but they mostly read as
   faint grey lines; the type distinction (calls vs references vs governs) is lost.
6. **No overview/minimap** when zoomed into a subgraph — easy to get lost.
7. **The knowledge↔code story is buried.** The single most valuable thing (which
   rules govern which code) is a tiny minority and not surfaced by default.
8. **Two modes feel disjoint** — the macro community map and the micro node graph
   could transition more fluidly / share more visual language.
9. **Aesthetics are utilitarian** — functional GitHub-dark, but not memorable or
   delightful; spacing, type scale, and motion are minimal.

**Things to preserve (they work well):**
- Offline, instant, self-contained.
- Faint-edges-until-hover keeps the canvas calm.
- Clickable search results and clickable neighbours for fast hopping.
- Semantic zoom is genuinely useful at scale.
- Agent markdown export.

---

## 6. Hard constraints (a redesign MUST respect these)

- **Single self-contained `.html` file.** All CSS/JS inline. **No CDN, no web
  fonts, no external assets, no network at runtime.** It opens from `file://`.
- **Canvas-based rendering for the graph.** At 1k–5k nodes, per-node DOM/SVG
  elements are too slow. The node/edge field must stay on `<canvas>` (2D). UI
  chrome (sidebar, panels, tooltips) can be DOM/CSS.
- **System fonts only** (`ui-sans-serif` / `system-ui`).
- **Dark theme is the baseline** (light theme optional, not required).
- **Performance:** smooth pan/zoom and a live force simulation at ≥30fps with
  ~1,500 nodes on a laptop. Keep per-frame work O(n) where possible.
- **Works for both a human and an agent** — the agent path is text export, so the
  data model and "what's currently visible" must remain inspectable.
- **No build step / framework dependency** is preferred (today it's vanilla JS).
  A redesign can introduce structure but should not require a toolchain to view.

---

## 7. What I'd love a redesign to deliver

Open-ended — propose freely, but priorities:
1. A visual system that makes a **dominant majority + sparse important minority**
   legible at once (the function-soup + rare-rules problem).
2. A clearer **information hierarchy** for the sidebar/controls (maybe collapsible
   sections, tabs, or a command palette).
3. A more **meaningful edge language** (so calls vs governs vs references read
   differently without becoming noisy).
4. A **fluid macro↔micro** experience (community map ↔ node graph).
5. A first-class way to spotlight the **code⊕knowledge** relationship.
6. Overall **polish**: type scale, spacing, motion, empty/hover/selected states,
   and a distinctive but calm aesthetic suited to long exploration sessions.

Deliverables welcome in any form: annotated mockups, a component/token system, a
redesigned sidebar layout, canvas treatment ideas, interaction flows, or a moodboard.
