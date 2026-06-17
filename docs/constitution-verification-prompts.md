# Fux Constitution — Verification & Hardening Prompts

Paste in order. Full spec: `docs/constitution-verification-handoff.md`. The build is implemented; these prove it holds, then harden it.

**Run R1 and R2 in a fresh session or subagent — not the one that built the plan.** Tell each to *report, not fix*. Through-line still applies: Fux never calls a model; the agent does the thinking.

---

## R1 — Red-team the constitution (fresh subagent, fux then anton)

```
Adversary mode. The constitution claims neither a developer nor an agent can break it. Try to break
it — do not help me, do not fix anything yet. Work the verification matrix in
docs/constitution-verification-handoff.md §2. In the fux repo (then the repo-relevant rows in anton),
attempt each and report a row: attack, exact command(s), observed result, CAUGHT or SLIPPED, and the
expected signal vs what you saw.
1  hand-edit a ratified constitutional rule's body
2  add a constitutional rule without `fux ratify`
3  edit .fux/constitution.lock directly
4  edit a ratified debate transcript
5  promote a standard rule via `tier: constitutional` frontmatter edit
6  change code so a constitutional rule's seal drifts
7  `git commit --no-verify`, then confirm CI `fux gate` still catches it (check the required-check config)
8  regenerate the migration baseline to hide a new blocker (is it visible in the PR diff?)
9  route a `deterministic` money/PII principle through the AI critic
10 `pip install fux-engine` with no extras and confirm the maintenance path imports model-free
For every SLIP, give the minimal fix but DO NOT apply it. Label each guard mechanical / CI / procedural
honestly. End with a one-line verdict: is the claim true?
```

---

## R2 — Independent principal review (fresh subagent, fux)

```
Fresh-eyes review against docs/constitution-handoff.md §9 and the verification handoff §3 — you did
NOT write this code. Verify each item by RUNNING it, with evidence, not by reading:
- grep the maintenance path (check/gate/verify/seal/constitution/critic/hooks) for any LLM import;
  confirm default install is model-free
- run `fux gate` twice on an unchanged tree and diff the output (must be identical)
- dependencies = [] ; LLM is an extra only
- money/PII/audit/numbers never reach the critic's AI pass
- coverage is report-first, blocking opt-in by tier
- docs (plan/implementation/cli/README) match the shipped surface
- files ≤100 lines (≤50 utils) — list any over
Report each as PASS/FAIL with file:line evidence. Flag anything over-built and recommend cuts. Do not
change code — give me the report.
```

---

## R3 — Dogfood the real ritual (fux then anton)

```
Walk the real ritual, not a fixture. In fux: run `/fux debate` on con-amendment for real, escalate to
me, I ratify. Confirm the ratification block, debate_hash, constitution.lock, and the provenance check
all populate. Then in anton: same for the money/PII rule. Show me a `fux constitution` status view
(build it if it doesn't exist) of what's constitutional, what each governs, and current violations.
Finally, break each ratified rule by hand and show me the exact gate output a future me would see —
if any message is cryptic, propose a clearer one.
```

---

## Remediation (only after R1/R2, if anything SLIPPED or FAILED)

```
From the R1/R2 report, fix only the confirmed SLIP/FAIL items, smallest change each, in priority:
mechanical guards that failed first, then over-build cuts, then doc drift. For each fix: the attack it
closes, the change, and a regression test that reproduces the original break and now passes. Re-run the
full red-team rows you touched and paste CAUGHT for each. Keep $0/stdlib/determinism/≤100-line intact.
```

---

## Hardening follow-ups (after verification is clean, priority order)

### F1 — Advisory-first critic
```
Make the judgment-principle critic default to SUGGEST, not block; only deterministic hard-invariants
(money/PII) block. Add a per-repo opt-in to escalate a judgment principle to blocking once trusted.
Test: a judgment violation surfaces as advisory and does not fail the gate by default; a deterministic
violation still blocks. Update docs.
```

### F2 — `fux constitution` status view
```
Add a `fux constitution` command (deterministic, $0): list constitutional rules, what each governs
(code_refs), ratifier + date, recent debates, and current violations grouped by severity. One readable
screen. Tests + cli.md + README.
```

### F3 — "Is this constitutional?" heuristic
```
Add one line to con-amendment: a rule is constitutional only if a wrong answer costs money/PII/audit/
trust AND the rule never legitimately changes. Make `/fux debate` surface this test when a proposal is
tagged tier: constitutional, so over-/under-constitutionalizing is caught at authoring. Re-ratify
con-amendment (it changed).
```

### F4 — Runtime critic on Anton (deferred §5.3)
```
In anton, expose the critic as a callable in front of the riskiest live path (start with one money or
PII path). Deterministic checks block; judgment critique is advisory at first. Cage meters the agent
tokens. Add a probe that attempts a forbidden runtime action and is caught. Keep it scoped to one path;
do not widen until it's proven. Update anton docs + guardrails.
```
