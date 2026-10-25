---
type: Guide
description: "How fux is used, told as five short stories — a developer at the terminal, a pull request, a coding agent (the primary user), a package that ships its own index (sheetpane), and search with no AI in it at all (the secondary users: people and scripts) — plus what fux is not and how to describe it. Written for the README's readers, the repo's About, blog posts and talks."
---

# How fux is used

**One idea, five ways in.** This page is the long form of the README's *Who
searches it* table. It exists so that anyone describing fux — in a README, a
blog post, a talk, a sales call — tells the same true story, and so that a
reader deciding whether to adopt it can see themselves in one of the five.

**The order of importance is not the order of the stories.** The primary user
of fux is the AI coding agent (Story 3, and Story 4 is the agent reaching into
a dependency). People at a terminal, pull requests and scripts (Stories 1, 2
and 5) are the secondary users. They matter, and they come free: nothing inside
fux is AI, so an index built for an agent can be read by anything. The stories
run in the order a team meets them — a person first, then the agent — not in
the order fux is built for.

Everything here is released in `5.1.0` unless it is marked **in build**. Nothing
is promised that the queue does not hold.

## The one idea

Google does not store the web. It builds an **index** of the web, and the index
is what you search. The pages stay where they are; the index says which words
are on which pages, and how strongly; a query is ranked against the index; the
result is a link to the page, not a copy of it.

fux applies that idea to the documents a team writes — ADRs, runbooks, specs,
wiki pages, PDFs, spreadsheets — with two changes that make it fit a repository:

1. **The index is committed to git.** It is small (statistics, not content),
   plain JSONL, and it diffs like code. Everyone who clones the repository has
   it. There is no server, no account and no key, so there is nothing to be
   down.
2. **The answer is checked against the source at answer time.** `fux answer`
   quotes the exact lines it ranked, re-reads them from the file or the URL, and
   says `current` or `stale`. If nothing in the index scores for the question,
   it says so instead of returning the nearest thing.

No model runs inside fux. The ranking is arithmetic over words (BM25F with
field weights), so the same question returns the same bytes on every machine,
today and in a year. That is what makes the rest of this page possible: a
person, a script and an agent all get the *same* answer, so they can hold each
other to it.

## Story 1 — Priya, at the terminal, week one

Priya joined on Monday. On Thursday a deploy goes wrong and she needs to know
how a rollback works here. The old way is three tabs: the wiki, a Slack search,
a teammate's DM.

```console
$ fux answer "how do I roll back a release"
# Deploying and rolling back

To roll back a bad release, run `make rollback` from the release branch.
The previous image tag is kept for 7 days.

  -- docs/deploy.md:L1-L6 (sha 6155f9c4ddf7, current)
```

Three things happened. fux ranked every indexed document for the question and
chose one. It quoted the lines, with a locator she can open. And it re-read
`docs/deploy.md` just now and confirmed those lines still say that — `current`.

A month later someone rewrites the deploy doc. The same command, unchanged,
says `stale` and names the file. Priya does not have to know the doc changed;
the answer tells her.

The question she asks next — *"kubernetes autoscaling limits"* — is not
documented anywhere in the repo. fux says `No confident matches` and gives a
`confidence: none` band. It does not hand her the deploy doc again because it
happens to mention Kubernetes.

**No AI was involved.** This is a search engine with a terminal. It is the
secondary use; the agent in Story 3 is the primary one, and it gets exactly the
same answer.

## Story 2 — The pull request

The team keeps the index current the same way it keeps everything else current:
in commits.

- `fux hooks` installs `post-commit`, `post-merge` and `post-checkout` hooks
  that re-index after the fact, and a merge driver so two branches that both
  touched the index merge cleanly.
- The pull request that adds a runbook also adds a few lines under
  `.fux/index/`. A reviewer can see them. They are not opaque: `REGISTER` holds
  one line per document, and the shards are plain JSONL.
- CI runs `fux doctor` (read-only, offline) and `fux ingest --check --json`,
  which reports what has drifted between the committed sources and the
  committed index, so a pipeline can refuse a pull request whose index is
  behind its documents.
- A script that wants file paths rather than prose runs `fux find --json` and
  pipes the result. A release checklist that must cite evidence runs `fux answer
  --receipt`, and anyone can later run `fux verify` on that receipt to reproduce
  or refuse it.

When Priya's teammate pulls on Friday, their clone answers exactly as hers did
on Thursday. There is no "the search cluster was reindexing" and no "my local
copy has different embeddings". There is one index, and it is in git.

## Story 3 — The coding agent (the primary user)

Priya's agent — Claude Code, Codex, Copilot or Kiro — reads every line of the
code and still does not know *why* the code is the way it is. That lives in the
documents. Left alone, the agent greps, guesses, or confidently paraphrases a
doc that went stale six months ago.

`fux setup` writes the agent's skills and instructions into the repository, and
`fux mcp` serves the index over MCP as three tools: `fux_search`, `fux_passage`
and `fux_related`. The instructions say, in effect:

- **Search the index before you grep.** The index ranks; grep does not.
- **Read the JSON, not the prose.** The band, the locators and the shas are
  fields.
- **An archived document is history**, not the current design. The index marks
  it; treat it accordingly.
- **If the band is `none`, say the docs are silent.** Do not fill the gap.

There is deliberately no `answer` tool over MCP. The agent writes the answer;
fux supplies the evidence and the verdict on it. That split is what lets a
reviewer ask the agent *"where did you get that?"* and get a line range back
rather than a shrug.

The framing Arpit uses for this is the Google test: if a question is asked and
the agent gets the best ten documents, its answer will be mostly right, or the
right answer will be one click away. fux is built and measured against that
test, not against how many tokens it indexed.

## Story 4 — The package that ships its own index

> **Released in 5.1.0** ([SR-PKG-INDEX](../records/0166_pkg-index.md)). The
> author's recipe is [Publish an index package](publish-an-index-package.md).
> sheetpane does not ship a segment yet, so the transcript below is the shape
> of a real run, not a capture of one.

Arpit maintains [sheetpane](https://github.com/arpitarya/sheetpane): two web
components that view, edit and review `.xlsx` and `.csv` files inside any web
page. It has docs — what the two modes do, which formats it reads, that cells
are plain text and formulas are out of scope. Today, an application that
depends on sheetpane cannot search those docs with fux unless it indexes
`node_modules/sheetpane/docs` itself, and an npm-only consumer cannot ingest at
all, because ingest is Python.

fux 5.1.0 moves that work to where it belongs:

1. **sheetpane's CI** runs `fux ingest` over its docs and `fux pack`, which
   emits a small segment — the index shards, the identifier families it was
   built with, and a manifest carrying a digest — and ships it inside the npm
   tarball. The docs themselves stay in the package; the segment is statistics.
2. **The consuming app** — say the PDF review suite that embeds sheetpane —
   pins it with one row in its committed `.fux/config/plugins.toml`:
   `kind = "index"`, the name, the version, the digest. fux refuses a segment
   whose bytes do not match the pin, the same way it refuses a decoder package
   that does not.
3. **One query searches both.** A developer on the suite asks:

   ```console
   $ fux ask "does sheetpane support formulas"
   ```

   and the ranked list holds a hit from the suite's own ADR on why sheetpane
   was chosen, and a hit whose location reads
   `pkg:sheetpane@<version>#docs/cells.md` — sheetpane's own line saying cells
   are plain text and formulas are not supported. `fux_passage` reads that
   passage **in place**, inside the installed package, after a path-containment
   check. Nothing was copied and nothing was re-ingested. *(Illustrative until
   sheetpane packs a segment: the location and the verb are what 5.1.0 does.)*

Word statistics are summed across the repo's index and every pinned segment and
ranked once, and the same query hashes the same way in Python and Node. A large
package can crowd an application's own docs out of the top of the list; `scope`
(`fux ask --scope`, and on the MCP tool) is the lever: `repo`, `packages` or
`all` (the default).

The first consumer is [codelaw](https://github.com/arpitarya/codelaw), whose
rules are Markdown files. The spike that gated the design pointed today's fux
at the published rule pack and asked twenty plain-words questions, sealed
before the first query; the right rule was in the top five for **19 of 20**,
against a pre-registered bar of 16
([run](../work/regression/2026-10-25-w298-step1-codelaw-rules/report.md)).

The 10 000-document design point counts the merged corpus — the repository plus
every pinned segment — and `fux doctor` reports the sum.

## Story 5 — Search with no AI in it at all (the secondary users)

The agent is the primary user, and the reason fux exists. People and scripts
are the second audience, and they are served by the same index without an
agent anywhere, because determinism was never about AI — it is what lets a
person, a script and an agent hold each other to one answer.

- **A local docs portal.** `fux serve` opens a page on localhost with six tabs —
  Ask, Answer, Documents, Words, Index, Identifiers. A writer uses the Words tab
  to see which terms carry weight, the Index tab to find boilerplate, duplicate
  and unreachable documents, and `fux inspect` to get the same thing as a
  report. That is a content audit, not an agent feature.
- **The editor.** `fux lsp`, and the VS Code extension that wraps it, gives
  search, link hovers, backlinks and a warning when a link points at an
  archived document.
- **Scripts.** `fux find --json` is a ranked `ls`. A release script that must
  confirm every runbook names an owner, a docs linter, a Slack bot that answers
  `/where-is` — none of them needs a model.
- **A website.** `fux llms` prints the corpus as an `llms.txt`, and `fux llms
  --full` the full text, so a published site can offer the same index its
  authors use.
- **Identifiers.** `RF 118`, `RF-118` and `RF118` are the same ticket; `fux
  identifiers` teaches the index your families so they rank as one.

A team that never installs an agent still gets a search engine over its own
documents, committed with them, that says *I don't know* when it doesn't.

## What fux is not

Three things get compared to fux. Two comparisons are fair; one is a category
error, and we stopped making it.

| | what it is for | the honest line |
|---|---|---|
| **`grep` / `rg`** | finding a string you already know, fast | the right tool when you know the string; fux is for when you know the *question*. `fux find` is the ranked version of it. |
| **Code search (symbols, call graphs)** | navigating code structure | fux has no AST and no symbols. It covers what you *wrote down*. Pair them. |
| **A vector database + RAG stack** | a chat feature *inside* a product, serving end users at runtime, with an embedding model, a store and a server | **a different job.** fux is the developer-side index of a team's own documents, committed next to them and searched by the people and tools working on that repository. It is not a runtime service and it has no model. If you build a product chatbot later, fux can be what hands it cited, verified passages; it does not replace the chatbot's own stack. |

The README used to carry a three-column table with a vector-DB column. It was
dropped on 2026-10-25 because a reader who needs a product chatbot should not
be talked out of one, and a reader who needs a committed index of their docs
was being asked to evaluate the wrong axis.

Two more things fux does not do, said plainly because a buyer will ask:

- **Semantic matching out of the box.** Ranking is lexical. "revert" does not
  match "undo" until you say so — with `--expand` for a one-off, or durably with
  `fux correct`, which writes the question onto the document that answers it.
- **Promise beyond 10 000 documents.** That is the design point and a ceiling
  on what is measured and what is claimed. Every published number was taken at
  or below it.

## How to describe it

For the repo's About line, a tweet, a slide or the first sentence of a call.

- **One line:** *A search engine for the documents your team writes. The index
  lives in git.*
- **Two lines:** *fux builds a small index of your docs — Markdown, PDFs, Office
  files, wiki pages — and commits it. Your coding agent gets ranked, cited
  evidence checked against the source, and a refusal when the docs are silent;
  anyone who clones the repo gets the same answer from a terminal, an editor or a
  script, with no server and no model.*
- **Who it is for, in order:** AI coding agents first; people and scripts
  second, at no extra cost.
- **The analogy:** Google for your own documents, except the index is checked
  into the repository and the answer tells you if the page changed.
- **Pronounced "fox".**

**Claims that are always safe**, because each has a pre-registered bar and a
filed run (see [`work/regression/`](../work/regression/README.md)):

- ranked, byte-identical results on every machine, Python and Node alike;
- a current / stale verdict on every quoted answer, and a refusal when the docs
  are silent;
- zero dependencies, nothing hosted, offline by default, PII redacted before
  commit;
- the numbers in the README's *Measured, not assumed* section, exactly as
  written there.

**Claims never to make:** semantic search, code search, anything above
10 000 documents, and anything in this page marked *in build* described as
shipped.

## Where to go next

- [`README.md`](../README.md) — the front door, with the quickstart.
- [Publish an index package](publish-an-index-package.md) — the author's
  recipe for Story 4.
- [The paper](paper/the-fux-index-paper.md) — the architecture of record.
- [`work/OPEN-WORK.md`](../work/OPEN-WORK.md) — what is being built, with its
  state.
