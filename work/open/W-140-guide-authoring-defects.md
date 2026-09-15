---
type: OpenItem
id: W-140
title: "W-140 — the defects writing the operating guides uncovered"
description: "Writing ten consumer skills from the code (SR-AGENT-POLICY decision 15, 2026-09-11) meant checking every flag, field and verdict against src/fux and running most verbs. That found code defects, SR-vs-code disagreements, and guide text that names workarounds which must change when each defect is fixed."
status: open
lane: agent
timestamp: 2026-09-11T00:00:00Z
---

✅ **Row 12's last third landed 2026-09-15** — `routes()` takes an expansion
budget and returns `(routes, truncated)`; `truncated` is in `--json` and in
both text renderings, on both readers, and SR-GRAPH decision 17 carries it.

⚠ **There is no MCP surface for `truncated`, because there is no `fux_path`
tool.** The compare doc's *"`--json` and MCP carry it"* names a surface that
does not exist — `fux_related` returns a neighbourhood, not a route. Stated in
SR-GRAPH 17c rather than quietly dropped.

⚠ **Two-reader check done and it is byte-equal on `truncated`.** The one
difference found is `"reliability": 1.0` against `1` — `json.dumps` against
`JSON.stringify`, already recorded in
[SR-NODE-SEARCH](../../records/0153_node-search.md), present in the confidence
block too, and **not this change's**.

# W-140 — defects found while writing the operating guides

**Model: Opus** — each row needs a call on whether the code or the record is
wrong, and several touch the refer plane, PII and receipts.

**Provenance.** Found 2026-09-11 in a Cowork session by five drafting agents and
one adversarial reviewer, reading `src/fux/` and running verbs on a copy of the
tree (Linux, Python 3.12, no network). **Each row is re-derived on the Mac
before it is fixed** — rule 4, and row 1 held up exactly as filed. Row 19 is
this repo's own, found on macOS/CPython 3.14.

🔴 **Hazard for whoever fixes a row:** the shipped guides in
`src/fux/templates/agents/*-SKILL.md` name workarounds for rows marked **(guide)**.
**Fix the defect and edit the guide in the same change** (SR-AGENT-POLICY 15g),
then refresh this repo's renderings.

## 1 · Code defects

| # | defect | where | record |
|---|---|---|---|
| 12 | ✅ **RULED 2026-09-14 (Arpit): (c) bound the walk's work, (b)'s message as the truncation notice — build it.** Was: HANDED OVER 2026-09-12 — the compare doc exists and the fork is Arpit's. [`compare/path-hops-bound.compare.md`](../compare/path-hops-bound.compare.md), with the measurement the row lacked: **0.65 s at `--hops 2`, 84.6 s at `--hops 6`**, ~11× per hop above 4, on a 738-node / 4 446-edge index with hubs at out-degree 260 and in-degree 152. Proposed verdict **(c) bound the walk's work**, with `truncated` in every rendering including `--json` and MCP. **Nothing is implemented and nothing should be until he rules** | `graph/walk.py`, `cli.py` | SR-GRAPH |

| 21 | ✅ **Answered 2026-09-15, and the diagnosis was aimed at the wrong window.** A soak (`tools/runner-race/soak.py`) drove the second commit across a live runner **104 times, 67 of them inside the run** — the stranding this row waited eleven attempts for did **not** fire, and is now *unreproduced* rather than *waiting* (⚠ not *closed*: the surviving ordering needs a delay inside `run_once`). What DID fire, twice in the soak and once in `tests_e2e` itself, is a different race: `git add -A` dies on `.fux/index/<shard>.jsonl.tmp`. **Fixed as W-185** — 0 failures in 3 871 probe runs against 2 335 of 3 933, six green `test_maintenance.py` runs. ⚠ **Nothing proves the 2026-09-12 failure was either one**: that output was never captured, which is what this row said to do | `tests_e2e/test_maintenance.py` `_drain` | SR-MAINTENANCE |

### Row 21 — what was tried on 2026-09-12, and why nothing was changed

**11 attempts, 0 reproductions**, on the machine and tree where it first failed:

| attempt | shape | result |
|---|---|---|
| 1 | `tests_e2e/test_maintenance.py` alone | 13 passed, 1 skipped |
| 2-9 | `tests tests_e2e -k "two_commits… or post_commit_defers or maintenance"` ×8 | all green |
| 10-12 | the **full** combined `tests tests_e2e` ×3 — the shape it failed in | all green (3 unrelated failures, none this test) |

⚠ **Attempts 10-12 ran while a 10 000-document corpus was being generated and
indexed in another process**, so the machine was loaded — the condition row 19
records as making its own race *more* likely, not less. It still did not fire.

**A hypothesis is recorded and deliberately NOT acted on.** `_drain` polls
`doctor --json` for `running == false and pending == 0` — and **both are true in
the window before a detached runner has started**, between `post-commit`
returning and the runner taking the lock. A `_drain` that lands in that window
returns `True` having waited for nothing. That would explain a load-dependent
one-in-many failure exactly.

🔴 **It is a hypothesis, and row 19 is why it stays one.** Row 19's first
diagnosis was confident, wrong, and cost two sessions; its gate did not hold and
the third failure gave the real answer. **Changing `_drain` now would be the same
mistake in the same file** — and a `_drain` that waits for a runner to *appear*
would hang forever in the legitimate case where the hook found nothing to do.

**What would settle it, cheaply:** have `_drain` record the runner's `last_run`
before it starts polling and refuse to return `True` until that value has
changed. That is a *stronger* wait with no new failure mode — but it is still a
change to the thing under suspicion, so it waits for one captured failure.

## 2 · Records that disagree with the code

✅ **ALL THIRTEEN CLOSED 2026-09-12**, each re-derived against `src/fux` on the
Mac first (rule 4). **Seven were the record's fault and six were the code's** —
which is the reason this section was worth working through rather than
rubber-stamping: the guess *"the code is right, fix the docs"* would have been
wrong half the time.

| # | verdict | what landed |
|---|---|---|
| freshness states | **record** | SR-REFER d19 and SR-ASK said **SIX** and then listed five; `Verdict.label` returns five and the schema enum has five. An off-by-one from the day `as-ingested` joined a four-state set. `freshness.py`'s *"SIXTH position"* corrected too |
| `passage.ordinal` | **both, opposite ways** | **`--json` was the CODE's fault** — two accepted records promised the field and the payload never carried it; `Citation` gains `ordinal` and `answer.passages[]` emits it, pinned through `subprocess` because a unit test on the dataclass would have passed all along. **MCP was the RECORD's fault**: `fux_passage` reads a line span off disk and has no ordinal to carry; the clause is withdrawn |
| `digest.sha256` | **code** | A fux `sha` is a **40-hex blake2b-160**, and the in-toto attestation labelled it `sha256`. in-toto's `DigestSet` is keyed **by algorithm**, so an external verifier would hash with SHA-256, get 64 characters, and report a mismatch **on a perfectly good receipt** — a failure landing off this machine with no route back. Emits `blake2b-160`; **reads `sha256` forever**, because every receipt already in a ticket carries it |
| `--journal` | **record, and a fork filed** | d10 said *"only `--journal` WRITES"*; `[cli.answer] journal = true` writes too, and d10 had explicitly reserved always-on journalling as a fork *"no session may pick"*. **Not picked here** — SR-PROVENANCE and SR-OUTPUT both now say what is true, and W-147 (**shipped 2026-09-13**) asks Arpit the one question |
| SR-FIND veto 4 | **record** | It grepped `^\[band\]`; the line is `confidence: …`. **A veto check that cannot fire reads as passing**, which is worse than no check |
| graph schema | **record** | `graph.schema.json` described a plane that has never existed: kinds `supersedes`/`links` (really `ref`/`code`/`tag`), `grade` as a string (an int, 10/8/6), community labels as ints (strings, `c0`). ⚠ `plane.load()` **validates against that file**, so the fiction was one type check from refusing every real graph |
| stale graph plane | **code** | SR-GRAPH and `plane.py` both said a stale plane *"is refused"* and **nothing checked**. An `ingest` with no `build` left `explain`/`graph`/`path` answering from edges the records no longer carry. `load()` now calls `accel.is_fresh` — reused, not reimplemented |
| SR-MCP | **record, three claims** | The server does **not** hold the index open (it re-reads per call) — and the consequence was stated **backwards**, telling an operator to restart a server that did not need it. `fux_passage` does not fetch or re-score. `fux_related` is one hop, not routes. Mermaid **and** its ASCII twin updated together |
| doctor levels | **record** | `refusal rules`, `decoder bindings` and `fuxignore usable` are `warn` on content and **`error` on a parse failure**; the table said `warn`. The code is right — a policy file the engine cannot read is what `tune.toml` taught (d10) |
| doctor writes | **code** | `fux doctor` **created `.fux/` and `.fux/runtime/CACHEDIR.TAG`** on a repo that had never seen fux — read-only is its first sentence. Two causes two modules apart: the writability probe `mkdir`'d, and `maintain/daemon.py`'s path helper called `derived_dir` **from a pure read**. The test asserts on the **whole tree**, because the second cause was nowhere near the check that exposed it |
| `.fuxignore` | **record** | SR-DOTFUX said *"never rewritten"*; `fux ingest` rewrites two delimited blocks at its top, above every hand-written line. It is the one committed file under `.fux/` a verb edits — exactly the fact that table exists to carry |
| version-mismatch error | **code** | It said *delete `.fux/index/` and run `fux ingest`*, *"safe because the index holds statistics, never content"* — **the one remedy SR-INDEX-LIFECYCLE d10a exists to prevent**, with a reassurance that is false for every `url:` record. Names `--full` now and warns off the delete |
| `meta` / bare `fetch=` | **record, twice** | A line's `meta=hashed` **does** win over a source-wide `plain` — the claimed "no way to be stricter" was never implemented (and nothing leaks either way). And a bare line takes **whatever `[sources.url] fetcher` names**, not `http` — SR-CONFIG d5 contradicted its own next paragraph, the W-83 shape |
| `[agents]` / SR-TUNE / SR-OUTPUT | **record** | The config diagram and its twin said **three** vendors (`codex` missing) where the code has four. SR-TUNE said **six** tables — `[index]`, the one table that is the declared exception, was missing; *"measured — `fux tune`"* named a verb that only prints the specimen; **d10a's `[priority]` orphan warning is UNBUILT** and now says so. SR-OUTPUT §1 still drew a `[defaults]`/`[verb]` file that has not existed since the three-root rewrite |
| doctor & never-fetched URLs | **code** | SR-MAINTENANCE d5a forbids hooks touching the network and pays for it with *"that is a delay, not a silence — `fux doctor` reports them"*. **It did not.** Every line of the row came from `url:` records **in the index**, and an unfetched line has none. Built as *listed minus indexed*, loudest in the `none indexed` branch where *"no URLs"* and *"five waiting on a fetch"* had read identically |

<details>
<summary>The original list, kept verbatim — what was claimed before any of it was re-derived</summary>


- **SR-ASK / SR-REFER d19 / `output.schema.json`** say six freshness states; `Verdict.label` has five.
- **SR-ANSWER d9, SR-REFER d17**: `passage.ordinal` in `--json`/MCP — absent.
- **SR-PROVENANCE d11**: `digest.sha256` is a 40-hex blake2b, not SHA-256; d10 says only `--journal` writes, but `[cli.answer] journal` does too.
- **SR-FIND** veto check 4 greps `^\[band\]`; the line is `confidence: …`.
- **SR-GRAPH / `graph.schema.json`**: edge kind `supersedes` unlisted; grades are ints, not strings; labels are `c0`; a stale plane is not refused.
- **SR-MCP**: `fux_passage` does not fetch or re-score; `fux_related` returns edges only; citations are document-level; the index is not held open.
- **SR-DOCTOR**: `refusal rules`, `decoder bindings`, `fuxignore usable` fail as errors, not warnings; doctor creates `.fux/` and `CACHEDIR.TAG`.
- **SR-DOTFUX**: says `.fuxignore` is never rewritten; ingest rewrites its skip blocks.
- **SR-INDEX-LIFECYCLE 10a** warns against deleting `.fux/index/`; the version-mismatch error tells users to.
- **SR-URL-LIST**: a line's `meta=hashed` does win over a source-wide `plain`; **SR-CONFIG d5**: a line with no `fetch=` uses `[sources.url] fetcher`, not `http`.
- **SR-CONFIG**: absent `[agents] install` means four vendors; `Config`'s default and `config.schema.json` lag (missing `keep`, `ttl`, `enrich`, `update`, `sweep_minutes`, `acquired_max_bytes`).
- **SR-TUNE**: `fux tune` prints defaults and measures nothing; `[priority]` warnings are unbuilt; seven tables, not six. **SR-OUTPUT §1** still shows the old `[defaults]` layout.
- **SR-MAINTENANCE 5a**: doctor does not report never-fetched hand-added URL lines.

</details>

## Closed so far

- **Row 22 — row 9's own correction crashed on Windows, for one character.**
  Found 2026-09-12 by running the suite, not by reading. The fixed
  version-mismatch message opened its warning with `⚠`; `cp1252` cannot encode
  it, so `print()` raises `UnicodeEncodeError` and **the command dies instead of
  rendering the remedy** — on the Windows-first fleet `CLAUDE.md` §Litmus names
  as a design input. The remedy a reader most needs is the one they would never
  have seen. `WARNING:` now.
  [SR-INDEX-LIFECYCLE](../../records/0108_index-lifecycle.md) decision 10a
  carries it, with the general shape: **a message that names a remedy has to be
  printable wherever the error it explains can happen.**
  ⚠ **`tests/test_windows_console_safe.py` already forbade this and was already
  red** — the character arrived with row 9's fix on an uncommitted tree, so
  nothing was failing in CI because nothing had been committed. No guide change.
  2026-09-12.


- **Row 1 — URL citations were never verified live.** Reproduced on macOS by
  reading the contract on both sides and asserting it, fixed in
  `refer/source.py` by routing the live fetch through ingest's own `_unpack`
  and `_decode_fetched`, recorded as
  [SR-URL-FRESHNESS](../../records/0147_url-freshness.md) decision 6a with
  SR-REFER decision 23's false sentence corrected. `ANSWER-SKILL.md` and
  `FETCHER-SKILL.md` lost the workaround they named, and this repo's four
  renderings of each were refreshed. 2026-09-11.

- **Row 2 — PII past redaction.** Both halves reproduced on macOS first. The
  frontmatter `title:` is now redacted in the same pass as the body, so the
  title field and its terms are built from redacted text
  ([SR-PII](../../records/0148_pii.md) decision 19a). **A path cannot be
  redacted** — `loc` is an address and `id` is the index's key — so ingest
  prints a note naming the documents whose path matches a rule (19b). The
  pinned "exactly two redaction sites" test was the thing that caught the
  title as a third source; it now pins four and says why. `PII-SKILL.md` and
  its four renderings updated. 2026-09-11.

- **Row 3 — `fux add <URL> --no-update` never fetched.** Three artifacts
  promised the one fetch (SR-URL-LIST decision 14, `--help`, the CHANGELOG)
  and the pin filter, which runs above `fetch_all`'s grouping, knew nothing
  about an add. `cmd_add` now passes the URL it just wrote as `first_fetch`,
  and a test pins that the set has exactly one populator — a wider one would
  make the pin advisory. ⚠ **A pinned line written by hand is still never
  fetched**: recorded in decision 14 as the gap it is, owed to
  SR-MAINTENANCE 5a. 2026-09-11.

- **Row 4 — `fux update --failed` was parsed and never read.** It fell through
  to the ordinary narrow pass, fetching the *stale* set and reporting that as a
  success. It now selects `fail_streak > 0` intersected with what is still
  listed, and wins over `--all` as the more specific selector. SR-CLI carries
  what a verbatim surface capture cannot prove: that a flag is read, not merely
  accepted. 2026-09-11.

- **Row 19 — the merge-driver e2e test asserted a number that is not a
  property of the merge.** ⚠ **The first diagnosis was wrong and the first gate
  did not hold** — it failed again the same day with the quiesce in place, and
  the third failure is what gave the real answer.

  - **What it asserted:** `ver == 2` on both records after the merge. `ver`
    counts how many times a document's sha has **changed relative to the index
    it is compared against** — and this fixture bounces between three checkouts
    on a hooked repo, where `post-commit` spawns a detached re-index. How many
    passes land against which committed shard varies with machine load. It was
    observed at **1** (a pass had not landed) and at **4** (several had), and
    neither number says anything about whether the driver merged correctly.
  - **What it asserts now:** each record's `sha` equals the content sha of the
    merged file on disk — *the index describes the merged working tree*, which
    is the claim the test exists to make, and nothing about scheduling can
    inflate it. `ver >= 2` keeps the *an edit happened* signal.
  - **`quiesce()` stays and moved earlier** — after every hooked commit, not
    just before the final read. Staging a shard a detached runner may be
    rewriting is a real hazard even when nothing asserts on it.
  - ⚠ **The merge driver was never the defect**, and two sessions' worth of
    suspicion pointed at it because the failing assertion sat under it.
    2026-09-11.

- **Row 13 — `fux doctor` had no `tune.toml` row.** The worst shape for this
  file: `fux ingest` reads only `[index]`, so a bad ranking knob leaves a clean
  index and a green doctor while every query in the repo refuses. `doctor` now
  calls `tune.load` and quotes its refusal — an **error**, not a warning, unlike
  an absent `output.toml`. [SR-DOCTOR](../../records/0152_doctor.md) decision
  10. `CONFIG-SKILL.md` and all three config pointers lose the workaround.
  2026-09-11.

- **Row 8 — unknown `fux.toml` keys are silently ignored — MOVED to W-122, not
  fixed here.** The fix is a key set to validate against, and
  W-122 already owned exactly that as gate R-2, and **landed it on 2026-09-12**
  ([IMPLEMENTATION](../IMPLEMENTATION.md) §W-122):
  *SR-CONFIG's fenced key tree ↔ `config.py`, both directions, so a key is
  real only if it is in the tree*. Hand-writing a second key set here would
  create the duplicate source of truth W-122 exists to remove — and this defect
  (`types_file`, `acquired_max_bytes`) is the evidence for that gate, not a
  separate task. 2026-09-11.

- **Row 12, the two halves that were defects rather than forks.** `fux path`
  validated neither end: a typo printed *No route … within N hop(s)* and exited
  **0**, byte-identical to the honest answer for two real unconnected documents.
  `explain` had been fixed for this in W-63 and the verb beside it kept it —
  so the check is now one function both verbs call. A `tag:` id was never
  checked on either verb, because the test read the committed index and a tag
  has no record there; the **plane** answers for tags now.
  [SR-GRAPH](../../records/0126_graph.md) carries both, plus the control
  test that honest emptiness still exits 0. `GRAPH-SKILL.md` loses *"run
  `fux explain` on both ends first"*. **The `--hops` third of the row was a
  fork until 2026-09-14, when Arpit ruled (c)** — see the compare doc's §3 for
  the exact build list. 2026-09-11, ruled 2026-09-14.

- **Row 9 — the merge driver's refusal named a fix that could not work.** It
  said *re-run `fux ingest`*, and ingest cannot read the file the refusal had
  just written: it holds both sides with conflict markers. What the reader got
  was a shard-header error reading as corruption. Both halves fixed — the
  message names taking either side first (a shard is derived, so either is
  safe), and the reader diagnoses markers as markers before parsing the
  header, the way `tune.toml` and `output.toml` already did.
  [SR-MERGE-DRIVER](../../records/0130_merge-driver.md) and
  [SR-INDEX-LIFECYCLE](../../records/0108_index-lifecycle.md). 2026-09-11.

- **Row 10 — `[cli.json] enabled = true` turned `fux hooks` into a report.**
  The verb selected report-instead-of-install from `args.json`, which the
  output config fills — so a repo that renders JSON had a `fux hooks` that
  installed nothing and printed a true report of a repo nobody had wired.
  `--status` selects the mode now; `--json` selects only the rendering, and the
  resolver keeps the flag as typed so an explicit `fux hooks --json` still
  reports. **SR-OUTPUT's claim that a rendering config's blast radius is the
  resolver was false for one verb** and now says so. 2026-09-11.

- **Row 18 — the four small ones, all four of them statements fux shipped that
  were not true.** `.fux/.gitignore` now carries `__pycache__/` (by name, as a
  directory — a wildcard would drop a consumer's committed decoder from git);
  `fux setup` announces a **hand-written** `AGENTS.md` rather than re-printing
  the whole template at the file it wrote itself, decided by the policy marker;
  the starter `urls` header is **derived from the list spec**, so it can no
  longer say *two attributes* while there are seven, or promise a full sweep
  `fux update` stopped doing; and the starter `pii.toml` and `doctor`'s
  redaction note stop pointing at `tools/pii-probe/probe.py`, which is in the
  repository and not in the wheel. SR-DOTFUX, SR-PII decision 20, SR-DOCTOR.
  2026-09-11.

- **Row 17 — the shipped refusal policy refused real wiki pages, and promised a
  warning that does not exist.** `requested_suffix_not` means *this URL asked
  for a web page* and listed only `.html`/`.htm`, so the file's highest-value
  rule refused every `viewpage.action`, `Page.aspx`, `index.php` and `.jsp`
  document. Both suffix rules carry the server-page extensions now, and the
  cases they exist for are pinned unchanged (a `.xlsx` answered in HTML; a
  216-byte stub at a share link). **There is no warn level** — the comment
  claiming one is gone, and a test pins that no `warn` field exists so the
  prose cannot drift back before the code does.
  [SR-REFUSAL](../../records/0146_refusals.md). ⚠ Write-if-missing, so no
  existing repo gets the fix. 2026-09-11.

- **Row 5 — `fux add` overrode the consumer's own `[sources.url]`.** Every
  generated line states every attribute (decision 12) and the values came from
  `spec.defaults()`, the **engine's** built-ins — so a repo configured with
  `ttl = "7d"` got `ttl=24h` written onto every line the CLI produced, and the
  middle layer of a three-layer resolution was dead for all of them. The line
  now states the **resolved** value, so decision 12 is whole and the word it
  states is the consumer's; an explicit flag still beats both.
  [SR-URL-LIST](../../records/0116_url-list.md). 2026-09-11.

- **Row 15 — `timeout_seconds` bounded nothing.** Validated at construction,
  stamped into every answer bundle, printed by `--audit`, read by nothing: a
  consumer fetcher that blocked forever hung `fux answer` behind a number that
  read as a guarantee. The fetch runs in a worker and the query stops waiting
  at the deadline — a bound on *waiting*, which is the only honest one, since
  Python cannot interrupt a blocking socket in consumer code. A timeout raises
  `FuxError`, so it degrades down the path that already existed.
  [SR-REFER](../../records/0127_refer-plane.md). 2026-09-11.

- **Row 11 — the background runner never rebuilt the accelerator.** Every CLI
  verb builds it where the shards are written so `ask --fast` never pays; the
  runner called `run()` directly and skipped it, leaving the one derived plane
  stale after every background pass and handing the cost to the next query. It
  builds now, best-effort and after the outcome is decided — a disposable plane
  must not turn a correct re-index into a reported failure — and the result is
  recorded in the run status.
  [SR-MAINTENANCE](../../records/0129_hooks.md). 2026-09-11.

- **Row 6 — every `ttl=` in every repo was dead at ask time.** `answer` built
  its policy with `cache_ttl_seconds` at the default `0`, and decision 11
  resolves the interval as `min(policy, line)` — so `min(0, 86400)` made the
  `cached` verdict unreachable by construction. The arithmetic was right;
  nothing could set its left operand. `--cache-ttl` is the way to ask, parsed
  by the source list's own duration grammar; the default stays `0`, so W-60
  verdict F holds. ⚠ **The row's third claim was wrong**: `update=never` not
  stopping an answer-time fetch is SR-URL-FRESHNESS decision 15 working —
  `ttl=` is ask-time, `update=` is update-time, and merging them is what that
  decision exists to prevent. 2026-09-11.

- **Row 7 — `fux verify --rerun` fetched, in the one verb ruled never to.**
  It called the refer plane, so SR-PROVENANCE decision 14 — *`fux verify`
  NEVER FETCHES*, Arpit, 2026-08-27 — was contradicted by the code for sixteen
  days, and the failure that decision names in its own words (one receipt, two
  machines, different verdicts) was the shipped behaviour. The re-run re-ranks
  from the committed index alone now, and a refer-path receipt is
  `unverifiable` naming the ruling. 🔴 **And the comparison read only the
  digest** — an index-path subject has none by design, so `""` compared equal
  to `""` and an index receipt could report `reproduced` against a different
  document. Cited documents compare as `(name, sha)`. 2026-09-11.

- **Row 20 — the freshness gate demanded records with nothing to say.** A
  describer row may now narrow itself to symbols (`` `path::name,name` ``), and
  the gate demands that record only when the change touches one of them. A bare
  path still means the whole file, and an undecidable diff demands everybody —
  **it narrows on a fact, never on a guess**. ⚠ **Two rows narrowed, not
  twenty**: a too-short list disables a record silently, which is worse than the
  noise, so a row is narrowed only by someone who has read that record's whole
  reach in the file. [SR-WORK-OWNERSHIP](../../records/0054_WORK-ownership.md).
  2026-09-11.

- **Row 14 — the verb built to be read had nothing to read.**
  `fux update --check` exits 0 whether or not anything drifted — deliberately,
  since drift is a fact and a non-zero exit makes *your docs changed* look like
  a broken command — and it had no `--json`, so the only way to act on the
  answer was to parse a table meant for a person. `--json` emits
  `{drifted, fresh, unchecked_urls}`, built beside the text rather than parsed
  out of it, and still exits 0. `update` joins `CLI_VERBS` with an empty tuple
  and gains `--no-output-config`, which SR-OUTPUT decision 15 requires of any
  verb that reads the file — **caught by its own test before the change was
  committed.** 2026-09-12.

- **Row 16 — the record was too narrow; the code is as designed.** Reproduced
  on macOS: a `pii.toml` edit followed by an offline `fux ingest --full`
  redacted the `file:` document and left the `url:` record's title carrying the
  address. **SR-PII decision 18 said *a pinned URL*; the truth is every `url:`
  record that was not fetched this run**, and an offline ingest fetches none.
  Widened there, with the `run.py` comment's *"invalidates every carried
  extraction"* corrected to mean every carried FILE extraction. ⚠ **The fix
  stays declined** (decision 18's own call) — but the cost objection is
  recorded as weaker than it reads, because the re-derivation would only ever
  happen on a policy edit, which already costs a full re-extract. **No guide
  change: the guide already said it generally, ahead of the record.**
  2026-09-12.

## Definition of done

Each row: reproduce on the Mac, then fix the code **or** amend the record, update
any guide marked **(guide)**, re-render this repo's copies, and delete the row.
The file closes when both sections are empty.

## From OPEN-WORK (moved 2026-09-11)

*Moved here verbatim when OPEN-WORK became one-to-two-line rows (Arpit, 2026-09-11). Links are rewritten for this directory.*

*This is what the queue said at the move. Re-derive it before believing it (OPEN-WORK rule 4).*

- 🔴 **W-140 — the defects writing the operating guides uncovered.** `agent` · *(records:
  SR-REFER · SR-PII · SR-URL-LIST · SR-PROVENANCE · SR-MAINTENANCE · SR-CONFIG ·
  and the disagreements listed in the file)* · Checking ten new skills against the code
  (SR-AGENT-POLICY decision 15) found **18 code defects** and **13 records that disagree with the
  code**. ⚠ Guides name workarounds for several: **fix the defect and the guide in one
  change.** **Row 1 is closed** (URL citations were never verified live — the refer plane
  rejected the fetcher contract's tuple, so no `url:` citation ever reached `current`;
  fixed, recorded as SR-URL-FRESHNESS 6a, both guides and all four renderings updated).
  **Row 2 is the remaining 🔴** — a frontmatter `title:` or a filename carries PII past
  redaction. Row 19 was added from this repo's own suite. —
  [detail](W-140-guide-authoring-defects.md) `filed: 2026-09-11`
