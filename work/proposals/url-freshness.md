---
type: Proposal
title: URL freshness — the half of the corpus git cannot tell you about
description: Docs in the repo re-index on commit; a URL has no commit. Proposes a query-driven detector, an optional validator in the fetcher contract, a clock (hook / daemon / CI), a bounded parallel refresh, and the reporting that should ship whatever else does not.
status: proposed
timestamp: 2026-08-22T00:00:00Z
---

# URL freshness — the half of the corpus git cannot tell you about

**Arpit's question, 2026-08-22:** *"How do we keep the documents up to date —
specifically the URLs, not what's in the repository? Repo documents can be
re-indexed on every commit. But what about the URLs?"*

The observation is exact, and the asymmetry it names is the whole problem.
**A file change is an event. A URL change is not.** Everything below follows
from that one sentence.

---

## §0 — Two reframes, before any mechanism

**Reframe 1: two different freshness questions, and one is already shipped.**

| question | status |
|---|---|
| *Is the document I am citing still true?* | **solved.** The refer plane fetches the cited URL and compares `fetched_sha` against `indexed_sha`, returning `current` / `stale` / `unverified` / `cached` ([`refer/freshness.py`](../../src/fux/refer/freshness.py)) |
| *Does the index still rank this URL correctly?* | **unsolved. This proposal.** |

The consequence is the one that should govern how hard this is pushed: **a
stale `url:` record costs recall, not correctness.** A document whose content
changed cannot be mis-answered — refer re-fetches it and re-scores — but it
can **fail to surface at all**, because ranking runs on the terms the index
recorded. Recall is a weaker good than correctness, and this work should be
priced as buying the weaker one.

[`record-freshness`](../compare/record-freshness.compare.md) already
established why: content verification *is* an `ETag`, and it is strictly more
precise than any age bound. Nothing here re-opens that.

**Reframe 2: a *detector* and a *clock* are different roles.** Most of the
apparent options collapse once they are separated. A detector answers *which
URLs are worth fetching*; a clock answers *when anyone looks*. §1 is a
detector. §2 is a cheaper detector. §3 is the clock. They compose; they do
not compete.

---

## §1 — The detector that is nearly free: let queries mark dirty

The refer plane **already** fetches cited URLs and already computes
`fetched_sha`. When it differs from `indexed_sha` it renders `stale` to the
caller and then throws the knowledge away.

**Proposal:** record that doc id in the dirty list.

Both halves exist. [`maintain/dirty.py`](../../src/fux/maintain/dirty.py) is
the append-only, union-not-replacement, gitignored list `post-commit` already
writes; [`ingest/run.py`](../../src/fux/ingest/run.py)'s `run(only_urls=…)`
is already the parameter that narrows a networked run to a named subset —
built for `fux add <URL>` in W-63, and it does not care why the subset is
small. The new code is one call site in `refer/` and a filter that maps
`url:` doc ids back to URLs.

**What makes this better than any scheduler:** prioritisation comes out
**usage-weighted, for free**. Documents people actually retrieve get verified
constantly because they are cited; documents nobody retrieves drift, and
staleness in a document nobody retrieves is staleness nobody pays for. That
is the frequency-weighted freshness objective the crawl literature optimises
toward, except the weight is observed rather than estimated.

**Its limit is exact and disqualifies it as a complete answer:** it only ever
sees documents someone retrieved. At 100k URLs the corpus is mostly tail.
**§1 covers the head; §3 covers the tail.**

**The crux this carries.** `dirty.py`'s docstring says the list is
*"advisory, never authoritative"* — the sentence that keeps L3 true, because
`fux ingest` re-walks the whole corpus regardless of what the list says. A
URL refresh driven by that list **is** authoritative for the URLs it names,
because not fetching the rest is the entire point. The defence has to be
written down rather than assumed:

> The `url:` half of the index is **already** a mosaic of different moments —
> every record holds whatever its last fetch produced, and no two were
> necessarily fetched together. A partial refresh changes the *spread* of
> those moments, not the kind of object the index is. L3 says *same sources →
> same bytes*, and a URL is not the same source twice.

⚠ **This is not "just index the delta"**, which was ruled *not* the fix for
R5 on the git path. That argument was about an offline filesystem walk that
is already cheap; this is a networked path that is not cheap, and the
economics that made delta-indexing the wrong trade there are the economics
that make it the right one here.

---

## §2 — The cheaper detector: an optional validator in the fetcher contract

### The constraint

`fetch(url) -> str` returns markdown. No headers, no status code. **Fux
structurally cannot issue a conditional GET** — no `If-None-Match`, no `304`.
Every "did it change?" costs a full fetch *and* a render; with `fetch=cdp`,
a browser render. That is the cost driver behind every option in §3.

### The shape

```python
def validate(url: str) -> str | None:
    """Cheap answer to 'might this have changed?'
    Return an opaque token, or None for 'I cannot tell'."""
```

Three properties, each load-bearing:

- **The fetcher reports; fux compares.** The fetcher hands back whatever its
  world calls a validator — an `ETag`, a `Last-Modified`, a Confluence
  `version.number`, a git blob sha — and **fux** diffs it against the stored
  one. Transport stays consumer-side; policy stays engine-side. That is the
  same line [ADR-FETCHER](../../docs/adr/0019_fetcher.md) decision 8 draws
  around `[sources.url.config]`.
- **`None` means "I do not know", not "unchanged".** It degrades to a full
  fetch. A fetcher with no `validate` at all behaves identically, so **every
  existing fetcher keeps working with zero migration.**
- **The token is opaque.** Fux never parses it. That is what stops `validate`
  from smuggling HTTP semantics into an engine that has none.

### Batching, without a batch signature

Sequential per-URL HEADs are still N round trips. **`connect()` already
provides the batch bracket.** A Confluence fetcher runs one
`cql=lastModified > …` sweep inside `connect()`, caches the result in a module
dict, and answers `validate()` from memory. One query covers thousands of
pages, with **zero contract complexity**, using a seam that already exists.

| path at 100k URLs | cost |
|---|---|
| today, `fetch=http`, sequential | 100k GETs + HTML→markdown — **hours** |
| today, `fetch=cdp`, sequential | 100k browser renders — **not viable** |
| per-URL `validate` + fetch the changed ~2 % | **~90 min** |
| batch-in-`connect()` + fetch the changed ~2 % | **minutes** |
| any of the above × §4's parallelism | ÷ N |

### The invariant that keeps L3 intact

**A changed token never means a changed record.** ETags flip on cosmetic
bytes; `Last-Modified` flips on a touch. So:

- token **unchanged** → skip the fetch. *This is the only thing `validate` is
  permitted to do.*
- token **changed** → fetch, then **still** compare the sanitized sha before
  anything about the record moves.

`ver` still increments only on a real change of the sanitized sha, through
the shared `sanitize` that [ADR-REFER](../../docs/adr/0030_refer-plane.md)
decision 3 already forced. **Therefore `validate` can only ever save work; it
can never cause a shard to churn.** A chatty ETag costs a wasted fetch, not a
wrong index. Degradation is correct too: a server emitting a fresh token every
request always reads "changed", which is exactly today's behaviour.

### The honest case against

ADR-FETCHER's own Consequences say: *"The contract now has a second caller,
and it did not change. That is the evidence for decision 1's shape."* Four
functions have survived two callers untouched. A fifth must beat three
objections:

1. **"§1 already covers this."** Partly — and this is the real crux. §1
   covers what was retrieved; `validate` covers the tail. Complements, not
   alternatives. **If a consumer's tail does not matter, they do not need
   §2.**
2. **"An optional function nobody implements is dead weight."** Real, and it
   has a clean test: **the shipped `http.py` must implement it.** A
   conditional GET is a handful of stdlib lines on top of the
   `urllib.request.Request` already in the template. If the default fetcher
   cannot implement it cleanly, that is evidence the abstraction is wrong.
3. **Contract creep** — today `validate`, tomorrow `list_children`,
   `paginate`, `authenticate`. The fence, and it should be written into the
   record: **`validate` is `fetch` at lower resolution, not a new
   capability.** Every other candidate fifth function would be new
   capability.

### Two small rulings it needs

- **`fux add <URL>` never validates.** A human just asked for that URL; fetch
  it. Validation belongs to `fux update` only — consistent with W-63
  decision 1.
- **A validator skip is not a fetch skip.** Today "skipped" means *failed*.
  98,000 unchanged documents must not print as skips:
  `ingested 100000 docs (2000 changed, 98000 unchanged), 3 skipped`.

---

## §3 — The clock → [`url-refresh-trigger`](../compare/url-refresh-trigger.compare.md)

A separate fork with its own document, because it has five real options and
turns on a law. In brief, and the compare doc is authoritative:

- **manual (today)** · **the `post-commit` hook** · **a local daemon** ·
  **a CI schedule opening a PR** · **query-driven (§1)**
- **The law in the way is L4** — *network only inside explicit, fenced,
  opt-in paths* — and the options differ mostly in **the quality of the
  opt-in**, which is the axis the matrix weights highest.
- **Proposed:** §1 unconditionally; the hook **only** for the commit that
  edits `.fux/sources/urls` (a real change event, bounded by the diff) and
  never as an opportunistic sweep on every commit (which makes every
  developer's `git commit` issue third-party network requests); and a daemon
  **or** CI as the deployment's clock — **CI where CI can reach the sources,
  a daemon where it cannot.** CLAUDE.md's litmus makes air-gapped estates a
  design input, and there CI does not exist.
- ⚠ [`maintenance-trigger`](../compare/maintenance-trigger.compare.md)
  already ruled this fork **for files** and rejected both CI and a daemon.
  **Its reasoning does not transfer**, and the compare doc says exactly why:
  for files the event already existed and the only question was who listens;
  for URLs there is no event, so the question is what supplies a clock at all.

---

## §4 — The cap, and the parallelism underneath it → [`url-fetch-concurrency`](../compare/url-fetch-concurrency.compare.md)

Arpit's request — *a limit on the number of URLs refreshed in parallel* —
**presumes a parallelism that does not exist.** `fetch_all` is a strictly
sequential loop. So the cap and the concurrency are one item, and the cap is
the easy half.

The hard half, checked rather than assumed: **the shipped `cdp.py` is not
thread-safe** (`connect()` sets a module-global `_session` holding one
WebSocket; `fetch()` reuses it), while **the shipped `http.py` is**. A blanket
thread pool would be correct for the fetcher most consumers use and would
silently corrupt the one the enterprise design point exists to serve — and it
would present as *wrong documents indexed*, not as a crash.

- **Proposed:** a fetcher module may declare `MAX_PARALLEL = n`; absent the
  declaration it is `1`. Fux uses `min(declared, configured)`. This is
  ADR-FETCHER decision 5's **declared, never detected** applied to a second
  property.
- **The finding that makes it cheap:** sequential fetching is not what makes
  the index deterministic — **the sort is.** `fetch_all` ends
  `fetched.sort(...)` / `skipped.sort(...)`, so completion order never
  reaches the committed bytes.
- **Two knobs, two kinds of refusal**, per Arpit's standing rule: the
  module's declaration is **capability** — exceeding it is a correctness
  violation, so it clamps down loudly; `[sources.url] max_parallel` is
  **policy** — a large value is merely rude, so it **warns with the number
  and is never clamped**; `< 1` is broken and refuses.
- **Proposed default `4`**, flagged as judgement rather than measurement.
  **Live sub-fork: global cap or per-host?** The politeness constraint in the
  literature is per-host; the common case at the design point is one wiki.
  Proposed: ship global, promote on an observed 429.

---

## §5 — Where the validator token lives

**Not in the record.** [`record-freshness`](../compare/record-freshness.compare.md)
verdict D settled that: a temporal or per-fetch field inside a shard means
write-if-different rewrites **every shard on every run**, and `git status`
clean after an unchanged re-ingest is the guarantee ADR-INGEST rests on.

**That verdict is about *records*. It says nothing about *runtime*.** So:

- **Phase 1 — runtime.** `.fux/runtime/url-state.json`:
  `loc → {token, validated_at, changed_at, fail_streak}`. Gitignored,
  derived, already outside the byte-identity assertion — the same treatment
  `stamp.json` and the fetch cache get. **Costs the determinism law nothing.**
- **The tension it creates:** runtime does not survive a clone, so a CI
  runner (§3, option D) starts every run with no tokens and does the full
  sweep `validate` exists to prevent. Conservative in the safe direction — it
  over-fetches, it never under-reports — but it does blunt the mechanism in
  the deployment that most wants it.
- **Phase 2 — the committed sidecar, if the numbers justify it.**
  `.fux/sources/urls.state`, beside the list it describes. Two arguments it
  needs, both available:
  - **Churn:** it changes only when a URL's token changes, **not on every
    ingest**. Categorically different from the per-record timestamp verdict D
    killed.
  - **Determinism:** the token is network-derived and not reproducible —
    **but neither is the `sha` field it accompanies.** The sidecar is no less
    deterministic than the record it describes, and the `url:` half of the
    index is already network-derived throughout.
  - **It does not violate "the list is intent, not state"**
    ([ADR-URL-LIST](../../docs/adr/0018_url-list.md) decision 6). Keeping
    state in a *separate* file is that decision honoured, not broken.

**L5 disappears with one move: store `sha256(token)`, never the token.** Fux
only ever tests tokens for **equality** — it never needs the plaintext. A
hash compares identically and leaks no `Last-Modified` timestamp or version
number for an access-controlled page. Free, complete, and it makes the
sidecar safe to commit even for `meta=hashed` sources, which is the default
L5 mandates for non-git sources.

---

## §6 — The gap none of the above closes: URLs that die

[ADR-URL-INGEST](../../docs/adr/0008_url-ingest.md) decision 4: *a failed
fetch keeps the prior record*, reported as a skip, because a flaky network
must never present as a deletion. **Correct — and it means a permanently dead
URL lives in the index forever** until a human deletes its line.
[`doctor.py`](../../src/fux/doctor.py) has **no URL health check at all**;
its checks are the background runner, the Python version, the repo root, the
layout and the accelerator.

**Proposed:** the `fail_streak` counter in §5's state file, plus a
`fux doctor` line — *"12 URLs have failed 5 consecutive runs"*, naming them.
**Report, never auto-delete.** Auto-deletion on failure is precisely what
decision 4 forbids, and the counter does not weaken it — it makes the
consequence of the rule visible instead of silent.

---

## §7 — The half that should ship whatever else does not

If Arpit rules "nothing automatic", the largest part of the current failure is
still recoverable for near-zero cost, because **the failure is not that the
index is stale — it is that it is *silently* stale.**

- `fux doctor`: how many `url:` records exist, how many were validated in the
  last run, how many have never been re-fetched since first ingest, how many
  are failing.
- `fux ask`: a one-line declaration in the shape ADR-MAINTENANCE decision 1b
  already established for the pending re-index count.

**This is separable, cheaper than everything above, and blocked on none of
the forks.** It is the recommended first landing.

---

## §8 — The forks, all Arpit's

1. **Which clock?** → [`url-refresh-trigger`](../compare/url-refresh-trigger.compare.md).
   Proposed: §1 always; hook narrowly; daemon **or** CI by deployment.
2. **Does the hook fetch at all?** Even scoped to *the commit that edits the
   URL list*, this is the first time an installed hook touches the network.
   Proposed: yes, behind a config gate **separate** from the gate that
   installs indexing hooks.
3. **Amend the four-function contract?** (§2) The one fork that cannot be
   deferred behind a measurement, because everything else is sized by it.
   Proposed: yes, optional, with `http.py` shipping an implementation as the
   proof.
4. **Token storage** (§5): runtime-only, or the committed sidecar? Proposed:
   runtime in Phase 1, decide Phase 2 on Phase 1's numbers.
5. **Concurrency shape** (§4) → [`url-fetch-concurrency`](../compare/url-fetch-concurrency.compare.md).
   Proposed: declared capability, `min(declared, configured)`.
6. **The cap's default and scope** (§4): `4`? global or per-host? Proposed:
   `4`, global, promote on an observed 429.
7. **What the narrowed refresh is called.** `fux update --dirty`?
   `--stale`? `--changed`? It is a new flag on a verb that shipped
   **yesterday** (`v0.35.0`, 2026-08-21), and the name is the part that is
   expensive to change later — cheap now, a deprecation cycle in a month.
8. **Dead-URL reporting** (§6): `doctor` only, or also a standing line in
   `fux update`'s summary? Proposed: both — `doctor` is where someone looks
   deliberately, the summary is where someone looks anyway.

---

## Graduation trigger

**Two of these forks have already graduated** into the compare docs named
above; this file is the umbrella and the argument, not a substitute for them.

**The proposal as a whole graduates on a number: the fraction of a
`fux update` sweep that re-fetched a document whose sanitized sha was
unchanged.** That is measurable today with no new code — run `fux update`
twice against a real corpus and count. **At ≥ 80 %, §2 argues itself and fork
3 should be ruled yes.** Below ~40 %, the four-function contract stays as it
is and §1 plus §7 are the whole of this work.

**It does not graduate on corpus size**, deliberately. A 100k-URL corpus of
mostly-static reference pages needs this less than a 2k-URL corpus of active
wiki pages.

---

## References

- [`url-refresh-trigger`](../compare/url-refresh-trigger.compare.md) ·
  [`url-fetch-concurrency`](../compare/url-fetch-concurrency.compare.md) —
  the two live forks split out of this proposal
- [`record-freshness`](../compare/record-freshness.compare.md) — verdict D,
  no age bound in a record; §5 is the runtime loophole it did not close
- [`maintenance-trigger`](../compare/maintenance-trigger.compare.md) — the
  accepted answer for **files**, and the reasoning §3 explains does not
  transfer to URLs
- [`hook-at-scale`](../compare/hook-at-scale.compare.md) — verdict B, the
  deferring hook (W-66, built 2026-08-22)
- [`refer-fetch-cache`](../compare/refer-fetch-cache.compare.md) — the TTL
  cache, and `cached` as a fourth verdict state
- [ADR-URL-INGEST](../../docs/adr/0008_url-ingest.md) ·
  [ADR-FETCHER](../../docs/adr/0019_fetcher.md) ·
  [ADR-URL-LIST](../../docs/adr/0018_url-list.md) ·
  [ADR-REFER](../../docs/adr/0030_refer-plane.md) ·
  [ADR-MAINTENANCE](../../docs/adr/0032_hooks.md)
- [`maintain/dirty.py`](../../src/fux/maintain/dirty.py) ·
  [`maintain/runner.py`](../../src/fux/maintain/runner.py) ·
  [`ingest/run.py`](../../src/fux/ingest/run.py) (`only_urls`) ·
  [`ingest/urlsrc.py`](../../src/fux/ingest/urlsrc.py) (`fetch_all`,
  `sanitize`) · [`refer/freshness.py`](../../src/fux/refer/freshness.py) ·
  [`doctor.py`](../../src/fux/doctor.py)
- [`proposals/knowledge-ci.md`](knowledge-ci.md) — part (a), the staleness
  gate, is §3's CI option sketched on 2026-08-09
- **External** — RFC 9110 §8.8 (validators; `ETag` preferred over
  `Last-Modified` because content-based validation beats timestamps) ·
  J. Cho & H. Garcia-Molina, *Effective Page Refresh Policies for Web
  Crawlers*, ACM TODS 28(4), 2003 — the frequency-weighted freshness
  objective §1 reaches by observation instead of estimation, and the reason
  §4 does **not** propose an adaptive per-URL schedule: proportional-to-
  change-rate does not straightforwardly beat uniform
- [W-75](../open/W-75-url-freshness.md) — the tracked item
