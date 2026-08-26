# W-74 — fux has no contract for what "right" means

**Status:** OPEN
**Lane:** `arpit` — **six forks gate what gets built** ([the proposal](../proposals/measuring-answer-quality.md) §11).
The agent-executable remainder is named below and starts the moment forks 1–4 are ruled.
**Filed:** 2026-08-22 (Cowork), from Arpit's question — *"how right is it going to be?"*
**Spec:** [`../proposals/measuring-answer-quality.md`](../proposals/measuring-answer-quality.md) — this file is the state; the argument is there
**Blocked by:** **forks 1–4** (Arpit) and, for anything that *runs*, **a corpus that does not currently exist** — see Hazards
**Closes with:** **`ADR-RS`** (owns the measurement discipline; this adds what quantity is worth freezing) and, if fork 5 rules for publishing, **`ADR-ANSWER`** (owns the stated ceiling)
**Model:** **Opus** for the fork rulings and the cost vector — every one of them is a judgment about what counts as success, and a metric chosen badly is wrong *quietly* for months. **Sonnet** for the harness once the declarations are frozen: generalising `tools/pruning-eval/pruning/metrics.py` is mechanical work against a written spec.

## The claim

**Fux measures rigorously and has never declared what it is measuring.**

[ADR-RS](../../docs/adr/0036_predictions.md) governs *how* a claim is frozen —
threshold first, verdict never edited, register complete. It is silent on *what
quantity is worth freezing*. Every quality number this project has produced
therefore carries an undeclared query distribution and an implicit cost model in
which a fabricated citation and an honest decline count the same.

## Why it is not hypothetical

Two live runs already passed their number and failed their claim, and a human
caught both:

- [**P1-GATE**](../regression/2026-08-09-pruning-eval/VERDICT.md) — hit@5 delta
  of exactly 0.00 pts, inside a ≤2 pt bar, **because the treatment touched
  0–2.5 % of documents**.
- [**The budget sweep**](../regression/2026-08-22-budget-sweep/ANALYSIS.md) — a
  rule that output *keep* on a result where the kept thing never once won.

A third case cannot be cited at all: the hybrid arm that moved `.182 → .855`
with no engine change lives in `archive/v0.26/conformance/` and **archive is not
evidence**. Its corpus no longer exists.

## Definition of done

**Part A — the declarations (blocked on forks 1–4, then `agent`)**

- [ ] Forks 1–6 ruled, each recorded in the proposal where it was asked.
- [ ] `mix.toml` exists beside the harness: intent classes, weights, and a
      comment on each weight saying **what it is a claim about**. Versioned and
      frozen the way a pre-registration is frozen.
- [ ] The four funnel gates are defined in prose precise enough that two people
      compute the same number: `reachable` · `in window (recall@k)` · `placed
      (nDCG@k, MRR)` · `answered`. Each names its owner.
- [ ] The cost vector is written down with its weights argued, not asserted.
- [ ] **The quotation rule is stated somewhere normative:** no quality figure is
      quotable without `mix@version` and `corpus@id` beside it.

**Part B — the instrument (`agent`, blocked additionally on a corpus)**

- [ ] `tools/pruning-eval/pruning/metrics.py` generalised from
      *"pruning arm A vs B"* to *"any arm, reported per mix class"* — the
      existing `aggregate()` slice mechanism is the seam; the document-level
      aggregation rule copied from `_run_find` **does not change**.
- [ ] Recall@k reported as the ceiling, separately from placement.
- [ ] Paired bootstrap over per-query ranks; every delta carries an interval and
      the run states its minimum detectable effect.
- [ ] A run filed under [`../regression/`](../regression/README.md) meeting the
      per-run contract, with `mix@version` and `corpus@id` in its frontmatter.

**Part C — only if fork 5 rules for it**

- [ ] The scorecard published, and `ADR-ANSWER` updated to say the ceiling it
      already promises is now a measured number.

## Hazards

- ⚠ **Part B cannot run today and saying otherwise would be the third instance
  of the defect this item exists to fix.** `acme` and `orbit` were lost in the
  2026-08-20 `fux-lab` wipe with their generator; `tools/pruning-eval/` still
  hard-codes reading them; the five-tier redesign (10/100/1 000/5 000/10 000) is
  **specified and unexecuted**, with two open questions that are Arpit's
  ([SETUP-LAB](../setup/fux-lab.md)). **Part A is worth doing anyway** — it is
  declaration, not measurement, and declaring is most of its value.
- ⚠ **This is not a re-filing of
  [W-62](../../archive/open/W-62-measure-against-the-outside-world.md).** That
  item's parts 1 and 2 — the three-way comparison and the five external
  cold-start reports — were **withdrawn by Arpit, 2026-08-22**, are his
  personally, and its own note says **no agent should re-file them**. W-74
  measures **fux against itself over time**, against its own corpora. If the two
  are ever confused, W-74 yields.
- ⚠ **Fork 4 is the one that can quietly break a law-adjacent property.**
  Measuring the `answered` gate needs a judge model. That is outside the
  maintenance path, so **L3 is not violated** — but it makes the number
  non-reproducible and model-version-dependent, which is what the frozen
  threshold exists to prevent. Ruling "measure it" without also pinning the
  model and the prompt makes every future comparison meaningless.
- ⚠ **A metric chosen to flatter is undetectable later.** Under-weighting the
  `currency` and `unanswerable` classes raises every number fux reports and
  hides the two failure modes it is known to have. Whoever sets the weights
  should set them **before** seeing what they do to the score — the same
  discipline as ADR-RS, applied one level up.
- **Deliberately not filed in `work/BLOCKED.json`.** These forks block **this
  item only**; nothing else in the queue waits on them, and the repo-level
  decision flag currently reads `PROCEED`. Flipping it would overstate the
  blockage.
