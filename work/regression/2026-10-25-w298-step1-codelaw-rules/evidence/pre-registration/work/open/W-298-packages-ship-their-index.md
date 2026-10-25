---
type: Handoff
name: W-298
description: "Arpit, 2026-10-25 (voice): a package author builds and ships a Fux index of the package's docs; a consumer pins it, and one query searches the repo's own index plus every pinned package index, without re-ingesting. First consumer: codelaw's rule packs. Steps 2–6 designed and RULED 2026-10-25 (Cowork, chat); step 1 PASSED the same day (19/20, bar 16). The build is W-299 · W-300 · W-301 · W-302, ratified not built; W-299 and W-302 are 🟢. All six steps done; CLOSED and archived 2026-10-25."
item: W-298
filed: 2026-10-25
filed_by: "Arpit (Cowork, Opus 5.5)"
updated: 2026-10-25
updated_by: "Arpit (Cowork, Fable 5.1)"
ball: agent
---

# W-298 — research: packages ship their own Fux index; one query searches many

## At a glance

| step | what we do | what it gives us | state |
|---|---|---|---|
| 1 | Spike with today's fux: point `sources.yaml` at `node_modules/@codelaw/rules-js/rules`, write 20 plain-words intents, count how often the right rule is in the top 5. Bar set now: **16 of 20** | evidence that free-text search over rules is worth building for | ✅ **PASS 2026-10-25 — 19/20** ([run](../../work/regression/2026-10-25-w298-step1-codelaw-rules/report.md), [verdict](../../work/regression/2026-10-25-w298-step1-codelaw-rules/VERDICT.md)); on the published pack (140 rules, not 438), fux `main` @ `658bc91`, intents sealed before the first query |
| 2 | Design how a project pins a package's index: name, version, fingerprint — reusing the plugin pinning fux already has | everyone's machine searches the same thing | ✅ designed 2026-10-25 → **W-299** |
| 3 | Design one query over many indexes, with word statistics merged so one big package cannot drown the repo's own docs, in Python and Node | fair ranking, the same answer on every machine | ✅ designed 2026-10-25 → **W-300** |
| 4 | Design how a hit names its package, and how the passage is read in place inside the installed package, never copied | the source of every hit is visible; content stays in the package | ✅ designed 2026-10-25 → **W-301** |
| 5 | Design the publish path: a package's CI runs `fux ingest` over its docs and ships the index with a reproducible fingerprint | any package author can do it | ✅ designed 2026-10-25 → **W-302** (`fux pack`) |
| 6 | Write the proposal and the draft SR; Arpit rules on it and the three open questions | a build item, or a parked one | ✅ ruled 2026-10-25 in chat — five rulings below; four build items filed. The draft SR (SR-PKG-INDEX) is W-299 step 0 |

**Arpit, 2026-10-25 (voice):** *"whosoever is creating those packages, they can
create the Fux index. And rather than Fux trying to re-ingest it, it can search
through multiple indexes. That means there could be one Fux index present at the
root of a project. There could be another index present inside node modules
package. And if you have Fux installed, it can look into all of those."*
→ *"Yes, please go ahead and file it as a Fux work item."*

**Arpit, 2026-10-25 (Cowork, chat), on the design:** *"This looks good to me. If
there are any open questions, let's answer them right now and then file the work
items for all."* Five rulings, same session:

| fork | ruled |
|---|---|
| A · where the pin lives | **`.fux/config/plugins.toml`, `kind = "index"`** — over a `packages:` section in `sources.yaml` |
| B · how an author ships | **a read-only `fux pack <outdir>` verb** — over a recipe only |
| `scope` on `fux_search` | **yes**: `repo` · `packages` · `all`, default `all`; SR-MCP amendment, still three tools |
| segment wire compatibility | **lockstep** — the reader refuses a foreign `_format` / `analyzer` / `tf_fields` by name; the manifest records the builder's fux version; no "minimum version" field |
| the 10 000 ceiling | **counts the merged corpus** — repo + every pinned segment, because that is what one query runs over; `fux doctor` reports the sum |

**Design points accepted with it** (the chat proposal, 2026-10-25): the digest
covers the **segment files only** so one pin serves npm and PyPI; the query is
hashed **once per distinct `identifiers` digest** and each segment ships the
`identifiers.toml` it was built with; `df` / `n` / `total_flen` are **summed** and
`rank()` runs once (shared idf is correct; no per-segment prior without L13
evidence); a hit's location names the **docs** package —
`pkg:@codelaw/rules-js@0.2.0#rules/js/exports-at-end.md` — and `fux_passage`
reads it in place after `..`-collapse and containment (SR-MCP d7 widened).

**Filed from it — ratified, not built (W-299, W-302 🟢 since step 1 passed; W-300, W-301 🟡 on W-299):**
[W-299](../../work/open/W-299-index-package-pin.md) pin + runtime inflation + SR-PKG-INDEX ·
[W-300](../../work/open/W-300-merged-query-over-segments.md) merged query + `scope` ·
[W-301](../../work/open/W-301-pkg-locations-read-in-place.md) `pkg:` locations + passage in place ·
[W-302](../../work/open/W-302-fux-pack-publish-path.md) `fux pack`.

**Model:** **Cowork**, Opus — a `research` item, never Claude Code
([SR-WORK-OPEN-QUEUE](../../records/0051_WORK-open-queue.md) rule 37a). Step 1
runs fux as a user and writes no code into this repo.

## Why

- **Ingest is Python-only; the Node plane only reads.** A consumer asked to ingest
  a package's docs itself can never do it from an npm-only install.
- **Built once where the package is built**, the index needs no ingest at install,
  is read by either runtime, and keeps the package's content inside the package
  ([L3](../../records/0005_LAW-3-content-never-durable.md)).
- **First consumer:** codelaw's rule packs — 438 Markdown rule files — as the
  free-text layer of codelaw's W-05 (an agent asks *"debounced fetch hook"* and
  gets the rules and the decision behind them; codelaw keeps the exact verdict).
- **Generic, not codelaw-specific:** any npm or PyPI package that ships docs.

## What fux would have to learn (to be designed, not built, here)

1. **Package sources, pinned.** A committed row per package: name, registry,
   version and digest of the shipped segment. Reuse
   [SR-PLUGINS](../../records/0165_plugins.md) P2–P4 and P7 as they stand:
   declared, never detected; located by name (`importlib.util.find_spec` /
   Node module resolution, never a path); missing or drifted is a loud
   `FuxError` naming the install line; `fux setup --pin` re-pins after an upgrade.
   The resolved path lives in gitignored `.fux/runtime/`
   ([SR-DOTFUX](../../records/0102_fux-directory.md)); the committed index holds
   only the pin.
2. **A multi-segment query.** `fux_search` ranks across the repo's own index plus
   every pinned package segment. Document statistics (df, N) merge across
   segments, so the result is deterministic for a pinned set
   ([L4](../../records/0006_LAW-4-deterministic.md)). Both runtimes
   ([SR-NODE-SEARCH](../../records/0153_node-search.md)).
3. **Namespaced locations.** A hit carries a `pkg:` location, e.g.
   `pkg:npm/@codelaw/rules-js@0.2.0#rules/js/exports-at-end.md`; `fux_passage`
   resolves it by package name, in place, and still refuses to escape what it
   may read ([SR-MCP](../../records/0136_mcp.md) decision 7).
4. **A publish path for authors.** A documented way for a package's CI to run
   `fux ingest` over its docs and ship the segment in its tarball or wheel, with
   a digest anyone can reproduce from the same files.

## Ruled in codelaw, recorded here for context

**Arpit, 2026-10-25 (voice):** codelaw ships each pack's index as **its own
optional package, never inside the rule pack and never installed by default** —
*"I would like to go with @codelaw/rules-js-fux-index"*, *"Both. It should be NPM
as well as PyPI."* That work, and the codelaw law amendment it needs, is codelaw's
W-34, not this item. **For fux this means the segment arrives in a package of its
own** — the pin names the index package, not the docs package — and step 4 has to
say how a hit in `@codelaw/rules-js-fux-index` resolves to the rule file that
lives in `@codelaw/rules-js`.

## Open questions for Arpit (step 6) — ✅ all three ruled 2026-10-25, see the table above

- An optional `scope` parameter on `fux_search` (repo only / packages only)? An
  SR-MCP amendment either way — the tool descriptions are gated, and there is
  still no fourth tool.
- Segment wire-format compatibility across fux versions: lockstep only, or a
  declared minimum version in the segment?
- Does a shipped segment count toward the 10 000-document ceiling
  ([SR-WORK-SCALE](../../records/0057_WORK-scale.md))?

## Definition of done

- Step 1's run is filed under `work/regression/` with its 20 intents, ranks and the
  pre-set bar (≥ 16 of 20 in the top 5); below the bar, this item closes as
  *parked* with the evidence.
- ~~Steps 2–5 are a proposal in `work/proposals/` and a draft SR, status `proposed`,
  with an inbox row for the ruling.~~ **Superseded 2026-10-25:** Arpit ruled in chat and
  asked for work items instead; the design lives in W-299–W-302 and the SR is W-299 step 0.
  What remains of this item is **step 1**: below the bar, W-299–W-302 close *parked* with it.

## Hazards

- **Merged statistics are the hard part.** Two segments built by different fux
  versions, or with different stopwords or identifier families, may not be
  mergeable at all; step 3 must say what refuses.
- **The 10 000 ceiling** governs what step 1 may claim (438 rules + this repo's
  docs is far inside it).
- A recursive walk over `work/` excludes `work/golden/` (L11) — step 1 needs
  none.

**Records affected (proposed):** a new SR (package sources), SR-PLUGINS (reuse),
SR-MCP (only if `scope` is added), SR-DOTFUX (resolved paths under `runtime/`),
SR-NODE-SEARCH (the merged query in Node). **None changed by this file.**

**Also written up for Arpit:** the Claude Doc *"Fux work item — packages ship
their own index"* (2026-10-25) — the same content; this file is the source of
truth.

**Step 1 ran 2026-10-25 (Cowork, Fable 5.1):** Arpit — *"How to execute 298 step 1. You go ahead and execute it."* Run from a fresh clone of `main` @ `658bc91` in the cloud container (the Mac's venv cannot run the engine from the bridge), `@codelaw/rules-js@0.1.0` from npm under `node_modules/`. **PASS: 19 of 20 in the top 5, 13 at rank 1.** Filed as [`2026-10-25-w298-step1-codelaw-rules`](../../work/regression/2026-10-25-w298-step1-codelaw-rules/report.md). **Every step of this item is done; closed and archived 2026-10-25** (SR-WORK-OPEN-QUEUE rules 54–58). Live successors: W-299 · W-300 · W-301 · W-302.
