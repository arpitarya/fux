---
type: OpenItem
id: W-143
title: "W-143 — the four no-op ranking priors: remeasure on golden data, then Arpit decides"
description: "archived_weight, superseded_weight, rerank_weight and recency_half_life_days are built, wired and multiply by one. Arpit ruled remeasure, then (b): build the instrument into the golden test data. Question: does ANY single global value clear 0 broken?"
status: open
lane: agent
timestamp: 2026-08-28T00:00:00Z
---

# W-143 — the four no-op ranking priors

**Model: Opus** — it writes a pre-registration and calls a gate.

- **Filed 2026-08-28** as an OPEN-WORK row with no file and no id; given both on 2026-09-11.
- **Lane:** `agent` once W-136's ladder is frozen, then back to Arpit with the result.
- **Blocked on:** [W-136](W-136-golden-benchmark.md) phase 1b and phase 2.

## From OPEN-WORK (moved 2026-09-11)

*Moved here verbatim when OPEN-WORK became one-to-two-line rows (Arpit, 2026-09-11). Links are rewritten for this directory.*

*This is what the queue said at the move. Re-derive it before believing it (OPEN-WORK rule 4).*

- 🟠 **THE FOUR NO-OP RANKING PRIORS — one problem, one blocker.** `agent`, then `arpit` ·
  *(records: [ADR-CONFIDENCE](../../docs/adr/0142_confidence.md) ·
  [ADR-TUNE](../../docs/adr/0135_tuning.md) ·
  [ADR-ARCHIVED-CONTENT](../../docs/adr/0134_archived-content.md) ·
  [ADR-RS](../../docs/adr/0133_predictions.md))* · `filed: 2026-08-28` ·
  `ruled: 2026-09-11`

  | knob | ships at | what it would act on |
  |---|---|---|
  | `archived_weight` | `1.0` | a source line declaring `archived=true` |
  | `superseded_weight` | `1.0` | a document another declares `supersedes:` |
  | `rerank_weight` | `0.0` | passage proximity, and since W-108 the refer plane's rescore too |
  | `recency_half_life_days` | `0.0` | a committed `mtime` |

  **Each is built, wired, reads its input, and multiplies by one.** So on
  ranking priors, `HEAD` **is** `1.0.0` — which explains the shipped-default
  nulls better than a saturated corpus did.

  🟠 **Arpit ruled 2026-09-11: REMEASURE, then decide** — not ship, not close.
  **Lane: `agent` for the remeasure, then back to Arpit with the result.**

  🔴 **The remeasure's question is NOT *"which value?"***. `P-SUPERSEDE` did not
  fail because `0.5` was wrong: at `0.5` it fixed `q015`/`q049` and **broke
  `q022`/`q033`**, and *every* broken query had the **superseded document as its
  correct answer**. Supersession belongs to the **query's intent**, not to the
  document — *"what do we do now?"* and *"what did we do before?"* want opposite
  rankings from one corpus, and a per-document multiplier cannot express that.
  **So the pre-registered question is: does ANY single global value clear a
  `0 broken` bar?** ⚠ **A run answering NO is a success** and is the likelier
  answer — it would close the knob permanently and move the work query-side. A
  run designed only to find a good value cannot report that.

  🔴 **THE REMEASURE CANNOT RUN, AND THAT IS MEASURED — 2026-09-11.** The
  precondition check ran before it
  ([the run](../regression/2026-09-11-four-priors-headroom/report.md)) and found
  **three of the four priors move 0 of 50 goldens at every value including
  `0.0`**: `superseded_weight`, `archived_weight` and `recency_half_life_days`
  all have **zero headroom on the hand-graded corpus.** `adr-0019` says
  *"Supersedes ADR-0007"* in **prose** and declares no `supersedes:` key —
  `git log -S "supersedes:"` is empty on **every branch of the playground's whole
  history**. So the pre-registered question is met **vacuously** at every value.
  ⚠ Caught by ADR-RS decision 22d hours after it was ratified; without it this
  files as a clean pass. ⚠ **The 2026-08-25 run's corpus is not recoverable** —
  it stands as measured and can be neither reproduced nor contradicted.
  ✅ `rerank_weight` is the one prior with headroom; net `+4` at `1.0`, 0 broken,
  **below the floor**, so the hold stands unchanged.

  🟢 **Arpit ruled (b), 2026-09-11 — build the instrument into the test data.**
  *"Set up the test data… so that at least we can test it."* The playground route is
  void under [L9](../../docs/adr/0011_LAW-9-environments.md); closing the knob (c) was not
  chosen. **[Prompt 1](../golden/prompts/1-codex-seed.md) part A §3** (it absorbed prompt 1b on 2026-09-12) has Codex add ≥ 4
  superseding pairs (`supersedes:` in frontmatter), ≥ 4 documents under `seed/archive/`,
  a date per seed, and ≥ 22 intent-split questions; phase 2 declares the archived
  directories, commits each file at its date and checks the coverage counts. The standing
  rule behind it is [ADR-RS](../../docs/adr/0133_predictions.md) **decision 23**.
  **Lane: `agent` once W-136's ladder is frozen, then back to Arpit with the result.**

  **What the remeasure still needs:**

  - **A frozen pre-registration** naming its `k`, its arms and the `0 broken`
    bar *before* the first number ([ADR-QUALITY](../../docs/adr/0141_quality-contract.md)
    decision 2a). ⚠ W-110's gate was VOIDED for exactly the omission this would
    repeat.
  - **The query set split by intent** — *current-seeking* against
    *history-seeking* — declared in the pre-registration. A set holding only the
    first kind will clear any bar and prove nothing.
  - ⚠ **Not runnable from Cowork**: that bridge is Linux/py3.10/no-egress and
    the `.venv` is macOS-built (verified 2026-09-11).

  ⚠ **`rerank_weight = 1.0` was asked for on 2026-09-11 and is HELD**, on a
  premise that does not hold — it was wanted *as a way to make the reranker
  depend on `archived=true`*, and the reranker is **proximity only**, with no
  concept of retirement. The flag already reaches ranking through
  `archived_weight`; wiring it into the reranker too would state one rule in two
  places (L0). On its own merits the knob has `+4` hand-graded, `informed`,
  **below the resolution floor** — the same evidential position as
  `superseded_weight`, so shipping one on argument while holding the other on
  measurement would not be a defensible pair. ⚠ **Its `22 % → 100 %, 94 fixed,
  0 broken`** ([C2](../regression/2026-08-28-benchmark-contested/VERDICT-C2.md))
  is **not** an argument for the default and the pre-registration said so before
  the number existed: that suite rewards exactly what the reranker does, and
  `c = 0` is a property of the generator, not a safety result.

## 2026-09-12 — the corpus this was blocked for now exists

The open blocker names three options for the four no-op priors and calls (b)
*build a purpose-made corpus*. **It is built and frozen**
([`work/golden/ladder/`](../golden/ladder/)):

- **`superseded_weight`** — 4 declared seed pairs and 98 declared `ext/` pairs;
  the built index carries `superseded` on 102 records at rung 1 000. The
  2026-09-12 run counts **145 co-ranked pairs at `rung-seed`, 74 of them
  inverted** — real, countable headroom, where the playground had none.
- **`archived_weight`** — 5 `seed/archive/` + 98 `ext/archive/` documents, and
  `archived=true` is **declared** in every rung's `sources/dirs`.
- **`recency_half_life_days`** — every document committed at its own date;
  **1 000 of 1 000 carry an `mtime`**, against ten files from one commit before.

🔴 **The inversion count is a KEY-FREE endpoint**, so a sweep against it is not
contaminated by [W-145](W-145-codex-regenerates-the-key.md) and does not wait on
it. ⚠ It needs its own pre-registration, and it must name its endpoint — the
document plane and the passage plane disagree
([analysis](../regression/2026-09-12-golden-ladder/ANALYSIS.md) §2).

⚠ **This does not answer Arpit's question**; it removes *"cannot run"* as the
reason it is unanswered.

## ✅ ANSWERED 2026-09-12 — and the answer is **NO**

**[VERDICT-W143](../regression/2026-09-12-priors-and-tables/VERDICT-W143.md).** Arpit's pre-registered question —
*does ANY single global value clear a `0 broken` bar?* — has run on the corpus
he ruled should be built for it, and returns the answer this file predicted was
likelier.

- **26 intent-split probes**, 13 current-seeking / 13 history-seeking, truth read
  off the `supersedes:` and `archived=true` **declarations** — so **no answer key
  is involved** and this does not wait on [W-145](W-145-codex-regenerates-the-key.md).
- **Every value that perfects current-seeking (13/13) dismantles history-seeking**,
  one probe for one. `recency_half_life_days` at a year or less takes it to **0/13**.
- **Three candidates appeared to clear and none survives**: each clears on one
  rung and breaks on another, on a different probe, and each has a net of +1 or
  +2 against decision 19's floor of 6.
- **Both directions have headroom**, so this is a measured negative and not
  decision 22d's Inconclusive — which is exactly what the 2026-09-11 precondition
  check could not say.

🔴 **The lane is now `arpit`.** This file's own framing was *"agent for the
remeasure, then back to Arpit with the result"*. The result is back. The three
options are unchanged and all three are his:

1. **Close the knobs** — option (c), now with evidence rather than an argument.
2. **Move the mechanism query-side** — a query carries its intent; a document
   does not. ⚠ **No record has opened this and a session must not open it by
   implementing it.**
3. **Leave them at their no-op defaults**, and stop describing them as tunable
   quality levers.

⚠ **What this does NOT do:** change a default, close a knob, or authorise a
query-side design. [ADR-TUNE](../../docs/adr/0135_tuning.md) decision 13 carries
the result; the amendment is his.
