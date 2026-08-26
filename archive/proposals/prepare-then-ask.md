---
type: Proposal
title: Prepare, then ask — a warm corpus before the first question, and an answer that knows nothing changed
description: Arpit's end-to-end flow, checked against the CLI. Two gaps — ingest warms the index but not the refer plane, and no answer is ever memoized — and two flags rather than two verbs. Nothing researched, nothing measured.
status: proposed
timestamp: 2026-08-26T00:00:00Z
---

# Prepare, then ask

**Arpit, 2026-08-26**, describing the flow he expects:

> *"Before getting the answer, I should have ingested all the documents as well
> as the URLs. The URLs should have already been cached, and whatever needs to
> be extracted from those URLs should be already extracted. Is there a command
> for it? … Now when you ask a question … for the URLs, it should again fetch
> those documents which are relevant and check if anything has changed. If
> nothing has changed, then give the same old answer. If things have changed,
> then maybe reframe the answer."*

⚠ **This document is a capture, not a design.** It records the flow, what the
code does today, and the two gaps between them. **No research has been done and
no number has been measured** — that pass is deliberately deferred. Every
mechanism below is a sketch and every cost estimate in it is absent on purpose.

---

## §0 — The flow, mapped onto what exists

| Arpit's step | today |
|---|---|
| record + ingest a directory, a document or a URL | **`fux add <entry>`** — records the line, ingests, and fetches that one URL |
| re-read everything already listed, re-fetching URLs | **`fux update`** — subsumed the retired `ingest --refresh-urls` |
| re-index offline only | **`fux ingest`** — never imports a fetcher (L4) |
| ask, from the index alone | **`fux ask`** / **`fux find`** |
| ask, fetching the cited sources and re-scoring | **`fux answer`** — the refer plane |
| *"check if anything has changed"* | **shipped** — the refer plane compares `fetched_sha` against `indexed_sha` and returns `current` / `stale` / `unverified` / `cached` |
| *"if nothing has changed, give the same old answer"* | **does not exist** |

**So most of the flow is already a command.** The answer to *"is there a command
for it?"* is **`fux update`** — with two things it does not do.

---

## §1 — Gap 1: ingest warms the index, not the answer path

**`fux update` fetches URLs to build index *statistics*.** Terms, postings,
document meta — the things ranking needs.

**The refer plane fetches again, into a different store, at answer time.** The
TTL fetch cache ([`refer/fetchcache.py`](../../src/fux/refer/fetchcache.py))
and the passage chunks are populated by `fux answer`, never by ingest.

**The consequence is the one Arpit's flow is trying to avoid:** after
*"everything is ingested"*, the first question still pays a **full render per
cited URL**. Nothing in the corpus is warm in the sense he means.

**And the separation is deliberate, not an oversight.** The two stores are
provably distinct — ARC is keyed `(loc, sha)` so a hit is byte-identical or it
is not a hit; the TTL cache is served *before* a sha is confirmed, which is what
a TTL is. **Any warming proposal has to say which of the two it fills**, and
filling the second one has a consequence — see §4.

---

## §2 — Gap 2: there is no answer memo

**`fux answer` re-fetches and re-scores on every call.** The verdict reports
what happened to the source; **the answer is recomputed either way.**

So *"nothing changed → the same old answer"* is not a behaviour fux has. It is
not disabled, not configurable, not slow — **it is absent**.

⚠ **Note what the verdict already gives us for free.** The comparison Arpit
wants as the memo's validity check — *did the cited bytes change?* — is
**already performed on every answer**. What is missing is only the memory of
what was said last time.

---

## §3 — The proposed shape: two flags, not two verbs

**`fux update --warm`** — after re-ingesting, prime the refer plane for every
listed URL, so the first question is not the one that pays. This is the single
*"everything is ready"* command the flow asks for.

**`fux answer --memo`** — cache the produced answer keyed on
`(query, tune hash, the set of cited (loc, sha))`. On a re-ask: fetch, compare
shas → **all match, replay the stored answer** and report `current`; **any
differ, recompute** and report `changed`.

**Why flags and not verbs, and this is the load-bearing part:**

- **`fux` has exactly two named networked paths** — `fux add <URL>` and
  `fux update` ([ADR-CLI](../../docs/adr/0002_cli-surface.md) decision 1e).
  A third verb that opens a socket is **a new L4 fence**, and L4's whole value
  is that the fenced set is small enough to name in one breath.
- **`--warm` rides a path that is already networked.** It costs no new fence.
- **`--memo` opens no socket at all** — it fetches exactly what `fux answer`
  already fetches, and only decides whether to recompute afterwards.
- ADR-CLI veto 1 forbids `fux <verb> <subverb>`, so `fux cache warm` is not
  available even if a verb were wanted.

**Precedent for `--warm` being a flag on the existing verb, not a new one:**
`fux add` already ends in `ingest.run`, deliberately, *"because a second write
path is how L3's byte-identical guarantee breaks"*
([`sources.py`](../../src/fux/sources.py)). The same argument applies to a
second fetch path.

---

## §4 — What is NOT decided (the research pass)

**These are the questions, unanswered. Nothing below is a recommendation.**

1. **Which store does `--warm` fill?** The TTL cache, ARC, the chunk cache, or
   more than one. Each has a different soundness story and they are not
   interchangeable.

2. ⚠ **The interaction between the two proposals is the sharp edge.** If
   `--warm` fills the **TTL** cache, then the next `fux answer` may be served
   from a TTL hit — **which is not a sha confirmation**. A memo validated by a
   TTL hit would replay an answer on bytes nobody confirmed, and it would look
   exactly like a confirmed one. **A memo must never be validated by anything
   but a sha comparison**, and saying that is easy while enforcing it is a test
   somebody has to write.

3. **What does the memo key actually have to contain?** `(query, tune hash,
   cited (loc, sha))` is a guess. A missed input silently returns a stale answer
   under a `current` label, which is the worst failure available here.

4. **Is a memo a lie about freshness?** The `cached` verdict exists precisely
   because ADR-REFER refuses to collapse *"we did not look"* into *"we looked
   and it was fine"*. **A replayed answer is a fifth epistemic position** and
   probably needs to say so rather than borrowing `current`.

5. **What does *"reframe the answer"* mean, concretely?** Today a changed source
   produces a recomputed answer. Arpit's *"maybe reframe"* may mean something
   more — a diff, a *"this changed since you last asked"* line — and that is a
   separate feature wearing this one's clothes.

6. **What does a `--warm` sweep cost, and does it pay?** Unmeasured. **The
   honest version of this proposal is that nobody knows whether the cold first
   question is a real problem on a real corpus.**

7. **Where does the memo live?** It cannot be committed — it is derived,
   per-machine and wall-clock-adjacent, so it belongs with the gitignored
   artifacts (`.fux/runtime/`), never in `.fux/index/`. Same treatment the TTL
   cache and `stamp.json` already get.

8. **Does the memo have to survive a re-ingest?** An index write can change what
   ranks without changing any cited sha. **The key as sketched does not notice
   that**, which is either a bug in the sketch or an argument for including the
   index root hash.

---

## §5 — Where this sits against what is already open

**Both flags land inside [W-75](../open/W-75-url-freshness.md)**, and one of
them is blocked by it.

- **`--warm` is startable.** It re-fetches what is already listed and warms a
  cache; it decides nothing W-75 has to rule first.
- ⚠ **`--memo` is not.** `fetch(url) -> str` returns markdown with **no
  headers** ([ADR-FETCHER](../../docs/adr/0019_fetcher.md)), so fux structurally
  cannot issue a conditional GET (RFC 9110 §13) and **every *"did it change?"*
  costs a full render**. Whether that cost is acceptable is one of W-75's own
  unruled forks — see [url-refresh-trigger](../compare/url-refresh-trigger.compare.md).
- ⚠ **`cdp.py` is not thread-safe** (`global _session`, one WebSocket). A
  `--warm` sweep that reaches for parallelism inherits W-75's worst hazard:
  *plausible documents attributed to the wrong URLs*, which passes every
  determinism check and is caught only by a human reading an answer. See
  [url-fetch-concurrency](../compare/url-fetch-concurrency.compare.md).

**Neither flag needs a recorded ingest time**, so the `max_age_seconds` question
that [`refer/freshness.py`](../../src/fux/refer/freshness.py) documents and
refuses is **untouched by this** — the memo is validated by sha, not by age.

---

## §6 — Graduation trigger

**This proposal splits, and the two halves graduate separately.**

- **`--warm` graduates** when a measured first-question latency on a
  URL-bearing corpus shows the cold refer plane is the dominant cost — **or**
  when W-75's trigger fork is ruled, whichever comes first, since that ruling
  decides what a warm sweep is allowed to do.
- **`--memo` graduates** only after W-75's trigger fork is ruled **and** open
  question 2 has a written answer — a memo that can be validated by a TTL hit
  must not be built.

**If neither fires, this stays parked**, which is the correct outcome for an
idea with no measurement behind it.

---

## §7 — References

- **The code this was read against**, 2026-08-26:
  [`cli.py`](../../src/fux/cli.py) ·
  [`sources.py`](../../src/fux/sources.py) ·
  [`ingest/urlsrc.py`](../../src/fux/ingest/urlsrc.py) ·
  [`refer/fetchcache.py`](../../src/fux/refer/fetchcache.py) ·
  [`refer/freshness.py`](../../src/fux/refer/freshness.py)
- **The records it must not contradict:**
  [ADR-CLI](../../docs/adr/0002_cli-surface.md) (the verb surface, the two
  networked paths) ·
  [ADR-REFER](../../docs/adr/0030_refer-plane.md) (the three-state guarantee and
  the fourth verdict) ·
  [ADR-FETCHER](../../docs/adr/0019_fetcher.md) (the consumer-fetcher contract) ·
  [ADR-URL-INGEST](../../docs/adr/0008_url-ingest.md)
- **The open item it belongs to:** [W-75](../open/W-75-url-freshness.md) and its
  proposal, [URL freshness](url-freshness.md).
- **Conditional requests**, for the header problem: RFC 9110 §13
  (`If-None-Match` / `If-Modified-Since`) —
  <https://www.rfc-editor.org/rfc/rfc9110#section-13>.
- **The "record and fetch" precedent** already surveyed for `fux add`:
  `uv add` locks and syncs by default; `helm repo add` records *and* fetches.
