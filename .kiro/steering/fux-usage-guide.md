---
inclusion: auto
name: fux-usage-guide
description: Running any fux command in this repository - resolving the fux binary when it reports not found, choosing between ask, find, answer, explain, graph and path, and reading --json instead of prose. Use before falling back to grep.
---

# Running Fux

- **Resolve the command once per session:** `fux --version`, then
  `uv run fux --version`, then `./.venv/bin/fux --version`, then
  `python -m fux --version`. `command not found` on the first rung does not mean
  fux is absent.
- **Never activate a virtualenv, change the shell's search path, or install
  anything** to make it run.
- **Prefer `--json` and branch on fields**, never on the wording.
- `ask`/`find` return documents; **only `answer` returns line ranges.**
- If every rung fails, say which you tried, then say you fell back.

Full procedure: the `fux-usage` skill.
