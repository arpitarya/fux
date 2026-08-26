---
type: OpenItem
id: W-82
title: "W-82 — the consolidated build: five phases shipped, two measurements owed, and twenty-seven rulings that are Arpit's"
description: "One document replacing W-74, W-75, W-77 and W-81 and the five docs behind them. The BUILD is closed out — five phases shipped in 2.0.0-alpha.2 with nine records amended and 1 433 tests green. What stays open is not code: twenty-seven forks that are Arpit's, and two measurements whose corpora do not exist. Carries the folded verdicts and the withdrawn prepare-then-ask so nothing became uncitable."
status: open
lane: arpit
timestamp: 2026-08-26T00:00:00Z
---

# W-82 — the consolidated build

> ## ✅ THE BUILD IS CLOSED OUT (2026-08-26). WHAT REMAINS IS NOT CODE.
>
> **Five of the six phases shipped in `2.0.0-alpha.2`** — §3.1 the URL health
> report, §3.2 the detector, §3.3 parallel fetch and the cap, §3.4 the
> changed/unchanged line, §3.6 the agent surface. Nine records amended in the
> same change; **1 433 unit tests green**. The outcome is a row in
> [`IMPLEMENTATION.md`](../IMPLEMENTATION.md).
>
> ⚠ **THE ITEM STAYS OPEN, AND DELETING IT WOULD BE THE BUG.** Its row is not a
> tombstone — it now carries exactly three kinds of live work, none of which an
> agent may close:
>
> | still open | why it cannot be closed by building |
> |---|---|
> | **§5 — twenty-seven forks** | every one is a judgement about what counts as success, and OPEN-WORK rule 5 puts them in the `arpit` lane |
> | **§3.0 — the Phase 0 measurement** | needs a **real URL corpus**, which does not exist on any machine this has run on |
> | **§3.5 — the measurement apparatus** | needs **`fux-playground`**, same |
>
> **Neither missing phase is a coding task**, and producing a number for either
> without its corpus is precisely the failure ADR-RS exists to prevent.
>
> ⚠ **`tests_e2e/` IS UNVERIFIED and must be run before release.** It spawns the
> real CLI and fails **identically — 55 failed / 11 errors — on a CLEAN TREE**
> in the build environment (Python 3.10 only; the unit suite ran under a
> harness-only `tomli`→`tomllib` shim that never enters the repo). Identical
> before and after means **no regression**. It does **not** mean green.

**Filed 2026-08-26 on Arpit's instruction**, replacing four open items and five
supporting documents with one file.

| replaced | now |
|---|---|
| `W-74` answer-quality measurement contract | §5.2 |
| `W-75` URL freshness | §3, §5.1 |
| `W-77` record reconciliation | §5.3 |
| `W-81` the sealed set and the two controls | §3.5, §5.4 |
| `proposals/url-freshness.md` | §2, §3 |
| `proposals/measuring-answer-quality.md` | §5.2 |
| `proposals/prepare-then-ask.md` | **§6.0 — folded in verbatim**; §1 and §3.4 |
| `compare/url-refresh-trigger.compare.md` | **§4.1 — verdict folded in verbatim** |
| `compare/url-fetch-concurrency.compare.md` | **§4.2 — verdict folded in verbatim** |
| *(new 2026-08-26)* the agent surface + the venv ladder | **§3.6** |

⚠ **The two compare verdicts were folded in, not summarised.** Archiving a
compare doc makes its verdict uncitable (*archive is not evidence*), and §1's
calls rest on those verdicts. §4 is therefore the live home of both, including
their reopen triggers. **Their archived originals may be named, never cited.**

⚠ **`prepare-then-ask` was folded in the same way (§6.0), on Arpit's
instruction of 2026-08-26** — its two flags are **withdrawn**, but the three
findings underneath them are not, and they would have been lost to the archive.
**§6.0 is the live record.**

**Model:** **Opus** for every fork in §5 — each is a judgement about what counts
as success, and a metric chosen badly is wrong *quietly* for months. **Sonnet**
for §3.0's measurement once a corpus exists, which is mechanical against a
frozen threshold.

*(The build's model guidance is spent: §3.2's L3 argument, §3.3's thread-safety
argument and §3.6's ladder all landed 2026-08-26.)*

---

## §1 — The four calls made on 2026-08-26

| | call | grounded in |
|---|---|---|
| **content store** | **not built** — reasoning in §6 with a reopen trigger | new; no prior proposal |
| **detector** | **query-driven dirty list**, unconditional; the clock is a separate fork | §4.1 verdict E |
| **answer-time fetch** | **every cited URL fetched before the final answer** — cited sources only, not the whole ranked window | Arpit, 2026-08-26 |
| **concurrency** | **declared capability**, `min(declared, configured)` | §4.2 verdict C |

### The ruling that shaped the rest

> *"If it is a URL, then the actual document should be fetched before giving the
> final answer so that we know whether the document is correct or not."*
> — Arpit, 2026-08-26

**Two consequences, both load-bearing.**

1. **It is already shipped.** `fux answer` fetches each cited URL, compares
   `fetched_sha` against `indexed_sha`, and returns `current` / `stale` /
   `unverified` / `cached`
   ([`refer/freshness.py`](../../src/fux/refer/freshness.py)). The refer plane
   has been on `answer`'s default path since P6.

2. **It collapsed `prepare-then-ask`.** If the bytes are fetched regardless, a
   warmed content store saves nothing on the answer path, and an answer memo
   caches the output of a pure function whose inputs were just downloaded.
   **`update --warm` and `answer --memo` are both withdrawn.** What survives is
   §3.4 alone.

---

## §2 — The gap that survives the ruling

**Fetching at answer time fixes correctness and cannot fix recall.**

```
a URL changes upstream
  → the index still holds the OLD terms
  → the document does not rank into the candidate window
  → it is never cited
  → it is never fetched
  → nothing ever notices
```

**A stale `url:` record costs recall, not correctness.** It cannot be
mis-answered; it can only fail to surface. That is the ceiling on what this work
is worth, and it is why §3 is priced as buying the weaker good.

It bites hardest exactly at the design point: at 10 000 documents inside a
corporation, the tail nobody has queried yet is most of the corpus.

**A file change is an event. A URL change is not.** Everything in §3 follows
from that one asymmetry.

---

## §3 — The six phases — five SHIPPED, two measurements owed

> **BUILT 2026-08-26: §3.1, §3.2, §3.3, §3.4 and §3.6.** Five of the six landed
> in one change with their records amended (ADR-DOTFUX, ADR-INGEST, ADR-REFER,
> ADR-MAINTENANCE, ADR-ANSWER, ADR-ASK, ADR-AGENT-POLICY, ADR-FETCHER,
> ADR-CONFIG) and **1 433 unit tests green**.
>
> ⚠ **§3.0 and §3.5 did NOT land, and neither is a code task.** §3.0 needs a
> real URL corpus to run `fux update` twice against; §3.5 needs
> `fux-playground`. Neither exists on the machine this was built on, and
> inventing a number for either is the failure ADR-RS exists to prevent.
>
> ⚠ **`tests_e2e/` is UNVERIFIED here**, and honestly so: it spawns the real
> CLI and fails identically (55 failed / 11 errors) on a clean tree in this
> environment. **Identical before and after**, so this change introduces no
> regression — but *green* is not a claim anyone may make from here.
>
> ⚠ **Three corrections the build made to this document's own plan**, each
> found by reading the code rather than the spec, and each left visible rather
> than edited away:
> 1. **`url-state.json` may NOT carry `validated_at` / `changed_at`.**
>    `refer/fetchcache.py` states the invariant ADR-REFER rests on — *wall clock
>    lives in the TTL store and nowhere else*. Freshness is counted in
>    **networked runs**, not seconds.
> 2. **Kiro was already in `KNOWN_AGENTS` and `AGENT_FILES`**, shipping a
>    `.kiro/steering/` file. §3.6 said it needed adding; it needed *extending*.
> 3. **Rung 4 is `python -m fux.cli`, not `python -m fux`.** `fux.cli` is
>    already importable and already used by `tests_e2e/`, so the ladder is
>    complete **without** adding `src/fux/__main__.py` — which retires fork B's
>    urgency, though the fork itself stands.

### 3.0 · Phase 0 — the measurement that rules fork 3

**No new code.** Run `fux update` twice against a real URL corpus; count the
fraction of fetched documents whose **sanitized** sha was unchanged.

| result | consequence |
|---|---|
| **≥ 80 %** | fork 3 is **yes** — the contract gains an optional `validate` |
| **≤ ~40 %** | the contract stays at four functions; this item shrinks to §3.1–3.2 |
| between | **ambiguous → Arpit, unadjudicated** (CLAUDE.md §pre-registered thresholds) |

- Files under [`../regression/`](../regression/README.md) per the conformance-run contract.
- ⚠ **Classification is `informed`** — whoever runs it will have read this file.
  That is the correct label, not a reason to delay.
- ⚠ **It collides with §5.4.** This is a *cost* measurement made entirely of
  deltas, and ADR-RS decision 12 as written forbids an informed run from
  supplying one. **Disclose the conflict in the report; do not self-exempt.**

### 3.1 · Phase 1 — the URL health report

**The failure today is not that the index is stale — it is that it is
*silently* stale.** This half fixes that alone and is the cheapest thing here.
**It ships whatever else is ruled.**

- `fux doctor` gains a URL section: how many `url:` records exist · how many
  were validated in the last run · how many have never been re-fetched since
  first ingest · how many are failing.
- A `fail_streak` counter behind it, in `.fux/runtime/url-state.json` —
  gitignored and derived, the same treatment `stamp.json` and the fetch cache get.
- **Report, never auto-delete.** [ADR-URL-INGEST](../../docs/adr/0008_url-ingest.md)
  decision 4 forbids treating a failed fetch as a deletion. **A permanently dead
  URL therefore lives in the index forever** until a human removes its line —
  the counter makes that consequence visible rather than silent.

**Current state:** [`doctor.py`](../../src/fux/doctor.py) has **no URL check at
all** — its checks are the background runner, the Python version, the repo root,
the layout and the accelerator.

**Record:** ADR-URL-INGEST.

### 3.2 · Phase 2 — the detector

**Both halves already exist.** The refer plane computes `fetched_sha`, sees it
differ from `indexed_sha`, renders `stale` — and throws the knowledge away.

**The change: record that doc id in the dirty list.**

- [`maintain/dirty.py`](../../src/fux/maintain/dirty.py) — the append-only,
  union-not-replacement, gitignored list `post-commit` already writes.
- `ingest.run(only_urls=…)` ([`ingest/run.py`](../../src/fux/ingest/run.py)
  line 110) — already the parameter that narrows a networked run to a named
  subset, built for `fux add <URL>` in W-63.
- **New code: one call site in `refer/`, plus a filter mapping `url:` doc ids
  back to URLs.**

**Why this beats any scheduler:** prioritisation comes out **usage-weighted for
free**. Documents people retrieve get verified constantly because they are
cited; staleness in a document nobody retrieves is staleness nobody pays for.
That is the frequency-weighted freshness objective the crawl literature
optimises toward, except the weight is **observed rather than estimated**.

⚠ **The crux, and it must be written into the record rather than assumed.**
`dirty.py` says the list is *"advisory, never authoritative"* — the sentence
that keeps L3 true, because `fux ingest` re-walks the whole corpus regardless.
A URL refresh driven by that list **is** authoritative for the URLs it names,
because not fetching the rest is the entire point. The defence:

> The `url:` half of the index is **already** a mosaic of different moments —
> every record holds whatever its last fetch produced, and no two were
> necessarily fetched together. A partial refresh changes the *spread* of those
> moments, not the kind of object the index is. L3 is *same sources → same
> bytes*, and **a URL is not the same source twice.**

⚠ **Do not confuse this with "just index the delta"**, which was ruled **not**
the fix for R5. That was an offline filesystem walk that is already cheap; this
is a networked path that is not, and the economics invert.

**Limit, stated:** the detector only ever sees documents someone retrieved. **It
covers the head; the tail needs a clock, and the clock is fork 1.**

**Records:** ADR-URL-INGEST · ADR-MAINTENANCE.

### 3.3 · Phase 3 — parallel fetch and the cap

**The cap presumes a parallelism that does not exist.**
[`fetch_all`](../../src/fux/ingest/urlsrc.py) walks URLs in a strictly
sequential loop, sorted, grouped by fetcher, inside one `connect()`/`close()`
bracket per group. **There is no threading anywhere in `src/fux/`** — this is
the first. `concurrent.futures` is stdlib, so **L1 is untouched**; the novelty
is the argument, not the import.

**The finding that makes it cheap: sequential fetching is not what makes the
index deterministic — the sort is.** `fetch_all` ends
`fetched.sort(key=lambda f: f.url)` and `skipped.sort(...)`, so completion order
never reaches the committed bytes. **Concurrency inside that function is
invisible to L3.**

**The shape** (§4.2, verdict C):

- A fetcher module may declare `MAX_PARALLEL = n`. **Absent the declaration the
  value is 1**, and behaviour is byte-for-byte what ships today.
- Fux uses `min(declared, configured)` workers.
- **`connect()` / `close()` stay once per group, not once per worker.** That is
  what makes this safe to reason about: the lifecycle is unchanged and only
  `fetch` is called concurrently. A fetcher declaring `MAX_PARALLEL > 1` is
  declaring exactly *my `fetch` is reentrant given one `connect`*.

**Two knobs, two kinds of refusal** — Arpit's standing rule, *state the cost,
don't clamp the knob*:

| value | kind | treatment |
|---|---|---|
| `MAX_PARALLEL` in the module | **capability** | exceeding it is a correctness violation → **clamp down, loudly, on stderr**, naming the module and the number |
| `[sources.url] max_parallel` in `fux.toml` | **policy** | a large value is merely rude → **warn with the number, never clamp** |
| `max_parallel < 1` | **broken** | `FuxError`, the treatment `cache_ttl_seconds < 0` already gets |

⚠ **Why a blind pool is disqualified — and it is not "it crashes".**

| | `http.py` | `cdp.py` |
|---|---|---|
| state during `fetch` | fresh `urllib.request.Request` per call | **`global _session`** — one WebSocket set by `connect()`, reused by every `fetch()` |
| safe from N threads | **yes** | **no** |

Two threads writing frames onto one CDP socket produce **plausible documents
attributed to the wrong URLs**. That lands in the committed index, **passes
every determinism check** (the sort still runs), and is found only by a human
reading an answer. **A concurrency bug presenting as a content bug is the worst
class available** in an engine whose promise is citation fidelity.

- **`cdp.py` ships declaring `MAX_PARALLEL = 1` explicitly**, not by omission.
  Omission and `1` behave identically, but the explicit line is where the
  *reason* gets written for the consumer who copies the file and starts editing.
- **Default `4`, global** — judgement, not measurement (fork 6).
- **One test is owed that no manual checking substitutes for:** a fetcher
  declaring `1` must be **observed** never to have two `fetch` calls in flight.
  Assert with a counter inside a test fetcher, not by reading the pool code.
- **The progress plane needs no change and gains meaning** — its rule is
  *counts, not clocks*, and a count completed is still a count completed out of
  order.

**Records:** ADR-FETCHER (the contract) · ADR-CONFIG (`max_parallel`).

### 3.4 · Phase 4 — the changed/unchanged line

**All that survives of `prepare-then-ask`.**

- Remember the previous answer's cited `(loc, sha)` set in `.fux/runtime/`.
- `fux answer` opens with *"nothing has changed since you last asked"*, or names
  which sources moved.
- **It is a report, not a memo.** No answer is stored and nothing is replayed —
  every answer is recomputed on freshly fetched bytes, per §1's ruling.

**Why it needs no fifth verdict state.** ADR-REFER's four labels are
**per-citation** facts about a fetch. This is a **per-answer** statement about a
comparison between two runs. Different object, different place — no collision
with the rule that `cached` is never folded into `current`.

**Record:** ADR-ANSWER.

### 3.5 · Phase 5 — the measurement apparatus (`agent` lane, independent)

Unrelated to the URL work and blocked on nothing. **A rule that is written and
unbuilt reads as in force**, and two of the six accepted parts of the
run-classification rule are unbuilt — ADR-RS decision 15, filed `NOT BUILT`.

**The sealed query subset.** A fixed subset of `fux-playground`'s 50 queries,
held by one owner, never shown to anyone who authors an artifact, scored on
request, rotated when it leaks.

- ⚠ **It must be mechanical.** BIG-bench's canary GUID was embedded *so that*
  labs would exclude it, and a model reproduced it anyway. **A directory an
  agent is asked not to read is not sealed** — the minimum credible version is
  that the sealed queries do not live in the working tree at all.
- ⚠ **The power tension must be answered in writing, not split silently.** 50
  queries is already under-powered — TREC puts MAP error near 2.4 %, and the
  provisional floor is ±2 queries. Split 50 into 35 visible + 15 sealed and the
  sealed half's floor is *worse* than the whole set's. **Three honest options:**
  grow the set first · seal a proportion of a larger set · accept that the
  sealed half detects only large effects and say so. **Picking silently is the
  failure mode.**

**The two control arms.** *Neural Retrievers are Biased Towards LLM-Generated
Content* (KDD 2024) shows retrievers rank LLM-written text higher
**independently of whether it informs**. Every enrichment arm on file added ~70
tokens of fluent prose to nine of ten documents with no matched control, so
**text presence and text content are not separable in any number filed**.

| arm | what it isolates |
|---|---|
| **decoy queries** | a query set the enrichment was not aimed at — catches an intervention that helps because it added prose, not meaning |
| **content-free placebo** | enrichment of matched length carrying no information — the direct measurement of source bias on this corpus |

⚠ **This does not threaten the finding it qualifies.** If source bias is real
here, enrichment's *content* contribution is **lower** than measured, not
higher — and blind it was already below the floor.

**The orphaned-module check.** Three modules were deleted in two days for having
no caller — `query/hybrid.py`, `query/fuse.py`, `embed/fuxvec.py` — **all three
with passing tests the whole time**, which is exactly why none was noticed: a
tested module looks alive. The check flags any `src/` module with no importer
outside its own package and no caller outside its own tests. ⚠ **It needs a
declared-exception list** — entry points, `__init__` re-exports and
CLI-dispatched handlers all look orphaned to a naive importer graph, and a check
that cannot go green gets deleted.

**Not in scope:** re-running the enrichment arms (those reports are frozen and
stand as filed; new controls produce a **new** run), and fixing the resolution
floor's placeholder value (its own measurement, its own item).

**Record:** ADR-RS decision 15 loses `NOT BUILT` in the same change.

### 3.6 · Phase 6 — the agent surface, and the invocation ladder under it

**Filed 2026-08-26 on Arpit's instruction:** *"include all the possible skills
needed to run fux for AI agents, steering documents, or whatever would help AI
automatically understand how to use fux… and the documents should account for
`.venv` being active or inactive."*

#### What already exists — this is not greenfield

[ADR-AGENT-POLICY](../../docs/adr/0035_agent-policy.md) is **accepted and
built**. `fux setup` writes four renderings by default, from
[`src/fux/templates/agents/`](../../src/fux/templates/agents/):

| vendor | file written | template |
|---|---|---|
| claude | `.claude/skills/fux-archived-results/SKILL.md` | `SKILL.md` |
| claude | `.claude/skills/fux-enrich/SKILL.md` | `ENRICH-SKILL.md` |
| copilot | `.github/agents/fux.agent.md` | `fux.agent.md` |
| copilot | `.github/instructions/fux-archived-results.instructions.md` | (same name) |

**Both skills teach *interpretation*, not *operation*.** One is how to read an
`archived` mark; the other is enrichment. **Nothing teaches an agent how to
drive fux end to end**, and nothing at all mentions how to invoke it.

#### ⚠ The defect this phase exists to fix, and it is live today

`fux.agent.md` tells the agent to run a bare `fux ask`, and then says:

> *"If `fux` is not installed or there is no index, say so and fall back to
> ordinary search."*

**In a repo where fux is installed into `.venv` and the venv is not activated,
`fux` is not on `PATH`.** The agent gets `command not found`, concludes *not
installed*, and **silently falls back to grep** — with a correct-sounding
explanation. The engine is present, the index is committed, and the agent never
touches either.

**This is the worst failure shape available here:** it does not error, it
degrades, and the degradation is indistinguishable from an honest answer.
`fux ask` returning nothing is loud; an agent deciding fux is absent is silent.

**Confirmed against the code, 2026-08-26:**

- `pyproject.toml` declares `fux = "fux.cli:main"` — a **console script**, so it
  exists only where the installing environment's `bin/` is on `PATH`.
- **There is no `src/fux/__main__.py`**, so **`python -m fux` does not work
  today.** Any ladder that wants that rung is a code change, not a doc change.
- **No file under `templates/agents/`, `.claude/skills/` or `DOGFOOD.md`
  mentions `.venv`, `uv run`, `PATH`, `pipx` or `python -m fux`** — checked by
  grep, not assumed.

#### The invocation ladder — what the steering documents must say

**A single resolution order, written once and identical in every rendering.**
The agent tries each rung and stops at the first that answers:

| rung | probe | when it is the right answer |
|---|---|---|
| 1 | `fux --version` | the venv is active, or fux is installed globally (`pipx`, `uv tool`, system) |
| 2 | `uv run fux --version` | a `uv`-managed repo — resolves and activates without the human having done so |
| 3 | `./.venv/bin/fux --version` (`.venv\Scripts\fux.exe` on Windows) | the venv exists and is **not** active — **the case Arpit named** |
| 4 | `python -m fux --version` | ⚠ **does not exist yet** — fork B below |

**Three rules that make the ladder safe rather than clever:**

1. **Probe, never assume.** The agent runs `--version` first and **caches the
   working invocation for the session**. A ladder re-walked per call is four
   subprocesses per question.
2. **Exhausting the ladder is not "fux is not installed".** It is *"fux could
   not be invoked"*, and the steering document must make the agent **say which
   rungs it tried**. That single sentence turns today's silent degradation into
   a diagnosable one.
3. ⚠ **Never activate anything.** The agent does not `source .venv/bin/activate`,
   does not export `PATH`, does not `pip install`. It **calls an absolute path**.
   Mutating the human's shell environment to make a read-only query work is a
   side effect nobody consented to.

⚠ **`fux --version` is the probe, never `which fux`.** `which` answers *is there
a file*, not *does it run* — a stale shim from a deleted venv passes `which` and
fails on execution. And **`fux doctor` is the wrong probe too**: it is the
heaviest verb, it can legitimately exit non-zero on a healthy install, and it
needs a repo root that the probe must not presuppose.

#### The two targets: Claude and Kiro — ruled by Arpit, 2026-08-26

**The finding that makes this cheap: Kiro implements the same open Agent Skills
standard Claude does.** A skill is a folder with a `SKILL.md` carrying `name` +
`description` frontmatter, loaded by progressive disclosure — description at
startup, body on activation. **`.claude/skills/fux-archived-results/SKILL.md`
is already a valid Kiro skill.** The difference is the **path**, not the
content.

| | Claude | Kiro |
|---|---|---|
| skills | `.claude/skills/<name>/SKILL.md` | `.kiro/skills/<name>/SKILL.md` |
| steering | `CLAUDE.md` / skill bodies | `.kiro/steering/*.md` |
| vendor-neutral | — | `AGENTS.md` (supported, always included) |
| global scope | — | `~/.kiro/skills/`, `~/.kiro/steering/` |

**Consequence for `AGENT_FILES` in [`setup.py`](../../src/fux/setup.py): one
template, two destinations.** `kiro` joins `KNOWN_AGENTS` and maps the *same*
`SKILL.md` / `ENRICH-SKILL.md` / the new usage skill into `.kiro/skills/`.
**This is not a second rendering to keep in sync** — it is the same bytes at a
second path, which is strictly stronger than decision 2's conformance test
because agreement is by construction rather than by assertion.

⚠ **Three Kiro-specific traps, each checked against the docs, each capable of
silently voiding the whole phase:**

1. **Kiro CLI does not support steering inclusion modes — every file in
   `.kiro/steering/` loads on every interaction.** So a large steering document
   is a permanent context tax there, and `inclusion: manual` **does not protect
   you**. ⚠ **This is the argument for shipping fux's guidance as a *skill*,
   not as steering:** skills are progressive-disclosure on every surface.
2. **Kiro custom agents load neither skills nor steering by default.** They
   need explicit `resources` entries — `skill://.kiro/skills/*/SKILL.md` and
   `file://.kiro/steering/**/*.md`. **A consumer running a custom agent gets
   none of fux's files and no error**, which is this phase's own failure mode
   reappearing one layer up. **The skill body must say this**, because fux
   cannot write into someone's agent config.
3. **`name` must equal the folder name**, lowercase letters, numbers and
   hyphens, ≤64 chars; `description` ≤1024. The shipped `SKILL.md` already
   satisfies this — **the new usage skill must be checked, not assumed.**

**Where the venv requirement belongs in the frontmatter.** Kiro's skill format
has an optional **`compatibility`** field for *environment requirements (e.g.
required tools, network access)*. ⚠ **It is a declaration, not an enforcement
mechanism** — nothing checks it — so **the ladder still has to be in the body.**
Putting it only in `compatibility` would be the "knob that cannot work" failure
this project has already paid for once.

#### What gets written

- **A `fux-usage` skill** — the operating manual the surface is missing: the
  ladder, the four read verbs and when each is right (`ask` ranked, `find`
  pipeable paths, `answer` a cited answer over fetched sources, `explain`/`graph`/
  `path` the relations), `--json` over prose, and **what to do when there is no
  index** (`fux ingest && fux build`, and say so rather than guessing).
  **Written once, installed to `.claude/skills/` and `.kiro/skills/`.**
- **The ladder folded into every existing rendering**, not bolted beside them.
  ADR-AGENT-POLICY decision 2's conformance test asserts the renderings agree;
  **a ladder in one and not the others is exactly what that test exists to
  catch**, so every rendering moves in the same change.
- **A `fux doctor` line reporting how fux was invoked and whether `.venv` is
  active** — the human-facing half of the same fact, and it rides §3.1's new
  doctor section rather than adding a second one.

#### Constraints this phase inherits and must not break

- **L1 — `$0`, stdlib-only.** A skill is markdown. **No launcher, no shim, no
  wrapper script** — the ladder is instructions the agent follows, not code fux
  ships. **If this phase grows a binary, it has gone wrong.**
- **ADR-AGENT-POLICY decision 5 — declared, never detected.** Which agents get
  files comes from `[agents] install` in `fux.toml`, **never from sniffing the
  filesystem**, and veto 4 fires on inferring it. ⚠ **The ladder is the
  opposite case and the distinction must be stated in the record:** it is the
  *agent* probing its own runtime at call time, not *fux* deriving a
  declaration at setup time. **Different actor, different moment** — but it will
  read as a contradiction to anyone skimming, so say why it is not.
- **ADR-AGENT-POLICY decision 6** — every file `fux setup` writes is announced
  in the terminal, with how to turn it off. A new skill is a new announced file.
- **ADR-CLI veto 7 — ASCII only** in anything that reaches a Windows console.
- **The Windows rung is not optional.** Windows-first fleets are a design input
  under CLAUDE.md §Litmus, and `.venv\Scripts\fux.exe` is a different path, not
  a footnote.

#### Forks — Arpit's

- **A. Does a `fux-usage` skill ship at all, or does the ladder just amend the
  existing renderings?** A fifth file is more surface and more announcement;
  amending is smaller and buries an operating manual inside a document about
  archived results.
- **B. Does `python -m fux` become a supported entry point?** ⚠ **Downgraded
  2026-08-26, not closed.** The ladder shipped with **`python -m fux.cli`** as
  rung 4 — already importable, already what `tests_e2e/` spawns — so the hole
  this fork was about **does not exist**. What remains is cosmetic and real:
  `python -m fux` is what a user will type, and today it fails. Adding
  `src/fux/__main__.py` is three lines and a **second public entry point to
  support forever**.
- **C. Which vendors?** ✅ **RULED 2026-08-26: Claude and Kiro** — and **built**.
  ⚠ **The premise was wrong: `kiro` was ALREADY in `KNOWN_AGENTS`**, shipping a
  `.kiro/steering/` rendering. What actually landed is the usage skill at
  `.kiro/skills/fux-usage/SKILL.md`, from the **same template bytes** Claude
  gets. ⚠ **What is still open inside the ruling:** `copilot` is
  already shipped and installed by default — **does it stay, or is it dropped?**
  Dropping a vendor removes files from repos that already have them, which
  `fux setup` has no mechanism for (it writes and keeps; it never deletes).
  **Leaving it is the cheaper and probably correct call, but it is not what was
  ruled**, so it is asked rather than assumed.
- **D. For Kiro specifically: skill only, or also a `.kiro/steering/` file?**
  ⚠ **Partly answered by the build**: the *usage* guidance shipped as a skill
  for the reason below, and the existing *archived-results* rendering stays as
  steering with `inclusion: always` — correct, because a policy should be
  ambient and an operating manual should not. **What is still yours** is whether
  that split is the rule or the exception.
  ⚠ **The trap above says skill.** Kiro CLI loads every steering file on every
  interaction with no inclusion modes, so steering is a permanent context tax
  and `manual` does not save you. A steering file is only worth it if fux's
  guidance should be *unconditionally* present — and the whole argument for a
  skill is that it should not be.
- **E. Is a repo-root `AGENTS.md` written?** Kiro reads it and it is the
  vendor-neutral convention, so it would cover tools fux never names. ⚠ It is
  also the **most intrusive** file on the list — the one a human is most likely
  to already own — and Kiro always includes it with no inclusion modes, so it
  carries trap 1's cost by construction.

#### Definition of done

- [ ] The ladder is written **once** and appears **identically** in every
      rendering, with decision 2's conformance test extended to assert it.
- [ ] `kiro` is in `KNOWN_AGENTS`, and the **same template bytes** land at
      `.kiro/skills/<name>/SKILL.md` — a second path, not a second rendering.
- [ ] Every skill's `name` equals its folder name (lowercase, hyphens, <=64)
      and its `description` is <=1024 chars — **checked by a test, not by eye**.
- [ ] The skill body tells a Kiro user that **custom agents load neither skills
      nor steering by default** and names the `skill://` / `file://` `resources`
      entries — fux cannot write that config, so it must say it.
- [ ] The Windows rung is present in every rendering.
- [ ] The *"could not be invoked, here is what I tried"* wording replaces
      *"not installed"* in `fux.agent.md`, and the fallback stops being silent.
- [ ] ⚠ **A test asserts no rendering tells an agent to activate a venv,
      export `PATH`, or install anything.** That is the failure mode worth
      gating, because it is the one a well-meaning edit introduces.
- [ ] `fux doctor` reports the resolved invocation and whether `.venv` is active.
- [ ] ADR-AGENT-POLICY amended in the same change; `no ADR affected` is not
      available here.

---

## §4 — The folded verdicts

**Live here because their compare docs were archived on 2026-08-26.** Archive is
not evidence; these are.

### 4.1 · URL refresh trigger — what supplies the clock

> **Verdict: E always, B narrowly, and C-or-D as the deployment's clock.**
> **The fork's premise is wrong as stated:** *detector* and *clock* are two
> roles, and only the clock is a genuine either/or.
> **E — query-driven detection** is not a trigger at all, conflicts with
> nothing, and should be built whatever else is ruled.
> **B — the post-commit hook** is admissible **only** for the commit that
> changes `.fux/sources/urls`; a hook refreshing *stale* URLs on every commit
> turns every developer's `git commit` into third-party network traffic and is
> **L4 dead**.
> **C — a local daemon** and **D — a CI schedule** are the same role for
> different deployments: **D where CI can reach the sources, C where it cannot.**
> In an air-gapped estate with an intranet Confluence, **D does not exist and C
> is the only clock there is.**
> **Confidence:** high that detector ≠ clock and that E is unconditional; high
> on B's narrow scoping; **medium** on shipping C now rather than parking it.

**The axis that decides it is the quality of the L4 opt-in**, not the mechanism:

| option | where the opt-in is |
|---|---|
| **B** hook | `fux hooks --install` — one-time, and its consequence (network on every commit, forever) is **invisible at the moment of consent**. The weakest of the four |
| **C** daemon | starting it, and it stays visible while it runs |
| **D** CI | a workflow file — committed, reviewed, readable by anyone in the repo. **The strongest, and it is not close** |

⚠ **B2 is the trap, and it is the appealing one.** Using commits as a sampling
clock fits the repo's grain — until you write down what a colleague experiences:
they clone, run one `fux hooks --install` because the README said to, and from
then on every commit sends requests to hosts they never chose, on a schedule
they cannot see, from a machine that may be on a customer's network. **The
failure is not technical — the consent does not match the consequence.**

⚠ **The sibling fork's rejection of CI does not transfer.**
`maintenance-trigger` rejected CI because *a bot commits over the human's diff*.
That was aimed at a bot **committing back**. A bot opening a **PR** does not
race a human's next commit. **What does transfer is the warning:** implemented
as push-and-commit rather than PR-and-merge, D becomes the option already
rejected.

⚠ **C's cost must not be minimised by pointing at `runner.py`.** A daemon is a
lifecycle: start, stop, restart on crash, log somewhere, survive a laptop
sleeping, not run twice, not run as a stale build after an upgrade.
`runner.py` solves the **locking** half and none of the **operations** half.

**Reopen when** any of — a consumer's corpus has a real push feed (webhooks,
Atom, a CQL cursor), which demotes every clock to a fallback; **or** the
detector is measured covering ≥ 90 % of documents actually retrieved, which
shrinks the clock to a quarterly sweep; **or** a fetcher ships whose `validate`
is cheap enough that a full sweep costs less than the coordination any clock
needs.

### 4.2 · URL fetch concurrency — declared capability

> **Verdict: C — declared capability, cap resolved as `min(fetcher's declared
> maximum, configured maximum)`.**
> A fetcher module may declare `MAX_PARALLEL = n`; **absent the declaration the
> value is 1** and behaviour is byte-for-byte what ships today. This is
> ADR-FETCHER decision 5's own principle — **declared, never detected** —
> applied to a second property, and it is the only option that lets the
> thread-safe `http.py` go parallel without breaking the thread-unsafe `cdp.py`.
> **Confidence:** high on C over B/D/E, high on the sort finding, **medium** on
> the default `4`, **low-to-medium** on global-vs-per-host.

**Why the losers lose:**

- **B — a blind pool.** Correct for the fetcher most consumers use, silently
  corrupting for the one the enterprise design point exists to serve. See §3.3.
- **D — an optional `fetch_many`.** Moves **per-URL error isolation** across the
  boundary. Today a `fetch` that raises becomes one `Skipped` and the batch
  continues — that is ADR-URL-INGEST decision 4 in code. Under `fetch_many`,
  every fetcher author must reimplement it correctly, and most will not.
- **E — a process pool.** Not wrong, **disproportionate**. Runs
  `configure()`/`connect()` N times — for `cdp.py` that is N Chrome instances,
  and for any fetcher holding an SSO session it is N logins. It turns a
  concurrency setting into a resource incident.

**The live sub-fork: global or per-host?** The crawler literature's politeness
constraint is **per-host**, because the resource protected is one server. A
corpus of URLs over 40 hosts with a global cap of 4 is *under*-parallel; the
same cap against one Confluence is roughly right. **Proposed: ship global**, and
promote to global-plus-per-host when a 429 is actually observed — shipping both
now means picking a second default with no more evidence than the first.

**Reopen when** a consumer's URL list is dominated by one host and a politeness
complaint or a 429 is actually observed; **or** a fetcher appears that is safe
to call concurrently but only within one host, which `MAX_PARALLEL` as a single
integer cannot express.

---

## §5 — Blocked on a ruling — the register

**Twenty-seven forks — twenty-three inherited, plus §3.6's. One of §3.6's is now
ruled (C: **Claude and Kiro**); it split into two smaller ones, so the count
holds. No agent may pick a default on any of them.** §3.6's are stated in full at the end of that
section rather than repeated here, because they are read alongside the ladder.

### 5.1 · URL freshness — 8 forks

| # | fork | proposed, where one exists |
|---|---|---|
| 1 | **which clock covers the tail?** | §4.1 — daemon **or** CI by deployment |
| 2 | **does the hook fetch at all?** | yes, only for the commit editing `.fux/sources/urls`, behind a config gate **separate** from the indexing-hook gate |
| 3 | **amend the four-function contract with `validate`?** | yes, optional, `http.py` shipping the proof — **gated on §3.0** |
| 4 | **token storage** | runtime-only first; decide the committed sidecar on the numbers |
| 5 | **concurrency shape** | ✅ **ruled 2026-08-26** — §4.2 |
| 6 | **cap default and scope** | `4`, global, promote on an observed 429 |
| 7 | **what the narrowed refresh is called** | `--dirty`? `--stale`? `--changed`? **Cheap now, a deprecation cycle in a month** |
| 8 | **dead-URL reporting** | both `doctor` and the `update` summary |

**On fork 3 — the case for `validate`, and the honest case against.**

```python
def validate(url: str) -> str | None:
    """Cheap answer to 'might this have changed?'
    Return an opaque token, or None for 'I cannot tell'."""
```

- **The fetcher reports; fux compares.** An `ETag`, a `Last-Modified`, a
  Confluence `version.number`, a git blob sha — and **fux** diffs it. Transport
  stays consumer-side, policy engine-side.
- **`None` means "I do not know", not "unchanged"** — it degrades to a full
  fetch, so **every existing fetcher keeps working with zero migration.**
- **The token is opaque.** Fux never parses it, which is what stops `validate`
  smuggling HTTP semantics into an engine that has none.
- **Batching needs no batch signature.** `connect()` already provides the
  bracket: a Confluence fetcher runs one `cql=lastModified > …` sweep inside it,
  caches the result, and answers `validate()` from memory.
- ⚠ **The invariant, and if one sentence reaches the implementer it is this
  one: a changed token must NEVER mean a changed record.** Token unchanged →
  skip the fetch, *the only thing `validate` is permitted to do*. Token changed
  → fetch, then **still** compare the sanitized sha. Otherwise a chatty ETag
  churns shards and byte-determinism is gone. **So `validate` can only ever save
  work; it can never cause a shard to churn.**
- **Against:** four functions have survived two callers untouched. A fifth must
  beat three objections — *the detector already covers this* (partly: head vs
  tail), *an optional function nobody implements is dead weight* (clean test:
  **the shipped `http.py` must implement it**), and *contract creep* (the fence:
  **`validate` is `fetch` at lower resolution, not a new capability**).
- **Two small rulings it needs:** `fux add <URL>` **never validates** — a human
  just asked for that URL. And **a validator skip is not a fetch skip**: today
  "skipped" means *failed*, and unchanged documents must not print as skips.

**On fork 4 — where the token lives.** Not in the record:
[`record-freshness`](../compare/record-freshness.compare.md) verdict D settled
that a temporal field inside a shard means write-if-different rewrites **every
shard on every run**. **That verdict is about records and says nothing about
runtime**, so `.fux/runtime/url-state.json` costs the determinism law nothing.
⚠ **The tension it creates:** runtime does not survive a clone, so a CI runner
starts with no tokens and does the full sweep `validate` exists to prevent —
safe in direction (over-fetch, never under-report), but it blunts the mechanism
in the deployment that most wants it. **L5 disappears with one move: store
`sha256(token)`, never the token** — fux only ever tests tokens for equality.

**Not in scope, and none of it reopens here:** any age bound on a record · a
per-line `refresh=` / `validate=` attribute (ADR-URL-LIST decision 11 closes the
set at two) · an adaptive per-URL crawl schedule (the literature does not
straightforwardly support proportional-to-change-rate over uniform) · a
push/webhook receiver (that is consumer code calling `fux update`).

### 5.2 · What "right" means — 6 forks

**Fux measures rigorously and has never declared what it is measuring.** ADR-RS
governs *how* a claim is frozen and is silent on *what quantity is worth
freezing*, so every quality number this project has produced carries an
**undeclared query distribution** and an implicit cost model in which a
fabricated citation and an honest decline count the same.

**Not hypothetical — two runs already passed their number and failed their
claim, and a human caught both:**

- [**P1-GATE**](../regression/2026-08-09-pruning-eval/VERDICT.md) — hit@5 delta
  of exactly 0.00 inside a ≤2 pt bar, **because the treatment touched 0–2.5 % of
  documents**.
- [**The budget sweep**](../regression/2026-08-22-budget-sweep/ANALYSIS.md) — a
  rule that output *keep* on a result where the kept thing never once won:
  *"satisfied by its letter and violated by its purpose"*.

**The forks:**

1. **Where does `P(q)` come from before real logs exist?** A declared prior ·
   uniform-and-say-so · refuse to weight and report per-class only. **The third
   is the most defensible and the least usable**, which is the whole fork.
2. **Is `unanswerable` inside the gate or beside it?** Inside, and one number
   covers fabrication; beside, and the gate stays comparable with the historical
   hit@5 series. **It cannot be both.**
3. **Who sets the cost weights, and are they published?** Published invites the
   accusation of tuning the metric to the engine; unpublished makes the headline
   unauditable.
4. **Is the `answered` gate measured at all?** ⚠ **The one that can quietly
   break a law-adjacent property.** It needs a judge model — outside the
   maintenance path, so **L3 is not violated** — but it makes the number
   non-reproducible and model-version-dependent, which is exactly what the
   frozen threshold exists to prevent. **Ruling "measure it" without pinning the
   model *and* the prompt makes every future comparison meaningless.**
5. **Does the scorecard become a public claim (README) or stay internal?**
6. **Does a query log get built to source `P(q)`?**

**The shape it proposes**, if the forks rule for it: a versioned `mix.toml`
declaring intent classes and weights, frozen the way a pre-registration is
frozen; a four-gate funnel — `reachable` → `in window (recall@k)` → `placed
(nDCG@k, MRR)` → `answered` — of which **`recall@k` is the honest headline
because it is a ceiling and the gate fux most fully controls**; correct-per-1000
context bytes as the reported curve, compared **at equal byte budget or not at
all**; cost-weighted error so silent failures reach the headline; and
calibration (ECE plus decline precision).

⚠ **Part B cannot run regardless.** `acme` and `orbit` were lost in the
2026-08-20 lab wipe with their generator; `tools/pruning-eval/` still hard-codes
reading them; the five-tier redesign (10 / 100 / 1 000 / 5 000 / 10 000) is
**specified and unexecuted**. **Part A — the declarations — is worth doing
anyway**, because declaring is most of the value.

⚠ **This is not a re-filing of W-62.** That item's parts 1–2 were withdrawn by
Arpit on 2026-08-22 and are his personally. This measures **fux against itself
over time**. If the two are ever confused, this yields.

⚠ **A metric chosen to flatter is undetectable later.** Under-weighting
`currency` and `unanswerable` raises every number fux reports and hides the two
failure modes it is known to have. **Whoever sets the weights should set them
before seeing what they do to the score** — ADR-RS's own discipline, one level up.

### 5.3 · The records — 6 rulings

1. **ADR-REFER decision 4's premise is dead.** It refuses `max_age_seconds`
   because *"there is no such provenance"* — and the record now carries `mtime`.
   The decision may still stand on decision 5's content-verification ground.
   **It is currently standing but unargued, which is the one state a record
   should never be in.**
2. **ADR-ENRICHED vs ADR-ENRICH** — superseded, narrowed, or independently live.
3. **Three status flips.** ADR-MCP, ADR-ENRICH and ADR-RERANK are all
   `proposed` with register rows reading `built: yes`. ADR-RERANK is
   additionally **measured** (28 → 32 of 50, 4 fixed / 0 broken, +8 ms p95).
4. **ADR-TUNE's key names.** Built in `v2.0.0-alpha.1`, so the five field-weight
   names are **a shipped interface**, and renaming one is breaking from here.
   The record is still `status: proposed` — **the state that makes the change
   free. This is the last cheap moment.**
5. **The status vocabulary has no value for a record whose SUBJECT ceased to
   exist.** ADR-CODES-TABLE described a file that was deleted; it was **never
   accepted** and **nothing supersedes it**. Options: a fourth status · rule
   that `superseded` covers subject-deletion · rule that `proposed` is the
   correct resting state and write it down. ⚠ The alternative precedent is
   worse and was not repeated: deleting a record from the register once forced a
   renumber that put **two records on `0022`**.
6. **A frozen pre-registration pointer that is WRONG** (not deleted) — mirror,
   corrections file, or nothing. Neither gate catches it.

**Plus the archived-link fork.** ~40 links now point *into* `archive/`. Whether
a link in an ADR's prose is **naming** an archived item or **citing** it is
Arpit's call:

| reading | says |
|---|---|
| **naming** | prose like *"W-52's trigger"* names the item; the link is a convenience pointer, and archive-is-not-evidence is about *grounding*, not hyperlinks |
| **citing** | a Reference block is exactly where a claim is grounded; a link there **is** the citation |

⚠ **A test was written for this and deliberately removed rather than shipped
red** — it could not tell the two apart. Adjudicating it by writing a looser
check would be the moving-threshold failure in a different costume.

**And the governance gap, which is this section's real deliverable.**
`tests/test_adr_freshness.py` passed throughout W-76 **while sixteen records
went stale**, because ownership is **directory-level**:

> `src/fux/query/` is owned by **ADR-ASK**. Rewriting the scorer satisfied the
> check by touching ADR-ASK — while **ADR-RANKING**, whose entire subject is
> that scorer, rotted silently and was never opened.

**The check is not wrong; it is narrower than it reads.** Either widen it to
honour a declared *describes* relationship, or say plainly in CLAUDE.md that it
does not protect a record from its own subject changing underneath it.

### 5.4 · One ruling on the measurement rule itself

**A scope defect in ADR-RS decision 12, found on the rule's FIRST application.**
An informed run *"never supplies a delta"* — and the first run filed under the
rule is `informed` by construction and made **entirely** of deltas: a wheel 30×
smaller, an index 22.6 % smaller, an ingest 6.8× faster.

**As written, the rule forbids reporting a file size.** That is plainly not what
was ruled.

**The missing distinction:** contamination needs an evaluation set to exist.

| kind of number | can authorship contaminate it? |
|---|---|
| nDCG, pass@k, fixed/broken on a golden set | **yes** — this is what decision 12 is for |
| bytes on disk, wall-clock, wheel size | **no** — nothing to have seen |
| p95 latency on a *chosen* query set | ⚠ **partly** — the metric cannot be fitted, the **sample** can |

⚠ **The third row is why this is not a one-line fix.** Any narrowing has to say
which side latency falls on, and the answer is probably *declare the query set
and how it was chosen* rather than *blind or informed*.

**Not adjudicated by an agent.** The measurement that found this applied the
rule **as written** and disclosed the conflict rather than quietly exempting
itself.

---

## §6 — Considered and not built

*Two things were argued and dropped on 2026-08-26. Both are recorded here in
full so nobody re-derives them, and because their source documents are archived
and therefore uncitable.*

### 6.0 · `prepare-then-ask` — folded in, and withdrawn

**Folded here at Arpit's instruction (2026-08-26), the same treatment §4 gave
the compare verdicts.** `archive/proposals/prepare-then-ask.md` may be named,
never cited. **This section is the live record of it.**

**The flow he described:**

> *"Before getting the answer, I should have ingested all the documents as well
> as the URLs. The URLs should have already been cached, and whatever needs to
> be extracted from those URLs should be already extracted. Is there a command
> for it? … Now when you ask a question … for the URLs, it should again fetch
> those documents which are relevant and check if anything has changed. If
> nothing has changed, then give the same old answer."*

**Mapped onto what exists — most of it is already a command:**

| the step | today |
|---|---|
| record + ingest a directory, document or URL | **`fux add <entry>`** — records the line, ingests, fetches that one URL |
| re-read everything listed, re-fetching URLs | **`fux update`** — subsumed the retired `ingest --refresh-urls` |
| re-index offline only | **`fux ingest`** — never imports a fetcher (L4) |
| ask from the index alone | **`fux ask`** / **`fux find`** |
| ask, fetching cited sources and re-scoring | **`fux answer`** — the refer plane |
| *"check if anything has changed"* | **shipped** — `fetched_sha` vs `indexed_sha` |
| *"if nothing changed, give the same old answer"* | **did not exist** |

**The answer to *"is there a command for it?"* is `fux update`.**

**The two gaps it identified, and both were real:**

1. **`fux update` warms the index, not the answer path.** It fetches URLs to
   build index *statistics*; the refer plane's TTL cache and passage chunks are
   populated by `fux answer`, never by ingest. So after *"everything is
   ingested"*, the first question still paid a full render per cited URL.
2. **There was no answer memo.** `fux answer` re-fetches and re-scores on every
   call; the verdict reports what happened to the source and **the answer is
   recomputed either way.**

**It proposed `fux update --warm` and `fux answer --memo` as flags, not verbs** —
because `fux` has exactly two named networked paths (`fux add <URL>` and
`fux update`), a third verb that opens a socket is a **new L4 fence**, and
ADR-CLI veto 1 forbids `fux <verb> <subverb>` anyway.

⚠ **Both flags are WITHDRAWN, and §1's ruling is why.** If the actual document
is fetched before every final answer:

- **`--warm` saves nothing on the answer path** — those bytes were going to be
  downloaded regardless.
- **`--memo` caches the output of a pure function whose inputs were just
  downloaded.** `fux answer` is model-free and deterministic; ARC is keyed
  `(loc, sha)` so identical bytes give an identical answer by construction. The
  only saving is rescore+assemble — **stdlib CPU on bytes already in hand**, on
  a lexical engine, unmeasured and probably milliseconds.

**What survived is §3.4** — a *report* that says whether anything changed since
the last identical question. **No answer is stored and nothing is replayed.**

**The three findings worth keeping, because they outlive the flags:**

- ⚠ **The sharp edge, and it is why `--memo` could never have been built
  casually:** if `--warm` filled the **TTL** cache, the next `fux answer` could
  be served from a TTL hit — **which is not a sha confirmation** — and a memo
  validated by one would **replay an answer on bytes nobody confirmed while
  reporting `current`.** That is ADR-REFER decision 6's *"we did not look"*
  collapse reappearing one layer up. **A memo must never be validated by
  anything but a sha comparison.**
- **A replayed answer is a fifth epistemic position.** The `cached` verdict
  exists precisely because ADR-REFER refuses to fold *"we did not look"* into
  *"we looked and it was fine"*. ⚠ **§3.4 sidesteps this rather than solving
  it**: it is a *per-answer* statement about two runs, not a *per-citation* fact
  about a fetch, so it needs no fifth label. **A real memo would.**
- **A memo key would have had to include the index root hash.** An index write
  can change what ranks without changing any cited sha, and the sketched key
  `(query, tune hash, cited (loc, sha))` **does not notice that** — it would
  return a stale answer under a `current` label, the worst failure available.

**Also settled and still true:** neither flag needed a recorded ingest time, so
the `max_age_seconds` question is untouched by any of this — validation is by
sha, never by age. And *"maybe reframe the answer"* was never specified; a diff
or a *"this changed since you last asked"* line is **a separate feature wearing
this one's clothes**, and §3.4 is deliberately the small half.

**Reopen when** a measurement shows rescore+assemble is a material share of
`fux answer`'s wall time on a real corpus — **which nobody has measured**, and
which §3.0's harness could answer as a by-product.

### 6.1 · The local content store

**The idea:** persist whole fetched documents locally, content-addressed, so any
question parses against local bytes instead of re-fetching.

**Why it is dropped — §1's ruling removed its main purpose:**

| purpose | survives? |
|---|---|
| avoid re-fetching across questions | ❌ every cited URL is fetched regardless |
| speed at answer time | ❌ same reason |
| re-derive without re-fetch (new chunker, new sanitizer) | ✅ but narrow |
| answer when the source is unreachable | ✅ but narrow |

**The objection that decided it is not a law — it is the product.** Fux's pitch
is *nothing about the corpus is copied*. A persistent document store is a copy
of the corpus. It is legal under **L2's single `snapshot` exception** if ruled
so, and it moves fux from *an index that refers* toward *an index with a content
cache*, which is what every competitor already is.

**What already exists, and is enough:**

- [`refer/arc.py`](../../src/fux/refer/arc.py) — keyed `(loc, sha)`, so a hit is
  byte-identical or it is not a hit. **In memory; dies with the process.**
- [`refer/fetchcache.py`](../../src/fux/refer/fetchcache.py) — on disk,
  TTL-bounded, served **before** a sha is confirmed. **Two stores, provably
  separate**, and that separation is load-bearing.

**Reopen when** either — a chunker or sanitizer change is actually wanted and
priced, and a full network re-sweep is the blocker; **or** a consumer needs
answers with the network unavailable and accepts `snapshot` semantics per source.

---

## §7 — Definition of done

**§3, the agent lane:**

- [ ] §3.0 filed under `regression/` with `classification: informed` and the
      decision-12 conflict disclosed, not self-exempted.
- [ ] §3.1 `fux doctor` URL section + `fail_streak`, report-never-delete.
- [ ] §3.2 detector wired, with the mosaic defence written **into the record**.
- [ ] §3.3 `MAX_PARALLEL`, `min(declared, configured)`, both refusal kinds, and
      the in-flight-counter test.
- [ ] §3.4 the changed/unchanged line, with no answer stored.
- [ ] §3.5 sealed subset (mechanical, power tension answered in writing), decoy
      set, placebo, orphaned-module check with its exception list — and ADR-RS
      decision 15 loses `NOT BUILT` in the same change.
- [ ] §3.6 the invocation ladder in every rendering (Windows rung included), the
      *"could not be invoked"* wording replacing *"not installed"*, the test
      forbidding any rendering from activating a venv or exporting `PATH`, the
      `fux doctor` line, and ADR-AGENT-POLICY amended in the same change.

**§5, Arpit's lane:**

- [ ] The 8 URL forks ruled (5 is done).
- [ ] The 6 measurement forks ruled, weights set **before** seeing their effect.
- [ ] The 6 record rulings made, plus the archived-link fork and the governance gap.
- [ ] Decision 12's scope line written, or a decision that cost measurements
      keep disclosing the conflict. **Both are defensible; picking is not an
      agent's call.**
- [ ] §3.6's remaining forks ruled (C is ruled: **Claude and Kiro**): whether a
      `fux-usage` skill ships or the ladder amends in place · whether
      `python -m fux` becomes a supported entry point · whether `copilot` stays
      now that Kiro is in · skill-only or also `.kiro/steering/` · whether a
      repo-root `AGENTS.md` is written.

---

## §8 — References

- **Records:** [ADR-URL-INGEST](../../docs/adr/0008_url-ingest.md) ·
  [ADR-URL-LIST](../../docs/adr/0018_url-list.md) ·
  [ADR-FETCHER](../../docs/adr/0019_fetcher.md) ·
  [ADR-REFER](../../docs/adr/0030_refer-plane.md) ·
  [ADR-MAINTENANCE](../../docs/adr/0032_hooks.md) ·
  [ADR-RS](../../docs/adr/0036_predictions.md) ·
  [ADR-CONFIG](../../docs/adr/0014_config.md) ·
  [ADR-ANSWER](../../docs/adr/0006_answer.md) ·
  [ADR-AGENT-POLICY](../../docs/adr/0035_agent-policy.md) (§3.6 — decisions 2,
  5 and 6, and veto 4) · [ADR-CLI](../../docs/adr/0002_cli-surface.md) (veto 7,
  ASCII on a Windows console)
- **Live compare docs still cited:**
  [`record-freshness`](../compare/record-freshness.compare.md) (verdict D) ·
  [`maintenance-trigger`](../compare/maintenance-trigger.compare.md) ·
  [`hook-at-scale`](../compare/hook-at-scale.compare.md) ·
  [`refer-fetch-cache`](../compare/refer-fetch-cache.compare.md)
- **Evidence:** [P1-GATE](../regression/2026-08-09-pruning-eval/VERDICT.md) ·
  [the budget sweep](../regression/2026-08-22-budget-sweep/ANALYSIS.md)
- **Code read against, 2026-08-26:**
  [`ingest/urlsrc.py`](../../src/fux/ingest/urlsrc.py) (`fetch_all`, the trailing
  sorts) · [`ingest/run.py`](../../src/fux/ingest/run.py) (`only_urls`) ·
  [`maintain/dirty.py`](../../src/fux/maintain/dirty.py) ·
  [`refer/freshness.py`](../../src/fux/refer/freshness.py) ·
  [`refer/arc.py`](../../src/fux/refer/arc.py) ·
  [`refer/fetchcache.py`](../../src/fux/refer/fetchcache.py) ·
  [`doctor.py`](../../src/fux/doctor.py) · **for §3.6:**
  [`setup.py`](../../src/fux/setup.py) (`AGENT_FILES`, the vendor→template map) ·
  [`templates/agents/`](../../src/fux/templates/agents/) (`SKILL.md`,
  `ENRICH-SKILL.md`, `fux.agent.md`, `fux-archived-results.instructions.md`,
  `POLICY.md`) · `pyproject.toml` `[project.scripts]` — and the **absence** of
  `src/fux/__main__.py`, which is what makes fork B a code change
- **External, for §3.6** — fetched and read 2026-08-26, both pages updated
  2026-08-04: [Kiro · Steering](https://kiro.dev/docs/steering/) — `.kiro/steering/`,
  the four inclusion modes, **and the CLI caveat that inclusion modes are not
  supported there**; [Kiro · Agent Skills](https://kiro.dev/docs/skills/) —
  `.kiro/skills/<name>/SKILL.md`, the open [Agent Skills](https://agentskills.io)
  standard Claude also implements, the `compatibility` frontmatter field, and
  **custom agents loading neither skills nor steering by default**;
  [AGENTS.md](https://agents.md/)
- **External:** RFC 9110 §8.8 and §13 (validators and conditional requests — the
  headers `fetch(url) -> str` does not return) · Megiddo & Modha, *ARC*, FAST '03 ·
  Cho & Garcia-Molina, *Effective Page Refresh Policies for Web Crawlers*, ACM
  TODS 28(4), 2003 · *Neural Retrievers are Biased Towards LLM-Generated
  Content*, KDD 2024 · Megiddo/TREC MAP-error figures per ADR-RS
- **Superseded and archived 2026-08-26** — may be named, never cited:
  `archive/open/W-74…`, `W-75…`, `W-77…`, `W-81…` ·
  `archive/proposals/url-freshness.md`, `measuring-answer-quality.md`,
  `prepare-then-ask.md` · `archive/compare/url-refresh-trigger.compare.md`,
  `url-fetch-concurrency.compare.md`
