---
inclusion: always
---

# Archived results from the Fux index

Fux indexes retired documentation alongside live documentation deliberately —
retired documents are the honest answer to "why does this look the way it does".
Fux **marks** them and **states no conclusion**, because the right conclusion
depends on why the question was asked. That judgment is yours.

## Spot the mark

- `--json`: `"archived": true` on the result object. **Branch on the field, not
  on the prose** — the note's wording is not a contract, the boolean is.
- Text output: an `[archived]` prefix on the title.
- A `note:` line on stderr giving the count.

## Establish the stance first

| stance | archived content is | what to do |
|---|---|---|
| **history** — *why did we choose X* | **the answer** | use it; cite as authoritative for its period, and date it |
| **current architecture** — *how does X work* | **misleading** | prefer live; use archived only as explicit contrast |
| **building** — *implement X* | **dangerous** | never port code, schema, structure or naming from it |

**Ambiguous stance → treat it as building.** Worst downside if you guess wrong.

## The rules — regardless of stance

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

## Do not

- Hide or silently demote archived results — the user may want them.
- Infer "archived" from an `archive/` path segment. The mark is **declared** on
  a source, never derived from a path.
- Read a demoted ranking as a correctness signal. Demotion is a configurable
  weight and is a no-op at its default.

> `inclusion: always` is deliberate. `fileMatch` does not fit — this is triggered
> by a tool's output, not by which file is open — and `manual` would mean the
> agent must remember to pull the very guidance it needs in order to know it
> should. The file is kept short to earn its always-on slot.

<!-- policy-version: 1 -->
