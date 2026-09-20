---
type: Pre-Registration
description: "W-204 phase A: every question of both golden sets through `fux ask` and `fux answer` on all eight rungs, at one frozen HEAD, producing one human-readable RUNG-NNNNN.md per rung. It files NO score and predicts NOTHING about correctness — its only claims are the surface ones, per set."
run: 2026-09-20-golden-ladder-outputs
item: W-204
status: frozen
filed: 2026-09-20
---

# PRE-REGISTRATION — W-204 phase A, the eight-rung output pass

🔴 **FROZEN, and committed before any number exists**
([SR-RS](../../../records/0133_predictions.md) decision 10b). A threshold or a
claim added to this document after the first row is filed is a moved threshold,
whatever it is called.

---

## 1 · What this run is, and what it explicitly is NOT

**It is an output pass.** For every question in both sets, on every rung, it
records **what `fux ask` ranked, what `fux answer` returned or declined, and
what it cited** — and stops there. The deliverable is one human-readable
`RUNG-NNNNN.md` per rung, derived mechanically from the machine hand-offs so the
two cannot disagree.

🔴 **It files no score, no accuracy and no verdict, because no Claude session
can.** No answer key reaches this session by any route, **a paste included**
([L11](../../../records/0012_LAW-11-sealed-answer-key.md)). A key **may** sit on
this machine, at the one address L11 decision 3 has permitted since 2026-09-18;
it is Arpit's, and it is closed to this session **on both spellings**, exactly as
decision 5 states. Nothing in this run opens, lists, globs, stats, hashes or
counts either of them, and every recursive search this run performs over `work/`
excludes `work/golden/`.

🔴 **There is no column for *correct*.** That column is born in W-204 phase D,
after Arpit opens the key, and nowhere earlier. A per-rung document is an
**output** record: it carries what fux did and never what it should have done.

⚠ **A report that guessed at correctness would train the next reader to trust a
guess**, which is why this document states the prohibition rather than assuming
the prompt carries it.

## 2 · The frozen engine

| | |
|---|---|
| engine commit | 🔴 **`538f34978141a54b28b78b7ea76d36969cf63aa0`** — frozen here, before any call |
| engine version | `fux 3.0.0-alpha.1` |
| index format written | **`fux.index.v4`** ([W-194](../../../archive/open/W-194-delete-hashed-meta.md), 2026-09-20) |
| reader | Python only. The Node reader is not an arm of this run |

**Later commits in this run touch no engine byte, and that is checkable rather
than asserted.** This run files its own artifacts under `work/regression/`,
`work/golden/ladder/` and `tools/quality-controls/`; the invariant is

```bash
git diff --stat 538f3497..HEAD -- src node .fux/tune.toml   # must be empty
```

and the closing report states the result of running it.

## 3 · The eight rungs, and both sets, and both verbs

**Eight rungs**, the whole ladder, smallest to largest:

| rung | documents |
|---|---:|
| `rung-seed` | 20 |
| `rung-00100` | 100 |
| `rung-00200` | 200 |
| `rung-00500` | 500 |
| `rung-01000` | 1 000 |
| `rung-02000` | 2 000 |
| `rung-05000` | 5 000 |
| `rung-10000` | 10 000 |

**Both sets, kept apart at every step and never pooled** —
`work/golden/questions/set-1.jsonl` (**125** questions, Codex-authored) and
`set-2.jsonl` (**124**, Claude-authored). 🔴 **The gap between the sets is the
measurement**; a figure spanning both erases exactly what two authors were
commissioned to expose, and this run prints no such figure.

**Both verbs, per question, from inside the rung directory:**

```
fux ask    "<question>" --json --band --top 10
fux answer "<question>" --json
```

**249 questions × 2 verbs × 8 rungs = 3 984 calls.**

## 4 · `[bm25f] b` — the value, and a fork this run had to take

🔴 **This run ranks at `b = 0.15`**, the value
[W-144](../../../archive/open/W-144-structure-aware-extraction.md) measured and
shipped as the engine default on 2026-09-16
([SR-RANKING](../../../records/0111_ranking.md) decision 3). It is the first
ranking default in that record that is measured rather than inherited, and it is
what HEAD ships.

⚠ **The eight rung directories did not carry it, and the run had to change
them.** Each rung's `.fux/tune.toml` was written by `fux setup` on **2026-09-12**
and has held `b = 0.75` ever since — unmodified since `Sep 15 23:07`, at one
commit (`630fd3b fux: index configuration`) in each rung's own git history. That
is **exactly the upgrade trap W-144's CHANGELOG entry names**: `fux setup` writes
`b` out in full, so a repository set up before the ruling keeps `0.75` and does
not move.

**So this run sets `b = 0.15` in all eight rung `.fux/tune.toml` files before any
call, and that edit is a named step of the run rather than a silent fix.** The
reasoning, stated before the numbers exist:

- `b` is applied at **query time**, so the change needs no re-ingest and cannot
  reach the committed index.
- Phase A's stated goal is *"outputs per rung, **at HEAD**"*. Ranking at `0.75`
  would measure a ranker nobody ships and nobody ruled.
- W-204 phase B says *"the `[bm25f] b` default differs between arms; that **is**
  the arm"* — which only holds if each arm runs at **its own** default. HEAD's
  default is `0.15`.
- `--no-tune` was rejected: it discards every other tuned key as well, and it is
  not what [prompt 5](../../golden/prompts/5-claude-run.md) runs.

🔴 **A defect in a filed run is declared here, not resolved here.** The
[2026-09-16 `rung-00100` run](../2026-09-16-golden-rung-00100/report.md) states
in both its frozen pre-registration and its report that it ranked at `b = 0.15`.
The rung's `.fux/tune.toml` held `0.75` before that run and holds it now, with no
modification in between, and prompt 5's command line carries no `--no-tune` —
so that run **most likely ranked at `0.75` under a report that says `0.15`.**
This run does not edit that filed report (a filed measurement is frozen); the
finding goes to this run's `ANALYSIS.md` and to Arpit. It is stated **before**
this run's numbers exist so that it cannot later read as a convenience.

⚠ **Either way, no number here may be compared with any golden number filed
before today** — the index format, the engine and the ranker have all moved.

## 5 · `[sources.url] meta` — the second forced repair

🔴 **Every rung's `fux.toml` carries `meta = "hashed"`, and HEAD refuses to load
it by name.** W-194 deleted the key on 2026-09-20 with no deprecation window;
`fux doctor` in `rung-seed` at the frozen sha returns

```
[FAIL] fux.toml loads: [sources.url] meta is not a fux.toml key
```

**No rung can be read at HEAD until the line is gone**, so this run deletes it
from all eight. Two facts that bound the change: `fux.toml` is **untracked** in
each rung's git repository, and the key governed **URL** record display, while
every rung is a directory corpus with no URLs. Nothing in `seed/` or `ext/`
moves, and §6's manifest check is re-run afterwards to prove it.

## 6 · Corpus verification — done before this document was frozen

- 🔴 **`ladder_check.py`, all four checks including check 4 (`seed_drift`), on
  all eight rungs: PASS.** Manifests consistent, nesting verified across all
  eight, every manifest path inside `seed/` or `ext/`, **`seed_drift` NONE** on
  every rung.
- 🔴 **Every document on disk hashed against its committed `.sha256`:
  18 820 documents, 0 mismatched, 0 missing**, across all eight rungs.

**A drift stops the run.** Neither check found one.

## 7 · The re-ingest, and why it is not optional

🔴 **Every rung is re-ingested at HEAD, once, with `--no-fetch`.** The committed
stamps read `engine: fux 2.0.1` / `engine_commit: bed465f3` and the shards on
disk are `fux.index.v3`; HEAD writes **v4**, so no committed rung index is
readable by the frozen engine. This satisfies prompt 5 step 2's *"unless the
engine version **and** engine_commit differ"* clause in its strongest form —
both differ, and the format differs too.

`--no-fetch` is required, not preferred: it is what keeps the pass offline
([L4](../../../records/0006_LAW-4-offline-default.md)) and deterministic, and no
rung has a URL to fetch.

**`work/golden/ladder/rung-NNNNN.index` is updated with the new `engine`,
`engine_commit` and `index_root_sha256`** in the same change, and the re-ingest
is filed as a numbered step of this run. ⚠ **`index_root_sha256` will move on
every rung**, which is the expected consequence of a format bump and not a
finding.

## 8 · What this run may claim — the surface claims, per set

🔴 **These are the only claims this run is permitted to make**, and each is
reported **per set** and **per rung**, never pooled:

| # | surface claim | how it is computed |
|---|---|---|
| S1 | **decline rate** — how many questions `fux answer` declined | the `answerable` / decline field of the answer JSON |
| S2 | **band distribution** — how the confidence band falls | the `band` field of `fux ask --band` |
| S3 | **empty ranked lists** — how many questions `fux ask` returned nothing for | `len(ranked) == 0` |
| S4 | **latency tail** — the slowest calls, per verb | wall-clock per call, reported as a tail, never as a benchmark |

⚠ **S4 is descriptive and is NOT a benchmark measurement.** This machine is
shared ([SR-WORK-SESSION](../../../records/0060_WORK-session.md) decision 12),
the arms are not interleaved because **there are no arms**, and no latency claim
here may be cited against
[SR-WORK-BENCHMARK](../../../records/0053_WORK-benchmark.md)'s captures.

🔴 **What this run may NOT claim, exhaustively:** whether an answer is right or
wrong; `hit@k`, `recall@k`, `precision` or any keyed metric; a difficulty band;
a comparison against any earlier golden run; a comparison between the two sets
beyond reporting each separately; and any statement about a version other than
the frozen HEAD.

**Headroom ([SR-RS](../../../records/0133_predictions.md) decision 22) does not
apply and is not omitted by oversight.** Decision 22 governs a **paired** run —
two arms, an endpoint, a direction. This run has one arm, no endpoint and no
comparison, so there is no direction to disclose headroom in. **W-204 phase B is
the paired run**, and its own pre-registration carries the disclosure.

## 9 · What is recorded, per set, never merged

| file | one line or section per question |
|---|---|
| `evidence/<rung>/predictions-set-N.jsonl` | `{id, ranked[], answerable, band}` |
| `evidence/<rung>/handoff-set-N.jsonl` | the above **plus** `question`, `answer_text`, `citations[{doc,lines}]`, `rung`, `engine_commit` — self-contained, and **what Arpit gives a scorer** |
| `evidence/<rung>/RUNG-NNNNN.md` | the human-readable twin: a header with engine commit, rung and index version; **set 1 in full, then set 2, never interleaved**; per question the id, the question text, the top-10 `ask` locators with band and `answerable`, the answer text or the decline, the cited locators and the freshness verdict |

🔴 **The `.md` is generated by `tools/quality-controls/rung_outputs.py` from the
two hand-offs, never written by hand**, so the eight documents cannot disagree
with the rows phase D will score. The generator is unit-tested before it is
used.

⚠ **One ambiguous id scores the wrong set.** The two hand-offs stay in separate
files at every step, and the generator refuses a set whose ids collide with the
other's.

## 10 · Classification, and what is read

**`classification: informed`**, for the reason the 2026-09-16 `rung-00100` run
gave and one more:

- **Set 2 can never be blind** — its author and its runner are the same model
  family, permanently ([SR-WORK-GOLDEN](../../../records/0066_WORK-golden.md)).
- **Set 1 is no longer blind either**, since the 2026-09-17 L11 breach recorded
  in [W-196](../../../archive/open/W-196-l11-breach-2026-09-17.md) — a Cowork
  Claude session was pasted both keys.
- **This pass feeds a scored run** (phase D), which is on its own sufficient.

**What this run reads:** `work/golden/seed/`, `work/golden/questions/set-1.jsonl`
and `set-2.jsonl` (ids and text only), `work/golden/ladder/`,
`work/golden/README.md`, `work/golden/prompts/`, and the eight rung directories
under `~/my_programs/fux-lab/corpora/golden/`. **Nothing else, and nothing at
either spelling of the sealed-key directory L11 decision 5 closes.**

## 11 · The reproduce command

```bash
cd ~/my_programs/fux-lab/corpora/golden/<RUNG>
/Users/arpitarya/my_programs/fux/.venv/bin/fux ask    "<question>" --json --band --top 10
/Users/arpitarya/my_programs/fux/.venv/bin/fux answer "<question>" --json
```

with the engine at `538f3497`, `b = 0.15`, the rung re-ingested once at `--no-fetch`.
**A run whose numbers cannot be regenerated is an anecdote.**
