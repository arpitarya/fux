---
type: Proposal
name: consumer-intent-policy
title: "Fux states the fact; the consumer states the policy — archived results across reader intents"
description: "The same archived document is authoritative, misleading or dangerous depending on why it was asked for. Rather than Fux carrying a taxonomy of reader intents, the engine emits an intent-neutral fact and ships policy files that agent consumers (Claude, Copilot, Kiro) load natively. Three layers, one fact, N policies."
status: graduated
timestamp: 2026-08-22T00:00:00Z
---

# Fux states the fact; the consumer states the policy

> **Status: GRADUATED, 2026-08-22 — same day.** Arpit accepted the layering and
> asked for a record: **[ADR-AGENT-POLICY](../../docs/adr/0035_agent-policy.md)**.
> **That record is now the decision; this file is kept as the research and the
> reasoning that produced it, and may be named but not cited as authority.**
> The four renderings moved to their real home at
> [`src/fux/templates/agents/`](../../src/fux/templates/agents/) — one copy, not
> two. **Opened by Arpit** on noticing the archived disclaimer was written for
> one reader.

## The observation that opened this

[ADR-DIR-LIST](../../docs/adr/0022_dir-list.md) decision 12 originally read:

> *archived content may be named, but the build is based on the records*

**It assumes the reader is building.** Arpit's point: Fux is queried from at
least three stances, and *"maybe more — there could be"*. That last clause is
the load-bearing one, and §3 turns it into the design.

## §1 — The same document, three meanings

| the question | stance | archived content is | the reader wants |
|---|---|---|---|
| *why did we choose SQLite* | history · business | **the answer** | to read it as authoritative **for its period** |
| *how does ingest work now* | architecture | **misleading** | the live document, with this as contrast |
| *implement the ingest cache* | an agent building | **dangerous** | never to port from it |

**The third row is not hypothetical.** This repository's own probe returned
**5/5 archived documents** for *"what is the ingest cache"*, describing the
per-file cache — a subsystem `CLAUDE.md` explicitly forbids porting back. A
build agent acting on that answer reintroduces a deleted design, confidently.

**And the first row is why demotion alone does not solve it.** A business reader
asking *why* is served **best** by the archived document. Push it down and the
tool gets worse at one of its jobs to get better at another.

## §2 — Three layers, and each has exactly one owner

| layer | owner | says | mechanism |
|---|---|---|---|
| **the record** | Fux, at ingest | `archived: true` | declared on a `dirs` line, never derived from a path |
| **the disclaimer** | Fux, at output | *what archived **is*** | a response-level note; `"archived": true` in `--json` |
| **the policy** | **the consumer** | *what to **do** about it* | a skill / instructions / steering file the agent already loads |

**The split is the proposal.** Everything else follows from it.

### Why the fact belongs to Fux

A rule enforced by whether a reader notices a path prefix inside a context
window is a rule with no mechanism — ADR-DIR-LIST's own words. Fux's job is to
make the fact **unmissable and machine-readable**: a response-level note that
cannot be skimmed past, and a `--json` boolean a program can branch on without
parsing prose.

### Why the policy does not

Three reasons, and the second is the strongest:

1. **The intent list is open.** Arpit named three and said there may be more. An
   enum that is provably incomplete on the day it ships is worse than no enum,
   because it invites callers to squeeze a fourth intent into the closest of
   three.
2. **It is the precedent the engine already set.** The
   [refer plane](../../docs/adr/0030_refer-plane.md) returns
   `current` / `stale` / `unverified` and **refuses to collapse "we did not
   look" into "we looked and it was fine"** — the *caller* supplies the freshness
   policy, because *"three callers want three different answers from the same
   index, and no single engine-wide policy is right for more than one of them."*
   **Archived is the identical shape of claim.** Deciding it differently would
   make the engine inconsistent with itself.
3. **It is the product argument.** Fux's stated audience is agents. An engine
   that emits facts and a policy layer that interprets them is exactly
   index-and-refer applied one level up.

## §3 — Why not `fux ask --intent=build`

The obvious alternative, and it is rejected rather than ignored.

| | cost |
|---|---|
| **the taxonomy** | closed enum, open problem — it is wrong the moment someone asks a fourth kind of question |
| **the law** | policy moves inside the engine, which is what index-and-refer exists to avoid |
| **the surface** | a flag on `ask` that `find` and `answer` must then mirror ([ADR-FIND](../../docs/adr/0005_find.md) makes `find` a projection of `ask`) |
| **determinism** | none — intent does not enter the index, so **L3 is not threatened**. This is the one cost it does *not* carry, and saying so keeps the rejection honest |

**Kept as the reopen-trigger:** if consumers converge on the same three or four
intents in practice, a flag stops being a guess and becomes a shorthand for
something observed. Until then it is an invented taxonomy.

## §4 — What ships to consumers

**One policy, four native formats**, because an agent only reads the file its
own tooling loads. Drafts live beside this doc in
[`consumer-policy/`](consumer-policy/).

| consumer | file | mechanism |
|---|---|---|
| **Claude** (Code · Cowork) | `SKILL.md` in a skill directory | model-invoked; the `description` is what makes it fire |
| **GitHub Copilot** | `.github/agents/fux.agent.md` | a **custom agent** — `description`, `tools`, model-invocable and user-selectable |
| **GitHub Copilot** | `.github/instructions/fux-archived-results.instructions.md` | `applyTo:` glob — **ambient**, and not made redundant by the agent |
| **Kiro** (AWS) | `.kiro/steering/fux-archived-results.md` | `inclusion:` frontmatter — `always`, `fileMatch`, `manual` |

**The agent does not replace the instructions file.** They fire differently, and
the gap between them is the dangerous case: someone runs `fux ask` in a
terminal, pastes the output into Copilot chat, and **the agent was never
invoked** — but the archived results are still there. The ambient instructions
file is what covers that. Ship both.

**The shared policy, in one sentence each:**

1. Fux marks archived results. **Never drop the mark when summarising.**
2. **Establish the stance before using an archived result** — history, current
   architecture, or building.
3. **Never port code or design from an archived document.** Cite the live
   successor; if there is none, say so.
4. **If every result is archived, say that in the answer.** Presenting retired
   design as current is the failure this whole layer exists to prevent.
5. The mark is `"archived": true` in `--json`. **Branch on the field, not on the
   prose** — the prose wording is not a contract, the field is.

## §5 — `fux setup` installs them (Arpit, 2026-08-22)

**This was §5's open question and it is now answered: Fux ships them, through
`fux setup`.** The mechanism already exists and needs no new machinery —
`setup.py` reads `templates/` out of the wheel (`template_bytes`, *"read, never
imported"*) and lays files down with `_write_if_missing`, which is exactly the
write-if-missing, never-clobber semantics a consumer-owned file wants. The
fetchers already work this way.

So the build is **four more templates and four more `_write_if_missing` calls**.
That is not the hard part. The hard part is below.

### ⚠ This makes `fux setup` write outside its own namespace

Everything `fux setup` writes today lives in **fux's own territory** — `.fux/**`
and `fux.toml`. These files do not:

| file | lands in | whose namespace |
|---|---|---|
| `fux.agent.md` | `.github/agents/` | **GitHub's** |
| `fux-archived-results.instructions.md` | `.github/instructions/` | **GitHub's** |
| `steering-fux-archived-results.md` | `.kiro/steering/` | **AWS's** |
| `SKILL.md` | a skill directory | **Anthropic's** |

**A tool that installs itself into `.github/` on setup is doing something a user
may not expect**, and `.github/` in particular is a directory people treat as
theirs. Write-if-missing protects an *existing* file; it does not ask permission
to create a new one in someone else's folder.

**Three unresolved calls, and they are Arpit's:**

1. **Opt-in, opt-out, or unconditional?** A `fux setup --agents` flag, on by
   default, or always? The safe default is **opt-in with a loud line in
   `setup`'s output** naming what it would write.
2. **All four, or only the ones the repo shows signs of using?** Writing Kiro
   steering into a repo that has never seen Kiro is clutter. Detecting
   (`.github/` exists → Copilot; `.kiro/` exists → Kiro) is cheap but is a
   *heuristic*, and this project does not like heuristics — ADR-DIR-LIST
   decision 4 chose **declared, never derived** for exactly this reason. The
   consistent answer is a declaration, not detection.
3. **Which record owns it?** `src/fux/setup.py` belongs to
   **[ADR-DOTFUX](../../docs/adr/0003_fux-directory.md)** — *"the second
   scaffolding moment — the consumer-owned files, write-if-missing"*. That
   record is about **the `.fux/` directory**, and these files are the first
   things `setup` would write that are **not in it**. So either ADR-DOTFUX
   widens from "the `.fux/` layout" to "what setup lays down", or this earns its
   own record. **Naming that before the build is Law zero working as intended**
   — an agent that starts here will otherwise edit `setup.py` and discover mid-
   change that the owning record does not describe what it is doing.

### Drift is now Fux's problem, and it is not hypothetical

Between the first draft of these files and this revision — **inside one working
session** — GitHub's recommended surface moved from instructions files to
**custom agents**. Shipping means owning three vendors' formats as they move.
Two mitigations are in the design already: **write-if-missing** never overwrites
a consumer's edit, and a `policy-version` metadata key makes a stale file
identifiable rather than merely old. **Neither makes the maintenance go away.**

## §6 — What this still does not decide

- **Whether the disclaimer ships ahead of its instrument.** ADR-DIR-LIST
  decision 10 gates it, and that is Arpit's to lift. This proposal changes the
  *wording*, not the gate.
- **Whether an archived source should declare its successor.**
  `archive/README.md` already maps every archived doc to its live successor, but
  that is repo-level and the index cannot see it. A `successor=` attribute on a
  `dirs` line would let the disclaimer name where to look instead — and would
  break decision 3's one-attribute cap. **Out of scope; noted so it is not
  re-discovered.**

## Reference

- The wording this replaces, and the amendment:
  [ADR-DIR-LIST](../../docs/adr/0022_dir-list.md) decision 12.
- The precedent for caller-owned policy:
  [ADR-REFER](../../docs/adr/0030_refer-plane.md) and
  [`src/fux/refer/freshness.py`](../../src/fux/refer/freshness.py)'s module
  docstring — *"three callers want three different answers from the same index"*.
- The measured failure this addresses: the 5/5 archived probe in
  [W-44](../open/W-44-archived-content-signalling.md).
- Kiro steering files, format and inclusion modes — <https://kiro.dev/docs/steering/>
- GitHub Copilot repository and path-specific custom instructions —
  <https://docs.github.com/en/copilot/how-tos/configure-custom-instructions-in-your-ide/add-repository-instructions-in-your-ide>
