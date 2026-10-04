---
type: Handoff
name: W-251
description: "The 2026-10-03 backlog audit — every B-row read against its source. 66 stale rows deleted, 31 rows promoted into seven agent items, two dozen record sentences found false or stale (W-245), and the forks that needed Arpit's own word gathered as one inbox row. 2026-10-04: 12 of the 24 forks ruled by delegation (§4), 3 ruled in part, 11 lines left that are his alone (§3) — two Laws, three options he personally declined (#15 returned by the Opus review), two reservations in his name, a taste call, a frozen surface, his tokens, his hands."
item: W-251
filed: 2026-10-03
ball: arpit
---

# W-251 — the backlog audit: what was ratified, what waits on Arpit

**Model:** none — this item is a list of rulings. Each *yes* below lands through
W-245 (a record sentence) or a new item;
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
| B-040 | W-247 | `cmd_*` render what `fux.api` builds; one payload, one place |
| B-007 | W-248 | `fux enrich`'s worklist is declared scope ∪ the decoder queue's *model-needed* rows |
| B-034 | W-249 | `fux mcp` / `fux serve` hold the index open, keyed on `.fux/runtime/stamp.json` — index residency, **not** W-242's refused T3 memo |
| B-037 | [W-250](W-250-dogfood-fux-hooks.md) | run `fux hooks` in this repository |
| B-125 | [W-252](W-252-node-arm-preregistration-2.md) | `PRE-REGISTRATION-NODE-2` on lab rungs, so the Node arm can be called green |
| the stale sentences | W-245 | eleven record sentences the audit found false against the code or stale against a later decision |

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

## §3 — 🔴 For Arpit — the lines only he can answer

**Second delegation, 2026-10-04** (Arpit, Cowork, verbatim): *"Review open
work and backlog. Ratify whatever you can. Think about it, research and ratify
whatever you can. For backlog, create proposal documents with ratified or
recommended approach. Create a compare if needed or if there are multiple
approaches. And go for it. Once everything is done, I want Opus 5.5 to review
it."* Seven research passes re-read every cited record and the code behind each
of the 24 lines below. **Where the evidence settles a line and no Law, no option
he declined in person and no reservation written in his name stands in the
way, it is ruled in §4.** What is left here is his alone. Numbers are the
original ones, so a line can be named across sessions.

| # | fork (rows) | recommendation, corrected | why only he can | yes lands in |
|---|---|---|---|---|
| 1 | **The `enriched` ingest mode** (B-006): sign off, or retire it | **Retire the mode unbuilt — and KEEP edge grade `6` reserved** for inferred edges. Yesterday's line said *release grade 6*; that collides with #3's surviving candidate (inferred edges *"must carry `INFERRED`"*, SR-ENRICH §candidates) — so the grade stays, the mode goes. Nothing moves under L1: SR-ENRICHED is already archived (`archive/adr-old/0017`); this is an in-record strike-through of the folded section (0137:304–371), SR-EXTRACTED d3's *"until the `enriched` mode is built"*, CLAUDE.md's *two ingest modes*, GLOSSARY, and the schema enum `["extracted","enriched"]`. **S, Sonnet** | he ratified the mode by name on 2026-08-19 (W-30); the sign-off half is his, so the retirement is the symmetric half | SR-ENRICH folded d1–d6, SR-EXTRACTED d3, CLAUDE.md, `index-record.schema.json` |
| 2 | **Consumer-side template refresh** (B-013, B-014) | **A or B** of [`consumer-template-refresh`](../compare/consumer-template-refresh.compare.md). ⚠ Corrected: option A is **not** the variant he declined — the declined one (2026-08-26, W-86 P7) was *copy inert, built-in runs*; A keeps *the copy runs* (d8/d10) and adds *an unedited copy is refreshed on upgrade*. It still crosses three fences in his name: SR-DOTFUX d6 *"never a rewrite"*, SR-FETCHER d12 (his, 2026-08-28), and L10's *"seeded once, then the consumer owns it"*. **B** (stamp + `doctor` names the gap, never writes) crosses none and is the d6-conformant mechanism | declined in person; touches L10's text | SR-DECODE d10, SR-DOTFUX 6a, SR-FETCHER d12, L10 (if A) |
| 3 | **`find --no-archived`** — the one build left of the query-side lens (B-143) | **Yes, small**: a REMOVE-only filter on the declared `archived` fact in SR-FIND d7's shape, `band` computed unfiltered (d9), Node twin trivial. **S, Sonnet.** The other four parts of the lens are ruled in §4 | taste — he stopped W-168's last query-side steps before gen-4 scores, and nobody has asked for the filter in words (the compare's *"what do we do now?"* is d6's own probe phrasing) | SR-FIND d7 + a `W-nn` |
| 4 | **The graph verbs' `--json` shape** — B-147, the one row of the parity fork left | ⚠ **Direction reversed from yesterday.** The library's `explain`/`graph`/`path` shapes are the *unruled* ones (*"predates this record"*); the CLI's carry rulings — SR-CLI d13, SR-GRAPH d13 (lexical seeds; the library seeds from the boosted ranking, the *"walk over its own output"* the record warns against), and **his** `truncated` on `path` (W-140 row 12). So converging *on the library* deletes ruled content and moves two CLIs (Python and Node). Recommendation: **library → CLI shape**, which reopens SR-API d1's freeze | either direction touches a shape he ruled or the surface he froze | SR-API d1/d6 or SR-CLI |
| 9 | **A size prediction at 10 000** (B-099) | **His word on two things**: accepting the section plane's **+98.4 %** (25.4 → 50.4 MB at rung-10000, the VERDICT hands it to him) and whether an **R-series** size promise returns at all — R7 was retired in his words, *"Remove that promise, it's not needed … no successor is owed."* **Agent alternative, no word needed:** a `W`-id regression bar on the *built* gen-4 plane under W-236 Part B, pre-registered before that build runs (≤ 2.0× the doc plane and ≤ 55 MB; largest file ≤ 1 MiB), labelled post-hoc-informed — a feature gate, not an architectural claim (the register's R/W split) | reviving a promise he declined; accepting a cost he has seen | SR-INDEX-LIFECYCLE, SR-POSTINGS Consequences; W-236 |
| 16 | **Component records must own something** — the strong rule (B-055) | The strong rule (*a `component` record must own something*) and the per-record verdicts for the ten `owns: []` records stay his. **The weak rule is ruled in §4** | `records/README.md` §The three kinds: *"That is Arpit's call, one record at a time"*; d11 is in his name | SR-WORK-OWNERSHIP d11 |
| 18 | **L4 and a query-time model** (B-162) | Amend L4 — **draft, for yes/no:** *"Deterministic — no model call on the maintenance or query path. … No maintenance path (`ingest`, `daemon`, hooks) and no query path (`ask`, `find`, `answer`, `explain`, `graph`, `path`, `serve`, `mcp`) may ever call a model — not to be smarter at ingest, not to summarize, not to rerank, not once. A model's output enters fux only as a pinned, committed, sha-keyed artefact produced by its own deliberate command and then read deterministically; a vector the caller supplies is input, not a call."* Forbids: a cross-encoder/ONNX at query time (SR-RERANK d1a becomes law; its veto 1 then needs L4 amended, not a record); any fux verb embedding the query. Permits: `fux enrich`, a committed `V/` plane, `--qvec`. ⚠ Decide `fux embed` explicitly — it would call a consumer embedder from inside a fux verb; put it on the enrich side (own command, pinned) or forbid it | a Law (SR-LAW-0 d3) | SR-LAW-4 + `gen-laws.py --write`; SR-LAW-2 trade 2; SR-RERANK veto 1 |
| 22 | **A required check on `main` for the differential arms** (B-076, gate half) | **No, not now** — the release is the gate (SR-WORK-RELEASE d11a) and `enforce_admins: true` would block the direct pushes d13 (his, 2026-09-29) permits. ⚠ Corrected: d10 is *descriptive*, not a ruling; the record's Alternatives say outright *"Not rejected — not decided. It is Arpit's call"* | an explicit reservation in his name | SR-WORK-RELEASE §Alternatives |
| 25 | **L3's `snapshot` sentence** (B-154, the Law half) | L3's text says *"The single exception is explicit per-source `snapshot` policy"* while SR-LAW-3 §1 lists **three** exceptions and no `snapshot` mechanism exists anywhere. **Keep the word as the reserved hook** (cheaper than re-litigating a committed copy for air-gapped consumers later) **or** re-point: *"The only exceptions are declared per source on a committed line the operator wrote — §1 names them; none is built as a committed copy today."* The grammar half is ruled in §4 | a Law | SR-LAW-3 + `gen-laws.py --write` |
| 15 | **SR-RS d12's scope defect** (B-174) — ⚠ **returned from §4 by the Opus 5.5 review, 2026-10-04** | **Yes, re-word it along the record's own contamination table** (the §4 text, unchanged): a delta is forbidden on an *evaluation-set metric* (nDCG, pass@k, hit@k, fixed/broken on a golden set); bytes on disk, wall-clock and wheel size may be stated; a latency on a chosen query set may be stated with the sample's authorship disclosed (d13). Block header → *REPAIRED <date> — the trigger fired 2026-08-27* (three genuine disclosures: model-removal, rank-flip-susceptibility, p3-sha-stability); the *"Arpit ruled the text stands"* paragraph stays as the argument | **This is the option he declined in person** — the block records *"No narrowing to evaluation-set metrics"* and *"Do not narrow decision 12. Disclose."* — which is exactly the class §3's own test reserves to him. His trigger (*"Reopen when the disclosure has been written three times"*) has fired, so the question is **open again**; it does not say who closes it, and a measurement-integrity rule he ruled on personally is not one an agent narrows by reading its trigger as a pre-authorisation. The wording is ready; the yes is his | one record edit, SR-RS d12 (the text above); B-174 stays deleted — this row is its home |
| 23 | **An enriched rung** (B-108, B-109, B-110, B-245 condition 2) | **Filed as [W-257](W-257-enriched-rung.md)** with the blind-author protocol the plan missed (SR-RS d11: an author who has read any question set yields an `informed` rung and the three rows get no delta). The launch is his tokens | his tokens | W-257 |
| 24 | **Real-network captures** (B-101, B-102 live, B-124 live) | **Filed as [W-258](W-258-live-network-captures.md)** — one hands-on session, in the order B-124 live (20 min, no credentials) → B-102 (a public 429 host) → B-101 (signed-in Chrome, ≥ 12 session-gated URLs). The loopback halves and B-103 are agent work and went to [W-256](W-256-no-key-measurements.md) | his hands | W-258 |

**Default if unanswered:** the recommendation stands as *recommended*, not
ratified, and each row stays where it is.

---

## §4 — Ruled 2026-10-04 by delegation

Each line below is ruled under the 2026-10-04 delegation quoted in §3, by the
test §3 states: the evidence settles it, and nothing in the way is a Law, an
option he declined in person, or a reservation written in his name. **A ruling
here is reversible by one word from him**; the Opus 5.5 review he asked for
reads this table first. *Lands in* names where the sentence or the build goes:
a W-245 row (the record sentence), a new
item, or a `BACKLOG.md` move.

| # | fork (rows) | ruling | the evidence that settled it | lands in |
|---|---|---|---|---|
| 3 | **Query-side lens, four of five parts** (B-143, B-144, B-145) | (2) **`--as-of` refused.** (1) **`--intent` as a flag refused — reworded**: *doc-type* intent is SR-RANKING d13; the *history/current* intent the three records actually named stays OUT by his S1 ruling (SR-TUNE d20, 2026-09-24) and only he reopens it. (4) **`supersedes:` stays a declared fact**; the concept question closes. (5) Candidates: **inferred edges and richer embeddings remain**, behind B-245; semantic expansion is served by doc2query `ctx` (SR-ENRICH d15) and caller `--expand` (SR-EXPAND d1), mined pairs (**d18**, not d17 — d17 is RM3's removal) cover declared abbreviations; retirement flags → `superseded_by:` (SR-ENRICH d17) | `mtime` is a checkout artefact / `null` off git (SR-API d7 🔴); his SR-WORK-TESTDATA A21/R5 *require* `supersedes:`; the intent lexicon (`constants.toml:627–644`) has no now-vs-before cue, so the shipped prior never answered d6's question | W-245 (SR-TUNE d15c, SR-ARCHIVED-CONTENT d6, SR-API d7, SR-ENRICH §candidates); B-144 deleted, B-143/B-145 reworded; [compare](../compare/query-side-lens.compare.md) verdict |
| 4 | **CLI ↔ library parity, three of four rows** (B-146, B-148, B-151) | **B-146 ratified:** `--under` applies a component boundary on both CLIs and `Weighting.priority_for` gains it. **B-151 ratified:** `find --json` writes `confidence` before `fused`, documented and tested. **B-148 REFUSED** (the compare recommended yes): a `changed_since` field whose value depends on the previous run's gitignored `last-cited.json` makes `answer --json` differ between two machines on identical bytes — the class SR-CLI veto 5 forbids; stderr stays the home | Node's `priorityFor` (`rank.mjs:65`) **already** applies the boundary while Python's does not — a cross-runtime divergence the arm cannot see (needs a `[priority]` key colliding with a sibling); SR-TUNE d8 + SR-DIR-LIST 2e make the key a directory, not a string prefix; SR-FIND says the key order is *"not a decision anybody took"* | W-253; W-245 (SR-FIND d7 + Consequences, SR-TUNE d8a, SR-API d6, SR-ANSWER d10); B-146/B-148/B-151 deleted; [compare](../compare/cli-library-parity.compare.md) verdict |
| 5 | **`ttl` paces the daemon?** (B-027) | **No — nothing owed.** `ttl` is ask-time (SR-URL-FRESHNESS d15 🔴), `update=` is the only update-time attribute (SR-URL-LIST d14, his R-1), the daemon's one clock is `sweep_minutes` (SR-MAINTENANCE 9d refuses adaptive scheduling). A `ttl`-ordered sweep would be the third clock d15 exists to prevent | the *Owed* line (2026-09-01) predates d14/d15 and contradicts them; `daemon.py:325–357` sweeps every line, no ordering | W-245 (SR-URL-FRESHNESS Consequences); B-027 deleted |
| 6 | **Node twins for `verify`, `--why`, `--receipt`, `--journal`** (B-033) | **Declared OUT OF SCOPE on the Node reader, in d18's shape — not "permanent"**: a new SR-NODE-SEARCH decision 25 naming what reopens it (a consumer asks for verification where no Python runs). ⚠ Corrected: there is no "subset table" to add rows to; the record's idiom for a declared gap is d18 | the absence was already his (frontmatter *"ratifies: Arpit, 2026-09-12 — R1–R6"*); nothing structural forbids the four — `verify` never fetches (SR-PROVENANCE d14, his), `--journal` writes a gitignored log — they are unbuilt because nobody asked | W-245 (SR-NODE-SEARCH d25 + Consequences); W-252's pre-registration lists the four as excluded; B-033 → `cost` B-263 |
| 7 | **`fux pii-probe` as a verb** (B-038) | **No verb.** ⚠ Two corrections to the record: the rule is SR-CLI **veto 6** (a verb appears only with promotion evidence — a caller), not veto 1 (which is about nesting); and the `fux-pii` skill carries a **reduced** probe (git-tracked plain text, digests not values), not *"a standalone copy"* — the repo tool also reads decoded and `url:` documents. Reopen trigger: a consumer asks to probe decoded or `url:` documents, which only the engine can do | d20 was a session's fix (W-140 row 18), not his ruling; nobody has pointed at a caller | W-245 (SR-PII d20); B-038 → `cost` B-264 |
| 8 | **TTL store cap** (B-092) | **Accepted — a design default, not a measured one.** It is `fux.toml [refer] fetch_cache_max_bytes` (L12 d1), a consumer turns it, no measurement picks a byte cap. Wording: `524288000` is 500 **MiB** | `refer/__init__.py:183` reads the key; the only literal is in the template; Node never fetches | W-245 (SR-CACHE d9, check #5); B-092 → `cost` B-265 |
| 10 | **Remove the bare-`str` fetcher ramp in 3.0** (B-100) | **Yes.** `fetch` returns `tuple[bytes, str]`; a `str` is refused with a `FuxError` naming the fetcher and the contract (a named skip, never a crash — d2 still governs). Remove the `str`-inside-tuple coercion too: one contract | the protection is **already void**: 3.0.0-alpha.2 (SR-URL-LIST d16/d17, his breaking change) made every pre-2026-08-26 repo rewrite its URL lines, so the ramp protected nothing the major had not broken; SR-FETCHER 17d already names it as contradicting the pipe ruling; no shipped template returns `str` | W-253 (code + SR-FETCHER d2/17d + CHANGELOG); B-100 deleted |
| 11 | **Does `separation` stay the band's quantity?** (B-114) | **Keep it, stop calibrating it.** `separation_floor` is not recalibrated — not for RRF (SR-EXPAND d10), not for any arm: d17 measured that it does not carry correctness, so a calibrated floor on it would be a calibrated non-predictor. The next lever is `doc_coverage_floor` — W-256 §2 | `confidence.py:209–211` is the only branch on it and feeds a label that refuses nothing since W-214; d17 did **not** establish worse-than-random (p = 0.25) | W-245 (SR-CONFIDENCE Consequences); B-114 → `cost` B-266 |
| 12 | **Tabular latency** (B-120, B-262) | **Nothing to rule.** B-120 is a **reopen trigger, not a debt** — SR-TABULAR's own words: *"if the ~2.6 s … is reported as a blocker by anyone actually using it, the declined alternative above is the answer, and it is one constant"*; the trigger has not fired (rule 9, the shape §1 used to delete B-003). B-262 stays `unmeasured` with its gate. ⚠ Corrected: plan §5 said gen-4 lacks *"the tabular seed documents SR-WORK-TESTDATA T-rows describe"* — **no T-row names tabular documents**; a T15 is the prerequisite | the degrade-to-bands constant was declined by Arpit (2026-09-06) *with* a trigger attached | B-120 deleted; B-262 closer and plan §5 reworded |
| 13 | **CAP-3's query set** (B-128) | ⚠ **Yesterday's recommendation was wrong.** CAP-3's set *is* stated — `judged.jsonl` + `key.jsonl`, planted by the generator (SR-WORK-BENCHMARK d3) — just not in d1's text. The retired golden sets belong to the golden ladder in fux-lab; a golden question has no relevant document in a fux-benchmark tier, and moving golden data into the benchmark re-crosses SR-WORK-ENVIRONMENTS' line. Ruling: **d1 names the sets** — timing captures run on `queries.jsonl`, CAP-3/CAP-4 on the judged set; the timing set keeps no key | the filed run (`2026-09-13-benchmark-captures/report.md:70–91`): *"CAP-3 — hit@k, 42 judged questions"* | W-245 (SR-WORK-BENCHMARK d1 + Consequences ⚠); B-128 deleted |
| 14 | **Collect a query log?** (B-137) | **Not now.** The opt-in journal (SR-PROVENANCE d10, his: always-on *"is still refused"*) is the only lawful collector and the project runs none; a supply graded from it is `informed` (SR-RS d11) and can ground a regression claim, never a golden one. Making fux collect is his (reverses d10); a transmission clause is a Law change (L9) | `provenance.py:834–870` — the journal exists, default off, both consent surfaces tested | W-245 (SR-LAW-9 Consequences — wording only); B-137 reclassed `unruled` B-268 (rule 22) |
| 16 | **Component records — the weak rule** (B-055, half) | **A `kind: component` record with `owns: []` must carry a `describes` row on a `src/` component and name, in its own body, which of d7's two cases it is.** The strong rule stays proposed (§3 #16) | `records/README.md` already asserts the first half is true (the ten left `_UNREACHABLE_BY_THE_GATE` via `describes` on 2026-09-21); four of the ten (SR-FIND, SR-URL-INGEST, SR-DIR-LIST, SR-CACHEDIR-TAG) state no case today | W-246 (one stdlib test); W-245 (SR-WORK-OWNERSHIP d11 + four record paragraphs); B-055 reworded |
| 17 | **Key-scoped `describes`** (B-060) | **The cheap half**: the three `config.py` rows narrow to `src/fux/config.py::UrlSource,_load_url_source`; SR-DOCTOR d1's *"which the describes table cannot express today"* → *"expresses at symbol, not key, granularity (W-140 row 20)"*. ⚠ Weaker than claimed: the motivating `"codex"` edit was **module-level** (`KNOWN_AGENTS`), and `changed_symbols` demands everybody for a hunk outside any def — so that case is **not** fixed; narrowing helps only for edits inside other defs. Said so in d10; the key grid stays declined | symbol narrowing is a shipped, decided mechanism (d10 addendum, 2026-09-11), applied to three rows — register maintenance, not reopening the declined grid; the keys live in `UrlSource` (line 214) and `_load_url_source` (line 710) | W-245 (`records/README.md` describes table ×3, SR-WORK-OWNERSHIP d10, SR-DOCTOR d1); B-060 deleted |
| 19 | **WORKLOG cut** (B-246) | **Cut at each v-major, first at 3.0.0 GA**: in the change that tags `vN.0.0`, every entry dated before the tag moves verbatim to `archive/worklog/WORKLOG-v<N-1>.md` (newest first), one `archive/README.md` row names `work/WORKLOG.md` as successor; the move is SR-WORK-SESSION d2's mechanical exception; an archived entry keeps SR-WORK-OPEN-QUEUE rule 58's status (history of a closure) and backs no live claim (SR-WORK-ARCHIVE d5); the veto grep spans both | 13 945 lines / 1.51 MB / 626 entries; majors land every ~3 weeks so *yearly* never fires in time; `archive/**` is already link-exempt in every test (`test_doc_links.py:60`, `test_law_handles.py:47`, `test_archive_law.py:49`); no test reads WORKLOG content | W-245 (SR-WORK-SESSION new decision + Consequences, SR-WORK-GOVERNANCE table + Consequences, SR-WORK-ARCHIVE d2); B-246 deleted |
| 20 | **Kiro's ambient pointers** (B-170) | **`cost`, not a fold-in and not a flag.** 15c already states the cost (10 985 B measured, the `~10 KB` claim is accurate), the bound (`POINTER_MAX_BYTES = 1200`) and the exit (`[agents] install` without `kiro`). The interim *"`--agents kiro-ide`"* **cannot be built as written** — no `--agents` flag exists (only `--no-agents`), vendors come from the closed `KNOWN_AGENTS`, and a vendor-*version* enum is the catalogue-that-rots the record's §3 rejects; fux cannot observe the CLI version (d5). Not folded into B-251: that proposal is about *model* behaviour and says *"Not a per-model file set"*; B-170 is a vendor-CLI capability fact | `setup.py:380–395`, `cli.py:365`, `config.py:174`; Kiro CLI 3.0 reportedly honours inclusion modes, so the tax is shrinking on its own | W-245 (SR-AGENT-POLICY 15c append); B-170 → `cost` B-267 |
| 21 | **B-048's two-strikes — does "a check that cannot exist" stand?** | **It stands.** Prose self-contradiction inside one record has no parser; L0's answer is one source + generated copies. ⚠ Named precisely so the label stops drifting: *"the W-83 class"* is prose-vs-prose only — a row/frontmatter or code/docstring drift is a different class and **may** be gated (the row-ball check already exists). No record edit; B-252 carries the sentence | IMPLEMENTATION names the class three times, not two (lines 1745, 2008, 3253); only the third is the strict class | B-252 row reworded |
| — | **B-150 — the passage carries the frontmatter block** (`unruled`) | **A leading frontmatter block is its own passage UNIT** — heading `""`, never folds forward, detected with `frontmatter.parse` (shared with ingest, never reimplemented) and only on the undecoded path (decoded Markdown may legitimately begin with `---`, `parse.py:30–35`). Line ranges stay exact, every byte still lands in exactly one passage, the block stays quotable and stays indexed at document level (W-205). New SR-CHUNKING decision; SR-ANSWER's consequence sentence closes | SR-ANSWER delegated it (*"`chunk.py`'s call, not this record's"*); `_chunk.py:245+` `_fold` rides the preamble into the first section, so d16's rescoring hands the first passage extra tf from `title:`/`description:` words today | W-254; B-150 deleted |
| — | **B-154 — `snapshot`, the grammar half** (`unruled`) | **No `snapshot` attribute in 3.0.** The per-source retention that exists is `keep=` (SR-ACQUIRED d4), gitignored by L3 d4. A *committed* copy of content is L3's reserved exception and opens only by amending L3 — never by a grammar row (the Law half is §3 #25) | `snapshot` exists nowhere in `src/`; SR-URL-LIST §Considered itself says *"an L3 decision, not a grammar one"* | W-245 (SR-URL-LIST §Considered row); B-154 reworded to the L3 half |
| — | **B-260 — a pathological PII regex** (`unbuilt`) | **(a) + (e)** of [`pii-regex-bound`](../compare/pii-regex-bound.compare.md): a **stdlib static linter at load** (`re._parser` AST: refuse an unbounded repeat whose body holds another unbounded or variable repeat, and a backreference inside an unbounded repeat — the classic ReDoS class) is the only decision that cannot differ between machines, so it is the only one allowed to decide an ingest; plus a **`doctor` stress-timing row** (fixed adversarial strings, `fux.toml [doctor] pii_rule_budget_ms`), where wall-clock legitimately lives — advisory, never a committed byte. The `regex` dependency with `timeout=` is the reopen trigger, not the answer: it puts a clock in the write path and would be fux's first runtime dependency | `_sre` holds the GIL for the whole match, so a watchdog thread cannot interrupt and `signal.alarm` is POSIX-only — option (b) is infeasible, not just non-deterministic; the shipped email rule is quadratic on a long `@`-less run, which (e) shows and (a) cannot | W-255; B-260 deleted |
| — | **B-002, B-098, B-113, B-261 gate 2, B-103, loopback halves of B-102/B-124** (`unbuilt`/`unmeasured`) | **Measure first, with what exists** — the plan's sections that need no key and no hands: §8 (the delta/full split — B-002 is ruled *on the number*: if the non-extract phases are < ~5 s at rung-10000, the dirty list stays advisory and SR-MAINTENANCE 1a-3 cites the run; else a runtime parse cache becomes an item), §2 (`doc_coverage` AUC over the W-213 rows — gate 2, then SR-CONFIDENCE d12 and #11's next lever), §4 lab-side (B-103 Windows daemon e2e, B-102 loopback 429, B-124 loopback `as-ingested`) | the W-213 captures (2 992 rows, 3 retired sets × 8 rungs) carry `doc_coverage`; `phase_times.py` exists; nothing waits on a key | [W-256](W-256-no-key-measurements.md); B-098, B-113, B-103 deleted (promoted); B-002, B-261 reworded |
| — | **B-031, B-041, B-259** (`unbuilt`, `ungated`) | **Approaches ruled, builds parked** in [`build-plan-2026-10`](../proposals/build-plan-2026-10.md): B-031 — the `add`/`remove --json` shape is **declared** in SR-CLI as *declared, not shipped*, with its trigger (a `fux_add` MCP tool or `api.add` is proposed); B-041 — fence-aware grammars in **one** module both consumers import, dispatch on extension, Node twin for refer parity (decoding the three to Markdown was rejected: they would leave `prose_types`, so Node would stop citing them, and frontmatter would stop being parsed); B-259 — `unicodedata`-based column width, no dependency, the function and tests sketched | SR-CLI's own rule is *wait for a caller*; no corpus here carries `.rst`/`.adoc`/`.org`; `progress.py:134–157` has four `len()` sites | W-245 (SR-CLI Consequences, the shape); rows reworded; B-269 (the plan's row) |
| — | **Citation fixes** | SR-ENRICH "d6" (B-006, W-251 §3 #1) → **SR-ENRICHED folded d6** (0137:367 — main d6 is the tilt); CLAUDE.md:101 *"SR-ENRICH decision 8"* → the same folded d6 (main d8 is *frontmatter stripped*); SR-EXPAND "d17" for mined expansion → **d18** | read against the record | W-245 (CLAUDE.md — a fact fix, exempt under SR-WORK-DOCS d8); this file |

## Definition of done

1. Every §3 line has his word — *yes*, *no*, or his own ruling — written back
   into this file beside the line.
2. Each §4 ruling has landed: its W-245 row written and restamped, its item
   closed, its `BACKLOG.md` move done. Each *yes* in §3 becomes a W-245 row or
   a new `W-nn`; each *no* repoints or deletes its row **in the same change**.
3. The four compare docs carry a verdict block that is no longer `proposed`
   (three are ruled in part today; what is left of each is a §3 line).
4. This file archives with its row.

## Hazards

- ⚠ **Rule 25 was applied, not assumed:** every deleted row's statement was
  checked for a second home before deletion; B-232 was the one row that *was*
  the only home, and it is B-260 now — promoted to W-255 on 2026-10-04.
- ⚠ **The cost class grew by seven rows on 2026-10-03 and five more on
  2026-10-04, and that is correct** — a `cost` row is an argument that has been
  had, written down so nobody reopens it.
- ⚠ **§4's rulings are delegated, not his.** The delegation is quoted verbatim
  in §3; the test it was applied by is stated there; the one ruling that touches
  text he said *stands* (#15) was flagged in its own row. **The Opus 5.5 review
  (2026-10-04, the green-items session) returned #15 to §3**: it is the narrowing
  he declined in person, and a fired reopen-trigger reopens a question without
  saying who closes it. Every other §4 line was applied as ruled (W-245, W-253,
  W-254, W-255). One word from him reverses any line.
- ⚠ **Yesterday's §3 carried four factual errors** that the 2026-10-04 research
  found — #13 (CAP-3's set is stated), #4 (the parity direction for the graph
  verbs is backwards), #1 (releasing grade 6 collides with #3), #20 (`--agents`
  does not exist). A recommendation column is a claim and is checked like one.
- A concurrent Claude Code session closed W-242 (Tier 2, 3.0.0-alpha.10) in the
  same tree while the audit ran, and another closed W-244 while this ruling
  pass ran; nothing here touches `src/`, `node/` or `tests/`.
