---
type: Standing Record
kind: component
name: SR-INSPECT
title: "SR-INSPECT (0156) — `fux inspect`, the index X-ray: six lenses, three flagged checks, and a local dictionary that names the hashes"
description: "Arpit asked whether a consumed index is a good index or a bad one. `fux inspect` answers it descriptively: six lenses over the committed shards — boilerplate, findability, length and fields, duplication and templates, analyzer coverage, graph — each printing distributions and named lists, each naming the lever that would change what it found and applying none. Exactly three numbers carry a pass/attention flag and their floors are provisional, measured on the golden ladder and dropped to descriptive if one ever flags a healthy rung. The committed index holds term hashes, so the words come from a gitignored dictionary built by re-tokenising the sources locally; nothing new is committed and nothing is fetched."
status: accepted
date: 2026-09-14
feature: the index X-ray
owns: [src/fux/inspect@d1930eef9504]
laws: [L2, L3, L4, L6, L8]
timestamp: 2026-09-14T00:00:00Z
content_sha: bc9e054e10e489221ca1d091246a1fa0e9dd2986a7bb7aa3a13f0a9615a06b20
ratifies: W-169
---

# SR-INSPECT — what the index looks like, said out loud

## §1 — For humans

**`fux doctor` tells you whether the machine is set up. `fux inspect` tells you
whether the index is any good.** They are different questions with different
remedies: `doctor`'s finding is fixed by a command or a config edit,
`inspect`'s by a change to the corpus — a stopword, an `archived=`, a decoder,
an enrichment. That is why this is a verb and not a flag.

**It is descriptive, and that is the design rather than a limitation.** Six
lenses print numbers and named lists. Exactly three numbers carry a flag, and
every one of those three says *provisional* on the line it prints. There is no
one-number index score, for the same reason the confidence band refuses to be
one number: it would be the figure everybody quotes and the one nobody can act
on.

**The words are the hard part.** The committed index holds 8-byte term hashes,
not words — a deliberate privacy property — so *"`tldr` is on every document"*
is unanswerable from the index alone. `inspect` re-tokenises the sources that
are already on this disk, with the same analyzer, into a **gitignored**
hash → word dictionary under `.fux/runtime/inspect/`. Nothing new is committed,
nothing is fetched, and the report is byte-identical run to run.

```mermaid
flowchart LR
    IDX[".fux/index/<br/>hashes + statistics"] --> V["one pass<br/>IndexView"]
    SRC["the sources<br/>already on this disk"] --> D[".fux/runtime/inspect/<br/>dictionary.json · GITIGNORED"]
    D --> V
    V --> L["six lenses"]
    L --> C["three flagged checks<br/>provisional floors"]
    L --> R["report.md + report.json<br/>every finding names its LEVER"]
    C --> R
    R -.->|"never applies one"| X["stopwords · .fuxignore<br/>archived= · enrich · decoder"]
```

<details>
<summary><b>ASCII twin</b> — the same diagram, for terminals, diffs, and any reader without a Mermaid renderer</summary>

```text
  .fux/index/ ------------+
  hashes + statistics     |
                          v
  the sources --> dictionary.json --> IndexView --> six lenses --+--> report.md
  on this disk    GITIGNORED           one pass                  |    report.json
                                                                 +--> three checks
                                                                      (provisional)
                                          every finding NAMES a lever
                                          and APPLIES none:
                                          stopwords . .fuxignore
                                          archived= . enrich . decoder
```

</details>

### Examples

```console
$ fux inspect --retrieval-sample 25 --top 10
# `fux inspect` — the index, as it is

1179 document(s) · 26749 distinct term(s) · 457919 posting(s) · 5708 edge(s)

**Read-only.** Every finding below names the lever that would change it, and applies none.

## Checks — four numbers, three of which carry a flag

| check | value | floor | status | what it means |
|---|---|---|---|---|
| unreachable share | 0.1 % | <= 0.01 *(provisional)* | ok | 1 of 1179 documents carry no distinctive term at all, so no query can select them (EXHAUSTIVE - every document was checked) |
| boilerplate share | 7.2 % | <= 0.60 *(provisional)* | ok | 33027 of 457919 postings carry one of 46 term(s) on half the corpus or more |
| near-duplicate share | 13.4 % | <= 0.20 *(provisional)* | ok | 158 of 1179 documents are one half of a near-duplicate pair (Jaccard >= 0.80); 231 pair(s) |
| findable share | 100.0 % | — *(descriptive: no floor separates a healthy corpus from a bad one)* | descriptive | 25 of 25 documents are returned in the top 3 for their own most distinctive words (an evenly spaced SAMPLE - the share is an estimate) |

… 120 lines omitted …

| word | df | share | idf |
|---|---|---|---|
| `2026` | 1016 | 86 % | 0.15 |
| `md` | 990 | 84 % | 0.18 |
| `work` | 969 | 82 % | 0.20 |
```

Captured on this repository at `91255adb`. The top-`df` row is the *"TLDR is
everywhere"* case Arpit asked for, on a real corpus: `2026` is on 86 % of these
documents and scores almost nothing.

---

## §2 — For agents

### Context

**Arpit, 2026-09-13:** *"I need some kind of tool to analyse the index that is
consumed: is it a good index or a bad index?"* Three related questions came with
it — which words are on every document, whether documents produce similar index
shapes, and whether the result is good.

Nothing answered any of them. `fux doctor` answers *is this repository set up*;
`fux ask --why` answers *why did this one document rank*; the benchmark answers
*how well does the engine do on a graded corpus*. Between the three there was no
way to look at a corpus and see its shape — and the M1 pruning gate is the
standing proof that this matters: k=128 pruning returned a zero delta on three
eval corpora because their documents' **median vocabulary is 32–46 distinct
terms**, so the treatment was a no-op for 97 %+ of documents. That fact was
discoverable from the index the whole time and nobody could see it.

### Decision

1. **`fux inspect` is a verb, beside `doctor`, never inside it.** `doctor`
   checks the **environment**; `inspect` checks the **index** (L6's vocabulary:
   it is an index, not a db). Both are read-only and neither applies a lever.
   The boundary test is the remedy: a row belongs to `doctor` when the fix is a
   command or a config edit, and here when the fix is a change to the corpus.

2. **It reads the COMMITTED index, never `.fux/runtime/`.** `inspect` works in
   a clone that has never run `fux build`. A report that silently described a
   stale accelerator would be the worst kind of wrong — plausible.

3. **Words come from a local, gitignored dictionary**, built by re-tokenising
   the sources with the live analyzer:
   `.fux/runtime/inspect/dictionary.json`. The committed index stays hashes
   ([SR-POSTINGS](0112_postings.md) decision 2) and **nothing new is
   committed**. The dictionary's cache key is the **shard content shas**, never
   an mtime — an mtime reports a `git checkout` as fresh.

4. **The dictionary never fetches.** A `file:` document is read from the
   working tree (reading your own checkout is not a fetch); a `url:` document
   is read from `.fux/acquired/` when its bytes were retained and is **skipped,
   named, and counted** otherwise. L4 has no exception here and needs none.

5. **The field texts are built by `ingest/extract.py`'s own helpers,
   imported.** `_headings_and_body` knows about code fences and about
   `.rst`/`.adoc`/`.org`; `_title` knows where a title comes from. A second
   copy of that logic would name words the index does not hold and miss words
   it does, and the report would be confidently wrong about which terms exist.

6. **Six lenses, and each names its own finding:**

   | lens | what it says | what it names |
   |---|---|---|
   | **boilerplate** | terms by `df/N` with IDF; hapax share; Zipf slope; Heaps β | the top-`df` words |
   | **findability** | distinctive-term count per document; self-retrieval | **unfindable documents** |
   | **length & fields** | per-field token totals; body and vocabulary percentiles | empty titles, headingless documents, `ctx` over body, the shortest |
   | **duplication & templates** | minhash Jaccard; heading-set signatures | near-duplicate pairs, template families |
   | **analyzer coverage** | word-like runs kept vs seen; dictionary coverage | documents the index knows only by their file name, undecodable and unreadable ones, and `queue.tsv` |
   | **graph** | orphans, hubs by in-degree, community sizes | isolated documents and mega-hubs |

7. **Findability is answered twice, and the report says which half is which.**
   *No distinctive term* is **exhaustive** — a document whose every term sits on
   more than 10 % of the corpus carries nothing a query can select it by, and no
   retrieval run is needed to know that. *Self-retrieval* is a **sample**: it is
   one full query per document, so it runs over an evenly spaced sample
   (`--retrieval-sample`, `0` for all of them) and the share is labelled an
   estimate.

8. **Distinctive and boilerplate are SHARES of the corpus, not IDF numbers** —
   at or below 10 % of documents, and at or above 50 %. An absolute IDF floor
   moves with `n`, so the same term would be boilerplate on one rung of a
   corpus and not on the next, and the report's own vocabulary would stop
   meaning one thing.

9. **Exactly three checks carry a flag** — **unreachable share**, boilerplate
   share of postings, near-duplicate share — **and every floor is provisional
   and prints that word.** The rule a floor satisfies, pre-registered: it does
   not flag any golden rung, and it does flag a corpus that is bad in that
   bound's own dimension. **A floor that fails the rule is dropped to
   descriptive** — the number still prints, the flag does not.

9a. 🔴 **`findable share` is a DROPPED floor, and the rule is what dropped
   it.** Self-retrieval was planned as the headline check and measures almost
   nothing: **1.000 on every golden rung and 1.000 on the planted-bad corpus**,
   forty copies of one runbook. The cause is structural, not a bad threshold —
   a fingerprint is the document's own rarest terms, and a document's **path is
   part of its indexed vocabulary and unique by construction**, so anything
   with one rare term, its own file name included, retrieves itself. The number
   prints under the findability lens; the flag went to the exhaustive half.

9b. ⚠ **The boilerplate floor is the weakest of the three and says so.** Every
   golden rung sits at **0.47** — they are generated from one template — while
   this repository sits at **0.072** and planted-bad at **0.985**. A bound near
   the honest-looking 0.25 would flag all seven rungs, which decision 9 forbids,
   so the bound is **0.60** and catches only the pathological case. **That the
   golden ladder is 47 % boilerplate is a finding about the ladder**, filed with
   the run rather than smoothed over here.

10. **A flag is *attention*, never a failure. `fux inspect` exits 0 whatever it
    finds.** *"Your index has boilerplate"* is the report, not an error. It
    exits non-zero only when it cannot produce a report at all — no committed
    index — which the CLI boundary already renders.

11. **There is no one-number index score.** Refused for the same reason
    [SR-CONFIDENCE](0141_confidence.md) refuses to collapse the band: it would
    be the number everyone quotes and the only one nobody can act on.

12. **Every finding prints its lever and applies none.** The table lives in
    `src/fux/inspect/lenses.py::LEVERS` and is held equal to the one below by
    `tests/test_inspect_levers.py`, so the report can never recommend a knob
    the records do not describe.

    | finding | lever |
    |---|---|
    | boilerplate term | `[index]` stopwords, or an analyzer amendment — an index change, with its own record |
    | template family | `.fuxignore`, `archived=`, or `supersedes` on the one that is current |
    | near-duplicate pair | `.fuxignore`, `archived=`, or `supersedes` on the one that is current |
    | unfindable document | `fux enrich`, `fux correct`, or fix the source |
    | orphan | link-IDF and the graph-composed `ask` (W-161) — until then, add a link from a document that is read |
    | hub | link-IDF and the graph-composed `ask` (W-161) — until then, nothing: a hub is a fact about the corpus |
    | file-name-only document | a decoder (`fux-decoder`), or leave it in `.fux/enrich/queue.tsv` for a model to describe |
    | unreadable document | re-ingest, or `keep = true` on the url line so the bytes are retained |

13. **Every truncated list ships its full count beside it.** A capped top-20
    read as a total is how *"20 near-duplicate pairs"* comes to mean *exactly
    20* when the real number is 231 — and the truncation is invisible, because
    20 is exactly what a cap of 20 looks like. Found by checking this repo's own
    first report: orphans read `20` and are **341**.

14. **The report carries no timestamp.** A wall-clock line would make the file
    differ on every run — L3's byte-identical guarantee broken by a decoration —
    and the determinism test would then have to exclude the one line most
    likely to hide a real change underneath it. Provenance is the shard shas,
    which are a fact about the input rather than about when somebody looked.

15. **Two artifacts, both under `.fux/runtime/inspect/`**: `report.md` and
    `report.json`. `git status` is clean on a clean clone after a run.

16. **Python only, for now.** The dictionary build re-tokenises sources, which
    is an ingest-side job the Node reader has no home for
    ([SR-NODE-SEARCH](0153_node-search.md) names the derived planes it is
    deliberately a subset of). `inspect` **is** declared in Node's `CLI_VERBS`
    all the same: that table is not a verb list, it is what `.fux/output.toml`
    may legally say, and a repo whose file carries `[cli.json] inspect = true`
    must validate on both readers.

### Consequences

- **The M1 finding is now one command.** *"Report the fraction of the
  population a treatment actually touched"* was a hard-won lesson with no
  instrument; the vocabulary percentiles are that instrument, and on this repo
  they read `min 8 · p10 54 · p50 289 · p90 794 · max 10094`.

- **The report is an input to W-168, not a step in it.** Every one of the ten
  search improvements is gated on a golden question and a pre-registration;
  `inspect` says which of them this corpus would even be touched by. It does
  not, and may not, move a ranking.

- **The three floors are the debt.** They are measured on the ladder and marked
  provisional, and nothing yet re-measures them when the ladder grows a rung.
  Filed with the run that set them rather than left implicit.

- **`inspect` is slow on a large corpus and says so with a progress bar.** The
  dictionary half re-tokenises every document and the retrieval half is one
  query per sampled document. It joins `_PROGRESS_COMMANDS` for that reason:
  silence on a minute-long read reads as a hang.

### Alternatives considered

- **A flag on `fux doctor`.** Rejected by decision 1. One command answering two
  questions with two unrelated remedies produces one list a reader cannot
  triage — and `doctor`'s exit code means *this repository is broken*, which a
  corpus with boilerplate in it is not.

- **A one-number index score.** Rejected by decision 11.

- **Reading words out of the committed index.** Impossible by construction and
  that is the point: [SR-POSTINGS](0112_postings.md) decision 2 commits hashes.
  The alternative on the table was committing a term dictionary beside them,
  which trades the privacy property for a convenience and would have to be
  argued on L2's terms. Nobody has argued it.

- **Publishing the minhash estimate rather than the exact Jaccard.** Rejected:
  a 64-permutation estimate has a standard error near 0.06, so the number in the
  report would move when the permutation seeds moved — and the seeds are an
  implementation detail no reader should have to know. The estimate finds
  candidate pairs; the exact set intersection is what is printed.

- **Self-retrieval over every document by default.** Rejected on cost: one full
  query each, measured at ~0.2 s on this repo's 1 179 documents with the
  accelerator warm, which is four minutes for a diagnostic. `0` asks for it
  explicitly.

### Reference (required)

- Code: [`src/fux/inspect/`](../src/fux/inspect/) — `_scan.py` (the one pass),
  `dictionary.py` (the local hash → word join), `lenses.py` (the six and
  `LEVERS`), `checks.py` (the three floors), `__init__.py` (the report).
- The spec it was built from:
  `archive/proposals/fux-inspect.md` §2–§5b — archived 2026-09-14 once this
  record existed; named as history, never cited as authority.
  The item that built it shipped and archived on 2026-09-14 —
  [`work/IMPLEMENTATION.md`](../work/IMPLEMENTATION.md) §2026-09-14 W-169 is
  the live record of what landed and of the three things the item did not
  predict.
- The floors: [`work/regression/2026-09-14-inspect-floors/`](../work/regression/2026-09-14-inspect-floors/report.md).
- Zipf, *Human Behavior and the Principle of Least Effort*, 1949 · Heaps,
  *Information Retrieval: Computational and Theoretical Aspects*, 1978 ·
  Broder, *On the resemblance and containment of documents*, 1997 (minhash) ·
  Azzopardi, de Rijke and Balog, *Building simulated queries for known-item
  topics*, SIGIR 2007 (retrievability).

### Veto condition

**Reopen this record when any of these becomes true:**

1. **A floor flags a healthy golden rung.** Decision 9 then applies: that
   number drops to descriptive, as `findable share` already has. Checkable today —
   `fux inspect --json` over each rung and compare each `checks[].flagged`
   against the rung's own row in the floors run.
2. **`git status` is not clean after a run in a clean clone.** Decision 15's
   whole claim. `tests_e2e/test_inspect_verb.py` asserts it.
3. **The report is not byte-identical over an unchanged index.** Decision 14,
   and an L3 defect rather than a preference.
4. **`LEVERS` and decision 12's table disagree**, which
   `tests/test_inspect_levers.py` catches, or a lever names a knob no record
   describes.
5. **A lens cannot find its plant** on the planted corpus in
   `tests_e2e/`. That lens is removed from the report rather than left printing
   a number nobody can trust — the keep/remove call the item pre-registered.
6. **`inspect` gains a write.** It would then be a maintenance verb with a
   model-free promise to keep, and the boundary in decision 1 would no longer
   be the boundary.
