---
name: fux-debate
description: "author a constitutional/standard rule by a two-agent free debate — blind first passes, anti-sycophancy, human ratifier; Fux spends nothing"
trigger: /fux debate
---

# /fux debate — two-agent free debate to author a rule

The *intelligence* is **this host session's** tokens (and two sub-agents it spawns); the
only Fux **code** that runs is the deterministic harness: capture the transcript → hash it →
hand it to `fux ratify`. Fux makes **no** API call. This is how a principle becomes law
(plan §7b): a genuine debate, not a rubber stamp, with a **human as tie-breaker and
ratifier**.

## Inputs

`/fux debate "<proposed rule>" [--tier constitutional]` — e.g.
`/fux debate "never commit money docs or PII; plans live in elgar" --tier constitutional`.

Default tier is `standard`. `--tier constitutional` raises the bar (extra adversarial round
on instant agreement) and means the result, if ratified, enters the apex via `fux ratify`.

## Procedure (you, the host agent, drive this)

1. **Ensure engine + project** — `skills/fux/SKILL.md` Steps 1–2.

2. **"Is this constitutional?" test — only when `--tier constitutional` (surface, don't gate).**
   Before spawning the debate, put this test to the human in one line (it is a **judgment** call,
   never a deterministic check — per the deterministic/judgment split, no `$0` check can decide it):

   > A rule is constitutional **only if** a wrong answer costs **money, PII, audit, or trust**
   > **AND** the rule **never legitimately changes**. If either half fails, it is a `standard`
   > rule — not constitutional.

   - **Over-constitutionalizing** — the rule is expected to evolve (a convention, a default, a
     style call): drop `--tier constitutional`, author it as `standard`.
   - **Under-constitutionalizing** — a money/PII/audit invariant proposed as `standard`: raise it.

   This is the authoring article of [`con-amendment-v2`](../../../../.fux/rules/con-amendment-v2.md).
   Surface it; let the human classify; record their answer in the transcript's first lines.

3. **Spawn two sub-agents — blind first pass.** Use the Task tool (Claude Code) / Agent tool
   (Cowork) to spawn **two** agents. Brief **both identically**: each is *fluent in building
   **and** selling* the product, and has **no assigned side** — this is a free debate, not a
   pro/con setup. Give each only the proposed rule and the codebase, **not the other's
   output**. Each returns, independently:
   - its honest position (adopt / adopt-amended / reject), with reasoning grounded in this
     repo's code and constraints;
   - **at least one concrete objection** to the rule as written (a failure mode, a cost, a
     case it breaks) — an agent that raises none has not done its job; send it back.

4. **Reveal + debate.** Show each agent the other's first pass and run 1–3 rounds where they
   cross-examine: defend, concede, or amend. Capture every round verbatim.

5. **Anti-sycophancy gates (enforce, do not skip):**
   - Each agent must have surfaced **≥ 1 concrete objection** (step 3).
   - **Convergence counts only after both genuinely tried to break the rule** — if either
     agreed without attempting to falsify it, run another adversarial round.
   - **Instant agreement on a `--tier constitutional` rule forces one extra adversarial
     round** — the apex is too important to wave through.

6. **Outcome.**
   - **Converged** → write the full transcript (both blind passes + every round + the agreed
     final wording + residual risks) to `.fux/debates/<rule-id>.md`. Then present the agreed
     rule and hand the user the exact commands to author + ratify — **do not ratify
     yourself**, the human is the ratifier:
     ```
     fux new rule <rule-id> --domain <domain>     # then fill the body + set tier
     fux ratify <rule-id> --by "<human name>" --debate .fux/debates/<rule-id>.md
     ```
     `fux ratify` hashes the transcript into `ratification.debate_hash` — the durable
     "who argued what, and when" record behind the law. On a protected branch with a
     remote, `fux ratify` **automatically writes on a new `constitution/<rule-id>` branch
     and opens a PR** (§2g of the enforcement handoff) — a ratification can never land on
     the protected branch directly; it merges only after the required `fux gate` +
     `ai-review` checks pass. `--no-pr` does a local/offline in-place ratify instead.
   - **Not converged** → **escalate to the human** with both final positions side by side and
     the unresolved crux. Do **not** author or ratify. The human is the tie-breaker; once they
     decide, write the transcript (including their ruling) and proceed to ratify as above.

## Why a debate, not a prompt

A rule waved into the constitution on one agent's say-so is a single point of failure. Two
blind passes plus a forced adversarial round surface the objection a lone author rationalises
away, and the hashed transcript means the *reasoning* — not just the verdict — is auditable
forever via `ratification.debate_hash`. The harness is deterministic and `$0`; the judgement
is the session you are already paying for.
