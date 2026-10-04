---
type: Handoff
name: W-246
description: "The gates the records asked for and nobody wrote — seventeen small stdlib tests and three `doctor` rows, each promoted from a backlog `ungated`/`unbuilt` row whose source already states what to check. Ratified 2026-10-03 by delegation, NOT built."
item: W-246
filed: 2026-10-03
ball: agent
---

# W-246 — the mechanical gates the backlog named

**Model:** Claude Code, **Sonnet** — every gate below is written against a
sentence in a record that already says what it asserts; none needs a design.
Land them in small commits grouped as the table groups them; a gate that goes
red on the live tree is a **finding** to file, never a reason to loosen it.

**Why one item.** SR-WORK-BACKLOG decision 2: *an agent can close an `ungated`*.
The 2026-10-03 audit ([W-251](W-251-backlog-audit-rulings.md)) found seventeen
rows whose closer is a test or a doctor row of a few dozen lines each. One item
keeps the queue honest about how much work it is (an afternoon, not a month)
and lets each gate cite the same ruling.

## Definition of done — every row lands, or says in the record why it cannot

### A · Repo-discipline tests (`tests/`)

| from | test | asserts |
|---|---|---|
| B-052 | `test_withdrawn_claims.py` | a table of (withdrawn phrase, retiring record, date) — *zero-dependency guarantee*, *stdlib-only runtime*, *never leaves the machine*, *hashed, bounded, and local* — appears nowhere in `src/`, `node/src`, `docs/`, `records/`, `CLAUDE.md` outside allow-listed history lines. Says in its docstring it catches recurrence, not new withdrawals ([SR-LAWS](../../records/0001_LAWS.md) d10) |
| B-054 | `test_l2_dependencies.py` | `pyproject.toml` optional deps ⊆ `{dev}`; `node/package.json` has no `dependencies`; every runtime dep's licence expression is OSI and its name appears in an accepted record. The two veto commands of [SR-LAW-2](../../records/0004_LAW-2-zero-cost.md), promoted verbatim |
| B-056 | in `test_sr_frontmatter.py` | `kind: process` ⇒ `owns` is not empty, with an exemption list that names each exempt record and its stated decision ([SR-WORK-OWNERSHIP](../../records/0054_WORK-ownership.md) veto 6) |
| B-047 | in `test_open_work_rows_are_short.py` | rules 37 (group headers present), 38 (every `work/open/W-*.md` names an `SR-`), 47 (no `commit|staged|push` in OPEN-WORK — Arpit's standing rule). Then amend [SR-WORK-OPEN-QUEUE](../../records/0051_WORK-open-queue.md) Consequences: the thirteen conduct rules (1, 5, 11, 12, 29, 30, 32, 33, 35, 36, 48, 50, 53) are *judgement, permanently* |
| B-068 | `test_guide_flags_exist.py` | every `fux <verb> --flag` token in `src/fux/templates/agents/*.md` parses against the argparse parser; a removed workaround flag reddens the guide ([SR-AGENT-POLICY](../../records/0132_agent-policy.md) d15g) |
| B-075 | in `test_cli.py` | every `add_argument` dest in `cli.py` is read somewhere under `src/fux` (`args.<dest>` / `getattr(args, "<dest>")`) — the accepted-but-unread floor ([SR-CLI](../../records/0101_cli-surface.md) §What this costs the capture) |
| B-076 | `test_differential_arms_import.py` | `graph_arm.py`, `goldens_grade.py`, `adversarial_corpus.py` import; amend [SR-T1-ACCELERATOR](../../records/0110_accelerator.md) Consequences. (A required check on `main` is W-251 §3 #22 — his) |
| B-077 | in `tools/differential/adversarial_corpus.py` + its test | the root argument is required; refuses when it equals the engine tree or holds a `.git` without `CI` set |
| B-079 | `test_dotdir_hygiene.py` | `ast.parse` + `compile` every `templates/*.py.txt` and `.fux/{fetchers,decoders}/*.py`; `[tool.ruff] extend-include` the dotdir for whoever runs ruff (not a dev dep — stay stdlib) |
| B-073 | in `test_setup.py` | every rule id in `templates/pii.toml.txt` exists in this repo's `.fux/pii.toml` — subset by id, never byte-equal ([SR-PII](../../records/0148_pii.md) d17) |
| B-065 | in `test_mcp.py` | for `fux_passage` and `fux_related`, as already done for `fux_search`: every field the handler emits is named in the description and vice versa ([SR-MCP](../../records/0136_mcp.md) Consequences). Completeness-in-general stays judgement — say so in the record |
| B-156 | in `test_regression_runs.py` | the per-query rows file is not byte-identical to any `questions/set-N.jsonl` and every row carries `id` and `rank` or `arm` ([SR-RS](../../records/0133_predictions.md) d21b — ruled *fires*, W-251 §2) |

### B · Engine invariants

| from | gate | asserts |
|---|---|---|
| B-072 | `test_postings_are_full.py` | on a fixture index every analyzer term of every document has a posting — the full-postings law P1 closed on ([SR-POSTINGS](../../records/0112_postings.md) Consequences). **M**, the one non-trivial test here |
| B-084 | in `tests/ingest/` | a fetcher module without `MAX_PARALLEL` runs serial (the fail-safe that exists in `urlsrc.py` and is untested); `doctor` names a fetcher declaring more than 1 ([SR-LAW-4](../../records/0006_LAW-4-deterministic.md) Consequences) |
| B-085 | in `templates/cdp.py.txt` + `tests/ingest/test_cdp_fetcher.py` | paused requests == resolutions per fetch, else raise naming the URL before `LOAD_TIMEOUT_S` ([SR-CDP-FETCHER](../../records/0118_cdp-fetcher.md) Consequences) |
| B-086 | `doctor.py::_accelerator` + test | compares the manifest's per-shard sha to the shard bytes — the deep check `accel.py`'s docstring claims and doctor does not do; a same-size same-mtime byte flip warns ([SR-RUNTIME-STAMP](../../records/0124_runtime-stamp.md) Consequences) |

### C · `doctor` rows

| from | row | asserts |
|---|---|---|
| B-020 | `priority keys` | a `[priority]` key that prefix-matches no `sources/dirs` entry or URL is named — the orphan check that already exists for sources, applied to tune ([SR-TUNE](../../records/0135_tuning.md) d10a: drop the tune-load-warning half, the seam does not exist) |
| B-074 | beside `fuxignore usable` | a `.fuxignore` rule shadowed by an earlier rule (never reachable) is a warning — the one observable symptom of a wrong reorder ([SR-FUXIGNORE](../../records/0144_fuxignore.md) Consequences) |
| B-080 | `decoder imports` | AST-scan `.fux/decoders/*.py` for `urllib`, `socket`, `http.client`, `requests`, `ssl` → warning. **The record must call it a tripwire, never coverage** — it fails open on dynamic imports ([SR-DECODE](../../records/0139_decode.md) Consequences) |
| B-168 | `ranking priors` | owes `intent_weight` with its count of documents of the preferred type — the per-record-declaration prior d5a was waiting for ([SR-DOCTOR](../../records/0152_doctor.md) d5a; [SR-RANKING](../../records/0111_ranking.md) d13) |
| B-161 | `journal size` | warns above `[cli.answer] journal_max_bytes` (new key, template + `doctor --fix`; L12) ([SR-PROVENANCE](../../records/0142_provenance.md) d15 — ruled *accept*, W-251 §2) |

### D · Closing

- Each record named above gains one sentence saying the gate exists, in the
  change that lands it; `sr-hash` restamped.
- Both suites whole. A WORKLOG entry naming any gate that was **red on the live
  tree** and what it found.

## Out of scope

- Anything the audit classed *judgement* — those are `cost` B-252 and stay there.
- The walking-tests fix — that is [W-244](W-244-l11-ingest-walk-2026-10-03.md)'s DoD 3.
