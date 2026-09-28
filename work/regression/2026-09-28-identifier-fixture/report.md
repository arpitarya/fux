---
type: Regression Run
name: identifier-fixture
description: "W-233 DoD 1 — where an identifier still breaks after analyzer v3. The whole form is never stemmed (0 of 7 862 whole terms at rung-10000) and an exact query ranks its own document first 7 of 7 times. What still breaks is SPELLING: a space, a Unicode dash, a missing separator or a dropped leading zero puts a shared-parts neighbour above the exact document, and rf118, 2.3.1 and a 7-char sha reach nothing at all. An ID inside a path or a URL has no whole form of its own. Python and Node agree on all 48 cases."
run: 2026-09-28-identifier-fixture
item: W-233
classification: informed
status: complete
timestamp: 2026-09-28T00:00:00Z
---

# Where an identifier still breaks after analyzer v3

**A precondition fixture, not an arm.** It uses one engine (`b8afb5bf`) and
makes no comparison and no bar. It is **not a paired run**, so
[SR-RS](../../../records/0133_predictions.md) decision 22's disclosure
does not apply.

**Reproduce:**

```bash
.venv/bin/python tools/quality-controls/identifier_fixture.py \
    --rung rung-10000 --out work/regression/2026-09-28-identifier-fixture/evidence
```

The script has three parts:

- **Q1–Q6** run 48 document/query pairs through `analyze` on both readers,
  Python in process and `node/src/query/analyzer.mjs` via `node`.
- **Q7** ingests a 29-document scratch corpus with the real CLI and reads
  `fux ask --json`. The corpus is deleted on exit.
- **Q8** analyzes a frozen rung's text read-only. It has no ingest and no arm.

**The unit is a case, not a query.** The files are
[`evidence/per-case-rows.jsonl`](evidence/per-case-rows.jsonl) (48 rows) and
[`evidence/ranking-rows.jsonl`](evidence/ranking-rows.jsonl) (14 rows). Every
count below derives from them and from
[`evidence/summary.json`](evidence/summary.json).

**Outcome of a case:**

- `WHOLE`: the identifier's own lowercased spelling is a term on both sides.
- `PARTS`: only other terms overlap.
- `NONE`: nothing overlaps.

---

## Q1–Q6 · what the analyzer does (both readers)

| q | what | cases | WHOLE | PARTS | NONE | Python ≠ Node |
|---|---|---:|---:|---:|---:|---:|
| Q1 | stemming the whole form | 8 | 7 | 1 | 0 | 0 |
| Q2 | query/document spelling mismatch | 11 | 2 | 7 | 2 | 0 |
| Q3 | leading zeros | 5 | 1 | 4 | 0 | 0 |
| Q4 | separators v3 does not cover | 12 | 3 | 8 | 1 | 0 |
| Q5 | long opaque IDs | 6 | 4 | 0 | 2 | 0 |
| Q6 | paths and URLs | 6 | 2 | 4 | 0 | 0 |

- **Q1: no break.** `stem.should_stem` stems only `isalpha()` tokens, so a
  whole form carrying `-`, `.`, `/`, `_` or a digit is never stemmed.
  `PROJ-ALPHA-releases` is indexed as itself. The one `PARTS` row is the query
  `PROJ-ALPHA-release`, a different identifier, and `PARTS` is the right
  outcome for it. **Family (b), "whole unstemmed", is already true of v3's
  whole form.** Only the parts are stemmed (`DAIRY-2` → `dairy-2` whole, plus
  the part `dairi`).
- **Q2: the real break.** These queries all fail to reach the whole form
  `rf-118`:
  - `RF 118`, and the en dash, em dash, U+2010 hyphen and minus sign reach the
    parts only;
  - `RF_118` reaches `rf_118`, which is a different term;
  - `rf118` → `NONE`;
  - a document writing `RF118`, queried as `RF-118` → `NONE`.
- **Q3: leading zeros break it.** `ADR-4` vs `ADR-0004` and `DOCK-3` vs
  `DOCK-03` reach the parts only, in both directions.
- **Q4: mixed.**
  - `JIRA:PROJ-1` keeps `proj-1` whole (the `:` ends the token), so a `PROJ-1`
    query is `WHOLE`.
  - `#1234`, `C++`, `ops@example`, `~/.fux`, `run(fast)` and `v2.3.1+build.5`
    have no whole form.
  - `2.3.1` against `v2.3.1` → **`NONE`**: the parts `2`, `3`, `1` are single
    characters and are dropped.
- **Q5.** A full sha and a UUID are whole on both sides; the UUID's case folds
  and its first segment is also a part. **A 7- or 8-character sha prefix →
  `NONE`**: there is no prefix lookup.
- **Q6.** A path is whole as written, and its file-name stem (`bm25f`) is a
  part. But `bm25f.py` and `query/bm25f.py` reach parts only. **An ID inside a
  URL has no whole form of its own:** `https://example.com/wiki/RF-118?rev=2`
  yields the raw token `example.com/wiki/RF-118`, so `rf-118` is never a term.

## Q7 · ranking: does the exact document win?

The corpus is 9 targets and neighbours plus 20 filler documents. Each
neighbour shares the target's parts (`RF-119` with `118` twice as a quantity;
`ADR-0040` with `ADR 4` and `step 4 of 4`; `v2.3.0` with `3.1`; `bm25.py`).

| query | target rank | first |
|---|---:|---|
| `RF-118` · `what is RF-118` | **1** · **1** | target |
| `RF 118` · `RF–118` | 🔴 **2** · **2** | `rf-119.md` |
| `rf118` | 🔴 **—** | nothing |
| `ADR-0004` | **1** | target |
| `ADR-4` · `ADR 4` | 🔴 **2** · **2** | `adr-0040.md` |
| `v2.3.1` | **1** | target |
| `2.3.1` | 🔴 **—** | nothing |
| full sha | **1** | target |
| `d3139fdb` (8-char prefix) | 🔴 **—** | nothing |
| `bm25f.py` · `src/fux/query/bm25f.py` | **1** · **1** | target |

**Every query that reaches the whole form ranks its document first (7 of 7).
Every one that does not either loses to the shared-parts neighbour (4) or finds
nothing (3).** This agrees with the
[2026-09-21 run](../2026-09-21-identifier-analyzer/report.md), where the exact
sibling IDs ranked first in both arms: **a separate exact field (family c) has
no break to fix here.** The failures are spelling, not scoring.

## Q8 · cost and the population, three rungs

| rung | docs | postings | whole-form distinct / postings | digit-free whole postings | families (n≥3, m≥2) · with a letter prefix |
|---|---:|---:|---|---:|---|
| rung-00100 | 100 | 19 473 | 745 / 1 472 | 707 | — · 12 |
| rung-01000 | 1 000 | 106 362 | 2 068 / 6 932 | 4 362 | — · 43 |
| **rung-10000** | **10 000** | **975 188** | **7 862 / 61 554** (6.3 %) | **40 870** | **53 · 43** |

Only rung-10000 is filed under `evidence/`. The two smaller rungs were run
with the same command into scratch, and their numbers are copied from its
output.

At rung-10000:

- **Stemming alters no whole form: 0 of 7 862 distinct.**
- **Digit-free whole forms are 289 distinct terms but 40 870 postings** (66 %
  of whole-form postings: `after-hours`, `alarm_label`, `a-to-z`). Candidate
  (a′) would shed about 4.2 % of all postings and almost no dictionary.
- **The population the Q2/Q4/Q5 breaks need is ABSENT on the ladder.** Every
  rung has 0 documents with a Unicode-dash ID (letters, dash, digits), a
  `PROJ:ID-n` prefix, a `#nnn` reference or a 7–40-char hex id.
- ⚠ **But 662 documents carry an en dash between two digits** (2 322 numeric
  ranges, `10–12`). That is the population a global dash fold would touch
  instead. **Only 35 documents carry a zero-padded ID**,
  the same 35 on every rung, so they come from the seed.
- **Shape families are mostly noise without a letter prefix.** The largest
  "families" are dates (`d-d-d`, 2 264 values), decimals (`d.d`, 1 407), link
  paths (`ext/…/d-x-x.x`, 991) and `400/hour`. **Requiring a literal letter
  prefix leaves 43 of 53**: `WIKI-BWD-{n}`, `BWD-{n}`, `ZAC-{n}`,
  `NRL-HSE-{n}` and so on.

⚠ **Q8 analyzes the whole file text, frontmatter included**, where ingest
fields it. The totals are an estimate of the analyzer's reach, not the index's
posting count. The 2026-09-21 run carries the ingested totals.

## Authorship

| what | who |
|---|---|
| the ladder rungs and their identifiers | **Codex** and **Claude** (gen 3, per rung README) |
| the 48 cases, the Q7 corpus, this instrument | this session |
| golden questions or answers | **none read, none needed** |

**`informed`.** The instrument's author wrote the cases and reads the results,
and the tree has been unlocked since 2026-09-21 (L11). Every number here is a
count or a rank on authored fixtures, and none is a quality claim.
