---
name: fux-enrich
description: Generate enrichment for documents in a Fux corpus. Use ONLY when explicitly asked to enrich, re-enrich, or fill in enrichment — for one named document or URL ("enrich this page", "enrich the ranking ADR", "enrich https://…") or for a named scope ("enrich the ADRs", "fill in the missing enrichment"). Writes files into .fux/enrich/ that are committed to the repository and that change search ranking.
---

# Enriching a Fux corpus

Fux ranks from a committed index. **Enrichment adds the QUESTIONS a searcher
would type, so a document can be found by words it does not literally
contain** — a postmortem titled *"checkout unavailable for 47 minutes"* should
be findable by *"what happened during the checkout outage"*, a word that
appears nowhere in it.

🔴 **You write questions, not a summary.** That changed on 2026-09-05, and it
changed because prose was measured and questions were not: a blind enrichment
run scored **+1 fixed / −1 broken** — no net gain — and the one it broke was
broken by *context prose that carried currency words into a superseded
record*. Questions cannot do that: a question is a retrieval claim about one
document, and `fux enrich --check` refuses one that does not retrieve it.

The technique is **doc2query** (Nogueira & Lin 2019) with **doc2query−−**'s
filter (arXiv 2301.03266).

Fux does not call a model. **You are the model.** `fux enrich` computes the
worklist and validates what you write; generating the text is this skill's job.

> ⚠ **This skill writes files that are committed and that change ranking.**
> Only run it when a human asked for it by name. Never run it as a side effect
> of another task.

## 0 · Decide what you were asked for, before running anything

| the request named | you enrich |
|---|---|
| one document or URL | that one |
| a scope ("the ADRs", "docs/runbooks") | that scope — after step 1's count |
| nothing in particular ("enrich the corpus") | **ask first.** See step 1 |

## 1 · Get the worklist yourself

**You run this, not the human.** Do not ask them to paste a plan.

```bash
fux enrich --plan                          # every declared scope
fux enrich --plan docs/adr/0012_ranking.md # one document
fux enrich --plan https://example.com/x    # one URL
```

```
scope docs/adr (enrich=true) — filtered to docs/adr/0012_ranking.md
  docs/adr/0012_ranking.md  sha 3f8a1c2d9b04e7a1c05b2f9d84e6a3771c0d5e82  9 chunks  MISSING
-> 1 document, 9 chunks
```

**`TARGET` is exact** — the loc as the index spells it, or the URL as
`.fux/sources/urls` spells it. Not a prefix, not a glob. If you are unsure of
the spelling, run `fux enrich --plan` with no target and read it off the plan.

**`TARGET` filters; it does not widen.** A document no `enrich=true` line
reaches is not enrichable, and naming it will tell you so rather than doing it.
Which directories get enriched is a human's decision — never add `enrich=true`
yourself.

### 🔴 More than one document in the plan? Ask.

If the plan returns **more than one document** and the request did not name a
scope explicitly, **stop and ask**:

> The plan has 41 documents / 380 chunks in `docs/adr`. Do you want all of
> them, or shall I start with one?

State the count and the chunk total, then **wait**. Do not start. Do not pick.
A bulk enrichment run changes ranking across a whole scope, and it is not a
thing to be inferred from an ambiguous sentence.

**Copy the sha exactly as printed — the whole thing.** It is the filename and
it is the one field fux verifies; a prefix is refused as `STALE`.

`STALE` means the document changed after it was enriched. Treat it exactly like
`MISSING`: write a fresh file under the **new** sha. Do not edit the old one.

If the plan is empty, nothing is declared — say so and stop.

## 2 · Read the document, re-plan, then write the file

For each document: read it, write the questions, then **immediately before saving,
re-run `fux enrich --plan <that document>` and confirm the sha is unchanged.**

🔴 **This is not ceremony.** Between the plan and the write you read a
document, thought, and wrote several lines. A rebase, a concurrent edit or
another agent in the same repo can move the document in that window, and an
enrichment written under a sha the document no longer has is invisible: fux
simply does not find it, and nothing reports an error. If the sha moved, throw
away the sha — not the prose, which is probably still true — and start that
document again from the new plan line.

Write `.fux/enrich/<sha>.md` — the **full** sha from the plan, not a prefix of
it and not one you compute.

```markdown
---
source: docs/adr/0012_ranking.md
source_sha: 3f8a1c2d9b04e7a1c05b2f9d84e6a3771c0d5e82
chunks: 9
model: <the model you are>
generated: 2026-08-23
skill: fux-enrich@1
---
How does fux decide which result comes first?
Why are per-field scores never added together?
What controls how much a long document is penalised?
Where do the BM25F field weights live and can I change them?
Why can the length normaliser not be a tuning knob?
What makes a term-frequency count stop mattering?
```

**One question per line. Five to ten. Nothing else in the body.**

If the document **supersedes** another, or **is superseded by** another, say so
in the *frontmatter*, never in a question:

```markdown
superseded_by: docs/adr/0019_calder-gateway.md
```

🔴 **`superseded_by:` is the one key here that reaches the RANKING.** It marks
this document retired, exactly as the successor's own `supersedes:` would — and
it exists because a document retired years ago cannot name a successor that did
not exist yet. The named document must be in the corpus; a name that resolves
to nothing is ignored. Do not write it unless the document itself, or the
successor, says so.

**Every frontmatter key is required.** `fux enrich --check` refuses a file
missing any of them, and a refused file is silently not indexed.

`source_sha` is the one key fux **verifies**. `model` is a claim fux
**records** and cannot check — stamp it honestly.

## 3 · What to write in the body

**Five to ten questions, one per line, each ending in `?`.** Nothing else — no
summary paragraph, no heading, no bullet markers.

Every word becomes searchable vocabulary attached to this document, which is
exactly the leverage and exactly the risk.

**Write the question someone would type BEFORE they knew this document
existed.** That is the whole test. If they already knew the title, they would
not be searching.

**Do:**

- Use the vocabulary a *searcher* brings, not the document's own. If the
  document already said the word, indexing it again buys nothing.
- Cover the distinct things this document answers — a runbook answers *how do
  I roll it back*, *who approves it* and *what breaks if I do not*, and those
  are three questions, not one.
- Use the surrounding system's real terminology — read the neighbouring files
  if you are unsure what things are called.

**Do not:**

- **Echo the document's title.** A question that repeats the heading retrieves
  the document trivially and teaches the index nothing; `--check` scores with
  the `title` field **zeroed** precisely so that trick does not pass.
- **Write a summary, or any statement.** A line that does not end in `?` is not
  checked by the filter, so a claim smuggled into the body is exactly the
  unchecked prose this skill stopped asking for.
- **State currency or supersession in a question.** *"Is this the current
  decision?"* attaches the word *current* to whichever document it is written
  on — including a retired one. Currency goes in `superseded_by:`.
- **Invent facts.** A question the document does not answer will retrieve it as
  though it did.
- Include the frontmatter's own values. Fux strips the frontmatter before
  indexing precisely so a document cannot match a query for its own metadata.
- Guess at a sha, a chunk count, or a path. They come from `--plan`.

### The filter, and what it is actually checking

`fux enrich --check` runs **every question you wrote as a real search** and
refuses the file if a question does not place its own document in the **top
3**. A question that retrieves something else is not neutral — it adds terms
that pull *other* documents up.

⚠ **Scored with `title` and `ctx` zeroed.** `title`, so echoing the heading
cannot pass; `ctx`, because enrichment text is itself indexed as `ctx` and a
question would otherwise retrieve its document *through itself* — passing on
the second run and failing on the first.

⚠ **The filter is corpus-dependent.** A question that passes today can be
refused after an unrelated ingest moves the corpus statistics. `--check`
**reports**; it never rewrites your file and never deletes one.

### 🔴 Never write a value that must not be committed

An enrichment body is committed **and** indexed, so anything you put in one
travels twice: in the file every clone of this repo gets, and as a search term
inside `.fux/index/`.

**Do not copy an email address, a key, a token, an account number or a personal
identifier out of the document and into your prose.** You almost never need to
— you are describing what the document is *about*, and the identity of a
particular person or credential is never that.

`fux enrich --check` refuses a file whose body matches a rule in
`.fux/pii.toml` and names the rule. When it does, **rewrite the sentence
without the value.** Do not add a `pii.toml` rule to cover it: that would index
`[PII:email]` as vocabulary, which is worse than useless.

## 4 · Check your work

```bash
fux enrich --check docs/adr/0012_ranking.md   # the one you just wrote
fux enrich --check                            # the whole scope
```

```
enrichment: 1 scope(s) declared
  docs/adr                     41/41  ok
```

If `--check` refuses a file, it names the reason. Fix it and re-run.

**`n/total` is always the whole scope**, even under a `TARGET`. A one-document
run leaving `40/41` is the requested outcome, not a failure.

## 5 · Finishing

**A single-target run:** say which document you enriched, how many questions
you wrote, and in one line that it is now findable by words its neighbours are
not — that tilt is the point of
enrichment and it is real (see below). Then stop.

**A scope run:** one scope, then `--check`, then the next. **Do not start a
second scope until the first reports `n/n`**, because a half-finished scope
tilts ranking toward whichever half you finished. If the plan is larger than
you can complete, say which scopes you did and which you did not, and stop.
Leaving a clear boundary is fine; leaving a scope half-covered is not.

⚠ **That rule is about scope runs and only scope runs.** A single-target run
leaves its scope partial on purpose — that is what was asked for.

## 6 · Committing

The files go in git. They are part of the corpus, they are reviewed like any
other change, and a reviewer reading the diff should be able to tell whether
the context you wrote is true.

Do not commit them yourself unless asked.
