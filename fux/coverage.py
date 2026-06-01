"""`fux coverage` — % of important code files with a governing rule (plan §10.3)."""
from __future__ import annotations

import fnmatch
from dataclasses import dataclass
from pathlib import Path

from fux import config, loader, paths


@dataclass
class Coverage:
    total: int
    governed: int
    uncovered: list[str]

    @property
    def pct(self) -> float:
        return 100.0 * self.governed / self.total if self.total else 100.0


def run(root: Path) -> Coverage:
    cfg = config.load(paths.Footprint(root).config)
    rs = loader.resolve(root, cfg)
    governed = {ref.split("#")[0].rstrip("/") for r in rs.rules for ref in r.code_refs}
    important = _important_files(root, cfg)
    uncovered = sorted(f for f in important if f not in governed)
    return Coverage(total=len(important), governed=len(important) - len(uncovered),
                    uncovered=uncovered)


def _important_files(root: Path, cfg: dict) -> list[str]:
    out: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if rel.startswith(".fux/"):
            continue
        if any(fnmatch.fnmatch(rel, g) for g in cfg["ignore_globs"]):
            continue
        if any(fnmatch.fnmatch(rel, g) for g in cfg["important_globs"]):
            out.append(rel)
    return out
