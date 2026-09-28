---
type: Standing Record
kind: law
name: SR-LAW-7
title: "SR-LAW-7 (0009) — L7 — Python ≥ 3.12"
description: "The floor that makes the other laws affordable: tomllib in the stdlib, modern typing, exception groups, and since 2026-09-28 the 3.12 typing and stdlib additions — each one a dependency not taken. L8 is its Node twin."
status: accepted
date: 2026-08-18
feature: the rationale, history and reopen-trigger of L7
owns: []
laws: [L7]
timestamp: 2026-08-18T00:00:00Z
content_sha: 6e5fe94795d04eb9a798fcadd82425a045ff04509a554049f346ef4aef8a13e1
---

# SR-LAW-7 — L7 — Python ≥ 3.12

## §1 — For humans

> **This record is the HOME of law L7 — §2's first block IS the law**, and the
> rest of this record is its rationale: why it exists, what it has cost, how its
> wording has moved, and what would reopen it.
> [`CLAUDE.md` §Non-negotiable constraints](../CLAUDE.md) carries a
> **generated** copy, held byte-equal by
> [`tests/test_claude_md_laws.py`](../tests/test_claude_md_laws.py) —
> [SR-LAW-0](0002_LAW-0-authority.md) decisions 1 and 5, on Arpit's ruling of
> 2026-09-06. ⚠ **`CLAUDE.md` is not the source any more**; amend the law here.

**The one-line case.** 3.11 is where the standard library got good enough that refusing dependencies stopped being painful; 3.12 is the oldest Python that is still worth starting from.

**The handle:** *Python ≥ 3.12* — the one-line form from [SR-LAWS](0001_LAWS.md)'s
table. ⚠ **A handle is not the law**; read the law in §2 below.

**This law is the enabler of the others, which is the only reason a version floor is a law at all.**

| what 3.11 gives | the dependency it replaced |
|---|---|
| `tomllib` | `tomli` / `toml` — and every config file fux reads is TOML |
| PEP 604 `X \| Y`, PEP 585 generics | `typing_extensions` |
| `ExceptionGroup`, `except*` | hand-rolled aggregation in the fetch pool |
| `Self`, `LiteralString` | `typing_extensions` again |
| ~10–60% CPython speedup | a chunk of the accelerator's margin, free |

| **3.12 adds** | |
| PEP 695 generic syntax — `class Box[T]:`, `type X = …` | `TypeVar` boilerplate, and `typing_extensions.TypeAliasType` |
| PEP 698 `typing.override` | `typing_extensions.override` |
| PEP 701 f-strings (nested quotes, multi-line expressions) | `.format()` workarounds inside f-strings |
| `itertools.batched`, `Path.walk()`, `Path.relative_to(walk_up=True)` | the hand-rolled chunker and `os.walk` + path glue |

**`tomllib` is the load-bearing one.** `.fux/tune.toml`, `.fux/output.toml`, `.fux/pii.toml`, `.fux/refusals.toml` and `fux.toml` are all read with it. Under 3.10 every one of those needs a third-party parser — which, before 2026-09-06, [L2](0004_LAW-2-zero-cost.md) forbade outright.

⚠ **L2's amendment weakened this law's justification without changing the law.** A TOML parser is now installable. **3.11 remained the floor until 2026-09-28** — the typing and `ExceptionGroup` arguments stand on their own, and lowering it would buy compatibility with a Python nobody is deploying — but the *strongest* argument for it is no longer *"there is no alternative"*.

**Diagram — Mermaid and its ASCII twin. Update both, always, together.**

```mermaid
flowchart LR
    R["SR-LAW-7<br/>(THIS RECORD — states law L7)"]
    N["SR-LAWS<br/>(the handles L0..L12 — routes, never states)"]
    C["CLAUDE.md §Non-negotiable constraints<br/>(GENERATED from the records · test-bound)"]
    B["records bound by L7<br/>(cite the number, never restate)"]
    R --> C
    N --> R
    N --> B
    C -. "regenerate: scripts/gen-laws.py --write" .-> R
```

<details>
<summary><b>ASCII twin</b> — the same diagram, for terminals, diffs, and any reader without a Mermaid renderer</summary>

```text
       SR-LAW-7   <-- THIS RECORD states law L7
            |
            | scripts/gen-laws.py  (test-bound, byte-equal)
            v
   CLAUDE.md §Non-negotiable constraints
        (GENERATED -- not the source)

               SR-LAWS
     (the handles L0..L12 -- routes, never states)
                   |
          +--------+---------+
          v                  v
      SR-LAW-7          records bound by L7
   (the law, plus its     (cite the number,
    rationale, history     never restate)
    and veto)
```

</details>

---

## §2 — For agents

### The law (normative)

🔴 **This block IS law L7.** It is the only normative statement of it, and
[`CLAUDE.md` §Non-negotiable constraints](../CLAUDE.md) carries a **generated**
copy of it — rendered from these bytes by
[`scripts/gen-laws.py`](../scripts/gen-laws.py) and held byte-equal by
[`tests/test_claude_md_laws.py`](../tests/test_claude_md_laws.py).
Amend it **here**, then run `python scripts/gen-laws.py --write`.
Amending a law needs Arpit's ruling, named in this record
([SR-LAW-0](0002_LAW-0-authority.md) decision 3).

<!-- LAW-TEXT:BEGIN L7 -->
- **L7** · **Python ≥ 3.12** (`tomllib`, modern typing — PEP 695 type parameters, `typing.override`, `itertools.batched`). Match the surrounding style. **[L8](0010_LAW-8-node-22.md) is its Node twin.**
<!-- LAW-TEXT:END L7 -->

### Context

L7 predates the record set: it lives in the steering doc every session reads
first, and [SR-LAWS](0001_LAWS.md) gave it a citable handle so a decision could
name it without quoting it. **What was still missing was a place to put the
reasoning** — why the law is worth its cost, what it has already been narrowed
by, and what would have to become true to reopen it.

That material had been accumulating inside `SR-LAWS` itself, which was becoming
one record carrying eight subjects. This record is L7's share of it, split out
on 2026-09-06 at Arpit's ruling.

### Decision

**1. Python ≥ 3.12 is the floor,** declared in `requires-python`, asserted by the classifier list, and read by `fux doctor` from `src/fux/constants.toml` `[python] min`.

⚠ **Amended 2026-09-28 on Arpit's ruling** (Cowork, W-234): *"law 7 which says python 311, change it to Python 312"*, and asked when, *"Python 3.12 breaks in the next release."* **It is a breaking change**, listed under **Breaking** in the CHANGELOG: a 3.11 install that upgrades is refused by pip rather than failing at runtime. The CI matrix dropped 3.11 in the same change.

**Why 3.12 and why now.** Nothing in the build *needed* 3.12 on the day. What the bump buys is the table in §1, usable without a guard, and one fewer interpreter in the test matrix. Python 3.11 reaches end of security support in October 2027; 3.12 is supported until October 2028. This decision's own clause 3 below says the floor rises only for a named reason; **the reason named here is Arpit's ruling and the table above**, not merely that a newer version exists.

**2. Match the surrounding style.** Modern typing throughout; no `typing_extensions`, no `from typing import List`.

**3. The floor rises only for a reason that is named,** never because a newer version exists. Tested against 3.12–3.14.

### Consequences

- **Easier:** every config path, with no parser to vendor or install.
- **Harder:** an enterprise fleet pinned to 3.11 or older cannot run fux at all (3.9 and 3.10 were already out before 2026-09-28). That is a real deployment cost in exactly the environments fux targets, and the floor was chosen knowing it.
- ⚠ **The justification narrowed on 2026-09-06** without the law moving. Recorded here so a later session does not find the `tomllib` argument, notice it is now optional, and conclude the floor is.

### Alternatives considered

- **Support 3.9+ with a vendored TOML parser.** Rejected when written: it was hand-rolling a parser to avoid a dependency, to support a Python that gets nothing else fux wants. ⚠ Reopenable in principle since L2's amendment; **still refused**, because the cost is a permanent compatibility surface for a shrinking population.
- **Require 3.12+.** Rejected when written: nothing in the build needed it, and each bump strands deployments for free. ⚠ **Adopted 2026-09-28** (decision 1) on Arpit's ruling. The stranding cost is real, and it was accepted, not refuted.
- **Stay on 3.11 until it reaches end of life (October 2027).** Not chosen: Arpit ruled the bump for the next release.

### Reference (required)

- `CLAUDE.md` §Non-negotiable constraints — the normative text. Repo path: [`../../CLAUDE.md`](../CLAUDE.md)
- `pyproject.toml` — `requires-python = ">=3.12"`, the executable form of this law
- PEP 695 — https://peps.python.org/pep-0695/ · PEP 698 — https://peps.python.org/pep-0698/ · PEP 701 — https://peps.python.org/pep-0701/
- Python release status (3.11 security support to 2027-10, 3.12 to 2028-10) — https://devguide.python.org/versions/
- PEP 680 (`tomllib`) — https://peps.python.org/pep-0680/
- [SR-CONFIG](0113_config.md) · [SR-TUNE](0135_tuning.md) — the readers that depend on it

### Veto condition

**Reopen if** a supported Python drops below 3.12 in `pyproject.toml`, or if a `typing_extensions` import appears.

**How to check it:**

```bash
grep -n 'requires-python' pyproject.toml        # expect: >=3.12
grep -rn 'typing_extensions' src/               # expect: no output
```
