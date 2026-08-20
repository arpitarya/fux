---
type: Compare Doc
title: Refer-Plane Fetch Cache
description: Whether the refer plane should cache fetched `url:` bytes locally with a wall-clock TTL to avoid a live fetch on every citation, and how to do it without touching the committed record or breaking the three-state verdict.
status: accepted
timestamp: 2026-08-20T00:00:00Z
---

# Trading a fetch for a TTL — Comparison

> **Verdict: F — a gitignored, per-machine fetch cache for `url:`
> sources**, keyed by `loc`, carrying a real wall-clock `fetched_at`. This is
> the same non-reproducible-runtime-state pattern
> [ADR-RUNTIME-STAMP](../../docs/adr/0028_runtime-stamp.md) already uses for
> `stamp.json` — a cheap local pre-check ahead of the real one, never itself
> proof of freshness — applied to the refer plane's fetch step instead of the
> accelerator's build step. **It does not touch the committed record**:
> [record-freshness](record-freshness.compare.md)'s verdict D and
> [W-58](../open/W-58-no-recorded-ingest-time.md) are unaffected, because the
> clock lives in gitignored cache metadata, not in a shard. A cache-served
> answer gets a **fourth verdict state, `cached`**, carrying `age_seconds` —
> never silently relabelled `current` — so
> [ADR-REFER](../../docs/adr/0031_refer-plane.md) decision 6 still holds.
> Default `cache_ttl_seconds = 0` (off): a caller opts in per source, same
> shape as `mode = snapshot` already being opt-in.
> **Status:** ✅ accepted (Arpit, 2026-08-20) — **as proposed**: default
> `cache_ttl_seconds` **300 s**, and build proceeds **without waiting on
> R4**, on the Confluence-rate-limit rationale stated above. **This decision
> is independent of [W-58](../open/W-58-no-recorded-ingest-time.md) /
> [record-freshness](record-freshness.compare.md), which is still ⏳ awaiting
> Arpit on its own terms** — accepting F does not answer whether the
> committed record needs a timestamp; the two questions do not share a
> verdict.
> **Reopen when:** a real workflow shows the ACL-staleness window (below)
> caused a wrong-access answer — at that point `no_cache` becomes mandatory,
> not advisory, for the affected source class.

## Context

The refer plane fetches `url:` documents through the consumer's injected
fetcher and verifies by content sha
([ADR-REFER](../../docs/adr/0031_refer-plane.md) decisions 1–5). The existing
`ARC` cache (decision 9) is keyed `(loc, sha)` and is proven
**correctness-neutral** — "cannot change the answer" — because a hit only ever
returns bytes already known to match the recorded sha. It does not save the
*first* fetch, and it does nothing for `mode = always` re-verifying the same
document across repeated queries at the same index version other than avoid
re-downloading identical bytes.

[record-freshness](record-freshness.compare.md) settled a narrower question —
whether the **committed record** needs a timestamp — as **no**: content
verification is strictly more precise than any age, and a timestamp inside a
shard breaks reproducibility (mtimes don't survive a clone; a per-record epoch
rewrites every shard on re-ingest). That verdict is correct and this document
does not reopen it.

**Arpit's proposal, this conversation, 2026-08-20:** cache non-git-sourced
documents locally with a fetch timestamp; expose an age/freshness property; if
the cached copy isn't recent enough, fetch again, update the cache, *then*
answer. That is a different question from record-freshness's: it is not about
the committed index at all, it is about whether the refer plane should trust a
**local, ephemeral copy** for a bounded window before paying for a live fetch.

## What the field already worked out

**`stale-while-revalidate` (RFC 5861)** lets a cache "immediately return a
stale response while it revalidates it in the background, thereby hiding
latency (both in the network and on the server) from clients." The shape is
exactly what's proposed here: serve fast, but the spec never lets "fast" be
confused with "verified" — revalidation still happens, just not synchronously
on the caller's critical path.

**This repo already has the pattern**, one layer over:
[ADR-RUNTIME-STAMP](../../docs/adr/0028_runtime-stamp.md)'s `stamp.json`
records a per-shard `[size, mtime_ns]` specifically so `fux build` can skip a
real content-hash check on the common unchanged case — and is "deliberately
excluded" from the byte-identity set because mtimes aren't reproducible, and
is "never itself proof of freshness," only a filter ahead of the real check
(`manifest.json`'s content-sha map). A `url:` fetch cache with a wall-clock
`fetched_at` is the same idea, one pipeline stage later: a cheap, volatile,
gitignored pre-check ahead of the real one (content-sha verification against
the recorded sha).

**Enterprise source systems rate-limit, independent of R4.** Confluence
Cloud's REST API runs a points-based quota — apps share a **65,000-point
hourly pool by default** — and Atlassian's own avoidance guidance is to
"cache stable responses," "use ETags and conditional headers," and "distribute
requests over time." That is a second, independent justification the original
record-freshness document never had in view: it was reasoning about the
committed record and about *this caller's* latency (R4), not about hammering a
10⁵–10⁶-document Confluence estate with one fetch per citation per query
across every agent session hitting Fux at once — exactly the scale the
project's own litmus test names as the design point.

## The fork

Four sub-decisions, not one:

**1. Where does the cache live?** A separate, gitignored store —
`.fux/runtime/fetch-cache/`, alongside `stamp.json`/`manifest.json` — never
inside ARC's own keyspace. ARC's "cannot change the answer" proof depends on
being keyed by an *already-known-correct* sha; a TTL entry is served before
that's confirmed. Mixing the two stores risks a future edit accidentally
routing a TTL-hit through code that assumes the ARC invariant.

**2. What triggers a cache-serve vs. a real fetch?** Only relevant under
`mode = always` — `mode = never` never fetches at all (decision 7 stands,
untouched: reading the local checkout isn't a fetch and has no cache to
consult). A new policy field, `cache_ttl_seconds` (**default 0, disabled**):

- entry exists and `now − fetched_at ≤ cache_ttl_seconds` → serve the cached
  bytes, verify the recorded index sha against the **cached** `fetched_sha`
  (no network call) → label `cached`.
- otherwise → real fetch, overwrite the cache entry
  (`bytes`, `fetched_at = now`, `fetched_sha`), verify as today → `current` /
  `stale` / `unverified`.

Default-off matches decision 4's own logic: "a knob that lies is worse than a
missing knob" — at `cache_ttl_seconds = 0` there is no ambiguity about what a
caller is getting, because nothing is ever served from cache.

**3. The label.** Decision 6 exists so "nothing downstream can collapse 'we
did not look' into 'we looked and it was fine.'" A cache-serve *is* "we did
not look, this call" — so it needs the same discipline a fetch failure gets.
Proposed: a **fourth** verdict state, `cached`, carrying `age_seconds`.
`current` is reserved for "verified against the source this call," full stop.

**4. Build now, or wait for R4?** record-freshness's own reopen-trigger for a
corpus-level stamp was "R4 shows the fetch dominates, and a caller wants
bounded staleness to avoid it." Arpit is that caller, today — but the
Confluence rate-limit case is a *second* trigger the original document never
measured against, because it isn't about this caller's latency at all, it's
about not getting `429`'d by the source system regardless of how fast Fux's
own answer comes back. **Recommendation: proceed without R4**, on the
rate-limit rationale stated explicitly — not by quietly treating R4's trigger
as satisfied when it isn't.

**5. L2 / L5 — this is content, briefly, outside its source.** Caching fetched
*bytes* to local disk — even gitignored, even TTL-bounded — is the situation
L2's "single exception... explicit per-source `snapshot` policy" exists for.
Two consequences, both real forks Arpit should rule on rather than have
assumed:

- **Opt-in per source**, structurally identical to `mode = snapshot` already
  being opt-in — `cache_ttl_seconds = 0` is the default for every source
  unless a source's own config sets it.
- **ACL-staleness window.** An access grant can be revoked at the source
  between a cache write and a `cached`-labelled serve inside the TTL. A
  `no_cache` per-source escape hatch should exist regardless of
  `cache_ttl_seconds`, for any source flagged access-controlled or regulated —
  and the *default* TTL should stay short (proposing **300 s** as a starting
  number; open for Arpit to set) rather than something that turns a revoked
  grant into a five-minute-plus leak.

## Consequences

- **ADR-REFER gains a decision on acceptance** — not written into the ADR file
  yet, because this compare doc is what's live until Arpit rules; the decision
  and its veto-condition language land in ADR-REFER in the same change that
  builds this, per Law zero.
- **`Policy` gains `cache_ttl_seconds: int = 0`**, travelling in the bundle
  alongside `mode`/`timeout_seconds` per decision 8 — extended, not
  reinvented.
- **record-freshness and W-58 are unchanged.** No `_format` bump, no
  ADR-RECORD change, no shard rewritten — this is the option that costs the
  committed index nothing, same as D did.
- **New test surface**: a TTL hit returns bytes byte-identical to what a live
  fetch would have returned (same differential style as the existing ARC
  test); `cache_ttl_seconds = 0` never produces a `cached` verdict, ever —
  regression-proofing the opt-in default; the network fence
  (`tests/refer/test_refer_plane.py`'s AST import check) still passes, because
  this is cache bookkeeping, not a second fetch mechanism.

## Reopen trigger

**A real workflow shows the ACL-staleness window produced a wrong-access
answer** — a caller saw content from a source they'd since lost access to,
inside the TTL. At that point `no_cache` stops being advisory for
access-controlled sources and becomes mandatory, checked at ingest. Separately
— **not a reopen, a revisit**: once R4 runs, check whether the rate-limit
rationale alone still justifies the default TTL chosen here, now that the
latency question has an actual number.

## References

- `stale-while-revalidate`, RFC 5861 — <https://httpwg.org/specs/rfc5861.html>
- Confluence Cloud rate limiting and Atlassian's own caching/ETag guidance —
  <https://developer.atlassian.com/cloud/confluence/rate-limiting/>
- The precedent this reuses —
  [ADR-RUNTIME-STAMP](../../docs/adr/0028_runtime-stamp.md)
- The plane this amends — [ADR-REFER](../../docs/adr/0031_refer-plane.md),
  decisions 4, 6, 7, 9
- The sibling decision this does not reopen —
  [record-freshness](record-freshness.compare.md) ·
  [W-58](../open/W-58-no-recorded-ingest-time.md)
- The item this document backs — [W-60](../open/W-60-refer-fetch-cache.md)
