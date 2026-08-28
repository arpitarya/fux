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

**Split from [W-82](../../archive/open/W-82-the-consolidated-build.md) §5.2 on 2026-08-27**
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
| ~~**P1**~~ | the measurement apparatus — sealed subset, decoy set, content-free placebo, ~~orphaned-module check~~ | ✅ **ALL BUILT, and three of four now USED to adjudicate** (decoys 2026-08-27; `unanswerable` and placebo 2026-08-28). 🔴 **The sealed subset is EXERCISED, NOT PROVEN** — it postdates the enrichment it was applied to, so its split cannot test contamination; that is a *chronology* limit, not an unbuilt apparatus, and it is tracked in ADR-RS decision 15 rather than here |
| **P2** | the quality runs — `recall@k`, the funnel, the cost-weighted curve | 🔴 **`recall@k` is BLOCKED ON AN ADR, not on inputs** — two blind annotators (κ = 0.96) measured the goldens' relevance sets **incomplete**, so the metric is not computable until the schema decision lands. **Part B needs corpora that no longer exist.** See §P2 below |
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

- [x] ✅ **The sealed query subset** — BUILT 2026-08-28,
      [`seal.py`](../../tools/quality-controls/seal.py), 15 of 50 split by
      `sha256(id)`: deterministic, seedless, order-independent. The power
      tension is answered in writing (Arpit: seal 15, grow the set later).
      A sealed holdout is what FrontierMath actually used; disclosure alone is
      the fallback, and BIG-bench's canary is the counter-example.
      🔴 **EXERCISED 2026-08-28, and it CANNOT adjudicate yet** —
      [the run](../regression/2026-08-28-placebo-and-seal/report.md). The seal
      **postdates by four days** the enrichment it was applied to, whose author
      saw all fifty queries, so its "sealed" 15 were never hidden from anyone.
      **A post-hoc split of a fully-seen set cannot test contamination.** Its
      first adjudicating use needs an artifact authored *after* the seal
      existed, by an author given the visible 35 only. Tracked in ADR-RS
      decision 15, not here.
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

- [ ] **`recall@k` — the blocker was mis-stated, and it is smaller than it
      reads.** ⚠ **CORRECTED 2026-08-28 (Claude Code, ran the audit):** the
      earlier belief that the golden schema carries a multi-document `expect`
      list — `expect: [{"id": ..., "max_rank": ...}, ...]` — was itself wrong.
      That key is `tools/differential/playground_grade.py`'s docstring, which
      had drifted from the real consumer; `fux-playground/goldens/queries.jsonl`
      has never had an `expect` field. **The real schema is one scalar `doc` +
      `max_rank` per golden** — confirmed against `fux-playground/check.py`.
      There is no missing annotation *format*, and there never was, but not
      because a list degenerated to size 1 — because there is no list at all.
      🔴 **What is genuinely missing is COMPLETENESS, not annotation.** `doc` +
      `max_rank` is a **rank contract** — *"this document must come back at
      rank ≤ n"* — and it has never promised *"this is every relevant
      document."* A document a golden doesn't name may be irrelevant, or may
      just be one nobody asserted. `recall@k` needs the second reading, the
      schema only ever supplied the first.
      - [x] **Run the audit** (Arpit, 2026-08-28 — *"check first, then
            decide"*): `python3 tools/quality-controls/relevance_audit.py
            ~/my_programs/fux-playground`. ✅ **Done 2026-08-28 (Claude Code,
            local shell reaches the playground).** First run was vacuous — it
            read the nonexistent `expect` key and reported "0 asserted" for
            all 50, which looked like a finding and wasn't. Fixed the script's
            schema to match `doc`/`max_rank`, re-ran: **all 50 goldens assert
            exactly one `doc`, none unasserted, 9 `known_failure`.**
      - [x] ~~**Every golden asserts one document, so `recall@k` IS `hit@k`**~~
            🔴 **WITHDRAWN 2026-08-28, same day, by
            [the blind run](../regression/2026-08-28-blind-unanswerable/report.md).**
            The field count was right about the file's *shape* and wrong about
            the corpus. A **blind annotator** — fresh session, corpus plus a
            stripped query list, no scores — judged **25 of 50** questions to
            have more than one genuinely relevant document (22 with two, 3 with
            three), against **one asserted for all 50**.
            **So `recall@k` ≠ `hit@k` on this corpus, and is not computable
            from the current goldens.** The audit script said as much in its own
            output: *"completeness is a human judgment about documents, and no
            count can substitute for it."* It was treated as nearly settled
            anyway, for a few hours, on a count.
            ⚠ **No filed number is invalidated.** Past runs measured *"did the
            asserted document come back"* — that is `hit@k`, reported as
            `hit@k`. What changes is that it **may not be called `recall@k`**.
            - [x] ✅ **A second blind annotator RAN 2026-08-28** —
                  [the agreement run](../regression/2026-08-28-annotator-agreement/report.md).
                  A different fresh session, denied the goldens, the scores,
                  `fux`, **and the first annotator's answers**, judged 26 of 50
                  multi-document. **Cohen's κ = 0.960**; 49/50 agreement on the
                  multi/single call; **both name the same 25**. Annotator 1 was
                  also caught omitting the golden's own asserted doc on `q027`,
                  which is what a second reader is for.
                  **The one-document assumption is refuted by measurement.**
            - [x] ✅ **THE SCHEMA DECISION — RULED 2026-08-28 (Arpit): option
                  B.** The rank contract and the relevance set become **two
                  fields**, because the defect is conceptual and making the
                  existing field plural would have carried the conflation
                  forward. Recorded as
                  [ADR-QUALITY](../../docs/adr/0044_quality-contract.md)
                  **decision 12**, with four rules: a declaration is required
                  with any relevance set; `recall@k` is computable only over
                  `complete` queries; `doc` must appear in `relevant`; and both
                  fields are optional so nothing historical breaks.
                  **Built in the same change** —
                  [`tools/quality/goldens.py`](../../tools/quality/goldens.py)
                  validates it, +12 tests, and the un-migrated playground file
                  stays valid (reporting `recall@k` as *not computable*, which
                  is the honest answer).
            - [ ] **Migrate `fux-playground/goldens/queries.jsonl`.** The
                  migrated set is built and validated — **43 `complete`, 7
                  `partial`, 26 multi-document** — and is filed as
                  [evidence](../regression/2026-08-28-annotator-agreement/evidence/queries-migrated-decision-12.jsonl)
                  plus placed uncommitted in the playground as
                  `goldens/queries.decision12.jsonl`.
                  ⚠ **Deliberately NOT overwriting `queries.jsonl`** — that is a
                  sibling repo with its own uncommitted work, and swapping the
                  file every measurement is graded against is a human's call.
                  **The 7 `partial` rows are where the two annotators' exact
                  sets differed**; they take the union and are excluded from
                  `recall@k` rather than being adjudicated by an agent.
- [ ] **The `unanswerable` class does not exist** and must be authored **blind**,
      or it contaminates the set it is meant to test (the W-78 lesson).
      ✅ **UNBLOCKED 2026-08-28 (Arpit): a fresh session, corpus only, with the
      prompt committed** — [`tools/quality-controls/BLIND-AUTHOR-BRIEF.md`](../../tools/quality-controls/BLIND-AUTHOR-BRIEF.md).
      ADR-RS decision 11's test is *no access to the queries, judgments or prior
      scores*; it does not require a human, and a fresh session given only the
      corpus satisfies it literally.
      🔴 **The leak channel is the PROMPT, and the prompt's author is not
      blind.** The brief was written by a session that had read the goldens, the
      decoys, the `known_failure` list and four runs of scores — so the
      mitigation is **publication, not trust**: it is committed, short, and
      checkable for the three things it must not contain (an example question, a
      difficulty steer, any topic list). ⚠ **This makes the claim checkable, not
      true by fiat** — the same limit `seal.py` has.
      ⚠ **The 15 decoys are still NOT this class**, and the reason is now
      recorded properly: not merely *"an agent wrote them"* but that **an
      informed author fits the DIFFICULTY DISTRIBUTION even with no correct
      answer to fit to.** The decoy set drifted generic — parental leave, badge
      systems, invoice disputes — which is that effect, visible.
      - [x] ✅ **RUN 2026-08-28** —
            [the run](../regression/2026-08-28-blind-unanswerable/report.md),
            classified `blind`. A fresh session with the corpus and the brief
            and nothing else wrote 20 questions; a **second, independent** fresh
            session ruled all 20 genuinely unanswerable, none at low confidence.
            **The class now exists.**
            🔴 **And it found the thing controls exist to find: the engine
            reported `answerable: true` on 20 of 20** — 6 `grounded`, 13
            `partial`, 1 `weak`, with 17 of 20 at or above the
            `separation_floor` (median separation `0.448`). **Zero abstentions
            on a purpose-built abstention test.**
            ⚠ **The brief's validation loop is WRONG and was not followed as
            written.** It grades a submitted question by the engine's own
            `answerable`, so a `DROP` was meant to mean *"the corpus answers
            it."* **That is circular** — it uses the system under test as the
            arbiter of the test's own validity, and would have thrown away all
            20 good questions as defective. Ground truth came from the second
            blind session reading the corpus instead. **The drop count the
            brief demands is therefore 0, not 20**, and the brief needs
            amending before anyone runs it again.
            ⚠ **No threshold proposed, R10 untouched** — a floor fitted to the
            20 numbers that exposed the problem would be the moving-threshold
            failure in a new costume.
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
      [ADR-FETCHER](../../docs/adr/0019_fetcher.md) decision 12 — the design and the
      invariant, moved to a live record when W-82 archived, because an archived
      file may be named and never cited —
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
[W-82 ruling 3](../../archive/open/W-82-rulings-2026-08-27.md), which is the ruling being **held**
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
- [ ] **`recall@k` is computed and is the reported headline.** ✅ **The schema
      blocker is GONE — ruled option B, 2026-08-28** ([ADR-QUALITY](../../docs/adr/0044_quality-contract.md)
      decision 12), built and validated, with the migrated 50-query set filed
      (**43 `complete`**, so recall is computable over 43/50 the moment it
      lands). **What remains is two mechanical steps, neither a decision:**
      ① the playground's `queries.jsonl` is swapped for the migrated file —
      a human's call in a sibling repo, not an agent's; ② a harness computes
      the number and reports it **with the 43/50 fraction beside it**, which
      decision 12 rule b requires.
- [ ] **The `judged` series pins model + prompt + version** and is never
      compared across judge versions. ⚠ **It IS ruled in** — fork 4, and
      [ADR-QUALITY](../../docs/adr/0044_quality-contract.md) decision 9 governs
      it — so this is not conditional any more. **No judged run has happened**,
      so the pinning has never been exercised.
- [x] ✅ **A record owns the quality contract** —
      [ADR-QUALITY](../../docs/adr/0044_quality-contract.md), written 2026-08-27
      rather than amending ADR-RS. Its components are claimed in the ownership
      table (`tools/quality/`).

## References

- **The verdict:** [`work/compare/what-good-means.compare.md`](../compare/what-good-means.compare.md)
- **The parent:** [W-82](../../archive/open/W-82-the-consolidated-build.md) §5.2 — now a pointer here
- **The rule it extends:** [ADR-RS](../../docs/adr/0036_predictions.md)
- **The two caught failures:** [P1-GATE](../regression/2026-08-09-pruning-eval/VERDICT.md) ·
  [budget sweep](../regression/2026-08-22-budget-sweep/ANALYSIS.md)
