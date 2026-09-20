---
type: Analysis
run: 2026-09-20-golden-ladder-outputs
item: W-204
description: "What follows from phase A's surface claims — a defect in a filed run's stated ranker, a confidence band with an inert middle, and an authorship gap that widens with corpus size. No correctness, and nothing ruled."
filed: 2026-09-20
---

# ANALYSIS — W-204 phase A

🔴 **Surface claims only.** Nothing here says whether an answer was right, and
nothing here rules on a threshold. Each item names a **specific** next action
and a command that reproduces the observation; where the cause is unresolved it
says so rather than choosing a plausible one.

---

## 1 · A filed run states a `b` its corpus contradicts — **Arpit's, not this session's**

**What was observed.** The eight rung directories' `.fux/tune.toml` files each
carry `b = 0.75`, written by `fux setup` on 2026-09-12, at one commit
(`630fd3b`) in each rung's own git history, with a filesystem mtime of
`Sep 15 23:07` and **no modification between then and today**.

**Why that is a problem.** The
[2026-09-16 `rung-00100` run](../2026-09-16-golden-rung-00100/report.md) states,
in **both** its frozen pre-registration and its report, that it ranked at
`b = 0.15`:

> 🔴 **`[bm25f] b` changed from `0.75` to `0.15` earlier today** … **it moves
> every score and every ranked order here.**

Three facts sit against that sentence:

- the rung's own `tune.toml` held `0.75` before that run and holds it now,
- `.fux/tune.toml` overrides the engine default, which is what
  [SR-TUNE](../../../records/0130_tuning.md) is for, and
- [prompt 5](../../golden/prompts/5-claude-run.md)'s command line carries no
  `--no-tune`, the only flag that would have bypassed it.

**So that run most likely ranked at `0.75` under a report that says `0.15`.**

🔴 **Unresolved, deliberately.** This is a *most likely*, not a demonstration.
It could be disproved by evidence this session cannot reach — an ad-hoc edit
reverted afterwards, or an invocation not recorded in the report. **Proving it
would need the 2026-09-16 engine and that rung's v3 index**, and the v3 index no
longer exists: this run's own re-ingest overwrote it, which is itself a reason
the check must happen on Arpit's judgement rather than by a session quietly
re-running something.

**What was NOT done, and why.** The 2026-09-16 report and pre-registration were
**not edited**. A filed measurement is frozen
([SR-RS](../../../records/0133_predictions.md) decision 10b and the per-run
contract's *"corrections noted, not silently applied"*), and a session that
repairs a report about its own predecessor's ranker is doing the thing the
freeze exists to prevent.

**The specific next action — Arpit's.** Decide which of these the 2026-09-16 run
is, and record it *beside* that run rather than inside it:

| | if it ranked at `0.75` | if it ranked at `0.15` |
|---|---|---|
| the run's numbers | stand, under a corrected `b` | stand as filed |
| its report's `b` sentence | is wrong and needs a note filed beside it | is right |
| its scored half (the L11-breach scoring) | was scored against a ranker nobody has since run | unchanged |

**Reproduce the observation:**

```bash
cd ~/my_programs/fux-lab/corpora/golden/rung-00100
git log --format='%h %ad %s' --date=short -- .fux/tune.toml
git show 630fd3b:.fux/tune.toml | grep '^b '
```

**The generalisable half is already fixed.** This run's pre-registration writes
the effective `b` down **and** says where it came from, and §4 of it records the
fork rather than leaving the value to be inferred from a default. ⚠ **That is
not a gate.** Nothing mechanically checks that a golden run's declared `b`
matches the `tune.toml` it ran against, and this is the **first** recorded
occurrence of that failure class — under
[SR-WORK-SESSION](../../../records/0060_WORK-session.md) decision 13 a gate is
owed on the **second**, and naming it here is what makes the second countable.

---

## 2 · The confidence band's middle is inert to corpus size

**What was observed.** From `rung-00100` upward — 100 to 10 000 documents, a
100× growth — **every** band transition is `grounded ↔ weak`: 22 one way, 21 the
other, **43 of 43**. The `partial` set is byte-identical at all seven of those
rungs: the same 37 questions in set 1, the same 40 in set 2.

`partial` lost members exactly once, on the single step from 20 to 100 documents
(17 → `grounded`, 9 → `weak`), and **gained a member at no point in the ladder.**

**Why it matters.** The three bands read as a scale — more support, less support
— but on this corpus the middle one behaves like a **separate, static
classification** that the other two exchange members around rather than through.
Combined with finding 1 of the report (`weak` ⇔ `answerable: false`, 3 984 of
3 984), the operative behaviour is **binary**: `grounded + partial` are
answerable, `weak` is not, and `partial` carries no signal that responds to how
much corpus there is to be confident about.

**What this does NOT establish.** Whether that is a defect or the design.
[SR-CONFIDENCE](../../../records/0141_confidence.md) owns the band, and it may
be that `partial` is meant to key off something corpus size cannot move. **A
run that files no key cannot tell a well-behaved invariant from a dead branch**,
and this one does not try.

**The specific next action.** A question for SR-CONFIDENCE's owner, answerable
without a key: *what input can move a question into `partial`?* If the answer is
*"the first ingest and nothing after"*, then the band is documented as it
behaves. If it is *"coverage and separation, which both move with corpus size"*,
then 43-of-43 is a finding against the implementation and wants its own item.

**Reproduce:**

```bash
python - <<'PY'
import json, collections
from pathlib import Path
B = Path("work/regression/2026-09-20-golden-ladder-outputs/evidence")
R = ["rung-seed","rung-00100","rung-00200","rung-00500",
     "rung-01000","rung-02000","rung-05000","rung-10000"]
t = collections.Counter()
for n in (1, 2):
    prev = None
    for i, r in enumerate(R):
        b = {json.loads(l)["id"]: json.loads(l)["band"]
             for l in (B/r/f"handoff-set-{n}.jsonl").read_text().splitlines() if l.strip()}
        if prev and i >= 2:
            t.update((prev[k], b[k]) for k in b if b[k] != prev[k])
        prev = b
print(t)   # -> only ('grounded','weak') and ('weak','grounded')
PY
```

---

## 3 · The authorship gap is present at every rung and widens with corpus size

**What was observed.** Set 2 is declared unanswerable more often than set 1 at
**every one of the eight rungs**, by 7.7 to 17.1 percentage points. The gap is
narrowest at `rung-seed` (21.8 % against 13.6 %) and widest at `rung-10000`
(35.5 % against 19.2 %) — set 1 flattens at 19.2 % from 2 000 documents up while
set 2 keeps climbing.

**Why it matters.** This is the measurement two authors were commissioned to
produce, and it is now visible across the whole ladder rather than at one point.
**It reproduces the 2026-09-16 run's finding 1** at a different `b`, a different
index format and a different engine — which is worth more than the original
observation, because it rules out the three things that changed in between.

🔴 **It is not a claim that either set is better, harder or more correct.**
Nothing was scored. Two readings survive this evidence and **only a key
separates them**:

- set 2 contains more genuinely unanswerable questions, and the gate is
  **working** — increasingly well as the corpus grows; or
- set 2's phrasing is harder for this retriever, and the gate is **discarding
  answerable questions** — increasingly many as the corpus grows.

The 2026-09-16 scored half pointed at the second (declined-but-answerable
outnumbering correct abstentions by 11–12×), but **that scoring was an L11
breach and none of its numbers may be cited**
([W-196](../../../archive/open/W-196-l11-breach-2026-09-17.md)), so it grounds
nothing here.

**The specific next action.** W-204 phase D, per rung, per set: split the
`answerable: false` rows into `abstain_correct` and `abstain_wrong` against the
key. **The rows exist** — `evidence/<rung>/handoff-set-N.jsonl` — so this costs
a join and no re-run. 🔴 **Whichever way it lands, it lands per set**; pooling
the two erases the gap that is the point.

---

## 4 · What this run leaves unmeasured, stated rather than implied

- **Everything about correctness.** No `hit@k`, no `recall@k`, no difficulty
  band, no answer verdict. W-204 phase D.
- **Any comparison with an earlier golden run.** The engine, the index format
  and the ranker all moved; see §1 for why the nearest candidate baseline is
  itself in doubt.
- **The Node reader.** One reader, Python, one arm.
- **Latency as a benchmark.** Descriptive only — no arms, nothing interleaved,
  a shared machine.
- **The `ext/` filler's effect on ranking.** The ladder grows by adding
  generated documents; how many of the 43 band transitions are the seed corpus
  responding to real competition and how many are filler artefacts is
  **unresolved**, and the honest instrument for it is
  [W-191](../../../archive/open/W-191-the-ladder-carries-no-links.md)'s
  successor — link-bearing seed documents — not a re-reading of these rows.

## 5 · One process defect, for the record

⚠ **The step-1 archive move broke a frozen verdict's pointer and nothing in the
prescribed test list caught it.** `2026-08-27-p3-sha-stability/VERDICT.md` names
`work/open/W-87-what-good-means.md`, which W-204 absorbed and archived the same
day; `tests/test_regression_runs.py` catches it and was not among the five tests
the session was told to run. Repaired the way that test prescribes — the
pre-registration is **mirrored** into the run at its nearest committed state,
the verdict itself untouched, and §P3's `≥ 80 %` threshold is byte-identical in
both versions. **The lesson is about the test list, not the move**: closing an
item can invalidate a frozen artifact three directories away, and only the full
suite sees it.
