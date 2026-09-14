---
type: Report
description: "The three fux inspect floors, measured on all seven golden rungs plus two planted corpora and this repository. Two bounds are admissible and ship provisional; the third — findable share — has no admissible bound and ships descriptive, because it reads 1.000 on every rung AND on forty copies of one runbook. The run also measured something nobody had: the golden ladder is 47 % boilerplate at every rung, its Heaps beta falls from 0.60 to 0.20 as it grows, and its Zipf slope is -2.36 against natural language's -1."
run: 2026-09-14-inspect-floors
item: W-169
pre_registration: work/regression/2026-09-14-inspect-floors/PRE-REGISTRATION.md
classification: blind
filed: 2026-09-14
---

# `fux inspect`'s three floors — and what the golden ladder turned out to look like

**What this run decides:** which of `fux inspect`'s four reported shares may
carry a *pass / attention* flag, and at what bound. The ruling is
[`VERDICT.md`](VERDICT.md).

🔴 **Read [`PRE-REGISTRATION.md`](PRE-REGISTRATION.md) §1 first, and read it as
a correction.** An earlier draft of this report claimed that file was
*"committed alone at `34306eb5`, ahead of the first number"*. **Both halves were
false** — that commit carries 28 files including the whole of
`src/fux/inspect/`, and the file was written after the rungs were measured. What
**is** checkable is the criterion itself: the proposal's §3 is in git at
`df257ad5` (2026-09-13, a clean prior commit) and its §5b plus the item's DoD 5
at `91255adb`, **a commit that contains no `fux inspect` at all**, so no number
could have informed either. The correction is stated rather than the claim
quietly dropped, because a false provenance claim about a threshold is the
pre-registration failure wearing the discipline's own clothes.

**`not a paired run`.** It compares corpora, never two arms of one corpus, and
states no delta. There is no improvement or regression headroom to disclose
because nothing was changed and re-measured.

⚠ **No evaluation material was read.** The three shares are properties of an
index, so this run reads each rung's `docs/` directory and nothing else — not
`queries.jsonl`, not `judged.jsonl`, not `key.jsonl`. That is what makes the
classification `blind` rather than a claim about care taken.

---

## 1 · What ran

Each golden rung was hardlinked (`cp -al`, so the benchmark corpora were never
written to) into `~/my_programs/fux-lab/inspect-floors/`, given a three-line
`.fux/`, then `fux ingest` → `fux build` → `fux inspect --json
--rebuild-dictionary --retrieval-sample 100`.

Two planted corpora and this repository ran beside them:

| corpus | what it is |
|---|---|
| `rung-00100` … `rung-10000` | the golden ladder's seven rungs, `docs/` only |
| `planted-bad` | **40 documents, one runbook copied forty times**, differing only in a two-digit service number. Built to be bad in all three ways at once |
| `planted-lenses` | the 27-document fixture `tests_e2e/test_inspect_verb.py` uses — one plant per lens, including one document with no distinctive term |
| `fux-repo` | this repository at `34306eb5`. **Reported, and an input to nothing** — *never tuned to this repo* |

Per-corpus rows: [`evidence/corpora.jsonl`](evidence/corpora.jsonl). The full
`fux inspect --json` output for each is beside it, one file per corpus.

## 2 · The numbers

| corpus | docs | terms | unreachable | boilerplate | near-dup | findable | Heaps β | Zipf |
|---|---|---|---|---|---|---|---|---|
| `planted-lenses` | 27 | 249 | **0.0370** | 0.4096 | 0.0741 | 1.000 | 0.815 | −1.14 |
| `planted-bad` | 40 | 105 | 0.0000 | **0.9848** | **1.0000** | 1.000 | 0.148 | −1.43 |
| `rung-00100` | 100 | 9 619 | 0.0000 | 0.4713 | 0.0000 | 1.000 | 0.599 | −2.10 |
| `rung-00200` | 200 | 10 322 | 0.0000 | 0.4732 | 0.0000 | 1.000 | 0.469 | −2.15 |
| `rung-00500` | 500 | 10 663 | 0.0000 | 0.4748 | 0.0000 | 1.000 | 0.291 | −2.18 |
| `rung-01000` | 1 000 | 11 163 | 0.0000 | 0.4747 | 0.0000 | 1.000 | 0.199 | −2.26 |
| `fux-repo` | 1 179 | 26 749 | 0.0008 | 0.0721 | 0.1425 | 0.970 | 0.564 | −0.96 |
| `rung-02000` | 2 000 | 12 163 | 0.0000 | 0.4748 | 0.0000 | 1.000 | 0.151 | −2.32 |
| `rung-05000` | 5 000 | 15 163 | 0.0000 | 0.4750 | 0.0000 | 1.000 | 0.154 | −2.34 |
| `rung-10000` | 10 000 | 20 163 | 0.0000 | 0.4733 | 0.0000 | 1.000 | 0.205 | −2.36 |

`findable share` is a sample of 100 documents on every corpus above 100
documents and is every document on `planted-lenses` and `planted-bad`.

## 3 · The verdict on each bound, against the frozen rule

| number | admissible bound | flags a rung? | flags a bad corpus? | verdict |
|---|---|---|---|---|
| **unreachable share** | `<= 0.01` | no — 0.0000 on all seven | **yes** — `planted-lenses` 0.0370 | **ships, provisional** |
| **near-duplicate share** | `<= 0.20` | no — 0.0000 on all seven | **yes** — `planted-bad` 1.0000 | **ships, provisional** |
| **boilerplate share** | `<= 0.60` | no — 0.4713–0.4750 on all seven | **yes** — `planted-bad` 0.9848 | **ships, provisional — and weak** |
| **findable share** | **none exists** | — | **no** — 1.000 on every rung *and* 1.000 on `planted-bad` | 🔴 **descriptive** ([verdict](VERDICT.md)) |

### 3a 🔴 `findable share` has no admissible bound, and the reason is structural

Self-retrieval was the plan's headline check: *does a document come back in the
top 3 for its own most distinctive words?* It reads **1.000 on every golden
rung and 1.000 on forty copies of one runbook**. No bound separates those, so
the rule drops it.

**It is not a threshold problem.** A fingerprint is built from the document's
own rarest terms, and a document's **path is part of its indexed vocabulary and
is unique by construction** — so any document with one rare term, its own file
name included, retrieves itself. `planted-bad`'s documents differ only by a
two-digit service number, and that number is enough.

**The flag moved to the exhaustive half.** *No distinctive term at all* costs no
queries, is computed for every document rather than a sample, and fires on
exactly the corpus shape it names: `planted-lenses` carries one such document
out of 27 and reads 0.0370.

### 3b ⚠ The boilerplate bound is the weakest of the three and ships saying so

Every rung sits at **0.47** — half of every posting in the golden ladder is a
term that is on half the corpus. This repository sits at **0.072**, a factor of
6.5 below. A bound anywhere near the honest-looking 0.25 would flag **all seven
rungs**, which the frozen rule forbids, so the bound is 0.60 and catches only
the pathological case.

**That is the rule working as written, and it is also the rule's cost**: the
ladder sets the ceiling on what any bound here may claim.

## 4 · What this run measured that nobody had asked for

**The golden ladder's rungs are not independent corpora of increasing size.
They are one vocabulary spread over more documents.** Three numbers say it, and
they agree:

- **The vocabulary barely grows.** 9 619 distinct terms at 100 documents;
  20 163 at 10 000. A hundredfold increase in documents buys **2.1× the
  vocabulary**.
- **Heaps β falls from 0.599 to ~0.20** and stays there. β is the exponent in
  `V = K·T^β`; natural-language corpora sit at 0.4–0.6, and this repository
  measures 0.564. A β of 0.20 means each new document brings almost no new
  words.
- **The Zipf slope is −2.36**, against −0.96 on this repository and ≈ −1 for
  natural language. The term-frequency distribution is far steeper than prose.
- **The median document vocabulary is flat at 521–526 distinct terms on every
  rung**, which is the generator's template showing through.

⚠ **What this does and does not mean.** It does **not** invalidate a relative
comparison on one rung: two arms graded on the same corpus are still two arms
graded on the same corpus. It **does** mean the ladder is a narrower instrument
than its document counts suggest, and it bears directly on
[W-156](../../open/W-156-prevalence-outside-golden.md) — *may a ranking change
ship on golden evidence alone* — which is open and Arpit's.

**This is a finding for him, not a call for this run to make.** It is filed
here, named in [W-169](../../open/W-169-fux-inspect.md)'s closure and in
W-156's detail, and it changes no threshold and no default.

## 5 · Authorship

| artifact | author | could reach |
|---|---|---|
| the golden ladder's seven corpora | the benchmark generator, before this item existed (`~/my_programs/fux-benchmark/corpora/`) | n/a — authored with no knowledge of these three shares, which did not exist |
| `planted-bad`, `planted-lenses` | Claude (this session), 2026-09-14 | **none.** Written to be bad in the three named dimensions; no queries, judgments or prior scores were read, and none exist for these shares |
| the three bounds | Claude (this session), 2026-09-14, against the frozen rule | the numbers in §2 and nothing else |
| `fux inspect` itself | Claude (this session) | none |
| this analysis | Claude (this session) | the numbers in §2 |

**Nothing in this run had access to evaluation queries, judgments or prior
per-query scores**, and the three shares have no prior scores to be exposed to —
this is their first measurement. `classification: blind`.

## 6 · Per-query rows

`no per-query rows` in the evaluation sense — this run grades no queries and
compares no arms. What stands in their place is **one row per corpus** in
[`evidence/corpora.jsonl`](evidence/corpora.jsonl) plus the complete
`fux inspect --json` output for each, which is every number any later reader
would need to recompute a bound or contest one.

## 7 · Reproduce

```bash
# one rung, from the benchmark corpora, in the lab; reads docs/ only
R=01000
BENCH=~/my_programs/fux-benchmark/corpora/docs-$R
LAB=~/my_programs/fux-lab/inspect-floors/rung-$R
rm -rf "$LAB" && mkdir -p "$LAB" && cp -al "$BENCH/docs" "$LAB/docs"
cd "$LAB" && printf '[sources]\n' > fux.toml && mkdir -p .fux/sources \
  && printf 'docs\n' > .fux/sources/dirs && : > .fux/pii.toml
fux ingest && fux build
fux inspect --json --rebuild-dictionary --retrieval-sample 100 | \
  python -c 'import json,sys; [print(c["name"], c["value"], c["status"]) for c in json.load(sys.stdin)["checks"]]'
```

`planted-bad` and `planted-lenses` are rebuilt by
`tests_e2e/test_inspect_verb.py::_planted` and by the forty-runbook generator
quoted in §1; both are in the lab and neither is committed.
