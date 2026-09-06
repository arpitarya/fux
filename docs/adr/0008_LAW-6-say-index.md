---
type: ADR
name: ADR-LAW-6
title: "ADR-LAW-6 (0008) — L6 — say "index", not "db""
description: "Load-bearing vocabulary, ruled by council: what fux commits is statistics that make documents findable, and calling it a database invites every expectation the architecture refuses."
status: accepted
date: 2026-08-18
feature: the rationale, history and reopen-trigger of L6
owns: []
laws: [L6]
timestamp: 2026-08-18T00:00:00Z
---

# ADR-LAW-6 — L6 — say "index", not "db"

## §1 — For humans

> **This record is the RATIONALE for law L6. It is not the law.**
> The normative text lives in
> [`CLAUDE.md` §Non-negotiable constraints](../../CLAUDE.md), and that is its
> only home. This record explains why the law exists, what it has cost, how its
> wording has moved, and what would reopen it — **without restating it**, per
> [ADR-LAWS](0001_LAWS.md) decision 3.

**The one-line case.** Call it a database and the next question is always *"so where's the data?"* — and the honest answer, *"there isn't any"*, stops sounding like an architecture and starts sounding like a bug.

**The handle:** *Say "index", not "db"* — the one-line form from [ADR-LAWS](0001_LAWS.md)'s
table. ⚠ **A handle is not the law**; read the law at its home.

**Why a vocabulary rule is a law.** The other seven laws describe what the code may do. This one describes what everyone will *assume* it does, and the assumption arrives before anyone reads the code.

**"Database" imports a set of expectations fux deliberately does not meet:** that it holds the data, that it is the system of record, that you back it up, that you restore it, that it drifts from the source and needs reconciling, that querying it is querying your documents.

**"Index" imports the right ones:** that it points at things it does not contain, that it is rebuilt rather than restored, that it is derived from a corpus that lives elsewhere, and that it can be regenerated if lost.

**This is not style.** [L2](0004_LAW-2-content-never-durable.md) is the architecture; L6 is the sentence that stops people arguing against L2 without realising they are doing it. Every *"why don't we just cache the bodies"* conversation starts with somebody calling it a database.

**Diagram — Mermaid and its ASCII twin. Update both, always, together.**

```mermaid
flowchart LR
    C["CLAUDE.md §Non-negotiable constraints<br/>(the only normative text)"]
    N["ADR-LAWS<br/>(the handles L1..L8)"]
    R["ADR-LAW-6<br/>(this record — rationale, history, veto)"]
    B["records bound by L6<br/>(cite the number, never restate)"]
    C --> N --> R
    N --> B
    R -. "explains, never restates" .-> C
```

<details>
<summary><b>ASCII twin</b> — the same diagram, for terminals, diffs, and any reader without a Mermaid renderer</summary>

```text
   CLAUDE.md §Non-negotiable constraints
        (the only normative text)
                   |
                   v
               ADR-LAWS
          (the handles L1..L8)
                   |
          +--------+---------+
          v                  v
      ADR-LAW-6            records bound by L6
   (rationale, history,   (cite the number,
    veto -- never the      never restate)
    law itself)
          :
          +.... explains, never restates ....> CLAUDE.md
```

</details>

---

## §2 — For agents

### Context

L6 predates the record set: it lives in the steering doc every session reads
first, and [ADR-LAWS](0001_LAWS.md) gave it a citable handle so a decision could
name it without quoting it. **What was still missing was a place to put the
reasoning** — why the law is worth its cost, what it has already been narrowed
by, and what would have to become true to reopen it.

That material had been accumulating inside `ADR-LAWS` itself, which was becoming
one record carrying eight subjects. This record is L6's share of it, split out
on 2026-09-06 at Arpit's ruling.

### Decision

**1. The committed artifact is an **index**, in prose, in code, in `--help`, and in error messages.**

**2. `db`, `database`, `store` and `cache` are wrong for the committed plane.** `cache` remains correct for `runtime/fetch-cache/`, which really is one.

**3. It is a council ruling and load-bearing vocabulary,** not a preference. A record that calls it a database is a defect to fix on contact.

### Consequences

- **Easier:** the L2 conversation, every time, with everyone.
- **Harder:** nothing measurable. This law costs a word.
- ⚠ **It cannot be fully mechanised.** A grep finds the word; it does not find a paragraph that describes an index *as if* it were a database without using the word. That is the same limit [ADR-LAWS](0001_LAWS.md) records for the narrower-claim hazard.

### Alternatives considered

- **Leave it to review.** Rejected on the same evidence as the paraphrase rule: review did not catch the ones already in the record set.
- **Allow "db" informally in comments.** Rejected: the informal usage is where it starts, and code comments are read more carefully than prose.

### Reference (required)

- `CLAUDE.md` §Non-negotiable constraints — the normative text. Repo path: [`../../CLAUDE.md`](../../CLAUDE.md)
- [`docs/GLOSSARY.md`](../GLOSSARY.md) — every recurring term, defined once
- [ADR-LAW-2](0004_LAW-2-content-never-durable.md) — the architecture this vocabulary protects
- Lakoff & Johnson, *Metaphors We Live By* (1980) — the case that the noun chosen for a system governs the inferences drawn about it

### Veto condition

**Reopen if** the committed plane ever genuinely holds content — at which point the word would have stopped being wrong, and [L2](0004_LAW-2-content-never-durable.md) would have fallen first.

**How to check it:**

```bash
grep -rni '\bdb\b\|database' src/fux docs work --include='*.py' --include='*.md' | grep -v 'fetch-cache'
# expect: no output describing the committed plane
```
