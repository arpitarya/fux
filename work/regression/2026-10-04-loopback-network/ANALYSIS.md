---
type: Analysis
description: "W-256 section 4 - what loopback showed and the two things worth keeping: a fixture trap (the shipped small-document refusal) and a record that named the wrong journal file."
run: 2026-10-04-loopback-network
item: W-256
classification: informed
filed: 2026-10-04
---

# ANALYSIS - the mechanisms are wired; the trap and the wrong file name

## What it shows

Both mechanisms are connected end to end on the shipped code. The retry bound
(3), the exact doubling (1, 2, 4 s on the server's clock), the by-host counter,
its persistence in `url-state.json`, the stderr note and the doctor row agree
with SR-FETCHER decision 13 to the digit. The retained-bytes path reports
`as-ingested` with agreeing shas when the source is gone, the doctor block equals
the journal, and the quarter veto fires exactly where the share crosses it.

## What it does not show

How a real host rate-limits, `Retry-After` (never read), real outages, a real
citation mix, TLS or redirects. The veto - `as-ingested` over a quarter *on a
reachable corpus* - is not ruled by a designed 33 % on a corpus where I took the
server down on purpose; that is W-258's.

## Two findings worth keeping

1. **A fixture trap, not a defect:** a document under 1024 bytes at an
   extensionless URL is refused by the shipped `suspiciously-small-document`
   rule. The first `ok` control hit it. Any future loopback fixture must exceed
   the cap.
2. **A record named the wrong file.** SR-ACQUIRED said the journal is
   `.fux/runtime/ingest-log.jsonl`; it is `provenance.jsonl` (that is what the
   engine writes and what doctor reads; `ingest-log.jsonl` is W-200's unrelated
   ingest ledger). Corrected in the same change that cites this run.

## On the three attempts

The two failed attempts are instrument defects in a script written one session
earlier and never run until the measurement; they are kept as evidence
rather than overwritten. Nothing the pre-registration states about expected
values changed; four of the five B-102 observation groups were identical in all
three attempts.
