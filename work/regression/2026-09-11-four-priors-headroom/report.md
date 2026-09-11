---
type: Run Report
run: 2026-09-11-four-priors-headroom
classification: informed
date: 2026-09-11
---

# Three of the four ranking priors have ZERO headroom on the hand-graded corpus — the remeasure cannot run there

🔴 **THIS IS NOT THE REMEASURE ARPIT ORDERED. It is the precondition check that
had to come first, and it FAILED.** No threshold is proposed, no verdict is
filed, and nothing here rules on any default.

**The finding in one line:** on the repaired `fux-playground`, `superseded_weight`,
`archived_weight` and `recency_half_life_days` produce **byte-identical results at
every value tested, including the extremes** — because the corpus declares none of
the facts they act on. **The only prior that moves is `rerank_weight`, which Arpit
explicitly HELD on 2026-09-11.**

| prior | values tested | goldens that changed | headroom |
|---|---|---:|---|
| `superseded_weight` | 1.0 · 0.5 · 0.1 · **0.0** | **0 of 50** | 🔴 **0** |
| `archived_weight` | 1.0 · 0.5 · **0.0** | **0 of 50** | 🔴 **0** |
| `recency_half_life_days` | 0.0 · 30 · 365 | **0 of 50** | 🔴 **0** |
| `rerank_weight` | 0.0 · 0.5 · 1.0 | **1** at 0.5, **4** at 1.0 | ✅ 13 improvement / 37 regression |

**`0.0` is the sharpest column.** `superseded_weight = 0.0` multiplies a
superseded document's score by zero — it would push such a document below every
other result in the corpus. **Nothing moved.** That is not a weak effect; it is
the absence of any document for the prior to act on.

## Why: the corpus never declares what three of the priors read

- **`superseded_weight` reads a `supersedes:` FRONTMATTER key**, resolved by
  `ingest/priors.py::superseded_ids` — *declared, never inferred*
  ([ADR-INGEST](../../../docs/adr/0016_ingest.md)).
  `docs/adr-0019-calder-gateway.md` says **in prose** *"Supersedes
  [ADR-0007](adr-0007-helix-mesh.md)"* and carries `title`, `tags` and `status`
  in its frontmatter — **and no `supersedes:` key**. `adr-0007` carries
  `status: superseded`, which nothing reads for this prior.
  🔴 **`git log -S "supersedes:" -- docs/` in `fux-playground` returns nothing:
  the corpus has NEVER carried the declaration**, on any branch, in its whole
  history.
- **`archived_weight` reads `archived=true` on a `.fux/sources/dirs` line.** The
  playground's list is one line, `docs`, with no attribute — **0 documents
  declared archived**.
- **`recency_half_life_days` reads the committed `mtime`.** All ten documents
  carry one, so the input exists — but the decay is normalised so the newest
  document is `1.0`, and ten files written in one commit are not spread far
  enough apart in `mtime` for any half-life to reorder them. **Input present,
  variance absent.**

`fux doctor` had already said the first two, and this run turns its count into a
measurement:

```
[WARN] ranking priors: BUILT, WIRED AND SWITCHED OFF at these values:
       archived_weight=1 (0 document(s) declared archived=true);
       superseded_weight=1 (0 document(s) superseded by another document);
       rerank_weight=0; recency_half_life_days=0 (10 document(s) carrying an mtime)
```

## What this means for the item Arpit ruled on

**His ruling, 2026-09-11:** *REMEASURE, then decide* — and the pre-registered
question was **not** *"which value?"* but ***"does ANY single global
`superseded_weight` value clear a `0 broken` bar?"***

🔴 **That question cannot be asked on this corpus.** Every value clears `0 broken`
**vacuously**, because every value breaks nothing and fixes nothing. A run
reporting *"`0 broken` at every value — the bar is met"* would be true, worthless,
and extremely misleading.

⚠ **This is exactly the failure [ADR-RS](../../../docs/adr/0043_predictions.md)
decision 22d was ratified to prevent, arriving three hours after it landed.** It
is the `heading` control's shape — *returned its predicted null at 100 % in both
arms with zero headroom, so it returned the right answer for the wrong reason*.
Without the headroom rule this run would have been filed as a clean pass.

**The item's own premise does not hold.** It says the hand-graded playground is
*"the only corpus with queries whose correct answer IS the retired document"*.
**The queries are; the corpus is not.** `q022` and `q033` — named in advance as
the queries `superseded_weight = 0.5` broke on 2026-08-25 — are still in the
goldens and both still pass, because the knob reaches neither.

⚠ **The 2026-08-25 run measured a corpus this one cannot reproduce.** That run
found `0.5` fixed `q015`/`q049` and broke `q022`/`q033`; the 2026-08-24 run
recorded `q015` recovering *"via a committed `supersedes:` declaration"*. **No
such declaration exists in this repository's history.** Those runs stand as
measured — nothing supersedes a measurement except a better measurement — but
**their corpus is not the corpus that exists today**, and no run on today's
playground can reproduce, confirm or contradict them.

## `rerank_weight` — the one that moves, and it stays held

| value | fixed | broken | net | discordant |
|---|---:|---:|---:|---:|
| 0.5 | 1 (`q013`) | **0** | **1** | 1 |
| 1.0 | 4 (`q013`, `q015`, `q020`, `q026`) | **0** | **4** | 4 |

**Headroom: 13 improvement, 37 regression, both PROVEN** — the feature-off arm
(`rerank_weight = 0.0`) is exactly the off/on control decision 22c requires, and
it demonstrably moves these queries.

🔴 **Net 4 is below the resolution floor and is "no detected change".** Decision
19: nets of 1, 2, 3, 4 and 5 **cannot clear α = 0.05 at any discordant count**;
four flips all one way gives `p = 0.125`. **So this run does not support raising
the default**, and it agrees exactly with the evidential position the queue row
already recorded (*"`+4` hand-graded, `informed`, below the resolution floor"*).

✅ **What it adds is that the `+4` is now reproducible on a committed index with
per-query rows filed**, which the earlier hand-graded figure was not. ⚠ **It
remains `informed`** and it is **not** an argument for the default. Arpit's hold
stands, and this run gives no reason to lift it.

## Authorship — classification `informed`

| artifact | author | could reach |
|---|---|---|
| the 10 documents | a fresh session, 2026-08-20 rebuild | — |
| the 50 goldens | human authorship, predating the rebuild; 7 resolved by a third blind annotator 2026-09-11 | — |
| the sweep, this report | Claude Code (Opus), 2026-09-11 | **everything**: the goldens, every prior score, the 2026-08-25 run |

⚠ **`informed`, so no delta here may be compared with a blind arm**, and the
`rerank_weight` numbers are **not a generalisation estimate**. The zero-headroom
finding is not a delta at all — it is a property of the corpus, checkable by
anyone with `grep`.

## What this run may never be used to say

- That `superseded_weight` is safe at any value. **It was not tested** — there
  was nothing to test it on.
- That the four-priors remeasure is done. **It has not started.**
- That `rerank_weight` should ship at `1.0`. Net 4 cannot clear α.
- That the 2026-08-25 result was wrong. It measured a different corpus.

## 🔴 Handed back to Arpit — the remeasure needs a decision before it can run

The instrument does not exist. **Three ways to get one, and choosing is his:**

1. **Declare the supersession the corpus already states in prose** — add
   `supersedes: [adr-0007-helix-mesh.md]` to `adr-0019`'s frontmatter. One line,
   and it makes the corpus say in metadata what it says in text. ⚠ **It changes
   the committed index and therefore every golden number filed against it**, so
   it is a corpus revision, not a fix, and it must be a deliberate act.
2. **Build the instrument elsewhere** — a purpose-made corpus with declared
   supersession and a query set split by intent (*current-seeking* vs
   *history-seeking*), which the item already says the pre-registration must
   declare. More work, and it does not disturb a hand-graded corpus.
3. **Close the knob on this evidence.** The item's own text says *"a run
   answering NO is a success and is the likelier answer"*. This run does not
   answer NO — it answers *cannot ask* — but the argument behind the expected NO
   is untouched and is structural: **supersession belongs to the query's intent,
   not to the document**, and a per-document multiplier cannot express that. That
   argument needs no corpus.

## Evidence

- [`evidence/per-query.jsonl`](evidence/per-query.jsonl) — **650 rows**, one per
  golden per arm, 13 arms across 4 priors. Sorted, keys sorted, no clock:
  byte-stable across runs, which is how the identical-result finding is checkable
  rather than asserted.

## Environment

| | |
|---|---|
| engine | `fux-engine` 2.0.0-alpha.7, fux `107b5d6` |
| corpus | `fux-playground` `fece5a3`, `docs/` only — 10 documents, sha256 of sorted file digests `871c492f…` |
| where | `~/my_programs/fux-lab/2026-09-11-four-priors-headroom` — a **copy**; `fux-playground` was not touched |
| python | 3.14.3 · **os** Darwin arm64 |

## Reproduce

```bash
# the corpus declares no supersession — the whole finding, in one command
cd ~/my_programs/fux-playground
git log --all -S "supersedes:" --oneline -- docs/     # empty, on every branch
head -5 docs/adr-0019-calder-gateway.md                # prose says it; frontmatter does not

# and the sweep that turns that into a measurement
LAB=~/my_programs/fux-lab/2026-09-11-four-priors-headroom
git archive --format=tar fece5a3 -o /tmp/pg.tar && mkdir -p "$LAB" && tar -xf /tmp/pg.tar -C "$LAB"
cd "$LAB"
for v in 1.0 0.5 0.1 0.0; do
  sed -i '' "s/^superseded_weight.*/superseded_weight       = $v/" .fux/tune.toml
  /Users/arpitarya/my_programs/fux/.venv/bin/python check.py --rows "/tmp/sw-$v.jsonl" >/dev/null
  echo "$v -> $(md5 -q /tmp/sw-$v.jsonl)"       # four identical digests
done
```
