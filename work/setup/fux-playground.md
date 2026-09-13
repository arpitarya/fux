---
type: Setup
name: SETUP-PLAYGROUND
title: SETUP-PLAYGROUND — fux-playground, Arpit's sandbox
description: "How the sibling sandbox is stood up, the URL carry-forward trap that governs anything done in it, and the grading contract SR-WORK-ENVIRONMENTS retired — kept as history, never as a live instrument."
location: ~/my_programs/fux-playground
kind: sibling git repository (one local commit; no remote)
timestamp: 2026-09-12T00:00:00Z
---

# SETUP-PLAYGROUND — `fux-playground`

> **This is a setup document, not a decision record.** It records how the
> sandbox is stood up and the operational traps inside it. See
> [`README.md`](README.md) for what belongs in this directory.

🔴 **What this environment is for, and who may touch it, is stated by
[SR-WORK-ENVIRONMENTS](../../records/0052_WORK-environments.md) and nowhere else.** Read it
there. This document does not restate it and must never be read as a second
source for it ([L0](../../records/0002_LAW-0-authority.md)).

- **Name:** `SETUP-PLAYGROUND` — cite this by name
- **Location:** `~/my_programs/fux-playground` — a **sibling repository**, not a
  directory in this one
- **Created:** 2026-08-12, from the extraction pair now at
  [`archive/handoff/v0.31.0-fux-playground-extraction-handoff.md`](../../archive/handoff/v0.31.0-fux-playground-extraction-handoff.md)
- **Siblings:** [SETUP-LAB](fux-lab.md) · [SETUP-BENCHMARK](fux-benchmark.md).
  See [`README.md`](README.md) §Which is which.

---

## How to set it up

```bash
# 1. the repo sits NEXT TO fux, never inside it
cd ~/my_programs && ls        # expect: fux  fux-lab  fux-benchmark  fux-playground

# 2. it declares the engine as an editable dependency on the working tree
#    next door, so what you try by hand is the code being edited
grep -A2 'tool.uv.sources' ~/my_programs/fux-playground/pyproject.toml
#   [tool.uv.sources]
#   fux-engine = { path = "../fux", editable = true }
```

**Chrome CDP here listens on port 9299**, not the 9222 shown in this repo's
commented `fux.toml`. That difference is deliberate: the two can be running at
once.

## ⚠ Its committed index is `fux.index.v1`

Current fux is `fux.index.v2` — five fields, and it **refuses** a v1 shard
outright rather than mixing analyzers. `fux ingest --full && fux build` is
required before that repo answers a query at all. Checked 2026-08-25; nothing
has rebuilt it since.

This is also why the 2026-09-05 vector gate could not test its own bar — the
control it graded against was reading a corpus the engine could not open
([the run](../regression/2026-09-05-vector-gate/report.md)).

## The trap that governs anything done here

**A plain `fux ingest` carries existing `url:` records forward
byte-identically** — offline-by-default means reconciliation only happens on a
networked run. So once `--refresh-urls` has run, URL records are in
`.fux/index/`, and a later plain ingest will **not** remove them. Commit after a
refresh and a file-only index is silently gone.

Related: on a refresh, a *failed* fetch keeps the prior record rather than
deleting it — so *"record exists"* never proves *"fetched this run"*.

## Open

- **No git remote exists.** The repo has one local commit. If the paper cites
  this corpus it needs a public URL; that is a decision, not a task.

---

## What it used to be, until 2026-09-11

<details>
<summary><b>The graded contract — history, void forward, never an instrument again</b></summary>

**Kept because filed runs cite it**, and a reader who meets *"32/50 on the
playground"* in a 2026-08 verdict needs to know what was counted. Those runs
stand exactly as measured ([SR-WORK-ENVIRONMENTS](../../records/0052_WORK-environments.md)
decision 4, *forward only*). **Nothing here may be re-run, re-graded, cited as a
current capability, or restored.**

| part | what it was |
|---|---|
| **corpus** | 10 documents, mixed types, 100–400 lines — a fictional 10k-engineer company's internal developer platform (Calder Group / Helix), chosen over a trading domain **specifically** to satisfy the do-not-design-in-reference-to-Anton litmus |
| **goldens** | ~50 queries in `goldens/queries.jsonl`, graded on **rank**, never score; written from the corpus, never from what fux returned (there was no `--update-goldens` flag, by design) |
| **committed index** | file documents only; zero `url:` records |
| **URLs** | 10, mixed to stress the CDP fetcher — a runtime smoke test, never graded on ranking |
| **staleness guard** | `check.py --index-guard`: a fresh `fux ingest` had to reproduce the committed index byte for byte |
| **known failures** | `known_failure: "<reason>"` — an `XPASS` failed the run |
| **state, 2026-08-20** | corpus, `check.py` and the guard were rebuilt after the repo went missing (W-56); **the ~50 goldens were not**, deliberately — a golden derived from the engine under test passes forever, including on the day ranking breaks |

**Arpit had already called it, 2026-08-22:** *"[fux-playground is] for me to try
it out how it works, how does it feel like… No testing or anything or any sample
set should be captured from Fux Playground."* It sat in this document as a
*planned redesign, not yet executed* for twenty days while the corpus went on
being the instrument for the four ranking priors, W-97's veto leg and every
blind annotation run. **SR-WORK-ENVIRONMENTS is that ruling made law**, and the reconciliation is
[W-138](../../archive/open/W-138-reconcile-with-l9.md).

⚠ **What went with it, stated rather than discovered:** this was the project's
only ranking regression net. The replacement is the golden ladder in `fux-lab`
([`work/golden/`](../golden/README.md), W-136) — **and until a rung is graded
against an uncontaminated key, there is no net at all**, not a quieter one.

</details>

---

## The decision — `examples/` leaves the engine repo

*Settled 2026-08-12. Kept here because it is the reason this repository exists.*
⚠ **Its fourth part — the graded golden contract — was retired by SR-WORK-ENVIRONMENTS on
2026-09-11**; the other three stand.

## Context

`examples/playground/` was a 20-document AcmePay fixture living inside the
engine repo, added with the M1 T0 slice. Three things were wrong with it.

- **It contaminated the engine's own corpus.** This repo's `fux.toml` ingests
  `docs`, `README.md`, `CLAUDE.md`. The fixture's documents sat in the same
  tree, so the demo corpus and the dogfood corpus were one `dirs` edit away from
  measuring each other.

- **It shipped by accident of layout.** The sdist excluded it only because
  `[tool.hatch.build.targets.sdist]` happened not to name it — not because
  anyone decided a fixture should or should not be in the distribution.

- **It could not be graded.** It had no expected answers. A ranking regression
  changed what it printed and nothing noticed. A fixture that cannot fail is a
  screenshot.

Arpit's framing was direct: *"I do not want examples."*

## Decision

**`examples/` is deleted from this repository, and the demo corpus is rebuilt as
a separate sibling repository, `fux-playground`.**

1. **Separate repository, not a moved directory.** It is a real consumer of fux:
   it declares the engine as an editable dependency on the sibling working tree
   (`../fux`), so what runs there is the code being edited next door rather than
   a released wheel.

2. **The committed index is file documents only.** Zero `url:` records. URLs
   remain in the corpus as a *runtime smoke test* of the CDP fetcher, run
   deliberately and never committed.

3. **URL documents are not graded on ranking.** Their content is owned by third
   parties and changes without notice; a golden over it would be a test of the
   internet.

4. ⚠ **RETIRED 2026-09-11 by [SR-WORK-ENVIRONMENTS](../../records/0052_WORK-environments.md).**
   *"The golden queries are the regression contract"* — fifty hand-written
   queries asserting ranks — was the fourth part, and this environment no longer
   holds a contract anyone measures against.

## Alternatives considered

| option | why not |
|---|---|
| Keep `examples/` and add goldens in place | Leaves the corpus-contamination problem entirely unfixed, which was the first of the three reasons to act. |
| Move it to `tests_e2e/fixtures/` | Makes it a test fixture rather than something a human reads. The corpus has to be readable in twenty minutes or nobody validates that the goldens encode the right answers. |
| Grade the URL documents too | Third-party content changes without notice, so every such golden is a scheduled false alarm. It would also require committing fetched content, which [L2](../../records/0004_LAW-2-content-never-durable.md) forbids. |
| Publish `fux-playground` with a GitHub remote now | Out of scope and Arpit's call. No remote was created; the repo has one local commit. |

## Consequences

**Easier.**

- The engine's own dogfood corpus is now exactly its own documentation.
- The CDP fetcher has an exercise: ten pages including a client-rendered SPA, a
  redirect chain, and the same document over two transports.
- **Since SR-WORK-ENVIRONMENTS:** Arpit can break, edit or wipe this repo without moving a number
  anywhere.

**Harder, and what we now owe.**

- `.fux/fetchers/cdp.py` exists in both repos as a verbatim copy. The playground
  records the provenance commit (`43ba631`) and its sha256; a drift is caught by
  a human, not a test.
- `fux-playground` has no home beyond a local checkout. Open for Arpit.

**What this measured, in passing.** Building the corpus surfaced two engine
behaviours worth recording, neither of which was fixed here (out of scope):
markdown **link targets are tokenized into the linking document's body**, so
filename words inflate `df` for exactly the terms that should discriminate
(`glossary`: `df=9` as indexed vs `df=1` in prose); and at ten documents, `df`
saturation plus BM25's `tf` saturation at `k1=1.2` means term *presence* beats
*aboutness*, so a glossary that mentions everything once outranks the document
that owns the topic.

## References (required)

- [SR-WORK-ENVIRONMENTS](../../records/0052_WORK-environments.md) — the law that gave this
  environment its one job, and retired the other one.
- Google SRE Workbook, *Alerting on SLOs* —
  https://sre.google/workbook/alerting-on-slos/ — the source of the corpus's
  two-window burn-rate content, chosen so the fixture reads like real platform
  documentation rather than lorem ipsum.
- TREC's relevance-judgment methodology (`qrels`): judgments are made by
  assessors reading documents, never derived from a system's own output —
  https://trec.nist.gov/data/reljudge_eng.html — the discipline behind the
  retired rule that a golden is written from the corpus, and the one the golden
  ladder inherits.
- Robertson & Zaragoza, *The Probabilistic Relevance Framework: BM25 and Beyond*
  (2009) — https://www.staff.city.ac.uk/~sbrp622/papers/foundations_bm25_review.pdf
  — §3 on `k1` term-frequency saturation, the mechanism behind the third class
  of failure this corpus planted.
- [SR-RECORD](../../records/0109_index-record.md) — the committed index format ·
  [SR-URL-LIST](../../records/0116_url-list.md) ·
  [SR-DOTFUX](../../records/0102_fux-directory.md) — the URL source and `.fux/`
  layout this repo consumes.
