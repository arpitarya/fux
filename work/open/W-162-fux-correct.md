---
type: Handoff
name: W-162
description: "`fux correct \"<question>\" <doc>` — a human-authored question line appended to the document's enrichment file, marked human, surviving regeneration, reported-never-refused by --check, doubling as a local eval row; a rare --pin; negative corrections refused. Ships with its guide skill, agent steering, --json provenance, doctor rows and glossary entries."
item: W-162
filed: 2026-09-13
ball: agent
---

# W-162 — `fux correct`, and everything that makes it usable

**Model: Sonnet for the verb (a written DoD against `enrich.py`); Opus for the
skill and the steering text**, because a guide that tells an agent to write
corrections unasked is the failure that does not error.

**Accepted:** Arpit, 2026-09-13 — [compare doc](../compare/fux-correct.compare.md).
Ratified, not built.

## Definition of done — the verb

1. `fux correct "<question>" <doc>` appends the question to
   `.fux/enrich/<source sha>.md`, creating the file (frontmatter + this one
   line) when none exists. The line is **marked human** in a way that survives
   indexing: the text is a body line (so it reaches `ctx`); the marker is the
   thing SR-ENRICH's frontmatter-stripping rule does not index.
2. `fux enrich <doc>` regeneration **preserves human lines**, byte for byte,
   and a test proves it.
3. `fux enrich --check` **reports** a human line that fails self-retrieval and
   **never refuses** it; the report says `human` beside the line.
4. `--pin`: writes the exact question → doc pin; `ask`/`answer` place the doc
   at #1 for that exact normalised query, labelled `pinned` in prose, `--json`
   and the receipt. `fux doctor` gains a row: pins whose document's content
   sha changed since the pin (suspended until `fux correct --reaffirm`).
5. **Negative form refused** with the pointer to `supersedes` / `archived=`.
6. **Eval row:** each correction lands as a row in `.fux/eval/corrections.tsv`
   (committed — it is the human's own claim, not a use record); a check runs
   them on every full-suite run and fails on a regression. Never the sealed
   golden.
7. Provenance: `via: ctx (human)` / `ctx (model)` in `--why`, `--json`, the
   receipt.
8. PII: the question text runs through `pii.toml`; a firing rule refuses with
   the rule name, as `enrich --check` does.
9. Both readers: Node reads pins and provenance byte-equal.

## Definition of done — skills and steering

10. **Guide skill `fux-correct`** (joins the ten of
    [SR-AGENT-POLICY](../../records/0132_agent-policy.md) decision 15; edit
    the template, never a rendering; scoped pointers on all four vendors):
    when to correct vs fix the source vs `supersedes`/`archived=`; how to
    phrase a line (the searcher's words, never the title's); when `--pin` is
    justified; reading the `--check` report; reviewing a correction in a PR.
11. **Agent steering in `POLICY.md`:** an agent that was served the wrong
    document and then found the right one **proposes** the
    `fux correct` command in its reply — it **never writes** the correction
    unasked. Same only-when-explicitly-asked rule as `fux-enrich`,
    `fux-decoder`, `fux-fetcher`.
12. MCP: `fux_search` results carry the `via` field so an agent can see a
    human line fired.
13. `docs/GLOSSARY.md`: *correction*, *human line*, *pin*. README: one
    paragraph under the enrichment section.
14. Records: SR-ENRICH (human lines, marker, regeneration rule, `--check`
    behaviour), SR-CLI (the verb), SR-PROVENANCE, SR-DOCTOR (the pin row),
    SR-AGENT-POLICY (the skill and the steering rule). Ownership table +
    `test_sr_ownership.py` for any new module.

## Out of scope

- Raising `ctx`'s weight so corrections bite harder — a ranking change,
  W-156's rule.
- Per-query demotion of any kind.
- Anything that learns from what people clicked (L8).

## Where the work is

[`src/fux/enrich.py`](../../src/fux/enrich.py) (the file writer, `--check`),
[`src/fux/query/provenance.py`](../../src/fux/query/provenance.py),
[`src/fux/doctor.py`](../../src/fux/doctor.py),
[`src/fux/templates/agents/`](../../src/fux/templates/agents/) (POLICY.md and
the skill templates), `node/src/verbs/`.

## Records this will touch

SR-ENRICH · SR-CLI · SR-PROVENANCE · SR-DOCTOR · SR-AGENT-POLICY · SR-PII (a
note, no rule change).
