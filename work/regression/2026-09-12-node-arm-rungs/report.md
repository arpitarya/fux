---
type: Report
name: node-arm-on-the-golden-ladder
description: "The Node differential arm, run for the first time on the committed golden ladder rather than on fux's own index. Both ends of the ladder, manifest-verified: 750 comparisons each, 0 discordant, graph digests identical. And the reason the arm had been green until now: it compared Node against a Python path nobody runs."
classification: blind
timestamp: 2026-09-12T00:00:00Z
---

# The Node arm on the golden ladder — W-107

## 0 · Classification — `blind`

### Authorship

Per [ADR-RS](../../../docs/adr/0133_predictions.md) decisions 11–15.

| artifact | author | could reach |
|---|---|---|
| the corpora (the eight golden rungs) | built 2026-09-12 by `build_golden_rung.py` from the committed seed + generator, W-136 phase 2 | none of this run's queries — the rungs predate it |
| the query set | **derived from each corpus's own vocabulary** by `queryset.py`'s fixed rule, capped by position | the corpus. **no** queries, **no** judgments, **no** prior scores |
| the harness (`node_arm.py`, `rungs.py`, `graph_arm.py`) | this session | the corpora and the manifests. **no** answer key |
| the analysis | this session | the numbers below and the code |

🔴 **`work/golden/golden-answer/` and `work/golden/questions/` were not opened,
and this arm has no reason to open them** — it compares two readers against
each other, so it needs no ground truth ([PRE-REG-NODE-2](../../benchmark/PRE-REGISTRATION-NODE-2.md) §4).

⚠ **This is an equivalence run, not a retrieval-quality run.** No delta against
any other run is stated, and none could be: the quantity measured is *"do two
readers disagree"*, which has no baseline to move against.

## 1 · What ran

| | |
|---|---|
| instrument | [PRE-REG-NODE-2](../../benchmark/PRE-REGISTRATION-NODE-2.md), frozen 2026-09-12, sha `2ea40303…` |
| corpora | `rung-00100` and `rung-10000` — **§4's per-push ends** — in `fux-lab`, each **verified against its committed manifest before a single query ran** |
| engine | `fux 2.0.0-alpha.7`, Python 3.14.3, Node **v24.13.0**, darwin/arm64 |
| queries | 125 per rung, corpus-derived by fixed rule + 5 hazard pins, × tops 1/5/20 × `find`+`ask` |

```console
$ python tools/differential/node_arm.py --rung rung-00100 --evidence <run>/evidence
$ python tools/differential/graph_arm.py --rung rung-00100
$ python tools/differential/node_arm.py --rung rung-10000 --evidence <run>/evidence
$ python tools/differential/graph_arm.py --rung rung-10000
```

## 2 · The numbers

| rung | comparisons | discordant | graph plane |
|---|---|---|---|
| `rung-00100` | **750** | **0** | python `546282562f8f…` = node `546282562f8f…` |
| `rung-10000` | **750** | **0** | python `a7bcc8245f83…` = node `a7bcc8245f83…` |

Per-query rows — one per query per verb per depth, pass/fail — are in
[`evidence/`](evidence/) as JSONL, as §6 requires. Wall clock: 3 s and 1 m 47 s.

### Headroom, both directions — [ADR-RS](../../../docs/adr/0133_predictions.md) decision 22

**This is a paired run with an unusual shape: there is no better arm.** The
endpoint is a discordance count, so *improvement* is not defined and the only
question decision 22 can ask is whether a zero is a real zero or a saturated
instrument.

| direction | headroom | why |
|---|---|---|
| **improvement headroom** | **0 of 750** | the comparisons *wrong in both arms* — here, already discordant and therefore fixable. There are none, so nothing in this run could have got better. **A zero on this direction is the honest reading of a green equivalence arm**, not a defect in it |
| **regression headroom** | **750 of 750, per rung** | the comparisons *right in both arms*, every one of which could have gone discordant. Nothing is structurally forced to agree, and 26 of them — the hazard pins plus the `df == 1` singletons — are shapes chosen to break a reader |
| **observed** | **0 discordant of 750**, both rungs | |
| **positive control** | 🔴 **the instrument DOES fire** | the same harness and the same queries on a copy of `rung-00100` with `rerank_weight` flipped: **20 of 58 discordant** ([`evidence/tune-gap-probe.txt`](evidence/tune-gap-probe.txt)). A null from an arm just shown detecting a real divergence is a null about the readers, not about the corpus |

⚠ **What the zero does NOT clear.** Saturation is ruled out; *coverage* is not.
125 queries per rung reach the vocabulary bands `queryset.py` samples, and a
divergence living only in a shape neither the pins nor those bands touch —
`answer`'s passage locators, `explain`, `path`, an `--expand` query — would
return 0 here and be no less real. **`find` and `ask` are what ran.**

⚠ **No `VERDICT.md`, and nothing here says `N5 passes`.** Three reasons, and
each is sufficient on its own:

1. **N5/N6 say *"over every golden"***, and the golden questions are not
   released to any Claude session yet ([W-145](../../open/W-145-codex-regenerates-the-key.md)).
   What ran is a corpus-derived substitute, which is a different set.
2. **§4 requires all three OS/libm pairs and Node 20 + 22.** This is one
   machine, one Node, and **Node 24** — outside the matrix it names.
3. **§2: a green arm is filed, not announced.** Only a red one is information.

## 3 · 🔴 The finding — the arm was green because it tested the wrong Python

**`node_arm.py` called `scan.ask` directly.** `fux find` does not: it calls
`run_query`, which loads `.fux/tune.toml`, applies the archived weighting and
runs the proximity reranker. So the arm compared **Node against a Python path
that no user reaches**, and both sides ignored the same things.

Pointed at the path the CLI actually uses, on **fux's own repository**:

| arm | discordant |
|---|---|
| contract — `.fux/tune.toml` applied, as `fux find` applies it | **90 of 174** |
| transcription — `--no-tune`, the engine's own answer | **0 of 174** |

**Cause: Node reads no `tune.toml` at all.** `node/src/config/` holds
`root.mjs` and nothing else; no file under `node/src/` mentions tune. W-107 R5
lists `.fux/tune.toml — absent = defaults; malformed = hard error` in the fixed
read path, and that row is **unbuilt**. `rerank.mjs` is still owed by Phase 2.

**Reproduced in isolation** — [`evidence/tune-gap-probe.txt`](evidence/tune-gap-probe.txt).
A copy of `rung-00100` with exactly one key changed, `rerank_weight 0.0 → 0.3`:

| same corpus, same queries | discordant |
|---|---|
| contract arm | **20 of 58** |
| transcription arm | **0 of 58** |

⚠ **Why the ladder runs in §2 are unaffected:** every golden rung's effective
tune is **all defaults**, so on them the contract and transcription arms are
the same run. The gap is real, and the instrument that would have shown it was
pointed away from it.

## 4 · Conditions worth recording

- **A concurrent session rewrote this repo's `.fux/` at 16:08**, deleting all
  253 index shards from the working tree. The §3 numbers on fux's own index
  were measured **before** that and are not re-runnable against the tree as it
  now stands — which is why §3's finding is carried by the isolated probe in
  `evidence/`, on a corpus this run controls, rather than by those numbers.
- **The §2 runs are immune to it**, and that is not luck: separating the engine
  root from the corpus root is part of this change, so the arm imports `fux`
  from the checkout and reads its index from `fux-lab`.
- **Machine load does not bias this run.** The measured quantity is a
  discordance count, not a duration; the wall-clock figures are reported as
  description, never as a fence (the fence moved to `fux-benchmark`, §5 of the
  pre-registration).
