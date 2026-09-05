---
type: Analysis
run: 2026-09-05-expand
date: 2026-09-05
---

# What 16–0 does and does not establish

## 1 · The mechanism is confirmed; the operating conditions are not

**16 fixed / 0 broken, and 6 of the 9 hand-annotated vocabulary-gap failures
closed.** No ranking arithmetic changed: the same engine, the same corpus, the
same goldens, with words added to the query. The gap was vocabulary, and
supplying vocabulary closed it.

🔴 **The condition under which that happened is the finding's ceiling.** The
blind author **read all ten documents** before writing a single expansion. An
agent facing a 10 000-document corpus reads a handful. This run therefore
measures *"can supplied vocabulary close a vocabulary gap"* — yes — and **not**
*"can an agent supply it in practice"*, which is the question a consumer has.

**The measurement that would answer it**, and it is not this one: expansions
written from **only what a first `fux ask` returned**, which is the information
an agent actually has at the moment it would retry.

```bash
# sketch: expansions authored from the top-5 of a first search, not the corpus
fux ask "<q>" --json --top 5   # -> hand to the expansion author instead of docs/
```

## 2 · The guard cost nothing, and that was not obvious in advance

`rank()` drops any candidate matching no original query term. The worry was
that it would also drop genuinely relevant documents whose match is weak —
0 broken says it did not, on this corpus.

⚠ **Do not over-read it.** Every golden here has its answer *somewhere* in the
question's own vocabulary, however faintly; a corpus where the right document
shares **no** term with the question would be dropped by the guard and the
expansion could not save it. **That is the intended trade** — such a document
cannot be cited honestly — but it is a real recall ceiling and it belongs
beside the number.

## 3 · The `expand_weight = 0.2` default is untested by this run

Every arm ran at `0.2`. **Nothing here says `0.2` is better than `0.1` or
`0.5`**, and 16–0 would very likely survive a range of values. It joins
[W-97](../../open/W-97-tuner-knob-sweep.md)'s sweep, which now has a third knob
and a corpus that can actually see this one move.

**Repro for a sweep:**
```bash
for w in 0.05 0.1 0.2 0.5 1.0; do
  printf '[ranking]\nexpand_weight = %s\n' "$w" > <corpus>/.fux/tune.toml
  python evidence/expand_bench.py <corpus> ... /tmp/rows-$w.csv
done
```

## 4 · `-q` multi-query fusion is NOT measured here

W-109 shipped two things and this run grades one. `-q` has unit tests
(`tests/query/test_fuse.py`) and no graded run: writing a second phrasing per
query is a second blind-authoring pass, and doing it in the same session as the
first would have let one inform the other.

**Unresolved, and stated as unresolved:** whether fusing two phrasings helps on
this corpus at all. ADR-EXPAND decision 11 already names one reason to be
cautious — at `--top 5` the fusion sees very little.

## 5 · What this run cannot support

- Any claim about a corpus the expansion author has not read.
- Any claim about `expand_weight`'s value.
- Any claim about `-q`.
- Any comparison with a run measured on the enriched playground.
- Any claim at 10 000 documents.
