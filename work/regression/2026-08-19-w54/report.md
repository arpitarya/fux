---
type: Report
title: "2026-08-19 — W-54: the URL path, exercised offline end to end"
description: "A surface capture of the sources rewrite: fux setup writes the fetchers, the one grammar parses both lists, a fragment survives, and a corpus holding hashed records builds — exit 0."
timestamp: 2026-08-19T00:00:00Z
---

# 2026-08-19 — W-54: the URL path, exercised offline end to end

**This is a surface capture, not a measurement.** Every block below is
verbatim output from the commands shown. It pre-registers no threshold and
gates no prediction. What it does is close four defects that this repo's own
test suite could not have caught, and it exists because of the reason W-54
states plainly:

> **This repo does not exercise the URL path** — there is no
> `.fux/sources/urls` and `[sources.url]` is commented out in `fux.toml`.
> Every defect here is therefore latent: shipped, real, and with no current
> victim.

`pytest -q tests` passing says nothing about four of W-54's five defects,
because nothing in this repo's corpus reaches them. This fixture is what says
something.

## Reproduce

```bash
FUX=/path/to/fux work/regression/2026-08-19-w54/evidence/fixture.sh /tmp/fux-w54-demo
cd /tmp/fux-w54-demo
fux url && fux ingest && fux ingest --refresh-urls && fux build && fux doctor
```

Offline throughout: the fixture replaces both shipped fetchers with a
deterministic stand-in ([`evidence/demo-fetcher.py`](evidence/demo-fetcher.py))
that serves five fixed pages and raises on a sixth. No network, no Chrome, no
CI secret.

**Successor to
[`2026-08-18-ingest-and-index/evidence/fixture.sh`](../2026-08-18-ingest-and-index/evidence/fixture.sh)**,
which reproduces the *pre-W-54* surface (`[sources.url] middleware`,
`[sources] dirs`). That fixture was **not** edited: it is the evidence of what
that run measured, and rewriting a filed run's evidence so it no longer
reproduces that run's numbers falsifies the run. It is superseded here, in the
way this directory supersedes anything — by a newer run.

## §1 — A fresh tree, and no hand-written fetcher

The defect W-54 §3 closes: `DEFAULT_FETCHER` named a file that did not exist,
and there was no supported way to obtain one.

```console
$ fux setup
  wrote .fux/README.md
  wrote .fux/.gitignore
  wrote .fux/fetchers/http.py
  wrote .fux/fetchers/cdp.py
  wrote .fux/sources/dirs
  wrote .fux/sources/urls
  wrote fux.toml
setup: 7 file(s) written. They are yours: commit them, edit them, fux will not rewrite them.
next: add entries to .fux/sources/dirs, then `fux ingest`
```

Nothing was copied in from this repo. Both fetchers came out of the installed
wheel as package data, and the fixture asserts both exist before continuing.

## §2 — The managing verb, and a list it did not fully write

```console
$ fux url https://example.invalid/handbook/deploys --cdp
added     https://example.invalid/handbook/deploys fetch=cdp meta=hashed
  in .fux/sources/urls — commit it; `fux ingest --refresh-urls` fetches

$ fux url
* https://example.invalid/gone fetch=http meta=hashed
  https://example.invalid/handbook#deploys fetch=http meta=hashed
  https://example.invalid/handbook#oncall fetch=http meta=hashed
  https://example.invalid/handbook/deploys fetch=cdp meta=hashed
* https://example.invalid/handbook/oncall fetch=http meta=hashed
  https://example.invalid/public/api fetch=http meta=plain

* 2 line(s) do not state every attribute, so fux did not write them. They load fine (the reader is lenient); `fux url <URL>` rewrites one in full.
```

The `*` is ADR-URL-LIST decision 13 working: the fixture wrote some lines by
hand on purpose, they load, and the completeness check reports them rather
than refusing them.

## §3 — Offline by default, then the one networked path

```console
$ fux ingest
ingested 2 docs (2 changed), 0 skipped, 2 shards written
accelerator: 33 terms, 33 blocks, 35 postings (derived, not committed)

$ fux ingest --refresh-urls
  [fetcher] configure({'greeting': 'hello'})
  [fetcher] connect()
  [fetcher] close()
  [fetcher] configure({'greeting': 'hello'})
  [fetcher] connect()
  [fetcher] close()
ingested 7 docs (5 changed), 1 skipped, 5 shards written
  skip https://example.invalid/gone: fetch failed: 404 not found
accelerator: 57 terms, 57 blocks, 69 postings (derived, not committed)
```

**Two `configure`/`connect`/`close` brackets, not one.** Five URLs route to two
fetchers — four to `http.py`, one to `cdp.py` because its line says
`fetch=cdp` — and each group is bracketed separately. A fetcher no line names
is never imported at all.

A failed fetch is a skip that keeps the prior record, not a deletion.

## §4 — The defect with a measured cost: hashed meta now builds

W-54 §4. `meta = "hashed"` is the default and an L5 default; under it,
`--refresh-urls` used to write an index that no `fux build` would ever accept.

```console
$ fux build
accelerator rebuilt from the committed index: 7 docs, 57 terms, 57 blocks, 69 postings
# exit 0
```

```console
$ ls .fux/runtime/manifest.json
.fux/runtime/manifest.json
{'docs': 7, 'terms': 57, 'blocks': 57, 'analyzer': 'v1', 'index_schema': 'fux.index.v1'}
```

**`analyzer` is `v1` and `index_schema` is `fux.index.v1` — unchanged.** That
is ADR-INDEX-LIFECYCLE decision 9 visible in the artefact: the `title_h` shape
changed and neither version moved, because the property set did not change,
`title_h` is not a term, and the old shape is already refused per record with
the migration named.

## §5 — The five URL records, as committed

```json
{"id": "url:https://example.invalid/handbook#deploys", "meta": "hashed", "title_h": "h:a73cb6b8319268d5", "wlen": 11}
{"id": "url:https://example.invalid/handbook#oncall",  "meta": "hashed", "title_h": "h:2a33413e00f63cb3", "wlen": 11}
{"id": "url:https://example.invalid/handbook/deploys", "meta": "hashed", "title_h": "h:29d574ede4d0db02", "wlen": 12}
{"id": "url:https://example.invalid/handbook/oncall",  "meta": "hashed", "title_h": "h:30aef0c52cf11116", "wlen": 11}
{"id": "url:https://example.invalid/public/api",       "meta": "plain",  "title": "Public API reference", "wlen": 16}
```

Four things to read here, and each is one of W-54's defects:

- **A fragment survived.** `.../handbook#oncall` is in the index as itself.
  Before, `#` began a comment anywhere on the line and it loaded as
  `.../handbook`.
- **Two URLs differing only by fragment are two records.** `#oncall` and
  `#deploys` both exist, with different `wlen` and different `title_h`. Before,
  they collapsed into one under the dedupe and one document disappeared with
  **no error at all** — the failure ADR-URL-LIST decision 5 exists to prevent,
  reached by a different route.
- **`title_h` carries its `h:` prefix**, which is why §4 exits 0.
- **`meta=plain` loosened the floor for exactly one document.** The public API
  page carries a readable `title`; every other URL record carries none. The
  source-wide setting stayed `hashed`.

## §6 — The differential, over a corpus the harness had never seen

`fux ask` and `fux ask --scan` must return byte-identical `--json` payloads.
The harness had never run against a corpus containing a hashed record — which
is precisely why it never saw W-47.

```console
$ for q in "oncall pager" "deploys frozen" "handbook" "public api" "refer plane"; do
    diff <(fux ask "$q" --json --top 20) <(fux ask "$q" --json --top 20 --scan) >/dev/null \
      && echo "IDENTICAL  $q" || echo "DIVERGED   $q"
  done
IDENTICAL  oncall pager
IDENTICAL  deploys frozen
IDENTICAL  handbook
IDENTICAL  public api
IDENTICAL  refer plane
```

And a hashed record still answers, opaquely, which is the mode working as
designed and a real usability cost:

```console
$ fux ask "pager" --explain
1.8967  30aef0c52cf11116  (https://example.invalid/handbook/oncall)

[accelerator]
```

**The prefix is storage, not display.** The index holds `h:30aef0c52cf11116`;
the verb prints the hash. A reader cannot tell the field's shape changed, which
is exactly why the change did not need an `_format` bump.

## §7 — Doctor, on the finished tree

```console
$ fux doctor
[OK] python version: 3.14, fux 0.32.0
[OK] repo root: /private/tmp/fux-w54-cap
[OK] .fux/ writable: /private/tmp/fux-w54-cap/.fux
[OK] index not gitignored: the committed index is tracked
[OK] .fux/ layout declared: every entry is declared
[OK] accelerator: fresh, derived, untracked (/private/tmp/fux-w54-cap/.fux)
```

## What this run does not show

- **No timing.** Seven documents measures nothing about speed, and reporting a
  number from this corpus would be the overclaim the pre-registration
  discipline exists to stop. The 27.2 ms → 4 248.8 ms cost of the hashed-meta
  defect is
  [the M2 run's](../2026-08-12-m2-accelerator/report.md) number, cited here,
  not re-derived.
- **No real network.** The stand-in fetcher is deterministic by construction,
  so nothing here exercises `urllib`, redirects, charset decoding, or the CDP
  transport. Those stay covered by unit tests over the pure parts and by a
  human running it once.
- **No `archived=` behaviour.** The declaration parses; nothing reads it. That
  is deliberate and gated on W-44's instrument
  ([ADR-DIR-LIST](../../../docs/adr/0022_dir-list.md) decision 10).
