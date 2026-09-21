---
type: OpenItem
id: W-204
title: "W-204 — every rung's outputs on paper, the key opened once, one final score, and v1.0.0 · v2.0.1 · HEAD on the same ladder"
description: "Arpit, 2026-09-20: one document per rung holding every question and what fux answered; then he lifts the golden-answer restriction and one scoring pass produces the final score; and a version benchmark of v1.0.0 vs v2.0.1 vs HEAD on the same rungs. Absorbs every item that was waiting on golden test data or a scored run — W-136, W-87, W-190, W-195, W-191, W-176 steps 4–10, W-161's measured arms, W-175."
status: open
lane: agent
timestamp: 2026-09-20T00:00:00Z
filed: 2026-09-20
ball: agent
---

# W-204 — outputs per rung → key opened → one score → three engines

**Model: Sonnet for phases A and B** (a written definition of done, mechanical
runs, stdlib checks); **Opus for phases C and D** — C retires a Law and
regenerates two byte-gated blocks, D turns 5 000+ per-query rows into the one
number Arpit reads, and a wrong call in either is not caught by any test.
**Phase C's first step is Arpit's hands** — pasting prompt 9 — and no model
executes that.

**Arpit, 2026-09-20 (Cowork):** *"one document for every rung … question and
answers for what rung 100 gave, rung 200 gave, and so on. Then at the end I lift
the restrictions for golden answers, and we do a comparison and generate a final
score. A benchmark between version one, version two and the latest head. All the
work documents that depend on similar test data — merge them into one."*

Ruled in the same exchange: the arms are **`v1.0.0` · `v2.0.1` · `HEAD`**; the
merge takes the **whole** golden/test-data chain; **Claude Code scores from the
key file** once L11 is amended; this session files the item and Claude Code
does the archive mechanics.

---

## ✅ RULED 2026-09-21 (Arpit, Cowork) — the 2026-09-21 exposure was his paste; there is no breach

*"I copy-pasted it so that at least I can get a score. I thought all the test
cases were run. Run them, then I'll paste it again. Ignore the breach. That was
on me. Delete the work item."*

- **W-207 is withdrawn.** It never had a detail file — only queue rows, written
  by the session that stopped — so nothing is archived; the id is spent and not
  reused. **No number carries a breach label from this date**; every golden
  number is `informed`, as prompt 9 already says.
- **The route is now settled by him, not by a guard:** he pastes the key into
  the scoring session when the runs are done. That is phase C in practice; the
  L11 amendment prompt 9 lands is the paperwork, and it may follow the score.
- **Order stands:** finish phase B (the arms manifest is written), then he pastes
  the key, then phase D scores A + B from the hand-offs. W-205 part 2's arms run
  in whichever session is next; execution of frozen code is not authorship.

## ✅ RULED 2026-09-20 (Arpit, Cowork) — no feature waits on Codex; Claude authors **set 3**

*"A feature should not be held hostage because Codex needs to run a change. When
test data is needed and it is urgent, Claude creates it — you have the questions,
let me know when you need the answers. After the current run, Claude creates
another set — call it set 3 — and adds the `RF-118 / RF-119` shape of ids so
that it can be unlocked and we can move on."*

**What this changes here — inputs I-2 and I-3 stop being Codex's:**

| | before | now |
|---|---|---|
| **I-2** link-bearing + id-bearing seed documents | prompt 7, Codex | **set 3, Claude** — one authoring session, after phase A is filed (it is) |
| **I-3** paraphrases for W-175 | Codex | **a blind Claude session**, the same authoring shape; unchanged in substance, only the author |
| **I-1** prompt 9 | Arpit | unchanged — the key opens on his paste |

**Set 3, defined:**

- **Seed additions** in `work/golden/seed/` (Claude-written, committed): documents
  carrying **identifiers of the failing shape** — a shared prefix plus a short
  number, siblings that differ only in the number (`RF-118 / RF-119 / RF-120`,
  `PROJ-123 / PROJ-124`), in body text **and** in front-matter `doc_id:` — and
  the **link-bearing documents** prompt 7 specified (12 links among existing
  documents, 3 documents findable only by anchor text, one 4+ cluster), so W-191's
  census exits 0 and one ladder rebuild serves both.
- **Questions + answers** — `s3-001…`, the prompt-3 contract (same type mix, the
  answer-file format, `difficulty` computed not typed), **plus** an id-query per
  new identifier and the link-dependent questions W-161/W-176-gate-6 need.
- **The authoring route is L11 decision 6's, unchanged**: one session reads
  `seed/` and writes the seed additions; writes `questions/set-3.jsonl` (ids + text);
  hands the **answers to Arpit in the chat**, writes no key file, never runs a rung,
  and leaves. From that handoff set 3 is closed to Claude exactly as sets 1 and 2 —
  until prompt 9. **Every set 3 number is `informed`, permanently**, for the same
  reason set 2's are; after prompt 9 that is every number anyway.
- **Then:** prompt 4 rebuilds all eight rungs (set 3's documents enter `seed/`, so
  every rung carries them); phase A re-runs on the rebuilt ladder for all three
  sets — this is the *"run twice"* the default above already priced in; the first
  phase A stays filed as the pre-set-3 baseline.

⚠ **Codex is not excluded — it is not waited on.** If Arpit runs prompt 7 later,
its documents join `seed/` like any other and the ladder rebuilds again. Two
authors of seed documents make authorship visible, which was the point of two
sets; a third author does not undo it.

**Records this ruling touches (next Claude Code change, not this file):**
[SR-WORK-GOLDEN](../../records/0066_WORK-golden.md) decision 2 gains set 3 and
the standing rule *"an agent-authored set is created whenever a measurement would
otherwise wait on Codex"*; L11 decision 6's authoring carve-out is cited as
applying per set; `work/golden/README.md` §The two question sets becomes three;
prompt 3 is generalised to *"prompt 3 — Claude authors set N"* with a
**seed-additions** part, and prompt 7 is marked *optional, Codex, whenever*.

## What this item absorbs — eight rows become one

| was | what it owed | where it lives now |
|---|---|---|
| **W-136** | the sealed benchmark — phase 5 on seven unrun rungs, prompt 6 never run | **phases A and D**. Its file carries the ladder's history; nothing in it is restated here |
| **W-87** | the `judged` series; a clean-corpus `recall@k`; Part B on the ladder | **phase D** — the funnel per SR-WORK-QUALITY, per set, on set 1 for Part B |
| **W-190** | the first real difficulty run over a key | **phase D step 2** — `tools/golden-difficulty/` over both keys, per rung |
| **W-195** | the per-band breakdown | **phase D step 5** — filed beside every scored rung, never from `type` or from fux's results |
| **W-191** | link-bearing seed documents (prompt 7, Codex) | **input I-2** below — Arpit's; the ladder rebuild and re-run it forces is phase A's *"run twice"* hazard |
| **W-176** steps 4–10 | the measured abstention gates | **phase E** — each gate's pre-registration cites the D rows; steps 1–3 stay shipped, and the *build* of gates 4–9 remains a `fux build` item filed separately when D's rows exist |
| **W-161** measured arms | RRF boost + `related` tier, measured | **phase E**, after I-2; the build shipped 2026-09-15 and is not this item's |
| **W-175** | correction generalisation, arms (iii)→(ii)→(i) | **input I-3** + **phase E** — the harness is built; it waits on Codex paraphrases and nothing else |

**Not absorbed, deliberately:** W-168 / W-201 / W-202 / W-203 (identifier
analyzer — golden *seed*, not golden *answers*, and W-202 is green on its own)
and W-199 (fetcher routing). They stay as filed.

⚠ **The eight detail files are history, not authority, from this filing on.** Each
carries a one-line banner pointing here; Claude Code moves them to
`archive/open/` with their `archive/README.md` rows (queue rules 54–58) in the
change that runs phase A — the prompt at the end of this file does that.

---

## The order, and why it is load-bearing

```
A  outputs per rung, at HEAD  ─┐
B  three engines, same rungs   ─┤  frozen and committed, engine_commit on every row
                                ▼
C  Arpit pastes prompt 9 — L11 amended, key readable
                                ▼
D  one scoring pass over A + B  →  FINAL-SCORE.md
                                ▼
E  the gated items measure off D's rows
```

🔴 **A and B run and are committed BEFORE C.** The moment any Claude session
reads the key, every run made *after* that is `informed` in the strong sense —
the runner's family has seen the answers. Runs frozen before the lift keep the
one property the ladder was built for: nobody who produced the rows had the key.
Prompt 9 already records the weaker consequence — *"every golden number is
`informed`"* from the lift on — and this item does not argue with it; it simply
does all the running first, so the label describes the scorer and never the
runner.

⚠ **Two inputs are Arpit's and Codex's, and neither is on the critical path of
A, B, C or D.** They are listed as inputs, not blockers, so the ball stays 🟢:

| input | who | what it unlocks | if it never arrives |
|---|---|---|---|
| **I-1** prompt 9 pasted into Claude Code | Arpit | phase C, therefore D and E | A and B still produce every per-rung document and the unscored three-engine comparison; the final score does not exist |
| **I-2** set 3 seed additions (links + `RF-118`-shaped ids) | **Claude** (ruled 2026-09-20; was prompt 7, Codex) | W-161's arms, W-176 gate 6, W-168 step 8 (phase E) | those three stay `unmeasurable`, filed as such, and are never reported as null effects (SR-RS decision 23) |
| **I-3** blind paraphrases for W-175, arm (iii) | **a blind Claude session** (ruled 2026-09-20; was Codex) | W-175's measurement (phase E) | the harness stays built and unrun |

**Decision taken with a default — Arpit may override:** **A does not wait for
I-2.** If prompt 7 lands later, all eight rungs are rebuilt (prompt 4) and A is
re-run — roughly 4 000 `fux` calls, cheap in machine time — and the first A
stays filed as the pre-link baseline. Running A once, after I-2, saves that
re-run and costs the calendar; his call.

---

## ✅ PHASE A IS DONE — 2026-09-20 (Claude Code)

**Filed:** [`work/regression/2026-09-20-golden-ladder-outputs/`](../regression/2026-09-20-golden-ladder-outputs/report.md)
— 3 984 calls, all eight rungs, both sets, both verbs, at the frozen engine
`538f34978141a54b28b78b7ea76d36969cf63aa0`, `classification: informed`. Eight
`RUNG-NNNNN.md` documents, generated by
[`rung_outputs.py`](../../tools/quality-controls/rung_outputs.py) and never
written by hand. **No score, and no correctness column anywhere.**

**Every definition-of-done item met**, and the merge mechanics with it: the
eight absorbed files are in `archive/open/` with their `archive/README.md` rows.

🔴 **Three things this item did not predict, and each is worth reading before
phase B starts:**

1. **No rung would load at HEAD.** Every rung's `fux.toml` carried
   `meta = "hashed"`, which HEAD **refuses by name** after W-194. Phase B's
   `v1.0.0` and `v2.0.1` arms will hit the mirror image of this — those engines
   *require* the key that HEAD refuses — so **the arms cannot share a `fux.toml`**
   and the arms manifest has to say so per arm.
2. **This item's `b` hazard was wrong in its premise.** It said *"whatever `b`
   is at the frozen sha is the value"*; the **rung directories** carried
   `b = 0.75` from 2026-09-12 and would have overridden the engine default
   silently. That is W-144's upgrade trap, observed in the wild. Phase A set all
   eight to HEAD's measured `0.15` and declared it in the pre-registration.
   🔴 **Phase B must check each arm's rung copy the same way** — *"the default
   differs between arms; that IS the arm"* only holds if each arm actually runs
   at its own default rather than at whatever `fux setup` last wrote.
3. 🔴 **The 2026-09-16 `rung-00100` run's stated `b` is in doubt, and the check
   is no longer runnable.** It reports `b = 0.15`; that rung's `tune.toml` held
   `0.75` before it and holds it now, unmodified, and prompt 5 carries no
   `--no-tune`. **Its filed report was not edited.** ⚠ Phase A's own re-ingest
   overwrote the v3 index the check would need, so this is **Arpit's ruling**
   and no session can settle it by re-running anything.
   [ANALYSIS §1](../regression/2026-09-20-golden-ladder-outputs/ANALYSIS.md).

⚠ **Also unanticipated:** `--no-fetch` **alone** is refused across a format bump
— the engine names `--full` as the only route — so the re-ingest is
`ingest --full --no-fetch`, safe here only because no rung holds a `url:` record.

**Two findings reproduce and one is new.** `band: weak` ⇔ `answerable: false` on
3 984 of 3 984 rows, and the authorship gap at every rung; new is that the
confidence band's **middle is inert** — 43 of 43 transitions are
`grounded ↔ weak` from 100 documents up, and `partial` gains a member at no
point in the ladder. **That is a question for SR-CONFIDENCE, not a verdict**, and
it is phase D that can tell a well-behaved invariant from a dead branch.

**The row stays 🟢 — phase B is next**, and its pre-registration can now name the
sha phase A froze.

---

## Phase A — one document per rung, at HEAD

**Goal:** `work/regression/<date>-golden-ladder-outputs/RUNG-NNNNN.md`, one per
rung, eight in all — `rung-seed`, `00100`, `00200`, `00500`, `01000`, `02000`,
`05000`, `10000`. Each is the human-readable twin of prompt 5's hand-off: **one
section per question, both sets, set 1 first then set 2, never interleaved**:

- the id and the question text, verbatim from `questions/set-N.jsonl`
- what `fux ask` ranked — top 10 locators, in order, with band and `answerable`
- what `fux answer` returned — the answer text or the decline, the cited
  locators, the freshness verdict
- the `engine_commit`, rung, and `fux.index` version, once per document header

🔴 **No column for *correct*.** That column is born in phase D and nowhere
earlier. A per-rung document is an *output* record; it carries what fux did and
never what it should have done.

**Definition of done**

1. **Pre-registration first**, one for the eight-rung pass — the five-rung
   registration of 2026-09-12 does not cover this run (W-136 said so), and a
   registration across eight rungs is a new document. It names the frozen `HEAD`
   sha, the eight rungs, both sets, the two verbs, and states that **it files no
   score and predicts nothing about correctness** — its only claims are the
   surface ones (decline rate, band distribution, empty ranked lists, latency
   tail), per set.
2. **Corpus verification before any call** — `ladder_check.py` including check 4
   (`seed_drift`), every rung 100 % against its manifest. A drift stops the run.
3. 🔴 **Every rung is re-ingested at HEAD.** The rungs' stamps read
   `fux.index.v3`; W-194 moved HEAD to **v4** on 2026-09-20, so no committed
   rung index is readable by HEAD. One ingest per rung with `--no-fetch`, the
   `ladder/rung-NNNNN.index` stamps updated with version **and commit**, and the
   re-ingest filed as a step of this run, not hidden.
4. **Prompt 5's machine hand-offs are produced too** — `handoff-set-N.jsonl` and
   `predictions-set-N.jsonl` per rung. The `.md` is derived from them by a
   script committed under `tools/quality-controls/`, never written by hand, so
   the eight documents cannot disagree with the rows phase D scores.
5. **Blind, and said so** — `work/golden/seed/`, `questions/`, `ladder/` and the
   corpus are all that is read; the run's `report.md` states it.
6. **Filed under the per-run contract** — `report.md`, `ANALYSIS.md`, the
   `evidence/` tree, a row in `work/regression/README.md`, registry bump.
   `classification: informed` for the same reason the `rung-00100` run gave: it
   feeds a scored run and set 2 can never be blind.

**Hazards**

- The `rung-00100` run of 2026-09-16 was taken at `[bm25f] b = 0.15`, after the
  sweep. Whatever `b` is at the frozen sha is the value; the pre-registration
  writes it down, and A's `rung-00100` is a **new** run, not a re-file of the old.
- 249 questions × 2 verbs × 8 rungs ≈ **4 000 calls**; `rung-10000` alone is
  the slow one. One rung per session is fine; the pre-registration is one.
- The two hand-offs must stay apart in every file — one ambiguous id scores the
  wrong set (golden README).

## Phase B — three engines on the same rungs

**Goal:** the same eight rungs, both sets, run under **`v1.0.0`**, **`v2.0.1`**
and **`HEAD`** — HEAD's rows are phase A's, not a second pass — so that phase D
can score all three from one key and SR-WORK-BENCHMARK's seven captures are
filed for each pair.

**Arms**

| arm | install | index it writes | notes |
|---|---|---|---|
| **v1.0.0** | `pip install fux-engine==1.0.0` into its own venv | `fux.index.v1` | tag `v1.0.0`, 2026-08-22. No `pii.toml` concept, `fux update` not `ingest`, different flags — the runbook adapts the invocation per arm and records it |
| **v2.0.1** | `pip install fux-engine==2.0.1` into its own venv | `fux.index.v2` | the release on PyPI; the version string the rungs' stamps still carried until W-186 |
| **HEAD** | the frozen sha from phase A | `fux.index.v4` | phase A's rows |

🔴 **Three engines, three indexes, no shared bytes** — the asymmetry
[PRE-REG-BENCH-V1-VS-HEAD](../benchmark/PRE-REGISTRATION-V1-VS-HEAD.md) §1.1
states for two arms holds for three. Each arm ingests the same rung bytes into
**its own copy** of the rung directory under `fux-lab` (never into the rung's
committed `.fux/`), so the comparison is end-to-end — ingest → index → rank →
answer — and every claim is worded that way.

**Definition of done**

1. **A new pre-registration**, `work/benchmark/PRE-REGISTRATION-V1-V2-HEAD.md`,
   citing the 2026-08-28 one and not editing it (that document froze one sha and
   two arms; this is a new id space). It fixes: the three shas, the eight rungs,
   both sets, the three pairwise comparisons (`v1→v2`, `v2→HEAD`, `v1→HEAD`),
   and the primary metric per pair.
2. 🔴 **The power caveat is written before the first row.** Set 1 has 125
   questions and set 2 has 124, and the 2026-08-28 pre-registration's own table
   puts `N = 100–150` at power 0.17–0.60 for the effects a version bump
   produces. **The two sets are never pooled to reach 240** (golden README). So
   this benchmark is pre-registered as **descriptive per set**, with the paired
   floor of SR-RS decision 19 applied *per set* and any pair that does not clear
   it reported as *not distinguishable at this N* — never as *no difference*.
3. **The seven captures** ([SR-WORK-BENCHMARK](../../records/0053_WORK-benchmark.md)),
   per query and per arm: ranked lists; what moved between arms; `hit@k` at
   1/5/10/20/50 — **filled in phase D**, empty until then; the answer layer with
   the planted unanswerables — **also D**; committed index bytes per rung per
   arm — **now**; speed, arms interleaved on one machine, per L9 in
   `fux-benchmark` for timing only — **now**; and the HTML report, one CAP slide
   per capture, from `reports/TEMPLATE.html`, filed with D's numbers.
4. **The null control runs first** — the same arm twice on the same rung must
   report zero moved rows, or the harness is wrong and nothing else is measured.
5. **An arms manifest** before any A-vs-B row: venv path, `pip freeze`, the sha
   or wheel hash, the exact command line per arm.

**Hazards**

- `v1.0.0` may not ingest a rung as the rung is laid out (types allowlist,
  `.fux/sources` shape, no `pii.toml`). The runbook records what was adapted
  and the pre-registration says whether the adaptation is part of the arm.
- Rung indexes for old arms are **throwaway copies**; nothing writes into
  `~/my_programs/fux-lab/corpora/golden/rung-*/.fux/` except phase A's HEAD
  re-ingest.
- The `[bm25f] b` default differs between arms; that *is* the arm, not a knob
  to equalise.

## Phase C — Arpit opens the key (I-1)

**His step, one paste:** [prompt 9](../golden/prompts/9-claude-code-open-the-key.md)
into Claude Code. It amends L11 with his name and date, narrows decision 5 to
*write*, retires the guards that forbid reading, keeps the ones that forbid
committing, and regenerates the two byte-gated `CLAUDE.md` blocks. **Nothing in
this item restates prompt 9**; two things are added to it here:

1. 🔴 **Prompt 9 step 8 scores `rung-00100` only, from the 2026-09-16 hand-offs.**
   Under this item it scores **phase A's eight rungs and phase B's three arms**
   instead — the 2026-09-16 rows were taken at a different `b` and a v3 index and
   are superseded as a baseline, kept as history.
2. 🔴 **C runs after A and B are committed**, per the ordering above. If Arpit
   pastes prompt 9 first, A and B still run — but every one of their rows is
   then produced by a session whose family has had the key, and the per-rung
   documents say so in their header. The order is a recommendation he can
   overrule; the label is not.

Until he pastes it: **L11 stands as written.** No step of A or B opens, lists,
globs, stats, hashes or counts `work/golden/golden-answers/` or the older
spelling, and every recursive search over `work/` excludes `work/golden/`.

## Phase D — one scoring pass, one final score

**Goal:** `work/regression/<date>-golden-final-score/FINAL-SCORE.md` — the one
document Arpit reads — plus per-query rows for every rung × set × arm.

**Steps, in order**

1. **Join** each hand-off to its key on `id`; a row with no key line or a key
   line with no row is an error, not a skip.
2. **Difficulty** — run `tools/golden-difficulty/` over both keys: `difficulty_static`
   per question, `distractors_at_rung` per rung. 🔴 **The bands `d <= 1 / 2 / >= 3`
   freeze the moment the first number is filed by band** (SR-RS decision 10b) —
   if the distribution puts 80 % of questions in one band, move the thresholds
   *before* step 4 and record why, never after.
3. **Per-query verdicts**, per set, per rung, per arm: `hit@k` at 1/5/10/20/50
   against `relevant`; `primary` rank; `recall@k` over questions whose key
   declares the set `complete`; `abstain_correct` / `abstain_wrong` /
   `answered_wrong` on the answer layer; the answer-text verdict (`correct` ·
   `partial` · `wrong` · `declined`) with the evidence quote as the criterion.
4. **The funnel** ([SR-WORK-QUALITY](../../records/0056_WORK-quality.md)):
   `reachable → in window → placed → answered`, cost-weighted at the frozen
   `c = 2`, with the weight-stability interval and the risk–coverage curve
   beside every scalar. This is W-87's headline, computed for the first time on
   a key the measurer did not write (set 1) and, separately, on set 2.
5. **Per band** (W-195), per set, per rung — filed beside step 3's rows, never
   pooled across sets.
6. **Pooling**: top-5 hits outside `relevant` are judged and, if relevant, added
   with `key_version` advanced; the updated key goes **back to Arpit's
   directory, and nowhere else** — no agent commits a key byte (what remains of
   L11).
7. **FINAL-SCORE.md** — one table per set: rows = rungs, columns = arms, cells =
   the funnel headline with `hit@5` and `abstain_correct` beside it; one line per
   pairwise arm comparison naming the discordant count and whether it clears the
   d19 floor; the set-1 vs set-2 gap stated as the authorship measurement it is;
   every number labelled `informed` with the reason (scorer's family had the
   key; set 2 also authored by it).

**Definition of done:** every rung × set × arm has per-query rows; FINAL-SCORE.md
exists; the three-arm HTML report (phase B capture 7) is filed; W-87's `judged`
series has its first pinned run; W-190's bands are frozen or moved with a reason;
W-195's breakdown exists for every rung; `work/regression/README.md`,
`DOC-REGISTRY`, `IMPLEMENTATION.md` and the WORKLOG carry it.

🔴 **What D may never do:** derive difficulty from fux's results or from `type`;
pool the two sets; move a threshold after a number exists under it; report an
input-less measurement (links, paraphrases) as a null.

## Phase E — what D's rows unblock (filed as separate items when D lands)

Not this item's work; listed so nothing re-derives it:

- **W-176 gates 4–9** — each pre-registers both directions against D's
  unanswerable and answerable rows, builds behind its flag, measures, keeps or
  removes on its own row. **Gate 6 and W-161's arms need I-2 first.**
- **W-161's two arms** — after I-2 and a ladder rebuild; the paired floor on
  D-shaped rows.
- **W-175** — after I-3; the harness exists and applies no bar of its own.

---

## Records this item will have to touch

- [SR-LAW-11](../../records/0012_LAW-11-sealed-answer-key.md) — by prompt 9, Arpit's ruling named (phase C)
- [SR-WORK-GOLDEN](../../records/0066_WORK-golden.md) — decision 2's custody paragraph, the `blind`/`informed` split (C); decision 13 if bands move (D)
- [SR-RS](../../records/0133_predictions.md) — decision 11's classification for golden runs (C)
- [SR-WORK-QUALITY](../../records/0056_WORK-quality.md) — the first `judged` run pins model + prompt + version (D)
- [SR-WORK-BENCHMARK](../../records/0053_WORK-benchmark.md) — nothing to amend; the seven are the contract B and D satisfy

## What closes this item

FINAL-SCORE.md filed, all eight `RUNG-NNNNN.md` documents filed, the three-arm
report filed, and the eight absorbed files in `archive/open/` with their rows.
Phase E's items are opened from D's rows in the closing change; they are not
this item's definition of done.

---

## Claude Code prompt — the merge mechanics and phase A

**Model: Sonnet.** Paste from the root of the `fux` repo.

```
Read CLAUDE.md, records/0051_WORK-open-queue.md rules 8–12 and 54–58,
records/0060_WORK-session.md, and work/open/W-204-golden-outputs-scoring-and-version-benchmark.md.
L11 stands as written: never open, list, glob, stat, hash or count
work/golden/golden-answers/ or work/golden/golden-answer/, and exclude
work/golden/ from every recursive search over work/.

1. Close the eight absorbed items as "merged into W-204": move
   work/open/W-136-*.md, W-87-*.md, W-190-*.md, W-195-*.md, W-191-*.md,
   W-176-*.md, W-161-*.md and W-175-*.md to archive/open/ byte for byte
   (git mv), and add a row for each to archive/README.md §open/ naming
   2026-09-20 and W-204 as the successor. Their OPEN-WORK rows are already
   gone. Run tests/test_no_work_item_is_lost.py, tests/test_archive_law.py,
   tests/test_open_work_rows_are_short.py, tests/test_doc_links.py and
   tests/test_handoff_names_its_model.py; fix any link that pointed into
   work/open/ for those files by pointing it at W-204 or the archive.
2. Write the phase A pre-registration under
   work/regression/<today>-golden-ladder-outputs/PRE-REGISTRATION.md exactly
   as W-204 §Phase A item 1 specifies, freezing HEAD's sha and the current
   [bm25f] b, and commit it before any run.
3. Run ladder_check.py with check 4 on all eight rungs in
   ~/my_programs/fux-lab/corpora/golden/. Stop on any drift.
4. Re-ingest every rung at HEAD with --no-fetch (fux.index.v4), update
   work/golden/ladder/rung-NNNNN.index with version and commit, and file the
   re-ingest as a step of the run.
5. Write tools/quality-controls/rung_outputs.py: it takes a rung's
   handoff-set-1.jsonl and handoff-set-2.jsonl and emits RUNG-NNNNN.md in the
   shape W-204 §Phase A specifies — set 1 then set 2, one section per
   question, no correctness column. Unit-test it on two synthetic rows.
6. Execute prompt 5 on rung-seed and rung-00100 first; confirm the .md
   renders; then the remaining six, one per commit, slowest last.
7. File the run under the per-run contract, classification: informed, with
   the surface-claim analysis the pre-registration allows and nothing about
   correctness. Row in work/regression/README.md, DOC-REGISTRY bump,
   IMPLEMENTATION.md, WORKLOG entry, NOW.md. Update W-204 §Phase A to done
   and leave its row 🟢 for phase B.
8. Run both suites whole before believing any of it is done.
```

Phase B gets its own prompt when A is filed — its pre-registration depends on
the sha A froze. Phase C is prompt 9. Phase D's prompt is written after C
lands, because its first line is a path no prompt may name until then.
