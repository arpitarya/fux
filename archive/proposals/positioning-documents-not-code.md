---
type: Proposal
title: "Positioning — a search index over written knowledge, not over code"
description: "Audit of why fux is filed next to AST/code-graph tools, with the evidence that it parses no code (and by default indexes none), every live wording that implies otherwise, proposed replacements, and the OKF v0.1 conformance state of the docs/ + work/ bundle. GRADUATED 2026-09-12: §4 applied with Arpit's reframing, §5 as the glossary entry only, §6 option (b) plus a gate."
status: graduated
timestamp: 2026-09-11T00:00:00Z
graduated: 2026-09-12
---

# Positioning — written knowledge, not code

⚠ **The title and filename still say *documents*, and the file name is kept so
existing links resolve. The framing they came from was overruled** — see the
graduation block immediately below.

## ✅ GRADUATED 2026-09-12 — what Arpit ruled, and what landed

**The trigger fired**: Arpit accepted §4, picked §5's cheap alternative, and
picked §6 option (b). **Read this section before any row below** — §4's
proposed wording was *overruled on framing*, so the tables in §4 are now a
record of what was proposed, not of what shipped.

### 🔴 The one thing this proposal got wrong

**§4 defined fux relative to code** — *"the documents around your code"*.
Arpit struck it: *"I don't want it to say around my code. The code word should
not be there… It will be all the documents present within an organization or
not an organization."*

- The proposal set out to stop fux being filed next to code tools, and then
  **kept code as the reference point** — a weaker version of the same defect.
- **The corpus is written knowledge**: decisions, runbooks, specs, wiki pages,
  policies, contracts, notes. A repository is one place it can live, **not what
  fux is about**, and a solo user with no organization at all is a user.
- Arpit also struck *"organization"* from the tagline: *"I want even people who
  are not part of an organization to use it as well."* Second person carries
  both.

**Shipped tagline:** *A search index for your written knowledge — decisions,
runbooks, specs, wiki pages — committed to git and read by agents.*

### What landed

| § | ruling | what changed |
|---|---|---|
| 4.1 tagline | **reframed** | `README.md:3` — the line above. No "code", no "codebase", no "organization". |
| 4.2 lede | **applied, reworded** | The proposal's *"It does not read the code."* was dropped from the lede — a denial in the second sentence keeps the association alive. `README.md:6-8` now says *"committed to git"*, not *"committed next to your code"*. |
| 4.3 bullet | **applied** | New last bullet under *Why fux*: **It indexes documents, not code.** The counterweight lives here, once, where someone checking will look. Still names no competitor. |
| 4.4 pyproject | **applied** | `description` → *"rank your written knowledge…"*; `codebase`, `llm`, `claude` dropped from `keywords`; **Quality Assurance** classifier dropped; `Text Processing :: Indexing` and `Internet :: WWW/HTTP :: Indexing/Search` added. ⚠ **PyPI only changes on the next upload.** |
| 4.5 glossary | **applied** | `docs/GLOSSARY.md` → **Documents, not code**, the three facts of §1, so `fux ask` has a live answer on fux's own repo. |
| 4.6 `docs/index.md` | n/a | Nothing implied code analysis. (It changed for §6 instead.) |
| 4.7 paper | **applied** | `work/paper/the-fux-index-paper.md:155-156` — the non-existent *symbol edges* are gone. |
| 4.8 agent templates | **applied** (proposal said low priority) | All three usage renderings + their five installed copies: *"this codebase's history or design"* → *"this project's"*. Recorded as an amendment in [SR-AGENT-POLICY](../../records/0132_agent-policy.md), with why `policy-version` stays at 1. |
| 4.8 GitHub About/topics | **still open** | Not reachable from a Cowork session. Arpit's hands: `gh repo view arpitarya/fux --json description,repositoryTopics`. |
| **5** `code` edge kind | **glossary only** | Arpit chose the cheap alternative. New entry **`code` (edge kind)** in the glossary; **the rename to `path` was NOT done** and stays owned by [SR-GRAPH](../../records/0126_graph.md). |
| **6** OKF | **option (b)** | See below. |

### §6 — option (b), and the two places it could not be applied literally

**Arpit picked (b): fix the files.** Applied as:

1. **The ALL-CAPS exemption is retired.** It was a repo convention the spec does
   not have, which is the whole reason the numbers disagreed. 18 trackers now
   declare a `type` — `OPEN-WORK` (Queue), `WORKLOG` (Log), `GLOSSARY`
   (Glossary), `DOC-REGISTRY` (Registry), `IMPLEMENTATION` (Milestone Log),
   `INTERVIEW` (Handoff), `MACHINE` (Runbook), `NOW` (Pointer),
   `governance.md` (Governance), the SR register (Register), and every
   directory `README.md` (Index). `CLAUDE.md` and `docs/index.md` both updated.
2. **`work/regression/*/evidence/**` is declared outside the bundle**, as (b)
   said. Evidence is cited *by* a document; it is not one.
3. ⚠ **Two things (b) could not touch, and why that is not a dodge.**
   - **Filed regression runs before 2026-08-25** — 29 `report.md` / `ANALYSIS.md`
     files. `tests/test_regression_runs.py` already baselines its own rule on
     that date, in its own words: *turning a rule on by editing the evidence it
     governs is the failure the rule is about.* Same baseline, stated in
     `docs/index.md`. The one post-baseline miss —
     `2026-09-06-csv-chunk-granularity/ANALYSIS.md` — **was** fixed.
   - **`work/golden/seed/` and `golden-answer/`** — the sealed benchmark's test
     data, authored outside this lane. Declared outside the bundle; editing it
     to satisfy a docs rule would corrupt the instrument.
4. **A gate, which is the part that makes it stick.** New
   [`tests/test_okf_bundle.py`](../../tests/test_okf_bundle.py): 237 documents
   checked, **0 failures**. The §6 finding was *94 of 314 files fail a bar this
   repo claimed in prose and checked nowhere* — prose is what let it drift, so
   prose is not the fix.

### Also fixed on contact

- **`src/fux/frontmatter.py:3`** — *"the zero-dependency guarantee made
  concrete"*, a promise L1's 2026-09-06 amendment withdrew. §6 found it and did
  not fix it; it is fixed now, and noted in [SR-LAWS](../../records/0001_LAWS.md).

### Still open after this

- **GitHub About + topics** (§4.8) — Arpit's hands, needs `gh`.
- **The PyPI page** — text changes only on the next upload; older release pages
  keep theirs forever.
- **The `code` → `path` rename** (§5) — deliberately not done. Glossary defines
  it instead.
- **OKF v0.2 drift** (§6) — the repo pins v0.1 and the upstream spec read v0.2
  on 2026-09-11. Unchanged by this work.

---

**Model: Sonnet** applies accepted wording (exact before/after text below).
**Model: Opus** for the `code` edge-kind rename in §5, because it changes a
committed record field and SR-GRAPH.

~~**Graduates when** Arpit accepts or strikes each line in §4. Nothing here is
applied.~~ **Fired 2026-09-12** — see the section above. **No SR affected** by
the wording itself; §5's rename would affect
[SR-GRAPH](../../records/0126_graph.md) and SR-RECORD.

---

## 1. Takeaway

- **Fux has no code-analysis layer.** No AST, no symbols, no call graph.
- **Stronger than the brief assumed: fux does not index code by default.**
  `.py` is not on `DEFAULT_TYPES`; ingest reports `not an indexed file type`.
- **The misfiling has a real history.** v0.1–v0.26 `fux-engine` *was* partly a
  code-graph tool (stdlib `ast`, a tree-sitter `[ast]` extra, call edges, AST
  seals, a Graphify parity matrix). Old tags and crawler caches still say so.
- **Live wording still leans on it:** "AI-assisted codebases" (PyPI alpha.7
  README), keyword `codebase`, classifier *Quality Assurance*, and the paper's
  "symbol edges" — which do not exist.

## 2. Evidence — no AST layer (brief task 1)

**grep** `grep -rniE "ast\.|tree_sitter|tree-sitter|parse_code" src/ tools/`

| hit | what it is | verdict |
|---|---|---|
| `src/fux/doctor.py:113,117,154,155,156,174,426` | `last.get(` / `past.` | regex false positive |
| `src/fux/refer/__init__.py:292` | `least.` | regex false positive |
| `src/fux/derive/format.py:137` | `past.` | regex false positive |
| `src/fux/sources.py:392` | `last.` | regex false positive |
| `src/fux/graph/graph.schema.json:32` | "a test asserts the ABSENCE of the import by parsing the module's AST" | a **self-check** on fux's own source |
| `tools/` | none | — |

- `import ast` exists only in `tests/refer/test_{rescore,refer_plane,source,arc,freshness}.py` — each parses **fux's own module** to prove a forbidden import is absent.
- No `tree_sitter` anywhere in `src/` or `tools/`. `dependencies = []`.

**Default type list** (`.fux/sources/types`, derived from `ingest/gitdir.py` `DEFAULT_TYPES`):
prose (`md rst adoc org txt markdown`) + decoders (`csv docx drawio html image ini json jsonl mail pdf pptx rtf svg toml xlsx xml yaml`). **No source-code extension.**

```bash
# repro, 2026-09-11, fux 2.0.0-alpha.7 working tree
mkdir -p r/docs r/src && cd r && git init -q
printf '# Deploy\nroll back with make rollback\n' > docs/deploy.md
printf 'def rollback():\n    """roll back release"""\n' > src/app.py
fux setup --no-agents && echo src >> .fux/sources/dirs && fux ingest
#   not indexed src/app.py: not an indexed file type
fux find rollback
#   docs/deploy.md
```

**Fux against its own corpus** (working tree, reference scan):

| query | top 5 | reading |
|---|---|---|
| `fux find "AST"` | 5/5 `archive/v0.1/…` (test-repo plan, pyproject, marketing plan, README, implementation notes) | **true hits, correctly marked archived** — v0.1 really parsed code. **Zero live docs.** |
| `fux ask "does fux parse code"` | `archive/open/W-86…`, `archive/v0.26-implemented/v0.25.0…`, `work/regression/2026-08-20-ingest-cost-profile/report.md`, `archive/v0.1/docs/marketing-plan.md`, `work/regression/2026-09-02-enrich-pii-leak/report.md` | 🔴 **both live hits are lexical false positives** — "parse" = ingest's parse stage, "code" = test code. None answers the question. |
| same, `--expand "AST call graph tree-sitter symbols Graphify adjacent tools"` | 5/5 `archive/v0.1/…` | the one live answer — paper §2 *Adjacent tools* — never reaches top 5 |

- **grep vs fux:** grep's 10 `src/` text hits are substring noise; fux's are real documents but historical. **Neither surfaces a live statement that fux does not parse code — because none exists.** That gap is itself a positioning defect (§4.5).

## 3. Why fux gets filed next to code-graph tools

Ranked by weight of evidence, strongest first.

1. **The pre-reset lineage said it outright.** Tags `v0.1.0`–`v0.26.0` exist.
   - `archive/v0.1/pyproject.toml`: `ast = ["tree-sitter>=0.23", …]`; keywords `rules, graph, …, mcp`.
   - `archive/v0.1/README.md:123`: *"merges your rules with code symbols and call edges across Python (stdlib `ast`) and JS/TS, Go, Rust"*.
   - `archive/v0.26/pyproject.toml`: *"rules bound to code, read by agents before they touch anything"*.
   - ⚠ **Unverified:** which of those versions reached PyPI. PyPI release pages are immutable, so any that did still carry that text.
   - A web fetch of the GitHub repo page on 2026-09-11 returned v0.26's README (*"git-versioned Markdown corpus"*) while `main` is `80ee187` — **crawler caches lag by weeks.**
2. **The released tagline.** `v2.0.0-alpha.7:README.md` (what PyPI renders): *"Deterministic knowledge retrieval for AI-assisted codebases"*.
3. **Metadata.** keyword `codebase`; classifier `Topic :: Software Development :: Quality Assurance` — a v0.1 carry-over from rule checking, and the static-analysis neighbourhood.
4. **Agent hooks.** "built for coding agents", skills for Claude Code/Codex/Copilot/Kiro, *"search the index before grepping"* — true, and it reads as code search without a counterweight.
5. **The paper.** `work/paper/the-fux-index-paper.md:155-156`: *"Fux is the knowledge-side complement, joined at file-path/symbol edges."* **There are no symbol edges** — `ingest/edges.py` resolves backtick spans to *ingested document paths* only.
6. **An edge kind named `code`.** Same mechanism as 5, surfaced by `fux explain` / `graph` / `path`.

## 4. Audit + proposed wording (brief tasks 2 and 3)

⚠ **`README.md` has an uncommitted rewrite in the working tree.** Rows below
cite both. The rewrite already drops "AI-assisted codebases"; it does not add
a counterweight.

### 4.1 README tagline — `README.md:3`

| | text |
|---|---|
| HEAD / PyPI alpha.7 | **Deterministic knowledge retrieval for AI-assisted codebases — rank from a small git-carried index, fetch content from the systems that own it, verify at answer time.** |
| working tree | **A search index for your docs that lives in your git repo — built for coding agents.** |
| **proposed** | **A search index for the documents around your code — decisions, runbooks, specs, wiki pages — that lives in your git repo and is read by coding agents.** |

### 4.2 README lede — `README.md:5-7` (working tree)

| | text |
|---|---|
| current | Fux ranks documents from a small, plain-text index committed next to your code, then reads the answer back from the source itself. No server, no vector database, no API key, and no model anywhere on the path. |
| **proposed** | Fux ranks documents from a small, plain-text index committed next to your code, then reads the answer back from the source itself. **It does not read the code.** No server, no vector database, no API key, and no model anywhere on the path. |

### 4.3 README — new bullet at the end of *Why fux* (working tree, after line 24)

- **proposed:** `- **Documents, not code.** Fux parses no source code — no AST, no symbols, no call graph — and source files are not on its default type list. Pair it with a code-graph tool for structure; fux covers the decisions and docs around it.`
- Deliberately **names no competitor**: naming one in the front door strengthens exactly the association being removed.

### 4.4 `pyproject.toml` (identical at HEAD, working tree and tag alpha.7)

| field | current | proposed |
|---|---|---|
| `description` (line 8) | Fux — rank organizational knowledge from a small index committed to git; fetch content from the systems that own it; verify freshness at answer time. | Fux — rank the documents around a codebase (decisions, runbooks, specs, wikis) from a small index committed to git; fetch content from the systems that own it; verify freshness at answer time. |
| `keywords` (line 13) | `knowledge, index, search, claude, agent, frontmatter, llm, adr, codebase` | `knowledge, documentation, search, index, bm25, adr, runbook, frontmatter, agent` — drops `codebase`, `llm`, `claude` |
| `classifiers` | `Topic :: Software Development :: Documentation` · `Topic :: Software Development :: Quality Assurance` | keep the first; **drop Quality Assurance**; add `Topic :: Text Processing :: Indexing` and `Topic :: Internet :: WWW/HTTP :: Indexing/Search` ([trove list](https://pypi.org/classifiers/)) |

⚠ **PyPI only changes on the next upload.** Older release pages keep their text.

### 4.5 The corpus itself — a live answer to "does fux parse code"

- `docs/GLOSSARY.md` has no entry that would rank. **Proposed:** a *Documents, not code* entry stating the three facts in §1, so `fux ask` answers this on fux's own repo.

### 4.6 `docs/index.md`

- **No wording implies code analysis.** Nothing to change.

### 4.7 Paper — `work/paper/the-fux-index-paper.md:155-156`

| | text |
|---|---|
| current | Fux is the knowledge-side complement, joined at file-path/symbol edges. |
| **proposed** | Fux is the knowledge-side complement: it parses no code, and joins a code tool only where a document names a file path. |

### 4.8 Not audited, worth one look

- **GitHub About + topics** — could not be read from here (API 403, page cache stale). `gh repo view arpitarya/fux --json description,repositoryTopics`. Topics are a strong classifier signal.
- Agent templates (`src/fux/templates/agents/{USAGE-SKILL.md:11, fux-usage.instructions.md:13, fux.agent.md:13}`): *"this codebase's history or design"* — accurate; low priority.

## 5. The `code` edge kind (flag, not a wording fix)

- `ingest/edges.py`: `code` = a backtick span that resolves to another **ingested document's path**. It is a link, not code analysis.
- A rename (e.g. `path`) changes the committed record and `graph.schema.json` examples — **owned by SR-GRAPH**, Opus, its own change.
- Cheap alternative: define it in `docs/GLOSSARY.md` as *"a backtick-quoted path to another indexed document — not parsed code."*

## 6. OKF v0.1 (brief task 4)

**The brief's premise is stale.** `.fux/cache/` was v0.26's OKF Markdown corpus
(`archive/v0.26/README.md:165,223`). Since the v0.30 reset **fux emits no
corpus at all** — L2: the index holds statistics, never content.

**Where OKF is used today:**

| surface | role | state |
|---|---|---|
| `docs/` + `work/` bundle, root `docs/index.md` (`okf_version: "0.1"`) | the repo's own knowledge docs | see scan below |
| `src/fux/frontmatter.py` | **consumer**: permissive parse, unknown keys preserved | conformant with the consumer rules |
| ingest | reads `title`, `tags`, `supersedes` — **not `type`** | OKF-neutral |
| `.fux/enrich/<sha>.md` | frontmatter validated by `enrich.py` (`source, source_sha, chunks, model, generated, skill`) | **no `type`** — not an OKF concept, and not declared a bundle |

**Bundle scan** (fux's own parser; non-reserved `.md` under `docs/` + `work/`, 2026-09-11):

| class | count | conformant to the spec's *non-empty `type`* rule? |
|---|---|---|
| typed (lowercase 147 + ALL-CAPS 73) | 220 | yes |
| ALL-CAPS, no `type` | 37 | **no** — exempt by *repo convention*; the spec has no such exemption |
| lowercase, no frontmatter | 15 | **no** — `work/governance.md` + 14 frozen `report.md` runs (2026-08-09…08-23) |
| lowercase, frontmatter but no `type` | 42 | **no** — all enrichment evidence under `work/regression/*/evidence/` |
| `docs/index.md` (reserved) | 1 | yes — only `okf_version` |

- **Verdict: strictly, 94 of 314 files fail.** Under the repo's own stated bar (lowercase docs typed) it is **57**, and 56 of those are frozen regression runs or their evidence.
- `WORKLOG.md` follows OKF's log *style*, but the spec's log semantics bind the reserved filename `log.md`; as `WORKLOG.md` it is an ordinary file.
- ⚠ **Spec drift.** Upstream `okf/SPEC.md` read as **v0.2** on 2026-09-11 (conformance at §11). The repo pins v0.1 and cites v0.1 section numbers (`frontmatter.py` cites "OKF §9"). The v0.1 text was not retrievable; the rule tested above is the one CLAUDE.md states for v0.1.
- ⚠ **Stale claim found on contact, not fixed:** `frontmatter.py:3` — *"the zero-dependency guarantee made concrete"* — that guarantee was withdrawn with L1's 2026-09-06 amendment.

**Options (Arpit's call):** (a) state the ALL-CAPS/evidence exemptions as a documented *profile* of OKF and stop claiming plain conformance; (b) add `type:` to the 37 trackers and exclude `evidence/` from the bundle in `docs/index.md`; (c) do nothing — consumers must not reject a bundle for this.

## 7. Corrections to the brief that commissioned this

- **No bundled static embedding model** — the dense lane was deleted 2026-08-25 (`alpha.1`). RRF now fuses the **ranks** of repeated `-q` phrasings (`query/fuse.py`).
- **No `.fux/cache/`** and **no `docs/PLAN.md`** (archived 2026-08-18).
- **Code files are not ingested as text** by default — see §2.

## Reference

- Code: `src/fux/ingest/edges.py`, `src/fux/ingest/gitdir.py` (`DEFAULT_TYPES`), `src/fux/enrich.py`, `src/fux/frontmatter.py`, `src/fux/query/fuse.py`.
- OKF spec: https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md
- PyPI trove classifiers: https://pypi.org/classifiers/
