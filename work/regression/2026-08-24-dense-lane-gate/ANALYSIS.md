---
type: Analysis
name: 2026-08-24-dense-lane-gate-analysis
description: "Why the dense lane failed: the bundled embedding has no layers, so it is order-blind like BM25F. Every rebuild that could fix q015 converges on the capability ADR-RERANK veto 1 refuses."
timestamp: 2026-08-24T00:00:00Z
---

# Analysis — the dense lane's gate

## 1 · The finding is mechanical, not statistical

`src/fux/embed/model.py::embed` does exactly this: tokenize (stdlib WordPiece),
look each token up in a packed table, **sum**, divide by the count, quantize.

**No transformer layers. No attention. No position.**

It is a bag of word-vectors, averaged. Which means the dense lane's model of a
passage is the same *kind* of model BM25F has — a set of terms with no order —
just projected into a different space.

**So the lane cannot distinguish *"current"* from *"no longer current"*.** And
`always` mode **breaks `q015`**, which is precisely that query. The one failure
a semantic lane was most expected to rescue is the one it makes worse.

## 2 · Phase 7 was right about the unit and wrong about the constraint

The Phase 7 argument was that the document-level lane failed (3 fixed / 9
broken) because **the unit** was wrong — *"a 12 KB document with ten sections
averaged into one point sits near none of them"* — and that per-chunk vectors
would fix it.

The unit **is** better. A chunk is a coherent span and its mean is a less
meaningless point than a document's. **It just was not the binding constraint.**
Averaging 60 word-vectors instead of 600 gives a sharper point that still cannot
represent word order, and word order is where this corpus's confusions live: a
current/superseded ADR pair, a current/legacy runbook pair.

**Generalisable form:** *changing the granularity of an averaging operation does
not change what averaging can represent.*

## 3 · The convergence, which is the strategically important part

Every way to fix `q015` requires reading **word order**:

| path | needs | blocked by |
|---|---|---|
| rebuild the dense lane with a contextual encoder | transformer layers at query time | L1 (`$0`, stdlib-only) and cross-machine determinism |
| the cross-encoder ADR-RERANK deferred | same, at rerank time | **veto 1 condition 2** — `onnxruntime` is not byte-identical across x86-64 / arm64 |
| per-chunk lexical index (option A) | a committed format change | does **not** fix it — still order-blind |
| `superseded_weight` | a declared `supersedes:` key | inert on the fixture; does not generalise to prose negation |

**Three of the four converge on the same capability**, and it is the one thing
fux has refused twice on determinism grounds. That is now a load-bearing
constraint rather than a footnote: **fux's architecture cannot currently
represent negation, and every escape route runs through the same locked door.**

⚠ This is an observation, **not a proposal to unlock it**. The determinism
argument that closed that door is untouched and is a good argument.

## 4 · Specific improvements

**4.1 — Keep the vectors, keep the lane off.** The committed `int8` vectors cost
nothing at rest and zero query time while `mode = off`. A better pooling reuses
them unchanged. Deleting them would throw away the only part of Phase 7 that
survived.
*Repro:* none needed — this is a do-nothing.

**4.2 — The `superseded_weight` path is the only unlocked one, and it is
untested.** It cannot fix prose negation in general, but it *can* fix the
declared current/superseded pair — which is what `q015` and `q016` actually are.
⚠ It needs the fixture to declare supersession in frontmatter, which re-shas the
document and stales its enrichment.
*Repro:* add `supersedes:` to ADR-0019, re-enrich, sweep `superseded_weight`,
and check whether `q015` recovers for the blind arms.

**4.3 — Unresolved: is mean-pooling salvageable at all?** Nothing here tests
alternatives that stay stdlib — max-pooling, per-field pooling, or pooling over
sliding windows. All are cheap to try and none has been.
*Repro:* variants of `embed()`, same five-arm sweep.

## 5 · What is NOT concluded

That the dense lane is worthless. It is worthless **at this pooling**, on this
corpus, against these fifty queries. The unit change was real progress and the
bytes are already paid for.
