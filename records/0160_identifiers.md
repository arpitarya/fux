---
type: Standing Record
kind: component
name: SR-IDENTIFIERS
title: SR-IDENTIFIERS (0160) — identifier families are kept whole however they are typed
description: "A committed .fux/identifiers.toml names ID families (RF-{n}); both readers match them against the text at ingest and at query time and add one canonical term per match beside analyzer v3's output, so RF 118, rf118, RF–118 and RF-0118 are the term rf-118. [user] is hand-written and wins; [detected] is written only by `fux identifiers --write` from an inspect lens. The effective rules' digest is stamped into every shard header."
status: accepted
date: 2026-09-28
feature: "identifier families — `.fux/identifiers.toml`, its matcher on both readers, the lens, `fux identifiers`, the doctor rows and the serve Identifiers tab"
owns: [.fux/identifiers.toml@b595944e4c27, node/src/query/identifiers.mjs@d9fcbed75730, node/test/identifiers.test.mjs@69bcab39922f, src/fux/identifiers_cmd.py@76f2087bb2bb, src/fux/query/identifiers.py@a1dad759d69f]
laws: [L2, L4, L10, L12]
timestamp: 2026-09-28T00:00:00Z
content_sha: 3cadd4b97f4f7b8aefb27561bc03648e0744459356f979fba90c7ab5e72ddcae
ratifies: "W-233 — Arpit, 2026-09-28 (Cowork), F1–F5: a verb writes [detected]; refresh on demand with a doctor warning; templates by default and a guarded regex in [user] only; the whole form unstemmed plus its parts; [detected] applies once written and [user] overrides it"
---

<!-- COMPONENTS-START — GENERATED from records/README.md's OWNERSHIP and DESCRIBES tables by scripts/gen-components.py. Do not edit by hand: change the table, then run `python scripts/gen-components.py --write`. -->

**Owns** — the components this record decides:

- `.fux/identifiers.toml` · file
- `node/src/query/identifiers.mjs` · file
- `node/test/identifiers.test.mjs` · file
- `src/fux/identifiers_cmd.py` · file
- `src/fux/query/identifiers.py` · file

<!-- COMPONENTS-END -->

# SR-IDENTIFIERS — identifier families are kept whole however they are typed

## §1 — For humans

**Analyzer v3 keeps `RF-118` whole only when it is written `RF-118`.** The
[fixture run](../work/regression/2026-09-28-identifier-fixture/report.md)
measured what that leaves:

- `RF 118`, `RF–118` and `ADR-4` (for `ADR-0004`) reach only the parts, and the
  exact document ranks **second**, below a neighbour that merely shares them;
- `rf118` reaches nothing.

**Nothing was wrong with scoring.** Every query that reached the whole form
ranked its document first. **The break is spelling.**

A **family** is a template such as `RF-{n}`, written in `.fux/identifiers.toml`.
Both readers look for it in the text, in a document at ingest and in a question
at query time. Every match adds **one** term, its canonical form (`rf-118`),
beside everything v3 already emits. So the five spellings above become one
term, and the document that names the ID outranks the one that only shares its
parts. **An empty file changes nothing, byte for byte**, and that is also the
rollback.

**Who writes the file:**

- **You**, in `[user]`, which always wins.
- **fux**, in `[detected]`, but only when you run `fux identifiers --write`.
  The lens behind it finds letter-prefixed shapes that repeat across documents.
- **Experts** may write a regex in `[user]`. It is checked when loaded, and a
  construct that could loop, or that Python and Node read differently, is
  refused by name.

`fux serve`'s **Identifiers** tab tests a pattern before you commit it.

## §2 — For agents

### Context

- **The measurement:**
  [fixture](../work/regression/2026-09-28-identifier-fixture/report.md) and
  [ANALYSIS](../work/regression/2026-09-28-identifier-fixture/ANALYSIS.md).
- **The design and its alternatives:**
  [compare doc](../work/compare/identifiers-whole.compare.md) S1–S8.
- **The forks:** Arpit's F1–F5, in
  [W-233](../archive/open/W-233-identifiers-retained-whole.md).
- **The shared analyzer:** stated in [SR-RANKING](0111_ranking.md) decision 9.
  This record adds an input to it and changes none of its steps.

### Decision

1. **The file.** `.fux/identifiers.toml` (`constants.toml [files] identifiers`)
   has two tables:
   - `[user]` holds `keep`, `drop` and `regex`;
   - `[detected]` holds `families`.

   **Its existence is required (L12).** `fux setup` writes it and
   `fux doctor --fix` restores it. **An empty or absent table is the ordinary
   state and never an error**, so a `[user]`-only file is valid (F1). Unknown
   tables and keys are refused.
2. **Precedence.** The effective rules are `(detected − drop) ∪ keep`, with
   templates sorted by code point, then `regex` in file order. `drop` beats
   both. A `drop` entry must itself parse. The engine never writes `[user]`.
3. **Templates are the default and the only form `[detected]` holds** (F3).
   The grammar:
   - letters and digits are literal, matched case-insensitively;
   - `-` and `_` are flexible, accepting `-`, `_`, U+2010–U+2015, U+2212 and one
     space (`constants.toml [identifiers] flexible_separators`), or nothing
     where a letter meets a digit;
   - `.` `/` `:` match themselves;
   - `{n}` is a digit run, and `{X}` is a letter run.

   **A template must start with a literal letter**, because without that
   `{X}-{n}` matches `step 4`. A placeholder may not directly follow a
   same-kind element.
4. **What a match emits: ONE canonical term, beside v3, never instead of it.**
   - The canonical form: the template's literals lowercased, its own
     separator, `{n}` without leading zeros, `{X}` lowercased.
   - It is placed immediately before the first v3 raw token starting at or
     after the match, or last when there is none.
   - It adds nothing when v3 already emitted that term for that span, so
     `RF-118` written plainly costs zero postings.
   - It is never stopworded and never stemmed (F4).

   The whole form v3 emits for a separator-bearing token was already unstemmed
   (`stem.should_stem`: letters only), and the fixture measured 0 of 7 862
   changed.
5. **Matching runs over the TEXT, not v3's tokens.**
   - That is what reaches `…/wiki/RF-118?rev=2`.
   - A match may not touch a letter, a digit or a flexible separator on either
     side, nor a `.` that continues into an alphanumeric.
   - So `XRF-118`, `RF-1180` and `TSL-RF-119-A` do not match `RF-{n}`.
6. **A `[user]` regex, for experts only, behind a STATIC guard** (F3). It is
   checked at load on both readers, with no timeout (L4).
   - **Refused:** any `(?` except `(?:`, a quantifier on a group, a stacked or
     possessive quantifier, `^`/`$`, an unescaped `.`, `\s`, any escape
     outside `\d \w \b \t \n \r \xhh \uhhhh` and escaped punctuation, set
     operations or a nested `[` in a class, and a pattern that matches the
     empty string.
   - **Rewritten:** `\d` → `[0-9]`, `\w` → `[A-Za-z0-9_]`, and a capture
     group → `(?:…)`.
   - **The canonical form** of a regex match is the match lowercased, with
     every run of flexible separators read as `-`.
7. **The rules reach the analyzer as a parameter, never as process state.**
   - `analyze(text, ids)`, `tokenize(text, ids)` and
     `query_term_hashes(query, ids)` take them.
   - Ingest loads them once. Every query path that matches against the index
     takes them from `identifiers.for_root(root)`, a cache keyed by the file's
     stat: scan, accelerator, `run_query` and its expansion, the band guard,
     confidence, `find --all`, related, provenance, and the Node twins.
   - **Deliberately without families:**
     - `correct.normalise`, because a stored correction's key must not move
       when the families do;
     - `mined`;
     - the passes that analyze a question and fetched text in one function
       (rerank, refer's rescore, headings, `find --phrase`), which are
       self-consistent on v3's terms.
8. **The effective rules' digest is stamped into every shard header** as
   `identifiers` (`store.header_for`), only when rules exist.
   - **Absent means no families**, which is true of every index built before
     this record, so `_format` does not move.
   - Ingest's reuse gate compares the whole expected header, so a moved digest
     re-analyses every document. A moved digest also re-derives carried `url:`
     records.
   - `fux ingest --check` and `fux doctor` compare the header with the file.
     The digest is committed, so a fresh clone in CI can see a stale index.
   - Two branches built under different families conflict on `<header>` in the
     merge driver, and a re-ingest resolves it.
   - The readers ignore the field: they see a shard, not a repo.
9. **Detection is an inspect lens and nothing else writes `[detected]`**
   (F1, F2).
   - The lens: [`inspect/idfamilies.py`](../src/fux/inspect/idfamilies.py),
     decided by [SR-INSPECT](0156_inspect.md).
   - `fux identifiers` prints the families and their diff against the file.
   - `--write` replaces only the `[detected]` table, byte-preserving
     everything else, and refuses to write a file it would not load.
   - **Detection never runs inside `fux ingest`**, because one new document
     must not change the analysis of every other.
   - `[detected]` applies as soon as it is written, and `[user]` overrides it
     (F5).
10. **Four `fux doctor` rows**, registered in [SR-DOCTOR](0152_doctor.md):
    - `identifiers.toml loads` (error);
    - `identifier families indexed` (error: the header against the file);
    - `identifier families current` (warn: new or gone families, F2);
    - `identifier regex parity` (only with a `[user]` regex): Python `re` and
      V8 run the same compiled source over the first
      `inspect.toml [identifiers] parity_sample` documents, and any difference
      in spans is a FAIL.
11. **`fux serve` has an Identifiers tab** ([SR-SERVE](0158_serve.md)). It is a
    read-only test bench that shows for a typed pattern:
    - its matches;
    - each match's canonical term and its terms with and without the family;
    - the Python/V8 parity;
    - a refusal with its reason;
    - the line to paste;
    - the detected families.
12. **Not built, each with the condition that reopens it** (compare doc
    verdict block):
    - a separate exact field;
    - a sha/UUID prefix index;
    - a global Unicode-dash fold (662 rung documents carry it only in numeric
      ranges);
    - a bare `2.3.1` for `v2.3.1`.

### Consequences

- **Measured, and it shipped on the frozen table.** The
  [pre-registered run](../work/regression/2026-09-28-identifier-families/VERDICT.md)
  is a PASS:
  - a variant-spelled ID query reaches its own document at rank 1 by net +25 /
    +88 / +105 with 0 broken on rung-00100 / 01000 / 10000;
  - the exact spelling is unchanged at 100 %, and 0 of 60 prose questions
    moved;
  - the committed index grows +0.3 % at rung-10000.

  ⚠ It is a mechanism result on the ladder's own IDs, not a measure of how
  often real questions are spelled that way
  ([ANALYSIS](../work/regression/2026-09-28-identifier-families/ANALYSIS.md)).
- **An empty file is a rollback.** G3 of the pre-registered run checks it byte
  for byte against the engine before this record.
- **A consumer opts in by running one verb.** Nothing changes behind their
  back, and an ingest reports the re-analysis as ordinary work.
- **The file is one more mandatory config file** (L12), so a repo from before
  it needs `fux doctor --fix` or `fux setup` once.

### Alternatives considered

The rejected mechanisms (the exact field, a global fold, the prefix index, and
restricting the whole form to digits) and the reasons are in the
[compare doc](../work/compare/identifiers-whole.compare.md)'s matrix. Three
further alternatives were weighed:

- **Detection inside `fux ingest`.** Refused by F2: it is deterministic, but
  one added document can re-analyse the corpus.
- **Free regex as the default.** Refused by F3: flavour drift between the two
  readers, and catastrophic backtracking.
- **The digest in `runtime/`, `pii.toml`'s shape.** Rejected, because a fresh
  clone has no `runtime/` and CI could not see a stale index.

### Reference (required)

- Elasticsearch `word_delimiter_graph` `protected_words` and the
  `pattern_capture` filter: a user list kept whole, and matches emitted beside
  the original.
- spaCy `Token.shape_`: the lens's grouping key.
- Russ Cox, *Regular Expression Matching Can Be Simple And Fast* (2007), and
  OWASP ReDoS: why the guard is static.
- All are listed in [BIBLIOGRAPHY](BIBLIOGRAPHY.md) §1.

### Veto condition

**Reopen if** any of these holds:

- the two readers analyze a string differently under the same rules;
- an empty file writes a byte the engine before this record did not;
- a committed index and its `identifiers.toml` disagree without
  `fux ingest --check` saying so.

**How to check it:**

```bash
.venv/bin/python -m pytest -q tests/query/test_identifiers.py tests/ingest/test_delta.py
node --test node/test/identifiers.test.mjs
# expect: passed — the shared fixture, the inertness property, and the header gate
```

---

## References

**Records** — [SR-RANKING](0111_ranking.md) · [SR-INSPECT](0156_inspect.md) ·
[SR-DOCTOR](0152_doctor.md) · [SR-SERVE](0158_serve.md) ·
[SR-INGEST](0106_ingest.md) · [SR-INDEX-LIFECYCLE](0108_index-lifecycle.md)

**Work** — [W-233](../archive/open/W-233-identifiers-retained-whole.md) ·
[compare](../work/compare/identifiers-whole.compare.md) ·
[fixture](../work/regression/2026-09-28-identifier-fixture/report.md) ·
[pre-registration](../work/regression/2026-09-28-identifier-families/PRE-REGISTRATION.md)
