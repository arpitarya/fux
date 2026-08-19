---
type: ADR
name: ADR-CDP-FETCHER
title: "ADR-CDP-FETCHER (0020) — the CDP fetcher"
description: "The browser fetcher, for pages a plain GET cannot read. Drives your existing Chrome over CDP on a hand-rolled stdlib WebSocket; declared per URL, never escalated to."
status: accepted
timestamp: 2026-08-19T00:00:00Z
---

# ADR-CDP-FETCHER — the browser fetcher

- **Name:** `ADR-CDP-FETCHER` — cite this everywhere; never cite the number
- **Status:** accepted
- **Date:** 2026-08-19
- **Feature:** `.fux/fetchers/cdp.py` — the reference fetcher for pages that only exist after JavaScript runs, or behind a session a headless client does not have
- **Owns:** nothing in `src/` — it is **consumer code**, and the ownership table covers `src/` and `tools/`. Its test is [`tests/ingest/test_cdp_fetcher.py`](../../tests/ingest/test_cdp_fetcher.py)
- **Laws:** L1, L4 — see [ADR-LAWS](0001_laws.md); never restated here
- **Implements:** [ADR-FETCHER](0019_fetcher.md)

---

## §1 — For humans

Some documents do not exist in the HTML a plain GET returns. A Confluence page,
an internal dashboard, anything rendered client-side — the bytes on the wire are
a loading shell, and the document you wanted appears only after JavaScript runs.
Worse, the ones worth indexing are usually the ones behind a login.

`cdp.py` handles both by **driving the browser you already have**. It attaches
to your running Chrome over the Chrome DevTools Protocol, navigates, waits for
load, settles, and reads the rendered `outerHTML` — then converts it to markdown
deterministically. Because it is *your* browser, it is *your* session: pages you
are logged into are pages it can read, with no credential ever entering fux's
config.

Two properties are worth stating because neither was forced:

**It carries no dependency.** The WebSocket client is hand-rolled RFC 6455 on
stdlib `socket`; the HTML→markdown pass is `html.parser`. L1 binds fux's
runtime, not your fetcher — this file could have imported `websockets` and
nothing would have broken. It does not, so `pip install fux-engine` remains the
whole install even for the browser path.

**It is never escalated to.** A URL uses this fetcher because a human wrote
`fetch=cdp` on its line ([ADR-URL-LIST](0018_url-list.md)), not because a
cheaper fetch failed and something retried. That is
[ADR-FETCHER](0019_fetcher.md) decision 5, and it is what keeps the same URL
producing the same bytes on a bad network day.

**Diagram — Mermaid and its ASCII twin. Update both, always, together.**

```mermaid
flowchart LR
    U["url with fetch=cdp"] --> D["discover or launch<br/>your Chrome"]
    D --> W["WebSocket<br/>hand-rolled RFC 6455"]
    W --> N["Page.navigate<br/>wait loadEventFired<br/>settle"]
    N --> E["Runtime.evaluate<br/>rendered outerHTML"]
    E --> M["HTML to markdown<br/>deterministic"]
```

<details>
<summary><b>ASCII twin</b> — the same diagram, for terminals, diffs, and any reader without a Mermaid renderer</summary>

```text
  url (fetch=cdp)
        |
        v
  discover or launch YOUR Chrome  --(never a bundled browser)
        |
        v
  WebSocket: hand-rolled RFC 6455 on stdlib socket  --(no dependency)
        |
        v
  Page.navigate -> wait loadEventFired -> settle_ms
        |
        v
  Runtime.evaluate: rendered outerHTML
        |
        v
  HTML -> markdown, deterministic  -->  one document
```

</details>

### Examples

Declare it per URL — only lines that need a browser get one
([ADR-URL-LIST](0018_url-list.md)):

```console
$ cat .fux/sources/urls
https://example.com/docs/api                 # plain GET; no fetcher decision
https://wiki.corp/display/ENG/runbook        fetch=cdp
```

Tune it from `fux.toml`, never by editing the file, so your edits and an
upgrade cannot collide:

```toml
[sources.url]
fetcher = ".fux/fetchers/cdp.py"

[sources.url.config]        # fux passes this VERBATIM and reads no key in it
cdp_port       = 9222
settle_ms      = 500
load_timeout_s = 30
launch_chrome  = true
```

The entry points, a captured run, and the record it produces are in §2.
---

## §2 — For agents

### Context

[ADR-FETCHER](0019_fetcher.md) says fux never fetches, which is only useful if a
fetcher exists that can reach the documents the design point actually cares
about. The litmus is a large corporate corpus: Confluence, SharePoint, internal
wikis. Those are the JavaScript-rendered, session-gated case, not the static-file
case — so the *first* fetcher had to be the hard one, or the cap would have
looked like a way to avoid the problem rather than a way to place it.

The transport was already solved and thrown away once: the archived v0.26 engine
shipped and dogfooded this exact path (`ws.py`, `cdp.py`, `htmlmd.py`). Porting
it was cheaper than rebuilding it and is covered by
[ADR-PORT-LIST](0015_port-list.md)'s discipline of porting with tests rather
than rewriting.

### Decision

**1. Drive the user's existing Chrome; never bundle or download a browser.**
Discover a running instance on the configured port, or launch the one already
installed. A tool that downloads a browser has a several-hundred-megabyte
install and an air-gap story it cannot tell.

**2. Stdlib only, by choice.** RFC 6455 hand-rolled on `socket`, HTML parsed
with `html.parser`. L1 binds fux's runtime and not consumer code, so this is a
choice — made so that the browser path costs no install step and the file stays
readable as a worked example of the contract.

**3. Ported from the archived v0.26 engine, with its tests.** `ws.py`, `cdp.py`
and `htmlmd.py`, which shipped and were dogfooded on this path. Named, not
cited — the archive is not evidence.

**4. Tunables come from `[sources.url.config]`, not from editing the file.**
The constants in the file are *defaults*; the table overrides them. This is what
keeps a consumer's `fux.toml` diff small and their fetcher file mergeable, and
it is [ADR-FETCHER](0019_fetcher.md) decision 8 in use.

**5. HTML→markdown is deterministic** — same bytes in, same markdown out, no
model, no heuristic scoring. It runs inside `--refresh-urls`, but what it
produces has to be as reproducible as a repo file or the index stops being
byte-reproducible for URL documents.

**6. This fetcher is chosen by declaration.** `fetch=cdp` on the URL's line.
It is never the target of an automatic escalation from a cheaper fetcher —
[ADR-FETCHER](0019_fetcher.md) decision 5.

**7. It is yours.** Committed to your repo, never rewritten by fux, and every
part of it — port, wait strategy, extraction, even the transport — is editable.
Swapping in Playwright is a supported outcome; fux imports none of it, only the
four entry points.

**8. It reaches your repo through `fux setup`, and only then.** Amended
2026-08-19: the file ships in the wheel as package data
([`src/fux/templates/cdp.py.txt`](../../src/fux/templates/cdp.py.txt)) with an
extension Python cannot import, and `fux setup` copies it into
`.fux/fetchers/cdp.py` write-if-missing. **Ingest never writes it** — a repo
that indexes only local files never sees a byte of WebSocket code, which is
what decision 1's "never bundle a browser" is worth nothing without.

### What it looks like

**The four entry points, as this file implements them**
([`src/fux/templates/cdp.py.txt`](../../src/fux/templates/cdp.py.txt), copied
to `.fux/fetchers/cdp.py` by `fux setup`):

```python
def configure(config: dict) -> None: ...   # [sources.url.config], verbatim;
                                           # module constants are only defaults
def connect() -> None: ...                 # discover Chrome on cdp_port, or
                                           # launch the installed one
def fetch(url: str) -> str: ...            # navigate -> loadEventFired ->
                                           # settle -> outerHTML -> markdown.
                                           # Raises: fux skips, keeps prior record
def close() -> None: ...                   # called even if a fetch raised
```

**A run**, captured against the no-network fetcher that stands in for this one
in [the filed fixture](../../work/regression/2026-08-18-ingest-and-index/report.md) §6.
The lifecycle is the real thing; only the transport differs:

```console
$ fux ingest --refresh-urls
  [fetcher] configure({'greeting': 'hello'})
  [fetcher] connect()
  [fetcher] close()
ingested 4 docs (2 changed), 3 skipped, 2 shards written
  skip https://example.invalid/gone: fetch failed: 404 not found
```

`configure` receives the table verbatim, `connect`/`close` bracket the batch,
and a failed page is a **skip** that keeps the previous record — never a
deletion.

**What lands in the index.** Nothing in the record says a browser was involved:
`fetch=` is a routing decision, not a property of the document
([ADR-URL-LIST](0018_url-list.md) §The attribute set). Captured, `meta` left at
its `hashed` default — note `title_h`, its `h:` prefix
([ADR-RECORD](0010_index-record.md) rule 2), and the absence of
`title`/`phrases`:

```json
{
  "id":      "url:https://example.invalid/handbook/oncall",
  "loc":     "https://example.invalid/handbook/oncall",
  "src":     "url",
  "meta":    "hashed",
  "mode":    "extracted",
  "sha":     "2643f1afb68339f2f808d85f67aad193b820dd86",
  "title_h": "h:30aef0c52cf11116",
  "ver":     1,
  "wlen":    11
}
```

**`mode` is `extracted`.** A browser rendered the page and the record is still
deterministic: what the fetcher returns is *bytes*, and everything after that is
the same extraction any repo file gets ([ADR-EXTRACTED](0016_extracted-mode.md)).
**Rendering is not enrichment.**

### Consequences

- **A browser must exist on the machine that ingests.** Fine for a developer
  laptop and for most CI, and it is the price of reading pages that only exist
  after JavaScript. A URL that does not need it should not declare `fetch=cdp`.
- **This is the slow path.** A browser round trip per URL, plus a settle. It is
  why [ADR-HTTP-FETCHER](0021_http-fetcher.md) is the default and this is the
  opt-in, rather than the other way round.
- **It is not linted** ([ADR-FETCHER](0019_fetcher.md) §Consequences) and it is
  ~600 lines of consumer code carrying a protocol implementation. Its test
  exists precisely because nothing else guards it.
- **It is not shipped, though two docstrings said it was.** The wheel packages
  `src/fux` only, and `GENERATED_FILES` does not include it, so this file exists
  in *this* repo and nowhere else — [W-54](../../work/open/W-54-sources-rewrite.md).

### Alternatives considered

- **Playwright or Selenium.** Rejected for the default reference fetcher: a
  dependency plus a browser download, and the thing being demonstrated is that
  the contract needs neither. Still fully supported as *your* choice — decision 7.
- **A bundled headless browser.** Rejected under decision 1: install size, and
  it breaks the air-gapped and locked-down-corporate story that is the whole
  design point.
- **`requests` + a readability heuristic.** Rejected: a dependency, and it does
  not solve the case this fetcher exists for — a page that has not rendered yet
  has nothing to be readable about.
- **Making this the default fetcher.** Rejected: it demands a browser for URLs
  that a plain GET would have answered. See
  [ADR-HTTP-FETCHER](0021_http-fetcher.md).

### Reference (required)

- The file itself — [`.fux/fetchers/cdp.py`](../../.fux/fetchers/cdp.py), whose
  module docstring states the contract it implements.
- Its test, including that it lives in the declared plane —
  [`tests/ingest/test_cdp_fetcher.py`](../../tests/ingest/test_cdp_fetcher.py).
- The contract — [ADR-FETCHER](0019_fetcher.md).
- The behaviour around it, captured against a no-network fetcher —
  [`work/regression/2026-08-18-ingest-and-index/`](../../work/regression/2026-08-18-ingest-and-index/report.md) §6.
- The WebSocket framing this implements — RFC 6455:
  https://www.rfc-editor.org/rfc/rfc6455
- The protocol it speaks — Chrome DevTools Protocol:
  https://chromedevtools.github.io/devtools-protocol/

### Veto condition

**Reopen this decision if** the file acquires an `import` outside the standard
library, or if it stops being reachable only by declaration — either means the
two properties §1 claims for it are no longer true of the bytes.

**How to check it:**

```bash
# 1. stdlib only
grep -nE "^\s*(import|from) " .fux/fetchers/cdp.py \
  | grep -vE "socket|ssl|json|base64|hashlib|struct|os|sys|time|re|html|urllib.parse|subprocess|shutil|pathlib|typing|dataclasses|__future__"
# expect: no output

# 2. no browser is downloaded or bundled
grep -niE "download|install|playwright|selenium" .fux/fetchers/cdp.py
# expect: no output outside prose about swapping it yourself

# 3. it is still chosen by declaration, not escalation
grep -rn "fetch=cdp\|escalat\|fallback" src/fux/ingest/urlsrc.py
# expect: no automatic-escalation logic in fux's half
```
