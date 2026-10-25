---
type: Run Report
run: 2026-10-25-w298-step1-codelaw-rules
item: W-298
date: 2026-10-25
classification: informed
status: PASS — 19 of 20 intents place the right rule in the top 5 (bar 16)
---

# 2026-10-25 — W-298 step 1: free-text search over codelaw's rule pack — **PASS**

**The question the item set:** is free-text search over a rule pack worth
building for? Point today's fux at `node_modules/@codelaw/rules-js/rules`, write
20 plain-words intents, count how often the right rule is in the **top 5**. **Bar
set in the item before the run: 16 of 20** (W-298, filed 2026-10-25).

**Result: `fux ask` 19 / 20 in the top 5 · 13 / 20 at rank 1 · `fux find` identical
on every row.** The one miss (`i08`) lands at rank 6.

## What ran

| | |
|---|---|
| engine | fux **5.0.0**, `main` @ `658bc91` (2026-10-25 17:27 IST), run from a fresh clone in a Linux container — not the Mac; the Mac's `.venv` cannot run the engine from the Cowork bridge (MACHINE.md) |
| corpus | `@codelaw/rules-js@0.1.0` from npm — **140** Markdown rules under `rules/{graph,js,node,react,stencil,ts}/`, 588 KB. ⚠ W-298 says *438 rules*; that count is not the published pack. Recorded, not reconciled |
| consumer repo | scratch git repo; `fux setup --no-agents --no-hooks`; `sources.yaml` → `paths.include: [node_modules/@codelaw/rules-js/rules]`; no `.fuxignore` line; shipped `tune.toml` and `identifiers.toml` untouched |
| ingest | `ingested 140 docs (140 changed), 0 not indexed, 0 skipped, 106 shards written` — 0.78 s wall |
| queries | 20 intents, `fux ask --json --top 10` and `fux find --json --top 10`, default scan path; rank = position of the expected rule's `loc` |
| rows | [`evidence/rows.tsv`](evidence/rows.tsv) — one row per intent per verb, with the top-5 locations; raw JSON per call in [`evidence/raw/`](evidence/raw/) |

## Per-intent ranks (`ask`; `find` is identical)

| id | intent | expected | rank |
|---|---|---|---|
| i01 | my useEffect is missing a variable in its dependency array | react/exhaustive-deps | **1** |
| i02 | warning about key when rendering a list with map | react/jsx-key | **1** |
| i03 | opening a link in a new tab is a security risk | react/jsx-no-target-blank | **1** |
| i04 | can I call a hook inside an if statement | react/rules-of-hooks | **1** |
| i05 | naming convention for a custom hook | react/hook-prefix | **1** |
| i06 | how should I name the props interface of a component | react/props-type-name | 3 |
| i07 | switch case keeps running into the next one without a break | js/no-fallthrough | **1** |
| i08 | put all the module exports at the bottom of the file | js/exports-at-end | **6 — miss** |
| i09 | should I use default export or named exports | js/no-default-export | **1** |
| i10 | order of import statements, node builtins first then packages then local files | js/import-groups | **1** |
| i11 | left a debugger line in the code | js/no-debugger | **1** |
| i12 | checking if something is NaN with === does not work | js/use-isnan | 2 |
| i13 | a function is exported but no file imports it anywhere | graph/no-unused-exports | 2 |
| i14 | async function passed to the Promise constructor | js/no-async-promise-executor | **1** |
| i15 | using the any type in typescript | ts/no-explicit-any | 4 |
| i16 | ts-ignore comment to silence the compiler error | ts/ban-ts-comment | **1** |
| i17 | importing something that is only used as a type | ts/type-only-imports | 2 |
| i18 | exiting the process from inside library code | node/no-process-exit | **1** |
| i19 | package imported but not listed in package.json dependencies | node/no-extraneous-import | 2 |
| i20 | boolean property on a web component that starts out switched on | stencil/ban-default-true | **1** |

**hit@5 = 19/20 · hit@1 = 13/20 · mean rank of the 19 hits = 1.63.**

## What this does and does not claim

- It clears the bar the item set **before** the run, so W-298's family (W-299–W-302) is not parked.
- It is **one author's 20 intents on 140 documents** — far inside the 10 000 ceiling, and no golden claim. It says *the words a developer uses to describe a lint problem reach the rule that names it*, on this pack, with the shipped tune.
- It is **not** evidence about multi-segment ranking (W-300) — one segment ran, the consumer repo had no documents of its own.
- Not a paired run; no delta is stated against anything.

## Authorship

| artifact | author | could reach |
|---|---|---|
| the 20 intents and their expected rules ([`evidence/intents.tsv`](evidence/intents.tsv), sha256 in `intents.sha256`, sealed 11:59:53 UTC before the first query) | Cowork (Fable 5.1) — the measuring session | the rule **titles** list (`grep ^title:`) and one rule body; **no** query result, no score |
| the corpus | codelaw's authors, via npm | n/a |
| the engine | fux `main` @ `658bc91`; shipped `tune.toml` | n/a — nothing tuned for this run |
| `run.py`, this report, ANALYSIS, VERDICT | the same Cowork session | the rows, after the run |

`informed`: the intents' author is the engine builder's model family and read the
titles it then wrote intents against. The bar was fixed by the item before the
author saw either the rules or a result; the intents were sealed before the first
call.
