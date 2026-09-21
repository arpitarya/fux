---
type: Analysis
run: 2026-09-21-ladder-set-3-rebuild
description: "Three things the rebuild had to decide that prompt 4 does not cover, and two it found. The ceiling decides the rung sizes; the ext tail is what gives way; and the ladder having links at last is an unblock, never a result."
filed: 2026-09-21
---

# ANALYSIS — what the set-3 rebuild decided, and what it found

## 1 · The seed grew, so something had to give — and the ceiling chose which

**Diagnosis.** `build_golden_rung.py` takes `--count` as *total documents,
seeds included*, so a seed that grows by eight either pushes eight generated
documents out of every rung or pushes every rung eight documents higher. Prompt
4 does not decide this, because when it was written the seed had never grown.

**Change, specific:** the rung totals stay at their headline sizes and the **ext
tail gives way**. `rung-10000` at 10 008 documents would be **through the ceiling**
[SR-WORK-SCALE](../../../records/0057_WORK-scale.md) sets at 10 000 — a ceiling
on *what may be measured*, not a rounding convention — and no other rung's size
has any meaning independent of the top one.

```bash
.venv/bin/python work/regression/2026-09-21-ladder-set-3-rebuild/evidence/rebuild.py rung-00100
```

**Unresolved, and stated as such:** the ladder's rungs are now *"100 documents,
28 of them seed"* where they were *"100 documents, 20 of them seed"*. **The seed
fraction rose from 20 % to 28 % at `rung-00100` and is unchanged at
`rung-10000`** (0.20 % → 0.28 %). Nothing in this run measures what that does to
a ranking at the small end, and **no number from this ladder may be differenced
against the old one** for exactly that reason.

## 2 · `rung-seed` is 28, and that is a definition rather than a change

**Diagnosis.** The old `RUNGS` table hardcoded `("rung-seed", 20)`, which read as
a target and was a snapshot. Passing 20 against a 28-document seed makes
`ext_n = -8`, and the builder's own `len(all_docs) != count` check refuses it.

**Change, specific:** the driver passes `None` for `rung-seed` and resolves it to
`len(seed_docs)` at run time, so the seed rung is *the seed corpus* by
construction and cannot fall out of date again.

## 3 · The block boundary — checked because it could have been silent

**Diagnosis.** The generator emits blocks of ten, and **slots 5 and 6 are a
supersession pair**: slot 5 is the retired document, slot 6 declares
`supersedes:` pointing at it. Every rung's ext count used to be a multiple of
ten; they are now `≡ 2 (mod 10)`. A boundary between slots 5 and 6 would put a
`supersedes:` target outside the rung.

**Why it is safe, and it is arithmetic rather than luck:** truncation can only
ever drop the *later* member of the pair, and slot 6 is the later one. A rung can
hold a retired document with no successor; it can never hold a successor with no
target. The builder's `unknown` check would have refused it, and refused nothing.

**Measured cost of the off-block tail:** at `rung-00100`, sibling 29 · adjacent
22 · filler 14 · variant 7 of 72, against an exact 40/30/20/10 of 28.8 · 21.6 ·
14.4 · 7.2 — **the closest integers to the declared mix.** The effect is nil.

## 4 · 🔴 FOUND: the ladder has `ref` edges for the first time, and that is an unblock and not a result

**61 on every rung, from 0.** Three features were built against this ladder and
none of them could be measured, because the input they act on was not in the
corpus — the failure [SR-RS](../../../records/0133_predictions.md) decision 23
names, and the reason [W-191](../../../archive/open/W-191-the-ladder-carries-no-links.md)
existed.

🔴 **What this run must not be read as saying.** It says the input exists. It says
nothing about whether anchor text, the `related` tier or gate 6 improves anything,
and `[bm25f] anchor` remains `0.0` on every rung. **A weight moves only on its own
passing pre-registered run**, and this run has no arms, no endpoint and no
threshold.

⚠ **61 edges from 8 source documents is a concentrated graph.** All eight sources
are set-3 documents, 25 of the 28 seed documents are targets, and `22-cold-chain-document-map.md`
is a hub by design. A link feature measured here is measured on **one author's
linking style** — which is better than zero and is not a general claim, and the
first arm that uses it should say so in its own pre-registration.

## 5 · 🔴 FOUND: the seed-drift gate fired first, and the suite was red until the rebuild landed

`tests/test_golden_ladder_seed.py` failed on **8 of 8 rungs** in this session's
baseline run, before anything was rebuilt. That is the gate built after the
2026-09-15 drift working exactly as designed, on the next occurrence.

⚠ **The consequence is worth naming rather than discovering:** **adding a seed
document makes the fast suite red**, repo-wide, until all eight rungs are rebuilt
— and a full rebuild is ~50 minutes of wall clock, dominated by one git commit
per distinct document date (2 446 commits at `rung-10000`). A session that adds a
seed document and stops has left the repository failing.

**Not escalated into a change.** The alternative — a gate that warns instead of
failing — is the state the ladder was in for the weeks that produced two silent
drifts. **Red is correct here**; what was missing was anyone saying how long it
takes to go green, and that is now written down.

## 6 · ⚠ Recorded, not resolved: the L11 hook fired on a document *about* the rule

Writing `work/golden/README.md` was blocked by
`.claude/hooks/guard-golden-answer.sh` because the **prose** named the
singular-spelled key directory. The guard matches a bare substring of the command
and fails closed, which is right; the cost is that a document explaining the rule
cannot spell the thing it explains.

**This is the fourth recorded occurrence of the class** (W-198 named it; W-204
phase A was the third, on its own pre-registration). The document was reworded to
cite L11's decisions instead, and **no guard was weakened** — the same resolution
the previous occurrence took.

🔴 **It is put to Arpit rather than fixed here**, because every available fix is a
judgment about the law's surface, not an implementation detail: narrowing the
hook to tool calls that *target* the path would weaken a guard whose whole value
is failing closed, and a convention that *prose may never spell either path*
would need to exempt the law and the records that already do. **Two strikes makes
a gate owed** ([SR-WORK-SESSION](../../../records/0060_WORK-session.md) decision
13), and what the gate should assert is his call.
