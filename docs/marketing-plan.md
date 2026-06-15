# Fux & Cage — Go-to-Market Plan

> Fux-led, Cage second. Anton is the proof, not the pitch.
> Status: draft v1 · owner: Arpit · last updated: 2026-06-14

---

## 0. The 30-second context

**Anton** (AlphaForge Anton) is a self-hosted AI investment terminal for Indian
markets. It aggregates seven brokers into one INR-correct portfolio and layers
**Orff**, a multi-provider AI concierge that composes live UI in chat — without
financial data leaving the machine.

Anton didn't grow one big app. It grew a **family of small, single-purpose,
deterministic tools**, each owning one concern a finance app must get right:

| Sibling | Owns | Public-OSS potential |
|---|---|---|
| **fux** | Knowledge engine — rules/formulas/memory that ground both Claude Code and Orff | **High — lead product** |
| **cage** | Token + savings ledger — what you spent, what each tool saved, counterfactuals | **High — second launch** |
| bach | Encrypted secrets vault (local daemon) | Medium (later) |
| wagner | IAM / multi-user auth | Low (commodity space) |
| dante | Security audit (10 "circles") | Medium (later) |
| elgar | Private plan store (money docs never touch the repo) | Low (niche) |

This plan is about the two with the broadest developer appeal — **fux and
cage** — because they solve problems that *every* AI-assisted codebase has, not
just a finance app. Anton is the credibility: a real, non-trivial system these
tools already run in production-for-one.

---

## 1. Why these two are the products to launch

The wider market is drowning in AI coding tools that are **probabilistic,
heavyweight, and lock you to one vendor**. Fux and Cage share a spine that is the
opposite, and that spine *is* the wedge:

- **`$0` and stdlib-only** — no third-party runtime deps, no mandatory LLM calls.
- **Deterministic** — same input ⇒ same output. No hallucinated numbers.
- **Substrate → derived views** — you maintain one source of truth; everything
  else regenerates for free.
- **Tool-agnostic** — they target a *protocol* (a rule schema, a wire format),
  never a named vendor. Works with Claude Code, Codex, Copilot, any client.

This is a *family* with a shared philosophy (alongside the earlier `graphify`:
code → graph). That coherence is a marketing asset — it lets each launch lift the
next, and it tells a bigger story than any single tool: **a deterministic
substrate layer underneath the probabilistic AI-dev stack.**

---

## 2. Positioning — the wedge sentences

The wedge is one sentence that makes the product feel inevitable and that a
competitor *cannot say about themselves*.

### Fux (primary)

> **Memory tools record what your agent did. Fux records *why* your code is the
> way it is — and checks it's still true.**

Why it holds:
- Names the category everyone knows (agent memory / context tools).
- The structural gap competitors can't claim: memory tools *capture* (probabilistic,
  auto-summarised); Fux is *authored + verifiable* — `fux seal` binds a rule to an
  AST fingerprint, `fux check` flags when governed code drifts. "Checks it's still
  true" is the part a capture-based memory tool literally cannot do.
- Survives the double *so what*: it's verifiable → so your AI doesn't reason against
  invariants that silently changed → so you stop shipping AI edits that break the
  *why* nobody wrote down.

**Sub-wedge for the cost angle (use in HN comments, not the headline):**
"Every Fux maintenance command is shell/AST/parse — no LLM calls. `fux savings`
measures the token-cost win from your own files instead of asking you to trust it."

### Cage (second)

> **You're paying for five AI tools and have no idea which one is saving you
> money. Cage meters every call, collects a savings receipt from each tool, and
> tells you what any *other* combination would have cost — every number tagged
> measured, modeled, or estimated.**

Why it holds:
- Names the real, current pain: a stack of AI tools with opaque, overlapping spend.
- Structural gap: dashboards show *spend*; Cage shows *attributed savings +
  counterfactuals*, and never lets a projection masquerade as an invoice.
- The `measured / modeled / estimated` tag is the trust primitive — it's the thing
  a generic "LLM cost tracker" can't claim.

**Category bid (the visionary line, use sparingly):**
"graphify turned code into a graph. fux turned decisions into verifiable rules.
Cage turns AI-tool traffic into an honest ledger. Three deterministic substrates
under the probabilistic stack."

---

## 3. Narrative — the enemy and the inevitable future

**The enemy (Fux):** your codebase's *reasons* live in people's heads and in
inline comments nobody greps, and they rot silently. Your AI agent confidently
edits against invariants that no longer hold because nothing ever checked.

**The enemy (Cage):** the AI-dev stack is a black box of overlapping subscriptions.
You can't tell your boss — or yourself — which tool earned its seat.

**The inevitable future (state it with conviction, let people argue):**
> Once verifiable, deterministic context is normal, shipping AI changes against
> undocumented invariants will look as reckless as deploying without tests — and
> running a stack of AI tools without an honest savings ledger will look like
> running cloud infra with no billing dashboard.

The argument *is* the distribution. The category you're naming: **the
deterministic substrate layer** beneath probabilistic AI tooling.

---

## 4. Audience & where they hang out

| Segment | Why they care | Find them |
|---|---|---|
| Claude Code / Codex / Copilot power users | Fux plugs straight into their agent hooks; Cage meters their spend | r/ClaudeAI, HN, X AI-dev circle |
| Staff/principal eng on large codebases | "Why is this code like this" rot is their daily tax | HN, Lobsters, r/ExperiencedDevs |
| AI-agent / tooling builders | Tool-agnostic protocol, MCP server, deterministic graph | r/LocalLLaMA, MCP community, X |
| Cost-conscious eng leads / indie devs | Cage's attribution + ROI per tool | HN, r/programming, X build-in-public |
| OSS / dev-tool enthusiasts | `$0`, zero-dep, stdlib-only is catnip | Lobsters, HN, Product Hunt |

---

## 5. Channel plan & sequencing

Do **not** launch everywhere at once. Each wave sharpens the next and you capture
attention (stars, emails, follows) between them. Fux runs the full sequence first;
Cage follows ~4–6 weeks later and reuses the proven copy.

### Wave 0 — Soft launch / copy-hardening (week 1)
- Post Fux in **one friendly small audience**: r/ClaudeAI or the MCP/Claude Code
  Discord, framed as "built this for my own agent setup, rough edges welcome."
- Goal is not reach — it's to *harvest the exact words* people use and fix the hook
  before the big stage. Watch which sentence they repeat back to you; that becomes
  your headline.

### Wave 1 — Show HN (week 2, the centerpiece)
- The highest-signal technical crowd and the hardest to fake. Win here and the rest
  rides the wake.
- Title (plain, < 80 chars, no adjectives):
  `Show HN: Fux – records why your code is the way it is, and checks it's still true`
- Pre-write the first comment (see §6). Be present for the first 2 hours, reply to
  every critic generously, never ask for upvotes.

### Wave 2 — Product Hunt (within 1–2 days of HN, while momentum is live)
- Ride the HN result; point to it as social proof.
- Non-negotiable: a **demo GIF** showing `fux why <id>` → the rule + its *why* + the
  governed code in the first 3 seconds, then the Solar Terminal graph igniting.
- Launch 12:01am PT, Tue–Thu. Maker present all day.

### Wave 3 — Long-form dev.to / blog article (week 2–3, the durable asset)
- The compounding piece. Teach, don't sell. Strong angle:
  **"Your AI agent reasons against invariants that silently changed — here's a
  $0, deterministic way to catch it."** (the contrarian/problem deep-dive)
- Real code, the AST-fingerprint `fux seal` mechanism, a diagram of the
  substrate → INDEX/graph/memory tiers, and the honest "what it doesn't do yet."
- Canonical-link to the repo. This becomes the thing you *link* in Reddit/HN
  comments later — real material, not spam.

### Wave 4 — Reddit, seeded from real discussion (week 3+)
- Problem-first titles, product as a footnote, one sub at a time:
  - r/ClaudeAI, r/LocalLLaMA — agent/hook angle
  - r/ExperiencedDevs — the "code reasons rot in people's heads" angle
  - r/programming — the `$0` deterministic angle (strict self-promo ratio; lead with the essay)
- Respect each sub's self-promo ratio. You're a member who built something, not a
  marketer who showed up.

### Wave 5 — X / build-in-public (continuous, underneath all of it)
- Don't treat X as a launch-day spike — run it as the connective tissue:
  - The wedge thread on launch day (thread = the dev.to article, compressed).
  - Ongoing: short demo clips (the graph viewer is *visually* striking — use it),
    one honest tradeoff per post, the family story (graphify → fux → cage).
  - Reply to people complaining about exactly the problem Fux/Cage solve.

### More channels worth a shot (lower priority, opportunistic)
- **Lobsters** — even more deterministic/zero-dep-friendly than HN; great fit, but
  invite-only and ratio-strict. Post the article, not an ad.
- **MCP server directories / awesome-lists** — `fux mcp` and Cage's planned MCP make
  them legitimately listable. Cheap durable backlinks + discovery.
- **Claude Code / Codex plugin & skill ecosystems** — Fux ships skills and hooks;
  being in the relevant marketplace/registry is distribution you don't have to
  re-earn.
- **Hacker Newsletter / Console.dev / TLDR-style dev newsletters** — submit the
  article once it has HN traction; they pull from there.
- **GitHub itself** — the README *is* a landing page. Topics/tags, a sharp hero
  line, a demo GIF at the top, and a pinned repo on your profile.
- **Show & tell in the Anthropic / Claude developer community** — Fux is genuinely
  a Claude-aware tool; that's a native, non-spammy fit.

---

## 6. Drafted copy (paste-ready, then iterate)

### Fux — Show HN first comment (pre-write, post immediately)

> I build a self-hosted investing terminal (Anton) where an AI concierge composes
> live UI and answers questions about my portfolio. The recurring failure wasn't
> the model — it was that the *reasons* behind my code (why current value not
> invested cost, why INR-normalise first, which cost-basis method) lived in inline
> comments the agent never read, and went stale the moment the code moved.
>
> Fux is my fix. You author each rule once — *what* and *why* — and Fux derives a
> one-line INDEX (read first, cheap), lazily-opened rule files (read only when
> relevant), and a code↔knowledge graph. `fux seal` binds a rule to an AST
> fingerprint of its code, so `fux check` tells you when the governed code changed
> *structure* and the rule might be stale. Every maintenance command is
> shell/AST/parse — no LLM calls, zero third-party deps, Python stdlib only.
>
> What it does NOT do yet: the semantic re-rank and hybrid recall are opt-in and
> early; the non-Python AST extraction is a brace-matched heuristic by default
> (real tree-sitter is an optional extra); and "authored, not captured" means it
> asks you to write the *why* — it won't invent it for you.
>
> I'd love feedback on one thing specifically: is AST-fingerprint sealing the right
> primitive for "this rule may be stale," or is that too coarse? Repo: <link>

### Fux — README hero (top of repo, above the fold)

> **Fux records *why* your code is the way it is — and checks it's still true.**
> A portable, agent-aware knowledge engine. One frontmatter substrate → derived
> index, graph, and memory. `$0`, deterministic, stdlib-only — no mandatory LLM
> calls. `pip install`, point it at your repo, `fux why <id>`.

*(Add a demo GIF here: `fux why day-pnl` → rule + why + governed code, then the
graph viewer igniting the `governs` links.)*

### Fux — X launch thread (opening posts)

> 1/ Your AI agent knows what it changed last week. It has no idea *why* that
> function can't be touched — and neither does the new hire.
>
> 2/ Memory tools fix the first problem by recording what the agent *did*. That's
> the easy half. The hard half is the *why* behind the code — and whether it's
> still true after the code moved.
>
> 3/ So I built Fux. You write each rule once (what + why). It derives a cheap
> one-line index your agent reads first, plus rules it opens only when relevant —
> and `fux seal` binds each rule to an AST fingerprint so it can tell you when the
> code drifted out from under it.
>
> 4/ Every maintenance path is shell/AST/parse. No LLM calls, zero deps, stdlib
> only. `fux savings` measures the token win from your own files — you don't have
> to take it on faith. <repo>

### Cage — Show HN title + first-comment seed (for the second launch)

> `Show HN: Cage – an honest ledger for what your AI-tool stack costs and saves`

> First comment: I run a few deterministic context tools (a code-graph, a rules
> engine) in front of my LLM calls, and I couldn't answer a basic question: which
> one is actually saving me money? Cage meters every call and collects a *savings
> receipt* from each tool, then derives attribution + a counterfactual matrix —
> what the full stack cost vs. what any other combination would have. Every cell is
> tagged `measured` / `modeled` / `estimated`, so you always know which numbers are
> invoices and which are projections. `$0`, stdlib-only, fail-open (a metering
> error never breaks your call). What's not done yet: the OpenAI-compat proxy and
> the plugin are next; Shapley attribution is a deferred opt-in. `cage demo`
> reproduces the worked example against a real ledger. <repo>

### Cage — README hero

> **You pay for five AI tools and can't say which one earns its seat. Cage meters
> every call, collects a savings receipt from each tool, and shows what any other
> combination would have cost — every number tagged measured, modeled, or
> estimated.** `$0`, stdlib-only, deterministic, fail-open.

---

## 7. The family story (the multiplier)

Tell this once the individual tools have landed — it converts users into people
who repeat your worldview:

> **graphify** turns code into a graph. **fux** turns decisions into verifiable
> rules. **cage** turns AI-tool traffic into an honest ledger. Same constitution
> every time — `$0`, stdlib-only, deterministic, substrate → derived views, no
> model in the maintenance path. A deterministic layer underneath the
> probabilistic AI-dev stack.

Use Anton as the proof-of-life: "these aren't demos — they run a real seven-broker
investing terminal with an AI concierge today." Show, don't claim.

---

## 8. Metrics — what to watch, what to cut

**Leading signals (within the launch window):**
- Comment depth/quality > raw upvotes.
- GitHub stars-per-hour during the first 6h of each wave.
- "How do I use this for X?" questions = product-market pull.
- People explaining the tool to *each other* in the thread = the wedge landed.

**Kill criteria:** a channel that sends traffic but no stars means the *copy or
fit* is off — fix the hook before abandoning the channel.

**Double-down signals:** one thread outperforming 5× → write the follow-up, turn
the top comment into the next headline, go deeper on whatever resonated.

**Always harvest language:** the exact words people use to describe the tool back to
you are your next headline. Steal them.

**Capture between waves:** every star, email, follow. Attention you don't capture
evaporates.

---

## 9. Pre-launch checklist (do before Wave 1)

- [x] **Fux README hero rewritten** — leads with the verifiability wedge; demo-GIF
      slot added at the top. *(GIF itself: capture per `docs/launch/gif-storyboard.md`.)*
- [x] **One-command install verified** — `init → new → build → why → savings` runs
      clean; full record in `docs/launch/install-verification.md`. One follow-up:
      re-run on a real macOS/3.14 box (sandbox couldn't reach the Python mirror).
- [x] **Show HN first comment pre-written** — `docs/launch/show-hn.md` (title +
      first comment + pre-loaded answers to the tough questions).
- [x] **dev.to article drafted** — `docs/launch/devto-article.md` (teaching-first,
      product as payoff). Publish in Wave 3.
- [x] **Name decision made** — keep **Fux**; README etymology tightened with a
      "(The name is deliberate.)" so it reads as a choice, not an accident.
- [ ] **Demo GIF recorded** — the one item needing your screen; storyboard + capture
      script ready in `docs/launch/gif-storyboard.md`.
- [ ] **Landing / pinned-repo state** — README is the landing page; once the GIF is
      in, pin the repo and add GitHub topics. Confirm it survives a front-page spike.
- [ ] **Cage** left for the second launch; don't split attention on day one.

---

## 10. One-line summary

Lead with Fux's verifiability wedge on Show HN, harden the copy in a soft launch
first, ride HN into Product Hunt and a teaching article, then run Reddit and X off
that real material — and launch Cage the same way 4–6 weeks later, with the
"deterministic substrate family" story tying both to Anton as living proof.
