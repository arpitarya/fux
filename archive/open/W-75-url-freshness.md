# W-75 — the index has no way to learn that a URL changed

**Status:** OPEN — **eight forks, all Arpit's. Nothing is buildable until
forks 1, 3 and 5 are ruled.**
**Lane:** `arpit` for the forks; `agent` for Phase 0 and Phase 1 below, which
are unblocked
**Filed:** 2026-08-22 (Cowork), from Arpit's question about keeping documents
current
**Spec:** [`../proposals/url-freshness.md`](../proposals/url-freshness.md) —
the argument and all eight forks
**Forks split out:**
[`../compare/url-refresh-trigger.compare.md`](../compare/url-refresh-trigger.compare.md)
(fork 1) ·
[`../compare/url-fetch-concurrency.compare.md`](../compare/url-fetch-concurrency.compare.md)
(forks 5–6)
**Closes with:** **`ADR-FETCHER`** (the contract, if fork 3 is yes) ·
**`ADR-URL-INGEST`** (what an unchanged run reports) · **`ADR-MAINTENANCE`**
(if the hook fetches) · **`ADR-CONFIG`** (`max_parallel`, the validator gate) ·
**`ADR-DOTFUX`** (only if the token sidecar commits). **Not `ADR-URL-LIST`** —
its decision 11 closes the attribute set at two, and nothing here needs a
third.
**Model:** **Opus** for the forks and Phase 2 — fork 3 amends a contract that
has survived two callers unchanged, and fork 5 is a correctness argument about
thread safety whose failure mode is *wrong documents indexed*, not a crash.
**Sonnet** is enough for Phase 0.

## The claim

**Nothing in fux can learn that a URL changed.** A repo document changes and
`post-commit` re-indexes it. A URL changes and the index finds out when a
human next types `fux update` — and nothing anywhere reports how long ago
that was.

## Why it is smaller than it looks — and where it still bites

**A stale `url:` record costs recall, not correctness.** The refer plane
already re-fetches every cited URL and compares `fetched_sha` against
`indexed_sha`, so a changed document cannot be *mis-answered*
([`refer/freshness.py`](../../src/fux/refer/freshness.py)). It can only fail
to **surface**, because ranking runs on the terms the index recorded.

That is the correct frame and it is also the ceiling on how much this is
worth. It bites hardest exactly where the design point is: a large corporate
estate, where the tail nobody has queried yet is most of the corpus.

## The hard constraint everything is sized by

`fetch(url) -> str` returns markdown — **no headers, no status code.** Fux
structurally cannot issue a conditional GET, so every *"did it change?"* costs
a full fetch and a render. With `fetch=cdp` that is a browser render.
`fetch_all` is a strictly sequential loop. At 100k URLs both facts are
disqualifying on their own.

## Definition of done

**Phase 0 — the measurement that rules fork 3.** Run `fux update` twice
against a real corpus; count the fraction of fetched documents whose sanitized
sha was unchanged. **No new code.** File under
[`../regression/`](../regression/README.md). **≥ 80 % → fork 3 is yes;
≤ ~40 % → the contract stays at four functions and the item shrinks to
Phase 1 plus §7.** This is the proposal's graduation trigger and it gates the
expensive half.

**Phase 1 — reporting, and it is unblocked by every fork.** `fux doctor`
gains a URL section: how many `url:` records, how many validated in the last
run, how many never re-fetched since first ingest, how many failing. Plus the
`fail_streak` counter behind it. **The current failure is not that the index
is stale, it is that it is silently stale**, and this half fixes that alone.
**Report, never auto-delete** — [ADR-URL-INGEST](../../docs/adr/0008_url-ingest.md)
decision 4 forbids treating a failed fetch as a deletion, and this makes the
consequence of that rule visible instead of invisible.

**Phase 2 — the detector** (proposal §1). The refer plane records a `url:`
doc id in the dirty list when `fetched_sha != indexed_sha`; a narrowed refresh
consumes it. Both halves already exist —
[`maintain/dirty.py`](../../src/fux/maintain/dirty.py) and
`ingest.run(only_urls=…)` — so this is one call site and a filter.

**Phase 3 — the validator** (proposal §2), only if Phase 0 says yes.
`validate(url) -> str | None`, optional, `None` meaning *I cannot tell*.
`http.py` must ship an implementation or the abstraction is unproven.

**Phase 4 — concurrency and the cap** (proposal §4, fork 5).

## Hazards

- **`dirty.py` says the list is *"advisory, never authoritative"*** — the
  sentence that keeps L3 true. A URL refresh driven by it **is**
  authoritative for the URLs it names. The defence is in proposal §1 and must
  be written into the record rather than assumed: the `url:` half of the index
  is already a mosaic of different moments. ⚠ **Do not confuse this with
  *"just index the delta"***, which was ruled *not* the fix for R5 — that was
  an offline walk that is already cheap.
- **A changed validator token must never mean a changed record.** Token
  changed → fetch → **still** compare the sanitized sha. Otherwise a chatty
  ETag churns shards and byte-determinism is gone. If exactly one sentence
  from this item reaches the implementer, it is this one.
- **`cdp.py` is not thread-safe** — `connect()` sets a module-global
  `_session` holding one WebSocket that `fetch()` reuses. A blind thread pool
  interleaves CDP frames on one socket and produces **plausible documents
  attributed to the wrong URLs**: it passes every determinism check and is
  found by a human reading an answer.
- **A hook that fetches is new.** Even scoped to the commit that edits
  `.fux/sources/urls`, it is the first time an installed hook touches the
  network, and the L4 opt-in (`fux hooks --install`) is a one-time act whose
  consequence is invisible at the moment of consent. It needs its own config
  gate, separate from the indexing hooks.
- **Never store a validator token in plaintext.** Fux only ever tests tokens
  for equality, so `sha256(token)` compares identically and leaks nothing —
  which is what makes a committed sidecar safe under L5 for `meta=hashed`
  sources.
- **Runtime state does not survive a clone.** A CI runner therefore starts
  with no tokens and does the full sweep the validator exists to prevent.
  Safe direction (over-fetch, never under-report), but it is exactly the
  deployment that most wants the mechanism.

## Not in scope

- **Any age bound on a record.** [`record-freshness`](../compare/record-freshness.compare.md)
  verdict D settled it and nothing here reopens it. §5's state file is
  *runtime*, which that verdict does not reach.
- **A per-line `refresh=` or `validate=` attribute.** ADR-URL-LIST decision
  11 closes the attribute set at two and nothing here needs a third.
- **An adaptive per-URL crawl schedule.** Phase 2's usage weighting is
  strictly better evidence than an estimated change rate, and the literature
  does not straightforwardly support proportional-to-change-rate over uniform.
- **A push/webhook receiver.** That is consumer code calling `fux update`; it
  adds no fux surface and needs no item. Worth documenting, not building.
