# Fux — code + architecture review (2026-08-28)

*Reviewed on a cloud mirror of `src/fux`, 16 ADRs, CLAUDE.md, OPEN-WORK, CI — `device_bash` was wedged, so no git, no test run. Every P0/P1 below was re-read in the source by me; the two "reproduced" items were reproduced by a reviewer on a synthetic corpus, not on the device. Treat as findings to verify with `pytest -q tests tests_e2e` on the real tree, not as landed facts. Model: Fable 5 + 4 parallel review agents.*

## Verdict

- The architecture (index-and-refer, committed wire index + derived runtime, differential law, candidates-not-scores accelerator) is sound and unusually well-argued. Nothing here says "rebuild again."
- The risk has moved from *design* to *drift*: several records describe behaviour the code does not have (the W-83 class), and the differential law has one verified hole.
- Biggest lever is not ranking — it is the agent-facing surface (MCP robustness, passage bounds, config strictness) and per-session doc cost.

## A. Defects — fix first (agent lane)

| # | Sev | Claim | Where | Fix |
|---|---|---|---|---|
| 1 | P0 | `--fast` ≠ `--scan` when `recency_half_life_days > 0`. `_kth_score` gets the caller's `Weighting` (`newest_mtime=0`), only `rank()` sets it → theta over-estimates → docs pruned. Reviewer repro: 251/2700 divergences, 0 with recency off. | `derive/accel.py:274, 358-380`; `query/rank.py:272-273` | Set `newest_mtime` on the weighting once in `accel_candidates` before the loop; add a recency arm to the differential sweep. ADR-ACCELERATOR veto condition. |
| 2 | P0 | Any non-`FuxError` in an MCP tool call kills the server (`k="abc"`, `path=123`, PermissionError). | `mcp.py:326-333, 369-384` | `except Exception` → `isError` result; wrap loop body. Add a malformed-arg test. |
| 3 | P0 | `output.toml` "sole source of truth" makes every release that adds an output key hard-fail every existing repo — including `fux mcp` before `initialize`. | `output_config.py:52-67`; `mcp.py:368` | Unset key → `BUILT_IN` + one stderr note / `doctor` row; keep hard error for *unknown* keys. (ADR-OUTPUT decision 20 — Arpit's call, but the MCP start-up death is a defect.) |
| 4 | P1 | `fux answer` / MCP `k=1` can never be `weak`: list truncated to 1 before `_fill_confidence`, so `separation=1.0` always. | `query/__init__.py:682, 188-228`; `confidence.py:424-427` | Compute separation from the pre-truncation window's top-2. ADR-CONFIDENCE. |
| 5 | P1 | Graph verbs trust a stale `graph.json`; `plane.load()` checks schema only. ADR-GRAPH says it refuses stale. | `graph/plane.py:78-100` | Call `accel.is_fresh(root)` in `load()`, same "run `fux build`" error. Record drift → fix code or record. |
| 6 | P1 | `fux mcp` re-reads the whole index per call; ADR-MCP claims a warm server with resident mmaps. | `mcp.py:175, 262`; `accel.py:454` | Cache `read_index`/`Runtime` in `serve()` keyed on stamp mtime. Fix ADR-MCP §1 diagram too. |
| 7 | P1 | `fux_passage` unbounded and unscoped: whole file, any path in repo (`.env`, runtime journals). | `mcp.py:238-253` | Require path ∈ index; default 200-line window; `max_bytes` + `truncated: true`. |
| 8 | P1 | Committed symlink to a file outside the repo is indexed as `src=git, meta=plain` — title/terms of `~/.ssh/config` into a committed shard. | `ingest/gitdir.py:425-433` | Skip `is_symlink()` (POLICY reason) or require resolved target under root. L2/L5. |
| 9 | P1 | Hooks installed where git never runs them: worktrees (git uses the common dir's hooks) and any `core.hooksPath` repo (husky/lefthook). `status` still says "fux". | `maintain/hooks.py:139-151` | `git rev-parse --git-path hooks`; refuse otherwise. |
| 10 | P1 | `mtime` prior depends on clone depth / git presence / `%ct` (rewritten by rebase, squash). Failure → `{}` silently → same sources, different committed bytes. Non-ASCII paths never match (quotepath). | `ingest/priors.py:47-62` | `%at`, `-z -c core.quotepath=false`, detect shallow, refuse-not-silent on failure. L3. |
| 11 | P1 | Detached runner indexes the working tree (unstaged edits ship in the next commit) and rewrites shards mid-rebase. | `maintain/runner.py:516-534` → `ingest/run.py:163` | Read from `HEAD` (`ls-tree -z` + `cat-file --batch`); skip on `rebase-merge`/`MERGE_HEAD`/`index.lock`. ADR-HOOKS. |
| 12 | P1 | `DisplayCache.put` is O(n) reads per put → URL-heavy ingest O(n²). | `store/displaycache.py:86-110` | One `index.json` (sha→seq,size) or a seq counter file. |
| 13 | P1 | Decoder registry rebuilt + consumer decoders re-`exec`'d per file, 3× per file. | `decode/__init__.py:211-249, 277, 302` | Build once per `run()`, thread through. |
| 14 | P1 | Analyzer is ASCII-only: `Straße café 日本語` → `stra e caf`. Enterprise litmus fails. | `query/analyzer.py:41` | NFKC + `\w+` + `casefold()`; Porter only on `isascii()`. Header pin invalidates. |
| 15 | P2 | Windows CRLF into committed/executed files (`.fuxignore`, `queue.tsv`, hook scripts → `#!/bin/sh\r`). | `fuxignore.py:461`, `queue.py:122`, `hooks.py:170,206` | `newline="\n"`; a test that greps `write_text(` without it. |
| 16 | P2 | Security nits: DOCTYPE scan only first 8 KB; PDF inflate cap per stream not per doc (+O(n²) sum); `cdp.py` uses default Chrome profile (SSO cookies reach committed hashes) and hijacks an existing tab. | `_xml.py:37-48`; `pdfdoc.py:73-101`; `cdp.py.txt:326-412` | Whole-buffer DOCTYPE search; doc-level inflate budget; `--user-data-dir=<tmp>`, `PUT /json/new`, `wait()`. |
| 17 | P2 | Runtime state files RMW with no lock/atomic rename (`dirty`, `urlstate`, `lastcited`, daemon pid). `lastcited` evicts lexicographically-smallest, not oldest. | `dirty.py:83-108`, `lastcited.py:150-153`, `daemon.py:358` | Reuse `writer._atomic_write`; take `write_lock` in `record_head`. |
| 18 | P2 | MCP: `ping` → `-32601` (spec: empty result); `protocolVersion` hard-coded; negative `k` returns `scored[:-1]`; `confidence` can be `null` on the surface whose description says "read the confidence block". | `mcp.py:32, 169, 215, 338` | Handle ping; echo supported version; schema `minimum: 1`; emit `{"band":"unknown"}` not null. |
| 19 | P2 | Merge: empty shard deleted → modify/delete conflict bypasses the driver; driver registered `--local` so fresh clones text-merge shards silently. | `store/writer.py:94-96`; `hooks.py:179-191` | Never delete a shard (header-only); `doctor` fails when `.gitattributes` names an unregistered driver. |
| 20 | P2 | Refer plane sorts on raw float; `rank()`/`rerank()` sort on `round(…,9)`. Cross-arch tie flips. | `_rescore.py:110`; `_assemble.py:126-181` | Same `(-round(s,9), sha, locator)` key. |

## B. Architecture / structure

- **Split the god-modules, no behaviour change.** `query/__init__.py` (1151 lines, 5 concerns) → `pipeline.py` / `render.py` / `verbs.py`; `ingest/run.py` 380-line `run()` → `walk → reconcile_urls → extract → resolve → stamp_priors → write` with one dataclass between steps; `sources.py` list-editing → `ingest/sourcelist.py`. Only the ownership table changes.
- **Dead surface.** `refer/arc.py` is never constructed (140 lines, O(n²) if it were); `rank()` still accepts legacy `archived_weight/archived_dirs` beside `weighting`; `stem.py:224` unreachable branch; `_build.py` docstring describes the old df counting. Delete or wire.
- **Compute freshness once.** `is_fresh` (256 `stat()`s) runs twice per `ask` (`run_query` + `_declare_no_accelerator`) and in every verb. Return it from `run_query`.
- **Accelerator at scale.** `Runtime.docs` `json.loads` every doc row per query; `_kth_score` rescore is O(T·|hits|). Fixed-width offset table for `docs.jsonl` (same `struct` trick as `.idx`) + running partial scores. Matters >10k docs; describe, don't measure yet.
- **Ingest at scale.** Whole corpus bytes in RAM, every shard parsed, every doc edge-scanned even when reusable, `rglob` descends `node_modules/` before `.fuxignore` speaks. Stream the walk, prune on ancestor verdict, key edge *scan* results on sha.
- **`routes()` is exponential in `--hops`** with `limit` applied after enumeration and no CLI clamp. Best-first on `-log(reliability)`, stop at `limit`; clamp hops ≤ 4.
- **Chunker has no fence state** — `# comment` inside a code block becomes a heading and a passage title. Track ``` / ~~~ toggles.
- **`--why` under-reports the multiplier** (only `archived_weight`; superseded/recency/priority hidden). Provenance says "×1.0" when the doc was scaled ×0.42.
- **Config surface.** 3 files, ~30 knobs, 6-level precedence for 7 output keys, a by-name `_REFUSED` catalogue. The *boundary* (indexed / ranked / printed) is right; collapse `[cli]`/`[cli.json]`/`[cli.<verb>]`/`[cli.json.<verb>]` to `[cli]` + `[cli.<verb>]`, `json` as a key.
- **CLI startup.** `fux --version` ≈ 60 ms vs 13 ms interpreter; `output_config` (dataclasses→inspect, tomllib) imported at parser build. Move `BUILT_IN` to a constants module. ADR-CLI decision 7 says this already.

## C. Retrieval quality — stdlib-only, in cost order

1. **Every ranking prior HEAD added ships as a no-op** (`superseded_weight=1.0`, `recency=0`, `rerank_weight=0.0`) — on priors, HEAD *is* 1.0.0. OPEN-WORK already knows; the missing piece is `fux doctor` saying "this corpus declares `supersedes:` and the prior is off." Disclosure, not a ranking change.
2. **Per-field length normalisation.** Current BM25F normalises on one weighted doc length; a title hit is penalised by body length. Real BM25F is per-field `b_f`, `avg_flen_f` — the data (`flen`, `total_flen`) is already committed. Block bound stays valid. Gate on a blind run.
3. **Unicode analyzer** (A.14) — it's a quality item as much as a bug.
4. **Heading-ancestry tokens into `ctx` at ingest** (H1>H2 path as terms). Structure-preserving chunking beat fine-grained semantic splitting in the 2026 36-strategy study (nDCG@5 0.459 vs <0.244 fixed-char); Chroma found ~200-token no-overlap best. Your chunker is close; measure the size knob.
5. **Deterministic RM3 pseudo-relevance feedback** over the committed `terms` of the top-k (fixed k, t). Offline, byte-deterministic, one `Scoring` field. The only query-side signal you don't have.
6. **Reranker: enable after a *blind* re-measure only.** C2 showed 94 fixed / 0 broken on a headroom suite and +4/0 on hand-graded text — both `informed`. Also `rerank.py:728` only reranks `file:` docs, never `url:` — that's a gap regardless of the default.
7. **Cite BM25S** for the eager-impact idea (your 4-bit impacts are that) — grounding for the paper, free.
8. **Don't build:** dense lane (correctly deleted), RRF (one lane), learned-sparse at query time. Inference-free learned sparse (arXiv 2411.04403, doc-side only, 1.1× BM25 latency) is the one model-assisted thing that fits — as an `enrich` output emitting term weights, never in `ingest`.

## D. Agent-facing surface (where adoption is decided)

- Agents are steered to the CLI; `USAGE-SKILL.md` never mentions `fux mcp`. One paragraph: "if an MCP server named `fux` is present, `fux_search` → `fux_passage` first." `fux setup` should emit a `.mcp.json` snippet.
- Adopt Anthropic's tool-writing guidance: `response_format: concise|detailed` enum, a 25k-token cap, pagination, descriptions "as to a new hire." Sourcegraph Deep Search and Claude Code's Explore both return *compact citations, not content* — Fux's shape already matches; say so in the description.
- Proof-of-possession (Augment): `fux_passage` requires the caller to present the file sha. Cheap, and it closes the passage-leak (A.7) in a way that reads as a feature.
- Evidence on the "grep vs index" fight cuts both ways: Amazon (Feb 2026) — agentic keyword search ≈ 90 % of RAG with zero staleness; Copilot shipped semantic search for "2 % less time, no quality change"; Milvus — grep burns 40 % more tokens at scale. Fux's wedge is exactly the middle: deterministic index, zero staleness (fresh sha), token-cheap. Lead with the token number, not the ms number.
- MCP spec 2026-07-28 moved to a stateless core (`initialize` optional, version in `_meta`, `server/discover` probe, `ttlMs` on list results). Your newline framing is correct; add `ping`, echo version, plan for `server/discover`.
- Distribution stack that costs nothing: `uvx fux`, `server.json` in the MCP Registry, a Claude Code plugin (`.claude-plugin/plugin.json` + `skills/` + `.mcp.json`), Cursor deeplink. AGENTS.md is now a Linux Foundation standard (60k repos) — you already write it.

## E. Tests, CI, process weight

- **CI:** no `ruff check`, no type check, no coverage, installs `uv` it never uses, `cache: pip` is a no-op without a requirements file. 8 OS×Python jobs each run both suites. One lint job + coverage on Linux/3.12 only. ci.yml says "fux gate" is a required check; CLAUDE.md says none — one is stale.
- **Missing test classes:** differential arm with recency on (A.1); `answer` vs `ask --top 5` confidence agreement (A.4); `plane.load` staleness (A.5); malformed MCP args (A.2); cross-arch refer-plane sort (A.20); `write_text(` without `newline` grep-test (A.15); hypothesis round-trip for `frontmatter` and "specimen loads every key" for `tune`/`output` (dev-only dep, runtime stays $0); an "imported-but-never-called" gate — `test_orphaned_modules` misses `ARC` because it is imported.
- **Doc weight per session:** CLAUDE.md ≈ 12.8k tokens; the 16 ADRs staged ≈ 112k; `adr/README.md` 37 KB; WORKLOG 700 KB; `setup.py` is 65 % prose, much of it dated incident narrative. Mandated reading order ≈ 35–40k tokens before the first edit, every session. Without touching Law zero: (a) each ADR = normative §Decision ≤ ~6 KB (test-enforced) + append-only §History that the freshness gate still counts as "touched"; (b) CLAUDE.md → ≤ 8 KB binding core + `docs/PROCESS.md`; (c) code comments cite `W-nn`/decision numbers, never re-tell the incident.
- **Record drift found (W-83 class, CI green):** ADR-GRAPH (stale refusal), ADR-MCP (warm server, diagram), ADR-CLI decision 7 (import cost), ADR-OUTPUT "not reached by the regression". Four in one read — the "re-read the records you touched" obligation is not holding on its own; that is the second strike your own two-strikes rule names.

## F. Sequencing

- **Agent lane, this week:** A.1, A.2, A.4, A.5, A.6, A.7, A.8, A.13, A.15, A.18 — all mechanical, all with a test, each names its ADR.
- **Arpit lane:** A.3 (output.toml strictness — your decision 20), A.9/A.11 (hooks read HEAD — ADR-HOOKS reopen), A.14 (analyzer bump = index invalidation), C.1 disclosure, doc-tiering shape (E), MCP-first steering for agents (D).
- **Measure before flipping:** C.2 per-field norm, C.6 reranker default — both blind, both on the contested suite plus the 50 goldens.

## G. What is good (keep it)

- One scorer, one sort; the accelerator returns candidates not scores; rounding-aware skip test. The differential law is a property of the set, not a spot-check.
- Per-field unweighted block extrema recombined at query time — weights tunable without rebuild, monotonicity argument stated and correct.
- Canonical write boundary refuses floats/nulls/non-NFC/U+2028; writer byte-compares so an unchanged corpus leaves `git status` clean.
- `_zip` caps from the central directory; merge driver refuses on same-ver/different-bytes; `O_CREAT|O_EXCL` lock; `is_alive` avoids the Windows `kill(pid,0)` trap.
- Four-state freshness vocabulary (`current/stale/unverified/cached`) that refuses to collapse "did not look" into "fine"; `isError` vs JSON-RPC error split is right; retired-config-key errors name the new home.

## Sources (research)

- Claude Code no-index rationale — https://vadim.blog/claude-code-no-indexing/
- Amazon, agentic keyword search ≈ RAG — https://arxiv.org/abs/2602.23368
- Milvus, grep token cost — https://milvus.io/blog/why-im-against-claude-codes-grep-only-retrieval-it-just-burns-too-many-tokens.md
- Copilot semantic search A/B — https://github.blog/changelog/2026-03-17-copilot-coding-agent-works-faster-with-semantic-code-search/
- Augment proof-of-possession — https://www.augmentcode.com/blog/a-real-time-index-for-your-codebase-secure-personal-scalable
- Sourcegraph Deep Search subagents — https://sourcegraph.com/changelog/deep-search-subagents
- Cursor Merkle indexing — https://read.engineerscodex.com/p/how-cursor-indexes-codebases-fast
- BM25S — https://arxiv.org/abs/2407.03618
- Inference-free learned sparse — https://arxiv.org/abs/2411.04403
- Chunking, 36 strategies — https://arxiv.org/html/2603.06976 · Chroma — https://www.trychroma.com/research/evaluating-chunking
- CodeRAG-Bench — https://aclanthology.org/2025.findings-naacl.176.pdf · SWE-Explore — https://arxiv.org/html/2606.07297v1
- Anthropic, writing tools for agents — https://www.anthropic.com/engineering/writing-tools-for-agents
- MCP 2026-07-28 — https://blog.modelcontextprotocol.io/posts/2026-07-28/ · stdio — https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/stdio
- IR significance testing — https://arxiv.org/html/2501.03930v1
- AGENTS.md → Linux Foundation — https://openai.com/index/agentic-ai-foundation/
