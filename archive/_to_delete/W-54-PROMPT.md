# Claude Code prompt — W-54, the sources rewrite, through to a published release

You are working in `~/my_programs/fux` on `main`. Read `CLAUDE.md` first, then
`work/INTERVIEW.md`, then `work/open/W-54-sources-rewrite.md`. **Model: Opus.**

**There is no second spec.** `work/open/W-54-sources-rewrite.md` is the work
order and the records are the design. Do not write a plan document — this repo's
standing rule is that a second document naming what to do next is always the
stale one. Your plan lives in your head and in the commits.

---

## Step 0 — commit what is already there, first

The working tree has ~72 modified files from a long documentation session:
eight new ADRs, the `middleware` → `fetcher` rename (code + tests, verified
green), six closed work items, and the queue restructure. **None of it is
committed.**

1. `git status --short` and read it. **Some files appear both staged and
   unstaged** — something staged them that was not me. Reconcile before you
   commit; do not `git add -A` over a state you have not read.
2. Run the full suite: `uv sync --extra dev && uv run pytest -q tests && uv run pytest -q tests_e2e`.
3. Commit it as **one docs+rename commit**, message beginning `docs:`, ending
   with `no ADR affected` **only if** that is true — it is not, so cite the
   records instead.
4. **Stop and do not proceed if the suite is red.** A red baseline makes every
   later failure ambiguous.

---

## Step 1 — build W-54, in its five sections, in order

`work/open/W-54-sources-rewrite.md` §What lands gives the order and the reason
for it. The binding records:

| section | record |
|---|---|
| one parser, two files | `ADR-URL-LIST` (0018) decisions 2–13 |
| `dirs` leaves `fux.toml` | `ADR-DIR-LIST` (0023) |
| `fux setup` + the fetchers | `ADR-FETCHER` (0019), `ADR-HTTP-FETCHER` (0021), `ADR-CDP-FETCHER` (0020) |
| the `title_h` fix | `ADR-URL-INGEST` (0008), `ADR-INDEX-LIFECYCLE` (0009) |
| the URL manager verb | `ADR-URL-LIST` (0018) 12–13, `ADR-CLI` (0002) |

**Commit per section, not once at the end.** Each commit: code + tests + the
record it changes, together. Law zero — no behaviour change lands without its
record updated in the same change.

### The five hazards, restated because they are the whole risk

1. **One parser, not two.** `urls` and `dirs` share it. Two parsers for one
   grammar is how `#`-handling, sorting and the unknown-key error end up
   disagreeing.
2. **Do not relax the accelerator invariant** in `derive/build.py`. Fix the
   *field shape* — `title_h` becomes `"h:" + term_hash(...)` — so `scan.py`'s
   raw-byte regex stops matching and the two paths agree by construction. Strip
   the prefix in `query/rank.py:90` and `derive/build.py:143`.
3. **Do not switch the URL `meta` default to `plain`.** L5 is a law.
4. **`ensure_layout` never writes a fetcher.** `fux setup` does. Ingest must not
   put code into a repo that only wanted an index.
5. **Do not derive `archived` from the path.** Declared on a line, never
   inferred. `ADR-DIR-LIST` replaced its own predecessor over exactly this.

### Two things W-54 leaves to you, deliberately

- **The `title_h` migration.** A committed index already holding a bare
  `title_h` must be re-ingested. Decide whether that warrants an `analyzer` or
  `_format` bump, and write the reasoning into `ADR-INDEX-LIFECYCLE`.
- **`ADR-CLI`'s mental model.** Two new verbs take the surface from six to
  eight, and its §1 sentence — *"three build the index and three query it"* —
  stops being true. W-54's closing section proposes lifecycle / write / sources
  / read. Settle it **in** the amendment. **"No subcommand tree" is the
  constraint that survives**: the URL manager takes flags, it does not become
  `fux url add`.

---

## Step 2 — verify, and understand why the normal suite is not enough

**This repo does not exercise the URL path.** There is no `.fux/sources/urls`
and `[sources.url]` is commented out in `fux.toml`. `pytest -q tests` passing
tells you **nothing** about four of the five defects you just fixed.

- **Extend** `work/regression/2026-08-18-ingest-and-index/evidence/fixture.sh`
  to cover: a hashed URL record that ingests **and builds** (exit 0, manifest
  present); a fragment-bearing URL surviving round-trip; two URLs differing only
  by fragment producing two records; a fresh tree with no hand-written fetcher.
- **File a regression run** under `work/regression/<date>-w54/` with `report.md`
  and `ANALYSIS.md` — every measurement run is filed, no exceptions.
- Assert the differential: scan and accelerator return identical scores on a
  corpus containing a hashed record. **That harness has never seen one.**
- `bash scripts/adr-guard.sh` and both suites must be green.

---

## Step 3 — close the item

- `work/IMPLEMENTATION.md` — the outcome row.
- Delete W-54's row from `work/OPEN-WORK.md`; move
  `work/open/W-54-sources-rewrite.md` to `archive/open/` and add its row to
  `archive/README.md` naming the live successor. **The row is deleted, the file
  is archived** — that is the 2026-08-19 rule.
- `docs/adr/README.md` — flip the **`built`** column to `yes` for
  `ADR-URL-LIST`, `ADR-HTTP-FETCHER` and `ADR-DIR-LIST`.
- `work/DOC-REGISTRY.md` — a row bump for every doc touched.
- `work/WORKLOG.md` — one entry, with its `Cost:` line.
- `work/INTERVIEW.md` — kept current *during* the work, not at the end.

---

## Step 4 — release `v0.33.0`

Only if everything above is green.

1. `src/fux/__init__.py`: `0.32.0` → `0.33.0`. It is the single source;
   `pyproject.toml` reads it dynamically.
2. `CHANGELOG.md`: move `[Unreleased]` into `## [0.33.0] - <today>`.
   **Two retired keys are breaking** — `[sources.url] middleware` and
   `[sources] dirs` — and both must be called out with the migration in the
   entry, not just in a record.
3. Commit `release: v0.33.0 — <one line on what it is>`, in the register of the
   `v0.32.0` commit: what shipped, the measured claim, the honest limits.
4. `git tag v0.33.0 && git push origin main --tags`.
5. `gh release create v0.33.0 --notes-from-tag` — the GitHub Release is what
   triggers `.github/workflows/publish.yml`, which publishes to PyPI over OIDC
   trusted publishing. **Do not run `twine` by hand.**
6. `gh run watch` on the publish workflow. **CI green is your responsibility to
   check** — the merge wall does not guarantee it. Do not report success until
   the workflow is green and the version is live on PyPI.

---

## Standing rules you will be judged against

- **Every ADR up to date, in the change that would make it wrong.** Not at the
  end. `scripts/adr-guard.sh` enforces it; `no ADR affected` in a commit message
  is a *claim under your name*, not a skip.
- **Records are cited by name** — `ADR-RECORD`, never `ADR-0010`.
- **Archive is not evidence.** A doc under `archive/` may be named, never cited
  as backing a live claim, and archived filenames are history — never rename one.
- **Never edit a past `WORKLOG` entry.** Append.
- **If something is wrong in the plan, say so and stop.** W-54 was assembled
  from five items in one sitting; if a section contradicts a record, the record
  wins and the item is the defect.
