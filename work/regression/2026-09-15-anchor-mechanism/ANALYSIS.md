---
type: Analysis
run: 2026-09-15-anchor-mechanism
item: W-168
description: "The diagnosis: the golden ladder was grown from a seed corpus containing no hyperlinks, so every link-dependent feature on the queue is unmeasurable on it — the anchor field (W-168 step 8), BOTH of W-161's arms (ask_kinds is `ref` and there are no `ref` edges), and W-176's graph-coherence gate. The queue calls these 'waiting on Codex's questions'; they are waiting on link-bearing DOCUMENTS, and no question can substitute. Whether to add links to the frozen ladder or build a sibling corpus is Arpit's, and is not taken here."
filed: 2026-09-15
---

# ANALYSIS — three items are waiting on the wrong thing

## The diagnosis, in one sentence

**The golden corpus contains no hyperlinks at all**, so the ladder carries
`supersedes` edges and nothing else — and *every* queued feature that reads a
link edge is inert on it, regardless of what questions anyone writes.

## What follows from `0 ref edges`, by arithmetic and not by inference

| feature | reads | on the ladder |
|---|---|---|
| **W-168 step 8** — the `[bm25f] anchor` field | `at`/`al` on any edge | **0 of 1 002 edges carry them** → inert at every weight, measured 0/124 on three rungs |
| **W-161 arm A** — Tier A's RRF boost | the `ask` walk, `[graph] ask_kinds` | 🔴 **defaults to `ref` alone, and there are no `ref` edges** → the walk returns the seed and nothing else |
| **W-161 arm B** — Tier B `related` | the same walk | 🔴 **always empty** → "the answer document appears in `related`" cannot be true for any question |
| **W-176 step 10** — the graph-coherence gate | the same walk | would return `unknown` for **every** question, which is the degradation it is specified to have on a link-poor corpus — the ladder is link-**free** |

Confirmed at the CLI, not only in the index:

```bash
cd ~/my_programs/fux-lab/corpora/golden/rung-01000
.../fux/.venv/bin/python -m fux graph --seed seed/01-sop-temperature-excursion.md
#     #1  seed     seed/01-sop-temperature-excursion.md      <- and nothing else
```

That seed document **is** superseded, so even the supersession edges are not
reached: the `ask` walk is narrowed to `ref` by
[`tune.py`](../../../src/fux/tune.py) `ask_kinds: str = "ref"`.

## 🔴 The correction this forces on the queue

[`work/OPEN-WORK.md`](../../OPEN-WORK.md) and
[W-168](../../open/W-168-search-improvements.md) row 8 say these items are
waiting on **Codex's golden questions**. That is not what they are waiting on.

> **A question cannot create the edge the feature reads.** A link-dependent
> question over a corpus with no links is a question with no answer, and
> SR-RS decision 23a's own words are that *the test data must contain the input
> the feature acts on* — the **input**, which here is a document that links to
> another using words the target does not use.

So the Codex task on 2026-09-30 is **corpus authorship, then questions** — and
the queue currently asks for half of it. W-168 row 8's stated reason is wrong in
a second way as well: it reads *"no Claude session opens the sealed key"*, which
is true and is **not** why row 8 is blocked — the blocker is authorship of
linked documents, not key access.

## Specific changes

| # | change | where | repro / check |
|---|---|---|---|
| 1 | row 8's obligation becomes **documents first, then questions**, and its reason stops citing key access | [`W-168`](../../open/W-168-search-improvements.md) §gating table | — |
| 2 | W-161's *"waits on link-dependent questions"* becomes *"waits on `ref` edges in the corpus, then questions"* | [`W-161`](../../open/W-161-graph-composed-ask.md) | `fux graph --seed` above |
| 3 | W-176 step 10 records that its `unknown` degradation is **currently the only reachable outcome** | [`W-176`](../../open/W-176-abstention-gates.md) | — |
| 4 | both frozen pre-registrations gain a pointer to this run under *What the data must contain* — **no threshold moves** | [`anchor-text`](../2026-09-15-anchor-text/PRE-REGISTRATION.md), [`graph-ask`](../2026-09-14-graph-ask/PRE-REGISTRATION.md) | SR-RS d10b: a pointer is not a threshold |
| 5 | the Codex prompt gains the corpus obligation | [`work/golden/prompts/`](../../golden/prompts/) | — |

## 🔴 Unresolved, and it is Arpit's — not taken here

**Adding `ref` edges to the golden corpus changes the corpus**, and every number
already filed against the ladder was measured on the link-free one. Two routes,
with different costs:

| route | what it costs |
|---|---|
| **(a)** extend the existing seed documents with links | the ladder's documents change → `rung-*.sha256` manifests are rewritten, and comparability with every filed ladder number is broken |
| **(b)** add new link-bearing documents, leaving the existing ones untouched | the ladder grows; nesting and the document manifests still change, but no existing document moves |
| **(c)** a sibling corpus for link-dependent features only | the ladder is frozen, but a link feature is then never measured at 10 000 documents alongside everything else |

**This is not an agent's call.** It decides whether months of filed ladder
numbers stay comparable, and [SR-RS](../../../records/0133_predictions.md)
decision 10b's spirit — a recorded negative that stops building is a success —
cuts toward stating it rather than quietly picking (b).

⚠ **A concurrent session was extending `work/golden/seed/` while this ran** —
131 lines added across 7 documents, staged and uncommitted. **Zero of those
lines contain link syntax**, checked, so this run's finding is not stale; but it
shows the corpus is being grown *without* the structure these three items need,
which is the failure mode this analysis exists to stop repeating.

## What this run does NOT do

1. **It rules no threshold.** No `VERDICT.md`, here or in either pre-registered
   directory. The anchor arms have still never run.
2. **It does not say the anchor field is worthless** — the positive control
   shows it works exactly as specified on a corpus that has link text.
3. **It does not touch the corpus.** Not one byte of `work/golden/` was written.
