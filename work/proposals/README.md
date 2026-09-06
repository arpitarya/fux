# `work/proposals/` — parked ideas

**How to use this directory.** Ideas worth keeping that are **not being built
now** and **not yet decided**. Same rigor as a compare doc — context, sketch,
grounded references — but for future work rather than an active fork.

**A live fork gets [`../compare/`](../compare/README.md); a not-yet-decided
idea gets a proposal here.** Nothing in this directory is a commitment;
everything in it is findable.

Every proposal names its **graduation trigger**: the condition under which it
stops being parked. Without one it is a wish, and it will sit here forever.

Per OKF, every file here carries frontmatter:

```yaml
---
type: Proposal
title: <idea>
description: <one line>
status: proposed        # proposed | graduated | rejected
timestamp: <ISO 8601>
---
```

**Lifecycle.** `proposed` → picked up → **graduates** into a compare doc (if
there is a fork) or a plan entry (if not), and this file's status is updated
with a link. A **fully implemented** proposal moves to
[`../../archive/`](../../archive/README.md) with a row naming its live
successor; so does a **superseded** one, because a deleted document leaves no
trace that anything is missing.

⚠ **A `graduated` file may still live here** — that is what `graduated` means:
the decision moved into a record or a queue item, and the file is kept because
part of it is still to do. `search-v3.md` is the worked example.

---

# Index

*Newest first. Every `.md` in this directory has a row; a file with no row is
the defect this ordering exists to make visible.*

## Filed 2026-09-05

* [Unblock 2026-09-05 — a proposed ruling for every row in the inbox](unblock-2026-09-05.md)
  — eleven rows were *Blocked on Arpit*, six past the 5-day threshold. Proposes
  a default per row (`R-1`…`R-11`, plus W-112's compare doc) with the evidence
  beside it, names the agent-lane items that need no ruling, and two rows the
  repo had already closed (Windows e2e runs in CI; the clean-recall number is
  the doc2query `none` arm). **Nothing implemented, nothing defaulted.**
  **Graduates when Arpit strikes or accepts each line.**
* [Claude Code prompt — execute the 2026-09-05 unblock](unblock-2026-09-05-claude-code-prompt.md)
  — the companion. A bracket per line; **anything left blank is a blocker, not
  a default.** Graduates with the document above.

## Filed 2026-09-04

* [Search v3 — better answers per verb, a Node.js read plane, and agent-run vectors](search-v3.md)
  — ✅ **`graduated`: RATIFIED by Arpit 2026-09-05**, and **five of its seven
  items have closed** (W-108, W-109, W-110, W-111 landed; W-107 Phase 0 and
  W-106 measured). **W-107 Phases 1–4 and W-112 remain**, both on Arpit, which
  is why it is still here rather than archived. Where `ask`/`find`/`answer`
  lose (measured), the fixes inside L1–L8, the Python-writes /
  Python-or-Node-reads split, the pinned vector plane an agent can produce, the
  target architecture ([`../architecture-search-v3.svg`](../architecture-search-v3.svg)),
  the research appendix, and the plan — **W-106 … W-112**, each with a detail
  file under [`../open/`](../open/README.md).
  ⚠ **Its frontmatter said the three proposals it supersedes were "deleted in
  the same change". They were not** — they sat here unindexed until 2026-09-05
  and were then archived. Corrected in the file.
* [Claude Code prompt — execute Search v3](search-v3-claude-code-prompt.md)
  — `graduated`: **this is the ratification instrument**, handed over and
  executed on 2026-09-05. Kept as the record of what was authorised and in what
  order, not because anything in it is still to do.

## Filed 2026-08-28 — two reviews

⚠ **Both are findings to verify, not landed facts, and each says so.** Neither
has been audited against what has since shipped; a session acting on one
re-derives its claims first.

* [ADR review — 2026-08-28](adr-review-2026-08-28.md) — all 47 live records
  read against the register's own rules. *"The rule set is excellent; the
  records don't follow it, and nothing mechanical notices."* Five rules each
  broken in 20–45 of 47. **Record-vs-record only** — no claim in it was checked
  against `src/` or `tests/`. **Graduates into lint tests plus one bulk pass**;
  some of that has since landed (`test_adr_ownership`, `test_adr_freshness`,
  the `describes` relation), **which nobody has reconciled against this list.**
* [Code + architecture review — 2026-08-28](architecture-review-2026-08-28.md)
  — *"Nothing here says rebuild again."* The risk has moved from design to
  **drift**: records describing behaviour the code does not have (the W-83
  class). ⚠ **Ran on a cloud mirror with a wedged shell — no git, no test
  run**, so every P0/P1 is to reproduce. **Graduates item by item as each is
  verified on the real tree.**

## Filed 2026-08-26

* [Structure-aware extraction](structure-aware-extraction.md) — tables, code
  fences and lists as **fields, not decoders**. By the time a decoder finishes,
  a table **is already Markdown**, and weighting it is `extract.py`'s job.
  ⚠ **The boundary is the load-bearing part:** in decoders, every
  consumer-owned decoder re-implements ranking policy in code fux cannot test
  or version; in `extract.py`, one implementation and every format inherits it
  free. Names the strongest concrete suspicion — **table cells inflate `flen`,
  so BM25 length normalisation makes a table-heavy document read as denser than
  it is**. **Graduates when W-86's P4 (OOXML) lands**; a ranking change then
  needs a pre-registration and a verdict at 10 000 documents, never an argument.

## Filed 2026-08-22

* [Ranking tuning, and the utility that would do it](ranking-tuning.md) —
  research note. **Twelve ranking constants**, and the literature's verdict that
  tuning `k1`/`b` buys ~nothing (Anserini's 5-fold CV recovers the default to
  four decimals on 250 topics). Argues the **instrument** (evaluate + gate) is
  the product and the **optimiser** is not, and that judgment supply — not
  search — is the binding constraint.
  ⚠ **Substantially overtaken.** ADR-TUNE shipped 2026-08-24, so *"one of them
  configurable"* is false; the integer-field-weight constraint it names was
  **dissolved by W-73**; its *"one decision waiting"* was the **hybrid
  default**, and that lane was deleted 2026-08-25. It also proposes the verb
  name `fux tune`, **which ADR-TUNE has since taken for something else.**
  🔴 **Its graduation trigger named the hybrid default and can never fire as
  written.** The live successor for the question it asks is **W-97**, the knob
  sweep, whose pre-registration is
  [`../benchmark/PRE-REGISTRATION-TUNER.md`](../benchmark/PRE-REGISTRATION-TUNER.md).
* [T2 segments](t2-segments.md) — **was ADR-T2-SEGMENTS (0037) until Arpit
  moved it here the same day.** The record that **T2 is not built**, decided by
  measurement: [R9](../regression/2026-08-22-r9-t2-at-10k/VERDICT.md) answered
  worst-case queries in **12.46 ms against a 150 ms bar**. **Nothing was ever
  built** — no `tpack`, no BIC codec, no `tier` knob in `src/`. Its old veto is
  now a **graduation trigger**, and the difference matters: *a veto is checked,
  a trigger is remembered*. **Graduates if a measured warm p95 exceeds 150 ms**
  — a number, never a corpus size. ⚠ Two frozen files still cite it as an ADR
  and always will; see its head.

## Filed 2026-08-10

* [Agent search-API landscape](agent-search-landscape.md) — research note, not
  a build item: Parallel / Perplexity / Exa / Brave independently arrived at
  three index-and-refer decisions, and the corpus they *cannot* reach names
  Fux's wedge. **The evidence base the refer-plane proposals cited.**
  *(Both of those graduated and were archived 2026-08-20 when M4's core landed;
  their live successor is [ADR-REFER](../../docs/adr/0037_refer-plane.md). One
  shipped with its central knob deliberately refused — the reasoning is in the
  record and the open question is
  [W-58](../../archive/open/W-58-no-recorded-ingest-time.md).)*

## Filed 2026-08-09 — for the v0.30 architecture

* [MCP as the adapter endgame](mcp-adapters.md) — one protocol instead of
  per-app adapters; the org's own auth. **Graduates on the first MCP-gateway
  design partner or a fourth adapter request.**
* [Knowledge CI](knowledge-ci.md) — PRs fail when the index is stale; decisions
  the diff contradicts surface as cited review comments. **Graduates after M6
  dogfoods green two weeks.**
* [Wavelet-tree self-index](wavelet-self-index.md) — research note preserving
  the rejected option C of the keyspace compare. **Reopens only on a law change
  or a P5 bottleneck.**

## Carried over from 2026-07-21 — architecture-agnostic survivors

Both are *strengthened* by the v0.30 index-and-refer rebuild: the MST keyspace
gives them their substrate natively.

* [Research-to-Spec](research-to-spec.md) — evidence-backed specs; every claim
  cites the corpus at a commit.
* [Knowledge diff & time-travel](knowledge-diff.md) — `fux diff` / `fux log`;
  ask questions of past knowledge. A natural fit for the one-root-hash keyspace.

*(The third survivor, **audit evidence trail**, graduated 2026-08-27 into
[ADR-PROVENANCE](../../docs/adr/0053_provenance.md) and was **archived
2026-09-05** — see below. The fourth idea from that ideation, the
**product-memory corpus**, graduated into the v0.26 plan; its successor concept
is the committed index + ledger of the current architecture.)*

---

# Left this directory

*Rows live in [`../../archive/README.md`](../../archive/README.md); they are
named here so the reason is findable from where the file used to be.*
**Archive is not evidence** — any of these may be named, none may be cited as
backing a live claim.

| left | when | why, and the live successor |
|---|---|---|
| [`audit-evidence-trail.md`](../../archive/proposals/audit-evidence-trail.md) | 2026-09-05 | **Graduated 2026-08-27 → [ADR-PROVENANCE](../../docs/adr/0053_provenance.md)**; `fux answer --audit`, `--receipt`, `--journal`, `ask --why` and `fux verify` all shipped. It then sat here nine days against this file's own lifecycle rule — **the move was late, the decision never changed.** ⚠ Its graduation trigger, *an enterprise design partner materializes*, **never fired and could not**: it waited on somebody else's arrival rather than naming a condition anyone here could check |
| [`node-search-port.md`](../../archive/proposals/node-search-port.md) · [`agent-run-embeddings.md`](../../archive/proposals/agent-run-embeddings.md) · [`retrieval-quality-per-verb.md`](../../archive/proposals/retrieval-quality-per-verb.md) | 2026-09-05 | **Superseded 2026-09-04** by [`search-v3.md`](search-v3.md), which folded all three in whole. Live successors: **W-107**, **W-112**, and **W-108 … W-111**. ⚠ `search-v3.md` said they were *"deleted in the same change"* — **they never were**, and they sat here unindexed for two days |
| [`tune-file-and-source-priority.md`](../../archive/proposals/tune-file-and-source-priority.md) | 2026-08-27 | Graduated 2026-08-22 → [ADR-TUNE](../../docs/adr/0045_tuning.md); kept for the survey and its ten forks as they were put |
| [`playground-goldens-draft.md`](../../archive/proposals/playground-goldens-draft.md) | 2026-08-27 | Graduated 2026-08-24 when Arpit waived the human-author rule and the 50 candidates were installed; the run is [`../regression/2026-08-24-rerank-and-goldens/`](../regression/2026-08-24-rerank-and-goldens/report.md) |
| [`answer-provenance.md`](../../archive/proposals/answer-provenance.md) | 2026-08-27 | Graduated same-day → [ADR-PROVENANCE](../../docs/adr/0053_provenance.md), built and green. Kept for the prior-art table and **five open forks**, of which fork 1 — always-on journalling as an ADR-TUNE key — is the one a session will be tempted to default |
| [`consumer-intent-policy.md`](../../archive/proposals/consumer-intent-policy.md) | 2026-08-22 | Became [ADR-AGENT-POLICY](../../docs/adr/0042_agent-policy.md), accepted **and built**: `fux setup` installs the four renderings, which live at [`src/fux/templates/agents/`](../../src/fux/templates/agents/) |
| [`process-diet.md`](../../archive/proposals/process-diet.md) | 2026-08-21 | Graduated same-session (PRIORITY P7); the `Cost:` line is gone from the WORKLOG format |

**v0.26-era proposals** (tied to the archived substrate engine) are at
[`archive/v0.26/proposals/`](../../archive/v0.26/proposals/):
knowledge-substrate (superseded by the index-and-refer architecture),
chunk-level-dense-codes, and hybrid-degrades-at-scale (✅ resolved 2026-07-22 as
a corpus artifact).
