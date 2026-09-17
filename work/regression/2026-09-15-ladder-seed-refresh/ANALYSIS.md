---
type: Analysis
run: 2026-09-15-ladder-seed-refresh
item: W-136
description: "Why eight frozen rungs could carry a superseded seed while every check in the repo passed, what shipped so it cannot happen a third time, and the two things left for Arpit."
filed: 2026-09-15
---

# ANALYSIS — a ladder that only ever checked itself

## The diagnosis

The golden ladder had **three** things that look like drift detection, and all
three ask the same question in different words:

| mechanism | the question it asks |
|---|---|
| `rungs.verify(documents_too=True)` | does this corpus match **its own manifest**? |
| `tools/differential/ladder_check.py` | do the manifests **agree with each other**? |
| the `.index` stamp + `index_root_sha256` | was this index built from **these bytes**? |

None of them asks *"is the `seed/` half of this rung the seed corpus this
repository has?"* — and a rung's `seed/` is a **copy**, made once at build time
from `work/golden/seed/`. The moment the original moves, the copy is wrong and
every mechanism above goes on agreeing.

On 2026-09-15, seven of the twenty seed documents grew by 131 lines
(`0aa4bbcf`). Every rung had been frozen three days earlier. Both question sets
were then authored **from the new text**. So the benchmark was, at the moment
prompt 4 ran, a set of questions written against sentences no corpus on the
ladder contained.

🔴 **The consequence is the reason L11 exists in the shape it does.** A rung in
that state does not error. It ingests, ranks, answers, and produces a number
that is indistinguishable from a good one — it just quietly cannot find the
paragraph a question is about. That is the same failure mode as a leaked answer
key, arriving from the opposite direction.

**It was found by reading, not by tooling.** Prompt 4 says to verify the rungs;
the only reason the staleness surfaced is that the verification compared the
manifests' `seed/` lines to the live `work/golden/seed/` by hand, which nothing
had ever done.

## The specific changes

**1. `rungs.seed_drift(name)`** — [`tools/differential/rungs.py`](../../../tools/differential/rungs.py).
Hashes the live `work/golden/seed/` and compares it to a rung's manifest:
documents absent, manifest paths no longer in the seed, and documents whose
bytes moved. It reads `work/golden/seed/` and `work/golden/ladder/` and nothing
else — the two directories [L11](../../../records/0012_LAW-11-sealed-answer-key.md)
leaves open.

```bash
./.venv/bin/python -c "import sys; sys.path.insert(0,'tools/differential'); import rungs; print(rungs.seed_drift('rung-10000') or 'clean')"
```

**2. `ladder_check.py` check 4** — [`tools/differential/ladder_check.py`](../../../tools/differential/ladder_check.py).
Prints `STALE` beside a drifted rung and exits non-zero. This is the form that
runs on a machine with no corpus.

```bash
./.venv/bin/python tools/differential/ladder_check.py
```

**3. The gate** — [`tests/test_golden_ladder_seed.py`](../../../tests/test_golden_ladder_seed.py),
one parametrised case per rung, in the **fast** suite. It needs no corpus, so a
clean clone and a CI runner both run it.

```bash
./.venv/bin/python -m pytest -q tests/test_golden_ladder_seed.py
```

**Two strikes, so a gate** — [SR-WORK-SESSION](../../../records/0060_WORK-session.md)
decision 13. Strike one was W-186 on 2026-09-15 (*"Nothing detected it. No test,
hook or CI arm reads a rung"*); this is strike two, same class: **the ladder
drifts and nothing notices**. The check demonstrated itself during the rebuild —
it was green on the six rebuilt rungs and red on `rung-05000` and `rung-10000`
while those two were still building.

**4. The rebuild itself** — [`evidence/rebuild.py`](evidence/rebuild.py), a thin
driver over the **unmodified** 2026-09-12 builder and generator. Not editing
them is the point: `ext/` coming back byte-identical is only evidence if the
thing that produced it did not change.

## What is NOT resolved

- 🔴 **Why the seed was extended at all is not stated anywhere.** `0aa4bbcf`
  committed the extension as one line of a much longer message — *"the golden
  seed extension (131 lines across 7 documents, none containing link syntax)"* —
  as a concurrent session's work swept in on an instruction to commit everything
  staged. There is no work item, no record and no rationale for the change
  itself. **The rebuild takes the current seed as authoritative because the
  question sets were authored from it**, which is the only defensible reading;
  it is not the same as knowing why it moved.
- ⚠ **One claim in `2026-09-15-anchor-mechanism` is imprecise and its conclusion
  survives anyway.** That report says the seed *"carries zero markdown or HTML
  link syntax"*. It carries **three `<a href>` tags**, all in
  `seed/09-dock-scheduling-wiki-export.html` under a heading literally called
  *Stale links*, all pointing at site-absolute paths (`/wiki/kalpa-slot-sync`)
  that resolve to no document in any rung. They were there before the extension
  and are untouched by it, so *"0 anchor-bearing edges of 1 002"* stands — an
  `href` with no corpus target creates no `ref` edge. **The correction is filed
  here rather than applied there**, because a filed report is frozen.
- **The old rungs' numbers are not recoverable.** The corpora were rebuilt in
  place. What is kept is the full pre-rebuild ladder
  ([`evidence/ladder-before-2026-09-12/`](evidence/ladder-before-2026-09-12/)),
  which is enough to identify which corpus an old number belonged to and not
  enough to re-measure on it.

## 🔴 Red tests this session did not cause and deliberately did not fix

Both suites are **red on the working tree, and were red before this session
touched anything** — a baseline was taken by reverting this session's two
`tools/differential/` edits and re-running.

- **unit: 4 failed, 4 769 passed, 6 skipped.** `test_open_work_rows_are_short`
  (W-177's and W-144's rows, 319 and 297 characters — another session's),
  `test_sr_content_hash`, `test_sr_freshness`, `test_sr_owns_hash`.
- **e2e: 7 failed, 135 passed, 1 skipped** — every one of them `fux update`,
  `refresh-urls` or fetch-at-answer, which is another session's **in-flight
  W-177** work deleting the verb.

They are recorded here because [`LESSONS.md`](../../LESSONS.md) is right that a
red test on an uncommitted tree is invisible, and a session that finds one owes
saying so.

⚠ **One of them this session touches, and it is stamped by hand.**
`tests/test_sr_owns_hash.py` lists fifteen components whose owning record's
`owns:` hash is stale; `SR-T1-ACCELERATOR` ([`records/0110_accelerator.md`](../../../records/0110_accelerator.md))
owns `tools/differential`, so this session's two edits there are carried by that
record — a Consequences note recording that the ladder's custody sits in the
harness's directory by accident of location, that **nothing about the
accelerator changed**, and that whether ladder custody deserves a record of its
own is Arpit's.

🔴 **The stamp was written by hand for `tools/differential` alone.**
`scripts/sr-owns.py --write` has no per-record option and stamps all fifteen,
which would **bless another session's uncommitted `src/fux/derive` work inside
this commit** — precisely the partial-sweep failure the 2026-09-15 worklog
records as its own two-strikes class. `src/fux/derive@d97158a8fa5b` is therefore
left at its stale value on purpose. It is theirs to stamp, in the change that
lands the code.

## For Arpit

**1. 🔴 A directory named `work/golden/golden-answers/` exists.**
[L11](../../../records/0012_LAW-11-sealed-answer-key.md) and
[SR-WORK-GOLDEN](../../../records/0066_WORK-golden.md) both say the answer
directory *"was deleted by Arpit on 2026-09-15 and is not a location"*. One
`ls work/golden/` — needed to find `ladder/` — returned that name. **Nothing
was done with it**: not entered, listed, stat'd, hashed or deleted, because
deleting is itself a tool call reaching into it, and SR-WORK-GOLDEN says so
explicitly. **Only Arpit can act on this**, and until he does, every Claude
session that runs `ls work/golden/` learns the same thing.

**2. ⚠ The guards are spelled for the singular name and this one is plural.**
Every entry in `.claude/settings.json` `permissions.deny` matches the path
segment `golden-answer` exactly — `Read(**/golden-answer/**)`,
`Bash(ls:*golden-answer*)` and twenty-odd others. A directory called
`golden-answers` is **not** matched by the `**/golden-answer/**` globs. What
does catch it is `guard-golden-answer.sh`, which greps for the substring and so
matches the plural by luck rather than by design. **Four of the five guards have
a hole the width of one letter**, and the hook is the only one standing in it.
Worth a `W-nn` and a settings fix; not filed here, because a queue row naming
that path is itself a thing every future session reads.
