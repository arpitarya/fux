# OPEN-WORK — what is still open

*Items first, grouped by the record they belong to. **The rules and the standing
obligations are at the foot of this file** — read them once, then work from the
top.*

**Lane tags:** `agent` — an agent can close it alone · `arpit` — only Arpit can.
The two run **concurrently**; never order one against the other.

---

## Blocked on Arpit — the inbox

**Empty.** All three items filed 2026-08-24 were **delegated back the same day**
(*"all is on you. Make a call on it"*) and discharged — goldens created,
installed and graded; Phase 6 built and the cross-encoder refused with a stated
reopening condition. Decisions in
`archive/open/W-76-DECISIONS.md` D27–D30, evidence in
[`regression/2026-08-24-rerank-and-goldens/`](regression/2026-08-24-rerank-and-goldens/).

**The blind re-grade RAN (2026-08-24), and it did not come back small.**
Enrichment written by an author who had **not** seen the goldens is worth
**`+1`** (`32 -> 33`); the enrichment as committed, whose author had, is worth
**`+9`** (`32 -> 41`). Both previously-recorded numbers reproduced exactly.
⚠ **Corrected 2026-08-25, by the rule that ruling made.** The originally filed
diagnostic — *"the contaminated arm breaks zero of fifty"* — is **p ≈ 0.49** as
a marginal comparison and does not carry the weight it was given. **The force is
the CONCORDANCE**: both blind authors broke the *same two* queries and the
informed author preserved exactly those two, **≈ 0.028**. And `+1` / `-1` are
**below the resolution floor** the new rule sets, so the honest reading of the
blind arms is **no detected effect**, not `+1`.
[The run](regression/2026-08-24-blind-enrichment-regrade/report.md) ·
[what it means, unadjudicated](regression/2026-08-24-blind-enrichment-regrade/ANALYSIS.md).

**RULING 2 IS MADE (Arpit, 2026-08-25): the run-classification rule is
ACCEPTED**, in the rewritten form — every measured run is `blind` or `informed`
and says which; an informed run is **reclassified, never banned**, and never
supplies a delta. In force as
[ADR-RS](../docs/adr/0036_predictions.md) decisions 11-14 and
[`CLAUDE.md`](../CLAUDE.md) §Conformance runs, checked by
[`tests/test_regression_runs.py`](../tests/test_regression_runs.py) from
2026-08-25 forward. ⚠ Two of its six parts are **build work and did not take
effect** — [W-81](open/W-81-the-sealed-set-and-the-two-controls.md).

**One ruling is still owed, and it is yours — [W-78](open/W-78-enrichment-was-measured-against-its-own-answers.md) below.**

---

## Open items, by record

### [ADR-ENRICHED](../docs/adr/0017_enriched-mode.md) · the bundled embedding — a live claim grounded in an archived file

- **W-80** · `agent` · **filed 2026-08-24.** **fux tells a user with a corrupt model to run `tools/distill/distill.py`, and that path does not exist** — two live error messages in `src/fux/embed/model.py`, plus `model.json`'s `recipe` field, all point at it. It is **recoverable**: `archive/v0.26/tools/distill/distill.py` matches the shipped bundle on **every** checkable field (teacher `potion-base-8M`, magic `FUXEMB1\0`, the quantization string **verbatim**). ⚠ **The bundle's own integrity claim passes** — sha256 and size match — so **integrity is fine and provenance is what is missing**. ⚠ **The obvious fix is illegal**: repointing `model.json` at the archive grounds a **live claim** in an archived document, which archive-is-not-evidence forbids — so the fork is *restore it live* or *delete the provenance claim entirely*. **It blocks any model change**, including [the retrieval-tuned swap](proposals/retrieval-tuned-static-embedding.md) that the dense lane's FAIL makes worth testing — [detail](open/W-80-the-bundled-model-has-no-live-recipe.md)

### [ADR-RERANK](../docs/adr/0041_rerank.md) · [ADR-RS](../docs/adr/0036_predictions.md) — a ruling made on a number nobody knew was contaminated (**ruling 2 settled 2026-08-25; ruling 1 open**)

- **W-78** · `arpit` · **filed 2026-08-24 from the blind re-grade.** **Enrichment is worth `+1` blind and `+9` when its author has read the failing queries.** ADR-RERANK's veto 1 deferred the cross-encoder on *"enrichment is worth 10 points and reranking 4, and a 35 MB dependency targets the class enrichment already covers deterministically and for free"* — **blind, that reads +1 against +4, and the class is not covered.** The record has been amended to stop asserting the contaminated number as today's evidence and **deliberately not reopened**: a ruling made on a comparison is reopened by the person who made it. ⚠ **Veto 1's condition 2 is independent and untouched** — `onnxruntime` is still not byte-identical across architectures, so the cross-encoder stays refused on determinism whatever is decided; reopening condition 1 licenses an argument, not a build. **RULING 2 IS MADE (Arpit, 2026-08-25): ACCEPTED, in the rewritten form** — [ADR-RS](../docs/adr/0036_predictions.md) decisions 11-14 and [`CLAUDE.md`](../CLAUDE.md) §Conformance runs now carry it, checked from 2026-08-25 forward; ⚠ two of its six parts are apparatus and did **not** take effect ([W-81](open/W-81-the-sealed-set-and-the-two-controls.md)). **The reasoning it settled:** fux forbids `--update-goldens` because a golden regenerated from engine output is a screenshot with a test attached — **this is the same failure through the other door**, corpus metadata fitted to the goldens, and nothing forbade it. The rule landed in [ADR-RS](../docs/adr/0036_predictions.md), which is where a measurement-protocol rule belongs (`fux enrich` **cannot** enforce it — the model is the author and fux never calls one). ⚠ **The wording originally drafted here was REFUSED**; what was accepted is *reclassify, never ban*, TREC's mechanism since 1994. **The confound is CLOSED (2026-08-24): a second blind author scored `31/50`, net `-1`.** Two blind authors, `+1` and `-1`, mean zero — and **both broke the same two queries** while the contaminated author broke neither, which is a property of the task rather than of craft. **The mechanism is one word**: `q015` asks for the *current* decision and both blind authors truthfully wrote *"no-longer-current"* on the **superseded** ADR, while the contaminated one wrote *"retired and replaced"*. **BM25F cannot see negation**, so honest metadata about a retired document ranks it as a live one. ⚠ Fux's own answer, `[ranking] superseded_weight`, is **inert on the fixture** — `superseded_ids` reads a frontmatter `supersedes:` key and the playground declares supersession in prose only, so the prior has never been graded. **ONE ruling remains: [reopen-or-confirm](compare/cross-encoder-reopen.compare.md) — recommend CONFIRM, on a rewritten reason.** [The blind-authorship rule](compare/blind-authorship-rule.compare.md) is **✅ accepted (2026-08-25)**. ⚠ **Three corrections to this item's own evidence are recorded in it**: the *zero broken* argument is **p ≈ 0.49** as a marginal comparison and must be cited as the **concordance** instead (≈ 0.028, ~17x the weight); fifty queries is **under-powered** (TREC ~2.4 % error at 50 topics) so `+1`/`-1` are noise; and the runs have **no source-bias control**, which KDD 2024 shows matters for any LLM-written text — now owed as [W-81](open/W-81-the-sealed-set-and-the-two-controls.md). ⚠ **Under the rule this item's own ruling created, `+1` and `-1` are below the resolution floor**: the honest reading of the blind arms is *no detected effect*, and the statistic that survives is the concordance. **Model: Opus** — the ruling is a judgement about evidence — [detail](open/W-78-enrichment-was-measured-against-its-own-answers.md)

### [ADR-RANKING](../docs/adr/0012_ranking.md) · the whole register — records vs the code they describe

- **W-77** · `arpit` · **filed 2026-08-24 after a full ADR audit.** Sixteen records described a schema, a scoring model and a derived plane that W-76 replaced; all sixteen were amended the same day, along with five broken links, three wrong `built` cells, and a byte-count comment in `src/fux/derive/format.py` that had been lying since Phase 1. **What remains needs a human.** The finding worth reading is the governance gap: `tests/test_adr_freshness.py` passed throughout W-76 and the records still rotted, because ownership is **directory-level** — rewriting the scorer under `src/fux/query/` satisfied the check by touching **ADR-ASK**, while **ADR-RANKING**, whose entire subject is that scorer, was never opened. Four rulings owed: **ADR-REFER decision 4's premise is dead** (it refuses `max_age_seconds` because *"there is no such provenance"*; the record now carries `mtime`) and the decision is **standing but unargued**; ADR-ENRICHED vs ADR-ENRICH supersession; three status flips (ADR-MCP, ADR-ENRICH, ADR-RERANK — the last is built **and measured**); and ADR-TUNE's key names — **narrowed 2026-08-24**: ADR-TUNE is now BUILT (`v2.0.0-alpha.1`), so those names are a shipped interface rather than a proposal and renaming one is breaking from here; the record is still `status: proposed`, which is the state that makes the change free. **The mechanical half is now DONE (2026-08-24):** sixteen register labels corrected and the table sorted `0001`-`0041` contiguous, plus **71 further broken links** found by a repo-wide sweep and repointed — all of them links into `work/open/` for items that had closed into `archive/open/`, or ADR paths written from a stale display label. Gated by [`tests/test_doc_links.py`](../tests/test_doc_links.py) under the two-strikes rule. ⚠ **One new fork came out of that sweep and is NOT adjudicated**: ~40 of those repointed links now point *into* `archive/`, and whether a link in an ADR's prose is *naming* an archived item or *citing* it is a call only Arpit makes — a test was written for it and deliberately removed rather than shipped red — [detail](open/W-77-record-reconciliation.md)

### [ADR-RS](../docs/adr/0036_predictions.md) — the discipline says how a claim is frozen, not what to measure

- **W-81** · `agent` · **filed 2026-08-25 out of W-78 ruling 2.** **Four of the accepted rule's six parts took effect the day it was ruled; two did not, and a rule that is written and unbuilt reads as in force.** Classification, reporting, the comparison bar and the resolution floor are protocol — ADR-RS decisions 11-14, live now. **The sealed query subset and the decoy / content-free-placebo control arms are apparatus**, filed as decision 15 `NOT BUILT`. ⚠ **Sealing makes the power problem worse before it makes it better** — 50 queries is already under-powered at TREC's ~2.4 % error, and splitting it shrinks the half that carries the claim; §1 says the three honest options and forbids picking silently. ⚠ **And "sealed" has to be mechanical**: BIG-bench's canary GUID was embedded *so that* labs would exclude it and a model reproduced it anyway, so a directory an agent is asked not to read is not sealed. The controls close a real gap — KDD 2024's **source bias**, where retrievers rank LLM prose higher regardless of whether it informs, and every enrichment arm on file added ~70 tokens of it with no matched placebo. ⚠ **This does not threaten the finding it qualifies**: source bias would make enrichment's true content contribution *lower*, and blind it was already below the floor — [detail](open/W-81-the-sealed-set-and-the-two-controls.md)

- **W-74** · `arpit` · **BLOCKED ON ARPIT — six forks gate what gets built** · **fux has no contract for what "right" means.** ADR-RS governs *how* a claim is frozen and is silent on *what quantity is worth freezing*, so every quality number this project has produced carries an **undeclared query distribution** and an implicit cost model in which a fabricated citation and an honest decline count the same. Two live runs already passed their number and failed their claim — [P1-GATE](regression/2026-08-09-pruning-eval/VERDICT.md) (0.00 pt delta because the treatment touched 0–2.5 % of documents) and [the budget sweep](regression/2026-08-22-budget-sweep/ANALYSIS.md) (*"satisfied by its letter and violated by its purpose"*) — and **a human caught both, not the metric**. Proposes a scorecard: a versioned `mix.toml`, a four-gate funnel whose middle gate (`recall@k`) is the only one fux owns outright, correct-per-byte as the headline, cost-weighted error, calibration. ⚠ **Not a re-filing of W-62** — that item's parts 1–2 are withdrawn and Arpit's; this measures **fux against itself**. **Part A (the declarations) is unblocked by the lab; Part B cannot run — `acme`/`orbit` are gone and the five-tier redesign is unexecuted.** **Model: Opus** for the forks and the cost vector, Sonnet for the harness — [detail](open/W-74-answer-quality-measurement-contract.md) · [spec](proposals/measuring-answer-quality.md)

### [ADR-URL-INGEST](../docs/adr/0008_url-ingest.md) · [ADR-FETCHER](../docs/adr/0019_fetcher.md) — nothing in fux can learn that a URL changed

- **W-75** · `arpit` + `agent` · **BLOCKED ON ARPIT for the build (eight forks); Phases 0 and 1 are STARTABLE now** · **a file change is an event, a URL change is not.** `post-commit` re-indexes a changed repo document; a changed URL is discovered when a human next types `fux update`, and **nothing reports how long ago that was**. Smaller than it looks and worse where it bites: the refer plane already re-fetches every cited URL and compares shas, so a stale `url:` record costs **recall, not correctness** — it cannot be mis-answered, only fail to surface, which is the tail, which at the design point is most of the corpus. Sized by two facts that are each disqualifying at 100k URLs: `fetch(url) -> str` returns markdown with **no headers**, so fux structurally cannot issue a conditional GET and every *"did it change?"* costs a full render; and `fetch_all` is a **strictly sequential loop**. ⚠ Three hazards carried in the item: `dirty.py`'s *"advisory, never authoritative"* is the sentence that keeps L3 true and a URL refresh driven by it is **not** advisory (defence written, and it is **not** *"just index the delta"*, which was ruled not the fix for R5); a changed validator token must **never** mean a changed record; and **`cdp.py` is not thread-safe** (`global _session`, one WebSocket) so a blind thread pool yields *plausible documents attributed to the wrong URLs* — passes every determinism check, caught only by a human reading an answer. **Model: Opus** for the forks and the contract, Sonnet for Phase 0 — [detail](open/W-75-url-freshness.md) · [spec](proposals/url-freshness.md) · forks split to [trigger](compare/url-refresh-trigger.compare.md) and [concurrency](compare/url-fetch-concurrency.compare.md)

---

# The rules

*Kept at the foot deliberately: they change rarely, and the items are what a
session needs first.*

1. **Maintained in the same change as the work**, never afterwards. An item
   finishes, a defect is found, scope moves, something blocks or unblocks: this
   file and the item's detail file change in that same edit. A session that
   updates the queue "at the end" has already lied to the one after it.
2. **A resolved thing leaves this file entirely — including the sentence saying
   it resolved.** No "X was decided and left the inbox", no "closed on the
   12th", no note explaining an absence. **A row that is still here is still
   open**, and that is the only thing this file says. An item's own row may
   state that its *decision* is made and its build is not — that is its status,
   not a tombstone. Everything else about a closed item lives in
   [`IMPLEMENTATION.md`](IMPLEMENTATION.md), the [WORKLOG](WORKLOG.md), and the
   archived detail file.
3. **Completed items are removed, never ticked.** Closing is legal only once
   the outcome is recorded in [`IMPLEMENTATION.md`](IMPLEMENTATION.md) and any
   evidence is filed under [`regression/`](regression/README.md). **The row is
   deleted; the detail file moves to [`archive/open/`](../archive/open/)**
   (Arpit, 2026-08-19) — the reasoning that produced a call is worth keeping,
   the queue entry is not. The durable record is still the ADR plus the
   [WORKLOG](WORKLOG.md) entry; an archived file may be named, never cited. No
   tombstones, no DONE rows, no `closed/` inside `work/`.
   **The length of this file is the signal of how much is actually pending.**
4. **The markers here are assertions, not evidence. Re-derive, do not read.**
   Before treating anything as pending or done, reconcile against
   `regression/`, `IMPLEMENTATION.md`, and the repo itself (`git log`,
   `git tag`, the code). A stale ✅ overstates progress; a stale pending row
   that an unrelated commit already closed understates it — **both are the same
   class of defect**.
5. **Two lanes, ordered independently — they run concurrently.** `arpit` needs
   a human's hands; `agent` an agent can execute alone. Forcing one priority
   order across both is what makes a session sit idle behind a decision it was
   never going to make. Order **within** a lane; never across them.
6. **Priority is damage that accrues with elapsed time**, above damage that is
   merely present-but-static. A wrong constant that is the same size next month
   can wait; an unratified record that more code ships under every day cannot.
   Only the former gets worse by waiting.
7. **No separate prioritization or sequencing document.** Ordering lives here.
   A second document naming what to do next is always the stale one.
8. **Grouped by record, because that is where the work lands.** An item's group
   is the record its change will have to update — which is Law zero made
   visible: if you cannot name the record, say **"no ADR affected"** out loud.

## Standing obligations (every session)

- **WORKLOG entry per substantive exchange** — a chat-only session counts.
  (The `Cost:` line was mandatory here until 2026-08-21 — dropped, PRIORITY
  P7: 58/58 entries had said `unmeasured`.)
- **This file and the item's detail file** on any status change; a DOC-REGISTRY
  row bump for any doc touched; INTERVIEW kept current *during* the session.
- **Reconcile before you report** (rule 4).
- **Records are cited by name** — `ADR-RECORD`, never a number. "archived
  ADR-NNNN" *with its path* means the frozen v0.26 line under
  `archive/v0.26-docs/adr/`; a bare `ADR-<NAME>` means `docs/adr/`.
- **No behaviour change lands without its record updated in the same change.**
  If a change genuinely touches no recorded decision, say **"no ADR affected"**
  in the commit message rather than skipping the check silently.
- **The lab persists.** `~/my_programs/fux-lab` is never deleted or rebuilt —
  new runs are new environments inside it ([SETUP-LAB](setup/fux-lab.md)).
