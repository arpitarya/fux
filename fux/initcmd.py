"""`fux init` — scaffold the .fux/ footprint + wire hooks + agent pointers."""
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

AGENTS_POINTER_START = "<!-- fux:agents:start -->"
AGENTS_POINTER_END = "<!-- fux:agents:end -->"
_AGENTS_POINTER = f"""{AGENTS_POINTER_START}
## Fux knowledge engine

This project's rules, memory, narrative, and graph live in `.fux/` (one substrate).

- First check `fux context` for the compact INDEX when answering project questions.
- Look up a rule with `fux why <id>` and file coverage with `fux refs <path>`.
- Rebuild derived views with `fux build`; check drift with `fux check`.
- Keep durable project knowledge in `.fux/` entries instead of orphan notes.
{AGENTS_POINTER_END}"""

COPILOT_POINTER_START = "<!-- fux:copilot:start -->"
COPILOT_POINTER_END = "<!-- fux:copilot:end -->"
_COPILOT_POINTER = f"""{COPILOT_POINTER_START}
# Fux knowledge engine

This repository stores durable rules, memory, narrative, and graph data in `.fux/`.

When answering, reviewing, or suggesting code:
- Prefer `fux context`, `fux recall "<question>"`, `fux why <id>`, and `fux refs <path>` for project knowledge.
- Preserve and update `.fux/` entries when a code change creates or changes a durable rule.
- Treat `.fux/out/` as generated output from `fux build`.
{COPILOT_POINTER_END}"""


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
    agents = _agents_pointer(root)
    copilot = _copilot_pointer(root)
    prompts = _copilot_prompts(root)
    return {"footprint": str(fp.base), "settings": str(settings_path),
            "claude_md": str(pointer), "agents_md": str(agents),
            "copilot_instructions": str(copilot),
            "copilot_prompts": [str(p) for p in prompts]}


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
    _write_pointer(path, "# CLAUDE.md\n", POINTER_START, POINTER_END, _POINTER)
    return path


def _agents_pointer(root: Path) -> Path:
    path = root / "AGENTS.md"
    _write_pointer(path, "# AGENTS.md\n", AGENTS_POINTER_START, AGENTS_POINTER_END,
                   _AGENTS_POINTER)
    return path


def _copilot_pointer(root: Path) -> Path:
    path = root / ".github" / "copilot-instructions.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    _write_pointer(path, "", COPILOT_POINTER_START, COPILOT_POINTER_END,
                   _COPILOT_POINTER)
    return path


def _copilot_prompts(root: Path) -> list[Path]:
    src = paths.bundled_data_dir() / "copilot" / "prompts"
    if not src.exists():
        return []
    dst = root / ".github" / "prompts"
    dst.mkdir(parents=True, exist_ok=True)
    copied = []
    for prompt in sorted(src.glob("*.prompt.md")):
        target = dst / prompt.name
        if not target.exists():
            target.write_text(prompt.read_text(encoding="utf-8"), encoding="utf-8")
        copied.append(target)
    return copied


def _write_pointer(path: Path, default: str, start: str, end: str, pointer: str) -> None:
    text = path.read_text(encoding="utf-8") if path.exists() else default
    if start in text:
        head, _, rest = text.partition(start)
        _, _, tail = rest.partition(end)
        text = head + pointer + tail
    else:
        text = text.rstrip() + "\n\n" + pointer + "\n"
    path.write_text(text, encoding="utf-8")
