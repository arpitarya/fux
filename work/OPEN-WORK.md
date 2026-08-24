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

**One follow-up is worth a person and is not blocking anything:** have someone
write enrichment for the playground **without reading `goldens/queries.jsonl`**,
and re-grade. The enrichment measured on 2026-08-24 was written by an author who
had already seen the failing queries, so `38/50` and `41/50` are an **upper
bound**, not a measurement — disclosed in that run's `ANALYSIS.md` §1. The
unenriched `28 -> 32` is unaffected. This is also what would let **W-76 veto 3**
(*how small is "a small tilt"?*) be set on a clean number rather than a
contaminated one.

---

## Open items, by record

### [ADR-RANKING](../docs/adr/0012_ranking.md) · the whole register — records vs the code they describe

- **W-77** · `arpit` · **filed 2026-08-24 after a full ADR audit.** Sixteen records described a schema, a scoring model and a derived plane that W-76 replaced; all sixteen were amended the same day, along with five broken links, three wrong `built` cells, and a byte-count comment in `src/fux/derive/format.py` that had been lying since Phase 1. **What remains needs a human.** The finding worth reading is the governance gap: `tests/test_adr_freshness.py` passed throughout W-76 and the records still rotted, because ownership is **directory-level** — rewriting the scorer under `src/fux/query/` satisfied the check by touching **ADR-ASK**, while **ADR-RANKING**, whose entire subject is that scorer, was never opened. Four rulings owed: **ADR-REFER decision 4's premise is dead** (it refuses `max_age_seconds` because *"there is no such provenance"*; the record now carries `mtime`) and the decision is **standing but unargued**; ADR-ENRICHED vs ADR-ENRICH supersession; three status flips (ADR-MCP, ADR-ENRICH, ADR-RERANK — the last is built **and measured**); and ADR-TUNE's key names — **narrowed 2026-08-24**: ADR-TUNE is now BUILT (`v2.0.0-alpha.1`), so those names are a shipped interface rather than a proposal and renaming one is breaking from here; the record is still `status: proposed`, which is the state that makes the change free. **The mechanical half is now DONE (2026-08-24):** sixteen register labels corrected and the table sorted `0001`-`0041` contiguous, plus **71 further broken links** found by a repo-wide sweep and repointed — all of them links into `work/open/` for items that had closed into `archive/open/`, or ADR paths written from a stale display label. Gated by [`tests/test_doc_links.py`](../tests/test_doc_links.py) under the two-strikes rule. ⚠ **One new fork came out of that sweep and is NOT adjudicated**: ~40 of those repointed links now point *into* `archive/`, and whether a link in an ADR's prose is *naming* an archived item or *citing* it is a call only Arpit makes — a test was written for it and deliberately removed rather than shipped red — [detail](open/W-77-record-reconciliation.md)

### [ADR-RS](../docs/adr/0036_predictions.md) — the discipline says how a claim is frozen, not what to measure

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
