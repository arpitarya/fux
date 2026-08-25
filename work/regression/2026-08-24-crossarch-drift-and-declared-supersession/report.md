---
type: Report
name: 2026-08-24-crossarch-drift-and-declared-supersession
description: "Two experiments on one question: can fux fix q015? Route 4 measured onnxruntime's cross-architecture drift and CONFIRMED veto 1 condition 2. Route 2 declared the supersession offline and RECOVERED q015 in both blind arms, without touching condition 2."
timestamp: 2026-08-24T00:00:00Z
---

# Cross-architecture drift, and the declared supersession

Arpit, 2026-08-24: *"Let's try route four and build route two as well. Will
that unblock?"*

**Short answer: no, and that is the good outcome.** Route 4 nailed condition 2
shut with a number. Route 2 made condition 2 irrelevant to the failure that
prompted all of this.

---

## Route 4 — is a cross-encoder deterministic across architectures?

**No. Measured, not assumed.**

**What was tested.** Not a particular model — the *property*. A fixed ONNX
graph shaped like one transformer encoder block (MatMul, Softmax,
LayerNormalization, Gelu, residuals) at MiniLM-L6 dimensions (seq 128, hidden
384, ffn 1536), with weights and input generated once and shipped as bytes.
Both machines ran identical files.

**Configured to be as deterministic as possible**, so the result is a floor and
not an artefact: `onnxruntime==1.23.2` on both, `intra_op_num_threads=1`,
`inter_op_num_threads=1`, `ORT_SEQUENTIAL`, **all graph optimisations
disabled** (so the comparison is kernels, not whichever fusion each build
chose).

| | x86_64 (Linux, cloud) | aarch64 (Linux, Arpit's VM) |
|---|---|---|
| onnxruntime | 1.23.2 | 1.23.2 |
| `sha256(out)` | `ff476682…` | `b3b86c04…` |
| pooled scalar | `-0.021671757` | `-0.021671748` |
| pooled bits | `f888b1bc` | `f388b1bc` |

| statistic | value |
|---|---|
| bit-identical | **NO** |
| elements differing | **40 746 / 49 152 — 82.9 %** |
| max abs delta | **1.907e-06** |
| max relative delta | **7.726e-03** |
| max ULPs | 81 920 |

**What it means for fux.** `rank()` sorts on `round(score, 9)`. The drift on a
score of order 1 is **~1.9e-06 — about two thousand times the rounding.** Two
passages within that of each other reorder by architecture. And this is **one
block**; a six-layer cross-encoder compounds it.

**Verdict: veto 1 condition 2 is CONFIRMED.** It was an assumption when it was
written. It is now a measurement, and the measurement is not close.

---

## Route 2 — declare the fact offline, rank on it deterministically

**It works, and precisely on the failure it was aimed at.**

The idea: a model reads the corpus **at authoring time**, understands the prose
*"Supersedes ADR-0007 … this is the current decision"*, and emits a
**committed declaration** — `supersedes: [docs/adr-0007-helix-mesh.md]` in
ADR-0019's frontmatter. A human reviews it in the diff. At query time
`superseded_weight` demotes the retired document with integer-deterministic
arithmetic that already ships.

**The flag fires** (it never had before — the fixture declared supersession in
prose only):

```
docs/adr-0007-helix-mesh.md      superseded: True
docs/adr-0019-calder-gateway.md  supersedes -> file:docs/adr-0007-helix-mesh.md
```

| arm | before | best after | `q015` |
|---|---|---|---|
| unenriched | 32 / 50 | **33 / 50** @ `w=0.7` | passes either way |
| **blind #1** | 33 / 50 | **34 / 50** @ `w=0.7` | **FAIL → pass** |
| **blind #2** | 31 / 50 | **32 / 50** @ `w=0.7` | **FAIL → pass** |

**`q015` recovers in both independent blind arms**, at `w` = 0.7, 0.5 and 0.3 —
so it is the mechanism, not a lucky weight. `q016` also recovers. `q021`
(the *soak* query) is untouched, which is correct: different mechanism.

**The declaration alone does nothing.** At `w = 1.0` the flag is set and `q015`
still fails. The fact has to be *used*. Declaration **and** weight, together.

**Over-demotion costs.** At `w = 0.3` totals fall to 31 / 29 — the retired
document is still the best answer to some questions. `0.7` is the measured
sweet spot on this corpus and is **not** proposed as a default.

---

## Disclosures

- ⚠ **This route was designed by someone who had read `q015`.** The mitigation
  is that the declaration is copied from **the document's own prose**, is
  reviewable in a diff, and was validated on **both** blind arms plus `q016`,
  which was not targeted. It is not a clean-room result and is not claimed as
  one.
- ⚠ **ADR-0019's enrichment was re-pinned by hand** — same body, new
  `source_sha`, because the frontmatter change re-shas the document. The
  enrichment text describes content that did not change.
- The route 4 graph is **synthetic**, not MiniLM. The ops are the ops, and the
  direction of the finding is robust: a real model has six times the layers.
- One corpus, 10 documents, 50 queries.
