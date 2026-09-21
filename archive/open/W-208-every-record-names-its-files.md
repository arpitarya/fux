---
type: OpenItem
id: W-208
title: "W-208 — every record names the files and folders it governs, Node included: 35 unowned paths, 13 ungated component records, 28 node files no record names"
description: "Arpit, 2026-09-21: review all the records and link files or folders into each and every SR, even the node ones. Audited the same day against the ownership model (SR-WORK-OWNERSHIP, records/README.md §Ownership and §Describes, tests/sr_lib.py). This file is the ratified disposition: which path each record gains, and a generated Components block so the links can never drift from the table."
status: open
lane: agent
timestamp: 2026-09-21T00:00:00Z
filed: 2026-09-21
ball: agent
ruled: 2026-09-21
---

# W-208 — every record names its files

**Model: Opus for step 1** (a new generated block in every record is a
SR-LAW-0 decision 5 view, and the wrong shape restates the table); **Sonnet for
steps 2–5** — every path below is decided, what remains is frontmatter edits,
table rows, a script and its byte-equal test.

**The model that already exists, and is kept:** `owns:` in frontmatter (path +
content hash, freshness-gated), the OWNERSHIP table in `records/README.md`
(the executable twin `tests/sr_lib.py` reads), and the additive DESCRIBES
table for a record whose subject reaches into a component another record owns.
**This item adds no third relation.** It fills the two that exist and makes the
body of every record show what its frontmatter claims.

**The audit (2026-09-21, read-only):** 288 paths walked; **35 with no owner**;
**13 `kind: component` records with `owns: []`** (the list README §"thirteen
ungated" already names); all 47 authored `node/*.mjs` resolve to SR-NODE-SEARCH
by the `node/` prefix, but **28 of them are named by no record at all** and
**no DESCRIBES row points at any node file** even where another record's whole
subject lives there; SR-WORK-SESSION names **zero** code paths. The four
ownership tests pass — every gap is one the tests do not measure.

---

## 1 · A generated **Components** block in every record (the mechanism)

Linking 89 records by hand is the restatement L0 forbids: the body and the
table would drift the first week. So the link is **generated from the tables**:

- `scripts/gen-components.py --write` renders, into every record with a
  non-empty `owns` or any DESCRIBES row, a block between
  `<!-- COMPONENTS-START -->` / `<!-- COMPONENTS-END -->` directly under the
  frontmatter: **Owns** — each path as a relative link, one per line, with its
  kind (`file` / `dir`); **Describes** — each `path::symbol` the table names,
  with the owning record linked. A record that owns and describes nothing gets
  the one line *"Owns nothing — SR-WORK-OWNERSHIP decision 7, case (a|b)"* or,
  for a law, nothing.
- `tests/test_record_components.py` holds every block byte-equal to the
  generator's output — the `gen-laws.py` / `test_claude_md_laws.py` pattern,
  which is the only form of a generated view SR-LAW-0 decision 5 permits.
- `tests/test_doc_links.py` already resolves every relative link, so a path that
  moves fails the build in two places.

**So "link files into every SR" is one script and one table edit per record,
never a prose edit** — and the DOC-REGISTRY's own rule 1 (no row for a generated
view) is respected by recording the block beside SR-WORK-OWNERSHIP, not in the
registry.

## 2 · The 35 unowned paths — who gains them

| path | gains it | as |
|---|---|---|
| `.fux/decoders/*.py` (18 twins of the built-ins) | SR-DECODE | owns (dir) — a twin that moves without its template fires the freshness gate, which is the point |
| `.fux/fetchers/cdp.py` · `src/fux/templates/cdp.py.txt` | SR-CDP-FETCHER | owns (carved out of SR-FETCHER's dir claim) |
| `.fux/fetchers/http.py` · `src/fux/templates/http.py.txt` | SR-HTTP-FETCHER | owns (same carve-out) |
| `.fux/tune.toml` | SR-TUNE | owns |
| `.fux/output.toml` | SR-OUTPUT | owns |
| `.fux/pii.toml` | SR-PII | owns |
| `.fux/refusals.toml` | SR-REFUSAL | owns |
| `.fux/formats.toml` | SR-TYPES | owns |
| `scripts/sr-guard.sh` · `scripts/sr-hash.py` · `scripts/sr-owns.py` · `tests/sr_lib.py` · `tests/test_sr_*.py` | SR-WORK-OWNERSHIP | owns — its own veto 6 already flags that it owns nothing; decision 7's case (b) is withdrawn for it |
| `scripts/gen-laws.py` · `scripts/gen-golden.py` · `scripts/gen-components.py` | SR-LAW-0 | owns — decision 5 is what they render |
| `scripts/check-open-work-inbox.py` · `.claude/hooks/guard-open-work-inbox.sh` | SR-WORK-OPEN-QUEUE | owns |
| `scripts/commit-paths.py` · `.claude/hooks/require-progress.sh` | SR-WORK-SESSION | owns — the record that names zero code paths today |
| `.claude/hooks/fux-index-hint.sh` | SR-AGENT-SURFACES | owns |
| `tests/` (the directory) | **no owner, by decision** — each process record owns its enforcing test file; a directory claim would make every test's owner SR-X and the per-file rule meaningless. README §Ownership says so in one sentence |
| `tests_e2e/` (the directory) | SR-CLI | owns — *the package as a user* is the CLI surface; SR-FIND, SR-ANSWER, SR-PROVENANCE, SR-OUTPUT gain DESCRIBES rows on `tests_e2e/test_verbs.py` |

## 3 · The thirteen ungated component records — each claims or describes

| record | gains |
|---|---|
| SR-FIND (0104) | describes `src/fux/query/__init__.py::cmd_find` |
| SR-ANSWER (0105) | owns `src/fux/query/refer_answer.py` (carve-out from SR-ASK; README row already calls it "the seam") |
| SR-URL-INGEST (0107) | describes `src/fux/ingest/urlsrc.py::fetch_all`, `ingest/run.py::<the url branch>`, `maintain/dirty.py` |
| SR-RECORD (0109) | owns `src/fux/store/index-record.schema.json`; describes `store/format.py`, `store/writer.py`, `store/canonical.py` |
| SR-CDP-FETCHER (0118) · SR-HTTP-FETCHER (0119) | owns per §2 |
| SR-DIR-LIST (0120) | describes `src/fux/ingest/gitdir.py`, `ingest/sourcelist.py::<the dirs grammar>` |
| SR-CACHEDIR-TAG (0121) | describes `src/fux/store/fuxdir.py::<the tag writer>` |
| SR-DOCS-TABLE (0122) · SR-RUNTIME-MANIFEST (0123) · SR-RUNTIME-STAMP (0124) · SR-RUNTIME-STATS (0125) | **honest case (a), now stated in each body** (runtime companion of `derive/_build.py`); each gains describes rows on `src/fux/derive/_build.py`, `derive/format.py` (+ `derive/accel.py`, `query/bm25f.py` for STATS) |
| SR-LOCKS (0140) | honest case (b), already stated; gains describes `store/fuxdir.py`, `maintain/runner.py`, `maintain/daemon.py` |
| SR-WORK-GOVERNANCE (0065) | owns `tests/test_record_paths_resolve.py`, `tests/test_work_queue_rules_have_one_home.py`; the other eleven test files it names are owned by their own records and linked from the Components block, not re-owned |

## 4 · Node — the reader gets named, file by file

- SR-NODE-SEARCH keeps `node/` whole (README's "44" becomes **47**, counted by
  `git ls-files`, and the Components block lists all 47 — that alone closes
  the "28 files no record names" gap).
- **DESCRIBES rows added** where another record's whole subject lives in a node
  file: SR-URL-FRESHNESS → `node/src/refer/freshness.mjs`, `refer/source.mjs` · SR-OUTPUT → `node/src/config/output.mjs` · SR-RANKING → `node/src/query/rank.mjs` · SR-MCP → `node/src/verbs/mcp.mjs`, `node/mcp-tools.json` · SR-ENRICH → `node/src/correct.mjs` · SR-DECODE → `node/src/decode/registry.mjs` · SR-API → `node/src/index.mjs` · SR-WORK-RELEASE → `node/dist/fux.mjs` (the L10 artefact, named not owned — it is build output).
- `node/test/config.test.mjs` and `node/test/pins.test.mjs` are named by no
  record: SR-CONFIG and SR-ENRICH (pins) gain describes rows.

## 5 · The other DESCRIBES rows the audit found obvious

SR-FIND → `query/__init__.py` · SR-RUNTIME-STATS, SR-PROVENANCE → `query/scan.py` · SR-POSTINGS → `store/collisions.py` · SR-DIR-LIST, SR-FUXIGNORE, SR-TYPES → `ingest/gitdir.py` · SR-CACHEDIR-TAG, SR-LOCKS → `store/fuxdir.py` · SR-LOCKS → `maintain/runner.py`, `maintain/daemon.py`.

---

## Definition of done

1. `scripts/gen-components.py`, `tests/test_record_components.py`; the block
   present in all 89 records; SR-WORK-OWNERSHIP gains a decision naming the
   block as the one permitted body form of the tables (SR-LAW-0 d5 view) and
   retracts its own case-(b) claim; README §Ownership gains the `tests/` sentence.
2. Every row in §2–§5 landed: frontmatter `owns` (with hashes via
   `scripts/sr-owns.py`), OWNERSHIP and DESCRIBES table rows, and the carve-outs
   (SR-FETCHER's dir claim minus the two templates; SR-ASK minus
   `refer_answer.py`) — with `RULE-SINCE` entries where a rule's scope moved.
3. The four honest-case records (0122–0125) and SR-LOCKS say in their body
   which case they are.
4. `python3 -m pytest -q tests/test_sr_ownership.py test_sr_owns_consistency.py test_sr_owns_hash.py test_sr_freshness.py test_record_components.py test_doc_links.py test_record_paths_resolve.py` green; then both suites whole.
5. WORKLOG entry with the counts (unowned 35 → 0 by decision; ungated 13 → 0;
   node files named 19 → 47); registry rows for `records/` and `scripts/`.

## Out of scope

- A third relation (e.g. "tests"). Owns + describes is the model; this item
  fills it.
- Re-deciding any existing owner. A carve-out moves a file to the record whose
  subject it is; nothing else moves.
- `node/compat/`, `node/hash/` — exempt by SR-NODE-SEARCH's own decision; they
  appear in the block as owned, nothing more.
