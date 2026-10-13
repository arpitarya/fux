---
type: Handoff
name: W-278
description: "Arpit's ruling (2026-10-11, Cowork): the section term's third form — the best section scored AS A STANDALONE DOCUMENT (document average length, its parent's title/path/ctx folded in) and combined by max, λ ≤ 1 — replacing both the section-average yardstick and the concentration gate; with the latency fix the L13 guardrail needs; measured on set-7-claude (W-277, R10 re-amended) under one pre-registered decided arm."
item: W-278
filed: 2026-10-11
ball: arpit
---

# W-278 — section term v3: the best section scored as a document, combined by max

**Status: RULED 2026-10-11 (Arpit, Cowork): *"update the work items to go with
the suggestive approach"* — this item is the approach. ✅ DoD 1–3 landed
2026-10-13 (Claude Code, Opus 5.5)** — the record, the latency fix (+68.6 ms
standalone at gen-5 `rung-10000`, against 100), the build on both readers.
W-277's data is placed (2026-10-12: generation 6, seeds 113–182,
`set-7-claude`, 165 questions; W-277 closed). W-270 closed on this ruling; its
STOP stands.

**Ruled 2026-10-13 (Arpit, Claude Code), before the build: *own-match only*.**
`max_k` runs over the sections that carry a query term in their **own** body or
heading; a section that would match only through its parent's title, path or
ctx is not scored, so a document matching only in its title gains nothing
(SR-SECTIONS decision 5). The alternative, every section, would have scored a
title-only match as the document's shortest section: a length leap of its own.

**Supersedes this item's first form (filed earlier on 2026-10-11)**: *"bonus only
when the answer is concentrated, whole document on its normal yardstick"*. Both of
those changes are withdrawn — §Why below shows the first leaves the
over-credit in place at every λ and the second has a hole. What remains from
the first form is the latency fix (DoD 2) and the measurement shape.

**Model:** **Claude Code, Opus** for phases 1–4 (the record, the build and the
bar — no test catches a bad bar); **Sonnet** for the capture against the
written procedure; **Arpit** scores; the decider is a frozen script.

## Why — what the two failed terms actually reward (no key read)

Read from the arms' own `ranked` lists and the runtime document table — never
from a score row (L11's named door stays shut).

- **Both terms lift long documents indiscriminately.** Rank-1 changes at
  λ = 2.0: set-5 (W-269) 24 changes, the incoming document a 1 000–2 400-token
  manual in **19**, the outgoing one short in 23; set-6 (W-270) 21 changes,
  incoming long in **17**, outgoing short in 15. Wins and losses are the same
  move; which side it lands on depends only on whether the manual happened to
  be the answer.
- **The yardstick is the cause.** `rank._section_gain` (`b4d961cd`) scores
  `whole` — the document as one unit — against the **section** average length:
  31.5 tokens on gen-5 `rung-01000` (4 247 units), against a **document**
  average of 134. A 2 000-token manual is 64× "too long" on that scale, so
  `whole` collapses to ≈ 0.16·idf per term and the "gain" is nearly the full
  section score. Per matched term (idf = 1, tf = 1, `b` 0.15, `k1` 1.2):

  | unit | score |
  |---|---:|
  | short competitor, 150 tokens, tf 1 · tf 2 | **0.99** · 1.37 |
  | the manual's own document score | 0.47 |
  | the manual + W-269's gain at λ 2 (section 0.81 − whole 0.16, ×2) | **1.77** |
  | the manual + the first form of this item (whole on the document average: 0.81 − 0.47, ×2 · ×1) | 1.16 · 0.82 |
  | **the manual's best section scored as a document (max form)** | **1.01** |

  A manual that mentions a word once, in any one of 25 sections, outranks a
  short document that mentions it twice. That is the shape of every loss.
- **W-236 and W-269 are the same term for a long document.** Gain-only removed
  the *short*-document credit (G3) and nothing else: with `whole` ≈ 0 the gain
  is the section score, i.e. B2 again. The additive form double-counts the
  same matches.
- **The first form of this item does not fix it.** `whole` on the document
  average still gives 1.16 at λ 2 (beats a tf = 1 competitor) and 0.82 at λ 1
  (loses to it): no λ equals *fair*. The concentration gate has a hole — one
  rare term matched once in one section is 100 % concentrated.
- **The max form has no such knob.** The section scores exactly what an equally
  matching short document scores (1.01 against 0.99), and a long document can
  never leap over a short one that matches better; the other terms, the title
  and the tie-breaks decide. This is the document-by-best-passage model of
  Callan (1994) and Kaszkiel & Zobel (1997), on the same yardstick as the
  document plane.

## The mechanism (to be written into SR-SECTIONS decision 5 at DoD 1)

For a candidate document `d`, with `λ = [ranking] section_weight`:

```
S_sec*(d#s_k) = score_record( section body + heading slots ∪ parent title/path/ctx slots,
                              flen = section flen ++ parent title/path/ctx flen,
                              document df and n, DOCUMENT avg_wlen )
G(d)  = max(0, max_k S_sec*(d#s_k) − S_doc'(d))
S(d)  = ( S_doc(d) + λ · G(d) ) · w(d)          with 0 < λ ≤ 1
```

- **One yardstick.** Every unit — the document and each section-as-document —
  is scored on the document plane's `avg_wlen`, `df` and `n`. `sec_avg_wlen`,
  `sec_total_flen` and `sec_units` leave the runtime stats, both readers; the
  differential law has one number fewer to transcribe.
- **A section is scored as the short document it would be**: its own body and
  heading, plus its parent's title, path and ctx slots and their lengths, so a
  question that names the manual is credited to the section as it would be to
  a stand-alone note with that title.
- **`S_doc'(d)`** is the document's score over the same five slots. **Anchor
  stays document-level and outside both units**: its fold is added once to
  `S_doc` as today and never to a section.
- **`λ = 1` is pure max** — the document scores `max(S_doc, best S_sec*)`;
  `λ ∈ (0, 1)` interpolates toward it. **`λ > 1` is refused** by the record: it
  extrapolates past the section's own score, which is what produced the leaps.
- **A sectionless document gains nothing**, as before (`nsec` absent → no
  arithmetic; byte-identical at every λ, W-269's G3). **`0.0` stays OFF**
  (decision 7): the plane is never opened.
- The accelerator's skip ceiling still bounds the term: `G ≤ S_sec*`, and with
  `λ ≤ 1` the contribution is at most one section's score. Re-check, do not
  assume. `--why` and the `section` hit key keep decision 6's meaning; a gain of
  zero names no section.

## Definition of done

| DoD | what | state |
|---|---|---|
| 1 · record first (L0) | [SR-SECTIONS](../../records/0161_sections.md) decision 5 amended to the form above as the third mechanism, W-236's and W-269's kept beside it as history; the `λ ≤ 1` refusal stated there and in [SR-TUNE](../../records/0135_tuning.md); the runtime stats change in [SR-RUNTIME-STATS](../../records/0125_runtime-stats.md); [`compare/section-units`](../compare/section-units.compare.md) notes the reopen | ✅ 2026-10-13: d5 (third form, own-match), d7 (the scan's two routes), SR-TUNE (`_fraction`), SR-RUNTIME-STATS (`sec_*` gone, `fux.runtime.v11`), compare doc |
| 2 · 🔴 latency first | `scan.py:_attach_sections` reads pre-parsed section postings from the runtime segment instead of ≈ 18 900 `json.loads` per query ([W-270 ANALYSIS](../regression/2026-10-11-section-retest-set-6/ANALYSIS.md) §1). **Measured alone, before any scored arm**: median `ask` at `rung-10000` within L13's +100 ms. If it misses, stop — no arm can PASS | ✅ 2026-10-13, gen-5 `rung-10000`, `latency.py` (3 × 110 calls per arm): a byte-pattern read of the committed plane **failed, +190.4 ms**; the runtime read **passed, +68.6 ms** (403.8 → 472.4). [evidence](../regression/2026-10-13-section-term-v3/evidence/latency-precheck/). The bar's own latency row is re-measured on gen 6 |
| 3 · build | the form above on [W-273](W-273-section-records-implementation.md)'s branch, Python and Node (differential law), the accelerator bound re-checked; off = byte-identical (G0). Gates as W-270: G0, G1, G3, plus **G4 (a construction check, no key): no document's section contribution exceeds its best section's `S_sec*`**, and **G5 (descriptive, no key): the length distribution of incoming rank-1 documents against the baseline's**, the diagnostic above, so a length-driven arm is visible before any score | ✅ 2026-10-13: `rank._section_gain` and `rank.mjs` (third form); the scan's runtime route + committed fallback on both readers (`fresh.mjs` split out of `accel.mjs`, the bundle refuses a cycle); `section_weight` bounded by `_fraction`; G4 and G5 written ([`g4.py`](../regression/2026-10-13-section-term-v3/evidence/g4.py), [`g5.py`](../regression/2026-10-13-section-term-v3/evidence/g5.py)); the gates run in DoD 5 |
| 4 · the bar, frozen and committed alone | L13 shape, on `set-7-claude` at the generation-6 ladder (W-277). **One decided arm, named before any number: `sw-1.0` (pure max)**; `sw-0.5` (Callan's interpolation) reported only; no arm above 1.0 | ✅ 2026-10-13: [PRE-REGISTRATION](../regression/2026-10-13-section-term-v3/PRE-REGISTRATION.md), engine **`08ef6293`**, committed before the gen-6 ladder exists; C2's margin is L13's default from the slice size |
| 5 · capture | baseline (sections off), the decided arm, the reported arm | ✅ 2026-10-13: gen-6 ladder ([rebuild](../regression/2026-10-13-ladder-gen6-rebuild/report.md)); three arms + the pre-section engine captured ([report](../regression/2026-10-13-section-term-v3/report.md)); G0, G1, G3, G4 PASS; latency +49.5 ms PASS; rank 1 moved on 7 of 165 at `sw-1.0` |
| 6 · 🔴 Arpit scores; a session that did not capture runs the frozen decider | PASS → W-273 phase 2 ships `section_weight = 1.0`; FAIL → step 10 closes on three mechanisms; INCONCLUSIVE → Arpit | 🔴 **INCONCLUSIVE** 2026-10-13, decider run by Arpit ([VERDICT](../regression/2026-10-13-section-term-v3/VERDICT.md)): 0 losses, +6 `hit@1`, slice 5 of 24 below SR-RS d19's floor. **Arpit's ruling owed** |

**Optional, decides nothing:** a report-only rehearsal on `set-6-claude` (L13:
a set on which a mechanism was decided may report another, never decide it) to
catch a broken build before set 7 lands.

## Hazards

- ⚠ **The data decides whether anything can win.** W-277's R10, as first
  amended, built competitors that out-match the section under any BM25 unit
  (words in title, heading, first lines and ≥ 2 more); it was re-amended the
  same day so that the long document loses at baseline **by length alone**. A
  run on data built the first way FAILs every mechanism by construction.
- ⚠ Every number is `informed`: Claude authors set 7 and builds the engine.
- ⚠ One mechanism per arm. `b` is not touched (at `b = 0.15` a 15× document
  already pays a 2.1× per-term penalty; raising `b` manufactures the problem).
- ⚠ The corpus shape sets the averages: 882 of `rung-01000`'s 1 000 documents
  are ~100-token filler, which makes every seed document "long". The max form
  is scale-free; an additive λ is not.
- ⚠ U1 stays refused (no section index from fetched content).

## Custody

- 🔴 **No session reads the key** (L11). G4 and G5 read only the engine's own
  output and the runtime document table.
- `informed`, permanently.

## Records

[SR-SECTIONS](../../records/0161_sections.md) decision 5 (the mechanism),
[SR-TUNE](../../records/0135_tuning.md) (`section_weight` ≤ 1.0),
[SR-RUNTIME-STATS](../../records/0125_runtime-stats.md) (the section statistics
leave), [SR-RANKING](../../records/0111_ranking.md) (owner of
`rank._section_gain`), [SR-NODE-SEARCH](../../records/0153_node-search.md),
[SR-RS](../../records/0133_predictions.md) (the pre-registration). Laws: L0, L4,
L11, L12, L13.

## Reference

- [W-270](../../archive/open/W-270-section-retest-set-6.md) (closed) · [VERDICT](../regression/2026-10-11-section-retest-set-6/VERDICT.md) · [report](../regression/2026-10-11-section-retest-set-6/report.md)
- [W-269 VERDICT](../regression/2026-10-10-section-gain-only/VERDICT.md) · [W-236 VERDICT](../regression/2026-10-10-section-records/VERDICT.md)
- [W-273](W-273-section-records-implementation.md) · W-277 (closed 2026-10-12) · [SR-WORK-TESTDATA](../../records/0068_WORK-test-data.md) R10
- Callan (1994), Kaszkiel & Zobel (1997) — [BIBLIOGRAPHY](../../records/BIBLIOGRAPHY.md)
