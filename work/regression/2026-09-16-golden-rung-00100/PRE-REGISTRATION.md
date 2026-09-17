---
type: Pre-Registration
description: "Phase 5 of W-136 on rung-00100: run both question sets through `fux ask` and `fux answer`, write predictions and a self-contained hand-off Arpit gives Codex. NO scoring — this run cannot say whether an answer is right, and does not try."
run: 2026-09-16-golden-rung-00100
item: W-136
status: frozen
filed: 2026-09-16
---

# PRE-REGISTRATION — golden phase 5, `rung-00100`

🔴 **FROZEN, and committed before any number exists**
([SR-RS](../../../records/0133_predictions.md) decision 10b).

---

## 1 · What this run is, and what it explicitly is NOT

**It is a prediction run.** For every question in both sets it records **what fux
answered, what it ranked, and whether it declined** — and stops there.

🔴 **It files no score, no accuracy, and no verdict, because no Claude session
can.** There is **no answer key anywhere** and none reaches this session by any
route, a paste included
([L11](../../../records/0012_LAW-11-sealed-answer-key.md)). *Correct* and
*incorrect* appear for the first time in
[prompt 6](../../golden/prompts/6-codex-score.md)'s output, from **Codex**,
against a key **Arpit pastes there himself**.

⚠ **A report that guessed at correctness would train the next reader to trust a
guess**, which is why the prompt forbids it and this document repeats the
prohibition rather than assuming it.

## 2 · Engine, rung, and the one thing that changed today

| | |
|---|---|
| rung | **`rung-00100`** — 100 documents, the 20 seed documents plus 80 `ext/` |
| engine version | `fux 2.0.1`, matching the rung's stamp |
| engine commit | **differs from the stamp** (`e71f27c6` against `bed465f3`) |
| index | 🔴 **the rung's own, NOT re-ingested** |

**Why no re-ingest.** [Prompt 5](../../golden/prompts/5-claude-run.md) step 2
re-ingests only when the engine version **and** the commit differ. **The version
matches**, and nothing between those two commits touches the committed index
format: W-177 is the CLI surface, W-178 is the `.fux/sources/urls` grammar, and
W-144 is a **query-time** ranking default. Verified before the run: the shard
header reads `fux.index.v3` / `analyzer: v2` and the engine accepts it.

🔴 **`[bm25f] b` CHANGED TODAY, from `0.75` to `0.15`**
([W-144](../2026-09-16-b-sweep-2/VERDICT.md)). It needs no re-ingest — `b` is
applied at query time — **but it moves every score and every ranked order this
run produces.**

⚠ **So no number from this run may be compared with any golden number filed
before 2026-09-16.** They measure different rankers on the same corpus. Stated
here, before the run, so it cannot be discovered afterwards as a convenience.

## 3 · Corpus verification — done before this was frozen

- **All 100 documents hashed against [`rung-00100.sha256`](../../golden/ladder/rung-00100.sha256): 0 mismatches, 0 missing.**
- **`rungs.seed_drift('rung-00100')`: NONE** — the rung carries the seed corpus
  this repository actually has, which is the check
  [W-186's second strike](../2026-09-15-ladder-seed-refresh/report.md) put in
  place.

## 4 · What is recorded, per set, never merged

Two sets, **kept apart at every step** — one file each, never pooled:

| file | one line per question |
|---|---|
| `evidence/predictions-set-N.jsonl` | `{id, ranked[], answerable, band}` |
| `evidence/handoff-set-N.jsonl` | the above **plus** `question`, `answer_text`, `citations[{doc,lines}]`, `rung`, `engine_commit` — self-contained, and **what Arpit gives Codex** |

**Two `fux` calls per question**: `ask --json --band --top 10` and
`answer --json`. 249 questions → **498 calls**.

🔴 **Set 1 and set 2 are NEVER pooled into one figure.** The gap between them is
the measurement — set 1 is Codex-authored, set 2 is Claude-authored — and a mean
across both erases exactly what two authors were commissioned to expose.

⚠ **Every set 2 number carries `informed` permanently**, beside the number, every
time: its author and its runner are the same model family
([SR-WORK-GOLDEN](../../../records/0066_WORK-golden.md)).

## 5 · Headroom, and why it is not the usual disclosure

**This run has no arms.** One engine, one configuration, one pass — so
[SR-RS](../../../records/0133_predictions.md) decision 22b's paired headroom does
not apply, and stating a fabricated version of it would be worse than stating
none.

**What is disclosed instead**, per set:

- **how many questions fux DECLINED** (`answerable: false`) — the population no
  scoring can reward;
- **the band distribution** (`grounded` / `partial` / `weak` / `none`);
- **how many returned an empty ranked list** — a question the corpus cannot
  reach at all, which is a data fact rather than a ranking one;
- **the slowest and the emptiest results**, named.

🔴 **A decline is not a wrong answer and this run may not call it one.** Whether
declining was *correct* is a property of the key, which is Codex's.

## 6 · Classification

**Set 1: `blind` is not claimable by this run and this run claims nothing** — it
files no score. **Set 2: `informed` permanently.** The labels attach to the
**scores**, in prompt 6's output; this document records which label each set will
carry so prompt 6 cannot be the first place anyone thinks about it.

## 7 · What this run does NOT do

- **It does not score.** Not once, not approximately, not as a sanity check.
- **It does not re-ingest**, per §2.
- **It does not run another rung.** One rung, named in the report.
- **It does not touch `work/golden/questions/` beyond reading `id` and
  `question`**, which is what
  [SR-WORK-GOLDEN](../../../records/0066_WORK-golden.md) decision 2 permits.
- 🔴 **It does not create, open, list, hash or delete the directory L11 names.**
  That directory was deleted on 2026-09-15 and **is not a location**.
