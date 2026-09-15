---
type: Handoff
name: W-176
description: "The nine abstention gates of compare/abstention-gates.compare.md, ruled (a) by Arpit 2026-09-14: all nine, in order, each behind its own flag, each kept or removed on its own row. Gates 1 and 9 are a rule and text and land now; 4 and 3 are the first measured gates; 2, 7, 8 next; 5 then; 6 after W-161. Every measured gate waits on a golden key with enough unanswerable questions to clear the d19 floor — Codex, 2026-09-30. The verdict stays a weakest-link chain and every signal is returned as its own field under .fux/output.toml (both ruled 2026-09-13)."
item: W-176
filed: 2026-09-14
ball: agent
---

# W-176 — the nine abstention gates, one program

**Model: Opus for gates 4, 5 and 6 (an answer-type grammar, two IR estimators, a
graph statistic); Sonnet for 1, 2, 3, 7, 8, 9 once the pre-registration exists.**

**Ruled 2026-09-14 by Arpit — option (a)** of
[`compare/abstention-gates.compare.md`](../compare/abstention-gates.compare.md),
which stays the spec: §3 is the mechanism table, §4 the output surface (ruled
2026-09-13), §5 the order, §6 what each gate touches, §6b the per-gate
keep/remove rows. **None of it is repeated here.** The two earlier rulings bind
every step: the verdict is a gate chain, weakest link, never a blended number;
and every independent signal is returned as its own field, visibility set in
`.fux/output.toml`.

## ✅ Steps 1–3 landed 2026-09-15 — `c7a274b3`

| step | gate | state |
|---|---|---|
| 1 | **1** `weak` ⇒ `answerable: false` | ✅ done — SR-CONFIDENCE 3a, three tests |
| 2 | **9** consumer steering | ✅ done — both MCP tool descriptions, three guides, four copies each |
| 3 | **output surface** | ✅ done — `failed` names which gate refused; SR-OUTPUT 24 |

🔴 **The defect gate 1 closed was structural, not a threshold.** `answerable`
was `band != none`, and *nothing scored above zero* is the one state no real
corpus produces — BM25F returns something for almost any query. So the refusal
was **unreachable**, which is why four separate runs measured the symptom and
none could name the cause. The cause is one expression.

⚠ **Nothing behavioural broke when it changed.** No test in either suite
asserted the old reading, on either reader. That is the second finding: the
band table and `answerable` had never been held in agreement by anything, and
now `test_the_band_table_and_answerable_cannot_disagree` walks every band and
`test_every_refusal_names_at_least_one_failed_gate` holds `failed` and
`answerable` together — so a **ninth gate added later cannot arrive
answerable-by-default**, which is the direction that loses silently.

**Step 3 was narrowed where §4's ruling met SR-OUTPUT decision 19**, and the
narrowing is recorded rather than taken quietly. §4 says *"`output.toml`
decides which appear, per verb"*. An unset output key is a hard error, so nine
signals would be **nine breaking changes**, each making `fux ask` exit 1 in
every repository whose config predates it. They get **one key between them —
the `band` key that already exists** ([SR-OUTPUT](../../records/0143_output-defaults.md)
decision 24); `--json` carries all of them unconditionally, as ruled. What it
gives up: a consumer cannot show one prose signal and hide another.

**Steps 4–10 are unchanged and still gated.** Every one needs golden
unanswerable questions in enough number to clear the d19 floor — Codex,
2026-09-30. Step 10's other gate, W-161, **is now built**.

## Definition of done — per gate, in this order

| step | gate | kind | bar |
|---|---|---|---|
| 1 | **1** `weak` ⇒ `answerable: false` | rule | unit test on the band table; e2e goldens; SR-CONFIDENCE d3 rewritten |
| 2 | **9** consumer steering | text | MCP descriptions + guide skills say *the documents don't say* on `weak`/`false`; renderings equal templates |
| 3 | **output surface** | plumbing | every signal a field in `--json`; `output.toml` toggles the prose keys; Node byte-equal. Lands with step 1 so later gates only add a field |
| 4 | **4** answer-type check | measured | pre-register → flag → measure both directions → call |
| 5 | **3** passage co-occurrence | measured | same |
| 6 | **2** IDF-weighted coverage | measured | same |
| 7 | **7** identifier hard-fail | measured | same; rides on W-168 step 3's identifier field if it has landed, exact-token check otherwise |
| 8 | **8** verification floor | measured | same; the answer gate's floor |
| 9 | **5** QPP — NQC, Clarity | measured | same; pure functions of scores, df, n |
| 10 | **6** graph coherence | measured | **after W-161**; degrades to `unknown` on a link-poor corpus, tested |

**Every measured gate:** pre-register both directions (SR-RS d22) → implement
behind `[confidence] gate_<name> = false` → measure on golden unanswerable
**and** answerable classes → keep only if abstentions rise on unanswerable
(net ≥ SR-RS d19 floor) **and** zero new abstentions on answerable. **Remove =
the flag stays, default off, the record names the failed direction.** A
withdrawn gate is never loosened to pass. Never tune on the 20 blind-authored
unanswerables; they are the frozen control.

## What gates the measured steps

- 🟣 **The golden key must carry enough unanswerable questions** for the d19
  floor to be reachable. That is a Codex task, never Claude's, and Codex is
  available **2026-09-30**. Steps 1–3 do not wait; steps 4–10 do.
- 🔴 **Step 10 has a second, harder gate found 2026-09-15: the ladder has no
  links.** [The anchor mechanism probe](../regression/2026-09-15-anchor-mechanism/report.md)
  counted **0 `ref` edges on all eight rungs**, and `[graph] ask_kinds` follows
  `ref` alone — so the graph-coherence gate would return **`unknown` for every
  question**, which is its specified link-poor degradation and is therefore
  **currently its only reachable outcome**. It is testable in that state and
  **not measurable** in any other, until the corpus carries links.
- Step 10 also waits on [W-161](W-161-graph-composed-ask.md).

## Out of scope

- A blended confidence number — refused by ruling, not deferred.
- Any gate tuned on the 20 controls.
- A tenth mechanism; a new one is a compare-doc amendment first.

## Verification, and the keep/remove call

Per gate, §6b's row is the whole call. The program closes when every row
reads *kept* or *removed*, SR-CONFIDENCE names each kept gate and each withdrawn
one with its failed direction, and the golden ladder's headline carries
*abstains k of N* beside every quality number.

## Records this will touch

SR-CONFIDENCE · SR-REFER-PLANE · SR-CHUNKING · SR-ANSWER · SR-RANKING ·
SR-RUNTIME-STATS · SR-GRAPH · SR-AGENT-POLICY · SR-MCP · SR-OUTPUT-DEFAULTS ·
SR-NODE-SEARCH · SR-RS (d22 both directions, on every arm).
