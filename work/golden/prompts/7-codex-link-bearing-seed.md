---
type: Prompt
title: "Prompt 7 — Codex: link-bearing seed documents, so three link features stop measuring nothing"
item: W-191
timestamp: 2026-09-16T00:00:00Z
---

# Prompt 7 — Codex: give the seed corpus links

⚠ **OPTIONAL, and on no critical path since 2026-09-20.** Arpit ruled that day
that **no feature waits on Codex**: the link-bearing documents this prompt asks
for are now carried by **set 3**, authored by Claude under
[prompt 3](3-claude-questions.md) part B
([SR-WORK-GOLDEN](../../../records/0066_WORK-golden.md) decision 14). **Nothing
is blocked on this prompt any more.**

🔴 **It is kept, and it is still worth running whenever Codex is available**, for
the reason below: links written by the party that will measure them are links
whose shape the measurer already knows. **Set 3's links are `informed`
permanently and Codex's would not be** — so running this later buys a cleaner
arm, and the two are then reported apart like any other authorship pair, never
pooled.

**Model: Codex, highest reasoning setting.** These documents decide whether three
separate measurements mean anything, and a corpus written by the session that
will measure it is a corpus whose shape that session already knows.

🔴 **Why Codex and not Claude.** Same rule as prompts 1 and 2:
[W-191 → W-204](../../open/W-204-golden-outputs-scoring-and-version-benchmark.md) **specifies and
requests**; it does not write seed content. A link-ranking feature measured on
links the measurer authored is measuring its own handwriting.

**This is an AMENDMENT to the existing seed, not a new corpus.** Nothing already
in `work/golden/seed/` is deleted, renamed or re-dated, and **no existing fact
changes** — both question sets were written against those documents and are
already released.

🔴 **It writes files and nothing else.** No questions, no answers, no key.

**Paste everything below the line into Codex, from the root of the `fux` repo.**

---

You are extending a sealed benchmark's seed corpus.

**Read:** `work/golden/README.md` sections *Feature coverage* and *Phase 4*, and
then **every file in `work/golden/seed/` including `work/golden/seed/archive/`**,
and `work/golden/seed-dates.tsv`.

🔴 **Do not read `work/golden/questions/`.** Both sets are released and this task
has nothing to do with them.

## The problem you are fixing

The corpus has **zero `ref` edges**. Every edge in all eight ladder rungs is a
`supersedes` edge, and there is **no link syntax anywhere in `seed/`** —
measured, on 2026-09-15.

Three features therefore measure nothing, and one of them already filed a
misleading zero:

| feature | what it needs |
|---|---|
| **anchor text as a ranking field** | a document findable **only** through the words *another* document used to link to it |
| **graph-composed `ask`** | enough `ref` edges that a walk from a starting document reaches somewhere |
| **graph coherence as an abstention gate** | a neighbourhood dense enough that *"the evidence hangs together"* is distinguishable from *"there is no graph here"* |

## What fux counts as a link — read this before writing one

fux extracts a `ref` edge from **an ordinary markdown inline link in the body**:

```markdown
[the escalation path](../seed/01-sop-temperature-excursion.md)
```

⚠ **Every example path in this prompt is written from THIS FILE's location**
(`work/golden/prompts/`), so the repo's own link check verifies that the file
exists. **Inside a seed document, drop the `../seed/` and write the bare
filename** — the documents sit beside each other.

- **The target is resolved as a repo path**, relative to the linking file. From
  one seed document to another, the target is the **bare filename** —
  `07-rate-card-and-surcharges.md` — because the documents are siblings. A
  target beginning `seed/` or `work/golden/seed/` is wrong from there and
  resolves to nothing.
- **A link whose target does not resolve to an ingested document is dropped
  silently.** Check every path you write against the actual filenames.
- **A `#fragment` is stripped** before resolution, so `(...md#surcharges)` is fine.
- **Reference-style links (`[text][ref]`) are NOT extracted.** Inline only.
- **Links in `.html` and `.txt` seed files do not count** — the extractor reads
  the markdown body. Put these in `.md` files.
- **The anchor text is what the linking author wrote**, and it is the whole
  point: it becomes a searchable field on the *target*.

## What to write

### A · 12 links among the EXISTING seed documents

Add inline links into the bodies of existing `.md` seed documents, pointing at
other seed documents, **as a real author would** — a sentence like *"the
escalation path is in the temperature excursion SOP"*, with *the temperature
excursion SOP* as the anchor text and `01-sop-temperature-excursion.md` as the
target.

- **Spread them**, so at least **6 distinct documents** are link targets and at
  least **6 distinct documents** are link sources.
- 🔴 **Change no fact.** Add the sentence that carries the link, or reword an
  existing sentence to carry it. Do not change a number, a name, a date, a
  decision or a heading. **Both question sets are already released against these
  documents.**
- **The `supersedes:` pairs are the natural place for several of them** — a 2026
  document referring back to the 2023 one it replaced — and that is fine, but do
  not make them all that shape.

### B · 3 NEW documents findable only by their anchor text

**This is the case the anchor-text feature exists for, and the corpus has none.**

Write **three new seed documents** whose own text does **not** contain the words
people would search for them by — and then link to each of them, from two
different existing documents, **using those words as the anchor text**.

A worked shape, which you should vary rather than copy:

- the new document is titled *"Form 27-B"* and its body is procedural, full of
  form-field names and clause numbers;
- it never uses the phrase *"damaged pallet claim"* anywhere;
- two other documents link to it with **`damaged pallet claim`** as the anchor
  text and `16-form-27b.md` as the target — written, from a seed document, as
  an ordinary inline link.

So: **the phrase reaches the document only through the link.** For each of the
three, tell me in your summary which phrase that is.

- Name them `16-…`, `17-…`, `18-…`, continuing the existing numbering.
- **They are new subjects, not new facts about old ones** — the README's rule
  that no document may state a fact about a seed entity applies to you here,
  because the released questions were written without them.
- Add a row per document to `work/golden/seed-dates.tsv`, in its existing format.

### C · One densely connected neighbourhood

Among everything above, ensure **at least one cluster of 4+ documents** that
link to each other in more than one direction — so a walk from any of them
reaches the rest. The abstention gate needs a neighbourhood that *is* coherent
in order for *"not coherent"* to mean anything.

## What NOT to do

- **No questions and no answers.** Not a draft, not a comment.
- **No link to a file that does not exist**, and no link into `ext/` or into a
  ladder rung — the seed must stand alone, because it is copied into all eight.
- **No reference-style links, no HTML anchors, no bare URLs.**
- **Do not renumber, rename, re-date or delete anything that exists.**

## What to report back

Plain text in the chat, no file:

1. **A table of every link you added**: source file, anchor text, target file.
2. **The three anchor-only phrases** from part B, one per new document.
3. **A count**: how many `ref` edges this should produce, by your own reading of
   the rules above.
4. **A confirmation** that you changed no existing fact, and that you did not
   open `work/golden/questions/`.

⚠ **Your count in (3) is checked against the engine's.** After this lands, a
Claude session re-ingests and counts the actual `ref` edges per rung. If the two
disagree, the difference is the finding — links that look right and resolve to
nothing are exactly the failure this corpus already has.
