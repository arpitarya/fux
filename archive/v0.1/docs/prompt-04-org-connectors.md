# Claude Code prompt: Fux org connectors + cross-repo graph

You are completing Fux's org-knowledge ingestion (Jira, Confluence, Swagger/OpenAPI, a
generic connector contract) and adding a cross-repo global graph. Full spec:
`docs/handoff-04-org-connectors.md` — read it first; Definition of Done and
Non-negotiables are binding. **Hard boundary: the engine stays `$0`/deterministic — all
fetch + semantic extraction ride the host-agent `ingest` skill path, never `build`/`check`.**

## Context to load first
- Read: `fux/data/skills/ingest/SKILL.md`, the `ingest`/`fetch-rules` command impl,
  `fux/data/schema.json` (source fields + `source_type` enum), `docs/cli.md`
  (ingest/`--recheck`/`source-drift`), `fux/importer.py`, `fux/graph.py`, `CLAUDE.md`.
- Reference for shape only (read-only): `graphify/global_graph.py`, `graphify/wiki.py`,
  `graphify/manifest_ingest.py` in the graphify repo.

## Task
1. Verify + harden **OpenAPI** ingest end-to-end on a real spec. 2. Add **Confluence**
   and **Jira** as ingest source types (host-agent/MCP fetch → draft rules-with-why in the
   queue, with `source_type`/`source`/`source_hash`/`fetched`; read-only). 3. Document a
   **generic connector contract** so new sources are fragments, not forks. 4. Add
   `fux/globalgraph.py` + a `fux global` command: deterministic merge of registered repos'
   `graph.json` into `~/.fux/global-graph.json` + manifest, with a query path. 5. Wire
   provenance/staleness via existing `--recheck`/`source-drift`.

## Required workflow
1. **Explore** the ingest skill contract + schema source fields before writing.
2. **Plan** the source-type additions, the generic contract, and the global-graph merge;
   pause for my confirmation. Resolve handoff §10 (MCP vs skill-fetch; which connector first)
   before building connectors.
3. **Implement incrementally**, keeping the suite green; start with the connector I pick in §10.
4. **Update docs**: README org story, `docs/cli.md`, `ingest/SKILL.md`, `docs/fux-plan.md`
   + `docs/fux-implementation.md`, schema guides if fields change, whats-new. Propose the
   CLAUDE.md invariant note for review.
5. **Verify**: `python -m pytest -q`; fixture OpenAPI/Confluence/Jira → expected draft rules;
   `--recheck` → `source-drift`; global-graph merge deterministic.

## Constraints (hard)
- **Zero network/LLM on `build`/`check`.** Fetch/extract is the host-agent skill path;
  the one engine-side network read (`--recheck`) stays behind the `[scrape]` extra and off
  the default `check` path.
- **Draft-only:** every ingested item is `status: draft`, `tier: standard` — never
  auto-active, never auto-constitutional. Human `candidates accept` promotes.
- **Read-only** (no write-back). **No credential storage** — auth by reference/MCP only.
- **No new required runtime deps.** Stdlib + opt-in extras only.
- Do NOT touch the constitution/ratify path, seal/check semantics, or the error contract.

## Acceptance criteria (self-check)
- [ ] OpenAPI ingest verified → per-endpoint draft rules with provenance.
- [ ] Confluence + Jira ingest → draft rules with correct `source_type`/`source_hash`; read-only.
- [ ] Generic connector contract documented; nothing auto-activates.
- [ ] `fux global` merges repo graphs deterministically into `~/.fux/global-graph.json` + manifest; corrupt-manifest backs up not wipes.
- [ ] `--recheck` raises `source-drift` on changed sources.
- [ ] `$0` proof: deterministic half runs network-disabled; network half gated behind `[scrape]`.
- [ ] Docs synced (plan + implementation + cli + SKILL + schema guides).

## Tests
Add: fixture OpenAPI/Confluence/Jira → expected drafts + provenance; staleness `--recheck`;
draft-gate (no auto-activation); two-repo global-graph merge determinism + corrupt-manifest backup.

## Guardrails
- Resolve handoff §10 (MCP-first vs skill-fetch; global-graph governance; first connector)
  with me before implementing connectors.
- If a source needs auth you can't reference safely, STOP and ask — never hardcode or store creds.
- Ask before writing outside the repo (e.g. `~/.fux/`) beyond the documented global-graph path.
