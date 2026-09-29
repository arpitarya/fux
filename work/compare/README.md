---
type: Index
description: "Index of the live forks: verdict first, every one with a reopen-trigger."
---

# `work/compare/` — live forks, verdict first

**How to use this directory.** One doc per **live fork**: a genuine decision
with real options, an experiment, or an alternative implementation that
actually exists alongside the current one. Every doc carries two things
non-negotiably — a **verdict** and an explicit **reopen-trigger**, the
condition under which the comparison must be redone.

**Fork or idea?** A fork has options on the table now → here. An idea nobody
has decided on → [`../proposals/`](../proposals/README.md). If you cannot tell
which, it is a proposal.

**The reopen-trigger is a condition, not a date.** Write what would have to
become *true* for the comparison to be worth redoing, in terms someone can
check today. A trigger phrased as an event to await never fires.

**The verdict block sits at the top of every doc** — status, the call,
confidence, and the reopen-trigger — so a reader gets the decision without the
debate, and the debate without archaeology. v0.26-era compare docs are archived
at [`archive/v0.26-docs/compare/`](../../archive/v0.26-docs/compare/).

🔴 **Two live forks** — eight after the 2026-09-20 sweep, down from 24; plus `intent-doctype-prior` (2026-09-24), `identifiers-whole` and `authority-prior` (2026-09-28), `rm3-selective` (2026-09-29); **less seven decided and built forks archived 2026-09-24**, each after its live triggers were ported into its owning record
([W-206](../../archive/open/W-206-compare-and-proposals-sweep.md)). **Sixteen left**, and
the split is worth knowing before you go looking for one:

- **Nine were MERGED into their owning record** — the verdict and the
  reopen-trigger both live there now, so the row in
  [`archive/compare/README.md`](../../archive/compare/README.md) says *"the
  trigger lives in `<record>` `<decision>`"* rather than why it cannot fire.
  **The fork is still checkable; it is checkable somewhere better.**
- **Seven had triggers that can no longer fire** — a premise that died, a
  precondition that was deleted, a target above the measurement ceiling.

⚠ **Two of the nine needed a PORT before they could move**: `index-lock`'s
NFS/SMB trigger was absent from [SR-LOCKS](../../records/0140_locks.md) and
`maintenance-trigger`'s half-written-shard condition was absent from
[SR-MAINTENANCE](../../records/0129_hooks.md). Archiving first would have
deleted the only written statement of each — which is why the rule is *port,
then move*, in that order and in one change.

| doc | fork | verdict | status |
|-----|------|---------|--------|
| [authority-prior](authority-prior.compare.md) | W-168 step 8 — the git authority prior: which statistic (authors, commits, their product), how it is scaled (corpus-normalised, keyless saturating, capped log), where the counts live (`M/`, a plane, only when on), and the recency trap | ✅ **ruled 2026-09-28 (Arpit): A3 · S2 · L1** — authors × commits, `f = 1 − 1/(a·c)`, two ints on `M/`, `authority_weight` at `0.0`; [pre-registered](../regression/2026-09-28-authority-prior/PRE-REGISTRATION.md), not built | the run FAILs (weight stays `0.0`, counts stay as facts; superseded exemption or A1 next); S2 saturates on a real corpus (S3); history dominated by mass commits |
| [identifiers-whole](identifiers-whole.compare.md) | W-233: how an identifier is kept whole after analyzer v3 (families in `.fux/identifiers.toml`, matched on both sides) and the eight sub-decisions F1–F5 left open | ✅ **built, measured PASS 2026-09-28, inside F1–F5 (ruled):** family matching (e) with a per-family canonical form (d); no exact field, no stemming change, no sha prefix, no global dash fold; the rules digest stamped into each shard header | (c) a case where the canonical term is shared and a parts-neighbour still wins; (f) ≥ 6 documents citing a hex id by prefix; a letter-prefixed ID with a Unicode dash no family covers |
| [section-units](section-units.compare.md) | W-168 step 10 — what unit the ranking sees (documents re-ranked by best section at query time, section records, or per-section statistics), how a section backs off to its document, and what a PASS is measured on | ✅ **ruled 2026-09-29 (Arpit): U2 · B2 · E1** — `doc#section` records in the index, superseding U0 (2026-09-27); ⏸ parked, pool 1 < 6, not built | a set with a `step10_section` pool ≥ 6 (starts the build); U2's size fails SR-WORK-SCALE (U3 next); `[bm25f] b` back above `0.5` |
| [rm3-selective](rm3-selective.compare.md) | W-168 step 5 — whether RM3 returns as SELECTIVE expansion, gated by the first pass's band, after SR-EXPAND d17 removed it | ⏳ **proposed 2026-09-29:** R0, stay removed. Post hoc on both filed runs, every band gate still loses a baseline rank-1 hit or nets below the gain bar; selective expansion is the only form it may return in | a gate fixed before any score clears both frozen clauses on a set not yet scored with RM3; needs SR-EXPAND d17 amended |
| [intent-doctype-prior](intent-doctype-prior.compare.md) | W-168 step 9 — where a document's type is declared (per source, a query-time glob table, front-matter), how a question's intent is read (a fixed cue lexicon, consumer cues, a model), and whether step 3's history/current intent joins the step | ⏸ **parked (2026-09-24)** — the measured I1 pool on gen 2 is 2 and 1, below 6, so the step stops before build. Recommended when it reopens: D2 a `[doctype]` glob table in `tune.toml`, read at query time; I1 a fixed engine cue lexicon; M1 `[ranking] intent_weight` at `0.0`; S1 step 3's intent stays out. Measured first: 0 of 32 seed front-matters declare a type and every seed is in one source directory, so D2 is the only option testable on the frozen ladder | the run FAILs (weight stays 0); the tagged pool is below 6 (stop before build); or a corpus with per-folder or per-document types arrives |
| [abstention-gates](abstention-gates.compare.md) | which gates decide `answerable`, and how the signals combine — graduates option C of the abstention-gate proposal | **proposed** on which gates and their floors; **ruled (Arpit, 2026-09-13):** a gate chain, never a blended number, and every independent signal returned as its own field, visibility in `output.toml` | a measured gate abstains on answerable golden questions above its pre-registered ceiling (withdrawn, not loosened); or the key cannot carry enough unanswerable questions for a decidable verdict |

Convention: `> **Verdict:**` blockquote first, then Context → Options →
Matrix → Consequences → References → Reopen-trigger. Docs here are compact;
if one outgrows a screen, split it into a *For humans* summary section and a
*For AI agents* decision-data section (per OPEN-WORK convention).
