# Fux — Remaining Backlog (consolidated handoff)

**Owner:** Arpit · **Repo:** `fux` · **Driving model:** Claude Code.
One doc covering everything planned-but-not-shipped. **Each item is its OWN PR** (single-concern discipline) — this is a roadmap + index, not a "do it all in one commit" spec. Verify actual state before building each; some may be partially done.

---

## Shipped (do NOT rebuild — confirmed in git log)
Constitution Phases 0–5 + 3b + amendment-by-supersession (v0.4–0.5) · enforcement wall: `fux gate` + `ai-review` required checks + Claude Code git identity (v0.6) · cage receipt (v0.7) · graph viewer perf + governance overlay (v0.8) · scrape + `fux how` + CDP config + generated CLI help (v0.9) · ingest-from-files incl. `ingestreduce`/`ingestqueue` (v0.10).

---

## Non-negotiables (apply to every item)
`$0`, stdlib, deterministic on the maintenance path; **agent fetches/parses/debates, fux governs**; engine imports no network/LLM/parser/OCR library (guard test); web/file/connector-sourced rules are `status: draft`, never auto-active; **money never flows through fux** (ADR 0001 — `fux/docs/decisions/0001-fux-elgar-relationship.md`); files ≤100 lines; docs in the same change.

---

## Pending — in priority order (each = one PR)

### 1. self-build + `--self` ("fux explains fux")  ·  spec: `docs/scrape-howto-cli-handoff.md` §C
`selfbuild.py` is missing. Ship `fux self-build` — AST-extract fux's own `fux/*.py` graph + its `.fux/rules` + docs → bundled `data/self/` (`$0`, deterministic, in the wheel). Add a `--self` scope to `query`/`explain`/`path`/`recall` (+ the `how` corpus) that reads `data/self/`, works in any repo with no project `.fux/`. Test: bundle regenerates byte-identically from source. **You already chose this as the next PR — finish it.**

### 2. Decision capture  ·  spec: `docs/decision-capture-handoff.md` + prompt
`decisioncapture.py` is missing. On a `/fux debate` or council conclusion, write a tamper-evident ADR (`debate_hash` + `content_seal`) routed by content — world/code → fux, app → anton, **money → elgar (fux keeps only `elgar://decision/<id>`, never the body, per ADR 0001)**; confirm mandatory for money. Small, high-leverage (makes every future debate self-documenting).

### 3. Batch + linked-document ingestion (PR3)  ·  spec: `docs/batch-ingest-handoff.md`
**Verify first** — `ingestqueue`/`ingestreduce` exist, so part may be done. Confirm/finish: multi-source + globs → draft review queue; `--follow-links` (depth-1, same-origin, capped, allow-list, list-and-confirm); json/yaml/swagger source types (Swagger → per-endpoint rules + `--recheck` contract drift).

### 4. Connector ingestion (PR4)  ·  spec: `docs/batch-ingest-handoff.md` §7
Jira/Confluence/GitHub via MCP/API, server-side filtered (JQL/query/since-cursor), low-trust queue items. Fallback ladder when the connector fails: REST+PAT → export/`git clone` → CDP-via-session(JSON, not DOM) → DOM scrape (last resort). Probes are rungs 4–5, not the default.

### 5. Enforcement PII-content gate probe  ·  spec: `docs/constitution-enforcement-handoff.md`
Close the residual gap: a stray PAN/Aadhaar in a non-plan `.py`/`.md` is only caught locally (bypassable, absent from CI). Port dante's PII regexes into a **stdlib** probe and add it to the `gate` job (don't pip-depend on dante). Stdlib, `$0`.

### 6. (User action, not a build) `BRANCH_PROTECTION_TOKEN`
Add an admin-scoped PAT as a repo secret so the weekly drift audit (`audit-protection.yml`) runs in CI instead of failing on the default token's 403.

---

## Deferred / optional (not in this backlog unless you say so)
Graph git-history playback (v0.8 deferred) · OKF `resource`/`description` schema fields + progressive disclosure · F4 runtime critic on Anton's `append_memory` (Anton repo, not fux).

---

## Acceptance (overall)
Each pending item ships as its own PR through the existing wall (branch → PR → `fux gate` + `ai-review` green → merge), with its own doc updates, guard test green, files ≤100 lines, and the money-firewall intact. Recommended order: 1 → 2 → 3 → 4 → 5.
