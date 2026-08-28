---
type: Analysis
name: BENCH-V1-VS-HEAD-ANALYSIS
title: "What the version benchmark actually found, and what it could never have found"
description: "Three findings: the primary endpoint was saturated before it ran and could not detect anything; the supersession prior works perfectly and ships switched off, which is why B2 failed its predicted PASS; and the generated corpus cannot test an answer layer's honesty. Each with a repro command."
timestamp: 2026-08-28T00:00:00Z
---

# Analysis — `1.0.0` vs `HEAD`

> ⚠ **This run is `informed`** ([`report.md`](report.md) §Authorship). Nothing
> below states a delta as a generalisation. The findings are about **the
> instrument and the shipped defaults**, both of which are facts about the tree
> rather than estimates from a sample.

---

## Finding 1 — the primary endpoint was saturated before it ran

**`hit@5` = 240/240 and MRR@10 = 1.0000 in *both* arms, at *every* tier.**
Rank-1 accuracy is 100 % as well. There was no headroom: the metric could not
have gone up, and B1's `p = 1.0` says the two arms never disagreed, not that
they are equally good.

**Why.** The generator plants each marker in exactly one document. A term with
`df = 1` in a corpus of 10 000 is the easiest retrieval problem BM25 has —
five-field BM25F, a `v2` analyzer and a proximity reranker cannot improve on
"already rank 1", and cannot break it either.

🔴 **The pre-registration's power table answered the wrong question.** It sized
the set so that a 10 %/3 % effect would be detected — correctly, and that work
stands. It never asked whether *the queries could express such an effect*, and
they cannot: `pb` and `pc` are structurally 0 on a marker suite. **A power
calculation says how many queries; it does not say whether the queries are
hard.** That is the lesson, and it is reusable by every paired run this repo
files after this one.

**The improvement.** A discriminating suite needs queries where the right answer
is *contested* — several documents plausibly matching, one correct. The two
suites here that had contested answers, chains and decoys, both produced signal
(50 % inversions; a decoy occasionally reaching the top 5). **Marker queries
should be kept as a null-control instrument and never again used as a primary
quality endpoint.**

```bash
# reproduce the ceiling in one line
python3 -c "import json;rows=[json.loads(l) for l in open('evidence/rows/A-t1000.jsonl')];\
pr=[r for r in rows if r['suite']=='pairs'];print(sum(r['rank']==1 for r in pr),'/',len(pr))"
```

---

## Finding 2 — the supersession prior works, and ships switched off

**B2 failed its predicted PASS, and the reason is not the one the item
predicted.** The item said a failure would mean *"the priors shipped and do not
do the job they were built for."* They do the job. They are disabled by default.

- Both arms invert **identically**: 21/40 at tier 1 000, 17/40 at 10 000,
  5/10 at 100 — a coin flip, which is what a lexically symmetric pair should
  give an engine with no currency signal.
- `superseded_weight` defaults to **`1.0`** and `recency_half_life_days` to
  **`0.0`** ([`src/fux/tune.py`](../../../src/fux/tune.py)), so on shipped
  defaults **both priors are multiplicative no-ops**. Arm B parses
  `supersedes:`, builds the edge, resolves the flag onto the retired document —
  and then multiplies its score by one.
- **Post-hoc, and labelled as such:** the same arm B with
  `[ranking] superseded_weight = 0.5` in `.fux/tune.toml` takes inversions from
  **21/40 to 0/40** — 21 fixed, 0 broken, exact two-sided `p ≈ 1e-6` — while
  marker retrieval is untouched at 240/240. **This is not a version delta and
  carries no pre-registered verdict.**

🔴 **This post-hoc result does NOT say "lower the default", and reading it that
way would be a real error.** [`P-SUPERSEDE`](../2026-08-25-supersession-and-reranker-default/VERDICT.md)
already ruled exactly that change **FAIL** on 2026-08-25, on the playground,
against a frozen ">= 1 fixed / 0 broken" bar: at `0.5` it fixed one query and
**broke two**, and the diagnosis was that **every broken query had the
SUPERSEDED document as its correct answer** — *supersession belongs to the
query's intent, not to the document*, and a per-document multiplier cannot
express that.

**This corpus cannot see that failure mode, by construction.** Every planted
chain query's correct answer is the successor; not one asks for the retired
document. So `0 broken` here is a property of the generator, not a refutation of
P-SUPERSEDE — the two results are consistent, and the older one is the more
informative because its corpus contains the case that breaks.

**So the version-to-version claim is:** `HEAD` gains the *machinery* to rank a
superseded document below its successor and, out of the box, ranks them exactly
as `1.0.0` did. A corpus that declares `supersedes:` gets nothing until somebody
edits a file they have no reason to know exists.

**The improvement, and it is narrower than it first looks.** Changing the
default is the option P-SUPERSEDE already failed. What is left, and what this
run actually supports, is that **a corpus declaring `supersedes:` today gets
nothing and is told nothing** — `fux doctor` could say the prior is disabled,
which is a disclosure rather than a ranking change. The deeper fix is the one
P-SUPERSEDE named: a per-document multiplier cannot express a query-intent
signal. **This analysis makes neither call.**

```bash
cp -R runs/<run>/work/B-t1000 runs/<run>/work/B-t1000tuned
printf '[ranking]\nsuperseded_weight = 0.5\n' > runs/<run>/work/B-t1000tuned/.fux/tune.toml
python3 bin/bench.py quality --run <run> --arm B --tier t1000 --label Btuned --work t1000tuned
python3 bin/bench.py mcnemar --a rows/B-t1000.jsonl --b rows/Btuned-t1000.jsonl \
        --suite chains --key current_first
```

---

## Finding 3 — neither arm declines, and this corpus cannot say much about that

**0 declines out of 20, in both arms, at every tier.** For a query whose term
appears in no document, both engines return three passages.

Arm B is not silent about it — it returns `band: partial`, `coverage: 0.0009`
and `missing: ["zq00000w"]`. **It has the information and does not act on it**,
which matches what the record already says: `doc_coverage` reports and does not
gate.

⚠ **The honest limit, and it is severe.** On a generated corpus *"unanswerable"*
means *no document holds the queried marker* — not *no true answer exists*. The
base documents are word-salad from a closed vocabulary and state no facts at
all, so this instrument can show an answer layer declining when **nothing
matches**. It cannot show one declining when **something matches but does not
support the claim**, which is the failure that matters. B7 as run is a weak
test, and its null should not be read as reassurance.

---

## Finding 4 — the harness bug worth writing down

`fux setup` anchors on the **nearest git root**, not on `cwd`. The first
`prepare` wrote `.fux/`, `.claude/`, `.github/` and `.kiro/` into
`fux-benchmark/` itself and left the corpus without an index — and the *next*
step failed with a `FileNotFoundError` on `.fux/sources/dirs`, which reads like
a broken harness rather than like a working directory in the wrong place. Both
arms do it, so it is not a version difference. Each work directory is now
`git init`-ed, which is also what a real consumer's tree looks like.

---

## What this run may never be used to say

Beyond the pre-registration's own §5: **it may not be used to say the two
engines retrieve equally well.** The primary suite was saturated, so the
observed equality is a property of the queries. The only quality suites that
could have discriminated were the chains — where the arms are equal because a
default is off — and the decoys, where both arms are near-perfect.

## Unresolved

- **Whether `HEAD` improves contested-answer retrieval at all is unmeasured**,
  and no run in `work/regression/` measures it. The suite that would has not
  been built.
- **Whether a `blind` version benchmark is achievable in one session: no.**
  The two-session protocol in `report.md` §Authorship is the only route, and
  nothing in the repo enforces it.
