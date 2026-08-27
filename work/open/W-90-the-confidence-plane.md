---
type: Handoff
name: W-90
title: W-90 — the confidence plane
description: "Fux states how much it believes its own answer, so a consuming agent can tell a grounded result from the closest thing in a corpus that never discusses the question."
status: open
date: 2026-08-27
amended: 2026-08-27
timestamp: 2026-08-27T00:00:00Z
---

# W-90 — the confidence plane

> ## ⚖ R10 RAN on 2026-08-27, and is `INCONCLUSIVE` — read this first
>
> [VERDICT](../regression/2026-08-27-r10-separation-floor/VERDICT.md) ·
> [report](../regression/2026-08-27-r10-separation-floor/report.md)
>
> **`SEPARATION_FLOOR` stays `0.10`. No test was edited** — and could not be,
> because `tests/query/test_confidence.py` asserts the rule relative to the
> constant and never its value, which is exactly why that was built.
>
> **The blocker was never the environment.** This file and `OPEN-WORK.md` both
> said the run *"simply cannot start"* without `fux-playground`;
> `~/my_programs/fux-playground` was on the machine the whole time, with its 50
> goldens, and grades 41/50. The claim came from sessions that had no shell.
>
> ⚠ **It is inconclusive for a reason nobody predicted: the pre-registration
> contradicts itself.** The curve reaches `t = 0.75` at `separation 0.3`,
> **falls back to 0.60 at `0.4`**, then rises to 1.00 — and the frozen document
> holds two rules that read that differently:
>
> | frozen text | reads it as |
> |---|---|
> | §The measurement — lowest bin reaching `t` **and staying at or above it for every higher bin** | floor **`0.5`** |
> | §Frozen verdict rules row 4 — a **non-monotone** crossing is *"too noisy to read → no change"* | **no change** |
>
> **Both fit, so it was handed to Arpit rather than adjudicated**
> (`CLAUDE.md` §A pre-registered threshold may never move). ⚠ **Picking `0.5`
> would be the moving-threshold failure in its most natural costume.**
> Corrected for the future in [ADR-RS](../../docs/adr/0036_predictions.md)
> decision 18 — **never by editing the frozen file** (W-82 ruling 8).
>
> **What is true either way:** six queries sit at or above `0.5`, the bin that
> first reaches `t` holds four, and the top two bins are empty. **No reading
> supports shipping a constant**, which the pre-registration said in advance.

**Model: Opus.** The build is done; what remains is a **gate call** (R10) and a
**record ratification**, both judgment under [CLAUDE.md](../../CLAUDE.md) §the
lifecycle. R10 could be Sonnet once its pre-registration is frozen — freezing it
is the Opus part, and decision 6 makes it harder than it looks.

## Why this exists

An agent handed a ranked list cannot tell *"these documents answer your
question"* from *"these are the closest things in a corpus that never discusses
it"*. Both arrive as a score, a title and a citation, and every citation is
real. That is where an agent invents an answer and grounds it in a genuine file.

Arpit, 2026-08-27, in Cowork: *"Fux will be used as an input for the agents, and
I want agents to know that, okay, the outputs that Fux gave, it's not having a
huge overlap… or it is not confident enough."*

## What is built (2026-08-27)

Decisions are in [ADR-CONFIDENCE](../../docs/adr/0045_confidence.md); this file
is the state, not a second copy of the record.

| piece | where | state |
|---|---|---|
| the four signals and the band | `src/fux/query/confidence.py` | built |
| `(surface, analyzed)` pairs | `src/fux/query/analyzer.py::analyze_pairs` | built |
| `stats_out` on the two candidate paths | `query/rank.py`, `query/scan.py`, `derive/accel.py` | built |
| `confidence_out` on `run_query` | `query/__init__.py` | built |
| `ask` / `find` / `answer`, JSON **and** stderr | `query/__init__.py` | built |
| the `fux_search` MCP result + tool description | `src/fux/mcp.py` | built |
| the declared output shape | `query/output.schema.json#confidence` | built |
| tests | `tests/query/test_confidence.py` (30), `tests/query/test_analyzer.py` (8) | **38 green in isolation** |

## ⚠ Two collisions with the concurrent session, both caught late

This item was written as **W-89** and its record as **ADR 0043**. Both were
taken by the concurrent session *while this session was building*:

- **W-89** is now *does L2 reach a query log?* → this item is **W-90**.
- **0043** is now `0043_locks.md` and **0044** is `0044_quality-contract.md` →
  this record is **0045**.

⚠ **`docs/adr/0043_confidence.md` and `work/open/W-89-the-confidence-plane.md`
are STRAY FILES and must be deleted.** They are the misnumbered originals. The
sandbox lost its bridge before they could be removed, and no `rm` has run. Two
records at `0043` will fail `tests/test_adr_ownership.py` and is exactly the
condition the register warns about.

**The second collision was substantive, and it improved the design.**
[ADR-QUALITY](../../docs/adr/0044_quality-contract.md) landed the same day and
its decision 6 had **already frozen the abstention economics** — `t = 0.75`,
penalty `c = t/(1-t) = 2`, with Chow's rule fixing the reject threshold from the
ratio. This record had independently invented `SEPARATION_FLOOR = 0.10`.
**Two abstention thresholds governing one decision is drift with extra steps**,
so ADR-CONFIDENCE decision 6 was rewritten: the floor is a **proxy** whose
calibration target is ADR-QUALITY's `t`, and R10's job is to find the
`separation` at which `P(correct) = t` — not to pick a good-looking number.

## The forks Arpit ruled, and the one he did not

**Ruled live in Cowork, 2026-08-27, rather than through a compare doc** — noted
because the lifecycle's step 0 normally routes a genuine fork through
[`work/compare/`](../compare/README.md).

- **Surface scope — RULED: everything, `answer` included.**
- **Commit policy — RULED: commit nothing.** The tree carries the concurrent
  session's staged work; this is left uncommitted for Arpit to land in one pass.
- ✅ **Cutoff policy — RULED 2026-08-27 (Arpit, Cowork).** The band **ships**;
  the assumption is ratified. `SEPARATION_FLOOR = 0.10` stays a declared proxy
  calibrated against ADR-QUALITY's `t = 0.75`, and R10 finds the real value or
  says in writing that it is a heuristic.
- ✅ **Emission surface — RULED 2026-08-27 (Arpit, Cowork): `--band` gates the
  CLI; the MCP result is always on.** Recorded as
  [ADR-CONFIDENCE](../../docs/adr/0045_confidence.md) decision 11, with
  decisions 1 and 4 amended. ✅ **BUILT 2026-08-27** — see [ADR-OUTPUT](../../docs/adr/0047_output-defaults.md) and the closed [W-92](../../archive/open/W-92-output-defaults.md).
- ✅ **Ratification — RULED 2026-08-27: ADR-CONFIDENCE is `accepted`**, amended
  first so the record and the code do not disagree. The register row now reads
  `accepted` / `built: partial` — partial because decision 11 is unimplemented.
  ⚠ **`accepted` ratifies the DECISION, not the code.** The unverified suite and
  R10 are separate and stay open below.

## Open — what is owed

0. ✅ **Decision 11 is BUILT (2026-08-27).** `--band` gates `ask`/`find`/`answer`
   in `--json` and on stderr, resolved once in `cli._apply_output_defaults`;
   `mcp.py` is untouched and unconditional; `output.schema.json#confidence` is
   `required: "band_requested"`. ✅ **The cost is retired, not mitigated** —
   [ADR-OUTPUT](../../docs/adr/0047_output-defaults.md) lets a repo commit
   `band = true`, which is a default rather than documentation.
1. ✅ **The two stray files are GONE** — re-derived 2026-08-27 by listing:
   `docs/adr/0043_confidence.md` does not exist (`0043` is `0043_locks.md`) and
   `work/open/W-89-the-confidence-plane.md` does not exist. ⚠ **Verified by
   filesystem, not by `git`** — the Cowork bridge has no shell.
2. ⚠ **R10 is PRE-REGISTERED (2026-08-27) and still UNRUN.** Arpit ruled the
   method: **measure the curve, then declare it a heuristic.** Frozen at
   [`work/regression/2026-08-27-r10-separation-floor/evidence/PRE-REGISTRATION.md`](../regression/2026-08-27-r10-separation-floor/evidence/PRE-REGISTRATION.md)
   — ten fixed bins, the floor being the lowest bin reaching `t = 0.75` **that
   stays at or above it**, per-bin counts published beside every rate.
   ⚠ **It cannot start: `fux-playground` is not on the build machine**, the same
   blocker as W-87 P1. ⚠ **`separation` is ordinal and Chow's rule assumes a
   probability** — the run NAMES that gap rather than closing it, and any report
   calling the result *calibrated* is wrong. ⚠ **Three of the four frozen
   outcomes change nothing**; at ~5 queries per bin the boundary resolves to no
   better than ±0.2, so *not yet* is the likeliest honest answer.
3. ✅ **ADR-CONFIDENCE is `accepted`** (2026-08-27), amended by decision 11
   first. The register's ownership table already carries
   `src/fux/query/confidence.py` → ADR-CONFIDENCE, and
   `tests/test_adr_ownership.py` needed no edit — it parses the table rather
   than hard-coding it.
4. **`ask`/`find` can only report `verified: unverified`.** Honest today. Making
   it more is a fetch on the `ask` path, which is an L4 decision and a different
   record.
5. ✅ **THE SUITE CLAIM ABOVE WAS WRONG AND IS CORRECTED.** *59 failed / 1811
   passed / 8 errors* was the **3.10 sandbox plus concurrent-session
   artifacts**, not real failures — and *predicted* has now been *verified*.
   Measured 2026-08-27 in the cloud container on Python 3.11.15:
   **604 passed / 0 failed baseline → 614 passed / 0 failed**, with W-91's
   in-flight work merged in. `tests/derive/test_weighted_bound.py` passes.
   ⚠ **27 of ~60 test files were staged**; `tests_e2e/`,
   `test_adr_freshness.py` and `test_doc_links.py` **have not run**.

## How to check it

```bash
uv run pytest -q tests/query/test_confidence.py tests/query/test_analyzer.py
uv run pytest -q tests/derive/test_weighted_bound.py     # the open question
fux ask "<a query about something absent>" --json | jq .confidence
```
