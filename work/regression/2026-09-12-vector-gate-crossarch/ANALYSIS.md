---
type: Analysis
description: "What the zero means, the one improvement it licenses, and the two things it deliberately does not settle."
run: 2026-09-12-vector-gate-crossarch
filed: 2026-09-12
---

# ANALYSIS — the two-architecture arm

## 1 · The finding, stated as narrowly as it holds

**Holding the embedder build fixed and varying the architecture changes
nothing** — not the float vector, not the int8 quantisation, not the ordering.
119 + 124 vectors, byte-identical, 0/124 discordant.

**That is more surprising than it reads.** `quantise` is
`round(127 * x / max|x|)` per vector, so a **single ULP** difference in the
largest component shifts the scale and can move several codes. Zero differing
codes out of 93 312 means the two builds agreed to the last bit on every
component of every vector — which says the model's forward pass here is
composed of operations whose results are exactly specified by IEEE-754 and
whose reduction order the two builds happen to share.

## 2 · The improvement it licenses — one sentence in W-112, and only one

**W-112's determinism claim can drop the CPU clause.**
[W-106](../../../archive/open/W-106-vector-gate.md) recorded it as *"same clone + same
embedder build"* with the architecture question open. On this evidence the
claim is **"same embedder build"** and nothing more.

⚠ **It does not license the plane.** The reason the vector plane is unbuilt is
the *implementation* result — two implementations of one model sharing **0 of
125** int8 vectors — and this run does not touch it. A pinned committed vector
is still an artefact of one build.

## 3 · Two things this does NOT settle, and both are easy to over-read

- 🔴 **Native x86-64 is still unmeasured.** Rosetta runs the x86-64 *build*,
  translated. It answers *"does the x86-64 build differ?"* and stands in for
  *"does x86-64 hardware differ?"*. Under Rosetta the x86 kernels see no
  AVX-512, so a native modern x86 machine may choose different vectorised
  reduction paths — the exact mechanism that would break bit-equality.
  **Anyone quoting this number for a Linux/x86 CI runner is quoting the wrong
  measurement.** Closing that needs a real x86-64 machine, and it is a new item
  if anyone wants it, not a gap in this one.
- **Nothing here is about retrieval quality.** No golden answer was read and
  none exists for this endpoint. The `>= 3 fixed / 0 broken` bar
  [DENSE-CHUNK](../2026-08-24-dense-lane-gate/VERDICT.md) froze was untestable
  on 2026-09-05 and is untestable now, for a new reason: the golden ladder's
  questions carry **no rank contract**.

## 4 · Specific improvements, each with a repro

| # | improvement | repro / where |
|---|---|---|
| 1 | **Amend W-112's determinism sentence** to drop the architecture clause, citing this run and naming the Rosetta caveat in the same breath | [W-112](../../open/W-112-vector-plane.md) |
| 2 | **`embed_py.py` should record the pinned revision it actually resolved.** It accepts a `revision` argument and reports whatever it was given — including `null`. Two runs a month apart can silently embed two model snapshots, and nothing in the output would say so | `tools/vector-gate/embed_py.py`: report `model.model_card_data` or the resolved commit from the HF cache |
| 3 | **`torch==2.2.2` + `numpy>=2` fails from inside `encode()` with *"Numpy is not available"***, naming neither package. Any future arm should assert the pair at start-up rather than 40 seconds in | add a version check to `embed_py.py`'s head |

**Unresolved, and stated as unresolved:** *why* two implementations diverge
while two architectures do not. The plausible cause is that the Node arm runs
ONNX kernels and the Python arm runs torch kernels — a different graph, not a
different machine — but **this run did not test that**, and the 2026-09-05 run
did not either.
