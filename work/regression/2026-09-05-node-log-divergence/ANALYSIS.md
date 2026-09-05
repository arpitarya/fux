---
type: Analysis
run: 2026-09-05-node-log-divergence
date: 2026-09-05
---

# What this says about the `log()` decision — and what it does not decide

**This file does not pick.** W-107 Phase 0's third bullet is Arpit's, and the
ratification of 2026-09-05 left it unstruck. What follows is the measurement
laid against each option, and the one thing that would change the answer.

## 1 · The divergence is real, and it is seven orders of magnitude below the sort key

Two facts, and they point in opposite directions:

- **`Math.log` and `math.log` genuinely differ** — 655 of 100 000 on
  darwin/arm64, the same order as the glibc number W-107 cites. Anyone who
  assumes two runtimes compute the same log is wrong.
- **Every difference is one ulp** (max `2.211e-16` relative), and `rank.py`'s
  sort key is already `(-round(score, 9), id)`. A `round(9)` boundary is
  ~`1e-9` wide near unit magnitude. **Nothing measured comes within seven
  orders of magnitude of it.**

## 2 · What each option buys, priced against that

### (a) One portable `log` in both runtimes

**Buys:** bit-identical scores, so the third differential arm can assert
byte-equality on the `--json` payload exactly as the accelerator arm does today
— one law, one assertion, no second vocabulary for "equal enough".

**Costs:** `bm25f.idf` changes, so **every committed golden, every filed score
and the existing two-arm differential law are re-derived in Python first**. It
is a corpus-wide ranking change made to fix a difference that no measurement
here can see. It also adds a hand-rolled transcendental to the runtime — under
L1 that is allowed (stdlib only, no dependency) but it is a new thing to be
wrong in, and being wrong in it is a silent, corpus-wide ranking error.

### (b) The arm compares at `round(9)`

**Buys:** no Python change, no golden re-derivation, no new arithmetic. The
tolerance is **the sort key's own resolution**, not a number invented to make a
test pass — which is the distinction between a tolerance and a moved threshold.

**Costs:** the third arm asserts something weaker than the accelerator arm does.
`ids`, `order`, `locs`, `headings` and `band` would still be byte-equal; only
the score *field* is compared at `round(9)`. A future divergence larger than one
ulp would have to be caught by the ordering assertion rather than the score one.

## 3 · The one thing that would change the answer

🔴 **The `idf` argument population in this run is 13 distinct values.** That is
a property of a 10-document corpus and a synthetic 10 000-document one whose
query terms are near-unique — not a property of fux. A corpus with a wide `df`
spread samples far more of `log`'s domain, and on the wide sample **0.655 % of
arguments do diverge**.

**So "0 discordant on 197 233 scored documents" is a true count and a weak
guarantee.** What makes option (b) defensible is not that count — it is that
every measured divergence is one ulp and `round(9)` cannot see one ulp. If a
divergence larger than ~`1e-9` relative is ever measured on any platform pair,
(b) collapses and (a) is the only option left.

**Improvement, with its repro:** widen the `idf` population before Phase 1 by
probing `log` over every `(df, n)` a real corpus produces — this repo's own
`.fux/index/` is the obvious one and is not synthetic.

```bash
E=work/regression/2026-09-05-node-log-divergence/evidence
python $E/dump.py . <(git ls-files '*.md' | head -200 | sed 's/.*/{"q": "&"}/') /tmp/self.json
python $E/logprobe.py /tmp/self.json /tmp/args.json && node $E/logprobe.mjs /tmp/args.json
```

## 4 · Unresolved, and it blocks Phase 1 rather than the decision

**Only one platform pair was measured.** macOS/Apple-libm against
V8-on-darwin-arm64. W-107's hazard cites **glibc 2.39**, which is what CI runs,
and this machine has no Linux. Node 20 and 22 — the versions the Phase 4 CI
matrix names — were not run either.

**This is not a reason to delay the decision** (the shape of the finding — one
ulp — is a property of two IEEE-conforming libms and will not become a
1e-9 difference on a third). **It is a reason not to freeze the
pre-registration's comparison clause until the Linux number exists**, because a
pre-registered threshold may never move, and freezing a tolerance on one
platform pair is exactly how one ends up moved later.

## 5 · What this run cannot support

- Any claim about glibc, musl, Node 20/22, or x86-64.
- Any claim that fux's scores are byte-identical across runtimes **in general**
  — only that they were, on these two corpora, whose `idf` arguments take 13
  distinct values.
- Any statement above 10 000 documents.
