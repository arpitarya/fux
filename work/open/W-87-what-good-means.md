---
type: OpenItem
id: W-87
title: "W-87 — define what \"good\" means, THEN measure"
description: "Split out of W-82 on 2026-08-27 and then widened: six forks defining the quality contract, and every measurement, benchmark, regression and verification task that was waiting behind them. Phase 0 is RULED (2026-08-27, ADR-QUALITY) — all six forks, with the cost model frozen before any score. P5 is DONE (2026-08-27) and found a live ingest crash. What remains is P1-P4, blocked on inputs and environment rather than on a decision."
status: open
lane: arpit
timestamp: 2026-08-27T00:00:00Z
---

# W-87 — define what "good" means, then measure

## ✅ PHASE 0 IS RULED — 2026-08-27 (Arpit), all six forks

**The contract is declared.** It lives in
[ADR-QUALITY](../../docs/adr/0044_quality-contract.md); the argument behind it is
[the compare doc](../compare/what-good-means.compare.md), now `accepted`; the
frozen declarations are [`tools/quality/mix.toml`](../../tools/quality/mix.toml).

- **All six proposed verdicts accepted as written**, plus a mechanism for fork 3
  the compare doc did not specify: the cost is a **confidence target**,
  `t = 0.75` → penalty `c = t/(1-t) = 2`, frozen **before any score exists under
  it** — which is the only thing that made it rulable today rather than later.
- **Two guards ship with it**: every verdict publishes a **weight-stability
  interval** (the range of `c` over which it holds) and the **risk–coverage
  curve** beside the scalar.
- ⚠ **Fork 6's law question is NOT settled** — it is filed as
  [W-89](../../archive/open/W-89-does-l2-reach-a-query-log.md), as fork 6's own verdict asks.
- ⚠ **P1–P4 are untouched by this.** The contract being declared is what
  *unblocks* them; it does not advance them, and every environmental blocker
  below still stands.

---

**Model: Opus** for Phase 0 — every fork is a judgment call with no test that
can catch a wrong one, and fork 3 is order-dependent in a way that cannot be
repaired afterwards. **Sonnet is fine for the phases below it**, once the
contract is written.

**Split from [W-82](W-82-the-consolidated-build.md) §5.2 on 2026-08-27**
(*"let's cover it as part of separate work"*), then **widened the same day** to
absorb W-82's measurement work.

## Why the measurement work moved here

**Arpit, 2026-08-27:** *"first, we need to define what good is and then maybe
run all those benchmarks, test, regression, etcetera."*

**That is a sequencing argument and it is correct.** A benchmark run before the
bar is declared produces a number nobody can interpret — and this project has
the receipts: **two runs passed their number and failed their claim**, both
caught by a human rather than by the gate. Running more measurements against an
undeclared contract manufactures more of exactly that.

⚠ **One honest exception, recorded so nobody treats the sequence as absolute.**
**§3.0 is NOT blocked by Phase 0.** Its threshold is already pre-registered and
frozen (≥ 80 % → fork 3 is yes; ≤ 40 % → no; between → Arpit, unadjudicated), and
a frozen threshold may never move. It lives here because it is measurement work
and this is now the measurement item — **not because it is waiting on the
contract.** It may run the moment a URL corpus exists.

## The phases

| phase | what | blocked by |
|---|---|---|
| ~~**P0**~~ | ~~declare the contract — the six forks~~ | ✅ **RULED 2026-08-27** — [ADR-QUALITY](../../docs/adr/0044_quality-contract.md). P1–P2 are unblocked on the contract and blocked only on inputs |
| **P1** | the measurement apparatus — sealed subset, decoy set, content-free placebo, ~~orphaned-module check~~ | P0 · needs `fux-playground` — ⚠ except the **orphaned-module check, ✅ BUILT 2026-08-27**, which never did |
| **P2** | the quality runs — `recall@k`, the funnel, the cost-weighted curve | P0 · P1 · needs corpora |
| ~~**P3**~~ | **§3.0** — sanitized-sha stability | ✅ **PASS 2026-08-27**, 19/19 = 100 % — [verdict](../regression/2026-08-27-p3-sha-stability/VERDICT.md) |
| ~~**P4**~~ | forks 3 & 4 — `validate` and token storage | ✅ **RULED AND BUILT 2026-08-28** — [ADR-FETCHER](../../docs/adr/0019_fetcher.md) decision 12, [ADR-MAINTENANCE](../../docs/adr/0032_hooks.md) decision 13 |
| ~~**P5**~~ | ~~`tests_e2e/` verification~~ | ✅ **DONE 2026-08-27** — 74/74 on 3.11.15; found one real defect |

**What did NOT move, and why:** W-82's seven blocked rulings (1, 4, 6, 7, 12, 16
and 3) are **record and code edits waiting on a file lock**, not measurement.
Refiling them here would cut them loose from W-82's definition-of-done and
duplicate OPEN-WORK, which rule 7 forbids.

---

## The gap

**Fux measures rigorously and has never declared what it is measuring.**
[ADR-RS](../../docs/adr/0036_predictions.md) governs *how* a claim is frozen and
is silent on *what quantity is worth freezing* — so every quality number fux has
produced carries an **undeclared query distribution** and an implicit cost model
in which **a fabricated citation and an honest decline count the same.**

⚠ **Two runs already passed their number and failed their claim, and a human
caught both** — [P1-GATE](../regression/2026-08-09-pruning-eval/VERDICT.md)
(a 0.00 delta over a population the treatment never touched) and
[the budget sweep](../regression/2026-08-22-budget-sweep/ANALYSIS.md)
(*"satisfied by its letter and violated by its purpose"*). **Both were caught by
judgment, not by the gate.** That is the argument for this item.

---

## The proposed verdict

**In [`work/compare/what-good-means.compare.md`](../compare/what-good-means.compare.md)**
— researched against the retrieval and RAG-evaluation literature on 2026-08-27,
with a proposed answer per fork, a matrix, references, and a reopen trigger.

**What the literature settled, in one line each:**

| fork | proposed | the finding behind it |
|---|---|---|
| 1 · where `P(q)` comes from | **declare it; start uniform** | TREC weights topics equally *and says so* — the fork is declared vs undeclared |
| 2 · `unanswerable` in or out | **INSIDE**, with an answerable-only slice | accuracy-only metrics **reward** fabrication (*Nature*, 2026) |
| 3 · who sets the weights | **published, set BEFORE seeing the score** | the "open rubric" the literature recommends |
| 4 · is `answered` measured | **yes — separate `judged` series, never fused** | a documented GPT-4o judge collapse May→June 2026, zero coupling |
| 5 · public or internal | **funnel public, judged internal** | publishing the reproducible half *is* the auditability claim |
| 6 · build a query log | **no — and there is a law question first** | queries are content-adjacent; **L2 covers corpus content, not queries** |

**And the headline it proposes:** a four-gate funnel — `reachable` →
`in window (recall@k)` → `placed (nDCG, MRR)` → `answered` — with **recall@k as
the honest headline**, because retrieval sets a hard ceiling on everything
downstream and it is the gate fux most fully controls.

⚠ **`nDCG` is demoted for structural reasons, not stylistic ones:** a reranker
discards the retriever's ordering, and LLMs show **U-shaped** attention over
long context, so a *monotonically decaying* metric asserts a value curve the
consumer demonstrably does not have. Fux has a reranker and feeds an agent —
both conditions hold.

---

## What was blocked on Arpit — all three closed 2026-08-27

- [x] **Accept or override the compare verdict**, fork by fork. → **all six
      accepted as written.**
- [x] ⚠ **Fork 3, the order-dependent one.** → **ruled and frozen in time.**
      `t = 0.75` → `c = 2`, committed in `mix.toml` **before** any score exists
      under it, which is the only ordering under which the number means
      anything. Veto condition 3 in ADR-QUALITY is the check that it never moves
      afterwards.
- [x] **Fork 6's law question** — does L2 reach a query log? → **not answered,
      deliberately.** Ruled out of the metrics decision and filed as
      [W-89](../../archive/open/W-89-does-l2-reach-a-query-log.md), `arpit` lane.

**Nothing in this item is blocked on Arpit any more.** What remains is blocked
on **inputs and environment** — see the phases below.

## P1 — the measurement apparatus (moved from W-82 §3.5, 2026-08-27)

**Owed since W-78 ruling 2 was accepted**, and ⚠ **nothing may cite any of it as
in force until it is built** — ADR-RS's own register says *"the sealed set and
the two controls — **owed, not built**"*.

- [ ] **The sealed query subset** — mechanical, with the power tension answered
      in writing. A sealed holdout is what FrontierMath actually used;
      disclosure alone is the fallback, and BIG-bench's canary is the
      counter-example (a marker embedded *so that* labs could exclude it, and
      reproduced by models trained on it regardless).
- [x] ✅ **The decoy set** — BUILT 2026-08-27,
      [`tools/quality-controls/decoys.jsonl`](../../tools/quality-controls/decoys.jsonl).
      Fifteen domain-plausible questions the corpus cannot answer.
      ⚠ **This is the one kind of evaluation material an agent may author** —
      there is no correct answer, so there is nothing to fit. That is why these
      were written and the goldens were not.
      🔴 **They found a defect on their first run**: one of fifteen is reported
      `grounded`, because `coverage` is corpus-wide and its terms scatter across
      four documents —
      [the run](../regression/2026-08-27-decoy-control/report.md),
      ADR-CONFIDENCE decision 12. **Named, not fixed.**
- [x] ✅ **The content-free placebo arm** — BUILT 2026-08-27,
      [`tools/quality-controls/placebo.py`](../../tools/quality-controls/placebo.py).
      Matched-length enrichment carrying no information about its document.
      ⚠ **One shared sentence pool, so every placebo has the same vocabulary** —
      a placebo *about an unrelated topic* would still discriminate, and would
      measure something else. Deterministic from the source sha (L3, verified
      byte-identical), no model called, and it **installs nothing**.
      ⚠ **BUILT is not RUN.** A placebo produces its value as a **delta between
      arms**, which decision 12 governs, so grading three ways needs the
      blind/informed question answered before any number may be cited.
- [x] ✅ **The orphaned-module check** — BUILT 2026-08-27,
      [`tests/test_orphaned_modules.py`](../../tests/test_orphaned_modules.py).
      **Its exception list is EMPTY**, which was the design goal: the two
      non-static entry points are both already *declared* in the repository, so
      the check reads them instead of hard-coding rows. `[project.scripts]`
      gives `fux.cli` and `fux.maintain.mergedriver`; `decode.BUILTIN_MODULES`
      gives all fourteen dynamically-loaded decoders; `fux.__main__` is rung 4
      of the invocation ladder. Adding a decoder or a console script keeps the
      check honest with no edit to it.

      ⚠ **Reachability from an entry point, not "has an importer."** The naive
      check is too weak *and* too strong: `hybrid.py` and `fuse.py` imported
      each other, so each had an importer and both were dead — while nearly
      every live module here is imported only by its own package's `__init__`,
      which is normal. **The walk follows `import_module("literal")` too**, or
      it would call every decoder dead on day one and get switched off.

      ⚠ **Proven, not merely green.** A companion test reconstructs the
      mutually-importing dead pair and asserts both are flagged, and a planted
      dead module was confirmed to turn the live check red and green again on
      removal — **this repo has recorded two vacuous passes and does not need a
      third.**

- [ ] **ADR-RS decision 15 loses `NOT BUILT`** in the same change. ⚠ **NOT
      flipped** — decision 15 is about the content-free placebo, and three of
      P1's four items are still owed. One item landing does not discharge it.

⚠ **The claim that these needed an absent `fux-playground` was FALSE** — it was
on the machine all along, with its 50 goldens, and two of the three were built on
2026-08-27 within the hour. **Only the sealed subset remains**, and it is blocked
on a judgement rather than an environment: decision 15 says sealing *shrinks* the
visible set and whoever builds it must resolve that tension, not inherit it.

## P2 — the quality runs

- [ ] **`recall@k` is not computed today.** It needs known-relevant sets per
      query — real annotation across the 50 playground goldens.
      ⚠ **Also not this session's to do.** Annotating *which documents are
      relevant* after seeing which ones rank well is how a metric gets fitted to
      the system it is meant to judge. **The annotation must precede the
      scores**, and for this session it no longer can.
- [ ] **The `unanswerable` class does not exist** and must be authored — and
      authored **blind**, or it contaminates the set it is meant to test
      (the W-78 lesson).
      🔴 **THIS SESSION CANNOT AUTHOR IT.** It has read the goldens, the decoys,
      and per-query scores across four measurement runs. **Anything it wrote
      would be informed by construction**, and the one property this class needs
      is that its author had not looked. ⚠ **The 15 decoys are NOT this class** —
      they are a control, authored by this session, and using them as the
      `unanswerable` class would launder informed material into a blind slot.
      **It needs a different author.**
- [ ] ⚠ **Part B cannot run as specified.** `acme` and `orbit` were lost in the
      2026-08-20 lab wipe **along with their generator**, and
      `tools/pruning-eval/` still hard-codes reading them. **Part A — the
      declarations — needs none of that**, and declaring is most of the value.
- [x] ✅ **MEASURED 2026-08-28** —
      [the run](../regression/2026-08-28-resolution-floor/report.md), ADR-RS
      decision 19. 🔴 **The placeholder admits coin flips**: a paired exact test
      needs a net of **6–16** depending on how many queries flipped, and **at
      net 2 the p-value is never below 0.68.**
      ⚠ **It is the wrong SHAPE too** — the bar tracks the **flips**, not the set
      size — so replacing `2` with `8` would be a better wrong answer.
      **The cheapest fix is a REPORTING change: a run must state its discordant
      count**, and no filed run does, so no paired result on record can be
      tested from what was filed.
      ⚠ **NOT ADOPTED** — replacing the floor changes how filed results read,
      which is Arpit's call. Two filed uplifts are named and re-judged by
      nothing.

## P3 — §3.0, the sanitized-sha stability measurement (moved from W-82, 2026-08-27)

> ### ✅ RAN 2026-08-27 — `PASS`, 19/19 = 100 %
>
> [VERDICT](../regression/2026-08-27-p3-sha-stability/VERDICT.md) ·
> [report](../regression/2026-08-27-p3-sha-stability/report.md)
>
> **Against a frozen `≥ 80 %`, so fork 3 CLEARS its gate and P4 is unblocked.**
> The corpus was 19 real external documentation URLs — RFCs, PEPs,
> `docs.python.org`, Wikipedia, a live status page — in a new lab environment.
>
> - **A control arm was run**, because a 100 % with none is the M1 failure: a
>   treatment that touched nothing, reported as a null effect. Two volatile URLs
>   were added and `Special:Random` changed while the 19 did not. **The
>   instrument detects change.**
> - ⚠ **CLEARED IS NOT DECIDED.** Fork 3 is Arpit's, and ADR-FETCHER decision
>   3's argument against anything that composes is untouched by this number.
> - ⚠ **The spec named no INTERVAL** and the runs are **12 seconds** apart. That
>   measures **server-side determinism** — do timestamps, ad slots, CSRF tokens
>   or session ids break the sha for an unchanged document? **None of 19 real
>   pages did.** It does **not** measure document churn over a sweep interval,
>   which is the other half of what `validate` is worth and needs a **new**
>   pre-registration with an interval in it.
> - ⚠ **`informed`**, as this spec anticipated, and **ADR-RS decision 12's
>   reopen trigger has FIRED** — its disclosure has now been written four times.
>   Recorded in the run's `ANALYSIS.md` §3 and **not acted on**: decision 12 is
>   Arpit's and its own text forbids a session narrowing it.

**No new code.** Run `fux update` twice against a real URL corpus; count the
fraction of fetched documents whose **sanitized** sha was unchanged.

| result | consequence |
|---|---|
| **≥ 80 %** | fork 3 is **yes** — the contract gains an optional `validate` |
| **≤ ~40 %** | the contract stays at four functions |
| between | **ambiguous → Arpit, unadjudicated** |

- ⚠ **The threshold is already frozen and may never move.** This is why P3 does
  not wait on P0.
- ⚠ **Classification is `informed`** — whoever runs it will have read the spec.
  That is the correct label, not a reason to delay.
- ⚠ **It collides with ADR-RS decision 12**, which is a cost measurement made
  entirely of deltas. Ruled 2026-08-27: **disclose the conflict in the report;
  do not self-exempt, and do not narrow decision 12 to let it through.**

## P4 — forks 3 & 4 (moved from W-82 §5.1, 2026-08-27)

> **🔓 UNBLOCKED 2026-08-27.** P3 returned **100 %** against a frozen `≥ 80 %`.
> The gate is the only thing that was in the way; **both forks are now
> decidable, and neither is decided.**

- [x] ✅ **Fork 3 — BUILT 2026-08-28.** `validate(url) -> str | None`, optional,
      with the shipped `http.py` implementing it (a `HEAD` for `ETag`, falling
      back to `Last-Modified`). **Verified live: 3 of 7 real URLs skipped their
      body fetch**, while `Special:Random` — whose token rotates every request —
      is re-fetched every run, which is the invariant working.
      ⚠ **It reaches existing repos only when they copy the fetcher in**:
      `fux setup` is write-if-missing. Measured — a repo made before the change
      learned **0 of 7** tokens until its `http.py` was replaced by hand.
      ADR-FETCHER decision 12. *(Original gate note: cleared ([P3](../regression/2026-08-27-p3-sha-stability/VERDICT.md)).
      ⚠ **Still Arpit's**, and the number does not answer it: the case against is
      that four functions survived two callers untouched, and ADR-FETCHER
      decision 3's refusal of anything that composes is independent of P3.
      **The design is fully worked out** in
      [W-82 §5.1](W-82-the-consolidated-build.md#51--url-freshness--8-forks),
      including the one invariant an implementer must carry: **a changed token
      must NEVER mean a changed record** — token unchanged → skip the fetch, and
      that is *all* `validate` may do; token changed → fetch, then **still**
      compare the sanitized sha. Otherwise a chatty `ETag` churns shards and
      byte-determinism is gone.
- [x] ✅ **Fork 4 — BUILT 2026-08-28.** `token_sha` in
      `.fux/runtime/url-state.json`: **`sha256(token)`, never the token**, so L5
      is untouched by construction. Counters, no clocks — a token is an opaque
      equality witness even when a server built it from a timestamp.
      🔴 **It was declared, written and NOT read back for its first hour**, so
      `validate()` matched nothing while every test passed —
      `state.schema.json`'s own header predicts that failure in as many words.
      Now gated by a round-trip test that walks the *declared* shape.
      ADR-MAINTENANCE decision 13.

## P5 — `tests_e2e/` verification (moved from W-82, 2026-08-27)

### ✅ DONE — 2026-08-27, on Python 3.11.15 with an editable install

**`74 passed, 0 failed, 0 skipped`**, repeated four times. The unit suite is
`1085 passed` beside it, and the two together are `1159 passed / 2 skipped`.

⚠ **W-82's premise was wrong, and the wrongness mattered.** It recorded
*"it fails identically (55/11) on a clean tree, so there is no regression."*
The first run on a real 3.11 install returned **64/8** — three tests that had
been written off as environmental were passing, and of the eight that were
not, **one was a live crash in shipped code**. *"Fails identically"* was
measured on an environment too broken to distinguish a defect from a shim.

**What the eight actually were:**

| failure | verdict |
|---|---|
| `test_add_of_a_file_does_not_override_the_type_allowlist` | 🔴 **real defect in `run.py`** — see below |
| `test_machine_data_beside_a_document_is_not_indexed` | stale — asserted `.json` was not indexed, reversed by Arpit's 2026-08-26 ruling |
| `test_setup_writes_the_types_file_with_the_default_spelled_out` | stale — asserted a `No .json` sentence the template correctly stopped writing |
| `test_doctor_reports_a_stale_lock_without_clearing_it` | stale — wrote `runner.lock`, renamed to `write.lock` by W-86 P6 |
| 4 × `test_maintenance.py` hook tests | environmental — the hook is `command -v fux || exit 0`, and no console script was installed |

⚠ **Three of those four stale tests were passing their own fabricated premise
back to themselves.** The stale-lock one wrote a filename nothing reads, then
asserted `doctor` reported a stale lock — it did not, and had not since the
rename. A test that fabricates its input can go green on a dead surface.

### 🔴 The defect P5 found: one unreadable document ended the entire ingest

`run()`'s record loop iterated **every walked file** and reached
`file_shas[doc_id]` for a document the parse plane had already dropped:

    KeyError: 'file:docs/architecture.pdf'   # run.py:319

`file_shas`, `extracted` and `scans` are all narrowed to `parsed`. The record
loop was the fourth collection and it was not. **This is the precise failure
W-86 P6's drop-rather-than-raise was built to prevent** — one `%PDF` header
nothing can decode takes down a 10 000-document run — and it was reachable
from a plain `fux ingest`, not just from `add`.

⚠ **It became reachable on 2026-08-26**, when `.pdf` joined `DEFAULT_TYPES`.
Before that the walker rejected it by type and the loop never saw it. **A
widened allowlist and an un-narrowed loop were each harmless alone.**

- [x] Fixed: `if doc_id not in parsed: continue`, so the document is queued
      rather than recorded, and the run completes.
- [x] Gated in the **unit** suite —
      [`tests/ingest/test_unreadable_document.py`](../../tests/ingest/test_unreadable_document.py),
      5 tests, all five verified red against the pre-fix loop. The invariant
      test asserts the four collections agree, not the symptom, so widening
      the walker to another undecodable type cannot silently reopen it.
- [x] Gated in `tests_e2e/` too, as
      `test_an_added_file_that_no_decoder_can_read_is_queued_not_fatal` — the
      crash was only ever visible through the shipped command.

### A flake, found by repetition rather than by one run

`test_the_post_commit_hook_reindexes_after_a_commit` **raced from 2026-08-22
until 2026-08-27**. It read the index on the line after the commit, which was
sound while `post-commit` re-indexed inline; when the fork resolved to option B
the hook became `fux ingest --spawn-runner` and the read started outrunning a
detached process. It failed **about one run in three** here and passes on a
fast machine. Now waits via `_drain`, like every sibling test.

⚠ **It now overlaps `test_post_commit_defers_and_a_detached_runner_drains_the_list`
almost exactly** — same corpus, same commit, same assertion. Flagged in the
docstring, not deleted: which survives is a call about what the suite should
say.

### What running the suite found next

⚠ **P5's real value was not the 74/74.** Running the FULL unit suite in an
environment that could run it surfaced a second live defect, in a different
plane: **`fux daemon`'s sweep never reached the ingest**, in any repository,
because `from ..ingest import run` binds the re-exported function and the
broad `except Exception` turned the resulting `AttributeError` into a silent
`"failed"` forever. Written up under
[W-82 ruling 3](W-82-rulings-2026-08-27.md), which is the ruling being **held**
on *"prove the daemon runs in a real repo"* — **the hold was right.**

### What P5 does NOT establish

- ⚠ **One platform, one Python.** Linux, CPython 3.11.15. macOS and Windows
      are unverified, and `test_maintenance.py` is the suite most likely to
      differ — it drives real git, real hooks and real detached processes.
- ⚠ **The four hook tests need `fux` on `PATH`.** They pass only against an
      editable install; with none they go green-by-vacuity, because the hook's
      first line is `command -v fux >/dev/null 2>&1 || exit 0`. **A CI job that
      forgets the install proves nothing and says nothing.** That is worth a
      guard of its own and does not have one.

---

## Definition of done

- [x] Six forks ruled, recorded in the compare doc's verdict block **and in
      [ADR-QUALITY](../../docs/adr/0044_quality-contract.md)** — 2026-08-27.
- [x] A versioned [`mix.toml`](../../tools/quality/mix.toml) exists, frozen the
      way a pre-registration is frozen. ⚠ *"every report prints its version"* is
      **owed by the first report**, not by this file — no harness reads it yet.
- [x] The cost weights are committed **before** the first score under them.
      `t = 0.75` → `c = 2`, frozen 2026-08-27 with `recall@k` still uncomputed —
      which is exactly the ordering the rule demands.
- [ ] `recall@k` is computed and is the reported headline.
- [ ] The `judged` series, if ruled in, pins **model + prompt + version** and is
      never compared across judge versions.
- [ ] ADR-RS amended to own the quality contract, or a new record written for it.

## References

- **The verdict:** [`work/compare/what-good-means.compare.md`](../compare/what-good-means.compare.md)
- **The parent:** [W-82](W-82-the-consolidated-build.md) §5.2 — now a pointer here
- **The rule it extends:** [ADR-RS](../../docs/adr/0036_predictions.md)
- **The two caught failures:** [P1-GATE](../regression/2026-08-09-pruning-eval/VERDICT.md) ·
  [budget sweep](../regression/2026-08-22-budget-sweep/ANALYSIS.md)
