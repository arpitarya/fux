---
type: Register
description: "The SR register: the convention, the ownership table, and the state of every record."
---

# SRs — the decision records

**How to use this file.** This is the register: the naming convention, the
record shape, the ownership table, and the rules every record obeys. Read it
before writing an SR, before citing one, and before adding a module to `src/`.

One SR per completed feature or ruled measurement. Every SR carries a
reference. **Every record is cited by NAME in prose, never by number.**

## What an SR is — and what it is not

**A Standing Record is a maintained specification, not a decision log entry.**
The name changed on 2026-09-13 (Arpit) because the old one was importing the
wrong lifecycle:

| an ADR, as the practice defines it | an SR, as this repo actually works |
|---|---|
| immutable once accepted | **amended in the same change as the code** (Law zero) |
| superseded records kept forever — the history *is* the value | **superseded records are deleted** (Arpit, 2026-09-06) |
| cited by number: a number is a fixed point in time | **cited by name, never number** — because the content moves |
| one decision, in its context, at one moment | **owns `src/` components**, carries a veto condition to check *today* |

Every divergence above is a deliberate ruling of this repo's. Together they
mean the artifact **stands** — it must be true now — which is what the name
says and what "ADR" denied. The word was already in use everywhere else here:
*standing directive*, *standing rule*, *standing obligations*, *standing
constraints*.

⚠ **The decision-log role is not lost; it was never here.** It lives in
[`work/compare/`](../work/compare/README.md) (the fork, its verdict, its
reopen-trigger), in `work/regression/*/VERDICT.md` (*nothing supersedes a
measurement except a better measurement* — immutability, on the artifact that
needs it), and in [`work/WORKLOG.md`](../work/WORKLOG.md).

⚠ **`archive/v0.26-docs/adr/` keeps its name and its `ADR-NNNN` citation form.**
It is frozen, it is a different numbering, and renaming a frozen tree to match
a live convention is how an archive stops being evidence of what was.

## One directory, one state

**`records/` is the only home a decision record has** (Arpit, 2026-09-06). The
archive tier is gone: the retired records were **deleted**, not filed, and
nothing outside this directory is a record. A citation therefore resolves here
or it does not resolve at all.

- **There is no "superseded" location.** A record that is superseded is
  **rewritten or deleted in the change that supersedes it**, and the successor
  states plainly what it replaced — in prose, by name. There is no second file
  left behind to be found and mistaken for current.
- **A record whose subject ceased to exist is deleted**, and the decision that
  killed the subject says so.
- **Nothing in this repo may cite an archived record**, by path or by name, as
  backing for a live claim. A name may appear in a sentence about history; a
  link to one may not, because the file is not there.

New records are written here, from [`TEMPLATE.md`](TEMPLATE.md).

**Four files here are NOT records** and carry no number: this register,
[`TEMPLATE.md`](TEMPLATE.md), [`RULE-SINCE`](RULE-SINCE), and
[`BIBLIOGRAPHY.md`](BIBLIOGRAPHY.md) — every external paper, standard and
piece of prior art any record cites, in one table per engine area, each row
ending in **what depends on it or what was not built because of it**. It is
an index of the register's sourcing and **never an authority**: where it and
a record disagree, the record wins and the bibliography is the defect. It is
not a Standing Record because it owns no component, rules nothing, and has
no veto condition to check.

---

## The three kinds

**Every record declares a `kind`, and the kind selects which gate it answers
to** (Arpit, 2026-09-13). It is the answer to one question:

> *What would have to change for this record to become wrong?*

| `kind` | becomes wrong when | today | the gate the kind selects |
|---|---|---|---|
| `law` | **Arpit rules differently** | 12 — SR-LAWS + SR-LAW-0…SR-LAW-8, SR-LAW-10 and SR-LAW-11 | [`tests/test_claude_md_laws.py`](../tests/test_claude_md_laws.py) holds `CLAUDE.md`'s generated block byte-equal to the record; a record conflicting with a law is void in the conflicting part |
| `component` | **the code changes** | 52 | [`tests/test_sr_freshness.py`](../tests/test_sr_freshness.py) and [`scripts/sr-guard.sh`](../scripts/sr-guard.sh) — the owning record is touched in the same change |
| `process` | **the way work is done changes**, with no code behind it | 19 — SR-RS, SR-PORT-LIST, SR-AGENT-SURFACES, and the sixteen WORK records SR-WORK-OPEN-QUEUE, SR-WORK-ENVIRONMENTS, SR-WORK-BENCHMARK, SR-WORK-OWNERSHIP, SR-WORK-BACKLOG, SR-WORK-QUALITY, SR-WORK-SCALE, SR-WORK-LIFECYCLE, SR-WORK-DOCS, SR-WORK-SESSION, SR-WORK-OKF, SR-WORK-ARCHIVE, SR-WORK-RELEASE, SR-WORK-BLOCKERS, SR-WORK-GOVERNANCE, SR-WORK-GOLDEN | its enforcement is a test, so it **owns that test** |

**The kind selects an *additional* gate; it never switches one off.** The
ownership and freshness gates apply to any record with a non-empty `owns`,
whatever its kind — which is why SR-LAWS is `law` and still owns the
cross-cutting modules.

⚠ **`kind` is written, not derived, and that is the point.** `law` is derivable
from the filename; `component` and `process` are **not** separable from `owns`
alone. **SR-POSTINGS owns `tools/pruning-eval` and is a component record;
SR-WORK-QUALITY owns `tools/quality` and is a process one** — identical shape,
opposite kind. A derived field would have to guess, and a guess in this position
reads as authority.

### 🔴 What the kind made visible: thirteen ungated component records

**30 of 80 records carry `owns: []`.** Ten are law records, which is correct,
and **seven are `process` records that name their own hole out loud** — each in
its own decision, never by omission: [SR-WORK-OWNERSHIP](0054_WORK-ownership.md)
decision 7, [SR-WORK-BACKLOG](0055_WORK-backlog.md) decision 7,
[SR-PORT-LIST](0114_port-list.md), [SR-AGENT-SURFACES](0155_agent-surfaces.md),
and the three the 2026-09-14 `CLAUDE.md` extraction added —
[SR-WORK-SCALE](0057_WORK-scale.md) decision 15,
[SR-WORK-LIFECYCLE](0058_WORK-lifecycle.md) decision 12 and
[SR-WORK-SESSION](0060_WORK-session.md) decision 13, whose subjects are what a
sentence may claim, the order work happens in, and whether a written handoff is
true — none of which a checker can grade without grading it wrongly. **The
other thirteen are `component` records that own no component**, so the freshness
gate can never fire for them and nothing said so before this key existed:

`SR-FIND` · `SR-ANSWER` · `SR-URL-INGEST` · `SR-RECORD` · `SR-CDP-FETCHER` ·
`SR-HTTP-FETCHER` · `SR-DIR-LIST` · `SR-CACHEDIR-TAG` · `SR-DOCS-TABLE` ·
`SR-RUNTIME-MANIFEST` · `SR-RUNTIME-STAMP` · `SR-RUNTIME-STATS` · `SR-LOCKS`

**This is named, not yet gated.** The rule that would close it — *a
`kind: component` record must have a non-empty `owns`* — turns thirteen silent
holes red on the day it lands, and each one is a real question: does the record
gain an owner, get re-kinded, or earn a stated exemption? **That is Arpit's
call, one record at a time**, and inventing an owner to satisfy a check would be
the moving-threshold failure wearing a helpful face. [SR-WORK-OWNERSHIP](0054_WORK-ownership.md) decision 7 already names **two honest cases** for owning
nothing — a record in the list above has to claim one of them, or stop being
`component`. Two records were re-kinded
rather than left in that list: **SR-WORK-OWNERSHIP** (the record-to-component model)
and **SR-PORT-LIST** (the boundary with the archived engine) are `process`.

⚠ **`process` is the kind that can rot.** Every process record exists because a
rule had no home, so the kind is one drawer away from becoming where
unclassifiable rules go to be unenforced. **Owning its enforcing test is the
only thing that stops that**, and it is load-bearing rather than decorative.

## The convention

**Path.** `records/NNNN_<short-name>.md`, on **three ranges** (Arpit, 2026-09-11; the WORK range added 2026-09-13):

| range | holds | a new record takes |
|---|---|---|
| `0001`–`0050` | the **Law** records only — `0001` SR-LAWS, `0002`–`0012` the eleven laws (SR-LAW-0…SR-LAW-8, SR-LAW-10, SR-LAW-11) | the next free number **from `0013`** |
| `0051`–`0100` | the **WORK** records only — how work is done: `0051` SR-WORK-OPEN-QUEUE, `0052` SR-WORK-ENVIRONMENTS, `0053` SR-WORK-BENCHMARK, `0054` SR-WORK-OWNERSHIP, `0055` SR-WORK-BACKLOG, `0056` SR-WORK-QUALITY (Arpit, 2026-09-13), and `0057`–`0064` the eight the `CLAUDE.md` extraction filled — SR-WORK-SCALE, SR-WORK-LIFECYCLE, SR-WORK-DOCS, SR-WORK-SESSION, SR-WORK-OKF, SR-WORK-ARCHIVE, SR-WORK-RELEASE, SR-WORK-BLOCKERS (Arpit, 2026-09-14), `0065` SR-WORK-GOVERNANCE, the governance map converted from `work/governance.md` (Arpit, 2026-09-14), and `0066` SR-WORK-GOLDEN, the sealed answer key's guards and what may be read instead — the prohibition itself is law L11 at `0012` (Arpit, 2026-09-15) | the next free number **from `0067`** |
| `0101`– | **every other record**, sequentially | the next free number **after the highest** |

**`0013`–`0050` and `0067`–`0100` are reserved and EMPTY — there are no
placeholder files.** A gap in either range is the reservation, not a missing
record; nothing scans for one and nothing should create one to fill it.
⚠ **The handle `L9` is retired and never reused; its FILE NUMBER was not.**
`SR-LAW-9` held `0011` until 2026-09-13, when the environment rule became a WORK
record at `0052`; `SR-LAW-10` then moved `0012` → `0011` to close the hole
(Arpit, same day). That is the register's own rule applied, not an exception to
it: **the number is a filename ordinal, not an identity**, and nothing
identifies a record by number. What may never move is the *handle* — `L10` is
still `L10` — because a handle IS an identity and is cited in code comments and
commit messages that nobody will revisit.
**If either family passes its ceiling, renumber deliberately — and do not borrow
from the other**, which is what a shared `0001`–`0100` range would have invited.

**The WORK records stand to *how work is done* as the `SR-LAW-n` records stand
to the laws** (Arpit, 2026-09-13): one subject per record, a normative block,
and a generated view in the file a session actually reads. **A law still
outranks a WORK record** — these govern how work is tracked, never what a law
permits.

The number is a filename ordinal, **not an identity** — it is scoped to its
directory and its generation, and it restarts when a record set is replaced.
Nothing identifies a record by number.

**Cite by NAME, never by number.** In prose, always `SR-RECORD`, never
"ADR-0004". Numbers exist so the archive can map a retired record to its
successor. **A live doc that says "ADR-0004" is a defect; fix it on contact.**

### Frontmatter is the metadata, and the body never restates it

**Ten keys, in this order** — `type` · `name` · `title` · `description` ·
`status` · `date` · `feature` · `owns` · `laws` · `timestamp`. Two more are
optional and appear only where they are true: `supersedes` and `ratifies`.

| key | value |
|---|---|
| `type` | always `Standing Record` |
| `kind` | `law` · `component` · `process` — which gate this record answers to; see §The three kinds |
| `name` | `SR-<NAME>` — cite this everywhere |
| `title` | `SR-<NAME> (NNNN) — <short decision title>`; carries both name and number |
| `description` | one sentence; what the record decides |
| `status` | `proposed` · `accepted` · `superseded` |
| `date` | `YYYY-MM-DD` — when the decision was taken |
| `feature` | the one feature this record belongs to |
| `owns` | inline list of the `src/`/`tools/` paths this record claims, each as `path@<12-hex content hash>`, `[]` when none. **must match the ownership table below** (paths only; the hash is not part of the identity). Stamped by [`scripts/sr-owns.py`](../scripts/sr-owns.py) **before** `sr-hash.py` |
| `laws` | inline list of SR-LAWS numbers (`[L1, L3]`), `[]` when none. Never restate a law |
| `content_sha` | SHA-256 of this file with its own `content_sha:` line removed — stamped by [`scripts/sr-hash.py`](../scripts/sr-hash.py) **in the same change that amends the record** |
| `timestamp` | ISO-8601, for OKF consumers |

**Any value containing `: ` must be quoted** — `fux`'s parser is permissive and
will read it, but strict YAML refuses the whole block, **which makes the
record's metadata invisible to GitHub, editors and every generator.**

⚠ **The body opens at §1 and restates none of it.** Every record used to carry
both a frontmatter block and a `- **Name:** …` bullet list, written by hand at
different times, and **they drifted**.
[`tests/test_sr_frontmatter.py`](../tests/test_sr_frontmatter.py) forbids
the second copy, checks the key set and its order, checks the quoting, and
checks the title carries both the name and the number.

### A record states what is true now. It carries no history.

⚠ **There are no `Amended` sections, and the word does not appear as a
heading.** When a decision changes, **rewrite the sentence it changed** — in
place, in the same commit. **A record is read top-down by an agent that will act
on the first answer it finds, so a correction appended below a false sentence is
a false sentence with a footnote.**

**What a record holds:** what fux does today, and what it is committed to doing.
**What it does not hold:** what it used to do, what a superseded amendment said,
what a number was before it was corrected, or which work item corrected it. Git
holds all of that, and git is where it belongs.

**The one exception is an argument that still binds.** A rejected alternative
belongs in *Alternatives considered* — not because it is history, but because
**it is the reason the current shape is the current shape**, and leaving it out
invites the argument back. The same goes for a defect a decision exists to
prevent: **the failure is the argument, the date it happened is not.**

### Two sections and a bibliography

- **§1 — For humans.** One screen, maximum. Includes a diagram: a Mermaid block
  **and** a hand-paired ASCII twin, **updated together whenever either
  changes**. The twin is collapsed inside a `<details>` block, with a blank line
  after `</summary>` or the fence will not render.

  §1 may also carry **Examples** — real, capture-copied, two or three at most —
  and **Charts**, whose default is *none*. Both are deleted, not left empty,
  when they do not apply.
- **§2 — For agents.** Context · decision · consequences · alternatives
  considered · reference · veto condition. Decisions are numbered, so another
  record can cite `decision 3` rather than quoting.
- **References.** The last section: every source the record cites, gathered —
  **Records · Code · Measured evidence · Project docs · Papers and
  specifications**, empty groups deleted. It is an index, not an argument:
  **nothing appears there that is not cited in the body**, and **an archived
  document is never listed there.**

**The reference is grounded.** A paper, a live doc, code, or measured evidence
under [`work/regression/`](../work/regression/README.md). **Never an archived
doc** — nothing guarantees an archived file was not overwritten after the fact.
An archived doc may be *named* in a record; it may not *back* a live claim.

**The veto condition is a condition, not an event.** Write what would have to
become **true** for the decision to reopen, phrased so someone can check it
today with a command or a look at the code. **A veto written as an event to
await never fires, because nobody is waiting** — and a veto keyed to a filename
goes stale when the file is renamed, where one keyed to a committed value does
not.

**A record that restates a cross-cutting principle is a bug.** Each law lives in
exactly one place — **its own `SR-LAW-n` record**, which `SR-LAWS` routes to.
Every other record names the law's number in its `laws:` key and moves on. **The
paraphrase is what drifts.** ⚠ **The home moved on 2026-09-12** (W-122): it was
`CLAUDE.md` §Non-negotiable constraints, which now carries a **generated**,
test-bound view of all ten.

**Ownership is a table, not a judgement call, and it has an executable twin.**
Every `src/`/`tools/` component is claimed by exactly one record in the
ownership table below. ⚠ **When that table changes, edit
[`tests/test_sr_ownership.py`](../tests/test_sr_ownership.py) in the same
change** — its exemption sets and pinned counts are hand-maintained, so the two
drift silently otherwise. **That is why the executable twin exists**: a table
nothing reads is a table nobody notices going wrong.

**Records live in `records/`, and nowhere else.** There is **no archive tier for
records** (Arpit, 2026-09-06): a superseded record is **rewritten or deleted in
the same change that accepts its successor**, and the successor states in prose
what it replaced. Nothing is left behind to be found and mistaken for current,
and **no live doc may link to a retired record** — the file is gone.
[`tests/test_doc_links.py`](../tests/test_doc_links.py) is what notices a link
that no longer resolves.

### Records are kept current by a check, not by good intentions

[SR-LAW-0](0002_LAW-0-authority.md) decision 1a is the rule — three
obligations, of which the third cannot be checked; these are where the
first two are enforced:

| where | what it does |
|---|---|
| [`tests/test_sr_freshness.py`](../tests/test_sr_freshness.py) | runs in CI with `fetch-depth: 0`. Fails any commit since the rule landed that changed an SR-owned component without touching **that component's owning record specifically** — touching some other record does not count |
| [`tests/test_sr_register_status.py`](../tests/test_sr_register_status.py) | fails when a status cell below disagrees with the record's own frontmatter, or when a record on disk is missing from the table. **The record is the truth; this table indexes it** |
| [`tests/test_sr_owns_consistency.py`](../tests/test_sr_owns_consistency.py) | fails when a record's `owns:` key and the ownership table disagree — **in either direction** |
| [`tests/test_sr_frontmatter.py`](../tests/test_sr_frontmatter.py) | the ten keys, their order, the quoting, the title, and the two things a body may not contain |
| [`tests/test_sr_ownership.py`](../tests/test_sr_ownership.py) | every component claimed exactly once, every owner resolvable, every number unique within a directory |
| [`scripts/sr-guard.sh`](../scripts/sr-guard.sh) | the freshness check as a `commit-msg` hook: `ln -sf ../../scripts/sr-guard.sh .git/hooks/commit-msg` |
| [`tests/test_claude_md_laws.py`](../tests/test_claude_md_laws.py) | holds `CLAUDE.md`'s law block byte-equal to the eleven `SR-LAW-n` records, refuses a verbatim third copy in any live document, and checks that `SR-LAWS` routes every handle. **Deleting this file makes the block an illegal restatement** — SR-LAW-0 decision 5 |
| [`scripts/gen-laws.py`](../scripts/gen-laws.py) | the generator behind it: `--write` regenerates `CLAUDE.md`'s block from the records, `--check` is the test as a command |
| [`tests/test_claude_md_golden.py`](../tests/test_claude_md_golden.py) | the same bind for `CLAUDE.md`'s §Golden answer key block and [SR-WORK-GOLDEN](0066_WORK-golden.md). **The view exists because Cowork reads `CLAUDE.md` and does not read `records/`** — decision 3 |
| [`scripts/gen-golden.py`](../scripts/gen-golden.py) | its generator: `--write` regenerates that block from the record, `--check` is the test as a command |
| [`tests/test_sr_config_keys.py`](../tests/test_sr_config_keys.py) | the key-tree gate — SR-CONFIG ↔ `config.py` and SR-TUNE ↔ `tune.py`'s `_SCHEMA`, **both directions**, so *a key is real only if it is in its record's declared block* (SR-LAW-0 decision 6) |

**The escape hatch is a line reading exactly `no SR affected` in the commit
message**, on its own line. **It is not a silent skip — it is a claim, in git
history, under your name**, that you checked and there was nothing to update.

⚠ **What none of these prove.** The freshness gate checks that a record was
**touched**, never that it is **coherent**. A record can be edited into
self-contradiction in the same commit and every mechanical check passes. **That
has happened, and the code implemented the wrong sentence.**

**The baseline is self-bootstrapping**: the freshness check applies from the
commit that added it, never retroactively. After a bulk review the baseline can
move forward by writing a commit sha into
[`records/RULE-SINCE`](RULE-SINCE) — ⚠ at the cost that the commits it skips
past are **no longer re-auditable by the gate.**

Start from [`TEMPLATE.md`](TEMPLATE.md).

---

## The register

| # | name | title | status | built |
|---|------|-------|--------|-------|
| [0001](0001_LAWS.md) | **SR-LAWS** | The non-negotiable constraints have exactly one home, and records cite it | accepted | yes |
| [0003](0003_LAW-1-zero-cost.md) | **SR-LAW-1** | **L1** — `$0`, FOSS-only: OSI-approved licences only, with source-available (BSL/SSPL/Elastic v2) named as failing it. Why fux is never a purchase order; and the 2026-09-06 amendment that withdrew the zero-dependency guarantee while hardening the money clause | accepted | yes |
| [0004](0004_LAW-2-content-never-durable.md) | **SR-LAW-2** | **L2** — content is never durable outside its source system. The law the architecture rests on, its three declared exceptions, and why a summary of a confidential document is one | accepted | yes |
| [0005](0005_LAW-3-deterministic.md) | **SR-LAW-3** | **L3** — deterministic; no model in the maintenance path. Byte-identical index and root hash, the enrichment boundary that keeps it true, and the pin problem L1's amendment created | accepted | yes |
| [0006](0006_LAW-4-offline-by-default.md) | **SR-LAW-4** | **L4** — offline by default. Fenced opt-in paths, *plural*; the narrowing that already happened once across nine records; and the use-record gap this law does not close | accepted | yes |
| [0007](0007_LAW-5-hashed-meta.md) | **SR-LAW-5** | ~~**L5**~~ — **RETIRED 2026-09-20 (Arpit, W-194).** Hashed meta for non-git sources, enforced at write time. The mechanism was deleted outright, and there is no residue of the law once the mechanism is gone. **The ACL-mismatch leak it closed is now an ACCEPTED, DOCUMENTED EXPOSURE**; the record is kept for the argument, the citation and the reopen trigger, and the handle L5 is never reused | superseded | yes |
| [0008](0008_LAW-6-say-index.md) | **SR-LAW-6** | **L6** — say "index", not "db". Load-bearing vocabulary: the noun governs the inferences, and every *"why not cache the bodies"* conversation starts with the wrong one | accepted | yes |
| [0009](0009_LAW-7-python-311.md) | **SR-LAW-7** | **L7** — Python ≥ 3.11. The floor that made refusing dependencies affordable, and the justification that narrowed on 2026-09-06 without the floor moving | accepted | yes |
| [0010](0010_LAW-8-use-record.md) | **SR-LAW-8** | **L8** — a use record is never committed. Written, reverted and re-narrowed in one day; gitignored is the test, not `.fux/`; and the transmission clause that did not survive | accepted | yes |
| [0012](0012_LAW-11-sealed-answer-key.md) | **SR-LAW-11** | **L11** — the golden answer key is Arpit's custody and no agent may read one: since 2026-09-18 a key may exist at exactly one address, `work/golden/golden-answers/`, gitignored and never committed, and it is closed to every agent on both spellings for reading, listing, hashing and deleting alike; one file is the same breach as ten; an instruction to open it is void. A breach does not fail loudly — it yields a benchmark number indistinguishable from a clean one | accepted | yes |
| [0011](0011_LAW-10-bundled-output.md) | **SR-LAW-10** | **L10** — the consumer is served build output, never source. One generated artifact per plane in someone else’s repository; `.fux/decoders/` and `.fux/fetchers/` excepted because there source IS the contract; bundled ≠ minified | accepted | yes |
| [0051](0051_WORK-open-queue.md) | **SR-WORK-OPEN-QUEUE** | How `OPEN-WORK.md` works — fifty-three rules in seven groups (what the file is · an item's lifecycle · the shape of a row · the four balls · ordering · the Blocked-on-Arpit inbox · standing obligations), stated once here and rendered into the queue's footer and `CLAUDE.md` as generated views held byte-equal by a test | accepted | yes |
| [0052](0052_WORK-environments.md) | **SR-WORK-ENVIRONMENTS** | Each sibling environment has one job — `fux-playground` is Arpit's hands alone, `fux-lab` runs every measurement on the golden test data up to 10 000 documents, `fux-benchmark` compares the current build against the previous major. **Was law L9 until 2026-09-13**; the handle is retired | accepted | yes |
| [0053](0053_WORK-benchmark.md) | **SR-WORK-BENCHMARK** | What every benchmark run captures — the ranked lists, what moved between the arms, `hit@k` at 1/5/10/20/50, the answer layer with its planted unanswerables, the committed index size, the speed, and an HTML report, per query and never as a total. Halt gates are functionality and are not captured | accepted | yes |
| [0054](0054_WORK-ownership.md) | **SR-WORK-OWNERSHIP** | `owns` and `describes` — the record-to-component model itself, which two tests enforced and no record decided. Exactly one owner per component; any number of describers, and the freshness gate demands all of them | accepted | **no** |
| [0055](0055_WORK-backlog.md) | **SR-WORK-BACKLOG** | How `BACKLOG.md` works — the named-but-unclaimed in five classes (`unbuilt` · `ungated` · `unmeasured` · `unruled` · `cost`), no detail files, promotion into the queue by opening a `W-nn`, and the one rule that inverts the queue's: **its length is not a signal** | accepted | yes |
| [0056](0056_WORK-quality.md) | **SR-WORK-QUALITY** | What *"good"* means — a four-gate funnel with `recall@k` as the headline, a declared and versioned query mix, unanswerable queries inside the gate, and the cost of an error published before any score exists | accepted | **no** |
| [0057](0057_WORK-scale.md) | **SR-WORK-SCALE** | The design point is 10 000 documents, and since 2026-08-22 that is a ceiling on **measurement and on commitment** — no threshold, budget, bound, veto or pre-registration above it, and no work blocked on one. **Descriptions of how the design behaves at 10⁵ stay and are not stale**; commitments go. Two withdrawn R ids that are never reused | accepted | **partial** |
| [0058](0058_WORK-lifecycle.md) | **SR-WORK-LIFECYCLE** | How a feature travels — compare doc on a fork, proposal doc on a parked idea, the plan, the handoff in the item's own file, the paste-ready prompt, then one record. **Every handoff and prompt names the model that should execute it**, because an under-powered model does not error, it returns confident wrong work | accepted | **partial** |
| [0059](0059_WORK-docs.md) | **SR-WORK-DOCS** | The documentation contract in one place — the form rules (short points, takeaway first, 3–4 line paragraphs), **an agent may edit its own steering files** under two obligations with facts exempt, and the seven documents every task updates before it is done. The registry lists live documents only, one row each | accepted | yes |
| [0060](0060_WORK-session.md) | **SR-WORK-SESSION** | What a session owes before it ends — the append-only worklog (a chat-only session counts), the interview kept current **during** the work, the milestone row earned by landing, the one-line pointer for a session that dies mid-task, the transition markers, the ten-line answer, and the two hazards of sharing a machine | accepted | **partial** |
| [0061](0061_WORK-okf.md) | **SR-WORK-OKF** | The repo is a declared **Open Knowledge Format v0.1** bundle — `docs/` + `records/` + `work/`, rooted at `docs/index.md`, every knowledge document carrying a non-empty `type`. **The ALL-CAPS exemption was retired 2026-09-12**: the spec never had one, and 94 of 314 files were failing the bar the repo claimed | accepted | yes |
| [0062](0062_WORK-archive.md) | **SR-WORK-ARCHIVE** | One archive, at the repo root, mirroring where each retired document came from. An archived doc may be **named** — link included — and may **never ground a live claim**, because nothing guarantees it was not overwritten after retirement. Records are the exception: never archived, rewritten or deleted in the superseding change | accepted | yes |
| [0063](0063_WORK-release.md) | **SR-WORK-RELEASE** | One name in two registries from one trigger — PyPI automatically by OIDC, **npm staged for a human to approve** — four hand-written version sites plus one derived bundle held equal by `check-version-parity.py`. **`main` has no required status checks**: history is protected, the quality gate is not, so CI green is the author's to read | accepted | yes |
| [0066](0066_WORK-golden.md) | **SR-WORK-GOLDEN** | The sealed answer key — **no Claude session opens it**, by any tool, while Arpit, Codex and ChatGPT may. Five guards stand behind the rule and **not one is a guarantee**: they all run as the same Mac user as the agent they restrain. `CLAUDE.md` therefore keeps a **generated, test-bound view**, which is the only cover Cowork has. **Three question sets since 2026-09-20** (decision 14): an agent-authored set is created whenever a measurement would otherwise wait on Codex, and every number on one is `informed` for ever | accepted | yes |
| [0065](0065_WORK-governance.md) | **SR-WORK-GOVERNANCE** | The governance map — which file governs what, who reads it, what enforces it, and what obliges you to touch it, across four layers (root steering, `work/`, `docs/` + `records/`, `archive/`). It names homes and restates no rule that has one, and it carries **no counts**: its predecessor's counts drifted twice | accepted | yes |
| [0064](0064_WORK-blockers.md) | **SR-WORK-BLOCKERS** | A blocker is a **file, not a remark** — `work/BLOCKED.json`, four decision values, and a stop. No working around one by picking a plausible default. Three hooks enforce it: the inbox injected into every prompt, a `Stop` that refuses three times then relents, and a **per-asset** write lock | accepted | yes |
| [0101](0101_cli-surface.md) | **SR-CLI** | The command-line surface — flat verbs in seven groups, one error boundary, three output modes, every command captured verbatim | accepted | yes |
| [0102](0102_fux-directory.md) | **SR-DOTFUX** | The `.fux/` directory — every child declared committed or derived; the ignore rule asserted against git itself | accepted | yes |
| [0103](0103_ask.md) | **SR-ASK** | The `ask` verb — one scorer, one sort; the path that answers can never change the answer | accepted | yes |
| [0104](0104_find.md) | **SR-FIND** | The `find` verb — one line per hit, for pipes; a projection of `ask`, not a second strategy | accepted | yes |
| [0105](0105_answer.md) | **SR-ANSWER** | The `answer` verb — a fetched, re-scored passage with a fresh sha, its footing stated every time, and no model on the path | accepted | yes |
| [0106](0106_ingest.md) | **SR-INGEST** | How ingest works — carry unchanged extraction forward, re-resolve every edge, write only shards whose bytes changed | accepted | yes |
| [0107](0107_url-ingest.md) | **SR-URL-INGEST** | URL ingestion behaviour — fetching only inside a named fenced path, a failed fetch is a skip not a deletion, de-listing needs no network | accepted | yes |
| [0108](0108_index-lifecycle.md) | **SR-INDEX-LIFECYCLE** | Index generation and update — one canonical encoder, write-if-different, a derived plane that refuses to diverge | accepted | yes |
| [0109](0109_index-record.md) | **SR-RECORD** | One line of the committed index, property by property — including the ones that are conditional | accepted | yes |
| [0110](0110_accelerator.md) | **SR-T1-ACCELERATOR** | The derived T1 accelerator — disposable, term-major, and forbidden from changing an answer | accepted | yes |
| [0111](0111_ranking.md) | **SR-RANKING** | How documents are scored and ordered — BM25F, weight-then-saturate once, one scorer and one rounded sort | accepted | yes |
| [0112](0112_postings.md) | **SR-POSTINGS** | The postings in two shapes — doc-major in git for diffs, term-major in the runtime plane for queries | accepted | yes |
| [0113](0113_config.md) | **SR-CONFIG** | `fux.toml` and every property in it — three tables read, three refused by name, one passed through unread | accepted | yes |
| [0114](0114_port-list.md) | **SR-PORT-LIST** | Port, don't rewrite — a closed list, each module with its tests, and a port earns its place by having a caller | accepted | partial |
| [0115](0115_extracted-mode.md) | **SR-EXTRACTED** | The `extracted` ingest mode — everything taken from the document, nothing invented; the mode every guarantee is stated for | accepted | yes |
| [0116](0116_url-list.md) | **SR-URL-LIST** | The committed URL list — one per line so it merges at scale; loader-sorted so config order can never change committed bytes; one grammar for the `urls` and `dirs` lists (`types` left it for TOML on 2026-09-11). **`fetch=` is mandatory on every line since 2026-09-20** — there is no source-wide fallback to inherit, and a line without one fails to load | accepted | yes |
| [0117](0117_fetcher.md) | **SR-FETCHER** | The consumer-owned fetcher — fux never fetches; one fetcher per URL, declared not detected, returning bytes and a content type, and nothing composes. **Routed since 2026-09-20** (decision 16): pin ▸ binding ▸ claim on the URL's host, regex patterns allowed, claims read with `ast` and never imported, **no default layer at all**, and two patterns matching one host is a hard error rather than a guessed order | accepted | yes |
| [0118](0118_cdp-fetcher.md) | **SR-CDP-FETCHER** | The browser fetcher — borrows your signed-in Chrome over CDP and **intercepts the response**, returning the server's bytes rather than a rendering; never escalated to | accepted | yes |
| [0119](0119_http-fetcher.md) | **SR-HTTP-FETCHER** | The default fetcher — a plain stdlib GET written into your repo by `fux setup`, so core keeps zero network lines; and it never escalates | accepted | yes |
| [0120](0120_dir-list.md) | **SR-DIR-LIST** | The committed directory list — `!` subtracts, and `archived=true` is a declaration never derived from a path | accepted | yes |
| [0121](0121_cachedir-tag.md) | **SR-CACHEDIR-TAG** | CACHEDIR.TAG marks a derived `.fux/` directory disposable, so backup and archive tools skip it for free | accepted | yes |
| [0122](0122_docs-table.md) | **SR-DOCS-TABLE** | `docs.jsonl` — the docidx-ordered doc table every other derived structure joins against; nothing in it is derived, only carried | accepted | yes |
| [0123](0123_runtime-manifest.md) | **SR-RUNTIME-MANIFEST** | `manifest.json` — the per-shard content-sha fingerprint, plus the doc-table field set that a version string could not be trusted to carry | accepted | yes |
| [0124](0124_runtime-stamp.md) | **SR-RUNTIME-STAMP** | `stamp.json` — the cheap, non-reproducible size/mtime pre-check ahead of the manifest's real one | accepted | yes |
| [0125](0125_runtime-stats.md) | **SR-RUNTIME-STATS** | `stats.json` — the corpus-wide numbers BM25F reads, stored RAW so a field weight cannot bake into the plane | accepted | yes |
| [0126](0126_graph.md) | **SR-GRAPH** | The graph lane — `explain`/`graph`/`path`, unseeded label-propagation communities in a derived plane, and PPR-lite with a **lazy** walk | accepted | yes |
| [0127](0127_refer-plane.md) | **SR-REFER** | Fetch through the *consumer's* fetcher, verify by content sha, assemble under a **byte** budget with a floor, and record the staleness discovered | accepted | yes |
| [0128](0128_types-list.md) | **SR-TYPES** | Which files are documents, **and which metadata keys are searchable** — prose plus every format a built-in decoder reads; absent means the default, never "everything"; `.fux/formats.toml` (`include` + `[decoders]` + **`[meta]`**, a third key since 2026-09-20) replaces it, and the old `.fux/sources/types` is refused and converted | accepted | yes |
| [0129](0129_hooks.md) | **SR-MAINTENANCE** | The hooks that keep a committed index in step — `post-commit` **defers**, no hook touches the network, one write lock, and a resident daemon for the URL tail | accepted | yes |
| [0130](0130_merge-driver.md) | **SR-MERGE-DRIVER** | The committed index merges line by line, last-writer-wins on `(ver, sha)`, and refuses rather than guesses | accepted | yes |
| [0131](0131_cache.md) | **SR-CACHE** | Two caches, two different proofs — ARC keyed `(loc, sha)` cannot change an answer; the TTL store is opt-in, disk-bounded, and answers `cached`, never `current` | accepted | yes |
| [0132](0132_agent-policy.md) | **SR-AGENT-POLICY** | Fux ships the policy its consumers need to read it correctly — one canonical policy carried as a **verbatim block** into each vendor's native format, from a declaration and never from detection | accepted | yes |
| [0133](0133_predictions.md) | **SR-RS** | The R predictions — a claim frozen before measurement, four ways one can end (**FAIL is a success of the method**), and the blind/informed split on the runs that measure them | accepted | partial |
| [0134](0134_archived-content.md) | **SR-ARCHIVED-CONTENT** | What a document declared `archived=true` does once indexed — a record property, a marker, a disclaimer that states the fact and refuses to interpret it, and a demotion nobody takes by default | accepted | yes |
| [0135](0135_tuning.md) | **SR-TUNE** | `.fux/tune.toml` — every knob that changes ordering, decided by one mechanical test, plus `[index]` (`max_phrases`, `max_table_rows`), the declared exception that changes the index; plus per-source priority in either direction | accepted | yes |
| [0136](0136_mcp.md) | **SR-MCP** | `fux mcp` — the stdio JSON-RPC server for coding agents. Three tools rather than the whole verb surface, stdlib-only, and **`answer` is deliberately absent** | accepted | yes |
| [0137](0137_enrich.md) | **SR-ENRICH** | Enrichment as an **agent skill, not an API call** — fux plans and validates, a coding agent generates, and partial coverage is the steady state | accepted | yes |
| [0138](0138_rerank.md) | **SR-RERANK** | Proximity reranking over the refer plane's own passages — and the cross-encoder refused on cross-machine determinism, not on cost | accepted | yes |
| [0139](0139_decode.md) | **SR-DECODE** | The decoder plane — bytes become Markdown in one place, and a consumer may bring a dependency fux may not. **A decoder also claims which of its metadata keys are identity** (`META_FIELDS`, 2026-09-20) — read on the import path, unlike a fetcher's `ROUTES`, because a decoder is imported to decode anyway | accepted | yes |
| [0140](0140_locks.md) | **SR-LOCKS** | The one mutex fux owns over the committed index, and the three sibling files that are constantly mistaken for locks | accepted | yes |
| [0141](0141_confidence.md) | **SR-CONFIDENCE** | How much the index believes its own answer — four deterministic signals and one band, so an agent can tell a grounded result from the closest thing in a corpus that never discusses the question. ⚠ **Amended 2026-08-27 (decision 11): `--band` gates the CLI, the MCP result is always on** — the block is always computed, only its emission is gated | accepted | **partial** |
| [0142](0142_provenance.md) | **SR-PROVENANCE** | Fux does not keep an audit trail; it makes one derivable — a derivation on `ask --why`, a re-runnable receipt on `answer --receipt`, and `fux verify`'s four-state verdict | accepted | yes |
| [0143](0143_output-defaults.md) | **SR-OUTPUT** | Output defaults are configurable in a third file, `.fux/output.toml` — a third boundary: not what is indexed, not which documents come back, but **how they are shown**. The one surface it exists for is **MCP**, which has no flags at all | accepted | yes |
| [0144](0144_fuxignore.md) | **SR-FUXIGNORE** | `.fux/.fuxignore` — one file for what is not indexed, in `.gitignore`'s grammar; read first, and the only thing that outranks the type allowlist in both directions | accepted | yes |
| [0145](0145_acquired-plane.md) | **SR-ACQUIRED** | Fetched source bytes are retained in `.fux/acquired/` — a **third** category beside committed and derived: gitignored like derived, but **not rebuildable**, only re-acquirable, and only while the source exists and the session holds. Clock-free: eviction orders by `run_seq`, never by an mtime | accepted | **no** |
| [0146](0146_refusals.md) | **SR-REFUSAL** | The response a server sends **instead** of the document — a sign-in wall, a paywall, an Office viewer shell. A declarative `.fux/refusals.toml`, **every condition pure over the bytes** (SR-FETCHER decision 13 held rather than amended), under an always-on magic-byte floor no consumer can switch off | accepted | **no** |
| [0147](0147_url-freshness.md) | **SR-URL-FRESHNESS** | Six verdicts that never collapse into each other — `as-ingested` is a real comparison against retained bytes, and is neither `current` nor `unverified`. Plus `ttl=` as a per-URL bound that **narrows** the caller's policy and can never widen it | accepted | **no** |
| [0148](0148_pii.md) | **SR-PII** | **Redact what gets committed; leave alone what stays local.** A consumer-owned `.fux/pii.toml` redacts the index and nothing else — acquired bytes, refer passages and `fux answer` quotes stay as they are. The sha is taken **before** redaction, or every redacted document verifies as `stale` against its own unchanged source. **No built-in floor**, unlike SR-REFUSAL: a format signature is a fact, a PII definition is a policy. **The file is required** — `fux setup` writes the starter and every command but `setup`, `tune` and `output` stops without it; `doctor` fails the row. A rule may name a closed-set checksum, `luhn` or `verhoeff` | accepted | **no** |
| [0149](0149_expand.md) | **SR-EXPAND** | The caller supplies the vocabulary (`--expand`, scored at `expand_weight`) and fuses its own phrasings (`-q`, RRF in rank space); a document matching only supplied terms is never returned | accepted | yes |
| [0150](0150_tabular.md) | **SR-TABULAR** | Tabular documents — one passage per row, `max_table_rows` (500 -> 20 000; `.fux/tune.toml [index]` since 2026-09-11), and the two silent data losses that hid behind both | accepted | yes |
| [0151](0151_chunking.md) | **SR-CHUNKING** | A chunk does three jobs and one span cannot do all three — the one fold rule that derives every unit from heading depth with nothing declared, the boundary ladder that makes every document quotable, and why small-to-big was rejected | accepted | yes |
| [0152](0152_doctor.md) | **SR-DOCTOR** | The health command — fifteen checks, one owner. `warn` is the default and `error` is reserved for a repo a verb will refuse; a check that degrades to `skipped` must name the row that does fail; `fux doctor` never repairs. Carved out of SR-DOTFUX so a change to one check stops demanding eight records | accepted | yes |
| [0153](0153_node-search.md) | **SR-NODE-SEARCH** | The Node read plane — a second reader for an index Python writes, zero dependencies and no build step, held byte-equal by the third arm of the differential law. The `_format` version policy, the never-fetch rule, the `url:`-verdict asymmetry, the tool descriptions both runtimes read from one file, and the three places Node is deliberately a SUBSET of Python — the derived graph plane, the accelerator label, and the decoder boundary. ⚠ **`partial` until 2026-09-12**, when decision 8's gap closed: the reader now reads `.fux/tune.toml` and `.fux/output.toml`, and this repo went 90 of 174 discordant to 0 of 199 | accepted | yes |
| [0154](0154_api.md) | **SR-API** | `from fux import open` — the read-only library surface, frozen. One `output.schema.json` for three readers (CLI JSON, Python objects, Node objects); nothing that writes is in it; every method through `run_query`, so the library cannot rank differently from the CLI (decision 6, 2026-09-12); and the renderer split that makes `cmd_ask` call it is deliberately staged, not done — W-148 (closed 2026-09-15) row 4 | accepted | **partial** |
| [0155](0155_agent-surfaces.md) | **SR-AGENT-SURFACES** | the word *agent surface*, and the taxonomy by what a surface DOES rather than which vendor reads it — instructing (skills · steering · rules · instructions · agents), acting (hooks · settings · commands · subagents · output styles), protocol (MCP descriptions, no file at all) and emitted (CLI output, the busiest surface fux has). Five acting surfaces ship, Claude-only; an acting surface may enforce only where the rule is exact, so the hook is advisory and exits 0 always; a co-owned surface is seeded, never overwritten, and cannot be byte-pinned | accepted | n/a — the roster is SR-AGENT-POLICY's |
| [0156](0156_inspect.md) | **SR-INSPECT** | `fux inspect` — the index X-ray. Six lenses over the COMMITTED shards (boilerplate · findability · length and fields · duplication and templates · analyzer coverage · graph), each printing distributions and named lists and each naming the lever that would change what it found. **Descriptive by default:** exactly three numbers carry a pass/attention flag, every floor prints the word *provisional*, and a floor that flags a healthy golden rung is dropped to descriptive. The words come from a GITIGNORED hash-to-word dictionary built by re-tokenising the sources locally — nothing new is committed, nothing is fetched, no timestamp in the report. No one-number index score, ever | accepted | yes |
| [0157](0157_observe.md) | **SR-OBSERVE** | `.fux/observers/` — the observe-only hook fux exposes AFTER a verb has rendered: one frozen counts-only fact record (verb · `args_hash` · band · answerable · counts · refer verdicts · ms · version) handed to every consumer-owned observer, return value discarded, raise → skipped, slow → **abandoned** at `[observe] max_ms`, exit code never touched. The third readable-source exemption in SR-LAW-10. fux ships no observer and names no subscriber. Built 2026-09-15 (W-170): fux's stdout is taken away for the dispatch, because an observer's `print` reached the answer and the hostile test caught it; **Node is declared out of scope** (SR-NODE-SEARCH decision 18) | accepted | yes |
| [0002](0002_LAW-0-authority.md) | **SR-LAW-0** | L0 — a rule is stated in exactly one SR and every other artifact links to it; the Law records outrank every other record and a conflicting record is void in the conflicting part; a Law changes only on Arpit's ruling | accepted | yes |

> ## Renumbered again on 2026-09-13 — the quality contract became a WORK record
>
> **`SR-QUALITY` at `0141` became [SR-WORK-QUALITY](0056_WORK-quality.md) at
> `0056`**, and the fourteen records above it closed the hole: `0142`
> SR-CONFIDENCE → `0141`, through `0155` SR-API → `0154`. Ruled by Arpit,
> 2026-09-13.
>
> **Why.** *What a quality number means* is how work is measured, not what the
> engine guarantees — the same argument that moved the environment rule out of
> the laws two days earlier. It was already `kind: process`; the band was the
> only thing still saying otherwise.
>
> ⚠ **The handle `SR-QUALITY` is retired and never reused.** A handle is an
> identity, so retiring one is the expensive half of this change and is the
> reason it was ruled rather than assumed. **Every live citation reads
> `SR-WORK-QUALITY`.**
>
> - **What was rewritten:** 500 exact `NNNN_slug.md` path tokens across 111
>   files, 16 index-table link labels, the fifteen affected `title:` keys, and
>   112 `SR-QUALITY` name citations across 31 live files. Two links still
>   pointing at the long-dead `0044_quality-contract.md` —
>   `src/fux/query/provenance.py` and `tools/quality/mix.toml` — were repaired
>   in the same pass.
> - **What was skipped:** `.fux/index/` and `.fux/runtime/` (content-addressed
>   — re-ingested, never sed'd); `archive/v0.26*/`, a different and frozen
>   numbering; and the **name** in [`work/WORKLOG.md`](../work/WORKLOG.md),
>   `CHANGELOG.md` and `archive/open/`, which are history and say
>   `SR-QUALITY` because that is what it was called. Their **paths** were
>   rewritten; their prose was not.
> - **Bare numbers in prose were not rewritten**, for the reason the
>   2026-09-11 pass gives below.
> - **This is the fourth renumber.**

> ## Renumbered again on 2026-09-11 — the laws were given their own range
>
> **Every non-law record moved up by 90**, in its existing order: `0011`
> SR-CLI → `0101`, through `0064` SR-DOCTOR → `0154`. The nine law records
> did not move. Ruled by Arpit, 2026-09-11, executed by
> `scripts/renumber-adrs.py` in one commit and deleted with it.
>
> **Why.** A law and an ordinary record sat interleaved on one number line, so
> **accepting a new law pushed nothing and accepting a new record pushed
> nothing — until a tenth law had nowhere to go but `0065`**, next to the
> newest ordinary record and nowhere near the other nine. The range makes the
> law set contiguous permanently, at the price of one mechanical rename.
>
> ⚠ **The first new law will take `0011`, which was SR-CLI's ordinal until
> today** — and it did, the same day: [SR-WORK-ENVIRONMENTS](0052_WORK-environments.md). That is exactly the vacated-ordinal hazard W-82 ruling 7 named, and
> it is being accepted a second time rather than avoided: the alternative is
> reserving from `0065` and leaving the laws non-contiguous, which is the
> problem. **A frozen document citing `0011` means SR-CLI; a document written
> after 2026-09-11 citing `0011` means a law.** The only thing that separates
> them is the date on the document and the name beside the number.
>
> ⚠ **What could NOT be corrected, again.**
> [`work/WORKLOG.md`](../work/WORKLOG.md) is append-only, so **every bare
> number in it older than 2026-09-11 names a different record than it does
> today** — a second layer on top of the 2026-09-06 pass. Resolve any bare
> number through the **name** written beside it, and never through the number
> alone. Bare numbers in prose were deliberately **not** rewritten: guessing
> which four digits in a sentence mean a record is how a renumber lies.
>
> - **What was rewritten:** 1 772 exact `NNNN_slug.md` path tokens across 136
>   files, every one naming a record that exists and moves. Unresolved SR
>   links were **437 before and 437 after** — the renumber added none, and the
>   437 pre-existing broken links were left broken on purpose, so the diff
>   stays reviewable.
> - **What was skipped:** `.fux/index/` and `.fux/runtime/` (content-addressed
>   — re-ingested instead, never sed'd) and `archive/v0.26*/`, a different and
>   frozen numbering.
> - **This is the third renumber.** The first put two records on `0022`. Each
>   one is a further reason the cite-by-name rule exists.

> ## The number line was renumbered on 2026-09-06, and W-82 ruling 7 was overridden
>
> **`0001`–`0064`, contiguous, no holes.** `0001` is the router
> [SR-LAWS](0001_LAWS.md); `0002`–`0009` are the eight law records; `0010`
> upward is every other record, in its previous order.
>
> ⚠ **This reverses a standing rule, and the reversal is Arpit's.** W-82 ruling
> 7 said **a vacated ordinal is burned and never reused**, and this register
> carried two burned ones — `0017` (`SR-ENRICHED`, superseded) and `0025`
> (`SR-CODES-TABLE`, archived with no successor). **Both holes are gone**: the
> renumber closed them along with everything else.
>
> ⚠ **The rule was right and the cost it named was real.** *"A hole costs
> nothing when every citation is a name; closing one costs every citation in
> the repo."* Closing them cost **996 path links across 52 records**, rewritten
> mechanically in one pass with every link verified to resolve. That was
> affordable **only** because it was scripted and verified; it is not a
> precedent for doing it by hand, and a future compaction is still the failure
> ruling 7 exists to prevent — a previous one put **two records on `0022`**.
>
> ⚠ **What could NOT be corrected.** [`work/WORKLOG.md`](../work/WORKLOG.md)
> is append-only and 810 KB. **Every bare number in it older than 2026-09-06
> now names a different record**, and those sentences may not be rewritten.
> The same was already true of some of them from the 2026-08-27 pass. **Read a
> bare number in any document older than 2026-09-06 as an ordinal at the time
> of writing**, resolve it through the name beside it, and never trust it
> alone.
>
> - **This is why the cite-by-name rule exists**, and this renumber is the
>   second time the project has paid for the times it was not followed.
> - **`SR-CONFIDENCE` once existed at two paths** — `0141_confidence.md` and
>   `0141_confidence.md`, same `name:` — while `0043` was also `SR-LOCKS`.
>   Ruled 2026-08-27: keep the later file, on the substantive ground that its
>   decision 6 binds `SEPARATION_FLOOR` to
>   [SR-WORK-QUALITY](0056_WORK-quality.md)'s frozen `t = 0.75`. The duplicate
>   was deleted, and the survivor is now [0141](0141_confidence.md).
> - **A note here once claimed a renumber had already happened** and pointed at
>   `0123_runtime-manifest.md` and `0140_locks.md`, neither of which ever
>   existed. It was false when written. It is retained as the reason nobody
>   should trust a number in an old document.

**`status` and `built` are two different questions, and conflating them is a
mistake this project has already paid for.** `status: accepted` means **the
decision is ratified**. `built` means **the engine does it**. A record can be
accepted and unbuilt — that is a decision made ahead of the code, which is
legitimate and is how [SR-ENRICH](0137_enrich.md) and
[SR-WORK-QUALITY](0056_WORK-quality.md) exist today. **What is not legitimate is
a reader having to open the record to find out.**

**A row with `built: no` or `partial` names work somebody has to do**, and
belongs to an item in [`work/OPEN-WORK.md`](../work/OPEN-WORK.md) if somebody is
doing it, and in [`work/BACKLOG.md`](../work/BACKLOG.md) if nobody is —
otherwise it is a decision nobody is going to act on, which is a wish.
⚠ **The second home was added on 2026-09-13** ([SR-WORK-BACKLOG](0055_WORK-backlog.md)):
this sentence used to name the queue alone, and satisfying it that way would have
put 241 unclaimed items into a file whose length is supposed to mean *how much is
pending*.

---

## Ownership — which record owns which component

**This table is the answer, not a judgement call.** Every component in `src/`
and `tools/` appears here exactly once, and
[`tests/test_sr_ownership.py`](../tests/test_sr_ownership.py) fails on one
that does not.

**Most specific wins.** A record may carve a single file out of another's
directory-level claim — `store/fuxdir.py` out of `store/`, `query/rank.py` out
of `query/`, `maintain/mergedriver.py` out of `maintain/`. **A carve-out is
justified when the file carries a *different decision*, not merely a different
concern**: the reranker is separate because it is the one thing under `query/`
that reads the **working tree**; the merge driver because its failure mode and
its gate are its own.

**A record may own nothing, and there are two honest reasons for it.** Some
records specify one file another record already generates — the runtime-plane
companions. Others state a mechanism spread across components each already
claimed by the record carrying its decisions, as [SR-LOCKS](0140_locks.md)
does. ⚠ **In both cases the freshness gate cannot demand that record**, so
nothing mechanical will catch it going stale.

⚠ **Directory-level ownership lets a change be discharged against the wrong
record.** The freshness gate demands the *owning* record for a changed
component, so editing a file can be satisfied by touching whichever record owns
its directory — **while the record whose subject *is* that file need never be
opened.** A record that describes a component it does not own has no mechanical
protection at all. **Open both.**

**A component that genuinely has no decision yet is claimed by an open work
item** (`W-nn`) instead. The test resolves that id against
[`work/OPEN-WORK.md`](../work/OPEN-WORK.md); a `W-nn` that has closed fails
the check, so **a component cannot stay unowned by accident.**

**Both change together.** A record's `owns:` key and this table are asserted
equal **in both directions** by
[`tests/test_sr_owns_consistency.py`](../tests/test_sr_owns_consistency.py)
— a path here that its owner does not declare fails as loudly as a claim this
table does not grant.

<!-- OWNERSHIP-TABLE-START -->

| component | owner | note |
|---|---|---|
| `src/fux/__init__.py` | SR-LAWS | package identity and version. Every release bump opens that record, which is correct rather than annoying |
| `src/fux/errors.py` | SR-LAWS | the single flat `FuxError` — CLAUDE.md §Error contract |
| `src/fux/schema.py` | SR-LAWS | the **one** schema mechanism every plane's declared shape loads through. Here for the same reason `errors.py` is: it is cross-cutting, and SR-LAWS is the one record that legitimately spans planes. **The schema FILES are not here** — each lives beside the code it describes, so its ownership is correct by construction |
| `src/fux/frontmatter.py` | SR-LAWS | hand-rolled parser — L1, `$0` stdlib-only |
| `src/fux/cli.py` | SR-CLI | the flat verb surface, the boundary error contract, and the `--json` shape |
| `src/fux/api.py` | SR-API | `from fux import open` — the read-only library surface. **Carved out of nothing**: it is a new component, and it is the Python half of the one shape both readers expose — `node/src/index.mjs` is its Node twin, method for method. ⚠ The re-export that makes `from fux import open` resolve lives in `src/fux/__init__.py`, which SR-LAWS owns, and **no `describes` row covers it**: the qualifier narrows to top-level `def`s and `class`es, `open` there is an imported NAME, and an un-narrowed row would demand this record on every version bump. The gate reaches SR-API through `api.py` instead — editing the re-export alone does not open it, and that gap is stated rather than hidden |
| `src/fux/__main__.py` | SR-CLI | `python -m fux` — the invocation ladder's last rung, and the spelling a human guesses |
| `src/fux/sources.py` | SR-CLI | `add`/`remove`/`update` — the writer for **all three** source lists, and the verbs over them. The types list's edits go through `ingest/typesfile.py` (SR-TYPES decision 12) |
| `src/fux/progress.py` | SR-CLI | the progress plane — stderr-only, TTY-gated, counts not clocks |
| `src/fux/config.py` | SR-CONFIG | `fux.toml`'s schema, the opaque `[sources.url.config]` table, and the tables refused by name rather than ignored |
| `src/fux/tune.py` | SR-TUNE | `.fux/tune.toml` — the loader, the closed key set, the two refusals, and the `[priority]` data. **The priority RESOLUTION is not here**: it lives on `query/rank.py::Weighting`, next to the bound that has to agree with it |
| `src/fux/doctor.py` | SR-DOCTOR | every check, its level, and the register naming whose subject each one reports on. **Carved out of SR-DOTFUX for a different DECISION, not a different concern** (Arpit, 2026-09-11): the layout assertions are still SR-DOTFUX's subject, but this file's subject is the health command itself — and seven records describing one file made the freshness gate demand all eight for any change to any check |
| `src/fux/setup.py` | SR-DOTFUX | the second scaffolding moment — the consumer-owned files, write-if-missing |
| `src/fux/store/` | SR-INDEX-LIFECYCLE | canonical bytes, shard addressing, writer/reader, collisions, and the declared record shape |
| `src/fux/store/fuxdir.py` | SR-DOTFUX | the `.fux/` layout generator — and the **three** kind declarations (`COMMITTED`, `DERIVED`, `ACQUIRED`) the generated README table is built from |
| `src/fux/store/nodebundle.py` | SR-NODE-SEARCH | the Node plane's bundler — one generated `.mjs` per plane, built at publish (L10). **Carved out of `store/`'s claim for a different DECISION**, on `acquired.py`'s precedent: everything else under `store/` is the committed index, and this is a build-time tool that never reads or writes one. It is the only place a change to how the reader is SHIPPED can land, which is what makes the freshness gate reach this record |
| `src/fux/store/acquired.py` | SR-ACQUIRED | the retained-bytes plane — content-addressed blobs, the advisory manifest, `sweep` and `evict`. **Carved out of `store/`'s claim for a different DECISION, not a different concern**: everything else under `store/` is the committed index, and this is the one plane that is neither committed nor rebuildable |
| `src/fux/ingest/` | SR-INGEST | git-dir walk, parse, edges — writes the committed plane |
| `src/fux/ingest/priors.py` | SR-INGEST | ⚠ **covered by the directory claim, and described by no record's decisions.** It computes the supersession and recency priors and writes `mtime` and `superseded` into the committed record; SR-RECORD documents the properties and SR-TUNE the weights, but the module's own behaviour is unrecorded |
| `src/fux/ingest/extract.py` | SR-EXTRACTED | what extraction *promises* — title, phrases, terms and per-field lengths, taken from the bytes and nothing else |
| `src/fux/ingest/sourcelist.py` | SR-URL-LIST | the one line grammar `.fux/sources/dirs` and `.fux/sources/urls` are parsed by — and the `TYPES` entry vocabulary, which `fux source --types` checks against and `fux setup` reads the old `.fux/sources/types` with |
| `src/fux/ingest/fuxignore.py` | SR-FUXIGNORE | `.fux/.fuxignore` — the `.gitignore` grammar, the last-match-wins resolution, and the duplicate-pattern warning. **Carved out of SR-INGEST's directory claim for a different DECISION, not a different concern**: everything else under `ingest/` is a step in the walk, and this is a *precedence rule* over it — the one thing that outranks the type allowlist |
| `src/fux/ingest/typesfile.py` | SR-TYPES | `.fux/formats.toml` — the closed two-key shape, the one-line editors that refuse a layout they did not write, the refusal of the old `.fux/sources/types`, and its conversion. **Carved out of SR-INGEST's directory claim on `fuxignore.py`'s precedent**: a *policy over* the walk — what counts as a document — not a step in it |
| `src/fux/ingest/urlsrc.py` | SR-FETCHER | fux's half of the fetch contract — load, configure, bound, call, normalize |
| `src/fux/ingest/pii.py` | SR-PII | the redaction matcher, the ruleset digest, and the plane table stating that redaction reaches the committed index and nothing else. Carved out of SR-INGEST's directory claim on `fuxignore.py`'s precedent — a *policy over* the walk, not a step in it |
| `src/fux/ingest/refusals.py` | SR-REFUSAL | the refusal matcher — six byte-pure conditions and the always-on magic-byte floor. **Carved out of SR-INGEST's directory claim on `fuxignore.py`'s precedent**: everything else under `ingest/` is a step in the walk, and this is a *refusal rule* over it |
| `src/fux/ingest/ingestlog.py` | SR-INGEST | W-200's ingest ledger — one runtime line per consumed document naming its decoder and, for a URL, its fetcher. 🔴 **Not `src/fux/query/provenance.py`**, which is SR-PROVENANCE's answer receipts and the opposite subject: that one records what somebody **asked** and L8 governs it, this one records what **ingest did** and L8 does not reach it. The collision was not noticed when W-200 named the path; both docstrings now open by naming the other |
| `src/fux/decode/` | SR-DECODE | bytes → Markdown, in one place: the built-in decoders, the registry, the override precedence and the `.fux/decoders/` consumer seam. Separate from SR-INGEST's claim because the record it carries is a **boundary** — where consumer-supplied dependencies become legal — not a step in the walk |
| `src/fux/decode/csv.py` | SR-TABULAR | how much of a `.csv`/`.tsv` is read — `.fux/tune.toml [index] max_table_rows`. Carved out of SR-DECODE's directory claim on `freshness.py`'s precedent: the record is about **tabular documents**, which reaches past `decode/` into how `refer` cites them |
| `src/fux/decode/xlsx.py` | SR-TABULAR | the same limit, applied per SHEET — a sheet is the workbook's own division, so truncating the fifth because the first four were long would be arbitrary |
| `src/fux/decode/_limits.py` | SR-TABULAR | the `ContextVar` seam that lets a two-name decoder read committed config without the protocol growing a third parameter (decision 5) |
| `src/fux/derive/` | SR-T1-ACCELERATOR | T1 build, block maxima, skipping, and the declared runtime shapes |
| `src/fux/query/` | SR-ASK | the scan, unification, and the display-only resolution after it — bound by the differential law |
| `src/fux/query/rank.py` | SR-RANKING | the one scorer and the one sort, and `Weighting`, which is where every document multiplier must travel to reach the pruning bound |
| `src/fux/query/bm25f.py` | SR-RANKING | BM25F, `Scoring`, and `derive_wlen` — the one place the weighting arithmetic exists |
| `src/fux/query/analyzer.py` | SR-RANKING | split, lowercase, stopword, stem, hash — in that order, shared by ingest and query |
| `src/fux/query/stem.py` | SR-RANKING | the Porter implementation, checked against the published test vectors |
| `src/fux/query/tokenize.py` | SR-RANKING | the shim both `ingest/` and `query/` import, which is what makes the two sides agree **by construction** rather than by review |
| `src/fux/query/rerank.py` | SR-RERANK | proximity reranking — carved out because it is the one thing under `query/` that reads the **working tree** rather than the committed index, and because the decision it carries is a *refusal* |
| `src/fux/query/confidence.py` | SR-CONFIDENCE | the four signals and the band, computed from what ranking already produced |
| `src/fux/query/expand.py` | SR-EXPAND | the `Expansion` object — what to score, what the user actually asked, and at what weight. Carved out of `query/` because the decision it carries is a **refusal**: a document matching no original term is not ranked low, it is not returned |
| `src/fux/query/fuse.py` | SR-EXPAND | reciprocal rank fusion for `-q`. **A revival, not a restoration** — the deleted module fused SCORES; this one fuses ranks, which is why it comes back under a record rather than off the port list |
| `src/fux/query/provenance.py` | SR-PROVENANCE | the derivation, the receipt, the journal and `verify`'s four-state verdict. **Carved out of `query/` for a different DECISION, not a different concern**: everything else under `query/` answers a question, and this answers *how the answer was reached* — and it is the one module in the tree that may write a plaintext use record (L8, as reverted) |
| `src/fux/output_config.py` | SR-OUTPUT | `.fux/output.toml` — three roots (`[cli]`, `[cli.json]`, `[mcp]`), the two closed key sets (`CLI_VERBS`, `MCP_KEYS`), and the precedence chain (flag -> `[cli.json.<verb>]` -> `[cli.json]` -> `[cli.<verb>]` -> `[cli]` -> bypass -> `FuxError`). **Since 2026-08-28 the file, once in effect, is the sole source of truth** — an unset key errors rather than falling back to `BUILT_IN`. **Top-level, beside `tune.py`, because it is a peer of it**: same shape, different boundary — `tune.py` changes which documents come back, this changes how they are shown |
| `src/fux/enrich.py` | SR-ENRICH | `fux enrich --plan/--check` — the deterministic halves |
| `src/fux/observe.py` | SR-OBSERVE | `.fux/observers/` — the dispatcher, the closed counts record, `args_hash`, and the liveness file `fux doctor` reads. **The only extension point that cannot change an answer**, and the module is where that is made structural rather than promised: no return path, a copy not a reference, dispatch after every write, and fux's own stdout taken away while consumer code runs |
| `tools/observer-bench/` | SR-OBSERVE | what the hook COSTS: the reference observer that prices the seam, the slow observer that tests what the cap actually promises, and the interleaved runner (W-181). ⚠ **The reference observer's realism is an assertion** — it prices the dispatch, never a subscriber's work, and its own docstring opens with that warning |
| `src/fux/correct.py` | SR-ENRICH | `fux correct` — the human half of the same plane: the eval file, the pin store, and the `corrections:` marker that says which body lines a person wrote. **Beside `enrich.py` rather than inside it**, because the two differ by AUTHOR: one plans and validates a model's text, the other writes a line a person typed, and folding them would make one module answer to two authors |
| `src/fux/mcp.py` | SR-MCP | the stdio JSON-RPC server — three tools, stdlib-only, warm across calls. **`answer` is deliberately absent**: the agent is the answerer |
| `src/fux/graph/` | SR-GRAPH | edges lifted into adjacency, unseeded label-propagation communities, PPR-lite, and the three relational verbs. Owns `.fux/runtime/graph.json` |
| `src/fux/inspect/` | SR-INSPECT | the index X-ray — one pass over the committed shards, the gitignored hash-to-word dictionary, the six lenses and the three provisional floors. **Reads only**, and the row is what makes the freshness gate demand that record the moment a lens changes what it claims about a corpus |
| `src/fux/maintain/` | SR-MAINTENANCE | the git hooks and their installer, the deferring runner, the write lock, the daemon and the local state files. **L5's write-time check is deliberately NOT here** — it lives in `store/writer.py`, because a check beside the thing it guards cannot be skipped |
| `src/fux/maintain/mergedriver.py` | SR-MERGE-DRIVER | the merge driver itself — carved out because its failure mode and its gate are its own |
| `src/fux/refer/` | SR-REFER | source · freshness · chunk · rescore · assemble. **Imports no transport**: the consumer's fetcher is injected |
| `src/fux/refer/_chunk.py` | SR-CHUNKING | what a passage IS — the fold rule that derives row/unit/section/file from heading depth, the universal table rule and the paragraph→line→word ladder. Carved out of SR-REFER's directory claim on `freshness.py`'s precedent: the subject reaches past `refer/` into what decoders EMIT |
| `src/fux/refer/freshness.py` | SR-URL-FRESHNESS | the six verdicts and the policy object — the **claim-strength vocabulary**, which now reaches past `refer/` into the output schema and `fux verify`. Carved out of SR-REFER's directory claim on `arc.py`'s precedent |
| `src/fux/refer/arc.py` | SR-CACHE | the content cache, keyed `(loc, sha)` so a hit cannot change an answer |
| `src/fux/refer/fetchcache.py` | SR-CACHE | the TTL fetch store — the only place in the engine that reads a wall clock |
| `src/fux/templates/` | SR-FETCHER | the two shipped fetchers as package data; **bytes, never imported** |
| `src/fux/templates/pii.toml.txt` | SR-PII | the shipped starter rules, written into every repo by `fux setup` — the safe ones enabled (credentials, email, PAN, US SSN/ITIN/MBI, Canadian SIN), the risky ones commented out with what each still over-matches (decisions 12 and 12a) |
| `src/fux/templates/refusals.toml.txt` | SR-REFUSAL | the six shipped starter rules. Carved out of SR-FETCHER's `templates/` claim on `ENRICH-SKILL.md`'s precedent — it is data a consumer edits, not a fetcher |
| `src/fux/templates/agents/` | SR-AGENT-POLICY | the canonical agent policy and its per-vendor renderings, shipped as wheel package data (`setup.py` itself stays with SR-DOTFUX — one component, one owner) |
| `src/fux/templates/agents/ENRICH-SKILL.md` | SR-ENRICH | the generation half — a skill rather than code, because a model call may not live under `src/` |
| `src/fux/templates/agents/DECODER-SKILL.md` | SR-DECODE | how to write or edit a decoder — a **build procedure for one plane**, not a rendering of the archived-results policy |
| `tests/test_work_environments.py` | SR-WORK-ENVIRONMENTS | the guard that keeps the three siblings apart — nothing under `src/`, `tests/`, `tools/` or `work/` reads `fux-playground`, and a measurement names the lab. **A `kind: process` record owns its enforcement** |
| `tests/test_benchmark_capture.py` | SR-WORK-BENCHMARK | the seven captures a filed benchmark run must carry — CAP-1…CAP-7 at the paths decision 7 names, baselined at 2026-09-13. **A `kind: process` record owns its enforcement** |
| `tests/test_backlog_rows_are_short.py` | SR-WORK-BACKLOG | rules 11-16: ids unique and ascending WITHIN each class section, one line at most 400 chars, no detail file, four columns, a source that EXISTS, and what closes it. ⚠ **Not whether the cited LOCATION is real** — that a file exists is checkable and that a sentence in it says what the row claims is not; the row's accuracy stays a human obligation |
| `tests/test_verb_table_agreement.py` | SR-DOTFUX | `.fux/README.md`'s verb table, SR-CLI §1's, and `build_parser()` held together. **The parser settles a disagreement** — comparing two documents can only say they differ. The prose is deliberately not compared |
| `tests/test_doctor_register_is_complete.py` | SR-DOCTOR | every live `doctor` row is registered and every registered row still exists, read by RUNNING doctor rather than parsing it. Conditional rows are exempted **by name** |
| `tests/test_confidence_floor_off.py` | SR-CONFIDENCE | decision 13's *"nothing mechanical catches it"*, caught: the `confidence floors` doctor row and `ask`'s once-per-process stderr note, both suppressed under `--json` and MCP, both from one string |
| `tests/test_handoff_names_its_model.py` | SR-WORK-LIFECYCLE | decision 6's one mechanical clause — every open item names what should execute it, and there is no second home for a handoff. **The record's only owned component**, and it was owed as a debt by its own decision 12 until 2026-09-14 |
| `tests/test_open_work_rows_are_short.py` | SR-WORK-OPEN-QUEUE | the row shape, the four balls and the `↳ blocks:` sub-rows — rules 13–19, 20–34 and 42–44. **A `kind: process` record owns its enforcement**, which is what makes the freshness gate able to demand it at all |
| `tests/test_open_work_is_not_stale.py` | SR-WORK-OPEN-QUEUE | the inbox's arithmetic and its claims about itself — rules 39–41 and 45, plus the tombstone rule 10 |
| `tests/test_no_work_item_is_lost.py` | SR-WORK-OPEN-QUEUE | the archive-never-delete invariant — rules 54–58. Every `W-nn` id resolves to a file in `work/open/` or `archive/open/`, with the ids that genuinely have none exempted **by name, never by range**; an exemption that stops being true fails the test, so the list shrinks and never rots |
| `tests/test_regression_runs.py` | SR-RS | the per-run contract for a conformance run. **The harnesses are not claimed here**: a harness belongs to the feature it measures, the discipline belongs to the record |
| `tools/pruning-eval/` | SR-POSTINGS | the gate harness and its frozen pre-registrations, held by the record that owns the pruning decision and carries its standing law |
| `tools/maintenance-bench/` | SR-MAINTENANCE | the hook-latency and merge-driver harness. **One file runs both, and a component is owned once** |
| `tools/runner-race/` | SR-MAINTENANCE | the soak that walks a second commit across a live runner's lifetime, to make the handoff window fire on purpose rather than waiting for it (W-182). ⚠ **It changes nothing under `src/` by design** — the first reproduction is a CAPTURE, and an unreproducible sweep is a result |
| `tools/pii-probe/` | SR-PII | what a rule would remove from a real corpus. The only thing that can see an over-broad rule — `doctor` compiles patterns and structurally cannot |
| `tools/refusal-probe/` | SR-REFUSAL | the shipped rules against real captured responses, and the runnable form of this record's veto condition. Owned by the record whose claim it tests |
| `tools/refer-bench/` | SR-REFER | the latency harness and its frozen pre-registration — a real `http.server` behind the **consumer's own generated fetcher**, so the measured path is the shipped one |
| `tools/refer-budget-sweep/` | SR-REFER | the assembler-vs-greedy budget sweep and its frozen pre-registration |
| `tools/differential/` | SR-T1-ACCELERATOR | the differential-law harness and its bench. ⚠ **Nothing imported it until 2026-09-15, and it broke silently twice while nothing did** (W-184: a PNG killed the query set, and `archived_weight` outlived the parameter by two days). `tests/derive/test_differential_harness.py` now imports `queryset` and `run` and holds the two assumptions that failed; **running it over a real corpus is still a person's job** |
| `tools/quality-controls/` | SR-RS | **every measurement control**, and the harnesses that run them: the content-free placebo, the decoy query set and the sealed subset (decision 15), plus the three built 2026-09-12 — `priors-probes.jsonl` + `priors_sweep.py` (intent-split probes over declared supersession and archived directories), `heading_control.py` (the rebuilt `heading` control with its own feature-off arm) and `table_flen.py` (the table-`flen` counterfactual). Owned by the record that demands them, not by the records whose behaviour they test: **a control belongs to the measurement discipline, so changing what a control IS updates the rule rather than the feature** |
| `tools/archived-signal-eval/` | SR-ARCHIVED-CONTENT | the live-vs-archived contamination instrument, its frozen pre-registration and its query set. Owned by the record whose claim it tests, because this measures a **feature gate** and takes no `R` id |
| `tools/graph-bench/` | SR-GRAPH | cost-attribution profiler for the graph lane — not a gate |
| `tools/golden-difficulty/` | SR-WORK-GOLDEN | the golden question difficulty scorer (decision 13) — a count of the discriminations a question forces, computed from the key and the corpus. Owned by the record that governs the benchmark's process, not by any engine record, because 🔴 **it must never read a prediction, a score or an index**: difficulty derived from fux's own results makes every stratified claim a tautology. It also **refuses a key path inside this repository**, which is [SR-LAW-11](0012_LAW-11-sealed-answer-key.md) made executable |
| `tools/quality/` | SR-WORK-QUALITY | the frozen quality contract — the declared query mix and the published cost of an error — **and `goldens.py`, the schema that keeps the rank contract and the relevance set apart** (decision 12). The mix and the cost are a **frozen instrument, not a harness**; `goldens.py` is the one executable thing here, and it exists because decision 12's rules are mechanical: an undeclared relevance list, or a `doc` outside its own relevance set, is refused rather than trusted |
| `tools/vector-gate/` | SR-RS | W-106's instrument — does a **contextual** embedder fused by RRF reach DENSE-CHUNK's frozen bar, and **do two implementations of one model produce the same vector**. ⚠ Held here by **decision 10's fallback**, the `tools/t2-eval/` precedent: the record it belongs to (`SR-VECTORS`) **does not exist** — W-112 is blocked on this instrument's own result, and a proposal is not a valid owner. It moves to `SR-VECTORS` if and when that record is accepted |
| `tools/t2-eval/` | SR-RS | a harness whose feature record was retired, held here by SR-RS decision 10's fallback. **A retired record cannot own anything, and a proposal is not a valid owner** |
| `node/` | SR-NODE-SEARCH | the Node read plane — 44 `.mjs` files as AUTHORED, shipped as ONE bundled file (L10, decision 13); no `dependencies` key, and no build step **for the consumer**. **The only owned component outside `src/` and `tools/`**, so `test_sr_ownership.py::components()` does not demand it; the row is what makes the freshness gate demand this record when a `.mjs` file changes. `compat/` and `hash/` have no Python twin and are exempt by decision |

| `tests/test_doc_registry.py` | SR-WORK-DOCS | the registry's own rules as code — live documents only, one row per document, no row pointing into `archive/`, every target existing. **A `kind: process` record owns its enforcement**; this test had **no owner at all** until 2026-09-14, so no change to it could ever demand the rule it enforces |
| `tests/test_doc_links.py` | SR-WORK-DOCS | every relative link in a live document resolves, and the exemption list — the append-only worklog, filed runs, pre-registrations, the archive, the changelog, the template's placeholders. **Each exemption is a frozen-by-law document, not a convenience**, which is why the list belongs to the documentation record rather than to the archive one |
| `tests/test_okf_bundle.py` | SR-WORK-OKF | parseable frontmatter and a non-empty `type` across `docs/` + `records/` + `work/`, the asserted document count, and the three declared boundaries whose reasons live in the docstring. **Previously unowned** — the conformance claim was gated and the gate belonged to nobody |
| `tests/test_archive_law.py` | SR-WORK-ARCHIVE | one archive, and no live document pointing into it where the rule forbids it. **Previously unowned.** What it cannot check is the naming-versus-citing line, which is stated in [SR-WORK-ARCHIVE](0062_WORK-archive.md) decision 8 as an unguarded hole rather than approximated by a looser check |
| `scripts/check-version-parity.py` | SR-WORK-RELEASE | the `SITES` list and the `--with-bundle` derivation check — the only thing standing between a missed version bump and a PyPI wheel and npm tarball naming different releases. **The first claimed component under `scripts/`**, and previously unowned despite being run by CI and by the release workflow |
| `tests/test_version_parity.py` | SR-WORK-RELEASE | runs the parity script on every push and builds a bundle to check the derivation. **Previously unowned** |
| `.claude/hooks/stop-if-blocked.sh` | SR-WORK-BLOCKERS | the `Stop` hook — refuses to end a turn while a blocker is unsurfaced, three times, then relents. **The relent is deliberate** and is stated in [SR-WORK-BLOCKERS](0064_WORK-blockers.md) decision 8: a hook that can never be escaped turns a blocker into a hang, and a hung session cannot report the question it owes |
| `.claude/hooks/inject-inbox.sh` | SR-WORK-BLOCKERS | the `UserPromptSubmit` hook — prepends `work/BLOCKED.json` and the queue's inbox to every prompt, so a pending decision cannot go unmentioned |
| `.claude/hooks/session-lock.sh` | SR-WORK-BLOCKERS | the `PreToolUse` hook — one writer **per asset**, not per session, so two sessions editing different files run in parallel while two editing the queue collide. **The first claimed components under `.claude/`** |
| `.claude/hooks/guard-golden-answer.sh` | SR-WORK-GOLDEN | the `PreToolUse` hook that refuses any Claude Code tool call **targeting** the sealed answer key. ⚠ **Two known false positives, and no agent can fix them**: its TARGET check is a bare substring, so it also refuses every edit to *itself* and to `archive/open/W-198-golden-answers-canonical.md` — neither of which is a key. Both are asserted as measured facts in `tests/test_golden_key_guards.py`. Left deliberately unowned by [SR-WORK-BLOCKERS](0064_WORK-blockers.md) decision 10 — *"it belongs to the sealed benchmark's rule"* — until that rule had a record. **What it cannot see is stated rather than approximated** ([SR-WORK-GOLDEN](0066_WORK-golden.md) decision 6): a recursive grep that never names the folder |
| `.claude/hooks/guard-sealed-key.sh` | SR-WORK-GOLDEN | the **sixth** guard, added 2026-09-20 with W-198. It closes the first hook's Bash-branch gap — that branch never matched a bare plural path, so an arbitrary shell command could reach the canonical spelling. 🔴 **A second file rather than a one-line fix**, because the first hook refuses every edit to itself and routing around a working guard was the wrong trade. Its TARGET check is anchored to a **path component**, the fix `tests/test_golden_key_never_committed.py` already made, so it does not inherit the false positives above |
| `tests/test_golden_key_guards.py` | SR-WORK-GOLDEN | the test that fails when any guard stops covering a spelling. It found two holes on its first run: a slash-terminated `.gitignore` pattern that matched only while the directory existed, and the Bash-branch gap the sixth guard closes. Works from `git check-ignore`, `git ls-files` and synthetic paths — it opens nothing |
| `scripts/gen-golden.py` | SR-WORK-GOLDEN | renders `CLAUDE.md` §Golden answer key from the record's one normative block, rewriting link targets and doing nothing else. **A second generator rather than a flag on `gen-laws.py`**, whose contract is a validated *set* of ten handles; the link rewrite is imported from it, not copied |
| `tests/test_claude_md_golden.py` | SR-WORK-GOLDEN | holds that block byte-equal to the record, refuses a verbatim third copy in any live document, and asserts `work/golden/README.md` links rather than restates. **Deleting this file makes the `CLAUDE.md` block an illegal restatement** — SR-LAW-0 decision 5, the same shape as the law block's bind |
<!-- OWNERSHIP-TABLE-END -->

---

## Describes — which record's subject REACHES INTO a component it does not own

**A second, additive relation** ([SR-WORK-OWNERSHIP](0054_WORK-ownership.md)). Ownership
stays exactly one record per component; **describes is any number**, and the
freshness gate demands the owner **and every describer**.

⚠ **This exists because the gate was narrower than it read.** `src/fux/query/`
is owned by SR-ASK, so rewriting the scorer satisfied the check by touching
SR-ASK — while **SR-RANKING, whose entire subject is that scorer, rotted
silently** and was never opened. It passed through all of W-76 that way, sixteen
records deep.

**`describes` never substitutes for `owns`.** A component with no owner fails
whatever describes it, and a record listed as describing something it also owns
is a defect (veto 2). **Every row states its reason** — a bare pair is
unauditable, and an unauditable table stops being trusted.

⚠ **Seeded small and first-hand.** Four rows, each verified against a change
actually made, rather than a sweep guessing at intent — a bulk fill would make
the relation *look* enforced while asserting things nobody checked.

<!-- DESCRIBES-TABLE-START -->

**A component may be narrowed to SYMBOLS: `` `path::name,name` ``.** The gate
then demands that record only when the change touches one of those top-level
`def`s or `class`es. A bare path means the whole file and is the default —
every row written before 2026-09-11 is one, and a describer that has not
narrowed itself is still describing everything.

⚠ **Narrow a row only when you can show the symbol list is the record's WHOLE
reach in that file.** A too-narrow list switches the gate off silently, which
is worse than the noise it removes — `tests/test_sr_freshness.py` checks every
named symbol exists, and nothing can check that the list is complete. The two
rows narrowed so far were each verified by reading every mention in the file
(W-140 row 20).

| component | record | why it reaches in |
|---|---|---|
| `src/fux/cli.py` | SR-OUTPUT | decision 10 binds **every gated flag** in this file to `default=None`. Owned by SR-CLI, constrained here — and the constraint failing silently is precisely how six flags shipped at `default=False` |
| `src/fux/query/__init__.py` | SR-CONFIDENCE | the confidence block is assembled and emitted here (`confidence_out`, `_fill_confidence`), while SR-ASK owns the module for the scan and unification |
| `src/fux/query/__init__.py::_show_band,_gated,_print_index_answer,_print_refer_answer,cmd_ask,cmd_find,cmd_answer` | SR-OUTPUT | the emission gate (`_show_band`, `_gated`) lives here — where a rendering decision reaches into a file whose subject is the query itself |
| `src/fux/derive/accel.py` | SR-CONFIDENCE | `stats_out` is passed through here so the accelerator and the scan agree about `df`/`n`. **The differential law is what makes this load-bearing**: if only one path carried it, the two would disagree about how confident fux is |
| `src/fux/query/rank.py` | SR-TUNE | `[priority]` is DATA in SR-TUNE and RESOLUTION on `rank.py::Weighting` — the register's own ownership note already says so, which is what made this row checkable rather than asserted |
| `src/fux/ingest/run.py` | SR-PII | the redaction pass, and its position between `content_sha` and `extract_fields` — decision 3, which is the whole record. Also `_pii_ruleset_moved`, the reuse invalidation. Owned by SR-INGEST for the walk |
| `src/fux/enrich.py` | SR-PII | `enrich=` for `url:` documents — `_document_text` reading the retained blob, and the single synthetic `.fux/sources/urls` scope. Owned by SR-ENRICH for enrichment itself |
| `src/fux/ingest/sourcelist.py` | SR-PII | `enrich` on the URL list, resolved through the same three layers as `keep` and `ttl` |
| `src/fux/config.py` | SR-PII | `[sources.url] enrich` — the source-wide layer |
| `src/fux/cli.py::_require_pii_rules,main` | SR-PII | `_require_pii_rules` and `PII_EXEMPT` — decision 17's refusal, placed before dispatch so a verb added later is gated without knowing it. Owned by SR-CLI for the verb surface; the rule and its exemptions are this record's |
| `src/fux/setup.py::run` | SR-PII | writes `.fux/pii.toml` from the starter, write-if-missing — the half of decision 17 that makes the refusal fixable. Owned by SR-DOTFUX for scaffolding |
| `src/fux/store/fuxdir.py` | SR-PII | `pii.toml`'s row in `COMMITTED_FILES` — **the ruleset is committed, and that is the decision** (decision 1): a redaction rule that lived on a gitignored path would redact one clone and not the next, so the file has to sit in the category `fux doctor` audits. Owned by SR-DOTFUX for the layout |
| `src/fux/ingest/urlsrc.py` | SR-ACQUIRED | retention lives in `fetch_all()` and **never inside a fetcher** (decision 5) — W-86 P8's precedent, so every fetcher gains it with no line changed in any of them. Owned by SR-FETCHER for the contract itself |
| `src/fux/ingest/urlsrc.py` | SR-REFUSAL | the refusal check sits in `fetch_all()`, **after `_unpack` and before persist and decode** (decision 1) — the ordering is the decision, and it lives in a file this record does not own |
| `src/fux/ingest/urlsrc.py` | SR-URL-FRESHNESS | `UrlEntry.ttl`, and `resolve_urls` applying the same three layers to it as to `keep` — a per-URL freshness bound resolved inside the ingest module |
| `src/fux/ingest/sourcelist.py` | SR-URL-FRESHNESS | `ttl` is the **first typed attribute** in the grammar: `Attribute` grew an optional `validate` callable because a duration cannot be a closed enum. Owned by SR-URL-LIST for the grammar itself, constrained here |
| `src/fux/ingest/sourcelist.py` | SR-ACQUIRED | `keep`, and its default flipping to `true` (decision 4) — a value in a file this record does not own |
| `src/fux/config.py` | SR-ACQUIRED | `[sources.url] keep` and `acquired_max_bytes` — the source-wide layer and the store's bound |
| `src/fux/config.py` | SR-URL-FRESHNESS | `[sources.url] ttl`, validated by the source list's **own** duration grammar rather than a second copy, so `--ttl 1x` and a hand-written `ttl=1x` fail identically |
| `src/fux/refer/__init__.py` | SR-URL-FRESHNESS | both `as-ingested` fallback points in `_obtain`, and `min(policy, declared)` — decision 11's arithmetic, which is where a per-URL value is prevented from widening a caller's policy |
| `src/fux/refer/source.py` | SR-URL-FRESHNESS | `from_acquired`, and decision 6's rule that it **imports** `_decode_fetched` and `sanitize` rather than reimplementing them — the property the whole fallback rests on |
| `src/fux/store/fuxdir.py` | SR-ACQUIRED | the `ACQUIRED` declaration and its `.gitignore` line. Owned by SR-DOTFUX for the layout; this is the record that added the third kind |
| `src/fux/mcp.py` | SR-OUTPUT | decisions 11, 16 and 17 reach in directly: `[mcp]`'s closed key set (`top` only, `band` refused by name), `tools/list` advertising the RESOLVED `top` rather than a literal (the W-83-class defect this decision exists to prevent), and `[mcp]` being loaded once at `serve()` start rather than per search. Owned by SR-MCP for the protocol itself; this is a rendering decision reaching into the module that serves it |

| `src/fux/query/__init__.py` | SR-ANSWER | `cmd_answer` and both printers live here — `ANSWER_TOP`, the refer/index fork, `_freshness_of`. ⚠ **Added 2026-09-05 because this record owned NOTHING and therefore could never be opened by the gate**: W-108 rewrote the `answer` verb and the freshness check demanded SR-ASK, SR-CONFIDENCE, SR-OUTPUT, SR-REFER and SR-URL-FRESHNESS — every record except the one whose entire subject is the verb. Owned by SR-ASK for the scan and unification |
| `src/fux/query/refer_answer.py` | SR-ANSWER | the seam between `cmd_answer` and `refer()` — the candidate list, and `_load_fetchers`' per-URL dispatch. Owned by SR-ASK under its `src/fux/query/` claim |
| `src/fux/refer/_rescore.py` | SR-RERANK | `passage_boost` and the bounded multiplicative uplift reach in here (decision 9) — the same constant that reorders documents scores their passages. Owned by SR-REFER under its `src/fux/refer/` claim |
| `src/fux/maintain/urlstate.py` | SR-REFUSAL | `refused` and `record_refusals` — the counter's storage, in the file SR-MAINTENANCE owns, on `rate_limited`'s shape with the key turned from host to rule |
| `src/fux/ingest/urlsrc.py` | SR-URL-FRESHNESS | `_record_refusals` in `fetch_all()` — see SR-REFUSAL decision 11; the counting sits beside the refusal check the row above places |
| `src/fux/ingest/sourcelist.py` | SR-ARCHIVED-CONTENT | `archived` on both lists — `dirs` since 2026-08-22 and `urls` since 2026-09-11 (decision 1a), the same name, values and default on each. ⚠ **Added because this record OWNED NOTHING in `src/` and could therefore never be opened by the freshness gate** — the [SR-ANSWER](0105_answer.md) precedent above, exactly: W-126 amended this record and the gate demanded seven others instead |
| `src/fux/ingest/urlsrc.py` | SR-ARCHIVED-CONTENT | `UrlEntry.archived`, and `resolve_urls` applying **two** layers to it where `keep` and `ttl` take three — the absence of a source-wide layer is decision 1a's call, not an omission |
| `src/fux/ingest/run.py` | SR-ARCHIVED-CONTENT | `_archived_url_ids` and `_with_archived` — the declaration reaching a record, including a CARRIED one, which is the half that makes a retired page declarable at all. Owned by SR-INGEST for the walk |
| `src/fux/setup.py::detect_workspace,wire_workspace,_yarn_berry_linker` | SR-NODE-SEARCH | the monorepo half of decision 15 — which signals mean a workspace, and the format-preserving splice into a manifest fux does not own. **It lives in `setup.py` rather than in `fuxdir.py` by structure, not by convention**: `ensure_layout` runs at the head of every ingest and must never edit a consumer's `package.json`. Owned by SR-DOTFUX as scaffolding |
| `src/fux/doctor.py::_node_reader,_installed_reader` | SR-NODE-SEARCH | the `node reader` row — the version, the shape, a stale `src/` tree still in the consumer's repo, and a shape-C manifest with nothing installed to resolve it. Owned by SR-DOCTOR, which decides what a row IS |
| `tools/differential/node_arm.py::bundle_entry,Arm` | SR-NODE-SEARCH | the sixth surface — the published bundle against the module tree it was built from (`bundle_entry` builds it per run; `Arm.compare_bundle`, `compare_bundle_api` and `compare_bundle_mcp` compare it). ⚠ **Narrowed to the top-level symbols the gate can resolve** — a method name here would switch the gate off silently, which `tests/test_sr_freshness.py::test_the_narrowing_is_recorded_where_the_gate_can_read_it` catches. Owned by SR-T1-ACCELERATOR, which owns the harness |
| `src/fux/store/fuxdir.py::ensure_node_reader,node_version,node_shape,_node_source,_packaged_node_files,_prune_node_reader,_workspace_manifest` | SR-NODE-SEARCH | the vendoring half of R2 — which files are written into `.fux/node/` and the version comparison that decides whether to overwrite. **The `.fux/` SHAPE is still SR-DOTFUX's subject** (it is the fourth shape there); what this record decides is that the vendored thing is a reader and that a stale one is a wrong answer |
<!-- DESCRIBES-TABLE-END -->

