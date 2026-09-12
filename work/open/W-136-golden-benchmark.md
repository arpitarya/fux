---
type: OpenItem
id: W-136
title: "W-136 — the sealed golden benchmark"
description: "Arpit, 2026-09-11: Codex writes 10 seed documents and ~100 questions with answers Claude never sees; Claude grows the corpus 10 → 10 000 blind; Claude runs fux per rung; Codex scores without revealing answers. The test data for fux-lab (L9)."
status: open
lane: arpit
timestamp: 2026-09-11T00:00:00Z
---

# W-136 — the sealed golden benchmark

**The process is [`work/golden/README.md`](../golden/README.md)** — stated there
once; this file carries only state. Prompts: [`work/golden/prompts/`](../golden/prompts/).

## State

| phase | who | lane | state |
|---|---|---|---|
| 1. Seed + answer key | Codex, **stood in for by Claude 2026-09-12** | — | ✅ **done, provisionally** — 20 documents, `seed-dates.tsv`, 124-question key held in chat. Regenerated under [W-145](W-145-codex-regenerates-the-key.md) |
| 2. Extend 10 → 10 000, blind | Claude Code (Opus) | `agent` | ✅ **done to rung 1 000** on 2026-09-12 — five rungs built, frozen and committed *before* the questions were opened. `rung-02000`/`05000`/`10000` are **not built**: Arpit capped this session at 1 000. |
| 3. Freeze ladder, release questions | Codex | `arpit` — run prompt 3 | ⚠ **released early** on 2026-09-12, before the ladder existed — ids permuted so no band identifies the unanswerables. Phase 2 was on its honour and did not open `questions/`. |
| 4. Run each rung | Claude Code | `agent` | ✅ **run on 2026-09-12** for the five built rungs, under a committed pre-registration ([`work/regression/2026-09-12-golden-ladder/`](../regression/2026-09-12-golden-ladder/PRE-REGISTRATION.md)). Predictions and prose answers are filed per rung. |
| 5. Score each rung | Codex | `arpit` — run prompt 5 | 🟢 **ready** — predictions and answers are filed for five rungs. Every number it produces is `informed` until [W-145](W-145-codex-regenerates-the-key.md) closes. |

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
same breath for Codex to regenerate the key — [W-145](W-145-codex-regenerates-the-key.md),
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

## Where the key lives (Arpit, 2026-09-11)

- **Never in the directory by default.** Codex asks in phases 1, 3 and 5: *(1) the
  file `golden-answer/answers.jsonl`, or (2) the chat?* — and waits. The placeholder
  file was removed.

## Feature coverage — prompt 1b (Arpit, 2026-09-11)

- Ruled (b) for the four ranking priors: Codex adds ≥ 4 superseding pairs, ≥ 4 archived documents, a date per seed and ≥ 22 intent-split questions ([prompt 1](../golden/prompts/1-codex-seed.md) part A §3, which absorbed prompt 1b on 2026-09-12); phase 2 declares, dates and checks coverage. Rule: ADR-RS decision 23. The first rung is `rung-seed`.

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
  *(records: [ADR-RS](../../docs/adr/0133_predictions.md) · [ADR-QUALITY](../../docs/adr/0141_quality-contract.md) ·
  setup: [fux-lab](../setup/fux-lab.md))* · **Arpit, 2026-09-11.**
  Codex writes 10 seed documents and ~100 questions with answers in
  `work/golden/golden-answer/` — **Claude never reads it**. Claude grows the corpus
  **10 → 10 000** without seeing a question; Codex freezes it and releases questions
  only; Claude runs fux per rung; Codex scores and returns per-query results with no
  answers. The test data for fux-lab ([L9](../../docs/adr/0011_LAW-9-environments.md)). Process:
  [`golden/README.md`](../golden/README.md) — [detail](W-136-golden-benchmark.md)
  `filed: 2026-09-11`
