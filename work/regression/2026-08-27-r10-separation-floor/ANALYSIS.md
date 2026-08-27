---
type: Analysis
title: What R10 found, what it could not, and the two defects it surfaced on the way
description: The verdict is INCONCLUSIVE because two frozen rules disagree. Getting to a number at all required repairing an unreadable committed index, and exposed a URL-path skip message that states a falsehood.
timestamp: 2026-08-27T17:05:00Z
---

# Analysis — R10, the separation floor

## 1 · The pre-registration contradicts itself, and only data could show it

**The finding that matters most is not the curve.** It is that
`PRE-REGISTRATION.md` froze two rules that disagree on the shape the data
actually took: a crossing at `0.3`, a fall-back at `0.4`, then a rise.

- §The measurement's *"and stays at or above it for every higher bin"* selects
  **0.5**.
- §Frozen verdict rules row 4 calls a non-monotone crossing **unreadable, no
  change**.

**Neither is wrong; they were written for different worries** — the first
against picking a single-bin wobble, the second against reading noise at all —
and nobody noticed they overlap until a curve did both things at once.

**The improvement, and it is specific:** a pre-registration that fixes both a
*selection rule* and a *verdict table* must state which one governs when they
disagree. One line — *"row 4 governs; §The measurement applies only once row 4
is satisfied"*, or the reverse — would have made this run decidable.

⚠ **This must not be fixed by editing the frozen document** (W-82 ruling 8).
It belongs in **ADR-RS**, which is where a correction to a frozen
pre-registration lives, and in the *next* pre-registration.
**Repro:** `evidence/render.py evidence/per-query.json`.

## 2 · The playground's committed index was unreadable, and the error said the wrong thing

**Before any measurement could run**, all 50 goldens failed with
`shard missing/mismatched _format header`. The committed index was
`fux.index.v1`; this engine writes `fux.index.v2`.

- **There is no migrate verb**, so the only path is deleting `.fux/index/` and
  re-ingesting — which is safe, because the index holds statistics and never
  content, and **the message did not say any of that.**
- ⚠ **It was the least informative of the three header checks and it guards the
  likeliest case.** The analyzer and `tf_fields` checks beside it in
  `store/reader.py` both name found-and-expected. The `_format` one — the one an
  **engine upgrade** trips — named neither, so it reads as corruption.
- **Fixed**, and split in two: a *version skew* now names both versions and the
  way out; a *missing* header says the file is not a shard, because telling
  someone to re-ingest over what may be a truncated write is worse than saying
  nothing. Gated by two tests in `tests/store/test_writer_reader.py`.
- **Repro:** write a shard whose first line is `{"_format":"fux.index.v1"}` and
  read it.

## 3 · A URL skip reported "no decoder" for a decoder that ran

Found in the fux-lab daemon environment, filed with
[the daemon run](../2026-08-27-daemon-real-url/report.md), and repeated here
because it is the same class as §2: **an error message that sends the reader
somewhere there is nothing to find.**

`https://httpbin.org/uuid` was skipped as `no decoder for application/json`
while `jsondoc` is built in, claims `.json`, ran, and correctly dropped a bare
UUID — leaving nothing. `decode.reason()` has always drawn that distinction and
its docstring says conflating the two *"would make the queue useless"*; the
**file** path used it and the **URL** path did not.

Fixed, with a second defect found alongside: `decode()` was called **without
`root`**, so a consumer-owned decoder in `.fux/decoders/` never applied to URL
content — ADR-DECODE's premise stopping exactly at the network boundary.

## 4 · What the curve does and does not say

**It does say the signal orders correctness in the large.** `P(correct)` runs
0.44 → 0.45 → 0.50 in the three most populated bins and reaches 1.00 in the
sparse upper ones. `separation` is not noise.

**It cannot locate a boundary.** Six queries sit at or above `0.5`; the bin that
first reaches `t` holds four, where one query flipping moves it to `0.50` or
`1.00`; the top two bins are empty. The pre-registration conceded ±0.2 and the
top of this range is worse.

⚠ **`separation == 1.0` never occurred (n = 0).** The frozen special case did
not fire — no query on this corpus produced exactly one scoring document. That
is a fact about a 10-document corpus, not about the signal, and it is one more
reason nothing here generalises.

## 5 · Unresolved, and stated as unresolved

- **Whether the floor is `0.5`.** Arpit's call; see `VERDICT.md`. No session may
  take it.
- **Whether `separation` can carry a calibrated probability at all.** The
  pre-registration refused to fit one on 50 queries and that refusal stands —
  a calibration needs its own pre-registration and a sample that supports it.
- **Nine goldens have no `known_failure` annotation.** `check.py` supports the
  marker and the playground README documents *"41 pass · 9 xfail"*, but no
  golden carries one, so a full run reports `FAIL — 9 of 50`. **Annotating them
  would turn a red gate green**, which is a judgement about what the suite
  should assert and is not an agent's to make. Named, not done.
