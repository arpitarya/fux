# Claude Code prompt: Fux master build orchestrator (one PR at a time, publish, next)

**Supersedes `docs/prompt-replace-graphify-obsidian.md`** — same engine, wider queue.
You execute a fixed queue of build items **one at a time**. For each: implement → test in
the dummy repo → open a PR → (I merge) → publish the package → next. The end-state:
Fux covers everything I used **Graphify** and **Obsidian** for *and* ships the four
capabilities I explicitly asked to build (multi-assistant, connectors, global-graph,
build cache), after which Graphify is removed from my workflow.

Read this whole prompt, then read `CLAUDE.md`, and confirm the queue with me before any code.

## Ground truth (established this session — do not re-derive)

- Package **`fux-engine`**, version = `fux.__version__`, release via
  **`.github/workflows/publish.yml`** (tag/release-triggered). Never `twine` push by hand.
- Build is fast (**~3s at 28k nodes, measured**); the 23k-node pain is the **browser
  viewer**, not the engine. The build cache saves only ~25% of that ~3s — real but modest.
- **No Graphify query log / `~/.graphify`** exists → parity is proven by a live head-to-head
  run on this repo, not a log replay.
- Fux **already** carries edge-confidence labels and `source_type: jira|confluence|openapi`
  in its schema — several items below *complete a half-built pattern*, not greenfield.
- Field-level specs already written — use them, don't reinvent:
  `docs/handoff-01-parity-command.md`, `docs/handoff-02-multi-assistant.md`,
  `docs/handoff-03-graph-scale.md`, `docs/handoff-04-org-connectors.md`,
  `docs/prompt-03a-viewer-scale.md`, `docs/fux-vs-graphify-parity-matrix.md`,
  `docs/graphify-obsidian-inspiration.md`, `docs/fux-roadmap-implementation-spec.md`,
  `docs/fux-lab-handoff.md`.

## Two hard truths (non-negotiable)

1. **You cannot self-merge.** Fux's wall requires `fux gate` + `ai-review`; `ai-review`
   refuses when reviewer == author. Each item ends at "PR open, checks green." **I merge.**
2. **Publishing to PyPI is irreversible/public.** Prepare the release (version bump +
   changelog in the PR); after I merge, push the release tag **only on my explicit confirm**.
   `publish.yml` uploads. Never publish unasked.

## The queue (ordered — confirm/adjust with me first)

Each item = one branch = one PR = one release. Resolve its spec's OPEN QUESTIONS **before**
coding it (the loop enforces this). The residual-risk note on each is the thing to settle first.

**Q0 — `fux-lab` harness.** Spec: `docs/fux-lab-handoff.md`. The dummy repo every later item
is tested in. No publish (test fixture, not shipped) — just merge.

**Q1 — Native navigable graph (replaces Graphify `graph.html` + Obsidian).** Spec:
`docs/prompt-03a-viewer-scale.md` + inspiration doc. Viewer level-of-detail (never render all
nodes), ego-graph focus view, backlinks in `why`/`serve`, `[[wikilink]]`→`related` resolution
at build, `fux build --profile`. *Residual:* the viewer must not mutate `graph.json`; default
build stays byte-identical.

**Q2 — Build cache + incremental recompute (03b).** Spec: `docs/handoff-03-graph-scale.md`.
Per-file extraction cache keyed by content hash + extractor version; `affected`-style recompute;
`--force`/`--full` bypass. *Residual (settle first):* determinism — cached/incremental build
MUST be byte-identical to a full build (ship the proving test); and confirm community indices
stay stable across incremental builds. Note it saves ~25% of a ~3s build — value is CI/hook
latency, not the 23k UX (that was Q1).

**Q3 — Export parity (removes Graphify's export edge).** Parity matrix row 9. Deterministic
serializers of `graph.json`: **GraphML** + **Neo4j/Cypher** (+ **SVG** if cheap). `$0`, no new
deps. Skip network *push* variants or gate behind an extra.

**Q4 — Doc/media ingest edge cases.** Everything Graphify extracted from docs/PDFs/images →
Fux's host-agent `ingest` skill → draft rules (engine stays `$0`; model = host session, never
engine). *Residual:* **video/audio is out** (needs a model + heavy deps) — record it as a
documented residual gap, don't fake it. Obsidian-vault export stays optional (Q1 makes Fux
self-sufficient for navigation).

**Q5 — Connectors: Jira / Confluence / Swagger (04a).** Spec: `docs/handoff-04-org-connectors.md`.
Complete the ingest pattern (OpenAPI already works) → draft rules with provenance, read-only.
*Residual (settle first):* prefer an existing **MCP connector** for auth vs skill-fetch; and add
a **visible staleness signal** (a `check`/`lint` advisory when a `source_type: jira|confluence`
rule hasn't been re-checked in N days) so ingested governance "why" can't silently rot.

**Q6 — Cross-repo global graph (04b).** `fux global` merges per-repo `graph.json` into
`~/.fux/global-graph.json` + manifest, with a cross-repo query path (graphify `global_graph.py`
shape). *Residual:* deterministic merge; corrupt-manifest backs up, never wipes.

**Q7 — Multi-assistant surface (02).** Spec: `docs/handoff-02-multi-assistant.md`. Extend
`skillgen` (`platforms.toml` + fragments) + `fux hooks` to **exactly these five surfaces I
use: Claude Code, Claude Cowork, Copilot, Kiro, Codex** — no others (don't add Cursor/Aider/
Gemini/etc. on spec). Claude Code + Codex + Copilot already have partial wiring (`fux hooks`,
skillgen) — verify/complete them. **Kiro** is net-new (`.kiro/skills/` + `.kiro/steering/fux.md`,
graphify's layout). Payload-hook platforms (Claude Code; Codex PreToolUse) get the live
pre-search hook; steering-only platforms (Copilot-VS-Code, Kiro) get an always-on query-first
instruction file. *Residual (settle first):* **Claude Cowork** wiring mechanism — most likely
identical to Claude Code (skills + MCP + hooks); confirm with me before implementing it rather
than guessing. A *true* VS Code Marketplace extension stays out unless I ask separately (a
Copilot-VS-Code steering install is in).

**Q8 — Prove parity on THIS repo (removal gate).** Spec: `docs/handoff-01-parity-command.md`,
adapted: no log, so run Fux vs Graphify head-to-head on this repo → removal-readiness report,
two sub-scores never blended (graph-parity vs fux-only governance). **Do not proceed to Q9 until
this reports ready** (or I override).

**Q9 — Remove Graphify + drop Obsidian (the objective).** Only after Q8 green: uninstall the
Graphify tool + its footprint (`graphify-out/`, `graphify install` files under `.cursor`/`.kiro`/
skills/MCP, CI/pre-commit refs, the Obsidian-export habit). **Edge-case sweep:** grep the repo(s)
for `graphify`/`obsidian`; migrate each to the Fux equivalent or record why it's dropped.
`fux gate` green. This touches my environment — **I run the uninstall**; you prepare it, verify
coverage, and hand me the commands + residual-gap list.

Running checklist in every PR + back to me: `[ ] Q0 [ ] Q1 [ ] Q2 [ ] Q3 [ ] Q4 [ ] Q5 [ ] Q6 [ ] Q7 [ ] Q8 [ ] Q9`.

## The per-item loop (current item, in order)

1. **Load & decide.** Read the item's spec + OPEN QUESTIONS + its residual-risk note; get my
   answers **before coding**. Don't guess.
2. **Branch.** `git checkout main && git pull`; `feat/<item-slug>`.
3. **Explore → Plan → Confirm.** Explore real code; post a short plan (files, approach,
   fixtures); **pause for my confirmation.**
4. **Implement incrementally.** Small commits; build stays green; follow the spec's constraints.
5. **Test in `fux-lab`.** Extend fixtures + goldens + negative guards for the *new* surface.
   `python run_lab.py` + the offline `$0` sweep + `pytest`. All green.
6. **Docs (part of done).** Update what the spec's §9.5 names — `docs/fux-plan.md`,
   `docs/fux-implementation.md`, `docs/cli.md` (regenerate the registry table, don't hand-edit),
   README, whats-new. **Propose** CLAUDE.md/AGENTS.md edits for review — never auto-apply.
7. **Prepare release.** Bump `fux.__version__` (semver-appropriate) + changelog entry in the PR.
8. **Gate.** `fux gate`, `python -m pytest -q`, `python -m tools.skillgen --check`. Fix every red.
9. **Open PR (do not merge).** `gh` PR with objective + item, what changed, done-checklist ticked,
   `run_lab.py`/gate/parity evidence, version bump, proposed CLAUDE.md edits, queue checklist. **STOP.**
10. **I merge.** Tell me what to review (esp. determinism/constitution-sensitive diffs).
11. **Publish — on my explicit go.** After merge, ask me to confirm; on confirm, push the release
    tag so `publish.yml` uploads `fux-engine`; verify it on PyPI.
12. **Advance.** `git checkout main && git pull`, tick the queue, next item at step 1. When the
    queue is empty, summarize every PR + release + the residual-gap list, then stop.

## Hard constraints (every item)

- **Never merge; never bypass the wall.** **Never publish without my explicit confirmation.**
- **Constitution:** `$0`, stdlib-only, deterministic, **no LLM on any maintenance path**
  (doc/media extraction rides the host-agent `ingest` skill, never engine code). No new *required*
  deps — network/heavy paths behind opt-in extras. If an item seems to need otherwise, STOP and ask.
- **Determinism sacred** where graph output is touched: default `graph.json` byte-identical;
  cached/incremental == full build (Q2 proving test); viewer never mutates it; new modes opt-in.
- **Draft-only ingestion** (Q4/Q5): nothing auto-active, nothing auto-constitutional.
- **Generated skill artifacts** (Q7), never hand-authored; `skillgen --check` guards it.
- **Never edit the engine to make a test pass** — a real bug is a finding.
- **One item at a time.** Don't start the next branch until the current PR is merged + released.
- **Honesty over coverage:** if Fux genuinely can't cover a Graphify use (video), say so and
  record the residual gap — don't fake parity.
- **Ambiguity or constitution-touching change → STOP and ask.**

## First action

Do **not** code. Reply with: the confirmed queue + order; the answers you need from me on the
Q0 open questions **and** the residual-risk questions for Q2 (cache determinism / community-index
stability), Q5 (MCP vs skill for Jira/Confluence), and Q7 (confirm the Claude Cowork wiring
mechanism — the five target surfaces are fixed: Claude Code, Cowork, Copilot, Kiro, Codex); a
one-paragraph plan for Q0; and any Graphify use you suspect Fux can't cover. Then wait for my go.
