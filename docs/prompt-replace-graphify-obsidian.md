# Claude Code prompt: make Fux replace Graphify + Obsidian, one PR at a time

You are executing a fixed **objective**: get Fux to fully cover what I use **Graphify**
and **Obsidian** for on this repo — code+docs knowledge graph, navigable linked-note
browsing, and the edge cases — then **remove Graphify from my workflow**. You do this as
an ordered **queue**, one item at a time. For each item: implement → test in the dummy
repo → open a PR → (I merge) → publish the package → move to the next. Repeat until the
queue is empty and Graphify is gone.

Read this whole prompt, then read `CLAUDE.md` and confirm the queue with me before touching code.

## Ground truth (already established this session — do not re-derive)

- Package: **`fux-engine`**, version = `fux.__version__`, release via
  **`.github/workflows/publish.yml`** (tag/release-triggered). Do **not** `twine` push by hand.
- The **build is fast** (~3s at 28k nodes, measured); the 23k-node pain is the **browser
  viewer**, not the engine. So the graph work is **viewer/navigation**, not a rebuild cache.
- **No Graphify query log or `~/.graphify` exists**, so parity is proven by a **live
  head-to-head run on this repo**, not by replaying a log.
- Supporting detail lives in: `docs/fux-vs-graphify-parity-matrix.md` (what "replace" means
  + the removal checklist), `docs/graphify-obsidian-inspiration.md` (what to borrow),
  `docs/handoff-03-graph-scale.md`, `docs/prompt-03a-viewer-scale.md`,
  `docs/fux-roadmap-implementation-spec.md`. Use them as the field-level specs.

## Two hard truths you must respect (not negotiable)

1. **You cannot self-merge.** Fux's wall requires `fux gate` + `ai-review`, and `ai-review`
   refuses when reviewer == author. Your job on each item ends at "PR open, checks green."
   **I merge.** Never bypass the wall.
2. **Publishing to PyPI is irreversible and public.** You may *prepare* the release (version
   bump + changelog in the PR) and, after I merge, **push the release tag only after I
   explicitly confirm**. `publish.yml` does the actual upload. Never publish unasked.

## The queue (ordered — this is the path to removing Graphify + Obsidian)

Each item is scoped to close a specific gap that blocks removal. Confirm/adjust with me first.

**Q0 — Build the dummy repo (`fux-lab`) harness.** Spec: `docs/fux-lab-handoff.md` +
`docs/fux-lab-claude-code-prompt.md`. It is the repo every later item is tested in. No
package publish for Q0 (it's a test fixture, not shipped) — just merge it.

**Q1 — Native navigable graph (replaces Graphify's `graph.html` AND the need for Obsidian).**
Spec: `docs/prompt-03a-viewer-scale.md` + Obsidian borrows in the inspiration doc.
- Viewer **level-of-detail**: never render all nodes at once; community-collapsed above a
  threshold, expand on click.
- **Ego-graph** view: focus a rule/file/symbol → its 1–2 hop neighbourhood (reuse
  `query`/`explain`). This is the Obsidian-style "local graph" that removes the need to
  open an Obsidian vault to navigate.
- **Backlinks** (Obsidian's killer feature): surface "which rules link here" in `why`/`serve`.
- **`[[wikilink]]` resolution**: a `[[other-rule]]` in a rule body resolves to a `related`
  edge at build (deterministic — mirrors the memory convention). This makes Fux authoring
  feel like Obsidian without Obsidian.
- **`fux build --profile`**: per-phase timing, so scale claims stay measured.
- Determinism: the viewer must not change `graph.json`; default build stays byte-identical.

**Q2 — Export parity (removes Graphify's last graph advantage).** Spec: parity matrix row 9.
Add deterministic serializers of the existing `graph.json`: **GraphML** (Gephi/yEd) and
**Neo4j/Cypher**; **SVG** if cheap. Pure serialization, `$0`, no new deps. Skip the network
*push* variants (or gate behind an extra).

**Q3 — Doc/media ingest edge cases (the honest boundary).** Ensure everything Graphify
extracted from **docs/PDFs/images** on this repo is covered by Fux's **host-agent `ingest`
skill** → draft rules (engine stays `$0`; the model is the host session, never engine code).
- **Explicit edge case — video/audio:** Fux will **not** transcribe video deterministically
  (that's a model + heavy deps = out of constitution). If I actually rely on Graphify for
  video, that stays a documented residual gap — surface it, don't fake it.
- Obsidian-vault export stays **optional** (for when I *want* Obsidian), not required, since
  Q1 makes Fux self-sufficient for navigation.

**Q4 — Prove parity on THIS repo (the removal gate).** Spec: `docs/handoff-01-parity-command.md`,
adapted: since there's no query log, run Fux and Graphify **head-to-head on this repo** and
emit a **removal-readiness report** — for each way I use Graphify (map, query, path, explain,
report, export, browse), does Fux have a verified equivalent? Two sub-scores, never blended:
graph-parity (replaceable) vs the fux-only governance surface (why I keep Fux). **Do not
proceed to Q5 until this reports ready** (or I override).

**Q5 — Remove Graphify + drop Obsidian (the objective).** Only after Q4 is green:
- Uninstall the Graphify tool and remove its footprint from my workflow/repo: `graphify-out/`,
  any `graphify install`-written files (`.cursor/rules/*graphify*`, `.kiro/…`, skill/steering
  files, MCP entries), CI/pre-commit references, and the Obsidian-export habit.
- **Edge-case sweep:** grep the repo(s) for `graphify`/`obsidian` references; for each, either
  migrate it to the Fux equivalent or record why it's intentionally dropped. Nothing dangling.
- Verify `fux gate` green and every removed workflow has a working Fux replacement.
- This item touches my environment — **I run the actual uninstall**; you prepare it, verify
  coverage, and hand me the exact commands + the residual-gap list (e.g. video).

**Explicitly OUT of scope for this objective** (do not build — they don't block removing
Graphify/Obsidian on this repo): multi-assistant surface, org connectors (Jira/Confluence),
cross-repo global graph, incremental build cache, SCIP. If I later want them, they're separate.

Keep a running checklist in each PR and back to me: `[ ] Q0 [ ] Q1 [ ] Q2 [ ] Q3 [ ] Q4 [ ] Q5`.

## The per-item loop (run for the current queue item, in order)

1. **Load & decide.** Read the item's spec + any §10 OPEN QUESTIONS; get my answers **before
   coding**. Don't guess.
2. **Branch.** `git checkout main && git pull`; `feat/<item-slug>`. One item = one branch = one PR.
3. **Explore → Plan → Confirm.** Explore real code first; post a short plan (files, approach,
   fixtures); **pause for my confirmation.**
4. **Implement incrementally.** Small commits; build stays green; follow the spec's constraints.
5. **Test in `fux-lab`.** Extend the dummy repo with fixtures + goldens + negative guards for
   the *new* surface. Run `python run_lab.py` and the offline `$0` sweep. Add/extend `pytest`.
   All green.
6. **Docs (part of done).** Update everything the spec's §9.5 names — `docs/fux-plan.md`,
   `docs/fux-implementation.md`, `docs/cli.md` (regenerate the registry table, don't hand-edit),
   README, whats-new. **Propose** CLAUDE.md/AGENTS.md edits for my review — never auto-apply.
7. **Prepare the release.** Bump `fux.__version__` (semver-appropriate) and add a changelog/
   whats-new entry **in this PR**, so merging + tagging will publish cleanly.
8. **Gate.** `fux gate`, `python -m pytest -q`, `python -m tools.skillgen --check`. Fix every red.
9. **Open the PR (do not merge).** `gh` PR with: the objective + this item, what changed, the
   done-checklist ticked, the `run_lab.py`/gate/parity evidence, the version bump, proposed
   CLAUDE.md edits called out, and the queue checklist. Then **STOP.**
10. **I merge.** Tell me what to review (especially determinism/constitution-sensitive diffs).
11. **Publish — on my explicit go.** After I merge, ask me to confirm the release; on confirm,
    push the release tag so `publish.yml` uploads `fux-engine`. Verify it appears on PyPI.
12. **Advance.** `git checkout main && git pull`, tick the queue, next item at step 1. When the
    queue is empty and Q5 is done, summarize every PR + release and the residual-gap list, then stop.

## Hard constraints (every item)

- **Never merge; never bypass the wall.** PR + green + human review is the finish line.
- **Never publish to PyPI without my explicit confirmation** (irreversible/public).
- **Constitution:** `$0`, stdlib-only, deterministic, **no LLM on any maintenance path**
  (doc/media extraction rides the host-agent `ingest` skill, never engine code). If an item
  seems to need it, STOP and ask.
- **Determinism sacred** where graph output is touched: default `graph.json` byte-identical;
  the viewer never mutates it; new build modes are opt-in.
- **Never edit the engine to make a test pass** — a real bug is a finding.
- **One item at a time.** Don't start the next branch until the current PR is merged (+ released).
- **Honesty over coverage:** if Fux genuinely can't cover a Graphify use (e.g. video), say so
  and record it as a residual gap — do not fake parity to justify removal.
- **Ambiguity or constitution-touching change → STOP and ask.**

## First action

Do **not** code. Reply with: the confirmed queue + order, the Q0 (`fux-lab`) open questions
you need answered, a one-paragraph plan for Q0, and a one-line note on any Graphify use you
suspect Fux can't cover (so we surface the residual gap early). Then wait for my go.
