---
type: OpenItem
id: W-110
title: "W-110 — fux-enrich writes questions, and --check refuses the ones the index cannot find"
description: "Blind enrichment measured +1 / −1 because the skill asks for context prose and the prose carried currency words into superseded records. Re-aim the skill at doc2query (5–10 questions per document, one per line; currency in frontmatter, never prose) and add doc2query−−'s filter using fux's own index as the relevance model: a question that does not place its document in the top-k is refused by --check."
status: open
lane: agent
timestamp: 2026-09-04T00:00:00Z
---

# W-110 — doc2query enrichment

**Model: Opus.** The skill text is the product and no test can grade prose;
the filter touches what gets committed and indexed.

## The spec this implements

[`../proposals/search-v3.md`](../proposals/search-v3.md) §4 and §8 (W-110).
Literature: docTTTTTquery (Nogueira & Lin 2019), Doc2Query−− (arXiv
2301.03266).

## Definition of done

- [ ] `src/fux/templates/agents/ENRICH-SKILL.md` (and every vendored copy
      `fux setup` writes): body = questions a searcher would type, one per
      line, 5–10; no summary; supersession as `supersedes:` /
      `superseded_by:` frontmatter keys, never a sentence; the PII rule
      unchanged.
- [ ] `enrich.py`: a body line that parses as a question is checked by
      **self-retrieval** — analyzed, hashed, ranked with `rank()` over the
      committed index; refused if its own document is not in the top-*k*
      (`k` stated in ADR-ENRICH, default 3). Reported as `refused: … — does
      not retrieve its document`, same shape as the PII refusal. Prose bodies
      written under the old skill stay valid.
- [ ] `ingest/run.py`: `superseded_by:` in an enrichment's frontmatter
      resolves onto the record's `superseded` flag exactly as a document's
      own `supersedes:` does (ADR-ENRICH + ADR-INGEST amended) — the
      *declared* path the second-author analysis named and nobody built.
- [ ] Gate filed: the `none` / `placebo` / `real` arms from
      `2026-08-28-placebo-and-seal` re-graded on `recall@k`; **blind**
      author; per-query rows; net ≥ 6.
- [ ] ADR-ENRICH, ADR-INGEST amended; CHANGELOG; `IMPLEMENTATION.md`; this
      file to `archive/open/`.

## Blockers

- `arpit`: ratification; `k` for the filter.

## Hazards

- 🔴 The filter is deterministic but **corpus-dependent**: a question can
  pass on one clone and be refused after an unrelated ingest moves `df`.
  `--check` reports; it never rewrites; the file stays committed. Say so in
  the record.
- 🔴 A question that mentions the document's own title trivially passes —
  the skill must forbid title-echo, and the filter should ignore `title`
  field matches (decision for ADR-ENRICH).
- Enrichment vocabulary is inside the PII boundary (W-102); unchanged.

## Out of scope

Running enrichment. Any change to `.fux/index/` shape. Deleting existing
enrichment files.
