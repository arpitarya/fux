---
type: ADR
name: ADR-URL-MIDDLEWARE
title: ADR-URL-MIDDLEWARE (0010) — URL source via consumer-owned middleware (CDP template)
description: Adds src:"url" to the committed schema, fetched exclusively through a consumer-owned middleware file (fux.toml [sources.url]) under `fux ingest --refresh-urls`. Core ships no URL adapter and no network code; hashed meta is the default; offline ingest carries url records forward byte-identically. Ships a CDP template ported from the archived v0.26 engine. Amended by ADR-FUX-DIR — the URL list is now .fux/sources/urls, the middleware .fux/middleware/cdp.py, and tunables an opaque [sources.url.config] table.
status: superseded
timestamp: 2026-08-11T00:00:00Z
---

# ADR-URL-MIDDLEWARE — URL source via consumer-owned middleware

> **Superseded and archived 2026-08-18.** This record is **history**, not
> evidence: it may be *named*, never cited as backing a live claim.
> **Live successor: ADR-URL-INGEST** in
> [`docs/adr/`](../../docs/adr/README.md). See
> [`../README.md`](../README.md) §Archive is not evidence.


- **Name:** `ADR-URL-MIDDLEWARE` — cite this everywhere; never cite the number
- **Status:** superseded by ADR-URL-INGEST
- **Owns:** `src/fux/ingest/urlsrc.py`
- **Laws:** L1, L2, L4, L5 — see [ADR-LAWS](../../docs/adr/0001_laws.md); never restated here
  he ratifies by flipping this line)
- **Date:** 2026-08-10 · **amended 2026-08-11** by
  [ADR-FUX-DIR](0011_fux-dir-layout.md), before ratification
- **Feature:** URL ingestion through a package-consumer-owned middleware
  file, with a Chrome DevTools Protocol template
  (`.fux/middleware/cdp.py`).

> **Amendment (2026-08-11, ADR-FUX-DIR).** Three placements decided here moved
> while this ADR was still `proposed`, so it is amended in place rather than
> superseded. The mechanism is unchanged; only *where things live*:
>
> | was (2026-08-10) | is (ADR-FUX-DIR) |
> |---|---|
> | `urls = [...]` inline in `fux.toml` | `.fux/sources/urls`, one URL per line |
> | `cdp_middleware.py` at the repo root | `.fux/middleware/cdp.py` |
> | tunables as module constants | `[sources.url.config]`, passed verbatim to a new optional `configure(config)` hook |
>
> An inline `urls` key is now a hard `FuxError` — no shim; this ADR's v1 was
> hours old and unreleased.

## Context

Arpit asked for "a file that can be edited by the package consumer to
connect to Chrome DevTools Protocol, used by fux to ingest URLs — something
like a middleware." Three standing rules collide with a naive "add a CDP
adapter" reading:

1. **The adapter cap (git + HTTP + Confluence) is a decision**
   ([INTERVIEW.md](../../work/INTERVIEW.md) non-relitigable #6; PLAN.md M4 —
   "more systems arrive via [the MCP proposal](../../work/proposals/mcp-adapters.md),
   not code").
2. **Laws L1 and L4 bind this decision** — see [ADR-LAWS](../../docs/adr/0001_laws.md); they
   are not restated here. `src/fux/` currently contains zero network code.
3. **ADR-INDEX-FORMAT froze the schema** with `src: "git"` as the only exercised
   value, and hashed meta unexercised.

The resolution: fux core gains **no adapter**. It gains a generic,
config-declared extension point — `[sources.url] middleware = "<file>.py>"` —
and the *consumer's own file* does the fetching. CDP, auth, retries, or a
swapped-in Playwright all live on the consumer's side of that boundary. This
is the same shape the MCP proposal reaches for ("integration arrives as
configuration, not core code"), landed early because the mechanism costs
~100 lines of loader and zero dependencies. The cap on fux-shipped source
*systems* stands.

Precedent: the archived v0.26 engine shipped exactly this capture path —
`render = "cdp"`, hand-rolled RFC 6455 WebSocket on stdlib, user's own
Chrome, never a bundled browser (accepted 2026-07-21). The template is a
port of `archive/v0.26/src/fux/ingest/{ws,cdp,htmlmd}.py`, which dogfooded
through v0.25. Porting archived code requires this ADR + sign-off per
CLAUDE.md — that is what this document is.

## Decision

### The contract

`fux.toml`:

```toml
[sources.url]
middleware = ".fux/middleware/cdp.py"   # repo-root-relative, consumer-owned
urls_file  = ".fux/sources/urls"        # one URL per line, committed
meta       = "hashed"                   # default; "plain" is per-source opt-in

[sources.url.config]                    # opaque to fux (ADR-FUX-DIR)
cdp_port = 9222
```

The middleware file must define `fetch(url: str) -> str` (one markdown
document per URL; raising ⇒ the URL is skipped with the error as reason,
never a crash) and may define `connect()` / `close()`, called once around
the batch, and `configure(config)` (ADR-FUX-DIR), called once after import with
the config table verbatim. Fux passes nothing else and imports nothing else —
transport is entirely the consumer's.

### Schema (extends ADR-INDEX-FORMAT; no frozen field changes shape)

| field | url-source value |
|---|---|
| `id` | `"url:" + url` (fragment-free, byte-exact as configured) |
| `src` | `"url"` |
| `loc` | the url, no prefix |
| `meta` | **`"hashed"` by default** — the non-git law, exercised for the first time: `title_h = blake2b16(title)`, no `title`, no `phrases`. `"plain"` only by explicit per-source opt-in. |
| `sha` | `content_sha` of the **sanitized markdown bytes as ingested** — not the raw HTML, which is unstable across renders |
| everything else | identical to git docs: `ver` bump rule, `mode:"extracted"`, hashed `terms`, `wlen`, `code`, `edges` |

The index stores statistics of the fetched text and never the text — the
content-durability law holds; there is no snapshot here.

### Offline semantics (the load-bearing part)

- **Fetching happens ONLY under `fux ingest --refresh-urls`.** A plain
  ingest never imports the middleware and carries every existing `url:`
  record forward **byte-identically** — necessary because the writer's
  implicit-deletion rule would otherwise silently drop url docs on every
  offline run. A missing `urls_file` is likewise only an error on a
  refresh.
- On a refresh: a configured URL whose fetch **fails keeps its prior
  record** (transient network failure ≠ document deletion); a URL removed
  from `.fux/sources/urls` disappears. Reconciliation only on the run that
  opted into the network.
- URLs are deduped and sorted before fetching; U+2028/U+2029/U+0085 and
  CRLF are normalized by the loader before bytes reach the canonical
  writer (`store/canonical.py` would refuse them loudly otherwise).

### Edges

An absolute `http(s)` markdown link now resolves to `url:<target>` iff that
exact URL is itself an ingested doc — dangling links stay dropped, same
rule as paths. `code`-span basename resolution remains file-only (a
backtick path is a claim about the repo, never about a URL). Relative
links inside fetched pages never resolve as repo paths.

## Consequences

- `src/fux/` still contains zero network code and zero new dependencies;
  the import-fence posture is unchanged. The only sockets live in the
  consumer's file, outside the package.
- Hashed meta gets its first real exercise ahead of M5's write-time
  enforcement; `fux ask` already displays `title_h`-only records (reader
  accepted both forms from day one, §7).
- `title_h` is defined as `term_hash(title)` (16-hex blake2b) — decided
  here; ADR-INDEX-FORMAT named the field but not its hash.
- The determinism law is scoped honestly: same *fetched text* → same
  bytes. The web itself is not deterministic; `sha`/`ver` absorb that,
  and refreshes are explicit, so committed-index churn is always an
  intentional act with a diff.
- The M4 refer plane will need a fetch path for `src:"url"` docs at
  verify time; the natural answer is this same middleware, decided then.
- ~~Owed: GLOSSARY entries ("url source", "middleware")~~ — paid by
  ADR-FUX-DIR's change. `fux doctor` still says nothing about middleware health
  (deliberate — doctor stays offline); its new checks are about layout, not
  the middleware.
- Tests: `tests/ingest/test_urlsrc.py` (contract, carry-forward, hashed
  default, determinism, reconciliation — all offline via a fake
  middleware) and `tests/ingest/test_cdp_middleware.py` (RFC 6455 framing
  round-trips, the §1.3 handshake vector, HTML→markdown, contract
  surface — no sockets).
