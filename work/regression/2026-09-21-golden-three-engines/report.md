---
type: Report
run: 2026-09-21-golden-three-engines
item: W-204
classification: informed
description: "W-204 phase B: fux-engine 1.0.0, 2.0.1 and the frozen HEAD on the same eight golden rungs and the same three question sets, end to end from ingest. 8 976 rows. Captures 1, 2, 5 and 6 filed; 3, 4 and 7 left empty for phase D, because each needs the key. The null control passed at 0 moved rows of 374."
filed: 2026-09-21
---

# REPORT — three engines, one ladder, and no score

🔴 **This run files NO correctness number, and that is the design.** The key is
not open; `hit@k`, the answer-layer capture and the HTML report that reports them
are **phase D's**. What is here is what each engine *did*.

**Pre-registration:** [PRE-REG-BENCH-V1-V2-HEAD](../../benchmark/PRE-REGISTRATION-V1-V2-HEAD.md),
frozen at `efe1f6b6` before any arm ran. **Arms manifest:**
[`evidence/ARMS.md`](evidence/ARMS.md), written before the first A-vs-B row.

## 🔴 The null control ran FIRST and passed

**`v1.0.0` against itself, `rung-00500`, all three sets, two independent
`arm_corpus.py` builds and two independent runs: 374 rows compared, 0 moved.**

Nothing else in this run was measured until that number existed. It compares
what the **engine decided** — the ranked list, the answer text, the citations,
the band and `answerable` — and deliberately not `ask_ms` or the arm label,
because wall clock is not a result and a control that failed on a busy machine
would be a control nobody trusts.

**It could have failed.** An unseeded iteration order, a wall-clock field or a
path-dependent tie-break produces differences between *identical* arms, and every
one would have been attributed to the version bump.

## The three arms

| | v1 | v2 | HEAD |
|---|---|---|---|
| version | `fux 1.0.0` | `fux 2.0.1` | `fux 3.0.0-alpha.1` @ `7a88a165` |
| index format | `fux.index.v1` | `fux.index.v2` | `fux.index.v4` |
| interpreter | CPython 3.11.15 | 3.11.15 | 3.14.3 |
| `[bm25f] b` | **no `tune.toml` at all** | 🔴 **0.75** | 🔴 **0.15** |
| `ask --band` | 🔴 **does not exist** | yes | yes |
| seed documents it can read | 🔴 **24 of 28** | 28 | 28 |

**8 976 rows** — 374 questions × 8 rungs × 3 arms. HEAD's 2 992 are phase A's, at
the sha this manifest names; re-running them would spend 6 000 calls reproducing
a file that exists.

## 🔴 The two asymmetries were measured on a smoke arm BEFORE the run

Both are in [ARMS.md](evidence/ARMS.md) §2, written before the first row:

1. **v1.0.0 has no `formats.toml` and indexes `.md`/`.txt` only**, so it skips
   `02-sensor-thresholds.yaml`, `06-re-fw-telematics-cutover.eml` and two
   `.html` files — **on every one of its eight builds**, visible in the run log.
   🔴 **That is the arm.** The capability came later; there is no mechanism in
   v1 to give it. **So a `v1 → v2` figure is dominated by *v2 can read four more
   file types*, which is a real product difference and is NOT a ranking result.**
2. **v1.0.0's `ask` has no `--band`**, and argparse exits `2` on an unknown flag.
   A harness that hardcoded it would have recorded ~3 000 empty results for v1
   and they would read as a ranking collapse. **`band` and `answerable` are
   `null` on every v1 row, never `weak`**, and every band statement in this
   benchmark is a `v2 → HEAD` statement.

## Capture 2 — what moved, and the one sentence that stops it being misread

Full rows in [`evidence/captures.md`](evidence/captures.md). At `rung-10000`:

| pair | set | n | top-1 changed | whole list changed |
|---|---:|---:|---:|---:|
| v1 → v2 | 1 | 125 | 40 | 109 |
| v1 → v2 | 2 | 124 | 61 | 110 |
| v1 → v2 | 3 | 125 | 48 | 115 |
| **v2 → HEAD** | 1 | 125 | 42 | **125** |
| **v2 → HEAD** | 2 | 124 | 58 | **124** |
| **v2 → HEAD** | 3 | 125 | 66 | **125** |
| v1 → HEAD | 1 | 125 | 67 | 125 |

🔴 **`v2 → HEAD` changes the ranked list on EVERY query at EVERY rung, and the
cause is one measured knob.** v2 ships `b = 0.75` and HEAD ships `b = 0.15` —
[W-144](../2026-09-16-b-sweep-2/VERDICT.md), the first ranking default in
SR-RANKING that was measured rather than inherited. Length normalisation enters
every document's score, so moving it reorders everything.

⚠ **The honest reading is *one knob moved and it reorders everything*, not *the
engine was rewritten*.** The pre-registration's rule — *"the `b` default differs
between arms; that IS the arm, not a knob to equalise"* — is what makes these
rows legitimate, and equalising `b` would measure a version of HEAD nobody ships
against a version of v2 nobody shipped.

🔴 **A changed list is not a better list.** With no key, *125 of 125 moved*
says the engines disagree and says nothing about which is right. **That is
phase D's question and this run does not touch it.**

## Capture 5 — committed index bytes (KB)

| rung | v1 | v2 | HEAD | HEAD ÷ v1 |
|---|---:|---:|---:|---:|
| `rung-seed` | 200 | 212 | 216 | 1.08 |
| `rung-01000` | 2 700 | 2 972 | 3 052 | 1.13 |
| `rung-10000` | **21 444** | **24 120** | **24 876** | **1.16** |

**HEAD commits 16 % more than v1 at 10 000 documents** — and v1 is indexing
**four fewer seed documents**, so a slice of that is corpus rather than format.
The growth is monotone and modest; nothing here is a regression against the
2026-08-28 `1.25×` bar, which this run does not inherit.

## Capture 6 — speed, `ask` p50 / p95 ms

| rung | v1 | v2 | HEAD |
|---|---|---|---|
| `rung-seed` | 38 / 40 | 60 / 66 | 69 / 71 |
| `rung-01000` | 58 / 66 | 96 / 127 | 98 / 106 |
| `rung-10000` | **237 / 336** | **322 / 438** | **304 / 379** |

⚠ 🔴 **NOT interleaved — the arms ran in blocks, so this is DESCRIPTIVE and may
not be cited against [SR-WORK-BENCHMARK](../../../records/0053_WORK-benchmark.md)'s
capture 6.** L9 requires interleaving and this run did not do it: 16 sequential
arm builds and runs on one machine, over about two hours, with other work on the
box. **A latency claim from these numbers needs a second, interleaved run.**

⚠ **v1 is the fastest arm and it is also doing less** — 24 documents rather than
28 at the seed, no confidence band, no anchor branch. **Faster is not better when
the arms are not doing the same work.**

## 🔴 Captures 3, 4 and 7 are EMPTY, and each says why

| # | capture | state |
|---|---|---|
| 1 | ranked lists per query per arm | ✅ **filed** — 8 976 rows |
| 2 | what moved between arms | ✅ **filed** |
| 3 | `hit@k` at 1/5/10/20/50 | ⬜ **phase D** — needs `relevant` from the key |
| 4 | the answer layer vs the planted unanswerables | ⬜ **phase D** — needs `answerable` |
| 5 | committed index bytes | ✅ **filed** |
| 6 | speed | ✅ **filed, descriptive** |
| 7 | the HTML report | ⬜ **phase D** — it reports 3 and 4 |

**The skeleton for capture 7 is filed** at
[`work/benchmark/reports/2026-09-21-golden-three-engines.html`](../../benchmark/reports/2026-09-21-golden-three-engines.html),
with every section present and the three unscored ones carrying
`<p class="nonumber">` — the template's rule 4: *a capture this run has no number
for KEEPS its section and says so; deleting the section hides the gap.*

## Headroom — why there is none to disclose

🔴 **No endpoint in this run is scored, so there is no headroom to state.**
[SR-RS](../../../records/0133_predictions.md) decision 22 asks, per endpoint and
per direction, how many queries *could* have changed — **improvement headroom**
being the queries not right in both arms and **regression headroom** the queries
not wrong in both. Both questions need a notion of *right*, and this run has
none: the key is not open and captures 3 and 4 are deliberately empty.

**Capture 2 counts movement, and movement has no direction without a key.** A
headroom number computed from it would be the count of queries that differ,
dressed as a ceiling on improvement — which is precisely the kind of number
decision 22 exists to stop.

⚠ **Stated rather than omitted**, because a missing disclosure and an
inapplicable one look identical in a filed report. **Phase D is the scored run**,
and headroom is disclosed there, on rows this run already filed.

## What phase B may NOT be read as saying

- That any arm is better, more accurate or more useful. **No key, no correctness.**
- That `v1 → v2` is a ranking comparison. It is dominated by a **types allowlist**.
- That `v2 → HEAD` is an algorithm change. It is dominated by **one measured knob**.
- Any latency claim. **Not interleaved.**
- Anything pooled across the three sets.

## Reproduce

```bash
evidence/run-arms.sh          # the 16 builds and runs
python3 evidence/null_check.py   # the control
python3 evidence/captures.py     # every table above
```

## Authorship

| artifact | author | blind? |
|---|---|---|
| `questions/set-1.jsonl` | Codex | blindness ended at the 2026-09-17 breach |
| `questions/set-2.jsonl`, `set-3.jsonl` | Claude | never blind |
| the arms, the manifest, this run | Claude Code | — |

**`classification: informed`** on [SR-RS](../../../records/0133_predictions.md)
decision 11 — sets 2 and 3 share an author with the runner, set 1 lost
blindness, and these rows feed a scored run. **No arm here is `blind` and none
may be labelled so.** 🔴 **No answer key was used, needed or reachable.**
