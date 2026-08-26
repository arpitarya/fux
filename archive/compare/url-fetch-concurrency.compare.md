---
type: Compare Doc
title: URL Fetch Concurrency — parallelising a contract that is single-URL by design
description: Arpit's cap on parallel URL refreshes, and the question underneath it — the shipped cdp fetcher is not thread-safe, so concurrency is a contract question before it is a config key. Compares sequential, a blind pool, declared capability, fetch_many, and processes.
status: proposed
timestamp: 2026-08-22T00:00:00Z
---

# URL fetch concurrency — Comparison

> **Verdict: C — declared capability, with the cap resolved as
> `min(fetcher's declared maximum, configured maximum)` — proposed, not
> ruled.**
> A fetcher module may declare `MAX_PARALLEL = n`; **absent the declaration
> the value is 1** and behaviour is byte-for-byte what ships today. Fux pools
> only up to what the module declared, and never above what the consumer
> configured. This is [ADR-FETCHER](../../docs/adr/0019_fetcher.md) decision
> 5's own principle — **declared, never detected** — applied to a second
> property, and it is the only option that lets the shipped `http.py` (which
> *is* thread-safe) go parallel without breaking the shipped `cdp.py` (which
> is *not*: `connect()` sets a module-global `_session` holding one WebSocket,
> and `fetch()` reuses it).
> **The finding that makes this cheap: sequential fetching is not what makes
> the index deterministic — the sort is.**
> [`fetch_all`](../../src/fux/ingest/urlsrc.py) ends
> `fetched.sort(key=lambda f: f.url)` and `skipped.sort(...)`, so completion
> order never reaches the committed bytes. Concurrency inside that function
> is invisible to L3.
> **Two knobs, two different kinds of refusal**, per Arpit's standing rule
> (*state the cost, don't clamp the knob*): the module's declaration is
> **capability** and exceeding it is a correctness violation → hard refusal;
> the config value is **policy** and a large one is merely rude → **warn with
> the number, never clamp**. `max_parallel < 1` is broken → refuse.
> **Status:** ⏳ awaiting Arpit (2026-08-22). **Confidence:** high on C over
> B/D/E, high on the sort finding, **medium** on the default (`4`) and
> **low-to-medium** on global-vs-per-host, which is the live sub-fork below.
> **Reopen when:** a consumer's URL list is dominated by one host and a
> politeness complaint or a 429 is actually observed — that is the evidence
> that turns the per-host sub-fork from theory into a defect; **or** a fetcher
> appears that is safe to call concurrently but only within one host, which
> `MAX_PARALLEL` as a single integer cannot express.

## Context

Arpit's request was a cap: *"on refresh URL, I want a limit of number of
parallel URLs that can be refreshed."* **A cap presumes parallelism, and
there is none.** [`fetch_all`](../../src/fux/ingest/urlsrc.py) walks URLs in
a strictly sequential loop, sorted, grouped by fetcher, inside one
`connect()`/`close()` bracket per group. At the design point in CLAUDE.md's
litmus that is the binding cost of every option in
[`url-refresh-trigger`](url-refresh-trigger.compare.md): 100k sequential
plain GETs is hours, and 100k sequential browser renders is not a number
worth writing down.

So the cap and the concurrency are one item, and **the cap is the easy half.**
The hard half is that the contract is single-URL on purpose
([ADR-FETCHER](../../docs/adr/0019_fetcher.md) decision 2), and one of the two
fetchers fux ships cannot survive being called from two threads.

**What the two shipped fetchers actually do** — checked, not assumed:

| | `http.py` | `cdp.py` |
|---|---|---|
| state during `fetch` | reads module globals; builds a fresh `urllib.request.Request` per call | **`global _session`** — one WebSocket set by `connect()`, reused by every `fetch()` |
| `configure` | mutates globals via `globals()[name] = …`, **once, before any fetch** | same shape |
| safe to call from N threads | **yes** | **no** — one socket, sequenced CDP message ids |

That asymmetry is the entire argument for C. A blanket pool would be correct
for the fetcher most consumers use and silently corrupt for the one the
enterprise design point exists to serve.

**There is no threading anywhere in `src/fux/` today** — no `threading`, no
`concurrent.futures`, no `multiprocessing`. This is the first. `concurrent.futures`
is stdlib, so **L1 is untouched**; the novelty is the argument, not the import.

## Options

**A — sequential (status quo).** Nothing to build. The cap is a knob with
nothing to cap, and `fux update` at scale stays unusable.

**B — a thread pool over `fetch()`, unconditionally.** Fux runs N workers.
Correct for `http.py`. **Silently wrong for `cdp.py`** — interleaved CDP
frames on one socket, and the failure presents as garbled or swapped page
content, i.e. as *wrong documents indexed*, not as a crash. It also breaks
every consumer-written fetcher that assumed the contract's serial shape,
which the contract entitled them to assume.

**C — declared capability.** The module optionally sets `MAX_PARALLEL = n`.
Fux uses `min(declared, configured)` workers, default `1` when undeclared.
`http.py` ships declaring a value; `cdp.py` ships declaring nothing (or `1`
explicitly, which is better — see Consequences). Existing and consumer-written
fetchers are unaffected by construction.

**D — an optional `fetch_many(urls) -> dict[str, str]`.** The fetcher owns
its own concurrency entirely. Maximum power, and it hands the fetcher a
responsibility fux currently holds and holds well: **per-URL error
isolation.** Today a `fetch` that raises becomes one `Skipped` and the batch
continues; a `fetch_many` that raises loses the whole group, and every fetcher
author has to re-implement the isolation `fetch_all` already does correctly.
It is also a second, larger amendment to a four-function contract that has
survived two callers unchanged.

**E — a process pool**, one fetcher instance per process. Sidesteps thread
safety entirely. Also runs `configure()`/`connect()` N times — for `cdp.py`
that is **N Chrome instances**, and for any fetcher holding an SSO session it
is N logins. Heavy, and it turns a concurrency setting into a resource
incident.

## Matrix

| criterion (weight) | A sequential | B blind pool | **C declared** | D `fetch_many` | E processes |
|---|---|---|---|---|---|
| safe for the shipped `cdp.py` (H) | yes | **no — silent corruption** | **yes** | yes | yes, at N× cost |
| safe for existing consumer fetchers (H) | yes | **no** | **yes — default 1** | yes | yes |
| keeps per-URL error isolation in fux (H) | yes | yes | **yes** | **no** | yes |
| committed bytes unaffected (H) | yes | yes — the sort | yes — the sort | yes — the sort | yes — the sort |
| contract amendment size (M) | none | none, but breaks the promise | **a module constant, not a function** | **a fifth function** | none |
| speed-up available (M) | 1× | N× | **N×, where declared** | N× | N×, minus startup |
| resource cost (M) | lowest | low | low | fetcher's choice | **highest** |
| expresses per-host politeness (L) | n/a | no | no — see sub-fork | fetcher's choice | no |

## Why the losers lose

**B's failure mode is the disqualifying one, and it is not "it crashes".** Two
threads writing frames onto one CDP socket produce *plausible documents
attributed to the wrong URLs*. That lands in the committed index, passes
every determinism check (the sort still runs), and is discovered by a human
reading an answer. **A concurrency bug that presents as a content bug is the
worst class available** in an engine whose entire promise is citation
fidelity.

**D loses on a subtlety worth stating**, because at first glance it is the
"proper" design: it moves error isolation across the boundary. ADR-FETCHER
decision 2's shape — *one URL in, one document or a raise out* — is what lets
`fetch_all` turn a dead page into a `Skipped` and keep going, which is
[ADR-URL-INGEST](../../docs/adr/0008_url-ingest.md) decision 4 in code. Under
`fetch_many`, decision 4 becomes something each consumer must reimplement
correctly, and most will not.

**E is not wrong, it is disproportionate.** It buys thread-safety with
process count, and the fetcher most in need of concurrency (`cdp.py`, the
slow one) is exactly the fetcher whose per-process cost is highest.

## The cap, and the two kinds of refusal

Arpit's rule — **state the cost, refuse only what is broken or duplicates a
tool** — resolves cleanly here because there are two different values wearing
one name:

- **`MAX_PARALLEL` in the fetcher module is capability.** It is the author
  saying *this code is safe at N*. A configured value above it is not a
  preference, it is a correctness violation, so it is **clamped down to the
  declaration, loudly, on stderr** — naming the module and the number.
- **`[sources.url] max_parallel` in `fux.toml` is policy** — politeness,
  local bandwidth, how much load the wiki should take. **Never clamped
  down**; a large value is honoured, with a stderr warning that states the
  cost in the units that matter: *"max_parallel = 64 will open up to 64
  concurrent connections; most Confluence deployments rate-limit above ~10
  and will return 429, which fux records as a skip — a skip keeps the prior
  record, so a throttled run looks like a quiet one."*
- **`max_parallel < 1` is broken** and refuses with a `FuxError`, the same
  treatment `cache_ttl_seconds < 0` already gets in
  [`refer/freshness.py`](../../src/fux/refer/freshness.py).

**Proposed default: `4`.** Low enough to be polite to a single intranet host
without configuration, high enough that the difference from `1` is
immediately visible. It is a judgement call, not a measurement — flagged as
such, and cheap to change.

## The live sub-fork: global or per-host?

`max_parallel` as one integer is a **global** cap. The crawler literature's
politeness constraint is **per-host**, because the resource being protected
is one server, not the network. A corpus of 100k URLs spread over 40 hosts
with a global cap of 4 is *under*-parallel; the same cap against one
Confluence is roughly right.

Three shapes, listed without a recommendation because the evidence to choose
does not exist yet:

1. **Global only.** One key, simple, correct for the single-wiki corpus that
   is the common case at the design point.
2. **Global plus a per-host default** (`max_parallel` and
   `max_parallel_per_host`), both honoured, the stricter binding.
3. **Per-host only**, derived from the URL's netloc.

**Proposed: ship 1, and let the reopen-trigger above promote it to 2 when a
429 is actually observed.** Shipping 2 now means picking a second default with
no more evidence than the first.

## Consequences

- **`cdp.py` should declare `MAX_PARALLEL = 1` explicitly rather than omit
  it.** Omission and `1` behave identically, but the explicit line is where
  the *reason* gets written down for the consumer who copies the file and
  starts editing — which is the whole point of shipping fetchers as consumer
  code from birth (ADR-FETCHER decision 5).
- **The progress plane (W-64) needs no change and gains meaning.** Its rule
  is **counts, not clocks**, and a count completed is still a count completed
  out of order. A parallel fetch is the case that most needed a progress
  bar and least needed a timer.
- **This composes with the validator** (`proposals/url-freshness.md` §3): if
  a `validate` function lands, it runs under the same pool and the same cap,
  and the cheap-check-then-fetch shape multiplies with the parallelism rather
  than competing with it.
- **`connect()` / `close()` stay once per group, not once per worker.** That
  is what makes C safe to reason about: the lifecycle is unchanged and only
  `fetch` is called concurrently. A fetcher declaring `MAX_PARALLEL > 1` is
  declaring exactly that — *my `fetch` is reentrant given one `connect`*.
- **One test is owed that no amount of manual checking substitutes for**: a
  fetcher declaring `1` must be observed never to have two `fetch` calls in
  flight. Assert it with a counter inside a test fetcher, not by reading the
  pool code.

## Reopen trigger

Stated in the verdict block: **an observed 429 or politeness complaint** on a
single-host-dominated corpus promotes the per-host sub-fork from theory to
defect; **a fetcher that is concurrency-safe only within a host** is the case
a single `MAX_PARALLEL` integer cannot express and would force shape 2 or 3.

## References

- [ADR-FETCHER](../../docs/adr/0019_fetcher.md) — decision 2 (four functions,
  one required), decision 5 (**declared, never detected** — the principle C
  extends), decision 6 (fetchers are consumer code from birth)
- [ADR-URL-INGEST](../../docs/adr/0008_url-ingest.md) — decision 4, the
  per-URL skip that D would relocate
- [`ingest/urlsrc.py`](../../src/fux/ingest/urlsrc.py) — `fetch_all`, and the
  trailing sorts that make concurrency invisible to the committed bytes
- [`src/fux/templates/cdp.py.txt`](../../src/fux/templates/cdp.py.txt) —
  `global _session`, the reason B is unsafe ·
  [`http.py.txt`](../../src/fux/templates/http.py.txt) — the reason A is
  leaving speed on the table
- [`refer/freshness.py`](../../src/fux/refer/freshness.py) — the
  refuse-what-is-broken precedent (`cache_ttl_seconds < 0`)
- [`proposals/tune-file-and-source-priority.md`](../proposals/tune-file-and-source-priority.md)
  — Arpit's *state the cost, don't clamp the knob* rule, and the boundary
  test that keeps `max_parallel` out of `tune.toml`: **it changes no byte in
  `.fux/index/`, but it is not a ranking value either — it is operational,
  so it belongs in `fux.toml` beside the other `[sources.url]` keys**
- [`url-refresh-trigger`](url-refresh-trigger.compare.md) — the sibling fork;
  every clock in it is bounded by the throughput decided here
