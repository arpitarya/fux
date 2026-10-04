---
type: Handoff
name: W-248
description: "`fux enrich` derives its worklist from declared scope ∪ the decoder queue's model-needed rows, so the queue `fux ingest` writes is finally read by something. Amends SR-ENRICH decision 4. Ratified 2026-10-03 by delegation, NOT built."
item: W-248
filed: 2026-10-03
ball: agent
---

# W-248 — something consumes the decoder queue

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
