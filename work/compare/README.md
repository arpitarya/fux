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

🔴 **Two live forks** — eight after the 2026-09-20 sweep, down from 24; plus `intent-doctype-prior` (2026-09-24), `identifiers-whole` and `authority-prior` (2026-09-28), `rm3-selective` (2026-09-29), `shared-runtime` (2026-09-30); **less `intent-doctype-prior` and `identifiers-whole`, archived 2026-09-29** (built and measured, triggers ported into SR-TUNE d20 and SR-IDENTIFIERS d12); **less seven decided and built forks archived 2026-09-24**, each after its live triggers were ported into its owning record
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
| [shared-runtime](shared-runtime.compare.md) | W-242 — one query cache for both readers: read each shard once (T0), Node reads Python's `.fux/runtime/` (T1), Node builds it too (T2), or a query-result cache (T3) | ✅ **ruled 2026-09-30 (Arpit): T0 · T1 · T2; all three BUILT and PASS 2026-10-03** ([report](../regression/2026-09-30-shared-runtime/report.md)); T3 refused; Fork A (`graph.json` in Node) open | a Node-built plane differs from a Python-built one outside `stamp.json`; a fresh-plane Node query is not faster than its scan at rung-01000+; MCP repeats above a quarter of calls (T3) |
| [node-plane-rebuild](node-plane-rebuild.compare.md) | W-235 — how the Node reader stops paying ~80 % of a query to rebuild the graph plane: parse less (O1), build lazily (O2), or read Python's derived `graph.json` (O3, changes SR-NODE-SEARCH d9) | ✅ **O1 built 2026-09-29** — `id` and `edges` only; ~0.50 s → ~0.15 s, output byte-identical; d9 unchanged | `graphRecords` + `buildPlane` + GC above half a Node `find`'s profile again; the writer stops sorting keys |
| [authority-prior](authority-prior.compare.md) | W-168 step 8 — the git authority prior: which statistic (authors, commits, their product), how it is scaled (corpus-normalised, keyless saturating, capped log), where the counts live (`M/`, a plane, only when on), and the recency trap | ✅ **ruled 2026-09-28 (Arpit): A3 · S2 · L1** — authors × commits, `f = 1 − 1/(a·c)`, two ints on `M/`, `authority_weight` at `0.0`. 🔴 **Measured FAIL (drift); removed 2026-10-03 with its counts (option c, index v7)** — [verdict](../regression/2026-09-28-authority-prior/VERDICT.md) | the run FAILs (weight stays `0.0`, counts stay as facts; superseded exemption or A1 next); S2 saturates on a real corpus (S3); history dominated by mass commits |
| [section-units](section-units.compare.md) | W-168 step 10 — what unit the ranking sees (documents re-ranked by best section at query time, section records, or per-section statistics), how a section backs off to its document, and what a PASS is measured on | ✅ **ruled 2026-09-29 (Arpit): U2 · B2 · E1** — `doc#section` records in the index, superseding U0 (2026-09-27); ⏸ parked, pool 1 < 6, not built | a set with a `step10_section` pool ≥ 6 (starts the build); U2's size fails SR-WORK-SCALE (U3 next); `[bm25f] b` back above `0.5` |
| [rm3-selective](rm3-selective.compare.md) | W-168 step 5 — whether RM3 returns as SELECTIVE expansion, gated by the first pass's band, after SR-EXPAND d17 removed it | ✅ **ruled 2026-09-29 (Arpit): R1 · G3** — RM3 expands only on a `grounded` first pass (superseding R0 the same day). 🔴 **Measured FAIL (no gain) 2026-10-03 and RM3 removed again** — [verdict](../regression/2026-09-30-rm3-grounded/VERDICT.md), SR-EXPAND d17. Earlier: Post hoc on both filed runs, every band gate still loses a baseline rank-1 hit or nets below the gain bar; selective expansion is the only form it may return in | a gate fixed before any score clears both frozen clauses on a set not yet scored with RM3; needs SR-EXPAND d17 amended |
| [abstention-gates](abstention-gates.compare.md) | which gates decide `answerable`, and how the signals combine — graduates option C of the abstention-gate proposal | **proposed** on which gates and their floors; **ruled (Arpit, 2026-09-13):** a gate chain, never a blended number, and every independent signal returned as its own field, visibility in `output.toml` | a measured gate abstains on answerable golden questions above its pre-registered ceiling (withdrawn, not loosened); or the key cannot carry enough unanswerable questions for a decidable verdict |
| [l12-classify](l12-classify.compare.md) | W-225 step 1 — every site L12's veto greps find in `src/fux` and `node/src`, classified tunable, tunable-new, fixed or not-a-value (359 rows) | ✅ **ratified 2026-09-27 (Arpit):** R1–R6 as recommended, recorded in SR-LAW-12 decisions 1, 6, 9a, 9b; the working table for W-225's remaining stages | a veto grep, or R5's widened successor, prints a site that is not a row here |

Convention: `> **Verdict:**` blockquote first, then Context → Options →
Matrix → Consequences → References → Reopen-trigger. Docs here are compact;
if one outgrows a screen, split it into a *For humans* summary section and a
*For AI agents* decision-data section (per OPEN-WORK convention).
