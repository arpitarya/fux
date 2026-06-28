# Fux — Batch & Linked-Document Ingestion (PR3): One-Shot Prompt

Paste into Claude Code in the `fux` repo, **after PR2 (single-source `/fux ingest`) is merged**. Full spec: `docs/batch-ingest-handoff.md`. This is its OWN PR.

```
Extend `/fux ingest` to (a) ingest MANY sources at once and (b) optionally follow a URL to the documents
it links, per docs/batch-ingest-handoff.md. Build on the merged PR2 single-source ingest — do not
reimplement its extract→classify→draft pipeline. Read that handoff plus the ingest skill, cli.py, and
fux/data/schema.json first. Plan briefly, show me the plan, then implement.

HARD CONSTRAINTS: $0, stdlib only, deterministic on the engine path. The AGENT fetches, crawls, and parses;
fux governs. Engine imports NO network/LLM/PDF/Excel/Word/OCR/vision library — guard test proves it. Every
ingested item is status: draft in a review queue — nothing auto-activates or auto-promotes. Files ≤100
lines. No new runtime deps. Docs in THIS PR.

DO:
1. BATCH: `fux ingest <a> <b> <c> …` accepts N URLs/files/globs. Expand globs deterministically, dedup the
   source list, loop PR2's single-source pipeline over each. PARTIAL-FAILURE-TOLERANT: a source that fails
   is recorded as `failed` with a reason and the batch continues. Dedup ingested drafts by source_hash.
2. DRAFT REVIEW QUEUE: new ingestqueue.py (≤100) writes/reads a manifest (.fux/ingest/queue.md) — one row
   per item: source, source_type, status: draft|failed, trust flag, draft id. Add `fux ingest --queue` to
   show it. The queue is the output; you triage then /fux debate → fux ratify the keepers. NEVER inline
   auto-active rules.
3. LINKED DOCS (opt-in, BOUNDED): with `--follow-links`, when a URL is an HTML page the AGENT discovers the
   documents it links and ingests them under HARD bounds:
   - depth-1 ONLY (never recursive)
   - same-origin by default; `--cross-origin` to widen
   - extension allow-list: .pdf .xlsx .csv .docx .txt .md .json .yaml .yml + images + OpenAPI/Swagger specs
     — NEVER executables/scripts/archives
   - capped at `--max N` (default 20); refuse-with-message above it
   - LIST-AND-CONFIRM before download by default (show discovered links, user picks); `--yes` takes all up
     to the cap. No silent mass-download.
   - a DIRECT file URL (…/circular.pdf) skips discovery and is ingested as that file.
4. Add extract branches + `source_type` enum values: `.docx` (docx skill), `.json`, `.yaml`/`.yml`, and
   SWAGGER/OPENAPI (a .json/.yaml spec, a raw-spec URL, or a Swagger-UI page → CDP-render to find the spec).
   A Swagger source drafts a rule PER endpoint contract / required-param set / auth scheme / deprecation;
   source_hash + `--recheck` flag contract drift when the spec changes. New source_type values:
   url|pdf|xlsx|docx|txt|image|json|yaml|openapi.
   (Candidate follow-ups, do NOT build now: JSON Schema / GraphQL / proto / SQL DDL — same structured-spec
   pattern; git/PR rationale — Tier 2. Slack/Jira — never auto-ingest.)
5. Trust unchanged at scale: regulatory → DRAFT-VERIFY; image/OCR-derived money/regulatory → verify-source,
   never auto-trusted (these drive triage order in the queue).
6. TOKEN REDUCTION (reduce-before-draft, $0): new ingestreduce.py (≤100) operates on the agent's EXTRACTED
   text only (never parses a binary), and the skill feeds the agent the reduced extract, not the whole doc:
   - per-type structure slicing: PDF → headings + tables + rule-bearing passages; Excel → schema + sample
     rows + formulas (NEVER the full data grid); Word → headings + section leads; JSON/YAML/Swagger →
     contract/schema, not example values.
   - rule-signal pre-filter reusing recall.py BM25F: keep chunks matching must/shall/required/deprecated/
     limit/rate/threshold/constraint/unique/not-null… PLUS surrounding section (reduce toward candidates,
     never a hard cut).
   - boilerplate/header/footer/page-number strip; whitespace normalize; dedup repeated blocks.
   - incremental re-ingest: on --recheck of a changed source, diff new vs cached extract, draft only the
     CHANGED sections.
   - `--full` bypasses reduction (use for high-stakes regulatory). Report tokens before→after and file it
     via the existing cage_receipt (fail-open). ingestreduce.py must import NO parser/network/LLM library.

TESTS + PROVE IT:
- a batch of mixed sources → one queue with correct per-source draft|failed status; one failing source does
  NOT abort the batch; dedup by source_hash works.
- `--follow-links` is depth-1, respects cap + allow-list + same-origin, and requires confirm unless `--yes`;
  a direct file URL skips discovery.
- a JSON, YAML, and Swagger/OpenAPI source each draft correctly; a Swagger spec drafts per-endpoint rules
  and `--recheck` flags contract drift when the spec changes.
- reduce-before-draft cuts tokens on a large PDF/Excel and reports before→after; `--full` bypasses it;
  Excel never sends the full grid; re-ingest of a changed source drafts only the changed sections;
  ingestreduce.py imports no parser/network/LLM library (guard test).
- regulatory + image/OCR money drafts flagged verify-source; nothing auto-ratifies.
- GUARD TEST: no network/LLM/PDF/Excel/Word/OCR/vision import reachable from the engine path; default
  install offline + model-free.
Run `python -m pytest -q` and paste output. Update cli.md/README/fux-plan in this PR.
```

---

## PR4 (separate, after PR3) — Connector ingestion: Jira / Confluence / GitHub

```
Add a CONNECTOR source class to `/fux ingest` per docs/batch-ingest-handoff.md §7. This is its OWN PR,
after the file/URL batch (PR3) is merged. The agent pulls structured data via the existing MCP connectors
/ APIs (Jira, Confluence, GitHub); fux NEVER builds a client or calls an API. The same reduce → draft →
review-queue → govern pipeline runs on the result.

HARD CONSTRAINTS: $0/stdlib/deterministic engine path; agent pulls via connector, fux governs; engine
imports no network/HTTP/connector client. Connector-sourced items are LOW-TRUST candidates in the queue,
never auto-active. Files ≤100 lines. Docs in this PR.

EFFICIENCY STACK (most impactful first — "pull less" beats "reduce more"):
1. SERVER-SIDE FILTER, mandatory — refuse an unbounded pull. Jira via JQL (acceptance-criteria/decision
   tickets, a board, a label — NEVER "all sprints" unfiltered); GitHub via API query (PRs/ADRs/docs, not
   CI logs/bot comments); Confluence via space/page query.
2. DELTA: `updated-since` cursor — ingest a board/space once, then only what changed.
3. STRUCTURE-SLICE per item: Jira → title + description + ACCEPTANCE CRITERIA (drop comments/status
   history); GitHub → PR/commit title + body + linked issue + ADRs (drop CI/bot noise; code rules stay
   `fux mine`'s job); Confluence → page body (drop comments/version history).
4. reduce-before-draft (ingestreduce.py) + dedup by source_hash on what remains.

DO:
- Add source_type values jira|confluence|github. Add the connector branches to the ingest skill (agent
  uses the MCP/API connector; passes structured JSON to the existing pipeline).
- Mandatory explicit query/filter (refuse "everything"); cap item count; list-and-confirm before drafting.
- Recommended build order: GitHub first (highest signal, most on-thesis), then Jira, then Confluence.
- FALLBACK LADDER when the MCP connector doesn't work (most efficient first; prefer structured JSON every
  rung): (1) MCP connector; (2) direct REST API + PAT — same JSON + JQL/GraphQL filtering; (3) native
  export / `git clone` (GitHub needs neither connector nor probe — clone + API); (4) CDP via the
  AUTHENTICATED browser session calling the JSON `/rest/api/...` endpoints (SSO-only/no-PAT case) — fetch
  JSON in page context, do NOT scrape the DOM; (5) CDP DOM scraping — last resort only. Probes are rungs
  4–5, not the default. The agent does the fetching at every rung; engine stays $0/client-free.

TESTS: a filtered Jira/GitHub/Confluence pull drafts low-trust queue items with provenance; an unbounded
pull is REFUSED; delta cursor re-ingests only changed items; code-rule extraction is NOT duplicated
(that's fux mine); guard test — engine imports no network/connector client.
Run pytest, paste output, update docs.
```
