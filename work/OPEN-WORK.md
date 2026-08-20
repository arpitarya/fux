# OPEN-WORK — what is still open

*Items first, grouped by the record they belong to. **The rules and the standing
obligations are at the foot of this file** — read them once, then work from the
top.*

**Lane tags:** `agent` — an agent can close it alone · `arpit` — only Arpit can.
The two run **concurrently**; never order one against the other.

---

## Blocked on Arpit — the inbox

**Empty.**

---

## Open items, by record

### [ADR-ASK](../docs/adr/0004_ask.md) · [ADR-FIND](../docs/adr/0005_find.md) · [ADR-ANSWER](../docs/adr/0006_answer.md)

- **W-46** · `agent` · Sonnet · `ask --hybrid` crashes on a source install — the missing-model guard catches the wrong exceptions — [detail](open/W-46-hybrid-missing-model-crash.md)
- **W-48** · `agent` · Sonnet · **low** · three output-contract inconsistencies across the three verbs — [detail](open/W-48-query-output-contract.md)

### [ADR-DIR-LIST](../docs/adr/0023_dir-list.md)

- **W-45** · `agent` · **Opus** to decide, Sonnet to build · `.fux/sources/dirs` is include-only, so committed measurement evidence contaminates the corpus it measures. **Its schema question is answered** — an exclusion attribute on a directory line, and the file now exists to carry one (W-54, 2026-08-19). **The fork itself still owes a compare doc**, and the attribute set is closed at one until this record changes — [detail](open/W-45-source-exclusion.md)

### [ADR-DIR-LIST](../docs/adr/0023_dir-list.md) · [ADR-RANKING](../docs/adr/0012_ranking.md) — **parked**

*Both are gated on a pre-registered instrument that does not exist, is not an
item, and has no owner. **Parked with a trigger, not scheduled**: they resume
when the pre-registration is written, and not because they look ready.*

- **W-44** · **PARKED** · annotate archived results, never reorder — decided ([ADR-DIR-LIST](../docs/adr/0023_dir-list.md)); **trigger: a frozen query set with expected live-vs-archived answers exists** — [detail](open/W-44-archived-content-signalling.md)
- **W-52** · **PARKED** · `df` is computed over the union — **42% of live terms carry an inflated `df`**; **trigger: the same pre-registration, plus a second corpus** — [detail](open/W-52-df-over-the-union.md)

### No record yet — the unbuilt milestones

*Each writes its own record when it lands. **The detail file is the spec** —
`PLAN.md` was archived 2026-08-18 and its scope migrated into these files.*

- **W-23** · `agent` · **next, and unblocked** · M3 graph lane — edges, community, `explain`/`graph`/`path`; none of the three verbs exists in `cli.py` — [detail](open/W-23-m3-graph-lane.md)
- **W-24** · `agent` · **next, and unblocked** · M4 refer plane — HTTP+Confluence, ARC, assembler, freshness fence; `src/fux/refer/` is a 7-line stub · *no live spec; write one first* — [detail](open/W-24-m4-refer-plane.md)
- **W-25** · `agent` · blocked by W-23, W-24 · M5 maintenance — hooks, line-wise LWW merge driver, hashed-meta enforcement — [detail](open/W-25-m5-maintenance.md)
- **W-26** · `agent` · blocked by W-25 · M6 scale & T2 — `tpack`, mmap segments, 100k/1M bench, paper §4–§6 rewritten to measured — [detail](open/W-26-m6-scale-t2.md)
- **W-27** · `agent` · blocked by W-26 · M7 dogfood & release gate — fux + Anton, two weeks — [detail](open/W-27-m7-dogfood-release-gate.md)
- **W-38** · **PARKED** · blocked by W-26 · M8 deferred set — one record + sign-off each; **pruning work is forbidden outside this item** — [detail](open/W-38-m8-deferred.md)

---

## Predictions still unmeasured

| id | prediction | threshold | measured at |
|----|-----------|-----------|-------------|
| R4 | refer plane | cold k=10 ≤ 3 s / warm ≤ 300 ms | W-24 |
| R5 | 20-doc commit re-index | < 1 s via hook | W-25 |
| R6 | machine planes conflict-free, human conflicts preserved | three-tier harness | W-25 |
| R7 | committed @100k target density | ≤ 250 MB packed; tier-auto correct | W-26 |

R1 **PASS** · **R2 3/3 PASS** ([run](regression/2026-08-12-r2-close/report.md)) ·
**R3 PASS** — worst-case p95 **27.2 ms** vs a 150 ms bar on 8 870 RFCs
([run](regression/2026-08-12-m2-accelerator/report.md)).
P1 **FAIL** — full postings, permanently
([verdict](regression/2026-08-09-pruning-rerun/VERDICT.md)); P2–P7 retired with
plan revision 1, their successors R3–R7.

**Where the build stands** is [`IMPLEMENTATION.md`](IMPLEMENTATION.md), not this
file. M0, M1 and M2 have shipped; **`v0.33.0` is on PyPI** (2026-08-19, the
sources rewrite — verified black-box from the published wheel).

---
---

# The rules

*Kept at the foot deliberately: they change rarely, and the items are what a
session needs first.*

1. **Maintained in the same change as the work**, never afterwards. An item
   finishes, a defect is found, scope moves, something blocks or unblocks: this
   file and the item's detail file change in that same edit. A session that
   updates the queue "at the end" has already lied to the one after it.
2. **Completed items are removed, never ticked.** Closing is legal only once
   the outcome is recorded in [`IMPLEMENTATION.md`](IMPLEMENTATION.md) and any
   evidence is filed under [`regression/`](regression/README.md). **The row is
   deleted; the detail file moves to [`archive/open/`](../archive/open/)**
   (Arpit, 2026-08-19) — the reasoning that produced a call is worth keeping,
   the queue entry is not. The durable record is still the ADR plus the
   [WORKLOG](WORKLOG.md) entry; an archived file may be named, never cited. No
   tombstones, no DONE rows, no `closed/` inside `work/`.
   **The length of this file is the signal of how much is actually pending.**
3. **The markers here are assertions, not evidence. Re-derive, do not read.**
   Before treating anything as pending or done, reconcile against
   `regression/`, `IMPLEMENTATION.md`, and the repo itself (`git log`,
   `git tag`, the code). A stale ✅ overstates progress; a stale pending row
   that an unrelated commit already closed understates it — **both are the same
   class of defect**.
4. **Two lanes, ordered independently — they run concurrently.** `arpit` needs
   a human's hands; `agent` an agent can execute alone. Forcing one priority
   order across both is what makes a session sit idle behind a decision it was
   never going to make. Order **within** a lane; never across them.
5. **Priority is damage that accrues with elapsed time**, above damage that is
   merely present-but-static. A wrong constant that is the same size next month
   can wait; an unratified record that more code ships under every day cannot.
   Only the former gets worse by waiting.
6. **No separate prioritization or sequencing document.** Ordering lives here.
   A second document naming what to do next is always the stale one.
7. **Grouped by record, because that is where the work lands.** An item's group
   is the record its change will have to update — which is Law zero made
   visible: if you cannot name the record, say **"no ADR affected"** out loud.

## Standing obligations (every session)

- **WORKLOG entry per substantive exchange**, with its `Cost:` line — a
  chat-only session counts.
- **This file and the item's detail file** on any status change; a DOC-REGISTRY
  row bump for any doc touched; INTERVIEW kept current *during* the session.
- **Reconcile before you report** (rule 3).
- **Records are cited by name** — `ADR-RECORD`, never a number. "archived
  ADR-NNNN" *with its path* means the frozen v0.26 line under
  `archive/v0.26-docs/adr/`; a bare `ADR-<NAME>` means `docs/adr/`.
- **No behaviour change lands without its record updated in the same change.**
  If a change genuinely touches no recorded decision, say **"no ADR affected"**
  in the commit message rather than skipping the check silently.
- **The lab persists.** `~/my_programs/fux-lab` is never deleted or rebuilt —
  new runs are new environments inside it ([SETUP-LAB](setup/fux-lab.md)).
