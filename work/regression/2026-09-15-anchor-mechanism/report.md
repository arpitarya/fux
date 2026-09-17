---
type: Report
run: 2026-09-15-anchor-mechanism
item: W-168
classification: surface capture
description: "The anchor field cannot move on the golden ladder: 0 anchor-bearing edges on all eight rungs, every edge `supersedes`, and 0/124 questions move at anchor ∈ {0.5, 1.0, 2.0, 3.0} on rung-seed, rung-00100, rung-01000 and rung-10000 — the design point included. A positive control on a built corpus moves the target from non-candidate to top-1, so the zero is the corpus and not the harness. A data defect under SR-RS decision 23b — NOT a null, and NOT a verdict against the frozen pre-registration."
filed: 2026-09-15
---

# REPORT — the anchor field has no input on the golden ladder

**Not the arms.** [The anchor-text
pre-registration](../2026-09-15-anchor-text/PRE-REGISTRATION.md) is untouched by
this run and still has no `VERDICT.md`. Its clause 5 forbids proceeding on a
corpus that does not satisfy §*What the data must contain*; **this run is the
measurement of whether that corpus does**, and the answer is no.

It is the **mechanism probe** [SR-RS](../../../records/0133_predictions.md)
decision 22c requires before an endpoint may be believed — the same shape that
carried the finding in [the `b` sweep](../2026-09-15-b-sweep/VERDICT.md) hours
earlier.

## Why this could run today, with the key sealed

**Movement is not correctness.** Whether a ranking *changes* is arithmetic on
two rank lists; whether it changed for the *better* needs the judgments. So this
run reads `work/golden/questions/questions.jsonl` — `{"id", "question"}`, 124
rows, released 2026-09-12 — and **no answer key**, which is closed to every
Claude session by [L11](../../../records/0012_LAW-11-sealed-answer-key.md).

That is the whole reason a zero here is worth filing: **it needs no judge.**

## 1 — What the corpus offers the feature

Counted from the committed index of every rung, twice, by two independently
written counters that agree.

| rung | documents | edges | **anchor-bearing** | kinds |
|---|---:|---:|---:|---|
| `rung-seed` | 20 | 4 | **0** | `supersedes` 4 |
| `rung-00100` | 100 | 12 | **0** | `supersedes` 12 |
| `rung-00200` | 200 | 22 | **0** | `supersedes` 22 |
| `rung-00500` | 500 | 52 | **0** | `supersedes` 52 |
| `rung-01000` | 1 000 | 102 | **0** | `supersedes` 102 |
| `rung-02000` | 2 000 | 202 | **0** | `supersedes` 202 |
| `rung-05000` | 5 000 | 502 | **0** | `supersedes` 502 |
| `rung-10000` | 10 000 | 1 002 | **0** | `supersedes` 1 002 |

🔴 **Not one `ref` edge exists anywhere on the ladder.** Every edge on all eight
rungs is `supersedes`, carried by explicit supersession metadata. An anchor
edge is one that carries `at` (hashed anchor terms) and `al` (anchor token
length) — W-168 step 1's decision 1 — and **no edge on the ladder carries
either**.

The source confirms it upstream of the index: **zero occurrences of markdown or
HTML link syntax** across `work/golden/seed/`. The corpus is SOPs, a YAML
threshold file, an email thread, a handover log, an HTML wiki export and a FAQ —
a realistic logistics corpus in which **no document hyperlinks to another**.

## 2 — What the questions do at each weight

124 questions, one lever, everything else held at its shipped value.

| rung | `anchor` | top-1 changed | top-10 changed |
|---|---|---:|---:|
| `rung-seed` | 0.5 / 1.0 / 2.0 / 3.0 | **0 / 124** each | **0 / 124** each |
| `rung-00100` | 0.5 / 1.0 / 2.0 / 3.0 | **0 / 124** each | **0 / 124** each |
| `rung-01000` | 0.5 / 1.0 / 2.0 / 3.0 | **0 / 124** each | **0 / 124** each |
| **`rung-10000`** | 0.5 / 1.0 / 2.0 / 3.0 | **0 / 124** each | **0 / 124** each |

All 124 questions return results in the baseline arm on every rung, so the zero
is not an empty-result artifact. **1 488 per-query rows** under `evidence/`.

⚠ **`rung-10000` is the design point** — [SR-WORK-SCALE](../../../records/0057_WORK-scale.md)'s
ceiling, and the rung any claim about the engine at scale must reach. The lever
is inert there too, on 10 000 documents and 1 002 edges.

## 3 — The positive control, and it is what makes the zero mean anything

**A zero everywhere is also what a broken harness produces.** So the same
`rank()` function was run against a three-document corpus built for the purpose,
in which `b-target.md` never uses the words `zarvox throughput ceiling` and the
only place they appear is `a-linker.md`'s **link text**:

| `anchor` | top-`k` |
|---|---|
| **0.0** | `a-linker.md` only — **the target is not even a candidate** |
| 0.5 | `a-linker.md`, then `b-target.md` appears |
| 1.0 | `a-linker.md`, `b-target.md` closing |
| **2.0** | **`b-target.md` first**, `a-linker.md` second |
| 3.0 | `b-target.md` first, by a wider margin |

Its index carries exactly what the ladder lacks:
`{"al": 3, "at": {3 hashes}, "dst": "file:docs/b-target.md", "kind": "ref"}`.

🔴 **Both halves of the feature are alive** — the retrieval half
(`_add_anchor_only_candidates` makes a non-candidate reachable at 0.5) and the
scoring fold (it wins at 2.0). **The harness would have seen movement. There
was none to see.**

## Authorship

| artifact | author | could reach |
|---|---|---|
| the golden corpus and ladder | Codex (docs 1–10), Claude (11–15, `archive/`, rungs) | — |
| `questions.jsonl` | the provisional key's author | ids and text only were read here |
| the probe, the control corpus, this analysis | this session (Claude Opus 5) | **no judgments, no answer key, no prior scores** |

**A surface capture**: no arms against a threshold, no judged queries, no
verdict, so no `blind`/`informed` split applies (§Per-run contract row 7). **No
answer key was read**, and under Arpit's 2026-09-12 chat option none exists on
this machine to read.

## Reproduce

```bash
.venv/bin/python tools/quality-controls/anchor_probe.py \
  --corpus ~/my_programs/fux-lab/corpora/golden \
  --rungs rung-seed rung-00100 rung-01000 --k 10 \
  --rows work/regression/2026-09-15-anchor-mechanism/evidence/anchor-rows-small.jsonl

# the design point, ~25 min on this machine
.venv/bin/python tools/quality-controls/anchor_probe.py \
  --corpus ~/my_programs/fux-lab/corpora/golden --rungs rung-10000 --k 10 \
  --rows work/regression/2026-09-15-anchor-mechanism/evidence/anchor-rows-10000.jsonl
```

⚠ **Use fux's own venv.** The default `python3` on this machine is another
project's and lacks `tomllib`, which L7 requires.

⚠ **The ladder was read as re-ingested by
[W-186](../2026-09-15-ladder-reingest/report.md) at `fux.index.v3`**,
`engine_commit 1c84acb6`. At `fux.index.v2` the rungs are unreadable by HEAD and
this run cannot be reproduced at all.
