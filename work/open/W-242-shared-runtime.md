---
type: Handoff
name: W-242
description: "One derived plane, both readers (Arpit, 2026-09-30 — T0 · T1 · T2 in compare/shared-runtime): Node reads each shard once per query, reads Python's .fux/runtime/ when fresh, and builds the same plane byte-identically with its own `fux build`. No new cache; a query-result cache is refused. Ratified, not built."
item: W-242
filed: 2026-09-30
ball: agent
---

# W-242 — one runtime, two writers, two readers

**Status: ratified 2026-09-30, not built.** Arpit, 2026-09-30: *"I agree to
building tier zero, agree to building tier one, and agree to build tier two.
That means Node will also write."* Research, options and the refused T3:
[`compare/shared-runtime`](../compare/shared-runtime.compare.md). Diagram:
[`architecture-caching.svg`](../architecture-caching.svg). Recorded in
[SR-T1-ACCELERATOR](../../records/0110_accelerator.md) d18,
[SR-NODE-SEARCH](../../records/0153_node-search.md) d24,
[SR-CACHE](../../records/0131_cache.md) d13.

**Model:** Claude Code, **Opus**. Tier 2 is a second writer of a binary
format whose whole value is that two readers agree on it to the byte.

## The one idea

The "common file" is **`.fux/runtime/` exactly as Python writes it today** —
`postings/xx.jsonl` + `xx.idx`, `anchors/xx.json`, `docs.jsonl`, `stats.json`,
`mined.json`, `graph.json`, `manifest.json`, `stamp.json`. **Python's layout
is the contract; no file, field or schema string changes.** Either runtime may
build it; either runtime reads it when it is fresh and scans when it is not.

## Evidence (2026-09-30, one machine, the Cowork VM's mount)

- Node `find rollback`, this repo (1 995 docs, 257 shards, 38 MB): 0.36–0.42 s.
- **769 shard opens for 257 shards** — scan, `graphRecords` and
  `tableFromShards` each read every shard. `rawRecordLines` is 207 of 383 ms.
- The table and the caveat are in the compare doc. The filed baseline is
  step 0 below, not these numbers.

## Definition of done — in this order, one commit per tier

### Step 0 — baseline, pre-registered

1. `work/regression/<date>-shared-runtime/PRE-REGISTRATION.md`, frozen before
   any code: Node `find`, `ask`, `answer` on this repo and on fux-lab
   `rung-01000` and `rung-10000` (L9 — never the playground), medians of 7,
   cold and warm. Endpoint: wall time; stdout must be byte-identical before
   and after every tier.

### Tier 0 — each shard read once per Node query

2. One read of each shard per process, shared by `scan.mjs`,
   `reader.mjs::graphRecords` and `mined.mjs::tableFromShards`. Where the
   buffer lives (a per-call shard set passed down, or a reader object on
   `index.mjs`) is the builder's call; **a module-level cache that outlives a
   call is not** — `fux mcp` is long-lived and the index changes under it.
3. A test that counts shard reads per query (spy on the reader) and fails above
   one per shard.
4. Arm at 0 discordant; stdout byte-identical on six verb × corpus cells, as
   W-235 did.

### Tier 1 — Node reads the plane

5. Twins, owned by SR-T1-ACCELERATOR (Arpit's 2026-09-23 ownership rule):
   `node/src/derive/format.mjs` ↔ `format.py`, `node/src/derive/accel.mjs` ↔
   `accel.py`. Every file name and constant from `constants.toml` via
   `config/constants.mjs` (L12).
6. `isFresh` transcribes `accel.py::is_fresh` exactly: stamp and manifest
   present, `schema == RUNTIME_SCHEMA`, `docs_fields` equal, shard count equal,
   and each shard's `[size, mtime_ns]` equal to `stamp.json`'s.
   🔴 **`mtime_ns` needs `fs.statSync(p, {bigint: true}).mtimeNs`.** The values
   are ~1.79 × 10¹⁸, past 2⁵³; a `Number` rounds them and the check never
   matches — Node would scan forever and every test would still pass.
7. Candidates and statistics only, handed to the shared `rank.mjs` — never a
   score (SR-T1-ACCELERATOR d2). Transcribe the skip loop: rarest term first,
   exact `theta`, the per-field `mx`/`mnw` bound at the query's weights (d3,
   d5), the rounding-aware skip `round(bound, 9) < round(theta, 9)` (d6), the
   anchor seed before the loop (d15), `mined.json` for the pair table (d16),
   `1 + authority_weight` in the maximum (d17).
8. The 62-byte `.idx` entry (`<8sHQI` + `5H` + `5I` + `IIH`, little-endian) is
   decoded with `DataView`. **One committed fixture read by both suites** —
   `tests/derive/idx-fixture.*` with its decoded rows — the W-202 pattern,
   because a transposed field is a silent miss, not an error.
9. Anything not fresh — missing, stale, unknown `schema` — **answers from the
   scan, never an error**, as in Python. `ranked_by` says which.
   `--fast` / `--scan` get Node twins if Python's CLI still exposes them.
10. **Fork A is not in scope.** Node keeps rebuilding the graph plane in
    memory (SR-NODE-SEARCH d9) until Arpit rules.
11. Arm: Node-plane = Node-scan = Python-plane on candidates, `(n, total_wlen,
    df)` and ordering, on this repo, `rung-10000` and the adversarial index.

### Tier 2 — Node builds the plane

12. `node/src/derive/build.mjs` ↔ `_build.py`, and a Node `fux build` verb —
    today refused by name. Input: the committed shards and nothing else (d1).
13. **The two build invariants refuse the build**, as `_assert_invariants`
    does (d7) — never a divergent plane.
14. **The lock.** `.fux/runtime/write.lock` by SR-LOCKS' protocol, exactly:
    `O_CREAT|O_EXCL` (`fs.openSync(p, "wx")`), pid JSON, re-entry by pid, a
    malformed lock reads as held, nothing breaks a lock automatically. A Python
    `ingest` and a Node `build` must exclude each other through the file alone.
15. `derived_dir`'s side effects twinned — the `CACHEDIR.TAG`
    ([SR-CACHEDIR-TAG](../../records/0121_cachedir-tag.md)).
16. **Byte-identity.** Node-built vs Python-built, `diff -r` excluding
    `stamp.json`, on this repo, `rung-10000` and the adversarial index. Every
    `DETERMINISTIC_FILES` member, every `postings/*.jsonl` and `*.idx`, every
    `anchors/*.json`. Then the cross-read: Python answers from a Node-built
    plane and Node from a Python-built one, arm at 0 discordant.
17. **Write order:** the plane is valid only once `stamp.json` exists, so it is
    written **last**, after `manifest.json` — as Python does. A reader racing a
    build sees "stale" and scans, never a half-plane.
18. **When Node builds: only on `fux build`.** No read verb builds
    (SR-LOCKS d2 — read verbs hold nothing). See open question 2.

### Close

19. Filed run: step 0's cells after each tier, in the pre-registered folder.
20. Records amended **in the same change as the code** (below), the
    `architecture-two-readers.svg` redrawn (Node gains a plane and a writer),
    CHANGELOG, and this item archived.

## Hazards — each one has bitten this codebase before in some form

- **JSON bytes differ by serializer, and differ per file.** `_write_json` and
  `docs.jsonl` use `sort_keys=True, separators=(",",":"), ensure_ascii=False`;
  **`graph/plane.py` uses `sort_keys=False` and the default `ensure_ascii=True`**
  — so `graph.json` escapes every non-ASCII character as `\uXXXX` and keeps
  insertion order. `JSON.stringify` does neither. Write each file's serializer
  deliberately.
- **Float text.** Python `repr` and JS `toString` differ (`1e-07` vs `1e-7`,
  `1e+16` vs `10000000000000000`). Route every float through
  `compat/pyfloat.mjs`.
- **Sort order.** Python sorts by code point; `cmpCodePoints` exists for this.
  `Array.prototype.sort` with no comparator sorts UTF-16 units.
- **mtime precision** — step 6. Also: the stamp's mtimes are written from the
  build's own `stat`, so the Node build must stat with BigInt too.
- **Mixed versions.** A consumer on an older Node bundle meets a newer Python
  plane: `schema` mismatch → scan. The reverse is the same. Never an error,
  never a guess.
- **The differential arm must not compare a plane with itself.** Each lane
  names which runtime built the plane it reads.

## Open questions — Arpit's, none blocks Tiers 0–2

1. **Fork A** — does Node read `graph.json` when fresh? Recommendation: yes in
   production; the harness forces a rebuild so N2 still proves digest equality.
   Worth ~55 ms of today's 383.
2. **Auto-build.** Should a Node read verb build a missing plane? Recommendation:
   **no** — it turns a read into a writer and breaks SR-LOCKS d2. `fux doctor`
   already says *"run `fux build`"*.

## Out of scope

- T3, the query-result cache — refused (compare doc, *Why not T3*).
- Node `ingest` — it needs the decoder plane (SR-NODE-SEARCH d11).
- Any change to the plane's format.

## Records this will touch, in the build change

SR-T1-ACCELERATOR (d18 moves to built; owns `node/src/derive/`) ·
SR-NODE-SEARCH (d9 if Fork A, d10, d24, the verb list) · SR-LOCKS (d1 — a
second writer) · SR-CLI (Node `build`) · SR-API (if `index.mjs` exposes it) ·
SR-CACHEDIR-TAG · `records/README.md` ownership rows · `tests/test_node_twins.py`
(the `_build.py` → `build.mjs` private-module rule already covers it) ·
CHANGELOG.
