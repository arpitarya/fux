---
type: ADR
name: ADR-URL-INGEST
title: ADR-URL-INGEST (0008) — URL ingestion through consumer-owned fetcher
description: Fux never fetches. A consumer-owned file does, behind a four-function contract, only under the two named fenced paths (fux add <URL> and fux update), with the URL list as a committed line-oriented file.
status: accepted
timestamp: 2026-08-18T00:00:00Z
---

# ADR-URL-INGEST — URL ingestion through consumer-owned fetcher

- **Name:** `ADR-URL-INGEST` — cite this everywhere; never cite the number
- **Status:** accepted
- **Supersedes:** `ADR-URL-MIDDLEWARE` — **archived 2026-08-18** at
  [`archive/adr/`](../../archive/adr/README.md); it may be named, never cited
- **Owns:** nothing of its own — `src/fux/ingest/urlsrc.py` (fux's half of the
  fetch contract) moved to [ADR-FETCHER](0019_fetcher.md) when the contract
  split out; this record governs the `url:` source and the committed URL list
  format, enforced by [ADR-URL-LIST](0018_url-list.md)
- **Laws:** L2, L4, L5 — see [ADR-LAWS](0001_laws.md); never restated here
- **Date:** 2026-08-18
- **Feature:** the `url:` source and its fetcher boundary
- **Evidence:** [`work/regression/2026-08-18-ingest-and-index/`](../../work/regression/2026-08-18-ingest-and-index/report.md) §6

---

## §1 — For humans

**Fux does not fetch URLs. Your code does.**

You write a file — `.fux/fetchers/cdp.py` by default, from a shipped template
— that knows how to get a page: your browser, your proxy, your SSO, your
retries. Fux imports it by path, hands it one URL at a time, and takes back
markdown. Every line of network code lives on your side of that boundary, in
your repo, where you can read and change it.

This is what lets a single adapter cap hold. "Support Confluence behind our
SSO" stops being a feature request against fux and becomes fifteen lines in a
file you already own.

Two rules make it safe rather than merely clever. Fetching happens **only**
under the two named fenced paths — `fux add <URL>` and `fux update` — and a
plain ingest never even imports your file. And a page that fails to fetch is
recorded as a skip; it does **not** delete the document you already have,
because a flaky network must never look like a deletion.

**Diagram — Mermaid and its ASCII twin. Update both, always, together.**

```mermaid
flowchart LR
    subgraph fux ["fux — no network code"]
        R["fux add &lt;URL&gt; · fux update"]
        U[".fux/sources/urls<br/>committed, one per line"]
        N["normalize<br/>CRLF · U+2028/9/85 · NUL"]
        W["records src:url"]
    end
    subgraph yours ["your repo, your code"]
        M[".fux/fetchers/cdp.py<br/>fetch · configure · connect · close"]
    end
    U --> R
    R -->|"one URL at a time"| M
    M -->|"markdown, or raises"| N
    N --> W
    M -.->|"network lives here only"| NET(("the internet"))
```

<details>
<summary><b>ASCII twin</b> — the same diagram, for terminals, diffs, and any reader without a Mermaid renderer</summary>

```text
   fux  (no network code)                 your repo, your code
  +--------------------------+           +------------------------------+
  | .fux/sources/urls        |           | .fux/fetchers/cdp.py       |
  |   committed, 1 per line  |           |   fetch(url) -> str  REQUIRED|
  |            |             |  one URL  |   configure(cfg)    optional |
  |  add <URL> · update -----+---------->|   connect() / close()        |
  |            ^             |           +---------------+--------------+
  |            |  markdown, or raises                    |
  |     normalize (CRLF, U+2028/9/85, NUL)               v
  |            |                                  ( the internet )
  |            v
  |   records with src:"url"
  +--------------------------+

   A plain `fux ingest` never imports the fetcher at all.
```

</details>

### Examples

Offline is the default — a plain ingest never imports your fetcher:

```console
$ fux ingest
ingested 2 docs (0 changed), 2 skipped, 0 shards written
```

Either fenced path runs the whole contract, and a dead page is a **skip**, not a
crash:

```console
$ fux update
  [fetcher] configure({'greeting': 'hello'})
  [fetcher] connect()
  [fetcher] close()
ingested 4 docs (2 changed), 3 skipped, 2 shards written
  skip https://example.invalid/gone: fetch failed: 404 not found
```

---

## §2 — For agents

### Context

Fux's design point is a corporation's estate: Confluence behind SSO, wikis
behind proxies, pages a headless browser must render before there is any text.
Supporting that natively means auth code, transport code and browser code
inside the engine — and an adapter list that grows forever.

The adapter cap (git + HTTP + Confluence) is a decision, not a backlog. It only
survives if "fetch this page" can be answered **without** engine code. So the
question was never "which adapters", it was "where is the boundary".

### Decision

**1–2. The fetch contract left this record on 2026-08-19.** *Fux never
fetches; a consumer-owned fetcher does*, and the four-function contract that
states it, are now [ADR-FETCHER](0019_fetcher.md) decisions 1 and 2 — including
the rename from *middleware*, the `.fux/fetchers/` location, and the rule that
exactly one fetcher runs per URL. **They are not restated here**: a record that
paraphrases another is the paraphrase that drifts. What follows is what this
record still owns — how URL ingestion *behaves* around that contract.

**3. Fetching happens only under a named fenced path.** Since 2026-08-21
(W-63) there are **two** — `fux add <URL>`, scoped to the URL just added, and
`fux update`, which is what `--refresh-urls` retired into. A plain ingest
carries every listed `url:` record forward byte-identically and never imports
the fetcher. The count is not the rule; being named, fenced and opt-in is
(L4, [ADR-CLI](0002_cli-surface.md) decision 1e).

**4. A failed fetch keeps the prior record.** It is reported as a skip. A
transient failure must never present as a deletion.

**4a. Reconciliation is not fetching, and does not wait for it** (2026-08-21,
W-63). Only a URL *removed from the list* removes a document — and it does so
on the **next run, networked or not**. This decision used to end "and
reconciliation happens only on the run that opted into the network", which
made deleting a document require the one capability deletion has no use for.
That was a defect, not a design; it is [ADR-INGEST](0007_ingest.md)
decision 9, and it is what `fux remove <URL>` rests on.

**5–6. The file format left this record on 2026-08-19 too.** The committed
list, its grammar, its comment rule, the dedupe-and-sort, the closed attribute
set and the `file:lineno` errors are [ADR-URL-LIST](0018_url-list.md)
decisions 2–13, built in
[`sourcelist.py`](../../src/fux/ingest/sourcelist.py) and shared with
`.fux/sources/dirs`. **Not restated here.** What this record keeps is the
`read_urls` → `resolve_urls` → `fetch_all` pipeline in
[`urlsrc.py`](../../src/fux/ingest/urlsrc.py): parse, layer the source-wide
policy under the line, then fetch each URL through the fetcher its line
declared, importing only the fetchers some line actually names.

**7. `[sources.url.config]` is passed to `configure` verbatim** — moved to
[ADR-FETCHER](0019_fetcher.md) decision 8, where the contract lives.

**8. Fux normalizes what comes back**, rather than trusting it: CRLF to LF,
U+2028/U+2029/U+0085 to spaces, NUL stripped. Those are legal in JSON and
hostile to every line-oriented tool downstream.

**9. Hashed meta is the default for URL sources**, and `plain` is an explicit
per-source opt-in for public content. **See the defect in §Consequences: the
default currently does not work.**

### What it looks like

Verbatim from [the capture](../../work/regression/2026-08-18-ingest-and-index/report.md) §6,
using the no-network fetcher in
[`evidence/demo-fetcher.py`](../../work/regression/2026-08-19-w54/evidence/demo-fetcher.py).

**Offline is the default — the fetcher is not even imported:**

```console
$ fux ingest
ingested 2 docs (0 changed), 2 skipped, 0 shards written
```

**A fenced path runs the whole contract:**

```console
$ fux update
  [fetcher] configure({'greeting': 'hello'})
  [fetcher] connect()
  [fetcher] close()
ingested 4 docs (2 changed), 3 skipped, 2 shards written
  skip docs/empty.md: empty
  skip docs/logo.png: binary
  skip https://example.invalid/gone: fetch failed: 404 not found
```

`configure` receives `[sources.url.config]` verbatim, `connect`/`close` bracket
the batch, and the 404 becomes a skip while the other two documents land.

**A URL record**, `meta = "hashed"` — no display text, `title_h` instead of
`title`/`phrases`:

```json
{
  "id": "url:https://example.invalid/handbook/oncall",
  "loc": "https://example.invalid/handbook/oncall",
  "meta": "hashed",
  "mode": "extracted",
  "sha": "2643f1afb68339f2f808d85f67aad193b820dd86",
  "src": "url",
  "title_h": "h:30aef0c52cf11116",
  "ver": 1,
  "wlen": 11
}
```

### Consequences

- **`src/fux/` still contains zero network lines**, which is the property the
  adapter cap rests on.
- **Fetcher is not linted by default.** It lives in a dotdir and ruff skips
  those. Accepted: it is consumer code, not a CI target.
- **Hashed results are unreadable by design** — `fux ask` prints
  `30aef0c52cf11116` where a title would be. That is the mode working, and it
  is a real usability cost worth stating rather than discovering.
- **The default was broken, and is fixed (2026-08-19).** With
  `meta = "hashed"`, the networked path wrote the committed index and
  then **failed at the accelerator build, exit 1**, and every later `fux build`
  failed too: the bare 16-hex `title_h` tripped the invariant that keeps the
  scan and the accelerator in agreement, so a corpus with one hashed URL record
  was stuck on the reference scan permanently — 27.2 ms against 4 248.8 ms at
  RFC scale, the whole M2 result forfeited by following the documentation.
  Diagnosis in
  [ANALYSIS.md](../../work/regression/2026-08-18-ingest-and-index/ANALYSIS.md).
  **The fix was the field's shape**, `"h:" + term_hash(...)`
  ([ADR-RECORD](0010_index-record.md) rule 2), not the check — and the
  differential harness now carries a hashed record, which it never had.
- **This record is itself accepted, not proposed** — ratified as-is by W-31
  ([IMPLEMENTATION.md](../../work/IMPLEMENTATION.md), 2026-08-19).

### Alternatives considered

- **Built-in HTTP fetching.** Rejected: puts auth, proxy and retry code in the
  engine, and every enterprise variation becomes an engine change.
- **A plugin API with a registry and entry points.** Rejected as heavier than
  the problem: a file path and four function names need no packaging,
  versioning or discovery, and the consumer can read the whole thing.
- **A subprocess protocol** (fux shells out, JSON on stdout). Rejected: an
  import is simpler to write, debug and test, and the trust boundary is the
  same — it is the consumer's own repo either way.
- **URLs as a TOML array in `fux.toml`.** Rejected on diff and merge behaviour
  at enterprise scale; a line-oriented file is what git is good at.
- **Fetch on every ingest, with a cache.** Rejected: it makes the network a
  dependency of the ordinary path, and offline-by-default is the property that
  lets ingest run on a hook.

### Reference (required)

- The fux half of the contract —
  [`src/fux/ingest/urlsrc.py`](../../src/fux/ingest/urlsrc.py) (its docstring
  is the normative statement of the four functions).
- The carry-forward rule — [`src/fux/ingest/run.py`](../../src/fux/ingest/run.py)
  module docstring.
- A working no-network fetcher, and the captured session —
  [`work/regression/2026-08-18-ingest-and-index/`](../../work/regression/2026-08-18-ingest-and-index/report.md) §6.
- The opaque-config-table discipline this copies — PEP 518 `[tool.*]`:
  https://peps.python.org/pep-0518/#tool-table
- The transport the shipped template uses — Chrome DevTools Protocol:
  https://chromedevtools.github.io/devtools-protocol/

### Veto condition

**Reopen this decision if** engine code acquires a network call, or if the
fetcher boundary stops being sufficient — concretely, if a consumer cannot
express a needed source without changing `src/fux/`.

**How to check it:**

```bash
# 1. the engine still has no network code — the property the cap rests on
grep -rnE '^\s*(import|from)\s+(socket|http|urllib|ssl|asyncio|requests|httpx)' src/fux/
# expect: no output

# 2. fetching is still gated — one branch, reached only by the two fenced paths
grep -n 'refresh_urls\|only_urls' src/fux/ingest/run.py
# expect: the fetcher load sits inside the `if refresh_urls:` branch and nowhere
#         else; `only_urls` narrows WHICH listed URLs it fetches, never whether

# 2b. removal does NOT need the network (W-63) — this must have no gate at all
grep -n '_listed_url_ids' src/fux/ingest/run.py
# expect: called on the offline branch; reading a committed file is not a fetch

# 3. the config table is still opaque — fux must never read a key inside it
grep -rn 'url.config\[' src/fux/
# expect: no output (passed verbatim to configure(), never indexed)
```
---

## References

*Every source this record cites, gathered in one place. §2's **Reference
(required)** names the grounding; this is the complete list. An archived
document is never listed here — the body may name one, but archive is not
evidence.*

**Records** — [ADR-LAWS](0001_laws.md) · [ADR-CLI](0002_cli-surface.md) ·
[ADR-INGEST](0007_ingest.md) · [ADR-RECORD](0010_index-record.md) ·
[ADR-URL-LIST](0018_url-list.md) · [ADR-FETCHER](0019_fetcher.md)

**Code**

- [`src/fux/ingest/run.py`](../../src/fux/ingest/run.py)
- [`src/fux/ingest/sourcelist.py`](../../src/fux/ingest/sourcelist.py)
- [`src/fux/ingest/urlsrc.py`](../../src/fux/ingest/urlsrc.py)

**Measured evidence**

- [`work/regression/2026-08-18-ingest-and-index/ANALYSIS.md`](../../work/regression/2026-08-18-ingest-and-index/ANALYSIS.md)
- [`work/regression/2026-08-18-ingest-and-index/report.md`](../../work/regression/2026-08-18-ingest-and-index/report.md)
- [`work/regression/2026-08-19-w54/evidence/demo-fetcher.py`](../../work/regression/2026-08-19-w54/evidence/demo-fetcher.py)

**Project docs**

- [`work/IMPLEMENTATION.md`](../../work/IMPLEMENTATION.md)

**Papers and specifications**

- Chrome DevTools Protocol — the transport the shipped browser template uses
  <https://chromedevtools.github.io/devtools-protocol/>
- PEP 518 `[tool]` table — the opaque-config-table discipline this copies
  <https://peps.python.org/pep-0518/#tool-table>
