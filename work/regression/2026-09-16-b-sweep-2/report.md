---
type: Regression Run
name: b-sweep-2
description: "The lower `b` range, run against the re-specified rule. `b = 0.15` is the first descending value that clears: `content` +30 and `main` +30, p = 0.0000 each against a required 12, with all four controls holding — including `verbose`, which is proven able to lose, and `dump`, reclassified as a control the day before."
run: 2026-09-16-b-sweep-2
item: W-144
prediction: W-144-B-SWEEP-2
classification: informed
status: complete
timestamp: 2026-09-16T00:00:00Z
---

# The lower `b` sweep, run

**Verdict: [`PASS` at `b = 0.15`](VERDICT.md).** Ruled against
[the pre-registration](PRE-REGISTRATION.md), frozen and **committed alone**
before this ran.

**Reproduce:**

```bash
.venv/bin/python tools/quality-controls/w144_graded.py gen --dest /tmp/w144corpus2
.venv/bin/python tools/quality-controls/w144_graded.py bsweep --corpus /tmp/w144corpus2 \
    --values 0.75 0.4 0.3 0.2 0.15
```

**510 generated documents, 180 probes in six families**, 30 each. One lever
moves — `[bm25f] b` — and `flen` is the **shipped** one in every arm: this is
not option (b) and it excludes no table tokens. Probe-term `df` 2–12,
`avg_wlen` 566.2.

---

## hit@1 per family, per value

| family | role | `0.75` | `0.4` | `0.3` | `0.2` | **`0.15`** |
|---|---|---:|---:|---:|---:|---:|
| `main` | benefit | 0/30 | 0/30 | 0/30 | 0/30 | **30/30** |
| `content` | benefit | 0/30 | 0/30 | **30/30** | **30/30** | **30/30** |
| `dump` | 🔴 control | 30/30 | 30/30 | 30/30 | 30/30 | **30/30** |
| `inverse` | control | 30/30 | 30/30 | 30/30 | 30/30 | 30/30 |
| `placebo` | control | 30/30 | 30/30 | 30/30 | 30/30 | 30/30 |
| **`verbose`** | control | 30/30 | 30/30 | 30/30 | 30/30 | **30/30** |

## The rule, applied in descending order

| `b` | `content` | `main` | controls | clears? |
|---|---:|---:|---|---|
| 0.4 | +0 | +0 | all hold | **no** — neither benefit family moves |
| 0.3 | **+30** | +0 | all hold | **no** — `main` does not net positive |
| 0.2 | **+30** | +0 | all hold | **no** — same reason |
| **0.15** | **+30** | **+30** | **all four hold** | ✅ **clears** |

**At `0.15`:** both benefit families `b = 30, c = 0`, discordant 30, **net 30**,
`p = 0.0000`, against decision 19's **required net of 12** at that count.

🔴 **Descending order is what makes the answer `0.15` rather than something
lower.** The rule reports the **smallest departure from `0.75` that works**, not
the best value, and it stops at the first one.

## Why the controls' holding means something here

**`inverse` and `placebo` have never moved, at any value** — so *"nothing
regressed"* on them is consistent with safety and is not evidence of it. That is
exactly why Arpit made a fourth control a condition of the ruling.

✅ **`verbose` is proven able to lose**: [the control probe](../2026-09-16-b-sweep-2-control/report.md)
put it at 30/30 across this whole range and **0/30 at `b = 0`**, `p = 0.0000`.
**Its `+0` here is a measurement rather than a tautology** — and without it,
`b = 0` and `b = 0.15` are indistinguishable on every other instrument.

✅ **`dump` holds**, which is the specific harm the sweep had to rule out:
W-155 showed option (b) drove it **30/30 → 0/30**.

## Headroom, both directions (SR-RS 22b, 22e, 22f)

Measured in the **baseline** arm (22f):

| family | regression headroom | improvement headroom |
|---|---:|---:|
| `main` | 0 | **30** |
| `content` | 0 | **30** |
| `dump` · `inverse` · `placebo` · `verbose` | **30** each | 0 |

🔴 **Every family is saturated in one direction by construction** (22e): a
benefit family is built wrong at the baseline or the lever has nothing to fix; a
control is built right at it or it cannot report. **The table is read per
family**, and reading a benefit family's zero regression headroom as a fault
would be reading the design as a fault.

## Step 4's checks, after shipping `0.15`

**Arpit's ruling left step 4 unchanged: ship on a clear, with an L3 check and
two-reader byte equality in the same change.** Both ran against the new default:

| check | result |
|---|---|
| **scan vs accelerator, byte-for-byte** | ✅ **22 144 comparisons, byte-identical in every mode** — 692 queries × 4 `top` values × 2 skipping modes × 4 `[priority]` weights ([`evidence/differential-after-ship.txt`](evidence/differential-after-ship.txt)) |
| **two readers** | ✅ `tests/test_node_config_parity.py` holds `B` equal in both; the Node suite passes and the L10 bundle rebuilds |
| **both suites** | ✅ green, whole |

🔴 **The differential is the check that matters here.** `b` sits in the
denominator of every score, so a value that the scan and the accelerator applied
differently would produce **two orderings from one index** — and it would do so
silently, because each path is internally consistent.

⚠ **No fux test pinned `b`'s value**, which is why the suites passing is not
evidence the change is correct. The differential is; the sweep is what says it is
*better*.

## What this does NOT establish

- 🔴 **It does not transfer.** 510 **generated** documents, `informed`, authored
  by this project's own tool. It says a lower `b` ranks better **on documents
  shaped like these**.
- **It does not test option (b).** Excluding table tokens from `flen` is a
  different mechanism, and W-155 showed it destroys `dump`.
- **It is not comparable with [the 2026-09-15 sweep](../2026-09-15-b-sweep/VERDICT.md).**
  Adding 30 terms moved every probe term's `df`, so these are a **replication on
  a different corpus**.
- **No value below `0.15` was tried**, by rule.

## Authorship

| what | who |
|---|---|
| the corpus generator and the `verbose` family | this session |
| the range, the descending rule, the control condition, the `dump` reclassification | **Arpit** (2026-09-15 and 2026-09-16) |
| the frozen bar | [SR-RS](../../../records/0133_predictions.md) decision 19, unchanged |

**`informed`** — synthetic corpus, and its author reads the results. An informed
run is **reclassified, not banned**: filed, cited, never compared with a blind
run.
