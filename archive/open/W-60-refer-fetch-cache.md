# W-60 — a TTL-bounded local cache for `url:` fetches, so the refer plane doesn't hit the source on every citation

**Status:** OPEN (Lane A) — **DECIDED 2026-08-20, Arpit: option F.**
[`refer-fetch-cache.compare.md`](../compare/refer-fetch-cache.compare.md) is
accepted as proposed: a gitignored, per-machine cache keyed by `loc`, a real
wall-clock `fetched_at` (same treatment as `stamp.json`), a new
`cache_ttl_seconds` policy knob (**default 300 s**, opt-in per source), and a
fourth verdict state `cached` so decision 6's three-state guarantee survives.
**Does not touch the committed record** — record-freshness's verdict D and
W-58 are unaffected and remain separately ⏳ awaiting Arpit. · **Filed:**
2026-08-20
**Blocked by:** — · **unblocks:** nothing else is waiting on it; it is itself
the whole ask.
**Model:** **Opus** — it amends ADR-REFER's correctness invariant (decision
9's "cannot change the answer" contract) and carries an ACL-staleness question
under L2/L5; a wrong call here is exactly the "confident, plausible, wrong"
failure mode CLAUDE.md warns an under-powered model produces silently.

## The finding / origin

Arpit, in conversation, 2026-08-20: cache non-git-sourced documents locally
with a fetch timestamp; expose an age/freshness property; if the cached copy
isn't recent enough, fetch again, update the cache, then answer.
Independently grounded beyond the original ask: Confluence Cloud's REST API is
rate-limited (a 65,000-point/hour shared pool by default), and Atlassian's own
avoidance guidance is "cache stable responses" and "use ETags and conditional
headers" — a live confirmation of CLAUDE.md's "enterprise realities are design
inputs" litmus, not just a latency optimisation gated on R4.

## Definition of done

- [x] **Arpit ratified 2026-08-20**: option F, as proposed — default
      `cache_ttl_seconds = 300 s`, build proceeds without waiting on R4, on
      the rate-limit rationale.
- [ ] `Policy` gains `cache_ttl_seconds: int = 0`; travels in the bundle
      (decision 8).
- [ ] A `.fux/runtime/fetch-cache/` store, gitignored, **separate from ARC's
      own storage** — entries `{loc, fetched_at, fetched_sha, bytes}`.
- [ ] The verdict enum gains `cached`, carrying `age_seconds`;
      `current`/`stale`/`unverified` unchanged in meaning.
- [ ] `mode = never` unaffected (decision 7) — it never fetches, so there is
      nothing to cache-serve.
- [ ] Tests: a TTL hit returns bytes byte-identical to what a live fetch would
      return (same style as the existing ARC differential);
      `cache_ttl_seconds = 0` never produces a `cached` verdict, under any
      input (regression-proofs the opt-in default); the network fence
      (`tests/refer/test_refer_plane.py`'s AST import check) still passes —
      this is cache bookkeeping, not a second fetch mechanism.
- [ ] A `no_cache` per-source escape hatch for access-controlled/regulated
      sources, honoured regardless of `cache_ttl_seconds`.
- [ ] ADR-REFER amended in the same change that builds this (Law zero): a new
      decision, plus veto-condition language for the ACL-staleness case.
- [ ] `record-freshness.compare.md` / W-58 explicitly noted as untouched in
      the amendment, so a future reader doesn't conflate the two.

## Hazard

**Do not let a `cached` verdict get summarised as `current` anywhere
downstream** — that is decision 4's "knob that lies," refused once already,
reappearing in a new location. **Do not store the TTL cache inside ARC's own
keyspace** — ARC's "cannot change the answer" proof depends on being keyed by
an already-known-correct sha; a TTL entry is served *before* that's confirmed,
so the two stores must stay provably separate.

## Evidence

This conversation, 2026-08-20 (Cowork). Confluence rate-limit figures and
`stale-while-revalidate` semantics are in
[`refer-fetch-cache.compare.md`](../compare/refer-fetch-cache.compare.md)'s
References section, fetched live 2026-08-20.
