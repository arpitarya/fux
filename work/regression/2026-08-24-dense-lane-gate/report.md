---
type: Report
name: 2026-08-24-dense-lane-gate
description: "The dense lane's pre-registered gate, run for the first time. 0 fixed / 2 broken against a >= 3-fixed / 0-broken bar. The cause is structural: the bundled embedding is a mean-pool of static token vectors."
timestamp: 2026-08-24T00:00:00Z
---

# The dense lane's gate, run

The ruling is [`VERDICT.md`](VERDICT.md). **FAIL.** This is the method and the
surface capture behind it.

## Why it ran now

Arpit, 2026-08-24: *"on c, let's turn it on."* `[dense] mode` ships `off`
behind a **pre-registered** bar, so the answer to "turn it on" is to run the
bar rather than to flip the switch.

## Method

| | |
|---|---|
| corpus | `fux-playground`, 10 documents, 65 committed chunk vectors |
| goldens | 50 ranked queries, unmodified |
| engine | `fux-engine` 2.0.0-alpha.1 |
| enrichment | **none**, in every arm — the variable under test is the lane |
| constant | `[ranking] rerank_weight = 1.0`, the playground's own setting |
| swept | `mode` × `threshold` × `weight`, 5 settings incl. the `off` control |

Each arm is a full `fux ingest --full` + `fux build` + `check.py`, so no arm
inherits another's derived plane.

## Surface capture

The verbatim console output of all five arms is
[`evidence/sweep.txt`](evidence/sweep.txt), each with its failing query ids so
fixed/broken is derivable rather than asserted.

```
== mode=off (control)          FAIL 18 · pass 32
== mode=gated t=0.5 w=0.25     FAIL 18 · pass 32     <- gate never fires
== mode=gated t=8.0 w=0.25     FAIL 19 · pass 31     <- fires; costs q020
== mode=always w=0.25          FAIL 20 · pass 30     <- costs q015, q020
== mode=always w=0.5           FAIL 20 · pass 30
```

## The correction this run forced on itself

An earlier reading of a coarser sweep concluded `gated` was **dead code**. It
is not. The top lexical score on this corpus is **~8.08** and the gate is
`results[0].score < threshold`, so `t = 0.5` and `t = 2.0` simply never trip
it. `t = 8.0` and `t = 100` do. **The code works; what it admits does not.**

That correction is recorded rather than quietly fixed, because "delete the dead
code" was already being written down when it turned out not to be dead.

## Reproduce

```bash
# fux-playground, fux 2.0.0-alpha.1 installed editable, .fux/enrich empty
printf '[ranking]\nrerank_weight = 1.0\n[dense]\nmode = "always"\nweight = 0.25\n' > .fux/tune.toml
fux ingest --full && fux build && python check.py
```
