---
type: Handoff
title: Debug & observability — [debug] config, fux doctor, fux why, debug skill
description: Make every Fux stage inspectable without a debugger — a toml-exposed debug surface, a whole-install diagnostic, negative-result explanation, and a skill so agents can self-diagnose.
status: ready
blocked_by: none (v0.23.x shipped)
timestamp: 2026-07-22T00:00:00Z
---

# Handoff 0005 — Debug & observability

## Context

Fux is deterministic and cited, which makes it *auditable* — but not yet
*diagnosable*. Today the only debug surface is `FUX_DEBUG=1` inside
`src/fux/hooks.py` (fail-open tracing). Everything else — ingest decisions,
chunk boundaries, index reuse, candidate selection, dense scan, graph
expansion, answer sentence choice, state/lock consistency — is opaque.

**Arpit's requirements (2026-07-22):** a debugging plan covering *everything*;
the level **exposed as a value in `fux.toml`**; and it must **work with skills**
so an agent can diagnose without a human reading logs.

**Why this matters at the enterprise litmus:** at 10⁵–10⁶ documents behind SSO
on a Windows fleet, "it returned nothing and I don't know why" is the support
burden. A tool that can explain its own behaviour offline is the difference
between a ticket and a self-serve fix.

## The five questions debug must answer

Every feature below exists to answer one of these, and nothing else:

1. **Why is my document not in the corpus?** (walk/skip/convert/extras)
2. **Why did my query not return it?** (candidates, scores, dense, graph)
3. **Why is the answer wrong or thin?** (chunking, fidelity, sentence choice)
4. **Why is my install/corpus in a bad state?** (config, drift, state-desync)
5. **Why is it slow / big?** (per-stage timing, per-plane sizes)

## Definition of done

1. `[debug]` section in `fux.toml`, parsed like every other section, with
   precedence **flag > env > toml > off**.
2. Debug output **never touches stdout** — stderr or a file only. All existing
   goldens pass unchanged with debug at every level (this is the hard gate).
3. `fux doctor` diagnoses the whole install and exits 0/1; `--json` for agents.
4. `fux why "<query>" --doc <path>` explains a document's fate for that query,
   **including when it does not appear** (the negative case).
5. A third skill, `fux-debug`, ships with `fux setup --skills`, and the two
   existing skills gain a one-line escalation pointer to it.
6. Docs: `docs/example/DEBUG.md` (worked failures + fixes), TOML/CLI/SKILLS/
   SETUP updated, GLOSSARY terms, registry rows.
7. Both suites green + a new determinism test proving debug output does not
   alter stdout at any level. ADR 0012. Version **0.24.0**.

## A. `[debug]` in fux.toml

Add `DebugParams` to `src/fux/config.py`, following the existing dataclass
pattern (`IndexParams`, `GraphParams`, …):

```toml
[debug]
level      = "off"       # off | info | debug | trace
categories = ["*"]       # subset of the stage names below, or "*"
output     = "stderr"    # "stderr" | a file path (e.g. ".fux/debug.log")
timing     = false       # per-stage wall time (non-deterministic — off the stdout path)
redact     = true        # log ids/paths/counts, never document content
max_bytes  = 5000000     # cap the log file; truncate-with-notice, never silently
```

**Categories = pipeline stages**, so a trace reads as a story:

`config` · `walk` · `convert` · `chunk` · `index` · `state` · `lock` ·
`query` · `lexical` · `dense` · `graph` · `answer` · `hooks` · `web`

**Levels:**

| level | emits |
|-------|-------|
| `off` | nothing (today's behaviour) |
| `info` | one line per stage: counts, decisions, durations if `timing` |
| `debug` | per-document decisions (skip reasons, converter chosen, reuse hits) |
| `trace` | per-chunk / per-term detail (postings, candidate lists, scores) |

**Precedence:** `--debug[=LEVEL]` (global flag) > `FUX_DEBUG=<level|1>` >
`[debug] level` > `off`. `FUX_DEBUG=1` must keep meaning `debug` for
back-compat with the existing hook contract.

## B. The emitter — `src/fux/debug.py`

Small, stdlib-only, importable everywhere without cycles:

```python
dbg(category, level, msg, **fields)      # structured; fields become key=value
timer(category, label)                   # context manager; no-ops unless timing
is_enabled(category, level) -> bool      # guard expensive f-strings at call sites
```

Rules, all testable:

- **Never writes to stdout.** Unit-tested by capturing stdout during a
  `trace`-level run and asserting it is byte-identical to an `off` run.
- **Lazy**: `is_enabled()` guards any formatting that costs anything, so
  `off` has no measurable overhead (assert in the perf test).
- **Redaction on by default**: log `path`, `chunk_id`, counts, scores — never
  document text. `redact = false` is opt-in and warns once.
- **Deterministic content**: no timestamps unless `timing`; stable field order.
  A `--debug=trace` run twice on the same corpus produces identical stderr
  (test it — this is what makes debug output diffable).

## C. `fux doctor` — the "everything" check

One command that answers "is this install/corpus sane?", grouped and
exit-coded (0 healthy, 1 problems found). `--json` mirrors the structure.

| Group | Checks |
|-------|--------|
| **environment** | fux version, Python version, install path, bundled model present + sha match, wheel data files intact |
| **capabilities** | which optional paths are available: markitdown, docling, tesseract binary, Chrome for CDP, `websocket-client` fallback — each with the exact install command when missing |
| **config** | fux.toml found at *absolute path*; every source entry resolved to a file count; **entries matching zero files flagged loudly** (the #1 cause of "no results"); excludes applied |
| **corpus** | cache/index/state/lock present; doc/chunk counts; index format + version; per-plane sizes |
| **consistency** | three-way state ↔ lock ↔ sources; drift/stale/desync counts; orphaned cache entries |
| **agent surface** | AGENTS.md, skills, hooks present and where; whether hooks are wired into the host tool's settings |
| **self-test** | ingest a temp doc into a scratch dir, query it, assert the citation resolves — proves the whole path end to end |

Each failing check prints **what is wrong, why it matters, and the exact fix
command**. That last column is the difference between a diagnostic and a log.

## D. `fux why` — negative-result explanation

The sharpest tool, because `--explain` only explains results that *appeared*:

```
fux why "<query>" --doc docs/adr/0007.md        # why this doc did/didn't rank
fux why "<query>" --doc <path> --json
```

Walk the pipeline for that one document and report the first place it fell out:

1. **In the corpus?** in lock / in cache / in index — if not, the skip reason
   from ingest (binary, size cap, missing extra, excluded by glob).
2. **Chunks** — how many, their heading paths, which contain query terms.
3. **Lexical** — per-term df/idf and per-field tf; the BM25F score it *would*
   have scored; whether it entered the candidate pool and at what rank.
4. **Dense** — its code's Hamming distance, whether it made the prefilter, its
   exact cosine, its `dense_global` rank.
5. **Graph** — whether expansion reached it, from which seed, via which edge.
6. **Verdict** — one sentence: *"not returned: rank 47 lexical, no dense
   candidate (cosine 0.19 < pool cut 0.31), no edge from any seed."*

That verdict line is the whole feature. Everything above it is evidence.

## E. Skills integration (Arpit's requirement)

**New skill `fux-debug`** in `src/fux/agents/generate.py::_SKILLS`, written for
triggering:

```
description: Diagnose Fux itself — when queries return nothing or look stale
or wrong, when ingest skipped files, or when a command errors. Runs fux doctor,
fux ingest --check, and fux why to find the cause before changing anything.
```

Its workflow section, in this order (cheapest first):

1. `fux doctor --json` — is the install/corpus healthy?
2. `fux ingest --check` — is the corpus stale? (re-ingest, re-ask)
3. `fux why "<question>" --doc <expected-file> --json` — why is the expected
   document missing or low?
4. If a passage looks thin: check `fidelity`; `fux ingest --advanced <file>`.
5. Only if still unexplained: re-run the failing command with
   `--debug=debug` (stderr) and report the trace.
6. **Report, don't guess** — the skill must tell the agent to surface the
   doctor/why output rather than speculate about causes.

**Existing skills gain one line each**: `fux-query` → "if results look wrong or
empty, use the fux-debug skill"; `fux-ingest` → same for skipped/stale files.

## F. Files

```
src/fux/debug.py            NEW — emitter, levels, categories, redaction, timing
src/fux/config.py           + DebugParams, [debug] parsing, precedence
src/fux/cli.py              + global --debug[=LEVEL]; + doctor, why subcommands
src/fux/doctor.py           NEW — the checks above, text + --json renderers
src/fux/query/why.py        NEW — per-document pipeline walk + verdict
src/fux/agents/generate.py  + fux-debug skill; pointer lines in the other two
src/fux/ingest/*.py         dbg() calls at walk/convert/chunk decisions
src/fux/index/*.py          dbg() at reuse/build/postings
src/fux/query/*.py          dbg() at candidates/dense/graph/fusion/answer
docs/example/DEBUG.md       NEW — worked failure → diagnosis → fix
```

## G. Milestones

- **M1 — `[debug]` config + emitter.** DebugParams, precedence, `debug.py`,
  redaction, the stdout-purity test. No call sites yet.
- **M2 — instrument the pipeline.** `dbg()`/`timer()` at every stage listed in
  §A; assert `off` has no measurable cost; trace output is reproducible.
- **M3 — `fux doctor`.** All seven groups, text + `--json`, fix commands,
  self-test; exit codes.
- **M4 — `fux why`.** Pipeline walk + verdict line; covers in-corpus,
  not-in-corpus, and ranked-but-low cases; `--json`.
- **M5 — skills + agent surface.** `fux-debug` skill, pointer lines, SETUP/
  SKILLS docs; assert generation in tests.
- **M6 — docs + suites.** `docs/example/DEBUG.md`, TOML/CLI/GLOSSARY/registry;
  e2e coverage for doctor/why/debug-levels; ADR 0012; bump **0.24.0**.

## H. Hard constraints

- `$0`/stdlib only; no new runtime deps (stdlib `logging` is acceptable *if*
  it never touches stdout and stays deterministic — a hand-rolled emitter is
  also fine and may be simpler to keep deterministic; decide at M1, record why).
- **Determinism is not negotiable**: existing goldens must pass byte-identical
  with `--debug=trace` set. Timing values only appear when `timing = true`, and
  never on stdout.
- Debug must not change *behaviour* — no code path may branch on debug level
  except to emit.
- Redaction default-on: an enterprise will send you these logs.

## I. Edge cases (tests)

Invalid level/category in toml (clear FuxError naming the key); `FUX_DEBUG=1`
back-compat; unwritable `output` path (warn to stderr, continue — debug must
never break a run); log exceeding `max_bytes` (truncate with a notice);
`doctor` on a directory with no fux.toml (explain + exit 1); `doctor` when the
model bundle is missing; `why` for a path not in the corpus; `why` for a path
that does not exist on disk; `why` with `--lexical-only`; unicode paths in
debug output; concurrent runs writing the same log file.

## J. Open questions (answer during build → ADR 0012)

1. Hand-rolled emitter vs stdlib `logging` — pick on determinism/simplicity.
2. Should `doctor --json` be stable enough for CI gating (i.e. a documented
   schema), or explicitly advisory? Recommend documented + stable.
3. Does `why` deserve `--all` (rank every doc's fate) or stay single-doc?
4. Whether `timing` belongs in `[debug]` or its own `[profile]` section.

## Close-out

ADR 0012; docs law full pass; IMPLEMENTATION.md phase-5 rows (pre-registered
with this handoff) updated at **every milestone**; archive this pair as
`docs/archive/v0.24.0-debug-observability-*.md`; CHANGELOG entry + README
"What's new" mirror; version 0.24.0.
