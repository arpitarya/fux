"""Path resolution for the global engine and per-project footprint (plan §4)."""
from __future__ import annotations

import os
import re
from pathlib import Path


def claude_home() -> Path:
    return Path(os.environ.get("CLAUDE_CONFIG_DIR", Path.home() / ".claude"))


def global_dir() -> Path:
    """Cross-project best practices (its own git repo). plan §5."""
    return Path(os.environ.get("FUX_GLOBAL", claude_home() / "fux" / "global"))


def packs_dir() -> Path:
    return Path(os.environ.get("FUX_PACKS", claude_home() / "fux" / "packs"))


def bundled_data_dir() -> Path:
    """Seed data shipped with the fux package (global rules, hooks, skills, schema)."""
    return Path(__file__).parent / "data"


def schema_path() -> Path:
    env = os.environ.get("FUX_SCHEMA")
    if env:
        return Path(env)
    installed = claude_home() / "fux" / "schema.json"
    if installed.exists():
        return installed
    return bundled_data_dir() / "schema.json"


def home_memory_dir(root: Path) -> Path:
    """Claude's home-dir cross-session memory for a project (plan §17.16).

    Claude slugifies the absolute project path by replacing every non-alphanumeric
    run with ``-`` (so ``/Users/a/my_programs/anton`` → ``-Users-a-my-programs-anton``
    — underscores become hyphens too, not just slashes)."""
    slug = re.sub(r"[^A-Za-z0-9]+", "-", str(root.resolve()))
    return claude_home() / "projects" / slug / "memory"


def find_project_root(start: Path | None = None) -> Path | None:
    """Walk up from ``start`` to the dir containing a ``.fux/`` footprint."""
    cur = (start or Path.cwd()).resolve()
    for parent in [cur, *cur.parents]:
        if (parent / ".fux").is_dir():
            return parent
    return None


class Footprint:
    """The per-project ``.fux/`` layout (plan §4)."""

    def __init__(self, root: Path):
        self.root = root
        self.base = root / ".fux"

    @property
    def rules(self) -> Path:
        return self.base / "rules"

    @property
    def glossary(self) -> Path:
        return self.base / "glossary"

    @property
    def memory(self) -> Path:
        return self.base / "memory"

    @property
    def out(self) -> Path:
        return self.base / "out"

    @property
    def config(self) -> Path:
        return self.base / "config.toml"

    def out_file(self, name: str) -> Path:
        self.out.mkdir(parents=True, exist_ok=True)
        return self.out / name
