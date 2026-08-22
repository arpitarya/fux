# Pre-registration v2 — R6, with a tier 1 that can be informative

**Written before any number was produced by the re-specified harness.** Tier
definitions, the control arm, the informativeness test and the verdict rule are
fixed here so they cannot be adjusted in the direction the numbers happen to
point.

**This file supersedes nothing.** [`PRE-REGISTRATION.md`](PRE-REGISTRATION.md)
§3 governed the 2026-08-20 run and still does; that run's verdict
([R6-MERGE](../../work/regression/2026-08-20-r6-merge-driver/VERDICT.md)) stands
exactly as filed. This is a **new instrument for a new run**, in the same
relationship `PRE-REGISTRATION-v2.md` has to `PRE-REGISTRATION.md` in
`tools/pruning-eval/`.

---

## 0. Disclosure — this is written by someone who knows a great deal

The rule is that a pre-registration is written before the numbers. That is only
partly true here, and pretending otherwise would be worse than saying it:

1. **R6 already ran, on 2026-08-20, and returned INCONCLUSIVE.** All three
   tiers matched; tier 2 was informative; **tier 1 was not** — it merged
   cleanly with the driver removed, so it proved nothing.
2. **The result fitted no row of the frozen verdict table.** §3.1 said an
   uninformative tier "does not count toward the pass"; §3.2's PASS row
   required tiers 1 *and* 2 informative and its INCONCLUSIVE row required
   *neither* to be. All-match-with-one-informative is in neither.
   **Arpit ruled §3.1 governs**, and
   [ADR-MERGE-DRIVER](../../docs/adr/0034_merge-driver.md) was accepted on that
   reading rather than on a clean pass.
3. **A post-hoc arm already exists and already answered the question.**
   `run.py`'s `tier1b` — disjoint adds selected by hashing into one shard — was
   added *after* seeing tier 1's failure, is labelled post-hoc in its own
   docstring, and sits outside the verdict. **It tells us how to re-specify
   tier 1. It is not evidence, and this file does not treat it as any.**

So: whoever writes this file has a strong prior about what the re-specified
tier 1 will do. That is the condition under which a pre-registration is most
necessary and least trustworthy, and the mitigations are these:

- **The threshold is copied verbatim** (§2) and is not restated in looser words
  anywhere below.
- **Tier 1's re-specification is not invented here.** It is `tier1b`'s existing
  definition, promoted from post-hoc arm to judged tier. That definition is in
  git history from before this session, so *what* is being measured is
  checkable independently of anyone's word.
- **The verdict table's new row hands its case to Arpit rather than resolving
  it** (§3.2). The runner gains nothing by writing it one way or the other,
  which is the point.

### 0.1 A weaker evidence chain than the original had, stated plainly

`PRE-REGISTRATION.md` could say *"`git log` on this file is the evidence: it is
committed **before** the run it governs."* **This file cannot say that.** It was
written in a working tree with a large uncommitted change set that a concurrent
session also holds, so committing it alone was not available, and the run below
was produced from that same tree.

What survives as evidence: the tier definitions are promoted verbatim from code
that was already committed, and the engine sha in the report is recorded as
`+dirty`. **A reader who wants the strong form of this guarantee should treat
this run as weaker than the 2026-08-20 one on exactly this axis**, and that is
recorded here rather than discovered later.

## 1. The question

**R6** — can two people work on one repository at once without the machine
planes conflicting, while their own prose still conflicts exactly as it always
did?

Unchanged. This run does not re-ask it; it asks it with an instrument whose
tier 1 can produce an answer.

## 2. The threshold — verbatim, and not restated

**Machine planes conflict-free, human conflicts preserved**, via a three-tier
merge harness.

That is the whole threshold. It is the same string as
[`PRE-REGISTRATION.md`](PRE-REGISTRATION.md) §3, character for character, and
nothing below reworded it.

## 3. The tiers

Every tier builds a throwaway git repository, wires it with
`fux hooks --install`, branches, edits, ingests on each branch, and runs a real
`git merge`. Nothing is mocked; the driver is invoked by git's own merge
machinery.

| tier | what merges | expected |
|---|---|---|
| **1 · machine, disjoint adds into one shard** | both sides add a different document, and the pair is **selected at run time by hashing so both land in the same shard file** | **no conflict** — the union |
| **2 · machine, one shard, two lines** | two existing documents that hash into the *same* shard file, one edited on each side | **no conflict** — adjacency is not a disagreement |
| **3 · the same document, both sides** | one document edited differently on each side | **conflict preserved** — the prose conflicts, and the shard is left carrying *both* sides |

**What changed, and why it is a re-specification rather than a new tier.** Tier
1 previously said only "both sides add different documents". Two documents
added on two branches usually hash into two *different* shard files, and git's
ordinary textual merge copes with two different files without any help — so the
tier could pass while proving nothing about the driver. The scenario it meant to
test is *"two people add documents at the same time"*; pinning the pair into one
shard is what makes that scenario actually exercise the machinery. **Tier 2 was
already selected this way**, by hashing at run time rather than by hope, and its
own justification in the frozen file applies here word for word.

**The original tier 1 is still run, and reported, and unjudged.** It is the
everyday case — most concurrent adds really do land in different shards — and
the fact that it needs no driver is a true and useful finding. Dropping it
because it was uninformative would be deleting a result. It appears in the
report as `1-disjoint (unjudged)`.

### 3.1 The control arm

Each tier is **also run with the merge driver unregistered**. Without it, a tier
that passes proves nothing: the driver could be doing nothing at all and git's
own textual merge could be succeeding by luck.

**A tier is *informative* when the control arm does not come out the way the
treatment arm did** — for the two clean tiers, that means the control conflicts
in the machine plane. **A tier that merges cleanly in both arms is
uninformative and does not count toward the pass.**

Tier 3 claims no informativeness: a genuine disagreement conflicts in both arms
by design, and that is the point rather than a weakness.

### 3.2 The verdict rule — with the case that fell through

| outcome | condition | action |
|---|---|---|
| **PASS** | all three tiers match their expected column, **and** tiers 1 and 2 are both informative per §3.1 | [ADR-MERGE-DRIVER](../../docs/adr/0034_merge-driver.md) veto 2 is satisfied on a clean pass |
| **FAIL** | any tier deviates from its expected column — a machine plane conflicting, or a human conflict silently resolved | ADR-MERGE-DRIVER returns to `proposed` (its veto 5) |
| **PARTIAL** | all three tiers match, and **exactly one** of tiers 1 and 2 is informative | **Reported and handed to Arpit. The runner does not adjudicate it.** |
| **INCONCLUSIVE** | all three tiers match, and **neither** tier 1 nor tier 2 is informative | the instrument, not the engine, is what failed; nothing is ruled |

**The `PARTIAL` row is the repair**, and it is written to resolve nothing on
purpose. The 2026-08-20 result landed exactly there and had nowhere to go;
under this table it has a name, and the name routes it to a human, which is
what CLAUDE.md already required of any result between clearly-passing and
clearly-failing. A row that instead declared partial informativeness a PASS
would be this session deciding — after seeing the 2026-08-20 result — the very
question Arpit was asked to rule on.

**Expected, and stated in advance so it cannot be claimed afterwards as
insight:** with tier 1 hash-selected, both clean tiers should be informative
and this run should land on `PASS` or `FAIL`, not `PARTIAL`. If it lands on
`PARTIAL` anyway, that is a finding about the harness and is Arpit's.

## 4. The instrument

- **Harness:** [`run.py`](run.py) in this directory, `--only r6`. Reproduce
  command in the filed report.
- **Engine:** the working tree, by path. The commit sha is recorded in the
  report, with `+dirty` where the tree is not clean — see §0.1.
- **Surface:** recorded with the number. R6 is a pass/fail on merge behaviour
  rather than a latency measurement, so it is far less surface-sensitive than
  R5 — but the surface is recorded anyway, because a merge driver is exactly
  the kind of thing that behaves differently under another git version.
- **Corpus:** synthetic, generated by the harness, seeded and deterministic —
  100 documents, frontmatter, one `#` title, forty distinct terms and one
  outbound link each, so extraction and edge resolution both do real work.

## 5. What this run does not measure

Unchanged from [`PRE-REGISTRATION.md`](PRE-REGISTRATION.md) §5, and repeated
here so this file stands alone:

- **Not the merge driver's behaviour under `git rerere`, submodules, or octopus
  merges.** Two-parent merges only.
- **Not an add/add shard conflict.** git does not invoke a content merge driver
  when a file is added on both sides with no common ancestor; that limitation is
  recorded in ADR-MERGE-DRIVER and is out of scope here.
- **Not concurrent *processes*.** One writer at a time is assumed; the
  prediction is about branches, not about two `fux ingest` runs racing.
  ⚠ **This exclusion is worth re-reading now that W-66 has shipped a background
  runner**, which makes two concurrent `fux ingest` processes a thing that can
  actually happen. That is the single-writer lock's problem, not the merge
  driver's, and it is asserted in `tests/maintain/test_runner.py` rather than
  here — but the boundary between the two is thinner than it was when this
  exclusion was first written.

## 6. Declared limitations (stated before the result, not after)

- **The evidence chain is weaker than the original run's** (§0.1): this file was
  not committed before the run, because the tree it was written in could not be
  committed alone.
- **The prior is strong** (§0): the post-hoc `tier1b` already indicated what a
  hash-selected tier 1 does. This run converts that indication into a
  pre-registered result; it does not discover it.
- **One surface, one git version.** A merge driver's behaviour is a function of
  git's merge machinery, and this run exercises exactly one build of it.
