---
type: Handoff
name: W-251
description: "The 2026-10-03 backlog audit — every B-row read against its source. 66 stale rows deleted, 31 rows promoted into seven agent items, two dozen record sentences found false or stale (W-245), and the forks that need Arpit's own word gathered here as one inbox row with a recommendation per line. Ratified by delegation where evidence settles it; recommended where only he can."
item: W-251
filed: 2026-10-03
ball: arpit
---

# W-251 — the backlog audit: what was ratified, what waits on Arpit

**Model:** none — this item is a list of rulings. Each *yes* below lands through
[W-245](W-245-record-sentences-stale.md) (a record sentence) or a new item;
each *no* deletes or repoints a backlog row. **Arpit answers the §3 table one
line at a time**; the rest of this file is the evidence.

**Delegation.** Arpit, 2026-10-03 (Cowork): *"Review open work and backlog.
Ratify whatever you can. Think about it, research and ratify whatever you can.
For backlog, create proposal documents with ratified or recommended approach.
Create a compare if needed."* Four parallel audits read every row of
[`BACKLOG.md`](../BACKLOG.md) against the sentence it cites and the code it
names; a sample of each audit's citations was re-read by the ruling session
before anything below was written. **Where the source itself had already
answered the row, the row was closed by delegation. Where the answer is his
taste, his money or his hands, it is in §3 with a recommendation.**

---

## §1 — Ratified by delegation (done in this change)

**Stale rows deleted — SR-WORK-BACKLOG rule 26** (the source was rewritten, the
thing built, or the fork ruled since 2026-09-13). The id is retired, never
reused; the sentence that closes each is in the cited record.

| id | why it is gone | where the source says so |
|---|---|---|
| B-003 | a measured negative with a reopen trigger is a **veto condition**, not a debt (rule 9) | [SR-MAINTENANCE](../../records/0129_hooks.md) Consequences, *"the reopen trigger is a measured one-document re-ingest above 5 s"* |
| B-004 | no record **decides** a wire encoding — SR-POSTINGS ratifies plain doc-major JSON; nothing is `unbuilt` | [SR-POSTINGS](../../records/0112_postings.md) decisions 1–7 |
| B-005 | merged into B-006 (one fork: the `enriched` mode's sign-off) | [SR-EXTRACTED](../../records/0115_extracted-mode.md) decision 3 |
| B-008 | the migration was **refused by ruling**; the manual step is documented — rule 10 | [SR-DECODE](../../records/0139_decode.md) decision 17, *"Deleting them is the upgrade step, and it is manual"* |
| B-012 | an **accepted** consequence, re-filed as `cost` B-258 | [SR-FUXIGNORE](../../records/0144_fuxignore.md) Consequences, *"Accepted: a repo has a handful of dead URLs"* |
| B-025 | built — `doctor`'s never-fetched row (W-140 row 13) | [SR-DOCTOR](../../records/0152_doctor.md); `doctor.py::_unfetched_note` |
| B-026 | the retirement path exists and is named by the report: `fux remove <url>` | [SR-URL-INGEST](../../records/0107_url-ingest.md) decision 4 |
| B-028 | the display cache was **deleted** with its fork (W-194) | [SR-RECORD](../../records/0109_index-record.md) Consequences |
| B-035, B-036 | the corpora generator and the pinned 1.x arm are built and ran 2026-09-12 | [`setup/fux-benchmark.md`](../setup/fux-benchmark.md); the record's sentence is stale → W-245 |
| B-039 | a per-corpus human edit, not engine work; `enrich --check` already names the file | [SR-PII](../../records/0148_pii.md) decision 1 |
| B-042 | *keep it approximate* was **ruled** 2026-09-06 | [SR-DECODE](../../records/0139_decode.md) decision 15 |
| B-043 | a veto condition with two stated triggers (rule 9) | [SR-CDP-FETCHER](../../records/0118_cdp-fetcher.md) decision 12 |
| B-045 | the daemon is the closer and exists; the verb the row named is deleted | [SR-URL-INGEST](../../records/0107_url-ingest.md) decision 9 |
| B-046 | the ladder moved into `fux-lab` | [`setup/fux-lab.md`](../setup/fux-lab.md) |
| B-241 | the record explains why nothing is owed | [SR-URL-LIST](../../records/0116_url-list.md) decision 11 |
| B-051 | law text has one source and a generated view bound by `test_claude_md_laws.py` since 2026-09-12 | [SR-LAWS](../../records/0001_LAWS.md) decision 8 |
| B-057 | the record **retracted** its owns-nothing claim (W-208) | [SR-WORK-OWNERSHIP](../../records/0054_WORK-ownership.md) decision 7 |
| B-058, B-059 | `describes` rows now open SR-RUNTIME-STATS and SR-LOCKS; the records' sentences are stale → W-245 | [`records/README.md`](../../records/README.md) §DESCRIBES |
| B-063 | `bm25f.py` is carved out to SR-RANKING; the example closed | [`records/README.md`](../../records/README.md) §Ownership |
| B-066 | publish is gated on CI green (d11/d14, *"two strikes made into a gate"*) | [SR-WORK-RELEASE](../../records/0063_WORK-release.md) decision 14 |
| B-078 | `test_no_code_under_the_four_roots_reaches_the_sandbox` exists | [SR-WORK-ENVIRONMENTS](../../records/0052_WORK-environments.md) — sentence stale → W-245 |
| B-081 | neither shipped fetcher imports `fux.decode` since W-199 — the record's sentence is **false** → W-245 | [SR-FETCHER](../../records/0117_fetcher.md) Consequences |
| B-082 | `fux mcp` now loads `output_config` and hard-fails like `ask` | [SR-MCP](../../records/0136_mcp.md) Consequences — sentence stale → W-245 |
| B-088 | `separation_floor` measured on 8 rungs × 3 sets (W-213) | [SR-CONFIDENCE](../../records/0141_confidence.md) decision 17 |
| B-104 | the reranker was graded on a second corpus: FAIL, 7 better / 47 worse | [`2026-09-16-rerank-quality-b2`](../regression/2026-09-16-rerank-quality-b2/VERDICT.md) |
| B-111 | the resolution floor was replaced by SR-RS d19's measured paired floor **before** the row was filed | [SR-WORK-QUALITY](../../records/0056_WORK-quality.md) veto 5, *"SPENT — fired 2026-08-28"* |
| B-118 | `fux graph` is 0.35–0.40 s at rung-10000 (W-238); the compare it pointed at is archived | [`2026-09-29-w238-verb-latency`](../regression/2026-09-29-w238-verb-latency/report.md) |
| B-126 | every arm job runs `fux build` first; 0 of 225 discordant with it | [SR-NODE-SEARCH](../../records/0153_node-search.md) decision 9 |
| B-130 | the same measurement as B-113 — merged into it | [SR-CONFIDENCE](../../records/0141_confidence.md) decision 12 |
| B-131 | L11's locked key had its first adjudicating use — every paired comparison in the final score cleared d19 on sets authored sealed | [`FINAL-SCORE`](../regression/2026-09-22-golden-final-score/FINAL-SCORE.md) |
| B-133 | RM3 measured as an arm three times and removed (SR-EXPAND d17) | [`rm3-selective`](../compare/rm3-selective.compare.md) |
| B-136 | both suites have run whole on the real repo many times since | [`WORKLOG`](../WORKLOG.md) 2026-09-30 |
| B-138 | `routes()` is bounded by **work**, option (c), ruled 2026-09-14 | [SR-GRAPH](../../records/0126_graph.md) decision 17 — d12's "unresolved" text stale → W-245 |
| B-139, B-171 | a missing required file is a hard error naming it; `doctor` runs; `doctor --fix` is the 3.0 migration | [L12](../../records/0014_LAW-12-values-live-in-config.md) decision 3; [SR-OUTPUT](../../records/0143_output-defaults.md) decision 20 — SR-CLI's bullet stale → W-245 |
| B-140, B-142 | `weak` is a signal, `answerable = band != none` (W-214); the second-threshold hole closed when the floor stopped abstaining | [SR-CONFIDENCE](../../records/0141_confidence.md) decision 3a — d13/d14 text stale → W-245 |
| B-152 | the strict-mode reservation on exit `2` is retired (W-193) | [SR-CLI](../../records/0101_cli-surface.md) decision 5 — §1 table stale → W-245 |
| B-153 | a decision with a live reopen trigger in SR-IDENTIFIERS, not a fork | [SR-IDENTIFIERS](../../records/0160_identifiers.md) |
| B-155 | the optional-function fork was ruled 2026-08-28 | [SR-FETCHER](../../records/0117_fetcher.md) decision 12 — SR-MAINTENANCE d11 text stale → W-245 |
| B-157 | SR-WORK-TESTDATA A2/A20/R5 name `seed/archive/`; Arpit's own ask confirmed the exemption | [SR-WORK-TESTDATA](../../records/0068_WORK-test-data.md) |
| B-159 | ruled and declined twice; an accepted gap with a tripwire → `cost` B-255 | [SR-LAW-9](../../records/0011_LAW-9-use-record.md) §The gap |
| B-160 | nothing to rule — reopens when a record wants a readable journal | [SR-LAW-9](../../records/0011_LAW-9-use-record.md) Consequences |
| B-163 | re-grounded by the 2026-09-28 renumber ruling | [SR-LAW-7](../../records/0009_LAW-7-python-312.md) |
| B-164 | the three priors were removed; W-97's leg and R-11 moved into W-204, now complete | [SR-TUNE](../../records/0135_tuning.md); [`archive/README.md`](../../archive/README.md) |
| B-165 | the golden schema **is** an SR now: `relevant` list + `primary` | [SR-WORK-TESTDATA](../../records/0068_WORK-test-data.md) A9 |
| B-166 | an ownership holding pattern downstream of B-245; folded into that row | [SR-RS](../../records/0133_predictions.md) decision 20 |
| B-169 | the record already ruled the refusal *correct* → `cost` B-256 | [SR-CHUNKING](../../records/0151_chunking.md) decision 6 |
| B-173 | an accepted trust boundary with disclosure in the receipt → `cost` B-257 | [SR-EXPAND](../../records/0149_expand.md) Consequences |
| B-191 | its only source is an **archived** record; L1 says named, never cited; the exposure lives under L3 (B-190) | [L1](../../records/0003_LAW-1-retired-records-archived.md) |
| B-208, B-209 | cost **paid**: W-194 deleted the hashed mode; the deprecation cycle was discharged by 3.0's deletion of `fux update` | [SR-URL-INGEST](../../records/0107_url-ingest.md) Consequences, decision 8 |
| B-247 | premise died: `DOC-REGISTRY.md` is retired and SR-WORK-REGISTRY requires one row per live document | [SR-WORK-REGISTRY](../../records/0067_WORK-registry.md) |
| B-048, B-049, B-050, B-053, B-061, B-062, B-071 | seven rows restating one judgement every source already rules *cannot be mechanised* → one `cost` row, B-252 | [SR-LAW-0](../../records/0002_LAW-0-authority.md) §What is gated |
| B-069 | B-236 already carries *periodic re-reading of the vendor docs* | [SR-AGENT-POLICY](../../records/0132_agent-policy.md) |
| B-083, B-087 | stated, accepted, remedy named (`--full`; a validator *if ever wanted*) → `cost` B-254; B-087 nothing owed | [SR-INGEST](../../records/0106_ingest.md); [SR-INDEX-LIFECYCLE](../../records/0108_index-lifecycle.md) |

**Promoted into the queue — rule 23** (file + row + ball, backlog row deleted):

| rows | item | what it is |
|---|---|---|
| B-020, B-047 (gate half), B-052, B-054, B-056, B-065, B-068, B-072, B-073, B-074, B-075, B-076 (smoke half), B-077, B-079, B-080, B-084, B-085, B-086, B-168 | [W-246](W-246-mechanical-gates.md) | the small tests and `doctor` rows the records asked for and nobody wrote — all stdlib, each one named in the item |
| B-040 | [W-247](W-247-api-renderer-split.md) | `cmd_*` render what `fux.api` builds; one payload, one place |
| B-007 | [W-248](W-248-enrich-consumes-queue.md) | `fux enrich`'s worklist is declared scope ∪ the decoder queue's *model-needed* rows |
| B-034 | [W-249](W-249-resident-index-mcp-serve.md) | `fux mcp` / `fux serve` hold the index open, keyed on `.fux/runtime/stamp.json` — index residency, **not** W-242's refused T3 memo |
| B-037 | [W-250](W-250-dogfood-fux-hooks.md) | run `fux hooks` in this repository |
| B-125 | [W-252](W-252-node-arm-preregistration-2.md) | `PRE-REGISTRATION-NODE-2` on lab rungs, so the Node arm can be called green |
| the stale sentences | [W-245](W-245-record-sentences-stale.md) | eleven record sentences the audit found false against the code or stale against a later decision |

**Ratified sentences whose rows left with their item:** B-141, B-149, B-158, B-172, B-167, B-154's `max_age` half (→ W-245); B-156, B-161 (→ W-246). §2 below is the ruling each sentence carries.

**Reclassified** (rule 22: the class is what must happen first): B-044 → `unmeasured` B-262 · B-134 → `ungated` B-259 · B-232 → `unbuilt` B-260 (SR-PII says *Owed, filed in OPEN-WORK*; it was not — this row was its only home, rule 25).

**Repointed in place** (text only, same id): B-002 (dirty list unused — accurate; closer kept) · B-013/B-014 → [`compare/consumer-template-refresh`](../compare/consumer-template-refresh.compare.md) · B-040 gone · B-055 (ten `owns: []` component records, not thirteen) · B-143/B-144/B-145 → [`compare/query-side-lens`](../compare/query-side-lens.compare.md) · B-146/B-147/B-148/B-151 → [`compare/cli-library-parity`](../compare/cli-library-parity.compare.md) · B-154 (`max_age` is `ttl=`; `tag` and `snapshot` remain) · B-167 (the 429 trigger reads *attributable to fux's own parallelism*) · B-180/B-181/B-183/B-184 (proposal triggers, see [`proposals/README.md`](../proposals/README.md)) · B-190 (ex-L5 retired, the exposure stands under L3) · B-193 (3.11 too; the floor is 3.12) · B-207 (`fux ingest --refetch-all`) · B-237 (the gap binds the `weak` label only) · B-245 absorbs B-166.

**New rows filed:** B-252 (coherence is judgement) · B-254 · B-255 · B-256 · B-257 · B-258 (costs, above) · B-259 · B-260 · B-261 (abstention gates 2–9 lost their queue home when W-204 closed — `unbuilt`, ruled option (a) 2026-09-14) · B-262 · B-253 ([`proposals/measurement-plan-2026-10.md`](../proposals/measurement-plan-2026-10.md), the 21 measurable-now rows as one plan, under *Parked ideas*).

---

## §2 — Ratified by delegation, needing a record sentence (→ W-245)

Each of these is a *yes* the evidence already gives; W-245 writes the sentence.

| row | ruling | record, decision |
|---|---|---|
| B-141 | **confirm as built** — an explicit `--band` prints `grounded`; since W-214 the band is informational, so a flag that goes quiet on the good case reads as broken | SR-CONFIDENCE d4: strike *"sub-call … if Arpit wanted the silence"* |
| B-158 | **confirm the narrow scope** — the quote *"bundled and then published in Python as well as in the npm package"* is about the Node bundle shipping in both registries; nothing since treats `src/fux` as anything but pip-installed Python | SR-LAW-10 §Alternatives, close the bullet |
| B-149 | **refuse** re-scoring every `ask`/`find` result — the committed index ranks, `refer` cites; `answer`'s width stays a constant | SR-ANSWER d4 Consequences |
| B-172 | **accept the split permanently** — the URL line's one-line-per-URL diff review (SR-URL-LIST d4/d12) is what TOML tables would lose, and W-199 just grew that grammar | SR-TYPES Consequences |
| B-161 | **accept** — a kilobyte receipt on a gitignored path needs no law; one `doctor` warn row above a `[cli.answer] journal_max_bytes` key (W-246) | SR-PROVENANCE d15 |
| B-156 | **the two-strikes gate fires** — with an arm-agnostic check: the rows file is not byte-identical to any `questions/set-N.jsonl` and each row carries `id` + `rank`/`arm` (W-246) | SR-RS d21b |
| B-167 | re-word the trigger: *a 429 attributable to fux's own parallelism against a real host* (httpbin's always-429 endpoint fired the letter, not the spirit) | SR-CONFIG d7a |
| B-154 | strike `max_age` (it is `ttl=`); `tag` goes in the per-document enrichment file, not the line (grammar stays closed); `snapshot` stays SR-REFER's L3 question | SR-URL-LIST §Considered |
| B-180 | the proposal's thesis — *the instrument is the product* — **has shipped** (ladder + `tools/golden-score` + PRE-REGISTRATION/VERDICT); mark `graduated`, archive once SR-LAWS/SR-TUNE repoint their citations of its §8 survey | `proposals/ranking-tuning.md` |
| B-129 | the gate programme's home: B-261 (`unbuilt`); W-213 measured gate 1 and removed it; gates 2–9 are measured one per item when picked | SR-WORK-BENCHMARK Consequences |

---

## §3 — 🔴 For Arpit — one answer per line

Recommendation first; the strongest counter beside it. **Default if unanswered:
the recommendation stands as *recommended*, not ratified, and the row stays.**

| # | fork (rows) | recommendation | the counter | yes lands in |
|---|---|---|---|---|
| 1 | **The `enriched` ingest mode** (B-006, ex-B-005): sign off, or retire it and release edge grade `6` | **Retire.** `fux enrich` (doc2query, SR-ENRICH d15) and mined expansion (SR-EXPAND d17) cover what the mode was for, deterministically; a model-assisted *ingest* mode has had no sign-off in six weeks and L4 is simpler without the exception | the mode was ratified by name on 2026-08-19 and grade 6 is reserved for it; retiring is a record retirement under L1 | SR-ENRICH d6, SR-EXTRACTED d3; archive under L1 |
| 2 | **Consumer-side template refresh** (B-013, B-014; adjacent B-073, B-221) | **option A** of [`consumer-template-refresh`](../compare/consumer-template-refresh.compare.md): every engine-written copy carries `# fux-template: <sha>`; an unedited copy is engine-owned and refreshed like `node/`; an edited copy is frozen and `doctor` names its version gap | SR-DECODE d10 **declined** the hash stamp; reopening a declined option is his, and it changes who owns `.fux/decoders/` | SR-DECODE d10, SR-FETCHER d12, SR-DOTFUX 6a |
| 3 | **Query-side lens** (B-143, B-144, B-145) | per [`query-side-lens`](../compare/query-side-lens.compare.md): `--intent` is **answered** by the shipped cue-derived prior (no flag); `--as-of` **refused** (a recency order, the thing d15 removed); `find --no-archived` is the one lever worth a build; `supersedes:` stays a **declared fact** (tie-break, edge, `superseded_by:`) and the question closes; of the four enrichment candidates only inferred edges and embeddings remain, both behind B-245 | he stopped W-168 steps 6/7 — he may want no query-side lever before gen-4 scores | SR-TUNE d15, SR-ARCHIVED-CONTENT d6, SR-API d7, SR-ENRICH §candidates |
| 4 | **CLI ↔ library parity** (B-146, B-147, B-148, B-151) | per [`cli-library-parity`](../compare/cli-library-parity.compare.md): component-boundary `under` on both surfaces and in `priority_for`; CLI `--json` for `explain`/`graph`/`path` adopts the library/Node shape; `changed_since` becomes a JSON field; `confidence` precedes `fused` in both verbs — all inside the already-breaking 3.0 | CLI `--json` is a documented SR-CLI contract; a consumer may have scripted the old shape | SR-API d6/d7, SR-CLI, SR-FIND, SR-ANSWER d10 |
| 5 | **`ttl` paces the daemon?** (B-027) | **no — option (c), nothing**: SR-URL-LIST d14 built the ask-time / update-time wall on purpose; `sweep_minutes` is the daemon's only clock until a consumer asks | the record's own *Owed* line says `ttl` should feed sweep order | SR-URL-FRESHNESS Consequences (close the *Owed*) |
| 6 | **Node twins for `verify`, `--why`, `--receipt`, `--journal`** (B-033) | **rule a permanent subset** — add the four to SR-NODE-SEARCH's subset table and stop listing them as owed; the Node plane is a reader-and-builder (W-242), not an answer-verifier | W-242 makes Node a writer; "read-only subset" is a weaker argument than it was | SR-NODE-SEARCH Consequences |
| 7 | **`fux pii-probe` as a verb?** (B-038) | **no verb** — the standalone copy in the `fux-pii` skill is the home; SR-CLI veto 1 refuses a second way on a shrug | a verb is discoverable, a skill copy drifts | SR-PII d20 |
| 8 | **TTL store cap 500 MB** (B-092) | write the *accepted-forever* note; no measurement picks a byte cap | — | SR-CACHE d9 |
| 9 | **A size prediction at 10 000** (B-099) | **register one**: the section-size run has the number in hand (25.4 → 50.4 MB at rung-10000, not graded because no record sets a bar) — a new prediction id with a bar | a bar invented after the number is post-hoc; register it as *the next* generation's bar | SR-INDEX-LIFECYCLE, SR-RS |
| 10 | **Remove the bare-`str` fetcher return ramp in 3.0** (B-100) | **yes** — 3.0 is the breaking major (`fetch=` mandatory, `update` deleted); no consumer fetcher outside this repo is known | unmeasurable either way | SR-FETCHER d2 |
| 11 | **Does `separation` stay the band's quantity at all?** (B-114) | **keep as the label's quantity, stop calibrating it** — d17 found it does not carry correctness; recalibrating a non-predictive number for RRF is moot | the band then rests on a quantity the record calls non-predictive | SR-CONFIDENCE d17 |
| 12 | **Tabular latency: cascade or the declined constant** (B-120, B-044→B-262) | **cascade, measured first** — `recall@k` stage-1 is the gate; the plan is in [`measurement-plan-2026-10`](../proposals/measurement-plan-2026-10.md) §5 | the declined degrade-to-bands constant is one line | SR-TABULAR, SR-CHUNKING |
| 13 | **CAP-3's query set** (B-128) | the retired sets (1–3) — open, reusable, no key needed | timing on retired sets is `informed` by construction | SR-WORK-BENCHMARK d1 |
| 14 | **Collect a query log?** (B-137) | **not now** — nothing waits on it except B-093's cache trace; decide when a consumer exists | the judgment supply argument in SR-LAWS d8 | SR-LAW-9 |
| 15 | **SR-RS d12's scope defect** (B-174) | the trigger fired 2026-08-27 (fourth disclosure); **re-word d12** along the record's own contamination table (an evaluation set can be contaminated; bytes and wall-clock cannot; chosen-sample latency *partly*) | his ruling *"text stands, do not narrow"* predates the trigger he set | SR-RS d12 |
| 16 | **Component records must own something?** (B-055) | **yes, with a named exemption list** — ten records carry `owns: []`; adopt the proposed rule, exempt by name | an exemption list is the threshold d6 refused | SR-WORK-OWNERSHIP d11 |
| 17 | **Key-scoped `describes`** (B-060) | **the cheap half**: symbol-narrow the three `config.py` rows via the W-140 row-20 mechanism; the key grid stays declined | the over-firing is only mostly fixed by narrowing | SR-WORK-OWNERSHIP d10 |
| 18 | **L4 and a query-time model** (B-162) | **amend L4** to bar a model *call* on the maintenance **or** query path while permitting a pinned, committed derived artefact (`V/`) — the differential law already makes a query-time model impossible, so the law costs nothing and restores the co-guard L2's amendment removed | written wide it pre-empts B-245's vector plane; hence the artefact carve-out | SR-LAW-4 (a Law — his word only) |
| 19 | **WORKLOG cut** (B-246) | cut at each **v-major** into `archive/worklog/`, not yearly (aligns with CHANGELOG; fewer seams) | WORKLOG is link-exempt and grep-searched for history | SR-WORK-GOVERNANCE |
| 20 | **Kiro's ambient pointers** (B-170) | fold into [`cross-model-agent-guides`](../proposals/cross-model-agent-guides.md) as its first concrete case; interim: write the Kiro steering set only under `--agents kiro-ide` | B-251's trigger is a mis-trigger, not a token tax | SR-AGENT-POLICY d15c |
| 21 | **B-048's two-strikes** — IMPLEMENTATION names *"the W-83 class"* twice since; does *"a check that cannot exist"* still stand? | **it stands** — SR-LAW-0 §What is gated argues it; confirm so the row rests in `cost` B-252 | the rule says twice → a gate | SR-LAW-0 |
| 22 | **A required check on `main` for the differential arms** (B-076, second half) | **no** — SR-WORK-RELEASE d10 keeps merges ungated by design; the import-smoke half is W-246 | a schedule is not a gate | SR-WORK-RELEASE d10 |
| 23 | **An enriched rung** (B-108, B-109, B-110, B-245's second condition) | **produce one**, model-generated questions over rung-01000 with `enrich=true` — the only deliverable four rows wait on; it is his tokens | cost | the measurement plan §7 |
| 24 | **Real-network captures** (B-101, B-102, B-093, B-124's live half) | one hands-on session on his machine: signed-in Chrome against session-gated sources, a real rate-limit, a journalled answer whose source then disappears | his time | the measurement plan §4 |

## Definition of done

1. Every §3 line has his word — *yes*, *no*, or his own ruling — written back
   into this file beside the line.
2. Each *yes* is either a W-245 sentence or a new `W-nn`; each *no* repoints or
   deletes its row in [`BACKLOG.md`](../BACKLOG.md) **in the same change**.
3. The three compare docs carry a verdict block that is no longer `proposed`.
4. This file archives with its row.

## Hazards

- ⚠ **Rule 25 was applied, not assumed:** every deleted row's statement was
  checked for a second home before deletion; B-232 was the one row that *was*
  the only home, and it is B-260 now.
- ⚠ **The cost class grew by seven rows and that is correct** — a `cost` row
  is an argument that has been had, written down so nobody reopens it.
- A concurrent Claude Code session closed W-242 (Tier 2, 3.0.0-alpha.10) in the
  same tree while this audit ran; nothing here touches `src/`, `node/` or `tests/`.
