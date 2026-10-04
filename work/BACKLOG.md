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
W-165 (three CLI fixes), W-166 (carry-forward invalidation), W-168 (search improvements), W-169 (`fux inspect`), W-170 (cage search leg), W-176 (the nine abstention gates, from B-175).

---

## `unbuilt` — a ratified decision the code does not implement

| id | what is outstanding | named in | what closes it |
|---|---|---|---|
| B-002 | The dirty list "alone buys no speedup" — the runner still calls today's `fux ingest`, which walks the corpus; the list's input is unused | [SR-MAINTENANCE](../records/0129_hooks.md) decision 1a, point 3 | An incremental re-index that consumes the dirty list |
| B-006 | The `enriched` ingest mode has no sign-off — "the sign-off half has not been given"; grade `6` `INFERRED` stays reserved for it (ex-B-005) | [SR-ENRICH](../records/0137_enrich.md) decision 6 · [SR-EXTRACTED](../records/0115_extracted-mode.md) decision 3 | Arpit: sign off, or retire the mode and release grade 6 — [W-251](open/W-251-backlog-audit-rulings.md) §3 #1 recommends retire |
| B-013 | Engine upgrades do not reach a consumer's `.fux/decoders/`; four real defects "would each have needed every consumer to refresh their copy" | [SR-DECODE](../records/0139_decode.md) decision 10 ⚠ · [SR-DOTFUX](../records/0102_fux-directory.md) decision 8 | Arpit rules [`compare/consumer-template-refresh`](compare/consumer-template-refresh.compare.md) (W-251 §3 #2) |
| B-014 | The fetcher optional-functions gap is "made visible, not closed" — the consumer still copies `validate()`/`is_rate_limited()` in themselves | [SR-FETCHER](../records/0117_fetcher.md) decision 12 ⚠ · [SR-DOTFUX](../records/0102_fux-directory.md) decision 6 | The same ruling as B-013 — [`compare/consumer-template-refresh`](compare/consumer-template-refresh.compare.md) |
| B-027 | `ttl=` bounds the TTL fetch cache and nothing else — it does not influence which URLs `fux daemon` sweeps first | [SR-URL-FRESHNESS](../records/0147_url-freshness.md) Consequences, *Owed* | Arpit: W-251 §3 #5 recommends **nothing** — d14's ask-time/update-time wall stands and `sweep_minutes` is the clock |
| B-031 | The write verbs have no `--json`; a machine-readable `add` needs a shape for *recorded, fetched, ingested* | [SR-CLI](../records/0101_cli-surface.md) Consequences | A caller who needs it, then a declared shape |
| B-033 | `verify`, `--why`, `--receipt` and `--journal` "have no Node twin at all" — a stated absence, not a covered one | [SR-NODE-SEARCH](../records/0153_node-search.md) Consequences ⚠ | Arpit: W-251 §3 #6 recommends a ruled permanent subset — the four join SR-NODE-SEARCH's subset table |
| B-038 | `tools/pii-probe/` is the only instrument that sees an over-broad rule and shipping it as a CLI verb "is NOT decided here" | [SR-PII](../records/0148_pii.md) decision 20 ⚠ | Arpit: W-251 §3 #7 recommends no verb — the `fux-pii` skill's copy is the home |
| B-041 | `.rst`, `.adoc` and `.org` keep their own regexes in `extract.py` and get no fence handling | [SR-DECODE](../records/0139_decode.md) decision 14 ⚠ | Fence-aware grammars for those three |
| B-260 | A pathological PII regex can hang an ingest — Python's `re` has no timeout; SR-PII calls the bound "Owed, and filed in OPEN-WORK", and it was not (ex-B-232, the row that was its only home) | [SR-PII](../records/0148_pii.md) Consequences, *Owed* | A regex time or complexity bound at load, with a doctor line |
| B-261 | Abstention gates 2–9 are ruled (option (a), 2026-09-14) and unbuilt; their queue home, W-204 phase E, closed complete without them. W-213 measured gate 1 and removed it | [`abstention-gates`](compare/abstention-gates.compare.md) · [SR-CONFIDENCE](../records/0141_confidence.md) decision 3a | One `W-nn` per gate when picked; the measurement plan §2 |

---

## `ungated` — a stated rule nothing mechanically checks

| id | what is outstanding | named in | what closes it |
|---|---|---|---|
| B-055 | Ten `component` records carry `owns: []`, so the freshness gate can never fire for them; the rule that would close it is "proposed and NOT in force" | [SR-WORK-OWNERSHIP](../records/0054_WORK-ownership.md) decision 11 ⚠ · [`records/README.md`](../records/README.md) §The three kinds | Arpit: W-251 §3 #16 recommends the rule with a named exemption list, then one test |
| B-060 | `describes` is FILE-scoped and the descriptions are KEY-scoped, so a commit touching `config.py` demands every describing record; key-scoped `describes` was DECLINED, not rejected | [SR-WORK-OWNERSHIP](../records/0054_WORK-ownership.md) decision 10 🔴 · [SR-DOCTOR](../records/0152_doctor.md) decision 1 ⚠ | Arpit: W-251 §3 #17 — symbol-narrow the three `config.py` rows |
| B-259 | Display width is not `len()`: a path holding a CJK character or emoji renders two columns and can still wrap. "No test covers it" (ex-B-134, misfiled `unmeasured`) | [SR-CLI](../records/0101_cli-surface.md) decision 12 ⚠ | A width-aware measure plus a test in `test_progress.py` |

---

## `unmeasured` — a live default, constant or claim with no measurement behind it

| id | what is outstanding | named in | what closes it |
|---|---|---|---|
| B-089 | `title`, `path` and `ctx` "are carried forward from nothing — defensible starting points, not measured optima" | [SR-RANKING](../records/0111_ranking.md) decision 3 ⚠ | A pre-registered tuning run over the three weights |
| B-090 | `[ranking] expand_weight` ships at `0.2`, "ratified by Arpit and unmeasured on any corpus in this repo" | [SR-TUNE](../records/0135_tuning.md) decision 12 ⚠ · [SR-EXPAND](../records/0149_expand.md) decision 5 | A graded run sweeping `expand_weight` on a rung |
| B-091 | PPR "has three constants and no measurement behind two of them" — `ITERATIONS = 3` and `LAZINESS = 0.5` are conventional | [SR-GRAPH](../records/0126_graph.md) Consequences ⚠ | A pre-registered measurement of iterations and laziness |
| B-092 | The TTL store's `max_bytes` default is 500 MB, "a number chosen here, not specified" | [SR-CACHE](../records/0131_cache.md) decision 9 | Arpit: W-251 §3 #8 — the accepted-forever note; no measurement picks a byte cap |
| B-093 | ARC-vs-LRU "does not rest on a from-scratch Fux measurement" — post-hoc, on a synthetic trace, where the trigger asked for a real workload | [SR-CACHE](../records/0131_cache.md) Consequences ⚠ | A hit-rate measurement on real Fux workloads |
| B-094 | The accelerator "gets slower in proportion to the spread… it is spent, not free, and the amount must be measured under SR-RS with a frozen pre-registration" | [SR-TUNE](../records/0135_tuning.md) Consequences ⚠ | A pre-registered measurement of the spread's cost |
| B-095 | Narrowing what counts as a document is a ranking change and "this record does not claim it is an improvement. Nothing has been measured" | [SR-TYPES](../records/0128_types-list.md) Consequences, first ⚠ | A measured run of the type filter against ranking |
| B-096 | The `max_phrases = 32` evidence is "post-hoc and single-corpus" | [SR-EXTRACTED](../records/0115_extracted-mode.md) decision 9 ⚠ | A pre-registered measurement on another corpus |
| B-097 | The smallest corpus at which the doc-major argument stops holding "has never been measured" | [SR-POSTINGS](../records/0112_postings.md) Context ⚠ | A measurement, if the argument is contested |
| B-098 | The measured 23× carry-forward split "no longer describes the pipeline… nobody has re-measured the split" | [SR-INGEST](../records/0106_ingest.md) §1 ⚠ | Re-measure delta against `--full` |
| B-099 | The retired 100 000-document packed-size promise "has no successor"; the section-size run has a number (25.4 → 50.4 MB at rung-10000) and no record sets a bar | [SR-INDEX-LIFECYCLE](../records/0108_index-lifecycle.md) Consequences · [SR-POSTINGS](../records/0112_postings.md) Consequences | Arpit: W-251 §3 #9 — register a size prediction at 10 000, new id, as the next generation's bar |
| B-100 | The cost of removing the bare-`str` fetcher return ramp "has never been measured" — nobody has checked whether a consumer fetcher exists outside this repo | [SR-FETCHER](../records/0117_fetcher.md) decision 2 ⚠ | Arpit: W-251 §3 #10 — remove it with 3.0, the breaking major; it cannot be measured |
| B-101 | `MAX_PARALLEL` stays `1` because the capture "does not justify a number" — every page was loopback HTML with no auth, redirect or CDN hop | [SR-CDP-FETCHER](../records/0118_cdp-fetcher.md) decision 7c 🔴 | A live run against real session-gated sources |
| B-102 | The daemon sweep's capture ran against `127.0.0.1`: "the rate-limit path was never exercised, and W-82 ruling 3's hold is narrowed, not lifted" | [SR-MAINTENANCE](../records/0129_hooks.md) decision 9c-i ⚠ | A real-network sweep exercising rate limiting |
| B-103 | The daemon lifecycle is verified "macOS only, and the detached-process mechanics are the part most likely to differ on Windows" | [SR-MAINTENANCE](../records/0129_hooks.md) decision 9c-i ⚠ | A Windows daemon-lifecycle capture |
| B-105 | The cross-encoder refusal "stands anyway, because nobody has measured the quantity that decides it" — gap tightness over ~20 similar documents | [SR-RERANK](../records/0138_rerank.md) veto 1 ⚠ | Measure drift and adjacent gaps on a real cross-encoder |
| B-106 | Nobody has measured how many undeclared negations a real corpus contains — *"this approach was abandoned"*, *"unlike Y"* | [SR-RERANK](../records/0138_rerank.md) veto 1 ⚠ | Count undeclared negations in a real corpus |
| B-107 | An exact top-5 tie is broken by `docidx` rather than relevance, "and 4.38 % of queries contain one" | [SR-RERANK](../records/0138_rerank.md) veto 5 ⚠ | A relevance-bearing tie-break |
| B-108 | Doc2query questions are "BUILT AND UNPROVEN" — the four-arm run was voided because its bar never named `k` | [SR-ENRICH](../records/0137_enrich.md) decision 15 🔴 | A re-registered bar naming `k`, then a run |
| B-109 | The `--check` filter's own value is unproven: it refused 2 of 98 questions and moved no recall number at any `k` | [SR-ENRICH](../records/0137_enrich.md) decision 16 ⚠ | A run where the filter treats enough questions to be visible |
| B-110 | The enrichment tilt "is real" and `ctx`'s weight is conditional on it being small — "which is a measurement, not an opinion" | [SR-ENRICH](../records/0137_enrich.md) decision 6 | Measure the tilt at partial coverage |
| B-112 | The `judged` series stays internal until 5–10 % of its scores are cross-checked against a human; no cross-check exists | [SR-WORK-QUALITY](../records/0056_WORK-quality.md) decision 10 | Human-adjudicate 5–10 % of judged scores, then publish |
| B-113 | The `doc_coverage` gate is off because the two populations overlap; turning it on "needs a new measurement on a golden rung"; one decoy in fifteen reads `grounded` (ex-B-130) | [SR-CONFIDENCE](../records/0141_confidence.md) decision 12 · [SR-RS](../records/0133_predictions.md) decision 15 ⚠ | [the plan](proposals/measurement-plan-2026-10.md) §2 — AUC on the retired sets' rows |
| B-114 | `--band` on a fused or multi-`-q` query describes the first arm; d17 then found `separation` "does not carry correctness on this corpus" | [SR-CONFIDENCE](../records/0141_confidence.md) the W-109 ⚠, decision 17 · [SR-EXPAND](../records/0149_expand.md) decision 10 | Arpit: W-251 §3 #11 — does `separation` stay the band's quantity at all; recalibrating it for RRF is moot |
| B-115 | Decision 15 "remains unmeasured" — no endpoint touched `pdf`/`rtf`/`csv`/`jsonl` heading emission; decision 16 is "INCONCLUSIVE, not a null" | [SR-DECODE](../records/0139_decode.md) Consequences ⚠ and 🔴 | Endpoints over those four formats, and over `phrases` noise |
| B-116 | `toml`, `yaml` and `ini` emit no filename title — "pre-existing… not changed here. Recorded so it is a decision next time" | [SR-DECODE](../records/0139_decode.md) decision 11a ⚠ | Measure, then emit a title or rule it out |
| B-117 | The repeated table header is scored, so every band of a table gains a uniform uplift against non-table passages | [SR-REFER](../records/0127_refer-plane.md) decision 25 ⚠ | Measure the uplift, or stop scoring the repeated header |
| B-119 | The refer plane fetches serially, so the latency bound "is a statement about the source's latency at k=10, not about fux" | [SR-REFER](../records/0127_refer-plane.md) veto 1 ⚠ | Parallel fetch, or re-measure and re-register the bound |
| B-120 | ~2.6 s per document per query at the 20 000-row tabular default, multiplied by a multi-document `ask --refer` | [SR-TABULAR](../records/0150_tabular.md) Consequences 🔴 | Arpit: W-251 §3 #12 — cascade, measured first ([plan](proposals/measurement-plan-2026-10.md) §5, with B-262), or the declined degrade-to-bands constant |
| B-121 | "Raising the row limit is also an index-size change, not only a latency one" | [SR-TABULAR](../records/0150_tabular.md) Consequences ⚠ | A measured index-size budget for tabular corpora |
| B-122 | Nothing has been measured about how often anyone reaches for `.fuxignore`'s `!` re-inclusion, which admits an undecoded format as raw bytes | [SR-FUXIGNORE](../records/0144_fuxignore.md) Consequences ⚠ · [SR-TYPES](../records/0128_types-list.md) Consequences ⚠ | Measure `!`-admitted formats across real repos |
| B-123 | The starter PII scan was "a false-positive check on one technical corpus, not a recall measurement — nothing here contains a real identifier" | [SR-PII](../records/0148_pii.md) decision 12a | A recall measurement on a corpus with real identifiers |
| B-124 | The `as-ingested` veto's instrument runs over journalled answers only, so it reports `unknown` and the condition "has never had data to run against" | [SR-ACQUIRED](../records/0145_acquired-plane.md) Consequences ⚠ · [SR-URL-FRESHNESS](../records/0147_url-freshness.md) Consequences | Journalled answers on a corpus with reachable sources |
| B-127 | The corpus behind SR-ANSWER decisions 11–13 was retired: "the run stands as filed and cannot be re-run where it was run" | [SR-ANSWER](../records/0105_answer.md) Reference ⚠ | A live graded corpus to re-measure the three decisions on |
| B-128 | The timing set keeps no key — "a key for it can only be built by re-reading the corpus" — so CAP-3's query set is unstated | [SR-WORK-BENCHMARK](../records/0053_WORK-benchmark.md) Consequences ⚠ | Arpit: W-251 §3 #13 recommends the retired sets — open, no key needed |
| B-132 | Two RRF arms at `--top 5` fuse shallowly: a document ranked 6th in both arms is invisible to the fusion | [SR-EXPAND](../records/0149_expand.md) Consequences | A deeper fusion decision, or a higher `--top` |
| B-135 | The double-load hazard "is unchanged and still unmeasured" — Copilot sees two same-name skill copies | [SR-AGENT-POLICY](../records/0132_agent-policy.md) decision 14a ⚠ | Observe or rule out a duplicate-name error in Copilot |
| B-137 | A judgment supply in the hundreds is "legal to collect and still not collected" — the L9 reversal "unblocks that pressure rather than resolving it" | [SR-LAWS](../records/0001_LAWS.md) decision 8 · [SR-LAW-9](../records/0011_LAW-9-use-record.md) Consequences | Arpit: W-251 §3 #14 recommends not now — nothing waits on it but B-093 |
| B-245 | The vector plane (`fux embed`, `.fux/vectors/`, `--qvec`, RRF fusion) — closed unbuilt 2026-09-14: its gate can never fire; `tools/vector-gate/` is held by the fallback until `SR-VECTORS` (ex-B-166) | [SR-RS](../records/0133_predictions.md) d19, d20 · archived W-112 | **Reopen only when both hold:** a rank-contract corpus exists **and** doc2query's ceiling is measured (plan §7) |
| B-262 | Cascade ranking is "unbuilt and unmeasured, deliberately" — stage-1 `recall@k` is the gate; nothing is built until it is measured (ex-B-044, reclassed) | [SR-CHUNKING](../records/0151_chunking.md) §What is NOT done · [SR-TABULAR](../records/0150_tabular.md) Consequences 🔴 | Stage-1 `recall@k` above ~0.98 on golden tables (the measurement plan §5) |

---

## `unruled` — a fork named and not decided. Only Arpit closes one

| id | what is outstanding | named in | what closes it |
|---|---|---|---|
| B-143 | The query-side lens — `--intent`, `--as-of`, `--no-archived` — was "an unopened fork with no compare doc"; it has one now | [SR-TUNE](../records/0135_tuning.md) decision 15 ⚠ · [SR-ARCHIVED-CONTENT](../records/0134_archived-content.md) decision 6 🔴 · [SR-API](../records/0154_api.md) decision 7 ⚠ | Arpit rules [`query-side-lens`](compare/query-side-lens.compare.md) (W-251 §3 #3) |
| B-144 | Whether anyone will ever write `supersedes:` is "a question about the concept, not the knob, and is Arpit's" — his own SR-WORK-TESTDATA A21/R5 require it in seed docs | [SR-TUNE](../records/0135_tuning.md) decision 15 ⚠ | Arpit: [`compare/query-side-lens`](compare/query-side-lens.compare.md) recommends keep as a declared fact; the question closes |
| B-145 | Of four candidate enrichments two are resolved by other means (expansion → mined/doc2query; retirement → `superseded_by:`); inferred edges and richer embeddings remain, "None is approved" | [SR-ENRICH](../records/0137_enrich.md) §The candidate enrichments | Both behind B-245's reopen trigger; a ruling per candidate when it fires |
| B-146 | `find(under=…)` applies a component boundary in the library and a bare prefix on the CLI — "STATED rather than fixed, because it is a ruling" | [SR-API](../records/0154_api.md) decision 6 ⚠ · [SR-FIND](../records/0104_find.md) decision 7 | Arpit rules [`compare/cli-library-parity`](compare/cli-library-parity.compare.md) (W-251 §3 #4): component boundary on both, and in `priority_for` |
| B-147 | `explain`, `graph` and `path` return different payloads on the library surfaces than on either CLI — "Stated; not smoothed over" | [SR-API](../records/0154_api.md) decision 6 ⚠ | [`compare/cli-library-parity`](compare/cli-library-parity.compare.md): the CLI adopts the library/Node shape in 3.0 — Arpit's yes |
| B-148 | Promoting the changed-since line from stderr into a `--json` field "would be additive but would move a documented surface, so it is a fork rather than a default" | [SR-ANSWER](../records/0105_answer.md) decision 10 ⚠ | [`compare/cli-library-parity`](compare/cli-library-parity.compare.md): add the field in 3.0 — Arpit's yes |
| B-150 | The passage carries the document's frontmatter block — "a real readability cost… Stripping it is `chunk.py`'s call, not this record's" | [SR-ANSWER](../records/0105_answer.md) Consequences | A decision in SR-REFER on stripping frontmatter |
| B-151 | `find` emits `fused` before `confidence` and `ask` the reverse — "that ordering is not a decision anybody took" | [SR-FIND](../records/0104_find.md) Consequences ⚠ | [`compare/cli-library-parity`](compare/cli-library-parity.compare.md): `confidence` first in both — Arpit's yes |
| B-154 | `snapshot` is the one URL-list attribute still undecided — `max_age` is `ttl=` and `tag` belongs in the enrichment file (W-251 §2); URL documents' `tag` edges stay empty until then | [SR-URL-LIST](../records/0116_url-list.md) §Considered for the set | A record deciding `snapshot` under L3 — SR-REFER's |
| B-162 | L4 lost its co-guard: a query-time model is held off only by SR-RERANK's determinism refusal — "a decision, and decisions are what an SR is designed to supersede" | [SR-LAW-2](../records/0004_LAW-2-zero-cost.md) §The 2026-09-06 amendment, trade 2 | Arpit (a Law): W-251 §3 #18 recommends barring a model *call* on the query path while permitting a pinned committed artefact |
| B-170 | Kiro's twelve pointers are ambient on a CLI without inclusion modes — ~10 KB in every request, paid by developers not using fux | [SR-AGENT-POLICY](../records/0132_agent-policy.md) decision 15c 🔴 · [SR-DOTFUX](../records/0102_fux-directory.md) decision 9 ⚠ | Arpit: W-251 §3 #20 — fold into B-251 as its first case; interim, emit the Kiro set only under `--agents kiro-ide` |
| B-174 | Decision 12's scope defect is "KNOWN and DELIBERATELY UNREPAIRED"; the trigger was three written disclosures and the fourth was written 2026-08-27 — **the trigger has fired** | [SR-RS](../records/0133_predictions.md) decision 12 ⚠ | Arpit: W-251 §3 #15 — re-word d12 along the record's own contamination table |

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
| B-246 | `WORKLOG.md` archive-and-truncate — append-only and growing forever (~14 000 lines); a cut into `archive/worklog/` would cap the live file under the one-archive law. Parked since 2026-08-21 | [SR-WORK-GOVERNANCE](../records/0065_WORK-governance.md) Consequences | Arpit: W-251 §3 #19 recommends a cut at each v-major, not yearly |
| B-248 | Glassbox sessions — counts and cross-session joins, which fux does not do; the sketch is materialise-then-index. ⚠ The `fetch=` closed-tuple blocker is **struck** (W-178, then W-199) | [`glassbox-sessions.md`](proposals/glassbox-sessions.md) | A second event-stream source is asked for |
| B-250 | Code pattern recognition — a committed, deterministic clone-and-shape map for code, as a separate distribution; the query and call-graph halves are a buy (ast-grep, tree-sitter graph servers) | [`code-pattern-recognition.md`](proposals/code-pattern-recognition.md) | A second ask for a code-shape answer that must be committed at a sha |
| B-251 | Cross-model agent guides — the shipped guides load the same everywhere but trigger and comply differently per model; five deterministic levers, eval matrix first, and no in-file "if you are model X" branch | [`cross-model-agent-guides.md`](proposals/cross-model-agent-guides.md) | A filed mis-trigger or broken rule on a non-Claude or smaller model, or Arpit asks for the matrix |
| B-253 | The measurement plan — the twenty-one `unmeasured` rows that can be measured now, as eight pre-registrations with rung, endpoint, instrument and bar | [`measurement-plan-2026-10.md`](proposals/measurement-plan-2026-10.md) | Per section: its data in hand **and** a decision waiting on the number — then a `W-nn` |

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
| B-252 | Record↔code coherence is judgement — self-contradiction, a record ahead of its code, a paraphrased rule, a narrowed law, a short symbol list, a missing `describes` row, a key's meaning: each source rules it "cannot be mechanised" (ex-B-048/049/050/053/061/062/071) | [SR-LAW-0](../records/0002_LAW-0-authority.md) §What is gated | Nothing — permanently ungated |
| B-254 | Term-hash collision detection is complete only on a full run; a collision involving a carried-forward document is not detected on a delta — "`--full` is the complete check" (ex-B-083) | [SR-INGEST](../records/0106_ingest.md) Consequences | Accepted; `fux ingest --full` is the remedy |
| B-255 | No law forbids transmitting a use record — the transmission clause was put to Arpit and declined; "what holds today is the code, not a law" (ex-B-159) | [SR-LAW-9](../records/0011_LAW-9-use-record.md) §The gap the ratification opens | A re-ruling, or `.fux/runtime/` becoming shareable by any route (SR-LAWS decision 8's tripwire) |
| B-256 | A single unbreakable token comes back oversized and the assembler refuses it — "That is correct, and it is now the only case"; `answer` falls back to the index (ex-B-169) | [SR-CHUNKING](../records/0151_chunking.md) decision 6 | A rung below `word`, if ever wanted |
| B-257 | A caller can supply a misleading `--expand` term — "a trust boundary this record does not close"; the caller is the user's own agent, the receipt records the term, and `[mcp]` can disable it (ex-B-173) | [SR-EXPAND](../records/0149_expand.md) Consequences | Accepted; a trust model only if a shared server exposes `expand` |
| B-258 | A URL skip is recorded nowhere and prints on every networked run — "Accepted: a repo has a handful of dead URLs, not hundreds"; the dead-URL report counts streaks (ex-B-012) | [SR-FUXIGNORE](../records/0144_fuxignore.md) Consequences ⚠ · [SR-INGEST](../records/0106_ingest.md) Consequences | Accepted; `url-state.json` is where repeat failure lives |
