---
name: fux-archived-results
description: Interpret archived results from the Fux index correctly. Use whenever a Fux query (fux ask, fux find, fux answer, or their --json output) returns results marked archived, or whenever an answer is being built from Fux output that may include retired documents. Establishes the reader's stance first, because the same archived document is authoritative for a history question, misleading for an architecture question, and dangerous for a build task.
---

# Archived results from Fux

Fux indexes retired documentation alongside live documentation, deliberately —
retired documents are the honest answer to *"why does this look the way it
does"*. It marks them and **states no conclusion**, because the right conclusion
depends on why the question was asked.

**That judgment is yours. This skill is how to make it.**

## 1. Spot the mark

| surface | the mark |
|---|---|
| `--json` | `"archived": true` on the result object |
| text output | an `[archived]` prefix on the title |
| any response containing one | a `note:` line on **stderr** naming the count |

**Branch on the `--json` field, never on the prose.** The note's wording is not
a contract; the boolean is. If you are parsing text output and the `[archived]`
prefix is your only signal, prefer re-running with `--json`.

## 2. Establish the stance before you use the result

Ask what kind of question is actually being answered:

| stance | the question sounds like | archived content is | what to do |
|---|---|---|---|
| **history** | *why did we choose X* · *what did we used to do* · *when did this change* | **the answer** | Use it. Cite it as authoritative **for its period**, and date it. |
| **current architecture** | *how does X work* · *what is the design* · *where does Y live* | **misleading** | Prefer live sources. Use archived only as explicit contrast — *"this was the design until…"*. |
| **building** | *implement X* · *fix Y* · *add Z* | **dangerous** | **Never port code, structure, or design from it.** It may describe a subsystem the project has deliberately deleted. |

**When the stance is ambiguous, treat it as building.** That is the ordering
with the worst downside if you guess wrong.

## 3. The rules — regardless of stance

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

## 4. Worked example

```console
$ fux ask "what is the ingest cache" --top 3
5.9021  [archived] Ingest cache and chunker     (archive/v0.26-docs/adr/0002-...)
4.8813  [archived] Per-file cache invalidation  (archive/v0.26-docs/adr/0006-...)
3.9902  [archived] Chunker tuning               (archive/v0.26-docs/adr/0009-...)

note: 3 of 3 results are from archived sources — retired from the live
      corpus. An archived document records what was true when it was
      retired, not what is true now.
```

**Building** → *"Every result is retired. The per-file cache was removed and
should not be reintroduced; I found no current equivalent. Tell me what you are
trying to achieve and I will look for how it is done now."*

**History** → *"The ingest cache was a per-file cache — here is how it worked,
per the retired records, and here is when it was removed."*

**Both are correct answers to the same output.** The difference is the stance,
and nothing in the Fux output decides it for you.

## 5. What NOT to do

- Do not silently demote or hide archived results — the user may want them.
- Do not assume `archive/` in a path means archived. The mark is **declared**,
  not derived from a path; a path is a hint and can be wrong.
- Do not treat a demoted ranking as a correctness signal. Demotion is a
  configurable weight; at the default it does nothing at all.

<!-- policy-version: 1 -->
