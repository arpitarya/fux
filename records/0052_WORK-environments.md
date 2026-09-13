---
type: Standing Record
kind: process
name: SR-WORK-ENVIRONMENTS
title: "SR-WORK-ENVIRONMENTS (0052) — each sibling environment has one job"
description: "Which of the three sibling directories may do what. The playground is Arpit's hands only; the lab runs every measurement on golden test data up to 10 000 documents; the benchmark compares two fux versions on its own corpora, capturing what SR-WORK-BENCHMARK says it captures. Why the three were separated, what it voids, and what would reopen it."
status: accepted
amended: 2026-09-13
date: 2026-09-11
feature: which sibling environment may do what — the playground, the lab and the benchmark, and the rule that keeps them apart
owns: [tests/test_work_environments.py@3ed28dd3934f]
laws: []
timestamp: 2026-09-11T00:00:00Z
content_sha: de9f9c6f9b3dcb1169ccaf273090c32efd444f556620b8d2fd9e83431bd79d03
---

# SR-WORK-ENVIRONMENTS — each sibling environment has one job

## §1 — For humans

> **This record is the HOME of the environment rule — §2's first block IS the
> rule**, and the rest of this record is its rationale: why it exists, what it
> costs and voids, and what would reopen it. **No copy exists anywhere else**;
> every other artifact references this record.
> ⚠ **This was law L9 until 2026-09-13** (Arpit). It is a WORK record now —
> which environment may do what is how work is done, not what the engine
> guarantees — and **the handle `L9` is retired and never reused.**

**The one-line case.** Three sibling directories — `fux-playground`,
`fux-lab`, `fux-benchmark` — had drifted into doing each other's jobs. The
playground, which Arpit keeps for trying things by hand, had become the corpus
every measurement graded against; the benchmark was going to host the lab's
test data. **An environment with two jobs serves neither**: a hand-edit to try
something silently moves a number, and a number nobody can reproduce gets cited.

**The handle:** *Each sibling environment has one job* — the one-line form from
[SR-LAWS](0001_LAWS.md)'s table. ⚠ **A handle is not the law**; read the law at
its home.

| environment | its one job | its data | who touches it |
|---|---|---|---|
| `fux-playground` | Arpit trying things by hand | whatever he puts there | **Arpit only** |
| `fux-lab` | every measurement and evaluation run | the golden test data, ≤ 10 000 documents | agents and Arpit |
| `fux-benchmark` | comparing two fux versions — the captures are [SR-WORK-BENCHMARK](0053_WORK-benchmark.md) | its own 100 → 10 000-document corpora | agents and Arpit |

**Arpit, 2026-09-11, ruling:** *"Fux playground should never be used for
testing. It is only and only for my usage… Fux Lab should be used for all kinds
of testing… use golden test data, only ten k… Fux benchmark should do only
benchmark testing… and benchmark should always use two fux versions, the
previous major version and the latest version."*

**Diagram — Mermaid and its ASCII twin. Update both, always, together.**

```mermaid
flowchart LR
    A["Arpit's hands"] --> P["fux-playground<br/>(no agent, no test, no number)"]
    G["work/golden<br/>(golden test data, key sealed)"] --> L["fux-lab<br/>(every measurement, ≤10k docs)"]
    C["benchmark corpora<br/>(100 … 10 000 docs)"] --> B["fux-benchmark<br/>(current build vs previous major,<br/>captures per SR-WORK-BENCHMARK)"]
    L --> R["work/regression<br/>(filed evidence)"]
    B --> R
```

<details>
<summary><b>ASCII twin</b> — the same diagram, for terminals, diffs, and any reader without a Mermaid renderer</summary>

```text
  Arpit's hands ---------------> fux-playground   (no agent, no test, no number)

  work/golden (sealed key) ----> fux-lab          (every measurement, <=10k docs) --+
                                                                                   +--> work/regression
  benchmark corpora -----------> fux-benchmark    (current build vs prev major;   --+
   (100 ... 10 000 docs)                           captures: SR-WORK-BENCHMARK)
```

</details>

---

## §2 — For agents

### The rule (normative)

🔴 **This block IS the rule**, and it is the only statement of it. Nothing is
generated from it and no other file carries a copy — amend it here.

**Each sibling environment has one job** (Arpit, 2026-09-11).
- **`fux-playground` is Arpit's alone**, for trying things by hand. No agent,
    script, test, measurement or benchmark ever reads, ingests, grades against,
    copies or files a number from it.
- **`fux-lab` runs every measurement and evaluation**, on the **golden test data
    only** (`work/golden/`), **at most 10 000 documents**. fux's own `tests/` and
    `tests_e2e/` keep their built-in fixtures.
- **`fux-benchmark` runs benchmarks only**, always across **two fux versions** —
    the current build and the newest release of the previous major. **What a run
    captures is [SR-WORK-BENCHMARK](0053_WORK-benchmark.md)** and is not restated
    here. Its corpora are folders of **100, 200, 500, 1 000, 2 000, 5 000 and
    10 000** documents; each document about **1 000 lines**, lines up to about
    **300 characters**, with tables, charts, bullet points and Mermaid diagrams,
    written to read as machine-made or by several authors, professional or
    amateur.

### Context

The three siblings were set up at different times for different reasons —
[SETUP-PLAYGROUND](../work/setup/fux-playground.md) *grades*,
[SETUP-LAB](../work/setup/fux-lab.md) *measures*,
[SETUP-BENCHMARK](../work/setup/fux-benchmark.md) *compares* — and nothing
stopped one borrowing another's corpus. By 2026-09-11 the playground's 50
hand-graded goldens were the instrument for the four ranking priors, W-97's veto
leg, W-87 Part B's proposed retarget and every blind annotation run, while the
playground's working tree was also where Arpit tried things by hand — the same
tree whose template overwrite had left it indexing nothing for weeks. The W-136
golden ladder had just been placed inside `fux-benchmark`.

### Decision

**1. `fux-playground` is Arpit's alone.** No agent, script, test suite,
measurement or benchmark reads, ingests, grades against, copies or files a
number from it. Arpit may do anything in it by hand.

**2. `fux-lab` runs every measurement and evaluation.** Its data is the golden
test data ([`work/golden/`](../work/golden/README.md), W-136) and nothing
else, at **at most 10 000 documents**. **Scope (Arpit, 2026-09-11):** this binds
measurement and evaluation runs — anything filed under `work/regression/`. fux's
own `tests/` and `tests_e2e/` keep their built-in fixtures; they test code, not
quality.

**3. `fux-benchmark` runs benchmarks only** — a version-to-version comparison,
never an adjudication. **It captures quality among other things**
([SR-WORK-BENCHMARK](0053_WORK-benchmark.md), Arpit 2026-09-13); what it does
not do is *rule* on what it captured. A pre-registered bar and its verdict are
the lab's, under [SR-RS](0133_predictions.md).

- **What it captures:** the seven captures of
  [SR-WORK-BENCHMARK](0053_WORK-benchmark.md) — ranked lists, what moved,
  `hit@k`, the answer layer, index size, speed, and an HTML report. **That
  record is the only statement of them.**
- **Always two fux versions:** the **current build** and the **newest release of
  the previous major** (Arpit, 2026-09-11). Today: `2.0.0-alpha.x` against the
  newest `1.x`.
- **Corpora:** one folder each for **100, 200, 500, 1 000, 2 000, 5 000 and
  10 000** documents.
- **Each document:** about **1 000 lines**, lines up to about **300 characters**
  wide (Arpit: *"300 chars wide"*), containing **tables, charts, bullet points
  and Mermaid diagrams**; some read as machine-written, others as written by
  several people, professional or amateur.
- **Queries:** a fixed, versioned set per corpus, with a **planted key** the
  generator emits — needed by `hit@k` and by the unanswerables
  ([SR-WORK-BENCHMARK](0053_WORK-benchmark.md) decision 3). ⚠ **Planted is not
  sealed:** the sealed golden answer key is the lab's
  ([`work/golden/`](../work/golden/README.md)) and never moves into a benchmark
  corpus.

**4. Forward only.** Runs already filed against the playground **stand exactly
as measured** and are not re-graded; a law is not a re-judgement. What is void
(per [L0](0002_LAW-0-authority.md)) is every **plan** that would use the
playground from here on — reconciled by
[W-138](../archive/open/W-138-reconcile-with-l9.md).

**5. A benchmark's retained ranked list is measurement evidence, not a use
record.** Its queries are a versioned synthetic set, not a record of anyone
going looking; [L8](0010_LAW-8-use-record.md) is not engaged.

**6. This is a WORK record, not a law, and the handle `L9` is retired**
(Arpit, 2026-09-13). Which environment may do what is **how work is done** —
process — not a guarantee the engine makes to a consumer, which is what a law
is. The record moved from `0011` in the Law range to `0052` in the WORK range
and changed `kind: law` → `kind: process`; it now **owns its enforcing test**,
`tests/test_work_environments.py`, which is what that kind means.
⚠ **`L9` is retired and never reused.** The law handles are `L0`–`L8` and `L10`,
with a deliberate gap — renumbering `L10` down would silently change the meaning
of every citation ever written, which is the failure the retired prediction ids
`R7`/`R8` already taught. **The file number is a different thing and did move**:
`SR-LAW-10` took `0011` the same day, because a number is an ordinal and nothing
identifies a record by one.
⚠ **What this costs:** the rule loses law precedence. A record conflicting with
a law is void in the conflicting part; a record conflicting with this one is
just a conflict, resolved by reading. **Nothing about the rule's content
changed** — the three environments and their one job each are exactly as
ruled on 2026-09-11.


### Consequences

- 🔴 **The hand-graded instrument is gone.** The playground's 50 goldens, the
  blind annotations and the third-annotator resolution can no longer grade
  anything new. **The golden ladder is now the only quality instrument**, and it
  does not exist yet (W-136 phase 1 is unrun).
- 🔴 **Three pending plans lose their corpus:** the four-priors remeasure's option
  *(a)* (declare `supersedes:` in the playground), W-97's veto leg, and R-11's
  retarget of W-87 Part B. Each moves to the lab's golden data or closes.
- **The W-136 ladder moves** from `fux-benchmark/corpora/golden/` to `fux-lab`.
- **The benchmark corpora do not exist.** The current `t100`/`t1000`/`t10000` are
  generated with a different shape; the 1 000-line, table-and-diagram documents
  need a generator, and 100/200/500/2 000/5 000 folders are new.
- **Every benchmark run carries two installs**, so the previous major must stay
  installable — a pinned `fux-engine==1.x` in its own virtualenv, per SETUP-BENCHMARK.
- **Easier:** Arpit can break, edit or wipe the playground without moving any
  number anywhere.
- ⚠ **Nothing mechanical enforces decision 1 yet** — W-138 is where a check is
  owed. Until then this record and CLAUDE.md are the guard.

### Alternatives considered

- **Keep the playground as the grading corpus and ask for care.** Rejected by
  Arpit: *"only and only for my usage."* Care had already failed — its tree
  indexed nothing for weeks while being graded against.
- **One shared corpus for the lab and the benchmark.** Rejected: a benchmark
  needs large, uniform documents and a stable query set to time; the lab needs a
  sealed answer key. One corpus would compromise both, and the lab's key would
  sit where timing runs touch it.
- **Benchmark only published releases** (newest release vs previous major).
  Declined 2026-09-11 in favour of the current build, so a regression is caught
  before it ships.
- **Benchmark every previous version.** Not asked for; two versions bound the
  cost and answer the question that matters — *did this major change it?*

### Reference (required)

- `CLAUDE.md` §Non-negotiable constraints — the normative text. Repo path: [`../../CLAUDE.md`](../CLAUDE.md)
- [SETUP-PLAYGROUND](../work/setup/fux-playground.md) ·
  [SETUP-LAB](../work/setup/fux-lab.md) ·
  [SETUP-BENCHMARK](../work/setup/fux-benchmark.md) — the three environments as they were set up
- [`work/golden/README.md`](../work/golden/README.md) — the golden test data the lab uses
- [SR-WORK-BENCHMARK](0053_WORK-benchmark.md) — what a benchmark run captures; this record decides only where it runs
- [SR-RS](0133_predictions.md) · [SR-WORK-QUALITY](0056_WORK-quality.md) — the measurement rules the lab runs under
- **Keeping evaluation data out of the hands that tune the system** — Sainz et al.,
  *NLP Evaluation in trouble: On the Need to Measure LLM Data Contamination for each
  Benchmark*, Findings of EMNLP 2023 — https://arxiv.org/abs/2310.18018
- **Benchmarking two versions and keeping every result to compare against** — the
  airspeed velocity (`asv`) model of per-commit benchmark history — https://asv.readthedocs.io/

### Veto condition

**Reopen if** any of these becomes true — check them, do not wait for them:

1. **A tool, test, script or filed run reads `fux-playground`** after 2026-09-11.
2. **A measurement run is filed on data other than the golden test data**, or on
   more than 10 000 documents.
3. **A benchmark run is filed with one fux version**, or with a pair other than
   the current build and the newest release of the previous major.
4. **A benchmark run files a subset of the captures** — that condition is
   [SR-WORK-BENCHMARK](0053_WORK-benchmark.md)'s to state and
   `tests/test_benchmark_capture.py` to check; this record's interest is only
   that the run happened here, with two versions.
5. **Any file states this rule instead of referencing this record** — a
   `CLAUDE.md` bullet, a skill, a README explaining what the lab is for. There
   is no generated copy, so a second statement is a plain duplication.
6. **`L9` is reused for a new law.** The handle is an identity and is cited in
   code comments and commit messages nobody will revisit, so reusing it makes an
   old citation resolve to something it never meant.
   ⚠ **The FILE NUMBER is not part of this.** `records/0011` was refilled the
   same day by `SR-LAW-10` moving down from `0012` (Arpit, 2026-09-13) — the
   register's own rule, that a number is an ordinal and not an identity, applied
   rather than excepted.

**How to check it:**

```bash
grep -rn "fux-playground" tools tests src scripts --include='*.py' --include='*.sh'
# expect: nothing that reads it (W-138 removes today's hits)
ls work/regression | awk '$0 >= "2026-09-12"'
# then, per new run: corpus is work/golden (lab) or a benchmark folder, and a
# benchmark run names two versions and files evidence/ranked-lists.*
```
