# ANALYSIS — 2026-08-18 ingest / `.fux/` / index capture

One defect, and it is the serious kind: two shipped features that are each
correct on their own and cannot both be used.

---

## Finding — hashed meta makes the accelerator unbuildable (defect)

**What happens.** With `[sources.url] meta = "hashed"` — **the default**, and a
law-L5 default at that — `fux ingest --refresh-urls` writes the committed index
and then fails, exit 1:

```
error: .fux/index/aa.jsonl:2: the quoted 16-hex token '30aef0c52cf11116'
appears outside `terms` in record 'url:https://example.invalid/handbook/oncall'.
… Refusing to build a divergent accelerator.
```

Every subsequent `fux build` fails the same way. **A corpus containing one
hashed URL record can never have an accelerator again.**

**Why.** Two decisions, each right, that were never run together:

1. `ingest/run.py:135` — for hashed meta, `record["title_h"] = term_hash(title)`.
   No display text leaks; that is the point of the mode.
2. `derive/build.py::_assert_invariants` — refuses to build if a quoted 16-hex
   token appears outside `terms`, because `query/scan.py` derives `df` from
   **raw bytes** and would count that token as a term while the accelerator,
   counting from parsed postings, would not. The two paths would then score the
   same corpus differently — a breach of the differential law.

`term_hash` returns exactly a 16-hex string. So `title_h` is *always* a quoted
16-hex token outside `terms`, and the invariant *always* fires.

**Confirmed by contrast**, same corpus, same commands, one config key changed:

| `meta` | `ingest --refresh-urls` | accelerator | `ask` title |
|---|---|---|---|
| `"plain"` | exit 0 | builds (70 terms) | `Oncall handbook` |
| `"hashed"` *(default)* | **exit 1** | **never builds** | `30aef0c52cf11116` |

**Blast radius.** Hashed meta is the default for non-git sources, and URLs are
the only non-git source that ships. So the default URL-ingestion path yields a
corpus permanently stuck on the reference scan. On the RFC corpus that is the
difference between a warm p95 of **27.2 ms and 4 248.8 ms** — the entire M2
result, silently forfeited by using a documented default.

**Why it was not caught.** ADR-URL-MIDDLEWARE shipped in 0.31.x; the build-time
invariant shipped with the accelerator in 0.32.0. Each has tests; neither test
suite ingests a hashed URL record *and* builds. The R2/R3 runs are file-corpus
only. Nothing exercised the intersection.

**It is also silently correct-looking.** The committed index is written and
`ask` answers — from the scan. A user sees results, not a broken feature.

### Recommended fix

**Make `title_h` not look like a term**, rather than teaching the invariant
about exceptions:

```python
record["title_h"] = "h:" + store_mod.term_hash(fields.title)
```

- `scan.py`'s raw-byte regex stops matching it, so the two paths agree *by
  construction* — no exception list to keep in sync with a hash-shaped field
  that someone adds later.
- The invariant keeps its full strength. Exempting `title_h` by key name would
  weaken a check whose whole value is that it admits nothing.
- Two readers need the prefix stripped: `query/rank.py:90` and
  `derive/build.py:143`, both of which use `title_h` as a display fallback.

**Migration:** any committed index already holding `title_h` must be
re-ingested. Worth an `analyzer`/`_format` consideration before choosing the
final shape — that is a decision for the fix, not for this capture.

**Tests owed:** ingest a hashed URL record and build, asserting exit 0 and a
manifest; assert `scan` and `accelerator` return identical scores on a corpus
containing one. The differential harness never sees a hashed record today.

**Filed as [W-47](../../open/W-47-hashed-meta-blocks-accelerator.md).** Not
fixed here — this session's mandate is documentation, and a fix that changes
committed bytes needs its own commit, its own tests, and a call on migration.

---

## Checked and found sound

Recorded because they were suspected and cleared, and a future session should
not re-litigate them:

- **A failed build does not leave a stale accelerator answering silently.** The
  runtime manifest pins a per-shard sha of the committed bytes; on drift `ask`
  falls back to the scan, `--explain` reports `[scan]`, and `fux doctor` says
  `accelerator: stale … run \`fux build\``. Correct on all three surfaces.
- **Re-ingest is byte-identical** on an unchanged corpus (law L3), verified by
  `sha1sum` across runs.
- **A deletion is honoured** — the record and its now-empty shard file both
  disappear, rather than the record lingering.
- **A failed fetch does not delete a document.** `https://example.invalid/gone`
  is recorded as a skip and the batch continues.

## What this capture does not establish

- Nothing about ranking quality: five documents, hand-written.
- Nothing about performance: no timings taken, and cloud-container wall-clock
  is not comparable across surfaces ([`../../MACHINE.md`](../../MACHINE.md)).
- Nothing about a real browser middleware: the fixture's middleware is a
  no-network stand-in, which exercises the *contract*, not CDP.
