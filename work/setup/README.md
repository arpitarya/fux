# `work/setup/` — the things fux needs that fux does not contain

**How to use this directory.** Fux depends on two working directories that sit
**next to** the repo and are not part of it. Neither is shipped, neither is a
submodule, and neither can be reconstructed from anything in this tree. This
directory is where each one's setup and standing contract is written down, so a
session on a fresh machine can stand them up rather than discover them.

| document | thing | location | what it is |
|---|---|---|---|
| [SETUP-PLAYGROUND](fux-playground.md) | `fux-playground` | `~/my_programs/fux-playground` | a **sibling git repository** — the graded fixture corpus |
| [SETUP-LAB](fux-lab.md) | `fux-lab` | `~/my_programs/fux-lab` | a **scratch working directory** — the measurement environment |

## Which is which

They get confused, so:

- **The playground GRADES.** Ten adversarial documents and ~50 hand-written
  golden queries asserting *ranks*. It answers *"did this change break an
  answer?"* Its output is pass / xfail / XPASS.
- **The lab MEASURES.** One directory per corpus, each with its own venv,
  baselines and pinned engine version. It answers *"how big, how fast, how
  accurate?"* Its output is numbers, filed into
  [`../regression/`](../regression/README.md).

A ranking change should survive the playground. A performance or size claim
needs the lab.

## Why these are documents and not ADRs

A setup document records **how a thing is stood up and what its contract is** —
operational knowledge that a new machine or a new session needs. An ADR records
a **decision someone could later supersede**.

`SETUP-PLAYGROUND` was an ADR until 2026-08-18 and mostly was not one: the
sibling-repo layout, the CDP port, the golden-file rules and the URL
carry-forward trap are all *how it works*, not a position anyone argues with.
The one real decision inside it — **`examples/` is deleted from the engine
repo** — is settled and kept at the foot of that document, because it is the
reason the repository exists.

This is the same distinction that moved the two P1 rulings into
[`../regression/`](../regression/README.md) as verdicts: **`docs/adr/` is for
decisions, and a great deal of valuable writing is not a decision.**

## The rules

1. **Every document here names its `location` in frontmatter**, and that
   location is **outside this repository** — if it were inside, it would not
   belong here.
2. **`type: Setup`**, with a `name` that is cited in prose (`SETUP-LAB`), the
   same by-name convention the records use.
3. **Setup, not status.** What a thing *is* and how to stand it up. Live work
   against it belongs in [`../OPEN-WORK.md`](../OPEN-WORK.md); measurements
   belong in [`../regression/`](../regression/README.md).
4. **A new external dependency gets a document here in the change that creates
   it** — the same rule the doc registry applies to itself.

Checked by [`../../tests/test_setup_docs.py`](../../tests/test_setup_docs.py).
