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

🔴 **Eight live forks, down from 24 on 2026-09-20**
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
| [ask-graph-expansion](ask-graph-expansion.compare.md) | a document BM25F never retrieves can still be the answer when the retrieved ones link to it — should `ask` follow links, and how: a labelled second list, a rank-fused boost, a score blend, or leave `ask` alone | **accepted (Arpit, 2026-09-13)** — two atoms `fux lexical` + `fux graph --seed`, `ask` = their composition, a **boosted** tier (RRF) and a labelled **related** tier; `answer` reads `ask`; Node gains the graph plane. Items W-160 / W-161 | the composition tests cannot hold; Node cannot reach `graph.json` digest equality; or the registered prediction fails — the atoms stay, the two-tier `ask` is withdrawn |
| [fux-correct](fux-correct.compare.md) | the wrong document was served for a question the corpus answers — pin, human document expansion, Rocchio feedback, or log learning | **accepted (Arpit, 2026-09-13)** — a human-authored question line on the document's enrichment file (`ctx`), marked human, surviving regeneration, reported-never-refused, doubling as an eval row; a rare `--pin`; negative corrections refused. Item W-162 | human lines fix only their exact phrasing on the eval set (then the pin is the honest mechanism); or `ctx`'s weight must rise for corrections to bite (a ranking change, W-156's rule) |
| [abstention-gates](abstention-gates.compare.md) | which gates decide `answerable`, and how the signals combine — graduates option C of the abstention-gate proposal | **proposed** on which gates and their floors; **ruled (Arpit, 2026-09-13):** a gate chain, never a blended number, and every independent signal returned as its own field, visibility in `output.toml` | a measured gate abstains on answerable golden questions above its pre-registered ceiling (withdrawn, not loosened); or the key cannot carry enough unanswerable questions for a decidable verdict |
| [types-toml](types-toml.compare.md) | does `.fux/sources/types` become `.fux/formats.toml`, and in what shape — reversing SR-TYPES' recorded rejection of a TOML types list | **D** — an `include` glob array plus a `[decoders]` table keyed by extension (Ruff's `include`/`extension` pair); F1–F6 as proposed. Shipped as [SR-TYPES](../../records/0128_types-list.md) decision 12; the conversion re-ingested this repo byte-identical. **Paid:** the three source lists no longer share one grammar | ✅ accepted (Arpit, 2026-09-11) — built (W-130) |
| [what-good-means](what-good-means.compare.md) | what a fux quality number actually measures — six forks: the query prior, `unanswerable` in or out, who sets the cost weights, whether `answered` is judged, public or internal, and whether to build a query log | **All six as proposed**, plus a mechanism §4 did not specify: the cost of an error is a **confidence target**, `t = 0.75` → `c = t/(1-t) = 2`, frozen **before** any score exists under it. Headline is **`recall@k`** at equal byte budget; `nDCG` demoted to a diagnostic because a reranker discards the ordering and LLM attention is U-shaped. Shipped as [SR-WORK-QUALITY](../../records/0056_WORK-quality.md). ✅ **Fork 6 ruled `no query log` and did NOT rule whether L2 reaches one; that was [W-89](../../archive/open/W-89-does-l2-reach-a-query-log.md), now RULED (Arpit, 2026-08-27): a new law, `L8` — *a use record never leaves the machine*** ⚠ **reverted by Arpit the same day** to permit plaintext queries and answers and a stdout receipt; what survives is the confinement — normative text in [`CLAUDE.md`](../../CLAUDE.md) §Non-negotiable constraints, reasoning in [SR-LAWS](../../records/0001_LAWS.md) decision 8. ⚠ The archived path above is where the file belongs; the `git mv` is outstanding (see [`OPEN-WORK.md`](../OPEN-WORK.md)) | ✅ accepted (Arpit, 2026-08-27) |
| [df-over-the-union](df-over-the-union.compare.md) | should ARCHIVED documents count toward `df` (rarity)? | **A + D — change nothing.** `df` stays computed over the union; the mechanism this was really asking for had already shipped as `archived_weight`. ⚠ Its pointer still says the knob lives in `fux.toml`; `[ranking]` moved wholesale to `.fux/tune.toml` in `v2.0.0-alpha.1` and the old table now errors | ✅ accepted (Arpit, 2026-08-22) — **row added 2026-08-25; the doc had none** |
| [blind-authorship-rule](blind-authorship-rule.compare.md) | does the measurement discipline gain a blind-authorship rule, and **in what words** | **ACCEPTED, in the rewritten form of §5** — every measured run is `blind` or `informed`; an informed run is **reclassified, never banned**, and never supplies a delta (TREC's manual/automatic split, since 1994); a delta below the set's resolution is *no detected change*. **The wording drafted 2026-08-24 was refused** — wrong in four ways CONSORT 2025 and ARRIVE 2.0 name precisely, and silent on power and controls. ⚠ **Two of six parts are apparatus and did NOT take effect** ([W-82 §5.4](../../archive/open/W-82-the-consolidated-build.md)). Also carries **three corrections to fux's own filed evidence** | ✅ accepted (Arpit, 2026-08-25) |
| [hook-at-scale](hook-at-scale.compare.md) | what `post-commit` does when the corpus is large — ceiling vs defer vs pre-push vs incremental | **B — the hook defers**: commit cost becomes git's cost (0.34 s at 100k, constant), and it is the only option that reaches the 1 s bound at every size. **Built 2026-08-22** (W-66, all four phases) | ✅ accepted (Arpit, 2026-08-22) |

Convention: `> **Verdict:**` blockquote first, then Context → Options →
Matrix → Consequences → References → Reopen-trigger. Docs here are compact;
if one outgrows a screen, split it into a *For humans* summary section and a
*For AI agents* decision-data section (per OPEN-WORK convention).
