---
type: OpenItem
id: W-206
title: "W-206 — the compare/ and proposals/ sweep: 24 forks → 8 live, 17 proposals → 10 parked"
description: "Arpit, 2026-09-20: review every compare doc and proposal; merge what can be merged, archive what is implemented or no longer needed. Reviewed the same day (two read-only passes over all 41 files against the repo's own archive rules); this file is the ratified disposition table. Claude Code executes the moves, the record ports and the citation repoints in one change."
status: open
lane: agent
timestamp: 2026-09-20T00:00:00Z
filed: 2026-09-20
ball: agent
ruled: 2026-09-20
---

# W-206 — the compare/ and proposals/ sweep

**Model: Sonnet** — every call below is made; what remains is `git mv`, archive
rows, porting a trigger sentence into a record, repointing citations, and the
doc tests. **Opus only for step 2** (record edits — an accepted record may not
ground on `archive/`, and the port has to say the same thing the doc said).

**The rules applied, not restated:** a compare doc archives only when its fork
is closed **and** its reopen-trigger can no longer fire
([`archive/compare/README.md`](../../archive/compare/README.md)); a proposal
archives when fully implemented, superseded, or every item it graduated into has
closed ([`proposals/README.md`](../proposals/README.md));
[SR-WORK-ARCHIVE](../../records/0062_WORK-archive.md) decisions 4–8 decide
whether a citation may point into `archive/`.

**One default taken (Arpit may override):** *merge into a record* means the
record already carries the verdict **and** the reopen-trigger (or gains it in
this change), so the compare doc's job is done and it archives with a row that
says **"the trigger lives in `<record>` `<decision>`"** — a second permitted
form of the *why it cannot fire* sentence. Without this, nine decided forks stay
live forever because their triggers are checkable, which is not what "live
fork" means.

---

## A · `work/compare/` — 24 docs

### A1 · Stay live (8) — fix first where flagged

| doc | why it stays | fix in this change |
|---|---|---|
| `fux-correct` | W-175's generalisation measurement unrun → W-204 I-3 / phase E | — |
| `types-toml` | trigger 1 is adjacent to W-199's `[sources.url.routes]` TOML | — |
| `hook-at-scale` | half 2 (deferred re-index answers from a mismatched index) checkable | **absorbs `maintenance-trigger`** (below) |
| `abstention-gates` | gates 4–9 unmeasured → W-204 phase E | frontmatter `proposed` → `decided (Arpit, 2026-09-14, option a)`; README row updated |
| `ask-graph-expansion` | W-161's arms unmeasured → W-204 phase E | body says W-161 "waits on W-156" — it **shipped 2026-09-15 unmeasured**; add the dated note |
| `blind-authorship-rule` | triggers 1, 2, 4 live | record that **trigger 3 fired 2026-08-28** (SR-RS d19: floor ±2 → 6) |
| `what-good-means` | triggers 1, 3, 5 live | record that **trigger 4 fired 2026-08-28** (same ruling); §5's "50 playground goldens" retired under L9 |
| `df-over-the-union` | A (leave `df` alone) still holds | record that **trigger 4 fired 2026-09-13** (`archived_weight` removed, W-152): the verdict now rests on A alone; trigger 2 is unwordable |

### A2 · Merge into the owning record, then archive (9)

| doc | record that holds the verdict | what must be ported before the move |
|---|---|---|
| `cache-policy` | SR-CACHE veto 6 | nothing — already verbatim |
| `refer-fetch-cache` | SR-CACHE veto 7 | nothing; the doc's "record-freshness ⏳ awaiting Arpit" is stale |
| `copilot-skill-surface` | SR-AGENT-POLICY d14–16 | nothing — d16 carries the duplicate-name trigger |
| `cross-encoder-reopen` | SR-RERANK veto 1 | nothing — the adjacent-gap floor is there; the §6 recommendation was refused |
| `file-type-filter` | SR-TYPES reopen 1 | nothing — its mechanism was superseded by `types-toml` anyway |
| `index-lock` | SR-LOCKS | 🔴 **port the NFS/SMB trigger** into SR-LOCKS' reopen list — it is absent |
| `maintenance-trigger` | SR-MAINTENANCE d1a (+ `hook-at-scale`) | port the *half-written shard* trigger into SR-MAINTENANCE's veto list; ⚠ the doc cites "d1d" for deferral — the record numbers it **1a** |
| `path-hops-bound` | SR-GRAPH d17 (`routes()` budget, `truncated`) | doc says "not yet implemented" — it is; the four triggers are checkable and live in d17 |
| `table-tokens-in-flen` | SR-RANKING d3 / SR-TUNE (`b = 0.15`, W-144 PASS 2026-09-16) | frontmatter `proposed` → `decided`; the measured result is recorded in the record, not the doc |

### A3 · Archive — closed and the trigger cannot fire (7)

| doc | why the trigger cannot fire | successor named in the row | citation to repoint |
|---|---|---|---|
| `graph-plane-format` | half 1 is the 50k target, above the measurement ceiling; half 2 (a real 10k corpus > 1 s) has no corpus | SR-GRAPH d8 | — |
| `index-format` | T2 declined (R9 12.46 ms vs 150 ms); 200k is above the ceiling; the Python-version half belongs to L3's owner | SR-INDEX-RECORD · SR-POSTINGS · SR-LAW-3 | `docs/GLOSSARY.md` |
| `record-freshness` | premise dead 2026-08-25 (`mtime` committed); SR-REFER d4 carries its own reopen | SR-REFER-PLANE d4 · SR-URL-FRESHNESS | `refer/freshness.py` docstring still recites the dead premise — fix |
| `record-shape-migration` | no trigger exists; a landed migration cannot be redone; index is at v4 | SR-INDEX-RECORD · SR-TUNE d6 | — |
| `source-exclusion` | verdict E (`!` entry) is the **deprecated spelling**; option B (`.fuxignore`) won via SR-FUXIGNORE, whose grammar scopes by path | SR-FUXIGNORE · SR-DIR-LIST d2b | — |
| `storage-architecture` | trigger 1 fired and was absorbed (P1-RERUN); 2 says "even hashed" — L5 retired; 3 unmeasurable | SR-REFER-PLANE · SR-LAW-2 · SR-POSTINGS | `docs/GLOSSARY.md` |
| `meta-privacy` | every trigger presupposes hashed meta or the display cache — both deleted 2026-09-20 (W-194, L5 retired). ⚠ Doc's 2026-08-25 note "both halves are built" is false — say so in the row | SR-LAW-5 (retired; holds the exposure and reopen) | — |

**After A:** 8 live forks; `work/compare/README.md` rewritten to those eight;
`archive/compare/README.md` gains 16 rows.

---

## B · `work/proposals/` — 17 files

### B1 · Stay parked (10) — fix first where flagged

| file | fix |
|---|---|
| `adr-review-2026-08-28` | note the register it audits is now 88 records, not 47; trigger unchanged |
| `architecture-review-2026-08-28` | add the cross-references: A.14 ↔ W-205, C.5 ↔ `search-improvements-v3` #4, C.2 ↔ W-144 |
| `identifier-exact-match` | — (graduated → W-205, W-202; live) |
| `search-improvements-v3` | — (graduated → W-168; steps 3–10 outstanding) |
| `mcp-adapters` | replace the retired "PLAN M5 cap" reference with SR-FETCHER's adapter cap |
| `t2-segments` | drop the stray `name:` frontmatter key |
| `wavelet-self-index` | — |
| `glassbox-sessions` | README row + B-248 still name the `sourcelist.py` closed-tuple blocker that W-178 shipped 2026-09-15 — strike it |
| `knowledge-ci` | restate the trigger without M6/M4: *"fux's own CI runs `fux ingest --check` green for two weeks"* |
| `ranking-tuning` | B-180 / README row point at W-97 (archived) and W-136 (merged) → **W-204** (judgments now arrive from its scoring pass) |

### B2 · Archive (6)

| file | why | successor in the row | repoint |
|---|---|---|---|
| `quality-endpoint-for-reranking` | trigger fired 2026-09-15 (`agreement` 0.4141), graduated → W-154, **W-154 closed FAIL 2026-09-16**; `cited_decision.py` shipped | W-154 archive row · `2026-09-16-rerank-quality-b2/VERDICT.md` · SR-RS | `archive/README.md` L184 calls it a "live successor" — fix; frontmatter `status` |
| `structure-aware-extraction` | graduated → W-144, **closed 2026-09-16** (`b = 0.15`); code-fence row now W-205; boundary argument lives in SR-DECODE §Alternatives | W-144 archive row · SR-RANKING d3 · SR-DECODE · `table-tokens-in-flen` (→ SR-RANKING d3 after A2) | 🔴 SR-DECODE's Reference block cites this file — repoint to its own §Alternatives; README/BACKLOG preambles |
| `agent-search-landscape` | keep-reason (B-187 "two live records ground on it") is false — only `BIBLIOGRAPHY.md` §11 names it, and a bibliography may name an archived doc | `BIBLIOGRAPHY.md` §11 · SR-REFER-PLANE | B-187 row deleted |
| `positioning-documents-not-code` | all six surfaces shipped; PyPI page refreshed by three releases since; the `code`→`path` rename "deliberately not done" per the file itself. ⚠ **GitHub About/topics is Arpit's `gh`** — one line left for him, not a reason to keep the file | `README.md:3` · GLOSSARY *Documents, not code* · `test_okf_bundle.py` | B-176 row deleted; README row |
| `knowledge-diff` | no trigger (README: a wish); 2026-07 "v1 / Anton corpus" era; the primitives it wants (`answer --receipt`, `fux verify`) shipped 2026-08-27 as SR-PROVENANCE | SR-PROVENANCE | B-186 row deleted |
| `research-to-spec` | same — no trigger, same era, same primitives | SR-PROVENANCE | B-185 row deleted |

### B3 · Reconcile, keep (1)

| file | the defect | the fix |
|---|---|---|
| `fetcher-routing` | It is the **pipe** proposal (2026-09-18: `decoder=` required on every URL line; `ROUTES` dropped by edge case 14). W-199 cites "the twenty edge cases in §2–§3" that are no longer there and, since 2026-09-20, revives `ROUTES` + regex routes. Both are Arpit's rulings and they compose: | **W-199 is the one spec**, and it is the pipe *plus* routing: `fetch=<stem>` mandatory and resolved (routes → claims → refuse) **and** `decoder=<stem>` required, written once at `fux add`. Proposal: add a dated note that edge case 14 is superseded by the 2026-09-20 ruling and the edge-case count is 16; add its missing README row; W-199 §"The shape" cites the pipe's §2–§3 by their real headings. **W-199 gains one DoD line: `decoder=` per the pipe ruling.** |

**After B:** 10 parked; `work/proposals/README.md` index rewritten (every file a
row — `fetcher-routing` and `quality-endpoint` had none); `BACKLOG.md` §Parked
ideas loses B-176, B-185, B-186, B-187, B-249 and repoints B-180, B-248.

---

## Definition of done

1. Every move is a `git mv` with an `archive/compare/README.md` or
   `archive/README.md` §proposals row in the same change (rules 54–58 by analogy;
   `tests/test_archive_law.py`).
2. Every record port in A2 lands **before** its doc moves (L0: the record first);
   SR-LOCKS and SR-MAINTENANCE gain the two trigger sentences named above.
3. No live document links into `archive/` afterwards: `docs/GLOSSARY.md` (two),
   SR-DECODE's Reference block, `archive/README.md` L184, `refer/freshness.py`
   docstring — `tests/test_doc_links.py`, `test_record_paths_resolve`,
   `test_archive_law.py` green.
4. The eight A1 fixes and the ten B1 fixes are applied (frontmatter status,
   fired-trigger notes, dead references).
5. `work/compare/README.md`, `work/proposals/README.md`, `work/BACKLOG.md`
   rewritten to the surviving sets; `DOC-REGISTRY.md` rows for all three plus
   `archive/`.
6. W-199 carries the pipe's `decoder=` line (B3); `proposals/fetcher-routing.md`
   carries the supersession note.
7. WORKLOG entry names the counts: compare 24 → 8, proposals 17 → 10, records
   touched, citations repointed.

## Out of scope

- Re-arguing any verdict. A row in this file changes **where** a decision lives,
  never what it says.
- `archive/v0.26-docs/` — untouched.
- The GitHub About/topics line — Arpit's `gh`, noted in the WORKLOG.
