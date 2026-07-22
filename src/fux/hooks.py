"""Hook entrypoints — a boundary, like `cli.main`, but fail-open.

The contract (CLAUDE.md): a hook error never breaks the session, but nothing
fails *silent* — every swallowed exception traces under ``FUX_DEBUG=1``. These
run inside other tools' hot paths, so they stay quiet unless they have
something useful to inject.
"""

from __future__ import annotations

import json
import os
import sys
import traceback
from pathlib import Path

from . import debug

_TOP = 3
_SNIPPET_LINES = 3


def cmd_hook(args) -> int:
    try:
        debug.dbg("hooks", "info", "hook fired", event=args.event)
        if args.event == "prompt-submit":
            return _prompt_submit()
        return _session_end()
    except Exception:
        if os.environ.get("FUX_DEBUG"):
            traceback.print_exc()
        debug.dbg("hooks", "debug", "hook error swallowed (fail-open)", event=args.event)
        return 0  # fail-open — never break the host session


def _prompt_submit() -> int:
    """Claude Code UserPromptSubmit: inject top passages as additional context."""
    payload = json.loads(sys.stdin.read() or "{}")
    prompt = payload.get("prompt", "")
    if not isinstance(prompt, str) or len(prompt.split()) < 3:
        debug.dbg("hooks", "debug", "prompt too short — no injection")
        return 0
    from .config import find_root, load
    from .index import load_searcher

    config = load(find_root(Path.cwd()))
    results = load_searcher(config).search(prompt, top=_TOP)
    debug.dbg("hooks", "debug", "prompt-submit passages", results=len(results))
    if not results:
        return 0
    lines = ["Fux corpus passages relevant to this prompt (cite file:line):"]
    for r in results:
        loc = f"{r.file}:{r.start}-{r.end}" if r.start is not None else r.file
        snippet = " ".join(r.text.split("\n")[:_SNIPPET_LINES])
        lines.append(f"- {loc} · {snippet[:300]}")
    lines.append("(from `fux ask` — run it directly for more)")
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "UserPromptSubmit",
                    "additionalContext": "\n".join(lines),
                }
            },
            ensure_ascii=False,
        )
    )
    return 0


def _session_end() -> int:
    """Stop hook: advisory doc-registry nudge — nags, never blocks."""
    from .config import find_root

    try:
        root = find_root(Path.cwd())
    except Exception:
        return 0
    registry = root / "docs" / "DOC-REGISTRY.md"
    if registry.is_file():
        print(
            "fux: docs/DOC-REGISTRY.md tracks maintained docs — if this session "
            "changed behaviour, check the registry's triggers and update the docs."
        )
    return 0
