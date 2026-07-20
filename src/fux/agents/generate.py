"""Agent-file generation: one contract, rendered into every surface.

Canonical instructions live in AGENTS.md (the open standard); CLAUDE.md,
copilot-instructions and Kiro steering get thin pointers; skills follow the
Agent Skills open standard (one SKILL.md per skill, read by 32+ tools); hooks
enforce injection where the host supports it. Everything is idempotent: managed
blocks are delimited by markers, user content outside them is never touched
(see compare/agent-integration.compare.md)."""

from __future__ import annotations

import json
from pathlib import Path

from ..errors import FuxError

MANAGED_START = "<!-- fux:managed:start -->"
MANAGED_END = "<!-- fux:managed:end -->"

PROMPT_SUBMIT_CMD = "fux hook prompt-submit"
SESSION_END_CMD = "fux hook session-end"

_CONTRACT = """\
## Fux — query the project's knowledge before guessing

This project maintains a Fux corpus (`.fux/cache/` — versioned knowledge with
provenance). Before answering questions about this project's docs, decisions,
or history:

1. Run `fux ask "<question>" --json` and prefer its passages (with `file:line`
   citations) over your own recall.
2. Use `fux find "<topic>"` to locate documents; `fux answer "<question>"
   --explain` for a cited, extractive answer plus the reasoning behind it.
3. Results carry `fidelity: inferred` provenance. If a cited source looks thin,
   fix or extend the source document and re-run `fux ingest` (the advanced
   re-ingest tier arrives in v1.1).
4. After adding or editing source folders, re-run `fux ingest` — the index
   updates incrementally — then re-ask.

All commands are `$0`, offline, and deterministic; `--json` is the agent path."""

_POINTER = """\
## Fux

This project uses **Fux** (a $0, deterministic knowledge engine). The canonical
agent contract lives in [AGENTS.md](AGENTS.md) (fux-managed section): query the
corpus with `fux ask "<question>" --json` before answering questions about this
project's docs or decisions."""

_SKILLS = {
    "fux-query": """\
---
name: fux-query
description: Query this project's Fux knowledge corpus — ranked passages (fux ask), file locator (fux find), extractive cited answers (fux answer). Use before answering any question about the project's docs, decisions, or history.
---

# fux-query

Fux answers natural-language questions over this project's own documents —
offline, deterministic, `$0`, with `file:line` citations.

## Commands

- `fux ask "<question>" --json` — ranked passages (the default agent call).
- `fux find "<topic>" --json` — which files cover a topic.
- `fux answer "<question>" --json --explain` — extractive cited answer + why.
- Modifiers: `--top N`, `-C N` (passage lines, ask only), `--answer-max N`.

## Workflow

1. Ask first, answer second: prefer returned passages over recall.
2. Trust the citations — every passage carries its source `file:line`.
3. Zero hits ≠ "does not exist": try broader terms with `fux find`, and check
   the corpus is fresh (`fux ingest --check`).
4. If sources changed, run `fux ingest` (incremental) and re-ask.
""",
    "fux-ingest": """\
---
name: fux-ingest
description: Maintain this project's Fux corpus — run fux ingest after adding or editing source documents, check freshness with --check, inspect skipped files. Use when queries look stale or new documents were added.
---

# fux-ingest

`fux ingest` converts the folders configured in `fux.toml` into the OKF cache
(`.fux/cache/`) with provenance frontmatter, a manifest, and a BM25F index.
Deterministic and incremental: unchanged files are never rewritten.

## Commands

- `fux ingest` — convert + index (incremental; safe to run any time).
- `fux ingest --check` — drift report (exit 1 when sources changed).
- `fux ingest --list-skipped` — what was skipped and why (binary, missing
  extras, unrecognized extensions).
- `fux ingest --list-inferred` — files at inferred fidelity.

## Workflow

1. After adding/editing docs: `fux ingest`, then re-run the question.
2. Before trusting query results in a long session: `fux ingest --check`.
3. Office/PDF need the opt-in extra: `pip install 'fux-engine[ingest]'`.
""",
}

_KIRO_HOOK = {
    "enabled": True,
    "name": "Fux: query the corpus first",
    "description": "Inject Fux passages so answers cite the project's own documents",
    "version": "1",
    "when": {"type": "userTriggered"},
    "then": {
        "type": "askAgent",
        "prompt": (
            'Run `fux ask "<the current question>" --json` and ground your answer '
            "in the returned passages (cite their file:line). If sources changed, "
            "run `fux ingest` first."
        ),
    },
}


def generate_agent_files(
    root: Path, *, agents: bool = False, skills: bool = False, hooks: bool = False
) -> list[tuple[str, str]]:
    """Generate the requested surfaces; returns (relative path, state) pairs."""
    results: list[tuple[str, str]] = []
    if agents:
        results.append(_upsert_block(root, "AGENTS.md", _CONTRACT))
        results.append(_upsert_block(root, "CLAUDE.md", _POINTER))
        results.append(_upsert_block(root, ".github/copilot-instructions.md", _POINTER))
        results.append(_upsert_block(root, ".kiro/steering/fux.md", _CONTRACT))
    if skills:
        for name, content in _SKILLS.items():
            results.append(_write_file(root, f".claude/skills/{name}/SKILL.md", content))
    if hooks:
        results.append(_merge_claude_settings(root))
        results.append(
            _write_file(
                root,
                ".kiro/hooks/fux-query.kiro.hook",
                json.dumps(_KIRO_HOOK, indent=2, ensure_ascii=False) + "\n",
            )
        )
    return results


def _upsert_block(root: Path, rel: str, content: str) -> tuple[str, str]:
    """Insert or refresh the fux-managed block; user content outside it is kept."""
    path = root / rel
    block = f"{MANAGED_START}\n{content.strip()}\n{MANAGED_END}"
    if not path.is_file():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(block + "\n", encoding="utf-8")
        return rel, "created"
    text = path.read_text(encoding="utf-8")
    if MANAGED_START in text and MANAGED_END in text:
        head, _, rest = text.partition(MANAGED_START)
        _, _, tail = rest.partition(MANAGED_END)
        new = head + block + tail
    else:
        new = text.rstrip("\n") + "\n\n" + block + "\n"
    if new == text:
        return rel, "unchanged"
    path.write_text(new, encoding="utf-8")
    return rel, "updated"


def _write_file(root: Path, rel: str, content: str) -> tuple[str, str]:
    path = root / rel
    if path.is_file():
        if path.read_text(encoding="utf-8") == content:
            return rel, "unchanged"
        path.write_text(content, encoding="utf-8")
        return rel, "updated"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return rel, "created"


def _merge_claude_settings(root: Path) -> tuple[str, str]:
    """Add fux hook entries to .claude/settings.json without touching user keys."""
    rel = ".claude/settings.json"
    path = root / rel
    settings: dict = {}
    if path.is_file():
        try:
            settings = json.loads(path.read_text(encoding="utf-8"))
        except ValueError as exc:
            raise FuxError(f"{rel} is not valid JSON ({exc}) — fix it, then re-run") from exc
    hooks = settings.setdefault("hooks", {})
    changed = False
    for event, command in (("UserPromptSubmit", PROMPT_SUBMIT_CMD), ("Stop", SESSION_END_CMD)):
        entries = hooks.setdefault(event, [])
        present = any(
            h.get("command") == command
            for entry in entries
            if isinstance(entry, dict)
            for h in entry.get("hooks", [])
            if isinstance(h, dict)
        )
        if not present:
            entries.append({"hooks": [{"type": "command", "command": command}]})
            changed = True
    if not changed and path.is_file():
        return rel, "unchanged"
    state = "updated" if path.is_file() else "created"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(settings, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return rel, state
