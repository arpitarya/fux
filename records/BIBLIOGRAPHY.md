---
type: Bibliography
title: "BIBLIOGRAPHY — every paper that built fux, and what it holds up"
description: "One row per external paper, standard or piece of prior art this repo cites, grouped by the part of the engine it touches. Each row says what it is in a line or two and then the only thing that matters: what DEPENDS on it, or what was NOT BUILT because of it. Derived from the References section of every record, compare doc, proposal, environment note and the paper itself."
status: accepted
timestamp: 2026-09-13T00:00:00Z
---

# BIBLIOGRAPHY — the reading that became the engine

**What this file is.** Every external source the repo cites, in one place,
with the one fact a reader wants: **did it become code, or did it stop code
from being written?** A paper that only reassured somebody is noted as such —
convergent design is not evidence, and this file says so where it applies.

**What this file is not.** It is not a reading list and it is not the
authority. The authority for any decision is the record that made it; this
file points at that record and never re-argues it. Where a record and this
file disagree, **the record wins and this file is the defect.**

## The legend — the fourth column, and only these five words

| marker | means |
|---|---|
| **BUILT** | code exists today that implements or is parameterised by this source |
| **NOT BUILT** | the source is the reason something specific was *not* written, or was written and deleted |
| **REFUSED** | a live proposal was declined against it, and the refusal is recorded with a reopen-trigger |
| **PARKED** | read, filed, nothing decided — it sits in `proposals/` behind a graduation trigger |
| **METHOD** | it governs how this repo measures, blinds, pre-registers or writes, not what the engine does |

> ⚠ **A source is listed once, under the part of the engine it decides.**
> Several are cited by three or four records; the row names the one that owns
> the decision, and the rest are found by following it.

---

## 1 · Ranking and scoring

| source | what it is | what depends on it — or what it stopped |
|---|---|---|
| Robertson & Zaragoza, *The Probabilistic Relevance Framework: BM25 and Beyond* (2009) | The scoring model itself, and §3's `k1` term-frequency saturation. | **BUILT** — every score fux prints. [SR-ASK](0103_ask.md), [SR-RANKING](0111_ranking.md). Its `k1` saturation is also the third failure class planted deliberately in the `fux-playground` corpus. |
| Robertson, Zaragoza & Taylor, *Simple BM25 Extension to Multiple Weighted Fields* (CIKM 2004) | The original BM25**F** formulation — fields weighted before, not after, saturation. | **BUILT** — the field weights (`title`, `heading`, `body`) and the single `avg_wlen`. [SR-RANKING](0111_ranking.md). |
| Zobel & Moffat, *Inverted Files for Text Search Engines* (ACM CSUR 38(2), 2006) | The survey. §5 prices positional postings; elsewhere it contrasts doc-major and term-major organisation. | **BUILT** — term-major postings ([SR-POSTINGS](0112_postings.md)). **NOT BUILT** — positional postings: [SR-ASK](0103_ask.md) decision 8 declines the cost this paper quantifies, which is *why* proximity had to be solved later by reranking over passages instead. |
| Ding & Suel, *Faster Top-k Document Retrieval Using Block-Max Indexes* (SIGIR 2011) | Block-max upper bounds, and the definition of **safe** pruning — same top-k, less work. | **BUILT** — `derive/accel.py`. [SR-ACCELERATOR](0110_accelerator.md), and the word *safe* in [SR-TUNE](0135_tuning.md). |
| Broder, Carmel, Herscovici, Soffer & Zien, *Efficient query evaluation using a two-level retrieval process* (CIKM 2003) | WAND. The upper-bound invariant a skip must never violate. | **BUILT** — the accelerator's bound check, and the reason a tuning knob may not break it. [SR-TUNE](0135_tuning.md). |
| Craswell, Robertson, Zaragoza & Taylor, *Relevance weighting for query independent evidence* (SIGIR 2005) | The saturating transform for query-independent features (recency, authority, priors). | **NOT BUILT — deferred by name.** [SR-TUNE](0135_tuning.md) records it as the correct shape for a future prior and ships the multiplicative form instead. |
| LUCENE-6819, *Deprecate index-time boosts* | Lucene's own removal of boosts baked into stored values. | **NOT BUILT** — a ranking preference may never be fused into a committed value. It is why boosts live in `.fux/tune.toml` and nowhere in the index. [SR-TUNE](0135_tuning.md). |
| Cormack, Clarke & Büttcher, *Reciprocal Rank Fusion outperforms Condorcet and individual Rank Learning Methods* (SIGIR 2009) | RRF, and the constant `k = 60`. Fuse **ranks**, never scores on unrelated scales. | **BUILT** — `query/fuse.py`, and it is **`-q` multi-query fusion ONLY**. ⚠ **This row said "and the fusion inside `--expand`" until 2026-09-14. That was wrong** and is corrected here: `--expand` does no fusion at all — it is a weighted term multiplier inside a *single* `rank()` call (`query/expand.py`), and the two mechanisms never meet. [SR-EXPAND](0149_expand.md). `k = 60` is the paper's, untuned, and deliberately not a `tune.toml` key. Because RRF sums small reciprocals, a fused answer reports the confidence band of the **first** query's own ranking and flags `fused: true`. |
| arXiv 2605.18561 — identifier-aware tokenization for BM25 on code | Splitting identifiers is the single largest lift available to BM25; the best BM25 *variant* adds ~0.2 % on top of it. | **BUILT** — `query/analyzer.py` emits whole **and** parts (`getUserName` → `getusername`, `get`, `user`, `name`). It is also the argument for **not** chasing BM25 variants. |
| Porter, *An algorithm for suffix stripping* (1980), with the Snowball `voc.txt`/`output.txt` vectors | The stemmer, and a published conformance vocabulary. | **BUILT** — `query/stem.py`, stdlib-only, and pinned term-for-term against the published vectors in the Node port's differential arm. |

### 1b · The ten parked ranking ideas — one paper each

*All ten sit behind **W-156** in [`../work/proposals/search-improvements-v3.md`](../work/proposals/search-improvements-v3.md)
(filed 2026-09-13, Arpit: *"keep all ten of them"*). Each is its own ranking
change with its own golden questions and its own pre-registration — so each
paper below is **PARKED**, and the number in brackets is the idea it grounds.*

| source | what it is | status |
|---|---|---|
| Craswell, Hawking & Robertson, *Effective site finding using link anchor information* (SIGIR 2001) | Index the words other documents use when **linking** to a document. | **PARKED [1]** — the anchor-text field. Also the reason hubs must be **damped** in the accepted graph-expanded `ask` ([`../work/compare/ask-graph-expansion.compare.md`](../work/compare/ask-graph-expansion.compare.md)), so it is the one paper here with a foot in a shipped decision. |
| Lavrenko & Croft, *Relevance-based language models* (SIGIR 2001); Abdul-Jaleel et al., *UMass at TREC 2004* (RM3) | Pseudo-relevance feedback: pull distinctive terms from the top-k and re-query once. | **PARKED [4]** — an auto-filled `--expand`. ⚠ Filed with its own warning: *drift is real; pre-register or don't build.* |
| Metzler & Croft, *A Markov random field model for term dependencies* (SIGIR 2005) | The sequential dependence model — score ordered and unordered term windows. | **PARKED [6]** — phrase sense (*"index lock"* vs *"lock the index"*) **without a positional index**, scored in refer on the fetched bytes. This is the cheap answer to the cost Zobel & Moffat priced and SR-ASK declined. |
| Carbonell & Goldstein, *The Use of MMR, Diversity-Based Reranking* (SIGIR 1998) | Maximal marginal relevance — trade a little relevance for coverage. | **PARKED [7]** — swap the 5th hit when the top-5 share one graph community. ⚠ *Measure — it can hurt precision.* |
| Jardine & van Rijsbergen, *The use of hierarchic clustering in information retrieval* (1971) | The cluster hypothesis: closely associated documents tend to be relevant to the same request. | **PARKED [7]** — the justification for diversifying by community at all, and cited again by the abstention work as the basis for graph coherence. |
| Kamps et al., element / section retrieval at **INEX** | Rank sections, back off to the document. | **PARKED [10]** — the largest of the ten: a plane change, and a major release of its own. |
| Apache Lucene, `WordDelimiterGraphFilter` — `PRESERVE_ORIGINAL`, `CATENATE_ALL`, `SPLIT_ON_NUMERICS` | Split on intra-word delimiters and **re-emit the undelimited original alongside the parts** (`wi-fi-4000` → `wi`, `fi`, `4000`, `wifi4000`). | **PARKED [3]** — the cheapest of the four families in [`../work/proposals/identifier-exact-match.md`](../work/proposals/identifier-exact-match.md), and the one fux already half-implements: `query/analyzer.py` emits whole-and-parts for `snake_case` and `camelCase` only, because `_WORD_RE`'s class holds `_` and not `-`. |
| Apache Lucene, `KeywordRepeatFilter` (with `RemoveDuplicatesTokenFilter`) | Emit every token twice, once marked keyword, so a keyword-respecting stemmer indexes **the stemmed and the unstemmed form into the same field**. | **PARKED [3]** — the fix for the three MANGLED ids (`KFS` → `kf`). ⚠ **`should_stem` in `query/stem.py` is already fux's `KeywordMarkerFilter`** — it protects digits and underscores and not acronyms — so this is an under-specification, not an absence. |
| Elastic, *Mixing exact search with stemming* — multi-fields and `quote_field_suffix` | One analyzed field plus an un-analyzed `.exact` subfield, with quoted queries routed to the exact one. | **PARKED [3]** — this **is** W-168 step 2 as written, and the only family that can *weight* an exact hit above a stemmed one. Also the only one needing committed postings, hence a [SR-INDEX-LIFECYCLE](0108_index-lifecycle.md) 9.1 decision. |
| Russ Cox, *Regular Expression Matching with a Trigram Index* (2012), with Sourcegraph's zoekt and GitHub's **Blackbird** (*sparse grams*) | Drop tokens entirely and index n-grams, which is what buys substring, punctuation and regex search. Blackbird states outright that code search wants **no stemmer and no stopword stripping**, and replaces fixed trigrams with sparse grams because `for` produced too many false positives. | **NOT BUILT — named to stop it being re-invented.** A second index plane and a far larger index; [`../work/proposals/identifier-exact-match.md`](../work/proposals/identifier-exact-match.md) §3d puts it **out of scope for 3.0**. |

### 1a · The tuning literature — read in full, **PARKED in full**

*All of these sit behind [`work/proposals/ranking-tuning.md`](../work/proposals/ranking-tuning.md).
Nothing in this block has changed a shipped number. They are here so a future
session does not re-read them to reach the same parked conclusion.*

| source | what it is | status |
|---|---|---|
| Kamphuis, de Vries, Boytsov & Lin, *Which BM25 Do You Mean?* (ECIR 2020) | Eight BM25 variants compared; *"no significant differences between any variant."* | **PARKED** — and the strongest single argument for never adding a variant switch. |
| Trotman, Puurula & Burgess, *Improvements to BM25 and Language Models Examined* (ADCS 2014) | Particle-swarm search over `k1`/`b`. | **PARKED** — the method a tuning run would use. |
| Zaragoza et al., *Microsoft Cambridge at TREC-13* | BM25F tuned in anger; `k1 = 27.5` — evidence the defaults are corpus-shaped, not universal. | **PARKED**. |
| Taylor, Zaragoza, Craswell, Robertson & Burges, *Optimisation methods for ranking functions with multiple parameters* (CIKM 2006) | The schedule for multi-parameter ranking optimisation. | **PARKED** — cited for its step schedule, 25 points/dimension. |
| Metzler & Croft, *Linear feature-based models for information retrieval* | Coordinate ascent, the RankLib default. | **PARKED**. |
| Lipani et al., *A systematic approach to normalization in probabilistic models* | Length normalisation as a systematic family, not a constant. | **PARKED** — the second-order argument in the same direction. |
| Svore & Burges, *A Machine Learning Approach for Improved BM25 Retrieval* | The identifiability degeneracy — several parameter sets score identically. | **PARKED** — the reason a tuned number needs a stability interval, not just a maximum. |

### 1c · Corpus diagnostics — the `fux inspect` proposal

*Four classical results behind a proposed read-only verb that X-rays the index:
which words are on every document, which documents no query can reach, and
which are near-duplicates. [`../archive/proposals/fux-inspect.md`](../archive/proposals/fux-inspect.md),
filed 2026-09-13.*

| source | what it is | status |
|---|---|---|
| Zipf, *Human Behavior and the Principle of Least Effort* (1949) | Term frequency follows a power law — a handful of words carry almost no information. | **PROPOSED** — the boilerplate lens: terms with `df/N` high and IDF ≈ 0 score nothing and bloat postings. The *"TLDR"* words Arpit asked to see. |
| Heaps, *Information Retrieval: Computational and Theoretical Aspects* (1978) | Vocabulary size grows as a sublinear power of corpus size. | **PROPOSED** — the fit that says whether a corpus's vocabulary is behaving normally, or whether a template is flattening it. |
| Broder, *On the resemblance and containment of documents* (1997) | MinHash — estimate set resemblance from a small signature. | **PROPOSED** — near-duplicate pairs and **template families** over hashed term sets. Duplicates split `df` and confuse ranking; this is the answer to *"did they create a similar index?"* |
| Azzopardi, de Rijke & Balog, *Building simulated queries for known-item topics* (SIGIR 2007) | **Retrievability** — whether a document can be reached by any plausible query at all. | **PROPOSED** — the findability lens, and the sharpest idea in the proposal: *a document no query can reach is stored, not indexed.* |

---

## 2 · Index structure, compression and storage

> 🔴 **This is the section where reading stopped code from being written.**
> The paper's committed-index design rests on these; the engine ships almost
> none of them, and [`docs/paper/the-fux-index-paper.md`](../docs/paper/the-fux-index-paper.md)'s
> status banner is the record of that.

| source | what it is | what depends on it — or what it stopped |
|---|---|---|
| Carmel, Cohen, Fagin, Farchi, Herscovici, Maarek & Soffer, *Static Index Pruning for Information Retrieval Systems* (SIGIR 2001) | Most of an inverted index can be dropped with bounded early-precision loss. | **NOT BUILT — falsified here.** Prediction P1 gated all construction on it and **FAILED** (2026-08-09). The committed index carries **full postings, permanently** ([SR-POSTINGS](0112_postings.md) decision 8). The method worked exactly as designed: the paper was right in general and wrong on this corpus. |
| Büttcher & Clarke, *A Document-Centric Approach to Static Index Pruning in Text Retrieval Systems* (CIKM 2006) | Keep each document's top terms by KL contribution — document-centric rather than term-centric. | **NOT BUILT in the engine.** It *was* built as an experiment: [`tools/pruning-eval/pruning/kl_select.py`](../tools/pruning-eval/pruning/kl_select.py) implements it, and that harness is what produced the FAIL above. |
| Mackenzie et al. (SIGIR 2024) | Pruning's recall reductions produce *"no significant differences"* once a re-rank stage runs. | **METHOD** — it is why the pruning pre-registration gates on **recall@20 of the candidate set**, not on the index's own `hit@5`. [`tools/pruning-eval/PRE-REGISTRATION-v2.md`](../tools/pruning-eval/PRE-REGISTRATION-v2.md). |
| Ottaviano & Venturini, *Partitioned Elias-Fano Indexes* (SIGIR 2014) | 4.63 bits/docid on Gov2. | **NOT BUILT** — parameterises the paper's §5 size model only. The measured `~4 922 packed B/doc` on real documents is produced by no codec this cites. |
| Moffat & Stuiver, *Binary Interpolative Coding for Effective Index Compression* (Information Retrieval 3(1), 2000) | < 1 bit/int on clustered lists. | **NOT BUILT** — same model, same caveat. |
| Pibiri & Venturini, *Techniques for Inverted Index Compression* (ACM CSUR, 2020); with Mallia & Porciani (ECIR 2019) | The survey the wire-format codec choice would be made from. | **NOT BUILT**. |
| Esposito, Graf & Vigna, *RecSplit: Minimal Perfect Hashing via Recursive Splitting* (ALENEX 2020) | Static term sets at ~2 bits/key. | **NOT BUILT** — there is no MPH term dictionary. |
| Groot Koerkamp, *PtrHash: Minimal Perfect Hashing at RAM Throughput* (SEA 2025) | The faster successor. | **NOT BUILT** — same. |
| Navarro, *Wavelet Trees for All* (CPM 2012), with Ferragina & Manzini, *Opportunistic Data Structures with Applications* / FM-index (FOCS 2000) | One succinct structure answering postings **and** forward index in ~n·log σ bits. | **REFUSED** — the theoretically maximal unification, rejected for v0.30 because every operation is bit-level rank/select: native-speed in C, hopeless in interpreted Python. Kept as [`work/proposals/wavelet-self-index.md`](../work/proposals/wavelet-self-index.md) with a two-condition graduation trigger. |
| Goodwin, Hopcroft, Luu, Clemmer, Curmei, Elnikety & He, *BitFunnel* (SIGIR 2017) | Bit-signature prefiltering. | **NOT BUILT — died with its host.** It was the paper's §8 "signature prefilter" mitigation; it went when `embed/fuxvec.py` was deleted (2026-08-25). |
| Auvolat & Taïani, *Merkle Search Trees: Efficient State-Based CRDTs in Open Networks* (SRDS 2019) | Ordered content-addressed trees with unique representation and state-based-CRDT merge. | **NOT BUILT — superseded 2026-08-09.** The paper's six-prefix single keyspace (`L/ P/ D/ V/ E/ M/`) does not exist: **git already supplies the Merkle tree**, and the committed plane is sharded canonical JSONL. The paper's §4 is deliberately exempt from rewrite and stands as a description of the superseded design. |
| Wang, Dinh, Ooi, Chen, Chen, Ji & Zhang, *ForkBase: An Efficient Storage Engine for Blockchain and Forkable Applications* (VLDB 11(10), 2018) | Versioning, dedup and tamper evidence pushed into the storage substrate. | **NOT BUILT** — the idea survived, the engine did not: git *is* the substrate, so nothing was written. |
| DeCandia et al., *Dynamo: Amazon's Highly Available Key-value Store* (SOSP 2007) | Read repair — serve possibly-stale state, verify what a read touches. | **BUILT, as a principle** — the freshness contract: the index may be stale, the **answer** is verified per read. [SR-REFER](0127_refer-plane.md), [SR-URL-FRESHNESS](0147_url-freshness.md). |
| Budiu, McSherry, Ryzhyk & Tannen, *DBSP: Automatic Incremental View Maintenance for Rich Query Languages* (VLDB 16, 2023) | Delta maintenance is provably equal to recompute. | **BUILT, as a licence** — it is the theoretical permission for incremental re-ingest ([SR-INGEST](0106_ingest.md)). No DBSP machinery exists in the tree. |
| DoltHub, *Cell-level Three-way Merge in Dolt* (2020) | Structural merging still surfaces semantic conflicts. | **NOT BUILT** — deliberately. fux eliminates the dominant conflict classes *by construction* (sorted, one-record-per-line, canonical) rather than merging cleverly. [SR-MERGE-DRIVER](0130_merge-driver.md). |
| Callan, *Distributed Information Retrieval* (2000); Si & Callan, ReDDE (SIGIR 2003) | Federated search: brokers rank from collection summaries; resource selection and result merging are the hard problems. | **NOT BUILT — dissolved.** fux occupies the *cooperative* corner with a single scorer: summaries are maintained rather than sampled, and score merging vanishes because sources are byte stores, not engines. |
| Campos, Mangaravite, Pasquali, Jorge, Nunes & Jatowt, *YAKE! Keyword Extraction from Single Documents* (Information Sciences, 2020) | Unsupervised per-document keyword extraction. | **NOT BUILT** — named in the paper as the keyword source for a pruned index; the pruned index is what P1 killed. |

---

## 3 · Caching and freshness

| source | what it is | what depends on it — or what it stopped |
|---|---|---|
| Megiddo & Modha, *ARC: A Self-Tuning, Low Overhead Replacement Cache* (FAST '03) | Adaptive replacement — scan-resistant, self-tuning between recency and frequency. | **BUILT** — `refer/arc.py`. [SR-CACHE](0131_cache.md). ⚠ Its win over LRU was measured on a **synthetic** trace and adopted on a post-hoc metric with that stated; the reopen-trigger asking for a real workload is still live ([`work/compare/cache-policy.compare.md`](../archive/compare/cache-policy.compare.md)). |
| RFC 5861, *HTTP Cache-Control Extensions for Stale Content* (`stale-while-revalidate`) | Serve stale immediately, revalidate behind it. | **BUILT, as the shape refused to be blurred** — fux tells you which verdict you got (`current`, `stale`, `as-ingested`, `cached`, `unverified`) rather than silently serving stale. [SR-CACHE](0131_cache.md) decision 7. |
| RFC 9110 conditional requests / `ETag` | Validators beat timestamps; `304` when nothing changed. | **BUILT** — the refetch path. [`work/compare/record-freshness.compare.md`](../archive/compare/record-freshness.compare.md). |
| Cao et al., *Re3: Learning to Balance Relevance & Recency for Temporal Information Retrieval* (2025) | Recency and relevance traded explicitly rather than implicitly. | **PARKED** — grounding for [`work/compare/df-over-the-union.compare.md`](../work/compare/df-over-the-union.compare.md); no recency prior ships. |

---

## 4 · The graph plane

| source | what it is | what depends on it — or what it stopped |
|---|---|---|
| Page, Brin, Motwani & Winograd, *The PageRank Citation Ranking: Bringing Order to the Web* (1999) | Random-surfer centrality, and the 0.85 damping constant. | **BUILT** — the graph plane's centrality and its damping default, taken from the paper rather than tuned. [SR-GRAPH](0126_graph.md). |
| Raghavan, Albert & Kumara, *Near linear time algorithm to detect community structures in large-scale networks* (Phys. Rev. E 76, 2007) | Label propagation — communities in near-linear time, no parameter to pick. | **BUILT** — `fux graph`'s communities, and the near-linear bound is what makes it affordable on a hook. |
| Levin & Peres, *Markov Chains and Mixing Times*, §1.3 | Lazy chains as the standard device for removing periodicity. | **BUILT** — the walk is lazy for this reason and no other. |
| Haveliwala, *Topic-Sensitive PageRank* (WWW 2002) | A personalised restart vector — the walk biased toward a set of seed documents rather than the whole corpus. | **ACCEPTED, not yet built** — the seeding behind `fux graph --seed` and the graph-expanded `ask` ratified 2026-09-13. The seeds are the lexical top-k, **taken by rank, not score**. |
| Valiant, *The complexity of enumerating and reliability problems* (SIAM J. Comput. 8(3), 1979) | Counting simple paths is **#P-complete**. | **NOT BUILT** — unbounded path enumeration. It is why `fux path` has a `--hops` ceiling and says so honestly instead of pretending completeness. [`work/compare/path-hops-bound.compare.md`](../archive/compare/path-hops-bound.compare.md). |
| Yen, *Finding the K Shortest Loopless Paths in a Network* (Management Science 17(11), 1971) | The bounded alternative to enumeration. | **NOT BUILT — named as the replacement** if the enumeration is ever swapped out. |

---

## 5 · Query expansion and document enrichment

| source | what it is | what depends on it — or what it stopped |
|---|---|---|
| Wang, Yang & Wei, *Query2doc: Query Expansion with Large Language Models* (2023) | An LLM pseudo-passage appended to the query: +3 % to +15 % BM25, no fine-tuning; weighted ~1:5 against the query. | **BUILT** — `fux ask --expand "<pseudo passage>"`, scored at a fixed lower weight, recorded verbatim on the receipt and replayable by `fux verify`. **fux never calls the model; the caller is one.** [SR-EXPAND](0149_expand.md). |
| Jagerman, Zhuang, Qin, Wang & Bendersky, *Query Expansion by Prompting Large Language Models* (2023) | Chain-of-thought is the best expansion prompt for BM25, and beats classical PRF. | **BUILT** — the prompt guidance in the expand skill, and the argument against building PRF. |
| Nogueira & Lin, *docTTTTTquery* / doc2query | Document-side expansion, using **training** queries only — the split enforced mechanically. | **BUILT** — `fux enrich`. And its most important contribution is negative: *document-side enrichment is not novel; doing it **without** the train/test split is what was novel here.* [SR-RS](0133_predictions.md). |
| Gospodinov, MacAvaney & Macdonald, *Doc2Query−−* (2023) | Generated queries bloat the index ~33 %; filtering them back out recovers most of it. | **NOT BUILT** — no filtering step exists; the bloat is accepted and named. |
| RM3 / pseudo-relevance feedback (classical) | The model-free expansion alternative. | **NOT BUILT** — known to *hurt* on short-passage corpora and help on long newswire. Recorded as *"may be measured, never assumed."* Its papers are now filed in §1b [4]. |
| Nogueira, Yang, Lin & Cho, *Document expansion by query prediction* (2019) | doc2query proper — predict the questions a document answers and append them to it. | **ACCEPTED 2026-09-13** — the ancestor of `fux correct`: a **human**-authored question line appended to the document's existing enrichment file. Same mechanism, different author, and authorship is carried as provenance. [`../work/compare/fux-correct.compare.md`](../work/compare/fux-correct.compare.md). |
| Rocchio, *Relevance feedback in information retrieval*, in Salton (ed.), *The SMART Retrieval System* (1971) | Move the query toward the document the user chose. | **NOT BUILT — and correctly identified as already present.** Query-time only, nothing persists, which is exactly what `--expand` does by hand. Considered as option (c) for `fux correct` and passed over for the durable mechanism. |

---

## 6 · Reranking, and the dense lane that died

| source | what it is | what depends on it — or what it stopped |
|---|---|---|
| NevIR (EACL 2024), with the SIGIR 2025 reproduction (arXiv 2502.13506) | Negation, measured: random 25 %, TF-IDF 2 %, SPLADE++ 8–9 %, bi-encoders 7–11 %, cross-encoders ≈ 50 %, listwise LLM rerankers best. | **NOT BUILT — this paper killed the litmus test.** The vector plane had been justified on a negation/currency query; NevIR shows **dense bi-encoders do not solve negation either**. The gate was re-aimed at vocabulary-gap failures, and currency is solved by **metadata** (declared supersession) instead. |
| Morris, Kuleshov, Shmatikov & Rush, *Text Embeddings Reveal (Almost) As Much As Text* (EMNLP 2023) | 92 % exact-match text recovery from 32-token GTR embeddings — embedding inversion is a demonstrated attack. | **BUILT, as a documented accepted risk** — the strongest-evidenced of three leaks in the hashed-record review; the field was kept and the exposure written down rather than closed. Reopen if `--hybrid` ever becomes default-on. ⚠ **The review this grounded is MOOT since 2026-09-20**: W-194 deleted hashed meta and retired L5, so the record it assessed no longer exists and the *title* leak it sat beside is now accepted outright. **Nothing about the paper became untrue**, and a dense lane returning would put it straight back in force. [`work/compare/meta-privacy.compare.md`](../archive/compare/meta-privacy.compare.md), [SR-LAW-5](0007_LAW-5-hashed-meta.md) (superseded). |
| Ettin reranker line (17.6 M / 32.8 M) | The actual model class behind the record's *"17–32 M cross-encoder"*. | **REFUSED** — the cross-encoder is refused on **cross-machine determinism**, not cost. Condition 1 was **vacated** (not replaced) in 2026-08-25 because substituting a second unmeasured claim for the first is the exact error being documented. [SR-RERANK](0138_rerank.md), [`work/compare/cross-encoder-reopen.compare.md`](../archive/compare/cross-encoder-reopen.compare.md). |
| RankZephyr (arXiv 2312.02724) | Listwise LLM reranking, open weights. | **NOT BUILT** — L1 and L4 (no model, no network) rule it out before quality is discussed. |
| BM25S (arXiv 2407.03618) | Sparse BM25 at speed in numpy/scipy. | **PARKED** — architecture review only; L1 (stdlib) makes it unadoptable as-is. |
| Inference-free learned sparse retrieval (arXiv 2411.04403) | Learned sparse weights with no query-time model. | **PARKED** — the one learned-sparse family L4 does not immediately forbid. Nothing built. |

---

## 7 · Chunking and extraction

| source | what it is | what depends on it — or what it stopped |
|---|---|---|
| UAX #29, *Unicode Text Segmentation* | *"Plain text provides inadequate information for determining good sentence boundaries."* | **NOT BUILT — there is no sentence rung** in the chunk ladder, and this is the reason rather than an oversight: doing it properly needs CLDR locale data (**L1**), doing it improperly cuts mid-sentence. [SR-CHUNKING](0151_chunking.md) decision 5. |
| Docling, `HierarchicalChunker` / `HybridChunker` | A mature implementation that merges only chunks *"with the same headings and captions"*, treats headings as **context prepended**, and has **no per-format chunking declaration at all**. | **BUILT** — the parent/sibling merge rule, and the separation of *what delimits* from *what names*. **And it caused a removal**: [SR-DECODE](0139_decode.md) decision 19's per-format chunking declaration was deleted because a mature system solving the same problem never needed one. ⚠ **Convergent design, not a measurement.** |
| Chroma, *Evaluating Chunking Strategies for Retrieval* | Token-level: 200-token chunks score 8.0 precision/IoU against 1.5 at 800, recall roughly flat. | **Corroboration only, and explicitly insufficient.** Same *direction* as fux's own `hit@1` 0.229 → 0.875 per-row result — but embedding-based where fux is lexical BM25F. 🔴 It does **not** discharge the veto condition; an outside paper agreeing with an `informed` run does not make it a blind one. |
| *Document segmentation strategies for retrieval* (arXiv 2602.16974) | Six segmentation methods × four embedders: *structure-based outperforms semantic/LLM-guided*; whole-document contextualisation **degrades in-document retrieval**. | **BUILT** — the external case that fux's deterministic structural chunking is the **right** answer, not merely the one L1 forced. Also the case against small-to-big. ⚠ Covers narrative text only — it grounds the *method*, not the table rule. |
| Chunking strategies, 36 compared (arXiv 2603.06976) | The broad survey. | **PARKED** — architecture-review reading. |
| *Named but NOT read* — docling discussion #191; IBM, *Chunking in RAG* | — | Listed in [SR-CHUNKING](0151_chunking.md) as **seen and skipped**, so a later session knows they were not missed. *A citation nobody followed is a defect in a different coat.* |

---

## 8 · Answering, confidence and abstention

| source | what it is | what depends on it — or what it stopped |
|---|---|---|
| Ji et al., *Survey of Hallucination in Natural Language Generation* (2022) | A confident wrong answer is the expensive failure mode. | **BUILT** — `fux answer` **quotes and cites; it does not generate.** [SR-ANSWER](0105_answer.md). |
| Cronen-Townsend, Zhou & Croft, *Predicting Query Performance* (SIGIR 2002) | Retrieval-time difficulty is computable **without relevance judgments**. | **BUILT** — the confidence band exists at all because of this. [SR-CONFIDENCE](0141_confidence.md). |
| Shtok, Kurland, Carmel, Raiber & Markovits, *Predicting Query Performance by Query-Drift Estimation* (TOIS 2012) | Score dispersion among the top results as the difficulty signal. | **BUILT** — the band's actual statistic. |
| Rajpurkar, Jia & Liang, *Know What You Don't Know: Unanswerable Questions for SQuAD* (ACL 2018) | Answerable/unanswerable pairing as an evaluation design. | **NOT BUILT — and it exposed a hole.** Blind-authored unanswerable questions were run twice: **fux abstained 0 times out of 20.** |
| Kamath, Jia & Liang, *Selective Question Answering under Domain Shift* (ACL 2020) | Risk–coverage under shift; the El-Yaniv lineage applied to QA. | **PARKED** — [`archive/proposals/abstention-gate.md`](../archive/proposals/abstention-gate.md) (archived 2026-09-14; live successor W-176), awaiting Arpit's pick between disclose / gate / build. |
| El-Yaniv & Wiener, *On the Foundations of Noise-free Selective Classification* (JMLR 11, 2010) | The formalism for a reject option. | **PARKED** — same proposal. |
| *Machine Learning with a Reject Option: A Survey* (Chow's rule) | Only the **cost ratio** moves the reject threshold, never the absolute costs. | **PARKED** — the arithmetic an abstention gate would use. |
| *Performance measures for classification systems with rejection* | The threshold as `(C_r − C_c)/(C_e − C_c)`. | **PARKED**. |
| *Overcoming Common Flaws in the Evaluation of Selective Classification Systems* (NeurIPS 2024) | Risk–coverage curves and AURC as the honest measure. | **PARKED** — the measure the gate would be judged on. |
| *Why Language Models Hallucinate* (2025) | The confidence-target form `penalty = t/(1−t)`, with natural anchors `t = 0.5 / 0.75 / 0.9`. | **PARKED** — the scoring form [SR-WORK-QUALITY](0056_WORK-quality.md) would adopt. |
| *Evaluating large language models for accuracy incentivizes hallucinations*, **Nature (2026)** | Accuracy-only scoring rewards guessing over abstention. | **METHOD — non-negotiable.** It is why [SR-WORK-QUALITY](0056_WORK-quality.md) decision 5 exists: fux may not publish an accuracy-only headline. |
| *I-CALM — Incentivizing Confidence-Aware Abstention* | Abstention is far more sensitive to the abstention **reward** than to the error penalty. | **PARKED**. |
| Harabagiu, Moldovan et al., *FALCON: boosting knowledge for answer engines* (TREC-9, 2000) | Answer-type matching: *how many* expects a number, *when* a date, *who* a capitalised name. | **PROPOSED — and it is the load-bearing one.** Of nine candidate abstention mechanisms, the answer-type check is the **only** one that reaches the u017 class: a question assembled from the corpus's own words, which every term-overlap signal scores highly. [`../work/compare/abstention-gates.compare.md`](../work/compare/abstention-gates.compare.md). |
| *Hallucinations Undermine Trust; Metacognition is a Way Forward* | The open rubric and the Utility–Error curve. | **NOT BUILT** — the blended single number is refused; the curve is the shape, if ever. |

---

## 9 · How this repo measures itself

*Nothing in this section is engine code. All of it is why a number in this
repo is allowed to be believed.*

| source | what it is | what depends on it |
|---|---|---|
| Voorhees & Harman, *TREC: Experiment and Evaluation in Information Retrieval* (2005) | Per-query relevance judgments as the unit of evidence. | **METHOD** — [SR-WORK-BENCHMARK](0053_WORK-benchmark.md); every run files per-query rows, not a mean. |
| TREC's manual/automatic run split (in force since 1994) | Manual runs are **reported and reclassified**, never banned, and still contribute to the pool. | **METHOD** — [SR-RS](0133_predictions.md) decisions 11–12 copy the mechanism exactly: *reclassify, do not ban.* |
| TREC relevance-judgment methodology (`qrels`) | Judgments come from assessors reading documents — **never** derived from a system's own output. | **METHOD** — the golden ladder's discipline, and the rule that a golden is written from the corpus. |
| CONSORT 2025, item 20a | Abandon binary blinding labels; name **who** was blind at **which stage**, analysts included. | **METHOD** — the per-artifact blinding list. It is also the standard used to **refuse** a proposed rule (*"an artifact whose author has seen the evaluation set is not evidence"*) on four named faults. |
| ARRIVE 2.0, item 5 | *"Describe who was aware of the group allocation at the different stages."* | **METHOD** — [SR-RS](0133_predictions.md) decision 13's sentence, copied verbatim. |
| Kaufman, Rosset et al., *Leakage in Data Mining* (KDD 2011) | Legitimacy is a property of **how a feature came to exist**, not of its values. | **METHOD** — an enrichment note *is* a feature; this is the test applied to it. |
| Kriegeskorte, Simmons, Bellgowan & Baker, *Circular analysis in systems neuroscience* (Nature Neuroscience, 2009) | Double dipping — the same data selecting the artifact and scoring it. | **METHOD** — the closest fit for the **human** role in this failure; the blind-authorship rule. |
| Dwork et al., *adaptive overfitting* (Science, 2015) | Overfitting through repeated feedback from measured scores. | **CONSIDERED AND REJECTED as the fit** — fux's author saw inputs, not scores. Logged so nobody reaches for it again. |
| Dai et al., *Neural Retrievers are Biased Towards LLM-Generated Content* (KDD 2024) | **Source bias** — retrievers rank LLM-written text higher regardless of whether it informs; the effect reaches rerankers. | **BUILT (as a control)** — [`tools/quality-controls/placebo.py`](../tools/quality-controls/placebo.py). Every enrichment arm had added ~115 words of fluent prose with **no matched control**, so presence and content were never separable. ⚠ The placebo has been built and **never run**. |
| BIG-bench's canary GUID; FrontierMath's sealed holdout | The two standing demonstrations that disclosure is a fallback and a **sealed set** is the control. | **BUILT (as a control)** — [`tools/quality-controls/seal.py`](../tools/quality-controls/seal.py). Also never run. |
| Center for Open Science, *Preregistration* | The practice, and the outcome-reporting bias it exists to prevent. | **METHOD** — every `PRE-REGISTRATION*.md` in the repo, and the standing rule that **a pre-registered threshold may never move.** |
| Sainz et al., *NLP Evaluation in trouble: On the Need to Measure LLM Data Contamination for each Benchmark* (Findings of EMNLP 2023) | The instrument must live outside the system under test. | **METHOD** — why `fux-lab` is a separate repo and not a directory. [`work/setup/fux-lab.md`](../work/setup/fux-lab.md). |
| Chen & Revels, *Robust benchmarking in noisy environments* (arXiv 1608.04295) | Medians and interleaving, not means and sequencing. | **METHOD** — `fux-benchmark`'s two-arm interleaved design. [`work/setup/fux-benchmark.md`](../work/setup/fux-benchmark.md). |
| *airspeed velocity* (`asv`) | Keep every result per commit so the next run has a baseline. | **METHOD** — the regression directory's per-run contract. |
| RAGChecker (NeurIPS 2024) | Retriever quality **bounds** the whole system. | **METHOD** — the funnel, and why `recall@k` is the metric fux optimises rather than an end-to-end score it does not own. |
| *Benchmarking IR Models on Complex Retrieval Tasks* (arXiv 2509.07253) | `recall@k` is the most directly actionable RAG metric. | **METHOD** — same; `recall@k` reported as a **curve**, not a point. |
| *RAG Evaluation in the Era of LLMs: A Comprehensive Survey* (arXiv 2504.14891) | Position bias over long context. | **NOT BUILT** — a decaying rank discount was **rejected**: it misdescribes an agent consumer, which reads what it is given. |
| *Who Drifted: the System or the Judge?* (2026) | A measured GPT-4o evaluator collapse between May and June 2026. | **NOT BUILT** — there is **no LLM-as-judge** anywhere in the harness, and this is the measurement that settles it. |
| *A Systematic, Large-Scale Evaluation of LLM-as-a-Judge* (2026) | Judged datasets are not authoritative beyond their temporal scope. | **NOT BUILT** — same refusal, second source. |
| *Information retrieval evaluation using test collections* (2016) | TREC weights topics equally **and states the assumption**. | **METHOD** — the model for stating an assumption rather than hiding it. |
| *Goodhart's Law Comes for Every Benchmark You Trust* (CACM) | Publishing a metric makes it a target. | **METHOD** — why headline numbers carry their controls. |
| `cwl_eval` (SIGIR 2019 demo) | The C/W/L user-model framework for evaluation measures. | **REJECTED alternative** — considered for the quality funnel and not taken; recorded so the option is visible rather than forgotten. |
| *Weight stability intervals for multi-criteria decision analysis using the weighted sum model* | When a weighted-sum ranking is stable under weight perturbation. | **METHOD** — [SR-WORK-QUALITY](0056_WORK-quality.md) decision 7's guard. |
| Buckley & Voorhees, *Evaluating Evaluation Measure Stability*; Buckley, Dimmick, Voorhees & Lynam, *Bias and the limits of pooling*; Smucker, Allan & Carterette, *A comparison of statistical significance tests for IR evaluation*; Fuhr, *Some Common Mistakes In IR Evaluation*; Sakai, *Topic set size design*; IR significance testing (arXiv 2501.03930) | The evaluation-methodology block behind any future tuning run. | **PARKED** — [`work/proposals/ranking-tuning.md`](../work/proposals/ranking-tuning.md). The **exact two-sided binomial** in [`tools/quality-controls/verdict.py`](../tools/quality-controls/verdict.py) is the one piece of this that shipped. |

---

## 10 · Privacy, PII and the laws

| source | what it is | what depends on it — or what it stopped |
|---|---|---|
| Barbaro & Zeller Jr., *A Face Is Exposed for AOL Searcher No. 4417749*, NYT, 9 August 2006 | 20 million de-identified queries; one user identified **from the queries alone**. | **Law L8's grounding.** ⚠ **OVERRIDDEN, NOT REFUTED** (2026-08-27): the owner weighed it against a readable local log and chose the log. Nothing about the case became untrue — **a future session may not cite the reversal as evidence the risk was disproved.** The mitigation is confinement: the use record is gitignored. [SR-LAWS](0001_LAWS.md). |
| Morris et al., EMNLP 2023 | *(see §6)* | The embedding-inversion half of the same review. |
| H. P. Luhn, *Computer for verifying numbers*, US 2,950,048 (1960) | The mod-10 check digit. | **BUILT** — the `luhn` validator in `.fux/pii.toml`, with the `79927398713` vector. [SR-PII](0148_pii.md). |
| J. Verhoeff, *Error Detecting Decimal Codes*, Mathematical Centre Tracts 29 (1969) | The dihedral-group check digit, catching transpositions Luhn misses. | **BUILT** — the `verhoeff` validator, its D5 tables and the `2363` vector. |
| Nygard, *Documenting Architecture Decisions* (2011) | The ADR form. | **BUILT** — the whole `records/` register descends from it (renamed SR, 2026-09-13). |
| Lakoff & Johnson, *Metaphors We Live By* (1980) | The noun chosen for a system governs the inferences drawn about it. | **BUILT** — Law L6, *say index*. Calling it a database would have imported the wrong expectations. |

---

## 11 · Landscape reading — read, not adopted

*Read while positioning fux; none of it changed the engine. Kept so the
market claim in `README.md` is sourced and so nobody re-reads it cold.*
[`work/proposals/agent-search-landscape.md`](../archive/proposals/agent-search-landscape.md) ·
[`work/proposals/architecture-review-2026-08-28.md`](../work/proposals/architecture-review-2026-08-28.md)

- *Lore — git commits as structured knowledge for AI agents* (arXiv 2603.15566) — git as the knowledge-protocol substrate. **The nearest neighbour to fux's own premise.**
- Amazon, *agentic keyword search ≈ RAG* (arXiv 2602.23368) — the case that a keyword index is enough for an agent.
- CodeRAG-Bench (NAACL Findings 2025) · SWE-Explore (arXiv 2606.07297) — code-retrieval benchmarks. **Deliberately not adopted**: fux parses no code and by default indexes none.
- Graphify — deterministic AST knowledge graphs for agents. **Structure, not ranked retrieval**; named in the paper as the complement, not the competitor.
- Parallel, Perplexity, Exa, Brave, Jina, Linkup; turbopuffer, Quickwit, Common Crawl, Cloudflare Pay-Per-Crawl — the commercial agent-search landscape.

---

## 12 · Standards and specifications

*Not papers. Listed because several of them are load-bearing in exactly the
way a paper is: they decide a byte, not a preference.*

| spec | what it decides |
|---|---|
| **RFC 8785** — JSON Canonicalization Scheme | **BUILT** — the committed record's encoder. One byte sequence per record, on every machine. |
| **RFC 7693** — BLAKE2 | **BUILT** — the digest, including the 32-bit-halves reimplementation in the Node reader, pinned against Appendix A at digest sizes 1, 8 and 20. |
| **RFC 6455** — WebSocket | **BUILT** — the hand-rolled client the CDP fetcher speaks; no dependency. |
| **RFC 5861** · **RFC 9110** | *(see §3)* |
| **RFC 3986** §3.1 · **RFC 8259** §8.1 | **BUILT** — the `scheme://` grammar; JSON is UTF-8 by definition, so there is one encoding. |
| **UAX #29** | *(see §7)* |
| **TOML v1.0.0**, and Python `tomllib` | **BUILT** — every config file; duplicate keys invalid, read-only, 3.11+ (**L7**). |
| **JSON Lines** | **BUILT** — the committed index container. |
| **PEP 518** `[tool]` table | **BUILT** — the opaque-config-table discipline `fux.toml` copies. |
| `gitignore(5)` · `gitattributes(5)` · `githooks(5)` · **git partial clone** · **git pack format** | **BUILT** — `.fuxignore`'s grammar and last-match-wins; the merge driver's registration; that `post-commit` cannot affect the commit; prior art for the node-major seekable store. |
| **CACHEDIR.TAG** | **BUILT** — `.fux/runtime/` is tagged so backup tools skip it. |
| **POSIX** utility conventions | **BUILT** — `fux find`'s output shape. |
| **Model Context Protocol** (stdio transport) | **BUILT** — `fux mcp`. |
| **Chrome DevTools Protocol**, `Fetch` domain · **Fetch Standard** §CORS-safelisted response headers | **BUILT** — the CDP fetcher's interception, and why an in-page cross-origin fetch cannot see `ETag`. |
| Claude Agent Skills · Codex skills · GitHub Copilot agent skills · Kiro steering · VS Code agent skills | **BUILT** — the four vendor surfaces `fux setup` writes. [SR-AGENT-POLICY](0132_agent-policy.md). |
| `cargo add` · `helm repo add` · `uv` · Python `argparse` · ripgrep types · GitHub Linguist overrides · Sphinx `source_suffix` and two-phase build · Bazel hermeticity · Lucene `IndexWriter` · `git gc --auto` · Homebrew `brew doctor` · `scrapy-playwright` · SQLite file format · Elastic `_explain` / `indices_boost` · Solr DisMax · SLSA · in-toto · W3C PROV-O · EU AI Act Art. 12 · Google SRE Workbook · `SOURCE_DATE_EPOCH` | **Prior art**, each cited once for one decision. The two that decided *against* something: **Elasticsearch `indices_boost`**'s first-match rule (unusable, so fux went multiplicative) and **`brew doctor`**'s documented drift into warning on supported configurations (the failure `fux doctor` guards against). |
| Apache Solr `QueryElevationComponent` (`elevate.xml`) · Elasticsearch *Pinned query* · SharePoint promoted results | **PRIOR ART, narrowed to a rare escape hatch** — an exact query forced to rank #1 from a committed file. Kept as `fux correct --pin` and deliberately not the main mechanism: it fixes one phrasing and leaves the next one wrong. |
| **Automatic browser fallback**, as argued by its proponents | **REFUSED** — the one entry here listed because fux does the opposite: a browser fetch is **per-request opt-in**, never an automatic escalation. [SR-HTTP-FETCHER](0119_http-fetcher.md). |

---

## 13 · Maintaining this file

**Trigger — update this file in the same change that:**

1. adds a source to any record's **Papers and specifications** block, a compare
   doc's **References**, a proposal, or an environment note;
2. changes a source's *status* — a **PARKED** proposal graduates, a **REFUSED**
   fork reopens, a **NOT BUILT** row gets built, or a measurement falsifies a
   row the way P1 falsified static index pruning;
3. deletes code that a row names. A row pointing at a deleted module is the
   same defect as a registry row pointing at a deleted file.

**Three rules, matching the register's own:**

- **Nothing appears here that is not cited somewhere else in the repo.** This
  file is an index of the repo's sourcing, not a reading list. A source that
  belongs only here belongs in a proposal instead.
- **The fourth column is the point.** A row that says what a paper *is* and not
  what it *holds up* is not finished. If nothing depends on it and it stopped
  nothing, it goes to §11.
- **Never soften a negative row.** *Falsified*, *refused*, *deleted*,
  *overridden* are the accurate words, and the rows that carry them are the
  most useful ones in the file.

**Last full sweep: 2026-09-13**, re-run the same day against the five documents filed after the first pass — [`fux-inspect`](../archive/proposals/fux-inspect.md), [`search-improvements-v3`](../work/proposals/search-improvements-v3.md), [`abstention-gates`](../work/compare/abstention-gates.compare.md), [`fux-correct`](../work/compare/fux-correct.compare.md) and [`ask-graph-expansion`](../work/compare/ask-graph-expansion.compare.md) — which added 16 sources and moved three rows. ⚠ **The first pass read only each document's final `References` block**; these five carry theirs under `## Reference` (singular) or inline, so a sweep matches both and reads the body, not just the tail.

**Known gap.** `work/regression/**` run reports are not swept for citations —
runs cite the records, not the other way round. If that ever stops being true,
this file is wrong before it is incomplete.
