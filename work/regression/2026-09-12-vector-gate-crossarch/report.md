---
type: Report
description: "W-106's owed two-architecture arm. One embedder implementation on arm64 and on x86-64 (Rosetta) produces BYTE-IDENTICAL int8 vectors and 0/124 discordant top-5 orderings — inverting the 2026-09-05 finding, where two IMPLEMENTATIONS on one architecture shared 0 of 125 vectors and disagreed on 41 of 50 orderings."
items: W-106
run: 2026-09-12-vector-gate-crossarch
classification: informed
engine: fux-engine 2.0.0-alpha.7
pre_registration: none — this arm has no pre-registered threshold; it reports a count
filed: 2026-09-12
---

# The two-architecture arm — the last thing W-106 owed

**One question, and it is W-112's, not retrieval's:** *if the vector plane
commits a pinned vector to git, does whoever clones the repo recompute the same
one?* The 2026-09-05 run answered half of it. This is the other half.

---

## Authorship

| artifact | author | could reach the queries? | could reach the answers? |
|---|---|---|---|
| the harness (`prepare.py`, `embed_py.py`, `cross_arm.py`) | prior sessions, 2026-09-04/05 | — | — |
| the corpus and the query set | **Codex** (`work/golden/`), sealed key | n/a | **no Claude session has read the key, and this run does not need one** |
| this run, its two environments and this report | Claude Code, this session | read the questions | no |

**`informed`, and it barely matters here.** There is **no correct answer to
fit**: the endpoint is *"do two builds of one model produce the same bytes"*,
which is true or false independently of what any query means. Recorded as
`informed` anyway, because the author read the question set.

---

## The two arms — identical in everything but the instruction set

| | arm64 | x86-64 |
|---|---|---|
| Python | 3.9.6 (`/usr/bin/python3`, universal binary) | 3.9.6, **the same binary under `arch -x86_64`** |
| torch | 2.2.2 | 2.2.2 |
| sentence-transformers | 2.7.0 | 2.7.0 |
| numpy | 1.26.4 | 1.26.4 |
| model | `BAAI/bge-small-en-v1.5`, 384 dims | the same |
| reported runtime | `python 3.9.6 Darwin/arm64` | `python 3.9.6 Darwin/x86_64` |

**Every version is pinned to the same value on both sides on purpose.** The arm
is worth nothing if the two differ in anything else — and `torch==2.2.2` is the
constraint that set the rest: it is the last release with macOS **x86-64**
wheels, and it needs `numpy<2`.

**Corpus:** the golden ladder's `rung-seed`, 11 markdown documents → **119
chunks** through `fux.refer._chunk.chunk`. **Queries:** all **124** of
`work/golden/questions/questions.jsonl`. Per
[L9](../../../docs/adr/0011_LAW-9-environments.md), a measurement runs on the
lab's golden data; the 2026-09-05 run's corpus was `fux-playground`, which the
same law retired.

---

## Result — zero divergence, at every level

| level | chunks (n=119) | queries (n=124) |
|---|---|---|
| cosine between arms, **minimum** | **1.000000** | **1.000000** |
| int8 vectors **identical** | **119 / 119** | **124 / 124** |
| int8 codes differing | **0 / 45 696** (0.00 %) | **0 / 47 616** (0.00 %) |

**Top-5 dense orderings discordant between the two architectures: 0 / 124.**

Per-query rows: [`evidence/per-query-rows.csv`](evidence/per-query-rows.csv) —
one row per query, both orderings, the cosine and the identical-flag.
Per-chunk: [`evidence/per-chunk-rows.csv`](evidence/per-chunk-rows.csv).

---

## Headroom — how many queries COULD have differed

**ADR-RS decision 22.** A null is only as informative as the number of queries
that were free to move, and this one is a null in both directions.

| direction | what it would mean here | headroom |
|---|---|---|
| **improvement** | a query where the two arms **disagree today** and a fix would make them agree | **0 of 124** — they already agree on every query, so there is nothing to improve and no room to show one |
| **regression** | a query where the two arms agree today and could have disagreed | **124 of 124** — every query's ordering is an independent product of 384 floats computed twice by two separate binaries, and a single ULP in the largest component would re-scale the int8 quantisation |

🔴 **The regression headroom is what makes this result mean anything.** All 124
queries were free to diverge and none did, across **93 312 int8 codes**. Had the
headroom been small — say a corpus where every query returns the same document
by construction — a 0/124 would have been a fact about the corpus rather than
about the arms.

⚠ **The improvement headroom is 0 and that is not a warning.** It is the shape
of the endpoint: *"do these agree"* has no improvable direction once they do.
Stated rather than omitted, because decision 22b says a bare number answers
neither question.

---

## What this changes, and what it does not

🔴 **It inverts where the 2026-09-05 run pointed.** That run measured **two
implementations** (`@huggingface/transformers` in Node, `sentence-transformers`
in Python) on **one** architecture and found cosine **0.9964**, **0 of 125**
int8 vectors identical, **41 of 50** top-5 orderings discordant. This run holds
the implementation fixed and varies the architecture, and finds **nothing at
all**.

**Read together: the variable is the implementation, not the machine.** W-106's
filed conclusion — *"a pinned committed vector is an artefact of one
implementation"* — is **strengthened and narrowed**. W-112's determinism claim
does not have to say *"same clone + same embedder build + same CPU"*; on this
evidence **"same embedder build"** is the whole of it.

⚠ **Rosetta is a translation, and the report says which question it answers.**
`arch -x86_64` runs the **x86-64 build** of torch, translated onto arm64
hardware. So this is a real answer to *"does the x86-64 BUILD of this library
produce different vectors?"* — **no** — and a **stand-in** for *"does native
x86-64 HARDWARE produce different vectors?"*. The distinction is not academic:
under Rosetta the x86 kernels see no AVX-512, so a native modern x86 machine may
select different vectorised reduction paths. **A zero here does not license a
zero there**, and W-112 may not quote this as one.

⚠ **No delta is stated against 2026-09-05.** Different corpus, different query
set, and one is `fux-playground`. The two runs are read side by side as two
different measurements, which is what
[ADR-RS](../../../docs/adr/0133_predictions.md) decision 12 requires.

**This does not revive the vector plane.** The retrieval half of W-106 —
DENSE-CHUNK's `>= 3 fixed / 0 broken` — was never testable and is not testable
now: the ladder's questions carry no rank contract. **W-112 stays where it is.**

---

## Reproduce

```bash
# two environments, pinned identically, differing only in arch
/usr/bin/python3 -m venv /tmp/vecgate-arm/venv
arch -x86_64 /usr/bin/python3 -m venv /tmp/vecgate-x86/venv
for V in /tmp/vecgate-arm /tmp/vecgate-x86; do
  $V/venv/bin/python -m pip install -q 'torch==2.2.2' 'sentence-transformers==2.7.0' 'numpy<2'
done

mkdir -p /tmp/vecgate/corpus/docs
cp ~/my_programs/fux-lab/corpora/golden/rung-seed/seed/*.md /tmp/vecgate/corpus/docs/
python3 -c "import json;[print(json.dumps({'id':r['id'],'q':r['question']})) for r in \
  (json.loads(l) for l in open('work/golden/questions/questions.jsonl') if l.strip())]" \
  > /tmp/vecgate/queries.jsonl

G=$PWD/tools/vector-gate
python3 $G/prepare.py /tmp/vecgate/corpus /tmp/vecgate/queries.jsonl /tmp/vecgate/prepared.json
/tmp/vecgate-arm/venv/bin/python $G/embed_py.py /tmp/vecgate/prepared.json /tmp/vecgate/vec-arm64.json
arch -x86_64 /tmp/vecgate-x86/venv/bin/python $G/embed_py.py /tmp/vecgate/prepared.json /tmp/vecgate/vec-x86_64.json
python3 $G/cross_arm.py /tmp/vecgate/prepared.json /tmp/vecgate/vec-arm64.json /tmp/vecgate/vec-x86_64.json
```

⚠ **Two traps this run hit, both silent:** `torch 2.2.2` with `numpy>=2`
raises *"Numpy is not available"* from inside `encode()` — an error that names
neither package version; and `arch -x86_64 uv` fails outright (Homebrew's `uv`
is arm64-only), which is why the environments are built with the universal
`/usr/bin/python3` rather than with `uv`.
