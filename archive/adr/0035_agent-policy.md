---
type: ADR
name: ADR-AGENT-POLICY
title: "ADR-AGENT-POLICY (0035) — Fux ships the policy its consumers need to read it correctly"
description: "Fux's readers are AI agents, and an engine whose output is misread is an engine that does not work. Fux emits intent-neutral facts and ships one canonical policy rendered into each agent's native format, installed by fux setup from a declaration, never from detection, and never clobbering a file the consumer owns."
status: accepted
date: 2026-08-22
feature: the agent-facing policy and skill artifacts Fux ships, and their installer
owns: [src/fux/templates/agents]
laws: [L1, L6]
timestamp: 2026-08-22T00:00:00Z
---

# ADR-AGENT-POLICY — shipping the policy, not just the facts

## §1 — For humans

**Fux's readers are agents.** That is the product's whole premise, and it has a
consequence worth writing down: **an engine whose output is systematically
misread is an engine that does not work**, however correct its index.
Correctness that does not survive the reader is not correctness.

The concrete case is archived documents.
[ADR-ARCHIVED-CONTENT](0037_archived-content.md) decision 7 makes Fux state a
**fact** — *this document is retired* — and deliberately **states no
conclusion**, because the right conclusion depends on why the question was
asked. That is the honest design, and it leaves a gap: *somebody* has to supply
the conclusion.

**This record says who: the consuming agent, using policy Fux ships.**

```mermaid
flowchart LR
    S[".fux/sources/dirs<br/>archived= declared"] --> I["ingest"]
    I --> R["record<br/>archived: true"]
    R --> O["ask · find · answer<br/>the FACT, no conclusion"]
    O --> A["the agent"]
    P["fux setup<br/>writes the policy + the skills"] --> A
    A --> ANS["an answer that<br/>knows what retired means"]
```

<details>
<summary><b>ASCII twin</b> — the same diagram, for terminals, diffs, and any reader without a Mermaid renderer</summary>

```text
  .fux/sources/dirs (archived=) --> ingest --> record: archived: true
                                                        |
                                                        v
                                    ask . find . answer  =  THE FACT
                                                        |    (no conclusion)
   fux setup  --> policy + skill files -------------------+--> the agent
                  (Claude . Codex . Copilot . Kiro)      |
                                                         v
                                        an answer that knows what retired means

  Fux states what IS. The agent decides what to DO. Neither alone is the mechanism.
```

</details>

### Examples

**What `fux setup` writes, and what it says about it:**

```console
$ fux setup                       # abridged: the usage/decoder/enrich skills
  wrote fux.toml                  # are written too, one folder each
  wrote .fux/sources/dirs
  wrote .claude/skills/fux-archived-results/SKILL.md
  wrote .codex/skills/fux-usage/SKILL.md
  wrote .github/agents/fux.agent.md
  wrote .github/instructions/fux-archived-results.instructions.md
  wrote .kiro/steering/fux-archived-results.md
  wrote AGENTS.md

  note: everything after .fux/sources/dirs is OUTSIDE .fux/ — it teaches
        Claude, Codex, Copilot and Kiro how to read this index. Turn them off
        with [agents] install = [] in fux.toml, or `fux setup --no-agents`.
```

**The announcement is the safeguard, not a courtesy.** These land in directories
GitHub, AWS and Anthropic own, so a user who did not want them must be able to
learn they exist from the terminal they just ran — not from a later `git status`
on a repository they share with a team.

**Opting out is a declaration, and it persists:**

```console
$ fux setup --no-agents
  wrote fux.toml          # [agents] install = []
  wrote .fux/sources/dirs
```

---

## §2 — For agents

### Context

Fux indexes retired documentation deliberately — it is the honest answer to
*"why does this look the way it does"* — and marks it rather than hiding it. The
disclaimer is **intent-neutral**: it says what archived *is* and stops, because
the same document is **the answer** to a history question, **misleading** to an
architecture question, and **dangerous** to a build task.

**The engine must not carry that taxonomy.** The list of stances is open, and a
provably incomplete enum invites callers to squeeze a fourth stance into the
closest of three. The [refer plane](0030_refer-plane.md) set the precedent — it
refuses to collapse *we did not look* into *we looked and it was fine*, because
**three callers want three different answers from the same index.**

So the policy lives with the caller. **The question this record answers is
whether Fux ships it.**

### Decision

**1. Fux ships agent policy, and it is a product decision rather than a
convenience.** A tool whose stated audience is agents, that emits a fact no
agent knows how to read, has shipped half a feature. **The measured case is this
repository's own**: *"what is the ingest cache"* returned **5/5 archived**
documents describing a subsystem `CLAUDE.md` forbids porting back. An agent
acting on that answer reintroduces a deleted design, confidently and with
citations.

**2. One canonical policy, carried as a VERBATIM block, not as a restatement.**
`templates/agents/POLICY.md` is the source of truth, and its rules live between
`<!-- fux:policy:begin v1 -->` and `<!-- fux:policy:end v1 -->`. **Every policy
rendering includes that block byte for byte.** Format-native framing may
surround it — a Kiro table, a Copilot heading, a skill's worked example — but the
block itself may not be reworded, reordered, or partially included.

⚠ **This shape was forced by a failure, on the first run of the check that was
supposed to confirm it.** The renderings had been written to *say the same
thing*: *"never drop the mark when you summarise"* against *"never drop the
archived mark when summarising"*. Same meaning, different bytes — and **no
substring test can tell a legitimate rewording from a dropped rule. A test that
cannot fail correctly is worse than no test, because it certifies agreement it
never checked.**

So agreement is **exact match on a shared block** — the same device this project
uses for a Mermaid diagram and its ASCII twin: two representations, one asserted
to match. **A rule changed in one rendering and not the others is worse than no
policy at all**, because two agents then disagree about the same output.

**The renderings stay hand-written** — a handful of short files do not earn a
generator, and L1 keeps the dependency budget at zero. The block is what makes
that safe.

**2a. Three files are exempt from the verbatim block, and the exemption is
pinned.** `ENRICH-SKILL.md`, `USAGE-SKILL.md` and `DECODER-SKILL.md` are
**build procedures and an operating manual**, not renderings of the
archived-results policy — inlining an eight-rule preamble about interpreting
search results into a file about parsing file formats would duplicate a policy
that already has a rendering per vendor. `test_the_exemptions_are_deliberate`
is what keeps widening the exemption a decision.

**3. Three vendors now, and the set is open by construction.** Claude (skills),
GitHub Copilot (custom agents **and** ambient instructions), Kiro (steering
**and** skills). Adding a fourth is a template plus a rendering plus a row —
**not a new decision.** What *would* reopen this record is a vendor changing its
format.

⚠ **Amended 2026-09-06: the fourth arrived, and the claim held — with one
correction.** OpenAI Codex is decision 11 below, and it cost **zero new
templates**: two rows and two destinations. But *"a template plus a rendering
plus a row"* was **incomplete** — Codex needed decision 12's gate change as
well, because it is the first vendor whose only ambient plane is a file this
record deliberately kept **outside** the per-vendor map. **The set is open by
construction; the INSTALLER is not quite.** Read decision 3 as *a vendor with
its own ambient plane* costs a row, and anything else costs a row and a
question.

**4. Copilot gets an agent and instructions, and they are not alternatives.**
The **agent** fires when selected or routed to; the **instructions** (`applyTo:`)
fire on every matching request. ⚠ **The gap between them is the dangerous case**:
someone runs `fux ask` in a terminal, pastes the output into chat, and the agent
was never invoked — but the archived results are still there. Ambient
instructions cover that. Ship both.

**5. Installed from a DECLARATION, never from detection — and the declaration
ships COMPLETE.** `fux setup` installs all three vendors by default, and
`fux.toml` carries

```toml
[agents]
install = ["claude", "copilot", "kiro"]
```

**written out in full by `setup`, not left implicit** — the same treatment the
type allowlist gets, for the same reason: **a default a user can read and edit
in a file they own is a different thing from a default buried in the engine.**

**Detection is refused.** Fux never sniffs for `.kiro/` or `.github/` and infers
intent — that is precisely the derivation
[ADR-DIR-LIST](0022_dir-list.md) decision 4 refused for `archived`, and the
reasoning transfers unchanged: **a heuristic is exact for the repo it was
written against and a silent convention for everyone else.**
Install-all-by-default and declared-never-derived are compatible **because the
declaration is written down, visibly, at the moment of install.**

**Why all three rather than opt-in.** An opt-in flag is a feature nobody knows
exists, so the policy layer would be present in the product and absent in every
repository — and **the failure it prevents is silent**: an agent confidently
citing a deleted design, with a correct-looking citation.

**6. `setup` writes outside `.fux/`, and must SAY so — loudly, every time.**
Everything else `fux setup` writes lives in fux's own territory. These land in
**`.github/`, `.kiro/` and `.claude/`, which belong to GitHub, AWS and
Anthropic.**

Because decision 5 makes the install default-on, **the announcement is the
entire remaining safeguard**, and it is therefore mandatory rather than
nice-to-have. `setup` names every path it wrote outside `.fux/`, and names the
key that turns them off. **`--no-agents` is the one-shot escape; `install = []`
is its durable form.**

⚠ **The cost this carries, stated rather than discovered.** Three of the
renderings are **ambient** — Copilot's two `instructions/` files (`applyTo:
"**"`) and Kiro's steering (`inclusion: always`) enter *every* request in that
repository, for every developer, whether or not they are using Fux at that
moment. **That is a standing context tax imposed by a tool they installed for
something else.** Two things keep it defensible and both are obligations:
**the ambient renderings stay short — growth is a regression, not an
improvement** — and **`setup` announces them**, so the tax is visible to whoever
pays it.

**7. Write-if-missing, inherited rather than reinvented.** `setup.py` reads
templates out of the wheel (*read, never imported*) and lays them down with
`_write_if_missing`. A consumer's edit is never overwritten. ⚠ **The corollary
is that a stale policy file is invisible**, which is what decision 8 exists for.

**8. Every policy rendering carries `policy-version`.** In frontmatter where the
vendor allows it, in a comment where it does not. A file the consumer has edited
is theirs and stays; a file three versions behind is at least **identifiable**.
**Without this, write-if-missing means *install once, drift forever*.**

**9. Policy ships as steering; an operating manual ships as a skill.**

| the guidance… | ships as | because |
|---|---|---|
| must shape an answer the agent is *already* giving — the archived-results stance | **steering**, `inclusion: always` / `applyTo: "**"` | an agent not thinking about Fux still must not cite a retired design as evidence. **If it has to be *loaded* to apply, it does not apply** |
| is consulted *while doing a thing* — how to invoke Fux, how to write a decoder | **skill**, progressive disclosure | there is no reason to tax an interaction that never touches Fux |

**The test to apply:** *does an agent that has never heard of Fux still need this
sentence to avoid being wrong?* Yes → steering. No → skill.

⚠ **This is a rule because the tax is not optional on every vendor.** Kiro CLI
supports **no steering inclusion modes** — every file in `.kiro/steering/` enters
every interaction, so `inclusion: manual` protects nobody. Decision 6's
announcement makes the tax visible; **this decision is what keeps it small.**

**9a. A skill that writes committed code must never be ambient on any surface.**
`fux-enrich` and `fux-decoder` write into committed directories and change what
is indexed, so they ship to **skill** surfaces only and to no ambient one. **A
Kiro skill is progressive-disclosure; only Kiro *steering* is ambient**, which
is what admits Kiro while still excluding Copilot's `instructions/`.

⚠ **Amended 2026-09-06 — the rule is unchanged; the roster was wrong.** This
decision read *"the two skill surfaces — Claude and Kiro"*, which was a count of
what existed in August, quietly doing the work of a rule. There are now **four**
(`.claude/skills`, `.kiro/skills`, `.codex/skills`, `.github/skills`), and
`fux-enrich` had reached only the first. **Read 9a as a predicate on the
surface, never as a list of vendors.**

**10. One template may map to two destinations, and that is stronger than a
conformance test.** Kiro implements the same open Agent Skills standard Claude
does, so the identical `USAGE-SKILL.md` bytes are written to both
`.claude/skills/fux-usage/SKILL.md` and `.kiro/skills/fux-usage/SKILL.md`.
**That is agreement by construction**, strictly stronger than decision 2's
conformance test asserting two separately-maintained files still match.

**11. `fux-usage` teaches a four-rung invocation ladder, and the ladder is
gated.** ⚠ **The defect it closes was live and in this record's own templates.**
`fux.agent.md` read *"If `fux` is not installed or there is no index, say so and
fall back to ordinary search."* But `fux` is a **console script** — on `PATH`
only where its installing environment's `bin/` is — so in any repo whose fux
lives in an unactivated `.venv/`, an agent got `command not found`, concluded
*not installed*, and **silently used grep** while the engine sat there and the
committed index sat beside it. **It did not error. It degraded, and the
degradation read exactly like an honest answer.**

The ladder is `fux` → `uv run fux` → `./.venv/bin/fux` (`.venv\Scripts\fux.exe`
on Windows) → `python -m fux`, probed with `--version` and cached for the
session. Three rules are gated by
[`tests/test_setup_agents_usage.py`](../../tests/test_setup_agents_usage.py):

1. the rungs appear **in order** in every rendering;
2. exhausting them yields *"could not be invoked, here is what I tried"* and
   **never** a claim that the package is absent;
3. **no rendering may tell an agent to activate a virtualenv, modify `PATH`, or
   install anything.** ⚠ **That last one is the failure a well-meaning edit
   introduces, which is why it is a test and not a sentence.**

⚠ **Rung 4 is the spelling a human guesses, not the one that happened to work
first.** An agent reporting *"I tried `python -m fux.cli`"* has named something
no reader recognises as the obvious attempt. `fux.cli` still works and is what
`tests_e2e/` spawns; it is simply no longer what the ladder teaches.

**12. `fux-usage` states which verb yields a line range.** `ask` and `find` are
document-level (`docs/mesh.md`); `answer` is span-level
(`docs/mesh.md:L10-L13`).

⚠ **Omitting it produced a wrong conclusion in the field**: a user ran `fux ask`,
saw no line numbers, and reported that fux does not return them. It does — from
`answer`. **A feature that is built, tested and undocumented is
indistinguishable from one that does not exist.** And it is L4 showing through
the surface rather than an oversight worth designing away: a line range can only
be computed by chunking the *fetched* bytes, and `ask` is offline by default.

⚠ **The shipped usage skill gained the retry rule on 2026-09-05** (W-109):
when a search returns `band: partial` with a non-empty `missing`, re-ask with
the corpus's own word, or keep the question and add `--expand`, or pass a second
phrasing with `-q`. **A wrong guess costs nothing** — expansion terms are scored
below the user's own and a document matching only them is never returned — which
is what makes the retry safe to recommend to an agent.

**It is in the skill because the surface cannot teach it.** `--json` reports
`missing`; nothing in the output says what to do about it, and an agent that
does not know the slot exists re-runs the same failing question.
[ADR-EXPAND](0054_expand.md).

⚠ **The `fux-enrich` skill was re-aimed at doc2query on 2026-09-05** (W-110):
its body is now **five to ten questions a searcher would type**, one per line,
and no summary. Prose was measured at **+1 fixed / −1 broken** and the break was
context prose carrying currency words into a superseded record.

**This is a skill change with a mechanical partner**, which is new for this
record's subject: `fux enrich --check` now *tests* what the skill asks for —
a question that does not retrieve its own document in the top 3 is refused by
name. The skill and the check say the same thing, and only one of them can be
ignored.

⚠ **The skill's `superseded_by:` instruction reaches the RANKING.** It is the
only key in that frontmatter that does. The skill says so in the same breath as
it introduces it, because an agent that writes one casually retires a live
document.

**11. OpenAI Codex is the fourth vendor** (2026-09-06). Codex CLI reads project
skills from `.codex/skills/<name>/SKILL.md` — **the same open Agent Skills
standard Claude and Kiro implement** — so `USAGE-SKILL.md` and
`DECODER-SKILL.md` map there from the **same templates, byte for byte**. That is
decision 10's agreement-by-construction a third and fourth time, and it is why
this vendor added no file to `templates/agents/`.

⚠ **Codex has no per-file ambient surface** — no `applyTo:`, no inclusion mode.
Its always-on context is the repo-root `AGENTS.md` and nothing else. So:

| rendering | ships to Codex as | because |
|---|---|---|
| the archived-results policy | **`AGENTS.md`**, which already carries the verbatim block | decision 9: *if it has to be loaded to apply, it does not apply* — and a skill is loaded |
| the operating manual (`fux-usage`) | `.codex/skills/fux-usage/` | consulted while doing a thing |
| the decoder guide (`fux-decoder`) | `.codex/skills/fux-decoder/` | decision 9a — a committed-write skill gets skill surfaces only |
| `fux-enrich` | **nothing** | ADR-ENRICH decision 10 stands; a new vendor does not widen it |

**There is deliberately no `.codex/skills/fux-archived-results/`.** Writing one
would put the policy on a surface that has to be invoked, in the one vendor
where nothing else covers it.

**12. `AGENTS_MD_VENDORS` — the root file is written for the full set OR for a
vendor that has no other ambient plane.** `run()` previously wrote the
vendor-neutral `AGENTS.md` only when `installing == KNOWN_AGENTS`, on W-82
ruling 16's reasoning: *a partial declaration names what it wants, and a neutral
file nobody named is not covered by that naming.*

🔴 **That reasoning is sound for three vendors and false for the fourth.**
`install = ["codex"]` would have written two skills and **no archived-results
policy at all** — decision 1's silent failure, reintroduced through a config
line, in the vendor least able to notice. `AGENTS_MD_VENDORS = ("codex",)` names
the exception, and two tests hold both directions: Codex alone gets the root
file, and a `["claude"]` declaration still does not.

**13. ⚠ "claude-only" describes what fux WRITES, never what another agent
READS — and that gap is now real, not theoretical.** GitHub Copilot reads
project skills from `.github/skills`, `.agents/skills` **and `.claude/skills`**.
So in any repository where both `claude` and `copilot` install — the default —
**Copilot loads all four Claude skills, `fux-enrich` included**: the one
[ADR-ENRICH](0040_enrich.md) decision 10 confined to a single surface.

**Nothing fux can do closes this.** The path is Anthropic's convention, another
vendor chose to read it, and moving `fux-enrich` out of `.claude/skills/` would
break it for the vendor it was written for. **Recorded, not fixed.**

⚠ **Superseded in effect by decision 14, not in substance.** Copilot now gets
its **own** `fux-enrich` rendering, so the cross-read is no longer how it
reaches the skill — but the cross-read itself is unchanged, and every future
per-vendor confinement still has to be written as a claim about fux's writes.

⚠ **The exposure is bounded, and saying how is the point.** A Copilot-loaded
skill is **progressive-disclosure, not ambient**, so decision 9a's actual hazard
— a committed-write skill entering *every* request — **has not occurred.** What
changed is only the confinement's reach: it was always a claim about fux's
writes, and it now has to be read that way rather than as a claim about which
agents can invoke `fux enrich`.


**14. Copilot gets `.github/skills/`, and the fork closed A rather than C**
(Arpit, 2026-09-06). [`copilot-skill-surface`](../../work/compare/copilot-skill-surface.compare.md)
proposed **C — write nothing new**, on the ground that Copilot already reads
`.claude/skills` and the duplicate-name behaviour is unmeasured. **Overruled,
and the doc's own crux is weaker than it was written:**

- **The two copies are byte-identical by construction** — one template, N
  destinations, decision 10 — so a double-load is **idempotent**. The compare
  doc treated the collision as *unknown behaviour*; the honest bound is
  narrower: the only failure mode left is a **hard duplicate-name error**, not
  divergent instructions. That is a materially smaller risk than *"unknown"*,
  and saying so is a correction to fux's own filed reasoning.
- **C leaves a real hole.** `install = ["copilot"]` **without** `claude` gets an
  agent file, two ambient instruction files, and **no skills at all** — and C
  was correct only *because* `claude` usually installs, which is an assumption
  about the filesystem in all but name. Decision 5 refuses exactly that.

**What shipped is `fux-enrich` only**, because the ruling named it.
`fux-decoder` and `fux-usage` still have no `.github/skills/` rendering. ⚠
**That is now the asymmetry**, inverted from the one this session opened with,
and it is held by a test rather than by a sentence
(`test_the_two_rosters_differ_only_where_a_record_says_so`).


### Consequences

- ⚠ **Fux owns FOUR third-party formats it does not control.** This is a real
  maintenance liability and it is not hypothetical: **between drafting these
  files and revising them — inside one working session — GitHub's recommended
  surface moved from instructions to custom agents.** It moved again by
  2026-09-06: Copilot and Codex both added Agent Skills, which is what made
  decision 11 cheap and decision 13 true. Decisions 2, 7 and 8 are
  the mitigations; none of them makes the liability go away.
- **`fux setup` gains a flag** ([ADR-CLI](0002_cli-surface.md)'s surface to
  record) and a second *kind* of output
  ([ADR-DOTFUX](0003_fux-directory.md)'s scaffolding contract to widen). Both
  are amended by this record rather than claimed — **`setup.py` itself stays
  with ADR-DOTFUX, because one component is owned once.**
- 🔴 **A per-vendor confinement is only as strong as the vendor's read paths,
  and fux controls none of them.** Decision 13 is the first instance; it will
  not be the last, because every vendor that adopts Agent Skills has an
  incentive to read the other vendors' directories too. **Any future record that
  wants a skill on one surface only must state what it is confining — fux's
  write, not the reader's reach.**
- **The policy is prose, and prose is not enforceable.** Fux cannot verify that
  an agent obeyed it. What Fux can do — and decision 2's test does — is
  guarantee every agent was *told the same thing*.
- **`--json` is the stable contract, the prose is not.** Every rendering says
  *branch on the `archived` boolean, never on the note's wording*, so a future
  reword cannot break a consumer.
- ⚠ **Two things this record states that fux cannot enforce.** Kiro **custom
  agents load neither skills nor steering by default** — they need explicit
  `resources` — so a consumer on a custom agent receives none of these files
  **and gets no error**. Fux cannot write someone's agent config, so the skill
  body says it instead. And a skill's `compatibility` frontmatter field is **a
  declaration nothing checks**, so the ladder lives in the body; putting it only
  in `compatibility` would repeat the *knob that cannot work* failure this
  project has already paid for once.

### Alternatives considered

| | why not |
|---|---|
| **Document the policy, ship nothing** | every user writes their own, most write none, and the failure is silent — an agent confidently citing a deleted design |
| **`fux ask --intent=build`** | rejected in [ADR-ARCHIVED-CONTENT](0037_archived-content.md) decision 7: the stance list is open, and it puts policy inside an engine whose argument is that it ships facts |
| **One file for all agents** | a real convention and worth watching, but Claude skills and Kiro steering both need their own frontmatter to load at all. **A shared file that no tool loads natively is a file nobody reads** |
| **Detect installed agents and write accordingly** | derivation, not declaration — decision 5. Exact for the repo it was written against, a silent convention everywhere else |
| **Opt-in behind a flag** | **drafted this way and overruled.** A flag nobody knows about means the policy layer exists in the product and in no repository, and the failure it prevents is *silent*. The trust concern the flag answered is instead met by decision 6's mandatory announcement plus `--no-agents` |
| **Generate the renderings from the canonical policy** | a handful of short files do not earn a generator; decision 2's conformance test buys the same guarantee at a fraction of the machinery |
| **Ship the skills as steering too, "so they always apply"** | rejected under decision 9a: a skill that writes committed code and changes ranking must never enter every request |
| **Write `.github/skills/fux-decoder/` now that Copilot has a skill surface** | **not rejected — deferred to a compare doc.** Copilot already reads `.claude/skills` (decision 13), so in the default install this writes a *second* copy of a skill Copilot can already load, with the same `name:`. Whether that collides is **not known**, and shipping on a guess is the failure this project pays for elsewhere. [`copilot-skill-surface`](../../work/compare/copilot-skill-surface.compare.md) |
| **Give Codex its own `AGENTS.md` template** | it already has the right one. `AGENTS.md` is vendor-neutral by W-82 ruling 16 and carries the verbatim block; a Codex-specific copy would be a second rendering of a policy that has exactly one |

### Reference (required)

- The fact this policy interprets —
  [ADR-ARCHIVED-CONTENT](0037_archived-content.md) decisions 6 and 7.
- The precedent for caller-owned policy — [ADR-REFER](0030_refer-plane.md) and
  [`src/fux/refer/freshness.py`](../../src/fux/refer/freshness.py): *three
  callers want three different answers from the same index, and no single
  engine-wide policy is right for more than one of them.*
- The installer this extends — [`src/fux/setup.py`](../../src/fux/setup.py)
  (`run()`, `_write_if_missing`, `template_bytes`, and the per-vendor mapping);
  the artifacts themselves —
  [`src/fux/templates/agents/`](../../src/fux/templates/agents/).
- The tests that hold the record's claims —
  [`tests/test_setup_agents.py`](../../tests/test_setup_agents.py) and
  [`tests/test_setup_agents_usage.py`](../../tests/test_setup_agents_usage.py).
- Claude Agent Skills — <https://code.claude.com/docs/en/skills>
- GitHub Copilot custom agents configuration —
  <https://docs.github.com/en/copilot/reference/custom-agents-configuration>
- GitHub Copilot repository custom instructions —
  <https://docs.github.com/en/copilot/how-tos/configure-custom-instructions-in-your-ide/add-repository-instructions-in-your-ide>
- Kiro steering files and inclusion modes — <https://kiro.dev/docs/steering/>
- GitHub Copilot agent skills, and the three project-skill directories it reads
  (`.github/skills`, `.claude/skills`, `.agents/skills`) — the grounding for
  decisions 11 and 13 —
  <https://docs.github.com/en/copilot/concepts/agents/about-agent-skills>
- Codex CLI skills (`.codex/skills/`) and its `AGENTS.md` relationship — the
  grounding for decision 11 —
  <https://developers.openai.com/codex/guides/agents-md>
- The gate decision 12 changed —
  [`src/fux/setup.py`](../../src/fux/setup.py) (`AGENTS_MD_VENDORS`, and the
  `installing == KNOWN_AGENTS or …` branch in `run()`), held by
  `test_codex_alone_still_gets_the_root_agents_file` and
  `test_a_partial_declaration_without_codex_writes_no_root_agents_file`.

### Veto condition

**Reopen this decision if any of these becomes true:**

1. **`fux setup` writes an agent file without naming it in its output**, or
   without naming how to turn it off. Since decision 5 makes the install
   default-on, **the announcement is the only safeguard left.**
2. **`install = []` or `--no-agents` still writes an agent file.** The opt-out is
   the whole of a user's control here; if it leaks, decision 5 stops being a
   default and becomes a mandate.
3. **A shipped rendering no longer loads in its vendor's tool** — a renamed path,
   a changed frontmatter key, a retired mechanism. **This has already fired once
   during authoring.**
4. **The verbatim block differs by a byte** between the canonical policy and any
   non-exempt rendering — reworded, reordered, partially included, or absent.
   **An exact match is the only check that can detect it.**
5. **Fux infers which agents to install from the filesystem** — decision 5 is
   declared-never-derived.
5a. **A vendor is added to `KNOWN_AGENTS` whose ambient plane fux does not
   write** — decision 12's failure mode, generalised. `AGENTS_MD_VENDORS` is the
   list of vendors for which the root file *is* the plane; a fifth vendor with
   neither its own ambient rendering nor a row there installs skills and no
   policy, silently. **The question to ask of any new vendor: where does the
   archived-results block reach it?**
5b. **`fux-enrich` or `fux-decoder` becomes AMBIENT on any surface, on any
   vendor** — including through a read path fux does not write (decision 13).
   The confinement was never about which agent can invoke it; it is about a
   committed-write skill entering every request. **That, and only that, is the
   line**, and 2026-09-06 is when the roster stopped standing in for it.
5c. **A committed-write skill reaches a skill surface its twin does not, with
   no record naming the exception.** `fux-enrich` shipped to one surface while
   `fux-decoder` shipped to three, for weeks, inside a record that had
   **written the gap down** — and nothing failed, because an omission has no
   test. **A stated gap is not a closed one.**
6. **An ambient rendering grows.** They enter *every* request in a consumer's
   repository. **Growth is a regression**, because the cost is paid by developers
   who may not be using Fux at that moment — on every prompt, forever.
7. **A skill that writes committed code ships to an ambient surface** —
   decision 9a.
8. **The policy tells an agent what the answer is, rather than how to read the
   fact.** The moment a rendering encodes Fux's opinion about a *document*
   rather than about *what archived means*, **the engine has smuggled the intent
   taxonomy back in through the policy layer.**

**How to check them:**

```bash
# 1, 2 — every agent file setup writes is named in its output, and
#         --no-agents / install = [] writes none of them
uv run pytest -q tests/test_setup_agents.py -k "announces or optout"

# 3 — the shipped paths and frontmatter keys still match each vendor's docs.
#     No command can check this. It is a periodic read of the four URLs in
#     §Reference, and `policy-version` is what makes a stale file visible.

# 4 — every policy rendering carries the canonical block, byte for byte
uv run pytest -q tests/test_agent_policy_agreement.py

# 5 — no filesystem sniffing decides what gets installed
grep -rn "\.kiro\|\.github\|\.claude" src/fux/setup.py
# expect: only literal write targets, never an exists() branch that selects one

# 6 — the ambient renderings have not grown
wc -c src/fux/templates/agents/fux-archived-results.instructions.md \
      src/fux/templates/agents/fux-usage.instructions.md \
      src/fux/templates/agents/steering-fux-archived-results.md

# 7 — the code-writing skills ship to skill surfaces only
grep -n 'ENRICH-SKILL\|DECODER-SKILL' src/fux/setup.py
# expect: only under `.claude/skills/` and `.kiro/skills/`

# 8 — read the renderings. Each rule must be about how to READ the archived
#     flag, never about which document is right.
ls src/fux/templates/agents/
```

---

## References

*Every source this record cites, gathered in one place. §2's **Reference
(required)** names the grounding; this is the complete list. An archived
document is never listed here — the body may name one, but archive is not
evidence.*

**Records** — [ADR-CLI](0002_cli-surface.md) ·
[ADR-DOTFUX](0003_fux-directory.md) · [ADR-DIR-LIST](0022_dir-list.md) ·
[ADR-REFER](0030_refer-plane.md) ·
[ADR-ARCHIVED-CONTENT](0037_archived-content.md) ·
[ADR-ENRICH](0040_enrich.md) · [ADR-DECODE](0042_decode.md)

**Code**

- [`src/fux/refer/freshness.py`](../../src/fux/refer/freshness.py)
- [`src/fux/setup.py`](../../src/fux/setup.py)
- [`src/fux/templates/agents/`](../../src/fux/templates/agents/)
- [`tests/test_setup_agents.py`](../../tests/test_setup_agents.py)
- [`tests/test_setup_agents_usage.py`](../../tests/test_setup_agents_usage.py)

**Papers and specifications**

- Claude Agent Skills
  <https://code.claude.com/docs/en/skills>
- GitHub Copilot custom agents configuration
  <https://docs.github.com/en/copilot/reference/custom-agents-configuration>
- GitHub Copilot repository custom instructions
  <https://docs.github.com/en/copilot/how-tos/configure-custom-instructions-in-your-ide/add-repository-instructions-in-your-ide>
- Kiro steering files and inclusion modes
  <https://kiro.dev/docs/steering/>
