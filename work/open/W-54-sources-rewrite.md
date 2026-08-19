# W-54 — the sources rewrite: one parser, two files, and the URL path made to work

**Status:** OPEN (Lane A — agent-executable) · **Filed:** 2026-08-19
**Blocked by:** — · **Model:** **Opus.** Five previously separate defects that
share one parser and one generated set; the judgement is in the sequencing and
the record amendments, not in any single change.
**Spec:** the records below, all accepted; **this file is the work order, not a
second spec**
**Merged from:** W-47 · W-49 · W-50 · W-51 · W-53, 2026-08-19 (Arpit) — their
detail files are at [`archive/open/`](../../archive/open/), **merged, not
completed**

## Why one item

Each of the five carried a hazard section saying *land it with the others*.
They rewrite the same parser, the same generated set, and the same three
records. Five definitions of done for one change is the drift they each warned
about, written into the queue — and it made the queue's length lie, which is the
one thing [`OPEN-WORK.md`](../OPEN-WORK.md) rule 2 says it must not do.

**They are still five defects.** They are one *change*.

## What lands, and in this order

### 1. One parser, two files

`.fux/sources/urls` and `.fux/sources/dirs` share one reader. Grammar:
[ADR-URL-LIST](../../docs/adr/0018_url-list.md) decisions 2–13 — one entry per
line, `#` comments, dedupe and sort, `<entry> key=value …`, unknown key a loud
`file:lineno` error, duplicate-with-conflict an error, reader lenient and writer
strict.

**Do not write two parsers.** That is the drift this merge exists to prevent.

- **`#` begins a comment only at line start or after whitespace** — was W-49.
  Under a whitespace-delimited grammar it is forced, not chosen:
  `https://x/a#frag meta=plain` cannot otherwise parse. Fixes the silent
  fragment truncation that collapsed two URLs into one and dropped a document
  with no error.
- Attribute sets are per file and closed: `fetch` + `meta` for urls,
  `archived` for dirs.

### 2. `dirs` moves out of `fux.toml`

[ADR-DIR-LIST](../../docs/adr/0023_dir-list.md) — was W-53. `[sources] dirs`
becomes a retired key that errors with instructions. This repo's list migrates,
with `archive/v0.26-docs   archived=true`. **Write the declaration; do not read
it yet** — the annotation in results is [W-44](W-44-archived-content-signalling.md),
parked behind its instrument.

### 3. The fetchers become real — via `fux setup`

**Arpit, 2026-08-19: the fetchers are written at setup time, by a `fux setup`
verb.** Both of them — `http.py` and `cdp.py` — ship in the wheel as **package
data** (bytes, never imported, so the adapter cap holds) and are written
**write-if-missing** into `.fux/fetchers/` when a consumer runs setup. That
answers what W-51 could not: `DEFAULT_FETCHER` names a file that will exist,
without 28 KB of WebSocket code appearing unasked-for on someone's first
ingest, and without telling an air-gapped consumer to copy a file from GitHub.

Correct the two docstrings that claimed this already happened.

**Scaffolding now has two moments, and the split is deliberate:**

| moment | writes | why |
|---|---|---|
| `fux setup` | the fetchers, and the source-list files with their headers | **optional, explicit, once per repo.** A consumer asked for it |
| `ensure_layout`, at ingest | `.fux/README.md`, `.gitignore`, the directory structure | **mandatory and idempotent** — a fresh clone must be correct before a byte is written ([ADR-DOTFUX](../../docs/adr/0003_fux-directory.md) decision 6, ratified by Arpit in W-31 this morning) |

**`ensure_layout` must never write a fetcher.** That is what keeps ingest from
putting code into a repo that only wanted an index.

### 4. The hashed-meta defect

Was W-47, and it is the one with measured cost: `meta = "hashed"` is the
default and an L5 default, and under it `fux ingest --refresh-urls` writes an
index **no `fux build` will ever accept** — 27.2 ms becomes 4 248.8 ms at RFC
scale, the whole M2 result forfeited by following the documentation.

Fix the **field shape**, not the check: `title_h` becomes `"h:" + term_hash(...)`
so `scan.py`'s raw-byte regex stops matching it and the two paths agree *by
construction*. Strip the prefix in the two display-fallback readers
(`query/rank.py:90`, `derive/build.py:143`). **Decide the migration** — whether
a bare `title_h` in a committed index warrants an `analyzer` or `_format` bump.

### 5. The managing command

[ADR-URL-LIST](../../docs/adr/0018_url-list.md) 12–13 + W-50's ruling. A verb
that fetches a URL and **writes it plus every attribute** into the list; the
file is not edited by hand. `--cdp` / `--hash` decide what is *recorded*, never
what is fetched at ingest time — which is why the same list can never produce
different committed bytes on different invocations.

## Definition of done

- [x] One parser, both files, the comment rule fixed. `ingest/sourcelist.py`,
      2026-08-19 — `urls` built on it; `dirs` follows in the next change.
- [x] `dirs` migrated; the old key errors with instructions (whatever its
      value). This repo's list is `.fux/sources/dirs`, 2026-08-19.
- [x] `fux setup` writes both fetchers write-if-missing from wheel package
      data; `ensure_layout` writes **no** fetcher; `DEFAULT_FETCHER` resolves to
      a file that exists after setup. Verified from an installed wheel, not
      just the source tree, 2026-08-19.
- [x] `title_h` prefixed; the differential harness sees a hashed record for the
      first time; ingest-then-build exits 0 on the `meta = "hashed"` default.
      **Migration decided:** no `analyzer` or `_format` bump —
      ADR-INDEX-LIFECYCLE decision 9 carries the three conditions and the
      asymmetric-cost argument; the migration is `fux ingest --refresh-urls`
      and the build names it.
- [ ] The managing verb, writing every attribute explicitly.
- [ ] **Tests, per defect** — not one integration test standing in for five:
      a fragment survives round-trip and two fragment-differing URLs make two
      records · an unknown key errors at `file:lineno` · a duplicate with
      conflicting attributes errors · the two retired keys error · file order
      does not change committed bytes · a fresh tree ingests URLs with no
      hand-written fetcher · `ensure_layout` does not overwrite an edited
      `http.py` · scan and accelerator return identical scores on a corpus
      containing a hashed record.
- [ ] **Records amended in the same change** — Law zero:
      [ADR-CONFIG](../../docs/adr/0014_config.md) 2,
      [ADR-DOTFUX](../../docs/adr/0003_fux-directory.md) 2,
      [ADR-URL-INGEST](../../docs/adr/0008_url-ingest.md) 3,
      [ADR-CLI](../../docs/adr/0002_cli-surface.md) — **two new verbs, `setup`
      and the URL manager, taking the surface from six to eight.** Its §1
      mental model is *"three build the index and three query it"*, and that
      sentence stops being true; the record needs a grouping that survives
      (lifecycle: `setup`, `doctor` · write: `ingest`, `build` · sources: the
      manager · read: `ask`, `find`, `answer`) —
      [ADR-URL-LIST](../../docs/adr/0018_url-list.md) (written for a
      human-maintained file; comments and duplicates change meaning under a
      lockfile), and the **`built` column** in
      [the register](../../docs/adr/README.md) for ADR-URL-LIST,
      ADR-HTTP-FETCHER and ADR-DIR-LIST.
- [ ] `CHANGELOG.md` — `Fixed` for the defects, `Changed` **flagged breaking**
      for the two retired keys.
- [ ] Outcome in [`../IMPLEMENTATION.md`](../IMPLEMENTATION.md); this file
      archived and its row deleted.

## Hazards

- **Do not relax the accelerator invariant** (§4). It is what stands between the
  engine and a fast wrong answer. The field shape is the bug.
- **Do not switch the URL `meta` default to `plain` to dodge §4.** That trades a
  correctness bug for a privacy one, and L5 is a law.
- **Do not ship a fetcher inside the wheel and import it.** A fetcher fux
  imports is a fetcher fux owns, and the adapter cap is gone.
- **Do not derive `archived` from the path.** Declared, never derived — the
  reason ADR-DIR-LIST replaced its predecessor.
- **`ensure_layout` never overwrites.** An overwriting generator eats every
  fetcher edit on the next ingest.

## Note

**This repo does not exercise the URL path** — there is no `.fux/sources/urls`
and `[sources.url]` is commented out in `fux.toml`. Every defect here is
therefore latent: shipped, real, and with no current victim. It is being fixed
anyway, on Arpit's call (2026-08-19), because the first consumer hits all five
on day one, on the documented default. **The fixture in
[`work/regression/2026-08-18-ingest-and-index/evidence/`](../regression/2026-08-18-ingest-and-index/evidence/fixture.sh)
is the only thing that exercises it — extend that, do not trust this repo's own
corpus to catch a regression here.**


## The question `fux setup` raises, and does not answer

**A seventh and eighth verb break ADR-CLI's stated mental model.** The record
opens with *"`fux` has **six verbs and no subcommand tree**. Three of them build
the index and three of them query it, and the split is the whole mental
model."* Two more verbs and that sentence is false — and the fix is not to
count differently, it is to find the grouping the surface actually has now.
Proposed, to be settled **in** the amendment rather than after it:

| group | verbs | |
|---|---|---|
| lifecycle | `setup` · `doctor` | set the repo up, then check it |
| write | `ingest` · `build` | one writes the committed plane, one derives from it |
| sources | the URL manager | records what to index |
| read | `ask` · `find` · `answer` | differ only in how much they commit to |

**"No subcommand tree" is the constraint to preserve**, and it is the reason the
URL manager takes flags rather than becoming `fux url add`. Eight flat verbs is
still not a tree.
