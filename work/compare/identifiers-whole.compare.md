---
type: Compare
description: "W-233 — how an identifier is kept whole after analyzer v3. Arpit ruled the shape (F1–F5, 2026-09-28): inspect detects ID families, a committed .fux/identifiers.toml holds them, the analyzer reads only the file. This doc compares the mechanisms against the measured breaks and settles the eight sub-decisions the fixture raised inside that ruling."
item: W-233
---

# Identifiers retained whole — W-233

> **Verdict:** 🟡 **PROPOSED 2026-09-28, inside Arpit's F1–F5 ruling.** **Build
> family matching (e) with a per-family canonical form (d), and nothing else.**
> A template in `.fux/identifiers.toml` (`RF-{n}`) is matched against the
> **text** on both sides, ingest and query. Each match emits one extra term, its
> **canonical form**: the literal lowercased, any dash, space or `_` read as the
> template's separator, and leading zeros dropped from `{n}`. v3's whole form and
> parts stay exactly as they are. **No exact field (c), no stemming change (b),
> no sha-prefix index (f), no global dash fold.** The measured breaks are
> spelling, not scoring. S1–S8 below are the sub-decisions F1–F5 did not reach;
> each is overridable, and none blocks the build.

| | |
|---|---|
| **status** | 🟡 proposed; F1–F5 **ruled** (Arpit, 2026-09-28, Cowork) |
| **the call** | (e) + (d) per family, as S1–S8 specify |
| **confidence** | **high** that it fixes the six measured spelling breaks, which it does by construction; **medium** on cost, which the pre-registered run measures; **low** that the golden ladder can show it. The ladder's questions carry no spelling variants, so the probe is mechanical |
| **reopen-trigger** | **(c)** a case where the query and the document share the canonical term and a shared-parts neighbour still ranks above the document, on any rung; **(f)** a rung or a consumer corpus with ≥ 6 documents citing a 7–40-char hex id by prefix; **the global dash fold** a letter-prefixed ID written with a Unicode dash that no detected family covers, found by the lens on a real corpus |

## Context: what the fixture measured

[The fixture run](../regression/2026-09-28-identifier-fixture/report.md) put 48
document/query pairs through both readers, 14 queries through the real CLI, and
three rungs through the analyzer.
[ANALYSIS](../regression/2026-09-28-identifier-fixture/ANALYSIS.md) has the
diagnosis. In short:

| # | break | today | measured |
|---|---|---|---|
| B1 | `RF 118` · `RF–118` (any Unicode dash) · `RF_118` vs `RF-118` | parts only | exact doc ranks **2nd**, below `RF-119` |
| B2 | `rf118` vs `RF-118`, and `RF118` vs `RF-118` | **nothing** | no result |
| B3 | `ADR-4` · `ADR 4` vs `ADR-0004` | parts only | exact doc ranks **2nd**, below `ADR-0040` |
| B4 | `RF-118` inside `…/wiki/RF-118?rev=2`; `bm25f.py` inside a path | parts only | — |
| B5 | `2.3.1` vs `v2.3.1` | **nothing** | no result |
| B6 | a 7–8-char sha prefix | **nothing** | no result |
| — | stemming the whole form | **no break**: 0 of 7 862 whole terms stemmed | `should_stem` skips non-`isalpha` |
| — | an exact whole-form query | **no break** | rank **1**, 7 of 7 |

## The candidates against the breaks

| candidate | B1 | B2 | B3 | B4 | B5 | B6 | index cost | verdict |
|---|---|---|---|---|---|---|---|---|
| **(a)** v3 as shipped | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | +4.6 % bytes (paid) | ✅ stays |
| **(a′)** whole form only when it has a digit | — | — | — | — | — | — | −40 870 postings at rung-10000 (≈ −4.2 %), 289 terms | ⏸ a cost lever, not a fix. Not in scope |
| **(b)** whole form unstemmed | — | — | — | — | — | — | 0 | ✅ **already true** (S7 pins it with a test) |
| **(c)** a separate exact field | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | a new field, `_format` bump | ❌ fixes no measured break. Trigger above |
| **(d)** a query-side normalizer, **global** | ✅ | ⚠ | ❌ | ❌ | ❌ | ❌ | 0 docs; a query-only fold | ❌ alone: `step 4` → `step-4` is wrong, and zeros need a template |
| **(e)** declared/detected families, **with (d) scoped to each family** | ✅ | ✅ | ✅ | ✅ | ⚠ S6 | ❌ | one term per match whose canonical ≠ its v3 whole form | ✅ **the call** |
| **(f)** a prefix lookup for shas / UUIDs | — | — | — | — | — | ✅ | an edge-n-gram plane | ⏸ 0 hex docs on every rung. Trigger above |

## S1 · What a family match emits: the canonical form, beside v3

**One extra term per match: the canonical form, emitted only when v3 did not
already emit that exact string for that exact span.**

- The canonical form is built from the template:
  - literals lowercased;
  - a flexible separator rendered as the template's own character;
  - `{n}` with leading zeros dropped (`0` stays `0`);
  - `{X}` lowercased.
- Examples:
  - `RF-118`, `RF 118`, `rf118`, `RF–118` and `RF_118` all → `rf-118`;
  - `ADR-0004` and `ADR-4` → `adr-4`.
- **Dedup is per span.** A match whose span is exactly one v3 raw token already
  spelled canonically emits nothing more. `RF-118` written plainly costs
  **zero** extra postings. So tf is never double-counted for the common case,
  and the extra cost falls only on documents that wrote a variant.
- **Why beside v3, never instead of it:** every query that works today keeps
  working byte-identically. With an empty file, the analyzer's output is
  unchanged, which is also the rollback.
- **Position:** the canonical term goes immediately **before** the first v3
  term of its span. Both readers order by match start offset. Offsets are
  UTF-16 in Node and code points in Python, and they order identically.

## S2 · The template grammar (F3's templates)

| element | matches | canonical |
|---|---|---|
| a literal letter or digit | itself, **case-insensitive** (ASCII) | lowercased |
| `-` or `_` in a template (a *flexible separator*) | `-`, `_`, U+2010–U+2015, U+2212, one space, or **nothing** at a letter↔digit boundary | the template's own character |
| `.` `/` `:` in a template | exactly itself | itself |
| `{n}` | `[0-9]+` | leading zeros dropped |
| `{X}` | `[A-Za-z]+` | lowercased |

- **Rule: a template must start with a literal letter** (`RF-{n}`,
  `v{n}.{n}.{n}`). This is Q8's finding made structural. Without the rule,
  `{X}-{n}` with a space separator matches `step 4` and `page 12`; with it, the
  43 real families on rung-10000 all qualify and none of the date, decimal or
  path noise does.
- **Boundaries:** a match may not touch a letter or digit on either side
  (`XRF-118` and `RF-1180` do not match `RF-{n}`). It **may** touch `/`, `:`,
  `?`, `#` and `.`, which is what fixes B4.
- **An empty separator only between a letter and a digit.** `rf118` is
  unambiguous; `RFQA` for `RF-QA` is not.
- **No `{hex}` and no `{semver}`.** B6 is deferred (f), and a version is the
  ordinary template `v{n}.{n}.{n}`.

## S3 · Matching runs over the TEXT, not over v3's raw tokens

`_WORD_RE` joins across `/`, so `example.com/wiki/RF-118` is one raw token and
`rf-118` can never be one of its terms. Matching templates against the text
with their own boundaries is what reaches B4. The cost is one compiled
alternation per document at ingest and per query at query time.

## S4 · Where the rules are read, and what keeps ingest = query

- **Both readers read `.fux/identifiers.toml` directly**, at ingest and at
  query. The file's **existence** is mandatory (L12, F1). `fux setup` writes it
  and `doctor --fix` restores it. Empty sections are the ordinary state.
- **The EFFECTIVE rules' digest is stamped into every shard header** as
  `"identifiers"`. It is a digest of the compiled rule list, not of the file
  bytes, so a comment edit moves nothing. This is the ruled proposal's *"the
  file's hash is stamped into the index"*, and three things follow from it.
  - **Carry-forward re-analyses for free.** Ingest's `_reusable` compares the
    old header with the expected one for equality, so a moved digest reuses
    nothing.
  - **CI sees it.** `fux ingest --check` compares only content shas today, and
    a runtime-only digest (the `pii.toml` shape) lives in gitignored
    `runtime/`, which a fresh clone does not have. The header is committed, so
    `ingest --check` and `doctor` compare it with the file and name a stale
    index.
  - **Absent means empty, and that is true of every index built before
    W-233**, because no families existed. The field is written only when
    rules exist. An empty file therefore writes byte-identical shards, and no
    `_format` bump is claimed
    ([SR-INDEX-LIFECYCLE](../../records/0108_index-lifecycle.md) decision 9.1
    is about a property whose absence is ambiguous; this one's is not).
- **The readers do not refuse a digest they cannot check.** `store/reader`
  sees a shard path, not a repo. The comparison belongs to `doctor`,
  `ingest --check` and ingest's own gate. A query run between an edit and the
  next ingest degrades gracefully: its canonical term is not in the index yet,
  and v3's parts still match.
- **`ANALYZER_VERSION` stays `v3`.** The engine's pipeline did not change; a
  repo's families are its own config, and the header now names both.
- **Rules reach the analyzer as a parameter**, never as process state:
  `analyze(text, ids)`. The survey found every leaf's caller holds `root`
  within two frames, and a process-global rule set would leak between repos in
  one process (tests, `serve`, MCP). `correct.normalise` deliberately passes
  **no** rules: a stored correction's key must not move when the families do.

## S5 · The Unicode dash: inside a family only

A global U+2013 → `-` fold looks free and is not. 662 of rung-10000's documents
carry 2 322 en dashes between two digits: ranges (`10–12`), every one. Folding
all of them buys whole-form terms for ranges and **zero** letter-prefixed IDs.
Inside a family (S2), `RF–118` folds and `10–12` does not.

## S6 · What stays unfixed, said out loud

- **B5 `2.3.1` vs `v2.3.1`.** The template `v{n}.{n}.{n}` starts with a literal
  `v`, so a bare `2.3.1` does not match it. Nor can a `[user]` regex bridge it:
  the `v` touches the digit, so the boundary rule refuses the match, and a
  regex's canonical form keeps what it matched. **B5 stays unfixed.** It is
  one fixture row with no population measured on the ladder. Reopen it with a
  `{ver}` placeholder that canonicalizes without its `v` if a corpus shows the
  need.
- **B6 sha / UUID prefixes**: deferred (f).
- **`#1234`, `C++`, `ops@example`**: no family shape; unchanged.

## S7 · The regex guards (F3, `[user]` only)

**Static and deterministic, at load, on both readers.** A rejected pattern is a
hard error naming the construct.

| rejected | why |
|---|---|
| a quantifier on a group, `(…)+` `(…)*` `(…){m,n}` | nested/overlapping quantifiers: catastrophic backtracking |
| an alternation inside a quantified context | the same |
| backreferences `\1` `\k<…>` | not regular; flavour-dependent |
| lookaround `(?=` `(?!` `(?<=` `(?<!` | flavour-dependent (the engine adds its own boundaries) |
| inline flags `(?i)` etc., named groups | flavour-dependent syntax |
| `^` `$` | multiline semantics differ |
| unescaped `.` and `\s` | `.` and `\s` mean different sets in Python and JS |

- **Forced ASCII:** `\d` and `\w` compile under `re.ASCII` in Python and
  already mean ASCII in JS.
- A regex match's canonical form is the match lowercased, with any run of
  dash, `_` or space read as `-`. It gets no zero-stripping, because a regex has
  no `{n}`.
- **Parity:** `fux doctor` runs every `[user]` regex through both readers over
  a deterministic corpus sample and fails on any disagreement (F3).

## S8 · Detection: the lens (F1, F2)

A lens in `fux inspect`, read-only as SR-INSPECT requires.

- **Shape:**
  - every raw token with a digit and a separator becomes a spaCy-style shape
    (`X`, `x`, `d`, punctuation kept);
  - tokens are grouped by **literal letter prefix + shape**;
  - **a segment is kept literal when every member shares it**
    (`NRL-HSE-{n}`, not `NRL-{X}-{n}`).
- **Qualifies when:** ≥ `min_values` distinct values across ≥ `min_docs`
  documents, both in `inspect.toml` (L12). The fixture used 3 and 2; the lens
  ships with those and the pre-registration reports the sensitivity.
- **`fux identifiers`** prints the detected families and the diff against the
  file. **`fux identifiers --write`** rewrites only the `[detected]` section,
  sorted, with each family's value and document counts as a trailing comment.
  `[user]` is preserved byte for byte.
- **`doctor`**: *"N new families since the last write"* (F2).

## Test data (W-233 DoD 4)

- **Measurable now:** the query-side breaks B1–B3 on the ladder's own 43
  letter-prefixed families. The variant queries are generated mechanically
  (`BWD 116`, `bwd116`, `BWD–116`, zero variants), and the target is the
  document holding the id. This is W-205's `identifier_probe.py` method; it
  needs no golden answer.
- **Not on the ladder, named for the next generation (SR-WORK-TESTDATA):**
  - an ID written with a Unicode dash in the document;
  - an ID inside a URL or a path;
  - a colon-prefixed id (`JIRA:PROJ-1`);
  - a `#nnn` reference;
  - a hex id cited by prefix.

## References

- Elasticsearch [`word_delimiter_graph`](https://www.elastic.co/guide/en/elasticsearch/reference/current/analysis-word-delimiter-graph-tokenfilter.html):
  `preserve_original` (whole + parts, which is v3) and `protected_words` (a
  user list kept whole, which is `[user]`).
- Elasticsearch [`pattern_capture`](https://www.elastic.co/guide/en/elasticsearch/reference/current/analysis-pattern-capture-tokenfilter.html):
  regex-declared tokens emitted beside the original, which is S1's shape.
- Elasticsearch [multi-fields](https://www.elastic.co/guide/en/elasticsearch/reference/current/multi-fields.html):
  the `keyword` sub-field, which is (c).
- spaCy [`Token.shape_`](https://spacy.io/api/token#attributes): the
  deterministic shape feature S8 groups by.
- Russ Cox, [*Regular Expression Matching Can Be Simple And Fast*](https://swtch.com/~rsc/regexp/regexp1.html):
  why a backtracking engine needs S7's static guard. Python `re` and V8
  `irregexp` both backtrack.
- [OWASP, ReDoS](https://owasp.org/www-community/attacks/Regular_expression_Denial_of_Service_-_ReDoS):
  nested and overlapping quantifiers as the dangerous class.
