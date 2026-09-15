---
type: Report
run: 2026-09-15-ladder-seed-refresh
item: W-136
classification: surface capture
description: "Prompt 4's blind check found every one of the eight golden rungs frozen against a superseded seed — seven of twenty documents, 131 lines, changed under them on 2026-09-15 and nothing detected it. All eight rebuilt from the current seed and re-frozen; ext/ came back byte-identical on all eight, so the generator's determinism is measured rather than asserted."
filed: 2026-09-15
---

# REPORT — the golden ladder, re-frozen against the seed this repo actually has

**Not a paired run.** No arms, no judged queries, no threshold, no question
asked of a rung beyond one smoke `ask` per rung. It is
[prompt 4](../../golden/prompts/4-claude-corpus.md) performed as what it says
it is today — *a check, not a build* — and the check failed. A **surface
capture**, and it files no verdict.

🔴 **Honour declaration, which prompt 4 requires this report to make out loud.**
This session read `work/golden/seed/`, `work/golden/seed-dates.tsv`,
`work/golden/README.md`, `work/golden/prompts/4-claude-corpus.md` and
`work/golden/ladder/` — **and nothing else under `work/golden/`**. It did not
open, list, glob, grep, hash, count or stat `work/golden/questions/` or any path
holding an answer, and no question text and no answer text reached its context.

⚠ **Prompt 4's ordering rule was NOT kept, and could not be.** *"Run this
BEFORE prompts 2 and 3 where you can"* — Arpit ran prompts 2 and 3 earlier the
same day, so both question sets were on disk before this ran. **The honour rule
above is the whole of what protects this phase**, and nothing mechanical
enforces it. The rungs below are `blind` on that basis and on no other.

## What the check found

The ladder agreed with itself perfectly, and was wrong.

| check | result |
|---|---|
| all eight rungs present in `fux-lab` | ✅ |
| every document on disk matches its manifest | ✅ 0 drifted, 0 missing of 18 820 |
| nesting, rung N-1 ⊂ rung N | ✅ all seven steps |
| `ladder_check.py` | ✅ *"8 rungs, manifests consistent and nesting verified"* |
| 🔴 **manifest `seed/` half vs `work/golden/seed/`** | 🔴 **7 of 20 documents stale, on all eight rungs** |

**What moved under them.** Commit `0aa4bbcf` (2026-09-15 18:34) extended seven
of the twenty seed documents by **131 lines** — a concurrent Cowork session's
work, committed by the W-168 session on Arpit's instruction to commit everything
staged. The rungs were frozen on **2026-09-12**. The changed documents:

```
seed/01-sop-temperature-excursion.md
seed/03-postmortem-nagpur-vaccine-excursion.md
seed/04-night-shift-handover-log.txt
seed/05-decision-telematics-vendor-2023.md
seed/06-re-fw-telematics-cutover.eml
seed/08-driver-hours-and-safety-policy.md
seed/09-dock-scheduling-wiki-export.html
```

🔴 **Both question sets were authored after that commit** — `bed465f3` is the
tip — so the questions were written against seed text **no rung contained**.
A rung in that state does not fail: it answers, ranks, and returns a number
shaped exactly like a real one.

## What was done

`work/golden/seed/` genuinely changed, which is the one condition
[prompt 4](../../golden/prompts/4-claude-corpus.md) authorises a rebuild on
(*"rebuild ONLY what is missing or what a genuinely changed seed invalidates"*).
All eight rungs were rebuilt by [`evidence/rebuild.py`](evidence/rebuild.py), a
thin driver over the **unmodified** 2026-09-12 builder and generator —
`build_golden_rung.py` and `make_golden_ext.py` are the reproducibility claim
for `ext/`, and editing them would have destroyed the one check worth making.

| rung | documents | archived | superseded | `mtime` | `ask` | index format | seed files skipped |
|---|---:|---:|---:|---:|---:|---|---:|
| `rung-seed` | 20 | 5 | 4 | 20 / 20 | 3 results | `fux.index.v3` | 0 |
| `rung-00100` | 100 | 13 | 12 | 100 / 100 | 3 results | `fux.index.v3` | 0 |
| `rung-00200` | 200 | 23 | 22 | 200 / 200 | 3 results | `fux.index.v3` | 0 |
| `rung-00500` | 500 | 53 | 52 | 500 / 500 | 3 results | `fux.index.v3` | 0 |
| `rung-01000` | 1 000 | 103 | 102 | 1 000 / 1 000 | 3 results | `fux.index.v3` | 0 |
| `rung-02000` | 2 000 | 203 | 202 | 2 000 / 2 000 | 3 results | `fux.index.v3` | 0 |
| `rung-05000` | 5 000 | 503 | 502 | 5 000 / 5 000 | 3 results | `fux.index.v3` | 0 |
| `rung-10000` | 10 000 | 1 003 | 1 002 | 10 000 / 10 000 | 3 results | `fux.index.v3` | 0 |

**Every count is identical to 2026-09-12's** — the coverage files differ by zero
lines. Declarations, archived-ness and supersession are properties of *which*
documents are in a rung, and the rebuild changed none of them: it changed the
bytes of seven.

## 🔴 `ext/` came back byte-identical on all eight rungs

This is the claim the 2026-09-12 README made — *"anyone re-deriving them gets
the same bytes; that is the claim, and it is checkable"* — and it has now been
checked, three days later, on a different engine commit, by a different session.

```
rung          ext lines changed   seed lines changed   coverage lines changed
rung-seed              0                 14                    0
rung-00100             0                 14                    0
rung-00200             0                 14                    0
rung-00500             0                 14                    0
rung-01000             0                 14                    0
rung-02000             0                 14                    0
rung-05000             0                 14                    0
rung-10000             0                 14                    0
```

**18 800 generated documents, zero drift.** Fourteen changed lines per rung is
exactly seven documents leaving and seven arriving. The generator, its fixed
seed, its stable order and its seed-entity blacklist all hold.

⚠ **Every rung's `index_root_sha256` and `rung_head_commit` changed**, because
the indexed bytes changed. Old and new are in
[`evidence/rebuild-diff.tsv`](evidence/rebuild-diff.tsv), and the whole
pre-rebuild ladder is kept verbatim at
[`evidence/ladder-before-2026-09-12/`](evidence/ladder-before-2026-09-12/).

## 🔴 What this costs: every filed ladder number now names a corpus that is gone

Not a consequence of the rebuild — a consequence of the seed moving on
2026-09-15, which the rebuild only makes visible. Numbers measured on the old
rungs are numbers about a corpus that no longer exists, and **may not be
compared with anything measured from here on**:

- [`2026-09-15-anchor-mechanism`](../2026-09-15-anchor-mechanism/report.md) —
  0 of 124 flips at four anchor weights. ⚠ **Its finding survives and its
  numbers do not.** The finding is *the ladder has no anchor-bearing edges*, and
  the re-frozen seed still has none: its only three `<a href>` tags point at
  site-absolute paths that resolve to no document in any rung, they predate the
  extension, and an `href` with no corpus target creates no `ref` edge. ⚠ That
  report's wording — *"zero markdown or HTML link syntax"* — is imprecise;
  `ANALYSIS.md` §What is NOT resolved carries the correction, because a filed
  report is frozen.
- [`2026-09-15-ladder-reingest`](../2026-09-15-ladder-reingest/report.md) —
  a surface capture of eight index roots, all eight now superseded.

No frozen pre-registration pins a rung index root, so **no threshold moved and
none needed a dated addendum** — checked across `work/regression/` and
`work/benchmark/`.

## The gate this run owes — two strikes, so a check

**The failure class is *the golden ladder drifts and nothing detects it*, and
this is its second recorded occurrence** ([SR-WORK-SESSION](../../../records/0060_WORK-session.md)
decision 13):

1. **W-186, 2026-09-15** — a format bump and two retired config keys had made
   all eight rungs unreadable for nine days. *"Nothing detected it. No test,
   hook or CI arm reads a rung."*
2. **this run** — eight rungs frozen against a superseded seed. `verify()`
   passed, `ladder_check.py` passed, every manifest matched its corpus exactly.

🔴 **Both checks compare the ladder against itself.** `verify()` asks *does this
corpus match its manifest*; `ladder_check` asks *do the manifests agree with
each other*. Neither ever asks *is this the seed corpus the repo has*, and that
is the only question that catches a document changing upstream of a frozen rung.

Shipped in this change:

- **`rungs.seed_drift(name)`** — the live `work/golden/seed/` hashed against a
  rung's manifest. It reads `seed/` and nothing else under `work/golden/`.
- **`ladder_check.py` check 4**, which prints `STALE` beside the offending rung.
- **[`tests/test_golden_ladder_seed.py`](../../../tests/test_golden_ladder_seed.py)**
  — one parametrised case per rung, in the **fast** suite, needing no corpus,
  so it runs on a clean clone and on a runner. It caught the two un-rebuilt
  rungs while the rebuild was still running, which is the only demonstration a
  gate of this kind can give.

## Reproduce

```bash
# the check, on any machine, with or without the lab corpus
./.venv/bin/python -m pytest -q tests/test_golden_ladder_seed.py
./.venv/bin/python tools/differential/ladder_check.py

# the rebuild itself — needs ~/my_programs/fux-lab, ~26 min for all eight
./.venv/bin/python work/regression/2026-09-15-ladder-seed-refresh/evidence/rebuild.py
```

## What was NOT done

- **No question was asked of a rung beyond the smoke `ask`**, and no question
  was written. Prompt 4 forbids both; phase 5 is where a rung meets a question.
- **The ladder stops at 10 000.** `CLAUDE.md` §Litmus and
  [SR-WORK-ENVIRONMENTS](../../../records/0052_WORK-environments.md); no ninth
  rung exists and none was built.
- **A directory that L11 says is not a location was left untouched** — see
  `ANALYSIS.md` §For Arpit.
