# IMPLEMENTATION — the milestone log

**How to use this file.** This is the **evidence store**: what shipped, when,
and how it turned out. [`OPEN-WORK.md`](OPEN-WORK.md) reconciles against this
file before anything is treated as done, and a `W-nn` may only be **deleted**
from the queue once its outcome is recorded here.

Rules:

1. **Append a row when a milestone or release lands** — not when it is
   started, not when it is believed finished.
2. **Every row names its evidence**: the ADR that closed it, and the measured
   run under [`regression/`](regression/README.md) where one exists. A row
   with neither is a claim, not a record.
3. **Record the outcome honestly, including the negatives.** A measurement
   that stopped a month of building is a shipped result and belongs here.
4. **Ground it before writing it** — `git tag`, `git log`, the published
   package. Do not copy a status from another doc.
5. This file is **not** a changelog. `CHANGELOG.md` is per release, for users;
   this is per milestone, for the next session.

---

## Wave 3 — a signal worth publishing, a threshold that is not, and the last owed control (2026-08-28)

**Two calls. One shipped as ruled; one shipped half, because measuring it
produced a fact the ruling did not have.**

### `doc_coverage` — the signal ships, the gate is held

Arpit ruled *"add per-document coverage alongside, and let `grounded` require
both."* The field is computed, published and declared. **The gate is off.**

- **Derived in `rank()`, handed out through `stats_out`** — the seam
  ADR-CONFIDENCE already owns. Both scoring paths reach `rank()` with the same
  record dicts, so **the accelerator and the scan cannot disagree** and the
  differential law is untouched *by construction*, not by test.
- **`coverage` is unchanged**, so no consumer's reading of it moved.

🔴 **Why the gate is off, measured** ([run](regression/2026-08-28-doc-coverage/report.md)):

| population | n | min | median | max |
|---|---:|---:|---:|---:|
| real goldens reaching the clause | 37 | **0.401** | 0.882 | 1.000 |
| decoys reaching it | **1** | **0.710** | — | 0.710 |

**The decoy sits inside the goldens' range**, so no floor separates them, and a
floor of `1.0` — which *reads* structural — demotes **19 of 50** correct
answers. Picking a number from a 65-query table with no gap in it is **R10's
failure in a different costume**, and R10 is `INCONCLUSIVE` on this repo right
now for exactly that.

⚠ **And the original finding was smaller than it read: 14 of 15 decoys never
reach the clause**, being `partial` via `missing` already. The scattered-terms
case is **one query in fifteen**. The module now **reports** it instead of
claiming to catch it — an agent sees `doc_coverage: 0.42` beside
`band: grounded` and can act.

**The gating question went back to Arpit** rather than being resolved either
way. Shipping the expensive gate silently, or dropping his ruling silently,
would both have been a decision nobody made.

### The sealed subset — ADR-RS decision 15 loses `NOT BUILT`

Ruled: **seal 15 of 50, grow the set later.** Split by `sha256(id)` —
deterministic, seedless, **order-independent**, so re-sorting the goldens cannot
change the cut. Growing the corpus is a **reseal**, not an append.

**The power tension is resolved out loud, as decision 15 demanded:** 35 visible
and 15 sealed are **both underpowered and that is accepted rather than hidden.**
The ±2-query floor does not loosen because a set shrank — it gets *harder to
clear*. **Sealing buys a claim about contamination; it buys no precision.**

🔴 **5 of the 9 `known_failure` goldens landed in the sealed half** — 33 % vs
11 %. **Not corrected, because correcting it would be the bug**: balancing by
difficulty means reading the scores, which is the contamination the seal
prevents. A sealed score is **not comparable to a visible score** at this size.

⚠ **BUILT IS NOT PROVEN.** None of the three controls has been used in a run
that adjudicates anything.

### Verified

`tests/` **2 232 passed, 1 skipped** · `tests_e2e/` **73 passed** · playground
**`pass 41 · xfail 9`, PASS** — ranking is untouched, which it must be: the band
is computed from `rank()`'s output and nothing feeds back.


## Wave 2 — the daemon chain, in the order the ruling required (2026-08-28)

**Two calls, and the order was the point.** Ruling 3's own text says narrow and
the clock *"must land together or the tail silently stops being refreshed at
all"* — so observability shipped first, and narrowing second.

### The sweep status carries a reason and counts

`_sweep` returned a bare string. It now returns `outcome` plus what explains it,
and **`daemon.status` is declared in `state.schema.json`, which it never was.**

- **Both halves of the old shape cost something.** A `FuxError` about
  `max_parallel` and a dead network were the same `"failed"`; and ⚠ **an `"ok"`
  sweep could skip URLs silently** — `outcome: "ok"` with `skipped: 2` is a state
  the old shape could not express.
- **Verified live** against the lab repo that really skips:
  `{"fetched":2,"outcome":"ok","reason":"3 skipped, first: fetch failed: HTTPError:
  HTTP Error 404: Not Found","skipped":3}`, and `fux doctor`:
  **`[WARN] url daemon: … the last sweep reported ok but did not index 3
  document(s)`** — the exact case that was invisible the day before.
- **`reason` explains something or is absent**, never an empty string; bounded at
  300 characters; carries the **first** skip, not a list, because a file rewritten
  every sweep may not grow without someone deciding it should.
- **A daemon that never ran is not a doctor finding** — a check that fires for
  every repo is one people learn to skip.

### `fux update` is narrow by default

`fux update` refreshes the dirty list; **`fux update --all`** forces the full
sweep. No `--dirty`/`--stale`/`--changed` flag, per the ruling.

🔴 **The hazard that nearly shipped, and the reason to read a tolerance before
relying on it.** `dirty.read` collapses missing-and-unreadable to `[]` **on
purpose**, because it feeds reporting paths where *"cannot tell"* should degrade
quietly. Under narrow-by-default, **empty means fetch nothing** — so a repo that
never ran the hook, or whose `.fux/runtime/` was wiped, would have `fux update`
become a **silent no-op**. That is precisely the failure ruling 3 warns about,
arriving through a file's tolerance rather than through the ruling.

**`dirty.is_readable` draws the distinction: list absent ⇒ sweep everything; list
present and empty ⇒ fetch nothing.** Fail safe, not fail silent.

**All four paths verified live:**

| state | result |
|---|---|
| dirty list absent | `fetching 7 listed URL(s) (network) — no dirty list yet` |
| present, empty | `nothing to fetch — 0 known stale` |
| one stale URL | `fetching 1 of 7 … — 1 known stale. \`fux update --all\` fetches every one` |
| `--all` | `fetching 7 listed URL(s) (network) — \`--all\`` |

⚠ **A dirty URL no longer in the source list is not fetched** — the list is
advisory and outlives edits to the source list.

⚠ **The residual risk, stated rather than closed:** a repo running no daemon,
whose URLs change without any commit, now re-fetches only on `--all`. That is
the trade ruling 3 makes, and ruling 10 is what covers it. **Proxy and SSO
remain uncovered.**

### Verified

`tests/` **2 217 passed, 1 skipped** · `tests_e2e/` **73 passed** (74 minus the
duplicate deleted in wave 1). Records: ADR-MAINTENANCE 12, ADR-URL-INGEST 8,
ADR-CLI, ADR-DOTFUX, ADR-OUTPUT.


## Wave 1 — four calls made, and the smallest one was the largest (2026-08-27)

**Arpit ruled four independent blockers in one pass.** Three were minutes; one
turned out to be four defects wearing one name.

### `L8` — ratified as reverted

Shown the live text and confirmed. ADR-LAWS decision 8 now records the
ratification, and records what it does **not** do: the AOL-2006 grounding stays
**OVERRIDDEN, NOT REFUTED**, the risk is accepted, and the mitigation is
confinement alone. ⚠ **Nothing mechanical checks a law's wording** — the §1
handle sat on the withdrawn form in four live documents for hours and no test
noticed.

### The shadowed-submodule trap — FOUR sites, not one

The queue described one instance in `fux.ingest`. **A scan of every package
found four**, and the `ingest` one had already been fixed:

| package | shadowed | |
|---|---|---|
| `fux.derive` | `build` | ✅ fixed |
| `fux.refer` | `assemble`, `chunk`, `rescore` | ✅ fixed |
| `fux.ingest` | `run` | already aliased by a prior session |

**The module was renamed, not the function** — `assemble.py` → `_assemble.py`.
The function is the API and the module is implementation; the underscore says
what was already true and **no caller changed**, where renaming the export would
have touched roughly thirty sites for the same result.

🔴 **What the shadow had already cost, unnoticed:**
`tests/refer/test_refer_plane.py` fed **three functions** to `inspect.getsource`
believing it was scanning three modules for `urllib`/`socket` imports.
**L4's network import fence had silently stopped covering three files — 552
lines — and nothing failed**, because `getsource` works on a function too. The
fence is repaired and now reads the modules.

**Gated** by `tests/test_no_shadowed_submodules.py`, which walks every package
under `src/fux/` and carries a companion test proving it can see a planted
shadow — this repo has recorded vacuous passes before.

### The nine playground goldens — annotated, each with a verified reason

`pass 41 · xfail 9`, matching the README at last. **Every reason was checked
against the corpus rather than asserted**, and five of the nine turned out to be
sharper than "the corpus does not cover it" — **the answer is present and
plainly stated and the ranker puts something else first**:

- `q028`/`q029` — the runbook **states its own duration** on its second line and
  ranks 5.
- `q012` — an **exact command match inside a code block** loses to three
  documents that merely mention the word.
- `q019` — **supersession is recorded and does not invert a currency question**:
  the `status: superseded` ADR outranks the current one.
- `q044` — a **rejected-alternative** section is the answer and loses to the
  document about what was chosen.
- ⚠ `q035` — **enrichment did not close it.** The enrichment says in as many
  words that adding a retry makes an incident worse; the query is *"I added a
  retry and things got worse"*. Still rank 2.

⚠ **A marker lowers nothing.** `max_rank` is untouched, and a gap that closes
reports `XPASS` and **fails** the run — which is why annotating was safe.

### The duplicate post-commit test

`test_the_post_commit_hook_reindexes_after_a_commit` deleted; the deferral test
absorbed it and says so. The deleted one was written when `post-commit`
re-indexed **inline**, and its subject stopped existing when the fork resolved to
deferral. ⚠ It had also **raced since 2026-08-22**, failing about one run in
three on a loaded machine.

### Verified

`tests/` **2 203 passed, 1 skipped** · `tests_e2e/` **74 passed** ·
playground **41/50, PASS**.


## P3 PASSED, W-82's forks re-derived to zero, and a decoy that caught fux believing itself (2026-08-27)

**Evidence:** [P3](regression/2026-08-27-p3-sha-stability/VERDICT.md) ·
[the decoy control](regression/2026-08-27-decoy-control/report.md) ·
[`tools/quality-controls/`](../tools/quality-controls/README.md).

### W-87 P3 — PASS, and fork 3's gate clears

**19/19 = 100 %** of sanitized shas unchanged on an immediate re-fetch, against a
frozen `≥ 80 %`. Corpus: 19 real external documentation URLs — RFCs, PEPs,
`docs.python.org`, Wikipedia, a live status page — in a new lab environment.

- **A control arm was run**, because a 100 % with none is the M1 failure: a
  treatment that touched nothing, reported as a null effect. `Special:Random`
  changed; the 19 did not. **The instrument detects change.**
- **W-87 P4 is unblocked.** ⚠ **Cleared is not decided** — a fifth function on
  the fetcher contract is still Arpit's, and ADR-FETCHER decision 3's argument
  against composition is untouched by this number.
- ⚠ **The spec named no INTERVAL.** At 12 s apart this measures **server-side
  determinism** — do timestamps, ad slots, CSRF tokens break the sha for an
  unchanged document? None of 19 did. It does **not** measure document churn,
  which needs a new pre-registration with an interval in it.
- ⚠ **ADR-RS decision 12's reopen trigger has FIRED** — its disclosure has now
  been written four times, and its own text sets three as the trigger. Recorded,
  **not acted on**: decision 12 is Arpit's and forbids a session narrowing it.

### W-82 has ZERO open forks of its own

Re-derived against the code and the ledger, not against the prose. **27 total ·
18 ruled · 6 moved to W-87 (§5.2) · 2 moved to W-87 P4 (forks 3 and 4) · 1
(§3.6 fork A) answered by the build rather than a ruling** — the `fux-usage`
skill shipped for both vendors. Verified: `__main__.py` exists and
`python -m fux --version` works (ruling 14); `copilot` is still in `install`
(ruling 13).

**What remains under W-82 is not a fork:** ruling 3, held on Arpit's judgement.

### Two of ADR-RS decision 15's three controls, built

`tools/quality-controls/` — owed since W-78 ruling 2, and the blocker on them
(*"needs `fux-playground`, not on the build machine"*) **was false**.

- **The content-free placebo.** Matched-length enrichment carrying no
  information. ⚠ **One shared sentence pool, so every placebo has identical
  vocabulary** — a placebo *about another topic* would still discriminate.
  Deterministic from the source sha (L3, verified byte-identical), no model, and
  it installs nothing. An early version always overshot the target length and
  gave the arm a systematic **+8 %** bias — confounding length with content, the
  one confound it removes.
- **The decoy set.** Fifteen domain-plausible questions the corpus cannot answer.
  ⚠ **The one kind of evaluation material an agent may author** — no correct
  answer exists, so there is nothing to fit.
- **The sealed subset is NOT built and ADR-RS decision 15 KEEPS `NOT BUILT`.** It
  names three; two is not in force. And it is not mechanical — decision 15 itself
  says sealing shrinks the visible set and the tension must be resolved, not
  inherited.

### 🔴 The decoys caught something on their first run

**One of fifteen unanswerable questions is reported `grounded`.**

*"What is the SLA we publish for the payments API"* → `coverage: 1.0`,
`missing: []`, `separation: 0.58`, band **`grounded`**, citing the data-retention
policy. **No document discusses it.**

**The mechanism, verified term by term:** `coverage` and `missing` are
**corpus-wide**. All four terms occur — in **four different documents** — so
nothing is missing, both fact-based band clauses pass, and the band falls
through to `separation`, which it clears.

⚠ **That is the exact failure `confidence.py`'s docstring opens with.**
⚠ **And no ruling on R10 catches it**: `0.58` is above the `0.5` R10's selection
rule would have picked — worth knowing **before** R10 is ruled. It also suggests
`separation` answers the wrong question: it measures **decisiveness**, and a
corpus of near-misses is decisive about its best near-miss.

**Named, not fixed.** Per-document coverage changes a declared signal,
`output.schema.json`, the MCP result and every consumer — ADR-CONFIDENCE
decision 12. **No test pins the current behaviour**, deliberately: pinning a
defect is how it becomes the contract.

### Verified

`tests/` **2 192 passed, 1 skipped**. `tools/quality-controls/` claimed by ADR-RS
in the ownership table and its `owns:` list, same change.


## The daemon over the real internet, R10 measured, and a blocker that was never real (2026-08-27)

**Arpit authorised the network run.** What it closed, and what it exposed:

**Evidence:**
[the real-URL daemon capture](regression/2026-08-27-daemon-real-url/report.md) ·
[R10's verdict](regression/2026-08-27-r10-separation-floor/VERDICT.md).

### The blocker that was never real

`OPEN-WORK.md` §"Blocked on an environment that does not exist on the build
machine" listed six items. **Both environments existed**, on this machine, the
whole time — `~/my_programs/fux-lab` and `~/my_programs/fux-playground`, the
latter still holding its 50 goldens. The section was written by sessions that
had no shell and could not look.

⚠ **Two of the six were not blocked at all** and one of them, R10, was the
gate the confidence plane was waiting on.

### The daemon, against real external URLs

A new lab environment (`2026-08-27-daemon-real-url`) with seven real URLs.

| clause hands item 1 asked for | result |
|---|---|
| a detached process | ✅ pid reaped on `stop`, lock free |
| a real clock | ✅ |
| TLS · DNS · CDN | ✅ three hosts, two CDNs, ~500 KB |
| a real `404` | ✅ recorded skip, prior record kept |
| a real `429` | ✅ **first exercise ever** — `doctor`: `rate-limited by httpbin.org x8` |
| a proxy · SSO | ❌ needs a corporate network |

**The URL tail closed on a server nobody here controls:** a Wikipedia
`Special:Random` article changed between sweeps (`16:51:55Z` *Laurence Bennett*
→ `16:52:55Z` *Bargilt Iron Ore Mine*) and the daemon re-fetched, re-decoded and
re-indexed it **unassisted**, one interval later.

**W-82 ruling 3 is now held on a judgement, not on evidence.**

### R10 — INCONCLUSIVE, and not for the expected reason

The curve reaches `t = 0.75` at `separation 0.3`, **falls back to 0.60 at
`0.4`**, then rises to 1.00.

⚠ **The pre-registration froze two rules that disagree on exactly that shape** —
its selection rule picks `0.5`; its verdict table's non-monotone row picks *no
change*. **Handed to Arpit, not adjudicated.** `SEPARATION_FLOOR` stays `0.10`
and **no test was edited**, because `tests/query/test_confidence.py` asserts the
rule relative to the constant and never its value — a guard built for this
moment, working.

⚠ **Six queries sit at or above `0.5`**; the bin that first reaches `t` holds
four; the top two bins are empty. **No reading supports a shipped constant.**
Corrected for future runs in **ADR-RS decision 18**, never by editing the frozen
file.

### Three defects, all the same shape: a message that sends you nowhere

1. **`no decoder for application/json`** on a URL — while `jsondoc` is built in,
   claims `.json`, ran, and correctly dropped a bare UUID. The **file** path has
   always used `decode.reason()`, whose docstring says conflating *"nothing
   claims this"* with *"a decoder got nothing out"* would **make the queue
   useless**. ADR-FETCHER decision 11.
2. **Consumer decoders never reached URL content** — `decode()` called without
   `root`, so ADR-DECODE's *"a consumer may bring a dependency fux may not"*
   stopped at the network boundary. Found while fixing (1).
3. **`shard missing/mismatched _format header`** — the message an **engine
   upgrade** produces, and the least informative of `read_shard`'s three header
   checks while its two siblings both name found-and-expected. It made all 50
   playground goldens fail in a way that reads as corruption, with **no migrate
   verb** and no hint that a re-ingest is the answer. ADR-INDEX-LIFECYCLE.

**Four new tests** in `tests/ingest/test_urlsrc.py`, **two** in
`tests/store/test_writer_reader.py`.

### Named, not taken

- **A URL that needs a model can never be queued for one** — the file path
  writes `.fux/enrich/queue.tsv`, the URL path writes nothing
  (`grep -c queue urlsrc.py` → `0`). `queue.tsv` is committed, so it is a scope
  call.
- **Nine playground goldens carry no `known_failure`**, so a full run reports
  `FAIL — 9 of 50` against a README documenting *"41 pass · 9 xfail"*.
  Annotating them turns a red gate green.
- **Two `fux.toml` foot-guns**, both hit standing the environment up: appending
  `[sources.url]` is a duplicate-table error, and adding a key at the top of the
  existing table collides with `max_parallel` **25 lines below it**.

### Verified

`tests/` **2 183 passed, 1 skipped**. Playground restored and re-graded at
**41/50**, unchanged from before the run.


## The queue's backlog of moves, and five gates that were red (2026-08-27)

**A session with a working shell cleared what four Cowork sessions could not.**
The bridge had had no shell since 2026-08-26 (`device_bash` 5/5), so every item
below had been *decided* for a day or more and was waiting on `git`.

**Evidence:** `git log` for the moves;
[the daemon-lifecycle capture](regression/2026-08-27-daemon-lifecycle/report.md)
for the daemon; `uv run pytest -q tests` and `tests_e2e` for the gates.

### The measured starting point contradicted the queue

`OPEN-WORK.md` said **two** ADR tests were red. Locally, **twelve tests in five
groups** were. The queue was not wrong about the two it named; it had never seen
the other ten, because the sessions that filed it could not run the suite.

| group | why | outcome |
|---|---|---|
| ADR ownership + register (4) | `docs/adr/0047_fuxignore.md` was a stray duplicate of `0048` | `git rm` |
| doc links + registry (2) | five dead links, incl. two the register's own prose invented | repointed; the prose corrected |
| regression runs (4) | R10's directory holds a frozen pre-registration and **no report**, which the per-run contract made illegal | **ADR-RS decision 17** |
| tune specimen (1) | the matcher demanded `#key` on keys that Arpit's ruling had made **live lines** — *the test failed for the reason the change was made* | matcher fixed |
| ADR freshness (1) | see below | **ADR-OWNERSHIP decision 9** |

### The freshness gate convicted history and said in its docstring that it never would

`tests/test_adr_freshness.py` **ran here for the first time** and flagged eight
commits for not updating **ADR-CONFIDENCE**, **ADR-OUTPUT** and **ADR-RANKING**
— records and relations written on 2026-08-27, judging commits from weeks
earlier. The ownership table was read from the working tree.

- **Third occurrence.** `docs/adr/RULE-SINCE` records the other two: the
  ADR-CACHE carve-out (2026-08-21) and the register renumber (2026-08-22). Both
  times the remedy was moving the baseline forward — **retiring 95 commits of
  auditability to excuse a few.**
- **Fixed at the source instead**, per the two-strikes rule: the register is
  parsed **per commit** from `git show <sha>:docs/adr/README.md`. A row, a record
  or a relation that did not exist then does not judge now.
- **`RULE-SINCE` did not move**, and it now says so. A fourth entry means the fix
  failed — ADR-OWNERSHIP veto 6.
- **Three tests pin it**, one of them proving the gate *still bites*.

### The daemon runs — proven by a positive control, not a status read

The dead-sweep defect (`ingest_run.run` on a re-exported function, swallowed by
the broad handler) was fixed but unproven, and its unit gate patches a mock —
which cannot tell "the sweep called ingest" from "the sweep called the mock."

Run against a local HTTP server: `start` → sweep in ~1 s → **a page edited at
`15:11:21Z`, indexed by `15:12:04Z`, unassisted, one `sweep_minutes` later** →
`stop` → pid reaped, `write.lock` free. The indexed term exists **only** in the
fetched page and was absent beforehand.

⚠ **The network was `127.0.0.1`.** No proxy, TLS, SSO, rate limit or DNS —
**W-82 ruling 3's hold is NARROWED, not lifted**, and the recommendation is that
it stays held until one real external URL has been swept. ADR-MAINTENANCE 9c-i.

### A claim in the queue was wrong, and measurement is how that was found

`OPEN-WORK.md`: *"Four hook tests go green-by-vacuity without `fux` on `PATH`."*
Re-run with `PATH=/usr/bin:/bin` (git present, fux absent): **4 failed, 9
passed.** The four post-commit tests assert a term is findable afterwards and
fail hard. **Exactly one** passed vacuously —
`test_nothing_fux_spawned_outlives_its_own_run`, whose every assertion is that
something is ABSENT, which no `fux`-absent run can distinguish from success.
It now carries a positive control, and
`test_the_hook_environment_can_actually_find_fux` guards the whole class.

### Moved, deleted and reconciled

- **`git rm`**: `docs/adr/0047_fuxignore.md` (stray), `docs/adr/0017_enriched-mode.md`
  (superseded by ADR-ENRICH; register row deleted, every live citation repointed).
- **`git mv` to `archive/`**: `W-89`, `W-92`, `answer-provenance.md`,
  `output-toml-is-the-only-default.md`, `tune-file-and-source-priority.md`,
  `playground-goldens-draft.md` — six rows added to `archive/README.md`.
- **The register's §"the number line is contiguous" note was FALSE** and
  described a renumber that never ran and **must not** — it is the exact failure
  W-82 ruling 7 forbids, and it pointed at `0025_runtime-manifest.md` and
  `0042_locks.md`, **neither of which has ever existed**. `0017` and `0025` are
  burned ordinals, and the note now says why a hole costs nothing.
- **L8's one-line handle was stale in four live docs** — ADR-LAWS' §1 table,
  `INTERVIEW.md`, this file, and `compare/README.md` all carried the form Arpit
  **withdrew the same day he wrote it**. Reconciled to the live law. ⚠ **That is
  a reconciliation, not a ratification**; the sanity-check is still Arpit's.

### Verified

| suite | result |
|---|---|
| `tests/` | **2 170 passed, 1 skipped** (was 2 158 passed / 12 failed) |
| `tests_e2e/` | **74 passed, 1 skipped** — **macOS 15 / arm64 / CPython 3.14.2**, the second platform this suite has ever run on |

⚠ **Windows is still unverified**, and `test_maintenance.py` — real git, real
hooks, real detached processes — is the suite most likely to differ.


## W-93 — the skip list moves into the committed `.fux/.fuxignore` (2026-08-27)

**Built 2026-08-27 in two passes, and the first pass was wrong.**

**Pass 1** read Arpit's *"the skipped files should get added into `.fuxignore`,
not skipped"* as a diagnosis to check rather than an instruction. Checking was
right and the conclusion was not: `gitdir.walk_sources` records an *ignored* file
as skipped too, so materialising 599 paths would not have moved the count — and
that is true, but it answered a question he had not asked. What shipped was the
**count split** (decision 15), which was a real defect and beside his point.

**Pass 2** shipped what he asked for, after two questions instead of a third
inference. **Rulings (Arpit, 2026-08-27):** every ingest writes `.fuxignore` —
not an opt-in command, not inferred patterns — and **everything** goes in,
unreadable skips included.

**Evidence:** [ADR-FUXIGNORE](../docs/adr/0048_fuxignore.md) decision 11 and
11a–e; [ADR-INGEST](../docs/adr/0007_ingest.md) decisions 4 and 15, rewritten in
place. `src/fux/ingest/fuxignore.py` (`Generated`, `write_blocks`, `writable`,
`decide(hand_only=)`), `gitdir.py` (`would_index`, `_generated_kind`),
`skipnotice.py` (rewritten: the record is `.fuxignore`, plus `stale_warnings`).
**`tests/ingest` 316 passed.** No regression run, and none is owed — no
threshold, bound or gate ships here.

| shipped | where |
|---|---|
| two delimited blocks holding every unindexed path and why | `.fux/.fuxignore` |
| the blocks are written **first**, so any hand-written line beats them | `fuxignore.write_blocks` |
| the block a line sits in **is** its class | `BLOCK_NOT_INDEXED` / `BLOCK_SKIPPED` |
| the note is the reason that put the line there, carried across runs | `Verdict.reason()` |
| a hand-written pattern suppresses the lines it covers | `decide(hand_only=True)` |
| a stderr warning when a frozen line stops being true | `skipnotice.stale_warnings` |
| `.fux/runtime/skipped` deleted on every run | `skipnotice.legacy_path` |

**On this repo: 599 skips → 342 generated lines**, because the hand-written
`__pycache__/` and `*.py[cod]` collapse 257 of them.

⚠ **The accepted cost, stated before it was chosen and not undone: a generated
line DECIDES, so it freezes the verdict that produced it.** Widen
`.fux/sources/types` and the listed `.py` files stay out; write content into a
file listed as `empty` and it stays out. The escape hatches are a person's —
delete the line, or write `!<path>` below the blocks. The freeze is made loud
rather than removed.

⚠ **Two real losses, recorded rather than worked around.** A URL has no
repo-relative path, so a URL skip has nowhere to be recorded and **prints on
every networked run** — W-88's report-once promise now covers files only, and
repeat URL failure stays `url-state.json`'s job. And `fux ingest` now **writes
one of its own inputs**, so a new skip dirties the working tree on the hook path;
an unchanged run writes nothing, so steady state leaves `git status` quiet.

**Rejected:** inferred patterns (six lines rather than 342) — an inferred pattern
can over-reach onto a file the corpus does not have yet, and that failure is a
document silently missing, which is what ADR-FUXIGNORE exists to abolish. The
lever is left with the person instead.

⚠ **Not verified by `git` or the full suite.** `device_bash` failed 5/5, so the
build ran in the cloud container against a staged subset; `tests_e2e/` and the
ADR meta-suite did not run.

---

## W-93 pass 1 — `fux ingest` counts what it did not index in two numbers (2026-08-27)

**Built 2026-08-27, from one observation of Arpit's**: an ingest on this repo
printed `599 skipped` and his read was that those files *"should get added into
`.fuxignore`, not skipped"*.

**The proposed remedy would not have worked, and the code is the reason.**
`gitdir.walk_sources` records an *ignored* file as skipped too
(`skipped[rel] = verdict.reason()`), so moving 599 paths into `.fuxignore` only
changes the reason string — the count stays 599. Worse, per-file lines would
freeze a **derived** verdict: `not an indexed file type` comes from the type
allowlist, `.fuxignore` **outranks** the allowlist
([ADR-FUXIGNORE](../docs/adr/0048_fuxignore.md) decision 4), so 274 frozen
`.py` paths would silently survive the day a `.py` decoder or a `types` line
lands. Same class as the stale-premise failure `BLOCKED.json` is the case for.

**What the 599 actually were**, re-derived from `.fux/runtime/skipped`:

| count | what | verdict |
|---|---|---|
| 257 | `.pyc` under `archive/**/__pycache__/` | git already ignores them; fux walks them |
| 274 | `.py` under `archive/v0.1`, `archive/v0.26` | the allowlist working as designed |
| ~67 | `.sh` 24 · `.svg` 12 · `.log` 8 · `.jsonl` 5 · `.diff` 4 · `.png` 3 · `.out` 3 · misc | ditto |
| 1 | `binary` — a v0.26 test fixture | ditto |

547 of the 599 sit under `archive/`, which is `archived=true` in
`.fux/sources/dirs`.

**So the count was the defect, not the files.** One number spanned two
populations: *a committed list said no* and *fux could not read this*. Split
them and 599 becomes **598 not indexed, 1 skipped** — with nothing moved, no
rule changed and no byte touched.

**Evidence:** [ADR-INGEST](../docs/adr/0007_ingest.md) decision 15;
`src/fux/ingest/gitdir.py` (`POLICY` / `UNREADABLE`, `Skipped.kind`,
`partition`), `skipnotice.py` (`label`), `ingest/__init__.py` (the summary).
**14 new tests**, `tests/ingest` at **294 passed**. **No regression run, and
none is owed** — this change ships no threshold, bound or gate, and measures
nothing.

| shipped | where |
|---|---|
| a skip carries its class, set at the point of the skip | `gitdir.Skipped.kind` |
| the summary counts the two separately | `ingested … N not indexed, M skipped, …` |
| the printed line uses the summary's own word | `not indexed <path>` / `skip <path>` |
| `--list-skipped` and `.fux/runtime/skipped` **unchanged** — `path: reason`, sorted, unprefixed | the machine-readable twin things pipe |
| `__pycache__/` and `*.py[cod]` stated in `.fux/.fuxignore` | intent in a committed file |

⚠ **What the two `.fuxignore` lines do NOT do**, written down so nobody
re-derives it: they do not reduce the count (an ignored file is still a skip,
just a `POLICY` one) and they save no read (the allowlist already rejected
those files before any byte was read; `.fuxignore` filters files, it does not
prune the `rglob`). What they do is state the intent in a committed file and
keep it true if the allowlist ever widens.

⚠ **The open question this surfaced, deliberately not answered here:** fux's
walker reads **no `.gitignore`** and has no built-in prune, so it enumerates
257 untracked build artifacts on every run. Making `.fuxignore` prune the walk
would be a real saving **and** would conflict with the reported-never-silently-
dropped rule — an ignored directory's files would stop appearing in the skip
list at all. That is a fork with a verdict owed, not a patch. **Arpit's.**

⚠ **Not verified by `git` or by the full suite.** `device_bash` failed 5/5, so
the build ran in the cloud container against a staged subset;
`tests_e2e/` and the ADR meta-suite did not run here.

---

## W-91 — the provenance plane, and L8 reverted (2026-08-27)

**Built 2026-08-27, in one session, on Arpit's instruction to implement all four
phases and close out.** Fux now states **how the returned output got generated**
— the third statement about an answer, after *what it used* (the citation) and
*how much it believes it* ([ADR-CONFIDENCE](../docs/adr/0045_confidence.md)).

**Evidence:** [ADR-PROVENANCE](../docs/adr/0046_provenance.md) (`proposed`);
`src/fux/query/provenance.py`; `tests/query/test_provenance.py` — **29 tests
green**, 121 green across the staged subset. **No regression run, and none is
owed**: this change ships no threshold, bound or gate.

| shipped | surface |
|---|---|
| the derivation — matched terms with committed per-field counts, the four gates, the cut line, rerank and tune deltas | `fux ask --why` |
| the refer plane's own record, emitted at last | `fux answer --audit` |
| a re-runnable receipt — index digest · tune digest · engine · question · cited shas, **no wall clock** | `fux answer --receipt` |
| a local plaintext journal, **off by default** | `fux answer --journal` |
| four-state verification, config checked before corpus | `fux verify <receipt> [--rerun]` |
| three declared shapes | `query/output.schema.json` |

**The law change.** L8 was written the morning of 2026-08-27 (W-89, the row
below) and **reverted by Arpit the same afternoon**. Plaintext question *and*
answer are legal; the size bound became a design default; stdout is permitted.
**Committed paths and the network stay forbidden.** ⚠ The AOL-2006 grounding is
recorded as **overridden, not refuted**.

**Two defects in existing code, found and fixed here.** `fux answer --json` was
validated on one of three branches while its own declaration claimed all three
— W-84's defect class in a different file. And a receipt disagreed with its own
answer about freshness for one run, caught by running the command rather than by
a test.

⚠ **Not verified whole.** `device_bash` failed 5/5, so the work ran in the cloud
container against a staged subset. `tests_e2e/`, `test_adr_freshness.py` and
`test_doc_links.py` were never staged. **Nothing was committed.**

---

## W-89 — L8: the first law about *use* rather than about the corpus (2026-08-27)

**Ruled by Arpit, 2026-08-27.** W-89 asked whether **L2 reaches a query log**.
Three shapes were on the table — stretch L2, write a new law, or leave it a
product decision. **He chose the new law.**

**Evidence:** [ADR-LAWS](../docs/adr/0001_laws.md) decision 8 and its table row;
the normative text is in [`CLAUDE.md`](../CLAUDE.md) §Non-negotiable constraints,
edited in the same change as required by ADR-LAWS decision 4.
[ADR-QUALITY](../docs/adr/0044_quality-contract.md) decision 11 — the record that
declined to settle it — now names the answer. **No measured run: this is a
decision, not a measurement.**

> **L8** · *A use record never leaves the machine.*
>
> ⚠ **This handle changed on 2026-08-27, the day L8 was written**: it read *"What fux retains about use is hashed, bounded, and local"* until Arpit reverted the hashing, the size bound and the stdout prohibition hours later. Plaintext queries and answers are legal; what survives is the confinement. Read the law at its one home, `CLAUDE.md` §Non-negotiable constraints.

**What forced it.** The prohibition already existed as one ADR decision, and an
ADR is a thing another ADR may supersede. Two facts made that too thin:

| fact | found where |
|---|---|
| a durable use record **already exists** | [`maintain/lastcited.py`](../src/fux/maintain/lastcited.py) — 256 hashed question keys in `.fux/runtime/last-cited.json` |
| there is **live pressure to grow it** | [`work/proposals/ranking-tuning.md`](proposals/ranking-tuning.md) §8 — a per-repo query log as *"an asset fux gets for free"* |

**L8 landed green — it forbids nothing fux does today.** Verified against the
code before the law was written: hashed key (`sha256[:16]` of the normalised
query), `MAX_QUESTIONS = 256`, `.fux/runtime/` gitignored by name, stderr-only
so stdout stays byte-identical. No code changed.

⚠ **The honest limit, recorded in the ADR and repeated here.** A hashed key is
not anonymity: the *value* is the list of locators that answered, so the file
still says which documents are asked about and how often. Those locators are
already in the committed `M/` plane, so the file adds **frequency, not new
exposure** — L8 bounds it and keeps it off every shared surface, and does not
make it uninteresting. Grounded in the 2006 AOL search-log release, where
de-identified queries still identified a named individual.

⚠ **One hands-task outstanding:** `work/open/W-89-does-l2-reach-a-query-log.md`
still needs its `git mv` into `archive/open/` plus an `archive/README.md` row.
No agent has a shell — the sandbox bridge is down — so it is filed with the
other stray-file `git` operations in [`OPEN-WORK.md`](OPEN-WORK.md).

---

## W-88 — the skip notice: a skip is reported once (2026-08-27)

`fux ingest` reported every skipped file **on every run**. On a hook-driven
corpus that is tens to hundreds of identical lines each time, and Arpit's ask
was exact: *"showing it the first time is okay — showing it again and again is
not."*

**What shipped:** `src/fux/ingest/skipnotice.py` and one changed call site in
`ingest/__init__.py::ingest_and_report` — the single seam every verb already
prints through. The already-reported `(path, reason)` set lives in
`.fux/runtime/skipped`: derived, gitignored, sorted, **no wall clock**.

| property | how it is held |
|---|---|
| **no committed byte moves** | `test_suppression_never_moves_a_committed_byte` digests the shards either side of a suppressed run |
| a skip is never suppressed unseen | the notice is written *after* the unseen set is computed; a missing or corrupt file reads as *nothing reported yet* |
| a **changed reason** is news again | the key is `(path, reason)`, not the path |
| an offline run does not forget URL skips | `covers_urls=False` carries the URL entries forward — a plain `fux ingest` consults no URL, so it may not speak for that plane |
| `rm -rf .fux/runtime` stays safe | costs one repeat of the list; asserted, not assumed |

**What did NOT change:** the skip rules, the reasons, `--list-skipped`, or the
summary count — `N skipped` is still every skip. Only the enumeration is
suppressed, and the suppressed line names both ways to see it in full.

**Records:** [ADR-INGEST](../docs/adr/0007_ingest.md) decision 4 amended (it
owns `src/fux/ingest/`), [ADR-DOTFUX](../docs/adr/0003_fux-directory.md)
amended (`runtime/` gains a third derived file),
[ADR-CLI](../docs/adr/0002_cli-surface.md) annotated as describing-not-owning.
Reasoning archived at
[`archive/open/W-88-the-skip-notice.md`](../archive/open/W-88-the-skip-notice.md).

⚠ **Verification is partial and this is the honest statement of it.** 12 cases
in `tests/ingest/test_skipnotice.py`, green through a **stdlib harness** — the
build sandbox is Python 3.10 with no `pytest` and no network, so a `tomllib`
shim outside the repo stood in. **The `pytest` file itself and the rest of the
suite are unrun here.** `uv run pytest -q tests` on a real 3.11+ install is
owed before release.

---

## The record shape is declared once (2026-08-26)

`src/fux/store/index-record.json` declares every field of a committed
record; `store/recordshape.py` loads it; `store/writer.py` and `ingest/run.py`
read it instead of restating it.

**What it replaced agreed with itself only by habit** — the shape was assembled
inline **twice** in `ingest/run.py`, policed by `DISPLAY_FIELDS` in
`store/writer.py`, carried by `EXTRACTED_FIELDS` in `ingest/run.py`, and
described in prose by ADR-RECORD. **Nothing compared them.** Adding a display
field meant remembering a tuple in another module, and forgetting was silent:
the field shipped and L5's check did not look at it.

| property | how it is held |
|---|---|
| **no committed byte moved** | a test compares canonical encodings, not dicts |
| template key order is presentational | asserted — `canonical_dumps` sorts keys, and if that stops being true the template silently becomes a wire format |
| the template's `schema` equals `SCHEMA_ID` | two fux versions with different shapes must never both claim `fux.index.v2` |
| an undeclared field is refused by `build()` | a typo'd key used to reach the index and never be read again |
| `validate()` is **not** on the write path | asserted by a test, so the deliberate omission cannot rot into an assumption |

**Records:** ADR-INDEX-LIFECYCLE and ADR-INGEST amended in the same change.
**Verification:** 1 461 unit tests green (19 new).

## W-85 — `max_parallel` is required, never commented (2026-08-26)

**Arpit, ruling on W-83's output the same day:** *"I wanted a property exposed.
Where is that property? It should be present by default."* — then, shown the
commented line W-83 had written: **"never commented. If it is commented, throw
an error that the value has to be present."**

| what landed | where | outcome |
|---|---|---|
| **the key is required** — `[sources.url]` without `max_parallel` refuses to load, naming the line to paste | `config.py` | `UrlSource.max_parallel` has **no default**; the only key in `fux.toml` that does not |
| **the table ships live** — `[sources.url]` and its four keys uncommented | `setup.py` | the number is a number in the file, not a comment about one |
| **this repo's own `fux.toml`** updated by hand | `fux.toml` | nothing else could have — see below |
| doctor's `max_parallel unset` branch removed as unreachable | `doctor.py` | dead code that read like reassurance |

**W-83 shipped a config property to nobody who already had a `fux.toml`.**
`fux setup` is write-if-missing (ADR-DOTFUX), so a `_CONFIG` change reaches
**new repos only** — this repo's config still showed the pre-W-83 block when
Arpit opened it. **The general rule, now in ADR-DOTFUX:** if a template change
must reach existing repos, the mechanism is a **loader refusal or a `doctor`
check, never a rewrite** — a rewrite would eat a consumer's annotations, the
same reason `fux tune` prints a specimen instead of editing.

⚠ **One behaviour changed.** `fux add <URL>` used to record the line and print
*"no `[sources.url]` in fux.toml, so nothing can fetch this line yet"*; in a repo
scaffolded after this it fetches. **The gate moved to where it always really
was** — `.fux/sources/urls` is empty, and only an explicit `fux add` puts an
address in it. L4's *explicit, fenced, opt-in* is satisfied by the verb.

⚠ **A repo with no `[sources.url]` at all is exempt** and stays exempt: it
fetches nothing, so there is nothing to bound, and a required key there would
be noise.

**Records amended in the same change** (Law zero): ADR-CONFIG · ADR-DOTFUX.
**Item:** [`archive/open/W-85-…`](../archive/open/W-85-max-parallel-is-required.md).

**Verification: `tests/` 1 534 pass** under the same 3.10 shim; the two
`test_doctor` version failures are that shim, and the other five name a
concurrent session's files (`src/fux/schema.py`, `W-86`, ADR-GRAPH,
ADR-MAINTENANCE, `test_schemas.py`). ⚠ **`tests_e2e/` unverified**, same cause.
⚠ **Not committed**, same reason as W-83.

---

## W-83 — the unconfigured fetch ceiling (2026-08-26)

**Arpit:** the number of parallel requests `fux update` / `fux add <URL>` /
`fux ingest --refresh-urls` may open must be a stated property in `fux.toml`,
*"otherwise it'll become one of a DDoS attack."*

| what landed | where | outcome |
|---|---|---|
| **the unconfigured ceiling** — `resolve_parallel(module, None)` returns `min(declared, DEFAULT_MAX_PARALLEL)` | `ingest/urlsrc.py` | the constant had existed since §3.3 **referenced by nothing**; an unconfigured run inherited `http.py`'s declared `8` |
| **the knob in `fux.toml`** — `max_parallel` written into the commented `[sources.url]` block, number **interpolated** from the constant | `setup.py` | it was readable by `config.py` and named by nothing a consumer would open |
| **the policy in `fux doctor`** — the URL section says how many will be opened and where the number came from | `doctor.py` | reports policy only; **never imports the consumer's fetcher** to read `MAX_PARALLEL` off it |

**The finding worth carrying, and it is not the feature.** ADR-CONFIG's W-82
amendment **already specified** *"default `4` when a fetcher declares more"* —
while stating four paragraphs earlier that *"`None` means whatever the fetcher
declares."* **Two sentences in one amendment, contradicting each other**, and
the code implemented the wrong one. So this was **the code being brought into
line with a record that already had it right**, not a change against a record.

⚠ **The governance gap that surfaced and is NOT fixed.** `test_adr_freshness`
checks that an owning record was *touched*, never that it is *coherent*. A
record can be amended and self-contradicting in the same commit and every
mechanical check passes.

**Records amended in the same change** (Law zero): ADR-CONFIG · ADR-FETCHER ·
ADR-DOTFUX. **Item:**
[`archive/open/W-83-…`](../archive/open/W-83-the-unconfigured-fetch-ceiling.md).

**Verification: 1 484 unit tests pass**, **11 of them new** (3 on what silence
means, 3 on the written `fux.toml`, 5 on doctor). ⚠ **The total is not
attributable to this item alone** — a concurrent session was adding tests to the
same tree while this ran, which is why the count is reported and the *new* count
is enumerated.

⚠ **Four failures remain and none belongs to this change**, checked by name:
two are the **3.10 harness shim** (the build environment has no 3.11+
interpreter, so `fux doctor` correctly reports `3.10 < 3.11`), and two name the
other session's files — `test_adr_freshness` flags **ADR-INGEST** and
**ADR-INDEX-LIFECYCLE** over `ingest/run.py` and `store/`, and `test_doc_links`
flags a `W-84` file this session did not create.
⚠ **`tests_e2e/` unverified**, same shim cause, unchanged from W-82.
⚠ **Not committed** — staging was left to whoever commits next, because
re-staging mid-flight across another live session is the hazard CLAUDE.md names.

---

## W-82 §3.1-§3.6 — five phases of the consolidated build (2026-08-26)

| what landed | where | outcome |
|---|---|---|
| **§3.1 the URL health report** — `fux doctor` gains a URL section; `fail_streak` in `.fux/runtime/url-state.json` | `maintain/urlstate.py`, `doctor.py`, `ingest/run.py` | doctor had **no URL check at all**; report-never-delete, per ADR-URL-INGEST decision 4 |
| **§3.2 the detector** — the refer plane records a `url:` doc id when `fetched_sha != indexed_sha` | `refer/__init__.py` | **closes the recall loop**: a changed URL now gets its terms corrected instead of silently ceasing to rank |
| **§3.3 parallel fetch + the cap** — `MAX_PARALLEL` declared capability, `min(declared, configured)` | `ingest/urlsrc.py`, `config.py`, both fetcher templates | first threading in `src/fux/`; **stdlib, so L1 untouched**; invisible to L3 because the trailing sort, not the loop, is what makes the index deterministic |
| **§3.4 the changed/unchanged line** — the last answer's cited `(loc, sha)` set | `maintain/lastcited.py`, `query/__init__.py` | **a report, not a memo**: no answer stored, nothing replayed, stderr-only so stdout stays byte-identical |
| **§3.6 the agent surface** — `fux-usage` skill and the four-rung invocation ladder | `templates/agents/USAGE-SKILL.md` + 2 renderings, `setup.py` | closes a **live silent defect**: an unactivated `.venv` read as *not installed* and sent agents to grep |

**Records amended in the same change** (Law zero): ADR-DOTFUX · ADR-INGEST ·
ADR-REFER · ADR-MAINTENANCE · ADR-ANSWER · ADR-ASK · ADR-AGENT-POLICY ·
ADR-FETCHER · ADR-CONFIG.

**Verification: 1 433 unit tests green**, up from 1 335.
⚠ **`tests_e2e/` is UNVERIFIED** — it spawns the real CLI and fails identically
(55/11) on a clean tree in the build environment, so the change introduces no
regression and *green* is not a claim available from here.
⚠ **§3.0 and §3.5 did not land**, and neither is a code task: §3.0 needs a real
URL corpus, §3.5 needs `fux-playground`. Neither exists on this machine.

## Milestones

| milestone | shipped | release | closed by | outcome |
|---|---|---|---|---|
| **P1 — the pruning gate** | 2026-08-09 | — | [P1-GATE](regression/2026-08-09-pruning-eval/VERDICT.md) | **INCONCLUSIVE**, and correctly refused. Top-128 was a no-op for 97 %+ of documents on all three corpora — their median vocabulary is 32–46 distinct terms. [Run](regression/2026-08-09-pruning-eval/) |
| **P1 — the re-run** | 2026-08-09 | — | [P1-RERUN](regression/2026-08-09-pruning-rerun/VERDICT.md) | **FAIL.** Five selectors at matched retention; best arm 35.9 pts below unpruned recall@20 at 6 % retention. Option E accepted: the committed index carries **full postings, permanently**. A negative that ended the pruning design. [Run](regression/2026-08-09-pruning-rerun/) |
| **M0 — scaffold** | 2026-08-11 | `v0.30.0` | [ADR-RECORD](../archive/adr/0004_index-format.md) | `src/fux/` package, `fux --version`, `fux doctor`. |
| **M1 — the T0 vertical slice** | 2026-08-11 | `v0.30.0` | [ADR-RECORD](../archive/adr/0004_index-format.md) | Canonical committed store, git-dir ingest, scan-based `fux ask`. **R1 PASS · R2 2/3 PASS** at the time; the third was blocked on a doc-hygiene gap, not the engine. |
| **`.fux/` becomes a declared layout** | 2026-08-11 | *(0.31.x, never published)* | [ADR-DOTFUX](../archive/adr/0011_fux-dir-layout.md) | Every child declared committed or derived; URL source moved inside; `fux doctor` now asserts `git check-ignore` on the index — the ignore rule was the silent failure mode. |
| **URL ingestion via consumer middleware** | 2026-08-10 | *(0.31.x, never published)* | [ADR-URL-INGEST](../archive/adr/0010_url-source-consumer-middleware.md) | `src:"url"`, hashed-meta default, offline carry-forward. `src/fux/` still holds zero network lines — the adapter cap survived by making fetch *configuration plus consumer code*. |
| **The demo corpus leaves the repo** | 2026-08-12 | *(0.31.x, never published)* | [SETUP-PLAYGROUND](setup/fux-playground.md) | `examples/` deleted; graded `fux-playground` sibling with 50 ranked goldens — **41 pass / 9 named `xfail`**. |
| **R2 closes** | 2026-08-12 | — | [ADR-RECORD](../archive/adr/0004_index-format.md) §Consequences | **3/3 PASS** on this repo's own corpus, after adding `archive/v0.26-docs` to configured sources; index +45.1 %. Post-hoc finding filed as [W-44](../archive/open/W-44-archived-content-signalling.md), not solved. [Run](regression/2026-08-12-r2-close/report.md) |
| **M2 — the T1 accelerator** | 2026-08-12 | `v0.32.0` (PyPI 2026-08-13) | [ADR-T1-ACCELERATOR](../archive/adr/0005_derived-accelerator.md) | **R3 PASS** — worst-case warm p95 **27.2 ms** on 8 870 RFCs against a pre-registered 150 ms bar, where the reference scan takes 4 248.8 ms. Differential law byte-identical over 6 088 comparisons plus all 50 goldens. **Hybrid fusion measured net −6 and ships default-off.** [Run](regression/2026-08-12-m2-accelerator/report.md) ⚠ **Superseded 2026-08-25: the dense lane, the embedding model and `--hybrid` were DELETED** (Arpit). This row is kept as the build log it is — what was true when it was written — and is NOT a description of the engine today. See the model-removal row below. |
| **W-54 — the sources rewrite** | 2026-08-19 | `v0.33.0` (PyPI 2026-08-19, verified black-box from the published wheel) | [ADR-URL-LIST](../docs/adr/0018_url-list.md) · [ADR-DIR-LIST](../docs/adr/0022_dir-list.md) · [ADR-FETCHER](../docs/adr/0019_fetcher.md) · [ADR-HTTP-FETCHER](../docs/adr/0021_http-fetcher.md) · [ADR-INDEX-LIFECYCLE](../docs/adr/0009_index-lifecycle.md) 9 | **Five latent defects closed in five commits.** One parser for both committed source lists; `#` is a comment only at line start or after whitespace, so a URL fragment survives and two fragment-differing URLs are two documents rather than one silent deletion. `[sources] dirs` retired into `.fux/sources/dirs` with a declared `archived=` (parsed, not read — the *signal* stays gated on W-44). `fux setup` writes both fetchers from wheel package data, so `DEFAULT_FETCHER` names a file that exists and `ensure_layout` never puts code in a repo that wanted an index. **`title_h` gained an `h:` prefix**, which is the one with measured cost: under the L5 `hashed` default, ingest wrote an index no `fux build` would accept — 27.2 ms became 4 248.8 ms at RFC scale. `fux url` makes the list tool-managed and **never fetches**. [Run](regression/2026-08-19-w54/report.md) — the differential now holds over a corpus containing hashed records, **which the harness had never seen**, and that gap is why the defect survived |
| **M3 — the graph lane** | 2026-08-20 | `v0.34.0` (PyPI 2026-08-21) | [ADR-GRAPH](../docs/adr/0029_graph.md) | **Landed, with two named gaps it does not paper over.** `explain`/`graph`/`path`; edges lifted into two adjacency views (directed for routes, undirected for relatedness, **tag nodes are sinks** so a route cannot launder through a shared label); communities by **unseeded** label propagation — the randomness is *removed*, not seeded, and a test parses the module's AST to assert no `random` import — canonicalised to `c0`, `c1`, … by (size, smallest member) so adding a document cannot rename an unchanged partition; communities live in a **derived** plane because a label is global and committing it would turn a one-file commit into a corpus-wide diff. **The archived relational eval passes on the new kernel, 11/11**, its corpus copied into `tests_e2e/eval/` as a live fixture with its one vocabulary adaptation stated. **`ask` is byte-identical and asserted so through the CLI.** One deliberate correction to the port: the PPR walk is **lazy**, because the archived walk truncated at 3 iterations ranks by *parity* — seeded at `a` on a path `a-b-c-d` it scored `d` (3 hops) at 0.154 above `c` (2 hops) at 0.054. **The two gaps: the playground acceptance targets are unmeasured and determinism is verified on one machine, not two** — both carried by [W-57](../archive/open/W-57-graph-lane-acceptance.md), blocked by [W-56](../archive/open/W-56-sibling-environments-missing.md) |
| **M4 — the refer plane (core)** | 2026-08-20 | `v0.34.0` (PyPI 2026-08-21) | [ADR-REFER](../docs/adr/0030_refer-plane.md) — **⏳ proposed at landing; `accepted` 2026-08-21** (`9f8366e`, veto condition 2 still open) | **The core landed; the gate did not run, and the record says `proposed` because of it.** Six modules, 73 tests: `source` · `freshness` · `arc` · `chunk` · `rescore` · `assemble`. **Fux still does not fetch** — the plane reuses ADR-FETCHER's consumer-owned `fetch(url) -> str` contract, injected never imported, and an AST test asserts no `urllib`/`socket`/`http`/`ssl` import across all seven modules. **Two design changes forced by facts found while building.** (1) **`max_age_seconds` was refused, not deferred**: the graduating proposal measured age "against the ledger's recorded provenance", and there is none — the record carries `sha` and a revision counter `ver`, no time, and `runtime/stamp.json`'s mtimes are excluded from byte-identity precisely because they are not reproducible. Shipping the knob would have shipped one that silently does nothing. Freshness is instead a mode (`never`/`always`) plus **content verification** — comparing shas, which answers the question exactly rather than approximately, and reads no clock ([W-58](../archive/open/W-58-no-recorded-ingest-time.md)). (2) The assembler grew a **floor**: greedy score-per-byte is systematically biased toward short passages (50 B at score 3 = 0.060/B beats 400 B at score 8 = 0.020/B), so the best answer is seated first by absolute score. **The ARC differential caught a real defect while being written** — the cache-hit path wrote `"note": "cache hit"` into the bundle, so cache state leaked into the answer. **What is not claimed: R4, the budget sweep, and ARC-vs-LRU are all unmeasured** — [W-59](../archive/open/W-59-refer-plane-measurement.md), blocked by [W-56](../archive/open/W-56-sibling-environments-missing.md). No verb exposes the plane, deliberately |

## Defects closed outside a milestone

**Not milestones either.** A defect found by walking a surface, fixed on its
own, has no milestone row to live in — but rule 2 of
[`OPEN-WORK.md`](OPEN-WORK.md) still forbids deleting its item until the
outcome is recorded here.

| item | closed | closed by | outcome |
|---|---|---|---|
| **[W-86 CLOSED](../archive/open/W-86-the-decoder-plane.md)** — the decoder plane, complete | 2026-08-26 | [ADR-DECODE](../docs/adr/0042_decode.md) · amends [ADR-EXTRACTED](../docs/adr/0016_extracted-mode.md) · [ADR-INGEST](../docs/adr/0007_ingest.md) · [ADR-FETCHER](../docs/adr/0019_fetcher.md) · [ADR-MAINTENANCE](../docs/adr/0032_hooks.md) · [ADR-DOTFUX](../docs/adr/0003_fux-directory.md) · [ADR-TYPES](../docs/adr/0031_types-list.md) · [ADR-AGENT-POLICY](../docs/adr/0035_agent-policy.md) | **All nine phases built; ten forks ruled or dissolved.** ⚠ **P0 — a defect that had been shipping since the type allowlist existed.** `extract.py` derived headings with `^#{1,6}` alone while `DEFAULT_TYPES` admitted `.rst`, `.adoc` and `.org` — **three of six allowed types had EVERY heading land in the body field**, with an empty `phrases` list feeding the `§` lines `fux ask` renders. Each format now gets its own grammar; two guards are the substance rather than the regexes — **Org requires the space** after the asterisk run (or `*emphasis*` reads as a heading) and **reStructuredText requires a full-width rule** (or a row of dashes in a table becomes one). A decoded document always uses the Markdown grammar, because decoders emit Markdown by contract. **⚠ Re-ranks existing corpora, in the direction the field weights intend.** ⚠ **P8 — `fetch(url) -> tuple[bytes, str]`.** A fetcher did two jobs, and `http.py:43` stated the consequence as a rule nothing enforced: *"which fetcher retrieved a document would change the committed index"* — **L3 as a code comment**. Both fetchers and both templates stopped converting; `PREPEND_TITLE_HEADING` moved to the decoder, where it belongs. Type resolution is **declared first, path second, never sniffed**. ⚠ **A bare `str` return is still accepted as a deliberate transition ramp** — every pre-2026-08-26 consumer fetcher returns markdown, and the break was **never re-costed** (ADR-FETCHER's *"no external consumers"* line is dated v0.32.0 and predates the PyPI release); the ramp is what makes that acceptable, not a measurement. ⚠ **P6 — the queue, and a race that was reproduced before it was fixed.** `acquire()` had **one caller**; a foreground `fux ingest` evicted the background runner and then wrote **holding nothing**. `runner.lock` → **`write.lock`**, and `ingest`/`build`/`add`/`remove`/`update` all pass through `write_lock()`; **read verbs take nothing**, since a lock on the read path would fail a search because a re-index was running. **`acquire(required=True)` raises where `acquire()` returns False** — the same line meant opposite things to a runner (decline quietly) and a writer (never proceed unprotected), and `except OSError: degrade` was right for one and inverted for the other. **The queue** (`.fux/enrich/queue.tsv`, committed; `runtime/enrich-progress.tsv`, gitignored) is the first thing in fux that can **say** a document needs a model — `fux enrich` derives scope from a declared `dirs` line and cannot know a `.png` exists. Sorted, no clock, paths+shas+reason, never content. ⚠ **Nothing consumes it yet — that is fork G, still open.** **Diagrams:** both architecture SVGs updated and a third, `work/architecture-decoders.svg`, added. **`tests/` 1 698 green.** ⚠ **`tests_e2e/` unverified** (3.10 sandbox). ⚠ **Not committed** — a concurrent session holds files staged |
| **[W-86 P7b](../archive/open/W-86-the-decoder-plane.md)** — the `fux-decoder` skill | 2026-08-26 | [ADR-DECODE](../docs/adr/0042_decode.md) decision 12 · [ADR-AGENT-POLICY](../docs/adr/0035_agent-policy.md) | **Arpit asked how a custom decoder is built, and the answer lived only in a module docstring and in ADR-DECODE §2 — the agent-facing half of a record, which is not where a consumer looks.** New `templates/agents/DECODER-SKILL.md`, rendered to `.claude/skills/fux-decoder/` and `.kiro/skills/fux-decoder/`, **never to an ambient surface** because it writes committed Python that changes what is indexed. **Vendor choice follows ADR-ENRICH decision 10's REASONING rather than its vendor list**: that decision made `fux-enrich` claude-only because the other two renderings were ambient, and W-82 3.6 established a Kiro *skill* is progressive-disclosure while only Kiro *steering* is ambient — so Kiro is admitted and Copilot's `instructions/` still excluded. **Exempt from the verbatim policy-block check** and the third name on that escape hatch (after ENRICH-SKILL and USAGE-SKILL); the exemption is pinned by `test_the_exemptions_are_deliberate`, so widening it stays a decision rather than the cheapest way to fix a red test. **The skill carries reasoning, not just a recipe** (Arpit: *"always add some documentation on how it is built, and pointers"*): the contract with a why per rule, the four judgement calls where decoders actually go wrong, the shared-helper table, and a pointer table naming which shipped decoder to read for which shape of format. ⚠ **Its verification section is the load-bearing part** — decode a real file and READ it, because all four P2-P5 defects produced plausible text rather than an error. **`tests/` 1 637 green.** ⚠ Not committed |
| **[W-86 P7](../archive/open/W-86-the-decoder-plane.md)** — setup exports every decoder | 2026-08-26 | [ADR-DECODE](../docs/adr/0042_decode.md) decision 11 · [ADR-DOTFUX](../docs/adr/0003_fux-directory.md) | **Arpit overruled the item's own recommendation and the record says so.** §13.4 argued *seam yes, export-all no*; he ruled `fux setup` writes **all sixteen** decoders into `.fux/decoders/` and **the copy is what runs**, on the argument that a consumer invited to override decoders should be able to read them in their own repo. Two middles offered and declined: `fux decoder eject <name>`, and a hash-stamped *inert-until-edited* variant. ⚠ **The cost, taken knowingly: after setup, `src/fux/decode/` does not execute in that repo** — engine upgrades reach nobody's decoders, and each of the four P2-P5 defects would have needed every consumer to refresh by hand. **Two mechanism findings, neither a policy choice:** (1) **imports inside `decode/` had to become absolute** — a path-loaded file has no parent package, so `from . import _xml` raises and **every copy carrying a helper import would have been dead on arrival**; absolute imports make the shipped bytes and the edited bytes identical, asserted by a byte-identity test; (2) **no `.py.txt` template**, and the asymmetry with fetchers is principled — a fetcher's extension is un-importable because it holds network code that must not live inside an offline package, while a decoder is stdlib-only and offline and therefore already a legitimate module, so the module **is** the template and a second copy under `templates/` would be the `_MdParser` defect sixteen times over. **A deleted copy falls back to the built-in** — `rm pdfdoc.py` must not look identical to a corpus with no PDFs. `fuxdir.DECLARED` gains `decoders`, so `fux doctor` does not warn. ⚠ **Caught by an existing guard rather than shipped:** `.fux/README.md` is encoded ASCII for Windows consoles, so an em-dash in the new description failed the write immediately. **8 new tests; `tests/` 1 631 green.** This repo now carries its own sixteen copies. ⚠ Not committed — concurrent session live |
| **[W-86 P2–P5](../archive/open/W-86-the-decoder-plane.md)** — every decoder | 2026-08-26 | [ADR-DECODE](../docs/adr/0042_decode.md) decision 10 | **16 built-in decoders, 30 extensions, all stdlib** — HTML, `.eml`, JSON, `.ipynb`, TOML, INI/`.properties`, CSV/TSV, XML, YAML (subset), `.docx`, `.pptx`, `.xlsx`, ODF, RTF, `.drawio`, PDF — plus three shared private modules: `_zip.py` (bomb caps, **sorted** members, numeric slide/sheet ordering), `_xml.py` (**a DOCTYPE is refused outright**, closing billion-laughs and XXE in one rule), `_ooxml.py` (run assembly, table rendering). **Four defects found in the build, each of which produces plausible garbage rather than an error:** (1) **ODF text sits directly on `text:p`**, not in run elements — reusing `_ooxml.paragraph_text` made **an entire format decode to nothing, silently**, caught only because a fixture was decoded by hand; (2) `slide10.xml` sorts before `slide2.xml`, so lexical member order gives a deck that is deterministic **and wrong**, which is worse than noisy because nothing looks broken; (3) OOXML **table cells are paragraphs too**, so without an in-table check every cell's `tf` doubles; (4) joining Word runs **with a space** turns *"runbook"* — which Word splits whenever a spell-checker touches it — into two terms nobody types. **PDF is scanned for `stream…endstream`, NOT parsed through the xref**: a conformant reader needs xref tables, object streams and compressed xref streams, all three of which fail on exactly the malformed files a real corpus holds, and scanning finds text a strict reader refuses. ⚠ **Stated cost:** `ToUnicode` CMaps are merged across all fonts, so a document with two subset fonts disagreeing on one byte gets one wrong — reading per-font maps needs the object graph this approach avoids. **A PDF with no text layer returns `None`** — the queue signal, distinguished from a text layer that fails to *parse*, which is a decode failure. **JSON keys sorted** (two exports ordered differently must decode identically, L3); **YAML aliases read once, never expanded** (a *conformant* parser inflates `tf`); **notebook outputs dropped** (re-execution artifacts make the index depend on who hit Run). **59 decoder tests; `tests/` 1 623 green.** ⚠ Not committed — concurrent session live |
| **[W-86 P1](../archive/open/W-86-the-decoder-plane.md)** — the decoder plane | 2026-08-26 | [ADR-DECODE](../docs/adr/0042_decode.md) · amends [ADR-INGEST](../docs/adr/0007_ingest.md) · [ADR-FETCHER](../docs/adr/0019_fetcher.md) · [ADR-HTTP-FETCHER](../docs/adr/0021_http-fetcher.md) · [ADR-CDP-FETCHER](../docs/adr/0020_cdp-fetcher.md) | **The plane already existed and was duplicated FOUR times, not twice** — `.fux/fetchers/http.py`, `cdp.py`, **and both wheel templates**, which are what `fux setup` writes into every new consumer's repo, so the duplication was **shipped**. `http.py`'s docstring stated the consequence as a rule nothing enforced: *"which fetcher retrieved a document would change the committed index"* — **L3 as a code comment**. ⚠ **ADR-HTTP-FETCHER decision 7 claimed a test that did not exist**: it read *"a test asserts the two agree on the same input"*, and the cited test asserted determinism and heading handling, never agreement. A record asserting a guarantee its own cited test does not check, standing since 2026-08-19. New `src/fux/decode/` with `htmldoc.py` **lifted verbatim** (behaviour preserved deliberately — any difference would silently re-rank every URL-sourced document already committed). `parse_document(content, rel_path, root)` is the new seam and returns `None` for an unreadable document; **`parse(content)` is unchanged**, so no existing corpus moves. `_skip_reason` now consults the registry **before** judging bytes — *"binary"* stopped being a sufficient reason to skip the moment a `.docx` became a document. Parsing moved **above** `file_shas` so an unreadable file contributes no sha (a sha with no record makes the reuse map claim a document the index lacks). **Protocol ruled by Arpit: bytes default, path opt-in** (`WANTS_PATH`), override **by module name** not by extension, `BUILTIN_MODULES` an explicit sorted tuple never a directory scan (L3). **A missing consumer dependency is a hard error naming the module** — detection would let two machines commit different indexes from identical sources. `DecodeFailed` is deliberately **not** a `FuxError`. ⚠ **`DEFAULT_TYPES` UNCHANGED** — ADR-TYPES verdict G was measured. **20 new tests, `tests/` 1 566 green.** ⚠ `tests_e2e/` unverified (Python 3.10 sandbox); the two `test_doctor.py` failures are that shim and predate this change. ⚠ **Not committed** — a concurrent session was live in the tree |
| **[W-84](../archive/open/W-84-heading-level-ask.md)** — `ask` cites at heading level | 2026-08-26 | [ADR-ASK](../docs/adr/0004_ask.md) decision 10 · [ADR-MCP](../docs/adr/0039_mcp.md) decision 9 | **The refusal is half the outcome.** Arpit asked whether `ask` should cite lines; it may not. A line range on `ask` could only be computed at **ingest**, so one edit makes it point at the wrong lines *while looking exactly as right as before* — the defect class of `max_age_seconds` and of a `cached` verdict reported as `current`. It also costs a positional index (2–4× the postings, Zobel & Moffat 2006 §5) against an index whose whole pitch is that it fits in git, and its value is thinnest where the cost is highest: `file:` sources are already in the working tree, `url:` sources are the ones most likely to have changed since ingest. **`answer` cites lines because it fetched the bytes and cites their sha.** What shipped instead was already committed: `phrases` — the document's headings, extracted at ingest since M2 and rendered by **`answer --no-refer` alone**. New `src/fux/query/headings.py` selects the ones matching the query (shared analyzer, scored by count of *distinct* query terms, zeros dropped, sorted `(-matches, document position)`, capped at 3) and `fux ask` renders them as indented `§` lines, `ask/find --json` as an always-present `"headings"` array, and MCP `fux_search` in its result rows. **`fux find`'s piped stdout is byte-identical** — a `§` on it would be read as a filename ([ADR-DIR-LIST](../docs/adr/0022_dir-list.md) decision 12's argument). **Display-only**, run on the already-unified list after `run_query` returns, exactly where `_resolve_title` runs under P5, so no seam exists for the differential law to break through — re-verified on this repo, `diff` of the two paths is `IDENTICAL` with headings present. ⚠ **A live defect found on the way:** `fux_search`'s **MCP tool description** claimed *"line-range citations"* and `_search` has never returned one — the identical wrong claim `ad95a24` had fixed in `docs/guide.html` and the usage skills **earlier the same day**, surviving in the machine-facing copy, where it is worse: an agent acts on a tool description with no human reading the output beside it. Corrected and pinned by a test. **Tool descriptions are documentation compiled into the package and no gate reads them** — `fux_passage`'s and `fux_related`'s remain unchecked. **21 new tests, `tests/` 1 500 green.** ⚠ **`tests_e2e/` unverified** (Python 3.10 sandbox, `tomllib` shim that never enters the repo — the two `test_doctor.py` failures are that shim, and predate this change). ⚠ **Not committed** — a concurrent session was mid-rename in the tree (`store/recordshape.py` → `recordschema.py`) and a W-84 commit would have swept it in |
| **[W-63](../archive/open/W-63-source-verbs.md)** — the source verbs | 2026-08-21 | `v0.35.0` (PyPI 2026-08-21, verified black-box from the published wheel) | [ADR-CLI](../docs/adr/0002_cli-surface.md) 1a-1e · [ADR-INGEST](../docs/adr/0007_ingest.md) 9-10 · [ADR-DIR-LIST](../docs/adr/0022_dir-list.md) 2d-2e, 3a · [the capture](regression/2026-08-21-source-verbs/report.md) | **The corpus finally has a command.** `fux add` / `fux remove` / `fux update` over all three committed source lists, dispatching on the entry — anything with a `scheme://` is a URL, `--types` says type pattern, everything else is a path, and a path may be a directory **or a single document**, which the list always accepted and no command ever wrote. `add` ingests by default and **fetches the one URL it just added**, announcing on stderr; `remove` deletes the line or, for a path held only by a listed ancestor, **subtracts it with `!`** and says which branch it took; `update` re-reads what is listed and **never writes a line**, which is the one sentence that keeps three verbs from overlapping. `fux url` deleted outright (four days old, pre-1.0); `ingest --refresh-urls` hidden for one release. **Two defects fixed first, both real independent of the verbs.** A de-listed URL used to survive an offline ingest, so **deleting a document required the network it has no use for** — reconciliation reads a committed file and now runs on every ingest, while the transient-failure guarantee (a *still-listed* URL whose fetch fails keeps its record) is untouched, because one keys on the list and the other on the fetch. And a carried `url:` record kept edges resolved against a **previous** run's corpus, so a removed document survived as a target in the derived graph plane; every carried record's edges are re-checked against the run's own id set. Both verified by mutation — reinstating either turns the new tests red. **Capturing the surface found four more defects the unit suite did not**, three of them in W-63 itself, and every one did something defensible while *saying* something false: an L4 announcement that fired with nothing fetched; `add '*.pdf' --types` **silently un-indexing every markdown document** (the types file replaces the built-in allowlist rather than extending it — W-55's invisible filter from a new direction); a type-allowlist skip reported as a failed fetch; and `explain` answering for a document not in the index. All fixed, all written up in [ANALYSIS](regression/2026-08-21-source-verbs/ANALYSIS.md). **L4's text did not change** — it already read *paths*, plural; what was wrong was the nine records and eleven docstrings that narrowed it to `--refresh-urls`, and those were corrected rather than the law restated. `src/fux/sources.py` re-owned from ADR-URL-LIST to ADR-CLI in the same change |
| **[W-64](../archive/open/W-64-progress-plane.md)** — a progress plane for the write verbs | 2026-08-21 | [ADR-CLI](../docs/adr/0002_cli-surface.md) decision 9 · [the capture](regression/2026-08-21-progress-plane/report.md) | **Built and captured; not a milestone and not a gate.** `src/fux/progress.py` — stdlib, stderr-only, TTY-gated, count-based, threshold-gated at ~200, and **clock-free**: no `time` import, no elapsed, no ETA, no rate, because ingest is a maintenance path. Seven phases across `ingest.run()` (`walk`/`extract`/`edges`/`write`) and `derive.build()` (`read`/`codes`/`graph`/`postings`), reported through a `progress=None` keyword that **means silent, so no existing caller or test changed** — which is what kept this small. `main` builds **one** `Progress` and hands it to both, so an `ingest` that also builds is one continuous sequence rather than two bars fighting for a line. **The invariant is a test, not an intention**: `tests_e2e/test_progress_surface.py` runs each write verb twice, with and without `--progress`, and asserts stdout is byte-identical — a leak there would corrupt the `--json` contract every agent consumer reads. **Found while capturing, and fixed in the same change:** a phase whose total is not documents must name its unit, or `write`'s `252/252` sitting under `edges`' `1203/1203` reads as losing 950 documents. **The one open call was decided on its stated default** rather than stalling: the git hooks export `FUX_NO_PROGRESS=0` and show the bar, reversible in one line if [W-61](../archive/open/W-61-maintenance-measurement.md)'s fork lands on B. ⚠ **What is not claimed: repaint cost at R5's 100 000 documents.** This ran at 1 203; the bar is a write plus a flush per document, and that is [W-26](../archive/open/W-26-m6-scale-t2.md)'s to measure, not this row's to assume |
| **the Windows console class, gated** — `fux add` crashed on a rejected file | 2026-08-21 | `35eeae0` · [ADR-CLI](../docs/adr/0002_cli-surface.md) consequence + veto 7 | **Second occurrence of the class, so it became a check in the change that recorded it** (CLAUDE.md's two-strikes rule). `fux add` on a file the type allowlist rejects printed `→` (U+2192); `cp1252` cannot encode it, so `print()` raised `UnicodeEncodeError` and the verb exited non-zero. **Both Windows CI arms went red on the `v0.35.0` release commit; every POSIX arm and every local run was green** — the first occurrence was `fux doctor`'s checkmarks at `v0.30.0`. `tests/test_windows_console_safe.py` parses every module under `src/fux/` and refuses a non-cp1252 character in any string reaching `print()`, `FuxError()` or `.write()`. **Scoped to streaming calls, not all string literals**, because the first version flagged `store/canonical.py` and `ingest/urlsrc.py` for holding U+2028/U+2029/U+0085 as the sentinels they strip — a guard that flags the code defending against a character is one people learn to switch off. One test skipped on Windows: there is no SIGINT to deliver to another pid there. |
| **the prediction series, reopened** — R4, R5, R6 measured | 2026-08-20 | [R4-REFER](regression/2026-08-20-refer-plane-r4/VERDICT.md) · [R5-HOOK](regression/2026-08-20-r5-hook-latency/VERDICT.md) · [R6-MERGE](regression/2026-08-20-r6-merge-driver/VERDICT.md) | **Arpit lifted the hold; three gates ran the same day, and two of them did not pass.** Pre-registrations frozen and committed first (`d98874d`) — thresholds, judged arms, judged corpus size, statistic, verdict tables. **R4 PASS**: cold k=10 p95 **1.113 s** / 3 s, warm **0.016 s** / 300 ms, through the *shipped* consumer fetcher against a loopback server. Its verdict carries its own boundary: the plane fetches **serially**, so cold cost is `k ×` the source's latency — the 500 ms arm breaches at 5.069 s, and paper §8's "(k=10, parallel)" is not built. **R5 FAIL**: **44.4 s** at the judged 100 000 documents against a **1 s** bound, **0.651 s at 1 000** where it passes. Attributed rather than left as *it is slow* — git is ~constant (0.34 s at 100k) and two O(corpus) passes are the whole cost, 51.5 % ingest / 47.6 % derive, **so a 10× speedup still misses by 4.5×**. Delta ingest had already taken the per-document half; what is left is parse-everything, resolve-every-edge, write-every-shard. **R6 INCONCLUSIVE, and the engine is not the reason**: every tier matched, tiers 2 and 3 informatively against a control arm run with the driver unregistered — adjacency does not conflict, and a same-`ver` disagreement is **refused with both sides left in the file**. Tier 1 merged cleanly *without* the driver, so it proves nothing, and the frozen table does not cover "all match, some informative". **The control arm justified itself on its first execution.** ⚠ **Two decisions now sit with Arpit**: the fork R5 opened ([`hook-at-scale.compare.md`](compare/hook-at-scale.compare.md), proposed **B — the hook defers**) and R6's arithmetic. ⚠ **Nothing was tuned to pass**: `src/` last changed in `3a9aabc`, before the pre-registrations |

| **delta ingest** — full re-extraction was the measured bottleneck | 2026-08-20 | [ADR-INGEST](../docs/adr/0007_ingest.md) decision **1b** · [ADR-CLI](../docs/adr/0002_cli-surface.md) | **A veto condition fired and was honoured in the same change.** ADR-INGEST said re-extraction happens every run and named the measurement that would reopen it; the [cost profile](regression/2026-08-20-ingest-cost-profile/report.md) supplied it — **92 % of a full ingest is `_fuxvec_code`**, the dense embedding, at 1 k and 5 k documents alike, with parse and edge resolution together under 5 %. **The split is between what the corpus can change and what it cannot.** Edges are corpus-wide — a new document resolves a link that dangled yesterday — so they re-resolve every run, unchanged. Extraction depends on nothing but one document's own bytes, which the record's `sha` pins, so an unchanged document keeps the `title`, `phrases`, `terms`, `wlen` and `code` it already had. Result: **22.7× at 1 000 docs, 26.4× at 5 000, byte-identical** — asserted on shard digests after an edit, an addition and a deletion, each against the full run's own output, never a hand-written expectation. Gated on three conditions together: the sha matches, the record is `file:` with `meta: plain`, and the shard header still equals `store.HEADER` — the last of these is what stops **two analyzers inside one index**, which would be undetectable afterwards. ⚠ **Two guarantees are narrower now, and are recorded rather than hidden**: term-hash collision detection is complete only under `fux ingest --full`, because a carried-forward document contributes hashes that cannot be un-hashed; and a newly available embedding bundle does not retro-fit `code` onto documents that have not changed. ⚠ **This is not R5.** It makes R5 reachable at corpus sizes where it was not; the gate itself is held ([W-61](../archive/open/W-61-maintenance-measurement.md)) |

| **W-60** — the TTL fetch cache | 2026-08-20 | [ADR-REFER](../docs/adr/0030_refer-plane.md) 5a-5c, 6 | **Built to Arpit's verdict F.** A gitignored `.fux/runtime/fetch-cache/`, keyed by `loc`, with a real `fetched_at` — **off by default** (`cache_ttl_seconds = 0`), opt-in per caller, and a `no_cache` escape hatch that wins regardless. **Not a latency optimisation**: Confluence Cloud's REST API is rate-limited against a shared hourly budget, so ten questions about one runbook must not be ten fetches — at scale that is throttling, and a throttled fetch degrades to `unverified` for reasons that have nothing to do with the document. **Two separations carry the design.** The TTL store is **not** ARC's: ARC is keyed `(loc, sha)` so a hit is provably the right bytes, while a TTL entry is served *before* the sha is confirmed — sharing a keyspace would cost that proof with no test to notice. And **wall clock lives here and nowhere else**, the same treatment `stamp.json` gets: derived, per-machine, never reaching a committed record, so **decision 4 and [W-58](../archive/open/W-58-no-recorded-ingest-time.md) are untouched**. `cached` is a **fourth verdict**, never folded into `current` — it carries `age_seconds` and still records whether the bytes matched the index. A `git:` document is never TTL-cached: a local read is free, so caching it would buy a staleness window for nothing. **One honest gap recorded as a veto condition**: a permission revoked at the source is not observed until the entry expires, and nothing detects it — `no_cache` is a policy set in advance, not something the engine notices |

| **M5 — maintenance (core)** | 2026-08-20 | `v0.34.0` (PyPI 2026-08-21) | [ADR-MAINTENANCE](../docs/adr/0032_hooks.md) — **⏳ proposed, deliberately** | **Built; both gates unrun, so the record is not accepted.** Three pieces. **Hooks:** `post-commit`/`post-merge` re-ingest, `post-checkout` rebuilds the derived plane; all best-effort, none can block a commit, and installation **refuses rather than clobbers** a hook fux did not write. **`post-commit`, not `pre-commit`** — pre-commit reads the *working* tree, so with `git add -p` it would index bytes nobody committed and write that into the commit: **wrong**, where a post-commit index is merely **late**, and the lag is visible. **The merge driver:** line-wise last-writer-wins on `(ver, sha)` over `.fux/index/*.jsonl`, output sorted by id so two machines merge to the same bytes. It **refuses in four cases** — same `ver` different bytes, delete-vs-modify, both-added-differently, header change — writing ordinary conflict markers that keep both sides and naming the fix. **Verified by control and treatment**: the same merge conflicts without the driver and merges cleanly with it. **L5 at write time:** the hashed-meta rule moved out of `ingest/run.py` (one caller) into `write_index` (the only way bytes reach a shard), checked per record before any shard is touched. **The existing corpus already complied**, so it landed without changing a committed byte. One honest limitation found by running it: **git does not invoke a content merge driver for an add/add**, and that is documented rather than worked around. ⚠ **R5 and R6 are unrun** — the harness exists, and Arpit held prediction runs on 2026-08-20 — [W-61](../archive/open/W-61-maintenance-measurement.md) |
| **[W-61](../archive/open/W-61-maintenance-measurement.md)** — M5's two gates, ruled | 2026-08-22 | [ADR-MAINTENANCE](../docs/adr/0032_hooks.md) **accepted** · [ADR-MERGE-DRIVER](../docs/adr/0033_merge-driver.md) **accepted** · [the fork's verdict](compare/hook-at-scale.compare.md) | **Both gates closed by ruling, and neither by a passing re-measurement — which is the honest description.** **R5's fork:** Arpit ruled **B — the hook defers**, in its *detached-runner* variant: `post-commit` writes a **dirty list** of the changed documents, spawns a **one-shot** re-index that exits, and returns; commit cost becomes git's cost, **constant in the corpus**. Checked against [`maintenance-trigger.compare.md`](compare/maintenance-trigger.compare.md), which is `accepted` and rejected a watch **daemon** — the objection does not transfer to a process that exits, and that doc's own consequences had left a later layer open. **A list rather than a flag** is the deliberate part: it is exactly the input option **D** consumes, so D becomes a later increment instead of a rewrite — and D is **deferred, not rejected**, because at 50 000 documents its 4× speedup no longer reaches the bound while B stays constant. **`fux ask` now declares the pending count** (stderr, ASCII, never a gate), which is what keeps the widened index/tree window honest rather than silent. **R6:** adjudicated **PASS** under the pre-registration's §3.1, tier 1 dropped as uninformative and the record carried by tiers 2 and 3. ⚠ **Two debts, both named rather than absorbed:** the filed R6-MERGE verdict still reads INCONCLUSIVE and was **not edited** — the ruling is an addendum beside it — and **§3.1 still contradicts §3.2**, so ADR-MERGE-DRIVER is accepted on a *reading*, with [W-67](../archive/open/W-67-r6-instrument-repair.md) owing the repair and a re-run, and its veto 5 set to return the record to `proposed` if the repair overturns the reading. ⚠ **No code shipped in this change** — the build is [W-66](../archive/open/W-66-deferred-hook.md), and ADR-MAINTENANCE is accepted for the *decision* while the behaviour it describes is still unbuilt |
| **[W-66](../archive/open/W-66-deferred-hook.md) Phases 1+3** — the dirty list, and `ask`'s pending declaration | 2026-08-22 | [ADR-MAINTENANCE](../docs/adr/0032_hooks.md) · [ADR-INGEST](../docs/adr/0007_ingest.md) | **The Sonnet-executable slices of the ruling above, built; the Opus slice deliberately not attempted.** `src/fux/maintain/dirty.py` — a gitignored, newline-delimited union under `.fux/runtime/dirty`; `post-commit` appends via `git diff-tree --root` (correct on the repo's first commit too) *before* its still-synchronous `fux ingest` call; `ingest/run.py::run()` clears it only after `write_index` succeeds, so a run that dies partway leaves the list intact. **Advisory, asserted rather than argued**: `test_ingest_is_byte_identical_regardless_of_the_dirty_list` runs the same corpus through present/absent/stale/corrupt list states and diffs the shard bytes. `fux ask` declares a non-empty pending count on **stderr** only (`query/__init__.py::_declare_pending`), ASCII, proven not to touch the `--json`/stdout contract by a byte-comparison test. **What is not here, on purpose:** Phase 2 (the detached one-shot runner and its single-writer lock) — [W-66](../archive/open/W-66-deferred-hook.md)'s own model line assigns it to Opus, because a silent, rare, cross-platform spawn/lock failure corrupts the index rather than raising an exception; and Phase 4 (the `fux doctor`/`--json` runner status), which cannot report on a lock that does not exist yet. `uv run pytest -q tests tests_e2e`: 1040 passed |
| **[W-44](../archive/open/W-44-archived-content-signalling.md)'s demotion weight** — a configurable, no-op-by-default score multiplier for archived directories | 2026-08-22 | [ADR-ARCHIVED-CONTENT](../docs/adr/0037_archived-content.md) decision 6 · [ADR-ASK](../docs/adr/0004_ask.md) · [ADR-CONFIG](../docs/adr/0014_config.md) · [ADR-T1-ACCELERATOR](../docs/adr/0011_accelerator.md) | **Built to the 2026-08-22 ruling that reconciled "archived docs demoted" with the earlier "ranking never reorders."** `[ranking] archived_weight` in `fux.toml` — default `1.0`, rejecting negatives, non-numbers and bools explicitly (`bool` is an `int` subclass in Python, so `= true` would otherwise silently parse as `1`). `ingest/gitdir.py::archived_dirs()` reads the existing `archived=true` declaration ADR-DIR-LIST already parses (decision 4 stands: never a path convention). Applied in `query/rank.py::rank()` — **the one function both the scan and the accelerator funnel through**, so the differential law carries the demotion down both candidate-generation paths for free rather than needing to be kept in step by hand; at the default the multiply is skipped outright, not merely a no-op multiply, which is the stronger of the two byte-identity guarantees the item's own DoD asked for. **Two tests, not one, as required**: `tests/query/test_scan.py` asserts byte-identical results at the default *and* a live document overtaking an archived one once a weight is configured; `tests_e2e/test_verbs.py::test_archived_weight_demotes_only_when_configured` proves the same through the shipped CLI. **What is not here, on purpose:** the per-record `archived` property, the `[archived]` marker and the response-level disclaimer (ADR-ARCHIVED-CONTENT decisions 1/3/7) — gated on a pre-registered live-vs-archived query set that does not exist yet, per the 2026-08-19/2026-08-22 rulings on file. `uv run pytest -q tests tests_e2e`: 1040 passed |

| **[W-66](../archive/open/W-66-deferred-hook.md)** — the deferring hook, all four phases | 2026-08-22 | [ADR-MAINTENANCE](../docs/adr/0032_hooks.md) 1a–1d · [ADR-DOTFUX](../docs/adr/0003_fux-directory.md) · [ADR-INGEST](../docs/adr/0007_ingest.md) · [ADR-CLI](../docs/adr/0002_cli-surface.md) | **`post-commit` stopped waiting.** It records HEAD's paths into a gitignored dirty list, spawns a **detached one-shot** re-index, and returns — commit cost is git's cost and **constant in the corpus**, asserted end to end at 50 vs 800 documents, which is veto condition 5 in the words the record uses. `src/fux/maintain/runner.py`: an `O_CREAT|O_EXCL` pid lock (a 50-commit rebase produces **one** runner, and a second spawn exits quietly because the list is a union), a **cooperative** stop polled only *before* `write_index` (a stopped run leaves a byte-clean index and an untouched list — veto 8), and takeover on the single `ingest_and_report` seam so every write verb stops a runner before writing. `fux ingest --stop` exits **0** with nothing running. `fux doctor` reports the runner and **gained `--json`**, read-only, asserted byte-identical against held *and* stale locks in the file ADR-MAINTENANCE's veto-7 check names. **Three things the design did not anticipate.** (1) **`os.kill(pid, 0)` terminates a process on Windows** — CPython routes it through `TerminateProcess`, so the POSIX liveness idiom kills what it probes; `is_alive` uses `OpenProcess`/`WaitForSingleObject` and a test reads the source to keep it so. This is precisely the silent, rare, someone-else's-OS failure the phase was assigned to Opus for. (2) An **flock would have made stale locks impossible and was rejected** — it is held by a file descriptor nothing outside the process can name, and decision 1c needs the state *reportable*; the cost is a lock a killed runner leaves behind, answered by reporting and takeover rather than by a process silently deciding a lock is dead. (3) The dirty list is emptied by **subtracting a start-time snapshot**, never cleared, or a commit landing mid-run is silently dropped — so `dirty.clear` was removed outright and a test asserts it does not exist. Phase 1's shell pipeline (`cat`/`sed`/`sort`/`mv`) moved into Python as `record_head`: the part of a `#!/bin/sh` hook most likely to differ under git-for-windows, and untestable where it was. `uv run pytest -q tests tests_e2e`: 1101 passed |
| **[W-67](../archive/open/W-67-r6-instrument-repair.md)** — R6's instrument repaired, and re-run | 2026-08-22 | [R6-MERGE-RERUN](regression/2026-08-22-r6-rerun/VERDICT.md) **PASS** · [ADR-MERGE-DRIVER](../docs/adr/0033_merge-driver.md) | **ADR-MERGE-DRIVER no longer rests on a reading.** It was accepted 2026-08-22 on Arpit's adjudication of a contradictory instrument; the repaired instrument now returns a clean **PASS**. Tier 1 re-specified to select its two added documents **by hashing into one shard** is informative at last — the control arm conflicts, the treatment merges — so both machine tiers count and the verdict comes off the `PASS` row rather than a human reading. Veto 2 marked **SPENT**, veto 5 **did not fire** (the §3.1 reading survived the repair), and a new **veto 6** fires if a future run lands on `PARTIAL`. **The repair is a new instrument, not an edit.** `PRE-REGISTRATION-R6-v2.md` restates the threshold character for character and adds the row the old table lacked — *all tiers match, exactly one informative* — which **routes to Arpit rather than resolving**, so the session writing it gained nothing either way. The 2026-08-20 pre-registration and the filed R6-MERGE verdict are **byte-untouched**. ⚠ **One DoD box left unticked deliberately**: that item told this change to repair §3.1/§3.2 *and* a dead link inside the frozen file, while also saying the frozen file is never edited. The safer branch was taken and the departure is written into the item — Arpit's to overrule. ⚠ **Weaker evidence chain than the original**, declared before the run: the pre-registration could not be committed alone (a concurrent session held the tree), so `git log` cannot evidence the ordering; what substitutes is that tier 1's definition was **promoted verbatim** from a `tier1b` already in git history. **Finding kept rather than tidied**: most concurrent adds land in different shards and need no driver at all — the old tier 1 survives as an *unjudged* arm that shows it |
| **[W-65](../archive/open/W-65-design-point-reconciliation.md)** — the record set reconciled to 10 000 documents | 2026-08-22 | *(no ADR — it edits many records' prose; **no ADR affected** for the engine)* | **Fourteen live documents were still asserting a design point Arpit retired on 2026-08-21**, and a stale record reads as authority. All relabelled — **including four the item's own table never named**, found by re-deriving the grep it told the reader to re-derive: `wire-format.compare.md` carried a live reopen trigger keyed to `≤300 MB @1M` **and** to P2, retired with plan revision 1 (unreachable twice over); `index-format.compare.md`, the **accepted** committed-format decision, is sized only at 100k and 1M with no row at the design point; `work/proposals/ideal/` (5 files) was filed the *same day* the design point moved and already carried the old one; and `docs/adr/README.md`'s worked veto example was teaching every new record to key its vetoes to `≥100k-doc` — a size nothing will measure, i.e. the very "event nobody waits for" that section forbids. **Two live veto scripts** (ADR-POSTINGS, ADR-INDEX-LIFECYCLE) were still running a check described as `<= 250 MB packed @100k`; both now say the budget is retired with no successor and that re-deriving it is Arpit's, so nobody reads a pass or a fail off them. **ADR-POSTINGS was the one flagged to think hardest about, and it held**: doc-major is argued from a *structural* property — a posting list is keyed by term, so a one-word edit rewrites every line for every word it contains, at any corpus size — so the scale clause was **removed rather than divided by ten**, and the check that was actually run is written into the record. **One genuine finding**: `pruning-criterion`'s Bloom-plane elimination is stated as *"≈2.4 GB at 10⁶ docs, ruled out on arithmetic"*, and that becomes **~24 MB at 10⁴**, which nobody would rule out on size; the elimination survives on the **scale-invariant ratio** (11.69 bits/posting against 6.15), and that is now what the document says. Its §2 premise — *"the committed index is only small if most postings can be discarded"* — is simply **false at 10 000 documents**, where pruned and unpruned differ by single-digit megabytes; that makes P1's FAIL cheaper to obey and reopens nothing |
| **W-68** — `fux setup` installs the agent policy | 2026-08-22 | [ADR-AGENT-POLICY](../docs/adr/0035_agent-policy.md) **accepted** · [ADR-DOTFUX](../docs/adr/0003_fux-directory.md) · [ADR-CLI](../docs/adr/0002_cli-surface.md) | **Fux now ships the policy its consumers need in order to read its output correctly** — the half of the product that was missing while the engine emitted a fact no agent knew how to interpret. `setup.py` writes four renderings from `templates/agents/` (Claude skill · Copilot **agent** · Copilot ambient **instructions** · Kiro steering), **all three agents by default** on Arpit's call, with `[agents] install = ["claude", "copilot", "kiro"]` **spelled out in full** in `fux.toml` — the same visible-default pattern the type allowlist already used, which is what lets *install-by-default* and *declared-never-derived* both hold at once. **23 tests, and they assert the vetoes rather than the happy path**: every path outside `.fux/` is announced *and* so is how to turn it off (the announcement is the only safeguard left once opt-in is gone); `--no-agents` and `install = []` write nothing and leave **no vendor directory behind**; a consumer's edit survives a later `setup`; an unknown agent name is a loud error; `absent` and `empty` are different; and **the installer never branches on a vendor directory existing** — asserted directly, because sniffing for `.kiro/` is the derivation ADR-DIR-LIST decision 4 refused. The four renderings carry the eight rules as a **verbatim block**, so agreement across vendors is an exact match rather than a judgement — a shape forced by a failure on the check's first run, when the renderings said the same thing in different words. ⚠ **What is not claimed:** no agent has been observed obeying the policy. Fux can guarantee every agent was *told the same thing*; it cannot verify compliance, and veto 2 (a rendering that stops loading in its vendor's tool) has **no command** — it is a quarterly read of four vendor URLs, and it already fired once during authoring when GitHub moved from instructions to agents |
| **the 10 000-document ceiling, and two retired promises** | 2026-08-22 | *(scope ruling — [CLAUDE.md](../CLAUDE.md) §Litmus; **no ADR affected**)* | **Arpit closed 50 000 and 100 000 to measurement *and to commitment* until the tool is built out.** Two predictions were withdrawn rather than re-derived: **R7** (committed-index size, whose budget died with the old design point and which had been sitting blocked on a number only Arpit could pick) and **R8** (a graph-verb bound at 100 000, never registered). **The distinction the ruling turns on, and the one a later session must not blur:** a *promise* about a size Fux is not building for is removed; a *measurement already taken* at that size is untouched. **R5's 44.4 s at 100 000 stands exactly as filed**, its frozen pre-registration is not edited, and the tests and CHANGELOG entries that cite it as history are left alone — that number is why `post-commit` defers, and deleting it would delete the reason. **No feature was removed** (Arpit: *"keep them, they are going to be helpful either way"*), and the size checks in ADR-POSTINGS and ADR-INDEX-LIFECYCLE survive as **measurements with no threshold** — print the number, read no verdict off it. ⚠ **Two things this bought immediately:** W-26's last box dissolved with R7, and the queue's inbox dropped from three items to one |
| **[W-38](../archive/open/W-38-m8-deferred.md)** — M8's deferred set, dropped | 2026-08-22 | *(no ADR — nothing was built; **no ADR affected**)* | **Removed from the queue on Arpit's instruction. Dropped, not completed** — nothing in M8's deferred set was built, measured, or decided against; it stops being counted as pending. **The row is here because rule 3 requires an outcome before a row is deleted, and "dropped" is an outcome** — recording it as done would be a lie, and recording nothing would make the item look like it never existed. ⚠ **Its standing law was re-homed, not dropped with it**: *"pruning work is forbidden outside a dedicated item"* now lives in [ADR-POSTINGS](../docs/adr/0013_postings.md) §Consequences, where it belongs — it is a consequence of [P1-RERUN](regression/2026-08-09-pruning-rerun/VERDICT.md)'s measured **35.9-point recall loss**, not a scheduling preference, and deleting the row would otherwise have retired a constraint that a measurement paid for |
| **[W-26](../archive/open/W-26-m6-scale-t2.md)** — M6's tier question, answered: **T2 is not built** | 2026-08-22 | [R9-T2-AT-10K](regression/2026-08-22-r9-t2-at-10k/VERDICT.md) **PASS** · [the T2 proposal](proposals/t2-segments.md) (new, accepted) | **The largest thing in M6 was measured and declined.** T2 — `tpack` plus mmap byte-aligned segments — was scoped for this milestone and reserved a name a milestone in advance. R9 puts warm worst-case p95 at **12.46 ms on 10 000 documents against a 150 ms bar**, **12× inside**, so it is not built. **The bar is R3's own, reused verbatim rather than re-derived**: choosing a fresh number having already seen R3's 27.2 ms is the inversion the pre-registration rule exists to stop, and `graph-plane-format.compare.md` had recommended exactly this precedent. **R3's number could not itself be used as evidence** — its corpus was lost with the lab (W-56) — so this is a **new baseline, not a confirmation**. `the T2 proposal` is accepted as the record of a **decision not to build**, with a reopen condition that is **a number rather than a size**, so 50 000 documents *crossing* the bar reopens it and 50 000 documents *arriving* does not. The `[index] tier` knob is deliberately **still** not created — it has never existed in code, so *"tier-auto flips by measurement"* was governing an unbuilt mechanism. **The paper's §5–§6 are rewritten from projection to measurement**, with the 10⁶ figures relabelled as deferred-target projections rather than deleted; the abstract, §1.3's `~250 B/doc` and P1 claims, and §8's P2/P3 rows were corrected in the same pass. ⚠ **The caveat is the corpus**, declared in the pre-registration *before* the run as the likeliest problem: it is synthetic, **18× lighter per document** than R3's and with 37× fewer distinct terms. The judged quantity survives it — the accelerator is `df`-bound (1 000 → 1.25 ms, 10 000 → 12.46 ms, linear in document count) where the *scan* is bytes-bound and shows the full 170× gap — and a post-hoc density correction lands within 15 % of R3. **That is a consistency argument, not a measurement on real prose at 10 000 documents, which does not exist and is recorded as owed.** ⚠ **Two boxes remain, both Arpit's and both filed**: R7's budget re-derivation, and whether §4's *architectural* staleness (it describes an MST keyspace `index-format.compare.md` superseded) is in scope |
| **W-68** — `fux setup` installs the agent policy | 2026-08-22 | [ADR-AGENT-POLICY](../docs/adr/0035_agent-policy.md) **accepted** · [ADR-DOTFUX](../docs/adr/0003_fux-directory.md) · [ADR-CLI](../docs/adr/0002_cli-surface.md) · [ADR-CONFIG](../docs/adr/0014_config.md) | **Fux now ships the policy its readers need to read it correctly, and installs it by default.** Four renderings — a Claude skill, a Copilot agent, Copilot ambient instructions, Kiro steering — written into `.claude/`, `.github/` and `.kiro/`, which belong to **Anthropic, GitHub and AWS**. `[agents] install` is a validated closed set in `fux.toml`, **written out in full** by setup on the same reasoning `setup.py` already applies to the type allowlist: a default a user can read and edit in a file they own is a different thing from a default buried in the engine. An unknown vendor name is a **loud error**, because the failure mode of a typo is the worst kind — the file someone asked for is never written and nothing says so. **The two safeguards a default-on install needs are asserted rather than intended.** Every path outside `.fux/` is named in setup's output together with both escapes (`install = []`, `--no-agents`) — veto 1, and with the install default-on that announcement is the *entire* remaining safeguard. Both escapes write **no file and no vendor directory** — veto 1a; the directory half was worth testing separately, because a bare `.github/` fux created and did not fill is still fux writing into GitHub's namespace. Agreement across the five files is **exact match on a shared block** (veto 3), the two **ambient** renderings — on every prompt in a consumer's repo, forever — are size-bounded (veto 5), and the routing is asserted by source inspection to contain no `exists()`/`glob()`, keeping it **declared, never sniffed** (veto 4). ⚠ **Veto 6 was tried as a test and deliberately withdrawn**: the first version flagged `SKILL.md` for naming a document in a worked example, which decision 2 explicitly permits and the record itself prints. **A check that fires on correct content trains people to switch it off** — the same lesson `test_windows_console_safe.py` paid for when it flagged the code defending against a character — so veto 6 stays a prose judgement, and the withdrawal is written into the test file rather than left as a silent gap. `uv run pytest -q tests tests_e2e`: 1137 passed |
| **[W-26](../archive/open/W-26-m6-scale-t2.md)'s last box** — the R7 fork, written up rather than guessed | 2026-08-22 | `r7-size-budget.compare.md` (archived 2026-08-25) ⏳ awaiting Arpit | **Not a build — a fork filed the way the lifecycle says to file one.** W-26's remaining box is R7's size budget, and its own re-scope box says the re-derivation is Arpit's if it is not obvious. It is not: the question turned out to be not *what number* but **what kind of number**. Five shapes compared — an absolute at 10k, a **ratio to the indexed corpus**, a per-document allowance, a clone-time bound, and retiring R7. **Proposed: the ratio**, because an absolute is frozen against a corpus size and therefore dies whenever the design point moves — which has now happened twice (10⁶ → 10⁵ → 10⁴) — and re-deriving it is this exercise all over again at 50 000. **The number is deliberately left blank**, and that split is the point: the shape is derivable by someone who has never seen a fux measurement, the number is not, and the author had already seen it. Proposing `≤100 %` would propose a threshold the engine passes; `≤50 %` one it fails. ⚠ **A finding nothing had stated: the committed index is LARGER than the content it indexes** — 141 % of corpus bytes synthetic, **211 %** on this repo's real prose (23 % / 76 % packed). 91.3 % of it is `terms` as hex-string JSON keys, which is precisely what ADR-POSTINGS' unbuilt encoding exists to fix. ⚠ **R7's consumer changed and nobody had recorded it**: it gated T2, T2 was declined on latency, and what it gates now is **ADR-POSTINGS** — so retiring R7 was considered and rejected |
| **W-56** — the measuring environments, rebuilt | 2026-08-20 | *(no ADR — they are outside this repo)* · [SETUP-LAB](setup/fux-lab.md) · [SETUP-PLAYGROUND](setup/fux-playground.md) | **Both rebuilt from their setup docs, and both are now git repositories — which neither was, and which is exactly why they were lost.** `fux-lab`: `TEST-PLAN.md` with §0b, a **seeded** corpus generator verified byte-identical across two runs, an eval harness that drives the real CLI by subprocess and gates on quality only, `new-env.sh`, and a `smoke` environment run end to end (hit@5 1.0, MRR 1.0). Three bugs found by *running* it rather than reading it: `read -r A B < <(...)` returns non-zero at EOF without a trailing newline so `set -e` exited silently with no output at all; the system `python3` here is **3.9** and fux needs ≥3.11, which surfaces as a pip error listing every version ever published and reads like a packaging fault; and the harness reported **its own** interpreter beside the latency rather than the engine's (3.9 vs 3.14). `fux-playground`: the 10-document Calder Group / Helix corpus, `check.py` (rank-graded, **no `--update-goldens`**, XPASS fails the run), and `--index-guard` — **passing**, which is a determinism test on real content rather than a fixture. **The ~50 ranked goldens were deliberately NOT rebuilt**: a golden derived from the engine's own output passes forever, including on the day ranking breaks. ⚠ **Every baseline and every corpus behind them is unrecoverable** — `rfc` (8 872 docs, the corpus **R3's 27.2 ms was measured on**), `acme`, `orbit`, `1k`/`5k`/`10k`. A corpus generated now is a *different* corpus, so a number taken now is a new baseline and not a confirmation; the M2 report's reproduce block is annotated to say so rather than edited, because editing a filed run's evidence is itself forbidden |

| **W-45 + W-55** — what fux indexes | 2026-08-20 | [ADR-DIR-LIST](../docs/adr/0022_dir-list.md) 2a-2c · [ADR-TYPES](../docs/adr/0031_types-list.md) (new) | **Both verdicts built as one grammar change**, because they modify one file format. W-45 (**E**): `.fux/sources/dirs` accepts `!` exclusion entries — repo-relative globs removing a path and everything beneath it, order-independent, no un-exclude, no attributes. **Not the attribute the record anticipated**: the attribute grammar describes properties of the thing on the line, and two exclusions would have needed a comma sub-grammar the format has never had. W-55 (**G**): a compiled-in prose allowlist (`*.md`/`*.markdown`/`*.txt`/`*.rst`/`*.adoc`/`*.org`) replaced — not extended — by an optional `.fux/sources/types`; **absent means the default**, and a types file with no positive pattern is a loud error rather than a silently empty index. `*` does not cross a `/` (`fnmatch` would have made `work/regression/*/evidence` match `.../a/b/evidence`), so the matcher is hand-rolled. The three conditions are a **conjunction**, so there is no precedence to get wrong, and **every rejection is reported with its reason** — an invisible filter is what both items were opened about. **Measured before building: 33 of 150 documents (22.0 %) came from `work/regression/`, and 21 of 150 (14 %, 15 % of tokens) were not prose.** ⚠ **This is a ranking change and is unmeasured** — this repo's committed index was deliberately **not** re-ingested, so the corpus change stays a separate measured step alongside [W-52](../archive/open/W-52-df-over-the-union.md) |

| **W-46** — `ask --hybrid` crashed on a source install | 2026-08-20 | [ADR-CLI](../docs/adr/0002_cli-surface.md) | **Fixed.** `get_model()` returns `None` where the embedding bundle is not shipped, and `None.embed(...)` raised an `AttributeError` the guard's deliberately narrow tuple did not list — so the fallback written for exactly this case was **dead code from the day it was written**. Fixed with an explicit `None` check, not a widened `except`: widening would have swallowed every real bug inside `embed()`, which is the silent degradation the narrow tuple exists to prevent. Both halves asserted in `tests/derive/test_dense_and_hybrid.py` — the `None` path degrades to lexical at exit 0, a present-but-broken model still raises. **It survived because it cannot reproduce where `model.bin` exists, which is every development machine**, and `--hybrid` is default-off so nothing routine walked it. Diagnosis: [run](regression/2026-08-18-cli-surface/ANALYSIS.md) ⚠ **Superseded 2026-08-25: the dense lane, the embedding model and `--hybrid` were DELETED** (Arpit). This row is kept as the build log it is — what was true when it was written — and is NOT a description of the engine today. See the model-removal row below. |
| **W-48** — three output-contract inconsistencies across the query verbs | 2026-08-20 | [ADR-ASK](../docs/adr/0004_ask.md) · [ADR-ANSWER](../docs/adr/0006_answer.md) · [ADR-FIND](../docs/adr/0005_find.md) | **Two fixed, one deliberately not.** `ask --json --explain` now carries `"path"`, so which lane answered a slow query is readable by the caller that would log it; the key is emitted only under `--explain`, so the default payload stays byte-identical and the differential law through the CLI is untouched. `answer --json` now carries `"source": "index"` on the no-match branch, closing a trap in the very key ADR-ANSWER tells callers to switch on for the M4 upgrade. **Item 3 — `find`'s prose no-match line on stdout — was examined and left alone**, and is now *pinned by a test* so the decision is visible rather than merely remembered: the three verbs say the same thing for the same condition, and ADR-FIND ties reopening it to a real script observed breaking on it. Diagnosis: [run](regression/2026-08-18-query-verbs/ANALYSIS.md) |
| **PRIORITY P5** — materialise-first display for `hashed` records | 2026-08-21 | `1ba9be1` · [ADR-RECORD](../docs/adr/0010_index-record.md) · [ADR-INDEX-LIFECYCLE](../docs/adr/0009_index-lifecycle.md) · [ADR-INGEST](../docs/adr/0007_ingest.md) · [ADR-ASK](../docs/adr/0004_ask.md) · [ADR-REFER](../docs/adr/0030_refer-plane.md) | **Built to five direct rulings from Arpit, not assumed.** Ingest already holds a non-git document's bytes before writing its record, so it now also writes the title to a new gitignored, `sha`-keyed cache (`.fux/runtime/display-cache/`) before the record may commit — `store/writer.py` refuses a `hashed` record with no matching cache entry. `ask`/`find`/`answer` (text and `--json`) resolve through it; ranking does not (`rank()`'s two call sites pass no cache), so the differential law is untouched by construction — proved directly, not just argued (`test_the_scan_and_accelerator_paths_agree_on_a_cold_hashed_title`). **The two forks PRIORITY.md reserved for Arpit**: the mandatory cache needs **no L2 exception** (citing [ADR-CACHE](../docs/adr/0034_cache.md)'s identical two-day-earlier ruling on gitignored/never-committed caches); a cold cache **forces a re-fetch** to repopulate rather than degrading silently, though grounding found this changed no live behaviour (`_reusable()` already never carries a `hashed` record forward without a fetch attempt). **Two of three sub-questions ruled**: term-hash salting **not built** (a committed salt is not a salt); `code` **kept** on hashed records despite a demonstrated embedding-inversion risk (Morris et al., EMNLP 2023), traded against `--hybrid` ranking quality. **The third needed no ruling**: `loc`/`id` stay plaintext — `loc` is the refer plane's only fetch address (`fetcher(loc)`, no other route for a fresh clone) and is separately committed in plaintext via the URL source list already, so hashing it would cost function for zero privacy gained. This corrects the row's own original "reveals neither title tokens nor URL slug" done-when clause, stated explicitly rather than dropped. `uv run pytest -q tests tests_e2e`: 866 passed. Two unrelated commits landed in the same session and are **not** part of this row: `7b7679c` (the session-lock hook made per-asset) and `5509030` (ADR-CACHE + register reconciliation, pre-existing uncommitted work from a prior Cowork session) |
| **PRIORITY P6** — the refer plane wired into `answer` | 2026-08-21 | `9f8366e` · [ADR-REFER](../docs/adr/0030_refer-plane.md) · [ADR-ANSWER](../docs/adr/0006_answer.md) · [ADR-ASK](../docs/adr/0004_ask.md) · [ADR-CLI](../docs/adr/0002_cli-surface.md) | **`answer` fetches, verifies and re-scores by default now.** `src/fux/query/refer_answer.py`'s `answer_via_refer` calls the existing `refer()` with the winning citation and `Policy(mode=ALWAYS)`; `_load_fetcher` resolves and connects the *same* fetcher a `url:` document was ingested with, mirroring `ingest/urlsrc.py`'s own resolution exactly, degrading to `(None, noop)` — never raising — when nothing can be resolved. `"source": "refer"` in `--json`; `--no-refer` keeps the exact M2 index-only shape. Proved against the real CLI on the actual e2e fixture, not just in-process: a passage + a fresh `sha` that changes when the source file changes, without re-ingesting. **Both ADRs accepted, per the row's own done-when.** One tension found and put to Arpit rather than resolved silently: ADR-REFER's own text tied acceptance to the still-unmeasured W-59 budget sweep (separate from R4, which passed) — ruled **accept now**, budget sweep kept as a named, checkable veto condition rather than closed or hidden. ADR-ANSWER substantially rewritten, not status-flipped — its own veto condition had fired ("the disclaimer stops matching what the verb actually does"). **Deliberately scoped to `answer` only** — PRIORITY.md's row title named `ask` too, but its own done-when never tested `ask`, and fetching every ranked result (not just the winner) is a materially bigger, riskier change left undecided rather than assumed. **Found while capturing real output**: a refer passage on a document with frontmatter includes the frontmatter block verbatim (`refer/_chunk.py` doesn't strip it, unlike ingest's extraction) — a real readability cost, recorded rather than fixed, `chunk.py`'s call to make. `uv run pytest -q tests tests_e2e`: 877 passed |
| **[W-59](../archive/open/W-59-refer-plane-measurement.md)** — the refer plane's last measurement obligation, discharged | 2026-08-22 | [ADR-REFER](../docs/adr/0030_refer-plane.md) veto condition 2 updated · [the budget sweep](regression/2026-08-22-budget-sweep/report.md) | **The budget sweep ran, and the result is narrower than the item's own FLAT/NOT-FLAT rule anticipated.** By the letter (mean |delta| 12.55% on the shipped single-candidate path) it is NOT FLAT — but every measured delta was negative or zero: the greedy assembler never beat plain top-k, losing up to 35.5% at realistic budgets. Root cause: the per-document cap binds even with one candidate, which is every real `fux answer` call today. **Filed as [W-72](../archive/open/W-72-refer-per-doc-cap-single-candidate.md)** rather than fixed inside the measurement. R4 (PASS, 2026-08-20) and ARC-vs-LRU (Arpit's ruling, 2026-08-22 — ARC wins) close the item's other two open measurements. All three DoD items resolved; item deleted from OPEN-WORK |

| **[W-44](../archive/open/W-44-archived-content-signalling.md)** — archived content finally says so | 2026-08-22 | [ADR-ARCHIVED-CONTENT](../docs/adr/0037_archived-content.md) 1/3/7 · [ADR-INGEST](../docs/adr/0007_ingest.md) · [W44-SIGNAL](regression/2026-08-22-archived-signal/VERDICT.md) | **Open since 2026-08-12, and it closed in the order the record asked for.** The instrument decision 5 demanded was built first — 45 frozen queries in three slices, committed before any number — and **then Arpit lifted the gate by direct instruction**; either alone would have unblocked it. Measured **WARRANTED**: 32.00 pts live-intent contamination@5 against a 25 pt bar, findability guard 93.33 % against 60. The diagnosis is the slice gap — the ambiguous slice sits at 66 pts, the corpus's own archived share, so **the scorer has no currency signal at all** and the live slice only looks better because present-tense vocabulary correlates with live documents. Shipped: `archived: true` at ingest, `[archived]` on `ask`'s text, the flag in both verbs' `--json`, a response-level note on **stderr**. **`find`'s stdout stays bare** so it still pipes. **The ranking does not move** — the weight stays `1.0` and two tests assert order and scores are byte-identical with the marker present. One test had to be *sharpened rather than kept*: it compared whole result objects, which silently asserted the marker could never exist |
| **[W-69](../archive/open/W-69-prediction-register-check.md)** — the register check, and ADR-RS accepted | 2026-08-22 | [ADR-RS](../docs/adr/0036_predictions.md) — ⏳ proposed → **✅ accepted** | **A record whose central claim was *"the register is complete"* stopped being unverified.** `tests/test_prediction_register.py`, 13 assertions: every filed `VERDICT.md`'s `prediction:` id must have a register row — **not the reverse**, since a RETIRED id (R7, R8) never gets a verdict, and there is a test asserting that direction so it cannot be silently inverted. Two guards against the vacuous pass (the walk found verdicts; the registers parsed), and a constructed negative proving an unregistered id fails. **Building it forced one refinement:** the first non-`R` verdict arrived the same day, so `IMPLEMENTATION.md` grew a **feature-gate** table and the check reads both — completeness kept without inventing an architectural prediction nobody made. Mutation-tested: breaking one row fails the check and names the id |
| **[W-72](../archive/open/W-72-refer-per-doc-cap-single-candidate.md)** — `fux answer` stops discarding half its budget | 2026-08-22 | [ADR-REFER](../docs/adr/0030_refer-plane.md) veto 2 | The per-document cap applied even with one candidate document, which is **every** `fux answer` call. On a real query the assembled answer goes from **3 passages / 3 492 bytes to 6 / 6 991** against the same 8 000-byte budget. **Scoped, not a removal** — the cap binds again the moment a second document competes, with a test each way, keyed on the candidate set rather than on `k`. Filed by [the budget sweep](regression/2026-08-22-budget-sweep/report.md) that found it rather than fixed inside the measurement, and **veto 2 does not reopen acceptance**: the defect was a constant's scope, not the plane's shape |

| **[W-57](../archive/open/W-57-graph-lane-acceptance.md)** — the graph lane's acceptance measurement, both halves | 2026-08-22 | [ADR-GRAPH](../docs/adr/0029_graph.md) veto conditions **1 and 3** · [the run](regression/2026-08-22-graph-acceptance/report.md) | **Open since 2026-08-20, blocked the whole time on a corpus that no longer existed.** fux-playground's ~50 human goldens were lost on 2026-08-20 and its planned redesign may drop grading permanently, so the phenomena were graded against a **new 66-document fux-lab environment** (`graph-acceptance`) built for the purpose: **24/24**, XPASS 0. **Determinism closed the same day on a second machine** — `.fux/runtime/graph.json` hashes to `3ede5863…a30a53` on both an x86-64 Linux sandbox and Arpit's arm64 Mac, from independent `setup.sh` runs. **Two architectures is stronger than veto 1 asked for**: it also rules out float-width and byte-order dependence, which two machines of the same kind could not have caught. **Two departures are recorded, not smoothed over** — the corpus is a substitute, and its goldens were **agent-authored** (from construction ground truth, never from the engine's output) at Arpit's direct instruction, against the item's own "no agent should do it". The second-machine result is **appended** to the filed report as a dated addendum; §2's table still reads *"not checked"*, because that is what was true when it was filed |

| **[W-62](../archive/open/W-62-measure-against-the-outside-world.md)** — external validation, **withdrawn** | 2026-08-22 | *(no ADR — it owned no component; **no ADR affected**)* | **Arpit withdrew parts 1 and 2 and took them personally**: *"the whole w sixty two, remove it, cancel it out. That's on me. I'll own it."* **Part 3 shipped first** — the public README's two false statements of fact were fixed the same day (it claimed *"M2 shipped"* after M3/M4/M5 and five releases, and called the graph lane *unreleased* when it went out in `0.34.0`), verified against `git ls-remote` and the raw file at `main` rather than against the local copy. **Parts 1 and 2 are cancelled, not failed and not deferred**: the three-way comparison needed a Confluence-shaped export corpus that cannot be synthesised without defeating its purpose, and the cold-start half needed five external people. ⚠ **This does not answer the question it asked.** Whether Fux wins on private organisational documents is still **untested**, and the item's own Hazard note said that an item sitting open forever is itself information. What changed is who holds the question. **Id retired, not reused** |

| **[W-52](../archive/open/W-52-df-over-the-union.md)** — `df` over the union, **decided A + D** | 2026-08-22 | [ADR-ARCHIVED-CONTENT](../docs/adr/0037_archived-content.md) decision 4 · [the compare doc](compare/df-over-the-union.compare.md) | **Parked since 2026-08-19; closed by deciding not to change anything.** Arpit: *"I like a plus d approach."* `df` stays computed over the union (A) and currency is a **ranking-time** concern served by `archived_weight` (D). **Option D did not exist when the item was filed** — the weight shipped the same day, which is what made "change nothing" a real answer rather than an evasion. **Researched against primary sources, not argued from first principles**: Lucene keeps *deleted* documents in term statistics until merge and calls it minor unless the excluded population is **divergent**; Elasticsearch ships global-statistics merging as a discouraged opt-in and tells small corpora to use one statistical universe; temporal IR puts recency at re-ranking time. **The named condition was then measured and did not fire** — Jensen-Shannon divergence between the live and archived `df` shapes is **0.1514** on a 0–1 scale. ⚠ **Two DoD boxes are deliberately unticked**: the two-corpus ranking eval was the right price for *changing* `df` and was never owed for *declining to*. A cheaper measurement was substituted **because the decision changed nothing**, not because the standard moved. Also rejected on the way: **option E** (archived excluded by default), which Arpit proposed and then set aside — real console output showed it surfaces the right answer for live-intent questions but breaks 14 of 15 historical ones, and that a naive implementation returns an **empty result set** because filtering after top-k leaves nothing |

| **ADR-TUNE built** — the tunables file, per-source priority, and a stats plane that stopped baking a tunable | 2026-08-24 | `v2.0.0-alpha.1` | [ADR-TUNE](../docs/adr/0038_tuning.md) — ⏳ still `proposed`; `built` yes | **`.fux/tune.toml` exists and is read once per query.** Seven tables, a **closed** key set (an unknown table or key is a loud error), errors collected and reported together, merge-conflict markers and a UTF-8 BOM handled by name. Per-source `[priority]` in either direction, **longest matching entry wins**, resolved on `Weighting` so the scorer and the accelerator's bound cannot drift. `--no-tune` on the read verbs; `fux tune` prints and never writes. `[ranking]`/`[dense]` retired from `fux.toml` with an error naming the new home. **Two defects this build surfaced, neither anticipated by the record:** (1) `.fux/runtime/stats.json` stored a **pre-weighted** `total_wlen`, so a field weight would have moved `avg_wlen` on the scan path and not the accelerator path — a differential-law break needing a rebuild to repair; fixed by storing raw `total_flen`, `RUNTIME_SCHEMA` -> `fux.runtime.v4`. (2) `fux doctor` warned about files fux itself writes, because `.fux/` had no category for a committed *file*. **The finding worth carrying:** BM25 **saturates**, so an unweighted pruning bound is nearly indistinguishable from a weighted one at large `tf` — a sweep over a realistic corpus **passes while proving nothing**. The first fixture written did exactly that and the mutant survived it; the shipped fixture uses `tf = 1` and is **verified by mutation**. 1 352 unit + 73 e2e tests pass. ⚠ **Ratification is owed** — built is not accepted; and `[fuse]`'s two keys are settable but unreachable, stated in the record rather than hidden ⚠ **Superseded 2026-08-25: the dense lane, the embedding model and `--hybrid` were DELETED** (Arpit). This row is kept as the build log it is — what was true when it was written — and is NOT a description of the engine today. See the model-removal row below. |
| **[W-73](../archive/open/W-73-weighted-scores-vs-pruning-bound.md)** — the accelerator's differential law, weighted | 2026-08-23 | `v2.0.0-alpha.0` | [ADR-T1-ACCELERATOR](../docs/adr/0011_accelerator.md) · [ADR-RANKING](../docs/adr/0012_ranking.md) | **Fixed: the differential law now holds at every configured weight, not only at `1.0`.** `query/rank.py::Weighting` carries the query-time weights into the pruning bound; `derive/accel.py::block_bound` recombines per-field extrema at those weights; `_kth_score`/`_cannot_reach` take the weighting rather than assuming `1.0`. Adversarial fixture ([`tests/derive/test_weighted_bound.py`](../tests/derive/test_weighted_bound.py)) fails at `w = 500` without the fix, verified by reverting. Fork 3 (per-field extrema loosening the bound) measured **free — +0.0% blocks scanned** against 10 000 real documents, because 92.5% single-field postings make the per-field sum exact. [Run](regression/2026-08-23-fork3-per-field-bound/report.md). A second divergence found on the way: the derived doc table didn't carry `archived`, so `ask --fast`/`--scan` could disagree on that flag even at the default weight — fixed in the same change, `RUNTIME_SCHEMA` -> `fux.runtime.v3`. Gated the per-source priority feature entirely; unblocks [ADR-TUNE](../docs/adr/0038_tuning.md) decision 12 |
| **[W-76](../archive/open/W-76-amended-architecture.md)** — the amended architecture, all nine phases | 2026-08-23/24 | `v2.0.0-alpha.0` | [ADR-INDEX-LIFECYCLE](../docs/adr/0009_index-lifecycle.md) · [ADR-RECORD](../docs/adr/0010_index-record.md) · [ADR-TUNE](../docs/adr/0038_tuning.md) · [ADR-MCP](../docs/adr/0039_mcp.md) · [ADR-ENRICH](../docs/adr/0040_enrich.md) · [ADR-RERANK](../docs/adr/0041_rerank.md) | **The parked `ideal set` (archived 2026-08-25), re-argued against four rulings Arpit made 2026-08-23, and built.** Record shape moves to `fux.index.v2`: five-field BM25F (`body, heading, title, path, ctx`), body first, **-36.7% tf bytes while adding three fields**; `flen` replaces `wlen`; `code` dropped (91% of ingest, 0.4% of index). Analyzer moves to `v2` (Porter, 75/75 published vectors; identifier splitting). Priors (`supersedes:` edges, git commit recency) fold through `Weighting`. `.fux/tune.toml` + per-source priority, both directions allowed, fux states the cost. `fux enrich` (opt-in, never in `fux ingest`, keeps L3). `fux mcp` (stdio JSON-RPC, three tools, no `answer`). Proximity reranking in stdlib arithmetic — the specified cross-encoder **refused**, `onnxruntime` is not byte-identical across x86-64/arm64; measured on 50 new goldens **28 -> 32** (4 fixed, 0 broken), **+8ms p95** against a 150ms bar, 240 differential comparisons green — of 18 surviving failures, 18 are vocabulary gaps and 0 are ordering failures, so enrichment is deferred with a stated price rather than rejected. [Run](regression/2026-08-24-rerank-and-goldens/report.md). Per-chunk committed `int8` vectors with a derived Hamming-prefix prefilter, replacing the whole-document sign codes. **This repo's own index is migrated** — 434 records, delta run byte-identical to the full run; migrating it surfaced a real defect in ADR-INDEX-LIFECYCLE decision 10's migration command (`--full` read the index it exists to replace), fixed and amended into the record. Validated on fux-playground (21 376 differential comparisons byte-identical across a weight sweep) and fux-lab at 10 000 real documents (ingest 31.5s, build 1.4s, p95 33.53ms against a 150ms bar). **1271 unit + 73 e2e tests pass.** Every autonomous call taken in Arpit's absence is in [`W-76-DECISIONS.md`](../archive/open/W-76-DECISIONS.md) (D1-D30). ⚠ **All four new ADRs ship `status: proposed`** — built and reviewed phase-by-phase, ratification is a separate step. ⚠ **The 2026-08-24 rerank/goldens enrichment numbers are an upper bound, not a clean measurement** — the author had already seen the failing queries; a blind re-grade is the named, non-blocking follow-up ⚠ **Superseded 2026-08-25: the dense lane, the embedding model and `--hybrid` were DELETED** (Arpit). This row is kept as the build log it is — what was true when it was written — and is NOT a description of the engine today. See the model-removal row below. |
| **[W-79](../archive/open/W-79-remove-the-dead-fusion-code.md)** — the dead fusion code, deleted | 2026-08-26 | — | [ADR-TUNE](../docs/adr/0038_tuning.md) · [ADR-CLI](../docs/adr/0002_cli-surface.md) · [ADR-ASK](../docs/adr/0004_ask.md) · [ADR-T1-ACCELERATOR](../docs/adr/0011_accelerator.md) | **Ruled delete, per the item's own recommendation.** `src/fux/query/hybrid.py` (`hybrid_ask`, the module-level RRF fusion) is deleted — it was off the live path since W-76 Phase 7 gave `--hybrid` a lane through `query/dense.py`'s gated fusion, and its only caller was `tools/differential/playground_grade.py`'s `"hybrid"` grading mode, now repointed at `fux.query.run_query(..., use_hybrid=True)` — the same call `fux ask --hybrid` makes. `[fuse] rrf_k`/`dense_width` are removed from ADR-TUNE's `_SCHEMA`, `Tune` and the specimen — six tables, not seven. ⚠ **`query/fuse.py` was first kept and then deleted later the same day** — this row originally read *"is **kept**, since `tests/query/test_fuse.py` pins the archived engine's calibrated arithmetic"*, and that reason failed on review: what `rrf(offsets=)` pins is a supersession rank penalty calibrated on the **archived** engine, which archive-is-not-evidence forbids citing as live grounding, and live supersession is already `[ranking] superseded_weight` applied in score space at `query/rank.py:205`, to which a rank-space interval does not transfer. A module carrying a live-looking `RRF_K = 60` with no caller in `src/` misled a reader the same day. `src/fux/query/fuse.py` and `tests/query/test_fuse.py` are both deleted and [ADR-PORT-LIST](../docs/adr/0015_port-list.md)'s RRF row is struck. ⚠ **Two live proposals plan on `rrf(offsets=)` and are now more expensive** — `ideal/02-lexical-engine` (archived 2026-08-25) and `ideal/00-ideal-architecture` (archived 2026-08-25) both cite *"code is ported already"*; that premise is dead and reviving RRF needs a new record per ADR-PORT-LIST rule 1. `explain --no-tune` is removed from `src/fux/cli.py`'s parser — `cmd_explain` never read a tunable, so there was nothing to wire up; `--no-tune` now reads five verbs, not six. `[dense] mode = "gated"` is untouched — [DENSE-CHUNK](regression/2026-08-24-dense-lane-gate/VERDICT.md)'s FAIL stands, and stays `off` |
| **[W-80](../archive/open/W-80-the-bundled-model-has-no-live-recipe.md)** — the bundled model's missing provenance | 2026-08-25 | — | [ADR-ENRICHED](../archive/adr/0017_enriched-mode.md) | **CLOSED BY DISSOLUTION, not by fix.** fux told a user with a corrupt model to run `tools/distill/distill.py`, which is not in the repo; two live error messages and `model.json`'s `recipe` field pointed at it. **Neither fork it offered was taken** — the recipe was not restored live and the provenance claim was not deleted. The model was removed instead, so there is no bundle, no `recipe` field and no error message left to be wrong. ⚠ **One of its own claims was wrong and is corrected on the way out**: it cited *"ADR 0006's <=10 MB bundle budget"*, and **no such budget exists in any live record** — the 7.9 MB bundle was never governed by a written size rule at all, which is a weaker starting position than the item asserted. Two proposals retired with it |
| **The embedding model and the dense lane, DELETED** | 2026-08-25 | — | [ADR-T1-ACCELERATOR](../docs/adr/0011_accelerator.md) · [ADR-ASK](../docs/adr/0004_ask.md) · [ADR-CLI](../docs/adr/0002_cli-surface.md) · [ADR-TUNE](../docs/adr/0038_tuning.md) · [ADR-EXTRACTED](../docs/adr/0016_extracted-mode.md) · [ADR-INGEST](../docs/adr/0007_ingest.md) · [ADR-RECORD](../docs/adr/0010_index-record.md) · [ADR-CODES-TABLE](../archive/adr/0025_codes-table.md) · nine more | **Arpit's instruction, on the evidence already filed.** `src/fux/embed/` (model.py, fuxvec.py, chunkvec.py, the 7.9 MB `model.bin`), `query/dense.py`, `derive/dense.py`, `codes.jsonl`, the committed per-chunk `vectors` field, `[dense]` and **`ask --hybrid`**. Cause: DENSE-CHUNK measured **0 fixed / 2 broken at every setting that fires** — the model mean-pools static token vectors, so the lane was **as order-blind as BM25F** and duplicated the lexical lane's blind spot at far higher cost. **Measured A/B on the same corpus** ([run](regression/2026-08-25-model-removal/report.md)): wheel **6.84 MB -> 233 KB, 30.1x** (the download was **97 % model**); committed index **-22.6 %**; full ingest **6.8x** faster; **differential law intact**. **13 records amended**; `RUNTIME_SCHEMA` v4 -> v5. ⚠ **Ranking is unchanged by ARGUMENT, not measurement** — `mode` defaulted to `off` and the gate returned before any dense work, but 13 ADRs changed in the same commit so a cross-tree ranking diff was never possible |
| **[W-78](../archive/open/W-78-enrichment-was-measured-against-its-own-answers.md)** — a ruling made on a contaminated number | 2026-08-25 | — | [ADR-RS](../docs/adr/0036_predictions.md) decisions 11-16 · [ADR-RERANK](../docs/adr/0041_rerank.md) | **CLOSED — both rulings made, neither built anything.** **Ruling 2:** the run-classification rule **accepted** in its rewritten form — every measured run is `blind` or `informed`, an informed run is **reclassified rather than banned** and never supplies a delta, and a delta below the set's resolution is *no detected change*. **Ruling 1 (on delegation):** ADR-RERANK veto 1 **condition 1 VACATED** — withdrawn, not rewritten, because the drafted replacement's lead leg argues value from other corpora about a weaker model than the record specifies, and substituting a second unmeasured claim for the first is this item's own error; **condition 2 RESTATED** as *score-level drift below the target corpus's adjacent-gap floor*, after [measurement](regression/2026-08-25-rank-flip-susceptibility/report.md) showed the old `5e-10` bar was derived from `round(score, 9)` — not the binding constraint — and demanded **~200 000x** more precision than the corpus can resolve (0.00 % flips at the quoted drift). ⚠ **The cross-encoder remains refused and nothing was built**; the refusal now rests on **one measurable unmet condition** instead of a dead argument and a mis-specified bar. ⚠ **This record now holds NO position on the cross-encoder's value** — correct, because there is none |

## Ratified decisions

**Not milestones — human calls.** [`OPEN-WORK.md`](OPEN-WORK.md) rule 2 forbids
deleting an item until its outcome is recorded here, and a ratification has no
milestone row to live in. One line each, with the record that now holds it.

| item | decided | by | outcome |
|---|---|---|---|
| **W-30** — the ingest-mode naming | 2026-08-19 | Arpit | **Ratified `extracted` / `enriched`**, and split into a record per mode: [ADR-EXTRACTED](../docs/adr/0016_extracted-mode.md) (accepted — the deterministic contract, owns `ingest/extract.py`) and [ADR-ENRICHED](../archive/adr/0017_enriched-mode.md) (⏳ proposed — named and **fenced out of the maintenance path**, not authorized to build; the M8 gate in [W-38](../archive/open/W-38-m8-deferred.md) stands). Arpit's stated meaning — the index is refined by a coding agent — is what made the L3 boundary decidable: enrichment is its own command, its output pinned then ingested deterministically. Open 7 days |
| **W-44** — how retired content is signalled | 2026-08-19 | Arpit | **Option B: annotate, never reorder** → recorded first as ADR-ARCHIVED-SIGNAL and superseded hours later by [ADR-DIR-LIST](../docs/adr/0022_dir-list.md) when Arpit gave directories their own source file. **The file and the declaration shipped 2026-08-19 (W-54); the signal did not** — ADR-ARCHIVED-CONTENT decision 5 splits them, and W-44 still owns the instrument. A record from a source **declared** `archived=true` carries `archived: true`; every verb surfaces it; **the ranking is byte-identical**. Two changes on the way in: the signal is **declared, not derived** — the path heuristic was exact here and a silent convention for any other repo, and the **`df` contamination is not part of it** — 26.6% of records are archived and 42.1% of live terms carry an inflated `df`, which is a ranking change and is [W-52](../archive/open/W-52-df-over-the-union.md), behind its own pre-registration. Open 7 days |
| **W-50** — how a URL is fetched | 2026-08-19 | Arpit | **The URL list becomes tool-written**: a CLI command fetches and writes the URL plus its attributes, and the file is never hand-edited — so a flag decides what is *recorded*, not what is fetched at ingest time, and the same list can never produce different committed bytes. **Every written line states every attribute explicitly**, which left **L5 untouched**: it now means what a *missing* attribute means, and a correct file never exercises it. Recorded as [ADR-URL-LIST](../docs/adr/0018_url-list.md) 12–13; **built 2026-08-19 as `fux url`** — with one correction, that the verb *records* and does not fetch, because `--refresh-urls` is the only networked path in the engine (L4) |
| **W-33** — the ADR numbering convention | 2026-08-19 | Arpit | **Confirmed**: `docs/adr/` is the live set and **starts at 0001**; records under `archive/` are archived, and numbers there survive only to map a retired record to its successor. Cite-by-name stands, so **milestone items now reserve a NAME, never a number** — `ADR-GRAPH` (W-23), `ADR-REFER` (W-24), `ADR-MAINTENANCE` (W-25), `the T2 proposal` (W-26), swept in the same change. They had been reserving `0006`–`0009`, which accepted records already held: the collision this item was filed to prevent, live rather than hypothetical. Open 7 days |
| **W-31** — the `.fux/` layout and the URL fetcher | 2026-08-19 | Arpit | **Ratified as-is**, all three records: [ADR-DOTFUX](../docs/adr/0003_fux-directory.md), [ADR-URL-INGEST](../docs/adr/0008_url-ingest.md), [ADR-CONFIG](../docs/adr/0014_config.md). The builder-made call it flagged — `.fux/README.md` generated at **ingest** time rather than by `doctor --fix` — **stands**. Ratification arrived *after* the records read `accepted` on disk (2026-08-18, when the successors took the engine), which is the pattern this item existed to make visible. The known defect in ADR-URL-INGEST's default was W-54's to fix, and it was fixed the same day. Open 7 days |
| **W-32** — the `CLAUDE.md` rewrite | 2026-08-19 | Arpit | **Adopted.** The PROPOSED header is deleted and the M0a rewrite is in force. Corrected on the way in: the item's own "there is no `CLAUDE.md.proposed`" was wrong — the file existed (`bed2186`), was implemented into `CLAUDE.md` and deleted at `3892c55`; `git log --follow` could not see a delete-plus-overwrite, so a *verified* claim rested on evidence that could not show it. **Five factual passages had rotted** behind the header, one of them forbidding the milestone that shipped as `v0.32.0`. Open 10 days |
| **W-27** — the M7 dogfood gate | 2026-08-20 | Arpit | **Ratified closed, and redefined — by Arpit's word, not measured evidence.** The retired gate was a two-week logged-use period ending in a release Arpit had been using, blocked by W-26 (M6, still unbuilt at close). Arpit closed it directly instead: fux already dogfoods itself in this repo (`.fux/` self-indexed, `fux --version` runs), and that satisfies the intent. **New standing obligation, replacing the retired gate: [`DOGFOOD.md`](../DOGFOOD.md) is refreshed on every fux version upgrade** — not on a fixed two-week schedule. No regression run backs this row; it is a human call, recorded per rule 2, not a milestone landing. |

## Not yet shipped

`M6` scale & T2 ·
`M8` deferred. Their state is in
[`OPEN-WORK.md`](OPEN-WORK.md), their spec in [the ADR register](../docs/adr/README.md).
**Nothing above `M5` has a row here, and that is the honest position** — a
milestone earns its row by landing, not by being planned. **M3's and M4's own
rows name what they did not measure**, for the same reason. **M4's record went
`accepted` on 2026-08-21** once R4 passed and `answer` was wired onto the plane
— **with its budget-sweep veto condition left open** ([W-59](../archive/open/W-59-refer-plane-measurement.md)),
which is a different thing from measured. **M7 is not in this list** —
it closed by ratification, not by landing; see the W-27 row above.

## Predictions

> **This table is the register of pre-registered predictions — the whole set,
> and the only place that claims to be complete.** An id here is a claim frozen
> *before* it was measured; the threshold lives in a `PRE-REGISTRATION.md` under
> `tools/`, and the ruling lives in a `VERDICT.md` under
> [`regression/`](regression/README.md). **Ids are never reused**, including
> retired ones. **A row missing here is the failure mode**: R9 ran on 2026-08-22
> and was cited in six documents before anyone noticed it had no row — added
> 2026-08-22.

| id | status | where |
|---|---|---|
| R1 | **PASS** | M1 |
| R2 | **PASS 3/3** (2026-08-12) | [run](regression/2026-08-12-r2-close/report.md) |
| R3 | **PASS** — 27.2 ms p95 vs a 150 ms bar | [run](regression/2026-08-12-m2-accelerator/report.md) |
| R4 | **PASS** (2026-08-20) — cold p95 1.113 s / 3 s, warm 0.016 s / 300 ms, **serial fetch is the boundary** | [R4-REFER](regression/2026-08-20-refer-plane-r4/VERDICT.md) |
| R5 | **FAIL** (2026-08-20) — 44.4 s at 100 000 docs vs a 1 s bound; 3.523 s at the 10 000 design point, still failing. **Fork ruled 2026-08-22: B, the hook defers** — the failure stands as measured and is answered by changing the hook, not the threshold | [R5-HOOK](regression/2026-08-20-r5-hook-latency/VERDICT.md) · [the ruling](compare/hook-at-scale.compare.md) |
| R6 | **INCONCLUSIVE** (2026-08-20) — every tier matched, but tier 1 matched with the driver removed too. **Adjudicated PASS by Arpit 2026-08-22 under §3.1**; the verdict itself is unedited and the instrument's contradiction is [W-67](../archive/open/W-67-r6-instrument-repair.md) | [R6-MERGE](regression/2026-08-20-r6-merge-driver/VERDICT.md) |
| R7 | **RETIRED** (2026-08-22, Arpit) — **cancelled, never FAILed, and now withdrawn rather than re-derived.** *"Remove that promise, it's not needed."* There is no committed-size budget and no successor is owed; the size is still **measured and printed** by ADR-POSTINGS' and ADR-INDEX-LIFECYCLE's checks, as information rather than a gate. Id retired, not reused | `the retired compare doc` (archived 2026-08-25) · [analysis](regression/2026-08-21-r7-preliminary-analysis/ANALYSIS.md) |
| R8 | **RETIRED** (2026-08-22, Arpit) — never registered, never run. It was specified as a graph-verb bound **at 100 000 documents**, which is the class of commitment the same ruling removed. A graph bound, if wanted, is a new prediction at 10 000 with a new id | [where it was named](compare/graph-plane-format.compare.md) |
| R9 | **PASS** (2026-08-22) — the T1 accelerator at the 10 000-document design point: **12.46 ms worst-case p95 against R3's own 150 ms bar, reused verbatim rather than restated**. It is the measurement that answered M6's first question with *T2 is not needed*, and [the T2 proposal](proposals/t2-segments.md) is the record of not building it | [R9-T2-AT-10K](regression/2026-08-22-r9-t2-at-10k/VERDICT.md) |
| R10 | **INCONCLUSIVE** (2026-08-27) — the separation floor. The curve reaches `t = 0.75` at `separation 0.3`, **falls back at `0.4`**, then rises, and **two rules frozen in the same pre-registration disagree** about what that means: the selection rule picks `0.5`, the verdict table's row 4 (*non-monotone → too noisy*) picks no change. **Handed to Arpit, not adjudicated** (`CLAUDE.md` §A pre-registered threshold may never move). `SEPARATION_FLOOR` stays `0.10`; no test was edited, because `tests/query/test_confidence.py` asserts the rule relative to the constant and never its value. ⚠ **Six queries sit at or above `0.5`** and the top two bins are empty, so no reading supports a shipped constant — which the pre-registration said in advance. The contradiction is corrected in [ADR-RS](../docs/adr/0036_predictions.md) decision 18, never in the frozen file ✅ **RULED 2026-08-28 (Arpit): the VERDICT TABLE governs** — a non-monotone crossing is *no change*, and a selection rule applies only once the verdict table is satisfied. **`SEPARATION_FLOOR` stays `0.10`.** ⚠ **The verdict is unedited and stays `INCONCLUSIVE`**: the RULE is settled, the RESULT is not overturned — nothing supersedes a measurement except a better measurement. ⚠ **It does not reach the `grounded` decoy at `0.58`**, which is above the floor either reading would have picked. | [R10 verdict](regression/2026-08-27-r10-separation-floor/VERDICT.md) |
| P3 | **PASS** (2026-08-27) — sanitized-sha stability. **19/19 = 100 %** against a frozen `>= 80 %`, so **fork 3 clears its gate** and W-87 P4 is unblocked. A **control arm** was run so the 100 % is not the M1 failure (a treatment that touched nothing, reported as a null effect): `Special:Random` changed, the 19 documentation URLs did not. ⚠ **Cleared is not decided** — a fifth function on the fetcher contract is still a design call. ⚠ **The spec named no interval**; at 12 s apart this measures **server-side determinism**, not document churn, and a realistic-interval run is a NEW pre-registration | [P3 verdict](regression/2026-08-27-p3-sha-stability/VERDICT.md) |

## Feature gates (pre-registered, but not `R` predictions)

> **Why this is a second table and not four more rows above.** The `R` series is
> the paper's **architectural** claims ([ADR-RS](../docs/adr/0036_predictions.md))
> — ids frozen against the design's own predictions. A feature gate is also
> pre-registered, also frozen before its number existed, and also ruled by a
> `VERDICT.md`, but it is not one of the paper's claims and giving it an `R`
> number would invent an architectural prediction nobody made.
>
> **Both tables are checked, together, by
> [`tests/test_prediction_register.py`](../tests/test_prediction_register.py)**
> (W-69). Every filed verdict's `prediction:` id must appear in one of them, so
> "every measurement is accounted for" stays true without polluting the `R`
> series. A row with no verdict is normal in both — a RETIRED id never gets one.

| id | status | where |
|---|---|---|
| P-SUPERSEDE | **FAIL** (2026-08-25) — `[ranking] superseded_weight` against a frozen **>= 1 fixed / 0 broken** bar. **The prior FIRED for the first time since it shipped** (it needs a frontmatter `supersedes:` key; the playground declared supersession in prose only, so the flag had never set). At `0.5`: **fixes `q015`** — the canonical failure — and breaks `q022`/`q033`. At `0.25`: four breaks. **The control is clean**: the frontmatter edit alone fixes 0, breaks 0. **Every broken query has the SUPERSEDED document as its correct answer**, so the diagnosis is one cause, not four: **supersession belongs to the QUERY'S INTENT, not the document**, and a per-document multiplier cannot express it. ⚠ `informed`; ±2 on 50 queries is below decision 14's floor — the **direction** carries, the magnitude does not | [P-SUPERSEDE](regression/2026-08-25-supersession-and-reranker-default/VERDICT.md) |
| DENSE-CHUNK | **FAIL** (2026-08-24) — the per-chunk dense lane against its own **>= 3-fixed / 0-broken** bar: measured **0 fixed, 2 broken**, at every setting that fires. **0 fixed is the number that matters**; the bar needs 3. The cause is structural rather than tuning: `embed/model.py` **mean-pools static token vectors** (no layers, no attention), so the lane is **as order-blind as BM25F** — and `always` mode breaks **`q015`**, the current-vs-superseded query a semantic lane was most expected to rescue. **Phase 7 was right that per-chunk beats per-document and wrong that the unit was the binding constraint** — the pooling is. `[dense] mode` stays `off`; the committed vectors stay, because they cost nothing at rest and a better pooling reuses them unchanged | [DENSE-CHUNK](regression/2026-08-24-dense-lane-gate/VERDICT.md) ⚠ **2026-08-25: the verdict STANDS and its subject is GONE.** The lane, the model, the committed `vectors` and `[dense]` were deleted on Arpit's instruction. The clause *"the committed vectors stay, because they cost nothing at rest"* was wrong on its own terms — they were **23.0 % of the committed index** ([measured](regression/2026-08-25-model-removal/report.md)) — and it is moot either way. **The verdict itself is frozen and unedited**; its frozen pre-registration is mirrored into the run, since the module carrying it was deleted (ADR-RS decision 16). |
| W44-SIGNAL | **WARRANTED** (2026-08-22) — live-intent contamination@5 **32.00 pts** against a 25 pt bar; findability guard **93.33 %** against a 60 % floor. Discharged [ADR-ARCHIVED-CONTENT](../docs/adr/0037_archived-content.md) decision 5's gate, which Arpit **also** lifted by instruction the same session — the pre-registration was frozen first, so the number is evidence rather than a formality. Licenses the marker and disclaimer only; the demotion default stays [W-52](../archive/open/W-52-df-over-the-union.md)'s | [W44-SIGNAL](regression/2026-08-22-archived-signal/VERDICT.md) |
| P1 | **FAIL** — full postings, permanently | [P1-RERUN](regression/2026-08-09-pruning-rerun/VERDICT.md) |
| P2–P7 | retired with plan revision 1; successors are R3–R7 | [the ADR register](../docs/adr/README.md) |
