"""Load rule files and resolve the effective ruleset (plan §5).

effective = project ⊕ packs ⊕ global, with project overriding pack overriding
global by ``id``. Deprecated entries are kept (for history) but flagged.
"""
from __future__ import annotations

from pathlib import Path

from fux import config, frontmatter, paths
from fux.model import Rule, RuleSet


def load_dir(directory: Path, layer: str) -> list[Rule]:
    """Parse every ``*.md`` under ``directory`` into Rule objects."""
    rules: list[Rule] = []
    if not directory.is_dir():
        return rules
    for path in sorted(directory.rglob("*.md")):
        if path.name in ("INDEX.md", "DRIFT.md", "ONBOARDING.md", "README.md"):
            continue
        fm, body = frontmatter.split(path.read_text(encoding="utf-8"))
        rid = str(fm.get("id") or path.stem)
        rtype = str(fm.get("type") or "rule")
        rules.append(Rule(id=rid, type=rtype, fm=fm, body=body, path=path, layer=layer))
    return rules


def _source_dirs(fp: paths.Footprint) -> list[Path]:
    return [fp.rules, fp.glossary, fp.memory, fp.decisions]


def resolve(root: Path, cfg: dict | None = None) -> RuleSet:
    """Build the precedence-merged RuleSet for a project root."""
    fp = paths.Footprint(root)
    cfg = cfg or config.load(fp.config)
    merged: dict[str, Rule] = {}
    # Lowest precedence first; later layers overwrite by id.
    if cfg.get("use_global", True):
        for r in load_dir(paths.global_dir() / "rules", "global"):
            merged[r.id] = r
    for pack in cfg.get("packs", []):
        for r in load_dir(paths.packs_dir() / pack / "rules", f"pack:{pack}"):
            merged[r.id] = r
    for src in _source_dirs(fp):
        for r in load_dir(src, "project"):
            merged[r.id] = r
    return RuleSet(rules=list(merged.values()))


def load_all_layers(root: Path, cfg: dict | None = None) -> list[Rule]:
    """All rules across layers WITHOUT id-merge — for conflict detection."""
    fp = paths.Footprint(root)
    cfg = cfg or config.load(fp.config)
    out: list[Rule] = []
    if cfg.get("use_global", True):
        out += load_dir(paths.global_dir() / "rules", "global")
    for pack in cfg.get("packs", []):
        out += load_dir(paths.packs_dir() / pack / "rules", f"pack:{pack}")
    for src in _source_dirs(fp):
        out += load_dir(src, "project")
    return out
