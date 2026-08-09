---
type: Example
title: Debug & observability — worked failures, diagnosis, fixes
description: The [debug] config surface, the dbg()/timer() emitter contract, fux doctor's seven groups, and fux why's verdict line — worked against real failures. Normative for docs/handoff/0005.
timestamp: 2026-07-22T00:00:00Z
---

# Debug & observability — worked examples

*Companion to [CLI.md](CLI.md) (command I/O) and [TOML.md](TOML.md) (the
`[debug]` config block). This doc answers the five questions debug exists
for — worked against real failures, not abstractly.*

## The five questions

1. **Why is my document not in the corpus?** → `fux doctor` (config group) or
   `fux why --doc <path>` (corpus presence).
2. **Why did my query not return it?** → `fux why "<query>" --doc <path>`.
3. **Why is the answer wrong or thin?** → check `fidelity` in the result, then
   `fux ingest --advanced <file>`.
4. **Why is my install/corpus in a bad state?** → `fux doctor`.
5. **Why is it slow / big?** → `--debug=trace timing=true` (per-stage
   `elapsed_ms`) and `fux doctor`'s corpus group (per-plane sizes).

## `[debug]` — the config surface

```toml
[debug]
level      = "off"       # off | info | debug | trace
categories = ["*"]       # subset of: config walk convert chunk index state
                          #   lock query lexical dense graph answer hooks web
output     = "stderr"    # "stderr" or a file path (e.g. ".fux/debug.log")
timing     = false       # per-stage wall time (non-deterministic — off by default)
redact     = true        # log ids/paths/counts/scores; never document content
max_bytes  = 5000000     # cap the log file; truncate-with-notice, never silently
```

**Precedence** for `level` only: `--debug[=LEVEL]` (flag) > `FUX_DEBUG=<level|1>`
(env) > `[debug] level` (toml) > `off`. `FUX_DEBUG=1` still means `debug`, for
back-compat with the pre-v0.24 hook contract. Every other key is toml-only.

**The hard guarantee: debug never touches stdout, and never changes
behaviour.** Every existing golden passes byte-identical with `--debug=trace`
active — that's the gate proven in `tests_e2e/test_determinism.py`. Debug
output is stderr (or a file) only.

## Worked failure 1 — "my document isn't showing up"

```
$ fux why "install the widget" --doc docs/onboarding.md
docs/onboarding.md
  in corpus: False  (on disk but outside every configured [sources] entry
             (excluded, or no matching glob) — check fux.toml)

verdict: not in corpus: on disk but outside every configured [sources] entry
         (excluded, or no matching glob) — check fux.toml
```

**Diagnosis:** the file exists but no `[sources]` entry's directory (or glob)
reaches it. **Fix:** add its directory to `[sources]` in `fux.toml`, or move
the file under an existing one, then `fux ingest`.

## Worked failure 2 — "ingest skipped a file silently"

```
$ fux why "anything" --doc notes/report.pdf
notes/report.pdf
  in corpus: False  (requires the markitdown extra (pip install 'fux-engine[ingest]'))

verdict: not in corpus: requires the markitdown extra (pip install 'fux-engine[ingest]')
```

**Diagnosis:** office/PDF conversion needs the opt-in extra. **Fix:**
`pip install 'fux-engine[ingest]'` and re-run `fux ingest` — or check
`fux ingest --list-skipped` for every skip in one place.

## Worked failure 3 — "a whole source folder returns nothing"

The single most common silent misconfig: a `[sources]` glob that resolves to
zero files. Nothing in ingest itself warns about this — `fux doctor` does:

```
$ fux doctor
…
[✗] config
  FAIL  [sources] docs = 'notes/private': directory exists but matches 0 files
        why: the #1 silent misconfig — this entry contributes nothing, and
             `fux ingest` will not warn you
        fix: check fux.toml — did you mean a different directory for
             [sources] docs?
```

**Fix:** correct the path in `fux.toml`, then `fux ingest`.

## Worked failure 4 — "a document ranks, but too low to see"

```
$ fux why "install the widget" --doc "docs/unicode-café.md" --top 1
…
  lexical: rank=6 score=0.4297 in_pool=True (pool=200)
  dense: similarity=0.0084 in_prefilter=True hamming=126 (width=500)
  graph: reached=True as=seed via=None edge=None

verdict: not returned at --top 1: rank 6 overall (raise --top to 6 to see it)
```

**Diagnosis:** it *did* rank — just below the requested `--top`. **Fix:**
`fux ask "install the widget" --top 6` (or wider), or refine the query so this
document scores higher.

## Worked failure 5 — the full negative case

```
verdict: not returned: no lexical overlap, no dense candidate (cosine 0.19,
not among the 500 nearest FuxVec codes), no edge from any seed
```

**Diagnosis:** the query and the document share no terms, the dense pass put
it outside the FuxVec prefilter, and no graph edge connects it to any seed
document. **This is the honest answer** — the corpus genuinely doesn't
connect this query to this document. **Fix:** broaden the question, or check
whether the document actually covers the topic at all (`fux cat <doc>`).

## Worked failure 6 — "the corpus feels stale / a fresh clone answers wrong"

```
$ fux doctor
…
[✗] consistency
  FAIL  drift (source ↔ lock): 1 drifted
        why: a source changed since the last ingest; queries answer from stale text
        fix: fux ingest
```

**Fix:** `fux ingest` (drift), `fux ingest --web` (stale web pages past
`max_age_days`), or `fux ingest` again for state↔lock desync (a fresh clone
whose committed state plane disagrees with `fux.lock`).

## Worked failure 7 — "a returned passage looks thin or garbled"

```
$ fux ask "SLA terms" --json --top 1
{"results": [{"path": "notes/vendor.pdf.md", "fidelity": "inferred", "text": "…garbled…"}]}
```

**Diagnosis:** `fidelity: inferred` means the fast default conversion pass, not
the layout-aware one. **Fix:** `fux ingest --advanced notes/vendor.pdf` (needs
`docling`/`tesseract` — `fux doctor`'s capabilities group shows what's
installed and the exact command to add what's missing), then re-ask.

## Reading a trace

```
$ fux --debug=trace ask "widgets" --json 2>trace.log 1>/dev/null
$ cat trace.log
[query] info: retrieve seed=text k=5 lexical_only=False
[lexical] debug: bm25f candidates pool=200 candidates=1
[dense] debug: candidate similarities scored scored=1 missing_vectors=False
[dense] debug: fuxvec prefilter codes=1 width=500 scanned=1 rescued=1
[query] info: hybrid fusion rrf_k=60 results=1 dense_global_rescues=1
[graph] debug: edges collected seeds=1 hops=1 edges=0
[graph] debug: ppr expansion candidates=0 kept=0
[query] info: retrieve complete engine=hybrid passages=1 seeds=1 nodes=1 edges=0
```

Every line is `[category] level: message key=value …` — stable field order, no
wall-clock unless `timing = true`, so two `trace` runs on the same corpus
produce byte-identical stderr (this is what makes debug output diffable, and
is asserted by a determinism test). Categories map to pipeline stages: `walk`
· `convert` · `chunk` · `index` · `state` · `lock` · `query` · `lexical` ·
`dense` · `graph` · `answer` · `hooks` · `web`.

## `fux doctor` — the seven groups

See [CLI.md](CLI.md#fux-doctor--diagnose-the-whole-installcorpus) for full
worked output. One line each: **environment** (version, bundled model sha) ·
**capabilities** (markitdown/docling/tesseract/Chrome/websocket-client — never
fails health) · **config** (fux.toml + per-source-entry file counts) ·
**corpus** (cache/index/state/lock presence + sizes) · **consistency**
(drift/stale/desync) · **agent surface** (AGENTS.md/skills/hooks) ·
**self-test** (ingests a scratch canary doc, queries it, proves the citation
resolves — the whole path, end to end).

## `fux-debug` — the skill

`fux setup --skills` writes `.claude/skills/fux-debug/SKILL.md`, and the
`fux-query`/`fux-ingest` skills each carry a one-line escalation pointer to it.
See [SKILLS.md](SKILLS.md#skill-3--fux-debug) for the full content — its
workflow is exactly the cheapest-first order above: `doctor` → `ingest
--check` → `why` → `--advanced` → `--debug=debug` → **report, don't guess**.

## Related

[CLI.md](CLI.md) (`fux doctor`/`fux why` full I/O) ·
[TOML.md](TOML.md) (`[debug]` reference) ·
[SKILLS.md](SKILLS.md) (`fux-debug` skill) ·
[ADR 0012](../adr/0012-debug-observability.md) (the decisions behind this
surface).

## Maintenance

Rows in [`DOC-REGISTRY.md`](../DOC-REGISTRY.md). Trigger: any change to
`[debug]` semantics, `fux doctor`'s groups/checks, or `fux why`'s evidence
fields/verdict wording.
