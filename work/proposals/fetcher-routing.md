---
type: Proposal
title: "The fetcher pipe — a URL line declares its fetcher AND its decoder"
description: "Arpit's ruling 2026-09-18: a fetcher emits bytes in a format a decoder reads (csv, docx, drawio, html, json, xml, xlsx, pdf …), the decoder turns them into Markdown, fux ingests the Markdown. The URL line states both halves — `fetch=<stem> decoder=<stem>` — written once at `fux add` and never re-derived. Replaces the host-routing draft of the same date. Breaking: a line without `decoder=` does not load. Graduated into W-199."
status: graduated
timestamp: 2026-09-18T00:00:00Z
filed: 2026-09-18
---

**Graduated 2026-09-18 → [W-199](../open/W-199-fetcher-routing.md)** (Arpit).
This file stays the pattern the item points at.

# The fetcher pipe

## §1 — For humans

> **Arpit, 2026-09-18:** *"Whenever we add a URL, after that, we have to define
> what kind of fetch it is, what kind of decoder we want to use. And that is the
> one that gets saved in the URLs file."*
>
> *"The fetchers … should [emit] CSV, docx, drawio, html, json or xml, xlsx or
> any of those kind of files which can be read by [a] decoder, and then [the]
> decoder can go ahead and create a markdown file which can be ingested by fux.
> That is the pattern."*

Three stages, three owners, one line that names the first two:

    URL line ──fetch=cdp──▶ .fux/fetchers/cdp.py ──bytes──▶ .fux/decoders/xlsx.py ──Markdown──▶ fux ingest
               decoder=xlsx                                  (chosen by the LINE,
                                                              never by the header)

For a **file**, the extension picks the decoder. For a **URL** there is no
trustworthy extension — `?download=1`, `/export`, a `Content-Type` of
`application/octet-stream` — so today fux guesses from the header, then the
URL, then falls back to prose, on **every** ingest. The ruling replaces the
guess with a **declaration**: the line says `decoder=xlsx`, and that is the
decoder, run after run. It is the decoder plane's *"the file binds, the module
verifies"* applied to URLs, with the line as the file.

**Nothing new is detected.** `fux add` already fetches once (the fenced path);
that one fetch is where the type is *observed*, written to the line, and from
then on it is *declared*. A later ingest never reads the header for routing.

## §2 — The pattern

### The contract, unchanged

`fetch(url) -> tuple[bytes, str]` stays. A fetcher retrieves; it never converts.
The `str` it returns is the declared `Content-Type`, and after this change it is
**informational only at ingest** — used by `fux add` to propose a decoder, by
refusal rules that match on it, and by nothing else on the routing path.

### The line states both halves

    https://contoso.sharepoint.com/hr/policy.xlsx?download=1 fetch=cdp decoder=xlsx keep=true ttl=24h enrich=false archived=false update=auto

- `fetch=<stem>` — unchanged: `<fetchers dir>/<stem>.py`, default the stem of
  `[sources.url] fetcher`, written on every generated line (SR-URL-LIST
  decision 12 stands as is).
- `decoder=<stem>` — **new, and required.** A decoder module name — a built-in
  from `BUILTIN_MODULES` or a file in `.fux/decoders/` — exactly the vocabulary
  `.fux/formats.toml [decoders]` already uses. **No default.** A line without
  it fails to load with a named error.
- `decoder=prose` — the one reserved word, for a URL whose bytes are already
  text (`text/markdown`, `text/plain`). It names the `_PROSE` path that exists
  today and no module; it is reserved so no consumer file can shadow it.

### How `fux add` fills the two attributes

1. `--fetch <stem>` given → that; else the stem of `[sources.url] fetcher`.
   `--cdp` / `--http` stay as aliases of `--fetch cdp` / `--fetch http`.
2. `--decoder <stem>` given → that, verified to exist (a name is a stem: built-in
   or `.fux/decoders/<stem>.py`; anything else is the `_bind` error shape).
3. Neither → `fux add` performs its fenced fetch, maps the response's
   `Content-Type` through `_TYPE_EXT` to an extension, asks the decoder registry
   which module claims it, and writes **that stem**. `text/markdown` and
   `text/plain` write `prose`.
4. **Nothing maps** (unknown type, `application/octet-stream`, a type no decoder
   claims) → **`fux add` refuses**, prints the type it saw and the decoder stems
   on disk, and asks for `--decoder`. It never guesses and never writes a line
   it cannot ingest. This is the *"define what kind"* moment, forced only when
   the observation is not enough.

### What ingest does with them

`_decode_fetched(raw, entry.decoder, url, root)` — the **declared** decoder,
looked up by name via a new `decode.decoder_named(stem, root)` (built-in unless
a consumer file of that stem replaces it — the registry's existing rule).
`_TYPE_EXT` and the URL-extension fallback leave the ingest path entirely; they
are `fux add`'s tools now. `prose` short-circuits to the `_PROSE` branch.

The **refer plane** takes the same route: `refer/source.py` already imports
`_decode_fetched` rather than reimplementing it, and it now passes the entry's
declared decoder so ask-time re-decoding is byte-identical to ingest — the false-
staleness hazard its docstring names, closed structurally.

### What gets stronger for free

- **The magic-bytes floor** (SR-REFUSALS) checked the response's *claimed*
  type against its first bytes. Now it checks the **declared decoder's** format
  against the bytes: a line that says `decoder=xlsx` whose response does not
  start with `PK\x03\x04` is a refusal with a reason, whatever the header said.
  A login page can no longer sneak in under a wrong `Content-Type`.
- **The acquired blob's extension** comes from the declared decoder, not the
  header, so `.fux/acquired/` names files by what they *are*.
- **`fux doctor`** gains one row: every `decoder=` on every line resolves to a
  module; the check imports built-ins only, never a consumer decoder with a
  missing dependency — it reports the stem is *absent*, and leaves the
  dependency error to ingest, where `_load_consumer` already names it.

### Precedence, for the record

Line `decoder=` is the only thing consulted at ingest for a URL. The
`[decoders]` binding table and a module's `EXTENSIONS` decide what a *file*
gets and what `fux add` *proposes*; they never re-route a URL line. Most
specific wins, and the line is the most specific thing there is.

### Breaking, by ruling

> **Arpit, 2026-09-18, on migration:** *"Nothing needs to be done. It is a
> breaking change. That's all."*

A `.fux/sources/urls` written before this change carries no `decoder=`. It
fails to load with an error naming the line and the fix (`fux add <url>` again,
or write `decoder=<stem>` by hand). No accept-and-ignore, no lenient default,
no rewrite — the W-177 / W-194 precedent. SR-URL-LIST decision 13 (*the reader
is lenient*) gains its one exemption and says why.

## §3 — Edge cases the builder must handle

1. **`decoder=prose` is reserved.** A consumer file `.fux/decoders/prose.py` is a
   hard error at registry build, naming the reservation.
2. **`decoder=` names nothing.** Hard error at resolve (the `_bind` message
   shape: *"no decoder module named X — built-ins are …, `.fux/decoders/` has
   …"*); `fux doctor` reports it first.
3. **`decoder=` names a consumer module whose dependency is missing.** Ingest
   fails loudly (SR-DECODE decision 7, unchanged); doctor does not import it.
4. **Declared decoder disagrees with the bytes.** Magic floor refuses (xlsx,
   docx, pptx → `PK\x03\x04`; pdf → `%PDF-`); for formats with no magic
   (html, json, csv, xml) the decoder runs and its own *"nothing readable"*
   path records the skip. Never silently re-routed.
5. **Declared decoder disagrees with the header.** The header loses, silently.
   The line is the human's word; the header is the server's. Stated, so nobody
   "fixes" it.
6. **`fux add` on a URL that refuses (login page).** Refusal fires before the
   decoder proposal; `fux add` reports the refusal and writes no line. It does
   not write `decoder=html` for a sign-in shell.
7. **`fux add --no-fetch`** cannot observe a type → `--decoder` is **required**
   with it; refused otherwise, naming the reason.
8. **`fux add --decoder xlsx` when the add-fetch returns HTML.** The line is
   written as asked (declared wins), then the same ingest refuses it via the
   magic floor and says so — the human sees the disagreement on the first run.
9. **A decoder that `WANTS_PATH`.** Unchanged — `Decoder.__call__` writes the
   temp file with the decoder's own first extension as suffix.
10. **Consumer decoder overrides a built-in of the same stem.** `decoder=html`
    resolves to `.fux/decoders/html.py` when present — the registry's existing
    replace-wholesale rule, and the reason the vocabulary is *stems*.
11. **`update=never` lines** still must carry `decoder=` — the grammar is
    uniform; nothing is fetched, nothing is decoded, the attribute is simply
    there for the day `update=auto` returns.
12. **Round-trip.** Both attributes render on every generated line (decision 12
    as written); a pinned line reads back byte-identical.
13. **Duplicate URL, different `decoder=`.** The list is deduped by URL; today
    the entry with more declared attributes wins (`sourcelist.py:568`). Two
    lines with the same URL and *different* `decoder=` is a **hard error** —
    the two would ingest different bytes for one document id.
14. **`ROUTES`, host tables, add-time routing.** Not built. Dropped by this
    ruling; the earlier draft of this file is in git history only.
15. **The bare-`str` fetcher return** (SR-FETCHER decision 2's transition ramp,
    "already Markdown"). It contradicts *"a fetcher emits a format a decoder
    reads"* — see W-199 §Open question. **Not removed by this item unless
    Arpit says so**; the record says the ramp's cost was never measured.
16. **Node twin.** None — `node/src/refer/source.mjs` states it has no fetcher
    seam. Verify by grep.

## References

- [SR-DECODE](../../records/0139_decode.md) — the registry, the stem vocabulary,
  decision 7 (loud failure on a missing dependency).
- [SR-FETCHER](../../records/0117_fetcher.md) — decisions 1, 2, 4, 5, 5a (the
  content-type resolution this ruling retires at ingest).
- [SR-URL-LIST](../../records/0116_url-list.md) — decisions 12, 13.
- [SR-URL-INGEST](../../records/0107_url-ingest.md) — the ingest path.
- [SR-REFUSALS](../../records/0146_refusals.md) — the magic floor.
- [SR-ACQUIRED](../../records/0145_acquired-plane.md) — blob naming.
- [SR-CLI](../../records/0101_cli-surface.md) — the `add` verb's flags.
