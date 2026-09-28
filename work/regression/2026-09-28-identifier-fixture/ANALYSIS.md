---
type: Analysis
description: "What the W-233 fixture says to build, and what it says not to: query-side spelling folds per family and a matcher that finds IDs inside paths and URLs, yes; a separate exact field, a stemming change and a sha prefix index, no — each with the evidence and a repro."
run: 2026-09-28-identifier-fixture
item: W-233
---

# Analysis: the breaks are spelling, not scoring

The design these findings feed is argued in
[`work/compare/identifiers-whole.compare.md`](../../compare/identifiers-whole.compare.md).
This file states the diagnosis and nothing else.

**Repro for every line below:**

```bash
.venv/bin/python tools/quality-controls/identifier_fixture.py --rung rung-10000 --out /tmp/w233
```

## 1 · Not a break: stemming the whole form (Q1). Family (b) is already true.

- `stem.should_stem` returns false for anything that is not `isalpha()`, so a
  whole form with a digit or a separator is never stemmed.
- **0 of 7 862** whole-form terms at rung-10000 differ from their stem.
- **What this means for F4.** Arpit ruled *"whole unstemmed + parts"*.
  Under v3 that already holds for every whole form the analyzer emits. It
  becomes an obligation again only for the **new** whole forms W-233 adds (a
  folded `rf-118` from `RF 118`), and those contain a separator, so the same
  guard covers them. **No stemming change is needed. A test that pins it is.**

## 2 · Not a break: an exact query's rank (Q7). Family (c) has nothing to fix.

- Every query that reaches the whole form ranks its document first: **7 of 7**.
- The 2026-09-21 run found the same on the ladder: `RF-117/119/120`,
  `PROJ-123/124/125` and `TSL-RF-119-A/120-A` ranked first in both arms.
- **A separate exact field stays deferred.** Its reopen-trigger is a case
  where the whole form is shared and a parts-neighbour still ranks above it.
  Neither run produced one.

## 3 · THE break: spelling variants miss the whole form (Q2, Q3, Q4)

| the query writes | the document writes | today | Q7 rank |
|---|---|---|---|
| `RF 118` | `RF-118` | parts only | 🔴 2, below `RF-119` |
| `RF–118` (U+2013, and U+2010, U+2012, U+2014, U+2212) | `RF-118` | parts only | 🔴 2 |
| `rf118` | `RF-118` | **nothing** | 🔴 — |
| `RF-118` | `RF118` | **nothing** | — |
| `RF_118` | `RF-118` | parts only (`rf_118` ≠ `rf-118`) | — |
| `ADR-4` · `ADR 4` | `ADR-0004` | parts only | 🔴 2, below `ADR-0040` |
| `2.3.1` | `v2.3.1` | **nothing** (single-char parts dropped) | 🔴 — |

**The specific changes this points to** (the mechanism and where each fold is
allowed are the compare doc's):

1. **A Unicode dash is a hyphen, but only inside a family.** Mapping U+2010–U+2015
   and U+2212 to `-` everywhere looks free, and it is not.
   - **662 of the 10 000 rung documents** carry an en dash between two
     alphanumerics (2 322 occurrences), and every one is digit–digit: numeric
     ranges like `10–12`.
   - A global fold would give each range a whole term (`10-12`). That is the
     same hyphenated-prose cost v3 already pays for ASCII, extended to a new
     population, for 0 letter-prefixed IDs on the ladder.
   - **So the fold belongs to the family matcher.** `RF–118` folds because
     `RF-{n}` matches it with the dash class; `10–12` has no family.
2. **Space, no separator and `_`-for-`-` fold only inside a known family.**
   `RF 118` → `rf-118` is right. `step 4` → `step-4` is wrong. Only a declared
   or detected template (`RF-{n}`) can tell them apart, which is why F1–F5 put
   the families in a committed file.
3. **Leading zeros fold only per template.** `ADR-{n:4}` says the canonical
   form is 4-wide, so `ADR-4` → `adr-0004`. Without the template, `DOCK-03` and
   `DOCK-3` are not known to be one id.
4. **A version's bare number.** `v{semver}` also emits `2.3.1` for `v2.3.1`.

## 4 · A break the proposal did not name: IDs inside paths and URLs (Q6)

- `https://example.com/wiki/RF-118?rev=2` yields the raw token
  `example.com/wiki/RF-118`, because `_WORD_RE` joins across `/`. `rf-118` is
  never a term, so a `RF-118` query reaches only the parts.
- `bm25f.py` and `query/bm25f.py` reach only the parts of
  `src/fux/query/bm25f.py`.
- **So the family matcher must scan the TEXT, not the analyzer's raw tokens.**
  A template match inside a longer token emits the matched span's whole form
  as well.

## 5 · Deferred: sha / UUID prefixes (Q5)

- A 7- or 8-char sha prefix reaches nothing. There is no prefix lookup.
- **The ladder has 0 documents with a 7–40-char hex id**, so a prefix index
  would be built for a population no rung carries.
- **Deferred**, with the reopen-trigger in the compare doc.

## 6 · A design input for the lens: families need a literal letter prefix (Q8)

- At rung-10000, the four largest "families" by shape alone are noise: dates
  (2 264 values), decimals (1 407), link paths (991) and `400/hour` (377).
- Requiring a **literal letter prefix** leaves **43 of 53** qualifying
  families (n ≥ 3 values, m ≥ 2 documents). Every one is a real ID family:
  `BWD-{n}`, `WIKI-BWD-{n}`, `NRL-HSE-{n}`.
- `v{semver}` is the exception with no letter prefix beyond `v`, so it is a
  built-in template, not a detected one.

## 7 · Test data: what the ladder does NOT carry (DoD 4)

| shape | documents on the ladder (every rung) |
|---|---:|
| Unicode-dash id (letters, dash, digits) | **0** |
| any Unicode dash between alphanumerics | 662, all digit–digit ranges |
| `PROJ:ID-n` prefix | **0** |
| `#nnn` reference | **0** |
| 7–40-char hex id | **0** |
| zero-padded id | 35 (the seed) |

**Only the query side can be measured on the frozen ladder.** Spelling
variants of the ladder's own 43 letter-prefixed families (`BWD 116`,
`bwd116`, `BWD–116`) can be generated mechanically, and their target is the
document holding the id. That needs no golden answer: it is W-205's
`identifier_probe.py` method. **The document-side shapes (a Unicode dash, `#`,
hex, a colon prefix) are named for the next generation** and are not faked
here.
