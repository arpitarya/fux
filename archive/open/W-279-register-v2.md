---
type: Handoff
name: W-279
description: "Arpit's ruling (2026-10-13, Cowork, closing W-266): the committed register `.fux/index/REGISTER` moves to shape S1 — a `# fux.register.v2` format line, three tab-separated columns (loc, sha, decoder) and an optional `k=v` tail in the sources-list grammar — plus a new read-only verb `fux register [--json]` that prints the same rows from the index for machines, never committed. The build: register.py render and read by header, constants, SR-INGEST d22 rewritten to the real columns, doctor's three states, the verb in SR-CLI, tests."
item: W-279
filed: 2026-10-13
ball: agent
---

# W-279 — the register, shape S1, and `fux register --json`

**Status: CLOSED 2026-10-13 (Claude Code, Fable 5.1) — built as filed, DoD 1–6.**
SR-INGEST d22 rewritten in place (22c, 22d new); SR-CLI decision 18 and the
`fux register` block; `constants.toml [register]`; `register.py` renders v2,
reads by header, keeps unknown keys, refuses an unknown key on write; a URL
row's decoder and `fetch=` come from the committed list, not the run; doctor's
three states; the verb in Python; the merge driver keeps both header lines;
X-ray, explorer and facts read the v2 row; this repository re-ingested; 26
unit tests and 4 e2e tests. **Open after this item:** the section-split key
(DoD 7) — Arpit's pick, landing with W-273 phase 2;
[W-273's item file](../../work/open/W-273-section-records-implementation.md) carries it.

Filed 2026-10-13. Ruled by Arpit in Cowork on
2026-10-13 after the W-266 research was given in chat: *"s1 + fux register
--json"*. [W-266](../../archive/open/W-266-register-structure.md) is closed on
that ruling; its compare doc was not written — the comparison lived in chat at
his word, and §Why below keeps the part a future reader needs.

**Model:** Claude Code, **Opus** — a committed-plane format change, a record
rewrite, and a new verb.

## Why — what the file says today (measured 2026-10-13, this repo, 2 363 rows)

- `kind`: 2 363 of 2 363 rows say `file`. The one `url` value is visible from
  the `loc`.
- `fetcher`: 2 363 of 2 363 rows say `-`, a sentinel marking a non-field.
- `decoder`: two grammars — `prose` bare (1 364 rows) against
  `jsonl@sha:3ea594342cc73092` (603), `json@sha:…` (294), `csv`, `html`, `svg`,
  `toml`, `yaml` with digests.
- The reader is positional (`loc, kind, sha, decoder, fetcher = line.split("\t")`,
  `continue` on error): one added column makes `fux doctor` report *"no
  REGISTER beside an index of 2 363 documents"*. Wrong message, total failure.
- No format marker.
- `archived=true`, declared on the `archive` entry of `sources/dirs` (605 rows),
  is the one useful attribute the file lacks.
- **A record defect:** [SR-INGEST](../../records/0106_ingest.md) decision 22
  still states the columns as `loc · sha · decoder@version · fetcher ·
  outcome`; the file carries `kind`, not `outcome`, and only `register.py`'s
  docstring says why. The record and the code disagree while both look correct
  (L0's restatement test), and d22's `tests/…` link is a placeholder.
- Only reader: `doctor.py::_register`. Node and `tools/` do not read it.

**The shapes Arpit saw and what he refused.** S2 (S1 grouped by source entry):
seven headers on this repo, a stateful reader, a first-wins rule for a document
reachable from two entries — refused. JSONL: growth-safe but unreadable in a
PR — refused as the committed file; **it is the `--json` output of the verb
instead.** TOML/YAML (multi-line per document, diffs balloon; YAML needs a
dependency), Markdown table and CSV (positional again) — refused. A new
indented tree format (directories once, ≈ 86 KB saved of 304 KB): a row then
depends on the lines above it, a rename is a two-place diff, no tool knows it —
refused. **Two committed files, one for humans and one for machines:** the
machine's register already exists — it is the index record (`loc`, `sha`,
`src`, `archived`, `nsec`) — so a second committed copy would be a subset of
the shards sitting beside them, with its own drift. **Hence S1 + a verb.**

## The shape — S1 (to be stated in SR-INGEST d22 at DoD 1)

```
# fux.register.v2	rules=5
# loc	sha	decoder	[k=v ...]
CHANGELOG.md	e204170f5723f264be83b66ebdd6a7ee5c1fc9e0	prose
archive/PLAN-v0.30.md	2e0ef4e71c9f6d31558cf644bbf0da82c0af9b1d	prose	archived=true
archive/handoff/W-98-refusals-starter.toml	df910163da375301421bc54f7127a852e63a83ab	toml@sha:e547627e15b0eeba	archived=true
work/regression/2026-08-28-annotator-agreement/evidence/per-query.csv	d8369d3ec03afc0fce1e6aff16cdeb26f8063157	csv@sha:2c37b28e4a9f6292
https://wiki.example/ops/cold-store	9c1f0b2e7a4d5e6f8091a2b3c4d5e6f708192a3b	html@sha:773b7cb1d9a7be6e	fetch=cdp
```

- **Line 1, the format line:** `# fux.register.v2` and `rules=<extract.RULES_VERSION>`.
  `rules=` answers *"did the built-in decoder change"* once, for every bare
  `prose` row, instead of digesting 1 364 rows and churning them all on every
  fux upgrade. **Rule:** no `@sha:` tail = read by code shipped with fux at that
  rules version; a `@sha:` tail = read by consumer code in `.fux/decoders/`.
- **Line 2, the column header**, kept so a reader knows the spine without this
  module; **part of the bytes** (L4).
- **Three columns**, tab-separated: `loc`, `sha`, `decoder`. The tab after `loc`
  is what the whitespace-split sources grammar cannot give: walked paths carry
  spaces; a sources entry may not (SR-URL-LIST d8).
- **The tail**: zero or more `key=value`, no whitespace in a value, present only
  when it holds a value — **no sentinel**. Keys in v2: `archived=true` (from the
  source list's declaration on the record), `fetch=<name>` (URL rows with a
  fetcher). `superseded=true` is a candidate — declared on the record — and may
  join at DoD 1 if the record carries it on every document; otherwise it waits.
  🔴 **A section-split key is Arpit's ask (2026-10-13, Cowork: *"once done in
  registry i want something which tells me about section split as well"*)** —
  shown to him in chat as `sections=<n>` (free: `nsec` is on the record) with
  or without per-section line starts (`at=L1,L29,…`, which needs a `line`
  field on each section record — an SR-SECTIONS decision 3 amendment). **His
  pick is pending; whichever he picks lands only after section records reach
  `main` (W-273 phase 2), as a DoD 7 here or a follow-up item.** Until then the
  key is absent, and on a repo with `[index] section_records` off it stays
  absent.
- **Not on a row, by decision:** `kind` (visible from `loc`), `mode` (always
  `extracted`), titles or any display text (L3), anything run-shaped —
  `outcome`, timestamps, run ids (L4; d22's own story), anything naming a
  question, query or reader (L9).
- **Sorted by `loc`**, trailing newline, written only when bytes change,
  best-effort as today.
- **The reader** parses by the header, never by count: `loc, sha, decoder,
  *attrs = line.split("\t")`; `attrs` by `partition("=")`; **unknown keys are
  kept**. A v1 file (header `# loc\tkind\tsha\tdecoder\tfetcher`) is
  recognised as *old format*, not read as rows.

## `fux register [--json]` — the machine's view, derived, never committed

- Read-only, offline, no index write. Prints the register's rows **from the
  index** (the records plus the decoder digest table), so it cannot drift from
  it; the committed file is what a PR shows, the verb is what a program calls.
- Default output: the S1 text exactly as the file would be written — so
  `fux register | diff - .fux/index/REGISTER` is the drift check by hand.
- `--json`: JSONL, one object per document, keys `loc`, `sha`, `decoder`
  (`{"name", "digest"}` with `digest: null` for shipped decoders), `rules`, and
  every tail key by name. No prose in `--json` (SR-CLI's output contract).
- Not an L9 artifact: it names documents, never a question. Not a second
  committed file.

## Definition of done — in this order

1. **Record first (L0).** [SR-INGEST](../../records/0106_ingest.md) decision 22
   rewritten in place to v2: the format line, the three columns, the tail keys
   and the rule for `@sha:`, what stays off a row, the reader's contract, the
   migration; the placeholder test link replaced by
   [`tests/ingest/test_register.py`](../../tests/ingest/test_register.py).
   [SR-CLI](../../records/0101_cli-surface.md) gains `fux register` (read-only
   verb, its flags, exit codes by decisions 4–5). `constants.toml [register]`:
   `format = "fux.register.v2"`, the header, the key list (L12).
   [`.fux/README.md`](../../.fux/README.md)'s `index/` row names the register.
2. **`register.py`:** render v2; read by header; v1 detected and reported as
   old format; unknown keys kept. `run.py::_record_register` passes `archived`
   and the fetcher through; `rules=` from `extract.RULES_VERSION`.
3. **`doctor.py::_register`** reports three states, named: *missing* (no file),
   *old format — run `fux ingest`* (v1 header), *drift* (22b, unchanged). The
   first state's message stops naming a count that is not about the register.
4. **`fux register [--json]`** in the CLI, registered like every read-only verb;
   the fux skill/steering that lists verbs updated under decision 15's rules.
5. **Migration:** the next `fux ingest` writes v2 — one commit per consumer
   repo; this repository re-ingested in the same change. CHANGELOG: *Changed*
   (not Breaking: nothing a consumer runs reads the file).
6. **Tests:** two consecutive ingests write identical bytes (the d22 gate,
   existing, now against v2); a v1 file → *old format*, not *missing*; a row
   with an unknown `k=v` is kept; `archived=true` appears on exactly the
   documents under an `archived=true` entry; a URL row carries `fetch=` and a
   file row carries none; 22b's drift unchanged; `fux register` output equals
   the file's bytes on a current index; `--json` round-trips the same rows.
   Both suites, whole.

## Hazards

- ⚠ **L4:** `rules=` on the format line changes the file on an engine rules
  bump — correct (the built-in decoder did change) and stated. Nothing else on
  the file may depend on anything but the sources and the engine.
- ⚠ **L3:** paths and hashes only. A tail key that carries display text is a
  record change, not a config addition.
- ⚠ **L9:** the verb prints documents, never queries; no `--since`, no reader.
- ⚠ Keep the tail's key set **closed** in the record, like the sources lists'
  (`sourcelist.py` refuses an unknown attribute on write); the *reader* keeps
  unknown keys only so an older engine survives a newer file.

## Records this will touch

SR-INGEST (d22, rewritten in place) · SR-CLI (the verb) · SR-CONSTANTS /
`constants.toml [register]` · SR-DOTFUX (`.fux/README.md` row) · SR-AGENT-POLICY's
verb list · CHANGELOG.

## Key files

`src/fux/ingest/register.py` · `src/fux/ingest/run.py::_record_register` ·
`src/fux/doctor.py::_register` · `src/fux/constants.toml [register]` ·
`src/fux/cli.py` (the verb) · `tests/ingest/test_register.py` ·
`tests/test_doctor_fetcher_routes.py`.

## Reference

- [W-266](../../archive/open/W-266-register-structure.md) — the research and
  the candidate table (closed on this ruling).
- [SR-INGEST](../../records/0106_ingest.md) d22, 22a, 22b ·
  [SR-URL-LIST](../../records/0116_url-list.md) d8 (the `k=v` grammar, no
  whitespace in a value) · [SR-CLI](../../records/0101_cli-surface.md) d4–5.
- Laws: L0, L3, L4, L9, L12.
