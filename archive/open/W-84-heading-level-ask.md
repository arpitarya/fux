---
type: OpenItem
id: W-84
title: "W-84 — `ask` is heading-level, not line-level"
description: "Arpit asked whether `ask` should cite at line level. Line level would have to lie and would cost a positional index; heading level is already committed and free. `ask`, `find --json` and `fux_search` now name the sections that match the query."
status: implemented
lane: agent
timestamp: 2026-08-26T00:00:00Z
---

# W-84 — `ask` is heading-level, not line-level

**Model: Opus.** The deliverable was the *refusal* as much as the feature — a
line-range field on `ask` would have looked correct on every review and been
wrong on every edited document. No test catches that; only judgment does.

Arpit, 2026-08-26: *"would it be a good idea to have ask at line level rather
than document level?"* — then, on the answer: *"implement the heading level."*

---

## 1 — The question, and the answer given

**The instinct was right and the unit was wrong.** `ask` returning a bare
document *is* less useful than it could be. But the two candidate units are
not equally available to it.

| unit | where it comes from | what it costs `ask` |
|---|---|---|
| line range | chunking the **fetched** bytes | a fetch (L4) or a positional index (2–4× postings) |
| heading | `phrases`, **already committed** | nothing |

### Why a line range on `ask` would have to lie

`answer`'s `docs/mesh.md:L10-L13` is correct **by construction**: it is
computed on bytes fetched moments earlier, and cited with the sha of those
bytes ([ADR-ANSWER](../../docs/adr/0006_answer.md),
[ADR-REFER](../../docs/adr/0030_refer-plane.md)).

An `ask` line range could only be computed at **ingest**. Edit the file, and it
points at the wrong lines **while looking exactly as right as before**. That is
the shape of defect this repo has twice refused already — a knob or a field
that reports confidently on something it no longer knows:

- `max_age_seconds`, refused because a configured age answers a question the
  fetch never asked;
- `cached` never folding into `current`
  ([W-82 §6.0](../../work/open/W-82-the-consolidated-build.md), still open — the
  path is written from the repo root so it survives this file's retirement into
  `archive/open/`): a memo validated by
  a TTL hit reports `current` on unconfirmed bytes.

**And the cost is real.** Line numbers need term positions, i.e. a positional
index — conventionally 2–4× the postings (Zobel & Moffat 2006, §5). The
committed index's entire pitch is that it is small enough to live in git.

**The value is thinnest exactly where the cost is highest.** For `file:`
sources the document is in the working tree already; an agent with the path
opens it, and a line number saves one `grep`. The real value would be `url:`
sources — which are precisely the ones most likely to have changed since
ingest, so precisely the ones the stale range would lie about.

### Why headings are the version that ships

- **They are already in the index.** `ingest/extract.py` commits up to twelve
  headings per document as `phrases`. Nothing new is stored, extracted or
  computed at ingest.
- **They survive editing.** `§ Rollback procedure` still points at the right
  place after a paragraph is inserted, a section is re-wrapped, or the file is
  reformatted. `L10-L13` does not.
- **Their staleness exposure is `title`'s exactly** — the same field, from the
  same document, at the same ingest — and no reader has ever been confused by
  a stale title.
- **They read better for both audiences.** `docs/mesh.md § Rollback procedure`
  tells a human where to look and an agent what to ask `fux_passage` for.

---

## 2 — What shipped

### The selection rule ([`src/fux/query/headings.py`](../../src/fux/query/headings.py))

1. Analyze the query and each phrase through `tokenize` — **the one analyzer
   both sides of every match share**, so `Rollbacks` finds `rollback`.
2. Score a phrase by the count of **distinct query terms** it contains. A
   heading covering two asked-about terms beats one repeating a single term
   five times.
3. **Zero matches → nothing.** Never "the first three headings": inventing
   relevance is what extracted mode exists to forbid.
4. Sort by `(-matches, position in the document)`. The tie-break is document
   order, so the result is a deterministic function of the record (L3) with no
   set-iteration dependence.
5. Cap at `MAX_HEADINGS = 3`.

### The three surfaces

| surface | change |
|---|---|
| `fux ask` (text) | matched headings indented under the citation, prefixed `§` |
| `fux ask --json` / `fux find --json` | `"headings": [...]` per result, **always present** |
| `fux_search` (MCP) | `"headings": [...]` per result, from the record already read for `sha` |
| `fux find` (text) | **unchanged** — bare locators, because it exists to be piped |

### The defect found on the way

⚠ **`fux_search`'s MCP tool description claimed *"line-range citations"*** and
`_search` has never returned one. This is the same defect commit `ad95a24`
fixed in `docs/guide.html` and the usage skills — **still live in the surface
an agent actually reads**, and worse there, because an agent acts on a tool
description without a human in the loop. Corrected, and pinned by
`test_search_does_not_claim_line_ranges_it_never_returns`.

---

## 3 — The decisions, and why each went the way it did

**1. Display-only, applied after ranking.** `headings_for` runs on the
already-unified result list after `run_query` returns — exactly where
`_resolve_title` (P5) runs, and for the same reason: whichever candidate
generator answered, both resolve identically, so there is no seam for the
differential law to break through. Verified: `diff <(ask --json) <(ask --json
--fast)` on this repo returns `IDENTICAL`.

**2. `headings` is always present, `[]` when nothing matches.** An absent key
is a trap, not a signal (W-48): a caller cannot distinguish *"no heading
matched"* from *"this fux does not do headings"*.

**3. No `--headings` / `--no-headings` flag.** `find` is the terse, pipeable
verb and is unchanged; `ask` is the agent-facing verb whose job is to make a
citation actionable. A flag to suppress at most three indented lines is surface
for nothing. ⚠ **Reopen if** a real consumer's parse of `ask`'s stdout breaks —
the flag is the fix, and it is cheap to add later precisely because the default
is the useful one.

**4. Never in the locator.** The `(loc)` a reader copies stays a bare document
path. A heading is not part of an address, and `find`'s stdout stays bare for
the reason [ADR-DIR-LIST](../../docs/adr/0022_dir-list.md) decision 12 gave
about the archived marker: a prefix on a piped line is read as a filename.

**5. `§`, not `#` or `>`.** U+00A7 encodes in `cp1252`, so it clears the
Windows-console gate; `#` would read as a Markdown heading in captured output.

**6. Three, not twelve.** The point is to aim a reader at a section, not to
reproduce the outline. Twelve headings under five results is a page.

**7. `_title_from` split out of `_resolve_title`.** `ask` needs the record for
its `phrases` as well as its title, and two shard reads per result for one
record is a cost with no reader. `_resolve_title` keeps its name and behaviour
— that is what [ADR-ASK](../../docs/adr/0004_ask.md) cites.

---

## 4 — Definition of done, as met

- [x] `headings_for` — deterministic, analyzer-shared, capped, silent on no match
- [x] `ask` text + `ask/find --json` + `fux_search` render it
- [x] `find`'s piped stdout byte-identical to before
- [x] A `hashed` record yields nothing (L5 — it carries no `phrases` at all)
- [x] The differential law re-verified on this repo: `IDENTICAL`
- [x] The false `fux_search` description corrected and pinned by a test
- [x] [ADR-ASK](../../docs/adr/0004_ask.md) and [ADR-MCP](../../docs/adr/0039_mcp.md)
      amended in the same change — both, not only the one the freshness gate
      would have accepted
- [x] 21 new tests; `tests/` **1 483 green** (was 1 436)

## 5 — What was NOT verified, stated plainly

⚠ **`tests_e2e/` was not run.** The build sandbox has only Python 3.10 and
github.com is blocked, so no 3.11+ interpreter could be fetched; the unit suite
ran under a harness-only `tomllib` shim (`tomli` is that exact module
backported) which **never enters the repo**. The two `tests/test_doctor.py`
failures are that shim reporting `3.10 < 3.11` correctly. This is the same
disclosure W-82's build made and the same limitation — **`tests_e2e/` needs a
real 3.11+ install before release.**

⚠ **`tests/test_adr_freshness.py::test_working_tree_is_not_mid_violation` was
already failing before this change**, on a *concurrent session's* untracked
files (`src/fux/templates/index-record.json`,
`work/open/W-83-the-unconfigured-fetch-ceiling.md`). Not caused by W-84 and not
fixed by it — another session's work in flight.

## 6 — What this deliberately does not do

- **It does not make `ask` fetch.** L4 stands; `answer` is the verb that fetches.
- **It does not add positions to the index.** The wire format is untouched.
- **It does not change ranking.** A heading match does not, and may not, move a
  score — that is decision 1 and the differential law is what checks it.
- **It does not make `fux_search` span-level.** The MCP surface is still
  document-level by design; `fux_passage` is the call that reads lines.

## Reference

- Zobel & Moffat, *Inverted Files for Text Search Engines* (ACM Computing
  Surveys, 2006) — §5 on the cost of positional postings:
  <https://people.eng.unimelb.edu.au/jzobel/fulltext/acmcs06.pdf>
- The committed headings — [`src/fux/ingest/extract.py`](../../src/fux/ingest/extract.py)
  (`MAX_PHRASES = 12`), owned by [ADR-EXTRACTED](../../docs/adr/0016_extracted-mode.md)
- The span-level verb this is deliberately not —
  [ADR-ANSWER](../../docs/adr/0006_answer.md), [ADR-REFER](../../docs/adr/0030_refer-plane.md)
- The L5 rule that empties it for a `hashed` record —
  `DISPLAY_FIELDS` in [`src/fux/store/writer.py`](../../src/fux/store/writer.py)
