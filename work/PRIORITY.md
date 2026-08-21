# PRIORITY — the one order of work, and the gate that enforces it

**How to use this file.** Read it **before** `OPEN-WORK.md`. It ranks the work
an agent may pick up. The rule is simple and absolute:

> **An agent works on the highest-ranked item that is not DONE. Nothing else.**
> If the task you were handed is not that item, you **stop and block** — write
> `work/BLOCKED.json` with `decision: "ASK"` naming the item you were asked to
> do and the item this file says comes first, and end the turn.

Set by Arpit, 2026-08-20, from the independent audit of that date. Only Arpit
reorders this list. An agent may mark an item DONE (with the evidence named in
its row) and nothing more.

## The gate — what "block" means mechanically

1. Find the first row below whose `state` is not `DONE`. That is **the item**.
2. If your task is the item, or a strict prerequisite of it named in its row →
   proceed. Announce `→ P<n>: <what>` per CLAUDE.md §Say what you are doing.
3. Otherwise → `work/BLOCKED.json`:
   ```json
   {"decision":"ASK","reason":"asked for <task>; PRIORITY.md says P<n> <name> is first",
    "questions":["Reorder PRIORITY.md, or proceed with P<n>?"],
    "safe_alternative":"P<n>","surfaced":true,"filed":"YYYY-MM-DD"}
   ```
   and stop. **Do not do the asked task "quickly first".** Do not do doc
   polishing while waiting. The `Stop` hook already refuses to end a turn with
   an unsurfaced blocker; this file gives it something to catch.
4. **Exceptions, exhaustively:** a failing CI run on `main`; a security defect
   with a repro; a one-line statement-of-fact fix made *on contact* while doing
   the item. Nothing else jumps the queue — not "it's small", not "it's related".
5. An item is DONE only when its **evidence** column is true in the repo
   (`git log`, a test, a file) — never because a session said so. Re-derive.

## The order

| # | state | item | why it is here | done when (evidence) |
|---|---|---|---|---|
| **P1** | DONE | **Make Law zero actually enforce.** `fetch-depth: 0` in `.github/workflows/ci.yml`; `test_adr_freshness.py` requires the **owning** record (via `owner_of()`), not any record; escape-hatch regex anchored to a whole line `^no ADR affected$` / `[no-adr]`; `scripts/adr-guard.sh` stops reading `.git/COMMIT_EDITMSG` (use `commit-msg` hook or `$1`); new test: each record's `**Owns:**` line ⊆ the register table and no path owned twice. | Audit §C: CI audits zero commits on a shallow clone; any record satisfies any change; the guard reads the previous commit's message. Everything downstream trusts this gate. | `1fc51a7` (+ `docs/adr/RULE-SINCE` in a follow-up, still `1fc51a7`-named). `uv run pytest -q tests/test_adr_*` green; a deliberate touch to `src/fux/query/` + an unrelated record verified to **fail** locally (both the pytest check and `scripts/adr-guard.sh` as a `commit-msg` hook), then reverted before committing. Hook installed at `.git/hooks/commit-msg`. |
| **P2** | DONE | **One bulk ADR reconciliation**, then write `docs/adr/RULE-SINCE`. Fix the 11 material drifts in the audit (ADR-MAINTENANCE R5/R6 state, ADR-CLI 12 verbs + `sources/types`, ADR-REFER "R4 cannot run", ADR-DOTFUX `cache/`→`runtime/fetch-cache/` + `fetcher/`→`fetchers/`, ADR-REFER 5a's undeclared L2 exception, `FetchError` subclass, ADR-HTTP-FETCHER and ADR-URL-INGEST self-contradictions, ADR-GRAPH unfalsifiable veto, overlapping `Owns:`, ADR-ANSWER `"source":"index"`), the register header ("only ADR-LAWS lives here", `work/adr/`), 14 dead links, 18 archive-as-reference citations, CLAUDE.md:235 / README:42 / README:101 stale facts. Reconcile OPEN-WORK · IMPLEMENTATION · INTERVIEW on R4–R6; list r5/r6 in `regression/README.md`; add r5 `ANALYSIS.md`. | A record that is wrong reads as authority; P1 only stops *new* drift. | `1fc51a7`; `docs/adr/RULE-SINCE` names it. R4–R6/regression-README/r5-ANALYSIS.md were already reconciled in `a8adb22` — verified, not redone. `sources/types` (`DEFAULT_TYPES_FILE`) and ADR-ANSWER's `"source"` field were checked and found **not** drifted — no fix needed, noted rather than silently skipped. Link/citation counts came in lower on direct grep (10 dead links, 4 archive-as-reference, not 14/18) — every one found was fixed; the audit's counts were not re-verified against its original method. `uv run pytest -q tests` green except two **pre-existing, unrelated** failures this item did not cause or touch: `tools/graph-bench` (untracked, no owning record — a concurrent session's in-progress work) and that session's own new regression run missing its README row. |
| **P3** | OPEN | **Measure R7 now, on a real 10⁵-doc corpus — not "by building M6".** Pre-register first (threshold already stated: ≤250 MB @100k; add: clone time, `git status` latency, shard churn per re-ingest, repo growth over 30 re-ingests with realistic edit rate). Run in fux-lab as a new environment. File under `work/regression/`, `VERDICT.md`. **If FAIL, the JSONL wire format is dead the way pruning is dead** — the next item becomes the wire-format compare doc, not more verbs. | Measured bytes/doc are 7.7–11.9 KB vs the paper's ~250 B; R5 already failed 44× at 100k. This is the measurement that can falsify the architecture; every feature built before it is at risk. | Pre-registration committed *before* numbers; `VERDICT.md` with PASS/FAIL/INCONCLUSIVE; OPEN-WORK prediction row updated; ADR-INDEX-RECORD / ADR-POSTINGS veto checked against the number. |
| **P4** | OPEN | **Fix the reproduced engine defects** (each with a regression test): merge driver ancestor check (`mergedriver.py:442-448` — one side == base ⇒ take the other); UTF-8 BOM (`parse.py:22` → `utf-8-sig`); 16-hex heading tripwire (`derive/build.py:173-193`, root cause `query/scan.py:31`); path NFC normalisation (`gitdir.py:153`); CRLF via `read_text`/`write_text` (`mergedriver.py:472-480`, `sources.py:57`, `graph/plane.py:69`); ~~`FetchError` → plain `FuxError`~~ **done in `1fc51a7` (P2), incidentally — it was also P2's named drift**; fetch-cache size cap + eviction (`fetchcache.py:127`). | All reproduced; all small; the merge-driver one fires on most merges in a multi-author repo, which is the design point. | Six remaining tests that fail on `main` today and pass after; CHANGELOG rows; owning records updated in the same commits (P1 enforces this). |
| **P5** | OPEN | **Close the L5 leak honestly.** Decide (compare doc, Arpit's verdict) whether `hashed` meta must also: salt term hashes per index (kills cross-index dictionary attacks, breaks nothing), hash or drop `loc`/`id` for non-git sources, and exclude `code`. Then implement the verdict. | L5 is sold as closing an ACL-mismatch leak; today a `hashed` record still carries the URL slug, a dictionary-reversible bag of words with tf, and an embedding. An enterprise reviewer finds this in an afternoon. | `work/compare/meta-privacy.compare.md` reopened with verdict; `store/writer.py` enforces it; a test proves a `hashed` record reveals neither title tokens nor URL slug. |
| **P6** | OPEN | **Wire the refer plane into `ask` and `answer`.** `answer` fetches cited docs through the consumer fetcher, re-scores passages on fetched bytes, cites a fresh sha; `"source":"refer"` in JSON; `--no-refer` keeps the index-only path. Accept ADR-REFER and ADR-ANSWER in the same change. | It is the only part of the thesis competitors do not cover cheaply, and ~1.1k LOC of it is dead code today. Ranked below P3–P5 because wiring it onto a wire format that may be dead, or onto a leaking meta, is waste. | e2e test: `answer` on the fixture returns a passage + sha that changes when the source file changes; ADR-REFER `status: accepted`. |
| **P7** | OPEN | **Put the process on a diet** (Arpit decides scope; agent proposes the diff, does not apply). Candidates: drop the `Cost:` line (49/49 `unmeasured`); merge NOW into INTERVIEW; merge IMPLEMENTATION into OPEN-WORK's deleted-row commit messages; cap doc-meta tests to those that guard a *correctness* property; stop superseding records the day they are written. | 15 of the last 20 sessions shipped no engine code; prose:code 3.2:1; 30% of tests guard prose. Both resets were followed by more governance, not less. | A proposed CLAUDE.md diff filed under `work/proposals/`; Arpit's verdict recorded; whatever he accepts, applied in one commit. |
| **P8** | OPEN | **Measure against the outside world.** 50 real org-doc questions (fux-lab, a Confluence-shaped export): Fux BM25F vs `rg` vs one commercial baseline, metric = agent task success and tokens, not p95. Then get five external users to install it and report the first failure. Fix the public README first (origin is 17 commits behind; verify what GitHub renders). | 0 stars; download pattern looks like mirrors; industry converged on grep for local code. The wedge is private, off-disk docs — prove it or move the design point. | A `work/regression/` run with the three-way numbers; five named first-failure reports in `work/`; README on GitHub matches `main`. |

## What is deliberately **not** on this list

- Any new verb, adapter, MCP, M8 item, or "enriched" build. They wait behind P3.
- Doc polishing that is not a row above. If it is not P2, it is not work.
- Re-measuring R3 on a lost corpus. R3 stands as historical; P3 supersedes it.

## Maintenance

- Arpit reorders. An agent that believes the order is wrong files the argument
  in `BLOCKED.json` (`decision: "ASK"`) — it does not reorder.
- Marking DONE: flip `state`, cite the commit sha in the evidence column, bump
  this file's `DOC-REGISTRY.md` row. Rows are **not deleted** — this file is
  the order, not a queue; OPEN-WORK remains the queue and its rows still die
  on completion.
- When every row is DONE, Arpit writes the next list. An agent with nothing
  ranked ahead of it **stops** (CLAUDE.md §Triage first), it does not invent P9.
