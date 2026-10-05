---
type: Handoff
name: W-261
description: "Arpit's ruling 2026-10-04 (W-251 #16): every kind: component record owns at least one file. The ten owns: [] records each get a file of their own; where none exists, the code is split out into a new one."
item: W-261
filed: 2026-10-04
ball: agent
---

# W-261 — every component record owns a file

**Status: built 2026-10-05, DoD 1–4 met** — nine records own a moved file
(Python + Node twin where Node mirrors it), SR-SECTIONS exempt by name; the
strong rule is SR-WORK-OWNERSHIP d11 and `tests/test_sr_ownership.py`. Index
bytes verified unchanged: a docs+records corpus ingested and built with HEAD's
code and with the moved code gives byte-identical `.fux/index/` and runtime
deterministic files (and identical `find --json --band --under`). Stopped on
no record — every one of the ten had code of its own.

| record | now owns |
|---|---|
| SR-FIND | `src/fux/query/find.py`, `node/src/verbs/find.mjs` |
| SR-URL-INGEST | `src/fux/ingest/urlingest.py` (Node never fetches) |
| SR-DIR-LIST | `src/fux/ingest/dirlist.py`, `node/src/ingest/dirlist.mjs` |
| SR-CACHEDIR-TAG | `src/fux/store/cachedir.py`, `node/src/store/cachedir.mjs` |
| SR-DOCS-TABLE | `src/fux/derive/docstable.py`, `node/src/derive/docstable.mjs` |
| SR-RUNTIME-MANIFEST | `src/fux/derive/manifest.py`, `node/src/derive/manifest.mjs` |
| SR-RUNTIME-STAMP | `src/fux/derive/stamp.py`, `node/src/derive/stamp.mjs` |
| SR-RUNTIME-STATS | `src/fux/derive/stats.py`, `node/src/derive/stats.mjs` |
| SR-LOCKS | `src/fux/maintain/lock.py`, `node/src/maintain/lock.mjs` (was `runner.mjs`) |
| SR-SECTIONS | nothing — exempt by name until W-236 Part B |

_Ratified 2026-10-04._

**Arpit, 2026-10-04 (Cowork):** *"yes, there should be a document, every
component record on a file. All 10 of them, if the records don't exist, create
them."* Read as: the strong rule of B-055 is **yes**, and for each record below,
if no file exists that it can own, **create the file** by moving its code out of
the file that hosts it today. ⚠ If a record turns out to have no code of its own
at all, stop on that one and ask him: it may be a `process` record, not a
`component`.

**Model:** Claude Code, **Opus** (it moves code across both readers and the
ownership gate).

| record | today | first guess at the file it should own |
|---|---|---|
| SR-FIND (0104) | `owns: []` | the `find` verb's code, split from the shared query module (+ Node twin) |
| SR-URL-INGEST (0107) | `owns: []` | the URL branch of ingest |
| SR-DIR-LIST (0120) | `owns: []` | the directory-list reader |
| SR-CACHEDIR-TAG (0121) | `owns: []` | the `CACHEDIR.TAG` writer |
| SR-DOCS-TABLE (0122) | `owns: []` | the runtime docs-table writer/reader |
| SR-RUNTIME-MANIFEST (0123) | `owns: []` | the runtime manifest |
| SR-RUNTIME-STAMP (0124) | `owns: []` | the runtime stamp (`stamp.json`) |
| SR-RUNTIME-STATS (0125) | `owns: []` | the runtime stats |
| SR-LOCKS (0140) | `owns: []` | the lock helper |
| SR-SECTIONS (0161) | `owns: []`, proposed | the section plane, when W-236 Part B builds it (owns nothing until then; say so) |

## Definition of done

1. Each record lists a real file in `owns:`; no file is owned twice (the gate).
2. Moves are pure: no behaviour change. Full Python and Node suites green;
   index bytes unchanged on this repo.
3. Node twins follow their Python owner (Arpit, 2026-09-23).
4. SR-WORK-OWNERSHIP d11 states the strong rule as ruled; `records/README.md`
   §The three kinds drops "Arpit's call, one record at a time"; a stdlib test
   fails any `kind: component` record with `owns: []` (SR-SECTIONS exempt **by
   name** until W-236 Part B lands).
