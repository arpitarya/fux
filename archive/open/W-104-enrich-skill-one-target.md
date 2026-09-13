---
type: OpenItem
id: W-104
title: "W-104 — the fux-enrich skill runs --plan itself, enriches one named target, and asks before doing a list"
description: "Today the skill's step 1 is a bash block a human is assumed to have run, and its step 5 tells the agent to finish a whole scope. Both are wrong for the way it is actually invoked: `enrich this URL` should enrich that URL, and a 41-document plan should be a question, not a session. Add a target selector to `fux enrich --plan`, and rewrite the skill to plan internally, honour a named target, and prompt before a bulk run. The staleness hash already exists — this item pins it at write time rather than inventing a second one."
status: open
lane: agent
timestamp: 2026-09-01T00:00:00Z
---

# W-104 — one target, planned internally, confirmed before bulk

**Model: Sonnet** for the CLI selector and the skill rewrite. **Opus** for the
sentence in ADR-ENRICH that says what a target selector does *not* change,
because that is where a scope-shaped feature quietly becomes an ingest filter.

## The record this implements

[ADR-ENRICH](../../docs/adr/0040_enrich.md) — decisions 4 (scope is declared),
5 (partial coverage is the steady state), 10 (`fux-enrich` is invoked, never
ambient) and 11 (`--plan` prints the full sha). The skill file
[`ENRICH-SKILL.md`](../../src/fux/templates/agents/ENRICH-SKILL.md) is owned by
that record.

## Goal

Make the skill behave the way it is actually asked for. *"Enrich the ADR on
ranking"* should enrich that one document. *"Enrich the ADRs"* should say how
many there are and ask. Neither should require the human to have run
`fux enrich --plan` in another window first.

## What is already true, and must not be rebuilt

🔴 **The staleness hash exists and is the design.** Enrichment is keyed by the
source document's content sha: the file is named `<sha>.md` and carries
`source_sha:` in its frontmatter, `validate()` compares them, and
`_enrichment_for()` in [`run.py`](../../src/fux/ingest/run.py) simply does not
find a file for a document that changed. ADR-ENRICH decision 3 and
[`enrich.py`](../../src/fux/enrich.py)'s module docstring both say why: *"no
staleness check to forget to write."*

**Do not add a second hash.** A digest of the enrichment text, a `doc_hash`
field, a sidecar — each would be a second answer to a question that has one,
and the two would drift. What is genuinely missing is narrower and is below.

## The one real gap in the hashing

**A window between plan and write.** `--plan` prints a sha; the agent then
reads the document, writes prose, and saves `<sha>.md`. If the document changed
in between — a rebase, a concurrent edit, another agent — the agent writes an
enrichment under a sha the document no longer has. `--check` catches it
afterwards as an orphan, but only if someone runs `--check`.

The fix is one line of discipline plus one command: **the skill re-runs
`fux enrich --plan <target>` immediately before writing and confirms the sha is
unchanged.** No new state, no new field.

## Definition of done

### The CLI

- [ ] `fux enrich --plan [TARGET]` takes an optional positional. `TARGET` is a
      document `loc` (`docs/adr/0012_ranking.md`) or a URL exactly as it
      appears in `.fux/sources/urls`. Matching is **exact**, not a prefix and
      not a glob: a selector that silently matches two documents is how a
      one-document request becomes a bulk run.
- [ ] A `TARGET` that is not in any declared scope prints why — *not declared*
      (no `enrich=true` reaches it) is a different message from *not indexed*
      (fux has never seen it), because the fixes are different and the human
      needs to know which.
- [ ] 🔴 **`TARGET` filters the report, it does not widen scope.** A document
      outside every `enrich=true` scope is still not enrichable, and naming it
      does not make it so. Which directories get enriched stays a human's
      declaration — ADR-ENRICH decision 4, unchanged.
- [ ] `--check [TARGET]` takes the same selector, for symmetry. A human who
      just enriched one document should be able to check that one.
- [ ] Coverage arithmetic is unaffected: a filtered `--plan` still reports
      `n/total` for the scope, so a single-target run cannot read as a scope
      being complete.

### The skill

- [ ] **Step 1 becomes the agent's own call, not an instruction to the human.**
      The skill runs `fux enrich --plan` (or `--plan <target>` when the request
      named one) as its first action.
- [ ] **A named target is enriched, and only it.** *"Enrich the ranking ADR"*,
      *"enrich https://…"* → one `--plan <target>`, one file, one `--check`.
- [ ] **A multi-document plan is a question, not a session.** When the plan
      returns more than one document and the request did not name a scope
      explicitly, the skill states the count and the chunk total and asks
      whether to do all of them or one — and **stops for the answer.** It does
      not start and it does not pick.
- [ ] 🔴 **Re-plan before writing.** Immediately before writing each file, the
      skill re-runs `--plan <target>` and confirms the sha still matches what
      it read the document at. A changed sha means start over on that document;
      it never means write under the old one.
- [ ] Step 5's *"do not start a second scope until the first reports n/n"*
      survives **for a scope run** and is explicitly scoped to one: it is now
      wrong as a blanket rule, because a single-target run leaves a scope
      partial on purpose and that is the requested outcome, not a defect.
- [ ] The skill's frontmatter `description` gains the single-target and URL
      phrasings, so *"enrich this page"* routes here.
- [ ] [ADR-ENRICH](../../docs/adr/0040_enrich.md): a decision recording the
      selector, that it filters and never widens, and that the skill plans
      internally. Decision 5 (partial coverage is the steady state) is what
      makes single-target legitimate — cite it, do not restate it.

## Hazards

- 🔴 **A selector is one step from an ingest filter.** `fux enrich --plan x`
  must never become a way to enrich something no `enrich=true` line covers. If
  a reviewer cannot tell from the code which of the two it is, it is the wrong
  one.
- ⚠ **Prompting is only safe because the skill is invoked, never ambient**
  (ADR-ENRICH decision 10). An ambient skill that asks a question is an ambient
  skill that eventually gets a yes nobody meant.
- **The tilt is still real** (decision 6). A single-target run makes one
  document findable by words its neighbours are not. That is the requested
  behaviour and the skill should say so when it finishes, in one line, rather
  than leaving the human to discover it in a ranking.

## Out of scope

Any change to what enrichment *is* — the body guidance in step 3, the 60–120
word bar, the frontmatter key set. Batch generation, parallelism, or fux
calling a model: decisions 1 and 2, and none of this reopens them.
