# The canonical agent policy — the source of truth

**This file is not shipped to a consumer.** It is what the per-vendor renderings
in this directory must all say. [ADR-AGENT-POLICY](../../../../docs/adr/0035_agent-policy.md)
decision 2: the renderings are by hand, but **agreement is asserted, not
trusted** — every numbered rule below must appear in every rendering, and a test
checks it. A rule changed here and not there is worse than no policy at all,
because two agents then disagree about the same output.

## What Fux gives the agent

Fux indexes **retired** documentation alongside live documentation on purpose:
retired documents are the honest answer to *"why does this look the way it
does"*. Fux **marks** them and **states no conclusion**, because the right
conclusion depends on why the question was asked.

| surface | the mark |
|---|---|
| `--json` | `"archived": true` on the result object |
| text output | an `[archived]` prefix on the title |
| any response containing one | a `note:` line on **stderr** giving the count |

## The stances

| stance | the question sounds like | archived content is | what to do |
|---|---|---|---|
| **history** | *why did we choose X*, *what did we used to do* | **the answer** | use it; cite as authoritative **for its period**, and date it |
| **current architecture** | *how does X work*, *where does Y live* | **misleading** | prefer live sources; use archived only as explicit contrast |
| **building** | *implement X*, *fix Y*, *add Z* | **dangerous** | never port code, schema, structure or naming from it |

## The rules — this block appears VERBATIM in every rendering

**Copy it byte for byte.** Format-native framing may surround it; the block
itself may not be reworded, reordered, or partially included. That is what makes
agreement checkable by exact match rather than by judgement, and it is the same
device the ADRs use for a Mermaid diagram and its ASCII twin: two
representations, one asserted to match.

<!-- fux:policy:begin v1 — VERBATIM in every rendering. Do not reword. -->
1. **Branch on the `archived` field in `--json`, never on the note's prose.** The wording is not a contract; the boolean is.
2. **Establish the stance before using an archived result** — history, current architecture, or building.
3. **When the stance is ambiguous, treat it as building.** That is the ordering with the worst downside if you guess wrong.
4. **Never drop the mark when summarising.** A summary that launders a retired design into plain prose is the failure this policy exists to prevent.
5. **Never port from an archived document.** Retired means someone decided against it — it may describe a subsystem the project deliberately deleted.
6. **Name the live successor; if there is none, say so** rather than presenting the archived document as the current state.
7. **If every result is archived, lead with that** before answering.
8. **Never infer "archived" from an `archive/` path segment.** The mark is declared on a source, never derived from a path; a path is a hint and can be wrong.
<!-- fux:policy:end v1 -->

## The one thing a rendering must never do

- **Never encode an opinion about a particular document.** Every rule here is
  about *how to read the flag*. The moment a rendering says which document is
  right, Fux has smuggled a reader-intent taxonomy back in through the policy
  layer — which [ADR-DIR-LIST](../../../../docs/adr/0022_dir-list.md) decision
  12 refused on purpose. This is veto condition 5.

<!-- policy-version: 1 -->
