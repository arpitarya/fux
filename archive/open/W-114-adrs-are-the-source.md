---
type: OpenItem
id: W-114
title: "W-114 — L9: ADRs are the only source of truth, and the Law records outrank every other record"
description: "Arpit, 2026-09-06, ruling R-2 and going past it. A rule is stated in exactly one ADR; every other artifact links. The nine Law records outrank every other ADR and a conflicting record is void in the conflicting part. CLAUDE.md stops being normative and becomes a pointer, permanently. Carries the rename to ADR-LAW-n, the config single-source consolidation, and the key-tree gate that R-2 could not write until the source collapsed to one."
status: open
lane: agent
timestamp: 2026-09-06T00:00:00Z
---

# W-114 — L9, and the consolidation it makes possible

**Model: Opus.** This edits the constitution, moves the normative text of
every law, renames nine records and repoints every citation to them. A wrong
sentence here is authority. The mechanical halves (the rename sweep, the
generated block, the gate) are Sonnet-executable **after** Opus has landed
the text and the tests exist.

## Where this came from

**Arpit, 2026-09-06, deciding blocker 2 (R-2) and then widening it:**

> *"Let's keep it only in one document that is ADR. Every place else, let's
> drop it. ADRs are the only source of truth… if there is a change, the ADR
> changes and then it points to it."*
>
> *"It is a two level thing. All the ADRs are supposed to be followed, but
> none of the ADRs can break the Law ADRs."*
>
> *"Claude dot MD is not a law. It is just a pointer to ADRs, and you want to
> keep it that way."*

R-2 asked whether the twice-recorded W-83 shape gets a gate. The answer this
item lands is: **the gate was unwritable because the truth was in four
artifacts; collapse it to one and the gate becomes a parser.**

## 1 · The law, as proposed

> **L9** · **ADRs are the only source of truth, and the Law records outrank
> every other record.**
>
> **1. Source.** Every rule fux has is *stated* in exactly one ADR. Every
> other artifact — `CLAUDE.md`, a schema file, a config comment, a skill, a
> README, a diagram, a docstring — **links to it and never restates it**. A
> change is made in the record first; everything else keeps pointing.
>
> **2. Precedence.** The Law records `ADR-LAW-1` … `ADR-LAW-9` outrank every
> other ADR. A record that conflicts with a Law is **void in the conflicting
> part** — a defect to fix on contact, never a trade-off to weigh.
>
> **Amendment is entrenched.** A Law record changes **only on Arpit's ruling,
> named in the record**. An ordinary ADR a session may accept under the
> lifecycle. Without this clause "supreme" is decoration.

⚠ **What is a restatement, and what is not.** This test decides every case
below, and it is the difference between a law that can be followed and one
that gets routed around:

| kind | example | verdict |
|---|---|---|
| **describes** a rule a second time | `config.schema.json`'s `doc:` strings; a `fux.toml` comment explaining a key | 🔴 forbidden — becomes a link |
| **implements** it | `config.py` naming the key it parses | ✅ fine — it *is* the thing |
| **enforces** it | a runtime-loaded schema, a test | ✅ fine — an executable check, not a second statement |

**The test in one sentence:** *could this artifact and the record disagree
while both still look correct?* If yes, it is a restatement. If it would
simply fail, it is an implementation.

⚠ **Precedence is judgment, not a gate, and the record must say so.** No
parser reads *"does this record contradict L2."* The **source** clause is
partly checkable (§4); the **precedence** clause is not. W-83's original gap —
a record self-contradicting inside one file — is **unchanged by L9** and stays
named as unguarded.

## 2 · The rename, and why it removes a problem rather than adding one

`0002_l1-zero-cost.md` → **`0002_LAW-1-zero-cost.md`**, and the eight
siblings likewise. The cited **NAME** moves with the file: `ADR-L1` →
**`ADR-LAW-1`**, so the record's name and its filename agree, which
[the ADR standing rules](../../docs/adr/README.md) already require.

- 🟢 **It solves the ordinal problem the register was about to have.** L9's
  record cannot be `0010` without renumbering all sixty files a **second**
  time today. With `LAW-` in the filename, `docs/adr/*_LAW-*.md` finds all
  nine wherever they sit — so **L9 appends as `0061_LAW-9-adr-authority.md`**
  and contiguity stops mattering. The register's own rule already says the
  number is an ordinal, never an identity.
- **Every citation is repointed in the same commit** — `ADR-L1`…`ADR-L8` do
  not survive anywhere, including in `CLAUDE.md`, `docs/adr/README.md`,
  `RULE-SINCE`, `tests/test_adr_ownership.py`, and the eight records'
  cross-links.

## 3 · What moves, what stays — the CLAUDE.md inventory

**The rule that decides each row:** *normative and technical* → a record.
*Process, or a statement of fact about the repo* → stays, because there is no
record for "how an agent behaves in a session" and inventing one would be the
same duplication in a new place.

| CLAUDE.md section | verdict |
|---|---|
| Non-negotiable constraints (L1–L9) | 🔴 **moves** → the nine `ADR-LAW-n`; the section becomes a **generated** pointer block |
| Law zero (ADRs always up to date) · The ADR standing rules | 🔴 **moves** → `ADR-LAW-9` + ADR-OWNERSHIP |
| A pre-registered threshold may never move · Conformance runs | 🔴 **link** → ADR-RS already holds both |
| Litmus (the 10 000-document design point) | 🟠 **needs a record** — a real technical decision with no home |
| Archive is not evidence · Error contract · Package identity | 🟠 **needs a record** |
| OKF pattern | 🟠 link to ADR-DOCS-TABLE, or a record |
| Hard-won build knowledge — the two binding items (BM25F weight-then-saturate; no wall-clock on the maintenance path) | 🟠 **needs a record** — they are laws-in-waiting living in an appendix |
| Triage first · Documentation style · three-file session discipline · OPEN-WORK rules · Two hazards · Keep docs in sync · Session continuity · Blockers · Answer length · Say what you are doing | ✅ **stays** — agent process |
| Where the state of play lives · Layout · Build & test · Merge wall · What we are building | ✅ **stays** — pointers and statements of fact |

⚠ **The inventory is the deliverable of Phase 1, not a side note.** *"Move
everything technical"* without a written list is how half of it moves and
nobody can tell which half.

## 4 · The gate R-2 wanted, now writable

**Because the truth is in one place, the check is a parser.**

- `ADR-CONFIG` carries a **fenced key tree** (already — it is the ASCII twin,
  not prose). `tests/test_adr_config_keys.py` parses that fence and asserts
  **both directions**: every key in the tree is parsed by `config.py`, and
  every key `config.py` parses is in the tree.
- Same for **ADR-TUNE ↔ `tune.py`'s `_SCHEMA`**. ADR-TUNE already names
  `tune.specimen()` as the authority — the precedent for a generated view.
- **The rule that falls out, and it is the one that would have caught strike
  2:** *a key is real only if it is in the record's tree.* Prose mentions do
  not count — `acquired_max_bytes` sat "documented but never parsed" precisely
  because its only mention was prose (ADR-CONFIG decision 12).
- **`CLAUDE.md`'s law block is generated** from the nine records between
  markers, and a test asserts byte-equality. Agents keep the laws on first
  read; there is still one source.

## 5 · Definition of done

- [ ] **Phase 1 — the inventory** (§3) written into this file as a checklist
      with one row per CLAUDE.md section. Nothing moves before it exists.
- [ ] **Phase 2 — L9 lands.** `0061_LAW-9-adr-authority.md` created with §1's
      text; ADR-LAWS restructured to **meta-rules + index** (precedence,
      entrenchment, the restatement test) and **stops carrying law text**;
      the eight `ADR-LAW-n` records **promoted from rationale to normative**
      and each carries its own law's text.
- [ ] **Phase 3 — the rename.** Nine files to `*_LAW-n-*.md`; `ADR-Ln` →
      `ADR-LAW-n` everywhere; ownership table + `tests/test_adr_ownership.py`
      in the same commit; a test asserts no `ADR-L<digit>` spelling survives.
- [ ] **Phase 4 — CLAUDE.md becomes a pointer.** §Non-negotiable constraints
      replaced by a generated block between markers; `tests/test_claude_md_laws.py`
      asserts it matches the records; the section header states it is **not
      normative** and names where the text lives.
- [ ] **Phase 5 — the config consolidation.** The four live keys (`keep`,
      `ttl`, `enrich`, `acquired_max_bytes`) move into ADR-CONFIG's key tree;
      **`src/fux/config.schema.json` and `src/fux/derive/runtime.schema.json`
      are deleted** (both verified documentation-only, nothing loads them);
      `fux setup`'s `fux.toml` comments reduce to a link. ⚠ The four
      **runtime-loaded** schemas are untouched and the record says why they are
      exempt (they *enforce*, they do not *describe*).
- [ ] **Phase 6 — the gate.** `tests/test_adr_config_keys.py` (ADR-CONFIG ↔
      `config.py`, both directions) and the ADR-TUNE twin.
- [ ] CHANGELOG; `IMPLEMENTATION.md`; DOC-REGISTRY rows; this file to
      `archive/open/`.

## 6 · Hazards

- 🔴 **A concurrent session renumbered the entire register on 2026-09-06**
  (`0002`→`0010` for ADR-CLI, and so on) and split the eight law records out.
  **Re-derive every path before editing** and land the rename in **one**
  commit by **one** agent — two agents renaming in parallel is an unmergeable
  tree.
- 🔴 **Do not delete a schema before its keys are in the record.** Phase 5's
  order is absorb-then-delete; reversed, four live keys have no home at all.
- 🔴 **`tests/test_schemas.py` discovers `*.schema.json` by rglob.** Deleting
  two of them must not break its assertions — check before, not after.
- ⚠ **L9 supersedes ADR-LAWS decision 1** (*"CLAUDE.md is the single normative
  home"*), accepted **the same day**. The supersession is stated in the record
  with the date, not silently overwritten.
- ⚠ **The generated CLAUDE.md block is itself a restatement** — legal only
  because a test makes disagreement impossible. If the test is ever removed,
  the block violates L9. Say that in the record.
- **Answer-length and session-discipline rules stay in CLAUDE.md.** A session
  that "helpfully" moves them into an ADR has misread L9's scope.

## 7 · Out of scope

Any change to a law's *meaning* — L9 moves where laws live and how they rank;
it re-words none of L1–L8. The four runtime schemas. `tune.specimen()`. The
per-law records' rationale content, which is already correct.
