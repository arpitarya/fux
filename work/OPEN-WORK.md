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
[`open/W-76-DECISIONS.md`](open/W-76-DECISIONS.md) D27–D30, evidence in
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

### [ADR-T1-ACCELERATOR](../docs/adr/0011_accelerator.md) · [ADR-RANKING](../docs/adr/0012_ranking.md) — the differential law's unstated boundary

- **W-73** · `agent` · **BUILT 2026-08-23, uncommitted** — `rank.Weighting` carries the query-time weights into the bound, `derive/accel.py::block_bound` recombines per-field extrema *at those weights*, and `_kth_score`/`_cannot_reach` take the weighting rather than assuming `1.0`. **The differential law now holds at every configured weight**, which is what the row below said it did not. Fork 3 (per-field extrema loosening the bound) was the declared threat and **measured free — +0.0 % blocks scanned**, because 92.5 % single-field postings make the per-field sum exact rather than loose; filed in [`regression/2026-08-23-fork3-per-field-bound/`](regression/2026-08-23-fork3-per-field-bound/), re-run against 10 000 real documents. ⚠ **W-44's row still asserts the opposite and needs its correction.** Original statement follows — · **the differential law holds only at `archived_weight == 1.0`, and nothing says so.** The accelerator prunes blocks on **unweighted** score bounds and an **unweighted** `theta`, then `rank()` applies the weight afterwards — so at any configured weight, `ask --fast` and `ask --scan` can return different documents. Both directions diverge: `w > 1` skips a block whose document would have won; `w < 1` lowers the real threshold after the pruning that used the old one. `config.py` accepts **any non-negative float**, and `tools/differential/`'s thousands of comparisons all ran at the default. ⚠ **W-44's row asserts the opposite** — *"the differential law carries it down both the scan and accelerator paths for free"* — which is true at `1.0` and at no other value. **The fix is small** (weighted `theta`, ceiling × `w_max`) **and the argument is not**, which is why the model is Opus. **Gates the per-source priority feature entirely** — [the proposal](proposals/tune-file-and-source-priority.md)'s fork 9 is ruled (*both directions; fux states the cost and refuses only `w ≤ 0`*), so this is now the only thing standing between that design and a build. **Closes with [ADR-TUNE](../docs/adr/0038_tuning.md) decision 12 + an ADR-T1-ACCELERATOR amendment** — the record is written and is `proposed` partly *because* this is unbuilt; its **veto condition 2 is FIRING**. **Model: Opus** — [detail](open/W-73-weighted-scores-vs-pruning-bound.md)

### [ADR-RS](../docs/adr/0036_predictions.md) — the discipline says how a claim is frozen, not what to measure

- **W-74** · `arpit` · **BLOCKED ON ARPIT — six forks gate what gets built** · **fux has no contract for what "right" means.** ADR-RS governs *how* a claim is frozen and is silent on *what quantity is worth freezing*, so every quality number this project has produced carries an **undeclared query distribution** and an implicit cost model in which a fabricated citation and an honest decline count the same. Two live runs already passed their number and failed their claim — [P1-GATE](regression/2026-08-09-pruning-eval/VERDICT.md) (0.00 pt delta because the treatment touched 0–2.5 % of documents) and [the budget sweep](regression/2026-08-22-budget-sweep/ANALYSIS.md) (*"satisfied by its letter and violated by its purpose"*) — and **a human caught both, not the metric**. Proposes a scorecard: a versioned `mix.toml`, a four-gate funnel whose middle gate (`recall@k`) is the only one fux owns outright, correct-per-byte as the headline, cost-weighted error, calibration. ⚠ **Not a re-filing of W-62** — that item's parts 1–2 are withdrawn and Arpit's; this measures **fux against itself**. **Part A (the declarations) is unblocked by the lab; Part B cannot run — `acme`/`orbit` are gone and the five-tier redesign is unexecuted.** **Model: Opus** for the forks and the cost vector, Sonnet for the harness — [detail](open/W-74-answer-quality-measurement-contract.md) · [spec](proposals/measuring-answer-quality.md)

### [ADR-URL-INGEST](../docs/adr/0008_url-ingest.md) · [ADR-FETCHER](../docs/adr/0019_fetcher.md) — nothing in fux can learn that a URL changed

- **W-75** · `arpit` + `agent` · **BLOCKED ON ARPIT for the build (eight forks); Phases 0 and 1 are STARTABLE now** · **a file change is an event, a URL change is not.** `post-commit` re-indexes a changed repo document; a changed URL is discovered when a human next types `fux update`, and **nothing reports how long ago that was**. Smaller than it looks and worse where it bites: the refer plane already re-fetches every cited URL and compares shas, so a stale `url:` record costs **recall, not correctness** — it cannot be mis-answered, only fail to surface, which is the tail, which at the design point is most of the corpus. Sized by two facts that are each disqualifying at 100k URLs: `fetch(url) -> str` returns markdown with **no headers**, so fux structurally cannot issue a conditional GET and every *"did it change?"* costs a full render; and `fetch_all` is a **strictly sequential loop**. ⚠ Three hazards carried in the item: `dirty.py`'s *"advisory, never authoritative"* is the sentence that keeps L3 true and a URL refresh driven by it is **not** advisory (defence written, and it is **not** *"just index the delta"*, which was ruled not the fix for R5); a changed validator token must **never** mean a changed record; and **`cdp.py` is not thread-safe** (`global _session`, one WebSocket) so a blind thread pool yields *plausible documents attributed to the wrong URLs* — passes every determinism check, caught only by a human reading an answer. **Model: Opus** for the forks and the contract, Sonnet for Phase 0 — [detail](open/W-75-url-freshness.md) · [spec](proposals/url-freshness.md) · forks split to [trigger](compare/url-refresh-trigger.compare.md) and [concurrency](compare/url-fetch-concurrency.compare.md)

### [ADR-INDEX-LIFECYCLE](../docs/adr/0009_index-lifecycle.md) · [ADR-RECORD](../docs/adr/0010_record.md) · [ADR-TUNE](../docs/adr/0038_tuning.md) — the amended architecture, both forks ruled

- **W-76** · `agent` · **ALL NINE PHASES BUILT 2026-08-23/24, uncommitted.** Phase 6 landed 2026-08-24 as [ADR-RERANK](../docs/adr/0041_rerank.md) — proximity reranking in **stdlib arithmetic**, with the specified cross-encoder **refused** because `onnxruntime` is not byte-identical across x86-64 and arm64 and would make an answer depend on the machine. Measured on 50 new goldens: **28 -> 32** (4 fixed, **0 broken**), **+8 ms p95** against a 150 ms bar at 10 000 documents, differential law green over **240** comparisons. The decisive finding is what the reranker could NOT reach: of 18 surviving failures, **18 are vocabulary gaps and 0 are ordering failures**, so enrichment is worth 10 points where reranking is worth 4 — which is why the cross-encoder is deferred with a price rather than rejected. — analyzer v2 (Porter, 75/75 published vectors; identifier splitting), five-field BM25F with `derive_wlen` as the single site of the arithmetic, the 62-byte accelerator entry, priors, `.fux/tune.toml` keys, per-chunk committed `int8` vectors with a derived Hamming prefilter, `fux enrich` (ADR-ENRICH) and `fux mcp` (ADR-MCP). **1 246 tests pass.** Validated against real corpora: fux-playground **21 376 differential comparisons byte-identical** across a weight sweep, and fux-lab at 10 000 real documents — ingest 31.5 s, build 1.4 s, **p95 33.53 ms against a 150 ms bar**. **This repo's own index is migrated** — 434 records, `fux.index.v2`/analyzer `v2`, `code` field gone, delta run byte-identical to the full run. Doing that surfaced a real defect: **the migration command ADR-INDEX-LIFECYCLE decision 10 documents did not work** (`--full` read the index it exists to replace), fixed and amended into the record. Every decision taken in Arpit's absence is in [`open/W-76-DECISIONS.md`](open/W-76-DECISIONS.md). Original statement follows — · **the parked [ideal set](proposals/ideal/README.md) was re-argued against four rulings and is now a nine-phase build.** Fork A ruled **everything committed** — *"I don't want to run `fux build`. I want it committed. I'm going to clone the repo and run the query."* — so per-chunk `int8` vectors are **committed** and the 256-bit sign codes become the *derived accelerator* over them, under the existing differential law. That refusal cascades: doc 01's committed/derived split is **cancelled**, **L3's relaxation to result-determinism is refused**, the merge driver and the runtime stamp/manifest **stay**, and `refs/fux/<tree>` is demoted to cache warmth (a fresh clone runs no hooks and fetches no custom refs, so it could never have been a correctness path). Fork B ruled **`ctx` is a weighted BM25F field, with tuning kept** — which **forces ADR-TUNE's `wlen` fix into Phase 1**: `w_ctx` cannot be a tune key while field weights are baked into the committed `wlen` (decision 6, already violated once by `HEADING_WEIGHT`, and Phase 1 takes that from one field to five). ⚠ **[W-73](open/W-73-weighted-scores-vs-pruning-bound.md) must land before or with Phase 1** — the accelerator prunes on *unweighted* bounds and Phase 1 takes the weight count 2 → 5. Measured on this repo 2026-08-23: **92.5 % of postings are body-only**, so a body-first sparse tf encoding is **−36.7 %** on tf bytes *with five fields instead of two* — **analyzer v2 makes the index smaller (−5 %)**; committing the vectors is what costs (**+22 % net, ~152 MB at 10 000 docs**, accepted by Arpit on sight). **Veto 3 is a condition of the fork B ruling**, not decoration — *"if it is a small tilt"* is measured, and the threshold is proposed rather than ruled. **Arpit 2026-08-23: `fux build` STAYS** — not deleted, not made implicit; what was missing is that nothing tells a fresh clone it exists, so **Phase 0** puts a stderr declaration on the read verbs when committed shards are present and no accelerator is built, carrying *"results are identical either way"* and following W-66 Phase 3's rules verbatim (stderr never stdout, ASCII only, declares never gates). Phase 0 **ships independently, before any of the rest**. Also ruled: the `code` field is dropped in Phase 1 **for time, not bytes** — it is 0.4 % of the index and **91 % of every full ingest** (3.996 s of 4.38 s at 1 000 docs, filed), so dropping it makes ingest and hooks **~11× faster** until Phase 7; and it is **promoted, not replaced** — the same 256-bit Hamming scan returns in Phase 7 as the *derived prefilter* over committed `int8` vectors, per chunk instead of per document. `--hybrid` has no lane between Phases 1 and 7: keep it accepted and **fail loudly** (the `--refresh-urls` precedent, not the `fux url` one — 1.0.0 is on PyPI). **`.fux/tune.toml` is already specified** by [ADR-TUNE](../docs/adr/0038_tuning.md) and is where `w_ctx` lands. **Model: Opus** for Phases 1, 7 and 8 (the encoding, the `wlen` migration and the enrichment contract are arguments), **Sonnet** for Phases 0, 2, 3, 5, 6 and 9 — [detail](open/W-76-amended-architecture.md) · [spec](proposals/ideal/07-rulings.amendment.md)

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
