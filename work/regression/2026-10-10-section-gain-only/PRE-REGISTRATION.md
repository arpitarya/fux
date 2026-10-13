---
type: Pre-registration
description: "The frozen bar for W-269, section records' second mechanism: B2's GAIN-ONLY variant, S_doc + λ · max(0, best section − the document as one unit), so a sectionless document gains nothing. W-236's bar unchanged — set-5-claude at a re-ingested copy of gen-4 rung-01000, hit@1 on the step10_section pool read from counts, zero new rank-1 misses, G0/G1/G2 — with section_weight ∈ {0.25, 0.5, 1.0, 2.0} and one added gate, G3: every sectionless document's term at every λ equals λ = 0. Written before any W-269 build code."
run: 2026-10-10-section-gain-only
item: W-269
filed: 2026-10-10
measured: "not yet"
classification: informed
status: frozen
---

# Pre-registration — section records, gain-only (W-269)

## What is being asked

**When the short-document bias is removed, does a section term put a long
document whose answer sits under one heading at rank 1?** W-236 asked it with
B2 as built and failed (drift) at every weight
([verdict](../2026-10-10-section-records/VERDICT.md)). Its bar had named the
likelier failure in advance: a sectionless document is its own single section,
so it gained about `λ ×` its whole body and heading score. This run measures
whether any headroom remains once that credit is zero by construction.

⚠ **Nothing is built.** This file fixes the mechanism, the arms, the data, the
gates and the bar **before** the build, so the build cannot choose any of them
after a number exists ([SR-RS](../../../records/0133_predictions.md) d10b).

⚠ **Read this beside its predecessor.** This is the **second mechanism on the
same 90 questions**, and the session writing it has seen W-236's per-query rows.
A PASS here is weaker evidence than W-236's FAIL was. The grid and the form
below are fixed before any arm, and that is the only defence against the
second look.

## The mechanism, fixed before the build

[SR-SECTIONS](../../../records/0161_sections.md) decision 5 as amended on
2026-10-10 (commit `113ae3b4`, Arpit's ruling on W-269). **The build may not
deviate from it.** If it proves unbuildable as written, the build stops and the
change goes to the record first.

```
G(d)  = max(0, max_k S_sec(d#s_k) − S_self(d))
S(d)  = ( S_doc(d) + λ · G(d) ) · w(d)
```

| | value |
|---|---|
| `S_sec` | unchanged from W-236: the same `score_record`, body and heading slots, the document `df` and `n`, the section `avg_wlen` |
| `S_self` | the document's own record cut to the body and heading slots, scored the same way under the same section statistics |
| sectionless | `G = 0`, and **no arithmetic runs**: the score is byte-identical to `λ = 0` |
| `section` key | the section that earned the gain, or `null` when `G = 0`; present only when `λ ≠ 0` |
| everything else | W-236's: the plane, the section rule, the record, `_format` `fux.index.v8`, the accelerator's skip ceiling (still a bound, since `G ≤ max_k S_sec`) |
| `b` | **untouched** (`0.15`). Raising it is a separate ruling |

**Held for every arm:** the engine, the index root, the copy's `tune.toml` apart
from `section_weight`, the corpus and the questions.

## The arms

**Baseline:** `section_weight = 0.0` (`sw-0.0`). **Treatment:**
`section_weight ∈ {0.25, 0.5, 1.0, 2.0}`, tried in that order (`sw-0.25`,
`sw-0.5`, `sw-1.0`, `sw-2.0`).

- **Why this grid, and why not W-236's.** The gain is a difference, so it is
  smaller than the full section score that W-236's top value added. At
  `λ = 1.0` a document is credited the whole of what its best section scores
  beyond it, which is the natural midpoint. `2.0` is one doubling above it,
  because a smaller term needs a larger weight to move rank 1 at all. `0.25`
  and `0.5` are the halvings below. **Four values, as W-236 had**, so the
  exposure to clause 2 across the grid is the same. **No value is added after a
  number exists.**
- 🔴 **Every arm runs on a COPY**, never the rung. Source:
  `fux-lab/corpora/golden/rung-01000` at **`e776146f`**. The base is a `cp -a`
  to `fux-lab/arms/runs/gain-base/rung-01000`. On it: `fux doctor --fix` (every
  key it writes is recorded), then **`fux ingest --full`** with the W-269 build
  engine. Each arm is a `cp -a` of that base to
  `fux-lab/arms/runs/gain-sw-<λ>/rung-01000`, with only the `section_weight`
  line changed. `diff -r` must show nothing else. W-236's `sw-*` copies are not
  reused and are not written to.
- Every arm resolves all 90 questions against **one** index root at **one**
  engine commit, and the report records both
  ([SR-RS](../../../records/0133_predictions.md) d21c).
- **W-236's arms are not arms of this run.** No delta is stated against them.
  Its `sw-0.0` capture is used only by G0.

## The data

| | |
|---|---|
| question set | **`set-5-claude`**, 90 questions, `work/golden/questions/set-5-claude.jsonl`, sha256 at §Freeze |
| corpus | gen-4 **`rung-01000`** at `e776146f`, copied and re-ingested as above |
| harness | `tools/quality-controls/golden_run.py --sets 5-claude --arm sw-<λ> --engine-commit <build> --fux <pinned>`, unchanged: `ask --json --band --why --top 10` + `answer --json` |
| scoring | `tools/golden-score/score.py`, **started by Arpit from his own shell** ([L11](../../../records/0013_LAW-11-sealed-answer-key.md)); no agent invokes it |
| decider | [`evidence/decide.py`](evidence/decide.py), frozen by hash at §Freeze: W-236's decider with the arm names changed and a G3 refusal in front |

## The endpoint — W-236's, unchanged

| | measure | gates? |
|---|---|---|
| **primary** | **`hit@1`** on the key's **`step10_section`** pool | ✅ |
| secondary | **`section@1`**, read as the scorer's `evidence_quoted` | ❌ reported beside it, both arms, both directions |

The pool is read **from counts only**, exactly as W-236's
[§Reading the pool from counts](../2026-10-10-section-records/PRE-REGISTRATION.md#reading-the-pool-from-counts--why-no-tag-file-exists)
says: with clause 2 holding, pool wins = baseline `miss@1` − treatment
`miss@1`, losses 0; with clause 2 failing, the split is `undetermined` and never
needed. No session sees which questions are tagged.

## Gates that run before any arm is read

**G0 — byte identity at `0.0`.** The W-269 build at `sw-0.0` on its re-ingested
base, against **W-236's `sw-0.0` capture**
(`2026-10-10-section-records/evidence/sw-0.0/rung-01000/`), by
[`evidence/g0.py`](evidence/g0.py). **All 90 hand-off and prediction rows equal
except `ask_ms`, `answer_ms`, `arm`, `engine_commit` and `repo_head`.** W-236's
G0 tied that capture to the pre-section engine (0 of 90), so this ties the W-269
build to it as well. One difference stops the run as a build defect.

**G1 — the size bar at `rung-10000`, unchanged.** W-236's
[`g1.py`](../2026-10-10-section-records/evidence/g1.py), unchanged (sha256 at
§Freeze), on a `--full` copy of `rung-10000` at `99fe0b4` ingested by the W-269
build. The bars are W-236's: section ÷ document plane **≤ 2.0**; total
**≤ 55 000 000 B**; largest file **≤ 1 048 576 B**; totality misses and `nsec`
disagreements **0**. The W-269 build changes no ingest code, so this is
expected to reproduce W-236's `g1.json`. A different number is a build defect,
not a re-measurement.

**G2 — the pool.** The baseline arm's score must show
`pools.step10_section.reorderable@1 ≥ 6`. Below 6 stops before any verdict
(W-219). `decide.py` reads it first.

**G3 — the diagnosis, tested directly (added by W-269).** At every treatment λ,
**every sectionless document's section term is zero and its BM25F term
contributions are byte-identical to `λ = 0`**, on every one of the 90 questions,
over every candidate `rank()` scored (`ask --json --why --top 1000`, the whole
rung). By [`evidence/g3.py`](evidence/g3.py), which states the three conditions.
It compares `rank()`'s term rather than the final `score`, because the
proximity uplift applies only inside the rerank window and moves with the
window, not with the section term. **One failure stops the run as a build
defect**, and `decide.py` refuses to run without a G3 PASS.

## The decision rule — W-236's, frozen, unchanged

**The verdict table governs; the selection rule applies only to values the
table admits** ([SR-RS](../../../records/0133_predictions.md) d18).

For each treatment value, against `sw-0.0`, on the same engine and index:

1. **Gain.** On the `step10_section` pool, `hit@1` wins minus losses clears
   [SR-RS](../../../records/0133_predictions.md) d19 at the observed discordant
   count, computed by [`verdict.py`](../../../tools/quality-controls/verdict.py)
   and never by hand (d19a).
2. **No new misses.** **No question in the set, tagged or not, that hits at
   rank 1 in the baseline arm misses there in the treatment arm.** One loss
   fails the value.

| outcome | condition | consequence |
|---|---|---|
| **PASS** | some value clears 1 **and** 2 | the **first** such value, ascending, is the candidate `section_weight` default. **Nothing merges** until Arpit rules the size question (below) |
| **FAIL: drift** | no value holds 2 | `section_weight` stays `0.0`; the step closes as measured |
| **FAIL: no gain** | some value holds 2, and every such value has a net ≤ 0 on the pool | the same |
| **INCONCLUSIVE** | a value holds 2 with a positive pool net below d19's floor, and no value clears both; or anything this table does not name | written up with per-query rows under `evidence/` and **handed to Arpit** |

**On FAIL:** both mechanisms' results are recorded in SR-SECTIONS and the compare
doc, and the branch is Arpit's. **On PASS:** nothing merges until
[ANALYSIS §2](../2026-10-10-section-records/ANALYSIS.md)'s size question is
ruled by Arpit. On this repository the section plane is 8.0× the document plane
(`.jsonl` 75.6 %). Then SR-SECTIONS is accepted in the merging change, with the
`_format` bump and a **Breaking** CHANGELOG line.

**Reported beside every arm, gating nothing:** W-236's list, unchanged —
`section@1` wins and losses, `hit@1` and `primary@1` wins and losses on the
whole set, `hit@5` and `hit@10` totals, the `other` pool's `miss@1`, the
fraction of hits whose index `section` differs between arms, and headroom per
[SR-RS](../../../records/0133_predictions.md) d22 from the **baseline arm**
(d22f).

## Both directions, stated before the numbers

| direction | what it would look like | what it means |
|---|---|---|
| **helps** | a long document whose answer is one heading moves from rank 2–10 to rank 1; no incumbent rank-1 hit moves | the dilution was real and B2's failure was the short-document credit, not the absence of headroom |
| **hurts** | a long document with one dense, off-topic section overtakes a right document, sectioned or not | concentration in one section is not evidence of relevance at `b = 0.15`; **the likelier failure now**, because only multi-section documents can move and every one of them competes |
| **does nothing** | no question flips at any value | `b = 0.15` already removed the penalty, as the compare doc's *low confidence* said. **Post-hoc, and not a pass** |

## What this run may NOT do

1. **Move any number above.** SR-RS d10b.
2. **Report *the best weight*.** First-that-clears, ascending.
3. **Sweep anything else**: not the section rule, not `b`, not the field weights,
   not the form of `G`.
4. **Be adjudicated by the session that captures the arms.** Ambiguous → Arpit.
5. **Proceed past a STOP** (G0, G1, G2, G3).
6. **Open, read or be handed an answer key**, or invoke `score.py`. L11.
7. **Edit or re-ingest a ladder rung in place**, or write to W-236's arm copies.
8. **Merge the build to `main`**, before the verdict or after a PASS, until
   the size question is ruled.

## Freeze — filled before the commit that freezes this file

| | |
|---|---|
| `set-5-claude.jsonl` sha256 | `fb914925077f5a53a184685fc52eed5710ca758b9d9b0aafd9dbe3e5cd158a3a` |
| `evidence/decide.py` sha256 | `514f4784c2d1fab892bebdf3b25f196143452800431727bd6b0e4bfd87f80a6d` |
| `evidence/g0.py` sha256 | `00e07be6834571b14abc98b40b0bdfee125cc5faeef41e062654567aa79c3aef` |
| `evidence/g3.py` sha256 | `12e19e39299b36963ea63a3e096227e5b9a61deb6218d7f3bc54fee4e641c070` |
| W-236's `evidence/g1.py` sha256 (G1, reused unchanged) | `000939d2680ae423115d569dbfdcd08d688717d4768841df48a8a33c70c2df71` |
| the mechanism | SR-SECTIONS decision 5 at `113ae3b4` |
| the base engine | W-236's build `f2a139fd`, with `main` merged in (`81b0989a`); no W-269 build code exists at this file's freeze |
| rung-01000 head (gen 4) | `e776146fc4c51c5801c47144a058cf0eb8644145` |
| rung-10000 head | `99fe0b4` |
| the pool at W-236's baseline | 23 reorderable@1 (`sw-0.0`, Arpit's score, 2026-10-10). G2 re-reads it on this run's baseline arm |

**Headroom at W-236's baseline:** improvement **23** on the pool; regression
**45**, every rank-1 hit in the set being exposed to clause 2. ⚠ The verdict
reads this run's baseline arm (d22f), not W-236's.
