# Fux — Batch & Linked-Document Ingestion · PR3 Handoff

**Owner:** Arpit · **Repo:** `fux` · **Driving model:** Claude Code.
**Builds on PR2** (single-source `/fux ingest <url|file>`). Land PR2 first. Single concern here: *many* sources at once, and following a URL to the documents it links.

---

## 0. What this adds (from the debate)

- **Batch:** `fux ingest <a> <b> <c> …` — multiple URLs/files/globs in one run, partial-failure-tolerant, output is a **draft review queue**, never auto-active rules.
- **Linked documents:** opt-in `--follow-links` — when a URL is a *page*, discover the documents it links (PDF/Excel/Word/CSV/TXT/image/JSON/YAML), and ingest them too — **bounded and confirmed.** A direct file URL is just ingested as that file.
- **New source types:** `.docx` (agent's `docx` skill), **`.json`**, **`.yaml`/`.yml`**, and **Swagger/OpenAPI** — as a file *or* a link.

### Swagger / OpenAPI (the standout)
A Swagger/OpenAPI source — a `.json`/`.yaml` spec, a raw-spec URL, or a Swagger-UI page (CDP-render to find the spec) — is parsed by the agent into **per-contract draft rules**: one per endpoint contract, required-param set, auth scheme, or **deprecation**. Because the spec is machine-precise, `source_hash` + `--recheck` make fux **flag when the API contract you depend on changed** (an endpoint dropped, a param removed). Spec sources are the prime beneficiaries of drift re-check.

### Candidate extensions (from the debate — wire on demand)
- **Tier 1 (structured contracts, same pattern as Swagger):** JSON Schema, GraphQL SDL, protobuf `.proto`, SQL DDL / migrations — each a precise contract → invariant/convention rules + meaningful drift.
- **Tier 2 (on-thesis):** git commit / PR rationale as a source (the *why* itself; pairs with `fux why --history`).
- **Tier 3 (do NOT auto-ingest):** Slack / email / Jira comments — too noisy; route to manual `/fux distill`.

---

## 1. Non-negotiables

- `$0`, stdlib only, deterministic on the engine path. **The agent fetches, crawls, and parses; fux governs.** Engine imports no network/LLM/PDF/Excel/Word/OCR/vision library — guard test proves it.
- **Batch output is a draft review queue** — every ingested item is `status: draft` with provenance + a trust flag, written to a manifest for triage. Nothing auto-activates or auto-promotes to constitutional.
- **Link-following is bounded by construction** (see §3) — it can never become a recursive crawler.
- Files ≤100 lines (≤50 utils). No new runtime deps. Docs in this PR.

---

## 2. Batch ingestion

- Accept N positional sources: URLs, file paths, and globs (`./docs/*.pdf`). Expand globs deterministically; dedup the resulting source list.
- Loop PR2's single-source extract → classify → draft pipeline over each. **Partial-failure-tolerant:** a source that fails (404, unreadable, parse error) is recorded as `failed` with its reason and the batch continues — one bad source never aborts the run.
- **Dedup by `source_hash`** — re-ingesting an identical doc updates/skips rather than duplicating.
- Output → a **draft review queue manifest** at `.fux/ingest/queue.md` (or `out/`): one row per item — `source`, `source_type`, `status: draft|failed`, trust flag, draft id. You triage it, then `/fux debate` → `fux ratify` the keepers. Provide `fux ingest --queue` to show it.

## 3. URL → linked documents (opt-in, bounded)

Off by default. With `--follow-links`, when a URL resolves to an HTML *page* (not a direct file), the **agent** parses it for document links and ingests them under these hard bounds:

- **Depth-1 only.** The documents linked on *this* page — never follow links inside those documents. Not recursive, ever.
- **Same-origin by default** (`--cross-origin` to widen) — don't fetch arbitrary third-party hosts unasked.
- **Extension allow-list:** `.pdf .xlsx .csv .docx .txt .md .json .yaml .yml` + images + OpenAPI/Swagger specs only. **Never** executables/scripts/archives.
- **Capped:** at most `--max N` documents (default 20); refuse-with-message above it.
- **List-and-confirm before download** (default): show the discovered document links and let the user pick which to ingest; `--yes` skips the prompt and takes all (up to the cap). No silent mass-download.
- A **direct file URL** (`…/circular.pdf`) skips discovery and is ingested as that file.

This is the abuse-surface fence: a fintech tool must not be pointed at a URL and silently fetch hundreds of attacker-or-junk documents.

## 4. Trust & provenance (unchanged from PR2, applied at scale)

- Each draft carries `source` / `source_type` / `fetched` / `source_hash` and `status: draft`.
- Regulatory/compliance → DRAFT-VERIFY (verify against primary, human ratify). Image/OCR-derived **money or regulatory** figures → flagged `verify-source`, never auto-trusted. At batch scale these flags drive triage order in the queue.

---

## 4b. Token reduction — reduce before draft (`$0`, deterministic)

Reading whole PDFs/Excels/Words into the agent is the dominant token cost of ingestion. A new **reduce-before-draft** util cuts it without an LLM and without breaking zero-dep, because it operates on the agent's **already-extracted text/structured data** — it never parses a binary itself.

- **Structure-aware slicing per type:** PDF → headings + tables + rule-bearing passages (not full pages); **Excel → schema + sample rows + formulas/constraints, never the full data grid**; Word → headings + section leads; JSON/YAML/Swagger → the contract/schema, not every example value.
- **Rule-signal pre-filter (reuse fux's BM25F recall, `$0`):** keep chunks matching signal terms (`must`/`shall`/`required`/`deprecated`/`limit`/`rate`/`threshold`/`constraint`/`unique`/`not null`…) **plus their surrounding section** — reduces toward candidates, never a hard cut that drops an oddly-phrased rule.
- **Boilerplate strip:** repeated headers/footers/page numbers/legal boilerplate (deterministic regex); whitespace-normalize; dedup repeated blocks.
- **Incremental re-ingest:** on `--recheck` / re-ingest of a changed source, diff the new extract against the cached prior extract and draft only from the **changed** sections. Unchanged re-ingest (same `source_hash`) is already `$0`.
- **Opt-out for precision:** reduce by default; `--full` feeds the whole extract (use for high-stakes regulatory where precision beats cost).
- **Report + meter the saving:** print tokens before→after, and file it through the existing `cage_receipt` (fail-open) — fux's savings story, extended to ingestion.

---

## 5. Changes (file by file)

1. `data/skills/ingest/SKILL.md` — extend to (a) multi-source loop, (b) `--follow-links` page→document-link discovery (depth-1, same-origin, allow-list, cap, list-and-confirm), (c) new extract branches: `.docx`, `.json`, `.yaml`/`.yml`, and **Swagger/OpenAPI** (spec file, raw-spec URL, or Swagger-UI page → per-endpoint/param/deprecation draft rules).
2. `cli.py` — `ingest` takes N sources + globs; add `--follow-links`, `--cross-origin`, `--max N`, `--yes`, `--queue` flags.
3. **new** `ingestqueue.py` (≤100) — write/read the draft review-queue manifest; dedup by `source_hash`; record per-source `draft|failed` + reason. Deterministic, `$0`.
3b. **new** `ingestreduce.py` (≤100) — the §4b reduce-before-draft util: operates on extracted text only (no binary parsing), per-type structure slicing + BM25F rule-signal pre-filter (reuse `recall.py`) + boilerplate strip + incremental-diff on re-ingest. Deterministic, `$0`, stdlib. `--full` bypasses it; reports tokens before→after via `cage_receipt`. The guard test must confirm it imports no parser/network/LLM library.
4. `data/schema.json` — extend `source_type` enum with `docx`, `json`, `yaml`, `openapi` (existing kinds unchanged; additive).
5. Tests — a batch of mixed sources yields one queue with correct per-source status; a failing source doesn't abort the batch; dedup by `source_hash` works; `--follow-links` is depth-1, respects the cap + allow-list + same-origin, and requires confirm unless `--yes`; a direct file URL skips discovery; **guard test**: engine imports no network/LLM/PDF/Excel/Word/OCR/vision library.
6. Docs — `cli.md` (batch + the follow-links flags + bounds), `README.md` (one line), `fux-plan.md` (ingestion section).

---

## 6. Acceptance

- `fux ingest a.pdf b.xlsx https://x …` ingests all, tolerant of one failing, producing a single draft review queue; nothing auto-activates.
- `fux ingest <page-url> --follow-links` discovers the page's linked PDFs/Excels/Words/images/JSON/YAML, lists them, ingests the confirmed set under depth-1 / same-origin / cap / allow-list; a direct file URL is ingested directly.
- A Swagger/OpenAPI spec or link drafts per-endpoint/param/deprecation rules; `--recheck` flags contract drift when the spec changes.
- Drafts carry full provenance + trust flags; regulatory + image/OCR money flagged `verify-source`.
- Dedup by `source_hash`; partial failures recorded, not fatal.
- Reduce-before-draft cuts tokens on a large PDF/Excel (reports before→after); `--full` feeds the whole extract; Excel never sends the full data grid; re-ingest drafts only changed sections. The reducer imports no parser/network/LLM library.
- Guard test green; default install offline + model-free; files ≤100 lines; docs in sync.

---

## 7. Connector sources — Jira / Confluence / GitHub (separate PR4)

A new **connector source class** (distinct from file/URL): the agent pulls **structured data via the existing MCP connectors / APIs** (Jira, Confluence, GitHub) — fux never builds a client or calls an API — then the *same* reduce → draft → review-queue → govern pipeline runs. These are **low-trust** (a ticket/wiki page is not a spec): they land in the queue weighted as candidates, bounded and confirmed like `--follow-links`, never auto-active.

**Efficiency stack — most impactful first (the whole point; "pull less" beats "reduce more"):**
1. **Server-side filter — never the firehose.** Require a query: Jira via **JQL** (only acceptance-criteria/decision tickets, a board, a label — never "all sprints" unfiltered); GitHub via API query (PRs/ADRs/docs, not CI logs or bot comments); Confluence via space/page query. Tokens you never fetch cost nothing.
2. **Delta / `updated-since` cursor** — ingest a board/space once, then only what changed. Re-ingest is incremental.
3. **Structure-slice each item** — Jira: title + description + **acceptance criteria** (drop comment threads, status history); GitHub: PR/commit title + body + linked issue + ADRs (drop CI logs, bot noise; code rules stay `fux mine`'s job); Confluence: page body (drop comments, version history).
4. **Reduce-before-draft (§4b)** + **dedup by `source_hash`** on what remains.

**What's worth ingesting per connector:** GitHub → PR/commit *rationale* + ADRs + docs (the *why*, on-thesis); Jira → acceptance criteria + decisions (requirements); Confluence → runbooks/decisions/glossary pages. **Recommended order: GitHub first** (highest signal, most on-thesis).

**Bounds (same discipline as `--follow-links`):** an explicit query/filter is **mandatory** (refuse an unbounded "everything" pull); cap the item count; list-and-confirm before drafting. `source_type` gains `jira|confluence|github`.

**Fallback ladder — when the MCP connector doesn't work (most efficient first; prefer structured, server-filtered JSON at every rung):**
1. **MCP connector** — default. Structured, server-filtered, auth managed by the connector.
2. **Direct REST API + token (PAT)** — when the connector is unavailable/broken. *The* real fallback: same JSON, same JQL/GraphQL server-side filtering, same efficiency — the connector was only a wrapper around this.
3. **Native export / `git clone`** — bulk offline snapshot. **GitHub needs neither connector nor probe** — `git clone` gives code + ADRs + docs for `$0`, plus the API for PRs. Jira/Confluence: CSV / space export for a one-shot.
4. **CDP via the *authenticated browser session*, calling the JSON REST endpoints** — only when the API is reachable *only* through the logged-in browser (SSO-only, no PAT; enterprise/on-prem). The SPA calls `/rest/api/...` with the session cookie; `fetch()` those in page context via CDP → **structured JSON, not scraped DOM.** Borrow the browser's auth, keep the filtering.
5. **CDP DOM scraping** — absolute last resort, only when even the in-browser API is blocked. Fragile, token-heavy, breaks on UI changes; accept the cost knowingly.

Probes (CDP) are rungs 4–5, **not** the fallback — reach for the REST API and export/clone first. At every rung the *agent* does the fetching; fux governs; the engine stays `$0` and client-free.

> Scope note: build this as **PR4**, after the file/URL batch (PR3) lands — connector-backed ingestion is a distinct concern from file/URL ingestion and deserves its own PR + review.
