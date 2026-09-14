---
type: Analysis
description: "What the inspect-floors numbers change: two bounds ship, one number goes descriptive, and the golden ladder turns out to be one vocabulary spread over more documents. Three specific improvements, each with a repro command, and two unresolved causes stated as unresolved."
run: 2026-09-14-inspect-floors
item: W-169
filed: 2026-09-14
---

# Analysis — three improvements, and two things left unresolved

## 1 · Applied in this change

### 1a `findable share` lost its floor, and the mechanism is now recorded

**Finding:** 1.000 on every golden rung and 1.000 on `planted-bad`. No bound
separates them.

**Diagnosis, and it is not a threshold problem.** A fingerprint is the
document's own rarest terms; a document's **path is indexed vocabulary and is
unique by construction**. `planted-bad`'s forty documents differ by a two-digit
number, and that number is enough to retrieve each one.

**Applied:** the number ships `descriptive` (`floor=None`), the flag moved to
the exhaustive *unreachable share*, and both the code and
[SR-INSPECT](../../../records/0156_inspect.md) decision 9a state the mechanism
rather than the threshold.

```bash
cd ~/my_programs/fux-lab/inspect-floors/planted-bad
fux inspect --json --retrieval-sample 0 | python -c \
  'import json,sys; print([c for c in json.load(sys.stdin)["checks"] if c["name"]=="findable share"])'
# -> value 1.0, status "descriptive"
```

### 1b The boilerplate bound sits above the ladder, and says why

**Finding:** every rung is 0.471–0.475; this repository is 0.072.

**Applied:** bound 0.60, which flags `planted-bad` (0.985) and no rung. The
constant carries the three numbers in a comment and the record carries them in
decision 9b, because a bare `0.60` invites somebody to tighten it and break the
frozen rule.

### 1c Every truncated list now ships its count

**Finding, from this verb's first run on this repository:** the orphan list
showed `20` — which is what a cap of 20 looks like — and the real number is
**341**. Near-duplicate pairs read 20 and are **250**.

**Applied:** `orphan_count`, `pair_count`, `family_count`,
`unfindable_count`, and a unit test that plants twelve identical documents and
asserts a `top_lists=3` report still reports 66 pairs.

## 2 · Owed, and filed rather than done here

### 2a 🔴 The golden ladder is one vocabulary spread over more documents

**Finding:** 9 619 distinct terms at 100 documents → 20 163 at 10 000 (a
hundredfold in documents for **2.1×** in vocabulary); Heaps β **0.599 → ~0.20**;
Zipf slope **−2.36** against −0.96 here and ≈ −1 for prose; the median document
vocabulary flat at **521–526** on every rung.

**What it does not mean:** a relative comparison on one rung is unaffected. Two
arms on the same corpus remain two arms on the same corpus.

**What it does mean:** the ladder is a narrower instrument than its document
counts suggest — *rung 10 000* is not *ten thousand documents' worth of
vocabulary* — and a result that depends on term-distribution shape (anything
touching IDF, length normalisation, or expansion) generalises less far off it
than the size label implies.

**Where it goes:** [W-156](../../open/W-156-prevalence-outside-golden.md) is
open and Arpit's — *may a ranking change ship on golden evidence alone* — and
this is evidence for that question, not an answer to it. **Not acted on here:**
nothing in this change touches a threshold, a default or the ladder.

```bash
# the shape, per rung, from the filed rows
python -c 'import json
for l in open("work/regression/2026-09-14-inspect-floors/evidence/corpora.jsonl"):
    r = json.loads(l)
    if r["corpus"].startswith("rung"):
        print(r["corpus"], r["documents"], r["terms"], round(r["heaps_beta"],3), round(r["zipf_slope"],2))'
```

### 2b The floors are not re-measured when the ladder grows

Nothing re-runs this when a rung is added or a corpus is regenerated. The bounds
would keep their word *provisional* and stop being true. **Stated as owed**, and
named in SR-INSPECT's Consequences; a check would have to reach a corpus CI
cannot see, which is exactly [W-148](../../open/W-148-what-the-two-readers-still-owe.md)'s
first open call.

## 3 · Unresolved, and stated as unresolved

- **Why the golden generator's vocabulary saturates** is not diagnosed here.
  The numbers say it does; the generator lives in `~/my_programs/fux-benchmark`
  and this run did not read it. Whether that is a property worth changing is
  W-136/W-145 territory and Arpit's.
- **Whether 0.47 boilerplate is bad for the ladder's purpose** is genuinely
  open. A graded benchmark wants its queries to discriminate, and a corpus with
  half its postings on half its documents may still do that. This run measures
  the number and does not judge it.
