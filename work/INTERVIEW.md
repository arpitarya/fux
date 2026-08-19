# Model handoff — the agent-succession record

*The premise: the departing model answers for the record, so whatever succeeds it —
next model, next session, next agent — inherits the judgment and not just the files.
Governed by the same law as everything else here: keep it true, or flip the note.*

**Standing instruction to every future model reading this: you are now the
maintainer of this document. When the project's direction, decisions, or state
change, update it in the same change — CLAUDE.md binds you to that. You will retire
too. Leave it better.**

---

## How to use this file

**This is a state-of-play doc, not an end-of-session report.** Keep it current
*during* the session — the moment direction, a decision, or the live state
changes, not in a wrap-up pass. Write it for a **different model, arriving with
zero other context, mid-task**: someone who has never seen this repo should be
able to read the four sections below and resume warm.

**A stale INTERVIEW at handoff is as serious as a missing changelog entry.**
The four sections below are maintained. Everything after them is history —
valuable judgement, but not the state of play.

---

## 1 · State of play

*Updated 2026-08-19.* **Ground it before you edit it** — `git log`, `git tag`,
[`IMPLEMENTATION.md`](IMPLEMENTATION.md), [`regression/`](regression/README.md).

### The most recent change: W-54, the sources rewrite (2026-08-19)

- **The URL path works for the first time.** Five latent defects — shipped,
  real, and with no current victim because this repo does not use URL ingest —
  closed in five commits, each with its records. Evidence:
  [`regression/2026-08-19-w54/`](regression/2026-08-19-w54/report.md).
- **Both source lists are files now.** `.fux/sources/dirs` and
  `.fux/sources/urls`, one entry per line, **one parser**
  ([`ingest/sourcelist.py`](../src/fux/ingest/sourcelist.py)). `[sources] dirs`
  and `[sources.url] middleware` are retired keys that stop the run with
  instructions — **two breaking changes**, both cheapest now.
- **Two new verbs, eight in total.** `fux setup` writes the files a consumer
  owns (write-if-missing, from wheel package data); `fux url` records a URL with
  every attribute stated and **never fetches**. ADR-CLI's mental model is now
  four groups — lifecycle / write / sources / read — because the *count* was
  never the model. **"No subcommand tree" is the constraint that survived.**
- **`title_h` carries an `h:` prefix.** That was the defect with a measured
  cost: the L5 `hashed` default wrote an index no `fux build` would accept, so
  27.2 ms became 4 248.8 ms. **Fixed in the field's shape, never in the
  accelerator invariant.** No `_format` or `analyzer` bump — the reasoning is
  [ADR-INDEX-LIFECYCLE](../docs/adr/0009_index-lifecycle.md) decision 9, and
  the migration is `fux ingest --refresh-urls`.
- **`archived=` is parsed and deliberately unread.** ADR-DIR-LIST decision 10
  was amended to split the file from the signal: parsing a declaration nothing
  reads cannot be wrong, and changing what a verb says about a document needs
  an instrument. [W-44](open/W-44-archived-content-signalling.md) still owns it.

### Before that

- **M0, M1 and M2 have shipped.** `v0.32.0` is on PyPI (2026-08-13, verified
  black-box from the published wheel). `fux ingest` / `build` / `ask` / `find`
  / `answer` work end to end, with the derived T1 accelerator on warm queries.
- **R1 · R2 (3/3) · R3 all PASS.** R3's number: worst-case warm p95 **27.2 ms**
  on 8 870 RFCs against a pre-registered 150 ms bar.
- **The pruning gate closed FAIL.** The committed index carries full postings,
  permanently. That design branch is closed, not paused.
- **Hybrid fusion is built and ships default-off**, on a measured net −6.
  Flipping it needs new evidence *and* a separate sign-off.
- **Documentation moved into [`work/`](README.md) on 2026-08-18**, and the ADR
  system was rebuilt around cite-by-name, §1-humans/§2-agents, checkable veto
  conditions, and an ownership table with an executable twin.
- **A second move the same day** took the paper, both architecture diagrams,
  `handoff/`, and the eight v0.30 records into `work/`. `docs/` now holds only
  `GLOSSARY.md`, `index.md`, and the ADR register with `TEMPLATE.md`
  and ADR-LAWS.
- **The new record set has started.** [ADR-LAWS](../docs/adr/0001_laws.md)
  opened it at 0001; **[ADR-CLI](../docs/adr/0002_cli-surface.md)** is 0002 —
  the six-verb command-line surface, with every command and its real output
  captured in [`regression/2026-08-18-cli-surface/`](regression/2026-08-18-cli-surface/report.md).
  Writing it found a live defect ([W-46](open/W-46-hybrid-missing-model-crash.md)).
- **A great deal of valuable writing is not a decision** (2026-08-18). Three
  documents left `work/adr/` without being superseded, because none of them was
  ever an ADR: the two P1 rulings became **verdicts** beside their evidence,
  and ADR-PLAYGROUND became **SETUP-PLAYGROUND** in
  [`setup/`](setup/README.md) — most of it was how to stand up a sibling repo,
  not a position anyone argues with. A new **SETUP-LAB** was written the same
  day; the lab had run for weeks with its rules scattered across memory, a
  TEST-PLAN and a dozen worklog entries. **`work/adr/` is now five records, and
  every one has a named successor** — what is left is ratification, not writing.
- **A verdict is not an ADR** (2026-08-18). The two P1 rulings left the record
  set and became `VERDICT.md` files beside their evidence — `P1-GATE`
  (INCONCLUSIVE) and `P1-RERUN` (FAIL). Nothing supersedes a measurement except
  a better measurement, so a verdict is cited, never replaced. Only
  **SETUP-PLAYGROUND** is now unsuperseded in `work/adr/`.
- **`PLAN.md` is archived** (2026-08-18). Milestone scope was migrated into
  each W-item's detail file, so **an open item is now its own spec**; the port
  list became [ADR-PORT-LIST](../docs/adr/0015_port-list.md). `docs/` holds
  `GLOSSARY.md`, `index.md` and `adr/`, and nothing else.
- **Five more records landed 2026-08-18, all ⏳ proposed:**
  [ADR-RECORD](../docs/adr/0010_index-record.md) (the committed line, property
  by property), [ADR-T1-ACCELERATOR](../docs/adr/0011_accelerator.md),
  [ADR-RANKING](../docs/adr/0012_ranking.md),
  [ADR-POSTINGS](../docs/adr/0013_postings.md),
  [ADR-CONFIG](../docs/adr/0014_config.md). **The template's §1 now carries
  optional Examples and Charts sections**, and all nine earlier records were
  retrofitted with Examples in the same change.
- **Three verb records landed 2026-08-18, all ⏳ proposed:**
  [ADR-ASK](../docs/adr/0004_ask.md), [ADR-FIND](../docs/adr/0005_find.md),
  [ADR-ANSWER](../docs/adr/0006_answer.md) — written from a captured session
  ([`regression/2026-08-18-query-verbs/`](regression/2026-08-18-query-verbs/report.md)).
  The earlier three were re-indexed to 0007–0009 to seat them at the numbers
  Arpit chose; **no prose moved**, because records are cited by name.
- **Four more records landed 2026-08-18, all ⏳ proposed:** [ADR-DOTFUX](../docs/adr/0003_fux-directory.md), [ADR-INGEST](../docs/adr/0007_ingest.md), [ADR-URL-INGEST](../docs/adr/0008_url-ingest.md), [ADR-INDEX-LIFECYCLE](../docs/adr/0009_index-lifecycle.md) — written from a captured session in [`regression/2026-08-18-ingest-and-index/`](regression/2026-08-18-ingest-and-index/report.md). **They retire nothing yet**: three predecessors are unratified, so W-30/W-31 gate the swap.
- **The v0.30 record set is archived** (2026-08-18, Arpit's instruction, all
  five at once). `work/adr/` no longer exists; the map with a successor for each
  is [`../archive/adr/README.md`](../archive/adr/README.md). **The successors are
  accepted** and hold the components — a record cannot own the engine and be a
  proposal at the same time. Records that supersede nothing (ADR-FIND,
  ADR-ANSWER, ADR-RANKING, ADR-POSTINGS, ADR-PORT-LIST) stay ⏳ proposed.

## 2 · In flight, and the immediate next step

*Updated 2026-08-19.*

- **Nothing is half-built in `src/`.** W-54 landed complete — five sections,
  five commits, both suites green, `scripts/adr-guard.sh` exit 0. There is no
  partially-landed feature to finish.
- **The ADR rewrite is done.** `work/adr/` no longer exists; `docs/adr/` holds
  the live set, ADR-LAWS at 0001, and every archived record maps to a successor
  by **name** in [`../archive/adr/README.md`](../archive/adr/README.md).
- **The Lane B inbox is empty.** W-30, W-31, W-32, W-33 and W-44's decision
  were all ratified by Arpit on 2026-08-19 and their outcomes are in
  [`IMPLEMENTATION.md`](IMPLEMENTATION.md) §Ratified decisions.
- **`v0.33.0` is released and on PyPI** (2026-08-19), verified black-box from
  the published wheel: `fux setup` → `fux url` → `fux ingest` → `fux ask` in a
  fresh repo, from the installed package. CI and the publish workflow both
  green. **`CHANGELOG.md` `[Unreleased]` is empty.**
- **The immediate next step is M3 (W-23) or M4 (W-24), both unblocked.** M4 first is
  the standing recommendation — it is where two filed proposals graduate, and
  its API shape is the expensive thing to retrofit later. **M4 has no live
  spec**: the `v0.33.0` handoff pair was archived unexecuted, so whoever starts
  W-24 writes a fresh spec into its detail file first, **by Opus**, because two
  proposals graduate into the API shape.
- **Two items are PARKED behind one missing instrument** —
  [W-44](open/W-44-archived-content-signalling.md) and
  [W-52](open/W-52-df-over-the-union.md) both wait on a pre-registered query
  set with expected live-vs-archived answers. Nobody owns writing it. They
  resume when it exists, **not because they look ready**.
- **Three findings from W-54's run are not filed as items** and are named in
  its [ANALYSIS.md](regression/2026-08-19-w54/ANALYSIS.md): `fux doctor` should
  check the source lists, the generated `.fux/README.md` does not mention
  `dirs`, and the duplicated HTML→markdown pass is accepted rather than a
  defect. The first should ride with W-44.

## 3 · Standing constraints

The **laws** are normative in [`../CLAUDE.md`](../CLAUDE.md) §Non-negotiable
constraints and named L1–L7 by
[ADR-LAWS](../docs/adr/0001_laws.md). They are not restated here — that is the
rule ADR-LAWS exists to enforce. What follows are the constraints *on the work*,
which are not laws:

- **There is no handoff directory.** Retired 2026-08-18 on Arpit's
  instruction and moved wholesale to `archive/handoff/`. **A spec for open work
  lives in that item's detail file under [`open/`](open/README.md)** — spec and
  state in one place. Four of the archived artefacts were unresolved when they
  went (the ratification package, three `CLAUDE.md` diffs, the M4 pair); they
  may be named, never cited, and **M4 has no live spec** as a result.
- **There is exactly one archive, at the repo root.** Arpit's ruling of
  2026-08-10, restated 2026-08-18 after the `work/` restructure quietly
  reintroduced a second one. Anything archived moves to
  [`../archive/`](../archive/README.md), into a directory mirroring where it
  came from, with a row naming its live successor. Enforced by
  `tests/test_archive_law.py`.
- **Law zero: the ADRs are always up to date.** Arpit's standing instruction,
  2026-08-18, given emphatically. No behaviour change lands without its record
  updated in the *same* change; a change that touches no recorded decision says
  `no ADR affected` in the commit message. Enforced by
  `tests/test_adr_freshness.py` in CI and `scripts/adr-guard.sh` as a
  pre-commit hook — do not treat it as advisory, and do not "fix it in the next
  commit".
- **No M-milestone work while its gating prediction is unmeasured or failed.**
  A hard sequencing rule, not a preference.
- **A pre-registered threshold may never move.** Ambiguous results go to Arpit
  unadjudicated.
- **Do not port the archived engine.** [ADR-PORT-LIST](../docs/adr/0015_port-list.md)
  is the complete list, and it is closed; each entry comes forward with its
  tests, when its milestone needs it.
- **Do not design in reference to Anton.** The design point is a 10k-engineer
  corporation's mega-project. Anton is a testbed, not the priority filter.
- **The adapter cap (git + HTTP + Confluence) is a decision**, not a backlog.
- **`work/regression/` is the evidence store; the lab is scratch.** Never
  compare wall-clock across surfaces — see [`MACHINE.md`](MACHINE.md).

## 4 · Lessons learned

The ones that would change how a successor acts, newest first. Add to this list
when a session produces a lesson; do not let it become a changelog.

- **A law enforced over the wrong corpus is not enforced** (2026-08-19). The
  differential harness had asserted scan-vs-accelerator equality for a whole
  milestone and had **never once run against a hashed record** — the exact
  shape that broke the invariant. The law was right, the check was right, and
  the corpus it ran on could not reach the bug. **When you add a record shape,
  add it to the harness in the same change**, or the harness certifies a system
  nobody ships.
- **Fix the shape, not the check** (2026-08-19). `title_h` tripped the
  accelerator's build invariant, and the cheap fix was to relax the invariant.
  That invariant is the only thing between the engine and a *fast wrong answer*.
  Prefixing the field so the check cannot fire made the two paths agree **by
  construction** — strictly better than agreeing by assertion, and it cost one
  character. **When a check keeps firing on legitimate data, suspect the data's
  shape before the check.**
- **Do not edit a filed run's evidence** (2026-08-19). W-54's work order said to
  extend the 2026-08-18 fixture; that fixture reproduces the *pre*-W-54 surface
  and is what that run measured. Rewriting it would have made the run's own
  numbers unreproducible — a measurement is superseded by a **newer
  measurement**, never by an edit. The new fixture is a new run, the old one got
  a forward pointer, and the live citations were repointed so no claim was left
  ungrounded.
- **The count was never the mental model** (2026-08-19). ADR-CLI opened with
  *"six verbs — three build the index and three query it"*, and two new verbs
  made the sentence false. The temptation is to re-count. The fix was to find
  the grouping the surface actually had (lifecycle / write / sources / read) and
  notice that **"no subcommand tree" was the real constraint** all along. **A
  record that states an arithmetic fact about itself will go stale; state the
  invariant instead.**
- **A reorganisation can silently undo a ruling** (2026-08-18). The
  one-archive rule was decided on 2026-08-10 and written in `archive/README.md`;
  the `work/` restructure eight days later recreated a second archive inside
  `work/` without anyone noticing the contradiction — including the
  session that wrote both files. **When restructuring, re-read the rules the old
  structure encoded**, and prefer a check over a memory.
- **A permissive parser hides a broken file** (2026-08-18). `fux.frontmatter`
  is permissive on purpose (OKF §9) and read a record whose YAML was invalid;
  every other tool in the world refused it. **Validate against the strictest
  consumer, not your own.** The check now uses fux's own quoting rule to
  predict what strict YAML will reject.
- **A rule in prose is a rule that gets skipped** (2026-08-18). "No behaviour
  change without its ADR" had been written in `CLAUDE.md` for weeks. Replayed
  over the 25 commits before the check existed, **13 of them** changed an
  ADR-owned component and updated no record. The fix was not better wording; it
  was `tests/test_adr_freshness.py`. **When a rule matters, ship the check in
  the same change as the rule.**
- **Features that are individually correct can be mutually exclusive** (2026-08-18). Hashed meta writes a 16-hex `title_h`; the accelerator refuses any index with a 16-hex token outside `terms`. Both decisions were right; together they meant the **default** URL path could never build an accelerator ([closed 2026-08-19](regression/2026-08-19-w54/report.md)). Each shipped in a different release with its own tests, and nothing exercised the intersection. **Test the seam between two features, not just each feature.**
- **Documenting a surface walks paths nobody walks** (2026-08-18). Writing
  ADR-CLI meant running every verb and flag, which immediately surfaced W-46 —
  `ask --hybrid` crashing on a source install. The guard for that exact case
  was written and dead: it caught `FuxError, ImportError, FileNotFoundError`,
  and the real failure is an `AttributeError` from a documented `None` return.
  It survived because it cannot reproduce where the model bundle is present,
  which is every machine here.
- **Capture output, never illustrate it** (2026-08-18). ADR-CLI's examples are
  verbatim from a container run against a committed fixture. The cost was one
  run; the return was a real bug and a set of examples that cannot rot silently.
- **A written file can vanish from the Cowork mount** (2026-08-18). One created,
  verified, and staged file was gone from the working tree an hour later while
  `git ls-files` still had it. Verify deliverables exist before finishing; a
  repo-wide link check is what caught it. See [`MACHINE.md`](MACHINE.md).
- **A link checker on macOS is not a link checker** (2026-08-18). The
  filesystem is case-insensitive, so `glossary.md` resolves locally and 404s on
  Linux. Verify case against the filename, not against whether the path opens.
- **The Cowork device bridge cannot delete files** (2026-08-18). `git checkout`,
  `stash` and `reset --hard` all fail there. On that surface there is no undo —
  a bad bulk edit is fixed by editing forward. Details in [`MACHINE.md`](MACHINE.md).
- **An ignore rule is the silent failure mode** of putting committed and derived
  planes under one dotdir. The repo's own `.gitignore` carried a `.fux/*`
  blanket that would have eaten `sources/` and `fetchers/` with no error —
  which is why `fux doctor` now asserts `git check-ignore` on the index.
- **Fetcher tunables are an opaque table.** Typing `cdp_port`/`settle_ms`
  into `config.py` would have breached the adapter cap through the back door.
  `[sources.url.config]` is passed verbatim and never read — PEP 518 `[tool.*]`
  discipline. Hold that line for every future fetcher.
- **A recorded rank is a snapshot of a corpus at a date**, not a property of the
  engine. Read every recorded rank with its date attached.
- **An unindexed source is not a ranking failure.** R2's third question failed
  because its citation target was outside configured sources — a config gap
  that looked exactly like a relevance gap.
- **A pre-registered threshold is only as good as the corpus that tests it.**
  Always report the fraction of the population a treatment actually touched; an
  aggregate delta of zero over an untreated population is not evidence.
- **Recompute statistics over the pruned index, never borrow them** — borrowing
  measures a system nobody will ship.
- **Wrap the archive; never edit it.** Look for an existing seam before
  concluding an archived module has to change.

---

# History — the succession record

*Everything below is the running exit-interview: each departing model's
judgement, in its own words, newest reset first. It is background. The four
sections above are the state of play.*

---

## ⚠ Read this first — the second reset (2026-08-09)

**Everything below this section describes the v0.19–0.26 engine. That engine
is archived.** It is history worth having — the judgment in it is real — but
it is no longer the state of play. Read this block, then read the rest as
*background*.

**Update (2026-08-10, Cowork/Claude):** one post-M1 capability landed at
Arpit's direction — URL ingestion through a **consumer-owned fetcher
file** ([ADR-URL-INGEST](../archive/adr/0010_url-source-consumer-middleware.md), ⏳ proposed;
a CDP template ported from the archived `render="cdp"` path, now at
`.fux/fetchers/cdp.py`). The judgment worth inheriting: the adapter cap
survives by making URL fetch *configuration plus consumer code*, never core
code — `src/fux/` still has zero network lines; hashed meta got its first
real exercise; offline ingest carries `url:` records forward byte-identically
because the writer's implicit-deletion rule would otherwise eat them.

**Update (2026-08-11, Claude Code):** `.fux/` is now a **declared layout**
([ADR-DOTFUX](../archive/adr/0011_fux-dir-layout.md), ⏳ proposed) — every child is
committed or derived, and the URL source moved fully inside it. Two pieces of
judgment to inherit. First, **an ignore rule is the silent failure mode** of
putting committed and derived planes under one dotdir; the repo's own
`.gitignore` already carried a `.fux/*` blanket that would have eaten
`sources/` and `fetchers/` with no error, which is why `fux doctor` now
asserts `git check-ignore` on the index. Second, **fetcher tunables are an
opaque table**: typing `cdp_port`/`settle_ms` into `config.py` would have put
one fetcher's vocabulary into fux's schema and breached the adapter cap
through the back door. `[sources.url.config]` is passed verbatim and never
read — the PEP 518 `[tool.*]` discipline. Hold that line for every future
fetcher. Maintainers of this doc so
far: each session's model, per the standing instruction above — this entry
by Claude (Cowork, claude-fable-5).

**Update (2026-08-12, Claude Code):** Phase 0 of the v0.32.0 open-items
program cleared the backlog; **R2 is 3/3 PASS**. Three pieces of judgment to
inherit. First, **an unindexed source is not a ranking failure** — R2-Q3 had
been "failing" since M1 for want of one line in `fux.toml`, and ADR-RECORD was
right to diagnose it and *decline to fix it*, because moving the archived doc
set was Arpit's call; the restraint is why the eventual fix was one line
instead of an argument. Second, **the fix bought a new problem and it was
filed, not solved**: the retired v0.26 docs now answer questions about the
current engine (*"what is the ingest cache"* → 5/5 archived results
describing a deleted subsystem), found post-hoc, filed as W-44 with a
recommended *shape* and no mechanism — five hand-picked probes on one corpus
is not grounds to ship a ranking change, and the v0.26 line already paid to
learn that. Third, **a recorded rank is a snapshot of a corpus, not a
property of the engine**: ADR-RECORD's Q2 "#1" became "#2" because `README.md`
grew a relevant table two days later, so recorded ranks now carry their date.
Also worth knowing: **`CLAUDE.md.proposed` does not exist** — the M0a rewrite
has been the live `CLAUDE.md` since `3892c55`, which makes "reject" a
~800-line revert rather than a no-op. Entry by Claude Opus 5 (1M context).

**Update (2026-08-12, Claude Code — M2):** the T1 accelerator shipped and
**R3 PASSED** (worst-case p95 27.2 ms vs a 150 ms bar). Four pieces of
judgment to inherit.

**First, the differential law is a property of the candidate set, not of the
arithmetic — make it so structurally.** Float addition is not associative, so
a term-major accelerator that accumulates scores term-by-term produces
different low-order bits than the doc-major scan and a different `--json`
payload while being *logically correct*. `query/rank.py` exists so both paths
share one scorer and one sort. Do not "optimize" scoring back into the
accelerator; that is the whole design.

**Second, a green safety test can be measuring the corpus rather than the
code.** The differential harness was written before the accelerator, as
required — and it was blind: replacing the block bound with a constant **zero**
still produced byte-identical output at `top=5`, because on a 124-document
corpus the rarest query term already decides the answer. Sweeping
`top ∈ {1,5,20,50}` caught it instantly. **Every safety mechanism here now
needs a test that fails when the mechanism is disabled.** This is M1's pruning
lesson in a new costume: an aggregate result over an untreated population is
not evidence.

**Third, the archive's warnings are worth reading before building, not after.**
The dense lane closed three named gaps and broke nine queries — including all
five no-answer queries. INTERVIEW item 5 below already states the mechanism: a
binary prefilter always has a nearest neighbour, so "No confident matches"
stops being reachable, and the archived calibration measured that no score
floor separates noise from a true rescue. Hybrid ships **default-off** on that
evidence. Do not flip it without a lane that can decline.

**Fourth, dogfooding has a self-reference trap.** Filing a conformance run's
raw CLI output into `docs/` put the query strings into the indexed corpus, and
all three frozen R2 questions were promptly topped by their own evidence
files. Dot-prefixing the dumps fixed it; the general gap is W-45. Entry by
Claude Opus 5 (1M context).

**Q: What changed?**

- The substrate engine (v0.19 → v0.26, ADRs 0001–0015) is **archived at
  [`../archive/v0.26/`](../archive/v0.26/)**, runnable but reference-only. Its
  docs are at [`archive/v0.26-docs/`](../archive/v0.26-docs/); the old plan at
  [`archive/v0.26-implemented/PLAN-v0.26.md`](../archive/v0.26-implemented/PLAN-v0.26.md).

- The replacement architecture is **index-and-refer**, specified in
  [`paper/the-fux-index-paper.md`](paper/the-fux-index-paper.md): rank from a
  small index committed to git; fetch content from the systems that own it;
  verify at answer time.

- **There is no `src/` on `main` by design.** The package scaffold is
  deliberately deferred until M1's pruning eval passes — see below.

**Q: Why reset a working, published engine?**

Because the thing it was good at was not the thing the design point needs. The
v0.26 engine's committed artifact grew with *content* (cache + state plane).
At a 10-engineer repo that is fine; at a 10k-engineer corporation's
mega-project — the litmus since 2026-07-21 — it is a copy of the company's
knowledge in a git repo, with the staleness, duplication and ACL-drift
problems that implies. Index-and-refer commits **statistics only**, so the
artifact stops scaling with content.

Two other facts pushed it: archived ADR-0011 recorded query-at-scale as
unfixed (postings stored but not read at query time — a 100k query loads the
whole index), and the substrate's storage/profile/state machinery had become
the majority of the code for a minority of the value.

**Q: What must a successor NOT re-litigate?**

1. **The reset itself, and the archive.** Do not port the substrate, the lean
   profile, the state plane, or the per-file cache back. The port list in
   [the ADR register](../docs/adr/README.md) §"What survives" is the whole of what comes forward,
   and it comes forward *with its tests*.

2. **"Index", not "db".** A council ruling. What Fux commits is an index —
   statistics that make documents findable. It does not hold content.

3. **Content is never durable outside its source** except under explicit
   per-source `snapshot` policy. This is the new law and the reason the
   architecture works.

4. **Hashed meta is the default** for non-git sources, enforced at write time.
   It closes an ACL leak; it is not a configuration preference.

5. **Six compare docs are closed** ([`compare/`](compare/README.md)):
   architecture, wire/runtime split, one MST keyspace, hashed meta, ARC cache,
   storage. Each carries its own reopen-trigger — fire the trigger or leave it
   alone.

6. **The adapter cap (git + HTTP + Confluence) is a decision.** MCP is the
   endgame and is [a proposal](proposals/mcp-adapters.md), not a backlog item.

**Q: What is the one thing that gates everything?**

**P1 — does KL top-k pruning preserve ranking quality?** If it fails, the
committed index cannot be small and the architecture is falsified. So M1 runs
*before* anything is built on it, including the package scaffold, against a
threshold pre-registered in the [handoff](../archive/v0.30-rev1-planning/v0.30.0-m0-m1-gate-handoff.md)
§5.4 and [paper §8](paper/the-fux-index-paper.md).

**Moving that threshold after seeing the numbers is the single worst thing a
successor can do here.** A recorded negative that saves months of building is
a *successful* outcome of M1, not a failure of it. The verdict lives in
[P1-GATE](regression/2026-08-09-pruning-eval/VERDICT.md).

**Q: Where is the state of play, mechanically?**

[`OPEN-WORK.md`](OPEN-WORK.md) — the single live tracker, an **index** of
open items since 2026-08-12 with detail in [`open/`](open/README.md) (`W-nn` items +
P1–P7 statuses). It replaced the archived IMPLEMENTATION.md. `PLAN.md` is the
*spec* per milestone id; OPEN-WORK is the *state*. Pick work there.

**Q: What of the old answers below still holds?**

The **process** and the **person**: compare-doc-before-building, one ADR per
feature with references, docs true in the same change, worklog every exchange,
name the model on every handoff. Arpit's working style (concise, recommendation
first, debate culture, minority reports preserved) is unchanged and is the most
useful thing in the rest of this document. The **design lens** is also
unchanged and still binding: *design for a very large-scale project inside a
corporation*, not for Anton — Anton is a convenient small testbed, not the
priority filter.

What does **not** hold: every module, command, config key and ADR number
mentioned below. Treat them as archived history.

---

**Q: In one breath — what is this repo?**

Fux. A `$0`, stdlib-only, deterministic knowledge engine: the *why* behind code,
written as version-controlled rules bound to the exact lines they explain, read by
agents before they touch anything, and checked deterministically — never by a model
— so the reason can't be deleted by someone confident and can't silently go stale.

**Q: What does Arpit actually want?**

His words, near enough: *"I want AI agents to develop based on documentation —
Jira, Confluence, ADRs — and never deviate from it. The references must be
accessible to agents. None of the rules gets broken."* Two refinements that matter:
enforcement must not stop at pass/fail — a blocking finding must *tell the agent how
to fix it* (the loop); and everything built must be usable first-hand in **Anton**
(AlphaForge, his trading app — Fux's pilot, "instance zero") before any external
claim. He dogfoods before he sells. Respect that ordering.

**Q: What's the state of play?**

This is a **from-scratch rebuild** (July 2026). The previous build reached ~0.18.0,
pursued the full vision at once (graph, recall, verify, MCP, memory, federation),
and did not work as a whole — it is preserved under `archive/` for reference only.
Package skeleton is up (src/ layout, hatchling, v0.19.0, CLI + FuxError stubs, smoke
tests). **Pivot (July 20):** the rule engine is *held*. The first thing being built
is a **CLI that answers natural-language questions over documents in a defined set of
folders** — Arpit's own idea for instance-zero utility. Three design forks are
written up as compare docs in `work/compare/` (engine, output format, ingest
strategy) and are **awaiting Arpit's verdict** before any build. The engine fork also
decides whether `$0`/no-LLM/deterministic still binds this tool — do not assume; read
`work/compare/query-engine.compare.md`. The old strategic layer (Fux Fleet,
federation, the deferred Plane) is *not* carried forward — reviving anything out of
scope requires an ADR and Arpit's sign-off.

A standing rule was set here: **whenever a decision has multiple viable options,
write a compare doc first** (debate + matrix + references + proposed verdict) and let
Arpit choose. It's now step 0 of the lifecycle in CLAUDE.md.

**Query-CLI decisions (accepted 2026-07-20, see `work/compare/`):** staged hybrid,
entirely `$0` with **no external model** — any smart component is *built and packaged
inside* the wheel at ≤10 MB, no required external deps. Engine: v1 BM25F → v2 bundled
static embeddings (Model2Vec/Potion-class, distilled offline, quantized) fused with
RRF → v3 agent-facing ask/reply/explain. Output: passages default, `--answer` is
**extractive** (bundled embeddings + TextRank), never generative — a ≤10 MB model
cannot write faithful prose, so we *select and order source sentences*. Ingest:
two-tier `fux ingest` (inferred default, advanced on demand / agent-triggered), a
manifest of inferred files, `fux.toml` mapping file types → source dirs. This is the
new "state of play"; the rule engine remains held. Later same day: **numpy resolved
out** (pure-stdlib inference; candidate-only ranking makes it fast enough); ingest
extended with per-file **traceability frontmatter** (the hand-rolled frontmatter
parser's first dogfood — the held core sneaks back in through provenance), a
library-first `fux.ingest` API + agent skill, and fenced link/attachment crawling.
CLI naming `fux ask`/`find`/`answer` — **accepted 2026-07-21**. Same day: CDP
rendered-page ingestion accepted (`render = "cdp"`, hand-rolled RFC 6455 WebSocket
client on stdlib, user's own Chrome — never bundle a browser); numpy-vendoring
disproven with evidence (C extensions, platform wheels — see packaged-model doc), so
pure-stdlib inference is final; and a new fork opened + proposed:
**agent integration** — `fux init-agents` generating AGENTS.md (the Linux Foundation
standard most agents read) + CLAUDE.md/copilot-instructions/`.kiro/steering/`
pointers, plus Claude Code `UserPromptSubmit` and Kiro hooks for enforced injection;
MCP noted as "better later," deferred behind an ADR. Agent-integration **accepted 2026-07-21** with a twist the research earned: skills are
now an open standard (Agent Skills / SKILL.md, 32+ tools incl. Copilot and Kiro), so
**one skill file replaces the old build's per-platform skillgen** — ship `fux-query` +
`fux-ingest` skills once. Setup: single **`fux setup`** (renamed from `fux init` at
Arpit's call; interactive wizard + full flag coverage + `-y`, idempotent). The last
sub-decisions were then **resolved with research** (see query-engine compare doc):
no bundled reranker — RRF only (cross-attention needs ~80 MB models, 8× over budget;
the Anton eval set is the only thing that can reopen this); chunking =
structure-aware heading-based, 256–512 tokens, code/tables atomic; BM25F = heading
3.0 / path 2.0 / body 1.0, k1=1.2, b=0.75, config-overridable. **Every fork and
sub-decision is now decided.** Late additions (2026-07-21, all accepted): ingest
covers images (metadata stub → OCR via Tesseract/Docling in the advanced tier), JSON
(stdlib-flattened), YAML (fenced text — stdlib has no YAML parser), txt; a
**maintained e2e suite** in `tests_e2e/` (real CLI + fixture corpus + golden files)
is part of definition-of-done; **`work/DOC-REGISTRY.md`** tracks every maintained
doc's update trigger + last-verified date, enforced by an advisory session-end hook
and by the generated agent instructions; and CLAUDE.md carries a standing rule to
**auto-fold durable session knowledge into itself** — its scope section now states
the full decided design. Process additions (2026-07-21): **proposal docs** (`work/proposals/` — parked ideas,
graduate when picked up), **implemented docs archive to `archive/`**, and —
significant — **OKF conformance**: Fux follows Google's Open Knowledge Format v0.1
(markdown + frontmatter bundles; required `type`; index.md; log.md; permissive
consumption). Fux's substrate was already OKF-shaped, so this is near-free interop
with every OKF consumer — and strategic validation that markdown+frontmatter
knowledge bundles are becoming the industry standard Fux bet on. Final layer (2026-07-21): **the git-corpus bet** — Arpit's framing, now design: the
ingest cache is a long-term, git-versioned knowledge corpus feeding product
development (validated by the Knowledge-as-Code pattern and Karpathy's LLM-Wiki
paradigm; no competitor versions knowledge). Deterministic diff-friendly cache
output is a hard requirement. Three proposals parked (research-to-spec,
knowledge-diff, audit-evidence-trail — the last is the Plane's seed). **Every finalized phase
has a ready build spec** in `archive/handoff/`: **0001** (v1 — local inferred-tier
ingest, BM25F, ask/find/answer, agent files, both suites), **0002** (v1.1 — web
crawl, CDP via hand-rolled RFC 6455, advanced tier/OCR; blocked by 0001), **0003**
(v2 — eval harness first, distilled ≤10 MB bundled model, stdlib int8 inference,
RRF hybrid; blocked by 0001, independent of 0002). Arpit chose **one continuous
run** (master prompt 0000) over the dogfood-gated sequence, with DOGFOOD.md
emitted after phase 1 so Anton dogfooding runs in parallel.

**Phase 1 shipped (2026-07-21, v0.20.0).** The full v1 surface exists and both
suites are green (108 unit + 21 e2e incl. byte-determinism goldens): setup wizard,
inferred ingest → OKF cache with provenance, heading chunker, true BM25F
(weight-then-saturate), ask/find/answer with --json/--explain, extractive TextRank
answers, AGENTS.md/skills/hooks generation. ADRs 0001–0004; 0001 pair archived.
Build judgment a successor should keep: determinism beat wall-clock provenance
(`converted_at` = SOURCE_DATE_EPOCH/mtime); JSON index won by measurement (16 ms
load at 5k chunks — postings build, not format, dominates); the e2e suite earned
its keep immediately (caught skipped-files-as-drift and answer noise).

**Phase 3 shipped — the master run is complete (2026-07-21, v0.22.0).** Engine
v2 per handoff 0003 (ADRs 0006–0007): eval harness first (the gate and the
reopen-instrument), re-packed potion-base-8M at 7.93 MB int8 (sha-pinned, MIT),
stdlib inference with *exact* tokenizer parity, (sha, fidelity)-keyed vector
cache, RRF k=60 over BM25F candidates only, `--lexical-only` byte-parity
enforced by the pre-v2 goldens. The gate passed as a tie on the fixture set
(0.762/0.952/0.833 both engines) — recorded honestly in ADR 0006 with the
rank-level rescues and the zero-candidate limitation; hybrid ships enabled.
What a successor should know: the fixture eval saturates at this corpus size —
**the Anton private eval (tests_e2e/eval/README.md) is the real instrument**,
and it is the recorded reopen trigger for both the reranker and
distill-our-own decisions. Final state: 172 unit + 29 e2e tests, wheel 6.98 MB
with the bundle. Next action: Anton dogfood via DOGFOOD.md.

**Phase 2 shipped (2026-07-21, v0.21.0).** Web/CDP/advanced ingest per handoff
0002 (ADR 0005): stdlib HTML→MD (hand-rolled wins the default for determinism),
guardrailed crawl (robots non-negotiable, sha dedupe with dual provenance,
byte-stable re-crawl), hand-rolled RFC 6455 + minimal CDP (user's Chrome only;
settle = fixed delay, networkIdle deferred to dogfood), `--advanced` Docling/
tesseract upgrades with (sha, fidelity)-keyed index reuse, and the network fence
now *enforced by a test* (query/index cannot import web/cdp/ws). Suites at
phase gate: 154 unit + 24 e2e (+1 gated skip). Next: phase 3 (handoff 0003 —
eval harness first, then the bundled model + RRF).

**Q: Late direction change (2026-07-21) — the design lens?**

Arpit retired the Anton litmus: **do not design in reference to Anton — design
for a very large-scale project inside a corporation.** Consequences: the
knowledge substrate (SQLite, one-kernel, graph) is the default next phase, not a
wait-for-pain contingency; enterprise inputs (proxy/SSO ingest, Windows fleets,
air-gap installs, access boundaries, audit) are design requirements; the
audit-evidence-trail proposal gains priority; and Fux's laws re-read as its
enterprise sales story ($0 = auditable supply chain, offline = no data egress,
deterministic = compliance-grade). Anton stays a convenient small testbed only.

**Q: Phase 4 — where does it stand (2026-07-22)?**

**Shipped: v0.23.0, ADRs 0008–0011, M1–M8 all green.** The substrate is real —
SQLite store, committed `fux.lock` + `.fux/state/`, one-kernel `retrieve()` with
explain/graph/path/cat, FuxVec dense-global, full/lean profiles, `db pull`.
Parity held: all six v0.22 goldens are byte-identical through the kernel
re-plumb, and `--lexical-only` still measures exactly 0.762/0.952/0.833.

The engine got measurably better, not just bigger: **hit@5 0.952 → 1.000, MRR
0.833 → 0.873**, because FuxVec's full-corpus scan removed the candidate-only
ceiling ADR 0006 had recorded as unfixable-by-design.

Three things a successor should know about *how* it went, because they are the
process working rather than luck:

1. **The escalation that mattered.** M3 hit a real conflict — DoD 7 promised
   *identical* cross-profile rankings, but lean could not recover corpus-level
   `df`. Rather than quietly redefining "identical", it stopped and asked. Arpit
   ruled: keep the guarantee, add an exact df sidecar. That ruling is why lean
   parity is provable today instead of plausible.
2. **A prediction that missed, kept next to the measurement.** An M3a
   extrapolation warned the state plane would blow its 30 MB budget (~35 MB).
   The 100k benchmark measured **23 MB**. The projection had used this repo's
   own docs, which are adversarial (very long ids, wide vocabulary). Both
   numbers are in IMPLEMENTATION.md on purpose.
3. **What phase 4 measured and did NOT fix.** At 100k, a query takes ~10 s: the
   query path still loads the whole index into memory to build the `Searcher`,
   and the `postings` table — populated and indexed at ingest — is never read at
   query time. **The substrate solved storage at scale, not query at scale.**
   That is the honest head of phase 5, scoped in ADR 0011. Do not let the
   "substrate shipped" headline hide it.

**Q: Phase 5 — where does it stand (2026-07-22)?**

**Shipped: v0.24.0, ADR 0012, M1–M6 all green.** Debug & observability: a
hand-rolled, stdout-safe emitter (`fux.debug`) behind `[debug]` in fux.toml
with `--debug[=LEVEL]`/`FUX_DEBUG` precedence; `dbg()`/`timer()` calls at every
pipeline stage; `fux doctor` (seven groups, exit 0/1, every failing check
names the fix command); `fux why` (single-document negative-result verdict,
reading its dense/graph evidence straight from `kernel.retrieve()` so it can
never disagree with a real query); a third skill, `fux-debug`, plus a
one-line escalation pointer in the other two.

The gate that mattered: **the stdout-purity test was written at M1, before any
instrumentation existed**, specifically so it would still be exercising real
call sites by M6 rather than trivially passing against an empty emitter. It
held through all five milestones without a single stdout leak — the discipline
(`dbg()` is a no-op until `is_enabled()` says otherwise, and every write target
is stderr or an explicit file) did what it was designed to do.

One deliberate scope line: `fux doctor`'s "Chrome for CDP" check is
binary-presence only, not a live port probe — `import socket` outside
`ingest/` trips the standing network-fence test, and that fence is worth
keeping over one doctor check's completeness. See ADR 0012's "owed" section.

**Q: Phase 6 — where does it stand (2026-07-23)?**

**Shipped: v0.25.0, ADRs 0013–0014, M1–M6 all green — but read the "owed"
paragraph before calling this "fixed."** The acme-payments run measured two
real defects: the superseded document outranks the current one in 9/12
planted pairs, and `answer` fabricates confidently on all 4 well-formed
out-of-scope questions. Both got a deterministic, no-model mechanism this
phase. Neither is a clean fix, and both compare docs' calibration/measurement
rules are why that's the *correct* outcome, not a shortfall:

- **Supersession: annotate, never reorder** (Option A, accepted over the
  fusion-down-rank alternative). `find`/`ask` carry `superseded`/
  `superseded_by`, ranking is byte-identical to before; `answer` prefers the
  resolved successor when both are in its retrieved pool. Measured recovery,
  not assumed: **5 of 12** stale docs actually carry a machine-readable
  marker, **3 of the 9** original inversions do, and at the `answer` level the
  fix **fully corrects 1** (settlement) and de-cites the retired doc in a 2nd
  without promoting the current one (a retrieval limit, not a supersession
  one) — the other 6 are unmarked and permanently unreachable without a
  model. See `conformance/2026-07-23-supersession-recovery/`.
- **The confidence floor was built, calibrated, and shipped *disabled*.** The
  compare doc's calibration rule required a `min_confidence` value clearing
  all five eval gates or an honest report that none does. None does: the
  acme corpus's unanswerable and answerable score distributions interleave
  (declining all 4 fabrications needs floor ≥0.25; zero false declines on the
  55 answerable pairs needs floor ≤0.087 — the interval is empty). Shipping
  any tested non-zero default would have declined real answers. **The
  measured 0/4-decline defect this phase set out to fix is not fixed in
  v0.25.0** — say that plainly to anyone who asks, rather than letting the
  phase's existence imply it was. See
  `conformance/2026-07-23-min-confidence-calibration/` and ADR 0014's F1/F2
  follow-up (an absolute, cross-query-comparable signal — e.g. dense cosine —
  is the real path to a working floor; this phase's sentence score is
  pool-relative and cannot separate the two populations).

Both measurements were delegated to a background Opus subagent reusing one
editable-install acme environment across three passes (calibration sweep,
then a follow-up resumed via the same agent for the supersession
re-measurement) rather than three separate setups — worth doing again when a
build needs real-corpus evidence at this scale.

**Q: Phase 7 — what changed on 2026-07-24?**

**Option B (the fusion down-rank) was reopened by Arpit, and the second corpus
is why.** The orbit-fulfillment run (an independently-authored
warehouse/fulfillment corpus, deliberately disjoint from acme's fintech
vocabulary) reproduced every acme finding — and sharpened the supersession one
into something the annotate-only verdict could not absorb:

- **8/12 inversions** (acme 9/12) — the reopen-trigger's ≥8/12 bar, met exactly.
- **The engine annotates the document it ranks first.** 6/6
  frontmatter-reachable superseded docs carry `superseded`/`superseded_by` in
  `find --json`, and **5 of those 6 still outrank their replacement.** Option A
  works precisely as designed and does not move the number.
- **Mechanism:** in 6 of 8 inversions the current doc **wins BM25F outright**
  (up to 2×) and loses on a dense edge as thin as **0.0006 cosine** that RRF
  flips. Dense systematically prefers terse obsolete docs — a long current doc's
  embedding is diluted. So a penalty usually needs to overcome a very small gap.

**What reopening does and does not authorise.** It authorises *building the
penalty default-off and calibrating it across four eval sets* — not shipping it
on. Default `0` stays byte-identical to v0.25.0, and flipping it needs a proven
safe interval plus a separate Arpit sign-off, because B changes `find` ordering,
which is the one thing A deliberately avoided. **"No safe interval exists" is a
valid, valuable outcome** — the same rule that made the confidence floor ship
disabled. A successor who finds the knob at `0` and "helpfully" tunes it to a
plausible value has broken the phase's central discipline.

**The two defects are coupled — that is the other half of the phase.** Orbit
also refuted the runner-up *margin* check (every unanswerable margin exceeded the
six smallest answerable ones — inverted, not merely empty). But the smallest
answerable margins came from documents tying with **their own superseded twins**.
Finding 1 was manufacturing Finding 2's false-positive mode, so the penalty
de-confounds the margin and earns it one clean re-measurement. If it still fails
after that, fabrication is a **documented permanent no-model boundary**, not an
open defect — and the honest move is to write it down, not to invent a third
mechanism.

**Outcome (phase 8, same day): it failed. Fabrication is now written down as a
permanent boundary, and v0.26.0 is live on PyPI.** The penalty shipped enabled at
15, and the calibration was confirmed **black-box from the published package**
(orbit inversions 8→3, hit@1 .566→.698, hit@5 flat) — not just in-tree.

**Q: What did phase 8 teach that isn't in the code?**

Two mistakes worth inheriting, because both were *confident and wrong*:

- **"0.25.0 is not on PyPI" was false, and it reached a filed conformance
  document.** `pip install` fails with *"no matching distribution found"* on
  Python **< 3.11** because the package declares `requires-python >=3.11`. That
  reads exactly like "never published." An entire frozen-wheel workaround was
  built on the misreading. **Check `python -V` against `requires-python` before
  concluding anything about a package's existence.**
- **A version string is not a build identity.** The first orbit re-baseline ran a
  wheel that said `0.26.0` but was built *before* the default flipped to 15 — so
  it recorded pre-release behaviour as the reference, silently and green. What
  caught it was reading the baseline diff and asking why a number that *should*
  have moved hadn't. **Assert the behaviour you changed, not the version.**

The general lesson under both: a green run that agrees with your expectations is
the easiest place to hide a wrong premise. Diff against what you predicted, and
investigate the metric that *didn't* move.

**Q: What must a confident successor NOT "clean up"?**

1. **The hand-rolled frontmatter parser + validator** (once built) — that is the
   zero-dependency guarantee. Do not swap in PyYAML/jsonschema.
2. **The `$0` law.** No maintenance path may ever call an LLM — not once.
3. **The single `FuxError`.** Flat by design; no exception hierarchy.
4. **The df sidecar** (`.fux/state/df/`). It looks like redundant statistics you
   could recompute. You cannot — it is the *only* reason lean rankings are
   provably identical to full rather than approximately so, and deleting it
   silently downgrades a guarantee to a hope. See ADR 0008.
5. **The early return when BM25F finds zero candidates.** It looks like it is
   blocking FuxVec's rescue path. It is not — it is what keeps "No confident
   matches" reachable, since a binary prefilter always has a nearest neighbour.
   Measured: noise scores 0.23–0.26 cosine against a true rescue's 0.34, so no
   floor separates them. This exact mistake was made and reverted during M5;
   ADR 0010 records why.
4. **The lifecycle.** plan → handoff → prompt, then one ADR per feature, every rule
   and ADR carrying a reference. This is how work is trusted here.
6. **`[answer] min_confidence`'s default of `0.0`.** It looks unfinished — a
   knob nobody turned on. It is not: v0.25.0's calibration measured that
   every tested non-zero value declines real answers on the corpus used to
   justify it (the unanswerable and answerable score distributions
   interleave). Do not "fix" this by picking a plausible-looking default
   without new calibration evidence — that is the exact failure this phase
   exists to prevent. See ADR 0014.
5. **Anton first.** Built for and lived-with in Anton before any external claim.

**Q: How does Arpit like to work with a model?**

Concise and direct — minimum words, and he means it. Recommendation first, one call,
defended in a sentence; a decision, not a menu. He runs a debate culture:
significant plans get a devils-advocate or full council pass *before* building, and
he takes minority reports seriously — preserve dissent, don't absorb it. He extends
an idea mid-conversation with one short sentence and expects you to catch that it
reshapes the design. Litmus: "is it relevant to Anton?"

**Q: What does the repo demand of you mechanically?**

CLAUDE.md is binding: every code change updates PLAN.md (design of record), the
README, this document, the relevant ADR, and every other doc it touches — a change
is not done until the docs are true. Every behaviour change ships with a test.
`uv run pytest -q` green. Python ≥ 3.11, match the surrounding style.

---

*Maintained by: Claude Opus 4.8, July 2026 — reset the record for the from-scratch
rebuild; scoped to rules substrate + fix loop; carried the succession premise
forward. · Claude Fable 5, 2026-07-21 — executed the full master run: v1 query
CLI, v1.1 web/CDP/advanced, v2 hybrid engine (v0.20.0 → v0.22.0, ADRs
0001–0007); recorded the build judgment above; the Anton eval is the successor's
compass. · Claude Opus 4.8 (1M context), 2026-07-22 — built phase 4, the
knowledge substrate (v0.23.0, ADRs 0008–0011): escalated the DoD-7 conflict
rather than redefining it, mutation-tested the parity claims that resulted, and
recorded what the 100k benchmark exposed but did not fix (query-at-scale).
· Claude Sonnet 5, 2026-07-22 — built phase 5, debug & observability (v0.24.0,
ADR 0012): the emitter, `fux doctor`, `fux why`, and the `fux-debug` skill; kept
the stdout-purity gate green from M1's empty emitter through M6's fully
instrumented pipeline.
· Claude Opus 4.8 (Cowork), 2026-07-22 — ran the fux-lab conformance scaling
curve (1k→5k→10k, 0.23.0) and filed it into `work/proposals/hybrid-degrades-at-scale.md`.
Finding: the 1k "hybrid 4× worse" gap is not stable — it closes with scale as
lexical collapses toward hybrid; leans corpus-artifact (B) but does not settle
A vs B (same generator). Query latency is linear from the start, corroborating
ADR 0011's query-at-scale limit. No engine change made; acme-payments remains
the discriminating next run. Direction unchanged.
· Claude Sonnet 5, 2026-07-23 — built phase 6, trust & currency (v0.25.0,
ADRs 0013–0014): supersession parsed/persisted/annotated (never reorders;
`answer` prefers current when both are in pool); confidence floor built,
calibrated against all five gates via a background Opus subagent, and shipped
disabled — no value clears both the unanswerable and answerable gates.
Delegated both real-corpus measurements (calibration sweep, then supersession
recovery) to one resumed background agent sharing an editable-install acme
environment rather than three cold setups. Both proposals graduated to
`archive/` with their ADRs; the honest finding that the fabrication defect is
*not* fixed in this release is recorded here and in ADR 0014 on purpose.
· Claude Opus 5 (1M context), 2026-08-09 — wrote the reset block at the top of
this document and gave GLOSSARY its v0.30 vocabulary; committed the archive
move as its own commit so the reset and the work on top of it stay separable.
Executed M0a/M0-ADR and built M1's gate (the KL selector + eval harness) with
the threshold pre-registered before any number existed. The judgment worth
inheriting: the harness recomputes `df`/`n`/field lengths **from the pruned
postings**, because borrowing the baseline's statistics would have measured a
system nobody is going to ship.
· Claude Opus 4.8, 2026-07-24 — phase 7 M1: Arpit **reopened Option B** on the
orbit corpus's evidence (8/12 inversions; 5 of 6 annotated docs still outranking
their replacement). Amended the supersession compare-doc verdict — A stands, B
authorised **default-off only**, default flip gated on a proven safe interval +
separate sign-off. Penalty form decided as a **rank offset before fusion**
(scale-free sweep unit) in `[engine.hybrid]`; both deviations from the handoff's
letter recorded in IMPLEMENTATION.md.
· Claude Opus 4.8, 2026-07-24 — phase 8: **published v0.26.0 to PyPI** (PR #44,
merge `5ccd0a6`, 11/11 CI green), with both README honesty edits landing *before*
the release so the published page never carried the old "cannot hallucinate"
claim. Verified black-box from PyPI: the phase-7 penalty reproduces exactly
(orbit inversions 8→3, hit@1 .566→.698). Corrected two filed mistakes — 0.25.0
*was* on PyPI (a Python-<3.11 install failure had been misread as unpublished),
and a `0.26.0` wheel predating the M5 default flip nearly pinned pre-release
behaviour into orbit's baseline. Fixed the `zero_overlap_rescued` miscount
(clean rescues only) and left **Part C — non-monotone fusion — untouched and
scoped**, as its own Opus handoff.
· Claude Opus 5 (1M context), 2026-08-12 — Phase 0 of the v0.32.0 open-items
program: paid the archive-law debt, **closed R2 at 3/3 PASS**, and packaged
five ratification decisions. Recorded the post-hoc retired-content finding as
W-44 rather than fixing it, and corrected two things the tracker had wrong
(`CLAUDE.md.proposed` never existed; ADR-RECORD's recorded rank had drifted).
· Claude Opus 5 (1M context), 2026-08-12 — built M2: the T1 accelerator,
the differential law, bounded skipping, the dense lane and RRF (default-off on
measured evidence). **R3 PASS.** Mutation-tested the differential harness and
found it blind at the default `top`; fixed the harness rather than trusting
the green run.
(Add yourself here when you make a material update — model, date, one line.)*
