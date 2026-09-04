---
type: Proposal
title: "Better results from `ask`, `find` and `answer` — per verb, and the embeddings question settled"
description: "Research note + proposal. Where each verb loses today (measured), what would fix it inside L1–L4, and why 'embeddings via a chat skill' is not a thing — the chat skill already exists and it is doc2query."
status: proposed
timestamp: 2026-09-04T00:00:00Z
---

# Better results from `ask`, `find` and `answer`

**Filed 2026-09-04 · Cowork (Opus).** Research note, not a build item. Every
claim about fux is grounded in a filed run or in code; every claim about the
field carries its paper. Nothing here moves a default — three of the calls
below are already on the *Blocked on Arpit* list and are named as such.

## 0 · The one-screen answer

| verb | where it loses today (measured) | the fix that stays inside the laws | cost |
|---|---|---|---|
| **all three** | the proximity reranker measured **+4 fixed / 0 broken** and ships at `rerank_weight = 0.0` | turn it on (Arpit's call — W-94's sibling) | one default |
| **all three** | 18 of 18 surviving golden failures are **vocabulary gaps** — the searcher's word is not in the document | **agent-side query expansion** (Query2doc), fed to fux as extra terms; fux stays model-free | small CLI/MCP surface |
| **all three** | enrichment measured **+1 / −1 blind**, because it was prose "context"; two blind authors broke the same two queries | re-aim the `fux-enrich` skill at **doc2query** (questions, not context) and add a deterministic **self-retrieval filter** (doc2query−−) | skill text + one check |
| **`ask`** | the agent cannot tell a decisive #1 from a coin-flip — **4.38 % of top-5 orderings are ties broken by document index** | break ties on a declared signal, and say when a tie happened | small |
| **`ask`** (MCP) | `fux_search` already returns `band` / `missing` unconditionally, but the tool description tells the agent to *report* a gap, never to *retry* — so the agent never reformulates | one sentence in the description: on `partial`, re-search with the `missing` term replaced by the document's likely word (or §3's `--expand`) | tool description |
| **`find`** | pure ranked list; no way to require a phrase or scope a directory | `--phrase` (adjacency post-filter, local text) and `--under <dir>` | small |
| **`answer`** | **refers exactly one document** (`run_query(…, 1)`) — if BM25F picks the wrong doc, the answer cannot recover. `recall@1 = 0.60` vs `recall@5 = 0.95` on the 43 graded queries | refer the **top-3** and let passage rescoring choose across them; `refer()` already takes a list | small, deterministic |
| **`answer`** | passage rescoring is bag-of-words; the tightest passage does not win | add `rerank.passage_boost` to `_rescore` | small |
| **`answer`** | **0 of 20 unanswerable queries declined**; `doc_coverage` reports and does not gate | gate abstention on `answer` only (Arpit's call, already filed) | one default |
| **embeddings** | the dense lane died at **0 fixed / 2 broken** because the bundled model mean-pooled static vectors — as order-blind as BM25F | **no.** A chat model cannot emit vectors; a real encoder breaks L1 and cross-machine determinism; an API breaks L4. The *text* a chat skill can produce is doc2query, which is `fux enrich` | — |

**Ordering by value per unit of risk:** reranker default → `answer` refers top-3
→ agent-side expansion → doc2query re-aim of enrich → `find` filters → ties →
abstention gate. The first two are code fux already has, switched off or
under-used.

## 1 · Where the verbs actually lose — the evidence, not the vibe

- **Vocabulary gaps dominate.** Of the 18 golden failures that survived
  reranking, **18 are vocabulary gaps and 0 are ordering failures** — a
  mechanical term-membership check, not a judgement
  ([2026-08-24-rerank-and-goldens](../regression/2026-08-24-rerank-and-goldens/ANALYSIS.md) §5).
- **Negation is unrepresentable.** *"current"* vs *"no longer current"* pool
  to the same bag; every fix converges on reading word order, which L1 and
  cross-ISA determinism refuse
  ([dense-lane-gate](../regression/2026-08-24-dense-lane-gate/ANALYSIS.md) §3).
- **Enrichment as built is worth ~zero blind.** +1 and −1 from two blind
  authors, breaking the same two queries; +9 only when the author had seen the
  queries ([second-author](../regression/2026-08-24-blind-enrichment-second-author/ANALYSIS.md)).
- **The reranker is the one intervention that helped and broke nothing** —
  and it ships off (`tune.py` `rerank_weight: float = 0.0`).
- **`answer`'s ceiling is `recall@1`.** `0.5969` at k=1 against `0.9535` at
  k=5, because 19 of 43 graded queries have 2–3 relevant documents
  ([first-recall](../regression/2026-08-28-first-recall/ANALYSIS.md)). `answer`
  fetches only `results[0]` (`query/__init__.py::cmd_answer`, `top=1`), so it
  inherits the k=1 number by construction.
- **Nobody declines.** 0/20 on the unanswerable suite, both arms, every tier
  ([v1-vs-head](../regression/2026-08-28-benchmark-v1-vs-head/ANALYSIS.md) Finding 3).
- **4.38 % of top-5 orderings are decided by `docidx`**, i.e. by nothing
  ([rank-flip](../regression/2026-08-25-rank-flip-susceptibility/ANALYSIS.md) §2).

⚠ Every number above is from a 10-document playground or a generated corpus,
and most runs are `informed`. **None is a claim at 10 000 documents**, and a
blind golden set at the design point still does not exist (W-87 / W-96). That
gap bounds everything below.

## 2 · The embeddings question, settled

**"Create embeddings using some chat skill" cannot be done, and the reason is
not fux's laws — it is what a chat model is.**

- A chat model emits **text**. It has no vector output. Anthropic's own
  documentation: *"Anthropic does not offer its own embedding model"* and points
  to Voyage AI ([Claude docs](https://platform.claude.com/docs/en/build-with-claude/embeddings)).
  A skill can make Claude *write*; it cannot make Claude *embed*.
- The three ways to get vectors, each against a law:

| route | what it needs | law it hits |
|---|---|---|
| bundle a static model (what shipped) | 7.9 MB table, mean-pool | measured **0 fixed / 2 broken** — order-blind ([DENSE-CHUNK](../regression/2026-08-24-dense-lane-gate/VERDICT.md)) |
| bundle a contextual encoder | transformer layers at query time, `onnxruntime` or numpy | **L1**; float reduction order differs per ISA, so two clones disagree ([rank-flip](../regression/2026-08-25-rank-flip-susceptibility/ANALYSIS.md) §1 — the drift is real, its *ranking* effect unmeasured for a reranker) |
| call an embeddings API (Voyage, OpenAI) | network + key at ingest **and** at query | **L4**, `$0`, and L3 if it touches ingest |

- **What a chat skill *can* produce is already the strongest known text-side
  substitute for dense retrieval on BM25:** *document expansion by generated
  queries*. doc2query lifted BM25 on MS MARCO from **MRR@10 0.184 → 0.218**,
  docTTTTTquery to **0.265** with 10 generated queries per passage
  ([Nogueira & Lin 2019](https://cs.uwaterloo.ca/~jimmylin/publications/Nogueira_Lin_2019_docTTTTTquery-v2.pdf)).
  That is what `fux enrich` is — except the skill currently asks for
  *context prose*, not *questions*. §4 below.

**Verdict: no dense lane, no bundled model, no API — and no loss, because the
capability a chat skill actually has (writing) is the one the literature says
pays on a lexical index.**

### 2.1 · Addendum (2026-09-04, later) — the agent can *run* an embedder, and that is a different question

Arpit's clarification: the "chat" is Claude Code / Kiro, which can execute
tools. So the honest restatement is: **a skill cannot make the model emit
vectors, but it can make the agent run a program that does.** That is
ADR-FETCHER's pattern a third time —
network lives in consumer code, model calls live in a skill, and an embedder
would live in **consumer code the skill invokes**. Sketch, so it can be
judged rather than guessed at:

| piece | where | law |
|---|---|---|
| `.fux/embedders/<name>.{py,js}` — consumer-owned, written by `fux setup` like the fetchers; wraps whatever the host has (`sentence-transformers`, or **`@huggingface/transformers` under Node with no Python**) | consumer code | L1 held — fux imports nothing |
| `.fux/vectors/<sha>.jsonl` — per-chunk `int8` vectors, **pinned and committed** like `.fux/enrich/`; `fux ingest` folds them in deterministically | committed | L3 held — same pinned files → same bytes; **L2/L5 ⚠** — embedding inversion was already recorded as a *demonstrated* risk on hashed records and traded rather than closed (CHANGELOG 0.34.0, P5), so hashed-meta sources get no vectors by default |
| the **query** vector — fux cannot compute it. The agent runs the same embedder and passes it in: `fux ask --qvec <file>` / an MCP input | caller | L4 held — fux stays offline |
| fusion — **rank-space RRF**, never score addition (the deleted `fuse()` was score-space; RRF is what survives scale mismatch) | fux, stdlib | — |

**Three things that decide whether it is worth building, in order:**

1. **The bar is already written.** DENSE-CHUNK's `>= 3 fixed / 0 broken` on
   the frozen goldens. The FAIL it recorded was for a *static mean-pooled*
   model; a contextual encoder (bge-small, e5-small, nomic) has **never been
   measured here**, and `q015` (*"current"* vs *"no longer current"*) is the
   litmus — it is the one query a contextual model should rescue and a
   bag-of-vectors cannot. **Run the gate before writing the plane.** A
   scratch script that embeds the playground with one such model and
   re-grades the 50 goldens is an afternoon and answers the question that
   matters.
2. **Cross-machine determinism moves from fux to the host.** Pinned document
   vectors are fixed; the *query* vector is computed on each machine, and an
   ONNX/`transformers.js` run differs per ISA in low bits. The rank-flip
   run's finding applies: nothing reorders below the corpus's adjacent-gap
   floor (~5e-5 on 495 docs) and RRF's rank-space fusion is more tolerant
   still — but *"clone it and run the query"* becomes *"…with the same
   embedder version"*, and the receipt has to record the embedder's name and
   version to stay verifiable (`fux verify` would need `--qvec` too).
3. **`$0` stays true of fux and stops being true of the host.** The
   embedder is a download (30–130 MB), behind an enterprise proxy, on a
   Windows fleet — the deployment filter CLAUDE.md says did not get cheaper.
   Opt-in per source line (`embed=true`), exactly as `enrich=true`, so a
   corpus that declares nothing pays nothing.

**Recommendation:** measure first (item 1), then decide. If a contextual
model clears the bar on the goldens, this is a compare doc — the fork is
*pinned vectors + caller-supplied query vector* vs *doc2query text only*
(§4) — and doc2query is the arm that costs nothing and needs no gate to
ship. If it does not clear the bar, the question is closed with evidence
instead of a law.

## 3 · Cross-verb: agent-side query expansion (the biggest lever that stays inside the laws)

**The idea.** The searcher's word is not in the document (18/18 failures). A
model can guess the document's words from the question. Fux does not call a
model — but **the caller is a model**, on every path that matters (`fux mcp`,
the `fux-usage` skill, Claude Code). Let the agent expand, and let fux rank the
expansion deterministically.

**The literature.**

- **Query2doc** (Wang et al., EMNLP 2023): prompt the LLM for a short
  pseudo-passage, append it to the query, run BM25. **+3 % to +15 %** on
  MS MARCO / TREC DL, no fine-tuning
  ([arXiv 2303.07678](https://arxiv.org/abs/2303.07678)).
- **Query Expansion by Prompting LLMs** (Jagerman et al., 2023): chain-of-thought
  prompts are the best expansion prompt for BM25, and LLM expansion beats
  classical pseudo-relevance feedback
  ([arXiv 2305.03653](https://arxiv.org/abs/2305.03653)).
- **RM3 / PRF, the model-free alternative:** deterministic and stdlib-able,
  but it is known to *hurt* on short-passage corpora like MS MARCO while
  helping on long-document newswire — it should be measured, never assumed
  ([Anserini MS MARCO regressions](https://github.com/castorini/anserini/blob/master/docs/experiments-msmarco-passage.md)).

**The surface — three options, smallest first.**

1. **Nothing in fux.** The `fux-usage` skill and the `fux_search` tool
   description tell the agent: *when `band` is `partial`, re-ask with the
   `missing` terms replaced by the words the document would use.* Zero code.
   Weak, because the expansion overwhelms the original query — Query2doc
   repeats the original query 5× to keep it dominant, which an agent will not do.
2. **`fux ask "<question>" --expand "<pseudo passage>"`** — one extra
   positional/flag. The expansion's terms are analyzed with the same analyzer
   and scored at a **fixed lower weight** (Query2doc's 1:5 ratio, made a
   `[ranking] expand_weight` tune key). Deterministic: same strings in, same
   bytes out. The receipt records the expansion verbatim, so `fux verify` can
   replay it and L8 is untouched.
3. **Multi-query RRF** — `fux ask -q a -q b -q c`, fused with reciprocal rank
   fusion (`k = 60`, [Cormack et al. 2009](https://dl.acm.org/doi/10.1145/1571941.1572114)).
   The agent sends three phrasings in one call. RRF is rank-based, so it is
   immune to the scale mismatch that killed additive fusion. ⚠ `query/fuse.py`
   was this math and Arpit had it removed on 2026-08-26 for having no caller
   (W-79); ADR-PORT-LIST rule 1 says reviving it needs a **new record**, and
   this time it would have one — a lexical multi-query caller, not a dense lane.

**Recommend 2, then 3.** Both keep the boundary ADR-ENRICH drew: the model is
outside, fux validates and ranks what came back, and `--why` can show which
hits came from the expansion and which from the question.

**What it does not fix:** negation. An expansion adds words; it cannot subtract
*"current"* from a superseded record. That stays with `supersedes:` +
`superseded_weight` (W-94).

## 4 · Cross-verb: re-aim `fux enrich` at doc2query, with a deterministic filter

**The measured defect is in the *text*, not the mechanism.** The skill asks
for 60–120 words of context prose. Two blind authors produced +1 and −1. Both
broke `q015`/`q021` by writing honest currency vocabulary into a superseded
record.

**Three changes to the skill, none to L3.**

1. **Generate questions, not prose.** doc2query's unit is *"a question this
   passage answers"*, 5–10 per document, one per line. That is what a searcher
   types, so the vocabulary lands where BM25F needs it; it is also cheap to
   read in a diff. The `body` stays prose-free.
2. **Filter by self-retrieval — doc2query−−.** Gospodinov, MacAvaney & Macdonald
   (ECIR 2023) found that dropping generated queries a relevance model scores
   low **improves BM25 by up to 16 % and cuts the index by 33 %**, because
   seq2seq models hallucinate ([arXiv 2301.03266](https://arxiv.org/abs/2301.03266)).
   Fux has a deterministic relevance model already: **its own index.**
   `fux enrich --check` can run each generated question through `rank()` and
   refuse any that does not place its own document in the top-*k* — offline,
   stdlib, byte-deterministic, and it catches the invented question before it
   becomes committed vocabulary.
3. **Currency goes in frontmatter, never prose.** The skill must write
   `supersedes:` / *is superseded by* as a declared key, not as a sentence — the
   sentence is what broke `q015`. This is
   [second-author](../regression/2026-08-24-blind-enrichment-second-author/ANALYSIS.md)
   §3 option 1, which was called the honest one and never built.

**Gate before any of it ships:** the same three arms (`none` / `placebo` /
`real`) already built in `2026-08-28-placebo-and-seal`, re-graded on `recall@k`,
blind author, net ≥ 6 discordant per ADR-RS decision 19.

## 5 · `ask` — ranked documents for an agent

`ask`'s job is to hand an agent a list it can act on. Two things make the
list less actionable than it looks.

- **Ties are silent.** 4.38 % of top-5 orderings are decided by `docidx`. Break
  them on a **declared** signal — the same `Weighting` inputs, in a stated
  order: `superseded` first, then recency, then path priority, then id — and
  emit `tie: true` on the affected results. Deterministic on every machine; it
  turns *the same arbitrary answer everywhere* into *a stated answer everywhere*.
- **The agent never reformulates.** `fux_search` (MCP) already returns the
  confidence block unconditionally (ADR-CONFIDENCE decision 11), and its
  description tells the agent to *name* the missing terms — it never says
  *search again*. Add the retry rule to the description and to `fux-usage`:
  `partial` + `missing` ⇒ re-ask with the missing term replaced, or use §3's
  `--expand`. This is the cheapest retrieval loop there is, and it is the one
  RankGPT-style listwise LLM reranking already proves an LLM does well over a
  BM25 top-*k* ([Sun et al. 2023](https://arxiv.org/pdf/2309.15088);
  [RankZephyr](https://arxiv.org/html/2312.02724v1)) — except here the LLM is
  the caller, so it costs fux nothing.
- **Reranker on.** The +4/0 result is *informed* and below the resolution
  floor, so it is not proof — but it is the only intervention on record that
  broke nothing, and off-by-default means nobody measures it. Arpit's call.
- **Not recommended:** a per-passage lexical index for `ask`. Analysed already
  — it changes the committed format and still cannot see negation
  ([dense-lane-gate](../regression/2026-08-24-dense-lane-gate/ANALYSIS.md) §3
  option A). The reranker's `boost()` already scores documents by their best
  passage, which is the part that mattered.

## 6 · `find` — locations for a pipe

`find` exists to be piped, so *precision controls* beat *ranking cleverness*.

- **`--phrase "…"`** — keep only documents where the query's bigrams occur
  adjacent, using `rerank._adjacency_signal` on local text (declines `url:`
  docs offline, exactly as the reranker does). Deterministic post-filter; never
  retrieves.
- **`--under <dir>`** — scope to a source-list prefix. Trivial and missing.
- **`--all`** (conjunctive) — every query term must be present in the
  document's `terms`. BM25F is disjunctive; a grep user expects AND.
- **Reranker on** applies here too, at the same depth.
- **Not recommended:** fuzzy/prefix matching. The committed plane stores term
  *hashes*, so the index cannot enumerate terms sharing a prefix without a
  second committed structure. An unfixable-by-design gap; say it in the
  `missing` field rather than pretend.

## 7 · `answer` — the single passage, and the verb that claims

`answer` is where fux says *this is it*, so it carries the highest cost of
being wrong and has the most measured headroom.

1. **Refer the top-3, not the top-1.** `cmd_answer` calls `run_query(…, 1)`
   and hands `results[0]` to `refer()`. `refer()` accepts a list of citations
   and `_rescore` computes passage-level `df` across everything fetched — the
   machinery for a fair cross-document passage contest exists and is called
   with one document. Fetch `min(3, results)` within the existing byte budget
   (`per_doc_fraction` already bounds each). Expected effect is bounded by the
   `recall@1 → recall@3` gap, ~0.60 → ~0.9 on the graded set. Deterministic,
   offline for `file:` docs, and the receipt already lists every citation.
2. **Proximity in the passage rescore.** `_rescore.rescore` is bag-of-words
   BM25 over passages. Multiply by `rerank.passage_boost` (same analyzer, same
   chunker) so the passage that says the question back wins over the one
   that scatters its words.
3. **Abstain on `answer` only.** 0/20 declines. Gate on `doc_coverage` and
   `band == none/partial-by-missing-term`: emit `answer: null` with the block
   that already says why. `ask` and `find` keep reporting, never gating — a
   list is not a claim. Filed as Arpit's decision on 2026-08-28; this note
   only adds *which verb*.
4. **Sentence-level extraction stays out.** The agent is the answerer over MCP
   (ADR-MCP), and `answer`'s passages are its input. TextRank-style extraction
   over one passage adds a second scorer with nothing to measure it against.

## 8 · What this note does NOT recommend

- A cross-encoder, `onnxruntime`, numpy, or any model in the runtime path.
  ADR-RERANK veto 1 condition 2 stands; the rank-flip run only says the
  *quantity* it is stated in is the wrong one.
- Any change to the committed index shape. Everything above is query-time,
  tune-file, skill text, or a validator.
- Shipping any of it on the 10-document playground. The gate is a blind
  golden set at 10 000 documents (W-87 / W-96), per-query rows, net ≥ 6.

## 9 · Graduation trigger

Any one of: Arpit rules on `rerank_weight`; a blind golden set exists at the
design point; or `answer`'s top-3 refer is picked up as a W-item. The
per-verb sections then graduate separately — §7.1 needs no fork and goes
straight to a plan entry; §3 and §4 are forks and get compare docs.

## References

- [Query2doc: Query Expansion with Large Language Models](https://arxiv.org/abs/2303.07678) — Wang, Yang, Wei, EMNLP 2023
- [Query Expansion by Prompting Large Language Models](https://arxiv.org/abs/2305.03653) — Jagerman et al., 2023
- [Doc2Query−−: When Less is More](https://arxiv.org/abs/2301.03266) — Gospodinov, MacAvaney, Macdonald, ECIR 2023
- [From doc2query to docTTTTTquery](https://cs.uwaterloo.ca/~jimmylin/publications/Nogueira_Lin_2019_docTTTTTquery-v2.pdf) — Nogueira & Lin, 2019
- [Anserini MS MARCO passage regressions](https://github.com/castorini/anserini/blob/master/docs/experiments-msmarco-passage.md) — BM25 baselines
- [RankZephyr / listwise LLM reranking](https://arxiv.org/html/2312.02724v1); [RankGPT](https://arxiv.org/pdf/2309.15088)
- [Reciprocal rank fusion](https://dl.acm.org/doi/10.1145/1571941.1572114) — Cormack, Clarke, Buettcher, SIGIR 2009
- [Claude docs — Embeddings](https://platform.claude.com/docs/en/build-with-claude/embeddings) — *"Anthropic does not offer its own embedding model"*
- In-repo: [rerank-and-goldens](../regression/2026-08-24-rerank-and-goldens/ANALYSIS.md) · [blind second author](../regression/2026-08-24-blind-enrichment-second-author/ANALYSIS.md) · [DENSE-CHUNK](../regression/2026-08-24-dense-lane-gate/VERDICT.md) · [first-recall](../regression/2026-08-28-first-recall/ANALYSIS.md) · [v1-vs-head](../regression/2026-08-28-benchmark-v1-vs-head/ANALYSIS.md) · [rank-flip](../regression/2026-08-25-rank-flip-susceptibility/ANALYSIS.md) · `src/fux/query/__init__.py` · `src/fux/query/rerank.py` · `src/fux/refer/_rescore.py` · `src/fux/tune.py`
