---
type: Analysis
run: 2026-09-05-vector-gate
date: 2026-09-05
---

# What the vector gate found, and what it is not allowed to conclude

## 1 · The reproducibility finding is bigger than the retrieval one

W-106 was framed as a **retrieval** question — does a contextual embedder fix
vocabulary-gap failures? It answered a **reproducibility** one, and that answer
is decision-relevant for [W-112](../../open/W-112-vector-plane.md) whatever the
retrieval number turns out to be on a proper corpus.

**Two implementations of `bge-small-en-v1.5`, both correctly configured, agree
to cosine 0.9964 — and produce ZERO identical int8 vectors out of 125.**

W-112 proposes committing pinned `.fux/vectors/<sha>.jsonl` to git. What this
run measures is that such a file is an artefact of *the implementation that
wrote it*: a colleague who regenerates it with the other implementation gets
different bytes for every vector, and a different top-5 on 41 of 50 queries.

**That does not kill W-112 — it names the shape it has to take.** A pinned
plane can still work, but its determinism claim must be *"the same clone plus
the same embedder build"*, never *"the same model"*. `agent-run-embeddings.md`
already says the first; this run is the measurement behind it.

⚠ **And int8 is not the culprit.** Quantisation costs 0.9962 within one
implementation — cheaper than the gap between implementations. Anyone reading
this as "int8 is too lossy" has it backwards.

## 2 · The DoD prescribed the wrong pooling, and the wrong one scored better

W-106's definition of done specifies `pooling: 'mean'` for the Node arm.
**`BAAI/bge-small-en-v1.5` declares `pooling_mode: cls`.** Mean-pooling it is a
different function, and it is what the first Node arm computed.

**The misconfigured arm looked like the best result in the run** — 10 fixed / 4
broken, against 6/6 for the correct configuration. A session that ran only the
arm the DoD asked for would have reported the strongest number in the set and
attributed it to *contextual embeddings*.

**Repro:**
```bash
python -c "from sentence_transformers import SentenceTransformer as S; \
print(vars(S('BAAI/bge-small-en-v1.5')[1])['pooling_mode'])"   # -> cls
```

**Improvement:** any future embedder arm reads the model's declared pooling
from its own config rather than taking it from a spec. `embed_node.mjs` now
defaults to `cls` and takes pooling as an argument, with the reason in the file.

## 3 · On retrieval, both correct arms net zero — and the number is not judgeable

6 fixed / 6 broken and 5 fixed / 5 broken. **Neither reaches 0 broken**, which
is the half of DENSE-CHUNK's bar that the corpus problem makes *harder*, not
easier: a worse lexical baseline (28 passing rather than 32) leaves **fewer**
queries available to break. The `fixed` half is inflated by the same corpus; the
`broken` half is if anything suppressed.

🔴 **This is stated as a direction, not as a verdict.** Arpit ruled on
2026-09-05 that this run files no verdict, and the corpus behind DENSE-CHUNK's
control cannot be reconstructed (report §"The corpus problem"). **What is owed
before any ruling is a corpus, not another measurement.**

## 4 · The one thing that would change the retrieval answer

**Only 1 of the 9 vocabulary-gap failures moved, in both correct arms.** Those
nine are the population W-106 exists to test, and the run's headline should be
read as *"a contextual bi-encoder moved one of nine"*, not as *"net zero"* —
which is the aggregate hiding the actual subject.

Two candidate causes, and this run cannot separate them:

- **The chunks are too short.** 10 documents produce 75 chunks; several
  vocabulary-gap targets are single-section documents whose whole answer is one
  chunk with little context for a bi-encoder to use.
- **The failures are not all vocabulary gaps.** `q006`'s note is a genuine
  synonym gap (*outage* vs *unavailable*); `q007`'s is a **table-column
  layout** problem, which no embedding fixes.

**Improvement:** re-read the nine `known_failure` notes and split them into
*synonym gap* / *structure* / *negation* before the next run, so the denominator
is the population the instrument can actually address.

```bash
python -c "import json;[print(g['id'], g['known_failure'][:90]) for g in \
 (json.loads(l) for l in open('goldens/queries.jsonl')) if g.get('known_failure')]"
```

## 5 · What was not run, and is still owed

- 🔴 **The two-architecture arm** (x86-64 **and** arm64 query vectors). Only
  arm64 exists here. Result 2 compares *implementations*, which is a different
  cut and does not substitute for it.
- The comparison against DENSE-CHUNK's control, which needs the corpus back.

## 6 · What this run cannot support

- Any PASS or FAIL against DENSE-CHUNK's frozen bar.
- Any claim that the vector plane would or would not help on a real corpus.
- Any statement about a corpus other than these ten documents.
- Any claim at 10 000 documents.
