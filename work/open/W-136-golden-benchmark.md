---
type: OpenItem
id: W-136
title: "W-136 — the sealed golden benchmark"
description: "Arpit, 2026-09-11: Codex writes 10 seed documents and ~100 questions with answers Claude never sees; Claude grows the corpus 10 → 10 000 blind; Claude runs fux per rung; Codex scores without revealing answers. The test data for fux-lab (SR-WORK-ENVIRONMENTS)."
status: open
lane: arpit
timestamp: 2026-09-11T00:00:00Z
---

## 🔴 2026-09-17 — the hand-offs WERE scored, by the wrong party, in an L11 breach

**A Cowork Claude session was pasted both keys and scored them in chat**, in
[prompt 6E](../golden/prompts/6E-codex-score-ephemeral.md)'s shape.
[L11](../../records/0012_LAW-11-sealed-answer-key.md) gives the paste route to
**Codex alone**; the instruction was void and the session complied.
**[W-196](../../archive/open/W-196-l11-breach-2026-09-17.md)** carries it, and it is Arpit's ruling.

| | |
|---|---|
| filed | [the run](../regression/2026-09-16-golden-rung-00100/ANALYSIS.md) — fenced, every number non-citable |
| set 1 | 🔴 **no longer blind** — `informed (L11 breach 2026-09-17)` |
| set 2 | `informed`, permanently, as before |
| **prompt 6** | 🔴 **STILL UNRUN.** 6E files no per-query rows, so **W-87, W-176, W-190, W-191 and W-195 stay blocked** |

⚠ **Phase 5 is therefore *both* done and not done**, and the distinction is the
one that matters: the engine's standing on `rung-00100` is known to Arpit, and
**no evidence exists that any document may cite.** The section below stands as
filed on 2026-09-16 and is not edited.

## ✅ PHASE 5 RAN on `rung-00100` (2026-09-16) — the hand-offs are ready for Arpit

[The run](../regression/2026-09-16-golden-rung-00100/report.md). 249 questions,
498 `fux` calls, both sets kept apart at every step.

🔴 **It files NO SCORE and none may be inferred from it.** *Correct* first
appears in [prompt 6](../golden/prompts/6-codex-score.md)'s output, from Codex,
against a key Arpit pastes there.

**What he gives Codex**, self-contained, one line per question:

- `work/regression/2026-09-16-golden-rung-00100/evidence/handoff-set-1.jsonl` — 125
- `work/regression/2026-09-16-golden-rung-00100/evidence/handoff-set-2.jsonl` — 124

| | set 1 (Codex) | set 2 (Claude, `informed`) |
|---|---:|---:|
| declined | **36 — 28.8 %** | **52 — 41.9 %** |
| `grounded` / `partial` / `weak` | 52 / 37 / 36 | 32 / 40 / **52** |
| empty ranked · uncited | 0 · 0 | 0 · 0 |

🔴 **Finding 1 — authorship is visible in the instrument.** Same corpus, same
engine, same day; **set 2 declines half again as often**. **It is not a claim
that either set is better** — nothing was scored, and whether those declines are
right is the key's property. **It is what two authors were commissioned to
expose.**

🔴 **Finding 2 — `weak` and `declined` coincide EXACTLY, 249 of 249.** Not
correlated, identical. SR-CONFIDENCE's gate as ruled on 2026-09-14, observed at
corpus scale — and it means the two columns above carry **one** number.

⚠ **`[bm25f] b` moved `0.75 → 0.15` hours before this ran**, so every ranked
order is the new ranker's and **nothing scored from these hand-offs may be
compared with a pre-2026-09-16 golden number.** `engine_commit` is on every row.

⚠ **No re-ingest**: the engine version matches the rung's stamp and only the
commit differs. Corpus verified first — **100/100 documents against the manifest,
`seed_drift` NONE**.

**Next: prompt 6 — Codex scores, in a chat Arpit attends.** No Claude session
takes part, and the other seven rungs are unrun.

## Two routes to a score (Arpit, 2026-09-17)

He asked for *"a prompt where nothing gets saved in the memory and which just
generated the score and nothing else"*, so there are now two, and **choosing
between them is choosing what the number may be used for**:

| | [prompt 6](../golden/prompts/6-codex-score.md) | [prompt 6E](../golden/prompts/6E-codex-score-ephemeral.md) |
|---|---|---|
| writes | per-query + sealed-aggregate CSVs under `work/regression/` | **nothing** |
| pools unjudged top-5 hits | yes | **no — every figure is a lower bound** |
| returns updated keys | yes, `key_version` advances | **no** |
| the number may be cited | yes | 🔴 **no — not in a record, a compare doc, a work item, or against another golden number** |
| unblocks W-87 / W-176 / W-190 / W-191 | yes | **no** — those need filed per-query rows |

⚠ **6E does not close this item.** It tells him where the engine stands; it
produces no evidence, so the five items behind W-136 stay blocked until prompt 6
runs. Running 6E first costs one extra key exposure and nothing else.

# W-136 — the sealed golden benchmark

**Model: NONE — no Claude model executes this.** Phase 5 is **Codex's**, run
on Arpit's account, and the whole point of the instrument is that no Claude
session sees the answers. Stated rather than left blank so
[SR-WORK-LIFECYCLE](../../records/0058_WORK-lifecycle.md) decision 6 has an
answer here: *what would execute this* is a real question with a real answer,
and the answer is not one of the three models.

**The process is [`work/golden/README.md`](../golden/README.md)** — stated there
once; this file carries only state. Prompts: [`work/golden/prompts/`](../golden/prompts/).

## 🟣 Gated on 2026-09-30 — Arpit, 2026-09-13

**His Codex limit is exhausted; he runs prompt 5 on 2026-09-30.** Everything an
agent can do is done. The decision is made, so this left the *Blocked on Arpit*
table and is a 🟣 date gate in [OPEN-WORK](../OPEN-WORK.md).

- **What this gate holds up**, moved here from the inbox sub-row: **[W-87](W-87-what-good-means.md)'s
  recall half** and **[W-144](../../archive/open/W-144-structure-aware-extraction.md)'s cheap route**,
  both of which read per-query scores off phase 5. **Not W-145** — that governed
  what a number may *claim*, not whether it runs, and it closed as overtaken on
  2026-09-15 when Codex authored set 1.

## State

| phase | who | lane | state |
|---|---|---|---|
| 1. Seed + question sets | Codex (set 1) and Claude (set 2) | — | ✅ **DONE for real 2026-09-15** — the 20 seed documents and `seed-dates.tsv` stand; the provisional Claude key was deleted and **Arpit ran prompt 2 and prompt 3**. [`questions/`](../golden/questions/README.md): set 1 is Codex's (125, `s1-001…s1-125`), set 2 is Claude's (124, `s2-001…s2-124`); **both questions-only, both keys Arpit's**. W-145 closed as overtaken |
| 2. Extend 10 → 10 000, blind | Claude Code (Opus) | `agent` | ✅ **COMPLETE 2026-09-12 — all eight rungs to 10 000.** The first five were committed *before* the questions were opened (`92f5bff`); `rung-02000`/`05000`/`10000` were built later the same day from the **same committed generator and seed**, so what protects them is determinism rather than the clock — stated in [`golden/README.md`](../golden/README.md) rather than glossed. Nesting verified across all eight. 🔴 **RE-FROZEN 2026-09-15** — prompt 4's check found all eight rungs holding a **superseded seed** and rebuilt them; see below. |
| 3. Freeze ladder, release questions | Codex | `arpit` — run prompt 3 | ⚠ **released early** on 2026-09-12, before the ladder existed — ids permuted so no band identifies the unanswerables. Phase 2 was on its honour and did not open `questions/`. |
| 4. Run each rung | Claude Code | `agent` | ✅ **run on 2026-09-12** for the five rungs that existed then, under a committed pre-registration ([`work/regression/2026-09-12-golden-ladder/`](../regression/2026-09-12-golden-ladder/PRE-REGISTRATION.md)). ⚠ **`rung-02000`/`05000`/`10000` have NOT been run** — they were built after that run. Running them is cheap (the indexes are committed) but it needs its own pre-registration, because a run across eight rungs is not the run that was registered across five. |
| 5. Score each set, per rung | Codex | `arpit` — run prompt 6 | 🟣 **gated on 2026-09-30** (Arpit, 2026-09-13 — Codex limit exhausted). ⚠ **The premise visibly changed on 2026-09-15**, when Codex authored set 1; **only Arpit lifts a date gate**, so it stands until he says otherwise. ✅ **Set 1 is no longer `informed` for key authorship** — W-145's defect is gone. 🔴 **Set 2 is `informed` permanently** (SR-LAW-11 decision 7). |

## 🔴 Prompt 4 ran 2026-09-15 — and the ladder was stale

**The check failed, which is why the prompt is a check.** All eight rungs had
been frozen on 2026-09-12; `0aa4bbcf` then extended **7 of the 20 documents in
`work/golden/seed/` by 131 lines** on 2026-09-15, and **both question sets were
authored after that**. Every rung still carried the old bytes, and nothing saw
it: `verify()` compares a rung to its own manifest and `ladder_check` compares
the manifests to each other — neither asks whether `seed/` is the seed the repo
has.

- **All eight rebuilt and re-frozen** from the current seed with the
  **unmodified** 2026-09-12 builder and generator.
- 🔴 **`ext/` byte-identical on all eight** — 18 800 generated documents,
  **0 drift**, re-derived three days later at a different engine commit. The
  determinism claim is measured now.
- **Every coverage count unchanged**; 14 manifest lines moved per rung; every
  rung answers at `fux.index.v3` with **0 seed files on any skip list**.
- **Two strikes → a gate** ([SR-WORK-SESSION](../../records/0060_WORK-session.md)
  decision 13; W-186 was strike one): `rungs.seed_drift()`, `ladder_check.py`
  check 4 and [`tests/test_golden_ladder_seed.py`](../../tests/test_golden_ladder_seed.py).
- **Blind** — `work/golden/seed/` and nothing else under `work/golden/` was read.
- Filed: [`2026-09-15-ladder-seed-refresh`](../regression/2026-09-15-ladder-seed-refresh/report.md).

⚠ **Every number filed against the old rungs names a corpus that is gone** —
caused by the seed moving, not by the rebuild. No pre-registration pins a rung
index root, so no threshold moved.

⚠ **A rung is a COPY of `seed/`.** Touching a seed document in this repo
invalidates all eight until they are rebuilt — the gate is what makes that loud
instead of silent.

## Done in the filing change (2026-09-11)

- `work/golden/` scaffold, the process README and five prompts. **No key file** —
  where the key lives is Arpit's call each run (below).
- Guards: `.gitignore`, `!work/golden` in `.fux/sources/dirs`, Claude Code
  `permissions.deny` + `.claude/hooks/guard-golden-answer.sh`, CLAUDE.md §Golden
  answer key.

## Phase 1 — closed provisionally on 2026-09-12

**Arpit's Codex quota was exhausted with phase 1 half done**: the ten seed
documents had landed, the questions and answers had not. He ruled that Claude
write the rest so phase 2 is not blocked, and that a work item be filed in the
same breath for Codex to regenerate the key — W-145 (closed 2026-09-15 — [W-136](W-136-golden-benchmark.md) phase 5),
which carries what is contaminated and what any number may claim.

- **Twenty documents in `work/golden/seed/`.** Codex's ten, plus five
  feature-coverage documents (`11`–`15`, four superseding pairs) and five archived
  documents under `seed/archive/`, written by Claude.
- **`seed-dates.tsv`** covers all twenty, superseders newer than what they retire,
  archived documents oldest.
- **The key is 124 questions, held in the chat only** — Arpit chose option (2), so
  **no key file exists on this machine**. **`questions/questions.jsonl` (ids + text
  only) IS on disk** from 2026-09-12, so a chat agent runs a rung without being
  handed the questions — which breaks the release ordering deliberately and puts
  phase 2 on its honour; [`../golden/questions/README.md`](../golden/questions/README.md).
  🔴 **Ids were permuted and renumbered** so no id band identifies the twelve
  `unanswerable` questions; the first key handed over on 2026-09-12 is superseded by
  the renumbered one. Type mix inside ±5 points on every class;
  `superseded_weight` 12 · `archived_weight` 9 · `recency` 7 questions.
- **Prompt 1b was merged into prompt 1** and deleted (Arpit, 2026-09-12), so the
  regeneration is one run, not two.
- ⚠ **Every run scored against this key is `informed`** and no delta measured
  against it may be stated. That is W-145's whole subject.

## The seed brief (2026-09-11)

- **Quillfern Cold Logistics** — a fictional Indian cold-chain company (reefer
  trucking + temperature-controlled DCs). Ten deliberately inconsistent documents:
  `.md` with and without frontmatter, legacy `.yaml`, `.txt` shift log, `.eml`
  thread, `.html` wiki export; big and small; professional and amateur; multi-editor.
- Claude wrote the company, cast and roster; **Codex invents every fact.**
  Spec: [`prompts/1-codex-seed.md`](../golden/prompts/1-codex-seed.md).

## Where the key lives (Arpit, 2026-09-11 — SUPERSEDED TWICE)

⚠ **History. Do not act on this section.** The live answer is
[L11](../../records/0012_LAW-11-sealed-answer-key.md) decision 3: a key may live
at **`work/golden/golden-answers/`**, on Arpit's machine, gitignored, and closed
to every agent on both spellings. The per-run *file-or-chat* question below was
deleted on **2026-09-15** and the directory was permitted again on **2026-09-18**
([W-198](../../archive/open/W-198-golden-answers-canonical.md)); neither change restored the
question, because the route to a scoring turn is the chat, always.

- **Never in the directory by default.** Codex asks in phases 1, 3 and 5: *(1) the
  file `golden-answer/answers.jsonl`, or (2) the chat?* — and waits. The placeholder
  file was removed.

## Feature coverage — prompt 1b (Arpit, 2026-09-11)

- Ruled (b) for the four ranking priors: Codex adds ≥ 4 superseding pairs, ≥ 4 archived documents, a date per seed and ≥ 22 intent-split questions ([prompt 1](../golden/prompts/1-codex-seed.md) part A §3, which absorbed prompt 1b on 2026-09-12); phase 2 declares, dates and checks coverage. Rule: SR-RS decision 23. The first rung is `rung-seed`.

## Decisions taken with defaults — Arpit may override

- **Questions stay inside the key until the ladder is frozen.** An extender that
  has seen them makes every rung `informed`.
- **Ladder stops at 10 000** — the 2026-08-22 ceiling.
- **Corpus lives in `~/my_programs/fux-lab/corpora/golden/`**; only manifests
  are committed here.
- **One directory and one index per rung** (Arpit, 2026-09-11) — `rung-00010` …
  `rung-10000`, real copies, each its own git repo with a committed `.fux/` index built
  once per engine version in phase 2, so phase 4 only asks.
- **20 % sealed holdout**, reported only in aggregate.
- **Key completeness by pooling**: Codex judges non-key top-5 results per rung.

## Open

- ⚠ **Relation to W-87 Part B (R-11).** This ladder is a candidate Part B corpus
  with a key Claude cannot contaminate. Not decided here.
- ⚠ **The key is gitignored** — Arpit backs it up; git will not.
- ⚠ **Cowork cannot be blocked mechanically** from the folder; CLAUDE.md is the guard.

## From OPEN-WORK (moved 2026-09-11)

*Moved here verbatim when OPEN-WORK became one-to-two-line rows (Arpit, 2026-09-11). Links are rewritten for this directory.*

*This is what the queue said at the move. Re-derive it before believing it (OPEN-WORK rule 4).*

- 🟠 **W-136 — the sealed golden benchmark.** `arpit` (Codex phases), then `agent` ·
  *(records: [SR-RS](../../records/0133_predictions.md) · [SR-WORK-QUALITY](../../records/0056_WORK-quality.md) ·
  setup: [fux-lab](../setup/fux-lab.md))* · **Arpit, 2026-09-11.**
  Codex writes 10 seed documents and ~100 questions with answers in
  `work/golden/golden-answer/` — **Claude never reads it**. Claude grows the corpus
  **10 → 10 000** without seeing a question; Codex freezes it and releases questions
  only; Claude runs fux per rung; Codex scores and returns per-query results with no
  answers. The test data for fux-lab ([SR-WORK-ENVIRONMENTS](../../records/0052_WORK-environments.md)). Process:
  [`golden/README.md`](../golden/README.md) — [detail](W-136-golden-benchmark.md)
  `filed: 2026-09-11`

## 2026-09-12 — phase 2 closed, and what that leaves

**The ladder is complete: eight rungs, 20 → 10 000 documents, all nesting
byte-for-byte, 10 000/10 000 records carrying an `mtime`, 1 003 declared archived
and 1 002 declared superseded at the top rung.**

**10 000 is the ceiling and there is no rung above it.** `CLAUDE.md` §Litmus and
[SR-WORK-ENVIRONMENTS](../../records/0052_WORK-environments.md); a rung at 50 000 is not
deferred, it is forbidden.

### What is left on this item

| phase | who | state |
|---|---|---|
| 3. Freeze + release | Codex | ⚠ released early on 2026-09-12; ids permuted |
| **5. Score each rung** | **Codex** | 🟢 **ready — and it is the only thing left** |

**Everything an agent can do on W-136 is done.** Phase 5 is Codex's by design:
it is the half Claude may never see, and that separation is the whole point of
the benchmark.

⚠ **Two things phase 5 should know before it runs:**

1. **Every number is `informed` until W-145 (closed 2026-09-15 — [W-136](W-136-golden-benchmark.md) phase 5)
   closes** — the key is the Claude-authored stopgap.
2. **Phase 4 covers five rungs, not eight.** The three new rungs are built and
   indexed but **not run**, and running them needs its own pre-registration —
   a run across eight rungs is not the run that was registered across five.

### What the new rungs unblock, and what they do not

- ✅ They are the corpus for any measurement that wants scale up to the ceiling.
- 🔴 **They do not make W-115 measurable.** [VERDICT-W115](../regression/2026-09-12-reaim-and-instruments/VERDICT-W115.md)
  measured it on a purpose-built corpus instead, and the reason the ladder could
  not is **content, not size**: 1 of 800 `.md`/`.txt` documents carries a `#`
  inside a code fence, and a bigger draw from the same generator has the same
  proportion.

## ✅ RULED 2026-09-18 (Arpit) — prompt 6 is DEFERRED; 6E is enough for now

Asked whether to run prompt 6 on the `rung-00100` hand-offs now, later paired
with W-176's after-run, or skip it: **"Skip prompt 6 — 6E is enough for now."**

**What this means for the queue, written so nobody re-derives it:**

- The hand-offs stay on disk, stamped with `engine_commit`. They do not rot; the
  ruling can be lifted later and prompt 6 run on exactly these files.
- **No per-query rows exist and none will until the ruling is lifted.** W-87,
  W-176 gates 4–9 and W-191 wait on a scored run and stay 🔴 — blocked on Arpit,
  because only he lifts a "not now."
- ⚠ **W-176 can be built and cannot land.** The 6E numbers are the strongest
  signal the project has — over 90% of declines wrong, the gate abstaining more
  on answerable than unanswerable — and the band fix is an obvious build. But
  CLAUDE.md's sequencing rule says a milestone does not start while its gating
  prediction is unmeasured, and without rows there is no floor to clear. **A
  session that builds it files it as unmeasured, and does not switch it on.**
- The other seven rungs are unrun. Phase 5 on them is unaffected by this ruling;
  scoring them is.
