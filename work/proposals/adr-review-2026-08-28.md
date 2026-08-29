# ADR review — 2026-08-28

**Scope.** All 47 live records in `docs/adr/` plus `README.md`, `TEMPLATE.md`, `RULE-SINCE`, read against the register's own rules. Only `docs/adr/` was read; every claim about `src/` or `tests/` below is *record-vs-record*, not record-vs-code. Line numbers are from the files as of 2026-08-28.

**One-line verdict.** The rule set is excellent; the records don't follow it, and nothing mechanical notices. Five rules (`no history`, `ten keys`, `veto = checkable`, `References = index of the body`, `never an archived doc as grounding`) are each broken in 20–45 of 47 records. The fix is not 47 rewrites — it is ~6 new lint tests, then one bulk pass, then `RULE-SINCE` moves.

---

## 1. Systemic — the rules with no check behind them

| rule (README) | records violating | what a test would grep |
|---|---|---|
| **No history** — "the word Amended does not appear"; no `used to`, `originally`, `until <date>` | **~40 / 47.** Literal `Amended`/`AMENDED` in 0004 0009 0019 0031 0047 0049; dated `REVERSED`/`RULED by Arpit 2026-08-2x`/`BUILT 2026-08-28`/✅🔴 status logs in 0036 0044 0045 0047 0019 0032 0038; "This record previously read…" blockquotes kept in 0045 L262 0044 L246 0038 L157 | `\b(Amended|AMENDED|used to|originally|previously read|until 2026|since 2026|as of 2026|Ruled by|REVERSED|no longer)\b` in body — fail on any hit |
| **Ten keys, in order** | **9 / 47.** `amended:` in 0003 0004 0038 0045 0047; `ratified:` (not `ratifies`) in 0046 0047 0049; `built:` in 0047; `laws: [1, 3, 4]` / `[0]` instead of `[L1, L3, L4]` in 0045 0047 0049 | `test_adr_frontmatter.py` claims to check this — **it is either not running or not checking**; verify first |
| **Veto = condition + `How to check it`** | **20 / 47 have no check command at all** (0029–0036, 0038–0044, 0047–0049); 0047 has twelve conditions and zero commands; many "conditions" are events ("a real workflow is found…", "a major agent host drops MCP", "someone wants…") | fail a record whose Veto section has no `How to check` / fenced command |
| **References lists only what the body cites; never an archived doc** | **~35 / 47** list ADR-LAWS or other records the body never names; ~15 omit records/runs the body does cite; **archived docs listed or used as grounding** in 0015 (Reference *required* → `archive/v0.26/`), 0040 (Reference required → ADR-ENRICHED), 0038 0041 0044 0045 0046 0049 | parse `[ADR-X]( … )` in References, assert each name appears in §1/§2; assert no `archive/` path in References |
| **Cite by name, never number** | 0041 §1 example cites `ADR-0007`/`ADR-0019` | `ADR-\d{4}` in any live doc — README says this is already a defect |
| **Decisions numbered, unique, in order** | 0046 numbers **11, 12, 13 twice**; 0040 has **two 1–N sequences** (ADR-DECODE's "ADR-ENRICH decision 3" resolves to two things); 0045 orders 13 before 12 and 14 after "Decision 12's outcome"; 0032 uses 0, 1a–1d, 9c-i; 0029 has 8a and an unnumbered decision under *Reference*; 0007 goes 13 → 15 → 14 → 16; 0049 vetoes 1 2 3 6 4 5 | parse `**N.` under `### Decision`, assert strictly increasing and unique |
| **§1 one screen** | 17 / 47 over 90 lines; 0012 = 149, 0011 = 130, 0010 = 129 | soft warning at >80 lines between `## §1` and `## §2` |
| **Laws cited, never restated** | 0014 0018 0027 0032 0034 0040 0042 0044 0046 0047 paraphrase L2/L3/L5/L8 in prose; 0011 argues from L4 with `laws: [L1, L3]`; 0043 cites L7 for Windows portability (L7 is Python ≥3.11) | hard to lint; do in the bulk pass |
| **Transcripts real, trimmed never edited** | 0006 L99 `--json \| tail -1` cannot print `"source": "refer"`; 0030 L385 `--json` prints non-JSON; 0034 L83 `grep -n` output without line prefixes; 0021 L213 `score: 0.0000` hit; 0007 L118 `head -8` prints 9 lines; 0040 example names `0031_maintenance.md` (does not exist) and `--plan`/`--check` disagree on the same scope; 0045: **every** capture lacks the floors decisions 12–13 make required (veto 3 is violated by the record's own examples) | can't lint; rule: every block names corpus + commit or gets deleted |

**Register/README itself:** the ADR-CONFIDENCE row carries "⚠ Amended 2026-08-27 (decision 11)…" — history in the register; the ownership row for `output_config.py` says "Since 2026-08-28"; the DESCRIBES preamble says "four rows", the table has six; `built: no` on 0044 and 0049 while both records cite their own built tools/tests; 0043 is `proposed` while marked built and describing shipped behaviour.

---

## 2. Cross-record contradictions that will make code wrong

These are the ones an implementing agent trips on *today*. Ranked by blast radius.

1. **`c = t/(1−t) = 2` at `t = 0.75`.** 0.75/0.25 = **3**. 0044 L137, copied into 0045 L228. The frozen cost-of-error is mis-derived in both records; the cited paper's anchors give 3. Fix the number (or restate `t = 2/3` if −2 was intended) and say which.
2. **Output-config missing-file behaviour — three records, two states.** 0047 decision 20 says absent file → `ABSENT_OUTPUT` fallback; 0047 decision 19 (left standing) says `load()` raises; 0002 Consequences L756–773 and 0039 L207–212 still describe the hard-fail as live and `--no-output-config` as mandatory. 0047 §1 diagram + example still show the retired `[defaults]` layout ending at `BUILT_IN`.
3. **`_format` bump rule, three ways.** 0007 decision 13: `archived` added, no bump. 0009 decision 9: adding/removing a property bumps. 0010 L299: adding is a schema change. An agent adding a field cannot know.
4. **Resolution floor.** 0036 decision 14 (±2 on 50, "provisional") vs decision 19 (measured, net ≥ 6 McNemar); vetoes 9–10 and 0044 L304 / veto 5 enforce the dead one; 0012 L363 quotes the retired rule.
5. **Sealed subset** is simultaneously "does not exist" (0036 L292), "✅ built 2026-08-28" (0036 L305), and "NOT built" (README ownership row for `tools/quality-controls/`).
6. **Default fetcher for a bare URL line.** 0014 decision 5: whatever `[sources.url] fetcher` names. 0018 L217 + 0021 decision 1: `http`. 0020 §1 example sets `fetcher = cdp.py`, which under 0014 makes every bare line CDP.
7. **"Exactly two networked paths"** (0002 1d, 0008 decision 2, 0003 L244) vs the daemon that refreshes the URL tail (0032 decision 9, 0008 decision 9). Three paths, or the daemon needs a sentence. Related: 0032 "no hook ever touches the network" vs the hook-spawned runner draining a dirty list that contains `url:` ids — who consumes them is never said.
8. **Fetchers import fux or not.** 0019 L370–379 "shipped fetchers import `fux.decode`" vs 0019 L322 "zero fux imports" and veto L454 (a `fux` import is a veto). 0021's "whole fetcher" specimen lacks `validate`/`is_rate_limited` that 0019 says ships.
9. **Scorer boundary.** 0011 decision 2 "never scores" + 0012 decision 6 "nothing else computes BM25F" vs 0011's `block_bound`/`_kth_score`; both vetoes' greps are narrower than the vetoes.
10. **`doc_coverage_floor`** is a `tune.toml` key in 0038 5d + specimen and 0045 decision 13, and "NOT a key" in 0038 L523.
11. **`headings` in `ask --json`.** 0004 decision 8 says always present, no flag — then reverses below. 0005's "byte-identical to `ask --json`" identity + veto check 1 is likely false today.
12. **`hop_decay`** is a `[graph]` tune key in 0038 and a constant in 0029 decisions 10/12.
13. **Timestamp premise.** 0030 Context L94 "record has no timestamp" vs its own decision 4 "`mtime` is committed" (and forbids citing the premise); 0034 L280 cites it anyway; 0023 grounds fetch-cache disposability on the wrong record.
14. **Stamp vs manifest.** 0027 design: size+mtime match skips the hash; 0027's veto demands the hash catch an edit under a matching stamp; 0026 L136 says the hash runs every time.
15. **Query text logged or never.** 0044 decision 11 "never the query text" vs 0046 decisions 10–11 (journal of plaintext receipts incl. the question) and 0001 decision 8's two versions of L8 (network clause in the quoted text, dropped in the table).
16. **`setup` writes outside `.fux/`.** 0002 1f "`hooks` is the only verb that does" vs 0003 decision 9 / 0035 d5–d6 (`.claude/`, `.github/`, `.kiro/` by default). 0035's `fux setup` capture lists four files; its decisions write eight-plus.
17. **`[archived]` prefix on `find`.** 0037 decision 3 says `ask` and `find` show it; Consequences say `find` stdout is deliberately unmarked.
18. **Include-only directory list.** 0014 L299 "no exclusions" — false per 0022 (`!`), 0007, 0048. 0022's own veto ("a precedence rule between this file and something else") is already true via `.fuxignore`; 0048 veto 3 is already true via `fux remove`.

**Wrong cross-citations (mechanically checkable — a test could resolve `ADR-X decision N` / `veto N` against the target):** 0003→MAINTENANCE veto 7 (is 4), →URL-INGEST d4 (is 3), →CDP d8 (is 9); 0043→MAINTENANCE veto 7 (is 4), →"decision 11a with an amendment block" (does not exist); 0004→DIR-LIST d12 (has 1–5); 0001→PROVENANCE "decision C" (is 14), →CLI 1e (is 1d); 0048→URL-LIST d10 (is 4); 0042→its own d13 (is 12); 0046→its own d3 (is 9), d8 (is 7); 0036→d8 for the freeze (is 1); 0047→`ADR-FUX-DIR` (is ADR-DOTFUX); 0007→"ADR-TYPES verdict G" (no such label); 0030/0034→REFER d4's "knob that lies" (phrase absent).

---

## 3. Proposal — do it in this order

**Step 0 — find out why the existing tests are green.** `test_adr_frontmatter.py` is documented as checking the ten-key set; nine files violate it. Either the test is skipped in CI, its key check is looser than README says, or CI is red and nobody looked. This is the W-83 lesson again ("touched, not coherent") one level up — a *check* that is described but not enforced.

**Step 1 — ship the lints before the rewrite** (same-change-as-the-rule, per the currency law). One file, `tests/test_adr_lint.py`, six assertions:

- history vocabulary in body (list above) → fail
- decision numbers under `### Decision` strictly increasing, unique, integer
- Veto section contains a fenced `console`/`sh` block or `How to check it`
- every `[ADR-X]` in `## References` is named in §1/§2; no `archive/` path anywhere in References; every `ADR-X decision N` / `veto N` in any record resolves to an existing number in X
- frontmatter: exactly the ten keys + optional `supersedes`/`ratifies`; `laws:` items match `^L[1-8]$`
- `ADR-\d{4}` appears nowhere under `docs/`

Baseline these the same way freshness was — allow-list current failures per file, burn the list down in Step 2, so the tests are green from day one and *ratchet*.

**Step 2 — bulk rewrite, one record per commit, worst first.** Order by blast radius, not number: 0047, 0045, 0044, 0036, 0004, 0002, 0019, 0007/0009/0010 (the `_format` trio, one commit), 0014/0018/0020/0021 (the fetcher-default quartet, one commit), 0038, 0032, 0046, 0040, 0001. For each: delete every dated/amended sentence and rewrite the decision it was correcting *in place*; renumber; recapture or delete every transcript; rebuild References from the body; write one check command per veto. Expect each to shrink 20–40 %.

**Step 3 — three record-shape changes to TEMPLATE/README.**

- Add **`supersedes-decision:`-style pointers inside the record** — no. Instead: adopt the rule the register already implies but never states: *a corrected decision keeps its number and its text is replaced; a retired decision keeps its number with the single line "retired — see decision N"*. Today records do this inconsistently (0011 renames, 0046 duplicates, 0040 restarts).
- **Make `built` a frontmatter key** (0047 already invented one) so `test_adr_register_status.py` can assert the register column the same way it asserts `status`; today `built` is hand-maintained and wrong in three rows.
- **Move worked-instance narratives to `work/regression/` or WORKLOG** and let the record cite the run. The template's own advice ("the failure is the argument, the date is not") is right; the records keep the date because there is nowhere else obvious to put the story. Give them the place.

**Step 4 — move `RULE-SINCE` forward** after Step 2, with the comment naming this review, and say the cost out loud (per the carve-out note).

**What I would NOT do:** split the big records. 0002/0036/0038 are long because the surface is big, not because they ramble; once the history is gone they will be a third shorter anyway.

---

## 4. Per-record punch list

Two to three lines each; the subagent audits behind this have the full line-by-line detail if you want it filed under `work/open/`.

| record | top fixes |
|---|---|
| 0001 LAWS | Decision 8 is ~130 lines of L8's history with the quoted "ratified" text contradicting the ratified table on the network clause — collapse to what L8 permits/forbids. Diagrams say `L1..L7` (eight laws). Fix "decision C"→14, "1e"→1d, `alpha.2`→`alpha.3`. Check 1 greps a phrase that appears in this record, so it fails as written. |
| 0002 CLI | Consequences describe the output-config hard-fail that 0047 d20 reversed — first thing a reader hits. Fold the two dated deltas (L741–752) into 1b/1d. Add `output` to the group table, `--all`/`--no-agents` to the flag table. Reconcile 1d with the daemon and 1f with `setup`. |
| 0003 DOTFUX | Drop `amended:`. Turn the three dated "worked instances" into one numbered decision (absent file → doctor; wrong file → loader refusal). Fix three wrong cross-refs. Add `output.toml`/`.fuxignore` to every layout enumeration; drop the runtime skip ledger. |
| 0004 ASK | Rewrite decision 8 in place (`headings` present unless `sections=false`; `--sections/--no-sections`), delete the reversal block. Move confidence fields (L437–451) to CONFIDENCE, d11's `answer` clause to ANSWER. Fix References both ways; `DIR-LIST d12` doesn't exist. |
| 0005 FIND | State exactly which keys `find --json`/`ask --json` share and re-run veto check 1. Annotate or recapture L141. |
| 0006 ANSWER | L99 transcript is impossible — replace. "The surface" omits `--audit/--receipt/--journal` and the reranker. Show one real decision-10 stderr line. Veto check 2 isn't mechanical. |
| 0007 INGEST | Define *extraction carry-forward* (1b) vs *record carry-forward* (d9) — one term, two mechanisms today. Renumber 14/15/16. `.fux/runtime/skipped` both "still exists" (L520) and is deleted every run (veto 8, FUXIGNORE 11e). Fix the `head -8` example. |
| 0008 URL-INGEST | "Two fenced paths" vs the daemon in the same record. Delete d7 (restates L5). Veto check 1 greps `src/fux/` without `--include='*.py'`, so it matches the `.py.txt` templates. |
| 0009 INDEX-LIFECYCLE | Settle the `_format` rule here and make 0007 d13 / 0010 cite it. Decision 13 duplicates MAINTENANCE d7 verbatim — one owner. References wrong both directions. |
| 0010 RECORD | Replace the "illustration, not a capture" hashed record with 0008's real one (it exists). Say whether `mode: enriched` is a live value. Veto: check 2 tests *undeclared*, prose says *derivable*. |
| 0011 T1-ACCELERATOR | Rewrite d2 as "emits no score to the caller; partial scores exist only for θ" and align veto check 3. Strip L313/L392–414 narratives. Cut §1 (drop manifest capture + chart). |
| 0012 RANKING | Reground d3/veto check 4 on a live run, not "the archived baseline". Joint scorer-boundary statement with 0011. L363 quotes the retired floor. One chart, not two. |
| 0013 POSTINGS | Veto is an event ("if a phrase-query requirement arrives") — make it `grep positions`. State the 35.9-point result once. Pair the twins (ASCII has fields Mermaid lacks). |
| 0014 CONFIG | §1 + both diagrams say `[dense]` moved to tune.toml; d10 says removed. L299 "no exclusions" is false. 7a: state `DEFAULT_MAX_PARALLEL`'s number and which of policy/capability wins. |
| 0015 PORT-LIST | Reference (required) is grounded on `archive/` — the one thing forbidden. Add a ported/pending/retired column (register says `partial`, table doesn't say which). Check 2 always prints something. |
| 0016 EXTRACTED | d2 "pure function of bytes, path, links" vs `mtime` = commit time. Say once what "extraction" produces (d7 four fields vs §1 edges vs five tf fields). Five "once/now" passages. |
| 0018 URL-LIST | `fetch` default row contradicts CONFIG d5 — pick one across 0014/0018/0021. Check 1's regex matches every valid line; check 2 flags legal duplicates. `feature:` says two lists, there are three. |
| 0019 FETCHER | Worst amendment density in the set (dated rulings inside d11–13 and the veto). d2 "four functions" vs six entry points documented. L370–379 vs L322/veto on fux imports — one is stale. |
| 0020 CDP-FETCHER | §1 toml sets `fetcher = cdp.py` (makes every bare line CDP under 0014) and omits `max_parallel` (a `FuxError` under 0014 d7). Check 1's `grep -vE "...|re|os|time"` removes any line containing those substrings — vacuous. Capture shows committed `wlen`, which RANKING says never is. |
| 0021 HTTP-FETCHER | Before/After narrative → one present example. Specimen lacks `validate`/`is_rate_limited` that 0019 says ships. `score: 0.0000` hit looks invented. |
| 0022 DIR-LIST | Veto already true (`.fuxignore` is a precedence rule) — exclude it explicitly. `!` is "deprecated" yet `fux remove` writes it. Add `.fuxignore` to both diagrams. `laws:` lists L6, body uses L1. |
| 0023 CACHEDIR-TAG | State the exact bytes incl. trailing newline (byte-exactness is the whole decision). Ground fetch-cache disposability in CACHE d10, not T1. Drop LAWS from References. |
| 0024 DOCS-TABLE | "A principle was abandoned here… once held" → present tense. Is `flen` trimmed (4 vs 5 elements)? Is `docs_fields` compared ordered or as a set (0026 disagrees)? |
| 0026 RUNTIME-MANIFEST | Example says `fux.runtime.v3`; INDEX-LIFECYCLE says v5 today. "335 terms span >1 block" isn't derivable from the numbers shown. Say which verbs run the hash and when stamp short-circuits it. |
| 0027 RUNTIME-STAMP | Veto demands the hash catch what the design skips — rewrite as the size-preserving `touch -r` edit test and say so. Mermaid/ASCII/Alternatives name three different readers. L121 paraphrases L3. |
| 0028 RUNTIME-STATS | Five dated "once/now" passages incl. inside the veto. Define `mtime` once (commit time vs stat) — four records disagree. d1 "grows when ranking needs" vs veto "a fourth key is a reopen". |
| 0029 GRAPH | `hop_decay` constant here, tune key in 0038. Renumber 8a; promote the unnumbered decision under *Reference*. §1 ~100 lines with charts; captures name no corpus; veto transcript trimmed without marker. |
| 0030 REFER | Context L94 "no timestamp" vs d4 "`mtime` is committed" (d4 forbids citing the premise; L343 cites it). L385 `--json` prints non-JSON. Enumerate `Policy.mode`. `file:` vs `git:` for one source kind. |
| 0031 TYPES | Literal "⚠ Amended 2026-08-27" block. Diagram routes `!` re-include through the decoder gate; d7 says raw bytes. d10 "retires the consequence below" — consequence still stands. |
| 0032 MAINTENANCE | Numbering 0/1a–1d/9c-i — flatten. d12/d13 are ruling narratives. State the dirty-list path and who consumes `url:` entries (network fence). "Wall clock nowhere else" vs the daemon's sweep clock. `build` listed as a lock holder. |
| 0033 MERGE-DRIVER | Title says LWW on `(ver, sha)`; nothing orders by sha — rename "LWW on `ver`, equality on bytes". Fixture header is `v1`/two fields vs live `v2`/five — a header mismatch is itself a refusal case. |
| 0034 CACHE | L280 cites the premise REFER d4 declares dead. d8 "answers never read the clock" vs d7 `age_seconds` in the bundle. Is TTL `put()` gated by opt-in? `grep -n` capture without line prefixes. |
| 0035 AGENT-POLICY | `fux setup` capture: four files; decisions: eight-plus. `--no-agents` "persists" but setup is write-if-missing. Veto 3 "no command can check this"; veto 6 has no baseline byte count. |
| 0036 RS | d14 vs d19 (two floors); sealed subset three states; `recall@k` IS/IS NOT `hit@k` in one decision; unanswerable class exists/doesn't. Net-2 p = 0.50 vs "never below 0.68". Papers listed, never cited; six cited runs unlisted. §1 ~90 lines + two tables. |
| 0037 ARCHIVED-CONTENT | d3 says `find` shows `[archived]`; Consequences say `find` stdout is bare. Does `answer` prefix? `is_archived_loc()` — name says path, decision says declaration. Example C has two rows for one `loc`. |
| 0038 TUNE | L523 vs 5d on `doc_coverage_floor`. d4 is an explicit "REVERSED… *Original:*" block. `archive/proposals/` in References. Vetoes narrate "fired twice". |
| 0039 MCP | d10 text describes the `BUILT_IN["top"]` defect Consequences say was fixed. Example lacks the confidence block d10 mandates, `version: 1.0.0`. Where does `graph` fold? Veto "host drops MCP" is an event. |
| 0040 ENRICH | Section duplicated verbatim (L231–253). Two 1–N decision sequences. Example: `--plan` 2 stale vs `--check` 41/41 on the same scope; names `0031_maintenance.md`. Reference (required) → archived ADR-ENRICHED. |
| 0041 RERANK | No Context section. States the `+4` delta d7a says an informed run may not state. Cites `ADR-0007`/`ADR-0019` by number. Veto 1 is "when experiments are run". `archive/proposals/` in References. |
| 0042 DECODE | "decision 13" doesn't exist (is 12). `DecodeFailed` not a `FuxError` vs the one-flat-error contract — reconcile or name internal-only. Raise-vs-None queue rule unstated. L3 paraphrased twice. |
| 0043 LOCKS | `proposed` while built. Cites MAINTENANCE veto 7 (is 4) and "d11a with an amendment block" (doesn't exist); never cites MAINTENANCE d8, the ruling it restates. L7 cited for portability. Write the takeover as ordered steps. |
| 0044 QUALITY | `c = 2` → 3. Consequences 1/2/4 are all false per the record's own output block (recall@k computed; unanswerable class exists; floor measured). 25 vs 26 multi-relevant. d11 "never the query text" vs PROVENANCE. W-89 linked as `work/open/`, lives in `archive/`. |
| 0045 CONFIDENCE | `amended:`; `laws: [1, 3, 4]`; 13 before 12; reversed text kept as blockquote; every capture violates d1/d4/d11–13 and veto 3. `c = 2`. d14 claims ownership of `query/__init__.py` (ASK owns it). `doc_coverage` clause missing from d3's band table. |
| 0046 PROVENANCE | Decisions 11/12/13 each twice. `ratified:` key. Receipt is a hex digest in the example and an in-toto Statement in d11/15. L211 restates L8 with the network clause CLAUDE.md says was dropped. `[answer]` table doesn't exist in any config record. |
| 0047 OUTPUT | `built:` `amended:` `ratified:` keys; `laws: [1,3,4,7]`. §1 diagram/example/text = retired `[defaults]` layout ending at `BUILT_IN`. d19 (raises) left standing above d20 (fallback). "Six keys refused" — eight. Twelve vetoes, zero checks. `ADR-FUX-DIR`. A session test log inside Reference. |
| 0048 FUXIGNORE | Veto 3 already true (`fux remove` still writes `sources/dirs`). URL-LIST "d10" is d4. Shown `.fuxignore` ≠ the file the captures ran on. Seven history sentences incl. two "Arpit's ruling (2026-08-27)". |
| 0049 OWNERSHIP | `laws: [0]` (no L0). `ratified:`. Decision grounded on archived W-82. "Four rows" vs six. Vetoes 1 2 3 6 4 5, no checks; veto 5 contradicts d6 ("deliberately not mechanised"). Register `built: no` vs the tests it names. |

---

*Method: mechanical greps over all 47 files (frontmatter keys, §1 length, Mermaid/twin pairing, history vocabulary, veto/check presence) followed by four parallel full-read audits of 10–13 records each, cross-checking every `ADR-X decision N` citation against the target record. Not verified against `src/` or `tests/`.*
