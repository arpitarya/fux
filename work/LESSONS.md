---
type: Log
description: "Dated build lessons — what this project learned the hard way, newest first. A log rather than a record, because a record states what is true now and carries no history; these are the failures that shaped decisions, and the date is part of the lesson."
---

# LESSONS — what this build learned the hard way

**Why this is a log and not a record.** A record states what is true *now* and
**carries no history** ([the register](../records/README.md)); these entries
are dated failures, and the date is part of the lesson. Folded out of
`CLAUDE.md` §Hard-won build knowledge on 2026-09-14 (W-173), which is where
they had accumulated.

**How to use it.** Newest first. A lesson whose remedy is a *rule* belongs in a
record and is named here only as the failure that produced it. A lesson whose
remedy is *judgement* lives here and nowhere else — and it is unenforced by
construction, which is the honest half.

⚠ **Nothing here is normative.** Where an entry and a record disagree, the
record is the rule and this file is the anecdote that motivated it.

---

## 2026-09-21 — the restore is the hazard, not the commit; and an audit loop can lie

**Two halves of one afternoon, and the second is worse than the first.**

🔴 **A `git checkout` on a shared tree is as destructive as a bad commit, and
nothing warns you.** The repo's concurrency discipline is written for *staging*:
re-derive `git status`, commit with explicit pathspecs
([SR-WORK-SESSION](../records/0060_WORK-session.md) decision 10). A session
correctly noticing that a global stamper had touched eleven records it did not
own restored them with `git checkout` — **the right instinct** — and one of those
eleven had, by then, acquired two hundred lines of another session's amendment.
It went, without a message, and the file's line count was identical to `HEAD`
afterwards. **Restore needs the same explicit discipline staging does**: check
the diff of each path you are about to discard, not the reason you believe it
changed.

🔴 **And the audit that should have caught it reported `ok` for every file.**
The check was a shell loop:

```sh
n=$(grep -c "$needle" "$file" || echo 0)
[ "$n" = "0" ] && echo LOST || echo ok
```

`grep -c` prints `0` **and** exits 1 when it finds nothing, so `|| echo 0` fires
too and `$n` is `"0\n0"` — which never equals `"0"`. **Seventeen files, all
reported present, one of them absent.** The remedy is `grep -qF` and a real
`if`, and the lesson is the general one: **a verification step must be able to
fail.** Before trusting an audit loop, feed it a case you know is broken and
watch it say so. An audit that cannot produce a negative is not evidence of a
positive — it is the same shape as a green test that asserts nothing, and it is
harder to see because the output looks like work.

⚠ **Both halves were found by reading `git diff --stat` and disbelieving it**:
a record that should have grown by two hundred lines showed four. **The stat is
the cheap check that catches this class**, and it caught it twice in one day.

---

## 2026-09-21 — a repo-wide stamper is a concurrency hazard, and it is silent

**`scripts/sr-owns.py --write` and `scripts/sr-hash.py --write` take no path
argument.** They walk every record. On a tree another session is editing, that
means a change of yours re-stamps the `owns:` hashes of *their* records to match
*their* in-progress code — **silently satisfying the freshness gate that exists
to force them to touch the record.** It cost eleven records here; they were
restored only because each happened to carry exactly four changed lines, all
frontmatter, and nothing of theirs was mixed in yet. **An hour later the same
records had real body edits and restoring them would have destroyed work.**

**The sequence that works on a shared tree:** stage your paths → stamp → restore
theirs → verify with `git diff --name-only records/`. **The window is small and
it closes.** ⚠ Three earlier concurrency lessons here are all about *commits*;
this is the first where the hazard was a **generator**, which is worse, because a
commit is visible in `git log` and a stamp is four hex characters in a
frontmatter line nobody re-reads.

**The tell that caught it:** `git status` showed 3 untracked paths at session
start and ~45 modified files an hour later. **Re-derive status before every
stamp, not only before every commit.**

---

## 2026-09-21 — a data-shaped threshold can be frozen on a premise nobody measured

**Twice in one day, in opposite directions.** W-205 part 2 was held — and a whole
question set authored — on the premise that `RF-118`-shaped sibling identifiers
fail at `hit@1`. **All eight ranked first in both arms.** W-205 part 1 was
pre-registered on the premise that six front-matter-only identifiers were absent
from the index. **Five were already reachable.**

🔴 **Both premises were generalisations of a correctly recorded SINGLE case**, and
both were wrong for the same mechanical reason: **the analyzer splits**, so a
whole identifier can be absent while enough of its parts are present for the
document to be found anyway. *"The whole identifier is absent"* and *"the document
cannot be found by it"* are different statements.

**What it cost:** a seed-authoring pass, a ladder rebuild and a 5 984-call re-run
for part 2's headroom that was never needed; and a part-1 endpoint that reads as
*six fixed* until you look at the before-arm.

**What would have prevented it:** one probe run, minutes, before the freeze.
[SR-RS](../records/0133_predictions.md) decision 23c already does exactly this for
links — `ref_edge_census.py` **exits 2 when a corpus has none** — and there is no
equivalent for *does this input exercise the defect*. **The rule is that record's
to make and is in the inbox.**

## 2026-09-21 — `sr-owns.py --write` before `git add` stamps a hash that excludes the new file

The owns-hash enumerates a directory from **`git ls-files`**, deliberately, so an
untracked file is not in it. Run `scripts/sr-owns.py --write` while your new
module is still untracked and it stamps a hash of the directory **without** it;
`git add` then makes the file tracked and the gate fires on the next run, naming
a component you thought you had just stamped.

**Order: `git add`, then `sr-owns.py --write && sr-hash.py --write`, then commit.**
It cost two re-stamps in one session and looks exactly like a flaky gate.

## 2026-09-15 — "commit with explicit pathspecs" is not a rule you can follow mechanically

**Second occurrence of a failure class, and a gate now exists** —
[SR-WORK-SESSION](../records/0060_WORK-session.md) decision 13. The first is
§*"a green working tree can hide a red HEAD"* below.

**What happened.** W-177's session ran alongside another that was rebuilding
the golden ladder. It knew this, said so in its first output, listed the
directories it would stay off, and committed with an explicit pathspec — every
part of CLAUDE.md's advice, followed. **It built the pathspec list from
`git status`.** Three of the other session's staged files went into the commit:
an inbox-guard hook, its script, and two work-item files.

🔴 **The rule was followed and the defect happened anyway, which is the whole
lesson.** *"Explicit pathspec"* names a **property of the command**, and the
property was satisfied — the list was typed out, complete, and wrong. **An
explicit pathspec derived from the tree is `git commit -a` with more typing.**
The question a rule has to ask is not *did you name the paths* but **where did
the names come from**, and only one answer is safe: from the change you made,
never from the tree you made it in.

**Nothing broke here**, which is worth saying because it is the reason this
class survives: the swept files were complete, and `OPEN-WORK.md` already
linked two of them, so the commit arguably *fixed* a dangling-link state. The
cost was a commit message that does not describe its own commit — invisible
until somebody bisects.

**The gate** is [`scripts/commit-paths.py`](../scripts/commit-paths.py) with
[`tests/test_commit_paths.py`](../tests/test_commit_paths.py). It refuses in
**both** directions the pathspec is silent about: a dirty path you did not name
(`--leave-behind` is how you say you meant it), and a named path that is not
dirty — cause 2 below, the omitted restamp.

⚠ **It is a tool, not a hook, and one of its tests asserts the hole.** A
pathspec list that names the whole tree still passes it: no mechanism inside a
shared checkout can tell which dirty file belongs to which session. What it
buys is that leaving something behind becomes a decision in the shell history
instead of an accident — and that taking somebody else's file means **typing
its name**.

---

## 2026-09-15 — an emptied Blocked-on-Arpit inbox is one line, not a recap

Cowork emptied the inbox correctly (both rows ruled) but closed the section
with a multi-paragraph prose recap of what had just been decided — restating
rulings that already live in the item files and the worklog. Arpit had flagged
this shape before. [SR-WORK-OPEN-QUEUE](../records/0051_WORK-open-queue.md)
rule 45a already says exactly what belongs there: the table, header only, plus
one `*Empty since YYYY-MM-DD — <why>. <what's next.>*` line. Nothing else.
**The gate already existed** (`tests/test_open_work_is_not_stale.py`,
`tests/test_open_work_rows_are_short.py`); the failure was not reading rule
45a before writing the closing line. Check the record's exact required shape
before improvising a summary, even a well-intentioned one.

---

## 2026-09-15 — a flake fired, and I threw its traceback away with `| tail -3`

🔴 **`tests_e2e/test_maintenance.py::test_post_commit_defers_and_a_detached_runner_drains_the_list`
failed once in a combined run and passed on re-run — and I have nothing to show
for it**, because the command was `uv run pytest -q tests_e2e 2>&1 | tail -3`.
The summary line survived. The traceback did not.

⚠ **This is the SECOND time this exact loss has happened on this test family.**
`_drain`'s own docstring records the first: it returned `False` on the first
unparseable `doctor` call *"and the payload that caused it was discarded, so the
failure said only `assert False`"*. The helper was fixed. **The habit that threw
the output away was not**, and it is mine, not the code's.

**The remedy is judgement and belongs here:** a suite that is being run *because
something intermittent is suspected* is redirected to a file, never piped
through `tail`. `tail` is for a run you expect to pass.

**The remedy took eight minutes and worked on the second try.** Re-run three
times, `--tb=long`, redirected to `e2e-1.txt`/`-2`/`-3`. Run 2 failed and said:

```
fatal: unable to stat '.fux/index/ad.jsonl.tmp': No such file or directory
```

🔴 **Which is the race W-182 had captured in a throwaway repository an hour
earlier** — so the discarded traceback had been the answer all along, and the
only thing between not knowing and knowing was `> file` instead of `| tail`.
Filed and fixed the same day as W-185, with the traceback kept
[as evidence](regression/2026-09-15-runner-race-soak/evidence/e2e-capture.txt).

⚠ **Read the near-miss, not the recovery.** It happened to fire again within
three runs. At 1 in 13 — which is the rate `_drain`'s docstring records for the
last flake in this family — it would not have, and the session would have
written *"an unexplained e2e failure, did not reproduce"* into the worklog while
holding a filed work item that explained it.

---

## 2026-09-15 — a green synthetic arm covering for a dead real one

🔴 **`tools/differential/run.py` — the proof obligation for every ranking
change — has been unable to run on this repository, and nothing said so**, for
as long as a binary file has sat in a listed source directory.
`queryset.py::vocabulary` decodes every walked file as UTF-8; ten files in
`docs/paper/figures/` are not, and the first one raises.

**Why it stayed invisible.** There are two arms and only one of them is in the
suite. `tests/derive/test_differential.py` builds its own synthetic corpora,
passes in a second, and is what a session sees go green. The arm that runs over
a **real** repo is a tool you have to type — so *the differential is green* was
true of the half that could not have caught a corpus-shaped defect, and the
half that could was dead.

**The shape to recognise, because it is not specific to this tool:** a
hermetic test and an end-to-end run of the same thing are not redundant, and
when only the hermetic one is wired into CI, **its greenness is evidence about
the hermetic one alone**. The end-to-end half rots silently, and it rots
precisely on the inputs a synthetic fixture never produces — which is why it
existed.

⚠ **What it cost, concretely.** W-168 step 1's differential evidence — 11 072
byte-for-byte comparisons — had to be gathered through an **ad-hoc copy** of
the harness in a scratch directory. The numbers are real and the comparison is
the harness's own; the provenance is a workaround, and it is written into
[SR-T1-ACCELERATOR](../records/0110_accelerator.md) decision 15b and
W-184 (closed 2026-09-15) rather than left to be
rediscovered.

⚠ **The remedy is a rule and a repair, not judgement**, so it is W-184's: skip
what cannot be decoded, **say how many**, and a test that fails on a binary
file in a source dir. What lives here is the failure that produced it.

## 2026-09-15 — a green working tree hiding a red HEAD

🔴 **CLAUDE.md warns that a red test on an uncommitted tree is invisible to
every mechanism in this repo. This is the inverse, and nothing warns about
it:** a **green working tree can hide a red HEAD**, and `git status` cannot
tell you, because every fix is sitting right there looking like somebody
else's mess.

**What happened.** A session ran all three suites — 4614 / 142 / 36, green —
and reported it. HEAD alone failed **three** different gates:

| gate | why |
|---|---|
| `test_doc_links` | eight links pointing at files that moved |
| `test_doc_registry` | two rows pointing at documents that no longer exist there |
| `test_sr_owns_hash` | a record's `owns:` hash for a component the same session had changed |

**Every one of those was repaired in the working tree** — by another session's
uncommitted files, and by a restamp of my own that an explicit pathspec had
left out of its commit. So the suite passed on a tree nobody would ever clone.

**Three causes, and they are different from each other.** Worth separating,
because only the first is the obvious one:

1. **Two partial sweeps.** `git add X && git commit` takes the **whole index**,
   and on a shared tree the index already holds another session's staged work.
   `git commit -- X` is the form. CLAUDE.md names this exactly, and ten commits
   in that session used it while two did not.
2. **The opposite error, from the same tool.** An explicit pathspec will also
   happily *omit* a file your own change requires — a record's restamp, most
   easily. Pathspecs stop you taking too much and let you commit too little.
3. **An orphan that predated all of it.** A file had been moved in an earlier
   commit without its registry row, and it had been red since. Nobody noticed,
   because the working tree had the row.

**The remedy is judgement and it is one sentence: `git status` describes a
tree, not a commit.** To know whether HEAD is consistent you have to look at
HEAD — `git worktree add --detach <tmp> HEAD` and run the gates there.

⚠ **And that trick has a hole that must be known before it is trusted.** An
editable install points `import fux` at the **main** tree's `src/`, so a run
inside a detached worktree tests HEAD's *documents* and the live tree's *code*:

```
$ cd <worktree> && python -c "import fux; print(fux.__file__)"
/Users/.../fux/src/fux/__init__.py      # the MAIN tree, not this one
```

**So it isolates the docs, records and registry gates reliably, and the
behaviour tests only when `git status -- src/ node/` is empty.** If `src/` is
dirty, the worktree silently tests the wrong code and reports a number that
means nothing. Check that it is clean, or install into the worktree.

⚠ **Why there is no gate for this.** A check that HEAD is green means running
the suite against a commit on every commit, which is CI's job and not a
pre-commit hook's — and CI on a branch nobody has pushed catches it late,
which is exactly when this one was caught. **Stated as judgement, unenforced,
which is the honest half.**

## 2026-09-14 — five items in one session

- 🔴 **Read the evidence, then write the reader.** Three defects in one
  afternoon had one cause: a parser written against a guessed shape. `ARMS.toml`
  is `[[arm]]` — an array of tables, one per arm *per corpus* — and a reader
  that guessed `[A]`/`[B]` sections printed *not filed* in every cell of a file
  that had every value in it. `differed` in a null-control JSON is a **list**,
  and a card read `[] differed`. A `level="warn"` doctor row with `ok=True`
  renders `[OK]`, so a disclosure disclosed nothing. **In all three the code
  ran, produced output, and was wrong** — the only thing that caught them was
  running the thing and reading what came out.
- 🔴 **A gate's flag and a gate's rendering are different contracts, and the
  rendering is the one a person meets.** `tests/test_doctor.py` asserted
  `row.ok` and `row.level == "warn"` — both correct as fields — while the line
  a reader saw said `[OK]` beside *every citation from these will be
  `unverified`*. **Assert the rendered line**, because asserting the fields is
  what let it ship.
- **A pre-registered rule is worth more when it fires against you.**
  `fux inspect`'s headline check, self-retrieval, reads **1.000 on every golden
  rung and 1.000 on forty copies of one runbook**. The rule said a floor that
  cannot separate a healthy corpus from a bad one is dropped to descriptive, so
  it was — and the alternative was a check that reads `ok` on every corpus
  anybody will ever run it on. **A rule only demonstrates it works by costing
  you something.**
- 🔴 **A false provenance claim about a threshold is worse than no claim.** A
  report of mine said its pre-registration was *"committed alone, ahead of the
  first number"*; the commit carried 28 files including the implementation, and
  the file was written after the measurement. **The criterion did predate the
  numbers** — in two named commits — which is the part that was checkable, and
  the correction says so rather than dropping the sentence.
- **A key present on one code path and absent on the other is worse than a key
  on neither.** `answer`'s citation is built from an `AskResult` on one path and
  a refer-plane citation on the other; adding `pinned` to the first would have
  had a consumer read `false` from the second for a question that genuinely was
  pinned. The note went to stderr, before either branch.
- **Truncate a list, and ship its count in the same breath.** A top-20 orphan
  list read `20` and the real number was **341** — and *20* is exactly what a
  cap of 20 looks like.

## 2026-09-12 — two sessions, one machine

- 🔴 **A RED TEST ON AN UNCOMMITTED TREE IS INVISIBLE TO EVERY MECHANISM HERE.**
  CI reads commits; the SR-freshness hook reads a commit message; `pytest` reads
  whatever you choose to run. A test that a working-tree change turns red stays
  red and unseen until somebody commits — **and then it fails for whoever
  committed it.** It bit two sessions on the same day for different reasons.
  The only cover is to run **both suites, whole**, before believing a change is
  done; reading the code and concluding is what failed.
  ⚠ **It recurred on 2026-09-14**: a session left 343 files staged with three
  suite failures on them, and the next session inherited both.
- 🔴 **A loaded machine does not produce noise — it produces a clean, localised
  anomaly that reads like a finding.** One session's corpus build inflated a
  single benchmark tier's ingest ratio to **0.77 against ~0.46 everywhere
  else**: tier-localised, internally consistent, and in exactly the shape a
  real regression takes. **Noise gets distrusted; this would have been filed.**
  Caught by two sessions comparing timestamps — a conversation, not a
  mechanism. Interleaving arms (`A B A B`) is the only structural defence and
  it protects the *difference*, never the absolute number.
- **So: say what you are running, and when, to anyone sharing the machine.** It
  is the only thing that worked. Recorded in
  [SETUP-BENCHMARK](setup/fux-benchmark.md) standing rule 0a as an
  **unguarded** gap, because it is one, and as
  [SR-WORK-SESSION](../records/0060_WORK-session.md) decision 12.
- **Concurrent sessions commit, too.** A peer committed a fix to code this
  session had written and not yet committed. **Re-derive `git status`
  immediately before staging, and commit with explicit pathspecs** —
  `git commit -- <paths>` — when the index carries another session's work.
  ([SR-WORK-SESSION](../records/0060_WORK-session.md) decision 10.)

## 2026-08-09 — M1, the pruning gate

- **A pre-registered threshold is only as good as the corpus that tests it.**
  M1's k=128 arm returned a zero delta on all three eval corpora — and prune
  coverage showed why: their documents' median vocabulary is **32–46 distinct
  terms**, so top-128 was a **no-op for 97 %+ of documents**. **Always report
  the fraction of the population a treatment actually touched**; an aggregate
  delta of zero over an untreated population is not evidence.
  ✅ **This one got an instrument on 2026-09-14**: `fux inspect`'s vocabulary
  percentiles are that fraction, computed for any corpus in one command
  ([SR-INSPECT](../records/0156_inspect.md)).
- **Recompute statistics over the pruned index, never borrow them.** `df`, `n`
  and field lengths must come from the surviving postings, because that is what
  production holds. Borrowing the baseline's statistics makes scores line up and
  measures a system nobody will ship. **Keep a diagnostic arm that *does*
  borrow** — it is how a loss gets attributed to missing postings versus
  shifted statistics.
- **Wrap the archive; never edit it.** The archived `Searcher` exposed a `stats`
  seam, built for the lean profile, that turned out to be exactly the hook the
  diagnostic arm needed. **Look for an existing seam before concluding an
  archived module has to change.**
- **The archived engine's own recorded numbers are a free correctness check.**
  The harness's fixture baseline reproduced the archived lexical eval exactly
  (hit@5 0.952 / MRR 0.833) and orbit's lab number (0.887) — which is what makes
  *"we varied only the index"* a verified fact rather than an intention.

## Earlier — v0.19–0.26, the archived build

**The full set is in git history:** `git show 6473987:CLAUDE.md`.

**Two items still bind, and both are stated in the records that own the code
rather than here:**

| lesson | its home |
|---|---|
| **BM25F means weight-then-saturate ONCE** — never sum per-field BM25 | [SR-RANKING](../records/0111_ranking.md) |
| **No wall-clock output anywhere on the maintenance path** — timestamps derive from `SOURCE_DATE_EPOCH` or source mtime, or the byte-identical guarantee breaks | [SR-LAW-3](../records/0005_LAW-3-deterministic.md) |

They are listed here as the *lessons*; the *rules* are in those two records and
are not restated.
