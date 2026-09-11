---
type: OpenItem
id: W-113
title: "W-113 — `update=` : a declared per-URL policy for whether `fux update` goes out at all"
description: "Arpit, 2026-09-05, deciding R-1. A URL line can say keep=, ttl=, fetch= and meta= but cannot say whether it should be re-fetched. `ttl=` is ask-time and does not reach `fux update`. Add `update = auto|never`, resolved through the same three layers as keep/ttl/enrich, so a pinned reference stops opening a socket. It buys bandwidth by giving up freshness — it is NOT the ETag saving, and the record says so."
status: open
lane: agent
timestamp: 2026-09-05T00:00:00Z
---

# W-113 — `update=`, a declared refresh policy per URL

**Model: Opus.** Small code, but it adds a committed attribute to a source
list, touches two accepted records, and its whole value is in a boundary
being stated correctly. A wrong sentence here reads as authority.

## Where this came from

**Arpit ruled R-1 on 2026-09-05** ([`proposals/unblock-2026-09-05.md`](../proposals/unblock-2026-09-05.md)):
accept [ADR-CDP-FETCHER](../../docs/adr/0028_cdp-fetcher.md) decision 12 as
the ETag acceptance criterion — **and separately** expose whether a URL is
re-fetched at all as a declared property. This item is that second half. The
first half closes with no code.

## The gap, verified in the tree (2026-09-05)

`UrlEntry` carries `fetch`, `meta`, `keep` and `ttl`
([`src/fux/ingest/urlsrc.py`](../../src/fux/ingest/urlsrc.py) lines 66-81).
**None of them decides whether `fux update` goes out.**

- 🔴 **`ttl=` is ask-time and only ask-time.** It becomes
  `Policy.cache_ttl_seconds` in [`refer/freshness.py`](../../src/fux/refer/freshness.py)
  and bounds how long `fux answer` may cite without re-checking. It is *not*
  an update-time knob, and a second time-shaped key beside it would be read
  as one. **`update=` is deliberately not a duration.**
- `[sources.url]` in `fux.toml` has `fetcher`, `urls_file`, `meta`,
  `max_parallel` and the opaque `config` table. No refresh policy.

## Goal

A line can say *"this document is pinned — never go out for it"*, and
`fux update` honours it without a socket. The default is today's behaviour,
byte for byte.

## The shape

```
# .fux/sources/urls
https://www.rfc-editor.org/rfc/rfc7693   keep=true update=never
https://wiki.internal/runbook            update=auto
```

```toml
[sources.url]
update = "auto"     # the default for a line that does not say
```

- **Two values only: `auto` (today) and `never`.** No third value until one
  is measured. In particular **no `etag` value** — see the boundary below.
- **Three layers, exactly as `keep`/`ttl`/`enrich` already resolve**
  (`urlsrc.resolve_urls`, lines 142-166): built-in default → `[sources.url]`
  → the line. A line that *declared* it wins; silence takes the source-wide
  value.
- **`update=never` + `keep=true` is the coherent pair**: the bytes are
  retained in `.fux/acquired/`, `answer` verifies against them and reports
  `as-ingested` (ADR-ACQUIRED), and nothing opens a socket. That is *more*
  offline, with the grain of L4.
- **`update=never` + `keep=false` is legal and lossy** — the document is
  frozen at its indexed statistics with no bytes to verify against.
  `fux doctor` says so; it is not refused.

## Definition of done

- [ ] `UrlEntry.update: str = "auto"`; `resolve_urls` resolves it through the
      three layers; an unknown value is a loud `FuxError` naming the line.
- [ ] `UrlSource.update` in [`config.py`](../../src/fux/config.py) +
      `config.schema.json`; `fux.toml`'s commented block documents it.
- [ ] `fux update` and `fux ingest --refresh-urls` skip a `never` line
      **before the fetcher is resolved** — no import, no connect, no socket.
      The skip is reported on stderr with its reason, in the existing skip
      vocabulary (*not indexed* / *skipped* — this is a third word, and
      ADR-URL-LIST decides which).
- [ ] `fux add <URL> --no-update` writes `update=never` on the line it
      records. ⚠ `fux add` **still fetches once** — that is what makes the
      line ingestable at all; the flag governs every run after.
- [ ] `fux doctor`: count of `update=never` lines, and a warning for
      `never` + `keep=false`.
- [ ] Tests: three-layer resolution incl. line-beats-source; the no-socket
      assertion (a fetcher whose `fetch` raises is never called); an unknown
      value refused; `tests_e2e` covering `fux update` over a mixed list.
- [ ] **Byte-identity**: a corpus that declares nothing produces the same
      `.fux/index/` and the same `fux update` behaviour as before.
- [ ] [ADR-URL-LIST](../../docs/adr/0026_url-list.md) gains the attribute and
      the skip vocabulary; [ADR-URL-FRESHNESS](../../docs/adr/0059_url-freshness.md)
      gains the ask-time/update-time boundary in one paragraph;
      [ADR-CDP-FETCHER](../../docs/adr/0028_cdp-fetcher.md) decision 12 gains
      the veto condition below. CHANGELOG; `IMPLEMENTATION.md`; this file to
      `archive/open/`.

## 🔴 The boundary this item must state, not blur

**`update=never` buys bandwidth by giving up freshness. It is NOT the saving
the original ETag criterion promised**, and the records must not let a later
reader think it was.

- The ETag promise was *"check cheaply and stay fresh"*. CDP intercepts at the
  **response** stage, so the body has already crossed the wire; a matching
  ETag saves the decode and the shard comparison, not the transfer
  (ADR-CDP-FETCHER decision 12).
- The only thing that would deliver the original promise is **request-stage
  interception** — `Fetch.requestPaused` at the Request stage, injecting
  `If-None-Match`, letting the server answer `304`. **Not costed, not built,
  and not authorised by this item.**

**The veto condition, added to ADR-CDP-FETCHER decision 12 in this change:**

> *If a consumer reports refresh bandwidth as a blocker — or a corpus with
> more than a few hundred `update=auto` URLs is deployed behind a metered or
> proxied network — request-stage interception is re-costed. Until then the
> response-stage cost is accepted knowingly.*

A condition to check, never an event to await (ADR standing rules).

## Hazards

- 🔴 **Do not add a duration.** The moment `update=` takes `24h` it is
  indistinguishable from `ttl=` at a glance and the two will be conflated in
  a support thread. Two values, both words.
- 🔴 **Skip before resolving the fetcher.** Resolving imports consumer code;
  a `never` line must not execute a fetcher module at all.
- `fux add <URL> --no-update` still performs one fetch. Say it in `--help`,
  not only in the record.
- A `never` line whose blob was never kept has nothing to verify against —
  disclose, do not refuse.
- The URL list is **committed**: a new attribute changes a file every clone
  has. Silence must resolve to today's behaviour or every existing repo moves.

## ⚠ Repointed 2026-09-06

The ADR register was **renumbered wholesale** on 2026-09-06 (ADR-CLI `0002`
→ `0010`, ADR-CONFIG `0014` → `0022`, and so on) and the eight law records
were split out. Every path above was updated in that sweep; the **names** —
ADR-URL-LIST, ADR-URL-FRESHNESS, ADR-CDP-FETCHER — never moved, which is
what the cite-by-name rule is for. **Re-derive before editing**: a
concurrent session was live in the tree when this was written.

## Out of scope

Request-stage interception. Any change to `ttl=` or the refer plane. A
duration-valued `update=`. Anything about `dirs` lines — this is the URL
list only.
