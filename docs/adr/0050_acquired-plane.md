---
type: ADR
name: ADR-ACQUIRED
title: "ADR-ACQUIRED (0050) — retained source bytes"
description: "Fetched source bytes are retained in .fux/acquired/, a third category beside committed and derived: gitignored, and not rebuildable."
status: accepted
date: 2026-09-01
feature: the acquired plane
owns: [src/fux/store/acquired.py]
laws: []
timestamp: 2026-09-01T00:00:00Z
---

# ADR-ACQUIRED: fetched bytes are kept, in a plane that is neither committed nor derived

## §1 — For humans

Ingest fetches a URL, decodes the bytes, keeps the markdown and drops the bytes. Nothing retains the file the record was built from. ARC is in memory and dies with the process; `runtime/fetch-cache/` is a 300-second throttle guard that expires by design. So a `url:` record can only ever be checked against a *fresh fetch* — which needs the network, the session, and the source still existing.

`.fux/acquired/` keeps those bytes. A citation becomes checkable against the exact input that produced it, a decoder change can be replayed without a network round trip, and a failed verify stops meaning *"we know nothing"*.

It is a new category rather than a subdirectory of `runtime/` because of one property: **it is not rebuildable.** `runtime/` is defined by being reconstructible from committed bytes by `fux build`. An acquired blob can only be re-*acquired*, and only while the source still exists and the browser session still holds. Gitignored, like derived. Recoverable, unlike derived.

```mermaid
flowchart LR
    F["fetch()"] --> U["_unpack"]
    U --> R{"refused?"}
    R -- yes --> S["Skipped"]
    R -- no --> A[".fux/acquired/"]
    A --> D["_decode_fetched"]
    D --> I[".fux/index/"]
    A -.-> V["refer: as-ingested"]
```

<details>
<summary><b>ASCII twin</b> — the same diagram, for terminals, diffs, and any reader without a Mermaid renderer</summary>

```text
  +---------+    +----------+    +----------+  no   +------------+    +---------+    +--------+
  | fetch() | -> | _unpack  | -> | refused? | ----> | .fux/      | -> | _decode | -> | index/ |
  +---------+    +----------+    +----------+       | acquired/  |    +---------+    +--------+
                                      | yes         +------------+
                                      v                   :
                                 +---------+              v
                                 | Skipped |        refer: "as-ingested"
                                 +---------+
```

</details>

### Examples

```console
$ tree .fux/acquired/
  CACHEDIR.TAG   (176 bytes)
  manifest.json   (322 bytes)
  objects/39/3925dcbab1097fd3199d170719c619df5a22d5a1b1b5fe3e9726bcb35a7f41af.xlsx   (3,004 bytes)

$ cat .fux/acquired/manifest.json
{
  "entries": {
    "https://1drv.ms/x/c/.../TOKEN?download=1": {
      "bytes": 3004,
      "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      "run_seq": 4,
      "sha": "3925dcbab1097fd3199d170719c619df5a22d5a1b1b5fe3e9726bcb35a7f41af"
    }
  },
  "schema": "fux.acquired.v1"
}
```

---

## §2 — For agents

### Context

Three facts made this necessary at once.

`refer` can only verify a `url:` document by re-fetching it, so a disconnected or signed-out session degrades every citation to `unverified` — the weakest verdict, and indistinguishable from never having looked. A decoder change forces a full re-fetch of every URL to rebuild records from bytes fux already had and threw away. And the browser-session fetcher (ADR-CDP-FETCHER) makes fetching *expensive and interactive*: a signed-in Chrome, one URL at a time, which is a poor thing to require at answer time.

None is solved by the two caches that already exist, and `refer/fetchcache.py` states why: ARC caches what a fetch returned, keyed `(loc, sha)`, in memory; the fetch cache caches *whether a fetch is needed at all*, with a TTL. Neither is an artifact store, and conflating an expiring cache with a retained original is the mistake that file's own docstring warns against.

### Decision

1. **`.fux/acquired/` is a third category in `fuxdir.py`, beside `COMMITTED` and `DERIVED`.** It is gitignored and carries `CACHEDIR.TAG` like a derived plane, and it is **not rebuildable** — which is why it is not one.
2. **The layout is `acquired/objects/<sha256[:2]>/<sha256><ext>` plus `acquired/manifest.json`.** The extension comes from `_TYPE_EXT`, so a blob is both decoder-dispatchable and openable by a human. Sharding follows the index's own convention.
3. **The blob sha is not a field on the index record.** A sha on a committed record states a fact true on one machine: two developers pull the same repo, one has the bytes, and the record claims both do. The url→sha map lives in `manifest.json`, gitignored and advisory — the same shape and guarantees as `url-state.json`. **The record shape does not change.**
4. **`keep` is a line attribute defaulting to `true`**, resolved through the same three layers as `meta`: built-in default, then `[sources.url] keep`, then the line. `keep=false` or `--no-keep` opts out.
   ⚠ **It defaulted to `false` for one day.** The argument for off-by-default was a stranger's 9 000-URL corpus quietly filling a disk. Decision 8 answers that directly — the store is bounded and evicts — and once the blast radius is bounded, defaulting off means almost nobody gets the thing the plane exists for.
5. **Retention happens in `fetch_all()`, never inside a fetcher.** W-86 P8 removed conversion from `http.py` and `cdp.py` because it lived there as two hand-maintained copies that a comment asked to keep identical and nothing checked. Retention in the fetchers repeats that defect exactly, and would make *which fetcher retrieved a document* observable again. Above the boundary, every fetcher gains retention with no line changed in any of them.
6. **The order is `_unpack` → refusal check → persist → decode.** A refusal is never stored. Retaining a login page would keep the wrong bytes *and* make them look authoritative.
7. **The plane holds no wall clock.** Ordering is by `run_seq`, read from `maintain/urlstate.py` rather than started here — two run counters would drift, and the one that drifts would be the one deciding what gets deleted. Wall clock lives in `runtime/fetch-cache/` and nowhere else.
8. **The store is bounded by `[sources.url] acquired_max_bytes` (default 2 GiB), and eviction is by `run_seq`, oldest first** — never by `mtime`, which would be a clock. **A blob whose URL has `fail_streak > 0` is never evicted**: that is precisely the copy that cannot be re-acquired. `fail_streak > 0`, not `>= FAILING_STREAK` — that constant is the threshold for *reporting* a URL as dead; here one failure already means "may not be re-acquirable", and the cost of protecting it is one blob of disk.
9. **Sweeping and eviction are different acts.** `sweep()` removes blobs no URL points at — unreachable by construction, so nothing citable is lost. `evict()` removes something still referenced. Keeping them apart is what makes the second one safe to reason about.
10. **Only `url:` documents are retained.** A `file:` document is already on disk; a second copy would be nonsense.
11. **The manifest is written once, at the end of `fetch_all`.** Fetches run under a thread pool, and a per-fetch write is a corruption.

**Output — the plane after one retained fetch:**

```console
$ tree .fux/acquired/
  CACHEDIR.TAG
  manifest.json
  objects/39/3925dcbab1097fd3199d170719c619df5a22d5a1b1b5fe3e9726bcb35a7f41af.xlsx
```

### Consequences

**Easier.** A citation can be checked offline against the exact bytes that produced it — a stronger claim than comparing two fetches, which is why `refer/source.py` verifies with the same fetcher a document was ingested with: *a document fetched two ways is two documents*. A retained original removes that whole class of false staleness, and the browser-session fetcher stops being needed at answer time.

**Harder.** `.fux/` now has a directory that grows, and a bounded store means an eviction policy, which means a way to lose the only local copy of something. Decision 8's two rules are what confine that loss to blobs a re-fetch can restore; they are not optimisations and removing either breaks the guarantee.

**Owed.** A retained blob is source content on disk — gitignored, but present. The gitignore is machine-checked by `fux doctor`'s check-ignore assertion rather than trusted to a reader, and `CACHEDIR.TAG` keeps it out of backups. ⚠ **This paragraph named two gaps that Phase 3 had already closed, and it said so for a day** — `doctor._acquired_health` reports blob count, total bytes and the 80%-of-cap warning, and `sources._drop_acquired` drops the manifest entry and sweeps the blob on `fux remove <url>`. **A record describing behaviour the code no longer has reads as authority**, which is exactly Law zero's third obligation. What is genuinely still owed is **one** thing, filed in [`work/OPEN-WORK.md`](../../work/OPEN-WORK.md): `fux doctor` does not report the **`as-ingested` share**, which is this record's own veto check — until it does, that veto cannot be run.

### Alternatives considered

- **A save side-effect inside a consumer fetcher.** Costs no engine change and no record at all, and was the leading option until retention had to cover every fetcher. At that point it becomes three implementations of one behaviour across `http.py`, `cdp.py` and any successor — the exact duplication W-86 P8 removed, re-introduced under a different name.
- **A `blob` field on the index record.** Rejected by decision 3. Not merely expensive (a record-shape version question immediately after `fux.index.v2`) but wrong, because it commits a per-machine fact.
- **Reusing `runtime/fetch-cache/`.** Rejected: a TTL entry expires, and an artifact store that expires is not one. `fetchcache.py`'s own argument for keeping two stores provably separate applies unchanged to a third.
- **Storing under `runtime/`.** Rejected by decision 1. `runtime/` means rebuildable, and this is not.
- **Eviction by `mtime`.** Rejected by decision 7. It is the obvious implementation and it smuggles a wall clock into a plane that forbids one, through the filesystem rather than through a field.

### Reference (required)

- `src/fux/store/fuxdir.py` — the `COMMITTED` / `DERIVED` declaration this record extends
- `src/fux/refer/fetchcache.py` — the two-stores-provably-separate argument, and the wall-clock invariant
- `src/fux/maintain/urlstate.py` — the counters-not-clocks precedent, and `fail_streak`
- `tests/store/test_acquired.py` — 24 tests, including the failing-URL eviction guard and the no-wall-clock assertion
- ADR-DOTFUX (`0003_fux-directory.md`) · ADR-FETCHER (`0019_fetcher.md`) · ADR-REFER (`0030_refer-plane.md`)

### Veto condition

**Reopen this decision if:** `as-ingested` verdicts exceed a quarter of verified citations on a corpus whose sources are all reachable. That would mean the plane is masking a broken fetch path rather than covering a rare one, and the right fix is the fetch path, not a larger store.

**How to check it:** `fux doctor --json` — compare the `as-ingested` count against total verified citations.

> ⚠ **No output block for the veto check yet.** `fux doctor` does not report the count, so the check cannot be run today; it is filed with the two other doctor gaps in *Consequences*. `docs/adr/TEMPLATE.md` is explicit that an invented transcript is worse than none — capture it when doctor reports the number.

---

## References

*Every source this record cites, gathered in one place. §2's **Reference (required)** names the grounding; this is the complete list. An archived document is never listed here — the body may name one, but archive is not evidence.*

**Records:** ADR-DOTFUX · ADR-FETCHER · ADR-REFER · ADR-RECORD · ADR-URL-LIST · ADR-URL-INGEST · ADR-CACHEDIR-TAG · ADR-CLI · ADR-URL-FRESHNESS

**Code:**

- `src/fux/store/acquired.py`
- `src/fux/store/fuxdir.py`
- `src/fux/refer/fetchcache.py`
- `src/fux/refer/source.py`
- `src/fux/refer/freshness.py`
- `src/fux/maintain/urlstate.py`
- `src/fux/ingest/urlsrc.py`
- `src/fux/ingest/sourcelist.py`

**Tests:**

- `tests/store/test_acquired.py`
- `tests/refer/test_freshness_ttl.py`

**Work:**

- [`archive/open/W-98-acquired-plane.md`](../../archive/open/W-98-acquired-plane.md) — the item that produced this record, **named and not cited**: it was archived on 2026-09-01 when all four phases landed, and two of its own claims were wrong
