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
`structure-aware-extraction.md` (W-144) and `search-improvements-v3.md` (W-168) are the two today.

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

## Filed 2026-09-18

* [Exact identifier match — the two analyzer defects, and the four ways it is
  solved elsewhere](identifier-exact-match.md) — research for **W-168 step 2**,
  written after the [survival run](../regression/2026-09-16-identifier-survival/report.md)
  measured 0 of 33 identifiers surviving. Names the cause at line level: **D1**
  `_WORD_RE`'s class holds `_` but not `-`, `.` or `/`, so the docstring's
  *"whole AND parts"* promise is kept for `snake_case` and quietly broken for
  every other separator; **D2** `should_stem` protects digits and underscores
  but not all-letter acronyms, so Porter turns `KFS` into `kf`. ⚠ **Corrects the
  run's claim that a mangled id is unreachable** — ingest and query import the
  same `analyze()`, so it matches; what is lost is **precision**, one rare term
  becoming two common ones. Sets out four shipped solutions cheapest-first
  (`WordDelimiterGraphFilter`'s preserve-original · `KeywordRepeatFilter`'s
  stemmed-and-unstemmed-in-one-field · Elasticsearch multi-fields, which is step
  2 as written · trigram/sparse-gram planes, out of scope) and argues **(a) is a
  precondition of (c), not an alternative**. Proposes **gate A**, an
  analyzer-survival before/after that needs no Codex output.
  **Graduates when W-168 step 2's pre-registration is written.**

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

## Filed 2026-09-11

* [Positioning — written knowledge, not code](positioning-documents-not-code.md)
  — ✅ **`graduated`: RULED AND APPLIED by Arpit 2026-09-12.** Why fux was filed
  next to AST/code-graph tools: **it parses no code and, by default, indexes
  none** (`.py` → *not an indexed file type*); the misfiling traced to
  v0.1–v0.26, which did, plus *"AI-assisted codebases"*, the `codebase`
  keyword, the *Quality Assurance* classifier and the paper's non-existent
  *symbol edges*. **All six surfaces fixed**, plus the agent templates.
  🔴 **Arpit overruled the proposal's own framing** — it said *"the documents
  around your code"*, which keeps code as the reference point; the shipped
  tagline is *"A search index for your written knowledge"*, with no "code",
  "codebase" or "organization" in it. §5's `code`→`path` rename was **declined**
  in favour of a glossary definition. §6 went to **option (b)**: the ALL-CAPS
  exemption is retired, 18 trackers typed, evidence and sealed golden data
  declared outside the bundle, frozen pre-2026-08-25 runs exempt by the repo's
  own baseline — and `tests/test_okf_bundle.py` now gates it (237 docs, 0
  failures) so the claim and the tree cannot drift again.
  **Kept here, not archived:** GitHub About/topics still need Arpit's `gh`, the
  PyPI page changes only on the next upload, and §5's rename is a live fork.

## Filed 2026-08-28 — two reviews

⚠ **Both are findings to verify, not landed facts, and each says so.** Neither
has been audited against what has since shipped; a session acting on one
re-derives its claims first.

* [SR review — 2026-08-28](adr-review-2026-08-28.md) — all 47 live records
  read against the register's own rules. *"The rule set is excellent; the
  records don't follow it, and nothing mechanical notices."* Five rules each
  broken in 20–45 of 47. **Record-vs-record only** — no claim in it was checked
  against `src/` or `tests/`. **Graduates into lint tests plus one bulk pass**;
  some of that has since landed (`test_sr_ownership`, `test_sr_freshness`,
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
  condition is alive**: the decision waiting on it is **W-97**, and what it
  needs is 50 judgments on a corpus that is still an instrument —
  [SR-WORK-ENVIRONMENTS](../../records/0052_WORK-environments.md) voided the playground, so
  that is W-136's golden data. Pre-registration:
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

## Filed 2026-08-10

* [Agent search-API landscape](agent-search-landscape.md) — research note, not
  a build item: Parallel / Perplexity / Exa / Brave independently arrived at
  three index-and-refer decisions, and the corpus they *cannot* reach names
  Fux's wedge. **The evidence base the refer-plane proposals cited.**
  *(Both of those graduated and were archived 2026-08-20 when M4's core landed;
  their live successor is [SR-REFER](../../records/0127_refer-plane.md). One
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
[SR-PROVENANCE](../../records/0142_provenance.md) and was **archived
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
