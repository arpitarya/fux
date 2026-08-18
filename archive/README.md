# `archive/` — the one archive, and where each thing went

**Rule (Arpit, 2026-08-10, restated 2026-08-18): there is exactly ONE archive
directory, and it is this one, at the repo root.** Nothing under `docs/` or
`work/` is an archive. Anything that gets archived is moved here.

**How to use this file.** This README is the **map**. Every archived doc gets a
row naming its **live successor**, so a reader who lands here is sent forward
rather than left at a dead end.

Enforced by `tests/test_archive_law.py`, which fails when a directory named
`archive` appears anywhere but here.

---

## Archive is not evidence

**A doc in here may be *named*. It may never be *cited as backing a live
claim*.**

The reason is mechanical, not ceremonial: nothing guarantees an archived file
was not edited or overwritten after it was retired. An archived doc is a record
that something *was* decided, not proof of what is true now.

- A record's **Reference** section may say "superseded by X" and name an
  archived doc. It may not ground a decision in one — the ADR register
  ([`../docs/adr/README.md`](../docs/adr/README.md)) says so, and the template
  repeats it at the point of use.
- When you find a live doc citing an archived one, **repoint it at the live
  successor**. Do not simply delete the link: a deleted link leaves the claim
  ungrounded, which is worse, because nobody can see that anything is missing.
- If a claim's only support is an archived doc, it needs new grounding — code,
  a live doc, or a measured run under
  [`../work/regression/`](../work/regression/README.md).

Entries here are frozen and reference-only. **Relative links inside them
reflect the tree as it was** and are not repaired; a frozen document is never
edited, which is the property that makes its contents trustworthy.

---

## Layout — the archive mirrors the live tree

A retired artifact goes to `archive/<the-directory-it-came-from>/`. `work/adr/`
retires into `archive/adr/`, `work/handoff/` into `archive/handoff/`, and so on
for `compare/` and `proposals/` when their turn comes. Old *builds* keep their
version-named directories.

```
archive/
  README.md              this map
  adr/                   superseded decision records — old number -> successor NAME
  handoff/               executed handoff + prompt pairs of the current build
  v0.1/                  build: the first one, pre-reset #1
  v0.26/                 build: the v0.19-0.26 substrate engine, runnable
  v0.26-docs/            build: that engine's frozen doc set
  v0.26-implemented/     build: that line's executed artifacts
  v0.30-rev1-planning/   the rebuild's research phase, frozen
```

## Superseded decision records

[`adr/`](adr/README.md) — each row maps a retired **number** to its live
successor **name**. Numbers survive only here; live prose cites names.

**The whole v0.30 record set retired here on 2026-08-18** — five records, in
one change, on Arpit's instruction. `work/adr/` no longer exists; the live
records are in [`docs/adr/`](../docs/adr/README.md) and the archive's map names
a successor for every one.

## `handoff/` — the retired handoff directory

**The whole directory was retired on 2026-08-18**, on Arpit's instruction, and
moved here as-is. It holds two different kinds of thing, and the difference
matters:

**Executed pairs** — implemented, with the record that closed them. These have
live successors and are safe to be named from anywhere.

| artifact | shipped | live successor |
|---|---|---|
| [`v0.30.0-m1-t0-slice-handoff.md`](handoff/v0.30.0-m1-t0-slice-handoff.md) · [prompt](handoff/v0.30.0-m1-t0-slice-prompt.md) | 2026-08-10 | [ADR-INDEX-FORMAT](../work/adr/0004_index-format.md) |
| [`v0.31.0-fux-dir-layout-handoff.md`](handoff/v0.31.0-fux-dir-layout-handoff.md) · [prompt](handoff/v0.31.0-fux-dir-layout-prompt.md) | 2026-08-11 | [ADR-FUX-DIR](../work/adr/0011_fux-dir-layout.md) |
| [`v0.31.0-fux-playground-extraction-handoff.md`](handoff/v0.31.0-fux-playground-extraction-handoff.md) · [prompt](handoff/v0.31.0-fux-playground-extraction-prompt.md) | 2026-08-12 | [ADR-PLAYGROUND](../work/adr/0012_playground-sibling-repo.md) |
| [`v0.32.0-open-items-handoff.md`](handoff/v0.32.0-open-items-handoff.md) · [prompt](handoff/v0.32.0-open-items-prompt.md) | Phases 0 and 1 closed 2026-08-12 | [`work/IMPLEMENTATION.md`](../work/IMPLEMENTATION.md) — the M2 and R2-close rows |

**Retired while still unresolved — no live successor.** These were archived by
instruction, not by completion. **Nothing may cite them as grounding**; the
open items they relate to have to carry their own content from here on.

| artifact | what it was | the open item that outlived it |
|---|---|---|
| [`v0.32.0-ratification-package.md`](handoff/v0.32.0-ratification-package.md) | the five Lane B decisions packaged for one sitting | [W-30](../work/open/W-30-ratify-adr-0001.md) · [W-31](../work/open/W-31-ratify-adr-0010-0011.md) · [W-32](../work/open/W-32-claude-md-adoption.md) · [W-33](../work/open/W-33-adr-numbering-contradiction.md) · [W-44](../work/open/W-44-archived-content-signalling.md) — **each states its own decision now** |
| [`v0.30.0-claude-md.diff`](handoff/v0.30.0-claude-md.diff) · [`v0.30.0-m1-claude-md-build-test.diff`](handoff/v0.30.0-m1-claude-md-build-test.diff) · [`v0.31.0-claude-md-layout.diff`](handoff/v0.31.0-claude-md-layout.diff) | prepared `CLAUDE.md` diffs awaiting review | [W-32](../work/open/W-32-claude-md-adoption.md) — the live `CLAUDE.md` has since moved on; treat the diffs as history, not as a patch to apply |
| [`v0.32.0-adr-numbering.diff`](handoff/v0.32.0-adr-numbering.diff) | the numbering-contradiction fix | [W-33](../work/open/W-33-adr-numbering-contradiction.md) — **superseded**: the contradiction was resolved directly on 2026-08-18 |
| [`v0.33.0-m4-refer-plane-handoff.md`](handoff/v0.33.0-m4-refer-plane-handoff.md) · [prompt](handoff/v0.33.0-m4-refer-plane-prompt.md) | the M4 build spec, written but never executed | [W-24](../work/open/W-24-m4-refer-plane.md) — **M4 has no live spec.** Whoever starts it writes a fresh one; this pair may be read for ideas but not cited |

**Handoffs are no longer a live directory.** A spec for open work belongs in
that item's detail file under [`work/open/`](../work/open/README.md).

## Retired planning documents

| artifact | retired | live successors |
|---|---|---|
| [`PLAN-v0.30.md`](PLAN-v0.30.md) | 2026-08-18, on Arpit's instruction | **Milestone scope** → the item's own detail file under [`work/open/`](../work/open/README.md) (M3→W-23 … M8→W-38), migrated verbatim · **what shipped** → [`work/IMPLEMENTATION.md`](../work/IMPLEMENTATION.md) · **predictions** → [`work/OPEN-WORK.md`](../work/OPEN-WORK.md) · **the port list** → [ADR-PORT-LIST](../docs/adr/0015_port-list.md) · **risks and the process contract** → [`CLAUDE.md`](../CLAUDE.md) and [`work/INTERVIEW.md`](../work/INTERVIEW.md) §standing constraints |

Its content was migrated **before** it moved, so no live item was left citing
an archived document. The design of record is now the ADR register plus the
open queue: decisions in [`docs/adr/`](../docs/adr/README.md), scope in the
item that will build it.

## Old builds

| entry | what it is |
|---|---|
| [`v0.1/`](v0.1/) | the first build (pre-reset #1) |
| [`v0.26/`](v0.26/) | the v0.19–0.26 substrate engine — runnable, reference-only, never modified, never imported; M1's eval baseline |
| [`v0.26-docs/`](v0.26-docs/) | that engine's documentation: ADRs 0001–0015 (always cited as **"archived ADR-NNNN"** *with this path*), compare docs, tracker |
| [`v0.26-implemented/`](v0.26-implemented/) | the v0.26 line's implemented artifacts: master-prompt, `PLAN-v0.26.md`, every executed pair v0.20→v0.26 |
| [`v0.30-rev1-planning/`](v0.30-rev1-planning/) | the rebuild's research phase: both gate handoff pairs (→ ADR-PRUNING-GATE / ADR-PRUNING-RERUN) and the superseded rev-1 diagrams |

---

## History — the two rulings

**2026-08-10.** The v0.26 doc set used to sit nested inside a second archive
under `docs/`. Arpit ruled that everything belonging to an old build lives at
the repo root, and it moved to [`v0.26-docs/`](v0.26-docs/). That ruling scoped
the v0.26 doc set; a second archive continued to exist for completed doc
artifacts of the current build.

**2026-08-18.** The `work/` restructure carried that second archive along as
`work/archive/`, which is exactly the split the first ruling was aimed at.
Arpit restated the rule in its general form — **one archive, at root, and
anything archived moves here** — and `work/archive/` was dissolved into this
directory. There is no longer a second place to look.

The 2026-08-10 discrepancy is recorded rather than deleted because
[ADR-INDEX-FORMAT](../work/adr/0004_index-format.md) §Consequences cites it as
the reason R2 question 3 could not be answered at M1.
