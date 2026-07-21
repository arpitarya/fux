# Fux Fleet — the governance plane for agentic development

> **The line:** Agents write the code. Fleet proves they followed the rules — and puts them back on spec when they didn't.

*Vision draft · July 2026 · pre-plan — this document argues the bet; the plan comes after we agree on it.*

---

## The world this bets on (18–36 months out)

Every projection below traces to a signal observable today — no hype.

1. **Most enterprise code will be agent-written.** Signal: agent coding tools are already the default for greenfield work in every org that permits them ([METR: AI task horizons doubling ~7 months](https://metr.org/blog/2025-03-19-measuring-ai-ability-to-complete-long-tasks/)); the constraint on adoption in banks and insurers is not capability — it is governance sign-off.
2. **The bottleneck flips from generation to governance.** When code is cheap, the expensive question becomes "prove this change obeyed our rules." Signal: platform teams everywhere are hand-rolling CLAUDE.md / AGENTS.md conventions — prose, unverified, silently drifting, enforced by nothing ([users filing bugs asking for an enforcement mechanism](https://github.com/anthropics/claude-code/issues/7777)).
3. **Auditors start asking about AI-generated changes.** Signal: [EU AI Act obligations phasing in through 2027](https://artificialintelligenceact.eu/implementation-timeline/); model-risk frameworks ([SR 11-7](https://www.federalreserve.gov/supervisionreg/srletters/sr1107.htm) lineage) already require demonstrable control over automated decision systems; [SOC 2 auditors are beginning to ask how AI-written code is reviewed](https://omnithium.ai/blog/ai-agent-compliance-soc2-iso-eu-ai-act.html).
4. **Policy-as-code is the proven pattern, with a hole in it.** [OPA](https://www.openpolicyagent.org/) and [Sentinel](https://developer.hashicorp.com/sentinel) govern *infrastructure*. Nothing governs the *intent behind application code* — the invariants, formulas, and "why it must be this way" that agents most reliably violate. Signal: the category exists, is bought by enterprises, and stops at the Terraform boundary.

**The unnamed abstraction:** every organisation adopting agents needs a *deterministic control plane for AI-written code* — machine-readable rules derived from its own documentation, bound to the code they govern, enforced without a model in the loop, and reportable to an auditor. Nobody has named this category. The namer owns it.

## The idea

**Fux Fleet** scales the existing Fux engine from one repo to an organisation — by federation, not by platformisation. Three layers with a hard separation:

### Layer 1 — Engine (exists, never changes character)

Per-repo `fux`. `$0`, stdlib-only, deterministic. Rules bound to exact lines; agents read the *why* before touching code (hooks/MCP — [fux/hooks.py](../fux/hooks.py), [fux/mcpserver.py](../fux/mcpserver.py)); drift detected by AST, never by a model ([fux/verify.py](../fux/verify.py)); [`fux gate`](../fux/gate.py) blocks in CI. Status of everything shipped: [fux-implementation.md](fux-implementation.md); design of record: [fux-plan.md](fux-plan.md); command surface: [cli.md](cli.md). This layer stays MIT and free forever — it is the substrate the whole bet stands on.

### Layer 2 — Federation (the build)

The org's rule base, distributed like code:

- **Rule packs in git.** Versioned, namespaced packs (`org/`, `payments/`, repo-local) consumed like dependencies. No registry server — git *is* the registry. Precedence model: org → division → team → repo, with a deterministic conflict finding when active rules contradict.
- **Ratification as PR review.** A rule change is a pull request; CODEOWNERS routes it to the rule's owners; approval *is* ratification. We inherit GitHub's permissions and audit trail instead of building workflow software.
- **Ingest as the cold-start killer.** The org already wrote its rules — in Confluence, Jira, ADRs, OpenAPI specs. The existing connector-ingest pipeline ([ingest skill](../fux/data/skills/ingest/SKILL.md), [fux/ingestconnector.py](../fux/ingestconnector.py)) drafts the rule base from that corpus; humans ratify in bulk. Authoring cost drops from "write rules for 500 repos" to "review drafts."

### Layer 3 — Plane (the horizon — deferred by decision)

A read-only aggregation surface. Every `fux gate` run emits a JSON report artifact; the Plane collects them into what the *buyer* needs: fleet-wide coverage, violations blocked per team, rule staleness, and one-click compliance exports ("every agent-generated change in Q3, and the ratified rule that governed it"). The engine never phones home — the Plane consumes artifacts. That separation is the compliance story.

**Status: deferred.** Council call (see Decision record): building enterprise features for a fleet that doesn't exist yet is the pre-mortem's cause of death #2. The Plane activates on one trigger only — an enterprise design partner arriving with budget. Until then it is a horizon, not a build item.

## The loop — not a gate, a control system

A gate that only says *pass/fail* leaves a human holding every failure. Fleet closes the loop: **every blocking finding is a remediation instruction an agent can act on**, not a verdict a human must interpret.

Concretely: when `fux gate` blocks, it emits each finding in agent-readable form — the rule, its *why*, the exact governed lines, observed vs expected — rendered as a ready-to-execute fix prompt. The agent's next turn is determined: fix the code to satisfy the rule, or, if the rule itself is now wrong, open a rule-amendment PR for ratification. Then the gate re-verifies. The human enters only at the ratification boundary — exactly where judgment belongs.

The loop runs both directions:

- **Code drifted from rule** → finding tells the agent what to restore and why → agent fixes → gate re-verifies green. If the agent believes the rule is stale, it cannot ignore it — it must propose the amendment through ratification.
- **Source drifted from rule** (the Jira ticket closed differently, the Confluence page changed, the OpenAPI spec dropped an endpoint) → `--recheck` flags source-drift → the finding instructs the agent to re-draft the rule from the updated source → the re-draft lands in the review queue for human ratification.

The `$0` law holds throughout: the engine never *calls* a model — it *speaks to* models. Deterministic findings in, probabilistic fixes out, deterministic re-verification. Detect → explain → instruct → verify, until green. That's the difference between a linter with opinions and a control system: the steady state is *compliance*, not a backlog of violations.

## The wedge — inverted by council decision

**The wedge is the developer's felt pain, bottom-up:** *"Your CLAUDE.md is a suggestion. Fux is enforcement — and the agent fixes itself."* The adopter is the engineer already maintaining 200 lines of rules the agent ignores — a mass, daily, searchable pain (see Signal check, pain #1). Launch channel: Show HN / dev.to / Reddit, free, open source, one GIF of the loop. No procurement, no sales motion, no entity required.

**Compliance is the expansion, not the wedge.** The regulated-fintech story — "agent-generated PRs, provably governed, audit export included" — is what the *paying* buyer eventually needs, and it activates top-down only when a design partner shows up with budget. Original reasoning preserved: one team that can finally say yes to agents where compliance said no; the pack they ratify seeds the next team. But an open-source solo project cannot run that motion first — devs adopt bottom-up, enterprises follow the ubiquity.

**Instance zero: Anton.** Fleet is dogfooded before it is sold. Anton (AlphaForge) is already Fux's pilot — rules grounded in `aggregator.py`, with the brokers pilot and legacy-store decommission queued ([fux-implementation.md — dogfooding status](fux-implementation.md)). The Fleet build lands there first: a personal pack shared across `anton` + `fux` proves Federation at n=2; R1 scoped injection, R3 freshness on ingested broker/API sources, and R4's coverage gate all pay off first-hand in a money-critical codebase before any external claim is made. The demo repos in "First move" *are* these repos.

## The money — sequenced behind ubiquity

Open-core, with the split drawn where enterprises actually pay — but monetization is *deferred*, not designed away. In a forming category, ubiquity of the free substrate is the asset; premature paid tiers are how early tools lose the category to a later free one.

- **Free forever:** the engine, federation (packs, precedence, PR-ratification, ingest), the loop. Everything a single team needs. This is what wins the category, and it is the *entire* near-term strategy.
- **Paid — the Plane (on trigger):** fleet dashboard, compliance exports, retention, SSO/RBAC, per governed repo per month. The compliance export converts "nice dev tool" into "audit requirement line-item," and audit line-items don't get cut. Built when — and only when — an enterprise design partner arrives with budget.
- **Realistic ceiling:** platform-engineering budget line next to Snyk/SonarQube-class spend. Mid-six-figures ARR from a handful of regulated logos once the Plane exists; the category-ownership upside beyond that is real but not the base case.

## The moat

1. **Determinism is structural, not a feature.** Every competing "AI guardrail" puts a model in the enforcement path — which means it cannot go in front of an auditor, cannot run air-gapped, and costs per-token at fleet scale. Fux's enforcement path is `$0`, reproducible, and provable. A competitor cannot bolt this on; it is an architecture.
2. **The ratified corpus is the switching cost.** After a year, an org's Fux rule base *is* its institutional knowledge — ratified, versioned, bound to code. It compounds and it doesn't migrate.
3. **Category naming.** "Development governance" / "governed agentic development" — first credible open-source claim on the name wins the search results, the conference talks, and the default choice.

## The risk, named

**Platform capture.** GitHub or Anthropic ships a native governance layer and the default wins. Mitigation: the substrate is git-native, vendor-neutral, and open — position Fux as the *portable* standard the platforms can adopt rather than the product they kill. Move fast enough that the corpus exists before the platform feature does. Second risk: "CLAUDE.md + code review feels good enough" inertia — countered only by the wedge being a *compliance* story, not a productivity story; compliance doesn't accept "feels good enough."

## What this is not

Not a linter (lints check syntax; Fux checks *ratified intent*). Not an LLM guardrail (no model in the enforcement path, ever). Not a wiki (rules bind to lines and break loudly when code drifts). Not a platform (the engine stays small, sharp, per-repo — scale is federation). And not a mere gate — a gate reports failure; Fleet's findings *drive the repair*.

## Signal check — what people are actually complaining about (July 2026)

A pass over public developer pain (HN, Reddit, dev.to, GitHub issues, industry reports) validates the bet and adds roadmap items. Six pain clusters, each with the Fleet answer:

| # | Pain (with evidence) | Status |
|---|---|---|
| 1 | **"My CLAUDE.md gets ignored."** Widespread: rules files skipped past ~80 lines, delivered as low-priority context, [openly filed as bugs asking for an "enforcement mechanism"](https://github.com/anthropics/claude-code/issues/7777) ([200 lines of rules, ignored](https://dev.to/minatoplanb/i-wrote-200-lines-of-rules-for-claude-code-it-ignored-them-all-4639), [why it happens](https://dev.to/dylan_1e07ca370a5576/why-claude-code-ignores-your-claudemd-and-how-to-fix-it-2hip)) | ✅ Core thesis: prose is a suggestion, Fux is enforcement. **→ Roadmap R1** sharpens the fix |
| 2 | **Architectural drift** — agents default to *common over custom*; [documentation alone doesn't stop it](https://dev.to/vuong_ngo/ai-keeps-breaking-your-architectural-patterns-documentation-wont-fix-it-4dgj); teams hand-roll ["convention as code" scripts + CI](https://dev.to/monarchwadia/convention-as-code-enforcing-architecture-with-scripts-ci-and-ai-agents-hgd) | ✅ That hand-rolled pattern *is* `fux verify` + `gate`. **→ R6** packages it |
| 3 | **AI tech-debt at scale** — [1.7× more issues than human code, 30–40% of snippets with a CWE](https://www.secondtalent.com/resources/ai-generated-code-quality-metrics-and-statistics-for-2026/); "comprehension debt": merged code nobody understands; [governance magnifies or erodes quality](https://itbrief.co.uk/story/ai-coding-tools-may-raise-enterprise-software-risk) | 🟡 Coverage report exists. **→ R4** turns it into a gate for new critical code |
| 4 | **Silent spec–code drift** — the [dominant complaint in spec-driven development](https://arxiv.org/pdf/2606.27045): code evolves, spec doesn't; spec-first tools let the spec go stale | ✅ Drift detection is the engine's heart. **→ R5** makes Fux the enforcement layer *under* SDD tools |
| 5 | **Audit gap** — enterprise auditors now ask *who/what/why* per agent change; [attribution must be logged at execution time, not reconstructed](https://www.augmentcode.com/guides/multi-agent-outputs-n-pass-enterprise-audit); [only ~38% of orgs monitor AI activity end-to-end](https://omnithium.ai/blog/ai-agent-compliance-soc2-iso-eu-ai-act.html) | 🟡 Ratification trail exists. **→ R2** adds execution-time attribution receipts |
| 6 | **Stale wikis poison agents** — [a Confluence page looks identical reviewed last week or 3 years ago](https://community.atlassian.com/forums/App-Central-articles/Your-Confluence-wiki-is-confidently-giving-people-wrong/ba-p/3192612); [agents treat outdated docs as 100% true](https://www.techempower.com/blog/2026/06/16/what-if-the-repository-replaced-your-wiki-and-agents-maintained-it/); no test suite goes red for docs | 🟡 `--recheck` exists but is manual/opt-in. **→ R3** makes freshness continuous |

The strongest validation: pains 1, 2, and 4 are the product's existing core, being independently reinvented as one-off scripts by teams everywhere. The gaps are 3, 5, 6 — all closable with the primitives already built.

## Roadmap (signal-driven)

- **R1 — Scoped rule injection ("kill the CLAUDE.md tax").** Hooks/MCP serve *only* the rules governing the files being touched — ranked, capped, small. The 80-line attention limit stops mattering when context is 5 relevant rules instead of 200 lines of prose. Also the answer to context rot: deterministic scoped recall beats big memory. *(Engine; sharpen what [fux/touch.py](../fux/touch.py) / [fux/mcpserver.py](../fux/mcpserver.py) already half-do.)*
- **R2 — Attribution receipts.** `fux gate --json` records execution-time evidence per governed change: agent/model/session identity, rule versions checked, ratification refs, verdict. The Plane's compliance export is then assembled from receipts, not reconstructed. This is the feature auditors are starting to require by name. *(Engine emits — [fux/gate.py](../fux/gate.py); Plane aggregates.)*
- **R3 — Freshness / trust decay.** Scheduled `--recheck` in CI; every rule carries a visible `last-verified`; sources unverified past a threshold get an advisory finding that instructs the agent to re-draft from the current source (the loop, applied to staleness). Kills "the wiki looks fine" silently-wrong docs. *(Engine + CI recipe; `--recheck` exists opt-in in the [ingest skill](../fux/data/skills/ingest/SKILL.md).)*
- **R4 — Coverage gate for new critical code.** Opt-in: an agent-authored *new* important file with no governing rule is a blocking finding — the agent must draft the why before the code can land. Directly targets comprehension debt: no ungoverned understanding enters the codebase. *(Engine; [fux/coverage.py](../fux/coverage.py) exists report-only today.)*
- **R5 — SDD interop.** Import Kiro / Spec Kit / plain `spec.md` specs as ingest sources so existing spec-driven teams get drift enforcement without switching workflow. Position: Fux is not a competing SDD tool — it's the layer that keeps *any* spec true. *(Ingest connector — [fux/ingestconnector.py](../fux/ingestconnector.py).)*
- **R6 — Starter convention packs.** Ship the conventions teams keep hand-rolling (layered-architecture boundaries, error-handling, naming, API-contract rules) as ready packs — the "convention as code" pattern productised, and the seed content for Federation. *(Packs — [fux/data/packs/](../fux/data/packs/).)*

Priority (revised by council): **R1 + the loop first** — it serves the wedge *and* runs the falsification experiment the pre-mortem demands (does enforcement survive contact with deadlines?). R3/R4 ride the next train; R6/R5 are Federation adoption accelerants; **R2 moves with the Plane** — attribution receipts are what the paying buyer needs, and the paying buyer is on the horizon, not the roadmap.

## First move

1. **Build R1 + the loop, live in it.** Scoped rule injection and finding-as-fix-instruction, running in Anton daily. This is both the wedge feature and the experiment: if the loop doesn't stop *you* from bypassing the gate under deadline, the enforcement premise is wrong — find out before launching, not after.
2. **The eight-week gate (minority report, adopted):** no public launch before eight weeks of first-hand use. The tell to watch: Anton's rule base going stale, or you disabling the gate. Either one stops the launch and reopens the premise.
3. **The demo that sells the vision:** two repos (`anton` + `fux`) + one shared pack + a recorded run of an agent PR that violates a ratified rule, gets blocked by `fux gate` in CI, **receives the finding as a fix instruction, self-corrects, and goes green.** One GIF of the full loop; it *is* the Show HN.
4. **Ten conversations, dev-side:** engineers maintaining a CLAUDE.md — "does your agent actually follow it?" (The compliance-side conversations move to the Plane trigger.)

## Decision record — council, July 2026

Pressure-tested by a five-seat council (devils-advocate, pre-mortem, visionary, product-gtm, tenth-man). **Chair's call: keep the vision, invert the go-to-market.** Wedge flipped from compliance-first to developer-pain-first; Plane deferred to an explicit trigger; R2 re-sequenced with it; eight-week Anton dogfood gate adopted before any launch.

**Cruxes identified:** (1) bottom-up dev pain vs top-down compliance as the wedge — resolved: bottom-up first, compliance on trigger. (2) Does enforcement survive contact with deadlines, or die by config flag like every muted linter? — unresolved by argument; falsifiable in Anton via R1 + the loop. That experiment is first move #1.

**Minority report (devils-advocate, standing):** "Even reframed, this dies on curation. Rules are a garden; nobody pays the gardener. If the author's own rule base is stale by September, no launch."

**What flips the call:** an enterprise design partner with budget → re-elevate the Plane and R2. R1 + loop failing in Anton (violations persist, or the author bypasses his own gate) → stop; the enforcement premise itself is wrong.

## References

### Internal (this repo)

- [fux-plan.md](fux-plan.md) — design of record for the engine
- [fux-implementation.md](fux-implementation.md) — status tracker, incl. Anton pilot & pending dogfood runs
- [cli.md](cli.md) — command surface
- [README.md](../README.md) — public positioning ("records *why* — and checks it's still true")
- Engine modules cited above: [gate.py](../fux/gate.py) · [verify.py](../fux/verify.py) · [hooks.py](../fux/hooks.py) · [mcpserver.py](../fux/mcpserver.py) · [touch.py](../fux/touch.py) · [coverage.py](../fux/coverage.py) · [ingestconnector.py](../fux/ingestconnector.py) · [data/packs/](../fux/data/packs/) · [ingest skill](../fux/data/skills/ingest/SKILL.md)

### Community pain (the signal base)

- [I Wrote 200 Lines of Rules for Claude Code. It Ignored Them All](https://dev.to/minatoplanb/i-wrote-200-lines-of-rules-for-claude-code-it-ignored-them-all-4639) — dev.to
- [Why Claude Code Ignores Your CLAUDE.md (And How to Fix It)](https://dev.to/dylan_1e07ca370a5576/why-claude-code-ignores-your-claudemd-and-how-to-fix-it-2hip) — dev.to
- [claude-code#7777 — Claude ignores instructions in CLAUDE.md and agents](https://github.com/anthropics/claude-code/issues/7777) — GitHub issue
- [AI Keeps Breaking Your Architectural Patterns. Documentation Won't Fix It](https://dev.to/vuong_ngo/ai-keeps-breaking-your-architectural-patterns-documentation-wont-fix-it-4dgj) — dev.to
- [Convention as Code: Enforcing Architecture with Scripts, CI, and AI Agents](https://dev.to/monarchwadia/convention-as-code-enforcing-architecture-with-scripts-ci-and-ai-agents-hgd) — dev.to
- [AI agents break rules under everyday pressure](https://news.ycombinator.com/item?id=46067995) — Hacker News
- [Your Confluence wiki is confidently giving people wrong information right now](https://community.atlassian.com/forums/App-Central-articles/Your-Confluence-wiki-is-confidently-giving-people-wrong/ba-p/3192612) — Atlassian Community
- [What if the Repository Replaced Your Wiki (and Agents Maintained it)](https://www.techempower.com/blog/2026/06/16/what-if-the-repository-replaced-your-wiki-and-agents-maintained-it/) — TechEmpower

### Research

- [The Spec Growth Engine: Spec-Anchored, Code-Coupled, Drift-Enforced Architecture](https://arxiv.org/pdf/2606.27045) — arXiv (silent spec–code drift)
- [Codified Context: Infrastructure for AI Agents in a Complex Codebase](https://arxiv.org/pdf/2602.20478) — arXiv
- [Beyond the 'Diff': Addressing Agentic Entropy in Agentic Software Development](https://arxiv.org/pdf/2604.16323) — arXiv
- [Asymmetric Goal Drift in Coding Agents Under Value Conflict](https://arxiv.org/pdf/2603.03456) — arXiv
- [Measuring AI Ability to Complete Long Tasks](https://metr.org/blog/2025-03-19-measuring-ai-ability-to-complete-long-tasks/) — METR

### Industry & compliance

- [AI-Generated Code Quality Metrics and Statistics for 2026](https://www.secondtalent.com/resources/ai-generated-code-quality-metrics-and-statistics-for-2026/) — Second Talent (1.7× issue rate, CWE prevalence)
- [AI coding tools may raise enterprise software risk](https://itbrief.co.uk/story/ai-coding-tools-may-raise-enterprise-software-risk) — SIG State of Software 2026 (governance magnifies or erodes quality)
- [What Multi-Agent Outputs Need to Pass Enterprise Audit: Attributability and Reversibility](https://www.augmentcode.com/guides/multi-agent-outputs-n-pass-enterprise-audit) — Augment Code
- [AI Agent Compliance: Navigating SOC2, ISO 42001, and the EU AI Act](https://omnithium.ai/blog/ai-agent-compliance-soc2-iso-eu-ai-act.html) — Omnithium (~38% end-to-end monitoring stat)
- [EU AI Act implementation timeline](https://artificialintelligenceact.eu/implementation-timeline/)
- [SR 11-7: Guidance on Model Risk Management](https://www.federalreserve.gov/supervisionreg/srletters/sr1107.htm) — Federal Reserve

### Policy-as-code precedents

- [Open Policy Agent](https://www.openpolicyagent.org/) — the infra-governance pattern Fleet extends to code intent
- [HashiCorp Sentinel](https://developer.hashicorp.com/sentinel)

---

*Next: the plan — R1 + loop first (engine), then federation (packs + precedence), ratification flow after; Plane on trigger only.*
