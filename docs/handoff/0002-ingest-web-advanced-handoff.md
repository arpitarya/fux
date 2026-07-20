---
type: Handoff
title: Ingest v1.1 — web crawling, CDP rendering, advanced tier (OCR)
description: Extends 0001's local inferred-tier ingest with fenced web ingestion, rendered pages, and the agent-triggerable advanced fidelity tier.
status: ready
blocked_by: 0001-query-cli-v1-handoff.md
timestamp: 2026-07-21T00:00:00Z
---

# Handoff 0002 — Ingest v1.1: web, CDP, advanced tier

## Context

Builds directly on 0001 (must be implemented and dogfooded first). All decisions are
closed in [`../compare/ingest-strategy.compare.md`](../compare/ingest-strategy.compare.md)
— two-tier fidelity, fenced web path, CDP via hand-rolled WebSocket, provenance
frontmatter. This handoff turns the accepted design's deferred half into a build.
The fence is the whole point: **network exists only inside `fux ingest`; the query
path never touches it.** The corpus stays git-committed, deterministic, OKF-shaped.

## Definition of done

1. `[sources.web]` in `fux.toml` (urls, max_depth, same_domain, attachments,
   render) is honored by `fux ingest --web`: fetch → convert → cache with
   `origin: url|attachment`, `url`, `parent`, `depth` frontmatter.
2. Crawling follows links + downloads attachments to `max_depth`, same-domain by
   default, allowlist override, per-run page budget, robots.txt respected.
3. `render = "cdp"` sources capture the rendered DOM via the user's own headless
   Chrome (`--remote-debugging-port`), driven by a **hand-rolled RFC 6455 WebSocket
   client on stdlib `socket`/`hashlib`/`base64`** (~few hundred lines, unit-tested
   against a fake server); frontmatter records `renderer: cdp`.
4. `fux ingest --advanced <file|url>` re-converts one source with the advanced
   converter (Docling if installed; Tesseract for images) and flips
   `fidelity: advanced` in frontmatter + manifest. `--list-inferred` output makes
   upgrade candidates discoverable; the `fux-ingest` SKILL.md is updated with the
   judge-and-upgrade workflow.
5. Web fetches are reproducible-ish by design: cached page snapshots carry
   `fetched_at` + content sha; re-ingest of an unchanged page is a no-op (sha
   match), so git diffs stay meaningful.
6. Both suites green, including new e2e flows against a **local fixture HTTP
   server** (stdlib `http.server` in a pytest fixture — no real network in tests).

## In scope

- `ingest/web.py`: urllib fetcher (timeouts, retries, size caps, content-type
  routing), crawl frontier (BFS, depth/budget caps, dedupe by URL + sha),
  robots.txt (stdlib `urllib.robotparser`), HTML→Markdown conversion (stdlib
  `html.parser`-based converter — headings/lists/tables/links/code; good-enough
  fidelity, deterministic output).
- `ingest/cdp.py`: minimal CDP client — WS handshake + frames (RFC 6455, client
  masking, text frames, close), `Target.getTargets`/`Page.navigate`/
  `Page.loadEventFired` wait + settle delay/`Runtime.evaluate`
  (`document.documentElement.outerHTML`), Chrome discovery/launch helper
  (existing install only — never bundle), clean errors when Chrome is absent.
  Optional `websocket-client` extra as fallback path if the hand-rolled client
  fails (flagged, logged).
- `ingest/advanced.py`: converter registry for the advanced tier — Docling
  (office/PDF re-extraction), Tesseract via `pytesseract`-free subprocess call
  (`tesseract <img> stdout`) for images. All extras; all absent-safe with clear
  notices. Manifest/frontmatter fidelity transitions.
- CLI: `fux ingest --web`, `--advanced <target>`, `--list-skipped` extended with
  web skips. Config additions validated with helpful errors.
- Provenance: every web artifact traces `url` → `parent` → root config entry;
  citations in `ask`/`answer` display the original URL for web-origin chunks.

## Out of scope

Auth'd pages/cookies/logins; JS interaction beyond load-and-capture (no clicking);
scheduled/incremental crawling; MCP; anything on the query path touching network.

## Constraints (inherited + specific)

All CLAUDE.md constraints hold. Additionally: crawl politeness (rate-limit ~1 req/s
default, configurable; obey robots.txt — non-negotiable); size caps per fetch and
per run; deterministic cache serialization identical to 0001's; CDP is opt-in
per-source, never a silent fallback of plain fetch.

## Edge cases (tests must cover)

Redirect chains (cap + record final URL); non-HTML content-types at a crawled link
(route to converter or skip w/ notice); crawl cycles (A↔B); depth-0 (page only);
attachment larger than cap; robots.txt disallow (skipped + reported); Chrome not
installed / port busy / page never fires load (timeout → FuxError with guidance);
WS fragmentation + large frames; 4xx/5xx/timeouts (retry then report, never crash
the run); duplicate content at different URLs (sha dedupe, both provenances
recorded); UTF-8 and non-UTF-8 pages.

## Tests

- Unit: WS frame encode/decode (round-trip + RFC vectors), handshake against a fake
  socket; HTML→MD converter goldens; frontier logic (depth/budget/dedupe/cycles);
  robots.txt handling; fidelity transitions.
- E2E (`tests_e2e/`): fixture site served by stdlib `http.server` (pages + linked
  pdf/docx + an image) — crawl flow, attachment conversion, `--check` after source
  change, advanced-upgrade flow (skip CDP e2e in CI unless Chrome is present —
  `skipif`, but keep a manual smoke script `tests_e2e/manual_cdp_smoke.py`).

## Open questions (answer during build, record in the ADR)

1. HTML→MD: hand-rolled `html.parser` converter vs MarkItDown-for-HTML when the
   extra is installed — pick hand-rolled as default (determinism), extra as upgrade?
2. Settle strategy for CDP (fixed delay vs `networkIdle` heuristic) — measure on
   2–3 real SPA docs sites.
3. Crawl state file for resumability — worth it in v1.1 or defer?

## Close-out

ADR 0005 (web + CDP + advanced tier — reference the compare doc). Move this pair to
`docs/archive/` with `status: implemented`. Update plan/README/registry/worklog/
model-handoff-interview. Version bump minor.
