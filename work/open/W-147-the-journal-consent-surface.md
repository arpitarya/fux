---
type: OpenItem
id: W-147
title: "W-147 — `.fux/output.toml` can turn the journal on, and ADR-PROVENANCE decision 10 says only a flag can"
description: "A committed `[cli.answer] journal = true` writes a durable local record of every question asked in that repo. Decision 10 reserved always-on journalling as a fork nobody may pick; the capability then shipped through ADR-OUTPUT, which never mentions it. One ruling: is a committed opt-in consent, or does output.toml refuse the key?"
status: open
lane: arpit
timestamp: 2026-09-12T00:00:00Z
filed: 2026-09-12
---

# W-147 — the journal's second consent surface

**Model: Opus** if it needs analysis; **it needs a ruling, not analysis.**

**Found** 2026-09-12 re-deriving [W-140](W-140-guide-authoring-defects.md) row 3
against `src/fux`, on the Mac.

## What is true today

| | |
|---|---|
| **What writes** | `fux answer --journal`, **and** a repo whose `.fux/output.toml` carries `[cli.answer] journal = true` — both set the same `args.journal` |
| **What the record says** | [ADR-PROVENANCE](../../docs/adr/0143_provenance.md) decision 10: *"only `--journal` WRITES… the flag is the consent"*, and always-on journalling *"needs a `.fux/tune.toml` key… it is a fork, and no session may pick a default on one"* |
| **What is on by default** | nothing — `false` in `output_config.BUILT_IN` and in the generated specimen |
| **What is recorded** | 🔴 **nothing.** [ADR-OUTPUT](../../docs/adr/0144_output-defaults.md) never mentions `journal`; the key was added to `[cli.answer]` and the fork decision 10 reserved was never ruled |

## The one question

**Is a committed `journal = true` the explicit consent decision 10 asks for?**

- **(a) Yes — keep it, and record it.** A line in a committed file is *more*
  reviewable than a flag somebody types: it is in git, in a code review, and in
  `fux doctor`'s reach. ADR-OUTPUT gains a `journal` paragraph and decision 10
  is amended to name two consent surfaces.
- **(b) No — `output.toml` refuses the key by name.** That file already refuses
  a per-verb key at the shared level *"by name"*, so the machinery exists. The
  argument: every other key there changes how an answer is **displayed**; this
  one changes whether the question **survives the process**, and a reader
  skimming a rendering config has no reason to expect that.
- **(c) Neither — put it where decision 10 said.** A `.fux/tune.toml` key, as
  originally reserved. ⚠ This is the most work and the least obviously right:
  `tune.toml` is the *ranking* file, and journalling is not ranking.

## Why it is not an agent's call

Decision 10 named it a fork and said **no session may pick a default on one**.
It also sits on [L8](../../docs/adr/0010_LAW-8-use-record.md)'s territory — the
record of who went looking — which is a law Arpit ruled on three times in one
day and narrowed twice.

## Definition of done

1. Arpit rules (a), (b) or (c).
2. The chosen shape is built, with a test, and **ADR-PROVENANCE decision 10 and
   ADR-OUTPUT are both amended in the same change** — today one is false and the
   other is silent.
3. Row, inbox row and this file removed; outcome in `IMPLEMENTATION.md`.
