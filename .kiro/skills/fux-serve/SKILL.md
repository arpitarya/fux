---
name: fux-serve
description: Open the Fux ask explorer with `fux serve` — a local page that takes a question and shows the ranked documents, which word earned which part of each score, which links moved a result, the confidence band, and one lever per finding. Use for "why did this document rank first", "show me why fux returned these", "open the fux UI", "which word is carrying this result", or when somebody wants to SEE a ranking rather than read JSON. Read-only, localhost only; it proposes levers and applies none.
---

# The ask explorer — `fux serve`

`fux doctor` says whether the machine is set up. `fux inspect` says whether the
index is any good. **`fux serve` says why *this question* got *those ten
documents*.**

Resolve the `fux` command first — see the `fux-usage` skill (`fux` → `uv run fux` → `./.venv/bin/fux`, on Windows `.venv\Scripts\fux.exe` → `python -m fux`).

## 1 · When this is the right verb

| the ask | what to do |
|---|---|
| "why did this rank first?" | `fux serve`, then click the row — or `fux ask "…" --why` for the same facts as text |
| "show me the search, don't tell me" | `fux serve`, hand over the URL |
| "which word is carrying this result?" | the score-by-word bar in the row detail |
| "why is this document here at all — it has none of my words?" | the **reached by link, not by words** panel |
| "is the index any good?" | not this verb — `fux inspect` (`fux-inspect`) |
| "is the repo set up?" | not this verb — `fux doctor` (`fux-index`) |
| "give me the answer with line numbers" | not this verb — `fux answer` (`fux-answer`) |

## 2 · Running it

```
fux serve                 # http://127.0.0.1:7337
fux serve --port 8080
fux serve --open          # and launch a browser
```

It **does not return** — Ctrl-C stops it. In a non-interactive session, start it
in the background or simply hand the person the command; do not block a turn on
a server that never exits.

🔴 **It binds `127.0.0.1` and there is no `--host`.** That is a contract, not a
default: the page shows the corpus's vocabulary, its passages, and the questions
somebody typed. If asked to expose it on a network, say that fux refuses and
why — do not reach for a tunnel or a proxy to get around it.

## 3 · What the page is, and what it is not

**It is a renderer.** `GET /ask?q=…` returns the byte-identical stdout of
`fux ask --json --why --band`; the page draws it. **Nothing in the page computes
a score, a band or a rank.** So:

- every number on it is fux's own, and you can quote it;
- if a number you want is not on the page, the fix is to add it to `--why`,
  never to compute it in the browser or in your head;
- a page that started computing would be a second ranker, and two rankers can
  disagree while both look correct.

The routes, if you need them directly: `/` (the page), `/ask?q=…&top=N`,
`/graph?seed=…`, `/health`. **No route writes anything**, and `POST` is a 405.

## 4 · Reading a row

| what you see | what it means |
|---|---|
| the score | **BM25F × proximity uplift × archived multiplier** — the page prints all three factors |
| the stacked bar | one segment per query term, sized by that term's `contribution` |
| a red dashed pill | a query word this document **does not contain** |
| `↑ #3 → #1 via graph` | the walk moved it; the words alone did not put it there |
| `title match`, in gold | the match is in the title field — the strongest cheap signal |
| `archived` | see the `fux-archived-results` skill **before** using it in an answer |

**The confidence ring is the thing to read first.** If `answerable` is false —
which since 2026-09-22 means `band: none`, an empty result set — fux is saying
there is nothing here to build an answer from, and the page renders that as a
correct outcome, not an error. **Do not talk a person past an abstention.**

⚠ **A `weak` ring is NOT an abstention.** It says the ranking could not
separate the top two, and fux answers anyway: the ring is there so a person
opens both documents instead of trusting the order. Reading it as a refusal
re-introduces, by hand, the behaviour a 2 992-question measurement retired.

## 5 · Levers — propose, never apply

Every result carries action cards, each with a lever tag naming a command or a
config key: `fux correct --pin`, `fux enrich`, `[index] stopwords`, `title`,
`[graph] ask_boost`, `supersedes`, `archived=`.

🔴 **Never run a lever the page printed unless you were asked to.** Same rule as
`fux-inspect`. Each one changes what the index holds or how it ranks, for
everybody on the repository — a stopword removes a word from every query, a
`--pin` writes a committed file, an `archived=` changes what surfaces. The page
proposes; a person decides.

⚠ **Two of the thresholds behind those cards are provisional** — the boilerplate
line and the near-tie width — and the page says so in its footer. They are tuned
to no corpus. Quote a lever as *a thing worth looking at*, never as a measured
finding.

## 6 · What it writes

**Nothing.** `fux serve` keeps no log of its own, and no route writes a file.
The later rungs that emit a page to disk put it under `.fux/runtime/trace/`,
which is gitignored and regenerable — those pages quote passages, so they are
never committed.

Related skills: fux-usage, fux-search, fux-answer, fux-inspect, fux-graph, fux-correct, fux-archived-results.
