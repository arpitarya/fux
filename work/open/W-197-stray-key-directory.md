---
type: OpenItem
id: W-197
title: "W-197 — a plural key directory exists in the tree and no agent may touch it"
description: "work/golden/golden-answers/ (plural) is reported present in the working tree. CLAUDE.md §Golden answer key says no key file any agent can reach exists. Arpit inspects and removes it if it holds answers — deleting it is a tool call that reaches into it, so no agent may, on either spelling."
status: open
lane: arpit
timestamp: 2026-09-17T00:00:00Z
filed: 2026-09-17
ball: arpit
---

# W-197 — the plural key directory

**Model: NONE.** 🔴 **Nothing an agent may do here, including looking.**

## What is claimed, and by whom

**A directory `work/golden/golden-answers/` — plural — exists in the tree.** That
fact reached this session **as a report**, in the filing instruction. The scoring
session did not open it, and **this session did not open, list, stat, glob, hash
or delete it either.**

⚠ **It has not been verified to exist and will not be.** Confirming it would be a
tool call reaching a path that may hold a key, which is the breach
[L11](../../records/0012_LAW-11-sealed-answer-key.md) decision 5 names: *"Listing,
globbing, `stat`, line counts, hashing, format checks, diffs, copies, moves,
deletions and re-indexing are each a breach on their own. The test is whether the
tool call reaches a key, never whether the bytes came back."*

## Why it matters

**`CLAUDE.md` §Golden answer key states there is no key file any agent can
reach**, and [L11](../../records/0012_LAW-11-sealed-answer-key.md)'s central claim
is that *nothing is on disk to reach*. **A directory whose name is one letter from
the sealed one falsifies that claim if it holds answers** — L11's veto condition
says so directly: *"Also reopen if a key file is found on any machine an agent can
reach, whoever wrote it: the law's central claim is that no such file exists, and
one that does falsifies it rather than merely violating it."*

🔴 **And the plural spelling is the interesting part.** Every guard in this repo
was written against the **singular** path — the `.gitignore` entry, the
`permissions.deny` rules, `.claude/hooks/guard-golden-answer.sh`, and the
`!work/golden` line in `.fux/sources/dirs`. Whether each covers the plural one is
**a question about the guards**, and it is not answerable by an agent, because
answering it means aiming a tool at the path.

⚠ **One of them does cover it, and it is the reason this file exists at all:** the
hook matches the *substring*, so it blocked this session twice while it was
writing prose about the subject. **A guard that fires on a description is doing
its job** — it cannot tell a sentence from a `cat`, and it fails closed.

## 🔴 What Arpit does

1. **Inspect it himself.** Nobody else can.
2. **If it holds answers — remove it.** L11 decision 5 is explicit that *"no
   Claude session removes"* such a directory, *"even though decision 3 retires it:
   deleting it is a tool call that reaches into it. Arpit removes it himself, and
   until he does, its continued existence authorizes nothing."*
3. **If it does not hold answers**, say so here and this item closes — but the
   guards still want the plural spelling written into them explicitly, which
   becomes an `agent` row **at that point and not before**.

## What this session did instead

- **Named it and stopped.** No tool call of any kind was aimed at it.
- **The gate built for [W-196](../../archive/open/W-196-l11-breach-2026-09-17.md)** —
  [`tests/test_golden_key_never_committed.py`](../../tests/test_golden_key_never_committed.py)
  — works from `git ls-files` and **skips the whole sealed tree on both
  spellings**, so it can report *"a committed file elsewhere looks like a key"*
  without ever reading one.

## ✅ RULED 2026-09-18 (Arpit) — it holds answer docs, and it STAYS

**Arpit inspected it himself.** It holds answer docs. He rules: **keep them on
disk**, make `golden-answers/` the canonical spelling everywhere, guard **both**
spellings, and **amend L11** to permit a local, gitignored, agent-closed key
directory — the Cowork-mount exposure recorded as accepted.

**Step 2 above ("remove it") is superseded by the ruling.** The work is
[W-198](W-198-golden-answers-canonical.md); this item closes when it lands.
🔴 **Decision 5 is unchanged** — no agent aims any tool at the directory, on
either spelling, before or after.
