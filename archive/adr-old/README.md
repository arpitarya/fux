# `archive/adr/` — superseded records, and their live successors

**How to use this file.** When a decision record is superseded it moves here and
gets a row below, mapping its **old number** to the **name** of the record that
replaced it. That is the only place a number stays useful: live prose cites
`ADR-<NAME>`, never a number, so the archive is where numbering history remains
resolvable.

**Archive is not evidence.** These records may be *named* — "superseded by
ADR-X" — but never cited as backing a live claim; nothing guarantees an archived
file was not overwritten after retirement. Repoint any live citation at the
successor named below. See [`../README.md`](../README.md) §Archive is not
evidence.

## Moving a record here

**Only in the change that accepts its successor** — never before, so no claim is
ever left ungrounded. In that one change:

1. `git mv work/adr/000N_<name>.md archive/adr/` (or `docs/adr/…` if the record
   was still live). A record's directory is its state:
   [`docs/adr/`](../../docs/adr/README.md) live →
   [`work/adr/`](../../docs/adr/README.md) superseded-pending → here,
   superseded.
2. Set its `Status:` to `superseded by ADR-<SUCCESSOR>` and strip its
   superseded-pending banner — it is no longer pending, it is done.
3. Add its row below.
4. Remove its row from the register in
   [`../../docs/adr/README.md`](../../docs/adr/README.md), and rehome every
   component it owned in the ownership table — `tests/test_adr_ownership.py`
   fails otherwise, which is the point.
5. Repoint every live citation of it at the successor's **name**.

## ⚠ The live number line was renumbered on 2026-08-27 — a retired number here does not line up with the live one

**`0025` was vacated and then reused.** `ADR-CODES-TABLE` retired out of `0025`
with **no successor** (its subject, `codes.jsonl`, was deleted rather than
replaced), and on 2026-08-27 Arpit ruled the resulting hole closed: every live
record from `0026` up moved **down by one**. So `0025` is now
[ADR-RUNTIME-MANIFEST](../../docs/adr/0025_runtime-manifest.md), and the `0025`
row below is a **different record entirely**.

Three consequences, none of them cosmetic:

- **A retired number and a live number are two different address spaces**, and
  always were — `0022` and `0037` below already collided with live records
  before this renumber. Uniqueness is per directory, which is what
  `tests/test_adr_ownership.py` checks.
- **The `superseded by` column is a NAME for exactly this reason.** A name
  survives a renumber; the link beside it is a convenience that does not. If a
  link in this table ever disagrees with its name, **the name wins.**
- **Any document written before 2026-08-27 may name a record by a number that
  now means something else.** [`work/WORKLOG.md`](../../work/WORKLOG.md) is
  append-only, so a number of those sentences stand uncorrected on purpose.

## The map

| retired # | record | superseded by | date |
|---|---|---|---|
| [0017](0017_enriched-mode.md) | **ADR-ENRICHED** — the `enriched` (model-assisted) ingest mode | [ADR-ENRICH](../../docs/adr/0040_enrich.md) *(the whole record; its ratified content was folded in **verbatim first**, W-82 ruling 6, so no sentence was archived before it had a live home)*. ⚠ **The mode is still NOT authorized to be built** — superseding moved the decision, it did not grant the sign-off | 2026-08-27 |
| [0001](0001_ingest-mode-naming.md) | **ADR-INGEST-MODES** — ingest-mode naming | [ADR-INGEST](../../docs/adr/0007_ingest.md) | 2026-08-18 |
| [0022](0022_archived-signal.md) | **ADR-ARCHIVED-SIGNAL** — retired content is annotated, never reordered | [ADR-DIR-LIST](../../docs/adr/0022_dir-list.md) *(the whole record; `archived` becomes **declared** on a line rather than **derived** from the path)* | 2026-08-19 |
| [0004](0004_index-format.md) | **ADR-INDEX-FORMAT** — index format & committed store | [ADR-INGEST](../../docs/adr/0007_ingest.md) *(ingest)* · [ADR-INDEX-LIFECYCLE](../../docs/adr/0009_index-lifecycle.md) *(storage)* · [ADR-RECORD](../../docs/adr/0010_index-record.md) *(schema)* | 2026-08-18 |
| [0005](0005_derived-accelerator.md) | **ADR-ACCELERATOR** — derived T1 accelerator + the differential law | [ADR-ASK](../../docs/adr/0004_ask.md) *(query)* · [ADR-T1-ACCELERATOR](../../docs/adr/0011_accelerator.md) *(build)* | 2026-08-18 |
| [0010](0010_url-source-consumer-middleware.md) | **ADR-URL-MIDDLEWARE** — URL source via consumer middleware | [ADR-URL-INGEST](../../docs/adr/0008_url-ingest.md) | 2026-08-18 |
| [0011](0011_fux-dir-layout.md) | **ADR-FUX-DIR** — the `.fux/` layout | [ADR-DOTFUX](../../docs/adr/0003_fux-directory.md) *(layout)* · [ADR-CONFIG](../../docs/adr/0014_config.md) *(config)* | 2026-08-18 |
| [0025](0025_codes-table.md) | **ADR-CODES-TABLE** — `codes.jsonl`, the dense lane's per-document codes | **none — the subject was deleted, not replaced.** The live record of the refusal is [ADR-ASK](../../docs/adr/0004_ask.md) decision 9 | 2026-08-27 |
| [0037](0037_t2-segments.md) | **ADR-T2-SEGMENTS** — the T2 tier, deliberately not built | **none — a tier that was measured and declined.** The measurement stands; nothing replaced the record | 2026-08-22 |

⚠ **Two rows above have no successor, and that is a distinct outcome from
supersession.** A superseded record was replaced by a better decision; these two
describe subjects that **ceased to exist** — one deleted after its gate failed,
one never built. Neither may be revived by pointing at this file: a revival
needs a new record and Arpit's sign-off, exactly as
[ADR-PORT-LIST](../../docs/adr/0015_port-list.md) decision 6 says of a retired
port.

**All five went in one change**, on Arpit's instruction, rather than one at a
time as each successor was accepted. Two consequences follow and are recorded
here rather than left to be discovered:

1. **The successors are the records in force**, so they carry the components
   the archived records used to own, and their status moved from `proposed` to
   `accepted` — a record cannot own the engine and be a proposal at once.
2. **The open ratification items survive.** W-30 (ingest-mode naming) and W-31
   (the `.fux/` layout and the URL middleware) were never about *which record*
   holds the decision; they are Arpit's calls on the decisions themselves, and
   they now point at the successors.

**The v0.19–0.26 line is elsewhere.** Those records were never part of this
numbering; they are frozen at [`../v0.26-docs/adr/`](../v0.26-docs/adr/) and are
always cited as **"archived ADR-NNNN"** with that path.
