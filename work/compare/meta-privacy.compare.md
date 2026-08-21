---
type: Compare Doc
title: Meta Privacy
description: The committed index leaks summaries of access-controlled documents — plain vs hashed-default vs hashed-only meta; reopened for materialise-first display and its two forks.
status: accepted
timestamp: 2026-08-21T00:00:00Z
---

# Index meta privacy — Comparison

> **Original verdict (2026-08-09, unchanged): Hashed by default for every
> non-git source; plain requires explicit per-source config**
> (`meta = hashed | plain` on the ledger entry). Enforced at write time.
> **Reopened 2026-08-21 (PRIORITY.md P5)** — not by the trigger below, but by
> Arpit's own instruction: hashing-by-default is right, but `hashed` should
> stop meaning *unreadable*. §Reopened 2026-08-21 adds **option D —
> materialise first, then index**, plus rulings on the two forks and three
> sub-questions PRIORITY.md reserved for Arpit specifically, not an agent.
> **Status:** ✅ accepted (both halves) · **Confidence:** high on the
> original A/B/C call; medium-high on D's forks (D2/D5 accept a real, stated
> cost — see below) · **Reopen when (original, unfired):** an enterprise
> partner requires plaintext meta *and* proves repo-ACL ⊇ source-ACL. The
> second half of the original trigger — "hashed mode's degraded `explain`
> labels measurably block adoption" — is what 2026-08-21 answers.

## Context

A KL top-128 term list plus YAKE phrases is a decent *summary* of a
confidential Confluence page — sitting in every clone, in git history,
forever, readable by repo-cloners who lack Confluence access. Repo ACL
would silently become the union of all source ACLs. Term *hashes* mitigate
(postings/dictionary already store blake2b64 only) but common-word hashes
are dictionary-attackable, and `M/` titles/phrases were plaintext in v1.

## Options

- **A — Hashed by default, plain opt-in** *(verdict)*: external sources
  commit only hashes (query-able — queries hash their terms too — but not
  human-readable); git-dir sources default plain (cloners already have the
  content); `explain`/graph labels degrade to doc titles-from-fetch for
  hashed sources.
- **B — Plain everywhere**: best UX; unacceptable cross-ACL leak (git
  history makes it permanent).
- **C — Hashed everywhere**: max safety; needlessly lobotomizes labels for
  repo docs whose content every cloner can read anyway.

## Matrix

| criterion (weight) | A default-hashed | B plain | C all-hashed |
|---|---|---|---|
| cross-ACL leak (H) | **contained** | permanent | contained |
| ranking quality (H) | unchanged (hashes rank fine) | unchanged | unchanged |
| explain/graph labels (M) | degraded for external only | full | degraded everywhere |
| dictionary-attack residue (M) | hashes only; phrases absent | n/a | hashes only |
| enterprise review story (H) | **defensible** | fails | defensible, overkill |

## Consequences

`M/` stores per-source either plaintext or hash-only records; fetch-time
titles backfill display for hashed sources (cached in ARC, never
committed). Security section in the eventual ADR-0019 cites this doc.
Residual risk stated honestly: hashed terms remain vulnerable to
dictionary attack for common vocabulary — the leak is reduced to term-set
membership, not eliminated; sources needing zero index presence use
`mode = skip` (don't index), which M3 must also support.

## References

Paper §3.1, §9 · council transcript (WORKLOG 2026-08-09) · blake2b (stdlib)
· the `mode/meta` policy fields in PLAN M2–M3.

## Reopen-trigger (original A/B/C call)

See verdict block.

---

## Reopened 2026-08-21 — materialise-first, and five rulings

PRIORITY.md's P5 row named two forks explicitly reserved for Arpit ("not an
agent") and three narrower sub-questions also needing his verdict. All five
were put to him directly, with grounding gathered from the code first so he
was choosing between real options, not hypothetical ones. Rulings below;
implementation landed in the same change that added this section.

### Option D — materialise first, then index

The three original options (A/B/C, above) were about *what the committed
record carries*. D is orthogonal — it is about *what backs the display*, and
it is what makes closing the leak affordable to even discuss:

- **D — materialise first, then index** *(adopted)*: a non-git document's
  bytes are already in ingest's memory before its record is written
  (`fresh[doc_id]` in `ingest/run.py`) — extracting and caching the title
  there costs a write, not a fetch. The title lands in
  `.fux/runtime/display-cache/` (gitignored, content-addressed by `sha`,
  never committed) **before** `store/writer.py` will accept a `hashed`
  record for that `sha`. Every reader-facing surface
  (`display_title` in `store/format.py`, called from `ask`/`find`/`answer`,
  text and `--json` both) resolves from that cache, never from the committed
  line. A cold cache (evicted, or a pre-P5 record) degrades to the hash,
  **labelled** (`"<hash> (uncached — title unavailable)"`) rather than a bare
  hash indistinguishable from a working system.

D does not change the A/B/C verdict — hashing stays the default for non-git
sources. It changes what `hashed` *costs* a reader.

### Fork (a) — does the mandatory cache need an L2 exception?

**Ruled: no — outside L2 entirely.** Not "`hashed` implies `snapshot`", and
not a new named exception either.

Grounding: [ADR-CACHE](../../docs/adr/0035_cache.md) (written two days
earlier, same author, same reasoning target) already ruled that ARC and the
TTL fetch cache — gitignored, per-machine, never committed — sit outside
L2's scope: *"L2 forbids durable content; this store is deliberately the
opposite... nothing here is ever committed, so there is nothing for L2 to
except."* The P5 display cache is the same shape (gitignored,
content-addressed, local-only, never committed) and the identical reasoning
applies without modification. `store/displaycache.py`'s own docstring cites
this precedent rather than re-arguing it. CLAUDE.md §L2 and ADR-LAWS are
**untouched** by this change — the alternative (a new named exception) would
have added permanent normative surface for something that, on inspection,
never needed excepting.

### Fork (b) — the delta path: what happens on a cache miss?

**Ruled: force a re-fetch to repopulate — refuse rather than silently
commit or silently degrade.**

The literal question — does `_reusable()` ever carry forward a `hashed`
record without a fresh fetch, and if its cache went cold, does ingest force
network or admit a legal miss — turned out to be **structurally moot for
today's code**: `_reusable()`'s carry-forward gate is `src == "git" and meta
== "plain"` (`ingest/run.py`), so a non-git/`hashed` record is *never*
carried forward without a fetch attempt regardless of this ruling. Every
`--refresh-urls` run already re-fetches every configured URL, so "force a
re-fetch" is what the existing mechanism already does once the cache-write is
added to it — no new network trigger was needed to honour the ruling.

What the ruling *does* buy: **the invariant is enforced, not advisory.**
`store/writer.py`'s `assert_meta_policy` refuses to commit *any* `hashed`
record — freshly fetched or carried forward, on any call path, not just
ingest's — unless its `sha` has a cache entry. A plain `fux ingest` (no
`--refresh-urls`) still makes **zero** network calls, preserving the
offline-by-default guarantee `test_plain_ingest_is_offline_and_carries_urls_
forward` already pins down — it can now also fail loudly (naming the fix as
`--refresh-urls`) rather than commit a record no reader can ever show a title
for. The considered alternative — degrade silently at read time, never force
anything — was not chosen: refusal at write time is a stronger, earlier
guarantee than a read-time label, and it was available at no extra cost once
D's cache-write was already happening.

### Sub-question — salt term hashes per index?

**Ruled: don't build it.** A committed, per-index salt is not a salt — a
cloner receives it in the same clone. A genuine per-deployment salt
(out-of-band, shared only with legitimate query clients) was considered and
rejected: real added complexity — a new provisioning story every consumer of
the index has to get right — for a narrower gain than the original framing
implied, since volume leakage (`terms`' tf, `wlen`) reconstructs an attacker's
picture regardless of how the term *keys* were hashed. The honest fix this
row's own research pointed at is committing less, not hashing harder; salting
was not built.

### Sub-question — hash or drop `loc`/`id` for non-git sources?

**Not ruled — resolved by architecture before it reached Arpit.** Grounding
found `loc` is the literal fetch address the refer plane calls
(`fetcher(loc)` in `refer/source.py`, no other route exists for a fresh
clone that never ran ingest) and it is already committed in plaintext via a
second, independent path — the full URL list at `.fux/sources/url`
([ADR-URL-LIST](../../docs/adr/0018_url-list.md)). Hashing or dropping `loc`
in the `M/` record would cost the refer plane's only way to fetch a hashed
document, for **zero** added privacy (the URL is already readable one file
over). `loc`/`id` are unchanged. This is stated here as a finding, not a
ruling, because there was no live choice to put to Arpit once the fetch
dependency was grounded.

### Sub-question — exclude `code` from hashed records?

**Ruled: keep it.** `code` (a 32-byte sign-quantized embedding,
`embed/fuxvec.py`) stays on `hashed` records exactly as on `plain` ones.
Embedding inversion against it is a demonstrated attack, not a theoretical
one (92% exact-match text recovery from 32-token GTR embeddings, Morris et
al., EMNLP 2023, <https://arxiv.org/abs/2310.06816>) — the strongest-evidenced
of the three original leaks named in PRIORITY.md's row. Excluding it would
have cost `--hybrid`'s dense-lane ranking specifically for hashed documents
(`query/hybrid.py`'s `_dense_ids` drops any record with no `code`), a real
ranking cost weighed against a risk that is accepted and **documented here**
rather than closed. Reopen this specific call if `--hybrid` ever becomes
default-on (today it is default-off, PRIORITY.md/CHANGELOG) — the exposure
widens with the surface that uses the field.

## Reopen-trigger (2026-08-21 rulings)

Any of: (a) L2's "outside entirely" reasoning is shown wrong for *this*
cache specifically (not just cited from ADR-CACHE) — e.g. a real caller finds
a path where display-cache content becomes committed or otherwise durable
outside the source system; (b) a corpus is found where `_reusable()`'s
carry-forward gate *does* admit a non-git record without a fetch (a code
change this doc did not anticipate), reopening whether force-refetch still
holds; (c) `--hybrid` flips default-on, reopening the `code`-exclusion call;
(d) an enterprise partner's threat model makes volume leakage (tf/`wlen`)
the live concern rather than dictionary attack, which would revisit "commit
less" as a real design direction rather than a research note.
