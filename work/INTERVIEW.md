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

*Updated **2026-08-27**.* **Ground it before you edit it** — `git log`, `git tag`,
[`IMPLEMENTATION.md`](IMPLEMENTATION.md), [`regression/`](regression/README.md).

### The most recent change: P3 passed, and a decoy caught fux believing itself (2026-08-27)

**One gate closed, one defect found, and the finding matters more than the gate.**

**W-87 P3 is `PASS`** — 19/19 sanitized shas unchanged across two `fux update`
runs over 19 real documentation URLs, against a frozen `≥ 80 %`. **Fork 3's gate
clears and W-87 P4 is unblocked.** ⚠ *Cleared is not decided*: the fetcher
contract's fifth function is still Arpit's. ⚠ The spec **named no interval**, so
at 12 s apart this measures server-side determinism, not document churn.

**W-82 has zero open forks of its own** — re-derived against the code: 27 total,
18 ruled, 8 moved to W-87, 1 answered by the build. What is left under W-82 is
ruling 3, which is a judgement.

**🔴 Read this before ruling R10.** Two of ADR-RS decision 15's three controls
were built (`tools/quality-controls/`), and **the decoy set found a defect on its
first run**:

> *"What is the SLA we publish for the payments API"* → `band: grounded`,
> `coverage: 1.0`, `missing: []`, `separation: 0.58`, citing the data-retention
> policy. **No document in the corpus discusses it.**

- **`coverage` and `missing` are CORPUS-WIDE.** The four terms occur in four
  *different* documents, so nothing reads as missing, both fact-based band
  clauses pass, and the band falls through to `separation` — which it clears.
- ⚠ **No ruling on R10 closes this.** `0.58` is above the `0.5` R10's selection
  rule would have picked. **The two decisions should be read together**, and the
  case argues `separation` measures **decisiveness** rather than groundedness:
  a corpus of near-misses is decisive about its best near-miss.
- **Named, not fixed**, and **deliberately unpinned by any test** — pinning a
  defect is how it becomes the contract. ADR-CONFIDENCE decision 12.

**ADR-RS decision 15 keeps its `NOT BUILT` marker.** It names three controls; the
**sealed subset** is the one left, and it is blocked on a judgement rather than an
environment — decision 15 says sealing *shrinks* the visible set and whoever
builds it must resolve that tension rather than inherit it. On 50 goldens both
halves end up too small.

⚠ **And the blocker on all of P1 was false again** — *"needs `fux-playground`,
not on the build machine"*. It was on the machine; two of three were built within
the hour. **That is the third time in two sessions that a recorded blocker
evaporated on contact with a shell.**

---

### Before that: the daemon over the real internet, and R10 (2026-08-27)

**Read this first if you are picking up cold: a whole section of the queue was
false, and the reason generalises.**

`OPEN-WORK.md` was headed *"Blocked on an environment that does not exist on the
build machine"* and listed six items. **Both environments were on the machine
the whole time** — `~/my_programs/fux-lab` and `~/my_programs/fux-playground`,
the latter still holding its 50 goldens and grading 41/50. The section was
written by sessions that had no shell and could not look. **It had been holding
R10, the confidence plane's gate.**

⚠ **Rule 4 — re-derive, do not read — is not advice.** Two consecutive sessions
now have found the queue's own blockers to be stale or false the moment a shell
was available. **Check before you believe a blocker.**

**The daemon is done, against real external URLs.** Seven of them, chosen to
cover exactly what localhost could not: TLS, DNS, two CDNs, a real `404`, a real
`429`, and **Wikipedia's `Special:Random`** — content that genuinely differs
between fetches, on a server nobody here controls.

- **The URL tail closed unassisted**: `16:51:55Z` *Laurence Bennett* →
  `16:52:55Z` *Bargilt Iron Ore Mine*, one sweep interval, no command typed.
  That is the whole substance of W-82 ruling 3.
- **The rate-limit path fired for the first time ever** against a real 429 —
  `fux doctor`: `rate-limited by httpbin.org x8`.
- ⚠ **Proxy and SSO remain uncovered** and need a corporate network. **Ruling 3
  is now held on a JUDGEMENT, not on evidence** — the recommendation is that it
  may land, and the call is Arpit's.

**R10 ran and is `INCONCLUSIVE` — for a reason worth internalising.** Not
because 50 queries are thin, though they are. **The pre-registration froze two
rules that disagree on the curve the data actually produced**: it reaches
`t = 0.75` at `separation 0.3`, falls back at `0.4`, then rises. Its selection
rule picks `0.5`; its verdict table's non-monotone row picks *no change*.

- **Handed to Arpit, not adjudicated.** ⚠ **Picking `0.5` would be the
  moving-threshold failure in its most natural costume** — a defensible reading
  of a frozen sentence that quietly discards the row saying not to.
- **`SEPARATION_FLOOR` stays `0.10`, and no test was edited** — the confidence
  test asserts the rule relative to the constant and never its value, a guard
  built for exactly this moment and working.
- **The correction lives in [ADR-RS](../docs/adr/0036_predictions.md) decision
  18, never in the frozen file** (W-82 ruling 8).

**Three defects, all the same shape: an error message that sends the reader
somewhere there is nothing to find.** A URL skipped as *"no decoder for
application/json"* while `jsondoc` is built in and ran; consumer decoders never
reaching URL content because `decode()` was called without `root`; and
`shard missing/mismatched _format header`, which is what an **engine upgrade**
produces and which named neither version nor the way out. **If you are adding an
error path, say what was found, what was expected, and what to do.**

---

### Before that: the backlog cleared, and the checks were checked (2026-08-27)

**A session with a shell.** Four Cowork sessions had run without one
(`device_bash` 5/5 since 2026-08-26), so the queue had accumulated seven
decided-but-unexecuted items — and, less visibly, had **never been able to run
the test suite it was reporting on**.

**The first finding is the one to carry forward.** `OPEN-WORK.md` said *"two ADR
tests are RED right now."* **Twelve were**, in five groups. The queue was
accurate about what it had seen and blind to everything else, which is exactly
what `CLAUDE.md` §Two hazards describes: **a doc repeating a doc is not a second
source.** If you arrive with a shell and the queue was written without one,
**run the suite before you believe anything.**

**What closed.** Five hands items (plus two `BLOCKED.json` named that the queue's
table did not) — two `git rm`, six `git mv` into `archive/`, every ADR-ENRICHED
citation repointed. `tests/` went **2 158 passed / 12 failed → 2 170 / 0**, and
`tests_e2e/` ran on **macOS** for the first time (74 passed, 1 skipped).

**Three of the twelve failures were defects in the checks, not in the code**,
and they are the durable part:

1. **The ADR register's §"the number line is contiguous" note was FALSE.** It
   described a renumber of `0026`+ down by one that never ran — and **must never
   run**: W-82 ruling 7 forbids compacting a vacated ordinal, having already
   watched one put two records on `0022`. The note cited
   `0025_runtime-manifest.md` and `0042_locks.md`; **neither file has ever
   existed in this repo.** ⚠ **If you read a doc claiming the numbering is
   contiguous, it is stale.** `0017` and `0025` are burned, deliberately.
2. **`tests/test_adr_freshness.py` convicts history unless it is stopped**, and
   its own docstring claimed it never did. It ran here for the first time and
   flagged eight commits against records written the same day. Now the register
   is parsed **per commit** (`git show <sha>:docs/adr/README.md`) — ADR-OWNERSHIP
   decision 9. **`RULE-SINCE` did NOT move**; the standing precedent was to
   retire ~95 commits of auditability to excuse eight, twice before.
   **A fourth entry on `RULE-SINCE` means this fix failed.**
3. **A frozen pre-registration with no report is a legal state** —
   `pre-registered, not yet measured`, ADR-RS decision 17. R10's directory failed
   four checks for correctly following the method: commit the threshold first,
   measure when the environment exists.

**The daemon is proven, and the hold on W-82 ruling 3 is NARROWER — not lifted.**
Full lifecycle against a local HTTP server: a page edited at `15:11:21Z` was
indexed by `15:12:04Z`, unassisted, one `sweep_minutes` later; `stop` reaped the
pid and freed the lock
([capture](regression/2026-08-27-daemon-lifecycle/report.md)).

- **The check is a positive control**, not a status read: the indexed term exists
  only in the fetched page. That matters because the unit gate patches a mock,
  and **a mock cannot tell "the sweep called ingest" from "the sweep called the
  mock"** — which is precisely how the dead sweep hid for a day.
- ⚠ **Localhost is not the network.** No proxy, TLS, SSO, rate limit or DNS.
  Narrow-by-default's blast radius is *URLs that stop being swept*, so the
  recommendation is that **ruling 3 stays held** until one real external URL has
  been swept. **That is Arpit's call.**

**One queue claim was wrong and measurement is how it was caught.** *"Four hook
tests go green-by-vacuity without `fux` on `PATH`"* → re-run with
`PATH=/usr/bin:/bin`: **4 failed, 9 passed.** Exactly **one** was vacuous, and it
is the one whose every assertion is that something is ABSENT. **Prefer measuring
a claim about the test suite over reading one.**

⚠ **L8's one-line handle was stale in four live docs** — including this one and
ADR-LAWS' own §1 table — all carrying the form Arpit **withdrew the same day he
wrote it**. Reconciled. **That is a reconciliation, not a ratification**: the L8
sanity-check is still open and still his.

---

### Before that: the skip list is COMMITTED, in `.fux/.fuxignore` (W-93, 2026-08-27)

**Read this before touching ingest: `fux ingest` now writes a committed file
that is also its own input.** Two delimited blocks at the top of
`.fux/.fuxignore` hold every path the run did not index and why;
`.fux/runtime/skipped` is deleted on every run. Ruled by Arpit on 2026-08-27.

**How it stays safe.** The blocks are written **first**, above every
hand-written line — last match wins in this file, so a block written last would
silently beat a `!` somebody wrote. A block line is a **literal path**, never a
glob. **Which block a line sits in is its class**, so the `not indexed` /
`skipped` split survives a round trip with nothing parsing note text. The note
is **the reason that put the line there**, so the second run does not answer
*why* with *"because the first run said so"*. And **a hand-written pattern
suppresses the generated lines it covers** — `__pycache__/` and `*.py[cod]`
collapse 257 of this repo's 599, leaving 342.

⚠ **The cost, and it is not a bug to be fixed: a generated line DECIDES, so it
FREEZES.** Widen `.fux/sources/types` and the listed `.py` files stay out. Write
content into a file listed as `empty` and it stays out. **Arpit was told this
before he chose it and chose it anyway** — it is what "put the list in
`.fuxignore`" means, and the alternative is a file whose name is a lie. It is
made **loud**, not undone: `gitdir.would_index` re-checks every generated line
each run and warns on stderr, naming the edit that fixes it. Do not "fix" the
freeze.

⚠ **Two losses, recorded rather than worked around.** A URL has no
repo-relative path, so **W-88's report-once promise now covers files only** and
a URL skip prints on every networked run. And a new skip **dirties the working
tree** on the hook path; an unchanged run writes nothing, so steady state is
quiet.

**The process lesson is bigger than the change.** The first pass of this item
read the request as a diagnosis to verify, verified it, found it wrong, and
shipped something else that was correct and beside the point. **Checking was
right; substituting was not.** See §4.

### Before that: `fux ingest` counts what it did not index in TWO numbers (W-93 pass 1, 2026-08-27)

**Small change, and the reason it is at the top is the reasoning, not the size.**
Arpit saw `ingested 632 docs …, 599 skipped` on this repo and said the skipped
files *"should get added into `.fuxignore`, not skipped"*.

**Reading the walker first is what saved it.** `gitdir.walk_sources` records an
**ignored** file as skipped too, so moving 599 paths into `.fuxignore` would have
changed the reason string and left the count at 599. And per-file lines would
have frozen a **derived** verdict — `not an indexed file type` comes from the
type allowlist, and `.fuxignore` **outranks** the allowlist, so 274 frozen `.py`
paths would silently survive the day a `.py` decoder lands.

**The defect was the count, not the files.** 598 of the 599 were the allowlist
doing exactly its job; **one** was a `binary` fixture worth a look. One number
over two populations is a number nobody reads by the second run — the same
failure W-88's skip notice was written for, arrived at from the other side.

**So [ADR-INGEST](../docs/adr/0007_ingest.md) gained decision 15:** a skip
carries its class — `POLICY` (a committed list said no) or `UNREADABLE` (fux
opened it and could not read it) — **assigned where the skip is made, never
parsed back out of the reason string**, and the summary counts them separately.
`--list-skipped` and `.fux/runtime/skipped` are deliberately unchanged, because
things pipe them.

⚠ **The open fork this surfaced, and it is Arpit's:** fux's walker reads **no
`.gitignore`** and has no prune, so it enumerates 257 untracked `__pycache__`
artifacts on every run. Making `.fuxignore` prune the walk saves real work
**and** collides with reported-never-silently-dropped. Not filed as a `W-nn` —
the queue is human-blocked and this session was not going to invent scope.

### Before that: there are EIGHT laws now — `L8` (2026-08-27)

**If you read one thing before touching this repo: the law count changed.**
Ruled by Arpit on 2026-08-27, closing W-89.

> **L8** · *A use record never leaves the machine.*
>
> ⚠ **This handle changed on 2026-08-27, the day L8 was written**: it read *"What fux retains about use is hashed, bounded, and local"* until Arpit reverted the hashing, the size bound and the stdout prohibition hours later. Plaintext queries and answers are legal; what survives is the confinement. Read the law at its one home, `CLAUDE.md` §Non-negotiable constraints.

- **Every one of L1–L7 governs what fux does to documents.** L8 is the first law
  about what fux retains of *people using it*. L2 governs **corpus content**, and
  a query is not content however precisely it describes one — that was the gap.
- **Normative text is `CLAUDE.md` §Non-negotiable constraints**, as always. The
  handle, the reasoning and the limits are
  [ADR-LAWS](../docs/adr/0001_laws.md) **decision 8**. Both changed in one commit,
  which ADR-LAWS decision 4 requires — **if you find them committed separately,
  that is the defect, not a style question.**
- **L8 forbids nothing fux does today.** Verified against the code *before* the
  text was written: `maintain/lastcited.py` hashes the query key
  (`sha256[:16]` of the normalised text), bounds the store at `MAX_QUESTIONS = 256`,
  writes into gitignored `.fux/runtime/`, never raises, and reports on **stderr**
  so stdout stays byte-identical.
- ⚠ **The thing most likely to be misread.** L8 does **not** make the use record
  private. `last-cited.json` maps each hashed key to the locators that answered
  it, so it still says *which documents are asked about and how often*. Those
  locators are already in the committed `M/` plane — the file adds **frequency,
  not new exposure**. Grounded in the 2006 AOL search-log release, where
  de-identified queries still identified a named individual.
- ⚠ **Why this was a law and not one more ADR decision.** The prohibition already
  existed as [ADR-QUALITY](../docs/adr/0044_quality-contract.md) decision 11 — and
  an ADR is a thing another ADR may supersede. Meanwhile
  [`proposals/ranking-tuning.md`](proposals/ranking-tuning.md) §8 calls a per-repo
  query log *"an asset fux gets for free"*. **The pull toward building one is
  documented and growing**, which is OPEN-WORK rule 6's damage-that-accrues.

**W-89 is closed** — outcome in [`IMPLEMENTATION.md`](IMPLEMENTATION.md). ⚠ Its
detail file still needs a `git mv` into `archive/open/`; no shell was available,
so it is stamped `status: ruled` and filed with the other stray-file `git`
operations in [`OPEN-WORK.md`](OPEN-WORK.md).

---

### Before that: the record set was rewritten — metadata once, and no record carries history (2026-08-27)

**Arpit's instruction, and it reshaped all 45 records plus
[`TEMPLATE.md`](../docs/adr/TEMPLATE.md) and
[the register](../docs/adr/README.md).** Three parts, none cosmetic:

1. **Frontmatter is stated once.** Ten keys in a fixed order —
   `type · name · title · description · status · date · feature · owns · laws ·
   timestamp` (`supersedes`/`ratifies` optional) — and **the body opens at §1.**
   The `- **Name:** / **Status:** / **Date:** …` bullet block that every record
   also carried is deleted. Two hand-written copies of one fact drifted, which is
   what it was always going to do.
2. ⚠ **`Amended` is abolished, and this is the load-bearing part.** A correction
   is now a **rewrite of the sentence it corrects, in place**. An amendment
   appended below leaves the false sentence standing *above* its own correction,
   and **an agent reads top-down and acts on the first answer it finds** — the
   W-83 failure, attacked at its source.
3. **History is gone; arguments stayed.** W-nn narrative, dates and superseded
   prose removed. Rejected alternatives, the ⚠ silent-failure warnings and
   measured evidence all kept — **the failure is the argument, the date it
   happened is not.**

**Four things a session arriving cold will otherwise get wrong:**

1. ⚠ **THE SUITE HAS NEVER BEEN RUN AGAINST ANY OF THIS.** The bash sandbox died
   mid-session and did not recover. Every consistency claim — key order, owns
   agreement in both directions, the Mermaid/ASCII pairing, chart `source:` lines
   — was **derived by reading the tests and grepping the tree**. Run
   `uv run pytest -q tests` before trusting a word of it.
2. ⚠ **Three tests are red, and all three have one cause.**
   `docs/adr/0043_confidence.md` is a stale duplicate of `0045_confidence.md`
   (same `name:`; `0043` is also ADR-LOCKS). ✅ **Arpit ruled 2026-08-27: keep
   `0045`** — the concurrent-session reason for leaving it in place is
   discharged. `git rm` it and all three go green. **Do not "fix" them by
   reordering the register** — `register_names()` is keyed by name, so
   reordering only moves which of the two files reads as unlisted.
3. **Do not re-add an `Amended` block, and do not restore a record's history
   from git when you find prose missing.** It was removed deliberately, under an
   explicit instruction. `tests/test_adr_frontmatter.py` will fail you, but the
   reason matters more than the check.
4. **`Owns (on acceptance)` no longer exists.** A record that owns nothing
   declares `owns: []`, whatever its status. The conditional form let a record
   assert a claim the register did not grant and call the disagreement
   intentional.

⚠ **It crossed `BLOCKED.json`, and landed two of the blocked rulings by
accident.** That blocker says W-82 rulings **1, 4, 6, 7** are stuck on
`docs/adr/README.md` being held uncommitted by the concurrent session — and this
pass rewrote that file. **Ruling 1** (ADR-MCP / ADR-ENRICH / ADR-RERANK →
`accepted`) and **ruling 7** (ADR-CODES-TABLE out of the register, archived,
ordinal burned) are now **landed**; *flip where the code exists* and the archive
law produced them independently. **Rulings 4 and 6 are not landed** — the
`describes` column, and ADR-ENRICH superseding ADR-ENRICHED — and both apply
cleanly on top of the new register. **Do not let a second session claim 1 or 7
as still outstanding.**

**Also:** `0025_codes-table.md` moved to `archive/adr/` **with no successor** —
its subject (`codes.jsonl`, the dense lane) was deleted, and that closes the
2026-08-25 finding that the status vocabulary has no value for *a record whose
subject ceased to exist*. **The answer was archival, not a fourth status.**

### The change before it: fux states how much it believes its own answer (2026-08-27)

**[ADR-CONFIDENCE](../docs/adr/0045_confidence.md) (`0045`, ⏳ proposed) is the
runtime half of the quality contract below.** Every answer now carries four
signals (`coverage` idf-weighted · `separation` · `verified` · `support`), a
`band`, and an `answerable` boolean — on `ask`/`find`/`answer` in `--json`, on
**stderr** in text mode, and on the `fux_search` MCP result. State is
[W-90](open/W-90-the-confidence-plane.md).

**Five things a session arriving cold will otherwise get wrong:**

1. ⚠ **`SEPARATION_FLOOR` is a PROXY, not fux's own threshold.** ADR-QUALITY
   decision 6 froze `t = 0.75` hours earlier; two abstention thresholds
   governing one decision is drift. **R10 must find the `separation` at which
   `P(correct) = t`.** If you find yourself picking a floor because it makes
   bands look sensible, stop — that is the thing decision 6 forbids.
2. ⚠ **`separation` is ORDINAL and Chow's rule assumes a calibrated
   probability.** The record states that gap rather than closing it. R10 closes
   it or says plainly that the floor is a heuristic standing in for a
   probability nobody computed. **Do not close it by inference.**
3. ⚠ **`support` is bounded by `--top` and CANNOT become a corpus-wide count.**
   The accelerator skips documents it proved cannot reach the top `k`, so a
   corpus-wide number would differ between `--fast` and `--scan` — a
   differential-law break. This is a constraint, not an oversight; it was found
   while building.
4. ⚠ **`ask` and `find` can only ever report `verified: unverified`.** They
   fetch nothing. Reporting `current` because the index is internally consistent
   is the exact collapse the refer plane's four-state verdict exists to prevent.
5. ⚠ **The suite is NOT verified green and no baseline exists.** 59 failed /
   1811 passed / 8 errors on the last clean run; 38 new tests green in
   isolation; the sandbox died mid-verification.
   **`tests/derive/test_weighted_bound.py` is in the blast radius.** And two
   **stray misnumbered files** — `docs/adr/0043_confidence.md`,
   `work/open/W-89-the-confidence-plane.md` — are still on disk and must be
   deleted. ✅ **Ruled by Arpit 2026-08-27** (keep `0045`/`W-90`); the removal is
   two `git rm`s nobody has run yet, not an open question.

### The change before it: the quality contract is declared (2026-08-27)

**Fux now says what a quality number means, for the first time.**
[ADR-QUALITY](../docs/adr/0044_quality-contract.md) (`0044`, accepted) ratifies
W-87 Phase 0 — all six forks, on Arpit's ruling.

**Four things a session arriving cold will otherwise get wrong:**

1. ⚠ **The cost of an error is FROZEN and may never be re-set.** `t = 0.75` →
   `c = t/(1-t) = 2`, in [`tools/quality/mix.toml`](../tools/quality/mix.toml).
   It was committed **while `recall@k` is still uncomputed**, which is the only
   ordering under which it means anything. **If you find yourself adjusting `c`
   because a number came out badly, stop** — that is veto condition 3 and it
   voids decision 6.
2. ⚠ **`nDCG` is a diagnostic here, not the headline, and it is not a style
   preference.** Two conditions hold in fux — a reranker discards the retriever's
   ordering, and LLM attention is U-shaped — so a decaying discount asserts a
   value curve the consumer does not have. If either condition stops being true,
   veto condition 1 fires and the classical metrics come back.
3. ⚠ **`recall@k` — the declared headline — is NOT COMPUTED.** Neither is the
   `unanswerable` class, which does not exist and **must be authored blind**.
   The contract is a declaration, not an instrument; `tools/quality/` is read by
   nothing.
4. ⚠ **W-87's fork 6 ruled "no query log" and deliberately did NOT rule whether
   L2 reaches one.** That gap is [W-89](../archive/open/W-89-does-l2-reach-a-query-log.md).
   Do not close it by inference from ADR-QUALITY decision 11 — the record
   explicitly declines it.

**The queue is three items** — W-82, W-87, W-89 — and the *Blocked on Arpit*
inbox is no longer empty. ⚠ It said `Empty` for a day while W-87 existed as a
detail file with no index row.

### The change before it: W-86 closed — the decoder plane, complete (2026-08-26)

**Fux reads thirty extensions now, not six.** Sixteen built-in decoders, all
stdlib, no dependency added; `fux setup` copies them into `.fux/decoders/` and
**the copy is what runs**. Consumer decoders may bring dependencies the runtime
may not — [ADR-DECODE](../docs/adr/0042_decode.md) is the record, and the
detail file is archived at
[`archive/open/W-86-the-decoder-plane.md`](../archive/open/W-86-the-decoder-plane.md)
(named, never cited).

**Four things a session arriving cold will otherwise get wrong:**

1. ⚠ **The enrichment queue is written and nothing reads it.** That is **fork
   G**, deliberately open — `fux enrich` derives scope from a declared `dirs`
   line, and a decoder returning `None` is a *discovered* need. Different
   origins; merging them amends an accepted record. It is not a bug.
2. ⚠ **`DEFAULT_TYPES` is derived from BUILT-IN decoders only.** A default that
   grew when a consumer dropped a `logdoc.py` into `.fux/decoders/` would mean
   **adding a decoder silently starts indexing a new file type**. Pinned by a
   test.
3. ⚠ **A bare `str` from a fetcher is still accepted**, as a transition ramp.
   The P8 break was **never re-costed** — ADR-FETCHER's *"no external
   consumers"* is dated v0.32.0 and predates the PyPI release. Removing the
   ramp without measuring is removing the thing that makes the break survivable.
4. ⚠ **Markdown is ratified as the decoder intermediate, with no reopen
   trigger.** A future session proposing a structured `headings` field on
   `ParsedDoc` is reopening a decision, not filling a gap.

**Three forks moved into the archive with the item** — F (a docstring decoder
for source files), G (above), I (`fux decoder` as its own verb). Each returns
as a **new item with a new id** if wanted.

### The change before it: W-86 filed — the decoder plane (2026-08-26)

**No code moved. Three findings did.** Arpit asked whether fux could interpret
PDFs, decks, spreadsheets, JSON and YAML;
[W-86](../archive/open/W-86-the-decoder-plane.md) is the plan, and
[`compare/index-lock.compare.md`](compare/index-lock.compare.md) is the lock
fork he told the session to research and call itself.

1. **The decoder plane already exists, in the wrong place, twice.**
   `.fux/fetchers/http.py:69` is an HTML→Markdown decoder; `cdp.py:282` carries
   the same `_MdParser` marked *"Kept identical to…"*, tested by nothing.
   Neither is reachable from the git-dir walker — **a local `.html` on disk is
   never decoded.** A session that starts by *writing* an HTML decoder has
   already gone wrong.
2. **A live heading defect.** `.rst`, `.adoc` and `.org` are allowed types
   whose heading syntax matches nothing in `extract.py`'s `^(#{1,6})\s+`. Three
   of six allowed types have had every heading land in the body field since the
   allowlist shipped. That is P0 — a correctness fix, not a new capability.
3. **The index lock exists; its scope is the gap.** `runner.py::acquire` has
   **one caller**, the background runner. A foreground `fux ingest` evicts the
   runner and then writes holding nothing. ⚠ Read from call sites, **not
   reproduced.**

**The contract a decoder must satisfy is forced, not chosen:** `bytes →
Markdown | None`, because `extract.py` re-derives headings from `#` and a
decoder returning flat text silently disables *"heading match outranks body
match"* on every non-Markdown document. `None` means *a model must read this*,
and it feeds a **committed queue** with **gitignored progress** — Arpit's
split, 2026-08-26.

**Fork E was ruled the same day, and the law did not move.** Arpit: *"let the
consumer add the dependencies — unless the consumer adds the dependencies,
that feature won't be available."* This looked like an L1 amendment and is not
one: [ADR-ENRICH](../docs/adr/0040_enrich.md) decision 1 already states the
pattern as a table — network I/O → `.fux/fetchers/`, model calls → the
consumer's agent — and **this is its third row, `.fux/decoders/<name>.py`.**
L1 constrains the runtime fux ships; consumer code is not that. ⚠ **The
binding objection was L3, not L1** — a decoder that ran whenever its library
imported would make two developers with identical sources produce different
root hashes, so the set is **declared, not detected**, and a machine that
cannot satisfy it **fails loudly** rather than shipping a smaller index. ⚠ The
honest cost: a consumer decoder **can break L4 and no gate reaches it** — the
same asymmetry ADR-ENRICH decision 3 owns about `model:`.

**Two refusals to preserve.** `.json` may not re-enter the allowlist by
argument: ADR-TYPES verdict G was measured, and only a new pre-registration at
10 000 documents replaces it. And full YAML is refused **on correctness** —
expanding anchors duplicates terms and inflates `tf`, so the conformant parser
is the wrong one.

### The change before it: `ask` cites at heading level (W-84, 2026-08-26)

**Arpit asked whether `ask` should cite at line level. The answer was no, and
the refusal is the durable half** — [ADR-ASK](../docs/adr/0004_ask.md)
decision 10 carries it. A line range on `ask` could only be computed at
**ingest**, so one edit makes it point at the wrong lines *while looking
exactly as right as before*; it also costs a positional index (2–4× the
postings) against an index whose whole pitch is that it fits in git.
**`answer` cites lines because it fetched the bytes.** If a future session
proposes "just add line numbers to `ask`", that is the fence it is crossing.

**What shipped was already in the index.** `phrases` — the document's headings,
extracted at ingest since M2 — were rendered by `answer --no-refer` alone.
[`query/headings.py`](../src/fux/query/headings.py) now selects the ones
matching the query and `ask` (text), `ask/find --json` and MCP `fux_search`
render them. **Display-only, after `run_query` returns** — the position
`_resolve_title` occupies under P5, which is what keeps the differential law
intact. `find`'s piped stdout is byte-identical.

⚠ **The defect it found is the one to carry forward:** `fux_search`'s **MCP
tool description** claimed *"line-range citations"* it has never returned — the
identical wrong claim commit `ad95a24` had fixed in `docs/guide.html` earlier
the same day, surviving in the machine-facing copy. **Tool descriptions are
documentation compiled into the package and no gate reads them.**
`fux_passage`'s and `fux_related`'s are still unchecked.

⚠ **Not committed.** A concurrent session was mid-rename in the tree
(`store/recordshape.py` → `recordschema.py`); a W-84 commit would have swept a
half-finished rename in. **1 500 unit tests green**; `tests_e2e/` unverified
(3.10 sandbox — the same limitation W-82's build disclosed).

### The change before it: the queue is ONE item (2026-08-26)

**Arpit collapsed W-74, W-75, W-77 and W-81 — and the five documents behind
them — into a single file**,
[`open/W-82-the-consolidated-build.md`](open/W-82-the-consolidated-build.md).
**Read that before anything else in this section**; several paragraphs below
still describe the four items separately and are history now.

⚠ **A merge, not a close.** Nothing was decided by moving it. Every fork those
four items carried is still open and still Arpit's — twenty-three of them,
registered in W-82 §5.

⚠ **The two compare docs' verdicts were folded into W-82 §4 verbatim BEFORE the
archive move**, because archiving a compare doc makes its verdict uncitable and
W-82 §1's calls rest on them. **W-82 §4 is the live home of the clock verdict
and the concurrency verdict.** `archive/compare/url-refresh-trigger.compare.md`
and `url-fetch-concurrency.compare.md` may be named, never cited.

**Four calls were made the same day, and one of them withdrew a proposal:**

| call | consequence |
|---|---|
| **every cited URL is fetched before the final answer** | already shipped — and it **withdrew `update --warm` and `answer --memo` outright**, since fetching regardless leaves neither flag a justification |
| **the detector is the query-driven dirty list**, unconditional | W-82 §3.2; `dirty.py` and `run(only_urls=…)` both already exist |
| **concurrency is declared capability**, `min(declared, configured)` | W-82 §4.2 — the one fork of the twenty-four that is ruled |
| **no local content store** | W-82 §6, with a reopen trigger, so it is not re-derived |

⚠ **The gap that survives every one of those calls, and it is the reason W-82
exists:** fetching at answer time fixes **correctness** and cannot fix
**recall**. A URL that changed upstream still holds its old terms in the index,
so it never ranks into the candidate window, is never cited, is never fetched,
and **nothing notices**.

### The most recent change: the embedding model was DELETED (2026-08-25)

**Arpit removed the embedding model and the entire dense lane.** `src/fux/embed/`
(including a 7.9 MB `model.bin`), `query/dense.py`, `derive/dense.py`, the
committed per-chunk `vectors` field, `[dense]` and **`ask --hybrid`**. Cause:
[DENSE-CHUNK](regression/2026-08-24-dense-lane-gate/VERDICT.md) measured
**0 fixed / 2 broken at every setting that fires** — the model mean-pools static
token vectors, so the lane was **as order-blind as BM25F**. Measured cost of
carrying it: the **wheel was 97 % model** (6.84 MB -> 233 KB), the committed
index **-22.6 %**, a full ingest **6.8x** faster
([run](regression/2026-08-25-model-removal/report.md)).

**Fux is now lexical-only, with no bundled model and no path to a semantic lane
that does not start by re-adding a dependency.** That is the state of play; the
sections below that describe a dense lane are history and are marked.

### Before that: `v2.0.0-alpha.0`, and the records caught up to it (2026-08-24)

**`v2.0.0-alpha.0` is released.** It is a **pre-release on purpose**: the
committed record shape moved to `fux.index.v2` (five-field BM25F, `flen`
replacing `wlen`, the `code` field dropped) and the analyzer to `v2`, so it
ships ahead of a stable `2.0.0` to give the migration a soak. **All four new
records — ADR-TUNE, ADR-MCP, ADR-ENRICH, ADR-RERANK — are `status: proposed`.**
Ratifying them is a separate, human step and it is owed.

**W-73 and W-76 are closed.** Both built, both released, both recorded in
[`IMPLEMENTATION.md`](IMPLEMENTATION.md); their detail files retired into
`archive/open/`. The queue is **three, and every one of them is `arpit`**.

**What the 2026-08-24 audit found, and it is the thing to carry forward.**
`tests/test_adr_freshness.py` **passed throughout W-76 while sixteen records
went stale**, because ownership is **directory-level**: rewriting the scorer
under `src/fux/query/` satisfied the check by touching **ADR-ASK**, while
**ADR-RANKING**, whose entire subject is that scorer, was never opened. *The
check is not wrong; it is narrower than it reads.* Deciding whether a record
may declare *"I describe this component even though I do not own it"* is
[W-82 §5.3](open/W-82-the-consolidated-build.md)'s real deliverable.

**A second class was closed the same day.** The register's display labels
disagreed with their filenames on **sixteen** rows (the standing note claimed
four) and `[0039]` labelled two rows — which manufactured broken links, because
a link written from a label resolves to a plausible file that does not exist. A
repo-wide sweep found **71 more**. All fixed, and gated by
[`tests/test_doc_links.py`](../tests/test_doc_links.py) under the two-strikes
rule.

### Before that: two releases, and the queue is nearly empty (2026-08-21)

**`v0.35.0` is released and live on PyPI**, verified black-box from the
published wheel — a clean venv, `pip install fux-engine==0.35.0`, then `add` /
`remove` / `update --check` / `ask`. `fux url` answers `invalid choice`, which
is the retirement working. `v0.34.0` (the graph, refer and maintenance planes,
delta ingest) shipped the same day, ahead of it.

| what landed | where |
|---|---|
| **W-63 — the source verbs** `fux add` / `remove` / `update` over all three source lists; `fux url` deleted; `ingest --refresh-urls` hidden for one release | `v0.35.0` |
| **W-64 — the progress plane** on `ingest.run()` / `derive.build()`; stderr-only, TTY-gated, counts not clocks, stdout byte-identical with the bar on or off | `v0.35.0` |
| **scan-by-default** — `ask`/`find`/`answer`/`graph` take the reference scan unless `--fast`; three e2e tests had gone **vacuous** at the flip | `v0.35.0` |
| **PRIORITY P1–P7**, then `PRIORITY.md` archived — ordering lives in `OPEN-WORK.md` only | `1fc51a7`…`1a8ce1a` |
| **P6 — the refer plane wired into `answer`** as its default path (`--no-refer` restores the M2 shape); **ADR-REFER and ADR-ANSWER both flip `accepted`** | `9f8366e` |
| **the Windows console class became a check** — `→` in a `print()` crashed both Windows CI arms on the release commit; second occurrence of the class, so `tests/test_windows_console_safe.py` now gates it | `35eeae0` |

**The design point moved to 10 000 documents on 2026-08-21** (Arpit,
CLAUDE.md §Litmus). 50 000 then 100 000 are staged later targets. It re-scoped
W-26, lowered W-61's urgency (a 3.5 s problem, not a 44 s one) and **closed
nothing** — R5 fails at 10k too. The records still arguing from 10⁵–10⁶ are
[W-65](../archive/open/W-65-design-point-reconciliation.md), filed the same day and **closed 2026-08-22**.

**Suites: 1 010 passed, 1 skipped** (`tests` + `tests_e2e`, 2026-08-22) — 947
unit / 64 e2e, nine CI arms green including both Windows.

### Before that: three gates ran, and two did not pass (2026-08-20)

**Arpit lifted the hold on prediction runs, and R4, R5 and R6 all ran the same
day** against thresholds frozen and committed first.

| | verdict | the number |
|---|---|---|
| **R4** | **PASS** | cold k=10 p95 **1.113 s** / 3 s · warm **0.016 s** / 300 ms |
| **R5** | **FAIL** | **44.4 s** at 100 000 docs / **1 s** · **0.651 s at 1 000, where it passes** |
| **R6** | **INCONCLUSIVE** → adjudicated **PASS** (Arpit, 2026-08-22, §3.1) | every tier matched; tier 1 matched *without the driver too* |

**Read R5 as the useful kind of negative.** A 20-document commit costs whatever
touching the whole corpus costs, and the attribution says why: git is
~constant, and two O(corpus) passes are the entire 44 s. **A 10× speedup still
misses the bound by 4.5×** — which rules out "just optimise it" arithmetically
rather than by opinion. Only removing the work from the commit path reaches 1 s,
and that is an architectural call, so it went to a compare doc —
[`hook-at-scale.compare.md`](compare/hook-at-scale.compare.md), **ruled by Arpit
on 2026-08-22: B, the hook defers**, in a **detached-runner** variant.
`post-commit` writes a **dirty list** of the changed documents, spawns a
one-shot re-index that exits, and returns.

> **The correction worth carrying forward, because it is what everyone gets
> wrong on first contact.** "Just re-index the files that changed" is **already
> shipped** — delta extraction landed in M5, and **R5's 44.4 s was measured on a
> 20-document commit that was already skipping unchanged documents**. Cost
> tracks **corpus size, not delta size**: sha every file to learn what changed,
> parse every document because edges need it, resolve every edge because an edge
> is a claim about *other* documents, write every shard. An agent proposing
> delta ingest as the fix for R5 has re-derived M5.

**Option D is deferred, not rejected.** Making those passes incremental reaches
the bound at 10 000 (a 4× speedup gets to 0.99 s) but **not at 50 000**, the
next staged target, where it would need ~20×. B is constant in the corpus at
every size. The dirty list is deliberately a **list, not a flag**, because it is
exactly D's input — so D becomes a later increment rather than a rewrite.

**Read R6 as an instrument finding.** The engine did everything R6 says it
does. What failed is one third of the harness: tier 1 merges cleanly with the
driver removed, so it could never have failed. **The control arm — added while
writing the pre-registration — caught that on its first execution**, and
without it tier 1 would have been recorded as a pass that proved nothing.

⚠ **Both records stayed `proposed` on the day, and both went `accepted` on
2026-08-22** — neither on a passing re-measurement, which is the part to
understand before touching either. **ADR-MAINTENANCE** is accepted because the
fork R5's failure opened was *ruled*: it now describes a **deferring** hook, not
the inline one R5 judged. **ADR-MERGE-DRIVER** is accepted on Arpit's reading of
R6 — §3.1 governs, tier 1 is dropped as uninformative, tiers 2 and 3 carry it.
⚠ **Both carry a named debt.** ADR-MAINTENANCE describes behaviour that is
**not built** (W-66). ADR-MERGE-DRIVER rests on a **reading of a
self-contradicting pre-registration** (W-67), and its veto 5 returns it to
`proposed` if the repair overturns that reading. **R6-MERGE itself still reads
`INCONCLUSIVE` and was not edited** — the ruling is an addendum beside it. **ADR-REFER went `accepted` on 2026-08-21** once P6 made the
plane load-bearing in `answer`: accepted **carrying its budget-sweep veto
condition open**, which is Arpit's call and not the same as measured.

### Before that: delta ingest, and a veto that fired (2026-08-20)

**`fux ingest` no longer re-extracts what did not change.** ADR-INGEST
decision **1b**: an unchanged content `sha` keeps its `title`, `phrases`,
`terms`, `wlen` and `code`; **edges still re-resolve every run**, because they
are the one field the rest of the corpus can change without this document
changing. **22.7× at 1 000 documents, 26.4× at 5 000, byte-identical** to a
full run; `fux ingest --full` re-extracts regardless.

**Read this as a worked example of how a veto condition is supposed to work.**
The record said re-extraction happens every run *and named the measurement that
would reopen it*. That measurement was taken, filed
([the cost profile](regression/2026-08-20-ingest-cost-profile/report.md) —
92 % of an ingest is the dense embedding), and the decision changed in the same
change. Nobody had to argue about it.

**One guarantee is narrower, and it is written down**: term-hash collision
detection is complete only under `--full`. It is in ADR-INGEST's Consequences,
not hidden in a docstring. ⚠ **This paragraph used to name a second guarantee**
— *"a newly available embedding bundle does not retro-fit `code`"* — and both
the bundle and `code` were deleted (2026-08-23 and 2026-08-25). The carry-forward
property survives the field: a new extraction rule does not reach an unchanged
document until it changes or `--full` runs.

⚠ **It is not R5.** It makes R5 *reachable* at corpus sizes where the old build
could not have passed it. The gate itself is still held.

### Before that: the agent lane is empty (2026-08-20)

**Every item an agent could close alone is closed.** What remains needs Arpit:
a verdict, a hold lifted, or fifty goldens written by hand.

| shipped 2026-08-20 | record | measured? |
|---|---|---|
| W-46 · W-48 — two query defects | ADR-CLI · ADR-ASK · ADR-ANSWER | n/a |
| **M3** the graph lane | [ADR-GRAPH](../docs/adr/0029_graph.md) ✅ | **no** — W-57 |
| **M4 core** the refer plane | [ADR-REFER](../docs/adr/0030_refer-plane.md) ✅ (2026-08-21, veto 2 open) | **partly** — R4 passed; the budget sweep is W-59 |
| W-45 + W-55 — what fux indexes | [ADR-DIR-LIST](../docs/adr/0022_dir-list.md) · [ADR-TYPES](../docs/adr/0031_types-list.md) ✅ | **no** — rides with W-52 |
| W-56 — both lab environments | SETUP-LAB · SETUP-PLAYGROUND | rebuilt, under git |
| **M5** maintenance | [ADR-MAINTENANCE](../docs/adr/0032_hooks.md) ✅ · [ADR-MERGE-DRIVER](../docs/adr/0033_merge-driver.md) ✅ | **ruled, not passed** — W-66 builds it, W-67 repairs R6's instrument |
| W-60 — the TTL fetch cache | [ADR-REFER](../docs/adr/0030_refer-plane.md) 5a-5c ✅ | n/a |
| **W-63 · W-64** the source verbs, the progress plane | [ADR-CLI](../docs/adr/0002_cli-surface.md) ✅ | captured, not gated |

**No record on this list is `proposed` any more.** ADR-MAINTENANCE and
ADR-MERGE-DRIVER both went `accepted` on 2026-08-22 on Arpit's two calls;
ADR-REFER left the list on 2026-08-21. **What replaced "unratified" as the
standing risk is subtler and worth naming**: ADR-MAINTENANCE is an accepted
record describing **unbuilt** behaviour (W-66), and ADR-MERGE-DRIVER is an
accepted record resting on a **reading** rather than a clean pass (W-67). An
accepted record that is wrong reads as authority — which is what Law zero exists
to prevent — so both debts are written into the records themselves rather than
left only here.

**The hold on prediction runs was lifted on 2026-08-20** and R4, R5 and R6 ran
the same day. **R7 was closed *unmeasured* on 2026-08-21** — cancelled on
Arpit's call, not FAILed — and is re-derived and re-pre-registered at 10 000 by
M6. Both harnesses exist
([`tools/maintenance-bench/`](../tools/maintenance-bench/run.py), the rebuilt
lab).

**`fux` is fourteen flat verbs now** — `setup` `doctor` `ingest` `build`
`add` `remove` `update` `ask` `find` `answer` `explain` `graph` `path` `hooks`
— plus a separate `fux-merge-index` console script, because git invokes a merge
driver as a bare command. **`url` was deleted outright at `v0.35.0`** (four
days old, pre-1.0). **Still no subcommand tree.**

### Before that: M3 and M4's core landed (2026-08-20)

**Read this first: the engine grew two milestones and neither is measured, and
the reason is that the measuring environments are gone.**

- **M3, the graph lane, shipped** ([ADR-GRAPH](../docs/adr/0029_graph.md),
  accepted). `explain` / `graph` / `path`; communities by **unseeded** label
  propagation in a **derived** plane (`.fux/runtime/graph.json`); PPR-lite with
  a **lazy** walk. The archived relational eval passes on the new kernel,
  11/11, its corpus copied live into `tests_e2e/eval/`.
- **M4's core shipped** ([ADR-REFER](../docs/adr/0030_refer-plane.md),
  **⏳ proposed, not accepted**). `source` · `freshness` · `arc` · `chunk` ·
  `rescore` · `assemble`. **No verb exposes it** — deliberately.
- **`fux-lab` and `fux-playground` do not exist on this machine**
  ([W-56](../archive/open/W-56-sibling-environments-missing.md)). The lab is the one the
  standing obligation says is never deleted; the playground held **50 graded
  goldens with one local commit and no remote**. Between them they are the
  instrument for **R4, R5, R6 and R7 — every unmeasured prediction left in the
  plan** — and M2's own filed reproduce commands point into the lab and no
  longer run. **This is the single most consequential open item.**
- **Three things were deliberately not built, each on a fact:**
  - **`max_age_seconds`** — the committed record carries **no ingest time**
    (`ver` is a revision counter), so the bound could not have been honoured.
    Freshness is a mode plus **content verification** — comparing shas, which
    answers the question exactly rather than approximately.
    [W-58](../archive/open/W-58-no-recorded-ingest-time.md).
  - **A seeded community algorithm** — the randomness was *removed* instead,
    which is the stronger guarantee, and a test parses the module's AST to keep
    it that way.
  - **Wiring the refer plane into `ask`/`answer`** — its gate had not run, and
    putting an unmeasured plane on the default surface is how an unproven thing
    becomes load-bearing. **Flipped 2026-08-21**: R4 passed, and P6 wired
    **`answer` only** onto the plane by default (`--no-refer` restores the M2
    shape). `ask`/`find` and ranking are still untouched.
- **Two defects were found by measuring code rather than reading it.** The
  archived PPR walk truncated at three iterations **ranks by parity** (`d` at 3
  hops scored above `c` at 2); and greedy score-per-byte is **systematically
  biased toward short passages**, so a 50-byte fragment crowds out the 400-byte
  passage that answers the question. Both are fixed and both have tests that
  fail without the fix.
- **Suites: 681 green** (`tests` + `tests_e2e`), up from 547.

### Before that: W-54, the sources rewrite (2026-08-19)

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
- **`archived=` is parsed and deliberately unread.** ADR-ARCHIVED-CONTENT decision 5
  was amended to split the file from the signal: parsing a declaration nothing
  reads cannot be wrong, and changing what a verb says about a document needs
  an instrument. [W-44](../archive/open/W-44-archived-content-signalling.md) still owns it.

### Before that

- **M0, M1 and M2 have shipped.** `v0.32.0` is on PyPI (2026-08-13, verified
  black-box from the published wheel). `fux ingest` / `build` / `ask` / `find`
  / `answer` work end to end, with the derived T1 accelerator on warm queries.
- **R1 · R2 (3/3) · R3 all PASS.** R3's number: worst-case warm p95 **27.2 ms**
  on 8 870 RFCs against a pre-registered 150 ms bar.
- **The pruning gate closed FAIL.** The committed index carries full postings,
  permanently. That design branch is closed, not paused.
- ⚠ **Hybrid fusion is GONE (2026-08-25)**, not off. It shipped default-off on
  a measured net −6, its per-chunk successor measured **0 fixed / 2 broken**,
  and Arpit deleted the lane, the model and the flag. `--hybrid` is now an
  argparse error. **There is no dense lane to flip.**
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
  Writing it found a live defect ([W-46](../archive/open/W-46-hybrid-missing-model-crash.md)).
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

*Updated **2026-08-27**. The queue is **three**, and every one is `arpit`-lane:*

| item | what it needs | filed |
|---|---|---|
| **W-82** | 27 forks, none of which an agent may default | 2026-08-26 |
| **W-87** | ✅ Phase 0 ruled. P1–P5 need **environments, not decisions** — `fux-playground`, a real URL corpus, a 3.11+ install | 2026-08-27 |
| **W-89** | does **L2** reach a query log? A gap in the laws | 2026-08-27 |

**The immediate next step: nothing here is agent-closable.** Under CLAUDE.md
§Triage first, a session that finds this state says so in ≤3 lines and stops.

> ⚠ **Everything below this line in §2 is HISTORY and is stale as a status.**
> It still reads *"the queue is five"*, names W-74/W-75/W-77/W-81 as separate
> items (they were **merged into W-82** on 2026-08-26), and names W-78 as open
> (closed 2026-08-25). It is kept for the judgment in it, not for the counts.
> The table above is the state of play.

*Superseded lede, 2026-08-25: the queue is **five**: **W-78** (ruling 1 only —
reopen ADR-RERANK veto 1 or confirm it), **W-81** (`agent`), **W-77**, **W-74**,
**W-75**. Four of the five are `arpit`-lane rulings. W-73, W-76, W-79 and W-80
are closed and their entries below are history, not pending work.*

> ⚠ **The count in this section was wrong twice before it was right.** It said
> "three, all `arpit`" while W-79 was open and `agent`-lane, and again after
> W-81 was filed. The lesson is in `governance.md`: **a file whose job is to be
> the current state cannot be the one that is stale.**

> **Addendum 2026-08-26 — this section predates two things that happened since
> and needs a fuller pass; not done here, flagged instead.** (1) ADR-TUNE was
> built the same day this was last updated (see its 2026-08-24 amendment) —
> *"the immediate next step: build ADR-TUNE"* below is stale, it is built and
> `status: proposed` pending ratification. Building it surfaced two gaps
> (`[fuse]` unreachable, `explain --no-tune` inert), filed same-day as **W-79**
> in the `agent` lane — a fourth queue item this section's own count omits.
> (2) **W-79 is now closed** — ruled delete, built 2026-08-26:
> `query/hybrid.py` deleted, `[fuse]` out of ADR-TUNE's schema, `explain
> --no-tune` removed, `playground_grade.py` repointed at `run_query`. Detail:
> [`archive/open/W-79-remove-the-dead-fusion-code.md`](../archive/open/W-79-remove-the-dead-fusion-code.md),
> `IMPLEMENTATION.md`'s W-79 row. The queue is genuinely **W-77, W-74, W-75**
> now — three, and W-79's absence from the original count above was already
> wrong the day it was written, not made wrong by this close.

⚠ **~~The immediate next step: build ADR-TUNE~~ — BUILT 2026-08-24**, shipped
in `v2.0.0-alpha.1`; the record is still `status: proposed` pending
ratification (that ratification is W-77 ruling 3). **The immediate next step is
now W-78 ruling 1**, which is Arpit's. The paragraph below is kept as the
record of what was owed at the time. ⚠ **Parts of that record are stale on
arrival**: several of its own decisions shipped inside W-76 (6b's
`wlen`->`flen` migration, and query-time field weights), so read it against the
code before building from it.

⚠ **A live fork, unadjudicated, filed 2026-08-24:** ~40 of the links the sweep
repointed now point *into* `archive/`. Whether a link in an ADR's prose
*names* an archived item or *cites* it is Arpit's call — a test was written for
it and **deliberately removed rather than shipped red**, because it could not
tell the two apart. Both readings are written out in W-77.

- **W-75 was filed 2026-08-22** under a new
  **ADR-URL-INGEST · ADR-FETCHER** group: [nothing in fux can learn that a URL
  changed](open/W-82-the-consolidated-build.md), spec in
  [W-82 §3](open/W-82-the-consolidated-build.md), two forks split
  out to [W-82 §4.1](open/W-82-the-consolidated-build.md)
  and [W-82 §4.2](open/W-82-the-consolidated-build.md).
  **A file change is an event; a URL change is not** — `post-commit` re-indexes
  a changed repo document, a changed URL waits for a human to type `fux update`,
  and nothing reports how long ago that was. Two reframes carry the argument:
  *answer* freshness is already shipped, so a stale `url:` record costs
  **recall, not correctness**; and a **detector** and a **clock** are different
  roles, which collapses most of the apparent options. **Eight forks, all
  Arpit's** — fork 3 is the consequential one, because it amends a contract
  (`ADR-FETCHER` decision 2, four functions) that has survived two callers
  unchanged. **Phases 0 (measure) and 1 (report) are startable now and depend
  on no fork.** ⚠ Three hazards live in the item: `dirty.py`'s *"advisory,
  never authoritative"* is what keeps L3 true and a URL refresh driven by it is
  not advisory; a changed validator token must never mean a changed record; and
  **`cdp.py` is not thread-safe** (`global _session`, one WebSocket), so a blind
  thread pool produces plausible documents attributed to the wrong URLs — it
  passes every determinism check.
- **The queue's second item — W-74, filed 2026-08-22** under a new
  **ADR-RS** group: [fux has no contract for what *right* means](open/W-82-the-consolidated-build.md),
  spec in [W-82 §5.2](open/W-82-the-consolidated-build.md).
  ADR-RS governs *how* a claim is frozen and is silent on *what quantity is
  worth freezing*, so every quality number this project has produced carries an
  undeclared query distribution and an implicit cost model where a fabricated
  citation and an honest decline count the same. **Nothing is decided — it ends
  in six forks, all Arpit's**, and fork 4 is the one that can quietly break a
  law-adjacent property (measuring the `answered` gate needs a judge model:
  outside the maintenance path so L3 holds, non-reproducible unless the model
  and prompt are pinned). **Part A — the declarations — is unblocked by the
  lab; Part B cannot run**, because `acme`/`orbit` are gone and the five-tier
  redesign is unexecuted. ⚠ **It is not a re-filing of the withdrawn W-62** and
  says so in both files; if the two are ever confused, W-74 yields.
- **The immediate next step is Arpit's, not an agent's.** Three decisions sit
  in [`OPEN-WORK.md`](OPEN-WORK.md)'s inbox and `work/BLOCKED.json`, and **all
  three sit above completed work** — nothing is waiting to be built:
  1. **R7's committed-size budget at 10 000 documents.** W-26 says the
     re-derivation is his if it is not obvious, and it is not. ⚠ **The 10k
     size is already measured** (14.2 MB raw / 2.3 MB packed), so **a budget
     chosen after reading that number is contaminated by it** — which is
     exactly why it was asked rather than answered.
  2. **`R8` is claimed by two documents.** T2's measurement was registered as
     **R9**; confirm or swap.
  3. **W-67 left one DoD box unticked deliberately** — the frozen 2026-08-20
     pre-registration was not edited, because that item contradicted itself
     about whether it may be.
- **The maintenance plane is built, not just described.** W-66's four phases
  landed: `post-commit` defers to a detached one-shot runner behind a pid lock,
  the stop is cooperative and fires only before `write_index`, `fux ingest`
  takes over, `fux doctor` reports the runner and gained `--json`. **This is
  the change that answers R5's failure** — commit cost is git's cost and
  constant in the corpus, asserted end to end at 50 vs 800 documents.
- **M6's largest deliverable was measured and declined.** R9 puts warm
  worst-case p95 at **12.46 ms at 10 000 documents against R3's 150 ms bar**,
  so **T2 is not built** and
  [the T2 proposal](proposals/t2-segments.md) records why. **Read its
  reopen condition before proposing T2 again**: it is a *number*, not a size,
  so 50 000 documents arriving does not reopen it — 50 000 documents crossing
  150 ms does.
- **Do not quote R9's margin without its caveat.** The corpus is synthetic and
  **18× lighter per document** than R3's, with 37× fewer distinct terms. The
  judged quantity survives that (the accelerator is `df`-bound; the *scan* is
  bytes-bound and shows the full 170× gap), and a density correction lands
  within 15 % of R3 — but **nobody has measured T1 on real prose at 10 000
  documents**, that corpus does not exist, and it is recorded as owed.
- **Two traps found in the lab, both still live.** A stray `.fux/` and
  `fux.toml` sit at the **fux-lab root**, so `fux setup` in a fresh
  `<env>/repo/` resolves to the lab root and reports "nothing to do" while
  writing nothing — write `repo/fux.toml` first. And every environment
  `new-env.sh` scaffolds pins `fux-engine==0.33.0` from PyPI, which is neither
  current nor the working tree a tier measurement wants.
- **R6 no longer rests on a reading.** W-67 re-specified tier 1 to hash-select
  a shared shard and re-ran: **PASS**. ADR-MERGE-DRIVER's veto 2 is spent.
  **The frozen 2026-08-20 instrument was not edited** — the repair is a new
  file beside it.
- **W-65 reconciled fourteen documents** to the 10 000-document design point,
  four of which its own table never named. **Two live veto scripts** were still
  keyed to the retired `250 MB @100k` budget and now say so.

- **Before this pass — the prior state, now superseded above:** nothing was in
  flight in `src/`, the working tree was clean and `v0.35.0` was live on PyPI
  (`HEAD` = `9bb870e`, verified black-box from the published wheel). W-63 and
  W-64 both landed in it; their rows are deleted, their detail files are in
  `archive/open/`, and their outcomes are rows in
  [`IMPLEMENTATION.md`](IMPLEMENTATION.md).
- **What W-63 delivered.** `fux add` / `fux remove` / `fux update` over all
  three source lists, dispatching on the entry. `fux url` deleted;
  `ingest --refresh-urls` hidden for one release. Both `ingest/run.py`
  defects fixed: **a de-listed URL now leaves the index on an offline run**
  (deletion never needed the network) and a carried record's edges are
  re-checked rather than trusted. Nine records updated; surface captured at
  [`regression/2026-08-21-source-verbs`](regression/2026-08-21-source-verbs/report.md).
- **The one defect the release itself shipped, and its gate.** A `→` in
  `fux add`'s rejection message crashed both Windows CI arms — `cp1252` cannot
  encode it, so `print()` raised and the verb exited non-zero. **Second
  occurrence of the class** (`fux doctor`'s checkmarks, `v0.30.0`), so under
  the two-strikes rule it became `tests/test_windows_console_safe.py` in the
  change that recorded it. **CI caught what nine local runs could not** — read
  the Windows arms before calling a release green.
- **L4 now has two named networked paths, and its text did not change.**
  `fux add <URL>` (scoped to that URL) and `fux update`. The law already read
  *"paths"*, plural; what was wrong was the eleven records and docstrings that
  narrowed it to `--refresh-urls`, and those were corrected. **If you are
  tempted to edit CLAUDE.md's L4, don't** — it is agent-steering text, it is
  Arpit's to ratify, and in this case it was already right.
- **Concurrent sessions are not hypothetical here — they bit twice on
  2026-08-21.** First `src/fux/cli.py` was overwritten by another session and
  W-64's wiring vanished from it. Then a peer session and this one **deadlocked
  over who committed first**, each waiting for the other, neither able to see
  it from its own side. Both were resolved by `SendMessage`. **Re-read a
  shared file immediately before editing it**, prefer `Edit` over `Write` under
  `src/fux/` and `work/*.md`, and check `.claude/.locks/*/owner` before
  concluding a file is free.
- **Capturing a surface is not paperwork — it found four defects here.** Three
  were in the change being captured, and every one did something defensible
  while *saying* something false: an L4 announcement that fired with nothing
  fetched, `add --types` silently replacing the built-in allowlist, a skip
  reported as a failed fetch, `explain` answering for a document not in the
  index. Unit tests were green throughout.
  [ANALYSIS](regression/2026-08-21-source-verbs/ANALYSIS.md).
- **A test can pass for the wrong reason, and a default flip is how.** When
  `ask` flipped to scan-by-default, **three** e2e tests kept passing while
  silently ceasing to test anything — they drove the accelerator through a
  bare `ask`, which now scans, so they compared the scan with itself. If you
  change a default, grep for every test that depended on the old one.

- **`work/PRIORITY.md` does not exist.** It was archived; project memory and any
  prompt still pointing at it are stale. Ordering lives in
  [`OPEN-WORK.md`](OPEN-WORK.md), which is the rule anyway.

- **W-26 (M6) is the agent lane, and it is startable.** Its DoD wants every R
  prediction to carry *a measured value or an honest failure record*, and all
  three now do. R7 is M6's own measurement, not a precondition for it. **What it
  inherits: 47.6 % of R5's failing 44 s is `fux build`** — the derived plane M6
  is about to add a third tier to. Measure a tier's rebuild cost before choosing
  its default.
- **Both of R5's calls were ruled on 2026-08-22 and the inbox is empty.** The
  fork went to **B** ([`hook-at-scale.compare.md`](compare/hook-at-scale.compare.md),
  now `accepted`) and R6 to **PASS under §3.1**. They left two agent-lane items:
  **W-66** builds the deferring hook (Phase 1, the dirty list, lands alone and is
  Sonnet-executable; Phase 2's detached spawn and single-writer lock are
  **Opus** — they fail silently, rarely, and on someone else's OS), and **W-67**
  repairs the §3.1/§3.2 contradiction and re-runs a re-specified tier 1.
- **What else needs Arpit**, now that the hold is lifted and W-58 is ruled:
  1. **Write the playground's ~50 goldens** (W-57). No agent should do this:
     a golden derived from the engine's own output passes forever, including
     on the day ranking breaks. **W-59's budget sweep is blocked behind it**,
     so one human afternoon unblocks two items.
  2. ~~**The external-validation half of W-62**~~ — **withdrawn 2026-08-22 by
     Arpit**, who took parts 1 and 2 personally (*"that's on me, I'll own it"*).
     Its README half was completed the same day. **The question it asked is
     still unanswered** — whether Fux wins on private organisational documents
     is untested — so a future reader should not read this closure as evidence
     either way. See [`archive/open/`](../archive/open/W-62-measure-against-the-outside-world.md),
     named and not cited.
- **The old "W-26 looks available and is not" paragraph is retired, and this
  replaces it.** It rested on a DoD clause requiring *every* R prediction
  measured. All four now carry a measured value or an honest failure record —
  R4 ✅, R5 ❌, R6 ⚠, R7 closed unmeasured — so **W-26 is startable**, and its
  first question is whether T2 earns its place at 10 000 documents at all.
  Tier-auto still flips by measurement, never by hand.
- **Any R5 number taken before 2026-08-20 measures an engine that no longer
  exists.** Delta ingest changed ingest cost by more than an order of
  magnitude. When the hold lifts, re-run; do not reason from the old figure.
- **Nothing is half-built in `src/`, but two things are built-and-unproven.**
  M3 and M4's core both landed complete and green; what is missing is their
  *acceptance measurements*, carried by
  [W-57](../archive/open/W-57-graph-lane-acceptance.md) and
  [W-59](../archive/open/W-59-refer-plane-measurement.md). **Do not read "landed" as
  "validated"**, and **do not read ADR-REFER's `accepted` as "measured"**
  either — it was accepted on 2026-08-21 with its budget-sweep veto condition
  deliberately left open.
- **W-59 carries a standing instruction worth knowing before you run it:** if
  the budget sweep comes back flat, the greedy assembler **gets deleted**, not
  kept. **What changed on 2026-08-21:** the assembler is now on `answer`'s
  default path, so that deletion is a change to a released verb's output — the
  instruction stands, the change is bigger.
- **The ADR rewrite is done.** `work/adr/` no longer exists; `docs/adr/` holds
  the live set, ADR-LAWS at 0001, and every archived record maps to a successor
  by **name** in [`../archive/adr/README.md`](../archive/adr/README.md).
- **The Lane B inbox is empty.** W-30, W-31, W-32, W-33 and W-44's decision
  were all ratified by Arpit on 2026-08-19 and their outcomes are in
  [`IMPLEMENTATION.md`](IMPLEMENTATION.md) §Ratified decisions.
- **`v0.35.0` is released and on PyPI** (2026-08-21), verified black-box from
  the published wheel; `v0.34.0` shipped the same day ahead of it, and
  `v0.33.0` on 2026-08-19. **`CHANGELOG.md` `[Unreleased]` is empty again** —
  everything through the Windows fix is released.
- **M3 and M4 are done as of 2026-08-20** — the paragraph that used to sit here
  said they were the next step. Both proposals that were to graduate into M4
  have graduated and are archived; one of them shipped **with its central knob
  refused**, and the refusal is the interesting part (W-58).
- **Two items are PARKED behind one missing instrument** —
  [W-44](../archive/open/W-44-archived-content-signalling.md) and
  [W-52](../archive/open/W-52-df-over-the-union.md) both wait on a pre-registered query
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
  **`commit-msg`** hook — not `pre-commit`, because it has to read the commit
  message to honour the `no ADR affected` escape hatch, and that message does
  not exist yet at `pre-commit`. Do not treat it as advisory, and do not "fix
  it in the next commit".
- **No M-milestone work while its gating prediction is unmeasured or failed.**
  A hard sequencing rule, not a preference.
- **A pre-registered threshold may never move.** Ambiguous results go to Arpit
  unadjudicated.
- **Do not port the archived engine.** [ADR-PORT-LIST](../docs/adr/0015_port-list.md)
  is the complete list, and it is closed; each entry comes forward with its
  tests, when its milestone needs it.
- **The design point is 10 000 documents** (Arpit, 2026-08-21 — CLAUDE.md
  §Litmus is the normative home). 50 000 then 100 000 are staged later targets,
  **not the filter**. What did *not* change is the deployment filter: a 10 000-
  document corpus inside a corporation is still inside that corporation, so
  Windows fleets, proxies/SSO, air-gap and audit remain design inputs. **An
  argument that turns on 10⁵–10⁶ documents may not gate work today.**
- **Do not design in reference to Anton.** It is a testbed, not the priority
  filter.
- **The adapter cap (git + HTTP + Confluence) is a decision**, not a backlog.
- **`work/regression/` is the evidence store; the lab is scratch.** Never
  compare wall-clock across surfaces — see [`MACHINE.md`](MACHINE.md).

## 4 · Lessons learned

The ones that would change how a successor acts, newest first. Add to this list
when a session produces a lesson; do not let it become a changelog.

- **Verifying a request is not the same as answering it** (2026-08-27, W-93).
  Arpit asked for the skip list to be written into `.fuxignore`. The walker said
  his stated *mechanism* would not reduce the count — true — so the session
  shipped a different, correct change instead and reported it as done. He came
  back with the same sentence. **A wrong diagnosis inside a request does not
  invalidate the request**: say what the code says, then ask which shape he
  wants, and build that. The second pass took two questions and got it right.
- **Read the code before agreeing with the remedy, even when the person asking
  owns the repo** (2026-08-27, W-93 pass 1). *"The skipped files should get added into
  `.fuxignore`"* is a reasonable read of `599 skipped` and it does not work:
  the walker counts an ignored file as skipped, so the count would not have
  moved. The observation was right, the diagnosis was one layer off, and the
  only way to know was `gitdir.walk_sources`. **A remedy that sounds right is
  not a verified one; the fix is usually adjacent to the one proposed.**
- **A count over two populations is the same failure as a wall of text**
  (2026-08-27, W-93). W-88 stopped `fux ingest` printing 599 identical lines
  nobody read; the number those lines were replaced by was *also* unread,
  because 598 of it was a list working as designed. **When suppressing output,
  check that what survives still separates "we chose not to" from "we could
  not."**
- **A control arm is not optional in a harness whose job is to prove a feature
  works** (2026-08-20). R6's tier 1 passed and was worthless: it merges cleanly
  with the merge driver *uninstalled*, because two documents added on two
  branches land in different shard files and git has always handled that. The
  control arm was written into the pre-registration on principle and earned its
  place on the first run. **Before believing a green tier, ask what it would
  look like if the feature were absent.**
- **Attribute a failing number before anyone proposes a fix** (2026-08-20).
  "The hook takes 44 s" invites optimisation; the split — git ~constant, two
  O(corpus) passes at ~50/50 — proves optimisation cannot reach the bound, and
  turns a vague slowness into a specific architectural choice. Same lesson M1
  paid for once already.
- **Two sessions on one repository will collide, and the collision is silent**
  (2026-08-20). A concurrent session shipped W-25 as `621c83c` while this one
  was mid-edit on the same milestone, sweeping three of its files into that
  commit, and began W-60 minutes later — visible only because the harness
  reported files changing on disk underneath. **Check `git log` before starting
  an item, not only `OPEN-WORK.md`**: the queue is written at the end of a
  session and the commit exists before that. When you find a live build in
  flight, take a different item; re-applying your own version of it is how both
  copies get worse.
- **Run it; do not read it** (2026-08-20). Four defects in one session came
  from *executing* code that looked correct: the merge driver treated a
  one-sided **add** as a delete-vs-modify, so every disjoint addition — the
  common case — would have conflicted; `read -r A B < <(...)` returns non-zero
  at EOF without a trailing newline, so `set -e` killed a setup script with no
  output whatsoever; a bench reported **its own** interpreter beside a latency
  instead of the engine's; and an ARC differential caught cache state leaking
  into an answer. **None was visible by reading**, and three of the four would
  have passed a review.

- **A control is what makes a test mean something** (2026-08-20). The merge
  driver's test runs the same merge twice — once without the driver, once with
  — and asserts git conflicts in the first case. Without that arm the driver
  could have been doing nothing at all and the test would still have been
  green. **When you test that something helps, prove the harm exists first.**

- **Port the code, but measure it before you trust it** (2026-08-20). M3's PPR
  came off the archived kernel with its determinism discipline intact, and the
  discipline was right. The *algorithm* was not: moving all of a node's mass
  each step and stopping after a fixed three iterations makes a bipartite-ish
  graph **rank by parity** — seeded at `a` on the path `a-b-c-d` it scored `d`
  (3 hops) at 0.154 above `c` (2 hops) at 0.054. It had shipped that way. The
  artefact is purely from truncation, and the truncation is what makes the
  result deterministic, so the fix was a lazy walk rather than more iterations.
  **A port that passes its old tests can still be wrong; the old tests were
  written by someone who did not know either.**

- **A knob that cannot work is worse than a missing knob** (2026-08-20). M4's
  freshness policy was specified as `max_age_seconds`, with age read from "the
  ledger's recorded provenance". **There is no recorded time in a record** —
  `ver` is a revision counter, and `stamp.json`'s mtimes are excluded from
  byte-identity precisely because they are not reproducible. Building it anyway
  would have shipped a parameter that silently did nothing while a caller
  believed they had bounded their staleness. **Check that the input your design
  assumes actually exists before you implement the thing that consumes it** —
  and when it does not, say so in the record rather than approximating.

- **Removing randomness beats seeding it** (2026-08-20). Label propagation is
  random twice over and the reflex is `random.seed(0)`. A fixed seed makes one
  implementation reproducible; it does not survive a Python version that
  reorders a set, and it hides that the output depends on a number nobody
  chose. Sorting the visit order and breaking ties on the smallest label costs
  the same and needs no seed — and the test asserts the **absence of the
  import**, by parsing the AST, so the claim is checked rather than trusted.

- **A differential test earns its keep while you are writing it** (2026-08-20).
  The ARC cache's cached-vs-uncached assertion failed on its first run — not on
  the citations, but on a `"note": "cache hit"` string that leaked cache state
  into the answer. Nobody would have filed that as a bug and every caller
  diffing two runs would have hit it. **Write the byte-identity test before you
  believe the optimisation is neutral.**

- **A convention that is invisible decays, and you can measure the decay**
  (2026-08-20). W-45 argued that dot-prefixing `.evidence/` was "a convention
  riding on an implementation detail". It was possible to do better than argue:
  **2 of 7 filed runs use it and 5 do not**, and the 5 include every run filed
  after the item was opened. **When a doc says a convention is fragile, count
  how often it was actually followed** — the count is the argument.

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
by Claude (Cowork, claude-fable-5); the 2026-08-24 reconciliation pass by
Claude (Cowork, claude-opus-5).

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
floor separates noise from a true rescue. Hybrid shipped **default-off** on that
evidence. ⚠ **Superseded 2026-08-25: the lane was deleted**, so there is nothing
to flip — but **the lesson outlives the lane and is why this paragraph stays**:
a retrieval lane that cannot decline to answer will manufacture an answer, and
that is a property of the design, not of the model.

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
mega-project — the **deployment** litmus since 2026-07-21, whose scale filter
was revised to 10 000 documents on 2026-08-21 without touching the deployment
half — it is a copy of the company's
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
