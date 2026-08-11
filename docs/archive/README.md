# `docs/archive/` — completed doc artifacts

Handoffs, prompts and proposals live here **once they are fully implemented
and their ADR is written** (CLAUDE.md's archive law). Each carries
`status: implemented` and a link to the ADR that closed it, and is named by
the release version it shipped — `vX.Y.Z-name.md`, not its in-flight index.

Active directories (`handoff/`, `proposals/`) hold *live* work only, so
"what's in flight" is answerable by listing them.

| artifact | shipped | closed by |
|---|---|---|
| [`v0.30.0-m1-t0-slice-handoff.md`](v0.30.0-m1-t0-slice-handoff.md) · [prompt](v0.30.0-m1-t0-slice-prompt.md) | 2026-08-10 | [ADR-0004](../adr/0004-index-format.md) — the index format & committed store; R1 PASS, R2 2/3 PASS at M1 |
| [`v0.31.0-fux-dir-layout-handoff.md`](v0.31.0-fux-dir-layout-handoff.md) · [prompt](v0.31.0-fux-dir-layout-prompt.md) | 2026-08-11 | [ADR-0011](../adr/0011-fux-dir-layout.md) — the `.fux/` layout + URL-source relocation |
| [`v0.31.0-fux-playground-extraction-handoff.md`](v0.31.0-fux-playground-extraction-handoff.md) · [prompt](v0.31.0-fux-playground-extraction-prompt.md) | 2026-08-12 | [ADR-0012](../adr/0012-playground-sibling-repo.md) — the demo corpus leaves the engine repo (41 pass / 9 named `xfail`) |

## Two archives, and why the distinction matters

Both are called "archive". They hold different things, and conflating them
is what put four executed files in `handoff/` for three days
(W-43, closed 2026-08-12).

| directory | holds | rule |
|---|---|---|
| **`docs/archive/`** (here) | completed **doc artifacts** of the current v0.30 build — executed handoff/prompt pairs, implemented proposals | stamped `status: implemented` + ADR link; version-named |
| [`archive/v0.26/`](../../archive/v0.26/) (repo root) | the previous **engine** | runnable, reference-only, never modified, never imported |
| [`archive/v0.26-docs/`](../../archive/v0.26-docs/) (repo root) | the frozen v0.19–0.26 **documentation set** | never edited; its ADRs are always cited as **"archived ADR-NNNN"** with the path |
| [`archive/v0.26-implemented/`](../../archive/v0.26-implemented/) (repo root) | that build's implemented artifacts, including `PLAN-v0.26.md` | frozen |
| [`archive/v0.30-rev1-planning/`](../../archive/v0.30-rev1-planning/) (repo root) | the pre-gate planning pairs for M0/M1 | frozen |

**Short form:** root `archive/` = old **builds**. `docs/archive/` = completed
**doc artifacts** of the current build.

## The reset discrepancy — resolved 2026-08-10

The v0.26 doc set used to sit at `docs/archive/v0.26-docs/`, nested inside
this directory. **Arpit ruled on 2026-08-10** that the nested double-archive
be flattened: everything belonging to an *old build* lives at the repo root,
so the set moved to [`archive/v0.26-docs/`](../../archive/v0.26-docs/).

That ruling **scoped the v0.26 doc set**. It did not retire `docs/archive/`,
which is the destination CLAUDE.md's archive law names for completed doc
artifacts of the *current* build — and which has held the v0.31.0
`.fux`-layout pair since 2026-08-11 under exactly that reading.

The discrepancy is closed. It is recorded here rather than deleted because
it is cited from [ADR-0004](../adr/0004-index-format.md) §Consequences, where
it is the reason R2 question 3 could not be answered at M1.
