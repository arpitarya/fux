---
type: Handoff
name: W-231
description: "New law L13, ruled by Arpit 2026-09-28: a RETIRED SR is moved to archive/records/, never deleted. Superseded records are out of scope and keep today's rewrite-in-place rule. Reverses the 'records are never archived' half of SR-WORK-ARCHIVE decision 9 for retired records only."
item: W-231
filed: 2026-09-28
ball: agent
---

# W-231 — L13: a retired SR is archived, never deleted

**Model: Opus** (a new law, two record amendments, a generated block, an enforcement test).

## ✅ BUILT and CLOSED 2026-09-28 (Claude Code, Opus)

Every step below landed in one change: SR-LAW-13, L13 in SR-LAWS and the
register, SR-WORK-ARCHIVE decision 9 split, SR-LAW-5 moved to `archive/records/`
with its banner and map row, the enforcement test, and the regenerated
`CLAUDE.md` laws block. Both suites green.

## ✅ RULED 2026-09-28 (Arpit, Cowork)

*"create a new law if an sr is retired archive it"*, then *"no need for
superseded part"*.

- **Scope: RETIRED records only** (a record whose law, rule or subject was
  retired). **Superseded records are out of scope** and keep today's rule:
  rewritten or deleted in the change that supersedes them (SR-WORK-ARCHIVE
  decision 9 stands for them).
- **It is a law:** handle **L13**, record **SR-LAW-13** at the next free law
  file number (`0014` expected; confirm against the records/README range table).

## What the law says (for the build to state in SR-LAW-13)

1. A retired SR is **moved** to `archive/records/`, mirroring its path, in the
   same change that retires it. **Never deleted.**
2. `archive/README.md` gets a row for it, as for every archived document
   (SR-WORK-ARCHIVE decisions 1–3).
3. The moved file carries `status: archived` and a top banner:
   `ARCHIVED <date> — retired by <ruling>`. **No "superseded by" line** (Arpit).
4. It may be **named**, never **cited** as grounding for a live claim —
   SR-WORK-ARCHIVE decisions 4–7 apply unchanged.
5. A retired law handle is still never reused (SR-LAWS).

## Next, agent, in one change

- **Write SR-LAW-13**; add **L13** to SR-LAWS's handle table and `laws:` list.
- **Amend SR-WORK-ARCHIVE decision 9** (retired records are archived; superseded
  ones are still rewritten or deleted) and its mermaid/ASCII diagram, its
  Consequences and its "archive tier" alternative. **Amend records/README**
  §One directory, one state and the 0062 register row.
- **Backfill:** move **SR-LAW-5** (`0007`, retired 2026-09-20) to
  `archive/records/`. Its register row and SR-LAWS's L5 row then **name** it
  (no grounding link). Check for any other record whose register row says
  retired and is still in `records/`. **Do not restore** the records deleted on
  2026-09-06; git holds them.
- **Enforcement** (owned by SR-LAW-13 or SR-WORK-ARCHIVE):
  - fail if a file in `records/` is marked retired;
  - fail if a file in `archive/records/` lacks the banner, `status: archived`
    or its `archive/README.md` row.
- **Regenerate** the CLAUDE.md laws block (`python scripts/gen-laws.py --write`);
  `tests/test_claude_md_laws.py` green.
- Both suites whole, green. Close.
