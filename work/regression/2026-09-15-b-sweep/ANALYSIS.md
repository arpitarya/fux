---
type: Analysis
run: 2026-09-15-b-sweep
description: "Why the frozen range missed the effect, what the saturated controls cost this run, and the fork that goes to Arpit rather than being resolved here."
filed: 2026-09-15
---

# ANALYSIS — the range was set above the effect

## 1 · The diagnosis

**`b` scales length normalisation for every document at once; a table-inflated
`flen` is a large distortion on one document.** At `b = 0.75` the subject pays
for ~900 table tokens that have nothing to do with the query term, and the
rival — a third of the evidence, no table — wins by **0.64 score points**.
Reducing `b` to `0.4` recovers about a third of that gap and the rival is still
ahead. The curves cross near `0.1`.

**So the frozen range is not wrong about the mechanism; it is wrong about the
magnitude.** The pre-registration's own reasoning — *"`b` is THE
length-normalisation parameter, and a table-inflated `flen` is a length
problem"* — is confirmed. What nobody had was a number for how far `b` would
have to move, and `0.6 → 0.5 → 0.4` was chosen as *plausible departures from
the literature's default*, not from a measurement.

⚠ **This is the risk of picking arms by plausibility**, and it is the mirror
image of the risk the descending rule guards against. The rule protects against
picking an extreme because the curve is flat; nothing protected against framing
a range that stops short of the effect. **Both failures are invisible without
the mechanism probe.**

## 2 · What the saturated controls cost this run

🔴 **`inverse` and `placebo` sit at 30/30 in every arm, down to `b = 0`.** They
cannot demonstrate that they would catch a regression; they can only fail to
show one.

**That matters most for the thing this run is otherwise good news about.** The
headline reassurance — *nothing regresses anywhere, including `dump`* — rests on
families with **zero regression headroom in this corpus**. It is consistent with
lowering `b` being safe; it is not evidence that it is.

**Any lower-range pre-registration needs a control that can move**, or it will
reproduce this run's blind spot at a value far enough from `0.75` to matter.

## 3 · What is genuinely established, and it is not nothing

1. **No pre-registered value clears.** Frozen question, unambiguous answer.
2. **The lever reaches the endpoint below the frozen floor** — `content` at
   `≤ 0.3`, `main` at `≤ 0.15` — so the null in §1 of the report is *out of
   range*, not *inert*. SR-RS decision 22c satisfied by the probe.
3. 🔴 **Option (d) does not have option (b)'s defect.** `dump` — the family
   W-155 showed option (b) **destroyed** — holds 30/30 at every value down to
   zero. Lowering `b` rescales every document's length together; excluding table
   tokens rewrote one document's length by ~7×. **That asymmetry is the strongest
   argument in this run and it is an argument for (d), not for a value of it.**

## 4 · The fork, and it is Arpit's

| | |
|---|---|
| **take the fallback as written** | (b) + an idf guard, new pre-registration, same bar. ⚠ It re-inherits W-155's `dump` problem — the one thing §3.3 shows (d) does not have |
| **pre-register a lower range** | the arm exists and the run is minutes. ⚠ **Needs a control with regression headroom first** (§2), and `0.15` is a very long way from `0.75` — which is why the guard exists |
| **stop here** | `b` stays at `0.75`, W-144 closes as *measured, no change*, and the table-inflation defect stays open with its cause understood and unfixed |

🔴 **Not resolved here, deliberately.** The pre-registration's rule 4 hands an
ambiguous result to Arpit; this result is unambiguous about the rule and
ambiguous about what to do next, which is the same destination.

## 5 · The specific changes

| # | change | repro |
|---|---|---|
| 1 | `bsweep` — the arm option (d) needed | `python tools/quality-controls/w144_graded.py bsweep --corpus <dir>` |
| 2 | **the verdict filed: `FAIL`, no value clears** | `evidence/per-query-rows.jsonl`, 600 rows |
| 3 | **W-144 goes to Arpit's inbox**, not closed | `work/OPEN-WORK.md` |
| 4 | ⚠ a second stale-corpus instance found — `w144-graded` refuses to ingest, same class as W-186 | §6 |

## 6 · Unresolved

- **The fork in §4.**
- **A control with regression headroom.** Nothing in the current corpus can fail.
- ⚠ **`fux-lab/corpora/w144-graded` is stale** — three of five families and a
  `fux.toml` the engine refuses. **Regenerated into scratch for this run**, and
  the lab copy is left as it was. It is the same class as W-186 in a second
  corpus family, and **nothing detects it there either**.
