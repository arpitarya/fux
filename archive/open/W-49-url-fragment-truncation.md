# W-49 — a URL fragment is silently truncated, and can delete a document

**Status:** OPEN (Lane A — agent-executable) · **Filed:** 2026-08-19
**Blocked by:** — · **Model:** **Sonnet.** A three-line parser change against a
written definition of done — *but read the hazard first: the fix interacts with
[W-50](W-50-url-fetch-mechanism.md), which rewrites the same parser.*
**Opened by:** [ADR-URL-LIST](../../docs/adr/0018_url-list.md) §Consequences

## The defect

`read_urls` strips from the **first `#` anywhere on the line**:

```python
line = raw.split("#", 1)[0].strip()
```

A URL fragment is part of the URL. So:

```text
https://wiki.corp/handbook#oncall      ->  https://wiki.corp/handbook
https://wiki.corp/handbook#deploys     ->  https://wiki.corp/handbook
```

Both lines collapse to the same URL, the loader's `set` dedupes them, and
**one document leaves the corpus with no error and no skip line.** The other is
indexed under a locator that is not what the file said.

## Why it matters

This is the exact failure [ADR-URL-LIST](../../docs/adr/0018_url-list.md)
decision 5 exists to prevent — a line that does not mean what it says, failing
silently — reached by a different route. Decision 5 makes a typo'd *scheme* a
loud error precisely because "quietly fetching nothing is worse than a stopped
run"; a truncated fragment quietly fetches **the wrong page**, which is worse
again, because the record looks healthy.

Fragment-addressed documents are not exotic in the target corpus: Confluence
anchors, single-page handbooks with `#section` deep links, and generated API
docs all rely on them.

**Severity is bounded but real.** No URL source ships in this repo's own
`fux.toml`, so nothing is currently mis-indexed here. It bites the first
consumer who lists an anchored URL.

> **2026-08-19 — option A is now forced, not merely recommended.**
> [ADR-URL-LIST](../../docs/adr/0018_url-list.md) decision 7 makes a line
> whitespace-delimited (`<url> key=value …`). Under that grammar `#` **must**
> mean a comment only at line start or after whitespace, or
> `https://x/a#frag meta=plain` cannot be parsed at all. The options below are
> kept for the record; **A is the only one that survives the grammar.**

## The options

| option | rule | cost |
|---|---|---|
| **A · whitespace-delimited comment** *(recommended)* | `#` starts a comment **only when preceded by whitespace or at line start**. `https://x/a#b` keeps its fragment; `https://x/a  # note` still comments | one regex; matches how `.gitignore` and most line formats already behave |
| **B · comments only on their own line** | a line either is a comment or is a URL | simplest rule, but loses trailing annotation, which is how the file stays readable |
| **C · require escaping** (`\#`) | explicit | pushes the cost onto every consumer for a case they will not anticipate |

**A is recommended.** It preserves the trailing-comment affordance
[ADR-URL-LIST](../../docs/adr/0018_url-list.md) decision 3 exists for, and the
rule is one a reader can state.

## Definition of done

- [ ] Rule implemented in `read_urls`, whichever option Arpit's W-50 call
      implies (see Hazard).
- [ ] **Tests:** a URL with a fragment survives round-trip; two URLs differing
      only by fragment produce **two** records, not one; a trailing
      `  # comment` is still stripped; a bare `#` line is still ignored.
- [ ] [ADR-URL-LIST](../../docs/adr/0018_url-list.md) §Consequences: replace
      the known-defect note with a fixed-in reference, and amend decision 3 to
      state the new rule. **Same change** — Law zero.
- [ ] `CHANGELOG.md` under `[Unreleased] → Fixed`.
- [ ] This file archived to `archive/open/` and its OPEN-WORK row deleted,
      outcome recorded in [`../IMPLEMENTATION.md`](../IMPLEMENTATION.md).

## Hazard

**Do not fix this in isolation if [W-50](W-50-url-fetch-mechanism.md) is
live.** W-50's per-URL attribute grammar (`<url> fetch=cdp meta=plain`) rewrites
the same parser and has to answer the same question about where a comment
begins. Two sequential rewrites of one function, each with its own tests, is
how the two rules end up disagreeing. **If W-50 is decided, land this inside
it; if W-50 is rejected, land this alone.**

## Evidence

[`src/fux/ingest/urlsrc.py`](../../src/fux/ingest/urlsrc.py) `read_urls` —
read the line, then the docstring above it, which describes the intended
behaviour rather than this one.
