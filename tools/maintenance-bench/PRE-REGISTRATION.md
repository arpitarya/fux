# Pre-registration — M5's two gates, R5 and R6

**Written before any number was produced by this file's harness.** Metric
definitions, corpus sizes, arm definitions and the pass/fail conditions are
fixed here so they cannot be adjusted in the direction the numbers happen to
point. `git log` on this file is the evidence: it is committed **before** the
run it governs.

If something below turns out to be under-specified once the data exists, the
honest move is to **record the ambiguity and hand the call to Arpit** — not to
redefine the term.

---

## 0. Disclosure — numbers already exist, and that is why this file is strict

On 2026-08-20 the harness in [`run.py`](run.py) was run **before** the hold on
prediction runs was visible on disk. Those numbers are recorded in
[the WORKLOG](../../work/WORKLOG.md) and were **not** filed as a verdict. Two
consequences, both deliberate:

1. **They do not count.** They measured a build without delta ingest
   ([ADR-INGEST](../../docs/adr/0007_ingest.md) decision 1b), which changed
   ingest cost by more than an order of magnitude. The engine they described no
   longer exists.
2. **Whoever writes this file already has an idea where the threshold falls.**
   That is precisely the condition under which a pre-registration is most
   necessary and least trustworthy, so §2's corpus size is fixed by an argument
   that does not mention the data, and the argument is written out in full.

## 1. The questions

**R5** — can a repository keep its committed index in step **automatically**,
on every commit, without the developer noticing the cost?

**R6** — can two people work on one repository at once without the machine
planes conflicting, while their own prose still conflicts exactly as it always
did?

## 2. R5 — the threshold, and the corpus size it is judged at

**Threshold, verbatim from [`work/OPEN-WORK.md`](../../work/OPEN-WORK.md)
§Predictions and from paper §8 (P7): a 20-doc commit re-indexes in < 1 s via
the hook.** It does not move, and it is not restated in looser words below.

The threshold names no corpus size. **It is judged at 100 000 documents**, and
here is the argument, which is made without reference to any measurement:

- **The plan's own scale anchor is 10⁵.** R7 — the next prediction in the same
  table — is *"committed @100k target density"*. A maintenance path judged at a
  corpus size smaller than the one the size model is judged at would be
  measuring a different system than the plan describes.
- **CLAUDE.md's litmus makes 10⁵–10⁶ the design point, not a stretch goal**:
  *"Scale is the default, not the trigger."* The prediction comes from a paper
  whose §5 and §6 are computed at 10⁶ documents throughout.
- **A hook is judged where it is unattended.** The claim is that re-indexing
  can be automatic. On a 200-document repository nobody needed a prediction.

**The population curve is reported alongside, and never blended into the
verdict**: 1 000, 10 000 and 100 000 documents, each with its own row. That is
M1's lesson, already paid for once — *"always report the fraction of the
population a treatment actually touches"* — and it means a failure at 100 000
still yields the useful engineering answer, *the size at which the hook stops
being automatic*.

### 2.1 What is timed

**The wall-clock of `git commit` itself**, on a repository whose
`post-commit` hook was installed by `fux hooks --install`. Not `fux ingest` in
isolation: the prediction says *"via the hook"*, so git's own commit work, the
hook process spawn, the interpreter start, the ingest and the derived build are
all inside the number. A measurement that timed only the library call would be
measuring a thing no user experiences.

### 2.2 The edit that is timed

**Twenty existing documents rewritten**, then one commit. Not twenty additions:
an addition changes the corpus id set, and the prediction says *re-index*, which
is the steady-state case a repository is in almost all of the time. Additions
are reported as a **secondary arm** at the same sizes, unjudged, because they
are the more expensive case and hiding them would flatter the result.

### 2.3 The statistic

**Five commits per corpus size after one warm-up commit that is discarded.**
Judged on the **maximum**, with the median reported beside it. A hook that is
usually fast and occasionally not is a hook that a developer learns to distrust,
so the worst case is the number that decides — the same discipline R3 used.

### 2.4 The verdict rule

| outcome | condition |
|---|---|
| **PASS** | max ≤ 1.000 s at 100 000 documents |
| **FAIL** | max > 1.000 s at 100 000 documents |

There is no ambiguous band on R5: the threshold is a hard inequality on a
continuous quantity, and inventing a tolerance around it would be the looser
restatement the rule forbids. What *is* handed to Arpit rather than adjudicated
is anything the run reveals about the threshold's own construction — for
instance, if the number is dominated by a component the prediction plainly did
not have in mind.

**A FAIL is a shipped result.** [ADR-MAINTENANCE](../../docs/adr/0033_maintenance.md)
veto condition 1 already states what changes: *"`post-commit` is too slow to be
automatic and the hook becomes opt-in or incremental in a way it currently is
not."* Tuning the hook to pass is explicitly forbidden by
[W-61](../../work/open/W-61-maintenance-measurement.md)'s hazard.

## 3. R6 — the three tiers, and the control that makes them mean something

**Threshold, verbatim: machine planes conflict-free, human conflicts
preserved**, via a three-tier merge harness.

Every tier builds a throwaway git repository, wires it with
`fux hooks --install`, branches, edits, ingests on each branch, and runs a real
`git merge`. Nothing is mocked; the driver is invoked by git's own merge
machinery.

| tier | what merges | expected |
|---|---|---|
| **1 · machine, disjoint adds** | both sides add different documents | **no conflict** — the union |
| **2 · machine, one shard, two lines** | two documents that hash into the *same* shard file, one edited on each side | **no conflict** — adjacency is not a disagreement |
| **3 · the same document, both sides** | one document edited differently on each side | **conflict preserved** — the prose conflicts, and the shard is left carrying *both* sides |

**Tier 2 is chosen so the driver has to earn its place.** Two documents in two
different shards touch two different files, and a textual merge would have coped
on its own; the pair is therefore selected at run time by hashing, not by hope.

**Tier 3 is reported as prominently as the other two.** A harness that only
demonstrated *no conflicts* would be demonstrating that the merge driver is
dangerous. Two things are asserted there, not one: git reports the conflict,
**and** the shard file contains ordinary `<<<<<<<`/`>>>>>>>` markers with both
sides' bytes intact — the driver refused, rather than picking.

### 3.1 The control arm

Each tier is **also run with the merge driver unregistered**. Without it, a
tier that passes proves nothing: the driver could be doing nothing at all and
git's own textual merge could be succeeding by luck.

**R6 requires tiers 1 and 2 to conflict in the control arm and merge cleanly in
the treatment arm.** A tier that merges cleanly in *both* is reported as
**uninformative** and does not count toward the pass.

### 3.2 The verdict rule

| outcome | condition |
|---|---|
| **PASS** | all three tiers match their expected column, **and** tiers 1 and 2 are informative per §3.1 |
| **FAIL** | any tier deviates — a machine plane conflicting, or a human conflict silently resolved |
| **INCONCLUSIVE** | every tier matches but neither tier 1 nor tier 2 is informative |

## 4. The instrument

- **Harness:** [`run.py`](run.py) in this directory. Reproduce command in the
  filed report.
- **Engine:** the working tree, by path — **not** the published `0.33.0` wheel,
  which predates the maintenance plane entirely. The commit sha is recorded in
  the report.
- **Surface:** recorded with the number. Latency is not comparable across
  machines (fux-lab TEST-PLAN §2), so a re-run on another surface is a new
  measurement, not a confirmation.
- **Corpus:** synthetic, generated by the harness, seeded and deterministic —
  frontmatter, one `#` title, forty distinct terms and one outbound link per
  document, so extraction and edge resolution both do real work.

## 5. What this run does not measure

- **Not the merge driver's behaviour under `git rerere`, submodules, or
  octopus merges.** Two-parent merges only.
- **Not an add/add shard conflict.** git does not invoke a content merge driver
  when a file is added on both sides with no common ancestor; that limitation is
  recorded in ADR-MAINTENANCE and is out of scope here.
- **Not concurrent *processes*.** One writer at a time is assumed; the
  prediction is about branches, not about two `fux ingest` runs racing.
