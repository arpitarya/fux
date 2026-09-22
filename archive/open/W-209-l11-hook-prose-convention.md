---
type: OpenItem
id: W-209
title: "W-209 — the L11 hook and prose: accept it, one convention, one gate"
description: "Arpit, 2026-09-21 (Cowork): the hook stays fail-closed and untouched; prose that must spell a key path is written with the Write/Edit tool, never through a shell command; one test pins both behaviours. Closes the fourth-occurrence inbox row of 2026-09-21."
status: open
lane: agent
timestamp: 2026-09-21T00:00:00Z
filed: 2026-09-21
ball: agent
ruled: 2026-09-21
---

# W-209 — the L11 hook fires on prose: accept, convention, gate

**Model: Sonnet** — one rule stated once, one test, no engine code.

## ✅ RULED 2026-09-21 (Arpit, Cowork) — accept + convention

**The class.** `.claude/hooks/guard-golden-answer.sh` greps every **Bash**
command for the key directory's name and fails closed, so a heredoc or a
`python -c` that *writes prose* naming the path is refused, while the same prose
through the **Write/Edit tool** passes — those are checked by `file_path` only.
Fourth recorded occurrence on 2026-09-21
([ANALYSIS §6](../regression/2026-09-21-ladder-set-3-rebuild/ANALYSIS.md)).

**Example.** `cat > work/golden/README.md <<EOF … <the key path> … EOF` → BLOCKED.
Write tool, `file_path=work/golden/README.md`, same content → allowed.

**Ruled.** The hook is **not narrowed and not widened**. The convention: *prose
that must spell a key path is written with the Write/Edit tool, never through a
shell command.* Two strikes → a gate (SR-WORK-SESSION decision 13).

## Definition of done

1. The convention stated **once**, in SR-WORK-GOLDEN (the guards decision);
   `work/golden/README.md` links to it and does not restate it.
2. `tests/test_golden_hook_prose.py` feeds the hook three inputs and asserts:
   a Bash heredoc naming the path → exit 2; a Write call whose **content** names
   the path and whose `file_path` does not → exit 0; a Read whose `file_path` is
   under either spelling → exit 2. ⚠ Under W-204's switch the test runs against
   the **locked** state.
3. WORKLOG, IMPLEMENTATION.md, DOC-REGISTRY.

## Out of scope

Narrowing the hook to path-shaped tokens; a docs lint forbidding the spelling.
Both were offered on 2026-09-21 and declined.
