---
applyTo: "**"
---

# Archived results from the Fux index

Fux indexes retired documentation alongside live documentation on purpose, marks
the retired results, and **states no conclusion about them** — because the right
conclusion depends on why the question was asked. Apply the following whenever
Fux output is part of your context.

## Spot the mark

- `--json`: `"archived": true` on the result object — **branch on this field**,
  not on prose. The note's wording is not a contract; the boolean is.
- Text output: an `[archived]` prefix on the title.
- A `note:` line on stderr naming how many results are archived.

## Establish the stance before using an archived result

- **History** (*why did we choose X*, *what did we used to do*): archived
  content **is the answer**. Use it, cite it as authoritative for its period,
  and date it.
- **Current architecture** (*how does X work*, *where does Y live*): archived
  content is **misleading**. Prefer live sources; use archived only as explicit
  contrast — "this was the design until…".
- **Building** (*implement X*, *fix Y*): archived content is **dangerous**.
  Never port code, schema, structure, or naming from it — it may describe a
  subsystem the project deliberately deleted.

**When the stance is ambiguous, treat it as building.** That is the ordering
with the worst downside if you guess wrong.

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

- Do not hide or silently demote archived results — the user may want them.
- Do not infer "archived" from an `archive/` path segment. The mark is
  **declared** on a source, never derived from a path; a path is a hint and can
  be wrong.
- Do not read a demoted ranking as a correctness signal. Demotion is a
  configurable weight and does nothing at its default.

<!-- policy-version: 1 -->
