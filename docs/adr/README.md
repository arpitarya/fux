# ADRs — the decision records

**How to use this file.** This is the register: the naming convention, the
ownership table, and the rules every record obeys. Read it before writing an
ADR, before citing one, and before adding a module to `src/`.

One ADR per completed feature or ruled measurement. Every ADR carries a
reference. Every record is **cited by name** in prose.

## Two directories, three states

**This file is the register for both.** A record's directory *is* its state:

| state | directory | may back a live claim? |
|---|---|---|
| **live** | `docs/adr/` (here) | yes |
| **superseded** | [`archive/adr/`](../../archive/adr/README.md) | **no** — archive is not evidence |

As of **2026-08-18** the entire v0.30 set is **superseded-pending** in
`work/adr/`: those eight records are live and cited normally, and a replacement
set is being written here. Only **ADR-LAWS** lives in `docs/adr/`, because it
names the project's foundational rules rather than deciding a feature and is not
being replaced.

A record moves from `work/adr/` to `archive/adr/` **in the same change that
accepts its successor** — never before, so no claim is ever left ungrounded.
New records are written here, from [`TEMPLATE.md`](TEMPLATE.md).

---

## The convention

**Path.** `docs/adr/000N_<short-name>.md`, numbered sequentially. The number is
a filename ordinal, not an identity — **it is scoped to its directory and its
generation**, and it restarts when a record set is replaced. Two records can
carry `0001` at the same time and nothing breaks, because nothing identifies a
record by number.

**Frontmatter is a fixed six-key block**, and it is checked. `type` · `name` ·
`title` · `description` · `status` · `timestamp`, in that order; **any value
containing `: ` must be quoted**, `name`/`status` must match the body's
`**Name:**` and `**Status:**` lines, and the title must carry both the name and
the file number. `tests/test_adr_frontmatter.py` enforces every one of those —
it exists because frontmatter broke twice on 2026-08-18, once from an unquoted
colon that only strict YAML rejected, and once when a global rename substituted
a name for the number inside eight titles.

**Cite by NAME, never by number.** In prose, always `ADR-RECORD`, never
"ADR-0004". Numbers are for the historical record only — once a record is
superseded and moves to [`archive/adr/`](../../archive/adr/README.md),
its number is how the archive maps it to its successor. A live doc that says
"ADR-0004" is a defect; fix it on contact.

**Two sections, and they are for different readers.**

- **§1 — For humans.** One screen, maximum. Includes a diagram: a Mermaid
  block **and** a hand-paired ASCII twin. **Both are updated together whenever
  either changes** — a Mermaid block that has drifted from its ASCII twin is
  the same defect as a stale diagram.

  §1 may also carry two optional sections, in this order after the diagram:
  **Examples** — real, capture-copied, two or three at most — and **Charts**,
  whose default is *none*. Add a chart only when a shape argues better than a
  sentence; one measure per chart, every number measured or computed, and the
  same both-formats rule as the diagram. Both sections are deleted, not left
  empty, when they do not apply.

  **The ASCII twin is collapsed**, inside a `<details>` block with a
  `<summary>` naming it. The Mermaid renders on GitHub and is what a human
  sees; the twin is there for terminals, diffs, and any reader without a
  renderer, and it should not cost a screen to scroll past. Collapsing it is
  what keeps §1 to one screen while keeping the twin mandatory. Copy the shape
  from [`TEMPLATE.md`](TEMPLATE.md) — a blank line after `</summary>` is
  required, or the fenced block will not render.
- **§2 — For agents.** Context · decision · consequences · alternatives
  considered · reference · veto condition.

**The reference is grounded.** A paper, a live doc, code, or measured evidence
under [`work/regression/`](../../work/regression/README.md). **Never an archived
doc** — nothing guarantees an archived file was not overwritten after the fact
(see [`archive/README.md`](../../archive/README.md)). An archived doc
may be *named* in a record; it may not *back* a live claim.

**The veto condition is a condition, not an event.** Write what would have to
become **true** for the decision to reopen, phrased so someone can check it
today with a command or a look at the code. "Revisit when we hit scale" is not
a veto condition; "reopen if p95 on a ≥100k-doc corpus exceeds 150 ms" is.
A veto written as an event to await never fires, because nobody is waiting.

**A record that restates a cross-cutting principle is a bug.** The project's
foundational rules live in exactly one place — **ADR-LAWS**. Every other record
references it by name and cites the law's number. Do not paraphrase a law into
a record; the paraphrase is what drifts.

**Records are kept current by a check, not by good intentions.** `CLAUDE.md`
§Law zero is the rule; these are the two places it is enforced:

| where | what it does |
|---|---|
| `tests/test_adr_freshness.py` | runs in CI (`pytest -q tests`). Fails any commit since the rule landed that changed an ADR-owned component without touching a record — and fails a working tree that is mid-violation |
| [`scripts/adr-guard.sh`](../../scripts/adr-guard.sh) | the same check as a pre-commit hook: `ln -sf ../../scripts/adr-guard.sh .git/hooks/pre-commit` |

**The escape hatch is `no ADR affected` in the commit message** (or `[no-adr]`).
It is not a silent skip — it is a claim, in git history, under your name, that
you checked and there was nothing to update. That is exactly what the rule asks
for.

**The baseline is self-bootstrapping**: the check applies from the commit that
added it, never retroactively. After a bulk review you can move the baseline
forward by writing a commit sha into `docs/adr/RULE-SINCE`.

**Superseding.** A superseded record moves to `archive/adr/`, and
`archive/adr/README.md` maps its old number to its live successor. The
archive-is-not-evidence rule applies to it from that moment.

Start from [`TEMPLATE.md`](TEMPLATE.md).

---

## The register — the new set (`docs/adr/`)

**Numbering restarted at 0001** with ADR-LAWS (2026-08-18), because the v0.30
set is being replaced wholesale. This is the third restart: the v0.26 line ran
0001–0015, the v0.30 line restarted at 0001 on 2026-08-09, and this one starts
again here.

| # | name | title | status |
|---|------|-------|--------|
| [0001](0001_laws.md) | **ADR-LAWS** | The non-negotiable constraints have exactly one home, and records cite it | accepted |
| [0002](0002_cli-surface.md) | **ADR-CLI** | The command-line surface — six verbs, one boundary, three output modes; every command captured verbatim | accepted |
| [0003](0003_fux-directory.md) | **ADR-DOTFUX** | The `.fux/` directory — every child declared committed or derived; the ignore rule asserted against git | ⏳ proposed |
| [0004](0004_ask.md) | **ADR-ASK** | The `ask` verb — one scorer, one sort; the path that answers can never change the answer | ⏳ proposed |
| [0005](0005_find.md) | **ADR-FIND** | The `find` verb — one line per hit, for pipes; a projection of `ask`, not a second strategy | ⏳ proposed |
| [0006](0006_answer.md) | **ADR-ANSWER** | The `answer` verb — the single best answer the index can give, with its ceiling stated in every response | ⏳ proposed |
| [0007](0007_ingest.md) | **ADR-INGEST** | How ingest works — re-extract everything, re-resolve every edge, write only shards whose bytes changed | ⏳ proposed |
| [0008](0008_url-ingest.md) | **ADR-URL-INGEST** | URL ingestion through consumer-owned middleware — four functions, `--refresh-urls` only, a committed URL file | ⏳ proposed |
| [0009](0009_index-lifecycle.md) | **ADR-INDEX-LIFECYCLE** | Index generation and update — one canonical encoder, write-if-different, a derived plane that refuses to diverge | ⏳ proposed |
| [0010](0010_index-record.md) | **ADR-RECORD** | One line of the committed index, property by property — including the two that are conditional on privacy | ⏳ proposed |
| [0011](0011_accelerator.md) | **ADR-T1-ACCELERATOR** | The derived T1 accelerator — disposable, term-major, and forbidden from changing an answer | ⏳ proposed |
| [0012](0012_ranking.md) | **ADR-RANKING** | How documents are scored and ordered — BM25F, weight-then-saturate once, one scorer and one rounded sort | ⏳ proposed |
| [0013](0013_postings.md) | **ADR-POSTINGS** | The postings in two shapes — doc-major in git for diffs, term-major in the runtime plane for queries | ⏳ proposed |
| [0014](0014_config.md) | **ADR-CONFIG** | `fux.toml` and every property in it — including the one table fux passes through unread | ⏳ proposed |
| [0015](0015_port-list.md) | **ADR-PORT-LIST** | Port, don't rewrite — nine named modules from the archived engine, each with its tests, and the list is closed | ⏳ proposed |
| 0016+ | — | unwritten | planned |

**Eight of these are successors, and none has retired its predecessor yet.**
ADR-DOTFUX, ADR-ASK, ADR-INGEST, ADR-URL-INGEST, ADR-INDEX-LIFECYCLE,
ADR-RECORD, ADR-T1-ACCELERATOR and ADR-CONFIG each name what they supersede
(ADR-FIND, ADR-ANSWER, ADR-RANKING and ADR-POSTINGS supersede nothing — those
subjects never had a record), and each is ⏳ *proposed*. **Retirement happens in the change
that accepts them** — and three of the predecessors are themselves unratified
([W-30](../../work/open/W-30-ratify-adr-0001.md),
[W-31](../../work/open/W-31-ratify-adr-0010-0011.md)), so the ratifications come
first: replacing an unratified decision inherits its ambiguity. Until then the
predecessors keep their entries in the ownership table, and the successors carry
an **`Owns (on acceptance)`** line instead of `Owns`.

**Numbers collide across the two directories, and that is fine.** `0001` here
is ADR-LAWS; `0001` in `work/adr/` is ADR-INGEST, retiring. Nothing reads
a number to identify a record — that is exactly why the cite-by-name rule
exists, and why this restart costs nothing. `tests/test_adr_ownership.py`
enforces uniqueness **within** each directory, not across them.

## The v0.30 set is retired

**All five remaining records were archived on 2026-08-18**, in one change, on
Arpit's instruction — `work/adr/` no longer exists. Their map, with a named
successor for each, is [`archive/adr/README.md`](../../archive/adr/README.md).

Two consequences, recorded rather than left to be discovered:

- **The successors are the records in force.** They hold the components their
  predecessors used to own, and their status moved from ⏳ *proposed* to
  **accepted** — a record cannot own the engine and be a proposal at the same
  time.
- **The ratification items survive.** W-30 and W-31 were never about *which
  record* holds a decision; they are Arpit's calls on the ingest-mode naming,
  the `.fux/` layout and the URL middleware themselves, and they now point at
  the successors.

Records that supersede nothing — ADR-FIND, ADR-ANSWER, ADR-RANKING,
ADR-POSTINGS, ADR-PORT-LIST — **stay ⏳ proposed**. Nothing forced their hand.

The v0.26 engine's ADRs 0001–0015 are frozen at
[`archive/v0.26-docs/adr/`](../../archive/v0.26-docs/adr/) and are always cited
as **"archived ADR-NNNN"** with that path — a bare `ADR-<NAME>` in any live doc
means this directory.

---

## Ownership — which record owns which component

**This table is the answer, not a judgement call.** Every component in `src/`
and `tools/` appears here exactly once. A component owned by no record is a
defect, and `tests/test_adr_ownership.py` fails on it.

**Superseded-pending records still own things.** Eight of the owners below live
in `work/adr/`, and they keep their components until a successor takes them —
that transfer happens in the same change that accepts the successor.

**Proposed records declare `Owns (on acceptance)` instead**, and several are
deliberately more specific than a sibling's claim: ADR-RANKING takes
`query/rank.py`, `bm25f.py` and `tokenize.py` out of ADR-ASK's claim on
`src/fux/query/`, and ADR-CONFIG takes `config.py` out of ADR-DOTFUX's. Most
specific wins, exactly as the table already resolves `store/fuxdir.py` against
`store/`. **Nothing changes in the table below until acceptance.**

**Both change together.** When this table changes, edit
[`../../tests/test_adr_ownership.py`](../../tests/test_adr_ownership.py) in the
same change. They drift silently otherwise — that is the entire reason the
check exists.

A component that genuinely has no decision yet is claimed by an **open work
item** (`W-nn`) instead. The test resolves that id against
[`work/OPEN-WORK.md`](../../work/OPEN-WORK.md); a `W-nn` that has closed fails
the check, so a component cannot stay unowned by accident.

<!-- OWNERSHIP-TABLE-START -->

| component | owner | note |
|---|---|---|
| `src/fux/__init__.py` | ADR-LAWS | package identity and version |
| `src/fux/errors.py` | ADR-LAWS | the single flat `FuxError` — CLAUDE.md §Error contract |
| `src/fux/frontmatter.py` | ADR-LAWS | hand-rolled parser — law L1, `$0` stdlib-only |
| `src/fux/config.py` | ADR-CONFIG | `fux.toml` schema; the opaque `[sources.url.config]` table |
| `src/fux/doctor.py` | ADR-DOTFUX | the committed-vs-derived assertions, incl. `git check-ignore` |
| `src/fux/cli.py` | ADR-CLI | the six-verb surface, the boundary error contract, and the `--json` shape |
| `src/fux/store/` | ADR-INDEX-LIFECYCLE | canonical bytes, shard addressing, writer/reader, collisions |
| `src/fux/store/fuxdir.py` | ADR-DOTFUX | the `.fux/` layout generator |
| `src/fux/ingest/` | ADR-INGEST | git-dir walk, parse, edges — writes the committed plane |
| `src/fux/ingest/urlsrc.py` | ADR-URL-INGEST | the URL source and its consumer-owned middleware |
| `src/fux/derive/` | ADR-T1-ACCELERATOR | T1 build, block maxima, skipping, dense lane |
| `src/fux/query/` | ADR-ASK | BM25F, scan, rank, fusion — bound by the differential law |
| `src/fux/embed/` | ADR-T1-ACCELERATOR | `fuxvec` codes; ships default-off on measured evidence |
| `src/fux/refer/` | W-24 | stub — the refer plane is M4 and has no record yet |
| `tools/pruning-eval/` | W-38 | the gate harness and its frozen pre-registrations. **Owned by an open item, not a record** — the verdicts that used it ([P1-GATE](../../work/regression/2026-08-09-pruning-eval/VERDICT.md) · [P1-RERUN](../../work/regression/2026-08-09-pruning-rerun/VERDICT.md)) are no longer ADRs, and W-38 is the only live item permitted to touch pruning work |
| `tools/differential/` | ADR-T1-ACCELERATOR | the differential-law harness and the R3 bench |

<!-- OWNERSHIP-TABLE-END -->

---

## Path note (2026-08-18)

The `work/` move renamed several directories that older records cite:
`docs/conformance/` → `work/regression/`, `docs/compare/` → `work/compare/`,
`docs/open|proposals|archive/` → `work/…`, and `docs/{WORKLOG,INTERVIEW,
OPEN-WORK,DOC-REGISTRY}.md` → `work/…`. ADR filenames also went from
`000N-name.md` to `000N_name.md`.

A second move the same day took `docs/paper/`, `docs/handoff/` and the two
architecture SVGs into `work/`, and the eight v0.30 records into `work/adr/` as
superseded-pending. `docs/` now holds only `GLOSSARY.md`,
`index.md`, and this register with `TEMPLATE.md` and ADR-LAWS.

**ADR-LAWS was renumbered `0013` → `0001`** in the same change, opening the new
sequence. Anything written before 2026-08-18 that says "0013" means ADR-LAWS.

**Re-indexed again, later the same day**, to seat the three query verbs at
0004–0006 on Arpit's instruction: `0004_ingest` → **`0007_ingest`**,
`0005_url-ingest` → **`0008_url-ingest`**, `0006_index-lifecycle` →
**`0009_index-lifecycle`**. Nothing else changed — which is the cite-by-name
rule paying for itself twice in one day: a renumber costs three `git mv`s and a
sweep, and no prose moves.

Live references were rewritten in that same change. **Frozen artifacts were
not** — the pre-registrations under `tools/pruning-eval/` and the run reports
under `work/regression/<date>-*/` still carry pre-move paths, by the same rule
that keeps their pre-renumbering ADR ids: a frozen document is never edited.
Where a record quotes a *measured* path (ADR-RECORD's R2 results), the
path was repointed but the measurement is unchanged.

## Renumbering note (2026-08-09)

These files previously carried numbers 0016–0018 continuing the v0.26 sequence;
all live references were rewritten in the same change. Frozen artifacts
intentionally retain the old numbers — their "ADR-0017/0018" means today's
P1-GATE / P1-RERUN.
