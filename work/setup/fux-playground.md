---
type: Setup
name: SETUP-PLAYGROUND
title: SETUP-PLAYGROUND — fux-playground, the graded corpus
description: "How the graded fixture corpus is set up as a sibling repository, why it left the engine repo, and the contract that keeps it honest."
location: ~/my_programs/fux-playground
kind: sibling git repository (one local commit; no remote)
timestamp: 2026-08-12T00:00:00Z
---

# SETUP-PLAYGROUND — `fux-playground`, the graded corpus

> **This is a setup document, not a decision record.** It was written as an ADR
> and converted on 2026-08-18: most of it is *how to stand this thing up and
> what its contract is*, which is operational knowledge, not a decision anyone
> supersedes. See [`README.md`](README.md) for what belongs in this directory.
>
> The one genuine decision inside it — **`examples/` is deleted from the engine
> repo** — is recorded below under §The decision, and is settled.

- **Name:** `SETUP-PLAYGROUND` — cite this by name
- **Location:** `~/my_programs/fux-playground` — a **sibling repository**, not a
  directory in this one
- **Created:** 2026-08-12, from the extraction pair now at
  [`archive/handoff/v0.31.0-fux-playground-extraction-handoff.md`](../../archive/handoff/v0.31.0-fux-playground-extraction-handoff.md)
- **State at creation:** 41 pass · 9 named `xfail` · 0 unexplained failures
- **Sibling of:** [SETUP-LAB](fux-lab.md) — the two are often confused. The
  playground **grades**; the lab **measures**. See
  [`README.md`](README.md) §Which is which.

---

## How to set it up

```bash
# 1. the repo sits NEXT TO fux, never inside it
cd ~/my_programs && ls        # expect: fux  fux-playground

# 2. it declares the engine as an editable dependency on the working tree
#    next door, so goldens grade the code being edited — not a released wheel
grep -A2 'tool.uv.sources' ~/my_programs/fux-playground/pyproject.toml
#   [tool.uv.sources]
#   fux-engine = { path = "../fux", editable = true }

# 3. grade the corpus
cd ~/my_programs/fux-playground && python check.py

# 4. the staleness guard — a fresh ingest must reproduce the committed
#    index byte for byte, which doubles as a determinism test
python check.py --index-guard
```

**Chrome CDP for the playground listens on port 9299**, not the 9222 shown in
this repo's commented `fux.toml`. That difference is deliberate: the two can be
running at once.

## The contract

| part | rule |
|---|---|
| **corpus** | 10 documents, mixed types, 100–400 lines. A fictional 10k-engineer company's internal developer platform (Calder Group / Helix) — chosen over a trading domain **specifically** to satisfy the do-not-design-in-reference-to-Anton litmus |
| **goldens** | ~50 queries in `goldens/queries.jsonl`, graded on **rank**, never score. **Written from the corpus, never from what fux returns** — there is no `--update-goldens` flag, by design |
| **committed index** | **file documents only. Zero `url:` records.** |
| **URLs** | 10, deliberately mixed to stress the CDP middleware. A **runtime smoke test only** — never graded on ranking |
| **staleness guard** | a fresh `fux ingest` must reproduce the committed index byte for byte or `check.py --index-guard` fails |
| **known failures** | a query may carry `known_failure: "<reason>"`. The expectation is unchanged; a named gap does not redden the suite, and a known failure that starts **passing** is reported `XPASS` and **fails the run** |

## The trap that governs the design

**A plain `fux ingest` carries existing `url:` records forward
byte-identically** — offline-by-default means reconciliation only happens on a
networked run. So once `--refresh-urls` has run, URL records are in
`.fux/index/`, and a later plain ingest will **not** remove them. Commit after
a refresh and the file-only invariant is silently gone.

**Any URL smoke test must restore `.fux/index/` from git on every exit path.**

Related: on a refresh, a *failed* fetch keeps the prior record rather than
deleting it — so "record exists" never proves "fetched this run".

## Open

- **No git remote exists.** The repo has one local commit. If the paper cites
  this corpus it needs a public URL; that is a decision, not a task.

---

## The decision — `examples/` leaves the engine repo

*Settled 2026-08-12. Kept here because it is the reason this repository
exists.*

## Context

`examples/playground/` was a 20-document AcmePay fixture living inside the
engine repo, added with the M1 T0 slice. Three things were wrong with it.

- **It contaminated the engine's own corpus.** This repo's `fux.toml`
  ingests `docs`, `README.md`, `CLAUDE.md`. The fixture's documents sat in
  the same tree, so the demo corpus and the dogfood corpus were one
  `dirs` edit away from measuring each other.

- **It shipped by accident of layout.** The sdist excluded it only because
  `[tool.hatch.build.targets.sdist]` happened not to name it — not because
  anyone decided a fixture should or should not be in the distribution.

- **It could not be graded.** It had no expected answers. A ranking
  regression changed what it printed and nothing noticed. A fixture that
  cannot fail is a screenshot.

Arpit's framing was direct: *"I do not want examples."*

## Decision

**`examples/` is deleted from this repository, and the demo corpus is rebuilt
as a separate sibling repository, `fux-playground`, that is graded.**

Four parts to the decision.

1. **Separate repository, not a moved directory.** `fux-playground` is a
   real consumer of fux: it declares the engine as an editable dependency on
   the sibling working tree (`../fux`), so its goldens grade the code being
   edited next door rather than a released wheel.

2. **The committed index is file documents only.** Zero `url:` records. URLs
   remain in the corpus as a *runtime smoke test* of the CDP middleware, run
   deliberately and never committed.

3. **URL documents are not graded on ranking.** Their content is owned by
   third parties and changes without notice; a golden over it would be a test
   of the internet. They exist to exercise the middleware, which is the
   engine's only networked path and otherwise has no test surface.

4. **The golden queries are the regression contract.** Fifty hand-written
   queries assert *ranks*, never scores. Scores are an implementation detail;
   a rank is the thing a user experiences.

### The corpus is deliberately adversarial

Ten documents, each planting a named hazard: a superseded ADR that must yield
to its successor, two near-identical runbooks for different fleets, a
high-traffic guide that must *not* win specific questions, four words that
mean different things in two documents, a short notice owning one narrow
fact, a postmortem whose links carry half its answer, and five questions the
corpus genuinely cannot answer.

### Known failures are named, not hidden

A query may carry `known_failure: "<reason>"`. The expectation is unchanged —
it still states what a correct engine should do — but a named, understood gap
does not redden the suite. A known failure that starts *passing* is reported
as `XPASS` and fails the run, so a closed gap is recorded deliberately rather
than drifting.

At the time of writing: **41 pass, 9 xfail, 0 unexplained failures.** The nine
are the deliverable, not a defect in it — they are pre-registered targets for
the M2 dense lane and M3 graph lane.

## Alternatives considered

| option | why not |
|---|---|
| Keep `examples/` and add goldens in place | Leaves the corpus-contamination problem entirely unfixed, which was the first of the three reasons to act. |
| Move it to `tests_e2e/fixtures/` | Makes it a test fixture rather than something a human reads. The corpus has to be readable in twenty minutes or nobody validates that the goldens encode the right answers. |
| Grade the URL documents too | Third-party content changes without notice, so every such golden is a scheduled false alarm. It would also require committing fetched content, which the "content is never durable outside its source system" law forbids. |
| Publish `fux-playground` with a GitHub remote now | Out of scope and Arpit's call. No remote was created; the repo has one local commit. If the paper is going to cite this corpus it needs a public URL, which is a decision, not a task. |
| Let failing goldens simply stay red | A permanently red suite is not a regression net — nobody can tell a new break from the standing nine. `xfail` with a written mechanism keeps both signals. |

## Consequences

**Easier.**

- The engine's own dogfood corpus is now exactly its own documentation.
- A ranking change has to survive fifty ranked assertions across seven
  hazard classes before it can land quietly.
- The committed index is verified byte-for-byte on every run, so the
  determinism law is checked continuously rather than asserted.
- The CDP middleware finally has an exercise: ten pages including a
  client-rendered SPA, a redirect chain, and the same document over two
  transports.

**Harder, and what we now owe.**

- Two repositories to keep in step. The playground's `check.py --index-guard`
  fails loudly when the engine's output changes, which is the intended
  coupling, but it does mean an engine change can require a playground commit.
- `.fux/middleware/cdp.py` exists in both repos as a verbatim copy. The
  playground records the provenance commit (`43ba631`) and its sha256; a
  drift is currently caught by a human, not a test.
- The nine known failures are a standing debt. Each must be revisited when
  M2 and M3 land — and `XPASS` will say so.
- `fux-playground` has no home beyond a local checkout. Open for Arpit.

**What this measured, in passing.** Building the corpus surfaced two engine
behaviours worth recording, neither of which was fixed here (out of scope):
markdown **link targets are tokenized into the linking document's body**, so
filename words inflate `df` for exactly the terms that should discriminate
(`glossary`: `df=9` as indexed vs `df=1` in prose); and at ten documents,
`df` saturation plus BM25's `tf` saturation at `k1=1.2` means term *presence*
beats *aboutness*, so a glossary that mentions everything once outranks the
document that owns the topic. Both are documented in the playground's
`PLAYGROUND.md`.

## References (required)

- Google SRE Workbook, *Alerting on SLOs* —
  https://sre.google/workbook/alerting-on-slos/ — the source of the corpus's
  two-window burn-rate content, chosen so the fixture reads like real
  platform documentation rather than lorem ipsum.
- TREC's relevance-judgment methodology (`qrels`): judgments are made by
  assessors reading documents, never derived from a system's own output —
  https://trec.nist.gov/data/reljudge_eng.html — the discipline behind this
  corpus's rule that a golden is written from the corpus and never from what
  fux returned.
- pytest's `xfail` semantics, including `XPASS` as a failure —
  https://docs.pytest.org/en/stable/how-to/skipping.html#xfail-mark-test-functions-as-expected-to-fail
  — the model for `known_failure`.
- Robertson & Zaragoza, *The Probabilistic Relevance Framework: BM25 and
  Beyond* (2009) — https://www.staff.city.ac.uk/~sbrp622/papers/foundations_bm25_review.pdf
  — §3 on `k1` term-frequency saturation, which is the mechanism behind the
  third class of known failure.
- [ADR-RECORD](../../archive/adr/0004_index-format.md) — the committed index format the guard
  checks. [ADR-URL-INGEST](../../archive/adr/0010_url-source-consumer-middleware.md) /
  [ADR-DOTFUX](../../archive/adr/0011_fux-dir-layout.md) — the URL source and `.fux/` layout the
  playground consumes.
