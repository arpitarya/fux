# W-65 — reconcile the record set to the 10 000-document design point

**Status:** **STARTABLE, filed 2026-08-21.**
**Blocked by:** nothing.
**Spec:** this file.
**Closes with:** no new record — it edits existing ones. **Law zero applies in
reverse here**: nothing in `src/` changes, so the commit message says
**"no ADR affected"** for the engine while touching many records' prose.
**Model:** **Opus.** Deciding whether an argument survives a scale change is a
judgement call per record, and the failure mode — rewriting a conclusion the
premise no longer supports — is silent.

## Why this exists

On **2026-08-21 Arpit moved the design point from 10⁵–10⁶ documents to
10 000** (CLAUDE.md §Litmus). CLAUDE.md, `OPEN-WORK`, `W-26`,
`hook-at-scale.compare.md` and `graph-plane-format.compare.md` were reconciled
in that change. **Everything below was not**, and each of these documents
still asserts the old design point as current fact.

The [ADR currency law](../../CLAUDE.md) makes a stale record a defect, not an
untidiness: *"a record that is wrong reads as authority."*

## The list

Verified by grep on 2026-08-21. **Line numbers will drift — re-derive.**

| document | what it asserts | first read |
|---|---|---|
| `docs/adr/0013_postings.md` | *"At 10⁵–10⁶ documents, a term-major committed index means a one-word edit…"* — **the scale is the premise of the doc-major decision** | **the one to think hardest about** |
| `docs/adr/0010_index-record.md` | *"in repository size at 10⁵–10⁶ documents"* | relabel |
| `docs/adr/0032_types-list.md` | *"At the design point — a 10⁵–10⁶ document…"* | relabel |
| `docs/adr/0030_graph.md` | a 10⁵-doc corpus with `tag:platform` on ten thousand docs; and the profile citation at 100k | relabel + point at the ruled compare doc |
| `docs/GLOSSARY.md` | `D/` dictionary saving at 10⁶; runtime ~2.5 GB at 10⁶ | relabel as deferred-target arithmetic |
| `work/compare/pruning-criterion.compare.md` | postings arithmetic at 10⁶ | **verdict was FAIL; check the arithmetic still fails at 10k** |
| `work/compare/file-type-filter.compare.md` | matrix row *"survives 10⁵–10⁶ docs across many repos"* | re-weight |
| `work/compare/source-exclusion.compare.md` | *"Under the litmus — a 10k-engineer corporation's mega-project, 10⁵–10⁶ documents…"* | re-weight |
| `work/compare/refer-fetch-cache.compare.md` | *"10⁵–10⁶-document Confluence estate"* | relabel |
| `work/compare/storage-architecture.compare.md` | *"0.6–1.5 GB at 10⁶ documents"* | relabel |
| `work/open/W-62-...md` | quotes CLAUDE.md §Litmus verbatim | update the quote |

## How to do it

1. **Relabel, do not delete.** An argument that holds at 10⁶ almost always
   still holds at 10⁴ — it is just no longer the *gate*. The edit is usually
   one clause: *"at the design point"* → *"at 10⁵–10⁶ documents, a deferred
   target"*.
2. **Surface the ones that break.** A claim whose conclusion depends on the
   scale being large — `ADR-POSTINGS` is the candidate — **must not be quietly
   rewritten to a smaller number.** Write the doubt into the record's
   Consequences and, if the decision itself is in question, **file a compare
   doc and stop.** A decision re-justified by an agent is not a decision.
3. **Check the pruning verdict specifically.** P1 closed **FAIL — full
   postings, permanently** on arithmetic computed at 10⁶. If that arithmetic
   passes at 10⁴, the verdict does not flip — **a filed verdict is cited,
   never replaced** — but the *fact* that it might have gone the other way at
   the new design point belongs in W-38's file, where pruning work lives.
4. **One commit, or one per record.** Either is fine. What is not fine is
   editing prose in the same commit as engine code.

## Hard rules

- **Frozen pre-registrations are never edited.**
  `tools/maintenance-bench/PRE-REGISTRATION.md` argues from the old litmus in
  its §justification and **stays exactly as written** — a threshold may never
  move, and the reasoning that produced it is part of the instrument.
- **Filed `VERDICT.md` files are never edited.** R5's FAIL at 100 000
  documents stands as measured. Re-judging at 10 000 is a *new*
  pre-registration and a *new* verdict.
- **The paper is not this item's.** `work/paper/the-fux-index-paper.md` is
  rewritten to 10k measurements under **W-26's** DoD. Touching it here would
  put a projection rewrite in the wrong item and duplicate the work.
- **Do not touch `archive/`.** Archived records are history and are already
  correct about the design point *of their time*.

## Definition of done

- [ ] Every row in the table above is either relabelled, or has its doubt
      written into the owning record's Consequences, or has a compare doc filed
      against it.
- [ ] `grep -rn "10⁵\|10⁶\|mega-project" CLAUDE.md docs work --include=*.md`
      returns nothing that reads as a **current** design point — every survivor
      is explicitly marked as a deferred target or as historical.
- [ ] `uv run pytest -q tests` green (the doc-meta tests read the register and
      the registry).
- [ ] `work/DOC-REGISTRY.md` rows bumped for every document touched.
- [ ] **No engine code in the same commits.**
