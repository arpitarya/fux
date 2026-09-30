---
type: Report
description: "W-168 step 8, the git authority prior: built off at 0.0 in both readers and captured on five arms of set-4-claude at a re-ingested copy of rung-01000. Captured, not scored. The precondition holds: au-0.0 ranks all 125 questions identically to the ip-0.1 hand-off the tag was computed from."
run: 2026-09-28-authority-prior
rung: rung-01000
item: W-168
filed: 2026-09-30
measured: 2026-09-30
classification: informed
status: captured
---

# Report — the git authority prior, W-168 step 8

**Captured, not scored.** Scoring is Arpit's hand
([L11](../../../records/0013_LAW-11-sealed-answer-key.md) decision 13), and the
decision belongs to a session that did not capture
([the pre-registration](PRE-REGISTRATION.md) §What this run may NOT do, 5).

## What ran

- **Engine:** `ee00d0cd` plus the uncommitted step-8 build, stamped
  `ee00d0cd+uncommitted.8f5b5d75` in every hand-off (a digest of the
  `src/fux` and `node/src` diff, unchanged across the capture). The build
  was committed afterwards unchanged; the commit that carries it names this stamp.
- **Index format:** the build moves the index to `fux.index.v6` (runtime
  `fux.runtime.v8`), because [SR-INDEX-LIFECYCLE](../../../records/0108_index-lifecycle.md)
  decision 9.1 bumps `_format` for a new record property (step 4's `abbr` is
  the precedent). The pre-registration did not decide this.
- **Arms:** `au-base` is a `cp -a` of `fux-lab/arms/runs/ip-base/rung-01000`,
  with `intent_weight = 0.1`, then `fux doctor --fix`, then `fux ingest --full`.
  `doctor --fix` also wrote keys that do not reach ranking
  (`refer.timeout_seconds`, `output [api]`, `inspect [identifiers]`):
  [`evidence/doctor-fix.diff`](evidence/doctor-fix.diff). Each arm is a
  `cp -a` of the base with only `authority_weight` changed.
- **Index checks:** against v5, only the `_format` header and the two new
  fields changed. The 12 multi-commit documents' counts match
  [`evidence/multi-commit.tsv`](evidence/multi-commit.tsv). No `@` appears
  in any shard. Index root `fa5b0686…` and `separation_floor 0.1` are the
  same in every arm.
- **Harness:** `tools/quality-controls/golden_run.py`, as in step 9.

## Precondition — the re-ingest moved nothing

`au-0.0` ranks **125 of 125** questions identically to
`2026-09-28-intent-prior/evidence/ip-0.1/rung-01000/handoff-set-4-claude.jsonl`
(sha256 `6207c88e…`, the frozen reference). **No id moved**, so the tag and
the pools stand as frozen. Checked twice: once by the capturing session, and
once, independently, by the session that filed this report.

## The arms, against `au-0.0`

| arm | rank 1 changed | of which tagged | order changed | top-10 membership changed | bands g/p/w | median ask ms |
|---|---:|---:|---:|---:|---|---:|
| `au-0.0` | 0 | 0 | 0 | 0 | 67/24/34 | 166.4 |
| `au-0.1` | 7 | 7 | 71 | 16 | 73/24/28 | 166.9 |
| `au-0.2` | 12 | 12 | 89 | 34 | 79/24/22 | 172.5 |
| `au-0.3` | 17 | 17 | 97 | 44 | 75/24/26 | 171.1 |
| `au-0.5` | 29 | 29 | 108 | 70 | 69/24/32 | 200.4 |

**A changed rank 1 is not a win or a loss.** Which way each moved is
known only after scoring. Every rank-1 change is on a tagged question.

⚠ **One sentence of the pre-registration's prose is wrong, and the bar is
not:** every 2-commit document has 2 authors, so its factor is `1 − 1/4 = 0.75`,
not the `0.5` the §Both directions paragraph estimated. It changes no number
the decision rule reads.

## Headroom

**Improvement headroom** (questions not right in both arms) and **regression headroom** (questions not wrong in both arms) are both deferred to scoring (SR-RS d22b, d22f): each needs the per-question hits, which only the score file carries.

## Hand-offs

| arm | sha256 |
|---|---|
| `au-0.0` | `fb61d35fa16b13da615fc356a67cf343d8ed255f12cd35e98a0228eb053d51fb` |
| `au-0.1` | `b60c84ba0fd8de75fbe314f5f8f4ee7972bd07c18ea4fc763665dd4a5951ead7` |
| `au-0.2` | `82b893be3b972814d488e696330a7d93bb15c08b0bd76e1715c46e9f7103ce83` |
| `au-0.3` | `e1b93aebb3559d3da8d02ef1e4f9107488abff1159e4c5a8fcef269af6e41aac` |
| `au-0.5` | `30b9f96700f08a646501a16caf8e5b0cfc81fe96e92a538b1edc1aafa1a71cbb` |

The per-arm summary is [`evidence/describe.json`](evidence/describe.json),
written by [`evidence/describe.py`](evidence/describe.py).

## Still owed

1. 🔴 **Arpit scores**: `just golden-score work/regression/2026-09-28-authority-prior`, in his shell.
2. **A session that did not capture** writes a frozen `decide.py` adapted
   from step 9's and applies the table. None exists yet.

## Authorship

The capturing session built and captured; it may not decide. It read only
`questions/set-4-claude.jsonl`: no key, no score file, and no scorer. It
disclosed one thing: reverting a worktree-only diff of the committed
`.fux/.fuxignore` showed it that file's existing lines, which name files
under the key directory. It saw names only, no content.
