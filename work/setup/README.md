---
type: Index
description: "Index of the three sibling environments — how each is stood up, and which is which."
---

# `work/setup/` — the things fux needs that fux does not contain

**How to use this directory.** Fux depends on three working directories that sit
**next to** the repo and are not part of it. None is shipped, none is a
submodule, and none can be reconstructed from anything in this tree. This
directory is where each one's setup and operational contract is written down, so
a session on a fresh machine can stand them up rather than discover them.

| document | thing | location | what it is |
|---|---|---|---|
| [SETUP-PLAYGROUND](fux-playground.md) | `fux-playground` | `~/my_programs/fux-playground` | a **sibling git repository** — Arpit's sandbox |
| [SETUP-LAB](fux-lab.md) | `fux-lab` | `~/my_programs/fux-lab` | a **scratch working directory** — the measurement environment |
| [SETUP-BENCHMARK](fux-benchmark.md) | `fux-benchmark` | `~/my_programs/fux-benchmark` | a **scratch git repository** — the two-version timing harness |

## Which is which

🔴 **Each one has exactly one job, and the job is stated by
[L9](../../docs/adr/0011_LAW-9-environments.md) — read it there.** This section
does not restate the law ([L0](../../docs/adr/0002_LAW-0-authority.md)); it
exists because the three get confused, and it points at the right document.

| if you want to | go to |
|---|---|
| try something by hand, break it, wipe it | the playground — **and you are Arpit, or you are in the wrong place** |
| produce a number anyone will cite: quality, size, accuracy, a verdict | [SETUP-LAB](fux-lab.md) |
| know how fast a query is, or whether a ranking moved between two versions | [SETUP-BENCHMARK](fux-benchmark.md) |

⚠ **Before 2026-09-11 the playground was the grading corpus**, and roughly forty
documents, tools and plans in this repo used it as an instrument. L9 ended that;
[W-138](../../archive/open/W-138-reconcile-with-l9.md) is the reconciliation, and
[`tests/test_l9_environments.py`](../../tests/test_l9_environments.py) is what
stops it coming back.

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
