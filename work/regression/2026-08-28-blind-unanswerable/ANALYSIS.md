---
type: Analysis
run: 2026-08-28-blind-unanswerable
date: 2026-08-28
---

# What to do about it

The [report](report.md) has the two findings. This is the diagnosis turned into
specific work, with what is **not** yet known stated as unresolved.

## Finding 1 — 0 of 20 abstentions

### Diagnosed cause (confident)

`answerable` is computed from **corpus-wide** `coverage` and `missing`: does the
query's idf mass exist *somewhere* in the index. A near-miss question — one
built from the corpus's own vocabulary asking for a fact the corpus omits —
satisfies that test by construction. **u001 is the cleanest possible case:** the
corpus contains the phrase *"four regions"*, so every content term of *"what are
the names of all four Calder Group regions"* is present; the names are not.

This is **not a new mechanism**. ADR-CONFIDENCE already carries it as a named,
untaken decision, found by the decoy control at 1-of-15 on 2026-08-27. What is
new is the magnitude when the set is *designed* to sit close to the corpus:
**1-of-15 becomes 20-of-20.**

### Unresolved — stated as unresolved

- 🔴 **Whether `doc_coverage` gating would fix it is NOT established here.** Its
  median on this set is `0.468`, which *looks* separable, but the same field was
  measured on 2026-08-28 and gating it at `1.0` turned **19 of 50 correct
  answers `partial`**. A floor chosen from these 20 numbers would be fitted to
  the set that exposed the problem. **Do not pick one from this run.**
- **Whether any single scalar can carry this** is open. The failure is
  *"the words are here, the fact is not"*, which is a claim about the top
  document's content, not about score geometry.

### Proposed work — none of it a threshold change

1. **Keep this set as a standing regression input.** It is the only
   purpose-built abstention test fux has, and it currently scores 0.
2. **Any future R10 measurement should report against this set as a second
   slice**, beside the goldens — a floor tuned only on answerable queries has
   never seen the case that matters.
3. **Do not raise `separation_floor` in response to this.** 17 of 20 sit above
   it with a median of `0.448`; a floor high enough to catch them would gut the
   answerable set. It is the wrong instrument.

## Finding 2 — 25 of 50 goldens have more than one relevant document

### Diagnosed cause (confident)

`expect`/`doc` was authored as a **rank contract** — *"this document must come
back at rank ≤ n"* — and was later read as a **relevance set** — *"this is the
document that answers it."* Those are different claims, and nothing in the
schema ever distinguished them. `relevance_audit.py` could only ever count
fields, and said so.

### Consequence, and it is immediate

**`recall@k` cannot be computed from the current goldens**, and the
2026-08-28 inference that it degenerates to `hit@k` is **withdrawn** — it was
sound about the file's shape and wrong about the corpus.

⚠ **This does not invalidate any past `hit@k` number.** `hit@k` asks *"did the
asserted document come back"*, which is exactly what those runs measured and
reported. Nothing filed needs re-labelling. What changes is that
**`hit@k` may not be called `recall@k`**, and W-87 P2's headline metric is not
computable from what exists.

### Proposed work

1. **A second blind annotator on the same 50 questions.** One reader is one
   opinion; agreement between two independent blind readers is what would make
   the multi-document judgment usable rather than merely credible. The three
   low-confidence rows (`q032`, `q046`, `q050`) are the priority.
2. **Then, and only then, a schema decision** — whether `expect` grows into a
   list, and whether the rank contract and the relevance set become two fields
   rather than one overloaded one. **That is an ADR, not a script change**, and
   it belongs to whoever owns the golden format.
3. **Until 1 and 2 land, keep reporting `hit@k` under its own name.**

## Reproduce

Both commands are in the [report](report.md). The annotation and the
ground-truth ruling are static files under `evidence/` — re-deriving them means
running a *new* blind session, which is a new run with its own directory, never
an edit to this one.
