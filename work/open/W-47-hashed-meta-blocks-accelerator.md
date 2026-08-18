# W-47 — hashed meta makes the accelerator unbuildable

**Status:** OPEN (Lane A — agent-executable) · **Filed:** 2026-08-18
**Blocked by:** — · **Model:** **Opus.** The one-line change is trivial; the
call it forces — committed-byte shape and whether existing indexes migrate —
is not, and it touches the format of record.

## The defect

With `[sources.url] meta = "hashed"` — **the default**, and a law-L5 default —
`fux ingest --refresh-urls` writes the committed index and then fails:

```
error: .fux/index/aa.jsonl:2: the quoted 16-hex token '30aef0c52cf11116' appears
outside `terms` in record 'url:https://example.invalid/handbook/oncall'.
… Refusing to build a divergent accelerator.
# exit 1
```

Every subsequent `fux build` fails identically. **A corpus containing one
hashed URL record can never have an accelerator again.**

## Why

Two decisions, each correct, that were never exercised together:

1. `ingest/run.py:135` writes `record["title_h"] = term_hash(title)` for hashed
   meta — no display text leaks, which is the point of the mode.
2. `derive/build.py::_assert_invariants` refuses to build when a quoted 16-hex
   token appears outside `terms`, because `query/scan.py` derives `df` from raw
   bytes and would count it as a term while the accelerator would not.

`term_hash` returns exactly 16 hex characters, so `title_h` **always** trips it.

**Confirmed by contrast** — same corpus, same commands, one config key:

| `meta` | `ingest --refresh-urls` | accelerator | `ask` title |
|---|---|---|---|
| `"plain"` | exit 0 | builds (70 terms) | `Oncall handbook` |
| `"hashed"` *(default)* | **exit 1** | **never builds** | `30aef0c52cf11116` |

## Why it matters

Hashed meta is the default for non-git sources, and URLs are the only non-git
source that ships — so the **default** URL path yields a corpus permanently
stuck on the reference scan. On the RFC corpus that is a warm p95 of
**4 248.8 ms instead of 27.2 ms**: the whole M2 result, forfeited by using a
documented default. It also looks fine from the outside, because the index is
written and `ask` still answers.

Not caught because ADR-URL-INGEST shipped in 0.31.x and the invariant in
0.32.0; each has tests, neither ingests a hashed record *and* builds.

## Definition of done

1. **Make `title_h` not look like a term** rather than teaching the invariant
   about exceptions — e.g. `"h:" + term_hash(...)`. `scan.py`'s raw-byte regex
   then stops matching it and the two paths agree *by construction*. Exempting
   the field by key name would weaken a check whose entire value is that it
   admits nothing.
2. Strip the prefix in the two display-fallback readers: `query/rank.py:90`
   and `derive/build.py:143`.
3. **Decide the migration** — any committed index already holding a bare
   `title_h` must be re-ingested. Whether that warrants an `analyzer` or
   `_format` bump is the judgement call this item is Opus-sized for.
4. **Tests:** ingest a hashed URL record and build, asserting exit 0 and a
   manifest; assert `scan` and `accelerator` return identical scores on a
   corpus containing one. The differential harness has never seen a hashed
   record.
5. `CHANGELOG.md` under `[Unreleased] → Fixed`.
6. [ADR-URL-INGEST](../../docs/adr/0008_url-ingest.md) §Consequences and
   [ADR-INDEX-LIFECYCLE](../../docs/adr/0009_index-lifecycle.md) §Consequences:
   replace the known-defect notes with a fixed-in reference.
7. This file and its OPEN-WORK row **deleted**, outcome recorded in
   [`../IMPLEMENTATION.md`](../IMPLEMENTATION.md).

## Hazards

- **Do not relax the invariant.** It is the thing standing between the engine
  and a fast wrong answer. The field shape is the bug, not the check.
- **Do not switch the default to `plain`.** Hashed-by-default closes an
  ACL-mismatch leak (law L5); making URL titles world-readable to dodge a
  format collision trades a correctness bug for a privacy one.

## Evidence

[`../regression/2026-08-18-ingest-and-index/ANALYSIS.md`](../regression/2026-08-18-ingest-and-index/ANALYSIS.md)
— diagnosis, the plain-vs-hashed contrast, and a no-network fixture that
reproduces it in one command.
