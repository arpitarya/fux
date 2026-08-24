---
name: fux-enrich
description: Generate enrichment for documents in a Fux corpus. Use ONLY when explicitly asked to enrich, re-enrich, or fill in enrichment for a named scope — for example "enrich the ADRs", "run fux enrich", "fill in the missing enrichment". Writes files into .fux/enrich/ that are committed to the repository and that change search ranking.
---

# Enriching a Fux corpus

Fux ranks from a committed index. **Enrichment adds a short piece of written
context to a document so it can be found by words it does not literally
contain** — a runbook about "the checkout circuit breaker" should be findable
by "payment resilience" even if that phrase never appears in it.

Fux does not call a model. **You are the model.** `fux enrich` computes the
worklist and validates what you write; generating the text is this skill's job.

> ⚠ **This skill writes files that are committed and that change ranking.**
> Only run it when a human asked for it by name. Never run it as a side effect
> of another task.

## 1 · Get the worklist

```bash
fux enrich --plan
```

```
scope docs/adr (enrich=true)
  docs/adr/0012_ranking.md      sha 3f8a1c2d9b04   9 chunks   MISSING
  docs/adr/0031_maintenance.md  sha 9b2e04f1a733   6 chunks   STALE (was 7c1d4e02b918)
-> 2 documents, 15 chunks
```

**Only documents in a declared scope appear.** A scope is a directory line in
`.fux/sources/dirs` carrying `enrich=true`. If the plan is empty, nothing is
declared — say so and stop; do not add the attribute yourself, because which
directories get enriched is a human's decision.

`STALE` means the document changed after it was enriched. Treat it exactly like
`MISSING`: write a fresh file under the **new** sha. Do not edit the old one.

## 2 · Read the document, then write the file

For each document in the plan, read it and write
`.fux/enrich/<sha>.md` — the sha from the plan, not one you compute.

```markdown
---
source: docs/adr/0012_ranking.md
source_sha: 3f8a1c2d9b04
chunks: 9
model: <the model you are>
generated: 2026-08-23
skill: fux-enrich@1
---
Establishes how Fux orders results: the BM25F field weights, term-frequency
saturation, and why per-field scores are never summed. Covers the length
normaliser and the reason it cannot be a tuning knob while it is committed.
Relevant to questions about relevance tuning, result ordering, scoring
constants, and why a document ranks where it does.
```

**Every frontmatter key is required.** `fux enrich --check` refuses a file
missing any of them, and a refused file is silently not indexed.

`source_sha` is the one key fux **verifies**. `model` is a claim fux
**records** and cannot check — stamp it honestly.

## 3 · What to write in the body

**Write what the document is about and what questions it answers**, in prose,
in about 60–120 words. Every word becomes searchable vocabulary attached to
this document, which is exactly the leverage and exactly the risk.

**Do:**

- Name the concepts in the vocabulary a *searcher* would use, not only the
  document's own. That is the entire point: if the document already said the
  word, indexing it again buys nothing.
- Name what kind of question this document answers.
- Use the surrounding system's real terminology — read the neighbouring files
  if you are unsure what things are called.
- Mention what it supersedes or is superseded by, if the document says so.

**Do not:**

- Summarise the content. A summary repeats words the document already has, and
  those are already indexed.
- Invent facts. If the document does not say something, it is not context, it
  is fiction — and it will be retrieved as though the document said it.
- Include the frontmatter's own values in the body. Fux strips the frontmatter
  before indexing precisely so a document cannot match a query for its own
  metadata.
- Add keywords in a list. This is prose; term frequency is computed from it,
  and a keyword pile distorts the length normaliser.
- Guess at a sha, a chunk count, or a path. They come from `--plan`.

## 4 · Check your work

```bash
fux enrich --check
```

```
enrichment: 1 scope(s) declared
  docs/adr                     41/41  ok
```

**Every scope must reach `n/n`.** Partial coverage *inside* a scope is a
defect: a document that has enrichment can be found by words a document without
it cannot, so a half-enriched scope tilts ranking toward whichever half you
finished.

If `--check` refuses a file, it names the reason. Fix it and re-run.

## 5 · Work scope by scope

One scope, then `--check`, then the next. A scope is sized to be finishable —
`docs/adr` is 41 documents, one comfortable session. **Do not start a second
scope until the first reports `n/n`**, because a half-finished scope is worse
than an untouched one.

If the plan is larger than you can complete, say which scopes you did and which
you did not, and stop. Leaving a clear boundary is fine; leaving a scope
half-covered is not.

## 6 · Committing

The files go in git. They are part of the corpus, they are reviewed like any
other change, and a reviewer reading the diff should be able to tell whether
the context you wrote is true.

Do not commit them yourself unless asked.
