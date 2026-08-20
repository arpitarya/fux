# W-58 — a committed record carries no ingest time, so no age bound can be honoured

**Status:** OPEN · **human** (Arpit) — **the compare doc is written and awaits
a verdict**: [`record-freshness.compare.md`](../compare/record-freshness.compare.md),
2026-08-20. Proposed **D — no age bound**; `max_age_seconds` is struck and
content verification is the answer. **A and C turned out to be the same
option** (the reproducible-builds convention for a deterministic stamp in a git
repo *is* the commit date), and a fifth — **E, one corpus-level stamp** — is
the shape to build if an age is ever wanted. · **Filed:** 2026-08-20
**Blocked by:** — · **unblocks** an age-based freshness mode, if one is wanted
**Model:** **Opus** — it changes ADR-RECORD and carries a determinism question.
**Research the field before proposing**: how other content-addressed and
document-index systems bound staleness without a wall-clock, and whether any
bound is wanted at all once content verification exists. **`mtime` is the
trap** — it does not survive a clone, so the intuitive option is the broken
one, and the compare doc must say why rather than omit it.

## The finding

A committed record's fields are:

```
id · src · loc · sha · ver · mode · meta · title · phrases · terms · wlen · edges
```

**None of them is temporal.** `ver` is a monotonic revision counter — it goes
up when the content sha changes — and says nothing about *when*.

`.fux/runtime/stamp.json` holds filesystem mtimes, but it is derived and is
**explicitly excluded** from `DETERMINISTIC_FILES` precisely because mtimes are
not reproducible. Using it to answer a query would make the same query at the
same commit answer differently on two machines.

## Why it matters

[`../proposals/caller-set-freshness-policy.md`](../proposals/caller-set-freshness-policy.md)
specified the refer plane's policy as `{max_age_seconds, timeout_seconds}`,
with age measured "against the ledger's recorded `sha@index` provenance, not
wall clock at query time".

**That provenance does not exist**, so the knob was not built.
[ADR-REFER](../../docs/adr/0031_refer-plane.md) decision 4 records the refusal
and the reasoning: shipping `max_age_seconds` would mean shipping a knob that
silently does nothing, and a caller passing `max_age_seconds=60` would
reasonably believe they had bounded their staleness. **A knob that lies is
worse than a missing knob**, because the caller cannot see it failing.

What shipped instead is a mode (`never` | `always`) plus content verification —
comparing the fetched sha against the recorded one, which answers *"is the
index still right"* **exactly** where an age only ever approximated it.

## The fork

**The honest first question is whether an age bound is wanted at all**, now
that content verification exists and is strictly more precise. If the answer is
no, this item closes by striking the knob from the proposal and archiving it —
that is a legitimate outcome and probably the cheapest one.

If it *is* wanted, the options are:

| option | shape | cost |
|---|---|---|
| **A — a `SOURCE_DATE_EPOCH`-derived stamp per record** | one field, deterministic by construction | changes ADR-RECORD and `_format`; the stamp is *build* time, not *source* time, which may not be the age anyone means |
| **B — the source's own mtime, floored to a coarse unit** | closer to what a reader means by "how old is this" | mtime is not reproducible across clones — a fresh `git clone` resets every one, so the age would reset with it |
| **C — the git commit date of the file** | genuinely meaningful and genuinely reproducible | requires reading git history at ingest, which the git-dir walker deliberately does not do (it reads bytes, not objects) |
| **D — no age, ever; content verification is the answer** | free | `max_age` never exists; the proposal's row for "an agent mid-loop wants generous max_age" is served by `never` instead |

**No recommendation.** Option B's flaw is worth flagging loudly because it is
the intuitive choice and it is the broken one: **mtimes do not survive a
clone**, so a CI checkout would consider the entire corpus freshly written.

## Definition of done

- [ ] Arpit decides whether an age bound is wanted at all.
- [ ] If yes: a compare doc, then a verdict, then an amendment to
      [ADR-RECORD](../../docs/adr/0010_index-record.md) and a `_format` bump.
- [ ] If no: strike `max_age_seconds` from
      [`../proposals/caller-set-freshness-policy.md`](../proposals/caller-set-freshness-policy.md)
      — or from its archived successor — and record the closure in
      [ADR-REFER](../../docs/adr/0031_refer-plane.md), whose veto condition 3
      is exactly this.

## Hazard

**Do not add a wall-clock timestamp at ingest.** It is the obvious
implementation and it breaks L3 outright: the same sources would produce a
different index every run, and the byte-identity guarantee is the property the
whole architecture rests on.

## Evidence

The record's field set, read from this repo's own committed index:

```bash
uv run python -c "
import json, pathlib
line = next(l for l in sorted(pathlib.Path('.fux/index').glob('*.jsonl'))[0].read_text().splitlines() if '\"_format\"' not in l)
print(sorted(json.loads(line)))"
```

Found while building the refer plane's freshness module for
[W-24](W-24-m4-refer-plane.md).
