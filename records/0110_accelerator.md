---
type: Standing Record
kind: component
name: SR-T1-ACCELERATOR
title: SR-T1-ACCELERATOR (0110) — the derived T1 accelerator
description: A disposable term-major index under .fux/runtime/ that makes warm queries fast and is forbidden from changing an answer. Candidates and statistics only, never scores.
status: accepted
date: 2026-08-18
feature: "`.fux/runtime/` — the derived index, `fux build`, and the block bound that makes skipping provable"
owns: [src/fux/derive@d97158a8fa5b, tools/differential@44301711f1ed]
laws: [L1, L3]
timestamp: 2026-08-18T00:00:00Z
content_sha: 00266fddd2d2307f69e9da0c9a68dc80a12b67abd7e3ac063db6f5593c026362
---

# SR-T1-ACCELERATOR — the derived T1 accelerator

## §1 — For humans

The committed index is **doc-major**: one line per document. That shape is
right for git — one document changes, one line changes — and wrong for
querying, because answering a three-word question means reading every document.

The accelerator is the same information **term-major**: for each term, the list
of documents containing it, in blocks of 128, with a small binary side-table
saying where each block is and what the best possible score inside it could be.
Rare terms open first; once the k-th best score is known exactly, any block
whose *best case* cannot beat it is never read at all.

It lives in `.fux/runtime/`, is gitignored, and is **disposable** — a pure
function of the committed shards. Delete it whenever; `fux build` brings it
back.

The rule that makes it safe: **it produces candidates and statistics, never
scores.** Both query paths hand their candidates to the same `rank()`. So
"fast" and "correct" are not in tension — the accelerator cannot change an
answer, only how quickly it arrives.

**Diagram — Mermaid and its ASCII twin. Update both, always, together.**

```mermaid
flowchart TD
    C[".fux/index/*.jsonl<br/>doc-major, COMMITTED"] -->|"fux build"| INV{"invariants hold?"}
    INV -->|no| ERR["refuse, exit 1<br/>never a divergent accelerator"]
    INV -->|yes| R[".fux/runtime/ — DERIVED"]
    R --> P["postings/xx.jsonl<br/>term-major, blocks of 128"]
    R --> I["postings/xx.idx<br/>62-byte entries:<br/>offset · per-field mx · per-field mnw"]
    R --> D["docs.jsonl<br/>loc · title · flen · archived · superseded · mtime"]
    R --> ST["stats.json<br/>n · RAW total_flen"]
    R --> M["manifest.json<br/>a sha per committed shard"]
    M -->|"drift?"| S["stale -> the scan answers"]
```

<details>
<summary><b>ASCII twin</b> — the same diagram, for terminals, diffs, and any reader without a Mermaid renderer</summary>

```text
   .fux/index/*.jsonl        doc-major, COMMITTED (the only input)
          |
          |  fux build
          v
   invariants hold? --no--> refuse, exit 1   (never a divergent accelerator)
          |
         yes
          v
   .fux/runtime/             DERIVED, gitignored, disposable
      postings/xx.jsonl      term-major, blocks of 128 postings
      postings/xx.idx        62-byte entries: offset, length, per-field mx,
                             per-field mnw, doc range, count
      docs.jsonl             id -> loc, title, flen, archived, superseded, mtime
      stats.json             n, total_flen (RAW per-field)
      manifest.json          a sha per committed shard  --drift--> stale
                                                                     |
                                              the scan answers <-----+
```

</details>

### Examples

```console
$ fux ingest
ingested 5 docs (5 changed), 5 shards written
accelerator: 97 terms, 97 blocks, 104 postings (derived, not committed)

$ fux build
accelerator rebuilt from the committed index: 5 docs, 97 terms, 97 blocks, 104 postings
```

The manifest is the staleness mechanism — a sha per committed shard. The
capture predates the current schema strings and is not edited; what it
demonstrates is the shape:

```json
{
  "analyzer": "v1", "block_size": 128, "blocks": 78, "docs": 3,
  "index_schema": "fux.index.v1", "schema": "fux.runtime.v1",
  "shards": {
    "2e.jsonl": "2d4f19bcd8f8af905da1103648c3df21007d3255",
    "88.jsonl": "61abfc1c7540bf7b0626fbb9de360a42496b5908",
    "e6.jsonl": "c7c7b09f882e30a96612927a3d1921c79f4e57b2"
  },
  "terms": 78
}
```

When it drifts, the engine says so rather than answering from a stale cache:

```console
$ fux doctor
[OK] accelerator: stale (the committed index changed since it was built) - `ask` falls back to the scan; run `fux build`
```

### Charts

Warm-query p95 on 8 870 RFC documents — the accelerator against the reference
scan it must agree with exactly, and the pre-registered bar it had to clear.

```mermaid
xychart-beta
    title "Warm ask p95, 8870 RFCs (ms, lower is better)"
    x-axis ["accelerator", "R3 bar", "reference scan"]
    y-axis "p95 latency (ms)" 0 --> 4400
    bar [27.2, 150, 4248.8]
```

<details>
<summary><b>ASCII twin</b> — the same chart, for terminals, diffs, and any reader without a Mermaid renderer</summary>

```text
  warm ask p95, 8870 RFC documents (ms, lower is better)

  accelerator      |  27.2                                    (R3 PASS)
  R3 bar           | 150                                      (pre-registered)
  reference scan   | ################################ 4248.8

                   0        1000      2000      3000      4000

  156x faster than the scan; 5.5x inside the bar.
  Same answers, byte for byte -- the difference is only time.

  source: work/regression/2026-08-12-m2-accelerator/report.md (R3 PASS)
```

</details>

---

## §2 — For agents

### Context

`query/scan.py` answers a fresh clone with no build step, which is a property
worth keeping. It is also 4 248.8 ms at p95 on 8 870 documents — not an
agent-facing latency.

A second index buys the latency back and introduces the real risk: two
implementations of one query that can silently disagree. Worse, they can
disagree *only in the last digits* — float addition is not associative, so a
term-major accumulation naturally produces different low-order bits than a
doc-major one, and `--json` payloads would differ while both were logically
correct.

### Decision

**1. The derived plane's only input is the committed shards.** Nothing else.
That is what makes it deletable, and what makes "rebuilds deterministically from
committed bytes" a checkable claim.

**2. It generates candidates and statistics, never scores.** Scoring and
sorting live in `rank()`, shared by both paths
([SR-RANKING](0111_ranking.md)). The differential law then reduces to "the
candidate set and `(n, total_wlen, df)` are identical", which a test can assert
— where `total_wlen` is a **float derived per query on both paths** from the
raw `total_flen` the stats plane stores.

**3. Postings are blocked at 128**, a measured shape, with a **binary offset
table** beside each shard — **62 bytes per entry, `<8sHQI` + `5H` + `5I` +
`IIH`** — carrying the block's byte offset and length, its per-field `mx` and
`mnw`, its document range, and its count. Binary because the alternative —
fixed-width integers inside the JSON line — needs zero padding, which JSON
forbids.

⚠ **`mx` and `mnw` are per-field arrays and deliberately UNWEIGHTED**,
recombined at the query's own weights by `block_bound`. A *weighted* extremum
cannot be stored once when the weights are query-time tune keys. Per-field
extrema over-estimate `mx` and under-estimate `mnw`, and **both errors push the
bound up**, so a block that could contain a winner is never skipped. Measured
cost: **+0.0 % blocks scanned**, because 92.5 % of postings are single-field,
which makes the per-field sum exact rather than loose
([fork 3](../work/regression/2026-08-23-fork3-per-field-bound/)).

**4. Skipping is proved, not heuristic.** Terms open rarest-first. After each,
every seen candidate has an exact score, so the k-th best `theta` is exact. An
unseen document can only score at most the sum over deferred terms of each
term's best block bound; if that cannot reach `theta`, no unopened block can
change the answer. Worst case is opening everything — the scan's work, never
wrong.

**5. The bound uses `mx` *and* `mnw`** because BM25F's contribution is
increasing in weighted tf and *decreasing* in document length. `mx` alone is
valid but loose.

**6. The skip test is rounding-aware:** `round(bound, 9) < round(theta, 9)`.
`rank()` orders by `(-round(score, 9), id)`, so a document scoring
`theta - 1e-12` still *ties* after rounding and can win on `id`. A naive
`bound < theta` is wrong exactly on ties — the class of bug a spot-check
misses.

**7. The build refuses rather than diverging** if either raw-byte invariant
fails ([SR-INDEX-LIFECYCLE](0108_index-lifecycle.md)).

**8. Staleness is detected via a per-shard sha in the manifest**, not assumed.
On drift `ask` falls back to the scan and says so under `--explain`; `doctor`
reports it.

**9. `stamp.json` is excluded from the determinism set** — it carries
filesystem mtimes, which are the cheap staleness pre-check and are not
reproducible by construction.

**10. The plane's four shapes are declared in one schema.**
[`derive/runtime.schema.json`](../src/fux/derive/runtime.schema.json)
declares the postings block line, the 62-byte offset entry, the doc table and
`stats.json`. **One file for all four, deliberately** — they are written by one
build, read by one query path, and versioned by **one string**, so four files
would invite three to be updated and the fourth forgotten.

⚠ **A disposable plane still needs a declared shape, and the reason is this
record's own central promise.** A shape that drifts does not corrupt the index
— **it makes one of the two paths disagree, which is a fast wrong answer.**
That is not hypothetical: `superseded` and `mtime` once joined the doc table
while `RUNTIME_SCHEMA` stayed put, and `ask --scan` applied a supersession
demotion that `ask --fast` did not. `DOCS_FIELDS` exists because of that.

**The assertion that earns its place is the struct string.** This module's own
docstring table described the 62-byte entry layout in prose and **nothing
compared it to `ENTRY_STRUCT`** — and the table has already been wrong once,
when the entry grew 40 → 62 bytes. Two tests hold it: the declared `struct`
equals `ENTRY_STRUCT.format`, **and** the per-field `code` values concatenate
back to it — because the format string could match while the field table beside
it described something else entirely, which is the kind of documentation that
reads as authority and is wrong.

**Every shape carries a worked example and the examples are tested.** The
offset entry's is packed through `pack_entry` and round-tripped through
`unpack_entry`; the doc-table and stats examples are asserted to carry exactly
the declared field sets; the postings example is checked for ascending docidx
and trimmed per-field tf.

### The weighted bound

**The block bound is safe on exactly one property, and it is a property about
the WEIGHTED score:**

```
for every unseen d:   w(d) * S(d)  <  theta_w      =>  d cannot enter the top-k
```

The accelerator once computed both halves **unweighted** — the ceiling from
`mx`/`mnw`, and `theta` from raw candidate scores — while `rank()` applied
`w(d)` *afterwards*, on a candidate set that had already been truncated. The
law therefore held at weight `1.0` and **at no other value**, while the config
accepted any non-negative float.

**Both halves are required, and each covers a direction the other does not:**

| half | what it fixes | the direction it covers |
|---|---|---|
| `theta` drawn from **weighted** candidate scores | demoting the current top-k lowers the real threshold, so a document pruned on the old `theta` should now enter | `w < 1` |
| ceiling scaled by **`Weighting.maximum`** | a promoted document is skipped on a ceiling that never knew about the promotion | `w > 1` |

**`maximum` is the supremum over the CONFIGURATION, never over the observed
candidates** — the document the test is about has not been seen, so nothing is
known about its weight except that the configuration bounds it. It is
`max(1.0, …)` **per factor**, never the configured weight alone: `1.0` is always
attainable, because a document that is not archived (or not listed under a
priority) is never scaled, and a configuration of demotions must not lower the
ceiling.

Weighting an *under-estimate* is legal: `_kth_score` scores over opened terms
only, and `w(d) * S_opened(d) <= w(d) * S_full(d)` for `w >= 0`, so a weighted
`theta` is still a lower bound and a lower `theta` skips less, never more.

**At `Weighting.trivial` every weighted path short-circuits**, so a corpus with
no configured weight is byte-identical to the unweighted arithmetic and the
differential evidence gathered at the default stands unmodified.

⚠ **Amended 2026-09-13: `Weighting` now carries ONE multiplier.** The three
document priors that could also make `trivial` false — `superseded_weight`,
`archived_weight`, `recency_half_life_days` — were removed (W-151, W-152;
[SR-TUNE](0135_tuning.md) decision 15), leaving `.fux/tune.toml`'s `[priority]`.
**Nothing about this decision changes.** `maximum` is still the supremum over
the configuration, the short-circuit still guards the property the bound rests
on, and `tests/derive/test_weighted_bound.py` still drives the adversarial case
down both paths — through `[priority]` instead of `archived_weight`. **The
vehicle is incidental; veto 5 binds whatever multiplier arrives next.**

**`block_bound` takes a `Scoring` for the same reason.** `k1`, `b` and the five
field weights are `.fux/tune.toml` keys, and they reach the **bound**, not only
the scorer; `accel_candidates`, `ask`, `_cannot_reach` and `_kth_score` thread
the same object down. Document-level multipliers travel through `Weighting`,
scoring parameters through `Scoring`; a multiplier or a parameter that reaches
the scorer without reaching the bound is the identical defect on a different
axis.

⚠ **The finding worth carrying forward is about how to TEST a bound.** **BM25
saturates, so an unweighted bound is nearly indistinguishable from a weighted
one whenever `tf` is large.** At `tf = 90` a term's contribution is already
within a percent of its `idf * (k1 + 1)` ceiling, so computing the bound at
weight `1.0` instead of `60.0` barely moves it and nothing diverges. The gap
only opens where weighted `tf` is comparable to `k1` — which means **small
counts**.

**So a weight sweep over a realistic corpus passes while proving nothing.** The
fixture that actually falsifies an unweighted bound needs every `tf` at 1 or 2,
the deferred term common and its documents short, and the opened term's
documents long enough that length normalisation keeps `theta` low. Verified by
mutation: reverting `block_bound`'s `scoring` argument makes it diverge at
`top = 20`
([`tests/test_tune_boundary.py`](../tests/test_tune_boundary.py)). **A
fixture that does not fail under that mutation certifies an unsound bound as
proven.**

**11. The implementation modules are private, because the function is the API.**
Renamed 2026-08-27 on Arpit's ruling — *remove the trap at the source.*

`build.py` → `_build.py`. `accel.py` and `stats.py` keep their names.

- **The trap.** `from .thing import thing` in a package `__init__` binds the
  **function** to `package.thing`, permanently shadowing the **submodule**. Both
  `from package import thing` and `import package.thing` then hand back the
  function, and every attribute access on it raises `AttributeError` at a call
  site far from the cause.
- **Why the MODULE was renamed rather than the function.** The function is what
  callers use; the module is implementation. An underscore says what was already
  true and **no caller changed** — where renaming the export would have touched
  roughly thirty sites for the same result.
- ⚠ **What this shape had already cost, unnoticed:** `fux.refer`'s shadow made
  `tests/refer/test_refer_plane.py` feed **three functions** to
  `inspect.getsource` while believing it was scanning three modules for
  `urllib`/`socket` imports. **L4's network import fence silently stopped
  covering three files** — 552 lines — and nothing failed, because
  `getsource` works on a function too. A shadow does not have to break a test to
  cost you one.
- **Gated by [`tests/test_no_shadowed_submodules.py`](../tests/test_no_shadowed_submodules.py)**,
  which walks every package under `src/fux/` and carries a companion test
  proving it can see a planted shadow — this repo has recorded vacuous passes
  before.

🔴 **The block bound prices each term at THAT term's weight since 2026-09-05**
(W-109, [SR-EXPAND](0149_expand.md) decisions 6-7). `--expand` gives
individual terms a multiplier, and an unweighted ceiling over weighted scores is
the **W-73 class of defect** — a bound that no longer bounds, failing silently
as *the accelerator returns a different answer from the scan*.

Two changes, and the second was found by measurement rather than by reasoning:

1. `_cannot_reach` multiplies each deferred term's `block_bound` by its own
   weight, and `_kth_score` scores `theta` with the same weights. Comparing a
   threshold and a ceiling in different units is how a bound stops bounding.
2. 🔴 **A candidate `rank()` will DROP may not set `theta`.** With `--expand`,
   a document matching only expansion terms is discarded by the hallucination
   guard, so counting it raises the threshold on the strength of a document
   nobody will be shown. `tests/derive/test_expand_bound.py` diverged at every
   `expand_weight >= 0.5` at `top = 20` until `_kth_score` filtered on the
   guard — **including at `1.0`, where the weights change no arithmetic at
   all** and the guard alone broke the bound.

⚠ **The test file catches three distinct injections and needs TWO corpus
shapes to do it**, because the `theta` and ceiling defects bite under opposite
conditions; the third is pinned as a direct property because no corpus shape
found it. That is recorded in the file itself — a differential test that cannot
fail is worse than none.

**13. Every pipe the harness reads is UTF-8, named rather than inherited.**
Added 2026-09-13, on `node-arm.yml`'s first run.

`subprocess.run(..., text=True)` decodes with the platform's preferred
encoding, which on a Windows runner is cp1252. Node writes UTF-8, so every
title carrying an em dash came back mojibake and the arm reported **174
transcription defects on both Windows jobs while all four Unix jobs were
clean** — the arm accusing the reader it exists to check.

🔴 **The failure shape is the point: a harness artifact is indistinguishable
from a finding, and this one was OS-localised, internally consistent and
100 % reproducible.** It is the same class as the loaded-machine anomaly in
`CLAUDE.md` §Hard-won build knowledge — plausible, tidy, and wrong. The arm
now names `encoding="utf-8"` on every call and reconfigures its own stdout,
because printing the report's `⚠` to a cp1252 console raises
`UnicodeEncodeError` *after* the comparison has already passed.

⚠ **The engine was never implicated in the mojibake** — `store/reader.py`
reads bytes and every `read_text` in `src/fux/` names its encoding. Checked
before the harness was touched, because *"fix the harness"* is what a session
says when it has decided the answer first.

🔴 **But the same call was wrong in four places inside `src/fux/`, and this is
where that is stated** — cited, never restated, by the records owning them.
`ingest/priors.py`, `maintain/runner.py` and `maintain/hooks.py` read **git**
through `subprocess.run(text=True)`, and `store/fuxdir.py` writes that same
call into the snippet `fux setup` leaves in a consumer's repository. Git's
output there is **paths**: on a Windows machine with one non-ASCII filename,
`ingest` raises `UnicodeDecodeError` from inside the recency prior, or silently
loses that file's date. All four now name `encoding="utf-8"` — with
`errors="replace"` in the engine, because a diagnostic read must not be able to
kill a verb — and so does every call under `tests/`, `tests_e2e/`, `scripts/`
and `tools/`. **69 sites; none of them was a decision, all of them were a
default.**

**12. The differential harness takes a CORPUS, not a repo — and a golden rung
is resolved through its committed manifest.** Added 2026-09-12 (W-107).

`node_arm.py`, `graph_arm.py` and `adversarial_corpus.py` each did
`sys.path.insert(0, ROOT / "src")` on the *same* argument they read the index
from, so the only corpus any of them could run on was a fux checkout. A golden
rung is a repo of documents with no `src/`. Engine root and corpus root are now
two different things, and that is what let the arm run on the ladder at all.

`rungs.py` resolves a rung name to `fux-lab`'s corpus and **verifies it against
`work/golden/ladder/rung-NNNNN.{index,sha256}` before a byte is read** — every
document hash and the index root hash — refusing on drift.

🔴 **This is the one failure a differential arm structurally cannot catch about
itself.** Two readers on a drifted corpus agree perfectly; the run is green and
names a corpus it did not measure. Verification is external to the comparison
or it is absent. `ladder_check.py` is the same argument with no corpus at all:
the eight manifests' counts, their `seed/`+`ext/`-only paths, and the nesting
`work/golden/README.md` called *"verified, not asserted"*.

**13. Two arms, because a discordance has to be attributable.** Added
2026-09-12 (W-107), and it is a correction, not an addition.

The Node arm called `scan.ask` directly. **`fux find` does not** — it calls
`run_query`, which applies `.fux/tune.toml`, the archived weighting and the
reranker. So the arm compared Node against a Python path no user reaches, and
was green because both sides ignored the same things — the failure
`queryset.py`'s own docstring names: a harness authored after the thing it
checks gets authored to pass.

| `--python-tune on` (default) | the **contract** — what `fux find` answers on this corpus |
| `--python-tune off` | the **transcription** — `--no-tune` ([SR-TUNE](0135_tuning.md) decision 11), the engine's own answer |

**They are the same run on a corpus whose tune is all-defaults**, which is
every golden rung. They differ on fux's own repo — 90 of 174 comparisons
against 0 — because, **when this was measured, Node read no `tune.toml` at
all**. ⚠ **Closed 2026-09-12** ([SR-NODE-SEARCH](0153_node-search.md) decision
8): the reader now reads `.fux/tune.toml` and `.fux/output.toml`, and this repo
went 90 of 174 discordant to 0 of 199. The two arms still exist — the
diagnostic pattern below is why — and on this repo they now agree.

⚠ **This is the diagnostic-arm pattern this repo already learned once** —
`CLAUDE.md` §"Hard-won build knowledge", M1: keep an arm that *does* borrow the
baseline's statistics, because it is how a loss gets attributed to the right
cause. A single arm reports a number; two arms report a diagnosis.

**14. The third arm compares SIX surfaces, and compared one until 2026-09-12.**

Decision 13 recorded the find that the arm's Python side called `scan.ask`
while `fux find` calls `run_query`, so **both readers were ignoring the same
files**. Closing that exposed the more general version of the same defect: the
arm compared `find` and `ask` and nothing else, so every other surface was
transcribed and never checked.

| surface | how it is compared | what it found on the first run |
|---|---|---|
| `find` · `ask` | the field table, per PRE-REG-NODE-2 §3 | — (already covered) |
| `explain` · `graph` · `path` | **whole parsed payloads**, both CLIs | different key names in all three, and a hand-rolled breadth-first walk where Python runs a PPR expansion |
| `mcp` | both servers, one stdio session each | handlers reading `args.id` where the advertised schema says `path` — in a package already on npm |
| `fux.api` vs `node/src/index.mjs` | all six methods | `api.py` ranking without its tune file; Node dropping `ordinal` from every passage |
| **the published BUNDLE vs the module tree** (`--bundle-cap`, 2026-09-12) | `find`/`ask`/`answer`, one MCP session, and the library export — whole payloads, both Node entry points | nothing: **0 discordant on this repo's index**. It was added because the arm read `node/fux.mjs` while a consumer runs the generated `.fux/node/fux.mjs` (L10, SR-NODE-SEARCH decisions 13-14) |

🔴 **The bundle row is decisions 9-12's own lesson applied to the instrument
itself** — *a transcription is only as true as the surface the instrument is
aimed at.* Once `fux setup` and npm ship a generated artefact, an arm that
compares the module tree is measuring a thing nobody executes. ⚠ **And the
bundler being deterministic does not cover it**: reproducible bytes can still
compile, run and answer differently, so the comparison is on **answers**. The
bundle is BUILT per run (`node_arm.bundle_entry`) rather than read off disk,
because a bundle on disk could be from another checkout.

**Whole payloads rather than a field list, for the graph lane**, because those
verbs carry no score to tolerance: every byte of meaning is in the structure,
and comparing a field list is exactly what would let two readers emit different
key names indefinitely.

⚠ **Two exclusions, both by NAME and neither by a loosened comparison** —
`ranked_by` (SR-NODE-SEARCH decision 10: Python's MCP surface opts into the
accelerator and Node has none, and the differential law is what makes the label
the only difference), and `answer` equality where Python cited a document Node
cannot decode (decision 11: the two then rescore over different passage
populations, so comparing would be meaningless rather than merely weak — what
is asserted instead is the invariant that Node cites no decoded document, on
every answer).

⚠ **The graph lane is SKIPPED, loudly, on a corpus with no fresh derived
plane.** Python's graph verbs refuse without `fux build` and Node's do not
(SR-NODE-SEARCH decision 9), so there is nothing to compare there — and a lane
that silently does not run is the failure decision 13 is about.


**15. The anchor seed happens BEFORE the skipping loop, and that ordering is
the whole correctness argument** (W-168 step 1, 2026-09-15).

`block_bound` bounds what a document can score **from the postings**. An anchor
contribution is not in the postings, so a document whose score comes from a
linker's wording is not bounded by it — and skipping would lose it. That is the
W-73 defect exactly: a bound that no longer bounds.

**Seeding every anchor-matching document up front makes the existing bound
sound again, unchanged.** After the seed, every document with a non-zero anchor
contribution for any query term is already a candidate, so an *unseen*
document's anchor contribution is **zero by construction** and `block_bound`
bounds it as it always did. The ceiling is therefore **exact** rather than
merely conservative, and nothing in it needed widening.

- **The other direction is safe too.** Anchor length only ever raises a
  candidate's `wlen`, and `mnw` under-estimates `wlen`, which pushes the bound
  **up** — the one error direction that never loses a document.
- **`theta` DOES carry the fold**, and must: a real candidate's real score
  includes its anchor terms. A higher `theta` skips more, which is sound
  because it is compared against a ceiling over documents that provably have
  none. Scoring a candidate without its anchor terms while `rank()` scores it
  with them would report a k-th best that no longer matches the ranking anyone
  sees — the same rule `--expand`'s per-term weights follow in `_kth_score`.
- **It is cheap.** Anchor postings are link text: a handful of words per edge
  against thousands per body.

**15a. `fux.runtime.v6` — the anchor plane.** `anchors/<prefix>.json` holds the
reverse map term → `[(docidx, count)]`; `docs.jsonl` carries each document's
`alen`; `stats.json` carries `total_anchor_len`. All three are folded from the
committed shards alone and gitignored, which is the whole of Arpit's ruling:
**the words are committed on the source's edge, and the per-target view ranking
needs is rebuilt, never committed.**

- **Sharded by the term hash's first byte**, mirroring `postings/` and the
  committed store, so a query opens one small file per term rather than a
  corpus-wide map.
- **Whole-file JSON, not the block-and-offset shape `postings/` uses.** Anchor
  postings are a small fraction of body postings, so a bisectable fixed-width
  table would buy nothing and add a second binary layout to keep in step.
- **`alen` is in the doc table, not the anchor shards**, because every
  candidate needs it and only a *matching* candidate needs its terms — a linked
  document is longer whether or not a single anchor word matches.
- **`DOCS_FIELDS` moved with the table**, which is the 2026-08-23 lesson that
  field set exists for: a key added while the schema string stayed put left an
  accelerator built minutes earlier still being read, and the two paths weighted
  the same document differently.

**15b. The differential arm ran at anchor ON as well as off.** 692 queries × 4
`top` values × 2 skipping modes over this repository's 1 237 documents:
**5 536 byte-identical comparisons at the default and 5 536 at `anchor = 2.0`,
zero mismatches** (2026-09-15). ⚠ **Run through an ad-hoc copy of the harness,
not `tools/differential/run.py`**, because `queryset.py::vocabulary` decodes
every walked file as UTF-8 and this repository's source dirs now hold ten files
that are not — a pre-existing harness defect, unrelated to this change, filed
as **W-184**. The comparison performed is the harness's own.

### Consequences

- **The differential law now covers the confidence block too.** `accel.ask`
  threads `stats_out` straight through to `rank()`, so both generators derive
  `df` over the same query hashes and report the same `n`, and `--fast` and
  `--scan` cannot disagree about how confident fux is
  ([SR-CONFIDENCE](0141_confidence.md) decision 9).
- ⚠ **The block bound is why `support` is not a corpus-wide count.** This plane
  skips documents it has *proved* cannot reach the top `k`, so it never scores
  them, while the reference scan scores everything. A corpus-wide *"47 documents
  matched"* would therefore differ between the two paths — a law break — so
  `support` counts only what both paths agree on. The better number is not
  available honestly, and the law is worth more than the better number.
- **`fux build` is a pure optimisation.** Nothing about correctness depends on
  the derived plane existing.
- **`rm -rf .fux/runtime` is always safe**, which is what lets the build be
  aggressive.
- **Two formats to keep in step.** The offset table's struct is a binary
  contract; `RUNTIME_SCHEMA` exists so a mismatch triggers a rebuild rather than
  a misread. **A schema string only moves when someone remembers to move it, and
  once nobody did** — which is why `docs_fields` is written into the manifest
  rather than trusted to the version string alone.
- **The doc table carries `archived`, `superseded` and `mtime`** because
  otherwise the accelerator could only re-derive them by matching `loc` against
  the configured directories, while the scan reads the record's own stamp — a
  second divergence, on the flag rather than the order.
- **`stats.json` stores RAW `total_flen`, not a pre-weighted total.** A stored
  weighted total is a **function of a tunable**: the moment a field weight
  became a key, `avg_wlen` would move on the scan path — which derives it per
  query — and *not* on this one, which read the baked number. Same corpus, two
  `avg_wlen`s: a differential-law break needing a **rebuild** to repair, which
  would make *"changing a knob needs no rebuild"* false. The plane's own record
  is [SR-RUNTIME-STATS](0125_runtime-stats.md).
- **The bound must stay an upper bound.** Any future scoring change — a sixth
  field, a different saturation — invalidates `block_bound` and the skipping
  argument with it. That is the veto below.
- **`fux build` is a two-lane build, and the second lane is not this
  record's.** The graph plane ([SR-GRAPH](0126_graph.md)) is written by the
  same `build()` call, from the same single pass over the committed shards —
  `_read_committed` returns the parsed records alongside the doc table so the
  graph plane costs no second read, and `DETERMINISTIC_FILES` covers
  `graph.json` too. **What is deliberately unchanged is the accelerator's own
  outputs and the differential law over them**: a graph plane that leaked into
  the lexical path would void every byte-identity claim here, so the graph
  lane's own eval asserts `ask` is unmoved through the CLI
  (`tests_e2e/test_relational.py::test_the_graph_lane_does_not_move_ask`).
- **`build()` takes the same optional `progress` seam `ingest.run()` does**,
  reporting its passes. `None` is the default and means silent, and the bar is
  stderr-only — so `DETERMINISTIC_FILES` and every byte-identity assertion here
  are untouched by construction. The rules are
  [SR-CLI](0101_cli-surface.md).
- **`accel.ask()` takes the same keyword-only weighting arguments `rank()`
  does**, with no-op defaults, so every existing caller is unaffected and the
  differential law between this path and the scan is unchanged.
- **A corpus with hashed URL records once had no accelerator at all** and paid
  4 248.8 ms rather than 27.2 ms — the whole accelerator result forfeited by
  following the documentation. Fixed in the *field shape*, never in this
  record's invariant ([SR-RECORD](0109_index-record.md) rule 2); the
  differential harness now carries a hashed record, which it never had.
- **`tools/differential/` now holds THREE arms, not one** (2026-09-12,
  [SR-NODE-SEARCH](0153_node-search.md)). This record owns the directory, so
  it says what is in it; the arms' *bars* belong to the records whose claims
  they test.
  - `goldens_grade.py` — `scan` vs `accelerator`, the arm this record exists
    for.
  - `node_arm.py` — **Python's reader vs Node's**, per document field. The
    comparison is on **parsed values, never on stdout bytes**: Python prints
    `--json` with `ensure_ascii=True` and `JSON.stringify` does not, so a byte
    diff fails on the first em-dash and measures nothing about the engine.
  - `graph_arm.py` — the in-memory graph plane's digest, both runtimes.
  - `adversarial_corpus.py` — writes a corpus whose ids straddle U+FFFF and
    whose scores tie exactly. ⚠ **It MUTATES the index it is pointed at**, so
    it runs in a copy or in CI, never against a repository anyone reads.

  ⚠ **The warning above still applies, and applies harder: no test imports any
  of them.** They are run by [`node-arm.yml`](../.github/workflows/node-arm.yml)
  on every push across 3 OSes × Node 20/22, which is a schedule rather than a
  gate — CI green is nobody's required check on `main`.
- ⚠ **`tools/differential/goldens_grade.py` grades two modes — `scan` and
  `accelerator` — and no test imports it.** ⚠ **It was `playground_grade.py`
  until 2026-09-12**, when [SR-WORK-ENVIRONMENTS](0052_WORK-environments.md) took its default
  corpus away and W-138 renamed it and made `--corpus`/`--goldens` required;
  the grading logic did not change, so the count below is still what that code
  produces. 🔴 **It has no live golden set to read** — the golden ladder's
  questions carry no `doc` + `max_rank` contract — so the differential law has
  no graded instrument today. Those two modes are exactly the pair the
  differential law binds together, so the harness is precisely a
  differential-law instrument. It has sat broken before, found by a sweep rather
  than by a test; **a live tool with no test importing it is a tool that can
  break silently.**
  **And it had, again (2026-08-28), three ways at once.** `golden["query"]`
  read a key the real goldens never had (`q`, not `query`) — a bare crash.
  `_rank_of` matched `r.id` (`"file:docs/…"`) against the goldens' bare `doc`
  paths, so no rank could ever match and every non-`known_failure` golden
  failed even when the top result was correct. And it called `scan_ask`/
  `accel.ask` directly with no `weighting`, so `.fux/tune.toml` was never
  applied — a systematic divergence from what `fux ask` actually returns, not
  noise. Fixed by routing both modes through `run_query` (the same entrypoint
  `cmd_ask` uses) with one shared `Tune`, loaded once per corpus; the harness
  now reproduces the retired consumer harness's own count exactly (41 pass / 0
  fail / 9 known-failure, on a corpus that no longer exists) with
  `scan == accelerator` holding. **Still no test
  imports it** — the warning above is unchanged by this fix.

### Alternatives considered

- **Commit the accelerator.** Rejected: it changes on every ingest and is a
  pure function of bytes already in git.
- **Score inside the accelerator and compare with a tolerance.** Rejected: a
  tolerance is a number nobody can defend. Structural identity needs none.
- **WAND/BlockMax as published, without the rounding-aware test.** Rejected on
  a real failure mode — this engine's sort is rounded and tie-broken by `id`,
  so the textbook strict inequality drops legitimate ties.
- **Skip the offset table; string-slice the block line for `mx`.** Rejected on
  measurement: 397 ms → 44 ms for the slice approach, and a `struct.unpack` at
  a computed index is strictly cheaper still, with the block line never touched.
- **A larger block size.** 128 is what was measured. Changing it is a
  measurement, not a preference.
- **Store weighted `mx`/`mnw`.** Rejected under decision 3: a weighted extremum
  cannot be stored once when the weights are query-time keys, and storing it
  anyway is what made the bound unsound at every non-default weight.

### Reference (required)

- The generator — [`src/fux/derive/_build.py`](../src/fux/derive/_build.py);
  the candidate path and the skipping proof —
  [`accel.py`](../src/fux/derive/accel.py) (its module docstring is the
  normative statement of the argument); the on-disk shapes —
  [`format.py`](../src/fux/derive/format.py) and
  [`runtime.schema.json`](../src/fux/derive/runtime.schema.json).
- The bound, exhaustively tested against every posting —
  [`tests/derive/test_bounds.py`](../tests/derive/test_bounds.py); the
  mutation-verified weighted case —
  [`tests/test_tune_boundary.py`](../tests/test_tune_boundary.py).
- **R3 PASS**, the measured basis for every number above —
  [`work/regression/2026-08-12-m2-accelerator/`](../work/regression/2026-08-12-m2-accelerator/report.md).
- The per-field bound's measured cost —
  [`work/regression/2026-08-23-fork3-per-field-bound/`](../work/regression/2026-08-23-fork3-per-field-bound/).
- Block-max WAND, the published technique this adapts — Ding & Suel, *Faster
  Top-k Document Retrieval Using Block-Max Indexes* (SIGIR 2011):
  https://engineering.nyu.edu/~suel/papers/bmw.pdf

### Veto condition

**Reopen this decision if** the two paths ever disagree, or if a scoring change
invalidates the block bound.

**And specifically: a weight that can reach the scorer without reaching the
bound.** Any new multiplier applied in `rank()` must be expressed through
`Weighting` so that `maximum` and the weighted `theta` see it. A multiplier
added directly in `rank()` re-opens exactly this defect, silently.

**How to check it:**

```bash
# 1. the differential law, the property the whole design rests on
# (scan is the default; --fast is what exercises this file)
diff <(fux ask "any query" --json --top 5) <(fux ask "any query" --json --top 5 --fast) \
  && echo IDENTICAL

# 2. the bound is still an upper bound over every posting
pytest -q tests/derive/test_bounds.py

# 3. the accelerator still produces no scores
grep -nE 'K1|B \*|idf\(' src/fux/derive/accel.py
# expect: only inside block_bound — score arithmetic anywhere else is the veto

# 4. the derived plane still has exactly one input
grep -n 'index_dir\|shard_path\|runtime_dir' src/fux/derive/_build.py
# expect: reads .fux/index only, writes .fux/runtime only

# 5. every score multiplier is routed through Weighting
grep -nE '\*=' src/fux/query/rank.py
# expect: only multiplies Weighting owns

# 6. the bound survives a NON-default weight, including the adversarial case
pytest -q tests/test_tune_boundary.py

# 7. the differential harness sweeps weights, not just the default
grep -n 'WEIGHTS' tools/differential/run.py
# expect: a tuple straddling 1.0 and reaching far enough to eat the block slack
```

---

## References

*Every source this record cites, gathered in one place. §2's **Reference
(required)** names the grounding; this is the complete list. An archived
document is never listed here — the body may name one, but archive is not
evidence.*

**Records** — [SR-LAWS](0001_LAWS.md) · [SR-CLI](0101_cli-surface.md) ·
[SR-ASK](0103_ask.md) · [SR-INDEX-LIFECYCLE](0108_index-lifecycle.md) ·
[SR-RECORD](0109_index-record.md) · [SR-RANKING](0111_ranking.md) ·
[SR-RUNTIME-STATS](0125_runtime-stats.md) · [SR-GRAPH](0126_graph.md) ·
[SR-TUNE](0135_tuning.md)

**Code**

- [`src/fux/derive/accel.py`](../src/fux/derive/accel.py)
- [`src/fux/derive/_build.py`](../src/fux/derive/_build.py)
- [`src/fux/derive/format.py`](../src/fux/derive/format.py)
- [`src/fux/derive/runtime.schema.json`](../src/fux/derive/runtime.schema.json)
- [`tests/derive/test_bounds.py`](../tests/derive/test_bounds.py)
- [`tests/test_tune_boundary.py`](../tests/test_tune_boundary.py)
- [`tools/differential/run.py`](../tools/differential/run.py)
- [`tools/differential/node_arm.py`](../tools/differential/node_arm.py)
- [`tools/differential/rungs.py`](../tools/differential/rungs.py)
- [`tools/differential/ladder_check.py`](../tools/differential/ladder_check.py)

**Measured evidence**

- [`work/regression/2026-08-12-m2-accelerator/report.md`](../work/regression/2026-08-12-m2-accelerator/report.md)
- [`work/regression/2026-08-18-ingest-and-index/report.md`](../work/regression/2026-08-18-ingest-and-index/report.md)
- [`work/regression/2026-08-19-w54/report.md`](../work/regression/2026-08-19-w54/report.md)
- [`work/regression/2026-09-12-node-arm-rungs/report.md`](../work/regression/2026-09-12-node-arm-rungs/report.md)
  — the harness's first run on the golden ladder, and the tune gap it found

**Papers and specifications**

- Ding & Suel, *Faster Top-k Document Retrieval Using Block-Max Indexes*
  (SIGIR 2011) — the technique the accelerator adapts
  <https://engineering.nyu.edu/~suel/papers/bmw.pdf>
