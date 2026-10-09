---
type: Queue
description: "The named-but-unclaimed: everything a record, proposal or compare doc says is outstanding and nobody is doing. The list only — its rules live in the record below."
governed_by: SR-WORK-BACKLOG
governed_by_path: records/0055_WORK-backlog.md
---

# BACKLOG — what has been named and is not being done

**This file is the LIST** (Arpit, 2026-09-13). Everything else — what the
backlog is, what feeds it, the shape of a row, the five classes, how an item
leaves, and the one obligation it puts on every session — is stated once in
**[SR-WORK-BACKLOG](../records/0055_WORK-backlog.md)** and is not repeated here.
Read that record before changing anything below it.

⚠ **Its length is not a signal.** [`OPEN-WORK.md`](OPEN-WORK.md)'s length is how
much is pending; this file's length is how honest the records have been. **Do
not trim it, and do not read it top-down as a priority order** —
[SR-WORK-BACKLOG](../records/0055_WORK-backlog.md) rules 3 and 28.

⚠ **The first sweep is a claim, not a proof.** Rows `B-001`–`B-241` come from
one reading of all seventy records on 2026-09-13; `B-242`–`B-244` were filed and promoted the same day (2026-09-14) — W-168, W-169, W-170; `B-245` is W-112 parked (2026-09-14); `B-175` left the same day, promoted as W-176. **Every row is individually
traceable to the sentence it cites; the set's completeness is not proven** and
no session should treat this file as exhaustive.

**Nothing here is in [`OPEN-WORK.md`](OPEN-WORK.md).** Items the records name
that the queue holds instead carry no row here: W-87, W-136, W-140,
W-144, W-145, W-146, W-147, W-148, W-154, W-155, W-157, and — promoted
from rows here on 2026-09-14 — W-163 (eight doctor rows), W-164 (four gates),
W-165 (three CLI fixes), W-166 (carry-forward invalidation), W-168 (search improvements), W-169 (`fux inspect`), W-170 (cage search leg), W-176 (the nine abstention gates, from B-175); from rows here on 2026-10-04 — W-253 (B-100, B-146, B-151), W-254 (B-150), W-255 (B-260), W-256 (B-098, B-113, B-103 and the loopback halves of B-102/B-124), W-257 (B-108–B-110), W-258 (B-101 and the live halves of B-102/B-124).

---

## `unbuilt` — a ratified decision the code does not implement

| id | what is outstanding | named in | what closes it |
|---|---|---|---|
| B-002 | The dirty list "alone buys no speedup" — the runner still calls today's `fux ingest`, which walks the corpus; the list's input is unused | [SR-MAINTENANCE](../records/0129_hooks.md) decision 1a, point 3 | Arpit, on [W-267](open/W-267-ingest-split-remeasure.md)'s re-measure (W-264 retired 2026-10-09) |
| B-006 | The `enriched` ingest mode has no sign-off — "the sign-off half has not been given"; grade `6` `INFERRED` stays reserved (ex-B-005) | [SR-ENRICH](../records/0137_enrich.md) folded decision 6 · [SR-EXTRACTED](../records/0115_extracted-mode.md) decision 3 | Arpit: [W-251](../archive/open/W-251-backlog-audit-rulings.md) §3 #1 recommends retire the mode, KEEP grade 6 for inferred edges |
| B-031 | The write verbs have no `--json`; the shape for *recorded, fetched, ingested* is now DECLARED, not shipped ([plan](proposals/build-plan-2026-10.md) §1, W-251 §4) | [SR-CLI](../records/0101_cli-surface.md) Consequences | A caller: a `fux_add` MCP tool or an `api.add` proposed in a record — then the declared shape is built |
| B-041 | `.rst`, `.adoc` and `.org` keep their own regexes in `extract.py` and get no fence handling; approach ruled — one fence-aware module both consumers import ([plan](proposals/build-plan-2026-10.md) §2) | [SR-DECODE](../records/0139_decode.md) decision 14 ⚠ | The first corpus or golden seed in one of the three formats, then the plan's §2 as a `W-nn` |
| B-261 | Abstention gates 2–9 are ruled (option (a), 2026-09-14) and unbuilt; gate 2 INCONCLUSIVE → [W-265](open/W-265-abstention-research.md); gates 4 and 3 are replayable next, 5/8 need captures, 6 waits on the graph value | [`abstention-gates`](compare/abstention-gates.compare.md) · [SR-CONFIDENCE](../records/0141_confidence.md) decision 3a | One `W-nn` per gate, in the ruled order |
| B-273 | Title-H1 generator slip: SOPs carry a template H1 unequal to their title (0.803–0.816 vs `core_share` 0.80) — 14–143 unplanted misfits per rung | [SR-INSPECT](../records/0156_inspect.md) decision 24 ⚠ · [gen-4 run](regression/2026-10-05-ladder-gen4-rebuild/report.md) | The **next** test-data generation's generator emits an H1 equal to the front-matter title |

---

## `ungated` — a stated rule nothing mechanically checks

| id | what is outstanding | named in | what closes it |
|---|---|---|---|
| B-259 | Display width is not `len()`: a path holding a CJK character or emoji renders two columns and can still wrap. "No test covers it" (ex-B-134); approach ruled — `unicodedata` column width, no dependency ([plan](proposals/build-plan-2026-10.md) §3) | [SR-CLI](../records/0101_cli-surface.md) decision 12 ⚠ | A session touching `progress.py` builds the plan's §3 with its test |

---

## `unmeasured` — a live default, constant or claim with no measurement behind it

| id | what is outstanding | named in | what closes it |
|---|---|---|---|
| B-089 | `title`, `path` and `ctx` "are carried forward from nothing — defensible starting points, not measured optima" | [SR-RANKING](../records/0111_ranking.md) decision 3 ⚠ | A pre-registered tuning run over the three weights |
| B-090 | `[ranking] expand_weight` ships at `0.2`, "ratified by Arpit and unmeasured on any corpus in this repo" | [SR-TUNE](../records/0135_tuning.md) decision 12 ⚠ · [SR-EXPAND](../records/0149_expand.md) decision 5 | A graded run sweeping `expand_weight` on a rung |
| B-091 | PPR "has three constants and no measurement behind two of them" — `ITERATIONS = 3` and `LAZINESS = 0.5` are conventional | [SR-GRAPH](../records/0126_graph.md) Consequences ⚠ | A pre-registered measurement of iterations and laziness |
| B-093 | ARC-vs-LRU "does not rest on a from-scratch Fux measurement" — post-hoc, on a synthetic trace, where the trigger asked for a real workload | [SR-CACHE](../records/0131_cache.md) Consequences ⚠ | A hit-rate measurement on a real usage journal — which waits on B-268 (no query log is collected) |
| B-094 | The accelerator "gets slower in proportion to the spread… it is spent, not free, and the amount must be measured under SR-RS with a frozen pre-registration" | [SR-TUNE](../records/0135_tuning.md) Consequences ⚠ | A pre-registered measurement of the spread's cost |
| B-095 | Narrowing what counts as a document is a ranking change and "this record does not claim it is an improvement. Nothing has been measured" | [SR-TYPES](../records/0128_types-list.md) Consequences, first ⚠ | A measured run of the type filter against ranking |
| B-096 | The `max_phrases = 32` evidence is "post-hoc and single-corpus" | [SR-EXTRACTED](../records/0115_extracted-mode.md) decision 9 ⚠ | A pre-registered measurement on another corpus |
| B-097 | The smallest corpus at which the doc-major argument stops holding "has never been measured" | [SR-POSTINGS](../records/0112_postings.md) Context ⚠ | A measurement, if the argument is contested |
| B-099 | The retired 100 000-document packed-size promise "has no successor"; the section-size run has a number (25.4 → 50.4 MB at rung-10000) and no record sets a bar | [SR-INDEX-LIFECYCLE](../records/0108_index-lifecycle.md) Consequences · [SR-POSTINGS](../records/0112_postings.md) Consequences | Arpit: W-251 §3 #9 — accept +98.4 %, an R-series promise or not; else a `W`-id bar under W-236 |
| B-105 | The cross-encoder refusal "stands anyway, because nobody has measured the quantity that decides it" — gap tightness over ~20 similar documents | [SR-RERANK](../records/0138_rerank.md) veto 1 ⚠ | Measure drift and adjacent gaps on a real cross-encoder |
| B-106 | Nobody has measured how many undeclared negations a real corpus contains — *"this approach was abandoned"*, *"unlike Y"* | [SR-RERANK](../records/0138_rerank.md) veto 1 ⚠ | Count undeclared negations in a real corpus |
| B-107 | An exact top-5 tie is broken by `docidx` rather than relevance, "and 4.38 % of queries contain one" | [SR-RERANK](../records/0138_rerank.md) veto 5 ⚠ | A relevance-bearing tie-break |
| B-112 | The `judged` series stays internal until 5–10 % of its scores are cross-checked against a human; no cross-check exists | [SR-WORK-QUALITY](../records/0056_WORK-quality.md) decision 10 | Human-adjudicate 5–10 % of judged scores, then publish |
| B-115 | Decision 15 "remains unmeasured" — no endpoint touched `pdf`/`rtf`/`csv`/`jsonl` heading emission; decision 16 is "INCONCLUSIVE, not a null" | [SR-DECODE](../records/0139_decode.md) Consequences ⚠ and 🔴 | Endpoints over those four formats, and over `phrases` noise |
| B-116 | `toml`, `yaml` and `ini` emit no filename title — "pre-existing… not changed here. Recorded so it is a decision next time" | [SR-DECODE](../records/0139_decode.md) decision 11a ⚠ | Measure, then emit a title or rule it out |
| B-117 | The repeated table header is scored, so every band of a table gains a uniform uplift against non-table passages | [SR-REFER](../records/0127_refer-plane.md) decision 25 ⚠ | Measure the uplift, or stop scoring the repeated header |
| B-119 | The refer plane fetches serially, so the latency bound "is a statement about the source's latency at k=10, not about fux" | [SR-REFER](../records/0127_refer-plane.md) veto 1 ⚠ | Parallel fetch, or re-measure and re-register the bound |
| B-121 | "Raising the row limit is also an index-size change, not only a latency one" | [SR-TABULAR](../records/0150_tabular.md) Consequences ⚠ | A measured index-size budget for tabular corpora |
| B-122 | Nothing has been measured about how often anyone reaches for `.fuxignore`'s `!` re-inclusion, which admits an undecoded format as raw bytes | [SR-FUXIGNORE](../records/0144_fuxignore.md) Consequences ⚠ · [SR-TYPES](../records/0128_types-list.md) Consequences ⚠ | Measure `!`-admitted formats across real repos |
| B-123 | The starter PII scan was "a false-positive check on one technical corpus, not a recall measurement — nothing here contains a real identifier" | [SR-PII](../records/0148_pii.md) decision 12a | A recall measurement on a corpus with real identifiers |
| B-127 | The corpus behind SR-ANSWER decisions 11–13 was retired: "the run stands as filed and cannot be re-run where it was run" | [SR-ANSWER](../records/0105_answer.md) Reference ⚠ | A live graded corpus to re-measure the three decisions on |
| B-132 | Two RRF arms at `--top 5` fuse shallowly: a document ranked 6th in both arms is invisible to the fusion | [SR-EXPAND](../records/0149_expand.md) Consequences | A deeper fusion decision, or a higher `--top` |
| B-135 | The double-load hazard "is unchanged and still unmeasured" — Copilot sees two same-name skill copies | [SR-AGENT-POLICY](../records/0132_agent-policy.md) decision 14a ⚠ | Observe or rule out a duplicate-name error in Copilot |
| B-245 | The vector plane (`fux embed`, `.fux/vectors/`, `--qvec`, RRF) — closed unbuilt 2026-09-14: its gate can never fire; `tools/vector-gate/` held by the fallback until `SR-VECTORS` | [SR-RS](../records/0133_predictions.md) d19, d20 · archived W-112 | **Reopen only when both hold:** a rank-contract corpus **and** doc2query's ceiling measured ([W-257](open/W-257-enriched-rung.md)) |
| B-262 | Cascade ranking is "unbuilt and unmeasured, deliberately" — stage-1 `recall@k` is the gate; its data does not exist: no SR-WORK-TESTDATA row names tabular documents, so a T15 comes first (ex-B-044) | [SR-CHUNKING](../records/0151_chunking.md) §What is NOT done · [SR-TABULAR](../records/0150_tabular.md) Consequences 🔴 | A tabular T-row and seed tables, then stage-1 `recall@k` > ~0.98 |

---

## `unruled` — a fork named and not decided. Only Arpit closes one

| id | what is outstanding | named in | what closes it |
|---|---|---|---|
| B-145 | Of four candidate enrichments two are served by other means (expansion → doc2query `ctx`, `--expand`, mined pairs d18; retirement → `superseded_by:`); inferred edges and richer embeddings remain, "None is approved" | [SR-ENRICH](../records/0137_enrich.md) §The candidate enrichments | Both behind B-245's reopen trigger; a ruling per candidate when it fires |
| B-162 | L4 lost its co-guard: a query-time model is held off only by SR-RERANK's determinism refusal — "a decision, and decisions are what an SR is designed to supersede" | [SR-LAW-2](../records/0004_LAW-2-zero-cost.md) §2026-09-06 amendment, trade 2 | Arpit (a Law), **parked by him 2026-10-04**: the draft is in [W-251](../archive/open/W-251-backlog-audit-rulings.md) §3 #18 |

### Parked ideas — [`work/proposals/`](proposals/README.md)

*Every file in that directory has a row here and only here; the proposal keeps
its own lifecycle, its own graduation trigger, and its own README row.
[`search-improvements-v3.md`](proposals/search-improvements-v3.md) carries no
row: what remains of it is **W-168** in the queue.*

⚠ **`structure-aware-extraction.md` was the other exception and it ARCHIVED on
2026-09-20** (W-206 B2) — W-144 closed 2026-09-16, and its boundary argument
lives in [SR-DECODE](../records/0139_decode.md) §Alternatives. **Five rows left
this table in the same change** — B-176, B-185, B-186, B-187 and B-249 — each
with its proposal.

| id | what is outstanding | named in | what closes it |
|---|---|---|---|
| B-180 | Ranking tuning — the instrument, not the optimiser. **The thesis shipped** (the ladder, `tools/golden-score`, PRE-REGISTRATION/VERDICT); marked `graduated` 2026-10-03. Kept because SR-LAWS and SR-TUNE ground on its §8 survey | [`ranking-tuning.md`](proposals/ranking-tuning.md) | Archives when SR-LAWS, SR-TUNE and BIBLIOGRAPHY repoint their citations (W-245's shape) |
| B-181 | T2 segments — nothing was ever built; the old veto is now a trigger. ⚠ p95 at rung-10000 has read above 150 ms on uninterleaved runs, so the trigger now measures **after** W-242 Tier 2 | [`t2-segments.md`](proposals/t2-segments.md) | An interleaved warm p95 above 150 ms at rung-10000 once W-242 Tier 2 has landed |
| B-182 | MCP as the adapter endgame — one protocol instead of per-app adapters, on the org's own auth | [`mcp-adapters.md`](proposals/mcp-adapters.md) | The first MCP-gateway design partner, or a fourth adapter request |
| B-183 | Knowledge CI — PRs fail when the index is stale; decisions the diff contradicts surface as cited review comments | [`knowledge-ci.md`](proposals/knowledge-ci.md) | fux's own CI runs `fux ingest --check` green for two weeks (the proposal's 2026-09-20 trigger) |
| B-184 | Wavelet-tree self-index — the preserved option C of the keyspace compare; its trigger named P5, retired with plan revision 1 | [`wavelet-self-index.md`](proposals/wavelet-self-index.md) | A law change, or runtime inflation measured as the bottleneck (ex-P5 / R5's successor) |
| B-248 | Glassbox sessions — counts and cross-session joins, which fux does not do; the sketch is materialise-then-index. ⚠ The `fetch=` closed-tuple blocker is **struck** (W-178, then W-199) | [`glassbox-sessions.md`](proposals/glassbox-sessions.md) | A second event-stream source is asked for |
| B-250 | Code pattern recognition — a committed, deterministic clone-and-shape map for code, as a separate distribution; the query and call-graph halves are a buy (ast-grep, tree-sitter graph servers) | [`code-pattern-recognition.md`](proposals/code-pattern-recognition.md) | A second ask for a code-shape answer that must be committed at a sha |
| B-251 | Cross-model agent guides — the shipped guides load the same everywhere but trigger and comply differently per model; five deterministic levers, eval matrix first, and no in-file "if you are model X" branch | [`cross-model-agent-guides.md`](proposals/cross-model-agent-guides.md) | A filed mis-trigger or broken rule on a non-Claude or smaller model, or Arpit asks for the matrix |
| B-253 | The measurement plan — the `unmeasured` rows measurable now, pre-registered; §2/§4-lab/§8 → W-256, §7 → [W-257](open/W-257-enriched-rung.md), §4-live → [W-258](open/W-258-live-network-captures.md) | [`measurement-plan-2026-10.md`](proposals/measurement-plan-2026-10.md) | Per remaining section: data in hand and a decision waiting, then a `W-nn` |
| B-268 | A query log, parked — "legal to collect and still not collected"; the opt-in journal (SR-PROVENANCE d10) is the only lawful collector and none runs; ruled *not now* 2026-10-04 (ex-B-137) | [SR-LAWS](../records/0001_LAWS.md) decision 8 · [SR-LAW-9](../records/0011_LAW-9-use-record.md) Consequences | Arpit: a consumer whose journal may be graded (`informed`, SR-RS d11) |
| B-269 | The build plan — the `unbuilt`/`ungated` rows whose approach was ruled 2026-10-04 and whose build nobody is about to start (B-031, B-041, B-259): key files, DoD, size, model, the law each must respect | [`build-plan-2026-10.md`](proposals/build-plan-2026-10.md) | Per section: its own trigger fires, or a session is about to build it — then a `W-nn` |
| B-270 | `fux enrich` plans the queue's *nothing readable* documents (W-248), but nothing indexes what it writes for them: ingest drops an unreadable document before extraction | [SR-ENRICH](../records/0137_enrich.md) d4 | the `enriched` mode ruling (W-251 §3 #1) |
| B-271 | SR-LAWS decision 7 still says `concurrent.futures` keeps *"the zero-dependency guarantee untouched"* — a guarantee L2's 2026-09-06 amendment withdrew; a Law record changes only on Arpit's word, so `tests/test_withdrawn_claims.py` holds it `xfail(strict)` | [SR-LAWS](../records/0001_LAWS.md) d7 | Arpit's word on one sentence (e.g. *"…so no runtime dependency is added"*) |
| B-272 | Index stores — the index may live in a database outside any repository, not only in git: one store boundary over today's reader/writer seam, `git` and `sql` stores, one writer, readers sync locally so `fux ask` stays offline | [`index-stores.md`](proposals/index-stores.md) | Arpit rules F1 (sync vs direct query), F2 (first backend), and names the first index outside a repo |

---

## `cost` — a consequence accepted deliberately. These never graduate

⚠ **A row here is an argument that has already been had.** It is written down so
the next session finds the argument instead of reopening it. It leaves when the
cost is paid, or when the decision that accepted it is reopened —
[SR-WORK-BACKLOG](../records/0055_WORK-backlog.md) decision 3.

| id | the cost accepted | named in | what would end it |
|---|---|---|---|
| B-188 | Every commit up to `ce425c7` is no longer re-auditable by the freshness gate — "the largest such cost yet" | [SR-WORK-OWNERSHIP](../records/0054_WORK-ownership.md) decision 10 · [`records/RULE-SINCE`](../records/RULE-SINCE) | Nothing; the cost is spent and recorded |
| B-189 | The benchmark baseline reaches no frozen report — five earlier benchmark-shaped runs stay incomparable, deliberately not retrofitted | [SR-WORK-BENCHMARK](../records/0053_WORK-benchmark.md) Consequences 🔴 | Nothing — retrofitting is the failure the rule prevents |
| B-190 | A hashed key is not anonymity: statistics about a document can still identify it, and `terms` is not salted — ex-L5 was RETIRED 2026-09-20 (W-194), so the exposure stands under L3 outright | [SR-LAW-3](../records/0005_LAW-3-content-never-durable.md) Consequences ⚠ · [SR-RECORD](../records/0109_index-record.md) Consequences | Nothing available; the law refuses to claim closure |
| B-192 | An answer is impossible when the source is gone; the acquired plane is the mitigation and it is opt-in, so the default really can fail to answer | [SR-LAW-3](../records/0005_LAW-3-content-never-durable.md) Consequences | Only a change of default |
| B-193 | A fleet pinned to 3.9, 3.10 or 3.11 cannot run fux at all — "a real deployment cost in exactly the environments fux targets"; the floor is 3.12 since 2026-09-28 | [SR-LAW-7](../records/0009_LAW-7-python-312.md) Consequences | Only lowering the floor |
| B-194 | The AOL-2006 grounding is overridden, not refuted: the risk is accepted and "the mitigation is confinement alone" | [SR-LAW-9](../records/0011_LAW-9-use-record.md) Consequences ⚠ | A re-ruling |
| B-195 | L6 cannot be fully mechanised — a grep finds the word, not a paragraph describing an index as if it were a database | [SR-LAW-6](../records/0008_LAW-6-say-index.md) Consequences ⚠ | Accept as judgement, or a reviewer checklist |
| B-196 | Precedence "is judgement and will stay judgement" — no parser reads *does this record contradict L3* | [SR-LAW-0](../records/0002_LAW-0-authority.md) §What is gated | Nothing — named as permanently ungated |
| B-197 | A consumer who never upgrades keeps their old module tree: the prune runs on a version difference, so nothing reaches a repository whose owner stopped running fux | [SR-LAW-10](../records/0012_LAW-10-bundled-output.md) decision 8 ⚠ | A prune that runs without a version difference |
| B-198 | `content_sha` "tells you THAT a record moved, never what moved", and it is not a signature | [SR-WORK-OWNERSHIP](../records/0054_WORK-ownership.md) decision 12 ⚠ | Nothing proposed; it is a drift detector only |
| B-199 | A record describing many components while owning none "is a smell, not an error — not mechanised", because any threshold would be arbitrary | [SR-WORK-OWNERSHIP](../records/0054_WORK-ownership.md) decision 6 ⚠ | A non-arbitrary threshold, if one exists |
| B-200 | git does not invoke a content merge driver for an add/add — "a real limitation and it is not worked around" | [SR-MERGE-DRIVER](../records/0130_merge-driver.md) Consequences ⚠ | Nothing; the printed `fux ingest` remedy is the fix |
| B-201 | A killed lock holder leaves a file only a human clears, and `wedged` "is left unresolved on purpose" | [SR-LOCKS](../records/0140_locks.md) Consequences | Nothing automatic may break a lock |
| B-202 | An analyzer bump "owes a full re-ingest on every existing index"; until it runs, the reader refuses the committed shards | [SR-INDEX-LIFECYCLE](../records/0108_index-lifecycle.md) Consequences | Accepted: `--full` is the migration |
| B-203 | Decision 9 and the `[index]` digest each change committed bytes on the next ingest of every existing corpus — a one-off re-extraction | [SR-EXTRACTED](../records/0115_extracted-mode.md) Consequences ⚠ · [SR-INGEST](../records/0106_ingest.md) decision 15a ⚠ | Accepted; a release note |
| B-204 | A new skip dirties the working tree, including on the hook path — "re-ingest is safe to run on a hook" now means "and it may stage a `.fuxignore` line" | [SR-INGEST](../records/0106_ingest.md) Consequences ⚠ | Exclude the generated blocks on the hook path |
| B-205 | `.fux/.fuxignore` is both ingest's input and its output: "what is given up is the weaker property that the file's content is independent of history" | [SR-INGEST](../records/0106_ingest.md) Consequences ⚠ | Accepted — convergence after one run is the guard |
| B-206 | The generated `.fuxignore` blocks make the file "as long as the corpus is unindexable" — hundreds of lines on this repo | [SR-FUXIGNORE](../records/0144_fuxignore.md) Consequences | Hand-written patterns; the lever is the consumer's |
| B-207 | A repo running no daemon "has no tail coverage at all"; `fux ingest --refetch-all` is the whole remedy and somebody has to remember it | [SR-URL-INGEST](../records/0107_url-ingest.md) decision 9 ⚠ | A default sweep, if one is ever ruled |
| B-210 | `update=never` with `keep=false` is "legal, lossy, and DISCLOSED rather than refused" — nothing for `answer` to verify a citation against | [SR-URL-LIST](../records/0116_url-list.md) decision 14b | Accepted; `doctor` names the lossy lines |
| B-211 | Editing `[sources.url]` later "still does not reach an existing line, and cannot" — the cost of every generated line stating everything | [SR-URL-LIST](../records/0116_url-list.md) decision 12 ⚠ | Accepted; re-run `fux add` per line |
| B-212 | A duplicate URL line "is invisible — a reviewer cannot see from the diff that a line was already present" | [SR-URL-LIST](../records/0116_url-list.md) Consequences | Accepted under decision 4 |
| B-213 | `rm -rf .fux/acquired` loses the only local copy of bytes that may not be re-fetchable, "and the loss is silent"; a fourth safeguard is deliberately absent | [SR-DOTFUX](../records/0102_fux-directory.md) Consequences ⚠ | A warning when the plane disappears |
| B-214 | A shell page indexes as a shell page — "the accepted cost of determinism"; the remedy is a human writing `fetch=cdp` on that line | [SR-HTTP-FETCHER](../records/0119_http-fetcher.md) Consequences | Nothing automatic; detection was held, not taken |
| B-215 | A rendered page "is no longer obtainable from this file" — a consumer wanting the DOM of a client-side-rendered page has to write it | [SR-CDP-FETCHER](../records/0118_cdp-fetcher.md) Consequences | Accepted; the retired implementation is archived |
| B-216 | The abandoned fetch thread "keeps running until the consumer's own socket timeout fires"; fux will not reach into consumer code to kill it | [SR-REFER](../records/0127_refer-plane.md) §`timeout_seconds` ⚠ | A fetcher-side bound in `[sources.url.config]` |
| B-217 | A cached copy can be served for a document the reader has since lost access to, and "nothing currently detects the case"; `no_cache` is advisory | [SR-REFER](../records/0127_refer-plane.md) veto 5 ⚠ · [SR-CACHE](../records/0131_cache.md) Consequences | Mandatory `no_cache` for access-controlled sources |
| B-218 | A local `.html` "loses its line range as a consequence" — the raw HTML had real lines and the converted Markdown does not | [SR-REFER](../records/0127_refer-plane.md) decision 24 ⚠ | A source-line map through decode |
| B-219 | Markdown as the intermediate throws structure away: a PDF line `# 3 of 7` or a CSV cell `#1 priority` "is promoted to a heading and weighted above body" | [SR-DECODE](../records/0139_decode.md) decision 2 ⚠ | Nothing — a reopen-trigger was offered and declined |
| B-220 | An overridden decoder makes the index a function of consumer-edited code — "named here so it is not discovered later" | [SR-DECODE](../records/0139_decode.md) Consequences ⚠ | Accepted cost of the consumer seam |
| B-221 | The type default "moves whenever a built-in decoder is added — a real coupling"; for a repo that ran setup, the list freezes instead | [SR-TYPES](../records/0128_types-list.md) Consequences ⚠ | A loader refusal or doctor check on a frozen list |
| B-222 | A generated format nobody has heard of arrives indexed; "the denylist is never finished" | [SR-TYPES](../records/0128_types-list.md) · [SR-FUXIGNORE](../records/0144_fuxignore.md) Consequences | Nothing; the allowlist is the structural answer |
| B-223 | The archived declaration "is only as honest as the person writing it. A derived signal cannot be forgotten; a declared one can" | [SR-DIR-LIST](../records/0120_dir-list.md) Consequences ⚠ | Accepted trade for consumers whose layout differs |
| B-224 | `-priority` is UNREACHABLE in the declared tie-break: `[priority]` multiplies the score, so it never separates two candidates | [SR-RANKING](../records/0111_ranking.md) the tie-break ⚠ | A `[priority]` declaration that does not multiply |
| B-225 | `support` "cannot be a corpus-wide count without breaking the law — the better number is not available honestly" | [SR-T1-ACCELERATOR](../records/0110_accelerator.md) Consequences ⚠ | Nothing; the law is worth more than the number |
| B-226 | The reranker reads the working tree at query time, "so its output is not a pure function of the committed index" | [SR-RERANK](../records/0138_rerank.md) decision 7 ⚠ | Nothing; it is why the default cannot flip silently |
| B-227 | Enrichment provenance "downgrades from measured to declared" — `model:` is a claim nothing here can confirm | [SR-ENRICH](../records/0137_enrich.md) decision 3 ⚠ | Accepted cost of decision 1 |
| B-228 | An enrichment written under a superseded sha "is invisible rather than wrong. This is the whole of the gap" | [SR-ENRICH](../records/0137_enrich.md) decision 13 | Accepted; a second hash is refused as drift-prone |
| B-229 | The mean assembled bytes went 2 517 → 6 467 over 43 graded queries — "a cost, reported rather than asserted away" | [SR-ANSWER](../records/0105_answer.md) decision 13 | Callers set `[refer] budget`, or a measured default |
| B-230 | A well-formed refusal rule that is wrong about the world silently drops real documents, "and nothing can" catch it | [SR-REFUSAL](../records/0146_refusals.md) Consequences | Reviewing the skip list; no mechanism is proposed |
| B-231 | Redaction is irreversible and an over-broad rule "leaves nothing looking wrong"; `doctor` cannot see it | [SR-PII](../records/0148_pii.md) Consequences | An instrument that detects over-broad rules |
| B-233 | A document's PATH cannot be redacted, so a matching path is only reported — "a consumer's call, never fux's" | [SR-PII](../records/0148_pii.md) decision 19b | Nothing in fux; the consumer renames or ignores |
| B-234 | The agent policy "is prose, and prose is not enforceable. Fux cannot verify that an agent obeyed it" | [SR-AGENT-POLICY](../records/0132_agent-policy.md) Consequences | Nothing; the guarantee is that all were told the same |
| B-235 | Copilot reads `.claude/skills`, so it loads `fux-enrich` — the skill SR-ENRICH confined to one surface. "Nothing fux can do closes this. Recorded, not fixed" | [SR-AGENT-POLICY](../records/0132_agent-policy.md) decision 13 | Nothing available |
| B-236 | Fux owns four third-party formats it does not control — "a real maintenance liability… none of them makes the liability go away" | [SR-AGENT-POLICY](../records/0132_agent-policy.md) Consequences ⚠ | Nothing; periodic re-reading of the vendor docs |
| B-237 | `separation` is an ordinal signal, not a calibrated probability; since W-214 removed the reject rule the gap binds only the `weak` label — "a rule needing none" has arrived for the gate | [SR-CONFIDENCE](../records/0141_confidence.md) decision 6 ⚠, decision 17 | A calibrated probability, if the label is ever to gate |
| B-238 | A stated `describes` claim's reach is file-scoped, so a doctor change "no longer mechanically opens SR-PII — strictly weaker" than what it replaced | [SR-DOCTOR](../records/0152_doctor.md) Consequences 🔴 | Key-scoped `describes` — see B-060 |
| B-252 | Record↔code coherence is judgement — prose self-contradiction inside one record ("the W-83 class", confirmed 2026-10-04 to mean THAT class only; row/frontmatter or code/docstring drift is gateable and is not it): each source rules it "cannot be mechanised" (ex-B-048/049/050/053/061/062/071) | [SR-LAW-0](../records/0002_LAW-0-authority.md) §What is gated | Nothing — permanently ungated |
| B-254 | Term-hash collision detection is complete only on a full run; a collision involving a carried-forward document is not detected on a delta — "`--full` is the complete check" (ex-B-083) | [SR-INGEST](../records/0106_ingest.md) Consequences | Accepted; `fux ingest --full` is the remedy |
| B-255 | No law forbids transmitting a use record — the transmission clause was put to Arpit and declined; "what holds today is the code, not a law" (ex-B-159) | [SR-LAW-9](../records/0011_LAW-9-use-record.md) §The gap the ratification opens | A re-ruling, or `.fux/runtime/` becoming shareable by any route (SR-LAWS decision 8's tripwire) |
| B-256 | A single unbreakable token comes back oversized and the assembler refuses it — "That is correct, and it is now the only case"; `answer` falls back to the index (ex-B-169) | [SR-CHUNKING](../records/0151_chunking.md) decision 6 | A rung below `word`, if ever wanted |
| B-257 | A caller can supply a misleading `--expand` term — "a trust boundary this record does not close"; the caller is the user's own agent, the receipt records the term, and `[mcp]` can disable it (ex-B-173) | [SR-EXPAND](../records/0149_expand.md) Consequences | Accepted; a trust model only if a shared server exposes `expand` |
| B-258 | A URL skip is recorded nowhere and prints on every networked run — "Accepted: a repo has a handful of dead URLs, not hundreds"; the dead-URL report counts streaks (ex-B-012) | [SR-FUXIGNORE](../records/0144_fuxignore.md) Consequences ⚠ · [SR-INGEST](../records/0106_ingest.md) Consequences | Accepted; `url-state.json` is where repeat failure lives |
| B-263 | `verify`, `--why`, `--receipt` and `--journal` are OUT OF SCOPE on the Node reader, declared rather than missing — nothing structural forbids them; nobody has asked for verification where no Python runs (ex-B-033, ruled 2026-10-04) | [SR-NODE-SEARCH](../records/0153_node-search.md) decision 25 (via W-245) | A consumer asks for verification on the Node plane; that amends d25 |
| B-264 | `fux pii-probe` is not a verb: SR-CLI veto 6 wants a caller, and the `fux-pii` skill carries a reduced probe (plain text, digests not values) — the engine-side probe stays repo tooling (ex-B-038, ruled 2026-10-04) | [SR-PII](../records/0148_pii.md) decision 20 | A consumer asks to probe decoded or `url:` documents, which only the engine can do |
| B-265 | The TTL store's cap is a design default, not a measured one — `fux.toml [refer] fetch_cache_max_bytes` (500 MiB in the template); a consumer turns it and no measurement picks a byte cap (ex-B-092, accepted 2026-10-04) | [SR-CACHE](../records/0131_cache.md) decision 9 | Nothing; the key is the lever |
| B-266 | `separation` stays the `grounded`/`weak` quantity; its floor is not recalibrated for RRF or any arm — d17 measured it does not carry correctness, so a calibrated floor would be a calibrated non-predictor (ex-B-114, ruled 2026-10-04) | [SR-CONFIDENCE](../records/0141_confidence.md) decision 17 | `doc_coverage_floor` measured (W-256 §2) replaces it |
| B-267 | Kiro's twelve pointers (10 985 B) are ambient on a CLI without inclusion modes; the exit is `[agents] install` without `kiro`; a per-CLI-version switch is refused — fux cannot observe the CLI version; no `--agents` flag exists (ex-B-170, ruled 2026-10-04) | [SR-AGENT-POLICY](../records/0132_agent-policy.md) decision 15c 🔴 | A `[agents]` key if Arpit asks; or Kiro CLI inclusion modes |
