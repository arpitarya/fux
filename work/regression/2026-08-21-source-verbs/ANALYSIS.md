---
type: Analysis
name: source-verbs-analysis
description: What the W-63 surface capture found — four defects, three of them in the change being captured and one older, each with a repro and a fix.
status: complete
timestamp: 2026-08-21T00:00:00Z
---

# What capturing the surface found

**The headline is not a number.** It is that **writing the transcript down
found four defects that the unit tests did not**, three of them in the change
being captured. Every one was a case where the code did something defensible
and *said* something false, which is precisely the class a test asserting
behaviour will not catch and a person reading output will.

That is the argument for the capture rule, restated with evidence.

| # | defect | found by | status |
|---|---|---|---|
| 1 | `update` announced a network fetch against an empty URL list | reading the capture | **fixed** |
| 2 | `add '*.pdf' --types` silently un-indexed every other document | running the verb | **fixed** |
| 3 | `add <file>` exited 1 saying "the fetch failed" about a PDF | e2e test written from the DoD | **fixed** |
| 4 | `explain <removed-doc>` answered as though it were still indexed | e2e test written from the DoD | **fixed** (older, not W-63's) |

---

## 1. `update` claimed a network call it did not make

**What happened.** After the capture removed the last URL, `fux update`
printed `fetching every listed URL (network)` on stderr — against a list with
no lines in it. It then made no request, correctly.

**Why it matters more than it looks.** That line is an **L4 announcement**: the
one thing the engine says out loud about going to the network. A fenced,
opt-in path whose announcement fires when nothing was fetched trains a reader
to ignore it, which is the only way that fence fails in practice.

**Fix.** `cmd_update` reads the list and refreshes only when it has entries;
the message now carries the count (`fetching 3 listed URL(s) (network)`), so
it cannot be true and vacuous at the same time.

**Repro (against the pre-fix code).**

```bash
sh evidence/fixture.sh /tmp/d && cd /tmp/d
python -m fux.cli remove https://wiki.corp/runbook   # empties the list
python -m fux.cli update                             # printed the fetch line anyway
```

## 2. Adding one file type removed every other

**What happened.** `.fux/sources/types` **replaces** the built-in allowlist
rather than extending it (ADR-TYPES) — absent means `DEFAULT_TYPES` applies,
and the moment the file exists it is the whole list. So
`fux add '*.pdf' --types` on a repo with no types file wrote a one-line file
and un-indexed every markdown document in the corpus. Exit 0, no warning; the
next `ingest` reported them as `not an indexed file type`.

**This is W-55's defect from a new direction** — an invisible filter — arriving
through the verb built to make the corpus easier to manage.

**Fix.** When `add` **creates** the types file, it seeds the built-in patterns
first, with a comment saying why. The diff then shows the allowlist growing by
one instead of being replaced by one, which is what the user meant.

**Repro (against the pre-fix code).**

```bash
sh evidence/fixture.sh /tmp/d && cd /tmp/d
python -m fux.cli ingest                       # 2 docs
python -m fux.cli add '*.pdf' --types
python -m fux.cli ingest                       # 0 docs; every .md now "not an indexed file type"
```

## 3. A type-allowlist skip was reported as a failed fetch

**What happened.** `cmd_add` checked whether the entry appeared in the run's
`skipped` list and, if so, printed `the line is written; the fetch failed: …`
and exited 1. It did that for **any** skip reason — so
`fux add docs/architecture.pdf` exited 1 claiming a fetch had failed for a
local file nothing had tried to fetch.

**Fix.** The failure branch is now gated on a fetch having been attempted. A
skip that is not a fetch failure is a fact about the corpus, exits 0, and for
the allowlist case says what would change it.

**Repro (against the pre-fix code).**

```bash
sh evidence/fixture.sh /tmp/d && cd /tmp/d
python -m fux.cli add docs/architecture.pdf    # exit 1, "the fetch failed"
```

## 4. `explain` could not tell "no edges" from "not in the corpus"

**Older than W-63, and surfaced by it.** `cmd_explain` printed
`<doc> has no recorded relationships.` and exited 0 both for a document with
no edges *and* for a document that is not in the index at all. Its own comment
said the two were different — `# Not in the graph at all — which is different
from "has no edges"` — directly above the branch that treated them the same.

**W-63 is what made it reachable in one command:** `fux remove docs/x.md` then
`fux explain docs/x.md`, which reports a deleted document as a known one.

**Fix.** `explain` now checks the committed index — not the graph plane, since
an edgeless document is absent from one and present in the other — and raises
for a document the corpus does not hold. It belongs to
[ADR-GRAPH](../../../docs/adr/0030_graph.md), updated in the same change.

**Repro (against the pre-fix code).**

```bash
sh evidence/fixture.sh /tmp/d && cd /tmp/d
python -m fux.cli ingest
python -m fux.cli remove docs/pruning.md
python -m fux.cli explain docs/pruning.md      # "has no recorded relationships", exit 0
```

---

## Unresolved

- **`--check` does not verify URL documents.** Doing so means fetching them,
  and `--check` is documented as not going to the network on its own. It says
  so on stderr and counts them separately rather than reporting them as fresh.
  Whether `--check --fetch` should exist is **not decided here** — it is a new
  flag on a new verb and wants its own call.
- **`fux update --check` reports drift on `dirs` only, per document.** It has
  no view of a *new* file that no record covers yet; that is what a plain
  `fux update` finds. Naming it here rather than implying `--check` is a
  complete answer.
