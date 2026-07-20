# Claude Code prompt: Fux roadmap orchestrator (queue-driven, PR-by-PR)

You are driving a **queue of implementation handoffs** to completion, **one at a
time**, each as its own branch → PR. You process a handoff fully (decide → implement →
test in the dummy repo → gate → open PR), then **STOP and wait for me to merge**, then
pull `main` and start the next. Repeat until the queue is empty.

Read this whole prompt first. Then read `CLAUDE.md` (house rules) and confirm the queue
and order with me before touching anything.

## Why you must NOT auto-merge (non-negotiable)

Fux's own merge wall requires two checks on `main`: `fux gate` **and** `ai-review`,
where `ai-review` **refuses when reviewer == author**. An agent that opens a PR *and*
merges it is reviewer == author — the exact thing this repo forbids. So your job ends at
**"PR opened, checks green, waiting for human review."** You never merge. "Publish" here
= push the branch and open the PR. I merge.

## The queue (ordered — confirm before starting)

Process in this order unless I say otherwise. The order is deliberate: the dummy-repo
harness must exist before anything can be tested in it; scale must land before parity so
parity benchmarks a fast Fux; connectors go last (largest surface, touches the
constitution path).

0. **fux-lab harness** — spec: `docs/fux-lab-handoff.md` + `docs/fux-lab-claude-code-prompt.md`.
   Prerequisite: it *is* the dummy repo everything else is tested in.
1. **Graph scale (23k nodes)** — `docs/handoff-03-graph-scale.md` + `docs/prompt-03-graph-scale.md`.
2. **Parity command** — `docs/handoff-01-parity-command.md` + `docs/prompt-01-parity-command.md`.
3. **Multi-assistant** — `docs/handoff-02-multi-assistant.md` + `docs/prompt-02-multi-assistant.md`.
4. **Org connectors** — `docs/handoff-04-org-connectors.md` + `docs/prompt-04-org-connectors.md`.

Maintain a running checklist (in the PR description and back to me) of queue progress:
`[ ] 0 fux-lab  [ ] 1 scale  [ ] 2 parity  [ ] 3 multi-assistant  [ ] 4 connectors`.

## The per-handoff loop (run this for each queue item, in order)

For the current handoff, do exactly these steps and do not skip ahead:

1. **Load & decide.** Read the handoff doc and its paired prompt. Surface its §10 OPEN
   QUESTIONS to me and **get answers before writing any code.** Do not guess them.
2. **Branch.** `git checkout main && git pull`, then create a focused branch
   (`feat/<handoff-slug>`). One handoff = one branch = one PR.
3. **Explore → Plan → Confirm.** Explore the real code first. Post a short plan (files
   you'll change, the approach, the test fixtures you'll add). **Pause for my confirmation.**
4. **Implement incrementally.** Small coherent commits; keep the build green throughout.
   Follow the paired prompt's constraints verbatim.
5. **Test in the dummy repo.** Extend `fux-lab/` with fixtures + goldens + negative
   guards for the *new* surface (don't assume the existing harness covers new code).
   Run `python run_lab.py` and the offline `$0` sweep. Add/extend `pytest` tests. All green.
6. **Docs (part of done).** Update every doc the handoff's §9.5 names — `docs/fux-plan.md`,
   `docs/fux-implementation.md`, `docs/cli.md` (regenerate the registry table, don't
   hand-edit), README, whats-new, `install.sh`/`SKILL.md` where relevant. For
   `CLAUDE.md`/`AGENTS.md`: **propose** the edit and flag it for my review — never
   silently rewrite steering files.
7. **Gate.** Run `fux gate`, `python -m pytest -q`, and `python -m tools.skillgen --check`.
   Fix every red. Do not proceed with a failing gate.
8. **Open the PR (do not merge).** Push the branch; open a PR with `gh` whose description
   contains: the handoff link, what changed, the definition-of-done checklist ticked, the
   test/`run_lab.py`/gate evidence, any proposed CLAUDE.md edits called out for review,
   and the queue checklist. Then **STOP.**
9. **Wait for human merge.** Tell me the PR is ready and what to review (especially any
   determinism/constitution-sensitive diff). Do nothing further on this item until I
   confirm it's merged.
10. **Advance.** On my confirmation: `git checkout main && git pull`, tick the queue,
    start the next handoff at step 1. When the queue is empty, summarize all PRs and stop.

## Hard constraints (apply to every handoff)

- **Never merge / never bypass the wall.** PR + green checks + human review is the finish
  line. If `ai-review` refuses because reviewer == author, that's working as intended —
  surface it, don't route around it.
- **Never break the constitution:** `$0`, stdlib-only, deterministic, **no LLM on any
  maintenance path**. If a handoff seems to require it, STOP and ask — do not proceed.
- **Never edit the Fux engine to make a test pass.** Tests report reality; a real bug is a
  finding, not something to hide. (Applies especially to the fux-lab harness.)
- **Determinism is sacred** (handoff-03): cached/incremental `graph.json` must be
  byte-identical to a full build; ship the proving test.
- **One handoff at a time.** Do not start the next branch until the current PR is merged.
- **Secrets by reference only.** Never paste or store credentials (relevant to connectors).
- **Ambiguity or conflict → STOP and ask.** Especially the §10 open questions and anything
  touching the constitution/ratify path or the error contract.

## Guardrails / when to stop and ask

- Before starting: confirm the queue + order with me, and that `gh` is authed and branch
  protection is in place (so PRs route correctly).
- Before coding each handoff: resolve its §10 open questions.
- If `fux gate` or `ai-review` blocks and the fix would weaken governance — stop, explain,
  ask. Never disable a check to get green.
- If a change would touch `main` directly, a constitutional rule, or `constitution.lock` —
  stop; those go through the documented ratify/PR path, never an ad-hoc edit.
- If scope balloons beyond the handoff (e.g. a connector needs a new auth system) — stop,
  propose splitting it into a follow-up handoff, don't silently expand the PR.

## First action

Do **not** start coding. Reply with: the confirmed queue + order, the open questions from
handoff-0 (fux-lab) that you need me to answer, and a one-paragraph plan for item 0. Wait
for my go.
