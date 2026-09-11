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
| 1. Seed + answer key | Codex | `arpit` — run prompt 1 | 🟡 **seed landed, key unverifiable** |
| 2. Extend 10 → 10 000, blind | Claude Code (Opus) | `agent` | ⏳ **next**, once Arpit confirms the key exists |
| 3. Freeze ladder, release questions | Codex | `arpit` — run prompt 3 | waits on 2 |
| 4. Run each rung | Claude Code | `agent` | waits on 3 · pre-registered, and reported under [ADR-RS](../../docs/adr/0133_predictions.md) decision 22 (where W-135 landed) |
| 5. Score each rung | Codex | `arpit` — run prompt 5 | waits on 4 |

## Done in the filing change (2026-09-11)

- `work/golden/` scaffold, the process README and five prompts. **No key file** —
  where the key lives is Arpit's call each run (below).
- Guards: `.gitignore`, `!work/golden` in `.fux/sources/dirs`, Claude Code
  `permissions.deny` + `.claude/hooks/guard-golden-answer.sh`, CLAUDE.md §Golden
  answer key.

## Phase 1, as far as Claude can see it (2026-09-11)

- **Ten seed documents are in `work/golden/seed/`** and committed — Quillfern Cold
  Logistics, in the six shapes the brief asked for (`.md` with and without
  frontmatter, `.yaml`, `.txt`, `.eml`, `.html`).
- ⚠ **Whether the questions and answers exist is outside any Claude session's
  reach**, by construction — the key is never read, listed or hashed. **Only Arpit
  can close phase 1**, and the inbox row asks him to.
- Phase 2 needs `seed/` and nothing else, so it is runnable the moment he confirms.

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
