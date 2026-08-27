---
type: OpenItem
id: W-86
title: "W-86 — the decoder plane: one home for bytes-to-Markdown, and a committed queue for what a model must read"
description: "Fux indexes six plain-text extensions. Everything an enterprise actually stores — PDF, decks, spreadsheets, HTML, mail, notebooks, config — is invisible to it. The hardest decoder is already written and lives inside the fetchers, twice. This lifts it into src/fux/decode/, adds the rest in cost order, fixes a live heading defect in four of the six types already allowed, and gives an undecodable file (an image, a scanned PDF) a durable committed place to say a model must read it."
status: open
lane: agent
timestamp: 2026-08-26T00:00:00Z
---

# W-86 — the decoder plane

**Model: Opus for §2, §3, §7 (P5) and every fork in §11 — the contract, the
heading grammar and the PDF decoder are judgement, and a wrong call there is
silent. Sonnet for P0–P4 and P6 once §2 is ratified** — those are mechanical
against a written contract with golden fixtures to verify them.

**Records:** [ADR-TYPES](../../docs/adr/0031_types-list.md) (the allowlist is
what gates entry) · [ADR-INGEST](../../docs/adr/0007_ingest.md) (`parse.py` is
the seam) · [ADR-EXTRACTED](../../docs/adr/0016_extracted-mode.md) (what
extraction may promise) · [ADR-ENRICH](../../docs/adr/0040_enrich.md) (the
queue's consumer) · [ADR-DOTFUX](../../docs/adr/0003_fux-directory.md) (what
`.fux/` holds) · [ADR-FETCHER](../../docs/adr/0019_fetcher.md) +
[ADR-HTTP-FETCHER](../../docs/adr/0021_http-fetcher.md) +
[ADR-CDP-FETCHER](../../docs/adr/0020_cdp-fetcher.md) (the two copies being
lifted). **A new `ADR-DECODE` owns `src/fux/decode/`.**

**Fork doc:** [`index-lock.compare.md`](../compare/index-lock.compare.md) —
the mutex/manifest call, ✅ **accepted 2026-08-26**. P6 is unblocked.

---

## 1 · The finding this item starts from

> ⚠ **CORRECTED DURING THE P1 BUILD (2026-08-26): there were FOUR copies, not
> two.** The two below, plus **both wheel templates** —
> `src/fux/templates/http.py.txt` and `cdp.py.txt` — which are what `fux setup`
> writes into every new consumer's repo. **The duplication was not confined to
> this repo; it was shipped.** All four now import `fux.decode.htmldoc`.
>
> ⚠ **And [ADR-HTTP-FETCHER](../../docs/adr/0021_http-fetcher.md) decision 7
> claimed a test that did not exist.** It read *"a test asserts the two agree on
> the same input"*; the cited test asserted the conversion was **deterministic**
> and handled headings — never that the copies agreed. **A record asserting a
> guarantee its own cited test does not check**, standing since 2026-08-19.

**The decoder plane already exists. It is in the wrong place, and there are
two copies of it.**

- `.fux/fetchers/http.py:69` — *"HTML -> Markdown - stdlib html.parser,
  deterministic"*, with `_MdParser`, `_TitleParser`, and a `pre`/code path.
- `.fux/fetchers/cdp.py:282` — the same `_MdParser`, carrying the comment
  *"Kept identical to…"*. Agreement by copy-paste, checked by nothing.

Three consequences, all live:

1. **A local `.html` on disk is never decoded.** The git-dir walker has no
   fetcher, so the only HTML decoder fux owns is unreachable from the only
   path most documents arrive by.
2. **Two copies drift.** Nothing tests that they agree.
3. **The decoding rules sit outside `src/fux/`**, in consumer-editable files,
   so **L1** does not even formally reach them.

---

## 2 · What a decoder IS — the contract ⚠ Opus, ratify before P0

**Not "everything to text."** A decoder maps **bytes → `ParsedDoc(meta, body)`**,
and Fux's already-shipped answer to the intermediate is **Markdown**.

That is not a preference; it is forced by
[`ingest/extract.py`](../../src/fux/ingest/extract.py), which re-derives
headings with `^(#{1,6})\s+` and puts them in their **own weighted field**. A
decoder returning flat text drops every heading into the body, silently
disabling *"heading match outranks body match"* on every non-Markdown document.

```
bytes ──▶ decode(bytes, rel_path) ──▶ Markdown ──▶ parse.py ──▶ ParsedDoc ──▶ extract.py
             │                                                                    │
             └─ cannot decode ──▶ the enrichment queue (§8)          title · phrases · terms · flen
```

**The contract, to be written into `ADR-DECODE`:**

| clause | rule |
|---|---|
| signature | `decode(raw: bytes, rel_path: str) -> str \| None` — Markdown, or `None` meaning *a model must read this* |
| determinism | **L3.** Same bytes → same string, byte for byte. Sorted iteration everywhere; no `set` order, no dict-insertion reliance, no wall clock |
| offline | **L4.** No decoder opens a socket. Ever — not for a schema, not for a font, not for an XML entity (see §9) |
| dependencies | **L1.** stdlib only — **for a built-in decoder.** A *consumer* decoder under `.fux/decoders/` may install what it likes (§12) |
| content | **L2.** The Markdown is transient — it feeds statistics and is discarded. No decoder writes it anywhere durable |
| failure | never raises for malformed input. Returns `None` and a reason. A corrupt PDF is a skipped document, not a failed ingest |

**Why `str | None` and not an exception:** a corrupt file in a 10 000-document
corpus must not stop the other 9 999, and the reason string is exactly what the
queue in §8 needs to record.

---

## 3 · The free win — four allowed types have never had headings ⚠ live defect

`DEFAULT_TYPES` in [`gitdir.py:133`](../../src/fux/ingest/gitdir.py) is:

```python
("*.md", "*.markdown", "*.txt", "*.rst", "*.adoc", "*.org")
```

`extract.py` knows only `#`. So:

| type | its heading syntax | matches `^#{1,6}\s+`? |
|---|---|---|
| `.md` / `.markdown` | `# Heading` | ✅ |
| `.txt` | — | n/a |
| `.rst` | `Heading` over `=======` | ❌ |
| `.adoc` | `== Section` | ❌ |
| `.org` | `* Heading` | ❌ |

**Three of six allowed types have had every heading land in the body field
since the allowlist shipped.** Their `phrases` list — which
`fux ask` now renders as `§` lines (W-84) and `answer --no-refer` uses — is
empty for them.

**This is not a decoder.** It is a heading grammar, it is cheap, and it should
land **first**, because it is a correctness fix to shipped behaviour rather
than a new capability.

⚠ **It changes rankings on existing corpora**, so it is a behaviour change:
ADR-EXTRACTED amended in the same change, and the golden fixtures in
`tests_e2e/` re-blessed **deliberately**, never regenerated blindly.

---

## 4 · Definition of done

- `src/fux/decode/` exists, is claimed by `ADR-DECODE` in the ownership table,
  and `tests/test_adr_ownership.py` is edited in the same change.
- `.fux/fetchers/http.py` and `cdp.py` **import** the shared decoder instead of
  carrying a copy, or the duplication is recorded as a deliberate refusal with
  a reason (§11 fork D).
- Every format in §6's shipped phases decodes to Markdown behind a golden
  fixture, and a **byte-identity test** asserts the same input decodes
  identically twice in one process and across two runs.
- `.rst` / `.adoc` / `.org` headings reach the `heading` field.
- An undecodable file produces a **committed queue entry** and no crash.
- `fux doctor` reports the queue's depth.
- **P7 only:** a declared consumer decoder whose dependency is missing **fails
  ingest with the install line**, and `fux doctor` reports it at setup time.
- **Both suites pass** — `tests/` and `tests_e2e/`.
- Every record in the header list that this touches is amended **in the same
  commit**, or the commit says `no ADR affected` and means it.

---

## 5 · Out of scope

- **OCR in a *built-in* decoder.** A model on the maintenance path is **L3**,
  full stop, and images stay `enriched`'s. ⚠ **Amended by §12:** a *consumer*
  decoder shelling out to Tesseract is a library boundary, not a model one, and
  is now permitted. The L3 line is the model, not the dependency.
- **Legacy `.doc` / `.xls` / `.ppt` and `.msg`** (OLE2/CFB) **in the runtime**.
  ⚠ **Fork E is RULED (§12)** — these arrive as *consumer* decoders with
  consumer dependencies, declared and committed. Not "filed, not built" any
  more; scoped, and after P1.
- **Archive containers** (`.zip`, `.tar`). A container is not a document, and
  recursive decoding is a decompression-bomb surface.
- **Any measurement above 10 000 documents.** The litmus is binding: no
  threshold, budget or verdict at 50k/100k, and no bench run there to prove a
  point about decoder cost.
- **Indexing source code.** ADR-TYPES excluded `.py`/`.sh` deliberately and
  that verdict stands. A *docstring-and-comment* decoder is a different object
  and is a proposal, not this item (§11 fork F).

---

## 6 · The formats, in cost order

**Tier 0 — not decoders at all.** `.rst` `.adoc` `.org` — heading grammar
only (§3).

| tier | formats | stdlib | note |
|---|---|---|---|
| **A** — small | JSON, `.ipynb`, TOML, INI/`.properties`, CSV/TSV, generic XML | `json` · `tomllib` · `configparser` · `csv` · `xml.etree` | `.ipynb` is free once JSON lands and is the highest-prose of the set |
| **B** — small, own module | **HTML** (lift, do not write), `.eml` | `html.parser` · `email` | `.eml` is underrated: in an enterprise, decisions live in mail threads |
| **C** — medium | OOXML `.docx`/`.pptx`/`.xlsx`, ODF `.odt`/`.ods`/`.odp`, `.drawio`, RTF | `zipfile` + `xml.etree` · `zlib` + `base64` | OOXML and ODF are the same shape — the second is nearly free after the first |
| **D** — large | **PDF** | `zlib` | text layer only: xref tables, object streams, `ToUnicode` CMaps |
| **E** — not stdlib | legacy OLE2, `.msg`, OCR, a stronger PDF | ⚠ **consumer's own** | **RULED (§12): `.fux/decoders/`, declared, consumer dependencies.** Images with no consumer decoder still → the queue (§8) |

### JSON — "trivial" is about the parse, not the decode

`json.loads` is one line. **The design is what becomes title, heading and
body**, and that is exactly where ADR-TYPES' verdict G lives: a raw JSON blob
took second place on a prose query, and `.json` was **11.4 % of this repo's
tokens** at 6 % of its documents.

**That was measured with no decoder** — raw bytes *were* the body. A decoder
that emits keys as headings, string values as body, and drops numbers, UUIDs,
timestamps and base64 is **a different object than the one that failed.**

⚠ **This does not reopen ADR-TYPES by argument.** Per the pre-registration
rule, a decoder that admits `.json` to the allowlist needs a **new
pre-registration at 10 000 documents** and a verdict. Verdict G stands until a
better measurement replaces it.

### YAML — why a subset, and what full YAML actually costs

The extra 80 % of the YAML spec is **type resolution**. Fux does not consume
types; it consumes words. Four concrete costs of going full:

| full-YAML feature | what it costs Fux |
|---|---|
| anchors + aliases (`&a` / `*a`) | expansion **duplicates terms → inflates `tf` → distorts ranking.** A conformant parser is *actively wrong* here: Fux wants the anchor's text read once and never expanded |
| nested aliases (billion laughs) | exponential expansion, unbounded memory at ingest, from a **committed** file. Offline, but still a denial of service |
| implicit typing (`NO`→false, sexagesimals, auto-dates) | changes **zero words**; adds hundreds of lines of **L1** surface owned forever |
| merge keys (`<<:`) | ordered-merge semantics — a silent **L3** determinism hazard |

**The subset is the whole text surface:** indentation, `key:`, `- ` items,
quoting, block scalars `|` and `>`, and multi-document `---`.

**Answering Arpit directly:** yes, full YAML stays `$0` — no dependency is
added either way. But you would write a conformant parser and then
**deliberately violate the spec at the one place that matters to ranking.**
The subset is not the cheap option; it is the correct one.

⚠ `frontmatter.py` is already a hand-rolled YAML subset. **The new decoder
must either reuse it or the two must be proven to agree** — a second YAML
dialect in one codebase is the `_MdParser` defect again (§1).

---

## 6b · The tree — one module per format (Arpit, 2026-08-26)

**Ruled: split by format, not by family.** An earlier draft grouped six formats
into `structured.py`; Arpit split it, and the reason is stronger than tidiness.

⚠ **The override seam works at module granularity.** `.fux/decoders/<name>.py`
wins **by name** (§13.4) — so a bundled `structured.py` would force a consumer
who wants to change **JSON** handling to take ownership of `.ipynb`, `.toml`,
`.ini`, `.csv` and `.xml` as well, and then never receive a bug fix for any of
them. **One module per format is what makes the override survivable.**

```
src/fux/decode/          built-in · stdlib-only (L1) · upgraded with the package
├── __init__.py          the registry + dispatch: ext -> decoder, override lookup
├── htmldoc.py     P1    .html .htm      -- LIFTED from .fux/fetchers/, not written
├── maildoc.py     P1    .eml
├── jsondoc.py     P2    .json           -- entry still gated on ADR-TYPES verdict G
├── ipynbdoc.py    P2    .ipynb          -- built on jsondoc
├── tomldoc.py     P2    .toml
├── inidoc.py      P2    .ini .properties
├── csvdoc.py      P2    .csv .tsv
├── xmldoc.py      P2    .xml            -- generic; OOXML/ODF/drawio use _xml
├── yamldoc.py     P3    .yaml .yml      -- THE SUBSET, not full YAML (§6)
├── docxdoc.py     P4    .docx
├── pptxdoc.py     P4    .pptx
├── xlsxdoc.py     P4    .xlsx
├── odtdoc.py      P4    .odt .ods .odp .fodt  -- ONE module, see below
├── rtfdoc.py      P4    .rtf
├── drawiodoc.py   P4    .drawio
├── pdfdoc.py      P5    .pdf            -- text layer only; none -> the queue
├── _zip.py              shared: bomb caps, SORTED namelist, member limits
├── _xml.py              shared: XXE-safe parsing, entity refusal
└── _ooxml.py            shared: the OOXML/ODF package walk

.fux/decoders/           consumer-owned (P7) -- overrides by name, or new formats
└── example.py.txt       ONE commented example written by `fux setup` (§13.4)
```

⚠ **Corrected during the P4 build: the three OpenDocument types are ONE
module, and that is the one exception to one-module-per-format.** ODF puts a
text document, a spreadsheet and a presentation in the *same* `content.xml`
with the *same* `text:h` / `text:p` / `table:table` elements — `.odt` and
`.ods` differ in which of those appear, not in how they are read. Three modules
would give a consumer three files to override to change one behaviour, which
inverts the seam's purpose. **OOXML genuinely needs three**, because Word,
PowerPoint and Excel store text three different ways (styles, slide parts, a
shared-string table).

**The `doc` suffix is not decoration.** `src/fux/decode/json.py` doing
`import json` resolves to stdlib under Python 3's absolute imports and is
*technically* fine — but four modules in this tree (`json`, `csv`, `xml`,
`yaml`) shadow stdlib names a reader is about to see imported one line below.
The suffix costs three characters and removes the question.

**Three things in the tree are not decoders**, and the underscore says so:
`__init__.py` is dispatch; `_zip.py`, `_xml.py` and `_ooxml.py` are shared
safety and structure. ⚠ **`_zip.py` exists because three families need
identical bomb caps and identical `namelist()` sorting** — written three times,
they diverge, which is §1's defect with a different filename.

**Not in this tree, deliberately:** P0's heading grammar (it is `extract.py`'s,
not a decoder's), and legacy OLE2 / OCR — those exist **only** under
`.fux/decoders/`, by §12.

---

## 7 · Phases

| phase | what | model | blocked by |
|---|---|---|---|
| **P0** | heading grammar for `.rst`/`.adoc`/`.org` (§3) | Opus | — |
| ✅ **P1** | **BUILT 2026-08-26** — `src/fux/decode/`, the `parse_document` seam, the consumer override, HTML lifted out of **four** copies. [ADR-DECODE](../../docs/adr/0042_decode.md); 20 new tests, `tests/` 1 566 green | — | **done** |
| ✅ **P2** | **BUILT 2026-08-26** — JSON, `.ipynb`, TOML, INI/`.properties`, CSV/TSV, XML, `.eml` | — | **done** |
| ✅ **P3** | **BUILT 2026-08-26** — the YAML subset; aliases read once, never expanded | — | **done** |
| ✅ **P4** | **BUILT 2026-08-26** — `.docx`/`.pptx`/`.xlsx`, ODF (one module), `.drawio`, RTF | — | **done** |
| ✅ **P5** | **BUILT 2026-08-26** — PDF text layer, scan-safe: no text → `None`, not an error | — | **done** |
| **P6** | the undecodable path: queue + progress + `write.lock` (§8) | Sonnet | ✅ **UNBLOCKED — fork C ruled 2026-08-26.** Startable |
| **P8** | **the fetcher split** (§13.2): `fetch(url) -> tuple[bytes, str]`, decoding moves to the decoder plane | **Opus** | ✅ **UNBLOCKED — fork H ruled 2026-08-26.** Startable. ⚠ Must re-check the *"no external consumers"* costing, which is dated v0.32.0 and predates the PyPI release |
| ✅ **P7** | **BUILT 2026-08-26** — `fux setup` writes all 16 into `.fux/decoders/`; **the copy runs**; deleted copy falls back to the built-in; imports made absolute so a path-loaded file works | — | **done** |

**P0 and P1 are independent of every fork in §11** and can start today. P6
cannot start at all until Arpit rules the lock.

---

## 8 · The undecodable path — queue, progress, lock

Arpit, 2026-08-26: **committed queue, gitignored progress.**

**Why this exists only now:** today nothing in fux can *say* "a model must read
this." `fux enrich --plan` derives scope from `enrich=true` on a `dirs` line
(ADR-ENRICH decision 4) — **declared**, not discovered. A decoder returning
`None` is a **discovered** need, and it has nowhere to go.

| file | git | holds |
|---|---|---|
| the queue | **committed** | one entry per undecodable document: path, content sha, reason (`image/png`, `pdf: no text layer`). **Sorted by path. No wall clock.** Never content (**L2**) |
| progress | **gitignored**, under `.fux/runtime/` | which entries *this machine* has processed |
| the mutex | **gitignored**, under `.fux/runtime/` | see the compare doc — it exists, and P6 widens who must hold it |

**The queue is a `type`-bearing committed artifact under L3**, so its writer is
held to the same determinism as the index: sorted, stable, byte-identical
across two machines.

⚠ **Edge case to check before writing a line of it:** `.fux/enrich/` is globbed
as `<sha>.md` and `enrich.py::prune` deletes orphans there. A queue file in
that directory must be proven invisible to both, or it lives elsewhere.

**On the lock, the finding that matters** — `acquire()` in
[`maintain/runner.py`](../../src/fux/maintain/runner.py) has **one caller, the
background runner**. A foreground `fux ingest` calls `request_stop` to evict a
runner and then writes **holding nothing**. Two foreground ingests race.
⚠ Asserted from call-site reading, **not reproduced** — P6 falsifies it first.

---

## 9 · Edge cases the build must handle

- **XXE and entity expansion.** `xml.etree` resolves entities. Every XML-shaped
  decoder — OOXML, ODF, `.drawio`, generic XML — must refuse external entities,
  or a document fetches a URL at ingest and breaks **L4** without going near a
  socket call we wrote.
- **Zip bombs.** OOXML and ODF are zip archives. Cap the uncompressed size and
  the member count; `zipfile` will happily inflate a 40 KB file into gigabytes.
- **Zip member order.** `zipfile.namelist()` returns archive order, which is
  writer-dependent. **Sort it** or two byte-identical-content decks decode
  differently.
- **Encoding.** `parse.py` decodes `utf-8-sig` and NFC-normalizes **once**.
  Decoders return `str`, so they must normalize nothing themselves and must not
  re-introduce a BOM.
- **Markdown injection.** A PDF line beginning `# ` becomes a heading. Usually
  correct, occasionally wrong; the contract must say which, and say it once.
- **Empty output.** A slide deck of only images decodes to `""` — that is
  **`None` and a queue entry**, not a zero-term document.
- **PDF without a text layer** is indistinguishable from a PDF whose text layer
  failed to parse, unless the decoder distinguishes them. It must: the first is
  a queue entry, the second is a defect.
- **`.gitattributes` / CRLF.** A `.docx` is binary; if a consumer's repo mangles
  it, decode fails on bytes fux never saw. Worth a `fux doctor` check.

---

## 10 · Tests

- **Golden fixtures per format**, one small file each, committed under
  `tests/fixtures/decode/`, with its expected Markdown beside it.
- **Byte-identity**: decode twice in one process and once in a fresh
  interpreter with `PYTHONHASHSEED` varied — identical bytes.
- **Two-machine determinism** for at least one zip-shaped format, the check
  `v0.37.1` already established.
- **The fetcher-agreement test**: `http.py` and `cdp.py` produce the same
  Markdown for the same HTML as `src/fux/decode/` — the test that would have
  caught `_MdParser` drifting.
- **Adversarial**: a zip bomb, an XXE document, a truncated PDF, a YAML
  billion-laughs file. Each returns `None` or a capped result; none raises,
  none hangs, none opens a socket.
- **The import fence** (**L4**) extended to `src/fux/decode/` — and a test that
  it does **not** reach `.fux/decoders/`, so the boundary is asserted rather
  than assumed (§12.4: nothing can gate consumer code).
- **The loud error (§12.3):** a declared consumer decoder whose module or
  dependency is absent makes `fux ingest` **fail**, naming what to install —
  never produce a quietly smaller index. Two machines, one declaration: same
  root hash, or a failure.
- **`tests_e2e/`**: a corpus containing one of each format, ingested through
  the real CLI.

---

## 11 · Forks — Arpit's, and no agent may pick a default

| # | fork | why it is his |
|---|---|---|
| ~~**A**~~ | ~~Does `.json` re-enter the allowlist?~~ | ✅ **RULED 2026-08-26, and WIDER than the question asked.** Arpit: *"all the ones which have a decoder"* — `DEFAULT_TYPES` goes from six prose globs to **thirty-six**: prose plus every extension a **built-in** decoder claims. ⚠ **This item was WRONG about why it was blocked.** It said reversing verdict G needed a new pre-registration at 10 000 documents; the pre-registration rule governs **frozen thresholds**, and the compare doc's own verdict block calls G's contents *"a defaults judgment rather than a measurement"*. **The overstatement was written into three places** — this row, ADR-DECODE decision 9 and `jsondoc.py`'s docstring — and all three are corrected. **The 14 %/11.4 % measurement stands**: it measured raw bytes as the body, and every admitted format now passes a decoder that drops ids, hashes, timestamps and numbers. ⚠ **Derived from BUILT-IN decoders only** — a default that grew when a consumer added `logdoc.py` would mean adding a decoder silently starts indexing a new type; pinned by a test |
| ~~**B**~~ | ~~Markdown intermediate, or a structured `headings` field?~~ | ✅ **RATIFIED 2026-08-26: Markdown is the contract.** Arpit: *"ratify immediately."* Decoded documents take the **exact path an already-prose file takes** — one pipeline, the best-tested one, no branch. ⚠ **The accepted cost, stated because it is real and one-directional:** a decoder that knows a line is body text cannot say so if that line begins with `#`. A PDF line `# 3 of 7 — see appendix` or a CSV cell `#1 priority` is promoted to a heading and weighted above body. **The structure was known at decode time and deliberately re-derived a step later**; that is the smell being accepted, not overlooked. No reopen-trigger was attached — the option to add one was offered and not taken, so this is settled rather than settled-for-now |
| ~~**C**~~ | ~~The lock — verdict B, plus the rename~~ | ✅ **RULED 2026-08-26: verdict B ACCEPTED and the lock WIDENS.** Two files — a gitignored mutex and a committed queue — because one must be gitignored and one must be committed, and no `.gitignore` expresses half a file. **`runner.lock` becomes `write.lock`**, and **every command that writes the committed index takes it** (`ingest`, `build`, `add`, `remove`, `update`, the runner); **read verbs take nothing**, since a lock on the read path would fail a search because a re-index was running. ⚠ **The build reproduces the two-foreground-ingests race FIRST** — it is read from call sites and has never been observed, and a fix built on an unverified defect is one nobody can check. ⚠ Also fix `except OSError: return False  # degrade, never block`, which is right for a runner and **inverted for a writer** |
| ~~**D**~~ | ~~Do the fetchers import `src/fux/decode/`?~~ | ✅ **DISSOLVED by the fork H ruling, 2026-08-26** — a fetcher that returns bytes does not decode at all, so there is nothing for it to import. Recorded as dissolved rather than deleted: the question was real until H was answered, and a reader of §11 should see why it stopped mattering |
| ~~**E**~~ | ~~**Legacy OLE2** — build, or refuse and say so~~ | ✅ **RULED by Arpit 2026-08-26 — see §12.** Consumer-owned decoders, declared; missing dependency is a loud error. **L1 is untouched** |
| **F** | **A docstring/comment decoder for source files** | ADR-TYPES excluded code deliberately. Extracting only prose from code is a different proposal and may reopen a settled verdict |
| **G** | **Does `fux enrich` consume the queue**, or does declared scope (ADR-ENRICH decision 4) stay the only origin? | A discovered need and a declared scope are different things; merging them amends an accepted record |

---

## 12 · Fork E — RULED 2026-08-26: the consumer-owned decoder

**Arpit:** *"let the consumer add the dependencies — unless the consumer adds
the dependencies, that feature won't be available."* Then, on how a machine
without them behaves: **declared, and error loudly.**

### 12.1 · The finding that makes this cost nothing

**L1 does not need amending, and the argument is already written down twice.**

[ADR-ENRICH](../../docs/adr/0040_enrich.md) decision 1 states the pattern as a
table and calls it *"ADR-FETCHER's pattern applied to a second boundary."*
**This ruling is the third row of that table:**

| fux refuses to own | the consumer owns it as |
|---|---|
| network I/O | `.fux/fetchers/http.py` — their code, loaded by path, never rewritten |
| model calls | `.claude/skills/fux-enrich/SKILL.md` — their agent, invoked by them |
| **third-party parsing libraries** | **`.fux/decoders/<name>.py` — their code, their dependency** ← *new* |

[ADR-FETCHER](../../docs/adr/0019_fetcher.md) decision 1 already says why this
is legitimate rather than a loophole:

> `src/fux/` holds no network code, no HTTP client, no browser driver, and no
> dependency for any of [them] … **a design choice rather than a dependency
> budget.**

**L1 constrains `src/fux/` — the runtime fux ships.** A consumer decoder is
not that. Fux's supply chain stays trivially auditable and procurement-free,
which is the enterprise feature L1 exists to deliver; the consumer opts into
`pypdf` **in their own file, in their own repo**, and fux never rewrites it.

⚠ **This is a finding, not a concession.** The session went into this expecting
to propose an L1 amendment and a matching edit to `CLAUDE.md` + ADR-LAWS.
**Neither is needed.** If a later session proposes amending L1 to permit
"optional dependencies", this section is the fence it is crossing — the
mechanism already exists and does not require the law to move.

### 12.2 · Two kinds of decoder

| | **built-in** | **consumer** |
|---|---|---|
| lives in | `src/fux/decode/` | `.fux/decoders/<name>.py` |
| dependencies | **stdlib only (L1)** | whatever the consumer installs |
| declaration | none — always available | **required**, committed |
| missing | impossible | **hard error naming what to install** |
| covers | §6 tiers 0/A/B/C/D | tier E: OLE2, `.msg`, OCR, a better PDF |

### 12.3 · How L3 survives — declared, not detected

**Detection would break L3 outright**, and this is the part that is not
obvious: if a decoder ran whenever its library happened to be importable, two
developers ingesting **identical sources** would produce **different root
hashes** — one indexes the `.doc`, the other queues it as undecodable. The
index would become a function of the environment, which is the one thing L3
forbids.

**Declared fixes it**, and the repo already has the mechanism three times over:

- **ADR-FETCHER's subtitle is literally *"declared not detected"***, and
  *"fetcher not found"* is already a loud error with a documented fix.
- **W-83** established that a declaration is a **ceiling**, never a floor.
- **W-85** established that a required key which is missing is an **error**,
  not a default — *"never commented; if it is commented, throw an error."*

So: the decoder set is **committed**, and a machine that cannot satisfy it
**refuses to ingest and names the missing dependency.** Same sources + same
declared config → same index, or a failure loud enough that nobody ships a
quietly smaller one.

### 12.4 · The honest cost, stated rather than implied

**A consumer decoder can break L4 and fux cannot stop it.** A fetcher is
*allowed* network; a decoder is not — but nothing in an import fence reaches
consumer code loaded by path.

This is the **same asymmetry ADR-ENRICH decision 3 already owns** about
`model:` — a claim fux records and cannot confirm. It is written the same way:
a documented consumer obligation, checked by review of a committed diff, not
by a gate. **Do not pretend a test covers it.**

Two smaller costs:

- **Ranking becomes environment-visible in one direction.** A repo whose
  decoder list a teammate cannot satisfy is a repo that teammate cannot ingest
  at all. That is the intended behaviour, and it will feel harsh the first time.
- **`fux doctor` gains real work** — report each declared decoder, whether it
  imports, and what to install. Without that, the loud error arrives at ingest
  instead of at setup.

### 12.5 · What this does NOT open

- **Not the runtime.** No third-party import may enter `src/fux/`. The import
  fence test stays and extends to `src/fux/decode/`.
- **Not the maintenance path's own machinery.** The index write mutex is
  runtime code, not consumer code — `filelock`/`portalocker` remain refused
  (see [the compare doc](../compare/index-lock.compare.md) §4, reconciled).
- **Not OCR into `extracted` mode.** A consumer decoder that shells out to
  Tesseract is a **library** boundary; a model is still forbidden on the
  maintenance path by **L3**, and images stay `enriched`'s.
- **Not a general "optional deps" policy** for query-time features. Scope is
  decoders. Anything wider is a new fork.

### 12.6 · What is now owed

| | |
|---|---|
| **new sub-fork ⚠ Arpit's** | Does a consumer decoder receive **bytes** (parallel to a decoder) or a **path** (parallel to a fetcher, which is handed a URL)? Bytes is safer; path is what a `pypdf` user will expect |
| build | `.fux/decoders/` loading, the committed declaration, `fux doctor` reporting, the loud error |
| records | `ADR-DECODE` carries §13; **ADR-ENRICH decision 1's table gains its third row in the same change** |
| ordering | **after P1** — the built-in seam must exist before a consumer plugs into it |

---

## 13 · Four follow-ups (Arpit, 2026-08-26)

### 13.1 · `fux decoder` — YES, and it may never install ⚠ fourth row of the table

**Recommended.** A verb that lists declared decoders, says which import, and
**prints the exact install command**.

⚠ **It must not run the install.** Running `pip` is network (**L4**) and mutates
the consumer's environment. This is the same boundary three times over, and it
now reads as a rule rather than a coincidence:

| fux refuses to | the consumer does it |
|---|---|
| fetch | writes `.fux/fetchers/http.py` |
| call a model | invokes their own agent |
| add a parsing dependency | writes `.fux/decoders/<name>.py` (§12) |
| **install anything** | **runs the command fux printed** |

`fux doctor` reports *health*; `fux decoder` is the detail surface — the same
split `doctor` and `tune` already have. **Amends [ADR-CLI](../../docs/adr/0002_cli-surface.md).**

### 13.2 · HTTP + CDP → decoders: HALF right, and the right half is a live defect

⚠ **Do not move them. Split them.** Fetching is network I/O and stays a
**fetcher** — that is ADR-FETCHER's entire subject, and decoders may never open
a socket (§2). What is misplaced is the **HTML→Markdown pass inside them**.

**The contract is the problem.** `fetch(url: str) -> str` returns **markdown**
today, so a fetcher does *both* jobs. `http.py:43` states the consequence as a
requirement it cannot enforce:

> *"Both fetchers must produce the same markdown from the same bytes, or which
> fetcher retrieved a URL becomes visible in the index."*

**That is a live L3 hazard written down as a coding convention.** Two fetchers,
one hand-maintained `_MdParser` copy each, and the committed index depends on
*which one ran*. Same sources → same index is the law it quietly breaks.

**The change:** `fetch(url) -> bytes` (plus content type), and decoding moves
to the decoder plane. Three payoffs, and the third is new capability:

1. The `_MdParser` duplication becomes **structurally impossible**, not
   "checked by a test we should write".
2. Which fetcher ran **stops being visible in the index** — the requirement
   retires instead of being enforced.
3. ⚠ **A URL serving a PDF becomes indexable.** Impossible today: the fetcher
   contract demands markdown back, so a non-HTML URL has nowhere to go.

⚠ **Cost, and it is the reason this is a fork and not a decision:** it is a
**breaking change to the consumer fetcher contract**. Every custom fetcher
returns markdown today. ADR-FETCHER already carries a version floor for
exactly this class of change.

### 13.3 · Tables and in-document structure — NOT decoders ⚠ boundary

**Refused as decoder work, and the refusal is the useful part.**

Decoding is **bytes → Markdown**. A table, a code block, a definition list, a
footnote — these **are already Markdown** by the time a decoder is done. The
real question is how [`extract.py`](../../src/fux/ingest/extract.py) *weights*
them, which is the extraction layer, one step later.

**Why the boundary matters more than the feature:**

- Put it in decoders → **every consumer decoder re-implements ranking policy**,
  inconsistently, in code fux does not own and cannot test. Consumer code
  setting ranking behaviour is a far worse defect than a missing table field.
- Put it in `extract.py` → **one implementation, and every format gets it
  free.** A table inside a PDF and a table inside a `.md` are then treated
  identically, because by that point they *are* identical.

Filed as [`proposals/structure-aware-extraction.md`](../proposals/structure-aware-extraction.md) —
an idea, not a fork, and **not part of W-86**.

### 13.4 · Editable decoders in `.fux/` — ⚠ RULED 2026-08-26: EXPORT THEM ALL

> ⚠ **ARPIT OVERRULED THIS SECTION THE SAME DAY, AND THE SECTION BELOW IS KEPT
> AS THE CASE HE HEARD AND REJECTED — not as current behaviour.**
>
> **The ruling: `fux setup` writes all sixteen decoders into `.fux/decoders/`,
> and the copy is what runs.** His argument: a consumer invited to override
> decoders should be able to *read* them in their own repo, and a seam you
> cannot see is a seam nobody uses. An eject-on-demand middle
> (`fux decoder eject <name>`) and a hash-stamped *inert-until-edited* variant
> were both offered and declined in favour of the simpler rule.
>
> **What that means, and it is a real cost he took knowingly:** after `fux
> setup`, `src/fux/decode/` **does not execute** in that repo. Engine upgrades
> reach nobody's decoders — each of the four defects found in the P2–P5 build
> would have required every consumer to refresh their copy by hand.
>
> **Two things the ruling did NOT change**, because they are mechanism rather
> than policy: a **deleted** copy falls back to the built-in (`rm pdfdoc.py`
> must not look like a corpus with no PDFs), and the copy is **byte-identical**
> to the shipped module — no `.py.txt`, no transform, because a decoder is
> stdlib-only and offline and therefore already a legitimate module. Imports
> inside `decode/` became **absolute** to make that true; a path-loaded file has
> no parent package, so a relative import would leave every copy dead on arrival.
>
> Built as **P7**; recorded in [ADR-DECODE](../../docs/adr/0042_decode.md)
> decision 11 and [ADR-DOTFUX](../../docs/adr/0003_fux-directory.md).

#### The case that was made and rejected

**The seam: yes**, and §12 already establishes it. `.fux/decoders/<name>.py`
overrides the built-in of the same name if present; absent means the built-in
runs. Same shape as fetchers, same reason.

⚠ **Shipping fifteen live copies at `fux setup`: no — and this item's own §1 is
the evidence.** `_MdParser` was copied into two files with a comment saying
*"Kept identical to…"* and nothing kept it identical. **A copied default never
receives a bug fix.** Exporting every decoder into every consumer repo is that
defect institutionalised at 15×, and it means upgrading fux upgrades nobody's
decoders.

**Recommended shape:**

| | |
|---|---|
| built-ins | stay in `src/fux/decode/` — tested, versioned, **upgraded with the package** |
| override | `.fux/decoders/<name>.py` wins **by name** when present |
| new formats | `.fux/decoders/` is the only home (§12) |
| `fux setup` writes | **one commented example**, not fifteen live copies |
| `fux decoder` reports | built-in vs overridden vs consumer-only, so a stale override is **visible** |

⚠ **The cost of the override, stated:** an overridden decoder makes the index a
function of consumer-edited code. That is **already true of fetchers** and is
accepted there; it is named here so it is not discovered later.

### 13.5 · What this adds to §11

| # | fork | status |
|---|---|---|
| ~~**H**~~ | ~~Does `fetch()` return bytes instead of markdown?~~ | ✅ **RULED 2026-08-26: `fetch(url) -> tuple[bytes, str]`** — the bytes the server sent, plus the `Content-Type` it declared. Arpit: *"fetcher should return html then decoder to use html and convert to markdown"*, refined to carry the type. ⚠ **The content type is not decoration:** the fetcher is the ONLY thing that ever sees the HTTP charset header, and `htmldoc` currently sniffs `<meta charset>` because a file on disk has none — for a URL the header is authoritative and strictly better. It also lets a URL serving a **PDF, `.docx` or `.csv` route to the right decoder**, which the markdown-returning contract forbids outright. **Breaking change to every consumer fetcher; cheapest now, in alpha.** ⚠ ADR-FETCHER's *"no external consumers"* costing is dated **v0.32.0** and `fux-engine` has since been published to PyPI — **the cost is unmeasured, not near-zero**, and P8 must say so rather than repeat the stale line |
| **I** | Is `fux decoder` its own verb, or subcommands under `fux doctor`? (§13.1) | Arpit's — ADR-CLI's surface |
| ~~**J**~~ | ~~Does `fux setup` write one commented example decoder, or nothing at all?~~ | ✅ **MOOT — superseded by the §13.4 ruling the same day.** Setup writes **all sixteen**, so there is no "one example" question left to answer. Struck rather than deleted so a reader of §13.5 does not go looking for an answer that was overtaken rather than given. *(Original framing: Arpit's — the fetcher precedent says *write something*, because a fresh consumer told to copy a file from docs is a defect ADR-FETCHER already recorded)* |

**P8** — the fetcher split (§13.2) — **blocked on fork H**, and it should land
**before** P7's consumer decoders, or consumers write against a contract that
is about to change.

---

## 14 · Why this is worth building

**One sentence:** fux currently indexes six plain-text extensions, and the
corpus it is pitched at — *organizational* knowledge, inside a corporation —
is mostly PDFs, decks, spreadsheets, wiki HTML and mail.

The litmus from `CLAUDE.md` applied honestly: *does this hold up on a
10 000-document corpus inside that corporation?* A 10 000-document corporate
corpus where fux can read six extensions is not a 10 000-document corpus. It
is a Markdown repo with a very good index.
