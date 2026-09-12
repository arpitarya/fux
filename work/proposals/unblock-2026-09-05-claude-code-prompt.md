---
type: Proposal
title: "Claude Code prompt — execute the 2026-09-05 unblock"
description: "Paste-ready. Arpit strikes or accepts each R-n line, then hands this to Opus in ~/my_programs/fux. Anything left blank is a blocker, not a default."
status: proposed
timestamp: 2026-09-05T00:00:00Z
---

> 🔴 **Void in part since 2026-09-11.** The R-11 bracket and every other line
> naming `fux-playground` are dead: [L9](../../docs/adr/0011_LAW-9-environments.md)
> made that environment Arpit's hands alone. The companion proposal's banner says
> what each one needs instead. Reconciled by [W-138](../../archive/open/W-138-reconcile-with-l9.md).

**Model: Opus** — every ratified line amends a record, freezes a threshold, or writes a gate; a wrong one passes every mechanical check fux has. Run in `~/my_programs/fux`.

---

You are executing the **2026-09-05 unblock** in the fux repo. Read, in this order, before touching anything: `CLAUDE.md` (binding), `work/INTERVIEW.md` (from the reset block), `work/OPEN-WORK.md`, then `work/proposals/unblock-2026-09-05.md` — **the spec**. Each `R-n` there names the row, the evidence, and what you do on ratification. Do not re-derive the evidence unless a claim looks wrong; if one is wrong, record it, do not stop.

## Rulings — this prompt is the ratification

<!-- Arpit: strike or accept each line before pasting. A line left as-is is ACCEPTED as proposed. A line marked OVERRIDE carries his ruling in its place. A line marked BLANK is a blocker: write work/BLOCKED.json and stop on it. -->

- **R-1** ETag criterion: **ACCEPTED 2026-09-05 — decision 12 is the criterion.** Two moves, not one: (a) delete the row, no code; (b) decision 12 **gains the veto condition** *"if a consumer reports refresh bandwidth as a blocker, or a corpus of more than a few hundred `update=auto` URLs is deployed behind a metered or proxied network, request-stage interception is re-costed."* Arpit also asked for the refresh policy to be a declared property — filed as **W-113**, `agent` lane, not part of this batch.
- **R-2** W-83 gate: **RULED 2026-09-06 — superseded by W-114.** Arpit went past the question: **L0** makes ADRs the only source of truth and the Law records supreme, `CLAUDE.md` a permanent pointer. The gate R-2 could not write becomes a parser once the source is single (ADR-CONFIG key tree ↔ `config.py`, both directions). Ship the per-query-gate tightening here; **everything else is W-114 and not this batch.**
- **R-3** W-107 `log()`: **[ (b) tolerance at `round(9)` ]** — the glibc and `idf` probes run before the sha freezes
- **R-4** W-110's `k`: **[ gate VOID · feature stays · next enrichment pre-registration fixes `k` = 3 before any number ]**
- **R-5** prior enrichment re-runs: **[ none owed — audit filed in the spec ]**
- **R-6** `superseded_weight`: **[ default stays · `doctor` discloses ]**
- **R-7** `rerank_weight` / no-op pattern: **[ record once in ADR-TUNE · `doctor` discloses · nothing moves ]**
- **R-8** zero abstentions: **[ gates nothing · reported beside `recall@k` from now on · no threshold ]**
- **R-9** headroom obligation: **[ ratified as written → ADR-RS ]**
- **R-10** the 7 `partial` goldens: **[ third blind reader · two-of-three rule fixed first ]**
- **R-11** W-87 Part B: **[ retarget at playground + `t10000` · `acme`/`orbit` retired ]** · the playground's staged wipe: **[ commit it | restore it ]** ← his hands, not yours
- **W-112** compare doc: **[ write it now, proposed verdict *doc2query first, vectors parked* ]** — the verdict itself stays his

## Order of work

**Start on the agent lane (spec §2) immediately** — none of it waits on a line above:

1. **W-101** — the `doctor` pass, all four things plus the `mtime`/recency check; add R-6/R-7's disclosure line in the same pass if those lines are accepted.
2. **The glibc probe** — a `workflow_dispatch` job on `ubuntu-latest`, Node 20 and 22; **the `idf` widening** on this repo's own index. File both as a `blind` addendum to `2026-09-05-node-log-divergence`.
3. Then, if R-3 is accepted: fill the cell, freeze the sha, **W-107 Phase 1**.
4. The reconciliations (spec §0), R-1, R-5, R-9 — deletions and record edits, an hour together.
5. R-2, R-4, R-6, R-7, R-8 — records and two tests.
6. R-10's blind reader, W-97's harness blockers (then a new `T` id for `expand_weight` **before** any pass), the `heading` control, W-96's paragraph, the lab emitter.
7. The W-112 compare doc, last — it is a reading of runs already filed.

## How to work each line

1. **Explore.** Read every file the spec names for that line. Reconcile against the code and `git log` — a stale claim is a defect to record, not a reason to stop.
2. **Implement**, tests first where a property is named (the parsed-key gate must be **clean today: 15 + 25 keys, 0 unread**; the per-query gate must **reject a copy of the goldens file**).
3. **Verify.** `uv run pytest -q tests` and `uv run pytest -q tests_e2e` green. The differential law re-run for anything touching `rank()` — nothing here should; if it does, stop and say why.
4. **Docs in the same commit** (Law zero): the owning record named on the line — amended, not touched; ownership table + `tests/test_adr_ownership.py` for any new test file; `work/IMPLEMENTATION.md` row; `work/DOC-REGISTRY.md` bumps; the OPEN-WORK row **deleted** and the detail file moved to `archive/open/` only after the IMPLEMENTATION row exists.
5. **Measured runs** (the two probes, R-10) follow `CLAUDE.md §Conformance runs`: classification, Authorship block, per-query rows, `ANALYSIS.md` with repro. Never above 10 000 documents.

Commit messages end with the records touched or `no ADR affected`; install the guard once: `ln -sf ../../scripts/adr-guard.sh .git/hooks/commit-msg`. Read `gh pr checks` yourself — the merge wall enforces nothing.

## Hard rules for this work

- **No default moves.** R-6, R-7, R-8 are disclosures and records; R-4 fixes `k` for the *next* run only.
- **No frozen threshold is edited.** The doc2query run stays *ambiguous* with no `VERDICT.md`; PRE-REGISTRATION-NODE's blank cell is filled, nothing else in it changes.
- **`fux-playground` is not restored by you.** If the R-11 bracket is blank, W-87 and W-112's corpus stay blocked and you say so.
- **A test that cannot fail is not shipped.** The parsed-key gate must be shown failing on an injected unread key before it lands.
- **Ten lines or fewer** per reply; announce transitions (`→ W-101: …` / `✓ W-101 · → R-3`); keep `work/NOW.md` current; append a `work/WORKLOG.md` entry per substantive exchange; keep `work/INTERVIEW.md` true during the session.

Start with the triage rule: read *Blocked on Arpit*, name every row older than 5 days with its age, then `→ W-101`.
