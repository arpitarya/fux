---
type: OpenItem
id: W-77
title: "W-77 — the records the freshness check could not protect, and four rulings owed"
description: "A full ADR audit on 2026-08-24 found sixteen records describing a schema, a scoring model and a derived plane that W-76 replaced. Sixteen were amended the same day. What is left needs a human: four rulings, one register-wide numbering defect, and a governance gap the check itself cannot close."
status: open
lane: arpit
timestamp: 2026-08-24T00:00:00Z
---

# W-77 — record reconciliation after W-76

## Why this exists — the governance gap, stated first

`tests/test_adr_freshness.py` requires a commit touching an ADR-owned component
to touch **that component's owning record**. It passed throughout W-76, and
**sixteen records still went stale**, because ownership is directory-level:

> `src/fux/query/` is owned by **ADR-ASK**. So rewriting the scorer satisfied
> the check by touching ADR-ASK — while **ADR-RANKING**, whose entire subject
> is that scorer, rotted silently and was never opened.

The same shape rotted ADR-POSTINGS, ADR-DOCS-TABLE, ADR-CODES-TABLE,
ADR-RUNTIME-STATS and ADR-RUNTIME-MANIFEST. **The check is not wrong; it is
narrower than it reads.** A component can be *described* by a record that does
not *own* it, and nothing tracks that relationship.

**That is the real deliverable of this item** — not the amendments, which are
done, but deciding whether a record should be able to declare *"I describe this
component even though I do not own it"* and have the check honour it.

## Done 2026-08-24 (no action needed)

Sixteen records amended, each as a dated blockquote quoting the false text:
ADR-RANKING · ADR-POSTINGS · ADR-RECORD · ADR-DOCS-TABLE · ADR-CODES-TABLE ·
ADR-RUNTIME-STATS · ADR-RUNTIME-MANIFEST · ADR-T1-ACCELERATOR · ADR-REFER ·
ADR-ANSWER · ADR-CLI · ADR-CONFIG · ADR-TUNE · ADR-ASK · ADR-INGEST ·
ADR-EXTRACTED · ADR-MERGE-DRIVER. Plus: five broken links, three wrong `built`
cells, a dead worked example in the register's own enforcement clause, and a
`# 40` byte-count comment in `src/fux/derive/format.py` that had been lying
since Phase 1.

**ADR-RUNTIME-STATS' veto had fired unrecorded** — it said *"reopen if BM25F
needs a statistic beyond `n`/`total_wlen`"*, and `newest_mtime` was added for
the recency prior. Now recorded.

## Owed — four rulings

**1. ADR-REFER decision 4's premise is dead.** It refuses `max_age_seconds`
on the stated ground that *"there is no such provenance"* — and the record now
carries `mtime`, a git commit timestamp, which is exactly that provenance.
W-58 closed on the same premise. The decision may still stand on decision 5's
content-verification ground, or it may be reopenable. **It is currently
standing but unargued**, which is the one state a record should never be in.

**2. ADR-ENRICHED vs ADR-ENRICH.** ADR-ENRICH says it *"supersedes the shape
of"* ADR-ENRICHED's generation path, while ADR-ENRICHED stays live,
un-archived and `built: no`. Per the register's own supersede-in-the-accepting-
change rule, someone has to rule whether ADR-ENRICHED is superseded, narrowed,
or still independently live.

**3. Three status flips.** ADR-MCP, ADR-ENRICH and ADR-RERANK are all
`proposed` with register rows reading `built: yes`. ADR-RERANK is additionally
**measured** (28 → 32 of 50, 4 fixed / 0 broken, +8 ms p95, differential law
green over 240 comparisons), which is the built-and-measured pair the register
treats as decisive elsewhere.

**4. ADR-TUNE's key names.** Its specimen `.fux/tune.toml` was reopened to add
five field weights and the `[dense]` table. Those five names were **an
amendment's proposal, not a decision** — `src/fux/tune.py` did not exist.

> **Narrowed 2026-08-24 — the module exists and the names are now load-bearing.**
> ADR-TUNE is built (`v2.0.0-alpha.1`). `src/fux/tune.py` implements every name
> in the specimen, and two tests assert the loader's key set and the shipped
> file are equal **in both directions**, so a name cannot drift from its
> documentation in either.
>
> **What is left is smaller and is still Arpit's**: the names are now a shipped
> interface rather than a proposal, so renaming one is a breaking change from
> here. If any of the five field-weight names or the `[dense]` key names are
> wrong, **this is the last cheap moment to say so** — the record is still
> `status: proposed`, which is exactly the state that makes the change free.

## Owed — one mechanical defect, bigger than it was flagged

~~**The register's display numbers are wrong on 17 rows, not 4.**~~
**FIXED 2026-08-24, once the concurrent session's work was committed.** The
count was **sixteen** rows, not seventeen; `[0039]` did label two rows, and four
rows were out of sequence. Every label now equals its filename and the table is
sorted `0001`–`0041`, contiguous.

**And the suspicion was right, and larger than suspected.** A repo-wide sweep
found **71 more broken links** beyond the five fixed in the audit — every one a
link into `work/open/` for an item that had closed into `archive/open/`, or an
ADR path written from a stale display label. All 71 repointed.

**Gated, under CLAUDE.md's two-strikes rule:**
[`tests/test_doc_links.py`](../../tests/test_doc_links.py) fails when any
relative link in a live document points at a file that does not exist. Frozen
trees are exempt **by law, not convenience** — `WORKLOG.md` is append-only,
`regression/` and `tools/` hold verdicts and pre-registrations that are never
edited — and that exemption's cost is stated in the module docstring.

## Also owed, small

- **ADR-RANKING §1's Examples block** is a stale console capture. Replacing it
  is an editorial call (what should the new example demonstrate — the
  five-field score, the `[archived]` marker, both?).
- **Two ownership notes are misleading**, flagged in the table itself:
  `src/fux/embed/` is claimed by ADR-T1-ACCELERATOR — the record that promises
  never to touch the committed plane — while `embed/chunkvec.py` writes the
  committed `vectors` field; and `ingest/priors.py` computes ranking priors
  under a record about walking git directories, with no ADR mentioning it.

## Owed — a new fork the link sweep surfaced, NOT adjudicated

**Repointing a broken link at an archived file resolves it without grounding
it.** The sweep's 71 fixes mostly turned `work/open/W-nn-*.md` into
`archive/open/W-nn-*.md`. Those links now *resolve* — but CLAUDE.md says an
archived doc **may be named, never cited as backing a live claim**, and roughly
forty of them sit in ADR prose and Reference blocks.

**Both readings are defensible, which is why this is a fork and not a fix:**

| reading | says |
|---|---|
| **the link is naming** | prose like *"W-52's trigger"* names the item; the link is a convenience pointer to where it went, and archive-is-not-evidence is about *grounding*, not about hyperlinks |
| **the link is citing** | a Reference block is exactly where a claim is grounded; a link there IS the citation, whatever the surrounding prose says |

**A test was written for this and then deliberately removed** rather than
shipped red: it could not tell the two apart, and it flagged ~40 lines that
mostly predate this session. Adjudicating it by writing a looser check would be
the failure CLAUDE.md §"a pre-registered threshold may never move" warns about,
in a different costume. **It goes to Arpit.**

If the answer is *citing*, the work is per-link and needs judgment — each one
repointed at its live successor (`IMPLEMENTATION.md`'s row, or the record that
absorbed the decision), not deleted.

## Definition of done

- [ ] The four rulings above are made and recorded.
- [x] ~~The register's 17-row numbering drift is fixed in one pass~~ — **done
      2026-08-24**: sixteen labels corrected, table sorted `0001`-`0041`, and
      71 further broken links repointed behind a new gate.
- [ ] The archived-link fork above is ruled: naming, or citing.
- [ ] A decision on the governance gap: either widen the freshness check to
      honour a declared *describes* relationship, or accept directory-level
      ownership and say plainly in `CLAUDE.md` that the check does not protect
      a record from its own subject changing underneath it.
