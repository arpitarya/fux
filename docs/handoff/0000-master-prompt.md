---
type: Handoff Prompt
title: Master prompt — execute handoffs 0001 → 0002 → 0003 sequentially
description: One paste-ready prompt that builds all three specced phases in order, with hard gates between them.
status: ready
timestamp: 2026-07-21T00:00:00Z
---

# Master prompt — build everything, one phase at a time

Paste everything below into Claude Code at the repo root.

---

You are building the Fux engine across **three committed specs, strictly in
sequence**: 0001 (query CLI v1) → 0002 (ingest v1.1: web/CDP/advanced) → 0003
(engine v2: bundled model + RRF hybrid). One phase at a time; a phase is not
started until the previous one is fully closed out.

**Ground rules for the whole run:**
1. Read `CLAUDE.md` first — it is binding for every phase (constraints, docs law,
   worklog duty, OKF pattern, doc registry).
2. Read `docs/model-handoff-interview.md` for judgment context.
3. Decisions are closed. The compare docs in `docs/compare/` record every verdict
   and its reopen-trigger. If you believe a decision must be reopened, stop and say
   so with evidence — do not silently deviate.
4. **Phase gate (hard):** a phase is complete only when its handoff's definition of
   done is met, both test suites are green, its ADRs are written, its docs updates
   are done (fux-plan, README, DOC-REGISTRY, worklog, model-handoff-interview), its
   handoff+prompt pair is moved to `docs/archive/` with `status: implemented`, and
   the version is bumped. Only then open the next handoff.
5. Between phases, print a short **phase report**: what shipped, test counts, open
   risks carried forward. Append it to `docs/worklog.md` (newest on top).
5b. **Live tracking (continuous):** `docs/implementation.md` is the milestone-level
   status board. Flip a row the moment a milestone completes; keep its "Now working
   on" line current at regular intervals during long milestones; record any
   deliberate spec deviation in its Deviations section. Never ✅ with failing tests.
6. Note: the plan's intended gate between phases was an Anton dogfood. Arpit has
   chosen a single continuous run instead — so after 0001, additionally generate
   `DOGFOOD.md` at the repo root: a 10-minute quickstart for pointing Fux at a real
   folder (Anton), so dogfooding can start in parallel while you continue.

**Phase 1 — execute `docs/handoff/0001-query-cli-v1-prompt.md`.**
Open it and follow it exactly (explore → milestone plan → implement → verify →
close out). Its handoff is `0001-query-cli-v1-handoff.md`.

**Phase 2 — execute `docs/handoff/0002-ingest-web-advanced-prompt.md`.**
Precondition: Phase 1 archived. Follow it exactly. Network stays inside the ingest
fence; tests use the local fixture HTTP server, never the real internet.

**Phase 3 — execute `docs/handoff/0003-hybrid-engine-v2-prompt.md`.**
Precondition: Phase 1 archived (Phase 2 done in this run). Eval harness first; the
eval gate (hybrid beats lexical on hit@5 and MRR) decides whether hybrid ships
enabled or behind `--hybrid` — record the numbers either way.

**Final close-out after Phase 3:**
- Full-suite run (`tests` + `tests_e2e` + eval) — all green, reported.
- `README.md` tells the complete story (install → setup → ingest → ask/find/answer
  → agent integration), truthful to what exists.
- `docs/worklog.md` gets a final "all three phases complete" entry; the
  model-handoff-interview's state of play reflects the shipped engine.
- Move `docs/handoff/0000-master-prompt.md` itself to `docs/archive/` with
  `status: implemented`.
- Version: 0.20.0 after Phase 1, 0.21.0 after Phase 2, 0.22.0 after Phase 3.

If any phase fails its gate, stop there, leave the repo green at the last completed
phase, and write up exactly what blocked you in the worklog. Do not start a phase
you cannot finish cleanly.

Begin with Phase 1. Show its milestone plan before writing code.
