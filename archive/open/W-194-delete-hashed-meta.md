---
type: OpenItem
id: W-194
title: "W-194 — delete meta=hashed: URL records are plain, the meta knob goes, L5 retires"
description: "BUILT 2026-09-20. Arpit's ruling 2026-09-17 — hashed meta is removed outright. `meta` exists for URLs only, so removing `hashed` deletes the whole attribute, the `title_h` field, the display cache and the write-time policy assert, and retires L5. fux.index bumps to v4. BUILT 2026-09-20."
status: closed
lane: agent
timestamp: 2026-09-17T00:00:00Z
filed: 2026-09-17
closed: 2026-09-20
ball: agent
---

# W-194 — delete `meta = "hashed"`

**Model: Opus** — it retires a law, changes the committed record shape and bumps
the index schema. Three record classes move together and a laws test is
byte-gated on the result.

✅ **BUILT 2026-09-20 (Claude Code, Opus 5).** This file is the decision and the
spec; **§Built at the end is what actually landed**, including six places the
delivered change differs from what is written below.

## The ruling

> **Arpit, 2026-09-17:** *"url meta=hashed remove it keep only plain."*

Two scoping answers given in the same exchange:

1. **Delete outright**, the `fux update` precedent (W-177) — `meta=` is not
   accepted anywhere any more, and an unknown attribute is a hard error. No
   deprecation window, no accept-and-ignore.
2. **Drop `title_h` from the record shape** and bump `SCHEMA_ID` to
   `fux.index.v4`. Existing indexes rebuild.

## Why the knob disappears entirely

`meta` exists **for URLs only** — stated in
[`SOURCES-SKILL.md`](../../src/fux/templates/agents/SOURCES-SKILL.md) §214 and
enforced by [`sourcelist.py`](../../src/fux/ingest/sourcelist.py) line 334, whose
attribute set is `("plain", "hashed")` defaulting to `hashed`. A two-valued
attribute with one value left is not an attribute. So "remove hashed" and
"remove `meta`" are the same change, and the record stops having two forms.

**L5 retires with it.** [SR-LAW-5](../../records/0007_LAW-5-hashed-meta.md) *is*
hashed meta — there is no residue of the law once the mechanism is gone. It
retires the way **L9 did on 2026-09-13**: struck through in the
[SR-LAWS](../../records/0001_LAWS.md) table with a dated RETIRED note, the
record itself moved to `status: superseded` and kept, **and the handle L5 is
never reused.**

⚠ **What the retirement does NOT undo.** L5 closed a real ACL-mismatch leak: a
title alone tells a reader that a document they cannot open exists. That leak
becomes an **accepted, documented exposure**, not a solved problem. The
superseding record must say so in those words, and must keep the AOL-2006
citation and the reopen trigger — a reopen is cheaper than a rediscovery.
[SR-LAW-2](../../records/0004_LAW-2-content-never-durable.md) §134 and
[BIBLIOGRAPHY](../../records/BIBLIOGRAPHY.md) (Morris et al., EMNLP 2023) both
point at this and both need the same sentence.

## Definition of done

1. `meta` is gone from `[sources.url]` in `fux.toml`, from the `.fux/sources/urls`
   line grammar, and from `config.py`'s `UrlSourceConfig`. A file still carrying
   `meta=` **fails to load with a named error**, not a warning.
2. `--hashed` and `--plain` are removed from `fux add` / the source verbs.
3. Every URL record ingests **plain**: `title` and `phrases`, never `title_h`.
4. `title_h` is absent from `index-record.schema.json`, `format.py`,
   `recordschema.py`, `reader.py` and the node twin. `SCHEMA_ID` →
   `fux.index.v4`.
5. `assert_meta_policy()` is deleted from `store/writer.py`.
6. **`store/displaycache.py` is deleted**, along with its `.fux/` directory row
   in `fuxdir.py`'s `DECLARED` — it exists only to serve display text for hashed
   records. ⚠ Removing the row without removing the directory trips
   **ADR-DOTFUX veto condition 1** and `fux doctor` flags it.
7. `fux doctor --json` no longer reports `hashed_meta`.
8. `query/headings.py`'s "a `hashed` record carries no `phrases`" branch is gone
   from both the Python and the `node/src/query/headings.mjs` twin.
9. CLAUDE.md's generated §Non-negotiable constraints shows **ten** live laws
   with L5 struck (the spec said eleven and miscounted — L9 was already retired,
   so twelve numbers minus two gaps is ten); `tests/test_claude_md_laws.py` passes byte-equal.
10. A migration note in CHANGELOG: **v3 indexes must be rebuilt** (`fux ingest`
    then `fux build`), and any URL source line carrying `meta=` must be edited.

## In scope / out of scope

**In:** the attribute, the record field, the display cache, the policy assert,
the CLI flags, the doctor row, both language twins, the records below, the
shipped agent skills, and the docs.

**Out:** `pii.toml` and term hashing. [SR-PII](../../records/0148_pii.md) §724 is
explicit — **`meta` is not redaction**. Terms stay hashed for every document;
this change touches *display text only*. Anyone reading this item as "fux stops
hashing" has misread it.

**Out:** `lastcited.py`'s hashed question keys (that is L8's business) and the
cache's hashed filenames ([SR-CACHE](../../records/0131_cache.md) §217).

## Key files

| area | files |
|---|---|
| config + grammar | `src/fux/config.py` (139, 179, 519–521), `src/fux/ingest/sourcelist.py` (334), `src/fux/sources.py` (512), `src/fux/templates/fux.toml.txt` (29), `fux.toml` |
| ingest | `src/fux/ingest/run.py` (60, 685–686), `src/fux/ingest/edges.py` (41) |
| record shape | `src/fux/store/format.py`, `index-record.schema.json`, `recordschema.py`, `reader.py`, `writer.py` (76, 112), `collisions.py`, `__init__.py` |
| delete | `src/fux/store/displaycache.py`, `tests/store/test_displaycache.py`, `tests/store/test_meta_policy.py` |
| query | `src/fux/query/headings.py` (48, 69), `query/__init__.py` (1965), `output.schema.json` (66), `derive/_build.py`, `derive/runtime.schema.json` (115), `mcp.py` (230), `inspect/dictionary.py` |
| CLI + setup | `src/fux/cli.py` (482), `src/fux/setup.py` (744–745) |
| node twin | `node/src/store/format.mjs`, `node/src/query/headings.mjs`, `node/src/correct.mjs` |
| shipped skills | `templates/agents/{CONFIG,PII,SOURCES}-SKILL.md` → regenerate `.agents/`, `.claude/`, `.kiro/` |
| docs | `docs/GLOSSARY.md`, `docs/index.md`, `docs/handbook.html`, `docs/paper/the-fux-index-paper.md`, `docs/paper/figures/{src/,}fig-03-ingest` and `fig-04-record` (**Mermaid source and the SVG twin, together**) |

## Records amended in the same change

`0001_LAWS` (strike L5) · `0007_LAW-5-hashed-meta` (→ `superseded`, plus the
accepted-exposure paragraph) · `0004_LAW-2` §134 · `0109_index-record` (the
"privacy forks two" section, the Mermaid + ASCII twin, the field table) ·
`0107_url-ingest` · `0102_fux-directory` (794, 809) · `0113_config` ·
`0116_url-list` · `0118_cdp-fetcher` (505–514) · `0119_http-fetcher` ·
`0103_ask` decision 8 · `0106_ingest` · `0108_index-lifecycle` · `0111_ranking` ·
`0127_refer-plane` · `0129_hooks` · `0131_cache` · `0136_mcp` · `0148_pii`
(§130–132, §195, §703, §724 — keep the "not a `meta` question" paragraph, it is
now the *only* thing standing) · `0110_accelerator` (683–687) · `README.md` ·
`BIBLIOGRAPHY.md`.

## Tests

- **Delete:** `tests/store/test_meta_policy.py`, `tests/store/test_displaycache.py`.
- **Rewrite, do not delete:** `tests/ingest/test_urlsrc.py`,
  `test_archived_urls.py`, `test_url_update_policy.py`, `test_sourcelist.py`,
  `test_validate.py`, `test_url_reredaction.py`, `tests/store/test_recordschema.py`,
  `tests/query/test_display_title.py`, `test_headings.py`, `test_provenance.py`,
  `tests/test_schemas.py`, `tests/test_doctor.py`, `tests/test_source_verbs.py`,
  `tests/derive/test_differential.py`, `tests/test_sr_ownership.py`.
- **New:** a URL source line carrying `meta=` is a **named load error**; a
  written URL record has `title` and no `title_h`; `SCHEMA_ID` is
  `fux.index.v4` and a v3 index is refused with a rebuild instruction.
- ⚠ `tests/derive/test_differential.py` and
  `tools/quality-controls/anchor_probe.py` were **given a hashed record on
  purpose** ([SR-ACCELERATOR](../../records/0110_accelerator.md) §683–687, after
  W-47) because the harness had never carried one. Those fixtures lose their
  reason to exist — the accelerator's differential now needs a *different*
  distinguishing record, not a silently-plain one.
- ⚠ Run the full suite under `pytest.ini` — full-suite runs have exhausted
  inodes via leftover `/tmp/pytest-of-*` on the device VM.

## Hazards

1. **The leak is real and is now accepted.** Do not let the supersession read as
   "L5 was wrong." It was right about the leak and lost on cost.
2. **`meta` ≠ PII.** Repeated because two records state it and a careless sweep
   will delete the wrong paragraphs.
3. **Twins.** Python/node, Mermaid/ASCII, Mermaid/SVG, templates/`.agents`+
   `.claude`+`.kiro`. Four kinds of pair in one change; each has bitten before.
4. **The law handle.** L5 is never reused. Eleven live laws, twelve numbers.

---

## ✅ Built 2026-09-20 (Claude Code, Opus 5)

**All ten items in *Definition of done* landed, plus the records, the docs, both
language twins and the shipped skills.** Six places the delivered change differs
from this spec, named rather than left to be found.

### 1. 🔴 Deleting `meta` silently disabled every delta ingest, and nothing failed

`ingest/run.py::_reusable` gated carry-forward on
`src == "git" **and** meta == "plain"`. Deleting the field made the second
clause `False` for every record in every corpus: **`reused_count` went to 0 and
every `fux ingest` became a full re-extract.** Nothing raised, nothing warned,
and **the committed index stayed byte-identical** — a full re-extraction
produces exactly what the carried fields held — so the only symptom was the run
taking longer.

**Caught by `tests/ingest/test_delta.py`, which asserts the COUNT and not the
bytes.** A test written against the output would have passed. That is the whole
argument for asserting the mechanism as well as the result, and it is why the
condition now carries the incident in its own docstring.

### 2. `store/displaycache.py` had no `DECLARED` row to remove

Item 6 says to delete the row in `fuxdir.py`'s `DECLARED` and warns that
removing it without removing the directory trips ADR-DOTFUX veto condition 1.
**There was no row.** The cache lived at `.fux/runtime/display-cache/` — a
*child* of `runtime/`, which is the declared entry — so `DECLARED` is untouched
and the veto condition was never in play. The file and its tests are deleted.

### 3. `fux doctor` had no `hashed_meta` row either

Item 7 asks for it to stop reporting one. `doctor.py` has never mentioned
`hashed`; the only match in the whole suite was a comment in `test_doctor.py`.
Nothing to remove.

### 4. The law generator needed a new rule, not just a list edit

`scripts/gen-laws.py` finds a law by its `LAW-TEXT` marker, and this spec keeps
SR-LAW-5 on disk at `status: superseded` — so the retired law kept rendering
into `CLAUDE.md` as if it still bound. **The generator now skips a record at
`status: superseded`**, which is a rule about retirement rather than a hard-coded
exception. The alternative — deleting the block — would have left the one
artifact that says what the rule *was* no longer saying it, and every historical
citation of L5 pointing at a record that had quietly stopped stating it.
**L9's precedent did not apply**: that record left the `*_LAW-*.md` glob by being
renamed, and L5 stays a law record because it never stopped being one — it
stopped being *in force*.

### 5. The differential harness's fixture was rewritten, not deleted

Hazard-adjacent: this spec says the hashed fixtures *"lose their reason to
exist"* and that the harness needs a different distinguishing record.
`_hashed()` became **`_url()`** — W-47's actual finding was that the harness had
never carried a `url:` record **at all**, which is still true of every other
fixture there. The `title_h` migration test became
**`test_a_stray_quoted_hash_still_stops_the_build`**, which exercises the
tripwire directly through a `title` that happens to be 16 hex characters: rarer
than the old default, and not impossible.

### 6. ⚠ A regeneration step overwrote two committed config files, and was reverted

Rewriting the vendor agent copies by looping over `setup.AGENT_FILES`
**clobbered `.claude/settings.json` and `.codex/hooks.json`** — files `fux setup`
seeds and never overwrites, and which in this repo carry the sealed-key deny
rules and hooks that W-198 had just widened. Restored from `HEAD` in the same
session; the 30 deny rules and both guard hooks are intact, and
`tests/test_golden_key_guards.py` proves it. **Named here because the safe loop
and the unsafe one look identical**, and the repo's own record
([SR-AGENT-SURFACES](../../records/0155_agent-surfaces.md)) already says
`settings.json` is co-owned and exempt from the drift test for exactly this
reason.

### What this change does NOT do

- **It does not stop fux hashing anything.** Terms are still hashed for every
  document and `.fux/pii.toml` is untouched — **display text only**, as §In
  scope says. The PII record's own argument never rested on L5; it rested on the
  gap L5 left, and that gap is unchanged.
- **It does not touch `lastcited.py`'s hashed question keys** (L8's) or the
  cache's hashed filenames (SR-CACHE).
- **It leaves `rank()` a pure function of the record**, which it now is by
  construction rather than by care: the P5 display-cache seam
  (`_resolve_title` / `_title_from`) is a no-op and is kept only because SR-ASK
  decision 10 names it.
