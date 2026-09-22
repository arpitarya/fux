---
type: Report
description: "A baseline capture of generation 2's `set-2-u` — 125 Claude-authored questions — on `rung-01000` at pinned engine `3f824de0`. One arm, no comparison, no score, no verdict about the engine. The deliverable is one hand-off file for Arpit."
run: 2026-09-22-golden-set-2u-rung-01000
item: W-215
classification: informed
filed: 2026-09-22
pre_registration: work/regression/2026-09-22-golden-set-2u-rung-01000/PRE-REGISTRATION.md
---

# REPORT — `set-2-u` baseline capture, `rung-01000`

🔴 **This is a BASELINE CAPTURE of a NEW question set. It is NOT a paired
comparison, and it files NO verdict about the engine.** One arm, one rung, one
engine; no baseline arm, no treatment arm, no endpoint, no direction, no delta
and no `VERDICT.md`. Nothing here is evidence that any engine behaviour
improved, regressed or held.

🔴 **There is no correctness column and there cannot be.** No answer key reached
this session by any route, a paste included
([L11](../../../records/0012_LAW-11-sealed-answer-key.md)). `just golden-state`
returned **`locked`** before anything else ran, and it was not changed. Nothing
in this run opened, listed, globbed, stat'd, hashed or counted a key directory
on either spelling, and every recursive search this run made over `work/`
excluded the golden tree. **The word *right* does not appear about any answer in
this document.**

🔴 **`classification: informed`, permanently, and the reason is one line:** the
set's author and its runner are the same model family. **This run is not blind
and is described as blind nowhere.**

---

## 1 · What ran

| | |
|---|---|
| rung | **`rung-01000`** — 1 000 documents, of which 28 seed |
| corpus | `~/my_programs/fux-lab/corpora/golden/rung-01000` |
| question set | **`set-2-u`** — generation 2, Claude-authored, **125 questions**, ids `s2u-001`…`s2u-125` |
| engine sha | 🔴 **`3f824de03a944a0d2e9cffb7a8ba09b439c17d02`** |
| engine version | **`fux 3.0.0-alpha.2`** |
| how it was pinned | a detached `git worktree` at that sha with its **own venv**, outside the repository |
| repo HEAD while the harness ran | `8eb8274f` — the pre-registration's own commit; stamped on every row as `repo_head` |
| calls | 125 × (`ask --json --band --why --top 10` + `answer --json`) = **250** |
| wall clock | 2026-09-22 **16:59:35Z → 17:00:08Z** (33 s) |
| rows written | **125** predictions, **125** hand-off — ids identical and in the same order, 125 unique |

**Why `engine_commit` and `repo_head` differ, and why that is not a defect:** the
harness (`tools/quality-controls/golden_run.py`) ran from the repository, the
**engine** ran from the pinned worktree. The two columns carry the two facts
separately so neither is hidden.

🔴 **The live repository tree was dirty and this run does not contain its
change.** A concurrent session is building **W-214** — `weak` demoted from a
refusal to a signal, `answerable` back to `band != none` — in
`src/fux/query/confidence.py`, `node/src/query/confidence.mjs` and two test
files, uncommitted. The repository's venv is an **editable** install pointing at
that tree, so the pinned worktree is what kept this capture's engine nameable.

⚠ **Consequence, declared in the pre-registration before any row existed:** every
`answerable` value below carries the **OLD, pre-W-214 semantics** — `band not in
(none, weak)`. When W-214 lands, this column describes a behaviour the engine no
longer has. **The `band` column is unaffected.**

## 2 · 🔴 The rung was RE-INGESTED once, and this is what moved

The pre-registration's condition fired: engine version **and** `engine_commit`
both differed from `work/golden/ladder/rung-01000.index`, the diff between them
touches `query/analyzer.py`, `ingest/extract.py` and `ingest/parse.py`, and
`fux doctor` at the pinned engine reported **`no readable index`** on two checks
against the committed alpha.1 index.

| step | result |
|---|---|
| `ladder_check.py`, all four checks incl. `seed_drift`, before | **8 rungs, manifests consistent, nesting verified**; `rung-01000` seed drift **none** |
| `rungs.verify(documents_too=True)`, before | **0 problems** over 1 000 documents |
| `fux ingest --full`, pinned engine, `tune.toml` **unedited** | 1 000 docs, 1 000 changed, **0 not indexed, 0 skipped**, 253 shards, 4.7 s |
| `rungs.verify(documents_too=True)`, after | **0 document problems** — the only disagreement was the index root, exactly as predicted |
| coverage recomputed from the new index | 1 000 documents · **103** archived · **101** superseded · **1 000** carrying `mtime` — **identical to the declarations**, so `rung-01000.coverage` needed no edit |
| `ladder_check.py` + `seed_drift`, after the record update | **clean** |

**What was updated:** `work/golden/ladder/rung-01000.index` — engine
`3.0.0-alpha.1 → 3.0.0-alpha.2`, `engine_commit` `3c885386 → 3f824de0`,
`index_root_sha256` **`fc53e0cc… → 17fe414e…`**, `rung_head_commit`
`d0912b74 → 69cbe802` (the re-indexed commit inside the rung's own repo).

⚠ **Two things a later reader needs from this.** (a) **Every golden number filed
before today against `rung-01000` names an index root that no longer exists** —
`fc53e0cc…` — and may not be differenced against anything here. (b) **The ladder
is now heterogeneous:** only `rung-01000` carries an alpha.2 index; the other
seven rungs still record `3.0.0-alpha.1` / `3c885386`. **A multi-rung run started
today would be running two engines' indexes unless it re-ingests the rest.**

## 3 · Ranking configuration — read, not edited

`[bm25f] b = 0.15` · `[bm25f] anchor = 0.0` · `[confidence] separation_floor =
0.1`, from the rung's committed `.fux/tune.toml`. **No value was changed by this
run.** W-144's `b = 0.75` upgrade trap was not present.

## 4 · The numbers — descriptive, `k = 10`

🔴 **`k = 10` everywhere**, because `--top 10` is what the ranked list is capped
at. There is no `k = 5` figure here and none may be derived from these rows.

### S2 · Band distribution

| band | n | share |
|---|---:|---:|
| `grounded` | 42 | 33.6 % |
| `partial` | **59** | **47.2 %** |
| `weak` | 24 | 19.2 % |
| `none` | **0** | 0 % |

🔴 **`band: weak` ⇔ `answerable: false` on 125 of 125 rows**, with no exception
in either direction — `answerable: true` on all 42 `grounded` and all 59
`partial`, `false` on all 24 `weak`. That is the same equivalence generation 1
showed on three sets, now on a set that did not exist then.

🔴 **The middle band is not thin on this set — it is the largest one.** 59 of 125
questions land in `partial`. ⚠ **This is stated as an observation about
`set-2-u`, not as a change**: generation 1's sets retired, the rung's index has
been rebuilt at a different engine, and the pre-registration forbids differencing
against any generation-1 figure. **Whether `partial` is large because the set is
different or because the engine is, this run cannot say** — that needs two arms.

### S1 · Declines

🔴 **0 of 125.** `fux answer` returned text on **every** call, including all 24
the band called `answerable: false`. **0 uncited answers** — every one of the 125
carries at least 4 citations. ⚠ **Consequence for whoever scores this:** an
`abstain_correct` computed from a null answer would be **0 by construction**, and
the only abstention signal in these rows is the `band`/`answerable` pair.

### S3 · Empty ranked lists

**0 of 125.** Every question returned a full list of **10**.

### S4 · Funnel gates

🔴 **125 of 125 rows carry all five integers** — `reachable`, `in_window`,
`placed`, `answered`, `cut_score`. The funnel W-204 phase D could not compute at
all is computable from this hand-off.

| gate | value across 125 questions |
|---|---|
| `reachable` | **1 000 on every question** — every document in the rung, with no variation |
| `in_window` | **20** on 124, **19** on one (`s2u-076`) |
| `placed` | **10 on every question** |
| `answered` | **1 on every question** |
| `cut_score` | 2.73 – 17.70 |

⚠ **Two of those five are not measuring the engine on this rung, and a funnel
figure that treats them as if they were is wrong.** `placed: 10` **is the
`--top 10` cap**, not a property of the ranking; and `reachable: 1000` is
saturated — the first gate discards nothing at 1 000 documents, so the funnel
here is `1000 → ~20 → cap → 1`. The gate that is doing work is `in_window`, and
it is **effectively constant too**. **Whether `reachable` ever becomes selective
is a question about larger rungs and this run does not answer it.**

### S5 · Latency — ⚠ DESCRIPTIVE, not a benchmark

| verb | p50 | p90 | max |
|---|---:|---:|---:|
| `ask` | 140 ms | 150 ms | **194 ms** (`s2u-001`) |
| `answer` | 122 ms | 128 ms | **162 ms** (`s2u-040`) |

⚠ **This may not be cited against
[SR-WORK-BENCHMARK](../../../records/0053_WORK-benchmark.md)'s captures.** One
arm, no interleaving, and a **shared machine with another Claude session actively
editing and running tests in the same repository throughout**
([SR-WORK-SESSION](../../../records/0060_WORK-session.md) decision 12). The
spread is narrow enough that nothing here looks like contention, which is an
observation and not a control.

### The emptiest results

| id | why it is here | band |
|---|---|---|
| `s2u-085` | **shortest answer by a factor of two** — 640 characters, 6 citations; the next shortest is 1 471 | `weak` |
| `s2u-033` | 1 471 characters, 7 citations | `partial` |
| `s2u-107` | **lowest cut line**, 2.73 | `partial` |
| `s2u-076` | the **only** question with `in_window: 19`; also the 4th-lowest cut line | `weak` |

Median answer length is 6 303 characters; median citation count is 12.

## 5 · 🔴 What looked wrong

**One finding, and it is about the HAND-OFF rather than the engine.**

🔴 **87 of 1 584 citations carry an empty `lines` and a `doc` that is not a
document path.** They look like this:

```
{"doc": "seed/09-dock-scheduling-wiki-export.html#p2", "lines": ""}
{"doc": "seed/06-re-fw-telematics-cutover.eml#p0",     "lines": ""}
{"doc": "ext/sibling/a07-halberd-dock-wiki.html#p8",   "lines": ""}
```

**Every one of them is a non-prose decoded document** — `.html`, `.eml`,
`.yaml` — whose locator grammar is `path#pN` (a decoded part) rather than
`path:L30-L46` (a line range). `golden_run._cite()` splits on the last `:` and
keeps the tail only when it starts with `L`, so for these the whole locator stays
in `doc` and `lines` is correctly left empty rather than invented.

⚠ **The hazard is a JOIN, and it is silent.** **28 of 125 questions are
affected**, across **30 distinct documents**. A scorer that joins
`citations[].doc` against a key listing documents by path will **not match** those
87 rows by exact string, and the failure looks like *fux cited nothing relevant*
rather than *two spellings of one document*. 🔴 **`ranked` is unaffected — 0 of
1 250 ranked entries carry a `#`** — so the two lists in the same row use
different spellings of the same document, which is exactly the shape that passes
a spot check.

**Not fixed here, deliberately.** Changing `_cite()` now would change the filed
rows after the pre-registration froze, and the right form is a judgement about
what a key lists. **What a scorer must do in the meantime: strip `#pN` from
`citations[].doc` before joining, and treat `lines: ""` as *whole decoded part*,
never as *no locator*.** Filed as the thing owed.

**Nothing else looked wrong.** 0 failed calls · 0 empty results · 0 uncited
answers · `freshness: current` on 125/125 · `source: refer` on 125/125 · one
`engine_commit` on every row · one `rung` on every row · 125 unique ids, all in
the `s2u-` namespace, so no collision with a retired set is possible.

## 6 · Two observations offered to the scorer, with no claim attached

🔴 **Neither is a finding about quality. Only a key can turn either into one.**

- **11 of 125 questions rank an `ext/` document first** (`s2u-022`, `030`, `033`,
  `034`, `039`, `042`, `045`, `048`, `052`, `058`, `085`), and **7 rank an
  `/archive/` document first** (`s2u-009`, `020`, `028`, `042`, `044`, `048`,
  `093`; `042` and `048` are in both lists). `ext/` is the hard-negative half of
  the rung and `archive/` is its retired half — **which is a fact about where the
  document sits, not about whether it answers the question.**
- **`cut_score` is HIGHEST on the band that refuses.** Medians: `weak` **8.48**,
  `partial` 7.48, `grounded` 7.24. The band withheld where the cut line was
  higher, which is the opposite of the intuition the threshold was built on. ⚠
  **Descriptive, single-arm, and not a re-run of W-213** — it is consistent with
  that verdict's finding and is not evidence for it.

## 7 · 🔴 Headroom ([SR-RS](../../../records/0133_predictions.md) decision 22)

**Undefined in both directions, and disclosed as undefined rather than omitted.**
Decision 22 governs a **paired** run; this has one arm and no endpoint, so
*improvement* headroom (queries not right in both arms) and *regression* headroom
(queries not wrong in both arms) have no arms to be computed over. **Neither is
zero, and neither is a null** — 22d's *Inconclusive* is not what this is either,
because nothing was tested.

**The structural ceiling on any future paired run that uses this set at this
rung is 125 questions.** The **usable** pool is smaller and this run cannot
measure how much smaller, because the answerable/unanswerable split lives in the
key. 🔴 **The nearest measured prior — 7–23 answerable questions per set per rung
on generation 1's three sets
([`2026-09-22-w168-step-inputs`](../2026-09-22-w168-step-inputs/report.md)) — is
about RETIRED sets and is cited as context, never as a property of `set-2-u`.**
Whether generation 2 carries a bigger pool is the thing W-215 was filed to change,
and **the first artifact that can answer it is a score, not this run.**

## 8 · 🔴 The deliverable — what Arpit picks up

> ### **`evidence/handoff-set-2-u.jsonl`** — 125 lines, one per question, self-contained.

Each line carries `id`, `question`, `answer_text`, `citations[{doc, lines}]`,
`ranked[10]`, `answerable`, `band`, `gates{reachable, in_window, placed,
answered, cut_score}`, `rung` and `engine_commit` — plus `freshness`, `source`,
`arm`, `repo_head`, `ask_ms` and `answer_ms`, which are additive and cost a
key-reading scorer nothing.

🔴 **There is no golden answer in that file and there never will be.**
`answer_text` and `citations` are **what fux produced**. `gates` is the five
integers from `--why` and **nothing else from the derivation**.

`evidence/predictions-set-2-u.jsonl` is the machine twin — `{id, ranked,
answerable, band}` — and exists so a join can be checked without reading prose.

🔴 **Scoring is not this session's and was not attempted.** It is
[`tools/golden-score/score.py`](../../../tools/golden-score/score.py), **started
by Arpit from his own shell**. It was not invoked here, in any form.

## 9 · Reproduce

```bash
git worktree add <tmp>/engine-pin 3f824de03a944a0d2e9cffb7a8ba09b439c17d02 --detach
cd <tmp>/engine-pin && uv venv .venv && uv pip install --python .venv/bin/python -e .
cd ~/my_programs/fux-lab/corpora/golden/rung-01000 && <tmp>/engine-pin/.venv/bin/fux ingest --full
cd ~/my_programs/fux
python3 tools/quality-controls/golden_run.py --rung rung-01000 --sets 2-u \
    --fux <tmp>/engine-pin/.venv/bin/fux \
    --engine-commit 3f824de03a944a0d2e9cffb7a8ba09b439c17d02 \
    --evidence work/regression/2026-09-22-golden-set-2u-rung-01000/evidence
```

⚠ **The re-ingest is part of the reproduce path, not a fix applied once.** A
clone with the alpha.1 index will not reproduce these rows.

## Authorship

**`classification: informed` — permanently.**

| artifact | authored by | could reach |
|---|---|---|
| `set-2-u`'s questions **and answers** | **Claude**, in a prior designated session under L11 decision 6's per-set carve-out | `work/golden/seed/` only |
| this run, the harness change, the pre-registration, this report | **Claude Code**, this session | the questions (`id` + `question`), the corpus, the ladder records — **no answer, by any route** |
| the corpus and the ladder | a 2026-09-12 builder + generator, rebuilt 2026-09-21 | **nothing evaluative**; no question was read by anything that produced a document |
| the engine | the repository's history to `3f824de0` | **none** |

🔴 **The first row is why this is informed and why nothing changes it: the set's
author and its runner are the same model family.** No separation of sessions
touches that, and no later care converts it.

⚠ **Independently sufficient even if that row vanished:** every golden number in
this project is `informed` permanently from the first unlock, 2026-09-22, and the
tree has been unlocked once.

**This session read no answer.** The tree was `locked` at the start and was not
changed; no lock-state command was run other than the read-only `just
golden-state`; the directory L11 decision 3 permits — and the older singular
spelling decision 5 closes — was not opened, listed, globbed, stat'd, hashed or
counted; and `set-2-u.jsonl` was committed after checking its **keys only**, all
125 rows being exactly `{"id","question"}`.

⚠ **One guard fired during this session and it fired correctly.** The first
attempt to write this report was blocked by `.claude/hooks/guard-golden-answer.sh`
because the **prose** of the Authorship section spelled a key directory's path.
The sentence was reworded to cite L11's decisions instead
([SR-WORK-GOLDEN](../../../records/0066_WORK-golden.md) decision 7's convention).
**No guard was weakened, and nothing in that directory was reached.**
