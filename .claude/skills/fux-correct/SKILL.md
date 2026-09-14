---
name: fux-correct
description: Write a human-authored question onto the document that answers it with `fux correct` — the marker, `--pin` and its suspension, `--reaffirm`, the eval file, and what `fux enrich --check` reports. Use ONLY when explicitly asked to correct, pin or reaffirm a result ("fux served the wrong doc, fix it", "pin this question to that page", "reaffirm the pin"). It writes COMMITTED files and changes what the index holds, so never run it because you noticed a bad result — propose it.
---

# Correcting a wrong answer — `fux correct`

`fux correct "<question>" <doc>` writes **one question a person typed** onto the
document that answers it. It lands in the same file `fux enrich` writes and is
indexed as the same `ctx` field — same file, same field, **different author**.

🔴 **Never run this because you noticed a bad result.** It writes files that are
committed and reviewed, and it records a claim under somebody's name. When you
find that fux served the wrong document and you know the right one, **propose
the command in your reply and stop** — §1.

Resolve the `fux` command first — see the `fux-usage` skill (`fux` → `uv run fux` → `./.venv/bin/fux`, on Windows `.venv\Scripts\fux.exe` → `python -m fux`).

## 1 · What to do when fux served the wrong document

**Say what happened, then offer the command. Do not run it.**

> I asked `fux ask "how do I roll back a release"` and it returned
> `docs/adr-storage.md`; the answer is in `docs/runbook-rollback.md`, which the
> query's words never reach. If you want that fixed durably:
>
>     fux correct "how do I roll back a release" docs/runbook-rollback.md
>
> That appends the question to the document's enrichment file and commits it, so
> it needs your review.

**Three alternatives to offer first, in this order** — the first that applies is
usually better than a correction:

| the real problem | the fix |
|---|---|
| the document does not use the words people search with, and **you can edit it** | **edit the document.** A correction is for a document you do not own or must not change |
| the served document is **retired** | `supersedes:` on the successor, or `archived=true` on its `.fux/sources/dirs` line — corpus-wide, not per query |
| the corpus genuinely does not answer it | say so. Neither a correction nor a pin makes an answer exist |

## 2 · The verb

| you were asked to | run |
|---|---|
| record the question people actually ask | `fux correct "<question>" <doc>` |
| also force this document to #1 for that exact question | `fux correct "<question>" <doc> --pin` |
| release a pin the document outgrew | `fux correct --reaffirm "<question>" <doc>` |
| keep the correction, drop the pin | `fux correct "<question>" <doc> --no-pin` |
| show every correction and any suspension | `fux correct --list --json` |

**The question is the searcher's words, never the title's.** A correction that
echoes the heading corrects nothing — the document already matched on those. The
question that failed is the one worth writing, verbatim if you have it.

**It does not take effect until `fux ingest` runs.** The verb prints that as its
last line; relay it.

## 3 · What it refuses, and what to do instead

| refusal | what it means |
|---|---|
| *reads as a negative correction* | you wrote *don't serve X*. That is a supersession or an archive decision and it is corpus-wide. Correct the RIGHT document instead |
| *matches `.fux/pii.toml` rule(s)* | the question contains a value the index redacts. **Rewrite it without the value** — a redacted question indexes `[PII:...]` and retrieves nothing |
| *is not in the index* | paste the `loc` exactly as `fux find` printed it |
| *that pin is SUSPENDED* | the document changed after the pin was made. Read it, then `--reaffirm` if it still answers, or `--no-pin` |

**A refused command writes nothing.** If you see an error, no file changed.

## 4 · `--pin` — rare, exact, and brittle on purpose

A pin forces one document to #1 for **one question**, matched on the analyzed
form (so capitalisation and plurals do not defeat it).

- 🔴 **Ask before adding one.** The body line already generalises across
  phrasings; a pin fixes exactly one. Offer `--pin` only when the human asked
  for that specific question to be right, every time.
- **It is applied AFTER the ranking**, so `--why` still shows the real ranking
  with the pin on top of it. `"pinned": true` in `--json`, `[pinned]` in text,
  and a `note:` on stderr.
- **A pinned document the ranking never returned is inserted with
  `"score": 0.0`** — the ranking never scored it. Do not read that as a bad
  match; read `pinned`.
- **A pin whose document changed is SUSPENDED and silently stops applying.**
  `fux doctor`'s `correction pins` row names every one. Only a person can say
  whether it still holds — never `--reaffirm` on your own initiative.
- **The vocabulary effect never suspends.** The question is still the question
  somebody asks.

## 5 · Reading `fux enrich --check` after a correction

| line | what it means |
|---|---|
| `reported (human): … does not retrieve its document` | the correction is **not biting**. Check that `fux ingest` has run. If it has, the words may be too close to what the document already says — or too far |
| `refused: …` | a **model** line failed, not a human one. That is `fux-enrich`'s business |

🔴 **A human line is REPORTED, never refused**, and the file stays indexed. A
correction is by definition a question that failed retrieval — that is what it
is for. **Every human line is checked whatever its punctuation**, so a
correction with no `?` is checked too.

## 6 · What lands on disk

| file | committed? | what it holds |
|---|---|---|
| `.fux/enrich/<source sha>.md` | **yes** | the question as a body line, and `corrections: N` in the frontmatter saying the last N lines are human |
| `.fux/eval/corrections.tsv` | **yes** | one row per correction — the durable record. Sorted, so a review diff does not depend on filing order |

- **The marker is in the frontmatter, which is never indexed; the text is in the
  body, which is.** So the marker adds no vocabulary.
- ⚠ **A regenerating `fux enrich` rewrites the whole file.** The eval file is
  what survives that, and `--check` names any correction whose line has gone
  missing. **When you regenerate enrichment for a document, carry its human
  lines forward** — read them out of the file before you overwrite it.
- **No date is written.** `generated:` comes from the document's own committed
  timestamp, so the bytes do not depend on when the command ran.

## 7 · Reviewing a correction in a PR

- **Is it a question somebody would type?** Not a summary, not the title.
- **Does the named document actually answer it?** A correction that points at
  the wrong document is worse than none — it adds vocabulary that pulls that
  document up for a question it cannot answer.
- **Is `--pin` justified?** A pin is one phrasing. Ask why the body line is not
  enough.
- **Is anything sensitive in the text?** It is committed and indexed both.

## Don't

- **Don't run `fux correct` unasked.** Propose it. This is the same rule
  `fux-enrich`, `fux-decoder` and `fux-fetcher` carry.
- **Don't add `--pin` on your own initiative**, and don't `--reaffirm` one.
- **Don't write a correction to make a demo work** — it is committed, and
  somebody will review it.
- **Don't echo the document's title** as the question.
- **Don't correct a retired document** — `supersedes` / `archived=` is the fix.
- **Don't claim it took effect before `fux ingest` has run.**
- **Don't read `"score": 0.0` on a pinned row as a bad match** — the ranking
  never scored it.
- **Don't edit `.fux/eval/corrections.tsv` by hand.** It has no escaping, and
  `fux correct` is what keeps it sorted and consistent with the enrichment file.

Related skills: fux-usage, fux-search, fux-answer, fux-enrich, fux-sources, fux-index, fux-pii, fux-archived-results.
