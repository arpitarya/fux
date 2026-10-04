---
type: Pre-registration
name: PRE-REG-NODE-3
description: "W-252 — frozen before the measurement: the Node differential arm on fux-lab rung-01000 and rung-10000, re-ingested to index v7 in throwaway copies. Endpoint 0 discordant of 801 per pass and identical graph digests; verify, --why, --receipt and --journal declared out of scope on the Node reader (SR-NODE-SEARCH decision 25). Supersedes PRE-REG-NODE-2 for the Node arm."
run: 2026-10-04-node-arm-2
item: W-252
frozen: 2026-10-04
supersedes: PRE-REG-NODE-2
---

# W-252 — the Node arm, pre-registered on data that counts

**Frozen 2026-10-04, before the arm was run for this purpose.** The run
directory holds this file and nothing else until the measurement lands. A
parity run, not a ranking run: no golden question, key or score is read, so
nothing is scored per query for quality. It is **`informed`** (below), which
costs nothing — the endpoint is *do two readers agree*, not *is either right*.

## 0 · Why this supersedes, and what it supersedes

[PRE-REG-NODE-2](../../benchmark/PRE-REGISTRATION-NODE-2.md) (frozen
2026-09-12) is **not** the document that names `fux-playground` —
[PRE-REG-NODE](../../benchmark/PRE-REGISTRATION-NODE.md) §4 is, and NODE-2
superseded it for exactly that reason on the day it was written. ⚠
[SR-NODE-SEARCH](../../../records/0153_node-search.md) Consequences still reads
*"PRE-REGISTRATION-NODE §4 names `fux-playground`"*; that is true of the first
document and **stale as a description of the live one**. W-252's premise,
*"its live pre-registration names the playground"*, inherits the same
confusion. This document does not edit either; it says so once.

NODE-2 stays frozen and is superseded **in the part below**, for four reasons
that are about the instrument, never a result:

1. **It cannot be run as written.** It says the rungs are read in place and
   verified against their manifests, and `rungs.resolve` does exactly that —
   but the lab's rungs carry **index format v5** and this engine (v7) refuses
   every verb on them. The arm must run on a **re-ingested copy**, and a copy's
   index root hash no longer equals the manifest's (§3).
2. **It names three comparisons (N5 `find`, N6 `ask`/`answer`, N7 graph digest)
   and the arm now covers six surfaces** — `explain`/`graph`/`path`, the MCP
   server, `fux.api`, and the published bundle against the module tree, none of
   which NODE-2's bar mentions (SR-NODE-SEARCH decisions 9–14).
3. **It says nothing about what the Node reader does not do.** `verify`,
   `--why`, `--receipt` and `--journal` have no Node twin (W-107 R6) and
   SR-NODE-SEARCH decision 25 (2026-10-04) declares them out of scope (§6).
4. **It predates W-242.** The Node reader now reads `.fux/runtime/` (Tier 1)
   and builds it itself (Tier 2, 2026-10-03). The tier the arm runs against
   has to be named (§4).

**N8 (the analyzer and hash, pinned not sampled) is not re-run here.** It is a
unit-test claim, held by `node/test/` and `tests/test_node_twins.py`, and this
document does not claim it.

## 1 · The claim under test

> A Node reader of an index this engine wrote returns what the Python reader
> returns, on every verb, library call, MCP tool and bundle the arm covers:
> same ids, same order, same locators, same band, same payload keys; scores
> equal at `round(9)` ([SR-RANKING decision 8a](../../../records/0111_ranking.md));
> and Node's in-memory graph plane equals Python's by digest.

## 2 · Where the data comes from, and where it does not

| | |
|---|---|
| corpora | **`rung-01000` and `rung-10000`**, generation 3, in `~/my_programs/fux-lab/corpora/golden/` — [L9](../../../records/0011_LAW-9-use-record.md): **never `fux-playground`**, never a corpus an agent invented |
| lab commit | `fux-lab` HEAD **`ed46bfefbe18bc35139ed2a909a2d4382fc15cbd`**. ⚠ That repository tracks no rung — `corpora/` is untracked in it, and its own working tree is dirty in `.gitignore`, `shared/generate/make_corpus.py`, `shared/regress/run.py`, none under `corpora/`. **The lab sha therefore pins the lab, not the bytes** |
| what pins the bytes | each rung is its own git repository. `rung-01000` HEAD **`b73348d56edf5c0e16aa6f344ad629ba1dd00c37`**, `rung-10000` HEAD **`cac5699ce2a48c8ded32a8f5e5df83234d87021e`**, each equal to `rung_head_commit` in the committed manifest [`work/golden/ladder/rung-NNNNN.index`](../../golden/README.md); each with **one** untracked file, `fux.toml` (the rung's own config). And the manifests: `rung-NNNNN.sha256`, one hash per document (1 000 and 10 000 rows) and `index_root_sha256` `103430af…` / `f9e4214f…` |
| verified clean, 2026-10-04 | `rungs.verify(name, <lab rung>)` returned `[]` for both: every document hash and the v5 index root equal the manifest. Phase 2 repeats it **before** the copy and records the output |
| index format | the lab's rungs are **v5** (engine `fux 3.0.0-alpha.5` at `80495b44`). This engine's index is **v7**. The 2026-09-12 run read the lab in place because the formats then matched; that is no longer possible |
| what the arm runs on | a **throwaway copy** of each rung (`cp -R` into the session scratchpad), **re-ingested to v7 by this engine** (`fux doctor --fix`, `fux ingest --full`, `fux build`) at the fux commit in §5. The documents in the copy are the lab's bytes; the **index is regenerated**, which is the point |
| what is never touched | **nothing in `~/my_programs/fux-lab` is modified, re-ingested, rebuilt or deleted** ([SR-WORK-OPEN-QUEUE](../../../records/0051_WORK-open-queue.md) rule 53, *the lab persists*). The copies are scratch and are deleted by the session that made them |
| precedent | the 2026-09-29 run ([`node-reader-per-call`](../2026-09-29-node-reader-per-call/report.md)) did the same on a scratch copy of `rung-10000` and ran `fux doctor --fix` on the copy only. Its lab was already v5 then (`output.toml` predating `[cli] max_headings`); **nothing about the lab changed between then and now** — the engine moved from v6 to v7 |
| key | 🔴 **No key is read** ([L11](../../../records/0013_LAW-11-sealed-answer-key.md)). The arm compares two readers against each other and needs no ground truth. `node_arm.py` takes its queries from `queryset.generate(root)`, which tokenises the **source documents** and is called with no golden list; `rungs.py` opens `work/golden/` only for `seed/`, which L11 permits. Neither opens `questions/` or any answers path. Phase 2 reads nothing under `work/golden/` |

A copy's index root hash differs from the manifest's by construction (a v7
index is not a v5 index), so `--rung` — which verifies that hash and **refuses**
on mismatch — is not used. The arm is pointed at the copy by path (§5) and the
**documents** are verified against the manifest instead.

## 3 · What the arm covers — every verb, and what it compares

`tools/differential/node_arm.py <copy> --queries corpus` ⚠ **`--queries corpus`
is mandatory**: for a bare path the default is `fixed`, the hand-written
list for *this* repository, which would run 29 queries that mean nothing on a
rung.

| surface | verbs / calls | compared as |
|---|---|---|
| ranking | `find`, `ask --band` at `--top` 1, 5, 20 | parsed values: `id`, `loc`, order, `title`, `archived`, `tie`, `headings` byte-equal; `score` at `round(9)`; the ten confidence fields byte-equal |
| graph lane | `explain`, `graph`, `path` | whole parsed payload, order byte-equal, `score` at `round(9)` |
| MCP | `tools/list`, `fux_search`, `fux_related`, `fux_passage` over one stdio session each | per call, structured content equal |
| library | `fux.api` / `node/src/index.mjs`: `find`, `ask`, `explain`, `graph`, `path`, `answer` | whole payload at `round(9)`; the `answer` lane asserts that Node never cites a decoded document it cannot reproduce (decision 11) |
| bundle | the published `fux.mjs` against the module tree it was built from: `find`, `ask`, `answer`, the library, MCP | whole parsed payload, exact |
| graph digest | `tools/differential/graph_arm.py <copy>` (N2) | Node's in-memory plane bytes against Python's, digest equal |
| build | `fux build` in the copy (Python), then `node node/fux.mjs build` into a second copy | every file under `.fux/runtime/` byte-equal **except `stamp.json`** |

**Two passes per rung, both pre-registered:** `--python-tune on` (the contract:
what `fux find` answers, tune and all) and `--python-tune off` (the
transcription: `--no-tune` on both sides). The rungs' `tune.toml` is the
template the doctor writes, so both passes should be the same run; running both
costs minutes and makes a discordance attributable.

### N — the denominator, stated in advance

Read from `node_arm.py`'s job construction (`main()`), then counted by calling
its own `corpus_queries` and `Arm` on throwaway v7 copies **without running any
Node comparison**. The same count held for both rungs.

| component | count | how |
|---|---|---|
| queries | **125** | `corpus_queries(root, 120)` returns 120 (the fixed-rule set capped by position; the full set is larger), plus the 5 hazard `PINS` (`zzqq`, `nonascii`, empty, three spaces, `zzzzzznomatch`), none of which the 120 contain |
| ranking jobs | **750** | 125 queries × 3 tops × 2 verbs (`find`, `ask`) — the figure of the 2026-09-12 run |
| `explain` | **8** | `--graph-cap` 8; ids by position `sorted(ids)[::len//8][:8]` (step 125 at 1 000, 1 250 at 10 000) |
| `graph` | **8** | the first 8 queries (all non-blank) |
| `path` | **7** | consecutive pairs of the 8 picked ids |
| bundle, per verb | **24** | `--bundle-cap` 8 non-blank queries × top 1 × {`find`, `ask`, `answer`} |
| MCP, bundle-MCP, API, bundle-API | **4** | one job each; each is a whole session and compares every call in it |
| **N** | **801** | 750 + 8 + 8 + 7 + 24 + 4, **per pass, per rung** |

So the run is **4 passes × 801 = 3 204 jobs** (2 rungs × 2 passes). If the
graph lane is skipped (`graph_lane_ready` false — it needs a fresh derived
plane, which `fux build` provides) N falls to 778; **a skipped graph lane is a
failed run, not a smaller N**, and phase 2 aborts on it.

## 4 · Which W-242 tier the arm runs against

**Tier 2, landed 2026-10-03** (`194d0ca4`): the Node reader reads
`.fux/runtime/` under the same freshness check as Python (Tier 1) **and builds
the plane itself** (`node fux.mjs build`). So:

- the ranking, graph, MCP, API and bundle jobs run with a **Python-built**
  plane present and fresh (`fux build` in the copy), which Node then reads;
- the **build** row above compares that plane with a **Node-built** one, so
  both writers of the plane are covered and the reader is not asked to trust a
  plane only one of them produced.

A change to `node/src/derive/` or to the freshness check between this freeze
and the run voids the run; the engine commit in §5 is recorded for that reason.

## 5 · The exact commands phase 2 runs

`$ENG` is this repository. `$W` is a fresh scratch directory. `fx` is
`$ENG/.venv/bin/python -m fux` with `PYTHONPATH=$ENG/src`. Nothing is run at
the repository root that writes `.fux/`.

```bash
ENG=/Users/arpitarya/my_programs/fux
LAB=~/my_programs/fux-lab/corpora/golden
cd $ENG && git rev-parse HEAD                    # record; src/, node/, tools/differential/ must equal the freeze commit's
git -C ~/my_programs/fux-lab rev-parse HEAD      # expect ed46bfef…
for r in rung-01000 rung-10000; do
  git -C $LAB/$r rev-parse HEAD ; git -C $LAB/$r status --short      # expect b73348d5… / cac5699c…, "?? fux.toml" only
  # 1. the lab rung is untouched and matches its committed manifest — BEFORE the copy
  $ENG/.venv/bin/python - <<PY
import sys; sys.path.insert(0, "$ENG/tools/differential"); import rungs
print("$r", rungs.verify("$r", rungs.corpora_root() / "$r"))        # must print []
PY
  # 2. the throwaway copy, migrated to v7 by this engine
  cp -R $LAB/$r $W/$r && cd $W/$r
  fx doctor --fix && fx ingest --full && fx build
  # 3. the copy's DOCUMENTS still equal the manifest (the index is expected to differ)
  #    hash every row of work/golden/ladder/$r.sha256 against $W/$r/<path>; 0 missing, 0 drifted
done
# the arm, both passes, both rungs — evidence in a directory per rung so file names do not collide
for r in rung-01000 rung-10000; do
  for t in on off; do
    $ENG/.venv/bin/python $ENG/tools/differential/node_arm.py $W/$r --queries corpus \
        --python-tune $t --evidence $ENG/work/regression/2026-10-04-node-arm-2/evidence/$r
  done
  $ENG/.venv/bin/python $ENG/tools/differential/graph_arm.py $W/$r
  # build equality: a second copy, runtime removed, Node builds it, diff except stamp.json
  cp -R $W/$r $W/$r-nodebuilt && rm -rf $W/$r-nodebuilt/.fux/runtime && (cd $W/$r-nodebuilt && node $ENG/node/fux.mjs build)
  diff -rq $W/$r/.fux/runtime $W/$r-nodebuilt/.fux/runtime        # only stamp.json may differ
done
```

The `--evidence` flag writes `node-arm-corpus-{contract,transcription}.jsonl`
(the label is `corpus` because a path, not `--rung`, names the root); each
carries a `_condition` row naming the copy's path. Phase 2 files the rung in the
report. The copies are deleted afterwards; the lab is not.

## 6 · Out of scope on the Node reader — declared, not failed

[SR-NODE-SEARCH decision 25](../../../records/0153_node-search.md) (2026-10-04):
**`fux verify`, `--why`, `--receipt` and `--journal` do not exist on the Node
reader** and are not planned. This arm does not exercise them, and **their
absence is not a discordance, a skip or a gap to close** — it is the declared
boundary of the claim in §1.

The consequence is the one W-252 asked for: *every difference in what the arm
covers is a defect*, and *a verb Node declares out of scope* is not a difference
at all. The two sentences read the same way because the line between them is
drawn here, in advance, and not after a number.

## 7 · The endpoint, and what a result means

**PASS** — on all four passes: **0 discordant of 801**, and **graph digests
identical** (`graph_arm.py` prints IDENTICAL), and the **build** row shows no
file but `stamp.json` differing, and the source rungs verify `[]` before the
copy and the copies' documents verify against the manifest. The exit code of
`node_arm.py` is 0.

**Anything else is a defect to file, never a threshold to move**
([SR-RS decision 10b](../../../records/0133_predictions.md)): no tolerance is
widened, no query dropped, no job re-classified, no lane skipped to reach zero.
A non-zero count names the job, and the job names the surface. An ambiguous
result goes to Arpit, not to whoever ran it.

- A `round(9)` score difference is already inside the ruled contract; it is not
  a discordance and the pre-registration does not add a looser one.
- A pass that fails to *run* (a refused rung, a skipped lane, a Node crash on a
  query) is a failed run: the arm already counts a reader that crashes as a
  discordance.
- **A green result is filed, not celebrated** (NODE-2 §2). It is also the only
  thing that lets [SR-NODE-SEARCH](../../../records/0153_node-search.md)
  Consequences stop saying *"cannot be called green yet"*.

## 8 · Classification, authorship, and what this cannot show

**`informed`**, permanently. The same model family built the Python reader, the
Node reader, this arm and this pre-registration, so agreement is parity and not
evidence that either is right — a transcription error shared by both would pass
(the 2026-09-12 run's own headline: the arm was green for a month because both
sides ignored the same things). The endpoint is parity, so this costs nothing.

| artifact | author | could reach |
|---|---|---|
| the rungs | Arpit's lab builder, 2026-09 (generation 3) | the seed corpus; no query of this run |
| the query set | `queryset.py`'s fixed rule over the copy's documents | the documents only — no key, no judgments, no prior score |
| the harness | earlier sessions, unchanged by this one | the corpora and the manifests |
| this document and the run | Claude Code, one session family | the code and the rungs; **not** `work/golden/` |

What this cannot show: quality (nothing is scored), agreement on a corpus with
index features the rungs lack, agreement on Windows or Linux libm (one machine,
one OS — the cross-OS half of NODE-2 §4 remains *aspirational until somebody
runs it there*), or the six-rung middle of the ladder. Only the two ends are
run, per NODE-2's own cadence.

## 9 · What would make this pre-registration wrong

- The graph lane skipping silently (N would read 778, not 801).
- A change to `node_arm.py`'s job construction before the run — the count in §3
  is of the harness as frozen; a different count is reported, not absorbed.
- A rung copy whose documents drift from the manifest — the run names a corpus
  it did not measure.
- The query set stopping to be corpus-derived (`--queries fixed` on a path).
