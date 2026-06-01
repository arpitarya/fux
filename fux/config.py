"""Per-project config (.fux/config.toml) — strictness, packs, globs (plan §8)."""
from __future__ import annotations

from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover  (Python <3.11)
    tomllib = None

MODES = ["off", "warn", "fix", "strict"]
DEFAULTS = {
    "mode": "fix",
    "packs": [],
    "important_globs": ["**/*.py", "**/*.ts", "**/*.tsx", "**/*.go", "**/*.rs"],
    "ignore_globs": ["**/node_modules/**", "**/.venv/**", "**/dist/**", "**/build/**"],
    "use_global": True,
    "recall_rerank": False,   # phase-2 opt-in local embeddings (recall-engine.compare.md)
}


def load(config_path: Path) -> dict:
    """Read config.toml, merged over DEFAULTS. Tolerant of a missing file."""
    cfg = dict(DEFAULTS)
    if config_path.exists() and tomllib is not None:
        with config_path.open("rb") as fh:
            data = tomllib.load(fh)
        cfg.update(data.get("fux", data))
    if cfg.get("mode") not in MODES:
        cfg["mode"] = "fix"
    return cfg


def default_toml() -> str:
    """The config.toml `fux init` writes."""
    return (
        "[fux]\n"
        '# Enforcement: off | warn | fix (default) | strict  — see fux-plan.md §8\n'
        'mode = "fix"\n\n'
        "# Opt-in rule packs from ~/.claude/fux/packs/ (plan §5)\n"
        "packs = []\n\n"
        "# Inherit ~/.claude/fux/global/ best practices\n"
        "use_global = true\n\n"
        "# Files that should ideally have a governing rule (fux coverage)\n"
        'important_globs = ["**/*.py", "**/*.ts", "**/*.tsx"]\n'
        'ignore_globs = ["**/node_modules/**", "**/.venv/**", "**/dist/**"]\n\n'
        "# Phase-2 local embedding re-rank for recall (no API). Off by default.\n"
        "recall_rerank = false\n"
    )
