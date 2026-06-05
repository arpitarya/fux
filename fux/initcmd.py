"""`fux init` — scaffold the .fux/ footprint + wire hooks + CLAUDE.md pointer (plan §4)."""
from __future__ import annotations

from pathlib import Path

from fux import config, paths, settings

POINTER_START = "<!-- fux:start -->"
POINTER_END = "<!-- fux:end -->"
_POINTER = f"""{POINTER_START}
## Fux knowledge engine

This project's rules, memory, narrative, and graph live in `.fux/` (one substrate).

- SessionStart injects the compact INDEX automatically — no manual read needed.
- Look up a rule: `fux why <id>` · what governs a file: `fux refs <path>`
- Rebuild derived views ($0): `fux build` · check for drift: `fux check`
- Author a new entry: `fux new <type> <id>`
{POINTER_END}"""


def run(root: Path, recall: bool = False) -> dict:
    fp = paths.Footprint(root)
    for d in (fp.rules, fp.glossary, fp.memory / "shared", fp.out):
        d.mkdir(parents=True, exist_ok=True)
    if not fp.config.exists():
        fp.config.write_text(config.default_toml(), encoding="utf-8")
    _gitignore(fp)
    (fp.out / ".gitkeep").touch()
    settings_path = settings.wire(root, recall=recall)
    pointer = _claude_pointer(root)
    return {"footprint": str(fp.base), "settings": str(settings_path), "claude_md": str(pointer)}


def _gitignore(fp: paths.Footprint) -> None:
    gi = fp.base / ".gitignore"
    if gi.exists():
        return
    gi.write_text("# Generated derived views — rebuilt by `fux build` ($0).\n"
                  "out/\n"
                  "# Machine-local runtime ledgers (usage + cumulative cost tracking).\n"
                  "usage.json\n"
                  "cost.json\n"
                  "# Personal-scope memory (scope: personal) stays local.\n"
                  "memory/personal/\n", encoding="utf-8")


def _claude_pointer(root: Path) -> Path:
    path = root / "CLAUDE.md"
    text = path.read_text(encoding="utf-8") if path.exists() else "# CLAUDE.md\n"
    if POINTER_START in text:
        head, _, rest = text.partition(POINTER_START)
        _, _, tail = rest.partition(POINTER_END)
        text = head + _POINTER + tail
    else:
        text = text.rstrip() + "\n\n" + _POINTER + "\n"
    path.write_text(text, encoding="utf-8")
    return path
