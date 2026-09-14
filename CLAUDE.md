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

## Law zero — the SRs are always up to date

**Arpit, 2026-08-18, emphatic and standing: *always* make sure the SRs are up
to date.** Not at the end of the milestone, not when someone asks — in the
change that makes them wrong.

Three things follow, and none of them is optional:

1. **No behaviour change lands without its SR updated in the same change.**
   Same commit, not the next one.
2. **If a change genuinely touches no recorded decision, say so out loud** —
   `no SR affected`, in the commit message. That is a claim under your name in
   git history, which is the point. Silence is not an answer.
3. **Before you finish a session, re-read the records you touched code under.**
   A record that describes behaviour the code no longer has is worse than no
   record: it reads as authority.

**This is enforced, not trusted.** `tests/test_sr_freshness.py` runs in CI on
every push (with `fetch-depth: 0`, so the runner can see the history it
audits) and fails a commit that changed an SR-owned component without
touching that component's **owning** record specifically — touching some
other record does not satisfy it. `scripts/sr-guard.sh` is the same check as
a `commit-msg` hook (not `pre-commit`: it has to read the commit message to
honor the `no SR affected` escape hatch, and `pre-commit` runs before that
message exists) — install it once:

```bash
ln -sf ../../scripts/sr-guard.sh .git/hooks/commit-msg
```

**Why it is enforced.** Replayed over the 25 commits before the check existed,
**13 of them** changed an owned component and updated no record. The prose rule
was already in this file the whole time. That is the measured case for a check.

⚠ **What the check does NOT prove, and nothing else does either.**
`tests/test_sr_freshness.py` proves an owning record was **touched** in the
change. **It never reads the record.** A record can be amended into
self-contradiction in the same commit and every mechanical check fux has will
pass — **W-83 is the case**: an accepted amendment contradicted itself, the code
implemented the wrong sentence, and CI was green the whole way.

**So point 3 above — re-read the records you touched code under — is the only
thing covering coherence, and it is unenforced.** Treat it as the obligation it
is, not as a tidy-up. Ruled 2026-08-27 (W-82 ruling 18): stated rather than
mechanised, because the two-strikes rule makes a *second* recorded occurrence
the trigger for a gate, and this has happened once.

## Triage first — a human-blocked queue stops the session

**Standing directive (Arpit, 2026-08-12).** Before any work, read
[`work/OPEN-WORK.md`](work/OPEN-WORK.md) and ask: *is any item agent-closable
right now?*

- **If not** — every remaining item is `OPEN·human`, gated on a verdict Arpit
  hasn't read, or waiting on his hands — the session's **first** output is the
  blocked-on-Arpit list (🔴 rows, 🔺 first) in ≤3 lines, then it **stops**.
- No invented scope, no doc polishing to fill the hours. "Next: Arpit reads…"
  buried at the end of a long session is the failure this rule exists to
  prevent; said upfront, it is the rule followed.
- His time and tokens are money. Applies to Cowork and Claude Code alike.
- **The inbox:** OPEN-WORK's header carries a *Blocked on Arpit* block, and
  each open item's file under `work/open/` carries its `filed` date. Every session keeps both
  current, and any `OPEN·human` row older than **5 days** is named, with its
  age, in the session's first output. **Each inbox row has a `↳ blocks:`
  sub-row naming every item that decision holds up** (Arpit, 2026-09-11; OPEN-WORK rule 10).
- **Two strikes → a gate (2026-08-12).** A failure class the WORKLOG records
  twice becomes a test or mechanical check in the same change that records
  the second occurrence — recurring lessons are gated, not re-learned.

## Where the state of play lives

| you want | read |
|---|---|
| what to work on next | [`work/OPEN-WORK.md`](work/OPEN-WORK.md) — **the single live queue**, two lanes |
| the spec for a milestone id | [the SR register](records/README.md) |
| why the architecture is this shape | [`work/paper/the-fux-index-paper.md`](work/paper/the-fux-index-paper.md) |
| a closed decision + its reopen-trigger | [`work/compare/`](work/compare/README.md) |
| the judgment behind the reset | [`work/INTERVIEW.md`](work/INTERVIEW.md) |
| a word you don't recognise | [`docs/GLOSSARY.md`](docs/GLOSSARY.md) |
| what has actually shipped | [`work/IMPLEMENTATION.md`](work/IMPLEMENTATION.md) |
| the measured evidence behind a claim | [`work/regression/`](work/regression/README.md) |
| what a benchmark run always captures | [SR-WORK-BENCHMARK](records/0053_WORK-benchmark.md) — the seven, stated once |
| why a command fails on *this* surface | [`work/MACHINE.md`](work/MACHINE.md) |
| which record owns a module | [`records/README.md`](records/README.md) §Ownership |
| the stages a feature moves through | [SR-WORK-LIFECYCLE](records/0058_WORK-lifecycle.md) |
| what a session owes before it ends, and how long an answer may be | [SR-WORK-SESSION](records/0060_WORK-session.md) |
| what a task owes the documentation | [SR-WORK-DOCS](records/0059_WORK-docs.md) |
| whether a number above 10 000 may be written down | [SR-WORK-SCALE](records/0057_WORK-scale.md) |
| whether a claim may be grounded in an archived doc | [SR-WORK-ARCHIVE](records/0062_WORK-archive.md) |
| what the bundle requires of a new doc | [SR-WORK-OKF](records/0061_WORK-okf.md) |
| how a release reaches PyPI and npm, and what blocks a merge | [SR-WORK-RELEASE](records/0063_WORK-release.md) |
| what to do when you cannot proceed without Arpit | [SR-WORK-BLOCKERS](records/0064_WORK-blockers.md) |
| the whole set of rules about how work is done | the **WORK** records `0051`–`0064` — [the register](records/README.md) §The register |

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
  [SR-EXTRACTED](records/0115_extracted-mode.md) — **accepted**) and
  `enriched` (opt-in, model-assisted,
  [SR-ENRICH](records/0137_enrich.md) — **accepted**: the name, the
  boundary and the record shape are ratified; **the build is not**). Both
  ratified by Arpit 2026-08-19. ⚠ **SR-ENRICHED was superseded 2026-08-27** —
  its contract was folded into SR-ENRICH verbatim first, and the
  non-authorization came with it (SR-ENRICH decision 8). **`fux enrich` is a
  different feature** and shipping it did not authorize the mode.
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

**Out of scope until it has an SR and Arpit's sign-off:** anything from the
archived build (the SQLite substrate, per-file cache, lean profile, state
plane, `fux.lock`), further adapters beyond the capped three, MCP (it is
[a proposal](work/proposals/mcp-adapters.md), not a backlog item), and every
M8 item.

**Do not port the archived engine.** [the SR register](records/README.md) §"What survives"
is the complete port list; each entry comes forward **with its tests**, when
its milestone needs it. Nothing else comes back.

## Non-negotiable constraints (generated — NOT the source)

⚠ **This section is NOT normative, and has not been since 2026-09-12.** Each law
is *stated* in exactly one record — [SR-LAW-0](records/0002_LAW-0-authority.md)
through [SR-WORK-ENVIRONMENTS](records/0052_WORK-environments.md) — and the block below is
**generated from them** by [`scripts/gen-laws.py`](scripts/gen-laws.py) and held
byte-equal by [`tests/test_claude_md_laws.py`](tests/test_claude_md_laws.py).

**So: amend the record, then run `python scripts/gen-laws.py --write`.** Editing
the block here is reverted by the next generation and fails the test in between.
It is reproduced at all because this is the file every session reads first, and
[SR-LAW-0](records/0002_LAW-0-authority.md) decision 5 permits a generated view
**for exactly as long as a test binds it** — remove the test and this block
violates decision 1.

[SR-LAWS](records/0001_LAWS.md) assigns the handles `L0`–`L8` and `L10` and routes each
to its record; that is all it does now.

<!-- LAWS:BEGIN — GENERATED from records/*_LAW-*.md by scripts/gen-laws.py. Do not edit by hand: amend the record, then run `python scripts/gen-laws.py --write`. -->

- **L0** · **SRs are the only source of truth, and the Law records outrank
  every other record.** Every rule is *stated* in exactly one SR; every other
  artifact — `CLAUDE.md`, a schema, a config comment, a skill, a diagram —
  **links to it and never restates it**, and a change is made in the record
  first. The Law records `SR-LAW-0`…`SR-WORK-ENVIRONMENTS` outrank every other SR: **a
  record that conflicts with a Law is void in the conflicting part**, never a
  trade-off to weigh. **A Law changes only on Arpit's ruling, named in the
  record**; an ordinary SR a session may accept.
  ⚠ **The test that decides a restatement:** *could this artifact and the
  record disagree while both still look correct?* If yes it is a restatement
  and is forbidden; if it would simply fail, it is an implementation
  (`config.py` naming a key) or an enforcement (a runtime schema, a test) and
  is permitted.
  ⚠ **`CLAUDE.md` §Non-negotiable constraints is NOT normative** — since
  2026-09-12 each law is stated in its own `SR-LAW-n` record, and what
  `CLAUDE.md` carries is generated from those records and held equal by a test.
  Precedence is **judgment, never a gate** — no parser reads *"does this
  contradict L2"* — and a record self-contradicting inside one file stays
  ungated. [SR-LAW-0](records/0002_LAW-0-authority.md).
- **L1** · **`$0`, FOSS-only.** Fux is zero-cost to run and carries no
  proprietary dependency: **no commercial licence, no paid or metered API, no
  subscription, no hosted model — ever.** Every dependency ships under an
  **OSI-approved licence**, identified by its **SPDX identifier**; permissive
  and copyleft both qualify, and nothing else does.
  ⚠ **Source-available is not open source, and that is the trap this clause
  exists for.** BSL 1.1, SSPL, Elastic License 2.0, Commons Clause, "fair
  source", and the free tier of a commercial product all **fail** L1 —
  precisely because each one looks like it passes. **The test is the OSI
  approved-licence list**, never the price, never a public repo, never the word
  "open" in a README.
  **Dependencies ship packaged.** Fux is one install with everything it needs —
  no optional extras, no "install this for PDFs", no capability that works on
  one machine and not another because of what somebody chose at install time.
  **Permission is not authorization:** the law permits a dependency, a record
  still decides one, and every runtime dependency is named by an accepted SR.
  **Dev, test and measurement tooling is bound by the same licence rule and
  nothing more** — OSI-licensed, and numpy/pandas/scipy explicitly fine.
  ⚠ **Amended 2026-09-06** (Arpit). The previous form forbade third-party runtime
  dependencies outright — the zero-dependency guarantee, sold as the product's
  central promise. **That guarantee is withdrawn**, deliberately, and
  [SR-LAW-1](records/0003_LAW-1-zero-cost.md) carries what it bought, what replaced
  it, and the three things it left unguarded.
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
- **L8** · **A use record is never committed.** Fux may record what was asked
  and what was answered — **in plaintext, with no law-level size bound** — and
  may print a per-answer provenance receipt on stdout. **Every durable trace of
  use lives on a gitignored path and never reaches a committed byte.**
  ⚠ **Gitignored is the test, not `.fux/`.** `.fux/index/`, `sources/`,
  `fetchers/`, `decoders/`, `enrich/`, `tune.toml`, `output.toml` and
  `.fuxignore` are all **committed**; `.fux/runtime/` is the only derived
  directory under it. *"Inside `.fux/`"* is not the rule and would put a journal
  beside the committed index. **L2 governs the corpus; L8 governs the record of
  who went looking in it** — a query is not content, and no other law reached
  it. ⚠ **Ruled three times on 2026-08-27 (Arpit): written, reverted, then
  narrowed to commits alone.** Hashing, a size bound, the stdout prohibition and
  **the transmission clause** were all in earlier forms and none survives;
  [SR-LAWS](records/0001_LAWS.md) decision 8 carries each pass and what it
  traded away — **including the gap the last one leaves open.**
- **L10** · **The consumer is served build output, never source.** Code fux puts in front of a consumer — `.py`, `.mjs`, `.js`, `.ts`, vendored into their tree or exported by a published package — is ONE generated artefact per plane, bundled at publish and never on their machine. The only exceptions are the consumer's own extension points, [`.fux/decoders/`](records/0139_decode.md) and [`.fux/fetchers/`](records/0117_fetcher.md), where readable source IS the contract. Bundled ≠ minified.

<!-- LAWS:END -->

## Litmus for any new work

**The design point is 10 000 documents, and it is a ceiling on what may be
measured and on what may be promised** (Arpit, 2026-08-21; the ceiling
2026-08-22). The rule, the three things it explicitly does not do, and the
per-sentence test are stated once in
[SR-WORK-SCALE](records/0057_WORK-scale.md) and are **not repeated here**.
Read decisions 1–7 before writing any number above 10 000 into a document, and
13 before treating a deferred-size gate as a blocker.

## How work happens here (the lifecycle)

**Every non-trivial feature moves through committed stages, and every handoff
and prompt names the model that should execute it.** The stages, the model
table, and what each stage owes are stated once in
[SR-WORK-LIFECYCLE](records/0058_WORK-lifecycle.md) — read it before scoping
work (decisions 6–8 before handing a prompt to anyone). The record convention
itself is [`records/README.md`](records/README.md).

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

**This repo is a declared Open Knowledge Format v0.1 bundle**, rooted at
[`docs/index.md`](docs/index.md). What the bundle contains, the field it
requires, the tracker vocabulary and the three declared boundaries are stated
once in [SR-WORK-OKF](records/0061_WORK-okf.md), enforced by
[`tests/test_okf_bundle.py`](tests/test_okf_bundle.py).

## Documentation (required)

**Three rule groups, one home, none of them restated here** —
[SR-WORK-DOCS](records/0059_WORK-docs.md):

- **how a doc is written** — decisions 1–5.
- **who may edit the agent-steering files, including this one, and under what
  two obligations** — decisions 6–8. **Read these before editing `CLAUDE.md`.**
- **the seven documents every task updates before it is done** — decisions
  9–13, and the registry rules in 11.

**The shared memory between sessions is [`work/`](work/README.md)**; `docs/`
holds what the project *is*. Read [`work/README.md`](work/README.md) once; it is
the map.

### OPEN-WORK — the single live queue

[`work/OPEN-WORK.md`](work/OPEN-WORK.md) is the *only* queue, and it is the
**list and nothing else**. Its rules — what the file is, an item's lifecycle,
the shape of a row, the four balls, ordering, the Blocked-on-Arpit inbox and the
standing obligations — are stated once in
[SR-WORK-OPEN-QUEUE](records/0051_WORK-open-queue.md) and are **not repeated
here or in the queue** (Arpit, 2026-09-13). Read that record before touching an
item.

### Archive is not evidence

**There is exactly one archive, [`archive/`](archive/README.md) at the repo
root.** What may be named, what may never be cited, how a citation is
repointed, the exposure the rule leaves unguarded, and the records exception are
stated once in [SR-WORK-ARCHIVE](records/0062_WORK-archive.md) — decisions 4–8
are the ones that decide whether a Reference block is legal.

### The SR standing rules

The register, the convention and the ownership table are in
[`records/README.md`](records/README.md). What binds every session:

- **No behaviour change lands without its SR updated in the same change.**
  See §Law zero. If a change genuinely touches no recorded decision, **say so
  explicitly — `no SR affected` in the commit message** — rather than silently
  skipping the check. Enforced by `tests/test_sr_freshness.py` (CI) and
  `scripts/sr-guard.sh` (`commit-msg` hook); neither can be satisfied by
  intending to update the record later.
- **Cite records by name, never by number.** `SR-RECORD`, not
  "ADR-0004". Numbers exist only so the archive can map a retired record to its
  successor. A live doc citing a number is a defect; fix it on contact.
  ("archived SR-NNNN" *with its path* still means the frozen v0.26 line.)
- **Ownership is a table, not a judgement call.** Every `src/`/`tools/`
  component is claimed by exactly one record in `records/README.md`. **When
  the table changes, edit [`tests/test_sr_ownership.py`](tests/test_sr_ownership.py)
  in the same change** — they drift silently otherwise, which is why the
  executable twin exists.
- **A record that restates a cross-cutting principle is a bug, not
  redundancy.** Each law has exactly one home — **its own
  [`SR-LAW-n`](records/0002_LAW-0-authority.md) record** — and
  [SR-LAWS](records/0001_LAWS.md) assigns the handles L0–L8 and L10 and routes to
  them. Every other record cites `SR-LAWS` and the number; none paraphrases.
  Paraphrases drift, and a drifted paraphrase in an accepted record reads as
  authority.
- **Veto conditions are conditions to check, never events to await.** State
  what would have to become *true* to reopen the decision, so it can be checked
  mechanically today. An event never fires, because nobody is waiting.
- **§1 is for humans (one screen, with a Mermaid diagram and its hand-paired
  ASCII twin — both updated together, the twin collapsed in a `<details>`
  block); §2 is for agents** (context · decision ·
  consequences · alternatives · reference · veto). The reference is grounded in
  code, a live doc, or measured evidence — **never an archived doc**.
- **Records live in `records/`, and nowhere else.** There is no archive tier
  for records (Arpit, 2026-09-06): a superseded record is **rewritten or deleted
  in the same change that accepts its successor**, and the successor states in
  prose what it replaced. Nothing is left behind to be found and mistaken for
  current, and no live doc may link to a retired record — the file is gone.

## Session continuity — what a session owes (required)

**Four files, one-line transition markers, and the rules that govern every
reply you write** — the worklog entry (a chat-only session counts), the
interview, the milestone log and [`work/NOW.md`](work/NOW.md) — are stated once
in [SR-WORK-SESSION](records/0060_WORK-session.md).

**Read it before your first answer, not before your last:** decisions 1–5 are
the files, 6–7 the markers, 8–9 how long an answer may be, and 10–12 the two
hazards of sharing a machine with another session.

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
6. **Classify the run — `blind` or `informed` — in the report's frontmatter,
   and name who authored each artifact and what evaluation material they could
   reach.** Required from 2026-08-25 for every *measured* run; a surface
   capture is exempt. See below.

**Every measured run is `blind` or `informed`, and says which.** A run is
**blind** only if *every* artifact it depends on — corpus enrichment, the
enrichment prompt, chunking and index configuration, retriever and reranker
settings, **and the analysis** — was authored with no access to the evaluation
queries, the judgments, prior per-query scores, or any derived report of them
(a failure list, a dashboard, a ticket naming a query). Anything else is
**informed**.

- **An informed run is reclassified, not banned.** File it, list it, cite it,
  let it inform the corpus. It is **never compared with a blind run and never
  used to state a delta.** This is TREC's manual/automatic split; a rule that
  bans useful work gets routed around, a rule that sorts it survives.
- **Say who authored each artifact and what they could reach** — *queries /
  judgments / prior scores / none*. The burden is on the author to argue
  exposure was absent. An informed number is **not** an "upper bound" (that
  claims a bounded magnitude a leak does not have); label it **"not a
  generalisation estimate."**
- **A delta below the set's resolution is "no detected change"**, whoever
  authored it. ⚠ **The floor is no longer a placeholder — it is MEASURED, and
  the old one was far too loose** (Arpit, 2026-08-28). Two arms graded on the
  same queries is a **paired** comparison, so only the queries that **flip**
  carry information: **the bar tracks the discordant count, never the set
  size.** **A net of 6 is the floor of all floors — a net of 1, 2, 3, 4 or 5
  cannot clear α = 0.05 at any discordant count** — and it rises from there
  (20 flips → net 10; 50 flips → net 16). The old *"±2 on 50"* admitted results
  whose best possible p-value is **0.50**. Table, script and the α discussion:
  [SR-RS](records/0133_predictions.md) decision 19.
- 🔴 **Every measured run records its PER-QUERY RESULTS under `evidence/`** —
  one row per query per arm, pass/fail. **Ruled by Arpit 2026-08-28:** *"record
  all the questions so we can check in detail."* ⚠ **A summary count is not
  enough and never was.** The discordant count, `b`, `c`, and every test anyone
  runs later are derivable from per-query rows **and from nothing else** — so a
  run that files only totals cannot be re-tested by anybody, including its own
  author. **No run filed before 2026-08-28 has them**, which is why none of the
  paired results on record can be checked from what was filed.
- **Do not edit a frozen report to classify it.** The rule is baselined at
  2026-08-25 on the run directory's own date, and
  `tests/test_regression_runs.py` checks it from there.

Ruled by Arpit 2026-08-25 (W-78 ruling 2); explained and guarded by
[SR-RS](records/0133_predictions.md) decisions 11-15. ⚠ Two parts of the
accepted rule — a **sealed** query set and the **decoy/placebo controls** — are
**not built** and are owed as W-81; nothing may cite them as in force.

**A verdict is not an SR.** When a run adjudicates a pre-registered
prediction, the ruling is a `VERDICT.md` beside its evidence — `type: Verdict`,
with the prediction id and the frozen pre-registration path. An SR records a
decision someone can supersede; **nothing supersedes a measurement except a
better measurement**, which is a new run with its own verdict. The *decisions*
that rest on a verdict live in `records/` and cite it. Enforced by
`tests/test_regression_runs.py`.

**The reproduce command must actually reproduce.** Findings that warrant a
change graduate to `work/proposals/` and, when accepted, an SR. Never ship a
ranking/behaviour change off a single synthetic corpus.

## Golden answer key — Claude never reads it (required)

**Arpit, 2026-09-11.** `work/golden/golden-answer/` holds the sealed benchmark's
questions and answers. **Arpit, Codex and ChatGPT may read it. No Claude session
may** — Cowork, Claude Code or subagent — by any tool: not to check the format,
count lines, hash it, or `grep -r` across `work/`.

- A leak does not fail loudly; it yields a benchmark number that looks clean.
- Guarded by `.gitignore`, `!work/golden` in `.fux/sources/dirs`, deny rules and
  `.claude/hooks/guard-golden-answer.sh` — **none is a guarantee** (same Mac user),
  and Cowork is covered only by this paragraph.
- **If a question or answer ever appears in your context, stop and say so.**
- The process, and what Claude may read (`seed/`, `questions.jsonl` after release):
  [`work/golden/README.md`](work/golden/README.md).

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
  architecture-{high-level,detailed,decoders,ask,answer,two-readers}.svg   the six
                    diagrams, redrawn from the code 2026-09-12. proposal-search-v3-target.svg is
                    a PROPOSAL's target state, deliberately outside that namespace.
  open/             one detail file per open W-nn; deleted with its row
  setup/            the three siblings — playground · lab · benchmark — outside this repo
                    (SR-WORK-ENVIRONMENTS)
  regression/       dated, measured evidence other docs cite as grounding; VERDICT.md rules
  golden/           the sealed benchmark — seed docs, ladder manifests, prompts; golden-answer/ is NEVER read by Claude
  compare/          live forks — verdict + explicit reopen-trigger
  proposals/        parked ideas, not yet decided
records/            THE STANDING RECORDS — the register, TEMPLATE.md, SR-LAWS and
                    SR-LAW-0…SR-LAW-10; new records land here. At the repo root
                    since 2026-09-13, and in the OKF bundle from wherever it sits
docs/               WHAT THE PROJECT IS
  GLOSSARY.md       every recurring term, defined once
  index.md          the OKF bundle root
src/fux/            the engine — every component claimed in records/README.md
tests/              the suite, incl. test_sr_ownership.py (the ownership twin)
tools/
  pruning-eval/     the gate — frozen pre-registrations, KL selector, eval harness
  differential/     the differential-law harness and the R3 bench
archive/            THE ONE ARCHIVE — everything retired, mirroring the live tree
  README.md         the map: every archived doc and its live successor
  adr/              superseded records; maps old number -> successor NAME
  handoff/          the retired handoff directory (executed pairs + unresolved specs)
  v0.26/            build: the previous engine — runnable, REFERENCE ONLY
  v0.26-docs/       build: the frozen v0.19–0.26 doc set ("archived SR-NNNN")
  v0.26-implemented/ · v0.30-rev1-planning/   frozen build artifacts
  v0.1/             build: the first one
```

**Records live in `records/`, and only there.** A superseded one is rewritten
or deleted in the same change that accepts its successor; the successor names
what it replaced, in prose. `work/adr/` no longer exists, and on 2026-09-06
Arpit deleted the archived records outright — there is no archive tier to
consult, and a record citation resolves into `records/` or not at all.

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

**`fux-engine` 2.0.0 is released on PyPI *and*, since 2026-09-12, on
npm**; `src/fux/` is the live tree and `node/` is the Node reader. One name in
both registries. **The two registries are NOT reached the same way:** a GitHub
release publishes to PyPI automatically (OIDC), while the npm half *stages* and
waits for a human to approve it on npmjs.com — npm's own recommendation, taken
deliberately. Both jobs hang off one `release: published` trigger in
[`publish.yml`](.github/workflows/publish.yml).

```bash
uv sync --extra dev
uv run pytest -q tests        # fast unit
uv run pytest -q tests_e2e    # the package as a user
node --test node/test/*.test.mjs               # the Node reader's own units
python -m fux.store.nodebundle node node/dist  # the published bundle (L10)
```

**What a consumer is served is BUILD OUTPUT, and since 2026-09-12 that is
[L10](records/0011_LAW-10-bundled-output.md).** `node/` is 44 authored `.mjs`
files; what `fux setup` vendors and npm publishes is **one generated
`fux.mjs`** — built by `src/fux/store/nodebundle.py`, into the wheel by
[`hatch_build.py`](hatch_build.py) and into the npm tarball by `publish.yml`,
from one build. ⚠ **`node --test node/test` (no glob) is not the invocation** —
it resolves as a module path and fails with `MODULE_NOT_FOUND`, which reads like
a test failure and is not one.

**A test that builds a repo by hand writes `.fux/pii.toml`** (an empty file is
enough), or ingest and every CLI verb refuse — [SR-PII](records/0148_pii.md)
decision 17.

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

## Package identity and release (do not change casually)

**Distribution name `fux-engine`; import package `fux`; released on PyPI and on
npm.** How a release reaches both registries, where the version number lives and
what keeps its copies equal, and what the merge wall does and does not block are
stated once in [SR-WORK-RELEASE](records/0063_WORK-release.md) — **read
decisions 10–11 before merging anything.** The version's history is
[`CHANGELOG.md`](CHANGELOG.md)'s and is not duplicated.

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

**2026-09-12 — two sessions, one machine**

- 🔴 **A RED TEST ON AN UNCOMMITTED TREE IS INVISIBLE TO EVERY MECHANISM HERE.**
  CI reads commits; the SR-freshness hook reads a commit message; `pytest` reads
  whatever you choose to run. A test that a working-tree change turns red stays
  red and unseen until somebody commits — and then it fails for whoever committed
  it. **It bit two sessions on the same day for different reasons.** The only
  cover is to run **both suites, whole**, before believing a change is done;
  reading the code and concluding is what failed.
- 🔴 **A loaded machine does not produce noise — it produces a clean, localised
  anomaly that reads like a finding.** One session's corpus build inflated a
  single benchmark tier's ingest ratio to **0.77 against ~0.46 everywhere else**:
  tier-localised, internally consistent, and in exactly the shape a real
  regression takes. **Noise gets distrusted; this would have been filed.** It was
  caught by two sessions comparing timestamps — a conversation, not a mechanism.
  Interleaving arms (`A B A B`) is the only structural defence and it protects
  the *difference*, never the absolute number.
- **So: say what you are running, and when, to anyone sharing the machine.** It
  is the only thing that worked. Recorded in
  [SETUP-BENCHMARK](work/setup/fux-benchmark.md) standing rule 0a as an
  **unguarded** gap, because it is one.
- **Concurrent sessions commit, too.** A peer committed a fix to code this
  session had written and not yet committed. Re-derive `git status` immediately
  before staging, and **commit with explicit pathspecs** — `git commit -- <paths>`
  — when the index carries another session's work.

**Earlier knowledge (v0.19–0.26)** is preserved in the archived CLAUDE.md at
git history (`git show 6473987:CLAUDE.md`). Two items still bind
because their code is on the port list:

- **BM25F means weight-then-saturate once** — never sum per-field BM25.
- **No wall-clock output anywhere on the maintenance path** — timestamps derive
  from `SOURCE_DATE_EPOCH`/source mtime, or the byte-identical guarantee breaks.

## Blockers stop the session (required)

**A blocker is a file — [`work/BLOCKED.json`](work/BLOCKED.json) — and the
session stops.** Its shape, the four decision values, the prohibition on working
around one, and the three hooks that enforce it are stated once in
[SR-WORK-BLOCKERS](records/0064_WORK-blockers.md).

