# Fux

> **Your documents already know the answer. Fux lets you ask them — offline, deterministic, `$0`, cited.**

[![PyPI](https://img.shields.io/pypi/v/fux-engine.svg)](https://pypi.org/project/fux-engine/)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![Dependencies](https://img.shields.io/badge/runtime%20deps-0-brightgreen.svg)](#the-0-guarantee)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Fux is a portable, agent-aware knowledge engine. `fux ingest` turns the folders you
point it at into a git-versioned Markdown corpus with provenance; `fux ask` answers
natural-language questions over it with ranked, `file:line`-cited passages — no
network, no API keys, no external model, the same answer every time.

**Pronounced "fox."** · Python ≥ 3.11 · stdlib only · MIT

## The story

You move into an old house. Down in the basement, the previous owner painted one
pipe bright red. There *is* a note explaining why — it's in a binder, in a box, in
one of forty folders the last owner left behind. You'll find it about a week after
the basement floods.

That's most project knowledge. The answer to "why did we do it this way?" *is*
written down — in a decision doc, a runbook, a PDF someone exported, a page twelve
levels deep in a wiki. Being written down isn't the problem. **Being findable at
the moment of confusion is** — and grep only works if you already know the magic
word. (Hand the folders to an AI assistant and it has the same problem, faster: it
guesses instead of digging.)

**Fux is the index to every note in the house.** Point it at your folders once;
ask in plain English; get back the actual passages — quoted verbatim, scored, cited
to the exact file and line — so you (or your agent) verify instead of trusting. And
because the corpus lives in git, what you knew and when you knew it has history,
like everything else that matters.

## See it

```bash
$ fux ask "why did we pick a composite index for trades?"
```

```
notes/anton/decisions/db-indexing.md:12  (score 7.412)
  ## 2026-05 — Indexing the trades table
  We chose a composite index on (symbol, ts) over per-column indexes because
  every hot query filters by symbol then range-scans time. Rejected a covering
  index — write amplification on the tick ingest path was too high.

notes/anton/schema/trades.md:5  (score 3.121)
  trades(symbol, ts, price, qty, status) — composite PK on (symbol, ts).

2 passages · corpus 50 docs · 12ms
```

The evidence, not a summary — with the `file:line` to jump to. Want it stitched
into prose? `fux answer` builds one from the source's own sentences, every clause
cited, nothing generated:

```
$ fux answer "why did we pick a composite index for trades?"

We chose a composite index on (symbol, ts) over per-column indexes because every
hot query filters by symbol then range-scans time. [1] Rejected a covering index —
write amplification on the tick ingest path was too high. [2]

Sources:
  [1] notes/anton/decisions/db-indexing.md:12
  [2] notes/anton/decisions/db-indexing.md:14
```

## Quickstart

```bash
pip install fux-engine         # zero runtime deps; ~7 MB wheel incl. the model

cd your-project
fux setup                      # wizard → fux.toml (every prompt has a flag; -y for defaults)
fux ingest                     # folders → .fux/ corpus + manifest + index
fux ask "why did we pick X?"   # ranked, cited passages
fux find "deploy runbook"      # which files
fux answer "how do rollbacks work?"   # extractive, cited answer
```

Optional Office/PDF converters (never on the query path):
`pip install 'fux-engine[ingest]'`. Ten-minute real-project walkthrough:
[DOGFOOD.md](DOGFOOD.md) · worked input/output for every command:
[docs/cli-examples.md](docs/cli-examples.md).

## Explain it like I'm five

Your notes are a giant pile of paper. Somewhere in the pile is the page that
answers your question — you just can't find it, so you ask the smart kid instead,
and the smart kid *makes something up*. Fux reads the whole pile once, remembers
where everything is, and when you ask, it holds up the actual page and points at
the actual sentence. It never makes anything up, it works with no internet, and it
answers the same way every single time.

## Why it's different

Properties, not features:

- **Deterministic.** Sorted walks, stable serialization, no wall-clock output, no
  model in the maintenance path. Same sources → byte-identical corpus and index;
  same question → same answer. Proven by golden-file tests on every commit.
- **Cited or it didn't happen.** Every passage carries `file:line`; `answer` is
  extractive — verbatim source sentences, ordered and cited — never generative, so
  it cannot hallucinate.
- **Hybrid retrieval, still offline.** BM25F field-weighted lexical search fused
  (RRF) with a **bundled 7.9 MB static-embedding model** inferred in pure stdlib —
  semantic recall for paraphrased questions with zero downloads, zero services.
  `--lexical-only` preserves the pure-BM25F path byte-for-byte. An eval harness
  gates every retrieval change.
- **`$0` and zero-dependency.** Stdlib-only runtime — the frontmatter parser, the
  WebSocket client, and the embedding inference are hand-rolled on purpose.
  Auditable line by line, portable as a tarball, runs air-gapped.
- **Agent-native.** `--json` everywhere, `--explain` shows *why* every result
  ranked (per-term field hits, dense rank, RRF contribution), and
  `fux setup --agents --skills --hooks` teaches Claude Code, Copilot, and Kiro to
  query the corpus before guessing — via AGENTS.md, the open SKILL.md standard,
  and fail-open hooks.
- **A corpus, not a disposable index.** `.fux/cache/` + manifest are designed to be
  *committed*: knowledge changes become reviewable diffs, and "what did we know in
  March?" is a `git checkout` away.

## How it works

```
sources (fux.toml) ──ingest──▶ .fux/cache/    OKF Markdown corpus + provenance   ← commit this
                               .fux/manifest.jsonl   sha-keyed ground truth      ← commit this
                               .fux/index/    BM25F postings + chunk vectors     ← derived; regenerable
ask/find/answer ◀── BM25F candidates ⊕ dense ranks → RRF fusion → cited passages
```

Ingest is **two-tier by design**: the fast *inferred* pass handles everything by
default (markdown/txt/code natively, JSON flattened, YAML fenced, images as
metadata stubs, Office/PDF via the extra); the *advanced* pass —
`fux ingest --advanced report.pdf` — re-converts exactly the files that deserve it
with Docling layout extraction or Tesseract OCR, and records the upgrade in each
file's `fidelity` frontmatter so readers (human or agent) know what they're
looking at.

The web is a source too, behind an explicit fence: `fux ingest --web` crawls
`[sources.web]` (robots.txt obeyed, depth/budget/domain caps, attachments
converted, full `url`/`parent`/`depth` provenance) — and `render = "cdp"` drives
your own headless Chrome over a hand-rolled RFC 6455 WebSocket client for
JS-rendered pages. **Network never touches the query path** — an import-fence test
enforces it.

<details>
<summary><strong>The full command surface</strong></summary>

```bash
fux setup                        # wizard → fux.toml; every prompt has a flag; -y
fux setup --agents --skills --hooks   # AGENTS.md + pointers, skills, agent hooks
fux ingest                       # convert + chunk + index (incremental by sha)
fux ingest --check [--strict]    # drift report (sha mismatch/new/missing); --strict exits 2
fux ingest --list-inferred       # upgrade candidates (inferred fidelity)
fux ingest --list-skipped        # what didn't ingest, and why
fux ingest --advanced <file>     # one file → Docling/Tesseract → fidelity: advanced
fux ingest --web                 # fenced crawl of [sources.web] (+ CDP rendering)
fux ask "<question>"             # ranked cited passages   (--json --explain --top -C)
fux find "<topic>"               # ranked files
fux answer "<question>"          # extractive cited answer (--answer-max)
fux ask … --lexical-only         # pure BM25F, byte-identical to v1
fux hook prompt-submit|session-end    # fail-open agent-hook entrypoints
```
</details>

## The `$0` guarantee

No maintenance or query path ever calls a model or the network. The bundled
semantic model is a static token→vector table shipped *inside* the wheel — looked
up, mean-pooled, and dot-producted in pure stdlib (int8, exact). The only network
code in the product lives inside the explicit `fux ingest --web` fence, and the
only model-adjacent tooling (distillation) runs at *development* time in
`tools/distill/`, never at runtime.

**Honest limits.** Fux retrieves and quotes; it does not write prose or reason
across documents — `answer` selects the source's own sentences, which is the
point, but means no synthesis beyond what's written. The bundled model is
English-biased (other languages degrade gracefully toward lexical). And retrieval
quality is measured, not promised: the committed eval harness gates changes, and
the current hybrid ships on a tie-with-rescues over lexical — the honest numbers
live in [ADR 0006](docs/adr/).

## The name

Named after *Johann Joseph Fux*, author of *Gradus ad Parnassum* (1725) — the
counterpoint treatise every composer learned the rules from. A tool built so the
reasons survive the people, named for the man who wrote the rulebook. The long-term
Fux vision — version-controlled **rules bound to code, checked deterministically**
— is on hold, deliberately, until this query engine has earned its keep in daily
use; the design of record is [docs/fux-plan.md](docs/fux-plan.md).

## Status

**v0.22.x — the full staged engine is shipped**: v1 query CLI, v1.1 web/CDP/
advanced ingest, v2 bundled-model hybrid — 170+ unit tests, 29 e2e goldens, eval
gate green. Decisions live in [docs/compare/](docs/compare/) and
[docs/adr/](docs/adr/); the docs are an OKF v0.1 bundle rooted at
[docs/index.md](docs/index.md); the old build is archived under
[`archive/`](archive/). Now dogfooding ([DOGFOOD.md](DOGFOOD.md)).

---

If the binder-in-a-box problem is real in your project, try Fux on one folder —
`pip install fux-engine`.

## License

MIT — see [LICENSE](LICENSE).
