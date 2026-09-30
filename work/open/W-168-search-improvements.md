---
type: Handoff
name: W-168
description: "The ten ranking improvements of proposals/search-improvements-v3.md, promoted as one program with ten gated steps: anchor text, corpus-mined expansion, unstemmed identifier field, RM3, supersession-aware ranking, SDM proximity, MMR diversification, git authority prior, intent → doc-type prior, section-level units. Each step is its own golden question → pre-registration → build → measure → keep/remove; never two in one arm."
item: W-168
filed: 2026-09-14
ball: arpit
---

## ✅ STEP 10 RE-RULED U2 → W-236 · STEP 5 RULED R1 · G3 → W-237 — 2026-09-29 (Arpit, Cowork) · ratified, NOT built

- **Step 10: U2 · B2 · E1** ([`compare/section-units`](../compare/section-units.compare.md)). Arpit, on voice: *"I want to go with U1"*. That was the voice session's name for section records, and he confirmed **U2** in the doc's lettering. It supersedes U0 (2026-09-27): a query-time re-rank cannot reach a long document that never became a candidate.
  - **Still stopped:** the pool is 1, against a floor of 6. U2 is what a qualifying set builds, and the doc lists what the plane change owes (an SR, a format bump, a size measurement, Opus).
- **Step 5 (RM3):** [`compare/rm3-selective`](../compare/rm3-selective.compare.md), at Arpit's ask (*"selective expansion rather than every time"*), recommendation first and his ruling after.
  - **Recommends R0, stay removed.** Post hoc on both filed runs, no band gate clears the drift clause. The best nets +4 tagged, where 7–10 were needed.
  - Selective expansion is recorded as the only form RM3 may return in.
  - ✅ **Ruled R0 the same day (Arpit):** RM3 stays removed and SR-EXPAND d17 is unchanged. Step 5 stays failed.
- ✅ **Re-ruled 11:25 (Arpit):** R1 · G3 supersedes R0. RM3 returns, expanding only on a `grounded` first pass. **Filed as [W-237](W-237-rm3-grounded-gate.md).**
- **Step 10 filed as [W-236](W-236-section-records.md)** (Arpit's ask): the design record and a size measurement now, then the build once a pool of 6 or more exists.
- **Unchanged:** step 8 is still the next build.

## ✅ STEPS 1 + 4 MEASURED TOGETHER — 2026-09-28 (Claude Code, Opus; a non-capturing session), W-232 PASS

[Verdict](../regression/2026-09-28-anchor-mined-set3/VERDICT.md). The shipped pair `anchor = 1.0` + `mined_weight = 0.5` beats mined-off 6/0 and anchor-off 7/0 at rank 1 on `set-3-claude`, with **0 losses**. All six wins over mined-off are step 4's tagged questions, which is its own 6/0 reproduced at `anchor = 1.0`. **Both steps' *combination unmeasured* warnings below are closed.** `informed`.

## ✅ STEP 8 BUILT AND CAPTURED — 2026-09-30 (Claude Code, Opus)

- **Built per the frozen bar**, off at `authority_weight = 0.0`, in both readers: `authors` and `commits` on each git-sourced `M/` record from the one `git log` walk (counts only; no name or email is written), the multiplicative prior, the accelerator bound `1 + w`, `fux lexical` forced off, `--why` `authority`. `tests/query/test_authority_prior.py` (80).
- ⚠ **Index format `fux.index.v6` / runtime `fux.runtime.v8`**, by SR-INDEX-LIFECYCLE d9.1 (a new record property bumps `_format`; step 4's `abbr` is the precedent). The pre-registration did not decide it. Every v5 index needs `fux ingest --full`, even with the key off.
- **Captured** `au-0.0 … au-0.5`: [report](../regression/2026-09-28-authority-prior/report.md). The precondition holds: `au-0.0` = `ip-0.1` on 125/125. Rank 1 moves on 0 / 7 / 12 / 17 / 29 questions.
- **Next:** 🔴 Arpit scores; then a session that did not capture writes `decide.py` from step 9's and applies the table.

## ✅ L11 13b LANDED · STEP 7 STOPS · STEP 8 RULED AND PRE-REGISTERED — 2026-09-28 (Claude Code, Opus)

- **Order (1) done.** [L11](../../records/0013_LAW-11-sealed-answer-key.md) **13b**, `score.py` and `tests/test_golden_score_output.py` landed in one change. `facets_top5` and `facets_key` are counts per question. 13b names both door-4 routes: per-row R8 tag membership, and relevant-document narrowing against `ranked`.
- ⏸ **Step 7 STOPS before build, key-free.** [Report](../regression/2026-09-28-mmr-trigger/report.md): on the `ip-0.1` hand-off, the swap's trigger (top 5 in one community) fires on **7 of 125** questions. Only **5** have another community in ranks 6–10.
  - **Arpit ruled the candidate depth** in this session: *"Ranks 6–10 → STOP"*. The swap only reorders what the user already receives, so the ceiling is 5, below 6.
  - **Cause:** 774 of 1 000 documents have no edge and are each their own community, so 81 of 125 top-5 lists already span five communities.
  - **Reopens on** a denser graph, or option C (a similarity measure, its own key and sweep). The facet column stays for that.
- ✅ **Step 8: compare doc filed and ruled.** [`compare/authority-prior`](../compare/authority-prior.compare.md). **Arpit, in this session:** *"Rule A3 · S2 · L1"*: authors × commits; `f = 1 − 1/(a·c)` with no extra key; two ints on `M/` from the existing `git log` walk. It was argued against SR-TUNE d15's two reasons for removing document priors.
- ✅ **Step 8 pre-registered.** [The frozen bar](../regression/2026-09-28-authority-prior/PRE-REGISTRATION.md).
  - **Arms:** `authority_weight ∈ {0.1, 0.2, 0.3, 0.5}` vs `0.0`, on a **re-ingested** copy of rung-01000 with the step-9 arm's tune.
  - **Tag:** the key-free `authority_reach` tag covers **101 of 125** (pool 31; the key's pool is 8). The 12 multi-commit documents are seed documents in most top-10 lists, so **59 held rank-1 hits can only lose**, and the set-wide zero-loss clause is the real gate.
- **Next: build step 8** (**Opus**), off at `0.0` and byte-identical there, in both readers, with the accelerator bound. Then capture the five arms on the copy. Then 🔴 Arpit scores, and a session that did not capture decides.
- **W-228's timing** ("after steps 6–10"): only step 8 is left.

## ✅ STEPS 7 AND 8 ENDPOINTS RULED — 2026-09-28 (Arpit, Cowork) · ratified, NOT built

**Arpit, 2026-09-28:** step 8 — *"go with the recommendation"*; step 7 — *"Okay, go with the recommendation"*, after asking what MMR is, why it touches only position 5, and why it computes no score.

- **Step 8 (authority prior):** judged at **`hit@1`, `primary@1` beside it**, as steps 1, 4 and 9 were. Pool of 8.
- **Step 7 (MMR) — design:** the **simple swap as proposed** (top 5 all in one community → swap #5 for the best document of the next community). **Not** classic scored MMR, and **not** option C (MMR over positions 2–5 with #1 pinned). Option C is reopened only if the simple swap passes but is judged too blunt; it would then need a similarity measure, a λ key in `tune.toml` (L12) and its own sweep.
- **Step 7 — a marker, not a score.** After a swap, #5 scores lower than the document it displaced, so the list is no longer score-sorted. The build adds a deterministic marker — `diversified: true`, the displaced document, the source community — in `ask --json`, `--why`, and the explorer's Ask tab (the W-229 parity test applies). No MMR number is invented.
- **Step 7 — measurement: amend [L11](../../records/0013_LAW-11-sealed-answer-key.md) d13** (a new **13b**) so `score.py` also emits, **per question id, two counts only**: *facets covered in the top 5* and *facets in the key*. No facet text, no document name. Arpit's ruling is this entry; the record is amended **in the same change as `score.py` and `tests/test_golden_score_output.py`**, never before — d13's own ⚠ about prose that claims a carve-out before the code has it.
  - ⚠ **Door 4:** a per-question *facets in the key* count is new per-row key-derived output. The 13b text must name it, as 13a named its `answerable`-per-tag route.
- **Step 7 — early stop, pre-registered:** the first scored output's *facets in the key* column gives the number of questions with ≥ 2 facets. **The step 7 bar must state, before any row, the minimum multi-facet pool that could clear the SR-RS d19 paired floor (net 6); below it, step 7 STOPs** with no build of the swap.
- **Order:** (1) L11 13b + `score.py` + its test — **Opus**; (2) step 8's compare doc (unchanged, agent-closable); (3) step 7 and step 8 pre-register, each its own bar. Scoring stays Arpit's hand.

## 🔴 STEPS 7 AND 8 BLOCKED ON THEIR ENDPOINTS — 2026-09-28 (Claude Code, Opus)

Nothing was pre-registered. Both questions are in `work/BLOCKED.json` and the inbox.

- **Step 7 (MMR) cannot use the pool of 8.** That pool is counted at rank 1, and MMR swaps position 5 only, so it cannot move `hit@1` by design.
- **Its ruled endpoint needs the key.** The 2026-09-23 ruling says *coverage in the top k, with `precision@1` unchanged*. The facets exist only in the key (prompt 11 Input 3). [L11](../../records/0013_LAW-11-sealed-answer-key.md) d13a lets `score.py` write per-tag pool counts and nothing per row.
  - A decider needs per-question coverage flips.
  - That output is a new entry on d13's allow-list, and a Law changes only on Arpit's ruling.
  - **Recommended:** amend d13 so the scorer also emits, per question id, *facets covered in the top 5* and *facets in the key*, as counts only. The alternative is to stop step 7.
- **Step 8 (authority) has no ruled endpoint.** The 2026-09-23 table predates the history corpus. Its pools were counted at rank 1 (pool 8) and rank 5 (pool 2).
  - **Recommended:** judge it at `hit@1` with `primary@1` beside it, as steps 1, 4 and 9 were.
- **Agent-closable meanwhile:** step 8's compare doc, covering the prior's form (authors × commits, log scaling, where the statistic lives in `M/`) and the recency trap. It needs no ruling to write.

## ✅ STEP 9 SHIPPED — 2026-09-28 (Claude Code, Opus); step 7 is next

- **`intent_weight = 0.1`** is the value in `src/fux/templates/tune.toml.txt`, which `fux setup` and `doctor --fix` write (L12: the template is the default's one home). The repo's own `.fux/tune.toml` matches it. **No reader code changed**: both planes read the key and hold no default of their own.
- `[doctype]` still ships empty, so nothing ranks differently on upgrade (the key is unreleased; `doctor --fix` writes `0.1`).
- **Records:** SR-TUNE 20 (default, MEASURED, reopen-trigger), SR-RANKING 13, SR-ASK 15, SR-NODE-SEARCH 22, SR-ANSWER, SR-PROVENANCE. Content and `owns:` hashes stamped. GLOSSARY and CHANGELOG updated.
- **Byte equality** is unchanged: no engine code moved. `test_intent_prior.py` still sweeps scan = accelerator = Node at `0.1` through `0.5`. The unit suite has 6 failures, all from other sessions' uncommitted work. e2e 152/152, Node 92/92.
- **Next:** step 7 (MMR, pool 8) pre-registers. **Opus.**

## ✅ STEP 9 DECIDED AND RATIFIED — 2026-09-28 (Claude Code, Opus; a non-capturing session); ship `intent_weight = 0.1`

[VERDICT](../regression/2026-09-28-intent-prior/VERDICT.md). The frozen
`decide.py` (sha `85298465…`, unchanged since `253f9c88`) read the five score
files and the frozen tags. It opened no key.

- **Tagged `hit@1` wins/losses:** 6/0 · 8/0 · 11/0 · 14/0 at `0.1 / 0.2 / 0.3 / 0.5`. Every value clears d19; **`0.1` is first, at exactly the floor** (net 6, p = 0.031).
- **Clause 2 holds everywhere:** no baseline rank-1 hit is lost at any weight, tagged or not. `hit@10` is 110 → 110.
- Every win is also a `primary@1` win. The wins are nested, and `0.5` wins the whole pool of 14. Headroom from the baseline arm is 14 / 66, as predicted.
- **Arpit ratified PASS at `0.1`** in this session.
- **Next:** ship per the bar's §If it passes, in one change: the `[ranking] intent_weight` default `0.1` on both engines (template and `constants`/tune reading), SR-RANKING, SR-TUNE, SR-ASK and SR-NODE-SEARCH amended, scan = accelerator = Node = bundle byte-identical, a CHANGELOG line. **Opus.** Then steps 7 and 8 pre-register.

## 🟢 STEP 9 SCORED — 2026-09-28 (Arpit's hand); the verdict is a NON-capturing session's

[Report §Scored](../regression/2026-09-28-intent-prior/report.md). Five complete
score files; set-wide `hit@1` 66 → 72 / 74 / 77 / 80 and `primary@1` 62 → 68 /
70 / 73 / 76 at `0.1 / 0.2 / 0.3 / 0.5`. **These totals are not the rule.**
Clauses 1–2 read tagged per-query flips, the SR-RS d19 floor, and zero baseline
rank-1 losses.
**Next:** a session that did not capture the arms runs
[`decide.py`](../regression/2026-09-28-intent-prior/evidence/decide.py) (sha
`85298465…`, written before the score) and files `VERDICT.md`. INCONCLUSIVE → Arpit.
This session wrote the bar, built step 9 and captured the arms, so it cannot.

## 🔴 STEP 9 ARMS CAPTURED — 2026-09-28 (Claude Code, Opus); the score is Arpit's, the verdict another session's

[Report](../regression/2026-09-28-intent-prior/report.md).

- **Five arms** `0.0 / 0.1 / 0.2 / 0.3 / 0.5` on one copy of rung-01000 (`b73348d5`), engine `a113b727` pinned in its own worktree. `doctor --fix` ran on the copy (10 tune keys, all template values), then the bar's three globs. No re-ingest.
- **`ip-0.0` equals the 2026-09-27 capture on 125/125 ranked lists and bands**, so the pool of 14 applies.
- **Rank 1 moves on 6 / 8 / 11 / 14 questions, all tagged.** No untagged ranking moved at all. These are changes, not improvements.
- **Written before any score:** [`evidence/decide.py`](../regression/2026-09-28-intent-prior/evidence/decide.py) (step 4's decider, arm names, set and tag reading changed) and `describe.py`.
- 🔴 **Next, in order:**
  1. Arpit runs `just golden-score work/regression/2026-09-28-intent-prior`. No unlock is needed.
  2. A session that did **not** capture the arms runs `evidence/decide.py`.
  3. An INCONCLUSIVE goes back to Arpit.

## ✅ STEP 9 BUILT — 2026-09-28 (Claude Code, Opus); the arms are next

The mechanism exactly as [the bar](../regression/2026-09-28-intent-prior/PRE-REGISTRATION.md)
fixes it, **off at `intent_weight = 0.0` with an empty `[doctype]`**. No treatment number exists.

- **Lexicon:** `constants.toml [intent]`, test-bound to the frozen tag. On set-4-claude, the engine's intents equal `tags-set-4-claude.jsonl`.
- **Prior:** inside `Weighting`, built per question; `maximum` = priority supremum × `(1 + w)`. `fux lexical` forces `0.0`.
- **`--why`:** `intent` {cue, type, weight} and per-document `intent_factor`, **absent when off**.
- **Both readers:** `node/src/query/intent.mjs`. ASCII-only case and whitespace, `.` over every character, globs over code points.
- **Proved** (`tests/query/test_intent_prior.py`): off never consults the lexicon; on scales exactly `1 + w`; scan = accelerator at 0.1/0.2/0.3/0.5, `[priority]` stacked; Node = Python.
- **Records:** SR-TUNE 20, SR-RANKING 13, SR-ASK 15, SR-NODE-SEARCH 22, SR-PROVENANCE, SR-CONSTANTS.
- **Next:** capture the five arms on a COPY of rung-01000 (`b73348d5`) at one engine commit. Run `doctor --fix` on the copy, then add the three globs. Then 🔴 Arpit scores, and a session that did not capture decides.

## ✅ STEP 9 PRE-REGISTERED — 2026-09-28 (Claude Code, Opus); the build is next

[The frozen bar](../regression/2026-09-28-intent-prior/PRE-REGISTRATION.md).
**Nothing is built and no treatment number exists.**

- **D2 · I1 · M1 · S1 as ruled:**
  - a query-time `[doctype]` glob table;
  - the 2026-09-24 cue lexicon, verbatim, test-bound to the tag;
  - `[ranking] intent_weight`, arms `{0.1, 0.2, 0.3, 0.5}` against `0.0`, first that clears.
- **The tag is the lexicon:** 25 questions (rationale 10 · reference 8 · procedure 7). **Pool 14**, equal to the key's `step9_intent` on both counts. No stop.
- ⚠ **`[priority]` is prefix-matched, not globbed**, so `[doctype]` needs a new matcher: whole-location, `*` crosses `/`, longest pattern wins.
- ⚠ The arm's three globs also type **15 `ext/` decoys `decision`**. They are left in.
- **Next:** build step 9 (**Opus**: a new tune table, a new ranking key and a lexicon in `constants.toml`, in both readers), off at `0.0` and byte-identical there. Then capture both arms at one commit on a copy of rung-01000. Then 🔴 Arpit scores, and a session that did not capture decides.

## ✅ STEP POOLS COUNTED FROM THE KEY — 2026-09-28 (Arpit re-scored; Claude Code, Opus); steps 6 and 10 stop

[Report §Step pools](../regression/2026-09-27-golden-set-4-rung-01000/report.md) · [scores](../regression/2026-09-27-golden-set-4-rung-01000/scores/single/rung-01000/set-4-claude.json) `pools`.

- **How:** text tags could not settle step 10: two rules gave 5 and 13. Arpit ruled *"Amend L11 d13"*, so [L11](../../records/0013_LAW-11-sealed-answer-key.md) decision 13a lets `score.py` count pools by the key's `exercises` tag, as counts only. He re-scored the same day.
- **Pools, tagged ∩ answerable ∩ miss@1 ∩ in the top ten** (`informed`):

  | step | tagged | pool @1 | pool @5 | |
  |---|---:|---:|---:|---|
  | 6 SDM | 20 | **3** | 1 | ⏸ **stops before build** |
  | 7 MMR | 15 | **8** | 2 | goes: owes a pre-registration |
  | 8 authority | 15 | **8** | 2 | goes: owes a pre-registration |
  | 9 intent | 25 | **14** | 1 | goes: forks already ruled D2 · I1 · M1 · S1 |
  | 10 section | 15 | **1** | 0 | ⏸ **stops**: U0 · B2 · E1 stay ruled, not built |

- ⚠ **The text cross-check was badly wrong**: it gave 6 → 15 and 10 → 5 or 13 ([`step-pools.txt`](../regression/2026-09-27-golden-set-4-rung-01000/evidence/step-pools.txt)). A key-free tag is not a pool.
- `_unrecognised` carries 11 questions, all of them unanswerable. Their tag is not recipe-shaped, and the guard counted them without echoing the tag. `other` carries 24 (pool 10).
- **Next, in order:**
  1. Step 9 pre-registers (the pool is largest and the forks are ruled). One mechanism per arm.
  2. Steps 7 and 8 each owe a compare doc or pre-registration.

## ✅ SET-4-CLAUDE CAPTURED 2026-09-27 AND SCORED 2026-09-28 (Arpit's hand); the pools are next

[Pre-registration](../regression/2026-09-27-golden-set-4-rung-01000/PRE-REGISTRATION.md) (`0ce0b845`, before any row) · [report](../regression/2026-09-27-golden-set-4-rung-01000/report.md).
This session is not W-227's, and it built no rung.

- **One arm, `rung-01000`, the rung's own engine `80495b44`**, with no
  re-ingest. **No `doctor --fix`:** the next-step line above was written for
  HEAD, whose W-225 stage 2 refuses the rung. Fixing it would have edited a
  frozen rung. The pin predates stage 2 and already carries step 4.
- **The shipped combination** (`anchor = 1.0`, `mined_weight = 0.5`) comes from
  the rung's own `tune.toml`, unedited. With one arm, this is a baseline, not a
  measurement of that combination.
- **125/125 rows** carry funnel gates, ten results, a `refer` answer and a
  `current` citation. None were declined. Bands: 69 `grounded` · 24 `partial` ·
  32 `weak` · 0 `none`.
- 🔴 **Next, in order:**
  1. ✅ ~~Arpit types `just golden-score …`~~, done 2026-09-28: n = 125, `hit@1` 66,
     `hit@5` 104, `hit@10` 110, `primary@1` 62, 0 abstentions, 11 answered that
     the key marks unanswerable, 95 evidence quoted. **`informed`.**
     [scores](../regression/2026-09-27-golden-set-4-rung-01000/scores/single/rung-01000/set-4-claude.json)
  2. Each step 6–10 counts its own pool from the score. **Below 6 stops that
     step.** Step 10 then pre-registers per U0 · B2 · E1.

## ✅ GENERATION-3 LADDER REBUILT — 2026-09-27 (Claude Code, Opus)

[Report](../regression/2026-09-27-ladder-gen3-rebuild/report.md) · [ANALYSIS](../regression/2026-09-27-ladder-gen3-rebuild/ANALYSIS.md).
This session had never read a question (A23), so it could do the rebuild.

- **All eight rungs were stale** (8/8 on `test_golden_ladder_seed`). All eight
  were rebuilt **from scratch** by the unmodified builder, because the seed
  history cannot be put under an existing rung. The history was replayed through
  `replay.py`. The build ran from a clean worktree at `80495b44`.
- **All 8/8 froze**: 68 seeds, headline sizes held, and every coverage count
  equals its declaration. History is on every rung: 12 documents, 34 commits,
  9 authors. `ref` edges stay at 82.
- **The generation-2 rungs are kept** at `fux-lab/corpora/golden-gen2/`, not
  deleted.
- ⚠ **HEAD's W-225 stage 2 refuses these rungs** until `fux doctor --fix` writes
  seven `tune.toml` keys. At `0cbbc44b` the index root is byte-identical, so the
  records stand.
- ⚠ The generator's banned-name list is still behind the seed. A hand search
  found no leak, only the shared surname `Sheikh` (821 `Imran Sheikh` decoys).
- **Next, in order:**
  1. A phase-5 run of `set-4-claude` on the new ladder: pre-register first, run
     `fux doctor --fix` on the rung, then capture `ask --why` + `answer`.
  2. 🔴 Arpit scores it.
  3. Each step 6–10 counts its own pool.

## ✅ STEP 4 SHIPPED at `mined_weight = 0.5` — 2026-09-27 (Claude Code, Opus), in `8d401423`

Shipped per §If it passes, in one change. A concurrent session committed the files as part of `8d401423`, byte-identical to the diff verified below.
- **Default:** `MINED_WEIGHT = 0.5` in `query/mined.py` and `query/mined.mjs`, read by `Tune` and the loader on both sides, plus the setup template's comment. A new test holds the two constants equal.
- **Tests:** the arms that meant "off" now pin `0.0`. A new test checks that the default, and `--no-tune`, give `0.5`. The Node reader is now also compared at the default.
- **Records:** SR-TUNE 19 + new 19a, SR-EXPAND 18, SR-ASK 14, SR-NODE-SEARCH 21, SR-INGEST 23, SR-INDEX-LIFECYCLE 15.
- **Verified on a clean worktree** (`ef7c6c62` + this diff only), because the main tree was mid-rebuild by another session:
  - unit tests: 5 716 passed; the only failures are the 8 known ladder-seed ones;
  - e2e: 151 passed;
  - Node: 88/88;
  - scan = accelerator: **22 144 comparisons byte-identical**;
  - Node = bundle = Python: **0 of 225 discordant**, at this repo's default of `0.5`.
- **CHANGELOG:** Unreleased/Added. The key never shipped at `0.0`, so **every** upgraded repo's ranking changes. `mined_weight = 0.0` is the way back.
- ⚠ Unmeasured, and ratified knowing it: the combination with `anchor = 1.0`. ✅ *Measured 2026-09-28 by W-232: [PASS](../regression/2026-09-28-anchor-mined-set3/VERDICT.md).*

## ✅ STEP 4 (ABBREVIATIONS) FILED PASS at `mined_weight = 0.5` — 2026-09-27 (Arpit, Cowork)

*"yes"*, when asked whether to ratify step 4 at `0.5`. [Verdict](../regression/2026-09-27-mined-expansion/VERDICT.md).
No confirmation arm at `anchor = 1.0`: the two ship together, and that
combination is unmeasured. ✅ *Measured 2026-09-28 by W-232: [PASS](../regression/2026-09-28-anchor-mined-set3/VERDICT.md).*

**Next, agent, in one change** (PRE-REGISTRATION §If it passes, as step 1 shipped):
- **Default:** `mined_weight = 0.5` in `tune.py` and `tune.mjs`, and in the setup template's comment.
- **Records:** SR-EXPAND 18 · SR-TUNE 19 · SR-INGEST · SR-INDEX-LIFECYCLE.
- **Byte equality:** scan = accelerator = Node = bundle at `0.5`.
- **CHANGELOG:** a `[ranking]` default change reaches every consumer that does not pin it in `tune.toml`.
- **Reopen-trigger:** a baseline rank-1 hit lost to a mined spelling, in any later run.

## 🔴 STEP 4 PASS BY THE TABLE at `mined_weight = 0.5` — 2026-09-27 (Claude Code, Opus); Arpit ratifies

[Verdict](../regression/2026-09-27-mined-expansion/VERDICT.md). Arpit scored the arms, and a session that did not capture them ran the frozen `decide.py`.

- `hit@1` on the 22 tagged questions, wins/losses: 2/0 · 4/0 · 5/0 · **6/0** at `0.1 · 0.2 · 0.3 · 0.5`. Only `0.5` reaches the floor of 6, with no margin.
- **No drift loss at any weight**, tagged or not. `hit@10` stays at 70 → 70. Headroom is 10 / 41, as predicted.
- ⚠ Five of the six wins are a relevant non-primary document reaching rank 1. `primary@1` moves only 1/0.
- ⚠ The arms ran at the rung's `anchor = 0.0`, but the engine ships `1.0`. The combination is unmeasured. ✅ *Measured 2026-09-28 by W-232: [PASS](../regression/2026-09-28-anchor-mined-set3/VERDICT.md).*
- 🔴 **Next:** Arpit ratifies, or asks for a confirmation arm at `anchor = 1.0`. On ratification, ship per the bar's §If it passes, in one change.

## 🔴 STEP 4 ARMS CAPTURED — 2026-09-27 (Claude Code, Opus); the score is Arpit's, the verdict another session's

[Report](../regression/2026-09-27-mined-expansion/report.md).

- **Five arms** `0.0 / 0.1 / 0.2 / 0.3 / 0.5`, on one re-ingested copy of
  `rung-01000` at `9cdde333`, at engine `f8b21bd5`. The re-ingest changed only
  `abbr`, on 8 records (9 pairs, as the bar predicted).
- **`mx-0.0` equals the 2026-09-24 capture on 80 of 80 rows**, so the pool of 10 applies.
- **Rank 1 moves on 2 / 5 / 6 / 7 questions, all tagged.** These are changes, not improvements.
- **Written before any score:** [`evidence/decide.py`](../regression/2026-09-27-mined-expansion/evidence/decide.py)
  (the W-221 decider, with only the arm names, set and tags changed) and `describe.py`.
- 🔴 **Next, in order:**
  1. Arpit runs `just golden-score work/regression/2026-09-27-mined-expansion`.
  2. A session that did **not** capture the arms runs `evidence/decide.py`.
  3. An INCONCLUSIVE goes back to Arpit.
- ⚠ **This session also read `questions/set-3-claude.jsonl`** through the harness,
  so the prompt-4 rebuild still needs a different session.

## ✅ STEP 4 BUILT — 2026-09-27 (Claude Code, Opus)

The mechanism exactly as [the bar](../regression/2026-09-27-mined-expansion/PRE-REGISTRATION.md)
fixes it, **off at `mined_weight = 0.0`**. No treatment number exists.

- **Mine:** `query/mined.py::mine`, the tag's regex (held equal by a test),
  over the redacted parsed body. On rung-01000's seed it finds the same 9 pairs
  whole-file mining finds.
- **Commit:** `abbr` on the declaring record, hashes, sorted, omitted when
  empty, carried → **`fux.index.v5`**. This repo re-ingested: full = delta =
  full, one hash.
- **Fold:** at read time, over the user's hashes, both directions; the table
  from the shards on the scan, from `mined.json` (`fux.runtime.v7`) on the
  accelerator. Stacks on `--expand` (`expand.stack`); `lexical` never folds.
- **Both readers:** Node twin in `mined.mjs`, `expand.stack`, `tune.minedWeight`.
- **Proved:** `0.0` never opens the table; scan = accelerator at 0.1/0.2/0.3/0.5
  (fixture) and at 0.3 on this repo (8 folding queries, 0 differ); Node = Python
  on `ask` and `lexical` at `0.0` and `0.3`. Both suites green except the 8
  ladder-seed failures, which wait on the gen-3 rebuild.
- **Records:** SR-EXPAND 18 (and d1 narrowed), SR-TUNE 19, SR-INDEX-LIFECYCLE
  15/15a, SR-RECORD, SR-INGEST 23, SR-T1-ACCELERATOR 16, and the rest the gate
  named.
- ⚠ **This engine refuses the v4 ladder rungs.** They were already stale for
  gen 3; the prompt-4 rebuild will write v5.
- **Next:** capture the five arms on a re-ingested COPY of rung-01000 at
  `9cdde333`, at one engine commit. Then 🔴 Arpit scores; a session that did
  not capture decides.

## ✅ STEP 4 PRE-REGISTERED — 2026-09-27 (Claude Code, Opus)

[The frozen bar](../regression/2026-09-27-mined-expansion/PRE-REGISTRATION.md).
**Nothing is built and no treatment number exists.**

- **One family:** `Long Form (ABBR)` pairs, mined per document at ingest, stored
  as hashes on the declaring document's own record, folded at read time. It is
  scored through `expand.build` at a new `[ranking] mined_weight` (default
  `0.0`); the arms are `{0.1, 0.2, 0.3, 0.5}`, first that clears.
- **Glossary lines and `aliases:` are NOT in the arm.** All 22 tagged questions
  already carry a `Term (ABBR)` form. A glossary line gives a definition, not a
  synonym. `aliases:` has no tagged question.
- **Tag `expansion_form`:** step_pools' rule, restricted to rung-01000's
  manifest seed, checked by hash. 22 of 80, the ruled count.
- **Pool 10 ≥ 6: no stop.** Drift exposure 41 rank-1 hits; one loss fails a value.
- ⚠ **A `_format` bump**, so the arms run on a re-ingested COPY of rung-01000
  (`9cdde333`), never the rung itself.
- **Next:** build step 4 (**Opus**: a record-shape change in both readers and
  the accelerator). Then capture both arms at one commit. Then Arpit scores.
- ⚠ **The rung rebuild needs a DIFFERENT session.** This one opened
  `work/golden/questions/` (for W-224's byte-identity replay and for the tag),
  which SR-WORK-TESTDATA A23 forbids.

## ✅ PROMPT 11 RUN — 2026-09-27 (Arpit's hand); generation 3 is in the tree

- A designated claude.ai chat authored generation 3. Blocks 1–4 are in the tree:
  - 26 new seed documents;
  - `seed-dates.tsv` rows;
  - `seed-history.tsv` (34 lines) and `seed-history/` revisions;
  - `questions/set-4-claude.jsonl`, 125 rows of `{id, question}`.
- Block 5, the key, is Arpit's alone. This session did not look for it.
- **Next, in order:**
  1. A **rung-rebuild** session ([golden README](../golden/README.md) phase 4) rebuilds the eight rungs, which replays the history through `replay.py`.
  2. **A phase-5 run** (golden README) runs `set-4-claude`.
  3. 🔴 Arpit scores it.
  4. Each step 6–10 counts its own pool; below 6 stops that step.
- Step 4 does not wait on any of this.

## ✅ RULED 2026-09-27 (Arpit, Cowork) — step 10's forks U0 · B2 · E1; step 5 FAIL again, and RM3 is removed

- **Step 10:** *"W168 go with the recommendation"* →
  [`section-units`](../compare/section-units.compare.md) **U0 · B2 · E1**:
  - a best-section term inside the existing rerank stage, with no index change;
  - `[ranking] section_weight`, default `0.0`;
  - judged on `hit@1` over the `step10_section` pool, with `section@1` beside it.

  Its pre-registration still waits on generation-3 data (prompt 11, then the
  rebuild and a scored `set-4-claude`). A pool below 6 stops it.
- **Step 5:** the W-221 re-run on the boosted first pass is filed **FAIL
  (drift)**, the same as 2026-09-23. *"remove all the RM3 related code"* →
  W-224 (built 2026-09-27: [SR-EXPAND](../../records/0149_expand.md) decision 17). Step 5 stays in this
  list as a failed step.

## 🔴 STEPS 6–10 UNBLOCKED AS FAR AS AN AGENT CAN — 2026-09-25 (Claude Code, Opus); the rest is Arpit's hand

**Ruled by Arpit, 2026-09-25:**
- **A fresh, designated Claude session authors the next set.** It is not this
  session, which has read set-3-claude's ids and rank movements in step 1's verdict
  (prompt 3's freshness rule).
- **Step 8's history goes into the seed, and the ladder is rebuilt** — a new
  baseline.

**Done, agent side:**

| step | blocker | what was done |
|---|---|---|
| 6 SDM | no tagged input | prompt 11 Input 2 — two passages with the same words, one answering |
| 7 MMR | no tagged input; *graph in `ask`* | Input 3 — facet clusters with a crowded facet, `facets` in the key. ✅ **The graph dependency is already met**: `ask` runs `lexical → graph → split` today (SR-ASK) |
| 8 authority | no corpus with history | Input 4 — authority pairs with a recency trap. **The instrument:** [`tools/golden-history/replay.py`](../../tools/golden-history/replay.py) + `seed-history.tsv`, wired into the rung builder. With no history file the builder reproduces the old ladder: same authors, dates, messages and trees on a scratch `rung-seed` |
| 9 intent | pool below 6 | Input 1 — topic triples of `-procedure-` / `-decision-` / `-reference-` files, ≥ 25 cue questions (D2 · I1, as ruled) |
| 10 section units | owes a compare doc | [`compare/section-units`](../compare/section-units.compare.md) — **U0 · B2 · E1 recommended**; Input 5 — long documents with one-section answers |

**Next, in order:**
1. ✅ ~~**Arpit:** run prompt 11 in a new claude.ai chat, and commit blocks 1–4~~, done 2026-09-27.
2. A **rung-rebuild** session ([golden README](../golden/README.md) phase 4) rebuilds the eight rungs, which replays the history.
3. **A phase-5 run** (golden README) runs `set-4-claude`. 🔴 Arpit scores it. Each step then counts its
   own pool: **below 6 stops that step**, as before.
4. ✅ ~~**Arpit:** step 10's forks~~, ruled U0 · B2 · E1 on 2026-09-27.

## 🔴 STEP 1 DECIDED BY THE TABLE 2026-09-24 — INCONCLUSIVE; the ruling is Arpit's

A session that did not capture the arms ran the frozen
[`decide.py`](../regression/2026-09-15-anchor-text/evidence/decide.py). It and
`verdict.py` are unchanged since `cfca651a`. → [VERDICT](../regression/2026-09-15-anchor-text/VERDICT.md).

- Tagged `hit@1`: `0.5` +2/−0 (cannot clear), `1.0` **+7/−0, p = 0.016, clears
  the floor of 7**, `2.0` and `3.0` +9/−0. Untagged 0/0 everywhere. **No baseline
  rank-1 hit lost at any weight.**
- Clause 3 holds at rank 1. **The hub half-moves**: `s3u-009` 8→6 and `s3u-043`
  5→4, both misses in every arm. The table sends that to Arpit.
- **Question (inbox):** PASS at `anchor = 1.0`, FAIL (clause 3), or keep
  INCONCLUSIVE? `anchor` stays `0.0` until he rules.

## 🔴 STEP 1 SCORED 2026-09-24, 11:45 (Arpit's hand) — the verdict is a NON-capturing session's

Five complete score files; set-wide `hit@1` 41 → 43 / 48 / 50 / 50 and
`primary@1` 18 → 25 / 30 / 33 / 33 ([report §4](../regression/2026-09-15-anchor-text/report.md)).
**These totals are not the rule.** Clauses 1–4 read tagged per-query flips, the
SR-RS d19 floor and the hub.
**Next:** a session that did not capture the arms runs
[`decide.py`](../regression/2026-09-15-anchor-text/evidence/decide.py) (frozen
at `cfca651a`) and files `VERDICT.md`. INCONCLUSIVE → Arpit.

## ✅ STEP 1 ARMS CAPTURED 2026-09-24 (Claude Code, Opus) — the score is Arpit's, the verdict another session's

[Report](../regression/2026-09-15-anchor-text/report.md) · [amended pre-registration](../regression/2026-09-15-anchor-text/PRE-REGISTRATION.md) §AMENDMENT 2026-09-24.

- **Amended first, committed at `cfca651a` before any call.** It names `hit@1`
  (`primary@1` beside it) on set-3-claude at `rung-01000`, and carries the ruling's
  *"ruled after the pools were seen — informed"* line. Also frozen there: the tag
  `anchor_dependent` (27 of 80, the gen-2 pool rule, imported) and
  `evidence/decide.py`. Clause 3 is read at rank 1, on the hub
  `01-sop-temperature-excursion`.
- **Built already:** `[bm25f] anchor` has shipped at `0.0` since 2026-09-15.
  Nothing in the engine changed.
- **Five arms** `0.0 / 0.5 / 1.0 / 2.0 / 3.0` ran on the rung's own engine
  `2dbe870f`, with no re-ingest. **`anchor-0.0` equals the gen-2 capture on 80 of
  80 rows.**
- **Rank 1 moves on 9 / 14 / 17 / 18 questions, all of them tagged.** The hub is
  first on 5 → 4 questions. These are changes, not improvements.
- 🔴 **Next, in order:**
  1. Arpit runs `just golden-score work/regression/2026-09-15-anchor-text`.
  2. A session that did **not** capture the arms runs `evidence/decide.py`.
  3. An INCONCLUSIVE goes back to Arpit.
- **Agent-side, meanwhile:** step 4's pre-registration.

## ✅ STEP 1 (ANCHOR) FILED PASS at `anchor = 1.0` — 2026-09-24 (Arpit, Cowork)

*"It is a pass. Ratify."* [Verdict](../regression/2026-09-15-anchor-text/VERDICT.md).
**Reopen-trigger:** the hub taking rank 1 on a miss, in any later run.

**✅ SHIPPED 2026-09-24 (Claude Code), in one change — PRE-REGISTRATION §If it passes:**
- **Default:** `ANCHOR = 1.0` in `query/bm25f.py` and `query/bm25f.mjs`, read by
  `Scoring`, `Tune` and the loader on both sides; the setup template's comment
  now says the value is measured.
- **Records:** SR-TUNE 17 + new 17a (the default, the upgrade divergence, and
  `--no-tune` no longer switching anchor off) · SR-RANKING 12c–12d · SR-INGEST new 17e.
- **L4:** this repo ingested from empty under `0.0` and under `1.0` gives
  byte-identical `.fux/index/` (1 792 documents, one hash).
- **Four surfaces, at `anchor = 1.0`:** scan = accelerator, **22 144
  comparisons byte-identical** (`tools/differential/run.py --skipping both`);
  Node = bundle = Python, **0 of 225 discordant** (`node_arm.py`, both arms).
- **Tests:** a new test holds `ANCHOR`, `K1` and `B` equal across the two
  engines (only their spelling was checked before); the anchor tests now cover
  the default, off, and 2.0.
- **CHANGELOG:** Unreleased/Changed — a repo that ran `fux setup` keeps `0.0`;
  a fresh clone gets `1.0`.
- ⚠ **This repo's own `.fux/tune.toml` still pins `0.0`** — the divergence,
  exactly as stated. Changing it is a separate choice for Arpit.

**Next:** step 4's pre-registration.

## ✅ RULED 2026-09-24 (Arpit, Cowork) — steps 1 and 4 are judged at RANK 1, on set-3-claude

*"yes"* — to *judge steps 1 (anchor) and 4 (expansion) at rank 1 on set-3-claude,
as steps 5 and 9 were ruled on 2026-09-23?*

- **Primary endpoint `hit@1`, `primary@1` beside it**, on **set-3-claude** at `rung-01000`.
- **Pools:** step 1 = **14**, step 4 = **10** winnable at rank 1 (2 and 0 at rank 5).
- ⚠ **Ruled AFTER the pools were seen — `informed`, and said so.** Not a moved
  threshold: neither step has a number, and step 1's frozen pre-registration names
  no `k`. Each step's pre-registration records this sentence.
- **Order:** step 1 first (pre-registration exists, pool larger; clause 3's hub
  control is `01-sop-…` with 8 inbound `ref` edges), then step 4 (not yet
  pre-registered). One mechanism per arm; each built off by default.

## ✅ STEP 9 FORKS RULED 2026-09-24 (Arpit, Cowork) — D2 · I1 · M1 · S1; still parked by the pool

*"agree implement all"* — on the recommendation *take D2, I1, S1; score first; stop below 6*. The score
came back with step 9's pool at **2 and 1**, so **the stop rule he agreed to fires:
nothing is built.** The forks are ruled, not deferred — a future set with an
intent-tagged pool ≥ 6 starts the build straight from them.

## 🔴 SCORED 2026-09-24 — each step's pool on generation 2; steps 1 and 4 have one, at rank 1 only

[Score and pools](../regression/2026-09-24-golden-gen2-rung-01000/report.md).
The tags come from question text and `seed/` alone
([`step_pools.py`](../regression/2026-09-24-golden-gen2-rung-01000/evidence/step_pools.py)).
**Winnable** means a tagged, answerable question that misses the endpoint.

| step | set-2-claude · rank 1 / rank 5 | set-3-claude · rank 1 / rank 5 | state |
|---|---|---|---|
| **1** anchor | 5 / 2 | **14** / 2 | 🔴 **the endpoint is Arpit's.** The frozen pre-registration names a floor of 6 and no `k` |
| **4** expansion | 0 / 0 | **10** / 0 | 🔴 not pre-registered; the endpoint is Arpit's |
| **9** intent | 2 / 0 | 1 / 0 | ⏸ **stops before build**: the pool is below 6 at every `k` (the compare doc's rule) |
| 2 identifier | 0 / 0 | 1 / 0 | left for W-205 on 2026-09-20 — confirms its stop |

- 🔴 **One question, the same shape as the 2026-09-23 ruling on steps 5 and 9:**
  judge steps 1 and 4 at **rank 1** (`hit@1`, with `primary@1` beside it), on
  set-3-claude?
  - At rank 5 neither can produce a verdict: the pools are 2 and 0.
  - ⚠ **This is asked after the pools were seen.** It is still not a moved
    threshold, because neither step has a number, and step 1's frozen file
    names no `k`. But it is **informed**, and the ruling should say so.
- **Step 1's clause 5 is now satisfied on the data:**
  - 17 anchor-distinctive terms on 5 targets;
  - 25 answerable questions use linker-only words;
  - a hub, `01-sop-…`, with 8 inbound `ref` edges, is available as clause 3's
    control.
- **Step 9's compare-doc forks are deferred, not refused.** The trigger to
  reopen is a question set whose intent-tagged pool is ≥ 6.

## 🔴 STEP 9 IS A COMPARE DOC — 2026-09-24 (Claude Code, Opus); three forks are Arpit's

[`compare/intent-doctype-prior`](../../archive/compare/intent-doctype-prior.compare.md) (archived 2026-09-29) —
the proposal's *"starts as a compare doc"*, done.

- **Measured first:** 0 of 32 seed front-matters declare a type, and every seed
  is in one source directory. So a per-source (D1) or front-matter (D3)
  declaration means building a new ladder. **Only D2 can be tested on the
  frozen one**: a `[doctype]` glob → type table in `tune.toml`, read at query
  time and written into the arm's copy from file names alone.
- **Recommended:** D2, then I1 (a fixed cue lexicon, which is also the pool's
  tag), then M1 (`[ranking] intent_weight`, at `0.0`), then **S1: step 3's
  history/current intent stays out**. One mechanism per arm.
- 🔴 **Two things wait on Arpit:**
  1. the three forks;
  2. `just golden-score` on the [gen-2 capture](../regression/2026-09-24-golden-gen2-rung-01000/report.md).
     A pool is *tagged ∩ in the top 10 ∩ missing rank 1*, and only the score
     supplies the last two terms.
- **Pool below 6 → stop before any build** (W-219).

## 🔴 STEP 5 ADJUDICATED 2026-09-23 — INCONCLUSIVE by the table; the filing is Arpit's

[VERDICT](../regression/2026-09-23-rm3/VERDICT.md), written by a session that did
not capture the arms, from the frozen `decide.py`.

- **No arm clears the gain bar** on the 92 tagged questions (nets −1, −1, +3, +2
  against 7–10 needed), and **every arm breaks the drift bound**: 6 / 8 / 8 / 11
  baseline rank-1 hits lost. `hit@10` also falls 102 → 89–94.
- The table names no row for *positive sub-floor net with drift broken*, so it
  lands in INCONCLUSIVE → Arpit.
- 🔴 **His call, minimal:** file RM3 as FAIL (drift at every weight) or keep it
  INCONCLUSIVE. **Nothing in the engine changes either way** — `rm3_weight`
  already defaults to `0.0`.
- ⚠ ANALYSIS §1's reading (feedback = lexical first pass, not the graph-boosted
  list) is still his to confirm; overturning it re-runs the arms.

## ✅ STEP 5 ARMS CAPTURED AND SCORED 2026-09-23 — the verdict is a different session's

[Report](../regression/2026-09-23-rm3/report.md) · [analysis](../regression/2026-09-23-rm3/ANALYSIS.md).
Five arms at engine `36c913c7`, index root `17fe414e…` on every copy, and a
re-ingest check that writes 0 shards. **Rank 1 changes on 17 / 28 / 37 / 48 of
125** as the weight rises (7–15 untagged). The capturing session did not read
the scores and does not adjudicate them.

- ✅ **Scored by Arpit, 01:03**: five files under `scores/rm3-<w>/rung-01000/`, 125 rows each, none partial, `"set": "2-u"`.
- **Then a session that did NOT capture the arms:** `evidence/decide.py` →
  `VERDICT.md`. INCONCLUSIVE goes to Arpit.
- ⚠ **One reading for him to confirm or overturn:** the feedback set is the
  lexical first pass, not the graph-boosted list `ask` prints (ANALYSIS §1). If
  he reads the pre-registration the other way, the arms are re-run.

## ✅ STEP 5 BUILT 2026-09-23 (Claude Code) — off by default, arms not yet captured

**No treatment number exists.** The mechanism is the frozen one, in both readers.

- **Built:** `query/rm3.py` and its twin `rm3.mjs` — both deleted 2026-09-27
  by W-224 ([SR-EXPAND](../../records/0149_expand.md) decision 17). Top 10 documents from an
  un-expanded first pass, their committed records, 10 RM1 terms, scored through
  `expand.build` at `[ranking] rm3_weight` (default **`0.0`**: no first pass).
- **Decided in the build, declared** in [SR-EXPAND](../../records/0149_expand.md) decision 16:
  1. a caller's `--expand` switches RM3 off;
  2. `fux lexical` never runs it;
  3. the first pass writes no stats;
  4. ⚠ **the first pass is the LEXICAL ranking.** On `rung-01000` the tune has
     `ask_boost = true`, so the feedback set is not always the list `ask`
     prints. The pre-registration's *"exactly the `--top 10` list the harness
     captures"* is its reason for `fbDocs = 10`, not a mechanism, and this
     reading is flagged rather than assumed.
- **Held:** `0.0` byte-identical (no first pass is asserted); scan == accelerator
  at every arm value; Python == Node through each reader's own `tune.toml`
  loader. `tests/query/test_rm3.py`.
- **Records:** SR-EXPAND 16 (owns `rm3.py`) · SR-TUNE 18 · SR-CLI 12 ·
  SR-NODE-SEARCH 20 · SR-ANSWER 15 · SR-CONFIDENCE 18.
- **Next:** capture `rm3-0.0` and `rm3-0.1 … 0.5` at the build's commit, then
  Arpit runs `just golden-score work/regression/2026-09-23-rm3`. Then a session
  that did **not** run the arms runs
  [`evidence/decide.py`](../regression/2026-09-23-rm3/evidence/decide.py), which
  was frozen before any score existed.
- **Step 9 cannot be pre-registered yet, for two reasons.** The proposal says
  `#9` *"starts as a compare doc"*. And its doc-type half is a declaration per
  source that the frozen ladder does not carry, so adding one changes a rung.

## ✅ STEP 5 PRE-REGISTERED 2026-09-23 (Claude Code) — pool 39, no stop; the build is next

[The frozen bar](../regression/2026-09-23-rm3/PRE-REGISTRATION.md). **Nothing
is built and no treatment number exists.**

- **Endpoint as ruled:** `hit@1` gates, `primary@1` is reported beside it.
  `[ranking] rm3_weight ∈ {0.1, 0.2, 0.3, 0.5}`, first that clears, ascending,
  against `0.0`. Top-10 feedback documents, 10 terms, RM1, scored through
  `expand.build`. All fixed before the build.
- **Drift bound = clause 2:** one baseline rank-1 hit lost **anywhere in the
  set** fails that value.
- **Tag `rm3_underspecified`:** a question that *names nothing* (no digit, no
  identifier, no mid-sentence capital, no quote). Mechanical, from question text
  alone. **92 of 125.**
- **Pool** (tagged, in the returned 10, missing rank 1): **39 ≥ 6 → no stop.**
  It is 39 of the ruling's 51 reorderable misses.
- 🔴 **Correction to the rationale, not to the ruling.** *"8 reorderable < `min_fix`
  ≈ 9"* compared the reorderable 8 with the bar for all 18 misses. With zero
  losses, 8 wins give a discordant count of 8, and the bar at 8 is 8, so that
  clears. **Any pool ≥ 6 admits a verdict**, and 6 wins with zero losses is the
  real minimum. The rank-1 ruling stands on the 51 versus 8. Filed as
  [W-219](../IMPLEMENTATION.md).
- **Next:** build step 5 (**Opus**). Then capture both arms at one engine commit
  with `golden_run.py`. Then Arpit runs `score.py` on each.

## ❌ STEP 5 (RM3) FILED FAIL — 2026-09-23 (Arpit, Cowork)

*"W168 mark it as fail."* Drift broken at every weight (6 → 11 rank-1 hits lost), no gain cleared;
`rm3_weight` stays `0.0`. [Verdict](../regression/2026-09-23-rm3/VERDICT.md) ·
SR-EXPAND decision 16. **Step 5 is closed.** Next here: **step 9** (intent prior,
judged at rank 1), then steps 1, 2 and 4 on the rebuilt ladder once W-215's
prompt-4 rebuild lands.

## ✅ RULED 2026-09-23 (Arpit, Cowork) — each remaining step is judged on its OWN measure; steps 5 and 9 at rank 1

*"Go with the recommendation. That is judge step five and nine at rank one. Six, seven, ten have their own measurements, so use that."*

**Why he was asked.** `set-2-claude`, scored 2026-09-23 on `rung-01000`: of 112 answerable questions, `hit@5` misses 18 and **10 of those are never retrieved at all**, so only **8** are reorderable. At rank 1, **51** misses are already in the top 50. ⚠ *Corrected 2026-09-23 ([W-219](../IMPLEMENTATION.md)): this said the 8 were "below `min_fix` ≈ 9", so no `hit@5` verdict was possible. That compared the 8 with the bar for all 18. With zero losses **6 wins clear**, so a `hit@5` verdict was very unlikely, not impossible. The ruling stands on 51 against 8.*

| step | judged on | primary endpoint | note |
|---|---|---|---|
| **5 · RM3** | **rank 1** | **`hit@1`**, `primary@1` reported beside it | its keep-rule already carries the drift bound: *no answerable question loses its top-1* |
| **9 · intent → doc-type prior** | **rank 1** | **`hit@1`**, `primary@1` reported beside it | the doc-type half must be declared per source first |
| **6 · SDM proximity** | its own | **passage-level** gain in refer | it scores the fetched bytes, not the document order |
| **7 · MMR** | its own | **coverage** in the top k, **with `precision@1` unchanged** | it must not move rank 1 by design; waits on the graph plane in `ask` |
| **10 · section units** | its own | **its own compare doc decides**, before any test | a plane change, its own major |

- ⚠ **`hit@1` is the primary endpoint and `primary@1` the secondary, on my reading of *rank one*.** A pre-registration names one; this is the one it names unless he says otherwise.
- 🔴 **The pool of 51 is across ALL answerable questions.** Each step acts only on its own kind — under-specified questions for 5, intent-labelled ones for 9 — so **each pre-registration first counts its own pool among the questions it tags**, and stops if that pool is below `min_fix` (⚠ read: below 6, W-219). **51 is the ceiling, not the promise.**
- 🔴 **The tags are set from the released question TEXT alone**, never from the key — [SR-WORK-TESTDATA](../../records/0068_WORK-test-data.md) T2, and `informed` whatever the result.
- **Not a moved threshold.** No step had been pre-registered; each one's endpoint is being chosen before its first number, which is what [SR-RS](../../records/0133_predictions.md) d10b requires.
- **Steps 1, 2 and 4** still need inputs the seed lacks — prompt 10 (W-215 items 2–4). **Step 3** is foreclosed; **step 8** needs a corpus with history (T11).

**So this item is 🟢 again: steps 5 and 9 can be pre-registered now.** Cheapest first: **step 5**, since RM3 needs no declaration.

## ✅ RULED 2026-09-20 (Arpit, Cowork) — step 2 leaves this item

*"W-168 — I agree, let's go with the recommended approach."* So: **Codex adds
identifiers of the failing shape** (shared prefix + short number — `RF-118 /
RF-119 / RF-120`, `PROJ-123 / PROJ-124`) **to the seed with W-191's link-bearing documents, so the ladder is rebuilt
once. Later the same day: Claude authors both as set 3** — W-204 input **I-2** —
and no step here waits on Codex.

**Step 2 (the exact identifier field) is no longer here** — it is part 2 of
[SR-RANKING](../../records/0111_ranking.md) decision 9 (W-205, **closed
2026-09-22** — family (a) shipped, (b) and (c) unbuilt), merged with the frontmatter
and analyzer defects on Arpit's ruling that they are one subject. Steps 3–10
stay.

⚠ **That ball is SUPERSEDED — corrected 2026-09-22.** This header read *"Ball →
🟡, waiting on W-204"* from 2026-09-20; **W-204 closed on 2026-09-22** and the
queue row went 🟢, leaving the file and the row disagreeing for two days (spotted
by the Cowork session that ruled W-214, and left for this one). **The ball is now
🔴, waiting on [W-215](../../archive/open/W-215-generation-2-corpus.md)** — and the sentence that
followed it was right about the shape and wrong about the item: every remaining
step does need a golden question or document it does not have, but the inputs
come from **generation 2**, not from W-204.


## 🔴 MEASURED 2026-09-22 — the blocker is the CORPUS, and it is one deliverable, not eight

[The step-input run](../regression/2026-09-22-w168-step-inputs/report.md) ·
[the anchor census](../regression/2026-09-22-anchor-input-census/report.md).
**No feature was built, and none should be until the corpus moves.**

🔴 **The pool ANY ranking change can win is 7–23 answerable questions per set
per rung**, and [SR-RS](../../records/0133_predictions.md) d19's required net at
those counts puts `min_fix` at **7–11**. **One step must fix 58–78 % of every
remaining failure, with ZERO regressions, in all three sets, to produce a
verdict at all.** ⚠ *Corrected 2026-09-23 (W-219): **26–86 %**. 6 wins with zero
losses clear in every bucket; `min_fix` was the all-flip bar.* W-205 part 2 family (a) came closest ever measured here —
`+1 / +3 / +4`, 0 regressions — and returned INCONCLUSIVE.

| step | state as of 2026-09-22 |
|---|---|
| **1** anchor text | 🔴 **blocked, new reason.** W-191 was fixed: the ladder now has **61 anchor-bearing `ref` edges per rung**. Anchor-**distinctive** terms: **1, and it is a filename.** Every word a linker uses is already in its target, so the fold can add tf and cannot make anything findable. The pre-registration's clause 5 still forbids the arms |
| **2** identifier field | 🔴 stopped 2026-09-18, unchanged — headroom 3–4 of 33 |
| **3** supersession | 🔴 **FORECLOSED — see below.** Not unbuilt; un-built by a ruling |
| **4** corpus-mined expansion | 🔴 **blocked.** Across 28 seed documents: **0** `Term (ABBR)` pairs, **1** glossary line (it matches *"copy"*), **3** `aliases:` on one document. Three alias pairs cannot produce seven flips |
| **5** RM3 · **6** SDM · **7** MMR | ⚠ **no `23c` tag exists for any of their inputs**, so none can state its headroom |
| **8** git authority prior | 🔴 blocked by the proposal's own words — needs a corpus with history; the ladder is synthetic and rebuilt at one stamp |
| **9** intent → doc-type | 🟢 **the intent half of its input is present and abundant** — 50 current-seeking and 17 history-seeking tags across sets 2 and 3, plus `priors-probes.jsonl`. 🟡 the **doc-type** half is undeclared in the golden corpus |
| **10** section units | ⚠ a plane change; owes its own compare doc first |

⚠ **Two `23c` tags read as a step's input and are NOT it.** `link_dependent: 14`
is **multi-hop** (the refer plane and the graph), not the anchor field;
`vocabulary_gap: 25` is colloquial **paraphrase**, which no `Term (ABBR)` miner
reaches. **Both tags are accurate about the question and wrong about which
feature it exercises**, and that is the more expensive kind of wrong.

**What generation 2 owes this item** is the report's §5 — six items, measured
rather than guessed, headed by *questions today's engine fails*, because
`hit@5` at 81–94 % is what leaves only 7–23 winnable.

**Instruments shipped with the finding** (second strike, so gates —
[SR-WORK-SESSION](../../records/0060_WORK-session.md) decision 13):
`ref_edge_census.py` now counts **anchor-distinctive** terms and exits **3**
when a corpus has links whose words its targets already have;
`ranking_headroom.py` moves SR-RS d22's arithmetic **in front of** the build.

## 🔴 STEP 3 IS FORECLOSED (2026-09-22) — by a measurement and a ruling, not by data

The corpus **has** superseded/successor pairs. **The mechanism is gone.**

[VERDICT-W143](../regression/2026-09-12-priors-and-tables/VERDICT-W143.md)
answered Arpit's own pre-registered question — *does ANY single global value
clear a `0 broken` bar?* — with **NO**:

| | current-seeking | history-seeking |
|---|---:|---:|
| shipped default | 11–12 / 13 | 8–9 / 13 |
| **any value that demotes** | **13 / 13** | **5 / 13, down to 0 / 13** |

> **Arpit, 2026-09-11:** *"every broken query had the superseded document as its
> correct answer. **Supersession belongs to the query's intent, not to the
> document.**"*

`superseded_weight` was **removed** on 2026-09-13 (W-151); `superseded` is a
tie-break now, read only where rounded scores are equal. **Re-introducing a
global demotion under a new name walks back a ruling on a measurement, and no
session does that.** Step 3's other two halves are out of reach for their own
reasons: the **walk** is W-161's graph-composed `ask`, which this item lists as
out of scope, and the **anchor inheritance** reads step 1's fold, which has
nothing to inherit.

🟡 **Where the ruling points instead is step 9's neighbourhood**, and the intent
labels for it exist — but step 9 as written is *intent → **doc-type***, a
different mechanism. **Whether they become one step is a scoping decision and
Arpit's**, exactly as the identifier work became one subject on his ruling.

---

# W-168 — the ten search improvements, one program

**Model: Opus for #4, #8, #9, #10 (drift, bias, a plane change); Sonnet for the rest once
a golden question and a pre-registration exist.**

**Promoted 2026-09-14 by Arpit** from
[`proposals/search-improvements-v3.md`](../proposals/search-improvements-v3.md), which
stays the spec (the per-idea table in its §1 and §3b is the definition of done here, not
repeated). **W-156 ruled 2026-09-14:** every step is a ranking change and lands under
[SR-RS](../../records/0133_predictions.md) decision 19's paired floor on golden data —
the single-corpus sentence is gone ([SR-LAW-0](../../records/0002_LAW-0-authority.md)
decision 2a). Nothing agent-side waits.

## ✅ MEASURED 2026-09-18 — step 2's stopping reason was wrong, and so was the premise's consequence

**Arpit, 2026-09-18:** *"Codex is not going to run it. You go ahead and run it."*
So this session wrote the 33 id-queries (one per identifier, targets by grep
over the seed, no key) and ran the baseline on rung-00100, 01000 and 10000:
[the run](../regression/2026-09-18-identifier-headroom/report.md) · `informed`.

| rung | primary hit@3 | headroom |
|---|---:|---:|
| 100 | **30/33** | 3 |
| 1 000 | 29/33 | 4 |
| 10 000 | **30/33** | 3 |

- 🔴 **Mangling is symmetric.** `dairi` IS in the index — the document is
  analyzed by the same analyzer. Split identifiers retrieve at ~90 % top-3 at
  every rung. The survival report compared query tokens to raw text.
- 🔴 **Headroom is 3–4 of 33, below the floor of 6 flips, on every rung.**
  Step 2 cannot be given a verdict on this corpus **whatever questions are
  written** — prompt 8 does not unblock it. What is missing is identifiers of
  the failing shape (a shared prefix + short number, `PROJ-123`) in the seed.
- 🔴 **The absolute misses are frontmatter-only identifiers**, unindexed by
  `parse.py`'s meta/body split — a different defect, filed as
  [W-201 → W-205 → SR-INGEST](../../records/0106_ingest.md) decision 23d, shipped.

**Step 2 stays stopped, for the corrected reason.** Prompt 8 is withdrawn as
the unblock; the unblock is a seed with the failing shape, which is a Codex
corpus-prompt note, or a ruling to descope the field until a consumer corpus
shows the shape.

## 🔴 Step 2 is STOPPED BEFORE IT STARTS (2026-09-16) — by this item's own rule

[The survival check](../regression/2026-09-16-identifier-survival/report.md).

**The proposal's §0: *"Build the golden question before the feature, or the
verdict is theatre."*** Measured:

| question set | questions | carrying an identifier |
|---|---:|---:|
| set 1 | 125 | **4** |
| set 2 | 124 | **0** |

**4 is below the floor of all floors.** A net of 6 is the minimum that clears α at
*any* discordant count, and 4 questions cannot produce 6 flips — so **no arm on
this set can return a result**, whatever the field does. A **data defect
(d23b), fixed in the data, never a null.**

🔴 **This is [W-191 → W-204](../regression/2026-09-22-golden-final-score/FINAL-SCORE.md)'s lesson applied one
step earlier.** There, a link feature was built and measured on a corpus with 0
`ref` edges, and `0 of 124 flips` was filed as a number before anybody counted
the input. Here the counting came first, at the cost of a few seconds.

### ✅ The premise is TRUE, and worse than the proposal stated

**0 of 33 distinct identifiers survive the analyzer whole.** Not *some* — zero.
**3 are MANGLED rather than split**, producing a string no document contains:

| identifier | tokens | |
|---|---|---|
| `DAIRY-2` | `['dairi', '2']` | `dairi` is nowhere in the corpus |
| `KFS-2014` | `['kf', '2014']` | the `S` is gone |
| `QCL-OPS-DOCK-03` | `['qcl', 'op', 'dock', '03']` | `OPS` became `op` |

🔴 **And the SEPARATOR decides the outcome** — `ERR_2031` survives whole,
`RF-118` does not. Coverage today is an accident of punctuation, and the
underscore case **already half-works**, which is the more dangerous state: a
build measured only on those would show a small gain from a field that changes
nothing for them.

### What step 2 needs before it may start

1. 🔴 **Id-queries — prompt 8,
   Codex's.** ⚠ **Unlike W-191, the documents are fine** (51 tokens across all
   20); only the questions are missing, which is a smaller ask.
2. ⚠ **A design decision, named and NOT taken:** an unstemmed field needs
   **committed postings**, so unlike step 1's anchor field it cannot fold at read
   time and cannot avoid a `_format` change
   ([SR-INDEX-LIFECYCLE](../../records/0108_index-lifecycle.md) decision 9.1).
   **Whether it rides 3.0's existing unreleased bump belongs in the build's own
   pre-registration.**

### ✅ Research filed 2026-09-18, GRADUATED 2026-09-20 — [`proposals/identifier-exact-match.md`](../../archive/proposals/identifier-exact-match.md) *(archived 2026-09-24)*

🔴 **It is now two items, and neither is step 2.** [W-203 → W-205 → SR-RANKING](../../records/0111_ranking.md) decision 9
carries the two analyzer defects and the four families, **waiting on this item** — not on a
design question, on a seed corpus of the failing shape. [W-202](../../archive/open/W-202-identifier-analyzer-gate.md)
is 🟢 and waits on nothing: freeze what the analyzer does to the 33 ids as a test, so any
later change shows as a diff. ⚠ **Step 2 as written picks family (c), the separate field —
and (a) preserve-original is a PRECONDITION of it, not an alternative.**

**Arpit asked 2026-09-18 how this is solved elsewhere, and for a before/after
test either side of the build.** Filed, not decided. Three things in it change
what step 2 is:

1. **The cause is two lines in [`query/analyzer.py`](../../src/fux/query/analyzer.py),
   and neither is a missing field.** **D1** — `_WORD_RE`'s class holds `_` and
   not `-`, `.` or `/`, so the module's own *"whole AND parts are both emitted"*
   is kept for `snake_case` and silently broken for every other separator; that
   **is** the underscore/hyphen asymmetry. **D2** — `should_stem` protects
   digits and underscores but not all-letter acronyms, so Porter takes `kfs` to
   `kf` and `dairy` to `dairi`. Reproduced against the shipped code.
2. ⚠ **A correction to the survival run.** Its §1 says a mangled id *"cannot be
   reached at all"*. **Ingest and query import the same `analyze()`**, so
   `DAIRY-2` typed as a query produces the same `['dairi', '2']` the document
   wrote and **does** match. What is lost is **precision** — one rare term
   becomes two common ones, sibling ids collide on `rf`, and the band reports
   `missing: dairi`. Step 2 is a ranking fix, not a recall fix, which is what
   keeps [SR-RS](../../records/0133_predictions.md) d19's paired floor the right bar.
3. 🟢 **Gate A — a before/after that does NOT wait on Codex.** Re-run
   `tools/quality-controls/identifier_survival.py` against the 33 frozen rows:
   before is measured (0 of 33), after must be 33 of 33 with 0 mangled. It
   falsifies a broken fix in seconds. ⚠ **It is a mechanism probe, never a
   ranking verdict** — only prompt 8's gate B can say the corpus got better.

⚠ **The four families are ordered cheapest-first in the proposal, and (a)
preserve-original is a PRECONDITION of (c) the separate field**, not an
alternative to it: a new field still has to be fed by a tokenizer that cannot
see past a hyphen. **The current framing of step 2 has that ordering backwards.**

---

## ✅ Step 1 BUILT 2026-09-15 — obligations 1–7 and 9 shipped; 8 and 10 are Codex's

**Claude Code, 2026-09-15.** The mechanism is in both readers, behind
`[bm25f] anchor`, **default `0.0`**. ⚠ **No claim about ranking quality is made
or may be made** — the frozen bar is
[`2026-09-15-anchor-text`](../regression/2026-09-15-anchor-text/PRE-REGISTRATION.md)
and it has no `VERDICT.md`.

| # | obligation | state |
|---|---|---|
| 1 | `_LINK_RE` captures the text; `DocScan.links` is `(text, target)` | ✅ |
| 2 | the SOURCE edge carries it; the record schema amended | ✅ **as `at` (hashed terms) + `al`, not the string — see below** |
| 3 | a reverse map in `.fux/runtime/` | ✅ `anchors/<prefix>.json` + `alen` + `total_anchor_len`, `fux.runtime.v6` |
| 4 | **retrieval**: an anchor match makes the `dst` a candidate | ✅ both generators, and `Expansion.matches` had to move with it |
| 5 | the fold lands **once**, in the shared read path | ✅ in `rank()`; **5 536 byte-identical comparisons at `anchor = 2.0`, 0 mismatches** |
| 6 | a `tune.toml` key, default 0 | ✅ `[bm25f] anchor` |
| 7 | the Node reader folds identically | ✅ with its own fixture — the differential arm could not have caught a forgotten transcription |
| 8 | 🔴 **link-bearing DOCUMENTS first, then golden question(s)** | 🔴 **Codex's** — and the reason here was wrong. The ladder carries **0 `ref` edges on all eight rungs** and `work/golden/seed/` has no link syntax at all ([measured](../regression/2026-09-15-anchor-mechanism/report.md)), so **no question can exercise this field** — SR-RS d23a wants the *input*, not the query. Key access was never the blocker |
| 9 | frozen pre-registration | ✅ [filed](../regression/2026-09-15-anchor-text/PRE-REGISTRATION.md) |
| 10 | measure → verdict → default on only on PASS | 🔴 **blocked on 8.** ⚠ The arms have still never run; a [mechanism probe](../regression/2026-09-15-anchor-mechanism/report.md) measured **0 of 124 flips at every weight on four rungs**, which is a **data defect (23b), not a null**, and rules nothing |

### Three decisions the build made that the ruling did not

1. 🔴 **The edge carries hashed TERMS, not the anchor string.** Link text is a
   verbatim fragment of the source's prose, so committing it plainly is content
   in the index ([L3](../../records/0005_LAW-3-content-never-durable.md)) and
   would need ex-L5's hashed-meta branch on top. A hash is a statistic, and it is
   the currency `terms` already uses — so the scan's byte prefilter finds an
   anchor source by the substring check it already runs, free. **The ruling was
   about WHERE the byte lives; this is about what it is.** Flagged rather than
   assumed: if Arpit wants the readable string for `fux explain`, it is a
   second field and a second decision.
2. **`_format` bumped to `fux.index.v3`**, because a property appeared and
   [SR-INDEX-LIFECYCLE](../../records/0108_index-lifecycle.md) decision 9.1 says
   that bumps. Cost: a whole-corpus diff and `fux ingest --full` for every
   consumer. ⚠ **The vendored Node bundle had to be rebuilt in the same change
   or it refuses the new index outright** — and that rebuild carried W-161's and
   W-176's bundle output too, which had not been regenerated.
3. **`alen` joins `wlen`.** Anchor tf is **unbounded in the number of linkers**
   where body tf is bounded by one document's length, so a linked-to document is
   priced as a longer document. It is the only guard against the hub failure the
   pre-registration names, which is why that is clause 3 of the decision rule.

### What it cost, and what it did not

- **Off costs nothing.** `0.0` is not weight zero — every anchor branch tests it
  and is skipped, so an unconfigured corpus does the float arithmetic it did
  before the field existed. Asserted, and measured: 5 536 byte-identical
  comparisons at the default.
- **On costs the reference scan one byte regex per line**, because a document's
  anchor length belongs in its `wlen` whether or not it matches.
- ⚠ **`tools/differential/run.py` could not run on this repository** —
  `queryset.py` decodes every walked file as UTF-8 and ten are not. Pre-existing,
  unrelated, filed as W-184 (closed 2026-09-15); the evidence
  was gathered through an ad-hoc copy of the same harness and is named as such.

### Records amended

[SR-INGEST](../../records/0106_ingest.md) 17 · [SR-EXTRACTED](../../records/0115_extracted-mode.md) 10 ·
[SR-INDEX-LIFECYCLE](../../records/0108_index-lifecycle.md) 14 · [SR-RANKING](../../records/0111_ranking.md) 12 ·
[SR-T1-ACCELERATOR](../../records/0110_accelerator.md) 15 · [SR-TUNE](../../records/0135_tuning.md) 17 ·
[SR-GRAPH](../../records/0126_graph.md) 18 · [SR-ASK](../../records/0103_ask.md) 13 ·
[SR-EXPAND](../../records/0149_expand.md) 15 · [SR-CONFIDENCE](../../records/0141_confidence.md) 16 ·
[SR-PII](../../records/0148_pii.md) 21 · [SR-ARCHIVED-CONTENT](../../records/0134_archived-content.md) 9 ·
[SR-NODE-SEARCH](../../records/0153_node-search.md) 19.

⚠ **SR-CONFIDENCE 16 is a finding, not a fix:** a document ranked #1 purely on
what its linkers call it reports **coverage 0** and names the query's word in
`confidence.missing`. That is the honest answer to *what does the top document
itself say?* — and whether it pushes a class of answers into `partial` is
**unmeasured and not in the decision rule**.

---

## ✅ Step 1 RULED 2026-09-15 by Arpit — option (c), the edge carries the text

> **Arpit, 2026-09-15:** *"ratify go with option C"*, on three options put to him
> in chat after the finding below. **Ratified, not built.**

### What was found first, 2026-09-15, before step 1 was built

**1 · Link TEXT is not extracted today, and edges do not carry it.**
[`ingest/edges.py`](../../src/fux/ingest/edges.py)'s `_LINK_RE` is
`\[[^\]]*\]\(([^)\s]+)…\)` — the anchor text sits in a **non-capturing**
class and is discarded; only the target is kept. `DocScan.links` is a list of
targets. So the proposal's *"cost: small — edges are already extracted"* is
half true: the **edges** are, the **words** are not, and `DocScan.links` has to
change shape. This is implementation, and it is unchanged by the ruling.

**2 · The field as SPECIFIED would have made a document's committed bytes a
function of OTHER documents.** If `A`'s `anchor` field is built from the link
text of every document pointing at `A`, then editing `B` changes `A`'s
committed bytes while [`maintain/runner.py`](../../src/fux/maintain/runner.py)
marks only `B` dirty — a full `fux ingest` and an incremental re-index would
produce **different indexes from the same sources**.

⚠ **That is [L4](../../records/0006_LAW-4-deterministic.md) failing on the
incremental path only, which is the worst shape for it**: the full-ingest path
stays byte-reproducible, so every test and every CI check that rebuilds from
scratch passes, and the drift appears only in a working repository that has
been edited over time. **Nothing in this repo would catch it.**

⚠ **Two corrections to that finding, both in fux's favour, both load-bearing
for the ruling:**

- **It is not reachable today.** `runner.py`'s `record_head` says in terms that
  *"`fux ingest` re-indexes the whole corpus regardless of what the list
  says"*, and **`B-002`** records that the dirty list's input is unused. There
  is no incremental path yet to disagree with the full one. The hazard is
  **B-002's inheritance**, not step 1's alone — but building step 1 first
  plants it where nothing would find it.
- **"Cross-document" is not what makes it wrong.** `df` and `avg_wlen` are
  corpus-wide too and cost nothing, because they are **counted at read time**:
  [`store/format.py`](../../src/fux/store/format.py) has `query/scan.py` find a
  term's `df` by scanning raw record bytes, and
  [`derive/accel.py`](../../src/fux/derive/accel.py) folds `idf(df, n)` and
  `avg_wlen` in the derived plane, which
  [`derive/__init__.py`](../../src/fux/derive/__init__.py) calls *"rebuildable
  from the committed shards and never committed"*.

**So the invariant this ruling protects is narrower and sharper than "no
cross-document dependencies":**

> **A committed per-document byte is a function of that document alone.
> Everything corpus-wide is a read-time fold.**

The anchor field as specified would have been the **first** thing ever to break
it. That is the whole reason the specified form was refused.

### The three options put to Arpit, and what he took

| | what it does | the invariant | cost |
|---|---|---|---|
| (a) | a changed document also dirties the targets of its out-edges | **stays broken, patched** | a change to SR-MAINTENANCE's re-index contract + a new equality test; every future cross-document field re-opens it |
| (b) | do not build step 1 (step 5's inheritance goes with it) | safe | loses the highest-value idea in the ten |
| **(c)** | **the text lives on the EDGE, folded in at read time** | **intact** | candidate generation must also retrieve via in-edges |

**He took (c).** `Edge(src=B, dst=A, text=…)` is a pure function of `B`'s own
bytes, which is exactly what `Edge` already is — the edge list is already
written onto the **source** document's committed record. Editing `B` rewrites
`B`'s edges and moves no other document's bytes. The re-index contract does not
change and L4 never enters the conversation.

**Step 5 is covered by the same mechanism** rather than inheriting the problem:
*"the successor inherits the target's anchor text"* becomes a second read-time
fold over the same in-edge map, not a second cross-document committed byte.

⚠ **Option (a) is refused here, not deferred.** The out-edge invalidation is
still probably owed — but as **its own `W-nn` under SR-MAINTENANCE, sequenced
with `B-002`**, with *edit a linker → incremental re-index → assert equal to a
full ingest* as its definition of done. That assertion is worth having whether
or not anchor text is ever built. **It is not this item's, and nothing in W-168
waits on it now.**

### Definition of done — step 1 under (c)

**Model: Opus** — a plane change and a retrieval change in one step.

| # | what | why it is in the list |
|---|---|---|
| 1 | `_LINK_RE` captures the anchor text; `DocScan.links` carries `(text, target)`; every caller updated | the words are not extracted anywhere today |
| 2 | the edge on the **source** document's committed record carries `text`; `index-record.schema.json` amended | this is the whole ruling — the byte stays with the document that wrote it |
| 3 | a reverse map `dst → [(src, text, grade)]` built in `.fux/runtime/`, by `fux build` and by `runner.py`'s post-pass | derived, gitignored, rebuilt whole — free under L4 |
| 4 | candidate generation: a query term matching anchor text makes the `dst` a candidate | ⚠ **this is a RETRIEVAL change, not a scoring one** — without it the document is never a candidate and no fold can rescue it |
| 5 | the fold lands **once, in the shared read path** — never in the accelerator alone | [`query/rank.py`](../../src/fux/query/rank.py) states the contract: *"the accelerator's build asserts it reproduces the same statistics"*; one-sided and `--fast` drifts from the scan |
| 6 | `anchor` is a BM25F field whose weight is a `tune.toml` key, **default 0** | SR-RS d19: behind a tunable, default off |
| 7 | the Node reader folds anchors identically | the differential law's third arm; L10 |
| 8 | golden question(s): a document findable **only** via a linker's wording | SR-RS decision 23 — the data must contain the input the feature acts on |
| 9 | frozen pre-registration, both directions, the SR-RS d19 paired floor | a threshold may never move |
| 10 | measure → verdict under `work/regression/` → **default on only on PASS** | on FAIL the tunable stays at 0 and the record names the failed direction |

**Anchor terms do NOT enter the committed postings.** Saying so is part of the
done-ness: it is what distinguishes (c) from the specified form, and a build
that quietly adds them has shipped (a) under (c)'s name.

### The tests, and the one that proves this is (c)

- 🔴 **`test_edge_text_is_a_function_of_its_source_alone`** — write `A` and `B`
  where `B` links to `A`; re-index `B` alone; assert **`A`'s committed bytes are
  byte-identical**. **This is the test the ruling exists for.** If it ever goes
  red, the build has drifted back into (a).
- `test_anchor_text_is_captured` — the link text survives `_LINK_RE` and reaches
  the record.
- differential: the scan and the accelerator return the same ranking for an
  anchor-matched query (obligation 5, made checkable).
- the Node twin for the same query (obligation 7).
- ⚠ **A general `full == incremental` test is NOT owed here** — it belongs to
  the out-edge `W-nn`/`B-002`, and claiming it here would be this item taking
  credit for a gate it does not build.

### Records to amend in the same change

[SR-INGEST](../../records/0106_ingest.md) (the record shape `edges.py` writes) ·
[SR-EXTRACTED](../../records/0115_extracted-mode.md) (its `edges` bullet, and
the same-sources-same-bytes guarantee now covers the text) ·
[SR-INDEX-LIFECYCLE](../../records/0108_index-lifecycle.md) (the record schema) ·
[SR-GRAPH](../../records/0126_graph.md) (edge kinds; the derived adjacency
carries text, and the reverse map is its neighbour) ·
[SR-RANKING](../../records/0112_postings.md)'s scorer records — the field and
its weight, **plus the sentence that anchor terms are not in the postings** ·
[SR-TUNE](../../records/0135_tuning.md) (the new key) ·
[SR-RS](../../records/0133_predictions.md) (one prediction id).

## Definition of done — per step, in this order

| step | idea | golden prerequisite (Codex's hands where the sealed key is involved) |
|---|---|---|
| 1 | #1 anchor-text field | documents findable only via a linker's wording |
| 2 | #3 identifier field | id-queries |
| 3 | #5 supersession-aware ranking | a superseded/successor pair |
| 4 | #2 corpus-mined expansion | acronym / house-term questions |
| 5 | #4 RM3 (drift bound pre-registered) | under-specified questions |
| 6 | #6 SDM proximity in refer | phrase-sensitive questions |
| 7 | #7 community MMR (after W-161) | multi-facet questions |
| 8 | #8 git authority prior — **starts with a corpus that has history, or does not start** | none in golden |
| 9 | #9 intent → doc-type prior | intent-labelled questions |
| 10 | #10 section units — its own compare doc first | long-document questions |

For every step: golden question(s) → frozen pre-registration (both directions, SR-RS
d19 floor) → build behind a tunable, default off → measure → verdict under
`work/regression/` → default on **only on PASS**; on FAIL the tunable stays at 0 and the
record names the failed direction. **One step per measurement.** Ambiguous → Arpit with
per-query rows.

## Out of scope

The graph-composed `ask` (W-161) and `fux correct` (W-162) — separate items.

## Records this will touch

Per step, as the proposal's §3 table lists: SR-RANKING · SR-POSTINGS · SR-EXTRACTED ·
SR-EXPAND · SR-GRAPH · SR-ARCHIVED-CONTENT · SR-REFER-PLANE · SR-CHUNKING · SR-ASK ·
SR-INDEX-RECORD · SR-TYPES-LIST · SR-RS (one prediction id per step).
