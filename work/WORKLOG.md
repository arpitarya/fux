# WORKLOG — the append-only session log

**How to use this file.** Every session appends **one entry before it ends** —
Cowork, Claude Code, a scheduled task, any of them. A chat-only session counts:
**if no code moved, that is itself the entry.** Think of each entry as a mini
exit-interview for the exchange that produced it, so a new chat can pick up
cold.

**Never edit a past entry. Append only.** Newest on top. If an old entry turns
out to be wrong, say so in a new entry — do not rewrite history. (The one
exception is a repo-wide mechanical rename, where every reference is repointed
in a single change; the entry that does it says so explicitly.)

Distinct from [`INTERVIEW.md`](INTERVIEW.md), which is the *current* state of
play: the worklog is the granular, per-exchange trail.

**Entry format** — the `Cost:` line is mandatory.

```
## YYYY-MM-DD — <one-line title>  ·  <Cowork | Claude Code>
- **Asked:** what the human requested.
- **Did:** what actually changed (files, decisions).
- **Decided / open:** verdicts reached, and what's still awaiting a call.
- **Next:** the single immediate next step.
- **Cost:** time and/or tokens this session spent. If it was not measured, say
  `unmeasured` and why — never omit the line.
```

---

## 2026-08-21 — PRIORITY P3: R7 closed unmeasured, on Arpit's call  ·  Claude Code

- **Asked:** execute P3 (measure R7 for real, pre-registered, in fux-lab).
  Mid-recon, Arpit asked the purpose and the odds; a cheap preliminary check
  (this repo's own committed index) put FAIL at ~70–80 % and Arpit chose to
  cancel the full ~1–2 hour run and close R7 on that signal instead.
- **Did:** measured this repo's own `.fux/index/` (345 real docs) two ways —
  per-field byte composition (`terms`/postings = 91.3 % of bytes, `code`/dense
  vector only 0.4 % — the earlier compression-risk hypothesis was wrong) and
  real git-pack compression in an isolated scratch repo (**2.429×**, measured,
  not assumed). Extrapolated linearly to 100k docs: **~470 MB, ~1.97× over the
  250 MB budget**. Found the threshold was sized against `ADR-POSTINGS`'s
  designed BIC/MPH encoding (⏳ proposed, unbuilt) — what's actually committed
  today is plain JSON (hex-string keys, no delta/quantization), so the number
  measures the wrong artifact. Filed
  `work/regression/2026-08-21-r7-preliminary-analysis/` (`report.md` +
  `ANALYSIS.md` + reproducible `evidence/`, **no `VERDICT.md`** — none is
  claimed, since no pre-registration exists to rule against). Reconciled
  `OPEN-WORK.md` (R7 row, W-26's inherited note), `PRIORITY.md` (P3 → DONE,
  cancelled not measured), `regression/README.md`'s index, and the two ADRs
  (`0009`, `0013`) whose veto checks cited `du -sh` (working-tree size) as
  "packed" — corrected to the real isolated-pack method, with the caveat
  inline.
- **Decided / open:** explicitly **not** treated as triggering P3's
  "wire format is dead" consequence — that was written for a measured FAIL
  against the real intended encoding, and this analysis measured neither a
  pre-registered run nor the real encoding. Left open: whether to prioritize
  building `ADR-POSTINGS`'s compact encoding now (plausibly closes the gap —
  a raw 8 B binary key alone roughly halves the dominant `terms` field's
  bloat) — flagged as the natural next step, not started. Corpus
  representativeness (this repo's docs vs. R7's intended synthetic corpus)
  is stated as unresolved, not glossed over.
- **Next:** Arpit's call on whether `ADR-POSTINGS` gets built next, or
  something else in `PRIORITY.md` takes priority (P4 onward).
- **Cost:** unmeasured precisely; one background recon agent plus this
  session's own analysis/edits, order of 30–40 minutes wall-clock — far under
  the ~1–2 hours the cancelled full run would have cost.

---

## 2026-08-21 — PRIORITY P1+P2: Law zero enforces the owning record; bulk reconciliation  ·  Claude Code

- **Asked:** "in priority file implement P1 and P2" — `work/PRIORITY.md`'s two
  top rows.
- **Did — P1** (`tests/adr_lib.py` new, shared table/owner parsing so the
  freshness gate and the ownership twin can't disagree): `ci.yml` gets
  `fetch-depth: 0`; `test_adr_freshness.py` now requires the **owning** record,
  not any record touched; its escape hatch is anchored to a whole line;
  `scripts/adr-guard.sh` moved from `pre-commit` (which reads the previous
  commit's leftover message) to `commit-msg`, rewritten portably (macOS's `awk`
  lacks gawk's 3-arg `match()`); new `test_adr_owns_consistency.py` checks each
  record's own `Owns:` line against the register. Verified live: staged
  `src/fux/query/` + an unrelated record, confirmed both the pytest check and
  the bash hook refuse it, confirmed the escape hatch and the owning-record
  case both pass, then reverted before committing anything.
- **Did — P2:** fixed the drifts P1's stricter check surfaced plus the audit's
  named list — three overlapping `Owns:` claims; ADR-MAINTENANCE/ADR-REFER's
  stale R4/R5/R6 status lines; ADR-CLI's verb count; ADR-DOTFUX's
  `fetcher/`→`fetchers/` and `cache/`→`runtime/fetch-cache/` (source fixed to
  match — `fuxdir.py`'s `DERIVED` dict dropped the unused top-level `cache`
  reservation); the `FetchError` subclass CLAUDE.md's error contract forbids,
  replaced with plain `FuxError` in `src/fux/refer/` + its tests; two
  self-contradicting records; ADR-REFER 5a's L2 relationship stated
  explicitly; ADR-GRAPH's veto repointed off retired query ids; the register's
  stale `work/adr/` header; 10 dead links; 4 archive-as-reference citations;
  stale CLAUDE.md/README facts. R4–R6/regression-README/r5-ANALYSIS.md were
  already reconciled in `a8adb22` — checked, not redone. `docs/adr/RULE-SINCE`
  written naming the reconciliation commit (`1fc51a7`), in a follow-up commit
  since it names its own sha.
- **Decided / open:** both flipped `DONE` in `PRIORITY.md`, evidence `1fc51a7`.
  `sources/types` and ADR-ANSWER's `"source"` field were checked and found
  **not** drifted — noted, not silently skipped. Two remaining test failures
  are **pre-existing and not mine**: `tools/graph-bench` (untracked, no owning
  record) and its own new regression run missing a README row — both belong to
  a concurrent session actively working in this repo during mine (confirmed:
  new untracked files and a fresh `work/regression/2026-08-21-*/` run appeared
  mid-session, and the shared git index got broadly `git add`-ed by that
  session partway through — my commit used explicit pathspecs, listing only
  my 28 files, to avoid capturing or disturbing that other work). Left
  entirely alone.
- **Next:** P3 (measure R7 on a real 10⁵-doc corpus) is next in `PRIORITY.md`
  order but was not asked for this session and was not started.
- **Cost:** unmeasured precisely; three parallel research agents plus this
  session's own edits/tests, order of tens of minutes wall-clock.

---

## 2026-08-20 — the prediction series reopened: R4 passes, R5 fails, R6 cannot say  ·  Claude Code

- **Asked:** implement the predictions measurement so the rest can proceed;
  then, mid-session, clear closed items out of OPEN-WORK and report where R5
  stood.
- **Read as:** Arpit lifting the hold on prediction runs (W-61 DoD box 1). Said
  so before starting rather than after.
- **Did — pre-registrations first, committed before any number existed**
  (`d98874d`): `tools/refer-bench/PRE-REGISTRATION.md` (R4) and
  `tools/maintenance-bench/PRE-REGISTRATION.md` (R5, R6). The second opens with
  a disclosure, because the harness had already been run once before the hold
  was visible on disk; those numbers were never filed and describe a build that
  no longer exists. R5's judged corpus size is fixed there by an argument that
  never mentions the data.
- **R4 — PASS.** Cold k=10 p95 **1.113 s** / 3 s, warm **0.016 s** / 300 ms,
  through the *shipped* consumer fetcher against a real loopback server. The
  verdict carries its own boundary: the plane fetches **serially**, so cold cost
  is `k ×` the source's latency; the 500 ms arm breaches at 5.069 s, and paper
  §8's "(k=10, parallel)" is not built. Two harness defects are recorded rather
  than quietly fixed — a fetcher passed as a module (every fetch degraded to
  `unverified`; **1.9 ms and a triumphant-looking pass**) and markdown served as
  `text/plain` to an HTML→markdown fetcher (whitespace collapsed, zero
  citations). Both are now guarded by fields in every report.
- **R5 — FAIL.** **44.4 s** at the judged 100 000 documents against a **1 s**
  bound; **0.651 s at 1 000**, where it passes. Attributed rather than left as
  *it is slow*: git is ~constant (0.34 s at 100k) and two O(corpus) passes are
  the whole cost, 51.5 % ingest / 47.6 % derive. **A 10× speedup still misses by
  4.5×** — only taking the work off the commit path reaches the bound.
- **R6 — INCONCLUSIVE, and the engine is not the reason.** Every tier matched;
  tiers 2 and 3 are informative against a **control arm** run with the driver
  unregistered. Tier 1 merged cleanly *without* the driver, so it proves
  nothing, and the frozen table does not cover "all match, some informative".
  The control arm was added while writing the pre-registration and justified
  itself on its first execution.
- **Decided / open:** **two calls now sit with Arpit** — the fork R5 opened
  (`work/compare/hook-at-scale.compare.md`, proposed **B, the hook defers**),
  and whether R6 reads as PASS under its own §3.1 or not-yet under §3.2, which
  disagree about this exact result. **ADR-MAINTENANCE stays `proposed`**, now
  for the opposite reason to before: not unmeasured, but measured and failing.
  ADR-REFER also stays `proposed` — one gate is not W-59's DoD.
- **Also:** OPEN-WORK reconciled — it already had 7 rows / 7 detail files, but
  carried three closed items' fingerprints (R5/R6 "measured at W-25"; "fux-lab
  is gone (W-56)"; M3/M4 "behind W-56"). All corrected. W-26 is now the only
  agent-closable item on the queue.
- **Not done, deliberately:** the hook was not tuned to pass — `src/` last
  changed in `3a9aabc`, before the pre-registrations — and tier 1 was not
  re-specified in the same change that files its verdict.
- **Next:** Arpit rules on `hook-at-scale.compare.md` and on R6's arithmetic.
  W-26 (M6) is startable meanwhile.
- **Cost:** **unmeasured, and now known to be unmeasurable retroactively** —
  `cage.toml` has no `[sources]`, so the ledger captured nothing this session
  and `cage import` pulls 0 calls. Roughly three hours wall-clock, most of it in
  100 000-document corpus builds.

## 2026-08-20 — queue review: one startable item, and a status that said the opposite of the repo  ·  Claude Code

- **Asked:** which OPEN-WORK items are unblocked and workable.
- **Did:** re-derived every row against `git log`, the detail files and the
  repo (rule 4). **W-61 is the only agent-startable item** — and its markers
  were stale: the row read `held — Arpit's word required` and the detail file's
  `Blocked by:` line named the hold, but Arpit lifted it on 2026-08-20 and
  `d98874d` committed the R5/R6 pre-registration the DoD asked for. Corrected
  both, ticked the two DoD boxes that are actually met, and fixed the
  predictions table, which claimed R5/R6 were *running* when they are
  pre-registered and **unrun**. DOC-REGISTRY rows bumped. No code changed —
  **no ADR affected**.
- **Decided / open:** W-26 stays gated behind R5/R6 filing. W-59's remainder
  (budget sweep) and W-57 are `arpit` — the goldens are human work. W-44/W-52/
  W-38 remain parked on triggers that have not fired. The inbox is empty, so
  nothing is aging against the 5-day rule.
- **Next:** run W-61 — R5 per corpus size and R6's three tiers with their
  control arms, against the frozen pre-registration, filed as a conformance run.
- **Cost:** unmeasured — short review session, no token tracking enabled.

## 2026-08-20 — W-58 closed: option D, no age bound  ·  Cowork
- **Asked:** what's blocking W-58; then, mid-discussion, Arpit ratified option
  D (no age bound) from `record-freshness.compare.md`.
- **Did:** compare doc flipped to `status: accepted` with the decided verdict;
  [ADR-REFER](../docs/adr/0031_refer-plane.md) decision 4 and veto condition 3
  amended to record the closure; `work/open/W-58-no-recorded-ingest-time.md`
  marked CLOSED and copied to `archive/open/` (the original in `work/open/`
  could not be `git mv`'d/removed from this session — no git access over the
  device bridge; still needs `git rm`); `OPEN-WORK.md`'s inbox and open-items
  row for W-58 removed.
- **Decided / open:** **D is final** — no ingest time is added to the
  committed record; content-sha verification is the answer, and
  `max_age_seconds` stays struck. Reopen trigger unchanged: R4 shows warm-path
  fetch cost dominating and a caller willing to trade staleness for latency,
  at which point build E (corpus-level stamp), not A/B/C.
- **Next:** a git-capable session should `git rm work/open/W-58-no-recorded-ingest-time.md`
  (superseded by the `archive/open/` copy) and bump the `DOC-REGISTRY.md` rows
  this touched (`docs/adr/`, `OPEN-WORK.md`, `compare/*.compare.md`, `open/`) —
  skipped this session to avoid colliding with the concurrently active local
  session editing those same rows.
- **Cost:** unmeasured — interactive Cowork session, no token/time tracking
  enabled.

## 2026-08-20 — delta ingest: a veto condition fired, and W-25/W-60 were taken by a concurrent session  ·  Claude Code

- **Asked:** implement W-25 and W-26, and W-60 too, as fast as possible.
- **Found first, and it changes the entry:** a **concurrent session shipped W-25
  as `621c83c` mid-session** (ADR-MAINTENANCE, `tests_e2e/test_maintenance.py`,
  W-61 filed) and swept in this session's `tools/maintenance-bench/run.py`,
  `tests/maintain/*` and `tests/store/test_meta_policy.py`, which it says
  plainly in its own commit message. It then began **W-60** —
  `src/fux/refer/fetchcache.py` and the amended `freshness.py` appeared on disk
  while this session was mid-edit. **W-60 was therefore not touched here**;
  racing a live build would have corrupted both.
- **Ran R5/R6 before the hold was visible.** The maintenance harness was run at
  ~11:05, and the hold on prediction runs was recorded in W-61 at ~11:13. The
  numbers exist and are **not filed as a verdict**: R6's three tiers passed;
  R5 measured 3.4 s at 1 000 documents and 17.2 s at 5 000 against a 1 s bar,
  which is a *failing* number for a build that no longer exists.
- **Did — the session's own contribution, and the reason that number moved:**
  **delta ingest.** ADR-INGEST's veto condition named "full re-extraction
  becomes the measured bottleneck at scale" as the thing that would reopen
  decision 1. A filed cost profile
  (`work/regression/2026-08-20-ingest-cost-profile/`) supplied it: **92 % of a
  full ingest is `_fuxvec_code`**, the dense embedding, at 1 k and 5 k alike.
  So extraction is now carried forward for an unchanged `sha` (decision **1b**)
  while **edges re-resolve every run** — 22.7× / 26.4× faster, **byte-identical**,
  with `fux ingest --full` as the escape hatch. ADR-INGEST and ADR-CLI amended
  in the same change; `tests/ingest/test_delta.py` asserts byte-identity after
  an edit, an addition and a deletion. 806 tests pass across both suites.
- **Decided / open:** **W-26 was not started, and should not be.** Its DoD
  requires every R prediction to carry a measured value or an honest failure
  record, and R4/R5/R6/R7 are all unrun under Arpit's hold. Building `tpack`
  and a T2 tier now means choosing the tier-auto threshold by hand and then
  looking for evidence for it — the inversion the pre-registration rule exists
  to stop. Two guarantees were **narrowed and written down** rather than
  glossed: term-hash collision detection is complete only under `--full`, and a
  newly available embedding bundle does not retro-fit `code`.
- **Next:** Arpit's word on lifting the hold on prediction runs — R5 is now
  worth re-running, because it is measuring a different engine.
- **Cost:** unmeasured (no token counter wired into this surface); roughly one
  hour of wall-clock, most of it in the corpus builds the profile needed.

## 2026-08-20 — W-60 ratified: option F  ·  Cowork

- **Asked:** "Let's go with option F" for the refer-plane fetch cache; then,
  "does this unlock W-58?"

- **Did:** marked `refer-fetch-cache.compare.md` **accepted** as proposed
  (default `cache_ttl_seconds = 300 s`, build proceeds without waiting on R4,
  on the Confluence-rate-limit rationale). Updated
  [`compare/README.md`](compare/README.md), W-60's detail file (DECIDED
  header, DoD's ratification item checked), and
  [`OPEN-WORK.md`](OPEN-WORK.md) — W-60 out of the Blocked-on-Arpit inbox
  (back to one: W-58) and into the `agent` lane, build-ready, Model: Opus.

- **Decided / open:** **W-58 is not unlocked.** record-freshness's verdict D
  (does the *committed record* need a timestamp — no) and W-60's verdict F
  (should the *runtime cache* carry a wall-clock timestamp — yes) are
  independent forks answering different questions; ratifying one carries no
  information about the other, and both compare docs say so explicitly.
  W-58/record-freshness stays ⏳ awaiting Arpit on its own terms — the inbox
  still shows it, alone.

- **Next:** W-60 is build-ready — a Claude Code session can execute it
  (Opus), amending ADR-REFER in the same change per Law zero. Separately,
  W-58/record-freshness still needs its own verdict whenever Arpit wants to
  take it.

- **Cost:** unmeasured — a short ratification exchange; no per-session token
  meter was read.

---

## 2026-08-20 — refer-plane fetch cache researched and filed as W-60  ·  Cowork

- **Asked:** what's blocked on W-58 (answered from the repo); then, separately,
  Arpit described an idea — cache non-git-sourced documents locally with a
  fetch timestamp, expose an age/freshness property, refetch-and-update the
  cache when it's stale, then answer — and asked for research on whether it's
  sound, followed by a document to implement it.

- **Did:** read [record-freshness](compare/record-freshness.compare.md),
  [ADR-REFER](../docs/adr/0031_refer-plane.md), and
  [ADR-RUNTIME-STAMP](../docs/adr/0028_runtime-stamp.md) to place the idea
  against what's already decided. Researched `stale-while-revalidate` (RFC
  5861) and Confluence Cloud's REST API rate limits (65,000-point/hour shared
  pool; Atlassian's own guidance is "cache stable responses" and "use ETags
  and conditional headers"). Wrote
  [`refer-fetch-cache.compare.md`](compare/refer-fetch-cache.compare.md)
  (proposed verdict F) and its item,
  [W-60](open/W-60-refer-fetch-cache.md); added both to
  [`OPEN-WORK.md`](OPEN-WORK.md)'s inbox (now two) and its
  ADR-GRAPH/ADR-REFER/ADR-RECORD group, and to
  [`compare/README.md`](compare/README.md)'s table.

- **Decided / open:** the *shape* is sound and reuses an already-accepted
  pattern rather than inventing one — a gitignored, wall-clock cache-entry
  timestamp (same treatment `stamp.json` already gets under
  ADR-RUNTIME-STAMP) never touches the committed record, so it does **not**
  reopen [W-58](open/W-58-no-recorded-ingest-time.md) or
  [record-freshness](compare/record-freshness.compare.md)'s verdict D — those
  stay exactly as they were. It **does** need a new, explicitly separate
  fourth verdict state (`cached`) so [ADR-REFER](../docs/adr/0031_refer-plane.md)
  decision 6's "never collapse 'we did not look' into 'we looked and it was
  fine'" guarantee survives, and it must live in its own store, never inside
  ARC's keyspace, because ARC's "cannot change the answer" proof depends on
  being keyed by an already-known-correct sha. **Two numbers are still
  Arpit's call**, both left open in the compare doc: the default
  `cache_ttl_seconds` (300 s proposed) and whether to build now on the
  Confluence-rate-limit rationale rather than wait for R4 — record-freshness's
  own reopen-trigger wanted R4 first, but the rate-limit case is a second,
  independent justification that document never had in view.

- **Next:** Arpit ratifies (or amends) `refer-fetch-cache.compare.md`'s
  verdict; once ratified, W-60 is build-ready (Model: Opus, per its own
  detail file) and ADR-REFER gets amended in the same change that builds it.

- **Cost:** unmeasured — a research-and-drafting exchange; no per-session
  token meter was read.

---

## 2026-08-20 — W-27 closed by Arpit's direct ratification, not the retired gate  ·  Claude Code

- **Asked:** review `work/open/` and archive whatever is complete; separately,
  Arpit then stated directly that W-27 is implemented and should close, with
  one ongoing requirement — dogfood tracking updated on every fux version
  upgrade.

- **Did:** first pass found nothing in `work/open/` complete against
  `IMPLEMENTATION.md`/repo state (all 9 items genuinely open — W-56's lab and
  playground scaffolding was mid-build by a concurrent session, goldens
  correctly not yet fabricated). On Arpit's explicit instruction, closed
  **W-27** (M7 dogfood & release gate) directly: its retired DoD (two weeks of
  logged daily use in fux + Anton, ending in a release Arpit had used) was
  never measured, and W-27 was still `blocked by W-26` (M6, unstarted) under
  that gate. Arpit overrode both and ratified closure on the fact that fux
  already dogfoods itself in this repo (`.fux/` self-indexed). Row deleted
  from `OPEN-WORK.md`; detail file moved to
  [`archive/open/W-27-m7-dogfood-release-gate.md`](../archive/open/W-27-m7-dogfood-release-gate.md);
  outcome recorded in `IMPLEMENTATION.md`'s Ratified decisions table; new
  [`DOGFOOD.md`](../DOGFOOD.md) created as the standing artifact for the
  replacement obligation; `DOC-REGISTRY.md` bumped for all four touched docs.

- **Decided / open:** **W-27's original DoD is not met and was not
  re-verified** — this is a human call recorded as such, not a measured
  closure. The replacement obligation (`DOGFOOD.md` refreshed on every version
  bump) has no log entries yet; nothing has shipped since `0.33.0`.

- **Next:** the agent lane's live blocker is [W-57](open/W-57-graph-lane-acceptance.md)
  (goldens need hand-grading) per the current inbox — W-56 already closed by a
  concurrent session during this exchange.

- **Cost:** unmeasured — no per-session token meter was read.

## 2026-08-20 — W-45 and W-55 were already closed; verified rather than rebuilt  ·  Claude Code

- **Asked:** implement W-45 and W-55 so they can be closed.

- **Did:** nothing to build. Both landed earlier the same day in `9ba02b1`
  ("what fux indexes, decided and built as one change"), and the closure is
  complete on every axis the rules require — no rows in
  [`OPEN-WORK.md`](OPEN-WORK.md), detail files moved to
  [`archive/open/`](../archive/open/), the outcome row in
  [`IMPLEMENTATION.md`](IMPLEMENTATION.md) line 50,
  [ADR-TYPES](../docs/adr/0032_types-list.md) accepted in the register, working
  tree clean. Re-derived per OPEN-WORK rule 4 rather than read off a marker:
  `git show --stat 9ba02b1`, the archive listing, and a full suite run —
  **719 passed** (`tests` + `tests_e2e`), matching the number that commit
  claims.

- **Decided / open:** no new decision. The ⚠ that rode with `9ba02b1` still
  stands and is *not* part of W-45/W-55: the type filter is a ranking change
  and this repo's committed index was deliberately not re-ingested, so the
  corpus change remains a separate measured step alongside
  [W-52](open/W-52-df-over-the-union.md) — which is **PARKED** on a
  pre-registration that does not exist.

- **Next:** the agent lane's `next` is [W-56](open/W-56-sibling-environments-missing.md)
  — rebuild `fux-lab` and the playground corpus; all four unmeasured
  predictions (R4–R7) are behind it.

- **Cost:** unmeasured — a verification exchange; no per-session token meter was
  read.

## 2026-08-20 (later) — the rest of the agent lane: W-45+W-55, W-56, M5, W-60  ·  Claude Code

- **Asked:** commit everything; **hold prediction runs until told explicitly**;
  review the rest of OPEN-WORK and implement every non-blocked item so it can
  be closed.

- **Did:** five commits, `773 → 804` tests, `adr-guard` exit 0 throughout.

  - **Committed the working tree** (`9dcf878`), most of it three concurrent
    sessions' work, with provenance recorded rather than implied. **The tree
    was red** — `work/NOW.md` had no DOC-REGISTRY row — and that one-line fix
    is the only content of mine in it.
  - **W-45 + W-55 closed as ONE grammar change** (`9ba02b1`). `!` exclusion
    entries in `.fux/sources/dirs`, and a compiled-in prose allowlist
    replaceable by `.fux/sources/types`. **`fnmatch` is not used** and that is
    load-bearing: its `*` crosses `/`, so `work/regression/*/evidence` would
    also have matched `.../a/b/evidence`.
  - **W-56 closed** (`ab1f673`) — **both sibling environments rebuilt and now
    under git**, which neither was.
  - **M5 shipped** (`621c83c`) — hooks, the merge driver, L5 at write time.
  - **W-60 shipped** (`3a9aabc`) — the TTL fetch cache, verdict F.

- **Decided / open:**

  - **The hold is honoured.** R4, R5, R6 and R7 are all unrun. Two records —
    ADR-REFER and ADR-MAINTENANCE — are **`proposed`, not accepted**, precisely
    because of it, and each says so in its own consequences.
  - **`post-commit`, not `pre-commit`,** and the argument is recorded:
    pre-commit reads the *working* tree, so with `git add -p` it indexes bytes
    nobody committed and writes them into the commit. **Wrong beats late**, so
    the index lags one commit and the lag is visible.
  - **The merge driver refuses in four cases** and never picks a side. Verified
    by **control and treatment**: the same merge conflicts without it and
    merges cleanly with it. Without the control it could have been doing
    nothing and the test would still have passed.
  - **A real bug found by running rather than reading**, in the driver's own
    branch order: a one-sided *add* was being treated as a delete-vs-modify, so
    every disjoint addition would have conflicted. That is the common case.
  - **Three bugs in the rebuilt lab, all found by running it**: `read -r` under
    `set -e` exiting silently with no output at all; the system `python3` being
    3.9 against fux's ≥3.11, which surfaces as a pip error listing every
    version ever published; and the harness printing **its own** interpreter
    beside the latency rather than the engine's.
  - **The playground's ~50 goldens were deliberately not rebuilt.** A golden
    derived from the engine's own output passes forever, including on the day
    ranking breaks. The corpus was written instead to make re-grading possible,
    and the phenomena verified to reproduce — *"what replaced helix mesh"*
    returns the superseded doc above the ADR that replaced it.
  - **W-57 had to be re-scoped**: `q005`/`q009`/`q011`/`q015` were ids in the
    lost golden set and cannot be recovered, so its targets are now phenomena.
  - **Every prior lab number is unreproducible**, including R3's 27.2 ms — the
    `rfc` corpus is gone. The M2 report's Reproduce block is **annotated, not
    edited**, because editing a filed run's evidence is itself forbidden.
  - **W-26 (M6) is NOT startable**, and I did not start it. Its DoD requires
    every R measured, and building `tpack` + T2 now would mean **hand-picking
    the tier-auto threshold the DoD forbids hardcoding**. Recorded in the item
    rather than left looking available.
  - **Two things landed that a concurrent session had already decided**, and I
    checked before assuming: `maintenance-trigger.compare.md` had ruled hooks
    (matching what I built) and left one sub-decision open, which
    ADR-MAINTENANCE now answers.
  - **Noticed, not acted on:** `CLAUDE.md` was edited directly by a concurrent
    session, and its own §Documentation discipline says agent-steering files
    are "proposed, never auto-applied — Arpit's to ratify". Presumably he
    directed it; nothing in the file records who ratified it.

- **Next:** **Arpit's, in three places.** Lift the hold when ready — the
  harnesses and both environments are now in place, so W-59 and W-61 can run
  the moment he says. Give W-58 its verdict. And **write the playground's
  goldens** (W-57), which is the only step here no agent should take.

- **Cost:** `unmeasured` — no `.cage/` ledger in this repo, so capture does not
  reach it. Five commits; +31 tests on top of the earlier session's +134.

## 2026-08-20 — closed the queue's agent lane: W-46, W-48, M3 and M4's core  ·  Claude Code

- **Asked:** review everything in OPEN-WORK and build the items to closure.

- **Did:** four commits. Triage first — the inbox was empty and five items were
  agent-closable, so the session proceeded.

  - **W-46 closed** (`9a8074f`). `get_model()` returns `None` on a source
    install and `None.embed(...)` raises `AttributeError`, which the guard's
    narrow tuple did not list — **the fallback written for exactly this case
    was dead from the day it was written**. Fixed with an explicit `None`
    check, not a wider `except`, and both halves are asserted.
  - **W-48 closed** (same commit). `ask --json --explain` now carries `"path"`;
    `answer --json` carries `"source"` on both branches — which makes
    ADR-ANSWER's own veto check true for the first time. **Item 3 was examined
    and deliberately left alone**, and is now pinned by a test so the decision
    is visible rather than remembered.
  - **W-45's compare doc written** (`d26e8fe`), from a fresh measurement rather
    than the item's prior write-up. Options C and D are **eliminated by
    measurement**: every contaminating file is git-*tracked*, and the
    dot-prefix convention was followed by 2 of 7 filed runs and dropped by the
    other 5. Proposed verdict is an exclusion **entry**, not the attribute
    ADR-DIR-LIST anticipated.
  - **W-23 / M3 shipped** (`a7b224a`) — `explain`/`graph`/`path`, unseeded
    label-propagation communities in a derived plane, PPR-lite. **The archived
    relational eval passes on the new kernel, 11/11.**
  - **W-24 / M4's core shipped** (`9238d4b`) — source · freshness · ARC ·
    chunk · rescore · assemble, 73 tests. Its spec was written into the item
    first (it had none), then the item was closed.

  Suites: **681 passing** across `tests` + `tests_e2e`, up from 547.

- **Decided / open:**

  - **Three things were refused rather than built, each on a fact:**
    (1) `max_age_seconds` — the record carries **no ingest time**, so the knob
    could not have been honoured and shipping it would have shipped one that
    silently does nothing (**W-58**); (2) a *seeded* community algorithm —
    removing the randomness is the stronger guarantee, asserted by parsing the
    module's AST; (3) wiring the refer plane into any verb — its gate has not
    run.
  - **Two defects were found by measuring rather than reading.** The archived
    PPR walk, truncated at 3 iterations, **ranks by parity** — seeded at `a` on
    a path `a-b-c-d` it scores `d` (3 hops) above `c` (2 hops). Fixed with a
    lazy walk. And greedy score-per-byte is **systematically biased toward
    short passages**, so the assembler grew a floor.
  - **The ARC differential caught a live defect while being written** — the
    cache-hit path leaked cache state into the answer's `note`.
  - **The biggest finding is not code: `fux-lab` and `fux-playground` are both
    gone from this machine** (**W-56**). The lab is the one the standing
    obligation says is never deleted; the playground held 50 graded goldens
    with **one local commit and no remote**. Between them they are the
    instrument for **R4, R5, R6 and R7** — every unmeasured prediction left —
    and M2's own filed reproduce commands point into the lab and no longer run.
  - **Nothing about M3 or M4 is claimed as measured.** ADR-GRAPH is accepted
    but names its two unmeasured gaps (**W-57**); **ADR-REFER is `proposed`,
    not accepted**, because R4 has not run (**W-59**).
  - **Also filed:** W-55 (the walker has **no file-type filter** — 14 % of this
    repo's index is `.json`/`.svg`/`.sh`/`.py`), found while measuring W-45. A
    concurrent session picked it up and wrote its compare doc.
  - **Two deviations from a written DoD, stated rather than hidden:** W-46's
    regression test landed beside the other hybrid tests instead of in
    `tests/query/` (duplicating a corpus fixture costs more than the path
    documents), and W-23's "two machines" determinism check ran on one.
  - **Concurrent sessions were live throughout** — three other Claude Code
    processes. `.fux/` was being rewritten by one of them and was left
    untouched; every commit used explicit paths rather than `git add -A`; the
    queue was re-read and re-reconciled before each write.
  - **Stale fact noticed, not fixed:** `CLAUDE.md` tells every session to get
    its cost from `cage report`, and **`cage report` was removed in cage v0.50**
    (`SURFACE-CUT`). Left alone because a concurrent session had `CLAUDE.md`
    staged; it is a one-line fix for whoever touches that file next.

- **Next:** **Arpit reads the inbox — W-56 first.** It blocks W-57 and W-59 and
  every remaining prediction, and an agent cannot fix it. Then W-58. On the
  agent lane, W-45 and W-55 are both decided and land as **one** grammar
  change; after that, **W-25 (M5) is next and unblocked** — its build is, its
  R5/R6 gates are not.

- **Cost:** `unmeasured` — this repo has no `.cage/` ledger, so capture does not
  reach it (`cage insights chats` → "No chats recorded yet"). Wall-clock: one
  long session; four commits, +134 tests.

## 2026-08-20 — reconciled OPEN-WORK; nothing was removable  ·  Claude Code
- **Asked:** review `OPEN-WORK.md` and remove whatever is done.
- **Did:** re-derived all ten rows against the code rather than reading their
  markers (rule 3), and **removed nothing, because nothing is done**:
  - **W-46** — `query/hybrid.py:97` is still `get_model().embed(query)` with an
    `except` tuple that omits `AttributeError`. The `None` guard the DoD asks
    for is absent. Real, unfixed.
  - **W-48** — `cmd_ask` still returns at the `--json` branch before the
    `--explain` block, and `cmd_answer`'s no-match `--json` is still
    `{"answer": null, "citation": null}` with no `"source"`. Both open.
  - **W-45** — no `source-exclusion.compare.md` in `work/compare/`.
  - **W-44 · W-52** — the only pre-registrations in the tree are the two
    pruning ones; no live-vs-archived query set exists, so both stay PARKED.
  - **W-23 · W-24** — no `explain`/`graph`/`path` verb in `cli.py`;
    `src/fux/refer/` is still the 7-line stub.
  - **W-25 · W-26 · W-27 · W-38** — blocked downstream, unchanged.
  - Also verified W-46's and W-48's DoDs still describe reality: ADR-CLI still
    carries the "we now owe a regression test" line and the `ask --hybrid`
    known-defect note, so neither item's spec has rotted under it.
- **Decided / open:** **two stale facts fixed on contact**, which is the other
  half of rule 3 — a stale row understates as badly as a stale ✅ overstates.
  The footer claimed `v0.32.0` is on PyPI (it is `0.33.0` since yesterday), and
  **W-45 was grouped under ADR-CONFIG and led with the retired `[sources] dirs`
  key**. Regrouped under **ADR-DIR-LIST** — rule 7 says an item's group is the
  record its change will have to update, and an exclusion attribute on a
  directory line is that record's now, not ADR-CONFIG's. Its detail file was
  repointed at `.fux/sources/dirs` in the same edit; the finding is unchanged.
- **Next:** the queue's own recommendation stands — **M4 ([W-24](open/W-24-m4-refer-plane.md))
  first, and it has no live spec**, so write one into its detail file by Opus
  before any code. W-46 is the cheapest real fix on the board if a short
  session wants one.
- **Cost:** unmeasured — `cage report` was removed in Cage v0.50 (SURFACE-CUT)
  and `cage insights chats` reports nothing for this repo, so capture does not
  reach it. A read-and-verify session; no code changed.

## 2026-08-19 — v0.33.0 released to PyPI  ·  Claude Code
- **Asked:** step 4 of the W-54 prompt — release, only if everything above was
  green. It was.
- **Did:** bumped `src/fux/__init__.py` to `0.33.0`, cut `[Unreleased]` into
  `## [0.33.0] - 2026-08-19` with both breaking migrations shown as diffs,
  fixed the version facts in `CLAUDE.md` and ADR-CLI's Feature line (statements
  of fact, fixed on contact), tagged, pushed, and created the GitHub Release —
  which is what triggers `publish.yml` and its OIDC trusted publishing. **CI
  green (12 jobs) and the publish workflow green**, both checked rather than
  assumed. `fux-engine 0.33.0` is on PyPI, verified black-box: installed the
  published wheel into a clean venv and ran `fux setup` → `fux url` →
  `fux ingest` → `fux ask` in a fresh repo.
- **Decided / open:** the release notes state the honest limits in the same
  breath as the claim — **nothing in this release exercises real HTTP**, the
  `archived=` declaration parses and is deliberately unread, and no new timing
  was measured (the 27.2 ms / 4 248.8 ms figures are cited from the M2 run, not
  re-derived on a seven-document fixture).
- **Next:** M3 ([W-23](open/W-23-m3-graph-lane.md)) or M4
  ([W-24](open/W-24-m4-refer-plane.md)), both unblocked. **M4 first is the
  standing recommendation and it has no live spec** — write one into its detail
  file, by Opus, before any code.
- **Cost:** unmeasured — `cage report` was removed in Cage v0.50 (SURFACE-CUT)
  and `cage insights chats` reports nothing for this repo, so capture does not
  reach it.

---

## 2026-08-19 — W-54: the sources rewrite, five defects, five commits  ·  Claude Code
- **Asked:** execute W-54 end to end — commit the uncommitted documentation
  session first, then build the five sections in order, verify, close the item,
  and release `v0.33.0`.
- **Did:**
  - **Step 0.** The working tree's ~73 files were *fully staged and clean* —
    the prompt's warning about files appearing both staged and unstaged did not
    reproduce, and `git diff` was empty. Suite green (446 + 12) before the
    baseline commit `4c7dd5e`.
  - **§1** `ingest/sourcelist.py` — **one parser for both committed lists**.
    `#` is a comment only at line start or after whitespace, which fixes the
    silent fragment truncation and is *forced* by the whitespace-delimited
    attribute grammar rather than chosen. Built ADR-URL-LIST decisions 7–13:
    the closed attribute sets, the `file:lineno` errors, the
    duplicate-with-conflict error, reader-lenient/writer-strict. `fetch=` now
    routes to `<fetchers dir>/<name>.py`; `meta` resolves in three layers
    (built-in → source-wide → line).
  - **§2** `[sources] dirs` retired; the corpus lives in `.fux/sources/dirs`
    with `archived=` **parsed and not read**. Amended ADR-DIR-LIST decision 10
    to split the file from the signal, with the reason the line falls there.
  - **§3** `fux setup` + both fetchers as **package data with an extension
    Python cannot import** (`templates/*.py.txt`), so the adapter cap is
    structural. Wrote `http.py`, generating its HTML→markdown pass *from*
    `cdp.py` so a test can assert the two are identical. Verified from a real
    installed wheel, not just the source tree.
  - **§4** `title_h` → `"h:" + term_hash(...)`. Decided the migration: **no
    `_format` or `analyzer` bump** (ADR-INDEX-LIFECYCLE **decision 9**, three
    conditions plus the asymmetric-cost argument), and the build's refusal now
    names `fux ingest --refresh-urls` instead of reporting the symptom.
  - **§5** `fux url` — flags not a subcommand tree, writes every attribute,
    edits **one line** so a human's grouping comments survive.
  - **Verification.** Filed [`2026-08-19-w54`](regression/2026-08-19-w54/report.md)
    with a new fixture that builds a repo from nothing and runs the whole URL
    path offline. `fux ingest --refresh-urls && fux build` exits 0 on the L5
    default; a fragment survives; two fragment-differing URLs are two records;
    the differential holds over a corpus containing hashed records.
- **Decided / open:**
  - **Two places the work order lost to a record**, both stated in the commits:
    §5 describes a verb that *fetches*, and ADR-CLI's captured surface makes
    `--refresh-urls` the only networked path (L4) — `fux url` records and never
    fetches. And Step 2 said to extend the 2026-08-18 fixture; that fixture is
    a filed run's evidence and reproduces the pre-W-54 surface, so it got a
    forward pointer and a **new** fixture instead. A measurement is superseded
    by a newer measurement, never by an edit.
  - **ADR-HTTP-FETCHER decision 2 was wrong** and was amended: it said
    `ensure_layout` writes `http.py`, which would put 28 KB of code into every
    repo on its first ingest. Arpit's `fux setup` ruling is the fix.
  - **Three findings filed in ANALYSIS.md, not as items:** `fux doctor` should
    check the source lists (should ride with W-44), the generated
    `.fux/README.md` does not mention `dirs`, and the duplicated HTML→markdown
    pass is accepted rather than a defect.
  - **Nothing here exercises real HTTP.** Stated as unresolved.
- **Next:** release `v0.33.0` — bump `src/fux/__init__.py`, move
  `[Unreleased]` (already written, with both breaking migrations) into the
  release section, tag, and let the GitHub Release trigger the PyPI publish.
- **Cost:** unmeasured — `cage report` was removed in Cage v0.50 (SURFACE-CUT)
  and `cage insights chats` reports "No chats recorded yet" for this repo, so
  capture does not reach it. One long Claude Code session, ~7 commits.

## 2026-08-19 — six single-file companion ADRs for the `.fux/runtime/` files  ·  Cowork
- **Asked:** explained what's inside `.fux/runtime/postings/` and the six other
  generated runtime files (`CACHEDIR.TAG`, `docs.jsonl`, `codes.jsonl`,
  `manifest.json`, `stamp.json`, `stats.json`) in chat, then Arpit asked for
  "independent ADRs for each of these."
- **Did:** flagged first that `src/fux/derive/` is already claimed once by
  ADR-T1-ACCELERATOR (0011, accepted) and ADR-POSTINGS (0013, proposed), and
  that one-record-per-file would fragment an already-decided feature — Arpit
  confirmed he wanted it anyway. Wrote **six new proposed records**, none
  owning a module (`Owns (on acceptance): no module`, same pattern
  ADR-POSTINGS already uses), so the ownership table in
  [`docs/adr/README.md`](adr/README.md) needed no edit: **ADR-CACHEDIR-TAG**
  (0024), **ADR-DOCS-TABLE** (0025), **ADR-CODES-TABLE** (0026),
  **ADR-RUNTIME-MANIFEST** (0027), **ADR-RUNTIME-STAMP** (0028),
  **ADR-RUNTIME-STATS** (0029). Added register rows for all six, a prose note
  explaining why they own nothing, and cross-referenced all six from
  ADR-POSTINGS' Reference section as requested. Verified against the repo's
  own suite in a throwaway sandbox (copied `docs/adr/`, `fux/__init__.py`,
  `fux/frontmatter.py`, the two test files, and `OPEN-WORK.md`) — caught and
  fixed one real defect this way: 0024's Examples section used a bare
  ` ```text ` fence for a raw file dump, which `test_adr_ownership.py`'s
  mermaid-twin check requires to live inside a collapsed `<details>` block;
  switched it to a ` ```console ` block instead. `tests/test_adr_ownership.py`
  + `tests/test_adr_frontmatter.py` pass in full against the real register
  (148/149 in the sandbox; the one failure was the sandbox missing most of
  `src/fux/`, not a real defect). Bumped the `docs/adr/` row in
  [`DOC-REGISTRY.md`](DOC-REGISTRY.md).
- **Decided / open:** these six records stay **⏳ proposed** — Arpit has not
  ratified them, only asked for them to be written. `test_adr_freshness.py`
  (git-diff based) and `scripts/adr-guard.sh` were not run this session — no
  `src/` change was made, so they should be unaffected, but neither was
  verified directly.
- **Next:** none filed — this was a documentation-only exchange, not a
  `W-nn` item. If Arpit wants these ratified, that's a status flip on each
  frontmatter block plus the two-sentence prose that goes with acceptance
  elsewhere in the register.
- **Cost:** unmeasured — no `cage report` capture reaches this Cowork session.

---

## 2026-08-19 — `fux setup` answers the fetcher-delivery question  ·  Cowork
- **Asked:** where does a consumer's `cdp.py` come from — **at setup time,
  `fux setup`.**
- **Did:** recorded it in [W-54](open/W-54-sources-rewrite.md) §3. Both fetchers
  ship in the wheel as **package data** — bytes, never imported, so the adapter
  cap holds — and `fux setup` writes them **write-if-missing**. That closes what
  W-51 could not: `DEFAULT_FETCHER` names a file that will exist, without 28 KB
  of WebSocket code appearing unasked-for on a first ingest, and without telling
  an air-gapped consumer to fetch a file from GitHub.
- **Decided / open:** scaffolding now has **two moments, and the split is
  load-bearing**: `fux setup` is optional, explicit and once per repo, and it
  writes the fetchers; `ensure_layout` stays mandatory and idempotent at ingest
  and writes the layout — **and must never write a fetcher**, or ingest puts code
  into a repo that only wanted an index. That preserves ADR-DOTFUX decision 6
  exactly as Arpit ratified it in W-31 this morning. **The cost is a record
  change nobody has priced yet**: ADR-CLI opens with *"six verbs and no
  subcommand tree — three build the index and three query it, and the split is
  the whole mental model,"* and W-54 now adds **two** verbs. The sentence stops
  being true, and the fix is not to recount but to find the grouping the surface
  actually has — proposed in W-54 as lifecycle (`setup`, `doctor`) · write
  (`ingest`, `build`) · sources (the URL manager) · read (`ask`, `find`,
  `answer`), to be settled **in** the amendment rather than after it.
  **"No subcommand tree" is the constraint that survives**, and it is why the URL
  manager takes flags instead of becoming `fux url add`.
- **Next:** start **W-54**.
- **Cost:** unmeasured — no per-session token count available. One item updated;
  no code changed.

## 2026-08-19 — The register gains a `built` axis; five items merge into W-54  ·  Cowork
- **Asked:** add the built axis · merge the five sources items · keep the URL
  work even though this repo does not use it · park the two that are gated.
- **Did:** **the register gains a `built` column** — `yes` / `partial` / `no`,
  and a paragraph saying why the two questions are different: `status: accepted`
  means *Arpit ratified the decision*, `built` means *the engine does it*. Four
  records were accepted-and-unbuilt with nothing in the index saying so, which is
  the `CLAUDE.md` PROPOSED defect in a new place — one word meaning one thing to
  the writer and another to the reader. **A row with `no` or `partial` must be
  claimed by an open item**, or it is a wish; the mapping is stated. **W-54
  filed**, merging W-47 · W-49 · W-50 · W-51 · W-53, whose files moved to
  `archive/open/` marked **merged, not completed** — they are still five defects,
  they are one change. Twelve live docs repointed to the successor. W-44 and
  W-52 **PARKED with triggers**. Queue regrouped; every link resolves.
- **Decided / open:** the URL subsystem is fixed **even though this repo never
  exercises it** — no `.fux/sources/urls`, `[sources.url]` commented out, so all
  five defects are latent, shipped, and victimless until the first consumer hits
  every one of them on day one on the documented default. That is Arpit's call
  and the reasoning is in W-54's §Note, together with the consequence nobody
  should have to rediscover: **this repo's own corpus cannot catch a regression
  here** — the 2026-08-18 fixture is the only thing that exercises the path, so
  extend it rather than trusting `pytest -q tests`. W-44 and W-52 are parked
  rather than ordered, because both were gated on a pre-registered instrument
  that does not exist, is not an item, and has no owner — a gate whose
  precondition nobody owns is *"revisit when we scale"* with better manners.
- **Next:** **W-54**, and the first question in it is `cdp.py`'s fate.
- **Cost:** unmeasured — no per-session token count available. One column, one
  merge, two parks; no code changed.

## 2026-08-19 — Inbox section reduced; full review of the queue and the register  ·  Cowork
- **Asked:** the inbox section should carry open items or say **Empty.** and
  nothing else. Then review all open work and the ADRs, find what is pending,
  and grill so implementation can start.
- **Did:** reduced §Blocked on Arpit to two words when there is nothing in it —
  the prose that had accumulated there was explaining an absence, which is the
  same defect as a tombstone row. Re-derived the register and the queue against
  the tree.
- **Found:** **four accepted records describe code that does not exist** —
  ADR-ENRICHED, ADR-HTTP-FETCHER, ADR-DIR-LIST, and ADR-URL-LIST decisions 7–13.
  Each says so in its own body; **the register's status column does not**, and
  that column is what a session reads first. `accepted` currently means "the
  decision is ratified" to the writer and "this is how the engine works" to the
  reader — the same two-meanings-one-word defect the `CLAUDE.md` PROPOSED header
  was. Also: **five open items concern a subsystem this repo does not use** —
  there is no `.fux/sources/urls` and `[sources.url]` is commented out in
  `fux.toml`, so URL ingestion has never run here outside a fixture. And the
  milestone chain has not moved since `v0.32.0` on 2026-08-12.
- **Decided / open:** nothing decided; put to Arpit as a sequencing question.
- **Next:** his call on scope and order, then build.
- **Cost:** unmeasured — no per-session token count available. One structural
  edit; no code changed.

## 2026-08-19 — Source dirs get their own file; ADR-ARCHIVED-SIGNAL superseded the day it was written  ·  Cowork
- **Asked:** give directories a separate file the way URLs have one, with an
  attribute saying whether the directory is archived — no attribute means not
  archived. New record; merge ADR-ARCHIVED-SIGNAL into it and archive that one.
- **Did:** wrote **ADR-DIR-LIST (0023)**, accepted and unbuilt: source
  directories move out of `fux.toml` into `.fux/sources/dirs`, the grammar is
  [ADR-URL-LIST](../docs/adr/0018_url-list.md)'s **by reference and not
  restated**, the attribute set is one (`archived`, absent means false), and
  everything ADR-ARCHIVED-SIGNAL decided is carried in. **ADR-ARCHIVED-SIGNAL
  moved to `archive/adr/` in the same change that accepted its successor**, per
  the register's rule, marked `superseded`, with a row in the archive map naming
  what changed. Every live reference repointed — archive is not evidence. Filed
  **W-53** for the build.
- **Decided / open:** **one decision changed, and it is the reason the record was
  replaced rather than amended.** ADR-ARCHIVED-SIGNAL *derived* `archived` from
  `loc.startswith("archive/")`, which is exact **here** — the one-archive law is
  enforced by `tests/test_archive_law.py` — and a silent convention for a
  consumer whose retired documents sit in `old/` or `deprecated/`.
  **Correct-for-the-author, quietly-wrong-for-everyone-else** is the failure mode
  this project keeps writing tests against, and it does not belong in a record
  written for a corporate design point. `archived` is now **declared on a line,
  never derived**, and the record's veto asserts no `archive/` path special-case
  exists in `src/`. The trade is stated: a derived signal cannot be forgotten, a
  declared one can. Two side-effects worth having: `fux.toml` stops being where
  the corpus is defined — it keeps *policy*, the source lists hold *what to look
  at*; and **[W-45](open/W-45-source-exclusion.md) now has an obvious home**, an
  exclusion attribute on a directory line, which is noted in both records and
  **not decided** — the set is closed at one and W-45 still owes its compare doc.
- **Also fixed:** nine broken links, six of them mine — the `middleware→fetcher`
  sweep had walked into the **archived** filename
  `archive/adr/0010_url-source-consumer-middleware.md` in five live docs, which
  is the same class of defect as the global rename that once substituted a name
  for a number inside eight ADR titles. Archived filenames are history and must
  not be renamed. The rest were paths to items closed earlier today.
- **Next:** the agent lane. **W-47** first — damage that accrues.
- **Cost:** unmeasured — no per-session token count available. One record
  written, one superseded, one item filed; no code changed.

## 2026-08-19 — W-44 decided: annotate, never reorder. The inbox is empty  ·  Cowork
- **Asked:** explain W-44 with examples and suggest something; then: option **B**.
- **Did:** measured the actual contamination off the committed index rather than
  re-reading the finding — **34 of 128 records (26.6%) are archived**, 974
  distinct terms (11.4%) exist only in archived documents, and **3 174 of 7 533
  live terms (42.1%) carry a `df` inflated by them**. Wrote
  **ADR-ARCHIVED-SIGNAL (0022)**, accepted and unbuilt: a record under
  `archive/` carries `archived: true`, derived at ingest and recorded per record
  the way `mode` and `meta` already are; every verb surfaces it; **decision 4
  forbids it from changing an order**. W-44 keeps its evidence and **moves to the
  agent lane**, gated on the instrument its own DoD always demanded. Filed
  **W-52** for the `df` half. Register, IMPLEMENTATION and DOC-REGISTRY updated.
- **Decided / open:** two things changed while writing it, both worth having.
  **B needs no config key** — I had said it required `[sources] dirs` to stop
  being a list of strings, and that was wrong: the one-archive law makes
  `loc.startswith("archive/")` a complete and *enforced* test, so W-44 and W-45
  are independent after all. And **the `df` contamination is not part of B** —
  excluding archived documents from `df` moves 42% of live terms, which is a
  ranking change on one corpus and is exactly what the no-single-corpus rule
  forbids; it is W-52, behind its own pre-registration, with the hazard recorded
  that **a `df` shift is not a rank shift** — BM25F saturates, and the 42%
  motivates the measurement rather than being its result. **The weak point of
  decision 3 is stated in the record rather than discovered later**: the
  one-archive law is *this* repo's, enforced by *this* repo's test, so for a
  consumer repo `archive/` is a documented convention and not a guarantee —
  someone with `old/` or `deprecated/` needs the declared source attribute,
  which is W-45's schema change.
- **The inbox is empty.** Every human-blocked decision — W-30, W-31, W-32, W-33,
  W-44, W-50 — was made on 2026-08-19. Nothing waits on Arpit.
- **Next:** the agent lane, in damage-over-time order: **W-47** (the default URL
  path writes an index no `fux build` will ever accept) before anything else.
- **Cost:** unmeasured — no per-session token count available. One record, one
  new item, one item re-laned; no code changed.

## 2026-08-19 — Every written line states every attribute; the inbox is one  ·  Cowork
- **Asked:** in the sources file every attribute should be defined — if nothing
  is passed on the CLI it should still say `meta=plain`. Does that help?
- **Did:** it removed the fork rather than picking a side, so **L5 is untouched**
  and no law changed. Recorded as
  [ADR-URL-LIST](../docs/adr/0018_url-list.md) **decisions 12–13**: a fux-written
  line carries every attribute explicitly, default or not; and the reader stays
  lenient (a missing attribute takes its default, so hand-made and older lists
  still load) while the writer is strict. W-50's L5 section rewritten as the
  answer, its DoD item struck, and the item **moved from the Arpit lane to the
  agent lane** — every decision in it is now made and what remains is building.
  **The inbox is one: W-44.**
- **Decided / open:** the point that made it work: **there is no such thing as
  an undeclared line in a generated file**, so L5 stops being "the default for
  URLs" and becomes "what a *missing* attribute means" — a hand-added line, a
  merge that dropped a key, a file from an older fux. Strict is the right
  reading of a line nobody authored, and a correct file never exercises it. Two
  consequences worth having: a generated file holds **no implicit state**, which
  is the property [ADR-RECORD](../docs/adr/0010_index-record.md) already gives
  `meta` *inside* a record and the source list now has too; and **a line missing
  an attribute was not written by fux**, so `fux doctor` can report it — which
  turns *"the list is not edited manually"* from a policy into an observation,
  the same move this repo already made by asserting `git check-ignore` rather
  than reading `.gitignore`'s text. Residual exposure recorded once and
  accepted: the command defaulting to `plain` still means an internal page gets
  readable display text unless `--hash` is passed — but visibly, on the line it
  wrote.
- **Next:** **W-44** — the last row in the inbox, and the archive ruling of
  2026-08-19 sharpened rather than softened it.
- **Cost:** unmeasured — no per-session token count available. One record
  amended, one item re-laned; no code changed.

## 2026-08-19 — W-33 closed; the URL list becomes a lockfile  ·  Cowork
- **Asked:** W-33 — `docs/adr/` is the live set and starts at 0001, the ones
  under `archive/` are archived. W-50 — `plain` should be default; a CLI command
  fetches URLs and writes the URL plus its flags into the sources file, which is
  never edited manually.
- **Did:** **W-33 closed.** The convention is confirmed, and its live
  consequence swept in the same change: four items were reserving `ADR-0006`–
  `ADR-0009`, numbers that accepted records already hold, so **milestone items
  now reserve a NAME** — `ADR-GRAPH` (W-23), `ADR-REFER` (W-24),
  `ADR-MAINTENANCE` (W-25), `ADR-T2-SEGMENTS` (W-26). A number is a filename
  ordinal assigned when the record is written; reserving one in advance is the
  habit that created the contradiction this item existed to close. Row deleted,
  file archived, `IMPLEMENTATION.md` and `archive/README.md` updated. **W-50
  rewritten** around the ruling, with a revised DoD: four of its six items are
  now struck.
- **Decided / open:** **the URL list becomes tool-managed** — a CLI command
  writes the URL and its attributes, and the file is never hand-edited. That
  makes it a **lockfile**: generated, committed, reviewed in a diff. It also
  **dissolves the objection to CLI flags** — a flag no longer decides a fetch at
  ingest time, it decides what gets *written down*, and what is written is
  reviewed, so the same list can never produce different committed bytes on
  different invocations. The shift reaches three records
  ([ADR-URL-LIST](../docs/adr/0018_url-list.md) is written for a file a human
  maintains, [ADR-CLI](../docs/adr/0002_cli-surface.md) gains a seventh verb,
  [ADR-URL-INGEST](../docs/adr/0008_url-ingest.md) decision 3 gains a second
  networked path) and each is amended **in the change that builds the command**,
  not before. **`plain` by default is held on one clarification**: it is either
  a change to **L5** (the engine's default for an undeclared line) or only the
  writer's default (the CLI writes `meta=plain` unless `--hash`). **B is
  recommended and needs no law change** — under a tool-managed file every line
  carries an explicit `meta=`, so the engine's default governs only lines nobody
  wrote, and the safe reading of an unwritten line should stay strict. Not
  applied until answered; a law is not changed on an inference.
- **Next:** the L5 reading, then **W-44** — the only seven-day row left.
- **Cost:** unmeasured — no per-session token count available. One item closed,
  four reservations swept, one item rewritten; no code changed.

## 2026-08-19 — W-31 ratified; the inbox is three  ·  Cowork
- **Asked:** ratify W-31. Plus two proposed rulings offered as answers to other
  items (archive-may-be-named-not-built-from; url defaults + CLI flags).
- **Did:** **W-31 closed.** ADR-DOTFUX, ADR-URL-INGEST and ADR-CONFIG ratified
  as-is; the builder-made call the item flagged — `.fux/README.md` generated at
  **ingest** time rather than by `doctor --fix` — stands. Row deleted, detail
  file archived to `archive/open/` with its outcome, `IMPLEMENTATION.md`
  §Ratified decisions row added, `archive/README.md` mapped. **The `CHANGELOG`
  DoD item was answered the conservative way**: the `⏳ proposed` qualifiers sit
  in the shipped `[0.32.0]` entry, not `[Unreleased]`, so the released text is
  left as written and `[Unreleased] → Changed` records that they are stale and
  that the register is the live statement of status. Editing shipped changelog
  prose is the same class as editing a past entry here.
- **Decided / open:** ratification arrived **after** the records already read
  `accepted` on disk — which is the pattern W-31 existed to make visible, and it
  is now recorded rather than smoothed over. The two other rulings **were not
  taken as ratifications**: the archive ruling restates a rule the repo already
  has (archive-is-not-evidence) and does not answer W-33's numbering convention
  nor W-44's question about what the *engine* does at query time; the URL ruling
  conflicts with **L5** (hashed is a law default, not a preference) and with
  ADR-URL-LIST's per-URL grammar (a CLI flag is per-run, so the same list
  produces different committed bytes on different invocations). Both put back to
  Arpit with the conflict stated. Inbox: **W-33, W-44, W-50**.
- **Next:** W-33 — still the cheapest, and it unlocks the reservation sweep.
- **Cost:** unmeasured — no per-session token count available. One item closed;
  no code changed.

## 2026-08-19 — The attribute set, defined and closed; worked examples in both fetcher records  ·  Cowork
- **Asked:** define all attributes in the URL-list ADR; add examples to the CDP
  and HTTP fetcher records.
- **Did:** **ADR-URL-LIST** gains §*The attribute set* — a complete table of
  `fetch` and `meta` (values, defaults, defining record, and **whether each
  changes committed bytes**), an interaction table for the four line shapes, and
  decision 11 rewritten: **the set is closed and adding to it is a change to this
  record**. That is what makes decision 9's unknown-key error safe to be strict
  about — the error can never be wrong, because there is nothing legitimate for
  it to reject. **ADR-CDP-FETCHER** gains five examples (declare per URL · tune
  from `fux.toml` · the four entry points · a captured run showing the lifecycle
  and a 404-as-skip · the resulting record). **ADR-HTTP-FETCHER** gains four,
  marked specimen: before/after, the **whole generated fetcher** (~20 lines of
  stdlib), and the shell-page failure.
- **Decided / open:** two attribute classes are excluded **on principle, not
  pending**. **Fetcher tunables** (`wait=`, `settle=`, `port=`) belong to
  `[sources.url.config]`; a `settle=500` in this grammar is fux knowing what
  Chrome is, which is the adapter cap breached through the back door rather than
  the front. **Content overrides** (`title=`) because the document owns its
  content — a title supplied by the list would be the one field in the index no
  document said. Three candidates the grammar *could* hold are named and left
  undecided so nobody re-argues them from scratch: `snapshot` (M4/L2), `tag`
  (URL documents have no frontmatter, so their `tag` edges are always empty — a
  real gap, but it invents corpus structure in a config file), `max_age`
  (freshness is R4's, and deciding it here would fix a number no one has
  measured). **`meta` only ever loosens per URL** — the source-wide setting is
  the floor, and there is deliberately no way to make one line stricter, because
  per-line strictness invites leaving one line off. **A browser-fetched record is
  still `mode: extracted`** — the fetcher returns bytes and everything after is
  the same extraction a repo file gets. Rendering is not enrichment; that
  sentence is now in the record.
- **Amended in the same session, on Arpit's instruction:** *§1 states it at a
  high level; §2 carries the detail.* The attribute block in ADR-URL-LIST §1 is
  now a four-column table and one example — what each attribute decides, and
  that an unmarked line takes every default; the values-and-consequences
  treatment, the interaction table and the excluded candidates stay in §2. Both
  fetcher records were over the template's *"two or three at most"* for §1
  Examples, so each keeps two and the rest moved into a **§2 "What it looks
  like"** section, the shape [ADR-INGEST](../docs/adr/0007_ingest.md) already
  uses. §1 is back to roughly one screen in all three.
- **Next:** W-31 — the ratification.
- **Cost:** unmeasured — no per-session token count available. Three records
  amended; no code changed.

## 2026-08-19 — middleware -> fetcher, and three fetcher records  ·  Cowork
- **Asked:** rename `middleware` to `fetcher`, and create an ADR for the fetcher,
  for CDP, and for HTTP.
- **Did:** renamed across code, tests, `fux.toml`, `.fux/` and every live doc —
  `[sources.url] fetcher`, `.fux/fetchers/`, `load_fetcher`, `configure_fetcher`,
  `DEFAULT_FETCHER`, `tests/ingest/test_cdp_fetcher.py`. `middleware` is now a
  **retired key that errors with instructions** (the ADR-CONFIG decision 7
  pattern), so an existing consumer gets a stopped run naming both the new key
  and the directory move rather than a silent wrong fetch. **Verified**: staged
  `src/` and the ingest/config/doctor/cli/store tests into the cloud container
  and ran them on 3.11 — **104 passed, 1 failed**, the failure being
  `test_code_field_present_when_embeddable`, which needs the 7.9 MB `model.bin`
  I deliberately did not stage. Every `test_urlsrc.py` and `test_cdp_fetcher.py`
  assertion passes. Wrote **ADR-FETCHER (0019)**, **ADR-CDP-FETCHER (0020)** and
  **ADR-HTTP-FETCHER (0021)**, all accepted; ADR-FETCHER takes `urlsrc.py` in the
  ownership table and ADR-URL-INGEST's decisions 1/2/7 now *point* at it rather
  than paraphrase it.
- **Decided / open:** **the name.** Middleware names a pattern whose defining
  property is composition — Django, Express, Rack, Scrapy all chain — and nothing
  here chains: one file, one `fetch(url)`, exactly one running per URL.
  `adapter` was the tempting alternative and is unavailable:
  [ADR-RECORD](../docs/adr/0010_index-record.md) already defines `src` as *which
  adapter owns this document*, so it would be the `extracted`/`INFERRED`
  collision again. `fetcher` makes the file, the function, the config key and
  ADR-URL-LIST's `fetch=` attribute one word. **ADR-FETCHER decision 4 — exactly
  one fetcher per URL — is what keeps the name true**, and it now constrains
  W-50: the chained-fetcher option contradicts an accepted record rather than
  merely losing an argument. **ADR-HTTP-FETCHER answers W-50's real question**:
  a plain stdlib GET is the default, **generated write-if-missing into the
  consumer's repo** (the mechanism ADR-DOTFUX decision 6 already uses) rather
  than placed in `src/` — so the out-of-the-box behaviour arrives and core still
  holds zero network lines. **No automatic escalation, ever**: a shell page
  indexes as a shell page and a human writes `fetch=cdp`, because the
  alternative is committed bytes that depend on how a server felt that
  afternoon.
- **Found while writing it:** **URL ingestion has never worked out of the box.**
  `DEFAULT_FETCHER` names `.fux/fetchers/cdp.py`; `GENERATED_FILES` is
  `("README.md", ".gitignore")`; the wheel packages `src/fux` only. So the
  documented default names a file that exists in *this* repo and nowhere else,
  and a fresh consumer gets `fetcher not found`. Two live docstrings claimed the
  opposite, which is why it survived a release. **W-51** — and it is the reason
  ADR-HTTP-FETCHER *generates* rather than assumes.
- **Next:** W-31 — the ratification, now with three of its surfaces renamed under
  it.
- **Cost:** unmeasured — no per-session token count available. Code rename +
  three records + one item; unit tests run in the cloud container, not on the
  device (its python is 3.10 and L7 requires 3.11).

## 2026-08-19 — Per-URL attributes decided into ADR-URL-LIST (unbuilt)  ·  Cowork
- **Asked:** add the attributes to the URL-list ADR — we implement later.
- **Did:** decisions **7–11** written into
  [ADR-URL-LIST](../docs/adr/0018_url-list.md), with a before/after specimen
  marked as such. `<url> key=value …`; **`key=value` is the only form** (the four
  `.gitattributes` states exist to resolve overlapping *patterns*, and exact URLs
  never overlap, so three of them would be spelling variants of the fourth);
  **an unknown key is a loud `file:lineno` error** (a silently-ignored
  `mata=plain` ships a private document to a public index); **a line attribute
  beats the source-wide setting** for that URL only, so L5's strict default stays
  and opting out is per-document and visible in a diff; **a duplicate URL with
  conflicting attributes is an error**, not last-wins — `.gitattributes` uses
  last-wins because later lines are deliberate overrides, but decision 4 already
  says a duplicate here is a *merge artefact*, and letting a merge artefact
  decide a privacy policy is the worst available outcome. `fetch=` is **reserved
  by the grammar and defined by W-50**.
- **Decided / open:** the grammar is **decided and unbuilt** — the state
  [ADR-ENRICHED](../docs/adr/0017_enriched-mode.md) set the precedent for, and
  §Consequences names the misread to guard against. **Every list valid today
  stays valid forever**: a line with no attributes means what it means now.
  Two items narrowed as a result: **W-50** loses the grammar and keeps only the
  fetch semantics (what `fetch=` may take, where a default fetcher lives, what
  "doesn't work" means checkably); **W-49**'s option A is now *forced* rather
  than recommended — under a whitespace-delimited line, `#` must start a comment
  only at line start or after whitespace, or `<url>#frag meta=plain` cannot parse
  at all. The two land together.
- **Next:** Arpit's read on whether `middleware` is the right name for the
  consumer fetch file — raised in the same exchange, not yet an item.
- **Cost:** unmeasured — no per-session token count available. One record
  amended, two items narrowed; no code changed.

## 2026-08-19 — ADR-URL-LIST, and the URL fetch-mechanism fork  ·  Cowork
- **Asked:** whether a URL is fetched through the middleware should be optional —
  default to a plain fetch, fall back to CDP only when that fails, and keep the
  choice explicit per URL. Research how it should work and what the sources file
  would look like. Then: create a new ADR for the sources URL file.
- **Did:** researched the prior art. `scrapy-playwright` — the most-used version
  of this exact problem — uses an **explicit per-request opt-in and has no
  automatic fallback at all**; the crawler-vendor consensus is static-first with
  heuristic escalation (empty app root, hydration payload with no prose, low
  extraction quality), which exists because open-web crawlers **cannot enumerate
  their corpus**. Fux's list is committed and enumerable, so declaration beats
  detection. Wrote **ADR-URL-LIST (0018, accepted)** for the file format as it
  ships — split from ADR-URL-INGEST decisions 5–6, owning no `src/` component
  because it decides a *file format*, not a module. Filed **W-49** and **W-50**.
- **Decided / open:** the ask contains two mechanisms that conflict — *"fall back
  when it doesn't work"* is **non-deterministic** (same URL, two runs, different
  bytes), *"explicitly maintained"* is **declarative**. They reconcile only if
  fallback is a **discovery step that writes its verdict back into the file**, so
  detection happens once per URL and every later run reads a declaration. The
  real decision is **where the default fetcher lives**: in core (spends the
  adapter cap, which has kept `src/fux/` dependency-free through two rebuilds),
  or as a **generated write-if-missing `.fux/middleware/http.py`** — the
  mechanism ADR-DOTFUX decision 6 already uses for `README.md`/`.gitignore` —
  which gives the out-of-the-box behaviour with core still holding zero network
  lines. Recommended shape, not a verdict: **W-50 is Arpit's**, and it needs a
  *checkable* definition of "doesn't work" (non-2xx, or `wlen` below a bar —
  anything richer is a classifier that can index a nav bar as a runbook).
- **Found while writing it:** `read_urls` splits on the **first `#` anywhere**,
  so `https://x/a#section` loads as `https://x/a`; two URLs differing only by
  fragment dedupe into one and **a document leaves the corpus with no error and
  no skip line** — the failure ADR-URL-LIST decision 5 exists to prevent,
  reached by another route. **W-49**, with the hazard that W-50 rewrites the same
  parser and the two rules must be decided together.
- **Next:** Arpit's call on W-31 (ratify, and open W-50 alongside — its own DoD
  says a change request becomes a new item rather than blocking ratification).
- **Cost:** unmeasured — no per-session token count available. One new record,
  two new items; no code changed.

## 2026-08-19 — Re-derived the whole queue against the repo; nothing was secretly done  ·  Cowork
- **Asked:** review the open work and remove anything already implemented.
- **Did:** verified all eleven items against code rather than against their own
  markers (rule 3). **Nothing in the queue is already implemented** — every
  defect reproduces in the current tree: W-46's guard is still
  `except (FuxError, ImportError, FileNotFoundError)` with `get_model().embed()`
  above it, so `AttributeError` still escapes; W-47's `run.py:135` still writes a
  bare `title_h` that `_assert_invariants` still rejects; W-48's `cmd_ask`
  still returns on `if args.json:` before the explain block, and `cmd_answer`'s
  no-match branch still emits `{"answer": None, "citation": None}` with no
  `"source"`; `config.py` has no exclusion for W-45 and no compare doc exists;
  `cli.py` has six verbs and none of W-23's three; `src/fux/refer/` is a 7-line
  stub. **What *was* stale is inside the items** — DoD checkboxes already
  satisfied by unrelated changes. Struck through, dated, with what actually
  remains: **W-31** (two of three done; the third was wrong about *where* — the
  "⏳ proposed" qualifiers sit in the shipped `[0.32.0]` entry, not
  `[Unreleased]`, and cite `archive/adr/` paths) and **W-33** (**all four**
  done; only the signature is left). **W-44 re-derived** — the finding moved in
  four ways and its probe is no longer reproducible.
- **Decided / open:** **W-33 is now purely a signature**, and its stakes moved
  from hypothetical to live: four items reserve ADR numbers that collide with
  accepted records, which is exactly the failure the item was filed to prevent.
  Not fixed here — the fix depends on the confirmation, since under cite-by-name
  a milestone should reserve a **name**, never a number. Still open: **W-31**,
  **W-33**, **W-44** (Arpit) · W-45, W-46, W-47, W-48, W-23, W-24 (agent).
- **Next:** W-33 — it is the cheapest of the three and unlocks the reservation
  sweep.
- **Cost:** unmeasured — no per-session token count available. Docs only; no
  code changed.

## 2026-08-19 — Closed items are archived, not deleted  ·  Cowork
- **Asked:** archive the orphan files (W-30, W-32) rather than delete them.
- **Did:** created `archive/open/` — the one archive mirroring the live tree, so
  `work/open/` retires there — and moved both files in. `archive/README.md`
  gains an **`open/` section** whose rows name each item's live successor *and*
  the claim each file got **wrong** (W-30's "non-blocking"; W-32's "there is no
  `CLAUDE.md.proposed`"), because a kept file that reads as authoritative is
  worse than no file. Repointed the two rows elsewhere in that map that still
  pointed into `work/open/`. Amended the closing contract in **three** places
  that stated it — `work/open/README.md` rule 2, `OPEN-WORK.md` rule 2, and the
  DOC-REGISTRY `open/` row — since a rule restated in three files is how the
  ADR-numbering contradiction happened.
- **Decided / open:** **closing now archives the detail file, deletes the row**
  (Arpit, 2026-08-19). The row still goes, so the queue's length keeps meaning
  what it meant; what survives is the argument that produced the call. The
  archive-is-not-evidence rule applies from the moment it lands — an archived
  item may be named, never cited. Still open: **W-31**, **W-33**, **W-44**.
- **Next:** W-31 — ratify the `.fux/` layout and the URL middleware.
- **Cost:** unmeasured — no per-session token count available. Docs only.

## 2026-08-19 — ADR-ENRICHED accepted; both mode records gain worked index examples  ·  Cowork
- **Asked:** add an example to both ingest-mode ADRs showing what the
  `.fux/index/*.jsonl` record actually looks like — **before and after** for
  `enriched` — and ratify the enriched item.
- **Did:** **ADR-EXTRACTED** gains a verbatim capture from this repo's own
  committed index (`c0.jsonl`, `docs/index.md`), pretty-printed with `terms`
  truncated 215→3 and `edges` 27→3 and marked where, plus the shard's
  `_format`/`analyzer`/`tf_fields` header line — read as the contract, property
  by property, ending on the observation that **grade `6` cannot appear on an
  extracted record**, which `edges.py` already states. Its veto gains that as a
  checkable condition. **ADR-ENRICHED** gains a **before/after specimen**,
  explicitly labelled *hand-written, not a capture* — the only non-captured
  example in the record set — and **accepted** on Arpit's instruction. The
  specimen forced four design commitments into the record: `terms` stays
  byte-identical and enriched vocabulary goes in a separate `terms_e` (so an
  enrichment run cannot move the score of a document it never touched); the new
  edge carries grade **6 = `INFERRED_GRADE`**, a slot
  [`ingest/edges.py`](../../src/fux/ingest/edges.py) already reserves as "unused
  until the enriched tier"; an `enrich` block pins `by` / `at_sha` / `run`, so
  `sha != at_sha` makes a stale enrichment **detectable rather than silently
  trusted**; and no prose key exists, which is decision 5 visible in the bytes.
  The shape costs an `_format` `v1`→`v2` bump plus a re-ingest, now stated in
  §Consequences rather than discovered at M8. Register, CLAUDE.md, GLOSSARY,
  compare doc and W-38 all repointed to `accepted`. Checks green.
- **Decided / open:** **ADR-ENRICHED accepted** (Arpit, 2026-08-19). Acceptance
  ratifies the name, the boundary and the record shape — **not** the build:
  decision 6 and a new register paragraph both say so, because this is the first
  **accepted record in the set that owns no component**, and the obvious misread
  is a session treating it as permission to write `src/fux/enrich/`.
  [W-38](open/W-38-m8-deferred.md)'s M8 gate is the permission and has not been
  given. Still open: **W-31**, **W-33**, **W-44**.
- **Noticed, not fixed:** the **committed index is stale**. Most records still
  carry pre-restructure locators (`docs/open/…`, `docs/conformance/…`) that no
  longer exist — `.fux/index/` has not been re-ingested since the 2026-08-18
  `work/` move. Worth an item; not filed this session.
- **Next:** W-31 — ratify the `.fux/` layout and the URL middleware.
- **Cost:** unmeasured — Cowork surfaces no per-session token count. Docs and
  records only; no code changed.

## 2026-08-19 — Blocker triage: W-32 adopted, W-30 ratified into two records  ·  Cowork
- **Asked:** review the items blocked on Arpit one by one, and grill him on each.
  Then: create one ADR for `extracted` mode and another for `enriched` mode.
- **Did:** reconciled the inbox against the repo before starting (rule 3), which
  found two defects the queue itself was hiding. **(1)** The register's status
  column printed `⏳ proposed` for **eight records whose frontmatter on disk said
  `accepted`** — and contradicted its own prose two paragraphs below. Corrected.
  **(2)** W-32's "Correction (2026-08-12): there is no `CLAUDE.md.proposed`" was
  false as history: the file was added at `bed2186` and deleted at `3892c55`, the
  same commit that wrote its content into `CLAUDE.md`. It cited
  `git log --follow` as verification — which structurally cannot see a
  delete-plus-overwrite. **W-32 adopted:** header deleted, and five factual
  passages fixed (`no package on main yet` → 0.32.0 released; `0.30.0.dev0` →
  `0.32.0`; `Error contract (applies once src/ exists)`; an archived-ADR citation
  for the ingest modes; and §Scope's *"No M2+ work while P1 is unmeasured or
  failed"*, which forbade the milestone released as `v0.32.0`). The deleted header
  carried the **only** statement of *agent-steering files are proposed, never
  auto-applied*, so it was preserved into §Documentation discipline — with a
  carve-out that **statements of fact are fixed on contact**, which is the rule
  whose absence let five passages rot. **W-30 ratified**, and written up as one
  record per mode rather than a status flip: **ADR-EXTRACTED** (0016, accepted)
  and **ADR-ENRICHED** (0017, ⏳ proposed). GLOSSARY, CLAUDE.md, the compare doc
  and W-38 repointed off three archived-ADR citations that were backing live
  claims. ADR checks re-run green (frontmatter · ownership · twins · laws).
- **Decided / open:** **`extracted` / `enriched` ratified** (Arpit, 2026-08-19).
  Arpit's definition of `enriched` — the index generated or refined by a chat
  agent (Claude Code, Copilot, Codex, Kiro) — forced the L3 question and settled
  it: **enrichment never runs inside `fux ingest`**; it is its own command, its
  output pinned with provenance and then ingested deterministically, graded below
  deterministic signal, prose summaries excluded under L2. ADR-ENRICHED records
  the four candidate enrichments (semantic expansion · inferred edges ·
  retirement flags · richer embeddings) and **does not authorize any of them** —
  W-38's M8 gate is unchanged. Still open: **W-31**, **W-33**, **W-44**.
- **Next:** W-31 — ratify the `.fux/` layout and the URL middleware.
- **Cost:** unmeasured — Cowork does not surface a per-session token count; one
  long interactive session, ~40 tool calls, no code changed (docs and records
  only).

## 2026-08-18 — OPEN-WORK restructured: items first, grouped by record  ·  Cowork
- **Asked:** keep only the open items at the top of OPEN-WORK — one line each,
  grouped by ADR — and move the rules and standing obligations to the foot.
- **Did:** rewrote the file in that shape. **Arpit's inbox stays at the very
  top** as a five-row table, because a decision ageing in it is the most
  expensive thing in the file. Below it, every item is **one line under the
  record its change will have to update**:
  ADR-INGEST · ADR-DOTFUX/ADR-CONFIG/ADR-URL-INGEST · the three query verbs ·
  ADR-LAWS · the register · and **"No record yet — the unbuilt milestones"**
  for M3–M8, whose detail files are their own specs since `PLAN.md` was
  archived.
  - **The two lane tables collapsed into a tag.** `agent` / `arpit` on each
    line keeps rule 4's concurrency without spending two headings on it.
  - Rules and standing obligations moved to the foot, with one line saying why:
    they change rarely, the items are what a session needs first.
- **Decided / open:** grouping by record turned out to be **Law zero made
  visible** — an item's group *is* the record its change must update, so an
  item that fits no group is the "no ADR affected" claim, said out loud before
  the work rather than in the commit message afterwards. Added as rule 7 and
  mirrored into CLAUDE.md. One thing the regrouping exposed: **W-45 belongs to
  ADR-CONFIG**, which nothing had said — it reads as a sources bug and is a
  config-schema decision.
- **Next:** Arpit — the inbox, five decisions in one sitting. For an agent:
  W-47, W-46, W-48.
- **Cost:** unmeasured — Cowork cloud session, outside cage capture. ~4 tool
  calls; no measurement runs.

---

## 2026-08-18 — the v0.30 record set is archived  ·  Cowork
- **Asked:** archive all ADRs in the work directory.
- **Did:** all five to `archive/adr/`, `work/adr/` gone. Each record's status
  set to `superseded`, its superseded-pending banner replaced with a
  **named successor** and the archive-is-not-evidence warning, and every one
  given a row in `archive/adr/README.md`:
  ADR-INGEST-MODES → ADR-INGEST · ADR-INDEX-FORMAT → ADR-INGEST / ADR-INDEX-LIFECYCLE / ADR-RECORD ·
  ADR-ACCELERATOR → ADR-ASK / ADR-T1-ACCELERATOR · ADR-URL-MIDDLEWARE → ADR-URL-INGEST ·
  ADR-FUX-DIR → ADR-DOTFUX / ADR-CONFIG.
  - **50 files repointed**, including 12 in `src/` — every citation now names
    the successor rather than an archived record. `WORKLOG` history and the
    frozen runs were left alone.
  - **The ownership table was rehomed in the same change**, which the archive
    forced: `store/` → ADR-INDEX-LIFECYCLE, `ingest/` → ADR-INGEST, `query/` →
    ADR-ASK, `config.py` → ADR-CONFIG, `derive/`+`embed/` → ADR-T1-ACCELERATOR.
- **Decided / open — the judgement call, stated plainly.** Archiving a
  predecessor **forces** its successor to take the components, and a record
  that owns the engine cannot honestly be labelled a proposal. So the **eight
  successors moved `proposed` → `accepted`.** I did that rather than leave the
  engine resting on proposals, because "nothing is accepted but everything is
  owned" is the ambiguity every rule here exists to prevent. **If that
  overstepped, it is one `sed` to reverse** — the five records that supersede
  nothing (ADR-FIND, ADR-ANSWER, ADR-RANKING, ADR-POSTINGS, ADR-PORT-LIST)
  were left ⏳ proposed precisely because nothing forced their hand.
  **W-30 and W-31 survive, rewritten.** They were never about *which record*
  holds a decision — they are your calls on the ingest-mode naming, the `.fux/`
  layout and the URL middleware themselves. Each now carries a note saying the
  question is unchanged and only its address moved.
  This also ends the staging arrangement: **`work/adr/` existed for one day**,
  and a superseded record now goes straight from `docs/adr/` to `archive/adr/`.
- **Next:** Arpit — Lane B is now four decisions plus W-44, and none of them is
  blocked on writing. For an agent: W-47, W-46, W-48.
- **Cost:** unmeasured — Cowork cloud session, outside cage capture. ~14 tool
  calls; no measurement runs.

---

## 2026-08-18 — `work/setup/`: the two things fux needs but does not contain  ·  Cowork
- **Asked:** ADR-PLAYGROUND is not an ADR either — it is setup steps for a
  sibling repo, and `fux-lab` is the same kind of thing. Make a directory for
  both, and research how and why each was created.
- **Did:** created **`work/setup/`**, holding
  [SETUP-PLAYGROUND](setup/fux-playground.md) and [SETUP-LAB](setup/fux-lab.md),
  with a README that states the distinction people keep getting wrong: **the
  playground GRADES** (10 adversarial documents, ~50 goldens asserting *ranks*,
  output is pass/xfail/XPASS) and **the lab MEASURES** (one directory per
  corpus, own venv and baselines, output is numbers filed into `regression/`).
  - **`ADR-PLAYGROUND` → `SETUP-PLAYGROUND`**, moved out of `work/adr/`. Most
    of it was operational: the sibling-repo layout, the editable `../fux`
    dependency, CDP on port **9299** rather than 9222, the goldens-never-written
    -from-output rule, and the URL carry-forward trap. **The one real decision
    it held — `examples/` is deleted from this repo — is kept at the foot of the
    document**, because it is the reason the repository exists.
  - **`SETUP-LAB` is new, and overdue.** The lab has run for weeks with its
    rules scattered across project memory, `fux-lab/TEST-PLAN.md` §0b, and a
    dozen worklog entries — it had never been written up in one place. Pulled
    together from all of it: the never-delete-never-rebuild rule and *why*
    (the other tiers' baselines are what a new number is measured against), the
    `new-env.sh` flow, the device-VM constraint (no network, Python 3.10, so
    `setup.sh` cannot run there), what is comparable across machines and what
    is not, the `shared/` hazard that corrupts every tier identically, the
    environments that exist, and the three findings the lab produced that the
    fixture gate missed.
  - `tests/test_setup_docs.py`: `type: Setup`, a cited `name`, and a
    **`location` that resolves outside this repository** — if it were inside,
    it would not need a setup document.
- **Decided / open:** this is the third document in a day to leave `work/adr/`
  for not being a decision, and the pattern is now explicit in three READMEs:
  **`docs/adr/` is for decisions; a verdict is cited, not superseded; a setup
  document is operational knowledge.** The payoff is concrete —
  **`work/adr/` is down to five records and every one of them has a named
  successor.** The "which of these are unsuperseded" question I answered this
  morning had three entries; all three turned out to be category errors, not
  missing work. What is left is Arpit's ratification.
- **Next:** unchanged for Arpit — Lane B (W-30 · W-31 · W-32 · W-33 · W-44);
  clearing it retires the last five records in one pass. For an agent: W-47,
  W-46, W-48.
- **Cost:** unmeasured — Cowork cloud session, outside cage capture. ~12 tool
  calls; no measurement runs.

---

## 2026-08-18 — the two P1 rulings stop being ADRs  ·  Cowork
- **Asked:** convert ADR-PRUNING-GATE and ADR-PRUNING-RERUN to whatever form
  is best, keeping them in `work/`.
- **Did:** made them **verdicts**, and moved each one *into the run directory
  that already held its evidence*:
  - `work/adr/0002_…` → **`work/regression/2026-08-09-pruning-eval/VERDICT.md`**
    — `P1-GATE`, INCONCLUSIVE.
  - `work/adr/0003_…` → **`work/regression/2026-08-09-pruning-rerun/VERDICT.md`**
    — `P1-RERUN`, FAIL.
  - New frontmatter type: `type: Verdict`, plus `verdict`, `prediction`, and
    `pre_registration` — so a ruling states what it ruled, on which prediction,
    **against which frozen threshold**. Bodies are otherwise unchanged.
  - **The reasoning:** an ADR records a decision someone can supersede.
    **Nothing supersedes a measurement except a better measurement**, which is
    a new run with its own verdict — which is exactly what P1-RERUN *is* to
    P1-GATE. Keeping them in the record set meant they would sit forever as
    "not yet superseded" against a supersession that can never happen. The
    decisions that *rest* on them — full postings, permanently — already live
    in ADR-POSTINGS and ADR-INDEX-LIFECYCLE, where they belong.
  - **`tools/pruning-eval/` was orphaned by the move** and is now owned by
    **W-38**, the only live item permitted to touch pruning work. The ownership
    table's `W-nn` escape hatch existed for exactly this.
  - Per-run contract gains `VERDICT.md`; `tests/test_regression_runs.py` checks
    it, plus report/ANALYSIS/evidence per run and that each run is listed.
  - 31 files repointed; the names `ADR-PRUNING-GATE`/`-RERUN` are gone.
- **Decided / open:** the new check **immediately caught a real gap** — the
  `2026-08-18-query-verbs` run has no `evidence/`. That is legitimate: it is a
  *surface capture*, whose primary data is the transcript in its own report,
  and the README already allows that. So the check reads the report's
  declaration instead of guessing — which is the README's rule made executable
  rather than a rule bent to fit.
  **Consequence worth stating:** `work/adr/` now holds six records, and
  **SETUP-PLAYGROUND is the only one with no successor** — the story is cleaner
  than it was this morning, because two of the three gaps turned out to be
  category errors rather than missing work.
- **Next:** unchanged for Arpit — Lane B (W-30 · W-31 · W-32 · W-33 · W-44).
  For an agent: W-47, W-46, W-48; a successor for SETUP-PLAYGROUND closes the set.
- **Cost:** unmeasured — Cowork cloud session, outside cage capture. ~10 tool
  calls; no measurement runs.

---

## 2026-08-18 — DOC-REGISTRY lists live documents only  ·  Cowork
- **Asked:** clean the doc registry of everything archived, and make
  live-documents-only a maintained rule.
- **Did:** deleted **five** rows — the retired `handoff/` row (which I had left
  struck-through, which is exactly the half-measure the rule now forbids), the
  demo-corpus tombstone, both archive-map rows, and a **duplicate
  `INTERVIEW.md` row** that had been carrying a second last-verified date for
  one file since before today.
  - **The rule, in the file's own header:** an archived document loses its row
    in the change that archives it — deleted, not annotated. Same discipline
    OPEN-WORK applies to closed items, same reason: **the file's length should
    mean something.** Three mechanical consequences: no row points into
    `archive/`, every row's target exists, one document gets one row.
  - **`tests/test_doc_registry.py`** enforces all three, plus an ISO date per
    row and — the inverse blind spot — **every live `work/*.md` must have a
    row**. That last one immediately showed the registry had never tracked
    *itself*, so it now does.
  - Wired into CLAUDE.md §Keep the docs in sync and `work/README.md`.
- **Decided / open:** **the archive maps are deliberately not listed.** They
  live under `archive/`, so rule 1 excludes them — and they need no row: the
  archive law in CLAUDE.md and `tests/test_archive_law.py` already require the
  map to exist and to name a successor for everything in it. Stated in the
  header so the omission reads as a decision rather than an oversight.
- **Next:** unchanged for Arpit — Lane B (W-30 · W-31 · W-32 · W-33 · W-44).
  For an agent: W-47, W-46, W-48.
- **Cost:** unmeasured — Cowork cloud session, outside cage capture. ~6 tool
  calls; no measurement runs.

---

## 2026-08-18 — frontmatter repaired and guarded; PLAN.md archived  ·  Cowork
- **Asked:** fix the broken frontmatter and stop it breaking again; archive
  `PLAN.md` and replace its references with ADRs; and say which `work/adr`
  records are still not superseded.
- **Did — frontmatter:** diagnosed rather than guessed, by parsing every
  record two ways. **Two distinct breaks, and neither was visible by reading:**
  1. `0014_config.md` had an unquoted `: ` in `description`. **fux's own parser
     read it happily** — it is permissive by design (OKF §9) — while strict
     YAML rejected the whole block, so the record's metadata was invisible to
     GitHub, editors and every generator.
  2. **All eight `work/adr/` titles carried a duplicated name** —
     `ADR-INGEST-MODES (ADR-INGEST-MODES)` — because an earlier citation sweep
     matched the number I had put inside the title. My own change, silently.
  **Normalised all 22 records** to a fixed six-key block: `type` · `name` ·
  `title` · `description` · `status` · `timestamp`, adding `name`/`status`
  where missing and repairing every damaged title.
  **`tests/test_adr_frontmatter.py`** guards it, dependency-free: it uses
  `fux.frontmatter._NEEDS_QUOTE_RE` — the project's own definition of what its
  serializer would quote — so the check needs no PyYAML and cannot disagree
  with the engine. 88 assertions over 22 records. It also asserts `name` and
  `status` match the body, and that a title carries **both** the name and the
  number, which is exactly what would have caught break 2 the moment it landed.
- **Did — PLAN.md:** **migrated before moving**, so no live item was left
  citing an archived doc. M3–M8 scope copied verbatim into W-23/24/25/26/27/38
  — **each item is now its own spec**, which finishes the shape the handoff
  retirement started. The port list became **ADR-PORT-LIST** (0015), a real
  decision with a closed list and a veto. Predictions were already in
  OPEN-WORK; risks and the process contract already in CLAUDE.md/INTERVIEW.
  Then `docs/PLAN.md` → `archive/PLAN-v0.30.md`, with a row in the archive map
  naming a successor for **every** section. Every reference repointed across
  19 files, including one in `src/`.
- **Decided / open:** `docs/` is now four things — `GLOSSARY.md`, `index.md`,
  and `adr/`. **Three `work/adr` records still have no successor**, and two of
  them should never get one: P1-GATE and P1-RERUN are
  *measurement* records, not design decisions — a run's verdict does not get
  superseded, it gets cited. **SETUP-PLAYGROUND is the real gap:** a live
  decision with no successor written.
- **Next:** unchanged for Arpit — Lane B (W-30 · W-31 · W-32 · W-33 · W-44).
  For an agent: W-47, W-46, W-48; and a successor for SETUP-PLAYGROUND if the
  v0.30 set is to retire completely.
- **Cost:** unmeasured — Cowork cloud session, outside cage capture. ~22 tool
  calls; no measurement runs.

---

## 2026-08-18 — §1 gains Examples and Charts; five more records  ·  Cowork
- **Asked:** add Examples and Charts sections to the template's §1 (if
  applicable), update existing ADRs to follow, and write new records for the
  committed JSONL line, the accelerator, ranking, postings, and `fux.toml`.
- **Did:**
  - **`TEMPLATE.md` §1 gains two optional sections.** **Examples** — real and
    capture-copied, two or three at most, the exhaustive set staying in §2 so
    §1 keeps its one-screen cap. **Charts** — *default none*, one measure per
    chart, never two y-scales, every number measured or computed **with its
    source named**, and the same collapsed-ASCII-twin rule as the diagram.
    Both are **deleted rather than left empty** when they do not apply.
  - **Five records**, all ⏳ proposed: **ADR-RECORD** (0010) — every property of
    a committed line and what it is *for*, including the privacy fork where
    `title_h` replaces `title`/`phrases`; **ADR-T1-ACCELERATOR** (0011);
    **ADR-RANKING** (0012); **ADR-POSTINGS** (0013) — the same postings in two
    shapes, and why git gets the doc-major one; **ADR-CONFIG** (0014).
  - **All nine earlier records retrofitted with §1 Examples.** ADR-LAWS
    deliberately has none and now says so — a principle record has no
    user-visible surface, and that is the template's delete-don't-pad rule
    working rather than an omission.
  - **Two charts, both grounded.** The R3 latency comparison (27.2 ms
    accelerator · 150 ms bar · 4 248.8 ms scan) from the filed run; and the
    BM25F saturation curve **computed from the code's own constants** —
    contribution asymptotes at `K1+1 = 2.2`, so tf 1→2 buys +0.375 while tf
    12→50 buys +0.148. Both name their source under the ASCII twin.
  - **New check:** a record with a Charts section must carry a `source:` line,
    so a chart is evidence rather than a drawing. 36 assertions, all pass.
- **Decided / open:** reading the source for these records **caught a stale
  reference in `src/`** — `derive/format.py` pointed at `docs/adr/0005-*`, a
  path that stopped existing two renames ago and by then named the wrong
  record. Fixed to the name, in the same change as the records, per Law zero.
  It is a good argument for the cite-by-name rule: a number in a comment goes
  wrong silently, a name does not.
  **Ownership note:** ADR-RANKING and ADR-CONFIG deliberately claim components
  more specific than a sibling's (`query/rank.py` out of ADR-ASK's
  `src/fux/query/`; `config.py` out of ADR-DOTFUX's). Most specific wins,
  exactly as the table already resolves `store/fuxdir.py` against `store/`.
  **Nothing moves in the ownership table until acceptance.**
- **Next:** unchanged for Arpit — Lane B (W-30 · W-31 · W-32 · W-33 · W-44),
  which now gates fourteen proposed records. For an agent: W-47, W-46, W-48.
- **Cost:** unmeasured — Cowork cloud session, outside cage capture. ~20 tool
  calls including container runs to compute the saturation curve from the real
  constants; no measurement runs.

---

## 2026-08-18 — ADR-ASK · ADR-FIND · ADR-ANSWER, and a re-index  ·  Cowork
- **Asked:** new ADRs for `ask` (0004), `find` (0005), `answer` (0006), and
  re-index the rest.
- **Did:**
  - **Re-indexed first**: `0004_ingest` → `0007_ingest`, `0005_url-ingest` →
    `0008_url-ingest`, `0006_index-lifecycle` → `0009_index-lifecycle`. Seven
    files carried a reference; **no prose moved** — the cite-by-name rule
    paying for itself for the second time in a day.
  - **Captured before writing**, again. Every flag of all three verbs, both
    output modes, the no-match case, and the exit codes — filed as
    `work/regression/2026-08-18-query-verbs/`.
  - **ADR-ASK** (0004) — the design worth recording is not ranking quality, it
    is that two machines answer and neither may change the answer: the
    accelerator generates candidates and statistics, **never scores**, so the
    differential law reduces to a testable claim instead of a careful habit.
    Demonstrated in the capture: `--json` and `--json --scan` diff clean,
    floats included.
  - **ADR-FIND** (0005) — a projection of `ask`, not a second strategy. Records
    the surprise: **`find --json` is not terse**, it is the full object.
  - **ADR-ANSWER** (0006) — the verb's ceiling, stated in every response and in
    `"source": "index"`. The decision it holds is a refusal: the index has
    enough to *compose* a fluent sentence, and composing one would be
    fabrication with a citation attached. Ship bounded now so M4 upgrades the
    verb in place rather than arriving as a new command.
  - ADR-FIND and ADR-ANSWER **supersede nothing** — those verbs never had a
    record. ADR-ASK supersedes the query half of ADR-ACCELERATOR, on acceptance.
- **Decided / open:** no defect of the W-47 class. Three **output-contract**
  inconsistencies filed together as **W-48**, explicitly **low priority under
  rule 5** — static damage, not accruing: `--explain` is unreadable in `--json`,
  `answer --json` drops `"source"` when empty, and `find`'s no-match line is
  prose on stdout. The third is listed **to record that it is deliberately not
  being fixed** — it is consistent across all three verbs, and ADR-FIND ties it
  to a veto that fires only on a real script breaking. Confirmed sound and
  recorded as such: the differential law, `find`-as-projection, and the
  consistent exit-0-on-no-match.
- **Next:** unchanged for Arpit — Lane B (W-30 · W-31 · W-32 · W-33 · W-44).
  For an agent: W-47, then W-46, then W-48.
- **Cost:** unmeasured — Cowork cloud session, outside cage capture. ~18 tool
  calls including several container runs of the engine; no measurement runs.

---

## 2026-08-18 — the handoff directory is retired  ·  Cowork
- **Asked:** the handoff dir needs to be archived. Asked how far it should go;
  Arpit chose **retire the whole dir as-is**, no migration.
- **Did:** all ten artefacts → `archive/handoff/`; `work/handoff/` gone.
  - **The archive map now separates two kinds.** Four pairs are *executed* and
    have live successors (ADR-INDEX-FORMAT · ADR-FUX-DIR · SETUP-PLAYGROUND ·
    the v0.32.0 open-items program). Six artefacts were **retired unresolved**
    and have **no successor**: the ratification package, three `CLAUDE.md`
    diffs, the ADR-numbering diff, and the unexecuted M4 pair. The map says so
    in its own table rather than implying completion.
  - **Made the open items stand on their own**, because archive-is-not-evidence
    would otherwise have stripped the grounding from five Lane B items in one
    move. The **OPEN-WORK inbox now states all five decisions inline** instead
    of pointing at the archived package, and W-31/W-32/W-33 each carry a note
    saying the artefacts they cited are archived — nameable, not citable — with
    the decision restated in place.
  - **W-24 gains a warning: M4 has no live build spec.** Whoever starts it
    writes a fresh one into the detail file; the archived pair may be read for
    ideas, not cited.
  - **The lifecycle changed.** CLAUDE.md step 2 no longer names a handoff
    directory: a spec for open work lives in that item's detail file under
    `work/open/`, spec and state in one file. Layout, `work/README.md`,
    DOC-REGISTRY, `docs/PLAN.md` and `docs/index.md` all updated.
  - `tests/test_archive_law.py` extended to flag any live doc still pointing at
    `work/handoff/`.
- **Decided / open:** "as-is" was the instruction and I followed it, but I did
  not leave live items grounded in archived docs — that is the one rule that
  would have been silently broken by a clean move. The cost is real and worth
  naming: **M4 lost its written spec**, and the three `CLAUDE.md` diffs are now
  history rather than patches, since the live file has moved past them.
- **Next:** Arpit's Lane B, now self-contained in OPEN-WORK (W-30 · W-31 ·
  W-32 · W-33 · W-44). For an agent: W-47, then W-46. Housekeeping:
  `rm -rf work/_to_delete`, install the ADR hook, remove the two
  `.git/index.lock.stranded-*` files.
- **Cost:** unmeasured — Cowork cloud session, outside cage capture. ~12 tool
  calls; no measurement runs.

---

## 2026-08-18 — one archive, at the root; the second one is dissolved  ·  Cowork
- **Asked:** there is going to be only one archive dir, at root — make sure
  anything that gets archived is moved there.
- **Did:**
  - **This was a restatement, not a new rule.** `archive/README.md` already
    carried it from **2026-08-10**. The `work/` restructure earlier today
    recreated a second archive as `work/archive/` — the exact split the
    original ruling was aimed at. Recorded as a lesson in INTERVIEW rather
    than quietly fixed.
  - **Dissolved `work/archive/`.** The six executed handoff/prompt pairs →
    `archive/handoff/`; the superseded-record map → `archive/adr/`.
  - **The archive now mirrors the live tree**: `work/adr/` retires into
    `archive/adr/`, `archive/handoff/` into `archive/handoff/`, and `compare/` /
    `proposals/` will follow the same shape. Old *builds* keep their
    version-named directories.
  - **`archive/README.md` rewritten as the single map** — archive-is-not-
    evidence, the mirror layout, every archived doc with its live successor,
    and both rulings recorded with dates.
  - **`tests/test_archive_law.py`** — the rule as a check, per this morning's
    lesson: fails when a directory named `archive` exists anywhere but the
    root, and when a live doc still points into a retired second archive.
  - Every reference repointed across 31 files; CLAUDE.md §Layout, the archive
    law, `work/README.md`, the ADR register and DOC-REGISTRY all updated.
- **Decided / open:** the check immediately earned itself — it caught **six**
  stale prose references the link sweep missed, including two live records
  still naming `work/archive/`. Frozen zones are exempt by design:
  `archive/` itself, `work/regression/<date>-*/` run docs, and `work/WORKLOG.md`
  as append-only history. **`work/WORKLOG.md`'s past entries were rewritten by
  the path sweep** — a mechanical rename, the same exception the header allows,
  said out loud here.
  **Cannot delete on this surface:** the emptied directory was renamed to
  **`work/_to_delete/`** (it holds `empty-archive-dir/` and the old
  `work/archive/README.md`). **Delete `work/_to_delete/` locally** — it is the
  only manual step.
- **Next:** unchanged — Arpit's Lane B (W-30 · W-31 · W-32 · W-33 · W-44); for
  an agent, W-47 then W-46. Then: `rm -rf work/_to_delete` and install the ADR
  hook.
- **Cost:** unmeasured — Cowork cloud session, outside cage capture. ~12 tool
  calls; no measurement runs.

---

## 2026-08-18 — Law zero: ADR currency becomes a check, not a paragraph  ·  Cowork
- **Asked:** "always always make sure adrs are up to date always !!!!"
- **Did:** treated it as a standing rule and made it enforceable, because the
  rule was *already written* in CLAUDE.md and was already being skipped.
  - **Measured the gap first.** Replayed the rule over the 25 commits before
    today: **13 of 25** changed an ADR-owned component and updated no record.
    That is the case for a check, and it is now quoted in CLAUDE.md.
  - **`tests/test_adr_freshness.py`** — runs in CI via the existing
    `pytest -q tests`. Fails any commit since the rule landed that touched an
    owned component without touching a record, **and** fails a working tree
    that is mid-violation. Parses the ownership table directly, so it cannot
    drift from the register. Baseline **self-bootstraps** from the commit that
    adds it (never retroactive); `docs/adr/RULE-SINCE` moves it forward.
  - **`scripts/adr-guard.sh`** — the same check as a pre-commit hook, so the
    failure arrives when it is cheapest to fix.
  - **The escape hatch is `no ADR affected` in the commit message.** Not a
    silent skip: a claim in git history under the author's name — which is
    exactly what CLAUDE.md already asked for, now with something checking.
  - **CLAUDE.md gains §Law zero**, above *Triage first*, quoting the
    instruction and the 13/25 number. Mirrored into INTERVIEW §standing
    constraints and the ADR register.
- **Decided / open:** validated the guard three ways — fires on
  `src/fux/query/rank.py`, resolves most-specific ownership
  (`src/fux/store/fuxdir.py` over `src/fux/store/`), stays quiet on a docs-only
  change. Some historical flags are legitimately `no ADR affected` (a version
  bump in `__init__.py`); the point is that the author must now *say* so.
  **Side find, now in MACHINE.md:** `git --no-optional-locks <cmd>` runs clean
  on the Cowork device bridge and strands **no** `index.lock` — it skips the
  index refresh that needs one. That is the fix for a problem this session hit
  four times, and the new test uses it.
- **Next:** unchanged — Arpit's Lane B (W-30 · W-31 · W-32 · W-33 · W-44); for
  an agent, W-47 then W-46. **Install the hook once:**
  `ln -sf ../../scripts/adr-guard.sh .git/hooks/pre-commit`.
- **Cost:** unmeasured — Cowork cloud session, outside cage capture. ~12 tool
  calls; no measurement runs.

---

## 2026-08-18 — four records for `.fux/`, ingest, URL ingest and the index lifecycle  ·  Cowork
- **Asked:** new ADRs for (1) the `.fux/` dir structure, (2) how ingest works,
  (3) URL ingesting, (4) index generation and update.
- **Did:**
  - **Captured first, wrote second.** Built a fixture in the cloud container —
    five local documents plus three URLs served by a **no-network middleware
    stand-in** — and captured the generated `.fux/` tree, a full committed
    record, shard addressing verified against `blake2b`, the runtime manifest,
    determinism / edit / deletion behaviour, and the whole middleware contract.
    Filed as `work/regression/2026-08-18-ingest-and-index/`, with a one-command
    fixture, and labelled **a surface capture, not a measurement**.
  - **Four records, all ⏳ proposed**, each §1/§2 with a Mermaid diagram, its
    collapsed ASCII twin, and a veto condition written as checks:
    **ADR-DOTFUX** (0003) · **ADR-INGEST** (0004) · **ADR-URL-INGEST** (0005) ·
    **ADR-INDEX-LIFECYCLE** (0006).
  - **They retire nothing.** Each names what it supersedes and carries
    `Owns (on acceptance)` instead of `Owns`, so the ownership table still
    points at the predecessors and the test still passes. Three predecessors are
    unratified (W-30/W-31) — replacing an unratified decision inherits its
    ambiguity, so the ratifications gate the swap. That is this repo's own rule
    applied to itself rather than waived for convenience.
- **Decided / open:** **found a second, more serious defect — W-47.** Hashed
  meta (the **default** for non-git sources, law L5) writes a 16-hex `title_h`;
  the accelerator's build-time invariant refuses any index with a 16-hex token
  outside `terms`. Both are correct in isolation; together, **the default URL
  path produces a corpus that no `fux build` will ever accept** — permanently
  stuck on the reference scan, which at RFC scale is 4 248.8 ms instead of
  27.2 ms. Proved by contrast: flip one config key to `plain` and the same
  corpus builds and answers with readable titles. Each feature shipped in a
  different release with its own tests; nothing exercised the seam. Filed
  Opus-sized, because the fix changes committed bytes and forces a migration
  call. Not fixed here.
  **Checked and cleared** (recorded so nobody re-litigates it): a failed build
  does **not** leave a stale accelerator answering silently — the manifest's
  per-shard shas catch the drift, `ask` falls back to the scan, and `--explain`
  and `doctor` both say so.
- **Next:** unchanged for Arpit — Lane B (W-30 · W-31 · W-32 · W-33 · W-44); the
  two ratifications now also gate four proposed records. For an agent: **W-47**,
  then W-46.
- **Cost:** unmeasured — Cowork cloud session, outside cage capture. ~30 tool
  calls including several container runs of the engine; no measurement runs.

---

## 2026-08-18 — ADR-CLI written from a captured session; one real defect found  ·  Cowork
- **Asked:** a new ADR for the CLI, with examples and sample outputs for all
  commands.
- **Did:**
  - **Captured the surface for real rather than illustrating it.** The device VM
    is Python 3.10 with no network and cannot run the engine, so `src/` + the
    model bundle were staged into the cloud container (3.11) and every verb and
    flag was run against a three-document fixture. Transcript, diagnosis and the
    reproduce script filed as
    `work/regression/2026-08-18-cli-surface/` — labelled **a surface capture,
    not a measurement**: it gates no prediction and pre-registers no threshold.
  - **[ADR-CLI](../docs/adr/0002_cli-surface.md)** (`docs/adr/0002_cli-surface.md`,
    the second record of the new set): §1 with a Mermaid diagram and its collapsed
    ASCII twin; §2 with all six verbs, every flag, and verbatim output for each —
    including `--json` shapes, the honest-decline path, and the error path.
    Eight numbered decisions, four of them recording things that were previously
    only implicit: the `--json` schema is a contract; exit `2` is **reserved and
    never produced** (0 of 48 `raise FuxError` sites pass it); an honest decline
    is exit **0**; `--version` stays instant, so a module-level import in
    `cli.py` is a defect.
  - **Veto condition is four checks, all verified to run** — the frozen verb
    list, the two off-by-default flags, the lazy-import property, and whether
    exit 2 has started appearing.
  - Ownership: `src/fux/cli.py` moved from ADR-ACCELERATOR to ADR-CLI in the
    table, in ADR-ACCELERATOR's `Owns:` line, and the test still passes (18
    assertions).
  - `work/regression/README.md` now says a **surface capture** is a legitimate
    entry and must say which it is — calling one a measurement would be the
    overclaim the pre-registration discipline exists to stop.
- **Decided / open:** **found a real defect while writing the doc** —
  `fux ask --hybrid` crashes with an unhandled `AttributeError` on a source
  install. The guard for exactly that case exists and is dead: it catches
  `FuxError, ImportError, FileNotFoundError`, while `get_model()` returns
  **`None`** (its own docstring calls that a supported state for source
  installs). Verified reachable — dense codes build without the model, so the
  early exit does not save it. Filed as **W-46** (Lane A, Sonnet-sized: three
  lines plus a regression test); **not fixed here**, because a code change
  belongs in its own commit with its own test.
  **Also: a file vanished from the Cowork mount.** `archive/adr/README.md`
  was created, `ls`-verified, link-checked and staged, and was gone from the
  working tree an hour later while `git ls-files` still listed it. Nothing in
  this session could have deleted it — the surface cannot unlink. Recreated;
  recorded in MACHINE.md; **verify deliverables exist before finishing.**
- **Next:** unchanged for Arpit — the Lane B inbox (W-30 · W-31 · W-32 · W-33 ·
  W-44). For an agent: **W-46** is the cheapest live item on the board.
- **Cost:** unmeasured — Cowork cloud session, outside cage capture. ~25 tool
  calls including one container run of the engine; no measurement runs, no
  network egress beyond the staged source.

---

## 2026-08-18 — ADR-LAWS renumbered to 0001; the new sequence opens  ·  Cowork
- **Asked:** rename the laws ADR to 0001.
- **Did:** `docs/adr/0013_laws.md` → `docs/adr/0001_laws.md`; all 14 referencing
  files repointed. The register split into **two tables** — the new set in
  `docs/adr/` (ADR-LAWS at 0001, 0002+ unwritten) and the retiring v0.30 set in
  `work/adr/` — and the third numbering restart recorded (v0.26 ran 0001–0015;
  v0.30 restarted 2026-08-09; this one starts now). `0006–0009`, previously
  reserved for M3–M6 under the old sequence, marked **void** — that work gets a
  record in the new set instead. New check
  `test_record_numbers_are_unique_within_a_directory`; 16 assertions pass, 0
  broken links.
- **Decided / open:** **`0001` now exists in two directories at once** —
  ADR-LAWS here, ADR-INGEST-MODES retiring in `work/adr/`. That is deliberate
  and harmless: numbers are ordinals scoped to a directory and a generation,
  and nothing identifies a record by number. It is the cite-by-name rule paying
  for itself — this restart cost one `mv` and a sweep, where under number-citation
  it would have been ambiguous everywhere. The test enforces uniqueness *within*
  a directory, not across them.
- **Next:** unchanged — Arpit's Lane B inbox (W-30 · W-31 · W-32 · W-33 · W-44);
  ratify before drafting successors.
- **Also:** the **ASCII twin is now collapsed** in a `<details>` block, on
  Arpit's instruction — the Mermaid renders on GitHub and is what a human sees;
  the twin is the fallback for terminals, diffs and renderer-less readers, and
  collapsing it is what lets §1 keep both while staying at one screen. Applied
  to ADR-LAWS and `TEMPLATE.md`, written into the convention and CLAUDE.md, and
  enforced by a new check: a record with a Mermaid block must carry an ASCII
  twin, wrapped in `<details>`, with the blank line after `</summary>` that the
  fence needs to render. 17 assertions pass.
- **Cost:** unmeasured — Cowork cloud session, outside cage capture. ~9 tool calls.

---

## 2026-08-18 — the paper, the diagrams, handoffs and the ADR set follow into `work/`  ·  Cowork
- **Asked:** move `docs/paper/` and `docs/handoff/` into `work/`, move both
  architecture diagrams into `work/`, and move every ADR except ADR-LAWS into a
  `work/` ADR directory — new records to be written later.
- **Did:**
  - `docs/paper/` → `work/paper/` · `docs/handoff/` → `archive/handoff/` ·
    `docs/architecture.svg` and `docs/architecture-overview.svg` → `work/`.
  - The eight v0.30 records → **`work/adr/`**, each stamped
    **superseded-pending** (Arpit's call when asked): still live, still
    citable, replacement planned. **ADR-LAWS stays in `docs/adr/`** with the
    register and `TEMPLATE.md`; new records are written there.
  - **A record's directory is now its state** — `docs/adr/` live ·
    `work/adr/` superseded-pending · `archive/adr/` superseded (and
    archive is not evidence). A record moves down one step **in the same change
    that accepts its successor, never before**, so no claim is ever ungrounded.
    Written into `CLAUDE.md`, the register, `work/README.md`, `work/adr/README.md`
    and `archive/adr/README.md`.
  - `docs/` is now `PLAN.md`, `GLOSSARY.md`, `index.md`, and `adr/`
    (register + TEMPLATE + ADR-LAWS). `docs/index.md` rewritten: the OKF bundle
    is `docs/` + `work/`, and the index spans both.
  - `tests/test_adr_ownership.py` extended to span both record directories, plus
    a new check that the register's link for each record points at the file that
    actually exists. 15 assertions, all pass.
  - Every relative link re-resolved: **0 broken** under the case-strict checker.
- **Decided / open:** the eight records were **not** archived — archiving them
  would have stripped the grounding from every claim that cites them (`src/`
  docstrings, CHANGELOG, PLAN, the compare docs) with nothing yet written to
  replace it. Superseded-pending keeps them citable while the new set is
  drafted. **Ratify before replacing:** four of the eight are still ⏳ proposed
  (W-30, W-31), and a successor to an unratified record inherits its ambiguity.
  No successor has been drafted yet.
- **Next:** unchanged — Arpit's Lane B inbox (W-30 · W-31 · W-32 · W-33 · W-44).
  The ratifications now gate the ADR rewrite as well as the shipped code.
- **Cost:** unmeasured — Cowork cloud session, outside cage capture. ~20 tool
  calls, no measurement runs, no network egress.

---

## 2026-08-18 — `work/` becomes the shared memory; the ADR system is rebuilt  ·  Cowork
- **Asked:** stand up a `work/` directory and an ADR system to a specified
  structure, seed every file with a how-to-use header, move the existing docs
  in, and encode all of it in `CLAUDE.md` so future sessions inherit it
  without being told.
- **Did:**
  - **Moved** (via `git mv`, history preserved): `docs/{WORKLOG,INTERVIEW,OPEN-WORK,DOC-REGISTRY}.md`
    → `work/`; `docs/{open,archive,compare,proposals}/` → `work/`;
    **`docs/conformance/` → `work/regression/`**. `docs/` keeps PLAN, GLOSSARY,
    paper, handoff, adr, index.
  - **Created:** `work/README.md` (the map + the three cross-cutting rules),
    `work/IMPLEMENTATION.md` (milestone log, seeded from `git tag` + CHANGELOG +
    the filed runs), `work/MACHINE.md`, `archive/adr/README.md`.
  - **Rewrote:** `archive/README.md` (archive-is-not-evidence + a live
    successor per row), and the how-to-use headers of OPEN-WORK, INTERVIEW,
    WORKLOG, and the `open/ compare/ proposals/ regression/` READMEs.
  - **OPEN-WORK** gained its six rules and split into **two lanes** — Lane A
    agent-executable, Lane B needs Arpit — ordered independently.
  - **INTERVIEW** gained four maintained sections (state of play · in flight +
    next step · standing constraints · lessons learned) ahead of the history.
  - **ADR system rebuilt:** files renamed `000N_name.md`; every record carries a
    `**Name:**`, `**Owns:**` and `**Laws:**` line and is **cited by name** in
    prose (313 citations rewritten); `README.md` is now the register +
    convention + **ownership table**; `TEMPLATE.md` rewritten to §1-humans
    (one screen, Mermaid **and** its ASCII twin) / §2-agents with a **veto
    condition written as a condition to check**; **+ADR-LAWS** — the laws have
    one home (`CLAUDE.md` §Non-negotiable constraints, now named L1–L7) and no
    record restates them.
  - **`tests/test_adr_ownership.py`** — the executable twin of the ownership
    table. It already caught one real restatement (ADR-URL-MIDDLEWARE was
    paraphrasing L1/L4), now fixed.
  - **`CLAUDE.md`** gained **§Documentation discipline** (three-file session
    discipline · the OPEN-WORK rules · archive-is-not-evidence · the concurrent
    -session and ground-truth hazards · the ADR standing rules), and three stale
    passages were corrected: §Layout, *"numbering continues at 0016"*, and
    *"`src/fux/` does not exist yet"*.
  - **`fux.toml`**: `work` added to `[sources] dirs`, or the engine stops being
    able to answer questions about its own state.
  - **Link integrity:** every relative link in every live doc re-resolved —
    0 broken under a **case-strict** checker (macOS's case-insensitive FS had
    silently "fixed" one link to `glossary.md`; filed as a lesson).
- **Decided / open:** frozen artifacts were **not** rewritten — the
  pre-registrations and the `work/regression/<date>-*/` run documents keep their
  pre-move paths, with the move map recorded in `docs/adr/README.md` §Path note.
  `WORKLOG.md`'s own past entries **were** touched, for the ADR-name rename
  only; that is the one mechanical exception the append-only rule allows, and
  this is it being said out loud. **W-33 is nearly closed** (the contradiction
  is gone; what remains is confirming the convention) and **W-32's cost of
  staying open dropped**. Nothing else in the queue changed state.
- **Next:** Arpit's Lane B inbox — five decisions in one sitting (W-30 · W-31 ·
  W-32 · W-33 · W-44). An agent should meanwhile take Lane A: **M4 first**, per
  the v0.32.0 handoff §5.
- **Cost:** unmeasured — Cowork cloud session, outside cage capture. Roughly one
  long session: ~40 tool calls, no measurement runs, no network egress.

---

## 2026-08-12 — Worklog mining: inbox, filed dates, two-strikes, Cost line  ·  Cowork
- **Asked:** what more can the worklog teach so time/money isn't wasted and open
  items close on time.
- **Did (Arpit's explicit go):** OPEN-WORK header gains a **Blocked on Arpit inbox**
  (the ratification package + W-44, dated) and every row a **`filed` date**, with
  the 5-day rule: an aging `OPEN·human` row is named, with its age, in every
  session's first output. CLAUDE.md's Triage section gains **two strikes → a gate**
  (a twice-recorded lesson is gated in the same change that records it) and the
  mandatory worklog **`Cost:` line**. Mirrored in cage (plus its new MACHINE.md)
  and milo. DOC-REGISTRY rows bumped.
- **Decided / open:** unchanged — the inbox holds five decisions in one sitting;
  W-22/M2 starts after Arpit reads the R2 verdict.
- **Next:** Arpit reads the Phase 0 report + ratification package (inbox, day 0).
- **Cost:** unmeasured — Cowork cloud session, outside cage capture.

---

## 2026-08-13 — v0.32.0 released to PyPI; branches cleaned  ·  Claude Code
- **Asked:** commit everything, merge to main, delete stale branches, publish a
  new version.
- **Did:** fast-forwarded `main` to the M2 branch (13 commits, **no merge
  commit** — zero divergence). Bumped `0.30.0 -> 0.32.0` and cut the CHANGELOG
  section; **0.31.x was never published, so its work ships here**. Pushed,
  waited for CI, and confirmed **all 10 matrix jobs green** (linux/macos/windows
  x py3.11-3.14 + build + gate) before releasing — the merge wall has no
  required checks, so that check is the session's job. Tagged `v0.32.0`,
  published the GitHub release, and the PyPI workflow succeeded.
- **Verified black-box from PyPI, not from the green workflow.** Both archived
  release mistakes were re-run as checks: the first `pip install` failed with
  *"no matching distribution found"* on **Python 3.9.6** against
  `requires-python >=3.11` — the exact false signal that once reached a filed
  conformance doc — so it was re-run on 3.14 and installed fine. Then the
  *behaviour* was asserted rather than the version string: the published wheel
  exposes `build`/`find`/`answer`, builds the accelerator on ingest, and
  **`ask` == `ask --scan` byte-identically**. The differential law holds in the
  shipped artifact.
- **Branches:** 6 remote branches were already deleted upstream (stale
  tracking refs, pruned). Of the rest, **three local branches were UNMERGED**
  (v0.6.0/v0.7.0/v0.18.0 era, 5 commits reachable from nowhere else). Rather
  than destroy them, their tips were tagged `archive/pre-reset/*` and pushed
  **before** deletion. `main` is now the only branch, local and remote.
- **Decided / open:** shipped with **ADR-ACCELERATOR, 0001, 0010 and 0011 all still
  ⏳ proposed** — the release does not ratify them. CLAUDE.md's "Package
  identity" section now says `0.30.0.dev0` against a released `0.32.0`; it is
  an agent-steering file, so that is logged as W-32's fourth stale passage
  rather than silently corrected.
- **Next:** Arpit reads the ratification package (5 decisions), then W-44/W-45.
  M3 and M4 are both unblocked; the M4 pair is written and waiting.

## 2026-08-12 — M2 ships: the T1 accelerator, R3 PASS  ·  Claude Code
- **Asked:** Phase 1 of the v0.32.0 program — W-22 / M2, the T1 accelerator —
  after Arpit said "go" twice (once for Phase 0, once for the M2 design plan).
- **Did:** design plan first, as the prompt required, then built it.
  **`query/rank.py` is the load-bearing decision**: the accelerator generates
  candidates and statistics only, and one shared scorer sorts for both paths,
  because float addition is not associative and a term-major accumulation
  would break byte-identity while being logically correct. Derived plane under
  `.fux/runtime/`: 128-posting block lines plus a 40-byte fixed-width binary
  offset table carrying `mx`/`mnw`/`first_doc`/`last_doc` — cheaper than B5's
  string-slicing and it keeps the block line valid JSON. Skipping is
  rarest-term-first with a rounding-aware bound. Two build-time invariants
  refuse to build an accelerator that could disagree with scan. Also: `fux
  build`, `find`, `answer`, `--scan`, `--hybrid`, a doctor check, the dense
  lane, and RRF ported with its archived tests.
- **Decided / open:** **R3 PASS — worst-case p95 27.2 ms vs a 150 ms bar**
  (scan: 4 248.8 ms) on 8 870 RFCs. Differential green over 5 536 comparisons
  and all 50 graded goldens. **Hybrid ships default-off on measurement:** net
  −6 on the graded corpus, and it breaks every no-answer query — the exact
  mechanism INTERVIEW item 5 already warned about. Three findings worth
  keeping: (a) **the differential harness was blind** until mutation testing
  forced a `top` sweep — a zero bound passed at `top=5`; (b) **PLAN's class-3
  list is wrong** (`q008`/`q017` are not known failures); (c) **filing Phase
  0's evidence into `docs/` contaminated the corpus it measured** — fixed by
  dot-prefixing, filed as W-45. ADR-ACCELERATOR written, ⏳ proposed. T2 stays
  unbuilt: R3's tripwire did not fire.
- **Next:** Arpit ratifies ADR-ACCELERATOR (M2's code is shipped under it) and the
  four-item package. Then M4 or M3 — both unblocked, handoff §5 recommends M4.

## 2026-08-12 — Triage-first stop-rule added to CLAUDE.md  ·  Cowork
- **Asked:** Arpit asked why hours of sessions closed no open items, then directed:
  the agent should have said sooner that everything was blocked on him — "money,
  time, everything is being wasted."
- **Did:** on his explicit instruction, added a **Triage first** section to
  CLAUDE.md (also to cage and milo): if every open item is `OPEN·human` or gated on
  a verdict he hasn't read, the session's first output is the blocked-on-Arpit list
  in ≤3 lines, then it stops — no invented scope. DOC-REGISTRY row bumped. Note:
  fux *was* closing items (W-42, W-43 today); the defect was burying "Next: Arpit
  reads…" at the end of long sessions instead of leading with it.
- **Decided / open:** unchanged — W-30/31/32/33/44 await Arpit; W-22/M2 starts only
  after he reads the Phase 0 report + ratification package.
- **Next:** Arpit reads the Phase 0 report and the ratification package.

---

## 2026-08-12 — Phase 0 of the open-items program: the backlog clears  ·  Claude Code
- **Asked:** execute Phase 0 of `handoff/v0.32.0-open-items-handoff.md` — W-43,
  W-33, W-42, and the W-30/31/32 ratification package — then stop before M2.
- **Did:** four commits.
  1. Committed the prior session's uncommitted restructure as its own unit
     (a stale zero-byte `.git/index.lock` with no owning process had to be
     removed first).
  2. **W-43 closed.** Both executed pairs moved to `archive/` stamped
     `status: implemented` + ADR link (the fux-playground pair still said
     "proposed"). Both READMEs reconciled; the two-archives distinction is now
     a table. Fixed the third stale claim: the M1-T0-slice banner asserted
     Arpit's ruling sent executed pairs to the *root* archive — that ruling
     scoped the v0.26 doc set. `archive/handoff/` now lists live work only.
  3. **W-42 closed — R2 is 3/3 PASS.** One line of `fux.toml`; no engine code.
     Q3's frozen target ranks #2 from a cold tree behind another archived hit
     carrying the same `[11, ∞)` interval. R1 re-asserted (double-ingest
     byte-identical). Index +45.1 % (942,479 → 1,367,888 raw) for +34 docs.
     Filed as `conformance/2026-08-12-r2-close/`.
  4. **W-33 + the ratification package.** `handoff/v0.32.0-adr-numbering.diff`
     (verified to apply) plus `handoff/v0.32.0-ratification-package.md` —
     five decisions, each answerable without reading anything else.
- **Decided / open:** three findings the handoff did not anticipate.
  **(a)** A post-hoc probe shows the newly-indexed v0.26 doc set answering
  questions about the *current* engine — *"what is the ingest cache"* returns
  5/5 archived results describing a subsystem CLAUDE.md forbids porting back.
  Filed as **W-44** with three options and a recommended *shape* (annotate,
  never reorder); **not fixed** — five hand-picked probes on one corpus is not
  grounds to ship a ranking change. **(b)** `CLAUDE.md.proposed` does not
  exist; the rewrite has been the live file since `3892c55`, so "adopt" means
  deleting a header and "reject" means reverting ~800 lines every session has
  followed. W-32's DoD was corrected. **(c)** ADR-INDEX-FORMAT's recorded "#1" for
  R2-Q2 is "#2" today, caused by README.md growing a `.fux/` table — the ADR
  now dates its ranks. **Recommendation on W-33: reading A** (restart at
  0001); the defect is that the policy is written in two places, not which
  policy it is.
- **Next:** Arpit reads the Phase 0 report and the ratification package. Phase 1
  (W-22 / M2, the T1 accelerator) starts only after the R2 verdict is seen —
  §B of `handoff/v0.32.0-open-items-prompt.md`.

## 2026-08-12 — OPEN-WORK becomes an index; the v0.32.0 open-items handoff  ·  Cowork
- **Asked:** reduce `OPEN-WORK.md` to one line per open item with detail in
  individual files, purge everything done, and produce a handoff + prompt to
  implement all the open items.
- **Did:** `work/OPEN-WORK.md` rewritten as an index (10.5 KB → 4.4 KB): one row
  per open item, no narrative, **every DONE item deleted** (W-20/W-21/W-40/W-41
  rows gone — their record is the ADR + this log). New `work/open/` with a README
  stating the contract and **13 detail files**, one per open item. Three items that
  were only prose before are now tracked ids: **W-31** (ADR-URL-MIDDLEWARE/0011 ratification),
  **W-32** (CLAUDE.md adoption), **W-33** (the ADR-numbering contradiction), plus
  **W-42** (close R2-Q3) and **W-43** (the archive-law debt). Wrote
  `handoff/v0.32.0-open-items-{handoff,prompt}.md`. Repointed `PLAN.md` and
  `INTERVIEW.md` off the dead `OPEN-WORK §2` anchor; fixed a broken relative link in
  `adr/README.md` (`../` → `../../` for the archived ADR path); DOC-REGISTRY +
  handoff/README rows updated.
- **Decided / open:** the closure rule is now explicit — **an item's detail file and
  its index row are deleted together when it closes**; `work/open/` holds open work
  only, which is what makes the index trustworthy. The handoff **refuses** to
  package M2–M7 as one buildable unit: that would break the repo's own
  plan→handoff→prompt-per-milestone law and produce confident slop across ~3 500
  LOC. It carries a full build spec for **M2 only**; each later milestone is entered
  through its own pair, written at the end of the phase before it. M4 is sequenced
  **before** M3 (both are legal after M2) because two filed proposals graduate into
  M4 and its API shape is the expensive thing to retrofit. `CLAUDE.md`'s stale
  `OPEN-WORK §2` pointer was **deliberately left in place** and added to W-32 — law
  7, agent-steering files are proposed, never auto-applied, even for a pointer.
- **Next:** run Phase 0 of `handoff/v0.32.0-open-items-prompt.md` §A (Opus) — W-43,
  W-33, W-42 and the W-30/31/32 ratification package — then stop for Arpit's R2
  verdict before Phase 1 (M2).


## 2026-08-12 — the playground leaves the repo and becomes graded  ·  Claude Code
- **Asked:** execute the v0.31.0 fux-playground handoff + prompt (W-41) —
  delete `examples/` from this repo, and build `~/my_programs/fux-playground`
  as a graded sibling: 10 internal-developer-platform documents, 10 URLs,
  ~50 golden queries, a committed file-only index with a staleness guard.
- **Did:** built the sibling repo (35 files, one local commit, **no remote**):
  ten Calder Group / Helix documents (107–297 lines, real frontmatter tags and
  cross-links — 88 edges resolve), `goldens/queries.jsonl` with 50 ranked
  queries across seven hazard classes, stdlib-only `tools/check.py`
  (`--goldens` / `--index-guard` / `--all` / `--verbose` / `--report`, and
  deliberately no `--update-goldens`) and `tools/smoke_urls.py` (restores
  `.fux/index/` on every exit path). In this repo: `examples/` deleted, every
  live reference repaired (README item 5 → the sibling; DOC-REGISTRY row
  retired; architecture.svg caption), **SETUP-PLAYGROUND** written, OPEN-WORK W-41,
  PLAN status lines, GLOSSARY +3 terms, handoff README row.
- **Verified (all four, real output):** `check.py --all` → **41 pass, 9 xfail,
  0 unexplained**, guard clean. Guard *proven to fail*: perturbed one P1-RERUN
  heading → exit 1 naming the record and the moved fields (`sha`, `ver`,
  `wlen`), reverted → clean. **10/10 URLs fetched through real Chrome 151 on
  port 9299**, zero substitutions, index restored (`git status` clean). fux's
  own suites: **221 passed** (`uv run pytest -q tests tests_e2e`).
- **Decided / open:** goldens assert **ranks, never scores**; URL docs are a
  runtime smoke test and are **not graded**; the committed index is
  **file-only** (the `--refresh-urls` carry-forward trap is the reason).
  Introduced `known_failure` (pytest-style `xfail`) so the 9 real engine gaps
  are *named with a mechanism* rather than leaving a permanently red suite —
  an `XPASS` fails the run when a gap closes. **Two engine findings recorded,
  not fixed** (out of scope): markdown **link targets are tokenized into the
  linking doc's body** (`glossary` `df=9` as indexed vs `df=1` in prose), and
  small-corpus `df` + BM25 `tf` saturation make term *presence* beat
  *aboutness*. **For Arpit:** the ADR numbering contradiction (took 0012;
  CLAUDE.md still says 0016), and fux-playground's long-term home (no remote
  by design).
- **Next:** Arpit's call on the two open questions; then W-22 (M2 accelerator),
  where five of the nine named gaps are the acceptance targets.

## 2026-08-11 — v0.31.0 executed: `.fux/` declared, URL source moved in  ·  Claude Code
- **Asked:** execute the v0.31.0 handoff + prompt (W-40) — systematize
  `.fux/`, move the URL list and middleware into it, move the CDP tunables
  into `fux.toml`.
- **Did:** new `store/fuxdir.py` (`ensure_layout` write-if-missing README +
  narrow `.gitignore`; `derived_dir` with spec-exact `CACHEDIR.TAG`), called
  at ingest start. `[sources.url]` now takes `urls_file` (default
  `.fux/sources/urls`) and an opaque `[sources.url.config]` table; inline
  `urls` is a hard error. New `urlsrc.read_urls` (comments/blanks, `file:lineno`
  scheme errors, missing-file loud only under `--refresh-urls`, empty valid,
  dedupe+sort) and a `configure(config)` hook called once before `connect()`.
  `git mv`'d the middleware to `.fux/middleware/cdp.py`; its constants became
  defaults `configure` overrides. `fux doctor` gained the `git check-ignore`
  assertion on `.fux/index` (error) and an undeclared-entry warning — `Check`
  grew a `level` field so warnings don't fail the exit code. **Root
  `.gitignore` had a `.fux/*` blanket that would have eaten `sources/` and
  `middleware/`; removed.** ADR-FUX-DIR written, ADR-URL-MIDDLEWARE amended in place, +4
  GLOSSARY terms, README/CHANGELOG/fux.toml/registry/OPEN-WORK/INTERVIEW
  updated; handoff + prompt archived as `implemented`.
- **Decided / open:** the handoff's §10 open question closed **as built** —
  `.fux/README.md` is generated at ingest, not by `doctor --fix` (reversible;
  ADR-FUX-DIR §Alternatives records it). **For Arpit:** ratify ADR-FUX-DIR (and
  ADR-URL-MIDDLEWARE); the one-line CLAUDE.md layout addition is **proposed, not
  applied** at `archive/handoff/v0.31.0-claude-md-layout.diff` (verified to apply
  cleanly). Note `git log --follow .fux/middleware/cdp.py` shows no pre-move
  history — the root file was staged but never committed, so there was none.
- **Verified:** 217 tests green (`.venv/bin/python -m pytest tests -q`);
  triple ingest on this repo byte-identical (0 shards written on runs 2–3);
  `fux ask` still cites; `git check-ignore` confirms committed planes tracked
  and `runtime/`/`cache/` ignored.
- **Next:** W-22 — M2's T1 accelerator (nothing blocks it).

## 2026-08-10 — .fux layout decided; v0.31.0 handoff + prompt written  ·  Cowork
- **Asked:** (1) URL list out of `fux.toml` into a separate file under
  `.fux/` (the list could be huge); (2) move `cdp_middleware.py` into
  `.fux/` too; (3) define `.fux/` systematically; (4) move the CDP
  tunables into `fux.toml`. Research it, then produce a handoff + prompt
  (not a direct build).
- **Did:** researched the grounding conventions — CACHEDIR.TAG spec
  (bford.info/cachedir), pytest/mypy self-tagging cache dirs (.gitignore +
  CACHEDIR.TAG written into their own dir), Husky's committed `.husky/`
  (consumer-edited code in a committed dotdir), PEP 518's `[tool.*]`
  opaque-table pattern. Ran the debate gate: the naive "typed CDP keys in
  config.py" design was BLOCKED (couples core to one middleware's
  vocabulary, against the adapter cap's spirit) and replaced with an
  opaque `[sources.url.config]` table passed verbatim to a new optional
  `configure(config)` hook. Decided layout: committed planes `index/`,
  `sources/`, `middleware/` vs derived `runtime/`, `cache/` (reserved for
  M2/M4, CACHEDIR.TAG-tagged), self-describing write-if-missing
  `.fux/README.md`, `.fux/.gitignore` that lists ONLY derived dirs, and
  two new doctor checks. Wrote the pair:
  `handoff/v0.31.0-fux-dir-layout-handoff.md` +
  `…-prompt.md` (**Sonnet** — closed design, test-verifiable DoD).
  A working reference implementation of the urls-file half exists in this
  session (all tests green) but was deliberately NOT committed — the
  handoff is the spec of record and Claude Code executes it clean.
- **Decided / open:** urls file = `.fux/sources/urls`, one per line,
  line-numbered loud errors; middleware = `.fux/middleware/cdp.py`
  (git mv); no back-compat for the hours-old root placement. ADR-FUX-DIR
  will record the layout; ADR-URL-MIDDLEWARE gets amended in place (still
  proposed). Open (non-blocking): reserved dir names `runtime/`/`cache/`
  are M2/M4's to rename; README generation at ingest vs doctor --fix.
- **Next:** Arpit pastes the prompt into Claude Code (Sonnet) and runs
  the build; ratifies ADR-URL-MIDDLEWARE + ADR-FUX-DIR after.

## 2026-08-10 — URL source via consumer middleware (CDP template); ADR-URL-MIDDLEWARE proposed  ·  Cowork
- **Asked:** (1) a file the package consumer can edit to connect to Chrome
  DevTools Protocol, used by fux to ingest URLs — "something like a
  middleware"; (2) why the committed index is many small JSONL files
  (answered in-chat: fixed-256 id-hash sharding per ADR-INDEX-FORMAT; ~60 docs →
  ~60 occupied shards of header + 1 record; by design, amortizes at scale).
- **Did:** built the consumer-middleware URL source, fully wired.
  `fux.toml [sources.url] middleware/urls/meta` → `ingest/urlsrc.py` loads
  the consumer's file (`fetch(url)->str` required, `connect`/`close`
  optional) — **only** under the new `fux ingest --refresh-urls`; a plain
  ingest carries `url:` records forward byte-identically (offline law +
  the writer's implicit-deletion rule). Records: `src:"url"`,
  `meta:"hashed"` **default** (first exercise of the non-git law;
  `title_h = term_hash(title)`, decided here), `"plain"` per-source
  opt-in. Failed fetch keeps the prior record; deconfigured URLs
  reconcile only on refresh. Edges: absolute http(s) links now resolve to
  in-corpus `url:` docs; `code`-span basenames stay file-only. Shipped
  `cdp_middleware.py` (repo root, consumer-owned): CDP over hand-rolled
  RFC 6455 WebSocket + deterministic HTML→markdown, ported from
  `archive/v0.26/src/fux/ingest/{ws,cdp,htmlmd}.py` (the accepted
  2026-07-21 `render="cdp"` path). Core still has zero network code/deps.
  Tests: `tests/ingest/test_urlsrc.py` (15, all offline via fake
  middleware) + `test_cdp_middleware.py` (9: RFC 6455 vectors/round-trips,
  html→md) — suite green.
- **Decided / open:** ADR-URL-MIDDLEWARE **proposed** (Arpit directed the build in
  session; he ratifies). Numbered 0010 because OPEN-WORK DoDs already cite
  0005–0009 for M2–M6. Adapter cap intact — core ships a generic
  middleware hook, not a URL adapter; all network lives in the consumer's
  file. Owed: GLOSSARY terms, M4 refer-plane fetch path for `src:"url"`.
- **Next:** Arpit ratifies ADR-URL-MIDDLEWARE; optionally uncomment `[sources.url]`
  in `fux.toml` and dogfood a real page via `fux ingest --refresh-urls`.

## 2026-08-11 — M0+M1 committed, pushed, and released as v0.30.0  ·  Claude Code
- **Asked:** commit everything from the M0+M1 build session, push, and
  publish a new version.
- **Did:** synced with concurrent doc changes (Arpit's archive-convention
  ruling — root `archive/` only, `archive/` retired — already landed
  in `OPEN-WORK.md`/handoff docs/ADR-INDEX-FORMAT by the time this ran); re-ran the
  full suite (164 green) and re-ingested this repo's dogfood index to
  reflect it; bumped `__version__` to `0.30.0` (dropping `.dev0` — the
  project's established per-milestone release cadence, matching how
  `0.22.0` shipped "the rebuild ships"); dated the CHANGELOG entry;
  committed the whole M0+M1 build (`c52948b`); pushed straight to `main`
  (no PR gate — required status checks were removed 2026-07-22).
  **CI caught a real bug**: `windows·py3.11`/`py3.14` went red —
  `fux doctor` printed a Unicode checkmark that crashes on Windows'
  default console codepage (`UnicodeEncodeError`, process exits 1 instead
  of printing). Fixed (`83c1888`, ASCII `[OK]`/`[FAIL]` markers + a
  `PYTHONIOENCODING=ascii` regression test), documented the catch in
  ADR-INDEX-FORMAT (`87543b1`), re-verified the full ubuntu+macos+windows matrix
  green, then cut `v0.30.0` via `gh release create` → PyPI publish fired
  and landed (confirmed live on the first poll — 165 tests, 3 commits
  total this session).
- **Decided / open:** the archive-convention follow-up (adding
  `archive/v0.26-docs` to `fux.toml` sources so R2-Q3 becomes literally
  satisfiable) is explicitly deferred to the next build turn, per
  `OPEN-WORK.md`'s own note — not done here.
- **Next:** M2 (W-22, the T1 accelerator) is unblocked. See `OPEN-WORK.md` §2.

## 2026-08-10 — Agent search-API landscape researched; three proposals filed  ·  Cowork
- **Asked:** how [platform.parallel.ai](https://platform.parallel.ai) works
  engineering-wise — both the retrieval engine and the platform/tenancy layer —
  "because we are also trying to build something along the same lines." Then:
  save the research into the repo.
- **Did:**
  - Researched Parallel Web Systems end to end (own crawler `ShapBot`, own
    index, no federation; $230M raised / $2B valuation) plus the peer set —
    Perplexity, Exa, Brave, Tavily, Linkup, Firecrawl, Jina — and the web-index
    cost literature (Wilson Lin, turbopuffer, Quickwit, Common Crawl,
    Cloudflare Pay Per Crawl). Every claim traced to a public source; vendor
    claims, third-party reports and inference kept separate.
  - Filed **three proposals**, all `status: proposed`, none built:
    - [`proposals/agent-search-landscape.md`](proposals/agent-search-landscape.md)
      — the research note and evidence base (a preserved note, in the same
      spirit as `wavelet-self-index.md`).
    - [`proposals/caller-set-freshness-policy.md`](proposals/caller-set-freshness-policy.md)
      — `fetch_policy`-style per-query staleness tolerance for the refer plane.
    - [`proposals/token-budget-retrieval.md`](proposals/token-budget-retrieval.md)
      — byte budget as the answer limit instead of `k`.
  - Updated `proposals/README.md` (index), `DOC-REGISTRY.md` (proposals row),
    and `OPEN-WORK.md` §1 (pointer so the M4 handoff picks both up).
- **Decided / open:**
  - **Three convergences confirmed, independently arrived at:** (1) the index
    is a cache with a caller-set TTL, not the source of truth — literally the
    refer plane; (2) the retrieval unit is a token budget, not a result count;
    (3) the retrieval unit is the *passage*, not the document — four
    independent arrivals (Parallel, Perplexity, Exa, Wilson Lin).
  - **The wedge is now written down and referenced:** Parallel's own FAQ says
    they crawl "only publicly available web content **without login
    credentials**." The whole funded peer set is locked out of the corpus the
    CLAUDE.md litmus is about. Cloudflare Pay Per Crawl (HTTP 402 +
    `crawler-price`) is an existential cost risk for them and a non-event for
    an inside-the-firewall index.
  - **Two external supports for decisions already taken:** Exa shipped a Rust
    BM25 inverted index *after* saying "we were neural all the way" — support
    for the full-postings lexical core of ADR-INDEX-FORMAT. And the hyperscaler markup
    on search primitives is 20–30× (Wilson Lin's cost table) — the `$0`/stdlib
    law is the economically correct architecture, not an ascetic one.
  - **Open (Arpit):** whether the two API-shape proposals get folded into the
    M4 handoff when W-24 starts, or stay parked. Nothing here changes a W-nn
    state or a prediction; no code touched.
- **Next:** unchanged — **W-22 (M2, the T1 accelerator)** is still the next
  build item. When W-24 (M4) is spec'd, read both API proposals before writing
  the handoff.

## 2026-08-10 — M0+M1 built: scaffold, canonical store, ingest, ask — R1 PASS, R2 2/3 PASS  ·  Claude Code
- **Asked:** execute the M0+M1 T0-slice handoff/prompt — build `src/fux/`,
  the canonical committed store, git-dir ingest, and scan-based `fux ask`,
  dogfooded on this repo, ending in ADR-INDEX-FORMAT and measured R1/R2.
- **Did:**
  - **Phase 0:** found the tree dirty (60 files staged from an earlier
    unfinished prep session — ADR renumbering, the index-format compare doc,
    the AcmePay playground fixture, a proposed CLAUDE.md rewrite). Asked;
    committed it (`6960237`) before starting, per the handoff's own "stop if
    dirty" instruction.
  - **M0 scaffold:** `src/fux/` (`store/`, `derive/` stub, `query/`,
    `ingest/`, `refer/` stub, `cli.py`, `errors.py`, `config.py`,
    `doctor.py`); `pyproject.toml` at `0.30.0.dev0`, zero runtime deps;
    restored `scripts/ai-review.sh`/`apply-branch-protection.sh` (present in
    live CI config, missing from the tree since the v0.26 archive move);
    fresh `CHANGELOG.md`. `fux --version`/`doctor` clean; build/twine/sdist
    checks clean.
  - **Canonical store** (`store/`): writer/reader for sharded doc-major
    JSONL, collision tracker, canonicalization boundary (no floats/nulls,
    NFC-enforced). Three schema fields the compare doc named but didn't
    fully specify — `sha` (hash algorithm), `ver` (semantics), `meta`
    (shape) — resolved by asking, not guessing (handoff §guardrails).
  - **Opus review checkpoint** on `store/` (handoff §11, before building on
    top of it): 2 blockers (dict keys never NFC-validated; the reader's
    `str.splitlines()` breaks on U+2028/2029/0085 the writer legally emits,
    so the store couldn't read its own output) + 10 should-fix/nit findings,
    all fixed — golden-vector tests, atomic writes, header field validation,
    cross-shard duplicate detection, shared-tracker collision test added.
  - **Ingest** (`ingest/`): git-dir adapter (sorted walk, skip-with-reason);
    ported tokenizer/frontmatter/FuxVec (incl. the 7.9 MB bundled model,
    asked and decided to bundle now rather than defer); new `ref`/`tag`/
    `code` edge extraction (not a direct port — new grade-int scheme).
    Asked and resolved a real spec conflict: the handoff fixes shard count
    at 256, but the already-committed `examples/playground/fux.toml` set
    `shards = 16` — kept the store's fixed-256 design (already
    Opus-reviewed), corrected the playground config instead.
  - **Query** (`query/`): B2 byte-prefilter scan + ported BM25F (2-field,
    `path` dropped per ADR-INDEX-FORMAT), corpus stats derived in-pass, never
    stored.
  - **Dogfood + R2:** ran the three frozen questions against this repo's own
    docs. Q1 passed; Q2 initially missed top-5 (a glossary's dictionary-style
    term repetition outranked the focused answer) — traced to the tokenizer
    having no stopword filtering (neither the archive nor the handoff spec'd
    one); asked, added it, re-verified Q1+Q2 (not just the one that had been
    failing). Q3's citation target (`archive/v0.26-docs/…`) doesn't
    exist — a pre-existing, independently-flagged discrepancy
    (`archive/README.md`, 2026-08-09, predates this session); asked,
    reported as testing a stale assumption rather than moving `archive/`
    content as a side effect of this ADR.
  - **Playground walkthrough:** all three questions + the superseded-pair
    check pass with real citations; double-ingest is a no-op; a one-doc edit
    changes exactly one shard file. Fixed two doc bugs in `PLAYGROUND.md`
    itself (never the fixture, per the handoff's rule): a stale "16 shards"
    comment and a hardcoded example shard filename that doesn't exist under
    the real sparse assignment.
  - **R1:** double-ingest byte-identical, verified locally; wired into CI as
    `tests_e2e/test_determinism.py` (already runs on the existing
    ubuntu+macos+windows matrix).
  - **ADR-INDEX-FORMAT** written and accepted — freezes the schema, canonical rules,
    unicode policy, and every build-time decision above.
  - Tests: 164 passing (unit + e2e), up from 0 at session start.
- **Decided / open:** ADR-INDEX-FORMAT accepted. Open for Arpit: whether to move
  `archive/v0.26-docs/` into `archive/` (resolves R2 Q3
  for real, pre-existing call, not created by this session); ratify
  ADR-INGEST-MODES. Nothing blocks M2.
- **Next:** start W-22 (M2 T1 accelerator) — see PLAN §M2. This session's
  changes are built and tested but **not yet committed**; confirm commit
  scope/message with Arpit before landing.

## 2026-08-10 — one archive, at root (Arpit's ruling) ·  Cowork
- **Asked:** everything which needs to be archived should be in the root
  archive dir.
- **Did:** flattened the double-nesting — `archive/v0.26/archive/v0.26-docs`
  → **`archive/v0.26-docs/`**, remaining nested collection →
  **`archive/v0.26-implemented/`** (master-prompt, PLAN-v0.26, executed
  v0.20–v0.26 handoff pairs); `archive/v0.26/` is engine-only again.
  Removed `archive/` (README parked in `_to_delete/` — device cannot
  delete; empty dir invisible to git). Wrote `archive/README.md` as the
  root-archive index + the standing convention. Re-pointed 12 live files;
  recorded dated resolutions in ADR-INDEX-FORMAT, OPEN-WORK, and the M1 handoff
  banner (the R2-Q3 discrepancy is now CLOSED; making Q3 satisfiable is a
  one-line fux.toml follow-up, parked for the M2 turn).
- **Decided / open:** standing rule — archived v0.30 artifacts get
  version-named root entries (`v0.30-…`); no doc-level archives ever.
- **Next:** Arpit reviews + commits (this sits alongside the staged M1
  work); then M2.

## 2026-08-09 — REVISION 2: JSONL format decided, ADRs renumbered, plan rewritten, first build packaged  ·  Cowork
- **Asked:** (across the evening) will the JSONL index work — verify against
  the paper; sample index block with per-property explanation; then: create
  a detailed plan, a handoff + prompt, and restart ADRs from 0001.
- **Did:**
  - **Benched the format live** (cloud sandbox): naive scan 653 ms@5k;
    prefilter 191 ms; sorted term-major bisect **0.035 ms**; common-term
    trap measured (df=400k line = 5.1 MB, 397 ms) and closed with
    128-posting block lines + integer `mx` skip (**44 ms**, 12 % parsed);
    git delta test: one-line edit in a 138 MB shard commits 2.5 s, repo
    52 MB after two commits (0.38× pack). Schema samples produced
    (doc-major record with binary-as-property `code`/`tpack`; derived
    block line).
  - **`compare/index-format.compare.md`** (accepted): tiered JSONL T0/T1/T2,
    git-as-Merkle-tree, supersedes MST keyspace + BIC wire for the
    committed plane (amendment notes added there); benches B1–B6 recorded.
  - **ADRs renumbered 0016/0017/0018 → 0001/0002/0003** (Arpit's call);
    32 live files rewritten; frozen artifacts (PRE-REGISTRATION*, conformance
    evidence/) untouched by policy; `adr/README.md` records the policy and
    the "archived ADR-NNNN" disambiguation rule.
  - **PLAN.md rewritten to revision 2**: gate closed (P1 FAIL, option E
    accepted by Arpit — full postings, pruning forbidden outside M8);
    milestones M0–M8 rebuilt around the T0/T1/T2 tiers; **R-series
    predictions** replace the closed P-series; port list updated (MST
    dropped, BIC → T2).
  - **First build handoff + prompt**: `handoff/v0.30.0-m1-t0-slice-*` —
    M0 scaffold + M1 T0 vertical slice (canonical store, git-dir ingest,
    scan `ask`, dogfood on this repo). Debate gate shaped it: R1
    cross-platform byte-determinism named the riskiest assumption (NFC
    rule, ubuntu+macos CI matrix); accelerator explicitly fenced to M2;
    three R2 questions frozen in the handoff so they can't drift. Sonnet
    with one Opus review checkpoint on the canonical writer.
  - OPEN-WORK rewritten (W-20…W-38 ledger, R-table); handoff/compare
    READMEs updated; DOC-REGISTRY bumped; keyspace-unification carries its
    superseded-note.
- **Decided / open:** run the M0+M1 prompt (Arpit); ratify ADR-INGEST-MODES
  naming (non-blocking); paper §4–§6 stale-by-design until M6.
- **Next:** paste `handoff/v0.30.0-m1-t0-slice-prompt.md` into Claude Code
  (Sonnet).

## 2026-08-09 — rev-1 planning artifacts archived to root archive  ·  Cowork
- **Asked:** archive the older plan docs in the root archive.
- **Did:** created `archive/v0.30-rev1-planning/` (with README) and moved:
  both executed handoff pairs (m0-m1-gate → ADR-INGEST-MODES/0002; m1-rerun →
  P1-RERUN) per the handoff lifecycle, plus the two revision-1 design
  diagrams (`architecture-components.svg`, `architecture-index-and-refer.svg`
  — they depict the superseded MST/BIC design). Links fixed in handoff
  README, index.md, DOC-REGISTRY, WORKLOG, INTERVIEW.
- **Decided / open:** the paper stays in place (M6 rewrites it from
  measurements — flagged, not stale-by-accident). `archive/handoff/` now
  holds only the live t0-slice pair.
- **Next:** unchanged — run the M1 prompt.
- **Addendum:** new `work/architecture-overview.svg` (five components, README-ready) and `work/architecture.svg` committed — the rev-2 working diagram (tiers T0/T1/T2, real record shapes, query path, measured numbers); index.md + DOC-REGISTRY updated.

## 2026-08-09 — AcmePay playground corpus added to the M1 slice  ·  Cowork
- **Asked:** a small 10–50 doc set to *play* with — see how Fux and its
  index actually look — in parallel to the formal test cases.
- **Did:** authored `examples/playground/` — 20 fictional AcmePay docs
  (ADRs incl. a superseded 0002→0005 pair, runbooks, API docs with the
  session's webhook/retry vocabulary, postmortems, cross-links, tags),
  `fux.toml` (16 shards), and `PLAYGROUND.md` (walkthrough: ingest, read a
  record, grep a term hash, one-line-diff demo, three questions). Wired
  into the M1 handoff/prompt/OPEN-WORK as a fixture: the corpus is never
  edited by the executing agent; its `.fux/index/` gets committed as the
  format's visible demo.
- **Decided / open:** playground is demo + smoke surface, not a quality
  gate (R-series unchanged).
- **Next:** unchanged — run the M1 prompt.

## 2026-08-09 — pruning-criterion research → compare doc + M1-rerun package  ·  Cowork
- **Asked:** explain P1-GATE in plain terms and propose what to do; then
  "is there a better way than just picking 128 words"; then "why not a
  combination / multiple properties in the index"; then write it and give
  the prompt; then worked before/after examples of the index rows.
- **Also did (same exchange):** added **§7a Worked examples** to
  `compare/pruning-criterion.compare.md` — three before/after index views
  in the committed-row format: (1) `webhooks.md` at k=64 losing `webhook`
  from its own postings vs A+B+C keeping it at *tighter* retention,
  (2) a 1 850-term document showing fixed-k ≈ retention on long docs (the
  budget only matters on short ones) and Rule C legitimately exceeding the
  budget — hence the δ-matching requirement, (3) the **term-major** view,
  where the postings list for `webhook` has lost every document actually
  about webhooks until the sweep restores them, with `df` recomputed after.
  Marked illustrative-not-measured; intended as a shape the executing agent
  can check its output against.
- **Did:** researched the criterion question (Carmel term-centric; Bilkent
  TOIS combination study; Mackenzie SIGIR '24 on re-rank pipelines;
  BitFunnel space numbers; learned-sparse). Wrote
  `compare/pruning-criterion.compare.md` (§humans + §agents, verdict-first,
  implementation contract in §7), `proposals/query-log-pruning.md`, and the
  **M1-rerun handoff + prompt**. Synced compare/proposals/handoff READMEs,
  OPEN-WORK (W-13 respecified, W-14 added).
- **Decided / open (proposed, measured by W-13):** three amendments —
  **(1) gate on recall@20**, not index hit@5: the index is a candidate
  generator feeding fetch-and-re-score, and published work says re-rank
  pipelines absorb pruning's recall loss; **(2) combined selector A+B+C** —
  heading spine ∪ impact budget ∪ per-term backstop — because KL penalises
  terms common across a homogeneous collection (the `webhook`/`webhooks.md`
  failure) and combinations measure ~2× single criteria; **(3) adaptive
  retention budget**, not fixed k. Ruled out on arithmetic: a Bloom
  "recall insurance" plane (~2.4 GB @1M — BitFunnel's own numbers).
  Fallback if pruning fails entirely: index ≈ 0.6–1.5 GB, partial clone +
  external-shards-only become mandatory.
- **Next:** Arpit rules on W-05, then run the M1-rerun prompt (**Opus
  throughout** — the last run failed at measurement design, not coding).

## 2026-08-09 — P1 re-run: the gate FAILED, on a corpus that could test it  ·  Claude Code
- **Asked:** amend ADR-INGEST-MODES with a better name for `inferred`; then execute the
  M1-rerun prompt (make the pruning gate decidable).
- **Did:**
  - **ADR-INGEST-MODES amended.** Arpit's instinct found a real defect: the first draft
    fixed one half of the collision and reproduced the other — `INFERRED` is the
    edge grade for *model-derived*, so the no-model tier could not be
    `inferred`. Naming the AI tier `enriched` vacates `extracted`; giving it to
    the deterministic tier makes the two vocabularies **agree** for zero
    migration. Decision now `extracted`/`enriched` (runner-up `derived`), still
    proposed.
  - **Corpus acquired:** 8 872 RFCs, sha256-manifest-pinned, 0 mismatches
    (`fetch_rfc.py`, a lab tool — network is lab-only).
  - **Corpus gate:** rfc median **967** distinct terms → PASS. repodocs (425),
    acme (32), orbit (36) → FAIL, demoted to secondary. That resolved the
    handoff's "which corpus gates" question mechanically.
  - **PRE-REGISTRATION-v2 committed before any gating number** (`3892c55`):
    recall@20 on the abstract-derived slice, matched retention, PASS/PARTIAL/
    FAIL/VOID.
  - **Ran** 5 arms × 3 rungs (~2 h 15 m), plus three diagnostics. 50 tests green.
- **Decided / open:**
  - **FAIL.** Best arm 0.627 vs unpruned 0.986 at 6 % retention (−35.9 pts vs a
    2-pt bar); −12.7 pts even at 30 %. All validity checks passed; gaps are
    7–27× the standard error. → [P1-RERUN](regression/2026-08-09-pruning-rerun/VERDICT.md).
  - **The compare doc's prediction was falsified in both halves** — arm 4 was
    predicted to match no-pruning and was the *worst*; arm 1 (KL), predicted to
    be the outlier, was the *best*. The counter-signal recorded in the
    pre-registration reproduced on a second corpus.
  - **New mechanism found:** a rule that forces heavily-weighted postings into a
    minority of documents degrades the **whole** index. Proved by restricting to
    the 372/400 queries whose gold document was byte-identical across two arms:
    recall still fell 0.441 → 0.298. A per-document evaluation would never see
    this.
  - **Consequence:** index-and-refer is *not* falsified; the "small index by
    pruning" claim is. Footprint 0.6–1.5 GB at 10⁶ docs; partial clone +
    external-shards-only become mandatory. `storage-architecture` took a size
    amendment (not a reopen); `pruning-criterion` marked ❌ falsified; P1-GATE
    gained a forward pointer and was otherwise left intact.
  - **W-01 stays blocked.** Biggest threat to the verdict, stated in the ADR: the
    eval's verbatim-sentence queries are close to a worst case for pruning.
- **Next:** W-15 — re-measure with a realistic short/keyword query workload,
  fresh pre-registration. It is the one thing that could reasonably overturn this.

## 2026-08-09 — M0a + ADR-INGEST-MODES + M1 executed: the gate ran  ·  Claude Code
- **Asked:** execute the M0/M1 handoff phase by phase without pausing.
- **Did:**
  - **W-00** — committed the reset as its own commit (`7fb81a8`) so the archive
    move and the work on top of it stay separable.
  - **W-03 (hygiene)** — GLOSSARY rewritten for the v0.30 vocabulary (archived
    v0.26 terms explicitly marked not-current); INTERVIEW gained a reset block
    at the top (what changed, why, the five things not to re-litigate);
    DOC-REGISTRY's two ⚠ rows cleared; `work/regression/README.md` created
    (the registry pointed at a path that did not exist).
    **CLAUDE.md rewritten as `CLAUDE.md.proposed` + a diff — proposed, never
    applied**, per the agent-steering-file rule.
  - **W-02** — [ADR-INGEST-MODES](../archive/adr/0001_ingest-mode-naming.md) written as
    `status: proposed` recommending `inferred`/`enriched`; not blocked on
    Arpit's ratification, per handoff §7.
  - **W-04** — `tools/pruning-eval/`: the KL selector as a pure, stdlib-only,
    tested function written for portability into the engine unchanged; a
    three-arm harness (baseline · pruned-with-recomputed-stats · diagnostic)
    over the archived BM25F scorer; 23 tests green. **PRE-REGISTRATION.md was
    committed before any gating corpus ran** (`f5300fc`).
- **Decided / open:**
  - **Harness validated externally**: the fixture baseline reproduces the
    archived engine's recorded lexical eval exactly (hit@5 0.952 / MRR 0.833)
    and orbit reproduces the lab's filed 0.887 (n=53). Re-runs are
    byte-identical; k=∞ ≡ baseline.
  - **The finding that matters is prune coverage.** At k=128 the treatment
    barely touches the population — acme 2.5 % of documents, orbit 1.6 %,
    synth 0 % — because these corpora's documents have a median of 32–46
    distinct terms while the paper's size model assumes ~10⁴-word documents.
    A zero delta over an untreated population is not evidence.
  - At k=64, where pruning does bite, acme loses **9.1 pts** hit@5.
  - **Verdict is therefore not a clean PASS** and is written up for Arpit
    rather than adjudicated — see [P1-GATE](regression/2026-08-09-pruning-eval/VERDICT.md).
    **W-01 (scaffold) stays blocked.**
- **Next:** Arpit rules on P1-GATE (and ratifies ADR-INGEST-MODES's naming).

## 2026-08-09 — M0+M1 handoff & prompt; debate gate re-ordered the plan  ·  Cowork
- **Asked:** create the handoff and prompt (first build package).
- **Did:** `docs/../archive/v0.30-rev1-planning/v0.30.0-m0-m1-gate-handoff.md` + `-prompt.md` +
  handoff README. Handoff covers M0a hygiene, ADR-INGEST-MODES, M1 (the gate), and
  M0b scaffold-on-PASS, with: the KL selector spec (pure/stdlib/portable),
  the harness spec, the **pre-registered** PASS/FAIL table, the failure
  catalogue + rare-term slice requirement, and per-phase model calls.
- **Decided / open:** **the debate gate blocked and amended the plan** —
  original M0(scaffold)→M1 would build a package P1 might falsify; corrected
  to M0a → ADR-INGEST-MODES → M1 → M0b. PLAN.md milestone table + §M0 and OPEN-WORK
  W-01…W-05 updated to the new order (W-01 now blocked_by W-05=PASS).
  Hard spec point recorded: df/n/field-lengths must be recomputed from
  *pruned* postings — reusing baseline stats would measure a system nobody
  ships. Still open: W-00 (Arpit's commit), ADR-INGEST-MODES naming answer, and the
  non-blocking question of whether the three eval corpora weigh equally.
- **Next:** Arpit answers naming (or not — the prompt proceeds either way),
  then run the prompt with Sonnet; verdict phase on Opus.

## 2026-08-09 — decision docs + OPEN-WORK tracker for the v0.30 build  ·  Cowork
- **Asked:** detailed build plan; compare docs (verdict at top) for every
  real fork; proposals for out-of-plan ideas; an OPEN-WORK doc for all
  unbuilt work; big docs get §humans + §agents sections; maintain
  everything (registry, index).
- **Did:**
  - `work/compare/` (fresh): storage-architecture, wire-format,
    keyspace-unification, meta-privacy, cache-policy — all ✅ accepted with
    reopen-triggers — and ingest-mode-naming ⏳ (Arpit ratifies via
    ADR-INGEST-MODES). README with verdict table. v0.26-era proposals moved to
    archive earlier this session.
  - `work/proposals/`: +mcp-adapters, +knowledge-ci, +wavelet-self-index
    (each with graduation trigger); README updated.
  - `work/OPEN-WORK.md`: §1 humans (status, open decisions W-00/0016/
    top-64) + §2 agents (W-00…W-12 ledger with blocked_by/DoD, P1–P7
    status table, standing obligations). Replaces archived IMPLEMENTATION.md.
  - PLAN.md gained a "For AI agents" quick-reference block; index.md and
    DOC-REGISTRY.md rewritten for the new tree (two knowingly-stale ⚠ rows
    — CLAUDE.md, GLOSSARY — tracked as W-03, not hidden).
- **Decided / open:** two-section (§humans/§agents) convention adopted for
  large docs. Open: W-00 (Arpit git-commits the reset), ADR-INGEST-MODES naming,
  top-64-vs-128 (M1 decides).
- **Next:** Arpit reviews + commits; then M0 handoff (Sonnet).

## 2026-08-09 — THE SECOND RESET: v0.26 archived, index-and-refer plan active  ·  Cowork
- **Asked:** write the design paper (v0.2, with figures + estimated numbers);
  then archive the existing code AND the old-system docs, and write a
  from-scratch implementation plan for the new architecture.
- **Did:**
  - **Paper:** `work/paper/the-fux-index-paper.md` + 4 SVG figures — 20
    refs, analytical size/latency models anchored on ADR-FUX-DIR measurements,
    falsifiable predictions P1–P7.
  - **Archive:** `src/ tests/ tests_e2e/ tools/ scripts/ pyproject.toml
    uv.lock CHANGELOG DOGFOOD README` → `archive/v0.26/` (reference-only,
    kept runnable — M1 uses it as the quality baseline). Old docs (ADRs
    0001–0015, compare/, example/, IMPLEMENTATION.md, flow diagram) →
    `archive/v0.26-docs/`; old plan → `archive/v0.26-implemented/PLAN-v0.26.md`.
    Kept live: WORKLOG, INTERVIEW, DOC-REGISTRY, GLOSSARY, proposals/,
    conformance/, handoff/, new SVGs, paper/.
  - **New plan:** `docs/PLAN.md` — M0 scaffold → M1 pruning-eval GATE (P1,
    kill-capable, numbers-as-DoD) → M2 MST keyspace → M3 wire index → M4
    runtime+kernel → M5 refer plane → M6 maintenance → M7 1M scale → M8
    deferred. Port-don't-rewrite list from v0.26 (frontmatter, BM25F, RRF,
    FuxVec, chunker, converters, PPR, eval sets). New root README stub.
- **Decided / open:** version line 0.30.0.dev0. ADR numbering continues
  from 0016 (fresh docs/adr/, TEMPLATE kept). Open at M0: ingest-mode
  naming ADR (Arpit's call); CLAUDE.md sync is M0 scope, not done in this
  exchange — CLAUDE.md still describes v0.26 in places until M0 lands.
- **Next:** M0 handoff + prompt (Sonnet), then the M1 gate.

## 2026-08-09 — council debate + index shrink + one-keyspace + ingest modes  ·  Cowork
- **Asked:** define all components (samples of ledger/postings/dict/codes/CSR/
  meta shown in chat); council-debate the architecture with a visionary seat;
  shrink the 700 MB committed index; can components merge into one; split
  ingest into no-AI vs AI modes. Commit the v2 diagram.
- **Did:** committed `docs/../archive/v0.30-rev1-planning/architecture-components.svg` (v2). Research: BIC
  postings (<1–2 bits/id), RecSplit/PtrHash MPH dict (~2 bits/key), wavelet-
  tree self-index (noted, rejected for decode cost). Council verdicts folded
  into the diagram.
- **Decided / open (chat-level, no ADR yet):** term is "index", not "db".
  Wire/runtime format split → committed ~220–290 MB @1M (top-64 ~160–200 MB);
  repo-source shards need not be committed (re-derived by hooks). All index
  components = ONE MST keyspace (L/P/D/V/E/M prefixes, one root hash, one
  join). Council: hashed meta default (ACL-mismatch leak — DA's strongest
  attack); adapters capped git+HTTP+Confluence, MCP endgame; pruning eval =
  milestone-1 DoD; v0.26 substrate untouched until dogfood; DA minority
  report: ship postings-by-term on current substrate first. Ingest modes:
  inferred (default, $0) + AI tier — naming open ("extracted" collides with
  ADR-0009 edge grades; "enriched" proposed, Arpit's call).
- **Next:** compare doc for the storage architecture, then the pruning-eval
  spike as milestone 1.

## 2026-08-09 — pivot: index-and-refer supersedes the FuxDB paper  ·  Cowork
- **Asked:** Arpit reshaped the design in debate: keyword/phrase db committed;
  content stays in source systems (git dirs, Confluence/SharePoint/Bloomreach);
  answer = rank from db → fetch cited docs live → cache. Then: remove the
  paper, commit the diagram, plan the build with 1M-doc numbers.
- **Did:** paper removed (Arpit deleted the file; index line dropped from
  proposals README). Committed `docs/../archive/v0.30-rev1-planning/architecture-index-and-refer.svg`.
  Researched the build basis: document-centric static index pruning
  (Büttcher–Clarke KL top-k), federated-search broker frame (cooperative,
  single-scorer), ARC cache, YAKE phrases. Build plan + budgets in chat.
- **Decided / open:** direction is index-and-refer (chat-level, no ADR yet);
  per-source policy refer|snapshot; step-1 gate = pruned-vs-full quality eval
  on the 100k synthetic. Open: compare doc before any build.
- **Next:** pruning eval spike (KL top-k into state, measure hit@5/P@10 vs
  full index).

## 2026-08-09 — storage-at-1M research arc → FuxDB design paper  ·  Cowork
- **Asked:** re-imagine storage for 1M docs × ~1k lines (research-driven); then:
  git-clone concern, dependency question, "new kind of database?", merge
  conflicts, freshness compromise (hooks + stale-ok + live check on final
  answer), better existing DB/graph?, papers?, finally: write the paper.
- **Did:** researched segments/PEF/BMW, prolly trees/Dolt, CRDTs/MST, ForkBase,
  TerminusDB, SWR/read-repair/DBSP, embedded-graph landscape (Kùzu archived —
  supply-chain lesson). Wrote **`work/proposals/fuxdb-paper.md`** (draft v0.1,
  19 refs, ADR-FUX-DIR numbers as baseline) + indexed it in proposals README.
- **Decided / open:** chat-level direction only, nothing accepted as ADR: merge
  = join ∘ rebuild; freshness as read-time contract (bends the network fence —
  needs explicit opt-in design); deps rejected (B "never"); FuxDB = MST ledger
  + immutable segments. Open: compare doc + spike before any build.
- **Next:** Arpit reviews the paper; if direction holds → storage-at-scale
  compare doc, then a narrow MST-ledger spike measured on the 100k synthetic.

## 2026-08-08 — design-rationale Q&A; response-style rule folded into CLAUDE.md  ·  Cowork
- **Asked:** why ingest copies docs instead of index-only; why a DB not a graph;
  can the db/graph live in git. Then: answers too long-winded — be precise, and
  bind that in CLAUDE.md. Follow-ups: millions-of-files concern (→ bulk tier,
  no file cache) and fresh-clone behaviour (→ local sources rebuild offline;
  bulk web warehouse must be re-crawled — not in git by design); why curated
  files aren't db rows (→ git review + agent/OKF readability); fux.db at 1M
  docs × 1000 lines (→ ~250–450 GB full profile extrapolated from ADR-FUX-DIR's
  10.8 KB/doc; lean ≈ 230 MB state — the designed answer at that scale).
- **Did:** answered from P1-GATE/0008/0009 + ingest-strategy compare (no code
  changed). Extended CLAUDE.md § Documentation style: chat responses follow the
  same short-paragraph, lead-with-takeaway rule.
- **Decided / open:** still open from the compare doc: whether `.fux/cache/` is
  ever committed (needs an ADR to flip).
- **Next:** none — docs-only exchange.

## 2026-07-24 — phase 9 executed: fusion finding was a misdiagnosis → ACCEPT  ·  Claude Code
- **Asked:** run handoff 0009 (the non-monotone fusion finding).
- **Did:**
  - **M0** — reproduced the arithmetic before trusting the pre-work: **160/160
    fused results reconcile to `Σ 1/(k + rank)` with zero delta**, including the
    penalised superseded doc. RRF *is* monotone; the filed finding is a
    misdiagnosis. (My checker first flagged 1/160 — it had omitted the penalty
    term, not the engine.)
  - **M1** — corrected "non-monotone" in place (marked) across the orbit
    ANALYSIS, the release-verification ANALYSIS, the conformance index, and the
    lab harness's check label.
  - **M2** — measured the real population across all four eval sets. Hybrid loses
    a lexical top-5 hit **~4% on realistic corpora** (acme 2/55, orbit 2/53),
    roughly offset by gains; four kinds affected, worst an orbit `factual`
    question lost from **lexical rank 1**. Synthetic 9–64%, **unexplained** (a
    near-duplicate/compressed-spread hypothesis was tested and rejected).
    **Supersession penalty not implicated** — identical at penalty 0 and 15.
  - **M3** — compare doc `hybrid-losing-lexical-hits`, three-way fork.
  - **M4** — Arpit **accepted ACCEPT** (no fusion change). Generalised the lab
    demotion check from zero-overlap-only to **all kinds** (INFO, gains beside
    losses); filed `proposals/chunk-level-dense-codes` as the finding's owner.
    No ADR (no engine change), no version bump.
  - **M5** — trackers, archives (belatedly archived the v0.26.0 release pair 0008
    too; phase-9 pair archived unversioned, as it shipped no release).
- **Decided / open:** the guard question is **closed as ACCEPT**, with a
  reopen-trigger (LOST exceeding gained by ≥3 on a realistic corpus, or the loss
  persisting after chunk-level dense codes ship). The `factual`-lost-from-rank-1
  case is the named case any future reopen is judged against.
- **Lesson kept:** a reconciliation script that models fewer terms than the
  engine manufactures the bug it was written to disprove. Model every term.
- **Next:** **chunk-level dense codes** — now the named owner of both the
  zero-overlap reach failure (1/6) and this ranking failure. Its own phase, own
  compare doc, gated on the ~200 B/doc committed-state budget.

## 2026-07-24 — phase 9 packaged: the "non-monotone fusion" finding is a misdiagnosis  ·  Claude Code
- **Asked:** write the Part C handoff for the non-monotone fusion finding.
- **Did:** diagnosed it first, and the filed framing does not survive contact.
  - **RRF *is* monotone in per-list rank** — `1/(k + rank)` is strictly
    decreasing. The filed claim conflates "monotone in per-list rank" (true) with
    "rank-preserving w.r.t. one input list" (false, and inherent to fusion).
  - **The reported case reconciles to the exact specified arithmetic**, to five
    decimals, across all three lists (`bm25f`, `dense`, `dense_global`). Two-list
    sums do not reconcile — `dense_global` is easy to forget.
  - **The real defect is dense quality:** the correct doc's similarity is
    **0.3297**, barely above ADR 0010's 0.23–0.26 noise band (dense_rank 56,
    dense_global_rank 117). Two of three lists voted against it. The doc that
    beat it had *worse* lexical (13 vs 5) and much better dense (0.4895).
  - **The supersession penalty is not implicated** — the doc is not superseded,
    and the finding predates v0.26.0.
  - Wrote handoff+prompt `0009-fusion-loses-lexical-hits` (**Opus** — the code is
    easy, the deliverable is a judgment about a guarantee), pre-registered the
    milestone table, updated PLAN.
- **Decided / open:** the phase is no longer a bug hunt. The open question is a
  product one — **should hybrid be barred from dropping a document
  `--lexical-only` would have returned in top-5?** Guard vs accept vs
  fix-the-input, headed for a compare doc. **"No engine change" is an expected,
  valid outcome**; this may be the zero-overlap/dense-quality finding seen from
  the fusion side. Named risk: manufacturing a fix because a phase was opened.
- **Next:** run 0009 in Claude Code with Opus; it reproduces the arithmetic
  itself first, then measures how big the population actually is (n=1 today).

## 2026-07-24 — v0.26.0 PUBLISHED to PyPI + Part B closed  ·  Claude Code
- **Asked:** execute handoff 0008 — apply the pending honesty edits, land phase 7
  by PR, publish, verify, close the follow-ups. Publish human-gated at M5.
- **Did:**
  - **M1** — both README honesty edits + the CLAUDE.md fold applied, *before* the
    release was cut. Verified the 0.26.0 CHANGELOG entry and its README mirror.
  - **M2/M3** — phase 7 moved off `main` onto `feat/phase7-supersession-downrank`
    (commit `2455469`), PR **#44**, **11/11 CI checks green**, merged `5ccd0a6`.
    470 unit + 100 e2e green locally too.
  - **M4** — **§10 Q1 is moot: 0.24.0 and 0.25.0 were already on PyPI.** Nothing
    to back-publish; only 0.26.0 was missing.
  - **M5** — Arpit gave the go. Tagged `v0.26.0`, cut the Release; tag↔version
    guard + `twine --strict` + OIDC all passed. **Live on PyPI.**
  - **M6** — clean-venv `pip install fux-engine==0.26.0`; setup→ingest→
    find/ask/why all work; the penalty is active in the published build; the
    **PyPI page renders both corrected claims** and neither old one.
  - **M7** — trackers updated; orbit now installs from PyPI (frozen-wheel
    workaround retired in TEST-PLAN + the orbit ANALYSIS).
  - **M8** — `zero_overlap_rescued` fixed to count *clean* rescues only (2 → 1);
    added `zero_overlap_in_top5` and `zero_overlap_demoted`. Orbit re-baselined
    deliberately; run filed as a conformance record.
- **Decided / open:**
  - **Two corrections worth keeping.** (1) *"0.25.0 is not on PyPI"* was wrong —
    `pip install` fails with "no matching distribution" on Python **<3.11**
    because of `requires-python`, and that was misread as unpublished. (2) *A
    version string is not a build identity* — the first orbit re-baseline used a
    `0.26.0` wheel built before the M5 default flip and would have pinned
    pre-release behaviour; caught by reading the baseline diff.
  - **One deviation from the approved wording, flagged in PR #44:** approved Edit
    2 listed the third refuted discriminator as "empty-pool". Empty-pool was never
    refuted — it correctly declines gibberish. Shipped **"margin ratio"**, matching
    ADR 0015 and the compare doc. Revert if Arpit disagrees.
  - **Independent confirmation:** orbit re-baselined on the *published* package
    reproduces phase 7 exactly — inversions **8 → 3**, hit@1 **.566 → .698**,
    hit@5 flat. The calibration holds black-box, not just in-tree.
- **Next:** **Part C** — the non-monotone fusion finding, now auto-detected by the
  suite (`zero_overlap_demoted` = 1). Needs its own Opus handoff + ADR; fusion was
  deliberately untouched during the release.

## 2026-07-24 — phase 7 reviewed → release handoff (0008) packaged  ·  Cowork
- **Asked:** one handoff+prompt for all pending items — first commit/push/publish
  everything built, then the next steps.
- **Did:** wrote handoff+prompt `0008-release-and-followups` (→ **Sonnet**, publish
  human-gated). Grounded it in the real state: phase 7 is **staged uncommitted on
  main**, `__version__` already 0.26.0, tags through v0.25.0, publish is
  release-triggered (tag↔version guard + twine --strict + OIDC), and ~nothing since
  0.23.0 is on PyPI. Sequenced so the two approved README honesty edits + the
  CLAUDE.md fold land **before** the release is cut (PyPI must not render the old
  "cannot hallucinate" claim). Part B = fix the `zero_overlap_rescued` suite
  miscount. Part C (scoped, not executed) = the non-monotone fusion finding (Opus,
  own handoff) + chunk-level dense codes.
- **Decided / open:** Q1 — publish 0.26.0 only (recommended; supersedes 0.24/0.25,
  carries corrected README) vs back-publish older versions. Q2 — the go/no-go on
  the irreversible release (human-gated at M5).
- **Next:** run 0008 in Claude Code; it pauses at M5 for Arpit's publish go.

## 2026-07-24 — phase 7 built: supersession down-rank shipped enabled (v0.26.0)  ·  Claude Code
- **Asked:** execute handoff 0007 — the default-off down-rank penalty, calibrate
  it across four eval sets, re-measure the runner-up margin, gated on M1
  (Arpit reopening Option B) and M5 (his sign-off before enabling).
- **Did:**
  - **M1** — Arpit reopened B. Amended the supersession compare-doc verdict
    (A stands; B authorised default-off), updated INTERVIEW + IMPLEMENTATION.
  - **M2** — `[engine.hybrid] supersession_penalty` as a **rank offset** in RRF
    (`1/(k+rank+N)`), applied to the deterministic frontmatter-marked set only.
    Lean honours it too (parity law). Landed at `0` with every golden unchanged.
  - **M3** — swept fixture/acme/orbit/synthetic 1k/5k/10k. **Safe interval
    `[11, ∞)`** to 500; zero hit@5 regression on any gate, any value, any kind;
    hit@1 improves (orbit .566→.698, acme .491→.564). **100% of
    frontmatter-reachable inversions recovered** (orbit 5/5, acme 3/3) — every
    residual one is unmarked. Harness validated against orbit's published
    numbers before sweeping.
  - **M4** — re-measured the margin de-confounded. **Still empty.** The confound
    was real (orbit's minimal `factual` question improved) but not the cause: a
    `how-to` question sits at 1e-05 before *and* after; acme is identical, its
    minimum a `cross-doc` question — the legitimate-consensus mode the compare
    doc predicted years of reasoning ago.
  - **M5** — surfaced both readings of the "majority" gate (all inversions:
    orbit 62% ✅ / acme 33% ❌; reachable: 100% both). **Arpit chose enable at 15.**
  - **M6** — ADR 0015, both compare docs closed out, conformance run filed,
    README/CHANGELOG/PLAN/GLOSSARY/TOML/registry updated, handoff+prompt archived
    as `v0.26.0-*`, version bumped. 470 unit + 100 e2e green.
- **Decided / open:**
  - **Fabrication is now a documented product boundary**, not an open defect —
    three no-model discriminators refuted across two corpora, one de-confounded.
    The decline-floor reopen-trigger is **retired**; no fourth mechanism proposed.
  - **Two README honesty-claim edits are PROPOSED, not applied** (positioning is
    Arpit's call): the "never generative, so it cannot hallucinate" line and the
    "measured, unfixed limit" phrasing in § Honest limits, both of which M4
    turned from provisional into permanent.
  - **Open (Arpit, unchanged):** release to PyPI — 0.25.0 was never published and
    0.26.0 now sits on top of it.
- **Next:** Arpit rules on the two README wording proposals; then open the
  v0.26.0 PR and read `gh pr checks` before merging (no required checks on main).

## 2026-07-24 — orbit run reviewed → phase 7 packaged (down-rank)  ·  Cowork
- **Asked:** review the second-corpus (orbit-fulfillment) output; what next.
- **Did:** synthesized the generalization verdict — all three acme findings
  reproduce on an independent domain (staleness 8/12 meeting the ≥8/12 gate;
  fabrication 0/4 with **both** no-model mechanisms refuted; zero-overlap 1/6).
  Surfaced the key coupling: the margin refutation is **confounded** — smallest
  "answerable" margins come from superseded-twin ties, so Finding 1's fix is the
  prerequisite to a fair Finding 2 verdict. Wrote handoff+prompt
  `0007-supersession-downrank` (→ v0.26.0, **Opus**): default-off penalty knob,
  four-eval-set calibration, and the margin re-measurement it unblocks.
  Pre-registered phase 7 in IMPLEMENTATION.md; filed the two orbit engine/suite
  findings (non-monotone fusion; zero_overlap_rescued miscount).
- **Decided / open:** the anti-B argument weakened — the penalised set is
  deterministic (author frontmatter, 6/6 surfaced), only the magnitude is tuned.
  **M1 gate:** Arpit must reopen Option B before Claude Code starts.
  Parallel Arpit calls: release v0.25.0 to PyPI (committed af374f0, unpublished);
  reframe the "never fabricate" claim if M4 confirms the no-model boundary.
- **Next:** Arpit reopens B (or not); phase 7 executes in Claude Code.

## 2026-07-24 — second realistic corpus (orbit-fulfillment): all three findings generalize  ·  Claude Code

- **Asked:** build a second realistic ~1k-doc corpus in a domain far from fintech and
  determine whether the three acme findings generalize; measure the deferred
  runner-up **margin check** directly.
- **Did:**
  - New generator `fux-lab/shared/generate/make_orbit.py` (warehouse/order-fulfillment,
    944 files, 50 hand-written hero docs, 57 typed eval pairs, deterministic). Marker
    split **known by construction**: 6/12 superseded docs carry `superseded_by:`.
    Unanswerable vocabulary verified absent (0 files for crypto/drone/graphql/cafeteria).
  - New measurement tooling: `shared/regress/margin.py` (top vs runner-up separability)
    and `shared/regress/floor_sweep.py` (empirical `min_confidence` curve over the full
    eval set).
  - Filed `work/regression/2026-07-24-orbit-fulfillment/` (report + ANALYSIS + 10
    evidence files); updated `conformance/README.md`, both reopen-triggered compare docs,
    DOC-REGISTRY; updated `fux-lab/TEST-PLAN.md` §1/§7.
- **Decided / open:**
  - **Staleness generalizes: 8/12 inversions — the Option-B ≥8/12 gate is MET.** 6/6
    frontmatter-reachable superseded docs carry the v0.25.0 annotation and **5 of 6
    still outrank their replacement**. Mechanism: current doc wins BM25F outright in 6/8
    cases and loses on a dense edge as thin as 0.0006 cosine, which RRF flips.
    **The gate's second clause (a tunable penalty) is NOT tested — B stays deferred.**
  - **Fabrication generalizes: 0/4.** Absolute floor **empty** (needs ≥0.121, false-declines
    start at 0.105) and the **margin check is refuted — empty AND inverted** (unanswerable
    margins exceed the smallest answerable ones; the smallest answerable margins come from
    stale/current ties, so Finding 1 manufactures Finding 2's false-positive mode).
    Recorded as a **documented product boundary**, not an open defect.
  - **Zero-overlap generalizes: 1/6 clean dense rescues**; hybrid also *demoted* a lexical
    rank-5 hit out of top-5 (fusion is not monotone).
  - **v0.25.0 features confirmed on independent data:** annotation surfaces 6/6; the
    permissive `min_confidence` default re-confirmed as the only zero-false-decline value.
  - **Caveat, flagged prominently:** `fux-engine==0.25.0` **is not on PyPI** (merged as
    `af374f0`, never released), so the run used a locally-built wheel driven strictly as a
    black box. Numbers describe that commit, not a published artifact.
- **Next:** run the **penalty-tuning experiment** for supersession down-ranking, gated
  jointly on the fixture gate, acme, orbit and the synthetic tiers, graduating via an ADR.

---

## 2026-07-23 — phase 6 built end-to-end, v0.25.0 shipped  ·  Claude Code
- **Asked:** execute the `0006-trust-currency-prompt.md` paste-ready prompt
  (supersession awareness + `answer` confidence floor).
- **Did:** confirmed M1's gate directly with Arpit (both compare docs were
  still `status: proposed` on disk despite an earlier Cowork worklog entry
  assuming acceptance) — accepted Option A on both, plus the `fux-query` skill
  update, via explicit questions. Built M2–M5 incrementally, both suites green
  at every milestone: supersession parsing/persistence/resolution
  (`index.build_index::_supersession_meta`/`_resolve_supersession`,
  `state.DocState.superseded_by`, sqlite `format_version` 2→3), `find`/`ask`
  annotation (ordering + all 4 lexical goldens unchanged), `[answer]
  min_confidence` mechanism, `answer.prefer_current`/`best_confidence` shared
  with `why`'s new decline explanation. Delegated the two judgment-heavy
  real-corpus measurements to a background Opus subagent, resumed once to
  reuse its editable-install acme environment rather than rebuild it: (1)
  confidence-floor calibration against all 5 gates — **no value clears both
  the unanswerable and answerable gates; shipped `min_confidence = 0.0`**; (2)
  supersession recovery re-measurement — **5/12 markers, 3/9 inversions
  marked, 1 fully corrected + 1 de-cited at the `answer` level, 6
  unmarked/unreachable**. Wrote ADR 0013 + 0014, filed both conformance runs,
  graduated both source proposals to `archive/`, archived the
  handoff+prompt as `v0.25.0-trust-currency-*`, updated CHANGELOG/README
  (What's new + Status + Honest limits)/PLAN §7-8/INTERVIEW/GLOSSARY/
  DOC-REGISTRY, bumped version 0.24.0→0.25.0. 444 unit + 100 e2e green
  throughout.
- **Decided / open:** both the supersession recovery and the confidence-floor
  fix are honestly **partial** — recorded plainly in every doc touched, not
  papered over. The CLAUDE.md edit (version line + phase-6 hard-won-knowledge
  section) was proposed for review per the handoff's explicit instruction, and
  Arpit approved it in-session — applied. No phase 7 is pre-registered.
- **Next:** phase 6 is fully closed. Candidates for phase 7 (not yet scoped):
  an absolute cross-query confidence signal for `answer` (ADR 0014 F1/F2), or
  Finding 2's deferred chunk-level dense codes (zero-overlap rescue).

## 2026-07-23 — phase 6 packaged + architecture diagram  ·  Cowork
- **Asked:** review the acme run in plain language; then plan/handoff/prompt the
  fixes; then a flow diagram of how Fux works, linked into the README.
- **Did:** wrote two compare docs (`supersession-handling`, `answer-decline-floor`)
  — both **accepted** by Arpit (annotate-not-down-rank; absolute floor, no margin).
  Wrote handoff+prompt `0006-trust-currency` (→ v0.25.0, **Model: Opus**),
  pre-registered phase-6 rows in IMPLEMENTATION.md, updated PLAN §7/§7a/§8.
  Added `docs/architecture-flow.mermaid` (validated: parses clean via mermaid+jsdom)
  and embedded it as a fenced `mermaid` block in README § How it works (renders on
  GitHub; ASCII sketch kept in a `<details>`). Bumped DOC-REGISTRY.
- **Decided / open:** M1 gate cleared. Skill-update open question → **yes**, update
  `fux-query` skill to read the `superseded` field (descriptive, not prescriptive).
  M4 calibration may legitimately return "no value satisfies all five gates."
- **Next:** phase 6 is executing in Claude Code (M2 in progress — parse+persist,
  with the `superseded` flag required in `.fux/state/`, not just the gitignored index).

## 2026-07-22 — acme-payments realistic run settles A vs B → B  ·  Cowork
- **Asked:** build a ~1 000-doc corpus with genuine prose diversity and run the
  conformance suite to settle whether the hybrid degradation is an engine defect
  (A) or a synthetic-corpus artifact (B). New environment inside fux-lab; pin 0.23.0.
- **Did:** authored `fux-lab/shared/generate/make_repo.py` (deterministic, stdlib,
  bespoke ADRs/runbooks/postmortems/RFCs/guides/API refs + 59 typed eval pairs +
  12 stale-vs-current pairs w/ 3 marker styles + 6 zero-overlap + 4 unanswerable);
  scaffolded `fux-lab/acme/` (VERSION 0.23.0); extended `shared/regress/run.py`
  with **additive, data-guarded** staleness-precision + typed-unanswerable-decline
  checks (no-op on synthetic tiers). Filed
  `work/regression/2026-07-22-acme-payments/` (report + ANALYSIS + evidence),
  indexed it, updated the proposal to **resolved**, split two new proposals,
  corrected the README/CHANGELOG "same rankings *and scores*" wording.
- **Decided / open:** **B — the 4× hybrid collapse is a corpus artifact.** On
  realistic prose hybrid hit@5 recovers .182→.855 (parity with lexical .873). The
  RRF reopen-trigger is answered: no fusion/reranker change warranted. **Three new
  real findings** the fixture gate missed: staleness 9/12 inversions (superseded
  doc outranks current), zero-overlap dense rescue 0/6 clean (even undiluted),
  honest-decline 0/4 on well-formed unanswerables (fabricates with sources).
  why/how-to/factual hit@5 = 1.00. Scorer matcher hand-verified before trusting
  numbers. No engine behaviour change shipped (one corpus = evidence, not proof).
- **Next:** graduate `staleness-ranking-ignores-supersession` (ingest-time
  supersession flag) and `honest-decline-well-formed-queries` (absolute-confidence
  floor) via compare docs + ADRs, each confirmed on a second realistic corpus.

## 2026-07-22 — conformance evidence gets a durable home (work/regression/)  ·  Cowork
- **Asked:** capture every test run's report + evidence into the fux repo in a
  dedicated place for analysis and improvement, and put the practice in CLAUDE.md
  so it is never missed.
- **Did:** created `work/regression/` with a README (the convention) and this
  run's folder `2026-07-22-scaling-1k-5k-10k/` (report.md, 5k.md, 10k.md,
  ANALYSIS.md, evidence/). ANALYSIS.md turns the numbers into two **measured**
  failure mechanisms + ranked fux improvements. Added a binding CLAUDE.md section
  "Conformance runs — file every one", a Layout entry, and a DOC-REGISTRY row.
- **Decided / open:** diagnosis (via 0.24.0 `fux why`/`--debug=trace`, retrieval
  byte-identical to 0.23.0): (1) zero-overlap miss = doc-vector dilution — correct
  doc at dense cosine 0.17-0.27, hamming ~110-126/256, outside the 500-prefilter
  → chunk-level dense codes is the structural fix; (2) hybrid demotion = RRF has
  no dense-quality floor — lexical rank 3/5 pushed to fused rank 6/10 because
  `dense_global_rescues=200` injects a near-random full list over near-identical
  prose. fux's trace is strong but mislabels fused lines `[lexical]` and omits
  per-doc source ranks — top observability win is a fusion trace. Ranking changes
  (admission threshold, confidence-weighted RRF, size-aware default) stay proposal
  candidates gated on the acme-payments run.
- **Next:** wire the capture into `fux-lab/shared/regress/run.py` (archive `fux why`
  + trace + doctor per run automatically); then run acme-payments (A-vs-B discriminator).

## 2026-07-22 — conformance scaling curve: 5k + 10k tiers run  ·  Cowork
- **Asked:** run the fux-lab conformance suite at 5k and 10k, compare against the
  1k baseline, produce a scaling curve, and file it per CLAUDE.md.
- **Did:** ran 5k and 10k (fux-engine 0.23.0, `--accept-baseline`) plus a
  same-machine 1k timing anchor. All in the cloud sandbox — the device VM has no
  network and Python 3.10 (< 3.11), so the pinned engine cannot install there;
  byte-budget and quality metrics are deterministic (a cloud 1k re-run was
  byte-identical to the Mac baseline), only wall-clock differs by machine. Wrote
  `fux-lab/{5k,10k}/results` + `baselines` and
  `fux-lab/results/2026-07-22-scaling-1k-5k-10k.md`; updated
  `work/proposals/hybrid-degrades-at-scale.md`, `work/DOC-REGISTRY.md`, `work/INTERVIEW.md`.
- **Decided / open:** the 1k "hybrid 4x worse" gap is NOT stable — it CLOSES with
  scale (hit@5 lexical/hybrid 4.49x -> 2.00x -> 1.54x) because lexical collapses
  toward hybrid (.818 -> .385 -> .192) while hybrid stays flat (~.13-.19). Leans
  reading B (corpus artifact) but does NOT settle A vs B — same generator.
  Zero-overlap rescue 0 at every tier, now well-powered (0/14 at 10k) -> narrows
  ADR 0010's rescue claim. Per-doc budgets flat/declining (no superlinear term).
  Query latency linear from the start (~0.20s + 0.16s per 1k docs), no flat
  regime -> corroborates ADR 0011. Fresh-clone tail-score divergence reproduces at
  all scales (README/CHANGELOG "same rankings and scores" still inaccurate). Only
  FAIL is the known zero-overlap rescue. No engine change made — mitigations stay
  candidates until the A-vs-B experiment resolves.
- **Next:** run the acme-payments realistic corpus
  (`fux-lab/prompts/build-realistic-repo.md`) — the discriminator for A vs B.

## 2026-07-22 — phase 5 built: debug & observability (v0.24.0) · Claude Code
- **Asked:** execute handoff 0005 exactly — `[debug]` in fux.toml, a stdout-pure
  emitter, `fux doctor`, `fux why`, the `fux-debug` skill, M1→M6 with the
  stdout-purity gate written before any instrumentation existed.
- **Did:** all six milestones, green throughout, IMPLEMENTATION.md updated per
  milestone (never batched):
  - **M1** `DebugParams`/`_parse_debug` in `config.py` (wired via
    `debug.apply_config()` inside `load()` — one config-load call site, not one
    per command); `src/fux/debug.py` (`dbg()`/`timer()`/`is_enabled()`,
    flag>env>toml>off precedence, redaction, max_bytes truncation, unwritable-
    output fallback); `--debug[=LEVEL]` global CLI flag; `tests/conftest.py`
    (autouse debug-state reset — needed once `load()` had a global side effect);
    e2e stdout-purity + stderr-reproducibility tests.
  - **M2** `dbg()`/`timer()` at walk/convert/chunk/index/lock/state/graph
    (ingest side) and query/lexical/dense/graph/answer/hooks/web (query side);
    trace-level content previews gated on `redact=false`; caught and fixed a
    latent flaky-test risk (ingest's own `Elapsed: N.Ns` stdout line is
    wall-clock, unrelated to debug — normalized in the test, not the product).
  - **M3** `src/fux/doctor.py` — 7 groups, `--json`, exit 0/1; zero-match
    `[sources]` globs surfaced loudly; self-test ingests a canary doc in a
    scratch temp dir and proves ingest→index→query→citation end to end.
  - **M4** `src/fux/query/why.py` — corpus-presence → chunks → lexical → dense →
    graph → one verdict sentence; dense/graph evidence read from
    `kernel.retrieve()` itself so `why` can't disagree with a real query.
  - **M5** `fux-debug` skill in `agents/generate.py::_SKILLS`; one-line
    escalation pointer added to `fux-query`/`fux-ingest`; `fux setup --skills`
    now writes 3 skills.
  - **M6** `docs/example/DEBUG.md` new (7 worked failures); CLI/TOML/SETUP/
    SKILLS/GLOSSARY/DOC-REGISTRY/PLAN/INTERVIEW updated.
  - **Close-out:** ADR 0012 (answered all 4 open questions); CHANGELOG entry +
    README mirror + command list; archived the handoff+prompt pair as
    `archive/v0.24.0-debug-observability-*.md` (status: implemented, ADR
    linked); bumped `__version__` → 0.24.0. Suites: **417 unit + 100 e2e**
    (+1 gated skip).
- **Decided / open:** `fux doctor`'s "Chrome for CDP" check is binary-presence
  only (`shutil.which`), not a live port probe — `import socket` outside
  `ingest/` trips the standing `test_import_fence.py` rule, and keeping that
  fence mattered more than one check's completeness (recorded in ADR 0012 and
  IMPLEMENTATION.md's Deviations). `why --all` deliberately not built (single-
  doc only, cost-scoped) — open for a future proposal if a real need appears.
- **Next:** none pending for phase 5. Next phase's head is still query-at-scale
  (ADR 0011) — the 100k-corpus ~10s query latency, unfixed.

---

## 2026-07-22 — release v0.23.1 (docs & examples) · Claude Code
- **Asked:** commit, push, and publish.
- **Did:** on main → branched `release/v0.23.1-docs-examples`. Confirmed all
  changes since 0.23.0 are docs/comments/test-path only (no engine change), so
  Arpit chose a **0.23.1 patch**. Bumped `__init__` → 0.23.1, added the CHANGELOG
  entry, mirrored it into README § What's new, updated CLAUDE.md identity + the
  smoke-test version assertions. Pre-flight green: **365 unit tests**, `python -m
  build`, `twine check --strict` both artifacts PASSED as 0.23.1. Committed the
  full working tree (this session's doc reorg + example bundle, plus pre-existing
  README/CHANGELOG work and the untracked `handoff/0005` debug-observability
  planning pair). Pushed → PR → merge → `gh release v0.23.1` → PyPI publish.
- **Decided / open:** patch, not minor — the wheel is functionally identical to
  0.23.0; the example bundle is docs, not a shipped feature. `handoff/0005` rode
  along in the same commit (it was already in the tree, registry-referenced).
- **Next:** none for this release; 0005 (debug & observability) is the next build.

---

## 2026-07-22 — three new example docs: SETUP / SKILLS / API · Claude Code
- **Asked:** add examples for (1) CLI setup variants + hooks installation,
  (2) skill usage, (3) the Python API creating a file in fux from another script.
- **Did:** created `docs/example/{SETUP,SKILLS,API}.md` (ALL-CAPS, no
  frontmatter). **Every block is verified against the real v0.23.x
  implementation**, not invented — ran `fux setup -y --agents --skills --hooks`
  on a scratch dir (captured the exact 8-file output + idempotent re-run),
  dumped the real `.claude/settings.json` and `.kiro/*.hook`, exercised
  `fux hook prompt-submit/session-end` I/O, and wrote+ran a real
  `find_root → load → ingest_paths → load_searcher.search` script (create file →
  `new=2…`, re-run → `unchanged`, `ingest --check` → `sha mismatch — re-ingest`).
  Corrected the `fux ask --json` shape in SKILLS.md after checking live output
  (`path`/`line_start`/`line_end`/`heading_path`/`fidelity`/`hybrid`, structured
  `corpus`, `engine`). Wired all five into `example/index.md`, `docs/index.md`
  (bundle line + OKF exemption), DOC-REGISTRY (3 rows), CLAUDE.md layout.
- **Decided / open:** grounded the API doc on the CLI's own entrypoints
  (`fux.config`/`fux.ingest`/`fux.index`) — no private path — so the example
  can't drift from the shipped CLI. Nothing open.
- **Next:** none — `example/` now has CLI, TOML, SETUP, SKILLS, API.

---

## 2026-07-22 — correction: fux-toml.md *is* the example → example/TOML.md · Claude Code
- **Asked:** the separate `example/fux.toml` I created was wrong — `fux-toml.md`
  itself is the example and should have been the thing moved into `example/`.
- **Did:** `rm docs/example/fux.toml`; `git mv docs/fux-toml.md
  docs/example/TOML.md` (name confirmed with Arpit — matches the ALL-CAPS
  example-dir convention set by CLI.md); stripped its frontmatter; fixed its
  now-deeper relative links (CLI.md became same-dir). **Updated the real code
  dependency:** `tests/test_config.py` reads this doc to assert the fenced
  example against the shipped dataclass defaults — repointed both paths to
  `docs/example/TOML.md` (16 config tests green). Merged the two DOC-REGISTRY
  rows into one; updated index.md (bundle line + OKF exemption list), CLAUDE.md
  layout, `example/index.md`, and `proposals/knowledge-substrate.md`.
- **Decided / open:** `example/` now holds exactly two maintained contracts —
  `CLI.md` (command I/O) and `TOML.md` (annotated config). There is no separate
  runnable `fux.toml` sample; the fenced block inside TOML.md is the copy source
  and the parser-asserted one. Nothing open.
- **Next:** none.

---

## 2026-07-22 — ALL-CAPS core docs + examples bundle · Claude Code
- **Asked:** `worklog.md`→`WORKLOG.md`; `fux-plan.md`→`PLAN.md`;
  `model-handoff-interview.md`→`INTERVIEW.md`; move `cli-examples.md` to a new
  `docs/example/` dir as `CLI.md`; add an example `fux.toml` there too.
- **Did:** `git mv` all four; **stripped YAML frontmatter** from WORKLOG/PLAN/
  INTERVIEW/CLI per the ALL-CAPS = no-frontmatter convention (they join
  IMPLEMENTATION/GLOSSARY/DOC-REGISTRY). Fixed CLI.md's six internal relative
  links for the extra dir depth. Created `docs/example/fux.toml` (complete
  copy-paste config, v0.23.x keys from `config.py`) + `docs/example/index.md`
  (OKF per-dir index). Rewired **every** live reference — README, CLAUDE.md
  (prose + layout block + convention list + log.md line), index.md, GLOSSARY,
  DOC-REGISTRY (+2 new rows), INTERVIEW, `adr/0002`, `adr/0011`,
  `compare/cli-surface`, `fux-toml.md`, `proposals/*`, and the doc-pointer
  comments in `src/fux/query/{statequery,verbs,api}.py` + two tests. Verified
  all relative `.md` links across docs/README/CLAUDE/DOGFOOD resolve.
- **Decided / open:** ALL-CAPS files carry **no** frontmatter (documented rule) —
  so promoting these four to ALL-CAPS dropped their OKF `type`; the convention
  explicitly exempts entry-point/tracker files, and index.md's OKF note was
  updated to say so. `fux-toml.md` stays the annotated *reference* (prose per
  key); `example/fux.toml` is the runnable example — both maintained. Archive
  prose naming old paths left as historical record; broken links I introduced
  (WORKLOG hist + one archived handoff) repointed to resolve. Nothing open.
- **Next:** none — new handoffs still use `NNNN-name.md` in flight.

---

## 2026-07-22 — archive docs renamed to release-version keys · Claude Code
- **Asked:** archive documents should be named by release version, not the
  in-flight `NNNN` index.
- **Did:** `git mv` all 8 archived handoff/prompt pairs to `vX.Y.Z-name.md`
  (0001→v0.20.0, 0002→v0.21.0, 0003→v0.22.0, 0004→v0.23.0); master-prompt kept
  unversioned (spans v0.20–v0.22, per Arpit). Rewired every live-doc link
  (`fux-plan.md` table + §7/§8, `adr/0008`, `proposals/knowledge-substrate.md`)
  and the `blocked_by:` frontmatter inside the archived docs. Folded the naming
  rule into CLAUDE.md (Archive section), refreshed `archive/README.md` with a
  shipped-artifacts index, bumped DOC-REGISTRY rows (CLAUDE/fux-plan/handoff/
  archive). Verified all `archive/*.md` markdown links resolve via a script.
- **Decided / open:** left historical prose that names `archive/handoff/000X-…`
  (worklog entries, archived-doc body instructions, IMPLEMENTATION.md:110's
  measured doc id) untouched — those record the paths that existed at build time;
  rewriting them would falsify the record. Nothing open.
- **Next:** none — future handoffs use `NNNN-name.md` while in flight, archive as
  `vX.Y.Z-name.md` on ship.

---

## 2026-07-22 — rename tracker to IMPLEMENTATION.md (git case fix) · Claude Code
- **Asked:** convert implementation.md to IMPLEMENTATION.md and update wherever
  necessary.
- **Did:** the file on disk was already `IMPLEMENTATION.md` but git still tracked
  it lowercase (case-preserving macOS FS) — `git mv -f docs/implementation.md
  docs/IMPLEMENTATION.md` so git agrees. Fixed the one stale live prose reference
  (`model-handoff-interview.md` §200k benchmark). Verified the maintained docs
  already used the uppercase name: CLAUDE.md, `docs/index.md`, `DOC-REGISTRY.md`.
- **Decided / open:** left lowercase refs in `archive/`, `archive/`, ADR
  0002, and prior worklog entries — those are immutable/historical records, not
  live docs. Nothing open.
- **Next:** none — casing is now consistent across the live doc set.

---

## 2026-07-22 — v0.23.0 merged to main and published to PyPI · Claude Code
- **Asked:** merge everything to main and publish.
- **Did:** pre-flight (wheel builds 7.04 MB, model bundled, `twine check --strict`
  passes, clean-install smoke test) → pushed `feat/phase4-knowledge-substrate` →
  **PR #38** → full matrix green (linux 3.11–3.14, macOS 3.11/3.14, **Windows
  3.11/3.14**) plus both required checks (`fux gate`, `ai-review`) → merged →
  release **v0.23.0** → publish workflow uploaded both artifacts (200 OK).
  Verified from PyPI on a clean Python 3.12 venv: install, ingest (writes
  `fux.lock` + `.fux/state/`), `ask`, `path`, `explain`, **zero runtime deps**.
- **Decided / open:** two verification stumbles worth remembering, neither a
  product defect. (1) The first "clean install" check ran on the system Python
  **3.9**, below the supported floor — a local wheel install succeeded there and
  looked like a pass, so it proved less than it appeared; re-run on 3.12.
  (2) `pypi.org/pypi/.../json` served a **cached** response reporting 0.22.1 as
  latest for a minute after a successful upload — the publish job log (200 OK +
  "View at" URL) is the authority, not the JSON API. Don't conclude a publish
  failed from that endpoint alone.
- **Next:** unchanged — **query-at-scale** is the head of phase 5: score from
  `postings` by term instead of loading every row (~10 s at 100k today; table,
  index and exact corpus stats already exist). Scoped in ADR 0011.

## 2026-07-22 — phase 4 complete: knowledge substrate shipped at v0.23.0 · Claude Code
- **Asked:** three rulings (integer token-sums approved as amendment; early-return
  judgment approved; state budget → measure at M8 before optimizing), then
  M6 → M7 → M8 → close-out, with a discipline check first.
- **Did:** discipline check passed (M1–M5 already committed as clean milestone
  commits; tracker rows ✅ with counts) except one reconcile — `fux path`'s
  renderer did not match the format cli-examples had specified first, so the
  **code was changed to follow the doc**, and the multi-path form documented.
  - **M6 PPR-lite:** constants as specced; seed-*rank* personalization; graph
    joins RRF as a fourth list. Guard: fusion skipped for node seeds, since a
    neighbour's passage among a document's own would misattribute it.
  - **M7 profiles:** lean = a Searcher over re-derived candidates with the df
    sidecar injected, so the kernel never learns its profile. Mid-corpus switch
    (full→lean) keeps rankings **and** scores — **mutation-verified non-vacuous**
    (making `lean_searcher` return None fails the test). LRU uses a monotonic
    counter, never a clock. `db pull` sha-verifies and refuses mismatches.
  - **M8:** committed generator + harness; 100k measured. **state 22.96 MB
    (≤30 ✓), df 0.92 MB (≤5 ✓)**, db 1081 MB (77% of §8b), FuxVec scan **54 ms
    < 150 → IVF not built**, ingest 566 s. Relational eval added for
    explain/graph/path.
  - **Close-out:** ADRs 0008–0011 (0010's flagged citations **verified**, not
    asserted); full docs pass; 0004 pair archived; **v0.23.0**.
  - Suites **172+29 → 365 unit + 71 e2e**; eval hit@5 **1.000**; `--lexical-only`
    still exactly 0.762/0.952/0.833.
- **Decided / open:** two behaviour changes recorded in Deviations — a fresh
  clone now answers *exactly* (better than DoD 2's doc-level, so the docs were
  corrected to match), and `auto` gained `lean_threshold` because §G read
  literally would have flipped every small repo to lean silently.
  **The M3a size warning was wrong and is kept next to the measurement that
  corrected it** (351 B/doc projected from this repo's adversarial docs vs
  230 B/doc actual); per the ruling, no zlib change was made.
  **⚠ The honest finding:** at 100k a query takes ~10 s — `postings` is stored
  and indexed but never read at query time, so the whole index still loads into
  memory. Phase 4 solved *storage* at scale, not *query* at scale.
- **Next:** **query-at-scale** — score from `postings` by term instead of
  loading every row (table, index and exact corpus stats already exist).
  Scoped in ADR 0011; it is the head of phase 5. Branch
  `feat/phase4-knowledge-substrate` (10 commits) is ready for PR to main.

## 2026-07-22 — phase 4 M3a–M5: df sidecar, kernel, FuxVec · Claude Code
- **Asked:** Arpit's DoD-7 ruling (Option B — exact df sidecar, guarantee does **not**
  soften), commit M1–M3 first, then continue M4→M8.
- **Did:** committed the backlog as three clean commits (spec docs / M1–M3 / sidecar),
  then landed M3a, M4, M5 — each green, each committed.
  - **M3a df sidecar** (`state/df/`): term hashes sharded by hash low byte,
    delta-encoded + varint df; `_stats.bin` holds total_docs/total_chunks and
    per-field token **sums** (integers round-trip exactly, and `avg_wlen`
    recomputes for any weights without re-ingesting). `Searcher` gained an
    optional `stats` injection — scoring math untouched, only input provenance
    changes. Parity is enforced, not asserted: every term in the vocabulary,
    scored over a strict *subset* (where subset-derived idf would diverge),
    matches full exactly — and **mutation-tested** (removing the injection fails
    both parity tests). Collisions raise rather than silently merging df.
  - **M4 kernel:** `retrieve() -> ResultGraph` is now the only retrieval path;
    ask/find/answer are projections, and explain/graph/path are new ones.
    `explain` = ask seeded by a node (its own `top_terms` become the query), so
    there is genuinely one code path. Edges now persist in the JSON store too.
  - **M5 FuxVec:** full-corpus Hamming prefilter → exact int8 rerank →
    `dense_global` as a third RRF list. **Gate beats v0.22 hybrid:** hit@1
    .762→.810 · hit@5 .952→**1.000** · MRR .833→.873, and ADR 0006's named
    zero-overlap miss is rescued. `--lexical-only` still measures exactly
    .762/.952/.833 with its four goldens byte-identical.
- **Decided / open:** two judgment calls recorded (implementation.md → Decisions,
  → ADR 0010). (1) **dense_global does not fire when BM25F returns zero
  candidates** — removing that early return made "No confident matches"
  unreachable, since a binary prefilter always has a nearest neighbour; measured
  noise scores 0.23–0.26 cosine vs a true rescue's 0.34, so no floor separates
  them as the corpus grows. Re-reading ADR 0006 settled it: "zero lexical
  candidates" meant the correct *document* had no overlap, not the query.
  (2) The two **hybrid goldens were updated deliberately**, with the eval table
  as justification; the four `--lexical-only` goldens were not touched.
  **⚠ Open (size):** early measurement projects the state envelope to ~35 MB
  @100k against Arpit's 30 MB budget — `meta/` + `sigs/` are the risk, not
  `df/` (~2 MB). M8 measures properly; cheap fixes noted if it confirms.
- **Next:** **M6 — PPR-lite expansion** (damping 0.85, 3 iterations, top-10
  ≥0.01, `[engine.graph]` config) + graph list into RRF. Then M7 (profiles +
  `db pull`), M8 (100k benchmark + gate), ADRs 0008–0011, docs pass, v0.23.0.
  Version still 0.22.1.

## 2026-07-21 — phase 4 M1–M3: substrate, state plane, graph · Claude Code
- **Asked:** execute handoff 0004 (knowledge substrate v3) — the full phase, M1 first,
  milestone plan posted before any code.
- **Did:** posted the M1–M8 plan with file-level breakdown, then built and landed
  **M1–M3**, each green before the next.
  - **M1** — `index/sqlstore.py` (schema A, format_version 2, WAL, single-writer
    `.fux/index/.lock`, PK-sorted writes) beside the JSON store, with `[index] format
    = json|sqlite|auto` dispatch; `ingest/lock.py` writes **`fux.lock`** at the repo
    root (format B) and the operational manifest moves to `.fux/index/manifest.jsonl`;
    `--check` is now lock-only and three-way (DRIFT/STALE/STATE-DESYNC); `fux setup`
    writes `.fux/index/` to `.gitignore`. **Parity proven, not asserted:** all six
    v0.22 goldens pass byte-for-byte on the sqlite backend (`tests_e2e/test_sqlite_parity.py`).
  - **M2** — `fux/state/` committed lean plane (format C: 256 buckets ×
    codes/sigs/meta, `FUXSTATE1\0` header, sorted records); Bloom signatures
    (k=4, 9.6 bits/term, 8–128 B — handoff open question 1 **decided**);
    `embed/fuxvec.py` sign-quantizer; bulk/mirror tier (`docs_text` rows, no files
    on disk); `fux cat`; and the **fresh-clone query path** — `rm -rf .fux/index`
    still answers `find`/`ask` at doc level from committed state, and `fux ingest`
    rebuilds the state buckets byte-for-byte.
  - **M3** — `fux/graph/` deterministic extraction: `references`, `cites` (links
    under a citations heading, ranked as evidence), `crawled_from`, `tagged`
    (tag *nodes*, so N docs sharing a tag cost N edges not N²), all EXTRACTED
    grade; node payloads (outline, top_terms) into the `docs` row.
  - Bugs the tests caught and fixed: vectors were hardcoded to the JSON store;
    sqlite corruption escaped past the CLI error boundary; a local-only `fux ingest`
    silently evicted mirror-tier `docs_text`; `fux cat` could not resolve on a
    fresh clone (manifest is in the runtime plane — now falls back to the lock).
  - Suites **172+29 → 262 unit + 55 e2e**, all green. cli-examples.md updated
    *before* each new renderer, per the handoff.
- **Decided / open:** three deviations recorded in implementation.md → Deviations
  (all headed for ADRs 0008/0011): `web:<slug>` ids apply to **all** fetched pages,
  not just bulk (otherwise every curated web doc reads as a permanent
  STATE-DESYNC); the operational manifest survives, relocated, rather than being
  replaced by the lock; `fux answer` has **no** state-only mode — it is extractive
  *and cited*, and citations need line-anchored passages, so it declines with a
  reason rather than citing lines the index never scored. **Open:** profile
  ranking parity (DoD 7) needs corpus-level df to be exact — Bloom-derived df is
  approximate; decide and record honestly at M7/M8.
- **Next:** **M4 — the kernel** (`retrieve()` + `ResultGraph`, re-plumb
  ask/find/answer under it with v0.22 golden byte-parity, then the
  `explain`/`graph`/`path` renderers). M4–M8 + ADRs 0008–0011 + the docs pass +
  the 0.23.0 bump are **not** started; version is still 0.22.1.

## 2026-07-21 — dummy playground repo for dogfooding · Claude Code
- **Asked:** set up a sibling repo with dummy data to play with the fux package.
- **Did:** created `~/my_programs/fux-playground` (git-initialized, initial commit) — fictional
  "Kestrel Coffee" roastery corpus: 3 md docs, 1 txt note, 2 py files, inventory.json,
  suppliers.yaml. Ran `fux setup --docs docs,notes --code src --data data -y` + `fux ingest`
  via fux's own .venv (fux 0.22.1): 8 files → 8 chunks, BM25F + embeddings. Verified
  `ask`/`find`/`answer` all return sensible results; `.fux/` cache committed per convention.
- **Decided / open:** nothing decided; playground is throwaway-adjacent but committed so
  re-ingest determinism can be diffed. `answer` output for the JSON-flattened chunk is noisy
  (dumps the whole flattened lot list) — possible future chunking/answer tuning observation.
- **Next:** play with queries in `fux-playground`; consider it a scratch dogfood corpus.

## 2026-07-21 — Pipeline stages reviewed → full platform matrix (linux/macos/windows) · Claude Code
- **Asked:** review all pipeline stages for necessity; the package must work on
  Python ≥ 3.11 across unix/linux/mac — then "and windows as well".
- **Did:** restructured CI — matrix now linux (3.11–3.14) + macos + windows
  (3.11 + 3.14 boundaries); **"fux gate" became a strict aggregator**
  (`if: always()` + explicit needs-result checks — a skipped required check
  would otherwise count as satisfied), so the wall now transitively requires
  every platform green; **ai-review no longer re-runs the suites** (they ran 3×
  per PR with zero added signal — its value is the separation-of-duties refusal
  + $0-law + credential probes, now ~10 s). Windows product fixes that CI made
  necessary: CLI boundary reconfigures stdout/stderr to UTF-8 on win32 (cp1252
  consoles crash on `·`/`→`), and `.gitattributes` forces LF everywhere with
  explicit binary guards (CRLF checkout would silently break fixture shas +
  goldens per platform; renormalize showed zero drift). pyproject gains the
  3.14 classifier.
- **Decided / open:** publish stages unchanged (pure-py wheel = one build for
  all OS). **Result: all 11 checks green on first run — Windows and macOS
  passed both suites with no further fixes needed.** Merged as PR #36.
- **Bookkeeping note (honest):** the Cowork session's README rewrite was
  uncommitted in the shared working tree and got swept into PR #36's commit
  (`git add --renormalize .` staged it; the unstage didn't hold). The content
  is intact and correct on main — only the commit message is wrong about it.
  Main is protected, so the history stands as-is rather than being rewritten.
- **Next:** Anton dogfood.

## 2026-07-21 — Agent commits now attributed + Verified on GitHub · Claude Code
- **Asked:** commits showed "Unverified" — why, and fix by attributing agent
  commits to Arpit's account.
- **Did:** diagnosed via the commits API: commits were already GPG-signed with
  Arpit's own key (`E38B58D8FDEF7698`), but the committer email
  `claude-code@fux.local` belongs to no GitHub account → `reason: no_user`.
  Fix (empirically converged): the noreply address gave `bad_email` — GitHub
  also requires the committer email to appear in the signing key's identities —
  so repo-local `user.email` is now `arpitarya.dev@gmail.com` (the key's UID,
  verified on the account). Live result on this very commit:
  `verified: true, reason: valid`, attributed to `arpitarya`, author name still
  `Claude (agent)`, `Co-Authored-By: Claude` trailer intact — the agent trail
  survives in metadata while GitHub verifies against Arpit's key.
- **Decided / open:** nothing open — future agent commits in this repo are
  Verified. (Historic commits keep their badge; rewriting history for a badge
  is not worth it.)
- **Next:** merge this PR; Anton dogfood continues.

## 2026-07-21 — v0.22.1 published; scheduled protection audit removed · Claude Code
- **Asked:** (1) what is audit-protection.yml, is it needed? (2) remove it.
- **Did:** explained it (weekly drift alarm comparing live branch protection vs
  `.github/branch-protection.json`; fails loudly, needed an admin PAT secret that
  was never set). **Removed the workflow** at Arpit's call — the wall itself is
  untouched (required checks + enforce_admins verified live); the JSON source of
  truth + `scripts/audit-branch-protection.sh` / `apply-branch-protection.sh`
  stay for manual audits (`./scripts/audit-branch-protection.sh arpitarya fux
  main`). Also this exchange: **v0.22.1 released and verified on PyPI** — wheel
  6.98 MB, sdist now 133 files with zero old-build/CI leaks (the 0.22.0 sdist
  had shipped `archive/`); publish ran with the new tag↔version guard.
- **Decided / open:** no scheduled tamper alarm on the wall anymore — re-add the
  workflow + a `BRANCH_PROTECTION_TOKEN` PAT if that guarantee is ever wanted back.
- **Next:** Anton dogfood.

## 2026-07-22 — First external conformance run: hybrid degrades 4× at 1k · Cowork
- **Asked:** what came out of the 1k test.
- **Result:** the fux-lab suite ran against **fux-engine 0.23.0 from PyPI** —
  52 checks, **51 pass, 1 fail**, plus two findings hidden in INFO rows.
- **The headline (bad):** on 1 000 docs with 11 planted pairs,
  **lexical-only hit@5 0.818 / MRR 0.576** vs **hybrid hit@5 0.182 / MRR
  0.136** — lexical found 9/11, hybrid found 2/11. Opposite direction from the
  engine's own gate (fixture-scale ADR 0006/0010, hit@5 1.000). **Hybrid is the
  default path**, so if this generalizes the default is worse than the flag.
  Fires the recorded reopen-trigger in `compare/query-engine.compare.md`.
- **Cause NOT isolated — two readings, both plausible:** (A) RRF has no quality
  floor, so a noise-carrying dense list demotes correct lexical hits; (B) the
  synthetic corpus is adversarial for dense (450 notes from one paragraph
  template → near-identical sign-quantized codes → arbitrary dense order).
  Discriminating experiment named: **run the same suite on the realistic
  acme-payments corpus**. Recovers → B (add a dense-quality guard); still
  degrades → A (the default engine mode is wrong at scale).
- **Secondary:** zero-overlap rescue **0/2 in both modes** — likely because the
  planted sentence sits in a doc that is otherwise about something else, so the
  *document* vector is dominated by surrounding text. If confirmed, a real
  documentable limit of doc-level dense search (argues for chunk-level codes),
  and ADR 0010's rescue claim holds only when the answer dominates its doc.
- **Tertiary:** fresh-clone parity passed on **top-1 only** — "lower-rank scores
  differ; state plane is quantized". README/CHANGELOG claim "same rankings *and
  scores*". Either narrow the claim or close the gap — a docs-accuracy issue
  at minimum.
- **What passed:** byte-identical double-ingest; all three drift cases
  distinguishable with correct `--strict` exits; honest decline in all three
  verbs (`answer` → null, 0 sources, no fabrication); citations resolve;
  `--lexical-only` stable; every size/latency within ±15 % of baseline.
  Measured @1k: ingest 0.46 s · verbs ~0.12 s · state **200 B/doc** (vs 230
  projected) · index 2 051 B/doc · cache 1 014 B/doc · lock 208 B/doc.
- **Did:** filed `proposals/hybrid-degrades-at-scale.md` with all three
  findings, both readings, the discriminating experiment, and candidate
  mitigations (dense admission threshold · confidence-weighted RRF ·
  size-aware default · `fux doctor` reporting which mode wins). Indexed in the
  proposals README.
- **Vindication of the harness:** an independent black-box suite on a
  realistic-size corpus found in one run what a 21-pair fixture gate could not.
- **Next:** build the acme-payments corpus and re-run — that decides A vs B.

## 2026-07-22 — Phase 5 specced: debug & observability (0005) · Cowork
- **Asked:** a debugging plan for fux *everything*; expose a value in the toml;
  must work with skills too.
- **Did:** wrote `handoff/0005-debug-observability-handoff.md` + prompt, framed
  around **five questions debug must answer** (doc not in corpus · query didn't
  return it · answer wrong/thin · install/corpus bad state · slow/big). Design:
  **`[debug]` section in fux.toml** (`level` off/info/debug/trace, `categories`
  = pipeline stages, `output` stderr|path, `timing`, `redact`, `max_bytes`),
  precedence flag > `FUX_DEBUG` > toml > off, keeping `FUX_DEBUG=1` back-compat
  with the existing hooks contract. New `src/fux/debug.py` emitter with a hard
  invariant: **debug never writes to stdout** — so every golden must pass
  byte-identical at `--debug=trace` (the gate, written at M1 before any
  instrumentation). Redaction default-on (ids/paths/counts, never document
  text — enterprises will email these logs); deterministic lines so two trace
  runs diff clean. Two new commands: **`fux doctor`** (7 groups incl. a
  self-test and — deliberately prominent — *source globs matching zero files*,
  the commonest silent misconfig; every failing check prints what/why/**the fix
  command**) and **`fux why "<q>" --doc <path>`** for the *negative* case
  `--explain` can't cover, ending in a one-line verdict ("not returned: rank 47
  lexical, no dense candidate (cosine 0.19 < pool cut 0.31), no edge from any
  seed") — that sentence is the feature. **Skills requirement met:** new
  `fux-debug` skill (doctor → check → why → fidelity → raise level → *report,
  don't guess*) plus escalation pointers added to fux-query/fux-ingest.
  M1–M6 pre-registered in IMPLEMENTATION.md per the every-execution law; PLAN
  build queue + status rows added; registry bumped.
- **Decided / open:** four open questions routed to ADR 0012 (hand-rolled vs
  stdlib logging; whether `doctor --json` is CI-stable; `why --all`; whether
  `timing` belongs in `[debug]` or its own `[profile]`).
- **Next:** run `handoff/0005-debug-observability-prompt.md` in Claude Code
  (→ v0.24.0), or the 1k regression prompt first — independent of each other.

## 2026-07-22 — 1k regression prompt written · Cowork
- **Asked:** a prompt to execute 1k and do regression testing.
- **Did:** wrote `fux-lab/prompts/run-1k-regression.md` — five steps: (1) run
  `./setup.sh`; (2) **hand-verify every verb's real `--json` shape before
  trusting the suite** (the suite guesses `results[].path`, `sources[].path`
  etc. and was written blind); (3) run `./run.sh` and triage each failure
  against an explicit table — *suite guessed wrong* → fix the suite and record
  the correction; *suite right, engine differs* → **leave it failing** and
  record a finding; *environment problem* → fix and note whether setup.sh
  should have caught it; (4) deepen thin assertions (honest-decline path,
  whether fresh-clone parity actually exercises committed state or silently
  skips, the three drift cases, making the determinism hashes visible so a
  no-op can't masquerade as a pass, cold-vs-warm latency); (5) report the
  metrics table, every suite↔CLI correction, genuine findings phrased for
  upstream filing, and corpus gaps that feed the realistic-repo work.
  Carries the independence ground rule (never read the engine's source to
  explain behaviour). Indexed in lab README + TEST-PLAN §7.
- **Framing that matters:** the prompt tells the agent to expect failures and
  that *correcting the harness is the main work* — the suite has never met a
  real binary, so the first run is its acceptance test.
- **Next:** Arpit runs the prompt; findings feed back as engine observations.

## 2026-07-22 — Clean 1k rebuild; scaffolder is now the single source of truth · Cowork
- **Asked:** remove the 1k dir and do a clean setup.
- **Found first:** `shared/new-env.sh`'s template had drifted from the
  hand-improved `1k/setup.sh` — it still only generated a corpus, so a
  scaffolded 10k/100k would have reproduced the exact "no .fux/" confusion.
  Fixed before rebuilding: the scaffolder now emits the full flow (bootstrap →
  generate → `fux setup --agents --skills --hooks` → `ingest` → `--check` →
  the present/MISSING verification block with per-plane sizes), plus `run.sh`,
  the `fux` shim, and a README whose first line answers "Where is `.fux/`?".
  Template written from a quoted heredoc + sed substitution so the emitted
  script stays readable. Added `--force` to replace an existing env.
- **Did:** `rm -rf 1k` → `shared/new-env.sh 1k`. Verified by scaffolding a
  throwaway 10k and diffing: **identical modulo tier name and the heavy gate**,
  so all environments are now created the same way and cannot drift.
  Also removed `uv init` leftovers (`main.py`, `pyproject.toml`) from
  `playground/`, which had the same scaffolding noise.
- **State:** `1k/` is bare — VERSION, setup.sh, run.sh, fux, README, baselines/
  — awaiting its first `./setup.sh`. Playground keeps its ingested state.
- **Next:** `cd fux-lab/1k && ./setup.sh` (clean run), then `./run.sh`.

## 2026-07-22 — 1k setup confirmed working; discoverability fixed · Cowork
- **Asked:** "i executed it but i don't see .fux folder in 1k dir."
- **Found:** it ran correctly — `.fux/` is at **`1k/corpus/.fux/`**, not
  `1k/.fux/`, because the corpus directory *is* the project (by design). On
  disk: 935 sources in fux.lock, `.fux/` 9.9 MB (cache 4.0 · index 2.0 · state
  4.0), 958 cache files, 1 012 state shards, index.json 1.3 MB, plus the agent
  surface (AGENTS.md, CLAUDE.md, .claude/, .kiro/). So the **first real
  end-to-end fux-lab run succeeded** — first time the harness has driven the
  published 0.23.0 wheel.
- **Real defect was discoverability, not function:** nothing told the user the
  project lives one level down. Fixed: `setup.sh`'s closing block now prints an
  explicit NOTE ("the corpus directory IS the project — .fux/ is inside
  corpus/, NOT in the environment root") plus a present/MISSING table with
  per-plane sizes and lock entry count; `1k/README.md` opens with a callout
  answering "Where is .fux/?" before anything else.
- **Worth noting for the engine:** this is the same confusion a first-time Fux
  user could hit in a repo with a nested docs folder — a candidate line for
  DOGFOOD.md or `fux setup`'s completion message ("wrote fux.toml and .fux/ in
  <abs path>"). Recorded here as an observation, not yet a proposal.
- **Next:** `cd fux-lab/1k && ./run.sh` — the suite's own first real exercise.

## 2026-07-22 — 1k env fixed: corpus IS the project, setup now ingests · Cowork
- **Asked:** "setup 1k the proper way — i don't see .fux dir."
- **Diagnosed:** correct. The old `1k/setup.sh` stopped after generating the
  corpus; `fux setup`/`fux ingest` only ran later, inside a *symlinked
  workspace* the suite created — so the env looked empty and nothing was
  hand-queryable. (Arpit's run had installed fux-engine 0.23.0 fine; the gap
  was purely the missing configure+ingest steps.)
- **Did:** made **the corpus directory the project** — `fux.toml`, `fux.lock`
  and `.fux/` live *inside* `corpus/`, exactly as in a real repo; dropped the
  symlinked workspace entirely (symlink traversal was its own confound).
  `setup.sh` now: bootstrap → generate (skip if present, `--regen` to rebuild)
  → `fux setup --docs docs,notes,reports --code src --data data --images assets
  --agents --skills --hooks -y` → `fux ingest` → `--check` → **prints the
  `.fux/` tree and sizes** so "is it there?" is answered on screen. Added a
  `1k/fux` shim (runs the env's binary inside corpus/). Suite's
  `setup_workspace` → `ensure_project` (idempotent fallback only).
  **Made bootstrap uv-aware** — prefers `uv venv`/`uv pip` when available
  (honours `.python-version`, which this env pins to 3.14), falls back to
  stdlib venv+pip with a clear ≥3.11 message; verifies `fux --version` and
  records the exact build to `.installed`. Removed stray `uv init` scaffolding
  (`main.py`, `pyproject.toml`); kept `.python-version` and committed it.
- **Could not verify here:** the venv's interpreter symlinks to a host pyenv
  path invisible to the sandbox, and the sandbox is Python 3.10 — so `.fux/`
  still gets created on Arpit's first `./setup.sh`, not by me.
- **Next:** `cd fux-lab/1k && ./setup.sh` → then `./fux ask "…"` / `./run.sh`.

## 2026-07-22 — fux-lab restructured: one directory per environment, own .venv · Cowork
- **Asked:** inside fux-lab, one dir for playground with its own `.venv`,
  another for 1k with its own, and 10k/100k set up later on his go-ahead.
- **Did:** restructured to **environment directories, each self-contained**:
  `playground/` and `1k/` each own a `.venv`, `VERSION` (its pinned
  `fux-engine` build), `setup.sh`, corpus, workspace, results and baselines.
  Shared tooling moved to `shared/` (`bootstrap.sh` — venv + version-pinned
  install with a Python ≥3.11 guard; `generate/`; `regress/run.py`, now
  **env-scoped** via `--env` with all paths resolved inside the env and the
  binary defaulting to `<env>/.venv/bin/fux`). Reports now pin the version
  under test. `shared/new-env.sh <name>` scaffolds 10k/100k on demand, wiring
  the `--i-know-this-is-heavy` gate into their setup so the gate lives in a
  readable file rather than muscle memory. Playground gained a `./fux` shim
  (no venv activation) and a "try breaking it" section that feeds observations
  back into the suite. README/TEST-PLAN/.gitignore rewritten for the layout;
  shell + Python syntax verified; 19 tracked files, all venvs/corpora/results
  ignored.
- **Why per-env venvs:** each pins its own build, so 1k can test a release
  candidate while 100k holds the last known-good — and no run can contaminate
  another environment's baseline.
- **Next:** `cd 1k && ./setup.sh && ./run.sh` on a Python ≥3.11 machine (first
  real end-to-end run); 10k/100k await Arpit's go.

## 2026-07-22 — fux-lab decoupled: independent conformance harness · Cowork
- **Asked:** the lab must be a **separate entity, not linked to the local fux
  repo at all**.
- **Did:** fully decoupled `fux-lab` and reframed it as an **independent
  conformance/regression harness for the published `fux-engine` package**.
  Install is now `pip install fux-engine` (PyPI or a candidate wheel) — never an
  editable install from a source tree; the suite drives the `fux` binary via
  subprocess only and never imports fux. TEST-PLAN gained **§0 Independence**
  as a standing rule; the CLI contract is now **derived from observation**
  (`fux --help`, real `--json` output) rather than from the engine's docs; every
  report pins `fux --version` + install method. The realistic-repo prompt gained
  a hard ground rule: *do not read/clone/link any Fux source tree; if observed
  behaviour looks wrong, record it as a finding rather than fixing the suite or
  consulting the engine*. Removed all `../fux` references (verified: zero
  remaining). `git init`'d as its own repo — 9 tracked files, all generated
  content gitignored.
- **Why it's better:** testing the artifact catches packaging faults an editable
  install conceals — exactly the class that shipped in fux 0.22.0's sdist. The
  harness is also now handable to anyone with just the package name.
- **Decided / open:** harness is standalone; realistic generator still pending
  (prompt ready). Suite still unrun end-to-end (Python 3.10 sandbox).
- **Next:** Arpit runs the realistic-repo prompt from the lab.

## 2026-07-22 — Realistic-repo test spec (acme-payments, 1k) · Cowork
- **Asked:** a plan to execute like a *regular repo* — some source, some docs,
  etc. — plus a prompt to set it up right for 1k docs.
- **Did:** accepted the critique (the synthetic generator makes proportional
  buckets, not a repo) and wrote
  **`fux-lab/prompts/build-realistic-repo.md`** — the paste-ready build spec for
  `generate/make_repo.py` producing **acme-payments**: real repo shape (src
  across 5 services, ADRs/RFCs/runbooks/postmortems/meeting-noise, migrations,
  configs, workflows, diagrams, vendor PDFs, wiki mirror), power-law sizes, a
  genuine reference graph incl. deliberately broken links, and the headline
  property — **~12 stale-vs-current contradictions** (superseded ADRs, inline
  dated notes, and unmarked stale guides) where returning the *old* answer is
  the failure the corpus exists to catch. Eval set ~50 questions typed by kind
  (factual/why/how-to/cross-doc/**stale-vs-current**/zero-overlap/
  **unanswerable** — the last verifying Fux still *declines* honestly). Suite
  integration specified: per-kind quality breakdown (an aggregate 0.95 can hide
  0.4 on staleness), a **staleness-precision metric** failing on any inversion,
  and a decline check. TEST-PLAN gained §2b + the spec link; `.gitignore` +=
  `repos/`. Synthetic generator retained for the 10k/100k scale tiers.
- **Decided / open:** realistic repo is the *primary* 1k target; synthetic =
  scale only. Generator not yet built (prompt handed to Arpit).
- **Next:** run the prompt in Claude Code; expect suite↔CLI mismatches on its
  first real end-to-end run (recorded as unverified in TEST-PLAN §6).

## 2026-07-22 — fux-lab created: test plan, generator, regression suite, playground · Cowork
- **Asked:** a testing plan + playground in a **sibling** dir; regression tiers
  at 1k/10k/100k across all source types. Arpit's calls: sibling
  `~/my_programs/fux-lab`; nothing generated committed; **start at 1k**, larger
  tiers on his go; assert all four families (determinism, perf, size, quality)
  and *document everything in detail to improve fux*; maintain the plan for
  on-demand testing.
- **Did:** requested access to `~/my_programs` (only `fux` was mounted) and
  created **`fux-lab/`**: `TEST-PLAN.md` (the maintained spec — tier table,
  required corpus composition, the four assertion families, the report contract
  that phrases findings as candidate `work/proposals/` entries, run
  instructions, maintenance rules); `generate/make_corpus.py` (stdlib,
  seeded/deterministic, 8 source types in fixed proportions, **planted link
  graph + eval pairs incl. zero-overlap + lexical distractors + adversarial
  shapes**, heavy-tier gate); `regress/run.py` (black-box CLI suite:
  double-ingest byte-identity, `--check` clean + DRIFT + `--strict`→2,
  fresh-clone parity, `--lexical-only` stability, citation resolution, all six
  verbs with latencies, size metrics, eval hit@1/hit@5/MRR per mode with
  zero-overlap rescue count, baseline diffing at ±15 %, dated markdown report);
  seeded `playground/`; `.gitignore` (corpora/workspaces/results out).
- **Verified:** 1k corpus builds — 1 008 files, 4.3 MB, 11 eval pairs — and
  **re-generates byte-identically**; gate refuses 10k without the flag; both
  scripts compile; missing-corpus path prints the exact fix.
- **Not verified (recorded in TEST-PLAN §6):** the suite has **never run
  end-to-end** — the sandbox is Python 3.10, fux needs ≥3.11. First real run is
  on Arpit's machine and doubles as the suite's own acceptance test.
- **Next:** Arpit runs the 1k suite locally; 10k/100k tiers await his go.

## 2026-07-22 — IMPLEMENTATION.md (every-execution law) + CHANGELOG · Cowork
- **Asked:** convert the implementation file to full caps; it must be updated on
  EVERY execution whatever the case; maintain a changelog linked from README
  with the latest change surfaced there.
- **Did:** renamed `docs/implementation.md` → **`docs/IMPLEMENTATION.md`**
  (two-step mv on the case-insensitive FS), frontmatter stripped per the
  ALL-CAPS convention, update contract rewritten: **every execution updates the
  file — completed, blocked, failed, interrupted, or abandoned** (🟡/⛔ + one-line
  why; no outcome skips it). CLAUDE.md 4b gained the third binding rule; layout,
  bundle index, registry, GLOSSARY, cli-examples links repointed (history left
  as-is). Created root **`CHANGELOG.md`** (0.19.0 → 0.23.0, keep-a-changelog
  style, from tracker data incl. the v0.23 eval table + known 10.6 s @100k
  limit); README gained **§ What's new** mirroring the latest entry + the
  CHANGELOG link; CLAUDE.md docs law gained 2b (changelog entry per bump,
  mirrored to README in the same change); registry rows for both.
- **Decided / open:** two new standing laws (every-execution tracker; changelog
  per bump). Nothing open.
- **Next:** next-phase head per the tracker: query-at-scale (postings unread at
  query time — ADR 0011).

## 2026-07-21 — M4+M5 reviewed; three rulings for the run-in · Cowork
- **Asked:** agent reported M4 (kernel re-plumb, six goldens byte-parity) + M5
  (FuxVec: hybrid+dense_global **0.810/1.000/0.873** vs v0.22's
  0.762/0.952/0.833; ADR 0006's named zero-overlap miss now retrieved;
  --lexical-only exactly preserved). Asked for the next-step prompt.
- **Rulings (Arpit via Cowork):** (1) **integer token-sums df header approved**
  — better than the spec'd averages (exact round-trip; avg_wlen recomputable
  for any weights without re-ingest); record as approved amendment in ADR 0008.
  (2) **Early-return judgment call approved** — correct reading of ADR 0006
  (rescue = doc-side zero overlap, via the third RRF list; noise floor
  0.23–0.26 vs 0.34 doesn't separate); record in ADR 0010 with those numbers.
  (3) **Budget risk: measure at M8 before optimizing** — if the synthetic 100k
  confirms >30 MB, apply per-bucket zlib first (simpler, no dictionary artifact
  to version), shared dict only if that misses; honest numbers either way.
- **Next:** continuation prompt → M6 (PPR-lite) → M7 → M8 → close-out at 0.23.0.

## 2026-07-21 — M3 escalation resolved: exact df sidecar, guarantee stays provable · Cowork
- **Asked:** the building agent escalated (correctly, per the no-silent-deviation
  rule): lean-profile BM25F can't be *provably* identical to full without exact
  corpus df — soften DoD 7 to eval-top-k, or grow the state plane?
- **Did (Arpit's call, via Cowork):** **grow the state — `state/df/XX.bin`
  sidecar** (delta-encoded term-hashes + varint df + corpus-stats header,
  ~2–5 MB @100k; incremental per-doc maintenance). DoD 7 *strengthened*:
  provably identical by construction (exact df sidecar + exact re-derived tf),
  asserted by full-corpus comparison on fixtures + eval as belt. Rationale:
  "identical rankings" is the brand promise (deterministic/compliance-grade) —
  softening converts a proof into an eval-shaped empirical claim. State
  envelope @100k: ~25–30 MB (still in Arpit's "around 10–20" band). Handoff
  format C + DoD 7 amended; proposal size table noted. Build state per the
  agent: M1–M3 done (uncommitted, suites green), M4–M8 pending, version 0.22.1.
- **Decided / open:** df sidecar in; continuation prompt handed to Arpit.
- **Next:** paste the continuation prompt into the running Claude Code session.

## 2026-07-21 — Milestone tracking law: pre-register + update every milestone · Cowork
- **Asked:** update the implementation file on every milestone, and put that in
  CLAUDE.md so it applies to every plan.
- **Did:** **Phase-4 table pre-registered** in `implementation.md` (M1–M8 +
  close-out, all ⬜, with the pre-registration note); "Now working on" updated.
  CLAUDE.md 4b split into its two binding halves: (1) every plan/handoff
  **pre-registers** its milestone table in implementation.md in the same change;
  (2) building agents update the row **at every single milestone completion**
  (status + tests + note — per milestone, never batched at phase end). The 0004
  prompt aligned: table already pre-registered, per-milestone updates binding.
- **Decided / open:** standing law for all future plans.
- **Next:** paste the 0004 prompt into Claude Code.

## 2026-07-21 — Proposal FINALIZED; plan + handoff 0004 + prompt written · Cowork
- **Asked:** finalize the proposal; create the plan, handoff, and prompt in as
  much detail as possible.
- **Did:** `proposals/knowledge-substrate.md` → **status: accepted** (graduated
  per lifecycle; header links the build spec). fux-plan: 0004 row added to the
  build queue (v3 — substrate; target v0.23.0, ADRs 0008–0011); §8 next-move
  rewritten. Wrote **`handoff/0004-knowledge-substrate-handoff.md`** — the
  build contract with normative specs: fux.db schema v2 (10 tables, WAL,
  single-writer lock, canonical ordering, citation-stable chunk ids), fux.lock
  format + staleness semantics, `.fux/state/` byte layouts (FUXSTATE1 magic,
  256 hash buckets, Bloom k=4 ~1 % FPR ≤128 B), FuxVec algorithm (quantize →
  Hamming top-500 fixed tie-breaks → exact rerank; IVF only if M8 shows
  >150 ms), kernel `retrieve()`/ResultGraph + PPR-lite constants (damping .85,
  3 iters, EXTRACTED 1.0/INFERRED 0.6, decay .8), CLI additions
  (explain/graph/path/cat/db pull), profiles incl. lean LRU; **M1–M8
  milestones** each with scope, plus DoD (8 phase-level criteria incl. v0.22
  golden byte-parity and the eval gate with zero-candidate rescue), 17 edge
  cases, 4 open questions routed to ADRs, close-out contract. Wrote the
  paste-ready **0004 prompt** (explore order, hard rules — parity sacred, math
  untouchable, cli-examples-before-renderers — verify gates, stop-clean
  semantics). Registry bumped.
- **Decided / open:** phase 4 fully specced. Nothing open in design.
- **Next:** paste `handoff/0004-knowledge-substrate-prompt.md` into Claude Code.

## 2026-07-21 — Git carries the state (committed lean plane) · Cowork
- **Asked:** git should carry the state — and it should be maintained.
- **Did:** the lean profile made this viable (~200 B/doc), so `.fux/state/` is
  now **committed, versioned state**: sharded by doc-id hash into 256 buckets
  (codes/sigs/meta, ~80 KB each @100k) so commits touching 50 docs change a few
  buckets, not a 20 MB blob; deterministic bytes = zero diff noise. What it
  buys: `git clone` → **instantly queryable** at doc level; `git log
  .fux/state/` = history of what the corpus knew; `git checkout <rev> && fux
  ask` = time-travel for free. **Maintained, enforced:** ingest rewrites
  state + lock atomically; session-end hook prompts the commit; CI's
  `--check --strict` becomes a **three-way state ↔ lock ↔ sources** gate —
  stale committed state fails the build. Honest limits: binary state (humans
  diff the lock), history growth (sharded deltas; high-churn/100k+ tiers switch
  to db-pull artifacts). §8 table, §8c subsection, §8e summary, appendix tree,
  M2 milestone all updated; gitignore narrows to `.fux/index/`.
- **Decided / open:** state-in-git folded into the ⏳ proposal.
- **Next:** Arpit's verdict → handoff 0004.

## 2026-07-21 — Lean profile: 100k docs in ~20 MB · Cowork
- **Asked:** can 100k docs land at ~10–20 MB total? Be creative; build from
  scratch if needed.
- **Did:** yes — by flipping the storage assumption. Entropy forbids compressing
  600 MB of text to 20 MB, but **determinism means Fux need not store text at
  all: sources are the storage; the index stores find + verify + re-derive**
  (deterministic converters + fux.lock shas reproduce exact bytes on demand).
  New §8c "lean profile" in the substrate proposal: **~200 B/doc persistent
  plane** — 32 B FuxVec code + 96–128 B **Bloom term signature** (validated by
  BitFunnel, Bing's production signature index, SIGIR'17 — fresh citation
  pulled) + ~50 B metadata → **100k ≈ 18–21 MB ✓**, 1M ≈ 200 MB. Query path:
  dense scan + signature prefilter → top ~50 docs → re-derive text → exact
  chunk BM25F/rerank (false positives only add candidates — rankings identical
  to full profile, eval-proven); bounded LRU keeps hot docs warm. Honest
  trades: cold-doc re-conversion latency; source availability at query time
  (web tiers may prefer full profile). Config `[index] profile = full|lean|
  auto`. Section renumbering fixed (8c lean, 8e fresh-clone summary);
  BitFunnel added to references.
- **Decided / open:** lean profile added to the ⏳ proposal; fits M5/M8.
- **Next:** Arpit's verdict on the proposal → handoff 0004.

## 2026-07-21 — Substrate proposal hardened: git contract, fux.lock, sizes, gaps · Cowork
- **Asked:** (1) exact git-committed file set — clone must rebuild from scratch;
  (2) a separate sources file with hash/date for staleness; (3) .fux size
  estimates at 1k/10k/100k/1M docs; (4) graphify as reference, not benchmark;
  (5) review the doc for gaps.
- **Did:** rewrote §8 as **the git contract** — invariant "clone rebuilds from
  scratch"; committed set = fux.toml + **fux.lock** + @lists + agent files;
  `.fux/` fully gitignored (curated-cache commit demoted to opt-in
  `[git] commit_cache` — the invariant outranks the diffs bet). New **§8a
  fux.lock**: committed root-level sorted-JSONL ledger (file kind: sha/bytes/
  converted_at/fidelity; url kind: sha/fetched_at/**max_age_days**) — staleness
  is structural (files by sha, web by age), `--check` works lock-only right
  after clone; replaces manifest.jsonl. New **§8b size envelope** with stated
  assumptions (~15 KB/doc bulk): 1k ≈ 15 MB · 10k ≈ 145 MB · 100k ≈ 1.4 GB ·
  1M ≈ 14 GB (text+postings dominate; vectors+codes <11 % — semantic is nearly
  free; lock sharding option >100k). §2 + references reworded: **graphify =
  prior art to learn from, never a benchmark**. New **§12 gaps review**, each
  resolved or ⚠ flagged: WAL concurrency, corruption=rebuild, chunk-id/citation
  stability, schema versioning, own-postings-vs-FTS5 made explicit, streaming
  ingest, ⚠ multi-corpus fan-out (federation's first requirement),
  ⚠ at-rest encryption deferred, db-pull auth v1, Windows/AV notes, relational
  eval pairs for graph/path. Appendix tree + M1 milestone aligned to the lock.
- **Decided / open:** proposal hardened; still one ⏳ awaiting Arpit's verdict.
- **Next:** Arpit's verdict → handoff 0004.

## 2026-07-21 — One proposal: knowledge-substrate.md (substrate + FuxVec) · Cowork
- **Asked:** merge the knowledge-substrate compare doc and the FuxVec proposal
  into ONE proposal with details on the approach.
- **Did:** created **`proposals/knowledge-substrate.md`** — the single
  consolidated post-v0.22 proposal, 11 sections: context (enterprise litmus),
  break analysis, SQLite store schema (incl. bulk `docs_text` + `codes`), the
  graph (deterministic + semantic edge tiers), the one-kernel/six-projections
  table, **FuxVec as §6 with the four-step approach detailed** (sign-quantize →
  big-int XOR/bit_count full scan → exact int8 rerank → deterministic IVF;
  storage verdicts incl. Parquet-as-export; standalone-package note; honest
  limits), source spec, git tiers + fresh-clone/db-pull story, enterprise
  inputs, the full sample-repo/CLI appendix (ask/answer/cat/explain/path with
  FuxVec + graph lines in --explain), and **§11 build sequencing** (handoff 0004
  milestones M1–M8, eval-gated). Deleted `compare/knowledge-substrate.compare.md`
  + `proposals/fuxvec.md`; repointed all links (compare README, proposals
  README, fux-plan, fux-toml ×2, cli-examples).
- **Decided / open:** one ⏳ document now carries the entire next phase.
- **Next:** Arpit's verdict on `proposals/knowledge-substrate.md` → handoff 0004.

## 2026-07-21 — Fresh-clone story, FuxVec proposal, answer example · Cowork
- **Asked:** (1) gitignored warehouse — what happens on a fresh clone? (2) build
  a vector db from scratch on JSON/Parquet as a package concept — push
  boundaries; (3) add a `fux answer` example.
- **Did:** substrate doc gained **"Fresh clone"** section — curated tier works
  immediately (cache is committed); bulk-local re-ingests to a byte-identical,
  manifest-verified warehouse; bulk-web either re-crawls (drift visible per doc)
  or uses the enterprise path: **warehouse as CI build artifact** + proposed
  `fux db pull` (download + sha-verify vs committed manifest — the lockfile/
  restore pattern). Wrote **`proposals/fuxvec.md`**: vector-db concept from
  scratch — sign-quantize 256-dim int8 → 256-bit codes (32 MB per 1M chunks),
  full-corpus scan via XOR + `int.bit_count()` (C-speed big-int popcount;
  ~tens of ms at 100k), exact int8 rerank of top ~500, deterministic IVF above
  ~100k, storage = packed shards/SQLite BLOBs (JSON for manifest/centroids;
  **Parquet = opt-in export extra** for DuckDB/Spark interop — pyarrow can't be
  a runtime dep); unlocks `dense_global` seeds → rescues ADR 0006's
  zero-candidate miss class; standalone `fuxvec` package noted as its own
  wedge. Substrate §3 vector-DB verdict updated ("adopting closed; building the
  concept proposed"); §8 gained the `fux answer` example (bulk logical-id +
  local file:line citations, graph-hop note). *Web quota blocked fresh cites —
  binary-quantization numbers flagged for build-time verification.*
- **Decided / open:** FuxVec = milestone inside the substrate handoff, eval-
  gated; `db pull` = proposed command. Substrate verdict still awaits Arpit.
- **Next:** Arpit's verdict on knowledge-substrate.compare.md → handoff 0004.

## 2026-07-21 — Litmus change: enterprise mega-project, not Anton · Cowork
- **Asked:** stop thinking of this project in reference to Anton; think from the
  point of a very large-scale project in corporations.
- **Did:** replaced the Anton litmus in CLAUDE.md with the **enterprise
  mega-project litmus** (scale is the default; enterprise realities are design
  inputs; the laws are the sales story: $0 = auditable supply chain, offline =
  no data egress, deterministic = compliance-grade). fux-plan §6a re-scoped
  (substrate = default forward path; standing proposals gain weight).
  knowledge-substrate doc: build trigger re-scoped (corporate corpora *start*
  past the breakpoint — substrate is the next phase, not a contingency) + new
  **"Enterprise design inputs"** section (proxy/SSO ingest, Windows fleets,
  air-gapped installs, corpus-per-boundary access model, audit priority).
  model-handoff-interview: direction-change Q&A added. Anton demoted to
  convenient small-scale testbed.
- **Decided / open:** litmus changed ✅. Substrate verdict still awaits Arpit's
  formal call, but its sequencing is now "next phase by default."
- **Next:** Arpit's verdict on knowledge-substrate.compare.md → handoff → build.

## 2026-07-21 — Documentation-style rule added to CLAUDE.md · Cowork
- **Asked:** add to CLAUDE.md — no large paragraphs in documents; split into
  points; make them roomier.
- **Did:** new **"Documentation style (required)"** section in CLAUDE.md, placed
  before the docs law: short points (one idea each), 3–4-line paragraph cap,
  blank lines between points/sections, tables for comparisons, takeaway-first
  bullets, and a fix-on-contact clause (splitting an existing wall of text is
  part of touching the doc — form is covered by the same staleness law as facts).
- **Decided / open:** binding for all future doc writing in the repo.
- **Next:** Anton dogfood (unchanged).

## 2026-07-21 — Correction accepted: bulk text lives IN the db, not as files · Cowork
- **Asked:** "saving 100k documents in cache is impractical — try to understand."
- **Did:** understood and fixed the real point — the previous tier design still
  put bulk text in a *gitignored file mirror*; but 100k files are impractical
  **as files** (walks, inodes, deletes, Windows/AV/sync), git or no git. Substrate
  doc corrected end to end: storage verdict is now **tier-dependent** — curated
  tier keeps per-file Markdown (review/git value at 10²–10⁴ docs); **bulk tier
  has no file cache at all** — converted text = `docs_text` rows in fux.db (one
  file on disk at any corpus size; SQLite reads small blobs ~35 % faster than
  the filesystem per its own benchmark). New `fux cat <doc>` materializes any
  single doc on demand; bulk citations use logical id + heading (no fabricated
  file paths); break-analysis row corrected (cache breaks at ~10⁴ *as files*);
  §7 tier table + §8 tree/CLI reworked ("never 100k files — your curated files
  plus one database"). CLAUDE.md + fux-plan tier language corrected to match.
- **Decided / open:** correction folded into the ⏳ substrate verdict (still
  awaiting Arpit's overall call on the doc).
- **Next:** Anton dogfood.

## 2026-07-21 — Consolidated into knowledge-substrate.compare.md · Cowork
- **Asked:** merge corpus-at-scale + document-knowledge-graph into ONE doc; show
  sample CLI + folder structure for the implemented substrate.
- **Did:** created **`compare/knowledge-substrate.compare.md`** — the single
  design of record for post-v0.22 architecture: verdict block with four decisions
  (SQLite substrate; doc-index-IS-the-graph; one kernel/six projections; git
  tiers), break analysis, prior-art (graphify/vector-DBs) condensed, source-spec
  extensions, research references, open build items — plus **§8 appendix**: the
  implemented-substrate walkthrough (fux.toml with globs/@lists/mirror tier;
  repo tree showing curated-committed vs mirror-gitignored vs one fux.db;
  worked CLI: resumable `--web` crawl, `ask` rescued via graph hop, `explain`
  node view, `path` with reliability + EXTRACTED tag, the new `--explain` graph
  line). Deleted the two superseded docs; fixed every live link (compare README,
  proposals README — graph marked *graduated*, fux-toml ×2, fux-plan,
  cli-examples). Worklog history left intact.
- **Decided / open:** one doc now carries the whole ⏳ decision; trigger
  unchanged (Anton: scale pain or relational questions).
- **Next:** Anton dogfood.

## 2026-07-21 — One kernel, six projections; sample-repo walkthrough · Cowork
- **Asked:** difference between ask/graph and explain/path — do they need to be
  separate, can one algorithm serve them? Plus: CLI usage + dir-structure examples
  for a sample repo.
- **Did:** researched PathRAG (AAAI'25: node-retrieval → flow-pruned paths with
  reliability scores → answers as ONE pipeline; paths are scored *byproducts*) and
  GraphRAG local search (entity-seeded = query-by-node). Designed the **unified
  kernel**: `retrieve(seed: text|node) → ResultGraph {seeds, expansion, paths,
  passages}`; all six verbs become projections (ask=passages, find=seeds,
  answer=synthesis, explain=node-seeded deep view, graph=nodes+edges, path=paths
  slice). Key insights recorded: `explain` is `ask` seeded by a node; **paths are
  retrieval provenance the PPR expansion already computes** — not a feature, a
  kept trail; `--explain` and `fux path` converge into one trust story. Written
  into corpus-at-scale §"One kernel, six projections" (engine implements one
  kernel + thin renderers; friendly verbs stay). Added **"A sample repo, end to
  end"** to cli-examples.md: acme-payments tree before/after, commit-vs-gitignore
  split per tier, human + agent daily flows, substrate-v2 era marked as proposed.
- **Decided / open:** one-kernel design folded into the substrate-v2 proposal;
  trigger unchanged.
- **Next:** Anton dogfood.

## 2026-07-21 — The merge: graph + corpus-at-scale = one knowledge substrate · Cowork
- **Asked:** is there an opportunity to merge the graph and corpus-at-scale?
  Creative, outside the box, with research.
- **Did:** found the unifying insight — **the level-1 doc index IS the graph's
  node table** (a doc entry's payload = a node's payload; the thin layer was the
  graph unrecognized). Designed "one substrate": single SQLite-v2 file with
  nodes/edges/chunks/postings/vectors; `ask`/`explain`/`graph`/`path` are three
  surfaces over the same tables; retrieval becomes seed (BM25F+dense on docs) →
  **deterministic PPR-lite expansion over edges** (multi-hop recall, zero model
  calls — the natural rescue for ADR 0006's zero-lexical-candidate miss class) →
  per-doc chunk detail → RRF with graph as third signal. Research validation:
  HippoRAG/LightRAG (PPR-from-seeds, 10–30× cheaper multi-hop; *operators beat
  structure* — cheap deterministic edges suffice), LazyGraphRAG (0.1 % indexing
  cost — defer expensive enrichment, exactly our host-session pattern),
  LiteSemRAG (LLM-free graph retrieval is a recognized lane). Bonus surfaces:
  community-detection → auto corpus map (OKF progressive disclosure, generated);
  `--explain` traversal lines; eval-gated. Written into
  `corpus-at-scale.compare.md` §"The merge"; graph proposal updated to point
  there. Two ⏳ items are now one "knowledge substrate v2" phase.
- **Decided / open:** merge proposed + recommended; trigger unchanged (Anton
  dogfood: scale pain *or* relational questions) → then compare verdict →
  handoff → ADR.
- **Next:** Anton dogfood — now the single gate for the substrate phase.

## 2026-07-21 — Document-knowledge-graph proposal parked · Cowork
- **Asked:** "how about creating a knowledge graph on all these documents — just
  a thought."
- **Did:** wrote `proposals/document-knowledge-graph.md` — the sanctioned vehicle,
  since CLAUDE.md bars graph resurrection without sign-off. Shape: a **document
  graph, not a code graph**, strictly a **derived view over the corpus**. Nodes =
  docs/URLs/tags (+ host-session concept nodes); edges in two tiers mirroring
  ingest — deterministic ($0: markdown `references`, citations, web
  `crawled_from` parent/depth, shared tags) and semantic (host-session skill,
  frontmatter-reviewable). Storage = SQLite-v2 rows (never a 512 MiB blob —
  graphify's ceiling). Surface: `fux graph` (neighborhood), `fux path` (how two
  docs connect), `fux explain` gains Links. Parked with a concrete graduation
  trigger: Anton dogfood surfaces a connects/depends/cites-shaped question that
  ask/answer handles poorly → graduates to a compare doc + ADR.
- **Decided / open:** parked, status: proposed. Nothing else open.
- **Next:** Anton dogfood (unchanged — and it's also this proposal's trigger).

## 2026-07-21 — Four course corrections from Arpit (purpose, $0 semantics, tiers, thin index) · Cowork
- **Asked:** (1) host-session LLM pass keeps fux $0; (2) the point is agents
  querying docs/links via Copilot/Claude extensions, not code; (3) vector-DB idea
  reframed — a thin layer over a *document* index with a drill-down command like
  `fux explain`; (4) millions of cache files in git is the wrong approach.
- **Did:** recorded all four in `corpus-at-scale.compare.md` §"Arpit's
  amendments": host-session semantic pass accepted as $0-legal (the old build's
  proven skill-token pattern — authoring may be model-assisted, checking/retrieval
  stay deterministic); docs-not-code focus accepted (sharpens wedge vs graphify;
  new fux-plan §6a); **two-level retrieval proposed + recommended** — compact
  doc-level index (entry + one vector per doc; 100k chunks → ~5k entries,
  brute-force viable forever, no ANN) routing to per-doc chunk loads, plus new
  `fux explain <doc>` drill-down verb; **git-tier correction accepted** — commit
  the *curated* corpus (10²–10⁴ files), gitignore bulk mirrors, commit
  fux.toml+manifest as the reproducible recipe ("git stores the recipe, not the
  warehouse"). CLAUDE.md purpose+tier folds; fux-plan §6a/§6b amended.
- **Decided / open:** 1, 2, 4 accepted; 3 recommended, folds into the SQLite-v2
  build when the scale trigger fires (`fux explain` can ship earlier as UX).
- **Next:** Anton dogfood on the shipped engine; scale work waits for its trigger.

## 2026-07-21 — Prior art: Graphify reviewed in full; vector-DB question closed · Cowork
- **Asked:** research how Graphify's index works; what about vector-DB-alikes?
- **Did:** read the full Graphify README (91.8k★, YC S26): it's a **knowledge
  graph, explicitly not a vector index** — tree-sitter AST locally for code (no
  LLM), an **LLM semantic pass for docs/media** (breaks Fux's $0 law), one
  graph.json (512 MiB cap — same single-blob pattern as our index.json, validating
  the SQLite-v2 proposal), Leiden communities, query/path/explain traversal, MCP,
  query-first hooks, committed graphify-out/ with a union-merge driver. Strategic
  note recorded: graphify ≈ the *archived* Fux build's graph layer, now
  market-validated — if the graph returns it's a view over the corpus. Vector DBs
  (LanceDB/Chroma/FAISS/sqlite-vec/ANN libs): all third-party runtime deps, and
  **ANN solves a problem Fux architected away** (candidates-first = ~200 exact dot
  products; nothing to approximate). Recorded escalation ladder for the
  zero-lexical-candidate miss class: SQLite-v2 brute-force → opt-in ANN extra.
  Both analyses added to `corpus-at-scale.compare.md` with references.
- **Decided / open:** no vector DB (closed with reasoning + reopen path); SQLite-v2
  proposal reinforced. Corpus-at-scale verdicts still ⏳ Arpit.
- **Next:** Arpit calls corpus-at-scale; Anton dogfood continues.

## 2026-07-21 — Scale review: corpus-at-scale compare + fux.toml reference · Cowork
- **Asked:** explain vectors.bin / index.json; is the cache scalable (thousands of
  files, millions of links)?; create + maintain a fux.toml example; sources could
  be folders/files/links at huge scale. Research it.
- **Did:** read the shipped store code (index.json = versioned JSON, full-load,
  postings derived in memory — ADR 0003; vectors.bin = single packed int8
  chunk-vector cache, (sha,fidelity)-keyed — ADR 0006). Researched scale paths:
  **stdlib `sqlite3`** (FTS5 ~3M rows/hr, snappy at 10k–100k docs; sqlite-vec
  brute-force numbers; Fux's dense pass is candidate-only so vectors don't
  bottleneck). Wrote `compare/corpus-at-scale.compare.md`: component-by-component
  break analysis (index.json breaks first ~25–50k chunks; the *cache* itself
  scales with sources and stays per-file Markdown forever — it's the product);
  proposed verdicts — index format v2 = single SQLite db (Fux's scorer unchanged,
  storage only; frontier solves million-link crawls) + `[sources]` globs/excludes,
  first-class files, `@list` files. Created maintained `fux-toml.md` (every
  shipped key + default from config.py; proposed extensions fenced). Registry +
  index + compare README synced.
- **Decided / open:** both scale verdicts ⏳ awaiting Arpit; build trigger = ~25k
  chunks or an outsized crawl.
- **Next:** Arpit reads corpus-at-scale; meanwhile Anton dogfood proceeds on the
  shipped formats (they're right-sized for it).

## 2026-07-21 — README upgraded to the old build's story-first format · Cowork
- **Asked:** review the README and upgrade it, referencing the older README's
  format.
- **Did:** rebuilt README.md on `archive/README.md`'s skeleton — tagline
  blockquote + badges, **The story** (the red-pipe narrative evolved for the
  query engine: the note exists, it's the *finding* that fails), **See it** (real
  as-shipped `fux ask`/`fux answer` output from cli-examples.md), Quickstart,
  ELI5, **Why it's different** (properties: deterministic, cited-or-didn't-happen,
  hybrid-offline, $0, agent-native, corpus-not-index), **How it works** (pipeline
  diagram + two-tier ingest + fenced web/CDP), collapsible full command surface,
  **The $0 guarantee** with honest limits (no synthesis, English-biased model,
  eval tie disclosed w/ ADR 0006 link), **The name** (kept; notes the rule-engine
  vision on hold), Status, closing CTA. Everything claims only shipped v0.22.x
  behaviour. Registry row bumped.
- **Decided / open:** nothing open.
- **Next:** Anton dogfood.

## 2026-07-21 — GLOSSARY.md rename + ALL-CAPS-no-frontmatter convention · Cowork
- **Asked:** rename glossary.md → GLOSSARY.md; ALL-CAPS markdown files need no
  YAML frontmatter.
- **Did:** renamed to [`../docs/GLOSSARY.md`](../docs/GLOSSARY.md) and stripped its frontmatter;
  stripped DOC-REGISTRY.md's frontmatter too (same rule); recorded the convention
  in CLAUDE.md §OKF (ALL-CAPS docs = entry-point files, exempt from `type` like
  CLAUDE.md/README.md; lowercase docs conform as before) and in the glossary's
  own Frontmatter entry; updated links in bundle index + registry row.
- **Decided / open:** convention adopted. Nothing open.
- **Next:** Anton dogfood (per the completed master run's close-out).

## 2026-07-21 — Pipeline review: sdist hygiene, publish guard, build-check → v0.22.1 · Claude Code
- **Asked:** review the pipeline with the new changes — is everything needed?
- **Did (review findings, all fixed except one):** (1) the 0.22.0 **sdist shipped
  the archived old build** (2.43 MB `archive/`) + `uv.lock` + `.github` — added
  hatch sdist excludes + a CI assertion that the sdist stays clean (root-level
  `archive/` only; `archive/` is intended content); (2) **publish.yml had a
  silent-failure mode** — unbumped `__version__` + `skip-existing: true` = green
  no-op publish — added a tag↔version guard + `twine check --strict`, and scoped
  `id-token: write` to the publish job only; (3) restored the old CI's
  **build-check job** (`python -m build` + `twine check`) so metadata bugs fail
  PRs, not releases; added PR concurrency cancellation; `.DS_Store` gitignored.
  Bumped to **v0.22.1** so the corrected sdist is the published one.
- **Needs Arpit:** the `BRANCH_PROTECTION_TOKEN` secret is **missing** — the
  weekly protection audit will fail loudly (default GITHUB_TOKEN can't read
  protection). Create an admin-scoped PAT and `gh secret set BRANCH_PROTECTION_TOKEN`.
- **Next:** merge via the wall, release v0.22.1, verify the sdist on PyPI.

## 2026-07-21 — Release pipeline restored + v0.22.0 published via the wall · Claude Code
- **Asked:** push and publish the new package; create the pipeline and always
  publish it the right way.
- **Did:** ported the merge wall's CI to the rebuild — `.github/workflows/ci.yml`
  with the two required contexts: **"fux gate"** (both suites: determinism,
  goldens, eval gate, packaging budgets) and **"ai-review"** (new
  `scripts/ai-review.sh`: separation-of-duties refusal, $0-law probe on
  pyproject dependencies, credential probe on the diff, suites on the merge
  result — deterministic, model-free, per the old script's design) + a 3.11–3.13
  matrix job. Restored `publish.yml` (release → OIDC trusted publishing, `pypi`
  environment) and `audit-protection.yml` + `branch-protection.json` (note
  refreshed) + audit/apply scripts unchanged. README install now `pip install
  fux-engine`. Release path: PR through the protected branch → checks green →
  merge → GitHub release v0.22.0 → publish workflow → PyPI.
- **Decided / open:** the rebuild's "fux gate" IS the test suites until the rule
  engine returns; the wall itself (contexts, enforce_admins) is unchanged.
- **Next:** Anton dogfood (`pip install fux-engine` now works there).

## 2026-07-21 — MASTER RUN COMPLETE: all three phases shipped (v0.22.0) · Claude Code
- **Asked:** the 0000 master prompt — 0001 → 0002 → 0003 with hard gates; this is
  the final close-out entry.
- **Did:** all three phases implemented, gated, and archived in one run:
  **v1** query CLI (v0.20.0, ADRs 0001–0004), **v1.1** web/CDP/advanced ingest
  (v0.21.0, ADR 0005), **v2** hybrid engine (v0.22.0, ADRs 0006–0007).
  Full-suite final run: `tests/` **173 passed** · `tests_e2e/` **29 passed +
  1 gated skip** (office-with-extra) · eval gate green. README tells the whole
  story (install → setup → ingest → ask/find/answer → agent integration →
  corpus-in-git); 0000 master prompt archived `status: implemented`;
  DOGFOOD.md live for Anton.
- **Decided / open:** hybrid ships **enabled** (gate passed as a tie on the
  fixture set — honest reading + rank-level rescues in ADR 0006); vectors are
  derived data (gitignore-able; corpus = cache + manifest); every open question
  in the three handoffs is resolved and recorded in its ADR.
- **Next:** dogfood in Anton (DOGFOOD.md): configure, ingest, live with
  `fux ask`, build the private Anton eval pairs — those numbers pick what gets
  built next (reopen triggers live in the compare docs).

## 2026-07-21 — PHASE 3 REPORT: Hybrid engine v2 shipped (v0.22.0) · Claude Code
- **Asked:** master run, phase 3 — execute handoff 0003 (eval-first hybrid v2).
- **Did (shipped):** eval harness (21 committed Q→passage pairs incl. deliberate
  zero-overlap paraphrases; hit@1/hit@5/MRR; `--project/--pairs` for private
  Anton evals); `tools/distill/` (potion-base-8M → int8 per-vector → packed
  7.93 MB `model.bin`, sha-pinned, MIT license-checked, recipe documented);
  `fux.embed` stdlib runtime (BertNormalizer+WordPiece with exact token-id
  parity, mean-pool folded into the scale, exact int8 cosine, lazy 10 ms load);
  `.fux/index/vectors.bin` chunk-vector cache ((sha, fidelity)-keyed reuse);
  RRF fusion (k=60) over BM25F candidates with full per-result hybrid detail;
  `--lexical-only` byte-parity with v1 proven by unchanged pre-v2 goldens;
  answer question-similarity factor; wheel ships the bundle (6.98 MB ≤ 15 MB).
- **Eval (the gate, in ADR 0006):** lexical 0.762/0.952/0.833 vs hybrid
  0.762/0.952/0.833 — a tie satisfies the ≥ gate → hybrid enabled. Rank-level
  paraphrase rescues observed; the one remaining miss has zero lexical
  candidates (the recorded candidate-only trade). Warm hybrid query 0.2 ms.
- **Decided / open (ADRs 0006–0007):** re-packed potion over distill-our-own
  (no in-domain corpus yet — Anton's is the reopen trigger); single vector
  file over shards; vectors gitignore-able as derived data. Open risks:
  English-biased model (non-English degrades toward lexical); zero-candidate
  documents unreachable by dense (by design, measured).
- **Next:** final master close-out (full suites, README story, archive 0000).

## 2026-07-21 — PHASE 2 REPORT: Ingest v1.1 shipped (v0.21.0) · Claude Code
- **Asked:** master run, phase 2 — execute handoff 0002 (web, CDP, advanced tier).
- **Did (shipped):** stdlib `html.parser` HTML→Markdown converter (deterministic;
  link/title extraction); `[sources.web]` config + fenced crawl — urllib fetcher
  (UA/timeouts/retries/size cap/redirect-final-URL), robots.txt obeyed, BFS
  frontier with depth/budget/domain caps + URL and sha dedupe (dual provenance),
  attachments through the 0001 converters, `url`/`parent`/`depth`/`fetched_at`
  provenance, byte-stable re-crawl of unchanged pages, web entries persist across
  local-only runs and are excluded from `--check`; hand-rolled RFC 6455 WebSocket
  client (RFC-vector + fake-server tested) + minimal CDP capture (existing Chrome
  only, settle delay, actionable errors, websocket-client extra as flagged
  fallback) + `manual_cdp_smoke.py`; advanced tier `fux ingest --advanced` —
  Docling/tesseract upgrades, (sha, fidelity)-keyed index reuse, upgrades survive
  re-ingest and reset when the source changes; AGENTS contract + fux-ingest skill
  teach judge-and-upgrade; import-fence test (query/index can never touch network
  modules). ADR 0005; 0002 pair archived; README/plan/registry/cli-examples/
  interview updated; v0.21.0.
- **Test counts:** `tests/` 154 passed · `tests_e2e/` 24 passed + 1 gated skip,
  incl. fixture-site crawl (robots/oversize/off-domain skips surfaced).
- **Decided / open (in ADR 0005):** hand-rolled HTML→MD as the always-present
  default (open Q1); CDP settle = fixed configurable delay, networkIdle deferred
  to dogfood evidence (open Q2); crawl resumability deferred (open Q3).
  **Open risks carried:** rendered capture depends on local Chrome; changed-page
  re-ingests are not byte-reproducible (inherent to network sources); HTML
  converter is good-enough, not pandoc.
- **Next:** Phase 3 — execute `handoff/0003-hybrid-engine-v2-prompt.md`.

## 2026-07-21 — PHASE 1 REPORT: Query CLI v1 shipped (v0.20.0) · Claude Code
- **Asked:** master prompt 0000 — execute handoffs 0001 → 0002 → 0003 in sequence
  with hard phase gates. This entry is the phase-1 gate report.
- **Did (shipped):** the complete v1 surface per handoff 0001 — `fux setup`
  (wizard + full flags + `-y`, idempotent TOML merge), hand-rolled frontmatter
  parser (subset YAML, permissive, unknown keys round-trip), inferred-tier ingest
  (md/txt/code/json/yaml/image-stub; office via the `[ingest]` extra) → OKF cache
  with provenance + per-dir index.md + canonical manifest.jsonl +
  `--check`/`--strict`/`--list-inferred`/`--list-skipped`, heading chunker
  (256–512 words, fences/tables atomic, source line spans), true BM25F
  (weight-then-saturate; JSON index, incremental by sha), `fux ask`/`find`/
  `answer` per the cli-examples.md contract (+ `--json`/`--explain`/`--top`/
  `-C`/`--answer-max`; extractive TextRank answers with `[n]` citations),
  `fux setup --agents --skills --hooks` (AGENTS.md managed block + CLAUDE.md/
  copilot/Kiro pointers, fux-query/fux-ingest SKILL.md, fail-open hooks).
  ADRs 0001–0004; 0001 pair archived (`status: implemented`); README rewritten;
  DOGFOOD.md emitted (master rule 6); version 0.20.0.
- **Test counts:** `tests/` 108 passed · `tests_e2e/` 20 passed + 1 gated skip
  (office-with-extra). Byte-identical determinism proven for double-ingest AND
  fresh re-ingest; goldens normalized (3 dp, volatile keys stripped), updated
  only via `FUX_UPDATE_GOLDENS=1`.
- **Decided / open:** `converted_at` = SOURCE_DATE_EPOCH/source-mtime, never wall
  clock (determinism outranks the spec's letter — Deviations + ADR 0002); index
  format JSON by measurement (16 ms load @5k chunks; postings build 525 ms
  dominates — escape hatch: persist postings); token ≈ whitespace word validated;
  answer noise guards (stopword-free overlap, 35 % keep floor) earned from smoke;
  implementation reworked to match cli-examples.md as the normative UX contract
  (--check advisory + --strict→2, JSON key shapes, [n]+Sources citations).
  **Open risks carried:** postings-build cost at very large corpora; paraphrase
  recall weak until v2 hybrid (by design); Cowork has no hook surface
  (instruction files only).
- **Next:** Phase 2 — execute `handoff/0002-ingest-web-advanced-prompt.md`.

## 2026-07-21 — Glossary created · Cowork
- **Asked:** create a glossary.
- **Did:** created [`../docs/GLOSSARY.md`](../docs/GLOSSARY.md) (`type: Glossary`) — ~35
  alphabetical entries covering engine terms (BM25F, RRF, static embeddings,
  chunk/passage, extractive answer, TextRank, eval harness/MRR), ingest terms
  (cache/corpus/manifest/index, fidelity inferred/advanced, Docling, Tesseract,
  CDP, RFC 6455, drift, provenance), process terms (compare doc, proposal,
  handoff, ADR, goldens, worklog, determinism, `$0`), and agent terms (AGENTS.md,
  SKILL.md, fail-open, Anton). Each entry links to its owning doc. Registered in
  DOC-REGISTRY (trigger: new recurring term or meaning change) + bundle index.
- **Decided / open:** nothing open.
- **Next:** Anton dogfooding (DOGFOOD.md) — the build is complete at v0.22.0.

## 2026-07-21 — CLI examples doc: the input/output contract · Cowork
- **Asked:** create examples of CLI input and output, link to necessary documents,
  maintain it.
- **Did:** created `docs/example/CLI.md` (archived) (`type: Reference`) — worked
  input/output for `fux setup` (wizard + flag forms), `fux ingest` (+ `--check`,
  `--list-inferred`, `--advanced`, `--web`), `ask` (incl. honest no-confident-match
  fallback), `find`, `answer` (extractive + citations), `--json` shape, `--explain`
  breakdown (BM25F factors; RRF detail noted for v2), and the error/exit-code
  contract in practice. Declared **normative**: e2e goldens derive from it;
  deviations go through the implementation tracker. Linked from: bundle index,
  cli-surface compare doc, handoff 0001 (formats normative), DOC-REGISTRY (trigger:
  any command/flag/output/exit change — update doc + goldens together).
- **Decided / open:** nothing open.
- **Next:** paste `handoff/0000-master-prompt.md` into Claude Code.

## 2026-07-21 — Implementation tracker created + wired in · Cowork
- **Asked:** an implementation file tracking everything the building agent
  implements, updated at regular intervals / task completion; update the docs.
- **Did:** created `docs/implementation.md` (archived) (`type: Implementation
  Tracker`): baseline table (✅ pre-build work), milestone tables for phases 1–3
  mirroring the handoffs (all ⬜, with per-row test counts + notes), a "Now working
  on" line the agent keeps current at regular intervals, a Deviations-from-spec
  section, and the binding update contract (flip on completion; never ✅ with
  failing tests). Wired it in: master prompt ground rule 5b + a "track as you go"
  line in all three phase prompts; CLAUDE.md docs-law item 4b + layout; registry
  row; bundle index entry.
- **Decided / open:** nothing open.
- **Next:** paste `handoff/0000-master-prompt.md` into Claude Code.

## 2026-07-21 — docs/ is now an OKF-conformant bundle · Cowork
- **Asked:** update the existing documents with OKF as well.
- **Did:** added OKF frontmatter (`type` + title/description/timestamp) to every
  doc that lacked it — fux-plan (`Plan`), model-handoff-interview (`Succession
  Record`), worklog (`Log`), DOC-REGISTRY (`Registry`), all six compare docs
  (`Compare Doc`, status: accepted), the four directory READMEs (`Index`), ADR
  TEMPLATE (`ADR Template`). Created bundle-root [`../docs/index.md`](../docs/index.md) declaring
  `okf_version: "0.1"` with progressive-disclosure listing. Verified by script:
  all 26 docs/*.md now start with a frontmatter block. CLAUDE.md OKF section
  updated: bundle scope = `docs/` (+ future ingest cache); root CLAUDE.md/README
  are entry points outside the bundle.
- **Decided / open:** nothing open.
- **Next:** paste `handoff/0000-master-prompt.md` into Claude Code.

## 2026-07-21 — Master prompt: one run for all three phases · Cowork
- **Asked:** one prompt to execute all of it, one by one.
- **Did:** wrote `archive/handoff/0000-master-prompt.md` (archived) —
  a single paste-ready prompt driving 0001 → 0002 → 0003 strictly in sequence with
  hard phase gates (DoD met + both suites green + ADRs + docs law + archive the
  pair + version bump before the next phase opens), phase reports appended to this
  worklog, stop-clean-on-failure semantics, and versions 0.20 → 0.21 → 0.22. Since
  the original plan gated 0002/0003 on Anton dogfood, the master prompt has Claude
  Code emit a `DOGFOOD.md` quickstart right after phase 1 so dogfooding runs in
  parallel with the remaining phases. Plan updated.
- **Decided / open:** continuous run accepted (dogfood in parallel, not as a gate).
- **Next:** paste `0000-master-prompt.md` into Claude Code and let it run.

## 2026-07-21 — Handoff+prompt pairs for everything finalized (0002, 0003) · Cowork
- **Asked:** create handoff + prompt documents covering *all* finalized work, not
  just v1.
- **Did:** wrote **0002 (Ingest v1.1)** — web crawling (urllib, robots.txt
  non-negotiable, depth/budget caps, HTML→MD via stdlib `html.parser`), CDP
  rendered pages (hand-rolled RFC 6455 client, fake-socket unit tests, Chrome
  optional), advanced tier (Docling/Tesseract extras, fidelity transitions,
  SKILL.md update), fixture HTTP-server e2e (no real network in tests), query-path
  isolation test. And **0003 (Engine v2)** — eval harness *first* (hit@1/5/MRR,
  recorded lexical baseline, the gate + reopen-instrument), distillation pipeline
  in `tools/distill/` (≤10 MB asserted, reproducible recipe, license check),
  stdlib-only inference (`fux.embed`, int8 dot products over BM25F candidates
  only), manifest-invalidated vector cache, RRF fusion + `--lexical-only`, ship
  gate = hybrid beats lexical on eval. Both pairs `blocked_by: 0001`. Plan now has
  the 3-phase build queue table; registry bumped.
- **Decided / open:** build order 0001 → dogfood → 0002/0003 in either order.
  Open question parked in 0003 for Arpit at review: commit vectors vs gitignore.
- **Next:** run the 0001 prompt in Claude Code.

## 2026-07-21 — Ideation (git-corpus bet) + v1 handoff & prompt written · Cowork
- **Asked:** Arpit's seed — the ingested corpus lives in git long-term and
  ultimately feeds product development. Think outside the box (uses, value, what to
  add), then a detailed implementation plan, with research.
- **Did:** researched signals (Knowledge-as-Code pattern Jan 2026; Karpathy LLM-Wiki
  paradigm; competitors semtools/rlama/qmd/llm-search — none version knowledge).
  Product-builder pass: winner = **product-memory corpus** (Arpit's seed, extended)
  — folded into fux-plan §6b + CLAUDE.md (deterministic diff-friendly cache is now a
  hard requirement); parked three proposals with OKF frontmatter:
  `research-to-spec`, `knowledge-diff` (fux diff/log, time-travel), and
  `audit-evidence-trail` (deterministic cited answers as evidence chain; Plane
  seed). Wrote the **detailed v1 implementation plan**:
  `handoff/0001-query-cli-v1-handoff.md` (DoD, in/out scope — web/CDP/OCR pushed to
  v1.1, embeddings v2; module layout; hard constraints; edge cases; both test
  suites; open questions; ADRs 0001–0004) + `0001-query-cli-v1-prompt.md`
  (paste-ready, explore→plan→implement→verify→close-out incl. archiving the pair
  and bumping to 0.20.0). Pre-mortem gate folded into the handoff (scope-drown,
  chunker quality, golden brittleness, parser correctness, cross-platform).
- **Decided / open:** git-corpus bet adopted into plan + CLAUDE.md ✅; v1 scope cut
  ✅ (local inferred-tier only). Nothing open.
- **Next:** run the 0001 prompt in Claude Code; dogfood the result in Anton.

## 2026-07-21 — Proposals dir, doc archiving, OKF conformance · Cowork
- **Asked:** add to CLAUDE.md — (1) proposal docs for later-stage ideas, (2) archive
  implemented docs, (3) follow the OKF pattern for the fux package and features.
- **Did:** identified OKF = **Google's Open Knowledge Format v0.1** (June 2026 open
  spec: markdown + YAML frontmatter bundles, required `type` field, index.md
  progressive disclosure, log.md history, citations; permissive consumption) — read
  the full spec; it's near-identical to Fux's native substrate, so conformance is
  cheap interop. CLAUDE.md: proposals added to lifecycle step 0
  (`work/proposals/`, `status: proposed`, graduate to compare/plan), archive rule
  (`archive/`, move on completion with `status: implemented` + ADR link), new
  "Follow the OKF pattern" section (type on every knowledge doc, cache = OKF
  bundle, worklog = log.md convention). Created `proposals/` + `archive/` READMEs;
  updated ingest doc (cache is an OKF bundle), DOC-REGISTRY (2 new rows), plan.
- **Decided / open:** all three ✅. Nothing open.
- **Next:** plan → handoff → prompt for query CLI v1 (OKF conformance now in scope).

## 2026-07-21 — Ingest types + e2e suite + doc registry; CLAUDE.md refreshed · Cowork
- **Asked:** ingest images/JSON/txt/YAML too; a thorough, *maintained* e2e test suite
  in a sibling dir; hooks + docs that prompt updating stale documents via a separate
  tracking file; update CLAUDE.md with the useful information. Research it.
- **Did:** researched OCR (Tesseract offline/open-source; Docling OCR stage; OCR
  quality is a first-class retrieval bottleneck → OCR belongs in the judge-able
  advanced tier), doc-freshness practice (last-reviewed signals, owners, docs-in-
  same-change, CI freshness scoring), pytest e2e patterns (per-dir conftest, golden
  files, subprocess CLI runs). Added file-type section to ingest doc (images:
  metadata stub inferred / OCR advanced; JSON stdlib-flattened; YAML fenced text —
  stdlib has no YAML parser; txt native). Created **`work/DOC-REGISTRY.md`** (trigger
  + last-verified per doc; hook reads it at session end, advisory + fail-open; also
  step 5 of the generated agent contract). CLAUDE.md: replaced the stale
  "decisions pending" scope with the decided design summary, added `tests_e2e/`
  mandate (fixture corpus + goldens, maintained), registry in the docs law, layout
  refresh, and a standing **auto-fold rule** (durable session knowledge → CLAUDE.md
  in the same change). Synced plan + agent-integration doc.
- **Decided / open:** all three additions ✅. Nothing open.
- **Next:** plan → handoff → prompt for query CLI v1 (now includes e2e suite +
  registry hook in scope).

## 2026-07-21 — Sub-decisions resolved with research; `init` → `setup` · Cowork
- **Asked:** research the open sub-decisions (reranker-beyond-RRF; chunking unit;
  BM25F field weights) and rename `fux init` to `fux setup`.
- **Did:** researched chunking (structure-aware heading-based wins — up to ~9-pt
  recall swing, 15-pt accuracy spread across strategies; 256–512-token sweet spot)
  and BM25F (weighted-tf-then-saturate per Lucene `combined_fields`; titles 2–5×
  body is standard; k1=1.2/b=0.75 defaults). Resolved all three in
  `query-engine.compare.md` with references: **no reranker** (cross-attention needs
  ~22 M-param/~80 MB models — 8× over the 10 MB budget; RRF stays), **chunking =
  heading-based**, 256–512 tokens, heading-path context, code/tables atomic,
  `file:line` boundaries; **BM25F = heading 3.0 / path 2.0 / body 1.0**, overridable
  in `fux.toml`. Renamed `fux init` → **`fux setup`** across cli-surface,
  agent-integration, compare README, plan, handoff (worklog history left intact).
- **Decided / open:** all sub-decisions ✅ — **nothing is open**. Reopen-triggers
  recorded (eval-set evidence only).
- **Next:** plan → handoff → prompt for query CLI v1.

## 2026-07-21 — Agent-integration accepted; one-SKILL.md verdict; `fux init` · Cowork
- **Asked:** accept agent-integration; are per-tool skills (Claude/Copilot/Kiro) a
  good idea; single setup command, interactive + flags. Research it.
- **Did:** researched — **Agent Skills is an open standard since Dec 2025**
  (agentskills.io); by Mar 2026, 32+ tools incl. Copilot, Kiro, Codex, Cursor,
  Gemini CLI read the same `SKILL.md`, so **one skill file serves all tools** (the
  old build's per-platform skillgen is obsolete). Added Skills section to
  agent-integration doc (layer cake: AGENTS.md=when, SKILL.md=how, hooks=enforced;
  ship `fux-query` + `fux-ingest` skills). Added `fux init` to cli-surface doc:
  interactive wizard default, flag-per-prompt, `-y`, idempotent (npm init / gh auth
  / clig.dev pattern). Synced plan + compare README.
- **Decided / open:** agent-integration ✅; skills = one SKILL.md ✅; `fux init` ✅.
  **All major forks now decided.** Open sub-decisions only: reranker-vs-RRF (rec:
  RRF), chunking unit, BM25F weights.
- **Next:** plan → handoff → prompt for query CLI v1.

## 2026-07-21 — CLI verbs + CDP accepted; numpy-vendoring disproven; agent-integration proposed · Cowork
- **Asked:** accept cli-surface + ingest verdicts; ingest must also work over Chrome
  DevTools Protocol; could numpy be vendored as internal files and resynced per
  build; new fork — Claude/Copilot/Kiro hooks or md files (or both, or better) so
  agents know to query fux; everything backed by references.
- **Did:** researched CDP (JSON-RPC over WebSocket; stdlib has no WS client → hand-
  rolled RFC 6455 client on `socket`, user's own headless Chrome, `render = "cdp"`
  config), numpy internals (core is platform-compiled C extensions + BLAS — not
  copyable Python; vendoring = per-platform build farm), and the agent-instructions
  landscape (AGENTS.md = Linux Foundation standard read by Copilot/Cursor/Codex/
  Windsurf/Zed, picked up by Kiro + Claude Code; Kiro steering + hooks; Claude Code
  `UserPromptSubmit`). Marked cli-surface accepted; added CDP section to ingest doc;
  added numpy-vendoring resolution with proof to packaged-model doc; wrote
  `agent-integration.compare.md` (proposed: files + hooks from one `fux init-agents`
  generator, MCP deferred). Synced plan + compare README.
- **Decided / open:** CLI verbs ✅; CDP ingestion ✅; numpy vendoring ✗ (stdlib
  stands). Open: agent-integration verdict; reranker-vs-RRF; chunking; BM25F weights.
- **Next:** Arpit calls agent-integration → then plan → handoff → prompt for v1.

## 2026-07-20 — Verdicts confirmed + refinements; numpy resolved out · Cowork
- **Asked:** accept engine/ingest/model verdicts. Refinements: friendlier CLI
  commands than `fux query --flags`; "what if I don't use numpy?"; ingest as a skill
  + usable from other Python scripts; ingest follows links and their attachments
  multiple levels deep; converted docs need metadata for maintenance/traceability.
- **Did:** wrote `cli-surface.compare.md` (proposed `fux ask`/`find`/`answer`, verb
  per intent). Resolved numpy in `packaged-model.compare.md`: **stdlib-only** — with
  candidate-only ranking (BM25F top-200 → dot products) query latency is single-digit
  ms without numpy; chunk vectors precomputed at ingest. Extended
  `ingest-strategy.compare.md`: per-file traceability frontmatter (source, sha256,
  fidelity, converter, origin/url/parent/depth — first dogfood of the hand-rolled
  frontmatter parser), library-first `fux.ingest` API + agent skill, fenced `--web`
  crawling (max_depth, same_domain, robots.txt, attachments). Synced plan + compare
  README.
- **Decided / open:** all four major forks ✅ accepted; numpy ✅ out. Open: CLI naming
  verdict (proposed verbs), reranker-vs-RRF (rec: RRF only), chunking unit, BM25F
  field weights.
- **Next:** Arpit calls the CLI naming → plan → handoff → prompt for query CLI v1.

## 2026-07-20 — Query-CLI decisions locked; researched + 4 compare docs · Cowork
- **Asked:** decide the three forks with additions — two-tier ingest (inferred +
  advanced/agent-triggered) + manifest + config-driven dirs; staged engine v1/v2/v3
  with a look at BM25 alternatives; output option 2 plus non-LLM synthesis via a
  model *built into the package*; hard rule — no external model, but a bundled model
  ≤10 MB is allowed. Research it.
- **Did:** web-researched retrieval (BM25F, SPLADE, cross-encoders, RRF hybrid ~91 %
  recall), tiny packageable models (Model2Vec/Potion ~8 MB, numpy dep), and non-LLM
  synthesis (TextRank/LexRank extractive). Rewrote `query-engine`, `query-output`,
  `ingest-strategy` compare docs with accepted verdicts; added
  `packaged-model.compare.md`. Synced `fux-plan.md` (Decisions §6) + compare README.
- **Decided / open:** engine = BM25F → +bundled static embeddings via RRF → agent
  surface; output = passages default + `--answer` extractive (no LLM); ingest =
  two-tier + manifest + `fux.toml`; model = ≤10 MB static embeddings, stdlib inference
  + optional numpy. **Honest limit recorded:** ≤10 MB can't *generate* prose —
  `--answer` selects/orders source sentences. Open: stdlib-vs-numpy, reranker-vs-RRF,
  chunking unit, BM25F field weights.
- **Next:** resolve the open sub-decisions, then plan → handoff → prompt for query
  CLI v1.

## 2026-07-20 — Pivot to a document-query CLI; three compare docs · Cowork
- **Asked:** hold the rule engine; make the first deliverable a CLI that answers
  natural-language questions over documents in a defined set of folders. Produce a
  compare doc wherever there are multiple options, decide by reading them.
- **Did:** wrote `work/compare/query-engine.compare.md`, `query-output.compare.md`,
  `ingest-strategy.compare.md` (+ `compare/README.md`). Grounded with references
  (BM25, RAG, sentence-transformers, MarkItDown/Docling). Synced the pivot into
  CLAUDE.md (scope + compare step 0), `fux-plan.md`, `model-handoff-interview.md`.
- **Decided / open:** proposed verdicts recorded in each compare doc; **all three
  forks await Arpit's call.** The engine fork also decides whether `$0`/no-LLM still
  binds this tool.
- **Next:** Arpit reads the compare docs and picks a verdict per fork → then
  plan → handoff → prompt for query CLI v1.

## 2026-07-20 — From-scratch rebuild: CLAUDE.md + package skeleton · Cowork
- **Asked:** review the old (non-working) build for context, then write a fresh
  CLAUDE.md and do basic Python package setup (keep the name, bump the version).
- **Did:** reviewed `archive/`; wrote binding CLAUDE.md (scope, constraints,
  lifecycle, docs-in-sync); scaffolded `src/fux/` (hatchling, v0.19.0, CLI +
  `FuxError`), README, `docs/fux-plan.md`, `docs/model-handoff-interview.md`,
  `docs/adr/TEMPLATE.md`. 4 smoke tests pass.
- **Decided / open:** src/ layout + hatchling; version 0.19.0 (bumped from old
  0.18.0); constraints carried forward from the old build.
- **Next:** (superseded by the pivot entry above).
