---
type: ADR
title: ADR-0005 — fenced web ingestion, CDP rendering, advanced fidelity tier
description: urllib crawl behind guardrails, hand-rolled RFC 6455 client for rendered pages, Docling/Tesseract upgrades — network never on the query path.
timestamp: 2026-07-21T00:00:00Z
---

# ADR-0005: web + CDP + advanced tier (ingest v1.1)

- **Status:** accepted
- **Date:** 2026-07-21
- **Feature:** handoff 0002 — web crawling, CDP rendering, `--advanced`

## Context

0001 shipped local inferred-tier ingest. The accepted ingest-strategy verdict
included three deferred halves: fenced link ingestion (crawl + attachments),
rendered-page capture over CDP, and the on-demand advanced fidelity tier. The
fence is the design's spine: **network exists only inside `fux ingest`; the
query path never touches it** (now enforced by a unit test, not just a rule).

## Decision

- **HTML→Markdown is hand-rolled on stdlib `html.parser`** (open question 1):
  headings/lists/tables/links/images/pre/blockquotes, whitespace-normalized so
  identical pages convert to identical bytes. MarkItDown stays an office-formats
  extra, not the web path — the web converter must be deterministic and always
  present, or the corpus's git story breaks on machines without extras.
- **Crawl guardrails:** BFS frontier, depth cap, per-run budget, same-domain
  default + allowlist, politeness delay (default 1 s), per-fetch size cap,
  4xx skip vs 5xx retry, robots.txt obeyed unconditionally (permissive only
  when robots.txt itself is unreachable — the standard interpretation).
  Duplicate content at different URLs is sha-deduped: indexed once, second URL
  recorded as `duplicate_of` provenance.
- **Provenance:** web artifacts carry `origin: url|attachment`, `url`,
  `parent`, `depth`, `fetched_at`; citations naturally display the URL (the
  manifest source *is* the URL), and synthetic conversions carry no line
  numbers rather than fabricated ones. `fetched_at` is reused when the fetched
  sha is unchanged, so re-crawls of unchanged sites are byte-identical no-ops.
  Web entries persist across local-only runs and are excluded from `--check`
  (web freshness = an explicit `--web` re-crawl; the check path stays offline).
- **CDP = hand-rolled RFC 6455** on `socket`/`hashlib`/`base64` (handshake with
  accept-key validation, masked client frames, fragmentation, 16/64-bit
  lengths, ping/pong) — unit-tested against RFC vectors and a fake server; the
  `websocket-client` extra is a *flagged, logged* fallback only. Capture =
  existing Chrome only (discover on the port, else launch `--headless=new`;
  never bundle a browser), `Page.navigate` → `loadEventFired` → settle →
  `Runtime.evaluate` outerHTML. **Settle strategy (open question 2): fixed
  configurable delay (`settle_ms`, default 500)** — a `networkIdle` heuristic
  needs Network-domain event tracking for marginal gain; revisit if Anton's
  real SPA targets capture incomplete DOMs. CDP fires only where configured
  (`render = "cdp"`), never as a silent fallback of plain fetch.
- **Advanced tier:** `fux ingest --advanced <file|url>` — Docling for
  office/PDF, `tesseract <img> stdout` subprocess for images (no pytesseract
  dependency); absent-safe with actionable errors. Fidelity flips in
  frontmatter + manifest; **index reuse is keyed on (sha, fidelity)** so
  upgraded text re-chunks despite the unchanged source sha; upgrades survive
  plain re-ingests and reset honestly when the source changes.
- **Crawl resumability (open question 3): deferred.** Budget-capped runs are
  small and re-crawls of unchanged pages are no-ops, so a state file buys
  little; reopen if Anton needs large-site crawls.

## Alternatives considered

- MarkItDown/BeautifulSoup for HTML — rejected as default (extra dependency on
  the always-present path; nondeterminism risk across versions).
- Bundling a browser (Playwright-style) — rejected outright: hundreds of MB,
  against the small-and-per-repo constraint; the user's own Chrome suffices.
- `websocket-client` as the primary transport — rejected: the dependency-free
  path is the product (same ethos as the frontmatter parser); it remains as a
  flagged fallback.
- Auto-advanced ingestion of everything — rejected in the compare doc: pay for
  fidelity only where a human or agent judged the inferred text insufficient.

## Consequences

Easier: web knowledge lands in the same OKF corpus with full provenance; agents
can judge fidelity and trigger upgrades themselves. Harder: rendered capture
depends on a local Chrome; `fetched_at` makes a *changed* page's re-ingest
non-reproducible byte-wise (inherent to network sources — the sha records what
was true); the HTML converter is good-enough fidelity, not pandoc.

## References (required)

- Ingest-strategy compare doc (verdict, web/CDP/advanced sections):
  [../compare/ingest-strategy.compare.md](../compare/ingest-strategy.compare.md)
- RFC 6455 — The WebSocket Protocol (handshake §4, framing §5):
  https://datatracker.ietf.org/doc/html/rfc6455
- Chrome DevTools Protocol (Page/Runtime domains):
  https://chromedevtools.github.io/devtools-protocol/
- robots.txt / RFC 9309 (Robots Exclusion Protocol):
  https://datatracker.ietf.org/doc/html/rfc9309
