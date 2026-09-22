---
type: OpenItem
id: W-214
title: "W-214 — the abstention gate's premise is measured and unsupported: `separation` does not carry correctness, and only Arpit may decide what the band becomes"
description: "W-213 measured the benefit half phase D could not. Across 2 992 questions, eight rungs and three independently authored sets, the questions the band withheld were MORE likely to be right than the ones it answered, risk rises as coverage falls on all three sets, and the band withheld fewer wrong answers than a rate-matched coin in all three. No floor fixes it, including 0.00. What the band should become reverses Arpit's W-176 gate 1 ruling and is his."
status: open
lane: build
timestamp: 2026-09-22T00:00:00Z
filed: 2026-09-22
ball: agent
---

# W-214 — the band refuses answers and buys nothing measurable by doing it

## ✅ RULED 2026-09-22 (Arpit, Cowork) — **option B**. Ratified, NOT built.

*"I'll go with option B, that is demote weak to a signal and stop it refusing."*

**So: `weak` stops being a refusal and becomes a published signal.** `answerable`
returns to `band != none`; the `weak` band, the four signals and
`failed: ["separation"]` are all still emitted, so a consumer that wants the old
behaviour has every byte it needs to implement it itself — **fux stops making
that choice on the consumer's behalf.**

🔴 **This reverses [SR-CONFIDENCE](../../records/0141_confidence.md) decision 3a
— his own W-176 gate 1 ruling of 2026-09-14 — and only this ruling could.** The
premise behind 3a (*ten wrong links produce a confident wrong answer*) is the one
[W-213](../regression/2026-09-22-band-operating-point/VERDICT.md) put a number
against: across 2 992 questions, eight rungs and three independently authored
sets, **the questions the band withheld were more likely to be RIGHT than the
ones it answered**, risk rose as coverage fell in all three sets, and the band
suppressed fewer wrong answers than a rate-matched coin in all three.

⚠ **What he is knowingly buying back, and it is a real cost.** Decision 3a exists
because `band != none` is **structurally almost never false** — BM25F scores
something for nearly any query — so after this change `answerable: false` fires
essentially only on an empty result set. **The W-48/W-176 gap re-opens: a field
that can hardly fire.** The difference from the pre-W-176 state is that the
disagreement is no longer silent — the band table must now say *signal*, not *do
not answer*, so two fields on one payload never again contradict each other.

**Model: Sonnet.** The code change is one expression per plane; the records,
the docs and the two tests are the work.

### Definition of done

1. **Python** — `src/fux/query/confidence.py`: `answerable` returns
   `self.band != NONE`. `failed` is unchanged and still carries `separation`.
2. **Node twin** — `node/src/query/confidence.mjs` line 71: the same change,
   `this.band !== NONE`. **Both planes move in one commit**, and the bundle is
   regenerated (`python -m fux.store.nodebundle node node/dist`, [L10](../../records/0011_LAW-10-bundled-output.md)).
3. **The band table stops saying *do not answer*.** SR-CONFIDENCE decision 3's
   `weak` row becomes *a signal: the ranking could not choose between the top
   hits — decide for yourself*, and **decision 3a is rewritten as the reversal
   it is**, dated, quoting this ruling, keeping the four-run table that produced
   it and naming the gap it re-opens. **Nothing is deleted from the record's
   history.**
4. **Every docstring that states the old rule is rewritten**, not just the
   expression — `confidence.py`'s `answerable` docstring is currently an
   argument FOR the behaviour being removed, and a stale docstring beside a
   reversed expression is how the next session gets it wrong.
5. **The agent-facing surfaces are re-stated**, because they tell agents to
   abstain: `.claude/skills/fux-search/SKILL.md`, `fux-answer`, `fux-mcp`,
   `fux-serve`, `.claude/commands/fux-search.md`, `fux-answer.md`, and
   `.claude/output-styles/fux-cited.md` ([SR-WORK-DOCS](../../records/0059_WORK-docs.md) decisions 6–8 apply).
6. **`docs/paper/the-fux-index-paper.md` §confidence and `fig-09-confidence`
   (both `.mmd` and the rendered `.svg`) carry the new semantics.**
7. **`work/IMPLEMENTATION.md`** records what landed; the registry row's
   `last-verified` bumps in the same change
   ([SR-WORK-REGISTRY](../../records/0067_WORK-registry.md)).

### Tests

- `tests/query/test_confidence.py::test_the_band_table_and_answerable_cannot_disagree`
  **must still pass** — it walks every band, and it is the gate that makes this
  change honest rather than a second silent disagreement. Update its expectation
  for `weak`, do not weaken the test.
- `test_a_zero_floor_makes_every_answer_answerable_and_that_is_the_cost` — check
  whether it still says anything true once `weak` is answerable at every floor;
  if it does not, **rewrite it, do not delete it**.
- **A new test that `weak` is still EMITTED** — band, `separation`, and
  `failed: ["separation"]` — because the whole ruling is *keep the signal, drop
  the refusal*, and a later cleanup that removes the now-unused `weak` branch
  would silently complete the wrong half of it.
- `node --test node/test/*.test.mjs` covers the twin.
- Both suites whole, per [`work/LESSONS.md`](../LESSONS.md).

### Out of scope

- **`separation_floor` does not move.** W-213 ruled it stays at `0.10` and this
  ruling does not reopen that verdict; the floor still decides the `weak` label,
  which is still published.
- **Option C (`doc_coverage` as the gated quantity) is not chosen and not
  killed** — it remains a lead needing its own pre-registration, and nothing
  here builds toward it.
- **Option D's judged arm is not commissioned.**
- **No re-measurement is required to land this.** The change is a ruling, not a
  prediction, so it owes no pre-registration — but it **does** change what
  `answerable` means on every future run, so any filed number that counted
  abstentions is about the old semantics and says so.


⚠ **He has ruled — see the block above. The sections below are the evidence
and the options AS THEY STOOD BEFORE the ruling**, kept because the argument
outlives the call. **Read the ruling for what is to be built.**

## What is measured

[W-213](../regression/2026-09-22-band-operating-point/VERDICT.md), `informed`
permanently. 2 992 questions · 8 rungs · 3 retired sets · HEAD `7d41fdab`.

| at the shipped `separation_floor = 0.10` | set-1 | set-2 | set-3 |
|---|---:|---:|---:|
| risk among what it **answered** | 0.335 | 0.516 | 0.489 |
| risk among what it **withheld** | **0.325** | **0.469** | **0.385** |
| wrong answers it suppressed | 62 | 135 | 104 |
| a coin withholding at its own rate would have suppressed | 63.6 | 144.6 | 124.5 |

🔴 **In every set, the questions it withheld were more likely to be right than
the ones it answered.** Removing the 96 key-unanswerable rows per set — which
can only flatter the gate, since answering one is always scored wrong — **widens
every gap**.

🔴 **Risk RISES as coverage falls, on all three sets** (set-1 `0.333 → 0.394`,
set-2 `0.502 → 0.534`, set-3 `0.461 → 0.600`). A working abstention gate makes
risk fall. **That is why no threshold wins: the threshold is not misplaced, the
quantity it thresholds does not carry the information.**

⚠ **And `0.00` — the clause OFF — did not clear the paired bar either.** *Turn
it off* has exactly as much support as *lower it*, which is none. **There is no
agent-closable move here.**

## Why this is his and not an agent's

**W-176 gate 1 (Arpit, 2026-09-14) ruled that `weak` IS a refusal**, reversing a
`answerable: band != NONE` that could never fire. The argument behind it —
[SR-CONFIDENCE](../../records/0141_confidence.md) decision 3's *ten wrong links
produce a confident wrong answer* — is exactly the premise this run puts a number
against. **A measurement is not a licence to undo a ruling**, and
[SR-LAW-0](../../records/0002_LAW-0-authority.md) is explicit about who moves
what.

⚠ **It is also the most consumer-visible field fux has.** `answerable: false` is
what an agent branches on; changing when it fires changes every consumer's
behaviour at once, and `fux answer` returns text on every call regardless — so a
consumer that ignores the flag sees no abstention at all today.

## The question, stated so it can be answered in one line

**Which of these is the band's future?**

| | option | what it costs | what it buys |
|---|---|---|---|
| **A** | **leave it exactly as it is** | ~25 % of answerable questions withheld for no measured benefit | no consumer churn; the mechanism stays for a corpus where it may work |
| **B** | **keep `weak` as a SIGNAL, stop it refusing** — `answerable` returns to `band != NONE`, `failed: ["separation"]` still published | re-opens the W-48/W-176 gap Arpit closed: a field that never fires | ~749 suppressed answers per ladder come back, of which the proxy calls ~60 % right |
| **C** | **replace the quantity** — gate on `doc_coverage` (*does the top document cover the question*) instead of `separation` | a new pre-registration and a build; `doc_coverage_floor` ships at `0.0`, the clause off | it asks something much nearer to correctness. **Untested — this is a lead, not a result** |
| **D** | **measure again with a judged arm first**, then decide | time; every hosted judge is barred by [L1](../../records/0003_LAW-1-zero-cost.md), so it needs a local FOSS one set up | tests the one assumption W-213 rests on — see below |

## What would falsify W-213's finding, named

🔴 **One assumption carries all of it:** the proxy (`evidence_quoted`, a
normalised substring test) must under-detect correctness **equally on both sides
of the gate**. A uniform miss cancels in a between-group comparison. **If fux
paraphrases more on high-separation queries than on low-separation ones, the
cancellation fails and the finding weakens.** That is option D's job and it is
the honest first move if he wants one.

⚠ **What is NOT claimed:** that the band is *worse* than random. Three sets
agreeing in direction is `p = 0.25` on a sign test, and only set-3 is
individually distinguishable (`p = 0.0123`). **The supported claim is: no
evidence the abstention beats chance, with the point estimate on the wrong side
everywhere.**

## Out of scope

`doc_coverage_floor`'s own sweep (option C's build, and **its own
pre-registration**), the judged series as a general instrument
([SR-WORK-QUALITY](../../records/0056_WORK-quality.md) decision 9), and anything
that moves `separation_floor` — W-213 ruled it stays at `0.10` and that verdict
is not reopened by this item.
