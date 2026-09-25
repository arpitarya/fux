---
type: Index
description: "Index of parked, undecided ideas, each with a graduation trigger."
---

# `work/proposals/` — parked ideas

**How to use this directory.** Ideas worth keeping that are **not being built
now** and **not yet decided**. Same rigor as a compare doc — context, sketch,
grounded references — but for future work rather than an active fork.

**A live fork gets [`../compare/`](../compare/README.md); a not-yet-decided
idea gets a proposal here.** Nothing in this directory is a commitment;
everything in it is findable.

Every proposal names its **graduation trigger**: the condition under which it
stops being parked. Without one it is a wish, and it will sit here forever.

**Every file here also carries one row in [`../BACKLOG.md`](../BACKLOG.md)**, under
*Parked ideas* — the backlog indexes this directory rather than duplicating it, the
row carries the graduation trigger and nothing else, and it is filed and deleted
in the same change as the proposal ([SR-WORK-BACKLOG](../../records/0055_WORK-backlog.md)
rules 6 and 27). A proposal whose remainder has become a `W-nn` carries no row —
`search-improvements-v3.md` (W-168) is the only one today. ⚠ **It was one of two
until 2026-09-20**, when `structure-aware-extraction.md` archived: W-144 closed
2026-09-16 and its boundary argument moved into
[SR-DECODE](../../records/0139_decode.md) §Alternatives.

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
part of it is still to do. `search-improvements-v3.md` is the worked example;
`search-v3.md` was one until every item it graduated into had closed, and it
moved to the archive on 2026-09-14.

---

# Index

*Newest first. Every `.md` in this directory has a row; a file with no row is
the defect this ordering exists to make visible.*

## Filed 2026-09-15

* [Glassbox sessions — event streams as a fux corpus](glassbox-sessions.md) —
  Arpit's ask of 2026-09-14: pull session-replay sessions and *"give me the
  numbers"* — what was on screen when an API call failed, and whether it later
  succeeded in another session. **The connection point already exists**
  (`.fux/fetchers/<name>.py` + `fetch=<name>`), but 🔴 **`fetch=`'s value set is
  closed at [`sourcelist.py:263`](../../src/fux/ingest/sourcelist.py) while
  `urlsrc.py`'s docstring says it resolves by filename** — the two have drifted
  and *no* third fetcher is possible today. Argues the answer is not a fetcher
  at all but **fetch → materialise → index**: aggregate deterministically at
  ingest and let fux *cite* the number, since fux counts nothing and joins
  nothing. ⚠ **Two forks first** — `.fux/index/` is committed and `pii.toml`'s
  regex validators do not bound a DOM snapshot (recommends indexing **dossiers
  only**); and thousands of session lines break `sources/urls`' human-ordered
  premise, which §6 argues dissolves §1 entirely. **Graduates on a second
  event-stream source being asked for** — one request is a use case, two is a
  shape.

## Filed 2026-09-13 — the 3.0 backlog

* [Ten ways to rank better — the 3.0 search backlog](search-improvements-v3.md)
  — ten ranking improvements Arpit kept on 2026-09-13, each independent of the
  graph-composed `ask`: anchor text, corpus-mined expansion, an unstemmed identifier
  field, RM3, supersession-aware ranking, SDM proximity, MMR diversification, a
  git-derived authority prior, an intent → doc-type prior, section-level units. Each
  graduates alone, behind W-156, with its own golden question and pre-registration.

## Filed 2026-08-22

* [Ranking tuning, and the utility that would do it](ranking-tuning.md) —
  research note. **Twelve ranking constants**, and the literature's verdict that
  tuning `k1`/`b` buys ~nothing (Anserini's 5-fold CV recovers the default to
  four decimals on 250 topics). Argues the **instrument** (evaluate + gate) is
  the product and the **optimiser** is not, and that judgment supply — not
  search — is the binding constraint.
  ⚠ **Substantially overtaken.** SR-TUNE shipped 2026-08-24, so *"one of them
  configurable"* is false; the integer-field-weight constraint it names was
  **dissolved by W-73**; its *"one decision waiting"* was the **hybrid
  default**, and that lane was deleted 2026-08-25. It also proposes the verb
  name `fux tune`, **which SR-TUNE has since taken for something else.**
  ⚠ **This row said its trigger *"named the hybrid default and can never fire as
  written"* until 2026-09-12. That was a misreading of the file.** The trigger
  is *"≥ 50 committed judgments on a fux corpus **and** a ranking decision
  waiting on them"* (§9); the hybrid default is named one paragraph later as
  *the candidate that would trip it first*, not as the condition. **The
  condition is alive**, and ⚠ **both items it named are gone** (repointed
  2026-09-20): **W-97 is archived** and **W-136 merged into W-204**. The
  condition itself is unchanged — *50 judgments on a fux corpus and a ranking
  decision waiting* — and both halves now sit in one place:
  [W-204](../regression/2026-09-22-golden-final-score/FINAL-SCORE.md)'s
  scoring pass is where judgments arrive, and phase D's per-query rows are what
  the next ranking decision waits on.
  [SR-WORK-ENVIRONMENTS](../../records/0052_WORK-environments.md) voided the
  playground, so the golden ladder is the only corpus this can run on.
  Pre-registration:
  [`../benchmark/PRE-REGISTRATION-TUNER.md`](../benchmark/PRE-REGISTRATION-TUNER.md).
  **Kept here, not archived:** [SR-LAWS](../../records/0001_LAWS.md) and
  [SR-TUNE](../../records/0135_tuning.md) both cite its §8 survey in their
  Reference blocks — archiving it would move two accepted records' grounding
  into `archive/`.
* [T2 segments](t2-segments.md) — **was SR-T2-SEGMENTS (0037) until Arpit
  moved it here the same day.** The record that **T2 is not built**, decided by
  measurement: [R9](../regression/2026-08-22-r9-t2-at-10k/VERDICT.md) answered
  worst-case queries in **12.46 ms against a 150 ms bar**. **Nothing was ever
  built** — no `tpack`, no BIC codec, no `tier` knob in `src/`. Its old veto is
  now a **graduation trigger**, and the difference matters: *a veto is checked,
  a trigger is remembered*. **Graduates if a measured warm p95 exceeds 150 ms**
  — a number, never a corpus size. ⚠ Two frozen files still cite it as an SR
  and always will; see its head.

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

---

# Left this directory

*Rows live in [`../../archive/README.md`](../../archive/README.md); they are
named here so the reason is findable from where the file used to be.*
**Archive is not evidence** — any of these may be named, none may be cited as
backing a live claim.

| left | when | why, and the live successor |
|---|---|---|
| [`adr-review-2026-08-28.md`](../../archive/proposals/adr-review-2026-08-28.md) | 2026-09-24 | **Overtaken, on Arpit's ruling** (*"Archive ADR review and architecture review."*). A record-vs-record review of 47 records that nobody reconciled against what landed after it — the ownership, freshness and `describes` gates it asked for shipped since. No live successor; its findings are not re-verified, and a session wanting one re-derives it on the current tree |
| [`architecture-review-2026-08-28.md`](../../archive/proposals/architecture-review-2026-08-28.md) | 2026-09-24 | **Overtaken, on Arpit's ruling.** Ran on a cloud mirror with a wedged shell — no git, no test run — so every P0/P1 was *to reproduce*, and none was reconciled in the month since. No live successor; same caveat |
| [`fetcher-routing.md`](../../archive/proposals/fetcher-routing.md) | 2026-09-24 | **Built in full.** Its keep-reason — *the `decoder=` half is W-199 DoD line 10 and is not built* — went stale on 2026-09-21, when that half shipped and W-199 closed. Live successors: [SR-URL-LIST](../../records/0116_url-list.md) 16–17, [SR-FETCHER](../../records/0117_fetcher.md) 16–17, [SR-DECODE](../../records/0139_decode.md) 21 |
| [`identifier-exact-match.md`](../../archive/proposals/identifier-exact-match.md) | 2026-09-24 | **Graduated → W-203 → W-205, closed 2026-09-22.** Kept *"as the argument they cite"*, but no record cites it — only [`BIBLIOGRAPHY.md`](../../records/BIBLIOGRAPHY.md), which may name an archived document. Live successors: [SR-RANKING](../../records/0111_ranking.md) decision 9 and [SR-INGEST](../../records/0106_ingest.md) decision 23d |
| [`quality-endpoint-for-reranking.md`](../../archive/proposals/quality-endpoint-for-reranking.md) | 2026-09-20 | **Its trigger fired, then its successor closed FAIL.** The [screen](../regression/2026-09-15-quality-endpoint-screen/VERDICT.md) returned `agreement` **0.4141** against a chance rate of 0.0748, inside a band frozen one commit earlier; it graduated into **W-154**, and W-154 closed **FAIL** 2026-09-16 — proximity reranking does not earn its latency on `ask`. ⚠ **`archive/README.md` called it a *live successor* of W-183 until the day it archived.** Live successors: [W-154's FAIL](../regression/2026-09-16-rerank-quality-b2/VERDICT.md) · the screen's verdict |
| [`structure-aware-extraction.md`](../../archive/proposals/structure-aware-extraction.md) | 2026-09-20 | **Graduated → W-144, closed 2026-09-16.** Its suspicion — table cells inflating `flen` — was measured and answered, but **not by the fields it proposed**: by lowering `b` to `0.15`, the first measured default in [SR-RANKING](../../records/0111_ranking.md) decision 3. 🔴 Its load-bearing half, the argument that **consumer decoders owning ranking policy is a worse defect than a missing field**, lives in [SR-DECODE](../../records/0139_decode.md) §Alternatives — which is where that record's Reference block was repointed, since an archived doc may not back a live claim |
| [`agent-search-landscape.md`](../../archive/proposals/agent-search-landscape.md) | 2026-09-20 | ⚠ **Its keep-reason was false.** It was held because *"two live records ground on it"*; only [`BIBLIOGRAPHY.md`](../../records/BIBLIOGRAPHY.md) §11 names it, and a bibliography naming an archived document is exactly what SR-WORK-ARCHIVE decision 4 permits. The research stands: four agent search APIs independently arrived at three index-and-refer decisions. Live successors: `BIBLIOGRAPHY.md` §11 · [SR-REFER](../../records/0127_refer-plane.md) |
| [`positioning-documents-not-code.md`](../../archive/proposals/positioning-documents-not-code.md) | 2026-09-20 | **All six surfaces shipped**, and Arpit **overruled the proposal's own framing**: it argued *"the documents around your code"*, which keeps code as the reference point, and the shipped tagline is *"A search index for your written knowledge"*. §5's rename was declined **by the file itself**; §6 went to option (b) and `test_okf_bundle.py` gates it. ⚠ **One line is left and it is not a reason to keep the file: GitHub About/topics is Arpit's `gh`** |
| [`knowledge-diff.md`](../../archive/proposals/knowledge-diff.md) | 2026-09-20 | **No graduation trigger — a wish**, which this file's own rule forbids, and its backlog row said so. 2026-07 era, before the rebuild. 🔴 The primitives it wanted shipped 2026-08-27 as [SR-PROVENANCE](../../records/0142_provenance.md): `--receipt`, `--audit`, `ask --why`, `fux verify`. What it does **not** give is time-travel over past commits — a new decision, not this file's remainder |
| [`research-to-spec.md`](../../archive/proposals/research-to-spec.md) | 2026-09-20 | **Same shape, same era, same answer** — no trigger, 2026-07, evidence-backed specs where every claim cites the corpus at a commit, which is what a receipt is. Live successor: [SR-PROVENANCE](../../records/0142_provenance.md) |
| [`search-v3-claude-code-prompt.md`](../../archive/proposals/search-v3-claude-code-prompt.md) | 2026-09-12 | **Executed in full on 2026-09-05** — Arpit ratified `search-v3.md` §8 through it and five of the seven items closed. It said so itself: *kept... not because anything in it is still to do*, which is this file's own definition of archivable. No live document cited it. Live successors: [`search-v3.md`](../../archive/proposals/search-v3.md) for what remains, and **W-107** and **W-112** |
| [`audit-evidence-trail.md`](../../archive/proposals/audit-evidence-trail.md) | 2026-09-05 | **Graduated 2026-08-27 → [SR-PROVENANCE](../../records/0142_provenance.md)**; `fux answer --audit`, `--receipt`, `--journal`, `ask --why` and `fux verify` all shipped. It then sat here nine days against this file's own lifecycle rule — **the move was late, the decision never changed.** ⚠ Its graduation trigger, *an enterprise design partner materializes*, **never fired and could not**: it waited on somebody else's arrival rather than naming a condition anyone here could check |
| [`node-search-port.md`](../../archive/proposals/node-search-port.md) · [`agent-run-embeddings.md`](../../archive/proposals/agent-run-embeddings.md) · [`retrieval-quality-per-verb.md`](../../archive/proposals/retrieval-quality-per-verb.md) | 2026-09-05 | **Superseded 2026-09-04** by [`search-v3.md`](../../archive/proposals/search-v3.md), which folded all three in whole. Live successors: **W-107**, **W-112**, and **W-108 … W-111**. ⚠ `search-v3.md` said they were *"deleted in the same change"* — **they never were**, and they sat here unindexed for two days |
| [`tune-file-and-source-priority.md`](../../archive/proposals/tune-file-and-source-priority.md) | 2026-08-27 | Graduated 2026-08-22 → [SR-TUNE](../../records/0135_tuning.md); kept for the survey and its ten forks as they were put |
| [`playground-goldens-draft.md`](../../archive/proposals/playground-goldens-draft.md) | 2026-08-27 | Graduated 2026-08-24 when Arpit waived the human-author rule and the 50 candidates were installed; the run is [`../regression/2026-08-24-rerank-and-goldens/`](../regression/2026-08-24-rerank-and-goldens/report.md) |
| [`answer-provenance.md`](../../archive/proposals/answer-provenance.md) | 2026-08-27 | Graduated same-day → [SR-PROVENANCE](../../records/0142_provenance.md), built and green. Kept for the prior-art table and **five open forks**, of which fork 1 — always-on journalling as an SR-TUNE key — is the one a session will be tempted to default |
| [`consumer-intent-policy.md`](../../archive/proposals/consumer-intent-policy.md) | 2026-08-22 | Became [SR-AGENT-POLICY](../../records/0132_agent-policy.md), accepted **and built**: `fux setup` installs the four renderings, which live at [`src/fux/templates/agents/`](../../src/fux/templates/agents/) |
| [`process-diet.md`](../../archive/proposals/process-diet.md) | 2026-08-21 | Graduated same-session (PRIORITY P7); the `Cost:` line is gone from the WORKLOG format |

**v0.26-era proposals** (tied to the archived substrate engine) are at
[`archive/v0.26/proposals/`](../../archive/v0.26/proposals/):
knowledge-substrate (superseded by the index-and-refer architecture),
chunk-level-dense-codes, and hybrid-degrades-at-scale (✅ resolved 2026-07-22 as
a corpus artifact).
