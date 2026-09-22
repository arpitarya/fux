---
type: Analysis
description: "What the set-2-u baseline capture diagnosed, and the specific changes it owes — each with a command that reproduces the symptom. No correctness claim, because no key was read."
run: 2026-09-22-golden-set-2u-rung-01000
item: W-215
filed: 2026-09-22
---

# ANALYSIS — `set-2-u` baseline capture, `rung-01000`

🔴 **Nothing below is a diagnosis of answer quality.** This run read no answer
key, so every cause here is about the **instrument and the hand-off**, and the
one thing that could turn a row into a finding — a score — is Arpit's.

---

## 1 · 🔴 The hand-off has two spellings of one document, and a join will not see it

**Symptom.** 87 of 1 584 citations carry `doc` ending in `#pN` and `lines: ""`,
across **28 of 125 questions** and **30 distinct documents**. `ranked` carries
**0** such entries, so the same row names the same document two ways.

**Cause, and it is not a bug in fux.** `fux answer`'s locator grammar for a
**non-prose decoded** document (`.html`, `.eml`, `.yaml`) is `path#pN` — a
decoded part — where a prose document gets `path:L30-L46`.
`golden_run._cite()` splits on the last `:` and keeps the tail only when it
starts with `L`; for `path#pN` there is no such tail, so the whole locator stays
in `doc` and `lines` is **correctly** left empty rather than invented.

```bash
cd ~/my_programs/fux
python3 - <<'PY'
import json, pathlib
H=[json.loads(l) for l in pathlib.Path(
  "work/regression/2026-09-22-golden-set-2u-rung-01000/evidence/handoff-set-2-u.jsonl"
).read_text().splitlines() if l.strip()]
bad=[(h["id"],c["doc"]) for h in H for c in h["citations"] if not c["lines"]]
print(len(bad), "citations with no line range;", len({i for i,_ in bad}), "questions;",
      len({p for _,p in bad}), "documents")
print(sum(1 for h in H for r in h["ranked"] if "#" in r), "ranked entries carry '#'")
PY
```

**The specific change owed — and it is a decision, not a patch.** Two forms are
available and they are not equivalent:

- **(a) split on `#` as well**, so `doc` is always a document path and `lines`
  carries `p2` or `L30-L46`. A scorer then joins on `doc` with no
  normalisation — and the field `lines` stops meaning *lines*.
- **(b) leave the row and normalise in the scorer.** The hand-off stays a
  verbatim record of what fux emitted, and every consumer strips `#pN` itself.

🔴 **Not chosen here, and deliberately not patched here**, because changing
`_cite()` after the pre-registration froze would change the filed rows, and
because the right answer depends on **what a key lists** — which this session
may not look at. **Put to Arpit with the run.** ⚠ **Until it is decided, a
scorer must strip `#pN` before joining and read `lines: ""` as *whole decoded
part*, never as *no locator*.**

⚠ **This is the FIRST recorded occurrence of this class**, so it is not yet the
two-strikes gate [SR-WORK-SESSION](../../../records/0060_WORK-session.md)
decision 13 would make owed. **If a second run trips it, the gate is a check that
every `citations[].doc` in a hand-off resolves to a path in the rung's manifest.**

## 2 · 🔴 The ladder is now heterogeneous, and nothing detects it

**Symptom.** `rung-01000` carries an index written by `fux 3.0.0-alpha.2` at
`3f824de0`; the other seven rungs still record `3.0.0-alpha.1` at `3c885386`.

**Cause.** The re-ingest rule is **per rung** and this run measured one rung.
`ladder_check.py` compares manifests to each other and to `work/golden/seed/`;
**none of its four checks compares one rung's `engine`/`engine_commit` against
another's**, so a multi-rung run started tomorrow would query two engines'
indexes and every check in the repository would stay green.

```bash
cd ~/my_programs/fux && grep -H "^engine" work/golden/ladder/rung-*.index
# rung-01000 is alpha.2 / 3f824de0; the other seven are alpha.1 / 3c885386
```

**The specific change owed:** `ladder_check.py` gains a fifth check — **every
rung's `.index` records the same `engine` and `engine_commit`, or the ladder is
not one instrument** — reported as a WARN rather than a failure while a
deliberate single-rung re-ingest is legal, and named in any multi-rung
pre-registration. ⚠ **Whether to instead re-ingest the other seven now is
Arpit's**, because it rewrites seven frozen records and every earlier number
filed against them.

## 3 · Two of the five funnel gates are constants on this rung

**Symptom.** `reachable: 1000` on 125 of 125, `placed: 10` on 125 of 125,
`answered: 1` on 125 of 125, `in_window: 20` on 124 and `19` on one.

**Cause, and only one of the two is the engine's.** `placed: 10` is **the
`--top 10` cap** the run itself passed — it would read `5` with the default
`--top`, and it measures the flag. `reachable: 1000` is the engine's, and it says
the first gate discards **nothing** at 1 000 documents: every query reaches every
document.

**The specific change owed:** the funnel's written form says which gates are
caps. A document that prints `1000 → 20 → 10 → 1` as fux's funnel is printing one
engine number, one flag and two constants.

```bash
cd ~/my_programs/fux/../fux-lab/corpora/golden/rung-01000 && \
  <pinned>/fux ask "dock scheduling" --json --why --top 3 | \
  python3 -c "import json,sys; print(json.load(sys.stdin)['derivation']['gates'])"
# `placed` follows --top; `reachable` does not move
```

⚠ **UNRESOLVED: whether `reachable` is ever selective.** It is saturated at 1 000
documents and this run has one rung, so nothing here says what it does at 10 000.
**Stated as unresolved rather than generalised.**

## 4 · This capture's `answerable` column has a known expiry date

**Symptom.** `band: weak` ⇔ `answerable: false` on 125 of 125.

**Cause.** The pinned engine predates **W-214**, which Arpit ruled on 2026-09-22
and a concurrent session was building, uncommitted, while this run executed:
`answerable` returns to `band != none` and `weak` becomes a signal. **After that
lands, the equivalence above is false by construction** and all 24 `weak` rows
become `answerable: true`.

```bash
cd ~/my_programs/fux && git log --oneline -1 -- src/fux/query/confidence.py
grep -n "return self.band" src/fux/query/confidence.py
```

**The specific change owed:** nothing in this directory — the rows are correct
for the engine named on them. **What is owed is that any document citing this
capture's abstention figures says which semantics they are**, which §1 and §4 of
the report do. ⚠ **A later paired run must not use this capture as its baseline
arm across the W-214 boundary**: that is two instruments, not two arms.

## 5 · What this run deliberately did NOT diagnose

- **Whether any answer is right.** No key was read; `tools/golden-score/score.py`
  was not invoked, and starting it is Arpit's hand.
- **Whether `partial` at 47.2 % is high.** There is no second arm and no licensed
  comparison — generation 1 retired and this rung's index was rebuilt.
- **Whether the 11 `ext/`-first and 7 `archive/`-first rank-1 results are
  errors.** Where a document sits is not whether it answers the question.
- **Anything about a rung other than `rung-01000`**, or an engine other than
  `3f824de0`.
