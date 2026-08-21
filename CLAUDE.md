# CLAUDE.md — coding-agent guide for the Fux engine (v0.30 rebuild)

Fux ranks organizational knowledge — documentation, decisions, runbooks — from
a **small index committed to git**, fetches content from the systems that own
it, and verifies freshness at answer time. Agents get ranked, cited answers;
nothing about the corpus is copied, and no model sits anywhere in the
maintenance path.

**This is the second from-scratch rebuild.** The v0.19–0.26 substrate engine
is archived at [`archive/v0.26/`](archive/v0.26/) — runnable, reference-only,
never imported by new code. The architecture being built is **index-and-refer**,
specified in [`work/paper/the-fux-index-paper.md`](work/paper/the-fux-index-paper.md).

This file is binding. Read it, then
[`work/INTERVIEW.md`](work/INTERVIEW.md) (start at the reset block), before
your first substantive change.

## Law zero — the ADRs are always up to date

**Arpit, 2026-08-18, emphatic and standing: *always* make sure the ADRs are up
to date.** Not at the end of the milestone, not when someone asks — in the
change that makes them wrong.

Three things follow, and none of them is optional:

1. **No behaviour change lands without its ADR updated in the same change.**
   Same commit, not the next one.
2. **If a change genuinely touches no recorded decision, say so out loud** —
   `no ADR affected`, in the commit message. That is a claim under your name in
   git history, which is the point. Silence is not an answer.
3. **Before you finish a session, re-read the records you touched code under.**
   A record that describes behaviour the code no longer has is worse than no
   record: it reads as authority.

**This is enforced, not trusted.** `tests/test_adr_freshness.py` runs in CI on
every push (with `fetch-depth: 0`, so the runner can see the history it
audits) and fails a commit that changed an ADR-owned component without
touching that component's **owning** record specifically — touching some
other record does not satisfy it. `scripts/adr-guard.sh` is the same check as
a `commit-msg` hook (not `pre-commit`: it has to read the commit message to
honor the `no ADR affected` escape hatch, and `pre-commit` runs before that
message exists) — install it once:

```bash
ln -sf ../../scripts/adr-guard.sh .git/hooks/commit-msg
```

**Why it is enforced.** Replayed over the 25 commits before the check existed,
**13 of them** changed an owned component and updated no record. The prose rule
was already in this file the whole time. That is the measured case for a check.

## Triage first — a human-blocked queue stops the session

**Standing directive (Arpit, 2026-08-12).** Before any work, read
[`work/OPEN-WORK.md`](work/OPEN-WORK.md) and ask: *is any item agent-closable
right now?*

- **If not** — every remaining item is `OPEN·human`, gated on a verdict Arpit
  hasn't read, or waiting on his hands — the session's **first** output is the
  blocked-on-Arpit list in ≤3 lines, then it **stops**.
- No invented scope, no doc polishing to fill the hours. "Next: Arpit reads…"
  buried at the end of a long session is the failure this rule exists to
  prevent; said upfront, it is the rule followed.
- His time and tokens are money. Applies to Cowork and Claude Code alike.
- **The inbox:** OPEN-WORK's header carries a *Blocked on Arpit* block and the
  open-items table carries a `filed` date per row. Every session keeps both
  current, and any `OPEN·human` row older than **5 days** is named, with its
  age, in the session's first output.
- **Two strikes → a gate (2026-08-12).** A failure class the WORKLOG records
  twice becomes a test or mechanical check in the same change that records
  the second occurrence — recurring lessons are gated, not re-learned.

## Where the state of play lives

| you want | read |
|---|---|
| what to work on next | [`work/OPEN-WORK.md`](work/OPEN-WORK.md) — **the single live queue**, two lanes |
| the spec for a milestone id | [the ADR register](docs/adr/README.md) |
| why the architecture is this shape | [`work/paper/the-fux-index-paper.md`](work/paper/the-fux-index-paper.md) |
| a closed decision + its reopen-trigger | [`work/compare/`](work/compare/README.md) |
| the judgment behind the reset | [`work/INTERVIEW.md`](work/INTERVIEW.md) |
| a word you don't recognise | [`docs/GLOSSARY.md`](docs/GLOSSARY.md) |
| what has actually shipped | [`work/IMPLEMENTATION.md`](work/IMPLEMENTATION.md) |
| the measured evidence behind a claim | [`work/regression/`](work/regression/README.md) |
| why a command fails on *this* surface | [`work/MACHINE.md`](work/MACHINE.md) |
| which record owns a module | [`docs/adr/README.md`](docs/adr/README.md) §Ownership |

Any work item or prediction that starts, finishes, blocks, or is descoped
updates `OPEN-WORK.md` **in the same change as the work**. PLAN is the spec;
OPEN-WORK is the state; `IMPLEMENTATION.md` is the record of what landed, and
is what OPEN-WORK reconciles against before an item may be deleted.

## What we are building (scope)

**One sentence:** rank from a small committed index; fetch content from the
systems that own it; verify at answer time.

- **The index is committed; content never is.** One content-addressed MST
  keyspace in git, six planes: `L/` ledger · `P/` postings · `D/` dictionary+df
  · `V/` dense codes · `E/` edges · `M/` doc meta.
- **Wire vs runtime.** The committed **wire format** (BIC postings, 4-bit
  impacts, front-coded ledger) is optimized for size and diffability and
  decoded **once**; git hooks inflate it into gitignored, mmap'd **runtime
  segments** optimized for query speed. Neither pays the other's tax.
- **The refer plane.** Answers rank in the index, fetch the cited documents
  from their source (git dir / HTTP / Confluence — **that cap is a decision**),
  re-score passages on the fetched bytes, and cite a fresh sha.
- **Two ingest modes.** `extracted` (default: `$0`, offline, deterministic,
  [ADR-EXTRACTED](docs/adr/0016_extracted-mode.md) — **accepted**) and
  `enriched` (opt-in, model-assisted,
  [ADR-ENRICHED](docs/adr/0017_enriched-mode.md) — **accepted**: the name, the
  boundary and the record shape are ratified; **the build is not** — it stays
  behind W-38's M8 gate). Both ratified by Arpit 2026-08-19.
  **`inferred` is retired**, because `INFERRED` is the edge grade for
  *model-derived* and the collision is the whole point of those records.
  **Enrichment never runs inside `fux ingest`** — it is its own command, its
  output pinned and then ingested deterministically. That boundary is what
  keeps L3 true.

**The build is gated on falsifiable predictions** (paper §8): a milestone does
not start while its gating prediction is unmeasured or failed. That is a hard
sequencing rule, not a preference. **P1 closed FAIL on 2026-08-09** — full
postings, permanently; the pruned-index design is dead, not deferred
([verdict](work/regression/2026-08-09-pruning-rerun/VERDICT.md)). P2–P7 were
retired with plan revision 1; their successors **R1–R7**, and which milestone
measures each, are in [`work/OPEN-WORK.md`](work/OPEN-WORK.md) §"Predictions
still unmeasured".

**Out of scope until it has an ADR and Arpit's sign-off:** anything from the
archived build (the SQLite substrate, per-file cache, lean profile, state
plane, `fux.lock`), further adapters beyond the capped three, MCP (it is
[a proposal](work/proposals/mcp-adapters.md), not a backlog item), and every
M8 item.

**Do not port the archived engine.** [the ADR register](docs/adr/README.md) §"What survives"
is the complete port list; each entry comes forward **with its tests**, when
its milestone needs it. Nothing else comes back.

## Non-negotiable constraints

**This section is the only normative statement of the laws.** They are named
**L1–L7** by [ADR-LAWS](docs/adr/0001_laws.md) so a record can cite one without
restating it — and no record may restate one. Changing a law changes this
section *and* ADR-LAWS' table, in the same commit.


- **L1** · **`$0`, stdlib-only runtime.** No third-party *runtime* dependencies. The
  frontmatter parser and every codec are hand-rolled on purpose — that is the
  zero-dependency guarantee and the product's central promise. Dev/test tooling
  may use extras; the runtime path may not. No numpy, pandas, or scipy
  anywhere, including in measurement harnesses.
- **L2** · **Content is never durable outside its source system.** The index holds
  statistics, never content. The single exception is explicit per-source
  `snapshot` policy. This is the law the whole architecture rests on.
- **L3** · **Deterministic — no model in the maintenance path.** Same sources →
  byte-identical index and root hash. No wall-clock output, no unseeded
  randomness, no set-iteration-order dependence. No maintenance path may ever
  call a model — not to be "smarter" at ingest, not to summarize, not once.
- **L4** · **Offline by default.** Network access only inside explicit, fenced,
  opt-in paths. An import fence test enforces it.
- **L5** · **Hashed meta is the default** for non-git sources, enforced at write time.
  It closes an ACL-mismatch leak, so it is not a configuration preference.
- **L6** · **Say "index", not "db".** What Fux commits is an index — statistics that
  make documents findable. A council ruling, and it is load-bearing vocabulary.
- **L7** · **Python ≥ 3.11** (`tomllib`, modern typing). Match the surrounding style.

## Litmus for any new work

**The design point is 10 000 documents** (Arpit, 2026-08-21). Fux is built,
measured and judged at that size. **50 000 and then 100 000 are staged later
targets, not the filter.**

This replaced a 10⁵–10⁶ design point on 2026-08-21. **What changed is the
scale filter. What did not change is the deployment filter** — a
10 000-document corpus inside a corporation is still inside that corporation.

- **Scale is a staged target, not the default.** 10k now; 50k next; 100k
  after that. An argument that turns on 10⁵–10⁶ documents describes where the
  design is heading and **may not gate work today**. A feature is not blocked,
  and a measurement is not owed, because of a size Fux is not yet built for.

- **Enterprise realities are still design inputs** — Windows-first fleets,
  proxies and SSO in front of every internal site, air-gapped/regulated
  environments, multi-team corpora with access boundaries, audit and
  compliance demands. None of these got cheaper when the corpus got smaller.

- **Fux's laws are enterprise features, not constraints** — `$0`/stdlib = a
  trivially auditable supply chain and no procurement; offline/no-API = no data
  ever leaves the tenant; deterministic = compliance-grade reproducibility.

The question per feature: *"does this hold up on a 10 000-document corpus
inside that corporation, and does it foreclose 50k later?"* **The second
clause is a check against painting into a corner — not a licence to build for
a size nobody is measuring.**

Anton remains a convenient testbed. **Do not design in reference to it.**

> **A gate judged at a deferred size is not a blocker.** A pre-registered
> threshold may never move (§the lifecycle), so a verdict measured at 100 000
> documents stands as measured — it is **re-judged at 10 000 by a new
> pre-registration**, never by editing the old one. Records and compare docs
> that argue from the old design point are stale until reconciled, and that
> reconciliation is an item, not a silent edit.

## How work happens here (the lifecycle)

Every non-trivial feature moves through this pipeline, and the artifacts are
committed:

0. **Compare (when there's a fork).** Whenever a decision has multiple viable
   options, write a *compare doc* in [`work/compare/`](work/compare) first —
   debate, matrix, grounded references, a proposed verdict Arpit accepts or
   overrides, and a **reopen-trigger**. Standing rule.
   **Proposals (when it's an idea, not a fork).** An idea worth keeping but not
   being built now gets a *proposal doc* in
   [`work/proposals/`](work/proposals) — same rigor, `status: proposed`.
   Parked, not lost: when picked up they graduate to a compare doc or plan entry.
1. **Plan** — the design of record. Update [the ADR register](docs/adr/README.md)
   before building: what, why, scope in/out, the decision.
2. **Handoff** — a self-contained spec: context, definition-of-done,
   constraints, key files, edge cases, tests, open questions. **It lives in the
   item's own detail file under [`work/open/`](work/open/README.md)**, not in a
   separate directory: the handoff directory was retired on 2026-08-18 and its
   contents moved to [`archive/handoff/`](archive/README.md). One item, one
   file, spec and state together.
3. **Prompt** — the paste-ready Claude Code prompt that executes the handoff
   (explore → plan → implement → verify), alongside its handoff.

**Every handoff and prompt names the model that should execute it** — a
`**Model: <name>**` line at the top, plus one sentence of *why*. State it when
handing the prompt over, too. Model choice is a silent failure mode: an
under-powered model on a judgment-heavy task does not error, it returns
confident, plausible, wrong work, and the cost lands later.

- **Opus** — the output quality *is* the deliverable and no test can catch a
  bad one: design, architecture, debate, ambiguous diagnosis, interpreting a
  confusing measurement, **calling a gate**, anything touching the
  non-negotiable constraints.
- **Sonnet** — well-specified implementation against a written
  definition-of-done with tests to verify it; mechanical suite runs.
- **Haiku** — mechanical bulk edits with an exact, unambiguous rule.

When borderline, say Opus and say why it was close. A handoff detailed enough
to be Sonnet-executable is itself the signal that the design phase was done.

Then, on completion:

4. **One feature → one ADR** in [`docs/adr/`](docs/adr/), from
   [`docs/adr/TEMPLATE.md`](docs/adr/TEMPLATE.md): §1 for humans (one screen,
   Mermaid + its ASCII twin), §2 for agents (context · decision · consequences ·
   alternatives · reference · veto condition). Give it a **NAME** and cite that
   name everywhere; the file number is an ordinal, not an identity. Add its
   components to the ownership table and update
   [`tests/test_adr_ownership.py`](tests/test_adr_ownership.py) in the same
   change. Full convention: [`docs/adr/README.md`](docs/adr/README.md).
   `archive/v0.26-docs/adr/0001`–`0015` are the **archived** engine's records —
   a distinct numbering from today's live `docs/adr/0001`–`0015`
   (ADR-LAWS…ADR-PORT-LIST) — and are cited as "archived ADR-NNNN" with that
   archive path, never bare "ADR-NNNN".

**Every rule, ADR, and material decision must carry a reference** — a paper, a
blog post, or a concrete example link. A rule or ADR with no reference is
incomplete. Ground the claim; don't assert it.

**Archive implemented docs — into the ONE archive.** When a proposal is fully
implemented and its ADR is written, move it to [`archive/`](archive/README.md)
in the same change, stamping `status: implemented` + the ADR link, and add its
row to `archive/README.md` naming its live successor. Active directories hold
*live* work only.

**There is no handoff directory.** It was retired on 2026-08-18; a spec for
open work lives in that item's detail file under
[`work/open/`](work/open/README.md), spec and state in one place.

## A pre-registered threshold may never move

When a decision is gated on a measurement, **write the threshold, the metric
definitions, and the slice definitions down before producing a number**, and
commit that file first. Then measure against it.

- A recorded **negative** that stops months of building is a *successful*
  outcome, not a failed task. Report it plainly.
- If a result lands between "clearly passes" and "clearly fails", write it up
  as **ambiguous and hand it to Arpit**. Do not adjudicate it, and do not
  restate the threshold in looser words.
- Post-hoc analysis is allowed and often valuable — but label it **post-hoc**
  and keep it out of the verdict.
- If the measurement turns out not to test what the threshold assumed, say
  *that*, rather than reporting the number as if it did.

See [`tools/pruning-eval/PRE-REGISTRATION.md`](tools/pruning-eval/PRE-REGISTRATION.md)
for the worked example.

## Follow the OKF pattern (docs)

Fux follows Google's **Open Knowledge Format** (OKF v0.1) — an open spec for
knowledge as a directory of Markdown files with YAML frontmatter:

- **The bundle is `docs/` + `work/`** — root index at
  [`docs/index.md`](docs/index.md), which declares `okf_version: "0.1"` and
  indexes both trees. (It spanned one tree until 2026-08-18; the split into
  *what the project is* / *what is happening to it* did not change the bundle,
  only its shape.) Repo-root CLAUDE.md/README.md are tool entry points outside
  the bundle.
  **Convention: ALL-CAPS markdown files carry no YAML frontmatter** —
  GLOSSARY.md, DOC-REGISTRY.md, OPEN-WORK.md, WORKLOG.md are entry-point/tracker
  files, exempt from the `type` requirement. Lowercase docs conform.
- **Frontmatter `type` on every knowledge doc** (the only OKF-required field) —
  `type: Compare Doc`, `type: Proposal`, `type: ADR`, `type: Handoff`,
  `type: Paper`. Provenance keys are legal OKF extensions; consumers must
  preserve unknown keys.
- **`log.md` semantics**: `work/WORKLOG.md` follows OKF's log convention
  (date-grouped, newest first).
- Conformance bar (OKF §9): parseable frontmatter + non-empty `type`
  everywhere; be permissive when consuming.

Reference: [OKF spec](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md) ·
[annotated guide](https://okf.md/spec/).

## Documentation style (required)

**No large paragraphs — they are hard to read.**

- Split dense prose into **short points** (bullets or numbered lists), one idea
  per point.
- Keep paragraphs to **3–4 lines max**; if it runs longer, it's two points.
- Make it **roomy**: blank lines between points and sections; tables for
  option/field comparisons; headings to break up long sections.
- Lead each point with the takeaway (bold it when it helps scanning).
- When you touch a doc that has a wall of text, split it in the same change —
  "fix stale docs on contact" applies to *form*, not just facts.
- **Chat responses too.** Answers in Cowork / Claude Code follow the same rule:
  precise, short paragraphs, lead with the takeaway.

## Documentation discipline (required)

**Agent-steering files are proposed, never auto-applied.** `CLAUDE.md` and any
other file that steers a session are Arpit's to ratify: an agent proposes a
change as a named diff and does not apply it to itself. This rule is why this
file carried a PROPOSED header from 2026-08-09 until Arpit adopted the rewrite
on 2026-08-19.

**Statements of fact about the repo are exempt.** A version number, a path, a
"does not exist yet" that now exists — fixed on contact, in the change that
notices it, with a DOC-REGISTRY bump. The rule protects what this file
*instructs*, never what it *claims*: three sessions read "there is no package on
`main` yet" while `fux-engine` was on PyPI, because a rule meant for normative
content was applied to a fact.

**The shared memory between sessions is [`work/`](work/README.md).** `docs/`
holds what the project *is* — plan, paper, glossary, decision records. `work/`
holds what is *happening to it*. Read
[`work/README.md`](work/README.md) once; it is the map.

### The three-file session discipline

Every session, without exception — **including a chat-only session where no
code moved**:

1. **[`work/WORKLOG.md`](work/WORKLOG.md)** — append **one entry before the
   session ends**: what was asked, what got done, what was decided or left
   open, and what's next. **Never edit a past entry.** Append only, newest on
   top. A wrong old entry is corrected by a new entry, not by a rewrite.
   (The mandatory `Cost:` line was dropped 2026-08-21, PRIORITY.md P7 —
   58 of 58 entries had said `unmeasured`; see
   [`work/proposals/process-diet.md`](work/proposals/process-diet.md).)
2. **[`work/INTERVIEW.md`](work/INTERVIEW.md)** — the state-of-play doc, kept
   current **during** the session, not in a wrap-up pass. Four maintained
   sections: state of play · in-flight work + the immediate next step ·
   standing constraints · lessons learned. Write it for a **different model
   arriving mid-task with zero other context**. **A stale INTERVIEW at handoff
   is as serious as a missing changelog entry.**
3. **[`work/IMPLEMENTATION.md`](work/IMPLEMENTATION.md)** — the milestone log:
   what shipped, when, and the outcome. This is the evidence store
   `OPEN-WORK` reconciles against before anything is called done. A row is
   earned by landing, never by being planned.

### OPEN-WORK — the single live queue

[`work/OPEN-WORK.md`](work/OPEN-WORK.md) is the *only* queue. Its length is the
signal of how much is actually pending.

1. **Updated in the same change as the work**, never afterwards — an item
   finishes, a defect appears, scope moves, something blocks or unblocks: the
   index row **and** the item's detail file change in that edit.
2. **Completed items are removed, never ticked.** Deletion is legal only once
   the outcome is in `IMPLEMENTATION.md` and any evidence is in
   `work/regression/`. No tombstones, no DONE rows, no `closed/`.
3. **Its markers are assertions, not evidence — re-derive, do not read.**
   Reconcile against `work/regression/`, `IMPLEMENTATION.md` and the repo
   itself (`git log`, `git tag`, the code) before believing any status. A stale
   ✅ overstates progress; a stale pending row that an unrelated commit already
   closed understates it — **same class of defect**.
4. **Two lanes, ordered independently.** `arpit` needs a human's hands;
   `agent` an agent can execute alone. They run concurrently — never force one
   priority order across both, and never idle behind a decision you were never
   going to make.
   **Items are grouped by the record each one will have to update** — Law zero
   made visible. If you cannot name the record an item belongs to, that is the
   "no ADR affected" claim, said out loud.
5. **Priority is damage that accrues with elapsed time**, above damage that is
   merely present-but-static. Only the former gets worse by waiting.
6. **No separate prioritization or sequencing doc.** Ordering lives inside
   OPEN-WORK. A second document naming what to do next is always the stale one.

### Archive is not evidence

A doc under **any** `archive/` may be *named* ("superseded by X"). It may
**never be cited as backing a live claim** — nothing guarantees an archived
file was not overwritten after retirement.

When repointing a citation away from an archived doc, **point it at the live
successor**, don't just delete the link: a deleted link leaves the claim
ungrounded, and nobody can see that anything is missing. If an archived doc was
a claim's only support, the claim needs new grounding — code, a live doc, or a
measured run under [`work/regression/`](work/regression/README.md).

**There is exactly ONE archive, and it is [`archive/`](archive/README.md) at
the repo root** (Arpit, 2026-08-10, restated 2026-08-18). Nothing under `docs/`
or `work/` is an archive. **Anything that gets archived is moved there**, into a
directory mirroring where it came from — `work/adr/` retires into
`archive/adr/`, and the handoff directory retired wholesale into
`archive/handoff/` — and gets a row in `archive/README.md` naming its live
successor, or saying plainly that it has none. Enforced by
`tests/test_archive_law.py`, which fails on a second `archive` directory
anywhere and on a live doc still pointing at one.

### Two hazards that bite silently

- **Concurrent sessions are real.** Cowork, Claude Code and scheduled tasks all
  touch these files. **Re-stage and re-apply your changes to `work/*.md` right
  before committing** — another session may have landed an entry in between.
- **Ground truth over prose.** Before writing any status claim — release state,
  test counts, "nothing pending", "X is done" — check it against the actual
  source of truth: `git log`/`status`/`tag`, the code, a command that
  reproduces. A doc repeating another doc is not a second source.

### The ADR standing rules

The register, the convention and the ownership table are in
[`docs/adr/README.md`](docs/adr/README.md). What binds every session:

- **No behaviour change lands without its ADR updated in the same change.**
  See §Law zero. If a change genuinely touches no recorded decision, **say so
  explicitly — `no ADR affected` in the commit message** — rather than silently
  skipping the check. Enforced by `tests/test_adr_freshness.py` (CI) and
  `scripts/adr-guard.sh` (`commit-msg` hook); neither can be satisfied by
  intending to update the record later.
- **Cite records by name, never by number.** `ADR-RECORD`, not
  "ADR-0004". Numbers exist only so the archive can map a retired record to its
  successor. A live doc citing a number is a defect; fix it on contact.
  ("archived ADR-NNNN" *with its path* still means the frozen v0.26 line.)
- **Ownership is a table, not a judgement call.** Every `src/`/`tools/`
  component is claimed by exactly one record in `docs/adr/README.md`. **When
  the table changes, edit [`tests/test_adr_ownership.py`](tests/test_adr_ownership.py)
  in the same change** — they drift silently otherwise, which is why the
  executable twin exists.
- **A record that restates a cross-cutting principle is a bug, not
  redundancy.** The non-negotiable constraints have exactly one home — this
  file — and are named L1–L7 by
  [ADR-LAWS](docs/adr/0001_laws.md). Every other record cites `ADR-LAWS` and
  the number; none paraphrases. Paraphrases drift, and a drifted paraphrase in
  an accepted record reads as authority.
- **Veto conditions are conditions to check, never events to await.** State
  what would have to become *true* to reopen the decision, so it can be checked
  mechanically today. An event never fires, because nobody is waiting.
- **§1 is for humans (one screen, with a Mermaid diagram and its hand-paired
  ASCII twin — both updated together, the twin collapsed in a `<details>`
  block); §2 is for agents** (context · decision ·
  consequences · alternatives · reference · veto). The reference is grounded in
  code, a live doc, or measured evidence — **never an archived doc**.
- **Records live in `docs/adr/`, and nowhere else.** A superseded record moves
  to [`archive/adr/`](archive/adr/README.md) — where archive-is-not-evidence
  applies from that moment — in the same change that accepts its successor, and
  `archive/adr/README.md` maps its old number to that successor's name.

## Keep the docs in sync (required)

**Every task updates the documentation — no exceptions.** This holds whether or
not the task touched code: a decision, a scope change, or a plan is also
documentation. A task is not "done" until the docs are true. At minimum:

1. **[`work/OPEN-WORK.md`](work/OPEN-WORK.md)** — the live tracker. **On every
   execution, whatever the outcome** — success, failure, blocked, interrupted,
   abandoned — the affected `W-nn` rows and prediction rows are updated before
   the session ends. A failed run records the failure with a one-line why.
   Never mark an item DONE with failing tests.
2. **[the ADR register](docs/adr/README.md)** — design of record; keep milestone status
   truthful when behaviour or scope changes.
3. **[`work/WORKLOG.md`](work/WORKLOG.md)** — an entry per substantive exchange
   (see below).
4. **[`work/INTERVIEW.md`](work/INTERVIEW.md)** — the agent-succession handoff.
   Read it before your first substantive change; update it when direction,
   strategy, or a major decision changes, and add yourself to its maintainer
   line when you do. You will retire too; leave it better.
5. **[`work/DOC-REGISTRY.md`](work/DOC-REGISTRY.md)** — bump the row for any doc
   you touched; new maintained doc → new row, same change. **It lists live
   documents only:** an archived doc's row is **deleted** in the change that
   archives it — not struck through, not annotated "retired" — the same
   discipline OPEN-WORK applies to closed items. No row may point into
   `archive/`, every row's target must exist, and one document gets one row.
   Enforced by `tests/test_doc_registry.py`.
6. **[`README.md`](README.md)** — the public front door: status, guarantees,
   reading order. **`CHANGELOG.md`** once a package exists.
7. **The relevant ADR**, [`docs/GLOSSARY.md`](docs/GLOSSARY.md) for any new
   recurring term, and every test the behaviour change needs.

**Auto-fold useful information into this file.** When a session produces
durable, repo-wide knowledge — a decision, a constraint, a disproven idea, a
pattern worth keeping — fold it in here concisely (details live in the linked
docs), in the same change. If a future agent would act differently knowing
something, it belongs here or is linked from here.

## Session continuity — the running worklog (required)

At the end of **every substantive exchange**, append an entry to
[`work/WORKLOG.md`](work/WORKLOG.md): what was asked, what was done, what was
decided or left open, and the single next step. A rolling exit-interview so a
*new chat can pick up cold*. **Applies in Cowork and Claude Code alike.** Newest
entry on top; short and true. Distinct from `INTERVIEW.md` (strategic,
cross-session succession) — the worklog is the granular, per-exchange trail.

## Conformance runs — file every one (required)

The fux-lab environment (`~/my_programs/fux-lab/`) is scratch and commits
nothing. Its **evidence is not** — every run's report + diagnosis + raw
evidence is filed into [`work/regression/`](work/regression), so engine
changes are made from measured data, not memory. Binding, like the docs law.

Per run, in the same change:

1. Create `work/regression/<date>-<run>/`.
2. Drop the run's own report(s) there.
3. Write `ANALYSIS.md` — the diagnosis turned into **specific improvements**,
   each with a repro command; state unresolved causes as unresolved.
4. Save the primary data under `evidence/`.
5. Add the run to [`work/regression/README.md`](work/regression/README.md)
   and bump the DOC-REGISTRY row.

**A verdict is not an ADR.** When a run adjudicates a pre-registered
prediction, the ruling is a `VERDICT.md` beside its evidence — `type: Verdict`,
with the prediction id and the frozen pre-registration path. An ADR records a
decision someone can supersede; **nothing supersedes a measurement except a
better measurement**, which is a new run with its own verdict. The *decisions*
that rest on a verdict live in `docs/adr/` and cite it. Enforced by
`tests/test_regression_runs.py`.

**The reproduce command must actually reproduce.** Findings that warrant a
change graduate to `work/proposals/` and, when accepted, an ADR. Never ship a
ranking/behaviour change off a single synthetic corpus.

## Layout

```
work/               THE SHARED MEMORY between sessions — start at work/README.md
  WORKLOG.md        append-only session log (an entry every session)
  INTERVIEW.md      state of play, kept current DURING the session
  IMPLEMENTATION.md milestone log — what shipped, when, outcome (the evidence store)
  OPEN-WORK.md      THE single live queue — two lanes; finished items are DELETED
  MACHINE.md        environment/tooling quirks per surface (local · bridge · cloud · CI)
  DOC-REGISTRY.md   doc freshness tracker (triggers + last-verified)
  paper/            the architecture of record + figures + predictions
  architecture.svg  the detailed diagram · architecture-overview.svg (5 components)
  open/             one detail file per open W-nn; deleted with its row
  setup/            fux-playground (grades) and fux-lab (measures) — outside this repo
  regression/       dated, measured evidence other docs cite as grounding; VERDICT.md rules
  compare/          live forks — verdict + explicit reopen-trigger
  proposals/        parked ideas, not yet decided
docs/               WHAT THE PROJECT IS
  GLOSSARY.md       every recurring term, defined once
  adr/              THE REGISTER + TEMPLATE.md + ADR-LAWS; new records land here
  index.md          the OKF bundle root
src/fux/            the engine — every component claimed in docs/adr/README.md
tests/              the suite, incl. test_adr_ownership.py (the ownership twin)
tools/
  pruning-eval/     the gate — frozen pre-registrations, KL selector, eval harness
  differential/     the differential-law harness and the R3 bench
archive/            THE ONE ARCHIVE — everything retired, mirroring the live tree
  README.md         the map: every archived doc and its live successor
  adr/              superseded records; maps old number -> successor NAME
  handoff/          the retired handoff directory (executed pairs + unresolved specs)
  v0.26/            build: the previous engine — runnable, REFERENCE ONLY
  v0.26-docs/       build: the frozen v0.19–0.26 doc set ("archived ADR-NNNN")
  v0.26-implemented/ · v0.30-rev1-planning/   frozen build artifacts
  v0.1/             build: the first one
```

**Records live in `docs/adr/`.** A superseded one moves to `archive/adr/` in
the same change that accepts its successor, and the archive maps its number to
that successor's name. The v0.30 set was archived wholesale on 2026-08-18;
`work/adr/` no longer exists.

**`src/fux/` was gated behind P1, and now exists.** The package scaffold was
M0b and landed only once the pruning gate had been decided — scaffolding a
package for an architecture a measurement might falsify is the "build the fun
part first" failure the plan exists to avoid. It shipped in `v0.30.0`; the
gating rule stands for every milestone after it.

## Error contract

Catch and render errors only at the boundaries (CLI `main`, hook entrypoints).
Internals keep raising. Raise the single `FuxError` for expected user-facing
failures — **no subclass hierarchy**. CLI exit codes: `0` ok · `1` error ·
`2` blocking (strict) · `130` interrupted.

## Build & test

**`fux-engine` 0.35.0 is released and on PyPI**; `src/fux/` is the live tree.

```bash
uv sync --extra dev
uv run pytest -q tests        # fast unit
uv run pytest -q tests_e2e    # the package as a user
```

**Two suites, both maintained** — `tests/` (fast unit) and `tests_e2e/` (the
package as a user: real CLI via `subprocess`, fixture corpus, golden files
updated deliberately and never regenerated blindly). A feature is not done
until both cover it and pass.

The archived engine still runs — reference, and M1's baseline. **Do not modify
it:**

```bash
cd archive/v0.26 && uv sync --extra dev && uv run pytest -q tests

# M1's gate: the KL selector's contract + the harness self-checks
archive/v0.26/.venv/bin/python -m pytest tools/pruning-eval/tests -q

# M1's gate: the experiment itself
archive/v0.26/.venv/bin/python tools/pruning-eval/run.py --corpus acme orbit synth
```

## Package identity (do not change casually)

- Distribution name: **`fux-engine`**. Import package: **`fux`**.
- Version: **`0.35.0`**, released (0.26.0 archived → reset → 0.30.0 → M2 at
  0.32.0 → the sources rewrite at 0.33.0 → the graph/refer/maintenance planes
  at 0.34.0 → the source verbs and the progress plane at 0.35.0). Bumped in
  `src/fux/__init__.py` only — it is the single source, read dynamically by
  `pyproject.toml`.

## Merge wall — what actually blocks a merge

**There are no required status checks on `main`.** What remains:
`enforce_admins: true`, no force-push, no deletion — history is protected, the
quality gate is not.

Practical consequence: **CI green is your responsibility to check, not
something the wall guarantees.** Read `gh pr checks <n>` yourself and do not
merge on red. Source of truth:
[`.github/branch-protection.json`](.github/branch-protection.json).

## Hard-won build knowledge (auto-folded)

**2026-08-09 — M1, the pruning gate**

- **A pre-registered threshold is only as good as the corpus that tests it.**
  M1's k=128 arm returned a zero delta on all three eval corpora — and prune
  coverage showed why: their documents' median vocabulary is 32–46 distinct
  terms, so top-128 was a **no-op for 97 %+ of documents**. Always report the
  fraction of the population a treatment actually touched; an aggregate delta
  of zero over an untreated population is not evidence.
- **Recompute statistics over the pruned index, never borrow them.** `df`, `n`
  and field lengths must come from the surviving postings, because that is what
  production holds. Borrowing the baseline's statistics makes scores line up
  and measures a system nobody will ship. Keep a diagnostic arm that *does*
  borrow — it is how a loss gets attributed to missing postings vs shifted
  statistics.
- **Wrap the archive; never edit it.** The archived `Searcher` exposed a
  `stats` seam (built for the lean profile) that turned out to be exactly the
  hook the diagnostic arm needed. Look for an existing seam before concluding
  an archived module has to change.
- **The archived engine's own recorded numbers are a free correctness check.**
  The harness's fixture baseline reproduced the archived lexical eval exactly
  (hit@5 0.952 / MRR 0.833) and orbit's lab number (0.887) — which is what
  makes "we varied only the index" a verified fact rather than an intention.

**Earlier knowledge (v0.19–0.26)** is preserved in the archived CLAUDE.md at
git history (`git show 6473987:CLAUDE.md`). Two items still bind
because their code is on the port list:

- **BM25F means weight-then-saturate once** — never sum per-field BM25.
- **No wall-clock output anywhere on the maintenance path** — timestamps derive
  from `SOURCE_DATE_EPOCH`/source mtime, or the byte-identical guarantee breaks.

## Blockers stop the session (required)

**A blocker is a file, not a remark.** The moment you cannot proceed without
Arpit, write `work/BLOCKED.json` and stop:

```json
{"decision":"ASK","reason":"one line","questions":["the minimum question"],
 "safe_alternative":"what you can do meanwhile, or \"\"","surfaced":false,"filed":"YYYY-MM-DD"}
```

`decision` is `ASK` (he can unblock you) · `REFUSE` (disallowed or unsafe) ·
`UNKNOWN` (out of scope to answer reliably) · `PROCEED` (nothing is blocked).

**Do not work around a blocker.** Choosing a plausible default and continuing is
how a week of work lands on the wrong side of a decision nobody made. Say it,
set `surfaced: true`, stop.

Three hooks enforce this rather than trusting anyone to remember —
`.claude/settings.json`:

| hook | does |
|---|---|
| `UserPromptSubmit` | prepends `work/BLOCKED.json` and the OPEN-WORK inbox to every prompt, so a pending decision cannot go unmentioned |
| `Stop` | refuses to end a turn while a blocker is unsurfaced, three times, then relents |
| `PreToolUse` | one writer **per asset** — a `Write`/`Edit`/`MultiEdit`/`NotebookEdit` locks only the file it targets (`.claude/.locks/<hash>/owner`, TTL 900s), so two sessions editing `work/OPEN-WORK.md` at once is still blocked, but two sessions editing different files run in parallel |

## Answer length (required)

**Ten lines or fewer unless asked for more.** Lead with the answer.

**Never summarise work you just did** — the diff showed it. Reasoning only when
asked or when the answer depends on it. No closing offers: ask a real question
or stop. Tables and code over prose. **Length follows the work, not the
effort**; a four-hour change can be three lines. `/output-style terse` carries
the same rules session-wide.

## Say what you are doing (required)

**Announce every transition, in one line, always.** Not a summary — a marker.

```
→ W-56: building fux-lab from SETUP-LAB
✓ W-56 lab environment · → W-56 playground corpus
✓ W-56 · → W-59: the R4 measurement
```

Rules:

- **Before starting**, name the item id and what you are about to do. One line.
- **On finishing**, `✓ <id>` and immediately what starts next. One line for
  both — a finish with no next is a stop, and a stop is its own sentence.
- **Use `TodoWrite`** for anything with more than two steps, and keep it
  current *during* the work. A todo list updated at the end is a report, not a
  plan.
- **Write the current line to [`work/NOW.md`](work/NOW.md)** — one line,
  overwritten. It is read back into the next session, so a session that dies
  mid-task leaves a note rather than a mystery.
- **This is not a recap.** §Answer length still holds: never restate what a
  diff already shows. A transition marker is a pointer, a summary is a
  substitute for reading — the first is required, the second is banned.
