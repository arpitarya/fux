# W-63 — `fux add` / `fux remove` / `fux update`, over dirs, documents and URLs

**Status:** BUILT 2026-08-21, uncommitted · **Filed:** 2026-08-21 · **Lane:** `agent`
**Decided by:** Arpit, 2026-08-21 — the surface, and the L4 fork below. The
design was settled in conversation; **what is open is the build, not the call.**
**Blocked by:** nothing.
**Closes with:** [ADR-CLI](../../docs/adr/0002_cli-surface.md),
[ADR-DIR-LIST](../../docs/adr/0022_dir-list.md),
[ADR-URL-LIST](../../docs/adr/0018_url-list.md),
[ADR-INGEST](../../docs/adr/0007_ingest.md) and
[ADR-LAWS](../../docs/adr/0001_laws.md) updated **in the same change**, plus a
surface capture filed under [`../regression/`](../regression/README.md).
**Model:** **Opus.** Three reasons, any one of which is sufficient: it edits
**L4**, which is a non-negotiable constraint; it retires a shipped verb from a
released package; and the remove-by-coverage rule is a judgement call about
grammar semantics that no test can catch if it is decided wrongly. A handoff
this detailed would normally read as Sonnet-executable — it is not, because the
law edit is the deliverable as much as the code is.

---

## Why this exists

`fux url` is the only verb that writes a source list, and it writes exactly one
of the three lists. `.fux/sources/dirs` and `.fux/sources/types` are hand-edited
or untouched since `fux setup` wrote them. So the corpus — the thing the whole
engine is about — is the one part of fux with no first-class CLI.

Arpit's instruction, 2026-08-21: **add and remove in the CLI rather than URL,
working for dirs and documents as well; add ingests by default; remove drops
the document from the index and the graph; and an `update` verb alongside them.**

## What was decided (2026-08-21) — do not re-litigate these

1. **`fux add <URL>` fetches that one URL.** Rejected: record-only
   (`git remote add`) and a required `--fetch` flag. Ingesting a URL without
   fetching it is a no-op, so any other option means "ingest by default"
   silently does not apply to URLs. The fetch is **scoped to the URL just
   added**, says on stderr that it went to the network, and `--no-fetch` opts
   out.
2. **`add` and `remove` write lines; `update` never touches a line.** That
   one sentence is what keeps three verbs from overlapping. Attribute edits stay
   on `add`, which is already an upsert (`sources.add()` returns `"updated"`).
3. **`fux update` subsumes `fux ingest --refresh-urls`.** After (1) the engine
   would otherwise have three networked paths; this leaves it at **two**, both
   explicitly named: `fux add <url>` and `fux update`.
4. **Remove-by-coverage.** A path with its own line is removed by deleting the
   line; a path covered by a listed ancestor is removed by writing a `!`
   exclusion. The verb states which it did.

## Two defects this depends on — fix them first

Both are in [`src/fux/ingest/run.py`](../../src/fux/ingest/run.py) and both are
real independent of this item. **`fux remove <url>` cannot work until (1) is
fixed**, and the graph half of the definition of done cannot hold until (2) is.

1. **A de-listed URL survives an offline ingest.** The non-refresh branch does
   `carried = dict(existing_urls)` — every prior `url:` record is carried
   forward unconditionally, so a URL removed from `.fux/sources/urls` only
   disappears on a `--refresh-urls` run. **Deletion needs no network.** The
   module docstring states the current behaviour as intended ("*reconciliation
   happens only on the run that opted into the network*"); that sentence is
   what this fix changes, and it changes in the same commit.
2. **Carried URL records keep stale `edges`.**
   [`graph/model.edges_from_records`](../../src/fux/graph/model.py) lifts them
   with no validation, on the docstring's claim that dangling edges were
   already dropped by `ingest/edges.py` — true only for records **re-resolved
   this run**. A removed document can therefore survive as an edge target in
   the derived graph plane.

**Keep the transient-failure guarantee.** A URL still listed whose fetch fails
keeps its prior record. What changes is only that a URL **no longer listed** is
dropped whether or not the run touched the network.

## Scope

**In:**

- `fux add <entry>` · `fux remove <entry>` · `fux update [entry]`, flat verbs.
- Entry dispatch: `http(s)://…` → `sourcelist.URLS`; `--types` → `TYPES`;
  otherwise → `DIRS` (which already covers both a directory and a single file).
- The two `run.py` defects above.
- Retiring `fux url` and `fux ingest --refresh-urls`.
- The five ADR edits, the ownership table, and a filed surface capture.

**Out:**

- The progress plane — that is [W-64](W-64-progress-plane.md), and it lands
  after this.
- Any change to the grammar in `sourcelist.py`. **Nothing in this item needs
  one**, which is most of why it is small.
- `archived=true` semantics (still W-44's, still parked).
- Scoped/partial ingest as an optimisation. `update <entry>` re-fetches that
  entry and then runs **the ordinary delta ingest**. A second write path is how
  L3 byte-determinism breaks, and delta ingest is already cheap for unchanged
  documents.

## The surface

**Captured verbatim on 2026-08-21** into
[`../regression/2026-08-21-source-verbs/`](../regression/2026-08-21-source-verbs/report.md),
replacing the intended transcripts this section held while it was a spec. Root
paths are abbreviated to `<root>`; everything else is exactly what the CLI
printed. Raw: [`evidence/capture.txt`](../regression/2026-08-21-source-verbs/evidence/capture.txt).

### `fux add`

```console
$ fux add handbook
added     handbook archived=false
  in .fux/sources/dirs
ingested 3 docs (1 changed, 2 carried forward), 1 skipped, 1 shards written
  skip docs/architecture.pdf: not an indexed file type
accelerator: 20 terms, 20 blocks, 21 postings (derived, not committed)
# exit 0

$ fux add https://wiki.corp/runbook --cdp --plain
added     https://wiki.corp/runbook fetch=cdp meta=plain
  in .fux/sources/urls
ingested 4 docs (1 changed, 3 carried forward), 1 skipped, 1 shards written
  skip docs/architecture.pdf: not an indexed file type
accelerator: 26 terms, 26 blocks, 27 postings (derived, not committed)
[stderr] fetching  https://wiki.corp/runbook (network — this URL only)
# exit 0

$ fux add *.pdf --types
added     *.pdf
  in .fux/sources/types
ingested 4 docs (1 changed, 3 carried forward), 0 skipped, 1 shards written
accelerator: 25 terms, 25 blocks, 26 postings (derived, not committed)
# exit 0

$ fux add docs --dry-run
would add docs archived=false
  in .fux/sources/dirs
  then: ingest (no network)
# exit 0

$ fux add
.fux/sources/dirs:
* docs archived=false
  docs/architecture.pdf archived=false
  handbook archived=false

* 1 line(s) do not state every attribute, so fux did not write them. They load fine (the reader is lenient); `fux add <entry>` rewrites one in full.
.fux/sources/types:
  *.adoc
  *.markdown
  *.md
  *.org
  *.pdf
  *.rst
  *.txt
.fux/sources/urls:
  https://wiki.corp/runbook fetch=cdp meta=plain
# exit 0
```

**Adding a file never overrides the type allowlist.** `gitdir` states inclusion
as a **conjunction with no precedence**, and promoting an explicitly-added file
past the allowlist would be the W-55 defect from a new direction. `add` runs the
type check and says so — and exits **0**, because a listed file the allowlist
rejects is a fact about the corpus rather than a failed command:

```console
$ fux add docs/architecture.pdf
added     docs/architecture.pdf archived=false
  in .fux/sources/dirs
ingested 3 docs (0 changed, 3 carried forward), 1 skipped, 0 shards written
  skip docs/architecture.pdf: not an indexed file type
accelerator: 20 terms, 20 blocks, 21 postings (derived, not committed)
  → the line is listed, and the type allowlist rejects it. `fux add '*.pdf' --types` allows it; adding a file never overrides the allowlist
# exit 0
```

### `fux remove`

```console
$ fux remove handbook
removed   handbook archived=false
  in .fux/sources/dirs
ingested 3 docs (0 changed, 3 carried forward), 0 skipped, 0 shards written
accelerator: 22 terms, 22 blocks, 23 postings (derived, not committed)
  dropped file:handbook/rota.md from the index
# exit 0

$ fux remove docs/onboarding.md
excluded  !docs/onboarding.md
  in .fux/sources/dirs — docs still listed; this path is subtracted from it
ingested 2 docs (0 changed, 2 carried forward), 1 skipped, 0 shards written
  skip docs/onboarding.md: excluded by !docs/onboarding.md
accelerator: 15 terms, 15 blocks, 15 postings (derived, not committed)
  dropped file:docs/onboarding.md from the index
# exit 0

$ fux remove https://wiki.corp/runbook
removed   https://wiki.corp/runbook fetch=cdp meta=plain
  in .fux/sources/urls
ingested 2 docs (0 changed, 2 carried forward), 1 skipped, 0 shards written
  skip docs/onboarding.md: excluded by !docs/onboarding.md
accelerator: 15 terms, 15 blocks, 15 postings (derived, not committed)
  dropped url:https://wiki.corp/runbook from the index
# exit 0

$ fux remove elsewhere/nope.md
[stderr] error: elsewhere/nope.md is not in <root>/.fux/sources/dirs: it has no line of its own, and no listed entry covers it. Both were checked. `fux add elsewhere/nope.md` would list it; nothing needs removing
# exit 1
```

**That URL removal made no network call** — which is defect 1, fixed: the
record left the index on an ordinary offline ingest.

### `fux update`

```console
$ fux update --check
  fresh  2 others
nothing has drifted.
# exit 0

$ fux update
ingested 2 docs (0 changed, 2 carried forward), 1 skipped, 0 shards written
  skip docs/onboarding.md: excluded by !docs/onboarding.md
accelerator: 15 terms, 15 blocks, 15 postings (derived, not committed)
# exit 0
```

No `fetching` line on that `update`: by then the URL list was empty. It
printed one before the capture caught it — ANALYSIS §1.

`--check` needs no new primitive:
[`refer/freshness.verify(indexed_sha, fetched_sha)`](../../src/fux/refer/freshness.py)
already exists, and for a file it is `store.content_sha` against the record's
`sha` — **fully offline for the `dirs` half.** `--check` does **not** fetch
URLs; it says how many it did not verify and why. Whether a `--check --fetch`
should exist is left undecided rather than guessed.

## Current state and key files

| file | what it already gives you |
|---|---|
| [`src/fux/sources.py`](../../src/fux/sources.py) | `add()` / `remove()` / `_list()` are **already generic over a `ListSpec`**. Only `_urls_file` and `cmd_url` are URL-specific. This is most of the work, already written |
| [`src/fux/ingest/sourcelist.py`](../../src/fux/ingest/sourcelist.py) | one grammar for all three lists; `DIRS` and `TYPES` carry `allow_exclusions=True`, `URLS` does not |
| [`src/fux/ingest/gitdir.py`](../../src/fux/ingest/gitdir.py) | `_candidate_paths` already branches on `base.is_file()` — **a single document needs no new list and no grammar change**. `_excluded_by` matches a path or any ancestor |
| [`src/fux/ingest/run.py`](../../src/fux/ingest/run.py) | the two defects; `run(root, *, refresh_urls, full)` is the seam to extend |
| [`src/fux/store/writer.py`](../../src/fux/store/writer.py) | `write_index` writes the **full** record set and deletes emptied shards — removal needs **no new delete path** |
| [`src/fux/graph/plane.py`](../../src/fux/graph/plane.py) | the plane is **derived** from records by `build_plane`, so a re-ingest rebuilds the graph. Defect (2) is the only thing between that and correctness |
| [`src/fux/cli.py`](../../src/fux/cli.py) | 12 verbs; ADR-CLI decision 7 requires handlers to import lazily |
| [`tests_e2e/test_verbs.py`](../../tests_e2e/test_verbs.py) | the package-as-a-user suite the new verbs join |

## Technical approach

**Phase 1 — the two `run.py` defects.** Land alone, with tests, before any CLI
work. Reconcile carried URLs against the list on **every** run; drop or
re-resolve stale edges on carried records. Update ADR-INGEST and ADR-GRAPH
consequences in the same commit. This phase is independently valuable and
independently revertible.

**Phase 2 — generalise `sources.py`.** Lift `_urls_file` into a
`(spec, path)` resolver over all three lists; add a `dispatch(entry, args)`
that returns the spec. Add `exclude_or_remove(path)` implementing decision (4):
exact entry line → delete; covered by an included ancestor → insert `!path`;
neither → `FuxError` naming both facts. **No change to `sourcelist.py`.**

**Phase 3 — the verbs.** `cmd_add` / `cmd_remove` / `cmd_update` in
`sources.py`, three lazy dispatchers in `cli.py`. `add`/`remove` call
`ingest.run` unless `--no-ingest`. `update` calls `urlsrc` for a scoped fetch,
then `ingest.run`. Retire `cmd_url` and `--refresh-urls`.

**Phase 4 — the records and the capture.** All five ADR edits, the ownership
table plus `tests/test_adr_ownership.py`, then a captured surface run filed
under `work/regression/2026-08-nn-source-verbs/` replacing every invented
transcript above.

## Hard constraints

- **L1** — stdlib only on the runtime path. No new dependency, not even for
  argument parsing.
- **L3** — same sources → byte-identical index. `update` and `add` must not
  create a second write path into the index; both end in `ingest.run`.
- **L4** — the law text changes in this item. See the ADR plan below.
- **ADR-CLI decision 1** — flat verbs, **no subcommand tree**. `fux add` /
  `fux remove` / `fux update` are flat; `fux source add` is the thing being
  refused.
- **ADR-CLI decision 3** — `main` is the only boundary. `sources.py` raises;
  it does not render.
- **ADR-CLI decision 7** — `fux --version` stays instant. New handlers import
  lazily inside their dispatch functions.
- **ADR-DIR-LIST / ADR-TYPES** — inclusion is a conjunction with no precedence.
  An explicit `add` of a file does **not** promote it past the type allowlist.
- **ADR-URL-LIST decision 12** — a written line states every attribute.
  `render_line` already does this; do not bypass it.

## Edge cases

| case | required behaviour |
|---|---|
| `fux add docs/` when `docs/` is already listed | `unchanged`, exit 0, no ingest unless attributes changed |
| `fux add docs/` when `!docs/` exists as an exclusion | **error.** `dirs` has no un-exclude by design; tell the user to delete the `!` line |
| `fux add` a path that does not exist on disk | error before writing the line — `walk_sources` already raises on a missing source, and writing a line that breaks the next ingest is worse |
| `fux remove` an entry that is neither a line nor covered | error, exit 1, naming both facts checked |
| `fux remove docs/` where `docs/` is the only entry | allowed; the index legitimately empties. Say how many documents were dropped |
| `fux add <url>` where the fetch fails | **the line stays written.** Recording and fetching are separate outcomes; report the failure and exit 1 |
| `fux add <url> --no-fetch` | line written, ordinary offline ingest runs, no network |
| `fux update` with no `[sources.url]` configured | the URL half is skipped silently; the `dirs` half still runs. **Not** an error — unlike today's `--refresh-urls` |
| `fux update <entry>` for an entry not in any list | error, exit 1. `update` never creates a line |
| a URL and a file resolving to the same `loc` | already impossible — ids are `url:`/`file:` prefixed |
| `fux add` with `--json` | out of scope. These verbs write; `--json` is the read surface |

## Definition of done

- [x] Defect 1 fixed: a de-listed URL leaves the index on an **offline** ingest;
      a still-listed URL whose fetch fails still keeps its prior record. Both
      asserted.
- [x] Defect 2 fixed: no record surviving a run carries an edge to a document
      absent from that run's record set. Asserted over a corpus containing
      carried `url:` records.
- [x] `fux add` writes to all three lists, dispatching on the entry, and ingests
      by default. `--no-ingest`, `--dry-run`, `--no-fetch` work.
- [x] `fux add <url>` fetches that URL only, and says on stderr that it did.
- [x] `fux remove` implements remove-by-coverage and reports which branch it
      took. The removed document is gone from the committed index **and** from
      the derived graph plane.
- [x] `fux update` works with and without an entry; `--check` is read-only and
      offline for `dirs` entries.
- [~] `fux url` is gone; `--refresh-urls` is hidden for one release (open question 2); `fux ingest` and
      `fux build` are unchanged in behaviour.
- [x] `tests/` and `tests_e2e/` both cover every verb; existing goldens updated
      **deliberately**, never regenerated blindly.
- [x] Records updated: ADR-CLI · ADR-DIR-LIST · ADR-URL-LIST · ADR-INGEST · ADR-GRAPH · ADR-URL-INGEST · ADR-FETCHER · ADR-DOTFUX · ADR-REFER (nine, not five — the L4 sweep reached further than the plan expected); ownership table +
      `tests/test_adr_ownership.py` edited together.
- [x] A surface capture filed under `work/regression/`, and every transcript in
      this file replaced by its verbatim output.
- [x] `OPEN-WORK.md`, `IMPLEMENTATION.md`, `DOC-REGISTRY.md`, `README.md`,
      `CHANGELOG.md` and `WORKLOG.md` true at the end.

## Tests

**Unit (`tests/`)**

- dispatch: `https://…` → URLS, `--types` → TYPES, everything else → DIRS.
- remove-by-coverage: own-line → delete; covered → `!`; neither → `FuxError`.
- `add` of a file whose type the allowlist rejects: line written, document
  skipped, reason reported.
- de-listed URL drops on an offline run; failed-fetch URL that is still listed
  does not.
- no surviving record has an edge to an id absent from the run's record set.
- `--dry-run` writes no bytes: assert the source file's sha is unchanged.

**End-to-end (`tests_e2e/`)**

- the three verbs against the fixture corpus, exit codes and stdout asserted.
- `fux remove` then `fux ask` for the removed document → no confident match;
  `fux explain` on it → not found.
- **the differential law still holds** after an add and a remove: `--scan` and
  the accelerator return byte-identical results.
- **`fux ingest` after `fux add X` produces the same bytes as `fux add X`
  produced** — the L3 assertion that matters most here.

## Open questions — resolved by their stated defaults

Both were pre-authorised in this file ("assumption if unanswered"), and both
are reversible pre-1.0, so neither blocked.

1. **`fux url` — deleted outright.** Four days old, pre-1.0, and every use of
   it is spelled `fux add <URL>` / `fux remove <URL>`. `CHANGELOG.md` says so
   loudly.
2. **`fux ingest --refresh-urls` — kept one release as a hidden alias.** It is
   a flag rather than a verb, it is older, and it is likelier to be in
   somebody's CI. `argparse.SUPPRESS` hides it from `--help`; a test asserts
   both halves (hidden, still parses).

**Deviation from the DoD, recorded rather than glossed.** The checklist says
"`fux url` and `fux ingest --refresh-urls` are gone". The flag is not gone,
because this file's own open question said to keep it. The checklist was
written before the question was answered; the answer wins.

## What was found by building it

Four defects, none of them predicted here, all fixed in the same change and
written up in
[ANALYSIS.md](../regression/2026-08-21-source-verbs/ANALYSIS.md):

| # | defect | where it came from |
|---|---|---|
| 1 | `update` announced a network fetch against an **empty** URL list | reading the capture |
| 2 | `add '*.pdf' --types` **silently un-indexed every markdown document** — the types file replaces the built-in allowlist rather than extending it | running the verb |
| 3 | `add <file>` exited 1 saying "the fetch failed" about a local PDF | writing the e2e test from the DoD |
| 4 | `explain <removed-doc>` answered as though it were still indexed | writing the e2e test from the DoD |

Defect 4 is **older than this item** and belongs to ADR-GRAPH; W-63 is what
made it reachable in two commands. Defect 2 is W-55's invisible filter
arriving from a new direction.

Two smaller ones, found the same way and fixed: `fux add docs/` wrote a
**second line** for a directory already listed as `docs` (the parser dedupes
on the exact string and cannot see it), and `fux add ftp://x/a` was refused
for "not existing on disk" rather than for not being an `http(s)` URL.

---

## The Claude Code prompt

**Model: Opus** — see the model note at the top of this file; the L4 edit is
the reason, and it is not negotiable down to Sonnet.

```text
Read CLAUDE.md, then work/open/W-63-source-verbs.md end to end before you touch
anything. That file is the spec; this prompt only tells you how to execute it.

EXPLORE (do not write yet)
- Read src/fux/sources.py, src/fux/ingest/sourcelist.py, src/fux/ingest/gitdir.py,
  src/fux/ingest/run.py, src/fux/ingest/urlsrc.py, src/fux/store/writer.py,
  src/fux/graph/model.py, src/fux/graph/plane.py, src/fux/cli.py.
- Read docs/adr/0002_cli-surface.md, 0022_dir-list.md, 0018_url-list.md,
  0007_ingest.md, 0001_laws.md, and docs/adr/README.md's ownership table.
- Confirm for yourself, in the code, the three claims the handoff rests on:
  (a) sources.add()/remove() are already generic over a ListSpec;
  (b) gitdir._candidate_paths already accepts a single file;
  (c) write_index writes the full record set and deletes emptied shards.
  If any is false, STOP and write work/BLOCKED.json — the whole plan assumes them.

PLAN
- Post the four phases from the handoff as a TodoWrite list and keep it current
  DURING the work, not at the end.
- Each phase is its own commit. Every commit message either names the record it
  updated or says `no ADR affected` explicitly.

IMPLEMENT — phase by phase, tests with each, never all at once
1. The two run.py defects, with unit tests, plus the ADR-INGEST and ADR-GRAPH
   consequence edits. Land this alone and run both suites before continuing.
2. Generalise sources.py to all three lists. NO change to sourcelist.py — if you
   find yourself editing the grammar, stop and re-read the handoff's Scope.
3. The three verbs in cli.py + sources.py. Retire `url` and `--refresh-urls`.
   Handlers import lazily (ADR-CLI decision 7) — verify `fux --version` is still
   instant with the check in ADR-CLI's veto section.
4. All five ADR edits, the ownership table, and tests/test_adr_ownership.py in
   the same commit as the code they describe.

VERIFY
- uv run pytest -q tests && uv run pytest -q tests_e2e
- Run ADR-CLI's four veto checks verbatim and paste the output. Check 1's
  expected verb list is now stale — update it in the record as part of the change.
- Assert the differential law still holds after an add and a remove.
- Assert `fux ingest` after `fux add X` produces the same bytes `fux add X` did.
- Capture every command in the handoff's Surface section verbatim into
  work/regression/<date>-source-verbs/ with a report.md, an ANALYSIS.md and a
  reproduce fixture, then REPLACE the invented transcripts in
  work/open/W-63-source-verbs.md with the captured output.

CONSTRAINTS — these fail the change, not just the review
- L1: no new runtime dependency.
- L3: add/remove/update must all end in ingest.run. Do not write a second path
  into the index.
- L4 changes in this commit: the engine has TWO named networked paths after this,
  `fux add <url>` and `fux update`. Update ADR-LAWS' table, and every ADR sentence
  saying `--refresh-urls` is the only networked path. Grep for it; there are
  several, including in module docstrings.
- ADR-CLI decision 1: flat verbs. `fux source add` is the thing being refused.
- Adding a file never overrides the type allowlist (ADR-DIR-LIST / ADR-TYPES:
  the three conditions are a conjunction with no precedence).

STOP AND ASK, do not choose a default, if:
- either open question at the foot of the handoff needs answering to proceed
  in a way you cannot reverse;
- an ADR edit would require restating a law rather than citing it;
- a golden file needs changing and you cannot articulate why the new value is
  correct.
Write work/BLOCKED.json with decision ASK and stop.

FINISH
- Update OPEN-WORK.md, IMPLEMENTATION.md, DOC-REGISTRY.md, README.md,
  CHANGELOG.md, INTERVIEW.md, NOW.md and append a WORKLOG.md entry.
- Do not merge on red. Read `gh pr checks <n>` yourself — there are no required
  status checks on main.
```

## The ADR edit plan

Draft text for the load-bearing edits. The executing session may improve the
prose; it may **not** drop an item.

**[ADR-LAWS](../../docs/adr/0001_laws.md) — L4.** Today: *"Network access only
inside explicit, fenced, opt-in paths."* That sentence survives; what changes is
every place that names `--refresh-urls` as the sole path. The law's table entry
becomes explicit that there are **two** fenced paths — `fux add <url>` (scoped
to the URL just added) and `fux update` — and that the import fence test covers
both. **Do not restate the law anywhere else**; a record that paraphrases a law
is a bug in this repo.

**[ADR-CLI](../../docs/adr/0002_cli-surface.md).**

- §1 group table: the **sources** row becomes `add · remove · update`, and the
  feature line goes from twelve verbs to **fourteen**.
- Decision **1a** is rewritten: `url` is retired; `add`/`remove`/`update` take
  its place. Keep the flatness argument verbatim — `fux source add` is now the
  tree being refused.
- A new decision records the split: **`add` and `remove` write lines; `update`
  never touches one.** This is the whole reason three verbs do not overlap and
  it belongs in the record, not in help text.
- A new decision records the **scoped fetch** on `add <url>` with its rejected
  alternatives (`git remote add`-style record-only; a required `--fetch`).
- Veto check 1's expected verb list is stale the moment this lands. Update it.
- Consequences: exit codes unchanged; `--json` untouched (these verbs write).

**[ADR-DIR-LIST](../../docs/adr/0022_dir-list.md).**

- Record **remove-by-coverage** and why it reuses `!` rather than inventing
  anything: the grammar already has subtraction, and the alternative — deleting
  the ancestor's line and re-adding its siblings — is a many-line diff for a
  one-document change.
- Record that **`add` of a file never overrides the type allowlist**, citing the
  conjunction-with-no-precedence rule rather than restating it.
- Note that a single file was always a legal entry; the CLI is new, the grammar
  is not.

**[ADR-URL-LIST](../../docs/adr/0018_url-list.md).** Decision 12 and 13 are
unchanged and must stay unchanged — the writer still emits every attribute.
What changes is the command that calls it: `fux url` → `fux add` / `fux remove`.
Every `fux url …` example in the record is rewritten.

**[ADR-INGEST](../../docs/adr/0007_ingest.md).**

- `--refresh-urls` retires into `fux update`.
- The **URL reconciliation** sentence changes: de-listing is honoured on every
  run; only *fetching* requires the networked path. State plainly that this is
  a behaviour change and that the prior sentence described the defect.
- ADR-GRAPH picks up the carried-edge fix in its consequences.

## Reference

- The conversation that decided it — 2026-08-21, Cowork; recorded in
  [`../WORKLOG.md`](../WORKLOG.md).
- Precedent surveyed for the `add`-does-the-work default:
  [`uv add`](https://docs.astral.sh/uv/reference/cli/) (locks and syncs by
  default, `--no-sync`/`--frozen` to opt out) and
  [`helm repo add`](https://helm.sh/docs/helm/helm_repo/) (records **and**
  fetches immediately). The rejected pole:
  [`cargo add`](https://doc.rust-lang.org/cargo/commands/cargo-add.html)
  (manifest only, never builds) and `git remote add` (records, never fetches).
  [`dvc add`](https://dvc.org/doc/command-reference/add) is the index-tool
  precedent for materialising at add time.
- The cost profile that says a post-`add` full ingest is affordable —
  [`../regression/2026-08-20-ingest-cost-profile/`](../regression/2026-08-20-ingest-cost-profile/report.md)
  (delta ingest is 22.7×/26.4× faster and byte-identical).
