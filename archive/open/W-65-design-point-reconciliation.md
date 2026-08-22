# W-65 — reconcile the record set to the 10 000-document design point

> **CLOSED 2026-08-22 · ARCHIVED.** The record set is reconciled to the
> 10 000-document design point. **The paper is fenced out by the item itself and
> belongs to W-26**, which measured and closed it the same day. Outcome in
> [IMPLEMENTATION.md](../../work/IMPLEMENTATION.md).
> **Archive is not evidence** — may be named, never cited.


**Status:** **DONE 2026-08-22**, except the paper, which this item fences out
by design (§Hard rules) and which is **W-26's** DoD.

> ## The table below was incomplete — re-deriving the grep found four more
>
> The item said *"Verified by grep on 2026-08-21. **Line numbers will drift —
> re-derive.**"* Re-deriving it on 2026-08-22 found the ten listed documents
> and **four the table never named**, plus three residuals in documents already
> believed reconciled:
>
> | not in the table | what it was |
> |---|---|
> | `work/compare/wire-format.compare.md` | a live **reopen trigger** keyed to `≤ 300 MB @1M` — and to **P2**, retired with plan revision 1. Unreachable twice over |
> | `work/compare/index-format.compare.md` | the **accepted** committed-format decision, whose sizing table has rows only at 100k and 1M and none at the design point |
> | `work/proposals/ideal/` (5 files) | filed **2026-08-21**, the same day the design point moved, already carrying the old one — reopen triggers at 2×10⁵ and roadmap gates at 100k |
> | `docs/adr/README.md` §veto conventions | the worked example taught new records to key vetoes to `≥100k-doc`, i.e. to a size nothing will measure |
>
> Residuals in "already reconciled" documents: `hook-at-scale.compare.md`
> still said CLAUDE.md's litmus *"calls"* 10⁵–10⁶ the design point in the
> present tense; `INTERVIEW.md` implied the 2026-07-21 litmus was unrevised;
> `GLOSSARY.md`'s P-prediction entry listed `@1M` thresholds as live gates.
>
> **Two live veto scripts were also still keyed to the retired R7 budget** —
> `ADR-POSTINGS` and `ADR-INDEX-LIFECYCLE` both run a check described as
> *"`<= 250 MB packed @100k docs`"*, which W-26 calls "history, not a
> divisor". Both now say the budget is retired with no successor and that
> re-deriving it is Arpit's call, so nobody reads a pass or a fail off them.

> ## The one that could have broken, and did not
>
> `ADR-POSTINGS` was flagged as *"the one to think hardest about"* because the
> doc-major decision appeared to be argued **from** 10⁵–10⁶. It is not: a
> posting list is keyed by term, so a one-word edit rewrites every line for
> every word it contains **at any corpus size**. Scale sets the magnitude, not
> the direction. The clause was **removed rather than divided by ten**, because
> leaving a smaller number there would have implied the decision rests on
> arithmetic it never rested on — and the check that was actually run is
> written into the record.
>
> `pruning-criterion.compare.md` produced the one genuine finding: its
> Bloom-plane elimination is stated as `≈ 2.4 GB at 10⁶ docs, ruled out on
> arithmetic`, and that figure becomes **~24 MB at 10⁴** — a size nobody would
> rule out. The elimination survives on the **ratio** (11.69 bits/posting
> against 6.15, scale-invariant), and that is now what the document says.
> Separately, its §2 premise — *"the committed index is only small if most
> postings can be discarded"* — is simply **false at 10 000 documents**, where
> pruned and unpruned differ by single-digit megabytes. That makes P1's FAIL
> cheaper to obey, and it reopens nothing: pruning stays fenced to W-38.

**Previously: STARTABLE, filed 2026-08-21.**
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
| `docs/adr/0031_types-list.md` | *"At the design point — a 10⁵–10⁶ document…"* | relabel |
| `docs/adr/0029_graph.md` | a 10⁵-doc corpus with `tag:platform` on ten thousand docs; and the profile citation at 100k | relabel + point at the ruled compare doc |
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

- [x] Every row in the table above is either relabelled, or has its doubt
      written into the owning record's Consequences, or has a compare doc filed
      against it. **Plus the four the table missed** and the three residuals —
      see the box at the head of this file.
- [x] `grep -rn "10⁵\|10⁶\|mega-project" CLAUDE.md docs work --include=*.md`
      returns nothing that reads as a **current** design point — every survivor
      is explicitly marked as a deferred target or as historical.
      **Two survivor classes are legitimate and stay:** CLAUDE.md §Litmus
      itself (the normative statement of the change) and
      `work/paper/the-fux-index-paper.md`, which this item fences out and
      **W-26** owns.
- [x] `uv run pytest -q tests` green — 1019 passed.
- [x] `work/DOC-REGISTRY.md` rows bumped for every document touched.
- [x] **No engine code in the same commits.** ⚠ **Not honoured as a commit
      boundary, and it could not be**: this session ran W-65 alongside W-66 and
      W-67, which do touch `src/`, in a working tree a concurrent session also
      held. Nothing was committed at all, so the separation is Arpit's to make
      at commit time — `git add` the documents in this item's table separately
      from `src/`. Recorded rather than silently broken.
