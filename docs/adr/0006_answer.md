---
type: ADR
name: ADR-ANSWER
title: ADR-ANSWER (0006) — the answer verb
description: The single best answer the index can give — a fetched, re-scored passage with a fresh sha, or the index's own structure when the source is unreachable. No model, ever, on this path.
status: accepted
date: 2026-08-18
feature: "`fux answer` — one answer, its footing stated, and the report of what changed since the question was last asked"
owns: []
laws: [L1, L2, L3]
timestamp: 2026-08-21T00:00:00Z
---

# ADR-ANSWER — the `answer` verb

## §1 — For humans

`answer` returns one thing instead of a list: by default, the passages that
best answer the question, fetched fresh from **the top three ranked documents'**
sources and re-scored against the question — verbatim, each with a citation
carrying a `sha` computed from those exact bytes.

**It reads three documents and returns one answer**, and those are different
sentences. The passage contest is cross-document, so the winning passage can
come from the second- or third-ranked document; on the 43 graded playground
queries it does, on 18 of them.
`--no-refer` (or the source being unreachable) falls back to the winning
record's own extracted structure — title, heading-derived phrases, citation.

**No model is involved and none ever will be on this path** — refer's passages
are fetched bytes, never a rewrite of them. There were always two dishonest
options: generate a fluent sentence from what little the index holds —
fabrication with a citation attached — or refuse to ship the verb at all.
Neither was taken.

**Diagram — Mermaid and its ASCII twin. Update both, always, together.**

```mermaid
flowchart TD
    Q["fux answer 'question'"] --> R["the same run_query as ask,<br/>top = ANSWER_TOP (3, fixed)"]
    R --> H{"a hit?"}
    H -->|no| N["No confident matches.<br/>exit 0, source: index"]
    H -->|yes| W["the top 3 records"]
    W --> NR{"--no-refer?"}
    NR -->|yes| IDX["index-only:<br/>title + phrases + citation<br/>(rank 1 only)"]
    NR -->|no, default| FET["ONE refer() call over all 3<br/>(file: local, url: the line's own fetcher)"]
    FET --> OK{"any document<br/>produced a passage?"}
    OK -->|yes| REF["refer: cross-document passage contest<br/>passages + fresh sha + verdict, per document"]
    OK -->|no — every one unreachable,<br/>no fetcher, deleted| IDX
    IDX --> SI["source: index"]
    REF --> SR["source: refer"]
```

<details>
<summary><b>ASCII twin</b> — the same diagram, for terminals, diffs, and any reader without a Mermaid renderer</summary>

```text
   fux answer "question"
          |
          v
   the same run_query as ask,  top = ANSWER_TOP (3, fixed; still no --top flag)
          |
          +-- a hit? --no--> "No confident matches."   exit 0, source: index
          |
         yes
          v
   the top 3 records
          |
          +-- --no-refer? --yes--------------------------+
          |                                               |
          no (default)                                    v
          |                                    index-only: title + phrases
          v                                     + citation   (rank 1 only,
   ONE refer() call over all three               source: index)
   file: -> local checkout (always)                          ^
   url:  -> the fetcher THAT LINE names                      |
          |                                                  |
          +-- any document produced a passage? --no (every  -+
          |                                    one unreachable / no fetcher /
         yes                                   deleted)
          v
   cross-document passage contest
   passages + a fresh sha + a per-document freshness verdict  (source: refer)
```

</details>

### Examples

```console
$ fux answer "why did pruning fail"
---
title: Why pruning failed
---

# Why pruning failed

The gate measured static pruning twice and it did not preserve candidate recall.

  -- docs/pruning.md:L1-L6 (sha b0093c74baa0, current)
```

`"source"` is the machine-readable form of that trailing line:

```console
$ fux answer "why did pruning fail" --json | tail -1
  "source": "refer"

$ fux answer "why did pruning fail" --no-refer --json | tail -1
  "source": "index"
```

---

## §2 — For agents

### Context

The committed index holds statistics, not content — documents stay in the
systems that own them. So an `answer` verb has nothing cached to summarise, and
the pressure is to fill that gap with something that *reads* like an answer.
Everything the index holds — title, heading phrases, score — can be arranged
into a fluent sentence. **With a citation attached, that sentence would be
indistinguishable from a real one.** It is the exact failure this engine exists
to refuse.

What replaces it is the refer plane: fetch the winning document from its
source, chunk it, re-score the chunks against the question, and cite the sha of
the bytes that were actually read.

### Decision

**1. `answer` returns what it could actually get**: a fetched, re-scored
passage when the source was reachable (refer, the **default**), or the index's
own extracted structure — title, heading-derived `phrases`, citation — when it
was not, or when the caller said `--no-refer`. Nothing is synthesised on either
path.

**2. Every text answer states its footing.** The refer path's trailing line
names the citation's locator, its fresh `sha` and its freshness verdict
(`current` / `stale` / `unverified` / `cached`); the index-only path names *why*
it fell back — `--no-refer was passed`, or the source could not be
reached/verified — rather than stating a blanket ceiling that is not true on
the common path.

**3. No model on this path, now or later.** Not to phrase, not to summarise,
not once — refer's passages are verbatim spans of fetched bytes
([ADR-REFER](0030_refer-plane.md)), never a rewrite of them.

**4. One ANSWER is forced; top-1 is not.** There is no `--top`, and a caller
wanting alternatives still wants [`ask`](0004_ask.md) — but since W-108 the
verb **refers `ANSWER_TOP` = 3 documents** and returns the best passages across
them. **Refer is wired into `answer` only** — `ask`/`find` return the
committed-index ranking unchanged.

⚠ **This sentence read *"Top-1 is forced"* until 2026-09-05 and it was
load-bearing for the wrong thing.** *One answer* is a promise about the
surface; *top-1* was an implementation width, and conflating them capped the
verb at `recall@1` — `0.4341` mean recall against `0.8256` at three, measured
on the 43 graded queries
([the run](../../work/regression/2026-09-05-answer-top3/report.md)). The
promise is kept; the width was never part of it.
Fetching and re-scoring *every* ranked result is a materially bigger change —
cost scales with `--top`, and it would change what "ranked" means for every
result rather than just the first — and is a distinct, undecided scope.

**5. It is the same ranking as `ask`**, truncated to three — a projection, never
a second strategy. Refer never re-ranks *which* document answers, only how that
one document's answer is produced.

**6. Phrases are read from the winning record's shard alone**, not from a
corpus pass. One document's answer costs one shard read. (Index-only path only
— the refer path has no `phrases`, it has fetched passages.)

**7. No confident match prints `No confident matches.` and exits 0**; `--json`
emits `{"answer": null, "citation": null, "source": "index"}`. **`"source"` is
present on every branch**, because it is the key callers switch on — an absent
key is a trap, not a signal. It carries two live values: `"refer"` (fetched and
re-scored) and `"index"` (fallback, or nothing to refer to).

**8. Refer is opt-out, not opt-in.** `--no-refer` keeps the index-only path.
This follows [ADR-REFER](0030_refer-plane.md)'s own reasoning: a `file:`
citation costs nothing to fetch (the local checkout, always), and a `url:`
citation exists in the corpus only because the user already configured
`[sources.url]` with a real address — the network dependency was created by
that configuration choice, not invented by `answer` deciding to fetch.

**9. The locator is a line range, not an ordinal.** `docs/pruning.md:L1-L6`,
because an agent acts on a citation by opening a file at a line and an ordinal
forces a second call to work out which lines those were. **The ordinal is not
lost** — it survives as `passage.ordinal` and in the `--json` and MCP payloads,
because it is stable across a reflow that moves every line number.

**10. `answer` reports whether anything changed since the same question was
last asked.** The comparison that needs — *did the cited bytes move?* — is
already performed on every call by the refer plane; what is remembered is only
the previous answer's `(loc, sha)` pairs, in gitignored
`.fux/runtime/last-cited.json`.

⚠ **It is a report, not a memo. No answer is stored and nothing is replayed.**
Every answer is recomputed on freshly fetched bytes. **A `--memo` flag was
proposed and refused**: this verb is model-free and deterministic and ARC is
keyed `(loc, sha)`, so identical bytes give an identical answer **by
construction** — a memo would cache the output of a pure function whose inputs
were just downloaded. Its sharpest hazard was that a memo validated by a TTL hit
would replay an answer on bytes nobody confirmed **while reporting `current`**.
Storing only `(loc, sha)` cannot do that, because there is no stored answer to
serve.

**It needs no fifth freshness label.** [ADR-REFER](0030_refer-plane.md)
decision 6's four labels are **per-citation** facts about one fetch; this is a
**per-answer** statement about two runs. Different object, different place.

⚠ **The line goes to stderr in BOTH text and JSON mode**, so this record's
documented stdout — including the `source` key callers switch on — is
**byte-identical with the feature on or off**. Promoting it to a JSON field
would be additive but would move a documented surface, so it is a fork rather
than a default.

**11. `answer` refers `ANSWER_TOP` = 3 documents, in ONE `refer()` call.**
Not three calls. `refer/_rescore.py` computes passage `df` across everything
fetched, so a single call is a **fair cross-document contest** and three calls
would score each document's passages only against its own siblings — a
different, and wrong, question.

**Three, and not a tunable.** The uplift is bounded by the `recall@1 ->
recall@3` gap, and every extra candidate is a real fetch against someone's
source system. A `[refer]` key here would be a new default nobody has measured,
on a verb whose defaults are already an open question.

⚠ **The winning document is no longer necessarily `ask`'s first result** — on
18 of the 43 graded queries it is not. That is the mechanism working, and it is
the thing to know before reading a citation: `ask` ranks documents, `answer`
ranks *passages*, and since W-108 those two orderings are allowed to disagree.

**12. Every passage names its own document, and the text surface prints a
locator per passage.** `answer.passages[]` carries `id`, `loc` and `sha`
alongside `heading`, `text` and `score`; `citation` is unchanged and still names
the **winning passage's** document.

⚠ **The text surface was already wrong before three documents made it obvious.**
Every passage printed above a single trailing `-- <locator>` line, which named
the *first* passage's line range whatever the second passage was. With passages
from three documents it would have named the wrong file — in the one product
whose promise is that a citation is checkable. Additive keys only: nothing was
removed or repurposed ([ADR-ASK](0004_ask.md) decision 11's rule).

**13. The byte budget is unchanged; the bytes SPENT went up, and that is the
price.** `[refer] budget` still bounds the whole rendered answer and is never
exceeded. But one document left most of it unused and three do not: mean
assembled bytes went **2 517 -> 6 467** over the 43 graded queries, and every
query rose.

⚠ **W-108's own hazard note asked for *"assembled bytes never exceed today's
for the same query"*, and that is false on 43 of 43 — by design, not by
accident.** It conflated the *bound* with the *spend*. The bound is the
invariant and it holds
(`tests/query/test_refer_answer.py::test_the_assembled_answer_never_exceeds_the_budget`);
the spend is a cost, and it is reported rather than asserted away. A caller who
wants the old cost sets `[refer] budget` to what it used to spend.

### The surface

| flag | effect |
|---|---|
| `--json` | machine-readable; `{answer, citation, source}` |
| `--fast` / `--scan` | as on `ask`; the path can never change the answer |
| `--no-refer` | skip the refer plane; answer from the index's own structure |
| `--no-tune` | ignore `.fux/tune.toml` |

No `--top` and no `--explain`. The verb returns one answer; **how many
documents it reads to build one is `ANSWER_TOP` = 3 and is not a flag**
(decision 11).

### What it looks like

Verbatim, captured against the fixture.

```console
$ fux answer "why did pruning fail"
---
title: Why pruning failed
---

# Why pruning failed

The gate measured static pruning twice and it did not preserve candidate recall.

  -- docs/pruning.md:L1-L6 (sha b0093c74baa0, current)
```

```console
$ fux answer "why did pruning fail" --json
{
  "answer": {
    "passages": [
      {
        "heading": "",
        "text": "---\ntitle: Why pruning failed\n---\n\n# Why pruning failed\n\nThe gate measured static pruning twice and it did not preserve candidate recall.",
        "score": 1.1353167502114923
      }
    ]
  },
  "citation": {
    "id": "file:docs/pruning.md",
    "loc": "docs/pruning.md:L1-L6",
    "sha": "b0093c74baa0bcae4a3d7e26d5ce1a074a11578b",
    "freshness": "current"
  },
  "source": "refer"
}
```

```console
$ fux answer "why did pruning fail" --no-refer
Why pruning failed
  - Why pruning failed

  -- docs/pruning.md

(from the index's own structure — --no-refer was passed)
```

**No match — refer has nothing to refer to:**

```console
$ fux answer "zzz nonexistent term"
No confident matches.
# exit 0

$ fux answer "zzz nonexistent term" --json
{
  "answer": null,
  "citation": null,
  "source": "index"
}
# exit 0
```

⚠ **`answer` accepts `--expand` and refuses `-q` (W-109, 2026-09-05).**
Expanding a question's vocabulary produces one answer to one question, which is
decision 4; fusing two phrasings produces an answer to a set, which is not.
[ADR-EXPAND](0054_expand.md) decision 12 records the split, and `--expand` is
recorded verbatim in the receipt so `fux verify --rerun` replays it rather than
re-running a different query and reporting `drifted`.

### Consequences

- **The passage carries the document's frontmatter block.** `refer/_chunk.py`
  chunks the fetched bytes as fetched — it does not strip the YAML frontmatter
  the way `ingest/extract.py`'s title/phrase extraction does. This is
  consistent with the refer plane's "it cannot invent" rule — the passage is a
  genuine verbatim span, frontmatter included — but it is a real readability
  cost on a document that opens with one, recorded rather than smoothed over.
  Stripping it is `chunk.py`'s call, not this record's.
- **A caller can detect which path answered programmatically** via `"source"`,
  without parsing prose.
- **`answer` is not a summariser and will never become one.** A future request
  for "just make it write a sentence" is refused by this record, not by taste.
- **`--json` is validated against `query/output.schema.json` before it is
  printed** ([ADR-ASK](0004_ask.md) decision 11), so a key cannot be quietly
  renamed out from under a consumer.
- 🔴 **`--band` reports a real `separation` on this verb for the first time,
  and it demotes.** At `top = 1` there was no runner-up, so
  `confidence.signals` returned `separation: 1.0` and `support: 1` on **every
  query `answer` has ever answered** — an artefact of the retrieval width, not
  a claim about the ranking. At three it is computed, and on the 43 graded
  queries **8 answers moved `grounded` -> `weak`**. No floor moved, no
  abstention was implemented and nothing gates on the band
  ([ADR-CONFIDENCE](0045_confidence.md) decision 14); what changed is that the
  number is now true.
- **`fux verify --rerun` retrieves `ANSWER_TOP` too.** A rerun that retrieved a
  different number of candidates than the answer did is not a rerun, and would
  have reported `drifted` on every multi-document answer while being right
  about nothing.

### Alternatives considered

- **Generate a fluent sentence from title + phrases.** Rejected: fabrication
  with a citation attached. The failure is invisible to the reader, which is
  what makes it the worst available option.
- **Return the top 3 and let the caller choose.** Rejected: that is `ask`. A
  verb named `answer` that returns three answers has no meaning.
- **Emit the disclaimer only in `--json`.** Rejected backwards — the human
  reader is the one who can be misled by a confident-looking answer; the machine
  has `"source"`.
- **Extractive summarisation over the `phrases` list.** Rejected: still
  synthesis, and still no access to the sentence a reader wants. The honest fix
  is the refer plane, not cleverer arrangement of what little is held.
- **`answer --memo`.** Rejected under decision 10, on the grounds that it would
  cache a pure function of bytes just downloaded — and could report `current`
  about bytes nobody confirmed.
- **An ordinal locator (`path#p3`).** Rejected under decision 9: an agent opens
  a file at a line, and the ordinal made every citation cost a second call.

### Reference (required)

- The verb — [`src/fux/query/__init__.py`](../../src/fux/query/__init__.py)
  (`cmd_answer`, `_phrases_for`, `_print_refer_answer`, `_print_index_answer`);
  its docstring is the normative statement of the no-model rule on this path.
- The refer wiring —
  [`src/fux/query/refer_answer.py`](../../src/fux/query/refer_answer.py)
  (`answer_via_refer`, the per-URL fetcher resolution that mirrors
  `ingest/urlsrc.py`'s own); the plane it calls —
  [ADR-REFER](0030_refer-plane.md).
- The ranking it projects — [ADR-ASK](0004_ask.md).
- Captured behaviour, both modes and the empty case —
  [`work/regression/2026-08-18-query-verbs/`](../../work/regression/2026-08-18-query-verbs/report.md).
- The e2e proof of the refer path, including the sha-changes-on-edit case and
  the multi-document citation surface —
  [`tests_e2e/test_verbs.py`](../../tests_e2e/test_verbs.py).
- **The measured basis for decisions 11-13** — `answer` over the 43 graded
  playground queries, before and after, per-query rows:
  [`work/regression/2026-09-05-answer-top3/`](../../work/regression/2026-09-05-answer-top3/report.md).
  `classification: informed`; **nothing is claimed at 10 000 documents.**
- The recall ceiling this removes, measured first —
  [`work/regression/2026-08-28-first-recall/`](../../work/regression/2026-08-28-first-recall/report.md).
- Why a confident wrong answer is the expensive failure — Ji et al., *Survey of
  Hallucination in Natural Language Generation* (2022):
  https://arxiv.org/abs/2202.03629

### Veto condition

**Reopen this decision if:** any synthesis appears on either path (refer's
passages must stay verbatim spans, never a rewrite); `--no-refer` is ever made
the default, silently reverting the common case without a decision recorded for
it; `ask`/`find` gain the same fetch-and-re-score wiring without their own
record entry (decision 4 scopes this record to `answer` alone, on purpose);
`"source"` stops being present on every `--json` branch; **`ANSWER_TOP` becomes
a flag or a `.fux/` key** (decision 11 refuses a knob, and a knob is how the
fetch count becomes a per-repo surprise against someone else's source system);
or **a passage stops naming the document it came from** (decision 12 — the
moment `answer.passages[]` loses `id`/`loc`/`sha`, a multi-document answer is
mis-attributing again).

**How to check it:**

```bash
# 1. no model, and no synthesis, on this path
grep -rnE 'summar|generate|llm|model' src/fux/query/__init__.py src/fux/query/refer_answer.py
# expect: no output beyond the phrase "no model is involved" in a docstring

# 2. --no-refer is opt-out, not the default
fux answer "any query" --json | grep '"source"'
# expect "refer" on a reachable corpus; "index" only with --no-refer, on a
# miss, or when the source could not be reached/verified

# 3. ask/find are untouched
grep -n 'refer_answer\|answer_via_refer' src/fux/query/__init__.py
# expect matches only inside cmd_answer / _answer_via_refer — never in
# cmd_ask or cmd_find

# 4. the fetch width is a constant, not a knob (decision 11)
grep -rn 'ANSWER_TOP' src/fux/
# expect: the definition in query/__init__.py and its uses in cmd_answer and
# cmd_verify's rerun -- and NOTHING under tune.py, config.py or cli.py

# 5. every passage still names its own document (decision 12)
fux answer "any query" --json | python -c 'import json,sys; ps=(json.load(sys.stdin)["answer"] or {}).get("passages",[]); print(all({"id","loc","sha"} <= set(p) for p in ps))'
# expect: True
```

---

## References

*Every source this record cites, gathered in one place. §2's **Reference
(required)** names the grounding; this is the complete list. An archived
document is never listed here — the body may name one, but archive is not
evidence.*

**Records** — [ADR-LAWS](0001_laws.md) · [ADR-ASK](0004_ask.md) ·
[ADR-REFER](0030_refer-plane.md)

**Code**

- [`src/fux/query/__init__.py`](../../src/fux/query/__init__.py)
- [`src/fux/query/refer_answer.py`](../../src/fux/query/refer_answer.py)
- [`tests_e2e/test_verbs.py`](../../tests_e2e/test_verbs.py)

**Measured evidence**

- [`work/regression/2026-08-18-query-verbs/report.md`](../../work/regression/2026-08-18-query-verbs/report.md)

**Papers and specifications**

- Ji et al., *Survey of Hallucination in Natural Language Generation* (2022) —
  why a confident wrong answer is the expensive failure
  <https://arxiv.org/abs/2202.03629>
