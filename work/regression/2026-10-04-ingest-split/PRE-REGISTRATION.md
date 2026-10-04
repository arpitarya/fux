---
type: Pre-registration
name: PRE-REG-INGEST-SPLIT
description: "W-256 section 8 - frozen before the measurement: the delta/full ingest split at fux-lab rung-10000 (a v7 throwaway copy), three interleaved repeats, identical root sha required. Decision rule: delta non-extract time under 5 s closes B-002 (the dirty list stays advisory); 5 s or more with walk+parse dominant files a parse-cache item; anything else goes to Arpit."
run: 2026-10-04-ingest-split
item: W-256
frozen: 2026-10-04
---

# W-256 section 8 - how much of a delta ingest is NOT extraction?

**Frozen 2026-10-04, before any timing exists.** The run directory holds this
file and nothing else until the measurement lands. A latency run, not a ranking
run: no golden question, key or score is read, no per-query quality row exists.
It is **`informed`** (section 6), which costs nothing - the endpoint is a clock.

## 1 - The question, and the decision it rules

[SR-MAINTENANCE](../../../records/0129_hooks.md) 1a-3 says the dirty list *"alone buys no
speedup"* and defers option D (incremental corpus-wide passes) to its own item.
The only number behind that is the 23x split SR-INGEST section 1 still cites,
which *"no longer describes the pipeline"*. W-239 timed **full** ingest only
(73.5 -> 12.8 s at rung-10000, extract 6.5 s of it) and never re-read the delta.
B-002 (rules on this number) waits on one fact: **at the design point, what does
a delta run cost that extraction does not account for?**

## 2 - The decision rule (verbatim from W-256 section 8; it may not move)

Let **N** = the **median over the three delta repeats** of
*(delta total wall time) - (the delta's `extract` phase time)*, at rung-10000.

- **N < 5 s -> B-002 closes.** The dirty list stays advisory
  (`maintain/dirty.py`'s docstring is true), SR-MAINTENANCE 1a-3 cites the run,
  and option D is *not needed at the design point*.
- **N >= 5 s AND walk + parse dominate -> a runtime parse cache keyed on content
  sha becomes its own item** (`.fux/runtime/parsed/`, pure in
  (sha, header, digests) like `_reusable`; M-L, Opus). **"Walk + parse dominate"
  is defined in section 4** and is decided on the same median.
- **Either outcome rewrites SR-INGEST section 1's 23x.**

### What the rule does NOT cover - stated now so no runner decides it later

1. **N >= 5 s but walk + parse do NOT dominate** (some other segment - edges,
   write, redact, the tail - carries the majority): a **split result. It goes to
   Arpit, not to the runner.** Neither "close" nor "file the parse cache" is
   licensed, and the run says which segment carried it.
2. **The three repeats straddle 5 s** (at least one below, at least one at or
   above): ambiguous, **handed to Arpit** (SR-RS decision 10b: a result between
   clearly passes and clearly fails is not adjudicated by whoever ran it). The
   median is reported, but it does not decide on its own.
3. **Exactly 5.000 s** is "at or above". The unit is seconds to the millisecond
   the script prints.

## 3 - The corpus, and where it does and does not come from

| | |
|---|---|
| corpus | **`fux-lab` `corpora/golden/rung-10000`**, generation 3 - [L9](../../../records/0011_LAW-9-use-record.md): never `fux-playground`, never an invented corpus |
| lab commit | `fux-lab` HEAD **`ed46bfefbe18bc35139ed2a909a2d4382fc15cbd`** (read 2026-10-04). That repository tracks no rung, so the lab sha pins the lab, not the bytes |
| what pins the bytes | the rung is its own git repository: HEAD **`cac5699ce2a48c8ded32a8f5e5df83234d87021e`**, one untracked file (`fux.toml`). The committed manifests `work/golden/ladder/rung-10000.sha256` / `.index` hold one hash per document and `index_root_sha256` |
| verified, 2026-10-04 | `rungs.verify("rung-10000", <lab rung>)` (`tools/differential/rungs.py`) returned `[]`. Phase 2 repeats it **before the copy** and files the output |
| index format | the lab's committed rung is **v5**; this engine writes and requires **v7** and refuses every verb on v5 |
| what is timed | a **throwaway copy** of the rung (`cp -R` into the session scratchpad), migrated by this engine: `fux doctor --fix`, `fux ingest --full`, `fux build` - in the copy only. The documents are the lab's bytes; the index is regenerated, which is the point |
| never touched | **nothing in `~/my_programs/fux-lab` is modified, re-ingested, rebuilt or deleted** ([SR-WORK-OPEN-QUEUE](../../../records/0051_WORK-open-queue.md) rule 53; corpora are kept). The copy is deleted by the session that made it. The script refuses a root that sits inside `fux-lab` outside a scratch/tmp path |
| copy verified | after the copy, every row of the manifest's per-document hashes is checked against the copy: **0 missing, 0 drifted**, or the run is void |
| key | **No key is read** ([L11](../../../records/0013_LAW-11-sealed-answer-key.md)). The only path under `work/golden/` this run reaches is `ladder/` through `rungs.verify`, which W-252 used for the same purpose |
| engine commit | the fux commit at run time is recorded; `src/fux/ingest/`, `src/fux/store/` and `tools/quality-controls/ingest_split.py` must equal the freeze commit's, or the run says what moved |

## 4 - The instrument, and why it is not simply `phase_times.py`

[`tools/quality-controls/ingest_split.py`](../../../tools/quality-controls/ingest_split.py)
(written for this run, frozen with it).

⚠ **`phase_times.py` from [W-239](../2026-09-29-w239-extract-speed/report.md)
cannot produce this split, and the item's wording assumed it could.** Its phases
are the engine's progress phases. `walk` wraps a single `update` *after*
`walk_sources` has already returned, so it reads **0.0 s by construction**
(W-239's own timings file: `('walk', 0.0)` on every row), and decode/parse, the
content sha and the reuse resolution run *between* phases and are in none of
them - W-239's rung-10000 total was 12.84 s against 8.3 s of named phases. The
4.5 s that is missing is exactly the thing this run exists to read.

So the script keeps the same progress hook **and names every gap between phase
events**. A run is cut into `before:<phase>` (the gap ahead of each phase),
each phase, and `tail`. The two categories the rule uses are defined from those
cuts, **now**:

- **walk** = `before:walk` + `walk` - config load, `walk_sources`, every file's
  bytes read.
- **parse** = the gap immediately after the `walk` event, up to the next phase
  event (`before:redact`, or `before:extract` if no redaction rules) - the
  existing-index load, decode/parse of every document, the content sha, and the
  reuse resolution. ⚠ It is a **gap, not a function**: it also carries the
  existing-index read and `_reusable`, and the run reports it as that, never as
  parse alone. If a finer cut is wanted to decide the parse-cache item it is
  a **post-hoc** cProfile and stays out of the verdict.
- **N (section 2)** = total wall time of the `run()` call - the `extract` phase
  (which is 0 or near 0 on an unchanged delta).
- **walk + parse dominate** = *(walk + parse) > 50 %* of N, on the median repeat
  of the three, **and** on at least two of the three repeats individually.

Each timed run is a **fresh process** (`ingest_split.py one`), because
`fux ingest` is one and W-239's fix was a per-process cache: repeated runs in one
interpreter would time caches a user never has. `total` is the wall clock around
`ingest.run`, so interpreter start-up and imports are **not** in N (the same
convention as W-239), and the report says so.

## 5 - The protocol

1. Verify the rung against its manifest; `cp -R`; `fux doctor --fix`;
   `fux ingest --full`; `fux build` in the copy; verify the copy's documents
   against the manifest.
2. `ingest_split.py run <copy> --repeats 3 --out evidence/`:
   - one **warm-up full ingest, discarded** (it records the runtime digests a
     delta run reuses against, and makes the first timed run no different from
     the others);
   - then **three repeats, each holding one delta run and one full run, interleaved**
     (delta first on odd repeats, full first on even), so drift on a shared
     machine ([SR-WORK-SESSION](../../../records/0060_WORK-session.md) decision
     12) hits both arms alike. Six timed runs in all.
3. The machine's load average is recorded before every run and the session says
   what else is running. **A repeat taken under a load average above half the
   core count is reported and re-taken once, both attempts filed** - not
   dropped, not chosen between after the fact.

## 6 - Validity conditions (a failure of any is a VOID run, not a result)

- **Identical root sha required**: the `.fux/index/` digest (sha-256 over every
  file, names included, W-239's digest) is **equal across the warm-up, all three
  deltas and all three fulls**. A full and a delta run of unchanged sources must
  produce byte-identical bytes ([L4](../../../records/0006_LAW-4-deterministic.md));
  if they do not, that is a **defect to file first** and the timing is moot.
- **Each timed delta is a true delta**: `changed == 0` and `reused == docs`.
  A delta that re-extracted anything timed a different thing.
- The graph/derived plane is not part of the clock; `fux build` is run once,
  outside it.
- 10 000 documents is the **design point and a ceiling** ([SR-WORK-SCALE](../../../records/0057_WORK-scale.md));
  no number above it is claimed or extrapolated.

## 7 - What is reported besides the endpoint

The **full/delta ratio** (median total of fulls over median total of deltas),
the per-segment split of every run (all six, as rows), the three delta N values
individually, and rung-01000 **not** - only the design point is run. Without a
ranking claim, **no paired floor or headroom applies**
([SR-RS](../../../records/0133_predictions.md) 19 and 22 are about paired quality
runs); the analogue is the straddle rule in section 2.

## 8 - Classification, authorship, and what this cannot show

**`informed`**, permanently - not because a key was seen but because the
instrument, the engine and this document are one model family's. Endpoint is a
clock, so this costs nothing.

| artifact | author | could reach |
|---|---|---|
| the rung | Arpit's lab builder, 2026-09 (generation 3) | the seed corpus; nothing of this run |
| the instrument | Claude Code, this session, from W-239's | the engine and the copy; no key |
| this document and the run | Claude Code, one session family | the code and the rungs; **not** `work/golden/` answers |

It cannot show: cost on a corpus whose documents are larger, more numerous or
more decoder-heavy than the rung (PDF / URL / decoder-bound corpora are
absent from it); timing on another machine (macOS, one box, Python version
recorded in the report); a dirty-list speedup (the dirty list is not exercised
by this run - it times what a delta costs with **no** change, the floor under
every real delta); or Windows/Linux.

## 9 - What would make this pre-registration wrong

- The `walk` / gap cut missing real time: the segments must sum to the run
  total (they do by construction) and the `tail` must not carry the majority -
  if it does, that is the split result of section 2 item 1 and is reported as
  such, not re-cut.
- A change to `src/fux/ingest/run.py`'s phase calls between this freeze and the
  run. The cut points are those of the frozen engine; a moved phase is reported,
  not absorbed.
- The copy's documents drifting from the manifest - the run would name a corpus
  it did not measure.
