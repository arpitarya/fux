---
type: Compare
description: "W-225 step 1 — every site SR-LAW-12's veto greps find in src/fux and node/src, classified tunable, fixed or not-a-value, with the calls Arpit has not seen listed for his review before step 3. Also records that the veto greps cover about 60 % of what the law forbids."
---

# L12 classify — W-225 step 1

> **Verdict:** ✅ **RATIFIED 2026-09-27 — Arpit: *"I accept the recommendation."***
> R1–R6 and the decoder-cap hazard all as recommended; recorded in
> [SR-LAW-12](../../records/0013_LAW-12-values-live-in-config.md) decisions 1, 6,
> 9a, 9b and §Veto condition. Step 3 is unblocked for these 359 rows; the ~220
> sites R5 found beyond the greps are classified here before step 4.

| | |
|---|---|
| **status** | ratified 2026-09-27. The table is built by a script and checked complete: an unmapped site fails the script. |
| **the call** | the *class* column of §The table, plus Arpit's answers to R1–R6 |
| **confidence** | high on `fixed` and on the tunables that already have a key; medium on the homes proposed for new keys |
| **reopen-trigger** | a veto grep (or its widened successor, R5) prints a site that is not a row here |

## Counts

| class | rows | meaning |
|---|---|---|
| `tunable` | 44 | an existing consumer key already overrides it; only the fallback goes |
| `tunable-new` | 76 | a consumer key must be created (home proposed) |
| `fixed` | 150 | moves to `src/fux/constants.toml` |
| `not-a-value` | 43 | a category SR-LAW-12 decision 6 names |
| `not-a-value?` | 46 | **a category decision 6 does NOT name — R1–R3** |
| **total** | **359** | 273 Python constants + 70 Node constants + 16 Python parameter defaults |

## For Arpit — R1–R6, before step 3

**R1 · Enum tags (42 rows).** Examples: `"grounded"`, `"reproduced"`,
`"stale"`, `"git"`/`"url"`, `"prose"`. Each is an identifier compared by name
and emitted in JSON. Both planes carry it. Decision 6 names *config key names*
but not these.
**Recommend: not-a-value.** Amend decision 6 to name *enum tags and wire
vocabulary*. They are contracts, like key names; a tag in TOML invites someone to
rename a JSON field. The Python/Node parity tests already pin them.
*Alternative:* `fixed`, meaning about 42 more keys in `constants.toml`.

**R2 · `KNOWN_AGENTS` (1).** The closed set that `fux.toml [agents] install`
selects from. **Recommend: not-a-value**, because it is a closed vocabulary.

**R3 · Presentation counts (3).** `MAX_REPORTED` (how many config errors print
at once; one row per plane) and `_number(digits=3)` in inspect.
**Recommend: not-a-value**, as message formatting.

**R4 · Six conflicts that the move to one home forces a decision on.** Today
each is two values that the code keeps consistent by accident. Every choice
below keeps today's behaviour.

| site | the two values | recommend |
|---|---|---|
| `config.py` `FIXED_SHARDS = 256` | `fux.toml [index] shards` also exists | the key is refused unless it equals the constant, so it is `fixed`, and the `fux.toml` key becomes a check |
| `rerank.py` `WEIGHT = 1.0` | `Tune.rerank_weight` ships `0.0` | these are two different knobs: give the query-time one its own key |
| `api.py` `path(hops=6)` | `output.toml [cli.path] hops` ships `2` | the API reads `output.toml` like the CLI does |
| `fetchcache.py` `DEFAULT_TTL_SECONDS = 300` | `Policy` default `0` (the cache is off) | the key ships `0`, and 300 becomes the documented recommended value |
| `urlsrc.py` `UNDECLARED_MAX_PARALLEL = 1` | SR-FETCHER decision 5: *declared, never detected* | `fixed`, not a knob |
| `inspect/facts.py` `DATA_SUFFIXES` | inspect's definition of *data file* | `fixed` |

**R5 · The veto greps cover about 60 % of what the law forbids.** They match
only `UPPER_CASE` module constants and numeric `def` defaults. **Not matched,
counted 2026-09-27:**

- 68 `_PRIVATE` module constants
- 62 dataclass and class-field numeric defaults, including `Tune` itself
- 81 `.get(key, <number>)` fallbacks
- at least 11 Node parameter defaults (`{ top = 5 }`)
- every inline literal inside a function body

A clean grep would therefore **not** mean the law is satisfied.
**Recommend:** widen the veto check into one AST-based test (Python `ast`, and a
tokenizer pass for `.mjs`), and classify that second set before step 4.
Estimated scope: **about 580 sites**, not 360.

**R6 · A new consumer file.** `.fux/inspect.toml` would hold 20 inspect
thresholds and sample sizes. Decision 1 permits a new file. *Alternative:* an
`[inspect]` table in `output.toml`.
**Recommend: the new file.** These values decide what counts as a finding, not
how output renders.

⚠ **A hazard step 3 must carry (the 20 decoder caps).** Examples are
`MAX_INFLATED` and `MAX_CELL_CHARS`. Each cap changes committed bytes. Today a
change to one is released together with a hand-bumped decoder `VERSION` (see
`xlsx.py` `VERSION = 2`). A consumer who edits the key in
`formats.toml [limits.<decoder>]` bumps nothing, so each cap **must enter the
extract-config digest**. Otherwise a changed cap leaves an index that
`fux ingest --check` still calls current.

⚠ ~~**Still open from W-225 §8:** the release vehicle~~ — ruled, R9 below.

## R7–R10 — the R5 scan's new calls, ruled 2026-09-27

The AST scanner (`tests/l12_lib.py`) found **~1 200 distinct sites** in the two
trees. The ratified categories settle most of them — message text, key names,
enum tags, `0`/`1`/`-1`, presentation counts. Four classes were calls nobody
had made. Arpit, the same day:

| # | the class | recommended | **ruled** |
|---|---|---|---|
| R7 | ~450 numbers fixed by a file format, protocol or algorithm (byte offsets, radix, masks, hash IVs, JSON-RPC codes, tuple indices, `indent=2`, heading cap 6, exit codes) | not-a-value | **`fixed` → `constants.toml`** |
| R8 | 45 Python + Node boolean parameter defaults (`refer=True`, `json=False`, `enabled=True`) | not-a-value | **a value — every default removed** |
| R9 | the release vehicle (W-225 §8) | 3.0, breaking | **3.0, breaking** — no auto-`--fix` |
| R10 | `__version__` in `src/fux/__init__.py` | leave it | **leave it** — SR-WORK-RELEASE's |

R7 and R8 went stricter than recommended. Recorded in SR-LAW-12 decision 6a;
decision 6's list is now **closed**. The *"first N, then (+M more)"* cut in a
message is R3's presentation count, not R7.

## Where the build departed from the table — for Arpit's review

Each keeps today's behaviour and satisfies L12; each moves a value to a
different home than the row proposed, because the code said something the
scan could not see. **Say so and any of them flips back.**

| row | the table said | built | why |
|---|---|---|---|
| `graph/walk.*` `EXPANSION_BUDGET` | `tunable-new` → `tune.toml [graph]` | `fixed` → `constants.toml [graph] path_expansion_budget` | an earlier ruling (Arpit, 2026-09-14, `path-hops-bound` option (c)) made it **NOT tunable**: a tune file that widened it would make `--hops 2` mean different things in two repos |
| `graph/community.*` `MAX_SWEEPS` | `tunable-new` → `tune.toml [graph]` | `fixed` → `constants.toml [graph] community_max_sweeps` | it runs in `fux build`, and SR-TUNE keeps `tune.toml` off the maintenance path; the code calls it a determinism backstop, not a knob |
| `query/fuse.*` `K` (RRF k) | not in the table (a one-letter name the grep missed) | `fixed` → `constants.toml [fuse] rrf_k` | the code says *"not tuned here and not a tune.toml key"* — a published constant (Cormack et al. 2009) |
| `query/rerank.*` `WEIGHT` (R4) | two keys, two names | **one key**, `[ranking] rerank_weight` | on inspection `WEIGHT = 1.0` was only an unused parameter default: every production call passed `tune.rerank_weight`. There is no second knob in behaviour; `1.0` is now the template comment's *"when you turn it on"* value, as R4 did for the fetch-cache TTL |
| rerank proximity mix `0.55 / 0.30 / 0.15` | not in the table (inline literals) | `tunable` → `tune.toml [ranking] rerank_base / rerank_span / rerank_adjacency` | weights a person could choose differently |
| `fux path` route limit `10` | not in the table (a parameter default) | `tunable` → `tune.toml [graph] path_limit` | a list length, beside `expand_limit` |
| `query/__init__.*` `ANSWER_TOP = 3` (answer's candidate count) | `presentation` → `output.toml` | `fixed` → `constants.toml [answer] candidates` | it decides which documents the refer plane fetches and re-scores, so it changes what is COMPUTED — SR-OUTPUT decision 2's boundary keeps it out of `output.toml`, and nothing in the product asks to tune it |
| API `graph(query, hops=2)` | `tunable` → `output.toml [cli.path] hops` | **required argument**, no default | `graph()` is a library call whose shape has no `[cli.graph]` table to read; `path()` does read `[cli.path] hops` (R4). A caller now names the depth |

**Two behaviours that are identical at the shipped values and differ only for a
repo that tuned away from them**, stated because no test on an untuned corpus
can see them: `refer/_rescore.py` scored passages at the engine's built-in
BM25F and now scores them at the repo's `[bm25f]`; and `fux enrich --check`'s
self-retrieval filter zeroed `title`/`ctx` on the built-in weights and now does
so on the repo's. Neither had a code default left to read.

## How the table was built

The three veto commands from SR-LAW-12 §Veto condition were run verbatim on
2026-09-27 at `ef7c6c62` plus the uncommitted L12 filing. Each hit was then
mapped by name, and by file where a name is reused, to one class. The mapping
fails on any unmapped site. One site is a false positive: `store/fuxdir.py:308`
sits inside a string of generated source. It is kept, marked `not-a-value`, so
that the count reconciles with the greps.

## The table

Sorted by class, then by site. Literals are cut at 40 characters.

| # | site | name | literal | class | home | why |
|---|---|---|---|---|---|---|
| 1 | `node/src/config/tune.mjs:63` | `DEFAULT_MAX_PHRASES` | `32;` | tunable | tune.toml [index] max_phrases | already overridable |
| 2 | `node/src/config/tune.mjs:64` | `DEFAULT_MAX_TABLE_ROWS` | `20000;` | tunable | tune.toml [index] max_table_rows | already overridable |
| 3 | `node/src/graph/walk.mjs:31` | `DAMPING` | `0.85;` | tunable | tune.toml [graph] damping | already overridable |
| 4 | `node/src/graph/walk.mjs:34` | `ITERATIONS` | `3;` | tunable | tune.toml [graph] iterations | already overridable |
| 5 | `node/src/graph/walk.mjs:37` | `LAZINESS` | `0.5;` | tunable | tune.toml [graph] laziness | already overridable |
| 6 | `node/src/graph/walk.mjs:40` | `HOP_DECAY` | `0.5;` | tunable | tune.toml [graph] hop_decay | already overridable |
| 7 | `node/src/ingest/gitdir.mjs:22` | `DEFAULT_DIRS_FILE` | `".fux/sources/dirs";` | tunable | fux.toml [sources] dirs_file / urls_file | already overridable; the constant is the fallback |
| 8 | `node/src/query/bm25f.mjs:9` | `FIELD_WEIGHTS` | `[1.0, 3.0, 2.0, 1.5, 1.0];` | tunable | tune.toml [bm25f] body…ctx | already overridable |
| 9 | `node/src/query/bm25f.mjs:13` | `K1` | `1.2;` | tunable | tune.toml [bm25f] k1 | already overridable |
| 10 | `node/src/query/bm25f.mjs:27` | `ANCHOR` | `1.0;` | tunable | tune.toml [bm25f] anchor | already overridable |
| 11 | `node/src/query/confidence.mjs:23` | `SEPARATION_FLOOR` | `0.10;` | tunable | tune.toml [confidence] separation_floor | already overridable |
| 12 | `node/src/query/confidence.mjs:25` | `DOC_COVERAGE_FLOOR` | `0.0;` | tunable | tune.toml [confidence] doc_coverage_floor | already overridable |
| 13 | `node/src/query/mined.mjs:18` | `MINED_WEIGHT` | `0.5;` | tunable | tune.toml [ranking] mined_weight | the worked example |
| 14 | `node/src/query/rerank.mjs:53` | `WEIGHT` | `1.0;` | tunable | tune.toml [ranking] rerank_weight | the reranker's uplift cap; ⚠ Tune.rerank_weight ships 0.0 and gates it — two values, one name |
| 15 | `node/src/refer/assemble.mjs:9` | `DEFAULT_BUDGET` | `8000;` | tunable | tune.toml [refer] budget | already overridable |
| 16 | `node/src/refer/assemble.mjs:10` | `PER_DOC_FRACTION` | `0.5;` | tunable | tune.toml [refer] per_doc_fraction | already overridable |
| 17 | `node/src/refer/chunk.mjs:20` | `MIN_PASSAGE_BYTES` | `120;` | tunable | tune.toml [refer] min_passage_bytes | already overridable |
| 18 | `node/src/refer/chunk.mjs:21` | `MAX_PASSAGE_BYTES` | `4000;` | tunable | tune.toml [refer] max_passage_bytes | already overridable |
| 19 | `src/fux/api.py:203` | `find()` | `top:int=5` | tunable | output.toml [cli.<verb>] top / hops | the API default; output.toml already carries top and hops for the CLI |
| 20 | `src/fux/api.py:337` | `graph()` | `hops:int=1, top:int=5` | tunable | output.toml [cli.<verb>] top / hops | the API default; output.toml already carries top and hops for the CLI |
| 21 | `src/fux/api.py:360` | `path()` | `hops:int=6` | tunable | output.toml [cli.path] hops | api default 6, CLI default 2 — two homes, and they disagree |
| 22 | `src/fux/config.py:22` | `DEFAULT_SWEEP_MINUTES` | `60` | tunable | fux.toml [sources.url] sweep_minutes | already overridable; two copies (config.py, daemon.py) |
| 23 | `src/fux/config.py:103` | `DEFAULT_URLS_FILE` | `".fux/sources/urls"` | tunable | fux.toml [sources] dirs_file / urls_file | already overridable; the constant is the fallback |
| 24 | `src/fux/config.py:104` | `DEFAULT_DIRS_FILE` | `".fux/sources/dirs"` | tunable | fux.toml [sources] dirs_file / urls_file | already overridable; the constant is the fallback |
| 25 | `src/fux/graph/walk.py:55` | `DAMPING` | `0.85` | tunable | tune.toml [graph] damping | already overridable |
| 26 | `src/fux/graph/walk.py:60` | `ITERATIONS` | `3` | tunable | tune.toml [graph] iterations | already overridable |
| 27 | `src/fux/graph/walk.py:65` | `LAZINESS` | `0.5` | tunable | tune.toml [graph] laziness | already overridable |
| 28 | `src/fux/graph/walk.py:69` | `HOP_DECAY` | `0.5` | tunable | tune.toml [graph] hop_decay | already overridable |
| 29 | `src/fux/ingest/urlsrc.py:309` | `DEFAULT_MAX_PARALLEL` | `4` | tunable | fux.toml [sources.url] max_parallel | already overridable |
| 30 | `src/fux/maintain/daemon.py:113` | `DEFAULT_SWEEP_MINUTES` | `60` | tunable | fux.toml [sources.url] sweep_minutes | already overridable; two copies (config.py, daemon.py) |
| 31 | `src/fux/query/bm25f.py:65` | `FIELD_WEIGHTS` | `(1.0, 3.0, 2.0, 1.5, 1.0)` | tunable | tune.toml [bm25f] body…ctx | already overridable |
| 32 | `src/fux/query/bm25f.py:74` | `K1` | `1.2` | tunable | tune.toml [bm25f] k1 | already overridable |
| 33 | `src/fux/query/bm25f.py:111` | `ANCHOR` | `1.0` | tunable | tune.toml [bm25f] anchor | already overridable |
| 34 | `src/fux/query/confidence.py:145` | `SEPARATION_FLOOR` | `0.10` | tunable | tune.toml [confidence] separation_floor | already overridable |
| 35 | `src/fux/query/confidence.py:185` | `DOC_COVERAGE_FLOOR` | `0.0` | tunable | tune.toml [confidence] doc_coverage_floor | already overridable |
| 36 | `src/fux/query/mined.py:49` | `MINED_WEIGHT` | `0.5` | tunable | tune.toml [ranking] mined_weight | the worked example |
| 37 | `src/fux/query/rerank.py:92` | `WEIGHT` | `1.0` | tunable | tune.toml [ranking] rerank_weight | the reranker's uplift cap; ⚠ Tune.rerank_weight ships 0.0 and gates it — two values, one name |
| 38 | `src/fux/refer/_assemble.py:67` | `DEFAULT_BUDGET` | `8000` | tunable | tune.toml [refer] budget | already overridable |
| 39 | `src/fux/refer/_assemble.py:70` | `PER_DOC_FRACTION` | `0.5` | tunable | tune.toml [refer] per_doc_fraction | already overridable |
| 40 | `src/fux/refer/_chunk.py:65` | `MIN_PASSAGE_BYTES` | `120` | tunable | tune.toml [refer] min_passage_bytes | already overridable |
| 41 | `src/fux/refer/_chunk.py:69` | `MAX_PASSAGE_BYTES` | `4000` | tunable | tune.toml [refer] max_passage_bytes | already overridable |
| 42 | `src/fux/store/acquired.py:266` | `DEFAULT_MAX_BYTES` | `2 * 1024 * 1024 * 1024` | tunable | fux.toml [sources.url] acquired_max_bytes | already overridable |
| 43 | `src/fux/tune.py:122` | `DEFAULT_MAX_PHRASES` | `32` | tunable | tune.toml [index] max_phrases | already overridable |
| 44 | `src/fux/tune.py:128` | `DEFAULT_MAX_TABLE_ROWS` | `20_000` | tunable | tune.toml [index] max_table_rows | already overridable |
| 45 | `node/src/graph/community.mjs:9` | `MAX_SWEEPS` | `20;` | tunable-new | tune.toml [graph] community_max_sweeps | a loop bound that changes output |
| 46 | `node/src/graph/walk.mjs:219` | `EXPANSION_BUDGET` | `200000;` | tunable-new | tune.toml [graph] expansion_budget | a walk bound |
| 47 | `node/src/query/headings.mjs:12` | `MAX_HEADINGS` | `3;` | tunable-new | output.toml [cli] max_headings | display count |
| 48 | `node/src/query/rerank.mjs:49` | `DEPTH` | `20;` | tunable-new | tune.toml [ranking] rerank_depth / rerank_coverage_power | ranking knobs |
| 49 | `node/src/query/rerank.mjs:58` | `COVERAGE_POWER` | `2;` | tunable-new | tune.toml [ranking] rerank_depth / rerank_coverage_power | ranking knobs |
| 50 | `node/src/refer/assemble.mjs:13` | `CITATION_OVERHEAD` | `80;` | tunable-new | tune.toml [refer] citation_overhead | budget accounting |
| 51 | `node/src/refer/chunk.mjs:23` | `TABLE_ROWS_PER_PASSAGE` | `1;` | tunable-new | tune.toml [refer] table_rows_per_passage | passage shape |
| 52 | `node/src/verbs/answer.mjs:34` | `ANSWER_TOP` | `3;` | tunable-new | output.toml [cli.answer] top | `answer` reads no `top` today |
| 53 | `src/fux/decode/_zip.py:28` | `MAX_UNCOMPRESSED` | `64 * 1024 * 1024` | tunable-new | formats.toml [limits.<decoder>] (NEW table) | ⚠ changes committed bytes — must enter extract-config-digest, or a changed cap leaves a stale index |
| 54 | `src/fux/decode/_zip.py:32` | `MAX_MEMBERS` | `4096` | tunable-new | formats.toml [limits.<decoder>] (NEW table) | ⚠ changes committed bytes — must enter extract-config-digest, or a changed cap leaves a stale index |
| 55 | `src/fux/decode/_zip.py:36` | `MAX_MEMBER_BYTES` | `32 * 1024 * 1024` | tunable-new | formats.toml [limits.<decoder>] (NEW table) | ⚠ changes committed bytes — must enter extract-config-digest, or a changed cap leaves a stale index |
| 56 | `src/fux/decode/csv.py:56` | `MAX_CELL_CHARS` | `500` | tunable-new | formats.toml [limits.<decoder>] (NEW table) | ⚠ changes committed bytes — must enter extract-config-digest, or a changed cap leaves a stale index |
| 57 | `src/fux/decode/drawio.py:45` | `MAX_INFLATED` | `16 * 1024 * 1024` | tunable-new | formats.toml [limits.<decoder>] (NEW table) | ⚠ changes committed bytes — must enter extract-config-digest, or a changed cap leaves a stale index |
| 58 | `src/fux/decode/image.py:57` | `MAX_INFLATED` | `1 * 1024 * 1024` | tunable-new | formats.toml [limits.<decoder>] (NEW table) | ⚠ changes committed bytes — must enter extract-config-digest, or a changed cap leaves a stale index |
| 59 | `src/fux/decode/json.py:47` | `MAX_DEPTH` | `6` | tunable-new | formats.toml [limits.<decoder>] (NEW table) | ⚠ changes committed bytes — must enter extract-config-digest, or a changed cap leaves a stale index |
| 60 | `src/fux/decode/json.py:60` | `MAX_HEADING_DEPTH` | `2` | tunable-new | formats.toml [limits.<decoder>] (NEW table) | ⚠ changes committed bytes — must enter extract-config-digest, or a changed cap leaves a stale index |
| 61 | `src/fux/decode/json.py:64` | `MIN_PROSE_LEN` | `3` | tunable-new | formats.toml [limits.<decoder>] (NEW table) | ⚠ changes committed bytes — must enter extract-config-digest, or a changed cap leaves a stale index |
| 62 | `src/fux/decode/json.py:70` | `MAX_ITEMS` | `500` | tunable-new | formats.toml [limits.<decoder>] (NEW table) | ⚠ changes committed bytes — must enter extract-config-digest, or a changed cap leaves a stale index |
| 63 | `src/fux/decode/jsonl.py:42` | `MAX_RECORDS` | `500` | tunable-new | formats.toml [limits.<decoder>] (NEW table) | ⚠ changes committed bytes — must enter extract-config-digest, or a changed cap leaves a stale index |
| 64 | `src/fux/decode/mail.py:62` | `MAX_BODY_CHARS` | `200_000` | tunable-new | formats.toml [limits.<decoder>] (NEW table) | ⚠ changes committed bytes — must enter extract-config-digest, or a changed cap leaves a stale index |
| 65 | `src/fux/decode/mail.py:66` | `MAX_MESSAGES` | `500` | tunable-new | formats.toml [limits.<decoder>] (NEW table) | ⚠ changes committed bytes — must enter extract-config-digest, or a changed cap leaves a stale index |
| 66 | `src/fux/decode/pdf.py:70` | `MAX_STREAMS` | `5000` | tunable-new | formats.toml [limits.<decoder>] (NEW table) | ⚠ changes committed bytes — must enter extract-config-digest, or a changed cap leaves a stale index |
| 67 | `src/fux/decode/pdf.py:71` | `MAX_INFLATED` | `64 * 1024 * 1024` | tunable-new | formats.toml [limits.<decoder>] (NEW table) | ⚠ changes committed bytes — must enter extract-config-digest, or a changed cap leaves a stale index |
| 68 | `src/fux/decode/pdf.py:72` | `MAX_TEXT_CHARS` | `2_000_000` | tunable-new | formats.toml [limits.<decoder>] (NEW table) | ⚠ changes committed bytes — must enter extract-config-digest, or a changed cap leaves a stale index |
| 69 | `src/fux/decode/rtf.py:60` | `MAX_CHARS` | `2_000_000` | tunable-new | formats.toml [limits.<decoder>] (NEW table) | ⚠ changes committed bytes — must enter extract-config-digest, or a changed cap leaves a stale index |
| 70 | `src/fux/decode/xlsx.py:48` | `MAX_COLS` | `40` | tunable-new | formats.toml [limits.<decoder>] (NEW table) | ⚠ changes committed bytes — must enter extract-config-digest, or a changed cap leaves a stale index |
| 71 | `src/fux/decode/xml.py:37` | `MIN_ATTR_LEN` | `12` | tunable-new | formats.toml [limits.<decoder>] (NEW table) | ⚠ changes committed bytes — must enter extract-config-digest, or a changed cap leaves a stale index |
| 72 | `src/fux/decode/yaml.py:50` | `MAX_DEPTH` | `6` | tunable-new | formats.toml [limits.<decoder>] (NEW table) | ⚠ changes committed bytes — must enter extract-config-digest, or a changed cap leaves a stale index |
| 73 | `src/fux/doctor.py:1674` | `AS_INGESTED_VETO_SHARE` | `0.25` | tunable-new | fux.toml [doctor] (NEW table) | doctor check thresholds |
| 74 | `src/fux/doctor.py:2463` | `THIN_URL_SHARE` | `0.01` | tunable-new | fux.toml [doctor] (NEW table) | doctor check thresholds |
| 75 | `src/fux/doctor.py:2466` | `THIN_URL_CHARS` | `200` | tunable-new | fux.toml [doctor] (NEW table) | doctor check thresholds |
| 76 | `src/fux/enrich.py:64` | `SELF_RETRIEVAL_K` | `3` | tunable-new | tune.toml [enrich] self_retrieval_k | an enrich check threshold |
| 77 | `src/fux/graph/community.py:51` | `MAX_SWEEPS` | `20` | tunable-new | tune.toml [graph] community_max_sweeps | a loop bound that changes output |
| 78 | `src/fux/graph/walk.py:321` | `EXPANSION_BUDGET` | `200_000` | tunable-new | tune.toml [graph] expansion_budget | a walk bound |
| 79 | `src/fux/ingest/refusals.py:126` | `BODY_SCAN_BYTES` | `1024 * 1024` | tunable-new | refusals.toml [scan] | refusal scan window |
| 80 | `src/fux/ingest/refusals.py:131` | `ALWAYS_SCAN_UNDER` | `8 * 1024` | tunable-new | refusals.toml [scan] | refusal scan window |
| 81 | `src/fux/ingest/urlsrc.py:315` | `UNDECLARED_MAX_PARALLEL` | `1` | tunable-new | fux.toml [sources.url] undeclared_max_parallel | ⚠ SR-FETCHER dec 5 calls this behaviour, not a knob — may be fixed |
| 82 | `src/fux/ingest/urlsrc.py:393` | `RATE_LIMIT_RETRIES` | `3` | tunable-new | fux.toml [sources.url] rate_limit_* | fetch politeness |
| 83 | `src/fux/ingest/urlsrc.py:394` | `RATE_LIMIT_BACKOFF_BASE` | `1.0` | tunable-new | fux.toml [sources.url] rate_limit_* | fetch politeness |
| 84 | `src/fux/ingest/urlsrc.py:624` | `THIN_DOCUMENT_WORDS` | `50` | tunable-new | fux.toml [sources.url] thin_* | thin-page detection |
| 85 | `src/fux/ingest/urlsrc.py:636` | `THIN_WORDS_PER_KB` | `2.0` | tunable-new | fux.toml [sources.url] thin_* | thin-page detection |
| 86 | `src/fux/inspect/_scan.py:46` | `BOILERPLATE_DF_SHARE` | `0.50` | tunable-new | .fux/inspect.toml (NEW file) | inspect finding thresholds |
| 87 | `src/fux/inspect/_scan.py:52` | `DISTINCTIVE_DF_SHARE` | `0.10` | tunable-new | .fux/inspect.toml (NEW file) | inspect finding thresholds |
| 88 | `src/fux/inspect/diff.py:107` | `render_markdown()` | `top:int=50` | tunable-new | .fux/inspect.toml (NEW file) | inspect list lengths |
| 89 | `src/fux/inspect/lenses.py:65` | `SIGNATURE_SIZE` | `64` | tunable-new | .fux/inspect.toml (NEW file) | inspect sampling/size |
| 90 | `src/fux/inspect/lenses.py:66` | `BAND_ROWS` | `4` | tunable-new | .fux/inspect.toml (NEW file) | inspect sampling/size |
| 91 | `src/fux/inspect/lenses.py:72` | `NEAR_DUPLICATE_JACCARD` | `0.80` | tunable-new | .fux/inspect.toml (NEW file) | inspect finding thresholds |
| 92 | `src/fux/inspect/lenses.py:226` | `boilerplate()` | `top:int=20` | tunable-new | .fux/inspect.toml (NEW file) | inspect list lengths |
| 93 | `src/fux/inspect/lenses.py:311` | `FINGERPRINT_TERMS` | `6` | tunable-new | .fux/inspect.toml (NEW file) | inspect sampling/size |
| 94 | `src/fux/inspect/lenses.py:315` | `FINDABLE_RANK` | `3` | tunable-new | .fux/inspect.toml (NEW file) | inspect sampling/size |
| 95 | `src/fux/inspect/lenses.py:320` | `DEFAULT_RETRIEVAL_SAMPLE` | `100` | tunable-new | .fux/inspect.toml (NEW file) | inspect sampling/size |
| 96 | `src/fux/inspect/lenses.py:448` | `lengths()` | `top_lists:int=10` | tunable-new | .fux/inspect.toml (NEW file) | inspect list lengths |
| 97 | `src/fux/inspect/lenses.py:501` | `duplication()` | `top_lists:int=20` | tunable-new | .fux/inspect.toml (NEW file) | inspect list lengths |
| 98 | `src/fux/inspect/lenses.py:638` | `graph_shape()` | `top_lists:int=20` | tunable-new | .fux/inspect.toml (NEW file) | inspect list lengths |
| 99 | `src/fux/inspect/probes.py:53` | `PROBE_RANK` | `10` | tunable-new | .fux/inspect.toml (NEW file) | inspect sampling/size |
| 100 | `src/fux/inspect/probes.py:57` | `DEFAULT_PROBE_SAMPLE` | `50` | tunable-new | .fux/inspect.toml (NEW file) | inspect sampling/size |
| 101 | `src/fux/inspect/xray.py:37` | `LINK_TARGET_SHARE` | `0.10` | tunable-new | .fux/inspect.toml (NEW file) | inspect finding thresholds |
| 102 | `src/fux/inspect/xray.py:77` | `fold()` | `top:int=20` | tunable-new | .fux/inspect.toml (NEW file) | inspect list lengths |
| 103 | `src/fux/inspect/xray.py:242` | `document()` | `passages_cap:int=200, words:int=25` | tunable-new | .fux/inspect.toml (NEW file) | inspect list lengths |
| 104 | `src/fux/maintain/daemon.py:108` | `POLL_S` | `1.0` | tunable-new | fux.toml [maintain] daemon_poll_s | daemon loop |
| 105 | `src/fux/maintain/lastcited.py:57` | `MAX_QUESTIONS` | `256` | tunable-new | fux.toml [maintain] last_cited_max | log bound |
| 106 | `src/fux/maintain/runner.py:114` | `STOP_TIMEOUT_S` | `30.0` | tunable-new | fux.toml [maintain] (NEW table) | runner bounds |
| 107 | `src/fux/maintain/runner.py:126` | `MAX_PASSES` | `5` | tunable-new | fux.toml [maintain] (NEW table) | runner bounds |
| 108 | `src/fux/maintain/urlstate.py:92` | `FAILING_STREAK` | `5` | tunable-new | fux.toml [sources.url] failing_streak | when a URL is reported failing |
| 109 | `src/fux/progress.py:38` | `THRESHOLD` | `200` | tunable-new | output.toml [cli] progress_threshold | when a progress bar appears |
| 110 | `src/fux/query/__init__.py:1403` | `ANSWER_TOP` | `3` | tunable-new | output.toml [cli.answer] top | `answer` reads no `top` today |
| 111 | `src/fux/query/headings.py:64` | `MAX_HEADINGS` | `3` | tunable-new | output.toml [cli] max_headings | display count |
| 112 | `src/fux/query/provenance.py:174` | `DEFAULT_JOURNAL_MAX` | `1000` | tunable-new | output.toml [cli.answer] journal_max | L8 journal bound; SR says a design default |
| 113 | `src/fux/query/rerank.py:78` | `DEPTH` | `20` | tunable-new | tune.toml [ranking] rerank_depth / rerank_coverage_power | ranking knobs |
| 114 | `src/fux/query/rerank.py:105` | `COVERAGE_POWER` | `2` | tunable-new | tune.toml [ranking] rerank_depth / rerank_coverage_power | ranking knobs |
| 115 | `src/fux/refer/_assemble.py:75` | `CITATION_OVERHEAD` | `80` | tunable-new | tune.toml [refer] citation_overhead | budget accounting |
| 116 | `src/fux/refer/_chunk.py:87` | `TABLE_ROWS_PER_PASSAGE` | `1` | tunable-new | tune.toml [refer] table_rows_per_passage | passage shape |
| 117 | `src/fux/refer/fetchcache.py:61` | `DEFAULT_TTL_SECONDS` | `300` | tunable-new | fux.toml [refer] fetch_cache_ttl | fetch-cache TTL; ⚠ Policy default 0 disables it — two values |
| 118 | `src/fux/refer/fetchcache.py:66` | `DEFAULT_MAX_BYTES` | `500 * 1024 * 1024` | tunable-new | fux.toml [refer] fetch_cache_max_bytes | cache bound |
| 119 | `src/fux/serve/__init__.py:78` | `DEFAULT_PORT` | `7337` | tunable-new | output.toml [cli.serve] port | serve port |
| 120 | `src/fux/serve/__init__.py:343` | `TRIAGE_ROWS` | `200` | tunable-new | .fux/inspect.toml (NEW file) | inspect sampling/size |
| 121 | `node/src/config/output.mjs:32` | `OUTPUT_NAME` | `".fux/output.toml";` | fixed | constants.toml [files] | an artefact file/dir name |
| 122 | `node/src/config/root.mjs:6` | `CONFIG_NAME` | `"fux.toml";` | fixed | constants.toml [files] | an artefact file/dir name |
| 123 | `node/src/config/tune.mjs:51` | `TUNE_NAME` | `".fux/tune.toml";` | fixed | constants.toml [files] | an artefact file/dir name |
| 124 | `node/src/correct.mjs:19` | `CORRECTIONS_FILE` | `".fux/eval/corrections.tsv";` | fixed | constants.toml [files] | an artefact file/dir name |
| 125 | `node/src/decode/registry.mjs:47` | `PROSE_TYPES` | `["*.md", "*.markdown", "*.txt", "*.rs…` | fixed | constants.toml [decoders.prose] types | Node twin of the prose globs |
| 126 | `node/src/graph/model.mjs:10` | `TAG_PREFIX` | `"tag:";` | fixed | constants.toml | a committed namespace/prefix |
| 127 | `node/src/graph/plane.mjs:16` | `SCHEMA` | `"fux.graph.v1";` | fixed | constants.toml [schema] | a schema id |
| 128 | `node/src/graph/plane.mjs:17` | `GRAPH_NAME` | `"graph.json";` | fixed | constants.toml [files] | an artefact file/dir name |
| 129 | `node/src/graph/walk.mjs:45` | `EXTRACTED_GRADE` | `10;` | fixed | constants.toml [graph] grades | committed in E/ |
| 130 | `node/src/graph/walk.mjs:67` | `EDGE_KINDS` | `["ref", "tag", "code", "supersedes"];` | fixed | constants.toml | committed field/kind vocabulary |
| 131 | `node/src/store/format.mjs:7` | `INDEX_DIR` | `".fux/index";` | fixed | constants.toml [files] | an artefact file/dir name |
| 132 | `node/src/store/format.mjs:8` | `SCHEMA_ID` | `"fux.index.v5";` | fixed | constants.toml [schema] | a schema id |
| 133 | `node/src/store/format.mjs:9` | `ANALYZER_VERSION` | `"v3";` | fixed | constants.toml [versions] | a format/rules version |
| 134 | `node/src/store/format.mjs:13` | `TF_FIELDS` | `["body", "heading", "title", "path", …` | fixed | constants.toml | committed field/kind vocabulary |
| 135 | `node/src/verbs/mcp.mjs:33` | `PROTOCOL_VERSION` | `"2024-11-05";` | fixed | constants.toml [versions] | a format/rules version |
| 136 | `src/fux/config.py:24` | `CONFIG_NAME` | `"fux.toml"` | fixed | constants.toml [files] | an artefact file/dir name |
| 137 | `src/fux/config.py:26` | `FIXED_SHARDS` | `256` | fixed | constants.toml [index] shards | ⚠ fux.toml [index] shards ALSO exists — the record must say which wins |
| 138 | `src/fux/config.py:102` | `FETCHERS_DIR` | `".fux/fetchers"` | fixed | constants.toml [files] | an artefact file/dir name |
| 139 | `src/fux/config.py:108` | `DEFAULT_TYPES_FILE` | `".fux/formats.toml"` | fixed | constants.toml [files] | an artefact file/dir name |
| 140 | `src/fux/config.py:113` | `LEGACY_TYPES_FILE` | `".fux/sources/types"` | fixed | constants.toml [files] | an artefact file/dir name |
| 141 | `src/fux/correct.py:83` | `CORRECTIONS_FILE` | `".fux/eval/corrections.tsv"` | fixed | constants.toml [files] | an artefact file/dir name |
| 142 | `src/fux/decode/__init__.py:75` | `CONSUMER_DIR` | `".fux/decoders"` | fixed | constants.toml [files] | an artefact file/dir name |
| 143 | `src/fux/decode/__init__.py:135` | `BUILTIN_MODULES` | `` | fixed | constants.toml [decoders] builtin | the built-in decoder list |
| 144 | `src/fux/decode/csv.py:38` | `VERSION` | `1` | fixed | constants.toml [decoders.<name>] version | a decoder version, in the decoder digest |
| 145 | `src/fux/decode/csv.py:40` | `EXTENSIONS` | `(".csv", ".tsv")` | fixed | constants.toml [decoders.<name>] extensions | what a built-in decoder claims |
| 146 | `src/fux/decode/docx.py:27` | `VERSION` | `1` | fixed | constants.toml [decoders.<name>] version | a decoder version, in the decoder digest |
| 147 | `src/fux/decode/docx.py:29` | `EXTENSIONS` | `(".docx", ".docm")` | fixed | constants.toml [decoders.<name>] extensions | what a built-in decoder claims |
| 148 | `src/fux/decode/drawio.py:38` | `VERSION` | `1` | fixed | constants.toml [decoders.<name>] version | a decoder version, in the decoder digest |
| 149 | `src/fux/decode/drawio.py:40` | `EXTENSIONS` | `(".drawio", ".dio")` | fixed | constants.toml [decoders.<name>] extensions | what a built-in decoder claims |
| 150 | `src/fux/decode/html.py:32` | `VERSION` | `1` | fixed | constants.toml [decoders.<name>] version | a decoder version, in the decoder digest |
| 151 | `src/fux/decode/html.py:34` | `EXTENSIONS` | `(".html", ".htm", ".xhtml")` | fixed | constants.toml [decoders.<name>] extensions | what a built-in decoder claims |
| 152 | `src/fux/decode/image.py:53` | `VERSION` | `1` | fixed | constants.toml [decoders.<name>] version | a decoder version, in the decoder digest |
| 153 | `src/fux/decode/image.py:55` | `EXTENSIONS` | `(".png", ".jpg", ".jpeg", ".gif")` | fixed | constants.toml [decoders.<name>] extensions | what a built-in decoder claims |
| 154 | `src/fux/decode/ini.py:28` | `VERSION` | `1` | fixed | constants.toml [decoders.<name>] version | a decoder version, in the decoder digest |
| 155 | `src/fux/decode/ini.py:30` | `EXTENSIONS` | `(".ini", ".cfg", ".properties")` | fixed | constants.toml [decoders.<name>] extensions | what a built-in decoder claims |
| 156 | `src/fux/decode/json.py:40` | `VERSION` | `1` | fixed | constants.toml [decoders.<name>] version | a decoder version, in the decoder digest |
| 157 | `src/fux/decode/json.py:42` | `EXTENSIONS` | `(".json",)` | fixed | constants.toml [decoders.<name>] extensions | what a built-in decoder claims |
| 158 | `src/fux/decode/jsonl.py:36` | `VERSION` | `1` | fixed | constants.toml [decoders.<name>] version | a decoder version, in the decoder digest |
| 159 | `src/fux/decode/jsonl.py:38` | `EXTENSIONS` | `(".jsonl",)` | fixed | constants.toml [decoders.<name>] extensions | what a built-in decoder claims |
| 160 | `src/fux/decode/mail.py:50` | `VERSION` | `1` | fixed | constants.toml [decoders.<name>] version | a decoder version, in the decoder digest |
| 161 | `src/fux/decode/mail.py:52` | `EXTENSIONS` | `(".eml", ".mbox")` | fixed | constants.toml [decoders.<name>] extensions | what a built-in decoder claims |
| 162 | `src/fux/decode/pdf.py:66` | `VERSION` | `1` | fixed | constants.toml [decoders.<name>] version | a decoder version, in the decoder digest |
| 163 | `src/fux/decode/pdf.py:68` | `EXTENSIONS` | `(".pdf",)` | fixed | constants.toml [decoders.<name>] extensions | what a built-in decoder claims |
| 164 | `src/fux/decode/pptx.py:33` | `VERSION` | `1` | fixed | constants.toml [decoders.<name>] version | a decoder version, in the decoder digest |
| 165 | `src/fux/decode/pptx.py:35` | `EXTENSIONS` | `(".pptx", ".pptm")` | fixed | constants.toml [decoders.<name>] extensions | what a built-in decoder claims |
| 166 | `src/fux/decode/rtf.py:41` | `VERSION` | `1` | fixed | constants.toml [decoders.<name>] version | a decoder version, in the decoder digest |
| 167 | `src/fux/decode/rtf.py:43` | `EXTENSIONS` | `(".rtf",)` | fixed | constants.toml [decoders.<name>] extensions | what a built-in decoder claims |
| 168 | `src/fux/decode/svg.py:40` | `VERSION` | `1` | fixed | constants.toml [decoders.<name>] version | a decoder version, in the decoder digest |
| 169 | `src/fux/decode/svg.py:42` | `EXTENSIONS` | `(".svg",)` | fixed | constants.toml [decoders.<name>] extensions | what a built-in decoder claims |
| 170 | `src/fux/decode/toml.py:28` | `VERSION` | `1` | fixed | constants.toml [decoders.<name>] version | a decoder version, in the decoder digest |
| 171 | `src/fux/decode/toml.py:30` | `EXTENSIONS` | `(".toml",)` | fixed | constants.toml [decoders.<name>] extensions | what a built-in decoder claims |
| 172 | `src/fux/decode/xlsx.py:33` | `VERSION` | `2` | fixed | constants.toml [decoders.<name>] version | a decoder version, in the decoder digest |
| 173 | `src/fux/decode/xlsx.py:35` | `EXTENSIONS` | `(".xlsx", ".xlsm")` | fixed | constants.toml [decoders.<name>] extensions | what a built-in decoder claims |
| 174 | `src/fux/decode/xml.py:31` | `VERSION` | `1` | fixed | constants.toml [decoders.<name>] version | a decoder version, in the decoder digest |
| 175 | `src/fux/decode/xml.py:33` | `EXTENSIONS` | `(".xml",)` | fixed | constants.toml [decoders.<name>] extensions | what a built-in decoder claims |
| 176 | `src/fux/decode/yaml.py:46` | `VERSION` | `1` | fixed | constants.toml [decoders.<name>] version | a decoder version, in the decoder digest |
| 177 | `src/fux/decode/yaml.py:48` | `EXTENSIONS` | `(".yaml", ".yml")` | fixed | constants.toml [decoders.<name>] extensions | what a built-in decoder claims |
| 178 | `src/fux/derive/format.py:67` | `RUNTIME_DIR` | `"runtime"` | fixed | constants.toml [files] | an artefact file/dir name |
| 179 | `src/fux/derive/format.py:70` | `BLOCK_SIZE` | `128` | fixed | constants.toml [runtime] block_size | runtime segment layout |
| 180 | `src/fux/derive/format.py:104` | `RUNTIME_SCHEMA` | `"fux.runtime.v7"` | fixed | constants.toml [schema] | a schema id |
| 181 | `src/fux/derive/format.py:142` | `DOCS_FIELDS` | `("id", "loc", "title", "flen", "archi…` | fixed | constants.toml | committed field/kind vocabulary |
| 182 | `src/fux/derive/format.py:144` | `DOCS_NAME` | `"docs.jsonl"` | fixed | constants.toml [files] | an artefact file/dir name |
| 183 | `src/fux/derive/format.py:152` | `ANCHORS_DIR` | `"anchors"` | fixed | constants.toml [files] | an artefact file/dir name |
| 184 | `src/fux/derive/format.py:153` | `STATS_NAME` | `"stats.json"` | fixed | constants.toml [files] | an artefact file/dir name |
| 185 | `src/fux/derive/format.py:155` | `MINED_NAME` | `"mined.json"` | fixed | constants.toml [files] | an artefact file/dir name |
| 186 | `src/fux/derive/format.py:156` | `MANIFEST_NAME` | `"manifest.json"` | fixed | constants.toml [files] | an artefact file/dir name |
| 187 | `src/fux/derive/format.py:157` | `STAMP_NAME` | `"stamp.json"` | fixed | constants.toml [files] | an artefact file/dir name |
| 188 | `src/fux/derive/format.py:158` | `POSTINGS_DIR` | `"postings"` | fixed | constants.toml [files] | an artefact file/dir name |
| 189 | `src/fux/derive/format.py:167` | `DETERMINISTIC_FILES` | `(DOCS_NAME, STATS_NAME, MINED_NAME, M…` | fixed | constants.toml [runtime] deterministic | artefact list (holds a bare literal) |
| 190 | `src/fux/doctor.py:28` | `PY_MIN` | `(3, 11)` | fixed | constants.toml [runtime] python_min | L7 |
| 191 | `src/fux/enrich.py:66` | `ENRICH_DIR` | `".fux/enrich"` | fixed | constants.toml [files] | an artefact file/dir name |
| 192 | `src/fux/enrich.py:453` | `URL_SCOPE` | `".fux/sources/urls"` | fixed | constants.toml [files] | an artefact file/dir name |
| 193 | `src/fux/graph/plane.py:35` | `GRAPH_NAME` | `"graph.json"` | fixed | constants.toml [files] | an artefact file/dir name |
| 194 | `src/fux/graph/plane.py:36` | `SCHEMA` | `"fux.graph.v1"` | fixed | constants.toml [schema] | a schema id |
| 195 | `src/fux/graph/walk.py:91` | `EDGE_KINDS` | `("ref", "tag", "code", "supersedes")` | fixed | constants.toml | committed field/kind vocabulary |
| 196 | `src/fux/ingest/decoderdigest.py:56` | `BUILTIN_PREFIX` | `"built-in:"` | fixed | constants.toml | a committed namespace/prefix |
| 197 | `src/fux/ingest/edges.py:64` | `TAG_PREFIX` | `"tag:"` | fixed | constants.toml | a committed namespace/prefix |
| 198 | `src/fux/ingest/edges.py:66` | `EXTRACTED_GRADE` | `10` | fixed | constants.toml [graph] grades | committed in E/ |
| 199 | `src/fux/ingest/edges.py:67` | `AMBIG_GRADE` | `8` | fixed | constants.toml [graph] grades | committed in E/ |
| 200 | `src/fux/ingest/edges.py:68` | `INFERRED_GRADE` | `6` | fixed | constants.toml [graph] grades | committed in E/ |
| 201 | `src/fux/ingest/extract.py:45` | `RULES_VERSION` | `3` | fixed | constants.toml [versions] | a format/rules version |
| 202 | `src/fux/ingest/fuxignore.py:128` | `IGNORE_FILE` | `".fux/.fuxignore"` | fixed | constants.toml [files] | an artefact file/dir name |
| 203 | `src/fux/ingest/ingestlog.py:105` | `INGEST_LOG_FILE` | `"ingest-log.jsonl"` | fixed | constants.toml [files] | an artefact file/dir name |
| 204 | `src/fux/ingest/pii.py:93` | `RULES_NAME` | `"pii.toml"` | fixed | constants.toml [files] | an artefact file/dir name |
| 205 | `src/fux/ingest/pii.py:517` | `COUNTS_NAME` | `"pii-counts.json"` | fixed | constants.toml [files] | an artefact file/dir name |
| 206 | `src/fux/ingest/queue.py:38` | `QUEUE_REL` | `".fux/enrich/queue.tsv"` | fixed | constants.toml [files] | an artefact file/dir name |
| 207 | `src/fux/ingest/queue.py:39` | `PROGRESS_REL` | `".fux/runtime/enrich-progress.tsv"` | fixed | constants.toml [files] | an artefact file/dir name |
| 208 | `src/fux/ingest/refusals.py:71` | `RULES_NAME` | `"refusals.toml"` | fixed | constants.toml [files] | an artefact file/dir name |
| 209 | `src/fux/ingest/register.py:57` | `NAME` | `"REGISTER"` | fixed | constants.toml [files] | an artefact file/dir name |
| 210 | `src/fux/ingest/register.py:61` | `HEADER` | `"` | fixed | constants.toml [register] header | committed REGISTER header |
| 211 | `src/fux/ingest/routes.py:37` | `REGEX_PREFIX` | `"re:"` | fixed | constants.toml | a committed namespace/prefix |
| 212 | `src/fux/ingest/run.py:1003` | `PII_DIGEST_FILE` | `"pii-digest"` | fixed | constants.toml [files] | an artefact file/dir name |
| 213 | `src/fux/ingest/run.py:1010` | `EXTRACT_CONFIG_DIGEST_FILE` | `"extract-config-digest"` | fixed | constants.toml [files] | an artefact file/dir name |
| 214 | `src/fux/ingest/run.py:1015` | `ENRICH_DIGEST_FILE` | `"enrich-digests.json"` | fixed | constants.toml [files] | an artefact file/dir name |
| 215 | `src/fux/ingest/run.py:1021` | `DECODER_DIGEST_FILE` | `"decoder-digests.json"` | fixed | constants.toml [files] | an artefact file/dir name |
| 216 | `src/fux/ingest/run.py:1214` | `STALE_REDACTION_FILE` | `"stale-redaction.json"` | fixed | constants.toml [files] | an artefact file/dir name |
| 217 | `src/fux/inspect/__init__.py:46` | `REPORT_NAME` | `"report.md"` | fixed | constants.toml [files] | an artefact file/dir name |
| 218 | `src/fux/inspect/__init__.py:47` | `JSON_NAME` | `"report.json"` | fixed | constants.toml [files] | an artefact file/dir name |
| 219 | `src/fux/inspect/dictionary.py:61` | `INSPECT_DIR` | `"inspect"` | fixed | constants.toml [files] | an artefact file/dir name |
| 220 | `src/fux/inspect/dictionary.py:62` | `DICTIONARY_NAME` | `"dictionary.json"` | fixed | constants.toml [files] | an artefact file/dir name |
| 221 | `src/fux/inspect/dictionary.py:63` | `SCHEMA` | `"fux.inspect.dictionary.v1"` | fixed | constants.toml [schema] | a schema id |
| 222 | `src/fux/inspect/facts.py:51` | `FACTS_NAME` | `"facts.json"` | fixed | constants.toml [files] | an artefact file/dir name |
| 223 | `src/fux/inspect/facts.py:52` | `SCHEMA` | `"fux.inspect.facts.v1"` | fixed | constants.toml [schema] | a schema id |
| 224 | `src/fux/inspect/facts.py:56` | `DATA_SUFFIXES` | `(".json", ".jsonl", ".csv", ".toml", …` | fixed | constants.toml [inspect] data_suffixes | ⚠ or tunable in inspect.toml — Arpit |
| 225 | `src/fux/inspect/probes.py:49` | `PROBES_NAME` | `"probes.json"` | fixed | constants.toml [files] | an artefact file/dir name |
| 226 | `src/fux/inspect/probes.py:50` | `SCHEMA` | `"fux.inspect.probes.v1"` | fixed | constants.toml [schema] | a schema id |
| 227 | `src/fux/maintain/daemon.py:96` | `PID_NAME` | `"daemon.pid"` | fixed | constants.toml [files] | an artefact file/dir name |
| 228 | `src/fux/maintain/daemon.py:97` | `STOP_NAME` | `"daemon.stop"` | fixed | constants.toml [files] | an artefact file/dir name |
| 229 | `src/fux/maintain/daemon.py:98` | `STATUS_NAME` | `"daemon.status"` | fixed | constants.toml [files] | an artefact file/dir name |
| 230 | `src/fux/maintain/dirty.py:33` | `DIRTY_NAME` | `"dirty"` | fixed | constants.toml [files] | an artefact file/dir name |
| 231 | `src/fux/maintain/hooks.py:77` | `MERGE_DRIVER_NAME` | `"fux-index"` | fixed | constants.toml [hooks] | written into .git — identifies fux's hooks |
| 232 | `src/fux/maintain/hooks.py:81` | `MARKER` | `"` | fixed | constants.toml [hooks] | written into .git — identifies fux's hooks |
| 233 | `src/fux/maintain/lastcited.py:52` | `LOG_NAME` | `"last-cited.json"` | fixed | constants.toml [files] | an artefact file/dir name |
| 234 | `src/fux/maintain/runner.py:106` | `LOCK_NAME` | `"write.lock"` | fixed | constants.toml [files] | an artefact file/dir name |
| 235 | `src/fux/maintain/runner.py:107` | `STOP_NAME` | `"runner.stop"` | fixed | constants.toml [files] | an artefact file/dir name |
| 236 | `src/fux/maintain/runner.py:108` | `STATUS_NAME` | `"runner.status"` | fixed | constants.toml [files] | an artefact file/dir name |
| 237 | `src/fux/maintain/runner.py:477` | `HANDOFF_ENV` | `"FUX_RUNNER_HANDOFF"` | fixed | constants.toml [env] | env var names |
| 238 | `src/fux/maintain/runner.py:493` | `NO_SPAWN_ENV` | `"FUX_NO_SPAWN"` | fixed | constants.toml [env] | env var names |
| 239 | `src/fux/maintain/urlstate.py:67` | `STATE_NAME` | `"url-state.json"` | fixed | constants.toml [files] | an artefact file/dir name |
| 240 | `src/fux/maintain/urlstate.py:70` | `SCHEMA_NAME` | `"state.schema.json"` | fixed | constants.toml [files] | an artefact file/dir name |
| 241 | `src/fux/mcp.py:32` | `PROTOCOL_VERSION` | `"2024-11-05"` | fixed | constants.toml [versions] | a format/rules version |
| 242 | `src/fux/observe.py:73` | `CONSUMER_DIR` | `".fux/observers"` | fixed | constants.toml [files] | an artefact file/dir name |
| 243 | `src/fux/observe.py:79` | `LIVENESS_NAME` | `"observers.json"` | fixed | constants.toml [files] | an artefact file/dir name |
| 244 | `src/fux/output_config.py:120` | `OUTPUT_NAME` | `".fux/output.toml"` | fixed | constants.toml [files] | an artefact file/dir name |
| 245 | `src/fux/query/__init__.py:526` | `OUTPUT_SCHEMA` | `"output.schema.json"` | fixed | constants.toml [files] | an artefact file/dir name |
| 246 | `src/fux/query/provenance.py:156` | `STATEMENT_TYPE` | `"https://in-toto.io/Statement/v1"` | fixed | constants.toml [receipt] | receipt format |
| 247 | `src/fux/query/provenance.py:161` | `PREDICATE_TYPE` | `"https://fux.dev/receipt/v1"` | fixed | constants.toml [receipt] | receipt format |
| 248 | `src/fux/query/provenance.py:167` | `LEGACY_SCHEMA` | `"fux.receipt.v1"` | fixed | constants.toml [schema] | a schema id |
| 249 | `src/fux/query/provenance.py:169` | `JOURNAL_NAME` | `"provenance.jsonl"` | fixed | constants.toml [files] | an artefact file/dir name |
| 250 | `src/fux/query/provenance.py:765` | `DIGEST_ALG` | `"blake2b-160"` | fixed | constants.toml [receipt] | receipt format |
| 251 | `src/fux/refer/fetchcache.py:57` | `CACHE_DIR` | `"fetch-cache"` | fixed | constants.toml [files] | an artefact file/dir name |
| 252 | `src/fux/serve/__init__.py:74` | `HOST` | `"127.0.0.1"` | fixed | constants.toml [serve] host | localhost-only is a law-level choice, not a knob |
| 253 | `src/fux/store/acquired.py:58` | `DIR_NAME` | `"acquired"` | fixed | constants.toml [files] | an artefact file/dir name |
| 254 | `src/fux/store/acquired.py:62` | `MANIFEST_NAME` | `"manifest.json"` | fixed | constants.toml [files] | an artefact file/dir name |
| 255 | `src/fux/store/acquired.py:64` | `OBJECTS_DIR` | `"objects"` | fixed | constants.toml [files] | an artefact file/dir name |
| 256 | `src/fux/store/acquired.py:67` | `SCHEMA` | `"fux.acquired.v1"` | fixed | constants.toml [schema] | a schema id |
| 257 | `src/fux/store/format.py:12` | `INDEX_DIR` | `".fux/index"` | fixed | constants.toml [files] | an artefact file/dir name |
| 258 | `src/fux/store/format.py:42` | `SCHEMA_ID` | `"fux.index.v5"` | fixed | constants.toml [schema] | a schema id |
| 259 | `src/fux/store/format.py:59` | `ANALYZER_VERSION` | `"v3"` | fixed | constants.toml [versions] | a format/rules version |
| 260 | `src/fux/store/format.py:76` | `TF_FIELDS` | `("body", "heading", "title", "path", …` | fixed | constants.toml | committed field/kind vocabulary |
| 261 | `src/fux/store/fuxdir.py:32` | `FUX_DIR` | `".fux"` | fixed | constants.toml [files] | an artefact file/dir name |
| 262 | `src/fux/store/fuxdir.py:64` | `GENERATED_FILES` | `("README.md", ".gitignore")` | fixed | constants.toml [bundle]/[fuxdir] | artefact names |
| 263 | `src/fux/store/fuxdir.py:94` | `CACHEDIR_SIGNATURE` | `"Signature: 8a477f597d28d172789f06886…` | fixed | constants.toml [fuxdir] cachedir_signature | a spec'd byte string |
| 264 | `src/fux/store/fuxdir.py:441` | `NODE_DIR` | `"node"` | fixed | constants.toml [bundle]/[fuxdir] | artefact names |
| 265 | `src/fux/store/fuxdir.py:442` | `NODE_ENTRY` | `"fux.mjs"` | fixed | constants.toml [bundle]/[fuxdir] | artefact names |
| 266 | `src/fux/store/fuxdir.py:443` | `NODE_SHIM` | `"fux"` | fixed | constants.toml [bundle]/[fuxdir] | artefact names |
| 267 | `src/fux/store/nodebundle.py:65` | `ENTRY` | `"fux.mjs"` | fixed | constants.toml [bundle]/[fuxdir] | artefact names |
| 268 | `src/fux/store/nodebundle.py:72` | `SIDECARS` | `("package.json", "mcp-tools.json", "R…` | fixed | constants.toml [bundle]/[fuxdir] | artefact names |
| 269 | `src/fux/store/recordschema.py:66` | `SCHEMA_NAME` | `"index-record.schema.json"` | fixed | constants.toml [files] | an artefact file/dir name |
| 270 | `src/fux/tune.py:93` | `TUNE_NAME` | `".fux/tune.toml"` | fixed | constants.toml [files] | an artefact file/dir name |
| 271 | `node/src/config/output.mjs:34` | `MAX_REPORTED` | `10;` | not-a-value? | — | how many config errors print at once — about the config itself |
| 272 | `node/src/config/tune.mjs:54` | `MAX_REPORTED` | `10;` | not-a-value? | — | how many config errors print at once — about the config itself |
| 273 | `node/src/query/confidence.mjs:16` | `GROUNDED` | `"grounded";` | not-a-value? | — | an enum tag / wire vocabulary — an identifier, like a key name |
| 274 | `node/src/query/confidence.mjs:17` | `WEAK` | `"weak";` | not-a-value? | — | an enum tag / wire vocabulary — an identifier, like a key name |
| 275 | `node/src/query/confidence.mjs:18` | `PARTIAL` | `"partial";` | not-a-value? | — | an enum tag / wire vocabulary — an identifier, like a key name |
| 276 | `node/src/query/confidence.mjs:19` | `NONE` | `"none";` | not-a-value? | — | an enum tag / wire vocabulary — an identifier, like a key name |
| 277 | `node/src/refer/freshness.mjs:12` | `CURRENT` | `"current";` | not-a-value? | — | an enum tag / wire vocabulary — an identifier, like a key name |
| 278 | `node/src/refer/freshness.mjs:13` | `STALE` | `"stale";` | not-a-value? | — | an enum tag / wire vocabulary — an identifier, like a key name |
| 279 | `node/src/refer/freshness.mjs:14` | `CACHED` | `"cached";` | not-a-value? | — | an enum tag / wire vocabulary — an identifier, like a key name |
| 280 | `node/src/refer/freshness.mjs:15` | `AS_INGESTED` | `"as-ingested";` | not-a-value? | — | an enum tag / wire vocabulary — an identifier, like a key name |
| 281 | `node/src/refer/freshness.mjs:16` | `UNVERIFIED` | `"unverified";` | not-a-value? | — | an enum tag / wire vocabulary — an identifier, like a key name |
| 282 | `node/src/refer/source.mjs:30` | `GIT` | `"git";` | not-a-value? | — | an enum tag / wire vocabulary — an identifier, like a key name |
| 283 | `node/src/refer/source.mjs:31` | `URL` | `"url";` | not-a-value? | — | an enum tag / wire vocabulary — an identifier, like a key name |
| 284 | `src/fux/config.py:119` | `KNOWN_AGENTS` | `("claude", "codex", "copilot", "kiro")` | not-a-value? | — | the closed agent set; fux.toml [agents] install selects from it |
| 285 | `src/fux/decode/__init__.py:93` | `PROSE_DECODER` | `"prose"` | not-a-value? | — | an enum tag / wire vocabulary — an identifier, like a key name |
| 286 | `src/fux/ingest/fuxignore.py:133` | `BLOCK_NOT_INDEXED` | `"not indexed"` | not-a-value? | — | an enum tag / wire vocabulary — an identifier, like a key name |
| 287 | `src/fux/ingest/fuxignore.py:134` | `BLOCK_SKIPPED` | `"skipped"` | not-a-value? | — | an enum tag / wire vocabulary — an identifier, like a key name |
| 288 | `src/fux/ingest/fuxignore.py:135` | `BLOCKS` | `(BLOCK_NOT_INDEXED, BLOCK_SKIPPED)` | not-a-value? | — | an enum tag / wire vocabulary — an identifier, like a key name |
| 289 | `src/fux/ingest/gitdir.py:99` | `POLICY` | `"policy"` | not-a-value? | — | an enum tag / wire vocabulary — an identifier, like a key name |
| 290 | `src/fux/ingest/gitdir.py:100` | `UNREADABLE` | `"unreadable"` | not-a-value? | — | an enum tag / wire vocabulary — an identifier, like a key name |
| 291 | `src/fux/ingest/gitdir.py:114` | `UNFETCHED` | `"unfetched"` | not-a-value? | — | an enum tag / wire vocabulary — an identifier, like a key name |
| 292 | `src/fux/ingest/ingestlog.py:111` | `PROSE` | `"prose"` | not-a-value? | — | an enum tag / wire vocabulary — an identifier, like a key name |
| 293 | `src/fux/ingest/ingestlog.py:116` | `UNKNOWN` | `"unknown"` | not-a-value? | — | an enum tag / wire vocabulary — an identifier, like a key name |
| 294 | `src/fux/ingest/refusals.py:408` | `MAGIC_FLOOR` | `"magic-floor"` | not-a-value? | — | an enum tag / wire vocabulary — an identifier, like a key name |
| 295 | `src/fux/ingest/register.py:66` | `UNKNOWN` | `"-"` | not-a-value? | — | an enum tag / wire vocabulary — an identifier, like a key name |
| 296 | `src/fux/ingest/skipnotice.py:84` | `LEGACY_NOTICE` | `"skipped"` | not-a-value? | — | an enum tag / wire vocabulary — an identifier, like a key name |
| 297 | `src/fux/ingest/sourcelist.py:344` | `PROSE_DECODER` | `"prose"` | not-a-value? | — | an enum tag / wire vocabulary — an identifier, like a key name |
| 298 | `src/fux/inspect/__init__.py:402` | `_number()` | `digits:int=3` | not-a-value? | — | display rounding digits — text formatting? |
| 299 | `src/fux/inspect/xray.py:40` | `FINDINGS` | `` | not-a-value? | — | an enum tag / wire vocabulary — an identifier, like a key name |
| 300 | `src/fux/query/confidence.py:108` | `GROUNDED` | `"grounded"` | not-a-value? | — | an enum tag / wire vocabulary — an identifier, like a key name |
| 301 | `src/fux/query/confidence.py:113` | `PARTIAL` | `"partial"` | not-a-value? | — | an enum tag / wire vocabulary — an identifier, like a key name |
| 302 | `src/fux/query/confidence.py:118` | `WEAK` | `"weak"` | not-a-value? | — | an enum tag / wire vocabulary — an identifier, like a key name |
| 303 | `src/fux/query/confidence.py:121` | `NONE` | `"none"` | not-a-value? | — | an enum tag / wire vocabulary — an identifier, like a key name |
| 304 | `src/fux/query/confidence.py:124` | `BANDS` | `(GROUNDED, PARTIAL, WEAK, NONE)` | not-a-value? | — | an enum tag / wire vocabulary — an identifier, like a key name |
| 305 | `src/fux/query/provenance.py:177` | `REPRODUCED` | `"reproduced"` | not-a-value? | — | an enum tag / wire vocabulary — an identifier, like a key name |
| 306 | `src/fux/query/provenance.py:178` | `DRIFTED_CORPUS` | `"drifted:corpus"` | not-a-value? | — | an enum tag / wire vocabulary — an identifier, like a key name |
| 307 | `src/fux/query/provenance.py:179` | `DRIFTED_CONFIG` | `"drifted:config"` | not-a-value? | — | an enum tag / wire vocabulary — an identifier, like a key name |
| 308 | `src/fux/query/provenance.py:180` | `UNVERIFIABLE` | `"unverifiable"` | not-a-value? | — | an enum tag / wire vocabulary — an identifier, like a key name |
| 309 | `src/fux/query/provenance.py:182` | `VERDICTS` | `(REPRODUCED, DRIFTED_CORPUS, DRIFTED_…` | not-a-value? | — | an enum tag / wire vocabulary — an identifier, like a key name |
| 310 | `src/fux/refer/freshness.py:76` | `NEVER` | `"never"` | not-a-value? | — | an enum tag / wire vocabulary — an identifier, like a key name |
| 311 | `src/fux/refer/freshness.py:79` | `ALWAYS` | `"always"` | not-a-value? | — | an enum tag / wire vocabulary — an identifier, like a key name |
| 312 | `src/fux/refer/freshness.py:81` | `MODES` | `(NEVER, ALWAYS)` | not-a-value? | — | an enum tag / wire vocabulary — an identifier, like a key name |
| 313 | `src/fux/refer/source.py:58` | `GIT` | `"git"` | not-a-value? | — | an enum tag / wire vocabulary — an identifier, like a key name |
| 314 | `src/fux/refer/source.py:59` | `URL` | `"url"` | not-a-value? | — | an enum tag / wire vocabulary — an identifier, like a key name |
| 315 | `src/fux/store/fuxdir.py:449` | `SHAPE_VENDORED` | `"A"` | not-a-value? | — | an enum tag / wire vocabulary — an identifier, like a key name |
| 316 | `src/fux/store/fuxdir.py:450` | `SHAPE_WORKSPACE` | `"C"` | not-a-value? | — | an enum tag / wire vocabulary — an identifier, like a key name |
| 317 | `node/src/config/output.mjs:35` | `ROOTS` | `["cli", "mcp"];` | not-a-value | — | names of config keys |
| 318 | `node/src/config/output.mjs:100` | `MCP_KEYS` | `["top"];` | not-a-value | — | names of config keys |
| 319 | `node/src/config/output.mjs:104` | `SHARED_CLI_KEYS` | `(() => {` | not-a-value | — | names of config keys |
| 320 | `node/src/config/tune.mjs:65` | `INDEX_TABLE` | `"index";` | not-a-value | — | names of config keys |
| 321 | `node/src/hash/blake2b.mjs:194` | `HEX` | `[];` | not-a-value | — | byte identity / computed lookup table |
| 322 | `node/src/query/rerank.mjs:62` | `MIN_TERMS` | `2;` | not-a-value | — | arithmetic identity: proximity needs two terms |
| 323 | `node/src/query/stem.mjs:64` | `STEP2` | `[` | not-a-value | — | the stemmer's rules — parsing logic, like a regex |
| 324 | `node/src/query/stem.mjs:73` | `STEP3` | `[` | not-a-value | — | the stemmer's rules — parsing logic, like a regex |
| 325 | `node/src/query/stem.mjs:78` | `STEP4` | `[` | not-a-value | — | the stemmer's rules — parsing logic, like a regex |
| 326 | `node/src/store/reader.mjs:15` | `NL` | `0x0a;` | not-a-value | — | byte identity / computed lookup table |
| 327 | `node/src/verbs/ask.mjs:33` | `ARCHIVED_MARKER` | `"[archived]";` | not-a-value | — | user-facing text |
| 328 | `node/src/verbs/ask.mjs:40` | `PINNED_MARKER` | `"[pinned]";` | not-a-value | — | user-facing text |
| 329 | `node/src/verbs/ask.mjs:41` | `SECTION_MARKER` | `"§";` | not-a-value | — | user-facing text |
| 330 | `node/src/verbs/ask.mjs:46` | `RELATED_HEADING` | `"related (linked from the answers, no…` | not-a-value | — | user-facing text |
| 331 | `node/src/verbs/ask.mjs:49` | `RELATED_MARKER` | `"<-";` | not-a-value | — | user-facing text |
| 332 | `node/src/verbs/find.mjs:134` | `NO_MATCHES` | `"No confident matches.";` | not-a-value | — | user-facing text |
| 333 | `src/fux/config.py:36` | `KNOWN_KEYS` | `` | not-a-value | — | names of config keys |
| 334 | `src/fux/config.py:62` | `OPAQUE_TABLES` | `("sources.url.config",)` | not-a-value | — | names of config keys |
| 335 | `src/fux/config.py:68` | `REFUSED_KEYS` | `` | not-a-value | — | names of config keys |
| 336 | `src/fux/correct.py:86` | `CORRECTIONS_KEY` | `"corrections"` | not-a-value | — | names of config keys |
| 337 | `src/fux/correct.py:91` | `HUMAN_MODEL` | `"none (human correction)"` | not-a-value | — | user-facing text |
| 338 | `src/fux/correct.py:92` | `HUMAN_SKILL` | `"fux-correct@1"` | not-a-value | — | user-facing text |
| 339 | `src/fux/doctor.py:2149` | `RETIRED_REFUSAL_STARTERS` | `()` | not-a-value | — | empty collection |
| 340 | `src/fux/doctor.py:2566` | `FLOOR_OFF_NOTE` | `` | not-a-value | — | user-facing text |
| 341 | `src/fux/enrich.py:75` | `REQUIRED_KEYS` | `("source", "source_sha", "chunks", "m…` | not-a-value | — | names of config keys |
| 342 | `src/fux/errors.py:18` | `__init__()` | `exit_code:int=1` | not-a-value | — | exit code 1 is an identity, not a setting |
| 343 | `src/fux/ingest/typesfile.py:79` | `KEYS` | `("include", "decoders", "meta")` | not-a-value | — | names of config keys |
| 344 | `src/fux/ingest/typesfile.py:86` | `META_TARGETS` | `("body", "heading", "title", "path", …` | not-a-value | — | names of config keys |
| 345 | `src/fux/maintain/hooks.py:75` | `REFS_NOTE` | `"refs/fux/<tree> — see the module not…` | not-a-value | — | user-facing text |
| 346 | `src/fux/output_config.py:219` | `MCP_KEYS` | `("top",)` | not-a-value | — | names of config keys |
| 347 | `src/fux/progress.py:184` | `update()` | `n:int=1` | not-a-value | — | increment of 1 is arithmetic identity |
| 348 | `src/fux/progress.py:203` | `update()` | `n:int=1` | not-a-value | — | increment of 1 is arithmetic identity |
| 349 | `src/fux/query/__init__.py:709` | `ARCHIVED_MARKER` | `"[archived]"` | not-a-value | — | user-facing text |
| 350 | `src/fux/query/__init__.py:714` | `SECTION_MARKER` | `"§"` | not-a-value | — | user-facing text |
| 351 | `src/fux/query/__init__.py:722` | `PINNED_MARKER` | `"[pinned]"` | not-a-value | — | user-facing text |
| 352 | `src/fux/query/__init__.py:728` | `RELATED_HEADING` | `"related (linked from the answers, no…` | not-a-value | — | user-facing text |
| 353 | `src/fux/query/__init__.py:733` | `RELATED_MARKER` | `"<-"` | not-a-value | — | user-facing text |
| 354 | `src/fux/query/__init__.py:845` | `NO_MATCHES` | `"No confident matches."` | not-a-value | — | user-facing text |
| 355 | `src/fux/serve/__init__.py:371` | `update()` | `n:int=1` | not-a-value | — | increment of 1 is arithmetic identity |
| 356 | `src/fux/store/fuxdir.py:91` | `DECLARED` | `(*COMMITTED, *COMMITTED_FILES, *DERIV…` | not-a-value | — | derived: a tuple of other names |
| 357 | `src/fux/store/fuxdir.py:95` | `CACHEDIR_TAG` | `` | not-a-value | — | user-facing text |
| 358 | `src/fux/store/fuxdir.py:308` | `ask()` | `` | not-a-value | — | grep false positive: a line of generated source inside a string |
| 359 | `src/fux/tune.py:132` | `INDEX_TABLE` | `"index"` | not-a-value | — | names of config keys |
