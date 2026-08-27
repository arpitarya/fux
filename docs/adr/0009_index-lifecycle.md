---
type: ADR
name: ADR-INDEX-LIFECYCLE
title: ADR-INDEX-LIFECYCLE (0009) — how the index is generated and updated
description: One canonical encoder, sharded doc-major JSONL, write-if-different; a derived accelerator bound by the differential law and detected stale by per-shard shas.
status: accepted
date: 2026-08-18
feature: generation and update of the committed index, and the refusal that keeps its derived accelerator from diverging
owns: [src/fux/store]
laws: [L1, L2, L3, L6]
timestamp: 2026-08-18T00:00:00Z
---

# ADR-INDEX-LIFECYCLE — how the index is generated and updated

## §1 — For humans

There are two indexes, and confusing them is the source of most questions.

The **committed index** is the product: `.fux/index/*.jsonl`, sharded, one
document per line, in git. It is what a colleague gets when they clone. It is
written through a single canonical encoder, so the same sources always produce
the same bytes — that is what makes it diffable and mergeable at all.

The **derived accelerator** is a cache: `.fux/runtime/`, gitignored, rebuilt by
`fux build`. It exists purely to make queries fast, and it is bound by a law —
its answers must be **byte-identical** to the reference scan's. If it cannot
guarantee that, it refuses to build rather than shipping a faster wrong answer.

Updates are cheap because writes are conditional: a shard whose bytes come out
identical is not touched. And staleness is not a guess — the runtime manifest
pins a sha of each committed shard, so the engine knows when its cache is
behind and falls back to the scan on its own.

**Diagram — Mermaid and its ASCII twin. Update both, always, together.**

```mermaid
flowchart TD
    R["records"] --> C["canonical encoder<br/>sorted keys · no floats · no nulls · NFC"]
    C --> S["shard = blake2b(id, 1 byte)<br/>256 shards"]
    S --> WD{"bytes identical?"}
    WD -->|yes| N["leave the file alone"]
    WD -->|no| WW[".fux/index/xx.jsonl — COMMITTED"]
    WW --> B["fux build"]
    B --> INV{"invariants hold?"}
    INV -->|no| ERR["refuse — exit 1"]
    INV -->|yes| A[".fux/runtime/ — DERIVED<br/>manifest pins per-shard sha"]
    A --> Q{"manifest matches?"}
    Q -->|yes| FAST["accelerator answers"]
    Q -->|no| SCAN["stale → scan answers"]
```

<details>
<summary><b>ASCII twin</b> — the same diagram, for terminals, diffs, and any reader without a Mermaid renderer</summary>

```text
   records
      |
      v
  canonical encoder   sorted keys · no floats · no nulls · NFC
      |
      v
  shard = blake2b(id, 1 byte)  ->  256 shards
      |
      +-- bytes identical? --yes--> leave the file alone
      |
      no
      v
  .fux/index/xx.jsonl   COMMITTED  (in git)
      |
      | fux build
      v
  invariants hold? --no--> refuse, exit 1 (never a divergent accelerator)
      |
     yes
      v
  .fux/runtime/   DERIVED  (gitignored; manifest pins a sha per shard)
      |
      +-- manifest matches committed shas? --yes--> accelerator answers
      |
      no --> STALE: the scan answers, and doctor/--explain say so
```

</details>

### Examples

The committed side — a header line, then one document per line:

```console
$ head -1 .fux/index/2e.jsonl
{"_format":"fux.index.v2","analyzer":"v2","tf_fields":["body","heading","title","path","ctx"]}
```

The derived side refuses rather than diverging, and says so when it is stale:

```console
$ fux build
error: .fux/index/aa.jsonl:2: … Refusing to build a divergent accelerator.
# exit 1

$ fux doctor
[OK] accelerator: stale (the committed index changed since it was built) - `ask` falls back to the scan; run `fux build`
```

---

## §2 — For agents

### Context

The committed index has to be three things at once: **small** enough to live in
git, **diffable** so a review shows what changed, and **mergeable** so two
branches touching different documents do not conflict. Those constraints, not
query speed, chose the format.

Query speed is then bought back with a derived structure — which introduces the
real risk. A cache that answers *differently* from the reference path is worse
than no cache, because the disagreement is invisible: both return results, and
only one is right.

### Decision

**1. Sharded doc-major JSONL.** One document per line; shard =
`blake2b(id, digest_size=1)` → `00.jsonl`…`ff.jsonl`, fixed at 256. Doc-major
means one document's change touches one line in one file, which is what makes
merges land.

**2. One canonical encoder, enforced at the write boundary.** Sorted keys,
`(",", ":")` separators, `ensure_ascii=False`, no floats, no nulls, NFC text.
Enforced in `store/canonical.py` rather than trusted of callers: a bug in
`ingest/` must fail loudly at the boundary, not silently corrupt committed
bytes.

**3. Every shard file opens with a `_format` header line**, carrying the schema
id, the analyzer version and the tf-field list, so a reader knows the schema and
analyzer without a side channel. Today: `fux.index.v2` / `v2` /
`["body","heading","title","path","ctx"]`, from
[`store/format.py`](../../src/fux/store/format.py).

**4. Write-if-different.** A shard whose bytes come out identical is left
untouched, so `git status` stays clean and re-ingest is free to run on a hook.

**5. The derived plane is disposable and never committed.** `.fux/runtime/` is
a pure function of `.fux/index/` — nothing else is an input. That is what makes
`rm -rf` on it always safe.

**6. The build refuses rather than diverging.** Two invariants are asserted at
build time, from the raw committed bytes: no quoted 16-hex token appears outside
`terms`, and the length field is found where the scan's regex finds it. If
either fails the build errors out, because `scan.py` derives its statistics from
raw bytes while the accelerator derives them from parsed records, and the two
must agree by construction.

**7. Staleness is detected, not assumed.** The runtime manifest pins a sha per
committed shard. On drift, `ask` falls back to the scan and says so under
`--explain`; `fux doctor` reports it.

**8. Term-hash collisions fail the build**, tracked across the whole run by a
single shared tracker — two distinct terms sharing an 8-byte digest would
silently merge their postings.

**9. A value-encoding change does not bump `_format` or `analyzer`; a property
change does.** Three conditions, all of which must hold:

1. **The property set is unchanged.** Nothing appeared, nothing left. Adding or
   removing a property is a schema change and bumps `_format`, because a reader
   cannot know what it is missing.
2. **`analyzer` is untouched by construction.** It versions how text becomes
   *terms*; a display field is not a term — it never enters `terms`, never
   enters the postings, and never participates in scoring
   ([ADR-RANKING](0012_ranking.md)). A display field cannot make a corpus's
   statistics mean something different.
3. **The old shape is already refused, per record, with the migration named.**
   `fux build` asserts decision 6 on every record; a `_format` bump would add a
   second, *coarser* refusal that says strictly less than the one that already
   fires.

**And the cost is asymmetric.** `_format` sits in the header line of every
shard, so bumping it rewrites all 256 headers in every consumer's index — a
whole-corpus diff — for a change touching one field on one record kind.
Meanwhile an old reader meeting a new value gets an opaque display string
either way. **Loud where it matters, nil where it does not** is what makes the
bump unnecessary rather than merely expensive.

**10. An analyzer change bumps `analyzer` and not `_format`.** Analyzer v2
splits identifiers *before* lowercasing and Porter-stems *before* hashing
(`query/analyzer.py`, `query/stem.py`). Both change which hash a given piece of
text produces, so **every `terms` key in the index changes** — and yet the
property set is unchanged: a record still has `terms`, still maps a 16-hex hash
to a per-field tf. **The function that produces the key changed**, and that is
precisely what the `analyzer` field pins.

**Nothing tries to migrate, and nothing tries to mix.** `store/reader.py`
refuses a shard whose header names another analyzer, and ingest's carry-forward
is gated on the same header, so a bump invalidates every carried field at once
rather than leaving a corpus half-analyzed. Two analyzers inside one index would
be undetectable at query time and would corrupt every `df`.

**10a. `--full` is the migration, and it must actually work on the index it
replaces.** `ingest` used to read the prior index unconditionally, before any
`--full` check, in order to carry `url:` records forward — so the documented
migration **refused the exact index it exists to replace**, and the only way out
was `rm -rf .fux/index/`, which silently destroys every `url:` record, the one
thing in the index that is not a function of a committed file.
`ingest/run.py::_existing_index` splits the two cases on one line:

> **Record identity is schema-stable; record content is not.**

- **`--full` on a foreign index** reads `id` and nothing else
  (`store/reader.py::foreign_url_ids`). No `url:` records → the old shards are
  discarded and every document is re-extracted from source, losing nothing a
  re-extraction does not restore. Any `url:` records → **refuse**, name them,
  and point at `fux update`, which is the only thing that can rebuild them.
- **A delta run on a foreign index** still refuses outright. Carry-forward
  genuinely cannot proceed across analyzers.
- **`read_index` still refuses a foreign shard**, unchanged.

This does not weaken *"nothing tries to migrate"* — it is what makes the
sentence true, because the alternative in practice was a consumer deleting the
directory by hand and never being told what went with it. Pinned by
[`tests/store/test_foreign_index.py`](../../tests/store/test_foreign_index.py),
including that `read_index` and delta ingest both still refuse.

**11. The record's shape is declared in one schema file, not four places.**
[`store/index-record.schema.json`](../../src/fux/store/index-record.schema.json)
declares every field — its type, when it is required, its default, whether it
carries display text, whether a delta ingest may carry it forward, and whether
it is omitted rather than written false. `store/recordschema.py` loads it;
`store/writer.py` reads `DISPLAY_FIELDS` from it; `ingest/run.py` builds both
record kinds through it.

⚠ **What it replaces agreed with itself only by habit.** The shape was assembled
inline **twice** in `ingest/run.py` (once for `git`, once for `url`), policed by
a `DISPLAY_FIELDS` tuple in `store/`, carried forward by an `EXTRACTED_FIELDS`
tuple in `ingest/`, and described in prose by
[ADR-RECORD](0010_index-record.md). **Nothing compared them.** Adding a display
field meant remembering a tuple in a different module, and forgetting was
**silent**: the field shipped and L5's check simply did not look at it.

Four properties hold it in place:

- **It changes no committed byte, and a test asserts exactly that** by comparing
  canonical encodings rather than dicts. `canonical_dumps` sorts keys, so the
  schema's key order is presentation and cannot reach the index — also asserted,
  because if that stops being true the schema silently becomes a wire format.
- **What *can* reach a byte is the field set, the defaults and `omit_when`**,
  which is why the schema's `schema` string must equal `SCHEMA_ID`: two fux
  versions with different shapes must never both call their output
  `fux.index.v2`.
- ⚠ **`validate()` is deliberately not on the write path.** `write_index`
  already enforces the one rule that closes a leak (L5's meta policy) and
  `canonical_dumps` already refuses floats, nulls and hostile text; a third gate
  on the hot path would re-check what those two guarantee. It is a tool for
  tests and for callers building records by hand — and **a test asserts the
  writer does not call it**, so the distinction cannot rot into an assumption.
- **`build()` refuses an undeclared field.** A typo'd key used to sail into the
  committed index and never be read again — no error, no test, a field that
  exists forever and means nothing.

**It is a schema, not a template**, and the vocabulary matters: a template is
something you copy and fill in, which is what `templates/http.py.txt` is. This
file is not copied anywhere — it declares a shape and is checked against the
code.

⚠ **It lives in `src/fux/store/`, not `src/fux/templates/`, and the ADR guard
is why.** The first commit attempt was refused: `templates/` is claimed by
[ADR-FETCHER](0019_fetcher.md), so a record-shape file put there would have been
owned by a record with nothing to say about the record shape. Beside the code
that owns it, the ownership is correct **by construction**.

**12. The derived plane has a schema too, and it covers all four shapes.**
[`derive/runtime.schema.json`](../../src/fux/derive/runtime.schema.json)
declares the postings block line, the 62-byte offset-table entry, the doc table
and `stats.json` — deliberately together, because they are written by one build,
read by one query path, and versioned by **one string** (`RUNTIME_SCHEMA`, today
`fux.runtime.v5`). Four files would invite three to be updated and the fourth
forgotten.

⚠ **A disposable plane still needs a schema, and the reason is not tidiness.**
The accelerator must return byte-identical results to the reference scan, so a
shape that drifts does not corrupt the index — **it makes one of the two paths
disagree, which is a fast wrong answer.** `superseded` and `mtime` were once
added to the doc table while `RUNTIME_SCHEMA` stayed put, and `ask --scan`
applied a supersession demotion that `ask --fast` did not. The **struct string**
is the sharpest case: it was described in prose and checked by nothing, and it
has already been wrong once (the entry grew 40 → 62 bytes).

**Every declared shape carries a worked example, and the examples are tested** —
not decorated. The record schema's examples are `validate()`d *and* pushed
through `canonical_dumps`, because an example that validates but cannot be
written is still a lie about what a record looks like. The offset entry's
example is packed and round-tripped. **A test asserts every shape has one**,
since a shape without an example is a shape somebody will guess at.

**13. L5 is enforced inside `write_index`**, per record, **before any shard is
touched**. It lived in one caller, so any second writer could have put a private
document's title into a committed shard and nothing would have refused. A
rejected batch now leaves the index exactly as it was, and there is no path into
a committed shard that skips the check. A non-git record must *state* `meta`; a
missing value is refused rather than defaulted, because guessing on a caller's
behalf is the leak the law exists to close.

`assert_meta_policy` carries a second per-record refusal in the same call — one
door, one lock, extended rather than duplicated: a `hashed` record with no
matching entry in `.fux/runtime/display-cache/` (keyed by `sha`) is refused.
The cache is gitignored runtime state, same tier as the accelerator, so decision
5 already covers it. Full rationale on [ADR-RECORD](0010_index-record.md).

### What it looks like

Verbatim from
[the capture](../../work/regression/2026-08-18-ingest-and-index/report.md). It
predates the v2 analyzer and the `flen` field and is **not edited** — a
transcript rewritten to match today's code is no longer evidence of anything.
The shapes it demonstrates — one header line then one document per line, shard
addressing, per-shard shas in the manifest — are unchanged.

**A shard, header line then documents:**

```console
$ head -c 240 .fux/index/2e.jsonl
{"_format":"fux.index.v1","analyzer":"v1","tf_fields":["heading","body"]}
{"code":"MlLhv73WJJYbpSiyUpUqGlZkY-rXcOv3D1-yqmU5txU","edges":[],"id":"file:docs/refer.md","loc":"docs/refer.md","meta":"plain","mode":"extracted","phrases":["The ref
```

**Shard addressing, verified against the files on disk:**

```console
file:docs/refer.md        -> 2e.jsonl
file:docs/pruning.md      -> 88.jsonl
file:docs/index-format.md -> e6.jsonl
```

**The derived manifest — the per-shard shas are the staleness mechanism:**

```json
{
  "analyzer": "v1",
  "block_size": 128,
  "blocks": 78,
  "docs": 3,
  "index_schema": "fux.index.v1",
  "schema": "fux.runtime.v1",
  "shards": {
    "2e.jsonl": "2d4f19bcd8f8af905da1103648c3df21007d3255",
    "88.jsonl": "61abfc1c7540bf7b0626fbb9de360a42496b5908",
    "e6.jsonl": "c7c7b09f882e30a96612927a3d1921c79f4e57b2"
  },
  "terms": 78
}
```

**Staleness, handled honestly** — checked precisely because a silent stale read
would be a serious defect:

```console
$ fux ask "who carries the pager" --explain
3.0934  30aef0c52cf11116  (https://example.invalid/handbook/oncall)

[scan]

$ fux doctor
[OK] accelerator: stale (the committed index changed since it was built) - `ask` falls back to the scan; run `fux build`
```

**A refused build** — the invariant doing its job, exit 1, on an index written
before `title_h` gained its `h:` prefix. Decision 9 is why the message names a
re-ingest rather than a version bump:

```console
$ fux build
error: .fux/index/aa.jsonl:2: the quoted 16-hex token '30aef0c52cf11116' appears
outside `terms` in record 'url:…/oncall'. `query/scan.py` counts it toward that
term's df from the raw bytes, and the accelerator counts from the postings, so
the two paths would score this corpus differently. Refusing to build a divergent
accelerator. This record's `title_h` predates the `h:` prefix
(ADR-INDEX-LIFECYCLE): re-run `fux update` to rewrite it.
```

**A corpus written today builds clean**, because the prefix means the scan's
pattern cannot match `title_h` at all — the two paths agree by construction, and
the differential harness carries a hashed record to prove it.

**An engine upgrade must say so, and say what to do.** Amended 2026-08-27, on
[the R10 run](../../work/regression/2026-08-27-r10-separation-floor/ANALYSIS.md) §2.

- **The situation.** `fux-playground`'s committed index was `fux.index.v1`; the
  engine writes `fux.index.v2`. **All 50 goldens failed** with
  `shard missing/mismatched _format header`, which reads as **corruption**.
- ⚠ **It was the least informative of `read_shard`'s three header checks, and
  it guards the likeliest case.** The analyzer and `tf_fields` checks beside it
  have always named found-and-expected; the `_format` one — the one an **engine
  upgrade** trips — named neither.
- **There is no migrate verb and there is not going to be one.** The way out is
  deleting `.fux/index/` and re-ingesting, which is safe **because the index
  holds statistics and never content** (L2 paying off), and the message now says
  exactly that.
- **A MISSING header is a different failure and says so.** No `_format` at all
  means the file is not a shard or the write was truncated. Telling someone to
  re-ingest over a half-written file is worse advice than none.
- **Refusing is unchanged.** Only the message moved; a foreign shard has always
  been refused rather than guessed at, and still is.

### Consequences

- **The committed index is reviewable.** A document change is one line in one
  shard, and `git diff` shows it.
- **Merges land per document.** Two branches editing different documents touch
  different lines and usually different shards.
  `.fux/index/*.jsonl` merges through a custom driver rather than textually
  ([ADR-MERGE-DRIVER](0033_merge-driver.md)); decision 4's write-if-different
  discipline is what makes that safe, because the driver's output is sorted by
  id, so two machines merging the same three inputs produce the same bytes.
- **The accelerator can be deleted at any moment** without loss, which is what
  lets it be rebuilt aggressively.
- **The invariant can refuse a build the user did not knowingly cause.** That is
  the correct trade, and it bit once: hashed URL records always tripped it, so
  the L5 default shipped an index no build would accept. **The invariant was not
  the bug; the field shape was.** Recorded here because the refusal *looks* like
  an accelerator defect and is not.
- **256 shards is fixed, not configurable.** `[index] shards` documents the
  value rather than setting it; changing it rewrites every path in the tree.
- **An analyzer bump owes a full re-ingest on every existing index.** Until it
  runs, `store/reader.py` refuses the committed shards — loudly, by design,
  rather than returning a silently wrong ranking. On this repo the v2 migration
  discharged 434 records / 218 shards / 6.3 MB, and a delta run reproduces the
  full run's shards byte for byte, so L3 holds on the migrated index.
- **Committed index size is measured, never gated.** A packed-size promise at
  100 000 documents was retired by ruling and has **no successor**; a size
  promise returns only as a new prediction at 10 000 documents with a new id.
  The preliminary read on this repo's own index measured **2.429×** git-pack
  compression — against today's plain-JSON placeholder rather than
  [ADR-POSTINGS](0013_postings.md)'s designed encoding, which is unbuilt. Read
  it as a number to watch, never as a pass or a fail; see
  [the analysis](../../work/regression/2026-08-21-r7-preliminary-analysis/ANALYSIS.md).

### Alternatives considered

- **SQLite.** Rejected: a binary file does not diff or merge, which forfeits
  the entire premise of committing the index to git.
- **Term-major postings in the committed plane.** Rejected: one document's edit
  would touch every term it contains, spraying the diff across the tree.
  Term-major is exactly right for the *derived* plane, which is where it lives.
- **Pruned postings** to shrink the committed index. Rejected on measurement:
  the gate failed — the best selector was 35.9 points below unpruned recall@20
  at 6 % retention. Full postings, permanently.
- **Commit the accelerator too**, to skip a build step on clone. Rejected: it
  changes on every ingest and is a pure function of bytes already committed.
- **Trust the accelerator and reconcile later.** Rejected outright: a wrong
  answer that arrives fast is the failure this engine is built to refuse.
- **Validate every record on the write path.** Rejected under decision 11: it
  re-checks what the encoder and the meta policy already guarantee, on the hot
  path, and a gate that duplicates another gate is the one that gets loosened
  first.

### Reference (required)

- The encoder —
  [`src/fux/store/canonical.py`](../../src/fux/store/canonical.py);
  addressing — [`format.py`](../../src/fux/store/format.py); conditional writes
  — [`writer.py`](../../src/fux/store/writer.py); collisions —
  [`collisions.py`](../../src/fux/store/collisions.py); the declared record
  shape —
  [`index-record.schema.json`](../../src/fux/store/index-record.schema.json)
  and [`recordschema.py`](../../src/fux/store/recordschema.py).
- The build and its invariants —
  [`src/fux/derive/build.py`](../../src/fux/derive/build.py) (the module
  docstring states why raw-byte and parsed statistics must agree); the derived
  plane's declared shapes —
  [`derive/runtime.schema.json`](../../src/fux/derive/runtime.schema.json).
- The write-time refusals — `assert_meta_policy` in
  [`store/writer.py`](../../src/fux/store/writer.py); the cache it checks —
  [`store/displaycache.py`](../../src/fux/store/displaycache.py).
- Artifacts and staleness behaviour, captured —
  [`work/regression/2026-08-18-ingest-and-index/`](../../work/regression/2026-08-18-ingest-and-index/report.md) §§2–5.
- The measured basis for the accelerator and the differential law —
  [`work/regression/2026-08-12-m2-accelerator/`](../../work/regression/2026-08-12-m2-accelerator/report.md).
- Canonical JSON, the prior art this follows — RFC 8785 (JCS):
  https://www.rfc-editor.org/rfc/rfc8785

### Veto condition

**Reopen this decision if** the committed index stops being byte-reproducible,
or if the accelerator is ever observed disagreeing with the scan.

**How to check it:**

```bash
# 1. byte-reproducibility — the property everything else rests on
sha1sum .fux/index/*.jsonl > /tmp/a && fux ingest >/dev/null \
  && sha1sum .fux/index/*.jsonl > /tmp/b && diff /tmp/a /tmp/b && echo OK

# 2. the two paths still agree, on this corpus
diff <(fux ask "any query" --json --fast) <(fux ask "any query" --scan --json) && echo IDENTICAL

# 3. the invariants are still asserted at build time
grep -n '_assert_invariants' src/fux/derive/build.py
# expect: defined and called per record — removing the call is the veto

# 4. the schema string still matches the code that writes it
grep -n 'SCHEMA_ID' src/fux/store/format.py
python3 -c "import json;print(json.load(open('src/fux/store/index-record.schema.json'))['schema'])"
# expect: the same string — two shapes must never both be called fux.index.v2
```

---

## References

*Every source this record cites, gathered in one place. §2's **Reference
(required)** names the grounding; this is the complete list. An archived
document is never listed here — the body may name one, but archive is not
evidence.*

**Records** — [ADR-LAWS](0001_laws.md) · [ADR-RECORD](0010_index-record.md) ·
[ADR-T1-ACCELERATOR](0011_accelerator.md) · [ADR-RANKING](0012_ranking.md) ·
[ADR-POSTINGS](0013_postings.md) · [ADR-FETCHER](0019_fetcher.md) ·
[ADR-MAINTENANCE](0032_hooks.md) · [ADR-MERGE-DRIVER](0033_merge-driver.md)

**Code**

- [`src/fux/derive/build.py`](../../src/fux/derive/build.py)
- [`src/fux/derive/runtime.schema.json`](../../src/fux/derive/runtime.schema.json)
- [`src/fux/store/canonical.py`](../../src/fux/store/canonical.py)
- [`src/fux/store/collisions.py`](../../src/fux/store/collisions.py)
- [`src/fux/store/displaycache.py`](../../src/fux/store/displaycache.py)
- [`src/fux/store/format.py`](../../src/fux/store/format.py)
- [`src/fux/store/index-record.schema.json`](../../src/fux/store/index-record.schema.json)
- [`src/fux/store/recordschema.py`](../../src/fux/store/recordschema.py)
- [`src/fux/store/writer.py`](../../src/fux/store/writer.py)
- [`tests/store/test_foreign_index.py`](../../tests/store/test_foreign_index.py)

**Measured evidence**

- [`work/regression/2026-08-12-m2-accelerator/report.md`](../../work/regression/2026-08-12-m2-accelerator/report.md)
- [`work/regression/2026-08-18-ingest-and-index/report.md`](../../work/regression/2026-08-18-ingest-and-index/report.md)
- [`work/regression/2026-08-19-w54/report.md`](../../work/regression/2026-08-19-w54/report.md)
- [`work/regression/2026-08-21-r7-preliminary-analysis/ANALYSIS.md`](../../work/regression/2026-08-21-r7-preliminary-analysis/ANALYSIS.md)

**Papers and specifications**

- RFC 8785 (JSON Canonicalization Scheme) — the canonical-JSON prior art the
  encoder follows
  <https://www.rfc-editor.org/rfc/rfc8785>
