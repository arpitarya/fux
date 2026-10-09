---
type: Pre-registration
description: "The frozen bar for W-257's full enriched rung (Arpit, 2026-10-10: the full rung, instructions unchanged). Three questions on set-5-claude at copies of the gen-4 rung-01000, all judged at hit@1 per W-168's endpoints and SR-RS d19's paired floor (verdict.py): B-108, does doc2query help (unfiltered against none, with a placebo arm); B-109, does the --check filter help or hurt (filtered against unfiltered); B-110, does partial coverage tilt ranking (25 and 50 percent against 100 percent, on the questions the un-enriched part answered). Written before the author runs and before any number exists."
run: 2026-10-10-enriched-rung
item: W-257
filed: 2026-10-10
measured: "not yet"
classification: informed
status: frozen
---

# Pre-registration — the enriched rung, W-257 (B-108 · B-109 · B-110)

## What is being asked

1. **B-108, doc2query.** If every document carries 5–10 questions that a
   searcher might type, written by a blind author, do more questions
   find their document at rank 1?
   ([SR-ENRICH](../../../records/0137_enrich.md) d15: *"BUILT AND UNPROVEN"*.)
2. **B-109, the filter.** `--check` refuses a question that does not retrieve
   its own document. Does removing those questions help ranking or hurt it?
   (d16: *"too small to see"* at 2 of 98. The pilot refused 31.8 %.)
3. **B-110, the tilt.** When only part of the corpus is enriched, does that part
   take rank 1 from questions the rest of the corpus was answering? (Main d6:
   *"a measurement, not an opinion"*.)

⚠ **Nothing has run.** The full rung is not yet authored. This file fixes the
arms, the data, the endpoint and the verdict table **before** the authoring
session exists, so none of them can be chosen after a number exists
([SR-RS](../../../records/0133_predictions.md) d10b).

## Classification — `informed`, and why the blind author does not change that

The enrichment is authored **blind** (W-257's protocol; SR-RS d11 is satisfied
for that artifact). **The run is still `informed`**, because the only scorable
set at this rung is `set-5-claude`. That set is Claude-authored, and
[L11](../../../records/0013_LAW-11-sealed-answer-key.md) d7 makes every number
on an agent-authored set `informed`, permanently. So every verdict below is
**not a generalisation estimate** (SR-RS d13). This is the same footing as every
W-168 step and W-236 Part B.

⚠ **This is a finding against W-257's premise, recorded here rather than
discovered later.** The item expected a blind author to buy B-108–B-110 *a
delta* under SR-RS d12. No set that exists today gives a blind run. What the
blind author does buy is that **the enrichment was not fitted to the set**.
Every number stays informed only because Claude wrote the questions it is
scored on.

## The endpoint — W-168's, unchanged

| | measure | gates? |
|---|---|---|
| **primary** | **`hit@1`** on `set-5-claude`, all 90 questions, per row from `score.py` | ✅ |
| secondary | `primary@1`; `hit@5`; `hit@10`; evidence quoted | ❌ reported beside, both directions |

**`k = 1`, named.** That is what voided the 2026-09-05 run (its bar never named
`k`). Steps 1, 4, 8 and 9 and W-236 were judged at the same endpoint.
**Every paired bar is SR-RS d19 at the observed discordant count, computed by
[`verdict.py`](../../../tools/quality-controls/verdict.py) and never by hand**
(d19a). A net below 6 never clears, at any count. No set-wide tag pool exists
for enrichment, so the whole set is the pool. (The key's pools are step tags.)

## The arms

Every arm is a **`cp -a` copy** of `fux-lab/corpora/golden/rung-01000` at
**`e776146f`**, never the rung itself (corpora are kept). Every arm is ingested
`--full` by **one engine commit**, which the report records with each arm's
index root (SR-RS d21c). Arms differ **only** in `.fux/sources/dirs` and
`.fux/enrich/`. `diff -r` between any two arms must show nothing else.

| arm | `dirs` | `.fux/enrich/` |
|---|---|---|
| **`none`** | as shipped | empty |
| **`declared`** | `enrich=true` on all four lines | empty |
| **`unfiltered`** | `enrich=true` on all four lines | **every file the author wrote, byte for byte** |
| **`filtered`** | the same | the same files with **every question line that first-pass `--check` refused removed**, and nothing else changed |
| **`placebo`** | the same | [`placebo.py`](../../../tools/quality-controls/placebo.py) output over `unfiltered`'s files: matched file count, line count and length, one shared pool |
| **`cov-25`** · **`cov-50`** | the same | `unfiltered`'s files for the subsets `S_25`, `S_50` only |

- **`cov-100` is `unfiltered`.** It is not built twice.
- **Scope is the full rung: all four `dirs` lines**, `seed`, `seed/archive`,
  `ext` and `ext/archive`. That is every indexed document, so `unfiltered` is
  100 % coverage. If `--plan` refuses `enrich=true` beside `archived=true`, the
  run **stops**. Scope is not narrowed after the fact.
- **The subsets.** Order every document that has a file in `unfiltered` by
  `sha256(loc as UTF-8)`, ascending. `S_25` is the first `ceil(0.25 n)`, `S_50`
  the first `ceil(0.50 n)`. The subsets are nested, deterministic and seedless,
  the same rule as the sealed subset (SR-RS d15).
- **The filter runs once**, on the first pass, on `unfiltered`'s files. That
  `check.txt` goes under `evidence/`. **No refused question is rewritten** (the
  ruling: instructions unchanged). A rewrite would delete B-109's arm.
- **The pilot's 94 files are not reused.** One author writes the whole rung, so
  the arms do not mix two sessions.
- If `placebo.py` cannot match **line count** on question-shaped bodies, the run
  **stops** and the gap goes to Arpit. The control is not loosened to fit.

## The authoring, as ruled — fixed here, not re-opened

**One fresh blind session, launched by Arpit in `fux-lab`**, under W-257's
protocol. It writes the full rung, runs `--check` once, reports and ends. **No
session that has read this file, any question set, any score or any capture
gives that session any content.** A session that captures arms never authors,
and the author never captures. The run records the author's model stamp, the
wall clock and the token cost as Arpit reports them.

## The data

| | |
|---|---|
| question set | **`set-5-claude`**, 90 questions, sha256 at §Freeze |
| decoys | [`decoys.jsonl`](../../../tools/quality-controls/decoys.jsonl), 15. **Reported beside, gating nothing**: `grounded` count per arm |
| corpus | gen-4 **`rung-01000`** at `e776146f`, copied per arm as above |
| harness | `tools/quality-controls/golden_run.py --sets 5-claude --arm <arm> --engine-commit <c> --fux <pinned>`: `ask --json --band --why --top 10` and `answer --json` |
| scoring | `tools/golden-score/score.py`, **started by Arpit from his own shell** ([L11](../../../records/0013_LAW-11-sealed-answer-key.md)). No agent invokes it |
| tilt join | `evidence/tilt.py`: committed **before any arm is scored**, its sha256 in the report. It implements §B-110 and nothing else, and **prints counts only, never a document name next to a hit** |

## Gates that run before any verdict is read

- **G0 — declaration is a no-op.** `declared` and `none` must have **the same
  index root**. If they differ, the run stops as an engine defect: a
  declaration without files must not move a byte.
- **G1 — every file is valid.** `--check` on `unfiltered` reports no malformed
  file and no sha mismatch. A malformed file is ignored by ingest (d9), which
  would silently shrink coverage. Any one stops the run.
- **G2 — headroom, from the `none` arm** (SR-RS d22f). The improvement
  direction needs at least 6 answerable questions that miss rank 1. The
  2026-10-09 capture of the same set at the same rung gives **36** (81
  answerable, 45 hit). The regression direction needs at least 6 rank-1 hits
  (**45** at that capture). Below 6 in a direction makes that direction
  **INCONCLUSIVE** (d22d), never *no detected change*.
- **G3 — the filter is visible** (B-109). First-pass `--check` must refuse
  **at least 10 %** of `unfiltered`'s questions. Below that, B-109 reports
  *"too small to see"* again and gives no verdict. (The pilot refused 31.8 %;
  d16's run refused 2 %.)

## The verdict tables, frozen

Each table reads `hit@1`, per question, on `set-5-claude`. *Net* is the
treatment arm's wins minus its losses against the comparison arm. *Clears* means
`verdict.py` gives p < 0.05 at the observed discordant count (SR-RS d19).

### B-108 — doc2query: `unfiltered` against `none`, with `placebo` as the control

| outcome | condition |
|---|---|
| **PASS** | `unfiltered` vs `none`: net > 0 and clears; **and** `placebo` vs `none` does not clear in the improvement direction |
| **FAIL: hurts** | `unfiltered` vs `none`: net < 0 and clears |
| **NO DETECTED CHANGE** | `unfiltered` vs `none` clears in neither direction, with G2 headroom in both |
| **INCONCLUSIVE → Arpit** | `placebo` clears in the improvement direction (the gain may be **presence of text**, not content); or headroom is zero in a direction; or anything this table does not name |

Reported beside it: `filtered` vs `none` (the shipped filter applied), the
same table read but gating nothing.

### B-109 — the filter: `filtered` against `unfiltered`

| outcome | condition |
|---|---|
| **TOO SMALL TO SEE** | G3 fails. No verdict |
| **FILTER HELPS** | net > 0 and clears: the refused questions were pulling **other** documents up |
| **FILTER HURTS** | net < 0 and clears: the refused paraphrases were bridging a vocabulary gap |
| **NO DETECTED CHANGE** | clears in neither direction, with headroom in both |
| **INCONCLUSIVE → Arpit** | zero headroom in a direction, or anything unnamed |

⚠ **On either clearing outcome, what `--check` does next is Arpit's.** It
reports and never rewrites (d16), and this run changes neither behaviour nor the
`self_retrieval_k` default.

### B-110 — the tilt: `cov-c` against `cov-100`, on the questions the un-enriched part answered

For `c ∈ {25, 50}`:

- **`Q_out(c)`** = the questions whose **rank-1 document in the `none` arm is not
  in `S_c`**. These are questions the un-enriched part of the corpus answers or
  holds at the top before anything is enriched. The set is read from harness
  output, so no key is needed to build it.
- On `Q_out(c)`, `cov-c` is paired with `cov-100`. A **loss** is a question that
  hits at rank 1 under full coverage and misses under partial coverage. The
  comparison is against `cov-100`, not against `none`, so doc2query's own
  effect cancels and only the partial-coverage difference remains.

| outcome at `c` | condition |
|---|---|
| **TILT** | losses − wins on `Q_out(c)` clears |
| **NO DETECTED TILT** | it does not clear, with headroom in both directions on `Q_out(c)` |
| **INCONCLUSIVE → Arpit** | zero headroom on `Q_out(c)` in a direction, or `\|Q_out(c)\| < 6` |

**What d6 reads off it:** the tilt is **small**, so `ctx` keeps its own tune key
as d6 conditions, only if the result is **NO DETECTED TILT at both 25 and
50**. A TILT at either coverage leaves d6's condition unmet, and what happens
to `ctx`'s weight is Arpit's.

**100 %** has no un-enriched part, so it has no tilt row. Its number is B-108's.

**Reported beside, gating nothing:** for `c ∈ {25, 50}`, the share of the 90
rank-1 documents that fall in `S_c` under `none` and under `cov-c`, beside
`|S_c| / N`. This shows the size of the shift. It is not a verdict.

## Reported beside every arm, gating nothing

Per arm: `hit@1`, `hit@5`, `hit@10`, `primary@1` totals and evidence quoted.
Per paired comparison: wins, losses, discordant count and p-value, plus
**headroom per endpoint and per direction** from the comparison's baseline arm
(SR-RS d22a–d22f). Also: questions per document; the refusal count per document;
decoy `grounded` per arm. Per-query rows go under `evidence/`, one row per
question per arm (SR-RS d19, "record all the questions").

## Both directions, stated before the numbers

| | helps | hurts |
|---|---|---|
| B-108 | a reader's word (*"breach"*, *"GPS"*) now reaches the document that says *"excursion"*, *"telematics"* | about 8 000 questions add vocabulary to every document, so a question's words now appear in **many** documents' `ctx`, and the right document's lead shrinks |
| B-109 | removing questions that *"pull OTHER documents up"* (the filter's own footer) ends that pull | the refused lines are the paraphrases doc2query exists for (the pilot's ANALYSIS §2). Removing them removes the gain |
| B-110 | — | an enriched document wins a question whose right answer is un-enriched. The likelier direction, by d6's own argument |

## What this run may NOT do

1. **Move any number above**, add an arm, or change `k`. SR-RS d10b.
2. **Rewrite a refused question**, or re-run `--check` and take the second pass.
3. **Let the author run anything but `--plan` and `--check`**, or let a capturing
   session author. SR-RS d11.
4. **Change `fux enrich`**, `self_retrieval_k`, or any ranking weight.
5. **Proceed past a STOP** (G0, G1, the `archived` refusal, the placebo gap).
6. **Be adjudicated by the session that captures the arms.** Ambiguous → Arpit.
7. **Open, read or be handed an answer key**, or invoke `score.py`. L11.
8. **Edit a ladder rung in place.** Copies only.
9. **Claim anything at 10 000 documents.** [SR-WORK-SCALE](../../../records/0057_WORK-scale.md).

## What each verdict changes (W-257 DoD 3–4, after the numbers)

- **SR-ENRICH d15** is rewritten from *"BUILT AND UNPROVEN"* to B-108's verdict.
  **d16** is rewritten to B-109's. **Main d6** is rewritten to B-110's. Then
  `sr-hash.py --write`.
- **B-108, B-109, B-110** leave `BACKLOG.md` on any verdict other than
  INCONCLUSIVE.
- **B-245's second condition** (*doc2query's ceiling measured*) is met by a
  B-108 PASS, FAIL or NO DETECTED CHANGE. It is not met by INCONCLUSIVE.
  B-245 still needs a rank-contract corpus.

## Freeze — filled before the commit that freezes this file

| | |
|---|---|
| `set-5-claude.jsonl` sha256 | `fb914925077f5a53a184685fc52eed5710ca758b9d9b0aafd9dbe3e5cd158a3a` |
| rung-01000 head · index root (gen 4) | `e776146fc4c51c5801c47144a058cf0eb8644145` · `5038b32b398d48c2c93cb6a05bd412427a3ee8bcd7e297449b90eb0d562acaca` |
| `rung-01000` `dirs` at that head | `seed` · `seed/archive archived=true` · `ext` · `ext/archive archived=true` |
| headroom at the 2026-10-09 capture ([report](../2026-10-09-golden-set-5-rung-01000/report.md)) | `hit@1` 45 of 81 answerable: improvement **36**, regression **45**. G2 re-reads it on `none` |
| the pilot ([capture](../2026-10-09-enrich-pilot-gen4/report.md)) | 745 questions over 94 `seed` documents; **31.8 %** refused on the first pass. Not an arm, and no delta is stated against it |
