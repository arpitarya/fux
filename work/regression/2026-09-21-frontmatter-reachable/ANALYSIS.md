---
type: Analysis
run: 2026-09-21-frontmatter-reachable
description: "One diagnosis that matters more than the PASS — the same unmeasured-premise error twice in one session — plus the supersession inversion a shared doc_id creates, and why the control moved nothing."
filed: 2026-09-21
---

# ANALYSIS — the PASS is fine; the premise error is the finding

## 1 · 🔴 The same mistake twice in one session, in two directions

| | the premise, frozen | what the before-arm measured |
|---|---|---|
| **part 2** | sibling identifiers (`RF-118/119/120`) fail, so set 3 supplies headroom | **they did not fail** — 8 of 8 ranked first in BOTH arms |
| **part 1** | six front-matter-only identifiers are absent from the index | **five were reachable** |

**Diagnosis.** Both premises were *generalisations of a correctly recorded single
case.* SR-INGEST decision 23 says `QCL-IT-ADR-08` was absent — one identifier,
measured. W-205 said `RF-118`-shaped ids were the failing shape — reasoned from
the analyzer, never probed. **In each case the record was right and the
population was assumed.**

🔴 **And the cause is the same mechanism in both: the analyzer SPLITS.** A
hyphenated identifier reaches the index as its parts, and the parts are often
present for unrelated reasons — `qcl`, `dock`, `03` in a dock-scheduling
document's own path and headings. **So *the whole identifier is absent* and *the
document cannot be found by it* are different statements**, and this session
froze thresholds on the first while meaning the second, twice.

**Change, specific** — the probe exists and costs minutes:

```bash
.venv/bin/python work/regression/2026-09-21-frontmatter-reachable/evidence/reach.py \
    --tree ~/my_programs/fux-lab/corpora/golden/rung-01000 \
    --fux .venv/bin/fux --out /tmp/premise.json
```

**Unresolved, and put to Arpit rather than taken:** whether
[SR-RS](../../../records/0133_predictions.md) decision 23 gains a clause —
*a data-shaped endpoint measures the defect on a handful of the proposed
population before the documents are authored or the threshold is frozen.*
Decision 23c already does this for links, mechanically, with a check that exits
non-zero. **It is a rule about measurement, so it is that record's.**

## 2 · Why the control moved nothing, and why that was not obvious

**60 of 60 unchanged.** The pre-registered worry was real arithmetic: `title`
tokens enter `flen`, `flen` feeds `avg_wlen`, and `avg_wlen` is in every
document's BM25F score. Adding a `doc_id` to every front-matter document should
have perturbed something.

**It did not, and the reason is proportion.** A `doc_id` is 3–5 tokens against a
`title` field of 5–10 and a document of hundreds; at `b = 0.15` length
normalisation is weak by design (W-144), so a shift of a fraction of a token in
`avg_wlen` moves no ordering. ⚠ **At `b = 0.75` — what `fux-engine 2.0.1` still
ships — this arm might not have been so quiet**, and nothing here measures that.

## 3 · The inversion is structural, not a tuning accident

Two documents share `QCL-QA-SOP-17`; both now carry it at `title` weight; the
archived one is shorter and wins on length normalisation. **A shared `doc_id` is
exactly what a superseded pair has** — the successor keeps the identifier of the
thing it replaces — so **part 1 makes supersession pairs MORE likely to invert,
not less.**

🔴 **The no-harm arms could not see it** and that is worth stating: the
id-queries count a family hit either way, and the control is set-1 prose. **A
condition that would have caught it does not exist**, and writing one now, after
seeing the result, would be a threshold moved.

**Named for the next pre-registration that touches `doc_id` ranking**: the
endpoint should be *the live half of a declared supersession outranks the
retired half*, which is key-free and was already measured once, on 2026-09-12,
at a coin flip.

## 4 · What shipped that no number here covers

The claim layer (`META_FIELDS`) and the binding (`[meta]`) are **built and
unexercised**: no built-in decoder declares a claim, because a decoded document
carries `meta={}`, and this run bound nothing. **Both are tested in
`tests/ingest/test_meta_fields.py` and neither is measured by this run.**

⚠ **That is not dead code and should not be read as such** — it is the ratified
mechanism for a consumer decoder (`.eml` → `Message-ID`), and SR-DECODE decision
20 is where it was decided. **But a reader looking for the number that justifies
it will not find one here**, and the honest reason is that the engine default is
what serves prose front-matter today.
