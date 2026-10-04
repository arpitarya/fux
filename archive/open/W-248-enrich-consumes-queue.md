---
type: Handoff
name: W-248
description: "`fux enrich` derives its worklist from declared scope ∪ the decoder queue's model-needed rows, so the queue `fux ingest` writes is finally read by something. Amends SR-ENRICH decision 4. Ratified 2026-10-03 by delegation, NOT built."
item: W-248
filed: 2026-10-03
ball: agent
---

# W-248 — something consumes the decoder queue

**✅ CLOSED 2026-10-04 — built as ruled, with two findings** (Claude Code; Sonnet built, Opus 5.5 reviewed):
- `fux enrich`'s worklist is declared scope ∪ `.fux/enrich/queue.tsv`'s *nothing readable* rows (`_queued_scope`); `--plan` heads them `(queued: a model is needed)`, `--check` counts them on their own line; an absent queue is no rows. `doctor` gains `queue: no decoder`, naming extensions and the `fux-decoder` skill. Both reason strings are now `constants.toml [decoders]` keys shared by writer and readers. `tests/enrich/test_queue_origin.py` (6); the L12 test passes with no allow-list line.
- ⚠ **Finding 1, filed as B-270:** enrichment written for a queued document reaches no index — ingest drops an unreadable document before extraction and reads `.fux/enrich/<sha>.md` only for one that parsed. That is the `enriched` mode's question (W-251 §3 #1), stated in SR-ENRICH d4.
- ⚠ **Finding 2:** no real ingest writes a *no decoder for X* row today (an unclaimed extension falls through to prose); the doctor row is correct and silent until one does. Stated in SR-ENRICH d4.
- Review fix: the new d4 text cited "decision 8" for the non-authorization; it is SR-ENRICHED's folded decision 6.
- Live successors: [SR-ENRICH](../../records/0137_enrich.md) d4, [SR-DECODE](../../records/0139_decode.md) d12, [SR-DOCTOR](../../records/0152_doctor.md).

**Model:** Claude Code, **Sonnet**.

**From** backlog B-007. [SR-DECODE](../../records/0139_decode.md) decision 12:
*"Nothing consumes the queue yet. `fux enrich` still derives its worklist from
declared scope … merging them amends an accepted record."* `ingest/run.py`
writes `queue.tsv`; `enrich.py` has no reference to it. A queue nobody reads is
a file that lies about being useful.

**Ruling (by delegation):** the worklist is **declared scope ∪ the queue rows
whose reason is *nothing readable* (a model is needed)**. Rows whose reason is
*no decoder for X* are **not** enrichment work — they become a `doctor` line
naming the extension, so a consumer sees *write a decoder* rather than *enrich
this*. The two origins stay distinct in `fux enrich --check`'s report.

## Definition of done

1. `enrich.py` reads `queue.tsv`, filters by reason, unions with declared scope;
   `--check` reports per origin (declared / queued).
2. `doctor` gains a `queue: no decoder` line listing the extensions the queue
   names, with the lever (`fux-decoder` skill).
3. [SR-ENRICH](../../records/0137_enrich.md) decision 4 amended; SR-DECODE d12's
   *"nothing consumes"* sentence rewritten; `sr-hash` restamped.
4. Tests: a planted repo with one undecodable binary and one unknown extension;
   the first is in the worklist, the second is a doctor line, neither is both.
5. Both suites whole; the L12 AST test passes with no new allow-list line.

## Out of scope

- Authorising the `enriched` ingest **mode** — that is W-251 §3 #1 and it is
  Arpit's. `fux enrich` is a different feature (CLAUDE.md §scope).
