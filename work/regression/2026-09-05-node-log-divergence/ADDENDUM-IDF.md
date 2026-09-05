---
type: Run Report
run: 2026-09-05-node-log-divergence
addendum: idf-population-widened
classification: blind
date: 2026-09-05
description: "The Phase 0 run's own stated limit, closed: the `idf` argument population goes 13 -> 182 distinct values on this repo's real index, and the divergence it could not see appears — 7.69 % of arguments and 8.98 % of scores. Nothing survives round(9) and no ordering moves."
---

# Addendum — the `idf` population, widened

**This is not a new run.** It closes the limit
[`report.md`](report.md) and
[`ANALYSIS.md`](ANALYSIS.md) §3 named in their own words, on the corpus §3
named: *"widen the `idf` population before Phase 1 by probing `log` over every
`(df, n)` a real corpus produces — this repo's own `.fux/index/` is the obvious
one and is not synthetic."*

**The frozen report is not edited.** It said what it measured and named what it
could not; this says what the widened probe measured.

## Why it was owed

🔴 **The Phase 0 run's `idf` argument population was 13 distinct values.** That
is a property of a 10-document corpus plus a synthetic 10 000-document one
whose query terms are near-unique — not a property of fux. Over those 13, zero
diverged, so *"0 discordant scores on 197 233 scored documents"* was **a true
count and a weak guarantee**: it was measured where `log` had almost nothing to
disagree about.

## Authorship — classification `blind`

| artifact | author | could reach |
|---|---|---|
| the probe, the dump, the Node scorer, the comparator | pre-existing, from the Phase 0 run — **unchanged, byte for byte** | — |
| the query set | Claude Code, 2026-09-05 | this repo's own markdown; **no score of any kind** |
| this addendum | Claude Code | the Phase 0 report and this probe's output |

**`blind` on the Phase 0 run's own terms, and on one more.** There is no
relevance judgment, no golden and no prior score to be exposed to: the measured
quantity is *do two runtimes compute the same double*, which is a property of
two libms and not of any ranking anyone graded.

**And the query set could not have been fitted**, because the rule that picked
it is mechanical and was written before any number existed: tokenize every
`.md` under `docs/` and `work/` with fux's own `tokenize`, order the vocabulary
by frequency, **take up to 60 terms from each of ten equal frequency strata**,
seed `11`. One term per query, because one term is one `idf` argument. That
rule spans df from the commonest term in the repo to a hapax rather than
clustering where the vocabulary happens to be dense. It is
[`evidence/queries-self.txt`](evidence/queries-self.txt), 605 terms, committed.

## What was measured

| | |
|---|---|
| Python | CPython **3.14.2**, macOS 26.3.1, arm64 (Apple libm) |
| Node | **v24.13.0**, V8, darwin/arm64 (fdlibm port) |
| corpus | **this repository's own committed index** — 838 documents, not synthetic |
| queries | **605** single terms, stratified over the vocabulary's frequency deciles |
| scored documents | **41 908** |

## Result

| population | distinct values | differ bit-for-bit | max relative | differ at `round(9)` |
|---|---:|---:|---:|---:|
| `idf` arguments — **Phase 0** | 13 | **0** | — | 0 |
| `idf` arguments — **widened, here** | **182** | **14 (7.69 %)** | `2.128e-16` | **0** |
| `wide` (100 000 seeded doubles, unchanged) | 100 000 | 655 (0.66 %) | `2.211e-16` | 0 |

| end-to-end BM25F | |
|---|---:|
| documents scored | 41 908 |
| scores differing **bit-for-bit** | **3 764 (8.98 %)** |
| max relative difference | **`5.463e-16`** |
| scores differing at `round(9)` | **0 (0.000 %)** |
| queries with a different top-5, **exact sort** | **0** |
| queries with a different top-5, `round(9)` sort | **0** |

Per-query rows: [`evidence/per-query-self.jsonl`](evidence/per-query-self.jsonl)
(605 rows) and the CSV beside it. Raw output:
[`evidence/logprobe-self-output.txt`](evidence/logprobe-self-output.txt).

## What this changes, and what it does not

🔴 **The divergence the Phase 0 run could not see is real, and it is larger in
the `idf` population than in the wide one** — 7.69 % against 0.66 %. Its
*"0 discordant scores"* was an artifact of 13 arguments, exactly as §3
suspected. **8.98 % of real BM25F scores on this repo differ between the two
runtimes.**

✅ **And none of it can reach the sort key.** `rank.py` sorts on
`round(score, 9)`; the largest disagreement measured here is `5.463e-16`
relative — about **seven orders of magnitude** below that resolution. Zero
scores differ after rounding, and **no top-5 ordering moves under either sort**,
rounded or exact.

**So the case for the pre-registration's option (b) is stronger than it was**,
not weaker: the earlier null was uninformative, this one is not. ⚠ **This
addendum does not pick an option.** The cell in
[`../../benchmark/PRE-REGISTRATION-NODE.md`](../../benchmark/PRE-REGISTRATION-NODE.md)
§2 is Arpit's and stays blank.

⚠ **The kill clause is unmoved and still the thing to watch.** Pre-registration
§6: a divergence above `~1e-9` relative on *any* platform pair supersedes the
document and makes (a) mandatory. `5.463e-16` is not close to it — **on this
platform pair.**

🔴 **glibc is still not measured, and that is now the ONLY blank.** CI runs on
`ubuntu-latest`; this machine has no Linux, and W-107's cited figure
(1 095 / 100 000) is a glibc number. The probe is one `workflow_dispatch` job —
[`.github/workflows/log-probe.yml`](../../../.github/workflows/log-probe.yml),
added 2026-09-05 and not yet run. **Until it has, the evidence is
darwin/arm64's alone.**

## Reproduce

```bash
E=work/regression/2026-09-05-node-log-divergence/evidence
.venv/bin/python $E/dump.py . $E/queries-self.txt /tmp/self.json
.venv/bin/python $E/logprobe.py /tmp/self.json /tmp/args.json && node $E/logprobe.mjs /tmp/args.json
node $E/score.mjs /tmp/self.json /tmp/self-scored.json
.venv/bin/python $E/compare.py /tmp/self-scored.json /tmp/per-query-self.csv
```

⚠ **The numbers move with the corpus.** This repo's index is the corpus, so a
later run over a later index will differ in the counts and must not be compared
row-for-row with these. What is comparable is the shape: *how many differ*, and
*whether any survives `round(9)`.*
