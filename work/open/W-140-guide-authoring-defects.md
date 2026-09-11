---
type: OpenItem
id: W-140
title: "W-140 — the defects writing the operating guides uncovered"
description: "Writing ten consumer skills from the code (ADR-AGENT-POLICY decision 15, 2026-09-11) meant checking every flag, field and verdict against src/fux and running most verbs. That found code defects, ADR-vs-code disagreements, and guide text that names workarounds which must change when each defect is fixed."
status: open
lane: agent
timestamp: 2026-09-11T00:00:00Z
---

# W-140 — defects found while writing the operating guides

**Model: Opus** — each row needs a call on whether the code or the record is
wrong, and several touch the refer plane, PII and receipts.

**Provenance.** Found 2026-09-11 in a Cowork session by five drafting agents and
one adversarial reviewer, reading `src/fux/` and running verbs on a copy of the
tree (Linux, Python 3.12, no network). **Not yet reproduced on the Mac** — rule 4
applies: re-derive before fixing.

🔴 **Hazard for whoever fixes a row:** the shipped guides in
`src/fux/templates/agents/*-SKILL.md` name workarounds for rows marked **(guide)**.
**Fix the defect and edit the guide in the same change** (ADR-AGENT-POLICY 15g),
then refresh this repo's renderings.

## 1 · Code defects

| # | defect | where | record |
|---|---|---|---|
| 1 | 🔴 **URL citations are never verified live.** `refer/source.py` rejects a non-`str` fetcher return; both shipped fetchers return `(bytes, content_type)`. Note `fetcher returned tuple, expected str`; verdict `as-ingested` or `unverified`. **(guide: ANSWER, FETCHER)** | `refer/source.py` ~143 | ADR-REFER d23 · ADR-FETCHER |
| 2 | 🔴 **PII leaks past redaction:** a frontmatter `title:` is committed unredacted (only the body is redacted), and a value in a filename lands in `loc`. **(guide: PII)** | `ingest/extract.py` ~139, `ingest/run.py` ~410 | ADR-PII |
| 3 | **`fux add <URL> --no-update` never fetches** — pinned URLs are dropped before the fetch, exit 1. `cli.py` help and CHANGELOG say it fetches once. **(guide: SOURCES)** | `ingest/run.py` ~216 | ADR-URL-LIST d14 |
| 4 | **`fux update --failed` is parsed and never read.** **(guide: SOURCES)** | `cli.py` ~405 | ADR-CLI |
| 5 | **`fux add <URL>` writes every attribute**, so `[sources.url]` `fetcher`/`meta`/`keep`/`ttl`/`update` never reach CLI-written lines. **(guide: SOURCES, FETCHER)** | `sources.py` | ADR-URL-LIST d14 |
| 6 | **`answer` runs with the fetch cache off**: `ttl=` never applies, `cached` is unreachable, `update=never` does not stop the answer-time fetch. | `query/refer_answer.py` ~104 | ADR-URL-FRESHNESS d11/d15 · ADR-REFER d20 · ADR-ACQUIRED |
| 7 | **`verify` misreports**: a `source: index` receipt and an unreachable URL both give `drifted:corpus`, not `unverifiable`; `--rerun` fetches. **(guide: ANSWER)** | `query/__init__.py` ~994, ~1075 | ADR-PROVENANCE d14 |
| 8 | **Unknown `fux.toml` keys are silently ignored.** | `config.py` ~154 | ADR-CONFIG |
| 9 | **The merge driver's refusal says re-run `fux ingest`**, which cannot read a shard with conflict markers. **(guide: MAINTAIN)** | `maintain/mergedriver.py` ~201 | ADR-MERGE-DRIVER d6 |
| 10 | **`fux hooks` installs nothing when `[cli.json] enabled = true`** — it only reports. **(guide: MAINTAIN)** | `maintain/__init__.py` ~113 | ADR-MAINTENANCE |
| 11 | **The background runner never rebuilds the accelerator.** | `maintain/runner.py` ~534 | ADR-MAINTENANCE 2a |
| 12 | **`fux path` never checks FROM/TO exist** (empty, exit 0); `explain tag:x` is never missing; `--hops` is unbounded (hops 7 > 60 s on ~960 docs). **(guide: GRAPH)** | `graph/__init__.py` | ADR-GRAPH |
| 13 | **`fux doctor` has no `tune.toml` row** — a broken tune file leaves doctor green. **(guide: CONFIG, pointers)** | `doctor.py` ~345, ~758 | ADR-DOCTOR · ADR-TUNE |
| 14 | **`fux update --check` always exits 0** and has no `--json`. **(guide: INDEX, MAINTAIN)** | `sources.py` | ADR-CLI |
| 15 | **No fetch timeout is enforced** — `timeout_seconds` is recorded and read nowhere. | `refer/freshness.py` ~44 | ADR-REFER |
| 16 | **URL documents keep old redactions after a `pii.toml` change** until re-fetched, `--full` included — the record says this only for `update=never`. **(guide: PII)** | `ingest/run.py` ~187 | ADR-PII |
| 17 | **Starter refusal rules refuse real wiki pages** (`viewpage.action`, `.aspx`, `.php`); `suspiciously-small-document`'s comment says *warn* but it refuses. **(guide: FETCHER)** | `templates/refusals.toml.txt` | ADR-REFUSAL |
| 18 | **Small ones:** `.fux/.gitignore` misses `__pycache__/` under `decoders/`/`fetchers/`; a re-run of `setup` always prints the `AGENTS.md` paste note; the generated `urls` header says "two attributes" and "re-fetches every line"; the starter `pii.toml` and doctor point at `tools/pii-probe/probe.py`, which is not in the package. | `setup.py`, `store/fuxdir.py`, `doctor.py` ~484 | ADR-DOTFUX · ADR-PII |

## 2 · Records that disagree with the code

- **ADR-ASK / ADR-REFER d19 / `output.schema.json`** say six freshness states; `Verdict.label` has five.
- **ADR-ANSWER d9, ADR-REFER d17**: `passage.ordinal` in `--json`/MCP — absent.
- **ADR-PROVENANCE d11**: `digest.sha256` is a 40-hex blake2b, not SHA-256; d10 says only `--journal` writes, but `[cli.answer] journal` does too.
- **ADR-FIND** veto check 4 greps `^\[band\]`; the line is `confidence: …`.
- **ADR-GRAPH / `graph.schema.json`**: edge kind `supersedes` unlisted; grades are ints, not strings; labels are `c0`; a stale plane is not refused.
- **ADR-MCP**: `fux_passage` does not fetch or re-score; `fux_related` returns edges only; citations are document-level; the index is not held open.
- **ADR-DOCTOR**: `refusal rules`, `decoder bindings`, `fuxignore usable` fail as errors, not warnings; doctor creates `.fux/` and `CACHEDIR.TAG`.
- **ADR-DOTFUX**: says `.fuxignore` is never rewritten; ingest rewrites its skip blocks.
- **ADR-INDEX-LIFECYCLE 10a** warns against deleting `.fux/index/`; the version-mismatch error tells users to.
- **ADR-URL-LIST**: a line's `meta=hashed` does win over a source-wide `plain`; **ADR-CONFIG d5**: a line with no `fetch=` uses `[sources.url] fetcher`, not `http`.
- **ADR-CONFIG**: absent `[agents] install` means four vendors; `Config`'s default and `config.schema.json` lag (missing `keep`, `ttl`, `enrich`, `update`, `sweep_minutes`, `acquired_max_bytes`).
- **ADR-TUNE**: `fux tune` prints defaults and measures nothing; `[priority]` warnings are unbuilt; seven tables, not six. **ADR-OUTPUT §1** still shows the old `[defaults]` layout.
- **ADR-MAINTENANCE 5a**: doctor does not report never-fetched hand-added URL lines.

## Definition of done

Each row: reproduce on the Mac, then fix the code **or** amend the record, update
any guide marked **(guide)**, re-render this repo's copies, and delete the row.
The file closes when both sections are empty.
