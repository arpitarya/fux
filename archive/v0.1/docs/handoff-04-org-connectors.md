# Handoff 04: Org scale — Jira / Confluence / Swagger connectors + cross-repo graph

**One-liner:** Let Fux ingest an organization's non-code knowledge sources (Jira,
Confluence, Swagger/OpenAPI, and a generic connector shape) into the draft-review
queue as rules-with-provenance, and merge many repos' graphs into one cross-repo
"global graph" — without breaking `$0`/determinism (network lives only in opt-in,
host-agent/skill paths, never on `check`).
**Owner / executor:** Claude Code
**Status:** Ready to build
**Stress-tested:** Devils-advocate — "an org connector story is a product in itself;
you'll drown in auth, pagination, rate limits, and stale-sync bugs, and it invites an
LLM onto the extraction path." **Survived with a hard boundary:** Fux does **not**
become an ETL platform. The engine stays deterministic; **fetching + semantic
extraction ride the host agent's tokens via the existing `ingest` skill pattern**
(exactly how OpenAPI already works), landing everything as `status: draft` in the
review queue — never auto-active, never auto-constitutional. The `[scrape]` extra
already fences the one network path. **Blocked one over-reach:** live bidirectional
sync (write back to Jira) is out — read-only ingestion only. **Residual risk:**
provenance/staleness — a rule sourced from a Confluence page that later changes; handled
by `source_hash` + the existing `--recheck`/`source-drift` mechanism.

## 1. Context & background

Fux's schema **already anticipates this**: `source_type` enum includes
`jira | confluence | github | openapi`, and `source`, `source_hash`, `fetched`,
`why_source` fields exist ([fux/data/schema.json](../fux/data/schema.json)). The
`ingest` skill already handles URLs/PDF/**Swagger/OpenAPI** → per-endpoint draft
rules, with a draft queue, `source_hash` dedup, and opt-in `--recheck`/`source-drift`
([docs/cli.md](cli.md)). So this handoff is mostly **completing a pattern that's
half-built**, plus adding a cross-repo global graph (graphify's `global_graph.py`
shows the shape). It is *not* a green-field connector platform.

## 2. Definition of done

- [ ] **Swagger/OpenAPI** end-to-end verified and documented on a real spec →
      per-endpoint/param/auth/deprecation draft rules in the queue (already designed;
      confirm + harden).
- [ ] **Confluence** + **Jira** ingestion via the `ingest` skill: given a page/issue
      URL (or exported content), the host agent extracts durable rules-with-why into
      the draft queue with `source_type`, `source`, `source_hash`, `fetched`. Read-only.
- [ ] A **generic connector contract** documented so a new source (ServiceNow, Notion,
      etc.) is a fragment, not a fork — normalize → extraction dict → draft queue.
- [ ] **Cross-repo global graph:** `fux global` builds/updates a `~/.fux/global-graph.json`
      + manifest merging per-repo `graph.json`, with a query path ("how does repo A relate
      to repo B"). Deterministic merge, `$0`.
- [ ] Provenance + staleness: every ingested rule carries `source_hash`; `--recheck`
      raises `source-drift` when the upstream changed (reuse existing mechanism).
- [ ] Engine stays `$0`/deterministic: no network or LLM on `build`/`check`; all fetch/
      extract is the opt-in skill path. Docs updated (§9.5).

## 3. Scope

**In scope:** verify/harden OpenAPI ingest; Jira + Confluence ingest via the skill;
a documented generic connector contract; the cross-repo global graph + query; provenance/
staleness wiring.
**Out of scope (explicit):** write-back / bidirectional sync; a background daemon that
polls services; storing credentials in Fux; putting any fetch/LLM call on the `check`/
`build` path; a hosted multi-tenant service. No new required runtime deps — network
stays behind the `[scrape]` extra and/or the host agent.

## 4. Current state

- Read first: `fux/data/skills/ingest/SKILL.md` (the ingest skill contract),
  the `ingest`/`fetch-rules` command impl, `fux/data/schema.json` (source fields +
  `source_type` enum), `docs/cli.md` (ingest/fetch-rules/`--recheck`/`source-drift`
  sections), `fux/importer.py`/`narrative.py` (migration paths), `fux/graph.py`
  (graph merge surface for the global graph).
- Reference for shape only (graphify, read-only): `graphify/global_graph.py`
  (`~/.graphify` manifest + merge), `graphify/wiki.py`, `graphify/mcp_ingest.py`,
  `graphify/manifest_ingest.py`, `graphify/pg_introspect.py`.

## 5. Technical approach (decided)

1. **Extend the ingest skill, don't add engine connectors.** Jira/Confluence become
   documented source types the skill knows how to fetch (host-agent tokens / MCP) and
   extract into the draft queue — identical to the OpenAPI flow that already works. The
   engine only ever sees a normalized extraction dict + provenance fields.
2. **Generic connector contract:** a small documented interface — `fetch(source) →
   text/records`, `extract → [draft rule]` — so adding a source is a skill fragment +
   a `source_type`. Where a native MCP connector exists (Jira/Confluence MCP), prefer it.
3. **Provenance/staleness:** reuse `source`, `source_hash`, `fetched` + `--recheck`
   (`source-drift`). Nothing auto-activates; `fux candidates accept` is the human gate.
4. **Cross-repo global graph (`fux/globalgraph.py` + `fux global`):** deterministic
   union of registered repos' `graph.json` into `~/.fux/global-graph.json` with a
   manifest (path, last-built, hash); a query path over the merged graph. Corrupt-manifest
   backup discipline (graphify's pattern). `$0`.
5. **Verify-source safety:** an OCR/image-derived money/regulatory figure stays flagged
   `verify-source` (already in `lint`) — never auto-trusted.

## 6. Non-negotiables / constraints

- **Engine determinism + `$0`:** zero network/LLM on `build`/`check`. Fetch + semantic
  extraction are the host-agent skill path only; the one engine-side network read
  (`--recheck`) stays behind the `[scrape]` extra and off the default `check` path.
- **Draft-only:** every ingested item lands `status: draft`, `tier: standard` — never
  auto-active, **never auto-constitutional**. Human `candidates accept` promotes.
- **No credential storage** in Fux; auth is the host/MCP's responsibility, referenced by
  name only.
- **Read-only.** No write-back to any source.
- **Do not touch:** the constitution/ratify path, seal/check semantics, the error contract.

## 7. Dependencies & prerequisites

Prefer existing **MCP connectors** for Jira/Confluence when available (the host agent
already authenticates them). OpenAPI needs only the spec. The global graph needs each
repo's `graph.json` present. Secrets by reference only — never pasted.

## 8. Edge cases & risks

- **Auth/rate limits/pagination** → the skill/MCP's problem, not the engine's; document
  partial-failure tolerance (one bad source recorded `failed`, batch continues — already
  the ingest contract).
- **Upstream page/issue edited after ingest** → `source_hash` + `--recheck`/`source-drift`.
- **Duplicate rules across repos in the global graph** → dedup by content/`source_hash`.
- **Confluence/Jira HTML noise** → reduce-before-draft trimming (already in ingest) so the
  agent drafts from signal, not chrome.
- **Global manifest corruption** → back up `.corrupt.<ts>` and rebuild, don't wipe.

## 9. Testing & validation

- Ingest: fixture OpenAPI spec → expected per-endpoint draft rules with provenance;
  fixture Confluence/Jira export → draft rules with correct `source_type`/`source_hash`.
- Staleness: change a fixture source → `--recheck` raises `source-drift`.
- Draft gate: assert nothing auto-activates; `candidates accept` promotes.
- Global graph: merge two fixture repo graphs → deterministic union; corrupt-manifest→backup.
- `$0` proof: the ingest/global paths run with network disabled for the deterministic
  half (extraction dict → queue), and the network half is provably gated behind `[scrape]`.
- `python -m pytest -q` green.

## 9.5 Documentation impact

- [ ] **README** — required: org/connector story + the read-only, draft-first, `$0`-engine boundary.
- [ ] **docs/cli.md** — required: Jira/Confluence source types, `fux global`, provenance flags.
- [ ] **fux/data/skills/ingest/SKILL.md** — required: the new source types + generic contract.
- [ ] **docs/fux-plan.md** + **docs/fux-implementation.md** — required (new capability + status).
- [ ] **docs/schema.json guides** (rule.guide.md/spec.guide.md) — required if source fields change.
- [ ] **CLAUDE.md** — propose: the "engine stays deterministic; connectors ride the skill" invariant.
- [ ] CHANGELOG/whats-new — required.

## 10. Open questions

- OPEN QUESTION: **native MCP connectors vs skill-fetch** for Jira/Confluence — do you
  already run Jira/Confluence MCPs? If so, prefer them (auth handled). Recommendation:
  MCP-first, skill-fetch fallback.
- OPEN QUESTION: does the **global graph** need governance (rules that span repos), or is
  it read-only navigation for now? Recommendation: read-only navigation first; cross-repo
  rules later.
- OPEN QUESTION: which single connector is highest value to nail first? Recommendation:
  **Confluence** (most "why" lives there) — then Jira, then verify OpenAPI.
