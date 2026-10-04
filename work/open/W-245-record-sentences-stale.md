---
type: Handoff
name: W-245
description: "Eleven-plus record sentences the 2026-10-03 backlog audit found false against the code or stale against a later decision — each one a rule-26 debt a closing session left behind. One pass, one commit per record, sr-hash restamped. Ratified 2026-10-03, NOT built."
item: W-245
filed: 2026-10-03
ball: agent
---

# W-245 — the record sentences that stopped being true

**Model:** Claude Code, **Sonnet** — every edit is against a written sentence
and a named successor; nothing here needs a diagnosis.

**Why this is an item and not a drive-by.** SR-WORK-BACKLOG rule 26 says the
session that rewrites a source deletes the row; the mirror obligation — the
session that closes an item rewrites the sentences that said it was open — has
no rule and was missed about once a week. The audit behind
[W-251](W-251-backlog-audit-rulings.md) found these by reading every backlog
row against its citation. A record that says *open* about a thing that is
closed reads as authority (SR-LAW-0), so this is a coherence debt, not polish.

## Definition of done — one sentence each, then `python scripts/sr-hash.py --write <nnnn>`

| record | the sentence | what is true now | came from |
|---|---|---|---|
| [SR-WORK-ENVIRONMENTS](../../records/0052_WORK-environments.md) Consequences | the benchmark corpora *"do not exist"*; the 1.x arm is owed | built by W-139; first run filed 2026-09-12 ([`setup/fux-benchmark.md`](../setup/fux-benchmark.md)) | B-035, B-036 |
| same record, Consequences | *"Nothing mechanical enforces decision 1 yet — W-138"* | `tests/test_work_environments.py::test_no_code_under_the_four_roots_reaches_the_sandbox` | B-078 |
| [SR-CLI](../../records/0101_cli-surface.md) Consequences | *"write verbs have no `--json`"* | `fux correct --json` exists (`cli.py`) | B-031 (row kept) |
| same record, Consequences bullet on the missing-file fork | *"the fork … is the first item in OPEN-WORK"* | ruled by L12 d3 / SR-OUTPUT d20: hard error, `doctor --fix` migrates | B-139 |
| same record, §1 exit-code table | `2` *blocking (strict) — reserved* | retired 2026-09-16 (d5 as amended) | B-152 |
| [SR-API](../../records/0154_api.md) Consequences | cites **W-148** as the tracker for the renderer split | W-148 closed 2026-09-15 with the split unlanded; it is [W-247](W-247-api-renderer-split.md) now | B-040 |
| [SR-MCP](../../records/0136_mcp.md) Consequences | the MCP surface escapes the `output.toml` hard-fail *"by luck of the code path"* | `serve()` calls `output_config.load`, which raises on a missing file | B-082 |
| same record; `src/fux/mcp.py` docstring | *"postings mmaps stay resident"* vs the record's re-read-per-request | pick the record's wording until [W-249](W-249-resident-index-mcp-serve.md) lands, then both say *resident, keyed on the stamp* | B-034 |
| [SR-FETCHER](../../records/0117_fetcher.md) Consequences; `templates/cdp.py.txt` comment | *"a shipped fetcher now carries `from fux.decode.html import …`"* | neither template imports `fux` since W-199 moved decoding to `decoder=` | B-081 |
| [SR-RUNTIME-STATS](../../records/0125_runtime-stats.md) Consequences | *"owns no module, so no mechanical check can point at it"* | a `describes` row opens it (`records/README.md` §DESCRIBES, 2026-09-21) | B-058 |
| [SR-LOCKS](../../records/0140_locks.md) Consequences | *"if this record goes stale, nothing mechanical will say so"* | a `describes` row on `store/fuxdir.py` opens it | B-059 |
| [SR-ASK](../../records/0103_ask.md) Consequences | *"rewriting `bm25f.py` satisfies the check by touching this record"* | `bm25f.py` is SR-RANKING's | B-063 |
| [SR-GRAPH](../../records/0126_graph.md) decision 12 | *"a fork this record has not resolved … filed in OPEN-WORK"* | d17 ruled it (work bound, option c) | B-138 |
| [SR-MAINTENANCE](../../records/0129_hooks.md) decision 11 | the fetcher-token fork is *"an unruled fork"* | SR-FETCHER d12 ruled it 2026-08-28 | B-155 |
| [SR-CONFIDENCE](../../records/0141_confidence.md) d6, d13, d14 | d6 *"a starting value with no standing"*; d13 *"a real hole in the argument"*; d14 *"that call is Arpit's, and open"* | d17 measured the floor; the hole closed with W-214; the call was made (3a) | B-088, B-142, B-140 |
| same record, d4 | *"a sub-call … if Arpit wanted the silence, this is the one line"* | confirmed as built (W-251 §2) — strike the hedge | B-141 |
| [SR-RERANK](../../records/0138_rerank.md) d7a | *"the default stays 0.0 although the bar was met"* | graded on a second corpus: FAIL ([verdict](../regression/2026-09-16-rerank-quality-b2/VERDICT.md)); `0.0` has a measured reason | B-104 |
| [SR-WORK-QUALITY](../../records/0056_WORK-quality.md) Consequences | the ±2-query floor *"is a placeholder for a measurement"* | spent 2026-08-28 (its own veto 5) | B-111 |
| [SR-WORK-OWNERSHIP](../../records/0054_WORK-ownership.md) d11 / veto 6 | *"thirteen component records carry `owns: []`"*; three named process records own nothing | ten do; the three named now own tests, two others (0057, 0114) do not | B-055, B-056 |
| [SR-T1-ACCELERATOR](../../records/0110_accelerator.md) Consequences | *"no test imports any of them"* | `tests/test_differential_arm.py` imports `node_arm` | B-076 |
| [SR-ENRICH](../../records/0137_enrich.md) §The candidate enrichments | the candidate table is **duplicated verbatim** | one copy | B-145 |
| [SR-PII](../../records/0148_pii.md) Consequences | the block is **duplicated**; *"Owed, and filed in OPEN-WORK"* points at nothing | one copy; the regex bound is B-260 | B-232 |
| [SR-NODE-SEARCH](../../records/0153_node-search.md) Consequences | the Node arm *"cannot be called green yet … names fux-playground"* | leave until [W-252](W-252-node-arm-preregistration-2.md) files NODE-2, then rewrite | B-125 |
| `tests/test_open_work_is_not_stale.py` docstrings | *"Rule 2/3"* | pre-renumber handles; repoint to SR-WORK-OPEN-QUEUE's current numbering | B-047 |
| [SR-LAW-10](../../records/0012_LAW-10-bundled-output.md) §Alternatives | *"reopen this specific bullet if the intent was wider"* | the scope is confirmed narrow (W-251 §2): the quote is about the Node bundle in both registries; close the bullet | B-158 |
| [SR-ANSWER](../../records/0105_answer.md) d4 Consequences | re-scoring every ranked result is *"a distinct, undecided scope"* | **refused** (W-251 §2): `ask`/`find` rank from the index, `answer`'s width is a constant | B-149 |
| [SR-TYPES](../../records/0128_types-list.md) Consequences | the three source lists' format split is *"open"* | **accepted permanently** (W-251 §2): the URL line's per-line diff review is what tables would lose | B-172 |
| [SR-CONFIG](../../records/0113_config.md) d7a | a per-host key *"is promoted when a 429 is actually observed"* | re-word: *a 429 attributable to fux's own parallelism against a real host* — httpbin's always-429 fired the letter, not the spirit (WORKLOG 2026-08-27) | B-167 |
| [SR-URL-LIST](../../records/0116_url-list.md) §Considered for the set | `snapshot`, `tag`, `max_age` undecided | `max_age` **is** `ttl=` — strike it; `tag` goes in the per-document enrichment file (SR-ENRICH d11), not the line; `snapshot` stays the L3 question for SR-REFER (row B-154 kept for it) | B-154 |
| [SR-URL-FRESHNESS](../../records/0147_url-freshness.md) Consequences *Owed* | `ttl` should feed the daemon's sweep order | **only on Arpit's yes to W-251 §3 #5** — then close the *Owed* line as *not wanted; `sweep_minutes` is the clock* | B-027 |
| [SR-WORK-BENCHMARK](../../records/0053_WORK-benchmark.md) Consequences | the abstention shape's *"fourth recorded occurrence"* points at the compare doc | point at B-261 too: the gate programme's queue home closed with W-204; gates 2–9 are `unbuilt` | B-129 |
| `src/fux/derive/accel.py` docstring | *"the deep check lives in `fux doctor`"* | doctor calls the same cheap `is_fresh`; the deep check is [W-246](W-246-mechanical-gates.md)'s | B-086 |
| `CLAUDE.md` §scope | *"MCP (it is a proposal, not a backlog item)"* | `fux mcp` shipped; the sentence means the **adapters** proposal — say so | B-182 |

Then: `python scripts/sr-hash.py --write` for each record touched; both suites
whole; a WORKLOG entry. **The rows that cited these sentences are already gone
from BACKLOG.md** (W-251 §1) — this item does not touch it.

## Out of scope

- Any sentence whose truth is still Arpit's to decide (W-251 §3).
- Rewriting history in archived documents (SR-WORK-ARCHIVE).
